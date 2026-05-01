"""Shared path normalization helpers."""

from __future__ import annotations

from pathlib import Path


def normalize_source_path(value: str | None, src_dir: str | None = None) -> str | None:
    """Normalize a source path from generated markdown or Docker instructions."""
    if not value:
        return None
    normalized = value.strip().strip("`").strip().strip('"').strip("'")
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
