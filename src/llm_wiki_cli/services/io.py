"""Encoding-safe I/O helpers for wiki markdown files.

All wiki reads go through :func:`read_md` so that files containing
non-UTF-8 bytes (e.g. Windows cp1252 punctuation like ``0x97`` en-dash)
don't crash the tool.  All writes go through :func:`write_md` to
normalize output to UTF-8 with Unix line-endings.
"""

from __future__ import annotations

from pathlib import Path


def read_md(path: Path) -> str:
    """Read a markdown file, tolerating non-UTF-8 encodings.

    Tries UTF-8 first; if that fails, falls back to cp1252 which covers
    common Windows-encoded punctuation (en-dash, em-dash, smart quotes).
    """
    data = path.read_bytes()
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError:
        return data.decode("cp1252")


def write_md(path: Path, text: str) -> None:
    """Write *text* to *path* as UTF-8 with Unix line-endings."""
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    path.write_text(normalized, encoding="utf-8")
