"""
chunk_token_histogram.py — Token-count histogram for classify_chunk prompts.

Simulates how llm_extract_comments.py formats each chunk into a prompt, counts
tokens using the GGUF model's own tokenizer, and prints a histogram.

Use the percentile table to choose N_CTX and CHUNK_SIZE in llm_extract_comments.py:
  n_ctx >= p95_prompt_tokens + CLASSIFY_MAX_TOKENS

The model is loaded CPU-only (n_gpu_layers=0) just for tokenization, so it
won't compete with a running GPU job but will use ~7–8 GB of RAM for 30–60s.
"""

import glob
import json
import os
import time
from pathlib import Path

from llama_cpp import Llama

import paths
from pipeline_utils import fmt_elapsed, now_str

# Model weights are machine-specific; see paths.py and HODL_MODELS_ROOT.
MODEL_PATH          = str(paths.resolve_model_path("bartowski/Qwen_Qwen3.5-9B-Q6_K_L.gguf"))
COMMENTS_DIR        = str(paths.COMMENTS_DIR)
CHUNK_SIZE          = 50      # must match llm_extract_comments.py
CLASSIFY_MAX_TOKENS = 512     # max_tokens used in classify_chunk
OUTPUT_FILE         = Path(__file__).parent / "chunk_token_histogram.txt"

SYSTEM_PROMPT = """/no_think
You are analyzing transcripts of Lancaster City Council meetings.
Public comment periods allow community members to address the council directly.
Public commenters typically state their name and home address at the start,
speak for up to 3 minutes (sometimes longer), and raise concerns or opinions.
Not every speaker is a public commenter — council members, staff, and presenters
are not public commenters.
Respond only with valid JSON and no other text.
"""

BUCKETS = [
    (0,      2000,   "0-2K"),
    (2000,   4000,   "2-4K"),
    (4000,   6000,   "4-6K"),
    (6000,   8000,   "6-8K"),
    (8000,   10000,  "8-10K"),
    (10000,  12000,  "10-12K"),
    (12000,  16000,  "12-16K"),
    (16000,  32000,  "16-32K"),
    (32000,  999999, "32K+"),
]


def format_blocks(blocks: list[dict]) -> str:
    lines = []
    for b in blocks:
        mins = int(b["start"] // 60)
        secs = int(b["start"] % 60)
        lines.append(f'[Block {b["block_id"]} | {mins:02d}:{secs:02d} | {b["speaker"]}]: "{b["text"]}"')
    return "\n".join(lines)


def get_blocks(data: dict) -> list[dict]:
    return data.get("blocks") or data.get("commenter_blocks") or []


def build_prompt(blocks: list[dict], meeting_title: str) -> str:
    """Render the full prompt as llm_extract_comments.classify_chunk would send it."""
    user_msg = (
        f"Meeting: {meeting_title}\n\n"
        f"Transcript blocks:\n{format_blocks(blocks)}\n\n"
        "Identify which blocks (if any) are from public comment speakers.\n"
        'Return JSON: {"public_comments": [{"block_id": <int>, "speaker_name": "<name or unknown>", "topic_summary": "<brief topic>"}]}\n'
        'If no blocks are public comments, return: {"public_comments": []}'
    )
    # Qwen3.5 chat template (matches what llama-cpp-python applies internally)
    return (
        f"<|im_start|>system\n{SYSTEM_PROMPT}<|im_end|>\n"
        f"<|im_start|>user\n{user_msg}<|im_end|>\n"
        f"<|im_start|>assistant\n"
    )


def pct(sorted_vals: list[int], p: float) -> int:
    if not sorted_vals:
        return 0
    idx = min(int(len(sorted_vals) * p / 100), len(sorted_vals) - 1)
    return sorted_vals[idx]


def main():
    t0 = time.perf_counter()

    print(f"[{now_str()}] Loading tokenizer (CPU-only, n_gpu_layers=0)...")
    print(f"  {MODEL_PATH}")
    llm = Llama(model_path=MODEL_PATH, n_gpu_layers=0, n_ctx=512, verbose=False)
    print(f"  Loaded in {fmt_elapsed(time.perf_counter() - t0)}\n")

    meeting_files = sorted(glob.glob(os.path.join(COMMENTS_DIR, "*.json")))
    print(f"[{now_str()}] Scanning {len(meeting_files)} meetings...")

    token_counts: list[int] = []
    n_meetings = 0

    for path in meeting_files:
        try:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            print(f"  SKIP {os.path.basename(path)}: {e}")
            continue

        blocks = get_blocks(data)
        if not blocks:
            continue

        n_meetings += 1
        title = data.get("title", os.path.basename(path))
        chunks = [blocks[i:i + CHUNK_SIZE] for i in range(0, len(blocks), CHUNK_SIZE)]

        for chunk in chunks:
            prompt = build_prompt(chunk, title)
            # special=True so <|im_start|> etc. are tokenized as single special tokens
            n_tokens = len(llm.tokenize(prompt.encode(), add_bos=False, special=True))
            token_counts.append(n_tokens)

    if not token_counts:
        print("No chunks found.")
        return

    token_counts.sort()
    total = len(token_counts)

    lines: list[str] = []
    lines.append(f"Chunk token histogram — {n_meetings} meetings, {total} chunks, CHUNK_SIZE={CHUNK_SIZE}")
    lines.append(f"Prompt tokens only (system + user + Qwen template); CLASSIFY_MAX_TOKENS={CLASSIFY_MAX_TOKENS} not included")
    lines.append("")

    max_bucket_count = max(
        sum(1 for t in token_counts if lo <= t < hi) for lo, hi, _ in BUCKETS
    )
    bar_scale = max(1, max_bucket_count // 50)

    for lo, hi, label in BUCKETS:
        count = sum(1 for t in token_counts if lo <= t < hi)
        bar = "#" * (count // bar_scale)
        lines.append(f"  {label:>8}  {count:5d}  {count / total * 100:5.1f}%  {bar}")

    lines.append("")
    lines.append(f"Percentiles -- prompt tokens  |  n_ctx needed (prompt + {CLASSIFY_MAX_TOKENS} max_tokens)")
    lines.append(f"  {'Pct':>4}   {'Prompt':>8}   {'n_ctx >=':>9}")
    lines.append(f"  {'-'*4}   {'-'*8}   {'-'*9}")
    for p in [50, 75, 90, 95, 99, 100]:
        v = pct(token_counts, p)
        label = f"p{p}" if p < 100 else "max"
        lines.append(f"  {label:>4}   {v:>8,}   {v + CLASSIFY_MAX_TOKENS:>9,}")

    lines.append("")
    lines.append(f"  Mean prompt: {sum(token_counts) // total:,} tokens")
    lines.append(f"  Total chunks: {total:,}  |  Total meetings: {n_meetings}")

    output = "\n".join(lines)
    print("\n" + output)

    OUTPUT_FILE.write_text(output + "\n", encoding="utf-8")
    print(f"\nWrote to {OUTPUT_FILE}  [{fmt_elapsed(time.perf_counter() - t0)}]")


if __name__ == "__main__":
    main()