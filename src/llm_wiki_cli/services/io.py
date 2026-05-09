"""Encoding-safe I/O helpers for wiki markdown files.

All wiki reads go through :func:`read_md` so that files containing
non-UTF-8 bytes (e.g. Windows cp1252 punctuation like ``0x97`` en-dash)
don't crash the tool.  All writes go through :func:`write_md` to
normalize output to UTF-8 with Unix line-endings.
"""

from __future__ import annotations

import os
import tempfile
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
    """Write *text* to *path* as UTF-8 with Unix line-endings.

    Writes through a same-directory temporary file and atomically replaces
    the destination so an interrupted process does not leave a truncated page.
    """
    _write_utf8_text(path, text)


def _write_utf8_text(path: Path, text: str) -> None:
    """Atomically write UTF-8 text with Unix line endings."""
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.", suffix=".tmp")
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(normalized.encode("utf-8"))
        os.replace(tmp, path)
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def write_text_output(path: str | Path, text: str) -> Path:
    """Write an explicit CLI/API output artifact as UTF-8 text.

    Unlike wiki paths, output paths are caller-controlled artifacts and may be
    absolute or outside the project root.
    """
    target = Path(path).expanduser()
    _write_utf8_text(target, text)
    return target
