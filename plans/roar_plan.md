<!--
RECOVERED 2026-09-03.

plans/windows_environment_upgrade_status.md section 1 listed this file as lost
and concluded the ISLS audit's figures had no artifact behind them. It was not
lost: it survived in the AITranscribe/hands_on_dl snapshot dated 2026-07-17,
which is the tree the audit was actually run against. Restored verbatim.

Read it alongside upgrade-plan Step 6, which argues this is no longer the right
next step and says why: a bigger model is not ground truth, it is an eighth
opinion, and the ISLS contribution needs one judge held constant while the
transcript varies rather than more judges. Its prerequisites are also unmet --
human labels do not exist yet (Step 4) and there is no Roar allocation.

The portability blocker it depended on IS now cleared: paths.py removed every
absolute D:\ literal, so nothing here is blocked on that any more.
-->

# Plan: Running a Larger Model on ROAR Collab

## What hardware is actually there (per ICDS docs, July 2026)

| Node type | Count | VRAM | Notes |
|---|---|---|---|
| 2x A100 | 38 | 2 x 40 GB | 48 cores, 384 GB RAM, Infiniband. The workhorse. |
| A40 | 12 | 48 GB | Single GPU, 1 TB RAM. Best single-GPU VRAM on the cluster. |
| 4x V100 | 2 | 4 x 32 GB | Older, scarce. |
| P100 | 60 | 12 GB | Too small for this. |

Allocation note: "open" accounts get free credits; a full A100 requires
requesting 24 standard cores, half A100 (MIG) requires 12. Check current
rates/credits at https://icds.psu.edu/services/roar/details-rates/

## Model choices by VRAM budget

- **Single A100 40 GB:** Qwen3-32B or Gemma-3-27B at AWQ/Q4 — a large step
  up from the 4–14B local models, fits with room for KV cache.
- **A40 48 GB:** same class, more KV-cache headroom for long meetings.
- **2x A100 (80 GB total):** 70B class — Llama-3.3-70B or Qwen2.5-72B at
  4-bit (~40–43 GB weights) with tensor parallelism across both GPUs.

Recommendation: start with a 32B on a single A100 (cheapest queue, simplest
job), and only go to 70B on 2x A100 if the 32B's agreement with the model
consensus doesn't clearly beat ministral-8b/qwen-9b.

## Software approach

Switch from llama-cpp to **vLLM** for cluster runs:

- Much higher throughput via continuous batching — your local 16 h run for
  ~74 meetings should compress to roughly 1–2 h.
- Keeps your grammar-constrained JSON: vLLM's guided decoding
  (`guided_json` / xgrammar backend) replaces the GBNF grammar.
- Install in a conda env on Roar or use a container (Roar supports
  Apptainer; `docs.icds.psu.edu/software/containers/`).

Code changes to `llm_extract_comments.py` / classify scripts are small:
replace the `Llama()` call with vLLM's `LLM()` + `SamplingParams`, batch
all chunks for a meeting in one `generate()` call. The resumable
skip-processed-files design carries over unchanged.

## Data transfer

Only `downloads/comments/` (the block JSONs) needs to go up — the audio and
transcripts stay home. It's small; `rsync`/Globus to scratch. Model weights:
download once to group storage, not scratch (scratch is purged).

## Example SLURM script

```bash
#!/bin/bash
#SBATCH --job-name=llm_extract
#SBATCH --account=<your_allocation>
#SBATCH --partition=sla-prio          # or open queue
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=24            # 24 cores = full A100
#SBATCH --gres=gpu:a100:1
#SBATCH --mem=180GB
#SBATCH --time=08:00:00
#SBATCH --output=logs/llm_extract_%j.log

module load anaconda
conda activate vllm_env

python llm_extract_comments.py \
    --model Qwen/Qwen3-32B-AWQ \
    --comments-dir $SCRATCH/comments \
    --out-dir $SCRATCH/llm_outputs/qwen3-32b
```

For 70B: `--gres=gpu:a100:2`, `--cpus-per-task=48`, add
`--tensor-parallel-size 2`.

## Order of operations

1. Confirm/request Roar Collab account + allocation (free credits first).
2. Interactive GPU session (`salloc ... --gres=gpu:a100:1`), build the
   vllm conda env, smoke-test on 1 meeting.
3. Port the two scripts to vLLM with guided JSON.
4. Batch job over all 78 meetings.
5. Drop the outputs into `downloads/llm_outputs/<model>/` and rerun
   `compare_model_agreement.py` — the big model becomes the reference
   point for scoring the small ones.
