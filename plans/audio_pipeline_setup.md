# Audio Pipeline Setup

Speaker diarization + high-quality transcription for city council meeting recordings.

## Hardware target
- 12GB VRAM GPU desktop (all heavy processing)
- 4GB VRAM laptop (dev/testing only)

## Folder structure

```
downloads/
  audio/                              # Input: .m4a files (git-ignored)
  pyannote_community-1_standard/      # Diarization output, overlap mode (git-ignored)
  pyannote_community-1_exclusive/     # Diarization output, exclusive mode (git-ignored)
  whisper_large-v3/                   # Transcription output (git-ignored)

plans/                                # This folder — git-committed, no personal info
audio_pipeline/                       # Scripts — git-committed
  setup_check.py
  download_models.py
  diarize.py
  transcribe.py
  compare_rttm.py
```

## Technology stack

| Task | Tool | Model | Notes |
|------|------|-------|-------|
| Diarization | pyannote-audio 4.0 | community-1 | open-weight; precision-2 is paid API |
| Transcription | faster-whisper | large-v3 FP16 | beam_size=10, best_of=5, VAD enabled |
| LLM extraction | TBD (Ollama/vLLM) | Llama 3 8B Instruct | future phase |

## Installation

```bash
# Activate venv first, then:
pip install "pyannote.audio>=4.0" faster-whisper soundfile
```

If faster-whisper can't find CUDA (ctranslate2 issue):
```bash
pip install ctranslate2 --extra-index-url https://pypi.nvidia.com
```

## HuggingFace setup

1. Create token at https://huggingface.co/settings/tokens
2. Accept license at https://huggingface.co/pyannote/speaker-diarization-community-1
3. Add to `.env`: `HF_TOKEN=hf_...`

## Usage sequence

### 1. Verify environment
```bash
python audio_pipeline/setup_check.py
```
Must show: CUDA available, correct GPU, pyannote + faster-whisper importable.

### 2. Download models
```bash
python audio_pipeline/download_models.py
```
Pre-downloads community-1 pipeline and whisper large-v3 to HuggingFace cache.

### 3. Smoke test — single file
```bash
# Pick the shortest .m4a for testing
python audio_pipeline/diarize.py --input "downloads/audio/<shortest_file>.m4a"
python audio_pipeline/transcribe.py --input "downloads/audio/<shortest_file>.m4a"
```
Check: RTTM files appear in both output folders; JSON appears in whisper folder.

### 4. Overnight run — all files
```bash
python audio_pipeline/diarize.py
python audio_pipeline/transcribe.py
```

## Diarization modes

Two modes are run per file and saved to separate folders:

**standard** (overlap-preserving): Records overlapping speech events. This is the
social-science correct approach — contested-floor moments (e.g., a commenter going
over time while a council member interrupts) are preserved as overlapping speaker
segments. Recommended for downstream analysis.

**exclusive**: Forces exactly one speaker per millisecond. Easier for audio slicing
but loses overlap information. Saved alongside standard output for comparison.

Both modes produce:
- `<stem>.rttm` — speaker timeline
- `<stem>_stats.json` — speaker counts, durations, overlap regions (for LLM comparison)

## Transcription settings (maximum quality)

```python
model = WhisperModel("large-v3", device="cuda", compute_type="float16")
segments, info = model.transcribe(
    audio_path,
    beam_size=10,
    best_of=5,
    vad_filter=True,
    vad_parameters={"min_silence_duration_ms": 500},
    condition_on_previous_text=False,
)
```

## Troubleshooting

**CUDA not available after install:**
Check `torch.cuda.is_available()`. May need to reinstall torch with correct CUDA version:
https://pytorch.org/get-started/locally/

**pyannote 401/403 error:**
HF token not set or license not accepted. Re-check `.env` and the model card page.

**faster-whisper float16 error:**
Fall back to `compute_type="int8"` first to confirm rest of pipeline works,
then fix ctranslate2 CUDA separately.

**.m4a format error from pyannote:**
Convert to 16kHz mono WAV:
```bash
ffmpeg -i input.m4a -ar 16000 -ac 1 output.wav
```

## Future work

- `compare_rttm.py`: LLM-assisted diff between standard and exclusive diarization outputs
- LLM extraction: Pydantic structured sentiment analysis per public comment segment