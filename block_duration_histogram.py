"""
Histogram of speech block durations across the filtered council video list.
Useful for deciding duration-based cutoffs as a proxy for public commenter blocks.
"""

import json
import glob
import os

METADATA_DIR  = r"C:\Users\Admin\PycharmProjects\hands_on_dl\downloads\metadata"
STANDARD_DIR  = r"C:\Users\Admin\PycharmProjects\hands_on_dl\downloads\grouped_standard"
OUTPUT_FILE   = r"C:\Users\Admin\PycharmProjects\hands_on_dl\block_duration_histogram.txt"

TARGET_CHANNEL_ID = "UCBuExvyMYDwZoQwbhldXwvg"
DATE_START = "20250722"
DATE_END   = "20251201"

# Cutoff to highlight (seconds). 300 = 5 minutes.
CUTOFF_S = 300

BUCKETS = [
    (0,    30,   "0-30s"),
    (30,   60,   "30-60s"),
    (60,   120,  "1-2min"),
    (120,  180,  "2-3min"),
    (180,  240,  "3-4min"),
    (240,  300,  "4-5min"),
    (300,  600,  "5-10min"),
    (600,  1200, "10-20min"),
    (1200, 99999,"20min+"),
]


def get_video_list() -> list[tuple[str, str, str]]:
    results = []
    for path in glob.glob(os.path.join(METADATA_DIR, "*.info.json")):
        with open(path, encoding="utf-8") as f:
            d = json.load(f)
        if d.get("channel_id") != TARGET_CHANNEL_ID:
            continue
        ud = d.get("upload_date", "")
        if not (DATE_START <= ud <= DATE_END):
            continue
        results.append((ud, d.get("title", ""), d.get("id", "")))
    results.sort(key=lambda x: x[0])
    return results


def main():
    videos = get_video_list()
    print(f"Scanning {len(videos)} videos...")

    durations = []
    missing = []
    for _, title, vid_id in videos:
        path = os.path.join(STANDARD_DIR, f"{title} [{vid_id}].json")
        if not os.path.exists(path):
            missing.append(f"{title} [{vid_id}]")
            continue
        with open(path, encoding="utf-8") as f:
            d = json.load(f)
        for b in d["blocks"]:
            durations.append(b["duration_s"])

    if missing:
        print(f"  Missing grouped_standard files ({len(missing)}):")
        for m in missing:
            print(f"    {m}")

    total = len(durations)
    if total == 0:
        print("No blocks found.")
        return

    lines = []
    lines.append(f"Block duration histogram — {len(videos)} videos, {total} blocks")
    lines.append(f"Date range: {DATE_START}–{DATE_END}  |  Channel: {TARGET_CHANNEL_ID}")
    lines.append("")

    bar_scale = max(1, max(
        sum(1 for d in durations if lo <= d < hi) for lo, hi, _ in BUCKETS
    ) // 60)

    for lo, hi, label in BUCKETS:
        count = sum(1 for d in durations if lo <= d < hi)
        bar = "#" * (count // bar_scale)
        marker = "  <- cutoff" if lo == CUTOFF_S else ""
        lines.append(f"  {label:>8}  {count:4d}  {count/total*100:5.1f}%  {bar}{marker}")

    lines.append("")
    under = sum(1 for d in durations if d < CUTOFF_S)
    over  = sum(1 for d in durations if d >= CUTOFF_S)
    lines.append(f"  Under {CUTOFF_S//60} min: {under} blocks ({under/total*100:.1f}%)")
    lines.append(f"  {CUTOFF_S//60} min+:     {over} blocks ({over/total*100:.1f}%)")
    lines.append(f"  Total:        {total}")
    lines.append(f"  Longest:      {max(durations)/60:.1f} min")
    lines.append(f"  Median:       {sorted(durations)[total//2]:.1f}s")

    output = "\n".join(lines)
    print("\n" + output)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(output + "\n")
    print(f"\nWrote to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
