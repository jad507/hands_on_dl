r"""
The cascade test on StressTest's meaning task (SSR), with a local model.

The audio LLMs chose the speaker's meaning at chance (doc 09 section 12). The
StressTest paper's cascade -- WhiStress marks the stressed words in the
transcript, then text-only GPT-4o picks the meaning -- got 83%. This asks
whether a LOCAL model can do the reading half: same two-choice question, text
only, the transcript given three ways:

    plain      i didn't say he stole the money.        (no stress information)
    whistress  i didn't say HE stole the money.        (WhiStress's prediction)
    gold       i didn't say HE stole the money.        (the dataset's true stress)

and, to put the detectors on equal footing (one word each, the one it rates
most stressed; score_stresstest.py's top-1 arms):

    whistress_top1   WhiStress's single top word (measure_whistress.py)
    wavelet          the Wavelet Prosody Toolkit's top word (measure_classical.py)
    praat            the Praat z-score's top word (measure_classical.py)

so the pre-transformer detectors get a score on the meaning task too: is a
signal-processing detector good enough to feed the reader?

The transcript is lower-cased and only stressed words are in CAPITALS, so a
stressed "I" shows as "I" and an unstressed one as "i". CAPITALS, not *italics*,
because that is the marking that survives Concord's word splitter. WhiStress's
prediction is its gt_text run (validate_whistress.py: given the transcript,
it marks each word), so all three variants share the same words.

plain measures what the text alone gives away (expected near 50%, since each
sentence appears with both meanings); gold is the ceiling for this model as a
reader; whistress is the realistic pipeline. Thinking off (like the paper's
GPT-4o), prompt, parsing and seeds from reproduce_stresstest_gemma.py.

    python cascade_stresstest.py --model google/gemma-4-E4B-it --ple-cpu
    python cascade_stresstest.py --backend server --model nemotron-3-nano-omni-q4km
    python cascade_stresstest.py ... --dataset stresspresso        # the paper's second benchmark
Outputs: stress_search/stresstest_repro/<model>/cascade_<variant>.jsonl, cascade_summary.json
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import reproduce_stresstest_gemma as R  # noqa: E402

HERE = Path(__file__).resolve().parent
PROMPT = ('The speaker said: "{sentence}"\n{note}'
          "Out of the following answers, according to the speaker's stressed words, "
          "what is most likely the underlying intention of the speaker?\n"
          "1. {answer_1}\n2. {answer_2}\nAnswer:")
NOTE = "Words in CAPITAL LETTERS were stressed by the speaker.\n"
VARIANTS = ("plain", "whistress", "gold", "whistress_top1", "wavelet", "praat")


def marked(transcription: str, stressed: list[int]) -> str:
    words = transcription.lower().split()
    return " ".join(w.upper() if i < len(stressed) and stressed[i] else w for i, w in enumerate(words))


DATASET = "stresstest"  # --dataset; stresspresso = the paper's second benchmark
PAPER = {"stresstest": {"whistress_to_gpt4o": 0.834, "gold_to_gpt4o": 0.862},
         "stresspresso": {"whistress_to_gpt4o": 0.797, "gold_to_gpt4o": 0.836}}


def whistress_marks() -> dict[str, list[int]]:
    """st_NNN -> WhiStress's per-word 0/1 on the true transcript."""
    ids = {}
    with open(HERE / "stress_search" / DATASET / "manifest.csv", newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            ids[(r["transcription_id"], r["interpretation_id"])] = r["video_id"]
    out = {}
    with open(HERE / "stress_search" / f"whistress_{DATASET}_validation.csv", newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if r["mode"] == "gt_text":
                out[ids[(r["transcription_id"], r["interpretation_id"])]] = json.loads(r["pred_binary"])
    return out


def top1_marks() -> dict[str, dict[str, list[int]]]:
    """variant -> st_NNN -> one-hot on the detector's top word ([] if it had none)."""
    out: dict[str, dict[str, list[int]]] = {"whistress_top1": {}, "wavelet": {}, "praat": {}}
    for name, file, col in (("whistress_top1", f"whistress_{DATASET}_top1.csv", "top_index"),
                            ("wavelet", f"classical_{DATASET}.csv", "wavelet_top_index"),
                            ("praat", f"classical_{DATASET}.csv", "praat_top_index")):
        with open(HERE / "stress_search" / file, newline="", encoding="utf-8") as f:
            for r in csv.DictReader(f):
                n = len(r["phrase"].split())
                out[name][r["video_id"]] = ([int(i == int(r[col])) for i in range(n)] if r[col] != "" else [])
    return out


def wald(k: int, n: int) -> list[float]:
    p = k / n
    h = 1.96 * math.sqrt(p * (1 - p) / n)
    return [round(max(0.0, p - h), 3), round(min(1.0, p + h), 3)]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    ap.add_argument("--backend", choices=("gemma", "server"), default="gemma")
    ap.add_argument("--model", default=R.MODEL_ID, help="HF id (gemma) or a label (server)")
    ap.add_argument("--ple-cpu", action="store_true")
    ap.add_argument("--variants", default=",".join(VARIANTS))
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--dataset", choices=sorted(PAPER), default="stresstest",
                    help="stresspresso: the paper's second benchmark (4 speakers; outputs under stresspresso_repro/)")
    args = ap.parse_args()

    global DATASET
    R.MODEL_ID, R.PLE_CPU = args.model, args.ple_cpu
    DATASET = R.DATASET = args.dataset
    R.AUDIO = HERE / "stress_search" / DATASET / "audio"
    out_dir = HERE / "stress_search" / f"{DATASET}_repro" / args.model.split("/")[-1]
    out_dir.mkdir(parents=True, exist_ok=True)
    if args.backend == "server":
        import reproduce_stresstest_server as S
        R.gemma = S.server_generate  # the rule-failure judge calls R.gemma too

    samples = R.load_samples()
    if args.limit:
        samples = samples[: args.limit]
    ws, top1 = whistress_marks(), top1_marks()
    summary = {"model": args.model, "backend": args.backend, "thinking": False,
               "dataset": DATASET, "paper_cascade_ssr": PAPER[DATASET],
               "results": {}}
    for variant in args.variants.split(","):
        path = out_dir / f"cascade_{variant}.jsonl"
        done = {json.loads(x)["id"] for x in open(path, encoding="utf-8")} if path.exists() else set()
        todo = [s for s in samples if s["id"] not in done]
        print(f"\n== {variant}: {len(done)} done, {len(todo)} to go", flush=True)
        with open(path, "a", encoding="utf-8") as fh:
            for j, s in enumerate(todo, 1):
                stress = ({"plain": [], "whistress": ws.get(s["id"], []), "gold": s["stress_binary"]}[variant]
                          if variant in ("plain", "whistress", "gold") else top1[variant].get(s["id"], []))
                prompt = PROMPT.format(sentence=marked(s["transcription"], stress),
                                       note="" if variant == "plain" else NOTE,
                                       answer_1=s["answers"][0], answer_2=s["answers"][1])
                try:
                    res = R.gemma(prompt, None, False, s["idx"], max_new_tokens=512)
                    # "The correct answer is **1. ...**": the first bolded option number
                    m = re.search(r"\*\*\s*([12])[.)]", res["content"])
                    pred, how = ((int(m[1]), "rule_bold_option") if m
                                 else R.parse_ssr(res["content"], s["answers"], prompt, s["idx"]))
                except Exception as e:  # keep going; retried on resume
                    print(f"  {s['id']} FAILED: {type(e).__name__}: {e}", flush=True)
                    continue
                row = {"id": s["id"], "variant": variant, "input_prompt": prompt,
                       "model_answer": res["content"], "pred": pred, "label": s["label"] + 1,
                       "correct": pred == s["label"] + 1, "parse_method": how,
                       "elapsed_s": res["elapsed_s"]}
                fh.write(json.dumps(row, ensure_ascii=False) + "\n")
                fh.flush()
                if j % 20 == 0 or j == len(todo):
                    print(f"  [{j}/{len(todo)}] {s['id']} pred={pred} label={s['label'] + 1}", flush=True)
        rows = [json.loads(x) for x in open(path, encoding="utf-8")]
        k = sum(r["correct"] for r in rows)
        print(f"  {variant}: {k}/{len(rows)} = {k / len(rows):.3f}", flush=True)
    # the summary covers every variant on disk, not just this invocation's
    for variant in VARIANTS:
        path = out_dir / f"cascade_{variant}.jsonl"
        rows = [json.loads(x) for x in open(path, encoding="utf-8")] if path.exists() else []
        if not rows:
            continue
        k = sum(r["correct"] for r in rows)
        methods: dict[str, int] = {}
        for r in rows:
            methods[r["parse_method"]] = methods.get(r["parse_method"], 0) + 1
        summary["results"][variant] = {"n": len(rows), "accuracy": round(k / len(rows), 3),
                                       "wald95": wald(k, len(rows)), "parse_methods": methods}
    (out_dir / "cascade_summary.json").write_text(json.dumps(summary, indent=1), encoding="utf-8")
    print(json.dumps(summary["results"], indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
