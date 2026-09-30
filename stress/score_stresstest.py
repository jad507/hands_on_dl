r"""
Score every stress-detection arm against StressTest's labels, on one scale.

The arms emit different things -- WhiStress a probability per word, the
wavelet toolkit a continuous prominence, Praat a z-score sum, an LLM markup
on some words or none -- so the common measure is TOP-1: the one word each
method rates most stressed, scored correct if it is a labelled stressed word.
170 of the 218 readings have exactly one stressed word, 43 have two, 5
three; picking a word at random scores 0.194. A clip where a method names
no word counts as a miss, never as skipped.

Also reported: word-level P/R/F1 with only the top word marked (so methods
that mark several words are not rewarded for it), a text-only "last word"
baseline (English default nuclear stress; StressTest reads every text with
2+ different placements, so no text-only rule can do well), and exact
McNemar tests between arms on the same clips.

Usage
-----
    python score_stresstest.py
"""

from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path

HERE = Path(__file__).resolve().parent
SS = HERE / "stress_search"

# name -> (csv, column holding the top phrase index); {d} is the dataset
ARMS = {
    "wavelet (classical)": ("classical_{d}.csv", "wavelet_top_index"),
    "praat z-score (classical)": ("classical_{d}.csv", "praat_top_index"),
    "whistress": ("whistress_{d}_top1.csv", "top_index"),
    "gemma general prompt": ("llm_{d}_top1.csv", "general_top_index"),
}


def wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    if n == 0:
        return (0.0, 0.0)
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (round(c - h, 3), round(c + h, 3))


def mcnemar_exact(b: int, c: int) -> float:
    """Two-sided exact p for b vs c discordant pairs."""
    n = b + c
    if n == 0:
        return 1.0
    k = min(b, c)
    p = sum(math.comb(n, i) for i in range(k + 1)) / 2 ** n
    return min(1.0, 2 * p)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dataset", default="stresstest", help="stresspresso for the paper's second benchmark")
    ap.add_argument("--manifest", type=Path, default=None)
    ap.add_argument("--out", type=Path, default=None)
    args = ap.parse_args()
    args.manifest = args.manifest or SS / args.dataset / "manifest.csv"
    args.out = args.out or SS / f"{args.dataset}_scores.json"

    gt = {r["video_id"]: json.loads(r["gt_binary"]) for r in csv.DictReader(open(args.manifest, encoding="utf-8"))}
    ids = sorted(gt)

    tops: dict[str, dict[str, int | None]] = {
        "last word (text only)": {i: len(gt[i]) - 1 for i in ids}}
    for name, (file, col) in ARMS.items():
        path = SS / file.format(d=args.dataset)
        if not path.exists():
            continue
        rows = {r["video_id"]: r for r in csv.DictReader(open(path, encoding="utf-8"))}
        if not set(ids) <= set(rows):
            print(f"{name}: {len(set(ids) & set(rows))}/{len(ids)} clips so far, skipped")
            continue
        tops[name] = {i: (int(rows[i][col]) if rows[i][col] != "" else None) for i in ids}

    hits = {m: {i: t[i] is not None and gt[i][t[i]] == 1 for i in ids} for m, t in tops.items()}
    out = {"n_clips": len(ids),
           "chance_top1": round(sum(sum(g) / len(g) for g in gt.values()) / len(gt), 3), "arms": {}}
    for m, t in tops.items():
        k = sum(hits[m].values())
        tp = k
        fp = sum(1 for i in ids if t[i] is not None) - k
        fn = sum(sum(g) for g in gt.values()) - tp
        prec = tp / (tp + fp) if tp + fp else 0.0
        rec = tp / (tp + fn) if tp + fn else 0.0
        out["arms"][m] = {
            "top1_acc": round(k / len(ids), 3), "top1_ci95": wilson(k, len(ids)),
            "named_a_word": sum(1 for i in ids if t[i] is not None),
            "top1_word_p": round(prec, 3), "top1_word_r": round(rec, 3),
            "top1_word_f1": round(2 * prec * rec / (prec + rec), 3) if prec + rec else 0.0}
    names = list(tops)
    out["mcnemar"] = {}
    for a in names:
        for b in names:
            if a < b:
                only_a = sum(hits[a][i] and not hits[b][i] for i in ids)
                only_b = sum(hits[b][i] and not hits[a][i] for i in ids)
                out["mcnemar"][f"{a} vs {b}"] = {"only_first": only_a, "only_second": only_b,
                                                 "p": round(mcnemar_exact(only_a, only_b), 4)}

    args.out.write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    print(f"{args.dataset}, {len(ids)} labelled readings; chance top-1 {out['chance_top1']}\n")
    print(f"  {'arm':28s} {'top-1':>6s}  {'95% CI':>14s}  {'named':>5s}  {'P':>5s} {'R':>5s} {'F1':>5s}")
    for m, s in sorted(out["arms"].items(), key=lambda kv: -kv[1]["top1_acc"]):
        print(f"  {m:28s} {s['top1_acc']:6.3f}  {str(s['top1_ci95']):>14s}  {s['named_a_word']:5d}  "
              f"{s['top1_word_p']:5.3f} {s['top1_word_r']:5.3f} {s['top1_word_f1']:5.3f}")
    print()
    for pair, s in out["mcnemar"].items():
        print(f"  {pair:62s} {s['only_first']:3d} vs {s['only_second']:3d}   p={s['p']}")


if __name__ == "__main__":
    main()
