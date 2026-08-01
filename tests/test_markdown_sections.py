from __future__ import annotations

from llm_wiki_cli.services.knowledge_evidence import sha256_bytes
from llm_wiki_cli.services.markdown_sections import (
    description_table_cells,
    mixed_table_projection,
    parse_markdown_document,
    parse_markdown_sections,
    preserve_level_two_section_exact,
    split_table_row,
    table_description_cells,
)


def test_hierarchy_normalizes_line_endings_and_commits_exact_section_bytes():
    crlf = (
        "# Café\r\n"
        "\r\n"
        "## Empty\r\n"
        "## Parent\r\n"
        "\r\n"
        "### Niño\r\n"
        "body\r\n"
    )
    lf = crlf.replace("\r\n", "\n")

    first = parse_markdown_document(crlf, "llm-wiki://guides/cafe")
    second = parse_markdown_document(lf, "llm-wiki://guides/cafe")

    assert first.normalized_markdown == lf
    assert first.exact_hash == second.exact_hash == sha256_bytes(lf.encode())
    assert first.ordering_hash == second.ordering_hash
    assert [section.title for section in first.sections] == [
        "Café",
        "Empty",
        "Parent",
        "Niño",
    ]
    empty = first.sections[1]
    assert empty.body == ""
    assert empty.exact_bytes == b"## Empty\n"
    assert empty.exact_hash == sha256_bytes(b"## Empty\n")
    nested = first.sections[-1]
    assert nested.parent_locator == first.sections[2].locator
    assert nested.start_byte > nested.start


def test_duplicate_nested_locators_include_each_sibling_occurrence_path():
    markdown = """# Root
## Repeat
### Child
one
## Repeat
### Child
two
## Δ / space
"""
    sections = parse_markdown_sections(markdown, "llm-wiki://modules/example")

    assert sections[1].occurrence_path == (1, 1)
    assert sections[3].occurrence_path == (1, 2)
    assert sections[2].occurrence_path == (1, 1, 1)
    assert sections[4].occurrence_path == (1, 2, 1)
    assert len({section.locator for section in sections}) == len(sections)
    assert sections[2].locator != sections[4].locator
    assert "%CE%94%20%2F%20space~1" in sections[-1].locator


def test_frontmatter_fences_and_indented_code_do_not_create_sections():
    markdown = """---
title: Example
fake: "## Frontmatter"
---
# Real

```python
## Backtick
```

~~~text
### Tilde
~~~

    ## Four-space code

## Visible
"""
    sections = parse_markdown_sections(markdown, "llm-wiki://guides/example")
    assert [section.title for section in sections] == ["Real", "Visible"]

    unclosed = """# Before
## Kept
```text
## Hidden forever
### Also hidden
"""
    sections = parse_markdown_sections(unclosed, "llm-wiki://guides/unclosed")
    assert [section.title for section in sections] == ["Before", "Kept"]


def test_unclosed_frontmatter_is_conservatively_ignored():
    markdown = """---
title: broken
## Not a section
"""
    document = parse_markdown_document(markdown, "llm-wiki://guides/broken")
    assert document.sections == ()
    assert document.exact_hash == sha256_bytes(markdown.encode())


def test_heading_rename_and_reorder_change_locator_or_order_commitment():
    original = "# Root\n## Alpha\nA\n## Beta\nB\n"
    renamed = "# Root\n## Gamma\nA\n## Beta\nB\n"
    reordered = "# Root\n## Beta\nB\n## Alpha\nA\n"

    before = parse_markdown_document(original, "llm-wiki://guides/example")
    after_rename = parse_markdown_document(renamed, "llm-wiki://guides/example")
    after_reorder = parse_markdown_document(reordered, "llm-wiki://guides/example")

    assert before.sections[1].locator != after_rename.sections[1].locator
    assert before.ordering_hash != after_rename.ordering_hash
    assert before.ordering_hash != after_reorder.ordering_hash


def test_pipe_table_parser_supports_escaped_and_inline_code_pipes():
    row = r"| `a|b` | escaped \| value | ``x|`|y`` | prose |"
    assert split_table_row(row) == [
        "`a|b`",
        r"escaped \| value",
        "``x|`|y``",
        "prose",
    ]


def test_mixed_projection_separates_structure_and_duplicate_semantics():
    before = r"""## Methods

| Method | Signature | Description |
|---|---|---|
| `a|b` | `a(x\|y)` | First \| description |
| `a|b` | ``a(`x|y`)`` | Second description |
| `new` | `new()` | — |
"""
    structural_change = before.replace("`a(x\\|y)`", "`a(x\\|y, z)`")
    semantic_change = before.replace(
        "Second description",
        "Human-edited description",
    )

    first = mixed_table_projection(before)
    structural = mixed_table_projection(structural_change)
    semantic = mixed_table_projection(semantic_change)

    assert [(cell.key, cell.occurrence) for cell in first.description_cells] == [
        ("a|b", 1),
        ("a|b", 2),
        ("new", 1),
    ]
    assert first.semantic_hash == structural.semantic_hash
    assert first.structural_hash != structural.structural_hash
    assert first.structural_hash == semantic.structural_hash
    assert first.semantic_hash != semantic.semantic_hash
    assert first.semantic_projection["description_cells"] == [
        {"key": "a|b", "description": "Second description"}
    ]


def test_projection_observes_duplicates_without_changing_legacy_collapse():
    markdown = """## Methods

| Method | Description |
|---|---|
| `same` | First |
| `same` | Second |
"""
    occurrences = description_table_cells(markdown)
    assert [(cell.key, cell.occurrence) for cell in occurrences] == [
        ("same", 1),
        ("same", 2),
    ]
    # Sync compatibility remains the historical last-duplicate-wins mapping.
    assert table_description_cells(markdown, "Methods") == {"same": "Second"}


def test_exact_level_two_preservation_keeps_first_duplicate_verbatim():
    existing = "## Notes\r\n\r\nFirst.\r\n## Notes\r\n\r\nSecond.\r\n"
    generated = "## Notes\n\nGenerated.\n## Notes\n\nGenerated two.\n"
    assert preserve_level_two_section_exact(existing, generated, "Notes") == (
        "## Notes\r\n\r\nFirst.\r\n"
        "## Notes\n\nGenerated two.\n"
    )
