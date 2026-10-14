"""
Tests for analyze_chunk_context.py.

The load-bearing test here is `test_exogenous_test_detects_a_planted_effect`.
The script's headline conclusion is a *negative* result -- that the chunk-framing
effect has no detectable direction once neighbours are measured independently of
the model. A negative result from a test with no power is worthless, and a broken
test looks exactly like a true null. So the suite plants a directional effect in
synthetic data and requires the test to find it, then plants none and requires it
not to.

Run:  python -m pytest tests/ -v
"""

import hashlib
import json
import math

import pytest

import analyze_chunk_context as ACC


def blk(bid, start, end, text, category="recurring", speaker="SPEAKER_00"):
    return {"block_id": bid, "speaker": speaker, "category": category,
            "start": start, "end": end, "duration_s": end - start,
            "segment_count": 1, "word_count": len(text.split()), "text": text}


def write_meeting(path, blocks):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({
        "title": "T", "video_id": "V", "upload_date": "20250101",
        "rttm_mode": "x", "speakers": [], "blocks": blocks}), encoding="utf-8")


def write_phase1(path, flagged, blocks):
    by = {b["block_id"]: b for b in blocks}
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({
        "title": "T", "video_id": "V", "upload_date": "20250101",
        "model": "m", "n_chunk_errors": 0,
        "public_comments": [
            {"block_id": i, "speaker": by[i]["speaker"], "start": by[i]["start"],
             "end": by[i]["end"], "speaker_name": "unknown", "reason": "t",
             "text": by[i]["text"]} for i in sorted(flagged)]}),
        encoding="utf-8")


# ------------------------------------------------------------------ helpers

def test_mates_returns_the_other_blocks_in_the_same_chunk():
    blocks = [blk(i, i * 10, i * 10 + 9, f"t{i}") for i in range(7)]
    assert [b["block_id"] for b in ACC.mates(blocks, 0, 3)] == [1, 2]
    assert [b["block_id"] for b in ACC.mates(blocks, 1, 3)] == [0, 2]
    assert [b["block_id"] for b in ACC.mates(blocks, 3, 3)] == [4, 5]
    assert ACC.mates(blocks, 6, 3) == []          # ragged final chunk, alone


def test_mates_never_includes_the_block_itself():
    blocks = [blk(i, i * 10, i * 10 + 9, f"t{i}") for i in range(6)]
    for pos in range(6):
        ids = [b["block_id"] for b in ACC.mates(blocks, pos, 3)]
        assert blocks[pos]["block_id"] not in ids


def test_binom_z_signs_and_scale():
    assert ACC.binom_z(50, 100) == pytest.approx(0.0)
    assert ACC.binom_z(100, 100) == pytest.approx(10.0)
    assert ACC.binom_z(0, 100) == pytest.approx(-10.0)
    assert math.isnan(ACC.binom_z(0, 0))


def test_variant_pairs_requires_both_sides(tmp_path):
    write_meeting(tmp_path / "a_standard.json", [])
    write_meeting(tmp_path / "a_exclusive.json", [])
    write_meeting(tmp_path / "b_standard.json", [])
    assert set(ACC.variant_pairs(tmp_path)) == {"a"}


# ------------------------------------------- power check on synthetic data

def build_corpus(tmp_path, directional: bool, n_meetings: int = 40):
    """Build variant pairs where the exclusive side drops one early block, so
    every later block lands in differently-composed chunks.

    When `directional` is True the model's flag follows the number of
    `commenter_candidate` neighbours in the chunk -- the exact effect Test 2
    exists to detect. When False the flag flips on an arbitrary but neighbour
    independent rule, so Test 2 should find nothing.
    """
    comments = tmp_path / "comments"
    outputs = tmp_path / "out"
    p1 = outputs / "m" / "phase1_public_comments"

    for n in range(n_meetings):
        # alternate categories so chunk composition genuinely varies
        blocks = [blk(i, i * 10, i * 10 + 9, f"m{n} t{i}",
                      category="commenter_candidate" if (i % 3 == 0) else "recurring")
                  for i in range(12)]
        A = blocks
        B = [b for b in blocks if b["block_id"] != 1]      # drop one, shift the rest
        write_meeting(comments / f"m{n}_standard.json", A)
        write_meeting(comments / f"m{n}_exclusive.json", B)

        def flags(seq, side):
            out = set()
            for pos, b in enumerate(seq):
                if directional:
                    # flag follows the exogenous neighbour property exactly
                    cc = sum(1 for x in ACC.mates(seq, pos, 3)
                             if x.get("category") == "commenter_candidate")
                    if cc >= 1:
                        out.add(b["block_id"])
                else:
                    # Pseudo-random in (meeting, block, side). Keyed on block
                    # IDENTITY, never on position, so the block deletion cannot
                    # induce a systematic relationship with chunk composition --
                    # which is exactly what a position-parity rule would do, and
                    # would masquerade as a (negative) directional effect.
                    # hashlib, not hash(): the builtin is salted per process
                    # unless PYTHONHASHSEED is set, which would make this test
                    # pass or fail depending on the run.
                    h = hashlib.sha256(
                        f"{n}:{b['block_id']}:{side}".encode()).digest()[0]
                    if h % 5 == 0:
                        out.add(b["block_id"])
            return out

        write_phase1(p1 / f"m{n}_standard.json", flags(A, "s"), A)
        write_phase1(p1 / f"m{n}_exclusive.json", flags(B, "e"), B)

    return comments, outputs


def test_exogenous_test_detects_a_planted_effect(tmp_path):
    """Power check. If the flag is generated from the neighbours' exogenous
    category, Test 2 must come back strongly concordant.

    Without this, the script's real-data null is indistinguishable from a test
    that cannot detect anything."""
    comments, outputs = build_corpus(tmp_path, directional=True)
    res = ACC.run(comments, outputs, tmp_path / "r", ["m"])
    exo = res["exogenous"]
    total = exo["concordant"] + exo["discordant"]
    assert total >= 20, "planted design produced too few comparable blocks"
    rate = exo["concordant"] / total
    assert rate > 0.85, f"planted directional effect not detected (rate={rate:.2f})"


def test_exogenous_test_finds_nothing_when_there_is_nothing(tmp_path):
    """Specificity check: a flag rule independent of the neighbours must not
    produce concordance."""
    comments, outputs = build_corpus(tmp_path, directional=False)
    res = ACC.run(comments, outputs, tmp_path / "r", ["m"])
    exo = res["exogenous"]
    total = exo["concordant"] + exo["discordant"]
    if total >= 20:
        z = ACC.binom_z(exo["concordant"], total)
        assert abs(z) < 3.0, f"spurious directional signal, z={z:.2f}"


def test_run_writes_its_outputs(tmp_path):
    comments, outputs = build_corpus(tmp_path, directional=True, n_meetings=5)
    out = tmp_path / "r"
    ACC.run(comments, outputs, out, ["m"])
    assert (out / "chunk_context_report.md").exists()
    assert (out / "chunk_context_detail.csv").exists()
    text = (out / "chunk_context_report.md").read_text(encoding="utf-8")
    assert "exogenous" in text.lower()


def test_blocks_with_changed_text_are_excluded(tmp_path):
    """A block whose own text changed is not a clean test of chunk company and
    must not enter either within-block design."""
    comments = tmp_path / "c"
    outputs = tmp_path / "o"
    A = [blk(i, i * 10, i * 10 + 9, f"t{i}",
             category="commenter_candidate" if i == 0 else "recurring")
         for i in range(6)]
    B = [dict(b) for b in A]
    B[4]["text"] = "completely different"
    write_meeting(comments / "x_standard.json", A)
    write_meeting(comments / "x_exclusive.json", B)
    p1 = outputs / "m" / "phase1_public_comments"
    write_phase1(p1 / "x_standard.json", {4}, A)
    write_phase1(p1 / "x_exclusive.json", set(), B)

    res = ACC.run(comments, outputs, tmp_path / "r", ["m"])
    # block 4 is the only flip and its text changed, so nothing may be counted
    assert res["exogenous"]["concordant"] + res["exogenous"]["discordant"] == 0
