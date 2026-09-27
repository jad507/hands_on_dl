# Controlled chunk-framing experiment

- Blocks: 1231
- Conditions: A_size3_off0, A2_size3_off0_repeat, B_size3_off1
- Everything held constant except where the phase-1 batch boundaries fall.

## Flagged counts

| condition | blocks flagged |
|---|---|
| A_size3_off0 | 240 |
| A2_size3_off0_repeat | 239 |
| B_size3_off1 | 242 |

## Pairwise

| comparison | changed | % of blocks | Jaccard | alpha | AC1 |
|---|---|---|---|---|---|
| A_size3_off0 vs A2_size3_off0_repeat | 5 | 0.406% | 0.9793 | 0.987 | 0.9941 |
| A_size3_off0 vs B_size3_off1 | 92 | 7.474% | 0.6794 | 0.7628 | 0.8909 |
| A2_size3_off0_repeat vs B_size3_off1 | 93 | 7.555% | 0.676 | 0.7598 | 0.8898 |

## The comparison this was built for

- **Control** (same setting, run twice): 5 blocks changed, **0.406%**
- **Effect** (batch boundaries shifted by one): 92 blocks changed, **7.474%**
- **Ratio: 18.4x**

Both numbers come from the same machine, the same session and the same model file, so unlike the June-versus-September comparison in `compare_corpus_runs.py` there is no toolchain gap in the control.

## Reading condition C

A large A-vs-C difference does **not** show that chunk size 1 is more accurate. There are no human labels here, so there is no accuracy -- only agreement. C measures how much of the judgement was coming from the neighbouring blocks. Whether that contribution helped or hurt is upgrade-plan Step 4's question, and needs the gold sample.
