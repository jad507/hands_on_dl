r"""
Portable path resolution for the hands_on_dl pipeline.

Every path in this project used to be an absolute Windows literal, which meant
nothing ran anywhere except one machine. This module replaces those literals
with two rules:

  1. Data lives inside the repository, so it is found relative to this file.
     No configuration needed; the scripts run wherever the repo is checked out.

  2. Model weights do NOT live in the repository (they are tens of gigabytes and
     git-ignored), so their location is machine-specific and must come from the
     HODL_MODELS_ROOT environment variable. There is deliberately no default:
     a wrong default would silently point at an empty directory and the failure
     would surface as "model not found" halfway through a run.

Every derived path can be overridden by an environment variable, which is what
makes a SLURM job on Roar (where the repo is read-only and scratch is elsewhere)
possible without editing code.

Environment variables, all optional except HODL_MODELS_ROOT:

    HODL_MODELS_ROOT    where GGUF / safetensors weights live   [REQUIRED]
                        Windows example: D:\LLM
                        Linux example:   /home/you/models
    HODL_DOWNLOADS_DIR  overrides <repo>/downloads
    HODL_COMMENTS_DIR   overrides <downloads>/comments
    HODL_OUTPUTS_ROOT   overrides <downloads>/llm_outputs
    HODL_THEMES_MD      overrides <downloads>/data_center_comment_themes.md
    HODL_PROMPTS_DIR    overrides <repo>/prompts
"""

from __future__ import annotations

import os
from pathlib import Path

# Derived, not declared: this file sits in the repository root, so the root is
# its parent. Using resolve() means symlinked checkouts still work.
REPO_ROOT: Path = Path(__file__).resolve().parent


def _env_path(var: str, default: Path) -> Path:
    """Return the path in `var` if set and non-empty, else `default`."""
    raw = os.environ.get(var, "").strip()
    return Path(raw).expanduser() if raw else default


DOWNLOADS_DIR: Path = _env_path("HODL_DOWNLOADS_DIR", REPO_ROOT / "downloads")
COMMENTS_DIR:  Path = _env_path("HODL_COMMENTS_DIR",  DOWNLOADS_DIR / "comments")
OUTPUTS_ROOT:  Path = _env_path("HODL_OUTPUTS_ROOT",  DOWNLOADS_DIR / "llm_outputs")
THEMES_MD_PATH: Path = _env_path("HODL_THEMES_MD",
                                 DOWNLOADS_DIR / "data_center_comment_themes.md")
PROMPTS_DIR:   Path = _env_path("HODL_PROMPTS_DIR",   REPO_ROOT / "prompts")

MODELS_CONFIG_PATH: Path = REPO_ROOT / "models.yaml"


class ModelsRootNotSet(RuntimeError):
    """HODL_MODELS_ROOT is required but was not set."""


def models_root(required: bool = True) -> Path | None:
    """
    Location of the model weights.

    Deliberately not a module-level constant: importing this module must not
    fail on a machine that has the repository but no weights (a laptop reading
    the code, CI, or `--list` before the drive is mounted). Callers that are
    about to load a model pass required=True and get a clear error; callers that
    only want to report status pass required=False and get None.
    """
    raw = os.environ.get("HODL_MODELS_ROOT", "").strip()
    if raw:
        return Path(raw).expanduser()
    if required:
        raise ModelsRootNotSet(
            "HODL_MODELS_ROOT is not set, so model weights cannot be located.\n"
            r"  Windows (PowerShell):  $env:HODL_MODELS_ROOT = 'D:\LLM'" "\n"
            "  Linux / macOS:         export HODL_MODELS_ROOT=$HOME/models\n"
            "Or add HODL_MODELS_ROOT to your .env file. See .env.example."
        )
    return None


def resolve_model_path(relative: str, required: bool = True) -> Path | None:
    """Join a registry-relative model path onto HODL_MODELS_ROOT.

    An absolute `relative` is honoured as-is, which keeps one-off experiments
    with a model outside the tree working without editing models.yaml.
    """
    p = Path(relative).expanduser()
    if p.is_absolute():
        return p
    root = models_root(required=required)
    return (root / p) if root is not None else None
