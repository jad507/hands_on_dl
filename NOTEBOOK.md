# Lab Notebook -- hands_on_dl

Append-only. Newest entry at the top. One entry per work session, however short.
Never edit a past entry to make it correct: write a new one saying so and link
back. The record of being wrong is the most valuable thing in here.

Every entry carries the commit hash. An entry without one cannot be reproduced.
Fill in **Surprised by** and **Open question** even when the answer is "nothing".

Scaffold and rationale: `AITranscribe/docs/isls2027/NOTEBOOK-template.md`.
Companion: `RESULTS.md`, one row per experiment, for finding a number fast.

---

## 2026-09-04 (later) -- ministral replicates the effect. The ratio is model-dependent: 5.5x to 18.4x.

**Commit:** 326b94b
**Ran:** `.
un_chunk_experiment.ps1 -Model ministral-8b -Conditions "A,A2,B"` (65m)
**Config:** same 12 meetings, same 1,231 blocks, same corpus directory as the
gemma run. Only the model differs.

**Result:**

| model | stratum | n | floor (A vs A2) | effect (A vs B) | ratio |
|---|---|---|---|---|---|
| gemma-4-4b | unanimous | 987 | 1.01% | 6.08% | 6.0x |
| gemma-4-4b | contested | 244 | 6.97% | 36.48% | 5.2x |
| gemma-4-4b | **all** | 1,231 | **2.19%** | **12.10%** | **5.5x** |
| ministral-8b | unanimous | 987 | 0.10% | 2.53% | 25.0x |
| ministral-8b | contested | 244 | 1.64% | 27.46% | 16.8x |
| ministral-8b | **all** | 1,231 | **0.41%** | **7.47%** | **18.4x** |

Stable positives lost to the shift: gemma **26.4%**, ministral **18.1%**.

**The effect replicates. The ratio does not, and that corrects what I wrote
three hours ago.** I said "5.5x is the number, not 17-51x". 5.5x is *gemma's*
number. ministral gives 18.4x. The honest statement is a **range of 5.5x to
18.4x overall, 5.2x to 25.0x by stratum, and it depends on the model.** A single
ratio should not be quoted at all.

**What is genuinely stable across the two models** -- and this is the part that
should carry the paper:

- Both show a large chunk-framing effect on byte-identical text.
- On **contested blocks both flip 27-36%** under a pure batching shift
  (gemma 36.48%, ministral 27.46%). That is the tightest cross-model agreement
  in any of this.
- Both lose a substantial share of their *own* most stable positives:
  26.4% and 18.1%.
- In both, the effect is several times the floor in every stratum.

**What is not stable, and has to be measured per model rather than assumed:**

- The **floor differs 5x between models**: gemma 2.19%, ministral 0.41%. Gemma
  is markedly noisier at fixed settings. Both are Q8 quantisations of similar
  size, so this is a property of the model, not obviously of the quantisation.
- Consequently the ratio differs 3x.

**On my earlier "the natural experiment underestimated the floor by 5x":** that
diagnosis holds for gemma (0.12% natural against 1.01% controlled on the
unanimous stratum) but I overgeneralised it. ministral's controlled unanimous
floor is 0.10%, which is *lower* than the pooled natural figure. The pooled
natural table mixed five models with floors spanning at least 0.10% to 2.19%, so
its per-stratum numbers were an average over models with very different noise --
which is a second reason not to quote it, independent of the selection bias.

**Surprised by:** how much cleaner ministral is. Flagged counts of 240 / 239 /
242 across the three conditions, against gemma's 247 / 258 / 260. Its control
moved 5 blocks out of 1,231. I had assumed run-to-run noise was a property of
the *harness* -- llama.cpp, the GPU, batching in the runtime -- and it is
substantially a property of the model.

That is worth stating because it changes what the reproducibility finding means.
`compare_corpus_runs.py` measured 0.80% for gemma across the June-September gap.
If ministral's floor is 0.41% *within a session*, its cross-toolchain figure
might be much lower, and the June corpus may be more citable for some models
than others. Untested.

**Decided:**
- Report per-model ratios, never a pooled one.
- Lead with the two cross-model invariants -- the 27-36% contested flip rate and
  the loss of the model's own stable positives -- rather than with a ratio.
- Measure the floor for any model before quoting an effect for it. It is one
  extra run of the same condition and it is not optional.

**Next:** phi-4 would make three models, and it had the *highest* natural
shifted-chunk rate (17.14%), so it is the most favourable case and worth having
for the range. Also still open: the offset 0/1/2 dose-response curve.

**Tested that idea immediately and it does not hold.** The speculation was that
a model's run-to-run noise might predict its context-sensitivity, which would let
a practitioner screen for this problem with one cheap repeat run instead of a
full experiment. Across the six usable models in the natural experiment, the
correlation between identical-chunk rate and shifted-chunk rate is **r = +0.13**
at n = 6. No relationship. The shortcut does not exist; the effect has to be
measured directly.

**And a sharper reason to stop using the natural experiment's per-model floors
at all.** They do not merely understate the level -- they are not rank
preserving. On the one pair that can be checked against a proper control:

| | gemma-4-4b | ministral-8b |
|---|---|---|
| natural, identical-chunk | 0.22% | 0.35% |
| controlled, A vs A2 | **2.19%** | **0.41%** |

The natural design says gemma is the quieter model. The controlled design says
it is five times noisier. **The ordering inverts.** One inversion out of one
checkable comparison is enough: those figures should not be used to compare
models, only to establish that the effect exists.

**Open question:** is gemma's higher floor related to its much higher flagged
count under size 1 (387 against size 3's 247)? Both look like the same
underlying looseness, and unlike the correlation above this one is a
within-model question rather than a six-point regression. Needs condition C on
ministral to test -- one more run.

---

## 2026-09-04 -- Controlled experiment: the effect replicates exactly, the noise floor does not. Ratio is 6x, not 51x.

**Commit:** 232baa1
**Ran:** `.
un_chunk_experiment.ps1 -Model gemma-4-4b` (2h 54m), then
`python chunk_experiment.py analyse`
**Config:** gemma-4-4b, 12 meetings, 1,231 blocks, phase 1, temperature 0,
corpus fixed across conditions.

**Scoring my predictions from the previous entry:**

| # | prediction | actual | verdict |
|---|---|---|---|
| 1 | A vs A2 noise 0.1-0.5% | **2.19%** | **wrong, by 4-20x** |
| 2 | A vs B effect 8-15% | **12.10%** | right |
| 3 | A vs C large, sign unknown | C flags **+57%** | right to not guess |
| 4 | size 5 less stable than size 3 | A vs D 9.8% < A vs B 12.1% | wrong |

**The headline, and it revises what I said earlier today downward.**

Stratified the same way as the natural experiment, using the June 5-model
consensus as an exogenous stratum:

| stratum | n | A vs A2 (noise) | A vs B (effect) | ratio |
|---|---|---|---|---|
| unanimous (0 or 5 votes) | 987 | 1.01% | 6.08% | **6.0x** |
| contested (1-4) | 244 | 6.97% | 36.48% | **5.2x** |
| all | 1,231 | 2.19% | 12.10% | **5.5x** |

Set that beside the natural experiment:

| | natural (variant pairs) | controlled |
|---|---|---|
| effect, unanimous blocks | 6.09% | **6.08%** |
| effect, contested blocks | 33.94% | **36.48%** |
| floor, unanimous blocks | 0.12% | **1.01%** |
| floor, contested blocks | 1.98% | **6.97%** |
| ratio | 17-51x | **5.2-6.0x** |

**The effect replicated to within 0.01 of a percentage point.** 6.09% against
6.08% on unanimous blocks is as close as this kind of measurement gets. The
mechanism is real and its magnitude is now measured twice by different designs.

**The noise floor was underestimated by a factor of five, and the reason is
selection.** The natural experiment's "identical chunk" bucket is not a random
sample of blocks: a block only lands there if its text *and* its whole enclosing
3-block chunk matched across the two variants, which happens preferentially in
stable, unambiguous stretches of a meeting. Conditioning on stability and then
measuring instability understates it. The controlled A-vs-A2 has no such
selection -- every block, same settings, run twice.

So **5.2-6.0x is the number to report, not 17-51x.** I stated 51x earlier today
and it was inflated by that selection effect. The effect is still unambiguous --
Jaccard 0.55 against a 0.90 control, alpha 0.63 against 0.93 -- and the ratio is
now nearly constant across strata (6.0x and 5.2x) where the natural experiment
gave 51x and 17x. That consistency is itself a sign the controlled design is
measuring one thing.

**Two mechanisms visible that the natural experiment could not show.**

1. **Batch context suppresses flagging.** Size 1 flags 387 blocks against size
   3's 247, a 57% increase, and it is nearly a superset: 233 of A's 247 flags
   survive, and C adds 154. So the model alone with a block says "public
   comment" far more often than the model shown that block beside two
   neighbours. Context does not refine the judgement so much as damp it.
2. **The offset shift degrades in both directions at once.** Of the 239 blocks
   flagged in *both* A and A2 -- the stable positives, by the strictest
   available definition -- only **73.6% survive the offset shift**. It is not a
   bias with a sign; a quarter of the model's own most reliable positives fall
   out when only the batching moves.

**A circularity I have to flag rather than bury.** I also cross-tabulated each
condition against the June 5-model consensus, and it looks damning for B: on the
865 blocks no model flagged, A flags 7 and B flags 28; on the 122 all five
flagged, A keeps 116 and B keeps 93. Read naively that says the offset shift
makes the classifier worse in both directions.

**It does not license that.** The June corpus was produced by all five models at
chunk size 3, offset 0 -- exactly condition A's settings -- and gemma-4-4b is one
of the five. The consensus is therefore doubly favourable to A: same batching,
and partly the same model. A agreeing with it more than B does is close to
tautological. That analysis is descriptive only and must not be reported as
evidence of accuracy. The claims that survive are the ones needing no external
reference: 12.10% vs 2.19%, and 73.6% of stable positives lost.

**Surprised by:** the floor, badly. I predicted 0.1-0.5% and wrote it down; it
came in at 2.19%. Two consecutive runs of the same model, same file, same
settings, same session, temperature 0, disagree about 27 of 1,231 blocks. The
flagged *count* alone moved 247 to 258. I had been treating temperature 0 as
approximately deterministic and it is not, at any of the three scales I have now
measured it (0.22%, 0.80%, 2.19% -- and the differences between those three are
selection effects, not disagreement).

Also surprised that size 5 sits *closer* to size 3 than an offset shift at size
3 does (9.8% vs 12.1%). Changing how much context a block gets perturbs the
answer less than changing *which* context it gets. That is a nice sharp
statement of the mechanism and I did not predict it.

**Decided:**
- Report **5.5x** (or 6.0x/5.2x by stratum) as the effect-to-floor ratio. Retire
  the 17-51x figures with a note explaining the selection bias, since they are
  already written into `07-windows-execution-findings.md`.
- Report the consensus cross-tab only with the circularity stated, or not at all.
- The A-vs-A2 floor of 2.19% is the one to use for this design. The 0.80%
  corpus-wide figure answers a different question (June vs September, whole
  corpus, includes a toolchain change).

**Next:** replicate on a second model. A mechanism that only appears in
gemma-4-4b is a gemma finding. ministral-8b is the obvious choice -- it had the
lowest shifted-chunk rate in the natural experiment (11.67%), so it is the
least favourable case.

**Read the flips before closing the entry, and they are not random.** 68 blocks
lost their flag under the offset shift, 81 gained one. Restricting to blocks
where all five June models agreed, so the "right" answer is as close to settled
as this corpus gets:

*Lost* -- flagged at offset 0, not at offset 1, all five models said yes:

> "i have to say my name yes okay susie gomez 100 block of north reservoir
> street um are you filling in the position on a legal standpoint or are you
> filling in the position on a board member s..."

That is a resident stating name and address. In municipal meetings it is the
single most unambiguous marker of a public comment there is, and it was dropped
because a batch boundary moved. Nothing about the text changed.

*Gained* -- not flagged at offset 0, flagged at offset 1, all five models said
no:

> "and i will pass it over to jen thank you hopefully i didn't push the button
> all right uh thank you madam mayor and student castle i'm pleased to speak to
> you tonight about the community deve..."

> "thank you for presentation director Campbell I'm sure we'll get more to this
> in the March meeting in the first and second reading but can you just talk a
> little bit about the t..."

Those are a staff presentation and a council member questioning staff.

So the shift is not adding noise around the edges. It is **losing the
public/official distinction in both directions** -- dropping residents who
identify themselves and picking up officials addressing each other. That is the
qualitative form of the 73.6%-of-stable-positives number, and it is what belongs
in the paper next to the statistic.

Ruled out the obvious confound: lost blocks have a median 114.5 words, gained
107. Not a length effect.

**Open question:** the dose-response. Condition B changes company for about 93%
of blocks in one step. Offsets 0/1/2 at size 3 would show whether the flip rate
tracks the *fraction* of company changed, turning a two-point contrast into a
curve. Two more runs, about an hour.

---

## 2026-09-03 (late) -- Controlled chunk experiment launched. Design recorded before results.

**Commit:** 63cf08b
**Ran:**
```
python chunk_experiment.py select --n 12
.
un_chunk_experiment.ps1 -Model gemma-4-4b     # running
```
**Config:** gemma-4-4b, 12 meetings, 1,231 blocks, phase 1 only, temperature 0.
Corpus fixed across all conditions via `HODL_COMMENTS_DIR`; each condition writes
to its own output root.

**Why:** everything so far is a natural experiment. The two pyannote modes
*happen* to shift batch boundaries, and blocks in shifted chunks *happen* to flip.
That is strong evidence but it leans on an accident, and which blocks land in
shifted chunks is not random. This replaces it with a design in which nothing
varies except where the boundaries fall.

**Conditions:**

| | size | offset | what it is |
|---|---|---|---|
| A | 3 | 0 | baseline, the corpus setting |
| A2 | 3 | 0 | **the same setting again** -- the control |
| B | 3 | 1 | every boundary after the first moves, blocks untouched |
| C | 1 | 0 | no batch context at all |
| D | 5 | 0 | more context |

**Predictions, written down now so they cannot be adjusted later:**

1. **A vs A2 will be near zero, but not zero.** This is the honest floor:
   same machine, same session, same model file, no toolchain gap -- unlike the
   0.80% June-versus-September figure, which contains an unrecorded change
   underneath. Prediction: **0.1-0.5%**, i.e. below the 0.80% and closer to the
   0.22% within-session estimate from the variant pairs.
2. **A vs B will be far larger.** Prediction: **8-15%** of blocks change. Lower
   than the 13.77% shifted-chunk figure, because there every block in the bucket
   had shifted company by construction, whereas offset 1 at size 3 changes
   company for ~28 of every 30 blocks but leaves the first chunk partly intact.
3. **A vs C is the one I have no prediction for**, and that is worth admitting.
   Removing context could stabilise the judgement or destabilise it; the model
   has less to go on either way. I expect a *large* difference and I do not know
   its sign in terms of flagged count.
4. **D (size 5) will be intermediate or worse than A.** If the mechanism is
   "more neighbours means more interference", size 5 should be less stable than
   size 3 under a shift, not more.

**Decided in advance:**
- If A vs A2 comes back **zero**, the pipeline is deterministic at fixed settings
  on this machine, and the entire A-vs-B difference is attributable to batching
  with no noise subtraction needed. That would be the cleanest possible result
  and I am not counting on it.
- A large A-vs-C difference does **not** mean size 1 is more accurate. There are
  no human labels here, so there is no accuracy, only agreement. C measures how
  much of the judgement came from the neighbours; whether that was good or bad is
  Step 4's question. Writing this down now because it is exactly the inference I
  would be tempted to make when the number arrives.

**Surprised by:** nothing yet, it is running.

**Next:** `python chunk_experiment.py analyse` when it lands. Then the same
design on a second model, because a mechanism that only appears in gemma is a
gemma finding, not a pipeline finding.

**Open question:** condition B changes company for ~93% of blocks. A cleaner
dose-response would vary offset 0/1/2 at size 3 and measure whether the flip
rate tracks the *fraction* of company changed. That is three more runs and would
turn a two-point contrast into a curve.

---

## 2026-09-03 (night) -- Noise floor measured: 0.80%. The chunk effect clears it by 17x.

**Commit:** 9d70760
**Ran:**
```
.
un_repro_check.ps1 -Model gemma-4-4b          # 3h 32m, 78 meetings
python compare_corpus_runs.py --rerun downloads/repro_check/2026-09-03/gemma-4-4b/phase1_public_comments
```
**Config:** gemma-4-4b phase 1, all 81 meeting files, temperature 0, chunk size 3,
scratch output root so no corpus file was touched (`git status downloads/llm_outputs` clean)

**Result:**

| | |
|---|---|
| Meetings compared | 78 |
| Blocks | 10,069 |
| **Blocks whose classification changed** | **81 (0.80%)** |
| Meetings reproducing exactly | 38 of 78 (**48.7%**) |
| Flagged: baseline / re-run | 1,863 / 1,880 (net +17, +0.9%) |
| Corpus Jaccard | 0.9576 |
| Krippendorff alpha (run vs run) | 0.9734 |
| Gwet AC1 (run vs run) | 0.9885 |

**The comparison that matters.** gemma's shifted-chunk flip rate is 13.77%. The
noise floor is 0.80%. **The chunk-framing effect is 17x its instrument.** It is
reportable.

**There are two noise floors and they are not the same number**, which I had
been conflating:

- *Within-session non-determinism*: gemma's identical-chunk flip rate between
  `_standard` and `_exclusive`, both produced in the June run, is **0.22%**.
- *Across toolchain state*: June corpus versus tonight's re-run is **0.80%**,
  about 3.6x larger. That difference is not noise in the same sense -- it is
  whatever changed underneath between June and now (a llama-cpp-python
  reinstall, a driver update, a model file replaced in place), which nothing
  recorded.

Use 0.80%, the larger one, as the floor. It is the conservative choice and the
effect clears it anyway.

**Surprised by:** that only **48.7% of meetings reproduce exactly**. The
aggregate moved 0.9% and I expected most meetings to be untouched; in fact half
of them moved. That is the same aggregate-stable / unit-unstable pattern the
Southwell literature predicts and that doc 05 found in the variant pairs, now
showing up in a place with no experimental manipulation at all -- just the same
model run twice.

Also surprised the drift has a slight direction: 49 blocks added versus 32
dropped, z = 1.89. Not significant at 0.05 and **not being claimed**, but it is
the second time a directional hint has appeared and failed to reach
significance. Worth watching rather than reporting.

**Decided:**
- Quote 0.80% as the noise floor, and report both floors in the paper rather
  than the flattering one.
- Do **not** claim the +17 drift is directional. z = 1.89 is a hint.
- The committed June corpus can be cited as a description of that artifact,
  labelled with its toolchain state. It should not be mixed with fresh runs in
  one agreement statistic.

**Also closed tonight:** the three meetings no model has ever coded are skipped
because they contain **zero blocks** -- `SKIP (no blocks)` in the log, and all
three have `blocks: []` and `speakers: []` in the source. Not a failed run, an
empty input. That fully closes the 81 / 78 / 76 count chain: 81 files, 3 empty,
78 coded, 2 of those stale duplicates, 76 real.

**Next:** the GPU is free. The direct chunk experiment is now the highest-value
run: one meeting at `p1_chunk_size` 1, 3 and 5 plus deliberate offsets, which
replaces the natural experiment with a controlled one and can separate framing
from non-determinism by repeated measurement at the same setting.

**Answered before closing the entry** -- the noise is *not* uniform, and the
guess in the first draft of this paragraph was backwards.

Cross-tabulating the 81 changed blocks against how many of the five core models
flagged them in June:

| models flagging it | population | changed | rate |
|---|---|---|---|
| 0 | 6,806 | 15 | 0.22% |
| 1 | 952 | 19 | 2.00% |
| 2 | 592 | 9 | 1.52% |
| 3 | 591 | 11 | 1.86% |
| 4 | 343 | 19 | 5.54% |
| 5 | 785 | 8 | 1.02% |

Collapsed: blocks the models agree about (0 or 5 votes) change **0.30%** of the
time; contested blocks (1-4) change **2.34%** of the time. A **7.7x**
concentration.

So run-to-run non-determinism lands almost entirely where the judgement is hard.
Reassuring in one direction -- clear cases are 99.7% stable, so this is not
random corruption. Uncomfortable in the other: the contested blocks are exactly
the ones a reliability claim rests on, and they are the least stable thing in
the corpus.

I had assumed this would *lower* the effective floor. It raises it for the
blocks that matter. Against the contested-block floor of 2.34%, gemma's
shifted-chunk flip rate of 13.77% clears by **5.9x** rather than 17x. Both
comparisons should be reported; the 17x alone would flatter the result.

**And the question that raised -- answered in the same sitting, because it
decides whether the headline holds.** Is the chunk-framing effect also
concentrated on contested blocks? If it were, the chunk effect and the
non-determinism would plausibly be one phenomenon (ambiguity plus any
perturbation) and the finding would be much narrower.

Same-text 1:1 blocks, split both ways:

| | unanimous (0 or 5 votes) | contested (1-4 votes) |
|---|---|---|
| chunk identical | 10/8,670 = **0.12%** | 54/2,725 = **1.98%** |
| chunk shifted | 206/3,385 = **6.09%** | 465/1,370 = **33.94%** |

Read this **down the columns**, which is the comparison that controls for
ambiguity:

- On blocks **every one of the five models agrees about**, shifting the chunk
  still flips **6.09%** against a 0.12% floor -- a **51x** effect.
- On contested blocks, 1.98% to 33.94% -- **17x**, and a third of all contested
  blocks flip.

So the chunk effect is **not** ambiguity amplification. It moves blocks that
every model agrees about, at fifty times the rate those blocks move on their
own. Ambiguity makes it worse (6% to 34%) but does not create it.

This also corrects the "5.9x" I wrote three paragraphs up. That compared the
shifted-chunk rate pooled across strata against the contested-only noise floor,
which mixes two populations. The within-stratum comparisons -- **51x** and
**17x** -- are the right ones, and both are larger. The pooled 17x from earlier
in this entry happens to land in the same place by coincidence, not by being the
same calculation.

**Still open:** the 6.09% on unanimous blocks is a third of a percent of the
corpus in absolute terms, but it is the number that makes the finding
mechanistic rather than statistical. Worth reading twenty of those blocks by
hand before writing the paper -- if they turn out to be near-boundary cases the
models happen to agree on for different reasons, that is a different story than
if they are clear public comments that flipped.

---

## 2026-09-03 (later) -- CAPITALS, not asterisks: Concord silently merges sentences

**Commit:** 475cd80
**Ran:**
```
node tools/concord_marker_probe.mjs
python -m pytest tests/ -q                       # 110 passing
python AITranscribe/transcribe2/doctor.py
python -m pytest AITranscribe/transcribe2/test_pipeline.py -q
pip install --no-deps praat-parselmouth
pip install --upgrade "transformers>=5.10.1"     # 5.5.0 -> 5.16.1
```

**Result:**

1. **ISLS doc 06's open question is answered, and half its suggestion is wrong.**
   The doc proposes prominence notation for policy P5 and says "capitals for
   stress or asterisks (`*money*`); test which survives tokenization". Both
   survive `stripTags()`. Only capitals survive **unitization**.

   `splitSentences()` splits after `.!?` only when the next non-whitespace
   character is `\p{Lu}` or a digit, looking one character further past a quote
   or an opening bracket. An asterisk is none of those, so:

   | notation | survives ingest | preserves unit boundaries |
   |---|---|---|
   | CAPITALS | yes | **yes** |
   | `[square]` | yes | **yes** |
   | `"quote"` | yes | **yes** |
   | `*asterisk*` | yes | **no** |
   | `**double**`, `_under_`, `^caret^`, `{curly}`, `|pipe|` | yes | **no** |
   | `<em>angle</em>` | **no** (silently stripped) | n/a |

   "He denied it. *Money* was the issue." becomes **one** unit, not two. That
   changes N, changes every content-hashed unit id, and changes the question the
   judge is asked, while looking like it worked. For a design whose thesis is
   that unit boundaries are load-bearing, that is disqualifying.

2. **Unit ids do change when the policy changes**, demonstrated rather than
   assumed: `u_7ca821c35c74adfb` plain vs `u_10d1e18e7506105e` with CAPITALS.
   Confirms doc 03 finding 3 and the requirement that cross-condition joins go
   through time anchors. `blockmatch.py` is that join.

3. **transcribe2 runs on this machine.** Its own suite is 45 passed, 8 subtests.
   `doctor.py` is now green on all five capabilities. Two installs got it there:
   `praat-parselmouth` 0.4.7 (unblocks F0, so the Tier-2 prosody path in doc 06
   is available) and `transformers` 5.5.0 to 5.16.1 (unblocks Gemma 4 audio).

4. **The transformers upgrade was the cheap path, as status doc section 2
   predicted.** `pip install --dry-run` showed it touching exactly three
   packages -- transformers, tokenizers, safetensors -- and not torch, peft or
   trl. Ran it, then re-ran both suites: hands_on_dl 110 passed, transcribe2 45
   passed, `llama_cpp.llama_supports_gpu_offload()` still True. No second
   environment was needed and none was created.

5. `doctor.py`'s `HF_TOKEN unset` warning is a false alarm: it does not read
   `.env`. Loaded via `load_env.ps1` the token is present and well-formed.

**Surprised by:** that the asterisk failure is a *unitization* failure rather
than a stripping one. I expected the answer to be decided by `stripTags` and it
was not -- asterisks pass that test cleanly. The thing that disqualifies them is
two modules downstream, produces no error, and would have been invisible until
somebody noticed the unit count was wrong. Doc 06 guessed the right question and
the wrong hazard.

Also surprised the transformers jump landed on 5.16.1 rather than 5.10.x, and
that nothing broke. The plan's original second-environment recommendation was
insurance against a risk that had already been retired.

**Decided:**
- **Policy P5 uses CAPITALS.** Square brackets are the fallback if capitals turn
  out to interact badly with a judge prompt. Not asterisks, not underscores.
- Pin the whole table in `tests/test_concord_markers.py`, driving Concord's real
  modules rather than reimplementing its tokenizer, so the finding tracks the
  dependency instead of a snapshot of it.
- Upgrade in place rather than build a second environment. Snapshots kept either
  side: `env-snapshot-2026-09-03-pip.txt` and `-post-upgrade-pip.txt`.
- Did **not** install librosa: parselmouth covers F0 and librosa is only the
  fallback, with a much larger dependency surface.

**Next:** the gemma re-run is at 17/81. When it lands, `compare_corpus_runs.py`
gives the full noise floor. After that the GPU is free for the direct
chunk-framing experiment: one meeting at `p1_chunk_size` 1, 3 and 5, plus
deliberate offsets, which is the clean version of the effect rather than the
natural experiment.

**Open question:** the notation choice is itself a transcription decision, which
doc 06 notes is "pleasingly recursive". But there is a real empirical question
under it: does an LLM judge given `MONEY` actually read it as prosodic emphasis,
or as shouting, or ignore it? Doc 06's proposed control is right -- give the
model the *wrong* prominence annotation and see whether it produces the meaning
that annotation implies. That needs no new corpus and is a good use of the GPU
once it is free.

---

## 2026-09-03 -- Chunk framing, not diarization, drives phase-1 instability

**Commit:** 26ebd2b (work uncommitted at time of writing)
**Ran:**
```
python compare_diarization_variants.py
python compare_model_agreement.py
python audit_corpus.py
python -m pytest tests/ -q
.\run_repro_check.ps1 -Model gemma-4-4b       # still running
```
**Config:** all 7 models, phase 1 and 2, committed corpus, `p1_chunk_size = 3`,
alignment `min_iou = 0.10`

**Result:**

1. **The five "lost" artifacts were not lost.** `compare_model_agreement.py` and
   `plans/roar_plan.md` survive in the `AITranscribe/hands_on_dl` snapshot dated
   2026-07-17 -- the tree the ISLS audit was actually run against. Recovered,
   modernised, and re-run. It **reproduces the audit's figures exactly**: 3,263
   blocks flagged by >=1 model, 785 unanimous (24.1%), 1,719 majority (52.7%),
   2,478 contested (75.9%), cross-model Jaccard 0.372-0.554, qwen q6-vs-q8 0.840.
   `plans/windows_environment_upgrade_status.md` section 1 concluded these numbers
   had no artifact behind them. They do. That section is superseded.

2. **The diarization-variant pilot does not measure what the audit thought.**
   Aligning the 26 variant pairs by time: 97.3% of blocks align 1:1, and of those
   **99.4% have byte-identical text** (3,230 of 3,250). The two pyannote modes
   disagree about a handful of turn boundaries, not about what was said. So the
   flag instability the audit found cannot mostly be an upstream-processing effect.

3. **It is a chunk-framing effect.** Holding text byte-identical and splitting on
   whether the enclosing 3-block chunk was also identical:

   | model | identical chunk | shifted chunk |
   |---|---|---|
   | gemma-4-4b | 0.22% | 13.77% |
   | ministral-8b | 0.35% | 11.67% |
   | phi-4 | 0.61% | 17.14% |
   | qwen3.5-9b-q6 | 1.27% | 13.67% |
   | qwen3.5-9b-q8 | 0.35% | 14.30% |
   | deepseek-r1-7b | 0.66% | 14.30% |
   | deepseek-r1-14b | 0.26% | 2.21% *(base-rate artifact, see below)* |

   A ~25x difference on identical input text. Normalised by blocks either variant
   called a public comment, the shifted-chunk disagreement rate is **50-60%** for
   the five usable models. Phase 1 batches blocks three at a time; one inserted or
   deleted block upstream shifts every later chunk boundary, so a block gets judged
   alongside different neighbours. `P1_CHUNK_SIZE` was chosen to fit a context
   window and was never treated as a methodological decision.

4. **deepseek-r1-14b's low rate is not stability.** It flags almost nothing, so it
   has almost nothing to flip. Among blocks it or its pair flagged, its
   shifted-chunk disagreement is 21/21 = 100%.

5. **Phase 2 is far more stable than phase 1.** On byte-identical text, mean
   absolute theme-score delta is 0.002-0.005 and only 0.2-0.8% of scores cross the
   0.5 threshold. Phase 2 scores one comment at a time, so it has no chunk to shift.
   That is consistent with the mechanism in (3) rather than with general model noise.

6. **Corpus count chain resolved.** 81 files in `downloads/comments`, 3 never coded
   by any model, giving the 78 every planning document quotes. Of those 78, **2 are
   stale files in the superseded `commenter_blocks` schema** that shadow meetings
   already present as `_standard`/`_exclusive` pairs. `get_blocks()` falls back to
   `commenter_blocks` silently, so all seven models coded them -- against a
   pre-filtered 31-block input instead of the full 243-block meeting, which is
   exactly the pre-filtering that function's own comment warns against. Real
   corpus: 76 legitimately coded files over 50 distinct meetings. Distinct meetings
   overall is **53, not the 55** the audit states.

7. **Noise floor, partial.** The gemma re-run is 4/81 meetings in. On those,
   4 of 974 blocks changed classification (0.41%), corpus Jaccard 0.962. Aggregate
   counts were identical (23 vs 23, 43 vs 43) while individual blocks swapped.

**Surprised by:** that the two diarization variants are ~99.4% identical in text.
The whole pilot was framed on them being meaningfully different processing. They
are not, and that is what makes the chunk result clean: the text is held
byte-identical rather than merely similar, so there is no transcript confound at
all. The finding got stronger by the premise being wrong.

Also surprised that phase 2 barely moves. I expected the continuous scores to be
noisier than the binary judgement, not ~50x quieter.

**Decided:**
- Report the identical-chunk residual (0.2-1.3%) as its own column rather than
  folding it into the chunk effect. It is run-to-run non-determinism and belongs
  with the reproducibility finding, not with the framing finding.
- Exclude `deepseek-r1-14b` from summary ratios, and always print a base-rate
  column next to any flip rate so its degeneracy is visible rather than inferred.
- `min_iou = 0.10` for alignment, with a sensitivity sweep written to
  `threshold_sensitivity.csv` so the choice is inspectable. Not yet pre-registered.
- Compute agreement over the **full block universe**, not only flagged blocks. The
  old framing selects on the outcome and cannot be chance-corrected. Both are
  reported; `all_blocks` is the one to quote.
- Do not delete the two stale files. Pin them in `tests/test_corpus_integrity.py`
  so a third one is a test failure, and decide on quarantine deliberately.

**Next:** let the gemma re-run finish, then `compare_corpus_runs.py` for the full
noise floor. The chunk effect only stands if the noise floor is well below 12-17%;
at 0.41% on the first four meetings it looks safe, but that is four meetings.

**Open question:** is the chunk effect *directional* or just noise amplification?
If a block is more likely to be called a public comment when batched with two real
comments than with two procedural blocks, that is a context-contamination bias with
a sign, and far more serious than symmetric instability. `flip_detail.csv` has the
data to answer it and I have not looked. Second: does `p1_chunk_size = 1`
eliminate it, and what does that cost in throughput and in recall?

---

## 2026-08-28 -- Environment audit and portability refactor

**Commit:** 26ebd2b and the four commits before it
**Ran:** environment inspection; refactor of paths, config and prompts into files
**Config:** venv at `../LancasterClaude/.venv`, Python 3.12.6, torch 2.11.0+cu128,
transformers 5.5.0, llama-cpp-python 0.3.24 (`llama_supports_gpu_offload()` True),
RTX A2000 12 GB, compute capability 8.6

**Result:** recorded in full in `plans/windows_environment_upgrade_status.md`.
Headline: this is not a conda environment and `transformers` was already on 5.x, so
the second-environment recommendation was unnecessary. Hardcoded `D:\` paths
removed from every `.py` and `.ps1`. Prompts extracted with `ast` so they are
byte-identical to what produced the corpus. Provenance block added to every output.

**Surprised by:** re-running gemma-4-4b on one meeting today gives 4 public comments
where the committed corpus has 5, with the same model file, prompt and temperature.
The refactor was verified behaviour-preserving and today's code is self-consistent,
so something outside the Python changed between June and now and nothing recorded it.

**Decided:** treat toolchain provenance as required rather than optional.

**Next:** size the reproducibility gap across the whole corpus.

**Open question:** whether the June corpus can be cited at all, or has to be
regenerated in one pass first.
