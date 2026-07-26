"""Focused checks for the controller-owned protected artifact store."""

from __future__ import annotations

import errno
import os
import stat
import subprocess
from contextlib import contextmanager
from pathlib import Path
from types import SimpleNamespace
from typing import cast

import pytest

import llm_wiki_cli.services.protected_artifacts as protected_artifacts
from llm_wiki_cli.services.protected_artifacts import (
    ProtectedArtifactDurabilityError,
    ProtectedArtifactIntegrityError,
    ProtectedArtifactLimitError,
    ProtectedArtifactLockError,
    ProtectedArtifactStore,
    canonical_json_bytes,
    validate_portable_relative_path,
)


def test_create_requires_new_or_empty_regular_root(tmp_path: Path):
    new_root = tmp_path / "new"
    store = ProtectedArtifactStore(new_root, create=True)
    assert store.root == new_root.resolve()

    empty_root = tmp_path / "empty"
    ProtectedArtifactStore(empty_root, create=True)
    assert ProtectedArtifactStore(empty_root, create=True).root == empty_root

    nonempty = tmp_path / "nonempty"
    nonempty_store = ProtectedArtifactStore(nonempty, create=True)
    nonempty_store._write_bytes("unknown", b"keep", immutable=True)
    with pytest.raises(ProtectedArtifactIntegrityError, match="must be empty"):
        ProtectedArtifactStore(nonempty, create=True)
    assert (nonempty / "unknown").read_text(encoding="utf-8") == "keep"


def test_create_rejects_redirected_root_without_writing_outside(tmp_path: Path):
    outside = tmp_path / "outside"
    outside.mkdir()
    root = tmp_path / "redirect"
    try:
        root.symlink_to(outside, target_is_directory=True)
    except OSError as exc:
        pytest.skip(f"directory symlinks are unavailable: {exc}")

    with pytest.raises(ProtectedArtifactIntegrityError, match="link|reparse"):
        ProtectedArtifactStore(root, create=True)
    assert not list(outside.iterdir())


@pytest.mark.skipif(os.name == "nt", reason="POSIX ownership and modes")
def test_posix_store_enforces_owner_only_modes_on_every_open(tmp_path: Path):
    store = ProtectedArtifactStore(tmp_path / "root", create=True)
    target = store.write_snapshot_json("nested/run.json", {"generation": 1})
    with store.lock():
        pass

    assert stat.S_IMODE(store.root.stat().st_mode) == 0o700
    assert stat.S_IMODE((store.root / "nested").stat().st_mode) == 0o700
    assert stat.S_IMODE(target.stat().st_mode) == 0o600
    assert stat.S_IMODE((store.root / "controller.lock").stat().st_mode) == 0o600

    target.chmod(0o640)
    with pytest.raises(ProtectedArtifactIntegrityError, match="owner-only mode 0600"):
        store.read_json("nested/run.json")

    target.chmod(0o600)
    (store.root / "nested").chmod(0o750)
    with pytest.raises(ProtectedArtifactIntegrityError, match="owner-only mode 0700"):
        store.read_json("nested/run.json")


@pytest.mark.skipif(os.name == "nt", reason="POSIX ownership and modes")
def test_existing_posix_root_must_already_be_private(tmp_path: Path):
    root = tmp_path / "root"
    root.mkdir(mode=0o750)
    root.chmod(0o750)

    with pytest.raises(ProtectedArtifactIntegrityError, match="owner-only mode 0700"):
        ProtectedArtifactStore(root, create=True)


@pytest.mark.skipif(os.name == "nt", reason="POSIX ownership and modes")
def test_posix_owner_mismatch_is_rejected():
    getter = getattr(os, "geteuid")
    payload = cast(
        os.stat_result,
        SimpleNamespace(
            st_mode=stat.S_IFREG | 0o600,
            st_uid=getter() + 1,
            st_nlink=1,
            st_reparse_tag=0,
            st_file_attributes=0,
        ),
    )

    with pytest.raises(ProtectedArtifactIntegrityError, match="owned by uid"):
        protected_artifacts._assert_regular_file_stat(payload, context="emulated")


def test_access_protection_evidence_is_host_derived(tmp_path: Path):
    store = ProtectedArtifactStore(tmp_path / "root", create=True)
    evidence = store.verify_access_protection()

    if os.name == "nt":
        assert evidence["mechanism"] == "windows-protected-dacl"
        assert evidence["principal"].startswith("sid:S-")
    elif protected_artifacts.sys.platform == "darwin":
        getter = getattr(os, "geteuid")
        assert evidence == {
            "mechanism": "darwin-owner-only-no-extended-acl",
            "principal": f"uid:{getter()}",
            "directory_mode": "0700",
            "file_mode": "0600",
            "extended_acl": "absent",
        }
    else:
        getter = getattr(os, "geteuid")
        assert evidence == {
            "mechanism": "posix-owner-only",
            "principal": f"uid:{getter()}",
            "directory_mode": "0700",
            "file_mode": "0600",
        }


@pytest.mark.skipif(os.name == "nt", reason="Darwin descriptor ACL emulation")
def test_emulated_darwin_absent_extended_acl_is_admissible(
    tmp_path: Path,
    monkeypatch,
):
    monkeypatch.setattr(protected_artifacts.sys, "platform", "darwin")
    monkeypatch.setattr(
        protected_artifacts,
        "_darwin_extended_acl_entry_count",
        lambda _descriptor: 0,
    )

    store = ProtectedArtifactStore(tmp_path / "root", create=True)

    assert store.verify_access_protection()["extended_acl"] == "absent"


@pytest.mark.skipif(os.name == "nt", reason="Darwin descriptor ACL emulation")
def test_emulated_darwin_present_extended_acl_is_rejected(
    tmp_path: Path,
    monkeypatch,
):
    monkeypatch.setattr(protected_artifacts.sys, "platform", "darwin")
    monkeypatch.setattr(
        protected_artifacts,
        "_darwin_extended_acl_entry_count",
        lambda _descriptor: 1,
    )

    with pytest.raises(ProtectedArtifactIntegrityError, match="extended ACL"):
        ProtectedArtifactStore(tmp_path / "root", create=True)


@pytest.mark.skipif(os.name == "nt", reason="Darwin descriptor ACL emulation")
def test_emulated_darwin_unavailable_acl_inspection_fails_closed(
    tmp_path: Path,
    monkeypatch,
):
    def unavailable(_descriptor: int) -> int:
        raise ProtectedArtifactIntegrityError(
            "Cannot load the macOS extended-ACL inspection functions."
        )

    monkeypatch.setattr(protected_artifacts.sys, "platform", "darwin")
    monkeypatch.setattr(
        protected_artifacts,
        "_darwin_extended_acl_entry_count",
        unavailable,
    )

    with pytest.raises(ProtectedArtifactIntegrityError, match="Cannot load"):
        ProtectedArtifactStore(tmp_path / "root", create=True)


@pytest.mark.skipif(os.name == "nt", reason="Darwin descriptor ACL emulation")
def test_emulated_darwin_replacement_during_acl_inspection_fails_closed(
    tmp_path: Path,
    monkeypatch,
):
    target = tmp_path / "protected"
    replacement = tmp_path / "replacement"
    target.write_bytes(b"original")
    replacement.write_bytes(b"replacement")
    target.chmod(0o600)
    replacement.chmod(0o600)
    expected = target.lstat()

    def replace_after_open(_descriptor: int) -> int:
        os.replace(replacement, target)
        return 0

    monkeypatch.setattr(protected_artifacts.sys, "platform", "darwin")
    monkeypatch.setattr(
        protected_artifacts,
        "_darwin_extended_acl_entry_count",
        replace_after_open,
    )

    with pytest.raises(
        ProtectedArtifactIntegrityError,
        match="changed while its macOS extended ACL was inspected",
    ):
        protected_artifacts._assert_darwin_no_extended_acl_path(
            target,
            context="emulated protected file",
            expected=expected,
        )


@pytest.mark.skipif(
    protected_artifacts.sys.platform != "darwin",
    reason="native Darwin extended ACL inspection",
)
def test_darwin_native_new_private_file_has_no_extended_acl(tmp_path: Path):
    target = tmp_path / "private"
    descriptor = os.open(target, os.O_CREAT | os.O_EXCL | os.O_RDWR, 0o600)
    try:
        assert protected_artifacts._darwin_extended_acl_entry_count(descriptor) == 0
    finally:
        os.close(descriptor)


@pytest.mark.skipif(
    protected_artifacts.sys.platform != "darwin",
    reason="native Darwin extended ACL inspection",
)
def test_darwin_native_non_empty_extended_acl_is_rejected(tmp_path: Path):
    target = tmp_path / "acl-bearing"
    target.write_bytes(b"protected")
    target.chmod(0o600)
    subprocess.run(
        [
            "/bin/chmod",
            "+a",
            f"user:{target.owner()} allow read",
            os.fspath(target),
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    descriptor = os.open(target, os.O_RDONLY | os.O_NOFOLLOW)
    try:
        assert protected_artifacts._darwin_extended_acl_entry_count(descriptor) == 1
        with pytest.raises(ProtectedArtifactIntegrityError, match="extended ACL"):
            protected_artifacts._assert_darwin_no_extended_acl_fd(
                descriptor,
                context="native ACL-bearing file",
            )
    finally:
        os.close(descriptor)


def test_darwin_acl_native_non_null_acl_is_present_and_freed_once(monkeypatch):
    freed: list[int] = []

    class FakeFunction:
        def __init__(self, implementation):
            self.implementation = implementation
            self.argtypes = None
            self.restype = None

        def __call__(self, *args):
            return self.implementation(*args)

    class FakeLibc:
        acl_get_fd_np = FakeFunction(lambda _descriptor, _kind: 123)
        acl_free = FakeFunction(lambda acl: freed.append(acl) or 0)

    monkeypatch.setattr(
        protected_artifacts.ctypes,
        "CDLL",
        lambda *_args, **_kwargs: FakeLibc(),
    )

    assert protected_artifacts._darwin_extended_acl_entry_count(5) == 1
    assert freed == [123]
    assert protected_artifacts._DARWIN_ACL_TYPE_EXTENDED == 0x00000100


def test_darwin_acl_native_enoent_is_absent_and_not_freed(monkeypatch):
    freed: list[int] = []

    class FakeFunction:
        def __init__(self, implementation):
            self.implementation = implementation
            self.argtypes = None
            self.restype = None

        def __call__(self, *args):
            return self.implementation(*args)

    def absent_acl(*_args):
        protected_artifacts.ctypes.set_errno(errno.ENOENT)
        return 0

    class FakeLibc:
        acl_get_fd_np = FakeFunction(absent_acl)
        acl_free = FakeFunction(lambda acl: freed.append(acl) or 0)

    monkeypatch.setattr(
        protected_artifacts.ctypes,
        "CDLL",
        lambda *_args, **_kwargs: FakeLibc(),
    )

    assert protected_artifacts._darwin_extended_acl_entry_count(5) == 0
    assert freed == []


@pytest.mark.parametrize(
    ("native_errno", "message"),
    [
        (0, "errno unknown"),
        (errno.EACCES, f"errno {errno.EACCES}"),
        (errno.EIO, f"errno {errno.EIO}"),
    ],
)
def test_darwin_acl_native_failures_are_not_treated_as_absence(
    monkeypatch,
    native_errno: int,
    message: str,
):
    freed: list[int] = []

    class FakeFunction:
        def __init__(self, implementation):
            self.implementation = implementation
            self.argtypes = None
            self.restype = None

        def __call__(self, *args):
            return self.implementation(*args)

    def failed_acl(*_args):
        protected_artifacts.ctypes.set_errno(native_errno)
        return 0

    class FakeLibc:
        acl_get_fd_np = FakeFunction(failed_acl)
        acl_free = FakeFunction(lambda acl: freed.append(acl) or 0)

    monkeypatch.setattr(
        protected_artifacts.ctypes,
        "CDLL",
        lambda *_args, **_kwargs: FakeLibc(),
    )

    with pytest.raises(ProtectedArtifactIntegrityError, match=message):
        protected_artifacts._darwin_extended_acl_entry_count(5)
    assert freed == []


@pytest.mark.parametrize(
    "relative",
    [
        "",
        ".",
        "../escape.json",
        "/absolute.json",
        "C:\\absolute.json",
        "double//separator.json",
        "trailing./file.json",
        "bad:/file.json",
        "NUL.json",
        "folder/con.txt",
        "COM¹.json",
        "folder/LPT².txt",
        "space /file.json",
        "cafe\u0301.json",
    ],
)
def test_portable_path_rejects_cross_platform_hazards(relative: str):
    with pytest.raises(ProtectedArtifactIntegrityError):
        validate_portable_relative_path(relative)


def test_portable_path_normalizes_windows_separators():
    assert validate_portable_relative_path(r"events\0001.json") == "events/0001.json"


def test_canonical_json_is_stable_and_rejects_nonfinite_values():
    first = canonical_json_bytes({"z": "é", "a": {"two": 2, "one": 1}})
    second = canonical_json_bytes({"a": {"one": 1, "two": 2}, "z": "é"})

    assert first == second
    assert first == '{"a":{"one":1,"two":2},"z":"é"}\n'.encode()
    with pytest.raises(ProtectedArtifactIntegrityError, match="canonical JSON"):
        canonical_json_bytes({"value": float("nan")})


def test_immutable_json_is_atomic_idempotent_and_write_once(tmp_path: Path):
    store = ProtectedArtifactStore(tmp_path / "root", create=True)
    target = store.write_immutable_json("artifacts/0001.json", {"value": 1})

    assert store.exists("artifacts/0001.json") is True
    assert store.read_json("artifacts/0001.json") == {"value": 1}
    assert store.write_immutable_json("artifacts/0001.json", {"value": 1}) == target
    with pytest.raises(ProtectedArtifactIntegrityError, match="different bytes"):
        store.write_immutable_json("artifacts/0001.json", {"value": 2})
    assert store.read_json("artifacts/0001.json") == {"value": 1}


def test_snapshot_and_projection_replace_atomically(tmp_path: Path):
    store = ProtectedArtifactStore(tmp_path / "root", create=True)
    store.write_snapshot_json("run.json", {"generation": 1})
    store.write_snapshot_json("run.json", {"generation": 2})
    store.write_projection_text("events/events.jsonl", "one\r\ntwo\r")

    assert store.read_json("run.json") == {"generation": 2}
    assert store.read_text("events/events.jsonl") == "one\ntwo\n"
    assert not list(store.root.rglob("*.protected-tmp"))


def test_reads_require_bounded_canonical_utf8(tmp_path: Path):
    root = tmp_path / "root"
    store = ProtectedArtifactStore(root, create=True)
    store._write_bytes(
        "pretty.json",
        b'{\n  "value": 1\n}\n',
        immutable=True,
    )
    store._write_bytes("large.txt", b"12345", immutable=True)
    store._write_bytes("binary.txt", b"\xff", immutable=True)

    with pytest.raises(ProtectedArtifactIntegrityError, match="not canonical"):
        store.read_json("pretty.json")
    with pytest.raises(ProtectedArtifactLimitError, match="4-byte"):
        store.read_text("large.txt", max_bytes=4)
    with pytest.raises(ProtectedArtifactIntegrityError, match="not UTF-8"):
        store.read_text("binary.txt")
    with pytest.raises(ProtectedArtifactLimitError, match="positive"):
        store.read_text("large.txt", max_bytes=0)


def test_missing_artifacts_and_parents_report_absent(tmp_path: Path):
    store = ProtectedArtifactStore(tmp_path / "root", create=True)
    assert store.exists("missing.json") is False
    assert store.exists("missing/child.json") is False
    with pytest.raises(FileNotFoundError):
        store.read_json("missing/child.json")


def test_symlink_leaf_and_parent_are_rejected_without_outside_write(tmp_path: Path):
    root = tmp_path / "root"
    store = ProtectedArtifactStore(root, create=True)
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "target.json").write_text('{"safe":true}\n', encoding="utf-8")
    try:
        (root / "leaf.json").symlink_to(outside / "target.json")
        (root / "redirect").symlink_to(outside, target_is_directory=True)
    except OSError as exc:
        pytest.skip(f"symlinks are unavailable: {exc}")

    with pytest.raises(ProtectedArtifactIntegrityError, match="read|link|regular"):
        store.read_json("leaf.json")
    with pytest.raises(ProtectedArtifactIntegrityError, match="write|open|regular"):
        store.write_snapshot_json("redirect/new.json", {"unsafe": True})
    assert not (outside / "new.json").exists()


def test_hard_link_leaf_is_rejected(tmp_path: Path):
    root = tmp_path / "root"
    store = ProtectedArtifactStore(root, create=True)
    outside = tmp_path / "outside.json"
    outside.write_text('{"value":1}\n', encoding="utf-8")
    outside.chmod(0o600)
    try:
        os.link(outside, root / "linked.json")
    except OSError as exc:
        pytest.skip(f"hard links are unavailable: {exc}")

    with pytest.raises(ProtectedArtifactIntegrityError, match="hard links"):
        store.read_json("linked.json")


def test_windows_tree_uses_fresh_metadata_instead_of_cached_direntry_stat(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    store = ProtectedArtifactStore(tmp_path / "root", create=True)
    target = store.write_snapshot_json("run.json", {"generation": 1})
    cached_stat_calls = 0
    fresh_stat_paths: list[Path] = []
    real_fresh_no_follow_stat = protected_artifacts.fresh_no_follow_stat

    class EmulatedWindowsDirEntry:
        name = target.name
        path = os.fspath(target)

        def stat(self, *, follow_symlinks: bool = True):
            nonlocal cached_stat_calls
            cached_stat_calls += 1
            raise AssertionError("Windows DirEntry.stat() metadata must not be trusted")

    @contextmanager
    def guarded(root: Path, components, **options):
        assert root == store.root
        assert tuple(components) == ()
        assert options["require_restrictive_dacl"] is True
        yield root

    @contextmanager
    def open_readonly(path: Path, **options):
        assert path == target
        assert options["require_restrictive_dacl"] is True
        with path.open("rb") as stream:
            yield stream, os.fstat(stream.fileno())

    def fresh_stat(path: str | Path) -> os.stat_result:
        fresh_stat_paths.append(Path(path))
        return real_fresh_no_follow_stat(path)

    monkeypatch.setattr(
        protected_artifacts.os,
        "scandir",
        lambda _directory: [EmulatedWindowsDirEntry()],
    )
    monkeypatch.setattr(
        protected_artifacts,
        "guard_windows_directory_chain",
        guarded,
    )
    monkeypatch.setattr(
        protected_artifacts,
        "open_windows_readonly_file",
        open_readonly,
    )
    monkeypatch.setattr(
        protected_artifacts,
        "fresh_no_follow_stat",
        fresh_stat,
    )

    store._verify_windows_tree()

    assert cached_stat_calls == 0
    assert fresh_stat_paths == [target]


@pytest.mark.skipif(os.name != "nt", reason="native Windows protected-tree checks")
def test_native_windows_reopens_store_with_lock_and_artifact(tmp_path: Path):
    store = ProtectedArtifactStore(tmp_path / "root", create=True)
    store.write_snapshot_json("nested/run.json", {"generation": 1})
    with store.lock():
        pass

    reopened = ProtectedArtifactStore(store.root)

    assert reopened.read_json("nested/run.json") == {"generation": 1}
    with reopened.lock():
        pass


@pytest.mark.skipif(os.name != "nt", reason="native Windows protected-tree checks")
def test_native_windows_reopen_rejects_hard_linked_artifact(tmp_path: Path):
    store = ProtectedArtifactStore(tmp_path / "root", create=True)
    target = store.write_snapshot_json("run.json", {"generation": 1})
    outside = tmp_path / "outside-link.json"
    try:
        os.link(target, outside)
    except OSError as exc:
        pytest.skip(f"hard links are unavailable: {exc}")

    with pytest.raises(ProtectedArtifactIntegrityError, match="hard links"):
        ProtectedArtifactStore(store.root)


@pytest.mark.skipif(os.name != "nt", reason="native Windows protected-tree checks")
def test_native_windows_reopen_rejects_hard_linked_controller_lock(
    tmp_path: Path,
):
    store = ProtectedArtifactStore(tmp_path / "root", create=True)
    with store.lock():
        pass
    outside = tmp_path / "outside-lock"
    try:
        os.link(store.root / "controller.lock", outside)
    except OSError as exc:
        pytest.skip(f"hard links are unavailable: {exc}")

    with pytest.raises(ProtectedArtifactIntegrityError, match="hard links"):
        ProtectedArtifactStore(store.root)


def test_casefold_collision_is_rejected_before_second_write(tmp_path: Path):
    store = ProtectedArtifactStore(tmp_path / "root", create=True)
    store.write_immutable_json("events/Alpha.json", {"value": 1})

    with pytest.raises(ProtectedArtifactIntegrityError, match="collid"):
        store.write_immutable_json("events/alpha.json", {"value": 2})
    events = store.root / "events"
    assert {entry.name for entry in events.iterdir()} == {"Alpha.json"}
    assert (events / "Alpha.json").read_bytes() == canonical_json_bytes({"value": 1})
    assert not list(events.glob("*.protected-tmp"))


def test_nonblocking_controller_lock_is_dedicated_to_root(tmp_path: Path):
    store = ProtectedArtifactStore(tmp_path / "root", create=True)
    second = ProtectedArtifactStore(store.root)

    with store.lock():
        with pytest.raises(ProtectedArtifactLockError, match="already holds"):
            with second.lock():
                pass

    assert (store.root / "controller.lock").read_text(
        encoding="ascii"
    ) == f"{os.getpid()}\n"
    with second.lock():
        pass


def test_lock_rejects_redirected_lock_file(tmp_path: Path):
    store = ProtectedArtifactStore(tmp_path / "root", create=True)
    outside = tmp_path / "outside.lock"
    outside.write_text("keep", encoding="utf-8")
    try:
        (store.root / "controller.lock").symlink_to(outside)
    except OSError as exc:
        pytest.skip(f"symlinks are unavailable: {exc}")

    with pytest.raises(ProtectedArtifactIntegrityError, match="lock|regular"):
        with store.lock():
            pass
    assert outside.read_text(encoding="utf-8") == "keep"


def test_windows_lock_path_is_opened_by_native_leaf_guard(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    store = ProtectedArtifactStore(tmp_path / "root", create=True)
    events: list[str] = []

    @contextmanager
    def guarded(root: Path, components, **options):
        assert root == store.root
        assert tuple(components) == ()
        assert options["require_restrictive_dacl"] is True
        events.append("guard")
        yield root

    def open_lock(path: Path) -> tuple[int, bool]:
        events.append("native-open")
        return os.open(path, os.O_RDWR | os.O_CREAT, 0o600), True

    monkeypatch.setattr(
        protected_artifacts,
        "guard_windows_directory_chain",
        guarded,
    )
    monkeypatch.setattr(
        protected_artifacts,
        "open_windows_guarded_lock_file",
        open_lock,
    )
    descriptor = store._open_windows_lock()
    os.close(descriptor)
    assert events == ["guard", "native-open"]


def test_windows_snapshot_uses_write_through_metadata_replace(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    store = ProtectedArtifactStore(tmp_path / "root", create=True)
    events: list[str] = []

    @contextmanager
    def guarded(root: Path, components, **options):
        assert root == store.root
        assert tuple(components) == ()
        assert options == {
            "create_missing": True,
            "require_restrictive_dacl": True,
        }
        yield root

    def create_private(path: Path) -> int:
        events.append("private-temp")
        return os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)

    def replace(source: Path, target: Path) -> None:
        events.append("write-through-replace")
        os.replace(source, target)

    @contextmanager
    def readonly(path: Path, **options):
        assert options["require_restrictive_dacl"] is True
        descriptor = os.open(path, os.O_RDONLY)
        stream = os.fdopen(descriptor, "rb")
        try:
            yield stream, os.fstat(stream.fileno())
        finally:
            stream.close()

    monkeypatch.setattr(
        protected_artifacts,
        "guard_windows_directory_chain",
        guarded,
    )
    monkeypatch.setattr(
        protected_artifacts,
        "open_windows_private_write_file",
        create_private,
    )
    monkeypatch.setattr(
        protected_artifacts,
        "replace_windows_file_write_through",
        replace,
    )
    monkeypatch.setattr(
        protected_artifacts,
        "open_windows_readonly_file",
        readonly,
    )
    store._write_windows(("run.json",), b'{"generation":1}\n', immutable=False)
    assert events == ["private-temp", "write-through-replace"]


def test_windows_immutable_uses_nonreplacing_write_through_move(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    store = ProtectedArtifactStore(tmp_path / "root", create=True)
    events: list[str] = []

    @contextmanager
    def guarded(root: Path, _components, **_options):
        yield root

    def create_private(path: Path) -> int:
        return os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)

    def move(source: Path, target: Path, *, replace_existing: bool) -> None:
        assert replace_existing is False
        events.append("write-through-no-replace")
        os.rename(source, target)

    @contextmanager
    def readonly(path: Path, **_options):
        descriptor = os.open(path, os.O_RDONLY)
        stream = os.fdopen(descriptor, "rb")
        try:
            yield stream, os.fstat(stream.fileno())
        finally:
            stream.close()

    monkeypatch.setattr(
        protected_artifacts,
        "guard_windows_directory_chain",
        guarded,
    )
    monkeypatch.setattr(
        protected_artifacts,
        "open_windows_private_write_file",
        create_private,
    )
    monkeypatch.setattr(
        protected_artifacts,
        "move_windows_path_write_through",
        move,
    )
    monkeypatch.setattr(
        protected_artifacts,
        "open_windows_readonly_file",
        readonly,
    )

    store._write_windows(("event.json",), b'{"event":1}\n', immutable=True)
    assert events == ["write-through-no-replace"]


def test_failed_atomic_replace_cleans_only_its_owned_temporary(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    store = ProtectedArtifactStore(tmp_path / "root", create=True)
    unknown = store.root / "unknown.txt"
    unknown.write_text("keep", encoding="utf-8")

    def failed_rename(*_args, **_kwargs):
        raise OSError(errno.EIO, "replace failed")

    if os.name == "nt":
        monkeypatch.setattr(
            protected_artifacts,
            "replace_windows_file_write_through",
            failed_rename,
        )
    else:
        monkeypatch.setattr(protected_artifacts.os, "rename", failed_rename)
    with pytest.raises(ProtectedArtifactIntegrityError, match="replace failed"):
        store.write_snapshot_json("run.json", {"generation": 1})

    assert unknown.read_text(encoding="utf-8") == "keep"
    assert not (store.root / "run.json").exists()
    assert not list(store.root.rglob("*.protected-tmp"))


def test_metadata_durability_failure_is_reported_after_atomic_commit(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    store = ProtectedArtifactStore(tmp_path / "root", create=True)

    if os.name == "nt":
        original_windows_replace = (
            protected_artifacts.replace_windows_file_write_through
        )

        def failed_windows_replace(source: Path, target: Path) -> None:
            original_windows_replace(source, target)
            raise protected_artifacts.WindowsDurabilityError(
                "directory metadata flush failed"
            )

        monkeypatch.setattr(
            protected_artifacts,
            "replace_windows_file_write_through",
            failed_windows_replace,
        )
    else:

        def failed_directory_sync(_descriptor: int) -> None:
            raise ProtectedArtifactDurabilityError("directory metadata flush failed")

        monkeypatch.setattr(
            protected_artifacts,
            "_fsync_directory",
            failed_directory_sync,
        )
    with pytest.raises(ProtectedArtifactDurabilityError, match="metadata flush"):
        store.write_snapshot_json("run.json", {"generation": 1})

    # Replacement already committed; callers see that durability was not proven.
    assert store.read_json("run.json") == {"generation": 1}


def test_root_identity_swap_is_detected(tmp_path: Path):
    root = tmp_path / "root"
    store = ProtectedArtifactStore(root, create=True)
    moved = tmp_path / "moved"
    root.rename(moved)
    root.mkdir(mode=0o700)
    root.chmod(0o700)

    with pytest.raises(ProtectedArtifactIntegrityError, match="changed identity"):
        store.write_snapshot_json("run.json", {"generation": 1})
    assert not list(root.iterdir())


def test_emulated_windows_reparse_attributes_are_rejected():
    payload = cast(
        os.stat_result,
        SimpleNamespace(
            st_mode=stat.S_IFREG | 0o600,
            st_reparse_tag=0,
            st_file_attributes=0x00000400,
            st_nlink=1,
        ),
    )

    with pytest.raises(ProtectedArtifactIntegrityError, match="reparse"):
        protected_artifacts._assert_regular_file_stat(payload, context="emulated")


@pytest.mark.parametrize("error_number", [errno.EINVAL, errno.ENOTSUP])
def test_unsupported_directory_fsync_is_a_visible_durability_failure(
    monkeypatch: pytest.MonkeyPatch,
    error_number: int,
):
    def unsupported(_descriptor):
        raise OSError(error_number, "unsupported")

    monkeypatch.setattr(protected_artifacts.os, "fsync", unsupported)
    with pytest.raises(ProtectedArtifactDurabilityError, match="durable"):
        protected_artifacts._fsync_directory(42)
