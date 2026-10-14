"""
ASR engines behind one interface.

The interface is deliberately narrow: given a spine and an audio file, fill in
`segment.text[engine_name]` for the segments you were asked about. Engines do not
create segments, merge segments, or reorder them. That restriction is what makes
the cross-engine comparison valid without an alignment step.

Two engines ship here:

  WhisperEngine  -- faster-whisper or openai-whisper, constrained to spine slices
  GemmaEngine    -- Gemma 4 E2B/E4B via HF Transformers, chunked to <= 30 s

Runtime note on Gemma 4 audio
-----------------------------
Use HF Transformers. As of the Gemma 4 launch (2026-04-02), llama.cpp could not
parse Gemma 4 audio at all -- llama-server returned

    {"error":{"code":500,"message":"audio input is not supported - hint: if this
    is unexpected, you may need to provide the mmproj", ...}}

even with `--mmproj` supplied (ggml-org/llama.cpp discussion #21334). It was
resolved a few days later via issue #21325, and Ollama's audio path had its own
crash. If you want to try llama.cpp anyway, `LlamaCppGemmaEngine` below speaks
the OpenAI `input_audio` shape against a local llama-server; treat it as
unverified and check `doctor` output first.
"""

from __future__ import annotations

import base64
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol

from spine import (
    Chunk,
    GEMMA_MAX_CLIP_S,
    Segment,
    Spine,
    plan_chunks,
    stitch,
)
from audio import load_slice, write_slice_wav

# Google's documented ASR prompt for Gemma 4. Reproduced verbatim from
# https://ai.google.dev/gemma/docs/capabilities/audio because deviating from the
# trained prompt shape is a silent quality regression.
GEMMA_ASR_PROMPT = (
    "Transcribe the following speech segment in its original language. "
    "Follow these specific instructions for formatting the answer:\n"
    "* Only output the transcription, with no newlines.\n"
    "* When transcribing numbers, write the digits, i.e. write 1.7 and not one "
    "point seven, and write 3 instead of three."
)

# Verbatim variant. This is a *transcription policy* in the sense of
# docs/isls2027/03-whisper-concord-spec.md -- an explicit, researcher-authored
# instruction about what belongs in the transcript, rather than whatever the
# decoder happens to do. Policies live in policies/*.yaml; this is the fallback.
GEMMA_VERBATIM_PROMPT = (
    "Transcribe the following speech segment verbatim in its original language. "
    "Follow these specific instructions for formatting the answer:\n"
    "* Only output the transcription, with no newlines.\n"
    "* Include filled pauses (uh, um), repetitions, false starts and self-corrections "
    "exactly as spoken. Do not clean them up.\n"
    "* Mark a word spoken with clear emphatic stress by writing it in CAPITALS, "
    "like THIS. Mark at most the words that genuinely carry contrastive stress.\n"
    "* Never use asterisks, underscores or angle brackets for emphasis. Capitals "
    "only; see the _NOTATION_NOTE in policies.json for what asterisks break.\n"
    "* When transcribing numbers, write the digits."
)


@dataclass
class EngineResult:
    text: str
    meta: dict = field(default_factory=dict)


class Engine(Protocol):
    name: str

    def transcribe_segments(
        self, spine: Spine, segments: list[Segment], progress=None
    ) -> dict[str, EngineResult]: ...


# ------------------------------------------------------------- whisper ---


class WhisperEngine:
    """Whisper, constrained to the frozen spine.

    Whisper is run once per segment rather than once per file. That costs some
    throughput and buys the thing the experiment needs: Whisper cannot invent its
    own segmentation, so its output units are identical to Gemma's units.

    It also sidesteps a real failure mode. Koenecke et al. (2024), "Careless
    Whisper", found hallucination concentrates in long non-vocal stretches
    (arXiv:2402.08021). Diarized speech segments contain much less silence than
    a raw meeting recording, so per-segment decoding reduces the exposure.
    """

    def __init__(
        self,
        model_size: str = "large-v3",
        device: str = "auto",
        compute_type: str = "auto",
        initial_prompt: str | None = None,
        language: str | None = "en",
        backend: str = "auto",  # "faster-whisper" | "openai-whisper" | "auto"
    ):
        self.model_size = model_size
        self.device = device
        self.compute_type = compute_type
        self.initial_prompt = initial_prompt
        self.language = language
        self.backend = backend
        self.name = f"whisper-{model_size}"
        self._model = None
        self._impl = None

    def _load(self):
        if self._model is not None:
            return
        order = (
            ["faster-whisper", "openai-whisper"]
            if self.backend == "auto"
            else [self.backend]
        )
        errors = []
        for impl in order:
            try:
                if impl == "faster-whisper":
                    from faster_whisper import WhisperModel

                    device = self.device if self.device != "auto" else "auto"
                    ct = self.compute_type
                    if ct == "auto":
                        ct = "float16" if device in ("cuda", "auto") else "int8"
                    self._model = WhisperModel(
                        self.model_size, device=device, compute_type=ct
                    )
                    self._impl = impl
                    return
                if impl == "openai-whisper":
                    import whisper

                    self._model = whisper.load_model(self.model_size)
                    self._impl = impl
                    return
            except Exception as e:  # noqa: BLE001 - we report all attempts
                errors.append(f"{impl}: {type(e).__name__}: {e}")
        raise RuntimeError(
            "could not load any Whisper backend.\n  "
            + "\n  ".join(errors)
            + "\nTry: pip install faster-whisper"
        )

    def transcribe_segments(self, spine, segments, progress=None):
        self._load()
        audio = Path(spine.audio_path)
        out: dict[str, EngineResult] = {}
        for i, seg in enumerate(segments):
            samples = load_slice(audio, seg.start, seg.end)
            t0 = time.perf_counter()
            if self._impl == "faster-whisper":
                pieces, meta = self._run_faster(samples)
            else:
                pieces, meta = self._run_openai(samples)
            meta["elapsed_s"] = round(time.perf_counter() - t0, 3)
            meta["backend"] = self._impl
            out[seg.seg_id] = EngineResult(text=" ".join(pieces).strip(), meta=meta)
            if progress:
                progress(i + 1, len(segments), seg.seg_id)
        return out

    def _run_faster(self, samples):
        segs, info = self._model.transcribe(
            samples,
            language=self.language,
            initial_prompt=self.initial_prompt,
            vad_filter=False,          # the spine already did VAD/diarization
            condition_on_previous_text=False,  # avoid cross-segment contamination
            word_timestamps=True,
        )
        texts, words, logprobs = [], [], []
        for s in segs:
            texts.append(s.text.strip())
            logprobs.append(getattr(s, "avg_logprob", None))
            for w in getattr(s, "words", None) or []:
                words.append(
                    {
                        "word": w.word,
                        "start": w.start,
                        "end": w.end,
                        "prob": getattr(w, "probability", None),
                    }
                )
        clean = [lp for lp in logprobs if lp is not None]
        return texts, {
            "words": words,
            "avg_logprob": (sum(clean) / len(clean)) if clean else None,
            "language_probability": getattr(info, "language_probability", None),
        }

    def _run_openai(self, samples):
        res = self._model.transcribe(
            samples,
            language=self.language,
            initial_prompt=self.initial_prompt,
            condition_on_previous_text=False,
            word_timestamps=True,
            verbose=False,
        )
        words = []
        for s in res.get("segments", []):
            for w in s.get("words", []) or []:
                words.append(
                    {
                        "word": w.get("word"),
                        "start": w.get("start"),
                        "end": w.get("end"),
                        "prob": w.get("probability"),
                    }
                )
        lps = [s.get("avg_logprob") for s in res.get("segments", []) if s.get("avg_logprob") is not None]
        return [res.get("text", "").strip()], {
            "words": words,
            "avg_logprob": (sum(lps) / len(lps)) if lps else None,
        }


# --------------------------------------------------------------- gemma ---


class GemmaEngine:
    """Gemma 4 E2B / E4B via HF Transformers.

    Constraints taken from https://ai.google.dev/gemma/docs/capabilities/audio:
      * max clip length 30 s  -> segments longer than that are chunked and stitched
      * 25 tokens per second of audio (Gemma 4; 6.25 for Gemma 3n)
      * 16 kHz mono float32 in [-1, 1]  -> guaranteed by audio.load_slice()
      * requires transformers >= 5.10.1

    `prompt` is the transcription policy. Swapping it is the whole experiment:
    same audio, same spine, same model, different researcher-authored instruction.
    """

    MODELS = {
        "E2B": "google/gemma-4-E2B-it",
        "E4B": "google/gemma-4-E4B-it",
        "12B": "google/gemma-4-12B-it",
    }
    TOKENS_PER_AUDIO_SECOND = 25

    def __init__(
        self,
        variant: str = "E4B",
        prompt: str = GEMMA_ASR_PROMPT,
        policy_name: str = "default-asr",
        max_new_tokens: int = 512,
        device_map: str = "auto",
        dtype: str = "auto",
        max_clip_s: float = GEMMA_MAX_CLIP_S,
    ):
        if variant not in self.MODELS:
            raise ValueError(f"variant must be one of {sorted(self.MODELS)}")
        self.variant = variant
        self.model_id = self.MODELS[variant]
        self.prompt = prompt
        self.policy_name = policy_name
        self.max_new_tokens = max_new_tokens
        self.device_map = device_map
        self.dtype = dtype
        self.max_clip_s = max_clip_s
        self.name = f"gemma-4-{variant}/{policy_name}"
        self._pipe = None

    def _load(self):
        if self._pipe is not None:
            return
        try:
            import transformers
            from transformers import pipeline
        except ImportError as e:
            raise RuntimeError(
                "transformers not installed. Gemma 4 audio needs >= 5.10.1:\n"
                "  pip install -U 'transformers>=5.10.1' torch accelerate"
            ) from e

        ver = getattr(transformers, "__version__", "0")
        if _version_tuple(ver) < (5, 10, 1):
            raise RuntimeError(
                f"transformers {ver} is too old for Gemma 4 audio; need >= 5.10.1.\n"
                "  pip install -U 'transformers>=5.10.1'"
            )
        self._pipe = pipeline(
            task="any-to-any",
            model=self.model_id,
            device_map=self.device_map,
            dtype=self.dtype,
        )

    def transcribe_segments(self, spine, segments, progress=None):
        self._load()
        audio = Path(spine.audio_path)
        tmp = Path(spine.audio_path).parent / "_chunks"
        out: dict[str, EngineResult] = {}

        for i, seg in enumerate(segments):
            chunks = plan_chunks(seg, max_clip_s=self.max_clip_s)
            pieces, per_chunk = [], []
            t0 = time.perf_counter()
            for ch in chunks:
                txt = self._transcribe_chunk(audio, ch, tmp, seg.seg_id)
                pieces.append(txt)
                per_chunk.append(
                    {"index": ch.index, "start": ch.start, "end": ch.end, "text": txt}
                )
            out[seg.seg_id] = EngineResult(
                text=stitch(pieces),
                meta={
                    "model_id": self.model_id,
                    "policy": self.policy_name,
                    "prompt_sha": _sha8(self.prompt),
                    "n_chunks": len(chunks),
                    "chunks": per_chunk if len(chunks) > 1 else None,
                    "audio_tokens_est": int(seg.duration * self.TOKENS_PER_AUDIO_SECOND),
                    "elapsed_s": round(time.perf_counter() - t0, 3),
                },
            )
            if progress:
                progress(i + 1, len(segments), seg.seg_id)
        return out

    def _transcribe_chunk(self, audio: Path, ch: Chunk, tmp: Path, seg_id: str) -> str:
        samples = load_slice(audio, ch.start, ch.end)
        wav = write_slice_wav(samples, tmp / f"{seg_id}_{ch.index:03d}.wav")
        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": self.prompt},
                    {"type": "audio", "audio": str(wav)},
                ],
            }
        ]
        try:
            outputs = self._pipe(
                messages,
                return_full_text=False,
                generate_kwargs={"max_new_tokens": self.max_new_tokens},
            )
            text = outputs[0]["generated_text"]
        finally:
            wav.unlink(missing_ok=True)
        return _strip_turn_marker(text)


class LlamaCppGemmaEngine:
    """Gemma 4 audio via a local llama-server. UNVERIFIED -- see module docstring.

    Speaks the OpenAI `input_audio` content shape:
        {"type": "input_audio", "input_audio": {"data": <b64 wav>, "format": "wav"}}
    Requires llama-server started with `--mmproj <mmproj-gemma-4-*.gguf>`.
    """

    def __init__(
        self,
        base_url: str = "http://localhost:8080/v1",
        model: str = "gemma-4",
        prompt: str = GEMMA_ASR_PROMPT,
        policy_name: str = "default-asr",
        max_clip_s: float = GEMMA_MAX_CLIP_S,
        timeout: int = 300,
    ):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.prompt = prompt
        self.policy_name = policy_name
        self.max_clip_s = max_clip_s
        self.timeout = timeout
        self.name = f"gemma-llamacpp/{policy_name}"

    def transcribe_segments(self, spine, segments, progress=None):
        import requests

        audio = Path(spine.audio_path)
        tmp = audio.parent / "_chunks"
        out: dict[str, EngineResult] = {}
        for i, seg in enumerate(segments):
            pieces = []
            for ch in plan_chunks(seg, max_clip_s=self.max_clip_s):
                samples = load_slice(audio, ch.start, ch.end)
                wav = write_slice_wav(samples, tmp / f"{seg.seg_id}_{ch.index:03d}.wav")
                b64 = base64.b64encode(wav.read_bytes()).decode()
                wav.unlink(missing_ok=True)
                resp = requests.post(
                    f"{self.base_url}/chat/completions",
                    json={
                        "model": self.model,
                        "messages": [
                            {
                                "role": "user",
                                "content": [
                                    {"type": "text", "text": self.prompt},
                                    {
                                        "type": "input_audio",
                                        "input_audio": {"data": b64, "format": "wav"},
                                    },
                                ],
                            }
                        ],
                    },
                    timeout=self.timeout,
                )
                if resp.status_code != 200:
                    raise RuntimeError(
                        f"llama-server {resp.status_code}: {resp.text[:400]}\n"
                        "If this says 'audio input is not supported', your build "
                        "predates Gemma 4 audio support or --mmproj is missing."
                    )
                pieces.append(
                    _strip_turn_marker(
                        resp.json()["choices"][0]["message"]["content"]
                    )
                )
            out[seg.seg_id] = EngineResult(
                text=stitch(pieces),
                meta={"policy": self.policy_name, "prompt_sha": _sha8(self.prompt)},
            )
            if progress:
                progress(i + 1, len(segments), seg.seg_id)
        return out


# ------------------------------------------------------------- helpers ---


def _strip_turn_marker(text: str) -> str:
    """Gemma emits a trailing turn marker; the docs' own examples show it."""
    for marker in ("<turn|>", "<end_of_turn>", "<|turn|>"):
        text = text.replace(marker, "")
    return text.strip()


def _sha8(s: str) -> str:
    import hashlib

    return hashlib.sha256(s.encode("utf-8")).hexdigest()[:8]


def _version_tuple(v: str) -> tuple[int, ...]:
    parts: list[int] = []
    for chunk in v.split("."):
        digits = ""
        for c in chunk:
            if c.isdigit():
                digits += c
            else:
                break
        parts.append(int(digits) if digits else 0)
    return tuple(parts[:3]) or (0,)
