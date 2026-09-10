"""Discover Python packages within a source tree.

Walks the directory tree under *src_dir* looking for ``pyproject.toml``
and ``setup.py`` markers, then extracts package metadata (name, version,
source root).  Each discovered package is represented as a
:class:`PackageInfo` dataclass.
"""

from __future__ import annotations

import ast
import posixpath
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Sequence

from ..config import EXCLUDED_DIRS
from .python_imports import normalized_root, under_root

if TYPE_CHECKING:
    from .source_snapshot import SourceSnapshot

try:  # Python 3.11+
    import tomllib  # type: ignore[reportMissingImports]
except ModuleNotFoundError:  # pragma: no cover - exercised on Python 3.9/3.10
    try:
        import tomli as tomllib  # type: ignore[reportMissingImports]
    except ModuleNotFoundError:  # pragma: no cover - dependency missing in ad-hoc envs
        tomllib = None


@dataclass(frozen=True)
class PackageInfo:
    """Metadata for a single Python package discovered on disk."""

    name: str
    root: str  # directory containing the package marker, relative to src_dir
    version: str
    marker_path: str  # relative path of pyproject.toml / setup.py
    import_roots: tuple[str, ...] | None = ()  # marker-relative; None means unknown


def _configured_import_roots(
    text: str, *, setup_py: bool = False
) -> tuple[str, ...] | None:
    """Read literal packaging source roots without executing a build backend."""
    roots = None
    specified = False
    if setup_py:
        try:
            tree = ast.parse(text)
        except SyntaxError:
            return None
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            if not (
                (isinstance(node.func, ast.Name) and node.func.id == "setup")
                or (isinstance(node.func, ast.Attribute) and node.func.attr == "setup")
            ):
                continue
            for keyword in node.keywords:
                if keyword.arg == "package_dir":
                    specified = True
                    try:
                        value = ast.literal_eval(keyword.value)
                    except (ValueError, TypeError, SyntaxError):
                        return None
                    roots = (
                        [value[""]] if isinstance(value, dict) and "" in value else None
                    )
    else:
        if tomllib is None:
            return None
        try:
            data = tomllib.loads(text)
        except (ValueError, TypeError):
            return None
        tool = data.get("tool", {})
        if not isinstance(tool, dict):
            return None
        setuptools = tool.get("setuptools", {})
        if isinstance(setuptools, dict):
            if "package-dir" in setuptools:
                specified = True
                mapping = setuptools["package-dir"]
                roots = (
                    [mapping[""]]
                    if isinstance(mapping, dict) and "" in mapping
                    else None
                )
            elif isinstance(setuptools.get("packages"), dict):
                find = setuptools["packages"].get("find", {})
                if isinstance(find, dict) and "where" in find:
                    specified, roots = True, find["where"]
        poetry = tool.get("poetry", {})
        if not specified and isinstance(poetry, dict) and "packages" in poetry:
            specified = True
            packages = poetry["packages"]
            if isinstance(packages, list) and all(
                isinstance(item, dict) for item in packages
            ):
                roots = [item.get("from", ".") for item in packages]
    if not specified:
        return ()
    if not isinstance(roots, list) or not roots:
        return None
    normalized = [normalized_root(root) for root in roots]
    if any(root is None for root in normalized):
        return None
    return tuple(sorted({root or "." for root in normalized}))


def _parse_pyproject_toml(text: str) -> dict[str, str]:
    """Parse project metadata from PEP 621 first, then Poetry metadata."""
    info: dict[str, str] = {}
    if tomllib is None:
        return info
    try:
        data = tomllib.loads(text)
    except Exception:
        return info

    project = data.get("project", {})
    if isinstance(project, dict) and project.get("name"):
        info["name"] = str(project["name"])
        if isinstance(project.get("version"), str):
            info["version"] = str(project["version"])
        elif "version" in project.get("dynamic", []):
            info["version"] = "dynamic"
        return info

    poetry = data.get("tool", {}).get("poetry", {})
    if isinstance(poetry, dict) and poetry.get("name"):
        info["name"] = str(poetry["name"])
        if isinstance(poetry.get("version"), str):
            info["version"] = str(poetry["version"])

    return info


def _parse_setup_py(text: str) -> dict[str, str]:
    """Extract *name* and *version* from a ``setup.py`` via AST inspection."""
    info: dict[str, str] = {}
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return info

    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        # match setup(...) or setuptools.setup(...)
        is_setup = (isinstance(func, ast.Name) and func.id == "setup") or (
            isinstance(func, ast.Attribute) and func.attr == "setup"
        )
        if not is_setup:
            continue
        for kw in node.keywords:
            if kw.arg in ("name", "version") and isinstance(kw.value, ast.Constant):
                info[kw.arg] = str(kw.value.value)
    return info


def _package_marker_paths(
    src_path: Path, source_snapshot: SourceSnapshot | None
) -> tuple[list[Path], list[Path]]:
    if source_snapshot is None:
        return (
            sorted(src_path.rglob("pyproject.toml")),
            sorted(src_path.rglob("setup.py")),
        )

    pyprojects = [
        marker.abs_path
        for marker in source_snapshot.package_markers
        if marker.abs_path.name == "pyproject.toml"
    ]
    setup_files = [
        marker.abs_path
        for marker in source_snapshot.package_markers
        if marker.abs_path.name == "setup.py"
    ]
    return (
        sorted(pyprojects, key=lambda path: path.relative_to(src_path).as_posix()),
        sorted(setup_files, key=lambda path: path.relative_to(src_path).as_posix()),
    )


def discover_packages(
    src_dir: str, *, source_snapshot: SourceSnapshot | None = None
) -> list[PackageInfo]:
    """Return all Python packages found under *src_dir*.

    A "package" is a directory containing ``pyproject.toml`` or
    ``setup.py`` with a discoverable project name.  Directories matching
    :data:`EXCLUDED_DIRS` are skipped.
    """
    src_path = Path(src_dir).resolve()
    packages: list[PackageInfo] = []
    pyproject_paths, setup_paths = _package_marker_paths(src_path, source_snapshot)

    for marker in pyproject_paths:
        rel = marker.relative_to(src_path)
        if not EXCLUDED_DIRS.isdisjoint(rel.parts):
            continue
        try:
            text = marker.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        info = _parse_pyproject_toml(text)
        name = info.get("name", "")
        if not name:
            continue
        packages.append(
            PackageInfo(
                name=name,
                root=rel.parent.as_posix() if rel.parent != Path(".") else ".",
                version=info.get("version", "0.0.0"),
                marker_path=rel.as_posix(),
                import_roots=_configured_import_roots(text),
            )
        )

    for marker in setup_paths:
        rel = marker.relative_to(src_path)
        if not EXCLUDED_DIRS.isdisjoint(rel.parts):
            continue
        # Skip if a pyproject.toml already covers this directory
        rel_root = rel.parent.as_posix() if rel.parent != Path(".") else "."
        if any(p.root == rel_root for p in packages):
            continue
        try:
            text = marker.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        info = _parse_setup_py(text)
        name = info.get("name", "")
        if not name:
            continue
        packages.append(
            PackageInfo(
                name=name,
                root=rel.parent.as_posix() if rel.parent != Path(".") else ".",
                version=info.get("version", "0.0.0"),
                marker_path=rel.as_posix(),
                import_roots=_configured_import_roots(text, setup_py=True),
            )
        )

    return packages


def stamp_inventory_packages(
    inventory: dict,
    packages: Sequence[PackageInfo],
    *,
    source_paths: Sequence[str] = (),
) -> None:
    """Add a ``"package"`` key to each inventory entry in-place.

    Files are matched to the *most specific* (longest root) package
    whose root is a prefix of the file path.  Files that don't belong
    to any package get ``package: None``.
    """
    # Sort packages longest-root-first for greedy matching
    sorted_pkgs = sorted(packages, key=lambda p: len(p.root), reverse=True)
    known_paths = {path.replace("\\", "/") for path in (*inventory, *source_paths)}
    scopes = {
        package: _package_import_scope(package, known_paths) for package in packages
    }

    for filepath, data in inventory.items():
        data.pop("python_import_scope", None)
        if data.get("language") != "python":
            data["package"] = None
            continue
        fp_posix = filepath.replace("\\", "/")
        matched = None
        for pkg in sorted_pkgs:
            prefix = pkg.root
            if prefix == ".":
                matched = pkg.name
                data["python_import_scope"] = {
                    "root": scopes[pkg]["root"],
                    "search_roots": list(scopes[pkg]["search_roots"]),
                }
                break
            if fp_posix == prefix or fp_posix.startswith(prefix + "/"):
                matched = pkg.name
                data["python_import_scope"] = {
                    "root": scopes[pkg]["root"],
                    "search_roots": list(scopes[pkg]["search_roots"]),
                }
                break
        data["package"] = matched


def _package_import_scope(package: PackageInfo, source_paths: set[str]) -> dict:
    root = normalized_root(package.root)
    if root is None:
        return {"root": package.root, "search_roots": []}
    roots = []
    if package.import_roots is not None:
        if package.import_roots:
            roots = [posixpath.join(root, item) for item in package.import_roots]
        else:
            roots = [root]
            src = posixpath.join(root, "src")
            if any(under_root(path, src) for path in source_paths):
                roots.append(src)
            if root and posixpath.join(root, "__init__.py") in source_paths:
                roots.append(posixpath.dirname(root))
    return {
        "root": root or ".",
        "search_roots": sorted({normalized_root(item) or "." for item in roots}),
    }
