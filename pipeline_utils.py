"""Shared timing utilities for pipeline scripts."""

import os
import platform
import subprocess
import time
from datetime import datetime


def fmt_elapsed(seconds: float) -> str:
    m, s = divmod(int(seconds), 60)
    h, m = divmod(m, 60)
    if h:
        return f"{h}h {m}m {s}s"
    if m:
        return f"{m}m {s}s"
    return f"{s}s"


def now_str() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def gpu_info() -> dict:
    """Best-effort GPU name/VRAM/driver via nvidia-smi. Empty dict if unavailable."""
    try:
        p = subprocess.run(
            ["nvidia-smi", "--query-gpu=name,memory.total,driver_version",
             "--format=csv,noheader"],
            capture_output=True, text=True, timeout=10,
            encoding="utf-8", errors="replace")
    except (OSError, subprocess.TimeoutExpired):
        return {}
    if p.returncode != 0 or not p.stdout.strip():
        return {}
    parts = [s.strip() for s in p.stdout.strip().splitlines()[0].split(",")]
    if len(parts) != 3:
        return {}
    name, vram, driver = parts
    return {"gpu_name": name, "gpu_vram": vram, "gpu_driver": driver}


def hardware_info() -> dict:
    """Machine identity, so a timing number can be compared across machines.

    This project runs the same scripts on at least two machines with different
    GPUs (a work desktop's RTX A2000 12GB, a home machine's RTX 5070 Ti 16GB),
    and an elapsed-time number is meaningless without knowing which one produced
    it. nvidia-smi is shelled out to rather than torch, so this works even in
    scripts with no torch dependency of their own.
    """
    info = {
        "host": platform.node(),
        "os": platform.platform(),
        "python": platform.python_version(),
        "cpu": platform.processor() or platform.machine(),
        "cpu_count": os.cpu_count(),
    }
    info.update(gpu_info())
    try:
        import torch
        info["torch"] = torch.__version__
        info["cuda_available"] = torch.cuda.is_available()
    except ImportError:
        pass
    return info


def hardware_summary() -> str:
    """One-line form of hardware_info(), for a log header."""
    hw = hardware_info()
    gpu = hw.get("gpu_name", "no GPU detected")
    return f"{hw.get('host')} | {gpu} | torch {hw.get('torch', 'n/a')}"