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
  python audio_pipeline/transcribe.py --compute-type int8        # lower VRAM, near-equal accuracy
  python audio_pipeline/transcribe.py --reload-every 1          # reload model every 1 files (default)
  python audio_pipeline/transcribe.py --reload-every 0           # disable reload
"""

import argparse
import gc
import json
import os
import sys
import time
import traceback
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(REPO_ROOT))
from pipeline_utils import fmt_elapsed, now_str  # noqa: E402
import whisper_io  # noqa: E402
AUDIO_DIR = REPO_ROOT / "downloads" / "audio"
MODEL_NAME = "large-v3"
OUT_DIR = REPO_ROOT / "downloads" / f"whisper_{MODEL_NAME}"

# Single source of truth for the decoding parameters. They are passed to
# model.transcribe() AND written into every output's provenance block, so
# defining them twice is how the record silently stops describing the run.
DECODE_PARAMS = {
    "beam_size": 10,
    "best_of": 5,
    "vad_filter": True,
    "vad_parameters": {"min_silence_duration_ms": 500},
    "condition_on_previous_text": False,
}


def _gpu_mem_str(reset_peak: bool = False) -> str:
    """Compact GPU memory line: alloc / reserved / peak-since-last-reset."""
    import torch
    if not torch.cuda.is_available():
        return "CPU mode"
    alloc   = torch.cuda.memory_allocated()       / 1024**3
    reserved = torch.cuda.memory_reserved()        / 1024**3
    peak    = torch.cuda.max_memory_allocated()   / 1024**3
    if reset_peak:
        torch.cuda.reset_peak_memory_stats()
    return f"alloc={alloc:.2f}GB  reserved={reserved:.2f}GB  peak={peak:.2f}GB"


def load_model(compute_type: str):
    from faster_whisper import WhisperModel

    print(f"Loading faster-whisper model: {MODEL_NAME} ({compute_type})")
    import torch
    device = "cuda" if torch.cuda.is_available() else "cpu"
    if device == "cpu":
        print("WARNING: CUDA not available. Transcription on CPU will be extremely slow.")
        compute_type = "int8"  # float16 not supported on CPU

    model = WhisperModel(MODEL_NAME, device=device, compute_type=compute_type)
    print(f"Model loaded on: {device}  |  {_gpu_mem_str(reset_peak=True)}")
    return model




SENTINEL_FILE = OUT_DIR.parent / "_transcribe_in_progress.txt"


def transcribe_file(model, audio_path: Path, out_dir: Path,
                    compute_type: str) -> bool:
    """Transcribe one file. Returns True if work was done, False if skipped."""
    out_path = out_dir / f"{audio_path.stem}.json"

    if out_path.exists():
        print(f"  Already done, skipping: {out_path.name}")
        return False

    # Write sentinel before entering CTranslate2. If the process is killed by a
    # native crash (STATUS_STACK_BUFFER_OVERRUN), this file survives and records
    # exactly which file caused it — the log's tee buffer may not flush in time.
    SENTINEL_FILE.write_text(str(audio_path), encoding="utf-8")

    print(f"  GPU before: {_gpu_mem_str()}")
    print(f"  Transcribing (this may take a while)...")
    t0 = time.perf_counter()
    segments, info = model.transcribe(str(audio_path), **DECODE_PARAMS)

    result = []
    for seg in segments:
        result.append({
            "start": round(seg.start, 3),
            "end": round(seg.end, 3),
            "text": seg.text.strip(),
        })

    # Provenance travels with the transcript, not beside it. See whisper_io.
    prov = whisper_io.build_provenance(
        model_name=MODEL_NAME,
        compute_type=compute_type,
        decode_params=DECODE_PARAMS,
        audio_path=audio_path,
        audio_info={
            "duration_s": round(info.duration, 3),
            "language": info.language,
            "language_probability": round(info.language_probability, 4),
        },
    )
    whisper_io.write_transcript(out_path, result, prov)
    SENTINEL_FILE.unlink(missing_ok=True)

    elapsed = time.perf_counter() - t0
    duration_min = info.duration / 60
    print(f"  Done: {len(result)} segments, audio {duration_min:.1f} min, elapsed {fmt_elapsed(elapsed)}")
    print(f"  Written: {out_path.name}")
    return True


def main():
    parser = argparse.ArgumentParser(description="Transcribe audio with faster-whisper large-v3")
    parser.add_argument(
        "--input", "-i",
        help="Single .wav/.flac file or directory (default: downloads/audio/)",
        default=None,
    )
    parser.add_argument(
        "--compute-type", "-c",
        choices=["float16", "int8"],
        default="float16",
        help="Precision (default: float16 for 12GB VRAM; use int8 if float16 errors)",
    )
    parser.add_argument(
        "--reload-every", "-r",
        type=int,
        default=1,
        metavar="N",
        help="Reload model every N transcribed files to flush CUDA fragmentation (0 = never; default: 1)",
    )
    args = parser.parse_args()

    if args.input:
        input_path = Path(args.input)
        if input_path.is_file():
            audio_files = [input_path]
        elif input_path.is_dir():
            audio_files = sorted([*input_path.glob("*.wav"), *input_path.glob("*.flac")])
        else:
            print(f"ERROR: --input path not found: {input_path}")
            sys.exit(1)
    else:
        audio_files = sorted([*AUDIO_DIR.glob("*.wav"), *AUDIO_DIR.glob("*.flac")])

    if not audio_files:
        print("No .wav/.flac files found. Check the input path.")
        sys.exit(1)

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    if SENTINEL_FILE.exists():
        crashed_on = SENTINEL_FILE.read_text(encoding="utf-8").strip()
        print(f"WARNING: previous run crashed mid-transcription on: {crashed_on}")
        print(f"  (sentinel: {SENTINEL_FILE})")
        SENTINEL_FILE.unlink()

    print(f"Files to transcribe: {len(audio_files)}")
    print(f"Output directory: {OUT_DIR}")

    model = load_model(args.compute_type)

    total_start = time.perf_counter()
    n_done = n_skipped = n_errors = 0

    for audio_path in audio_files:
        # Reload model every N transcribed files to flush CUDA memory fragmentation.
        # del must happen in this scope — the last reference to the old model lives here,
        # so gc.collect() only frees it after we del in main(), not inside a helper.
        if args.reload_every > 0 and n_done > 0 and n_done % args.reload_every == 0:
            import torch
            print(f"\n[{now_str()}] Reloading model after {n_done} files to flush CUDA fragmentation")
            print(f"  before unload: {_gpu_mem_str()}")
            del model
            gc.collect()
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            print(f"  after  unload: {_gpu_mem_str()}")
            model = load_model(args.compute_type)

        print(f"\n[{now_str()}] Processing: {audio_path.name}")
        try:
            did_work = transcribe_file(model, audio_path, OUT_DIR, args.compute_type)
            if did_work:
                n_done += 1
                print(f"  GPU: {_gpu_mem_str(reset_peak=True)}")
            else:
                n_skipped += 1
        except Exception:
            print(f"  ERROR on {audio_path.name}:")
            traceback.print_exc()
            n_errors += 1

    total_elapsed = time.perf_counter() - total_start
    print(f"\nSummary: {n_done} transcribed, {n_skipped} skipped, {n_errors} errors")
    print(f"Total time: {fmt_elapsed(total_elapsed)}")

    # Explicitly release CUDA resources before exit to avoid CTranslate2 destructor crash
    # on Windows (STATUS_STACK_BUFFER_OVERRUN / exit -1073740791).
    del model
    gc.collect()
    import torch
    if torch.cuda.is_available():
        torch.cuda.empty_cache()

    os._exit(0)


if __name__ == "__main__":
    main()