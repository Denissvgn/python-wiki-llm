"""Focused tests for package discovery and inventory stamping."""

from __future__ import annotations

import textwrap
from pathlib import Path

from llm_wiki_cli.services.packages import (
    PackageInfo,
    discover_packages,
    stamp_inventory_packages,
)
from llm_wiki_cli.services.source_snapshot import build_source_snapshot


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(textwrap.dedent(text).lstrip(), encoding="utf-8")


def test_discover_packages_reads_pep621_metadata(tmp_path):
    _write(
        tmp_path / "pkg" / "pyproject.toml",
        """
        [project]
        name = "pep-pkg"
        version = "1.2.3"
        """,
    )

    assert discover_packages(str(tmp_path)) == [
        PackageInfo(
            name="pep-pkg",
            root="pkg",
            version="1.2.3",
            marker_path="pkg/pyproject.toml",
        )
    ]


def test_discover_packages_marks_dynamic_pep621_version(tmp_path):
    _write(
        tmp_path / "pyproject.toml",
        """
        [project]
        name = "dynamic-pkg"
        dynamic = ["version"]
        """,
    )

    assert discover_packages(str(tmp_path))[0].version == "dynamic"


def test_discover_packages_uses_poetry_metadata(tmp_path):
    _write(
        tmp_path / "pyproject.toml",
        """
        [tool.poetry]
        name = "poetry-pkg"
        version = "2.4.0"
        """,
    )

    assert discover_packages(str(tmp_path)) == [
        PackageInfo(
            name="poetry-pkg",
            root=".",
            version="2.4.0",
            marker_path="pyproject.toml",
        )
    ]


def test_discover_packages_uses_setup_py_fallback(tmp_path):
    _write(
        tmp_path / "legacy" / "setup.py",
        """
        import setuptools

        setuptools.setup(name="legacy-pkg", version="0.9.0")
        """,
    )

    assert discover_packages(str(tmp_path)) == [
        PackageInfo(
            name="legacy-pkg",
            root="legacy",
            version="0.9.0",
            marker_path="legacy/setup.py",
        )
    ]


def test_discover_packages_defaults_missing_setup_py_version(tmp_path):
    _write(
        tmp_path / "setup.py",
        """
        from setuptools import setup

        setup(name="legacy-pkg")
        """,
    )

    assert discover_packages(str(tmp_path))[0].version == "0.0.0"


def test_discover_packages_prefers_pyproject_over_setup_py(tmp_path):
    _write(
        tmp_path / "pyproject.toml",
        """
        [project]
        name = "modern-pkg"
        version = "3.0.0"
        """,
    )
    _write(
        tmp_path / "setup.py",
        """
        from setuptools import setup

        setup(name="legacy-pkg", version="0.1.0")
        """,
    )

    assert discover_packages(str(tmp_path)) == [
        PackageInfo(
            name="modern-pkg",
            root=".",
            version="3.0.0",
            marker_path="pyproject.toml",
        )
    ]


def test_discover_packages_ignores_unparseable_markers(tmp_path):
    _write(tmp_path / "bad-pyproject" / "pyproject.toml", "[project\nname =")
    _write(
        tmp_path / "bad-setup" / "setup.py", "from setuptools import setup\nsetup(\n"
    )

    assert discover_packages(str(tmp_path)) == []


def test_discover_packages_ignores_unreadable_pyproject_text(tmp_path):
    marker = tmp_path / "pyproject.toml"
    marker.write_bytes(b"\xff\xfe\x00\x00")

    assert discover_packages(str(tmp_path)) == []


def test_discover_packages_skips_excluded_directories(tmp_path):
    _write(
        tmp_path / ".venv" / "pyproject.toml",
        """
        [project]
        name = "venv-pkg"
        version = "1.0.0"
        """,
    )
    _write(
        tmp_path / "dist" / "setup.py",
        """
        from setuptools import setup

        setup(name="dist-pkg", version="1.0.0")
        """,
    )

    assert discover_packages(str(tmp_path)) == []


def test_discover_packages_respects_source_snapshot_boundaries(tmp_path):
    _write(
        tmp_path / "snapshotted" / "pyproject.toml",
        """
        [project]
        name = "snapshotted-pkg"
        version = "1.0.0"
        """,
    )
    snapshot = build_source_snapshot(tmp_path)
    _write(
        tmp_path / "late" / "pyproject.toml",
        """
        [project]
        name = "late-pkg"
        version = "2.0.0"
        """,
    )

    snapshotted = discover_packages(str(tmp_path), source_snapshot=snapshot)
    standalone_names = {package.name for package in discover_packages(str(tmp_path))}

    assert [package.name for package in snapshotted] == ["snapshotted-pkg"]
    assert standalone_names == {"late-pkg", "snapshotted-pkg"}


def test_stamp_inventory_packages_uses_most_specific_root(tmp_path):
    inventory = {
        "pkg/core/app.py": {"language": "python"},
    }
    packages = [
        PackageInfo("pkg", "pkg", "1.0.0", "pkg/pyproject.toml"),
        PackageInfo("core", "pkg/core", "1.0.0", "pkg/core/pyproject.toml"),
    ]

    stamp_inventory_packages(inventory, packages)

    assert inventory["pkg/core/app.py"]["package"] == "core"


def test_stamp_inventory_packages_normalizes_windows_separators(tmp_path):
    inventory = {
        "pkg\\app.py": {"language": "python"},
    }
    packages = [
        PackageInfo("pkg", "pkg", "1.0.0", "pkg/pyproject.toml"),
    ]

    stamp_inventory_packages(inventory, packages)

    assert inventory["pkg\\app.py"]["package"] == "pkg"


def test_stamp_inventory_packages_does_not_match_partial_prefix(tmp_path):
    inventory = {
        "pkg_extra/app.py": {"language": "python"},
    }
    packages = [
        PackageInfo("pkg", "pkg", "1.0.0", "pkg/pyproject.toml"),
    ]

    stamp_inventory_packages(inventory, packages)

    assert inventory["pkg_extra/app.py"]["package"] is None


def test_stamp_inventory_packages_clears_non_python_entries(tmp_path):
    inventory = {
        "pkg/app.ts": {"language": "typescript", "package": "stale"},
    }
    packages = [
        PackageInfo("pkg", "pkg", "1.0.0", "pkg/pyproject.toml"),
    ]

    stamp_inventory_packages(inventory, packages)

    assert inventory["pkg/app.ts"]["package"] is None
