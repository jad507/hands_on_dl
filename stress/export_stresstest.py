r"""
Write StressTest to disk as wav files plus a manifest in clip_manifest.csv's
shape, so every measurement arm reads the same labelled recordings the same
way the corpus clips are read.

StressTest (slprl/StressTest, Yosha et al. 2025): 218 studio recordings by
one professional actor, 101 texts each read with 2+ stress placements, the
stressed word(s) labelled per reading. It is the labelled benchmark
validate_whistress.py already reproduced WhiStress's published number on.

Output (media gitignored, manifest tracked):
    stress_search/stresstest/audio/st_NNN.wav
    stress_search/stresstest/manifest.csv
        video_id, condition, path, phrase, bucket, qa_pass   (clip_manifest columns)
        transcription_id, interpretation_id, gt_binary, gt_words, intonation

StressPresso (slprl/StressPresso), the paper's second benchmark -- 202 readings
by 4 Expresso speakers, same fields -- goes to stress_search/stresspresso/
(sp_NNN.wav) with --dataset stresspresso.

Usage
-----
    python export_stresstest.py
    python export_stresstest.py --dataset stresspresso
"""

from __future__ import annotations

import argparse
import csv
import io
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
DATASETS = {"stresstest": ("slprl/StressTest", "st"), "stresspresso": ("slprl/StressPresso", "sp")}
FIELDS = ["video_id", "condition", "path", "phrase", "bucket", "qa_pass",
          "transcription_id", "interpretation_id", "gt_binary", "gt_words", "intonation"]


def main() -> None:
    import soundfile as sf
    from datasets import Audio, load_dataset

    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    ap.add_argument("--dataset", choices=sorted(DATASETS), default="stresstest")
    args = ap.parse_args()
    repo, prefix = DATASETS[args.dataset]
    OUT = HERE / "stress_search" / args.dataset
    ds = load_dataset(repo, split="test").cast_column("audio", Audio(decode=False))
    (OUT / "audio").mkdir(parents=True, exist_ok=True)
    with open(OUT / "manifest.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        for i, s in enumerate(ds):
            raw = s["audio"]
            arr, sr = sf.read(io.BytesIO(raw["bytes"]) if raw.get("bytes") else raw["path"], dtype="float32")
            path = OUT / "audio" / f"{prefix}_{i:03d}.wav"
            sf.write(path, arr, sr)
            w.writerow({
                "video_id": f"{prefix}_{i:03d}", "condition": args.dataset, "path": path.relative_to(HERE).as_posix(),
                "phrase": s["transcription"], "bucket": "", "qa_pass": "True",
                "transcription_id": s["transcription_id"], "interpretation_id": s["interpretation_id"],
                "gt_binary": json.dumps(list(s["stress_pattern"]["binary"])),
                "gt_words": json.dumps(s["stress_pattern"]["words"]),
                "intonation": s["intonation"],
            })
    print(f"wrote {len(ds)} clips to {OUT}")


if __name__ == "__main__":
    main()
