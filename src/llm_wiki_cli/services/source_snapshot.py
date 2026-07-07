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
    is_agent_worktree_path,
)
from ..extractors.common import LANGUAGE_EXTENSIONS, normalize_include_tests
from ..extractors.common import (
    GENERATED_JAVASCRIPT_BUNDLE_LANGUAGE,
    is_generated_javascript_bundle_path,
)

_DOC_SUFFIXES = {".md", ".txt", ".rst", ".html", ".json"}
_PACKAGE_MARKER_NAMES = {
    "cabal.project",
    "flake.nix",
    "go.mod",
    "package.json",
    "pyproject.toml",
    "setup.py",
    "stack.yaml",
}
_PACKAGE_MARKER_SUFFIXES = {".cabal"}
KNOWN_UNSUPPORTED_LANGUAGE_EXTENSIONS: dict[str, tuple[str, ...]] = {
    "shell": (".sh",),
}
_ADVISORY_UNSUPPORTED_LANGUAGES = (GENERATED_JAVASCRIPT_BUNDLE_LANGUAGE,)
_UNSUPPORTED_LANGUAGE_LABELS = {
    GENERATED_JAVASCRIPT_BUNDLE_LANGUAGE: "generated JavaScript bundle",
}
_UNSUPPORTED_SUMMARY_PATH_LIMIT = 5


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
    unsupported_files_by_language: dict[str, tuple[SourceFile, ...]]
    all_source_paths: tuple[str, ...]
    gitignore_fingerprint: str

    def language_paths(self, language: str) -> list[str]:
        """Return deterministic relative paths for a language."""
        return [
            source_file.rel_path
            for source_file in self.files_by_language.get(language, ())
        ]

    def unsupported_language_paths(self, language: str) -> list[str]:
        """Return deterministic unsupported relative paths for a language."""
        return [
            source_file.rel_path
            for source_file in self.unsupported_files_by_language.get(language, ())
        ]


@dataclass
class _SnapshotBuckets:
    files_by_language: dict[str, list[SourceFile]]
    dockerfile_candidates: list[SourceFile]
    compose_candidates: list[SourceFile]
    yaml_candidates: list[SourceFile]
    package_markers: list[SourceFile]
    unsupported_files_by_language: dict[str, list[SourceFile]]
    gitignore_paths: list[tuple[str, Path]]
    gitignore_rules: list[_GitignoreRule]
    include_tests: frozenset[str]


def _new_snapshot_buckets(
    include_tests: Iterable[str] | None = None,
) -> _SnapshotBuckets:
    return _SnapshotBuckets(
        files_by_language={language: [] for language in LANGUAGE_EXTENSIONS},
        dockerfile_candidates=[],
        compose_candidates=[],
        yaml_candidates=[],
        package_markers=[],
        unsupported_files_by_language={
            language: []
            for language in (
                tuple(KNOWN_UNSUPPORTED_LANGUAGE_EXTENSIONS)
                + _ADVISORY_UNSUPPORTED_LANGUAGES
            )
        },
        gitignore_paths=[],
        gitignore_rules=[],
        include_tests=normalize_include_tests(include_tests),
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


def _language_for_path(path: Path, include_tests: frozenset[str]) -> str | None:
    suffix = path.suffix
    for language, extensions in LANGUAGE_EXTENSIONS.items():
        if suffix not in extensions:
            continue
        if (
            language == "go"
            and path.name.endswith("_test.go")
            and "go" not in include_tests
        ):
            return None
        return language
    return None


def _unsupported_language_for_path(path: Path) -> str | None:
    suffix = path.suffix.lower()
    for language, extensions in KNOWN_UNSUPPORTED_LANGUAGE_EXTENSIONS.items():
        if suffix in extensions:
            return language
    return None


def _is_dockerfile_candidate(path: Path) -> bool:
    if path.suffix.lower() in _DOC_SUFFIXES:
        return False
    return any(fnmatch(path.name, pattern) for pattern in DOCKERFILE_PATTERNS)


def _is_compose_candidate(path: Path) -> bool:
    return any(fnmatch(path.name, pattern) for pattern in COMPOSE_PATTERNS)


def _is_package_marker(path: Path) -> bool:
    return (
        path.name in _PACKAGE_MARKER_NAMES
        or (path.name.startswith("requirements") and path.suffix == ".txt")
        or path.suffix.lower() in _PACKAGE_MARKER_SUFFIXES
    )


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


def _contains_src_lib_segment(path: Path) -> bool:
    parts = path.parts
    return any(
        part == "src" and index + 1 < len(parts) and parts[index + 1] == "lib"
        for index, part in enumerate(parts)
    )


def _is_root_unanchored_lib_directory_rule(rule: _GitignoreRule | None) -> bool:
    return (
        rule is not None
        and rule.base == ""
        and rule.pattern == "lib"
        and not rule.negated
        and rule.directory_only
        and not rule.anchored
    )


def _last_directory_ignore_rule(
    matcher: GitIgnoreMatcher, rel_path: str
) -> _GitignoreRule | None:
    rel_path = rel_path.strip("/")
    return matcher.last_matching_rule(f"{rel_path}/__llm_wiki_dir__")


def _is_rescuable_typescript_src_lib_directory(
    matcher: GitIgnoreMatcher, rel_dir: Path
) -> bool:
    if not _contains_src_lib_segment(rel_dir):
        return False
    return _is_root_unanchored_lib_directory_rule(
        _last_directory_ignore_rule(matcher, rel_dir.as_posix())
    )


def _is_rescuable_typescript_src_lib_file(
    matcher: GitIgnoreMatcher,
    rel: Path,
    language: str | None,
) -> bool:
    if language != "typescript" or not _contains_src_lib_segment(rel):
        return False
    return _is_root_unanchored_lib_directory_rule(
        matcher.last_matching_rule(rel.as_posix())
    )


def _empty_source_snapshot(root: Path) -> SourceSnapshot:
    return SourceSnapshot(
        root=root,
        files_by_language={language: () for language in LANGUAGE_EXTENSIONS},
        dockerfile_candidates=(),
        compose_candidates=(),
        yaml_candidates=(),
        package_markers=(),
        unsupported_files_by_language={
            language: ()
            for language in (
                tuple(KNOWN_UNSUPPORTED_LANGUAGE_EXTENSIONS)
                + _ADVISORY_UNSUPPORTED_LANGUAGES
            )
        },
        all_source_paths=(),
        gitignore_fingerprint=_sha256_labeled_files([]),
    )


def _relative_to_root(path: Path, root: Path) -> Path | None:
    try:
        return path.resolve().relative_to(root)
    except (OSError, ValueError):
        return None


def _is_excluded_walk_directory(rel_dir: Path, only_set: set[str] | None) -> bool:
    if rel_dir == Path("."):
        return False
    if not EXCLUDED_DIRS.isdisjoint(rel_dir.parts):
        return True
    rel_posix = rel_dir.as_posix()
    return is_agent_worktree_path(rel_posix) and not _only_set_contains_path_under(
        only_set, rel_posix
    )


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


def _only_set_contains_path_under(only_set: set[str] | None, rel_path: str) -> bool:
    if only_set is None:
        return False
    normalized = rel_path.strip("/")
    prefix = f"{normalized}/" if normalized else ""
    return any(path == normalized or path.startswith(prefix) for path in only_set)


def _prune_dirnames(
    dirnames: list[str],
    rel_dir: Path,
    matcher: GitIgnoreMatcher,
    only_set: set[str] | None,
) -> None:
    kept_dirnames = []
    for name in dirnames:
        if name in EXCLUDED_DIRS:
            continue
        child_rel = name if rel_dir == Path(".") else (rel_dir / name).as_posix()
        child_is_agent_worktree = is_agent_worktree_path(child_rel)
        if child_is_agent_worktree and not _only_set_contains_path_under(
            only_set, child_rel
        ):
            continue
        if _directory_ignored(matcher, child_rel) and not _only_set_contains_path_under(
            only_set, child_rel
        ):
            if not _is_rescuable_typescript_src_lib_directory(matcher, Path(child_rel)):
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
    language = _language_for_path(resolved, buckets.include_tests)
    if language is None:
        return

    rel_posix = rel.as_posix()
    if only_set is not None and rel_posix not in only_set:
        return

    source_file = _make_source_file(root, resolved, rel, language)
    _append_sorted(buckets.files_by_language[language], source_file)


def _record_unsupported_language_candidate(
    root: Path,
    resolved: Path,
    rel: Path,
    only_set: set[str] | None,
    buckets: _SnapshotBuckets,
) -> None:
    language = _unsupported_language_for_path(resolved)
    if language is None:
        return

    rel_posix = rel.as_posix()
    if only_set is not None and rel_posix not in only_set:
        return

    source_file = _make_source_file(root, resolved, rel, language)
    _append_sorted(buckets.unsupported_files_by_language[language], source_file)


def _record_generated_javascript_bundle_candidate(
    root: Path,
    resolved: Path,
    rel: Path,
    only_set: set[str] | None,
    buckets: _SnapshotBuckets,
) -> bool:
    rel_posix = rel.as_posix()
    if only_set is not None or not is_generated_javascript_bundle_path(rel_posix):
        return False

    source_file = _make_source_file(
        root,
        resolved,
        rel,
        GENERATED_JAVASCRIPT_BUNDLE_LANGUAGE,
    )
    _append_sorted(
        buckets.unsupported_files_by_language[GENERATED_JAVASCRIPT_BUNDLE_LANGUAGE],
        source_file,
    )
    return True


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
    rel_posix = rel.as_posix()
    if not resolved.is_file() or not EXCLUDED_DIRS.isdisjoint(rel.parts):
        return
    if is_agent_worktree_path(rel_posix) and (
        only_set is None or rel_posix not in only_set
    ):
        return

    package_source_file = _make_source_file(root, resolved, rel, None)
    if _is_package_marker(resolved):
        _append_sorted(buckets.package_markers, package_source_file)

    language = _language_for_path(resolved, buckets.include_tests)
    if matcher.is_ignored(rel_posix) and (
        only_set is None or rel_posix not in only_set
    ):
        if not _is_rescuable_typescript_src_lib_file(matcher, rel, language):
            return

    _record_infrastructure_candidates(resolved, package_source_file, buckets)
    if _record_generated_javascript_bundle_candidate(
        root, resolved, rel, only_set, buckets
    ):
        return
    _record_language_candidate(root, resolved, rel, only_set, buckets)
    _record_unsupported_language_candidate(root, resolved, rel, only_set, buckets)


def _collect_source_tree(
    root: Path, only_set: set[str] | None, buckets: _SnapshotBuckets
) -> None:
    for dirpath, dirnames, filenames in os.walk(root, topdown=True, followlinks=False):
        current_dir = Path(dirpath)
        rel_dir = _relative_to_root(current_dir, root)
        if rel_dir is None or _is_excluded_walk_directory(rel_dir, only_set):
            dirnames[:] = []
            continue

        _record_gitignore_rules(root, current_dir, rel_dir, buckets)
        matcher = GitIgnoreMatcher(buckets.gitignore_rules)
        _prune_dirnames(dirnames, rel_dir, matcher, only_set)

        for filename in filenames:
            _record_source_file(root, current_dir, filename, matcher, only_set, buckets)


def _build_source_snapshot(root: Path, buckets: _SnapshotBuckets) -> SourceSnapshot:
    sorted_languages = {
        language: tuple(sorted(source_files, key=lambda item: item.rel_path))
        for language, source_files in buckets.files_by_language.items()
    }
    sorted_unsupported_languages = {
        language: tuple(sorted(source_files, key=lambda item: item.rel_path))
        for language, source_files in buckets.unsupported_files_by_language.items()
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
        unsupported_files_by_language=sorted_unsupported_languages,
        all_source_paths=all_source_paths,
        gitignore_fingerprint=_sha256_labeled_files(buckets.gitignore_paths),
    )


def unsupported_source_summary(
    snapshot: SourceSnapshot, *, supported_languages: Iterable[str] = ()
) -> dict[str, dict[str, object]]:
    """Return nonempty unsupported source counts and paths.

    ``supported_languages`` lets command paths suppress advisory unsupported
    coverage once a plugin or built-in extractor for that language is active.
    """
    supported = set(supported_languages)
    summary: dict[str, dict[str, object]] = {}
    for language, source_files in sorted(
        snapshot.unsupported_files_by_language.items()
    ):
        if language in supported or not source_files:
            continue
        paths = [source_file.rel_path for source_file in source_files]
        summary[language] = {"count": len(paths), "paths": paths}
    return summary


def format_unsupported_source_summary(summary: dict[str, dict[str, object]]) -> str:
    """Return a concise human-readable unsupported-source summary."""
    if not summary:
        return ""
    counts = ", ".join(
        _format_unsupported_language_count(language, data)
        for language, data in sorted(summary.items())
    )
    return f"Unsupported sources detected: {counts}"


def unsupported_source_label(language: str) -> str:
    """Return the human-readable label for an unsupported source bucket."""
    return _UNSUPPORTED_LANGUAGE_LABELS.get(language, language)


def _format_unsupported_language_count(language: str, data: dict[str, object]) -> str:
    label = unsupported_source_label(language)
    raw_paths = data.get("paths", [])
    paths = (
        [str(path) for path in raw_paths if path] if isinstance(raw_paths, list) else []
    )
    raw_count = data.get("count")
    count = raw_count if isinstance(raw_count, int) else len(paths)
    if not paths:
        return f"{label}={count}"
    shown = paths[:_UNSUPPORTED_SUMMARY_PATH_LIMIT]
    suffix = ""
    if count > len(shown):
        suffix = f", +{count - len(shown)} more"
    return f"{label}={count} ({', '.join(shown)}{suffix})"


def build_source_snapshot(
    src_dir: str | Path,
    only_files: Iterable[str] | None = None,
    include_tests: Iterable[str] | None = None,
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

    buckets = _new_snapshot_buckets(include_tests)
    _collect_source_tree(root, only_set, buckets)
    return _build_source_snapshot(root, buckets)
