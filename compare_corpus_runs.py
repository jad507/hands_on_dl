r"""
Diff two runs of the same model over the same corpus.

Why
---
`plans/windows_environment_upgrade_status.md` section 3 recorded the most
consequential finding on this machine: re-running `gemma-4-4b` phase 1 today on
`HARB Meeting March 4 2025`, with the same model file, the same prompt and
temperature 0, produces four public comments where the committed corpus from
June 2026 has five. Block 5 is dropped. The refactor was shown to be
behaviour-preserving and today's code is self-consistent, so something outside
the Python changed -- a llama-cpp-python reinstall, a driver update, or a model
file replaced in place. The pipeline recorded none of those at the time, which
is the gap the new `provenance` block closes going forward.

That was one meeting and one model, which is an anecdote. The status document's
own recommendation was to re-run one model across the whole corpus and diff, to
turn it into a number. `run_repro_check.ps1` does the re-run into a scratch
output root; this script does the diff.

The number matters beyond housekeeping. The ISLS study measures how far
downstream codes move when the transcript changes. If the pipeline moves on its
own, between runs, with nothing changed, that movement sits in the same
measurement channel as the effect being studied and has to be reported as the
instrument's noise floor. An effect that does not clear the noise floor is not
an effect.

Usage
-----
    python compare_corpus_runs.py --rerun downloads/repro_check/2026-09-03/gemma-4-4b/phase1_public_comments
    python compare_corpus_runs.py --rerun <dir> --baseline <dir> --out <dir>

Outputs
-------
    reproducibility_report.md   the readable summary and the headline number
    per_meeting_delta.csv       every meeting, worst first
    changed_blocks.csv          every block whose classification changed
"""

from __future__ import annotations

import argparse
import csv
import json
import statistics
import sys
from pathlib import Path

import agreement as AG
import paths


def load_json(path: Path) -> dict | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        print(f"  WARN {path}: {e}", file=sys.stderr)
        return None


def flagged(path: Path) -> tuple[set, dict] | None:
    d = load_json(path)
    if d is None:
        return None
    ids, texts = set(), {}
    for c in d.get("public_comments", []):
        bid = c.get("block_id")
        if bid is None:
            continue
        ids.add(bid)
        texts[bid] = (c.get("text") or "")[:300]
    return ids, texts


def compare(baseline: Path, rerun: Path, comments_dir: Path, out_dir: Path) -> dict:
    out_dir.mkdir(parents=True, exist_ok=True)

    base_files = {p.stem: p for p in baseline.glob("*.json")}
    new_files = {p.stem: p for p in rerun.glob("*.json")}
    shared = sorted(set(base_files) & set(new_files))

    print(f"baseline : {baseline}  ({len(base_files)} files)")
    print(f"rerun    : {rerun}  ({len(new_files)} files)")
    print(f"shared   : {len(shared)}")
    if not shared:
        print("Nothing to compare.")
        return {}

    rows: list[dict] = []
    changed: list[dict] = []
    all_units: list[tuple[str, int]] = []
    base_flags: set = set()
    new_flags: set = set()

    for meeting in shared:
        b = flagged(base_files[meeting])
        n = flagged(new_files[meeting])
        if b is None or n is None:
            continue
        (b_ids, b_txt), (n_ids, n_txt) = b, n

        src = load_json(comments_dir / f"{meeting}.json")
        universe = []
        if src:
            universe = [blk["block_id"] for blk in
                        (src.get("blocks") or src.get("commenter_blocks") or [])]
        if not universe:
            universe = sorted(b_ids | n_ids)

        for bid in universe:
            all_units.append((meeting, bid))
            if bid in b_ids:
                base_flags.add((meeting, bid))
            if bid in n_ids:
                new_flags.add((meeting, bid))

        added, dropped = n_ids - b_ids, b_ids - n_ids
        j = AG.jaccard(b_ids, n_ids)
        rows.append({
            "meeting": meeting,
            "blocks_total": len(universe),
            "flagged_baseline": len(b_ids),
            "flagged_rerun": len(n_ids),
            "count_delta": len(n_ids) - len(b_ids),
            "added": len(added),
            "dropped": len(dropped),
            "changed": len(added) + len(dropped),
            "jaccard": None if j is None else round(j, 4),
            "identical": int(b_ids == n_ids),
        })
        for bid in sorted(dropped):
            changed.append({"meeting": meeting, "block_id": bid,
                            "direction": "dropped_in_rerun",
                            "text": b_txt.get(bid, "")})
        for bid in sorted(added):
            changed.append({"meeting": meeting, "block_id": bid,
                            "direction": "added_in_rerun",
                            "text": n_txt.get(bid, "")})

    rows.sort(key=lambda r: (-r["changed"], r["meeting"]))

    names, matrix = AG.matrix_from_flag_sets(
        all_units, {"baseline": base_flags, "rerun": new_flags},
        rater_order=["baseline", "rerun"])
    alpha = AG.krippendorff_alpha(matrix, AG.delta_nominal)
    ac1 = AG.gwet_ac1(matrix)
    corpus_jaccard = AG.jaccard(base_flags, new_flags)

    _write_csv(out_dir / "per_meeting_delta.csv", rows)
    _write_csv(out_dir / "changed_blocks.csv", changed)

    stats = {
        "meetings": len(rows),
        "identical_meetings": sum(r["identical"] for r in rows),
        "blocks": len(all_units),
        "flagged_baseline": len(base_flags),
        "flagged_rerun": len(new_flags),
        "blocks_changed": len(changed),
        "corpus_jaccard": corpus_jaccard,
        "krippendorff_alpha": alpha,
        "gwet_ac1": ac1,
    }
    report = build_report(stats, rows, baseline, rerun)
    (out_dir / "reproducibility_report.md").write_text(report, encoding="utf-8")
    print("\n" + report)
    print(f"\nwritten to {out_dir}")
    return stats


def build_report(s: dict, rows: list[dict], baseline: Path, rerun: Path) -> str:
    def f(x, nd=4):
        return "n/a" if x is None else f"{x:.{nd}f}"

    L: list[str] = []
    L.append("# Reproducibility: same model, same corpus, two runs\n")
    L.append(f"- Baseline: `{baseline}`")
    L.append(f"- Re-run:   `{rerun}`\n")
    L.append("## Headline\n")
    ident_pct = 100 * s["identical_meetings"] / s["meetings"] if s["meetings"] else 0
    L.append(f"- Meetings compared: **{s['meetings']}**")
    L.append(f"- Meetings whose flagged set is byte-identical: "
             f"**{s['identical_meetings']} ({ident_pct:.1f}%)**")
    L.append(f"- Blocks in those meetings: {s['blocks']}")
    L.append(f"- Flagged, baseline: {s['flagged_baseline']}   "
             f"re-run: {s['flagged_rerun']}   "
             f"net {s['flagged_rerun'] - s['flagged_baseline']:+d}")
    L.append(f"- Blocks whose classification changed: **{s['blocks_changed']}**")
    L.append(f"- Corpus-level Jaccard between the two runs: **{f(s['corpus_jaccard'])}**")
    L.append(f"- Krippendorff alpha (run vs run): {f(s['krippendorff_alpha'])}")
    L.append(f"- Gwet AC1 (run vs run): {f(s['gwet_ac1'])}\n")

    L.append("## How to read this\n")
    L.append("Two runs of the same model over the same input with temperature 0 "
             "should agree exactly. Every number above that is not perfect is the "
             "pipeline's noise floor.\n")
    L.append("The comparison to make is against the effect sizes this project "
             "wants to report. `compare_diarization_variants.py` finds that shifting "
             "the 3-block chunk window flips 12-17% of classifications on "
             "byte-identical text. If the run-to-run noise floor here is far below "
             "that, the chunk-framing effect is real and clears its instrument. If "
             "it is comparable, the two cannot be told apart and the chunk finding "
             "has to be re-run with repeated measurements before it is claimed.\n")

    if rows:
        deltas = [abs(r["count_delta"]) for r in rows]
        L.append(f"- Mean absolute per-meeting count delta: {statistics.mean(deltas):.2f}")
        L.append(f"- Max: {max(deltas)}\n")
        L.append("## Meetings that moved most\n")
        L.append("| meeting | blocks | baseline | rerun | added | dropped | Jaccard |")
        L.append("|---|---|---|---|---|---|---|")
        for r in rows[:20]:
            if not r["changed"]:
                continue
            L.append(f"| {r['meeting'][:52]} | {r['blocks_total']} | "
                     f"{r['flagged_baseline']} | {r['flagged_rerun']} | "
                     f"{r['added']} | {r['dropped']} | {f(r['jaccard'], 3)} |")
        L.append("\nFull detail in `changed_blocks.csv`, which carries the text of "
                 "every block whose classification moved.\n")
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
    ap = argparse.ArgumentParser(description="Diff two runs of one model.")
    ap.add_argument("--rerun", required=True,
                    help="phase1_public_comments dir from the new run")
    ap.add_argument("--baseline", default=None,
                    help="phase1_public_comments dir of the committed corpus; "
                         "derived from --model if omitted")
    ap.add_argument("--model", default=None,
                    help="model name, used to locate the baseline")
    ap.add_argument("--comments", default=None)
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    rerun = Path(args.rerun)
    if args.baseline:
        baseline = Path(args.baseline)
    else:
        model = args.model
        if not model:
            # .../repro_check/<tag>/<model>/phase1_public_comments
            model = rerun.parent.name
        baseline = paths.OUTPUTS_ROOT / model / "phase1_public_comments"

    comments = Path(args.comments) if args.comments else paths.COMMENTS_DIR
    out = Path(args.out) if args.out else (
        paths.DOWNLOADS_DIR / "agreement_analysis" / "reproducibility")

    if not rerun.is_dir():
        sys.exit(f"re-run directory not found: {rerun}")
    if not baseline.is_dir():
        sys.exit(f"baseline directory not found: {baseline}")

    compare(baseline, rerun, comments, out)


if __name__ == "__main__":
    main()
