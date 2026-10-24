"""Static coverage explanations over selected, content-bound Python sources.

These routes are report metadata. They do not create inventory declarations,
canonical pages, durable aliases or runtime import equivalence.
"""

from __future__ import annotations

import ast
import hashlib
from collections.abc import Iterable, Mapping
from pathlib import PurePosixPath

from ..extractors.python_extractor import (
    _static_import_bindings,
    _static_type_checking_block,
    module_alias_target,
)
from .knowledge_storage import KnowledgeStorageError
from .knowledge_storage_io import read_guarded
from .python_imports import PythonModuleIndex
from .source_selection import SourceSelectionError, locate_exact_repository_path
from .source_snapshot import SourceSnapshot

_MAX_SOURCE_BYTES = 1024 * 1024
_MAX_ALIAS_HOPS = 16


def _no_implementation(tree: ast.Module) -> bool:
    return all(
        isinstance(item, ast.Pass) or (
            isinstance(item, ast.Expr) and isinstance(item.value, ast.Constant)
            and isinstance(item.value.value, str)
        )
        for item in tree.body
    )


def _package_binding_is_clear(tree: ast.Module, child: str) -> bool:
    """Reject explicit child bindings, dynamic exports and executable setup."""
    bindings: dict[str, str] = {}
    postponed_annotations = any(
        isinstance(item, ast.ImportFrom) and item.level == 0
        and item.module == "__future__" and any(a.name == "annotations" for a in item.names)
        for item in tree.body
    )
    for item in tree.body:
        if _no_implementation(ast.Module(body=[item], type_ignores=[])):
            continue
        imported = _static_import_bindings(item)
        if imported is not None:
            if set(imported) & (set(bindings) | {child, "__getattr__"}):
                return False
            bindings.update(imported)
            continue
        if _static_type_checking_block(item, bindings):
            continue
        if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
            annotations = [item.returns, *(arg.annotation for arg in (
                *item.args.posonlyargs, *item.args.args, *item.args.kwonlyargs,
                *([item.args.vararg] if item.args.vararg else []),
                *([item.args.kwarg] if item.args.kwarg else []),
            ))]
            if (item.name in {child, "__getattr__"} or item.decorator_list
                    or item.args.defaults or any(item.args.kw_defaults)
                    or (not postponed_annotations and any(a is not None for a in annotations))):
                return False
            bindings[item.name] = ""
            continue
        if isinstance(item, ast.Assign) and all(isinstance(t, ast.Name) for t in item.targets):
            names = {t.id for t in item.targets if isinstance(t, ast.Name)}
            if names & ({child, "__getattr__"} | set(bindings)):
                return False
            try:
                ast.literal_eval(item.value)
            except (ValueError, TypeError):
                return False
            bindings.update(dict.fromkeys(names, ""))
            continue
        return False
    return True


def _alias_import(tree: ast.Module, name: str) -> tuple[str, str, str]:
    for statement in tree.body:
        imported = _static_import_bindings(statement)
        if imported is not None and name in imported:
            if isinstance(statement, ast.ImportFrom):
                parent = "." * statement.level + (statement.module or "")
                child = next(a.name for a in statement.names if (a.asname or a.name) == name)
                return imported[name], parent, child
            parent, _, child = imported[name].rpartition(".")
            return imported[name], parent, child
    return "", "", ""


def classify_uncovered_python_sources(
    snapshot: SourceSnapshot, inventory: Mapping, paths: Iterable[str],
) -> dict[str, dict]:
    """Explain only proven omissions; all unavailable proof stays uncovered.

    Reads are guarded, hash-checked and limited to 1 MiB per selected file.
    Alias chains stop after 16 hops. Namespace checks inspect only the expected
    initializer's presence; an existing unselected initializer is never read.
    Neither discovery nor inventory is modified.
    """
    selected = frozenset(snapshot.language_paths("python"))
    modules = {p: inventory.get(p, {"language": "python"}) for p in selected}
    index = PythonModuleIndex.build(modules)
    trees: dict[str, ast.Module | None] = {}

    def read(path: str) -> ast.Module | None:
        if path in trees:
            return trees[path]
        trees[path] = None
        if path not in selected:
            return None
        try:
            exact = locate_exact_repository_path(snapshot.root, path)
            if exact is None:
                return None
            raw = read_guarded(exact, _MAX_SOURCE_BYTES).content
            if "sha256:" + hashlib.sha256(raw).hexdigest() != snapshot.captured_content_hashes.get(path):
                return None
            try:
                source = raw.decode("utf-8")
            except UnicodeDecodeError:
                source = raw.decode("cp1252")
            trees[path] = ast.parse(source, filename=path)
        except (OSError, ValueError, UnicodeError, SyntaxError, KnowledgeStorageError, SourceSelectionError):
            pass
        return trees[path]

    result: dict[str, dict] = {}
    for path in sorted(set(paths) & selected):
        tree = read(path)
        if tree is None:
            continue
        content_hash = snapshot.captured_content_hashes[path]
        if PurePosixPath(path).name == "__init__.py" and _no_implementation(tree):
            result[path] = {"reason": "declaration-free-initializer", "content_hash": content_hash}
            continue
        if not module_alias_target(tree):
            continue
        route = [path]
        current = path
        reason = "alias-hop-limit"
        for hop in range(_MAX_ALIAS_HOPS + 1):
            tree = read(current)
            if tree is None:
                reason = "alias-source-unavailable"
                break
            binding = module_alias_target(tree)
            if not binding:
                if current not in inventory:
                    reason = "alias-target-not-extracted"
                elif _no_implementation(tree):
                    reason = "alias-target-no-implementation"
                else:
                    reason = "static-module-alias"
                break
            if hop == _MAX_ALIAS_HOPS:
                break
            module, parent, child = _alias_import(tree, binding)
            candidates = index.candidates(module, current)
            if len(candidates) != 1:
                reason = "alias-target-ambiguous" if candidates else "alias-target-not-selected"
                break
            target = next(iter(candidates))
            if parent:
                parents = index.candidates(parent, current)
                if parents:
                    if len(parents) != 1:
                        reason = "alias-package-binding-unproven"
                        break
                    parent_path = next(iter(parents))
                    parent_tree = read(parent_path)
                    if (PurePosixPath(parent_path).name != "__init__.py"
                            or parent_tree is None or not _package_binding_is_clear(parent_tree, child)):
                        reason = "alias-package-binding-unproven"
                        break
                else:
                    # A namespace package can have no initializer. Absence from
                    # selected inventory alone does not prove physical absence.
                    target_path = PurePosixPath(target)
                    package = target_path.parent.parent if target_path.name == "__init__.py" else target_path.parent
                    initializer = (package / "__init__.py").as_posix()
                    try:
                        if (not snapshot.path_is_effectively_selected(initializer)
                                or locate_exact_repository_path(snapshot.root, initializer) is not None):
                            reason = "alias-package-binding-unproven"
                            break
                    except (OSError, ValueError):
                        reason = "alias-package-binding-unproven"
                        break
            if target in route:
                route.append(target)
                reason = "alias-cycle"
                break
            route.append(target)
            current = target
        result[path] = {"reason": reason, "route": route, "content_hash": content_hash}
    return result
