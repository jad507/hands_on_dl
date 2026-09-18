# The Emphasis Stress Test

**Parent:** [00-INDEX](./00-INDEX.md) · **Related:** [03 — Technical spec](./03-whisper-concord-spec.md), [01 §E — the falsification](./01-literature-landscape.md#e-prior-work-that-varies-the-transcript--the-falsification-attempt)
**Added:** 2026-08-14

The proposal: use the actor's exercise — one sentence, spoken N times with stress on a different word each time — as a test case. *"I didn't say he stole the money."* Seven words, seven meanings, identical text.

**Verdict: the current pipeline scores zero on this, and that is the single most valuable thing in these documents.** Not a weakness to patch — the demonstration the whole paper needs.

---

## Why zero, and why "zero" is the right word

Run all seven readings through `whisper large-v3`. You get seven identical transcripts. Not similar — **identical**, modulo hallucination noise. Every LLM downstream receives the same seven-token string and has no basis for distinguishing "I didn't say it, someone else did" from "he stole something else."

This is not degraded signal. It is **total information destruction at the first stage.** Whatever the coding model outputs about emphasis is confabulation, and it will be *confident* confabulation, because the model has no way to represent its own ignorance here.

Compare that to the failure modes catalogued elsewhere in these documents. [Whisper's inconsistent disfluency handling](./01-literature-landscape.md#b2-whispers-disfluency-handling-is-inconsistent--and-that-is-the-finding) loses some information. [Hallucination on long pauses](./01-literature-landscape.md#b3-hallucination--koenecke-et-al-2024-careless-whisper) fabricates some. Prosody is a different category: it is 100% loss, silently, on every recording, always.

Three things follow.

### 1. This is the sharpest possible statement of the Ochs/Bucholtz argument

[Ochs (1979)](./01-literature-landscape.md#a1-ochs-e-1979-transcription-as-theory) argues that a transcript encodes a hypothesis about what matters — her example being that standard orthography makes children's sound play structurally invisible. That is an argument about *degree of visibility*.

Emphasis is the limit case. On [Bucholtz's representational axis](./01-literature-landscape.md#a2-bucholtz-m-2000-the-politics-of-transcription) — *how* something is transcribed — the choice to render prominence or not is **binary and total**. Mark it and the meaning is recoverable. Don't and it is gone, with no trace in the artifact that anything was lost.

And the field already solved this notationally. Jefferson conventions mark stress (underlining), volume (capitals), and pitch movement (↑↓). **Conversation analysis has been recording prosodic prominence in transcripts since the 1970s. ASR discarded the capability and nobody wrote down that it was a loss.** That sentence belongs in the paper.

### 2. It gives you an answer to the strongest objection in the literature

[Southwell et al. and the surrounding work](./01-literature-landscape.md#e1-the-strongest-counterexample--and-it-predicts-a-small-effect) found ASR-vs-human transcript differences cost only ~4.2% classification accuracy, and that a 57% WER cost only 20% of performance — concluding that discourse-level models are robust to word-level perturbation. That is the finding most likely to make a reviewer say "so what?"

The emphasis case is the reply, and it is not a dodge:

> **The magnitude of the transcription-policy effect is a function of where the construct lives.** Constructs encoded lexically — topic, collaborative skill, question type — survive transcription variation, exactly as prior work reports. Constructs encoded prosodically do not survive it at all. Prior work measured the first kind and generalized.

That reframes your study from "does transcription matter?" (answer: apparently not much) to **"for which constructs does transcription matter, and how would a researcher know in advance?"** — a question with an actionable answer for practitioners, which is what a methods contribution is supposed to produce.

It also connects straight back to [the decision point that motivated the project](./00-INDEX.md#provenance-note-on-the-framing). Breaths, pauses, stutters, false starts are not decoration; they encode **stance** — hesitation, hedging, uncertainty, discomfort. Any codebook with a stance construct is coding something partly prosodic. Most qualitative codebooks have one and don't flag it.

### 3. It is a 30-second demo

The Interactive Tools & Demos track rewards things you can *show*. This is showable at a table in Mumbai with headphones:

1. Play seven clips. The listener hears seven different meanings.
2. Show seven identical Whisper transcripts.
3. Show the LLM assigning identical codes to all seven.
4. Show a human assigning seven different codes.
5. Switch on the prominence-annotated policy. Show the codes separate.

No statistics required to land the point. Statistics come after.

---

## What it would take to fix — five tiers

| Tier | Approach | Rating | Honest assessment |
|---|---|---|---|
| **0** | Whisper text only *(current pipeline)* | **0 / 10** | Identical strings. No signal exists to reason from. |
| **1** | + word-level timestamps ([WhisperX](https://github.com/m-bain/whisperX) forced alignment) | **3 / 10** | Duration is one of three acoustic cues. Emphatic lengthening is real and measurable, but requires per-word-type normalization ("I" is inherently short, "money" long), and a speaker who emphasizes by pitch alone is invisible. Cheap — you have most of this already. |
| **2** | + acoustic prosodic features ([Parselmouth](https://parselmouth.readthedocs.io/)/Praat: F0, RMS, duration per word) | **7 / 10** | The classical approach. Reported unweighted accuracies for prominent-vs-non-prominent around **80–82%** (Heckmann et al. 2014, as cited in Linke & Schuppler). Fragile on spontaneous speech: creaky and breathy voice wreck F0 extraction, and it depends on accurate forced alignment. |
| **3** | Prominence-aware ASR (fine-tuned wav2vec2) | **8–9 / 10** *(binary only)* | See below. Best available, and it needs no forced alignment. |
| **4** | Audio-native LLM (Qwen2-Audio, GPT-4o audio, Gemini) | **untested** | Skips the transcript entirely, which also skips the thing your paper is about. Worth a pilot as a comparison arm; not the main design. |

### Tier 3 in detail — and the ceiling nobody can exceed

**[Linke, J., & Schuppler, B. (2025). "Prominence-aware automatic speech recognition for conversational speech."](https://arxiv.org/abs/2509.10116)** Graz University of Technology. Fine-tunes wav2vec2 XLSR with CTC loss to emit prominence levels alongside words.

Numbers worth memorizing:

- **Binary detector (`PDET₀₂`, unaccented vs. strongly accented): 89.72% ± 3.26% accuracy** on correctly recognized words (10-fold CV).
- **Three-level detector (`PDET₀₁₂`, adding weak prominence): 69.45% ± 2.11%.** Much worse.
- Prominence-aware ASR reached **85.53%** prominence accuracy on utterances where the word count was right — **with no WER degradation versus baseline.** You get prominence essentially free.
- No forced alignment required, and it worked from only ~4.4 hours of manually annotated speech.

**Now the number that constrains your entire design.** Human inter-annotator agreement on the GRASS corpus prominence annotations, by trained phoneticians:

| Contrast | Cohen's κ |
|---|---|
| PL0 vs PL2 (unaccented vs strongly accented) | **0.92** |
| PL0 vs PL1 (unaccented vs weakly accented) | 0.72 |
| **PL1 vs PL2 (weak vs strong)** | **0.57** |

**Trained human phoneticians agree κ = 0.57 on whether a word is weakly or strongly prominent.** The machine's worse performance at three levels is not a machine failure — it is tracking a genuine limit in the construct. The task is only reliably defined at the binary level.

Design consequence, and it is not optional: **binary prominence only.** Do not build a graded emphasis scale. If a reviewer asks why not, cite this table. It is a much better answer than "we didn't have time."

---

## Test corpora — best first

### 1. ADEPT (Papercup) — the research-grade option ⭐

**[ADEPT: A dataset for evaluating prosody transfer](https://engineering.papercup.com/posts/ADEPT/)** — Torresquintero et al., Interspeech 2021. **Dataset on Zenodo.**

This is the actor's exercise, done properly, already published, with human ground truth:

- **Topical emphasis: 33 sentences × (3 emphasis positions + neutral) = 132 utterances per speaker**, 2 speakers, studio-recorded with contextual cues given to voice actors.
- Plus five other prosodic classes: emotion, interpersonal attitude, propositional attitude, syntactic phrasing, marked tonicity. **1,104 utterances total.**
- **Human recognition-accuracy benchmarks** from 30 paid native English speakers on MTurk, verified via a transcription task. So you have not just labels but *how well humans do*, which is the ceiling for any model claim.
- The evaluation question design is already validated: *"Which question is best answered by the sample? (a) WHO went to the office yesterday? (b) Tian went WHERE yesterday? (c) Tian went to the office WHEN?"*

**This satisfies the [EvalCorpus contract from 03](./03-whisper-concord-spec.md#the-evaluation-data-contract) more completely than anything else found in this whole research effort** — audio, known ground truth, human perceptual labels, and a published benchmark. Check the Zenodo license before building on it.

Also relevant from the same group: **Ctrl-P** (interpretable, temporally precise control of prosodic features in TTS), same Interspeech.

### 2. VOA Learning English — public domain, already annotated 🏆

**[A Simple Sentence with Seven Meanings](https://learningenglish.voanews.com/a/a-simple-sentence-with-seven-meanings/4916769.html)** — VOA *Everyday Grammar*, Alice Bryant. **6 minutes 57 seconds of audio.**

Why this is the best *demo* asset:

- **Voice of America is a US federal government work — public domain.** No license question, no takedown risk, no permissions email. For a conference demo where you want to distribute the artifact, this is worth more than production value.
- Uses **"I didn't say he stole the money"** with **all seven stress positions**, spoken cleanly by a native speaker, each separated by narration.
- **The article text states the intended meaning of each reading.** That is a labeled corpus written in prose. Seven items, ground truth included.
- Segmenting seven target utterances out of a seven-minute file is maybe an hour of work.

### 3. YouTube candidates

Not verified beyond search results — check each before committing time. Your existing `yt-dlp` infrastructure (`download_playlist.py`, cookie handling) makes acquisition trivial.

| Video | URL | Note |
|---|---|---|
| "How Changing Emphasis On One Word Can Change Everything!" | `https://www.youtube.com/watch?v=iVVO7ggxops` | Appeared in two independent searches; attributed to a British English teaching channel. Most likely direct hit. |
| "Stress Patterns In English \| How to Emphasize Points" | `https://www.youtube.com/watch?v=3k2y3Cwg-0k` | Explearning Communications. Broader topic; may contain a usable segment. |
| "How to Get a British Accent — Lesson 6: Emphasis & Word Stress" | `https://www.youtube.com/watch?v=ToFuJLnfNw4` | Accent-teaching context. Useful as an accent-variation condition. |
| **Rachel's English** (channel) | search the channel | Cited by VOA as a respected pronunciation resource. Likely has dedicated sentence-stress content — **search the channel directly rather than relying on general web search**, which kept returning TikTok. |

Also non-video but useful for framing: [City Lit's acting blog on emphasis](https://www.citylit.ac.uk/blog/how-emphasis-changes-meaning-in-acting-fun-christmas-example), [Theatrefolk's "Same Lines, Different Meanings" exercise](https://www.theatrefolk.com/blog/19758-2), and [allthingslinguistic on the seven-meanings sentence](https://allthingslinguistic.com/post/176922479672/one-sentence-with-7-meanings-unlocks-a-mystery-of).

### Which to use for what

- **ADEPT** → the actual experiment. Human labels, benchmarks, N large enough for statistics.
- **VOA** → the demo, and the figure in the paper. Public domain means you can put the waveform on a slide and distribute the clips.
- **YouTube** → robustness checks. Non-studio audio, varied accents, real recording conditions — closer to the messy audio a working researcher actually has.

---

## Recommended change to the experimental design

Add one policy condition and one construct family to the design in [03](./03-whisper-concord-spec.md#experimental-design):

**Policy P5 — prominence-annotated.** Whisper text plus binary word-level prominence, rendered in a notation that survives [Concord's `stripTags()`](./03-whisper-concord-spec.md#finding-2-striptags-destroys-angle-bracket-markup). Angle brackets are deleted at import, so use Jefferson-style marking — capitals for stress (`I didn't say he stole the MONEY`) or asterisks (`*money*`). Test which survives tokenization and note that **the choice of marker is itself a representational transcription decision**, which is pleasingly recursive and worth a sentence in the paper.

**A prosodic construct family in the codebook.** Alongside the four lexically-encoded themes from [`data_center_comment_themes.md`](./05-hands-on-dl-upgrade-plan.md#what-is-genuinely-strong-here), add two or three constructs that live in prosody — contrastive focus, hedging/uncertainty, emphatic assertion.

**Why this single change is worth the effort:** it converts a study that [might find nothing](./01-literature-landscape.md#consequences-for-the-design) into one with a **guaranteed contrast**. Lexical constructs will be robust to transcription policy — that is the replication of prior work, and it is a legitimate result. Prosodic constructs will collapse without P5 and recover with it. You cannot fail to find something, and the something is the paper's thesis stated as a 2×2.

**Sequencing.** P5 is a Tier-2 build at minimum (Parselmouth features over WhisperX word alignments) and that is real work. If August runs short, ship the demo with the [VOA clips](#2-voa-learning-english--public-domain-already-annotated-) and Tier 0 alone — *"here are seven audio files, here is one transcript"* — and put Tiers 2–3 in Future Work. **The zero-signal demonstration does not require you to have solved the problem.** It only requires you to show that it exists, which you can do this afternoon.

---

## Open questions

- **ADEPT's Zenodo license** — not checked. Decides whether it can anchor the study.
- **Whether Concord's tokenization preserves `*emphasis*` or `CAPITALS`** through `splitSentences` and into the judge prompt. Testable in an hour; see [03 §Finding 1](./03-whisper-concord-spec.md#finding-1-unitization-is-punctuation-dependent).
- **Whether an LLM given prominence-annotated text actually recovers the intended meaning**, or just pattern-matches on the marker. Control: give it the *wrong* prominence annotation and see whether it dutifully produces the meaning that annotation implies. If it does, the annotation is working. If it produces the lexically-default reading regardless, it is ignoring the marker.
- **Whether Linke & Schuppler's detector transfers.** It was trained on conversational **Austrian German** (GRASS corpus). English performance is unknown; retraining needs an English prominence-annotated corpus. The [Helsinki Prosody Corpus](https://github.com/Helsinki-NLP/prosody) (prominence labels over LibriTTS) is the obvious candidate — unverified in this pass.

---

**Back to:** [00-INDEX](./00-INDEX.md)
