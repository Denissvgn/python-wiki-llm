"""Tests for package/readme metadata consistency."""

from __future__ import annotations

import re
from pathlib import Path

import yaml

from tests import release_artifact_smoke

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


def _ci_test_matrix() -> dict:
    ci = yaml.safe_load(
        (PROJECT_ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
    )
    return ci["jobs"]["test"]["strategy"]["matrix"]


def test_project_description_mentions_multi_language_projects():
    data = _pyproject()
    assert "multi-language projects" in data["project"]["description"]


def test_package_data_includes_rust_lockfile():
    data = _pyproject()
    package_data = data["tool"]["setuptools"]["package-data"]["llm_wiki_cli"]
    assert "extractors/rust_scripts/Cargo.lock" in package_data


def test_package_data_includes_typescript_lockfile():
    data = _pyproject()
    package_data = data["tool"]["setuptools"]["package-data"]["llm_wiki_cli"]
    assert "extractors/ts_scripts/package-lock.json" in package_data


def test_package_data_includes_haskell_helper_sources():
    data = _pyproject()
    package_data = data["tool"]["setuptools"]["package-data"]["llm_wiki_cli"]
    assert "extractors/haskell_scripts/Main.hs" in package_data
    assert "extractors/haskell_scripts/Inventory.hs" in package_data
    assert "extractors/haskell_scripts/Parser.hs" in package_data
    assert "extractors/haskell_scripts/Paths.hs" in package_data
    assert "extractors/haskell_scripts/Json.hs" in package_data


def test_package_data_includes_knowledge_schema():
    data = _pyproject()
    package_data = data["tool"]["setuptools"]["package-data"]["llm_wiki_cli"]
    assert "schemas/llm-wiki-knowledge-v1.schema.json" in package_data


def test_jsonschema_is_a_dev_only_dependency():
    data = _pyproject()
    assert "jsonschema>=4.18" in data["project"]["optional-dependencies"]["dev"]
    assert not any(
        dependency.lower().startswith("jsonschema")
        for dependency in data["project"]["dependencies"]
    )


def test_mcp_extra_stays_on_compatible_dependency_lines():
    data = _pyproject()

    assert data["project"]["optional-dependencies"]["mcp"] == [
        "mcp>=1.27,<2; python_version >= '3.10'",
        "pydantic-settings>=2.5.2,<2.15; python_version >= '3.10'",
    ]


def test_build_backend_requirement_is_a_dev_only_dependency():
    data = _pyproject()
    backend_requirement = data["build-system"]["requires"][0]

    assert backend_requirement == "setuptools==83.0.0"
    assert backend_requirement in data["project"]["optional-dependencies"]["dev"]
    assert not any(
        dependency.lower().startswith("setuptools")
        for dependency in data["project"]["dependencies"]
    )


def test_sdist_manifest_includes_knowledge_schema():
    manifest = (PROJECT_ROOT / "MANIFEST.in").read_text(encoding="utf-8")
    assert (
        "include src/llm_wiki_cli/schemas/llm-wiki-knowledge-v1.schema.json"
        in manifest.splitlines()
    )


def test_ci_verifies_schema_from_wheel_and_sdist_installations():
    ci = (PROJECT_ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
    assert "python -m build" in ci
    assert "python tests/verify_installed_knowledge_schema.py dist" in ci


def test_package_data_includes_bundled_skills():
    data = _pyproject()
    package_data = data["tool"]["setuptools"]["package-data"]["llm_wiki_cli"]
    assert "skills/agent-docs/SKILL.md" in package_data
    assert "skills/agent-docs/reference.md" in package_data
    assert "skills/wiki-sync/SKILL.md" in package_data
    assert "skills/wiki-sync/reference.md" in package_data
    assert "skills/wiki-bootstrap/SKILL.md" in package_data
    assert "skills/wiki-bootstrap/reference.md" in package_data
    assert "skills/wiki-reference/SKILL.md" in package_data
    assert "skills/wiki-reference/reference.md" in package_data
    assert {
        item
        for item in package_data
        if item.startswith("skills/wiki-reference/references/")
    } == {
        "skills/wiki-reference/references/context-query.md",
        "skills/wiki-reference/references/extractors-dependencies.md",
        "skills/wiki-reference/references/governance.md",
        "skills/wiki-reference/references/knowledge-consumption.md",
        "skills/wiki-reference/references/maintenance.md",
        "skills/wiki-reference/references/publishing.md",
        "skills/wiki-reference/references/repository-handoff.md",
        "skills/wiki-reference/references/resources-context.md",
        "skills/wiki-reference/references/surfaces-naming.md",
    }
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
    assert "skills/wiki-semantic-enhance/SKILL.md" in package_data
    assert "skills/wiki-semantic-enhance/reference.md" in package_data


def test_managed_reference_tree_matches_artifact_smoke_contract():
    root = PROJECT_ROOT / "src" / "llm_wiki_cli" / "skills" / "wiki-reference"

    assert release_artifact_smoke._validate_wiki_reference_tree(root) == 11


def test_core_dependencies_do_not_install_model_provider_sdks():
    data = _pyproject()
    dependency_names = {
        re.split(r"[<>=!~;\[]", value, maxsplit=1)[0].strip().lower()
        for value in data["project"].get("dependencies", [])
    }
    assert dependency_names.isdisjoint(
        {
            "anthropic",
            "dashscope",
            "deepseek",
            "google-genai",
            "google-generativeai",
            "mistralai",
            "openai",
        }
    )


def test_package_data_includes_bundled_documentation_hooks_plugin_sample():
    data = _pyproject()
    package_data = data["tool"]["setuptools"]["package-data"]["llm_wiki_cli"]
    assert "examples/plugins/documentation-hooks/llm-wiki-plugin.json" in package_data
    assert "examples/plugins/documentation-hooks/detectors.py" in package_data
    assert "examples/plugins/documentation-hooks/styles.py" in package_data


def test_sdist_manifest_includes_source_documentation_hooks_plugin_sample():
    manifest = (PROJECT_ROOT / "MANIFEST.in").read_text(encoding="utf-8")
    assert (
        "recursive-include examples/plugins/documentation-hooks *.py *.json" in manifest
    )


def test_sdist_manifest_includes_standalone_documentation_guide():
    manifest = (PROJECT_ROOT / "MANIFEST.in").read_text(encoding="utf-8")
    assert "include docs/standalone-documentation.md" in manifest


def test_project_distribution_name_is_pypi_safe_name():
    data = _pyproject()
    assert data["project"]["name"] == "agent-wiki-cli"


def test_project_version_is_release_target():
    data = _pyproject()
    assert data["project"]["version"] == "1.6.0"


def test_standalone_guide_is_installed_as_canonical_shared_documentation():
    data = _pyproject()
    assert data["tool"]["setuptools"]["data-files"] == {
        "share/doc/agent-wiki-cli": ["docs/standalone-documentation.md"]
    }


def test_release_metadata_uses_current_license_fields_and_pinned_backend():
    data = _pyproject()
    assert data["project"]["license"] == "MIT"
    assert data["project"]["license-files"] == ["LICENSE"]
    assert data["build-system"] == {
        "requires": ["setuptools==83.0.0"],
        "build-backend": "release_build_backend",
        "backend-path": ["."],
    }


def test_project_requires_python_3_10_or_newer():
    data = _pyproject()
    assert data["project"]["requires-python"] == ">=3.10"


def test_ci_pairs_selected_python_versions_with_one_os_each():
    assert _ci_test_matrix() == {
        "include": [
            {"os": "ubuntu-24.04", "python-version": "3.10"},
            {"os": "windows-2025", "python-version": "3.13"},
            {"os": "macos-15", "python-version": "3.14"},
        ]
    }


def test_readme_current_support_table_mentions_python_3_10_plus():
    readme = (PROJECT_ROOT / "README.md").read_text(encoding="utf-8")
    assert "| Python | stdlib `ast` | Python 3.10+ |" in readme
    assert "| Python | stdlib `ast` | Python 3.9+ |" not in readme


def test_changelog_1_2_0_documents_python_support_floor():
    changelog = (PROJECT_ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    assert changelog.count("## [1.2.0] - 2026-07-08") == 1

    release_notes = _changelog_section("## [1.2.0]")
    assert "Minimum supported Python is now 3.10" in release_notes
    assert "release automation covers Python 3.10 and 3.13" in release_notes


def test_readme_documents_bundled_skills():
    readme = (PROJECT_ROOT / "README.md").read_text(encoding="utf-8")

    for skill_id in [
        "agent-docs",
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
        "wiki-reference",
        "wiki-semantic-enhance",
        "wiki-sync",
    ]:
        assert f"`{skill_id}`" in readme


def test_public_lifecycle_docs_scope_legacy_generic_schema_migration():
    readme = (PROJECT_ROOT / "README.md").read_text(encoding="utf-8")
    release_notes = _changelog_section("## [Unreleased]")

    for text in (readme, release_notes):
        normalized = " ".join(text.split())
        assert "configured agent's current schema path" in normalized
        assert "`.agents.md`" in normalized
        assert "`AGENTS.md`" in normalized
        assert "user-owned, manually managed content" in normalized


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


def test_release_metadata_documents_surfaces_and_platforms():
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
        "package metadata",
    ]:
        assert required in release_metadata


def test_readme_development_commands_use_project_virtualenv():
    readme = (PROJECT_ROOT / "README.md").read_text(encoding="utf-8")
    readme_lines = {line.strip() for line in readme.splitlines()}

    for required in [
        '.venv/bin/pip install -e ".[dev]"',
        '.venv/bin/pip install -e ".[dev,mcp]"',
        ".venv/bin/python -m build",
    ]:
        assert required in readme

    assert 'pip install -e ".[dev]"' not in readme_lines
    assert not any("/pytest" in line for line in readme_lines)


def test_changelog_1_0_0_documents_public_surfaces():
    release_notes = _changelog_section("## [1.0.0]")
    release_text = " ".join(release_notes.split())

    for required in [
        "static-site",
        "documentation graph",
        "MCP",
        "Python API",
        "context",
        "plugin",
        "migration",
        "self-hosted documentation",
    ]:
        assert required in release_text


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


def test_wiki_integrity_uses_the_automatic_locked_helper_plan():
    workflow = yaml.safe_load(
        (PROJECT_ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
    )
    job = workflow["jobs"]["wiki-integrity"]
    delegation = next(
        step
        for step in job["steps"]
        if step.get("uses") == "./integrations/wiki-integrity"
    )
    assert delegation["with"] == {
        "src-dir": ".",
        "wiki-dir": "docs/llm_wiki",
    }

    action = yaml.safe_load(
        (PROJECT_ROOT / "integrations" / "wiki-integrity" / "action.yml").read_text(
            encoding="utf-8"
        )
    )
    steps = action["runs"]["steps"]
    setup = next(
        step
        for step in steps
        if step.get("name")
        == "Install the locked TypeScript and JavaScript extractor toolchain"
    )["run"]
    prepare = next(
        step
        for step in steps
        if step.get("name") == "Prepare the automatically selected extractor helpers"
    )["run"]

    assert "--mode routine" in setup
    assert "--mode qualification-go" not in setup
    assert "-I -m llm_wiki_cli.cli prepare-extractors" in prepare
    assert '--src-dir "${INPUT_SRC_DIR}"' in prepare
    assert '--cache-dir "${LLM_WIKI_CACHE_DIR}"' in prepare
    assert "--language" not in prepare
    assert "--source-selection" not in prepare
