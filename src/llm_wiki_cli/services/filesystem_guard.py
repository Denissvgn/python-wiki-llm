# pyright: reportAttributeAccessIssue=false
"""Small cross-platform guards for security-sensitive workspace writes.

POSIX callers should prefer descriptor-relative operations.  Windows does not
expose ``openat`` through the Python standard library, so pathname writers pin
every directory in the destination chain with native handles opened without
``FILE_SHARE_DELETE``.  A pinned chain cannot be renamed or replaced by a
junction while the guarded write is in progress.  That rename guarantee
requires ordinary ``FILE_LIST_DIRECTORY`` access; if Windows denies it, the
guard fails closed instead of falling back to an attribute-only handle.
"""

from __future__ import annotations

import ctypes
import hashlib
import os
import stat
import uuid
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import BinaryIO, Iterator, Sequence


_FILE_LIST_DIRECTORY = 0x00000001
_FILE_READ_ATTRIBUTES = 0x00000080
_DELETE = 0x00010000
_READ_CONTROL = 0x00020000
_GENERIC_WRITE = 0x40000000
_FILE_SHARE_READ = 0x00000001
_FILE_SHARE_WRITE = 0x00000002
_FILE_SHARE_DELETE = 0x00000004
_OPEN_EXISTING = 3
_FILE_FLAG_OPEN_REPARSE_POINT = 0x00200000
_FILE_FLAG_BACKUP_SEMANTICS = 0x02000000
_ERROR_ACCESS_DENIED = 5
_EXPECTED_EXISTING_UNSET = object()

GuardedTreeManifestEntry = tuple[str, int, int, int, int, int, str]
GuardedTreeManifest = tuple[GuardedTreeManifestEntry, ...]


class WindowsDirectoryGuardError(OSError):
    """Raised when a Windows directory chain cannot be pinned safely."""


class _WindowsDirectoryGuardUnavailableError(WindowsDirectoryGuardError):
    """Raised when Windows denies access required to pin a directory."""


class WindowsFileGuardError(OSError):
    """Raised when a Windows input file cannot be opened without redirection."""


class WindowsSecurityGuardError(OSError):
    """Raised when a Windows object lacks the required restrictive DACL."""


class WindowsDurabilityError(OSError):
    """Raised when Windows cannot confirm durable filesystem metadata."""


class WindowsIdentityUnavailableError(OSError):
    """Raised when Windows cannot expose a stable filesystem object identity."""


@dataclass(frozen=True)
class WindowsObjectIdentity:
    """Immutable Windows device and file identifier exposed by a real stat call."""

    device: int
    file_id: int

    def __post_init__(self) -> None:
        if not self.device or not self.file_id:
            raise WindowsIdentityUnavailableError(
                "Windows object identity components must both be non-zero."
            )


@dataclass(frozen=True)
class _WindowsPathHandleMetadata:
    """Metadata with consistent semantics across Windows path and handle stats."""

    size: int
    mtime_ns: int


def fresh_no_follow_stat(path: str | Path) -> os.stat_result:
    """Return uncached metadata for one path without following its leaf."""

    return os.stat(path, follow_symlinks=False)


def windows_object_identity(
    result: os.stat_result,
    *,
    context: str,
) -> WindowsObjectIdentity:
    """Extract identity from ``os.stat``/``os.fstat`` Windows metadata.

    ``DirEntry.stat()`` deliberately reports zero for ``st_dev`` and ``st_ino``
    on Windows.  Security-sensitive callers must therefore use a fresh path
    stat or a guarded handle stat before calling this helper.
    """

    return windows_object_identity_from_values(
        device=int(getattr(result, "st_dev", 0)),
        file_id=int(getattr(result, "st_ino", 0)),
        context=context,
    )


def windows_object_identity_from_values(
    *,
    device: int,
    file_id: int,
    context: str,
) -> WindowsObjectIdentity:
    """Build a Windows identity, failing closed when either component is absent."""

    if not device or not file_id:
        raise WindowsIdentityUnavailableError(
            f"Windows object identity is unavailable for {context}."
        )
    return WindowsObjectIdentity(
        device=int(device),
        file_id=file_id,
    )


def _windows_path_handle_metadata(
    result: os.stat_result,
) -> _WindowsPathHandleMetadata:
    """Return metadata safe to compare between Windows path and handle stats.

    On supported Python versions, a Windows pathname ``stat`` and an ``fstat``
    can expose different meanings for ``st_ctime``.  Size and last-write time
    retain matching semantics across those two observation channels.  Callers
    must separately validate safe file kind, reparse-point status, and
    ``WindowsObjectIdentity`` before comparing this metadata.
    """

    return _WindowsPathHandleMetadata(
        size=int(result.st_size),
        mtime_ns=int(
            getattr(result, "st_mtime_ns", int(result.st_mtime * 1_000_000_000))
        ),
    )


@contextmanager
def guard_windows_directory_chain(
    root: Path,
    relative_components: Sequence[str],
    *,
    create_missing: bool = False,
    require_restrictive_dacl: bool = False,
) -> Iterator[Path]:
    """Pin ``root`` and each child directory without delete sharing.

    ``FILE_FLAG_OPEN_REPARSE_POINT`` makes each component inspection operate on
    the link/junction itself.  Holding all ancestor handles without
    ``FILE_SHARE_DELETE`` closes the pathname-parent replacement window that a
    post-write ``lstat`` check cannot close on Windows.
    """

    if os.name != "nt":
        raise WindowsDirectoryGuardError(
            "Windows directory guards are unavailable on this platform."
        )

    root_path = Path(os.path.abspath(os.fspath(root)))
    if not root_path.anchor:
        raise WindowsDirectoryGuardError(
            f"Windows directory guard requires an absolute root: {root}"
        )
    current = Path(root_path.anchor)
    handles: list[int] = []
    try:
        handles.append(_open_windows_directory_guard(current))
        # Pin every ancestor from the drive/UNC anchor through the requested
        # root.  Pinning only ``root`` would still allow an ancestor rename to
        # redirect subsequent pathname opens to a replacement tree.
        root_components = root_path.parts[1:]
        for index, component in enumerate(root_components):
            current /= component
            handles.append(
                _open_windows_directory_guard(
                    current,
                    require_restrictive_dacl=(
                        require_restrictive_dacl and index == len(root_components) - 1
                    ),
                )
            )
        for component in relative_components:
            if component in {"", ".", ".."} or Path(component).name != component:
                raise WindowsDirectoryGuardError(
                    f"Unsafe Windows directory-chain component: {component!r}"
                )
            current /= component
            if create_missing:
                try:
                    if not os.path.lexists(current):
                        if require_restrictive_dacl:
                            create_private_windows_directory(current)
                        else:
                            current.mkdir(exist_ok=True)
                except WindowsDurabilityError:
                    raise
                except OSError as exc:
                    raise WindowsDirectoryGuardError(
                        f"Cannot create guarded Windows directory {current}: {exc}"
                    ) from exc
            handles.append(
                _open_windows_directory_guard(
                    current,
                    require_restrictive_dacl=require_restrictive_dacl,
                )
            )
        yield current
    finally:
        for handle in reversed(handles):
            _close_windows_handle(handle)


def _open_windows_directory_guard(
    path: Path,
    *,
    require_restrictive_dacl: bool = False,
) -> int:
    from ctypes import wintypes

    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    create_file = kernel32.CreateFileW
    create_file.argtypes = (
        wintypes.LPCWSTR,
        wintypes.DWORD,
        wintypes.DWORD,
        wintypes.LPVOID,
        wintypes.DWORD,
        wintypes.DWORD,
        wintypes.HANDLE,
    )
    create_file.restype = wintypes.HANDLE

    get_information = kernel32.GetFileInformationByHandle
    get_information.argtypes = (wintypes.HANDLE, wintypes.LPVOID)
    get_information.restype = wintypes.BOOL

    # FILE_LIST_DIRECTORY is intentionally requested in addition to attribute
    # access.  Attribute-only opens do not establish a sharing barrier, so
    # omitting FILE_SHARE_DELETE would otherwise fail to prevent rename or
    # replacement of this directory.
    desired_access = _FILE_LIST_DIRECTORY | _FILE_READ_ATTRIBUTES
    if require_restrictive_dacl:
        desired_access |= _READ_CONTROL
    handle = create_file(
        _windows_api_path(path),
        desired_access,
        _FILE_SHARE_READ | _FILE_SHARE_WRITE,
        None,
        _OPEN_EXISTING,
        _FILE_FLAG_BACKUP_SEMANTICS | _FILE_FLAG_OPEN_REPARSE_POINT,
        None,
    )
    invalid_handle = wintypes.HANDLE(-1).value
    if handle == invalid_handle:
        error_number = ctypes.get_last_error()
        error = ctypes.WinError(error_number)
        if error_number == _ERROR_ACCESS_DENIED:
            raise _WindowsDirectoryGuardUnavailableError(
                "Windows denied the list-directory access required to pin "
                f"{path}: {error}"
            ) from error
        raise WindowsDirectoryGuardError(
            f"Cannot pin Windows directory {path}: {error}"
        ) from error

    class _ByHandleFileInformation(ctypes.Structure):
        _fields_ = (
            ("dwFileAttributes", wintypes.DWORD),
            ("ftCreationTime", wintypes.FILETIME),
            ("ftLastAccessTime", wintypes.FILETIME),
            ("ftLastWriteTime", wintypes.FILETIME),
            ("dwVolumeSerialNumber", wintypes.DWORD),
            ("nFileSizeHigh", wintypes.DWORD),
            ("nFileSizeLow", wintypes.DWORD),
            ("nNumberOfLinks", wintypes.DWORD),
            ("nFileIndexHigh", wintypes.DWORD),
            ("nFileIndexLow", wintypes.DWORD),
        )

    information = _ByHandleFileInformation()
    if not get_information(handle, ctypes.byref(information)):
        error = ctypes.WinError(ctypes.get_last_error())
        _close_windows_handle(int(handle))
        raise WindowsDirectoryGuardError(
            f"Cannot inspect pinned Windows directory {path}: {error}"
        ) from error
    file_attribute_directory = 0x00000010
    file_attribute_reparse_point = 0x00000400
    attributes = int(information.dwFileAttributes)
    if (
        not attributes & file_attribute_directory
        or attributes & file_attribute_reparse_point
    ):
        _close_windows_handle(int(handle))
        raise WindowsDirectoryGuardError(
            f"Guarded Windows path is not a regular directory: {path}"
        )
    if require_restrictive_dacl:
        try:
            _verify_windows_handle_restrictive_dacl(int(handle), context=str(path))
        except Exception:
            _close_windows_handle(int(handle))
            raise
    return int(handle)


@contextmanager
def open_windows_readonly_file(
    path: Path,
    *,
    require_restrictive_dacl: bool = False,
    require_single_link: bool = True,
) -> Iterator[tuple[BinaryIO, os.stat_result]]:
    """Open one regular Windows file without following a reparse point.

    The native handle permits concurrent readers only.  In particular, it does
    not share writes or deletion, so an inventoried leaf cannot be modified,
    renamed, or replaced while the yielded Python stream is being consumed.
    The caller must separately pin the containing directory chain for the same
    interval.
    """

    if os.name != "nt":
        raise WindowsFileGuardError(
            "Windows read-only file guards are unavailable on this platform."
        )

    if require_restrictive_dacl:
        native_handle: int | None = _open_windows_readonly_file_handle(
            Path(path),
            require_restrictive_dacl=True,
            require_single_link=require_single_link,
        )
    elif require_single_link:
        # Preserve the legacy helper call shape for ordinary read guards and
        # existing embedders that substitute this private boundary in tests.
        native_handle = _open_windows_readonly_file_handle(Path(path))
    else:
        native_handle = _open_windows_readonly_file_handle(
            Path(path),
            require_single_link=False,
        )
    descriptor: int | None = None
    stream: BinaryIO | None = None
    try:
        try:
            import msvcrt

            descriptor = msvcrt.open_osfhandle(
                native_handle,
                os.O_RDONLY
                | getattr(os, "O_BINARY", 0)
                | getattr(os, "O_NOINHERIT", 0),
            )
            # The CRT descriptor owns the native handle after open_osfhandle.
            native_handle = None
            stream = os.fdopen(descriptor, "rb")
            descriptor = None
            opened = os.fstat(stream.fileno())
            try:
                windows_object_identity(opened, context=str(path))
            except WindowsIdentityUnavailableError as exc:
                raise WindowsFileGuardError(str(exc)) from exc
        except WindowsFileGuardError:
            raise
        except OSError as exc:
            raise WindowsFileGuardError(
                f"Cannot expose guarded Windows file {path} as a binary stream: {exc}"
            ) from exc

        # Keep caller exceptions outside the setup translation boundary.  In
        # particular, a destination-write failure while this source stream is
        # open must not be reported as a Windows input-file acquisition error.
        yield stream, opened
    finally:
        if stream is not None:
            stream.close()
        elif descriptor is not None:
            os.close(descriptor)
        elif native_handle is not None:
            _close_windows_handle(native_handle)


def _open_windows_readonly_file_handle(
    path: Path,
    *,
    require_restrictive_dacl: bool = False,
    require_single_link: bool = True,
) -> int:
    from ctypes import wintypes

    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    create_file = kernel32.CreateFileW
    create_file.argtypes = (
        wintypes.LPCWSTR,
        wintypes.DWORD,
        wintypes.DWORD,
        wintypes.LPVOID,
        wintypes.DWORD,
        wintypes.DWORD,
        wintypes.HANDLE,
    )
    create_file.restype = wintypes.HANDLE

    # OPEN_REPARSE_POINT makes validation apply to the leaf itself.  Sharing
    # reads but not writes/deletion freezes its identity and bytes until close.
    handle = create_file(
        _windows_api_path(path),
        0x80000000 | (0x00020000 if require_restrictive_dacl else 0),  # + READ_CONTROL
        0x00000001,  # FILE_SHARE_READ
        None,
        3,  # OPEN_EXISTING
        0x00200000 | 0x08000000,  # OPEN_REPARSE_POINT | SEQUENTIAL_SCAN
        None,
    )
    invalid_handle = wintypes.HANDLE(-1).value
    if handle == invalid_handle:
        error = ctypes.WinError(ctypes.get_last_error())
        raise WindowsFileGuardError(
            f"Cannot safely open Windows input file {path}: {error}"
        ) from error

    native_handle = int(handle)
    try:
        get_file_type = kernel32.GetFileType
        get_file_type.argtypes = (wintypes.HANDLE,)
        get_file_type.restype = wintypes.DWORD
        if int(get_file_type(handle)) != 0x0001:  # FILE_TYPE_DISK
            raise WindowsFileGuardError(
                f"Guarded Windows input is not a disk file: {path}"
            )

        get_information = kernel32.GetFileInformationByHandle
        get_information.argtypes = (wintypes.HANDLE, wintypes.LPVOID)
        get_information.restype = wintypes.BOOL

        class _ByHandleFileInformation(ctypes.Structure):
            _fields_ = (
                ("dwFileAttributes", wintypes.DWORD),
                ("ftCreationTime", wintypes.FILETIME),
                ("ftLastAccessTime", wintypes.FILETIME),
                ("ftLastWriteTime", wintypes.FILETIME),
                ("dwVolumeSerialNumber", wintypes.DWORD),
                ("nFileSizeHigh", wintypes.DWORD),
                ("nFileSizeLow", wintypes.DWORD),
                ("nNumberOfLinks", wintypes.DWORD),
                ("nFileIndexHigh", wintypes.DWORD),
                ("nFileIndexLow", wintypes.DWORD),
            )

        information = _ByHandleFileInformation()
        if not get_information(handle, ctypes.byref(information)):
            error = ctypes.WinError(ctypes.get_last_error())
            raise WindowsFileGuardError(
                f"Cannot inspect guarded Windows input file {path}: {error}"
            ) from error
        attributes = int(information.dwFileAttributes)
        if attributes & (0x00000010 | 0x00000040 | 0x00000400):
            raise WindowsFileGuardError(
                "Guarded Windows input is a directory, device, or reparse point: "
                f"{path}"
            )
        if require_single_link and int(information.nNumberOfLinks) != 1:
            raise WindowsFileGuardError(
                f"Guarded Windows input has additional hard links: {path}"
            )
        if require_restrictive_dacl:
            _verify_windows_handle_restrictive_dacl(
                native_handle,
                context=str(path),
            )
    except Exception:
        _close_windows_handle(native_handle)
        raise
    return native_handle


def create_private_windows_directory(path: Path) -> None:
    """Create one private directory through a write-through atomic rename."""

    if os.name != "nt":
        raise WindowsDirectoryGuardError(
            "Private Windows directory creation is unavailable on this platform."
        )
    from ctypes import wintypes

    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    create_directory = kernel32.CreateDirectoryW
    create_directory.argtypes = (wintypes.LPCWSTR, wintypes.LPVOID)
    create_directory.restype = wintypes.BOOL
    remove_directory = kernel32.RemoveDirectoryW
    remove_directory.argtypes = (wintypes.LPCWSTR,)
    remove_directory.restype = wintypes.BOOL

    target = Path(path)
    temporary = target.parent / (f".{target.name}.{uuid.uuid4().hex}.protected-dir-tmp")
    temporary_exists = False
    try:
        with _private_windows_security_attributes(directory=True) as security:
            if not create_directory(
                _windows_api_path(temporary),
                ctypes.byref(security),
            ):
                error = ctypes.WinError(ctypes.get_last_error())
                raise WindowsDirectoryGuardError(
                    f"Cannot create private Windows directory {temporary}: {error}"
                ) from error
        temporary_exists = True
        handle = _open_windows_directory_guard(
            temporary,
            require_restrictive_dacl=True,
        )
        _close_windows_handle(handle)
        move_windows_path_write_through(
            temporary,
            target,
            replace_existing=False,
        )
        temporary_exists = False
        handle = _open_windows_directory_guard(
            target,
            require_restrictive_dacl=True,
        )
        _close_windows_handle(handle)
    finally:
        if temporary_exists:
            if not remove_directory(_windows_api_path(temporary)):
                error_number = ctypes.get_last_error()
                if error_number not in {2, 3}:  # FILE/PATH_NOT_FOUND
                    error = ctypes.WinError(error_number)
                    raise WindowsDirectoryGuardError(
                        f"Cannot clean private Windows directory {temporary}: {error}"
                    ) from error


def open_windows_private_write_file(path: Path) -> int:
    """Create one private write-through file and return an owning CRT fd."""

    if os.name != "nt":
        raise WindowsFileGuardError(
            "Private Windows file creation is unavailable on this platform."
        )
    from ctypes import wintypes

    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    create_file = kernel32.CreateFileW
    create_file.argtypes = (
        wintypes.LPCWSTR,
        wintypes.DWORD,
        wintypes.DWORD,
        wintypes.LPVOID,
        wintypes.DWORD,
        wintypes.DWORD,
        wintypes.HANDLE,
    )
    create_file.restype = wintypes.HANDLE

    native_handle: int | None = None
    with _private_windows_security_attributes(directory=False) as security:
        handle = create_file(
            _windows_api_path(Path(path)),
            0x40000000 | 0x00020000,  # GENERIC_WRITE | READ_CONTROL
            0,
            ctypes.byref(security),
            1,  # CREATE_NEW
            0x00200000 | 0x08000000 | 0x80000000,
            # OPEN_REPARSE_POINT | SEQUENTIAL_SCAN | WRITE_THROUGH
            None,
        )
        invalid_handle = wintypes.HANDLE(-1).value
        if handle == invalid_handle:
            error = ctypes.WinError(ctypes.get_last_error())
            raise WindowsFileGuardError(
                f"Cannot create private Windows file {path}: {error}"
            ) from error
        native_handle = int(handle)

    try:
        _assert_windows_regular_file_handle(native_handle, Path(path))
        _verify_windows_handle_restrictive_dacl(native_handle, context=str(path))
        import msvcrt

        descriptor = msvcrt.open_osfhandle(
            native_handle,
            os.O_WRONLY | getattr(os, "O_BINARY", 0) | getattr(os, "O_NOINHERIT", 0),
        )
        native_handle = None
        return descriptor
    finally:
        if native_handle is not None:
            _close_windows_handle(native_handle)


def open_windows_guarded_lock_file(path: Path) -> tuple[int, bool]:
    """Open/create a non-reparse lock leaf and return ``(fd, created)``."""

    if os.name != "nt":
        raise WindowsFileGuardError(
            "Guarded Windows lock files are unavailable on this platform."
        )
    from ctypes import wintypes

    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    create_file = kernel32.CreateFileW
    create_file.argtypes = (
        wintypes.LPCWSTR,
        wintypes.DWORD,
        wintypes.DWORD,
        wintypes.LPVOID,
        wintypes.DWORD,
        wintypes.DWORD,
        wintypes.HANDLE,
    )
    create_file.restype = wintypes.HANDLE

    native_handle: int | None = None
    with _private_windows_security_attributes(directory=False) as security:
        ctypes.set_last_error(0)
        handle = create_file(
            _windows_api_path(Path(path)),
            0x80000000 | 0x40000000 | 0x00020000,
            # GENERIC_READ | GENERIC_WRITE | READ_CONTROL
            0x00000001 | 0x00000002,  # FILE_SHARE_READ | FILE_SHARE_WRITE
            ctypes.byref(security),
            4,  # OPEN_ALWAYS
            0x00200000 | 0x80000000,  # OPEN_REPARSE_POINT | WRITE_THROUGH
            None,
        )
        last_error = ctypes.get_last_error()
        invalid_handle = wintypes.HANDLE(-1).value
        if handle == invalid_handle:
            error = ctypes.WinError(last_error)
            raise WindowsFileGuardError(
                f"Cannot safely open Windows lock file {path}: {error}"
            ) from error
        native_handle = int(handle)
        created = last_error != 183  # ERROR_ALREADY_EXISTS

    try:
        _assert_windows_regular_file_handle(native_handle, Path(path))
        _verify_windows_handle_restrictive_dacl(native_handle, context=str(path))
        import msvcrt

        descriptor = msvcrt.open_osfhandle(
            native_handle,
            os.O_RDWR | getattr(os, "O_BINARY", 0) | getattr(os, "O_NOINHERIT", 0),
        )
        native_handle = None
        return descriptor, created
    finally:
        if native_handle is not None:
            _close_windows_handle(native_handle)


def replace_windows_file_write_through(source: Path, target: Path) -> None:
    """Atomically replace ``target`` and request write-through metadata."""

    move_windows_path_write_through(
        source,
        target,
        replace_existing=True,
    )


def move_windows_path_write_through(
    source: Path,
    target: Path,
    *,
    replace_existing: bool,
) -> None:
    """Move one file or directory and persist its namespace update."""

    if os.name != "nt":
        raise WindowsDurabilityError(
            "Write-through Windows moves are unavailable on this platform."
        )
    from ctypes import wintypes

    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    move_file = kernel32.MoveFileExW
    move_file.argtypes = (wintypes.LPCWSTR, wintypes.LPCWSTR, wintypes.DWORD)
    move_file.restype = wintypes.BOOL
    flags = 0x00000008  # MOVEFILE_WRITE_THROUGH
    if replace_existing:
        flags |= 0x00000001  # MOVEFILE_REPLACE_EXISTING
    if not move_file(
        _windows_api_path(Path(source)),
        _windows_api_path(Path(target)),
        flags,
    ):
        error_number = ctypes.get_last_error()
        if not replace_existing and error_number in {80, 183}:
            raise FileExistsError(error_number, os.strerror(error_number), target)
        error = ctypes.WinError(error_number)
        raise WindowsDurabilityError(
            f"Cannot durably move Windows path {source} to {target}: {error}"
        ) from error


def verify_windows_restrictive_dacl(path: Path) -> None:
    """Fail closed unless ``path`` has the protected-store Windows DACL."""

    if os.name != "nt":
        raise WindowsSecurityGuardError(
            "Windows DACL verification is unavailable on this platform."
        )
    payload = Path(path).lstat()
    if payload.st_file_attributes & 0x00000400:
        raise WindowsSecurityGuardError(
            f"Cannot verify a Windows reparse point as protected: {path}"
        )
    if stat.S_ISDIR(payload.st_mode):
        handle = _open_windows_directory_guard(
            Path(path),
            require_restrictive_dacl=True,
        )
        _close_windows_handle(handle)
        return
    handle = _open_windows_file_metadata_guard(Path(path))
    _close_windows_handle(handle)


def windows_current_user_sid() -> str:
    """Return the current process-token user SID as canonical text."""

    if os.name != "nt":
        raise WindowsSecurityGuardError(
            "Windows user SID lookup is unavailable on this platform."
        )
    return _current_windows_user_sid()


def windows_path_owner_sid(path: str | Path) -> str:
    """Return the owner SID of one Windows path without following its leaf."""

    if os.name != "nt":
        raise WindowsSecurityGuardError(
            "Windows path-owner lookup is unavailable on this platform."
        )
    from ctypes import wintypes

    target = Path(path)
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    create_file = kernel32.CreateFileW
    create_file.argtypes = (
        wintypes.LPCWSTR,
        wintypes.DWORD,
        wintypes.DWORD,
        wintypes.LPVOID,
        wintypes.DWORD,
        wintypes.DWORD,
        wintypes.HANDLE,
    )
    create_file.restype = wintypes.HANDLE
    handle = create_file(
        _windows_api_path(target),
        _FILE_READ_ATTRIBUTES | _READ_CONTROL,
        _FILE_SHARE_READ | _FILE_SHARE_WRITE,
        None,
        _OPEN_EXISTING,
        _FILE_FLAG_OPEN_REPARSE_POINT | _FILE_FLAG_BACKUP_SEMANTICS,
        None,
    )
    invalid_handle = wintypes.HANDLE(-1).value
    if handle == invalid_handle:
        error = ctypes.WinError(ctypes.get_last_error())
        raise WindowsSecurityGuardError(
            f"Cannot open Windows path-owner metadata for {target}: {error}"
        ) from error
    native_handle = int(handle)
    try:
        return _windows_handle_owner_sid(native_handle, context=str(target))
    finally:
        _close_windows_handle(native_handle)


def _windows_handle_owner_sid(handle: int, *, context: str) -> str:
    from ctypes import wintypes

    advapi32 = ctypes.WinDLL("advapi32", use_last_error=True)
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    get_security_info = advapi32.GetSecurityInfo
    get_security_info.argtypes = (
        wintypes.HANDLE,
        ctypes.c_int,
        wintypes.DWORD,
        ctypes.POINTER(wintypes.LPVOID),
        ctypes.POINTER(wintypes.LPVOID),
        ctypes.POINTER(wintypes.LPVOID),
        ctypes.POINTER(wintypes.LPVOID),
        ctypes.POINTER(wintypes.LPVOID),
    )
    get_security_info.restype = wintypes.DWORD
    local_free = kernel32.LocalFree
    local_free.argtypes = (wintypes.LPVOID,)
    local_free.restype = wintypes.LPVOID

    owner = wintypes.LPVOID()
    descriptor = wintypes.LPVOID()
    result = get_security_info(
        wintypes.HANDLE(handle),
        1,  # SE_FILE_OBJECT
        0x00000001,  # OWNER_SECURITY_INFORMATION
        ctypes.byref(owner),
        None,
        None,
        None,
        ctypes.byref(descriptor),
    )
    if result != 0:
        error = ctypes.WinError(result)
        raise WindowsSecurityGuardError(
            f"Cannot inspect Windows owner for {context}: {error}"
        ) from error
    try:
        if not owner:
            raise WindowsSecurityGuardError(
                f"Windows returned no owner SID for {context}."
            )
        return _windows_sid_string(owner)
    finally:
        if descriptor:
            local_free(descriptor)


def _open_windows_file_metadata_guard(path: Path) -> int:
    from ctypes import wintypes

    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    create_file = kernel32.CreateFileW
    create_file.argtypes = (
        wintypes.LPCWSTR,
        wintypes.DWORD,
        wintypes.DWORD,
        wintypes.LPVOID,
        wintypes.DWORD,
        wintypes.DWORD,
        wintypes.HANDLE,
    )
    create_file.restype = wintypes.HANDLE
    handle = create_file(
        _windows_api_path(path),
        0x0080 | 0x00020000,  # FILE_READ_ATTRIBUTES | READ_CONTROL
        0x00000001 | 0x00000002,  # FILE_SHARE_READ | FILE_SHARE_WRITE
        None,
        3,  # OPEN_EXISTING
        0x00200000,  # OPEN_REPARSE_POINT
        None,
    )
    invalid_handle = wintypes.HANDLE(-1).value
    if handle == invalid_handle:
        error = ctypes.WinError(ctypes.get_last_error())
        raise WindowsFileGuardError(
            f"Cannot open guarded Windows file metadata {path}: {error}"
        ) from error
    native_handle = int(handle)
    try:
        _assert_windows_regular_file_handle(native_handle, path)
        _verify_windows_handle_restrictive_dacl(
            native_handle,
            context=str(path),
        )
    except Exception:
        _close_windows_handle(native_handle)
        raise
    return native_handle


def _assert_windows_regular_file_handle(handle: int, path: Path) -> None:
    information = _windows_handle_information(handle, path)
    attributes = int(information.dwFileAttributes)
    if attributes & (0x00000010 | 0x00000040 | 0x00000400):
        raise WindowsFileGuardError(
            f"Guarded Windows file is a directory, device, or reparse point: {path}"
        )
    if int(information.nNumberOfLinks) != 1:
        raise WindowsFileGuardError(
            f"Guarded Windows file has additional hard links: {path}"
        )


def _windows_handle_information(handle: int, path: Path) -> ctypes.Structure:
    from ctypes import wintypes

    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    get_file_type = kernel32.GetFileType
    get_file_type.argtypes = (wintypes.HANDLE,)
    get_file_type.restype = wintypes.DWORD
    if int(get_file_type(wintypes.HANDLE(handle))) != 0x0001:  # FILE_TYPE_DISK
        raise WindowsFileGuardError(f"Guarded Windows path is not on disk: {path}")

    class _ByHandleFileInformation(ctypes.Structure):
        _fields_ = (
            ("dwFileAttributes", wintypes.DWORD),
            ("ftCreationTime", wintypes.FILETIME),
            ("ftLastAccessTime", wintypes.FILETIME),
            ("ftLastWriteTime", wintypes.FILETIME),
            ("dwVolumeSerialNumber", wintypes.DWORD),
            ("nFileSizeHigh", wintypes.DWORD),
            ("nFileSizeLow", wintypes.DWORD),
            ("nNumberOfLinks", wintypes.DWORD),
            ("nFileIndexHigh", wintypes.DWORD),
            ("nFileIndexLow", wintypes.DWORD),
        )

    get_information = kernel32.GetFileInformationByHandle
    get_information.argtypes = (wintypes.HANDLE, wintypes.LPVOID)
    get_information.restype = wintypes.BOOL
    information = _ByHandleFileInformation()
    if not get_information(
        wintypes.HANDLE(handle),
        ctypes.byref(information),
    ):
        error = ctypes.WinError(ctypes.get_last_error())
        raise WindowsFileGuardError(
            f"Cannot inspect guarded Windows path {path}: {error}"
        ) from error
    return information


@contextmanager
def _private_windows_security_attributes(
    *,
    directory: bool,
) -> Iterator[ctypes.Structure]:
    from ctypes import wintypes

    advapi32 = ctypes.WinDLL("advapi32", use_last_error=True)
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    convert = advapi32.ConvertStringSecurityDescriptorToSecurityDescriptorW
    convert.argtypes = (
        wintypes.LPCWSTR,
        wintypes.DWORD,
        ctypes.POINTER(wintypes.LPVOID),
        ctypes.POINTER(wintypes.DWORD),
    )
    convert.restype = wintypes.BOOL
    local_free = kernel32.LocalFree
    local_free.argtypes = (wintypes.LPVOID,)
    local_free.restype = wintypes.LPVOID

    class _SecurityAttributes(ctypes.Structure):
        _fields_ = (
            ("nLength", wintypes.DWORD),
            ("lpSecurityDescriptor", wintypes.LPVOID),
            ("bInheritHandle", wintypes.BOOL),
        )

    current_sid = _current_windows_user_sid()
    inheritance = "OICI" if directory else ""
    sddl = (
        f"O:{current_sid}D:P"
        f"(A;{inheritance};FA;;;{current_sid})"
        f"(A;{inheritance};FA;;;SY)"
        f"(A;{inheritance};FA;;;BA)"
    )
    descriptor = wintypes.LPVOID()
    if not convert(sddl, 1, ctypes.byref(descriptor), None):
        error = ctypes.WinError(ctypes.get_last_error())
        raise WindowsSecurityGuardError(
            f"Cannot construct restrictive Windows DACL: {error}"
        ) from error
    attributes = _SecurityAttributes(
        ctypes.sizeof(_SecurityAttributes),
        descriptor,
        False,
    )
    try:
        yield attributes
    finally:
        local_free(descriptor)


def _current_windows_user_sid() -> str:
    from ctypes import wintypes

    advapi32 = ctypes.WinDLL("advapi32", use_last_error=True)
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    open_process_token = advapi32.OpenProcessToken
    open_process_token.argtypes = (
        wintypes.HANDLE,
        wintypes.DWORD,
        ctypes.POINTER(wintypes.HANDLE),
    )
    open_process_token.restype = wintypes.BOOL
    get_token_information = advapi32.GetTokenInformation
    get_token_information.argtypes = (
        wintypes.HANDLE,
        ctypes.c_int,
        wintypes.LPVOID,
        wintypes.DWORD,
        ctypes.POINTER(wintypes.DWORD),
    )
    get_token_information.restype = wintypes.BOOL
    get_current_process = kernel32.GetCurrentProcess
    get_current_process.argtypes = ()
    get_current_process.restype = wintypes.HANDLE

    token = wintypes.HANDLE()
    if not open_process_token(
        get_current_process(),
        0x0008,  # TOKEN_QUERY
        ctypes.byref(token),
    ):
        error = ctypes.WinError(ctypes.get_last_error())
        raise WindowsSecurityGuardError(
            f"Cannot open the current Windows process token: {error}"
        ) from error

    class _SidAndAttributes(ctypes.Structure):
        _fields_ = (
            ("Sid", wintypes.LPVOID),
            ("Attributes", wintypes.DWORD),
        )

    class _TokenUser(ctypes.Structure):
        _fields_ = (("User", _SidAndAttributes),)

    try:
        required = wintypes.DWORD()
        get_token_information(
            token,
            1,  # TokenUser
            None,
            0,
            ctypes.byref(required),
        )
        if required.value == 0:
            error = ctypes.WinError(ctypes.get_last_error())
            raise WindowsSecurityGuardError(
                f"Cannot size the current Windows user SID: {error}"
            ) from error
        buffer = ctypes.create_string_buffer(required.value)
        if not get_token_information(
            token,
            1,
            buffer,
            required,
            ctypes.byref(required),
        ):
            error = ctypes.WinError(ctypes.get_last_error())
            raise WindowsSecurityGuardError(
                f"Cannot read the current Windows user SID: {error}"
            ) from error
        token_user = ctypes.cast(
            buffer,
            ctypes.POINTER(_TokenUser),
        ).contents
        return _windows_sid_string(token_user.User.Sid)
    finally:
        if token.value is not None:
            _close_windows_handle(int(token.value))


def _windows_sid_string(sid: ctypes.c_void_p) -> str:
    from ctypes import wintypes

    advapi32 = ctypes.WinDLL("advapi32", use_last_error=True)
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    convert = advapi32.ConvertSidToStringSidW
    convert.argtypes = (
        wintypes.LPVOID,
        ctypes.POINTER(wintypes.LPWSTR),
    )
    convert.restype = wintypes.BOOL
    local_free = kernel32.LocalFree
    local_free.argtypes = (wintypes.LPVOID,)
    local_free.restype = wintypes.LPVOID

    value = wintypes.LPWSTR()
    if not convert(sid, ctypes.byref(value)):
        error = ctypes.WinError(ctypes.get_last_error())
        raise WindowsSecurityGuardError(
            f"Cannot format a Windows SID: {error}"
        ) from error
    try:
        if value.value is None:
            raise WindowsSecurityGuardError("Windows returned an empty SID.")
        return value.value
    finally:
        local_free(ctypes.cast(value, wintypes.LPVOID))


def _verify_windows_handle_restrictive_dacl(handle: int, *, context: str) -> None:
    from ctypes import wintypes

    advapi32 = ctypes.WinDLL("advapi32", use_last_error=True)
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    get_security_info = advapi32.GetSecurityInfo
    get_security_info.argtypes = (
        wintypes.HANDLE,
        ctypes.c_int,
        wintypes.DWORD,
        ctypes.POINTER(wintypes.LPVOID),
        ctypes.POINTER(wintypes.LPVOID),
        ctypes.POINTER(wintypes.LPVOID),
        ctypes.POINTER(wintypes.LPVOID),
        ctypes.POINTER(wintypes.LPVOID),
    )
    get_security_info.restype = wintypes.DWORD
    get_descriptor_control = advapi32.GetSecurityDescriptorControl
    get_descriptor_control.argtypes = (
        wintypes.LPVOID,
        ctypes.POINTER(wintypes.WORD),
        ctypes.POINTER(wintypes.DWORD),
    )
    get_descriptor_control.restype = wintypes.BOOL
    get_descriptor_dacl = advapi32.GetSecurityDescriptorDacl
    get_descriptor_dacl.argtypes = (
        wintypes.LPVOID,
        ctypes.POINTER(wintypes.BOOL),
        ctypes.POINTER(wintypes.LPVOID),
        ctypes.POINTER(wintypes.BOOL),
    )
    get_descriptor_dacl.restype = wintypes.BOOL
    get_ace = advapi32.GetAce
    get_ace.argtypes = (
        wintypes.LPVOID,
        wintypes.DWORD,
        ctypes.POINTER(wintypes.LPVOID),
    )
    get_ace.restype = wintypes.BOOL
    local_free = kernel32.LocalFree
    local_free.argtypes = (wintypes.LPVOID,)
    local_free.restype = wintypes.LPVOID

    owner = wintypes.LPVOID()
    dacl = wintypes.LPVOID()
    descriptor = wintypes.LPVOID()
    result = get_security_info(
        wintypes.HANDLE(handle),
        1,  # SE_FILE_OBJECT
        0x00000001 | 0x00000004,  # OWNER | DACL
        ctypes.byref(owner),
        None,
        ctypes.byref(dacl),
        None,
        ctypes.byref(descriptor),
    )
    if result != 0:
        error = ctypes.WinError(result)
        raise WindowsSecurityGuardError(
            f"Cannot inspect Windows DACL for {context}: {error}"
        ) from error

    class _Acl(ctypes.Structure):
        _fields_ = (
            ("AclRevision", wintypes.BYTE),
            ("Sbz1", wintypes.BYTE),
            ("AclSize", wintypes.WORD),
            ("AceCount", wintypes.WORD),
            ("Sbz2", wintypes.WORD),
        )

    class _AceHeader(ctypes.Structure):
        _fields_ = (
            ("AceType", wintypes.BYTE),
            ("AceFlags", wintypes.BYTE),
            ("AceSize", wintypes.WORD),
        )

    class _AccessAce(ctypes.Structure):
        _fields_ = (
            ("Header", _AceHeader),
            ("Mask", wintypes.DWORD),
            ("SidStart", wintypes.DWORD),
        )

    try:
        current_sid = _current_windows_user_sid()
        if not owner or _windows_sid_string(owner) != current_sid:
            raise WindowsSecurityGuardError(
                f"Protected Windows object is not owned by the current user: {context}"
            )

        control = wintypes.WORD()
        revision = wintypes.DWORD()
        if not get_descriptor_control(
            descriptor,
            ctypes.byref(control),
            ctypes.byref(revision),
        ):
            error = ctypes.WinError(ctypes.get_last_error())
            raise WindowsSecurityGuardError(
                f"Cannot inspect Windows DACL control for {context}: {error}"
            ) from error
        if not int(control.value) & 0x1000:  # SE_DACL_PROTECTED
            raise WindowsSecurityGuardError(
                f"Protected Windows DACL inherits permissions: {context}"
            )

        present = wintypes.BOOL()
        defaulted = wintypes.BOOL()
        descriptor_dacl = wintypes.LPVOID()
        if not get_descriptor_dacl(
            descriptor,
            ctypes.byref(present),
            ctypes.byref(descriptor_dacl),
            ctypes.byref(defaulted),
        ):
            error = ctypes.WinError(ctypes.get_last_error())
            raise WindowsSecurityGuardError(
                f"Cannot read Windows DACL for {context}: {error}"
            ) from error
        if not present.value or not descriptor_dacl or defaulted.value:
            raise WindowsSecurityGuardError(
                f"Protected Windows object has no explicit non-NULL DACL: {context}"
            )

        allowed_sids = {
            current_sid,
            "S-1-5-18",  # LocalSystem
            "S-1-5-32-544",  # BUILTIN\Administrators
        }
        current_mask = 0
        acl = ctypes.cast(descriptor_dacl, ctypes.POINTER(_Acl)).contents
        for index in range(int(acl.AceCount)):
            ace_pointer = wintypes.LPVOID()
            if not get_ace(
                descriptor_dacl,
                index,
                ctypes.byref(ace_pointer),
            ):
                error = ctypes.WinError(ctypes.get_last_error())
                raise WindowsSecurityGuardError(
                    f"Cannot inspect Windows DACL entry for {context}: {error}"
                ) from error
            ace = ctypes.cast(
                ace_pointer,
                ctypes.POINTER(_AccessAce),
            ).contents
            ace_type = int(ace.Header.AceType)
            if ace_type not in {0, 1}:  # ACCESS_ALLOWED / ACCESS_DENIED
                raise WindowsSecurityGuardError(
                    f"Protected Windows DACL has an unsupported ACE: {context}"
                )
            ace_address = ace_pointer.value
            if ace_address is None:
                raise WindowsSecurityGuardError(
                    f"Windows returned an empty DACL entry for {context}"
                )
            sid_pointer = ctypes.c_void_p(int(ace_address) + _AccessAce.SidStart.offset)
            ace_sid = _windows_sid_string(sid_pointer)
            if ace_type == 1:
                raise WindowsSecurityGuardError(
                    f"Protected Windows DACL has an unevaluated deny ACE: {context}"
                )
            if ace_sid not in allowed_sids:
                raise WindowsSecurityGuardError(
                    "Protected Windows DACL grants access outside the current "
                    f"user, LocalSystem, or Administrators: {context}"
                )
            if ace_sid == current_sid:
                current_mask |= int(ace.Mask)

        file_all_access = 0x001F01FF
        generic_all = 0x10000000
        if (
            current_mask & file_all_access != file_all_access
            and not current_mask & generic_all
        ):
            raise WindowsSecurityGuardError(
                f"Protected Windows DACL does not grant the current user full access: "
                f"{context}"
            )
    finally:
        local_free(descriptor)


def _close_windows_handle(handle: int) -> None:
    if os.name != "nt":  # pragma: no cover - defensive for mocked unit tests
        return
    from ctypes import wintypes

    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    close_handle = kernel32.CloseHandle
    close_handle.argtypes = (wintypes.HANDLE,)
    close_handle.restype = wintypes.BOOL
    close_handle(wintypes.HANDLE(handle))


def _windows_api_path(path: Path) -> str:
    value = os.path.abspath(os.fspath(path))
    if value.startswith("\\\\?\\"):
        return value
    if value.startswith("\\\\"):
        return "\\\\?\\UNC\\" + value[2:]
    return "\\\\?\\" + value


def _read_posix_descriptor(descriptor: int) -> bytes:
    """Read one already-open descriptor from its current offset."""

    chunks: list[bytes] = []
    while chunk := os.read(descriptor, 1024 * 1024):
        chunks.append(chunk)
    return b"".join(chunks)


def _restore_posix_quarantined_entry(
    parent_fd: int,
    quarantine_name: str,
    target_name: str,
) -> bool:
    """Restore a claimed entry without replacing a concurrent target."""

    return _restore_posix_entry_between(
        parent_fd,
        quarantine_name,
        parent_fd,
        target_name,
    )


def _restore_posix_entry_between(
    source_fd: int,
    quarantine_name: str,
    target_fd: int,
    target_name: str,
) -> bool:
    """Restore a claimed entry across pinned directories without replacement."""

    try:
        metadata = os.stat(
            quarantine_name,
            dir_fd=source_fd,
            follow_symlinks=False,
        )
    except FileNotFoundError:
        return True
    if stat.S_ISDIR(metadata.st_mode):
        placeholder_created = False
        try:
            os.mkdir(target_name, 0o700, dir_fd=target_fd)
            placeholder_created = True
            os.rename(
                quarantine_name,
                target_name,
                src_dir_fd=source_fd,
                dst_dir_fd=target_fd,
            )
            return True
        except OSError:
            if placeholder_created:
                try:
                    os.rmdir(target_name, dir_fd=target_fd)
                except OSError:
                    pass
            return False
    try:
        os.link(
            quarantine_name,
            target_name,
            src_dir_fd=source_fd,
            dst_dir_fd=target_fd,
            follow_symlinks=False,
        )
    except OSError:
        return False
    os.unlink(quarantine_name, dir_fd=source_fd)
    return True


def _guarded_tree_manifest_posix_fd(
    directory_fd: int,
    *,
    prefix: str = "",
) -> GuardedTreeManifest:
    """Inventory one pinned POSIX directory tree without following links."""

    nofollow = getattr(os, "O_NOFOLLOW", None)
    directory = getattr(os, "O_DIRECTORY", None)
    if nofollow is None or directory is None:
        raise OSError("This POSIX platform cannot inventory guarded trees.")
    directory_flags = (
        os.O_RDONLY | nofollow | directory | getattr(os, "O_CLOEXEC", 0)
    )
    entries: list[GuardedTreeManifestEntry] = []
    for name in sorted(os.listdir(directory_fd)):
        metadata = os.stat(name, dir_fd=directory_fd, follow_symlinks=False)
        relative = f"{prefix}/{name}" if prefix else name
        payload = ""
        if stat.S_ISLNK(metadata.st_mode):
            payload = os.readlink(name, dir_fd=directory_fd)
        elif stat.S_ISREG(metadata.st_mode):
            descriptor = os.open(
                name,
                os.O_RDONLY | nofollow | getattr(os, "O_CLOEXEC", 0),
                dir_fd=directory_fd,
            )
            try:
                opened = os.fstat(descriptor)
                if (
                    opened.st_dev != metadata.st_dev
                    or opened.st_ino != metadata.st_ino
                    or not stat.S_ISREG(opened.st_mode)
                ):
                    raise OSError(
                        f"Guarded tree entry changed during inspection: {relative}"
                    )
                payload = hashlib.sha256(
                    _read_posix_descriptor(descriptor)
                ).hexdigest()
            finally:
                os.close(descriptor)
        elif not stat.S_ISDIR(metadata.st_mode):
            payload = "special"
        entries.append(
            (
                relative,
                metadata.st_mode,
                metadata.st_dev,
                metadata.st_ino,
                metadata.st_size,
                metadata.st_mtime_ns,
                payload,
            )
        )
        if stat.S_ISDIR(metadata.st_mode):
            child_fd = os.open(name, directory_flags, dir_fd=directory_fd)
            try:
                opened = os.fstat(child_fd)
                if (opened.st_dev, opened.st_ino) != (
                    metadata.st_dev,
                    metadata.st_ino,
                ):
                    raise OSError(
                        f"Guarded tree directory changed during inspection: {relative}"
                    )
                entries.extend(
                    _guarded_tree_manifest_posix_fd(child_fd, prefix=relative)
                )
            finally:
                os.close(child_fd)
    return tuple(entries)


def _guarded_tree_manifest_windows_path(root: Path) -> GuardedTreeManifest:
    """Inventory a Windows tree while its full directory chain is pinned."""

    entries: list[GuardedTreeManifestEntry] = []
    for current_root, directory_names, file_names in os.walk(
        root,
        topdown=True,
        followlinks=False,
    ):
        directory_names.sort()
        file_names.sort()
        current = Path(current_root)
        for name in (*directory_names, *file_names):
            candidate = current / name
            relative = candidate.relative_to(root).as_posix()
            entries.append(_guarded_tree_entry_windows_path(candidate, relative))
    return tuple(entries)


def _guarded_tree_entry_windows_path(
    candidate: Path,
    relative: str,
) -> GuardedTreeManifestEntry:
    """Capture one pinned Windows entry with stable leaf identity."""

    metadata = candidate.lstat()
    identity = windows_object_identity(metadata, context=str(candidate))
    payload = ""
    if getattr(metadata, "st_file_attributes", 0) & 0x00000400:
        payload = os.readlink(candidate)
    elif stat.S_ISREG(metadata.st_mode):
        with open_windows_readonly_file(
            candidate,
            require_single_link=False,
        ) as (stream, opened):
            if windows_object_identity(opened, context=str(candidate)) != identity:
                raise WindowsFileGuardError(
                    f"Guarded tree entry changed during inspection: {candidate}"
                )
            payload = hashlib.sha256(stream.read()).hexdigest()
    elif not stat.S_ISDIR(metadata.st_mode):
        payload = "special"
    return (
        relative,
        metadata.st_mode,
        identity.device,
        identity.file_id,
        metadata.st_size,
        metadata.st_mtime_ns,
        payload,
    )


def guarded_tree_manifest(path: Path) -> GuardedTreeManifest:
    """Return a deterministic manifest from a pinned, no-follow tree root."""

    target = Path(path)
    if not target.is_absolute():
        raise OSError(f"Guarded tree path must be absolute: {target}")
    if os.name == "nt":
        with guard_windows_directory_chain(
            Path(target.anchor),
            target.parts[1:],
        ):
            return _guarded_tree_manifest_windows_path(target)

    nofollow = getattr(os, "O_NOFOLLOW", None)
    directory = getattr(os, "O_DIRECTORY", None)
    if nofollow is None or directory is None:
        raise OSError("This POSIX platform cannot inventory guarded trees.")
    flags = os.O_RDONLY | nofollow | directory | getattr(os, "O_CLOEXEC", 0)
    descriptor = os.open(target.anchor, flags)
    try:
        for component in target.parts[1:]:
            child = os.open(component, flags, dir_fd=descriptor)
            os.close(descriptor)
            descriptor = child
        return _guarded_tree_manifest_posix_fd(descriptor)
    finally:
        os.close(descriptor)


def atomic_write_private_bytes(
    path: Path,
    data: bytes,
    *,
    expected_existing: bytes | None | object = _EXPECTED_EXISTING_UNSET,
) -> Path:
    """Atomically write one private file without following destination paths.

    POSIX writes stay descriptor-relative beneath a pinned parent directory.
    Windows pins the full directory chain and uses private, write-through native
    file creation plus a write-through atomic replacement.
    """

    target = Path(path)
    if not target.is_absolute():
        raise OSError(f"Private atomic output path must be absolute: {target}")
    if target.name in {"", ".", ".."} or target.parent == target:
        raise OSError(f"Private atomic output path has no safe filename: {target}")
    if not isinstance(data, bytes):
        raise TypeError("Private atomic output data must be bytes.")
    if os.name == "nt":
        _atomic_write_private_bytes_windows(
            target,
            data,
            expected_existing=expected_existing,
        )
    else:
        _atomic_write_private_bytes_posix(
            target,
            data,
            expected_existing=expected_existing,
        )
    return target


def atomic_write_executable_bytes(
    path: Path,
    data: bytes,
    *,
    expected_existing: bytes | None | object = _EXPECTED_EXISTING_UNSET,
) -> Path:
    """Atomically write one executable file beneath a pinned directory chain.

    POSIX replacement and mode assignment are descriptor-relative, so a
    concurrent parent-directory rebind cannot redirect the write. Windows has
    no executable mode bit and uses the same guarded replacement as private
    files.
    """

    return atomic_write_guarded_bytes(
        path,
        data,
        mode=0o700,
        require_single_link=False,
        expected_existing=expected_existing,
    )


def atomic_write_guarded_bytes(
    path: Path,
    data: bytes,
    *,
    mode: int = 0o600,
    require_single_link: bool = True,
    expected_existing: bytes | None | object = _EXPECTED_EXISTING_UNSET,
) -> Path:
    """Atomically replace bytes beneath a pinned, no-follow directory chain."""

    target = Path(path)
    if not target.is_absolute():
        raise OSError(f"Guarded output path must be absolute: {target}")
    if target.name in {"", ".", ".."} or target.parent == target:
        raise OSError(f"Guarded output path has no safe filename: {target}")
    if not isinstance(data, bytes):
        raise TypeError("Guarded output data must be bytes.")
    if os.name == "nt":
        _atomic_write_guarded_bytes_windows(
            target,
            data,
            expected_existing=expected_existing,
            require_single_link=require_single_link,
        )
    else:
        _atomic_write_private_bytes_posix(
            target,
            data,
            mode=mode,
            require_single_link=require_single_link,
            expected_existing=expected_existing,
        )
    return target


def ensure_guarded_directory(path: Path, *, mode: int = 0o755) -> Path:
    """Create one directory chain without following a redirected component."""

    target = Path(path)
    if not target.is_absolute():
        raise OSError(f"Guarded directory path must be absolute: {target}")
    if target == Path(target.anchor):
        return target
    if os.name == "nt":
        with guard_windows_directory_chain(
            Path(target.anchor),
            target.parts[1:],
            create_missing=True,
        ):
            return target

    nofollow = getattr(os, "O_NOFOLLOW", None)
    directory = getattr(os, "O_DIRECTORY", None)
    if nofollow is None or directory is None:
        raise OSError("This POSIX platform cannot create guarded directories.")
    flags = os.O_RDONLY | nofollow | directory | getattr(os, "O_CLOEXEC", 0)
    descriptor = os.open(target.anchor, flags)
    try:
        for component in target.parts[1:]:
            if component in {"", ".", ".."} or Path(component).name != component:
                raise OSError(f"Unsafe guarded directory component: {component!r}")
            try:
                child = os.open(component, flags, dir_fd=descriptor)
            except FileNotFoundError:
                os.mkdir(component, mode, dir_fd=descriptor)
                child = os.open(component, flags, dir_fd=descriptor)
            os.close(descriptor)
            descriptor = child
    finally:
        os.close(descriptor)
    return target


def unlink_guarded_bytes(path: Path, *, expected: bytes) -> None:
    """Unlink one exact regular file without following a rebound parent path."""

    target = Path(path)
    if not target.is_absolute():
        raise OSError(f"Guarded unlink path must be absolute: {target}")
    if not isinstance(expected, bytes):
        raise TypeError("Guarded unlink expected content must be bytes.")
    if os.name == "nt":
        quarantine = target.parent / f".llm-wiki-{uuid.uuid4().hex}.unlink-check"
        quarantined = False
        with guard_windows_directory_chain(
            Path(target.parent.anchor),
            target.parent.parts[1:],
        ):
            try:
                move_windows_path_write_through(
                    target,
                    quarantine,
                    replace_existing=False,
                )
                quarantined = True
                metadata = quarantine.lstat()
                if getattr(metadata, "st_file_attributes", 0) & 0x00000400:
                    raise WindowsFileGuardError(
                        f"Guarded unlink target is a reparse point: {target}"
                    )
                with open_windows_readonly_file(
                    quarantine,
                    require_single_link=False,
                ) as (stream, opened):
                    if (
                        not stat.S_ISREG(opened.st_mode)
                        or stream.read() != expected
                    ):
                        raise WindowsFileGuardError(
                            f"Guarded unlink target changed after preflight: {target}"
                        )
                quarantine.unlink()
                quarantined = False
            finally:
                if quarantined:
                    try:
                        move_windows_path_write_through(
                            quarantine,
                            target,
                            replace_existing=False,
                        )
                    except OSError:
                        pass
        return

    nofollow = getattr(os, "O_NOFOLLOW", None)
    directory = getattr(os, "O_DIRECTORY", None)
    if nofollow is None or directory is None:
        raise OSError("This POSIX platform cannot provide guarded unlink.")
    flags = os.O_RDONLY | nofollow | directory | getattr(os, "O_CLOEXEC", 0)
    parent_fd = os.open(target.anchor, flags)
    quarantine = f".llm-wiki-{uuid.uuid4().hex}.unlink-check"
    renamed = False
    try:
        for component in target.parent.parts[1:]:
            child = os.open(component, flags, dir_fd=parent_fd)
            os.close(parent_fd)
            parent_fd = child
        os.rename(
            target.name,
            quarantine,
            src_dir_fd=parent_fd,
            dst_dir_fd=parent_fd,
        )
        renamed = True
        descriptor = os.open(
            quarantine,
            os.O_RDONLY | nofollow | getattr(os, "O_CLOEXEC", 0),
            dir_fd=parent_fd,
        )
        try:
            metadata = os.fstat(descriptor)
            if not stat.S_ISREG(metadata.st_mode):
                raise OSError(f"Guarded unlink target is not a regular file: {target}")
            chunks: list[bytes] = []
            while chunk := os.read(descriptor, 1024 * 1024):
                chunks.append(chunk)
            if b"".join(chunks) != expected:
                raise OSError(
                    f"Guarded unlink target changed after preflight: {target}"
                )
        finally:
            os.close(descriptor)
        os.unlink(quarantine, dir_fd=parent_fd)
        renamed = False
        os.fsync(parent_fd)
    except BaseException:
        if renamed:
            if _restore_posix_quarantined_entry(
                parent_fd,
                quarantine,
                target.name,
            ):
                renamed = False
        raise
    finally:
        os.close(parent_fd)


def remove_guarded_tree(
    path: Path,
    *,
    expected_identity: tuple[int, int] | None = None,
    expected_manifest: GuardedTreeManifest | None = None,
) -> None:
    """Remove one confirmed directory tree through a private quarantine."""

    target = Path(path)
    if not target.is_absolute():
        raise OSError(f"Guarded tree-removal path must be absolute: {target}")
    if os.name == "nt":
        quarantine = target.parent / f".llm-wiki-{uuid.uuid4().hex}.tree-check"
        claimed = quarantine / "tree"
        quarantined = False
        expected_by_path = (
            {entry[0]: entry for entry in expected_manifest}
            if expected_manifest is not None
            else None
        )

        def clear_windows(directory_path: Path, *, prefix: str = "") -> None:
            with guard_windows_directory_chain(
                Path(directory_path.anchor),
                directory_path.parts[1:],
            ):
                names = sorted(os.listdir(directory_path))
                if expected_by_path is not None:
                    expected_names = sorted(
                        relative[len(prefix) + 1 :] if prefix else relative
                        for relative in expected_by_path
                        if (
                            (prefix and relative.startswith(f"{prefix}/"))
                            or (not prefix and "/" not in relative)
                        )
                        and "/"
                        not in (
                            relative[len(prefix) + 1 :] if prefix else relative
                        )
                    )
                    if names != expected_names:
                        raise WindowsDirectoryGuardError(
                            "Guarded tree directory entries changed during removal: "
                            f"{prefix or '.'}"
                        )
                for name in names:
                    relative = f"{prefix}/{name}" if prefix else name
                    candidate = directory_path / name
                    entry_quarantine = (
                        directory_path
                        / f".llm-wiki-{uuid.uuid4().hex}.entry-check"
                    )
                    create_private_windows_directory(entry_quarantine)
                    entry_claimed = entry_quarantine / "entry"
                    entry_moved = False
                    try:
                        move_windows_path_write_through(
                            candidate,
                            entry_claimed,
                            replace_existing=False,
                        )
                        entry_moved = True
                        entry = _guarded_tree_entry_windows_path(
                            entry_claimed,
                            relative,
                        )
                        if expected_by_path is not None and entry != expected_by_path.get(
                            relative
                        ):
                            raise WindowsDirectoryGuardError(
                                "Guarded tree entry changed during removal: "
                                f"{relative}"
                            )
                        is_reparse = bool(
                            getattr(
                                entry_claimed.lstat(),
                                "st_file_attributes",
                                0,
                            )
                            & 0x00000400
                        )
                        if stat.S_ISDIR(entry[1]) and not is_reparse:
                            clear_windows(entry_claimed, prefix=relative)
                            current_identity = windows_object_identity(
                                entry_claimed.lstat(),
                                context=str(entry_claimed),
                            )
                            if (current_identity.device, current_identity.file_id) != (
                                entry[2],
                                entry[3],
                            ):
                                raise WindowsDirectoryGuardError(
                                    "Guarded tree directory changed during removal: "
                                    f"{relative}"
                                )
                            entry_claimed.rmdir()
                        else:
                            if (
                                _guarded_tree_entry_windows_path(
                                    entry_claimed,
                                    relative,
                                )
                                != entry
                            ):
                                raise WindowsFileGuardError(
                                    "Guarded tree entry changed during removal: "
                                    f"{relative}"
                                )
                            entry_claimed.unlink()
                        entry_moved = False
                    finally:
                        if entry_moved:
                            try:
                                move_windows_path_write_through(
                                    entry_claimed,
                                    candidate,
                                    replace_existing=False,
                                )
                            except OSError:
                                pass
                        try:
                            entry_quarantine.rmdir()
                        except OSError:
                            pass
                    if os.path.lexists(candidate):
                        raise WindowsDirectoryGuardError(
                            f"Guarded tree entry appeared during removal: {relative}"
                        )

        with guard_windows_directory_chain(
            Path(target.parent.anchor),
            target.parent.parts[1:],
        ):
            create_private_windows_directory(quarantine)
            try:
                move_windows_path_write_through(
                    target,
                    claimed,
                    replace_existing=False,
                )
                quarantined = True
                metadata = claimed.lstat()
                identity = windows_object_identity(metadata, context=str(claimed))
                if (
                    getattr(metadata, "st_file_attributes", 0) & 0x00000400
                    or not stat.S_ISDIR(metadata.st_mode)
                ):
                    raise WindowsDirectoryGuardError(
                        f"Guarded tree-removal target is not a regular directory: {target}"
                    )
                if expected_identity is not None and (
                    identity.device,
                    identity.file_id,
                ) != expected_identity:
                    raise WindowsDirectoryGuardError(
                        f"Guarded tree-removal target changed after preflight: {target}"
                    )
                confirmed_manifest = _guarded_tree_manifest_windows_path(claimed)
                if (
                    expected_manifest is not None
                    and confirmed_manifest != expected_manifest
                ):
                    raise WindowsDirectoryGuardError(
                        f"Guarded tree-removal contents changed after preflight: {target}"
                    )
                if any(
                    stat.S_ISDIR(entry[1]) and entry[2] != identity.device
                    for entry in confirmed_manifest
                ):
                    raise WindowsDirectoryGuardError(
                        f"Guarded tree removal refuses a nested volume: {target}"
                    )
                clear_windows(claimed)
                current_identity = windows_object_identity(
                    claimed.lstat(),
                    context=str(claimed),
                )
                if current_identity != identity:
                    raise WindowsDirectoryGuardError(
                        f"Guarded tree-removal root changed during removal: {target}"
                    )
                claimed.rmdir()
                quarantined = False
            finally:
                if quarantined:
                    try:
                        move_windows_path_write_through(
                            claimed,
                            target,
                            replace_existing=False,
                        )
                    except OSError:
                        pass
                try:
                    quarantine.rmdir()
                except OSError:
                    pass
        return

    nofollow = getattr(os, "O_NOFOLLOW", None)
    directory = getattr(os, "O_DIRECTORY", None)
    if nofollow is None or directory is None:
        raise OSError("This POSIX platform cannot provide guarded tree removal.")
    flags = os.O_RDONLY | nofollow | directory | getattr(os, "O_CLOEXEC", 0)
    parent_fd = os.open(target.anchor, flags)
    quarantine_name = f".llm-wiki-{uuid.uuid4().hex}.tree-check"
    quarantine_fd: int | None = None
    root_fd: int | None = None
    quarantine_created = False
    quarantined = False
    expected_by_path = (
        {entry[0]: entry for entry in expected_manifest}
        if expected_manifest is not None
        else None
    )

    def current_entry(
        directory_fd: int,
        name: str,
        relative: str,
    ) -> GuardedTreeManifestEntry:
        metadata = os.stat(name, dir_fd=directory_fd, follow_symlinks=False)
        payload = ""
        if stat.S_ISLNK(metadata.st_mode):
            payload = os.readlink(name, dir_fd=directory_fd)
        elif stat.S_ISREG(metadata.st_mode):
            descriptor = os.open(
                name,
                os.O_RDONLY | nofollow | getattr(os, "O_CLOEXEC", 0),
                dir_fd=directory_fd,
            )
            try:
                opened = os.fstat(descriptor)
                if (opened.st_dev, opened.st_ino) != (
                    metadata.st_dev,
                    metadata.st_ino,
                ):
                    raise OSError(
                        f"Guarded tree entry changed during removal: {relative}"
                    )
                payload = hashlib.sha256(
                    _read_posix_descriptor(descriptor)
                ).hexdigest()
            finally:
                os.close(descriptor)
        elif not stat.S_ISDIR(metadata.st_mode):
            payload = "special"
        return (
            relative,
            metadata.st_mode,
            metadata.st_dev,
            metadata.st_ino,
            metadata.st_size,
            metadata.st_mtime_ns,
            payload,
        )

    def clear(directory_fd: int, *, root_device: int, prefix: str = "") -> None:
        names = sorted(os.listdir(directory_fd))
        if expected_by_path is not None:
            expected_names = sorted(
                relative[len(prefix) + 1 :] if prefix else relative
                for relative in expected_by_path
                if (
                    (prefix and relative.startswith(f"{prefix}/"))
                    or (not prefix and "/" not in relative)
                )
                and "/"
                not in (relative[len(prefix) + 1 :] if prefix else relative)
            )
            if names != expected_names:
                raise OSError(
                    "Guarded tree directory entries changed during removal: "
                    f"{prefix or '.'}"
                )
        for name in names:
            relative = f"{prefix}/{name}" if prefix else name
            entry_quarantine = f".llm-wiki-{uuid.uuid4().hex}.entry-check"
            os.mkdir(entry_quarantine, 0o700, dir_fd=directory_fd)
            entry_quarantine_fd = os.open(
                entry_quarantine,
                flags,
                dir_fd=directory_fd,
            )
            claimed = False
            try:
                os.rename(
                    name,
                    "entry",
                    src_dir_fd=directory_fd,
                    dst_dir_fd=entry_quarantine_fd,
                )
                claimed = True
                entry = current_entry(entry_quarantine_fd, "entry", relative)
                if expected_by_path is not None and entry != expected_by_path.get(
                    relative
                ):
                    raise OSError(
                        f"Guarded tree entry changed during removal: {relative}"
                    )
                if stat.S_ISDIR(entry[1]):
                    if entry[2] != root_device:
                        raise OSError(
                            f"Guarded tree removal refuses nested mount: {relative}"
                        )
                    child_fd = os.open(
                        "entry",
                        flags,
                        dir_fd=entry_quarantine_fd,
                    )
                    try:
                        opened = os.fstat(child_fd)
                        if (opened.st_dev, opened.st_ino) != (entry[2], entry[3]):
                            raise OSError(
                                "Guarded tree entry changed during removal: "
                                f"{relative}"
                            )
                        clear(
                            child_fd,
                            root_device=root_device,
                            prefix=relative,
                        )
                    finally:
                        os.close(child_fd)
                    os.rmdir("entry", dir_fd=entry_quarantine_fd)
                else:
                    current = current_entry(
                        entry_quarantine_fd,
                        "entry",
                        relative,
                    )
                    if current != entry:
                        raise OSError(
                            f"Guarded tree entry changed during removal: {relative}"
                        )
                    os.unlink("entry", dir_fd=entry_quarantine_fd)
                claimed = False
            except BaseException:
                if claimed:
                    claimed = not _restore_posix_entry_between(
                        entry_quarantine_fd,
                        "entry",
                        directory_fd,
                        name,
                    )
                raise
            finally:
                os.close(entry_quarantine_fd)
                try:
                    os.rmdir(entry_quarantine, dir_fd=directory_fd)
                except OSError:
                    # A retained claimed entry remains available for recovery.
                    pass
            try:
                os.stat(name, dir_fd=directory_fd, follow_symlinks=False)
            except FileNotFoundError:
                pass
            else:
                raise OSError(
                    f"Guarded tree entry appeared during removal: {relative}"
                )

    try:
        for component in target.parent.parts[1:]:
            child = os.open(component, flags, dir_fd=parent_fd)
            os.close(parent_fd)
            parent_fd = child
        os.mkdir(quarantine_name, 0o700, dir_fd=parent_fd)
        quarantine_created = True
        quarantine_fd = os.open(quarantine_name, flags, dir_fd=parent_fd)
        os.rename(
            target.name,
            "tree",
            src_dir_fd=parent_fd,
            dst_dir_fd=quarantine_fd,
        )
        quarantined = True
        root_fd = os.open("tree", flags, dir_fd=quarantine_fd)
        root_metadata = os.fstat(root_fd)
        root_identity = (root_metadata.st_dev, root_metadata.st_ino)
        if expected_identity is not None and root_identity != expected_identity:
            raise OSError(
                f"Guarded tree-removal target changed after preflight: {target}"
            )
        confirmed_manifest = _guarded_tree_manifest_posix_fd(root_fd)
        if expected_manifest is not None and confirmed_manifest != expected_manifest:
            raise OSError(
                f"Guarded tree-removal contents changed after preflight: {target}"
            )
        if any(
            stat.S_ISDIR(entry[1]) and entry[2] != root_metadata.st_dev
            for entry in confirmed_manifest
        ):
            raise OSError(f"Guarded tree removal refuses a nested mount: {target}")
        clear(root_fd, root_device=root_metadata.st_dev)
        current = os.stat("tree", dir_fd=quarantine_fd, follow_symlinks=False)
        if (current.st_dev, current.st_ino) != root_identity:
            raise OSError(f"Guarded tree-removal root changed during removal: {target}")
        os.rmdir("tree", dir_fd=quarantine_fd)
        quarantined = False
        os.close(root_fd)
        root_fd = None
        os.close(quarantine_fd)
        quarantine_fd = None
        os.rmdir(quarantine_name, dir_fd=parent_fd)
        quarantine_created = False
        os.fsync(parent_fd)
    except BaseException:
        if quarantined and quarantine_fd is not None:
            placeholder_created = False
            try:
                os.mkdir(target.name, 0o700, dir_fd=parent_fd)
                placeholder_created = True
                os.rename(
                    "tree",
                    target.name,
                    src_dir_fd=quarantine_fd,
                    dst_dir_fd=parent_fd,
                )
                quarantined = False
            except OSError:
                if placeholder_created:
                    try:
                        os.rmdir(target.name, dir_fd=parent_fd)
                    except OSError:
                        pass
            if not quarantined:
                try:
                    if root_fd is not None:
                        os.close(root_fd)
                    root_fd = None
                    os.close(quarantine_fd)
                    quarantine_fd = None
                    os.rmdir(quarantine_name, dir_fd=parent_fd)
                    quarantine_created = False
                except OSError:
                    pass
        raise
    finally:
        if root_fd is not None:
            os.close(root_fd)
        if quarantine_fd is not None:
            os.close(quarantine_fd)
        if quarantine_created and not quarantined:
            try:
                os.rmdir(quarantine_name, dir_fd=parent_fd)
            except OSError:
                pass
        os.close(parent_fd)


def _atomic_write_private_bytes_posix(
    target: Path,
    data: bytes,
    *,
    mode: int = 0o600,
    require_single_link: bool = True,
    expected_existing: bytes | None | object = _EXPECTED_EXISTING_UNSET,
) -> None:
    nofollow = getattr(os, "O_NOFOLLOW", None)
    directory = getattr(os, "O_DIRECTORY", None)
    if nofollow is None or directory is None:
        raise OSError("This POSIX platform cannot provide no-follow directory writes.")
    directory_flags = os.O_RDONLY | nofollow | directory | getattr(os, "O_CLOEXEC", 0)
    parent_fd = os.open(target.anchor, directory_flags)
    temporary_name = f".llm-wiki-{uuid.uuid4().hex}.private-tmp"
    quarantine_name = f".llm-wiki-{uuid.uuid4().hex}.replaced"
    temporary_exists = False
    quarantine_exists = False
    file_fd: int | None = None
    staged_identity: tuple[int, int] | None = None
    try:
        for component in target.parent.parts[1:]:
            if component in {"", ".", ".."} or Path(component).name != component:
                raise OSError(
                    f"Unsafe private-output directory component: {component!r}"
                )
            child_fd = os.open(component, directory_flags, dir_fd=parent_fd)
            os.close(parent_fd)
            parent_fd = child_fd

        try:
            existing = os.stat(
                target.name,
                dir_fd=parent_fd,
                follow_symlinks=False,
            )
        except FileNotFoundError:
            existing = None
        if existing is not None and (
            not stat.S_ISREG(existing.st_mode)
            or (require_single_link and existing.st_nlink != 1)
        ):
            raise OSError(
                f"Private atomic output target is not a single-link regular file: "
                f"{target}"
            )
        if expected_existing is not _EXPECTED_EXISTING_UNSET:
            if expected_existing is None:
                if existing is not None:
                    raise OSError(
                        f"Guarded output target appeared after preflight: {target}"
                    )
            else:
                if not isinstance(expected_existing, bytes):
                    raise TypeError("expected_existing must be bytes, None, or omitted")
                if existing is None:
                    raise OSError(
                        f"Guarded output target disappeared after preflight: {target}"
                    )
                existing_fd = os.open(
                    target.name,
                    os.O_RDONLY | nofollow | getattr(os, "O_CLOEXEC", 0),
                    dir_fd=parent_fd,
                )
                try:
                    opened = os.fstat(existing_fd)
                    if (
                        opened.st_dev != existing.st_dev
                        or opened.st_ino != existing.st_ino
                        or not stat.S_ISREG(opened.st_mode)
                    ):
                        raise OSError(
                            f"Guarded output target changed after preflight: {target}"
                        )
                    if _read_posix_descriptor(existing_fd) != expected_existing:
                        raise OSError(
                            f"Guarded output target changed after preflight: {target}"
                        )
                finally:
                    os.close(existing_fd)

        file_fd = os.open(
            temporary_name,
            (
                os.O_WRONLY
                | os.O_CREAT
                | os.O_EXCL
                | nofollow
                | getattr(os, "O_CLOEXEC", 0)
            ),
            0o600,
            dir_fd=parent_fd,
        )
        temporary_exists = True
        view = memoryview(data)
        while view:
            written = os.write(file_fd, view)
            if written <= 0:
                raise OSError("Private atomic output write made no progress.")
            view = view[written:]
        os.fchmod(file_fd, mode)
        os.fsync(file_fd)
        staged = os.fstat(file_fd)
        staged_identity = (staged.st_dev, staged.st_ino)
        os.close(file_fd)
        file_fd = None

        if expected_existing is _EXPECTED_EXISTING_UNSET:
            os.rename(
                temporary_name,
                target.name,
                src_dir_fd=parent_fd,
                dst_dir_fd=parent_fd,
            )
            temporary_exists = False
        elif expected_existing is None:
            # ``link`` supplies portable no-replace commit semantics.  An entry
            # appearing after preflight is preserved and makes the write fail.
            os.link(
                temporary_name,
                target.name,
                src_dir_fd=parent_fd,
                dst_dir_fd=parent_fd,
                follow_symlinks=False,
            )
            os.unlink(temporary_name, dir_fd=parent_fd)
            temporary_exists = False
        else:
            # Claim the exact destination entry, then verify the claimed bytes.
            # This binds the commit to the preflight snapshot instead of doing
            # a check followed by an unconditional replacing rename.
            os.rename(
                target.name,
                quarantine_name,
                src_dir_fd=parent_fd,
                dst_dir_fd=parent_fd,
            )
            quarantine_exists = True
            claimed_fd = os.open(
                quarantine_name,
                os.O_RDONLY | nofollow | getattr(os, "O_CLOEXEC", 0),
                dir_fd=parent_fd,
            )
            try:
                claimed = os.fstat(claimed_fd)
                if (
                    not stat.S_ISREG(claimed.st_mode)
                    or (require_single_link and claimed.st_nlink != 1)
                    or _read_posix_descriptor(claimed_fd) != expected_existing
                ):
                    raise OSError(
                        f"Guarded output target changed after preflight: {target}"
                    )
            finally:
                os.close(claimed_fd)
            os.link(
                temporary_name,
                target.name,
                src_dir_fd=parent_fd,
                dst_dir_fd=parent_fd,
                follow_symlinks=False,
            )
            os.unlink(temporary_name, dir_fd=parent_fd)
            temporary_exists = False
        written = os.stat(
            target.name,
            dir_fd=parent_fd,
            follow_symlinks=False,
        )
        if (
            not stat.S_ISREG(written.st_mode)
            or (require_single_link and written.st_nlink != 1)
            or stat.S_IMODE(written.st_mode) != mode
            or staged_identity != (written.st_dev, written.st_ino)
        ):
            raise OSError(
                f"Private atomic output did not retain safe file metadata: {target}"
            )
        if quarantine_exists:
            os.unlink(quarantine_name, dir_fd=parent_fd)
            quarantine_exists = False
        os.fsync(parent_fd)
    finally:
        if file_fd is not None:
            os.close(file_fd)
        if temporary_exists:
            try:
                os.unlink(temporary_name, dir_fd=parent_fd)
            except FileNotFoundError:
                pass
        if quarantine_exists:
            # Restore without replacing an entry created by another actor.  If
            # the original name is already occupied, retain the claimed bytes
            # under the quarantine name and fail visibly rather than erase
            # either version.
            _restore_posix_quarantined_entry(
                parent_fd,
                quarantine_name,
                target.name,
            )
        os.close(parent_fd)


def _commit_windows_absent_snapshot(temporary: Path, target: Path) -> None:
    """Commit a staged file only while the inspected target remains absent."""

    try:
        move_windows_path_write_through(
            temporary,
            target,
            replace_existing=False,
        )
    except FileExistsError as exc:
        raise OSError(
            f"Guarded output target appeared after preflight: {target}"
        ) from exc


def _atomic_write_private_bytes_windows(
    target: Path,
    data: bytes,
    *,
    expected_existing: bytes | None | object = _EXPECTED_EXISTING_UNSET,
    require_single_link: bool = True,
) -> None:
    parent = target.parent
    relative_components = parent.parts[1:]
    temporary = parent / f".llm-wiki-{uuid.uuid4().hex}.private-tmp"
    quarantine = parent / f".llm-wiki-{uuid.uuid4().hex}.replaced"
    temporary_exists = False
    quarantine_exists = False
    staged_identity: WindowsObjectIdentity | None = None
    with guard_windows_directory_chain(
        Path(parent.anchor),
        relative_components,
    ):
        if os.path.lexists(target):
            existing = target.lstat()
            if (
                getattr(existing, "st_file_attributes", 0) & 0x00000400
                or not stat.S_ISREG(existing.st_mode)
                or (require_single_link and existing.st_nlink != 1)
            ):
                raise WindowsFileGuardError(
                    "Private atomic output target is not a non-reparse, "
                    f"single-link regular file: {target}"
                )
        descriptor = open_windows_private_write_file(temporary)
        temporary_exists = True
        try:
            with os.fdopen(descriptor, "wb", closefd=True) as stream:
                stream.write(data)
                stream.flush()
                os.fsync(stream.fileno())
                staged_identity = windows_object_identity(
                    os.fstat(stream.fileno()),
                    context=str(temporary),
                )

            if expected_existing is _EXPECTED_EXISTING_UNSET:
                replace_windows_file_write_through(temporary, target)
                temporary_exists = False
            elif expected_existing is None:
                _commit_windows_absent_snapshot(temporary, target)
                temporary_exists = False
            else:
                if not isinstance(expected_existing, bytes):
                    raise TypeError("expected_existing must be bytes, None, or omitted")
                move_windows_path_write_through(
                    target,
                    quarantine,
                    replace_existing=False,
                )
                quarantine_exists = True
                with open_windows_readonly_file(
                    quarantine,
                    require_single_link=require_single_link,
                ) as (stream, metadata):
                    if (
                        not stat.S_ISREG(metadata.st_mode)
                        or (require_single_link and metadata.st_nlink != 1)
                        or stream.read() != expected_existing
                    ):
                        raise WindowsFileGuardError(
                            f"Guarded output target changed after preflight: {target}"
                        )
                move_windows_path_write_through(
                    temporary,
                    target,
                    replace_existing=False,
                )
                temporary_exists = False

            written = target.lstat()
            if (
                getattr(written, "st_file_attributes", 0) & 0x00000400
                or not stat.S_ISREG(written.st_mode)
                or (require_single_link and written.st_nlink != 1)
                or windows_object_identity(written, context=str(target))
                != staged_identity
            ):
                raise WindowsFileGuardError(
                    f"Private atomic output changed during commit: {target}"
                )
            verify_windows_restrictive_dacl(target)
            if quarantine_exists:
                quarantine.unlink()
                quarantine_exists = False
        finally:
            if temporary_exists:
                try:
                    temporary.unlink()
                except FileNotFoundError:
                    pass
            if quarantine_exists:
                try:
                    move_windows_path_write_through(
                        quarantine,
                        target,
                        replace_existing=False,
                    )
                except OSError:
                    # A concurrent target is preserved; the claimed private file
                    # remains at the quarantine path for explicit recovery.
                    pass


def _atomic_write_guarded_bytes_windows(
    target: Path,
    data: bytes,
    *,
    expected_existing: bytes | None | object = _EXPECTED_EXISTING_UNSET,
    require_single_link: bool = True,
) -> None:
    """Write a public Windows file with inherited ACL and snapshot binding.

    Unlike the private config writer, managed schemas, hooks, and scaffold
    files inherit their directory's ACL.  The full parent chain remains pinned
    while no-replace namespace moves bind a supplied preflight snapshot.
    """

    parent = target.parent
    relative_components = parent.parts[1:]
    temporary = parent / f".llm-wiki-{uuid.uuid4().hex}.guarded-tmp"
    quarantine = parent / f".llm-wiki-{uuid.uuid4().hex}.replaced"
    temporary_exists = False
    quarantine_exists = False
    staged_identity: WindowsObjectIdentity | None = None
    with guard_windows_directory_chain(
        Path(parent.anchor),
        relative_components,
    ):
        if os.path.lexists(target):
            existing = target.lstat()
            if (
                getattr(existing, "st_file_attributes", 0) & 0x00000400
                or not stat.S_ISREG(existing.st_mode)
                or (require_single_link and existing.st_nlink != 1)
            ):
                raise WindowsFileGuardError(
                    "Guarded Windows output target is not a non-reparse "
                    f"regular file: {target}"
                )
        descriptor = os.open(
            temporary,
            os.O_WRONLY
            | os.O_CREAT
            | os.O_EXCL
            | getattr(os, "O_BINARY", 0)
            | getattr(os, "O_NOINHERIT", 0),
            0o600,
        )
        temporary_exists = True
        try:
            with os.fdopen(descriptor, "wb", closefd=True) as stream:
                stream.write(data)
                stream.flush()
                os.fsync(stream.fileno())
                staged_identity = windows_object_identity(
                    os.fstat(stream.fileno()),
                    context=str(temporary),
                )

            if expected_existing is _EXPECTED_EXISTING_UNSET:
                move_windows_path_write_through(
                    temporary,
                    target,
                    replace_existing=True,
                )
                temporary_exists = False
            elif expected_existing is None:
                _commit_windows_absent_snapshot(temporary, target)
                temporary_exists = False
            else:
                if not isinstance(expected_existing, bytes):
                    raise TypeError("expected_existing must be bytes, None, or omitted")
                move_windows_path_write_through(
                    target,
                    quarantine,
                    replace_existing=False,
                )
                quarantine_exists = True
                with open_windows_readonly_file(
                    quarantine,
                    require_single_link=require_single_link,
                ) as (stream, metadata):
                    if (
                        not stat.S_ISREG(metadata.st_mode)
                        or (require_single_link and metadata.st_nlink != 1)
                        or stream.read() != expected_existing
                    ):
                        raise WindowsFileGuardError(
                            f"Guarded output target changed after preflight: {target}"
                        )
                move_windows_path_write_through(
                    temporary,
                    target,
                    replace_existing=False,
                )
                temporary_exists = False
            written = target.lstat()
            if (
                getattr(written, "st_file_attributes", 0) & 0x00000400
                or not stat.S_ISREG(written.st_mode)
                or (require_single_link and written.st_nlink != 1)
                or windows_object_identity(written, context=str(target))
                != staged_identity
            ):
                raise WindowsFileGuardError(
                    f"Guarded Windows output has unsafe metadata: {target}"
                )
            if quarantine_exists:
                quarantine.unlink()
                quarantine_exists = False
        finally:
            if temporary_exists:
                try:
                    temporary.unlink()
                except FileNotFoundError:
                    pass
            if quarantine_exists:
                try:
                    move_windows_path_write_through(
                        quarantine,
                        target,
                        replace_existing=False,
                    )
                except OSError:
                    # Both entries are retained when another target appeared.
                    pass


__all__ = [
    "GuardedTreeManifest",
    "GuardedTreeManifestEntry",
    "WindowsDirectoryGuardError",
    "WindowsDurabilityError",
    "WindowsFileGuardError",
    "WindowsIdentityUnavailableError",
    "WindowsObjectIdentity",
    "WindowsSecurityGuardError",
    "atomic_write_executable_bytes",
    "atomic_write_guarded_bytes",
    "atomic_write_private_bytes",
    "create_private_windows_directory",
    "ensure_guarded_directory",
    "fresh_no_follow_stat",
    "guard_windows_directory_chain",
    "guarded_tree_manifest",
    "move_windows_path_write_through",
    "open_windows_guarded_lock_file",
    "open_windows_private_write_file",
    "open_windows_readonly_file",
    "replace_windows_file_write_through",
    "remove_guarded_tree",
    "unlink_guarded_bytes",
    "verify_windows_restrictive_dacl",
    "windows_current_user_sid",
    "windows_object_identity",
    "windows_object_identity_from_values",
]
