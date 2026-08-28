# Bringing the Windows `hands_on_dl` environment up to date

**Written:** 2026-08-28. **Audience:** whoever is sitting at the Windows machine — you, or a
Claude Code session running there.

**The reading I took of the request.** The instruction that produced this document was, in
full: *"another set of instructions that will help get a currently-working `hands_on_dl`
environment on Windows to incorporate all the new changes."* "All the new changes" is
ambiguous between two things — the repository's own drift since this machine was last set up,
and parity with the three-repository stack now being built on the Linux workstation. This
document covers both, in that order, because the first is a prerequisite for the second.

**The recommendation you probably did not want, stated up front.** The safest way to
"incorporate the new changes" into a working environment is largely **not to modify it.** The
single most valuable thing on this machine is an environment where seven local language models
successfully coded 78 meetings across two phases. The new work needs `transformers` 5.x, which
is a **major** version boundary from the 4.x line, and the `llms.ipynb` notebook's LoRA and
`trl` finetuning path is exactly the kind of code that a major `transformers` bump breaks. The
plan below therefore adds a **second, separate environment** and leaves the working one alone.
See [§4](#4-the-new-dependencies-in-a-second-environment) for the argument in full and
[§4.1](#41-if-you-would-rather-upgrade-in-place-anyway) for the in-place path if you disagree.

Acronyms, expanded here and at first use in each section: **ASR** = automatic speech
recognition. **LLM** = large language model. **VAD** = voice activity detection. **RTTM** =
Rich Transcription Time Marked, the plain-text speaker-timeline format diarization emits.
**VTT** = WebVTT, the subtitle format Concord imports. **GGUF** = the quantized single-file
model format `llama.cpp` loads. **LoRA** = Low-Rank Adaptation, a finetuning method that
trains small inserted matrices instead of the full weights. **ISLS** = International Society of
the Learning Sciences.

---

## 1. Step one is not an install. It is `git status`.

**Do this before anything else, and do not skip it because it looks like bookkeeping.**

The `hands_on_dl` checkout on the Linux workstation is clean at `ee37763`
("Ran the rest. will have to check logs later.", **2026-06-11**) and matches `origin/main`
exactly. It has not moved in two and a half months.

But the repository audit in `AITranscribe/docs/isls2027/05-hands-on-dl-upgrade-plan.md`,
written 2026-08-14, cites and quotes numbers out of files that **are not in that commit and
are not on the Linux machine.** Checked by name against `git ls-files`, all returning zero
matches:

| File the audit cites | In `origin/main`? |
|---|---|
| `compare_model_agreement.py` | **no** |
| `downloads/agreement_analysis/contested_blocks.csv` (2.2 MB) | **no** |
| `downloads/agreement_analysis/core5_contested_blocks.csv` (611 KB) | **no** |
| `core5_model_agreement_report.md` | **no** |
| `plans/roar_plan.md` | **no** |

The audit reports specific figures from those files — 3,263 blocks flagged by at least one
model, 785 unanimous (24.1%), 1,719 majority-agreed (52.7%), 2,478 contested (75.9%),
cross-family pairwise Jaccard 0.372–0.554, and the `qwen3.5-9b-q6` vs `qwen3.5-9b-q8` figure
of 0.840 that is a same-model-two-quantizations self-consistency measurement rather than an
agreement measurement. Numbers that specific are not invented. **The files exist. This is the
only machine they can be on.**

```powershell
cd D:\Users\jad507\PycharmProjects\hands_on_dl
git status
git log --oneline -5
git stash list
```

Three possible outcomes:

- **Uncommitted files appear.** Expected. Go to [§1.1](#11-committing-the-orphaned-analysis-work).
- **The tree is clean and `git log` shows commits after `ee37763`.** Then the work is committed
  but unpushed. `git push` and stop worrying.
- **The tree is clean and `HEAD` is `ee37763`.** Then the audit ran against a copy of the tree
  that existed somewhere else — an uploaded snapshot, most likely — and those five artifacts
  are genuinely gone. Say so out loud rather than assuming, because it changes the Linux plan:
  `compare_diarization_variants.py` then has to be written from scratch, and the phase-1
  agreement numbers have to be recomputed before they can be cited in a paper.

Estimated likelihood: ~90% the first, ~5% each for the others.

### 1.1 Committing the orphaned analysis work

Do this in **two commits**, not one, because they carry very different risk:

```powershell
cd D:\Users\jad507\PycharmProjects\hands_on_dl

# Commit 1 — code and small reports. Low risk, high value, needed everywhere.
git add compare_model_agreement.py core5_model_agreement_report.md plans/roar_plan.md
git status                      # read it before committing; add anything else that is code
git commit -m "Add phase-1 model agreement comparison, its report, and the Roar plan"

# Commit 2 — the derived CSVs. Decide deliberately; see below.
git add downloads/agreement_analysis/
git commit -m "Add agreement_analysis review queues (contested blocks, core5 subset)"

git push
```

**On committing the CSVs.** 2.8 MB of derived data is well within what git handles, and the
repository already tracks `downloads/llm_outputs/` — 2,616 tracked files including every
model's per-meeting JSON. So committing them is consistent with what this repository already
does, and it makes the review queues available on the Linux machine, which is where the
comparison work is going to happen. The argument against is that they are *derived* — regenerable
from `compare_model_agreement.py` plus the committed `llm_outputs/`. **Commit them.**
Reproducibility of a derivation is not the same as having the artifact, and an ISLS reviewer
asking "what exactly did the 2,478 contested blocks look like" is better answered from a file
than from a promise to re-run a script.

One thing to check before pushing, and the reason to read `git status` rather than
`git add -A`: `contested_blocks.csv` contains public-comment text from real, identifiable
private citizens speaking at council meetings. It is public record, and the repository already
tracks the same text inside `downloads/comments/`, so this changes nothing about the exposure.
But confirm the GitHub remote is private before pushing.

### 1.2 Then, and only then, does the Linux machine pull

```powershell
git push
```

```bash
# on the Linux workstation
cd /home/itsnotmyfault/src/hands_on_dl && git pull
```

Getting this order wrong is the single most likely way to waste a day on this project: the
upgrade plan's Step 1 ("mine the diarization pilot") is a close cousin of what
`compare_model_agreement.py` already does for phase 1, and writing it fresh on Linux while an
implementation sits unpushed here is duplicated work that then has to be reconciled.

---

## 2. Snapshot the working environment before touching anything

This environment is the only place the seven-model corpus has ever been produced. Capture what
it is, so that any later breakage is a diff rather than an archaeology project.

```powershell
cd D:\Users\jad507\PycharmProjects\hands_on_dl
conda activate .\.venv

python -c "import sys; print(sys.version)"
python -c "import torch; print(torch.__version__, torch.version.cuda, torch.cuda.is_available()); print(torch.cuda.get_device_name(0))"
python -c "import llama_cpp; print(llama_cpp.__version__, llama_cpp.llama_supports_gpu_offload())"

# The two records that matter. Date-stamped so a later one does not overwrite this one.
pip freeze          > env-snapshot-2026-08-28-pip.txt
conda list --explicit > env-snapshot-2026-08-28-conda.txt
```

Keep both files. `pip freeze` is the rollback: if an install goes wrong,
`pip install -r env-snapshot-2026-08-28-pip.txt` restores the exact set. `conda list --explicit`
additionally captures the conda-side packages with their channel URLs, which `pip freeze`
cannot see. Do not commit them — add a line to `.gitignore` for `env-snapshot-*` — because
they are machine-specific and will accumulate.

Record the `llama_supports_gpu_offload()` answer in `NOTEBOOK.md`. It is the one fact about
this environment that nothing else can reconstruct later, and the Linux machine has a
documented history of that exact call returning `False` on a CUDA-labelled build.

---

## 3. The gap that is actually in the repository

Small, and worth closing regardless of anything else.

### 3.1 `llama-cpp-python` is missing from `requirements.txt`

`from llama_cpp import Llama` appears in three files — `llm_classify_human_themes.py`,
`llm_extract_comments.py` and `chunk_token_histogram.py` — and `llama-cpp-python` is not in
`requirements.txt`. A clean `pip install -r requirements.txt` therefore produces an
environment that fails at import on the repository's most important script.

It cannot be added as a bare name, because the working install here is almost certainly a
platform-specific prebuilt CUDA wheel rather than a PyPI source build. Add it as a comment
recording what actually works, which is more useful than a name pip would resolve wrongly:

```
# llama-cpp-python is NOT installable from PyPI for this project: the source distribution
# compiles against whatever CUDA it finds, and a CPU-only build wearing a CUDA label is a
# documented failure mode that produces no error, only a ~100x slowdown. Install the
# prebuilt wheel matching this machine's CUDA and Python:
#   Windows : https://github.com/JamePeng/llama-cpp-python/releases  (cuXXX-win)
#   Linux   : https://github.com/JamePeng/llama-cpp-python/releases  (cuXXX-linux)
# Record the exact wheel URL you used in NOTEBOOK.md.
```

Find the version currently installed here and write it down before doing anything else:

```powershell
pip show llama-cpp-python
```

### 3.2 The audio pipeline is already satisfied here

`requirements.txt` lists `pyannote.audio>=4.0`, `faster-whisper` and `soundfile`, and
`downloads/pyannote_community-1_standard/`, `_exclusive/` and `whisper_large-v3/` contain
outputs for 78 meetings. So that half of the stack ran here successfully. Confirm rather than
reinstall:

```powershell
python audio_pipeline\setup_check.py
```

Expect a real `.m4a` count from `downloads\audio` — this is the only machine with the source
audio, since `downloads/audio` and `downloads/videos` are git-ignored.

---

## 4. The new dependencies, in a *second* environment

**ASR** = automatic speech recognition. This section adds `AITranscribe/transcribe2` — the
multi-engine, multi-policy transcription harness that is the ISLS deliverable's front end.

Its `doctor.py` enforces `transformers >= 5.10.1`, and the docstring gives the reason:
*"Gemma 4 audio needs >= 5.10.1, and an older version fails at inference time, not at import
time."* Gemma 4 support first landed in `transformers` 5.5.0; the audio path needs 5.10.1.

**Why a second environment rather than an upgrade.** If the working environment is on
`transformers` 4.x — likely, given a Python 3.10 conda env set up for `llms.ipynb` — then
`pip install "transformers>=5.10.1"` is a major-version jump underneath `peft` and `trl`,
which are the packages the LoRA finetuning section of that notebook depends on. A major
version bump in the library those two wrap is the textbook way to break a working notebook.
Weigh that against the benefit: a second environment costs perhaps 6 GB of disk and one extra
`conda activate`. That is a cheap insurance premium on the only machine that has ever produced
the corpus.

Check what you are actually starting from before deciding:

```powershell
python -c "import transformers, peft, trl; print(transformers.__version__, peft.__version__, trl.__version__)"
```

If `transformers` already reports 5.10.1 or newer, this whole concern evaporates and you can
install `transcribe2`'s remaining dependencies straight into the working environment.

```powershell
# Second environment. Python 3.10 keeps it consistent with the existing one; 3.11 or 3.12
# also work. Do NOT use 3.13+ on this machine unless you have checked that a matching
# llama-cpp-python wheel exists for it — you will not need llama_cpp in this env, but
# staying on a Python you already have wheels for avoids a whole class of surprise.
conda create -p D:\Users\jad507\PycharmProjects\.venv-transcribe python=3.10 -y
conda activate D:\Users\jad507\PycharmProjects\.venv-transcribe

# PyTorch first, so nothing later replaces it with the CPU-only default PyPI wheel.
# The RTX A2000 12 GB is Ampere (compute capability sm_86), so the CUDA 12.8 / Blackwell
# story that governs the Linux workstation does not apply here — cu126 or cu128 both carry
# sm_86 kernels. Read the exact current command off https://pytorch.org/get-started/locally/
# rather than trusting this line, which will age.
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu128

python -c "import torch; print(torch.__version__, torch.cuda.is_available(), torch.cuda.get_arch_list())"
# get_arch_list() must contain sm_86. torch.cuda.is_available() returning True does NOT
# prove your architecture was compiled in — a wheel without your sm_ level reports an
# available device and then fails at the first kernel launch.

pip install "transformers>=5.10.1" accelerate faster-whisper "pyannote.audio>=4.0" `
            soundfile praat-parselmouth yt-dlp numpy tqdm python-dotenv pytest
```

Then verify with the harness's own check. It exists precisely because these dependencies fail
late and confusingly rather than early and clearly:

```powershell
cd D:\Users\jad507\PycharmProjects\AITranscribe\transcribe2
python doctor.py
```

`whisper` (the `openai-whisper` package) reporting `WARN … not installed` is expected —
`engines.py` prefers `faster-whisper` and only falls back.

### 4.1 If you would rather upgrade in place anyway

Reasonable if you have decided the notebooks are teaching material you are done with. Make it
reversible and make it one step at a time:

```powershell
pip freeze > env-snapshot-before-transformers5.txt
pip install "transformers>=5.10.1"
python -c "import transformers, peft, trl; print('imports ok', transformers.__version__)"
jupyter nbconvert --to notebook --execute llms.ipynb --output /tmp/llms-check.ipynb
```

That last line is the actual test. If the notebook still executes end to end, the upgrade was
safe. If it does not:

```powershell
pip install -r env-snapshot-before-transformers5.txt
```

### 4.2 Clone the two new repositories

```powershell
cd D:\Users\jad507\PycharmProjects
git clone https://github.com/emollick/concord.git
# AITranscribe: substitute your own remote URL — it is a private repo, not a public one.
git clone <your-AITranscribe-remote> AITranscribe
```

`AITranscribe` was created 2026-07-27 and last committed 2026-08-14. It carries the eight ISLS
planning documents, the `transcribe2` harness, and the SSRI grant material. If it has no
remote yet, the Linux workstation is the only copy, and pushing it somewhere is worth doing
before anything else in this document.

---

## 5. Windows-specific traps

Five, in descending order of how much time they cost when hit.

### 5.1 HuggingFace symlinks — the warning is a symptom, not the problem

`.env.example` already carries `HF_HUB_DISABLE_SYMLINKS_WARNING=1`, with the comment *"enable
Developer Mode for the proper fix."* That comment is correct and worth acting on. Without
symlink support the HuggingFace cache **copies** blobs instead of linking them, so every model
that appears under two references occupies disk twice. Whisper `large-v3` is ~3 GB; the
pyannote pipeline pulls several components. Suppressing the warning hides the duplication
rather than fixing it.

Enable Developer Mode: **Settings → System → For developers → Developer Mode → On.** No reboot.
Once it is on, remove `HF_HUB_DISABLE_SYMLINKS_WARNING` from `.env` so a future regression is
visible again rather than silenced.

### 5.2 cuDNN discovery works differently on Windows, and `LD_LIBRARY_PATH` is not the answer

**cuDNN** = CUDA Deep Neural Network library. CTranslate2 — the engine under `faster-whisper`
— links cuBLAS and cuDNN 9 dynamically. On Linux the fix is `LD_LIBRARY_PATH`. Windows has no
such variable: DLLs resolve through `PATH` and, since Python 3.8,
through explicitly registered directories via `os.add_dll_directory()`.

Since `whisper_large-v3` output already exists here, cuDNN is evidently already resolving —
most likely because a CUDA Toolkit install put the DLLs somewhere on `PATH`. **Do not touch
it.** But if the second environment cannot find cuDNN while the first can, that asymmetry is
the cause, and the fix is to install the libraries into the new environment and register the
directory:

```powershell
pip install nvidia-cublas-cu12 "nvidia-cudnn-cu12==9.*"
python -c "import os, nvidia.cublas.lib, nvidia.cudnn.lib; print(os.path.dirname(nvidia.cublas.lib.__file__)); print(os.path.dirname(nvidia.cudnn.lib.__file__))"
# Add both printed directories to PATH for the session, or call os.add_dll_directory()
# on each before importing faster_whisper.
```

### 5.3 `MAX_PATH` and the corpus's long filenames

Windows caps paths at 260 characters unless long-path support is enabled. This corpus is
close: filenames like
`City Council Budget Hearing - November 18, 2025 [W6aSdOttjPk].json`, nested under
`downloads\llm_outputs\deepseek-r1-14b\phase2_theme_scores\`, sit inside a project directory
that is already 44 characters deep at `D:\Users\jad507\PycharmProjects\hands_on_dl\`. Adding
another level — a new output directory, a per-policy subdirectory for the transcription
experiment — can push past the limit, and the failure is a confusing `FileNotFoundError` on a
file you can see in Explorer.

```powershell
# As Administrator. Survives reboots; applies system-wide.
New-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\FileSystem" `
    -Name "LongPathsEnabled" -Value 1 -PropertyType DWORD -Force

# Git needs telling separately — it has its own limit independent of the OS setting.
git config --system core.longpaths true
```

### 5.4 Line endings will churn the diff if `core.autocrlf` is set

`hands_on_dl` has **no `.gitattributes`**. If `core.autocrlf=true` here and `input` or unset on
Linux, files will show as wholly modified on one machine after being touched on the other, and
the noise will bury real changes in exactly the files you most need to review — the Python
scripts being made portable in Step 2 of the upgrade plan.

```powershell
git config core.autocrlf        # what is it now?
```

The durable fix is a `.gitattributes` in the repository root, committed once, which makes the
policy travel with the repository instead of living in two machines' local configs:

```
* text=auto
*.py   text eol=lf
*.md   text eol=lf
*.json text eol=lf
*.ps1  text eol=crlf
*.bat  text eol=crlf
```

`.ps1` and `.bat` get CRLF deliberately — some Windows shells are unhappy with LF-only batch
files. `concord` already ships a `.gitattributes`; this repository should too.

### 5.5 `load_env.ps1` is more fragile than it looks

```powershell
Get-Content .env | Where-Object { $_ -and $_ -notmatch '^\s*#' } | ForEach-Object {
    $name, $value = $_ -split '=', 2
    Set-Item -Path "Env:$name" -Value $value
}
Start-Service ssh-agent
```

Three sharp edges, none of which announce themselves:

1. **It does not strip surrounding quotes.** `HF_TOKEN="hf_abc"` sets the variable to
   `"hf_abc"` *with the quotes*, and HuggingFace then returns 401 for a token that looks
   correct in every printout. Keep `.env` values unquoted.
2. **It does not trim whitespace.** A trailing space after a value becomes part of the value.
3. **`Start-Service ssh-agent` needs Administrator** and will throw in a normal shell,
   aborting the rest of the pipeline if `$ErrorActionPreference` is `Stop`.

`load_personal.ps1` is the better implementation — it uses a regex with explicit `.Trim()`
calls. Worth making `load_env.ps1` match it, if you are editing anyway.

---

## 6. What should and should not be identical across the two machines

This is where the methodology and the sysadmin work touch, and it is easy to get wrong in a
way that only surfaces when a reviewer asks.

### 6.1 The two GPUs are different architectures, and float16 is not bit-identical across them

The RTX A2000 12 GB is Ampere (compute capability `sm_86`); the Linux workstation's RTX 5070 Ti
is Blackwell (`sm_120`). Floating-point reductions are not guaranteed bit-identical across GPU
architectures, CUDA versions, or library versions — kernel selection, tile sizes and reduction
order all differ.

**The practical consequence:** re-running `transcribe.py` on the same `.m4a` on the Linux
machine will not necessarily reproduce the existing `downloads/whisper_large-v3/` output
byte-for-byte. Most segments will match; some will differ by a word. For an ordinary
engineering project that is a curiosity. For a study whose entire claim is *"here is how much
the downstream codes move when the transcript changes"*, an uncontrolled machine-to-machine
transcript delta sits in the same measurement channel as the effect being measured.

Three things follow, and they are cheap:

1. **Do the actual experimental runs on one machine.** Whichever one. Not half on each.
2. **Record `(hostname, GPU, CUDA version, ctranslate2 version, faster-whisper version,
   compute_type, beam_size, best_of)` in every output file**, alongside the policy name and
   prompt hash that `transcribe2` already records. `audio_pipeline/transcribe.py` currently
   records none of it.
3. **If you do end up transcribing on both, measure the delta first.** Run one meeting on both
   machines with identical settings and diff the output. If it is zero, say so in the paper and
   the confound is closed. If it is not zero, you have quantified your instrument's noise floor
   — which is a genuinely useful number to have, because the effect you are looking for has to
   clear it.

Confidence that a nonzero delta exists: **~70%.** Confidence that it is small relative to the
policy effect: ~85%. Neither is measured — item 3 is how you replace both with a number.

`compute_type` deserves its own note. `audio_pipeline/transcribe.py` uses
`compute_type="float16"`, and it should stay that way on both machines. `int8` works on Ampere
but had a real incompatibility with Blackwell's INT8 tensor cores — fixed upstream in
CTranslate2 4.7.0 (PR #1982, "Enable multiple of 16 padding for INT8 Tensor Cores"), but
irrelevant here because on a 12 GB or 16 GB card `large-v3` in float16 fits comfortably and
int8 buys nothing worth a cross-machine inconsistency.

### 6.2 Model paths must stop being machine-specific

`llm_classify_human_themes.py` hardcodes `D:\Users\jad507\PycharmProjects\hands_on_dl\...` for
`COMMENTS_DIR`, `THEMES_MD_PATH` and `OUTPUTS_ROOT`, and `D:\LLM\...` for all seven GGUF paths.
`llm_extract_comments.py` and `chunk_token_histogram.py` do the same. Nothing runs anywhere
else.

This is Step 2 of the upgrade plan, scoped there at two hours, and it unblocks the Linux
machine, the Roar cluster (SLURM — Simple Linux Utility for Resource Management, the batch
scheduler — cannot see `D:\`), the API path, and any collaborator.

**Do it here, not on Linux.** Two reasons. You can test the refactor immediately against a
working environment with the models actually present, which is the only way to know the paths
resolve. And doing it in one place avoids a merge conflict in the file that most needs to stay
identical across machines. The shape:

```python
from pathlib import Path
import os

# Repository root, derived rather than declared, so the script runs wherever it is checked out.
REPO_ROOT    = Path(__file__).resolve().parent
COMMENTS_DIR = Path(os.environ.get("HODL_COMMENTS_DIR", REPO_ROOT / "downloads" / "comments"))
OUTPUTS_ROOT = Path(os.environ.get("HODL_OUTPUTS_ROOT", REPO_ROOT / "downloads" / "llm_outputs"))
# Model weights are large and machine-specific, so this one is env-var-first with no default
# that could silently point at the wrong place. Windows: D:\LLM. Linux: ~/models.
MODELS_ROOT  = Path(os.environ["HODL_MODELS_ROOT"])
```

Then the registry holds a filename relative to `MODELS_ROOT` rather than an absolute path, and
`HODL_MODELS_ROOT` goes in each machine's `.env`. The plan's other three sub-steps —
`config.yaml`, `--dry-run` / `--limit N`, and prompts in versioned files with the prompt hash
written into every output — are the same edit session.

The prompt-versioning one is the highest-leverage item in the plan per unit of effort, for a
reason worth stating without reference to the conversation that produced it: the prompts
currently live in Python string literals, so given an output file you cannot determine which
prompt produced it. Fixing that is ordinary engineering hygiene that happens to satisfy a
methodological disclosure requirement the ISLS community actively rewards — the CSCL 2024
paper *"Making Human-AI Contributions Transparent in Qualitative Coding"* by Lopez-Fierro &
Nguyen [won the Naomi Miyake Outstanding Student Paper Award](https://repository.isls.org/handle/1/10537)
and asks researchers to disclose their prompts.

### 6.3 The source audio lives only here

`downloads/audio/` and `downloads/videos/` are git-ignored, so the 78 `.m4a` recordings exist
only on this machine. The Linux workstation does not need them for upgrade-plan Steps 0–3, but
does for Step 5 (re-transcribing under N policies).

The corpus is reconstructible there with `yt-dlp` from `meetingurls.txt`,
`council_video_list.txt` and the committed cookies file — but a video removed or re-uploaded
since the original download would silently change the corpus. If byte-identical audio matters
for the claims (and for a study about transcript variation it plausibly does), copy rather than
re-download. Either way, diff the resulting file list against `downloads/downloaded.txt` and
treat a mismatch as a finding for `NOTEBOOK.md`, not a nuisance.

---

## 7. Optional: Concord on Windows

Concord is pure JavaScript with no build step and five runtime dependencies. Its `package.json`
requires Node ≥ 20.10 and it ships a Windows launcher.

```powershell
node --version                       # need >= 20.10; https://nodejs.org/ if absent
cd D:\Users\jad507\PycharmProjects\concord
.\start.bat                          # installs dependencies on first run, opens the browser
```

Then the keyless walkthrough: create a project, drop `demo\techcorp-exit-survey.csv` (2,500
synthetic exit-survey responses with six planted themes and a seeded oracle), set the
Director's provider to **mock** — a deterministic local fake model that emulates a
~90%-accurate judge, which exists so that calibration and correction, which need a *fallible*
judge, work end to end before any API key is pasted.

Run the release gate before trusting any number it produces:

```powershell
node --test tests\e2e\pipeline.test.js
```

Concord matters here for a reason beyond convenience. The upgrade plan's Step 4 — human labels
— is the real bottleneck, because nothing downstream of "how well do models agree with humans"
can proceed without a human-coded dataset, and the repository contains none. Concord's
Calibration Studio is built for exactly that job: restricted listener sessions, blind
double-coding, adjudication, then a frozen certificate. Doing your gold coding inside it rather
than in a spreadsheet gets you the provenance for free. That step needs no GPU and no models,
so it can proceed on this machine in parallel with everything else.

---

## 8. Order of operations

| # | Do | Where | Blocks |
|---|---|---|---|
| 1 | `git status`; commit and push the orphaned analysis work | Windows | **Everything on the Linux machine** |
| 2 | Snapshot the environment (`pip freeze`, `conda list --explicit`) | Windows | Any safe rollback later |
| 3 | Record `llama_supports_gpu_offload()` and the exact wheel version | Windows | Reproducing this environment ever again |
| 4 | Enable Developer Mode and long paths | Windows | §5.1, §5.3 |
| 5 | Add `.gitattributes`; commit | Windows | Readable diffs across machines |
| 6 | Do Step 2 of the upgrade plan (paths, config, prompt versioning) here | Windows | Linux, Roar, the API path, collaborators |
| 7 | Second environment; clone AITranscribe and concord; `doctor.py` | Windows | `transcribe2` on this machine |
| 8 | Concord + the demo walkthrough | either | Step 4, human labels |

Steps 1–3 are about an hour. Step 6 is the two-hour item that unblocks the most. Step 7 is
genuinely optional if the Linux workstation is going to be the transcription machine — and
[§6.1](#61-the-two-gpus-are-different-architectures-and-float16-is-not-bit-identical-across-them)
is an argument that it should be exactly one of them.

---

## 9. Confidence

| Claim | Confidence | Basis |
|---|---|---|
| `origin/main` lacks `compare_model_agreement.py` and `agreement_analysis/` | **~99%** | Checked by name against `git ls-files` on the Linux clone, 2026-08-28 |
| Those artifacts are on this Windows machine | ~90% | The `D:\` paths and the audit's specific figures. Not observed — [§1](#1-step-one-is-not-an-install-it-is-git-status) is the check |
| `llama_cpp` missing from `requirements.txt` | **~99%** | Read both files |
| A second environment is safer than upgrading `transformers` in place | ~80% | Major-version boundary under `peft`/`trl`. The starting version here is unknown — check it |
| The RTX A2000 12 GB is Ampere, `sm_86` | ~92% | GA106 die. The code comment `# RTX A2000 12 GB VRAM` fixes the card; the architecture is inference |
| Cross-architecture float16 transcripts differ somewhere | ~70% | General property of GPU floating-point reductions. Not measured — [§6.1](#61-the-two-gpus-are-different-architectures-and-float16-is-not-bit-identical-across-them) item 3 is how to replace this with a number |
| `MAX_PATH` is a live risk for this corpus | ~65% | Filenames are long and nesting is deep, but the current tree evidently fits. Adding one directory level is what changes it |
| Enabling Developer Mode fixes HF cache duplication | ~90% | Documented HuggingFace behaviour; the `.env.example` comment already says so |
| `load_env.ps1` does not strip quotes or trim whitespace | **~99%** | Read the script |
| Node ≥ 20.10 satisfies Concord | **~99%** | `package.json` `engines` field |

---

## 10. Sources

Read directly from the repositories:

- `hands_on_dl`: `README.md`, `requirements.txt`, `.env.example`, `.gitignore`,
  `load_env.ps1`, `load_personal.ps1`, `audio_pipeline/setup_check.py`,
  `plans/audio_pipeline_setup.md`, `llm_classify_human_themes.py` (model registry and module-scope paths)
- `AITranscribe`: `docs/isls2027/00-INDEX.md`, `docs/isls2027/05-hands-on-dl-upgrade-plan.md`,
  `transcribe2/README.md`, `transcribe2/doctor.py`, `transcribe2/run.py`
- `concord`: `README.md`, `package.json`

External, fetched 2026-08-28:

- [SYSTRAN/faster-whisper](https://github.com/SYSTRAN/faster-whisper) — cuDNN 9, `compute_type` values
- [OpenNMT/CTranslate2 releases](https://github.com/OpenNMT/CTranslate2/releases) — the Blackwell INT8 history (4.6.2, 4.7.0)
- [pyannote-audio releases](https://github.com/pyannote/pyannote-audio/releases) — 4.x breaking changes · [speaker-diarization-community-1](https://huggingface.co/pyannote/speaker-diarization-community-1)
- [transformers v5.5.0](https://github.com/huggingface/transformers/releases/tag/v5.5.0) — the Gemma 4 support floor
- [JamePeng/llama-cpp-python releases](https://github.com/JamePeng/llama-cpp-python/releases) — prebuilt CUDA wheels, Windows and Linux
- [PyTorch install selector](https://pytorch.org/get-started/locally/) — read the current command there rather than from this document
- [Lopez-Fierro & Nguyen, CSCL 2024](https://repository.isls.org/handle/1/10537)
- [emollick/concord](https://github.com/emollick/concord)

**Companion document:** `Shiro/transcription-stack-on-shiro.md` on the Linux workstation —
the same stack, from the other side.
