# Hands-On Deep Learning

## Session 1: Basics of Deep Learning and PyTorch

This session covers the basics of deep learning and PyTorch. Refer to the [introduction.ipynb](introduction.ipynb) notebook for the content.

## Contents

- [introduction.ipynb](introduction.ipynb) <a target="_blank" href="https://colab.research.google.com/github/arshandalili/hands_on_dl/blob/main/introduction.ipynb">
  <img src="https://colab.research.google.com/assets/colab-badge.svg" alt="Open In Colab"/>
</a>  - Covers:
  - PyTorch tensors, autograd, model definition and the training loop
  - Training logistic regression (softmax) with gradient descent on MNIST
  - Overfitting and regularization (weight decay, early stopping)

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