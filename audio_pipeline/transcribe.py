"""
transcribe.py — High-quality transcription using faster-whisper large-v3.

Settings are tuned for maximum accuracy (not speed):
  - FP16 precision (uses ~10GB of 12GB VRAM)
  - beam_size=10, best_of=5
  - VAD filter enabled (prevents hallucination loops during silence)
  - condition_on_previous_text=False (prevents repetition loops)

Output: downloads/whisper_large-v3/<stem>.json
Each JSON file is a list of {"start": float, "end": float, "text": str} objects.

Usage:
  python audio_pipeline/transcribe.py                            # all files
  python audio_pipeline/transcribe.py --input path/to/file.m4a  # single file
  python audio_pipeline/transcribe.py --compute-type int8        # fallback if float16 fails
"""

import argparse
import json
import sys
import traceback
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

REPO_ROOT = Path(__file__).parent.parent
AUDIO_DIR = REPO_ROOT / "downloads" / "audio"
MODEL_NAME = "large-v3"
OUT_DIR = REPO_ROOT / "downloads" / f"whisper_{MODEL_NAME}"


def load_model(compute_type: str):
    from faster_whisper import WhisperModel

    print(f"Loading faster-whisper model: {MODEL_NAME} ({compute_type})")
    import torch
    device = "cuda" if torch.cuda.is_available() else "cpu"
    if device == "cpu":
        print("WARNING: CUDA not available. Transcription on CPU will be extremely slow.")
        compute_type = "int8"  # float16 not supported on CPU

    model = WhisperModel(MODEL_NAME, device=device, compute_type=compute_type)
    print(f"Model loaded on: {device}")
    return model


def transcribe_file(model, audio_path: Path, out_dir: Path) -> bool:
    out_path = out_dir / f"{audio_path.stem}.json"

    if out_path.exists():
        print(f"  Already done, skipping: {out_path.name}")
        return True

    print(f"  Transcribing (this may take a while)...")
    segments, info = model.transcribe(
        str(audio_path),
        beam_size=10,
        best_of=5,
        vad_filter=True,
        vad_parameters={"min_silence_duration_ms": 500},
        condition_on_previous_text=False,
    )

    result = []
    for seg in segments:
        result.append({
            "start": round(seg.start, 3),
            "end": round(seg.end, 3),
            "text": seg.text.strip(),
        })

    out_path.write_text(json.dumps(result, indent=2, ensure_ascii=False))
    duration_min = info.duration / 60
    print(f"  Done: {len(result)} segments, audio {duration_min:.1f} min")
    print(f"  Written: {out_path.name}")
    return True


def main():
    parser = argparse.ArgumentParser(description="Transcribe audio with faster-whisper large-v3")
    parser.add_argument(
        "--input", "-i",
        help="Single .m4a file or directory (default: downloads/audio/)",
        default=None,
    )
    parser.add_argument(
        "--compute-type", "-c",
        choices=["float16", "int8"],
        default="float16",
        help="Precision (default: float16 for 12GB VRAM; use int8 if float16 errors)",
    )
    args = parser.parse_args()

    if args.input:
        input_path = Path(args.input)
        if input_path.is_file():
            audio_files = [input_path]
        elif input_path.is_dir():
            audio_files = sorted(input_path.glob("*.m4a"))
        else:
            print(f"ERROR: --input path not found: {input_path}")
            sys.exit(1)
    else:
        audio_files = sorted(AUDIO_DIR.glob("*.m4a"))

    if not audio_files:
        print("No .m4a files found. Check the input path.")
        sys.exit(1)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Files to transcribe: {len(audio_files)}")
    print(f"Output directory: {OUT_DIR}")

    model = load_model(args.compute_type)

    for audio_path in audio_files:
        print(f"\nProcessing: {audio_path.name}")
        try:
            transcribe_file(model, audio_path, OUT_DIR)
        except Exception:
            print(f"  ERROR on {audio_path.name}:")
            traceback.print_exc()

    print("\nDone.")


if __name__ == "__main__":
    main()