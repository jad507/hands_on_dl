r"""
Reproduce the StressTest paper's evaluation (Yosha et al., arXiv 2505.22765,
"StressTest: Can YOUR Speech LM Handle the Stress?") with a Gemma-4 audio model
as the speech LM under test (default gemma-4-E2B-it; --model for E4B or larger).

Protocol copied from the authors' code (github.com/slp-rl/StressTest,
stresstest/evaluation/src/evaluator/*), not paraphrased:

    ssr        Sentence Stress Reasoning, two-way multiple choice. Prompt 1,
               verbatim (the dataset also ships it as `audio_lm_prompt`).
               Metric: accuracy against `label` + 1.
    ssd        Sentence Stress Detection. Prompt 2, verbatim, given the
               transcription lower-cased with punctuation stripped (their
               normalize_sentence). A transcription word counts as predicted-
               stressed iff it is in the normalized predicted list (their
               process_agent_answer). Metric: binary P/R/F1 pooled over every
               word of every sample (their compute_prf_metrics).
    open_ssr   Open-ended SSR, prompt 3. Outputs are saved only: the paper
               scores them 1-5 with a GPT-4o judge, which is not run here.

The one deliberate deviation: the paper sends every free-text answer through a
GPT-4o "schema" judge to extract the chosen option / word list. Here the answer
is parsed with rules first; only when that is ambiguous is it sent to Gemma
itself (text only, no audio) with the paper's own judge prompt. Every row
records which path produced its answer (`parse_method`), so the size of this
deviation is visible in the summary.

Two conditions, run in this order so the cheap, paper-comparable one lands
first: `nothink` (enable_thinking=False; like the paper's non-reasoning
baselines) then `think` (enable_thinking=True; the setting measure_llm_stress.py
uses). Sampling uses Gemma's bundled generation defaults, seeded per sample.

Outputs, under stress_search/stresstest_repro/<model name>/:
    raw_<condition>_<task>.jsonl   one line per sample; resumable
    summary.json                   metrics, 95% CIs, parse-method counts

Usage
-----
    python reproduce_stresstest_gemma.py                    # everything
    python reproduce_stresstest_gemma.py --limit 5          # smoke test
    python reproduce_stresstest_gemma.py --conditions nothink --tasks ssr,ssd
    python reproduce_stresstest_gemma.py --model google/gemma-4-E4B-it
    python reproduce_stresstest_gemma.py --score-only
    python reproduce_stresstest_gemma.py --dataset stresspresso --conditions nothink --tasks ssr,ssd

--dataset stresspresso runs the paper's second benchmark (slprl/StressPresso:
202 readings by 4 Expresso speakers, same fields and prompts) from
stress_search/stresspresso/audio (export_stresstest.py --dataset stresspresso)
into stress_search/stresspresso_repro/<model>/.
"""

from __future__ import annotations

import argparse
import json
import math
import re
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from verify_stress import hardware_info  # noqa: E402

HERE = Path(__file__).resolve().parent
DATASETS = {"stresstest": ("slprl/StressTest", "st"), "stresspresso": ("slprl/StressPresso", "sp")}
DATASET = "stresstest"  # --dataset
AUDIO = HERE / "stress_search" / "stresstest" / "audio"
REPRO = HERE / "stress_search" / "stresstest_repro"
MODEL_ID = "google/gemma-4-E2B-it"  # overridden by --model
OUT = REPRO / MODEL_ID.split("/")[-1]

# stresstest/evaluation/src/evaluator/evaluation_prompts.yml, verbatim
# (including the trailing space after the SSD quote line).
PROMPT_SSR = ("Out of the following answers, according to the speaker's stressed words, "
              "what is most likely the underlying intention of the speaker?\n"
              "1. {answer_1}\n2. {answer_2}\nAnswer:")
PROMPT_SSD = ('The speaker said "{transcription}". \n'
              "According to the audio, what words did the speaker stress?\n"
              "Answer format: [stressed_word_1, ...]\nAnswer: ")
PROMPT_OPEN_SSR = ("According to the speaker's stressed words, what is most likely the "
                   "underlying intention of the speaker?\nAnswer:\n")

# stresstest/evaluation/src/agents/evaluator_{ssr_accuracy,stress_detection}.yml
JUDGE_SSR = '''You are a Speech-LM evaluator that helps evaluating models that have trouble in outputting a correct schema for an answer.
You are very good at outputting the correct schema according to the instructions.

INSTRUCTIONS:
Given a prompt with a question and possible answers that the Speech-LM received, and the output the model emmited, you are required to output the Speech-LM answer in a fixed format.
* The output should be aligned with the Speech-LM output, and should not include any additional information or context.
* The output should be a JSON object with a single key "answer" and a value that is the number of the correct answer according to the output of the Speech-LM.
* The answer should be an integer, either 1 or 2.

INPUT TO Speech-LM:
{input_prompt}
OUTPUT FROM Speech-LM:
{output}
YOUR EXPECTED JSON OUTPUT:'''

JUDGE_SSD = '''You are a Speech-LM evaluator that helps evaluating models that have trouble in outputting a correct schema for an answer.
You are very good at outputting the correct schema according to the instructions.

INSTRUCTIONS:
Given a prompt with a question that the Speech-LM received, and the output the model emitted, you are required to output the Speech-LM answer in a fixed format.
* The output should be aligned with the Speech-LM output, and should not include any additional information or context.
* The output should be a JSON object with a single key "answer" and a value that is a list of words according to the output of the Speech-LM.
* The answer should be a list of strings.
* If the model mistakenly outputs two or more words as a single word, you should split them into separate words.

INPUT TO Speech-LM:
{input_prompt}
OUTPUT FROM Speech-LM:
{output}
YOUR EXPECTED JSON OUTPUT:'''

CONDITIONS = {"nothink": False, "think": True}
TASKS = ("ssr", "ssd", "open_ssr")

_MODEL = None
_PROCESSOR = None
_DEVICE = None
PLE_CPU = False  # --ple-cpu

# --ple-cpu placement. E4B's bf16 weights (15.99 GB) exceed a 16 GB card, and
# device_map="auto" fills the GPU in module order and spills DECODER LAYERS to
# the CPU, so every generated token waits on PCIe. A third of E4B (2.82B of
# 8.0B params, 5.25 GiB) is the per-layer embedding table -- a lookup that
# reads one ~21 KB row per token -- so that table stays in system RAM and the
# lookup runs there, and everything that does matrix math goes to the GPU
# (~10 GiB). Same weights, same dtype; only placement differs. A device_map
# entry of "cpu" does NOT do this: accelerate treats it as offload and copies
# the whole 5.25 GiB table to the GPU on every call (first smoke test: OOM
# allocating exactly 5.25 GiB), so _load() places it by hand.


def normalize_sentence(text: str) -> str:
    """The authors' normalize_sentence: lower-case, drop punctuation."""
    return re.sub(r"[^\w\s]", "", text.lower())


def _load():
    global _MODEL, _PROCESSOR, _DEVICE
    if _MODEL is None:
        from transformers import AutoProcessor, AutoModelForMultimodalLM
        _PROCESSOR = AutoProcessor.from_pretrained(MODEL_ID)
        if not PLE_CPU:
            _MODEL = AutoModelForMultimodalLM.from_pretrained(MODEL_ID, dtype="auto", device_map="auto")
            _DEVICE = _MODEL.model.language_model.embed_tokens.weight.device
        else:
            import torch
            _MODEL = AutoModelForMultimodalLM.from_pretrained(MODEL_ID, dtype="auto")  # into RAM
            lm = _MODEL.model.language_model
            ple = lm.embed_tokens_per_layer
            lm.embed_tokens_per_layer = None  # hide it from .to()
            _MODEL.to("cuda")
            lm.embed_tokens_per_layer = ple   # back, still in RAM
            _DEVICE = lm.embed_tokens.weight.device
            ple.register_forward_pre_hook(
                lambda m, args: tuple(a.to("cpu") if torch.is_tensor(a) else a for a in args))
            ple.register_forward_hook(lambda m, args, out: out.to(_DEVICE))
    return _MODEL, _PROCESSOR


def gemma(prompt: str, wav: Path | None, thinking: bool, seed: int,
          max_new_tokens: int = 4096) -> dict:
    from transformers import set_seed
    model, processor = _load()
    content = [{"type": "text", "text": prompt}]
    if wav is not None:
        content.append({"type": "audio", "audio": str(wav)})
    inputs = processor.apply_chat_template(
        [{"role": "user", "content": content}], tokenize=True, return_dict=True,
        return_tensors="pt", add_generation_prompt=True,
        enable_thinking=thinking).to(_DEVICE)
    input_len = inputs["input_ids"].shape[-1]
    set_seed(seed)
    t0 = time.perf_counter()
    outputs = model.generate(**inputs, max_new_tokens=max_new_tokens)
    elapsed = time.perf_counter() - t0
    n_tok = outputs.shape[-1] - input_len
    response = processor.decode(outputs[0][input_len:], skip_special_tokens=False)
    parsed = processor.parse_response(response, prefix=inputs["input_ids"])
    return {"content": (parsed.get("content") or "").strip(),
            "thinking": parsed.get("thinking") or "",
            "n_tokens": int(n_tok), "hit_token_limit": n_tok >= max_new_tokens - 8,
            "elapsed_s": round(elapsed, 2)}


def _judge(template: str, input_prompt: str, output: str, seed: int):
    res = gemma(template.format(input_prompt=input_prompt, output=output), None,
                thinking=False, seed=seed, max_new_tokens=256)
    m = re.search(r"\{.*\}", res["content"], re.S)
    try:
        return json.loads(m.group(0))["answer"] if m else None
    except (json.JSONDecodeError, KeyError, TypeError):
        return None


def parse_ssr(output: str, answers: list[str], input_prompt: str, seed: int) -> tuple[int, str]:
    text = output.strip()
    m = re.match(r"^\W*(?:answer\W*)?(?:option\W*)?([12])\b", text, re.I)
    if m:
        return int(m.group(1)), "rule_leading_digit"
    digits = set(re.findall(r"(?<![\w.])([12])(?![\w])", text))
    if len(digits) == 1:
        return int(digits.pop()), "rule_single_digit"
    hits = [i + 1 for i, a in enumerate(answers) if a.strip().rstrip(".").lower() in text.lower()]
    if len(hits) == 1:
        return hits[0], "rule_answer_text"
    ans = _judge(JUDGE_SSR, input_prompt, output, seed)
    if ans in (1, 2, "1", "2"):
        return int(ans), "gemma_judge"
    return -1, "unparsed"


def _split_words(items) -> list[str]:
    words = []
    for it in items:
        words.extend(normalize_sentence(str(it)).split())
    return words


def parse_ssd(output: str, input_prompt: str, seed: int) -> tuple[list[str], str]:
    brackets = re.findall(r"\[([^\[\]]*)\]", output)
    if brackets:
        items = [x.strip().strip("'\"") for x in brackets[-1].split(",")]
        return _split_words(x for x in items if x), "rule_brackets"
    ans = _judge(JUDGE_SSD, input_prompt, output, seed)
    if isinstance(ans, list):
        return _split_words(ans), "gemma_judge"
    return [], "unparsed"


def load_samples() -> list[dict]:
    from datasets import Audio, load_dataset
    repo, prefix = DATASETS[DATASET]
    ds = load_dataset(repo, split="test").cast_column("audio", Audio(decode=False))
    samples = []
    for i, s in enumerate(ds):
        wav = AUDIO / f"{prefix}_{i:03d}.wav"
        if not wav.exists():
            raise SystemExit(f"{wav} missing: run export_stresstest.py --dataset {DATASET} first")
        samples.append({"idx": i, "id": f"{prefix}_{i:03d}", "wav": wav,
                        "transcription": s["transcription"],
                        "answers": list(s["possible_answers"]), "label": int(s["label"]),
                        "stress_binary": list(s["stress_pattern"]["binary"]),
                        "intonation": s["intonation"]})
    return samples


def run_one(task: str, thinking: bool, s: dict) -> dict:
    seed = s["idx"]
    if task == "ssr":
        prompt = PROMPT_SSR.format(answer_1=s["answers"][0], answer_2=s["answers"][1])
    elif task == "ssd":
        prompt = PROMPT_SSD.format(transcription=normalize_sentence(s["transcription"]))
    else:
        prompt = PROMPT_OPEN_SSR
    res = gemma(prompt, s["wav"], thinking, seed)
    row = {"id": s["id"], "intonation": s["intonation"], "input_prompt": prompt,
           "model_answer": res["content"], "thinking": res["thinking"],
           "n_tokens": res["n_tokens"], "hit_token_limit": res["hit_token_limit"],
           "elapsed_s": res["elapsed_s"]}
    if task == "ssr":
        pred, how = parse_ssr(res["content"], s["answers"], prompt, seed)
        row.update(pred=pred, label=s["label"] + 1, correct=pred == s["label"] + 1, parse_method=how)
    elif task == "ssd":
        words, how = parse_ssd(res["content"], prompt, seed)
        norm = set(words)
        row.update(pred_words=words,
                   stress_pred=[int(w in norm) for w in normalize_sentence(s["transcription"]).split()],
                   stress_labels=s["stress_binary"], parse_method=how)
    else:
        row.update(answers=s["answers"], label=s["label"] + 1)
    return row


def wilson(k: int, n: int, z: float = 1.96) -> list[float]:
    if n == 0:
        return [0.0, 0.0]
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return [round(c - h, 3), round(c + h, 3)]


def score() -> dict:
    summary = {"model": MODEL_ID, "dataset": DATASET, "paper": "arXiv 2505.22765",
               "paper_reference": {"ssr_accuracy": {"StresSLM": 0.862, "Gemini-2.5-Pro": 0.775,
                                                    "GPT-4o-audio": 0.688, "Qwen2Audio-7B": 0.532,
                                                    "human": 0.926},
                                   "ssd_f1": {"WhiStress": 0.883, "StresSLM": 0.869,
                                              "Gemini-2.5-Pro": 0.485, "GPT-4o-audio": 0.461,
                                              "Qwen2Audio-7B": 0.331}},
               "results": {}}
    for cond in CONDITIONS:
        for task in TASKS:
            path = OUT / f"raw_{cond}_{task}.jsonl"
            if not path.exists():
                continue
            rows = [json.loads(line) for line in open(path, encoding="utf-8")]
            if not rows:  # every sample so far failed (logged, retried on resume)
                continue
            r = {"n": len(rows),
                 "mean_elapsed_s": round(sum(x["elapsed_s"] for x in rows) / len(rows), 2),
                 "n_hit_token_limit": sum(x["hit_token_limit"] for x in rows)}
            if task != "open_ssr":
                methods: dict[str, int] = {}
                for x in rows:
                    methods[x["parse_method"]] = methods.get(x["parse_method"], 0) + 1
                r["parse_methods"] = methods
            if task == "ssr":
                k = sum(x["correct"] for x in rows)
                r.update(accuracy=round(k / len(rows), 3), ci95=wilson(k, len(rows)))
            elif task == "ssd":
                tp = fp = fn = 0
                bad = 0
                for x in rows:
                    p, l = x["stress_pred"], x["stress_labels"]
                    if len(p) != len(l):
                        bad += 1
                        continue
                    tp += sum(a and b for a, b in zip(p, l))
                    fp += sum(a and not b for a, b in zip(p, l))
                    fn += sum(b and not a for a, b in zip(p, l))
                prec = tp / (tp + fp) if tp + fp else 0.0
                rec = tp / (tp + fn) if tp + fn else 0.0
                f1 = 2 * prec * rec / (prec + rec) if prec + rec else 0.0
                r.update(precision=round(prec, 3), recall=round(rec, 3), f1=round(f1, 3),
                         n_length_mismatch=bad)
            else:
                r["note"] = "outputs saved; paper scores these 1-5 with a GPT-4o judge, not run here"
            summary["results"][f"{cond}/{task}"] = r
    return summary


def main() -> int:
    global MODEL_ID, OUT, PLE_CPU, DATASET, AUDIO, REPRO
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    ap.add_argument("--dataset", choices=sorted(DATASETS), default=DATASET)
    ap.add_argument("--model", default=MODEL_ID,
                    help="HF id of a Gemma-4 audio model (E2B/E4B take audio; 26B/31B do not)")
    ap.add_argument("--conditions", default="nothink,think")
    ap.add_argument("--tasks", default="ssr,ssd,open_ssr")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--score-only", action="store_true")
    ap.add_argument("--ple-cpu", action="store_true",
                    help="keep the per-layer embedding table in system RAM (E4B on a 16 GB card)")
    args = ap.parse_args()
    MODEL_ID = args.model
    PLE_CPU = args.ple_cpu
    DATASET = args.dataset
    AUDIO = HERE / "stress_search" / DATASET / "audio"
    REPRO = HERE / "stress_search" / f"{DATASET}_repro"
    OUT = REPRO / MODEL_ID.split("/")[-1]
    OUT.mkdir(parents=True, exist_ok=True)

    if not args.score_only:
        samples = load_samples()
        if args.limit:
            samples = samples[: args.limit]
        hw = hardware_info()
        print(f"host: {hw.get('host')}  gpu: {hw.get('gpu_name', 'none detected')}  "
              f"samples: {len(samples)}", flush=True)
        run_started = time.time()
        for cond in args.conditions.split(","):
            for task in args.tasks.split(","):
                path = OUT / f"raw_{cond}_{task}.jsonl"
                done = set()
                if path.exists():
                    done = {json.loads(line)["id"] for line in open(path, encoding="utf-8")}
                todo = [s for s in samples if s["id"] not in done]
                print(f"\n== {cond}/{task}: {len(done)} done, {len(todo)} to go", flush=True)
                with open(path, "a", encoding="utf-8") as fh:
                    for j, s in enumerate(todo, 1):
                        try:
                            row = run_one(task, CONDITIONS[cond], s)
                        except Exception as e:  # keep the overnight run alive; retried on resume
                            print(f"  {s['id']} FAILED: {type(e).__name__}: {e}", flush=True)
                            continue
                        fh.write(json.dumps(row, ensure_ascii=False) + "\n")
                        fh.flush()
                        tag = (f"pred={row['pred']} label={row['label']}" if task == "ssr"
                               else f"words={row['pred_words']}" if task == "ssd" else "")
                        print(f"  [{j}/{len(todo)}] {s['id']} {row['elapsed_s']}s {tag}", flush=True)
                (OUT / "summary.json").write_text(json.dumps(score(), indent=1), encoding="utf-8")
        (OUT / "run_manifest.json").write_text(json.dumps({
            **hw, "script": "reproduce_stresstest_gemma.py", "model": MODEL_ID, "dataset": DATASET, "ple_cpu": PLE_CPU,
            "conditions": args.conditions, "tasks": args.tasks, "limit": args.limit,
            "run_elapsed_s": round(time.time() - run_started, 1)}, indent=1), encoding="utf-8")

    summary = score()
    (OUT / "summary.json").write_text(json.dumps(summary, indent=1), encoding="utf-8")
    print(json.dumps(summary["results"], indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
