r"""
Score every method against the human stress labels on the YouTube/TikTok clips.

Labels come from label_server.py (labels/clip_labels.csv, v3 clips). Per clip,
the label used is the FIRST answer given before seeing WhiStress's pick
(whistress_seen = 0), because the labels grade WhiStress too. Only clips whose
blind answer names stressed word(s) are scored; "no clear stress", "can't tell"
and bad clips are counted and reported, not scored. Videos excluded in the review
(verify_stress.excluded_videos) are dropped, and so are single clips marked
bad in the review (verify_stress.bad_clips).

A method is right on a clip when the word it rates most stressed is one the
labeller marked. Methods: WhiStress, wavelet, Praat (top word), the "last word"
text-only rule, chance (1 / sentence length, averaged), and each LLM transcript's
emphasis marks (right = a marked word is a labelled one; a transcript with no
mark is wrong). Wald 95% intervals, clips treated as independent (they are not
quite: several readings per video). Beside each, the same method's StressTest
top-1 (stresstest_scores.json), for the controlled-vs-real-world comparison.

    python score_corpus_labels.py
"""
from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path

from summarize_llm_markup import emphasized, norm
from verify_stress import LABELS, bad_clips, excluded_videos

HERE = Path(__file__).resolve().parent
SS = HERE / "stress_search"


def wald(k: int, n: int) -> list[float]:
    if n == 0:
        return [0.0, 0.0]
    p = k / n
    h = 1.96 * math.sqrt(p * (1 - p) / n)
    return [round(max(0.0, p - h), 3), round(min(1.0, p + h), 3)]


def blind_labels(path: Path) -> dict[tuple[str, str], dict]:
    first = {}
    if path.exists():
        with open(path, newline="", encoding="utf-8") as f:
            for r in csv.DictReader(f):
                if r.get("whistress_seen", "0") == "0":
                    first.setdefault((r["video_id"], r["condition"]), r)
    return first


def read(path: Path) -> dict[tuple[str, str], dict]:
    if not path.exists():
        return {}
    with open(path, newline="", encoding="utf-8") as f:
        return {(r["video_id"], r["condition"]): r for r in csv.DictReader(f)}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    ap.add_argument("--labels", type=Path, default=LABELS / "clip_labels.csv")
    ap.add_argument("--tag", default="v3", help="which cut's result files: *_<tag>.csv")
    ap.add_argument("--out", type=Path, default=SS / "corpus_label_scores.json")
    args = ap.parse_args()
    t = args.tag

    excluded, bad = excluded_videos(), bad_clips()
    labels = {k: r for k, r in blind_labels(args.labels).items() if k[0] not in excluded and k not in bad}
    status = {}
    for r in labels.values():
        key = r["status"] + (f":{r['reason']}" if r["reason"] else "")
        status[key] = status.get(key, 0) + 1
    scored = {k: r for k, r in labels.items() if r["status"] == "stressed"}

    ws, cl = read(SS / f"whistress_reps_{t}.csv"), read(SS / f"classical_reps_{t}.csv")
    top_index = {  # method -> clip -> index of its top word in the phrase
        "whistress": {k: r["top_index"] for k, r in ws.items()},
        "wavelet (classical)": {k: r["wavelet_top_index"] for k, r in cl.items()},
        "praat z-score (classical)": {k: r["praat_top_index"] for k, r in cl.items()},
        "last word (text only)": {k: str(len(r["phrase"].split()) - 1) for k, r in scored.items()},
    }
    llm = {f"Nemotron / {p}": (SS / f"llamacpp_nemotron-3-nano-omni-q4km_{t}.csv", p)
           for p in ("vendor_asr", "plain", "general")}
    llm.update({f"Gemma-4 {m.upper()} / {p}": (SS / f"llm_stress_{m}_{t}.csv", p)
                for m in ("e4b", "e2b") for p in ("plain", "general")})
    st = json.loads((SS / "stresstest_scores.json").read_text())["arms"]

    out = {"labels": str(args.labels), "cut": t, "excluded_videos": len(excluded), "bad_clips_in_review": len(bad),
           "labelled_clips": len(labels), "by_status": status, "scored_clips": len(scored),
           "scored_videos": len({k[0] for k in scored}), "methods": {}}
    chance = sum(len(json.loads(r["stressed_indices"])) / len(r["phrase"].split()) for r in scored.values())
    out["methods"]["chance"] = {"n": len(scored), "accuracy": round(chance / max(len(scored), 1), 3),
                                "stresstest_top1": 0.194}
    for name, idx in top_index.items():
        k = n = 0
        for key, r in scored.items():
            i = idx.get(key, "")
            if i == "":
                continue  # method had no answer for this clip (alignment failed)
            n += 1
            k += int(i) in json.loads(r["stressed_indices"])
        out["methods"][name] = {"n": n, "correct": k, "accuracy": round(k / n, 3) if n else None,
                                "wald95": wald(k, n), "stresstest_top1": st.get(name, {}).get("top1_acc")}
    for name, (path, prompt) in llm.items():
        rows = read(path)
        if not rows:
            continue
        k = n = marked = 0
        for key, r in scored.items():
            if key not in rows:
                continue
            n += 1
            words = [norm(w) for w in r["phrase"].split()]
            gold = {words[i] for i in json.loads(r["stressed_indices"])}
            marks = {w for m in emphasized(rows[key].get(f"{prompt}_content") or "") for w in m.split()}
            marked += bool(marks & set(words))
            k += bool(marks & gold)
        out["methods"][name] = {"n": n, "correct": k, "marked": marked,
                                "accuracy": round(k / n, 3) if n else None, "wald95": wald(k, n)}
    for name, m in out["methods"].items():
        print(f"{name:28s} n={m['n']:4d}  acc {m['accuracy']}  {m.get('wald95', '')}"
              + (f"   StressTest {m['stresstest_top1']}" if m.get("stresstest_top1") is not None else ""))
    print("labels:", status, "| excluded videos:", len(excluded))
    args.out.write_text(json.dumps(out, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
