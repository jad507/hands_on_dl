# Windows upgrade plan: execution status and findings

**Written:** 2026-08-28, on the Windows workstation.
**Companion to:** `plans/windows_environment_upgrade.md`, which was written on a different
machine and could not observe this one. That document is left unedited as the plan as
received; this one records what was actually true here and what was done.

Three of its assumptions turned out to be wrong, and one of those changes what can be
claimed in a paper. Those come first.

---

## 1. SUPERSEDED 2026-09-03 -- the artifacts were found, and the numbers reproduce exactly

**Read this box before the section below it.** The section is left unedited as
the record of what was believed on 2026-08-28, because the reasoning that
produced a wrong conclusion is worth keeping. But its conclusion is wrong.

The search it describes was thorough and correct *for this machine*. What it
could not check was the one place the files actually were: `AITranscribe`, which
was not on this machine on 2026-08-28 and had no remote to clone from. It is
here now, and `AITranscribe/hands_on_dl/` is a snapshot of this repository dated
2026-07-17 -- the tree the ISLS audit was run against.

| File the audit cites | Verdict 2026-08-28 | Verdict 2026-09-03 |
|---|---|---|
| `compare_model_agreement.py` | gone | **found** in the snapshot; recovered |
| `plans/roar_plan.md` | gone | **found** in the snapshot; recovered |
| `core5_model_agreement_report.md` | gone | regenerated (it was derived output) |
| `downloads/agreement_analysis/contested_blocks.csv` | gone | regenerated |
| `downloads/agreement_analysis/core5_contested_blocks.csv` | gone | regenerated |

Re-running the recovered script against the committed corpus reproduces every
figure the audit quotes, to the digit: 3,263 blocks flagged by at least one
model, 785 unanimous (24.1%), 1,719 majority-agreed (52.7%), 2,478 contested
(75.9%), cross-family pairwise Jaccard 0.372-0.554, and 0.840 for
`qwen3.5-9b-q6` vs `qwen3.5-9b-q8`.

So the numbers were never unsupported, and the "order of operations step 1 is
dead" conclusion below does not follow. The advice this section gives about the
0.840 figure -- that it is a same-model-two-quantisations self-consistency
measurement and should not be framed as inter-model agreement -- was right, and
is now enforced in the code: `compare_model_agreement.py` reports cross-model
and within-family pairs in separate tables.

One thing the recovery does not change: section 3's finding stands, and the
regenerated numbers above come from the **June 2026 corpus**, not from a fresh
run. See section 3 and `NOTEBOOK.md` for what that licenses.

The general lesson is worth stating because it will recur: "absent from this
machine" and "does not exist" are different claims, and this document collapsed
them at ~95% confidence. The estimate was reasonable and wrong.

---

## 1a. (2026-08-28, as written) The orphaned analysis artifacts do not exist. The agreement numbers must be recomputed.

The plan's section 1 gave roughly 90 percent odds that five files were sitting uncommitted on
this machine, and ~5 percent that they were gone. It is the 5 percent case.

Checked 2026-08-28 against a clean tree at `742f6f6`, which equals `origin/main`, with no
stashes:

| File the AITranscribe audit cites | On this machine | In git history |
|---|---|---|
| `compare_model_agreement.py` | no | no |
| `core5_model_agreement_report.md` | no | no |
| `plans/roar_plan.md` | no | no |
| `downloads/agreement_analysis/contested_blocks.csv` | no | no |
| `downloads/agreement_analysis/core5_contested_blocks.csv` | no | no |

There is no `downloads/agreement_analysis/` directory at all. A filename search across the
repository for `*agreement*`, `*contested*`, `*roar*` and `*compare_model*` returns only one
meeting whose title happens to contain the word "Agreement".

**What follows, and it is the consequential part.** The audit in
`AITranscribe/docs/isls2027/05-hands-on-dl-upgrade-plan.md` reports specific figures out of
those files: 3,263 blocks flagged by at least one model, 785 unanimous (24.1 percent), 1,719
majority-agreed (52.7 percent), 2,478 contested (75.9 percent), cross-family pairwise Jaccard
0.372 to 0.554, and 0.840 for `qwen3.5-9b-q6` vs `qwen3.5-9b-q8`. **Those numbers currently
have no file behind them on any machine.** They cannot be cited until they are recomputed, and
`compare_model_agreement.py` has to be written from scratch to recompute them.

The one remaining possibility worth ruling out before accepting that: a third copy. An
uploaded snapshot to a chat session, a checkout on another drive, an external disk. If none
exists, the plan's order-of-operations step 1 is dead and step 6 becomes the top of the list.

Note also that the 0.840 figure is a same-model-two-quantizations comparison, so it measures
self-consistency, not inter-model agreement. Worth not repeating that framing when the number
is regenerated.

---

## 2. This is not a conda environment, and `transformers` is already on 5.x

The plan assumed a Python 3.10 conda environment on `transformers` 4.x, and built its section 4
recommendation (a whole second environment) on the risk of a 4.x to 5.x major-version jump
underneath `peft` and `trl`.

Observed here:

| | Plan assumed | Actually |
|---|---|---|
| Environment | conda env at `.\.venv` | plain venv at `..\LancasterClaude\.venv` |
| Python | 3.10 | 3.12.6 |
| transformers | 4.x | **5.5.0** |
| peft / trl | at risk from a 5.x bump | 0.18.1 / 1.0.0, already running against 5.x |
| torch | unknown | 2.11.0+cu128, `sm_86` present in `get_arch_list()` |
| llama-cpp-python | unknown | 0.3.24, `llama_supports_gpu_offload()` -> **True** |
| GPU | RTX A2000 12 GB, Ampere sm_86 inferred at ~92 percent | confirmed, compute capability 8.6 |

**The major-version boundary has already been crossed and nothing broke.** `transcribe2`
wants `transformers >= 5.10.1`; going 5.5.0 to 5.10.x is a minor bump within the same major
line, not the hazard the plan was insuring against. The second environment was not created,
for a simpler reason as well: `AITranscribe` is not on this machine and has no remote that
could be cloned from here, so there is currently nothing to put in a second environment.

**Recommendation when AITranscribe does arrive here:** snapshot, then upgrade in place, then
execute `llms.ipynb` end to end as the test. The plan's section 4.1 already describes exactly
this and it is now the cheaper path. Create the second environment only if that notebook
actually breaks.

Environment snapshot saved as `env-snapshot-2026-08-28-pip.txt` (219 packages). It is
gitignored via a new `env-snapshot-*` rule. `conda list --explicit` was not applicable.

---

## 3. The committed corpus is not reproducible on this machine today

This was not in the plan and is the most important thing found.

Re-running `gemma-4-4b` phase 1 on `HARB Meeting March 4 2025 [jXEH5zsabJU]`, with the same
model file, the same prompt, `temperature=0.0` and chunk size 3:

| Source | Public comment block IDs |
|---|---|
| Committed corpus (`d7cc7ef`, June 2026) | 1, 3, 4, 5, **6** -- five comments |
| Pre-refactor code, re-run today | 1, 3, 4, 6 -- four comments |
| Refactored code, re-run today | 1, 3, 4, 6 -- four comments |

Two things to separate carefully:

1. **The refactor is behaviour-preserving.** The pre-refactor script, extracted from `HEAD`
   and pointed at the same isolated input and output directories, produces results byte
   identical to the refactored script. Two consecutive runs of the refactored script also
   agree with each other, so today's code is deterministic.

2. **Today's code disagrees with the committed corpus**, systematically rather than
   randomly. Block 5 is dropped. The corpus file postdates the grammar-constraint commit
   `c81b4a3` and carries `n_chunk_errors: 0`, so it is not a stale-format artifact.

Something changed between the June run and now that is not the Python: a `llama-cpp-python`
reinstall, a GPU driver update (commit `c2f803c` mentions display driver trouble), or a model
file replaced in place. The pipeline recorded none of those, so it cannot be determined after
the fact -- which is exactly the gap the new `provenance` block closes going forward.

**Implications.**

- The plan's section 6.1 worried about cross-machine float16 drift at ~70 percent confidence.
  This is drift on *one* machine across *time*, which is the same problem and arguably worse,
  because nothing about the setup looked like it changed.
- If the phase-1 agreement numbers are regenerated (section 1), regenerate them from a single
  fresh run of all seven models rather than from the committed corpus, or the agreement
  statistics mix two toolchain states.
- Section 6.1's recommendation to record the toolchain tuple in every output should be treated
  as required, not optional. It now is, for the LLM scripts. `audio_pipeline/transcribe.py`
  still records nothing and should get the same treatment before any transcription run.
- Scope is unknown: one meeting, one model was tested. Quantifying it means re-running one
  model across all 78 meetings and diffing. That is a few hours of GPU time and would convert
  "the corpus may not be reproducible" into a number.

---

## 4. Already satisfied, no action needed

The plan's sections 4 and 5.1 and 5.3 turned out to be already done here:

| Setting | State |
|---|---|
| `HKLM\...\FileSystem\LongPathsEnabled` | already `1` |
| `git config core.longpaths` | already `true` |
| Developer Mode (`AllowDevelopmentWithoutDevLicense`) | already `1` |

Deepest existing path in the corpus is 188 characters, leaving about 70 characters of
headroom, so section 5.3's `MAX_PATH` concern is real but not currently binding.

Because Developer Mode is on, `HF_HUB_DISABLE_SYMLINKS_WARNING` was removed from `.env` and
`.env.example` as section 5.1 instructs, so a future regression becomes visible again.

`core.autocrlf` is `true` here, so section 5.4's concern was live. See below.

The corpus contains **81** meeting JSONs in `downloads/comments`, not the 78 the plan and audit
both cite. Minor, but the discrepancy should be resolved before any count goes in a paper.

---

## 5. What was changed

### New files

| File | Purpose |
|---|---|
| `paths.py` | Repo-root-derived paths, every one overridable by a `HODL_*` environment variable. `HODL_MODELS_ROOT` is required with no default, so a wrong guess cannot silently point at an empty directory. |
| `models.yaml` | The 13-model registry and sampling settings, moved out of Python literals. Model paths are relative to `HODL_MODELS_ROOT`. |
| `prompts/p1_system.txt`, `prompts/p2_system.txt`, `prompts/README.md` | The system prompts, extracted verbatim. |
| `provenance.py` | Builds the `provenance` block written into every output. |
| `.gitattributes` | Line-ending policy that travels with the repository. |

### Modified

- `llm_classify_human_themes.py` -- config and prompts loaded from files; `--dry-run` and
  `--limit N` added; `provenance` written into every output; `llama_cpp` import deferred so
  `--list`, `--dry-run` and `--help` do not initialise CUDA; preflight now hashes the prompt
  files it will use.
- `llm_extract_comments.py`, `chunk_token_histogram.py` -- hardcoded paths replaced. No
  absolute path literals remain in any `.py` or `.ps1` file in the repository.
- `load_env.ps1` -- rewritten. It now strips surrounding quotes (the failure mode where
  `HF_TOKEN="hf_abc"` produced a 401 for a token that looked correct in every printout), trims
  whitespace, warns if `HODL_MODELS_ROOT` is unset or points nowhere, and no longer aborts the
  caller when `Start-Service ssh-agent` fails without Administrator.
- `run_llm_classify.ps1`, `run_overnight.ps1` -- venv path derived rather than hardcoded,
  overridable with `HODL_VENV`; both now source `load_env.ps1`.
- `requirements.txt` -- `pyyaml` added; a comment block records why `llama-cpp-python` must be
  installed manually and which wheel works here.
- `.env.example`, `.env`, `README.md`, `.gitignore` -- updated to match.

### The prompt files are byte-identical to what produced the corpus

This mattered enough to verify rather than assume. The prompts were extracted from the Python
source with `ast`, not retyped, so the Unicode em-dashes and spacing in the originals are
preserved exactly. A round-trip check confirms the file content reproduces the original
rendered system string character for character for both phases. Had they been normalised to
ASCII, every recorded hash would have described a prompt that never produced any existing
output.

### `.gitattributes` causes no renormalization churn

Introducing `* text=auto` into a repository with 2,600-plus tracked files can rewrite
everything. Checked with `git add --renormalize`: only the files edited here appear. An earlier
draft marked `*.ipynb` as `-text`, which would have churned about 20,000 lines across the three
teaching notebooks; `text eol=lf` is a no-op instead, because they are already stored with LF.

---

## 6. Verification performed

- All Python compiles; `paths.py` imports cleanly with `-W error::SyntaxWarning`.
- `--list` works both with and without `HODL_MODELS_ROOT` set. All 13 registry paths resolve
  against `D:\LLM` and all 13 weight files are present.
- `--dry-run` passes for all nine `llama_cpp` models; the four non-`llama_cpp` entries still
  refuse cleanly with their load instructions.
- A real single-meeting inference run was executed against `gemma-4-4b`, using
  `HODL_COMMENTS_DIR` and `HODL_OUTPUTS_ROOT` to redirect both input and output into a
  scratch directory, so no corpus file was touched. `git status downloads/` is clean.
- The output `provenance` block was inspected and is additive: no existing key changed, and
  outputs that predate it still load.
- Concord cloned, `npm install` clean, release gate `node --test tests/e2e/pipeline.test.js`
  passes 18/18. Node here is v24.14.1, above the required 20.10.

---

## 7. What was not done, and why

| Item | Why |
|---|---|
| Commit and push the orphaned analysis work | The files do not exist. See section 1. |
| Clone `AITranscribe` | Private repository, no remote URL available from this machine. It should be pushed somewhere from the Linux workstation before anything else. |
| Second environment for `transcribe2` | Nothing to install into it until `AITranscribe` is here, and the argument for separating it has weakened considerably. See section 2. |
| Concord demo walkthrough | Requires driving a browser through project creation and Director configuration. The install and its release gate are verified; the walkthrough is a human sitting down with it. |
| Quantify the reproducibility gap | Needs a few hours of GPU time. See section 3. |

---

## 8. Suggested order from here

1. **Determine whether the five artifacts exist anywhere.** Everything about the phase-1
   agreement claims depends on the answer, and it is a five-minute search.
2. **Decide how to handle the reproducibility finding.** Either re-run one model across all 78
   meetings to size it, or accept that the corpus must be regenerated in one pass before any
   agreement statistic is computed from it.
3. **Push `AITranscribe` somewhere** from the Linux workstation. It is currently single-copy.
4. Commit the work described here (nothing has been committed yet).
5. Give `audio_pipeline/transcribe.py` the same provenance treatment before any transcription
   run, per section 6.1 of the plan.
6. Concord walkthrough and the human coding it unblocks -- no GPU needed, can proceed in
   parallel with everything else.

---

## 9. Status of section 8's order, as of 2026-09-03

| # | Item from section 8 | Status |
|---|---|---|
| 1 | Determine whether the five artifacts exist anywhere | **Done.** They do. Two recovered from the `AITranscribe/hands_on_dl` snapshot, three regenerated. See section 1. |
| 2 | Decide how to handle the reproducibility finding | **In progress.** Took the "re-run one model across the corpus and size it" path rather than the "regenerate everything first" path. `run_repro_check.ps1` runs it into a scratch output root; `compare_corpus_runs.py` diffs the result. See below for why the answer matters more than expected. |
| 3 | Push `AITranscribe` somewhere | **Moot here.** It is on this machine now, with its own git history. Whether it has a remote is a question for the Linux workstation. |
| 4 | Commit the work described in this document | **Done**, commits `2399602` through `26ebd2b`. |
| 5 | Give `audio_pipeline/transcribe.py` the same provenance treatment | **Done.** `whisper_io.py` records the section 6.1 tuple into every new transcript. The 78 existing bare-list transcripts load unchanged; both schemas are supported because provenance cannot be added retroactively and re-transcribing to obtain it would destroy the thing being preserved. |
| 6 | Concord walkthrough and the human coding it unblocks | **Not started.** Still the right parallel track; needs no GPU. |

### Why item 2's answer now matters more than it did

Section 3 framed run-to-run non-determinism as a threat to citing the corpus.
It is that, but it is also the **noise floor** against which this project's
first real finding has to be read.

`compare_diarization_variants.py` shows that a block whose text is
byte-identical across two runs is classified differently 12-17% of the time when
the 3-block batching window it was judged inside is composed differently, and
0.2-1.3% of the time when it is not. The second number is run-to-run
non-determinism -- the same effect section 3 found, measured at scale for the
first time.

That separation is the whole argument. If the noise floor were comparable to the
chunk effect, the two could not be told apart and neither could be claimed. At
roughly 20-40x apart they can. The full corpus re-run is what turns the
partial estimate into the number that goes in the paper, which is why item 2 is
no longer housekeeping.

### One thing section 8 did not list, found since

`audit_corpus.py` resolves the 81-versus-78 discrepancy noted in section 4, and
the answer is worse than a miscount. 81 files, 3 never coded by any model,
giving 78. Of those 78, **two are stale files in the superseded
`commenter_blocks` schema** that shadow meetings already present as
`_standard`/`_exclusive` pairs. `get_blocks()` falls back to `commenter_blocks`
without comment, so every model coded them -- against a pre-filtered 31-block
input instead of the full 243-block meeting, which is exactly the pre-filtering
`llm_classify_human_themes.py`'s own comment warns against.

Distinct meetings is **53, not the 55** the ISLS audit states, and the real
coded corpus is 76 files over 50 meetings. `tests/test_corpus_integrity.py` pins
all of this so a third stale file fails a test rather than quietly changing a
count.

Decision deferred deliberately: the two stale files have **not** been deleted or
quarantined. Removing them changes every corpus-level number already computed,
and that should be one deliberate act with a notebook entry, not a side effect of
a cleanup.
