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