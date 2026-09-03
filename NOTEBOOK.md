# Lab Notebook -- hands_on_dl

Append-only. Newest entry at the top. One entry per work session, however short.
Never edit a past entry to make it correct: write a new one saying so and link
back. The record of being wrong is the most valuable thing in here.

Every entry carries the commit hash. An entry without one cannot be reproduced.
Fill in **Surprised by** and **Open question** even when the answer is "nothing".

Scaffold and rationale: `AITranscribe/docs/isls2027/NOTEBOOK-template.md`.
Companion: `RESULTS.md`, one row per experiment, for finding a number fast.

---

## 2026-09-03 (later) -- CAPITALS, not asterisks: Concord silently merges sentences

**Commit:** 475cd80
**Ran:**
```
node tools/concord_marker_probe.mjs
python -m pytest tests/ -q                       # 110 passing
python AITranscribe/transcribe2/doctor.py
python -m pytest AITranscribe/transcribe2/test_pipeline.py -q
pip install --no-deps praat-parselmouth
pip install --upgrade "transformers>=5.10.1"     # 5.5.0 -> 5.16.1
```

**Result:**

1. **ISLS doc 06's open question is answered, and half its suggestion is wrong.**
   The doc proposes prominence notation for policy P5 and says "capitals for
   stress or asterisks (`*money*`); test which survives tokenization". Both
   survive `stripTags()`. Only capitals survive **unitization**.

   `splitSentences()` splits after `.!?` only when the next non-whitespace
   character is `\p{Lu}` or a digit, looking one character further past a quote
   or an opening bracket. An asterisk is none of those, so:

   | notation | survives ingest | preserves unit boundaries |
   |---|---|---|
   | CAPITALS | yes | **yes** |
   | `[square]` | yes | **yes** |
   | `"quote"` | yes | **yes** |
   | `*asterisk*` | yes | **no** |
   | `**double**`, `_under_`, `^caret^`, `{curly}`, `|pipe|` | yes | **no** |
   | `<em>angle</em>` | **no** (silently stripped) | n/a |

   "He denied it. *Money* was the issue." becomes **one** unit, not two. That
   changes N, changes every content-hashed unit id, and changes the question the
   judge is asked, while looking like it worked. For a design whose thesis is
   that unit boundaries are load-bearing, that is disqualifying.

2. **Unit ids do change when the policy changes**, demonstrated rather than
   assumed: `u_7ca821c35c74adfb` plain vs `u_10d1e18e7506105e` with CAPITALS.
   Confirms doc 03 finding 3 and the requirement that cross-condition joins go
   through time anchors. `blockmatch.py` is that join.

3. **transcribe2 runs on this machine.** Its own suite is 45 passed, 8 subtests.
   `doctor.py` is now green on all five capabilities. Two installs got it there:
   `praat-parselmouth` 0.4.7 (unblocks F0, so the Tier-2 prosody path in doc 06
   is available) and `transformers` 5.5.0 to 5.16.1 (unblocks Gemma 4 audio).

4. **The transformers upgrade was the cheap path, as status doc section 2
   predicted.** `pip install --dry-run` showed it touching exactly three
   packages -- transformers, tokenizers, safetensors -- and not torch, peft or
   trl. Ran it, then re-ran both suites: hands_on_dl 110 passed, transcribe2 45
   passed, `llama_cpp.llama_supports_gpu_offload()` still True. No second
   environment was needed and none was created.

5. `doctor.py`'s `HF_TOKEN unset` warning is a false alarm: it does not read
   `.env`. Loaded via `load_env.ps1` the token is present and well-formed.

**Surprised by:** that the asterisk failure is a *unitization* failure rather
than a stripping one. I expected the answer to be decided by `stripTags` and it
was not -- asterisks pass that test cleanly. The thing that disqualifies them is
two modules downstream, produces no error, and would have been invisible until
somebody noticed the unit count was wrong. Doc 06 guessed the right question and
the wrong hazard.

Also surprised the transformers jump landed on 5.16.1 rather than 5.10.x, and
that nothing broke. The plan's original second-environment recommendation was
insurance against a risk that had already been retired.

**Decided:**
- **Policy P5 uses CAPITALS.** Square brackets are the fallback if capitals turn
  out to interact badly with a judge prompt. Not asterisks, not underscores.
- Pin the whole table in `tests/test_concord_markers.py`, driving Concord's real
  modules rather than reimplementing its tokenizer, so the finding tracks the
  dependency instead of a snapshot of it.
- Upgrade in place rather than build a second environment. Snapshots kept either
  side: `env-snapshot-2026-09-03-pip.txt` and `-post-upgrade-pip.txt`.
- Did **not** install librosa: parselmouth covers F0 and librosa is only the
  fallback, with a much larger dependency surface.

**Next:** the gemma re-run is at 17/81. When it lands, `compare_corpus_runs.py`
gives the full noise floor. After that the GPU is free for the direct
chunk-framing experiment: one meeting at `p1_chunk_size` 1, 3 and 5, plus
deliberate offsets, which is the clean version of the effect rather than the
natural experiment.

**Open question:** the notation choice is itself a transcription decision, which
doc 06 notes is "pleasingly recursive". But there is a real empirical question
under it: does an LLM judge given `MONEY` actually read it as prosodic emphasis,
or as shouting, or ignore it? Doc 06's proposed control is right -- give the
model the *wrong* prominence annotation and see whether it produces the meaning
that annotation implies. That needs no new corpus and is a good use of the GPU
once it is free.

---

## 2026-09-03 -- Chunk framing, not diarization, drives phase-1 instability

**Commit:** 26ebd2b (work uncommitted at time of writing)
**Ran:**
```
python compare_diarization_variants.py
python compare_model_agreement.py
python audit_corpus.py
python -m pytest tests/ -q
.\run_repro_check.ps1 -Model gemma-4-4b       # still running
```
**Config:** all 7 models, phase 1 and 2, committed corpus, `p1_chunk_size = 3`,
alignment `min_iou = 0.10`

**Result:**

1. **The five "lost" artifacts were not lost.** `compare_model_agreement.py` and
   `plans/roar_plan.md` survive in the `AITranscribe/hands_on_dl` snapshot dated
   2026-07-17 -- the tree the ISLS audit was actually run against. Recovered,
   modernised, and re-run. It **reproduces the audit's figures exactly**: 3,263
   blocks flagged by >=1 model, 785 unanimous (24.1%), 1,719 majority (52.7%),
   2,478 contested (75.9%), cross-model Jaccard 0.372-0.554, qwen q6-vs-q8 0.840.
   `plans/windows_environment_upgrade_status.md` section 1 concluded these numbers
   had no artifact behind them. They do. That section is superseded.

2. **The diarization-variant pilot does not measure what the audit thought.**
   Aligning the 26 variant pairs by time: 97.3% of blocks align 1:1, and of those
   **99.4% have byte-identical text** (3,230 of 3,250). The two pyannote modes
   disagree about a handful of turn boundaries, not about what was said. So the
   flag instability the audit found cannot mostly be an upstream-processing effect.

3. **It is a chunk-framing effect.** Holding text byte-identical and splitting on
   whether the enclosing 3-block chunk was also identical:

   | model | identical chunk | shifted chunk |
   |---|---|---|
   | gemma-4-4b | 0.22% | 13.77% |
   | ministral-8b | 0.35% | 11.67% |
   | phi-4 | 0.61% | 17.14% |
   | qwen3.5-9b-q6 | 1.27% | 13.67% |
   | qwen3.5-9b-q8 | 0.35% | 14.30% |
   | deepseek-r1-7b | 0.66% | 14.30% |
   | deepseek-r1-14b | 0.26% | 2.21% *(base-rate artifact, see below)* |

   A ~25x difference on identical input text. Normalised by blocks either variant
   called a public comment, the shifted-chunk disagreement rate is **50-60%** for
   the five usable models. Phase 1 batches blocks three at a time; one inserted or
   deleted block upstream shifts every later chunk boundary, so a block gets judged
   alongside different neighbours. `P1_CHUNK_SIZE` was chosen to fit a context
   window and was never treated as a methodological decision.

4. **deepseek-r1-14b's low rate is not stability.** It flags almost nothing, so it
   has almost nothing to flip. Among blocks it or its pair flagged, its
   shifted-chunk disagreement is 21/21 = 100%.

5. **Phase 2 is far more stable than phase 1.** On byte-identical text, mean
   absolute theme-score delta is 0.002-0.005 and only 0.2-0.8% of scores cross the
   0.5 threshold. Phase 2 scores one comment at a time, so it has no chunk to shift.
   That is consistent with the mechanism in (3) rather than with general model noise.

6. **Corpus count chain resolved.** 81 files in `downloads/comments`, 3 never coded
   by any model, giving the 78 every planning document quotes. Of those 78, **2 are
   stale files in the superseded `commenter_blocks` schema** that shadow meetings
   already present as `_standard`/`_exclusive` pairs. `get_blocks()` falls back to
   `commenter_blocks` silently, so all seven models coded them -- against a
   pre-filtered 31-block input instead of the full 243-block meeting, which is
   exactly the pre-filtering that function's own comment warns against. Real
   corpus: 76 legitimately coded files over 50 distinct meetings. Distinct meetings
   overall is **53, not the 55** the audit states.

7. **Noise floor, partial.** The gemma re-run is 4/81 meetings in. On those,
   4 of 974 blocks changed classification (0.41%), corpus Jaccard 0.962. Aggregate
   counts were identical (23 vs 23, 43 vs 43) while individual blocks swapped.

**Surprised by:** that the two diarization variants are ~99.4% identical in text.
The whole pilot was framed on them being meaningfully different processing. They
are not, and that is what makes the chunk result clean: the text is held
byte-identical rather than merely similar, so there is no transcript confound at
all. The finding got stronger by the premise being wrong.

Also surprised that phase 2 barely moves. I expected the continuous scores to be
noisier than the binary judgement, not ~50x quieter.

**Decided:**
- Report the identical-chunk residual (0.2-1.3%) as its own column rather than
  folding it into the chunk effect. It is run-to-run non-determinism and belongs
  with the reproducibility finding, not with the framing finding.
- Exclude `deepseek-r1-14b` from summary ratios, and always print a base-rate
  column next to any flip rate so its degeneracy is visible rather than inferred.
- `min_iou = 0.10` for alignment, with a sensitivity sweep written to
  `threshold_sensitivity.csv` so the choice is inspectable. Not yet pre-registered.
- Compute agreement over the **full block universe**, not only flagged blocks. The
  old framing selects on the outcome and cannot be chance-corrected. Both are
  reported; `all_blocks` is the one to quote.
- Do not delete the two stale files. Pin them in `tests/test_corpus_integrity.py`
  so a third one is a test failure, and decide on quarantine deliberately.

**Next:** let the gemma re-run finish, then `compare_corpus_runs.py` for the full
noise floor. The chunk effect only stands if the noise floor is well below 12-17%;
at 0.41% on the first four meetings it looks safe, but that is four meetings.

**Open question:** is the chunk effect *directional* or just noise amplification?
If a block is more likely to be called a public comment when batched with two real
comments than with two procedural blocks, that is a context-contamination bias with
a sign, and far more serious than symmetric instability. `flip_detail.csv` has the
data to answer it and I have not looked. Second: does `p1_chunk_size = 1`
eliminate it, and what does that cost in throughput and in recall?

---

## 2026-08-28 -- Environment audit and portability refactor

**Commit:** 26ebd2b and the four commits before it
**Ran:** environment inspection; refactor of paths, config and prompts into files
**Config:** venv at `../LancasterClaude/.venv`, Python 3.12.6, torch 2.11.0+cu128,
transformers 5.5.0, llama-cpp-python 0.3.24 (`llama_supports_gpu_offload()` True),
RTX A2000 12 GB, compute capability 8.6

**Result:** recorded in full in `plans/windows_environment_upgrade_status.md`.
Headline: this is not a conda environment and `transformers` was already on 5.x, so
the second-environment recommendation was unnecessary. Hardcoded `D:\` paths
removed from every `.py` and `.ps1`. Prompts extracted with `ast` so they are
byte-identical to what produced the corpus. Provenance block added to every output.

**Surprised by:** re-running gemma-4-4b on one meeting today gives 4 public comments
where the committed corpus has 5, with the same model file, prompt and temperature.
The refactor was verified behaviour-preserving and today's code is self-consistent,
so something outside the Python changed between June and now and nothing recorded it.

**Decided:** treat toolchain provenance as required rather than optional.

**Next:** size the reproducibility gap across the whole corpus.

**Open question:** whether the June corpus can be cited at all, or has to be
regenerated in one pass first.
