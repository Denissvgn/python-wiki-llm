"""Shared path normalization helpers."""

from __future__ import annotations

import shlex
from pathlib import Path


def normalize_source_path(value: str | None, src_dir: str | None = None) -> str | None:
    """Normalize a source path from generated markdown or Docker instructions."""
    if not value:
        return None
    normalized = value.strip().strip("`").strip().strip('"').strip("'")
    if not normalized:
        return None
    normalized = normalized.replace("\\", "/")
    while normalized.startswith("./"):
        normalized = normalized[2:]

    candidate = Path(normalized)
    if src_dir and candidate.is_absolute():
        try:
            return candidate.resolve().relative_to(Path(src_dir).resolve()).as_posix()
        except ValueError:
            return candidate.as_posix()
    return normalized


def shell_quote(value: str | Path) -> str:
    """Quote a value for POSIX shell snippets, including Git Bash on Windows."""
    if isinstance(value, Path):
        return shlex.quote(value.as_posix())
    return shlex.quote(str(value))
