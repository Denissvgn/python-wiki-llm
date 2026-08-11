"""Shared source-tree discovery for inventory, Docker, and package scans."""

from __future__ import annotations

import hashlib
import os
import stat
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from fnmatch import fnmatch
from pathlib import Path
from typing import TYPE_CHECKING

from ..config import (
    COMPOSE_PATTERNS,
    DOCKERFILE_PATTERNS,
    EXCLUDED_DIRS,
    GitIgnoreMatcher,
    _GitignoreRule,
    _parse_gitignore_text,
    is_agent_worktree_path,
)
from ..extractors.common import (
    GENERATED_JAVASCRIPT_BUNDLE_LANGUAGE,
    LANGUAGE_EXTENSIONS,
    is_bundled_helper_implementation_path,
    is_generated_javascript_bundle_path,
    normalize_include_tests,
)
from .source_selection import (
    SOURCE_SELECTION_INPUTS_SCHEMA_VERSION,
    SOURCE_SELECTION_PATH,
    SourceSelectionError,
    SourceSelectionPolicy,
    locate_exact_repository_path,
    path_is_link_or_reparse,
    path_is_selected,
    resolve_source_selection,
    selection_may_contain_path,
)
from .validation import portable_path_key, require_repository_relative_path

if TYPE_CHECKING:
    from .knowledge_envelope import ConsumedInput

_DOC_SUFFIXES = {".md", ".txt", ".rst", ".html", ".json"}
_PACKAGE_MARKER_NAMES = {
    "Cargo.lock",
    "Cargo.toml",
    "Pipfile",
    "Pipfile.lock",
    "cabal.project",
    "flake.nix",
    "go.mod",
    "go.sum",
    "package-lock.json",
    "package.json",
    "pnpm-lock.yaml",
    "poetry.lock",
    "pyproject.toml",
    "setup.py",
    "stack.yaml",
    "tsconfig.json",
    "uv.lock",
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
_SOURCE_INPUT_KIND = "source"
_DOCKER_INPUT_KIND = "docker"
_COMPOSE_INPUT_KIND = "compose"
_YAML_INPUT_KIND = "yaml"
_PACKAGE_INPUT_KIND = "package"
_SELECTION_INPUT_KIND = "selection"
_INPUT_KIND_ORDER = (
    _COMPOSE_INPUT_KIND,
    _DOCKER_INPUT_KIND,
    _PACKAGE_INPUT_KIND,
    _SELECTION_INPUT_KIND,
    _YAML_INPUT_KIND,
    _SOURCE_INPUT_KIND,
)
_UNSET_EXPECTED_SELECTION_INPUTS = object()


class SourceSnapshotError(ValueError):
    """Field-specific failure selecting captured source snapshot state."""

    def __init__(self, field: str, message: str):
        self.field = field
        self.message = message
        super().__init__(f"{field}: {message}")


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
class SourceFileIntegrity:
    """Filesystem identity used for cheap between-stage mutation checks."""

    device: int
    inode: int
    mode_type: int
    size: int
    mtime_ns: int
    ctime_ns: int


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
    captured_content_hashes: dict[str, str]
    captured_input_kinds: dict[str, tuple[str, ...]]
    source_selection_policy: SourceSelectionPolicy | None = None
    selected_regular_paths: frozenset[str] = frozenset()
    gitignore_rules: tuple[_GitignoreRule, ...] = ()
    include_tests: frozenset[str] = frozenset()
    only_files: frozenset[str] | None = None
    captured_file_integrity: dict[str, SourceFileIntegrity] = field(
        default_factory=dict
    )
    captured_gitignore_paths: frozenset[str] = frozenset()

    @property
    def source_selection_path(self) -> str | None:
        """Return the repository-relative policy path, when configured."""
        policy = self.source_selection_policy
        return None if policy is None else policy.path

    @property
    def source_selection_origin(self) -> str | None:
        """Return whether selection was discovered by default or explicitly."""
        policy = self.source_selection_policy
        return None if policy is None else policy.origin

    @property
    def source_selection_fingerprint(self) -> str | None:
        """Return the semantic policy fingerprint, when configured."""
        policy = self.source_selection_policy
        return None if policy is None else policy.fingerprint

    @property
    def source_selection_identity(self) -> dict[str, str] | None:
        """Return the canonical persisted policy identity, when configured."""
        policy = self.source_selection_policy
        return None if policy is None else policy.identity

    @property
    def source_selection_inputs(self) -> dict[str, object] | None:
        """Return exact configured profile/gitignore content commitments."""

        if self.source_selection_policy is None:
            return None
        inputs = [
            {
                "path": path,
                "content_hash": self.captured_content_hashes[path],
            }
            for path, kinds in sorted(self.captured_input_kinds.items())
            if _SELECTION_INPUT_KIND in kinds
        ]
        return {
            "schema_version": SOURCE_SELECTION_INPUTS_SCHEMA_VERSION,
            "inputs": inputs,
        }

    def path_is_effectively_selected(self, path: str) -> bool:
        """Evaluate configured selection rules for an existing or missing path.

        ``selected_regular_paths`` is the finite, readable boundary for live
        reads.  This predicate intentionally omits the existence requirement so
        Git deletions can still be classified without re-admitting ignored,
        globally excluded, agent-worktree, or bundled-helper paths.
        """

        normalized = _validate_repository_path(path, "selected_path")
        policy = self.source_selection_policy
        if policy is None:
            return True
        if normalized == policy.path or not path_is_selected(policy, normalized):
            return False
        relative = Path(normalized)
        if not EXCLUDED_DIRS.isdisjoint(relative.parts):
            return False
        if is_agent_worktree_path(normalized):
            return False
        if is_bundled_helper_implementation_path(self.root / relative):
            return False
        matcher = GitIgnoreMatcher(list(self.gitignore_rules))
        ignored = matcher.is_ignored(normalized)
        language = _language_for_path(relative, frozenset())
        return not ignored or _is_rescuable_typescript_src_lib_file(
            matcher,
            relative,
            language,
        )

    def path_may_contain_effective_selection(self, path: str) -> bool:
        """Return whether a directory remains reachable by the live rules."""

        normalized = path.replace("\\", "/").strip("/")
        if normalized in {"", "."}:
            return True
        normalized = _validate_repository_path(normalized, "selected_directory")
        policy = self.source_selection_policy
        if policy is None:
            return True
        if not selection_may_contain_path(policy, normalized):
            return False
        relative = Path(normalized)
        if not EXCLUDED_DIRS.isdisjoint(relative.parts):
            return False
        if is_agent_worktree_path(normalized):
            return False
        matcher = GitIgnoreMatcher(list(self.gitignore_rules))
        return not _directory_ignored(
            matcher,
            normalized,
        ) or _is_rescuable_typescript_src_lib_directory(matcher, relative)

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

    def hashes_for(self, paths: Iterable[str] | None = None) -> dict[str, str]:
        """Return a validated copy of captured exact hashes without file I/O.

        When *paths* is provided, every requested path must be normalized,
        unique, and present in this snapshot. This makes the result safe to
        pass to consumers that require exact inventory coverage.
        """

        if paths is None:
            selected = tuple(sorted(self.captured_content_hashes))
        else:
            if isinstance(paths, (str, bytes)):
                raise SourceSnapshotError(
                    "captured_paths",
                    "must be an iterable of repository-relative paths",
                )
            selected_values: list[str] = []
            seen: set[str] = set()
            for index, path in enumerate(paths):
                normalized = _validate_repository_path(
                    path,
                    f"captured_paths[{index}]",
                )
                if normalized in seen:
                    raise SourceSnapshotError(
                        f"captured_paths[{index}]",
                        f"duplicates repository path {normalized!r}",
                    )
                seen.add(normalized)
                selected_values.append(normalized)
            selected = tuple(sorted(selected_values))

        for index, path in enumerate(selected):
            if path not in self.captured_content_hashes:
                raise SourceSnapshotError(
                    f"captured_paths[{index}]",
                    f"has no exact captured content hash for {path!r}",
                )
        return {path: self.captured_content_hashes[path] for path in selected}

    def to_consumed_inputs(
        self,
        paths: Iterable[str] | None = None,
    ) -> tuple[ConsumedInput, ...]:
        """Return canonical consumed inputs from already captured hashes."""

        from .knowledge_envelope import consumed_inputs_from_captured_hashes

        content_hashes = self.hashes_for(paths)
        candidate_kinds = {
            path: self.captured_input_kinds[path] for path in content_hashes
        }
        return consumed_inputs_from_captured_hashes(
            content_hashes,
            candidate_kinds,
        )

    def with_captured_inventory_paths(
        self,
        paths: Iterable[str],
    ) -> SourceSnapshot:
        """Commit extractor-returned paths absent from built-in discovery.

        Plugin extractors may own extensions unknown to the built-in language
        registry. The extractor result already supplies the exact finite path
        set, so this boundary reads only those missing files and never performs
        another tree walk or invokes an extractor.
        """

        content_hashes = dict(self.captured_content_hashes)
        input_kinds = dict(self.captured_input_kinds)
        file_integrity = dict(self.captured_file_integrity)
        all_source_paths = set(self.all_source_paths)
        portable_paths = {
            portable_path_key(path): path for path in self.selected_regular_paths
        }
        root = self.root.resolve()
        for index, raw_path in enumerate(paths):
            path = _validate_repository_path(
                raw_path,
                f"inventory_paths[{index}]",
            )
            if self.source_selection_policy is not None:
                if path == self.source_selection_policy.path or not path_is_selected(
                    self.source_selection_policy, path
                ):
                    continue
            if path in content_hashes:
                continue
            key = portable_path_key(path)
            previous = portable_paths.setdefault(key, path)
            if previous != path:
                raise SourceSnapshotError(
                    f"inventory_paths[{index}]",
                    "collides across supported filesystems with "
                    f"{previous!r}: {path!r}",
                )
            candidate = root / path
            if is_bundled_helper_implementation_path(candidate):
                continue
            if self.source_selection_policy is not None:
                try:
                    exact_candidate = locate_exact_repository_path(root, path)
                except SourceSelectionError as exc:
                    raise SourceSnapshotError(
                        f"inventory_paths[{index}]",
                        "must not traverse a symlink or reparse point and must "
                        f"use exact filesystem case: {path!r}",
                    ) from exc
                if exact_candidate is None:
                    raise SourceSnapshotError(
                        f"inventory_paths[{index}]",
                        f"must use exact filesystem case for a selected file: {path!r}",
                    )
                candidate = exact_candidate
                if path not in self.selected_regular_paths:
                    continue
            try:
                resolved = candidate.resolve(strict=True)
                resolved.relative_to(root)
            except (OSError, ValueError) as exc:
                raise SourceSnapshotError(
                    f"inventory_paths[{index}]",
                    f"must resolve to a readable file inside the source root: {path!r}",
                ) from exc
            if is_bundled_helper_implementation_path(resolved):
                continue
            content_hash = _sha256_file(resolved)
            if content_hash is None or not resolved.is_file():
                raise SourceSnapshotError(
                    f"inventory_paths[{index}]",
                    f"must resolve to a readable file inside the source root: {path!r}",
                )
            content_hashes[path] = content_hash
            input_kinds[path] = ("source",)
            integrity = _source_file_integrity(resolved)
            if integrity is None:
                raise SourceSnapshotError(
                    f"inventory_paths[{index}]",
                    f"changed during capture: {path!r}",
                )
            file_integrity[path] = integrity
            all_source_paths.add(path)
        return SourceSnapshot(
            root=self.root,
            files_by_language=self.files_by_language,
            dockerfile_candidates=self.dockerfile_candidates,
            compose_candidates=self.compose_candidates,
            yaml_candidates=self.yaml_candidates,
            package_markers=self.package_markers,
            unsupported_files_by_language=self.unsupported_files_by_language,
            all_source_paths=tuple(sorted(all_source_paths)),
            gitignore_fingerprint=self.gitignore_fingerprint,
            captured_content_hashes=content_hashes,
            captured_input_kinds=input_kinds,
            source_selection_policy=self.source_selection_policy,
            selected_regular_paths=self.selected_regular_paths,
            gitignore_rules=self.gitignore_rules,
            include_tests=self.include_tests,
            only_files=self.only_files,
            captured_file_integrity=file_integrity,
            captured_gitignore_paths=self.captured_gitignore_paths,
        )


@dataclass
class _SnapshotBuckets:
    files_by_language: dict[str, list[SourceFile]]
    dockerfile_candidates: list[SourceFile]
    compose_candidates: list[SourceFile]
    yaml_candidates: list[SourceFile]
    package_markers: list[SourceFile]
    unsupported_files_by_language: dict[str, list[SourceFile]]
    gitignore_contents: dict[str, bytes | None]
    gitignore_rules: list[_GitignoreRule]
    include_tests: frozenset[str]
    source_selection_policy: SourceSelectionPolicy | None
    selected_regular_paths: set[str]
    expected_gitignore_paths: frozenset[str] | None


def _new_snapshot_buckets(
    include_tests: Iterable[str] | None = None,
    source_selection_policy: SourceSelectionPolicy | None = None,
    *,
    expected_gitignore_paths: frozenset[str] | None = None,
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
        gitignore_contents={},
        gitignore_rules=[],
        include_tests=normalize_include_tests(include_tests),
        source_selection_policy=source_selection_policy,
        selected_regular_paths=set(),
        expected_gitignore_paths=expected_gitignore_paths,
    )


def _validate_repository_path(value: object, field: str) -> str:
    return require_repository_relative_path(
        value,
        text_error=SourceSnapshotError(
            field, "must be a non-empty repository-relative path"
        ),
        posix_error=SourceSnapshotError(
            field, "must be a repository-relative POSIX path"
        ),
        normalized_error=SourceSnapshotError(
            field, "must be a normalized repository-relative path"
        ),
    )


def _normalize_only_files(
    root: Path, only_files: Iterable[str] | None
) -> set[str] | None:
    if only_files is None:
        return None

    normalized: set[str] = set()
    for raw_path in only_files:
        candidate = root / raw_path
        if is_bundled_helper_implementation_path(candidate):
            continue
        try:
            resolved = candidate.resolve()
            rel = resolved.relative_to(root)
        except (OSError, ValueError):
            continue
        if is_bundled_helper_implementation_path(resolved):
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


def _sha256_bytes(content: bytes) -> str:
    return "sha256:" + hashlib.sha256(content).hexdigest()


def _sha256_file(path: Path) -> str | None:
    try:
        hasher = hashlib.sha256()
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                hasher.update(chunk)
    except OSError:
        return None
    return "sha256:" + hasher.hexdigest()


def _source_file_integrity(path: Path) -> SourceFileIntegrity | None:
    try:
        current = path.stat()
    except OSError:
        return None
    if not stat.S_ISREG(current.st_mode):
        return None
    return SourceFileIntegrity(
        device=current.st_dev,
        inode=current.st_ino,
        mode_type=stat.S_IFMT(current.st_mode),
        size=current.st_size,
        mtime_ns=current.st_mtime_ns,
        ctime_ns=current.st_ctime_ns,
    )


def _captured_file_integrity(
    root: Path,
    content_hashes: Mapping[str, str],
) -> dict[str, SourceFileIntegrity]:
    result: dict[str, SourceFileIntegrity] = {}
    for path in sorted(content_hashes):
        current = _source_file_integrity(root / path)
        if current is not None:
            result[path] = current
    return result


def _sha256_labeled_contents(contents: Mapping[str, bytes | None]) -> str:
    hasher = hashlib.sha256()
    for label, content in sorted(contents.items()):
        hasher.update(label.replace("\\", "/").encode("utf-8"))
        hasher.update(b"\0")
        if content is None:
            hasher.update(b"<unreadable>")
        else:
            hasher.update(content)
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


def _empty_source_snapshot(
    root: Path,
    source_selection_policy: SourceSelectionPolicy | None = None,
    *,
    include_tests: frozenset[str] = frozenset(),
    only_files: frozenset[str] | None = None,
) -> SourceSnapshot:
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
        gitignore_fingerprint=_sha256_labeled_contents({}),
        captured_content_hashes={},
        captured_input_kinds={},
        source_selection_policy=source_selection_policy,
        selected_regular_paths=frozenset(),
        gitignore_rules=(),
        include_tests=include_tests,
        only_files=only_files,
        captured_file_integrity={},
        captured_gitignore_paths=frozenset(),
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
    policy = buckets.source_selection_policy
    if policy is None:
        if path_is_link_or_reparse(gitignore):
            raise SourceSnapshotError(
                "gitignore",
                "ignore controls must not be symlinks or reparse points: "
                f"{gitignore.relative_to(root).as_posix()!r}",
            )
        if not gitignore.is_file():
            return
        base = "" if rel_dir == Path(".") else rel_dir.as_posix()
        rel_path = gitignore.relative_to(root).as_posix()
        if (
            buckets.expected_gitignore_paths is not None
            and rel_path not in buckets.expected_gitignore_paths
        ):
            raise SourceSnapshotError(
                "gitignore",
                f"new ignore control appeared during verification: {rel_path!r}",
            )
        try:
            content = gitignore.read_bytes()
        except OSError:
            content = None
        buckets.gitignore_contents[rel_path] = content
        if content is not None:
            buckets.gitignore_rules.extend(
                _parse_gitignore_text(content.decode("utf-8"), base)
            )
        return

    rel_path = gitignore.relative_to(root).as_posix()
    try:
        metadata = gitignore.lstat()
    except FileNotFoundError:
        return
    except OSError as exc:
        raise SourceSnapshotError(
            "source_selection",
            f"cannot inspect applicable selection input: {rel_path!r}",
        ) from exc
    if path_is_link_or_reparse(gitignore):
        rel_path = gitignore.relative_to(root).as_posix()
        raise SourceSnapshotError(
            "source_selection",
            f"applicable selection input must not be a symlink or reparse "
            f"point: {rel_path!r}",
        )
    if not stat.S_ISREG(metadata.st_mode):
        return
    if (
        buckets.expected_gitignore_paths is not None
        and rel_path not in buckets.expected_gitignore_paths
    ):
        raise SourceSnapshotError(
            "source_selection",
            f"new applicable selection input appeared during verification: {rel_path!r}",
        )

    base = "" if rel_dir == Path(".") else rel_dir.as_posix()
    try:
        content = gitignore.read_bytes()
    except OSError as exc:
        raise SourceSnapshotError(
            "source_selection",
            f"cannot read applicable selection input: {rel_path!r}",
        ) from exc
    buckets.gitignore_contents[rel_path] = content
    try:
        buckets.gitignore_rules.extend(
            _parse_gitignore_text(content.decode("utf-8"), base)
        )
    except UnicodeDecodeError as exc:
        raise SourceSnapshotError(
            "source_selection",
            f"applicable selection input must contain UTF-8 text: {rel_path!r}",
        ) from exc


def _only_set_contains_path_under(only_set: set[str] | None, rel_path: str) -> bool:
    if only_set is None:
        return False
    normalized = rel_path.strip("/")
    prefix = f"{normalized}/" if normalized else ""
    return any(path == normalized or path.startswith(prefix) for path in only_set)


def _prune_dirnames(
    root: Path,
    dirnames: list[str],
    rel_dir: Path,
    matcher: GitIgnoreMatcher,
    only_set: set[str] | None,
    buckets: _SnapshotBuckets,
) -> None:
    kept_dirnames = []
    for name in dirnames:
        if name in EXCLUDED_DIRS:
            continue
        child_rel = name if rel_dir == Path(".") else (rel_dir / name).as_posix()
        policy = buckets.source_selection_policy
        if policy is not None:
            try:
                if not selection_may_contain_path(policy, child_rel):
                    continue
            except SourceSelectionError as exc:
                raise SourceSnapshotError(
                    "source_selection",
                    f"selected directory is not portable: {child_rel!r}",
                ) from exc
        child_is_agent_worktree = is_agent_worktree_path(child_rel)
        if child_is_agent_worktree and (
            policy is not None
            or not _only_set_contains_path_under(only_set, child_rel)
        ):
            continue
        if policy is not None and path_is_link_or_reparse(root / child_rel):
            raise SourceSnapshotError(
                "source_selection",
                f"selected directory must not be a symlink or reparse point: "
                f"{child_rel!r}",
            )
        if (
            _directory_ignored(matcher, child_rel)
            and (
                policy is not None
                or not _only_set_contains_path_under(only_set, child_rel)
            )
            and not _is_rescuable_typescript_src_lib_directory(matcher, Path(child_rel))
        ):
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
    if is_bundled_helper_implementation_path(resolved):
        return
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
    if is_bundled_helper_implementation_path(path):
        return
    try:
        lexical_rel = path.relative_to(root).as_posix()
    except ValueError:
        return
    policy = buckets.source_selection_policy
    if policy is not None:
        if lexical_rel == policy.path:
            return
        try:
            if not path_is_selected(policy, lexical_rel):
                return
        except SourceSelectionError as exc:
            raise SourceSnapshotError(
                "source_selection",
                f"selected file is not portable: {lexical_rel!r}",
            ) from exc
        if path_is_link_or_reparse(path):
            raise SourceSnapshotError(
                "source_selection",
                f"selected file must not be a symlink or reparse point: "
                f"{lexical_rel!r}",
            )
    rel = _relative_to_root(path, root)
    if rel is None:
        return

    resolved = path.resolve()
    if is_bundled_helper_implementation_path(resolved):
        return
    rel_posix = rel.as_posix()
    if not resolved.is_file() or not EXCLUDED_DIRS.isdisjoint(rel.parts):
        return
    if is_agent_worktree_path(rel_posix) and (
        policy is not None or only_set is None or rel_posix not in only_set
    ):
        return

    package_source_file = _make_source_file(root, resolved, rel, None)
    if policy is None and _is_package_marker(resolved):
        _append_sorted(buckets.package_markers, package_source_file)

    language = _language_for_path(resolved, buckets.include_tests)
    ignored = matcher.is_ignored(rel_posix)
    rescued_typescript = _is_rescuable_typescript_src_lib_file(
        matcher, rel, language
    )
    if (
        ignored
        and (
            policy is not None
            or only_set is None
            or rel_posix not in only_set
        )
        and not rescued_typescript
    ):
        return

    if policy is not None and (not ignored or rescued_typescript):
        if filename != ".gitignore":
            buckets.selected_regular_paths.add(rel_posix)
        if policy is not None and _is_package_marker(resolved):
            _append_sorted(buckets.package_markers, package_source_file)

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
        _prune_dirnames(root, dirnames, rel_dir, matcher, only_set, buckets)

        for filename in filenames:
            _record_source_file(root, current_dir, filename, matcher, only_set, buckets)


def _collect_source_selection_controls(
    root: Path,
    buckets: _SnapshotBuckets,
) -> None:
    """Capture only applicable profile/ignore inputs without reading source files."""

    for dirpath, dirnames, _filenames in os.walk(
        root,
        topdown=True,
        followlinks=False,
    ):
        current_dir = Path(dirpath)
        rel_dir = _relative_to_root(current_dir, root)
        if rel_dir is None or _is_excluded_walk_directory(rel_dir, None):
            dirnames[:] = []
            continue
        _record_gitignore_rules(root, current_dir, rel_dir, buckets)
        matcher = GitIgnoreMatcher(buckets.gitignore_rules)
        _prune_dirnames(root, dirnames, rel_dir, matcher, None, buckets)


def capture_source_selection_inputs(
    src_dir: str | Path,
    *,
    source_selection: str | Path | None = None,
    selection_policy: SourceSelectionPolicy | None = None,
) -> dict[str, object] | None:
    """Capture exact selection-control commitments before any selected-file read."""

    root = Path(src_dir).resolve()
    policy = _resolve_snapshot_selection(
        root,
        source_selection=source_selection,
        selection_policy=selection_policy,
    )
    if policy is None:
        return None
    buckets = _new_snapshot_buckets(None, policy)
    if root.exists():
        _collect_source_selection_controls(root, buckets)
    return _selection_inputs_from_buckets(buckets)


def _selection_inputs_from_buckets(
    buckets: _SnapshotBuckets,
) -> dict[str, object] | None:
    policy = buckets.source_selection_policy
    if policy is None:
        return None
    inputs = [
        {"path": policy.path, "content_hash": policy.raw_content_hash},
        *[
            {"path": path, "content_hash": _sha256_bytes(content)}
            for path, content in sorted(buckets.gitignore_contents.items())
            if content is not None and path != policy.path
        ],
    ]
    return {
        "schema_version": SOURCE_SELECTION_INPUTS_SCHEMA_VERSION,
        "inputs": sorted(inputs, key=lambda item: str(item["path"])),
    }


def _add_captured_input_candidates(
    candidates: dict[str, set[str]],
    source_files: Iterable[SourceFile],
    kind: str,
) -> None:
    for source_file in source_files:
        candidates.setdefault(source_file.rel_path, set()).add(kind)


def _captured_snapshot_candidates(
    *,
    sorted_languages: Mapping[str, tuple[SourceFile, ...]],
    dockerfiles: tuple[SourceFile, ...],
    compose_files: tuple[SourceFile, ...],
    yaml_files: tuple[SourceFile, ...],
    package_markers: tuple[SourceFile, ...],
    gitignore_contents: Mapping[str, bytes | None],
    source_selection_policy: SourceSelectionPolicy | None,
) -> tuple[dict[str, set[str]], dict[str, SourceFile]]:
    candidates: dict[str, set[str]] = {}
    files_by_path: dict[str, SourceFile] = {}

    for source_files in sorted_languages.values():
        _add_captured_input_candidates(candidates, source_files, _SOURCE_INPUT_KIND)
        files_by_path.update((item.rel_path, item) for item in source_files)
    for source_files, kind in (
        (dockerfiles, _DOCKER_INPUT_KIND),
        (compose_files, _COMPOSE_INPUT_KIND),
        (yaml_files, _YAML_INPUT_KIND),
        (package_markers, _PACKAGE_INPUT_KIND),
    ):
        _add_captured_input_candidates(candidates, source_files, kind)
        files_by_path.update((item.rel_path, item) for item in source_files)
    for path, content in gitignore_contents.items():
        if content is not None:
            candidates.setdefault(path, set()).add(_SELECTION_INPUT_KIND)
    if source_selection_policy is not None:
        candidates.setdefault(source_selection_policy.path, set()).add(
            _SELECTION_INPUT_KIND
        )
    return candidates, files_by_path


def _captured_snapshot_inputs(
    *,
    sorted_languages: Mapping[str, tuple[SourceFile, ...]],
    dockerfiles: tuple[SourceFile, ...],
    compose_files: tuple[SourceFile, ...],
    yaml_files: tuple[SourceFile, ...],
    package_markers: tuple[SourceFile, ...],
    gitignore_contents: Mapping[str, bytes | None],
    source_selection_policy: SourceSelectionPolicy | None,
) -> tuple[dict[str, str], dict[str, tuple[str, ...]]]:
    candidates, files_by_path = _captured_snapshot_candidates(
        sorted_languages=sorted_languages,
        dockerfiles=dockerfiles,
        compose_files=compose_files,
        yaml_files=yaml_files,
        package_markers=package_markers,
        gitignore_contents=gitignore_contents,
        source_selection_policy=source_selection_policy,
    )

    content_hashes: dict[str, str] = {}
    input_kinds: dict[str, tuple[str, ...]] = {}
    for path in sorted(candidates):
        gitignore_content = gitignore_contents.get(path)
        if source_selection_policy is not None and path == source_selection_policy.path:
            content_hash = source_selection_policy.raw_content_hash
        elif gitignore_content is not None:
            content_hash = _sha256_bytes(gitignore_content)
        else:
            content_hash = _sha256_file(files_by_path[path].abs_path)
        if content_hash is None:
            continue
        content_hashes[path] = content_hash
        kinds = candidates[path]
        input_kinds[path] = tuple(kind for kind in _INPUT_KIND_ORDER if kind in kinds)
    return content_hashes, input_kinds


def _build_source_snapshot(
    root: Path,
    buckets: _SnapshotBuckets,
    *,
    only_files: frozenset[str] | None,
) -> SourceSnapshot:
    if (
        buckets.source_selection_policy is not None
        and not buckets.selected_regular_paths
    ):
        raise SourceSnapshotError(
            "source_selection",
            "configured selection is effectively empty after ignore and global "
            "source exclusions",
        )
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
    dockerfiles = tuple(
        sorted(buckets.dockerfile_candidates, key=lambda item: item.rel_path)
    )
    compose_files = tuple(
        sorted(buckets.compose_candidates, key=lambda item: item.rel_path)
    )
    yaml_files = tuple(sorted(buckets.yaml_candidates, key=lambda item: item.rel_path))
    package_markers = tuple(
        sorted(buckets.package_markers, key=lambda item: item.rel_path)
    )
    captured_content_hashes, captured_input_kinds = _captured_snapshot_inputs(
        sorted_languages=sorted_languages,
        dockerfiles=dockerfiles,
        compose_files=compose_files,
        yaml_files=yaml_files,
        package_markers=package_markers,
        gitignore_contents=buckets.gitignore_contents,
        source_selection_policy=buckets.source_selection_policy,
    )
    captured_file_integrity = _captured_file_integrity(
        root,
        captured_content_hashes,
    )

    return SourceSnapshot(
        root=root,
        files_by_language=sorted_languages,
        dockerfile_candidates=dockerfiles,
        compose_candidates=compose_files,
        yaml_candidates=yaml_files,
        package_markers=package_markers,
        unsupported_files_by_language=sorted_unsupported_languages,
        all_source_paths=all_source_paths,
        gitignore_fingerprint=_sha256_labeled_contents(buckets.gitignore_contents),
        captured_content_hashes=captured_content_hashes,
        captured_input_kinds=captured_input_kinds,
        source_selection_policy=buckets.source_selection_policy,
        selected_regular_paths=frozenset(buckets.selected_regular_paths),
        gitignore_rules=tuple(buckets.gitignore_rules),
        include_tests=buckets.include_tests,
        only_files=only_files,
        captured_file_integrity=captured_file_integrity,
        captured_gitignore_paths=frozenset(buckets.gitignore_contents),
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


def _policies_match(
    left: SourceSelectionPolicy,
    right: SourceSelectionPolicy,
) -> bool:
    return (
        left.source_root == right.source_root
        and left.path == right.path
        and left.fingerprint == right.fingerprint
        and left.raw_content_hash == right.raw_content_hash
    )


def _resolve_snapshot_selection(
    root: Path,
    *,
    source_selection: str | Path | None,
    selection_policy: SourceSelectionPolicy | None,
) -> SourceSelectionPolicy | None:
    if selection_policy is None:
        return resolve_source_selection(root, source_selection)
    if not isinstance(selection_policy, SourceSelectionPolicy):
        raise SourceSnapshotError(
            "selection_policy", "must be a resolved source-selection policy"
        )
    if selection_policy.source_root != root:
        raise SourceSnapshotError(
            "selection_policy",
            "must be bound to the same resolved source root as the snapshot",
        )
    requested_path: str | Path = (
        selection_policy.path if source_selection is None else source_selection
    )
    try:
        current = resolve_source_selection(root, requested_path)
    except SourceSelectionError as exc:
        raise SourceSnapshotError(
            "selection_policy",
            "does not match a current readable explicit selection file",
        ) from exc
    if current is None or not _policies_match(selection_policy, current):
        raise SourceSnapshotError(
            "selection_policy",
            "does not match the current explicit selection file",
        )
    return selection_policy


def build_source_snapshot(
    src_dir: str | Path,
    only_files: Iterable[str] | None = None,
    include_tests: Iterable[str] | None = None,
    *,
    source_selection: str | Path | None = None,
    selection_policy: SourceSelectionPolicy | None = None,
    expected_selection_inputs: Mapping[str, object] | None | object = (
        _UNSET_EXPECTED_SELECTION_INPUTS
    ),
) -> SourceSnapshot:
    """Build a deterministic source-tree snapshot rooted at *src_dir*.

    Source language files respect ``only_files`` when supplied. Docker,
    Compose, YAML, and package-marker candidates still cover the full source
    tree so command paths that restrict source extraction preserve their
    existing infrastructure and package behavior.
    """
    root = Path(src_dir).resolve()
    policy = _resolve_snapshot_selection(
        root,
        source_selection=source_selection,
        selection_policy=selection_policy,
    )
    only_set = _normalize_only_files(root, only_files)
    normalized_only_files = None if only_set is None else frozenset(only_set)
    normalized_include_tests = normalize_include_tests(include_tests)

    if not root.exists():
        return _empty_source_snapshot(
            root,
            policy,
            include_tests=normalized_include_tests,
            only_files=normalized_only_files,
        )

    buckets = _new_snapshot_buckets(normalized_include_tests, policy)
    _collect_source_tree(root, only_set, buckets)
    if expected_selection_inputs is not _UNSET_EXPECTED_SELECTION_INPUTS:
        current_inputs = _selection_inputs_from_buckets(buckets)
        if current_inputs != expected_selection_inputs:
            raise SourceSnapshotError(
                "source_selection",
                "applicable source-selection inputs changed during snapshot capture",
            )
    return _build_source_snapshot(
        root,
        buckets,
        only_files=normalized_only_files,
    )


def _hash_extra_inventory_path(
    root: Path,
    path: str,
    *,
    policy: SourceSelectionPolicy | None,
    selected_regular_paths: set[str],
) -> str | None:
    """Hash one extractor-owned path without admitting a newly selected path."""

    candidate = root / path
    if policy is not None:
        if path == policy.path or not path_is_selected(policy, path):
            return None
        try:
            exact_candidate = locate_exact_repository_path(root, path)
        except SourceSelectionError:
            return None
        if exact_candidate is None or path not in selected_regular_paths:
            return None
        candidate = exact_candidate
    try:
        resolved = candidate.resolve(strict=True)
        resolved.relative_to(root)
    except (OSError, ValueError):
        return None
    if is_bundled_helper_implementation_path(resolved) or not resolved.is_file():
        return None
    return _sha256_file(resolved)


def source_snapshot_inputs_match_current_files(snapshot: SourceSnapshot) -> bool:
    """Cheaply verify that every already captured input retains its identity.

    This checkpoint performs no tree discovery and no content reads for a
    normally constructed snapshot.  It compares the captured regular files'
    filesystem identity, type, size, and high-resolution change timestamps.
    The final structural verifier still re-hashes exact contents and detects
    added or newly selected candidates before a packet is returned.

    Snapshots constructed by older/direct callers may lack stat commitments;
    those individual inputs fall back to exact hashing without broadening the
    committed path set.
    """

    if not isinstance(snapshot, SourceSnapshot):
        raise TypeError("snapshot must be a SourceSnapshot")
    root = snapshot.root.resolve()
    for path, expected_hash in snapshot.captured_content_hashes.items():
        expected_integrity = snapshot.captured_file_integrity.get(path)
        if expected_integrity is not None:
            if _source_file_integrity(root / path) != expected_integrity:
                return False
            continue
        if _sha256_file(root / path) != expected_hash:
            return False
    return True


def source_snapshot_matches_current_files(snapshot: SourceSnapshot) -> bool:
    """Return whether *snapshot* still matches the selected source tree.

    This is an integrity verification, not a second semantic snapshot.  It
    walks only the built-in structural selectors, compares those paths before
    hashing, and then re-hashes the exact paths already committed by the
    snapshot (including extractor-owned paths).  It never runs an extractor or
    constructs another :class:`SourceSnapshot`.

    Selection controls and structural candidates are compared before content
    hashing so a changed ignore rule cannot cause a newly admitted file to be
    read during verification.
    """

    if not isinstance(snapshot, SourceSnapshot):
        raise TypeError("snapshot must be a SourceSnapshot")
    root = snapshot.root.resolve()
    if snapshot.source_selection_policy is None:
        try:
            newly_configured = locate_exact_repository_path(
                root,
                SOURCE_SELECTION_PATH,
            )
        except SourceSelectionError:
            return False
        if newly_configured is not None:
            return False
        policy = None
    else:
        policy = _resolve_snapshot_selection(
            root,
            source_selection=None,
            selection_policy=snapshot.source_selection_policy,
        )
        if policy is None or not _policies_match(
            snapshot.source_selection_policy,
            policy,
        ):
            return False

    buckets = _new_snapshot_buckets(
        snapshot.include_tests,
        policy,
        expected_gitignore_paths=snapshot.captured_gitignore_paths,
    )
    if root.exists():
        _collect_source_tree(
            root,
            None if snapshot.only_files is None else set(snapshot.only_files),
            buckets,
        )
    if policy is not None and not buckets.selected_regular_paths:
        return False
    if _selection_inputs_from_buckets(buckets) != snapshot.source_selection_inputs:
        return False

    sorted_languages = {
        language: tuple(sorted(files, key=lambda item: item.rel_path))
        for language, files in buckets.files_by_language.items()
    }
    sorted_unsupported = {
        language: tuple(sorted(files, key=lambda item: item.rel_path))
        for language, files in buckets.unsupported_files_by_language.items()
    }
    dockerfiles = tuple(
        sorted(buckets.dockerfile_candidates, key=lambda item: item.rel_path)
    )
    compose_files = tuple(
        sorted(buckets.compose_candidates, key=lambda item: item.rel_path)
    )
    yaml_files = tuple(sorted(buckets.yaml_candidates, key=lambda item: item.rel_path))
    package_markers = tuple(
        sorted(buckets.package_markers, key=lambda item: item.rel_path)
    )

    def paths(items: Iterable[SourceFile]) -> tuple[str, ...]:
        return tuple(item.rel_path for item in items)

    if {
        language: paths(files) for language, files in sorted_languages.items()
    } != {
        language: paths(files)
        for language, files in snapshot.files_by_language.items()
    }:
        return False
    if {
        language: paths(files) for language, files in sorted_unsupported.items()
    } != {
        language: paths(files)
        for language, files in snapshot.unsupported_files_by_language.items()
    }:
        return False
    if paths(dockerfiles) != paths(snapshot.dockerfile_candidates):
        return False
    if paths(compose_files) != paths(snapshot.compose_candidates):
        return False
    if paths(yaml_files) != paths(snapshot.yaml_candidates):
        return False
    if paths(package_markers) != paths(snapshot.package_markers):
        return False
    if (
        _sha256_labeled_contents(buckets.gitignore_contents)
        != snapshot.gitignore_fingerprint
    ):
        return False
    if frozenset(buckets.selected_regular_paths) != snapshot.selected_regular_paths:
        return False

    candidates, _files_by_path = _captured_snapshot_candidates(
        sorted_languages=sorted_languages,
        dockerfiles=dockerfiles,
        compose_files=compose_files,
        yaml_files=yaml_files,
        package_markers=package_markers,
        gitignore_contents=buckets.gitignore_contents,
        source_selection_policy=policy,
    )
    expected_builtin_sources = {
        item.rel_path
        for files in snapshot.files_by_language.values()
        for item in files
    }
    extra_inventory_paths = set(snapshot.all_source_paths) - expected_builtin_sources
    current_all_source_paths = {
        item.rel_path for files in sorted_languages.values() for item in files
    }
    for path in extra_inventory_paths:
        if path in candidates:
            return False
        candidates[path] = {_SOURCE_INPUT_KIND}
        current_all_source_paths.add(path)

    current_input_kinds = {
        path: tuple(kind for kind in _INPUT_KIND_ORDER if kind in kinds)
        for path, kinds in sorted(candidates.items())
    }
    if current_input_kinds != snapshot.captured_input_kinds:
        return False
    if tuple(sorted(current_all_source_paths)) != snapshot.all_source_paths:
        return False

    content_hashes, input_kinds = _captured_snapshot_inputs(
        sorted_languages=sorted_languages,
        dockerfiles=dockerfiles,
        compose_files=compose_files,
        yaml_files=yaml_files,
        package_markers=package_markers,
        gitignore_contents=buckets.gitignore_contents,
        source_selection_policy=policy,
    )
    for path in sorted(extra_inventory_paths):
        content_hash = _hash_extra_inventory_path(
            root,
            path,
            policy=policy,
            selected_regular_paths=buckets.selected_regular_paths,
        )
        if content_hash is None:
            return False
        content_hashes[path] = content_hash
        input_kinds[path] = (_SOURCE_INPUT_KIND,)
    return (
        content_hashes == snapshot.captured_content_hashes
        and input_kinds == snapshot.captured_input_kinds
    )
