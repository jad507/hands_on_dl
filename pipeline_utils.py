"""Shared timing utilities for pipeline scripts."""

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