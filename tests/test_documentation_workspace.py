"""Filesystem policy tests for external documentation workspaces."""

from __future__ import annotations

import io
import os
import stat
import subprocess
from contextlib import contextmanager
from pathlib import Path
from types import SimpleNamespace
from typing import cast

import pytest

from llm_wiki_cli.services import documentation_policy as documentation_policy_module
from llm_wiki_cli.services import filesystem_guard as filesystem_guard_module
from llm_wiki_cli.services.documentation_policy import (
    DocumentationPolicyError,
    capture_tree_baseline,
    compare_tree_baseline,
    resolve_documentation_policy,
    source_tree_baseline,
)
from llm_wiki_cli.services.filesystem_guard import (
    _WindowsDirectoryGuardUnavailableError,
    WindowsIdentityUnavailableError,
    _WindowsPathHandleMetadata,
    guard_windows_directory_chain,
    windows_object_identity_from_values,
    _windows_path_handle_metadata,
)


def _windows_regular_stat(
    *,
    size: int = 7,
    mtime_ns: int = 2_000,
    ctime_ns: int = 3_000,
    device: int = 11,
    file_id: int = 17,
) -> os.stat_result:
    return cast(
        os.stat_result,
        SimpleNamespace(
            st_mode=stat.S_IFREG | 0o600,
            st_size=size,
            st_mtime_ns=mtime_ns,
            st_mtime=mtime_ns / 1_000_000_000,
            st_ctime_ns=ctime_ns,
            st_ctime=ctime_ns / 1_000_000_000,
            st_dev=device,
            st_ino=file_id,
            st_file_attributes=0,
        ),
    )


class _GuardedBytes(io.BytesIO):
    def fileno(self) -> int:
        return 101


def _write_source(root: Path) -> None:
    root.mkdir(parents=True)
    (root / "module.py").write_text("def value():\n    return 1\n", encoding="utf-8")
    (root / "AGENTS.md").write_text("untrusted instructions\n", encoding="utf-8")
    plugin = root / ".llm-wiki" / "plugins" / "hostile"
    plugin.mkdir(parents=True)
    (plugin / "llm-wiki-plugin.json").write_text("{}\n", encoding="utf-8")
    (plugin / "plugin.py").write_text(
        "raise RuntimeError('must never execute')\n", encoding="utf-8"
    )


def test_policy_supports_no_git_source_and_unicode_paths(tmp_path):
    source = tmp_path / "source with spaces Ω"
    workspace = tmp_path / "documentation output Ω"
    _write_source(source)

    policy = resolve_documentation_policy(workspace, source_root=source)
    baseline = source_tree_baseline(source)

    assert policy.source_root == source.resolve()
    assert baseline.file_count == 4
    assert baseline.tree_hash.startswith("sha256:")
    assert ".git" in baseline.excluded_directories
    assert compare_tree_baseline(baseline, source).ok


@pytest.mark.parametrize("workspace_rel", [".", "docs", "nested/workspace"])
def test_policy_rejects_workspace_inside_source(tmp_path, workspace_rel):
    source = tmp_path / "source"
    _write_source(source)
    workspace = source / workspace_rel

    with pytest.raises(DocumentationPolicyError, match="must not overlap"):
        resolve_documentation_policy(workspace, source_root=source)


def test_policy_rejects_source_inside_workspace(tmp_path):
    workspace = tmp_path / "workspace"
    source = workspace / "source"
    _write_source(source)

    with pytest.raises(DocumentationPolicyError, match="must not overlap"):
        resolve_documentation_policy(workspace, source_root=source)


def test_policy_forbidden_roots_override_write_allowlist(tmp_path):
    source = tmp_path / "source"
    workspace = tmp_path / "workspace"
    cache = tmp_path / "cache"
    _write_source(source)
    policy = resolve_documentation_policy(
        workspace,
        source_root=source,
        helper_cache_root=cache,
    )

    assert policy.assert_write_allowed(workspace / "wiki" / "index.md")
    assert policy.assert_write_allowed(cache / "helper")
    with pytest.raises(DocumentationPolicyError, match="read-only evidence root"):
        policy.assert_write_allowed(source / "module.py")
    with pytest.raises(DocumentationPolicyError, match="outside"):
        policy.assert_write_allowed(tmp_path / "other" / "file.txt")


def test_tree_comparison_reports_added_removed_and_changed(tmp_path):
    source = tmp_path / "source"
    _write_source(source)
    (source / "removed.txt").write_text("remove\n", encoding="utf-8")
    baseline = source_tree_baseline(source)

    (source / "module.py").write_text("changed\n", encoding="utf-8")
    (source / "removed.txt").unlink()
    (source / "added.txt").write_text("added\n", encoding="utf-8")
    difference = compare_tree_baseline(baseline, source)

    assert difference.ok is False
    assert difference.added == ("added.txt",)
    assert difference.removed == ("removed.txt",)
    assert difference.changed == ("module.py",)


def test_tree_baseline_rejects_oversized_single_file(tmp_path):
    source = tmp_path / "source"
    source.mkdir()
    (source / "large.bin").write_bytes(b"12345")

    with pytest.raises(DocumentationPolicyError, match="per-file byte limit"):
        capture_tree_baseline(
            source,
            display="source",
            max_file_bytes=4,
            max_total_bytes=100,
        )


def test_tree_baseline_rejects_oversized_aggregate(tmp_path):
    source = tmp_path / "source"
    source.mkdir()
    (source / "one.bin").write_bytes(b"123")
    (source / "two.bin").write_bytes(b"456")

    with pytest.raises(DocumentationPolicyError, match="aggregate byte limit"):
        capture_tree_baseline(
            source,
            display="source",
            max_file_bytes=4,
            max_total_bytes=5,
        )


@pytest.mark.skipif(not hasattr(os, "symlink"), reason="symlinks unavailable")
def test_tree_baseline_rejects_symlinked_source_content(tmp_path):
    source = tmp_path / "source"
    outside = tmp_path / "outside.txt"
    _write_source(source)
    outside.write_text("outside\n", encoding="utf-8")
    try:
        (source / "escape.txt").symlink_to(outside)
    except OSError:
        pytest.skip("symlink creation is unavailable for this account")

    with pytest.raises(DocumentationPolicyError, match="Symlinked content"):
        source_tree_baseline(source)


@pytest.mark.skipif(not hasattr(os, "symlink"), reason="symlinks unavailable")
def test_tree_baseline_rejects_symlinked_source_root(tmp_path):
    real_source = tmp_path / "real-source"
    source_link = tmp_path / "source-link"
    _write_source(real_source)
    try:
        source_link.symlink_to(real_source, target_is_directory=True)
    except OSError:
        pytest.skip("directory symlink creation is unavailable for this account")

    with pytest.raises(DocumentationPolicyError, match="Symlinked source"):
        source_tree_baseline(source_link)


def test_tree_baseline_rejects_file_replaced_between_inspection_and_open(
    tmp_path, monkeypatch
):
    source = tmp_path / "source"
    _write_source(source)
    target = source / "module.py"
    replacement = source / "replacement.tmp"
    replacement.write_text("replacement\n", encoding="utf-8")
    swapped = False

    def swap_target() -> None:
        nonlocal swapped
        if not swapped:
            swapped = True
            target.replace(source / "module.original")
            replacement.replace(target)

    if os.name == "nt":
        real_guarded_open = documentation_policy_module.open_windows_readonly_file

        @contextmanager
        def swap_before_guarded_open(path):
            if Path(path) == target:
                with replacement.open("rb") as handle:
                    yield handle, os.fstat(handle.fileno())
                return
            with real_guarded_open(path) as opened:
                yield opened

        monkeypatch.setattr(
            documentation_policy_module,
            "open_windows_readonly_file",
            swap_before_guarded_open,
        )
    else:
        real_open = os.open

        def swap_before_open(path, flags, mode=0o777, *, dir_fd=None):
            if Path(path) == target:
                swap_target()
            if dir_fd is None:
                return real_open(path, flags, mode)
            return real_open(path, flags, mode, dir_fd=dir_fd)

        monkeypatch.setattr(os, "open", swap_before_open)

    with pytest.raises(DocumentationPolicyError, match="changed identity"):
        source_tree_baseline(source)


def test_tree_baseline_uses_fresh_identity_for_nested_entries(
    tmp_path,
    monkeypatch,
) -> None:
    source = tmp_path / "source"
    _write_source(source)
    cached_stat_calls: list[Path] = []
    guarded_directories: list[tuple[Path, tuple[str, ...]]] = []
    real_scandir = os.scandir

    class _ZeroIdentityEntry:
        def __init__(self, entry):
            self._entry = entry
            self.name = entry.name
            self.path = entry.path

        def stat(self, *, follow_symlinks=True):
            cached_stat_calls.append(Path(self.path))
            values = list(self._entry.stat(follow_symlinks=follow_symlinks))
            values[1] = 0
            values[2] = 0
            values[3] = 0
            return os.stat_result(values)

    class _ZeroIdentityScandir:
        def __init__(self, path):
            self._iterator = real_scandir(path)

        def __enter__(self):
            return self

        def __exit__(self, _exc_type, _exc, _traceback):
            self._iterator.close()

        def __iter__(self):
            return (_ZeroIdentityEntry(entry) for entry in self._iterator)

    class _WindowsOsProxy:
        name = "nt"

        def __getattr__(self, name):
            return getattr(os, name)

        def scandir(self, path):
            return _ZeroIdentityScandir(path)

    @contextmanager
    def fake_directory_guard(root, components):
        guarded_directories.append((root, tuple(components)))
        yield root.joinpath(*components)

    @contextmanager
    def fake_file_guard(path):
        with path.open("rb") as handle:
            yield handle, os.fstat(handle.fileno())

    monkeypatch.setattr(
        documentation_policy_module,
        "os",
        _WindowsOsProxy(),
    )
    monkeypatch.setattr(
        documentation_policy_module,
        "guard_windows_directory_chain",
        fake_directory_guard,
    )
    monkeypatch.setattr(
        documentation_policy_module,
        "open_windows_readonly_file",
        fake_file_guard,
    )

    baseline = source_tree_baseline(source)

    assert baseline.file_count == 4
    assert cached_stat_calls == []
    assert (
        source.resolve(),
        (".llm-wiki", "plugins", "hostile"),
    ) in guarded_directories


@pytest.mark.parametrize(
    ("device", "file_id"),
    ((0, 17), (23, 0)),
)
def test_windows_identity_fails_closed_when_a_component_is_zero(
    device,
    file_id,
) -> None:
    with pytest.raises(
        WindowsIdentityUnavailableError,
        match="identity is unavailable",
    ):
        windows_object_identity_from_values(
            device=device,
            file_id=file_id,
            context="test handle",
        )


def test_windows_path_handle_metadata_excludes_ctime() -> None:
    metadata = _windows_path_handle_metadata(
        _windows_regular_stat(size=23, mtime_ns=41, ctime_ns=59)
    )

    assert metadata == _WindowsPathHandleMetadata(size=23, mtime_ns=41)


def _configure_windows_policy_hash(
    monkeypatch,
    *,
    path_stats: list[os.stat_result],
    opened_before: os.stat_result,
    opened_after: os.stat_result,
    payload: bytes = b"content",
) -> None:
    observations = iter(path_stats)

    class _WindowsOsProxy:
        name = "nt"

        def __getattr__(self, name):
            return getattr(os, name)

        def fstat(self, _descriptor):
            return opened_after

    @contextmanager
    def fake_file_guard(_path):
        yield _GuardedBytes(payload), opened_before

    monkeypatch.setattr(documentation_policy_module, "os", _WindowsOsProxy())
    monkeypatch.setattr(
        documentation_policy_module,
        "fresh_no_follow_stat",
        lambda _path: next(observations),
    )
    monkeypatch.setattr(
        documentation_policy_module,
        "open_windows_readonly_file",
        fake_file_guard,
    )


def test_windows_hash_accepts_path_handle_ctime_difference(
    tmp_path,
    monkeypatch,
) -> None:
    path = tmp_path / "source.txt"
    opened = _windows_regular_stat(ctime_ns=200)
    _configure_windows_policy_hash(
        monkeypatch,
        path_stats=[
            _windows_regular_stat(ctime_ns=100),
            _windows_regular_stat(ctime_ns=300),
        ],
        opened_before=opened,
        opened_after=opened,
    )

    digest = documentation_policy_module._hash_windows_file(
        path,
        inspected=None,
        max_bytes=None,
    )

    assert (
        digest
        == "sha256:"
        + documentation_policy_module.hashlib.sha256(b"content").hexdigest()
    )


@pytest.mark.parametrize(
    ("size", "mtime_ns"),
    ((8, 2_000), (7, 2_001)),
)
def test_windows_hash_rejects_path_handle_size_or_mtime_difference(
    tmp_path,
    monkeypatch,
    size,
    mtime_ns,
) -> None:
    path = tmp_path / "source.txt"
    opened = _windows_regular_stat(size=size, mtime_ns=mtime_ns)
    _configure_windows_policy_hash(
        monkeypatch,
        path_stats=[_windows_regular_stat()],
        opened_before=opened,
        opened_after=opened,
    )

    with pytest.raises(DocumentationPolicyError, match="changed while"):
        documentation_policy_module._hash_windows_file(
            path,
            inspected=None,
            max_bytes=None,
        )


def test_windows_hash_rejects_same_handle_ctime_change(
    tmp_path,
    monkeypatch,
) -> None:
    path = tmp_path / "source.txt"
    _configure_windows_policy_hash(
        monkeypatch,
        path_stats=[_windows_regular_stat(ctime_ns=100)],
        opened_before=_windows_regular_stat(ctime_ns=200),
        opened_after=_windows_regular_stat(ctime_ns=201),
    )

    with pytest.raises(DocumentationPolicyError, match="changed while"):
        documentation_policy_module._hash_windows_file(
            path,
            inspected=None,
            max_bytes=None,
        )


@pytest.mark.parametrize("require_restrictive_dacl", [False, True])
def test_windows_directory_guard_requests_rename_barrier_access(
    tmp_path,
    monkeypatch,
    require_restrictive_dacl,
) -> None:
    from ctypes import wintypes

    create_calls: list[tuple[object, ...]] = []
    invalid_handle = wintypes.HANDLE(-1).value

    class _FakeFunction:
        argtypes = None
        restype = None

        def __init__(self, callback):
            self._callback = callback

        def __call__(self, *args):
            return self._callback(*args)

    def fake_create_file(*args):
        create_calls.append(args)
        return invalid_handle

    kernel32 = SimpleNamespace(
        CreateFileW=_FakeFunction(fake_create_file),
        GetFileInformationByHandle=_FakeFunction(lambda *_args: 0),
    )
    monkeypatch.setattr(
        filesystem_guard_module.ctypes,
        "WinDLL",
        lambda *_args, **_kwargs: kernel32,
        raising=False,
    )
    monkeypatch.setattr(
        filesystem_guard_module.ctypes,
        "get_last_error",
        lambda: filesystem_guard_module._ERROR_ACCESS_DENIED,
        raising=False,
    )
    monkeypatch.setattr(
        filesystem_guard_module.ctypes,
        "WinError",
        lambda code: PermissionError(code, "Access is denied"),
        raising=False,
    )

    with pytest.raises(
        _WindowsDirectoryGuardUnavailableError,
        match="list-directory access",
    ):
        filesystem_guard_module._open_windows_directory_guard(
            tmp_path,
            require_restrictive_dacl=require_restrictive_dacl,
        )

    assert len(create_calls) == 1
    desired_access = cast(int, create_calls[0][1])
    expected_access = (
        filesystem_guard_module._FILE_LIST_DIRECTORY
        | filesystem_guard_module._FILE_READ_ATTRIBUTES
    )
    if require_restrictive_dacl:
        expected_access |= filesystem_guard_module._READ_CONTROL
    assert desired_access == expected_access
    assert not desired_access & filesystem_guard_module._DELETE
    assert not desired_access & filesystem_guard_module._GENERIC_WRITE
    sharing = cast(int, create_calls[0][2])
    assert sharing == (
        filesystem_guard_module._FILE_SHARE_READ
        | filesystem_guard_module._FILE_SHARE_WRITE
    )
    assert not sharing & filesystem_guard_module._FILE_SHARE_DELETE


@pytest.mark.skipif(os.name != "nt", reason="Windows rename sharing semantics only")
@pytest.mark.parametrize("guarded_target", ["root", "child"])
def test_windows_directory_guard_blocks_rename_until_release(
    tmp_path,
    guarded_target,
) -> None:
    root = tmp_path / "root"
    child = root / "child"
    child.mkdir(parents=True)
    target = root if guarded_target == "root" else child
    renamed = (
        tmp_path / "renamed-root"
        if guarded_target == "root"
        else root / "renamed-child"
    )

    with guard_windows_directory_chain(root, ("child",)):
        with pytest.raises(OSError):
            target.rename(renamed)
        assert target.is_dir()

    target.rename(renamed)
    assert renamed.is_dir()


def test_relative_windows_hash_path_is_made_absolute_before_guarding(
    tmp_path,
    monkeypatch,
) -> None:
    source = tmp_path / "relative.txt"
    source.write_bytes(b"content")
    guarded_parents: list[Path] = []
    hashed_paths: list[Path] = []

    class _WindowsOsProxy:
        name = "nt"

        def __getattr__(self, name):
            return getattr(os, name)

    @contextmanager
    def fake_directory_guard(root, components):
        guarded_parents.append(root)
        assert components == ()
        yield root

    def fake_hash(path, *, inspected, max_bytes):
        hashed_paths.append(path)
        assert inspected is None
        assert max_bytes is None
        return "sha256:" + ("0" * 64)

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(documentation_policy_module, "os", _WindowsOsProxy())
    monkeypatch.setattr(
        documentation_policy_module,
        "guard_windows_directory_chain",
        fake_directory_guard,
    )
    monkeypatch.setattr(
        documentation_policy_module,
        "_hash_windows_file",
        fake_hash,
    )

    result = documentation_policy_module.hash_file("relative.txt")

    assert result == "sha256:" + ("0" * 64)
    assert hashed_paths == [source]
    assert guarded_parents == [tmp_path]


@pytest.mark.skipif(os.name != "nt", reason="Windows junction semantics only")
def test_tree_baseline_rejects_windows_junction(tmp_path):
    source = tmp_path / "source"
    junction_target = tmp_path / "junction-target"
    _write_source(source)
    junction_target.mkdir()
    (junction_target / "outside.txt").write_text("outside\n", encoding="utf-8")
    junction = source / "junction"
    completed = subprocess.run(
        [
            "cmd.exe",
            "/d",
            "/c",
            "mklink",
            "/J",
            str(junction),
            str(junction_target),
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode:
        pytest.skip(f"junction creation is unavailable: {completed.stderr.strip()}")

    with pytest.raises(DocumentationPolicyError, match="reparse-point"):
        source_tree_baseline(source)


def test_live_service_requires_explicit_safe_observation_policy(tmp_path):
    workspace = tmp_path / "workspace"
    capture = tmp_path / "capture"

    with pytest.raises(DocumentationPolicyError, match="must not contain"):
        resolve_documentation_policy(
            workspace,
            live_service_url="https://user:secret@example.test/?token=secret",
        )
    with pytest.raises(DocumentationPolicyError, match="capture root"):
        resolve_documentation_policy(
            workspace,
            live_service_url="https://example.test/demo",
            live_service_access_mode="anonymous",
            live_service_observation_allowed=True,
        )

    policy = resolve_documentation_policy(
        workspace,
        capture_root=capture,
        live_service_url="https://example.test/demo",
        live_service_access_mode="anonymous",
        live_service_observation_allowed=True,
    )
    portable = policy.to_portable_dict()
    assert portable["live_service"]["observation_allowed"] is True
    assert portable["live_service"]["secret_material_persisted"] is False
    assert "https://" not in str(portable)
