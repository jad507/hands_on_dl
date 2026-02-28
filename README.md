# Hands-On Deep Learning

Session 1: Basics of Deep Learning, Modern Paradigms and PyTorch.

This repository contains a Jupyter notebook that introduces PyTorch fundamentals, logistic regression with gradient descent on MNIST, and overfitting and regularization.

## Contents

- **`introduction.ipynb`** — Covers:
  - PyTorch tensors, autograd, model definition with `nn.Module`, and the training loop
  - Training logistic regression (softmax) with gradient descent on MNIST
  - Overfitting and regularization (weight decay, early stopping)

## Setup

### 1. Clone the repository

```bash
git clone https://github.com/YOUR_USERNAME/hands_on_dl.git
cd hands_on_dl
```

### 2. Create and activate the conda environment

Using the existing `.venv` conda environment in this repo:

```bash
conda activate ./.venv
```

If you need to create a new conda environment instead:

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

## Requirements

- Python 3.10+
- See `requirements.txt` for package versions (PyTorch, torchvision, matplotlib, numpy).

## License

MIT (or specify as needed.)
