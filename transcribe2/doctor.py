#!/usr/bin/env python3
"""
Environment check. Run this before anything else.

Every dependency here has a real failure mode that produces a confusing error
hours into a run rather than immediately. `transformers` in particular: Gemma 4
audio needs >= 5.10.1, and an older version fails at inference time, not at
import time.
"""

from __future__ import annotations

import importlib
import shutil
import subprocess
import sys

OK, WARN, FAIL = "  OK  ", " WARN ", " FAIL "


def _line(status: str, name: str, detail: str = "") -> None:
    print(f"[{status}] {name:<26} {detail}")


def _binary(name: str, version_flag: str = "-version") -> bool:
    path = shutil.which(name)
    if not path:
        _line(FAIL, name, "not on PATH")
        return False
    try:
        out = subprocess.run(
            [name, version_flag], capture_output=True, text=True, timeout=20
        )
        first = (out.stdout or out.stderr or "").strip().splitlines()
        _line(OK, name, first[0][:70] if first else path)
    except Exception as e:  # noqa: BLE001
        _line(WARN, name, f"present but {type(e).__name__}")
    return True


def _module(name: str, min_version: tuple[int, ...] | None = None, note: str = "") -> bool:
    try:
        mod = importlib.import_module(name)
    except ImportError:
        _line(WARN, name, f"not installed{'  -- ' + note if note else ''}")
        return False
    ver = getattr(mod, "__version__", "?")
    if min_version:
        from engines import _version_tuple

        if _version_tuple(str(ver)) < min_version:
            want = ".".join(map(str, min_version))
            _line(FAIL, name, f"{ver} -- need >= {want}. {note}")
            return False
    _line(OK, name, str(ver))
    return True


def main() -> int:
    print("=" * 74)
    print("transcribe2 environment check")
    print("=" * 74)
    print(f"python {sys.version.split()[0]}  ({sys.executable})")
    print()

    print("-- external binaries " + "-" * 52)
    have_ffmpeg = _binary("ffmpeg")
    _binary("ffprobe")
    have_ytdlp = _binary("yt-dlp", "--version")
    print()

    print("-- core python " + "-" * 58)
    have_numpy = _module("numpy")
    print()

    print("-- ASR: whisper " + "-" * 57)
    fw = _module("faster_whisper", note="pip install faster-whisper  (recommended)")
    ow = _module("whisper", note="pip install openai-whisper  (alternative)")
    print()

    print("-- ASR: gemma 4 " + "-" * 57)
    tf = _module(
        "transformers",
        min_version=(5, 10, 1),
        note="Gemma 4 audio requires >= 5.10.1: pip install -U 'transformers>=5.10.1'",
    )
    torch_ok = _module("torch")
    _module("accelerate", note="pip install accelerate  (for device_map='auto')")
    if torch_ok:
        try:
            import torch

            if torch.cuda.is_available():
                name = torch.cuda.get_device_name(0)
                vram = torch.cuda.get_device_properties(0).total_memory / 1024**3
                _line(OK, "CUDA", f"{name} -- {vram:.1f} GB VRAM")
                if vram < 8:
                    _line(WARN, "VRAM", "E4B in bf16 wants ~10 GB; use E2B or 4-bit")
            else:
                _line(WARN, "CUDA", "not available -- Gemma on CPU will be very slow")
        except Exception as e:  # noqa: BLE001
            _line(WARN, "CUDA", f"probe failed: {e}")
    print()

    print("-- diarization " + "-" * 58)
    pa = _module("pyannote.audio", note="pip install pyannote.audio  (gated models)")
    import os

    if os.environ.get("HF_TOKEN") or os.environ.get("HUGGINGFACE_TOKEN"):
        _line(OK, "HF_TOKEN", "set")
    else:
        _line(WARN, "HF_TOKEN", "unset -- pyannote models are gated; VAD fallback only")
    print()

    print("-- prosody (triage) " + "-" * 53)
    pm = _module("parselmouth", note="pip install praat-parselmouth  (best F0)")
    lb = _module("librosa", note="pip install librosa  (fallback F0)")
    if not pm and not lb:
        _line(WARN, "F0 tracking", "unavailable -- triage uses intensity + duration only")
    print()

    print("=" * 74)
    blocking = []
    if not have_ffmpeg:
        blocking.append("ffmpeg (required for everything)")
    if not have_numpy:
        blocking.append("numpy (required for everything)")
    if not (fw or ow):
        blocking.append("a whisper backend (faster-whisper or openai-whisper)")

    if blocking:
        print("BLOCKING -- install these first:")
        for b in blocking:
            print(f"  * {b}")
    else:
        print("Core pipeline is runnable.")

    caps = []
    caps.append(f"  yt-dlp URLs ....... {'yes' if have_ytdlp else 'no (local files only)'}")
    caps.append(f"  whisper ........... {'yes' if (fw or ow) else 'NO'}")
    caps.append(f"  gemma 4 audio ..... {'yes' if (tf and torch_ok) else 'no'}")
    caps.append(f"  real diarization .. {'yes' if pa else 'no (energy VAD, 1 speaker)'}")
    caps.append(f"  F0 for triage ..... {'yes' if (pm or lb) else 'no (degraded)'}")
    print("\nCapabilities:")
    print("\n".join(caps))
    print("=" * 74)
    return 1 if blocking else 0


if __name__ == "__main__":
    raise SystemExit(main())
