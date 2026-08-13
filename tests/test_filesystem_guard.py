"""Direct contracts for guarded filesystem mutation primitives."""

from __future__ import annotations

import os

import pytest

from llm_wiki_cli.services import filesystem_guard as guard


pytestmark = pytest.mark.skipif(os.name == "nt", reason="POSIX descriptor contracts")


def test_expected_file_change_at_claim_is_preserved(tmp_path, monkeypatch) -> None:
    target = tmp_path / "managed.md"
    expected = b"expected\n"
    changed = b"concurrent custom\n"
    target.write_bytes(expected)
    real_rename = guard.os.rename
    injected = False

    def change_then_rename(source, destination, *args, **kwargs):
        nonlocal injected
        if not injected and source == target.name:
            injected = True
            target.write_bytes(changed)
        return real_rename(source, destination, *args, **kwargs)

    monkeypatch.setattr(guard.os, "rename", change_then_rename)

    with pytest.raises(OSError, match="changed after preflight"):
        guard.atomic_write_guarded_bytes(
            target,
            b"managed replacement\n",
            expected_existing=expected,
        )

    assert target.read_bytes() == changed


def test_absent_target_appearing_at_commit_is_preserved(tmp_path, monkeypatch) -> None:
    target = tmp_path / "managed.md"
    appeared = b"new custom file\n"
    real_link = guard.os.link
    injected = False

    def appear_then_link(source, destination, *args, **kwargs):
        nonlocal injected
        if not injected and destination == target.name:
            injected = True
            target.write_bytes(appeared)
        return real_link(source, destination, *args, **kwargs)

    monkeypatch.setattr(guard.os, "link", appear_then_link)

    with pytest.raises(FileExistsError):
        guard.atomic_write_guarded_bytes(
            target,
            b"managed replacement\n",
            expected_existing=None,
        )

    assert target.read_bytes() == appeared


@pytest.mark.parametrize("existing", [None, b"expected\n"])
def test_post_link_replacement_fails_identity_check(
    tmp_path,
    monkeypatch,
    existing: bytes | None,
) -> None:
    target = tmp_path / "managed.md"
    if existing is not None:
        target.write_bytes(existing)
    concurrent = b"concurrent same-mode replacement\n"
    real_unlink = guard.os.unlink
    injected = False

    def replace_after_link(path, *args, **kwargs):
        nonlocal injected
        if (
            not injected
            and isinstance(path, str)
            and path.endswith(".private-tmp")
            and kwargs.get("dir_fd") is not None
        ):
            injected = True
            target.unlink()
            target.write_bytes(concurrent)
        return real_unlink(path, *args, **kwargs)

    monkeypatch.setattr(guard.os, "unlink", replace_after_link)

    with pytest.raises(OSError, match="safe file metadata"):
        guard.atomic_write_guarded_bytes(
            target,
            b"managed replacement\n",
            expected_existing=existing,
        )

    assert target.read_bytes() == concurrent
    if existing is not None:
        retained = list(tmp_path.glob(".llm-wiki-*.replaced"))
        assert len(retained) == 1
        assert retained[0].read_bytes() == existing


def test_unlink_restore_never_replaces_concurrent_target(tmp_path, monkeypatch) -> None:
    target = tmp_path / "managed.md"
    target.write_bytes(b"changed before removal\n")
    concurrent = b"new concurrent file\n"
    real_link = guard.os.link
    injected = False

    def occupy_then_restore(source, destination, *args, **kwargs):
        nonlocal injected
        if not injected and destination == target.name:
            injected = True
            target.write_bytes(concurrent)
        return real_link(source, destination, *args, **kwargs)

    monkeypatch.setattr(guard.os, "link", occupy_then_restore)

    with pytest.raises(OSError, match="changed after preflight"):
        guard.unlink_guarded_bytes(target, expected=b"expected\n")

    assert target.read_bytes() == concurrent
    retained = list(tmp_path.glob(".llm-wiki-*.unlink-check"))
    assert len(retained) == 1
    assert retained[0].read_bytes() == b"changed before removal\n"


def test_directory_claim_is_restored_without_overwrite(tmp_path, monkeypatch) -> None:
    target = tmp_path / "managed.md"
    target.write_bytes(b"expected\n")
    real_rename = guard.os.rename
    injected = False

    def directory_then_rename(source, destination, *args, **kwargs):
        nonlocal injected
        if not injected and source == target.name:
            injected = True
            target.unlink()
            target.mkdir()
            (target / "user.txt").write_text("user\n", encoding="utf-8")
        return real_rename(source, destination, *args, **kwargs)

    monkeypatch.setattr(guard.os, "rename", directory_then_rename)

    with pytest.raises(OSError):
        guard.atomic_write_guarded_bytes(
            target,
            b"managed replacement\n",
            expected_existing=b"expected\n",
        )

    assert (target / "user.txt").read_text(encoding="utf-8") == "user\n"


def test_tree_addition_at_claim_aborts_and_restores(tmp_path, monkeypatch) -> None:
    root = tmp_path / "wiki"
    root.mkdir()
    (root / "index.md").write_text("index\n", encoding="utf-8")
    manifest = guard.guarded_tree_manifest(root)
    identity = root.stat().st_dev, root.stat().st_ino
    real_rename = guard.os.rename
    injected = False

    def add_then_claim(source, destination, *args, **kwargs):
        nonlocal injected
        if not injected and source == root.name and destination == "tree":
            injected = True
            (root / "new-user-note.txt").write_text("new\n", encoding="utf-8")
        return real_rename(source, destination, *args, **kwargs)

    monkeypatch.setattr(guard.os, "rename", add_then_claim)

    with pytest.raises(OSError, match="contents changed"):
        guard.remove_guarded_tree(
            root,
            expected_identity=identity,
            expected_manifest=manifest,
        )

    assert (root / "index.md").exists()
    assert (root / "new-user-note.txt").read_text(encoding="utf-8") == "new\n"


def test_tree_addition_after_manifest_check_is_not_deleted(
    tmp_path,
    monkeypatch,
) -> None:
    root = tmp_path / "wiki"
    root.mkdir()
    (root / "index.md").write_text("index\n", encoding="utf-8")
    manifest = guard.guarded_tree_manifest(root)
    identity = root.stat().st_dev, root.stat().st_ino
    real_manifest = guard._guarded_tree_manifest_posix_fd
    injected = False

    def manifest_then_add(directory_fd, *, prefix=""):
        nonlocal injected
        result = real_manifest(directory_fd, prefix=prefix)
        if not injected and not prefix:
            injected = True
            descriptor = os.open(
                "new-user-note.txt",
                os.O_WRONLY | os.O_CREAT | os.O_EXCL,
                0o600,
                dir_fd=directory_fd,
            )
            os.write(descriptor, b"new\n")
            os.close(descriptor)
        return result

    monkeypatch.setattr(
        guard,
        "_guarded_tree_manifest_posix_fd",
        manifest_then_add,
    )

    with pytest.raises(OSError, match="directory entries changed"):
        guard.remove_guarded_tree(
            root,
            expected_identity=identity,
            expected_manifest=manifest,
        )

    assert (root / "index.md").exists()
    assert (root / "new-user-note.txt").read_text(encoding="utf-8") == "new\n"
