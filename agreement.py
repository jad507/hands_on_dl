r"""
Inter-rater reliability statistics.

Why this module exists
----------------------
The recovered `compare_model_agreement.py` reported pairwise Jaccard and a raw
"unanimous / majority / contested" split. Both are chance-uncorrected: with
seven models and a highly skewed marginal (a few percent of blocks are public
comments), "the models agree 94% of the time" is mostly a statement about how
rare the positive class is, not about how much the models agree.

`AITranscribe/docs/isls2027/05-hands-on-dl-upgrade-plan.md` Step 1.3 asks for
Krippendorff's alpha and Gwet's AC1 specifically, the latter "because it is
robust to the high-prevalence/low-marginal skew you have". Both are implemented
here from their published definitions rather than pulled in as dependencies:
the whole point of the ISLS contribution is that the measurement instrument is
inspectable, and a 60-line function whose test suite reproduces the reference
values from the literature is more inspectable than a pinned wheel.

Everything here operates on a *reliability matrix*: a list of rows, one per
rater (coder / model), each row a list of that rater's ratings for the units in
a fixed order, with None for "this rater did not rate this unit". This is
Krippendorff's own layout and it tolerates missing data, which matters because
phase 2 is incomplete for five of the seven models.

References
----------
Krippendorff, K. (2011). "Computing Krippendorff's Alpha-Reliability."
    https://repository.upenn.edu/asc_papers/43
Gwet, K. L. (2008). "Computing inter-rater reliability and its variance in the
    presence of high agreement." British Journal of Mathematical and
    Statistical Psychology 61(1), 29-48.
"""

from __future__ import annotations

import math
from collections import Counter, defaultdict
from typing import Callable, Iterable, Sequence

Rating = float | int | str | None
Matrix = Sequence[Sequence[Rating]]


# --------------------------------------------------------------------------
# Set-level similarity
# --------------------------------------------------------------------------

def jaccard(a: Iterable, b: Iterable) -> float | None:
    """Jaccard similarity |A and B| / |A or B|.

    Returns None rather than 1.0 when both sets are empty. Two models that both
    flagged nothing in a meeting have not demonstrated agreement about anything,
    and scoring that as perfect agreement inflates the mean across meetings --
    which is precisely the failure mode in a corpus where many meetings contain
    no public comment at all.
    """
    A, B = set(a), set(b)
    union = A | B
    if not union:
        return None
    return len(A & B) / len(union)


def dice(a: Iterable, b: Iterable) -> float | None:
    """Dice / F1 similarity 2|A and B| / (|A| + |B|). None if both empty."""
    A, B = set(a), set(b)
    denom = len(A) + len(B)
    if denom == 0:
        return None
    return 2 * len(A & B) / denom


# --------------------------------------------------------------------------
# Distance metrics for Krippendorff's alpha
# --------------------------------------------------------------------------

def delta_nominal(a: Rating, b: Rating) -> float:
    """Squared difference for unordered categories: 0 if identical else 1."""
    return 0.0 if a == b else 1.0


def delta_interval(a: Rating, b: Rating) -> float:
    """Squared difference for interval-scale values, e.g. 0.0-1.0 theme scores."""
    return (float(a) - float(b)) ** 2


def delta_ordinal_factory(values: Sequence) -> Callable[[Rating, Rating], float]:
    """Build an ordinal delta over a fixed, ordered set of category values.

    Ordinal delta depends on how many observations fall between the two ranks,
    so unlike the nominal and interval cases it cannot be a free function -- it
    has to be constructed against the data. Provided for completeness; the
    project currently uses nominal (phase 1) and interval (phase 2).
    """
    order = {v: i for i, v in enumerate(values)}

    def delta(a: Rating, b: Rating) -> float:
        i, j = order[a], order[b]
        return float((i - j) ** 2)

    return delta


# --------------------------------------------------------------------------
# Krippendorff's alpha
# --------------------------------------------------------------------------

def krippendorff_alpha(matrix: Matrix,
                       delta: Callable[[Rating, Rating], float] = delta_nominal,
                       ) -> float | None:
    """Krippendorff's alpha for a raters-by-units reliability matrix.

    alpha = 1 - Do/De, where Do is observed disagreement and De is the
    disagreement expected if ratings were assigned at random from the pooled
    set of actual ratings.

    Units rated by fewer than two raters carry no pairable information and are
    dropped, per Krippendorff. Returns None when fewer than two pairable values
    survive, and 1.0 when De is zero (every rater gave the same value to
    everything -- perfect agreement on a degenerate distribution, where alpha is
    conventionally taken as 1 rather than 0/0).

    `matrix` is a sequence of rows, one per rater, each of equal length, with
    None marking a missing rating.
    """
    if not matrix:
        return None
    n_units = len(matrix[0])
    for row in matrix:
        if len(row) != n_units:
            raise ValueError("all rater rows must have the same length")

    # Column-major: the values actually observed for each unit.
    units: list[list[Rating]] = []
    for u in range(n_units):
        vals = [row[u] for row in matrix if row[u] is not None]
        if len(vals) >= 2:
            units.append(vals)

    n = sum(len(v) for v in units)          # total pairable values
    if n < 2:
        return None

    # Observed disagreement: within each unit, the mean pairwise delta over
    # ordered pairs, weighted by that unit's share of pairable values.
    observed = 0.0
    for vals in units:
        m = len(vals)
        s = 0.0
        for i in range(m):
            for j in range(m):
                if i != j:
                    s += delta(vals[i], vals[j])
        observed += s / (m - 1)
    Do = observed / n

    # Expected disagreement: the same quantity over all ordered pairs drawn
    # from the pooled values, ignoring which unit they came from.
    pool: list[Rating] = [v for vals in units for v in vals]
    counts = Counter(pool)
    expected = 0.0
    keys = list(counts)
    for a in keys:
        for b in keys:
            if a == b:
                # ordered pairs of two DIFFERENT draws of the same value
                expected += counts[a] * (counts[a] - 1) * delta(a, a)
            else:
                expected += counts[a] * counts[b] * delta(a, b)
    De = expected / (n * (n - 1))

    if De == 0:
        return 1.0
    return 1.0 - Do / De


# --------------------------------------------------------------------------
# Gwet's AC1
# --------------------------------------------------------------------------

def gwet_ac1(matrix: Matrix) -> float | None:
    """Gwet's AC1 for nominal ratings on a raters-by-units matrix.

    AC1 = (p_a - p_e) / (1 - p_e), with

        p_a  observed agreement, the mean over units of the proportion of
             rater pairs within that unit that agree;
        p_e  Gwet's chance agreement, (1/(q-1)) * sum_k pi_k (1 - pi_k),
             where pi_k is the mean propensity to use category k and q the
             number of categories observed.

    The reason to prefer this over Cohen's or Fleiss's kappa here: kappa's
    chance term is a product of marginals, so when one category is very common
    -- as "not a public comment" is, at roughly 95% of blocks -- the chance term
    approaches the observed agreement and kappa collapses toward zero or below
    even when the raters plainly agree. Gwet's chance term is maximised at an
    even split and shrinks as the marginal skews, which is the behaviour you
    want for this corpus. This is the "high agreement paradox"; the unit test
    reproduces Gwet's own worked example of it.

    Units rated by fewer than two raters are dropped. Returns None if none
    survive, and 1.0 when only one category was ever used (q == 1 makes p_e
    undefined; every rater agreed on everything, so alpha-style convention
    gives 1).
    """
    units: list[list[Rating]] = []
    if not matrix:
        return None
    n_units = len(matrix[0])
    for u in range(n_units):
        vals = [row[u] for row in matrix if row[u] is not None]
        if len(vals) >= 2:
            units.append(vals)
    if not units:
        return None

    categories = sorted({v for vals in units for v in vals}, key=repr)
    q = len(categories)
    if q == 1:
        return 1.0

    N = len(units)

    # Observed agreement, averaged over units.
    p_a = 0.0
    for vals in units:
        n_i = len(vals)
        c = Counter(vals)
        agree_pairs = sum(r * (r - 1) for r in c.values())
        p_a += agree_pairs / (n_i * (n_i - 1))
    p_a /= N

    # Category propensities: mean over units of the within-unit share.
    pi = {}
    for k in categories:
        pi[k] = sum(Counter(vals)[k] / len(vals) for vals in units) / N

    p_e = sum(pi[k] * (1 - pi[k]) for k in categories) / (q - 1)

    if p_e >= 1.0:
        return None
    return (p_a - p_e) / (1 - p_e)


# --------------------------------------------------------------------------
# Fleiss' kappa, for contrast
# --------------------------------------------------------------------------

def fleiss_kappa(matrix: Matrix) -> float | None:
    """Fleiss' kappa on a raters-by-units nominal matrix.

    Included not because it is the right statistic for this corpus but because
    reporting it next to AC1 is how you *show* the high-agreement paradox rather
    than asserting it. A large gap between the two is the diagnostic.
    """
    units: list[list[Rating]] = []
    if not matrix:
        return None
    n_units = len(matrix[0])
    for u in range(n_units):
        vals = [row[u] for row in matrix if row[u] is not None]
        if len(vals) >= 2:
            units.append(vals)
    if not units:
        return None

    categories = sorted({v for vals in units for v in vals}, key=repr)
    if len(categories) == 1:
        return 1.0
    N = len(units)

    p_a = 0.0
    for vals in units:
        n_i = len(vals)
        c = Counter(vals)
        p_a += sum(r * (r - 1) for r in c.values()) / (n_i * (n_i - 1))
    p_a /= N

    total = sum(len(v) for v in units)
    p_e = 0.0
    for k in categories:
        p_k = sum(Counter(vals)[k] for vals in units) / total
        p_e += p_k * p_k

    if p_e >= 1.0:
        return None
    return (p_a - p_e) / (1 - p_e)


# --------------------------------------------------------------------------
# Convenience: build a reliability matrix from per-rater sets
# --------------------------------------------------------------------------

def matrix_from_flag_sets(units: Sequence,
                          flags: dict[str, set],
                          rated: dict[str, set] | None = None,
                          rater_order: Sequence[str] | None = None,
                          ) -> tuple[list[str], list[list[Rating]]]:
    """Turn "which units did each rater flag" into a binary reliability matrix.

    `units`   the full unit universe, in a fixed order. This matters: passing
              only the flagged units makes every chance-corrected statistic
              meaningless, because the negative class disappears.
    `flags`   rater -> set of units it flagged (rated 1).
    `rated`   rater -> set of units it saw at all. Units outside this set become
              None (missing) rather than 0. Defaults to "every rater saw every
              unit", which is true for phase 1 and false for phase 2.

    Returns (rater_names, matrix) with matrix rows in rater_names order.
    """
    names = list(rater_order) if rater_order is not None else sorted(flags)
    matrix: list[list[Rating]] = []
    for name in names:
        flagged = flags.get(name, set())
        seen = rated.get(name) if rated else None
        row: list[Rating] = []
        for u in units:
            if seen is not None and u not in seen:
                row.append(None)
            else:
                row.append(1 if u in flagged else 0)
        matrix.append(row)
    return names, matrix


def pairwise(matrix: Matrix, names: Sequence[str],
             stat: Callable[[Matrix], float | None]) -> dict[tuple[str, str], float | None]:
    """Apply a two-rater statistic to every pair of rows."""
    out: dict[tuple[str, str], float | None] = {}
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            out[(names[i], names[j])] = stat([matrix[i], matrix[j]])
    return out


def mean_ignoring_none(values: Iterable[float | None]) -> float | None:
    vals = [v for v in values if v is not None and not math.isnan(v)]
    if not vals:
        return None
    return sum(vals) / len(vals)
