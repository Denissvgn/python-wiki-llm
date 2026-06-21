"""Tests for schema block replacement."""

from llm_wiki_cli.services.schema import (
    CONSTRAINT_END,
    CONSTRAINT_START,
    build_schema_content,
    replace_schema_block,
)


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
    assert "llm-wiki prepare-extractors --src-dir ." in content
    assert "LLM_WIKI_GO=/path/to/go" in content
    assert "persistent inventory cache" in content
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
        "docs/llm_wiki/flows/",
        "docs/llm_wiki/infrastructure/",
        "docs/llm_wiki/dependencies.md",
        "docs/llm_wiki/load-order.md",
    ]:
        assert path in content
    assert "Do not edit generated Mermaid diagrams by hand" in content
    assert "semantic sections" in content
    assert "Static-site mirror output" in content
    assert "not as an editable source of truth" in content
    assert (
        "Docusaurus exports include generated front matter and sidebars.json" in content
    )


def test_ide_schema_mentions_incremental_sync_workflow():
    content = build_schema_content("copilot", "docs/llm_wiki")

    assert "llm-wiki sync --jobs auto" in content
    assert "If sync repairs only the manifest" in content
    assert "Sync output is a deterministic AST/docstring skeleton" in content
    assert "Passing lint is not enough" in content
    assert "_Auto-generated from ..._" in content
    assert "llm-wiki prepare-extractors --src-dir ." in content
    assert "LLM_WIKI_GO=/path/to/go" in content
    assert "llm-wiki lint --strict --jobs auto" in content


def test_cli_agent_schema_mentions_manual_sync_workflow():
    content = build_schema_content("claude", "docs/llm_wiki")

    assert "llm-wiki sync --jobs auto" in content
    assert "llm-wiki generate-prompt" in content
    assert "updated automatically on commit" not in content
