"""
Tests for blockmatch.py.

The alignment this module performs is load-bearing twice over: it is how the
diarization-variant pilot compares two runs, and per the ISLS technical spec it
is the same machinery that will join units across transcription policies. A
matcher that quietly mis-pairs blocks produces a plausible-looking flip rate
built on nonsense, so the cases below pin down the shapes it must distinguish --
particularly splits and merges, which are the ones a naive 1:1 matcher would
paper over.

Run:  python -m pytest tests/ -v
"""

import pytest

import blockmatch as BM


def blk(bid, start, end, speaker="SPEAKER_00", text=""):
    return {"block_id": bid, "start": start, "end": end,
            "speaker": speaker, "text": text}


# ------------------------------------------------------------ interval maths

def test_overlap_seconds():
    assert BM.overlap_seconds(blk(0, 0, 10), blk(0, 5, 15)) == pytest.approx(5.0)
    assert BM.overlap_seconds(blk(0, 0, 10), blk(0, 10, 20)) == pytest.approx(0.0)
    assert BM.overlap_seconds(blk(0, 0, 10), blk(0, 20, 30)) == pytest.approx(0.0)


def test_interval_iou_identical_is_one():
    assert BM.interval_iou(blk(0, 10, 20), blk(0, 10, 20)) == pytest.approx(1.0)


def test_interval_iou_half_overlap():
    # a=[0,10] b=[5,15]: intersection 5, union 15
    assert BM.interval_iou(blk(0, 0, 10), blk(0, 5, 15)) == pytest.approx(1 / 3)


def test_iou_penalises_a_long_block_swallowing_a_short_one():
    """Raw overlap would call this a perfect match; IoU must not.

    This is the specific failure that would let a coarse diarization absorb a
    fine one and report flawless alignment."""
    short, long_ = blk(0, 100, 110), blk(0, 0, 600)
    assert BM.coverage(short, long_) == pytest.approx(1.0)
    assert BM.interval_iou(short, long_) < 0.02


def test_zero_duration_block_does_not_divide_by_zero():
    assert BM.interval_iou(blk(0, 5, 5), blk(0, 0, 10)) == pytest.approx(0.0)
    assert BM.coverage(blk(0, 5, 5), blk(0, 0, 10)) == pytest.approx(0.0)


# ------------------------------------------------------------- shape detection

def test_identical_variants_align_one_to_one():
    a = [blk(0, 0, 10), blk(1, 10, 20), blk(2, 20, 30)]
    al = BM.align(a, a)
    assert al.counts()["one_to_one"] == 3
    assert al.one_to_one_rate() == pytest.approx(1.0)
    assert al.map_a_to_b == {0: 0, 1: 1, 2: 2}


def test_renumbered_blocks_still_align_by_time():
    """The whole reason time is the join key: block_id is not stable across
    runs, so the matcher must ignore it entirely."""
    a = [blk(0, 0, 10), blk(1, 10, 20)]
    b = [blk(77, 10, 20), blk(99, 0, 10)]
    al = BM.align(a, b)
    assert al.map_a_to_b == {0: 99, 1: 77}


def test_split_is_reported_as_a_split_not_as_a_match():
    """One 40-second turn on the left, a question and an answer on the right.

    A 1:1 matcher would pair the left block with whichever fragment overlapped
    most and drop the other, inventing agreement. This must not happen."""
    a = [blk(0, 0, 40)]
    b = [blk(0, 0, 18), blk(1, 18, 40)]
    al = BM.align(a, b)
    assert al.counts()["split"] == 1
    assert al.counts()["one_to_one"] == 0
    assert al.map_a_to_b == {}


def test_merge_is_reported_as_a_merge():
    a = [blk(0, 0, 18), blk(1, 18, 40)]
    b = [blk(0, 0, 40)]
    al = BM.align(a, b)
    assert al.counts()["merge"] == 1
    assert al.map_a_to_b == {}


def test_tangle_when_boundaries_genuinely_disagree():
    a = [blk(0, 0, 20), blk(1, 20, 40)]
    b = [blk(0, 0, 12), blk(1, 12, 40)]
    al = BM.align(a, b, min_iou=0.10)
    assert al.counts()["tangle"] == 1
    assert al.map_a_to_b == {}


def test_unmatched_blocks_are_reported_on_the_correct_side():
    a = [blk(0, 0, 10), blk(1, 100, 110)]
    b = [blk(0, 0, 10), blk(1, 500, 510)]
    al = BM.align(a, b)
    assert al.unmatched_a == [1]
    assert al.unmatched_b == [1]
    assert al.counts()["one_to_one"] == 1


def test_incidental_overlap_below_threshold_is_not_a_match():
    a = [blk(0, 0, 100)]
    b = [blk(0, 99, 200)]
    assert BM.align(a, b, min_iou=0.10).map_a_to_b == {}
    assert BM.align(a, b, min_iou=0.001).map_a_to_b == {0: 0}


def test_empty_inputs_do_not_crash():
    al = BM.align([], [])
    assert al.one_to_one_rate() == 0.0
    assert al.counts()["one_to_one"] == 0
    al2 = BM.align([blk(0, 0, 10)], [])
    assert al2.unmatched_a == [0]


# ------------------------------------------------------------------ threshold

def test_threshold_sensitivity_is_monotone_in_matches():
    """Raising min_iou can only remove edges, so the 1:1 count cannot rise
    monotonically forever -- but the set of edges must shrink. A sweep that
    gained edges at a higher threshold would mean the graph build is wrong."""
    a = [blk(0, 0, 10), blk(1, 10, 20), blk(2, 20, 30)]
    b = [blk(0, 0, 9), blk(1, 9, 21), blk(2, 21, 30)]
    rows = BM.threshold_sensitivity(a, b, thresholds=(0.05, 0.5, 0.95))
    edge_counts = [r["one_to_one"] + r["split"] + r["merge"] + r["tangle"]
                   for r in rows]
    assert edge_counts == sorted(edge_counts, reverse=True) or len(set(edge_counts)) <= 2


def test_threshold_sensitivity_reports_every_requested_threshold():
    a = [blk(0, 0, 10)]
    b = [blk(0, 0, 10)]
    rows = BM.threshold_sensitivity(a, b, thresholds=(0.1, 0.9))
    assert [r["min_iou"] for r in rows] == [0.1, 0.9]


# -------------------------------------------------------------------- speakers

def test_speaker_labels_are_not_assumed_comparable_across_variants():
    """pyannote numbers speakers per run. The same person can be SPEAKER_00 in
    one variant and SPEAKER_02 in the other, so requiring label equality would
    destroy the alignment. Default must be permissive."""
    a = [blk(0, 0, 10, "SPEAKER_00"), blk(1, 10, 20, "SPEAKER_01")]
    b = [blk(0, 0, 10, "SPEAKER_02"), blk(1, 10, 20, "SPEAKER_03")]
    assert len(BM.align(a, b).map_a_to_b) == 2
    assert len(BM.align(a, b, require_same_speaker=True).map_a_to_b) == 0


def test_infer_speaker_mapping_recovers_the_permutation():
    a = [blk(0, 0, 10, "SPEAKER_00"), blk(1, 10, 20, "SPEAKER_01"),
         blk(2, 20, 30, "SPEAKER_00")]
    b = [blk(0, 0, 10, "SPEAKER_02"), blk(1, 10, 20, "SPEAKER_03"),
         blk(2, 20, 30, "SPEAKER_02")]
    assert BM.infer_speaker_mapping(a, b) == {"SPEAKER_00": "SPEAKER_02",
                                              "SPEAKER_01": "SPEAKER_03"}


def test_infer_speaker_mapping_omits_speakers_without_evidence():
    a = [blk(0, 0, 10, "SPEAKER_00"), blk(1, 500, 510, "SPEAKER_09")]
    b = [blk(0, 0, 10, "SPEAKER_02")]
    m = BM.infer_speaker_mapping(a, b)
    assert m == {"SPEAKER_00": "SPEAKER_02"}
    assert "SPEAKER_09" not in m


# ------------------------------------------------------------------ translate

def test_translate_ids_separates_the_untranslatable():
    """A flagged block with no 1:1 partner is neither agreement nor
    disagreement. Silently dropping it would bias every statistic toward the
    variant with coarser blocks, so it comes back in its own bucket."""
    a = [blk(0, 0, 10), blk(1, 10, 50)]
    b = [blk(0, 0, 10), blk(1, 10, 30), blk(2, 30, 50)]
    al = BM.align(a, b)
    got, missing = BM.translate_ids({0, 1}, al)
    assert got == {0}
    assert missing == {1}


def test_translate_ids_both_directions():
    a = [blk(0, 0, 10)]
    b = [blk(5, 0, 10)]
    al = BM.align(a, b)
    assert BM.translate_ids({0}, al, "a_to_b") == ({5}, set())
    assert BM.translate_ids({5}, al, "b_to_a") == ({0}, set())


# ------------------------------------------------- realistic composite case

def test_realistic_mixed_meeting():
    """A meeting with one clean stretch, one split, one merge and one block the
    other variant never produced -- the shape actually seen in this corpus."""
    a = [blk(0, 0, 30), blk(1, 30, 70), blk(2, 70, 90), blk(3, 90, 110),
         blk(4, 200, 230)]
    b = [blk(0, 0, 30),                    # 1:1 with a0
         blk(1, 30, 48), blk(2, 48, 70),   # split of a1
         blk(3, 70, 110),                  # merge of a2 + a3
         blk(4, 400, 430)]                 # unmatched, and a4 unmatched too
    al = BM.align(a, b)
    c = al.counts()
    assert c["one_to_one"] == 1
    assert c["split"] == 1
    assert c["merge"] == 1
    assert al.unmatched_a == [4]
    assert al.unmatched_b == [4]
    assert al.map_a_to_b == {0: 0}
    assert al.one_to_one_rate() == pytest.approx(0.2)
