r"""
Cut the clip-granularity conditions for doc 09 section 3.2, from real audio
and the repetition timestamps `classify_explanation.py` already located.

For each classified video with audio on disk:

    rep_NN.wav     one clip per individual repetition (all buckets)
    reps_only.wav  repetitions concatenated, gaps stripped out
                   (spoken_explanation bucket only -- for no_explanation,
                   this would be near-identical to original.wav, a wasted
                   condition; see doc 09 section 3.2)

`original.wav` is not duplicated on disk -- the manifest just records the
path to the source audio, since it already exists and copying multi-hundred-
MB video files for every clip would burn disk for no reason.

Cutting is deterministic ffmpeg against real located timestamps, not a
model call -- the boundaries already exist and are more reliable than
asking a model to re-find them. What IS model-driven is the QA pass: after
cutting, ask Gemma-4 (spoon-fed the target sentence -- this is data prep,
not the measurement) whether each rep_NN.wav actually contains exactly one
clean utterance of it. That's the check against silent data-conversion
problems doc 09 asked for.

Idempotent: skips any clip that already exists, so this can be re-run as
`classify_explanation.py`'s output grows or as more source audio lands
(e.g. the background re-pull of the 81 YouTube originals).

Usage
-----
    python cut_clips.py                 # everything with audio available
    python cut_clips.py --limit 5       # smoke test
    python cut_clips.py --no-qa         # skip the Gemma QA pass (faster)
"""

from __future__ import annotations

import argparse
import csv
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from verify_stress import parse_vtt_words, locate, extend_phrase  # noqa: E402
import stress_from_audio as SFA  # noqa: E402

HERE = Path(__file__).resolve().parent
SDIR = HERE / "stress_search"
CLIPS_DIR = SDIR / "clips"


def find_source_audio(video_id: str, source: str) -> Path | None:
    """Locate whatever real audio/video we already have for this ID."""
    if source == "tiktok":
        hits = list((SDIR / "tiktok").glob(f"{video_id}*"))
        return hits[0] if hits else None
    # youtube: check the fresh-download dir, then the background re-pull dir
    for d, pats in [
        (SDIR / "youtube_video", ("*.mkv", "*.webm", "*.mp4")),
        (SDIR / "audio_repull", ("*.wav",)),
    ]:
        for pat in pats:
            hits = list(d.glob(f"{video_id}{pat[1:]}" if pat.startswith("*.") else pat))
            hits = [p for p in d.glob(pat) if p.stem == video_id]
            if hits:
                return hits[0]
    return None


def to_wav(src: Path, dst: Path) -> Path | None:
    if dst.exists():
        return dst
    dst.parent.mkdir(parents=True, exist_ok=True)
    r = subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(src),
                        "-ac", "1", "-ar", "16000", str(dst)])
    return dst if dst.exists() and r.returncode == 0 else None


def occurrences_for(video_id: str, source: str, phrase: str,
                    wav_for_words: Path) -> list[list[tuple]] | None:
    """Real per-word timestamps, same source the classifier used, so the
    cut boundaries match what was classified."""
    if source == "youtube":
        vtt = SDIR / "captions" / f"{video_id}.en.vtt"
        if vtt.exists():
            words = parse_vtt_words(vtt.read_text(encoding="utf-8", errors="replace"))
        else:
            words, _ = SFA.transcribe(wav_for_words)
    else:
        words, _ = SFA.transcribe(wav_for_words)
    phrase2 = extend_phrase(words, phrase, 3)
    occs = locate(words, phrase2)
    return occs if len(occs) >= 2 else None


def cut_reps(wav: Path, occs: list[list[tuple]], out_dir: Path) -> list[Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    paths = []
    for i, occ in enumerate(occs):
        start = max(0.0, occ[0][1] - 0.15)
        end = occ[-1][1] + 0.6
        dst = out_dir / f"rep_{i:02d}.wav"
        paths.append(dst)
        if dst.exists():
            continue
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error",
                        "-i", str(wav), "-ss", f"{start:.2f}", "-to", f"{end:.2f}",
                        "-ac", "1", "-ar", "16000", str(dst)])
    return paths


def cut_reps_only(wav: Path, occs: list[list[tuple]], out_dir: Path) -> Path:
    dst = out_dir / "reps_only.wav"
    if dst.exists():
        return dst
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        parts = []
        for i, occ in enumerate(occs):
            start = max(0.0, occ[0][1] - 0.15)
            end = occ[-1][1] + 0.4
            p = Path(td) / f"seg_{i:02d}.wav"
            subprocess.run(["ffmpeg", "-y", "-loglevel", "error",
                            "-i", str(wav), "-ss", f"{start:.2f}", "-to", f"{end:.2f}",
                            "-ac", "1", "-ar", "16000", str(p)])
            parts.append(p)
        listfile = Path(td) / "list.txt"
        listfile.write_text("\n".join(f"file '{p}'" for p in parts), encoding="utf-8")
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat",
                        "-safe", "0", "-i", str(listfile), "-c", "copy", str(dst)])
    return dst


def qa_check(wav: Path, phrase: str) -> bool | None:
    """Transcribe the cut and word-match it against the known target phrase.

    An earlier version of this asked Gemma-4 a subjective yes/no about the
    same clips. Spot-checked against a direct transcription, it was wrong:
    two clips it marked False turned out to be clean, complete, correct
    utterances on manual re-transcription. A yes/no self-report is the wrong
    tool for a question that already has a deterministic answer -- we know
    the target phrase, so just check the transcript against it. Allows one
    word of slop (ASR drops a short word occasionally) before failing.
    """
    words, _plain = SFA.transcribe(wav)
    got = [w for w, _ in words]
    want = phrase.split()
    matched = sum(1 for w in want if w in got)
    return matched >= len(want) - 1


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--no-qa", action="store_true")
    ap.add_argument("--classification",
                    default="stress_search/explanation_classification.csv")
    ap.add_argument("--clips-dir", default=str(CLIPS_DIR),
                    help="where to write clips; use a fresh one to re-cut (existing files are reused)")
    ap.add_argument("--manifest", default=str(SDIR / "clip_manifest.csv"))
    args = ap.parse_args()

    rows = list(csv.DictReader(open(HERE / args.classification, encoding="utf-8")))
    rows = [r for r in rows if r["bucket"] != "single_repetition"]
    if args.limit:
        rows = rows[: args.limit]

    manifest: list[dict] = []
    n_no_audio = 0
    for i, r in enumerate(rows, 1):
        vid, source, bucket, phrase = r["video_id"], r["source"], r["bucket"], r["phrase"]
        src = find_source_audio(vid, source)
        if src is None:
            n_no_audio += 1
            print(f"  [{i}/{len(rows)}] {vid}: no source audio yet, skipping")
            continue

        out_dir = Path(args.clips_dir) / vid
        wav = src if src.suffix == ".wav" else to_wav(src, out_dir / "_source.wav")
        if wav is None:
            print(f"  [{i}/{len(rows)}] {vid}: audio conversion failed")
            continue

        occs = occurrences_for(vid, source, phrase, wav)
        if occs is None:
            print(f"  [{i}/{len(rows)}] {vid}: could not re-locate repetitions, skipping")
            continue

        rep_paths = cut_reps(wav, occs, out_dir)
        manifest.append({"video_id": vid, "condition": "original", "path": str(src),
                         "phrase": phrase, "bucket": bucket})
        for j, p in enumerate(rep_paths):
            qa = None if args.no_qa else qa_check(p, phrase)
            manifest.append({"video_id": vid, "condition": f"rep_{j:02d}", "path": str(p),
                             "phrase": phrase, "bucket": bucket, "qa_pass": qa})

        if bucket == "spoken_explanation":
            ro = cut_reps_only(wav, occs, out_dir)
            manifest.append({"video_id": vid, "condition": "reps_only", "path": str(ro),
                             "phrase": phrase, "bucket": bucket})

        n_reps = len(rep_paths)
        qa_str = ""
        if not args.no_qa:
            n_pass = sum(1 for m in manifest[-n_reps:] if m.get("qa_pass") is True)
            qa_str = f"  QA {n_pass}/{n_reps} pass"
        print(f"  [{i}/{len(rows)}] {vid}: {n_reps} reps cut{qa_str}")

    out_path = Path(args.manifest)
    cols = ["video_id", "condition", "path", "phrase", "bucket", "qa_pass"]
    with open(out_path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        w.writerows(manifest)

    print(f"\n{len(manifest)} clip entries -> {out_path}")
    print(f"{n_no_audio} videos skipped (no source audio yet)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
