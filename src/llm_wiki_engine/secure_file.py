"""Helpers for writing local runtime files with best-effort privacy."""

from __future__ import annotations

import os
from pathlib import Path


def write_private_text(path: str | Path, text: str, *, encoding: str = "utf-8") -> Path:
    """Write text and restrict file permissions where the platform supports it.

    POSIX platforms support owner-only mode bits. Windows' ``chmod`` support is
    limited to read-only toggling, so this remains a best-effort operation there.
    """
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text, encoding=encoding)
    try:
        os.chmod(target, 0o600)
    except OSError:
        pass
    return target
