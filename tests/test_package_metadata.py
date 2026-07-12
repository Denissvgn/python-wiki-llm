"""Tests for package/readme metadata consistency."""

from __future__ import annotations

import ast
from pathlib import Path

try:
    import tomllib  # type: ignore[reportMissingImports]
except ModuleNotFoundError:  # pragma: no cover - Python 3.9/3.10
    import tomli as tomllib  # type: ignore[reportMissingImports]


PROJECT_ROOT = Path(__file__).parents[1]


def _changelog_section(heading: str) -> str:
    changelog = (PROJECT_ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    start = changelog.index(heading)
    next_release = changelog.index("\n## [", start + 1)
    return changelog[start:next_release]


def _pyproject() -> dict:
    return tomllib.loads((PROJECT_ROOT / "pyproject.toml").read_text(encoding="utf-8"))


def _ci_python_versions() -> list[str]:
    ci = (PROJECT_ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
    matrix_line = next(
        line.strip()
        for line in ci.splitlines()
        if line.strip().startswith("python-version:")
    )
    _, value = matrix_line.split(":", maxsplit=1)
    return ast.literal_eval(value.strip())


def test_project_description_mentions_multi_language_projects():
    data = _pyproject()
    assert "multi-language projects" in data["project"]["description"]


def test_package_data_includes_rust_lockfile():
    data = _pyproject()
    package_data = data["tool"]["setuptools"]["package-data"]["llm_wiki_cli"]
    assert "extractors/rust_scripts/Cargo.lock" in package_data


def test_package_data_includes_haskell_helper_sources():
    data = _pyproject()
    package_data = data["tool"]["setuptools"]["package-data"]["llm_wiki_cli"]
    assert "extractors/haskell_scripts/Main.hs" in package_data
    assert "extractors/haskell_scripts/Inventory.hs" in package_data
    assert "extractors/haskell_scripts/Parser.hs" in package_data
    assert "extractors/haskell_scripts/Paths.hs" in package_data
    assert "extractors/haskell_scripts/Json.hs" in package_data


def test_package_data_includes_bundled_skills():
    data = _pyproject()
    package_data = data["tool"]["setuptools"]["package-data"]["llm_wiki_cli"]
    assert "skills/wiki-sync/SKILL.md" in package_data
    assert "skills/wiki-sync/reference.md" in package_data
    assert "skills/wiki-bootstrap/SKILL.md" in package_data
    assert "skills/wiki-bootstrap/reference.md" in package_data
    assert "skills/attack-surface/SKILL.md" in package_data
    assert "skills/attack-surface/reference.md" in package_data
    assert "skills/dep-audit/SKILL.md" in package_data
    assert "skills/dep-audit/reference.md" in package_data
    assert "skills/dep-vuln-triage/SKILL.md" in package_data
    assert "skills/dep-vuln-triage/reference.md" in package_data
    assert "skills/doc-hub/SKILL.md" in package_data
    assert "skills/doc-hub/reference.md" in package_data
    assert "skills/doc-review/SKILL.md" in package_data
    assert "skills/doc-review/reference.md" in package_data
    assert "skills/impact-analysis/SKILL.md" in package_data
    assert "skills/impact-analysis/reference.md" in package_data
    assert "skills/infra-review/SKILL.md" in package_data
    assert "skills/infra-review/reference.md" in package_data
    assert "skills/onboarding-guide/SKILL.md" in package_data
    assert "skills/onboarding-guide/reference.md" in package_data
    assert "skills/publish-docs/SKILL.md" in package_data
    assert "skills/publish-docs/reference.md" in package_data
    assert "skills/usage-examples/SKILL.md" in package_data
    assert "skills/usage-examples/reference.md" in package_data
    assert "skills/user-docs-author/SKILL.md" in package_data
    assert "skills/user-docs-author/reference.md" in package_data


def test_package_data_includes_bundled_m4_plugin_sample():
    data = _pyproject()
    package_data = data["tool"]["setuptools"]["package-data"]["llm_wiki_cli"]
    assert (
        "examples/plugins/m4-documentation-hooks/llm-wiki-plugin.json" in package_data
    )
    assert "examples/plugins/m4-documentation-hooks/detectors.py" in package_data
    assert "examples/plugins/m4-documentation-hooks/styles.py" in package_data


def test_sdist_manifest_includes_source_m4_plugin_sample():
    manifest = (PROJECT_ROOT / "MANIFEST.in").read_text(encoding="utf-8")
    assert (
        "recursive-include examples/plugins/m4-documentation-hooks *.py *.json"
        in manifest
    )


def test_project_distribution_name_is_pypi_safe_name():
    data = _pyproject()
    assert data["project"]["name"] == "agent-wiki-cli"


def test_project_version_is_release_target():
    data = _pyproject()
    assert data["project"]["version"] == "1.4.0"


def test_project_requires_python_3_10_or_newer():
    data = _pyproject()
    assert data["project"]["requires-python"] == ">=3.10"


def test_ci_python_matrix_matches_supported_boundary_versions():
    assert _ci_python_versions() == ["3.10", "3.13"]


def test_readme_current_support_table_mentions_python_3_10_plus():
    readme = (PROJECT_ROOT / "README.md").read_text(encoding="utf-8")
    assert "| Python | stdlib `ast` | Python 3.10+ |" in readme
    assert "| Python | stdlib `ast` | Python 3.9+ |" not in readme


def test_changelog_1_2_0_documents_python_support_floor():
    changelog = (PROJECT_ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    assert changelog.count("## [1.2.0] - 2026-07-08") == 1

    release_notes = _changelog_section("## [1.2.0]")
    assert "Minimum supported Python is now 3.10" in release_notes
    assert "CI now tests Python 3.10 and 3.13" in release_notes


def test_readme_documents_bundled_skills():
    readme = (PROJECT_ROOT / "README.md").read_text(encoding="utf-8")

    for skill_id in [
        "attack-surface",
        "dep-audit",
        "dep-vuln-triage",
        "doc-hub",
        "doc-review",
        "impact-analysis",
        "infra-review",
        "onboarding-guide",
        "publish-docs",
        "usage-examples",
        "user-docs-author",
        "wiki-bootstrap",
        "wiki-sync",
    ]:
        assert f"`{skill_id}`" in readme


def test_readme_documents_autonomous_agent_consumption_paths():
    readme = (PROJECT_ROOT / "README.md").read_text(encoding="utf-8")
    assert "For autonomous agents" in readme
    assert "llm-wiki init --agent generic" in readme
    assert "llm-wiki skills export --dest" in readme
    assert "usage-examples" in readme


def test_readme_uses_distribution_name_for_uninstall():
    readme = (PROJECT_ROOT / "README.md").read_text(encoding="utf-8")
    assert "pip uninstall agent-wiki-cli" in readme
    assert "pip install agent-wiki-cli" in readme
    assert "pip uninstall llm-wiki-cli" not in readme
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


def test_readme_documents_resource_aware_execution():
    readme = (PROJECT_ROOT / "README.md").read_text(encoding="utf-8")
    text = " ".join(readme.split())

    assert "### Resource-aware execution" in readme
    assert "run one heavy gate at a time" in text
    assert "The supervising agent owns that schedule" in text
    assert "Use `--jobs 1` for interactive source scans" in text
    assert "isolated terminal or a controlled CI runner" in text
    assert "do not retry the same burst" in text
    assert "not proof that `llm-wiki` leaked a watcher" in text
    assert "For a narrow task with supplied files or a supplied diff" in text
    assert "budget and focus bound emitted output after a full deep inventory" in text
    assert "Extractor plan: requested=auto resolved=20" in readme
    assert '"extractor_jobs"' in readme
    for field in [
        "requested_jobs",
        "resolved_jobs",
        "eligible_parallel_plans",
        "effective_workers",
        "parallel_plan_ids",
        "sequential_plan_ids",
        "cache_elided_plan_ids",
    ]:
        assert field in readme
    assert "Default lint report serialization, MCP lint responses" in text
    assert "the `llm-wiki-context/v1` protocol stay unchanged" in text


def test_release_metadata_documents_surfaces_and_verification():
    readme = (PROJECT_ROOT / "README.md").read_text(encoding="utf-8")
    release_notes = _changelog_section("## [1.0.0]")
    release_metadata = " ".join("\n".join([readme, release_notes]).split())

    for required in [
        "canonical wiki surface registry",
        "landing page",
        ".llm-wiki-surface.json",
        "flows",
        "dependencies.md",
        "load-order.md",
        "site export",
        "site check",
        "Obsidian",
        "MCP",
        "Python API",
        "context filters",
        "plugin component types",
        "Ubuntu",
        "macOS",
        "Windows",
        "Python 3.9, 3.12, and 3.13",
        ".venv/bin/pytest -q",
        ".venv/bin/python -m build",
        "git diff --check",
    ]:
        assert required in release_metadata


def test_readme_release_verification_uses_project_virtualenv():
    readme = (PROJECT_ROOT / "README.md").read_text(encoding="utf-8")
    readme_lines = {line.strip() for line in readme.splitlines()}

    for required in [
        '.venv/bin/pip install -e ".[dev]"',
        ".venv/bin/pytest tests/ -v",
        ".venv/bin/python -m build",
        ".venv/bin/pytest -q",
    ]:
        assert required in readme

    assert 'pip install -e ".[dev]"' not in readme_lines
    assert not any(line.startswith("python -m pytest") for line in readme_lines)


def test_changelog_1_0_0_documents_m4_public_surfaces():
    release_notes = _changelog_section("## [1.0.0]")

    for required in [
        "static-site",
        "documentation graph",
        "MCP",
        "Python API",
        "context",
        "plugin",
        "migration",
        "dogfood",
        "release-readiness",
    ]:
        assert required in release_notes


def test_changelog_1_1_0_documents_haskell_release_boundaries():
    release_notes = _changelog_section("## [1.1.0]")
    release_text = " ".join(release_notes.split())

    for required in [
        "Haskell",
        "helper-backed",
        "syntax-only",
        "GHC 9.6.x",
        "default CI",
        "does not require GHC",
    ]:
        assert required in release_text


def test_default_ci_does_not_install_or_prepare_ghc():
    ci = (PROJECT_ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
    ci_lower = ci.lower()

    assert "ghc" not in ci_lower
    assert "prepare-extractors --language haskell" not in ci_lower
