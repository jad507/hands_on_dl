"""
Filter City Council videos by channel and upload date range, sorted oldest-first.
Output is written to a text file (one title per line).
"""

import argparse
import json
from pathlib import Path

# Assume the script is run from the project root (hands_on_dl).
PROJECT_ROOT = Path.cwd()
METADATA_DIR = PROJECT_ROOT / "downloads" / "metadata"
OUTPUT_FILE = PROJECT_ROOT / "council_video_list.txt"

# Stable channel ID for "City of Lancaster, PA"
TARGET_CHANNEL_ID = "UCBuExvyMYDwZoQwbhldXwvg"

# Dates in YYYYMMDD format (same format used in the metadata upload_date field)
DATE_START = "20250201"
DATE_END   = "20251201"


def load_metadata(path: Path) -> dict | None:
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"  Skipping {path.name}: {e}")
        return None


def main():
    parser = argparse.ArgumentParser(description="Filter council videos by channel and date range.")
    parser.add_argument("--include-id", action="store_true",
                        help="Append [YouTubeID] to each title (matches transcript/diarization filenames)")
    args = parser.parse_args()

    files = list(METADATA_DIR.glob("*.info.json"))
    print(f"Scanning {len(files)} metadata files...")

    matches = []
    for path in files:
        data = load_metadata(path)
        if data is None:
            continue

        channel_id  = data.get("channel_id", "")
        upload_date = data.get("upload_date", "")
        title       = data.get("title", path.name)
        video_id    = data.get("id", "")

        if channel_id != TARGET_CHANNEL_ID:
            continue
        if not (DATE_START <= upload_date <= DATE_END):
            continue

        label = f"{title} [{video_id}]" if args.include_id else title
        matches.append((upload_date, label))

    matches.sort(key=lambda x: x[0])  # oldest first

    print(f"\nFound {len(matches)} videos in range {DATE_START}–{DATE_END}:\n")
    for upload_date, label in matches:
        print(f"  {upload_date}  {label}")

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        for upload_date, label in matches:
            f.write(f"{upload_date}  {label}\n")

    print(f"\nWrote {len(matches)} entries to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()