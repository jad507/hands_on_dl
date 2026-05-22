"""
Two-phase pipeline using a local GGUF model to extract public comments and
produce a topic analysis from Lancaster City Council meeting transcripts.

Phase 1: For each meeting in COMMENTS_DIR, classify blocks as public comments
         or not, saving per-meeting results to PUBLIC_COMMENTS_DIR.
         Already-processed files are skipped so the run is resumable.

Phase 2: Aggregate all extracted public comments and generate a topic analysis
         saved to ANALYSIS_PATH.

Prerequisite: re-run extract_commenter_blocks.py (with corrected paths) to
populate COMMENTS_DIR with the updated unfiltered transcripts before running
this script.
"""

import json
import glob
import os
from tqdm import tqdm
from llama_cpp import Llama

MODEL_PATH          = r"D:\LLM\bartowski\Qwen_Qwen3.5-9B-Q6_K_L.gguf"
COMMENTS_DIR        = r"D:\Users\jad507\PycharmProjects\hands_on_dl\downloads\comments"
PUBLIC_COMMENTS_DIR = r"D:\Users\jad507\PycharmProjects\hands_on_dl\downloads\public_comments"
ANALYSIS_PATH       = r"D:\Users\jad507\PycharmProjects\hands_on_dl\downloads\topic_analysis.json"

N_CTX        = 8192
CHUNK_SIZE   = 50    # blocks per LLM call — keeps each call well within context
N_GPU_LAYERS = -1    # offload all layers to GPU

SYSTEM_PROMPT = """/no_think
You are analyzing transcripts of Lancaster City Council meetings.
Public comment periods allow community members to address the council directly.
Public commenters typically state their name and home address at the start,
speak for up to 3 minutes (sometimes longer), and raise concerns or opinions.
Not every speaker is a public commenter — council members, staff, and presenters
are not public commenters.
Respond only with valid JSON and no other text.
"""


def load_json(path: str) -> dict | None:
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"  Could not load {os.path.basename(path)}: {e}")
        return None


def get_blocks(data: dict) -> list[dict]:
    # Handle both old key name (commenter_blocks) and new key name (blocks)
    return data.get("blocks") or data.get("commenter_blocks") or []


def format_blocks(blocks: list[dict]) -> str:
    lines = []
    for b in blocks:
        mins = int(b["start"] // 60)
        secs = int(b["start"] % 60)
        lines.append(f'[Block {b["block_id"]} | {mins:02d}:{secs:02d} | {b["speaker"]}]: "{b["text"]}"')
    return "\n".join(lines)


def classify_chunk(llm: Llama, blocks: list[dict], meeting_title: str) -> list[dict]:
    user_msg = (
        f"Meeting: {meeting_title}\n\n"
        f"Transcript blocks:\n{format_blocks(blocks)}\n\n"
        "Identify which blocks (if any) are from public comment speakers.\n"
        'Return JSON: {"public_comments": [{"block_id": <int>, "speaker_name": "<name or unknown>", "topic_summary": "<brief topic>"}]}\n'
        'If no blocks are public comments, return: {"public_comments": []}'
    )
    response = llm.create_chat_completion(
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user",   "content": user_msg},
        ],
        temperature=0.0,
        max_tokens=512,
        response_format={"type": "json_object"},
    )
    raw = response["choices"][0]["message"]["content"].strip()
    try:
        return json.loads(raw).get("public_comments", [])
    except json.JSONDecodeError:
        tqdm.write(f"  Warning: unparseable JSON: {raw[:150]}")
        return []


def process_meeting(llm: Llama, path: str) -> dict | None:
    data = load_json(path)
    if data is None:
        return None

    blocks = get_blocks(data)
    if not blocks:
        return None

    title = data.get("title", os.path.basename(path))

    identified = []
    chunks = [blocks[i:i + CHUNK_SIZE] for i in range(0, len(blocks), CHUNK_SIZE)]
    for chunk in chunks:
        identified.extend(classify_chunk(llm, chunk, title))

    block_by_id = {b["block_id"]: b for b in blocks}
    public_comments = []
    for item in identified:
        bid = item.get("block_id")
        if bid not in block_by_id:
            continue
        b = block_by_id[bid]
        public_comments.append({
            "block_id":     bid,
            "speaker":      b["speaker"],
            "start":        b["start"],
            "end":          b["end"],
            "speaker_name": item.get("speaker_name", "unknown"),
            "topic_summary": item.get("topic_summary", ""),
            "text":         b["text"],
        })

    return {
        "title":          data.get("title"),
        "video_id":       data.get("video_id"),
        "upload_date":    data.get("upload_date"),
        "public_comments": public_comments,
    }


def summarize_comment_chunk(llm: Llama, comments: list[dict]) -> dict:
    comment_text = "\n\n".join(
        f'[{c["upload_date"]} | {c["speaker_name"]}]: {c["text"]}'
        for c in comments
    )
    response = llm.create_chat_completion(
        messages=[
            {"role": "system", "content": "/no_think\nYou summarize public comments from city council meetings. Respond only with valid JSON."},
            {"role": "user", "content": (
                "These are public comments from Lancaster City Council meetings.\n"
                "List the main topics/concerns raised with brief examples.\n\n"
                f"{comment_text}\n\n"
                'Return JSON: {"topics": [{"theme": "...", "examples": ["..."]}]}'
            )},
        ],
        temperature=0.0,
        max_tokens=1024,
        response_format={"type": "json_object"},
    )
    raw = response["choices"][0]["message"]["content"].strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {}


def analyze_topics(llm: Llama, all_meetings: list[dict]) -> dict:
    flat_comments = [
        {**c, "upload_date": m.get("upload_date", ""), "meeting_title": m.get("title", "")}
        for m in all_meetings
        for c in m.get("public_comments", [])
    ]

    if not flat_comments:
        return {"error": "No public comments found across all meetings."}

    print(f"  Aggregating {len(flat_comments)} public comments across {len(all_meetings)} meetings...")

    intermediate = []
    chunk_size = 30
    for i in range(0, len(flat_comments), chunk_size):
        result = summarize_comment_chunk(llm, flat_comments[i:i + chunk_size])
        if result:
            intermediate.append(result)

    response = llm.create_chat_completion(
        messages=[
            {"role": "system", "content": "/no_think\nYou synthesize research findings into a clear report. Respond only with valid JSON."},
            {"role": "user", "content": (
                "Below are intermediate topic summaries from Lancaster City Council public comments "
                f"({all_meetings[0].get('upload_date', '?')} to {all_meetings[-1].get('upload_date', '?')}).\n\n"
                f"{json.dumps(intermediate, indent=2)}\n\n"
                'Produce a final consolidated analysis answering: "What topics of concern do speakers '
                'raise to the Lancaster City Council during public comment periods?"\n'
                "Organize by major theme. Be specific.\n"
                'Return JSON: {"question": "...", "analysis": [{"theme": "...", "description": "...", '
                '"frequency": "common/occasional/rare", "examples": ["..."]}]}'
            )},
        ],
        temperature=0.2,
        max_tokens=2048,
        response_format={"type": "json_object"},
    )
    raw = response["choices"][0]["message"]["content"].strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {"raw_analysis": raw}


def main():
    os.makedirs(PUBLIC_COMMENTS_DIR, exist_ok=True)

    print(f"Loading model: {MODEL_PATH}")
    llm = Llama(
        model_path=MODEL_PATH,
        n_ctx=N_CTX,
        n_gpu_layers=N_GPU_LAYERS,
        verbose=False,
    )

    # --- Phase 1: per-meeting classification ---
    meeting_files = sorted(glob.glob(os.path.join(COMMENTS_DIR, "*.json")))
    print(f"\nPhase 1: {len(meeting_files)} meetings to process\n")

    all_results = []
    for path in tqdm(meeting_files):
        out_path = os.path.join(PUBLIC_COMMENTS_DIR, os.path.basename(path))
        if os.path.exists(out_path):
            cached = load_json(out_path)
            if cached:
                all_results.append(cached)
            continue

        result = process_meeting(llm, path)
        if result is None:
            tqdm.write(f"  SKIP (no blocks): {os.path.basename(path)}")
            continue

        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)

        n = len(result["public_comments"])
        tqdm.write(f"  {result['title']}: {n} public comments found")
        all_results.append(result)

    total_comments = sum(len(m["public_comments"]) for m in all_results)
    print(f"\nPhase 1 complete: {total_comments} public comments across {len(all_results)} meetings")

    # --- Phase 2: topic analysis ---
    print("\nPhase 2: Generating topic analysis...")
    all_results.sort(key=lambda m: m.get("upload_date") or "")
    analysis = analyze_topics(llm, all_results)

    with open(ANALYSIS_PATH, "w", encoding="utf-8") as f:
        json.dump(analysis, f, indent=2, ensure_ascii=False)
    print(f"\nAnalysis saved to: {ANALYSIS_PATH}")


if __name__ == "__main__":
    main()