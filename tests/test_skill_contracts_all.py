"""Every bundled skill is gated by the executable contract harness."""

from __future__ import annotations

from pathlib import Path

import pytest

from llm_wiki_cli.services import skills
from tests.skill_contract_harness import (
    SkillContractError,
    WORKFLOW_MARKER_EDIT,
    WORKFLOW_MARKER_REANCHOR,
    WORKFLOW_MARKER_STRICT,
    bundled_skill_dirs,
    collect_skill_contract_errors,
    extract_cli_examples,
    extract_context_request_examples,
    extract_mcp_tool_examples,
    extract_query_graph_examples,
    extract_workflow_markers,
    validate_workflow_ordering,
)


SKILL_DIRS = bundled_skill_dirs(skills.BUNDLED_SKILLS_ROOT)
SKILL_IDS = tuple(path.name for path in SKILL_DIRS)

# Skills whose documented workflow mutates canonical wiki Markdown and then
# validates it; each must exercise all three ordering markers.
MANAGED_MUTATION_SKILLS = (
    "dep-audit",
    "doc-review",
    "onboarding-guide",
    "usage-examples",
    "user-docs-author",
    "wiki-bootstrap",
    "wiki-sync",
)


def _write_manifest(tmp_path: Path, skill_id: str, body: str) -> Path:
    skill = tmp_path / skill_id
    skill.mkdir()
    manifest = skill / skills.SKILL_MANIFEST_NAME
    manifest.write_text(body, encoding="utf-8")
    return manifest


def test_every_bundled_skill_directory_is_gated():
    assert SKILL_IDS
    assert set(SKILL_IDS) == {
        entry.name
        for entry in skills.BUNDLED_SKILLS_ROOT.iterdir()
        if entry.is_dir()
    }


@pytest.mark.parametrize("skill_dir", SKILL_DIRS, ids=SKILL_IDS)
def test_bundled_skill_documents_no_contract_violations(skill_dir: Path):
    errors = collect_skill_contract_errors(skill_dir)

    assert not errors, "\n".join(errors)


@pytest.mark.parametrize("skill_dir", SKILL_DIRS, ids=SKILL_IDS)
def test_documented_commands_are_extracted_rather_than_silently_skipped(
    skill_dir: Path,
):
    documents_command = any(
        line.strip().startswith("llm-wiki ")
        for path in skill_dir.rglob("*.md")
        for line in path.read_text(encoding="utf-8").splitlines()
    )

    assert not documents_command or extract_cli_examples(skill_dir)


def test_corpus_exercises_every_contract_class():
    root = skills.BUNDLED_SKILLS_ROOT
    manifests = tuple(root.rglob("*.md"))

    assert extract_cli_examples(root)
    assert extract_context_request_examples(root)
    assert [
        example for path in manifests for example in extract_query_graph_examples(path)
    ]
    assert [
        example for path in manifests for example in extract_mcp_tool_examples(path)
    ]
    assert {
        marker.kind
        for skill_dir in SKILL_DIRS
        for marker in extract_workflow_markers(
            skill_dir / skills.SKILL_MANIFEST_NAME
        )
    } == {
        WORKFLOW_MARKER_EDIT,
        WORKFLOW_MARKER_REANCHOR,
        WORKFLOW_MARKER_STRICT,
    }


@pytest.mark.parametrize("skill_id", MANAGED_MUTATION_SKILLS)
def test_managed_mutation_skill_exercises_every_ordering_marker(skill_id: str):
    manifest = (
        skills.BUNDLED_SKILLS_ROOT / skill_id / skills.SKILL_MANIFEST_NAME
    )

    kinds = {marker.kind for marker in extract_workflow_markers(manifest)}

    assert kinds == {
        WORKFLOW_MARKER_EDIT,
        WORKFLOW_MARKER_REANCHOR,
        WORKFLOW_MARKER_STRICT,
    }


def test_ordering_harness_accepts_reanchored_workflow(tmp_path):
    manifest = _write_manifest(
        tmp_path,
        "reanchored",
        "\n".join(
            [
                "## Steps",
                "",
                "1. **Edit semantic surfaces only.** Rewrite canonical prose.",
                "",
                "2. **Re-anchor, then verify.**",
                "",
                "   ```bash",
                "   llm-wiki sync --jobs 1 --src-dir . --wiki-dir docs/llm_wiki",
                "   llm-wiki lint --strict --src-dir . --wiki-dir docs/llm_wiki",
                "   llm-wiki ci-check --src-dir . --wiki-dir docs/llm_wiki",
                "   ```",
                "",
            ]
        ),
    )

    validate_workflow_ordering(manifest)


def test_ordering_harness_rejects_edit_before_strict_validation(tmp_path):
    manifest = _write_manifest(
        tmp_path,
        "unanchored",
        "\n".join(
            [
                "## Steps",
                "",
                "1. **Refresh the wiki.**",
                "",
                "   ```bash",
                "   llm-wiki sync --jobs 1 --src-dir . --wiki-dir docs/llm_wiki",
                "   ```",
                "",
                "2. **Edit semantic surfaces only.** Rewrite canonical prose.",
                "",
                "3. **Validate.**",
                "",
                "   ```bash",
                "   llm-wiki lint --strict --src-dir . --wiki-dir docs/llm_wiki",
                "   ```",
                "",
            ]
        ),
    )

    with pytest.raises(
        SkillContractError,
        match=r"unanchored .*SKILL\.md:14.*canonical edit documented at line 9",
    ):
        validate_workflow_ordering(manifest)


def test_ordering_harness_rejects_dry_run_sync_as_reanchor(tmp_path):
    manifest = _write_manifest(
        tmp_path,
        "preview-only",
        "\n".join(
            [
                "## Workflow",
                "",
                "1. **Append the semantic log line.** Edit canonical Markdown.",
                "",
                "   ```bash",
                "   llm-wiki sync --dry-run --src-dir . --wiki-dir docs/llm_wiki",
                "   llm-wiki ci-check --src-dir . --wiki-dir docs/llm_wiki",
                "   ```",
                "",
            ]
        ),
    )

    with pytest.raises(
        SkillContractError,
        match=r"preview-only .*no intervening re-anchor sync",
    ):
        validate_workflow_ordering(manifest)


def test_ordering_harness_ignores_frontmatter_and_precondition_prose(tmp_path):
    manifest = _write_manifest(
        tmp_path,
        "read-only",
        "\n".join(
            [
                "---",
                "name: read-only",
                "description: Never edit canonical Markdown with this skill.",
                "---",
                "",
                "## Preconditions",
                "",
                "- Do not author semantic wiki prose here.",
                "",
                "## Steps",
                "",
                "1. **Collect diagnostics.**",
                "",
                "   ```bash",
                "   llm-wiki lint --strict --src-dir . --wiki-dir docs/llm_wiki",
                "   ```",
                "",
            ]
        ),
    )

    validate_workflow_ordering(manifest)

    assert [marker.kind for marker in extract_workflow_markers(manifest)] == [
        WORKFLOW_MARKER_STRICT
    ]


def test_contract_collector_reports_every_defect_class_together(tmp_path):
    manifest = _write_manifest(
        tmp_path,
        "broken",
        "\n".join(
            [
                "## Steps",
                "",
                "1. **Query the graph.** Use MCP `query_graph` with",
                '   `{"query_type": "callers", "value": "run", "limit": 20}`.',
                "",
                "2. **Edit semantic surfaces only.** Rewrite canonical prose.",
                "",
                "   ```bash",
                "   llm-wiki extract --cache-dir cache",
                "   llm-wiki lint --strict --src-dir . --wiki-dir docs/llm_wiki",
                "   ```",
                "",
            ]
        ),
    )

    errors = collect_skill_contract_errors(manifest.parent)

    assert len(errors) == 3
    assert any("unrecognized arguments" in error for error in errors)
    assert any("Unknown query field: query_type" in error for error in errors)
    assert any("no intervening re-anchor sync" in error for error in errors)
