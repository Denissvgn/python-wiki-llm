"""Shared source-tree discovery for inventory, Docker, and package scans."""

from __future__ import annotations

import os
from dataclasses import dataclass
from fnmatch import fnmatch
from pathlib import Path
from typing import Iterable

from ..config import (
    COMPOSE_PATTERNS,
    DOCKERFILE_PATTERNS,
    EXCLUDED_DIRS,
    build_gitignore_matcher,
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

    def language_paths(self, language: str) -> list[str]:
        """Return deterministic relative paths for a language."""
        return [source_file.rel_path for source_file in self.files_by_language.get(language, ())]


def _normalize_only_files(root: Path, only_files: Iterable[str] | None) -> set[str] | None:
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


def _make_source_file(root: Path, path: Path, rel: Path, language: str | None) -> SourceFile | None:
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


def build_source_snapshot(src_dir: str | Path, only_files: Iterable[str] | None = None) -> SourceSnapshot:
    """Build a deterministic source-tree snapshot rooted at *src_dir*.

    Source language files respect ``only_files`` when supplied. Docker,
    Compose, YAML, and package-marker candidates still cover the full source
    tree so command paths that restrict source extraction preserve their
    existing infrastructure and package behavior.
    """
    root = Path(src_dir).resolve()
    matcher = build_gitignore_matcher(root)
    only_set = _normalize_only_files(root, only_files)

    files_by_language: dict[str, list[SourceFile]] = {
        language: [] for language in LANGUAGE_EXTENSIONS
    }
    dockerfile_candidates: list[SourceFile] = []
    compose_candidates: list[SourceFile] = []
    yaml_candidates: list[SourceFile] = []
    package_markers: list[SourceFile] = []

    if not root.exists():
        return SourceSnapshot(
            root=root,
            files_by_language={language: () for language in LANGUAGE_EXTENSIONS},
            dockerfile_candidates=(),
            compose_candidates=(),
            yaml_candidates=(),
            package_markers=(),
            all_source_paths=(),
        )

    for dirpath, dirnames, filenames in os.walk(root, topdown=True, followlinks=False):
        dirnames[:] = [name for name in dirnames if name not in EXCLUDED_DIRS]
        current_dir = Path(dirpath)
        try:
            rel_dir = current_dir.resolve().relative_to(root)
        except (OSError, ValueError):
            dirnames[:] = []
            continue
        if rel_dir != Path(".") and not EXCLUDED_DIRS.isdisjoint(rel_dir.parts):
            dirnames[:] = []
            continue

        for filename in filenames:
            path = current_dir / filename
            try:
                resolved = path.resolve()
                rel = resolved.relative_to(root)
            except (OSError, ValueError):
                continue
            if not resolved.is_file() or not EXCLUDED_DIRS.isdisjoint(rel.parts):
                continue

            rel_posix = rel.as_posix()
            package_source_file = _make_source_file(root, resolved, rel, None)
            if filename in _PACKAGE_MARKERS:
                _append_sorted(package_markers, package_source_file)

            if matcher.is_ignored(rel_posix):
                continue

            docker_source_file = package_source_file
            if _is_dockerfile_candidate(resolved):
                _append_sorted(dockerfile_candidates, docker_source_file)
            if _is_compose_candidate(resolved):
                _append_sorted(compose_candidates, docker_source_file)
            if resolved.suffix.lower() in {".yml", ".yaml"}:
                _append_sorted(yaml_candidates, docker_source_file)

            language = _language_for_path(resolved)
            if language is None:
                continue
            if only_set is not None and rel_posix not in only_set:
                continue
            source_file = _make_source_file(root, resolved, rel, language)
            _append_sorted(files_by_language[language], source_file)

    sorted_languages = {
        language: tuple(sorted(source_files, key=lambda item: item.rel_path))
        for language, source_files in files_by_language.items()
    }
    all_source_paths = tuple(sorted(
        source_file.rel_path
        for source_files in sorted_languages.values()
        for source_file in source_files
    ))

    return SourceSnapshot(
        root=root,
        files_by_language=sorted_languages,
        dockerfile_candidates=tuple(sorted(dockerfile_candidates, key=lambda item: item.rel_path)),
        compose_candidates=tuple(sorted(compose_candidates, key=lambda item: item.rel_path)),
        yaml_candidates=tuple(sorted(yaml_candidates, key=lambda item: item.rel_path)),
        package_markers=tuple(sorted(package_markers, key=lambda item: item.rel_path)),
        all_source_paths=all_source_paths,
    )
