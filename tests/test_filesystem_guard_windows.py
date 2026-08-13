"""Native Windows contracts for guarded public files and tree removal."""

from __future__ import annotations

import os

import pytest

from llm_wiki_cli.services import filesystem_guard as guard


pytestmark = pytest.mark.skipif(os.name != "nt", reason="native Windows contracts")


def test_public_guarded_create_and_snapshot_replace(tmp_path) -> None:
    target = tmp_path / "managed.md"

    guard.atomic_write_guarded_bytes(
        target,
        b"first\n",
        mode=0o644,
        expected_existing=None,
    )
    guard.atomic_write_guarded_bytes(
        target,
        b"second\n",
        mode=0o644,
        expected_existing=b"first\n",
    )

    assert target.read_bytes() == b"second\n"


def test_public_guarded_mismatch_preserves_current_bytes(tmp_path) -> None:
    target = tmp_path / "managed.md"
    target.write_bytes(b"custom\n")

    with pytest.raises(OSError):
        guard.atomic_write_guarded_bytes(
            target,
            b"replacement\n",
            mode=0o644,
            expected_existing=b"expected\n",
        )

    assert target.read_bytes() == b"custom\n"


def test_public_absent_snapshot_collision_preserves_target_and_cleans_stage(
    tmp_path,
    monkeypatch,
) -> None:
    target = tmp_path / "managed.md"
    real_move = guard.move_windows_path_write_through

    def collide(source, destination, *, replace_existing):
        if destination == target and not replace_existing:
            target.write_bytes(b"concurrent\n")
        return real_move(
            source,
            destination,
            replace_existing=replace_existing,
        )

    monkeypatch.setattr(guard, "move_windows_path_write_through", collide)

    with pytest.raises(OSError, match="appeared after preflight"):
        guard.atomic_write_guarded_bytes(
            target,
            b"managed\n",
            mode=0o644,
            expected_existing=None,
        )

    assert target.read_bytes() == b"concurrent\n"
    assert not list(tmp_path.glob(".llm-wiki-*.guarded-tmp"))


def test_private_guarded_create_and_snapshot_replace(tmp_path) -> None:
    target = tmp_path / ".llm-wiki-agent"

    guard.atomic_write_private_bytes(
        target,
        b"first\n",
        expected_existing=None,
    )
    guard.atomic_write_private_bytes(
        target,
        b"second\n",
        expected_existing=b"first\n",
    )

    assert target.read_bytes() == b"second\n"


def test_private_guarded_mismatch_preserves_current_bytes(tmp_path) -> None:
    target = tmp_path / ".llm-wiki-agent"
    guard.atomic_write_private_bytes(target, b"custom\n")

    with pytest.raises(OSError):
        guard.atomic_write_private_bytes(
            target,
            b"replacement\n",
            expected_existing=b"expected\n",
        )

    assert target.read_bytes() == b"custom\n"


def test_private_absent_snapshot_collision_preserves_target_and_cleans_stage(
    tmp_path,
    monkeypatch,
) -> None:
    target = tmp_path / ".llm-wiki-agent"
    real_move = guard.move_windows_path_write_through

    def collide(source, destination, *, replace_existing):
        if destination == target and not replace_existing:
            target.write_bytes(b"concurrent\n")
        return real_move(
            source,
            destination,
            replace_existing=replace_existing,
        )

    monkeypatch.setattr(guard, "move_windows_path_write_through", collide)

    with pytest.raises(OSError, match="appeared after preflight"):
        guard.atomic_write_private_bytes(
            target,
            b"managed\n",
            expected_existing=None,
        )

    assert target.read_bytes() == b"concurrent\n"
    assert not list(tmp_path.glob(".llm-wiki-*.private-tmp"))


def test_guarded_unlink_removes_only_requested_hardlink(tmp_path) -> None:
    target = tmp_path / "managed-hook"
    sibling = tmp_path / "managed-hook-copy"
    target.write_bytes(b"managed\n")
    try:
        sibling.hardlink_to(target)
    except OSError as exc:
        pytest.skip(f"hard links unavailable: {exc}")

    guard.unlink_guarded_bytes(target, expected=b"managed\n")

    assert not target.exists()
    assert sibling.read_bytes() == b"managed\n"


def test_guarded_unlink_restores_hardlink_after_content_mismatch(tmp_path) -> None:
    target = tmp_path / "managed-hook"
    sibling = tmp_path / "managed-hook-copy"
    target.write_bytes(b"custom\n")
    try:
        sibling.hardlink_to(target)
    except OSError as exc:
        pytest.skip(f"hard links unavailable: {exc}")

    with pytest.raises(OSError, match="changed after preflight"):
        guard.unlink_guarded_bytes(target, expected=b"managed\n")

    assert target.read_bytes() == b"custom\n"
    assert sibling.read_bytes() == b"custom\n"


def test_exact_manifest_tree_removal(tmp_path) -> None:
    root = tmp_path / "wiki"
    nested = root / "entities"
    nested.mkdir(parents=True)
    (root / "index.md").write_text("index\n", encoding="utf-8")
    (nested / "page.md").write_text("page\n", encoding="utf-8")
    metadata = root.stat()
    identity = guard.windows_object_identity(metadata, context=str(root))
    manifest = guard.guarded_tree_manifest(root)

    guard.remove_guarded_tree(
        root,
        expected_identity=(identity.device, identity.file_id),
        expected_manifest=manifest,
    )

    assert not root.exists()


def test_post_plan_tree_addition_is_preserved(tmp_path) -> None:
    root = tmp_path / "wiki"
    root.mkdir()
    (root / "index.md").write_text("index\n", encoding="utf-8")
    metadata = root.stat()
    identity = guard.windows_object_identity(metadata, context=str(root))
    manifest = guard.guarded_tree_manifest(root)
    added = root / "new-user-note.txt"
    added.write_text("new\n", encoding="utf-8")

    with pytest.raises(OSError):
        guard.remove_guarded_tree(
            root,
            expected_identity=(identity.device, identity.file_id),
            expected_manifest=manifest,
        )

    assert added.read_text(encoding="utf-8") == "new\n"


def test_tree_symlink_is_unlinked_without_traversing_target(tmp_path) -> None:
    root = tmp_path / "wiki"
    outside = tmp_path / "outside"
    root.mkdir()
    outside.mkdir()
    sentinel = outside / "sentinel.txt"
    sentinel.write_text("outside\n", encoding="utf-8")
    link = root / "linked"
    try:
        link.symlink_to(outside, target_is_directory=True)
    except OSError as exc:
        pytest.skip(f"directory symlink unavailable: {exc}")
    metadata = root.stat()
    identity = guard.windows_object_identity(metadata, context=str(root))
    manifest = guard.guarded_tree_manifest(root)

    guard.remove_guarded_tree(
        root,
        expected_identity=(identity.device, identity.file_id),
        expected_manifest=manifest,
    )

    assert sentinel.read_text(encoding="utf-8") == "outside\n"
