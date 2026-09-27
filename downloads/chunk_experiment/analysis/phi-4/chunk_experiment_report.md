# Controlled chunk-framing experiment

- Blocks: 1231
- Conditions: A_size3_off0, A2_size3_off0_repeat, B_size3_off1, C_size1, D_size5
- Everything held constant except where the phase-1 batch boundaries fall.

## Flagged counts

| condition | blocks flagged |
|---|---|
| A_size3_off0 | 309 |
| A2_size3_off0_repeat | 297 |
| B_size3_off1 | 303 |
| C_size1 | 374 |
| D_size5 | 287 |

## Pairwise

| comparison | changed | % of blocks | Jaccard | alpha | AC1 |
|---|---|---|---|---|---|
| A_size3_off0 vs A2_size3_off0_repeat | 18 | 1.462% | 0.9423 | 0.9606 | 0.9767 |
| A_size3_off0 vs B_size3_off1 | 138 | 11.21% | 0.632 | 0.7 | 0.821 |
| A_size3_off0 vs C_size1 | 177 | 14.379% | 0.5884 | 0.6415 | 0.76 |
| A_size3_off0 vs D_size5 | 110 | 8.936% | 0.6884 | 0.7566 | 0.8588 |
| A2_size3_off0_repeat vs B_size3_off1 | 126 | 10.236% | 0.6529 | 0.7224 | 0.8379 |
| A2_size3_off0_repeat vs C_size1 | 169 | 13.729% | 0.5976 | 0.6539 | 0.7725 |
| A2_size3_off0_repeat vs D_size5 | 106 | 8.611% | 0.6928 | 0.7621 | 0.8651 |
| B_size3_off1 vs C_size1 | 159 | 12.916% | 0.6196 | 0.6762 | 0.7852 |
| B_size3_off1 vs D_size5 | 124 | 10.073% | 0.6527 | 0.7237 | 0.8415 |
| C_size1 vs D_size5 | 193 | 15.678% | 0.548 | 0.601 | 0.7418 |

## The comparison this was built for

- **Control** (same setting, run twice): 18 blocks changed, **1.462%**
- **Effect** (batch boundaries shifted by one): 138 blocks changed, **11.21%**
- **Ratio: 7.7x**

Both numbers come from the same machine, the same session and the same model file, so unlike the June-versus-September comparison in `compare_corpus_runs.py` there is no toolchain gap in the control.

## Reading condition C

A large A-vs-C difference does **not** show that chunk size 1 is more accurate. There are no human labels here, so there is no accuracy -- only agreement. C measures how much of the judgement was coming from the neighbouring blocks. Whether that contribution helped or hurt is upgrade-plan Step 4's question, and needs the gold sample.
