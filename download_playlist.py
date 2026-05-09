"""
Download a YouTube playlist into four parallel folders:

    downloads/videos/      -- full merged mp4
    downloads/audio/       -- audio-only m4a (derived from the saved video)
    downloads/transcripts/ -- YouTube auto-captions (srt/vtt)
    downloads/metadata/    -- yt-dlp .info.json (title, uploader, chapters, etc.)

Every artifact for a given video shares the same base filename
("<title> [<video_id>]") so you can join them downstream.

Filtering is by upload date — only videos published in the configured
window are downloaded. Tweak DATE_AFTER / DATE_BEFORE below.

Setup:
    pip install yt-dlp           # already in requirements.txt
    # ffmpeg must be on PATH (used for audio extraction)
"""

from __future__ import annotations

import argparse
import subprocess
from pathlib import Path

import yt_dlp
from yt_dlp.utils import DateRange


PLAYLIST_URL = "https://www.youtube.com/playlist?list=PLUQII5r8C6geSA2Dqrq783Si0H2ULsQya"

# Upload-date window. yt-dlp accepts either "YYYYMMDD" or relative forms like
# "today-2years", "now-18months", "today-30days". Set either to None to leave
# that side of the window open.
DATE_AFTER: str | None = "today-2years"
DATE_BEFORE: str | None = None

# Truncate long titles so Windows path limits don't bite. The [id] suffix
# keeps filenames unique even if two titles collide after truncation.
OUTTMPL = "%(title).180B [%(id)s].%(ext)s"


def _build_ydl_opts(video_dir: Path, transcript_dir: Path, metadata_dir: Path) -> dict:
    opts: dict = {
        "paths": {
            "home": str(video_dir),
            "subtitle": str(transcript_dir),
            "infojson": str(metadata_dir),
        },
        "outtmpl": {"default": OUTTMPL},
        "format": "bestvideo*+bestaudio/best",
        "merge_output_format": "mp4",
        "writesubtitles": True,
        "writeautomaticsub": True,
        "subtitleslangs": ["en.*", "en"],
        "subtitlesformat": "srt/vtt/best",
        "writeinfojson": True,
        "ignoreerrors": True,
        "postprocessors": [
            {"key": "FFmpegSubtitlesConvertor", "format": "srt"},
        ],
    }
    if DATE_AFTER or DATE_BEFORE:
        # DateRange's runtime accepts "YYYYMMDD" or relative strings like
        # "today-2years"; the type stub claims it only takes `date` objects.
        opts["daterange"] = DateRange(DATE_AFTER, DATE_BEFORE)  # type: ignore[arg-type]
    return opts


def _extract_audio(video_path: Path, audio_path: Path) -> None:
    audio_path.parent.mkdir(parents=True, exist_ok=True)
    copy_cmd = [
        "ffmpeg", "-y", "-loglevel", "error",
        "-i", str(video_path),
        "-vn", "-acodec", "copy",
        str(audio_path),
    ]
    if subprocess.run(copy_cmd).returncode == 0:
        return
    # Fall back to AAC re-encode if the source codec isn't .m4a-compatible.
    encode_cmd = [
        "ffmpeg", "-y", "-loglevel", "error",
        "-i", str(video_path),
        "-vn", "-c:a", "aac", "-b:a", "192k",
        str(audio_path),
    ]
    subprocess.run(encode_cmd, check=True)


def _derive_audio_files(video_dir: Path, audio_dir: Path) -> None:
    video_exts = {".mp4", ".mkv", ".webm", ".mov", ".m4v"}
    for video_file in sorted(video_dir.iterdir()):
        if not video_file.is_file() or video_file.suffix.lower() not in video_exts:
            continue
        audio_file = audio_dir / f"{video_file.stem}.m4a"
        if audio_file.exists():
            continue
        print(f"[audio] {video_file.name} -> {audio_file.name}")
        _extract_audio(video_file, audio_file)


def main(out_root: Path) -> None:
    video_dir = out_root / "videos"
    audio_dir = out_root / "audio"
    transcript_dir = out_root / "transcripts"
    metadata_dir = out_root / "metadata"
    for d in (video_dir, audio_dir, transcript_dir, metadata_dir):
        d.mkdir(parents=True, exist_ok=True)

    with yt_dlp.YoutubeDL(_build_ydl_opts(video_dir, transcript_dir, metadata_dir)) as ydl:
        ydl.download([PLAYLIST_URL])

    _derive_audio_files(video_dir, audio_dir)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Download a YouTube playlist into video/audio/transcript/metadata folders."
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=Path.cwd() / "downloads",
        help="output root directory (default: ./downloads relative to cwd)",
    )
    args = parser.parse_args()
    main(args.out.resolve())