"""
For each video in the filtered council list, copy the full transcript
from grouped_standard and grouped_exclusive to downloads/comments/.

Output naming:
  - If standard == exclusive:  [title] [id].json
  - If they differ:            [title] [id]_standard.json
                               [title] [id]_exclusive.json
"""

import json
import glob
import os

METADATA_DIR   = r"C:\Users\Admin\PycharmProjects\hands_on_dl\downloads\metadata"
STANDARD_DIR   = r"C:\Users\Admin\PycharmProjects\hands_on_dl\downloads\grouped_standard"
EXCLUSIVE_DIR  = r"C:\Users\Admin\PycharmProjects\hands_on_dl\downloads\grouped_exclusive"
OUTPUT_DIR     = r"C:\Users\Admin\PycharmProjects\hands_on_dl\downloads\comments"

TARGET_CHANNEL_ID = "UCBuExvyMYDwZoQwbhldXwvg"
DATE_START = "20250722"
DATE_END   = "20251201"


def load_json(path: str) -> dict | None:
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"  Could not load {os.path.basename(path)}: {e}")
        return None


def extract_commenter_data(grouped: dict) -> dict:
    """Return all speakers and blocks from the grouped transcript."""
    return {
        "speakers": grouped["speaker_classification"],
        "blocks": grouped["blocks"],
    }


def get_video_list() -> list[tuple[str, str, str]]:
    """Return list of (upload_date, title, video_id) for the target channel and date range."""
    files = glob.glob(os.path.join(METADATA_DIR, "*.info.json"))
    results = []
    for path in files:
        data = load_json(path)
        if data is None:
            continue
        if data.get("channel_id") != TARGET_CHANNEL_ID:
            continue
        upload_date = data.get("upload_date", "")
        if not (DATE_START <= upload_date <= DATE_END):
            continue
        results.append((upload_date, data.get("title", ""), data.get("id", "")))
    results.sort(key=lambda x: x[0])
    return results


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    videos = get_video_list()
    print(f"Processing {len(videos)} videos...\n")

    for upload_date, title, video_id in videos:
        filename = f"{title} [{video_id}].json"
        std_path  = os.path.join(STANDARD_DIR,  filename)
        excl_path = os.path.join(EXCLUSIVE_DIR, filename)

        std_raw  = load_json(std_path)  if os.path.exists(std_path)  else None
        excl_raw = load_json(excl_path) if os.path.exists(excl_path) else None

        if std_raw is None and excl_raw is None:
            print(f"  SKIP {title}: no grouped files found")
            continue

        std_data  = extract_commenter_data(std_raw)  if std_raw  else None
        excl_data = extract_commenter_data(excl_raw) if excl_raw else None

        base_name = f"{title} [{video_id}]"

        if std_data is not None and excl_data is not None:
            if std_data["blocks"] == excl_data["blocks"]:
                # Identical — write once, note both modes agree
                out = {
                    "title": title,
                    "video_id": video_id,
                    "upload_date": upload_date,
                    "rttm_modes": "standard=exclusive",
                    **std_data,
                }
                out_path = os.path.join(OUTPUT_DIR, f"{base_name}.json")
                with open(out_path, "w", encoding="utf-8") as f:
                    json.dump(out, f, indent=2, ensure_ascii=False)
                n = len(std_data["blocks"])
                print(f"  [SAME]  {base_name}  ({n} blocks)")
            else:
                # Differ — write two files
                for mode, data in [("standard", std_data), ("exclusive", excl_data)]:
                    out = {
                        "title": title,
                        "video_id": video_id,
                        "upload_date": upload_date,
                        "rttm_mode": mode,
                        **data,
                    }
                    out_path = os.path.join(OUTPUT_DIR, f"{base_name}_{mode}.json")
                    with open(out_path, "w", encoding="utf-8") as f:
                        json.dump(out, f, indent=2, ensure_ascii=False)
                ns = len(std_data["blocks"])
                ne = len(excl_data["blocks"])
                print(f"  [DIFF]  {base_name}  (std={ns} blocks, excl={ne} blocks)")
        else:
            # Only one mode available
            data, mode = (std_data, "standard") if std_data else (excl_data, "exclusive")
            out = {
                "title": title,
                "video_id": video_id,
                "upload_date": upload_date,
                "rttm_mode": mode,
                **data,
            }
            out_path = os.path.join(OUTPUT_DIR, f"{base_name}_{mode}.json")
            with open(out_path, "w", encoding="utf-8") as f:
                json.dump(out, f, indent=2, ensure_ascii=False)
            n = len(data["blocks"])
            print(f"  [{mode.upper()[:4]}]  {base_name}  ({n} blocks, only this mode found)")

    print(f"\nDone. Output in: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()