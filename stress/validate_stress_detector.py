r"""
Measure the stress detector against labelled ground truth.

Why this is worth doing
-----------------------
verify_stress.py reports which word a speaker leaned on. Every number it
produces rests on that being right, and until now nothing checked it. The
detector was validated by me looking at one video and finding the output
plausible, which is not validation.

Baruch College's Tools for Clear Speech publishes something better: the same
sentence recorded several times, one file per stress placement, with the
intended stressed word written into the FILENAME.

    IHadTheTextBookYesterday - Stress I.mp3
    IHadTheTextBookYesterday - Stress TextBook.mp3
    IHadTheTextBookYesterday - Stress Yesterday.mp3

That is ground truth produced by speech professionals for teaching, which makes
it exactly the reference the detector needed. It is a small set -- five files in
two sentence groups -- so what comes out is an indication, not a confidence
interval. It is still the difference between a measured error rate and none.

The second thing this establishes
---------------------------------
Each group is the doc 06 claim in its purest available form. The recordings are
deliberately different from each other; a trained speaker produced each one to
place the stress somewhere specific. Run Whisper over a group and the
transcripts come back identical. Not similar. The same string.

Elsewhere that has to be argued. Here the source itself asserts the readings
differ, in the filenames, and the ASR still cannot tell them apart.

Usage
-----
    python validate_stress_detector.py
    python validate_stress_detector.py --model medium.en --keep-audio
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import tempfile
from pathlib import Path

import verify_stress as V
import stress_from_audio as A

HERE = Path(__file__).resolve().parent

BASE = ("https://tools-for-clear-speech.nyc3.cdn.digitaloceanspaces.com"
        "/Suprasegmentals/Rhythm/ContrastingClarifying/")

# (group, filename, the word the recording is labelled as stressing)
LABELLED = [
    ("i_had_the_textbook_yesterday",
     "IHadTheTextBookYesterday%20-%20Stress%20I.mp3", "i"),
    ("i_had_the_textbook_yesterday",
     "IHadTheTextBookYesterday%20-%20Stress%20TextBook.mp3", "textbook"),
    ("i_had_the_textbook_yesterday",
     "IHadTheTextBookYesterday%20-%20Stress%20Yesterday.mp3", "yesterday"),
    ("professor_johnsons_class_is_in_room_10",
     "ProfessorJohnsonsClassIsInRoom%20-%20Stress%2010.mp3", "10"),
    ("professor_johnsons_class_is_in_room_10",
     "ProfessorJohnsonsClassIsInRoom%20-%20Stress%20Class.mp3", "class"),
]

NUMBER_WORDS = {"10": {"ten", "10"}, "ten": {"ten", "10"}}


def label_matches(predicted: str, label: str) -> bool:
    """Compare a predicted word against a filename label, tolerantly.

    Whisper writes "textbook" or "text book" unpredictably, and a numeral may
    come back as a digit or as a word. Neither difference is the detector being
    wrong about which word was stressed, so neither should count as an error.
    """
    p = re.sub(r"[^a-z0-9]", "", predicted.lower())
    l = re.sub(r"[^a-z0-9]", "", label.lower())
    if p == l or p in l or l in p:
        return True
    return bool(NUMBER_WORDS.get(l, set()) & {p} or
                NUMBER_WORDS.get(p, set()) & {l})


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1],
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--model", default="small.en")
    ap.add_argument("--out", default="stress_search/validation")
    ap.add_argument("--keep-audio", action="store_true")
    args = ap.parse_args()

    try:
        import parselmouth
    except ImportError:
        print("parselmouth required")
        return 1

    out = HERE / args.out
    out.mkdir(parents=True, exist_ok=True)
    work = (out / "audio") if args.keep_audio else Path(tempfile.mkdtemp())
    work.mkdir(parents=True, exist_ok=True)

    per_file, groups = [], {}
    for group, fname, label in LABELLED:
        url = BASE + fname
        wav = A.fetch(url, work)
        if wav is None:
            print(f"  could not fetch {fname}")
            continue
        try:
            words, plain = A.transcribe(Path(wav), args.model)
        except Exception as e:
            print(f"  transcription failed for {fname}: {e}")
            continue
        if not words:
            print(f"  empty transcript for {fname}")
            continue

        snd = parselmouth.Sound(str(wav))
        prof = V.prominence_profile(snd, words)   # the whole file is one reading
        if prof is None:
            print(f"  could not measure {fname}")
            continue

        per_file.append({
            "group": group, "file": fname, "label": label,
            "transcript": " ".join(w for w, _ in words),
            "profile": prof,
        })
        groups.setdefault(group, []).append(" ".join(w for w, _ in words))

    # Scoring happens per GROUP, not per file. The files in a group are
    # repetitions of one sentence, which is exactly the structure
    # stressed_indices needs to cancel out words that are prominent every time.
    for g in {r["group"] for r in per_file}:
        members = [r for r in per_file if r["group"] == g]
        picks = V.stressed_indices([r["profile"] for r in members])
        for r, k in zip(members, picks):
            r["predicted"] = r["profile"][k]["word"]
            r["correct"] = label_matches(r["predicted"], r["label"])

    for r in per_file:
        mark = "OK " if r["correct"] else "MISS"
        print(f"  [{mark}] labelled '{r['label']}', detected "
              f"'{r['predicted']}'   {r['file'][:48]}", flush=True)

    if not per_file:
        print("nothing measured")
        return 1

    n = len(per_file)
    hits = sum(1 for r in per_file if r["correct"])

    print("\n=== detector accuracy ===")
    print(f"  {hits} of {n} correct ({100 * hits / n:.0f}%)")

    print("\n=== ASR collapse, per sentence group ===")
    collapse = {}
    for g, texts in groups.items():
        distinct = len(set(texts))
        collapse[g] = {"recordings": len(texts), "distinct_transcripts": distinct}
        verdict = ("IDENTICAL" if distinct == 1
                   else f"{distinct} distinct transcripts")
        print(f"  {g}: {len(texts)} recordings, deliberately different "
              f"stress -> {verdict}")
        if distinct == 1:
            print(f"      \"{texts[0]}\"")

    report = {
        "accuracy": {"n": n, "correct": hits, "rate": round(hits / n, 3)},
        "asr_collapse": collapse,
        "files": [{k: v for k, v in r.items() if k != "profile"}
                  for r in per_file],
        "profiles": {r["file"]: r["profile"] for r in per_file},
        "source": BASE,
        "note": ("Ground truth is the stressed word named in each filename, "
                 "published by Baruch College Tools for Clear Speech. Five "
                 "files in two groups: indicative, not a confidence interval."),
    }
    (out / "detector_validation.json").write_text(
        json.dumps(report, indent=1), encoding="utf-8")
    print(f"\nwritten to {out / 'detector_validation.json'}")

    if hits < n:
        print("\nMisses are worth reading rather than averaging away: check the "
              "profile in the JSON to see whether the intended word came second.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
