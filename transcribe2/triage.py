"""
Non-circular triage: deciding which segments are worth a second, costlier pass.

The objection you raised is correct and worth stating precisely:

    "somehow figures out where sentences have ambiguity or emphasis that could
     change meaning, and then only shoves those lines to Gemma, but that seems
     like you'd have to already know the result before you send it for
     processing, lol"

Right -- if the router had to know *what the emphasis means*, it would be
circular. The escape is that you do not need the meaning. You need three things
that are all computable without it:

  1. ACOUSTIC   Is some word in this segment carrying unusual prosodic weight?
                Pure signal processing over F0 / intensity / duration. Answers
                "is something emphasized" without answering "what does it mean".

  2. SYNTACTIC  Is this the *kind* of sentence where emphasis placement changes
                truth conditions? Negation plus several focusable constituents
                is the classic shape: "I didn't say he stole the money."
                Computable from the Whisper text alone.

  3. EPISTEMIC  Did the cheap engine find this hard? Whisper already emits
                avg_logprob and per-word probabilities. Low confidence is a
                free signal that nobody uses.

A segment scores high when it is acoustically marked AND structurally capable of
carrying contrastive focus. That conjunction is the non-circular core: acoustics
says "something is stressed here", syntax says "stress here would matter", and
neither needed to know the answer first.

WHEN NOT TO USE THIS
--------------------
Do not use triage for the ISLS experiment. The experimental design in
docs/isls2027/03-whisper-concord-spec.md requires every segment to be processed
under every policy, because a policy that only ran on a *biased subset* of
segments cannot be compared to one that ran on all of them. Triage is a
production cost optimization. `run.py` therefore defaults to `--triage none`,
and turning it on prints a warning.

Its legitimate research use is the reverse: score every segment, run everything
anyway, and then check whether the triage score *predicts* where the engines
disagree. If it does, you have a cheap screening instrument, and that is a
publishable finding on its own.
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass, field
from pathlib import Path

from spine import Segment, Spine
from audio import load_slice, TARGET_SR

# ------------------------------------------------------------ syntactic ---

# Negation scopes over everything after it, which is what makes emphasis
# placement truth-conditional. "I never said she stole my money" has seven
# readings; "the meeting is at three" has essentially one.
NEGATION = re.compile(
    r"\b(not|n't|never|no|none|nobody|nothing|nowhere|neither|nor|cannot|can't|"
    r"won't|wouldn't|didn't|doesn't|don't|isn't|aren't|wasn't|weren't|hasn't|"
    r"haven't|hadn't|shouldn't|couldn't|mustn't)\b",
    re.I,
)

# Words that explicitly signal a contrast is being drawn.
CONTRAST = re.compile(
    r"\b(but|however|although|though|instead|rather|actually|really|whereas|"
    r"unlike|versus|vs|except|only|just|even|still|yet|anyway|regardless)\b",
    re.I,
)

# Reportative and modal verbs. "I didn't SAY it (I implied it)" is only available
# because 'say' contrasts with a family of neighbouring speech acts.
REPORTATIVE = re.compile(
    r"\b(said|say|says|told|tell|claimed|claim|stated|state|asked|ask|"
    r"suggested|suggest|implied|imply|mentioned|mention|thought|think|"
    r"believe|believed|know|knew|heard|hear)\b",
    re.I,
)

# Pronouns and possessives -- the cheapest focusable constituents in English.
FOCUSABLE_PRO = re.compile(
    r"\b(i|you|he|she|we|they|me|him|her|us|them|my|your|his|its|our|their|"
    r"mine|yours|hers|ours|theirs|this|that|these|those)\b",
    re.I,
)

HEDGE = re.compile(
    r"\b(maybe|perhaps|possibly|probably|sort of|kind of|i guess|i mean|"
    r"you know|somewhat|apparently|seems|seemed|might|maybe)\b",
    re.I,
)


@dataclass
class TriageScore:
    seg_id: str
    total: float
    acoustic: float
    syntactic: float
    epistemic: float
    detail: dict = field(default_factory=dict)

    def __repr__(self) -> str:  # pragma: no cover - cosmetic
        return (
            f"TriageScore({self.seg_id} total={self.total:.2f} "
            f"ac={self.acoustic:.2f} syn={self.syntactic:.2f} ep={self.epistemic:.2f})"
        )


def syntactic_score(text: str) -> tuple[float, dict]:
    """0..1 -- how much emphasis placement *could* change the meaning here.

    Knows nothing about what was actually emphasized. Purely: is this the shape
    of sentence where it would matter?
    """
    if not text or not text.strip():
        return 0.0, {"reason": "empty"}

    words = re.findall(r"[\w']+", text)
    n = len(words)
    if n < 3:
        return 0.0, {"reason": "too short", "n_words": n}

    has_neg = bool(NEGATION.search(text))
    n_contrast = len(CONTRAST.findall(text))
    has_report = bool(REPORTATIVE.search(text))
    n_focus = len(FOCUSABLE_PRO.findall(text))
    n_hedge = len(HEDGE.findall(text))

    score = 0.0
    score += 0.35 if has_neg else 0.0
    score += min(0.20, 0.10 * n_contrast)
    score += 0.15 if has_report else 0.0
    score += min(0.20, 0.05 * n_focus)
    score += min(0.10, 0.05 * n_hedge)

    # Negation + a reportative verb is the "I didn't SAY he stole it" shape --
    # the single most emphasis-sensitive construction in English. Bonus for it.
    if has_neg and has_report:
        score += 0.15

    # Very long segments dilute: one focusable pronoun in 200 words is noise.
    if n > 60:
        score *= 60.0 / n

    return min(1.0, score), {
        "n_words": n,
        "negation": has_neg,
        "contrast_markers": n_contrast,
        "reportative": has_report,
        "focusable_pronouns": n_focus,
        "hedges": n_hedge,
    }


# ------------------------------------------------------------- acoustic ---


def _rms_envelope(samples, sr: int, frame_ms: float = 25.0, hop_ms: float = 10.0):
    import numpy as np

    frame = max(1, int(sr * frame_ms / 1000))
    hop = max(1, int(sr * hop_ms / 1000))
    if len(samples) < frame:
        return np.zeros(0, dtype=np.float32)
    n = 1 + (len(samples) - frame) // hop
    idx = np.arange(frame)[None, :] + hop * np.arange(n)[:, None]
    frames = samples[idx]
    return np.sqrt(np.mean(frames.astype(np.float64) ** 2, axis=1) + 1e-12)


def _f0_track(samples, sr: int):
    """F0 contour. Uses parselmouth (Praat) if present, else librosa, else None.

    Degrading to None is fine -- the acoustic score falls back to intensity and
    duration, which are two of the three canonical prominence cues. It loses
    speakers who emphasize purely by pitch. `doctor` reports which path is live.
    """
    try:
        import numpy as np
        import parselmouth

        snd = parselmouth.Sound(samples.astype("float64"), sampling_frequency=sr)
        pitch = snd.to_pitch(time_step=0.01)
        f0 = pitch.selected_array["frequency"]
        f0[f0 == 0] = np.nan
        return f0, "parselmouth"
    except Exception:  # noqa: BLE001
        pass
    try:
        import numpy as np
        import librosa

        f0, _, _ = librosa.pyin(
            samples.astype("float32"),
            sr=sr,
            fmin=librosa.note_to_hz("C2"),
            fmax=librosa.note_to_hz("C7"),
            frame_length=1024,
        )
        return f0, "librosa"
    except Exception:  # noqa: BLE001
        return None, "none"


def acoustic_score(
    samples, sr: int = TARGET_SR, words: list[dict] | None = None
) -> tuple[float, dict]:
    """0..1 -- is some part of this segment unusually prosodically prominent?

    Measures *deviation within the segment*, not absolute level, so it is
    speaker-normalized for free: a quiet speaker who raises their voice scores
    the same as a loud one who raises theirs.

    Three cues, per the standard definition of prosodic prominence (F0, duration,
    amplitude -- Shattuck-Hufnagel & Turk 1996, as summarized in the ADEPT paper):
      * intensity peakiness  -- max RMS relative to the segment's own median
      * F0 range             -- pitch excursion across the segment
      * duration outliers    -- if word timings are supplied, per-word rate deviation
    """
    import numpy as np

    detail: dict = {}
    if samples is None or len(samples) < sr // 10:  # < 100 ms
        return 0.0, {"reason": "too short"}

    rms = _rms_envelope(samples, sr)
    if len(rms) < 5:
        return 0.0, {"reason": "too few frames"}

    voiced = rms[rms > np.percentile(rms, 25)]  # drop the silent tail
    med = float(np.median(voiced)) if len(voiced) else float(np.median(rms))
    peak = float(np.percentile(rms, 97))
    intensity_ratio = peak / (med + 1e-9)
    # ~2x over median is unremarkable in speech; ~6x is a genuine shout/stress.
    intensity_component = _squash((intensity_ratio - 2.0) / 4.0)
    detail["intensity_ratio"] = round(intensity_ratio, 3)

    f0, f0_backend = _f0_track(samples, sr)
    detail["f0_backend"] = f0_backend
    if f0 is not None:
        vals = np.asarray(f0, dtype="float64")
        vals = vals[~np.isnan(vals)]
        if len(vals) > 10:
            lo, hi = np.percentile(vals, [10, 90])
            semitones = 12.0 * math.log2(max(hi, 1e-6) / max(lo, 1e-6))
            # 4 semitones is ordinary declination; 12+ is a marked excursion.
            f0_component = _squash((semitones - 4.0) / 8.0)
            detail["f0_range_semitones"] = round(semitones, 2)
        else:
            f0_component = None
    else:
        f0_component = None

    dur_component = None
    if words:
        rates = []
        for w in words:
            token = (w.get("word") or "").strip()
            s, e = w.get("start"), w.get("end")
            if not token or s is None or e is None or e <= s:
                continue
            nchar = max(1, len(re.sub(r"[^\w]", "", token)))
            rates.append((e - s) / nchar)  # seconds per character
        if len(rates) >= 4:
            arr = np.asarray(rates)
            med_r = float(np.median(arr))
            mad = float(np.median(np.abs(arr - med_r))) + 1e-9
            z = float(np.max((arr - med_r) / (1.4826 * mad)))
            dur_component = _squash((z - 2.0) / 3.0)
            detail["max_duration_z"] = round(z, 2)

    parts = [c for c in (intensity_component, f0_component, dur_component) if c is not None]
    detail["components"] = {
        "intensity": _r(intensity_component),
        "f0": _r(f0_component),
        "duration": _r(dur_component),
    }
    return (sum(parts) / len(parts)) if parts else 0.0, detail


def epistemic_score(meta: dict) -> tuple[float, dict]:
    """0..1 from Whisper's own uncertainty. Free -- it already computed this."""
    detail = {}
    alp = meta.get("avg_logprob")
    if alp is None:
        return 0.0, {"reason": "no avg_logprob"}
    detail["avg_logprob"] = round(float(alp), 4)
    # Empirically ~ -0.2 is confident, ~ -1.0 is shaky.
    score = _squash((-float(alp) - 0.2) / 0.8)

    words = meta.get("words") or []
    probs = [w["prob"] for w in words if w.get("prob") is not None]
    if probs:
        import numpy as np

        low = float(np.mean([p < 0.5 for p in probs]))
        detail["frac_words_below_0.5"] = round(low, 3)
        score = max(score, _squash(low / 0.3))
    return score, detail


# --------------------------------------------------------------- combine ---


def score_segment(
    seg: Segment,
    audio_path: Path | None = None,
    text_engine: str = "",
    weights: tuple[float, float, float] = (0.45, 0.40, 0.15),
) -> TriageScore:
    """Combine the three signals. Defaults weight acoustics and syntax nearly
    equally and treat ASR uncertainty as a tiebreaker."""
    text = seg.text.get(text_engine, "") if text_engine else next(iter(seg.text.values()), "")
    meta = seg.meta.get(text_engine, {}) if text_engine else {}

    syn, syn_d = syntactic_score(text)
    ep, ep_d = epistemic_score(meta if isinstance(meta, dict) else {})

    ac, ac_d = 0.0, {"reason": "no audio supplied"}
    if audio_path is not None:
        try:
            samples = load_slice(Path(audio_path), seg.start, seg.end)
            ac, ac_d = acoustic_score(samples, TARGET_SR, (meta or {}).get("words"))
        except Exception as e:  # noqa: BLE001 - never let triage kill a run
            ac, ac_d = 0.0, {"error": f"{type(e).__name__}: {e}"}

    wa, ws, we = weights
    # Conjunction bonus: acoustically marked AND structurally sensitive is the
    # case the whole module exists to catch. Either alone is much weaker
    # evidence, so reward them landing together rather than just summing.
    base = wa * ac + ws * syn + we * ep
    total = min(1.0, base + 0.15 * (ac * syn))

    return TriageScore(
        seg_id=seg.seg_id,
        total=total,
        acoustic=ac,
        syntactic=syn,
        epistemic=ep,
        detail={"acoustic": ac_d, "syntactic": syn_d, "epistemic": ep_d},
    )


def score_spine(
    spine: Spine, text_engine: str = "", use_audio: bool = True
) -> list[TriageScore]:
    audio = Path(spine.audio_path) if use_audio else None
    return [score_segment(s, audio, text_engine) for s in spine.segments]


def select(
    scores: list[TriageScore], threshold: float = 0.5, top_k: int | None = None
) -> list[str]:
    ranked = sorted(scores, key=lambda s: s.total, reverse=True)
    if top_k is not None:
        return [s.seg_id for s in ranked[:top_k]]
    return [s.seg_id for s in ranked if s.total >= threshold]


def _squash(x: float) -> float:
    """Map any real to (0, 1) with a soft knee at 0. Keeps one loud outlier from
    saturating the score."""
    return 1.0 / (1.0 + math.exp(-3.0 * x))


def _r(x):
    return None if x is None else round(x, 3)
