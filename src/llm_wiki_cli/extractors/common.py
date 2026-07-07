"""Shared helpers for source-file extractor discovery and filtering."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Iterable

from ..config import (
    EXCLUDED_DIRS,
    GitIgnoreMatcher,
    build_gitignore_matcher,
    is_agent_worktree_path,
)

TYPESCRIPT_FAMILY_EXTENSIONS = (".ts", ".tsx", ".js", ".jsx")
JAVASCRIPT_EXTENSIONS = (".js", ".jsx")
GENERATED_JAVASCRIPT_BUNDLE_LANGUAGE = "generated_javascript_bundle"
_BUNDLE_ASSET_DIRS = {
    ("public", "assets"),
    ("public", "js"),
    ("static", "assets"),
    ("static", "js"),
}
_HASH_TOKEN_SPLIT_RE = re.compile(r"[-.]+")

LANGUAGE_EXTENSIONS: dict[str, tuple[str, ...]] = {
    "python": (".py",),
    "typescript": TYPESCRIPT_FAMILY_EXTENSIONS,
    "go": (".go",),
    "rust": (".rs",),
    "haskell": (".hs", ".lhs"),
}
INCLUDE_TEST_LANGUAGES = frozenset({"go"})
MAX_ONLY_FILES_ARG_CHARS = 60_000


def normalize_include_tests(include_tests: Iterable[str] | None) -> frozenset[str]:
    """Return the normalized set of languages whose test files are included."""
    if include_tests is None:
        return frozenset()
    normalized = frozenset(
        str(language).strip().lower()
        for language in include_tests
        if str(language).strip()
    )
    unsupported = sorted(normalized - INCLUDE_TEST_LANGUAGES)
    if unsupported:
        raise ValueError(f"Unsupported include-tests language: {unsupported[0]}")
    return normalized


def inventory_language_for_path(language: str, path: str | Path) -> str:
    """Return the precise inventory language label for a discovered file."""
    if language == "typescript" and Path(path).suffix in JAVASCRIPT_EXTENSIONS:
        return "javascript"
    return language


def is_generated_javascript_bundle_path(path: str | Path) -> bool:
    """Return True for generated/minified JavaScript static asset bundles."""
    path_text = path.as_posix() if isinstance(path, Path) else str(path)
    parts = tuple(part for part in path_text.replace("\\", "/").split("/") if part)
    if not parts or Path(parts[-1]).suffix.lower() != ".js":
        return False
    if "src" in parts[:-1]:
        return False
    if not _has_bundle_asset_directory(parts[:-1]):
        return False

    name = parts[-1]
    if name.endswith(".min.js"):
        return True
    return _looks_like_hashed_bundle_name(name)


def _has_bundle_asset_directory(directory_parts: tuple[str, ...]) -> bool:
    return any(
        directory_parts[index : index + 2] in _BUNDLE_ASSET_DIRS
        for index in range(len(directory_parts) - 1)
    )


def _looks_like_hashed_bundle_name(name: str) -> bool:
    stem = name[:-3]
    tokens = [token for token in _HASH_TOKEN_SPLIT_RE.split(stem) if token]
    if not tokens:
        return False
    token = tokens[-1]
    has_upper = any(char.isupper() for char in token)
    has_lower = any(char.islower() for char in token)
    return (
        len(token) >= 6
        and any(char.isalpha() for char in token)
        and (any(char.isdigit() for char in token) or (has_upper and has_lower))
    )


def should_skip_source_path(
    path: Path, src_path: Path, matcher: GitIgnoreMatcher | None = None
) -> bool:
    """Return True when *path* should be skipped for source extraction."""
    rel = path.relative_to(src_path)
    if not EXCLUDED_DIRS.isdisjoint(rel.parts):
        return True
    if is_agent_worktree_path(rel):
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
    include_tests: Iterable[str] | None = None,
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
    include_test_languages = normalize_include_tests(include_tests)

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
        rel_posix = rel.as_posix()
        if not EXCLUDED_DIRS.isdisjoint(rel.parts):
            continue
        if only_files is None and is_agent_worktree_path(rel_posix):
            continue
        if (
            only_files is None
            and language == "typescript"
            and is_generated_javascript_bundle_path(rel_posix)
        ):
            continue
        if matcher and matcher.is_ignored(rel.as_posix()) and only_files is None:
            continue
        if (
            language == "go"
            and resolved.name.endswith("_test.go")
            and "go" not in include_test_languages
        ):
            continue
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


def chunk_source_files_for_cli(
    source_files: list[str], *, max_chars: int | None = None
) -> list[list[str]]:
    """Split source paths into chunks safe for ``--only-files`` CLI arguments."""
    limit = max_chars or MAX_ONLY_FILES_ARG_CHARS
    chunks: list[list[str]] = []
    current: list[str] = []
    current_len = 0

    for source_file in source_files:
        next_len = (
            len(source_file) if not current else current_len + 1 + len(source_file)
        )
        if current and next_len > limit:
            chunks.append(current)
            current = [source_file]
            current_len = len(source_file)
            continue
        current.append(source_file)
        current_len = next_len

    if current:
        chunks.append(current)
    return chunks
