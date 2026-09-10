"""Pure Python import-root indexing over an already selected inventory."""

from __future__ import annotations

import posixpath
import sys
from collections import defaultdict
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import PurePosixPath

from .python_stdlib import python_stdlib_module_names


def is_python_source(filepath: str, data: object = None) -> bool:
    language = data.get("language") if isinstance(data, Mapping) else None
    return language == "python" or (not language and filepath.endswith(".py"))


def normalized_root(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    value = value.replace("\\", "/")
    if value.startswith("/") or ":" in value:
        return None
    result = posixpath.normpath(value or ".")
    if result == ".." or result.startswith("../"):
        return None
    return "" if result == "." else result


def under_root(path: str, root: str) -> bool:
    return not root or path == root or path.startswith(root + "/")


@dataclass(frozen=True)
class PythonImportScope:
    root: str
    search_roots: tuple[str, ...]
    declared: bool = False


@dataclass(frozen=True)
class PythonModuleIndex:
    exact: dict[str, frozenset[str]]
    scopes: tuple[PythonImportScope, ...]

    @classmethod
    def build(cls, inventory: Mapping) -> PythonModuleIndex:
        exact: defaultdict[str, set[str]] = defaultdict(set)
        inferred: dict[str, PythonImportScope] = {"": PythonImportScope("", ("",))}
        declared: dict[str, set[str]] = {}
        for raw_path, data in inventory.items():
            filepath = str(raw_path).replace("\\", "/")
            if not is_python_source(filepath, data):
                continue
            path = PurePosixPath(filepath)
            exact[path.with_suffix("").as_posix()].add(str(raw_path))
            if path.name == "__init__.py":
                exact[path.parent.as_posix()].add(str(raw_path))
            for index, part in enumerate(path.parts[:-1]):
                if part == "src":
                    root = "/".join(path.parts[:index])
                    source_root = "/".join(path.parts[: index + 1])
                    inferred[root] = PythonImportScope(root, (source_root, root))
            metadata = (
                data.get("python_import_scope") if isinstance(data, Mapping) else None
            )
            if not isinstance(metadata, Mapping):
                continue
            root = normalized_root(metadata.get("root"))
            roots = metadata.get("search_roots")
            if (
                root is None
                or not under_root(filepath, root)
                or not isinstance(roots, (list, tuple))
            ):
                continue
            normalized = [normalized_root(item) for item in roots]
            if any(item is None for item in normalized):
                continue
            declared.setdefault(root, set()).update(
                item for item in normalized if item is not None
            )
        for root, roots in declared.items():
            inferred[root] = PythonImportScope(root, tuple(sorted(roots)), True)
        return cls(
            {key: frozenset(value) for key, value in exact.items()},
            tuple(
                sorted(
                    inferred.values(), key=lambda scope: (-len(scope.root), scope.root)
                )
            ),
        )

    def candidates(self, module: str, importer: str) -> set[str]:
        module = module.strip().strip('"').strip("'").replace("\\", "/")
        importer = importer.replace("\\", "/")
        if not module:
            return set()
        scope = next(item for item in self.scopes if under_root(importer, item.root))
        if module.startswith("."):
            target = _relative_target(module, importer)
            if target is None or not under_root(target, scope.root):
                return set()
            return set(self.exact.get(target, ()))
        module_path = module.replace(".", "/")
        top = module_path.split("/", 1)[0]
        if top in sys.builtin_module_names:
            return set()
        if not scope.search_roots:
            return set()
        local = self._scope_candidates(module_path, scope)
        if local:
            return local
        if top in python_stdlib_module_names():
            return set()
        candidates: set[str] = set()
        for other in self.scopes:
            if not other.declared or other.root == scope.root:
                continue
            for target in self._scope_candidates(module_path, other):
                # Declared projects may expose qualified shared packages, not
                # every unrelated standalone file below an arbitrary src/.
                if under_root(target.replace("\\", "/"), other.root) and (
                    "/" in module_path
                    or PurePosixPath(target.replace("\\", "/")).name == "__init__.py"
                ):
                    candidates.add(target)
        return candidates

    def _scope_candidates(self, module: str, scope: PythonImportScope) -> set[str]:
        matches: set[str] = set()
        for root in scope.search_roots:
            path = normalized_root(posixpath.join(root, module))
            if path is not None:
                matches.update(self.exact.get(path, ()))
        return matches


def _relative_target(module: str, importer: str) -> str | None:
    parent = PurePosixPath(importer).parent
    if module.startswith(("./", "../")):
        return normalized_root(posixpath.join(parent.as_posix(), module))
    dots = len(module) - len(module.lstrip("."))
    if dots - 1 > len(parent.parts):
        return None
    for _ in range(dots - 1):
        parent = parent.parent
    tail = module[dots:].replace(".", "/")
    target = normalized_root(posixpath.join(parent.as_posix(), tail))
    return "__init__" if target == "" else target
