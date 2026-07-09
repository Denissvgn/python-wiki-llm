"""Tests for schema block replacement."""

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

    assert "llm-wiki sync --jobs auto --wiki-dir docs/llm_wiki --src-dir ." in content
    assert (
        "llm-wiki lint --strict --jobs auto --wiki-dir docs/llm_wiki --src-dir ."
        in content
    )
    assert (
        "llm-wiki lint --profile --cache-stats --wiki-dir docs/llm_wiki --src-dir ."
        in content
    )
    assert (
        "llm-wiki lint --strict --jobs auto --wiki-dir docs/llm_wiki "
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
    assert "validation loop before commit" in content
    assert "wiki commits separate from code commits" in content
    assert "capture tooling" in content
    assert "agent platform" in content


def test_agent_schema_mentions_tool_issue_reporting():
    content = build_schema_content("generic", "docs/llm_wiki")
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

    assert "llm-wiki sync --jobs auto" in content
    assert "If sync repairs only the manifest" in content
    assert "Sync output is a deterministic AST/docstring skeleton" in content
    assert "Passing lint is not enough" in content
    assert "_Auto-generated from ..._" in content
    assert "llm-wiki prepare-extractors --src-dir ." in content
    assert "wiki-reference" in content
    assert "llm-wiki lint --strict --jobs auto" in content


def test_cli_agent_schema_mentions_manual_sync_workflow():
    content = build_schema_content("claude", "docs/llm_wiki")

    assert "llm-wiki sync --jobs auto" in content
    assert "llm-wiki generate-prompt" in content
    assert "updated automatically on commit" not in content
