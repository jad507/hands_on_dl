# Whisper → Concord: Technical Specification

**Parent:** [00-INDEX](./00-INDEX.md) · **Prev:** [02 — Submission strategy](./02-submission-strategy.md) · **Next:** [04 — Coursework alignment](./04-coursework-alignment.md)

Everything in this document about Concord was read out of the source at [github.com/emollick/concord](https://github.com/emollick/concord) (`main`, 81 commits, MIT license, as of 2026-08-14). Citations are `path:symbol`. Nothing here is inferred from the README alone.

---

## The documented gap

Concord's README has a section titled *"What's NOT in v1"*, and the first entry is:

> **No local Whisper.** Transcripts import as VTT/SRT/JSON; audio transcription can attach later via any local OpenAI-compatible endpoint.

The design doc it points to (`docs/plans/2026-06-05-concord-v1-design.md`, §2) treats this as a deliberate scope cut, not an oversight. So the prefix stage is a documented hole with a documented interface: **produce VTT, SRT, or Zoom/Otter-style JSON, and Concord takes it from there.**

That is a much easier integration than it could have been. The work is not "make Whisper talk to Concord." The work is everything in [The alignment problem](#the-alignment-problem).

---

## What Concord actually accepts

`server/ingest/transcript.js:parse(filePath, {maxMergeGapSeconds})` is the whole ingestion surface for transcripts. Reading it in order:

### Format dispatch

```
.vtt  or content matching /^﻿?WEBVTT/  → parseVTT
.srt                                   → parseSRT   (identical block structure;
                                                      toSeconds handles comma decimals)
.json or content starting { or [       → parseZoomJSON
anything else                          → ConcordError("BAD_TRANSCRIPT")
```

### Speaker attribution — two supported forms

`transcript.js:cueSpeakerText` recognizes exactly two:

1. **VTT voice tags:** `<v Speaker Name>text</v>` (also `<v.classname Speaker>`)
2. **Prefix form:** `Speaker: text`, constrained by `SPEAKER_PREFIX = /^([A-Z][\w .'-]{0,40}?):\s+(.*)$/s`

Note the constraints on form 2: the speaker label **must start with a capital letter**, is **capped at 41 characters**, and may only contain word characters, spaces, periods, apostrophes, and hyphens. `pyannote`'s default `SPEAKER_00` labels satisfy this. `speaker_00` would not.

Cues with neither form get `speaker: null`, which later coerces to the literal string `"Speaker"`.

### Timestamp parsing

`transcript.js:toSeconds` accepts `HH:MM:SS.mmm`, `MM:SS.mmm`, bare float seconds, numbers, and comma decimals (`00:00:01,000`). Hours are capped at three digits.

### Turn merging

`transcript.js:mergeCues` merges **consecutive same-speaker cues** into one turn, but only when the silence between them is at most `DEFAULT_MAX_MERGE_GAP_SECONDS = 30`, overridable via the `maxMergeGapSeconds` option. The source comment explains the reasoning: an hour-long gap is a different moment in the meeting, not one continuous utterance.

Two behaviors worth knowing:

- Cues with **unknown timestamps merge unconditionally** — a null `t0`/`t1` "cannot prove a gap."
- Cues **without speakers deliberately do not merge.** Stored turns coerce `null` → `"Speaker"` while incoming cues keep `null`, so the equality check fails. The comment is explicit that this is intentional: anonymous captions often break mid-sentence, and merging them would fuse the entire file into one turn.

**Implication for your pipeline:** diarize before export. An un-diarized Whisper VTT will produce one turn per caption cue, which is an arbitrary and policy-dependent unit boundary — the exact confound the study is trying to measure. Your existing `pyannote` stage already handles this.

### Output shape

```js
{ turns: [ { speaker, t0, t1, text } ], issues: [ { kind, detail } ] }
```

`issues` accumulates `bad_cue`, `bad_timestamp`, `empty_segment`, `empty`. Worth surfacing in your harness — a policy that produces more parse issues than another is itself a finding.

---

## Three findings that shape the design

### Finding 1: unitization is punctuation-dependent

`server/ingest/unitize.js:splitSentences` splits on `[.!?]` followed by whitespace followed by an uppercase letter (`\p{Lu}`, any script) or a digit, with a guard list of abbreviations (`Dr.`, `e.g.`, single-letter initials, etc.). **Lowercase starts deliberately do not split.**

This matters enormously:

- A **fully unpunctuated verbatim transcript** — a defensible CA-style output — collapses to **one gigantic sentence unit per turn** under `scheme: "sentence"`.
- A transcript that renders a false start as `I— I mean` versus `I, I mean` versus `I. I mean` produces **one, one, and two** units respectively.

So the number of units, `N`, is a **function of the transcription policy**. Every proportion, every κ, every confidence interval has a policy-dependent denominator. You cannot naively compare "12% of units coded X" across conditions when the conditions disagree about what a unit is.

This is not a bug to route around. It is arguably the single most publishable thing in the study: **transcription policy silently determines the unit of analysis, and the unit of analysis determines the statistics.** Nobody in [the LLM-coding literature](./01-literature-landscape.md#c-llm-assisted-qualitative-coding) is controlling for this, because they all treat the transcript as given.

**Mitigation:** use `scheme: "turn"`, not `"sentence"`, for the primary analysis. Turn boundaries come from diarization, which you hold constant across conditions. Then run `"sentence"` as a secondary analysis and *report the unit-count drift as a result*.

### Finding 2: `stripTags` destroys angle-bracket markup

`transcript.js:stripTags` is `s.replace(/<[^>]*>/g, "")`, applied to every cue body after speaker extraction.

Anything in angle brackets is gone. If you were planning to annotate disfluencies as `<pause dur="1.2"/>` or `<breath/>`, it evaporates silently at import — no issue logged, no error. Use notation that survives:

| Phenomenon | Safe notation | Why |
|---|---|---|
| Timed pause | `(1.2)` | Jefferson-standard; parens survive |
| Untimed pause | `(.)` | ditto |
| Audible breath | `.hh` / `hh` | plain text |
| Cut-off / false start | `wor-` | plain text |
| Sound stretch | `wo:rd` | plain text |
| Overlap | `[ ]` | square brackets survive |

Jefferson notation happens to be entirely angle-bracket-free, which is convenient. See [01 §A3](./01-literature-landscape.md#a3-jefferson-transcription-notation).

Caveat: `(1.2)` and `wo:rd` will also affect `splitSentences` and any downstream tokenization. Measure that, do not assume it.

### Finding 3: unit IDs are content hashes

`server/core/ids.js`:

```js
export function unitId(corpusId, rowIndex, text) {
  return "u_" + sha256(`${corpusId}|${rowIndex}|${text}`).slice(0, 16);
}
```

The unit ID is a SHA-256 over corpus ID, source index, **and the unit text**. This is a good design for its intended purpose — IDs stay stable across re-imports of identical data, and skipped empty rows do not shift them, because the hash uses the *source* index rather than the emitted ordinal (`unitize.js`, comment at the `units.push` loop).

But it means: **change one character of transcription policy and every downstream unit ID changes.** Your gold labels, coded once against condition A, cannot be joined to condition B by ID. Neither can the paired statistics.

Fortunately, `unitize.js` carries the time anchors through. For transcript sources it populates:

```js
pos: { turn: ti, speaker: turn.speaker ?? null, t0: turn.t0 ?? null, t1: turn.t1 ?? null }
```

`pos.t0`, `pos.t1`, and `pos.speaker` survive into every unit record. **That is the join key.**

---

## The alignment problem

This is the core engineering problem, the schedule risk, and — done well — the reusable contribution.

**Statement.** Given the same audio transcribed under policies `P₁…Pₙ`, produce a canonical **unit spine** such that a human gold label applied once can be attached to the corresponding unit in every condition, and such that paired statistics are well-defined.

**Why it is not trivial.** Different policies produce different text, different unit counts, and — if a policy changes what counts as a pause worth marking — potentially different turn boundaries. Text-based alignment is circular (the text is the manipulated variable). ID-based alignment is impossible ([Finding 3](#finding-3-unit-ids-are-content-hashes)).

**The approach.** Anchor on time, not text.

1. **Freeze diarization once.** Run `pyannote` a single time on the source audio. Produce a canonical segmentation `S = [(speaker, t_start, t_end)]`. This is the spine. It is policy-independent by construction, because diarization operates on the acoustic signal, not on the transcript.
2. **Constrain every policy to the spine.** Transcribe each diarized segment independently under each policy. Emit one VTT cue per spine segment, with the spine segment's exact `t0`/`t1`. Never let a policy renegotiate segment boundaries.
3. **Set `maxMergeGapSeconds: 0`** at import, so `mergeCues` cannot fuse spine segments and change `N` between conditions. (Recall from [above](#turn-merging) that same-speaker cues merge when the gap is within the window; a zero window makes merging depend only on exact adjacency, which is stable across conditions because the spine is stable.) **Verify this empirically** — the merge condition is `gap <= maxMergeGapSeconds`, so back-to-back segments with `gap === 0` will still merge. If that proves true, use a small negative value or pre-merge nothing by inserting an epsilon gap in the emitted timestamps.
4. **Join on `(pos.speaker, round(pos.t0, 2))`.** With the spine frozen, this key is identical across conditions.
5. **Gold-code once, against the spine**, not against any single condition's text. A human coder listening to segment `k` produces a label for spine index `k`. That label is then valid for unit `k` in every condition — which is exactly the design that makes the comparison fair.

**Falsifiable check to run first, before building anything else:** import the same audio under two trivially different policies, join on `(speaker, t0)`, and confirm a 1:1 match on every segment. If that fails, the whole design fails, and it is better to know in August than in September. Budget one day.

---

## Experimental design

Hold constant: audio, diarization spine, codebook, judge model, judge prompt, temperature, seed. Vary: the transcription policy.

### Policy conditions

Mapped onto [Bucholtz's interpretive/representational axes](./01-literature-landscape.md#a2-bucholtz-m-2000-the-politics-of-transcription):

| ID | Policy | Interpretive (what) | Representational (how) |
|---|---|---|---|
| **P0** | Whisper default, no prompt | Model's implicit policy — *unknown and the point of the study* | Model default |
| **P1** | Clean verbatim | Fillers and false starts removed | Standard orthography, full punctuation |
| **P2** | Full verbatim | Fillers, repetitions, false starts retained | Standard orthography, full punctuation |
| **P3** | Full verbatim, unpunctuated | As P2 | No sentence punctuation — tests [Finding 1](#finding-1-unitization-is-punctuation-dependent) directly |
| **P4** | CA-lite | As P2, plus timed pauses and audible breath | Jefferson-subset notation ([Finding 2](#finding-2-striptags-destroys-angle-bracket-markup)) |

**P0 vs P1/P2 is the headline comparison.** If P0 does not sit cleanly on either side, that is the finding: *the default is not a policy, it is a shrug*, and it varies with audio length and speaker in ways the [ASR literature already hints at](./01-literature-landscape.md#b2-whispers-disfluency-handling-is-inconsistent--and-that-is-the-finding).

**Implementation caution.** Whisper's `initial_prompt` conditions style but does not guarantee compliance, and it competes for the same context that carries prior-segment text. Expect partial compliance and **measure it** — a disfluency-rate-per-condition table is a required sanity check, not an optional one. If prompt steering proves too weak, the fallback is a two-stage design: transcribe once at maximum fidelity, then apply deterministic post-processing rules per policy. That is arguably a *better* design anyway, since it isolates the policy from ASR variance. It is also a weaker claim about Whisper specifically. Decide deliberately.

### Statistics — and Concord already ships them

`server/stats/` is unusually well-stocked for this study. Exports read directly from source:

| Module | Exports | Use here |
|---|---|---|
| `agreement.js` | `percentAgreement`, `cohenKappa` (weighted, ordered), `krippendorffAlpha`, `gwetAC1`, `gwetAC2`, `perClass`, `confusion` | Judge-vs-gold agreement **within** each condition |
| `boot.js` | `bootstrapCI` (B=2000, seeded), **`mcnemar`**, **`tostEquivalence`** | `mcnemar` for paired binary label flips across conditions; bootstrap CIs on κ |
| `correction.js` | `dslMean`, `dslProportion`, **`dslDiff(unitsA, unitsB)`**, `dslOLS`, `dslLogit`, `ppiMean` | `dslDiff` is *literally* a corrected difference between two unit sets — the cross-condition comparison, with machine error already accounted for |
| `descriptives.js` | `crosstab`, `cooccurrence`, `timeTrend`, `correlationMatrix` | `cooccurrence` is the on-ramp to [ENA-style analysis](./01-literature-landscape.md#d-quantitative-ethnography--the-methodological-home) |
| `distributions.js` | `chi2Cdf`, `tCdf`, `normQuantile`, `bhQValues` | χ² for code × condition tables; Benjamini-Hochberg for the multiple-comparison problem you will absolutely have |

Three notes on using them well:

- **`tostEquivalence` is the test you actually want.** The naive framing — "is there a difference between policies?" — invites a null result that says nothing. The interesting question is *equivalence*: can a researcher treat clean and full verbatim as interchangeable within a tolerance of δ? Two one-sided tests answers that, and answers it in a form a methodologist can act on. Pick δ before you look at the data and write it down.
- **`mcnemar(pairs)` requires paired units**, which requires [the alignment problem](#the-alignment-problem) solved. It is the payoff for that work.
- **`dslDiff` is the headline number.** A corrected difference in code prevalence between two transcription conditions, with an honest interval, is the money figure of the paper.

You will also want **Shaffer's ρ** (`rhoR`, R) for the QE reviewer pool — Concord does not ship it. See [01 §D](./01-literature-landscape.md#d-quantitative-ethnography--the-methodological-home).

### Model configuration

`server/providers/ollama.js`: `DEFAULT_BASE_URL = "http://localhost:11434"`, auto-discovered, and the header comment states it is *"the only network adapter allowed under privacy mode 'strict'."* Privacy modes are enforced at the adapter layer, not the UI.

Two consequences:

- **Your existing local-model work transfers.** You have already run seven small models with grammar-constrained JSON via `llama-cpp` on the Lancaster corpus, and built cross-model agreement analysis. Concord's `panel.js` (multi-model panels) and `stability.js` are the same idea with more ceremony around it. Note that `llama.cpp`'s server speaks the OpenAI API, not Ollama's — point the **OpenAI adapter** at a local `baseUrl`, or run Ollama, whichever is less work.
- **"Strict" mode is an IRB asset.** Being able to state in a protocol that no unit text leaves the machine is materially easier to get approved than any argument about vendor no-training commitments. See [02 §IRB](./02-submission-strategy.md#irb--the-penn-state-process). Concord's PII layer supports this too: import takes `pii: "off" | "scan" | "pseudonymize"` (default `scan`), masking covers unit text *and* string metadata with a reversible vault at `projects/<slug>/vault/<corpusId>.json`, and the vault is excluded from every replication archive.

---

## The evaluation-data contract

Per your instruction to design against a hypothetical matched dataset rather than chase a specific one, here is the contract. Any corpus satisfying it drops in.

```
EvalCorpus := {
  audio:      [ { id, path, sample_rate, duration_s } ],
  spine:      [ { audio_id, seg_id, speaker, t0, t1 } ],        // frozen diarization
  human_txt:  [ { seg_id, text, convention } ],                  // gold transcript
  human_code: [ { seg_id, code, present: bool, rationale: str } ],
  codebook:   [ { code, definition, inclusion, exclusion, examples[] } ]
}
```

Field notes, each earned from something above:

- **`spine` is the primary key of the entire study.** Everything joins on `seg_id`. It must be produced once and never regenerated.
- **`convention`** on `human_txt` records which transcription convention the human used — because the human transcript is itself one condition, not ground truth for all conditions. This is the Ochs point, made operational.
- **`rationale`** is not decoration. The [deductive-coding literature](./01-literature-landscape.md#c2-inter-rater-reliability-studies-llm-vs-human) finds that step-by-step reasoning interventions improve both validity and IRR, and Concord's evidence inspector surfaces per-model rationales as a first-class object. Human rationales let you compare *reasons*, not just labels — and disagreement in reasons with agreement in labels is a genuinely interesting result.
- **`codebook`** with explicit inclusion/exclusion criteria is required for deductive coding to work at all. If a candidate corpus has labels but no codebook, the study is much weaker; you cannot ask a model to apply a rubric you do not have.

### Candidate corpora

The honest headline: **no single public corpus satisfies the full contract.** The pieces exist separately.

| Corpus | Audio | Human transcript | Human codes | Codebook | Notes |
|---|---|---|---|---|---|
| [**Santa Barbara Corpus (SBCSAE)**](https://www.linguistics.ucsb.edu/research/santa-barbara-corpus-spoken-american-english) | ✅ | ✅ **close transcription incl. disfluencies and overlaps** | ❌ | ❌ | Audio downloadable from [TalkBank](https://talkbank.org/) as MP3/WAV; transcripts free; ~249k words across Parts 1–4; timestamps align transcript to audio at the **intonation unit** level. **Best available source for the transcription-fidelity half.** Also on [Internet Archive](https://archive.org/details/santabarbara_201509) and [LDC](https://catalog.ldc.upenn.edu/LDC2000S85). |
| [**TalkMoves**](https://arxiv.org/abs/2204.09652) | ❌ **confirmed** | ✅ | ✅ | ✅ | 567 human-transcribed K-12 math lesson transcripts, speaker-segmented, **sentence-level annotation for ten discursive moves** grounded in accountable talk theory; 174,186 teacher + 59,874 student utterances; also carries Switchboard-style dialogue act labels; CC BY-NC-SA 4.0. Suresh, Jacobs, Harty, Perkoff, Martin & Sumner, LREC 2022. **Transcripts only — the source video/audio is not released.** Repos: [SumnerLab/TalkMoves](https://github.com/SumnerLab/TalkMoves), and a packaged copy via [edu-convokit](https://edu-convokit.readthedocs.io/en/latest/tutorial_talkmoves.html). [ACL Anthology](https://aclanthology.org/2022.lrec-1.497/) |
| **NCTE transcripts** (Demszky & Hill) | ❌ `[unverified]` | ✅ | ✅ | ✅ | 4th/5th grade math lessons with observation scores. Access is gated. `[unverified — not checked this pass]` |
| **TalkBank / CHILDES / CABank** | ✅ | ✅ CHAT format, media-linked | partial | varies | The broadest source of **media-linked** transcripts with rich disfluency coding. CABank in particular holds CA-style transcripts. Worth a dedicated afternoon. |
| **Your Lancaster city-council corpus** | ✅ | ❌ | ❌ | partial | 78 public meetings, already run through `whisper large-v3` + `pyannote` + 7 local models with a two-phase extraction/scoring codebook. **Public-record audio, no private identifiable information.** The transcription and coding are machine-produced, so it cannot serve as gold — but it is the ideal corpus for the *harness* demonstration and for pipeline shakedown, with essentially zero access friction. |

**Two things this table settles.** First, TalkMoves is confirmed transcripts-only, which rules it out as a full-contract corpus — but it remains the best available source for a **codebook**: ten discursive moves grounded in accountable talk theory, applied by humans at sentence level across 234k utterances. Borrow the construct definitions even though you cannot borrow the audio. Second, since no public corpus is complete, the composition below is not a compromise; it is the design.

Also worth an hour: **[edu-convokit](https://edu-convokit.readthedocs.io/en/latest/tutorial_talkmoves.html)** (Rose Wang et al.), a Python library for education conversation data that packages TalkMoves and several sibling corpora behind a common interface. It is the fastest route to surveying what human-coded education-discourse data actually exists, and it may already solve part of your loader problem.

**Recommended composition for an October submission:**

- **Harness demonstration** on the Lancaster corpus — it is yours, it is public record, it is already processed, and it demonstrates the tool working end to end at real scale.
- **Fidelity measurement** on a handful of SBCSAE conversations — this is where you can compare Whisper output under each policy against a genuinely close human transcript.
- **Gold coding** hand-produced by you on ~100–200 spine segments against a small codebook you author. Tedious but tractable, entirely under your control, and — as Rae's argument would have it — the part that requires actually listening to the recordings, which is the point.

That composition needs no data use agreement and no protocol. See [02 §IRB](./02-submission-strategy.md#what-this-means-for-the-october-timeline).

---

## Build phases

### Phase 1: the policy harness

```
audio → pyannote (once) → spine.json
spine.json + policy_config → whisper per segment → {policy_id}.vtt
```

Deliverables: `spine.json`, N conforming VTT files, a `policies/*.yaml` directory that is the human-readable record of each transcription policy. **The policy files are a contribution in themselves** — they are the artifact that makes the researcher's choice explicit, versioned, and citable, which is the whole argument of the paper.

### Phase 2: alignment verification

Import all N into Concord. Join on `(pos.speaker, pos.t0)`. Assert 1:1. Report unit-count drift under both `turn` and `sentence` schemes — that table is [Finding 1](#finding-1-unitization-is-punctuation-dependent) made empirical, and it is a result even if nothing else works.

### Phase 3: the comparison

Freeze codebook and judge. Run all N. Gold-code the spine once. Compute:

- κ / α / AC1 of judge-vs-gold **within** each condition (`agreement.js`)
- `dslProportion` per code per condition, and `dslDiff` between condition pairs (`correction.js`)
- `mcnemar` on paired label flips (`boot.js`)
- `tostEquivalence` against a pre-registered δ (`boot.js`)
- BH correction across the code × condition-pair grid (`distributions.js:bhQValues`)

### Phase 4: the four pages

See [02 §Backward plan](./02-submission-strategy.md#backward-plan).

### Explicit non-goals for v1

Say these out loud in the paper's limitations section rather than letting a reviewer find them:

- Not claiming the LLM interprets. Only that it labels consistently enough to detect an upstream-induced shift.
- Not claiming any policy is correct. The argument is that the choice should be the researcher's, explicit, and reported.
- Not attempting inductive code generation — [the literature says it does not work well](./01-literature-landscape.md#c1-the-numbers-do-not-line-up-and-that-is-itself-the-finding).
- Not generalizing beyond Whisper, one judge model, and one corpus. Single-model, single-corpus results are what a 4-page demo paper supports.

---

**Next:** [04 — Coursework alignment](./04-coursework-alignment.md)
