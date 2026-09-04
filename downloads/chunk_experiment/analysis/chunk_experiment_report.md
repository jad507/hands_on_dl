# Controlled chunk-framing experiment

- Blocks: 1231
- Conditions: A_size3_off0, A2_size3_off0_repeat, B_size3_off1, C_size1, D_size5
- Everything held constant except where the phase-1 batch boundaries fall.

## Flagged counts

| condition | blocks flagged |
|---|---|
| A_size3_off0 | 247 |
| A2_size3_off0_repeat | 258 |
| B_size3_off1 | 260 |
| C_size1 | 387 |
| D_size5 | 290 |

## Pairwise

| comparison | changed | % of blocks | Jaccard | alpha | AC1 |
|---|---|---|---|---|---|
| A_size3_off0 vs A2_size3_off0_repeat | 27 | 2.193% | 0.8985 | 0.9328 | 0.9675 |
| A_size3_off0 vs B_size3_off1 | 149 | 12.104% | 0.5457 | 0.63 | 0.8201 |
| A_size3_off0 vs C_size1 | 168 | 13.647% | 0.581 | 0.6433 | 0.779 |
| A_size3_off0 vs D_size5 | 121 | 9.829% | 0.6322 | 0.7119 | 0.8508 |
| A2_size3_off0_repeat vs B_size3_off1 | 144 | 11.698% | 0.565 | 0.6481 | 0.8248 |
| A2_size3_off0_repeat vs C_size1 | 159 | 12.916% | 0.6045 | 0.6661 | 0.7894 |
| A2_size3_off0_repeat vs D_size5 | 112 | 9.098% | 0.6606 | 0.7372 | 0.8609 |
| B_size3_off1 vs C_size1 | 153 | 12.429% | 0.6175 | 0.6794 | 0.7971 |
| B_size3_off1 vs D_size5 | 120 | 9.748% | 0.6418 | 0.7192 | 0.8507 |
| C_size1 vs D_size5 | 157 | 12.754% | 0.6235 | 0.6803 | 0.7879 |

## The comparison this was built for

- **Control** (same setting, run twice): 27 blocks changed, **2.193%**
- **Effect** (batch boundaries shifted by one): 149 blocks changed, **12.104%**
- **Ratio: 5.5x**

Both numbers come from the same machine, the same session and the same model file, so unlike the June-versus-September comparison in `compare_corpus_runs.py` there is no toolchain gap in the control.

## Reading condition C

A large A-vs-C difference does **not** show that chunk size 1 is more accurate. There are no human labels here, so there is no accuracy -- only agreement. C measures how much of the judgement was coming from the neighbouring blocks. Whether that contribution helped or hurt is upgrade-plan Step 4's question, and needs the gold sample.
