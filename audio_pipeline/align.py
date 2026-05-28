"""
align.py — Align whisper transcription segments to pyannote speaker labels.

Reads the whisper JSON and pyannote RTTM for each audio file, assigns each
whisper segment to the speaker with the most temporal overlap, and writes
an attributed JSON to downloads/aligned_MODE/.

Output per file: downloads/aligned_standard/<stem>.json
                 downloads/aligned_exclusive/<stem>.json

Each output JSON has the structure:
{
  "file": "<stem>",
  "rttm_mode": "standard" | "exclusive",
  "speaker_summary": {
    "SPEAKER_05": {"total_speech_s": 564.1, "segment_count": 127, "word_count": 4821},
    ...
  },
  "segments": [
    {"start": 116.0, "end": 121.1, "text": "...", "speaker": "SPEAKER_05"},
    ...
  ]
}

Usage:
  python audio_pipeline/align.py                      # all files, both modes
  python audio_pipeline/align.py --mode standard      # standard RTTM only
  python audio_pipeline/align.py --mode exclusive     # exclusive RTTM only
  python audio_pipeline/align.py --input downloads/audio/some_file.m4a
"""

import argparse
import json
import sys
import time
import traceback
from collections import defaultdict
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(REPO_ROOT))
from pipeline_utils import fmt_elapsed, now_str  # noqa: E402
AUDIO_DIR = REPO_ROOT / "downloads" / "audio"
WHISPER_DIR = REPO_ROOT / "downloads" / "whisper_large-v3"
RTTM_DIRS = {
    "standard": REPO_ROOT / "downloads" / "pyannote_community-1_standard",
    "exclusive": REPO_ROOT / "downloads" / "pyannote_community-1_exclusive",
}
OUT_DIRS = {
    "standard": REPO_ROOT / "downloads" / "aligned_standard",
    "exclusive": REPO_ROOT / "downloads" / "aligned_exclusive",
}


# ---------------------------------------------------------------------------
# RTTM parsing
# ---------------------------------------------------------------------------

def load_rttm(rttm_path: Path) -> list[dict]:
    """Parse an RTTM file into a list of {start, end, speaker} dicts.

    RTTM format: SPEAKER <file-id> <chnl> <tbeg> <tdur> <ortho> <stype> <name> <conf> <slat>
    The file-id field may contain spaces (e.g. long video titles), so we index
    from the right where field positions are stable regardless of filename length.
    """
    entries = []
    with open(rttm_path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith(";"):
                continue
            parts = line.split()
            if len(parts) < 10 or parts[0] != "SPEAKER":
                continue
            # Count from right: [-7]=tbeg, [-6]=tdur, [-3]=name
            start = float(parts[-7])
            duration = float(parts[-6])
            speaker = parts[-3]
            entries.append({"start": start, "end": start + duration, "speaker": speaker})
    return entries


# ---------------------------------------------------------------------------
# Alignment
# ---------------------------------------------------------------------------

def overlap_duration(a_start: float, a_end: float, b_start: float, b_end: float) -> float:
    return max(0.0, min(a_end, b_end) - max(a_start, b_start))


def assign_speaker(seg_start: float, seg_end: float, rttm_entries: list[dict]) -> str:
    """Return the RTTM speaker with the most overlap with [seg_start, seg_end]."""
    best_speaker = "UNKNOWN"
    best_overlap = 0.0
    for entry in rttm_entries:
        # Quick range check to avoid scanning every entry
        if entry["end"] < seg_start or entry["start"] > seg_end:
            continue
        ov = overlap_duration(seg_start, seg_end, entry["start"], entry["end"])
        if ov > best_overlap:
            best_overlap = ov
            best_speaker = entry["speaker"]
    return best_speaker


def align_file(stem: str, rttm_mode: str, force: bool = False) -> bool:
    whisper_path = WHISPER_DIR / f"{stem}.json"
    rttm_path = RTTM_DIRS[rttm_mode] / f"{stem}.rttm"
    out_path = OUT_DIRS[rttm_mode] / f"{stem}.json"

    if not whisper_path.exists():
        print(f"  [{rttm_mode}] SKIP — whisper output not found: {whisper_path.name}")
        return False
    if not rttm_path.exists():
        print(f"  [{rttm_mode}] SKIP — RTTM not found: {rttm_path.name}")
        return False
    if out_path.exists() and not force:
        print(f"  [{rttm_mode}] Already done, skipping.")
        return False

    whisper_segments = json.loads(whisper_path.read_text(encoding="utf-8"))
    rttm_entries = load_rttm(rttm_path)

    # Assign speakers
    attributed = []
    for seg in whisper_segments:
        speaker = assign_speaker(seg["start"], seg["end"], rttm_entries)
        attributed.append({
            "start": seg["start"],
            "end": seg["end"],
            "text": seg["text"],
            "speaker": speaker,
        })

    # Build speaker summary
    speaker_data = defaultdict(lambda: {"total_speech_s": 0.0, "segment_count": 0, "word_count": 0})
    for seg in attributed:
        spk = seg["speaker"]
        speaker_data[spk]["total_speech_s"] += seg["end"] - seg["start"]
        speaker_data[spk]["segment_count"] += 1
        speaker_data[spk]["word_count"] += len(seg["text"].split())

    speaker_summary = {
        spk: {
            "total_speech_s": round(v["total_speech_s"], 1),
            "segment_count": v["segment_count"],
            "word_count": v["word_count"],
        }
        for spk, v in sorted(speaker_data.items())
    }

    out = {
        "file": stem,
        "rttm_mode": rttm_mode,
        "speaker_summary": speaker_summary,
        "segments": attributed,
    }

    OUT_DIRS[rttm_mode].mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")

    n_unknown = sum(1 for s in attributed if s["speaker"] == "UNKNOWN")
    print(f"  [{rttm_mode}] {len(attributed)} segments, "
          f"{len(speaker_summary)} speakers, "
          f"{n_unknown} unattributed -> {out_path.name}")
    return True


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def stems_from_input(input_arg) -> list[str]:
    if input_arg:
        p = Path(input_arg)
        if p.is_file():
            return [p.stem]
        elif p.is_dir():
            return sorted(f.stem for f in p.glob("*.m4a"))
        else:
            print(f"ERROR: --input path not found: {p}")
            sys.exit(1)
    # Default: all files that have whisper output
    if not WHISPER_DIR.exists():
        print(f"ERROR: whisper output directory not found: {WHISPER_DIR}")
        sys.exit(1)
    return sorted(f.stem for f in WHISPER_DIR.glob("*.json"))


def main():
    parser = argparse.ArgumentParser(
        description="Align whisper transcription to pyannote speaker labels"
    )
    parser.add_argument(
        "--input", "-i",
        help="Single .m4a file, or directory of .m4a files (default: all with whisper output)",
        default=None,
    )
    parser.add_argument(
        "--mode", "-m",
        choices=["standard", "exclusive", "both"],
        default="both",
        help="Which RTTM mode to align against (default: both)",
    )
    parser.add_argument(
        "--force", "-f",
        action="store_true",
        help="Overwrite existing output files instead of skipping",
    )
    args = parser.parse_args()

    stems = stems_from_input(args.input)
    if not stems:
        print("No files to process.")
        sys.exit(1)

    modes = ["standard", "exclusive"] if args.mode == "both" else [args.mode]
    print(f"Files to align: {len(stems)}")
    print(f"Modes: {', '.join(modes)}")

    total_start = time.perf_counter()
    n_done = n_skipped = n_errors = 0

    for stem in stems:
        print(f"\n[{now_str()}] {stem[:80]}...")
        t0 = time.perf_counter()
        stem_did_work = False
        for mode in modes:
            try:
                did_work = align_file(stem, mode, force=args.force)
                if did_work:
                    n_done += 1
                    stem_did_work = True
                else:
                    n_skipped += 1
            except Exception:
                print(f"  [{mode}] ERROR:")
                traceback.print_exc()
                n_errors += 1
        if stem_did_work:
            print(f"  Elapsed: {fmt_elapsed(time.perf_counter() - t0)}")

    total_elapsed = time.perf_counter() - total_start
    print(f"\nSummary: {n_done} aligned, {n_skipped} skipped, {n_errors} errors")
    print(f"Total time: {fmt_elapsed(total_elapsed)}")


if __name__ == "__main__":
    main()
