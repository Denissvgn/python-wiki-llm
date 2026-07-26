"""Tests for markdown I/O helpers."""

from pathlib import Path

import pytest

from llm_wiki_cli.services import io
from llm_wiki_cli.services.io import (
    read_md,
    write_json_atomic,
    write_md,
    write_text_output,
)


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


def test_write_json_atomic_is_deterministic_utf8_with_one_unix_newline(tmp_path):
    path = tmp_path / "records" / "manifest.json"
    payload = {
        "z-last": {"b": 2, "a": 1},
        "a-first": "café",
    }

    result = write_json_atomic(path, payload)
    first = path.read_bytes()
    write_json_atomic(path, payload)

    assert result == path
    assert first == (
        '{\n  "a-first": "café",\n  "z-last": {\n    "a": 1,\n    "b": 2\n  }\n}\n'
    ).encode("utf-8")
    assert path.read_bytes() == first
    assert b"\r" not in first
    assert first.endswith(b"\n")
    assert not first.endswith(b"\n\n")
    assert not list(path.parent.glob(".manifest.json.*.tmp"))


def test_write_json_atomic_cleans_temp_and_preserves_destination_on_replace_failure(
    tmp_path, monkeypatch
):
    path = tmp_path / "manifest.json"
    path.write_bytes(b"previous\n")

    def fail_replace(source, destination):
        assert Path(source).parent == path.parent
        assert destination == path
        raise OSError("replace failed")

    monkeypatch.setattr(io.os, "replace", fail_replace)

    with pytest.raises(OSError, match="replace failed"):
        write_json_atomic(path, {"next": True})

    assert path.read_bytes() == b"previous\n"
    assert not list(tmp_path.glob(".manifest.json.*.tmp"))


@pytest.mark.parametrize(
    "payload",
    [
        {"invalid": float("nan")},
        {"invalid": float("inf")},
        {"invalid": object()},
        {"invalid": "\ud800"},
    ],
)
def test_write_json_atomic_serialization_failure_creates_no_temp(tmp_path, payload):
    path = tmp_path / "manifest.json"
    path.write_bytes(b"previous\n")

    with pytest.raises((TypeError, ValueError, UnicodeEncodeError)):
        write_json_atomic(path, payload)

    assert path.read_bytes() == b"previous\n"
    assert not list(tmp_path.glob(".manifest.json.*.tmp"))
