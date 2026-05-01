"""Tests for markdown I/O helpers."""

from llm_wiki_cli.services.io import read_md, write_md


def test_write_md_normalizes_newlines_and_reads_back(tmp_path):
    path = tmp_path / "wiki" / "page.md"
    write_md(path, "a\r\nb\rc\n")

    assert read_md(path) == "a\nb\nc\n"
    assert not list(path.parent.glob(".page.md.*.tmp"))
