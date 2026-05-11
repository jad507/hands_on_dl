"""
setup_check.py — Verify the audio pipeline environment before running.

Checks: Python, torch/CUDA, pyannote, faster-whisper, HF token, audio files.
"""

import os
import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

AUDIO_DIR = Path(__file__).parent.parent / "downloads" / "audio"


def _mask_token(token: str) -> str:
    if len(token) <= 8:
        return "****"
    return token[:4] + "****" + token[-4:]


def check_python():
    print(f"Python:        {sys.version}")


def check_torch():
    try:
        import torch
        cuda_ok = torch.cuda.is_available()
        print(f"torch:         {torch.__version__}")
        print(f"CUDA available:{' YES' if cuda_ok else ' NO'}")
        if cuda_ok:
            print(f"GPU:           {torch.cuda.get_device_name(0)}")
            props = torch.cuda.get_device_properties(0)
            vram_gb = props.total_memory / 1024**3
            print(f"VRAM:          {vram_gb:.1f} GB")
        else:
            print("  WARNING: CUDA not available — diarization and transcription will be very slow on CPU")
    except ImportError:
        print("torch:         NOT INSTALLED")


def check_pyannote():
    try:
        import pyannote.audio
        print(f"pyannote.audio:{pyannote.audio.__version__}")
    except ImportError:
        print("pyannote.audio:NOT INSTALLED — run: pip install 'pyannote.audio>=4.0'")


def check_faster_whisper():
    try:
        import faster_whisper
        print(f"faster-whisper:{faster_whisper.__version__}")
    except ImportError:
        print("faster-whisper:NOT INSTALLED — run: pip install faster-whisper")


def check_ctranslate2():
    try:
        import ctranslate2
        print(f"ctranslate2:   {ctranslate2.__version__}")
        devices = ctranslate2.get_supported_compute_types("cuda")
        print(f"  CUDA compute types: {sorted(devices)}")
    except ImportError:
        print("ctranslate2:   NOT INSTALLED (faster-whisper dependency)")
    except RuntimeError as e:
        print(f"ctranslate2:   installed but CUDA not usable: {e}")


def check_soundfile():
    try:
        import soundfile
        print(f"soundfile:     {soundfile.__version__}")
    except ImportError:
        print("soundfile:     NOT INSTALLED — run: pip install soundfile")


def check_hf_token():
    token = os.environ.get("HF_TOKEN", "")
    if token:
        print(f"HF_TOKEN:      {_mask_token(token)} (set)")
    else:
        print("HF_TOKEN:      NOT SET — add to .env before running diarize.py or download_models.py")


def check_audio_files():
    if not AUDIO_DIR.exists():
        print(f"Audio dir:     NOT FOUND at {AUDIO_DIR}")
        return
    m4a_files = sorted(AUDIO_DIR.glob("*.m4a"))
    total_bytes = sum(f.stat().st_size for f in m4a_files)
    total_gb = total_bytes / 1024**3
    print(f"Audio files:   {len(m4a_files)} .m4a files ({total_gb:.2f} GB) in {AUDIO_DIR}")
    if m4a_files:
        smallest = min(m4a_files, key=lambda f: f.stat().st_size)
        largest = max(m4a_files, key=lambda f: f.stat().st_size)
        print(f"  Smallest:    {smallest.name} ({smallest.stat().st_size / 1024**2:.0f} MB)")
        print(f"  Largest:     {largest.name} ({largest.stat().st_size / 1024**2:.0f} MB)")


if __name__ == "__main__":
    print("=" * 60)
    print("Audio Pipeline Environment Check")
    print("=" * 60)
    check_python()
    print()
    check_torch()
    print()
    check_pyannote()
    check_faster_whisper()
    check_ctranslate2()
    check_soundfile()
    print()
    check_hf_token()
    print()
    check_audio_files()
    print("=" * 60)