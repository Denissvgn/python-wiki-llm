"""Tests for schema block replacement."""

from llm_wiki_cli.services.schema import CONSTRAINT_END, CONSTRAINT_START, replace_schema_block


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
