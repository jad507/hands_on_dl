# Hands-On Deep Learning

## Session 1: Basics of Deep Learning and PyTorch

This session covers the basics of deep learning and PyTorch. Refer to the [introduction.ipynb](introduction.ipynb) notebook for the content.

## Session 2: Deep Learning for Images

This session covers deep learning techniques for image data. Refer to the [images.ipynb](images.ipynb) notebook for the content.

## Session 3: Large Language Models

This session covers practical workflows for small large language models, including pretrained evaluation, lightweight finetuning, and an OpenAI API example. Refer to the [llms.ipynb](llms.ipynb) notebook for the content.

## Contents

- [introduction.ipynb](introduction.ipynb) <a target="_blank" href="https://colab.research.google.com/github/arshandalili/hands_on_dl/blob/main/introduction.ipynb">
  <img src="https://colab.research.google.com/assets/colab-badge.svg" alt="Open In Colab"/>
</a>  - Covers:
  - PyTorch tensors, autograd, model definition and the training loop
  - Training logistic regression (softmax) with gradient descent on MNIST
  - Overfitting and regularization (weight decay, early stopping)

- [images.ipynb](images.ipynb) <a target="_blank" href="https://colab.research.google.com/github/arshandalili/hands_on_dl/blob/main/images.ipynb">
  <img src="https://colab.research.google.com/assets/colab-badge.svg" alt="Open In Colab"/>
</a>  - Covers:
  - Convolutional neural networks (CNNs) for image classification
  - Data augmentation and regularization for images
  - Transfer learning and fine-tuning pretrained vision models
  - Grad-CAM for visualizing image classification
  - Object detection with YOLO

- [llms.ipynb](llms.ipynb) <a target="_blank" href="https://colab.research.google.com/github/arshandalili/hands_on_dl/blob/main/llms.ipynb">
  <img src="https://colab.research.google.com/assets/colab-badge.svg" alt="Open In Colab"/>
</a>  - Covers:
  - Loading a small chat model and tokenizer from Hugging Face
  - Loading and reframing a dataset for instruction-style sentiment classification
  - Evaluating pretrained model performance on a held-out split
  - Finetuning with LoRA and comparing before/after accuracy
  - Making a sample OpenAI API call and printing the returned result

## Setup (if you want to run the notebook locally)

### 1. Clone the repository

```bash
git clone https://github.com/arshandalili/hands_on_dl.git
cd hands_on_dl
```

### 2. Create and activate the conda environment

Create a new conda environment instead:

```bash
conda create -p .venv python=3.10 -y
conda activate ./.venv
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Run the notebook

```bash
jupyter notebook introduction.ipynb
```

Or with JupyterLab:

```bash
pip install jupyterlab
jupyter lab introduction.ipynb
```
---

## Running the Lancaster council pipeline

The notebooks above are the original teaching material. This repository also
carries a research pipeline that transcribes Lancaster, PA city council meetings
and has seven local language models code the public comments in them.

### Configuration

Every path the pipeline uses is resolved relative to this repository, except the
model weights, which are too large to track in git and therefore live somewhere
machine-specific. Point `HODL_MODELS_ROOT` at that directory:

```powershell
# Windows
$env:HODL_MODELS_ROOT = 'D:\LLM'
```

```bash
# Linux / macOS
export HODL_MODELS_ROOT=$HOME/models
```

Or put it in `.env` (copy `.env.example`) and run `.\load_env.ps1`. `paths.py`
documents the full set of optional overrides, which matter on a cluster where the
checkout is read-only and outputs must go to scratch.

`llama-cpp-python` is required but is deliberately not installable from
`requirements.txt`; see the note at the bottom of that file.

### Classifying comments against human-identified themes

```bash
python llm_classify_human_themes.py --list                     # registry + which weights are present
python llm_classify_human_themes.py --model qwen3.5-9b-q6 --dry-run
python llm_classify_human_themes.py --model qwen3.5-9b-q6 --limit 2
python llm_classify_human_themes.py --model qwen3.5-9b-q6      # full run, both phases
```

`--dry-run` resolves every path, validates the config and prompts, and reports
what would happen without loading the model or writing anything. `--limit N`
caps how many meetings are processed, which is how to smoke-test a config change
without committing to a multi-hour run. Both are additive: neither changes what a
full run does.

Runs are resumable. A meeting whose output already exists and recorded no errors
is skipped; one that recorded errors is redone.

### Where the configuration lives

| What | Where | Why not in the Python |
|---|---|---|
| Model registry, sampling settings | `models.yaml` | Versioned as data; editable without touching code |
| System prompts | `prompts/*.txt` | So an output can be traced to the prompt that made it |
| Machine-specific paths | environment variables | So the same code runs on Windows, Linux and a cluster |

Every output JSON carries a `provenance` block recording the SHA-256 of the
prompt file and of the fully rendered system string, the model file's size and
mtime, the sampling settings, and the host, GPU and `llama-cpp-python` version
that produced it. That block is additive -- older outputs without it still load.
