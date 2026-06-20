"""Shared source-tree discovery for inventory, Docker, and package scans."""

from __future__ import annotations

import os
import hashlib
from dataclasses import dataclass
from fnmatch import fnmatch
from pathlib import Path
from typing import Iterable

from ..config import (
    COMPOSE_PATTERNS,
    DOCKERFILE_PATTERNS,
    EXCLUDED_DIRS,
    GitIgnoreMatcher,
    _GitignoreRule,
    _parse_gitignore_file,
)
from ..extractors.common import LANGUAGE_EXTENSIONS

_DOC_SUFFIXES = {".md", ".txt", ".rst", ".html", ".json"}
_PACKAGE_MARKERS = {"pyproject.toml", "setup.py"}


@dataclass(frozen=True)
class SourceFile:
    """A source-tree file discovered relative to a snapshot root."""

    rel_path: str
    abs_path: Path
    suffix: str
    language: str | None
    size: int
    mtime_ns: int


@dataclass(frozen=True)
class SourceSnapshot:
    """Filtered source-tree discovery results shared by lint/extract paths."""

    root: Path
    files_by_language: dict[str, tuple[SourceFile, ...]]
    dockerfile_candidates: tuple[SourceFile, ...]
    compose_candidates: tuple[SourceFile, ...]
    yaml_candidates: tuple[SourceFile, ...]
    package_markers: tuple[SourceFile, ...]
    all_source_paths: tuple[str, ...]
    gitignore_fingerprint: str

    def language_paths(self, language: str) -> list[str]:
        """Return deterministic relative paths for a language."""
        return [
            source_file.rel_path
            for source_file in self.files_by_language.get(language, ())
        ]


@dataclass
class _SnapshotBuckets:
    files_by_language: dict[str, list[SourceFile]]
    dockerfile_candidates: list[SourceFile]
    compose_candidates: list[SourceFile]
    yaml_candidates: list[SourceFile]
    package_markers: list[SourceFile]
    gitignore_paths: list[tuple[str, Path]]
    gitignore_rules: list[_GitignoreRule]


def _new_snapshot_buckets() -> _SnapshotBuckets:
    return _SnapshotBuckets(
        files_by_language={language: [] for language in LANGUAGE_EXTENSIONS},
        dockerfile_candidates=[],
        compose_candidates=[],
        yaml_candidates=[],
        package_markers=[],
        gitignore_paths=[],
        gitignore_rules=[],
    )


def _normalize_only_files(
    root: Path, only_files: Iterable[str] | None
) -> set[str] | None:
    if only_files is None:
        return None

    normalized: set[str] = set()
    for raw_path in only_files:
        try:
            resolved = (root / raw_path).resolve()
            rel = resolved.relative_to(root)
        except (OSError, ValueError):
            continue
        normalized.add(rel.as_posix())
    return normalized


def _language_for_path(path: Path) -> str | None:
    suffix = path.suffix
    for language, extensions in LANGUAGE_EXTENSIONS.items():
        if suffix not in extensions:
            continue
        if language == "typescript" and path.name.endswith(".d.ts"):
            return None
        if language == "go" and path.name.endswith("_test.go"):
            return None
        return language
    return None


def _is_dockerfile_candidate(path: Path) -> bool:
    if path.suffix.lower() in _DOC_SUFFIXES:
        return False
    return any(fnmatch(path.name, pattern) for pattern in DOCKERFILE_PATTERNS)


def _is_compose_candidate(path: Path) -> bool:
    return any(fnmatch(path.name, pattern) for pattern in COMPOSE_PATTERNS)


def _make_source_file(
    root: Path, path: Path, rel: Path, language: str | None
) -> SourceFile | None:
    try:
        stat = path.stat()
    except OSError:
        return None
    return SourceFile(
        rel_path=rel.as_posix(),
        abs_path=path,
        suffix=path.suffix,
        language=language,
        size=stat.st_size,
        mtime_ns=stat.st_mtime_ns,
    )


def _append_sorted(target: list[SourceFile], source_file: SourceFile | None) -> None:
    if source_file is not None:
        target.append(source_file)


def _sha256_labeled_files(paths: list[tuple[str, Path]]) -> str:
    hasher = hashlib.sha256()
    for label, path in sorted(paths, key=lambda item: item[0]):
        hasher.update(label.replace("\\", "/").encode("utf-8"))
        hasher.update(b"\0")
        try:
            hasher.update(path.read_bytes())
        except OSError:
            hasher.update(b"<unreadable>")
        hasher.update(b"\0")
    return "sha256:" + hasher.hexdigest()


def _directory_ignored(matcher: GitIgnoreMatcher, rel_path: str) -> bool:
    """Return whether a directory path is ignored by the current matcher."""
    rel_path = rel_path.strip("/")
    if not rel_path:
        return False
    return matcher.is_ignored(rel_path) or matcher.is_ignored(
        f"{rel_path}/__llm_wiki_dir__"
    )


def _empty_source_snapshot(root: Path) -> SourceSnapshot:
    return SourceSnapshot(
        root=root,
        files_by_language={language: () for language in LANGUAGE_EXTENSIONS},
        dockerfile_candidates=(),
        compose_candidates=(),
        yaml_candidates=(),
        package_markers=(),
        all_source_paths=(),
        gitignore_fingerprint=_sha256_labeled_files([]),
    )


def _relative_to_root(path: Path, root: Path) -> Path | None:
    try:
        return path.resolve().relative_to(root)
    except (OSError, ValueError):
        return None


def _is_excluded_walk_directory(rel_dir: Path) -> bool:
    return rel_dir != Path(".") and not EXCLUDED_DIRS.isdisjoint(rel_dir.parts)


def _record_gitignore_rules(
    root: Path,
    current_dir: Path,
    rel_dir: Path,
    buckets: _SnapshotBuckets,
) -> None:
    gitignore = current_dir / ".gitignore"
    if not gitignore.is_file():
        return

    base = "" if rel_dir == Path(".") else rel_dir.as_posix()
    buckets.gitignore_paths.append((gitignore.relative_to(root).as_posix(), gitignore))
    buckets.gitignore_rules.extend(_parse_gitignore_file(gitignore, base))


def _prune_dirnames(
    dirnames: list[str], rel_dir: Path, matcher: GitIgnoreMatcher
) -> None:
    kept_dirnames = []
    for name in dirnames:
        if name in EXCLUDED_DIRS:
            continue
        child_rel = name if rel_dir == Path(".") else (rel_dir / name).as_posix()
        if _directory_ignored(matcher, child_rel):
            continue
        kept_dirnames.append(name)
    dirnames[:] = kept_dirnames


def _record_infrastructure_candidates(
    resolved: Path,
    source_file: SourceFile | None,
    buckets: _SnapshotBuckets,
) -> None:
    if _is_dockerfile_candidate(resolved):
        _append_sorted(buckets.dockerfile_candidates, source_file)
    if _is_compose_candidate(resolved):
        _append_sorted(buckets.compose_candidates, source_file)
    if resolved.suffix.lower() in {".yml", ".yaml"}:
        _append_sorted(buckets.yaml_candidates, source_file)


def _record_language_candidate(
    root: Path,
    resolved: Path,
    rel: Path,
    only_set: set[str] | None,
    buckets: _SnapshotBuckets,
) -> None:
    language = _language_for_path(resolved)
    if language is None:
        return

    rel_posix = rel.as_posix()
    if only_set is not None and rel_posix not in only_set:
        return

    source_file = _make_source_file(root, resolved, rel, language)
    _append_sorted(buckets.files_by_language[language], source_file)


def _record_source_file(
    root: Path,
    current_dir: Path,
    filename: str,
    matcher: GitIgnoreMatcher,
    only_set: set[str] | None,
    buckets: _SnapshotBuckets,
) -> None:
    path = current_dir / filename
    rel = _relative_to_root(path, root)
    if rel is None:
        return

    resolved = path.resolve()
    if not resolved.is_file() or not EXCLUDED_DIRS.isdisjoint(rel.parts):
        return

    package_source_file = _make_source_file(root, resolved, rel, None)
    if filename in _PACKAGE_MARKERS:
        _append_sorted(buckets.package_markers, package_source_file)

    if matcher.is_ignored(rel.as_posix()):
        return

    _record_infrastructure_candidates(resolved, package_source_file, buckets)
    _record_language_candidate(root, resolved, rel, only_set, buckets)


def _collect_source_tree(
    root: Path, only_set: set[str] | None, buckets: _SnapshotBuckets
) -> None:
    for dirpath, dirnames, filenames in os.walk(root, topdown=True, followlinks=False):
        current_dir = Path(dirpath)
        rel_dir = _relative_to_root(current_dir, root)
        if rel_dir is None or _is_excluded_walk_directory(rel_dir):
            dirnames[:] = []
            continue

        _record_gitignore_rules(root, current_dir, rel_dir, buckets)
        matcher = GitIgnoreMatcher(buckets.gitignore_rules)
        _prune_dirnames(dirnames, rel_dir, matcher)

        for filename in filenames:
            _record_source_file(root, current_dir, filename, matcher, only_set, buckets)


def _build_source_snapshot(root: Path, buckets: _SnapshotBuckets) -> SourceSnapshot:
    sorted_languages = {
        language: tuple(sorted(source_files, key=lambda item: item.rel_path))
        for language, source_files in buckets.files_by_language.items()
    }
    all_source_paths = tuple(
        sorted(
            source_file.rel_path
            for source_files in sorted_languages.values()
            for source_file in source_files
        )
    )

    return SourceSnapshot(
        root=root,
        files_by_language=sorted_languages,
        dockerfile_candidates=tuple(
            sorted(buckets.dockerfile_candidates, key=lambda item: item.rel_path)
        ),
        compose_candidates=tuple(
            sorted(buckets.compose_candidates, key=lambda item: item.rel_path)
        ),
        yaml_candidates=tuple(
            sorted(buckets.yaml_candidates, key=lambda item: item.rel_path)
        ),
        package_markers=tuple(
            sorted(buckets.package_markers, key=lambda item: item.rel_path)
        ),
        all_source_paths=all_source_paths,
        gitignore_fingerprint=_sha256_labeled_files(buckets.gitignore_paths),
    )


def build_source_snapshot(
    src_dir: str | Path, only_files: Iterable[str] | None = None
) -> SourceSnapshot:
    """Build a deterministic source-tree snapshot rooted at *src_dir*.

    Source language files respect ``only_files`` when supplied. Docker,
    Compose, YAML, and package-marker candidates still cover the full source
    tree so command paths that restrict source extraction preserve their
    existing infrastructure and package behavior.
    """
    root = Path(src_dir).resolve()
    only_set = _normalize_only_files(root, only_files)

    if not root.exists():
        return _empty_source_snapshot(root)

    buckets = _new_snapshot_buckets()
    _collect_source_tree(root, only_set, buckets)
    return _build_source_snapshot(root, buckets)
