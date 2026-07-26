"""Tests for markdown I/O helpers."""

import os
import stat
from pathlib import Path

import pytest

from llm_wiki_cli.services.filesystem_guard import atomic_write_private_bytes
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
