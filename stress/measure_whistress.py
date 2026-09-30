r"""
Single-utterance stress detection across the corpus, with WhiStress.

Why this exists
---------------
verify_stress.py finds the stressed word by scoring each word against ITS OWN
average across the other repetitions of the same sentence (doc 09 section
7.2). That only works because demonstration videos repeat the sentence on
purpose; real speech says a sentence once. WhiStress (slp-rl, Interspeech
2025) takes one clip and labels each word stressed/unstressed with no second
reading, and validate_whistress.py reproduces its published StressTest
number on this machine (F1 0.884 vs 0.883), so it is the single-utterance
arm.

It runs here on every `rep_NN` clip in clip_manifest.csv -- one isolated
utterance each, with the other repetitions nowhere in its input -- so any
contrast it recovers across a video's reps was found one sentence at a time.

Per clip it records WhiStress's own transcript, its binary label for every
word, and the stress probability behind each label (softmax of the head's
logits, max over a word's sub-tokens -- the same merge rule the repo uses for
labels). Probabilities give a one-word-per-rep answer (`top_index`, the
phrase word with the highest stress probability) that lines up with
verify_stress.py's one-word-per-rep `stressed_index`, so the two can be
scored with the same distinct / coverage / walk statistics.

Rows are flushed to --out as each clip finishes and skipped on rerun
(measure_llm_stress.py's convention); --summarize aggregates whatever is
there against the detector's evidence without touching the GPU.

Usage
-----
    python measure_whistress.py                 # every rep clip
    python measure_whistress.py --limit 10      # smoke test
    python measure_whistress.py --summarize     # aggregate only
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from verify_stress import hardware_info, local_path, longest_walk  # noqa: E402
from validate_whistress import align  # noqa: E402

WHISTRESS_DIR = Path(os.environ.get("WHISTRESS_DIR", Path.home() / "src" / "WhiStress"))
sys.path.insert(0, str(WHISTRESS_DIR))

# Whisper's feature extractor pads or truncates to 30 s; anything past that is
# silently never heard.
WHISPER_WINDOW_S = 30.0
FIELDS = ["video_id", "condition", "phrase", "bucket", "qa_pass", "duration_s", "truncated",
          "pred_transcription", "pred_words", "pred_labels", "pred_probs",
          "phrase_labels", "phrase_probs", "words_aligned", "n_stressed", "top_index", "top_word",
          "seconds"]


def load_model(device: str):
    from whistress.inference_client.utils import get_loaded_model
    return get_loaded_model(device)


def word_stress(model, audio, sr: int, device: str) -> list[tuple[str, int, float]]:
    """WhiStress on one clip, audio only: [(word, label, p_stressed), ...].

    Mirrors whistress.inference_client.utils.inference_from_audio (same
    right-shift of the head's outputs onto the transcript tokens, same
    special-token filter, same sub-token merge) but keeps the probability
    as well as the argmax.
    """
    import torch
    import torch.nn.functional as F
    from whistress.inference_client.utils import (get_word_emphasis_pairs, merge_stressed_tokens,
                                                  prepare_audio)

    arr = prepare_audio({"array": audio, "sampling_rate": sr})
    feats = model.processor.feature_extractor(arr, sampling_rate=16000, return_tensors="pt")["input_features"]
    with torch.inference_mode():
        out = model.generate_dual(input_features=feats.to(device))
    head = F.softmax(out.logits, dim=-1)
    preds = torch.argmax(head, dim=-1)
    probs = head[..., 1]

    def shift(t):
        return torch.cat((t[:, -1:], t[:, :-1]), dim=1)[0]

    tokens = out.preds[0]
    labels = merge_stressed_tokens(get_word_emphasis_pairs(tokens, shift(preds), model.processor))
    p = merge_stressed_tokens(get_word_emphasis_pairs(tokens, shift(probs.float()), model.processor))
    assert [w for w, _ in labels] == [w for w, _ in p]
    return [(w.strip(), int(lab), float(pr)) for (w, lab), (_, pr) in zip(labels, p)]


def measure(args) -> None:
    import soundfile as sf

    rows = [r for r in csv.DictReader(open(args.manifest, encoding="utf-8"))
            if r["condition"].startswith(tuple(args.conditions.split(",")))]
    if args.limit:
        rows = rows[:args.limit]

    done = set()
    if args.out.exists():
        done = {(r["video_id"], r["condition"]) for r in csv.DictReader(open(args.out, encoding="utf-8"))}
        print(f"resuming: {len(done)} clips already in {args.out.name}", flush=True)
    todo = [r for r in rows if (r["video_id"], r["condition"]) not in done]

    hw = hardware_info()
    print(f"host: {hw.get('host')}  gpu: {hw.get('gpu_name', 'none')}  "
          f"{len(todo)} of {len(rows)} rep clips to measure", flush=True)
    manifest = args.out.with_name(args.out.stem + "_run_manifest.json")
    manifest.write_text(json.dumps({"hardware": hw, "whistress_dir": str(WHISTRESS_DIR),
                                    "started": time.strftime("%Y-%m-%d %H:%M:%S")}, indent=2) + "\n")
    if not todo:
        return

    model = load_model(args.device)
    new_file = not args.out.exists()
    with args.out.open("a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        if new_file:
            w.writeheader()
        for i, r in enumerate(todo, 1):
            t0 = time.time()
            audio, sr = sf.read(local_path(r["path"]), dtype="float32")
            if audio.ndim > 1:
                audio = audio.mean(axis=1)
            dur = len(audio) / sr
            words = word_stress(model, audio, sr, args.device)
            phrase = r["phrase"].split()
            phrase_labels, matched = align(phrase, [(wd, lab) for wd, lab, _ in words])
            phrase_probs, _ = align(phrase, [(wd, pr) for wd, _, pr in words])
            top = max(range(len(phrase)), key=lambda k: phrase_probs[k]) if matched else None
            row = {
                "video_id": r["video_id"], "condition": r["condition"], "phrase": r["phrase"],
                "bucket": r["bucket"], "qa_pass": r["qa_pass"],
                "duration_s": round(dur, 2), "truncated": dur > WHISPER_WINDOW_S,
                "pred_transcription": " ".join(wd for wd, _, _ in words),
                "pred_words": json.dumps([wd for wd, _, _ in words]),
                "pred_labels": json.dumps([lab for _, lab, _ in words]),
                "pred_probs": json.dumps([round(pr, 4) for _, _, pr in words]),
                "phrase_labels": json.dumps(phrase_labels),
                "phrase_probs": json.dumps([round(x, 4) for x in phrase_probs]),
                "words_aligned": matched,
                "n_stressed": sum(lab for _, lab, _ in words),
                "top_index": "" if top is None else top,
                "top_word": "" if top is None else phrase[top],
                "seconds": round(time.time() - t0, 3),
            }
            w.writerow(row)
            f.flush()
            if i % 25 == 0 or i == len(todo):
                print(f"  {i}/{len(todo)}  {r['video_id']} {r['condition']}: "
                      f"{row['top_word'] or '-'}  ({row['pred_transcription'][:60]})", flush=True)


def seq_stats(indices: list[int], n_words: int) -> dict:
    distinct = len(set(indices))
    return {"distinct": distinct, "coverage": round(distinct / n_words, 3) if n_words else 0,
            "walk": longest_walk(indices), "reps": len(indices)}


def summarize(args) -> dict:
    """Per video: WhiStress one-word-per-rep sequence vs the detector's
    cross-repetition sequence and its single-utterance fallback (raw
    within-sentence argmax, the path verify_stress.py takes with one rep),
    both recomputed from the detector's own stored per-rep profiles."""
    rows = list(csv.DictReader(open(args.out, encoding="utf-8")))
    evidence = json.load(open(args.evidence, encoding="utf-8")) if args.evidence.exists() else {}

    by_video: dict[str, list[dict]] = {}
    for r in rows:
        if args.qa_only and r["qa_pass"] != "True":
            continue
        by_video.setdefault(r["video_id"], []).append(r)

    per_video = []
    for vid, reps in sorted(by_video.items()):
        reps.sort(key=lambda r: r["condition"])
        phrase = reps[0]["phrase"].split()
        ws = [int(r["top_index"]) for r in reps if r["top_index"] != ""]
        rec = {"video_id": vid, "n_words": len(phrase), "whistress": seq_stats(ws, len(phrase)),
               "whistress_zero_stressed": sum(int(r["n_stressed"]) == 0 for r in reps),
               "whistress_words_aligned": round(sum(int(r["words_aligned"]) for r in reps)
                                                / (len(phrase) * len(reps)), 3)}
        ev = evidence.get(vid)
        if ev and ev["phrase"].split() == phrase:
            cross = ev["stressed_index"]
            raw = [max(range(len(p)), key=lambda k: p[k]["prominence"]) for p in ev["profiles"]]
            rec["detector_cross_rep"] = seq_stats(cross, len(phrase))
            rec["detector_single_utt"] = seq_stats(raw, len(phrase))
            # Rep-by-rep agreement only means something when both saw the same
            # repetitions in the same order.
            if len(cross) == len(reps) == len(ws):
                rec["agree_whistress_cross"] = sum(a == b for a, b in zip(ws, cross)) / len(ws)
                rec["agree_single_cross"] = sum(a == b for a, b in zip(raw, cross)) / len(raw)
        per_video.append(rec)

    def agg(vals: list[dict]) -> dict | None:
        if not vals:
            return None
        return {"n_videos": len(vals),
                "mean_distinct": round(sum(v["distinct"] for v in vals) / len(vals), 2),
                "mean_coverage": round(sum(v["coverage"] for v in vals) / len(vals), 3),
                "distinct_ge3": sum(v["distinct"] >= 3 for v in vals),
                "distinct_ge5": sum(v["distinct"] >= 5 for v in vals),
                "distinct_eq1": sum(v["distinct"] == 1 for v in vals)}

    def mean_of(key: str):
        vals = [v[key] for v in per_video if key in v]
        return {"n_videos": len(vals), "mean": round(sum(vals) / len(vals), 3)} if vals else None

    # Same videos for every method, or the comparison is not like for like.
    both = [v for v in per_video if "detector_cross_rep" in v]
    summary = {
        "clips": len(rows), "videos": len(per_video), "qa_only": args.qa_only,
        "all_videos": {"whistress": agg([v["whistress"] for v in per_video])},
        "videos_with_detector_evidence": {
            k: agg([v[k] for v in both])
            for k in ("whistress", "detector_single_utt", "detector_cross_rep")},
        "rep_agreement_with_cross_rep_detector": {
            "whistress": mean_of("agree_whistress_cross"),
            "detector_single_utt": mean_of("agree_single_cross")},
        "per_video": per_video,
    }
    args.summary.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in summary.items() if k != "per_video"}, indent=2))
    return summary


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--manifest", type=Path, default=HERE / "stress_search" / "clip_manifest.csv")
    ap.add_argument("--evidence", type=Path, default=HERE / "stress_search" / "stress_evidence.json")
    ap.add_argument("--out", type=Path, default=HERE / "stress_search" / "whistress_reps.csv")
    ap.add_argument("--summary", type=Path, default=HERE / "stress_search" / "whistress_reps_summary.json")
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--device", default="cuda")
    ap.add_argument("--conditions", default="rep_", help="comma-separated condition prefixes to measure")
    ap.add_argument("--summarize", action="store_true", help="aggregate existing rows only; no model")
    ap.add_argument("--all-clips", dest="qa_only", action="store_false",
                    help="include rep clips that failed cut QA in the summary")
    args = ap.parse_args()
    if not args.summarize:
        measure(args)
    # The per-video walk summary only means something for a video's repetitions;
    # labelled sets (StressTest) are scored by score_stresstest.py.
    if args.conditions == "rep_":
        summarize(args)


if __name__ == "__main__":
    main()
