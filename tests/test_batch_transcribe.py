"""
Tests for batch_transcribe.py.

The driver's whole job is to still be running after something goes wrong, so
these test the parts that decide what runs and what gets recorded. They never
invoke the real pipeline; `run_one` is exercised against a stub process.

Two properties matter most.

**Only success is skipped on resume.** A timeout or a crash says nothing about
whether a retry would work, so anything that is not "ok" must be retried. A
driver that skipped failures would quietly shrink the corpus on every restart.

**The manifest is written after every video.** Both overnight runs this month
were killed partway, and both times the log's last line was not the truth. The
manifest has to be the record, which means it cannot be written at the end.

Run:  python -m pytest tests/test_batch_transcribe.py -v
"""

import csv
import subprocess

import pytest

import batch_transcribe as B


def touch(d, name):
    p = d / name
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(b"\0")
    return p


# ----------------------------------------------------------- discovery ---


def test_find_media_takes_only_media_suffixes(tmp_path):
    touch(tmp_path, "a.mkv")
    touch(tmp_path, "b.webm")
    touch(tmp_path, "c.en.vtt")
    touch(tmp_path, "d.info.json")
    assert [p.name for p in B.find_media(tmp_path)] == ["a.mkv", "b.webm"]


def test_find_media_is_sorted(tmp_path):
    """A resumed run must process in the same order, so a partial manifest
    reads as a prefix of the whole job rather than an arbitrary subset."""
    for n in ("z.mkv", "a.mkv", "m.mkv"):
        touch(tmp_path, n)
    assert [p.name for p in B.find_media(tmp_path)] == ["a.mkv", "m.mkv", "z.mkv"]


def test_find_media_ignores_directories(tmp_path):
    (tmp_path / "sub.mkv").mkdir()
    touch(tmp_path, "real.mkv")
    assert [p.name for p in B.find_media(tmp_path)] == ["real.mkv"]


# -------------------------------------------------------------- resume ---


def test_resume_skips_only_ok(tmp_path):
    media = [touch(tmp_path, f"{v}.mkv") for v in ("v1", "v2", "v3", "v4")]
    rows = {
        "v1": {"video_id": "v1", "status": "ok"},
        "v2": {"video_id": "v2", "status": "failed"},
        "v3": {"video_id": "v3", "status": "timeout"},
        # v4 absent: never attempted
    }
    got = [p.stem for p in B.pending(media, rows, resume=True)]
    assert got == ["v2", "v3", "v4"], (
        "a timeout or a failure says nothing about whether a retry works, so "
        "both must be retried; only success may be skipped"
    )


def test_without_resume_everything_runs(tmp_path):
    media = [touch(tmp_path, f"{v}.mkv") for v in ("v1", "v2")]
    rows = {"v1": {"video_id": "v1", "status": "ok"}}
    assert len(B.pending(media, rows, resume=False)) == 2


def test_resume_with_no_manifest_runs_everything(tmp_path):
    media = [touch(tmp_path, "v1.mkv")]
    assert len(B.pending(media, {}, resume=True)) == 1


# ------------------------------------------------------------ manifest ---


def test_manifest_round_trips(tmp_path):
    p = tmp_path / "manifest.csv"
    rows = {"v1": {"video_id": "v1", "media_file": "v1.mkv", "status": "ok",
                   "elapsed_s": "12.3", "segments": "40", "engines": "whisper",
                   "returncode": "0", "note": ""}}
    B.write_manifest(p, rows)
    assert B.read_manifest(p)["v1"]["segments"] == "40"


def test_missing_manifest_is_not_an_error(tmp_path):
    assert B.read_manifest(tmp_path / "nope.csv") == {}


def test_manifest_write_is_atomic(tmp_path):
    """Written via a temp file and replaced, so a kill mid-write cannot leave a
    half-row that read_manifest would parse as truth."""
    p = tmp_path / "manifest.csv"
    B.write_manifest(p, {"v1": {"video_id": "v1", "status": "ok"}})
    B.write_manifest(p, {"v1": {"video_id": "v1", "status": "ok"},
                         "v2": {"video_id": "v2", "status": "failed"}})
    assert not list(tmp_path.glob("*.tmp"))
    with p.open(newline="", encoding="utf-8") as fh:
        assert len(list(csv.DictReader(fh))) == 2


def test_manifest_keeps_unknown_videos(tmp_path):
    """Rows for media no longer in the directory survive a rewrite. Deleting a
    file should not erase the record that it was once processed."""
    p = tmp_path / "manifest.csv"
    B.write_manifest(p, {"gone": {"video_id": "gone", "status": "ok"}})
    rows = B.read_manifest(p)
    rows["new"] = {"video_id": "new", "status": "ok"}
    B.write_manifest(p, rows)
    assert set(B.read_manifest(p)) == {"gone", "new"}


# ------------------------------------------------------------- run_one ---


class FakeProc:
    def __init__(self, returncode, stdout="", stderr=""):
        self.returncode, self.stdout, self.stderr = returncode, stdout, stderr


def test_run_one_records_success(tmp_path, monkeypatch):
    monkeypatch.setattr(B.subprocess, "run", lambda *a, **k: FakeProc(0, "done"))
    row = B.run_one(tmp_path / "v1.mkv", tmp_path / "out", "whisper",
                    60.0, [], "python", tmp_path / "run.py")
    assert row["status"] == "ok"
    assert row["video_id"] == "v1"


def test_run_one_records_failure_with_the_last_stderr_line(tmp_path, monkeypatch):
    monkeypatch.setattr(
        B.subprocess, "run",
        lambda *a, **k: FakeProc(1, "", "warning: blah\n\nRuntimeError: no audio\n"),
    )
    row = B.run_one(tmp_path / "v1.mkv", tmp_path / "out", "whisper",
                    60.0, [], "python", tmp_path / "run.py")
    assert row["status"] == "failed"
    assert "RuntimeError: no audio" in row["note"]


def test_run_one_survives_a_timeout(tmp_path, monkeypatch):
    def boom(*a, **k):
        raise subprocess.TimeoutExpired(cmd="x", timeout=60.0)

    monkeypatch.setattr(B.subprocess, "run", boom)
    row = B.run_one(tmp_path / "v1.mkv", tmp_path / "out", "whisper",
                    60.0, [], "python", tmp_path / "run.py")
    assert row["status"] == "timeout"


def test_run_one_survives_an_unexpected_exception(tmp_path, monkeypatch):
    """The driver must outlive any one video, including failures that are not
    the subprocess failing -- a bad path, a permissions error, anything."""
    def boom(*a, **k):
        raise OSError("file system said no")

    monkeypatch.setattr(B.subprocess, "run", boom)
    row = B.run_one(tmp_path / "v1.mkv", tmp_path / "out", "whisper",
                    60.0, [], "python", tmp_path / "run.py")
    assert row["status"] == "error"
    assert "OSError" in row["note"]


def test_run_one_gives_each_video_its_own_outdir(tmp_path, monkeypatch):
    """The reason this driver exists at all.

    run.py names its outputs from the sanitised title truncated to 120 chars,
    and reuses an existing wav without checking it belongs to this video. Two
    videos sharing a 120-char title prefix would silently share audio and
    spine. Separate output directories make that impossible.
    """
    seen = {}

    def capture(cmd, **k):
        seen["cmd"] = cmd
        return FakeProc(0)

    monkeypatch.setattr(B.subprocess, "run", capture)
    out = tmp_path / "out"
    for vid in ("aaa", "bbb"):
        B.run_one(tmp_path / f"{vid}.mkv", out, "whisper", 60.0, [],
                  "python", tmp_path / "run.py")
        assert str(out / vid) in seen["cmd"]


def test_run_one_always_passes_resume(tmp_path, monkeypatch):
    """A retried video must continue its own spine rather than rediarizing."""
    seen = {}
    monkeypatch.setattr(B.subprocess, "run",
                        lambda cmd, **k: seen.update(cmd=cmd) or FakeProc(0))
    B.run_one(tmp_path / "v1.mkv", tmp_path / "out", "whisper", 60.0, [],
              "python", tmp_path / "run.py")
    assert "--resume" in seen["cmd"]


def test_extra_arguments_reach_run_py(tmp_path, monkeypatch):
    seen = {}
    monkeypatch.setattr(B.subprocess, "run",
                        lambda cmd, **k: seen.update(cmd=cmd) or FakeProc(0))
    B.run_one(tmp_path / "v1.mkv", tmp_path / "out", "whisper", 60.0,
              ["--diarize", "vad"], "python", tmp_path / "run.py")
    assert seen["cmd"][-2:] == ["--diarize", "vad"]


# ---------------------------------------------------------------- main ---


def test_dry_run_writes_nothing(tmp_path, monkeypatch):
    media = tmp_path / "media"
    media.mkdir()
    touch(media, "v1.mkv")
    run_py = tmp_path / "run.py"
    run_py.write_text("", encoding="utf-8")
    out = tmp_path / "out"

    def explode(*a, **k):
        raise AssertionError("dry run must not start a process")

    monkeypatch.setattr(B.subprocess, "run", explode)
    rc = B.main(["--media-dir", str(media), "--outdir", str(out),
                 "--run-py", str(run_py), "--dry-run"])
    assert rc == 0
    assert not out.exists()


def test_main_writes_the_manifest_after_each_video(tmp_path, monkeypatch):
    """Not at the end. Both overnight runs this month were killed partway."""
    media = tmp_path / "media"
    media.mkdir()
    for v in ("v1", "v2"):
        touch(media, f"{v}.mkv")
    run_py = tmp_path / "run.py"
    run_py.write_text("", encoding="utf-8")
    out = tmp_path / "out"
    seen_counts = []

    def fake(cmd, **k):
        # What the manifest holds at the moment this video starts.
        seen_counts.append(len(B.read_manifest(out / "manifest.csv")))
        return FakeProc(0)

    monkeypatch.setattr(B.subprocess, "run", fake)
    B.main(["--media-dir", str(media), "--outdir", str(out),
            "--run-py", str(run_py)])
    assert seen_counts == [0, 1], (
        "the second video should start with the first already recorded"
    )


def test_main_returns_nonzero_when_a_video_failed(tmp_path, monkeypatch):
    """So a scheduled or unattended run can be noticed rather than assumed fine."""
    media = tmp_path / "media"
    media.mkdir()
    touch(media, "v1.mkv")
    run_py = tmp_path / "run.py"
    run_py.write_text("", encoding="utf-8")
    monkeypatch.setattr(B.subprocess, "run",
                        lambda *a, **k: FakeProc(1, "", "boom"))
    rc = B.main(["--media-dir", str(media), "--outdir", str(tmp_path / "out"),
                 "--run-py", str(run_py)])
    assert rc == 1


def test_main_refuses_a_missing_run_py(tmp_path):
    media = tmp_path / "media"
    media.mkdir()
    rc = B.main(["--media-dir", str(media), "--outdir", str(tmp_path / "out"),
                 "--run-py", str(tmp_path / "nope.py")])
    assert rc == 2


def test_one_failure_does_not_stop_the_rest(tmp_path, monkeypatch):
    """The whole point. Item 37 of 120 failing must not end the run."""
    media = tmp_path / "media"
    media.mkdir()
    for v in ("v1", "v2", "v3"):
        touch(media, f"{v}.mkv")
    run_py = tmp_path / "run.py"
    run_py.write_text("", encoding="utf-8")
    out = tmp_path / "out"

    def fake(cmd, **k):
        return FakeProc(1, "", "bad") if "v2" in str(cmd) else FakeProc(0)

    monkeypatch.setattr(B.subprocess, "run", fake)
    B.main(["--media-dir", str(media), "--outdir", str(out), "--run-py", str(run_py)])
    rows = B.read_manifest(out / "manifest.csv")
    assert [rows[v]["status"] for v in ("v1", "v2", "v3")] == ["ok", "failed", "ok"]
