r"""
Acoustic verification for the contrastive-stress corpus.

What this settles
-----------------
find_stress_videos.py proves that a sentence is REPEATED, by finding it several
times in the caption track. It cannot prove the repetitions differ, because the
captions are identical every time -- which is the whole point of doc 06, and
also the reason captions alone are not enough to build a corpus from.

This script closes that gap. For every repetition it measures which word the
speaker actually leaned on, and reports how many distinct words got the stress
across the video. The signature of a real demonstration is simple and strong:

    seven repetitions, seven different stressed words, one transcript.

A video where all seven repetitions stress the same word is somebody reading a
sentence seven times, not demonstrating contrastive stress. Nothing in the
caption track distinguishes those two cases. This does.

How stress is measured
----------------------
Three acoustic correlates, combined. English lexical and contrastive stress
shows up as some mixture of:

  - **Pitch** (fundamental frequency, F0). A stressed syllable is usually
    higher, or carries a pitch movement.
  - **Loudness** (intensity in dB).
  - **Length**. Stressed syllables are drawn out.

None is reliable alone. A speaker can emphasise by getting quieter and slower,
and pitch tracking fails on creaky or whispered voice. So each word gets a
z-score on all three within its own repetition, and the three are summed. Scoring
within the repetition matters: it removes the speaker's overall loudness and
register, so what is compared is which word stood out relative to its neighbours,
not how loud the recording was.

Word boundaries come from YouTube's own per-word caption timings, which are
present in the auto-caption VTT as inline <00:00:01.234> markers. This is not an
extra alignment step; it is data already sitting in the file that
find_stress_videos.py discarded.

What a result means
-------------------
`distinct_stress` is the count of different words that took top prominence
across the repetitions. Read it like this:

    distinct >= 5   excellent: a genuine multi-way contrastive demonstration
    distinct 3-4    usable: a partial demonstration, or a tracker slip on one
    distinct 2      weak
    distinct 1      not a demonstration; the same word every time

The stressed-word sequence is reported too, because the canonical demonstration
walks the stress left to right through the sentence, and seeing that pattern in
the output is much stronger evidence than the count alone.

Honest limits
-------------
Pitch tracking is imperfect on music beds, overlapping speech, and synthetic
voices. A word window from auto-captions can be off by a syllable. This gives you
a ranked shortlist with evidence attached, not a verdict; the top candidates
still deserve a human listening to them once.

Usage
-----
    python verify_stress.py --limit 5 --dry-run      # show what it would fetch
    python verify_stress.py --limit 20               # verify the top 20
    python verify_stress.py                          # everything in the CSV
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import os
import platform
import re
import shutil
import subprocess
import sys
import tempfile
import time
from collections import Counter
from pathlib import Path, PurePosixPath

HERE = Path(__file__).resolve().parent

WORD = re.compile(r"[a-z0-9']+")
CUE_TIME = re.compile(r"^(\d{2}:\d{2}:\d{2}\.\d{3})\s+-->\s+(\d{2}:\d{2}:\d{2}\.\d{3})")
INLINE_TS = re.compile(r"<(\d{2}:\d{2}:\d{2}\.\d{3})>")


def local_path(p: str) -> Path:
    """A manifest's audio path, resolved on THIS machine.

    Manifests (clip_manifest.csv and friends) record whatever path the machine
    that cut the clips used -- absolute Linux paths from Shiro, say -- and the
    audio itself is gitignored and copied between machines separately. A path
    that exists is used as is; otherwise everything from `stress_search` on is
    re-rooted at this checkout, so the same manifest works on Windows and Linux.
    Always absolute: callers symlink to it, and a relative target would resolve
    against the link's directory instead of the repo.
    """
    path = Path(p)
    if path.is_absolute() and path.exists():
        return path
    parts = PurePosixPath(p.replace("\\", "/")).parts
    if "stress_search" in parts:
        return HERE.joinpath(*parts[parts.index("stress_search"):])
    return HERE / p


# ------------------------------------------------------------- human labels
#
# label_server.py appends every click to a CSV under stress_search/labels/, so
# the files are logs, not tables: the latest row for a key is the answer, and
# changing your mind is just another row. Exclusions are applied by the analysis
# scripts at read time; no clip or result file is ever deleted for them.

LABELS = HERE / "stress_search" / "labels"


def latest_rows(path: Path, *key: str) -> dict[tuple, dict]:
    """The last row for each key in an append-only label log ({} if no file yet)."""
    if not path.exists():
        return {}
    with open(path, newline="", encoding="utf-8") as f:
        return {tuple(row[k] for k in key): row for row in csv.DictReader(f)}


def excluded_videos(path: Path | None = None) -> set[str]:
    """Videos the human review threw out (junk, not a stress demo, ...)."""
    rows = latest_rows(path or LABELS / "video_review.csv", "video_id")
    return {vid for (vid,), row in rows.items() if row["decision"] == "exclude"}


def bad_clips(path: Path | None = None) -> set[tuple[str, str]]:
    """(video_id, condition) of single clips marked unusable in a kept video."""
    rows = latest_rows(path or LABELS / "clip_review.csv", "video_id", "condition")
    return {key for key, row in rows.items() if row["bad"] == "1"}


# ----------------------------------------------------------- hardware/timing
#
# This corpus is being built on two machines with very different GPUs (a work
# desktop's RTX A2000 12GB and a home machine's RTX 5070 Ti 16GB), and a timing
# number is meaningless without knowing which machine produced it. gpu_info()
# shells out to nvidia-smi rather than importing torch, so it works in scripts
# (find_stress_videos.py) that have no GPU dependency of their own.

def gpu_info() -> dict:
    """Best-effort GPU name/VRAM/driver via nvidia-smi. Empty dict if unavailable."""
    try:
        p = subprocess.run(
            ["nvidia-smi", "--query-gpu=name,memory.total,driver_version",
             "--format=csv,noheader"],
            capture_output=True, text=True, timeout=10,
            encoding="utf-8", errors="replace")
    except (OSError, subprocess.TimeoutExpired):
        return {}
    if p.returncode != 0 or not p.stdout.strip():
        return {}
    parts = [s.strip() for s in p.stdout.strip().splitlines()[0].split(",")]
    if len(parts) != 3:
        return {}
    name, vram, driver = parts
    return {"gpu_name": name, "gpu_vram": vram, "gpu_driver": driver}


def hardware_info() -> dict:
    """Machine identity, for comparing run times across machines."""
    info = {
        "host": platform.node(),
        "os": platform.platform(),
        "python": platform.python_version(),
        "cpu": platform.processor() or platform.machine(),
        "cpu_count": os.cpu_count(),
    }
    info.update(gpu_info())
    try:
        import torch
        info["torch"] = torch.__version__
        info["cuda_available"] = torch.cuda.is_available()
    except ImportError:
        pass
    return info


def hms(s: str) -> float:
    h, m, sec = s.split(":")
    return int(h) * 3600 + int(m) * 60 + float(sec)


# --------------------------------------------------------- word-level timings

def parse_vtt_words(vtt: str) -> list[tuple[str, float]]:
    """Extract (word, start_seconds) from an auto-caption VTT.

    The inline <00:00:01.234> markers give the start of the word that follows.
    The first word of a cue starts at the cue's own start time.

    Auto-captions repeat each line as the next scrolls in, so a cue with no
    inline timings at all is a duplicate of what came before and is skipped;
    keeping those would double every word and wreck the windows.
    """
    words: list[tuple[str, float]] = []
    cue_start = 0.0
    pending_plain = False
    for raw in vtt.splitlines():
        m = CUE_TIME.match(raw.strip())
        if m:
            cue_start = hms(m.group(1))
            pending_plain = True
            continue
        line = raw.strip()
        if not line or line.startswith(("WEBVTT", "Kind:", "Language:")):
            continue
        if "<" not in line:
            # A plain restatement of the previous cue. Skip it.
            pending_plain = False
            continue
        pending_plain = False
        # Split on the inline timestamps, keeping which time each chunk follows.
        parts = INLINE_TS.split(line)
        t = cue_start
        for i, chunk in enumerate(parts):
            if i % 2 == 1:
                t = hms(chunk)
                continue
            clean = re.sub(r"</?c[^>]*>", " ", chunk)
            toks = WORD.findall(clean.lower().replace("\u2019", "'"))
            for j, w in enumerate(toks):
                words.append((w, t if j == 0 else t))
    return words


def locate(words: list[tuple[str, float]], phrase: str) -> list[list[tuple[str, float]]]:
    """Every occurrence of `phrase` in the word stream, with its word timings."""
    target = phrase.split()
    n = len(target)
    out = []
    i = 0
    while i <= len(words) - n:
        if [w for w, _ in words[i:i + n]] == target:
            out.append(words[i:i + n])
            i += n
        else:
            i += 1
    return out


# ------------------------------------------------------------------- audio

def download_audio(video_id: str, out: Path) -> Path | None:
    wav = out / f"{video_id}.wav"
    if wav.exists():
        return wav
    cmd = ["yt-dlp", "--no-update", "--no-warnings", "--ignore-config",
           "-f", "bestaudio/best", "-x", "--audio-format", "wav",
           "--postprocessor-args", "ExtractAudio:-ac 1 -ar 16000",
           "-o", str(out / f"{video_id}.%(ext)s"),
           f"https://www.youtube.com/watch?v={video_id}"]
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=300,
                           encoding="utf-8", errors="replace")
    except (subprocess.TimeoutExpired, OSError):
        return None
    return wav if wav.exists() else None


def prominence_profile(snd, occ: list[tuple[str, float]], tail: float = 0.45):
    """Per-word prominence for one repetition, z-scored within that repetition.

    Returns a list of dicts, or None if the audio could not be measured.
    """
    import numpy as np
    import parselmouth

    try:
        intensity = snd.to_intensity(minimum_pitch=75.0)
        pitch = snd.to_pitch()
    except Exception:
        return None

    bounds = []
    for k, (w, t) in enumerate(occ):
        end = occ[k + 1][1] if k + 1 < len(occ) else t + tail
        if end <= t:
            end = t + 0.08
        bounds.append((w, t, min(end, snd.get_total_duration())))

    rows = []
    for w, t0, t1 in bounds:
        if t1 - t0 < 0.03 or t0 >= snd.get_total_duration():
            rows.append({"word": w, "db": np.nan, "f0": np.nan, "dur": t1 - t0})
            continue
        # Half-open window. Sampling inclusive of t1 put the last sample inside
        # the NEXT word, so every word absorbed its successor's onset and the
        # loud word's neighbour tied with it. On a left-to-right walk that
        # systematically shifted the detected stress one word early.
        ts = np.linspace(t0, t1, 12, endpoint=False)
        dbs, f0s = [], []
        for t in ts:
            try:
                v = intensity.get_value(t)
                if v is not None and not np.isnan(v):
                    dbs.append(v)
            except Exception:
                pass
            try:
                f = pitch.get_value_at_time(t)
                if f is not None and not np.isnan(f) and f > 0:
                    f0s.append(f)
            except Exception:
                pass
        rows.append({"word": w,
                     "db": float(np.max(dbs)) if dbs else np.nan,
                     "f0": float(np.max(f0s)) if f0s else np.nan,
                     "dur": t1 - t0})

    def z(vals):
        a = np.array(vals, dtype=float)
        ok = ~np.isnan(a)
        if ok.sum() < 2:
            return np.zeros(len(a))
        mu, sd = a[ok].mean(), a[ok].std()
        if sd == 0:
            return np.zeros(len(a))
        out = (a - mu) / sd
        out[~ok] = 0.0
        return out

    zdb = z([r["db"] for r in rows])
    zf0 = z([r["f0"] for r in rows])
    zdu = z([r["dur"] for r in rows])
    for i, r in enumerate(rows):
        r["prominence"] = round(float(zdb[i] + zf0[i] + zdu[i]), 3)
        r["db"] = None if r["db"] != r["db"] else round(r["db"], 1)
        r["f0"] = None if r["f0"] != r["f0"] else round(r["f0"], 1)
        r["dur"] = round(r["dur"], 3)
    return rows


def stressed_indices(profiles: list[list[dict]]) -> list[int]:
    """Which word carried the stress in each repetition, corrected for the fact
    that some words are prominent every time.

    Taking argmax of raw prominence conflates two different things. Content
    words, and proper nouns especially, carry lexical stress in EVERY reading;
    function words never do. So the raw score keeps electing the same word no
    matter which one the speaker actually leaned on.

    Validation caught this. On the Baruch recording labelled as stressing
    "class", the detector chose "johnson's" -- which is indeed the loudest,
    highest word in the utterance, and is just as loud in the other reading of
    the same sentence. It is not what the speaker was contrasting.

    The fix uses structure we already have. Several repetitions of one sentence
    means each word can be scored against ITS OWN average across those
    repetitions. A word that is always prominent nets out to zero; a word that
    is unusually prominent in this particular reading stands out. What survives
    is contrastive stress rather than lexical stress.

    With a single repetition there is nothing to compare against, so this
    degrades to the raw score, which is then the best available.
    """
    if not profiles:
        return []
    n = min(len(p) for p in profiles)
    if len(profiles) < 2 or n == 0:
        return [max(range(len(p)), key=lambda k: p[k]["prominence"])
                for p in profiles]
    means = [sum(p[k]["prominence"] for p in profiles) / len(profiles)
             for k in range(n)]
    out = []
    for p in profiles:
        rel = [p[k]["prominence"] - means[k] for k in range(n)]
        out.append(max(range(n), key=lambda k: rel[k]))
    return out


def extend_phrase(words: list[tuple[str, float]], phrase: str,
                  min_repeats: int = 4, max_words: int = 20, keep_frac: float = 0.8) -> str:
    """Grow a detected phrase outward while it still repeats often enough.

    The repetition detector reports the phrase with the highest count, and a
    FRAGMENT of the target sentence can beat the sentence itself by one. On the
    public-domain VOA lesson it returned "he stole the money" (9 occurrences)
    rather than "i didn't say he stole the money" (8), because one reading was
    transcribed slightly differently and broke the longer match.

    That is not a harmless truncation. Every downstream number is computed over
    the phrase, so `coverage` -- distinct stressed words divided by words in the
    phrase -- came out as a perfect 1.0 for a four-word fragment of a seven-word
    sentence. The metric flattered the result precisely because the phrase was
    too short.

    Greedy extension fixes it: step outward one word at a time, keeping the
    extension whenever the longer phrase still occurs at least `min_repeats`
    times. That recovers the full sentence and stops at its real boundary, where
    the surrounding words start to vary.

    `min_repeats` alone is not a boundary test, though. With it at 3 (as the
    clip cutter used it), a word that happens to precede only 3 of 8 readings
    still clears it: X02JYzY5eO8 grew to "this i didn't say he stole her
    money", which locate() then found 3 times, and 5 of the 8 repetitions were
    never cut (38 of 90 corpus videos lost repetitions this way). So an
    extension must also keep at least `keep_frac` of the phrase's starting
    occurrences -- enough slack for the VOA case (8 of 9), none for 3 of 8.
    """
    cur = phrase.split()
    stream = [w for w, _ in words]

    def count(seq: list[str]) -> int:
        n, c, i = len(seq), 0, 0
        while i <= len(stream) - n:
            if stream[i:i + n] == seq:
                c += 1
                i += n
            else:
                i += 1
        return c

    keep = math.ceil(keep_frac * count(cur))
    changed = True
    while changed and len(cur) < max_words:
        changed = False
        for side in ("left", "right"):
            best_word, best_count = None, 0
            for i in range(len(stream) - len(cur) + 1):
                if stream[i:i + len(cur)] != cur:
                    continue
                j = i - 1 if side == "left" else i + len(cur)
                if 0 <= j < len(stream):
                    cand = ([stream[j]] + cur) if side == "left" else (cur + [stream[j]])
                    c = count(cand)
                    if c > best_count:
                        best_word, best_count = stream[j], c
            if best_word is not None and best_count >= max(min_repeats, keep):
                cur = ([best_word] + cur) if side == "left" else (cur + [best_word])
                changed = True
                if len(cur) >= max_words:
                    break
    return " ".join(cur)


def longest_walk(indices: list[int]) -> int:
    """Longest non-decreasing run through the stressed-word positions.

    The canonical demonstration walks the stress left to right: first word,
    second word, third word. Testing for a strictly monotone sequence looks like
    the right check and is too brittle in practice, because almost every real
    video opens with one neutral reading of the sentence before the walk starts,
    and pitch tracking slips on at least one repetition in most clips. Either
    breaks strict monotonicity and throws away a perfectly good example.

    The longest non-decreasing SUBSEQUENCE survives both: an intro reading and a
    couple of slips just fail to join the run, and the length of the run still
    says how much of the video is a left-to-right sweep.
    """
    if not indices:
        return 0
    best = [1] * len(indices)
    for i in range(1, len(indices)):
        for j in range(i):
            if indices[j] <= indices[i] and best[j] + 1 > best[i]:
                best[i] = best[j] + 1
    return max(best)


# -------------------------------------------------------------------- main

def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1],
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--search-dir", default="stress_search")
    ap.add_argument("--limit", type=int, default=0, help="0 = all")
    ap.add_argument("--min-repeats", type=int, default=4)
    ap.add_argument("--keep-audio", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    sdir = HERE / args.search_dir
    csv_path = sdir / "verified_candidates.csv"
    if not csv_path.exists():
        print(f"no candidates at {csv_path}; run find_stress_videos.py first")
        return 1

    rows = list(csv.DictReader(open(csv_path, encoding="utf-8")))
    rows = [r for r in rows if int(r["repeats"]) >= args.min_repeats]
    rows.sort(key=lambda r: -int(r["repeats"]))
    if args.limit:
        rows = rows[:args.limit]
    print(f"{len(rows)} candidates to verify\n")

    if args.dry_run:
        for r in rows:
            print(f"  x{r['repeats']:>2}  {r['phrase'][:52]:52s}  {r['url']}")
        return 0

    try:
        import parselmouth  # noqa: F401
    except ImportError:
        print("parselmouth is required:  pip install praat-parselmouth")
        return 1
    import parselmouth

    hw = hardware_info()
    print(f"host: {hw.get('host')}  "
          f"gpu: {hw.get('gpu_name', 'none detected')} ({hw.get('gpu_vram', '?')})\n")
    run_started = time.time()

    audio_dir = sdir / "audio"
    audio_dir.mkdir(exist_ok=True)
    work = Path(tempfile.mkdtemp()) if not args.keep_audio else audio_dir

    results, evidence = [], {}
    for i, r in enumerate(rows, 1):
        vid, phrase = r["video_id"], r["phrase"]
        vtt_path = sdir / "captions" / f"{vid}.en.vtt"
        if not vtt_path.exists():
            print(f"  [{i}/{len(rows)}] {vid}: no caption file, skipped")
            continue

        allwords = parse_vtt_words(vtt_path.read_text(encoding="utf-8",
                                                      errors="replace"))
        # The search reports the MOST-repeated phrase, which is routinely a
        # fragment of the sentence ("he stole the money" for "i didn't say he
        # stole the money"). Coverage divides by phrase length, so measuring the
        # fragment inflates every score. Grow it back first.
        phrase = extend_phrase(allwords, phrase, args.min_repeats)
        occs = locate(allwords, phrase)
        if len(occs) < args.min_repeats:
            print(f"  [{i}/{len(rows)}] {vid}: only {len(occs)} located, skipped")
            continue

        t_dl0 = time.perf_counter()
        wav = download_audio(vid, work)
        download_s = round(time.perf_counter() - t_dl0, 2)
        if wav is None:
            print(f"  [{i}/{len(rows)}] {vid}: audio download failed")
            continue

        try:
            snd = parselmouth.Sound(str(wav))
        except Exception as e:
            print(f"  [{i}/{len(rows)}] {vid}: unreadable audio ({e})")
            if not args.keep_audio:
                wav.unlink(missing_ok=True)
            continue

        t_m0 = time.perf_counter()
        profiles = []
        for occ in occs:
            prof = prominence_profile(snd, occ)
            if prof is not None:
                profiles.append(prof)
        # Score each word against its own average across the repetitions, so a
        # word that is loud in every reading does not win every reading.
        stressed = stressed_indices(profiles)
        measure_s = round(time.perf_counter() - t_m0, 2)

        if not args.keep_audio:
            wav.unlink(missing_ok=True)
        if len(profiles) < args.min_repeats:
            print(f"  [{i}/{len(rows)}] {vid}: measurement failed")
            continue

        toks = phrase.split()
        seq = [toks[k] for k in stressed]
        distinct = len(set(stressed))
        walk = longest_walk(stressed)

        res = {
            "video_id": vid, "url": r["url"], "title": r.get("title", ""),
            "phrase": phrase, "n_words": len(toks),
            "repetitions": len(profiles),
            "distinct_stress": distinct,
            "coverage": round(distinct / len(toks), 3),
            "walk": walk,
            "walk_frac": round(walk / len(stressed), 3),
            "stress_sequence": " > ".join(seq),
            "download_s": download_s,
            "measure_s": measure_s,
            "elapsed_s": round(download_s + measure_s, 2),
        }
        results.append(res)
        evidence[vid] = {"phrase": phrase, "profiles": profiles,
                         "stressed_index": stressed}

        flag = "***" if distinct >= 5 else (" **" if distinct >= 3 else "   ")
        print(f"  [{i}/{len(rows)}] {flag} {distinct} distinct of {len(profiles)} reps  "
              f"({res['elapsed_s']}s)  {vid}  {' > '.join(seq[:7])}", flush=True)

    if not args.keep_audio and work.exists() and work != audio_dir:
        shutil.rmtree(work, ignore_errors=True)

    results.sort(key=lambda r: (-r["distinct_stress"], -r["repetitions"]))
    cols = ["distinct_stress", "repetitions", "coverage", "walk", "walk_frac",
            "phrase", "stress_sequence", "url", "title", "n_words", "video_id",
            "download_s", "measure_s", "elapsed_s"]
    with open(sdir / "stress_verified.csv", "w", newline="",
              encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        w.writerows(results)
    (sdir / "stress_evidence.json").write_text(
        json.dumps(evidence, indent=1), encoding="utf-8")

    run_elapsed_s = round(time.time() - run_started, 1)
    (sdir / "run_manifest.json").write_text(json.dumps({
        **hw,
        "script": "verify_stress.py",
        "n_measured": len(results),
        "run_elapsed_s": run_elapsed_s,
        "mean_elapsed_s": round(sum(r["elapsed_s"] for r in results) / len(results), 2)
                          if results else None,
    }, indent=1), encoding="utf-8")

    strong = [r for r in results if r["distinct_stress"] >= 5]
    usable = [r for r in results if 3 <= r["distinct_stress"] < 5]
    print(f"\n=== {len(results)} measured in {run_elapsed_s}s "
          f"on {hw.get('host')} ({hw.get('gpu_name', 'no GPU')}) ===")
    print(f"  {len(strong)} strong (5+ distinct stressed words)")
    print(f"  {len(usable)} usable (3-4)")
    print(f"  written to {sdir / 'stress_verified.csv'}")
    for r in strong[:12]:
        print(f"  {r['distinct_stress']} of {r['n_words']}  {r['stress_sequence'][:70]}")
        print(f"           {r['url']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
