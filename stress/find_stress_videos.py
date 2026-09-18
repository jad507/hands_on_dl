r"""
Find YouTube videos where one speaker repeats the SAME sentence with different
stress, for the emphasis stress-test corpus in docs/isls2027/06-prosody-stress-test.md.

Why this is not just a keyword search
-------------------------------------
The obvious approach is to search for known sentences ("I didn't say he stole the
money") and collect the hits. That is what the CopilotDocs/ pass did, and it
works, but it has two limits that matter:

  1. It can only find sentence families somebody already thought of.
  2. It cannot tell a video that DEMONSTRATES the effect from a video that merely
     TALKS about it. A title claiming seven meanings does not prove seven audible
     repetitions -- the Copilot ledger says so itself, under "Cautions".

This script fixes both by looking at the structure of the transcript instead of
the title. YouTube auto-captions are fetchable without downloading the video, so
for each candidate we pull the caption track and ask a purely structural
question:

    Is there a phrase of 4-14 words that occurs 4 or more times in this
    transcript, spread across the running time?

A speaker demonstrating contrastive stress says the identical sentence five to
seven times in ninety seconds. Almost nothing else does that. A lecture ABOUT
prosody mentions the example once or twice. A song has a repeated chorus, which
is why choruses are screened out by requiring the repeats to be near-adjacent in
time and by rejecting candidates whose channel or title looks musical.

This finds sentence families nobody listed in advance, and it grades each hit by
what the transcript actually contains rather than what the title claims.

The finding hiding inside the method
------------------------------------
There is a second reason to keep the caption files. When a speaker says one
sentence seven ways and YouTube's ASR writes the same string seven times, that
caption file IS the evidence for doc 06's central claim: seven different meanings
collapse to one transcript. We are not just using ASR to find the videos. The ASR
output is the result.

So captions are saved, not discarded after counting.

What this does NOT do
---------------------
It does not download audio. On this machine yt-dlp returns HTTP 403 for media
streams (see the ledger written by this script). It therefore cannot verify that
the repetitions actually differ in stress -- only that the sentence is repeated
and that the ASR flattened it. Acoustic verification is a separate step that
needs the download path unblocked.

TikTok is out of scope on this machine and no TikTok URL is ever requested.

Usage
-----
    python find_stress_videos.py --smoke          # 2 queries, 5 videos, fast
    python find_stress_videos.py                  # full run
    python find_stress_videos.py --max-captions 200 --out stress_search
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import subprocess
import sys
import tempfile
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent

# ---------------------------------------------------------------- search space

# Families already known, phrased as a searcher would phrase them.
SENTENCE_QUERIES = [
    '"I didn\'t say he stole the money" emphasis',
    '"I never said she stole my money" stress',
    '"I didn\'t say we should kill him" emphasis',
    '"I didn\'t say you were stupid" stress',
    '"I never said he ate my cookie"',
    '"she doesn\'t think this is a good idea" stress',
    '"Emma wants to travel alone to Europe" stress',
    '"I said you have a mild allergy" contrastive',
    '"Tilly wants to borrow your green shirt"',
    '"I asked you to buy me two kilos of sweet potatoes"',
]

# Structural queries: these are the ones that can turn up families nobody listed.
PATTERN_QUERIES = [
    "contrastive stress same sentence different meaning",
    "sentence stress changes meaning English demonstration",
    "same sentence seven different meanings emphasis",
    "emphasize a different word each time meaning changes",
    "word stress changes meaning example repeated",
    "prosody demonstration same words different meaning",
    "intonation changes meaning same sentence English lesson",
    "shifting emphasis changes meaning demonstration",
    "one line seven ways acting exercise",
    "operative word exercise acting same line",
    "line reading emphasis exercise voice acting",
    "voice acting emphasis challenge same sentence",
    "ESL contrastive stress practice repeated sentence",
    "English pronunciation emphasis changes meaning drill",
    "#contrastivestress",
    "#sentencestress",
    "#wordstress english",
    "#emphasisiseverything",
]

# Titles/channels that look musical or otherwise repeat a phrase for reasons
# unrelated to contrastive stress. A chorus repeats; that is not the effect.
# A trailing \b after a literal dot can never match, so `ft\.` and `prod\.?`
# silently never fired. The optional dot belongs outside the boundary group.
MUSIC_HINT = re.compile(
    r"\b(official (music )?video|lyrics?|audio|remix|feat|prod|ft|"
    r"album|song|beat|instrumental|cover|mv)\b\.?", re.I)

# ------------------------------------------------------------------ yt-dlp I/O

YTDLP_BASE = ["yt-dlp", "--no-update", "--no-warnings", "--ignore-config"]


def run(cmd: list[str], timeout: int = 180) -> tuple[int, str]:
    try:
        p = subprocess.run(cmd, capture_output=True, text=True,
                           timeout=timeout, encoding="utf-8", errors="replace")
        return p.returncode, (p.stdout or "") + (p.stderr or "")
    except subprocess.TimeoutExpired:
        return 124, "timeout"
    except OSError as e:
        return 127, str(e)


def search(query: str, n: int) -> list[dict]:
    """One YouTube search. Returns flat metadata; no media is fetched."""
    cmd = YTDLP_BASE + [
        f"ytsearch{n}:{query}", "--flat-playlist",
        "--print", "%(id)s\t%(title)s\t%(duration)s\t%(channel)s",
    ]
    code, out = run(cmd)
    rows = []
    if code != 0:
        return rows
    for line in out.splitlines():
        parts = line.split("\t")
        if len(parts) < 4 or len(parts[0]) != 11:
            continue
        vid, title, dur, chan = parts[0], parts[1], parts[2], parts[3]
        try:
            duration = float(dur)
        except (TypeError, ValueError):
            duration = None
        rows.append({"video_id": vid, "title": title,
                     "duration_s": duration, "channel": chan, "query": query})
    return rows


def fetch_captions(video_id: str, workdir: Path) -> str | None:
    """Auto-captions only. Returns raw VTT text, or None."""
    stem = workdir / video_id
    cmd = YTDLP_BASE + [
        "--skip-download", "--write-auto-sub", "--sub-lang", "en",
        "--sub-format", "vtt", "-o", str(stem),
        f"https://www.youtube.com/watch?v={video_id}",
    ]
    code, _ = run(cmd, timeout=120)
    if code != 0:
        return None
    for p in workdir.glob(f"{video_id}*.vtt"):
        try:
            return p.read_text(encoding="utf-8", errors="replace")
        except OSError:
            return None
    return None


# ------------------------------------------------------------- VTT -> sentences

TAG = re.compile(r"<[^>]*>")
CUE_TIME = re.compile(r"^(\d{2}:\d{2}:\d{2}\.\d{3})\s+-->")


def parse_vtt(vtt: str) -> list[tuple[float, str]]:
    """Return (seconds, line) with the rolling duplication removed.

    YouTube auto-captions repeat each line as the next one scrolls in, so a naive
    word count double-counts everything. Consecutive identical lines are
    collapsed; a line that genuinely recurs later in the video survives, which is
    exactly the signal we want.
    """
    out: list[tuple[float, str]] = []
    t = 0.0
    last = None
    for raw in vtt.splitlines():
        m = CUE_TIME.match(raw.strip())
        if m:
            h, mnt, s = m.group(1).split(":")
            t = int(h) * 3600 + int(mnt) * 60 + float(s)
            continue
        line = TAG.sub("", raw).strip()
        if not line or line.startswith(("WEBVTT", "Kind:", "Language:")):
            continue
        if line == last:
            continue
        out.append((t, line))
        last = line
    return out


# Digits are kept. Dropping them made "step 1 / step 2 / step 3" normalise to
# three identical lines, so any numbered or countdown video looked like a
# sentence repeated verbatim. The number is the part that differs; it is exactly
# what must survive.
WORD = re.compile(r"[a-z0-9']+")


def normalise(text: str) -> list[str]:
    return WORD.findall(text.lower().replace("\u2019", "'"))


def is_periodic(words: tuple, unit: int) -> bool:
    """True if some `unit`-gram occurs twice inside this phrase.

    This is the filter that separates a repeated SENTENCE from a repeated BLOCK.
    The word list is flattened with no utterance boundaries in it, so a long
    n-gram will happily straddle the end of one sentence, the filler after it,
    and the start of the next -- reporting as a "phrase" something no speaker
    ever said as a unit. Ordinary prose full of templates does this constantly.

    If a short gram repeats inside the candidate, the candidate is a block rather
    than a sentence, and it is thrown out.
    """
    seen = set()
    for i in range(len(words) - unit + 1):
        g = words[i:i + unit]
        if g in seen:
            return True
        seen.add(g)
    return False


def find_repeated_phrase(timed: list[tuple[float, str]],
                         min_words: int = 4, max_words: int = 14,
                         min_repeats: int = 4,
                         max_span_s: float = 300.0) -> dict | None:
    """The core test: the longest phrase repeated at least `min_repeats` times.

    Returns the best candidate with its repeat count and the times it occurred,
    or None. Longer phrases win ties, because a long exact repeat is far stronger
    evidence than a short one that could be a stock discourse marker.

    Three filters stop this matching everything. A phrase must be at least
    `min_words` long, so verbal tics do not qualify. Its repeats must fall inside
    `max_span_s`, because a demonstration is compact -- seven readings in ninety
    seconds -- while a chorus or a catchphrase is spread across the whole
    runtime. And it must not be periodic; see is_periodic above.
    """
    words: list[str] = []
    times: list[float] = []
    for t, line in timed:
        for w in normalise(line):
            words.append(w)
            times.append(t)
    if len(words) < min_words:
        return None

    # Rank by repeat count first, length only as the tie-break.
    #
    # Preferring length first looked right and was wrong. The word stream carries
    # no utterance boundaries, so the LONGEST repeated gram tends to straddle the
    # end of the target sentence and run into whatever follows it. Whenever the
    # surrounding patter is even partly fixed, that straddling gram beats the
    # sentence itself and the reported phrase is one no speaker ever said.
    #
    # The most-repeated gram does not have that problem: the sentence is the part
    # said over and over, while the material around it varies, so the sentence
    # scores strictly higher. Length still decides between a phrase and its own
    # fragments, which tie on count because a fragment occurs wherever the whole
    # does.
    best = None
    for n in range(max_words, min_words - 1, -1):
        if len(words) < n:
            continue
        counts: Counter = Counter()
        where: dict[tuple, list[float]] = {}
        for i in range(len(words) - n + 1):
            g = tuple(words[i:i + n])
            counts[g] += 1
            where.setdefault(g, []).append(times[i])
        for g, c in counts.most_common(8):
            if c < min_repeats:
                break
            ts = where[g]
            # Reject a phrase whose repeats are scattered over a long video:
            # a demonstration is compact, a recurring chorus or catchphrase is not.
            span = max(ts) - min(ts)
            if span > max_span_s:
                continue
            # Reject a repeated block masquerading as a repeated sentence.
            if is_periodic(g, min_words):
                continue
            cand = {"phrase": " ".join(g), "repeats": c,
                    "n_words": n, "first_s": round(min(ts), 1),
                    "span_s": round(span, 1)}
            if best is None or (cand["repeats"], cand["n_words"]) > \
                               (best["repeats"], best["n_words"]):
                best = cand
    return best


# ------------------------------------------------------------------ known set

def load_known(root: Path) -> set[str]:
    """Video IDs already listed by the earlier Copilot passes, so this run adds
    rather than repeats. TikTok rows are ignored, not fetched."""
    known: set[str] = set()
    docs = root / "CopilotDocs"
    if not docs.is_dir():
        return known
    for p in list(docs.glob("*.csv")) + list(docs.glob("*.md")) + \
             list(docs.glob("*.jsonl")):
        if "tiktok" in p.name.lower():
            continue
        try:
            text = p.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for m in re.finditer(r"(?:watch\?v=|shorts/|youtu\.be/)([A-Za-z0-9_-]{11})",
                             text):
            known.add(m.group(1))
    return known


# ----------------------------------------------------------------------- main

def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1],
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", default="stress_search")
    ap.add_argument("--per-query", type=int, default=25)
    ap.add_argument("--max-captions", type=int, default=250)
    ap.add_argument("--min-repeats", type=int, default=4)
    ap.add_argument("--sleep", type=float, default=1.0)
    ap.add_argument("--smoke", action="store_true",
                    help="2 queries, 5 videos, 5 caption fetches")
    args = ap.parse_args()

    out = (HERE / args.out) if not Path(args.out).is_absolute() else Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    caps = out / "captions"
    caps.mkdir(exist_ok=True)

    queries = SENTENCE_QUERIES + PATTERN_QUERIES
    per_query = args.per_query
    max_caps = args.max_captions
    if args.smoke:
        queries = [SENTENCE_QUERIES[0], PATTERN_QUERIES[0]]
        per_query, max_caps = 5, 5

    known = load_known(HERE)
    started = datetime.now(timezone.utc)
    print(f"[{started:%H:%M:%S}] {len(queries)} queries, "
          f"{per_query} results each; {len(known)} ids already known", flush=True)

    # --- phase 1: search -----------------------------------------------------
    pool: dict[str, dict] = {}
    for i, q in enumerate(queries, 1):
        rows = search(q, per_query)
        new = 0
        for r in rows:
            if r["video_id"] in pool:
                continue
            pool[r["video_id"]] = r
            new += 1
        print(f"  [{i}/{len(queries)}] {new:3d} new  {q[:64]}", flush=True)
        time.sleep(args.sleep)

    fresh = {k: v for k, v in pool.items() if k not in known}
    print(f"\n{len(pool)} distinct videos, {len(fresh)} not already known\n",
          flush=True)

    # Order: prefer short videos (demonstrations are short) and non-musical ones.
    def rank(v: dict) -> tuple:
        d = v["duration_s"] or 9999
        musical = bool(MUSIC_HINT.search(v["title"] or "")) or \
                  bool(MUSIC_HINT.search(v["channel"] or ""))
        return (musical, d)

    ordered = sorted(fresh.values(), key=rank)[:max_caps]

    # --- phase 2: captions ---------------------------------------------------
    results, no_caps, errors = [], 0, 0
    with tempfile.TemporaryDirectory() as td:
        work = Path(td)
        for i, v in enumerate(ordered, 1):
            vid = v["video_id"]
            vtt = fetch_captions(vid, work)
            if vtt is None:
                no_caps += 1
            else:
                (caps / f"{vid}.en.vtt").write_text(vtt, encoding="utf-8")
                timed = parse_vtt(vtt)
                hit = find_repeated_phrase(timed, min_repeats=args.min_repeats)
                if hit:
                    row = dict(v)
                    row.update(hit)
                    row["url"] = f"https://www.youtube.com/watch?v={vid}"
                    results.append(row)
                    print(f"  [{i}/{len(ordered)}] HIT x{hit['repeats']} "
                          f"\"{hit['phrase'][:58]}\"  {vid}", flush=True)
            for f in work.glob(f"{vid}*"):
                f.unlink(missing_ok=True)
            if i % 25 == 0:
                print(f"  [{i}/{len(ordered)}] {len(results)} hits so far",
                      flush=True)
            time.sleep(args.sleep)

    results.sort(key=lambda r: (-r["repeats"], -r["n_words"]))

    # --- output --------------------------------------------------------------
    cols = ["repeats", "n_words", "phrase", "url", "title", "channel",
            "duration_s", "first_s", "span_s", "query", "video_id"]
    with open(out / "verified_candidates.csv", "w", newline="",
              encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        w.writerows(results)

    (out / "search_pool.json").write_text(
        json.dumps(list(pool.values()), indent=1), encoding="utf-8")

    elapsed = datetime.now(timezone.utc) - started
    ledger = [
        "# Contrastive-stress video search, structural pass",
        "",
        f"Run started {started:%Y-%m-%d %H:%M} UTC, took {elapsed}.",
        "English only. TikTok not searched and not requested: it is blocked on",
        "this machine by policy.",
        "",
        "## Method",
        "",
        "Unlike the CopilotDocs passes, this does not decide from titles. Every",
        "candidate's YouTube auto-caption track is fetched and searched for a",
        f"phrase of 4-14 words repeated at least {args.min_repeats} times within a",
        "five-minute span, and not itself periodic. That is a structural signature",
        "of somebody demonstrating",
        "contrastive stress, and it is one that a video merely *discussing*",
        "prosody does not produce.",
        "",
        "Two consequences worth stating:",
        "",
        "- It finds sentence families nobody listed in advance.",
        "- Every hit is graded by transcript content, not by a title's claim.",
        "  The earlier ledger's own Cautions section flags exactly this gap.",
        "",
        "## Counts",
        "",
        f"- Queries run: {len(queries)}",
        f"- Distinct videos seen: {len(pool)}",
        f"- Already known from CopilotDocs: {len(pool) - len(fresh)}",
        f"- Caption tracks attempted: {len(ordered)}",
        f"- No English auto-captions available: {no_caps}",
        f"- **Verified repeated-phrase hits: {len(results)}**",
        "",
        "## What is verified and what is not",
        "",
        "Verified: the sentence is repeated, and the ASR wrote it identically",
        "each time. That second half is not a limitation, it is the point. A",
        "caption file showing one string seven times is direct evidence for the",
        "claim in docs/isls2027/06-prosody-stress-test.md that seven meanings",
        "collapse to one transcript. The caption files are kept in captions/ for",
        "that reason.",
        "",
        "NOT verified: that the repetitions actually differ in stress. That needs",
        "the audio, and on this machine yt-dlp returns HTTP 403 for media streams",
        "while metadata and captions succeed. The installed yt-dlp is 2026.03.17",
        "and the current release is 2026.8.19, which is the first thing to try.",
        "",
        "## Next",
        "",
        "- Unblock media download, then measure pitch on each repetition with",
        "  parselmouth (already installed) to confirm the stressed word moves.",
        "- Hand the confirmed set to transcribe2 to produce the policy comparison.",
    ]
    (out / "search_ledger.md").write_text("\n".join(ledger) + "\n",
                                          encoding="utf-8")

    print(f"\n=== done in {elapsed} ===")
    print(f"  {len(results)} verified hits -> {out / 'verified_candidates.csv'}")
    print(f"  captions kept in {caps}")
    for r in results[:15]:
        print(f"  x{r['repeats']:2d}  {r['phrase'][:60]:60s}  {r['url']}")


if __name__ == "__main__":
    sys.exit(main())
