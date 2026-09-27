"""
Tests for export_vtt.py.

The export has one job that matters: send Concord N blocks and get N units back.
Everything else is formatting. So the tests concentrate on the three ways N can
silently change during import, each of which was read out of Concord's source
rather than guessed:

  1. `stripTags` deletes anything in angle brackets, with no error.
  2. `mergeCues` fuses same-speaker cues, and its test is `gap <= max`, so
     maxMergeGapSeconds = 0 does NOT disable merging.
  3. A speaker label that Concord cannot parse produces `null`, which coerces to
     the string "Speaker" -- and then every anonymous cue shares a speaker.

The last group drives the real Concord checkout end to end, and skips without it.

Run:  python -m pytest tests/ -v
"""

import json
import shutil
import subprocess
from pathlib import Path

import pytest

import export_vtt as EV

REPO = Path(__file__).resolve().parent.parent
CONCORD = REPO.parent / "concord"


def blk(bid, start, end, text, speaker="SPEAKER_00"):
    return {"block_id": bid, "speaker": speaker, "category": "recurring",
            "start": start, "end": end, "duration_s": end - start,
            "segment_count": 1, "word_count": len(text.split()), "text": text}


# ------------------------------------------------------------- timestamps

def test_timestamp_format():
    assert EV.fmt_timestamp(0) == "00:00:00.000"
    assert EV.fmt_timestamp(1.5) == "00:00:01.500"
    assert EV.fmt_timestamp(61.25) == "00:01:01.250"
    assert EV.fmt_timestamp(3661.007) == "01:01:01.007"


def test_timestamp_rounds_rather_than_truncates():
    """A truncating formatter drifts the anchor by up to a millisecond per cue,
    and the anchor is the only join key that survives a policy change."""
    assert EV.fmt_timestamp(1.0009) == "00:00:01.001"


def test_negative_timestamp_is_clamped():
    assert EV.fmt_timestamp(-5) == "00:00:00.000"


# -------------------------------------------------------------- sanitize

def test_angle_brackets_are_replaced_not_dropped():
    """stripTags would delete the whole span between < and >. Substituting the
    fullwidth forms keeps the characters visible; dropping them would lose text
    the transcript deliberately recorded."""
    text, n = EV.sanitize("he said <inaudible> then left")
    assert n == 2
    assert "<" not in text and ">" not in text
    assert "inaudible" in text


def test_sanitize_leaves_clean_text_untouched():
    text, n = EV.sanitize("nothing to escape here")
    assert n == 0
    assert text == "nothing to escape here"


# ---------------------------------------------------------------- speakers

def test_pyannote_labels_are_accepted():
    assert EV.SPEAKER_OK.match("SPEAKER_00")
    assert EV.SPEAKER_OK.match("Speaker")


def test_lowercase_labels_are_flagged():
    """Doc 03: the label must start with a capital. speaker_00 does not."""
    assert not EV.SPEAKER_OK.match("speaker_00")


def test_overlong_labels_are_flagged():
    assert not EV.SPEAKER_OK.match("A" * 42)


def test_invalid_speaker_labels_are_reported_not_silently_fixed():
    blocks = [blk(0, 0, 5, "hello", speaker="speaker_00")]
    _, _, stats = EV.build_vtt(blocks)
    assert stats["invalid_speaker_labels"] == ["speaker_00"]


# ------------------------------------------------------------------ merging

def test_zero_is_not_a_safe_merge_gap():
    """The single most surprising thing in Concord's ingest: mergeCues tests
    `gap <= maxMergeGapSeconds`, so two cues abutting exactly still merge at 0.
    Only a negative value disables merging."""
    assert EV.NO_MERGE_GAP_SECONDS < 0


def test_same_speaker_adjacency_is_reported_with_its_gap():
    blocks = [blk(0, 0, 10, "one"), blk(1, 12, 20, "two"),
              blk(2, 25, 30, "three", speaker="SPEAKER_01")]
    _, _, stats = EV.build_vtt(blocks)
    pairs = stats["same_speaker_adjacent_pairs"]
    assert len(pairs) == 1
    assert pairs[0]["gap_s"] == pytest.approx(2.0)
    assert stats["would_merge_at_concord_default_30s"] == 1


def test_a_large_gap_is_not_at_risk_at_the_default():
    blocks = [blk(0, 0, 10, "one"), blk(1, 100, 110, "two")]
    _, _, stats = EV.build_vtt(blocks)
    assert stats["would_merge_at_concord_default_30s"] == 0


# ------------------------------------------------------------------- output

def test_one_cue_per_block_with_a_voice_tag():
    blocks = [blk(0, 0, 5, "first"), blk(1, 10, 15, "second", "SPEAKER_01")]
    vtt, manifest, stats = EV.build_vtt(blocks)
    assert vtt.startswith("WEBVTT")
    assert vtt.count("-->") == 2
    assert "<v SPEAKER_00>first" in vtt
    assert "<v SPEAKER_01>second" in vtt
    assert stats["n_cues"] == 2
    assert [m["block_id"] for m in manifest] == [0, 1]


def test_empty_blocks_are_skipped_and_counted():
    """Concord drops empty cues anyway; counting them here means the manifest's
    cue count still matches what Concord will produce."""
    blocks = [blk(0, 0, 5, "real"), blk(1, 6, 7, "   ")]
    _, manifest, stats = EV.build_vtt(blocks)
    assert stats["n_cues"] == 1
    assert stats["n_empty_skipped"] == 1
    assert len(manifest) == 1


def test_manifest_carries_the_time_anchor():
    """Unit ids are content hashes and change with the transcription policy, so
    the manifest has to carry what survives: speaker plus start/end."""
    blocks = [blk(7, 12.5, 30.25, "text here", "SPEAKER_03")]
    _, manifest, _ = EV.build_vtt(blocks)
    m = manifest[0]
    assert m["block_id"] == 7
    assert m["speaker"] == "SPEAKER_03"
    assert m["start"] == pytest.approx(12.5)
    assert m["end"] == pytest.approx(30.25)


def test_export_one_writes_vtt_and_manifest(tmp_path):
    src = tmp_path / "Test Meeting [abc123].json"
    src.write_text(json.dumps({
        "title": "Test Meeting", "video_id": "abc123", "rttm_mode": "standard",
        "blocks": [blk(0, 0, 5, "hello"), blk(1, 10, 15, "world", "SPEAKER_01")],
    }), encoding="utf-8")
    out = tmp_path / "vtt"
    stats = EV.export_one(src, out)
    assert (out / "Test Meeting [abc123].vtt").exists()
    man = json.loads((out / "Test Meeting [abc123].manifest.json").read_text(encoding="utf-8"))
    assert man["concord_import"]["maxMergeGapSeconds"] == EV.NO_MERGE_GAP_SECONDS
    assert man["concord_import"]["scheme"] == "turn"
    assert stats["n_cues"] == 2


def test_legacy_schema_blocks_are_exportable(tmp_path):
    """The two stale commenter_blocks files still have to export, or the
    corpus-wide run dies partway through."""
    src = tmp_path / "Legacy.json"
    src.write_text(json.dumps({
        "title": "Legacy", "commenter_blocks": [blk(0, 0, 5, "hi")],
    }), encoding="utf-8")
    stats = EV.export_one(src, tmp_path / "out")
    assert stats["n_cues"] == 1


# ------------------------------------------------- real Concord round trip

concord_only = pytest.mark.skipif(
    shutil.which("node") is None
    or not (CONCORD / "server" / "ingest" / "transcript.js").is_file(),
    reason="node or the concord checkout is not available",
)


@concord_only
def test_round_trip_preserves_turn_count(tmp_path):
    """The whole point of the exporter, checked against the real parser."""
    blocks = [blk(i, i * 20, i * 20 + 15, f"block number {i}",
                  speaker=f"SPEAKER_0{i % 3}") for i in range(12)]
    src = tmp_path / "RT.json"
    src.write_text(json.dumps({"title": "RT", "blocks": blocks}), encoding="utf-8")
    out = tmp_path / "vtt"
    EV.export_one(src, out)

    r = subprocess.run(
        ["node", str(REPO / "tools" / "concord_roundtrip.mjs"), str(CONCORD), str(out)],
        capture_output=True, text=True, timeout=120)
    assert r.returncode == 0, r.stderr[-2000:]
    res = json.loads(r.stdout)[0]
    assert res["cues"] == 12
    assert res["turns"] == 12
    assert res["units_turn_scheme"] == 12
    assert res["cues_without_speaker"] == 0
    assert res["issues"] == []
    assert res["ok"]


def _turns_at(out_dir, gap):
    r = subprocess.run(
        ["node", str(REPO / "tools" / "concord_roundtrip.mjs"),
         str(CONCORD), str(out_dir), str(gap)],
        capture_output=True, text=True, timeout=120)
    assert r.returncode == 0, r.stderr[-2000:]
    return json.loads(r.stdout)[0]["turns"]


def _export(tmp_path, blocks, name="M"):
    src = tmp_path / f"{name}.json"
    src.write_text(json.dumps({"title": name, "blocks": blocks}), encoding="utf-8")
    out = tmp_path / name
    EV.export_one(src, out)
    return out


@concord_only
def test_concord_default_gap_really_does_merge(tmp_path):
    """Not a hypothetical: two same-speaker blocks 2 s apart become ONE turn at
    Concord's 30 s default. This is the case the exporter warns about, and 11
    such pairs exist in the real corpus."""
    out = _export(tmp_path, [blk(0, 0, 10, "first part"),
                             blk(1, 12, 20, "second part")], "gap2")
    assert _turns_at(out, 30) == 1, "the default should fuse these"
    assert _turns_at(out, -1) == 2, "-1 must preserve the block spine"
    # A 2 s gap is genuinely larger than 0, so 0 also holds here. The case
    # where 0 fails is the next test.
    assert _turns_at(out, 0) == 2


@concord_only
def test_zero_gap_is_unsafe_only_when_cues_abut_exactly(tmp_path):
    """The precise claim behind NO_MERGE_GAP_SECONDS = -1.

    mergeCues tests `gap <= maxMergeGapSeconds`. When one block ends exactly
    where the next begins -- gap 0.0, which diarization produces routinely --
    `0 <= 0` is true and the two fuse even at maxMergeGapSeconds = 0. Only a
    negative value is safe in general, and this is the case that proves it."""
    out = _export(tmp_path, [blk(0, 0, 10, "first part"),
                             blk(1, 10, 20, "second part")], "gap0")
    assert _turns_at(out, 30) == 1
    assert _turns_at(out, 0) == 1, "0 fuses exactly-abutting cues -- the whole point"
    assert _turns_at(out, -1) == 2, "-1 is the only value that preserves them"


@concord_only
def test_angle_bracket_text_survives_the_round_trip(tmp_path):
    """Unsanitized, `he said <inaudible> then left` loses the middle word at
    import. Sanitized, nothing is lost."""
    blocks = [blk(0, 0, 10, "he said <inaudible> then left")]
    src = tmp_path / "A.json"
    src.write_text(json.dumps({"title": "A", "blocks": blocks}), encoding="utf-8")
    out = tmp_path / "vtt"
    EV.export_one(src, out)
    text = (out / "A.vtt").read_text(encoding="utf-8")
    cue = [ln for ln in text.splitlines() if ln.startswith("<v ")][0]
    assert "inaudible" in cue
    # The only angle brackets left on the cue line are the voice tag's own.
    # (The timestamp line contains "-->", which is why this checks the cue
    # line rather than the whole file.)
    assert cue.count("<") == 1 and cue.count(">") == 1
