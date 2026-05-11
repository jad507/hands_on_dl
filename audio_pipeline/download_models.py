"""
download_models.py — Pre-download all models to the HuggingFace cache.

Run this before the overnight batch to avoid mid-run download failures.
Models downloaded:
  - pyannote/speaker-diarization-community-1 (requires HF_TOKEN + accepted license)
  - faster-whisper large-v3 (downloads from HuggingFace automatically)
"""

import os
import sys
from pathlib import Path

import torch
from dotenv import load_dotenv

load_dotenv()

HF_TOKEN = os.environ.get("HF_TOKEN", "")
PYANNOTE_MODEL_ID = "pyannote/speaker-diarization-community-1"
WHISPER_MODEL_ID = "large-v3"


def download_pyannote():
    print(f"\n[pyannote] Downloading pipeline: {PYANNOTE_MODEL_ID}")
    if not HF_TOKEN:
        print("  ERROR: HF_TOKEN not set. Cannot download gated pyannote models.")
        print("  Add HF_TOKEN to your .env file and re-run.")
        return False

    try:
        from pyannote.audio import Pipeline

        pipeline = Pipeline.from_pretrained(PYANNOTE_MODEL_ID, token=HF_TOKEN)
        print(f"  OK — pipeline loaded: {type(pipeline).__name__}")
        print(f"  Pipeline config: {pipeline}")
        # Move to CPU to free GPU memory; this just confirms the download worked
        del pipeline
        torch.cuda.empty_cache() if torch.cuda.is_available() else None
        return True
    except Exception as e:
        print(f"  ERROR: {e}")
        print()
        if "401" in str(e) or "403" in str(e):
            print("  Token rejected or license not accepted.")
            print(f"  Accept the license at: https://huggingface.co/{PYANNOTE_MODEL_ID}")
        return False


def download_whisper():
    print(f"\n[faster-whisper] Downloading model: {WHISPER_MODEL_ID}")
    try:
        from faster_whisper import WhisperModel

        # Use CPU for the download-only step to avoid consuming GPU memory
        print("  Loading on CPU to cache weights (this may take several minutes)...")
        model = WhisperModel(WHISPER_MODEL_ID, device="cpu", compute_type="int8")
        print(f"  OK — model cached: {WHISPER_MODEL_ID}")
        del model
        return True
    except Exception as e:
        print(f"  ERROR: {e}")
        return False


if __name__ == "__main__":
    print("=" * 60)
    print("Model Download / Cache Check")
    print("=" * 60)

    results = {}
    results["pyannote"] = download_pyannote()
    results["faster-whisper"] = download_whisper()

    print("\n" + "=" * 60)
    print("Summary:")
    for name, ok in results.items():
        status = "OK" if ok else "FAILED"
        print(f"  {name:<20} {status}")
    print("=" * 60)

    if not all(results.values()):
        sys.exit(1)