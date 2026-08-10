"""Tests for schema block replacement."""

from pathlib import Path

from llm_wiki_cli.services.schema import (
    CONSTRAINT_END,
    CONSTRAINT_START,
    build_schema_content,
    replace_schema_block,
)


def _squash_ws(content: str) -> str:
    return " ".join(content.split())


def test_replace_schema_block_preserves_literal_backslashes(tmp_path):
    schema_path = tmp_path / "AGENTS.md"
    schema_path.write_text(
        f"User intro\n\n{CONSTRAINT_START}\nold\n{CONSTRAINT_END}\n\nUser outro\n",
        encoding="utf-8",
    )
    new_content = f"{CONSTRAINT_START}\npath \\1 \\g<name>\n{CONSTRAINT_END}\n"

    replace_schema_block(schema_path, new_content)

    text = schema_path.read_text(encoding="utf-8")
    assert "path \\1 \\g<name>" in text
    assert "User intro" in text
    assert "User outro" in text


def test_agent_schema_mentions_current_sync_and_lint_runtime():
    content = build_schema_content("generic", "docs/llm_wiki")

    assert "llm-wiki sync --jobs 1 --wiki-dir docs/llm_wiki --src-dir ." in content
    assert (
        "llm-wiki lint --strict --jobs 1 --wiki-dir docs/llm_wiki --src-dir ."
        in content
    )
    assert (
        "llm-wiki lint --profile --cache-stats --wiki-dir docs/llm_wiki --src-dir ."
        in content
    )
    assert (
        "llm-wiki lint --strict --jobs 1 --wiki-dir docs/llm_wiki "
        "--src-dir <repo> --allow-external-src" in content
    )
    assert "llm-wiki prepare-extractors --src-dir ." in content
    assert "persistent inventory cache" in content
    assert "--allow-external-src" in content
    assert "project-root write guard" in content
    assert "large-diff guard" in content
    assert "semantic pass" in content
    assert "Lint passing is not enough" in content
    assert "_Auto-generated from ..._" in content


def test_agent_schema_pins_configured_source_selection_in_maintenance_recipes():
    profile = "config/team selection.json"
    content = build_schema_content(
        "generic",
        "docs/llm_wiki",
        source_selection=profile,
    )
    selection_arg = "--source-selection 'config/team selection.json'"

    for recipe in (
        "llm-wiki context --budget 8000 --src-dir . --format markdown "
        "--focus changed --knowledge-mode auto --read-only",
        "llm-wiki extract --src-dir .",
        "llm-wiki generate-prompt",
        "llm-wiki lint --strict --jobs 1",
        "llm-wiki prepare-extractors --src-dir .",
        "llm-wiki sync --jobs 1",
    ):
        recipe_lines = [line for line in content.splitlines() if recipe in line]
        assert recipe_lines
        assert all(selection_arg in line for line in recipe_lines)


def test_bundled_sync_skill_preserves_profile_and_uses_selected_diffs_only():
    skill_root = (
        Path(__file__).parents[1] / "src" / "llm_wiki_cli" / "skills" / "wiki-sync"
    )
    skill = (skill_root / "SKILL.md").read_text(encoding="utf-8")
    reference = (skill_root / "reference.md").read_text(encoding="utf-8")

    assert "--source-selection <profile>" in skill
    assert "--source-selection <profile>" in reference
    assert "never run an unrestricted `git diff` or `git diff --stat`" in skill
    assert "never read an unrestricted diff or stat" in reference


def test_agent_schema_is_scope_and_resource_aware():
    content = build_schema_content("generic", "docs/llm_wiki")
    text = _squash_ws(content)

    assert "## Resource-aware execution" in content
    assert "For broad repository-wide work" in content
    assert (
        "llm-wiki context --budget 8000 --src-dir . --format markdown "
        "--focus changed --knowledge-mode auto --read-only" in content
    )
    assert "For a narrow task with supplied files or a supplied diff" in content
    assert "skip the full context scan" in text
    assert "full deep inventory" in content
    assert "bound emitted output, not scan cost" in text
    assert "The supervisor owns heavy-gate scheduling" in content
    assert "must not launch a heavy gate unless the supervisor" in text
    assert "Use `--jobs 1` for interactive" in content
    assert "isolated terminal or controlled CI runner" in text
    assert "mark unfinished gates inconclusive" in text


def test_agent_schema_distinguishes_aggregate_and_concept_freshness():
    content = build_schema_content("generic", "docs/llm_wiki")
    text = _squash_ws(content)

    assert "`freshness`, and `freshness_evaluated`" in text
    assert "`evaluated (N concepts)`" in text
    assert "`unevaluated (snapshot-only read)`" in text
    assert "one result per concept" in text
    assert "does not mean every concept had a live comparison" in text
    assert "state, reason, and `live_comparison_performed`" in text
    assert "`live_comparison_performed: false` remains non-live" in text


def test_agent_schema_mentions_dependency_architecture_responsibilities():
    content = build_schema_content("generic", "docs/llm_wiki")

    assert "dependencies.md" in content
    assert "load-order.md" in content
    assert "--skip-dependencies" in content
    assert "## Notes" in content
    assert "agent-owned" in content
    assert "Import cycles" in content
    assert "undeclared" in content
    assert "unused" in content
    assert "warning diagnostics" in content


def test_agent_schema_points_to_wiki_reference_skill():
    content = build_schema_content("generic", "docs/llm_wiki")
    text = _squash_ws(content)

    assert "## Deep reference (read on demand)" in content
    # generic agents get the platform-neutral skills home
    assert ".llm-wiki/skills/wiki-reference/reference.md" in content
    # claude gets its native, auto-indexed skills directory
    claude_content = build_schema_content("claude", "docs/llm_wiki")
    assert ".claude/skills/wiki-reference/reference.md" in claude_content
    assert "llm-wiki skills install" in content
    assert "llm-wiki skills export --dest exported-skills" in content
    assert "Do not read it upfront" in text
    # Inline pointers keep trigger conditions next to the rules that need them.
    assert "Dependency reconciliation" in content
    assert "Extractor" in content
    assert "Static-site export" in content


def test_agent_schema_mentions_data_flow_review_responsibilities():
    content = build_schema_content("generic", "docs/llm_wiki")

    assert "## Data flow" in content
    assert "static-analysis gaps" in content
    assert "## Behavior" in content
    assert "observed side effects" in content


def test_agent_schema_mentions_canonical_surfaces_and_generated_ownership():
    content = build_schema_content("generic", "docs/llm_wiki")

    assert "canonical wiki surfaces" in content
    for path in [
        "docs/llm_wiki/index.md",
        "docs/llm_wiki/log.md",
        "docs/llm_wiki/entities/",
        "docs/llm_wiki/modules/",
        "docs/llm_wiki/workflows/",
        "docs/llm_wiki/guides/",
        "docs/llm_wiki/flows/",
        "docs/llm_wiki/infrastructure/",
        "docs/llm_wiki/dependencies.md",
        "docs/llm_wiki/load-order.md",
    ]:
        assert path in content
    assert "Do not edit generated Mermaid diagrams by hand" in content
    assert "Diagram style plugins may configure generated Mermaid flowchart" in content
    assert "cannot inject arbitrary Markdown" in content
    assert "semantic sections" in content
    assert "`sync` does not generate or overwrite guide prose" in content
    assert "Static-site mirror output" in content
    assert "not as an editable source of truth" in content


def test_agent_schema_mentions_user_docs_usage_example_workflow():
    content = build_schema_content("generic", "docs/llm_wiki")
    text = _squash_ws(content)

    assert "## User docs and usage examples" in content
    assert (
        "wiki-bootstrap -> wiki-sync -> user-docs-author -> usage-examples -> publish-docs"
        in text
    )
    assert "assets/<surface>/<page-stem>/" in content
    assert "semantic prose only" in content
    assert "generated blocks are CLI-owned" in content
    assert "source targets read-only" in content
    assert "no toolchain installs" in content
    assert "validation loop before delivery" in content
    assert "When repository policy permits a wiki commit" in content
    assert "keep it separate from code commits" in text
    assert "capture tooling" in content
    assert "agent platform" in content


def test_agent_schema_requires_repository_aware_git_handoff():
    content = build_schema_content("generic", "docs/llm_wiki")
    text = _squash_ws(content)

    assert "## Repository delivery preflight" in content
    assert (
        "git check-ignore --no-index -- docs/llm_wiki/ "
        "docs/llm_wiki/index.md" in content
    )
    assert "user's instructions and every applicable local repository rule" in text
    assert "Exit 0 means the wiki is local-only" in text
    assert "Exit 1 is only conditionally Git-eligible" in text
    assert "Any other result is indeterminate and fails closed" in text
    assert "do not stage, commit, force-add, or change ignore/exclude rules" in text
    assert '"Repository-aware Git handoff" policy in `wiki-reference`' in text
    assert "`external_agent_docs` keeps its stricter packet boundary" in text


def test_agent_schema_omits_tool_issue_reporting_by_default():
    content = build_schema_content("generic", "docs/llm_wiki")

    assert "## Report llm-wiki tool issues" not in content
    assert "llm-wiki-issues/" not in content


def test_agent_schema_mentions_tool_issue_reporting_when_enabled():
    content = build_schema_content("generic", "docs/llm_wiki", issue_reporting=True)
    text = _squash_ws(content)

    assert "## Report llm-wiki tool issues" in content
    assert "never work around it silently" in text
    assert "llm-wiki-issues/<YYYY-MM-DD>-<short-slug>.md" in content
    assert "outside `docs/llm_wiki/` so lint does not flag them" in text
    assert "exact command and flags you ran" in content
    assert "`llm-wiki --version` output" in content
    assert "minimal reproduction steps" in text
    assert "addressed upstream" in content


def test_ide_schema_mentions_incremental_sync_workflow():
    content = build_schema_content("copilot", "docs/llm_wiki")

    assert "llm-wiki sync --jobs 1" in content
    assert "If sync repairs only the manifest" in content
    assert "Sync output is a deterministic AST/docstring skeleton" in content
    assert "Passing lint is not enough" in content
    assert "_Auto-generated from ..._" in content
    assert "llm-wiki prepare-extractors --src-dir ." in content
    assert "wiki-reference" in content
    assert "llm-wiki lint --strict --jobs 1" in content


def test_cli_agent_schema_mentions_manual_sync_workflow():
    content = build_schema_content("claude", "docs/llm_wiki")

    assert "llm-wiki sync --jobs 1" in content
    assert "llm-wiki generate-prompt" in content
    assert "updated automatically on commit" not in content
