"""
Tests for agreement.py.

The reason these tests are worth their weight: the reliability statistics in
`agreement.py` are hand-implemented rather than imported, so nothing but a test
against published reference values distinguishes a correct implementation from
a plausible one. A wrong Krippendorff's alpha does not raise; it returns a
number that goes into a paper.

Reference values used here:

  Krippendorff's alpha -- the worked example distributed with the `krippendorff`
  Python package and derived from Krippendorff (2011), which reports
  alpha_nominal = 0.691 and alpha_interval = 0.811 for the matrix below.

  Gwet's AC1 -- the 2x2 table from Gwet (2008) that demonstrates the
  high-agreement paradox: 118 units both raters call positive, 5 and 2 units of
  disagreement, 0 units both call negative. Gwet reports AC1 = 0.9410 while
  kappa goes negative on the same data.

Run:  python -m pytest tests/ -v
"""

import math

import pytest

import agreement as A

N = None

# Krippendorff (2011) worked example: 3 raters, 15 units, missing data.
KRIPP_MATRIX = [
    [N, N, N, N, N, 3, 4, 1, 2, 1, 1, 3, 3, N, 3],
    [1, N, 2, 1, 3, 3, 4, 3, N, N, N, N, N, N, N],
    [N, N, 2, 1, 3, 4, 4, N, 2, 1, 1, 3, 3, N, 4],
]


def gwet_paradox_matrix():
    """Gwet's 2x2 high-agreement table as a 2-rater reliability matrix."""
    a, b = [], []
    for _ in range(118):
        a.append(1); b.append(1)
    for _ in range(5):
        a.append(1); b.append(0)
    for _ in range(2):
        a.append(0); b.append(1)
    return [a, b]


# ---------------------------------------------------------------- Krippendorff

def test_krippendorff_nominal_matches_published_value():
    alpha = A.krippendorff_alpha(KRIPP_MATRIX, A.delta_nominal)
    assert alpha == pytest.approx(0.691, abs=0.001)


def test_krippendorff_interval_matches_published_value():
    alpha = A.krippendorff_alpha(KRIPP_MATRIX, A.delta_interval)
    assert alpha == pytest.approx(0.811, abs=0.001)


def test_krippendorff_perfect_agreement_is_one():
    m = [[1, 0, 1, 0, 1], [1, 0, 1, 0, 1], [1, 0, 1, 0, 1]]
    assert A.krippendorff_alpha(m) == pytest.approx(1.0)


def test_krippendorff_is_one_when_everyone_says_the_same_thing():
    """Degenerate case: no variance at all. De is 0, so alpha is 1 by
    convention rather than 0/0. This is not a hypothetical -- a model that
    flags nothing in a meeting produces exactly this column."""
    m = [[0, 0, 0, 0], [0, 0, 0, 0]]
    assert A.krippendorff_alpha(m) == pytest.approx(1.0)


def test_krippendorff_systematic_disagreement_is_negative():
    """Two raters that invert each other do worse than chance."""
    m = [[1, 0, 1, 0, 1, 0], [0, 1, 0, 1, 0, 1]]
    alpha = A.krippendorff_alpha(m)
    assert alpha is not None and alpha < 0


def test_krippendorff_drops_units_with_one_rating():
    """Units only one rater saw carry no pairable information. Adding such a
    column must not move the statistic."""
    base = [[1, 0, 1], [1, 0, 1]]
    padded = [[1, 0, 1, 1], [1, 0, 1, N]]
    assert A.krippendorff_alpha(base) == pytest.approx(A.krippendorff_alpha(padded))


def test_krippendorff_returns_none_without_pairable_data():
    assert A.krippendorff_alpha([[1, N], [N, 1]]) is None
    assert A.krippendorff_alpha([]) is None


def test_krippendorff_rejects_ragged_matrix():
    with pytest.raises(ValueError):
        A.krippendorff_alpha([[1, 0, 1], [1, 0]])


# ----------------------------------------------------------------- Gwet's AC1

def test_gwet_ac1_matches_published_value():
    ac1 = A.gwet_ac1(gwet_paradox_matrix())
    assert ac1 == pytest.approx(0.941, abs=0.001)


def test_kappa_goes_negative_where_ac1_stays_high():
    """The high-agreement paradox, which is the whole reason AC1 is used here.

    Same data, two chance corrections: raters agree on 94.4% of units, AC1 says
    0.94, kappa says below zero. If this test ever fails, the argument for
    reporting AC1 on this corpus has to be re-made from scratch."""
    m = gwet_paradox_matrix()
    p_agree = sum(1 for x, y in zip(m[0], m[1]) if x == y) / len(m[0])
    assert p_agree == pytest.approx(0.944, abs=0.001)
    assert A.gwet_ac1(m) > 0.9
    assert A.fleiss_kappa(m) < 0


def test_gwet_ac1_perfect_agreement_is_one():
    m = [[1, 0, 1, 0], [1, 0, 1, 0]]
    assert A.gwet_ac1(m) == pytest.approx(1.0)


def test_gwet_ac1_single_category_is_one():
    assert A.gwet_ac1([[0, 0, 0], [0, 0, 0]]) == pytest.approx(1.0)


def test_gwet_ac1_handles_missing_and_more_than_two_raters():
    m = [[1, 1, 0, N], [1, 1, 0, 0], [1, 0, 0, 0]]
    ac1 = A.gwet_ac1(m)
    assert ac1 is not None and -1.0 <= ac1 <= 1.0


def test_gwet_ac1_returns_none_without_pairable_data():
    assert A.gwet_ac1([[1, N], [N, 1]]) is None


# -------------------------------------------------------------------- Jaccard

def test_jaccard_basics():
    assert A.jaccard({1, 2, 3}, {1, 2, 3}) == pytest.approx(1.0)
    assert A.jaccard({1, 2}, {3, 4}) == pytest.approx(0.0)
    assert A.jaccard({1, 2, 3}, {2, 3, 4}) == pytest.approx(0.5)


def test_jaccard_of_two_empty_sets_is_none_not_one():
    """Two models that both flagged nothing have agreed about nothing. Scoring
    that as 1.0 inflates the macro-average across a corpus where many meetings
    contain no public comment -- which is the specific way the recovered
    compare_model_agreement.py could have been read as overstating agreement.
    It happened to skip those pairs; this makes the choice explicit."""
    assert A.jaccard(set(), set()) is None


def test_jaccard_with_one_empty_set_is_zero():
    assert A.jaccard({1, 2}, set()) == pytest.approx(0.0)


def test_dice_is_at_least_jaccard():
    a, b = {1, 2, 3, 4}, {3, 4, 5}
    assert A.dice(a, b) >= A.jaccard(a, b)
    assert A.dice(set(), set()) is None


# ------------------------------------------------- matrix construction helpers

def test_matrix_from_flag_sets_covers_the_negative_class():
    """The universe of units must include unflagged ones, or every
    chance-corrected statistic is computed on a population with no negatives."""
    units = [0, 1, 2, 3, 4]
    flags = {"m1": {1, 3}, "m2": {1, 4}}
    names, m = A.matrix_from_flag_sets(units, flags)
    assert names == ["m1", "m2"]
    assert m[0] == [0, 1, 0, 1, 0]
    assert m[1] == [0, 1, 0, 0, 1]


def test_matrix_from_flag_sets_marks_unseen_units_missing():
    """A model that never ran on a meeting must produce None, not 0. Recording
    it as 0 would count a missing run as a confident negative -- the failure
    that matters most here, because phase 2 is incomplete for five of seven
    models."""
    units = [0, 1, 2]
    flags = {"m1": {1}, "m2": {1}}
    rated = {"m1": {0, 1, 2}, "m2": {1}}
    _, m = A.matrix_from_flag_sets(units, flags, rated=rated)
    assert m[0] == [0, 1, 0]
    assert m[1] == [None, 1, None]


def test_matrix_from_flag_sets_respects_rater_order():
    units = [0, 1]
    flags = {"b": {0}, "a": {1}}
    names, m = A.matrix_from_flag_sets(units, flags, rater_order=["b", "a"])
    assert names == ["b", "a"]
    assert m[0] == [1, 0]


def test_pairwise_covers_every_unordered_pair():
    m = [[1, 0], [1, 1], [0, 0]]
    names = ["a", "b", "c"]
    out = A.pairwise(m, names, A.krippendorff_alpha)
    assert set(out) == {("a", "b"), ("a", "c"), ("b", "c")}


def test_mean_ignoring_none():
    assert A.mean_ignoring_none([1.0, None, 3.0]) == pytest.approx(2.0)
    assert A.mean_ignoring_none([None, None]) is None
    assert A.mean_ignoring_none([1.0, float("nan")]) == pytest.approx(1.0)


# ------------------------------------------------------ property-ish sanity

@pytest.mark.parametrize("stat", [A.krippendorff_alpha, A.gwet_ac1, A.fleiss_kappa])
def test_statistics_stay_in_range_on_random_binary_data(stat):
    import random
    rng = random.Random(20260903)
    for _ in range(50):
        n_units = rng.randint(5, 40)
        n_raters = rng.randint(2, 7)
        m = [[rng.choice([0, 0, 0, 1]) for _ in range(n_units)]
             for _ in range(n_raters)]
        v = stat(m)
        if v is not None:
            assert not math.isnan(v)
            assert -1.0 - 1e-9 <= v <= 1.0 + 1e-9
