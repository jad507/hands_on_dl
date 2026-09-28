"""
Diarization -> the frozen spine.

This runs exactly once per recording. Its output is immutable. If you re-run it
with different settings you have created a *different experiment*, not an updated
one -- write it to a new spine file and compare them (which is, incidentally, the
`_standard` vs `_exclusive` comparison already sitting in hands_on_dl/downloads,
see docs/isls2027/05-hands-on-dl-upgrade-plan.md section 1).

Fallback: if pyannote is unavailable or has no HF token, `energy_vad_spine()`
produces a single-speaker spine from an energy VAD. Good enough to exercise the
whole pipeline on a file with one speaker -- which is exactly the emphasis test
case from docs/isls2027/06-prosody-stress-test.md.
"""

from __future__ import annotations

import os
from pathlib import Path

from spine import Segment, Spine, make_seg_id
from audio import TARGET_SR, load_slice, wav_info


def pyannote_spine(
    audio_path: Path,
    source: str,
    hf_token: str | None = None,
    pipeline_name: str = "pyannote/speaker-diarization-3.1",
    min_duration: float = 0.35,
    max_speakers: int | None = None,
) -> Spine:
    try:
        from pyannote.audio import Pipeline
    except ImportError as e:
        raise RuntimeError(
            "pyannote.audio not installed:\n  pip install pyannote.audio\n"
            "Then accept the model terms on Hugging Face and set HF_TOKEN."
        ) from e

    token = hf_token or os.environ.get("HF_TOKEN") or os.environ.get("HUGGINGFACE_TOKEN")
    if not token:
        raise RuntimeError(
            "pyannote needs a Hugging Face token (the models are gated).\n"
            "  1. Accept terms at https://hf.co/pyannote/speaker-diarization-3.1\n"
            "  2. set HF_TOKEN=hf_..."
        )

    pipe = Pipeline.from_pretrained(pipeline_name, use_auth_token=token)
    try:
        import torch

        if torch.cuda.is_available():
            pipe.to(torch.device("cuda"))
    except Exception:  # noqa: BLE001
        pass

    kwargs = {"max_speakers": max_speakers} if max_speakers else {}
    annotation = pipe(str(audio_path), **kwargs)

    raw = [
        (turn.start, turn.end, str(speaker))
        for turn, _, speaker in annotation.itertracks(yield_label=True)
    ]
    raw.sort(key=lambda t: t[0])

    segments: list[Segment] = []
    for start, end, speaker in raw:
        if end - start < min_duration:
            continue
        # Normalize to SPEAKER_00 form: Concord's SPEAKER_PREFIX regex requires an
        # initial capital, and lowercase labels would be silently dropped.
        # See docs/isls2027/03-whisper-concord-spec.md.
        label = speaker if speaker.startswith("SPEAKER") else f"SPEAKER_{speaker}"
        idx = len(segments)
        segments.append(
            Segment(
                seg_id=make_seg_id(idx, label, start),
                speaker=label,
                start=round(start, 3),
                end=round(end, 3),
            )
        )

    _, _, dur = wav_info(audio_path)
    return Spine(
        source=source,
        audio_path=str(audio_path),
        duration=dur,
        segments=segments,
        diarizer=pipeline_name,
    )


def energy_vad_spine(
    audio_path: Path,
    source: str,
    frame_ms: float = 30.0,
    min_speech_s: float = 0.4,
    min_silence_s: float = 0.35,
    percentile: float = 55.0,
    speaker: str = "SPEAKER_00",
) -> Spine:
    """Single-speaker fallback spine from an energy VAD.

    Deliberately simple and dependency-light. Not a diarizer -- it cannot tell
    speakers apart. Use it for single-speaker material and for smoke-testing the
    pipeline end to end without a gated model download.
    """
    import numpy as np

    sr, ch, dur = wav_info(audio_path)
    samples = load_slice(audio_path, 0.0, dur)
    if len(samples) == 0:
        raise RuntimeError(f"{audio_path} contains no samples")

    frame = max(1, int(sr * frame_ms / 1000))
    n = len(samples) // frame
    if n < 2:
        segs = [Segment(make_seg_id(0, speaker, 0.0), speaker, 0.0, round(dur, 3))]
        return Spine(source, str(audio_path), dur, segs, diarizer="energy-vad")

    energy = np.sqrt(
        (samples[: n * frame].reshape(n, frame).astype(np.float64) ** 2).mean(axis=1)
    )
    # Threshold relative to the file's own distribution -- no absolute dB assumption.
    thresh = max(np.percentile(energy, percentile) * 0.5, energy.max() * 0.02)
    speech = energy > thresh

    min_speech_f = max(1, int(min_speech_s * 1000 / frame_ms))
    min_sil_f = max(1, int(min_silence_s * 1000 / frame_ms))

    spans: list[list[int]] = []
    i = 0
    while i < n:
        if not speech[i]:
            i += 1
            continue
        j = i
        gap = 0
        while j < n:
            if speech[j]:
                gap = 0
            else:
                gap += 1
                if gap >= min_sil_f:
                    break
            j += 1
        end = j - gap
        if end - i >= min_speech_f:
            spans.append([i, end])
        i = j + 1

    segments: list[Segment] = []
    for k, (a, b) in enumerate(spans):
        start = round(a * frame / sr, 3)
        stop = round(min(dur, (b + 1) * frame / sr), 3)
        if stop <= start:
            continue
        segments.append(
            Segment(make_seg_id(len(segments), speaker, start), speaker, start, stop)
        )

    if not segments:  # everything below threshold; treat the file as one span
        segments = [Segment(make_seg_id(0, speaker, 0.0), speaker, 0.0, round(dur, 3))]

    return Spine(
        source=source,
        audio_path=str(audio_path),
        duration=dur,
        segments=segments,
        diarizer="energy-vad",
    )


def build_spine(
    audio_path: Path,
    source: str,
    method: str = "auto",
    **kwargs,
) -> Spine:
    """method: 'pyannote' | 'vad' | 'auto' (pyannote, silently falling back)."""
    if method == "vad":
        return energy_vad_spine(audio_path, source)
    if method == "pyannote":
        return pyannote_spine(audio_path, source, **kwargs)
    try:
        return pyannote_spine(audio_path, source, **kwargs)
    except Exception as e:  # noqa: BLE001
        print(f"[spine] pyannote unavailable ({type(e).__name__}: {e})")
        print("[spine] falling back to energy VAD -- SINGLE SPEAKER ONLY.")
        return energy_vad_spine(audio_path, source)
