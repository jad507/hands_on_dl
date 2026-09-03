r"""
Cross-model agreement for phase 1 public-comment extraction.

Provenance of this file
-----------------------
An earlier version of this script was written in June 2026 and produced the
figures quoted in `AITranscribe/docs/isls2027/05-hands-on-dl-upgrade-plan.md`
(3,263 blocks flagged by at least one model, 785 unanimous, cross-family
pairwise Jaccard 0.372-0.554). `plans/windows_environment_upgrade_status.md`
section 1 concluded that file was lost and the numbers had no artefact behind
them. It was not lost: it survived in the `AITranscribe/hands_on_dl` snapshot
dated 2026-07-17, which is the tree the audit was actually run against. This
file is that script, recovered and then substantially changed. The two changes
that move the numbers are below, and both are corrections rather than
refinements.

Correction 1: the unit universe was wrong
-----------------------------------------
The original computed agreement only over blocks that at least one model
flagged. That makes "24% unanimous" a statement about a population selected on
the outcome, and makes every chance-corrected statistic impossible, because the
negative class has been deleted. Roughly 95% of blocks are not public comments,
and a reliability statistic that never sees them cannot be interpreted.

This version reads the block list from `downloads/comments/` and scores every
block, flagged or not. Both framings are reported: `flagged_only` reproduces the
original numbers for continuity, `all_blocks` is the one to quote.

Correction 2: quantisation stability is not agreement
-----------------------------------------------------
The original pairwise matrix contained one high value, 0.840, for
`qwen3.5-9b-q6` vs `qwen3.5-9b-q8`. That is the same model at two
quantisations. It measures how much quantisation perturbs a model, not how much
two models agree, and averaging it into a cross-model mean inflates the mean.
Pairs are now partitioned into cross-model and within-model-family and reported
in separate tables.

What to expect from the statistics
----------------------------------
Fleiss' kappa and Gwet's AC1 are both reported on purpose. The corpus has a
heavily skewed marginal, which is the condition under which kappa collapses
toward zero even when raters visibly agree. A large gap between the two columns
is not a bug; it is the high-agreement paradox, and showing it is more honest
than picking whichever statistic flatters the result. See `agreement.py` and
its tests.

Outputs (to --out, default downloads/agreement_analysis/)
---------------------------------------------------------
    model_agreement_report.md   readable summary
    pairwise_jaccard.csv        model x model, macro-averaged over meetings
    pairwise_alpha.csv          model x model Krippendorff's alpha
    meeting_disagreement.csv    per meeting, worst first
    contested_blocks.csv        every block flagged by some-but-not-all models
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import defaultdict
from itertools import combinations
from pathlib import Path

import agreement as AG
import paths

# Models that are the same base model at a different quantisation. Pairs drawn
# from one of these groups measure quantisation sensitivity, not inter-model
# agreement, and are reported separately.
QUANT_FAMILIES: dict[str, list[str]] = {
    "qwen3.5-9b": ["qwen3.5-9b-q4", "qwen3.5-9b-q5", "qwen3.5-9b-q6", "qwen3.5-9b-q8"],
    "deepseek-r1": [],   # 7b and 14b are different models, not quantisations
}

# Excluded from the "core" tables by default. Both DeepSeek variants failed
# phase 1 in opposite directions -- 7b flagged 8,882 blocks, 14b flagged 195 --
# so including them measures how far a broken run sits from a working one.
DEFAULT_EXCLUDE = ["deepseek-r1-7b", "deepseek-r1-14b"]


def load_json(path: Path) -> dict | None:
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError) as e:
        print(f"  WARN could not read {path}: {e}", file=sys.stderr)
        return None


def same_family(a: str, b: str) -> str | None:
    for fam, members in QUANT_FAMILIES.items():
        if a in members and b in members:
            return fam
    return None


def collect(comments_dir: Path, outputs_root: Path, models: list[str]):
    """Build, per meeting: the full block list and each model's flagged set."""
    universe: dict[str, list] = {}       # meeting -> [block_id, ...]
    blocks: dict[str, dict] = {}         # meeting -> block_id -> block
    flags: dict[str, dict[str, set]] = defaultdict(dict)

    for model in models:
        d = outputs_root / model / "phase1_public_comments"
        if not d.is_dir():
            continue
        for f in sorted(d.glob("*.json")):
            meeting = f.stem
            data = load_json(f)
            if data is None:
                continue
            flags[meeting][model] = {
                c["block_id"] for c in data.get("public_comments", [])
                if c.get("block_id") is not None
            }
            if meeting not in universe:
                src = load_json(comments_dir / f"{meeting}.json")
                if src is None:
                    continue
                bl = src.get("blocks", [])
                universe[meeting] = [b["block_id"] for b in bl]
                blocks[meeting] = {b["block_id"]: b for b in bl}
    return universe, blocks, flags


def analyse(comments_dir: Path, outputs_root: Path, out_dir: Path,
            models: list[str] | None, exclude: list[str]) -> dict:
    out_dir.mkdir(parents=True, exist_ok=True)

    available = sorted(d.name for d in outputs_root.iterdir()
                       if (d / "phase1_public_comments").is_dir())
    models = models or [m for m in available if m not in exclude]
    print(f"models   : {', '.join(models)}")
    if exclude:
        print(f"excluded : {', '.join(x for x in exclude if x in available)}")

    universe, blocks, flags = collect(comments_dir, outputs_root, models)
    meetings = sorted(m for m in flags if m in universe)
    print(f"meetings : {len(meetings)}\n")

    # ---------------------------------------------------------------- totals
    meeting_rows: list[dict] = []
    contested_rows: list[dict] = []
    all_units: list[tuple[str, int]] = []
    all_flags: dict[str, set] = defaultdict(set)
    all_rated: dict[str, set] = defaultdict(set)

    for meeting in meetings:
        mm = flags[meeting]
        ran = [m for m in models if m in mm]
        n_models = len(ran)
        if n_models < 2:
            continue
        votes: dict[int, list[str]] = defaultdict(list)
        for m in ran:
            for bid in mm[m]:
                votes[bid].append(m)

        n_flagged = len(votes)
        unanimous = sum(1 for v in votes.values() if len(v) == n_models)
        majority = sum(1 for v in votes.values() if len(v) > n_models / 2)
        meeting_rows.append({
            "meeting": meeting,
            "models_ran": n_models,
            "blocks_total": len(universe[meeting]),
            "blocks_flagged_by_any": n_flagged,
            "unanimous": unanimous,
            "majority_agreed": majority,
            "contested": n_flagged - unanimous,
            "contested_share": round((n_flagged - unanimous) / n_flagged, 3) if n_flagged else 0.0,
        })
        for bid, vl in sorted(votes.items()):
            if 0 < len(vl) < n_models:
                b = blocks[meeting].get(bid, {})
                contested_rows.append({
                    "meeting": meeting, "block_id": bid,
                    "votes": len(vl), "of": n_models,
                    "models_voting_yes": ";".join(sorted(vl)),
                    "speaker": b.get("speaker", ""),
                    "start": b.get("start", ""),
                    "text_snippet": (b.get("text") or "")[:300],
                })

        for bid in universe[meeting]:
            all_units.append((meeting, bid))
        for m in ran:
            all_rated[m].update((meeting, bid) for bid in universe[meeting])
            all_flags[m].update((meeting, bid) for bid in mm[m])

    meeting_rows.sort(key=lambda r: (-r["contested_share"], -r["contested"]))

    # ------------------------------------------------- corpus-wide statistics
    names, matrix = AG.matrix_from_flag_sets(all_units, all_flags,
                                             rated=all_rated, rater_order=models)
    stats_all = {
        "n_units": len(all_units),
        "krippendorff_alpha": AG.krippendorff_alpha(matrix, AG.delta_nominal),
        "gwet_ac1": AG.gwet_ac1(matrix),
        "fleiss_kappa": AG.fleiss_kappa(matrix),
    }

    # Same statistics restricted to blocks somebody flagged, for continuity
    # with the numbers already quoted in the ISLS audit.
    flagged_units = [u for u in all_units if any(u in all_flags[m] for m in models)]
    _, fmatrix = AG.matrix_from_flag_sets(flagged_units, all_flags,
                                          rated=all_rated, rater_order=models)
    stats_flagged = {
        "n_units": len(flagged_units),
        "krippendorff_alpha": AG.krippendorff_alpha(fmatrix, AG.delta_nominal),
        "gwet_ac1": AG.gwet_ac1(fmatrix),
        "fleiss_kappa": AG.fleiss_kappa(fmatrix),
    }

    # ------------------------------------------------------- pairwise tables
    pair_jac: dict[tuple[str, str], list[float]] = defaultdict(list)
    for meeting in meetings:
        mm = flags[meeting]
        for a, b in combinations(models, 2):
            if a in mm and b in mm:
                j = AG.jaccard(mm[a], mm[b])
                if j is not None:
                    pair_jac[(a, b)].append(j)
    jac = {p: AG.mean_ignoring_none(v) for p, v in pair_jac.items()}

    idx = {m: i for i, m in enumerate(names)}
    alpha_pairs: dict[tuple[str, str], float | None] = {}
    for a, b in combinations(models, 2):
        alpha_pairs[(a, b)] = AG.krippendorff_alpha(
            [matrix[idx[a]], matrix[idx[b]]], AG.delta_nominal)

    cross = [(p, v) for p, v in jac.items() if not same_family(*p)]
    within = [(p, v) for p, v in jac.items() if same_family(*p)]

    _write_matrix(out_dir / "pairwise_jaccard.csv", models, jac)
    _write_matrix(out_dir / "pairwise_alpha.csv", models, alpha_pairs)
    _write_csv(out_dir / "meeting_disagreement.csv", meeting_rows)
    _write_csv(out_dir / "contested_blocks.csv", contested_rows)

    report = build_report(models, meetings, meeting_rows, stats_all,
                          stats_flagged, jac, alpha_pairs, cross, within,
                          all_flags, all_units)
    (out_dir / "model_agreement_report.md").write_text(report, encoding="utf-8")
    print(report)
    print(f"\nwritten to {out_dir}")
    return {"stats_all": stats_all, "stats_flagged": stats_flagged,
            "meeting_rows": meeting_rows, "jaccard": jac}


def build_report(models, meetings, meeting_rows, stats_all, stats_flagged,
                 jac, alpha_pairs, cross, within, all_flags, all_units) -> str:
    def f(x, nd=3):
        return "n/a" if x is None else f"{x:.{nd}f}"

    L: list[str] = []
    L.append("# Cross-model agreement: phase 1 public-comment extraction\n")
    L.append(f"- Models: {', '.join(models)}")
    L.append(f"- Meetings: {len(meetings)}")
    L.append(f"- Blocks in the corpus (the unit universe): {stats_all['n_units']}")
    L.append(f"- Blocks flagged by at least one model: {stats_flagged['n_units']}\n")

    tot_flagged = sum(r["blocks_flagged_by_any"] for r in meeting_rows)
    tot_unan = sum(r["unanimous"] for r in meeting_rows)
    tot_maj = sum(r["majority_agreed"] for r in meeting_rows)
    L.append("## Vote counts among flagged blocks\n")
    if tot_flagged:
        L.append(f"- Flagged by >=1 model: {tot_flagged}")
        L.append(f"- Unanimous: {tot_unan} ({100*tot_unan/tot_flagged:.1f}%)")
        L.append(f"- Majority-agreed: {tot_maj} ({100*tot_maj/tot_flagged:.1f}%)")
        L.append(f"- Contested: {tot_flagged-tot_unan} "
                 f"({100*(tot_flagged-tot_unan)/tot_flagged:.1f}%)\n")
    L.append("These are the numbers the ISLS audit quotes. They describe a "
             "population selected on the outcome -- only blocks somebody flagged "
             "-- so they cannot be chance-corrected and should not be read as "
             "reliability. The next section is the one to quote.\n")

    L.append("## Reliability over the full block universe\n")
    L.append("| statistic | all blocks | flagged blocks only |")
    L.append("|---|---|---|")
    L.append(f"| units | {stats_all['n_units']} | {stats_flagged['n_units']} |")
    L.append(f"| Krippendorff alpha (nominal) | {f(stats_all['krippendorff_alpha'])} | "
             f"{f(stats_flagged['krippendorff_alpha'])} |")
    L.append(f"| Gwet AC1 | {f(stats_all['gwet_ac1'])} | {f(stats_flagged['gwet_ac1'])} |")
    L.append(f"| Fleiss kappa | {f(stats_all['fleiss_kappa'])} | "
             f"{f(stats_flagged['fleiss_kappa'])} |\n")
    L.append("Read the two columns against each other. Over all blocks, AC1 is "
             "high because the models overwhelmingly agree that most blocks are "
             "not public comments -- which is true, and nearly free. Restricted to "
             "blocks somebody flagged, the skew is gone and the statistics fall to "
             "what agreement on the actual judgement looks like. Quote both, or "
             "the reader cannot tell which is being claimed.\n")

    L.append("## Per-model totals\n")
    maj_units = set()
    counts = defaultdict(int)
    for u in all_units:
        v = sum(1 for m in models if u in all_flags[m])
        counts[u] = v
        if v > len(models) / 2:
            maj_units.add(u)
    L.append("| model | blocks flagged | recall vs majority | precision vs majority |")
    L.append("|---|---|---|---|")
    for m in models:
        fl = all_flags[m]
        hit = len(fl & maj_units)
        rec = hit / len(maj_units) if maj_units else 0
        prec = hit / len(fl) if fl else 0
        L.append(f"| {m} | {len(fl)} | {rec:.3f} | {prec:.3f} |")
    L.append("\nThe majority vote is not ground truth. It is what these particular "
             "models happen to agree on, and a model that disagrees with it may be "
             "right. No human labels exist for this corpus yet, which is the "
             "bottleneck the upgrade plan's Step 4 exists to clear.\n")

    L.append("## Pairwise agreement, cross-model\n")
    L.append("| pair | mean Jaccard | Krippendorff alpha |")
    L.append("|---|---|---|")
    for (a, b), v in sorted(cross, key=lambda kv: -(kv[1] or 0)):
        L.append(f"| {a} vs {b} | {f(v)} | {f(alpha_pairs.get((a, b)))} |")
    if cross:
        vals = [v for _, v in cross if v is not None]
        if vals:
            L.append(f"\nCross-model Jaccard spans {min(vals):.3f}-{max(vals):.3f}.\n")

    if within:
        L.append("## Pairwise agreement, same model at different quantisation\n")
        L.append("| pair | mean Jaccard | Krippendorff alpha |")
        L.append("|---|---|---|")
        for (a, b), v in sorted(within, key=lambda kv: -(kv[1] or 0)):
            L.append(f"| {a} vs {b} | {f(v)} | {f(alpha_pairs.get((a, b)))} |")
        L.append("\n**These rows are not agreement measurements.** They are the same "
                 "model at two quantisations, so they measure how much quantisation "
                 "perturbs one model's judgement. The earlier version of this script "
                 "averaged them into the cross-model matrix, where the resulting 0.840 "
                 "read as the strongest inter-model agreement in the corpus. It is a "
                 "self-consistency ceiling instead, and a useful one: it bounds how "
                 "much agreement any two genuinely different models could show.\n")

    L.append("## Top 15 meetings by contested share\n")
    L.append("| meeting | blocks | flagged | unanimous | contested | share |")
    L.append("|---|---|---|---|---|---|")
    for r in meeting_rows[:15]:
        L.append(f"| {r['meeting'][:58]} | {r['blocks_total']} | "
                 f"{r['blocks_flagged_by_any']} | {r['unanimous']} | "
                 f"{r['contested']} | {r['contested_share']} |")
    L.append("\nFull detail in `contested_blocks.csv`, which is the manual-review "
             "queue for the gold-coding pass.\n")
    return "\n".join(L)


def _write_matrix(path: Path, models, pairs) -> None:
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow([""] + list(models))
        for a in models:
            row = [a]
            for b in models:
                if a == b:
                    row.append("1.000")
                else:
                    v = pairs.get((a, b), pairs.get((b, a)))
                    row.append("" if v is None else f"{v:.3f}")
            w.writerow(row)


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
    ap = argparse.ArgumentParser(description="Cross-model phase 1 agreement.")
    ap.add_argument("--comments", default=None)
    ap.add_argument("--outputs", default=None)
    ap.add_argument("--out", default=None)
    ap.add_argument("--models", nargs="*", default=None,
                    help="explicit model list (overrides --exclude)")
    ap.add_argument("--exclude", nargs="*", default=DEFAULT_EXCLUDE,
                    help=f"models to leave out (default: {' '.join(DEFAULT_EXCLUDE)})")
    ap.add_argument("--all-models", action="store_true",
                    help="include the excluded models; use to show how far the "
                         "failed DeepSeek runs sit from the working ones")
    args = ap.parse_args()

    comments = Path(args.comments) if args.comments else paths.COMMENTS_DIR
    outputs = Path(args.outputs) if args.outputs else paths.OUTPUTS_ROOT
    out = Path(args.out) if args.out else paths.DOWNLOADS_DIR / "agreement_analysis"
    exclude = [] if args.all_models else args.exclude

    analyse(comments, outputs, out, args.models, exclude)


if __name__ == "__main__":
    main()
