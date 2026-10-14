# Contrastive stress: do local audio LLMs hear it?

Code and results behind the ICDS Symposium 2026 poster by Jeffrey De Lucca
(M.S. in Artificial Intelligence student, Penn State World Campus, jad507@psu.edu).

*"I didn't say he stole the money"* means seven different things depending on which word is stressed, and a
transcript erases the difference. This folder reproduces the StressTest benchmark
([Yosha et al., 2025, arXiv 2505.22765](https://arxiv.org/abs/2505.22765)) with audio language models that run on
one consumer GPU, and adds two things the paper did not test: a pre-transformer signal-processing baseline, and
the paper's "detector marks the transcript, a text model reads it" pipeline with *local* readers.

All intervals are Wald 95% intervals (p ± 1.96·√(p(1−p)/n)); the readings are treated as independent, which they
are not quite (each StressTest sentence is read two or more ways by the same actor).

## Results

**Benchmarks.** StressTest: 218 readings by one actor. StressPresso: 202 readings by 4 Expresso speakers.
SSR = choose the speaker's meaning, 2 options (chance 50%). SSD = name the stressed words (word-level F1).
Local models: Gemma-4 E2B and E4B (transformers, bf16), NVIDIA Nemotron 3 Nano Omni 30B-A3B (llama.cpp, Q4_K_M).
Paper numbers in *italics*.

| model | StressTest SSR | StressTest SSD F1 | StressPresso SSR | StressPresso SSD F1 |
|---|---|---|---|---|
| Gemma-4 E2B, thinking off / on | 0.532 / 0.468 | 0.366 / 0.361 | 0.485 | 0.326 |
| Gemma-4 E4B, thinking off / on | 0.523 / 0.528 | 0.399 / 0.367 | 0.535 | 0.361 |
| Nemotron 3 Nano Omni, off / on | 0.518 / 0.560 | 0.441 / 0.338 | 0.520 | 0.351 |
| WhiStress (reproduced) | — | **0.884** (*0.883*) | — | **0.835** (*0.835*) |
| *GPT-4o-audio* | *0.688* | *0.461* | *0.648* | *0.369* |
| *Gemini-2.5-Pro* | *0.775* | *0.485* | *0.727* | *0.407* |
| *Qwen2-Audio-7B → StresSLM (fine-tuned)* | *0.532 → 0.862* | *0.331 → 0.869* | *— → 0.876* | *— → 0.806* |
| *human listeners* | *0.926* | | *0.896* | |

No local model's SSR clears chance on either benchmark (widest: Nemotron thinking, 0.560, Wald 0.494–0.626).

**Finding the stressed word** (top-1: is the word a method rates most stressed a labelled stressed word):

| method | StressTest | StressPresso |
|---|---|---|
| WhiStress (Whisper + stress head, 2025) | 0.982 | 0.941 |
| Wavelet Prosody Toolkit (Suni et al., 2017) | 0.606 | 0.644 |
| Praat z-score (F0 + intensity + duration) | 0.560 | 0.545 |
| "last word" text-only rule | 0.239 | 0.139 |
| chance | 0.194 | 0.164 |

**The pipeline test.** Same SSR question, text only: the transcript with the stressed word(s) in CAPITALS, from
each source, read by a local model with thinking off.

| marked in the transcript | E4B, StressTest | E4B, StressPresso | Nemotron, StressTest | Nemotron, StressPresso |
|---|---|---|---|---|
| nothing | 0.495 | 0.525 | 0.523 | 0.495 |
| Praat's top word | 0.578 | 0.624 | 0.564 | 0.584 |
| wavelet's top word | 0.610 | 0.614 | 0.592 | 0.619 |
| WhiStress's top word | 0.706 | 0.718 | 0.651 | 0.698 |
| WhiStress's marks | 0.716 | 0.683 | 0.656 | 0.683 |
| true stressed words | 0.729 | 0.713 | 0.683 | 0.698 |
| *(the audio instead)* | *0.523* | *0.535* | *0.518* | *0.520* |

A local model that cannot hear stress can read it: a classical detector's word in the transcript beats the model
listening to the audio itself, and WhiStress brings it close to its ceiling with perfect marks. The paper's
cascade with text GPT-4o: *0.834 / 0.862* (StressTest), *0.797 / 0.836* (StressPresso). Gemma-4 E2B is too weak a
reader to show this (0.514 plain, 0.583 with true marks). Each cell: n = 218 or 202, Wald half-width ≈ 0.06–0.07.

**Unprompted marks.** Asked only to transcribe, with a prompt that permits \*emphasis\* marking, on StressTest:
Nemotron marks 18 of 218 readings, 16 on the truly stressed word; Gemma-4 E4B marks 60, 16 right (0.27, about
chance); E2B marks 14, 4 right. A plain "transcribe verbatim" prompt: no marks from any of them.

## Reproducing

Scripts expect their data in `stress_search/` beside them. Audio is not included (the benchmark datasets are
downloadable; the rest is other people's recordings).

```
pip install -r requirements-stress.txt              # plus torch for your CUDA
git clone https://github.com/slp-rl/WhiStress       # then: git am patches/whistress-transformers5-compat.patch
git clone https://github.com/asuni/wavelet_prosody_toolkit    # in its own venv (see measure_classical.py)

python export_stresstest.py [--dataset stresspresso]          # benchmark audio + manifest
python validate_whistress.py [--dataset slprl/StressPresso ...]  # WhiStress SSD
python measure_whistress.py  --manifest stress_search/stresstest/manifest.csv --conditions stresstest --out ...
python measure_classical.py  --manifest stress_search/stresstest/manifest.csv --conditions stresstest --out ...
python score_stresstest.py [--dataset stresspresso]            # top-1 table
python reproduce_stresstest_gemma.py --model google/gemma-4-E4B-it --ple-cpu [--dataset stresspresso]
python reproduce_stresstest_server.py --model nemotron-3-nano-omni-q4km   # a running llama-server
python cascade_stresstest.py --model ... [--backend server] [--dataset stresspresso]
python measure_llm_stress.py / measure_llamacpp_stress.py ... ; python score_markup_stresstest.py
```

`--ple-cpu` keeps Gemma-4 E4B's per-layer embedding table (2.8B parameters, a lookup table) in system RAM so the
rest fits a 16 GB card; outputs are identical. Each script's docstring has the details and the exact settings
(sampling, prompt order, parsing). `reproduce_stresstest_qwen2audio.py` (Qwen2-Audio / StresSLM) is written but
was not run; those numbers are cited from the paper.

## Also here, not on the poster

An exploratory corpus of 91 YouTube/TikTok videos in which a speaker demonstrates contrastive stress
(`find_stress_videos.py`, `cut_clips.py`, `recut_clips.py`, `label_server.py`, `null_check_stress.py`). The
automatic clipper proved unreliable (in the first cut, 74% of clips started or ended mid-speech), so it was
dropped from the poster. Only URLs, manifests, detector outputs and review labels are included.

## Credits and licences

StressTest and StressPresso (slprl, CC BY-NC 4.0) and WhiStress (slp-rl; code MIT, weights CC BY-NC 4.0): Yosha,
Maimon, Adi, 2025. Files here that quote those datasets' transcripts or labels (`stress_search/stress*/manifest.csv`,
the per-sample outputs) carry the same non-commercial terms. Wavelet Prosody Toolkit: Suni et al., 2017. Praat:
Boersma and Weenink, via parselmouth. Gemma-4: Google. Nemotron 3 Nano Omni: NVIDIA; GGUF by ggml-org.
