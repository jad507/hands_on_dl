"""
diarize.py — Speaker diarization using pyannote-audio community-1.

Runs each audio file through the pipeline ONCE and saves both modes:
  - standard mode (overlap-preserving): downloads/pyannote_community-1_standard/
  - exclusive mode (one speaker per ms): downloads/pyannote_community-1_exclusive/

pyannote 4.0 returns a DiarizeOutput with both .speaker_diarization and
.exclusive_speaker_diarization attributes — no need to run twice.

Audio loading: torchaudio 2.11+ routes through torchcodec which requires Windows
"full-shared" ffmpeg DLLs. We bypass this by using ffmpeg subprocess + soundfile.

Each output folder receives:
  - <stem>.rttm       — speaker timeline in standard RTTM format
  - <stem>_stats.json — speaker statistics for later LLM-assisted comparison

Usage:
  python audio_pipeline/diarize.py                            # all files, both modes
  python audio_pipeline/diarize.py --input path/to/file.m4a  # single file, both modes
  python audio_pipeline/diarize.py --mode standard            # standard only
  python audio_pipeline/diarize.py --mode exclusive           # exclusive only
"""

import argparse
import json
import os
import subprocess
import sys
import tempfile
import traceback
from pathlib import Path

import soundfile as sf
import torch
from dotenv import load_dotenv

load_dotenv()

REPO_ROOT = Path(__file__).parent.parent
AUDIO_DIR = REPO_ROOT / "downloads" / "audio"
OUT_STANDARD = REPO_ROOT / "downloads" / "pyannote_community-1_standard"
OUT_EXCLUSIVE = REPO_ROOT / "downloads" / "pyannote_community-1_exclusive"
PYANNOTE_MODEL_ID = "pyannote/speaker-diarization-community-1"
HF_TOKEN = os.environ.get("HF_TOKEN", "")


def load_pipeline():
    if not HF_TOKEN:
        print("ERROR: HF_TOKEN not set in .env")
        sys.exit(1)

    from pyannote.audio import Pipeline

    print(f"Loading pyannote pipeline: {PYANNOTE_MODEL_ID}")
    pipeline = Pipeline.from_pretrained(PYANNOTE_MODEL_ID, token=HF_TOKEN)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    pipeline.to(device)
    print(f"Pipeline loaded on: {device}")
    return pipeline


def load_audio(audio_path: Path) -> dict:
    """Decode audio to 16kHz mono via ffmpeg, load with soundfile, return pyannote dict.

    torchaudio 2.11+ routes through torchcodec which fails on Windows without
    the full-shared ffmpeg DLLs. We use ffmpeg subprocess (already on PATH) to
    write a temp WAV, load it with soundfile, then delete it.
    """
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        tmp_path = tmp.name
    try:
        subprocess.run(
            ["ffmpeg", "-y", "-i", str(audio_path),
             "-ar", "16000", "-ac", "1", "-f", "wav", tmp_path],
            check=True, capture_output=True,
        )
        waveform_np, sample_rate = sf.read(tmp_path, dtype="float32")
        # soundfile returns (samples,) for mono; pyannote wants (channels, samples)
        waveform = torch.from_numpy(waveform_np).unsqueeze(0)
    finally:
        Path(tmp_path).unlink(missing_ok=True)
    return {"waveform": waveform, "sample_rate": sample_rate}


def compute_stats(annotation, mode: str) -> dict:
    """Extract speaker statistics from a pyannote Annotation object."""
    speakers = annotation.labels()
    speaker_durations = {spk: annotation.label_duration(spk) for spk in speakers}

    overlap_duration = 0.0
    if mode == "standard":
        try:
            total_speech = sum(speaker_durations.values())
            support_duration = annotation.get_timeline().support().duration()
            overlap_duration = max(0.0, total_speech - support_duration)
        except Exception:
            pass

    return {
        "mode": mode,
        "speaker_count": len(speakers),
        "speakers": {spk: round(dur, 3) for spk, dur in sorted(speaker_durations.items())},
        "total_speech_duration_s": round(sum(speaker_durations.values()), 3),
        "overlap_duration_s": round(overlap_duration, 3),
    }


def write_rttm(annotation, audio_path: Path, out_path: Path):
    """Write pyannote Annotation to RTTM file."""
    stem = audio_path.stem
    with open(out_path, "w") as f:
        for segment, _, speaker in annotation.itertracks(yield_label=True):
            start = segment.start
            duration = segment.end - segment.start
            f.write(
                f"SPEAKER {stem} 1 {start:.3f} {duration:.3f} "
                f"<NA> <NA> {speaker} <NA> <NA>\n"
            )


def process_file(pipeline, audio_path: Path, mode: str):
    std_rttm = OUT_STANDARD / f"{audio_path.stem}.rttm"
    std_stats = OUT_STANDARD / f"{audio_path.stem}_stats.json"
    excl_rttm = OUT_EXCLUSIVE / f"{audio_path.stem}.rttm"
    excl_stats = OUT_EXCLUSIVE / f"{audio_path.stem}_stats.json"

    need_standard = mode in ("standard", "both") and not (std_rttm.exists() and std_stats.exists())
    need_exclusive = mode in ("exclusive", "both") and not (excl_rttm.exists() and excl_stats.exists())

    if not need_standard and not need_exclusive:
        print(f"  Both modes already done, skipping.")
        return

    print(f"\nProcessing: {audio_path.name}")

    print(f"  Loading audio (ffmpeg -> soundfile)...")
    try:
        audio = load_audio(audio_path)
    except Exception:
        print(f"  ERROR loading audio:")
        traceback.print_exc()
        return

    print(f"  Running diarization pipeline...")
    try:
        result = pipeline(audio)
    except Exception:
        print(f"  ERROR during diarization:")
        traceback.print_exc()
        return

    std_annotation = result.speaker_diarization
    excl_annotation = result.exclusive_speaker_diarization

    if need_standard:
        try:
            OUT_STANDARD.mkdir(parents=True, exist_ok=True)
            write_rttm(std_annotation, audio_path, std_rttm)
            stats = compute_stats(std_annotation, "standard")
            std_stats.write_text(json.dumps(stats, indent=2))
            print(f"  [standard] {stats['speaker_count']} speakers, "
                  f"{stats['total_speech_duration_s']:.1f}s speech, "
                  f"{stats['overlap_duration_s']:.1f}s overlap -> {std_rttm.name}")
        except Exception:
            print(f"  [standard] ERROR writing output:")
            traceback.print_exc()

    if need_exclusive:
        try:
            OUT_EXCLUSIVE.mkdir(parents=True, exist_ok=True)
            write_rttm(excl_annotation, audio_path, excl_rttm)
            stats = compute_stats(excl_annotation, "exclusive")
            excl_stats.write_text(json.dumps(stats, indent=2))
            print(f"  [exclusive] {stats['speaker_count']} speakers, "
                  f"{stats['total_speech_duration_s']:.1f}s speech "
                  f"-> {excl_rttm.name}")
        except Exception:
            print(f"  [exclusive] ERROR writing output:")
            traceback.print_exc()


def main():
    parser = argparse.ArgumentParser(description="Run pyannote community-1 diarization")
    parser.add_argument(
        "--input", "-i",
        help="Single .m4a file or directory (default: downloads/audio/)",
        default=None,
    )
    parser.add_argument(
        "--mode", "-m",
        choices=["standard", "exclusive", "both"],
        default="both",
        help="Diarization mode (default: both)",
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

    print(f"Files to process: {len(audio_files)}")
    print(f"Mode: {args.mode}")

    pipeline = load_pipeline()

    for audio_path in audio_files:
        process_file(pipeline, audio_path, args.mode)

    print("\nDone.")


if __name__ == "__main__":
    main()
