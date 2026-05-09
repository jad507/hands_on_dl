"""
Download a YouTube playlist into four parallel folders:

    downloads/videos/      -- full merged mp4
    downloads/audio/       -- audio-only m4a (derived from the saved video)
    downloads/transcripts/ -- YouTube auto-captions (srt/vtt)
    downloads/metadata/    -- yt-dlp .info.json (title, uploader, chapters, etc.)

Every artifact for a given video shares the same base filename
("<title> [<video_id>]") so you can join them downstream.

Configure per-video time ranges in TIME_RANGES below to grab only the
segments you care about (e.g. just the public-comment portion of a long
meeting). Videos not listed in TIME_RANGES are downloaded in full;
mapping a video ID to [] skips it entirely.

Setup:
    pip install yt-dlp           # already in requirements.txt
    # ffmpeg must be on PATH (used for clip cuts and audio extraction)
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import yt_dlp


PLAYLIST_URL = "https://www.youtube.com/playlist?list=PLUQII5r8C6geSA2Dqrq783Si0H2ULsQya"

# Per-video clip ranges in seconds. Key is the 11-character YouTube video ID
# (run `yt-dlp --flat-playlist <PLAYLIST_URL>` once to list them). Each value
# is a list of (start, end) tuples; multiple tuples produce multiple clips
# concatenated into one output file.
#
#   TIME_RANGES = {
#       "dQw4w9WgXcQ": [(120, 480), (1800, 2400)],  # two clips from this video
#       "abcdefghijk": [],                          # skip entirely
#   }
TIME_RANGES: dict[str, list[tuple[float, float]]] = {
}

OUTPUT_ROOT = Path(__file__).resolve().parent / "downloads"
VIDEO_DIR = OUTPUT_ROOT / "videos"
AUDIO_DIR = OUTPUT_ROOT / "audio"
TRANSCRIPT_DIR = OUTPUT_ROOT / "transcripts"
METADATA_DIR = OUTPUT_ROOT / "metadata"

# Truncate long titles so Windows path limits don't bite. The [id] suffix
# keeps filenames unique even if two titles collide after truncation.
OUTTMPL = "%(title).180B [%(id)s].%(ext)s"


def _download_ranges(info_dict, ydl):
    """yt-dlp callback: returns the time ranges to keep for a given video."""
    video_id = info_dict.get("id")
    ranges = TIME_RANGES.get(video_id)
    if ranges is None:
        return [{"start_time": 0, "end_time": info_dict.get("duration") or 0}]
    if not ranges:
        return []
    return [{"start_time": float(s), "end_time": float(e)} for s, e in ranges]


def _build_ydl_opts() -> dict:
    return {
        "paths": {
            "home": str(VIDEO_DIR),
            "subtitle": str(TRANSCRIPT_DIR),
            "infojson": str(METADATA_DIR),
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
        "download_ranges": _download_ranges,
        "postprocessors": [
            {"key": "FFmpegSubtitlesConvertor", "format": "srt"},
        ],
    }


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


def _derive_audio_files() -> None:
    video_exts = {".mp4", ".mkv", ".webm", ".mov", ".m4v"}
    for video_file in sorted(VIDEO_DIR.iterdir()):
        if not video_file.is_file() or video_file.suffix.lower() not in video_exts:
            continue
        audio_file = AUDIO_DIR / f"{video_file.stem}.m4a"
        if audio_file.exists():
            continue
        print(f"[audio] {video_file.name} -> {audio_file.name}")
        _extract_audio(video_file, audio_file)


def main() -> None:
    for d in (VIDEO_DIR, AUDIO_DIR, TRANSCRIPT_DIR, METADATA_DIR):
        d.mkdir(parents=True, exist_ok=True)

    with yt_dlp.YoutubeDL(_build_ydl_opts()) as ydl:
        ydl.download([PLAYLIST_URL])

    _derive_audio_files()


if __name__ == "__main__":
    main()