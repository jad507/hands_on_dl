"""
Run provenance for the LLM classification pipeline.

Two problems this solves, both raised by plans/windows_environment_upgrade.md:

  1. Prompts used to live in Python string literals, so given an output file you
     could not determine which prompt produced it. Now every output records the
     SHA-256 of the prompt file and of the fully rendered system string.

  2. Outputs recorded nothing about the machine or library versions that made
     them. Float16 reductions are not bit-identical across GPU architectures, so
     a corpus produced half on an Ampere card and half on Blackwell has an
     uncontrolled difference sitting in the same measurement channel as the
     effect being studied. Recording the toolchain makes that visible in the
     data rather than in someone's memory.

The `provenance` block is additive: existing outputs without it still load, and
the resume/redo logic does not depend on it.
"""

from __future__ import annotations

import hashlib
import os
import platform
import socket
import subprocess
from datetime import datetime, timezone
from pathlib import Path


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def sha256_file(path: str | Path) -> str | None:
    try:
        h = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(1 << 20), b""):
                h.update(chunk)
        return h.hexdigest()
    except OSError:
        return None


def _pkg_version(name: str) -> str | None:
    try:
        from importlib.metadata import version
        return version(name)
    except Exception:
        return None


def _gpu_name() -> str | None:
    """Ask nvidia-smi rather than torch: this pipeline runs under llama_cpp and
    importing torch just to read a device name costs seconds and VRAM."""
    try:
        r = subprocess.run(
            ["nvidia-smi", "--query-gpu=name", "--format=csv,noheader"],
            capture_output=True, text=True, timeout=5,
        )
        if r.returncode == 0:
            return r.stdout.strip().splitlines()[0].strip()
    except Exception:
        pass
    return None


def _model_fingerprint(model_path: Path, hash_weights: bool) -> dict:
    """Identify the weights file. Hashing a 10 GB GGUF takes ~30-60 s, so it is
    opt-in via HODL_HASH_WEIGHTS=1; size plus mtime is enough to catch the
    ordinary mistake of pointing at a different quantisation."""
    info: dict = {"path_relative": str(model_path)}
    try:
        st = model_path.stat()
        info["size_bytes"] = st.st_size
        info["mtime_utc"] = datetime.fromtimestamp(
            st.st_mtime, tz=timezone.utc).isoformat()
    except OSError:
        info["size_bytes"] = None
        info["mtime_utc"] = None
    if hash_weights:
        info["sha256"] = sha256_file(model_path)
    return info


def build_provenance(
    *,
    model_name: str,
    model_cfg: dict,
    model_path: Path,
    prompt_file: Path,
    rendered_system: str,
    settings: dict,
    extra_files: dict[str, Path] | None = None,
) -> dict:
    """Assemble the provenance block written into every output JSON.

    `rendered_system` is the exact system string handed to the model, so its
    hash covers the /no_think prefix and (for phase 2) the substituted theme
    definitions -- things the prompt file's own hash cannot capture.
    """
    prompt_text = ""
    try:
        prompt_text = prompt_file.read_text(encoding="utf-8")
    except OSError:
        pass

    files = {
        "prompt": {
            "file": prompt_file.name,
            "sha256": sha256_text(prompt_text) if prompt_text else None,
        },
        "rendered_system_sha256": sha256_text(rendered_system),
    }
    for label, path in (extra_files or {}).items():
        try:
            files[label] = {
                "file": Path(path).name,
                "sha256": sha256_text(Path(path).read_text(encoding="utf-8")),
            }
        except OSError:
            files[label] = {"file": Path(path).name, "sha256": None}

    return {
        "generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "model": {
            "name": model_name,
            "backend": model_cfg.get("backend", "llama_cpp"),
            "n_ctx": model_cfg.get("n_ctx"),
            "n_gpu_layers": model_cfg.get("n_gpu_layers"),
            "no_think": model_cfg.get("no_think"),
            "strip_think": model_cfg.get("strip_think"),
            **_model_fingerprint(
                model_path,
                hash_weights=os.environ.get("HODL_HASH_WEIGHTS", "") == "1",
            ),
        },
        "sampling": {
            "temperature": settings.get("temperature"),
            "p1_chunk_size": settings.get("p1_chunk_size"),
            "p2_max_words": settings.get("p2_max_words"),
            "p1_max_tokens": settings.get("p1_max_tokens"),
            "p1_retry_max_tokens": settings.get("p1_retry_max_tokens"),
            "p2_max_tokens": settings.get("p2_max_tokens"),
        },
        "inputs": files,
        "runtime": {
            "hostname": socket.gethostname(),
            "platform": platform.platform(),
            "python": platform.python_version(),
            "llama_cpp_python": _pkg_version("llama_cpp_python"),
            "gpu": _gpu_name(),
        },
    }
