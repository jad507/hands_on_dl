# Execution findings from the Windows workstation

**Parent:** [00-INDEX](./00-INDEX.md)
**Written:** 2026-09-03, on the Windows machine that holds the corpus and the GPU.
**Corrects:** [05 — upgrade plan](./05-hands-on-dl-upgrade-plan.md) §1 and §5, [06 — prosody stress test](./06-prosody-stress-test.md) open questions, and `hands_on_dl/plans/windows_environment_upgrade_status.md` §1.

The planning documents were written on machines that could not see this one. This
records what happened when Steps 0-2 were actually executed, in the order the
findings change the plan. Two of them change what the paper claims.

Everything here is reproducible from `hands_on_dl` at commit `475cd80` and
later; the scripts named are in that repository and the numbers come from
`RESULTS.md` there.

---

## 1. The pilot in §1 of doc 05 does not measure transcription policy. It measures the batching window.

**This is the big one, and the finding survives — it just has a different cause
than the one the audit assigned it.**

Doc 05 §1 identifies the 26 meetings present in both `_standard` and
`_exclusive` pyannote variants as "structurally the ISLS experiment, one stage
earlier in the pipeline: the same audio, processed two different ways upstream,
then coded by the same model with the same prompt." It reports flag counts
differing on 16 of 26 pairs for ministral-8b while aggregate totals move ~1%, and
reads that as the Southwell pattern reproduced in local data.

Align the two variants by time — `blockmatch.py`, which is the alignment doc 05
Step 1.4 asks for and doc 03 needs — and the premise does not hold:

| | |
|---|---|
| Blocks on the standard side | 3,339 |
| Aligned 1:1 by time | 3,250 (97.3%) |
| ...of which **byte-identical text** | **3,230 (99.4%)** |
| ...of which text differs | 20 (0.6%) |
| No 1:1 partner (split / merge / tangle) | 89 (2.7%) |

**The two diarization modes barely disagree about what was said.** They disagree
about where a small number of turn boundaries fall. So whatever is destabilising
the coding, it is almost never the transcript.

Holding the text byte-identical and splitting on whether the 3-block chunk the
model judged the block inside was *also* identical:

| model | identical chunk | shifted chunk | ratio |
|---|---|---|---|
| gemma-4-4b | 0.22% | 13.77% | 63x |
| ministral-8b | 0.35% | 11.67% | 33x |
| phi-4 | 0.61% | 17.14% | 28x |
| qwen3.5-9b-q6 | 1.27% | 13.67% | 11x |
| qwen3.5-9b-q8 | 0.35% | 14.30% | 41x |
| deepseek-r1-7b | 0.66% | 14.30% | 22x |
| deepseek-r1-14b | 0.26% | 2.21% | *base-rate artifact* |

Normalised by the blocks either variant called a public comment — which removes
the base-rate artifact that makes deepseek-r1-14b look stable when it is merely
silent — the shifted-chunk **disagreement rate is 50-60%** for the five usable
models.

The mechanism is `P1_CHUNK_SIZE = 3` in `llm_classify_human_themes.py`. Phase 1
batches blocks three at a time and asks the model to judge the batch, so a single
inserted or deleted block upstream shifts every later chunk boundary and every
subsequent block is judged alongside different neighbours.

### Why this is a better result than the one it replaces

1. **The text is held byte-identical, not merely similar.** There is no
   transcript confound at all. The natural experiment is cleaner than the design
   it was standing in for.
2. **It is the same thesis, one layer up.** Doc 00 states the claim as "an
   unexamined ASR step silently fixes methodological choices that the field
   considers the researcher's to make." `P1_CHUNK_SIZE` was chosen to fit a
   context window, was never treated as a methodological decision, and decides
   the coding of roughly one block in seven. The argument generalises from the
   ASR step to the analysis harness, and it is *more* uncomfortable there,
   because the harness is unambiguously the researcher's own.
3. **It answers the Southwell objection differently.** Doc 06 answers it by
   construct location: lexical constructs survive, prosodic ones do not. This
   adds a second axis that has nothing to do with word error rate — the unit's
   *context window* is a free parameter, and prior work held it fixed without
   saying so.

### What must be said honestly alongside it

**The effect is destabilising, not directional.** The obvious test — condition on
how many of a block's chunk-mates the model flagged — gives P(flag) of 0.150,
0.182, 0.711 for 0, 1 and 2 flagged neighbours, and 73% concordance in a
within-block design. Both are near-worthless: all three blocks in a chunk are
classified in **one forward pass** and emitted as one JSON object, so their
labels are correlated by construction, and public comments genuinely cluster in
time.

Re-run with an exogenous neighbour measure — pyannote's `category` field, which
no language model ever saw — the effect disappears: **47.7% concordant, z =
-0.75, n = 258.** See `analyze_chunk_context.py`.

So: *the batching window destabilises unit-level coding* is supported. *The
batching window biases coding toward finding comments* is not. And the negative
result is weak rather than strong — `category` is a coarse proxy that the
pipeline's own comments call unreliable, and at n = 258 this test would miss a
small effect. The clean version needs human labels (Step 4) or a direct
experiment at several chunk sizes and offsets.

**The effect clears the instrument's noise floor. Measured, not assumed.**

A full re-run of `gemma-4-4b` phase 1 over the corpus (3h32m, 78 meetings,
10,069 blocks) against the committed June output gives the noise floor:

| | |
|---|---|
| Blocks whose classification changed | **81 (0.80%)** |
| Meetings reproducing exactly | 38 of 78 (**48.7%**) |
| Corpus Jaccard | 0.9576 |
| Krippendorff alpha (run vs run) | 0.9734 |

Two things about that number matter more than the number.

**The noise is not uniform.** It concentrates **7.7x** on contested blocks:
blocks all five core models agree about change 0.30% of the time, blocks they
disagree about 2.34%. Non-determinism lands where the judgement is hard, so a
pooled effect-to-floor ratio mixes two populations and should not be quoted
alone.

**Within consensus stratum the chunk effect survives, and that is what makes it
a mechanism rather than ambiguity amplification.** Same-text 1:1 blocks in the
natural experiment:

| | unanimous (0 or 5 votes) | contested (1-4 votes) |
|---|---|---|
| chunk identical | 0.12% | 1.98% |
| chunk shifted | **6.09%** | **33.94%** |

On blocks *every one of the five models agrees about*, shifting the batching
window still flips 6.09% of classifications. Ambiguity makes the effect worse --
6% to 34% -- but does not create it.

### The controlled replication, and the ratio it corrects

The above is a natural experiment: the two pyannote modes *happen* to shift
batch boundaries. A designed version ran the same 12 meetings and 1,231 blocks
five times with the corpus held fixed, varying only `--chunk-size` and
`--chunk-offset` (`chunk_experiment.py`). Conditions A (size 3, offset 0), **A2
(size 3, offset 0 again -- the control)**, B (size 3, offset 1), C (size 1), D
(size 5).

| stratum | n | A vs A2 (floor) | A vs B (effect) | ratio |
|---|---|---|---|---|
| unanimous | 987 | 1.01% | 6.08% | **6.0x** |
| contested | 244 | 6.97% | 36.48% | **5.2x** |
| all | 1,231 | 2.19% | 12.10% | **5.5x** |

Set against the natural experiment:

| | natural | controlled |
|---|---|---|
| effect, unanimous | 6.09% | **6.08%** |
| effect, contested | 33.94% | **36.48%** |
| floor, unanimous | 0.12% | **1.01%** |
| floor, contested | 1.98% | **6.97%** |

**The effect replicated to within 0.01 of a percentage point.** The magnitude is
now measured twice, by two designs, and agrees.

**The floor did not, and the reason is selection.** A block enters the natural
experiment's "identical chunk" bucket only if its text *and* its whole enclosing
chunk matched across variants -- which happens preferentially in stable,
unambiguous stretches. Conditioning on stability and then measuring instability
understates the floor about fivefold.

**The ratio is model-dependent and must not be pooled.** Replicating the same
three conditions on `ministral-8b`, same 12 meetings and same corpus directory:

| model | stratum | floor (A vs A2) | effect (A vs B) | ratio |
|---|---|---|---|---|
| gemma-4-4b | unanimous | 1.01% | 6.08% | 6.0x |
| gemma-4-4b | contested | 6.97% | 36.48% | 5.2x |
| gemma-4-4b | all | 2.19% | 12.10% | **5.5x** |
| ministral-8b | unanimous | 0.10% | 2.53% | 25.0x |
| ministral-8b | contested | 1.64% | 27.46% | 16.8x |
| ministral-8b | all | 0.41% | 7.47% | **18.4x** |

A 3x spread in the ratio, driven almost entirely by the floor -- which is itself
5x apart between the two models. An earlier draft of this document reported
17-51x from the natural experiment; a later one reported 5.5x. Both were single
numbers where the honest answer is a per-model range.

**Lead with the two cross-model invariants instead**, which are what actually
replicate:

- On **contested blocks both models flip 27-36%** under a pure batching shift
  (gemma 36.48%, ministral 27.46%). This is the tightest agreement anywhere in
  the analysis.
- Both lose a substantial share of their **own** most stable positives -- blocks
  they flagged in two independent runs at the same settings: **26.4%** for gemma,
  **18.1%** for ministral.

**Two cautions about the natural experiment's per-model figures.** They should be
used to establish that the effect exists and for nothing else.

First, they are not rank preserving. The natural design makes gemma look quieter
than ministral (0.22% against 0.35% identical-chunk); the controlled design makes
it five times noisier (2.19% against 0.41%). The ordering inverts on the one pair
that can be checked.

Second, there is **no cheap proxy for context sensitivity.** The tempting
shortcut -- screen a model with one repeat run, since a noisy model is presumably
a context-sensitive one -- does not work. Across the six usable models the
correlation between identical-chunk rate and shifted-chunk rate is r = +0.13 at
n = 6. The floor and the effect have to be measured separately, for each model,
which is two runs rather than one.

### Two mechanisms the natural experiment could not show

**Removing batch context changes which blocks are flagged -- but how much it
changes the count is model-specific.**

| model | size 3 | size 1 | ratio | size-3 flags kept at size 1 |
|---|---|---|---|---|
| gemma-4-4b | 247 | **387** | 1.57x | 233 / 247 (94.3%) |
| ministral-8b | 240 | **237** | 0.99x | 192 / 240 (**80.0%**) |

An earlier draft of this document reported "batch context suppresses flagging"
as a mechanism, on gemma's 57% increase. **That is a gemma finding.** ministral's
count is flat -- three blocks -- while **20% of its flags change identity**. Had
only counts been compared, the conclusion would have been that context does
nothing to ministral, which is the aggregate-stable / unit-unstable trap this
project exists to point at.

State the surviving claim at the membership level: removing the batch context
churns 6-20% of a model's flags, whether or not the total moves.

**The shift degrades in both directions at once.** Of the blocks flagged in
*both* A and A2 -- stable positives by the strictest available definition --
only **73.6%** (gemma) and **81.9%** (ministral) survive the offset shift. Not a
bias with a sign: a fifth to a quarter of each model's own most reliable
positives fall out when only the batching moves.

**Changing *which* context beats changing *how much*.** For gemma, A vs D (size
3 to 5) is 9.83%, smaller than A vs B (offset by one) at 12.10%.

### A methodological note that applies to everything above

**Every direction in this analysis has replicated across models. No magnitude
has.** The effect-to-floor ratio differs 3x between the two models tested, the
noise floor 5x, and the size-1 count behaviour differs qualitatively. Any
single-model magnitude here should be treated as provisional, and claims are
safer stated at the membership level than the count level.

### A circularity to state rather than bury

Cross-tabulating conditions against the June 5-model consensus looks damning for
B: on the 865 blocks no model flagged, A flags 7 and B flags 28; on the 122 all
five flagged, A keeps 116 and B keeps 93.

**That does not license the obvious reading.** The June corpus was produced by
all five models at chunk size 3, offset 0 -- condition A's exact settings -- and
gemma-4-4b is one of the five. The consensus is doubly favourable to A: same
batching, partly the same model. A agreeing with it more than B is close to
tautological. Report that cross-tab as descriptive only, never as evidence of
accuracy. The claims needing no external reference are the ones that stand:
12.10% against a 2.19% floor, and 73.6% of stable positives lost.

**A second finding hiding in the same run:** only 48.7% of meetings reproduce
exactly while the aggregate flagged count moves 0.9% (1,863 to 1,880). That is
the Southwell aggregate-stable / unit-unstable pattern appearing with **no
experimental manipulation at all** -- the same model, the same input, run twice.
Some of what prior work reads as robustness of discourse-level constructs is
this.

The drift direction is 49 added versus 32 dropped, z = 1.89. Not significant and
**not claimed**.

### Consequence for the experimental design in doc 03

Add `p1_chunk_size` to the pre-registered parameters, and hold it constant across
transcription-policy conditions. If it varies with policy — and it will, because
a policy that changes segmentation changes the block count — then the policy
effect and the framing effect are confounded and cannot be separated after the
fact.

---

## 2. Doc 06's open question is answered: use CAPITALS, not asterisks

Doc 06 proposes policy P5 (prominence-annotated transcripts) and leaves the
notation open: *"use Jefferson-style marking — capitals for stress or asterisks
(`*money*`). Test which survives tokenization."* It correctly identifies
`stripTags()` as the hazard.

`stripTags()` is not the hazard. Both survive it. The hazard is two modules
downstream, and it is silent.

`splitSentences()` in `server/ingest/unitize.js` splits after `.!?` only when the
next non-whitespace character matches `\p{Lu}` or a digit, with a special case
that looks one character past a quote or an opening bracket. An asterisk is none
of those, so a sentence whose first word is emphasised looks like it starts in
lowercase and **the split is suppressed**.

Driven through Concord's real modules (`hands_on_dl/tools/concord_marker_probe.mjs`,
pinned by `tests/test_concord_markers.py`):

| notation | survives ingest | preserves unit boundaries |
|---|---|---|
| `MONEY` (capitals) | yes | **yes** |
| `[money]` | yes | **yes** |
| `"money"` | yes | **yes** |
| `*money*` | yes | **no** |
| `**money**`, `_money_`, `^money^`, `{money}`, `\|money\|` | yes | **no** |
| `<em>money</em>` | **no** — silently stripped | n/a |

`"He denied it. *Money* was the issue."` yields **one** unit where the unmarked
text yields two.

That is disqualifying rather than cosmetic, and the reason is doc 03's own: unit
ids are content hashes, N is the denominator of every reported rate, and the
judge is asked about whatever the unit contains. A notation that quietly fuses
two sentences corrupts all three while producing output that looks correct.

**Decision: P5 uses CAPITALS**, with square brackets as the fallback if capitals
interact badly with a judge prompt.

Also demonstrated rather than assumed, confirming doc 03 finding 3: marking a
word changes the unit id (`u_7ca821c35c74adfb` plain vs `u_10d1e18e7506105e`
with capitals). Cross-condition joins must go through time anchors.
`blockmatch.py` is that join and it is written.

**Still open**, and doc 06 already frames the right control: does a judge given
`MONEY` read it as prosodic emphasis, as shouting, or ignore it? Give the model
the *wrong* prominence annotation and see whether it produces the meaning that
annotation implies. Needs no new corpus.

---

## 3. The corpus is smaller than every document says, and two files are contaminated

Doc 05 and the upgrade plan both quote 78 meetings; the audit says 55 distinct
meetings, 26 in two variants. `audit_corpus.py` resolves this:

```
81  files in downloads/comments
-3  meetings no model has ever coded
78  coded files  <- the number every document quotes
-2  stale files in the superseded commenter_blocks schema
76  legitimately coded files, over 50 distinct meetings
```

Distinct meetings is **53, not 55**: 26 multi-variant and 27 single-variant.

The two stale files are worse than a miscount. They are 2026-05-19 leftovers
using `commenter_blocks` where the 2026-05-28 re-run writes `blocks`, and they
**shadow meetings that already exist as `_standard`/`_exclusive` pairs**. Because
`get_blocks()` falls back to `commenter_blocks` without comment, all seven models
coded them — against a *pre-filtered* 31-block input instead of the full
243-block meeting for one of them. That is exactly the pre-filtering
`llm_classify_human_themes.py`'s own comment warns against:

> do NOT pre-filter to commenter_candidate blocks here. The
> recurring/commenter_candidate classification is unreliable for this task

They have deliberately **not** been deleted. Removing them changes every
corpus-level number already computed, and that should be one deliberate act with
a notebook entry rather than a side effect of a cleanup.
`tests/test_corpus_integrity.py` pins them so a third one is a test failure.

---

## 4. The artifacts doc 05 relies on were never lost, and its numbers reproduce exactly

`windows_environment_upgrade_status.md` §1 concluded that five analysis
artifacts were gone and that doc 05's figures "currently have no file behind
them on any machine." That was wrong, and instructively so: the search was
correct for the Windows machine but could not check `AITranscribe`, which was not
on it at the time and had no remote to clone from.

`AITranscribe/hands_on_dl/` is a snapshot of the repository dated 2026-07-17 —
the tree the audit was actually run against. `compare_model_agreement.py` and
`plans/roar_plan.md` were recovered from it; the other three were derived output
and have been regenerated.

Re-run against the committed corpus, the recovered script reproduces every figure
doc 05 quotes, to the digit: 3,263 flagged, 785 unanimous (24.1%), 1,719
majority-agreed (52.7%), 2,478 contested (75.9%), cross-family Jaccard
0.372-0.554, qwen q6-vs-q8 0.840.

**Doc 05 §1 and the audit numbers can be cited.** With one caveat carried from
§1 above: they describe the June 2026 corpus, which is not reproducible on this
machine today, so they are a description of that artifact rather than of what the
pipeline does now.

### Two corrections to how those numbers should be reported

**The unit universe was wrong.** The original computed agreement only over blocks
some model flagged. That selects on the outcome and makes chance correction
impossible, because the negative class — roughly 95% of blocks — is deleted.
Computed over all 10,017 blocks:

| statistic | all blocks | flagged blocks only |
|---|---|---|
| Krippendorff's alpha | 0.590 | 0.234 |
| Gwet's AC1 | 0.827 | 0.256 |
| Fleiss' kappa | 0.590 | 0.234 |

Both belong in the paper. Over all blocks the models agree that most things are
not public comments — true, and nearly free. Restricted to the actual judgement,
agreement falls by two thirds. Quoting either alone misleads.

**The 0.840 is not an agreement measurement**, as the status document already
noted. It is one model at two quantisations. It is now reported in its own table
as a self-consistency ceiling, which is genuinely useful: it bounds how much
agreement two different models could plausibly show.

---

## 5. Status of doc 05's Part 2, as executed

| Step | Status |
|---|---|
| 0. Lab notebook | **Done.** `NOTEBOOK.md` and `RESULTS.md` exist and are populated. |
| 1. Mine the diarization pilot | **Done, and it turned into something else.** See §1. `compare_diarization_variants.py`, `blockmatch.py`, `analyze_chunk_context.py`, and Krippendorff/Gwet in `agreement.py` with tests against published reference values. |
| 2. Portability + prompt versioning | **Done 2026-08-28.** No absolute path literals remain. Prompts are in files with hashes recorded in every output. |
| 3. Finish + analyze phase 2 | **Not started.** But phase 2 turns out to be far *more* stable than phase 1 — mean absolute theme-score delta 0.002-0.005 on byte-identical text, 0.2-0.8% crossing the 0.5 threshold. Phase 2 scores one comment at a time and so has no chunk to shift, which is independent support for the §1 mechanism. |
| 4. Human labels | **Not started.** Still the binding constraint on everything involving accuracy, and now also the clean test of §1's directionality question. |
| 5. Concord bridge | **Partly.** Concord is cloned and its release gate passes. The notation question (§2) and the id-stability question are answered. `export_vtt.py` is not written. |
| 6. ROAR / API | Correctly deferred. `plans/roar_plan.md` recovered and annotated. |

**The one thing to carry into the paper draft:** doc 05 said "if you only do two
things this week: start the notebook, and run the standard-vs-exclusive
comparison. The second one may already be your paper." That was right. It is just
a different paper than expected — the instrument that destabilises the coding is
the analysis harness, not the ASR, and the transcript is held byte-identical
while it happens.

---

**Back to:** [00-INDEX](./00-INDEX.md)
