r"""
Transcribe corpus clips with any audio model served by llama.cpp, for the
same emphasis-marking question measure_llm_stress.py asks of Gemma-4.

Why this exists
---------------
Models that don't fit the transformers path on Shiro's 16 GB card (Nemotron
3 Nano Omni: 30B params, a mixture of experts) run under llama-server, which
keeps the rarely-used expert weights in system RAM. This script talks to that
server's OpenAI-style endpoint, so any audio model llama.cpp supports can be
measured the same way; nothing in it is Nemotron-specific except defaults.

Prompts, all applied to every clip (one CSV row per clip, one column group
per prompt), with thinking off:

    vendor_asr  the model vendor's documented transcription prompt
                (NVIDIA: "Transcribe this audio.")
    plain       measure_llm_stress.PLAIN_PROMPT, verbatim -- the prompt
                Gemma-4 got, so the two are directly comparable
    general     measure_llm_stress.GENERAL_PROMPT, verbatim -- invites
                *emphasis* / pause / overlap markup without naming stress

Settings follow the vendor's documentation, not Gemma's: for Nemotron, audio
BEFORE the text (NVIDIA's example; Google's card says the opposite for
Gemma), temperature 0.2 and top_k 1 (NVIDIA's non-thinking / ASR settings),
seeded per clip. Rows flush per clip and resume on rerun; a manifest JSON
records the server's model, flags and hardware.

Start the server first (see doc 09 section 11), then e.g.:

    python measure_llamacpp_stress.py --model-name nemotron-3-nano-omni-q4km
    python measure_llamacpp_stress.py --model-name ... --limit 5     # smoke test
    python measure_llamacpp_stress.py --model-name ... --conditions rep_,reps_only
"""

from __future__ import annotations

import argparse
import base64
import csv
import json
import sys
import time
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from measure_llm_stress import GENERAL_PROMPT, PLAIN_PROMPT  # noqa: E402
from verify_stress import hardware_info, local_path  # noqa: E402

VENDOR_ASR = {"nemotron": "Transcribe this audio."}
PROMPT_NAMES = ("vendor_asr", "plain", "general")


def chat(url: str, wav: Path, text: str, audio_first: bool, seed: int, max_tokens: int,
         temperature: float, top_k: int, thinking: bool) -> dict:
    audio = {"type": "input_audio",
             "input_audio": {"data": base64.b64encode(wav.read_bytes()).decode(), "format": "wav"}}
    prompt = {"type": "text", "text": text}
    body = {"messages": [{"role": "user", "content": [audio, prompt] if audio_first else [prompt, audio]}],
            "max_tokens": max_tokens, "temperature": temperature, "top_k": top_k, "seed": seed,
            "chat_template_kwargs": {"enable_thinking": thinking}}
    req = urllib.request.Request(url + "/v1/chat/completions", data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json"})
    t0 = time.time()
    r = json.load(urllib.request.urlopen(req, timeout=1800))
    msg = r["choices"][0]["message"]
    usage = r.get("usage", {})
    return {"content": (msg.get("content") or "").strip(), "reasoning": msg.get("reasoning_content") or "",
            "n_tokens": usage.get("completion_tokens"), "finish": r["choices"][0].get("finish_reason"),
            "elapsed_s": round(time.time() - t0, 2)}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--model-name", required=True, help="label for outputs, e.g. nemotron-3-nano-omni-q4km")
    ap.add_argument("--vendor", default="nemotron", choices=sorted(VENDOR_ASR))
    ap.add_argument("--url", default="http://127.0.0.1:8081")
    ap.add_argument("--manifest", default=str(HERE / "stress_search" / "clip_manifest.csv"))
    ap.add_argument("--conditions", default="rep_", help="comma-separated condition prefixes")
    ap.add_argument("--out", type=Path, default=None, help="default stress_search/llamacpp_<model-name>.csv")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--text-first", action="store_true", help="put the prompt before the audio")
    ap.add_argument("--temperature", type=float, default=0.2)
    ap.add_argument("--top-k", type=int, default=1)
    ap.add_argument("--max-tokens", type=int, default=2048)
    args = ap.parse_args()
    out = args.out or HERE / "stress_search" / f"llamacpp_{args.model_name}.csv"

    prompts = {"vendor_asr": VENDOR_ASR[args.vendor], "plain": PLAIN_PROMPT, "general": GENERAL_PROMPT}
    rows = [r for r in csv.DictReader(open(args.manifest, encoding="utf-8"))
            if r["condition"].startswith(tuple(args.conditions.split(",")))]
    if args.limit:
        rows = rows[:args.limit]
    done = set()
    if out.exists():
        done = {(r["video_id"], r["condition"]) for r in csv.DictReader(open(out, encoding="utf-8"))}
    todo = [r for r in rows if (r["video_id"], r["condition"]) not in done]

    server = json.load(urllib.request.urlopen(args.url + "/props", timeout=30))
    hw = hardware_info()
    out.with_name(out.stem + "_run_manifest.json").write_text(json.dumps({
        "hardware": hw, "model_name": args.model_name, "server_model": server.get("model_path"),
        "server_build": server.get("build_info"), "prompts": prompts, "audio_first": not args.text_first,
        "temperature": args.temperature, "top_k": args.top_k, "max_tokens": args.max_tokens, "thinking": False,
        "started": time.strftime("%Y-%m-%d %H:%M:%S")}, indent=2) + "\n", encoding="utf-8")
    print(f"host: {hw.get('host')}  model: {args.model_name}  {len(todo)} of {len(rows)} clips to do", flush=True)

    fields = ["video_id", "condition", "phrase", "bucket", "qa_pass"] + \
             [f"{p}_{k}" for p in PROMPT_NAMES for k in ("content", "n_tokens", "finish", "elapsed_s")]
    new_file = not out.exists()
    with out.open("a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        if new_file:
            w.writeheader()
        for i, r in enumerate(todo, 1):
            wav = local_path(r["path"])
            row = {k: r[k] for k in ("video_id", "condition", "phrase", "bucket", "qa_pass")}
            for name, text in prompts.items():
                res = chat(args.url, wav, text, not args.text_first, i, args.max_tokens,
                           args.temperature, args.top_k, thinking=False)
                row.update({f"{name}_content": res["content"], f"{name}_n_tokens": res["n_tokens"],
                            f"{name}_finish": res["finish"], f"{name}_elapsed_s": res["elapsed_s"]})
            w.writerow(row)
            f.flush()
            if i % 25 == 0 or i == len(todo) or i <= 3:
                print(f"  [{i}/{len(todo)}] {r['video_id']} {r['condition']}: {row['plain_content'][:70]!r}", flush=True)


if __name__ == "__main__":
    main()
