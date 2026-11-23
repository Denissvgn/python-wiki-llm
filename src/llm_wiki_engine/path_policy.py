"""Workspace path policy: the default wiki directory, excluded directories,
agent worktrees and validation of wiki and source roots.

``llm_wiki_cli.config`` re-exports every name for existing callers.
"""

from __future__ import annotations

from .layout import DEFAULT_LAYOUT

import os
import sys
import warnings
from collections.abc import Callable
from pathlib import Path

from .filesystem_guard import (
    WindowsSecurityGuardError,
    windows_current_user_sid,
    windows_path_owner_sid,
)
from llm_wiki_engine.host import current_host
from .io import first_unsafe_path_component


DEFAULT_WIKI_DIR = DEFAULT_LAYOUT.wiki_dir

# Directories excluded from source-file scans.  This intentionally covers both
# conventional environment names (``.venv``) and environment internals
# (``site-packages``) so renamed virtualenvs still stay out of the wiki.
EXCLUDED_DIRS: set[str] = {
    ".cache",
    ".direnv",
    ".eggs",
    ".env",
    ".git",
    DEFAULT_LAYOUT.knowledge_store,
    DEFAULT_LAYOUT.manifest_objects,
    ".mypy_cache",
    ".next",
    ".nox",
    ".npm",
    ".nuxt",
    ".parcel-cache",
    ".pnpm-store",
    ".pyre",
    ".pytest_cache",
    ".ruff_cache",
    ".svelte-kit",
    ".tox",
    ".venv",
    ".virtualenv",
    ".vite",
    ".yarn",
    "__pycache__",
    "__pypackages__",
    "bower_components",
    "build",
    "coverage",
    "dist",
    "env",
    "htmlcov",
    "jspm_packages",
    "llm-wiki-extractors",
    "node_modules",
    "out",
    "site-packages",
    "target",
    "venv",
    "virtualenv",
}

AGENT_WORKTREE_DIR_PATTERNS: tuple[tuple[str, ...], ...] = ((".claude", "worktrees"),)

def _normalized_rel_parts(path: "str | Path") -> tuple[str, ...]:
    text = path.as_posix() if isinstance(path, Path) else str(path)
    text = text.replace("\\", "/").strip("/")
    return tuple(part for part in text.split("/") if part and part != ".")

def is_agent_worktree_path(path: "str | Path") -> bool:
    """Return whether *path* is inside a generated agent worktree subtree."""
    parts = _normalized_rel_parts(path)
    for pattern in AGENT_WORKTREE_DIR_PATTERNS:
        pattern_len = len(pattern)
        if pattern_len == 0 or len(parts) < pattern_len:
            continue
        for index in range(len(parts) - pattern_len + 1):
            if parts[index : index + pattern_len] == pattern:
                return True
    return False

class PathValidationError(ValueError):
    """Raised when a user-provided path escapes the project root."""

def validate_path(path: str, label: str = "path") -> Path:
    """Ensure *path* resolves inside the current working directory.

    Raises PathValidationError with a clear message if the resolved path escapes the
    repository root (cwd).
    """
    if "\0" in path:
        raise PathValidationError(f"Error: {label} contains an embedded NUL character.")
    resolved = (current_host().cwd() / path).resolve()
    cwd = current_host().cwd().resolve()
    try:
        resolved.relative_to(cwd)
    except ValueError:
        raise PathValidationError(
            f"Error: {label} '{path}' resolves to '{resolved}', "
            f"which is outside the project root '{cwd}'."
        )
    return resolved

def validate_source_root(
    path: str,
    label: str = "--src-dir",
    *,
    allow_external: bool = False,
) -> Path:
    """Validate a source root according to the CLI source-read policy.

    By default this preserves :func:`validate_path` behaviour and rejects paths
    outside the current working directory.  When ``allow_external`` is true, the
    path may live outside cwd but must resolve to an existing directory.
    """
    if not allow_external:
        return validate_path(path, label)

    try:
        candidate = Path(path).expanduser()
        if not candidate.is_absolute():
            candidate = current_host().cwd() / candidate
        resolved = candidate.resolve(strict=True)
    except (OSError, RuntimeError, ValueError) as exc:
        raise PathValidationError(
            f"Error: {label} '{path}' cannot be resolved to an existing "
            f"directory: {exc}."
        ) from exc
    if not resolved.is_dir():
        raise PathValidationError(
            f"Error: {label} '{path}' resolves to '{resolved}', "
            "which is not an existing directory."
        )
    normalized_candidate = Path(os.path.abspath(candidate))
    if resolved != normalized_candidate:
        effective_uid: int | None = None
        trusted_owner: Callable[[Path], bool] | None = None
        ownership_is_verifiable = False
        if sys.platform == "win32":
            try:
                current_sid = windows_current_user_sid()
            except (OSError, RuntimeError, TypeError, ValueError):
                pass
            else:
                if isinstance(current_sid, str) and current_sid:
                    ownership_is_verifiable = True
                    trusted_windows_sids = {
                        current_sid,
                        "S-1-5-18",  # LocalSystem
                        "S-1-5-32-544",  # Built-in Administrators
                    }

                    def is_trusted_windows_owner(component: Path) -> bool:
                        return windows_path_owner_sid(component) in trusted_windows_sids

                    trusted_owner = is_trusted_windows_owner
        else:
            get_effective_uid = getattr(os, "geteuid", None)
            if callable(get_effective_uid):
                try:
                    derived_uid = get_effective_uid()
                except (OSError, RuntimeError, TypeError, ValueError):
                    pass
                else:
                    if (
                        isinstance(derived_uid, int)
                        and not isinstance(derived_uid, bool)
                        and derived_uid >= 0
                    ):
                        effective_uid = derived_uid
                        ownership_is_verifiable = True
        trusted_uids = {0, effective_uid} if effective_uid is not None else set()
        try:
            unsafe = first_unsafe_path_component(
                candidate,
                trusted_symlink_uids=trusted_uids,
                trusted_symlink_owner=trusted_owner,
            )
        except (OSError, RuntimeError, WindowsSecurityGuardError) as exc:
            raise PathValidationError(
                f"Error: {label} '{path}' traverses a symlink or reparse point "
                "whose ownership cannot be verified on this platform."
            ) from exc
        if unsafe is not None:
            if not ownership_is_verifiable:
                raise PathValidationError(
                    f"Error: {label} '{path}' traverses symlink or reparse point "
                    f"'{unsafe}' whose ownership cannot be verified on this "
                    "platform."
                )
            if sys.platform == "win32":
                raise PathValidationError(
                    f"Error: {label} '{path}' traverses symlink or reparse point "
                    f"'{unsafe}' not owned by the current Windows user, "
                    "LocalSystem, or Administrators."
                )
            raise PathValidationError(
                f"Error: {label} '{path}' traverses symlink or reparse point "
                f"'{unsafe}' not owned by the current user or root."
            )
        warnings.warn(
            f"external source root '{normalized_candidate}' resolves to '{resolved}'.",
            UserWarning,
            stacklevel=2,
        )
    return resolved

def validate_source_paths(
    src_dir: str | Path,
    paths: list[str] | tuple[str, ...] | None,
    label: str = "--paths",
) -> None:
    """Ensure requested source file paths stay inside *src_dir*.

    The extract CLI accepts paths relative to ``--src-dir``.  Absolute paths are
    tolerated only when they still resolve inside the source root.
    """
    if not paths:
        return

    root = Path(src_dir).resolve()
    for raw_path in paths:
        candidate = Path(raw_path).expanduser()
        if not candidate.is_absolute():
            candidate = root / candidate
        try:
            candidate.resolve().relative_to(root)
        except (OSError, ValueError):
            raise PathValidationError(
                f"Error: {label} '{raw_path}' resolves outside source root '{root}'."
            )
