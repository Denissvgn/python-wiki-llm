"""Tests for markdown I/O helpers."""

from llm_wiki_cli.services.io import read_md, write_md, write_text_output


def test_write_md_normalizes_newlines_and_reads_back(tmp_path):
    path = tmp_path / "wiki" / "page.md"
    write_md(path, "a\r\nb\rc\n")

    assert read_md(path) == "a\nb\nc\n"
    assert not list(path.parent.glob(".page.md.*.tmp"))


def test_read_md_normalizes_existing_platform_newlines(tmp_path):
    path = tmp_path / "wiki" / "page.md"
    path.parent.mkdir(parents=True)
    path.write_bytes(b"a\r\nb\rc\n")

    assert read_md(path) == "a\nb\nc\n"


def test_write_text_output_normalizes_newlines_and_reads_back(tmp_path):
    path = tmp_path / "records" / "output.json"

    result = write_text_output(path, "a\r\nb\rc\n")

    assert result == path
    assert path.read_text(encoding="utf-8") == "a\nb\nc\n"
    assert not list(path.parent.glob(".output.json.*.tmp"))
