# 08. The prosody corpus, and moving to audio-native models

**Status:** executed 2026-09-04 on the Windows workstation.
**Relates to:** [06 (the emphasis stress test)](./06-prosody-stress-test.md), which this
executes and partly answers; [03 (Concord spec)](./03-whisper-concord-spec.md), which it
contradicts on one point; [07 (execution findings)](./07-windows-execution-findings.md).

Doc 06 argued that prosody is the limit case, that the pipeline scores zero on it, and
that this is the plan's best demonstration rather than its worst hole. It listed test
corpora to go and find, and it left the finding of them as future work.

That work is now done, and it produced something doc 06 did not anticipate: a working
instrument, a measured error rate for it, and a labelled reference set. This document
records what exists, then argues for the change the next phase should make.

---

## 1. What now exists

Three programs, in the order they run.

**`find_stress_videos.py`** searches YouTube and decides from the transcript rather than
the title. For every candidate it pulls the auto-caption track, which is fetchable
without downloading media, and looks for a structural signature: a phrase of 4 to 14
words repeated at least four times inside a five-minute span, not itself periodic. A
speaker demonstrating contrastive stress says one sentence five to seven times in ninety
seconds; a lecture *about* prosody mentions the example once.

**`verify_stress.py`** measures which word the speaker actually leaned on. Word
boundaries come from the per-word timings already present in the caption file as inline
`<00:00:01.234>` markers. Each word is scored on pitch, loudness and duration, z-scored
within its own repetition, then scored again against its own average across repetitions.

**`stress_from_audio.py`** drops the YouTube dependency: any URL yt-dlp can reach or any
local file, transcribed with Whisper for word timings, then the same measurement.

**`validate_stress_detector.py`** measures the detector against labelled ground truth.

### The numbers

| | |
|---|---|
| Queries run | 28 |
| Distinct videos seen | 497 |
| Already known from the earlier keyword passes | 16 |
| Caption tracks fetched | 250 |
| **Caption-verified repeated-sentence hits** | **91** |
| Acoustically measured | 81 |
| Skipped (fewer than 4 occurrences locatable in the captions) | 10 |
| Strong (5 or more distinct stressed words) | 20 |
| Usable (3 to 4) | 57 |
| **Full coverage (every word position stressed at least once)** | **11** |

The two that carry real weight, both full sentences rather than fragments:

- `watch?v=4Iqrm82LED4` -- "i didn't say he stole the money", 8 repetitions, **7 of 7**
  distinct stressed words, walking `i > didn't > say > he > stole > the > money` after
  one neutral opening reading.
- `watch?v=YXSkyQIKPeU` -- "finish work at 1:00 p.m.", 7 repetitions, **7 of 7**.

**Read the other nine full-coverage items with care.** They are all 4-word phrases, and
several are fragments the phrase detector truncated rather than complete utterances --
"i want you to", "the end of words", "we put stress on", and one doubled phrase, "come
here come here". Covering four positions out of four is a much weaker claim when the four
are not a sentence. `extend_phrase` grows a detected phrase outward while it still
repeats, but it cannot recover a boundary the captions never marked.

Coverage across all 81, as a fraction of sentence length: 11 at 1.0, 2 at 0.9, 19 at 0.8,
12 at 0.7, and the remaining 37 at 0.6 or below.

**The measurement is deterministic.** The first 30 were measured on 2026-09-04 and all 91
were remeasured on 2026-09-07 after a caption refetch: all 30 came back bit-identical on
phrase, repetition count, distinct-stress count and stress sequence. That is worth stating
because it is not true everywhere in this project -- the committed `llm_outputs` do not
reproduce today. Acoustic measurement of a fixed audio file has no sampling temperature;
LLM coding does.

**Diminishing returns are visible and expected.** The first 30 candidates yielded 14
strong (47%); the next 51 yielded 6 more (12%). The search pool was ranked, and the
ranking worked. Extending the corpus further means new queries, not more measurement of
what is already pooled.

### What searching structurally bought

The earlier passes searched for sentences somebody had already thought of. Searching for
the *shape* instead turned up families nobody had listed: "i never said she carried her
dog", "i didn't say he stole her money", "a wolf stole your purse", "the teacher didn't
grade", "finish work at 1:00 p.m.". Of 497 videos seen, only 16 were already known.

---

## 2. Ground truth, and the two bugs it caught

Baruch College's Tools for Clear Speech publishes the same sentence as separate
recordings, one per stress placement, with the intended stressed word **in the
filename**:

```
IHadTheTextBookYesterday - Stress I.mp3
IHadTheTextBookYesterday - Stress TextBook.mp3
IHadTheTextBookYesterday - Stress Yesterday.mp3
```

Five files, two sentence groups. Small enough that the resulting rate is indicative
rather than a confidence interval, and still the difference between a measured error
rate and none at all.

**Detector accuracy: 4 of 5 (80%).**

Both bugs it caught are worth recording, because both produced confident, plausible,
wrong output with no error and no warning.

**A filename collision.** `slug()` sanitised a URL and truncated to 60 characters. The
five recordings share a 103-character URL prefix, so all five mapped to one filename;
the cache check saw the file existed and returned the first download five times. The run
reported that every recording stressed the same word and that two different sentences
had the same transcript. Only the ground truth made the answer obviously impossible.
Against unlabelled YouTube data this would have read as a result.

**Lexical stress masquerading as contrastive stress.** After the collision was fixed,
accuracy was 3 of 5, and the miss was diagnostic. On the file labelled as stressing
*class*, the detector chose **"johnson's"** -- which genuinely is the loudest, highest
word in the utterance, and is equally loud in the *other* reading of the same sentence.
Raw prominence conflates the stress a word carries in every reading with the emphasis a
speaker placed deliberately in this one.

The fix uses structure the design already provides. With several repetitions of one
sentence, score each word against its own average across those repetitions: a word
prominent every time nets to zero, a word unusually prominent in this reading stands
out. Accuracy went 3/5 to 4/5, and "class" now beats "johnson's".

This is the same class of error as the batching finding in doc 07. A quiet, structural
property of the instrument was determining the answer.

---

## 3. The claim, now with ground truth behind it

Doc 06's central demonstration was, until now, an argument: seven readings that mean
seven different things produce one transcript. Making that argument required asserting
that the readings really did differ.

The Baruch recordings remove the assertion. A speech-teaching institution deliberately
produced three recordings with the stress in three different places and said so in the
filenames. Whisper returns, for all three:

```
"i had the textbook yesterday"
```

One string. And for the other group, two deliberately different readings, again one
string.

The public-domain VOA Learning English lesson gives the same result at greater length: 8
repetitions of "I didn't say he stole the money", 5 distinct stressed words measured,
and Whisper wrote the sentence identically 8 times. Public domain matters: that clip can
be reproduced in a paper with no rights question.

---

## 4. Where this sits in doc 06's tier table

Doc 06 laid out five tiers. What was built is **Tier 2**, and it lands where doc 06 said
it would.

| Tier | Doc 06's rating | Status now |
|---|---|---|
| 0. Whisper text only | 0/10 | The baseline being argued against. Confirmed. |
| 1. Word-level timestamps | 3/10 | Partially done, and the weakest link. See below. |
| **2. Acoustic features (Parselmouth F0/RMS/duration)** | **7/10** | **Built. Measured 80% on n=5.** |
| 3. Prominence-aware ASR (fine-tuned wav2vec2) | 8-9/10 binary | Not started. |
| 4. Audio-native LLM | untested | Not started. Section 5. |

Doc 06 cited 80-82% unweighted accuracy for classical prominence detection. The measured
80% sits exactly in that band, which is a reason to believe the implementation is
faithful rather than a reason to celebrate.

**Tier 1 is the weakest link and was skipped.** Word boundaries come from YouTube
auto-caption timings, which are approximate and can be off by a syllable. Every acoustic
number is measured over those windows. Proper forced alignment (WhisperX or the Montreal
Forced Aligner) is the cheapest available accuracy improvement and should come before
anything more ambitious.

**Doc 06's binary-only constraint still holds.** Trained phoneticians agree at kappa 0.57
on weak-versus-strong prominence. Nothing here should become a graded emphasis scale. The
current detector reports one stressed word per repetition, which is a
strongest-word-only claim and stays inside that limit.

---

## 5. The case for audio-native models, against doc 06's own objection

Doc 06 rated Tier 4 "untested" and warned:

> Skips the transcript entirely, which also skips the thing your paper is about. Worth a
> pilot as a comparison arm; not the main design.

That warning is right about one thing and, I think, wrong about the framing.

### The reframe

The paper's subject is not the transcript. It is **transcription policy as a
researcher-controlled parameter**. The transcript is where policy currently hides.

With Whisper, the policy is architecture. Its decision to drop filler words, tidy false
starts and invent punctuation lives in decoder defaults and training data. A researcher
cannot state that policy, cannot version it, and cannot vary it except by swapping
models. That is the problem the study exists to describe.

With an audio-native LLM, **the policy becomes a prompt**. It is written in English, it
lives in a text file, it is diffable, citable, and can be varied while everything else
is held constant.

That is not skipping the subject. That is the subject, made manipulable for the first
time. An audio-native model is the first instrument on which "transcription policy" is
literally a parameter rather than a metaphor.

### This is already half-built in this repository

`transcribe2/engines.py` contains a `GemmaEngine` and a `LlamaCppGemmaEngine`, written
but never run, and two prompts. The first reproduces Google's documented ASR prompt
verbatim. The second is the policy arm:

> "Transcribe the following speech segment verbatim... Include filled pauses (uh, um),
> repetitions, false starts and self-corrections exactly as spoken. Do not clean them
> up. Mark a word spoken with clear emphatic stress by surrounding it with asterisks..."

That is a researcher-authored transcription policy, in a file, already written. Nobody
has executed it. The environment check now passes and the model weights are present, so
executing it is a short task rather than a speculative one.

### The experiment this makes possible

Same audio, three transcription policies, everything else frozen by the spine design:

| Arm | Policy | What it tests |
|---|---|---|
| **A** | Whisper default | The status quo. Prosody destroyed. |
| **B** | Gemma 4, clean-verbatim prompt | Does an audio LLM under a *cleaning* policy destroy the same information? |
| **C** | Gemma 4, full-verbatim + emphasis marking | Does the information survive when the policy asks for it? |

Run all three over the 20 strong corpus items, where the acoustic measurement says which
word was stressed in each repetition. Then ask the only question that matters:

> **Does arm C recover the stress placement that arm A destroys, and how often?**

Every outcome is publishable, which is the property a study should have before it runs:

- **C recovers stress reliably.** Then the doc 06 claim sharpens rather than weakens. It
  was never "machines cannot hear emphasis"; it is "the *default policy* discards it, and
  the discarding was never a researcher's decision." That is a stronger and more useful
  claim, and it comes with a remedy.
- **C fails.** Then prosody is destroyed at the acoustic front end regardless of policy,
  doc 06's total-information-destruction claim stands at full strength, and the case
  applies to audio LLMs too rather than only to Whisper.
- **C partly works, unevenly.** Most likely, and most interesting: the effect size
  becomes a function of construct type, exactly as doc 06 argued in its answer to the
  Southwell objection.

The comparison bench for this already exists. `validate_stress_detector.py` takes labels
and reports accuracy; a Gemma arm drops into it as another predictor scored against the
same five labelled files.

### Do not let the audio LLM grade itself

One design warning. If Gemma both produces the transcript and judges which word was
stressed, the arm is self-scoring. The acoustic measurement must stay as the independent
referee, which is a further reason to strengthen Tier 1 and Tier 2 before running Tier 4
rather than instead of it.

---

## 6. A conflict between two parts of this repository

`GEMMA_VERBATIM_PROMPT` asks the model to mark emphatic stress **by surrounding the word
with asterisks**.

The Concord probes in doc 07 tested ten notations against Concord's real parser and found
that `*asterisks*` **move unit boundaries**. Marking emphasis that way does not annotate
the text; it changes how the sentence splitter divides it, so the number of units being
counted changes as a function of how many words the speaker emphasised.

The verified-safe notation is **CAPITALS**.

So the emphasis prompt, as written, is on a collision course with the downstream tool.
Nobody has hit it because the engine has never run. **Change the prompt to CAPITALS
before the first Gemma run**, or the unit counts in the first policy comparison will be
wrong in a way that correlates with the variable under study, which is the worst
available failure mode.

This is a small fix and a good illustration of why doc 07 tested Concord empirically
rather than trusting its documentation.

---

## 7. The modernisation roadmap, stage by stage

Ordered by ratio of benefit to effort, not by how modern the technology is.

### 7.1 Word alignment: caption timings to forced alignment

**Now:** YouTube auto-caption inline timings, or faster-whisper word timestamps.
**Next:** WhisperX or the Montreal Forced Aligner.
**Buys:** every acoustic measurement is currently taken over an approximate window. This
is the single largest source of error in the existing 80% and the cheapest to reduce.
**Costs:** one dependency, some GPU time. No research risk.

**Do this first.** It improves Tier 2 and is a prerequisite for interpreting Tier 3 and
Tier 4 fairly.

### 7.2 ASR: small.en to a current model

**Now:** `faster-whisper small.en`, chosen because it was fast.
**Next:** large-v3 or turbo, and treat the model size itself as a policy variable.
**Buys:** better word timings, better transcripts, and a free extra comparison arm --
does the *size* of the ASR model change downstream codes the way the *policy* does?
**Costs:** minutes per clip instead of seconds. The corpus is small; this is affordable.

### 7.3 Prominence: hand-rolled heuristic to a trained detector

**Now:** three z-scored acoustic correlates summed, then normalised across repetitions.
**Next:** the Tier 3 route in doc 06, fine-tuned wav2vec2 for prominence
(Linke and Schuppler 2025, 89.72% binary).
**Buys:** roughly ten accuracy points over the classical approach, no forced alignment
required, and a citable method instead of one invented here.
**Costs:** real work. Fine-tuning, or finding published weights.

**Judgement:** worth doing only if the corpus becomes the paper's centrepiece. If prosody
stays a limit-case demonstration, Tier 2 at 80% with a stated error rate is honest and
sufficient. Say the error rate; do not hide it.

### 7.4 The audio-native arm

Section 5. Run it as a **comparison arm with the acoustic referee held out**, not as a
replacement for the measurement.

Concretely, in order:

1. Change `GEMMA_VERBATIM_PROMPT` to CAPITALS.
2. Run `transcribe2` end to end on one short clip. Expect the torchcodec problem
   (Windows needs the full-shared FFmpeg build).
3. Run the three arms over the 5 labelled Baruch files. Score with
   `validate_stress_detector.py`.
4. If that is coherent, run over the 20 strong corpus items.

### 7.5 What NOT to modernise

**Do not replace `agreement.py`.** Krippendorff's alpha and Gwet's AC1 are checked
against published worked examples and are not improved by newer software.

**Do not build a graded emphasis scale**, however capable the model. The kappa 0.57
ceiling in doc 06 is a property of the construct, not of the instrument.

**Do not let a language model replace the acoustic measurement entirely.** The paper's
argument is that unexamined automated steps make silent methodological choices. Replacing
a measurement that can be inspected with one that cannot would be that argument, applied
to us, by us.

---

## 8. Everything else outstanding

Prosody is one strand. The rest of the programme, roughly in priority order:

1. **Human coding of the gold sample.** Still the bottleneck for the main study. The
   sample is drawn, stratified, blind, weighted and pre-registered. Roughly 8 to 12
   hours. Until it exists everything in doc 07 is agreement, not accuracy, and condition
   C of the chunk experiment cannot be interpreted at all.
2. **Finish phi-4** as the third model in the chunk experiment, about 3 hours. Two of the
   current claims rest on exactly two models.
3. ~~Measure the remaining 61 caption-verified candidates.~~ Done 2026-09-07;
   81 of 91 measured, 10 skipped for too few locatable occurrences. See the table above.
4. **First real `transcribe2` run.** Environment check passes; nothing has processed real
   audio.
5. **Decide what the paper is.** The batching finding is finished, controlled, replicated
   and needs no ethics approval. The transcription-policy study is the more ambitious
   one and needs `transcribe2` to have produced results. With five to six weeks to the
   likely deadline, the batching finding is the low-risk lead.

---

## 9. What could go wrong

**The ground truth is five files.** 80% from n=5 has an enormous interval around it. Do
not quote it as an accuracy figure without saying n. Expanding it is the highest-value
small task available; see 9.1.

**The corpus is teaching material.** Almost every item is an ESL or acting instructor
demonstrating deliberately. That is a clean signal and it is not spontaneous speech. Any
claim about prosody in the wild does not follow from it, and the council corpus is where
spontaneous speech actually lives.

**Synthetic voices.** Some clips may be TTS. A synthesised contrastive-stress
demonstration is still a valid test of whether ASR preserves stress, but it is not
evidence about human speakers. Worth spot-checking the strong items.

**Audio-LLM outputs are hard to falsify.** A model that says "the speaker emphasised
*stole*" is producing a claim, not a measurement. Keep the acoustic referee.

### 9.1 Expanding the ground truth

Three routes, cheapest first.

**More labelled teaching collections.** Baruch's naming convention is unlikely to be
unique. Other speech-pathology and ESL sites publish per-stress-placement files.

**Walk-derived labels.** In a canonical demonstration the speaker walks the stress left
to right, so in a video with exactly N repetitions of an N-word sentence, repetition k
stresses word k. That convention is independent of any acoustic measurement, so using it
as a label is not circular -- provided the walk is asserted by the source or confirmed
once by a human, and **not** inferred from the detector's own output. The two perfect
items already qualify, which would turn them into 14 labelled utterances immediately.

**One hour of human listening.** Fourteen strong videos, roughly 90 seconds each. A
person marking the stressed word per repetition produces a hundred or so labelled
utterances and settles the detector's accuracy properly. This is by far the strongest
option and it is small.

---

## 10. How to run any of it

```bash
# search YouTube by transcript structure
python find_stress_videos.py                      # 28 queries, ~25 min
python find_stress_videos.py --smoke              # 2 queries, ~30 s

# measure which word was stressed
python verify_stress.py --limit 30                # top 30 by repetition count
python verify_stress.py                           # all 91

# any non-YouTube source
python stress_from_audio.py https://example.org/lesson.mp3
python stress_from_audio.py clip.wav --phrase "i didn't say he stole the money"

# score the detector against labelled ground truth
python validate_stress_detector.py

# tests
python -m pytest test_find_stress_videos.py test_verify_stress.py -q   # 47
```

Outputs land in `stress_search/`, which is gitignored because caption tracks and audio
are bulky third-party content. The results CSVs and the ledger are small and could
reasonably be tracked; that decision has not been made.

TikTok is out of scope on this machine. No TikTok URL is ever requested, the
already-known-URL reader skips those files outright, and there is a test asserting it.
