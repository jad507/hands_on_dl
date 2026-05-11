"""
group_speakers.py — Merge aligned segments into contiguous speaker blocks.

Reads aligned JSON (from align.py) and:
  1. Merges consecutive same-speaker segments separated by <= max_gap_s into blocks
  2. Classifies speakers as "recurring" (council staff) vs "commenter_candidate"
     using two signals: total speech duration and average segment length
  3. Concatenates segment text within each block

Classification heuristic
------------------------
Council staff speak frequently in short bursts throughout the meeting.
Public commenters speak in one or two sustained blocks and then go silent.

  recurring: total_speech_s > recurring_threshold_s
             AND avg_segment_s < avg_segment_threshold_s
  commenter_candidate: everything else

Both thresholds are configurable via CLI. Defaults are conservative — when in
doubt a speaker is left as commenter_candidate for the LLM to review.

Output
------
  downloads/grouped_standard/<stem>.json
  downloads/grouped_exclusive/<stem>.json

Output format:
{
  "file": "<stem>",
  "rttm_mode": "standard",
  "speaker_classification": {
    "SPEAKER_05": {
      "category": "recurring",
      "total_speech_s": 564.1,
      "block_count": 12,
      "segment_count": 127,
      "avg_segment_s": 4.4
    },
    ...
  },
  "blocks": [
    {
      "block_id": 0,
      "speaker": "SPEAKER_05",
      "category": "recurring",
      "start": 116.0,
      "end": 131.7,
      "duration_s": 15.7,
      "segment_count": 3,
      "word_count": 42,
      "text": "Now that the longest minute of the day..."
    },
    ...
  ]
}

Usage:
  python audio_pipeline/group_speakers.py                     # all files, both modes
  python audio_pipeline/group_speakers.py --mode standard
  python audio_pipeline/group_speakers.py --input downloads/audio/some_file.m4a
  python audio_pipeline/group_speakers.py --max-gap 60        # merge gaps up to 60s
  python audio_pipeline/group_speakers.py --recurring-threshold 240  # >4min = recurring
"""

import argparse
import json
import sys
import traceback
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
ALIGNED_DIRS = {
    "standard": REPO_ROOT / "downloads" / "aligned_standard",
    "exclusive": REPO_ROOT / "downloads" / "aligned_exclusive",
}
OUT_DIRS = {
    "standard": REPO_ROOT / "downloads" / "grouped_standard",
    "exclusive": REPO_ROOT / "downloads" / "grouped_exclusive",
}

# Classification defaults
DEFAULT_MAX_GAP_S = 30.0          # merge same-speaker segments within this gap
DEFAULT_RECURRING_THRESHOLD_S = 180.0  # total speech > 3 min → likely recurring
DEFAULT_AVG_SEGMENT_THRESHOLD_S = 15.0  # avg segment < 15s → likely recurring


# ---------------------------------------------------------------------------
# Merging
# ---------------------------------------------------------------------------

def merge_segments(segments: list[dict], max_gap_s: float) -> list[dict]:
    """
    Merge consecutive same-speaker segments into blocks.

    A new block starts when:
      - the speaker changes, OR
      - the gap since the last same-speaker segment exceeds max_gap_s

    Within a block, text is joined with a single space.
    """
    if not segments:
        return []

    blocks = []
    current = {
        "speaker": segments[0]["speaker"],
        "start": segments[0]["start"],
        "end": segments[0]["end"],
        "texts": [segments[0]["text"]],
        "segment_count": 1,
    }

    for seg in segments[1:]:
        gap = seg["start"] - current["end"]
        same_speaker = seg["speaker"] == current["speaker"]

        if same_speaker and gap <= max_gap_s:
            # Extend current block
            current["end"] = seg["end"]
            current["texts"].append(seg["text"])
            current["segment_count"] += 1
        else:
            # Close current block and start a new one
            blocks.append(current)
            current = {
                "speaker": seg["speaker"],
                "start": seg["start"],
                "end": seg["end"],
                "texts": [seg["text"]],
                "segment_count": 1,
            }

    blocks.append(current)
    return blocks


# ---------------------------------------------------------------------------
# Classification
# ---------------------------------------------------------------------------

def classify_speakers(
    blocks: list[dict],
    aligned_summary: dict,
    recurring_threshold_s: float,
    avg_segment_threshold_s: float,
) -> dict:
    """
    Build per-speaker classification using total speech and average segment length.

    Uses the aligned speaker_summary for total speech/segment counts (which covers
    the full file), not just the blocks (which are merged).
    """
    classification = {}
    for speaker, stats in aligned_summary.items():
        total_s = stats["total_speech_s"]
        seg_count = stats["segment_count"]
        avg_seg_s = (total_s / seg_count) if seg_count > 0 else 0.0

        # Count blocks for this speaker
        block_count = sum(1 for b in blocks if b["speaker"] == speaker)

        is_high_duration = total_s > recurring_threshold_s
        is_short_avg_segment = avg_seg_s < avg_segment_threshold_s
        category = "recurring" if (is_high_duration and is_short_avg_segment) else "commenter_candidate"

        classification[speaker] = {
            "category": category,
            "total_speech_s": round(total_s, 1),
            "block_count": block_count,
            "segment_count": seg_count,
            "avg_segment_s": round(avg_seg_s, 1),
            "word_count": stats.get("word_count", 0),
        }

    return classification


# ---------------------------------------------------------------------------
# Main processing
# ---------------------------------------------------------------------------

def group_file(
    stem: str,
    mode: str,
    max_gap_s: float,
    recurring_threshold_s: float,
    avg_segment_threshold_s: float,
) -> bool:
    aligned_path = ALIGNED_DIRS[mode] / f"{stem}.json"
    out_path = OUT_DIRS[mode] / f"{stem}.json"

    if not aligned_path.exists():
        print(f"  [{mode}] SKIP — aligned output not found: {aligned_path.name}")
        return False
    if out_path.exists():
        print(f"  [{mode}] Already done, skipping.")
        return True

    data = json.loads(aligned_path.read_text(encoding="utf-8"))
    segments = data["segments"]
    aligned_summary = data.get("speaker_summary", {})

    raw_blocks = merge_segments(segments, max_gap_s)
    classification = classify_speakers(
        raw_blocks, aligned_summary, recurring_threshold_s, avg_segment_threshold_s
    )

    # Build final block list
    final_blocks = []
    for i, b in enumerate(raw_blocks):
        text = " ".join(b["texts"]).strip()
        category = classification.get(b["speaker"], {}).get("category", "commenter_candidate")
        final_blocks.append({
            "block_id": i,
            "speaker": b["speaker"],
            "category": category,
            "start": round(b["start"], 3),
            "end": round(b["end"], 3),
            "duration_s": round(b["end"] - b["start"], 1),
            "segment_count": b["segment_count"],
            "word_count": len(text.split()),
            "text": text,
        })

    out = {
        "file": stem,
        "rttm_mode": mode,
        "settings": {
            "max_gap_s": max_gap_s,
            "recurring_threshold_s": recurring_threshold_s,
            "avg_segment_threshold_s": avg_segment_threshold_s,
        },
        "speaker_classification": classification,
        "blocks": final_blocks,
    }

    OUT_DIRS[mode].mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")

    n_blocks = len(final_blocks)
    recurring = [s for s, c in classification.items() if c["category"] == "recurring"]
    candidates = [s for s, c in classification.items() if c["category"] == "commenter_candidate"]
    candidate_blocks = sum(1 for b in final_blocks if b["category"] == "commenter_candidate")

    print(f"  [{mode}] {n_blocks} blocks | "
          f"{len(recurring)} recurring speakers | "
          f"{len(candidates)} commenter candidates ({candidate_blocks} blocks) "
          f"-> {out_path.name}")
    return True


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def stems_from_input(input_arg, mode: str) -> list[str]:
    if input_arg:
        p = Path(input_arg)
        if p.is_file():
            return [p.stem]
        elif p.is_dir():
            return sorted(f.stem for f in p.glob("*.m4a"))
        else:
            print(f"ERROR: --input path not found: {p}")
            sys.exit(1)
    aligned_dir = ALIGNED_DIRS[mode]
    if not aligned_dir.exists():
        return []
    return sorted(f.stem for f in aligned_dir.glob("*.json"))


def main():
    parser = argparse.ArgumentParser(
        description="Merge aligned segments into speaker blocks and classify speakers"
    )
    parser.add_argument("--input", "-i", default=None,
                        help="Single .m4a file or directory (default: all aligned files)")
    parser.add_argument("--mode", "-m", choices=["standard", "exclusive", "both"],
                        default="both")
    parser.add_argument("--max-gap", type=float, default=DEFAULT_MAX_GAP_S,
                        help=f"Max gap (s) to merge same-speaker segments (default: {DEFAULT_MAX_GAP_S})")
    parser.add_argument("--recurring-threshold", type=float, default=DEFAULT_RECURRING_THRESHOLD_S,
                        help=f"Total speech (s) above which a speaker is 'recurring' (default: {DEFAULT_RECURRING_THRESHOLD_S})")
    parser.add_argument("--avg-segment-threshold", type=float, default=DEFAULT_AVG_SEGMENT_THRESHOLD_S,
                        help=f"Avg segment (s) below which a speaker is 'recurring' (default: {DEFAULT_AVG_SEGMENT_THRESHOLD_S})")
    args = parser.parse_args()

    modes = ["standard", "exclusive"] if args.mode == "both" else [args.mode]

    # Collect stems across all requested modes (union)
    all_stems = set()
    for mode in modes:
        all_stems.update(stems_from_input(args.input, mode))
    stems = sorted(all_stems)

    if not stems:
        print("No aligned files found. Run align.py first.")
        sys.exit(1)

    print(f"Files to group: {len(stems)}")
    print(f"Modes: {', '.join(modes)}")
    print(f"Settings: max_gap={args.max_gap}s, "
          f"recurring_threshold={args.recurring_threshold}s, "
          f"avg_segment_threshold={args.avg_segment_threshold}s")

    for stem in stems:
        print(f"\n{stem[:60]}...")
        for mode in modes:
            try:
                group_file(
                    stem, mode,
                    max_gap_s=args.max_gap,
                    recurring_threshold_s=args.recurring_threshold,
                    avg_segment_threshold_s=args.avg_segment_threshold,
                )
            except Exception:
                print(f"  [{mode}] ERROR:")
                traceback.print_exc()

    print("\nDone.")


if __name__ == "__main__":
    main()
