r"""
The StressTest reproduction (reproduce_stresstest_gemma.py) for a model served
by llama.cpp's llama-server instead of loaded through transformers.

Everything that defines the protocol -- the paper's three prompts, answer
parsing (rules first, then the model itself as text-only judge), scoring,
output layout -- is reproduce_stresstest_gemma.py's, imported and used
unchanged. Only the generation call is swapped for a request to the
server's OpenAI-style endpoint, with the model vendor's documented settings
instead of Gemma's.

Nemotron 3 Nano Omni (NVIDIA model card, "Best Practices" and "Audio
Example"):
    audio before the text (also the paper's "[audio] prompt" template)
    thinking off: temperature 0.2, top_k 1
    thinking on:  temperature 0.6, top_p 0.95, max 20480 output tokens
                  (NVIDIA's max_token; its vLLM-only reasoning_budget /
                  grace_period controls have no llama-server equivalent)

The server needs a context window above prompt + 20480 tokens for the
thinking condition (doc 09 section 11 has the command). Outputs go to
stress_search/stresstest_repro/<model-name>/, resumable, same files as the
Gemma runs, so score() and the summary are directly comparable.

Usage
-----
    python reproduce_stresstest_server.py --model nemotron-3-nano-omni-q4km --conditions nothink
    python reproduce_stresstest_server.py --model nemotron-3-nano-omni-q4km --limit 3
"""

from __future__ import annotations

import base64
import json
import sys
import time
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import reproduce_stresstest_gemma as R  # noqa: E402

URL = "http://127.0.0.1:8081"
SETTINGS = {
    False: {"temperature": 0.2, "top_k": 1, "max_tokens": 4096},
    True: {"temperature": 0.6, "top_p": 0.95, "max_tokens": 20480},
}


def server_generate(prompt: str, wav: Path | None, thinking: bool, seed: int,
                    max_new_tokens: int | None = None) -> dict:
    """Drop-in for R.gemma(): same arguments, same returned fields."""
    s = dict(SETTINGS[thinking])
    if max_new_tokens is not None:  # the text-only judge asks for 256
        s["max_tokens"] = max_new_tokens
    content = [{"type": "text", "text": prompt}]
    if wav is not None:
        content.insert(0, {"type": "input_audio", "input_audio": {
            "data": base64.b64encode(Path(wav).read_bytes()).decode(), "format": "wav"}})
    body = {"messages": [{"role": "user", "content": content}], "seed": seed,
            "chat_template_kwargs": {"enable_thinking": thinking}, **s}
    req = urllib.request.Request(URL + "/v1/chat/completions", data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json"})
    t0 = time.perf_counter()
    r = json.load(urllib.request.urlopen(req, timeout=3600))
    choice = r["choices"][0]
    return {"content": (choice["message"].get("content") or "").strip(),
            "thinking": choice["message"].get("reasoning_content") or "",
            "n_tokens": int(r.get("usage", {}).get("completion_tokens") or 0),
            "hit_token_limit": choice.get("finish_reason") == "length",
            "elapsed_s": round(time.perf_counter() - t0, 2)}


if __name__ == "__main__":
    R.gemma = server_generate  # run_one() and the judge both call R.gemma
    props = json.load(urllib.request.urlopen(URL + "/props", timeout=30))
    print(f"server: {props.get('model_path')}  build {props.get('build_info')}", flush=True)
    code = R.main()
    (R.OUT / "server_settings.json").write_text(json.dumps({
        "server_model": props.get("model_path"), "server_build": props.get("build_info"),
        "n_ctx": props.get("default_generation_settings", {}).get("n_ctx"),
        "audio_first": True, "settings": {"nothink": SETTINGS[False], "think": SETTINGS[True]}},
        indent=1), encoding="utf-8")
    sys.exit(code)
