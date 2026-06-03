"""
Theme classification pipeline using human-identified categories.

Unlike llm_extract_comments.py (which asks LLMs to discover themes independently),
this script uses the four themes already identified by Natalie Rae's research team.
The goal is to see how consistently each local LLM can apply human-defined categories
to new public comments.

Runs in two phases for one GGUF model at a time:

  Phase 1 — Public comment identification
    Classifies commenter_candidate blocks as genuine public comments or not.
    Per-model output lets you compare whether different models agree on which
    blocks count as public comments.
    Output: downloads/llm_outputs/<model_name>/phase1_public_comments/<meeting>.json

  Phase 2 — Theme scoring  (requires Phase 1 output)
    Scores each identified public comment against the four human themes from
    data_center_comment_themes.md on a 0.0–1.0 scale per theme.
    Output: downloads/llm_outputs/<model_name>/phase2_theme_scores/<meeting>.json

Usage:
  python llm_classify_human_themes.py --list
  python llm_classify_human_themes.py --model qwen3.5-9b-q6
  python llm_classify_human_themes.py --model phi-4 --phase 2
"""

import argparse
import json
import re
import os
import time
from glob import glob
from llama_cpp import Llama
from pipeline_utils import fmt_elapsed, now_str

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
COMMENTS_DIR   = r"D:\Users\jad507\PycharmProjects\hands_on_dl\downloads\comments"
THEMES_MD_PATH = r"D:\Users\jad507\PycharmProjects\hands_on_dl\downloads\data_center_comment_themes.md"
OUTPUTS_ROOT   = r"D:\Users\jad507\PycharmProjects\hands_on_dl\downloads\llm_outputs"

# Phase 1: blocks per LLM call. At ~100 words/block summary, 3 blocks ≈ 300
# content tokens — leaves ample headroom for reason fields in large meetings.
P1_CHUNK_SIZE = 3

# Phase 2: truncate comment text to this many words before sending.
# Keeps total prompt well under 8 192 tokens even with the full themes .md.
P2_MAX_WORDS = 600

# ---------------------------------------------------------------------------
# Model registry
# RTX A2000 12 GB VRAM — every model should fit with n_gpu_layers=-1
# except where noted.
# ---------------------------------------------------------------------------
MODELS: dict[str, dict] = {
    # ── Qwen 3.5 9B (three quantisation levels for ablation) ─────────────
    # Weights + KV cache at 16384 ctx (float16): q4≈7.8 GB, q5≈8.7 GB, q6≈9.9 GB — all fit A2000 12 GB
    "qwen3.5-9b-q6": {
        "path":         r"D:\LLM\bartowski\Qwen_Qwen3.5-9B-Q6_K_L.gguf",
        "no_think":     True,   # prepend /no_think to system prompt
        "strip_think":  False,
        "n_ctx":        16384,
        "n_gpu_layers": -1,
    },
    "qwen3.5-9b-q5": {
        "path":         r"D:\LLM\bartowski\Qwen_Qwen3.5-9B-Q5_K_M.gguf",
        "no_think":     True,
        "strip_think":  False,
        "n_ctx":        16384,
        "n_gpu_layers": -1,
    },
    "qwen3.5-9b-q4": {
        "path":         r"D:\LLM\bartowski\Qwen_Qwen3.5-9B-Q4_K_M.gguf",
        "no_think":     True,
        "strip_think":  False,
        "n_ctx":        16384,
        "n_gpu_layers": -1,
    },
    # Weights 8.9 GB + KV ~2.3 GB ≈ 11.2 GB — tight on A2000 12 GB; watch for OOM
    "qwen3.5-9b-q8": {
        "path":         r"D:\LLM\daniloreddy\Qwen3.5-9B_Q8_0.gguf",
        "no_think":     True,
        "strip_think":  False,
        "n_ctx":        16384,
        "n_gpu_layers": -1,
    },
    # ── DeepSeek R1 Qwen distills (thinking models — strip <think> tags) ──
    "deepseek-r1-7b": {
        "path":         r"D:\LLM\bartowski\DeepSeek-R1-Distill-Qwen-7B-Q6_K_L.gguf",
        "no_think":     False,
        "strip_think":  True,   # remove <think>…</think> before JSON parse
        "n_ctx":        16384,
        "n_gpu_layers": -1,
    },
    # Weights 8.4 GB + KV ~3.2 GB ≈ 11.6 GB — risky on A2000 12 GB; may OOM
    "deepseek-r1-14b": {
        "path":         r"D:\LLM\bartowski\DeepSeek-R1-Distill-Qwen-14B-Q4_K_M.gguf",
        "no_think":     False,
        "strip_think":  True,
        "n_ctx":        16384,
        "n_gpu_layers": -1,
    },
    # Weights 8.3 GB + KV ~2.7 GB ≈ 11.0 GB — tight on A2000 12 GB; watch for OOM
    "phi-4": {
        "path":         r"D:\LLM\unsloth\phi-4-Q4_K_M.gguf",
        "no_think":     False,
        "strip_think":  False,
        "n_ctx":        16384,
        "n_gpu_layers": -1,
    },
    # ── Gemma 4 4B effective (MoE) ────────────────────────────────────────
    # Weights 8.2 GB + small KV (low active-layer count) ≈ 9.7 GB — fits A2000 12 GB
    "gemma-4-4b": {
        "path":         r"D:\LLM\unsloth\gemma-4-E4B-it-UD-Q8_K_XL.gguf",
        "no_think":     False,
        "strip_think":  False,
        "n_ctx":        16384,
        "n_gpu_layers": -1,
    },
    # ── Llama 4 Scout — NOT RUNNABLE on A2000 12 GB ───────────────────────
    # "17B-16E" refers to 17B *active* parameters per token (MoE); total weights are
    # ~109B, quantised to ~59 GB across two GGUF files. Run on the remote 80 GB card.
    # llama_cpp auto-loads part 2 when given the path to part 1.
    "llama-4-scout": {
        "backend":      "llama_cpp",
        "path":         r"D:\LLM\unsloth\Llama-4-Scout-17B-16E-Instruct-UD-Q4_K_XL-00001-of-00002.gguf",
        "no_think":     False,
        "strip_think":  False,
        "n_ctx":        16384,
        "n_gpu_layers": -1,
    },
    # ── Ministral 8B GGUF (mistralai/Ministral-3-8B-Instruct-2512, Q8_0) ──
    # Weights 8.5 GB + KV ~2.2 GB ≈ 10.7 GB — fits A2000 12 GB
    "ministral-8b": {
        "backend":      "llama_cpp",
        "path":         r"D:\LLM\Ministral\Ministral-3-8B-Instruct-2512-Q8_0.gguf",
        "no_think":     False,
        "strip_think":  False,
        "n_ctx":        16384,
        "n_gpu_layers": -1,
    },
    # ── Ministral 8B native (mistralai/Ministral-3-8B-Instruct-2512, safetensors) ──
    # consolidated.safetensors ~9.8 GB. Requires HuggingFace transformers.
    "ministral-8b-hf": {
        "backend":      "transformers",
        "path":         r"D:\LLM\Ministral\consolidated.safetensors",
        "no_think":     False,
        "strip_think":  False,
        "n_ctx":        16384,
        "n_gpu_layers": -1,
    },
    # ── Gemma 4 31B — NOT RUNNABLE on A2000 12 GB ─────────────────────────
    # google/gemma-4-31B-it, bfloat16 safetensors (~59 GB). Run on the remote 80 GB card.
    # Requires HuggingFace transformers — NOT compatible with this script's llama_cpp
    # backend. Path points to the model directory, not a single file.
    "gemma-4-31b": {
        "backend":      "transformers",
        "path":         r"D:\LLM\google",
        "no_think":     False,
        "strip_think":  False,
        "n_ctx":        16384,
        "n_gpu_layers": -1,
    },
    # ── Llama 3.1 8B NVFP4 (nvidia/Llama-3.1-8B-Instruct-NVFP4) ──────────
    # NVIDIA's proprietary FP4 quantisation (~5.7 GB). Requires TensorRT-LLM or
    # vLLM with NVFP4 support — NOT loadable by llama_cpp. Path points to the
    # model directory, not a single file.
    "llama-3.1-nvfp4": {
        "backend":      "transformers",
        "path":         r"D:\LLM\nvidia",
        "no_think":     False,
        "strip_think":  False,
        "n_ctx":        16384,
        "n_gpu_layers": -1,
    },
}

# ---------------------------------------------------------------------------
# System prompts
# ---------------------------------------------------------------------------
P1_SYSTEM = """\
You are analyzing transcripts of Lancaster, PA city council meetings.

Each meeting has a public comment period where community members address the council.
You will receive ALL speech blocks from the meeting, each tagged with a diarization category:
  - "recurring"           — speaker appeared frequently in this meeting
  - "commenter_candidate" — speaker appeared rarely in this meeting

IMPORTANT: these categories are unreliable signals and must not be used as a hard filter.
Civically active residents often speak in multiple meetings and multiple times per meeting,
causing them to be classified as "recurring" even though they are genuine public commenters.
Diarization also sometimes captures a few words of an adjacent speaker (e.g. a council member
calling the next commenter) at the start or end of a block, which can distort category
assignment. Use the category as a weak hint only — rely primarily on the text content.

A block is NOT a public comment if the speaker is:
  - A council member, mayor, city clerk, or staff member conducting official business
  - Reading a vote roll call or meeting minutes
  - A presenter, expert witness, or attorney speaking at the council's invitation
  - Making a brief procedural statement (seconds, quorum calls, etc.)

A block IS a genuine public comment if the speaker:
  - Identifies themselves as a resident, community member, business owner, or local stakeholder
  - Expresses an opinion, concern, question, or position on a city decision
  - Is speaking during the public comment period (not during council discussion or a vote)

Respond only with valid JSON and no other text.\
"""

P2_SYSTEM_TEMPLATE = """\
You are scoring public comments from Lancaster, PA city council meetings against
four themes identified by human researchers through qualitative analysis.

Score each comment on all four themes from 0.0 (not relevant) to 1.0 (directly on-theme).
Comments may score highly on multiple themes. Be calibrated — most comments will score
0.0 or near 0.0 on most themes. Do not inflate scores.

Analytical stance: do not judge whether the speaker's claims are factually accurate.
Treat each comment as a situated narrative — score how strongly it engages with each
theme regardless of factual accuracy.

--- HUMAN-IDENTIFIED THEME DEFINITIONS ---
{themes_content}
--- END THEME DEFINITIONS ---

Respond only with valid JSON matching this exact structure (no extra keys):
{{
  "themes": {{
    "municipally_managed_resources": {{"score": <float 0.0-1.0>, "reasoning": "<1-2 sentences>"}},
    "municipal_process":             {{"score": <float 0.0-1.0>, "reasoning": "<1-2 sentences>"}},
    "health_and_well_being":         {{"score": <float 0.0-1.0>, "reasoning": "<1-2 sentences>"}},
    "power_dynamics_and_inequality": {{"score": <float 0.0-1.0>, "reasoning": "<1-2 sentences>"}}
  }}
}}\
"""

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def load_json(path: str) -> dict | None:
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"  Could not load {os.path.basename(path)}: {e}")
        return None


def get_blocks(data: dict) -> list[dict]:
    return data.get("blocks") or data.get("commenter_blocks") or []


def build_system(base: str, no_think: bool) -> str:
    return f"/no_think\n{base}" if no_think else base


def strip_think_tags(text: str) -> str:
    return re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()


def call_llm(llm: Llama, system: str, user: str, max_tokens: int,
             strip_think: bool) -> str | None:
    response = llm.create_chat_completion(
        messages=[
            {"role": "system", "content": system},
            {"role": "user",   "content": user},
        ],
        temperature=0.0,
        max_tokens=max_tokens,
        response_format={"type": "json_object"},
    )
    raw = response["choices"][0]["message"]["content"].strip()
    if strip_think:
        raw = strip_think_tags(raw)
    return raw


def parse_json_safe(raw: str, context: str) -> dict | None:
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        print(f"  JSON parse error ({context}): {raw[:120]}")
        return None


def truncate_words(text: str, max_words: int) -> str:
    words = text.split()
    if len(words) <= max_words:
        return text
    return " ".join(words[:max_words]) + " [truncated]"


# ---------------------------------------------------------------------------
# Phase 1
# ---------------------------------------------------------------------------

def format_p1_block(b: dict) -> str:
    mins     = int(b["start"] // 60)
    secs     = int(b["start"] % 60)
    category = b.get("category", "unknown")
    preview  = truncate_words(b.get("text", ""), 80)
    return f'Block {b["block_id"]} ({mins:02d}:{secs:02d}, {category}): "{preview}"'


def _p1_user_msg(blocks: list[dict], meeting_title: str) -> str:
    return (
        f"Meeting: {meeting_title}\n\n"
        "Speech blocks:\n"
        + "\n".join(format_p1_block(b) for b in blocks)
        + "\n\n"
        "List ONLY the blocks above that are genuine public comments from community members.\n"
        "Do not include blocks that are not public comments. Do not explain why non-comment blocks were omitted.\n"
        "\n"
        "Your response must be a JSON object with exactly this structure:\n"
        '{"public_comments": [{"block_id": <int>, "speaker_name": "<full name if stated, else unknown>", "reason": "<one sentence>"}]}\n'
        'If none are public comments, return: {"public_comments": []}'
    )


def _p1_retry_user_msg(block: dict, meeting_title: str) -> str:
    return (
        f"Meeting: {meeting_title}\n"
        f"{format_p1_block(block)}\n\n"
        "Is the block above a genuine public comment from a community member?\n"
        "\n"
        'If YES, respond with: {"public_comments": [{"block_id": '
        f'{block["block_id"]}'
        ', "speaker_name": "<name or unknown>", "reason": "<one sentence>"}]}\n'
        'If NO, respond with: {"public_comments": []}'
    )


def classify_p1_chunk(llm: Llama, blocks: list[dict], meeting_title: str,
                      system: str, strip_think: bool) -> tuple[list[dict], int]:
    raw = call_llm(llm, system, _p1_user_msg(blocks, meeting_title),
                   max_tokens=1500, strip_think=strip_think)
    if raw is None:
        return [], 1
    parsed = parse_json_safe(raw, f"P1 chunk from {meeting_title}")
    if parsed is not None and "public_comments" in parsed:
        return parsed["public_comments"], 0

    if parsed is not None:
        print(f"  P1 wrong schema from {meeting_title}: {list(parsed)[:5]} — retrying {len(blocks)} block(s) individually")
    else:
        print(f"  P1 JSON parse error from {meeting_title} — retrying {len(blocks)} block(s) individually")

    # Retry each block one at a time with a simpler prompt
    recovered: list[dict] = []
    n_still_failed = 0
    for block in blocks:
        retry_raw = call_llm(llm, system, _p1_retry_user_msg(block, meeting_title),
                             max_tokens=200, strip_think=strip_think)
        if retry_raw is None:
            n_still_failed += 1
            continue
        retry_parsed = parse_json_safe(retry_raw, f"P1 retry block {block['block_id']} from {meeting_title}")
        if retry_parsed is None or "public_comments" not in retry_parsed:
            n_still_failed += 1
        else:
            recovered.extend(retry_parsed["public_comments"])

    return recovered, (1 if n_still_failed > 0 else 0)


def run_phase1(llm: Llama, model_cfg: dict, model_name: str, out_dir: str) -> None:
    system        = build_system(P1_SYSTEM, model_cfg["no_think"])
    meeting_files = sorted(glob(os.path.join(COMMENTS_DIR, "*.json")))
    total_start   = time.perf_counter()
    n_done = n_skipped = n_errors = 0

    print(f"\n[{now_str()}] Phase 1 starting: {len(meeting_files)} meeting files")

    for path in meeting_files:
        out_path = os.path.join(out_dir, os.path.basename(path))
        if os.path.exists(out_path):
            existing = load_json(out_path)
            if existing and existing.get("n_chunk_errors", 0) == 0:
                print(f"  SKIP (already done): {os.path.basename(path)}")
                n_skipped += 1
                continue
            prior_errors = existing.get("n_chunk_errors", "?") if existing else "?"
            print(f"  REDO ({prior_errors} prior chunk errors): {os.path.basename(path)}")

        data = load_json(path)
        if data is None:
            n_errors += 1
            continue

        all_blocks = get_blocks(data)

        # NOTE for future maintainers: do NOT pre-filter to commenter_candidate blocks here.
        # The recurring/commenter_candidate classification is unreliable for this task:
        #   - Civically active residents speak in multiple meetings and multiple times per
        #     meeting, which causes the diarization pipeline to label them "recurring" even
        #     though they are genuine public commenters.
        #   - Diarization sometimes bleeds a few words of an adjacent speaker (e.g. a council
        #     member calling the next person to the mic) into a block, further distorting the
        #     category.  The category is passed to the LLM as a soft hint only.
        if not all_blocks:
            print(f"  SKIP (no blocks): {os.path.basename(path)}")
            n_skipped += 1
            continue

        title       = data.get("title", os.path.basename(path))
        block_by_id = {b["block_id"]: b for b in all_blocks}

        print(f"\n[{now_str()}] {title}")
        t0 = time.perf_counter()

        identified: list[dict] = []
        n_chunk_errors = 0
        chunks = [all_blocks[i:i + P1_CHUNK_SIZE]
                  for i in range(0, len(all_blocks), P1_CHUNK_SIZE)]
        for chunk in chunks:
            results, err = classify_p1_chunk(llm, chunk, title, system, model_cfg["strip_think"])
            identified.extend(results)
            n_chunk_errors += err

        public_comments = []
        for item in identified:
            bid = item.get("block_id")
            if bid not in block_by_id or not item.get("is_public_comment", True):
                continue
            b = block_by_id[bid]
            public_comments.append({
                "block_id":     bid,
                "speaker":      b["speaker"],
                "start":        b["start"],
                "end":          b["end"],
                "speaker_name": item.get("speaker_name", "unknown"),
                "reason":       item.get("reason", ""),
                "text":         b["text"],
            })

        result = {
            "title":           data.get("title"),
            "video_id":        data.get("video_id"),
            "upload_date":     data.get("upload_date"),
            "model":           model_name,
            "n_chunk_errors":  n_chunk_errors,
            "public_comments": public_comments,
        }
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)

        error_note = f"  {n_chunk_errors} chunk errors" if n_chunk_errors else ""
        print(f"  {len(public_comments)} public comments from {len(all_blocks)} blocks"
              f"{error_note}  [Elapsed: {fmt_elapsed(time.perf_counter() - t0)}]")
        n_done += 1

    print(f"\nSummary: {n_done} processed, {n_skipped} skipped, {n_errors} errors")
    print(f"Total time: {fmt_elapsed(time.perf_counter() - total_start)}")


# ---------------------------------------------------------------------------
# Phase 2
# ---------------------------------------------------------------------------

def load_themes_md() -> str:
    with open(THEMES_MD_PATH, encoding="utf-8") as f:
        return f.read()


def score_comment_themes(llm: Llama, comment_text: str, meeting_title: str,
                         block_id: int, system: str, strip_think: bool) -> dict | None:
    context = f"P2 block {block_id} from {meeting_title}"

    def _call(text: str) -> dict | None:
        user_msg = (
            f"Meeting: {meeting_title}\n"
            f"Block ID: {block_id}\n\n"
            f"Public comment text:\n\"{text}\"\n\n"
            "Score this comment against all four themes."
        )
        raw = call_llm(llm, system, user_msg, max_tokens=700, strip_think=strip_think)
        if raw is None:
            return None
        return parse_json_safe(raw, context)

    result = _call(comment_text)
    if result is None and len(comment_text.split()) > P2_MAX_WORDS:
        print(f"  P2 block {block_id}: retrying with {P2_MAX_WORDS}-word truncation")
        result = _call(truncate_words(comment_text, P2_MAX_WORDS))
    return result


def run_phase2(llm: Llama, model_cfg: dict, model_name: str,
               p1_dir: str, out_dir: str) -> None:
    themes_content = load_themes_md()
    system = build_system(
        P2_SYSTEM_TEMPLATE.format(themes_content=themes_content),
        model_cfg["no_think"],
    )

    p1_files    = sorted(glob(os.path.join(p1_dir, "*.json")))
    total_start = time.perf_counter()
    n_done = n_skipped = n_errors = 0

    if not p1_files:
        print(f"  No Phase 1 output found in {p1_dir} — run Phase 1 first.")
        return

    print(f"\n[{now_str()}] Phase 2 starting: {len(p1_files)} meetings with Phase 1 output")

    for path in p1_files:
        out_path = os.path.join(out_dir, os.path.basename(path))
        if os.path.exists(out_path):
            existing = load_json(out_path)
            if existing and existing.get("n_failed_comments", 0) == 0:
                print(f"  SKIP (already done): {os.path.basename(path)}")
                n_skipped += 1
                continue
            prior_failed = existing.get("n_failed_comments", "?") if existing else "?"
            print(f"  REDO ({prior_failed} prior failed comments): {os.path.basename(path)}")

        data = load_json(path)
        if data is None:
            n_errors += 1
            continue

        comments = data.get("public_comments", [])
        if not comments:
            print(f"  SKIP (no public comments): {os.path.basename(path)}")
            n_skipped += 1
            continue

        title        = data.get("title", os.path.basename(path))
        theme_scores = []

        print(f"\n[{now_str()}] {title}")
        t0 = time.perf_counter()

        for comment in comments:
            scores = score_comment_themes(
                llm,
                comment.get("text", ""),
                title,
                comment["block_id"],
                system,
                model_cfg["strip_think"],
            )
            theme_scores.append({
                "block_id":     comment["block_id"],
                "speaker":      comment.get("speaker"),
                "speaker_name": comment.get("speaker_name", "unknown"),
                "start":        comment.get("start"),
                "end":          comment.get("end"),
                "text":         comment.get("text", ""),
                "themes":       scores.get("themes") if scores else None,
            })

        n_scored = sum(1 for e in theme_scores if e["themes"] is not None)
        n_failed = len(theme_scores) - n_scored

        result = {
            "title":              data.get("title"),
            "video_id":           data.get("video_id"),
            "upload_date":        data.get("upload_date"),
            "model":              model_name,
            "n_failed_comments":  n_failed,
            "theme_scores":       theme_scores,
        }
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)

        fail_note = f"  {n_failed} failed" if n_failed else ""
        print(f"  {n_scored}/{len(comments)} comments scored"
              f"{fail_note}  [Elapsed: {fmt_elapsed(time.perf_counter() - t0)}]")
        n_done += 1

    print(f"\nSummary: {n_done} processed, {n_skipped} skipped, {n_errors} errors")
    print(f"Total time: {fmt_elapsed(time.perf_counter() - total_start)}")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Classify Lancaster council comments against human-identified themes."
    )
    parser.add_argument("--model", help="Model key from the registry (see --list)")
    parser.add_argument("--list",  action="store_true", help="Print available models and exit")
    parser.add_argument("--phase", choices=["1", "2", "both"], default="both",
                        help="Which phase to run (default: both)")
    args = parser.parse_args()

    if args.list:
        print("Available models:")
        for name, cfg in MODELS.items():
            exists  = "ok" if os.path.exists(cfg["path"]) else "NOT FOUND"
            backend = cfg.get("backend", "llama_cpp")
            flag    = "" if backend == "llama_cpp" else f"  [{backend} — not runnable here]"
            print(f"  {name:<22} {exists}  {os.path.basename(cfg['path'])}{flag}")
        return

    if not args.model:
        parser.error("--model is required unless --list is used")

    if args.model not in MODELS:
        print(f"Unknown model '{args.model}'. Run with --list to see options.")
        return

    model_cfg  = MODELS[args.model]
    model_name = args.model

    backend = model_cfg.get("backend", "llama_cpp")
    if backend != "llama_cpp":
        print(f"'{model_name}' uses backend '{backend}' and cannot be loaded by this script.")
        if model_name == "gemma-4-31b":
            print("  Load with: transformers.AutoModelForCausalLM (bfloat16 safetensors)")
        elif model_name == "llama-3.1-nvfp4":
            print("  Load with: TensorRT-LLM or vLLM with NVFP4 support")
        return

    if not os.path.exists(model_cfg["path"]):
        print(f"Model file not found: {model_cfg['path']}")
        return

    p1_dir = os.path.join(OUTPUTS_ROOT, model_name, "phase1_public_comments")
    p2_dir = os.path.join(OUTPUTS_ROOT, model_name, "phase2_theme_scores")
    os.makedirs(p1_dir, exist_ok=True)
    os.makedirs(p2_dir, exist_ok=True)

    print(f"[{now_str()}] Loading model: {model_cfg['path']}")
    t0  = time.perf_counter()
    llm = Llama(
        model_path=model_cfg["path"],
        n_ctx=model_cfg["n_ctx"],
        n_gpu_layers=model_cfg["n_gpu_layers"],
        verbose=True,
    )
    print(f"  Loaded in {fmt_elapsed(time.perf_counter() - t0)}")

    if args.phase in ("1", "both"):
        run_phase1(llm, model_cfg, model_name, p1_dir)

    if args.phase in ("2", "both"):
        run_phase2(llm, model_cfg, model_name, p1_dir, p2_dir)

    print("\nDone.")


if __name__ == "__main__":
    main()
