# `hands_on_dl` — State Audit and Upgrade Plan

**Parent:** [00-INDEX](./00-INDEX.md) · **Related:** [03 — Technical spec](./03-whisper-concord-spec.md)
**Audited:** 2026-08-14, against working tree at commit `ee37763` ("Ran the rest. will have to check logs later.")

Part 1 reconciles what is actually in the repository against recollection. Part 2 is the upgrade plan. Read Part 1 first — three of the corrections change what Part 2 recommends.

---

# Part 1: State audit

## Your recollection vs. the repository

| Recollection | Verdict | What's actually there |
|---|---|---|
| Completed local LLM filtering to public comments | ✅ **Correct** | 7 models × 78 meetings, phase 1 complete for all of them. `downloads/llm_outputs/<model>/phase1_public_comments/` |
| "Some deepseek models failing... labeling everything as public comment" | ⚠️ **Half right** | **Both** DeepSeek variants failed, in *opposite* directions. `deepseek-r1-7b` flagged **8,882** blocks (precision 0.192 against majority vote) — that's the over-flagging you remember. But `deepseek-r1-14b` flagged only **195** (recall 0.091) — near-total under-flagging. You remembered one failure mode and forgot the other. |
| Have not tried API or ROAR cluster LLM filtering | ✅ **Correct** | `apitest.py` … `apitest4.py` are exploratory endpoint probes — they hunt for a working base URL and model name against what looks like an institutional Azure-OpenAI-style gateway (`api-key` header) with one Anthropic attempt (`x-api-key`). None is wired into the pipeline. `plans/roar_plan.md` exists and is a good plan; nothing has run. |
| Did not do any machine-decided categorization (inductive coding) | ⚠️ **Mostly right, but you *started*** | `llm_extract_comments.py` has a phase 2 that aggregates comments and generates an independent topic analysis — genuine inductive coding. It ran **once, with one model** (Qwen3.5-9B-Q6), on **one meeting**. Output: `downloads/bartowski/Qwen_Qwen3.5-9B-Q6_K_L/public_comments/` contains exactly 1 file. So: scaffolded, smoke-tested, abandoned. Not nothing, but not a result. |
| Did deductive coding to the Rae 4-category criteria | ✅ **Correct, and better than you remember** | `llm_classify_human_themes.py` phase 2 scores every extracted comment **0.0–1.0 on each of four themes, with a free-text `reasoning` string per theme**, under a grammar-constrained JSON schema. That is not a label — it is a graded judgment with a rationale, which is exactly the shape [Concord's evidence inspector](./03-whisper-concord-spec.md#the-evaluation-data-contract) wants. **Phase 2 is incomplete:** deepseek-r1-14b 34/78; gemma 74; phi-4 74; qwen-q6 73; ministral 72; qwen-q8 72; deepseek-r1-7b 78. |
| Have not looked at agreement between Rae and any LLM | ✅ **Correct — and there is nothing to compare against** | `compare_model_agreement.py` covers **phase 1 only**. There is no phase-2 agreement analysis at all. More important: **the repository contains no per-comment human labels from Rae's team.** `data_center_comment_themes.md` has definitions and illustrative anchor quotes, but no coded dataset. Getting one is a prerequisite, not a task. |
| Have not done a human pass of the LLM categorization | ✅ **Correct** | `downloads/agreement_analysis/contested_blocks.csv` (2.2 MB) and `core5_contested_blocks.csv` (611 KB) exist as review queues. Nothing has consumed them. |

**On the lab notebook instinct: yes.** Your recollection was right on four of seven points, half-right on two, and wrong on one — after roughly ten days. The git log is doing notebook duty and is not up to it (`"Ran the rest. will have to check logs later."`, three consecutive commits titled `"gemma and ministral runs done"`). A scaffold is proposed in [Part 2, Step 0](#step-0-start-the-lab-notebook-today-1-hour).

---

## Five things the audit turned up that you did not mention

### 1. You already have pilot data for the ISLS study, and did not know it

`downloads/comments/` holds 81 files for 55 distinct meetings. **26 of those meetings exist in two variants** — `_standard` and `_exclusive` — because `pyannote` was run in two diarization modes and `extract_commenter_blocks.py` emits both when they differ. The other 29 meetings produced identical output under both modes and were written once.

Those 26 pairs are **the same audio, processed two different ways upstream, then coded by the same model with the same prompt.** That is structurally the ISLS experiment, one stage earlier in the pipeline. Running the comparison right now:

| Model | Pairs | Pairs where flag count differs | Total flagged (standard) | Total flagged (exclusive) |
|---|---|---|---|---|
| ministral-8b | 26 | **16** | 630 | 623 |
| qwen3.5-9b-q6 | 26 | **18** | 601 | 596 |
| phi-4 | 26 | **15** | 853 | 846 |

**Read the two columns on the right against the one in the middle.** Aggregate totals move by about 1%. Individual meetings move on 58–69% of pairs, sometimes a lot — *City Council Committee Meeting, June 2 2025* goes 25 → 18 for ministral-8b, a 28% swing on one meeting.

That is the [Southwell pattern from the literature](./01-literature-landscape.md#e1-the-strongest-counterexample--and-it-predicts-a-small-effect) reproduced in your own data: **aggregate robustness masking unit-level instability.** It is also, on its own, a defensible finding — and you can put it in a paper without collecting anything new. See [Step 1](#step-1-mine-the-pilot-you-already-have-1-week).

### 2. Phase-1 agreement is worse than the "53% majority" summary implies

From `core5_model_agreement_report.md` (the five usable models, DeepSeeks excluded):

- Blocks flagged by ≥1 model: **3,263**
- **Unanimous: 785 (24.1%)**
- Majority-agreed: 1,719 (52.7%)
- Contested: 2,478 (75.9%)

Cross-family pairwise Jaccard runs **0.372–0.554**. The one high number in the matrix — **0.840** — is `qwen3.5-9b-q6` vs `qwen3.5-9b-q8`, which is the *same model at two quantizations*. That is a self-consistency measurement, not an agreement measurement, and it should be reported separately or the matrix will mislead a reader (and possibly you).

Blunt reading: **five models applying the same prompt to the same text agree unanimously about a quarter of the time on the simplest possible judgment — "is this a public comment?"** Before any theme coding happens. That is a genuinely interesting result and it is also a warning about how much downstream analysis can rest on it.

### 3. Your block structure is already a spine

`downloads/comments/*.json` blocks carry:

```json
{"block_id": 0, "speaker": "SPEAKER_00", "category": "recurring",
 "start": 135.06, "end": 168.42, "duration_s": 33.4,
 "segment_count": 6, "word_count": 94, "text": "..."}
```

`block_id` + `speaker` + `start`/`end` is precisely the time-anchored join key that [the alignment problem in 03](./03-whisper-concord-spec.md#the-alignment-problem) exists to construct. **You built the hard part already, for a different reason.** The remaining work is freezing it and forbidding downstream stages from renegotiating boundaries.

### 4. There is at least one visible coding error worth looking at directly

In `downloads/llm_outputs/ministral-8b/phase2_theme_scores/City Council Budget Hearing - November 18, 2025 [W6aSdOttjPk].json`, block 58 scores **0.9** on `municipally_managed_resources`, with plausible-sounding reasoning about the city's water fund.

Two problems. First, the speaker is a **council member questioning the finance director** — not a public comment at all, so phase 1 produced a false positive and phase 2 dutifully coded it. Second, and worse, **the block fuses two speakers**: it runs from the councilperson's question straight into the director's answer (`"...what is this to do to future projections down the line yeah so this is the what what is showing on the screen..."`). One unit, two people, no boundary.

Pull this one up and read it. It is a five-minute demonstration that unit boundaries are load-bearing, and it will do more for your intuition than any statistic here.

### 5. Hardcoded absolute Windows paths block everything

`llm_classify_human_themes.py` has `D:\Users\jad507\PycharmProjects\hands_on_dl\...` at module scope for `COMMENTS_DIR`, `THEMES_MD_PATH`, and `OUTPUTS_ROOT`; `llm_extract_comments.py` does the same plus `D:\LLM\bartowski\...` for the model. Nothing runs anywhere but that one machine.

This is the single concrete blocker on the ROAR plan, the API path, and any possibility of a collaborator reproducing your work. It is also a two-hour fix.

---

## What is genuinely strong here

Stated plainly, because the audit above is mostly problems and the balance matters:

- **`data_center_comment_themes.md` is a real codebook.** Four themes, named sub-themes, anchor quotes with speaker attribution, and — unusually — an explicit **analytical stance**: *"The researchers did not assess the factual accuracy of speakers' claims. Comments are treated as situated narratives."* Most people attempting LLM coding studies do not have a human-authored codebook with a declared epistemology. You do.
- **Grammar-constrained JSON output.** `llama.cpp`'s schema-constrained sampler means the model *physically cannot* emit invalid JSON. Most published LLM-coding work parses free text and discards failures, which silently biases the sample. You avoided that.
- **Rationales, not just labels.** Every theme score carries a `reasoning` string. This lets you compare *reasons* across models and against humans, which is a stronger analysis than label agreement alone and maps directly onto Concord's evidence inspector.
- **Resumable, per-file, idempotent runs**, with pre-flight checks and retries. Cheap to say, tedious to build, and it is why seven models × 78 meetings actually finished.
- **Two diarization variants preserved rather than collapsed.** Accidental, and it gave you [the pilot](#1-you-already-have-pilot-data-for-the-isls-study-and-did-not-know-it).

---

# Part 2: Upgrade plan

Ordered by value per hour, with the [October ISLS deadline](./02-submission-strategy.md#timeline) as the constraint. Steps 0–2 need no new data, no cluster, and no IRB.

## Step 0: Start the lab notebook (today, 1 hour)

Create `hands_on_dl/NOTEBOOK.md`. Append-only, newest entry at top, one entry per work session. A scaffold is written to [`docs/isls2027/NOTEBOOK-template.md`](./NOTEBOOK-template.md) — copy it into the repo root.

Minimum viable entry:

```markdown
## 2026-08-14

**Ran:** compare_model_agreement.py on core5, phase 1 only
**Config:** commit ee37763, 5 models, 78 meetings
**Result:** unanimous 24.1%, majority 52.7%; qwen q6/q8 Jaccard 0.84 (same model, 2 quants — not independent)
**Surprised by:** deepseek-14b under-flags (195 blocks) as badly as 7b over-flags (8882)
**Next:** phase-2 agreement; no human labels exist yet
**Open question:** is block 58 in the Nov-18 budget hearing two speakers fused into one unit?
```

The `Surprised by` and `Open question` fields are the ones that pay off. Facts are recoverable from the repository; the reasoning that produced them is not — as this audit demonstrated.

Also add a `RESULTS.md` recording, per experiment: the commit hash, model, config, N, and the headline number. When you write the ISLS paper in September you will need these and they will not be in your head.

## Step 1: Mine the pilot you already have (1 week)

**This is the highest-value work in the entire plan, and it requires nothing new.**

1. **Write `compare_diarization_variants.py`** — for the 26 meetings with both variants, for each model, compute: flagged-count delta, Jaccard on flagged `block_id` sets, and (once block alignment is solved) per-block flip rate. Extend to phase 2: does the theme-score vector move for comments that survive in both variants?
2. **Fix the qwen q6/q8 reporting.** Split the pairwise matrix into *cross-model agreement* and *within-model quantization stability*. They answer different questions and averaging them together is misleading.
3. **Compute proper reliability statistics.** Jaccard is not the field's currency. You need **Krippendorff's α** and **Gwet's AC1** — the latter specifically because it is robust to the high-prevalence/low-marginal skew you have. [Concord ships all of them](./03-whisper-concord-spec.md#statistics--and-concord-already-ships-them) in `server/stats/agreement.js`; in Python, `krippendorff` and `irrCAC` are the usual choices.
4. **Add block-level alignment across variants.** The two diarization modes produce different block boundaries, so `block_id` will not join. Use `(speaker, round(start, 1))` with a tolerance window, or interval-overlap matching. **This is the same problem as [03 §The alignment problem](./03-whisper-concord-spec.md#the-alignment-problem) — solve it once here, on data you already own, and the ISLS harness inherits the solution.**

Deliverable: a figure showing aggregate stability alongside per-meeting instability. That figure alone could anchor a 4-page demo paper.

## Step 2: Make the code portable (2 hours, unblocks everything downstream)

1. Replace every hardcoded path with `pathlib.Path` resolved from an env var or CLI argument, defaulting to `Path(__file__).parent`. Affects `llm_classify_human_themes.py`, `llm_extract_comments.py`, `extract_commenter_blocks.py`.
2. Extract the config block into `config.yaml` (paths, chunk sizes, `N_CTX`, model registry).
3. Add `--dry-run` and `--limit N` flags for smoke tests.
4. Put the prompts in versioned files — `prompts/p1_public_comment.v1.txt`, `prompts/p2_theme_score.v1.txt` — and **record the prompt hash in every output file.** Right now the prompts live in Python string literals, which means you cannot tell from an output which prompt version produced it. This is [exactly what Lopez-Fierro & Nguyen's award-winning CSCL 2024 paper asks researchers to do](./02-submission-strategy.md#evidence-1-ai-in-qualitative-coding-work-does-not-merely-get-published--it-wins-awards): disclose the prompts used. Do it as engineering, get the methodology for free.

## Step 3: Finish and analyze phase 2 (1 week)

1. **Complete the missing runs.** 4–6 meetings per model, plus 44 for deepseek-r1-14b (which is probably not worth the GPU time — its phase-1 output is unusable, so its phase-2 output is coding a corrupt input set. Consider dropping it and saying so.)
2. **Write `compare_theme_agreement.py`.** Phase 2 is continuous (0.0–1.0 per theme), so this needs different machinery than phase 1: intraclass correlation or Krippendorff's α at interval level, plus α at nominal level after thresholding. **Choose and pre-register the threshold** — 0.5 is a decision, not a default, and sweeping it post hoc is a researcher degree of freedom you are trying to make visible in others.
3. **Analyze the rationales, not just the scores.** Where two models assign similar scores with incompatible reasoning, that is a more interesting finding than a κ. Sample 50 and read them.

## Step 4: Get human labels — the real bottleneck (start now, finishes last)

Nothing downstream of "how well do models agree with humans" can proceed without human-coded data. Two paths, run in parallel:

**Path A — ask Rae.** Her team did the exploratory thematic analysis that produced `data_center_comment_themes.md`. Ask whether per-comment coded data exists. If it does, this is secondary analysis of existing data and the question becomes a data use agreement plus [Penn State's IRB determination process](./02-submission-strategy.md#irb--the-penn-state-process). Ask now — a DUA takes longer than you expect, and the answer determines the paper.

**Path B — code it yourself.** Draw a stratified gold sample of **150–200 blocks** from `contested_blocks.csv`, oversampling contested ones. Code them against the four themes, blind to model output. Budget 8–12 hours.

Path B is not a consolation prize. Coding it yourself is what makes you able to *speak* about the codebook in a paper — and per [the methodological position that motivated this whole project](./00-INDEX.md#provenance-note-on-the-framing), the researcher who has not been through the data has no standing to interpret it. Do Path B regardless of whether Path A lands.

**Blind coding matters.** Do not look at model output first. Concord's Calibration Studio is built for exactly this (restricted listener sessions, blind double-coding, adjudication, then a frozen certificate), which is an argument for doing your gold coding *inside* Concord rather than in a spreadsheet.

## Step 5: Bridge to Concord (2 weeks, the ISLS deliverable)

Full contract in [03](./03-whisper-concord-spec.md). The `hands_on_dl`-specific work:

1. **`export_vtt.py`** — emit `downloads/comments/*.json` blocks as WebVTT with `<v SPEAKER_00>` voice tags and exact block `start`/`end`. Watch two things from the [source reading](./03-whisper-concord-spec.md#what-concord-actually-accepts): speaker labels must start with a capital letter (`SPEAKER_00` is fine, `speaker_00` is not), and **anything in angle brackets other than the voice tag gets deleted by `stripTags()`**.
2. **Set `maxMergeGapSeconds` to prevent re-merging.** Your blocks are already grouped; Concord's default 30-second same-speaker merge window will fuse them again and silently change N.
3. **Port the codebook.** `data_center_comment_themes.md` → four Concord constructs with inclusion/exclusion criteria and the anchor quotes as examples. Mostly mechanical; the four sub-themes per theme may or may not survive as separate constructs — decide deliberately.
4. **Point Concord at local models.** `llama.cpp`'s server speaks the OpenAI API, so use Concord's OpenAI adapter with a local `baseUrl`, or run Ollama (auto-discovered at `localhost:11434`). Either keeps you in privacy mode `strict`, where no unit text leaves the machine — which is worth real money in an IRB conversation.
5. **Then add the transcription-policy dimension.** Re-transcribe a subset under N policies, hold the frozen block spine, and run the [experimental design in 03](./03-whisper-concord-spec.md#experimental-design).

## Step 6: ROAR / API (defer — and here is why)

[`plans/roar_plan.md`](../roar_plan.md) is a good plan: vLLM instead of llama-cpp, guided JSON replacing GBNF, a 32B on a single A100 first, 70B on 2×A100 only if the 32B does not clearly beat ministral-8b. Keep it.

**But it is now the wrong next step.** The plan's stated purpose is to produce a reference model that scores the small ones. Since it was written, two things changed:

- **A big model is not ground truth.** It is an eighth opinion. Substituting "the 32B agrees with me" for "a human agrees with me" is the failure mode the [quantitative ethnography literature](./01-literature-landscape.md#d-quantitative-ethnography--the-methodological-home) exists to prevent, and an ISLS reviewer will say so.
- **The ISLS contribution does not need a bigger model.** It needs *one* judge held constant while the transcript varies. Adding models adds a nuisance dimension.

Prerequisites before it is worth doing: Step 2 (paths — SLURM cannot see `D:\`), Step 4 (human labels, so there is something to calibrate against), and a Roar allocation. Revisit after ISLS.

Same for the API path. `apitest*.py` should be either finished into a working adapter or deleted — four abandoned probe scripts in the repository root is how you forget you already tried this. If a frontier model is worth adding later, add it *after* there is gold data to measure it against.

---

## Sequencing summary

| Step | Effort | Blocks what | Do it when |
|---|---|---|---|
| 0. Lab notebook | 1 h | Nothing — pure insurance | **Today** |
| 1. Mine the diarization pilot | 1 wk | The ISLS demo's headline figure | **This week** |
| 2. Portability + prompt versioning | 2 h | ROAR, API, collaborators, reproducibility | **This week** |
| 3. Finish + analyze phase 2 | 1 wk | Any theme-level claim | August |
| 4. Human labels | 8–12 h + lead time | *Everything* involving accuracy | **Email Rae today**; code it yourself in August |
| 5. Concord bridge | 2 wk | The ISLS deliverable | Late August |
| 6. ROAR / API | — | Nothing on the ISLS path | After ISLS |

**If you only do two things this week: start the notebook, and run the standard-vs-exclusive comparison.** The second one may already be your paper.

---

**Back to:** [00-INDEX](./00-INDEX.md)
