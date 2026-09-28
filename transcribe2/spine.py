"""
The spine: a frozen, policy-independent segmentation of one recording.

This is the single most important object in the pipeline. Everything downstream
hangs off it, and nothing downstream is allowed to renegotiate it.

Why it exists
-------------
The research question is "what changes downstream when the transcription policy
changes?" That question is only answerable if the *units* stay fixed while the
*text* varies. If each engine picks its own segment boundaries, you cannot tell
whether a difference in the coded output came from the transcription policy or
from the units being different objects.

So: diarize ONCE, freeze the result, and make every ASR engine fill in text for
exactly those segments. Cross-engine comparison then joins on `seg_id` with no
alignment step at all.

The 30-second problem
---------------------
Gemma 4 E2B/E4B accept a maximum of 30 seconds of audio per clip
(https://ai.google.dev/gemma/docs/capabilities/audio). Real diarized turns are
routinely longer. So a segment may be *processed* as several chunks while
remaining ONE unit of analysis. `plan_chunks()` does that split; the engine
transcribes each chunk; `Segment.text` is the stitched result. The chunking is
an implementation detail of one engine and never leaks into the unit structure.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any

SCHEMA_VERSION = 1

# Gemma 4 E2B/E4B hard limit. Documented at
# https://ai.google.dev/gemma/docs/capabilities/audio ("Audio supports a maximum
# length of 30 seconds"). We plan to a smaller target so that a few hundred ms of
# resampling/padding slop cannot push a chunk over the cliff.
GEMMA_MAX_CLIP_S = 30.0
DEFAULT_CHUNK_TARGET_S = 27.0
DEFAULT_CHUNK_OVERLAP_S = 0.75


@dataclass
class Chunk:
    """A sub-slice of a Segment, sized to fit an engine's clip limit."""

    index: int
    start: float
    end: float

    @property
    def duration(self) -> float:
        return self.end - self.start


@dataclass
class Segment:
    """One unit of analysis. Boundaries are frozen; text is per-engine."""

    seg_id: str
    speaker: str
    start: float
    end: float
    # engine name -> transcript text, e.g. {"whisper": "...", "gemma-4-E4B": "..."}
    text: dict[str, str] = field(default_factory=dict)
    # engine name -> arbitrary per-engine detail (confidence, prosody notes, ...)
    meta: dict[str, Any] = field(default_factory=dict)

    @property
    def duration(self) -> float:
        return self.end - self.start

    def join_key(self, precision: int = 2) -> tuple[str, float]:
        """Time-anchored key. Stable across engines and across re-imports.

        Deliberately NOT derived from text: Concord's `unitId()` hashes unit text
        (server/core/ids.py), so any text-derived key changes the moment the
        transcription policy changes. See docs/isls2027/03-whisper-concord-spec.md.
        """
        return (self.speaker, round(self.start, precision))


@dataclass
class Spine:
    source: str          # original path or URL
    audio_path: str      # canonical 16 kHz mono wav
    duration: float
    segments: list[Segment] = field(default_factory=list)
    diarizer: str = "unknown"
    schema_version: int = SCHEMA_VERSION

    # ---------------------------------------------------------------- io ---

    def to_json(self, path: str | Path) -> None:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = asdict(self)
        path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    @classmethod
    def from_json(cls, path: str | Path) -> "Spine":
        raw = json.loads(Path(path).read_text(encoding="utf-8"))
        version = raw.get("schema_version", 0)
        if version != SCHEMA_VERSION:
            raise ValueError(
                f"spine schema version {version} != expected {SCHEMA_VERSION}; "
                "re-run diarization rather than migrating in place -- a spine is "
                "supposed to be immutable"
            )
        segs = [Segment(**s) for s in raw.pop("segments", [])]
        return cls(segments=segs, **raw)

    # ----------------------------------------------------------- queries ---

    def engines(self) -> list[str]:
        seen: list[str] = []
        for s in self.segments:
            for e in s.text:
                if e not in seen:
                    seen.append(e)
        return seen

    def missing(self, engine: str) -> list[Segment]:
        """Segments this engine has not transcribed yet. Powers resumable runs."""
        return [s for s in self.segments if not s.text.get(engine)]

    def speakers(self) -> list[str]:
        return sorted({s.speaker for s in self.segments})

    def validate(self) -> list[str]:
        """Structural problems that would silently corrupt a comparison."""
        problems: list[str] = []
        ids = [s.seg_id for s in self.segments]
        if len(ids) != len(set(ids)):
            problems.append("duplicate seg_id values")
        keys = [s.join_key() for s in self.segments]
        if len(keys) != len(set(keys)):
            problems.append(
                "duplicate (speaker, start) join keys -- cross-engine join is ambiguous"
            )
        for s in self.segments:
            if s.end <= s.start:
                problems.append(f"{s.seg_id}: non-positive duration")
            if s.start < 0:
                problems.append(f"{s.seg_id}: negative start")
        ordered = sorted(self.segments, key=lambda s: s.start)
        if [s.seg_id for s in ordered] != ids:
            problems.append("segments are not in start-time order")
        return problems


# ------------------------------------------------------------- chunking ---


def plan_chunks(
    segment: Segment,
    max_clip_s: float = GEMMA_MAX_CLIP_S,
    target_s: float = DEFAULT_CHUNK_TARGET_S,
    overlap_s: float = DEFAULT_CHUNK_OVERLAP_S,
) -> list[Chunk]:
    """Split one segment into engine-sized chunks.

    Guarantees, all of which are asserted in the tests:
      * every chunk is <= max_clip_s
      * chunks cover [segment.start, segment.end] with no gaps
      * consecutive chunks overlap by ~overlap_s (helps the model not clip a word
        at a boundary; the stitcher dedupes)
      * a segment that already fits returns exactly one chunk and is untouched
      * the split is deterministic -- same segment in, same chunks out, always
    """
    if target_s > max_clip_s:
        raise ValueError(f"target_s {target_s} exceeds max_clip_s {max_clip_s}")
    dur = segment.duration
    if dur <= max_clip_s:
        return [Chunk(index=0, start=segment.start, end=segment.end)]

    stride = target_s - overlap_s
    if stride <= 0:
        raise ValueError(f"overlap_s {overlap_s} must be < target_s {target_s}")

    chunks: list[Chunk] = []
    cursor = segment.start
    i = 0
    while cursor < segment.end:
        end = min(cursor + target_s, segment.end)
        chunks.append(Chunk(index=i, start=cursor, end=end))
        if end >= segment.end:
            break
        cursor += stride
        i += 1

    # A final sliver shorter than the overlap carries no new audio; fold it back.
    if len(chunks) >= 2 and chunks[-1].duration <= overlap_s:
        chunks.pop()
        chunks[-1] = Chunk(chunks[-1].index, chunks[-1].start, segment.end)
        if chunks[-1].duration > max_clip_s:  # pathological; re-split evenly
            return _even_split(segment, max_clip_s)
    return chunks


def _even_split(segment: Segment, max_clip_s: float) -> list[Chunk]:
    n = int(segment.duration // max_clip_s) + 1
    width = segment.duration / n
    return [
        Chunk(i, segment.start + i * width, segment.start + (i + 1) * width)
        for i in range(n)
    ]


def stitch(
    pieces: list[str], max_overlap_words: int = 8, min_overlap_words: int = 2
) -> str:
    """Join per-chunk transcripts, removing text duplicated across the overlap.

    Chunks overlap in time, so the model transcribes the boundary words twice.
    Find the longest suffix of the accumulated text that prefixes the next piece
    and drop the duplicate.

    `min_overlap_words` defaults to 2, and that default is load-bearing. A
    one-word match is not evidence of overlap -- English repeats single words
    constantly across a clause boundary. With a 1-word minimum,

        ["I never said that.", "That she stole it"]
        -> "I never said that. she stole it"          # word deleted

    because "that." and "That" normalize identically. Requiring two words fixes
    it. The chunk overlap is ~0.75 s, which is 2-3 words of ordinary speech, so
    genuine overlaps still match.

    Conservative by construction: when no overlap is detected it concatenates.
    A duplicated word is visible and recoverable; a deleted one is neither.
    """
    pieces = [p.strip() for p in pieces if p and p.strip()]
    if not pieces:
        return ""

    def norm(w: str) -> str:
        return w.lower().strip(".,!?;:\"'")

    out = pieces[0].split()
    for piece in pieces[1:]:
        words = piece.split()
        best = 0
        limit = min(max_overlap_words, len(out), len(words))
        for k in range(limit, min_overlap_words - 1, -1):
            if [norm(w) for w in out[-k:]] == [norm(w) for w in words[:k]]:
                best = k
                break
        out.extend(words[best:])
    return " ".join(out)


def make_seg_id(index: int, speaker: str, start: float) -> str:
    """Human-readable and stable. Index first so lexical sort == temporal sort."""
    return f"{index:05d}_{speaker}_{start:09.3f}"
