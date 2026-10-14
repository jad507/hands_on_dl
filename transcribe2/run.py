#!/usr/bin/env python3
"""
One entrypoint. Give it a file path or a URL; it produces aligned transcripts.

    python run.py "C:\\audio\\meeting.mp4"
    python run.py "https://www.youtube.com/watch?v=..." --engines whisper,gemma-E4B
    python run.py clip.wav --engines gemma-E2B:verbatim,gemma-E2B:clean
    python run.py meeting.wav --resume            # skip already-transcribed segments
    python run.py --doctor                        # check the environment first

Pipeline:
    acquire -> canonical 16k mono wav -> diarize ONCE -> spine.json
      -> each engine fills text[engine] for the same frozen segments
      -> emit per-engine VTT + one comparison CSV

Every run is resumable: the spine on disk is the state. Kill it, rerun with
--resume, and it picks up the segments that have no text for that engine.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import audio as A
import diarize as D
import emit as E
from spine import Spine


def parse_engine_spec(spec: str, policies: dict) -> object:
    """'whisper' | 'whisper:large-v3' | 'gemma-E4B' | 'gemma-E4B:verbatim'"""
    import engines as ENG

    name, _, arg = spec.partition(":")
    name = name.strip().lower()

    if name in ("whisper", "w"):
        return ENG.WhisperEngine(model_size=arg or "large-v3")

    m = re.fullmatch(r"gemma-?(e2b|e4b|12b)", name)
    if m:
        variant = m.group(1).upper()
        policy = arg or "default-asr"
        if policy in policies:
            prompt = policies[policy]
        elif policy == "default-asr":
            prompt = ENG.GEMMA_ASR_PROMPT
        elif policy == "verbatim":
            prompt = ENG.GEMMA_VERBATIM_PROMPT
        else:
            raise SystemExit(
                f"unknown policy {policy!r}. Known: "
                + ", ".join(sorted(set(policies) | {"default-asr", "verbatim"}))
            )
        return ENG.GemmaEngine(variant=variant, prompt=prompt, policy_name=policy)

    if name in ("gemma-llamacpp", "llamacpp"):
        policy = arg or "default-asr"
        prompt = policies.get(policy, ENG.GEMMA_ASR_PROMPT)
        return ENG.LlamaCppGemmaEngine(prompt=prompt, policy_name=policy)

    raise SystemExit(f"unrecognized engine spec: {spec!r}")


def load_policies(path: Path | None) -> dict:
    """policies.json: {"policy_name": "prompt text", ...}

    Keeping policies in a file rather than in code is the point of the whole
    project: the transcription policy becomes a versioned, citable artifact
    instead of a string literal nobody can recover from the output.
    """
    if path is None or not path.exists():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise SystemExit(f"{path} must be a JSON object of name -> prompt")
    return data


def progress_printer(label: str):
    t0 = time.perf_counter()

    def _p(done: int, total: int, seg_id: str):
        el = time.perf_counter() - t0
        rate = done / el if el > 0 else 0
        eta = (total - done) / rate if rate > 0 else 0
        sys.stdout.write(
            f"\r  [{label}] {done}/{total} "
            f"({100*done/total:5.1f}%) {rate:.2f} seg/s  ETA {eta/60:5.1f}m  {seg_id[:28]:<28}"
        )
        sys.stdout.flush()
        if done == total:
            sys.stdout.write("\n")

    return _p


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(
        description="Audio/video -> aligned multi-engine transcripts",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    ap.add_argument("source", nargs="?", help="local media file path or URL")
    ap.add_argument("-o", "--outdir", default="out", help="output directory")
    ap.add_argument(
        "--engines",
        default="whisper",
        help="comma-separated. e.g. whisper,gemma-E4B or gemma-E2B:verbatim",
    )
    ap.add_argument("--diarize", choices=["auto", "pyannote", "vad"], default="auto")
    ap.add_argument("--max-speakers", type=int, default=None)
    ap.add_argument("--policies", type=Path, default=None, help="policies.json")
    ap.add_argument("--cookies", type=Path, default=None, help="cookies.txt for yt-dlp")
    ap.add_argument("--resume", action="store_true", help="skip segments already done")
    ap.add_argument("--limit", type=int, default=None, help="first N segments only")
    ap.add_argument("--strict-resample", action="store_true",
                    help="high-precision soxr resampling (Gemma docs recommend Fourier)")
    ap.add_argument("--triage", choices=["none", "score", "route"], default="none",
                    help="none (default, correct for experiments); score = compute "
                         "and save but process everything; route = ONLY process "
                         "high-scoring segments with the second engine")
    ap.add_argument("--triage-threshold", type=float, default=0.5)
    ap.add_argument("--doctor", action="store_true", help="check environment and exit")
    args = ap.parse_args(argv)

    if args.doctor:
        import doctor

        return doctor.main()

    if not args.source:
        ap.error("source is required (or use --doctor)")

    outdir = Path(args.outdir).resolve()
    outdir.mkdir(parents=True, exist_ok=True)
    policies = load_policies(args.policies)

    # ---------------------------------------------------------- acquire ---
    print(f"[1/5] acquiring {args.source}")
    got = A.acquire(args.source, outdir / "media", cookies=args.cookies)
    safe = re.sub(r'[<>:"/\\|?*]', "_", got.title)[:120]
    print(f"      {got.media_path.name}")

    wav = outdir / "audio" / f"{safe}.wav"
    if wav.exists():
        print(f"[2/5] canonical wav exists: {wav.name}")
    else:
        print("[2/5] converting to 16 kHz mono")
        A.to_canonical_wav(got.media_path, wav, strict_resample=args.strict_resample)
    sr, ch, dur = A.wav_info(wav)
    print(f"      {sr} Hz / {ch}ch / {dur/60:.1f} min")

    # ------------------------------------------------------------ spine ---
    spine_path = outdir / "spines" / f"{safe}.spine.json"
    if spine_path.exists() and args.resume:
        spine = Spine.from_json(spine_path)
        print(f"[3/5] loaded spine: {len(spine.segments)} segments (resume)")
    else:
        print(f"[3/5] diarizing ({args.diarize})")
        spine = D.build_spine(
            wav, got.source, method=args.diarize, max_speakers=args.max_speakers
        )
        spine.to_json(spine_path)
        print(f"      {len(spine.segments)} segments, {len(spine.speakers())} speakers")

    problems = spine.validate()
    if problems:
        print("      !! spine validation problems:")
        for p in problems:
            print(f"         - {p}")
        return 2

    over = [s for s in spine.segments if s.duration > 30.0]
    if over:
        longest = max(s.duration for s in over)
        print(
            f"      note: {len(over)} segments exceed Gemma's 30 s clip limit "
            f"(longest {longest:.1f} s) -- these will be chunked and stitched"
        )

    targets = spine.segments[: args.limit] if args.limit else spine.segments

    # ---------------------------------------------------------- engines ---
    specs = [s for s in args.engines.split(",") if s.strip()]
    print(f"[4/5] running {len(specs)} engine(s) over {len(targets)} segments")

    routed: set[str] | None = None
    for n, spec in enumerate(specs):
        engine = parse_engine_spec(spec, policies)
        todo = [s for s in targets if not (args.resume and s.text.get(engine.name))]

        if args.triage == "route" and n > 0 and routed is not None:
            before = len(todo)
            todo = [s for s in todo if s.seg_id in routed]
            print(f"      TRIAGE ROUTING: {before} -> {len(todo)} segments")
            print("      !! routed runs are NOT valid for the policy-comparison")
            print("      !! experiment -- the conditions saw different segments.")

        if not todo:
            print(f"  [{engine.name}] nothing to do")
            continue
        print(f"  [{engine.name}] {len(todo)} segments")
        results = engine.transcribe_segments(
            spine, todo, progress=progress_printer(engine.name)
        )
        for seg in spine.segments:
            r = results.get(seg.seg_id)
            if r is not None:
                seg.text[engine.name] = r.text
                seg.meta[engine.name] = r.meta
        spine.to_json(spine_path)  # checkpoint after every engine

        if args.triage in ("score", "route") and n == 0:
            import triage as T

            print("      scoring segments for triage")
            scores = T.score_spine(spine, text_engine=engine.name, use_audio=True)
            E.to_triage_csv(scores, outdir / f"{safe}.triage.csv")
            routed = set(T.select(scores, threshold=args.triage_threshold))
            print(
                f"      {len(routed)}/{len(scores)} segments score "
                f">= {args.triage_threshold}"
            )

    # ------------------------------------------------------------ emit ---
    print("[5/5] emitting")
    for eng in spine.engines():
        slug = re.sub(r"[^\w.-]", "_", eng)
        E.to_vtt(spine, eng, outdir / "vtt" / f"{safe}__{slug}.vtt")
        E.to_plain_text(spine, eng, outdir / "txt" / f"{safe}__{slug}.txt")
    if len(spine.engines()) > 1:
        E.to_comparison_csv(spine, outdir / f"{safe}.comparison.csv")

    print(f"\nDone. {spine_path}")
    if len(spine.engines()) > 1:
        _summarize(spine)
    return 0


def _summarize(spine: Spine) -> None:
    engines = spine.engines()
    identical = differing = empty = 0
    for seg in spine.segments:
        texts = [" ".join((seg.text.get(e) or "").lower().split()) for e in engines]
        present = [t for t in texts if t]
        if not present:
            empty += 1
        elif len(set(present)) == 1 and len(present) == len(engines):
            identical += 1
        else:
            differing += 1
    total = max(1, identical + differing)
    print("\n--- cross-engine agreement ---")
    print(f"  engines:   {', '.join(engines)}")
    print(f"  identical: {identical}/{total} ({100*identical/total:.1f}%)")
    print(f"  differing: {differing}/{total} ({100*differing/total:.1f}%)")
    if empty:
        print(f"  no output: {empty}")
    print("  -> see the comparison CSV; differing segments are the population")
    print("     the transcription-policy study is about.")


if __name__ == "__main__":
    raise SystemExit(main())
