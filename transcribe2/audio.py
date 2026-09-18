"""
Audio acquisition and canonicalization.

Everything in the pipeline reads exactly one audio format: 16 kHz, mono, float32,
normalized to [-1, 1]. That is not an arbitrary house style -- it is what Gemma 4
requires, stated in Google's own docs:

    Sample Rate: 16kHz
    Bit Depth: 32-bit float format, with samples normalized within the range [-1, 1]
    Audio channels: Audio data is processed as a single audio channel.
    -- https://ai.google.dev/gemma/docs/capabilities/audio

Whisper wants the same thing, so one canonical form serves both engines. Doing
the conversion ONCE up front means the two engines are provably reading identical
samples, which matters: if you resampled separately per engine you would have
introduced a second uncontrolled variable into an experiment whose entire point
is controlling variables.

The docs also specify the resampling method:

    When resampling audio to 16 kHz, you should use a Fourier method for best
    results, such as scipy.signal.resample or librosa.sample(res_type='scipy').

ffmpeg's default resampler (swresample, a windowed-sinc) is not a Fourier method.
In practice the difference is small, but `--strict-resample` is provided for
runs where you would rather follow the vendor's recommendation exactly than
argue about it in a reviewer response.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import wave
from dataclasses import dataclass
from pathlib import Path

TARGET_SR = 16_000
TARGET_CHANNELS = 1

_URL_PREFIXES = ("http://", "https://", "www.")


class ToolMissing(RuntimeError):
    pass


def _require(tool: str) -> str:
    path = shutil.which(tool)
    if not path:
        raise ToolMissing(
            f"{tool!r} not found on PATH. "
            + {
                "ffmpeg": "Install from https://ffmpeg.org/download.html (or `winget install ffmpeg`).",
                "ffprobe": "Ships with ffmpeg.",
                "yt-dlp": "pip install -U yt-dlp",
            }.get(tool, "")
        )
    return path


def is_url(source: str) -> bool:
    return source.lower().startswith(_URL_PREFIXES)


def _run(cmd: list[str], what: str) -> subprocess.CompletedProcess:
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        tail = (proc.stderr or proc.stdout or "").strip().splitlines()[-12:]
        raise RuntimeError(f"{what} failed (exit {proc.returncode}):\n" + "\n".join(tail))
    return proc


# ------------------------------------------------------------- acquire ---


@dataclass
class Acquired:
    media_path: Path
    title: str
    source: str
    info: dict


def acquire(source: str, workdir: Path, cookies: Path | None = None) -> Acquired:
    """Resolve a local path or a URL to a media file on disk.

    Local files are used in place (never copied -- these can be gigabytes).
    URLs go through yt-dlp, which handles far more than YouTube.
    """
    workdir.mkdir(parents=True, exist_ok=True)

    if not is_url(source):
        p = Path(source).expanduser().resolve()
        if not p.exists():
            raise FileNotFoundError(f"no such file: {p}")
        return Acquired(media_path=p, title=p.stem, source=str(p), info={})

    _require("yt-dlp")
    out_tmpl = str(workdir / "%(title)s [%(id)s].%(ext)s")
    cmd = [
        "yt-dlp",
        "-f", "bestaudio/best",
        "--no-playlist",
        "--write-info-json",
        "--print", "after_move:filepath",
        "-o", out_tmpl,
        source,
    ]
    if cookies:
        cmd[1:1] = ["--cookies", str(cookies)]
    proc = _run(cmd, "yt-dlp download")

    lines = [ln.strip() for ln in proc.stdout.splitlines() if ln.strip()]
    if not lines:
        raise RuntimeError("yt-dlp produced no output path")
    media = Path(lines[-1])
    if not media.exists():
        raise RuntimeError(f"yt-dlp reported {media} but it does not exist")

    info: dict = {}
    for cand in (media.with_suffix(".info.json"), media.parent / f"{media.stem}.info.json"):
        if cand.exists():
            info = json.loads(cand.read_text(encoding="utf-8"))
            break

    return Acquired(
        media_path=media,
        title=info.get("title", media.stem),
        source=source,
        info=info,
    )


# ------------------------------------------------------ canonicalize ---


def probe_duration(path: Path) -> float:
    _require("ffprobe")
    proc = _run(
        [
            "ffprobe", "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            str(path),
        ],
        "ffprobe duration",
    )
    return float(proc.stdout.strip())


def to_canonical_wav(src: Path, dst: Path, strict_resample: bool = False) -> Path:
    """Decode anything ffmpeg understands to 16 kHz mono 16-bit PCM WAV.

    Stored as int16 rather than float32 because WAV float32 handling is uneven
    across readers; the float32 [-1, 1] conversion Gemma wants happens at load
    time in `load_slice()`, which is one line and unambiguous.
    """
    _require("ffmpeg")
    dst.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
        "-i", str(src),
        "-vn",
        "-ac", str(TARGET_CHANNELS),
        "-ar", str(TARGET_SR),
        "-acodec", "pcm_s16le",
        str(dst),
    ]
    if strict_resample:
        # soxr at very high precision -- closer to a Fourier method than the
        # default swresample kernel. Not identical to scipy.signal.resample; if
        # you need exactly that, resample in Python after loading.
        cmd[-1:-1] = ["-af", "aresample=resampler=soxr:precision=33"]
    _run(cmd, "ffmpeg transcode")
    if not dst.exists() or dst.stat().st_size == 0:
        raise RuntimeError(f"ffmpeg produced no output at {dst}")
    return dst


def wav_info(path: Path) -> tuple[int, int, float]:
    """(sample_rate, channels, duration_seconds) without loading the samples."""
    with wave.open(str(path), "rb") as w:
        sr = w.getframerate()
        ch = w.getnchannels()
        n = w.getnframes()
    return sr, ch, n / float(sr)


def load_slice(path: Path, start: float, end: float):
    """Read [start, end) as a float32 numpy array in [-1, 1] at 16 kHz.

    Reads only the requested frames. A three-hour meeting is ~170 MB as int16
    and it is pointless to hold all of it in memory to grab eight seconds.
    """
    import numpy as np  # local import so `--help` works without numpy installed

    with wave.open(str(path), "rb") as w:
        sr = w.getframerate()
        ch = w.getnchannels()
        width = w.getsampwidth()
        total = w.getnframes()
        if sr != TARGET_SR or ch != TARGET_CHANNELS or width != 2:
            raise ValueError(
                f"{path.name} is {sr} Hz / {ch}ch / {width*8}-bit; expected "
                f"{TARGET_SR} Hz / mono / 16-bit. Run to_canonical_wav() first."
            )
        first = max(0, int(round(start * sr)))
        last = min(total, int(round(end * sr)))
        if last <= first:
            return np.zeros(0, dtype=np.float32)
        w.setpos(first)
        raw = w.readframes(last - first)

    return np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0


def write_slice_wav(samples, dst: Path) -> Path:
    """Write float32 [-1, 1] samples back out as 16 kHz mono 16-bit WAV.

    Needed because some runtimes (llama.cpp's server, for one) want a file path
    or base64 WAV rather than an array.
    """
    import numpy as np

    dst.parent.mkdir(parents=True, exist_ok=True)
    clipped = np.clip(samples, -1.0, 1.0)
    pcm = (clipped * 32767.0).astype(np.int16)
    with wave.open(str(dst), "wb") as w:
        w.setnchannels(TARGET_CHANNELS)
        w.setsampwidth(2)
        w.setframerate(TARGET_SR)
        w.writeframes(pcm.tobytes())
    return dst
