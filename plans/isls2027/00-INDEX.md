# ISLS 2027 Track — Index

**Status:** planning, drafted 2026-08-14
**Target venue:** [ISLS Annual Meeting 2027](https://2027.isls.org/), Mumbai, India, June 12–16 2027. Theme: *Act Local, Think Global: Contextualizing Design, Learning and Technologies*.
**Working title of the contribution:** *Transcription policy as a researcher-controlled parameter: instrumenting the ASR→LLM qualitative-analysis pipeline*

---

## The one-paragraph version

Qualitative researchers have known since [Ochs (1979)](http://www.sscnet.ucla.edu/anthro/faculty/ochs/articles/ochs1979.pdf) that a transcript is a theoretical artifact, not a recording. When a lab adopts Whisper, that theory gets made by a neural network's decoder defaults instead of by the researcher — silently, inconsistently, and without leaving a record. The proposed contribution is a pipeline that (a) makes the transcription policy an explicit, versioned, researcher-authored configuration; (b) runs the *same audio* through N policies; and (c) measures how far the downstream qualitative codes move as a result, using [Concord](https://github.com/emollick/concord)'s calibration-and-correction machinery so the movement is reported with honest confidence intervals rather than vibes.

The claim is not "AI can do qualitative coding." The claim is: **an unexamined ASR step silently fixes methodological choices that the field considers the researcher's to make, and here is an instrument that surfaces them.**

---

## Documents

| # | Document | What it answers |
|---|---|---|
| 01 | [Literature landscape](./01-literature-landscape.md) | Who has done what; where the actual gap is; ~40 annotated sources |
| 02 | [Submission strategy & timeline](./02-submission-strategy.md) | Which ISLS track, what deadline, and the Penn State IRB process |
| 03 | [Whisper → Concord technical spec](./03-whisper-concord-spec.md) | The integration contract, read from Concord's actual source |
| 04 | [Coursework alignment](./04-coursework-alignment.md) | Routing this through AI 801 and STAT 500 instead of around them |
| 05 | [`hands_on_dl` audit & upgrade plan](./05-hands-on-dl-upgrade-plan.md) | What's actually in the repo vs. what you remember; ordered next steps |
| 06 | [The emphasis stress test](./06-prosody-stress-test.md) | Prosody as the limit case; test corpora; why the pipeline scores zero and why that's good |
| 07 | [Windows execution findings](./07-windows-execution-findings.md) | What happened when Steps 0-2 were run; corrects 05 §1 and 06's notation question |
| 08 | [Prosody corpus and modernisation](./08-prosody-corpus-and-modernisation.md) | The contrastive-stress corpus as actually built, its measured error rate, and the case for audio-native models |
| — | [Lab notebook template](./NOTEBOOK-template.md) | Copy to `hands_on_dl/NOTEBOOK.md` |

---

## The seven things that most change the plan

1. **The deadline is closer than it feels.** [ISLS 2026](https://2026.isls.org/) closed submissions on **20 October 2025** (after two extensions from an original 5 October) for a June 2026 conference. Applying the same offset, the ISLS 2027 deadline is likely **early-to-mid October 2026** — roughly **seven weeks** from today, and landing on top of the first STAT 500 midterm. See [02](./02-submission-strategy.md#timeline).

2. **Concord has a Whisper-shaped hole, stated in writing.** Its README's "What's NOT in v1" list opens with: *"No local Whisper. Transcripts import as VTT/SRT/JSON; audio transcription can attach later via any local OpenAI-compatible endpoint."* The prefix you want to build is the documented missing piece, not a speculative one. See [03](./03-whisper-concord-spec.md#the-documented-gap).

3. **Concord's unit IDs are content hashes, which breaks the experiment unless you plan for it.** `unitId(corpusId, srcIndex, text)` is a SHA-256 of the unit text. Change the transcription policy → change the text → change every unit ID. Cross-condition comparison therefore cannot use unit IDs as the join key. It must use the time anchors (`pos.t0` / `pos.speaker`), which *do* survive into the unit record. See [03](./03-whisper-concord-spec.md#finding-3-unit-ids-are-content-hashes).

4. **The gap is narrower than this document's first draft claimed — and prior work predicts a small effect.** An earlier version asserted that nobody had varied transcription while holding audio, codebook, and model constant. That was overstated and has been **retracted**. [Southwell et al. (EDM 2022)](https://educationaldatamining.org/edm2022/proceedings/2022.EDM-long-papers.26/index.html) and the literature around it report a **4.2% accuracy decrease** for classifying collaborative skills from ASR versus human transcripts, and that a **57% word error rate cost only 20%** of classifier performance — concluding that discourse-level models are robust to word-level perturbation. Plan for a null: pre-register an equivalence test and choose disfluency-sensitive constructs. Full accounting in [01 §E](./01-literature-landscape.md#e-prior-work-that-varies-the-transcript--the-falsification-attempt).

5. **You already have pilot data and did not know it** — but it measures something else. **[Executed 2026-09-03; see 07 §1.](./07-windows-execution-findings.md)** The 26 variant pairs are 99.4% byte-identical in text, so the instability below is not an upstream-processing effect: it is the analysis harness's 3-block batching window, which flips 12-17% of classifications on identical text. Same thesis, cleaner evidence, different mechanism. Original text follows.

     26 of the Lancaster meetings exist in two upstream variants (`_standard` and `_exclusive` pyannote diarization). Same audio, different processing, same model, same prompt. Flag counts differ on **16 of 26 pairs for ministral-8b** while the aggregate moves only **1.1%** — aggregate robustness masking per-unit instability, exactly the pattern the literature predicts. That comparison needs no new data, no cluster, and no IRB, and it may be the demo paper's headline figure. See [05 §1](./05-hands-on-dl-upgrade-plan.md#1-you-already-have-pilot-data-for-the-isls-study-and-did-not-know-it).

6. **Prosody is the limit case, and the pipeline scores zero on it.** Seven readings of *"I didn't say he stole the money"* — stress on a different word each time, seven different meanings — produce **seven identical Whisper transcripts**. Not degraded signal: total information destruction at stage one. This is not a hole in the plan; it is the plan's best demonstration, and it supplies the answer to the Southwell objection in item 4: *the size of the transcription-policy effect is a function of where the construct lives.* Lexical constructs survive; prosodic ones do not survive at all. See [06](./06-prosody-stress-test.md).

7. **ISLS is not hostile to this work — the opposite.** [Lopez-Fierro & Nguyen's "Making Human-AI Contributions Transparent in Qualitative Coding"](https://repository.isls.org/handle/1/10537) (CSCL 2024, pp. 3–10) **won the Naomi Miyake Outstanding Student Paper Award** — a student paper about AI in qualitative coding, at the front of the volume. And [Mathur & Shapiro's "Interactive Transcription Techniques for Interaction Analysis"](https://repository.isls.org/bitstream/1/8993/1/ICLS2022_19-26.pdf) (ICLS 2022, pp. 19–26) is a full-length transcription-methodology paper. Both genre and topic are established. There *is* a critical strand ("Luddite praxis"), and your framing is on its side. See [02 §What ISLS actually is](./02-submission-strategy.md#what-isls-actually-is-and-what-actually-gets-published-there).

---

## Provenance note on the framing

The study design is a response to a methodological position articulated in conversation by Rae, a professor who teaches qualitative methods in an education program. Stated in full, so it survives without the conversation:

> Her argument is that graduate students in her program typically take a single qualitative methods course, and come away not understanding how much labor competent qualitative work requires. Her concrete example: a researcher is effectively obliged to listen to every recording in full, and manual transcription must come *after* at least one complete pass through the data — because the first pass is what generates the researcher's decision points. Her illustration of such a decision point: *do you transcribe breaths, pauses, stutters, and false starts, because they carry information — or is it more faithful to trim most of that out?*

The design bet in this project is that Rae is right that the decision must be researcher-led, and simultaneously that the *execution* of the decision is now automatable. If both hold, then the interesting object is not "automated transcription" but **the difference in downstream analytic output when the same audio is transcribed under different researcher-authored policies**. How novel that is — and how large the difference is likely to be — is treated honestly in [01 §E](./01-literature-landscape.md#e-prior-work-that-varies-the-transcript--the-falsification-attempt), which retracts an earlier, more confident claim.

---

## Repository conventions

These documents are written to be `git commit`-able and readable a year from now with no memory of the conversation that produced them. Claims sourced from the web carry inline links. Claims that were **not** independently verified are marked `[unverified]`. Claims read directly out of source code cite `file:symbol`.
