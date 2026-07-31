from __future__ import annotations

import json
import os
import posixpath
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import TYPE_CHECKING

from ..config import is_agent_worktree_path
from .validation import (
    path_is_under as shared_path_is_under,
    path_is_under_scope as shared_path_is_under_scope,
)

if TYPE_CHECKING:
    from .source_snapshot import SourceSnapshot


@dataclass(frozen=True)
class _TsPathAliasRule:
    """One ``compilerOptions.paths`` mapping scoped to its tsconfig directory."""

    root: str
    prefix: str
    suffix: str
    wildcard: bool
    targets: tuple[str, ...]


@dataclass(frozen=True)
class _GoModuleScope:
    """One ``go.mod`` module declaration scoped to its directory."""

    root: str
    module: str


@dataclass(frozen=True)
class ModulePathResolver:
    """Indexed module import resolver for a fixed inventory."""

    inventory: dict
    lookup: dict[str, frozenset[str]]
    language_lookup: dict[str, dict[str, frozenset[str]]]
    go_package_lookup: dict[str, frozenset[str]]
    haskell_module_lookup: dict[str, frozenset[str]]
    go_module_scopes: tuple[_GoModuleScope, ...]
    ts_path_aliases: tuple[_TsPathAliasRule, ...]

    @classmethod
    def build(
        cls,
        inventory: dict,
        project_root: str | Path | None = None,
        *,
        source_snapshot: SourceSnapshot | None = None,
    ) -> ModulePathResolver:
        lookup: defaultdict[str, set[str]] = defaultdict(set)
        language_lookup: defaultdict[str, defaultdict[str, set[str]]] = defaultdict(
            lambda: defaultdict(set)
        )
        go_package_lookup: defaultdict[str, set[str]] = defaultdict(set)
        haskell_module_lookup: defaultdict[str, set[str]] = defaultdict(set)
        for filepath, data in inventory.items():
            path = PurePosixPath(filepath)
            path_no_suffix = path.with_suffix("").as_posix()
            path_parts = path.parts
            stripped_src = (
                "/".join(path_parts[1:])
                if path_parts and path_parts[0] == "src"
                else filepath
            )
            stripped_src_no_suffix = Path(stripped_src).with_suffix("").as_posix()
            comparable = {path_no_suffix, stripped_src_no_suffix, path.stem}
            package_paths: set[str] = set()
            if path.name == "__init__.py":
                package_dir = path.parent.as_posix()
                if package_dir != ".":
                    package_paths.add(package_dir)
                stripped_src_path = PurePosixPath(stripped_src)
                stripped_package_dir = stripped_src_path.parent.as_posix()
                if stripped_package_dir != ".":
                    package_paths.add(stripped_package_dir)
            if _is_typescript_index(filepath, data):
                index_dir = path.parent.as_posix()
                if index_dir != ".":
                    package_paths.add(index_dir)

            keys = set(comparable | package_paths)
            keys.update(_suffix_candidates(path_no_suffix))
            keys.update(_suffix_candidates(stripped_src_no_suffix))
            for package_path in package_paths:
                keys.update(_suffix_candidates(package_path))
            language_family = _language_family(data)
            for key in keys:
                if not key:
                    continue
                lookup[key].add(filepath)
                if language_family:
                    language_lookup[language_family][key].add(filepath)
            if _is_go_file(filepath, data):
                go_package_lookup[_package_dir(filepath)].add(filepath)
            if _is_haskell_entry(data):
                module_name = _normalize_haskell_module(data.get("module"))
                if module_name:
                    haskell_module_lookup[module_name].add(filepath)

        return cls(
            inventory=inventory,
            lookup={key: frozenset(value) for key, value in lookup.items()},
            language_lookup={
                language: {
                    key: frozenset(value) for key, value in language_values.items()
                }
                for language, language_values in language_lookup.items()
            },
            go_package_lookup={
                key: frozenset(value) for key, value in go_package_lookup.items()
            },
            haskell_module_lookup={
                key: frozenset(value) for key, value in haskell_module_lookup.items()
            },
            go_module_scopes=_read_go_module_scopes(
                project_root,
                source_snapshot,
            ),
            ts_path_aliases=_read_ts_path_aliases(
                project_root,
                source_snapshot,
            ),
        )

    def candidates(self, module: str, importer_filepath: str) -> set[str]:
        if self._is_go_importer(importer_filepath):
            return self._go_candidates(module, importer_filepath)
        if self._is_haskell_importer(importer_filepath):
            return self._haskell_candidates(module)
        if self._is_typescript_importer(importer_filepath):
            matched, candidate_stems = self._typescript_alias_candidate_stems(
                module, importer_filepath
            )
            if matched:
                return self._candidate_matches(candidate_stems, importer_filepath)

        candidate_stems = _candidate_stems(module, importer_filepath)
        return self._candidate_matches(candidate_stems, importer_filepath)

    def _candidate_matches(
        self, candidate_stems: set[str], importer_filepath: str
    ) -> set[str]:
        lookup = self._lookup_for_importer(importer_filepath)
        matches: set[str] = set()
        for candidate in candidate_stems:
            candidate = candidate.strip("/")
            if candidate:
                matches.update(lookup.get(candidate, ()))
        return matches

    def _lookup_for_importer(self, importer_filepath: str) -> dict[str, frozenset[str]]:
        data = self.inventory.get(importer_filepath)
        language_family = _language_family(data)
        if not language_family:
            return self.lookup
        return self.language_lookup.get(language_family, {})

    def typescript_path_alias_matched(
        self, module: str, importer_filepath: str
    ) -> bool:
        """Return true when *module* matches the importer's nearest tsconfig paths."""
        if not self._is_typescript_importer(importer_filepath):
            return False
        matched, _ = self._typescript_alias_candidate_stems(module, importer_filepath)
        return matched

    def _is_go_importer(self, importer_filepath: str) -> bool:
        data = self.inventory.get(importer_filepath)
        return isinstance(data, dict) and data.get("language") == "go"

    def _is_haskell_importer(self, importer_filepath: str) -> bool:
        data = self.inventory.get(importer_filepath)
        return _is_haskell_entry(data)

    def _is_typescript_importer(self, importer_filepath: str) -> bool:
        data = self.inventory.get(importer_filepath)
        return _is_typescript_entry(data)

    def _go_candidates(self, module: str, importer_filepath: str) -> set[str]:
        normalized = _normalize_module(module)
        if not normalized:
            return set()

        if normalized == "." or normalized.startswith(("./", "../")):
            package_dir = _relative_package_dir(normalized, importer_filepath)
            return set(self.go_package_lookup.get(package_dir, ()))

        nearest = self._nearest_go_scope(importer_filepath)
        if nearest and _path_under(normalized, nearest.module):
            matches = self._go_scope_matches(normalized, nearest)
            if matches:
                return matches

        for scope in sorted(
            self.go_module_scopes,
            key=lambda item: (len(item.module), item.root.count("/"), len(item.root)),
            reverse=True,
        ):
            if scope == nearest or not _path_under(normalized, scope.module):
                continue
            matches = self._go_scope_matches(normalized, scope)
            if matches:
                return matches

        return set()

    def _nearest_go_scope(self, importer_filepath: str) -> _GoModuleScope | None:
        matches = [
            scope
            for scope in self.go_module_scopes
            if _path_under_scope(importer_filepath, scope.root)
        ]
        if not matches:
            return None
        return max(matches, key=lambda item: (item.root.count("/"), len(item.root)))

    def _go_scope_matches(self, module: str, scope: _GoModuleScope) -> set[str]:
        package_dir = _go_package_dir_for_module(module, scope)
        return set(self.go_package_lookup.get(package_dir, ()))

    def _haskell_candidates(self, module: str) -> set[str]:
        normalized = _normalize_haskell_module(module)
        if not normalized:
            return set()
        return set(self.haskell_module_lookup.get(normalized, ()))

    def _typescript_alias_candidate_stems(
        self, module: str, importer_filepath: str
    ) -> tuple[bool, set[str]]:
        normalized = _normalize_module(module)
        if not normalized:
            return False, set()
        root = _nearest_ts_alias_root(self.ts_path_aliases, importer_filepath)
        if root is None:
            return False, set()

        matched = False
        candidate_stems: set[str] = set()
        for rule in self.ts_path_aliases:
            if rule.root != root:
                continue
            star = _match_ts_alias_rule(rule, normalized)
            if star is None:
                continue
            matched = True
            for target in rule.targets:
                candidate_stems.update(_ts_alias_target_stems(target, star))
        return matched, candidate_stems


def _suffix_candidates(path_no_suffix: str) -> set[str]:
    parts = tuple(part for part in path_no_suffix.split("/") if part)
    return {"/".join(parts[index:]) for index in range(1, len(parts))}


def _normalize_module(module: str) -> str:
    return module.strip().strip('"').strip("'").replace("\\", "/")


def _candidate_stems(module: str, importer_filepath: str) -> set[str]:
    if not module:
        return set()

    normalized = _normalize_module(module)
    if not normalized:
        return set()

    importer_parent = Path(importer_filepath).parent
    candidate_stems: set[str] = set()
    has_relative_candidate = False

    if normalized.startswith(("./", "../")):
        rel = normalized
        while rel.startswith("./"):
            rel = rel[2:]
        if rel.startswith("../") or rel:
            candidate_stems.add(
                posixpath.normpath((importer_parent / rel).as_posix()).strip("/")
            )
            has_relative_candidate = True
    elif normalized.startswith("."):
        dot_count = len(normalized) - len(normalized.lstrip("."))
        remainder = normalized[dot_count:]
        base = importer_parent
        for _ in range(max(dot_count - 1, 0)):
            base = base.parent
        if remainder:
            candidate_stems.add(
                posixpath.normpath(
                    (base / remainder.replace(".", "/")).as_posix()
                ).strip("/")
            )
        else:
            base_candidate = posixpath.normpath(base.as_posix()).strip("/")
            if base_candidate:
                candidate_stems.add(base_candidate)
                candidate_stems.add(f"{base_candidate}/__init__")
            else:
                candidate_stems.add("__init__")
        has_relative_candidate = True

    if not has_relative_candidate:
        module_path = normalized.replace("::", "/").replace(".", "/")
        clean_module_path = module_path.strip("/")
        if clean_module_path:
            candidate_stems.add(clean_module_path)
            if "/" not in clean_module_path:
                candidate_stems.add(Path(clean_module_path).name)

    return candidate_stems


def _is_go_file(filepath: str, data: object) -> bool:
    return (
        isinstance(data, dict)
        and data.get("language") == "go"
        and PurePosixPath(filepath).suffix == ".go"
    )


def _language_family(data: object) -> str:
    if not isinstance(data, dict):
        return ""
    language = data.get("language")
    if not isinstance(language, str) or not language:
        return ""
    if language in {"typescript", "javascript"}:
        return "typescript"
    return language


def _is_haskell_entry(data: object) -> bool:
    return isinstance(data, dict) and data.get("language") == "haskell"


def _is_typescript_entry(data: object) -> bool:
    return isinstance(data, dict) and data.get("language") in {
        "typescript",
        "javascript",
    }


def _is_typescript_index(filepath: str, data: object) -> bool:
    return _is_typescript_entry(data) and PurePosixPath(filepath).stem == "index"


def _normalize_haskell_module(module: object) -> str:
    if module is None:
        return ""
    return str(module).strip().strip('"').strip("'").strip()


def _package_dir(filepath: str) -> str:
    package_dir = PurePosixPath(filepath).parent.as_posix()
    return "" if package_dir == "." else package_dir


def _relative_package_dir(module: str, importer_filepath: str) -> str:
    importer_parent = _package_dir(importer_filepath)
    if module == ".":
        return importer_parent
    package_dir = posixpath.normpath(posixpath.join(importer_parent, module))
    return "" if package_dir == "." else package_dir.strip("/")


_GO_MODULE_EXCLUDED_DIRS: frozenset[str] = frozenset(
    {
        ".cache",
        ".git",
        ".hg",
        ".mypy_cache",
        ".pytest_cache",
        ".ruff_cache",
        ".svn",
        ".tox",
        ".venv",
        "__pycache__",
        "build",
        "dist",
        "env",
        "node_modules",
        "site-packages",
        "target",
        "venv",
        "vendor",
    }
)


def _read_go_module_scopes(
    project_root: str | Path | None,
    source_snapshot: SourceSnapshot | None = None,
) -> tuple[_GoModuleScope, ...]:
    if project_root is None:
        return ()
    root = Path(project_root).resolve()
    if not root.exists():
        return ()

    if source_snapshot is None:
        module_paths: list[Path] = []
        for current, dirs, files in os.walk(root):
            current_path = Path(current)
            dirs[:] = [
                d
                for d in dirs
                if d not in _GO_MODULE_EXCLUDED_DIRS
                and not _go_module_dir_is_agent_worktree(root, current_path, d)
            ]
            if "go.mod" in files:
                module_paths.append(current_path / "go.mod")
    else:
        module_paths = _snapshot_marker_paths(
            root,
            source_snapshot,
            "go.mod",
        )

    scopes: list[_GoModuleScope] = []
    for module_path in module_paths:
        module = _read_go_module_path(module_path)
        if module:
            scopes.append(
                _GoModuleScope(
                    root=_project_relative_dir(root, module_path.parent),
                    module=module,
                )
            )

    return tuple(
        sorted(
            scopes, key=lambda item: (item.root.count("/"), len(item.root), item.module)
        )
    )


def _go_module_dir_is_agent_worktree(
    project_root: Path, root_path: Path, dirname: str
) -> bool:
    try:
        rel = (root_path / dirname).relative_to(project_root).as_posix()
    except ValueError:
        return False
    return is_agent_worktree_path(rel)


def _read_go_module_path(path: Path) -> str:
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return ""

    for raw in text.splitlines():
        line = raw.split("//", 1)[0].strip()
        if not line.startswith("module "):
            continue
        tokens = line.split()
        if len(tokens) >= 2:
            return tokens[1].strip('"')
    return ""


def _go_package_dir_for_module(module: str, scope: _GoModuleScope) -> str:
    suffix = "" if module == scope.module else module[len(scope.module) + 1 :]
    return _join_posix(scope.root, suffix)


def _path_under(path: str, prefix: str) -> bool:
    return shared_path_is_under(path, prefix)


def _path_under_scope(path: str, scope_root: str) -> bool:
    return shared_path_is_under_scope(path, scope_root)


_TS_CONFIG_EXCLUDED_DIRS: frozenset[str] = frozenset(
    {
        ".cache",
        ".git",
        ".hg",
        ".mypy_cache",
        ".pytest_cache",
        ".ruff_cache",
        ".svn",
        ".tox",
        ".venv",
        "__pycache__",
        "build",
        "coverage",
        "dist",
        "env",
        "node_modules",
        "venv",
    }
)

_TS_SOURCE_SUFFIXES: tuple[str, ...] = (
    ".d.ts",
    ".tsx",
    ".ts",
    ".jsx",
    ".js",
)


def _read_ts_path_aliases(
    project_root: str | Path | None,
    source_snapshot: SourceSnapshot | None = None,
) -> tuple[_TsPathAliasRule, ...]:
    if project_root is None:
        return ()
    root = Path(project_root).resolve()
    if not root.exists():
        return ()

    if source_snapshot is None:
        tsconfig_paths: list[Path] = []
        for current, dirs, files in os.walk(root):
            dirs[:] = [d for d in dirs if d not in _TS_CONFIG_EXCLUDED_DIRS]
            if "tsconfig.json" in files:
                tsconfig_paths.append(Path(current) / "tsconfig.json")
    else:
        tsconfig_paths = _snapshot_marker_paths(
            root,
            source_snapshot,
            "tsconfig.json",
        )

    rules: list[_TsPathAliasRule] = []
    for tsconfig in tsconfig_paths:
        rules.extend(_parse_tsconfig_aliases(root, tsconfig))
    return tuple(
        sorted(
            rules,
            key=lambda rule: (
                rule.root.count("/"),
                len(rule.root),
                len(rule.prefix),
                rule.prefix,
                rule.suffix,
                rule.targets,
            ),
        )
    )


def _snapshot_marker_paths(
    project_root: Path,
    source_snapshot: SourceSnapshot,
    filename: str,
) -> list[Path]:
    paths: list[Path] = []
    for marker in source_snapshot.package_markers:
        if marker.abs_path.name != filename:
            continue
        try:
            marker.abs_path.relative_to(project_root)
        except ValueError:
            continue
        paths.append(marker.abs_path)
    return sorted(
        paths,
        key=lambda path: path.relative_to(project_root).as_posix(),
    )


def _parse_tsconfig_aliases(
    project_root: Path, tsconfig: Path
) -> list[_TsPathAliasRule]:
    try:
        data = json.loads(tsconfig.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, ValueError):
        return []
    if not isinstance(data, dict):
        return []
    compiler = data.get("compilerOptions", {})
    if not isinstance(compiler, dict):
        return []
    paths = compiler.get("paths", {})
    if not isinstance(paths, dict):
        return []

    root_rel = _project_relative_dir(project_root, tsconfig.parent)
    base_url = compiler.get("baseUrl", ".")
    base_url = str(base_url) if isinstance(base_url, str) else "."
    base_root = _join_posix(root_rel, base_url)

    rules: list[_TsPathAliasRule] = []
    for raw_pattern, raw_targets in paths.items():
        if not isinstance(raw_pattern, str) or not isinstance(raw_targets, list):
            continue
        targets = tuple(
            _join_posix(base_root, str(target))
            for target in raw_targets
            if isinstance(target, str)
        )
        if not targets:
            continue
        prefix, marker, suffix = raw_pattern.partition("*")
        rules.append(
            _TsPathAliasRule(
                root=root_rel,
                prefix=prefix,
                suffix=suffix if marker else "",
                wildcard=bool(marker),
                targets=targets,
            )
        )
    return rules


def _project_relative_dir(project_root: Path, directory: Path) -> str:
    try:
        rel = directory.relative_to(project_root)
    except ValueError:
        return ""
    value = rel.as_posix()
    return "" if value == "." else value


def _join_posix(*parts: str) -> str:
    joined = ""
    for part in parts:
        if not part or part == ".":
            continue
        joined = posixpath.join(joined, part.replace("\\", "/"))
    normalized = posixpath.normpath(joined or ".")
    return "" if normalized == "." else normalized.strip("/")


def _nearest_ts_alias_root(
    rules: tuple[_TsPathAliasRule, ...], importer_filepath: str
) -> str | None:
    roots = {
        rule.root for rule in rules if _path_under_scope(importer_filepath, rule.root)
    }
    if not roots:
        return None
    return max(roots, key=lambda root: (root.count("/"), len(root)))


def _match_ts_alias_rule(rule: _TsPathAliasRule, spec: str) -> str | None:
    if not rule.wildcard:
        return "" if spec == rule.prefix else None
    if not spec.startswith(rule.prefix):
        return None
    if rule.suffix and not spec.endswith(rule.suffix):
        return None
    end = len(spec) - len(rule.suffix) if rule.suffix else len(spec)
    if end < len(rule.prefix):
        return None
    return spec[len(rule.prefix) : end]


def _ts_alias_target_stems(target: str, star: str) -> set[str]:
    expanded = target.replace("*", star).replace("\\", "/")
    normalized = posixpath.normpath(expanded).strip("/")
    if not normalized or normalized == ".":
        return set()
    stem = _strip_ts_source_suffix(normalized)
    candidates = {stem}
    if normalized == stem:
        candidates.add(f"{stem}/index")
    return candidates


def _strip_ts_source_suffix(path: str) -> str:
    for suffix in _TS_SOURCE_SUFFIXES:
        if path.endswith(suffix):
            return path[: -len(suffix)]
    return path


def build_module_path_resolver(
    inventory: dict,
    project_root: str | Path | None = None,
    *,
    source_snapshot: SourceSnapshot | None = None,
) -> ModulePathResolver:
    """Build an indexed import resolver for repeated lookups."""
    return ModulePathResolver.build(
        inventory,
        project_root=project_root,
        source_snapshot=source_snapshot,
    )
