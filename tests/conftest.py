"""
Make the repository root importable from the test suite.

The analysis modules live in the repository root rather than in a package, so
`import agreement` only works if the root is on sys.path. pytest puts the
rootdir there when invoked as `python -m pytest`, but not when invoked as a
bare `pytest`, and the difference is an ImportError that looks like a missing
dependency. This removes the distinction.
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# `transcribe2/` and `stress/` came over from the AITranscribe repository, where
# each sat beside its own tests and imported its neighbours as top-level modules
# (`import audio`, `import verify_stress`). Rewriting those imports would make
# every future sync from that repository a merge conflict, so the path is
# widened here instead and the copied files stay byte-identical to their source.
for sub in ("transcribe2", "stress"):
    d = ROOT / sub
    if d.is_dir() and str(d) not in sys.path:
        sys.path.insert(0, str(d))
