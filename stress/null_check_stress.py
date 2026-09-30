r"""
Does a corpus-level stress statistic beat what the same method reports on
audio with no contrast in it?

Why this exists
---------------
Doc 09 section 2's headline -- 96% of clips show "recoverable stress" (3+
distinct stressed words), 30% "strong" (5+) -- counts how many different
words verify_stress.stressed_indices() elects across a video's repetitions.
That function scores each word against its own mean over the repetitions, and
mean-centering alone spreads the per-rep winner across positions: a column of
numbers minus its mean has a different argmax per row whatever the numbers
are. So the count has to be checked against a null before it means anything.

The null keeps every word's real measured prominences and shuffles which
repetition each value came from, independently per word position. Lexical
loudness (a proper noun loud in every reading) survives; any contrast inside a
single reading does not. If the statistic comes out the same, it was never
measuring contrast.

The same test runs on each single-utterance arm's one-clip-at-a-time answers
-- WhiStress (measure_whistress.py), the wavelet toolkit and the Praat
z-score (measure_classical.py) -- shuffling rep order within each video: a
left-to-right walk can only beat that null if each clip's answer depended on
which reading it was. All arms are scored on the identical clean clips.

Usage
-----
    python null_check_stress.py
    python null_check_stress.py --perms 1000
"""

from __future__ import annotations

import argparse
import csv
import json
import random
import statistics as st
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from verify_stress import longest_walk, stressed_indices  # noqa: E402


def stats(seqs: list[list[int]]) -> dict:
    d = [len(set(s)) for s in seqs]
    return {"mean_distinct": st.mean(d), "distinct_ge3": sum(x >= 3 for x in d),
            "distinct_ge5": sum(x >= 5 for x in d),
            "mean_walk_frac": st.mean(longest_walk(s) / len(s) for s in seqs)}


def compare(real: dict, nulls: list[dict]) -> dict:
    out = {}
    for k, v in real.items():
        vals = sorted(n[k] for n in nulls)
        n = len(vals)
        out[k] = {"real": round(v, 3), "null_median": round(vals[n // 2], 3),
                  "null_95": [round(vals[int(0.025 * n)], 3), round(vals[int(0.975 * n)], 3)],
                  "p_null_ge_real": round(sum(x >= v for x in vals) / n, 4)}
    return out


def shuffle_within_words(profiles: list[list[dict]], rng: random.Random) -> list[list[dict]]:
    n = min(len(p) for p in profiles)
    cols = [[p[k]["prominence"] for p in profiles] for k in range(n)]
    for c in cols:
        rng.shuffle(c)
    return [[{"prominence": cols[k][j]} for k in range(n)] for j in range(len(profiles))]


def clean_clips(path: Path) -> set[tuple[str, str]]:
    """Rep clips that passed cut QA, whose WhiStress transcript contains the
    whole phrase, and that hold no more than two extra words (one utterance,
    not an explanation or a neighbouring repetition). Defined once, from the
    clip's content, and applied to every method so all see the same clips."""
    keep = set()
    for r in csv.DictReader(open(path, encoding="utf-8")):
        n = len(r["phrase"].split())
        if (r["qa_pass"] == "True" and int(r["words_aligned"]) == n
                and len(json.loads(r["pred_words"])) <= n + 2):
            keep.add((r["video_id"], r["condition"]))
    return keep


def top_seqs(path: Path, col: str, clips: set[tuple[str, str]]) -> dict[str, dict[str, int]]:
    """video -> {condition: top phrase index} for the given clips."""
    out: dict[str, dict[str, int]] = {}
    for r in csv.DictReader(open(path, encoding="utf-8")):
        if (r["video_id"], r["condition"]) in clips and r[col] != "":
            out.setdefault(r["video_id"], {})[r["condition"]] = int(r[col])
    return out


def walk_vs_null(seqs: dict[str, list[int]], perms: int) -> dict:
    real = stats(list(seqs.values()))
    nulls = []
    for seed in range(perms):
        rng = random.Random(seed)
        nulls.append(stats([rng.sample(s, len(s)) for s in seqs.values()]))
    # Distinct counts are invariant to reordering, so only the walk has a null here.
    return {"n_videos": len(seqs), "n_clips": sum(len(s) for s in seqs.values()),
            "mean_distinct": round(real["mean_distinct"], 3),
            "videos_all_reps_same_word": sum(len(set(s)) == 1 for s in seqs.values()),
            "mean_walk_frac": compare({"mean_walk_frac": real["mean_walk_frac"]}, nulls)["mean_walk_frac"]}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--evidence", type=Path, default=HERE / "stress_search" / "stress_evidence.json")
    ap.add_argument("--whistress", type=Path, default=HERE / "stress_search" / "whistress_reps.csv")
    ap.add_argument("--classical", type=Path, default=HERE / "stress_search" / "classical_reps.csv")
    ap.add_argument("--out", type=Path, default=HERE / "stress_search" / "null_check_summary.json")
    ap.add_argument("--perms", type=int, default=300)
    ap.add_argument("--min-reps", type=int, default=3)
    args = ap.parse_args()

    ev = json.load(open(args.evidence, encoding="utf-8"))
    real = stats([e["stressed_index"] for e in ev.values()])
    nulls = []
    for seed in range(args.perms):
        rng = random.Random(seed)
        nulls.append(stats([stressed_indices(shuffle_within_words(e["profiles"], rng)) for e in ev.values()]))
    summary = {"perms": args.perms,
               "detector_cross_rep": {"n_videos": len(ev), **compare(real, nulls)}}

    if args.whistress.exists():
        clips = clean_clips(args.whistress)
        arms = {"whistress_single_utterance": top_seqs(args.whistress, "top_index", clips)}
        if args.classical.exists():
            arms["wavelet_single_utterance"] = top_seqs(args.classical, "wavelet_top_index", clips)
            arms["praat_single_utterance"] = top_seqs(args.classical, "praat_top_index", clips)
        # Same videos and same clips for every arm: keep a clip only if every arm named a word on it.
        videos = set.intersection(*(set(a) for a in arms.values()))
        for name, arm in arms.items():
            seqs = {}
            for v in videos:
                conds = sorted(set.intersection(*(set(a[v]) for a in arms.values())))
                if len(conds) >= args.min_reps:
                    seqs[v] = [arm[v][c] for c in conds]
            summary[name] = {"min_reps": args.min_reps, **walk_vs_null(seqs, args.perms)}

    args.out.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
