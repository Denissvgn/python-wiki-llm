"""Discover Python packages within a source tree.

Walks the directory tree under *src_dir* looking for ``pyproject.toml``
and ``setup.py`` markers, then extracts package metadata (name, version,
source root).  Each discovered package is represented as a
:class:`PackageInfo` dataclass.
"""

from __future__ import annotations

import ast
import configparser
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Sequence

from ..config import EXCLUDED_DIRS


@dataclass(frozen=True)
class PackageInfo:
    """Metadata for a single Python package discovered on disk."""

    name: str
    root: str  # directory containing the package marker, relative to src_dir
    version: str
    marker_path: str  # relative path of pyproject.toml / setup.py


def _parse_pyproject_toml(text: str) -> dict[str, str]:
    """Minimal TOML parser for ``[project]`` name and version fields.

    Full TOML parsing requires a third-party library (or Python 3.11+
    ``tomllib``).  We use a regex-based approach that covers the vast
    majority of real-world ``pyproject.toml`` files.
    """
    info: dict[str, str] = {}

    # Try to grab [project] name and version
    for key in ("name", "version"):
        pattern = rf'^\s*{key}\s*=\s*"([^"]+)"'
        m = re.search(pattern, text, re.MULTILINE)
        if m:
            info[key] = m.group(1)

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


def discover_packages(src_dir: str) -> list[PackageInfo]:
    """Return all Python packages found under *src_dir*.

    A "package" is a directory containing ``pyproject.toml`` or
    ``setup.py`` with a discoverable project name.  Directories matching
    :data:`EXCLUDED_DIRS` are skipped.
    """
    src_path = Path(src_dir).resolve()
    packages: list[PackageInfo] = []

    for marker in sorted(src_path.rglob("pyproject.toml")):
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

    for marker in sorted(src_path.rglob("setup.py")):
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
