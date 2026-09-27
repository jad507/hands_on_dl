# Reproducibility: same model, same corpus, two runs

- Baseline: `D:\Users\jad507\PycharmProjects\hands_on_dl\downloads\llm_outputs\gemma-4-4b\phase1_public_comments`
- Re-run:   `downloads\repro_check\2026-09-03\gemma-4-4b\phase1_public_comments`

## Headline

- Meetings compared: **78**
- Meetings whose flagged set is byte-identical: **38 (48.7%)**
- Blocks in those meetings: 10069
- Flagged, baseline: 1863   re-run: 1880   net +17
- Blocks whose classification changed: **81**
- Corpus-level Jaccard between the two runs: **0.9576**
- Krippendorff alpha (run vs run): 0.9734
- Gwet AC1 (run vs run): 0.9885

## How to read this

Two runs of the same model over the same input with temperature 0 should agree exactly. Every number above that is not perfect is the pipeline's noise floor.

The comparison to make is against the effect sizes this project wants to report. `compare_diarization_variants.py` finds that shifting the 3-block chunk window flips 12-17% of classifications on byte-identical text. If the run-to-run noise floor here is far below that, the chunk-framing effect is real and clears its instrument. If it is comparable, the two cannot be told apart and the chunk finding has to be re-run with repeated measurements before it is claimed.

- Mean absolute per-meeting count delta: 0.60
- Max: 3

## Meetings that moved most

| meeting | blocks | baseline | rerun | added | dropped | Jaccard |
|---|---|---|---|---|---|---|
| City Council Committee Meeting - October 6, 2025 [bu | 243 | 50 | 52 | 4 | 2 | 0.889 |
| City Council Committee Meeting - October 6, 2025 [bu | 31 | 15 | 12 | 1 | 4 | 0.688 |
| City Council Special Meeting - November 20, 2025 [aZ | 319 | 50 | 51 | 3 | 2 | 0.906 |
| City Council Committee Meeting - October 6, 2025 [bu | 243 | 50 | 52 | 3 | 1 | 0.924 |
| City Council Committee Meeting - June 2, 2025 [gyhG_ | 151 | 32 | 35 | 3 | 0 | 0.914 |
| City Council Meeting - April 8, 2025 [JNe8AGFZlIA]_e | 205 | 45 | 46 | 2 | 1 | 0.936 |
| City Council Meeting - April 8, 2025 [JNe8AGFZlIA]_s | 208 | 49 | 48 | 1 | 2 | 0.940 |
| City Council Meeting - March 25, 2025 [Ifn8fwwBK0I]_ | 165 | 43 | 42 | 1 | 2 | 0.932 |
| City Council Meeting - May 13, 2025 [eDkBOrErMeE]_ex | 194 | 50 | 53 | 3 | 0 | 0.943 |
| Planning Commission - August 6, 2025 [m50W4pVkNb4]_e | 220 | 45 | 46 | 2 | 1 | 0.936 |
| Traffic Commission Meeting - November 11, 2025 [Wof- | 220 | 23 | 26 | 3 | 0 | 0.885 |
| City Council Budget Hearing - November 18, 2025 [W6a | 280 | 23 | 23 | 1 | 1 | 0.917 |
| City Council Budget Hearing - October 21, 2025 [pkVz | 451 | 43 | 43 | 1 | 1 | 0.955 |
| City Council Committee Meeting - June 17, 2025 [e_aX | 44 | 9 | 9 | 1 | 1 | 0.800 |
| City Council Committee Meeting - March 3, 2025 [qEcu | 109 | 21 | 21 | 1 | 1 | 0.909 |
| City Council Meeting - July 22, 2025 [Y4mI4udbAfM] | 126 | 36 | 34 | 0 | 2 | 0.944 |
| City Council Meeting - June 24, 2025 [oisLME2wIuo] | 63 | 15 | 15 | 1 | 1 | 0.875 |
| City Council Meeting - May 13, 2025 [eDkBOrErMeE]_st | 195 | 54 | 56 | 2 | 0 | 0.964 |
| City Council Meeting - October 28, 2025 [Ffwwu-vf22M | 220 | 63 | 63 | 1 | 1 | 0.969 |
| Planning Commission Meeting - September 3, 2025 [5Pu | 103 | 14 | 14 | 1 | 1 | 0.867 |

Full detail in `changed_blocks.csv`, which carries the text of every block whose classification moved.
