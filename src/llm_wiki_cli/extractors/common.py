"""Shared helpers for source-file extractor discovery and filtering."""

from __future__ import annotations

import os
import posixpath
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

# These are project-source identities, relative to the owned ``llm_wiki_cli``
# package root.  Package markers and nested .gitignore files intentionally do
# not appear here: they remain snapshot inputs even though these implementation
# files are excluded from project-source discovery.
_BUNDLED_HELPER_IMPLEMENTATIONS = frozenset(
    {
        "extractors/ts_scripts/extract.js",
        "extractors/go_scripts/main.go",
        "extractors/rust_scripts/src/main.rs",
        "extractors/haskell_scripts/Inventory.hs",
        "extractors/haskell_scripts/Json.hs",
        "extractors/haskell_scripts/Main.hs",
        "extractors/haskell_scripts/Parser.hs",
        "extractors/haskell_scripts/Paths.hs",
    }
)
_WINDOWS_BUNDLED_HELPER_IMPLEMENTATIONS = frozenset(
    path.casefold() for path in _BUNDLED_HELPER_IMPLEMENTATIONS
)
BUNDLED_HELPER_IMPLEMENTATION_PATHS = frozenset(
    f"llm_wiki_cli/{relative_path}"
    for relative_path in _BUNDLED_HELPER_IMPLEMENTATIONS
)
_OWNED_PACKAGE_SENTINELS = (
    "__init__.py",
    "cli.py",
    "extractors/__init__.py",
    "extractors/common.py",
)


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


def _normalize_path_text(path: str | Path) -> str:
    """Return a separator-normalized lexical path without resolving it."""
    if isinstance(path, Path):
        # A concrete POSIX Path may legally contain a literal backslash.  Its
        # native ``as_posix`` form is already normalized for its platform.
        path_text = path.as_posix()
    else:
        # Raw path text has no native-path identity, so accept either common
        # separator to support subprocess output from another platform.
        path_text = str(path).replace("\\", "/")
    return posixpath.normpath(path_text) if path_text else ""


def _is_windows_absolute_path_text(path: str) -> bool:
    return bool(re.match(r"^[A-Za-z]:/", path)) or path.startswith("//")


def _is_absolute_path_text(path: str) -> bool:
    return path.startswith("/") or _is_windows_absolute_path_text(path)


def _path_is_within(path: str, directory: str) -> bool:
    if _is_windows_absolute_path_text(path) and _is_windows_absolute_path_text(
        directory
    ):
        path = path.casefold()
        directory = directory.casefold()
    return path == directory or path.startswith(f"{directory}/")


def _path_text_equal(left: str, right: str) -> bool:
    if _is_windows_absolute_path_text(left) and _is_windows_absolute_path_text(
        right
    ):
        return left.casefold() == right.casefold()
    return left == right


def _helper_relative_path_matches(relative_path: str, *, windows: bool) -> bool:
    if windows:
        return relative_path.casefold() in _WINDOWS_BUNDLED_HELPER_IMPLEMENTATIONS
    return relative_path in _BUNDLED_HELPER_IMPLEMENTATIONS


def _owned_package_sentinels_present(package_root: str) -> bool:
    """Prove that an inferred root is an LLM Wiki package source tree."""
    root = Path(package_root)
    try:
        return all(
            (root / relative_path).is_file()
            for relative_path in _OWNED_PACKAGE_SENTINELS
        )
    except (OSError, RuntimeError, ValueError):
        return False


def is_bundled_helper_implementation_path(
    path: str | Path,
    *,
    package_root: str | Path | None = None,
) -> bool:
    """Return whether *path* is one of this package's eight helper sources.

    ``package_root`` is an explicit, trusted ownership proof and must name the
    ``llm_wiki_cli`` package directory.  It is useful for lexical Windows paths
    and copied or non-editable installations whose paths must not be resolved
    through the running package.  Without it, the candidate package root is
    inferred from *path* and must contain the package sentinels above.  A
    consumer path that merely shares the package-relative suffix is therefore
    not classified as bundled source.
    """
    normalized = _normalize_path_text(path)
    if not normalized:
        return False

    if package_root is not None:
        normalized_root = _normalize_path_text(package_root)
        windows = _is_windows_absolute_path_text(normalized_root)
        package_name = posixpath.basename(normalized_root)
        if (package_name.casefold() if windows else package_name) != "llm_wiki_cli":
            return False
        explicit_candidates = [normalized]
        if not _is_absolute_path_text(normalized):
            explicit_candidates.extend(
                (
                    posixpath.join(normalized_root, normalized),
                    posixpath.join(posixpath.dirname(normalized_root), normalized),
                )
            )
        return any(
            _path_text_equal(
                candidate,
                f"{normalized_root}/{relative_path}",
            )
            for candidate in explicit_candidates
            for relative_path in _BUNDLED_HELPER_IMPLEMENTATIONS
        )

    if not _is_absolute_path_text(normalized):
        # Without an explicit owned root, relative spelling has no ownership
        # proof and must never be interpreted through ambient CWD.
        return False
    windows = _is_windows_absolute_path_text(normalized)
    if windows and os.name != "nt":
        # A foreign absolute path cannot provide filesystem ownership proof on
        # this host; callers can supply the trusted lexical package root.
        return False
    parts = normalized.split("/")
    for index, part in enumerate(parts):
        if (part.casefold() if windows else part) != "llm_wiki_cli":
            continue
        relative_path = "/".join(parts[index + 1 :])
        if not _helper_relative_path_matches(relative_path, windows=windows):
            continue
        package_root_text = "/".join(parts[: index + 1])
        if normalized.startswith("/"):
            package_root_text = f"/{package_root_text.lstrip('/')}"
        if _owned_package_sentinels_present(package_root_text):
            return True
    return False


def _resolved_inventory_path(path: str | Path) -> Path | None:
    """Resolve a concrete local path without interpreting foreign paths."""
    normalized = _normalize_path_text(path)
    if _is_windows_absolute_path_text(normalized) and os.name != "nt":
        return None
    try:
        concrete = path if isinstance(path, Path) else Path(str(path))
        return concrete.resolve()
    except (OSError, RuntimeError, ValueError):
        return None


def _normalized_context_root(root: str | Path) -> str:
    normalized = _normalize_path_text(root)
    if _is_windows_absolute_path_text(normalized) and os.name != "nt":
        return normalized
    try:
        concrete = root if isinstance(root, Path) else Path(str(root))
        return _normalize_path_text(concrete.resolve())
    except (OSError, RuntimeError, ValueError):
        return normalized


def _contextual_inventory_candidate(
    root: str | Path,
    relative_path: str,
) -> str | Path:
    normalized_root = _normalized_context_root(root)
    if _is_windows_absolute_path_text(normalized_root) and os.name != "nt":
        return posixpath.join(normalized_root, relative_path)
    return Path(normalized_root) / Path(relative_path)


def _inventory_classification_candidates(
    path: str | Path,
    *,
    source_root: str | Path | None,
    package_root: str | Path | None,
) -> tuple[str | Path, ...]:
    normalized = _normalize_path_text(path)
    if not normalized:
        return ()

    candidates: list[str | Path] = []
    concrete = path if isinstance(path, Path) else Path(str(path))
    if concrete.is_absolute():
        candidates.append(concrete)
    elif _is_absolute_path_text(normalized):
        candidates.append(normalized)
    else:
        if source_root is not None:
            candidates.append(_contextual_inventory_candidate(source_root, normalized))
        if package_root is not None:
            normalized_package_root = _normalized_context_root(package_root)
            candidates.extend(
                (
                    _contextual_inventory_candidate(package_root, normalized),
                    _contextual_inventory_candidate(
                        posixpath.dirname(normalized_package_root),
                        normalized,
                    ),
                )
            )

    expanded: list[str | Path] = []
    seen: set[tuple[bool, str]] = set()
    for candidate in candidates:
        key = (isinstance(candidate, Path), _normalize_path_text(candidate))
        if key not in seen:
            seen.add(key)
            expanded.append(candidate)
        resolved_candidate = _resolved_inventory_path(candidate)
        if resolved_candidate is not None:
            resolved_key = (True, _normalize_path_text(resolved_candidate))
            if resolved_key not in seen:
                seen.add(resolved_key)
                expanded.append(resolved_candidate)
    return tuple(expanded)


def is_bundled_inventory_path(
    path: str | Path,
    *,
    source_root: str | Path | None = None,
    package_root: str | Path | None = None,
) -> bool:
    """Classify an inventory key without consulting ambient CWD.

    Relative keys require an explicit source or package root.  Both their
    lexical identity and any locally resolvable target are checked, closing
    symlink aliases while leaving unrelated virtual plugin records untouched.
    """
    candidates = _inventory_classification_candidates(
        path,
        source_root=source_root,
        package_root=package_root,
    )
    return any(
        is_bundled_helper_implementation_path(candidate)
        or (
            package_root is not None
            and is_bundled_helper_implementation_path(
                candidate,
                package_root=package_root,
            )
        )
        for candidate in candidates
    )


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
        if is_bundled_helper_implementation_path(path):
            continue
        try:
            resolved = path.resolve()
            rel = resolved.relative_to(src_path)
        except (OSError, ValueError):
            continue
        if not resolved.is_file() or resolved.suffix not in extensions:
            continue
        if is_bundled_helper_implementation_path(resolved):
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


def filter_bundled_inventory(
    inventory: dict,
    scripts_dir: Path,
    *,
    source_root: str | Path | None = None,
    package_root: str | Path | None = None,
) -> dict:
    """Remove bundled/package-cache implementation files from an inventory.

    The absolute ``scripts_dir`` containment check is retained for installed
    package and prepared-cache defense.  ``source_root`` additionally lets
    relative subprocess results use the same owned-package classifier as
    source planning when the scanned checkout differs from this installation.
    ``package_root`` supplies the classifier's optional trusted ownership proof
    for lexical paths (for example a Windows path inspected on POSIX).
    """
    scripts_abs = _normalize_path_text(scripts_dir.resolve())
    filtered: dict = {}
    for fp, data in inventory.items():
        path_value = fp if isinstance(fp, Path) else str(fp)
        concrete_path = fp if isinstance(fp, Path) else Path(str(fp))
        fp_posix = _normalize_path_text(
            concrete_path if concrete_path.is_absolute() else path_value
        )
        absolute_candidates = (
            _inventory_classification_candidates(
                path_value,
                source_root=None,
                package_root=None,
            )
            if _is_absolute_path_text(fp_posix)
            else ()
        )
        if any(
            _path_is_within(_normalize_path_text(candidate), scripts_abs)
            for candidate in absolute_candidates
        ):
            continue
        if is_bundled_inventory_path(
            path_value,
            source_root=source_root,
            package_root=package_root,
        ):
            continue
        filtered[fp_posix] = data
    return filtered


def filter_bundled_source_inventory(
    inventory: dict,
    *,
    source_root: str | Path,
    package_root: str | Path | None = None,
) -> dict:
    """Remove owned helper records while preserving all retained key identity."""
    return {
        fp: data
        for fp, data in inventory.items()
        if not is_bundled_inventory_path(
            fp if isinstance(fp, Path) else str(fp),
            source_root=source_root,
            package_root=package_root,
        )
    }


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
