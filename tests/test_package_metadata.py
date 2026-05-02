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


def test_github_community_health_files_exist():
    expected = [
        "CODE_OF_CONDUCT.md",
        "SECURITY.md",
        ".github/ISSUE_TEMPLATE/bug_report.yml",
        ".github/ISSUE_TEMPLATE/feature_request.yml",
        ".github/ISSUE_TEMPLATE/config.yml",
    ]
    for path in expected:
        assert (PROJECT_ROOT / path).is_file(), path


def test_readme_documents_fork_first_policy():
    readme = (PROJECT_ROOT / "README.md").read_text(encoding="utf-8")
    assert "does not maintain a formal contribution process" in readme
    assert "freely fork it" in readme
    assert "CONTRIBUTING.md" not in readme
    assert not (PROJECT_ROOT / "CONTRIBUTING.md").exists()
    assert not (PROJECT_ROOT / ".github/PULL_REQUEST_TEMPLATE.md").exists()
