"""
Output emitters.

The VTT emitter exists to satisfy Concord's parser exactly. Every constraint
below was read out of concord/server/ingest/transcript.js, not guessed -- see
docs/isls2027/03-whisper-concord-spec.md for the full source reading.

  * `<v SPEAKER_00>text</v>` voice tags are one of only two speaker forms
    `cueSpeakerText` recognizes.
  * `stripTags()` is `s.replace(/<[^>]*>/g, "")`, so ANY other angle-bracket
    markup is silently deleted. Emphasis is therefore written with CAPITALS,
    never with tags and never with asterisks. Asterisks survive stripTags but
    suppress a sentence split two modules later in `unitize.js`, changing the
    unit count; see `_NOTATION_NOTE` in policies.json.
  * `mergeCues` fuses consecutive same-speaker cues when the gap is
    `<= maxMergeGapSeconds` (default 30). Since the merge test is `<=`, even a
    zero-gap setting merges touching cues -- so `epsilon_gap` shortens each cue
    by a hair to guarantee a strictly positive gap. Without this, Concord
    re-merges your frozen spine and N changes between conditions, which
    invalidates the entire comparison.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

from spine import Spine

EPSILON_GAP = 0.002  # 2 ms -- inaudible, but strictly > 0


def _ts(seconds: float) -> str:
    if seconds < 0:
        seconds = 0.0
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = seconds % 60
    return f"{h:02d}:{m:02d}:{s:06.3f}"


def to_vtt(
    spine: Spine,
    engine: str,
    out_path: Path,
    epsilon_gap: float = EPSILON_GAP,
    skip_empty: bool = True,
) -> Path:
    """Write one engine's transcript as WebVTT that Concord will not re-segment."""
    lines = ["WEBVTT", ""]
    lines.append(f"NOTE engine={engine}")
    lines.append(f"NOTE source={spine.source}")
    lines.append(f"NOTE diarizer={spine.diarizer}")
    lines.append(f"NOTE segments={len(spine.segments)}")
    lines.append("")

    n = 0
    for seg in spine.segments:
        text = (seg.text.get(engine) or "").strip()
        if not text and skip_empty:
            continue
        end = max(seg.start + 0.001, seg.end - epsilon_gap)
        # Angle brackets in the transcript would be eaten by stripTags AND would
        # corrupt the voice tag. Neutralize them here, visibly, not silently.
        text = text.replace("<", "(").replace(">", ")")
        lines.append(f"{_ts(seg.start)} --> {_ts(end)}")
        lines.append(f"<v {seg.speaker}>{text}</v>")
        lines.append("")
        n += 1

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"[emit] {out_path.name}: {n} cues")
    return out_path


def to_comparison_csv(spine: Spine, out_path: Path, engines: list[str] | None = None) -> Path:
    """One row per segment, one column per engine. The cross-engine diff, flat.

    This is the file to open first after a run: identical text across engines
    means the transcription policy made no difference for that segment, and
    differing text is exactly the population the study is about.
    """
    engines = engines or spine.engines()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(
            ["seg_id", "speaker", "start", "end", "duration"]
            + [f"text__{e}" for e in engines]
            + ["all_identical", "n_distinct"]
        )
        for seg in spine.segments:
            texts = [(seg.text.get(e) or "").strip() for e in engines]
            norm = [" ".join(t.lower().split()) for t in texts if t]
            distinct = len(set(norm))
            w.writerow(
                [
                    seg.seg_id,
                    seg.speaker,
                    f"{seg.start:.3f}",
                    f"{seg.end:.3f}",
                    f"{seg.duration:.3f}",
                ]
                + texts
                + [distinct <= 1, distinct]
            )
    print(f"[emit] {out_path.name}: {len(spine.segments)} rows x {len(engines)} engines")
    return out_path


def to_triage_csv(scores, out_path: Path) -> Path:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["seg_id", "total", "acoustic", "syntactic", "epistemic", "detail"])
        for s in sorted(scores, key=lambda x: x.total, reverse=True):
            w.writerow(
                [
                    s.seg_id,
                    f"{s.total:.4f}",
                    f"{s.acoustic:.4f}",
                    f"{s.syntactic:.4f}",
                    f"{s.epistemic:.4f}",
                    json.dumps(s.detail, default=str),
                ]
            )
    print(f"[emit] {out_path.name}: {len(scores)} scored segments")
    return out_path


def to_plain_text(spine: Spine, engine: str, out_path: Path) -> Path:
    lines = []
    for seg in spine.segments:
        text = (seg.text.get(engine) or "").strip()
        if text:
            lines.append(f"[{_ts(seg.start)}] {seg.speaker}: {text}")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return out_path
