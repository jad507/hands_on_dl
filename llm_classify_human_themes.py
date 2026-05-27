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
from glob import glob
from tqdm import tqdm
from llama_cpp import Llama

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
COMMENTS_DIR   = r"D:\Users\jad507\PycharmProjects\hands_on_dl\downloads\comments"
THEMES_MD_PATH = r"D:\Users\jad507\PycharmProjects\hands_on_dl\downloads\data_center_comment_themes.md"
OUTPUTS_ROOT   = r"D:\Users\jad507\PycharmProjects\hands_on_dl\downloads\llm_outputs"

# Phase 1: blocks per LLM call. At ~100 words/block summary, 15 blocks ≈ 1 500
# content tokens — comfortable for 8 192 ctx.
P1_CHUNK_SIZE = 15

# Phase 2: truncate comment text to this many words before sending.
# Keeps total prompt well under 8 192 tokens even with the full themes .md.
P2_MAX_WORDS = 600

# ---------------------------------------------------------------------------
# Model registry
# RTX A2000 12 GB VRAM — every model should fit with n_gpu_layers=-1
# except where noted.
# ---------------------------------------------------------------------------
MODELS: dict[str, dict] = {
    # ── Qwen 3.5 9B (three quantisation levels for ablation) ──────────────
    "qwen3.5-9b-q6": {
        "path":         r"D:\LLM\bartowski\Qwen_Qwen3.5-9B-Q6_K_L.gguf",
        "no_think":     True,   # prepend /no_think to system prompt
        "strip_think":  False,
        "n_ctx":        8192,
        "n_gpu_layers": -1,
    },
    "qwen3.5-9b-q5": {
        "path":         r"D:\LLM\bartowski\Qwen_Qwen3.5-9B-Q5_K_M.gguf",
        "no_think":     True,
        "strip_think":  False,
        "n_ctx":        8192,
        "n_gpu_layers": -1,
    },
    "qwen3.5-9b-q4": {
        "path":         r"D:\LLM\bartowski\Qwen_Qwen3.5-9B-Q4_K_M.gguf",
        "no_think":     True,
        "strip_think":  False,
        "n_ctx":        8192,
        "n_gpu_layers": -1,
    },
    "qwen3.5-9b-q8": {
        "path":         r"D:\LLM\daniloreddy\Qwen3.5-9B_Q8_0.gguf",
        "no_think":     True,
        "strip_think":  False,
        "n_ctx":        8192,
        "n_gpu_layers": -1,
    },
    # ── DeepSeek R1 Qwen distills (thinking models — strip <think> tags) ──
    "deepseek-r1-7b": {
        "path":         r"D:\LLM\bartowski\DeepSeek-R1-Distill-Qwen-7B-Q6_K_L.gguf",
        "no_think":     False,
        "strip_think":  True,   # remove <think>…</think> before JSON parse
        "n_ctx":        8192,
        "n_gpu_layers": -1,
    },
    "deepseek-r1-14b": {
        "path":         r"D:\LLM\bartowski\DeepSeek-R1-Distill-Qwen-14B-Q4_K_M.gguf",
        "no_think":     False,
        "strip_think":  True,
        "n_ctx":        8192,
        "n_gpu_layers": -1,    # ~9 GB — fits A2000 12 GB but leaves little headroom
    },
    # ── Phi-4 14B ─────────────────────────────────────────────────────────
    "phi-4": {
        "path":         r"D:\LLM\unsloth\phi-4-Q4_K_M.gguf",
        "no_think":     False,
        "strip_think":  False,
        "n_ctx":        8192,
        "n_gpu_layers": -1,    # ~8.5 GB — fits A2000 12 GB
    },
    # ── Gemma 4 4B effective (MoE) ────────────────────────────────────────
    "gemma-4-4b": {
        "path":         r"D:\LLM\unsloth\gemma-4-E4B-it-UD-Q8_K_XL.gguf",
        "no_think":     False,
        "strip_think":  False,
        "n_ctx":        8192,
        "n_gpu_layers": -1,
    },
    # ── Llama 4 Scout 17B-16E (split GGUF — llama_cpp auto-loads part 2) ─
    "llama-4-scout": {
        "path":         r"D:\LLM\unsloth\Llama-4-Scout-17B-16E-Instruct-UD-Q4_K_XL-00001-of-00002.gguf",
        "no_think":     False,
        "strip_think":  False,
        "n_ctx":        8192,
        "n_gpu_layers": -1,    # MoE: active params ~5B, full weights ~10 GB
    },
    # ── Ministral 8B ──────────────────────────────────────────────────────
    "ministral-8b": {
        "path":         r"D:\LLM\Ministral\Ministral-3-8B-Instruct-2512-Q8_0.gguf",
        "no_think":     False,
        "strip_think":  False,
        "n_ctx":        8192,
        "n_gpu_layers": -1,    # ~8.5 GB — fits A2000 12 GB
    },
}

# ---------------------------------------------------------------------------
# System prompts
# ---------------------------------------------------------------------------
P1_SYSTEM = """\
You are analyzing transcripts of Lancaster, PA city council meetings.

Each meeting has a public comment period where community members address the council.
The blocks you will see have already been pre-filtered to "commenter_candidate" speakers —
speakers who appeared rarely in this meeting and are therefore likely one-time commenters.
However, not every commenter_candidate is a genuine public commenter. A block is NOT a
public comment if the speaker is:
  - Reading a vote roll call or meeting minutes
  - A one-time presenter, expert witness, or attorney invited by the council
  - A staff member making a brief procedural statement

A block IS a genuine public comment if the speaker:
  - Identifies themselves as a resident, community member, business owner, or local stakeholder
  - Expresses an opinion, concern, question, or position on a city decision
  - Is speaking during the public comment period (not during a council discussion or vote)

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
        tqdm.write(f"  Could not load {os.path.basename(path)}: {e}")
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
        tqdm.write(f"  JSON parse error ({context}): {raw[:120]}")
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
    mins    = int(b["start"] // 60)
    secs    = int(b["start"] % 60)
    preview = truncate_words(b.get("text", ""), 80)
    return f'[Block {b["block_id"]} | {mins:02d}:{secs:02d}]: "{preview}"'


def classify_p1_chunk(llm: Llama, blocks: list[dict], meeting_title: str,
                      system: str, strip_think: bool) -> list[dict]:
    user_msg = (
        f"Meeting: {meeting_title}\n\n"
        "The following blocks are from speakers classified as commenter_candidates "
        "(appeared only rarely in this meeting):\n\n"
        + "\n".join(format_p1_block(b) for b in blocks)
        + "\n\nIdentify which blocks (if any) are genuine public comments from community members.\n"
        'Return JSON: {"public_comments": [{"block_id": <int>, '
        '"speaker_name": "<full name if stated, else unknown>", '
        '"is_public_comment": true, '
        '"reason": "<one sentence why>"}]}\n'
        'If none are public comments, return: {"public_comments": []}'
    )
    raw = call_llm(llm, system, user_msg, max_tokens=600, strip_think=strip_think)
    if raw is None:
        return []
    parsed = parse_json_safe(raw, f"P1 chunk from {meeting_title}")
    if parsed is None:
        return []
    return parsed.get("public_comments", [])


def run_phase1(llm: Llama, model_cfg: dict, model_name: str, out_dir: str) -> None:
    system        = build_system(P1_SYSTEM, model_cfg["no_think"])
    meeting_files = sorted(glob(os.path.join(COMMENTS_DIR, "*.json")))
    print(f"\nPhase 1: {len(meeting_files)} meeting files\n")

    for path in tqdm(meeting_files, desc="Phase 1"):
        out_path = os.path.join(out_dir, os.path.basename(path))
        if os.path.exists(out_path):
            tqdm.write(f"  SKIP (already done): {os.path.basename(path)}")
            continue

        data = load_json(path)
        if data is None:
            continue

        all_blocks       = get_blocks(data)
        candidate_blocks = [b for b in all_blocks if b.get("category") == "commenter_candidate"]

        if not candidate_blocks:
            tqdm.write(f"  SKIP (no candidates): {os.path.basename(path)}")
            continue

        title       = data.get("title", os.path.basename(path))
        block_by_id = {b["block_id"]: b for b in candidate_blocks}

        identified: list[dict] = []
        chunks = [candidate_blocks[i:i + P1_CHUNK_SIZE]
                  for i in range(0, len(candidate_blocks), P1_CHUNK_SIZE)]
        for chunk in chunks:
            identified.extend(
                classify_p1_chunk(llm, chunk, title, system, model_cfg["strip_think"])
            )

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
            "public_comments": public_comments,
        }
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)

        tqdm.write(f"  {title}: {len(public_comments)} public comments "
                   f"(from {len(candidate_blocks)} candidates)")


# ---------------------------------------------------------------------------
# Phase 2
# ---------------------------------------------------------------------------

def load_themes_md() -> str:
    with open(THEMES_MD_PATH, encoding="utf-8") as f:
        return f.read()


def score_comment_themes(llm: Llama, comment_text: str, meeting_title: str,
                         block_id: int, system: str, strip_think: bool) -> dict | None:
    text    = truncate_words(comment_text, P2_MAX_WORDS)
    user_msg = (
        f"Meeting: {meeting_title}\n"
        f"Block ID: {block_id}\n\n"
        f"Public comment text:\n\"{text}\"\n\n"
        "Score this comment against all four themes."
    )
    raw = call_llm(llm, system, user_msg, max_tokens=700, strip_think=strip_think)
    if raw is None:
        return None
    return parse_json_safe(raw, f"P2 block {block_id} from {meeting_title}")


def run_phase2(llm: Llama, model_cfg: dict, model_name: str,
               p1_dir: str, out_dir: str) -> None:
    themes_content = load_themes_md()
    system = build_system(
        P2_SYSTEM_TEMPLATE.format(themes_content=themes_content),
        model_cfg["no_think"],
    )

    p1_files = sorted(glob(os.path.join(p1_dir, "*.json")))
    if not p1_files:
        print(f"  No Phase 1 output found in {p1_dir} — run Phase 1 first.")
        return

    print(f"\nPhase 2: {len(p1_files)} meetings with Phase 1 output\n")

    for path in tqdm(p1_files, desc="Phase 2"):
        out_path = os.path.join(out_dir, os.path.basename(path))
        if os.path.exists(out_path):
            tqdm.write(f"  SKIP (already done): {os.path.basename(path)}")
            continue

        data = load_json(path)
        if data is None:
            continue

        comments = data.get("public_comments", [])
        if not comments:
            tqdm.write(f"  SKIP (no public comments): {os.path.basename(path)}")
            continue

        title       = data.get("title", os.path.basename(path))
        theme_scores = []

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

        result = {
            "title":        data.get("title"),
            "video_id":     data.get("video_id"),
            "upload_date":  data.get("upload_date"),
            "model":        model_name,
            "theme_scores": theme_scores,
        }
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)

        n_scored = sum(1 for e in theme_scores if e["themes"] is not None)
        tqdm.write(f"  {title}: {n_scored}/{len(comments)} comments scored")


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
            exists = "✓" if os.path.exists(cfg["path"]) else "✗ NOT FOUND"
            print(f"  {name:<22} {exists}  {os.path.basename(cfg['path'])}")
        return

    if not args.model:
        parser.error("--model is required unless --list is used")

    if args.model not in MODELS:
        print(f"Unknown model '{args.model}'. Run with --list to see options.")
        return

    model_cfg  = MODELS[args.model]
    model_name = args.model

    if not os.path.exists(model_cfg["path"]):
        print(f"Model file not found: {model_cfg['path']}")
        return

    p1_dir = os.path.join(OUTPUTS_ROOT, model_name, "phase1_public_comments")
    p2_dir = os.path.join(OUTPUTS_ROOT, model_name, "phase2_theme_scores")
    os.makedirs(p1_dir, exist_ok=True)
    os.makedirs(p2_dir, exist_ok=True)

    print(f"Loading model: {model_cfg['path']}")
    llm = Llama(
        model_path=model_cfg["path"],
        n_ctx=model_cfg["n_ctx"],
        n_gpu_layers=model_cfg["n_gpu_layers"],
        verbose=False,
    )

    if args.phase in ("1", "both"):
        run_phase1(llm, model_cfg, model_name, p1_dir)

    if args.phase in ("2", "both"):
        run_phase2(llm, model_cfg, model_name, p1_dir, p2_dir)

    print("\nDone.")


if __name__ == "__main__":
    main()
