r"""
Find and measure contrastive-stress demonstrations in ANY audio source.

Why this exists alongside verify_stress.py
------------------------------------------
verify_stress.py depends on YouTube's auto-caption track for word timings. That
is fast and free and works for hundreds of videos, but it only works on YouTube,
and only where captions exist.

This script drops that dependency. It takes any URL yt-dlp can reach, or any
local file, transcribes it with Whisper to get word-level timings, and then runs
the same repetition search and stress measurement. Vimeo, Dailymotion, a
university phonetics page, a public-domain VOA lesson, a file on disk.

The demonstration hiding in the method
--------------------------------------
Running Whisper here is not merely a means to an end. When a speaker reads one
sentence seven ways and Whisper returns the same seven words seven times, the
transcript is the evidence for doc 06's claim, produced by the exact tool the
claim is about. The transcript is written out next to the measurements for that
reason.

So the output has two halves that say opposite-looking things about the same
audio:

    Whisper says:  seven identical sentences.
    The acoustics say: seven different stressed words.

That gap is the finding.

Usage
-----
    python stress_from_audio.py https://vimeo.com/123456
    python stress_from_audio.py https://voa-audio.voanews.eu/.../lesson.mp3
    python stress_from_audio.py local_clip.wav --phrase "i didn't say he stole the money"
    python stress_from_audio.py --urls urls.txt --out other_sources
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import platform
import re
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import verify_stress as V
from find_stress_videos import find_repeated_phrase

# TikTok is blocked by policy on the Windows work desktop, not on this machine.
# The refusal below is keyed to hostname rather than removed outright, so this
# stays safe if the same script is ever run on that machine again.
TIKTOK_ALLOWED_HOSTS = {"shiro"}

HERE = Path(__file__).resolve().parent

SAFE = re.compile(r"[^A-Za-z0-9._-]+")


def slug(s: str, n: int = 60) -> str:
    """A filesystem-safe name that is unique per source.

    The obvious version -- sanitise and truncate -- silently collided and
    corrupted a whole run. Five recordings from one teaching collection share a
    103-character URL prefix, so truncating to 60 characters mapped all of them
    to the same filename; fetch() saw the file already existed, returned the
    first download five times, and the validation reported that every recording
    stressed the same word and that two different sentences had the same
    transcript. Nothing errored.

    So: keep the tail of the path, which is the part that differs, and append a
    hash of the full source so two sources can never share a name.
    """
    tail = SAFE.sub("_", s.rstrip("/").rsplit("/", 1)[-1]).strip("_")
    digest = hashlib.sha256(s.encode("utf-8")).hexdigest()[:10]
    return f"{tail[:n]}_{digest}" if tail else digest


def fetch(url: str, out: Path) -> Path | None:
    """Download to a 16 kHz mono wav. Handles yt-dlp sites and direct media URLs."""
    stem = out / slug(url)
    wav = stem.with_suffix(".wav")
    if wav.exists():
        return wav
    cmd = ["yt-dlp", "--no-update", "--no-warnings", "--ignore-config",
           "-f", "bestaudio/best", "-x", "--audio-format", "wav",
           "--postprocessor-args", "ExtractAudio:-ac 1 -ar 16000",
           "-o", str(stem) + ".%(ext)s", url]
    try:
        subprocess.run(cmd, capture_output=True, text=True, timeout=600,
                       encoding="utf-8", errors="replace")
    except (subprocess.TimeoutExpired, OSError):
        return None
    if wav.exists():
        return wav
    # Direct media URL that yt-dlp declined: let ffmpeg take it.
    try:
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", url,
                        "-ac", "1", "-ar", "16000", str(wav)],
                       capture_output=True, timeout=600)
    except (subprocess.TimeoutExpired, OSError):
        return None
    return wav if wav.exists() else None


def transcribe(wav: Path, model_size: str = "small.en"):
    """Word-level transcript via faster-whisper.

    Returns [(word, start_seconds)], in the same shape verify_stress.locate
    expects from a caption file, so everything downstream is shared.
    """
    from faster_whisper import WhisperModel

    device, compute = "cuda", "float16"
    try:
        model = WhisperModel(model_size, device=device, compute_type=compute)
    except Exception:
        model = WhisperModel(model_size, device="cpu", compute_type="int8")

    segments, _info = model.transcribe(str(wav), word_timestamps=True,
                                       vad_filter=False)
    words, plain = [], []
    for seg in segments:
        for w in (seg.words or []):
            toks = V.WORD.findall(w.word.lower().replace("\u2019", "'"))
            for t in toks:
                words.append((t, float(w.start)))
            if toks:
                plain.append(w.word.strip())
    return words, " ".join(plain)


def analyse(wav: Path, words, phrase: str | None, min_repeats: int):
    """Locate the repeated sentence and measure which word carried the stress."""
    import parselmouth

    if phrase is None:
        # Reuse the structural detector: hand it the word stream shaped as the
        # (time, line) pairs it expects, one word per line.
        hit = find_repeated_phrase([(t, w) for w, t in words],
                                   min_repeats=min_repeats, max_span_s=1200.0)
        if not hit:
            return None
        # The detector returns the most-repeated phrase, which can be a fragment
        # of the target sentence. Grow it back out to the real boundary before
        # anything is measured over it.
        phrase = V.extend_phrase(words, hit["phrase"], min_repeats)

    occs = V.locate(words, phrase)
    if len(occs) < min_repeats:
        return None

    snd = parselmouth.Sound(str(wav))
    toks = phrase.split()
    profiles = []
    for occ in occs:
        prof = V.prominence_profile(snd, occ)
        if prof is not None:
            profiles.append(prof)
    if len(profiles) < min_repeats:
        return None
    stressed = V.stressed_indices(profiles)

    return {
        "phrase": phrase,
        "n_words": len(toks),
        "repetitions": len(profiles),
        "distinct_stress": len(set(stressed)),
        "coverage": round(len(set(stressed)) / len(toks), 3),
        "walk": V.longest_walk(stressed),
        "walk_frac": round(V.longest_walk(stressed) / len(stressed), 3),
        "stress_sequence": " > ".join(toks[k] for k in stressed),
        "_profiles": profiles,
        "_stressed": stressed,
        "_occurrence_times": [round(o[0][1], 2) for o in occs],
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1],
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("sources", nargs="*", help="URLs or local audio files")
    ap.add_argument("--urls", help="file with one URL per line")
    ap.add_argument("--phrase", default=None,
                    help="target sentence; omit to detect it automatically")
    ap.add_argument("--min-repeats", type=int, default=4)
    ap.add_argument("--model", default="small.en")
    ap.add_argument("--out", default="stress_search/other_sources")
    ap.add_argument("--keep-audio", action="store_true")
    args = ap.parse_args()

    srcs = list(args.sources)
    if args.urls:
        srcs += [ln.strip() for ln in Path(args.urls).read_text(
            encoding="utf-8").splitlines()
            if ln.strip() and not ln.strip().startswith("#")]
    if not srcs:
        ap.error("give at least one URL or file, or --urls")

    if any("tiktok" in s.lower() for s in srcs) and \
            platform.node().lower() not in TIKTOK_ALLOWED_HOSTS:
        print("refusing: TikTok is out of scope on this machine")
        return 1

    out = HERE / args.out
    out.mkdir(parents=True, exist_ok=True)
    (out / "transcripts").mkdir(exist_ok=True)
    audio_dir = out / "audio"
    audio_dir.mkdir(exist_ok=True)
    work = audio_dir if args.keep_audio else Path(tempfile.mkdtemp())

    hw = V.hardware_info()
    print(f"host: {hw.get('host')}  "
          f"gpu: {hw.get('gpu_name', 'none detected')} ({hw.get('gpu_vram', '?')})\n")
    run_started = time.time()

    rows, evidence = [], {}
    for i, src in enumerate(srcs, 1):
        name = slug(src)
        local = Path(src)
        t_fetch0 = time.perf_counter()
        wav = local if local.exists() else fetch(src, work)
        fetch_s = round(time.perf_counter() - t_fetch0, 2)
        if wav is None or not Path(wav).exists():
            print(f"  [{i}/{len(srcs)}] could not fetch {src}")
            continue

        print(f"  [{i}/{len(srcs)}] transcribing {name} ...", flush=True)
        t_tr0 = time.perf_counter()
        try:
            words, plain = transcribe(Path(wav), args.model)
        except Exception as e:
            print(f"      transcription failed: {e}")
            continue
        transcribe_s = round(time.perf_counter() - t_tr0, 2)
        (out / "transcripts" / f"{name}.txt").write_text(plain, encoding="utf-8")

        t_an0 = time.perf_counter()
        res = analyse(Path(wav), words, args.phrase, args.min_repeats)
        analyse_s = round(time.perf_counter() - t_an0, 2)
        if res is None:
            print("      no repeated sentence found")
            continue

        evidence[name] = {k: res[k] for k in res if k.startswith("_")}
        evidence[name]["phrase"] = res["phrase"]
        row = {k: v for k, v in res.items() if not k.startswith("_")}
        row["source"] = src
        row["fetch_s"] = fetch_s
        row["transcribe_s"] = transcribe_s
        row["analyse_s"] = analyse_s
        row["elapsed_s"] = round(fetch_s + transcribe_s + analyse_s, 2)
        rows.append(row)
        flag = "***" if res["distinct_stress"] >= 5 else " **"
        print(f"      {flag} {res['distinct_stress']} distinct of "
              f"{res['repetitions']} reps ({row['elapsed_s']}s): "
              f"{res['stress_sequence'][:70]}")

    if rows:
        cols = ["distinct_stress", "repetitions", "coverage", "walk",
                "walk_frac", "phrase", "stress_sequence", "n_words", "source",
                "fetch_s", "transcribe_s", "analyse_s", "elapsed_s"]
        with open(out / "other_sources.csv", "w", newline="",
                  encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=cols, extrasaction="ignore")
            w.writeheader()
            w.writerows(sorted(rows, key=lambda r: -r["distinct_stress"]))
        (out / "other_sources_evidence.json").write_text(
            json.dumps(evidence, indent=1), encoding="utf-8")
        print(f"\n{len(rows)} measured -> {out / 'other_sources.csv'}")
        print(f"Whisper transcripts kept in {out / 'transcripts'} "
              "-- these are the doc 06 evidence.")
    else:
        print("\nnothing measurable")

    run_elapsed_s = round(time.time() - run_started, 1)
    (out / "run_manifest.json").write_text(json.dumps({
        **hw,
        "script": "stress_from_audio.py",
        "model": args.model,
        "n_measured": len(rows),
        "run_elapsed_s": run_elapsed_s,
        "mean_transcribe_s": round(
            sum(r["transcribe_s"] for r in rows) / len(rows), 2) if rows else None,
    }, indent=1), encoding="utf-8")
    print(f"run took {run_elapsed_s}s on {hw.get('host')} "
          f"({hw.get('gpu_name', 'no GPU')}); manifest written to "
          f"{out / 'run_manifest.json'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
