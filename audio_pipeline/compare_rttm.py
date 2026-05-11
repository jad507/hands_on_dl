"""
compare_rttm.py — LLM-assisted comparison of standard vs exclusive diarization.

STUB — not yet implemented. Requires a local LLM (e.g., Llama 3 8B via Ollama/vLLM).

Planned workflow:
  1. Load <stem>_stats.json from both standard and exclusive output folders
  2. Load both .rttm files
  3. Query local LLM: "Where do these diarizations disagree? Flag contested-floor events."
  4. Write a human-readable comparison report per audio file

Run:
  python audio_pipeline/compare_rttm.py --stem "Lancaster City Council Meeting, Monday, ..."
  python audio_pipeline/compare_rttm.py --all    # compare all files with outputs in both folders
"""

import argparse
import json
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
STD_DIR = REPO_ROOT / "downloads" / "pyannote_community-1_standard"
EXC_DIR = REPO_ROOT / "downloads" / "pyannote_community-1_exclusive"


def quick_stats_compare(stem: str):
    """Print a quick side-by-side stats summary without an LLM."""
    std_stats_path = STD_DIR / f"{stem}_stats.json"
    exc_stats_path = EXC_DIR / f"{stem}_stats.json"

    if not std_stats_path.exists():
        print(f"No standard stats found: {std_stats_path}")
        return
    if not exc_stats_path.exists():
        print(f"No exclusive stats found: {exc_stats_path}")
        return

    std = json.loads(std_stats_path.read_text())
    exc = json.loads(exc_stats_path.read_text())

    print(f"\n{'='*60}")
    print(f"File: {stem}")
    print(f"{'='*60}")
    print(f"{'':30} {'standard':>12} {'exclusive':>12}")
    print(f"{'Speaker count':30} {std['speaker_count']:>12} {exc['speaker_count']:>12}")
    print(f"{'Total speech (s)':30} {std['total_speech_duration_s']:>12.1f} {exc['total_speech_duration_s']:>12.1f}")
    print(f"{'Overlap (s)':30} {std['overlap_duration_s']:>12.1f} {'N/A':>12}")

    std_speakers = set(std.get("speakers", {}).keys())
    exc_speakers = set(exc.get("speakers", {}).keys())
    if std_speakers != exc_speakers:
        print(f"\nSpeaker label differences:")
        print(f"  In standard only: {std_speakers - exc_speakers}")
        print(f"  In exclusive only: {exc_speakers - std_speakers}")


def list_available_stems():
    if not STD_DIR.exists():
        return []
    return [p.stem for p in STD_DIR.glob("*.rttm")]


def main():
    parser = argparse.ArgumentParser(
        description="Compare standard vs exclusive diarization outputs"
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--stem", help="Audio file stem (filename without extension)")
    group.add_argument("--all", action="store_true", help="Compare all available files")
    args = parser.parse_args()

    print("NOTE: LLM-assisted comparison not yet implemented.")
    print("Showing quick stats comparison only.\n")

    if args.all:
        stems = list_available_stems()
        if not stems:
            print(f"No diarization output found in {STD_DIR}")
            return
        for stem in sorted(stems):
            quick_stats_compare(stem)
    else:
        quick_stats_compare(args.stem)

    print("\nFor LLM-assisted analysis: implement local LLM query in this script")
    print("once Ollama or vLLM is running.")


if __name__ == "__main__":
    main()