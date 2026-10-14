r"""
Are the LLMs' unprompted emphasis marks right? Scored on StressTest's labels.

On the YouTube/TikTok corpus an LLM transcript's emphasis mark (*word*,
**word**, or CAPITALS) could only be compared with WhiStress. Here the same
transcription prompts (measure_llamacpp_stress.py / measure_llm_stress.py)
were run on StressTest's 218 labelled clips, so each mark can be checked
against the words the actor really stressed.

Per model and prompt:
    marked        clips whose transcript marks at least one word of the sentence
    hit           marked clips where a marked word is a truly stressed word
    precision     hit / marked      (when it marks, is it right?)
    recall        hit / all clips   (how often does the transcript carry the stress?)
Wald 95% intervals (doc 09 section 13). WhiStress's top word is right on
0.982 of these clips (score_stresstest.py), for comparison.

    python score_markup_stresstest.py      # every *_stresstest.csv present
"""
from __future__ import annotations

import csv
import json
import math
import re
from pathlib import Path

from summarize_llm_markup import emphasized, norm

HERE = Path(__file__).resolve().parent
SS = HERE / "stress_search"
RUNS = {  # file -> (model label, prompt columns)
    "llamacpp_nemotron-3-nano-omni-q4km_stresstest.csv": ("Nemotron 3 Nano Omni Q4", ("vendor_asr", "plain", "general")),
    "llm_stress_e4b_stresstest.csv": ("Gemma-4 E4B", ("plain", "general")),
    "llm_stress_e2b_stresstest.csv": ("Gemma-4 E2B", ("plain", "general")),
}


def wald(k: int, n: int) -> list[float]:
    if n == 0:
        return [0.0, 0.0]
    p = k / n
    h = 1.96 * math.sqrt(p * (1 - p) / n)
    return [round(max(0.0, p - h), 3), round(min(1.0, p + h), 3)]


def main() -> None:
    gold = {}
    with open(SS / "stresstest" / "manifest.csv", newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            words = [norm(w) for w in r["phrase"].split()]
            gold[r["video_id"]] = (set(words), {norm(w) for w in json.loads(r["gt_words"])})
    out = {"n_clips": len(gold), "whistress_top1": 0.982, "runs": {}}
    for name, (label, prompts) in RUNS.items():
        path = SS / name
        if not path.exists():
            continue
        rows = list(csv.DictReader(open(path, encoding="utf-8")))
        for prompt in prompts:
            marked = hit = 0
            examples = []
            for r in rows:
                sentence, stressed = gold[r["video_id"]]
                marks = {t for m in emphasized(r.get(f"{prompt}_content") or "") for t in m.split()} & sentence
                if not marks:
                    continue
                marked += 1
                hit += bool(marks & stressed)
                if len(examples) < 8:
                    examples.append({"id": r["video_id"], "marks": sorted(marks), "gold": sorted(stressed),
                                     "text": (r[f"{prompt}_content"] or "")[:100]})
            n = len(rows)
            out["runs"][f"{label} / {prompt}"] = {
                "n": n, "marked": marked, "hit": hit,
                "marked_rate": round(marked / n, 3) if n else None, "marked_wald95": wald(marked, n),
                "precision": round(hit / marked, 3) if marked else None, "precision_wald95": wald(hit, marked),
                "recall": round(hit / n, 3) if n else None, "recall_wald95": wald(hit, n),
                "examples": examples}
            print(f"{label:26s} {prompt:10s} n={n:3d}  marked {marked:3d}  hit {hit:3d}"
                  + (f"  precision {hit / marked:.2f}" if marked else "") + f"  recall {hit / max(n, 1):.3f}")
    (SS / "markup_stresstest_scores.json").write_text(json.dumps(out, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
