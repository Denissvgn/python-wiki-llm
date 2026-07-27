"""Encoding-safe and atomic I/O helpers for wiki artifacts.

All wiki reads go through :func:`read_md` so that files containing
non-UTF-8 bytes (e.g. Windows cp1252 punctuation like ``0x97`` en-dash)
don't crash the tool.  All writes go through :func:`write_md` to
normalize output to UTF-8 with Unix line-endings.

Structured artifact writers use :func:`write_json_atomic` for deterministic
UTF-8 JSON staged in a unique same-directory temporary file.
"""

from __future__ import annotations

import os
import stat
import tempfile
from pathlib import Path
from typing import Any

from .knowledge_evidence import formatted_json_bytes


def first_unsafe_path_component(path: str | Path) -> Path | None:
    """Return the first traversal, symlink, or reparse component of a path.

    ``Path.resolve`` is deliberately not used: callers need to reject a path
    escape, not normalize it into an apparently safe leaf. Missing suffix
    components are permitted so the same helper can guard future targets.
    """

    lexical = Path(os.fspath(path))
    if ".." in lexical.parts:
        return lexical
    absolute = Path(os.path.abspath(lexical))
    current = Path(absolute.anchor)
    for part in absolute.parts[1:]:
        current /= part
        try:
            metadata = current.lstat()
        except FileNotFoundError:
            return None
        except OSError:
            return current
        attributes = getattr(metadata, "st_file_attributes", 0)
        reparse_flag = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0)
        special_link = stat.S_ISLNK(metadata.st_mode) or (
            bool(reparse_flag) and bool(attributes & reparse_flag)
        )
        if special_link:
            # Platform-level aliases such as macOS ``/var -> private/var`` are
            # root-owned entries directly below the filesystem root, outside
            # a checkout's control. Preserve those aliases while rejecting
            # every user/project-controlled component beneath them.
            if (
                current.parent == Path(absolute.anchor)
                and getattr(metadata, "st_uid", None) == 0
            ):
                continue
            return current
    return None


def read_md(path: Path) -> str:
    """Read a markdown file, tolerating non-UTF-8 encodings.

    Tries UTF-8 first; if that fails, falls back to cp1252 which covers
    common Windows-encoded punctuation (en-dash, em-dash, smart quotes).
    """
    data = path.read_bytes()
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError:
        text = data.decode("cp1252")
    return text.replace("\r\n", "\n").replace("\r", "\n")


def write_md(path: Path, text: str) -> None:
    """Write *text* to *path* as UTF-8 with Unix line-endings.

    Writes through a same-directory temporary file and atomically replaces
    the destination so an interrupted process does not leave a truncated page.
    """
    _write_utf8_text(path, text)


def _write_utf8_text(path: Path, text: str) -> None:
    """Atomically write UTF-8 text with Unix line endings."""
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    write_bytes_atomic(path, normalized.encode("utf-8"))


def write_bytes_atomic(path: str | Path, content: bytes) -> Path:
    """Atomically replace *path* with exact bytes staged in the same directory."""

    if not isinstance(content, bytes):
        raise TypeError("content must be bytes")
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(
        dir=target.parent,
        prefix=f".{target.name}.",
        suffix=".tmp",
    )
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(content)
        os.replace(tmp, target)
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise
    return target


def write_json_atomic(path: str | Path, payload: Any) -> Path:
    """Atomically write deterministic UTF-8 JSON and return its target path.

    Output uses sorted keys, Unix newlines, and exactly one trailing newline.
    Non-finite numbers and values unsupported by the standard JSON encoder are
    rejected before a temporary file is created.
    """

    target = Path(path)
    content = formatted_json_bytes(payload)
    write_bytes_atomic(target, content)
    return target


def write_text_output(path: str | Path, text: str) -> Path:
    """Write an explicit CLI/API output artifact as UTF-8 text.

    Unlike wiki paths, output paths are caller-controlled artifacts and may be
    absolute or outside the project root.
    """
    target = Path(path).expanduser()
    _write_utf8_text(target, text)
    return target
