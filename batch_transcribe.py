#!/usr/bin/env python3
"""
Run transcribe2 over a directory of media files, unattended.

`transcribe2/run.py` does one source at a time and is resumable within that
source: its spine on disk is the state, so a killed run picks up the segments
that have no text yet. Nothing iterates sources, which is what a corpus needs.
This does, and nothing else -- it deliberately owns no pipeline logic.

    python batch_transcribe.py --media-dir downloads/videos/stress_search/youtube \\
        --outdir downloads/transcribe2_runs --engines whisper

    python batch_transcribe.py ... --resume       # skip what already succeeded
    python batch_transcribe.py ... --dry-run      # list the work, touch nothing

Four things it is responsible for.

**One output directory per video, keyed on the file stem, not the title.**
run.py names its outputs from the video title, sanitised and truncated to 120
characters, so two videos sharing a 120-character prefix would write to the
same wav and the same spine -- and `if wav.exists()` accepts that silently, so
the second video would be transcribed from the first one's audio. That exact
failure has already happened once in this project, when a truncating slug
mapped five different URLs onto one filename and produced confident nonsense
that nothing errored on. Giving each video its own directory removes the
possibility instead of betting that titles stay short.

**Surviving failures.** One unreadable download should not end the run at item
37 of 120. Each video runs in its own process, so even a hard crash in a native
library costs one video rather than the corpus. That is not hypothetical here:
llama.cpp took the whole session down twice on this machine.

**Corpus-level resume.** Kill it, restart with --resume, and videos that
already succeeded are skipped outright. Videos that failed or never ran are
retried, and run.py's own --resume continues them mid-spine.

**A manifest.** One row per video, written after every video rather than at the
end, because a run that dies leaves the manifest as the record of what landed.
Reconstructing state from a log's last line has been wrong twice this month.
"""

from __future__ import annotations

import argparse
import csv
import subprocess
import sys
import time
from pathlib import Path

MEDIA_SUFFIXES = {".mkv", ".webm", ".mp4", ".m4a", ".mp3", ".wav", ".flac", ".opus"}

MANIFEST_FIELDS = [
    "video_id",
    "media_file",
    "status",
    "elapsed_s",
    "segments",
    "engines",
    "returncode",
    "note",
]

# Statuses. "ok" is the only one --resume skips; everything else is retried,
# because a timeout or a crash tells you nothing about whether a retry works.
OK = "ok"


def find_media(media_dir: Path) -> list[Path]:
    """Media files in one directory, sorted, newest-first ties broken by name.

    Sorted so a resumed run processes them in the same order as the first run,
    which makes a partial manifest readable as a prefix of the whole job.
    """
    return sorted(
        p for p in media_dir.iterdir()
        if p.is_file() and p.suffix.lower() in MEDIA_SUFFIXES
    )


def read_manifest(path: Path) -> dict[str, dict]:
    """Existing rows keyed by video_id. A missing or empty file is not an error."""
    if not path.exists():
        return {}
    with path.open(newline="", encoding="utf-8") as fh:
        return {r["video_id"]: r for r in csv.DictReader(fh) if r.get("video_id")}


def write_manifest(path: Path, rows: dict[str, dict]) -> None:
    """Rewrite the whole manifest. Small file, and a partial row is worse than
    a rewrite: this is the only durable record of what the run actually did."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=MANIFEST_FIELDS)
        w.writeheader()
        for vid in sorted(rows):
            w.writerow({k: rows[vid].get(k, "") for k in MANIFEST_FIELDS})
    tmp.replace(path)


def pending(media: list[Path], rows: dict[str, dict], resume: bool) -> list[Path]:
    """What still needs doing. Without --resume, everything."""
    if not resume:
        return list(media)
    return [p for p in media if rows.get(p.stem, {}).get("status") != OK]


def count_segments(video_out: Path) -> str:
    """Segments in whatever spine this video produced, for the manifest.

    Best effort: the number is reporting, not control flow, so a malformed or
    missing spine yields an empty cell rather than failing the video.
    """
    spines = list((video_out / "spines").glob("*.spine.json"))
    if not spines:
        return ""
    try:
        import json

        d = json.loads(spines[0].read_text(encoding="utf-8"))
        return str(len(d.get("segments", [])))
    except Exception:
        return ""


def run_one(
    media: Path,
    outdir: Path,
    engines: str,
    timeout_s: float,
    extra: list[str],
    python: str,
    run_py: Path,
) -> dict:
    """One video, in its own process. Never raises."""
    video_out = outdir / media.stem
    cmd = [
        python, str(run_py), str(media),
        "-o", str(video_out),
        "--engines", engines,
        "--resume",          # always: a retried video continues its own spine
        *extra,
    ]
    row = {
        "video_id": media.stem,
        "media_file": media.name,
        "engines": engines,
        "segments": "",
        "note": "",
    }
    t0 = time.perf_counter()
    try:
        proc = subprocess.run(
            cmd, capture_output=True, text=True, timeout=timeout_s,
            cwd=str(run_py.parent),
        )
        row["returncode"] = proc.returncode
        row["status"] = OK if proc.returncode == 0 else "failed"
        if proc.returncode != 0:
            # Last non-empty stderr line is nearly always the useful one, and
            # the full output is kept on disk beside the video's outputs.
            tail = [ln for ln in (proc.stderr or "").splitlines() if ln.strip()]
            row["note"] = (tail[-1] if tail else "no stderr")[:300]
        video_out.mkdir(parents=True, exist_ok=True)
        (video_out / "run.log").write_text(
            (proc.stdout or "") + "\n--- stderr ---\n" + (proc.stderr or ""),
            encoding="utf-8",
        )
    except subprocess.TimeoutExpired:
        row["returncode"] = ""
        row["status"] = "timeout"
        row["note"] = f"exceeded {timeout_s:.0f}s"
    except Exception as e:  # noqa: BLE001 - the driver must outlive any one video
        row["returncode"] = ""
        row["status"] = "error"
        row["note"] = f"{type(e).__name__}: {e}"[:300]
    row["elapsed_s"] = f"{time.perf_counter() - t0:.1f}"
    row["segments"] = count_segments(video_out)
    return row


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    ap.add_argument("--media-dir", type=Path, required=True)
    ap.add_argument("--outdir", type=Path, required=True)
    ap.add_argument("--engines", default="whisper")
    ap.add_argument("--resume", action="store_true",
                    help="skip videos whose manifest status is ok")
    ap.add_argument("--limit", type=int, default=None,
                    help="process at most N videos this invocation")
    ap.add_argument("--timeout", type=float, default=3600.0,
                    help="per-video seconds before giving up (default 3600)")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--python", default=sys.executable)
    ap.add_argument("--run-py", type=Path, default=None,
                    help="path to transcribe2/run.py (default: beside this script)")
    ap.add_argument("extra", nargs="*",
                    help="further arguments passed through to run.py")
    args = ap.parse_args(argv)

    run_py = (args.run_py or Path(__file__).resolve().parent / "transcribe2" / "run.py")
    if not run_py.exists():
        print(f"run.py not found at {run_py}", file=sys.stderr)
        return 2
    if not args.media_dir.is_dir():
        print(f"not a directory: {args.media_dir}", file=sys.stderr)
        return 2

    outdir = args.outdir.resolve()
    manifest_path = outdir / "manifest.csv"
    rows = read_manifest(manifest_path)
    media = find_media(args.media_dir)
    todo = pending(media, rows, args.resume)
    if args.limit:
        todo = todo[: args.limit]

    done_already = len(media) - len(pending(media, rows, args.resume))
    print(f"media files:  {len(media)}")
    print(f"already ok:   {done_already}")
    print(f"this run:     {len(todo)}")
    print(f"engines:      {args.engines}")
    print(f"outdir:       {outdir}")

    if args.dry_run:
        for p in todo:
            print(f"  would run: {p.name}")
        return 0
    if not todo:
        print("nothing to do")
        return 0

    outdir.mkdir(parents=True, exist_ok=True)
    counts = {"ok": 0, "failed": 0, "timeout": 0, "error": 0}
    t_start = time.perf_counter()

    for i, media_path in enumerate(todo, 1):
        print(f"\n[{i}/{len(todo)}] {media_path.name}", flush=True)
        row = run_one(
            media_path, outdir, args.engines, args.timeout,
            list(args.extra), args.python, run_py,
        )
        rows[row["video_id"]] = row
        # After every video, not at the end: a run that dies leaves this as the
        # only trustworthy record of what landed.
        write_manifest(manifest_path, rows)
        counts[row["status"]] = counts.get(row["status"], 0) + 1
        seg = f", {row['segments']} segments" if row["segments"] else ""
        note = f"  {row['note']}" if row["note"] else ""
        print(f"      {row['status']} in {row['elapsed_s']}s{seg}{note}", flush=True)

    elapsed = time.perf_counter() - t_start
    print(f"\n=== {len(todo)} attempted in {elapsed/60:.1f} min ===")
    for k in ("ok", "failed", "timeout", "error"):
        if counts.get(k):
            print(f"  {k:8s} {counts[k]}")
    print(f"  manifest {manifest_path}")
    # Non-zero if anything failed, so a scheduled run can be noticed.
    return 0 if counts.get("ok") == len(todo) else 1


if __name__ == "__main__":
    raise SystemExit(main())
