"""Discover Python packages within a source tree.

Walks the directory tree under *src_dir* looking for ``pyproject.toml``
and ``setup.py`` markers, then extracts package metadata (name, version,
source root).  Each discovered package is represented as a
:class:`PackageInfo` dataclass.
"""

from __future__ import annotations

import ast
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Sequence

from ..config import EXCLUDED_DIRS

if TYPE_CHECKING:
    from .source_snapshot import SourceSnapshot

try:  # Python 3.11+
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - exercised on Python 3.9/3.10
    try:
        import tomli as tomllib
    except ModuleNotFoundError:  # pragma: no cover - dependency missing in ad-hoc envs
        tomllib = None


@dataclass(frozen=True)
class PackageInfo:
    """Metadata for a single Python package discovered on disk."""

    name: str
    root: str  # directory containing the package marker, relative to src_dir
    version: str
    marker_path: str  # relative path of pyproject.toml / setup.py


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
        is_setup = (
            (isinstance(func, ast.Name) and func.id == "setup")
            or (isinstance(func, ast.Attribute) and func.attr == "setup")
        )
        if not is_setup:
            continue
        for kw in node.keywords:
            if kw.arg in ("name", "version") and isinstance(kw.value, ast.Constant):
                info[kw.arg] = str(kw.value.value)
    return info


def _package_marker_paths(src_path: Path, source_snapshot: SourceSnapshot | None) -> tuple[list[Path], list[Path]]:
    if source_snapshot is None:
        return (
            sorted(src_path.rglob("pyproject.toml")),
            sorted(src_path.rglob("setup.py")),
        )

    pyprojects = [
        marker.abs_path for marker in source_snapshot.package_markers
        if marker.abs_path.name == "pyproject.toml"
    ]
    setup_files = [
        marker.abs_path for marker in source_snapshot.package_markers
        if marker.abs_path.name == "setup.py"
    ]
    return (
        sorted(pyprojects, key=lambda path: path.relative_to(src_path).as_posix()),
        sorted(setup_files, key=lambda path: path.relative_to(src_path).as_posix()),
    )


def discover_packages(src_dir: str, *, source_snapshot: SourceSnapshot | None = None) -> list[PackageInfo]:
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
        packages.append(PackageInfo(
            name=name,
            root=rel.parent.as_posix() if rel.parent != Path(".") else ".",
            version=info.get("version", "0.0.0"),
            marker_path=rel.as_posix(),
        ))

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
        packages.append(PackageInfo(
            name=name,
            root=rel.parent.as_posix() if rel.parent != Path(".") else ".",
            version=info.get("version", "0.0.0"),
            marker_path=rel.as_posix(),
        ))

    return packages


def stamp_inventory_packages(
    inventory: dict,
    packages: Sequence[PackageInfo],
) -> None:
    """Add a ``"package"`` key to each inventory entry in-place.

    Files are matched to the *most specific* (longest root) package
    whose root is a prefix of the file path.  Files that don't belong
    to any package get ``package: None``.
    """
    # Sort packages longest-root-first for greedy matching
    sorted_pkgs = sorted(packages, key=lambda p: len(p.root), reverse=True)

    for filepath, data in inventory.items():
        if data.get("language") != "python":
            data["package"] = None
            continue
        fp_posix = filepath.replace("\\", "/")
        matched = None
        for pkg in sorted_pkgs:
            prefix = pkg.root
            if prefix == ".":
                matched = pkg.name
                break
            if fp_posix == prefix or fp_posix.startswith(prefix + "/"):
                matched = pkg.name
                break
        data["package"] = matched
