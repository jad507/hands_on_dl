# Results

One row per experiment. Add a row the moment a number exists; never let a number
live only in terminal scrollback. Prose, reasoning and things that went wrong
belong in `NOTEBOOK.md` -- this file is for finding a number fast.

Every row must carry the commit and enough config to re-run it.

| Date | Commit | Experiment | Config | N | Headline number |
|---|---|---|---|---|---|
| 2026-09-03 | 26ebd2b | Chunk-framing effect on phase 1 | 5 usable models, byte-identical text held constant, `p1_chunk_size=3` | 3,230 aligned blocks over 26 variant pairs | identical chunk **0.22-1.27%** flip; shifted chunk **11.67-17.14%** flip; ~25x |
| 2026-09-03 | 26ebd2b | Same, normalised by base rate | as above, denominator = blocks flagged in either variant | 26 variant pairs | shifted-chunk disagreement **50-60%** among positives |
| 2026-09-03 | 26ebd2b | Diarization variants: how different are they really? | `_standard` vs `_exclusive`, `min_iou=0.10` | 3,339 blocks / 26 pairs | **97.3%** align 1:1; of those **99.4% byte-identical text** |
| 2026-09-03 | 26ebd2b | Phase-2 theme-score stability on identical text | 7 models, 4 themes | 22,892 scored pairs | mean abs delta **0.002-0.005**; **0.2-0.8%** cross the 0.5 threshold |
| 2026-09-03 | 26ebd2b | Phase-1 cross-model agreement, full block universe | core 5, DeepSeeks excluded | 78 meetings / 10,017 blocks | Krippendorff alpha **0.590**, Gwet AC1 **0.827**, Fleiss kappa 0.590 |
| 2026-09-03 | 26ebd2b | Phase-1 agreement, flagged blocks only | core 5 | 3,224 blocks | Krippendorff alpha **0.234**, Gwet AC1 **0.256** |
| 2026-09-03 | 26ebd2b | Phase-1 vote counts (reproduces 2026-08-14 audit exactly) | core 5 | 3,263 flagged blocks | unanimous **24.1%**, majority **52.7%**, contested **75.9%** |
| 2026-09-03 | 26ebd2b | Cross-model pairwise Jaccard | core 5, macro-averaged over meetings | 78 meetings | **0.372-0.554** |
| 2026-09-03 | 26ebd2b | Quantisation stability (NOT agreement) | qwen3.5-9b q6 vs q8 | 78 meetings | Jaccard **0.840**, alpha 0.908 -- same model, two quantisations |
| 2026-09-03 | 9d70760 | **Run-to-run noise floor, complete** | gemma-4-4b phase 1, Sept re-run vs June corpus, 3h32m | 78 meetings / 10,069 blocks | **0.80%** of blocks changed; only **48.7%** of meetings reproduce exactly; Jaccard 0.9576, alpha 0.9734, AC1 0.9885 |
| 2026-09-03 | 9d70760 | Effect vs instrument | gemma shifted-chunk flip 13.77% against a 0.80% floor | - | **17x** -- the chunk-framing effect clears its noise floor |
| 2026-09-03 | 9d70760 | Within-session non-determinism | gemma identical-chunk flips, both variants from the June run | 2,279 blocks | **0.22%** -- the stricter floor; 0.80% above additionally contains an unrecorded toolchain change |
| 2026-09-03 | 9d70760 | Where the noise lives | changed blocks vs June vote count | 10,069 blocks | contested (1-4 votes) **2.34%** vs unanimous (0 or 5) **0.30%** -- a **7.7x** concentration |
| 2026-09-03 | 9d70760 | **Chunk effect within consensus stratum** | same-text 1:1 blocks, 5 core models | 16,150 block-observations | unanimous 0.12% -> **6.09%** (**51x**); contested 1.98% -> **33.94%** (**17x**) -- the effect is not ambiguity amplification |
| 2026-09-04 | 232baa1 | **CONTROLLED chunk experiment** | gemma-4-4b, 12 meetings, corpus fixed, only batching varies | 1,231 blocks | control A-vs-A2 **2.19%**; effect A-vs-B **12.10%**; **ratio 5.5x** |
| 2026-09-04 | 232baa1 | Controlled, by stratum | same | 1,231 blocks | unanimous 1.01% -> 6.08% (**6.0x**); contested 6.97% -> 36.48% (**5.2x**) |
| 2026-09-04 | 326b94b | **Controlled, ministral-8b replication** | same 12 meetings, same corpus, A/A2/B | 1,231 blocks | floor **0.41%**, effect **7.47%**, **ratio 18.4x** |
| 2026-09-04 | 326b94b | Ministral by stratum | same | 1,231 blocks | unanimous 0.10% -> 2.53% (**25.0x**); contested 1.64% -> 27.46% (**16.8x**) |
| 2026-09-04 | 326b94b | **Cross-model invariant** | gemma + ministral, contested blocks | 244 blocks each | both flip **27-36%** under a pure batching shift |
| 2026-09-04 | 326b94b | Stable positives lost | flagged in both A and A2, surviving B | 239 / 237 | gemma **26.4%** lost, ministral **18.1%** lost |
| 2026-09-04 | 326b94b | Noise floor is model-dependent | A vs A2, same corpus and settings | 1,231 blocks | gemma **2.19%** vs ministral **0.41%** -- a 5x spread |
| 2026-09-04 | 326b94b | Noise does NOT predict context sensitivity | natural experiment, 6 models | n=6 | Pearson **r = +0.13** -- no cheap screening proxy exists |
| 2026-09-04 | 232baa1 | **Effect replicates across designs** | natural vs controlled, unanimous blocks | - | **6.09%** vs **6.08%** -- the magnitude is reproduced; the *floor* was what differed |
| 2026-09-04 | 232baa1 | Stable positives lost to a batching shift | flagged in BOTH A and A2 | 239 blocks | only **73.6%** survive the offset shift |
| 2026-09-04 | 12ef17e | Batch context, size 1 vs size 3 (**gemma only**) | size 1 vs size 3 | 1,231 blocks | gemma flags **387** vs **247** (+57%). *Not general -- see next row.* |
| 2026-09-04 | 12ef17e | **Same test on ministral: count is flat** | size 1 vs size 3 | 1,231 blocks | ministral flags **237** vs **240** (0.99x) -- "context suppresses flagging" is a gemma finding |
| 2026-09-04 | 12ef17e | **What survives on both: membership churn** | size-3 flags retained at size 1 | 1,231 blocks | gemma keeps **94.3%**, ministral keeps **80.0%** -- ministral churns 20% while its total moves 3 blocks |
| 2026-09-04 | 232baa1 | Which context vs how much | A-vs-B (offset) 12.10% vs A-vs-D (size 3->5) 9.83% | 1,231 blocks | changing *which* neighbours perturbs more than changing *how many* |
| 2026-09-03 | d40ddea | Concord unit-count drift by scheme | 81 meetings exported as VTT, `maxMergeGapSeconds=-1` | 10,069 blocks | turn scheme N=**10,069**; sentence scheme N=**20,468** (**2.03x**); per-meeting ratio 1.00-**225** |
| 2026-09-03 | d40ddea | Concord round-trip fidelity | `export_vtt.py --verify` | 81 meetings / 10,069 cues | **81/81** preserve turn count exactly; 0 parse issues; 0 cues without a speaker |
| 2026-09-03 | d40ddea | Turns silently lost at Concord's default | same export, `maxMergeGapSeconds=30` | 81 meetings | **11 turns fused** (10,069 -> 10,058) |
| 2026-09-03 | d40ddea | Emphasis notation survival in Concord | `tools/concord_marker_probe.mjs` | 10 notations | CAPITALS / `[sq]` / `"q"` safe; `*ast*` `_und_` `^car^` `{cur}` `\|pip\|` **move unit boundaries**; `<angle>` silently stripped |
| 2026-09-03 | 26ebd2b | Chunk effect directionality (exogenous control) | pyannote `category` as neighbour measure | n=258 | **47.7% concordant, z=-0.75** -- no directional effect detected |
| 2026-09-03 | 26ebd2b | Corpus integrity | `audit_corpus.py` | 81 files | 3 uncoded, **2 stale pre-filtered duplicates**, 53 distinct meetings |
| 2026-08-28 | 26ebd2b | Reproducibility spot check | gemma-4-4b, 1 meeting, same model file and prompt | 1 meeting | committed corpus 5 comments, re-run **4** |

## Notes on reading these

**The two agreement rows are not alternatives.** Over all 10,017 blocks the models
agree that most things are not public comments, which is true and nearly free, so
AC1 is 0.827. Restricted to blocks somebody flagged, the skew is gone and AC1 falls
to 0.256. Quoting either alone misleads; quote both.

**The 0.840 row is not an agreement measurement.** It is one model at two
quantisations. It belongs in the table as a self-consistency ceiling -- it bounds
how much agreement two genuinely different models could plausibly show -- not as the
strongest inter-model result.

**There are two noise floors and they answer different questions.** 0.22% is
within-session non-determinism, measured between two variants produced in the
same June run. 0.80% is June versus September, which additionally contains an
unrecorded change in the toolchain. Use 0.80% as the floor: it is the
conservative choice and the chunk-framing effect clears it by 17x anyway.

**The chunk-framing rows are the ones with a paper in them.** They hold the input
text byte-identical, so there is no transcript confound: the only thing that varies
is which two neighbours the model saw the block alongside.

**Directions have replicated across models; magnitudes have not, once.** Every
effect here points the same way in both models tested, and every magnitude
differs substantially -- the ratio 3x, the floor 5x, and the size-1 count
behaviour qualitatively (gemma +57%, ministral flat). Treat any single-model
magnitude in this table as provisional until a second model confirms it, and
prefer membership-level statements to count-level ones: ministral's size-1 count
moves by three blocks while 20% of its flags change identity.

**Quote per-model ratios, never a pooled one.** The controlled design gives
5.5x for gemma-4-4b and 18.4x for ministral-8b: a 3x spread driven almost
entirely by the floor, which is itself 5x apart between the two models. Lead
instead with the two cross-model invariants -- contested blocks flip 27-36%
under a pure batching shift in both, and both lose 18-26% of their own most
stable positives.

**Do not use the natural experiment's per-model floors for anything.** They
understate the level and are not even rank preserving: the natural design makes
gemma look quieter than ministral (0.22% vs 0.35%) while the controlled design
makes it five times noisier (2.19% vs 0.41%). The
natural experiment's "identical chunk" bucket is a selected sample: a block only
lands there if its text and its whole enclosing chunk matched across variants,
which happens preferentially in stable stretches. Conditioning on stability and
then measuring instability understates the floor by about 5x. The controlled
A-vs-A2 has no such selection.

The *effect* is unaffected by this and replicated almost exactly across the two
designs (6.09% vs 6.08% on unanimous blocks). It was only ever the floor that
was mis-estimated. The 17-51x rows above are retained for the record and should
not be quoted.
