r"""
Reading and writing faster-whisper output, with provenance and both schemas.

Why this module exists
----------------------
`audio_pipeline/transcribe.py` wrote a bare JSON list of segments and recorded
nothing else: not the model, not the decoding parameters, not the machine. For
an ordinary engineering project that is fine. For this one it is a hole in the
instrument.

`plans/windows_environment_upgrade.md` section 6.1 makes the argument. Floating
point reductions are not bit-identical across GPU architectures, CUDA versions
or library versions, so re-transcribing the same audio on a different machine --
or on this one after a driver update -- will not necessarily reproduce the
existing output. The ISLS study's entire claim is about how far downstream codes
move when the transcript changes. An uncontrolled transcript delta sits in the
same measurement channel as the effect being measured, and without provenance
you cannot tell one from the other after the fact.

`plans/windows_environment_upgrade_status.md` section 3 then found that exact
problem one layer up, in the LLM stage, on one machine across time. Provenance
was added there. This closes the same gap for the ASR stage, which section 8
item 5 lists as required before any transcription run.

Two schemas
-----------
The 78 files already in `downloads/whisper_large-v3/` are bare lists. Rewriting
them is not possible -- the information was never captured -- and re-transcribing
to get it would destroy the very thing being preserved. So:

    legacy  [ {start, end, text}, ... ]
    current { "provenance": {...}, "segments": [ {start, end, text}, ... ] }

`load_segments()` accepts both, `load_provenance()` returns None for legacy, and
`write_transcript()` always writes the current shape. Nothing has to be migrated
and nothing silently loses data.
"""

from __future__ import annotations

import json
import platform
import socket
import subprocess
from datetime import datetime, timezone
from pathlib import Path

SEGMENTS_KEY = "segments"
PROVENANCE_KEY = "provenance"


# --------------------------------------------------------------------------
# Reading
# --------------------------------------------------------------------------

def load_segments(path: str | Path) -> list[dict]:
    """Segments from either schema.

    A bare list is the legacy shape and is returned as-is. A dict must carry
    `segments`; anything else raises rather than returning [] silently, because
    an empty transcript that should not be empty is the kind of failure that
    propagates all the way into a result table before anyone notices.
    """
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        if SEGMENTS_KEY in data:
            return data[SEGMENTS_KEY]
        raise ValueError(
            f"{path}: dict transcript without a '{SEGMENTS_KEY}' key "
            f"(found {sorted(data)})")
    raise ValueError(f"{path}: unrecognised transcript type {type(data).__name__}")


def load_provenance(path: str | Path) -> dict | None:
    """Provenance block, or None for a legacy file that never had one."""
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if isinstance(data, dict):
        return data.get(PROVENANCE_KEY)
    return None


def is_legacy(path: str | Path) -> bool:
    """True for a transcript written before provenance was recorded."""
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return isinstance(data, list)


# --------------------------------------------------------------------------
# Provenance
# --------------------------------------------------------------------------

def _pkg_version(name: str) -> str | None:
    try:
        from importlib.metadata import version
        return version(name)
    except Exception:
        return None


def _gpu_info() -> dict:
    """GPU name and driver, read from nvidia-smi.

    Deliberately not via torch: transcribe.py already imports torch, but this
    module is also used by readers that should not pay for a CUDA context just
    to inspect a file.
    """
    info: dict = {"name": None, "driver_version": None}
    try:
        r = subprocess.run(
            ["nvidia-smi", "--query-gpu=name,driver_version",
             "--format=csv,noheader"],
            capture_output=True, text=True, timeout=5)
        if r.returncode == 0 and r.stdout.strip():
            parts = [p.strip() for p in r.stdout.strip().splitlines()[0].split(",")]
            if len(parts) >= 2:
                info["name"], info["driver_version"] = parts[0], parts[1]
    except Exception:
        pass
    return info


def _cuda_info() -> dict:
    info: dict = {"torch_cuda": None, "device_capability": None}
    try:
        import torch
        info["torch_cuda"] = torch.version.cuda
        if torch.cuda.is_available():
            major, minor = torch.cuda.get_device_capability(0)
            info["device_capability"] = f"sm_{major}{minor}"
    except Exception:
        pass
    return info


def build_provenance(*, model_name: str, compute_type: str,
                     decode_params: dict, audio_path: str | Path,
                     audio_info: dict | None = None) -> dict:
    """The provenance block written into every new transcript.

    The tuple named in `windows_environment_upgrade.md` section 6.1 --
    hostname, GPU, CUDA version, ctranslate2 version, faster-whisper version,
    compute_type, beam_size, best_of -- plus the audio file's size and mtime,
    which is what catches the ordinary mistake of re-transcribing a file that
    was itself re-downloaded.
    """
    p = Path(audio_path)
    audio: dict = {"name": p.name}
    try:
        st = p.stat()
        audio["size_bytes"] = st.st_size
        audio["mtime_utc"] = datetime.fromtimestamp(
            st.st_mtime, tz=timezone.utc).isoformat()
    except OSError:
        audio["size_bytes"] = None
        audio["mtime_utc"] = None
    if audio_info:
        audio.update(audio_info)

    return {
        "generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "asr": {
            "engine": "faster-whisper",
            "model": model_name,
            "compute_type": compute_type,
            **decode_params,
        },
        "audio": audio,
        "runtime": {
            "hostname": socket.gethostname(),
            "platform": platform.platform(),
            "python": platform.python_version(),
            "faster_whisper": _pkg_version("faster-whisper"),
            "ctranslate2": _pkg_version("ctranslate2"),
            "torch": _pkg_version("torch"),
            **_cuda_info(),
            "gpu": _gpu_info(),
        },
    }


# --------------------------------------------------------------------------
# Writing
# --------------------------------------------------------------------------

def write_transcript(path: str | Path, segments: list[dict],
                     provenance: dict) -> None:
    """Write the current schema."""
    Path(path).write_text(
        json.dumps({PROVENANCE_KEY: provenance, SEGMENTS_KEY: segments},
                   indent=2, ensure_ascii=False),
        encoding="utf-8")


def describe(path: str | Path) -> str:
    """One-line human summary, for spot-checking a directory of transcripts."""
    prov = load_provenance(path)
    n = len(load_segments(path))
    if prov is None:
        return f"{Path(path).name}: {n} segments, LEGACY (no provenance)"
    asr = prov.get("asr", {})
    rt = prov.get("runtime", {})
    return (f"{Path(path).name}: {n} segments, {asr.get('model')} "
            f"{asr.get('compute_type')} beam={asr.get('beam_size')} "
            f"on {rt.get('hostname')} / {(rt.get('gpu') or {}).get('name')} "
            f"ct2={rt.get('ctranslate2')}")
