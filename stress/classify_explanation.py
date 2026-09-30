r"""
Classify each corpus video by whether it has spoken explanation between
repetitions of the target sentence, so the clip-granularity experiment
(doc 09 section 3.2) knows which videos support a real "reps-only, stripped
of explanation" condition and which don't.

Three buckets, built from data already on disk:

    spoken_explanation  -- substantial transcribed speech falls between two
                            consecutive repetitions. "reps-only" is a real,
                            distinct condition from "original" for these.
    no_explanation      -- the gaps between repetitions carry ~no speech.
                            "reps-only" and "original" are the same audio in
                            all but silence padding; building both is a
                            wasted condition.
    single_repetition   -- fewer than 2 occurrences located, so there is no
                            "between reps" to classify.

What this does NOT detect: video-only (on-screen text) explanation with no
spoken component. That is invisible to every audio-only method in this
project, not just this script. It will misclassify as no_explanation. State
that as a limitation, don't try to paper over it (see doc 09 section 3.2).

Usage
-----
    python classify_explanation.py                    # full corpus
    python classify_explanation.py --limit 5           # smoke test
"""

from __future__ import annotations

import argparse
import csv
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent / "transcribe2"))

from verify_stress import parse_vtt_words, locate, extend_phrase, WORD  # noqa: E402
import stress_from_audio as SFA  # noqa: E402

HERE = Path(__file__).resolve().parent
SDIR = HERE / "stress_search"

# A handful of words that show up as filler noise in captions/ASR (interjections,
# false starts) and shouldn't by themselves count as "explanation" if they're all
# that falls in a gap.
FILLER = {"uh", "um", "ah", "eh", "mm", "hmm", "okay", "ok", "so", "yeah", "and"}


def gap_word_count(all_words: list[tuple], t0: float, t1: float) -> int:
    """Non-filler words whose timestamp falls strictly between t0 and t1."""
    return sum(1 for w, t in all_words if t0 < t < t1 and w not in FILLER)


def occurrence_spans(occs: list[list[tuple]]) -> list[tuple[float, float]]:
    """(start, end) per occurrence, end estimated from the next word after it
    when available, else a fixed small pad -- exact end time isn't needed for
    classification, only "is there speech clearly between this and the next
    occurrence."""
    spans = []
    for occ in occs:
        start = occ[0][1]
        end = occ[-1][1] + 0.4  # pad past the last located word
        spans.append((start, end))
    return spans


def classify(all_words: list[tuple], occs: list[list[tuple]]) -> dict:
    if len(occs) < 2:
        return {"bucket": "single_repetition", "n_repetitions": len(occs),
                "max_gap_words": None, "mean_gap_words": None}
    spans = occurrence_spans(occs)
    gap_counts = []
    for i in range(len(spans) - 1):
        _, end_i = spans[i]
        start_next, _ = spans[i + 1]
        gap_counts.append(gap_word_count(all_words, end_i, start_next))
    max_gap = max(gap_counts)
    mean_gap = sum(gap_counts) / len(gap_counts)
    # Threshold: a handful of stray words (mis-timed caption boundary, a
    # trailing "okay") shouldn't flip the bucket. Real explanation between
    # repeats in this genre runs to a full sentence or more.
    bucket = "spoken_explanation" if max_gap >= 5 else "no_explanation"
    return {"bucket": bucket, "n_repetitions": len(occs),
            "max_gap_words": max_gap, "mean_gap_words": round(mean_gap, 1)}


def classify_youtube(video_id: str, phrase: str, min_repeats: int = 3) -> dict | None:
    vtt_path = SDIR / "captions" / f"{video_id}.en.vtt"
    if not vtt_path.exists():
        return None
    words = parse_vtt_words(vtt_path.read_text(encoding="utf-8", errors="replace"))
    phrase = extend_phrase(words, phrase, min_repeats)
    occs = locate(words, phrase)
    result = classify(words, occs)
    result.update({"video_id": video_id, "source": "youtube", "phrase": phrase})
    return result


def classify_local_audio(name: str, wav_path: Path, phrase: str,
                         min_repeats: int = 3) -> dict | None:
    """For sources with no caption track (TikTok): re-transcribe locally to
    get the full word stream, same as the measurement pass will need anyway."""
    if not wav_path.exists():
        return None
    words, _plain = SFA.transcribe(wav_path)
    phrase = extend_phrase(words, phrase, min_repeats)
    occs = locate(words, phrase)
    result = classify(words, occs)
    result.update({"video_id": name, "source": "tiktok", "phrase": phrase})
    return result


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    ap.add_argument("--limit", type=int, default=0, help="0 = all")
    ap.add_argument("--out", default="stress_search/explanation_classification.csv")
    args = ap.parse_args()

    rows: list[dict] = []

    # --- YouTube: 81 measured clips, real captions, no audio/GPU needed ---
    yt_rows = list(csv.DictReader(open(SDIR / "stress_verified.csv", encoding="utf-8")))
    if args.limit:
        yt_rows = yt_rows[: args.limit]
    for i, r in enumerate(yt_rows, 1):
        res = classify_youtube(r["video_id"], r["phrase"])
        if res:
            rows.append(res)
            print(f"  [{i}/{len(yt_rows)}] yt  {res['bucket']:<18} "
                  f"{res['n_repetitions']} reps  max_gap={res['max_gap_words']}  {r['video_id']}")
        else:
            print(f"  [{i}/{len(yt_rows)}] yt  NO CAPTIONS  {r['video_id']}")

    # --- TikTok: measured clips, need local re-transcription for full word stream ---
    tt_rows = list(csv.DictReader(open(SDIR / "tiktok_measured" / "other_sources.csv",
                                       encoding="utf-8")))
    if args.limit:
        tt_rows = tt_rows[: max(0, args.limit - len(yt_rows))]
    for i, r in enumerate(tt_rows, 1):
        vid = r["source"].rstrip("/").rsplit("/", 1)[-1]
        wav_candidates = list((SDIR / "tiktok").glob(f"{vid}*"))
        if not wav_candidates:
            print(f"  [{i}/{len(tt_rows)}] tt  NO LOCAL FILE  {vid}")
            continue
        src = wav_candidates[0]
        tmp_wav = Path(f"/tmp/classify_{vid}.wav")
        if src.suffix != ".wav":
            import subprocess
            subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(src),
                            "-ac", "1", "-ar", "16000", str(tmp_wav)])
            src = tmp_wav
        res = classify_local_audio(vid, src, r["phrase"])
        if res:
            rows.append(res)
            print(f"  [{i}/{len(tt_rows)}] tt  {res['bucket']:<18} "
                  f"{res['n_repetitions']} reps  max_gap={res['max_gap_words']}  {vid}")

    out_path = HERE / args.out
    cols = ["video_id", "source", "bucket", "n_repetitions", "max_gap_words",
            "mean_gap_words", "phrase"]
    with open(out_path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)

    from collections import Counter
    counts = Counter(r["bucket"] for r in rows)
    print(f"\n{len(rows)} classified -> {out_path}")
    for bucket, n in counts.most_common():
        print(f"  {bucket}: {n}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
