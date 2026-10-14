r"""
Classical (pre-neural) stress detection: acoustic features plus signal
processing, one utterance at a time, no training.

Why this exists
---------------
The poster compares an audio-native LLM against a "traditional automation"
baseline, meaning the signal-processing prosody tradition that predates
end-to-end models: measure pitch, loudness and duration, normalise, decide
which word stands out. WhiStress is not that (it is Whisper with a trained
head). Two methods from that tradition run here, on the same word
boundaries:

    wavelet   Wavelet Prosody Toolkit (Suni et al. 2017, Computer Speech &
              Language 45; asuni/wavelet_prosody_toolkit). Combines f0,
              energy and duration into one signal, takes its continuous
              wavelet transform, and scores each word by the strongest line
              of maximum amplitude inside it. Unsupervised; the method used to
              derive the Helsinki prosody corpus's prominence labels. Run
              through its own CLI (prosody_labeller) from its own venv
              (~/src/.venv-wavelet: it needs numpy>=2.4.6, .venv-transcribe
              pins 2.3.2), with its English config minus phone durations
              (wavelet_libritts_words.yaml says exactly what changed).
    praat     verify_stress.prominence_profile: per-word max intensity, max
              f0 and duration via Praat, z-scored within the one utterance,
              summed. The top word is the raw-prominence argmax -- the
              single-repetition path of stressed_indices(), with no
              cross-repetition correction.

Word boundaries for both come from faster-whisper small.en word timestamps
(stress_from_audio.py's setting). Classical systems used an HMM forced
aligner here; this is the one neural component, and it only says where words
start and end, never which is stressed.

Each method's per-word scores are aligned onto the manifest's reference
phrase (validate_whistress.align), and `top` is the phrase word it scores
highest. Rows flush per clip and resume on rerun. Per-clip work files (word
json, TextGrid, the toolkit's .prom output) persist under
stress_search/classical/<manifest name>/.

Usage
-----
    python measure_classical.py                                   # corpus rep clips
    python measure_classical.py --manifest stress_search/stresstest/manifest.csv \
        --conditions stresstest --out stress_search/classical_stresstest.csv
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from validate_whistress import align  # noqa: E402
from verify_stress import hardware_info, local_path, prominence_profile  # noqa: E402

WAVELET_VENV = Path(os.environ.get("WAVELET_VENV", Path.home() / "src" / ".venv-wavelet"))
WAVELET_CONFIG = HERE / "wavelet_libritts_words.yaml"
METHODS = ("wavelet", "praat")
FIELDS = ["video_id", "condition", "phrase", "qa_pass", "asr_transcription", "asr_words", "words_aligned",
          *[f"{m}_{k}" for m in METHODS for k in ("scores", "top_index", "top_word")], "seconds"]


def labeller() -> Path:
    """The toolkit's CLI inside its venv (Scripts\\*.exe on Windows, bin/ elsewhere)."""
    if os.name == "nt":
        return WAVELET_VENV / "Scripts" / "prosody_labeller.exe"
    return WAVELET_VENV / "bin" / "prosody_labeller"


def link_or_copy(src: Path, dst: Path) -> None:
    """Symlink where allowed; Windows refuses symlinks without Developer Mode, so copy there."""
    try:
        dst.symlink_to(src)
    except OSError:
        shutil.copyfile(src, dst)


def clip_id(r: dict) -> str:
    return f"{r['video_id']}__{r['condition']}"


def clean(word: str) -> str:
    return re.sub(r"^[^\w']+|[^\w']+$", "", word.strip())


def whisper_words(model, wav: str) -> list[dict]:
    segments, _ = model.transcribe(wav, word_timestamps=True, vad_filter=False)
    out = []
    for seg in segments:
        for w in seg.words or []:
            text = clean(w.word)
            if text:
                out.append({"word": text, "start": float(w.start), "end": float(w.end)})
    # Word intervals must not overlap in a TextGrid.
    for a, b in zip(out, out[1:]):
        a["end"] = min(a["end"], b["start"])
    return [w for w in out if w["end"] > w["start"]]


def write_textgrid(path: Path, words: list[dict], duration: float) -> None:
    """Praat long-format TextGrid, one `words` tier, gaps as empty intervals."""
    ivs, t = [], 0.0
    for w in words:
        if w["start"] > t:
            ivs.append((t, w["start"], ""))
        ivs.append((w["start"], w["end"], w["word"]))
        t = w["end"]
    end = max(duration, t)
    if end > t:
        ivs.append((t, end, ""))
    lines = ['File type = "ooTextFile"', 'Object class = "TextGrid"', "",
             "xmin = 0", f"xmax = {end}", "tiers? <exists>", "size = 1", "item []:",
             "    item [1]:", '        class = "IntervalTier"', '        name = "words"',
             "        xmin = 0", f"        xmax = {end}", f"        intervals: size = {len(ivs)}"]
    for i, (a, b, text) in enumerate(ivs, 1):
        lines += [f"        intervals [{i}]:", f"            xmin = {a}", f"            xmax = {b}",
                  '            text = "{}"'.format(text.replace('"', '""'))]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def read_prom(path: Path) -> list[tuple[str, float]]:
    """prosody_labeller output: file, start, end, word, prominence, boundary."""
    out = []
    for line in path.read_text(encoding="utf-8").splitlines():
        parts = line.split("\t")
        if len(parts) >= 5:
            out.append((parts[3], float(parts[4])))
    return out


def phrase_scores(phrase: list[str], pairs: list[tuple[str, float]]) -> tuple[list, int | None, int]:
    """Scores on reference-phrase positions (None where no word aligned), the
    top-scoring aligned position, and how many positions aligned."""
    # align() fills unmatched positions with 0, so wrap scores to tell them apart.
    marked = [(w, (1, s)) for w, s in pairs]
    mapped, n = align(phrase, marked)
    scores = [m[1] if isinstance(m, tuple) else None for m in mapped]
    have = [k for k, s in enumerate(scores) if s is not None]
    top = max(have, key=lambda k: scores[k]) if have else None
    return scores, top, n


def measure(args) -> None:
    import soundfile as sf

    prefixes = tuple(args.conditions.split(","))
    rows = [r for r in csv.DictReader(open(args.manifest, encoding="utf-8"))
            if r["condition"].startswith(prefixes)]
    if args.limit:
        rows = rows[:args.limit]
    done = set()
    if args.out.exists():
        done = {f"{r['video_id']}__{r['condition']}" for r in csv.DictReader(open(args.out, encoding="utf-8"))}
    todo = [r for r in rows if clip_id(r) not in done]
    work = args.work / Path(args.manifest).parent.name if Path(args.manifest).name == "manifest.csv" \
        else args.work / Path(args.manifest).stem
    work.mkdir(parents=True, exist_ok=True)

    hw = hardware_info()
    print(f"host: {hw.get('host')}  {len(todo)} of {len(rows)} clips to measure  work: {work}", flush=True)
    args.out.with_name(args.out.stem + "_run_manifest.json").write_text(json.dumps(
        {"hardware": hw, "wavelet_venv": str(WAVELET_VENV), "wavelet_config": WAVELET_CONFIG.name,
         "word_timestamps": "faster-whisper small.en", "started": time.strftime("%Y-%m-%d %H:%M:%S")},
        indent=2) + "\n")
    if not todo:
        return

    # 1. word boundaries -> <id>.words.json + <id>.TextGrid, wav symlinked beside them
    need = [r for r in todo if not (work / f"{clip_id(r)}.words.json").exists()]
    if need:
        from faster_whisper import WhisperModel
        try:
            model = WhisperModel("small.en", device="cuda", compute_type="float16")
        except Exception:
            model = WhisperModel("small.en", device="cpu", compute_type="int8")
        for i, r in enumerate(need, 1):
            cid = clip_id(r)
            wav = local_path(r["path"])
            link = work / f"{cid}.wav"
            if not link.exists():
                link_or_copy(wav, link)
            words = whisper_words(model, str(wav))
            write_textgrid(work / f"{cid}.TextGrid", words, sf.info(str(wav)).duration)
            (work / f"{cid}.words.json").write_text(json.dumps(words) + "\n", encoding="utf-8")
            if i % 50 == 0 or i == len(need):
                print(f"  word timestamps {i}/{len(need)}", flush=True)

    # 2. the toolkit's own batch CLI over every clip that lacks a .prom
    pending = [r for r in todo if not (work / f"{clip_id(r)}.prom").exists()]
    if pending:
        batch = work / "_batch"
        batch.mkdir(exist_ok=True)
        for p in batch.iterdir():
            p.unlink()
        for r in pending:
            link_or_copy(local_path(r["path"]), batch / f"{clip_id(r)}.wav")
        t0 = time.time()
        p = subprocess.run([str(labeller()), str(batch),
                            "-a", str(work), "-o", str(work), "-c", str(WAVELET_CONFIG), "-j", str(args.jobs)],
                           capture_output=True, text=True)
        n_err = p.stderr.count("Traceback")
        print(f"  prosody_labeller: {len(pending)} clips in {time.time() - t0:.0f}s, {n_err} failed", flush=True)
        if n_err:
            (work / "_labeller_stderr.log").write_text(p.stderr, encoding="utf-8")

    # 3. score both methods on the reference phrase
    import parselmouth
    new_file = not args.out.exists()
    with args.out.open("a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        if new_file:
            w.writeheader()
        for r in todo:
            t0 = time.time()
            cid = clip_id(r)
            words = json.loads((work / f"{cid}.words.json").read_text(encoding="utf-8"))
            phrase = r["phrase"].split()
            row = {"video_id": r["video_id"], "condition": r["condition"], "phrase": r["phrase"],
                   "qa_pass": r["qa_pass"], "asr_transcription": " ".join(x["word"] for x in words),
                   "asr_words": len(words)}
            prom = work / f"{cid}.prom"
            wav_pairs = read_prom(prom) if prom.exists() else []
            snd = parselmouth.Sound(str(local_path(r["path"])))
            prof = prominence_profile(snd, [(x["word"], x["start"]) for x in words]) if words else None
            praat_pairs = [(p["word"], p["prominence"]) for p in prof] if prof else []
            aligned = 0
            for m, pairs in (("wavelet", wav_pairs), ("praat", praat_pairs)):
                scores, top, n = phrase_scores(phrase, pairs)
                aligned = max(aligned, n)
                row[f"{m}_scores"] = json.dumps([None if s is None or not math.isfinite(s) else round(s, 3)
                                                 for s in scores])
                row[f"{m}_top_index"] = "" if top is None else top
                row[f"{m}_top_word"] = "" if top is None else phrase[top]
            row["words_aligned"] = aligned
            row["seconds"] = round(time.time() - t0, 3)
            w.writerow(row)
            f.flush()


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--manifest", default=str(HERE / "stress_search" / "clip_manifest.csv"))
    ap.add_argument("--conditions", default="rep_", help="comma-separated condition prefixes to measure")
    ap.add_argument("--out", type=Path, default=HERE / "stress_search" / "classical_reps.csv")
    ap.add_argument("--work", type=Path, default=HERE / "stress_search" / "classical")
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--jobs", type=int, default=8)
    measure(ap.parse_args())


if __name__ == "__main__":
    main()
