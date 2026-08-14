"""Portable contracts for the Windows guarded-namespace state machines.

The native Windows suite owns kernel handle, sharing, reparse-point, and ACL
integration.  These tests replace only those native boundaries so every core
lane can exercise the Python namespace algorithms and their fail-closed
cleanup behavior.
"""

from __future__ import annotations

import os
from collections.abc import Callable, Iterator, Sequence
from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, BinaryIO

import pytest

from llm_wiki_cli.services import filesystem_guard as guard


_EXPECTED_OMITTED = object()


class _WindowsOSProxy:
    """Expose the host ``os`` module with Windows dispatch selected locally."""

    name = "nt"

    def __getattr__(self, name: str) -> Any:
        return getattr(os, name)


@dataclass
class _PortableWindowsBoundaries:
    verified_private_paths: list[Path] = field(default_factory=list)


@contextmanager
def _portable_directory_guard(
    root: Path,
    relative_components: Sequence[str],
    *,
    create_missing: bool = False,
    require_restrictive_dacl: bool = False,
) -> Iterator[Path]:
    del require_restrictive_dacl
    current = Path(root).joinpath(*relative_components)
    if create_missing:
        current.mkdir(parents=True, exist_ok=True)
    yield current


@contextmanager
def _portable_readonly_file(
    path: Path,
    *,
    require_restrictive_dacl: bool = False,
    require_single_link: bool = True,
) -> Iterator[tuple[BinaryIO, os.stat_result]]:
    del require_restrictive_dacl, require_single_link
    with Path(path).open("rb") as stream:
        yield stream, os.fstat(stream.fileno())


def _portable_move(
    source: Path,
    destination: Path,
    *,
    replace_existing: bool,
) -> None:
    source = Path(source)
    destination = Path(destination)
    if not replace_existing and os.path.lexists(destination):
        raise FileExistsError(destination)
    if replace_existing:
        source.replace(destination)
    else:
        source.rename(destination)


def _portable_private_open(path: Path) -> int:
    return os.open(
        path,
        os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_BINARY", 0),
        0o600,
    )


@pytest.fixture
def portable_windows_boundaries(
    monkeypatch: pytest.MonkeyPatch,
) -> _PortableWindowsBoundaries:
    boundaries = _PortableWindowsBoundaries()
    monkeypatch.setattr(guard, "os", _WindowsOSProxy())
    monkeypatch.setattr(
        guard,
        "guard_windows_directory_chain",
        _portable_directory_guard,
    )
    monkeypatch.setattr(
        guard,
        "open_windows_readonly_file",
        _portable_readonly_file,
    )
    monkeypatch.setattr(guard, "move_windows_path_write_through", _portable_move)
    monkeypatch.setattr(
        guard,
        "replace_windows_file_write_through",
        lambda source, destination: _portable_move(
            source,
            destination,
            replace_existing=True,
        ),
    )
    monkeypatch.setattr(
        guard,
        "open_windows_private_write_file",
        _portable_private_open,
    )
    monkeypatch.setattr(
        guard,
        "verify_windows_restrictive_dacl",
        lambda path: boundaries.verified_private_paths.append(Path(path)),
    )
    monkeypatch.setattr(
        guard,
        "create_private_windows_directory",
        lambda path: Path(path).mkdir(mode=0o700),
    )
    return boundaries


def _write(
    kind: str,
    target: Path,
    data: bytes,
    *,
    expected_existing: bytes | None | object = _EXPECTED_OMITTED,
) -> Path:
    writer: Callable[..., Path]
    if kind == "public":
        writer = guard.atomic_write_guarded_bytes
    else:
        assert kind == "private"
        writer = guard.atomic_write_private_bytes
    if expected_existing is _EXPECTED_OMITTED:
        return writer(target, data)
    return writer(target, data, expected_existing=expected_existing)


def _stage_pattern(kind: str) -> str:
    return (
        ".llm-wiki-*.guarded-tmp"
        if kind == "public"
        else ".llm-wiki-*.private-tmp"
    )


def _assert_no_writer_stages(root: Path, kind: str) -> None:
    assert list(root.glob(_stage_pattern(kind))) == []
    assert list(root.glob(".llm-wiki-*.replaced")) == []


def _tree_identity(path: Path) -> tuple[int, int]:
    identity = guard.windows_object_identity(path.lstat(), context=str(path))
    return identity.device, identity.file_id


def test_windows_model_creates_guarded_directory(
    tmp_path: Path,
    portable_windows_boundaries: _PortableWindowsBoundaries,
) -> None:
    del portable_windows_boundaries
    target = tmp_path / "guarded" / "nested"

    assert guard.ensure_guarded_directory(target) == target
    assert target.is_dir()


@pytest.mark.parametrize("kind", ("public", "private"))
def test_windows_model_writer_supports_snapshot_and_unconditional_replacement(
    tmp_path: Path,
    portable_windows_boundaries: _PortableWindowsBoundaries,
    kind: str,
) -> None:
    target = tmp_path / f"{kind}.md"

    _write(kind, target, b"first\n", expected_existing=None)
    _write(kind, target, b"second\n", expected_existing=b"first\n")
    _write(kind, target, b"third\n")

    assert target.read_bytes() == b"third\n"
    _assert_no_writer_stages(tmp_path, kind)
    if kind == "private":
        assert portable_windows_boundaries.verified_private_paths == [
            target,
            target,
            target,
        ]
    else:
        assert portable_windows_boundaries.verified_private_paths == []


@pytest.mark.parametrize("kind", ("public", "private"))
def test_windows_model_writer_restores_exact_bytes_after_snapshot_mismatch(
    tmp_path: Path,
    portable_windows_boundaries: _PortableWindowsBoundaries,
    kind: str,
) -> None:
    del portable_windows_boundaries
    target = tmp_path / f"{kind}.md"
    target.write_bytes(b"custom\n")

    with pytest.raises(guard.WindowsFileGuardError, match="changed after preflight"):
        _write(
            kind,
            target,
            b"replacement\n",
            expected_existing=b"managed\n",
        )

    assert target.read_bytes() == b"custom\n"
    _assert_no_writer_stages(tmp_path, kind)


@pytest.mark.parametrize("kind", ("public", "private"))
def test_windows_model_absent_snapshot_collision_preserves_concurrent_bytes(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    portable_windows_boundaries: _PortableWindowsBoundaries,
    kind: str,
) -> None:
    del portable_windows_boundaries
    target = tmp_path / f"{kind}.md"
    concurrent = b"concurrent custom bytes\n"
    injected = False

    def collide(
        source: Path,
        destination: Path,
        *,
        replace_existing: bool,
    ) -> None:
        nonlocal injected
        if not injected and destination == target and not replace_existing:
            injected = True
            target.write_bytes(concurrent)
        _portable_move(
            source,
            destination,
            replace_existing=replace_existing,
        )

    monkeypatch.setattr(guard, "move_windows_path_write_through", collide)

    with pytest.raises(OSError, match="appeared after preflight"):
        _write(kind, target, b"managed\n", expected_existing=None)

    assert injected is True
    assert target.read_bytes() == concurrent
    _assert_no_writer_stages(tmp_path, kind)


@pytest.mark.parametrize(
    ("kind", "message"),
    (
        ("public", "regular file"),
        ("private", "single-link regular file"),
    ),
)
def test_windows_model_writer_rejects_hardlinked_target_without_mutation(
    tmp_path: Path,
    portable_windows_boundaries: _PortableWindowsBoundaries,
    kind: str,
    message: str,
) -> None:
    del portable_windows_boundaries
    target = tmp_path / f"{kind}.md"
    sibling = tmp_path / f"{kind}-sibling.md"
    original = b"shared custom bytes\n"
    target.write_bytes(original)
    sibling.hardlink_to(target)

    with pytest.raises(guard.WindowsFileGuardError, match=message):
        _write(kind, target, b"replacement\n")

    assert target.read_bytes() == original
    assert sibling.read_bytes() == original
    _assert_no_writer_stages(tmp_path, kind)


def test_windows_model_unlink_allows_hardlinks_and_removes_only_requested_name(
    tmp_path: Path,
    portable_windows_boundaries: _PortableWindowsBoundaries,
) -> None:
    del portable_windows_boundaries
    target = tmp_path / "managed-hook"
    sibling = tmp_path / "managed-hook-copy"
    target.write_bytes(b"managed\n")
    sibling.hardlink_to(target)

    guard.unlink_guarded_bytes(target, expected=b"managed\n")

    assert not target.exists()
    assert sibling.read_bytes() == b"managed\n"
    assert list(tmp_path.glob(".llm-wiki-*.unlink-check")) == []


def test_windows_model_unlink_mismatch_restores_exact_bytes(
    tmp_path: Path,
    portable_windows_boundaries: _PortableWindowsBoundaries,
) -> None:
    del portable_windows_boundaries
    target = tmp_path / "managed-hook"
    target.write_bytes(b"custom\n")

    with pytest.raises(guard.WindowsFileGuardError, match="changed after preflight"):
        guard.unlink_guarded_bytes(target, expected=b"managed\n")

    assert target.read_bytes() == b"custom\n"
    assert list(tmp_path.glob(".llm-wiki-*.unlink-check")) == []


def test_windows_model_unlink_restore_never_replaces_concurrent_target(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    portable_windows_boundaries: _PortableWindowsBoundaries,
) -> None:
    del portable_windows_boundaries
    target = tmp_path / "managed-hook"
    original = b"custom before removal\n"
    concurrent = b"new concurrent file\n"
    target.write_bytes(original)
    injected = False

    def occupy_restore_target(
        source: Path,
        destination: Path,
        *,
        replace_existing: bool,
    ) -> None:
        nonlocal injected
        if (
            not injected
            and source.name.endswith(".unlink-check")
            and destination == target
        ):
            injected = True
            target.write_bytes(concurrent)
        _portable_move(
            source,
            destination,
            replace_existing=replace_existing,
        )

    monkeypatch.setattr(
        guard,
        "move_windows_path_write_through",
        occupy_restore_target,
    )

    with pytest.raises(guard.WindowsFileGuardError, match="changed after preflight"):
        guard.unlink_guarded_bytes(target, expected=b"managed\n")

    assert injected is True
    assert target.read_bytes() == concurrent
    retained = list(tmp_path.glob(".llm-wiki-*.unlink-check"))
    assert len(retained) == 1
    assert retained[0].read_bytes() == original


def test_windows_model_tree_removal_matches_identity_and_manifest(
    tmp_path: Path,
    portable_windows_boundaries: _PortableWindowsBoundaries,
) -> None:
    del portable_windows_boundaries
    root = tmp_path / "wiki"
    (root / "entities").mkdir(parents=True)
    (root / "index.md").write_bytes(b"index\n")
    (root / "entities" / "page.md").write_bytes(b"page\n")
    identity = _tree_identity(root)
    manifest = guard.guarded_tree_manifest(root)

    guard.remove_guarded_tree(
        root,
        expected_identity=identity,
        expected_manifest=manifest,
    )

    assert not root.exists()
    assert list(tmp_path.glob(".llm-wiki-*.tree-check")) == []


def test_windows_model_tree_removal_supports_unbound_snapshot(
    tmp_path: Path,
    portable_windows_boundaries: _PortableWindowsBoundaries,
) -> None:
    del portable_windows_boundaries
    root = tmp_path / "wiki"
    (root / "entities").mkdir(parents=True)
    (root / "entities" / "page.md").write_bytes(b"page\n")

    guard.remove_guarded_tree(root)

    assert not root.exists()
    assert list(tmp_path.glob(".llm-wiki-*.tree-check")) == []


def test_windows_model_tree_manifest_drift_is_restored_without_data_loss(
    tmp_path: Path,
    portable_windows_boundaries: _PortableWindowsBoundaries,
) -> None:
    del portable_windows_boundaries
    root = tmp_path / "wiki"
    root.mkdir()
    original = root / "index.md"
    added = root / "new-user-note.txt"
    original.write_bytes(b"index\n")
    identity = _tree_identity(root)
    manifest = guard.guarded_tree_manifest(root)
    added.write_bytes(b"new user bytes\n")

    with pytest.raises(guard.WindowsDirectoryGuardError, match="contents changed"):
        guard.remove_guarded_tree(
            root,
            expected_identity=identity,
            expected_manifest=manifest,
        )

    assert original.read_bytes() == b"index\n"
    assert added.read_bytes() == b"new user bytes\n"
    assert list(tmp_path.glob(".llm-wiki-*.tree-check")) == []


def test_windows_model_tree_identity_drift_is_restored_without_data_loss(
    tmp_path: Path,
    portable_windows_boundaries: _PortableWindowsBoundaries,
) -> None:
    del portable_windows_boundaries
    root = tmp_path / "wiki"
    root.mkdir()
    page = root / "index.md"
    page.write_bytes(b"index\n")

    with pytest.raises(
        guard.WindowsDirectoryGuardError,
        match="changed after preflight",
    ):
        guard.remove_guarded_tree(root, expected_identity=(999, 999))

    assert page.read_bytes() == b"index\n"
    assert list(tmp_path.glob(".llm-wiki-*.tree-check")) == []
