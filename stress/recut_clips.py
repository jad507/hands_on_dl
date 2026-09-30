r"""
Re-cut the corpus repetitions with boundaries measured on the audio (v3).

cut_clips.py cut each repetition from its first word's start - 0.15 s to its
LAST word's START + 0.6 s, using YouTube caption timings (or faster-whisper
start times for TikTok). Only start times were kept, and a stressed final word
is drawn out ("I never said she stole my MOOONEY"), so the human review found
many clips ending mid-word; caption timings are also only approximate. And some
phrases were fragments of the real sentence, which no trimming can fix.

This keeps the old locations only as a rough guide and measures each boundary:

  1. Phrase: the human's corrected sentence from the review page
     (labels/video_review.csv correct_phrase) if there is one, else the
     classifier's phrase as before.
  2. Rough location of every repetition: as cut_clips.py did (caption or
     whisper word stream, exact match), plus a match allowing one wrong word,
     so a caption misspelling in one reading no longer loses that reading.
  3. Refine: transcribe a window around each rough location with faster-whisper
     (word start AND end times), find the phrase in it, and cut from the first
     word's start to the last word's end.
  4. Snap each cut to the quietest 20 ms frame nearby (up to 0.35 s outward),
     so a cut lands in a pause rather than inside a sound.
  5. QA, recorded per clip: the new clip's own transcript contains the phrase
     (one word of slop), and its first and last 60 ms are quiet (edge_db: dB
     below the clip's loud level; near 0 = cut through speech).

Writes clips_v3/ and clip_manifest_v3.csv; v2 is untouched.

    python recut_clips.py                     # all videos
    python recut_clips.py --only SGyNGqXqWXY  # one video, to listen to
"""
from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

import numpy as np
import soundfile as sf

sys.path.insert(0, str(Path(__file__).resolve().parent))
from verify_stress import (HERE, LABELS, WORD, extend_phrase, latest_rows,  # noqa: E402
                           locate, parse_vtt_words)
from cut_clips import find_source_audio, to_wav  # noqa: E402

SDIR = HERE / "stress_search"
SR = 16000
FRAME = 0.02
_WHISPER = None


def whisper():
    global _WHISPER
    if _WHISPER is None:
        from faster_whisper import WhisperModel
        try:
            _WHISPER = WhisperModel("small.en", device="cuda", compute_type="float16")
        except Exception:
            _WHISPER = WhisperModel("small.en", device="cpu", compute_type="int8")
    return _WHISPER


def words_with_ends(audio: np.ndarray, offset: float = 0.0) -> list[tuple[str, float, float]]:
    """[(word, start, end)] from faster-whisper, times in the source's seconds."""
    segs, _ = whisper().transcribe(audio.astype(np.float32), word_timestamps=True,
                                   vad_filter=False, language="en")
    out, dur = [], len(audio) / SR
    for seg in segs:
        for w in seg.words or []:
            if not 0 <= w.start <= w.end <= dur + 0.1:
                continue  # whisper sometimes stamps words past the end of a short input
            for t in WORD.findall(w.word.lower().replace("’", "'")):
                out.append((t, offset + float(w.start), offset + float(w.end)))
    return out


def fuzzy_locate(words: list[tuple], phrase: str, max_miss: int) -> list[list[tuple]]:
    """Like verify_stress.locate, but a reading with up to max_miss wrong words
    (same length, first or last word right) still counts."""
    target = phrase.split()
    n = len(target)
    out, i = [], 0
    while i <= len(words) - n:
        span = words[i:i + n]
        hits = sum(a[0] == b for a, b in zip(span, target))
        if hits >= n - max_miss and (span[0][0] == target[0] or span[-1][0] == target[-1]):
            out.append(span)
            i += n
        else:
            i += 1
    return out


def slack(n: int) -> int:
    """Misheard words tolerated in an n-word sentence ("red roses" -> "red rolls")."""
    return 2 if n >= 8 else 1 if n >= 4 else 0


def best_match(words: list[tuple], target: list[str], near: float,
               not_before: float = 0.0, reach: float = 2.0) -> tuple[int, int] | None:
    """(i, j) of the phrase in a window's words: most words matched in order,
    then closest to the expected start. Spans of n-1..n+1 words are tried, so a
    dropped or inserted short word still matches. A span must start within
    `reach` s of the expected start and not before the previous reading ended,
    so two rough locations can't both claim the same reading."""
    import difflib
    n, best, key = len(target), None, None
    for i in range(len(words)):
        if words[i][1] < not_before or abs(words[i][1] - near) > reach:
            continue
        for L in (n - 1, n, n + 1):
            if L < 1 or i + L > len(words):
                continue
            span = [w for w, *_ in words[i:i + L]]
            m = sum(b.size for b in difflib.SequenceMatcher(None, span, target).get_matching_blocks())
            if m < n - slack(n):
                continue
            k = (m, span[0] == target[0], span[-1] == target[-1], -abs(words[i][1] - near), -L)
            if key is None or k > key:
                best, key = (i, i + L - 1), k
    return best


def rms_db(x: np.ndarray) -> np.ndarray:
    f = int(FRAME * SR)
    n = len(x) // f
    rms = np.sqrt((x[: n * f].reshape(n, f) ** 2).mean(1)) + 1e-9
    return 20 * np.log10(rms)


def snap(audio: np.ndarray, t: float, direction: int, reach: float = 0.35) -> float:
    """The quietest frame within `reach` seconds of t, looking outward only
    (direction -1 = earlier, for a start; +1 = later, for an end)."""
    dur = len(audio) / SR
    t = min(max(t, 0.0), dur)  # a negative time would slice from the END of the array
    lo, hi = (t - reach, t) if direction < 0 else (t, t + reach)
    lo, hi = max(0.0, lo), min(dur, hi)
    seg = audio[int(lo * SR): int(hi * SR)]
    if len(seg) < int(FRAME * SR):
        return t
    db = rms_db(seg)
    # earliest quietest frame for an end, latest for a start: keep as much of the word as possible
    k = int(np.argmin(db)) if direction > 0 else len(db) - 1 - int(np.argmin(db[::-1]))
    return lo + (k + 0.5) * FRAME


def edge_db(x: np.ndarray) -> tuple[float, float]:
    db = rms_db(x)
    loud = np.percentile(db, 95)
    return round(float(db[:3].max() - loud), 1), round(float(db[-3:].max() - loud), 1)


def rel(p: Path) -> str:
    """Manifest paths relative to the repo where possible (verify_stress.local_path
    resolves them on any machine), so a manifest carries no home directory."""
    try:
        return Path(p).resolve().relative_to(HERE).as_posix()
    except ValueError:
        return str(p)


def rough_occurrences(vid: str, source: str, phrase: str, corrected: bool, audio_path: Path):
    """Where each reading roughly is: [(start, last_word_start)]."""
    vtt = SDIR / "captions" / f"{vid}.en.vtt"
    if source == "youtube" and vtt.exists():
        words = parse_vtt_words(vtt.read_text(encoding="utf-8", errors="replace"))
    else:
        audio, _ = sf.read(audio_path, dtype="float32")
        words = [(w, s) for w, s, _ in words_with_ends(audio)]
    if not corrected:
        phrase = extend_phrase(words, phrase, 3)  # exactly as cut_clips.py did
    occs = locate(words, phrase)
    fuzzy = fuzzy_locate(words, phrase, slack(len(phrase.split()))) if len(phrase.split()) >= 4 else occs
    if len(fuzzy) > len(occs):
        occs = fuzzy
    return phrase, [(o[0][1], o[-1][1]) for o in occs]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    ap.add_argument("--classification", default="stress_search/explanation_classification_v2.csv")
    ap.add_argument("--clips-dir", default=str(SDIR / "clips_v3"))
    ap.add_argument("--manifest", default=str(SDIR / "clip_manifest_v3.csv"))
    ap.add_argument("--only", default=None, help="comma-separated video ids")
    ap.add_argument("--reviews", default=str(LABELS / "video_review.csv"),
                    help="review log with corrected sentences (label_server.py)")
    args = ap.parse_args()

    reviews = {k[0]: r for k, r in latest_rows(Path(args.reviews), "video_id").items()}
    rows = [r for r in csv.DictReader(open(HERE / args.classification, encoding="utf-8"))
            if r["bucket"] != "single_repetition"]
    if args.only:
        rows = [r for r in rows if r["video_id"] in args.only.split(",")]

    manifest, clips_dir = [], Path(args.clips_dir)
    for i, r in enumerate(rows, 1):
        vid, source, bucket = r["video_id"], r["source"], r["bucket"]
        fixed = reviews.get(vid, {}).get("correct_phrase", "").strip().lower()
        phrase = " ".join(WORD.findall(fixed.replace("’", "'"))) if fixed else r["phrase"]
        src = find_source_audio(vid, source)
        if src is None:
            print(f"  [{i}/{len(rows)}] {vid}: no source audio")
            continue
        out_dir = clips_dir / vid
        wav = src if src.suffix == ".wav" else to_wav(src, out_dir / "_source.wav")
        audio, sr = sf.read(wav, dtype="float32")
        if audio.ndim > 1:
            audio = audio.mean(1)
        if sr != SR:  # sources are 16 kHz mono already; resample defensively
            import librosa
            audio = librosa.resample(audio, orig_sr=sr, target_sr=SR)
        phrase, rough = rough_occurrences(vid, source, phrase, bool(fixed), wav)
        target = phrase.split()
        if len(rough) < 2:
            print(f"  [{i}/{len(rows)}] {vid}: {len(rough)} readings of '{phrase}' found, skipped")
            continue

        out_dir.mkdir(parents=True, exist_ok=True)
        for old in out_dir.glob("rep_*.wav"):  # a re-run may find fewer readings
            old.unlink()
        manifest.append({"video_id": vid, "condition": "original", "path": rel(src),
                         "phrase": phrase, "bucket": bucket})
        spans, n_ok = [], 0
        for j, (t0, t_last) in enumerate(rough):
            w0 = max(0.0, t0 - 1.0)
            w1 = min(len(audio) / SR, t_last + 2.5)
            win = words_with_ends(audio[int(w0 * SR): int(w1 * SR)], w0)
            m = best_match(win, target, t0, not_before=spans[-1][1] - 0.2 if spans else 0.0)
            if m is not None and win[m[1]][2] - win[m[0]][1] < 0.3:
                m = None  # whisper's word times went backwards (seen once); don't trust them
            if m is None:  # whisper can't find it: fall back to the rough cut, marked
                start, end, how = t0 - 0.15, t_last + 0.6, "rough"
            else:
                start, end, how = win[m[0]][1], win[m[1]][2], "refined"
                start, end = snap(audio, start - 0.05, -1), snap(audio, end + 0.05, +1)
            start, end = max(0.0, start), min(len(audio) / SR, end)
            clip = audio[int(start * SR): int(end * SR)]
            dst = out_dir / f"rep_{j:02d}.wav"
            sf.write(dst, clip, SR)
            spans.append((start, end))
            if len(clip) < 0.2 * SR:  # a degenerate span: keep the row, fail it
                qa, (e0, e1) = False, (0.0, 0.0)
            else:
                got = [w for w, *_ in words_with_ends(clip)]
                qa = sum(1 for w in target if w in got) >= len(target) - 1
                e0, e1 = edge_db(clip)
            n_ok += qa and max(e0, e1) <= -20
            manifest.append({"video_id": vid, "condition": f"rep_{j:02d}", "path": rel(dst),
                             "phrase": phrase, "bucket": bucket, "qa_pass": qa, "boundary": how,
                             "start_s": round(start, 2), "end_s": round(end, 2),
                             "edge_start_db": e0, "edge_end_db": e1})
        if bucket == "spoken_explanation":
            dst = out_dir / "reps_only.wav"
            gap = np.zeros(int(0.3 * SR), dtype=np.float32)
            parts = [x for s, e in spans for x in (audio[int(s * SR): int(e * SR)], gap)]
            sf.write(dst, np.concatenate(parts), SR)
            manifest.append({"video_id": vid, "condition": "reps_only", "path": rel(dst),
                             "phrase": phrase, "bucket": bucket})
        print(f"  [{i}/{len(rows)}] {vid}: {len(spans)} reps, {n_ok} clean"
              + (f"  (phrase from review: '{phrase}')" if fixed else ""), flush=True)

    cols = ["video_id", "condition", "path", "phrase", "bucket", "qa_pass", "boundary",
            "start_s", "end_s", "edge_start_db", "edge_end_db"]
    if args.only and Path(args.manifest).exists():
        # re-cutting a few videos (label_server.py does this when a sentence is
        # corrected): replace their rows, keep everyone else's, in the old order
        with open(args.manifest, newline="", encoding="utf-8") as fh:
            old = list(csv.DictReader(fh))
        new_by_vid: dict[str, list] = {}
        for m in manifest:
            new_by_vid.setdefault(m["video_id"], []).append(m)
        redone = set(new_by_vid)  # a video that found < 2 readings keeps its old clips
        merged, placed = [], set()
        for m in old:
            vid = m["video_id"]
            if vid not in redone:
                merged.append(m)
            elif vid not in placed:
                merged.extend(new_by_vid.get(vid, []))
                placed.add(vid)
        merged.extend(m for vid, ms in new_by_vid.items() if vid not in placed for m in ms)
        manifest = merged
    with open(args.manifest, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        w.writerows(manifest)
    reps = [m for m in manifest if m["condition"].startswith("rep_")]
    clean = [m for m in reps if str(m["qa_pass"]) == "True"
             and max(float(m["edge_start_db"]), float(m["edge_end_db"])) <= -20]
    print(f"\n{len(reps)} rep clips in {len({m['video_id'] for m in reps})} videos; "
          f"{len(clean)} pass transcript + quiet-edge QA -> {args.manifest}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
