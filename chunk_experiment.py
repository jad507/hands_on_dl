r"""
The controlled chunk-framing experiment: select the corpus, then analyse it.

Why a designed experiment
-------------------------
`compare_diarization_variants.py` finds the effect as a *natural* experiment:
two pyannote modes happen to produce block lists that differ slightly, which
happens to shift the phase-1 batch boundaries, and blocks whose text is
byte-identical then get classified differently 12-17% of the time. That is
strong evidence but it leans on an accident, and the accident is not evenly
distributed -- only some blocks land in shifted chunks, and which ones is not
random.

Here nothing is accidental. The same meetings, the same block list, the same
model, the same prompt, the same temperature. The only thing that varies is
where the batch boundaries fall, set by `--chunk-size` and `--chunk-offset`.

Conditions
----------
    A   size 3, offset 0     baseline; reproduces the corpus setting
    A2  size 3, offset 0     the SAME setting again -- this is the control, and
                             it measures run-to-run non-determinism directly
                             rather than inferring it
    B   size 3, offset 1     every batch boundary after the first moves; the
                             block list is untouched
    C   size 1               no batch context at all
    D   size 5               more context

The comparisons that matter:

    A vs A2   non-determinism with everything held constant. This is the floor,
              measured under the same conditions as the effect rather than
              across a three-month toolchain gap.
    A vs B    the framing effect, cleanly. Same blocks, same text, different
              company. If this is much larger than A vs A2, the effect is real.
    A vs C    does removing batch context eliminate the instability, or does the
              model simply behave differently alone? C is not "the right
              answer" -- it is a different instrument.
    A vs D    does more context help or hurt?

C is worth stating carefully in advance: a large A-vs-C difference does **not**
show that size 1 is more accurate. Without human labels there is no accuracy
here, only agreement. C tells you how much of the judgement was coming from the
neighbours; whether that contribution was good or bad is Step 4's question.

Usage
-----
    python chunk_experiment.py select --n 12       # build the scratch corpus
    python chunk_experiment.py analyse             # after the runs finish

The runs themselves are driven by `run_chunk_experiment.ps1`.
"""

from __future__ import annotations

import argparse
import csv
import itertools
import json
import re
import shutil
import statistics
from collections import defaultdict
from pathlib import Path

import agreement as AG
import paths

CONDITIONS = {
    "A_size3_off0": {"size": 3, "offset": 0},
    "A2_size3_off0_repeat": {"size": 3, "offset": 0},
    "B_size3_off1": {"size": 3, "offset": 1},
    "C_size1": {"size": 1, "offset": 0},
    "D_size5": {"size": 5, "offset": 0},
}

# Stale files in the superseded commenter_blocks schema; see audit_corpus.py.
EXCLUDE = {
    "City Council Committee Meeting - October 6, 2025 [bubudvmIB_E]",
    "City Council Meeting - August 12, 2025 [Pg4nxjg-PUw]",
}


def load(p: Path):
    try:
        return json.loads(Path(p).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def select(comments_dir: Path, out_dir: Path, n: int, seed: int = 20260903) -> list[str]:
    """Choose meetings and copy them into a scratch corpus.

    Selection is deterministic and stated rather than convenient: `_standard`
    variants only (so no meeting is counted twice), stale-schema files excluded,
    and among the remainder the ones closest to the median block count, so the
    run is neither dominated by one enormous meeting nor made of trivial ones.
    """
    cands = []
    for p in sorted(comments_dir.glob("*.json")):
        stem = p.stem
        if stem in EXCLUDE:
            continue
        # one variant per meeting
        if stem.endswith("_exclusive"):
            continue
        d = load(p)
        if not d:
            continue
        blocks = d.get("blocks") or d.get("commenter_blocks") or []
        if len(blocks) < 20:
            continue
        cands.append((stem, len(blocks), p))

    if not cands:
        raise SystemExit(f"no candidate meetings in {comments_dir}")

    med = statistics.median(b for _, b, _ in cands)
    cands.sort(key=lambda t: (abs(t[1] - med), t[0]))
    chosen = sorted(cands[:n], key=lambda t: t[0])

    out_dir.mkdir(parents=True, exist_ok=True)
    for f in out_dir.glob("*.json"):
        f.unlink()
    total = 0
    for stem, nb, p in chosen:
        shutil.copy2(p, out_dir / p.name)
        total += nb
        print(f"  {nb:5d} blocks  {stem[:66]}")
    print(f"\n{len(chosen)} meetings, {total} blocks -> {out_dir}")
    print(f"median block count in corpus: {med:.0f}")
    return [c[0] for c in chosen]


def flagged(path: Path) -> set | None:
    d = load(path)
    if d is None:
        return None
    return {c["block_id"] for c in d.get("public_comments", [])
            if c.get("block_id") is not None}


def analyse(comments_dir: Path, runs_root: Path, out_dir: Path, model: str) -> dict:
    out_dir.mkdir(parents=True, exist_ok=True)
    present = [c for c in CONDITIONS
               if (runs_root / c / model / "phase1_public_comments").is_dir()]
    if len(present) < 2:
        raise SystemExit(f"need at least two completed conditions, found {present}")
    print(f"conditions present: {', '.join(present)}\n")

    # unit universe and per-condition flags
    universe: list[tuple[str, int]] = []
    blocks: dict[tuple[str, int], dict] = {}
    for p in sorted(comments_dir.glob("*.json")):
        d = load(p)
        if not d:
            continue
        for b in (d.get("blocks") or d.get("commenter_blocks") or []):
            universe.append((p.stem, b["block_id"]))
            blocks[(p.stem, b["block_id"])] = b

    flags: dict[str, set] = {}
    for cond in present:
        s: set = set()
        for f in (runs_root / cond / model / "phase1_public_comments").glob("*.json"):
            got = flagged(f)
            if got:
                s |= {(f.stem, b) for b in got}
        flags[cond] = s

    rows = []
    for a, b in itertools.combinations(present, 2):
        A, B = flags[a], flags[b]
        changed = A ^ B
        names, matrix = AG.matrix_from_flag_sets(universe, {a: A, b: B},
                                                 rater_order=[a, b])
        rows.append({
            "pair": f"{a} vs {b}",
            "flagged_a": len(A), "flagged_b": len(B),
            "net": len(B) - len(A),
            "changed": len(changed),
            "changed_pct": round(100 * len(changed) / len(universe), 3),
            "jaccard": round(AG.jaccard(A, B) or 0, 4),
            "krippendorff_alpha": round(AG.krippendorff_alpha(matrix) or 0, 4),
            "gwet_ac1": round(AG.gwet_ac1(matrix) or 0, 4),
        })

    _write_csv(out_dir / "condition_pairs.csv", rows)

    detail = []
    for cond in present:
        for key in sorted(flags[cond] | set()):
            pass
    changed_rows = []
    if "A_size3_off0" in present:
        base = flags["A_size3_off0"]
        for cond in present:
            if cond == "A_size3_off0":
                continue
            for key in sorted(base ^ flags[cond]):
                blk = blocks.get(key, {})
                changed_rows.append({
                    "condition": cond, "meeting": key[0], "block_id": key[1],
                    "in_baseline": int(key in base),
                    "in_condition": int(key in flags[cond]),
                    "speaker": blk.get("speaker"), "start": blk.get("start"),
                    "word_count": blk.get("word_count"),
                    "text": (blk.get("text") or "")[:300],
                })
    _write_csv(out_dir / "changed_blocks.csv", changed_rows)

    report = build_report(rows, universe, flags, present)
    (out_dir / "chunk_experiment_report.md").write_text(report, encoding="utf-8")
    print(report)
    print(f"\nwritten to {out_dir}")
    return {"rows": rows}


def build_report(rows, universe, flags, present) -> str:
    by = {r["pair"]: r for r in rows}
    L = ["# Controlled chunk-framing experiment\n"]
    L.append(f"- Blocks: {len(universe)}")
    L.append(f"- Conditions: {', '.join(present)}")
    L.append("- Everything held constant except where the phase-1 batch "
             "boundaries fall.\n")

    L.append("## Flagged counts\n")
    L.append("| condition | blocks flagged |")
    L.append("|---|---|")
    for c in present:
        L.append(f"| {c} | {len(flags[c])} |")
    L.append("")

    L.append("## Pairwise\n")
    L.append("| comparison | changed | % of blocks | Jaccard | alpha | AC1 |")
    L.append("|---|---|---|---|---|---|")
    for r in rows:
        L.append(f"| {r['pair']} | {r['changed']} | {r['changed_pct']}% | "
                 f"{r['jaccard']} | {r['krippendorff_alpha']} | {r['gwet_ac1']} |")
    L.append("")

    control = by.get("A_size3_off0 vs A2_size3_off0_repeat")
    effect = by.get("A_size3_off0 vs B_size3_off1")
    L.append("## The comparison this was built for\n")
    if control and effect:
        c, e = control["changed_pct"], effect["changed_pct"]
        L.append(f"- **Control** (same setting, run twice): {control['changed']} "
                 f"blocks changed, **{c}%**")
        L.append(f"- **Effect** (batch boundaries shifted by one): "
                 f"{effect['changed']} blocks changed, **{e}%**")
        if c > 0:
            L.append(f"- **Ratio: {e/c:.1f}x**\n")
        else:
            L.append("- The control found **zero** changes, so the pipeline is "
                     "deterministic at fixed settings on this subset and the "
                     "entire effect below is attributable to the batching.\n")
        L.append("Both numbers come from the same machine, the same session and "
                 "the same model file, so unlike the June-versus-September "
                 "comparison in `compare_corpus_runs.py` there is no toolchain "
                 "gap in the control.\n")
    else:
        L.append("*(A and A2 or B not both present yet.)*\n")

    L.append("## Reading condition C\n")
    L.append("A large A-vs-C difference does **not** show that chunk size 1 is "
             "more accurate. There are no human labels here, so there is no "
             "accuracy -- only agreement. C measures how much of the judgement "
             "was coming from the neighbouring blocks. Whether that contribution "
             "helped or hurt is upgrade-plan Step 4's question, and needs the "
             "gold sample.\n")
    return "\n".join(L)


def _write_csv(path: Path, rows: list[dict]) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    keys: list[str] = []
    for r in rows:
        for k in r:
            if k not in keys:
                keys.append(k)
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=keys)
        w.writeheader()
        w.writerows(rows)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1],
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("mode", choices=["select", "analyse"])
    ap.add_argument("--n", type=int, default=12)
    ap.add_argument("--model", default="gemma-4-4b")
    ap.add_argument("--comments", default=None)
    ap.add_argument("--corpus", default=None, help="scratch corpus directory")
    ap.add_argument("--runs", default=None, help="root holding one dir per condition")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    corpus = Path(args.corpus) if args.corpus else (
        paths.DOWNLOADS_DIR / "chunk_experiment" / "corpus")
    runs = Path(args.runs) if args.runs else (
        paths.DOWNLOADS_DIR / "chunk_experiment" / "runs")
    out = Path(args.out) if args.out else (
        paths.DOWNLOADS_DIR / "chunk_experiment" / "analysis")

    if args.mode == "select":
        src = Path(args.comments) if args.comments else paths.COMMENTS_DIR
        select(src, corpus, args.n)
    else:
        analyse(corpus, runs, out, args.model)


if __name__ == "__main__":
    main()
