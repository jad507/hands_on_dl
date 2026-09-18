# Pre-registration: gold coding sample

**Written:** 2026-09-03, before any coding.

Recorded now so that none of it can be adjusted after seeing results. Doc 05
Step 3.2 asks for the theme threshold to be pre-registered because "sweeping it
post hoc is a researcher degree of freedom you are trying to make visible in
others"; the same applies to every choice below.

## Sampling

- Universe: all 10069 blocks in 78 meetings coded by all
  5 core models. Blocks, not flagged blocks: sampling only
  flagged blocks would select on the outcome being evaluated.
- Excluded: meetings any core model did not code, so vote counts are comparable.
- Strata: number of core models that flagged the block, 0 to 5.
- Seed: `20260903`. Sample order shuffled so stratum is not inferable from position.
- Quotas and realised draw:

| stratum | population | requested | drawn | sampling fraction | IPW |
|---|---|---|---|---|---|
| 0 | 6806 | 25 | 25 | 0.003673 | 272.24 |
| 1 | 952 | 36 | 36 | 0.037815 | 26.4444 |
| 2 | 592 | 36 | 36 | 0.060811 | 16.4444 |
| 3 | 591 | 36 | 36 | 0.060914 | 16.4167 |
| 4 | 343 | 25 | 25 | 0.072886 | 13.72 |
| 5 | 785 | 22 | 22 | 0.028025 | 35.6818 |

Contested strata are deliberately oversampled. Because the sampling fraction per
stratum is recorded, population estimates must be computed with the inverse
probability weights above; unweighted proportions from this sample describe the
sample only.

## Analysis decisions, fixed in advance

1. **Phase-1 agreement** between human and model is computed over the full
   sample with Krippendorff's alpha (nominal) and Gwet's AC1, reported together.
   `unsure` is treated as missing, not as `no`.
2. **Phase-2 threshold is 0.5** for converting continuous theme scores to binary
   assignments. Chosen before seeing any human score. A sensitivity sweep over
   0.3-0.7 will be reported as a robustness check, not as the headline.
3. **Primary statistic is per-theme**, not pooled across the four themes.
4. **`deepseek-r1-7b` and `deepseek-r1-14b` are excluded** from the core
   comparison, on the pre-existing grounds that both phase-1 runs failed in
   opposite directions (8,882 vs 195 blocks flagged).
5. **Blocks the coder marks as fusing two speakers** are analysed separately and
   reported as a unitization finding rather than dropped.
6. Stopping rule: all 180 items are coded before any agreement
   statistic is computed. No interim looks.

## Blinding

`gold_sample_KEY.json` is not opened until `gold_coding.csv` is complete. The
coding sheet contains no model output, no stratum labels and no vote counts.
