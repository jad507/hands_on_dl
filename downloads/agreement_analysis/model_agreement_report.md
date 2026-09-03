# Cross-model agreement: phase 1 public-comment extraction

- Models: gemma-4-4b, ministral-8b, phi-4, qwen3.5-9b-q6, qwen3.5-9b-q8
- Meetings: 78
- Blocks in the corpus (the unit universe): 10017
- Blocks flagged by at least one model: 3224

## Vote counts among flagged blocks

- Flagged by >=1 model: 3263
- Unanimous: 785 (24.1%)
- Majority-agreed: 1719 (52.7%)
- Contested: 2478 (75.9%)

These are the numbers the ISLS audit quotes. They describe a population selected on the outcome -- only blocks somebody flagged -- so they cannot be chance-corrected and should not be read as reliability. The next section is the one to quote.

## Reliability over the full block universe

| statistic | all blocks | flagged blocks only |
|---|---|---|
| units | 10017 | 3224 |
| Krippendorff alpha (nominal) | 0.590 | 0.234 |
| Gwet AC1 | 0.827 | 0.256 |
| Fleiss kappa | 0.590 | 0.234 |

Read the two columns against each other. Over all blocks, AC1 is high because the models overwhelmingly agree that most blocks are not public comments -- which is true, and nearly free. Restricted to blocks somebody flagged, the skew is gone and the statistics fall to what agreement on the actual judgement looks like. Quote both, or the reader cannot tell which is being claimed.

## Per-model totals

| model | blocks flagged | recall vs majority | precision vs majority |
|---|---|---|---|
| gemma-4-4b | 1863 | 0.773 | 0.698 |
| ministral-8b | 1676 | 0.832 | 0.836 |
| phi-4 | 2362 | 0.924 | 0.658 |
| qwen3.5-9b-q6 | 1657 | 0.790 | 0.802 |
| qwen3.5-9b-q8 | 1648 | 0.791 | 0.808 |

The majority vote is not ground truth. It is what these particular models happen to agree on, and a model that disagrees with it may be right. No human labels exist for this corpus yet, which is the bottleneck the upgrade plan's Step 4 exists to clear.

## Pairwise agreement, cross-model

| pair | mean Jaccard | Krippendorff alpha |
|---|---|---|
| ministral-8b vs phi-4 | 0.554 | 0.617 |
| gemma-4-4b vs ministral-8b | 0.546 | 0.641 |
| gemma-4-4b vs phi-4 | 0.538 | 0.599 |
| ministral-8b vs qwen3.5-9b-q8 | 0.458 | 0.588 |
| ministral-8b vs qwen3.5-9b-q6 | 0.448 | 0.578 |
| phi-4 vs qwen3.5-9b-q8 | 0.425 | 0.521 |
| phi-4 vs qwen3.5-9b-q6 | 0.421 | 0.528 |
| gemma-4-4b vs qwen3.5-9b-q8 | 0.380 | 0.466 |
| gemma-4-4b vs qwen3.5-9b-q6 | 0.372 | 0.468 |

Cross-model Jaccard spans 0.372-0.554.

## Pairwise agreement, same model at different quantisation

| pair | mean Jaccard | Krippendorff alpha |
|---|---|---|
| qwen3.5-9b-q6 vs qwen3.5-9b-q8 | 0.840 | 0.908 |

**These rows are not agreement measurements.** They are the same model at two quantisations, so they measure how much quantisation perturbs one model's judgement. The earlier version of this script averaged them into the cross-model matrix, where the resulting 0.840 read as the strongest inter-model agreement in the corpus. It is a self-consistency ceiling instead, and a useful one: it bounds how much agreement any two genuinely different models could show.

## Top 15 meetings by contested share

| meeting | blocks | flagged | unanimous | contested | share |
|---|---|---|---|---|---|
| City Council Ethics Code Work Session - November 6, 2025 [ | 198 | 9 | 0 | 9 | 1.0 |
| Press Conference - Data Center Community Benefits Agreemen | 60 | 7 | 0 | 7 | 1.0 |
| Home Rule Transition Committee Meeting - October 29, 2025  | 53 | 5 | 0 | 5 | 1.0 |
| Planning Commission Meeting - October 15, 2025 [4rFO0GO6nw | 3 | 3 | 0 | 3 | 1.0 |
| City Council Committee Meeting - November 3, 2025 [nE5HiAt | 447 | 127 | 4 | 123 | 0.969 |
| Planning Commission Meeting - September 3, 2025 [5PuBv9zFX | 106 | 28 | 1 | 27 | 0.964 |
| City Council Budget Hearing - October 21, 2025 [pkVzY-53sJ | 451 | 90 | 4 | 86 | 0.956 |
| City Council Budget Hearing - November 18, 2025 [W6aSdOttj | 280 | 61 | 3 | 58 | 0.951 |
| City Council Meeting - November 25, 2025 [Re1Nhz9g1aM] | 196 | 36 | 2 | 34 | 0.944 |
| Planning Commission [vqNOsyBYp08] | 46 | 18 | 1 | 17 | 0.944 |
| City Council Committee Meeting - July 15, 2025 [z0C4LoiIcx | 51 | 16 | 1 | 15 | 0.938 |
| Planning Commission Meeting - September 3, 2025 [5PuBv9zFX | 103 | 31 | 2 | 29 | 0.935 |
| City Council Committee Meeting - July 1, 2025 [GduwovKQ8ek | 67 | 11 | 1 | 10 | 0.909 |
| City Council Committee Meeting - July 1, 2025 [GduwovKQ8ek | 67 | 11 | 1 | 10 | 0.909 |
| Traffic Commission Meeting - November 11, 2025 [Wof-B6HAg2 | 220 | 63 | 6 | 57 | 0.905 |

Full detail in `contested_blocks.csv`, which is the manual-review queue for the gold-coding pass.
