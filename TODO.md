# TODO

**Updated 2026-09-18.** Ranked, with the reason each one matters and the command
where there is one. Companion to `HANDOFF.md` (state and standing rules),
`NOTEBOOK.md` (reasoning, newest first) and `RESULTS.md` (one row per number).

Tick items here as they land. When one is done, say what it produced rather
than deleting it, so the list doubles as a record.

---

## Blocking everything

- [ ] **Human-code the gold sample.** 8 to 12 hours. The sample is drawn,
      stratified, blind, weighted and pre-registered in `downloads/gold_sample/`.
      Until it exists every result in the project is agreement between machines,
      not accuracy, and condition C of the chunk experiment cannot be interpreted
      at all. Concord's whole correction method rests on exactly this artifact,
      so nothing downstream substitutes for it. No amount of compute helps.

- [ ] **Label the 20 strong stress videos yourself.** About an hour. Roughly 90
      seconds each, marking which word carries the stress in each repetition,
      giving about 100 labelled utterances. The detector currently reports 80%
      accuracy **on n = 5**, and that interval is enormous. This is the cheapest
      high-value hour on the whole list. Binary prominence only; trained
      phoneticians agree at kappa 0.57 on weak versus strong.

---

## Weekend-runnable now

- [ ] **Finish the downloads.** 20 of about 120 done, resumable from
      `downloads/videos/stress_search/youtube_archive.txt`. No manifest was
      written before the session died, so the next run should produce one.
      Never TikTok; the user's own TikTok files stay untouched in their folder.

- [ ] **Run Whisper over the whole stress corpus.** Every dependency is cached
      locally. This produces the Tier 0 baseline and the frozen spine that any
      later Gemma comparison needs, so it is a prerequisite rather than a
      fallback.

      ```
      python batch_transcribe.py --media-dir downloads/videos/stress_search/youtube \
          --outdir downloads/transcribe2_runs --engines whisper --resume
      ```

      Launch it detached, not with `run_in_background` -- see HANDOFF section 6.

- [ ] **Decide about pyannote for this corpus.** The smoke test fell back to
      `energy-vad` because `HF_TOKEN` was not in the shell environment.
      `doctor.py` reports "real diarization: yes" on the package being installed,
      which is a weaker claim than it sounds. For one speaker repeating a
      sentence, VAD is arguably the better tool anyway; for council meetings it
      is not. Either load `.env` first or pass `--diarize vad` deliberately, so
      the choice is recorded rather than defaulted.

---

## Gemma audio, currently blocked

- [ ] **Update the llama.cpp build.** It is from 2026-08-03 and
      `llama-mtmd-cli` crashes with `0xC0000409` after loading the model, taking
      the Claude session down with it. `transcribe2/engines.py` documents why:
      llama.cpp could not parse Gemma 4 audio at launch, was fixed days later,
      and Ollama's audio path had its own crash. Test any new build in a
      throwaway shell, never in-session.

      The model itself is already here and needs no download:
      `gemma-4-E4B-it-UD-Q8_K_XL.gguf` plus `mmproj-F16.gguf`, whose metadata
      carries `clip.has_audio_encoder = True` and
      `clip.audio.projector_type = gemma4a`.

- [ ] **If llama.cpp stays broken, price the Transformers route.**
      `GemmaEngine` already implements it and transformers 5.16.1 clears the
      version gate, but `google/gemma-4-E4B-it` is **not** in the HF cache. That
      is a gated download of roughly 16 GB, and bf16 E4B does not fit 12 GB
      without offload, which would be slow across 120 videos.

- [ ] **Then run the policy comparison.** Same audio, same frozen spine,
      Whisper against `default-asr`, `full-verbatim` and `prominence-verbatim`.
      The question is whether an audio-native model recovers the stress
      placement Whisper destroys. Every outcome is publishable. Keep the
      acoustic detector as the referee: a model that both transcribes and judges
      the stress is scoring its own work.

---

## Concord

- [ ] **Run the demo end to end once.** `start.bat`, then
      `demo/techcorp-exit-survey.csv` with the Director set to `mock`. The mock
      judge is deliberately about 90% accurate, which is what makes the
      correction visibly move a number. Understanding the ladder on data that
      does not matter is cheaper than learning it on yours.

- [ ] **Decide the privacy mode before real data goes in.** `strict` disables
      every network adapter application-wide and forces local models. The
      corpus holds identifiable public testimony and the repository is public,
      so this is worth a deliberate choice.

- [ ] **Install Ollama** if Concord should judge locally. Auto-discovered at
      `localhost:11434`. Not needed for the mock or for an API key.

- [ ] **Re-run the marker probe after any Concord update.** The notation
      decision depends on `splitSentences()` behaviour that could change.

      ```
      node tools\concord_marker_probe.mjs D:\Users\jad507\PycharmProjects\concord
      ```

---

## Analysis debts

- [ ] **Audit `RESULTS.md` for mid-run analysis figures.** Before commit
      `8fe2bdf`, `chunk_experiment.py analyse` treated a condition's existing
      directory as complete, so a call made while a run was in flight reported a
      confident wrong effect with no warning. The guard stops it recurring but
      says nothing about what is already recorded, and **there is no way to tell
      from a figure's output whether it was affected**. Not yet audited.

- [ ] **Consider a fourth model for the chunk experiment.** The open question
      is why ministral is flat on condition C while gemma and phi-4 both
      suppress. At 8B it is both the largest of the three and the lowest-noise
      one, so "ignores the batch context" and "is simply more stable" predict
      the same observation and this design cannot separate them.

- [ ] **Decide what the ISLS paper is.** The batching finding is finished,
      controlled, replicated across three models and needs no ethics approval.
      The transcription-policy study is more ambitious and needs a real
      `transcribe2` run behind it. Doc 08 section 8 lays out the options.

---

## Housekeeping

- [ ] **Pick a canonical home for the duplicated code.** `transcribe2/` and the
      stress tools now exist in both this repository and `../AITranscribe`, with
      nothing enforcing that they match. Both copies were normalised to ASCII
      together so the next sync is a copy rather than a merge, but that only
      holds until someone edits one side. Same problem for the ISLS docs, which
      live in `plans/isls2027/` here and `docs/isls2027/` there.

- [ ] **Delete the merged branches** when convenient. `isls-chunk-framing` and
      `portable-paths-and-provenance` are both fully contained in `main`, local
      and on the remote.

---

## Done recently

- [x] **2026-09-18. Batch driver** (`batch_transcribe.py`, 22 tests). Smoke
      tested on a real 22-second video: 8 segments, whisper large-v3, 74
      seconds. First time `transcribe2` has processed real audio. Whisper
      returned **8 byte-identical strings** for 8 differently-stressed readings
      of "I didn't say we should kill him" -- the thesis, reproduced by the
      pipeline it is about.
- [x] **2026-09-18. Emphasis notation switched to CAPITALS** in all three
      places, and the note justifying asterisks replaced. It had checked
      `stripTags()`, found asterisks survive, and stopped; the hazard is
      `splitSentences()` two modules later.
- [x] **2026-09-18. Merged to `main` and pushed.** Repository confirmed public
      and left that way by decision.
- [x] **2026-09-07. phi-4 completed the chunk experiment.** Three models. The
      invariant to quote is contested blocks flipping **27.5-36.5%** under a
      pure batching shift.
- [x] **2026-09-07. Stress corpus measured**, 81 of 91. Measurement is
      deterministic across a three-day gap and a caption refetch.
