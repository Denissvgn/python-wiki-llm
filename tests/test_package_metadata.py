"""Tests for package/readme metadata consistency."""
from __future__ import annotations

from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - Python 3.9/3.10
    import tomli as tomllib


PROJECT_ROOT = Path(__file__).parents[1]


def test_project_description_mentions_multi_language_projects():
    data = tomllib.loads((PROJECT_ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    assert "multi-language projects" in data["project"]["description"]


def test_package_data_includes_rust_lockfile():
    data = tomllib.loads((PROJECT_ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    package_data = data["tool"]["setuptools"]["package-data"]["llm_wiki_cli"]
    assert "extractors/rust_scripts/Cargo.lock" in package_data


def test_readme_uses_distribution_name_for_uninstall():
    readme = (PROJECT_ROOT / "README.md").read_text(encoding="utf-8")
    assert "pip uninstall llm-wiki-cli" in readme
    assert "pip uninstall llm_wiki_cli" not in readme
