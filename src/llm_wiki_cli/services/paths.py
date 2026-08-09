"""Shared path normalization helpers."""

from __future__ import annotations

import shlex
from pathlib import Path, PurePosixPath, PureWindowsPath


_TEST_DIRECTORY_NAMES = frozenset({"test", "tests", "__tests__"})
_TEST_FILE_STEMS = frozenset({"conftest"})


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


def is_test_source_path(value: str | Path | None) -> bool:
    """Return whether *value* follows a common cross-language test path pattern.

    Inventory paths are normally POSIX-relative, but normalising separators here
    keeps filtering deterministic for callers and fixtures on Windows too.
    """
    if value is None:
        return False
    normalized = str(value).replace("\\", "/").strip("/")
    if not normalized:
        return False
    path = PurePosixPath(normalized)
    parts = tuple(part.casefold() for part in path.parts)
    if _TEST_DIRECTORY_NAMES.intersection(parts[:-1]):
        return True

    name = path.name.casefold()
    stem = path.stem.casefold()
    if stem in _TEST_FILE_STEMS or stem.startswith("test_"):
        return True
    if stem.endswith("_test"):
        return True
    return ".test." in name or ".spec." in name


def shell_quote(value: str | Path) -> str:
    """Quote a value for POSIX shell snippets, including Git Bash on Windows."""
    if isinstance(value, Path):
        return shlex.quote(value.as_posix())
    return shlex.quote(str(value))


def portable_source_root_label(
    value: str | Path,
    *,
    base: str | Path | None = None,
) -> str:
    """Return a host-independent source-root label for generated artifacts."""

    raw_value = str(value)
    candidate = Path(value).expanduser()
    foreign_windows = PureWindowsPath(raw_value)
    if not candidate.is_absolute():
        if PurePosixPath(raw_value).is_absolute() or foreign_windows.drive:
            return "<external-source-root>"
    anchor = Path.cwd() if base is None else Path(base).expanduser()
    try:
        relative = candidate.resolve().relative_to(anchor.resolve())
    except (OSError, RuntimeError, ValueError):
        return "<external-source-root>"
    return "." if relative == Path() else relative.as_posix()
