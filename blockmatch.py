r"""
Aligning speaker blocks across two upstream processing variants.

The problem
-----------
`downloads/comments/` holds 26 meetings in two variants, `_standard` and
`_exclusive`, produced by running pyannote in two diarization modes over the
same audio. They are the same recording processed two ways, which makes them a
natural experiment -- but the two variants draw speaker-turn boundaries in
different places, so `block_id` does not join. Block 12 in one variant is not
block 12 in the other, and in general is not any single block in the other.

`AITranscribe/docs/isls2027/05-hands-on-dl-upgrade-plan.md` Step 1.4 asks for
this, and notes that it is the same problem as the alignment problem in the
Concord technical spec (03): when the transcription policy changes, the text
changes, so any content-derived identifier changes with it. The only thing that
survives a re-transcription or a re-diarization is the *time anchor*. So the
join key is time.

What this module refuses to do
------------------------------
It does not force a one-to-one matching. Two diarization modes genuinely
produce splits and merges: one variant hears a single 40-second turn where the
other hears a question and an answer. Coercing that into 1:1 discards exactly
the phenomenon the ISLS study is about -- unit boundaries being load-bearing --
and, worse, does it silently.

Instead `align()` builds the bipartite overlap graph and reports its connected
components classified by shape:

    one_to_one   1 block on each side          -- safe to compare directly
    split        1 on the left, N on the right -- the right variant subdivided
    merge        N on the left, 1 on the right -- the right variant fused
    tangle       N and M, N > 1 and M > 1      -- boundaries genuinely disagree
    unmatched    a block with no overlap partner above threshold

Downstream code decides what to do with each shape and has to say so. Only
`one_to_one` gets an entry in `map_a_to_b`.

On speaker labels
-----------------
pyannote assigns `SPEAKER_00`, `SPEAKER_01` ... in order of appearance within a
run, so the labels are internal to a run and carry no cross-variant meaning.
`SPEAKER_03` in `_standard` and `SPEAKER_03` in `_exclusive` are not
necessarily the same person. `require_same_speaker` therefore defaults to
False. Use `infer_speaker_mapping()` to recover the correspondence empirically
from the alignment before relying on speaker identity across variants.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from typing import Iterable, Sequence

Block = dict


# --------------------------------------------------------------------------
# Interval primitives
# --------------------------------------------------------------------------

def overlap_seconds(a: Block, b: Block) -> float:
    """Seconds of wall-clock overlap between two blocks. 0.0 if disjoint."""
    lo = max(float(a["start"]), float(b["start"]))
    hi = min(float(a["end"]), float(b["end"]))
    return max(0.0, hi - lo)


def duration(b: Block) -> float:
    return max(0.0, float(b["end"]) - float(b["start"]))


def interval_iou(a: Block, b: Block) -> float:
    """Intersection over union on the time axis.

    IoU rather than raw overlap because raw overlap rewards long blocks: a
    600-second block that swallows a 10-second one overlaps it completely, and
    calling that a match would let a coarse diarization absorb a fine one and
    report perfect alignment.
    """
    inter = overlap_seconds(a, b)
    if inter <= 0:
        return 0.0
    union = duration(a) + duration(b) - inter
    return inter / union if union > 0 else 0.0


def coverage(a: Block, b: Block) -> float:
    """Fraction of `a` covered by `b`. Asymmetric, unlike IoU.

    Useful for describing splits: each fragment has low IoU with the parent but
    high coverage by it.
    """
    d = duration(a)
    return overlap_seconds(a, b) / d if d > 0 else 0.0


# --------------------------------------------------------------------------
# Alignment
# --------------------------------------------------------------------------

@dataclass
class Component:
    """One connected component of the bipartite overlap graph."""
    a_ids: list = field(default_factory=list)
    b_ids: list = field(default_factory=list)
    shape: str = "unmatched"          # one_to_one | split | merge | tangle | unmatched
    iou: float | None = None          # only meaningful for one_to_one


@dataclass
class Alignment:
    components: list[Component]
    map_a_to_b: dict                  # a_id -> b_id, one_to_one components only
    map_b_to_a: dict
    unmatched_a: list
    unmatched_b: list
    n_a: int
    n_b: int

    def counts(self) -> dict[str, int]:
        out = {"one_to_one": 0, "split": 0, "merge": 0, "tangle": 0,
               "unmatched_a": len(self.unmatched_a),
               "unmatched_b": len(self.unmatched_b)}
        for c in self.components:
            if c.shape in out:
                out[c.shape] += 1
        return out

    def one_to_one_rate(self) -> float:
        """Share of left-hand blocks that got a clean 1:1 partner.

        The single number worth quoting when describing how comparable two
        variants are. A low value is not a failure of the matcher; it is a
        finding about the two diarization modes.
        """
        return len(self.map_a_to_b) / self.n_a if self.n_a else 0.0


def align(blocks_a: Sequence[Block],
          blocks_b: Sequence[Block],
          min_iou: float = 0.10,
          require_same_speaker: bool = False,
          key: str = "block_id") -> Alignment:
    """Align two block lists by temporal overlap.

    `min_iou` is the threshold below which an overlap is treated as incidental
    rather than a correspondence. 0.10 is deliberately permissive: the cost of a
    spurious edge is that a component gets classified as a tangle and excluded
    from the 1:1 statistics, whereas the cost of a missed edge is a block
    silently reported as unmatched. Sweep it with `threshold_sensitivity()`
    before quoting any number that depends on it.
    """
    a_ids = [blk[key] for blk in blocks_a]
    b_ids = [blk[key] for blk in blocks_b]

    edges: list[tuple[int, int, float]] = []
    for i, ba in enumerate(blocks_a):
        for j, bb in enumerate(blocks_b):
            if require_same_speaker and ba.get("speaker") != bb.get("speaker"):
                continue
            v = interval_iou(ba, bb)
            if v >= min_iou:
                edges.append((i, j, v))

    # Union-find over the combined index space: A nodes 0..na-1, B nodes offset.
    na, nb = len(blocks_a), len(blocks_b)
    parent = list(range(na + nb))

    def find(x: int) -> int:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(x: int, y: int) -> None:
        rx, ry = find(x), find(y)
        if rx != ry:
            parent[ry] = rx

    iou_lookup: dict[tuple[int, int], float] = {}
    for i, j, v in edges:
        union(i, na + j)
        iou_lookup[(i, j)] = v

    groups: dict[int, tuple[list[int], list[int]]] = defaultdict(lambda: ([], []))
    for i in range(na):
        groups[find(i)][0].append(i)
    for j in range(nb):
        groups[find(na + j)][1].append(j)

    components: list[Component] = []
    map_a_to_b: dict = {}
    map_b_to_a: dict = {}
    unmatched_a: list = []
    unmatched_b: list = []

    for root in sorted(groups):
        ai, bj = groups[root]
        comp = Component(a_ids=[a_ids[i] for i in sorted(ai)],
                         b_ids=[b_ids[j] for j in sorted(bj)])
        if ai and not bj:
            comp.shape = "unmatched"
            unmatched_a.extend(comp.a_ids)
        elif bj and not ai:
            comp.shape = "unmatched"
            unmatched_b.extend(comp.b_ids)
        elif len(ai) == 1 and len(bj) == 1:
            comp.shape = "one_to_one"
            comp.iou = iou_lookup[(ai[0], bj[0])]
            map_a_to_b[a_ids[ai[0]]] = b_ids[bj[0]]
            map_b_to_a[b_ids[bj[0]]] = a_ids[ai[0]]
        elif len(ai) == 1:
            comp.shape = "split"
        elif len(bj) == 1:
            comp.shape = "merge"
        else:
            comp.shape = "tangle"
        components.append(comp)

    return Alignment(components=components,
                     map_a_to_b=map_a_to_b,
                     map_b_to_a=map_b_to_a,
                     unmatched_a=unmatched_a,
                     unmatched_b=unmatched_b,
                     n_a=na, n_b=nb)


def threshold_sensitivity(blocks_a: Sequence[Block],
                          blocks_b: Sequence[Block],
                          thresholds: Iterable[float] = (0.05, 0.10, 0.25, 0.50, 0.75),
                          ) -> list[dict]:
    """Re-align at several `min_iou` values and report how the shape counts move.

    Included because `min_iou` is a researcher degree of freedom of exactly the
    kind this project exists to make visible. If the headline number moves a lot
    across this sweep, the threshold has to be pre-registered and reported; if it
    does not, that is worth saying in the paper too.
    """
    rows = []
    for t in thresholds:
        al = align(blocks_a, blocks_b, min_iou=t)
        row = {"min_iou": t, "one_to_one_rate": round(al.one_to_one_rate(), 4)}
        row.update(al.counts())
        rows.append(row)
    return rows


def infer_speaker_mapping(blocks_a: Sequence[Block],
                          blocks_b: Sequence[Block],
                          alignment: Alignment | None = None,
                          key: str = "block_id") -> dict[str, str]:
    """Recover which speaker label in B corresponds to which in A.

    pyannote's labels are per-run, so this cannot be assumed and has to be
    measured. Built from the 1:1 components by majority vote weighted by
    overlap duration. Labels with no clean evidence are simply absent from the
    returned mapping rather than guessed.
    """
    if alignment is None:
        alignment = align(blocks_a, blocks_b, key=key)
    by_a = {blk[key]: blk for blk in blocks_a}
    by_b = {blk[key]: blk for blk in blocks_b}

    weight: dict[str, dict[str, float]] = defaultdict(lambda: defaultdict(float))
    for a_id, b_id in alignment.map_a_to_b.items():
        ba, bb = by_a[a_id], by_b[b_id]
        sa, sb = ba.get("speaker"), bb.get("speaker")
        if sa is None or sb is None:
            continue
        weight[sa][sb] += overlap_seconds(ba, bb)

    return {sa: max(cands, key=cands.get) for sa, cands in weight.items() if cands}


def translate_ids(ids: Iterable, alignment: Alignment,
                  direction: str = "a_to_b") -> tuple[set, set]:
    """Map a set of block ids through an alignment.

    Returns (translated, untranslatable). The second element is the point: a
    block flagged in one variant that has no 1:1 partner in the other cannot be
    scored as agreement or as disagreement, and dropping it silently would bias
    every downstream statistic toward whichever variant has coarser blocks.
    """
    mapping = alignment.map_a_to_b if direction == "a_to_b" else alignment.map_b_to_a
    translated, missing = set(), set()
    for i in ids:
        if i in mapping:
            translated.add(mapping[i])
        else:
            missing.add(i)
    return translated, missing
