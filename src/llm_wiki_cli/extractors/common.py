"""Shared helpers for source-file extractor discovery and filtering."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable

from ..config import EXCLUDED_DIRS, GitIgnoreMatcher, build_gitignore_matcher

LANGUAGE_EXTENSIONS: dict[str, tuple[str, ...]] = {
    "python": (".py",),
    "typescript": (".ts", ".tsx"),
    "go": (".go",),
    "rust": (".rs",),
}


def should_skip_source_path(path: Path, src_path: Path, matcher: GitIgnoreMatcher | None = None) -> bool:
    """Return True when *path* should be skipped for source extraction."""
    rel = path.relative_to(src_path)
    if not EXCLUDED_DIRS.isdisjoint(rel.parts):
        return True
    if matcher and matcher.is_ignored(rel.as_posix()):
        return True
    return False


def discover_source_files(
    src_dir: str,
    extensions: Iterable[str],
    *,
    only_files: list[str] | None = None,
    language: str | None = None,
    matcher: GitIgnoreMatcher | None = None,
) -> list[str]:
    """Return matching source files relative to *src_dir*.

    The returned paths use forward slashes and respect excluded directories and
    gitignore rules. Language-specific conventions that avoid generated or
    duplicate files are handled here so Python wrappers can skip toolchains when
    there is nothing useful to scan.
    """
    src_path = Path(src_dir).resolve()
    matcher = matcher or build_gitignore_matcher(src_path)
    extensions = tuple(extensions)

    if only_files is not None:
        candidates = [src_path / f for f in only_files]
    else:
        candidates = []
        for ext in extensions:
            candidates.extend(src_path.rglob(f"*{ext}"))

    result: list[str] = []
    seen: set[str] = set()
    for path in candidates:
        try:
            resolved = path.resolve()
            rel = resolved.relative_to(src_path)
        except (OSError, ValueError):
            continue
        if not resolved.is_file() or resolved.suffix not in extensions:
            continue
        if should_skip_source_path(resolved, src_path, matcher):
            continue
        if language == "typescript" and resolved.name.endswith(".d.ts"):
            continue
        if language == "go" and resolved.name.endswith("_test.go"):
            continue
        rel_posix = rel.as_posix()
        if rel_posix not in seen:
            result.append(rel_posix)
            seen.add(rel_posix)
    return sorted(result)


def filter_bundled_inventory(inventory: dict, scripts_dir: Path) -> dict:
    """Remove extractor implementation files from a subprocess inventory."""
    scripts_abs = scripts_dir.resolve().as_posix() + "/"
    filtered: dict = {}
    for fp, data in inventory.items():
        fp_posix = fp.replace("\\", "/")
        try:
            resolved = Path(fp).resolve().as_posix()
        except OSError:
            resolved = fp_posix
        if fp_posix.startswith(scripts_abs) or resolved.startswith(scripts_abs):
            continue
        filtered[fp_posix] = data
    return filtered
