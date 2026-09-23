"""Path/handle metadata semantics and Windows error classification controls."""

from contextlib import contextmanager
import hashlib
import io
import os
import stat
from types import SimpleNamespace

import pytest

from llm_wiki_cli.services import knowledge_storage_io as storage
from llm_wiki_cli.services import source_snapshot as sources
from llm_wiki_cli.services.filesystem_guard import (
    WindowsDirectoryGuardError, WindowsFileGuardError, fresh_no_follow_stat,
)
from llm_wiki_cli.services.knowledge_storage import KnowledgeStorageError


def metadata(**changes):
    values = dict(st_dev=7, st_ino=11, st_mode=stat.S_IFREG | 0o644, st_nlink=1,
                  st_size=6, st_mtime=0.0, st_mtime_ns=23, st_ctime_ns=100,
                  st_file_attributes=0)
    values.update(changes)
    return SimpleNamespace(**values)


def windows_storage(monkeypatch, *, named_before=None, named_after=None,
                    handle_before=None, handle_after=None):
    named_before = named_before or metadata()
    named_after = named_after or named_before
    handle_before = handle_before or metadata(st_ctime_ns=900, st_mode=stat.S_IFREG | 0o666)
    handle_after = handle_after or handle_before
    stats = iter((named_before, named_after))

    def named(_path):
        return next(stats)

    class Target:
        def __init__(self, path):
            self.path = path

        def __getattr__(self, name):
            return getattr(self.path, name)

        def __str__(self):
            return str(self.path)

        def lstat(self):
            return named(self.path)

    class WindowsOs:
        name = "nt"

        def __getattr__(self, name):
            return getattr(os, name)

        def fstat(self, descriptor):
            return handle_after

    class Stream(io.BytesIO):
        def fileno(self):
            return 17

    @contextmanager
    def directories(*args, **kwargs):
        yield

    @contextmanager
    def opened(*args, **kwargs):
        with Stream(b"abcdef") as stream:
            yield stream, handle_before

    monkeypatch.setattr(storage, "os", WindowsOs())
    monkeypatch.setattr(storage, "_absolute_path", Target)
    monkeypatch.setattr(storage, "guard_windows_directory_chain", directories)
    monkeypatch.setattr(storage, "open_windows_readonly_file", opened)
    monkeypatch.setattr(storage, "fresh_no_follow_stat", named, raising=False)


@pytest.mark.parametrize("ranged", [False, True])
def test_windows_read_compares_ctime_within_its_observation_channel(tmp_path, monkeypatch, ranged):
    windows_storage(monkeypatch)
    options = {"offset": 1, "length": 3, "file_bytes": 6} if ranged else {}
    result = storage.read_guarded(tmp_path / "pack.zip", 6, **options)
    assert result.content == (b"bcd" if ranged else b"abcdef")
    assert result.identity == (7, 11, stat.S_IFREG | 0o644, 6, 23, 100)


@pytest.mark.parametrize("channel", ["path", "handle"])
@pytest.mark.parametrize("changes", [
    {"st_dev": 8}, {"st_ino": 12}, {"st_size": 7}, {"st_mtime_ns": 24},
    {"st_ctime_ns": 1001}, {"st_mode": stat.S_IFREG | 0o444},
    {"st_nlink": 2}, {"st_file_attributes": 0x400},
], ids=["device", "inode", "size", "mtime", "ctime", "mode", "hardlink", "reparse"])
def test_windows_read_rejects_real_changes(tmp_path, monkeypatch, channel, changes):
    options = {"named_after": metadata(**changes)} if channel == "path" else {
        "handle_after": metadata(**{"st_ctime_ns": 900, "st_mode": stat.S_IFREG | 0o666, **changes})}
    windows_storage(monkeypatch, **options)
    with pytest.raises(KnowledgeStorageError):
        storage.read_guarded(tmp_path / "pack.zip", 6)


@pytest.mark.parametrize("changes", [{"st_dev": 0}, {"st_ino": 0}, {"st_ino": 12}, {"st_size": 8}])
def test_windows_read_rejects_unbound_handle(tmp_path, monkeypatch, changes):
    windows_storage(monkeypatch, handle_before=metadata(**changes))
    with pytest.raises(KnowledgeStorageError):
        storage.read_guarded(tmp_path / "pack.zip", 6)


@pytest.mark.parametrize("guard", [WindowsDirectoryGuardError, WindowsFileGuardError])
@pytest.mark.parametrize("cause,code", [(FileNotFoundError, "storage-missing"),
                                       (PermissionError, "storage-invalid"), (OSError, "storage-invalid")])
def test_windows_guard_preserves_missing_without_hiding_denied_access(tmp_path, monkeypatch, guard, cause, code):
    windows_storage(monkeypatch)

    @contextmanager
    def failed(*args, **kwargs):
        try:
            raise cause("native error")
        except OSError as exc:
            raise guard("guard failed") from exc
        yield  # pragma: no cover

    name = "guard_windows_directory_chain" if guard is WindowsDirectoryGuardError else "open_windows_readonly_file"
    monkeypatch.setattr(storage, name, failed)
    with pytest.raises(KnowledgeStorageError) as error:
        storage.read_guarded(tmp_path / "missing.json", 6)
    assert error.value.code == code


def shifted_handle_stat(descriptor):
    value = os.fstat(descriptor)
    return SimpleNamespace(**{name: getattr(value, name) for name in (
        "st_dev", "st_ino", "st_mode", "st_nlink", "st_size", "st_mtime", "st_mtime_ns")},
        st_ctime_ns=value.st_ctime_ns + 1_000_000_000)


class WindowsSourceOs:
    name = "nt"

    def __getattr__(self, name):
        return getattr(os, name)

    def fstat(self, descriptor):
        return shifted_handle_stat(descriptor)


def test_coherent_source_capture_binds_path_timestamps_and_control_files(tmp_path, monkeypatch):
    source = tmp_path / "app.py"
    source.write_bytes(b"value = 3\n")
    control = tmp_path / ".gitignore"
    control.write_bytes(b"ignored/\n")
    monkeypatch.setattr(sources, "os", WindowsSourceOs())
    snapshot = sources.build_source_snapshot(tmp_path, coherent=True)
    assert snapshot.captured_content_hashes["app.py"] == "sha256:" + hashlib.sha256(source.read_bytes()).hexdigest()
    for path in (source, control):
        assert snapshot.captured_file_integrity[path.name].ctime_ns == path.stat().st_ctime_ns
    assert sources.source_snapshot_inputs_match_current_files(snapshot)
    assert sources.source_snapshot_matches_current_files(snapshot)


@pytest.mark.parametrize("changes", [{"st_ino": 123456789}, {"st_mtime_ns": 0}, {"st_ctime_ns": 0}])
def test_coherent_source_capture_rejects_path_changes(tmp_path, monkeypatch, changes):
    source = tmp_path / "app.py"
    source.write_bytes(b"value = 3\n")
    original = fresh_no_follow_stat
    calls = 0

    def named(path):
        nonlocal calls
        calls += 1
        value = original(path)
        if calls == 1:
            return value
        data = {name: getattr(value, name) for name in (
            "st_dev", "st_ino", "st_mode", "st_nlink", "st_size", "st_mtime", "st_mtime_ns", "st_ctime_ns")}
        data.update(changes)
        return SimpleNamespace(**data)

    monkeypatch.setattr(sources, "os", WindowsSourceOs())
    monkeypatch.setattr(sources, "fresh_no_follow_stat", named, raising=False)
    with pytest.raises(sources.SourceSnapshotMutationError):
        sources._sha256_file(source, integrity_out={})
