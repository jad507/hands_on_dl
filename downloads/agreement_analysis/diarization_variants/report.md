# Diarization variants: alignment and the chunk-framing effect

- Variant pairs analysed: **26**
- Models: deepseek-r1-14b, deepseek-r1-7b, gemma-4-4b, ministral-8b, phi-4, qwen3.5-9b-q6, qwen3.5-9b-q8
- Alignment threshold `min_iou`: 0.1
- `p1_chunk_size`: **3**

## 1. The two variants barely differ in text

- Blocks (standard side): 3339, (exclusive side): 3319
- Aligned 1:1 by time: 3250 (97.3%)
  - byte-identical text: 3230 (99.4% of aligned)
  - text differs: 20 (0.6% of aligned)
- No 1:1 partner (split / merge / tangle / unmatched): 89

The two diarization modes disagree about a small number of turn boundaries, not about what was said. Any classification instability between them therefore cannot mostly be a transcript effect.

## 2. Where the instability actually comes from

Every row below is a block that aligned 1:1 across the two variants. The first two buckets hold blocks whose text is **byte-identical** in both; they differ only in whether the 3-block chunk the model judged them inside was also identical.

| model | chunk identical: flips/n | rate | chunk shifted: flips/n | rate | ratio | flagged either (ident/shift) |
|---|---|---|---|---|---|---|
| deepseek-r1-14b | 6/2279 | 0.26% | 21/951 | 2.21% | 9x | 69 / 21 |
| deepseek-r1-7b | 15/2279 | 0.66% | 136/951 | 14.30% | 22x | 2047 / 920 |
| gemma-4-4b | 5/2279 | 0.22% | 131/951 | 13.77% | 63x | 481 / 255 |
| ministral-8b | 8/2279 | 0.35% | 111/951 | 11.67% | 33x | 453 / 220 |
| phi-4 | 14/2279 | 0.61% | 163/951 | 17.14% | 28x | 600 / 320 |
| qwen3.5-9b-q6 | 29/2279 | 1.27% | 130/951 | 13.67% | 11x | 428 / 234 |
| qwen3.5-9b-q8 | 8/2279 | 0.35% | 136/951 | 14.30% | 41x | 423 / 226 |

The last column is why `deepseek-r1-14b` must be read separately from the rest. Its low shifted-chunk rate is not stability: it flags almost nothing, so it has almost nothing to flip. Normalising by the blocks either variant called a public comment removes the base-rate artefact:

| model | chunk identical | chunk shifted |
|---|---|---|
| deepseek-r1-14b | 8.70% | 100.00% |
| deepseek-r1-7b | 0.73% | 14.78% |
| gemma-4-4b | 1.04% | 51.37% |
| ministral-8b | 1.77% | 50.45% |
| phi-4 | 2.33% | 50.94% |
| qwen3.5-9b-q6 | 6.78% | 55.56% |
| qwen3.5-9b-q8 | 1.89% | 60.18% |

(Disagreements as a share of blocks flagged in at least one variant.)

Excluding `deepseek-r1-14b`, the identical-chunk flip rate spans 0.22%-1.27% and the shifted-chunk rate 11.67%-17.14%: a 25x difference on byte-identical input text.

`P1_CHUNK_SIZE` was set to fit a context window. On this evidence it also decides the classification of roughly one block in seven whenever an upstream change shifts the batching offset.

The identical-chunk column is not zero. Identical chunk, identical prompt and temperature 0 should be reproducible, so that residual is run-to-run non-determinism -- the same effect recorded in `plans/windows_environment_upgrade_status.md` section 3. It is reported separately here rather than folded into the chunk effect.

## 3. Phase 2 theme scores on identical text

| model | scored pairs | mean abs delta | median | share moving | share crossing 0.5 |
|---|---|---|---|---|---|
| deepseek-r1-14b | 252 | 0.005 | 0.000 | 1.2% | 0.8% |
| deepseek-r1-7b | 11264 | 0.002 | 0.000 | 0.5% | 0.4% |
| gemma-4-4b | 2400 | 0.002 | 0.000 | 2.2% | 0.2% |
| ministral-8b | 2216 | 0.003 | 0.000 | 2.2% | 0.3% |
| phi-4 | 2972 | 0.003 | 0.000 | 1.5% | 0.3% |
| qwen3.5-9b-q6 | 1768 | 0.003 | 0.000 | 1.0% | 0.3% |
| qwen3.5-9b-q8 | 2020 | 0.002 | 0.000 | 0.7% | 0.3% |

These are the same words scored twice. 'Share crossing 0.5' is the fraction that would change a binary theme assignment at the conventional threshold -- the number to quote when arguing that the threshold is a decision rather than a default.

## 4. Meetings where the variants align worst

| meeting | blocks (std/exc) | 1:1 | split | merge | tangle | rate |
|---|---|---|---|---|---|---|
| Home Rule Transition Committee Meeting - July 29, 2025 [c0 | 35/35 | 30 | 0 | 1 | 1 | 0.857 |
| City Council Meeting - April 29, 2025 [5N3AIQLoNPU] | 96/92 | 87 | 0 | 3 | 0 | 0.906 |
| City Council Committee Meeting - June 17, 2025 [e_aXcEkzyE | 46/44 | 43 | 0 | 1 | 0 | 0.935 |
| City Council Committee Meeting - July 15, 2025 [z0C4LoiIcx | 51/53 | 48 | 1 | 0 | 1 | 0.941 |
| Planning Commission Meeting - September 3, 2025 [5PuBv9zFX | 106/103 | 101 | 0 | 2 | 0 | 0.953 |
| City Council Committee Meeting - September 16, 2025 [XzF6- | 65/67 | 62 | 1 | 0 | 1 | 0.954 |
| Planning Commission - August 6, 2025 [m50W4pVkNb4] | 221/220 | 211 | 1 | 2 | 2 | 0.955 |
| City Council Committee Meeting - September 2, 2025 [bNf9xj | 94/94 | 90 | 0 | 0 | 2 | 0.957 |
| City Council Committee Meeting - April 1, 2025 [kplLo-BL1w | 247/242 | 237 | 0 | 3 | 1 | 0.960 |
| City Council Meeting - April 8, 2025 [JNe8AGFZlIA] | 208/205 | 201 | 1 | 2 | 0 | 0.966 |

See `threshold_sensitivity.csv` for how these shapes move with `min_iou`. The threshold is a researcher degree of freedom and should be pre-registered before any of these numbers are quoted.
