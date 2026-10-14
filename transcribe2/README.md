# transcribe2

Give it an audio/video file or a URL. It produces **aligned** transcripts from
multiple engines under multiple transcription policies, plus a VTT that
[Concord](https://github.com/emollick/concord) will import without re-segmenting.

```bash
python doctor.py                                  # check the environment FIRST
python run.py meeting.mp4                                            # whisper only
python run.py meeting.mp4 --engines whisper,gemma-E4B                # both engines
python run.py clip.wav --engines gemma-E2B:clean-verbatim,gemma-E2B:full-verbatim \
                       --policies policies.json                      # policy comparison
python run.py "https://youtube.com/watch?v=..." --engines whisper --resume
```

**Status:** all model-free paths are implemented and tested (45 tests, green). The
Whisper and Gemma engines are written but **have not been run** -- this machine had
no GPU and no model weights. Expect to debug the first real invocation. See
[What has and has not been tested](#what-has-and-has-not-been-tested).

---

## Why it is built this way

The obvious design -- run Whisper, run Gemma, diff the outputs -- does not work,
because each engine picks its own segment boundaries. You then cannot tell whether
a difference came from the *transcription policy* or from the two engines having
carved the audio into different objects. That confound is fatal to the research
question.

So:

```
source (file or URL)
  `- ffmpeg --> canonical 16 kHz mono WAV        (ONE conversion, both engines)
       `- diarize ONCE --> spine.json            (FROZEN. Nothing may change it.)
            |- whisper       fills text["whisper-large-v3"]      for those segments
            |- gemma:clean   fills text["gemma-4-E4B/clean"]     for those segments
            `- gemma:verbatim fills text["gemma-4-E4B/verbatim"] for those segments
                 `- emit: one VTT per engine + one comparison CSV
```

The spine is the contract. Every engine fills text for the *same* frozen
segments, so cross-engine comparison joins on `seg_id` with **no alignment step
at all**. This is the hard problem from
[`docs/isls2027/03-whisper-concord-spec.md`](../docs/isls2027/03-whisper-concord-spec.md#the-alignment-problem),
solved by construction rather than after the fact.

Three constraints drove the rest of the design, and all three were read from
primary sources rather than assumed:

| Constraint | Source | Consequence |
|---|---|---|
| Gemma 4 E2B/E4B accept **max 30 s** of audio per clip | [Google's audio docs](https://ai.google.dev/gemma/docs/capabilities/audio) | `plan_chunks()` splits long turns and `stitch()` rejoins them -- but the *unit of analysis* stays one segment |
| Gemma 4 wants **16 kHz mono float32 in [-1, 1]** | same | one canonical WAV, converted once, so both engines provably read identical samples |
| Concord's `mergeCues` fuses same-speaker cues when `gap <= maxMergeGapSeconds` | `concord/server/ingest/transcript.js` | the VTT emitter inserts a 2 ms gap; without it Concord silently re-merges your frozen spine and N changes between conditions |

---

## The triage question

You asked whether the pipeline could send only the *interesting* lines to the
expensive engine, and immediately spotted the problem:

> "that seems like you'd have to already know the result before you send it for
> processing, lol"

Correct -- if the router needed the **meaning**, it would be circular. It doesn't.
`triage.py` scores three things, none of which require knowing the answer:

| Signal | What it asks | Needs meaning? |
|---|---|---|
| **Acoustic** | Is some word here carrying unusual prosodic weight? (F0 range, intensity peakiness, per-word duration outliers, all z-scored *within* the segment so it is speaker-normalized) | No -- pure DSP |
| **Syntactic** | Is this the *kind* of sentence where emphasis placement changes truth conditions? Negation + reportative verb + focusable pronouns is the "I didn't SAY he stole it" shape | No -- pure lexical pattern |
| **Epistemic** | Did Whisper find this hard? `avg_logprob` and per-word probabilities are already computed and thrown away | No -- free |

A segment scores high when it is **acoustically marked AND structurally
sensitive**. That conjunction is the non-circular core: acoustics says "something
is stressed here", syntax says "stress here would matter", and neither needed the
interpretation first.

It demonstrably works. From the smoke test -- two segments with **byte-identical
Whisper text**, one containing an emphatic burst:

```
00001_SPEAKER_00_00006   total=0.963  ac=0.931 syn=0.750 ep=0.932   <- burst
00000_SPEAKER_00_00000   total=0.589  ac=0.380 syn=0.750 ep=0.500   <- no burst
00002_SPEAKER_00_00012   total=0.254  ac=0.382 syn=0.000 ep=0.547   <- flat declarative
```

### But do not use it for the experiment

`--triage` defaults to `none`, deliberately. A policy that ran on a *biased
subset* of segments cannot be compared against one that ran on all of them --
routing would confound exactly the comparison the study exists to make. Your own
alternative is the right one for research:

> "here's the results with whisper and diarization, and then here's the results
> with Gemma"

Run both, fully, on everything. That is `--triage none`, which is the default.

The legitimate research use of triage is the **reverse**: use `--triage score`,
which computes and saves scores but still processes everything. Then check
whether the score *predicts* where the engines disagree. If it does, you have a
cheap screening instrument for expensive analysis -- and that is a publishable
finding in its own right, independent of the main study.

`--triage route` exists for production use and prints a warning every time.

---

## Engines

### Whisper

Run **per segment**, not per file. Costs some throughput; buys two things:
Whisper cannot impose its own segmentation, and per-segment decoding sharply
reduces exposure to the failure mode Koenecke et al. (2024) documented --
hallucination concentrating in long non-vocal stretches
([arXiv:2402.08021](https://arxiv.org/abs/2402.08021)). Diarized speech segments
contain far less silence than a raw meeting recording.

`faster-whisper` preferred, `openai-whisper` as fallback, auto-detected.
`condition_on_previous_text=False` throughout, so segments cannot contaminate
each other.

### Gemma 4 E2B / E4B

**Use HF Transformers, not llama.cpp.** At the Gemma 4 launch (2026-04-02)
llama.cpp could not parse Gemma 4 audio at all -- `llama-server` returned
`"audio input is not supported"` even with `--mmproj` supplied
([discussion #21334](https://github.com/ggml-org/llama.cpp/discussions/21334)).
It was resolved days later via issue #21325, and Ollama's audio path had its own
crash. `LlamaCppGemmaEngine` is included and speaks the OpenAI `input_audio`
shape, but it is **unverified** -- check `doctor` first.

Requires `transformers >= 5.10.1`. An older version fails at *inference* time,
not import time, which is why `doctor` version-checks it explicitly.

Google's documented ASR prompt is used verbatim as the default, because deviating
from the trained prompt shape is a silent quality regression.

Rough sizing: ~10 GB VRAM for E4B in bf16, ~6 GB for E2B. 25 audio tokens per
second of audio (Gemma 4; 6.25 for Gemma 3n).

---

## Policies

`policies.json` is the experimental manipulation. Seven ship by default:

| Policy | Axis manipulated |
|---|---|
| `default-asr` | Google's own prompt -- the "no policy" baseline |
| `clean-verbatim` | interpretive: disfluencies removed |
| `full-verbatim` | interpretive: disfluencies kept |
| `full-verbatim-unpunctuated` | representational: tests Concord's punctuation-dependent unitization |
| `ca-lite` | representational: Jefferson-subset notation, pauses and breaths |
| `prominence` | marks emphatic stress with asterisks |
| `prominence-verbatim` | both |

The first five are P0-P4 from the technical spec, mapped onto
[Bucholtz's (2000) interpretive/representational axes](../docs/isls2027/01-literature-landscape.md#a2-bucholtz-m-2000-the-politics-of-transcription).
The prominence pair is P5 from the
[prosody stress test](../docs/isls2027/06-prosody-stress-test.md).

**Asterisks, not angle brackets, and not capitals.** Concord's `stripTags()` is
`s.replace(/<[^>]*>/g, "")`, so `<emphasis>` vanishes silently at import.
Capitals collide with the sentence splitter, which looks for `[.!?]` + whitespace
+ uppercase. Asterisks survive both -- verify it yourself on one import anyway.

Output files record the policy **name and a prompt hash**, never the prompt text.
So: never edit a policy in place after a run has used it. Add a `-v2` instead.

---

## What has and has not been tested

**Tested here, 45 unit tests plus an end-to-end smoke run:**

- chunk planning against the 30 s limit -- coverage, no gaps, no trailing slivers, determinism, durations from 30.1 s to 1 hour
- `stitch()` overlap removal, including a real bug caught by the tests: a
  one-word overlap minimum silently deleted a word in
  `["I never said that.", "That she stole it"]`. Minimum is now 2 words.
- spine round-trip, validation, and the text-independence of the join key
- VTT emission against every Concord parser constraint, including the 2 ms gap
  and Jefferson-notation survival
- triage scoring on synthetic audio with a known answer
- WAV round-trip and slice boundary accuracy
- `--help` and `doctor` on a bare environment

**Not tested -- no GPU, no model weights, no gated model access on this machine:**

- `WhisperEngine.transcribe_segments` -- the faster-whisper and openai-whisper
  call shapes are written from their documented APIs
- `GemmaEngine.transcribe_segments` -- the `pipeline(task="any-to-any", ...)` call
  and the `{"type": "audio", "audio": path}` message shape come straight from
  Google's docs, but have not been executed
- `LlamaCppGemmaEngine` -- unverified, see above
- `pyannote_spine` -- needs a gated model and an HF token
- actual ffmpeg/yt-dlp invocation on real media

Expect to debug the first real run. Start small:

```bash
python doctor.py
python run.py sample.wav --diarize vad --engines whisper --limit 3
python run.py sample.wav --diarize vad --engines whisper,gemma-E2B --limit 3
```

---

## Install

```bash
pip install numpy                                     # required
pip install faster-whisper                            # whisper backend
pip install -U "transformers>=5.10.1" torch accelerate # gemma 4 audio
pip install pyannote.audio                            # real diarization (gated)
pip install praat-parselmouth                         # best F0 for triage
pip install yt-dlp                                    # URL input
# ffmpeg must be on PATH: https://ffmpeg.org/download.html
```

`HF_TOKEN` must be set for pyannote -- the models are gated. Without it the
pipeline falls back to an energy VAD, which is **single-speaker only** and prints
a warning. That fallback is fine for the emphasis test cases (one actor, one
sentence) and useless for council meetings.

## Files

| File | What it does |
|---|---|
| `spine.py` | the frozen segmentation, 30 s chunk planner, overlap stitcher |
| `audio.py` | yt-dlp/local acquisition, ffmpeg canonicalization, sample slicing |
| `diarize.py` | pyannote -> spine, with an energy-VAD fallback |
| `engines.py` | Whisper, Gemma 4 (Transformers), Gemma 4 (llama.cpp, unverified) |
| `triage.py` | non-circular acoustic + syntactic + epistemic scoring |
| `emit.py` | Concord-safe VTT, comparison CSV, triage CSV, plain text |
| `run.py` | the CLI |
| `doctor.py` | environment check -- run this first |
| `policies.json` | the transcription policies; **this is the experiment** |
| `test_pipeline.py` | 45 tests, all model-free |
