# Reproducibility: same model, same corpus, two runs

- Baseline: `D:\Users\jad507\PycharmProjects\hands_on_dl\downloads\llm_outputs\gemma-4-4b\phase1_public_comments`
- Re-run:   `downloads\repro_check\2026-09-03\gemma-4-4b\phase1_public_comments`

## Headline

- Meetings compared: **4**
- Meetings whose flagged set is byte-identical: **2 (50.0%)**
- Blocks in those meetings: 974
- Flagged, baseline: 102   re-run: 102   net +0
- Blocks whose classification changed: **4**
- Corpus-level Jaccard between the two runs: **0.9615**
- Krippendorff alpha (run vs run): 0.9781
- Gwet AC1 (run vs run): 0.9949

## How to read this

Two runs of the same model over the same input with temperature 0 should agree exactly. Every number above that is not perfect is the pipeline's noise floor.

The comparison to make is against the effect sizes this project wants to report. `compare_diarization_variants.py` finds that shifting the 3-block chunk window flips 12-17% of classifications on byte-identical text. If the run-to-run noise floor here is far below that, the chunk-framing effect is real and clears its instrument. If it is comparable, the two cannot be told apart and the chunk finding has to be re-run with repeated measurements before it is claimed.

- Mean absolute per-meeting count delta: 0.00
- Max: 0

## Meetings that moved most

| meeting | blocks | baseline | rerun | added | dropped | Jaccard |
|---|---|---|---|---|---|---|
| City Council Budget Hearing - November 18, 2025 [W6a | 280 | 23 | 23 | 1 | 1 | 0.917 |
| City Council Budget Hearing - October 21, 2025 [pkVz | 451 | 43 | 43 | 1 | 1 | 0.955 |

Full detail in `changed_blocks.csv`, which carries the text of every block whose classification moved.
