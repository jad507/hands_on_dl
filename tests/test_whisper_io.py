"""
Tests for whisper_io.py.

Two schemas coexist here for good reason and neither may break the other: 78
transcripts already on disk are bare lists that can never be given provenance
retroactively, while every new transcript must carry it. The tests that matter
are the ones pinning that both load, and that the decoding parameters recorded
in provenance are the same object actually passed to the model.

Also verified: `audio_pipeline/align.py` reads through this loader, so a
provenance-carrying transcript does not silently align to zero segments.

Run:  python -m pytest tests/ -v
"""

import json

import pytest

import whisper_io


SEGMENTS = [
    {"start": 0.0, "end": 2.5, "text": "good evening everyone"},
    {"start": 2.5, "end": 6.0, "text": "i'll now call this meeting to order"},
]


# ------------------------------------------------------------ both schemas

def test_loads_legacy_bare_list(tmp_path):
    """The 78 transcripts already in downloads/whisper_large-v3 are bare lists.
    They predate provenance and cannot be given it retroactively, so they must
    keep loading forever."""
    p = tmp_path / "legacy.json"
    p.write_text(json.dumps(SEGMENTS), encoding="utf-8")
    assert whisper_io.load_segments(p) == SEGMENTS
    assert whisper_io.load_provenance(p) is None
    assert whisper_io.is_legacy(p)


def test_loads_current_schema_with_provenance(tmp_path):
    p = tmp_path / "current.json"
    prov = whisper_io.build_provenance(
        model_name="large-v3", compute_type="float16",
        decode_params={"beam_size": 10}, audio_path=p)
    whisper_io.write_transcript(p, SEGMENTS, prov)
    assert whisper_io.load_segments(p) == SEGMENTS
    assert whisper_io.load_provenance(p) is not None
    assert not whisper_io.is_legacy(p)


def test_round_trip_preserves_segments_exactly(tmp_path):
    p = tmp_path / "rt.json"
    whisper_io.write_transcript(p, SEGMENTS, {"x": 1})
    assert whisper_io.load_segments(p) == SEGMENTS


def test_unicode_survives_the_round_trip(tmp_path):
    """ensure_ascii=False plus explicit utf-8 on both ends. Council transcripts
    contain names that do not survive a mojibake round trip."""
    segs = [{"start": 0.0, "end": 1.0, "text": "Núñez said — quote ’"}]
    p = tmp_path / "u.json"
    whisper_io.write_transcript(p, segs, {})
    assert whisper_io.load_segments(p) == segs


# -------------------------------------------------------------- refusals

def test_dict_without_segments_key_raises(tmp_path):
    """Returning [] here would produce an empty transcript that propagates all
    the way into a result table before anyone notices."""
    p = tmp_path / "bad.json"
    p.write_text(json.dumps({"provenance": {}, "segs": SEGMENTS}), encoding="utf-8")
    with pytest.raises(ValueError, match="segments"):
        whisper_io.load_segments(p)


def test_unrecognised_type_raises(tmp_path):
    p = tmp_path / "weird.json"
    p.write_text(json.dumps("a string"), encoding="utf-8")
    with pytest.raises(ValueError):
        whisper_io.load_segments(p)


def test_empty_list_is_a_valid_transcript(tmp_path):
    """A meeting with no speech is legitimate; only a *malformed* file raises."""
    p = tmp_path / "empty.json"
    p.write_text("[]", encoding="utf-8")
    assert whisper_io.load_segments(p) == []


# ------------------------------------------------------------- provenance

def test_provenance_records_the_required_tuple(tmp_path):
    """windows_environment_upgrade.md section 6.1 names exactly what has to be
    in here: hostname, GPU, CUDA, ctranslate2, faster-whisper, compute_type,
    beam_size, best_of."""
    audio = tmp_path / "meeting.wav"
    audio.write_bytes(b"\0" * 1024)
    prov = whisper_io.build_provenance(
        model_name="large-v3", compute_type="float16",
        decode_params={"beam_size": 10, "best_of": 5},
        audio_path=audio)

    assert prov["asr"]["model"] == "large-v3"
    assert prov["asr"]["compute_type"] == "float16"
    assert prov["asr"]["beam_size"] == 10
    assert prov["asr"]["best_of"] == 5
    assert prov["audio"]["size_bytes"] == 1024
    assert prov["audio"]["name"] == "meeting.wav"
    for key in ("hostname", "platform", "python", "faster_whisper",
                "ctranslate2", "torch", "torch_cuda", "gpu"):
        assert key in prov["runtime"], f"missing runtime key {key}"
    assert "generated_utc" in prov


def test_provenance_survives_a_missing_audio_file(tmp_path):
    """Provenance must never be the reason a transcription run dies."""
    prov = whisper_io.build_provenance(
        model_name="large-v3", compute_type="float16",
        decode_params={}, audio_path=tmp_path / "nope.wav")
    assert prov["audio"]["size_bytes"] is None


def test_extra_audio_info_is_merged(tmp_path):
    prov = whisper_io.build_provenance(
        model_name="large-v3", compute_type="float16", decode_params={},
        audio_path=tmp_path / "a.wav",
        audio_info={"duration_s": 3600.5, "language": "en"})
    assert prov["audio"]["duration_s"] == 3600.5
    assert prov["audio"]["language"] == "en"


def test_describe_distinguishes_legacy_from_current(tmp_path):
    legacy = tmp_path / "l.json"
    legacy.write_text(json.dumps(SEGMENTS), encoding="utf-8")
    assert "LEGACY" in whisper_io.describe(legacy)

    current = tmp_path / "c.json"
    prov = whisper_io.build_provenance(
        model_name="large-v3", compute_type="float16",
        decode_params={"beam_size": 10}, audio_path=current)
    whisper_io.write_transcript(current, SEGMENTS, prov)
    assert "LEGACY" not in whisper_io.describe(current)
    assert "large-v3" in whisper_io.describe(current)


# ------------------------------------------------- consistency with the caller

def test_transcribe_decode_params_match_what_provenance_records():
    """DECODE_PARAMS is passed to model.transcribe() and written into
    provenance. If someone re-inlines the literals at the call site, the record
    stops describing the run and nothing complains. This test is the complaint.
    """
    import ast
    from pathlib import Path

    src = Path(__file__).resolve().parent.parent / "audio_pipeline" / "transcribe.py"
    tree = ast.parse(src.read_text(encoding="utf-8"))

    names = {t.id for node in ast.walk(tree)
             if isinstance(node, ast.Assign)
             for t in node.targets if isinstance(t, ast.Name)}
    assert "DECODE_PARAMS" in names, "transcribe.py no longer defines DECODE_PARAMS"

    text = src.read_text(encoding="utf-8")
    assert "model.transcribe(str(audio_path), **DECODE_PARAMS)" in text, (
        "transcribe() call no longer uses DECODE_PARAMS; provenance would "
        "record parameters that were not the ones used")
    assert "decode_params=DECODE_PARAMS" in text


def test_align_reads_through_the_loader():
    """align.py must not json.loads the transcript directly, or a
    provenance-carrying file aligns to nothing."""
    from pathlib import Path
    src = Path(__file__).resolve().parent.parent / "audio_pipeline" / "align.py"
    text = src.read_text(encoding="utf-8")
    assert "whisper_io.load_segments(whisper_path)" in text
    assert "json.loads(whisper_path.read_text" not in text
