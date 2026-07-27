"""Tests for markdown I/O helpers."""

import os
import stat
from pathlib import Path

import pytest

from llm_wiki_cli.services import io
from llm_wiki_cli.services.filesystem_guard import atomic_write_private_bytes
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


def test_atomic_write_private_bytes_replaces_with_private_durable_file(tmp_path):
    target = (tmp_path / "packet.json").resolve()
    target.write_bytes(b"old")
    if os.name != "nt":
        target.chmod(0o644)

    result = atomic_write_private_bytes(target, b'{"private":true}\n')

    assert result == target
    assert target.read_bytes() == b'{"private":true}\n'
    assert not list(tmp_path.glob(".llm-wiki-*.private-tmp"))
    if os.name != "nt":
        assert stat.S_IMODE(target.stat().st_mode) == 0o600


def test_atomic_write_private_bytes_rejects_relative_and_redirected_targets(
    tmp_path,
):
    with pytest.raises(OSError, match="absolute"):
        atomic_write_private_bytes(Path(tmp_path.name) / "packet.json", b"private")

    victim = tmp_path / "victim.json"
    victim.write_bytes(b"unchanged")
    target = tmp_path / "packet.json"
    try:
        target.symlink_to(victim)
    except OSError:
        pytest.skip("Symlinks are unavailable to this test account.")

    with pytest.raises(OSError, match="regular file|reparse"):
        atomic_write_private_bytes(target, b"private")

    assert victim.read_bytes() == b"unchanged"

    real_parent = tmp_path / "real-parent"
    real_parent.mkdir()
    linked_parent = tmp_path / "linked-parent"
    try:
        linked_parent.symlink_to(real_parent, target_is_directory=True)
    except OSError:
        pytest.skip("Directory symlinks are unavailable to this test account.")

    with pytest.raises(OSError):
        atomic_write_private_bytes(linked_parent / "packet.json", b"private")

    assert not (real_parent / "packet.json").exists()
