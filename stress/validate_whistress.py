r"""
Reproduce WhiStress's published number on StressTest before trusting it on
our corpus.

WhiStress (slp-rl, Interspeech 2025) is the single-utterance stress detector
doc 09 section 7.4 picked to replace the cross-repetition detector's
baseline: one clip in, a binary stressed/unstressed label per word out, no
second reading of the same sentence needed. It runs here from a local clone
(default ~/src/WhiStress, override with WHISTRESS_DIR) patched for
transformers 5 (branch `transformers5-compat`: decoder layers now return a
tensor instead of a tuple, so the repo's `outputs[0]` sliced off the batch
dimension). That patch is only trustworthy if the patched model reproduces
the authors' own number, so this checks it against one:

    StressTest (slprl/StressTest, 218 studio recordings by one professional
    actor, 101 texts x 2+ stress patterns each) -- Yosha et al. 2025,
    Table 3, sentence stress detection: WhiStress P 88.5 / R 88.1 / F1 88.3,
    word-level binary, ground-truth transcription supplied.

Two modes, both on every sample:

    gt_text     transcription supplied (the published protocol; the number
                to reproduce)
    audio_only  WhiStress transcribes the audio itself -- how it would
                actually run on our clips, where no clean transcript exists.
                Predicted words are aligned to the reference words before
                scoring, so a transcription error costs that word, not the
                rest of the sentence.

Per-sample rows go to --out as each finishes (resumable, same convention as
measure_llm_stress.py); the summary prints at the end and lands in
--summary.

Usage
-----
    python validate_whistress.py
    python validate_whistress.py --limit 10          # smoke test
"""

from __future__ import annotations

import argparse
import csv
import difflib
import json
import os
import re
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from verify_stress import hardware_info  # noqa: E402

WHISTRESS_DIR = Path(os.environ.get("WHISTRESS_DIR", Path.home() / "src" / "WhiStress"))
sys.path.insert(0, str(WHISTRESS_DIR))

PUBLISHED = {"precision": 0.885, "recall": 0.881, "f1": 0.883}
# the paper's WhiStress SSD F1 on its second benchmark (4 Expresso speakers)
PUBLISHED_BY_DATASET = {"slprl/StressTest": PUBLISHED, "slprl/StressPresso": {"f1": 0.835}}
MODES = ("gt_text", "audio_only")
FIELDS = ["mode", "transcription_id", "interpretation_id", "transcription", "gt_stressed",
          "pred_transcription", "pred_stressed", "gt_binary", "pred_binary",
          "words_aligned", "exact_set_match", "seconds"]


def norm(word: str) -> str:
    return re.sub(r"[^\w']", "", word.lower())


def align(ref_words: list[str], pred_pairs: list[tuple[str, int]]) -> tuple[list[int], int]:
    """Map predicted (word, stress) pairs onto reference word positions.

    Returns one label per reference word (unmatched reference words get 0,
    i.e. "not detected as stressed") and how many reference words were mapped.

    Identical words map directly; a same-length run of substituted words maps
    position by position, so a mishearing ("stole that money" for "stole the
    money") keeps the label of the word it replaced. Insertions, deletions
    and unequal-length substitutions stay unmapped.
    """
    ref = [norm(w) for w in ref_words]
    pred = [norm(w) for w, _ in pred_pairs]
    labels = [0] * len(ref)
    matched = 0
    for op, a0, a1, b0, b1 in difflib.SequenceMatcher(a=ref, b=pred, autojunk=False).get_opcodes():
        if op == "equal" or (op == "replace" and a1 - a0 == b1 - b0):
            for k in range(a1 - a0):
                labels[a0 + k] = pred_pairs[b0 + k][1]
                matched += 1
    return labels, matched


def prf(pred: list[int], gold: list[int]) -> dict:
    tp = sum(1 for p, g in zip(pred, gold) if p == 1 and g == 1)
    fp = sum(1 for p, g in zip(pred, gold) if p == 1 and g == 0)
    fn = sum(1 for p, g in zip(pred, gold) if p == 0 and g == 1)
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return {"precision": precision, "recall": recall, "f1": f1, "tp": tp, "fp": fp, "fn": fn}


def summarize(rows: list[dict]) -> dict:
    out = {}
    for mode in MODES:
        mine = [r for r in rows if r["mode"] == mode]
        if not mine:
            continue
        pred = [x for r in mine for x in json.loads(r["pred_binary"])]
        gold = [x for r in mine for x in json.loads(r["gt_binary"])]
        n_words = sum(len(json.loads(r["gt_binary"])) for r in mine)
        out[mode] = {
            "n_samples": len(mine),
            **prf(pred, gold),
            "exact_set_match": sum(r["exact_set_match"] == "True" for r in mine) / len(mine),
            "words_aligned": sum(int(r["words_aligned"]) for r in mine) / n_words,
        }
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", type=Path, default=HERE / "stress_search" / "whistress_stresstest_validation.csv")
    ap.add_argument("--summary", type=Path, default=HERE / "stress_search" / "whistress_stresstest_summary.json")
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--device", default="cuda")
    ap.add_argument("--dataset", default="slprl/StressTest", choices=sorted(PUBLISHED_BY_DATASET),
                    help="slprl/StressPresso for the paper's second benchmark (pass --out/--summary too)")
    args = ap.parse_args()

    import numpy as np
    from datasets import Audio, load_dataset
    from whistress import WhiStressInferenceClient

    hw = hardware_info()
    print(f"host: {hw.get('host')}  gpu: {hw.get('gpu_name', 'none')}  whistress: {WHISTRESS_DIR}", flush=True)

    ds = load_dataset(args.dataset, split="test")
    # decode=False + soundfile: no dependency on whichever audio backend
    # `datasets` would otherwise pick for this version.
    ds = ds.cast_column("audio", Audio(decode=False))
    if args.limit:
        ds = ds.select(range(min(args.limit, len(ds))))

    done: set[tuple[str, str, str]] = set()
    rows: list[dict] = []
    if args.out.exists():
        with args.out.open(newline="", encoding="utf-8") as f:
            for r in csv.DictReader(f):
                rows.append(r)
                done.add((r["mode"], r["transcription_id"], r["interpretation_id"]))
        print(f"resuming: {len(done)} rows already in {args.out.name}", flush=True)

    client = WhiStressInferenceClient(device=args.device)

    import io
    import soundfile as sf

    new_file = not args.out.exists()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        if new_file:
            w.writeheader()
        for i, s in enumerate(ds):
            raw = s["audio"]
            arr, sr = sf.read(io.BytesIO(raw["bytes"]) if raw.get("bytes") else raw["path"], dtype="float32")
            if arr.ndim > 1:
                arr = arr.mean(axis=1)
            audio = {"array": np.asarray(arr), "sampling_rate": sr}
            ref_words = s["transcription"].split()
            gold = list(s["stress_pattern"]["binary"])
            assert len(gold) == len(ref_words), (s["transcription"], gold)
            for mode in MODES:
                key = (mode, s["transcription_id"], s["interpretation_id"])
                if key in done:
                    continue
                t0 = time.time()
                pairs = client.predict(audio=audio, transcription=s["transcription"] if mode == "gt_text" else None,
                                       return_pairs=True)
                labels, matched = align(ref_words, pairs)
                row = {
                    "mode": mode,
                    "transcription_id": s["transcription_id"],
                    "interpretation_id": s["interpretation_id"],
                    "transcription": s["transcription"],
                    "gt_stressed": json.dumps(s["stress_pattern"]["words"]),
                    "pred_transcription": " ".join(wd for wd, _ in pairs),
                    "pred_stressed": json.dumps([wd for wd, st in pairs if st == 1]),
                    "gt_binary": json.dumps(gold),
                    "pred_binary": json.dumps(labels),
                    "words_aligned": matched,
                    "exact_set_match": labels == gold,
                    "seconds": round(time.time() - t0, 3),
                }
                w.writerow(row)
                f.flush()
                rows.append({k: str(v) for k, v in row.items()})
            if (i + 1) % 25 == 0:
                print(f"  {i + 1}/{len(ds)}", flush=True)

    published = PUBLISHED_BY_DATASET[args.dataset]
    summary = {"dataset": args.dataset, "published_stresstest_table3": published,
               "reproduced": summarize(rows), "hardware": hw}
    args.summary.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary["reproduced"], indent=2))
    print(f"published (gt_text protocol): F1 {published['f1']:.3f}")


if __name__ == "__main__":
    main()
