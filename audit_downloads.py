"""
Audit downloaded playlist artifacts; optionally re-fetch broken items.

For each video ID found in metadata/, this checks:
  - clean merged video file in videos/  (no '.fNNN.' format-ID suffix)
  - audio file in audio/                (size sanity-checked vs. duration)
  - at least one srt/vtt transcript in transcripts/

Usage:
    python audit_downloads.py --out <path>          # report only
    python audit_downloads.py --out <path> --fix    # re-fetch + re-extract
"""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass, field
from pathlib import Path

import yt_dlp

from download_playlist import (
    _audio_target_stem,
    _build_ydl_opts,
    _derive_audio_files,
)


VIDEO_EXTS = {".mp4", ".mkv", ".webm", ".mov", ".m4v"}
TRANSCRIPT_EXTS = {".srt", ".vtt"}

# AAC at 192 kbps is ~24 KB/s. Anything below 8 KB/s (~64 kbps) suggests a
# corrupt or near-empty audio file — flag it for re-extraction.
MIN_AUDIO_BYTES_PER_SECOND = 8_000

# Issues that block the downstream audio-transcription pipeline. Everything
# else is informational — e.g. missing merged video is fine when the audio
# was successfully extracted from a yt-dlp orphan, since the pipeline only
# consumes audio.
BLOCKING_ISSUES = {"NO_AUDIO", "SHORT_AUDIO"}

# Matches the 11-char YouTube ID bracketed in our filename convention.
ID_PATTERN = re.compile(r"\[([\w-]{11})\]")


@dataclass
class Audit:
    video_id: str
    title: str
    duration: float | None
    info_json: Path | None = None
    merged_video: Path | None = None
    orphans: list[Path] = field(default_factory=list)
    audio: Path | None = None
    transcripts: list[Path] = field(default_factory=list)
    issues: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        """No blocking issues — audio pipeline can proceed for this video."""
        return not any(i in BLOCKING_ISSUES for i in self.issues)

    @property
    def has_warnings(self) -> bool:
        return bool(self.issues) and self.ok


def _id_from_path(path: Path) -> str | None:
    m = ID_PATTERN.search(path.name)
    return m.group(1) if m else None


def _is_orphan_format_file(path: Path) -> bool:
    base, sep, fmt = path.stem.rpartition(".f")
    return bool(sep) and fmt.isdigit()


def _inventory(out_root: Path) -> dict[str, Audit]:
    metadata_dir = out_root / "metadata"
    video_dir = out_root / "videos"
    audio_dir = out_root / "audio"
    transcript_dir = out_root / "transcripts"

    audits: dict[str, Audit] = {}

    # metadata/ is the canonical "videos yt-dlp processed" — every successful
    # info-extract writes one of these even if the video download failed.
    if metadata_dir.exists():
        for info_file in sorted(metadata_dir.glob("*.info.json")):
            vid = _id_from_path(info_file)
            if not vid:
                continue
            try:
                meta = json.loads(info_file.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                meta = {}
            audits[vid] = Audit(
                video_id=vid,
                title=meta.get("title") or info_file.stem,
                duration=meta.get("duration"),
                info_json=info_file,
            )

    if video_dir.exists():
        for vfile in video_dir.iterdir():
            if not vfile.is_file() or vfile.suffix.lower() not in VIDEO_EXTS:
                continue
            vid = _id_from_path(vfile)
            if not vid or vid not in audits:
                continue
            if _is_orphan_format_file(vfile):
                audits[vid].orphans.append(vfile)
            else:
                audits[vid].merged_video = vfile

    if audio_dir.exists():
        for afile in audio_dir.iterdir():
            if not afile.is_file() or afile.suffix.lower() != ".m4a":
                continue
            vid = _id_from_path(afile)
            if vid and vid in audits:
                audits[vid].audio = afile

    if transcript_dir.exists():
        for tfile in transcript_dir.iterdir():
            if not tfile.is_file() or tfile.suffix.lower() not in TRANSCRIPT_EXTS:
                continue
            vid = _id_from_path(tfile)
            if vid and vid in audits:
                audits[vid].transcripts.append(tfile)

    return audits


def _classify(audits: dict[str, Audit]) -> None:
    for a in audits.values():
        if a.merged_video is None:
            a.issues.append("NO_MERGED_VIDEO")
        if a.orphans:
            a.issues.append("ORPHAN_FORMAT_FILES")
        if a.audio is None:
            a.issues.append("NO_AUDIO")
        elif a.duration:
            min_bytes = int(a.duration * MIN_AUDIO_BYTES_PER_SECOND)
            if a.audio.stat().st_size < min_bytes:
                a.issues.append("SHORT_AUDIO")
        if not a.transcripts:
            a.issues.append("NO_TRANSCRIPT")


def audit(out_root: Path) -> list[Audit]:
    audits = _inventory(out_root)
    _classify(audits)
    return sorted(audits.values(), key=lambda x: x.video_id)


def report(audits: list[Audit]) -> int:
    blocked = [a for a in audits if not a.ok]
    warned = [a for a in audits if a.has_warnings]
    clean = sum(1 for a in audits if not a.issues)
    print(
        f"\n=== Audit: {len(audits)} videos | {clean} clean | "
        f"{len(warned)} with warnings | {len(blocked)} blocked ===\n"
    )
    for a in blocked + warned:
        title = a.title if len(a.title) <= 78 else a.title[:75] + "..."
        marker = "BLOCKED" if not a.ok else "warn   "
        print(f"[{marker}] [{a.video_id}] {title}")
        for issue in a.issues:
            tag = "BLOCK" if issue in BLOCKING_ISSUES else "warn "
            print(f"    [{tag}] {issue}")
        for o in a.orphans:
            print(f"           orphan: {o.name}")
    if not blocked and not warned:
        print("All videos have a merged file, audio, and at least one transcript.")
    return len(blocked)


def _cleanup_misplaced(out_root: Path) -> None:
    """Sweep failed-merge artifacts out of videos/ and audio/.

    Each issue this fixes traces back to a yt-dlp run whose postprocessing
    step never finished (typically because the format-merge failed):

    * subtitles land in the home (videos) folder instead of the configured
      `subtitle` path
    * `*.info.json` for the playlist itself lands in home (we don't have a
      `pl_infojson` path configured for old downloads)
    * `[id].fNNN.{webm,mp4}` orphans pile up in videos/
    * `[id].fNNN.m4a` duplicates from earlier extractor runs (before the
      `_audio_target_stem` suffix-stripping logic) sit alongside the
      canonical `[id].m4a`

    `.part` files are intentionally left alone — yt-dlp resumes from them
    via HTTP Range requests on the next run, saving bandwidth on big
    streams. Orphan format files (.fNNN.webm, .fNNN.mp4) are only deleted
    when the canonical `[id].m4a` already exists in audio/, so we don't
    discard the only source the audio extractor could use.
    """
    video_dir = out_root / "videos"
    transcript_dir = out_root / "transcripts"
    audio_dir = out_root / "audio"
    metadata_dir = out_root / "metadata"
    if not video_dir.exists():
        return
    transcript_dir.mkdir(parents=True, exist_ok=True)
    metadata_dir.mkdir(parents=True, exist_ok=True)

    # Set of video IDs whose canonical (non-orphan) audio already exists.
    canonical_audio_ids: set[str] = set()
    if audio_dir.exists():
        for af in audio_dir.iterdir():
            if not (af.is_file() and af.suffix.lower() == ".m4a"):
                continue
            if _is_orphan_format_file(af):
                continue
            vid = _id_from_path(af)
            if vid:
                canonical_audio_ids.add(vid)

    moved_subs = 0
    deleted_dup_subs = 0
    moved_info = 0
    deleted_dup_info = 0
    deleted_orphans = 0
    deleted_audio_dups = 0

    for entry in video_dir.iterdir():
        if not entry.is_file():
            continue
        suffix = entry.suffix.lower()
        if suffix in TRANSCRIPT_EXTS:
            target = transcript_dir / entry.name
            if target.exists():
                entry.unlink()
                deleted_dup_subs += 1
            else:
                entry.rename(target)
                moved_subs += 1
        elif entry.name.endswith(".info.json"):
            target = metadata_dir / entry.name
            if target.exists():
                entry.unlink()
                deleted_dup_info += 1
            else:
                entry.rename(target)
                moved_info += 1
        elif suffix in VIDEO_EXTS and _is_orphan_format_file(entry):
            vid = _id_from_path(entry)
            if vid and vid in canonical_audio_ids:
                entry.unlink()
                deleted_orphans += 1

    if audio_dir.exists():
        for entry in audio_dir.iterdir():
            if not (entry.is_file() and entry.suffix.lower() == ".m4a"):
                continue
            if not _is_orphan_format_file(entry):
                continue
            vid = _id_from_path(entry)
            if vid and vid in canonical_audio_ids:
                entry.unlink()
                deleted_audio_dups += 1

    if moved_subs:
        print(f"  moved {moved_subs} misplaced transcript file(s) to transcripts/")
    if deleted_dup_subs:
        print(f"  deleted {deleted_dup_subs} duplicate transcript file(s) already present in transcripts/")
    if moved_info:
        print(f"  moved {moved_info} stray .info.json file(s) to metadata/")
    if deleted_dup_info:
        print(f"  deleted {deleted_dup_info} duplicate .info.json file(s) already present in metadata/")
    if deleted_orphans:
        print(f"  deleted {deleted_orphans} orphan .fNNN.* video file(s) (canonical audio already extracted)")
    if deleted_audio_dups:
        print(f"  deleted {deleted_audio_dups} stale .fNNN.m4a duplicate(s)")


def fix(out_root: Path, audits: list[Audit]) -> None:
    # Sub/.part cleanup may flip some "broken" items to OK on its own, so do
    # it first, then re-audit before deciding what needs re-downloading.
    _cleanup_misplaced(out_root)
    audits = audit(out_root)
    broken = [a for a in audits if not a.ok]
    if not broken:
        print("Nothing left to fix after cleanup.")
        return

    video_dir = out_root / "videos"
    audio_dir = out_root / "audio"
    transcript_dir = out_root / "transcripts"
    metadata_dir = out_root / "metadata"

    # Items that need yt-dlp to re-fetch: missing merged video, orphans on
    # disk (failed merge), or missing transcript.
    needs_redownload: list[str] = []
    # Items where everything yt-dlp produces is fine but the audio file is
    # missing/short — just need to re-run audio extraction.
    audio_only: list[str] = []

    for a in broken:
        # Wipe a suspect or absent audio file so re-extraction recreates it.
        if a.audio and ("SHORT_AUDIO" in a.issues):
            print(f"  removing short audio: {a.audio.name}")
            a.audio.unlink(missing_ok=True)
        # Wipe orphan format files so yt-dlp won't think the merge already
        # half-finished — fresh re-download produces a clean merged file.
        if "ORPHAN_FORMAT_FILES" in a.issues or "NO_MERGED_VIDEO" in a.issues:
            for o in a.orphans:
                print(f"  removing orphan: {o.name}")
                o.unlink(missing_ok=True)
            needs_redownload.append(a.video_id)
        elif "NO_TRANSCRIPT" in a.issues:
            needs_redownload.append(a.video_id)
        elif "NO_AUDIO" in a.issues or "SHORT_AUDIO" in a.issues:
            audio_only.append(a.video_id)

    if needs_redownload:
        print(f"\nRe-running yt-dlp for {len(needs_redownload)} item(s)...")
        urls = [f"https://www.youtube.com/watch?v={vid}" for vid in needs_redownload]
        opts = _build_ydl_opts(video_dir, transcript_dir, metadata_dir)
        with yt_dlp.YoutubeDL(opts) as ydl:
            ydl.download(urls)

    if needs_redownload or audio_only:
        # _derive_audio_files iterates everything in videos/ but cheaply skips
        # files whose .m4a already exists, so this is effectively scoped to
        # videos whose audio we just removed or never had.
        print("\nRe-extracting audio where needed...")
        _derive_audio_files(video_dir, audio_dir)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Audit downloaded playlist artifacts; optionally re-fetch broken items."
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=Path.cwd() / "downloads",
        help="output root directory (default: ./downloads relative to cwd)",
    )
    parser.add_argument(
        "--fix",
        action="store_true",
        help="re-download missing/orphaned items and re-extract audio",
    )
    args = parser.parse_args()
    out_root = args.out.resolve()

    audits = audit(out_root)
    report(audits)

    # Always run --fix regardless of whether anything is *blocked* — the
    # cleanup pass scrubs cosmetic warnings (misplaced subs, orphan format
    # files, stale .fNNN duplicates) that don't count as blocking but still
    # leave the dataset cluttered.
    if args.fix:
        fix(out_root, audits)
        print("\n--- post-fix audit ---")
        report(audit(out_root))


if __name__ == "__main__":
    main()