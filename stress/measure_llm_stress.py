r"""
The fourth measurement arm for doc 09: audio-native LLM transcription,
across every clip in `clip_manifest.csv` (every granularity condition --
original, reps_only, and each individual repetition -- for every classified
video), run through the same lens the acoustic detector and local Whisper
already get.

Two prompts, both applied to every clip, matching doc 09 section 3.1:

    plain      "Transcribe this audio verbatim, word for word." No mention
               of stress or emphasis. The fair, blind baseline -- directly
               comparable to local Whisper and the original source captions,
               since none of those get a hint either.
    general    The non-task-specific meaning-preserving prompt (doc 09
               section 3.1). Explicitly permits marking emphasis/pauses/
               overlaps in safe, Concord-surviving notation, but never
               mentions the target sentence or "contrastive stress." This
               is what actually tests whether the model does anything with
               the latitude it's given.

Both use the official low-level API (AutoProcessor + AutoModelForMultimodalLM
+ enable_thinking=True + Google's bundled sampling defaults), the settings
validated correct earlier in this session -- not the high-level pipeline()
wrapper, and not silently-defaulted generation kwargs.

For each (clip, prompt) pair this records, structurally rather than by eye:

    collapsed        does the transcript, compared against the OTHER
                      repetitions' transcripts of the same video/condition,
                      come out identical (the ASR-flattening finding)?
    markup_applied    does the output contain *asterisk emphasis*,
                      **bold**, (N.N) pause notation, [bracket] overlap
                      notation, or a trailing-hyphen cutoff? (general
                      prompt only -- plain has no reason to produce any)
    n_words_matched   how many of the target phrase's words appear in the
                      transcript, out of the total -- a cheap proxy for
                      "did it even get the sentence right" independent of
                      the markup question.

Usage
-----
    python measure_llm_stress.py                  # everything in the manifest
    python measure_llm_stress.py --limit 10        # smoke test
    python measure_llm_stress.py --condition original,reps_only  # subset
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from verify_stress import hardware_info, local_path  # noqa: E402

HERE = Path(__file__).resolve().parent
SDIR = HERE / "stress_search"

PLAIN_PROMPT = "Transcribe this audio verbatim, word for word."

GENERAL_PROMPT = '''Transcribe this audio. Your goal is a transcript that captures not just
the words but the meaning as it was actually communicated -- tone of
voice carries information that plain text normally throws away, and for
this transcript, it shouldn't.

Where the way something was said changes or clarifies what it means --
a word spoken with unusual emphasis, a phrase said sarcastically, a
pause that changes how a sentence lands -- represent that using plain-
text formatting, applied only where the audio genuinely supports it:

  - *italics* or **bold** for a word or phrase spoken with notable
    emphasis or stress
  - (1.2) for a perceptible pause, with its approximate length in
    seconds; (.) for a brief pause with no clear length
  - a trailing hyphen for a word that is cut off or restarted, e.g. "wor-"
  - [brackets] around words where two speakers are talking over each
    other

Do not use HTML or XML-style tags (anything in < > will be silently
deleted downstream). Do not add commentary, summaries, or explanation --
output only the transcript itself. If nothing in a stretch of audio
warrants this kind of marking, transcribe it as plain text; do not force
markup where the audio doesn't support it.'''

# The prompt's four notations. The cut-off rule was `\w-\b`, which matches
# ordinary hyphenated words ("well-known") and never a real trailing cut-off
# ("wor- "); all 20 plain-prompt "markup" hits in the first full run were that.
# summarize_llm_markup.py recounts existing CSVs by notation from the text.
MARKUP_RE = re.compile(r"\*\*[^*\n]+?\*\*|(?<!\*)\*[^*\n]+?\*(?!\*)|\(\d+(?:\.\d+)?\)|\(\.\)|\[[^\]\n]+\]"
                       r"|\b\w+-(?=\s|$|[,.;:!?\"'])")

MODEL_ID = "google/gemma-4-E2B-it"
PLE_CPU = False
_MODEL = None
_PROCESSOR = None
_DEVICE = None


def _load_model():
    """Same loading as reproduce_stresstest_gemma._load(). With PLE_CPU the
    per-layer embedding table (E4B: 2.82B params, 5.25 GiB -- a lookup table,
    no matrix math) stays in RAM and everything else goes to the GPU; that is
    what lets E4B fit in 16 GB. Outputs are bit-identical to all-GPU."""
    global _MODEL, _PROCESSOR, _DEVICE
    if _MODEL is None:
        from transformers import AutoProcessor, AutoModelForMultimodalLM
        _PROCESSOR = AutoProcessor.from_pretrained(MODEL_ID)
        if not PLE_CPU:
            _MODEL = AutoModelForMultimodalLM.from_pretrained(MODEL_ID, dtype="auto", device_map="auto")
            _DEVICE = _MODEL.model.language_model.embed_tokens.weight.device
        else:
            import torch
            _MODEL = AutoModelForMultimodalLM.from_pretrained(MODEL_ID, dtype="auto")  # into RAM
            lm = _MODEL.model.language_model
            ple = lm.embed_tokens_per_layer
            lm.embed_tokens_per_layer = None  # hide it from .to()
            _MODEL.to("cuda")
            lm.embed_tokens_per_layer = ple   # back, still in RAM
            _DEVICE = lm.embed_tokens.weight.device
            ple.register_forward_pre_hook(
                lambda m, args: tuple(a.to("cpu") if torch.is_tensor(a) else a for a in args))
            ple.register_forward_hook(lambda m, args, out: out.to(_DEVICE))
    return _MODEL, _PROCESSOR


def _gemma_call(wav: Path, prompt: str, max_new_tokens: int = 4096) -> dict:
    """One model call on <= GEMMA_MAX_CLIP_S of audio. Do not call this
    directly on anything longer -- see gemma_transcribe()."""
    model, processor = _load_model()
    messages = [{"role": "user", "content": [
        {"type": "text", "text": prompt},
        {"type": "audio", "audio": str(wav)},
    ]}]
    inputs = processor.apply_chat_template(
        messages, tokenize=True, return_dict=True, return_tensors="pt",
        add_generation_prompt=True, enable_thinking=True).to(_DEVICE)
    input_len = inputs["input_ids"].shape[-1]
    t0 = time.perf_counter()
    outputs = model.generate(**inputs, max_new_tokens=max_new_tokens)
    elapsed = time.perf_counter() - t0
    n_tok = outputs.shape[-1] - input_len
    response = processor.decode(outputs[0][input_len:], skip_special_tokens=False)
    parsed = processor.parse_response(response, prefix=inputs["input_ids"])
    return {
        "content": parsed.get("content", ""),
        "hit_token_limit": n_tok >= max_new_tokens - 8,
        "n_tokens": n_tok,
        "elapsed_s": round(elapsed, 2),
    }


def gemma_transcribe(wav: Path, prompt: str, max_new_tokens: int = 4096) -> dict:
    """Transcribe audio of any length.

    Gemma-4 E2B/E4B accept at most GEMMA_MAX_CLIP_S (30s) of audio per call --
    documented at ai.google.dev/gemma/docs/capabilities/audio and already
    encoded in transcribe2/spine.py. Feeding it longer audio directly does
    not error; it silently attends to only an initial slice and returns a
    plausible-looking but incomplete transcript. Caught this the hard way on
    a 384s clip: hit_token_limit was False (the model decided on its own it
    was "done" after ~10s), and the output was just the video's first ~30s
    of intro, not a truncated version of the whole thing.

    So: anything over the limit gets split with transcribe2's own
    plan_chunks()/stitch(), the same machinery GemmaEngine already uses in
    production, not a reimplementation of it.
    """
    sys.path.insert(0, str(HERE / "transcribe2"))
    from spine import Segment, plan_chunks, stitch, GEMMA_MAX_CLIP_S
    from audio import probe_duration, load_slice, write_slice_wav

    dur = probe_duration(wav)
    if dur <= GEMMA_MAX_CLIP_S:
        return _gemma_call(wav, prompt, max_new_tokens)

    seg = Segment(seg_id="full", speaker="_", start=0.0, end=dur)
    chunks = plan_chunks(seg, max_clip_s=GEMMA_MAX_CLIP_S)
    pieces, elapsed_total, hit_limit_any, n_tok_total = [], 0.0, False, 0
    for ch in chunks:
        samples = load_slice(wav, ch.start, ch.end)
        chunk_wav = write_slice_wav(samples, wav.parent / f"_chunk_{ch.index:03d}.wav")
        res = _gemma_call(chunk_wav, prompt, max_new_tokens)
        chunk_wav.unlink(missing_ok=True)
        pieces.append(res["content"])
        elapsed_total += res["elapsed_s"]
        hit_limit_any = hit_limit_any or res["hit_token_limit"]
        n_tok_total += res["n_tokens"]
    return {
        "content": stitch(pieces),
        "hit_token_limit": hit_limit_any,
        "n_tokens": n_tok_total,
        "elapsed_s": round(elapsed_total, 2),
        "n_chunks": len(chunks),
    }


def word_match(transcript: str, phrase: str) -> tuple[int, int]:
    got = set(re.findall(r"[a-z0-9']+", transcript.lower()))
    want = phrase.split()
    matched = sum(1 for w in want if w in got)
    return matched, len(want)


def main() -> int:
    global MODEL_ID, PLE_CPU
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    ap.add_argument("--manifest", default="stress_search/clip_manifest.csv")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--condition", default=None,
                    help="comma-separated: original,reps_only,rep_00,...  default: all")
    ap.add_argument("--out", default="stress_search/llm_stress_measured.csv")
    ap.add_argument("--model", default=MODEL_ID, help="e.g. google/gemma-4-E4B-it")
    ap.add_argument("--ple-cpu", action="store_true",
                    help="keep the per-layer embedding table in RAM (needed for E4B on 16 GB)")
    args = ap.parse_args()
    MODEL_ID, PLE_CPU = args.model, args.ple_cpu

    rows = list(csv.DictReader(open(HERE / args.manifest, encoding="utf-8")))
    if args.condition:
        wanted = set(args.condition.split(","))
        rows = [r for r in rows if r["condition"] in wanted
                or (r["condition"].startswith("rep_") and "rep_NN" in wanted)]
    if args.limit:
        rows = rows[: args.limit]

    hw = hardware_info()
    print(f"host: {hw.get('host')}  gpu: {hw.get('gpu_name', 'none detected')}\n")
    run_started = time.time()

    cols = ["video_id", "condition", "bucket",
            "plain_content", "plain_markup_applied", "plain_word_match",
            "plain_elapsed_s", "plain_hit_token_limit",
            "general_content", "general_markup_applied", "general_word_match",
            "general_elapsed_s", "general_hit_token_limit"]

    out_path = HERE / args.out
    # Resumable: a clip already written to a prior (possibly crashed or killed)
    # run of this same --out file is skipped, not redone. A multi-hour job with
    # nothing on disk until the very end throws away everything on any crash --
    # this was caught the hard way after 2 hours of real GPU time produced zero
    # output because the process was killed at clip 113/509.
    done: set[tuple[str, str]] = set()
    if out_path.exists():
        with open(out_path, encoding="utf-8") as fh:
            for r in csv.DictReader(fh):
                done.add((r["video_id"], r["condition"]))
        print(f"resuming: {len(done)} clips already done in {out_path}\n")
        fh_out = open(out_path, "a", newline="", encoding="utf-8")
        writer = csv.DictWriter(fh_out, fieldnames=cols, extrasaction="ignore")
    else:
        fh_out = open(out_path, "w", newline="", encoding="utf-8")
        writer = csv.DictWriter(fh_out, fieldnames=cols, extrasaction="ignore")
        writer.writeheader()
        fh_out.flush()

    n_measured_this_run = 0
    try:
        for i, r in enumerate(rows, 1):
            if (r["video_id"], r["condition"]) in done:
                continue

            wav = local_path(r["path"])
            if not wav.exists() or wav.suffix != ".wav":
                # original.wav entries point at the source (.mkv/.webm/.mp4/.wav);
                # non-wav sources need conversion once, cached alongside.
                if wav.exists():
                    cache = wav.parent / f"{wav.stem}__conv.wav"
                    if not cache.exists():
                        import subprocess
                        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(wav),
                                        "-ac", "1", "-ar", "16000", str(cache)])
                    wav = cache
                if not wav.exists():
                    print(f"  [{i}/{len(rows)}] {r['video_id']}/{r['condition']}: no audio, skip")
                    continue

            phrase = r["phrase"]
            row_out = {"video_id": r["video_id"], "condition": r["condition"],
                      "bucket": r.get("bucket", "")}
            for label, prompt in [("plain", PLAIN_PROMPT), ("general", GENERAL_PROMPT)]:
                try:
                    res = gemma_transcribe(wav, prompt)
                except Exception as e:
                    print(f"      {label} failed: {e}")
                    continue
                content = res["content"]
                matched, total = word_match(content, phrase)
                markup = bool(MARKUP_RE.search(content))
                row_out[f"{label}_content"] = content
                row_out[f"{label}_markup_applied"] = markup
                row_out[f"{label}_word_match"] = f"{matched}/{total}"
                row_out[f"{label}_elapsed_s"] = res["elapsed_s"]
                row_out[f"{label}_hit_token_limit"] = res["hit_token_limit"]

            writer.writerow(row_out)
            fh_out.flush()
            n_measured_this_run += 1
            print(f"  [{i}/{len(rows)}] {r['video_id']}/{r['condition']}  "
                  f"plain_markup={row_out.get('plain_markup_applied')}  "
                  f"general_markup={row_out.get('general_markup_applied')}")
    finally:
        fh_out.close()

    with open(out_path, encoding="utf-8") as fh:
        all_rows = list(csv.DictReader(fh))

    run_elapsed = round(time.time() - run_started, 1)
    n_general_markup = sum(1 for r in all_rows if r.get("general_markup_applied") == "True")
    n_plain_markup = sum(1 for r in all_rows if r.get("plain_markup_applied") == "True")
    results = all_rows  # for the final print block below, unchanged
    # llm_stress_measured.csv (the first E2B run) keeps its old manifest name.
    man = (SDIR / "llm_stress_run_manifest.json" if out_path.name == "llm_stress_measured.csv"
           else out_path.with_name(out_path.stem + "_run_manifest.json"))
    man.write_text(json.dumps({
        **hw, "script": "measure_llm_stress.py", "model": MODEL_ID, "ple_cpu": PLE_CPU,
        "manifest": args.manifest, "n_clips": len(results),
        "run_elapsed_s": run_elapsed,
        "n_general_markup_applied": n_general_markup,
        "n_plain_markup_applied": n_plain_markup,
    }, indent=1), encoding="utf-8")

    print(f"\n{len(results)} clips measured in {run_elapsed}s -> {out_path}")
    print(f"general prompt applied markup: {n_general_markup}/{len(results)}")
    print(f"plain prompt applied markup:   {n_plain_markup}/{len(results)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
