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

import os

import yt_dlp
from yt_dlp.utils import DateRange


# PLAYLIST_URL = "https://www.youtube.com/playlist?list=PLUQII5r8C6geSA2Dqrq783Si0H2ULsQya"
# PLAYLIST_URL = "https://www.youtube.com/playlist?list=PLjp6mGyg8T3wT7o-ADMyUsZK5u2d6FG2G"
PLAYLIST_URL = "https://www.youtube.com/@CityofLancasterPAGov/streams"

# Deno is required by yt-dlp for YouTube JS challenge solving.
# WinGet installs it here but doesn't always propagate to child processes.
_DENO_WINGET = Path(os.environ.get("LOCALAPPDATA", "")) / (
    "Microsoft/WinGet/Packages/"
    "DenoLand.Deno_Microsoft.Winget.Source_8wekyb3d8bbwe/deno.exe"
)
if _DENO_WINGET.exists():
    _deno_str = str(_DENO_WINGET)
    os.environ["PATH"] = str(_DENO_WINGET.parent) + os.pathsep + os.environ.get("PATH", "")
else:
    _deno_str = "deno"   # fall back to whatever is on PATH

# Upload-date window. yt-dlp accepts either "YYYYMMDD" or relative forms like
# "today-2years", "now-18months", "today-30days". Set either to None to leave
# that side of the window open.
DATE_AFTER: str | None = "20241231"   # 2025 and later
DATE_BEFORE: str | None = None

# Browser cookie source for YouTube auth. Leave as None to download anonymously
# (preferred). Only enable if you keep hitting "Sign in to confirm you're not
# a bot" errors AFTER installing Deno and trying again. If you do enable it,
# DON'T point it at your main Chrome profile — create a separate browser
# profile, sign into a throwaway Google account in that profile, then point
# this at it. The tuple is (browser[, profile[, keyring[, container]]]).
COOKIES_FROM_BROWSER: tuple[str, ...] | None = None
# COOKIES_FROM_BROWSER = ("chrome",)              # default Chrome profile
# COOKIES_FROM_BROWSER = ("chrome", "Profile 2")  # named Chrome profile (recommended)
# COOKIES_FROM_BROWSER = ("firefox", "default-release")

# Truncate long titles so Windows path limits don't bite. The [id] suffix
# keeps filenames unique even if two titles collide after truncation.
OUTTMPL = "%(title).180B [%(id)s].%(ext)s"


def _build_ydl_opts(
    video_dir: Path,
    transcript_dir: Path,
    metadata_dir: Path,
    archive_file: Path,
    start_at: int = 1,
    cookie_file: Path | None = None,
    cookies_from_browser: str | None = None,
) -> dict:
    opts: dict = {
        "paths": {
            "home": str(video_dir),
            "subtitle": str(transcript_dir),
            "infojson": str(metadata_dir),
            # Without this, the playlist-level <playlist title>.info.json
            # falls back to `home` and pollutes the videos/ folder.
            "pl_infojson": str(metadata_dir),
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
        # Persist downloaded-video IDs so repeat runs skip them instantly
        # without re-checking file existence for every item in the playlist.
        "download_archive": str(archive_file),
        # Point yt-dlp at Deno for YouTube JS challenge solving.
        # Format: {runtime_name: {config}} per yt-dlp YoutubeDL.__init__ docs.
        "js_runtimes": {"deno": {"path": _deno_str}},
        # Polite throttling — looks more human, dodges most rate gates.
        # Adds roughly (sleep_interval to max_sleep_interval) seconds between
        # video downloads, plus sleep_interval_requests between metadata calls.
        "sleep_interval_requests": 1,
        "sleep_interval": 3,
        "max_sleep_interval": 10,
        # Big mp4 streams (1+ GB council meetings) sometimes stall on slow
        # chunks; the default 20s socket timeout drops them and yt-dlp gives
        # up before retrying. These extend the patience on each chunk and the
        # number of automatic retries.
        "socket_timeout": 60,
        "retries": 10,
        "fragment_retries": 10,
        "postprocessors": [
            {"key": "FFmpegSubtitlesConvertor", "format": "srt"},
        ],
    }
    if DATE_AFTER or DATE_BEFORE:
        # DateRange's runtime accepts "YYYYMMDD" or relative strings like
        # "today-2years"; the type stub claims it only takes `date` objects.
        opts["daterange"] = DateRange(DATE_AFTER, DATE_BEFORE)  # type: ignore[arg-type]
    # android_vr client ignores cookies; force web client so the auth lands.
    if cookie_file or cookies_from_browser:
        opts["extractor_args"] = {"youtube": {"player_client": ["web"]}}
    if cookie_file:
        opts["cookiefile"] = str(cookie_file)
    elif cookies_from_browser:
        opts["cookiesfrombrowser"] = (cookies_from_browser,)
    elif COOKIES_FROM_BROWSER:
        opts["cookiesfrombrowser"] = COOKIES_FROM_BROWSER
    if start_at > 1:
        # yt-dlp playlist_items spec is 1-indexed; "21:" means item 21 to end.
        opts["playlist_items"] = f"{start_at}:"
    return opts


def _extract_audio(video_path: Path, audio_path: Path) -> bool:
    """Extract audio to 16 kHz mono WAV. Returns True on success.

    WAV/PCM sidesteps codec compatibility issues (Opus-in-WebM, AAC variants)
    that caused faster-whisper's PyAV loader and Silero VAD to silently produce
    zero segments on some YouTube downloads.
    """
    audio_path.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        "ffmpeg", "-y", "-loglevel", "error",
        "-i", str(video_path),
        "-vn", "-ar", "16000", "-ac", "1", "-f", "wav",
        str(audio_path),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        audio_path.unlink(missing_ok=True)
        tail = (result.stderr or "").strip().splitlines()[-1:]
        msg = tail[0] if tail else f"exit {result.returncode}"
        print(f"  [audio] FAILED ({video_path.name}): {msg}")
        return False
    return True


def _audio_target_stem(video_stem: str) -> str:
    """Drop yt-dlp's '.fNNN' format-ID suffix if present.

    yt-dlp leaves '<title> [<id>].fNNN.<ext>' files in the output dir when its
    merge step fails (e.g. one video has both '.f251.webm' audio-only and
    '.f299.mp4' video-only files instead of a merged '.mp4'). Stripping the
    suffix maps both orphans to the same audio target stem so we can pick the
    one that actually has an audio track.
    """
    base, sep, fmt = video_stem.rpartition(".f")
    return base if sep and fmt.isdigit() else video_stem


def _derive_audio_files(video_dir: Path, audio_dir: Path) -> None:
    video_exts = {".mp4", ".mkv", ".webm", ".mov", ".m4v"}
    by_target: dict[str, list[Path]] = {}
    for video_file in sorted(video_dir.iterdir()):
        if not video_file.is_file() or video_file.suffix.lower() not in video_exts:
            continue
        target = _audio_target_stem(video_file.stem)
        by_target.setdefault(target, []).append(video_file)

    failed: list[str] = []
    for target, sources in sorted(by_target.items()):
        audio_file = audio_dir / f"{target}.wav"
        if audio_file.exists():
            continue
        # Prefer non-orphan (merged) source first; orphans only as fallback.
        sources.sort(key=lambda p: _audio_target_stem(p.stem) != p.stem)
        for src in sources:
            print(f"[audio] {src.name} -> {audio_file.name}")
            if _extract_audio(src, audio_file):
                break
        else:
            failed.append(target)

    if failed:
        print(f"\n[audio] {len(failed)} video(s) had no audio extracted:")
        for name in failed:
            print(f"  - {name}")
        print(
            "  Likely cause: yt-dlp's merge step failed and only the video-only\n"
            "  '.fNNN.mp4' orphan is on disk. Delete that file from the videos/\n"
            "  folder and re-run the script for those items to try again."
        )


def main(
    out_root: Path,
    start_at: int = 1,
    urls: list[str] | None = None,
    cookie_file: Path | None = None,
    cookies_from_browser: str | None = None,
) -> None:
    video_dir = out_root / "videos"
    audio_dir = out_root / "audio"
    transcript_dir = out_root / "transcripts"
    metadata_dir = out_root / "metadata"
    for d in (video_dir, audio_dir, transcript_dir, metadata_dir):
        d.mkdir(parents=True, exist_ok=True)

    archive_file = out_root / "downloaded.txt"
    opts = _build_ydl_opts(
        video_dir, transcript_dir, metadata_dir, archive_file,
        start_at=start_at, cookie_file=cookie_file,
        cookies_from_browser=cookies_from_browser,
    )
    with yt_dlp.YoutubeDL(opts) as ydl:
        ydl.download(urls if urls else [PLAYLIST_URL])

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
    parser.add_argument(
        "--start-at",
        type=int,
        default=1,
        metavar="N",
        help="resume at playlist item N (1-indexed; e.g. --start-at 21 to skip the first 20)",
    )
    parser.add_argument(
        "--cookies-file",
        type=Path,
        metavar="FILE",
        help="Netscape cookies.txt exported from your browser (passes straight to yt-dlp)",
    )
    parser.add_argument(
        "--urls-file",
        type=Path,
        metavar="FILE",
        help="text file with one YouTube URL per line; overrides the built-in PLAYLIST_URL",
    )
    parser.add_argument(
        "--cookies-from-browser",
        metavar="BROWSER",
        help="extract live cookies from a browser (e.g. chrome, firefox); close the browser first",
    )
    args = parser.parse_args()

    download_urls = None
    if args.urls_file:
        download_urls = [
            line.strip()
            for line in args.urls_file.read_text(encoding="utf-8").splitlines()
            if line.strip() and not line.startswith("#")
        ]

    main(
        args.out.resolve(),
        start_at=args.start_at,
        urls=download_urls,
        cookie_file=args.cookies_file,
        cookies_from_browser=args.cookies_from_browser,
    )