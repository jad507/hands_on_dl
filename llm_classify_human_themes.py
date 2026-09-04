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

from __future__ import annotations

import argparse
import json
import re
import os
import time
from glob import glob
from pathlib import Path
from typing import TYPE_CHECKING

import yaml

import paths
import provenance
from pipeline_utils import fmt_elapsed, now_str

if TYPE_CHECKING:                      # pragma: no cover
    from llama_cpp import Llama

# llama_cpp is imported lazily inside main(). Importing it initialises CUDA,
# which costs seconds and VRAM, and --list / --dry-run / --help have no reason
# to pay that or to fail on a machine where the wheel is not installed.

# ---------------------------------------------------------------------------
# Paths -- resolved relative to the repository, overridable by environment
# variable. See paths.py.
# ---------------------------------------------------------------------------
COMMENTS_DIR   = str(paths.COMMENTS_DIR)
THEMES_MD_PATH = str(paths.THEMES_MD_PATH)
OUTPUTS_ROOT   = str(paths.OUTPUTS_ROOT)


# ---------------------------------------------------------------------------
# Configuration -- model registry and run settings live in models.yaml so that
# they are versioned as data rather than buried in Python literals.
# ---------------------------------------------------------------------------
def load_config(path: Path | None = None) -> tuple[dict, dict]:
    cfg_path = path or paths.MODELS_CONFIG_PATH
    with open(cfg_path, encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    return cfg.get("models", {}), cfg.get("settings", {})


MODELS, SETTINGS = load_config()

# Phase 1: blocks per LLM call. At ~100 words/block summary, 3 blocks ≈ 300
# content tokens — leaves ample headroom for reason fields in large meetings.
P1_CHUNK_SIZE = SETTINGS.get("p1_chunk_size", 3)

# Phase 2: truncate comment text to this many words before sending.
# Keeps total prompt well under 8 192 tokens even with the full themes .md.
P2_MAX_WORDS = SETTINGS.get("p2_max_words", 600)

TEMPERATURE         = SETTINGS.get("temperature", 0.0)
P1_MAX_TOKENS       = SETTINGS.get("p1_max_tokens", 1500)
P1_RETRY_MAX_TOKENS = SETTINGS.get("p1_retry_max_tokens", 300)
P2_MAX_TOKENS       = SETTINGS.get("p2_max_tokens", 700)

# Prompt files. Kept outside the source so a given output can be traced back to
# the exact text that produced it; see prompts/README.md.
P1_PROMPT_FILE = paths.PROMPTS_DIR / "p1_system.txt"
P2_PROMPT_FILE = paths.PROMPTS_DIR / "p2_system.txt"

# ---------------------------------------------------------------------------
# JSON Schemas (passed to llama.cpp's grammar-constrained sampler so the model
# physically cannot emit invalid output — illegal tokens are masked at sample
# time. Eliminates ~all schema-compliance errors. Truncation by max_tokens is
# still possible and is handled via per-block / per-comment retries.)
# ---------------------------------------------------------------------------
P1_SCHEMA: dict = {
    "type": "object",
    "properties": {
        "public_comments": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "block_id":     {"type": "integer"},
                    "speaker_name": {"type": "string"},
                    "reason":       {"type": "string"},
                },
                "required": ["block_id", "speaker_name", "reason"],
            },
        }
    },
    "required": ["public_comments"],
}

P2_THEME_KEYS = [
    "municipally_managed_resources",
    "municipal_process",
    "health_and_well_being",
    "power_dynamics_and_inequality",
]

P2_SCHEMA: dict = {
    "type": "object",
    "properties": {
        "themes": {
            "type": "object",
            "properties": {
                key: {
                    "type": "object",
                    "properties": {
                        "score":     {"type": "number", "minimum": 0.0, "maximum": 1.0},
                        "reasoning": {"type": "string"},
                    },
                    "required": ["score", "reasoning"],
                }
                for key in P2_THEME_KEYS
            },
            "required": P2_THEME_KEYS,
        }
    },
    "required": ["themes"],
}

# ---------------------------------------------------------------------------
# System prompts
#
# Loaded from prompts/*.txt rather than defined here, so that the SHA-256 of
# the file that produced any given output can be recorded alongside it.
# ---------------------------------------------------------------------------


def load_prompt(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def build_p2_system(themes_content: str) -> str:
    """Substitute the theme definitions into the phase 2 prompt.

    Plain replacement, not str.format: the prompt contains a literal JSON
    example, and requiring every brace in it to be doubled is a trap for
    anyone editing the prompt file.
    """
    return load_prompt(P2_PROMPT_FILE).replace("{themes_content}", themes_content)


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
             strip_think: bool, schema: dict | None = None) -> str | None:
    response_format: dict = {"type": "json_object"}
    if schema is not None:
        response_format["schema"] = schema
    response = llm.create_chat_completion(
        messages=[
            {"role": "system", "content": system},
            {"role": "user",   "content": user},
        ],
        temperature=TEMPERATURE,
        max_tokens=max_tokens,
        response_format=response_format,
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
                   max_tokens=P1_MAX_TOKENS, strip_think=strip_think, schema=P1_SCHEMA)
    if raw is not None:
        parsed = parse_json_safe(raw, f"P1 chunk from {meeting_title}")
        if parsed is not None and "public_comments" in parsed:
            return parsed["public_comments"], 0

    # Grammar constraints prevent schema mismatch, so reaching here means the
    # output was truncated by max_tokens (invalid JSON). Retry each block
    # individually — far smaller per-call output, less likely to hit the cap.
    print(f"  P1 truncated/invalid from {meeting_title} — retrying {len(blocks)} block(s) individually")

    # Retry each block one at a time with a simpler prompt
    recovered: list[dict] = []
    n_still_failed = 0
    for block in blocks:
        retry_raw = call_llm(llm, system, _p1_retry_user_msg(block, meeting_title),
                             max_tokens=P1_RETRY_MAX_TOKENS, strip_think=strip_think, schema=P1_SCHEMA)
        if retry_raw is None:
            n_still_failed += 1
            continue
        retry_parsed = parse_json_safe(retry_raw, f"P1 retry block {block['block_id']} from {meeting_title}")
        if retry_parsed is None or "public_comments" not in retry_parsed:
            n_still_failed += 1
        else:
            recovered.extend(retry_parsed["public_comments"])

    return recovered, (1 if n_still_failed > 0 else 0)


def p1_chunks(blocks: list, size: int, offset: int = 0) -> list[list]:
    """Split blocks into the batches phase 1 sends to the model.

    `offset` rotates where the batch boundaries fall WITHOUT changing the block
    list: the first chunk is short by `offset` blocks and every later boundary
    shifts by the same amount.

    That parameter exists because of what the diarization-variant analysis
    found. A single inserted or deleted block upstream shifts every later chunk
    boundary, and blocks judged in a differently-composed chunk change
    classification 12-17% of the time on byte-identical text. `offset`
    reproduces that shift deliberately, so the natural experiment in
    `compare_diarization_variants.py` can be replaced by a designed one in which
    nothing varies except the batching.

    Invariant: every block appears exactly once, in order, at any size and
    offset. Asserted in tests -- a chunker that dropped or duplicated a block
    would change N and quietly invalidate the comparison.
    """
    if size < 1:
        raise ValueError("chunk size must be at least 1")
    n = len(blocks)
    off = offset % size if offset else 0
    starts = ([0] + list(range(off, n, size))) if off else list(range(0, n, size))
    out = [blocks[a:b] for a, b in zip(starts, starts[1:] + [n])]
    return [c for c in out if c]


def run_phase1(llm: Llama, model_cfg: dict, model_name: str, out_dir: str,
               model_path: Path, limit: int | None = None,
               chunk_size: int | None = None, chunk_offset: int = 0) -> None:
    system        = build_system(load_prompt(P1_PROMPT_FILE), model_cfg["no_think"])
    meeting_files = sorted(glob(os.path.join(COMMENTS_DIR, "*.json")))
    total_start   = time.perf_counter()
    n_done = n_skipped = n_errors = 0

    prov = provenance.build_provenance(
        model_name=model_name, model_cfg=model_cfg, model_path=model_path,
        prompt_file=P1_PROMPT_FILE, rendered_system=system, settings=SETTINGS,
    )
    # The effective chunking, not the configured one. An output produced under
    # --chunk-size 5 must not look like one produced at the default.
    prov["chunking"] = {
        "p1_chunk_size": chunk_size or P1_CHUNK_SIZE,
        "p1_chunk_offset": chunk_offset,
    }

    if limit is not None:
        meeting_files = meeting_files[:limit]
        print(f"\n[{now_str()}] Phase 1 starting: {len(meeting_files)} meeting files "
              f"(--limit {limit})")
    else:
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
        chunks = p1_chunks(all_blocks, chunk_size or P1_CHUNK_SIZE,
                           chunk_offset)
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
            "provenance":      prov,
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

    def _call(text: str, simpler: bool = False) -> dict | None:
        if simpler:
            user_msg = (
                f"Public comment from {meeting_title} (block {block_id}):\n"
                f'"{text}"\n\n'
                "Score this comment 0.0-1.0 on each of the four themes."
            )
        else:
            user_msg = (
                f"Meeting: {meeting_title}\n"
                f"Block ID: {block_id}\n\n"
                f"Public comment text:\n\"{text}\"\n\n"
                "Score this comment against all four themes."
            )
        raw = call_llm(llm, system, user_msg, max_tokens=P2_MAX_TOKENS,
                       strip_think=strip_think, schema=P2_SCHEMA)
        if raw is None:
            return None
        parsed = parse_json_safe(raw, context)
        if parsed is None or "themes" not in parsed:
            return None
        return parsed

    result = _call(comment_text)
    if result is not None:
        return result

    if len(comment_text.split()) > P2_MAX_WORDS:
        print(f"  P2 block {block_id}: retrying with {P2_MAX_WORDS}-word truncation")
        result = _call(truncate_words(comment_text, P2_MAX_WORDS))
        if result is not None:
            return result

    print(f"  P2 block {block_id}: retrying with simpler prompt")
    return _call(truncate_words(comment_text, P2_MAX_WORDS), simpler=True)


def run_phase2(llm: Llama, model_cfg: dict, model_name: str,
               p1_dir: str, out_dir: str, model_path: Path,
               limit: int | None = None) -> None:
    themes_content = load_themes_md()
    system = build_system(
        build_p2_system(themes_content),
        model_cfg["no_think"],
    )

    p1_files    = sorted(glob(os.path.join(p1_dir, "*.json")))
    total_start = time.perf_counter()
    n_done = n_skipped = n_errors = 0

    if not p1_files:
        print(f"  No Phase 1 output found in {p1_dir} — run Phase 1 first.")
        return

    # The theme definitions are part of the phase 2 prompt, so their hash is
    # recorded too: editing that .md changes the prompt without changing any code.
    prov = provenance.build_provenance(
        model_name=model_name, model_cfg=model_cfg, model_path=model_path,
        prompt_file=P2_PROMPT_FILE, rendered_system=system, settings=SETTINGS,
        extra_files={"themes_md": paths.THEMES_MD_PATH},
    )

    if limit is not None:
        p1_files = p1_files[:limit]
        print(f"\n[{now_str()}] Phase 2 starting: {len(p1_files)} meetings with "
              f"Phase 1 output (--limit {limit})")
    else:
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
            "provenance":         prov,
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
# Pre-flight
# ---------------------------------------------------------------------------

def run_preflight(model_cfg: dict, phase: str, model_path: Path) -> bool:
    """Validate environment before loading the model. Returns False on any
    hard failure so main() can bail before the slow model load."""
    import subprocess
    print(f"[{now_str()}] Pre-flight checks")
    ok = True

    if not model_path.exists():
        print(f"  FAIL: model file not found: {model_path}")
        ok = False
    else:
        print(f"  OK   model file ({model_path.stat().st_size / 1e9:.2f} GB)")

    for label, prompt_file in (("phase 1 prompt", P1_PROMPT_FILE),
                               ("phase 2 prompt", P2_PROMPT_FILE)):
        needed = (phase in ("1", "both")) if label.endswith("1 prompt") else \
                 (phase in ("2", "both"))
        if not needed:
            continue
        if not prompt_file.exists():
            print(f"  FAIL: {label} missing: {prompt_file}")
            ok = False
        else:
            sha = provenance.sha256_text(prompt_file.read_text(encoding="utf-8"))
            print(f"  OK   {label} ({prompt_file.name}, sha {sha[:12]})")

    if not os.path.isdir(COMMENTS_DIR):
        print(f"  FAIL: comments directory missing: {COMMENTS_DIR}")
        ok = False
    else:
        n = len(glob(os.path.join(COMMENTS_DIR, "*.json")))
        if n == 0:
            print(f"  FAIL: no meeting JSONs in {COMMENTS_DIR}")
            ok = False
        else:
            print(f"  OK   {n} meeting files")

    if phase in ("2", "both"):
        if not os.path.exists(THEMES_MD_PATH):
            print(f"  FAIL: themes file missing: {THEMES_MD_PATH}")
            ok = False
        else:
            print(f"  OK   themes definition file")

    try:
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=name,memory.free,memory.total",
             "--format=csv,noheader"],
            capture_output=True, text=True, timeout=5,
        )
        if result.returncode == 0:
            print(f"  OK   GPU: {result.stdout.strip()}")
        else:
            print(f"  WARN nvidia-smi exit {result.returncode}; GPU state unknown")
    except Exception as e:
        print(f"  WARN nvidia-smi check failed: {e}")

    return ok


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
    parser.add_argument("--limit", type=int, metavar="N",
                        help="Process at most N meetings per phase. For smoke-testing "
                             "a config change without committing to a multi-hour run.")
    parser.add_argument("--chunk-size", type=int, metavar="N",
                        help="override p1_chunk_size for this run. The ISLS "
                             "finding is about this parameter, so it is "
                             "adjustable and recorded in every output's "
                             "provenance block.")
    parser.add_argument("--chunk-offset", type=int, default=0, metavar="K",
                        help="shift where phase-1 batch boundaries fall, without "
                             "changing the block list. Reproduces under control "
                             "what an inserted or deleted block upstream does by "
                             "accident.")
    parser.add_argument("--dry-run", action="store_true",
                        help="Resolve paths, validate config and prompts, and report what "
                             "would run -- without loading the model or writing anything.")
    args = parser.parse_args()

    if args.list:
        root = paths.models_root(required=False)
        print(f"HODL_MODELS_ROOT = {root if root else '(not set -- cannot check files)'}")
        print("Available models:")
        for name, cfg in MODELS.items():
            mp = paths.resolve_model_path(cfg["path"], required=False)
            if mp is None:
                exists = "unknown"
            else:
                exists = "ok" if mp.exists() else "NOT FOUND"
            backend = cfg.get("backend", "llama_cpp")
            flag    = "" if backend == "llama_cpp" else f"  [{backend} — not runnable here]"
            print(f"  {name:<22} {exists:<9}  {cfg['path']}{flag}")
        return

    if not args.model:
        parser.error("--model is required unless --list is used")

    if args.model not in MODELS:
        print(f"Unknown model '{args.model}'. Run with --list to see options.")
        return

    if args.limit is not None and args.limit < 1:
        parser.error("--limit must be at least 1")

    if args.chunk_size is not None and args.chunk_size < 1:
        parser.error("--chunk-size must be at least 1")
    if args.chunk_offset < 0:
        parser.error("--chunk-offset must not be negative")

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

    # required=False so a --dry-run on a machine without HODL_MODELS_ROOT still
    # reports every other problem instead of stopping at the first one.
    model_path = paths.resolve_model_path(model_cfg["path"], required=not args.dry_run)

    p1_dir = os.path.join(OUTPUTS_ROOT, model_name, "phase1_public_comments")
    p2_dir = os.path.join(OUTPUTS_ROOT, model_name, "phase2_theme_scores")

    if args.dry_run:
        print(f"[{now_str()}] DRY RUN -- nothing will be loaded or written\n")
        print(f"  model         {model_name}  ({backend})")
        print(f"  model path    {model_path if model_path else '(HODL_MODELS_ROOT not set)'}")
        print(f"  comments dir  {COMMENTS_DIR}")
        print(f"  themes md     {THEMES_MD_PATH}")
        print(f"  phase 1 out   {p1_dir}")
        print(f"  phase 2 out   {p2_dir}")
        print(f"  settings      {SETTINGS}")
        eff_size = args.chunk_size or SETTINGS.get("p1_chunk_size", 3)
        if args.chunk_size or args.chunk_offset:
            print(f"  chunking      size {eff_size} (OVERRIDE), "
                  f"offset {args.chunk_offset}")
        else:
            print(f"  chunking      size {eff_size}, offset 0 (defaults)")

        n_meetings = len(sorted(glob(os.path.join(COMMENTS_DIR, "*.json"))))
        n_planned  = min(n_meetings, args.limit) if args.limit else n_meetings
        print(f"\n  {n_meetings} meeting files found; "
              f"{n_planned} would be considered for phase {args.phase}")
        print("  (per-meeting SKIP/REDO resume logic is not evaluated in a dry run)\n")

        ok = run_preflight(model_cfg, args.phase,
                           model_path or Path("(unset)"))
        print("\nDry run OK." if ok else "\nDry run found problems (above).")
        return

    if not run_preflight(model_cfg, args.phase, model_path):
        print("Aborting before model load.")
        return

    os.makedirs(p1_dir, exist_ok=True)
    os.makedirs(p2_dir, exist_ok=True)

    from llama_cpp import Llama          # deferred: initialising CUDA is slow

    print(f"[{now_str()}] Loading model: {model_path}")
    t0  = time.perf_counter()
    llm = Llama(
        model_path=str(model_path),
        n_ctx=model_cfg["n_ctx"],
        n_gpu_layers=model_cfg["n_gpu_layers"],
        verbose=False,
    )
    print(f"  Loaded in {fmt_elapsed(time.perf_counter() - t0)}")

    if args.phase in ("1", "both"):
        run_phase1(llm, model_cfg, model_name, p1_dir,
                   model_path, limit=args.limit,
                   chunk_size=args.chunk_size,
                   chunk_offset=args.chunk_offset)

    if args.phase in ("2", "both"):
        run_phase2(llm, model_cfg, model_name, p1_dir, p2_dir, model_path, args.limit)

    print("\nDone.")


if __name__ == "__main__":
    main()
