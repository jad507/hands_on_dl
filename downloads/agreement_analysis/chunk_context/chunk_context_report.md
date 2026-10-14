# Is the chunk-framing effect directional?

- `p1_chunk_size`: 3
- Models: gemma-4-4b, ministral-8b, phi-4, qwen3.5-9b-q6, qwen3.5-9b-q8

## Test 1a (circular): P(flag | k chunk-mates flagged)

| chunk-mates | of which flagged | n | P(flag) |
|---|---|---|---|
| 0 | 0 | 90 | 0.000 |
| 1 | 0 | 170 | 0.176 |
| 1 | 1 | 30 | 0.000 |
| 2 | 0 | 22258 | 0.150 |
| 2 | 1 | 8172 | 0.182 |
| 2 | 2 | 2570 | 0.711 |

This looks like a large effect and is close to meaningless. All blocks in a chunk are classified in one forward pass and emitted as one JSON object, so their labels are correlated by construction. Public comments also cluster in time, which confounds it again.

## Test 1b (also circular): within-block, endogenous neighbours

- Same block, byte-identical text, chunk company differs, flag differs: 494
- Concordant with chunk-mate flag count: 361 (73.1%)
- Discordant: 133 (26.9%)
- z against a 50/50 null: 10.26
- Flag unchanged despite different company: 1223

Holding the block and its text constant removes the clustering confound but not the single-forward-pass one. Still not usable.

## Test 2 (the usable one): exogenous neighbours

Neighbour comment-likeness measured by pyannote's `category` field, derived from diarization speaker statistics, which no language model ever saw.

- Blocks where neighbour comment-likeness and the flag both differ: 258
- Concordant: 123 (47.7%)
- Discordant: 135 (52.3%)
- z against a 50/50 null: **-0.75**

Consistent with chance. **The directional reading is not supported.**

## What this licenses

- Supported: the batching window *destabilises* unit-level coding. A noise claim, with the input text held byte-identical.
- Not supported: the batching window *biases* coding toward finding comments.

The negative result is weak evidence, not strong. `category` is a coarse proxy and `llm_classify_human_themes.py`'s own comment calls the recurring/commenter_candidate split unreliable for this task. At n = 258 with a noisy proxy this test would miss a small effect. The clean version needs human labels on the neighbours (upgrade plan Step 4), or a direct experiment: re-run one meeting at `p1_chunk_size = 1` and at several deliberate chunk offsets.
