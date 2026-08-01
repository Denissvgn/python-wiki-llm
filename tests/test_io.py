"""Tests for markdown I/O helpers."""

import os
import stat
from pathlib import Path
from types import SimpleNamespace

import pytest

from llm_wiki_cli.services import io
from llm_wiki_cli.services.filesystem_guard import atomic_write_private_bytes
from llm_wiki_cli.services.io import (
    first_unsafe_path_component,
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


def test_first_unsafe_path_component_can_trust_explicit_symlink_owner(tmp_path):
    target = tmp_path / "target"
    target.mkdir()
    link = tmp_path / "link"
    try:
        link.symlink_to(target, target_is_directory=True)
    except OSError:
        pytest.skip("Directory symlinks are unavailable to this test account.")
    owner_uid = link.lstat().st_uid

    assert first_unsafe_path_component(link) == link
    assert (
        first_unsafe_path_component(
            link,
            trusted_symlink_uids={owner_uid},
        )
        is None
    )


def test_first_unsafe_path_component_rejects_untrusted_symlink_owner(tmp_path):
    target = tmp_path / "target"
    target.mkdir()
    link = tmp_path / "link"
    try:
        link.symlink_to(target, target_is_directory=True)
    except OSError:
        pytest.skip("Directory symlinks are unavailable to this test account.")
    owner_uid = link.lstat().st_uid
    different_uid = owner_uid + 1

    assert (
        first_unsafe_path_component(
            link,
            trusted_symlink_uids={different_uid},
        )
        == link
    )


def test_first_unsafe_path_component_checks_symlink_target_chain_with_owner_predicate(
    tmp_path,
):
    target = tmp_path / "target"
    target.mkdir()
    inner_link = tmp_path / "inner-link"
    outer_link = tmp_path / "outer-link"
    try:
        inner_link.symlink_to(target, target_is_directory=True)
        outer_link.symlink_to(inner_link, target_is_directory=True)
    except OSError:
        pytest.skip("Directory symlinks are unavailable to this test account.")
    predicate_calls: list[str] = []

    def trusts_outer_link(path: Path) -> bool:
        predicate_calls.append(path.name)
        return path.name == outer_link.name

    unsafe_path = first_unsafe_path_component(
        outer_link,
        trusted_symlink_owner=trusts_outer_link,
    )

    assert predicate_calls == [outer_link.name, inner_link.name]
    assert unsafe_path is not None
    assert unsafe_path.name == inner_link.name
    metadata = unsafe_path.lstat()
    reparse_flag = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0)
    assert stat.S_ISLNK(metadata.st_mode) or bool(
        reparse_flag and metadata.st_file_attributes & reparse_flag
    )


def test_first_unsafe_path_component_does_not_collapse_target_traversal(
    tmp_path, monkeypatch
):
    sensitive = tmp_path / "sensitive"
    nested = sensitive / "nested"
    target = sensitive / "target"
    nested.mkdir(parents=True)
    target.mkdir()
    inner_link = tmp_path / "inner-link"
    outer_link = tmp_path / "outer-link"
    try:
        inner_link.symlink_to(nested, target_is_directory=True)
        outer_link.symlink_to(
            Path("inner-link") / ".." / "target",
            target_is_directory=True,
        )
    except OSError:
        pytest.skip("Directory symlinks are unavailable to this test account.")
    owner_uid = outer_link.lstat().st_uid
    original_lstat = Path.lstat

    def lstat_with_untrusted_inner(path):
        metadata = original_lstat(path)
        if path == inner_link:
            return SimpleNamespace(
                st_file_attributes=getattr(metadata, "st_file_attributes", 0),
                st_mode=metadata.st_mode,
                st_uid=owner_uid + 1,
            )
        return metadata

    monkeypatch.setattr(Path, "lstat", lstat_with_untrusted_inner)

    assert (
        first_unsafe_path_component(
            outer_link,
            trusted_symlink_uids={owner_uid},
        )
        == inner_link
    )


def test_first_unsafe_path_component_walks_parent_parts_with_owner_predicate(
    tmp_path,
):
    project = tmp_path / "project"
    target = tmp_path / "target"
    project.mkdir()
    target.mkdir()
    link = tmp_path / "source-link"
    try:
        link.symlink_to(target, target_is_directory=True)
    except OSError:
        pytest.skip("Directory symlinks are unavailable to this test account.")
    raw_path = project / ".." / "source-link"

    assert (
        first_unsafe_path_component(
            raw_path,
            trusted_symlink_owner=lambda _path: False,
        )
        == link
    )


def test_first_unsafe_path_component_owner_predicate_preserves_target_traversal(
    tmp_path,
):
    project = tmp_path / "project"
    target = tmp_path / "target"
    project.mkdir()
    target.mkdir()
    inner_link = tmp_path / "inner-link"
    outer_link = tmp_path / "outer-link"
    try:
        inner_link.symlink_to(target, target_is_directory=True)
        outer_link.symlink_to(inner_link, target_is_directory=True)
    except OSError:
        pytest.skip("Directory symlinks are unavailable to this test account.")

    raw_path = project / ".." / "outer-link"

    predicate_calls: list[str] = []

    def trusts_outer_link(path: Path) -> bool:
        predicate_calls.append(path.name)
        return path.name == outer_link.name

    unsafe_path = first_unsafe_path_component(
        raw_path,
        trusted_symlink_owner=trusts_outer_link,
    )

    assert predicate_calls == [outer_link.name, inner_link.name]
    assert unsafe_path is not None
    assert unsafe_path.name == inner_link.name
    metadata = unsafe_path.lstat()
    reparse_flag = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0)
    assert stat.S_ISLNK(metadata.st_mode) or bool(
        reparse_flag and metadata.st_file_attributes & reparse_flag
    )
