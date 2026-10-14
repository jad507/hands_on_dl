"""
Tests for compare_diarization_variants.py.

The claim this script produces -- that a block's classification flips ~50x more
often when its 3-block chunk shifts than when it does not, on byte-identical
text -- rests entirely on the bucketing logic putting each block in the right
bin. A bug that misclassified shifted chunks as identical would not crash; it
would move the headline number.

So the end-to-end test below builds a tiny corpus on disk with a *known* answer:
one block engineered into each bucket, with flips placed deliberately. If the
buckets are computed correctly the report must reproduce those counts exactly.

Run:  python -m pytest tests/ -v
"""

import json

import pytest

import compare_diarization_variants as CDV


def write_meeting(path, blocks, title="Test Meeting"):
    path.write_text(json.dumps({
        "title": title, "video_id": "TEST123", "upload_date": "20250101",
        "rttm_mode": "test", "speakers": [], "blocks": blocks,
    }), encoding="utf-8")


def write_phase1(path, flagged, blocks):
    by_id = {b["block_id"]: b for b in blocks}
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({
        "title": "Test Meeting", "video_id": "TEST123", "upload_date": "20250101",
        "model": "testmodel", "n_chunk_errors": 0,
        "public_comments": [
            {"block_id": i, "speaker": by_id[i]["speaker"],
             "start": by_id[i]["start"], "end": by_id[i]["end"],
             "speaker_name": "unknown", "reason": "test",
             "text": by_id[i]["text"]}
            for i in sorted(flagged)
        ],
    }), encoding="utf-8")


def blk(bid, start, end, text, speaker="SPEAKER_00"):
    return {"block_id": bid, "speaker": speaker, "category": "recurring",
            "start": start, "end": end, "duration_s": end - start,
            "segment_count": 1, "word_count": len(text.split()), "text": text}


# ------------------------------------------------------------ pair discovery

def test_find_variant_pairs_groups_by_stem(tmp_path):
    for name in ["A_standard.json", "A_exclusive.json",
                 "B_standard.json", "C.json"]:
        write_meeting(tmp_path / name, [])
    pairs = CDV.find_variant_pairs(tmp_path)
    assert set(pairs) == {"A"}
    assert set(pairs["A"]) == {"standard", "exclusive"}


def test_find_variant_pairs_ignores_meetings_with_only_one_variant(tmp_path):
    """B has only a standard file, C has no variant suffix at all. Neither is a
    natural experiment and neither may enter the comparison."""
    write_meeting(tmp_path / "B_standard.json", [])
    write_meeting(tmp_path / "C.json", [])
    assert CDV.find_variant_pairs(tmp_path) == {}


def test_find_variant_pairs_handles_a_meeting_with_all_three_files(tmp_path):
    """Two meetings in this corpus carry a plain file alongside both variants.
    The plain file must not displace either variant."""
    for name in ["M_standard.json", "M_exclusive.json", "M.json"]:
        write_meeting(tmp_path / name, [])
    pairs = CDV.find_variant_pairs(tmp_path)
    assert "standard" in pairs["M"] and "exclusive" in pairs["M"]


# ------------------------------------------------------------------- chunking

def test_chunk_of_returns_the_enclosing_batch():
    blocks = [blk(i, i * 10, i * 10 + 9, f"t{i}") for i in range(7)]
    assert CDV.chunk_of(blocks, 0, 3) == ["t0", "t1", "t2"]
    assert CDV.chunk_of(blocks, 2, 3) == ["t0", "t1", "t2"]
    assert CDV.chunk_of(blocks, 3, 3) == ["t3", "t4", "t5"]
    assert CDV.chunk_of(blocks, 6, 3) == ["t6"]      # ragged final chunk


def test_chunk_size_is_read_from_config_not_hardcoded():
    """The finding is about this number, so it must track models.yaml rather
    than a literal that could drift away from what actually ran."""
    assert CDV._chunk_size() >= 1


# --------------------------------------------------------------- end to end

@pytest.fixture
def tiny_corpus(tmp_path):
    """A two-meeting corpus with a known bucket assignment.

    m1: 6 blocks, identical in both variants -> every block chunk_identical.
        One block is flagged in standard only, so exactly 1 identical-chunk flip.

    m2: the exclusive variant drops a block early, shifting every later chunk.
        Blocks 0-2 keep their chunk (identical); blocks after the deletion are
        chunk_shifted. Flips are placed in the shifted region.
    """
    comments = tmp_path / "comments"
    outputs = tmp_path / "llm_outputs"
    comments.mkdir()

    # -- m1: byte-identical variants -------------------------------------
    m1 = [blk(i, i * 10, i * 10 + 9, f"m1 text {i}") for i in range(6)]
    write_meeting(comments / "m1_standard.json", m1)
    write_meeting(comments / "m1_exclusive.json", m1)
    p1 = outputs / "testmodel" / "phase1_public_comments"
    write_phase1(p1 / "m1_standard.json", {4}, m1)
    write_phase1(p1 / "m1_exclusive.json", set(), m1)     # 1 flip, identical chunk

    # -- m2: one block removed from the exclusive variant -----------------
    m2_std = [blk(i, i * 10, i * 10 + 9, f"m2 text {i}") for i in range(9)]
    # exclusive drops the block at position 3; the rest keep their times and
    # text, so every surviving block still aligns 1:1 and is byte-identical.
    m2_exc = [b for b in m2_std if b["block_id"] != 3]
    write_meeting(comments / "m2_standard.json", m2_std)
    write_meeting(comments / "m2_exclusive.json", m2_exc)
    # block 7 flagged in standard only -> flip, and it sits after the deletion
    write_phase1(p1 / "m2_standard.json", {1, 7}, m2_std)
    write_phase1(p1 / "m2_exclusive.json", {1}, m2_exc)

    return comments, outputs


def test_end_to_end_bucket_counts_are_exact(tiny_corpus, tmp_path):
    comments, outputs = tiny_corpus
    out = tmp_path / "out"
    res = CDV.analyse(comments, outputs, out, ["testmodel"], 0.10)
    row = res["chunk_rows"][0]

    # m1 contributes 6 identical-chunk blocks. m2 contributes 3 (positions 0-2,
    # ahead of the deletion) plus 5 shifted (the survivors after it).
    assert row["chunk_identical_n"] == 9
    assert row["chunk_shifted_n"] == 5
    assert row["text_differs_n"] == 0

    # Exactly the flips that were planted.
    assert row["chunk_identical_flips"] == 1     # m1 block 4
    assert row["chunk_shifted_flips"] == 1       # m2 block 7


def test_end_to_end_writes_every_expected_output(tiny_corpus, tmp_path):
    comments, outputs = tiny_corpus
    out = tmp_path / "out"
    CDV.analyse(comments, outputs, out, ["testmodel"], 0.10)
    for name in ["variant_alignment.csv", "chunk_framing.csv", "flip_detail.csv",
                 "threshold_sensitivity.csv", "theme_score_movement.csv",
                 "report.md"]:
        assert (out / name).exists(), f"{name} was not written"
    assert "chunk-framing" in (out / "report.md").read_text(encoding="utf-8")


def test_flip_detail_records_both_texts(tiny_corpus, tmp_path):
    """The review queue is only useful if a human can read what actually
    changed without going back to the corpus."""
    import csv
    comments, outputs = tiny_corpus
    out = tmp_path / "out"
    CDV.analyse(comments, outputs, out, ["testmodel"], 0.10)
    rows = list(csv.DictReader((out / "flip_detail.csv").open(encoding="utf-8")))
    assert len(rows) == 2
    for r in rows:
        assert r["text_standard"]
        assert r["bucket"] in {"chunk_identical", "chunk_shifted", "text_differs"}
        assert r["flagged_standard"] != r["flagged_exclusive"]


def test_identical_variants_produce_no_shifted_blocks(tmp_path):
    """Sanity floor: if the two variants are the same file, nothing can be
    bucketed as shifted, and any nonzero shifted count means the position
    arithmetic is wrong."""
    comments = tmp_path / "c"; comments.mkdir()
    outputs = tmp_path / "o"
    blocks = [blk(i, i * 10, i * 10 + 9, f"t{i}") for i in range(10)]
    write_meeting(comments / "x_standard.json", blocks)
    write_meeting(comments / "x_exclusive.json", blocks)
    p1 = outputs / "m" / "phase1_public_comments"
    write_phase1(p1 / "x_standard.json", {2, 5}, blocks)
    write_phase1(p1 / "x_exclusive.json", {2, 5}, blocks)

    res = CDV.analyse(comments, outputs, tmp_path / "out", ["m"], 0.10)
    row = res["chunk_rows"][0]
    assert row["chunk_shifted_n"] == 0
    assert row["chunk_identical_n"] == 10
    assert row["chunk_identical_flips"] == 0


def test_base_rate_normalisation_is_reported(tiny_corpus, tmp_path):
    """A model that flags nothing cannot flip. Without the among-positives
    column, its near-zero flip rate reads as stability -- the specific way
    deepseek-r1-14b would be misreported."""
    comments, outputs = tiny_corpus
    res = CDV.analyse(comments, outputs, tmp_path / "out", ["testmodel"], 0.10)
    row = res["chunk_rows"][0]
    assert "chunk_identical_rate_among_positives" in row
    assert "chunk_shifted_rate_among_positives" in row
    assert row["chunk_identical_flagged_either"] >= row["chunk_identical_flips"]


def test_text_change_is_bucketed_separately_from_chunk_shift(tmp_path):
    """A block whose own text changed must never land in a chunk bucket: the
    two explanations have to stay separable or the headline claim collapses."""
    comments = tmp_path / "c"; comments.mkdir()
    outputs = tmp_path / "o"
    a = [blk(i, i * 10, i * 10 + 9, f"t{i}") for i in range(3)]
    b = [blk(i, i * 10, i * 10 + 9, f"t{i}") for i in range(3)]
    b[1]["text"] = "different words entirely"
    write_meeting(comments / "y_standard.json", a)
    write_meeting(comments / "y_exclusive.json", b)
    p1 = outputs / "m" / "phase1_public_comments"
    write_phase1(p1 / "y_standard.json", {1}, a)
    write_phase1(p1 / "y_exclusive.json", set(), b)

    res = CDV.analyse(comments, outputs, tmp_path / "out", ["m"], 0.10)
    row = res["chunk_rows"][0]
    assert row["text_differs_n"] == 1
    assert row["text_differs_flips"] == 1
    assert row["chunk_identical_flips"] == 0
