# Results

One row per experiment. Add a row the moment a number exists; never let a number
live only in terminal scrollback. Prose, reasoning and things that went wrong
belong in `NOTEBOOK.md` — this file is for finding a number fast.

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
| 2026-09-03 | 26ebd2b | Quantisation stability (NOT agreement) | qwen3.5-9b q6 vs q8 | 78 meetings | Jaccard **0.840**, alpha 0.908 — same model, two quantisations |
| 2026-09-03 | 26ebd2b | Run-to-run noise floor, partial | gemma-4-4b, phase 1, re-run vs committed corpus | 4 of 81 meetings, 974 blocks | **0.41%** of blocks changed; Jaccard 0.962 — *incomplete, see NOTEBOOK* |
| 2026-09-03 | 26ebd2b | Corpus integrity | `audit_corpus.py` | 81 files | 3 uncoded, **2 stale pre-filtered duplicates**, 53 distinct meetings |
| 2026-08-28 | 26ebd2b | Reproducibility spot check | gemma-4-4b, 1 meeting, same model file and prompt | 1 meeting | committed corpus 5 comments, re-run **4** |

## Notes on reading these

**The two agreement rows are not alternatives.** Over all 10,017 blocks the models
agree that most things are not public comments, which is true and nearly free, so
AC1 is 0.827. Restricted to blocks somebody flagged, the skew is gone and AC1 falls
to 0.256. Quoting either alone misleads; quote both.

**The 0.840 row is not an agreement measurement.** It is one model at two
quantisations. It belongs in the table as a self-consistency ceiling — it bounds
how much agreement two genuinely different models could plausibly show — not as the
strongest inter-model result.

**The noise-floor row is incomplete** and must not be cited until the full re-run
lands. It exists here so that a partial number cannot be mistaken for a final one.

**The chunk-framing rows are the ones with a paper in them.** They hold the input
text byte-identical, so there is no transcript confound: the only thing that varies
is which two neighbours the model saw the block alongside.
