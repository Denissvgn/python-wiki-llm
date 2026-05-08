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
        "User intro\n\n"
        f"{CONSTRAINT_START}\nold\n{CONSTRAINT_END}\n"
        "\nUser outro\n",
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
    assert "llm-wiki lint --strict --jobs auto --wiki-dir docs/llm_wiki --src-dir ." in content
    assert "llm-wiki lint --profile --cache-stats --wiki-dir docs/llm_wiki --src-dir ." in content
    assert "llm-wiki prepare-extractors --src-dir ." in content
    assert "persistent inventory cache" in content
    assert "large-diff guard" in content


def test_ide_schema_mentions_incremental_sync_workflow():
    content = build_schema_content("copilot", "docs/llm_wiki")

    assert "llm-wiki sync --jobs auto" in content
    assert "If sync repairs only the manifest" in content
    assert "llm-wiki prepare-extractors --src-dir ." in content
    assert "llm-wiki lint --strict --jobs auto" in content
