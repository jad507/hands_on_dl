r"""
Export `downloads/comments/*.json` blocks as WebVTT for Concord.

This is Step 5.1 of `AITranscribe/docs/isls2027/05-hands-on-dl-upgrade-plan.md`.
The contract comes from doc 03's reading of Concord's `server/ingest/transcript.js`,
and every constraint below was re-verified against the checkout at
`../concord` rather than taken on trust.

What Concord does to what we send it
------------------------------------
`parseVTT` -> `cueSpeakerText` -> `stripTags` -> `mergeCues`, then `unitize`.

1. **Voice tags.** `<v SPEAKER_00>text` is recognised by
   `/^<v(?:\.[^ >]*)?\s+([^>]+)>\s*([\s\S]*)$/`. The closing `</v>` is optional
   and stripped if present. This is the form used here.

2. **`stripTags` deletes everything else in angle brackets**, with no error and
   no issue logged: `s.replace(/<[^>]*>/g, "")`. Block text containing `<` or
   `>` would therefore lose an arbitrary span. This exporter replaces them with
   the fullwidth forms so nothing vanishes silently, and counts how often it had
   to.

3. **`mergeCues` fuses consecutive same-speaker cues when `gap <=
   maxMergeGapSeconds`**, default 30 s. Our blocks are already grouped turns, so
   any merging here re-negotiates unit boundaries the pipeline had already
   fixed -- which is the one thing this study cannot allow, since N is the
   denominator of every rate it reports.

   Note the comparison is `<=`, not `<`. **`maxMergeGapSeconds = 0` does not
   disable merging**: two adjacent cues with a gap of exactly 0 still merge. The
   only value that guarantees no merging is negative. This exporter emits the
   required setting in its manifest and refuses to stay quiet about it.

   Measured on this corpus: 23 same-speaker-adjacent block pairs out of 9,991
   (0.2%), of which 11 would merge at Concord's default of 30.

4. **Speaker labels** must satisfy `/^([A-Z][\w .'-]{0,40}?)$/` for the prefix
   form. The voice-tag form is more permissive, but a label that fails the
   prefix pattern is a portability hazard, so it is validated anyway.
   `SPEAKER_00` passes; `speaker_00` does not.

5. **Unitization scheme.** Doc 03 finding 1 says to use `scheme: "turn"` for the
   primary analysis, because `"sentence"` makes N a function of the punctuation
   the transcription policy chose. This exporter emits one cue per block, so
   `"turn"` reproduces the block spine exactly.

The manifest
------------
Unit ids in Concord are SHA-256 of the unit text, so they change whenever the
transcription policy changes and cannot be the join key across conditions
(doc 03 finding 3, demonstrated in `tests/test_concord_markers.py`). What
survives is the time anchor. `<stem>.manifest.json` records, per cue, the
`block_id`, speaker, start and end -- so a Concord unit can be mapped back to
the block it came from via `pos.t0` / `pos.speaker`, and `blockmatch.py` can
join across conditions.

Usage
-----
    python export_vtt.py                        # whole corpus
    python export_vtt.py --meeting "HARB*"      # glob
    python export_vtt.py --out downloads/vtt --verify
"""

from __future__ import annotations

import argparse
import fnmatch
import json
import re
import subprocess
import sys
from pathlib import Path

import paths

# Concord's SPEAKER_PREFIX, which the label must satisfy to be portable across
# both attribution forms.
SPEAKER_OK = re.compile(r"^[A-Z][\w .'-]{0,40}$")

# Value that actually disables merging. Not 0: mergeCues tests `gap <= max`.
NO_MERGE_GAP_SECONDS = -1


def fmt_timestamp(seconds: float) -> str:
    """HH:MM:SS.mmm, which `toSeconds` parses. Hours capped at three digits."""
    if seconds < 0:
        seconds = 0.0
    ms = int(round(seconds * 1000))
    h, rem = divmod(ms, 3_600_000)
    m, rem = divmod(rem, 60_000)
    s, ms = divmod(rem, 1000)
    return f"{h:02d}:{m:02d}:{s:02d}.{ms:03d}"


def sanitize(text: str) -> tuple[str, int]:
    """Make text safe for `stripTags`.

    Angle brackets are replaced with their fullwidth equivalents rather than
    escaped or dropped. HTML entities would not help -- stripTags runs on the
    raw string and `&lt;` is not what it looks for -- and dropping the character
    loses information the transcript deliberately recorded. Returns the text and
    how many substitutions were needed.
    """
    n = text.count("<") + text.count(">")
    if n:
        text = text.replace("<", "＜").replace(">", "＞")
    return text, n


def load_blocks(path: Path) -> tuple[dict, list[dict]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    blocks = data.get("blocks") or data.get("commenter_blocks") or []
    return data, blocks


def build_vtt(blocks: list[dict], title: str | None = None
              ) -> tuple[str, list[dict], dict]:
    """Return (vtt_text, manifest_rows, stats)."""
    lines = ["WEBVTT", ""]
    if title:
        # NOTE blocks are skipped by parseVTT (`/^(NOTE|STYLE|REGION)\b/`), so
        # this is a free place to keep the provenance a human needs when
        # opening the file, without reaching the parser.
        lines += [f"NOTE {title}", ""]

    manifest: list[dict] = []
    bad_speakers: set[str] = set()
    n_escaped = 0
    n_empty = 0

    for i, b in enumerate(blocks, start=1):
        text = (b.get("text") or "").strip()
        if not text:
            n_empty += 1
            continue                      # Concord drops empty cues anyway
        speaker = str(b.get("speaker") or "Speaker")
        if not SPEAKER_OK.match(speaker):
            bad_speakers.add(speaker)
        text, esc = sanitize(text)
        n_escaped += esc

        t0, t1 = float(b["start"]), float(b["end"])
        lines += [
            str(i),
            f"{fmt_timestamp(t0)} --> {fmt_timestamp(t1)}",
            f"<v {speaker}>{text}",
            "",
        ]
        manifest.append({
            "cue": i,
            "block_id": b.get("block_id"),
            "speaker": speaker,
            "start": t0,
            "end": t1,
            "category": b.get("category"),
            "word_count": b.get("word_count"),
        })

    # Same-speaker adjacency: the pairs Concord could fuse.
    at_risk = []
    for a, b in zip(manifest, manifest[1:]):
        if a["speaker"] == b["speaker"]:
            at_risk.append({"after_cue": a["cue"], "gap_s": round(b["start"] - a["end"], 3)})

    stats = {
        "n_blocks": len(blocks),
        "n_cues": len(manifest),
        "n_empty_skipped": n_empty,
        "n_angle_brackets_escaped": n_escaped,
        "invalid_speaker_labels": sorted(bad_speakers),
        "same_speaker_adjacent_pairs": at_risk,
        "would_merge_at_concord_default_30s": sum(
            1 for p in at_risk if p["gap_s"] <= 30),
        "required_max_merge_gap_seconds": NO_MERGE_GAP_SECONDS,
    }
    return "\n".join(lines), manifest, stats


def export_one(src: Path, out_dir: Path) -> dict:
    data, blocks = load_blocks(src)
    title = data.get("title")
    vtt, manifest, stats = build_vtt(blocks, title)

    out_dir.mkdir(parents=True, exist_ok=True)
    vtt_path = out_dir / f"{src.stem}.vtt"
    vtt_path.write_text(vtt, encoding="utf-8")
    (out_dir / f"{src.stem}.manifest.json").write_text(
        json.dumps({
            "source": src.name,
            "title": title,
            "video_id": data.get("video_id"),
            "rttm_mode": data.get("rttm_mode") or data.get("rttm_modes"),
            "concord_import": {
                "scheme": "turn",
                "maxMergeGapSeconds": NO_MERGE_GAP_SECONDS,
                "why": ("mergeCues tests `gap <= maxMergeGapSeconds`, so 0 still "
                        "merges adjacent cues. A negative value is the only one "
                        "that preserves the block spine."),
            },
            "stats": stats,
            "cues": manifest,
        }, indent=2, ensure_ascii=False),
        encoding="utf-8")
    stats["vtt"] = str(vtt_path)
    stats["meeting"] = src.stem
    return stats


def verify(out_dir: Path, concord_root: Path) -> list[dict]:
    """Round-trip every exported VTT through Concord and check N is preserved.

    The point is not that the VTT is well-formed -- it is that the number of
    turns Concord produces equals the number of blocks we sent. Anything else
    means unit boundaries moved during import, silently.
    """
    probe = Path(__file__).resolve().parent / "tools" / "concord_roundtrip.mjs"
    vtts = sorted(out_dir.glob("*.vtt"))
    if not vtts:
        return []
    r = subprocess.run(
        ["node", str(probe), str(concord_root), str(out_dir)],
        capture_output=True, text=True, timeout=600)
    if r.returncode != 0:
        print(f"verification failed:\n{r.stderr[-3000:]}", file=sys.stderr)
        return []
    return json.loads(r.stdout)


def main() -> None:
    ap = argparse.ArgumentParser(description="Export block JSON as WebVTT for Concord.")
    ap.add_argument("--comments", default=None)
    ap.add_argument("--out", default=None)
    ap.add_argument("--meeting", default=None,
                    help="glob to restrict which meetings are exported")
    ap.add_argument("--verify", action="store_true",
                    help="round-trip through Concord and check turn counts match")
    ap.add_argument("--concord", default=None)
    args = ap.parse_args()

    comments = Path(args.comments) if args.comments else paths.COMMENTS_DIR
    out_dir = Path(args.out) if args.out else paths.DOWNLOADS_DIR / "vtt"
    concord = Path(args.concord) if args.concord else paths.REPO_ROOT.parent / "concord"

    srcs = sorted(comments.glob("*.json"))
    if args.meeting:
        srcs = [p for p in srcs if fnmatch.fnmatch(p.stem, args.meeting)]
    if not srcs:
        sys.exit(f"no meetings matched in {comments}")

    print(f"exporting {len(srcs)} meetings to {out_dir}\n")
    all_stats = [export_one(p, out_dir) for p in srcs]

    tot_cues = sum(s["n_cues"] for s in all_stats)
    tot_esc = sum(s["n_angle_brackets_escaped"] for s in all_stats)
    tot_empty = sum(s["n_empty_skipped"] for s in all_stats)
    risk = sum(s["would_merge_at_concord_default_30s"] for s in all_stats)
    bad = sorted({sp for s in all_stats for sp in s["invalid_speaker_labels"]})

    print(f"  cues written                       : {tot_cues}")
    print(f"  empty blocks skipped               : {tot_empty}")
    print(f"  angle brackets escaped             : {tot_esc}")
    print(f"  speaker labels Concord would reject: {len(bad)} {bad[:5]}")
    print(f"  pairs that would MERGE at default  : {risk}")
    print()
    print(f"  Import with maxMergeGapSeconds = {NO_MERGE_GAP_SECONDS} and scheme "
          f'"turn".')
    print("  0 is NOT safe: mergeCues tests `gap <= maxMergeGapSeconds`.")

    if args.verify:
        print("\nverifying round-trip through Concord ...")
        results = verify(out_dir, concord)
        if not results:
            print("  (verification did not run)")
            return
        bad_rt = [r for r in results if not r.get("ok")]
        print(f"  {len(results) - len(bad_rt)}/{len(results)} meetings preserved "
              f"their turn count exactly")
        for r in bad_rt[:10]:
            print(f"  MISMATCH {r['file']}: sent {r.get('expected')} "
                  f"cues, Concord produced {r.get('turns')} turns")


if __name__ == "__main__":
    main()
