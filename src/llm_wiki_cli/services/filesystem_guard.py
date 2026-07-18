"""Small cross-platform guards for security-sensitive workspace writes.

POSIX callers should prefer descriptor-relative operations.  Windows does not
expose ``openat`` through the Python standard library, so pathname writers pin
every directory in the destination chain with native handles opened without
``FILE_SHARE_DELETE``.  A pinned chain cannot be renamed or replaced by a
junction while the guarded write is in progress.
"""

from __future__ import annotations

import ctypes
import os
from contextlib import contextmanager
from pathlib import Path
from typing import BinaryIO, Iterator, Sequence


class WindowsDirectoryGuardError(OSError):
    """Raised when a Windows directory chain cannot be pinned safely."""


class WindowsFileGuardError(OSError):
    """Raised when a Windows input file cannot be opened without redirection."""


@contextmanager
def guard_windows_directory_chain(
    root: Path,
    relative_components: Sequence[str],
    *,
    create_missing: bool = False,
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
        for component in root_path.parts[1:]:
            current /= component
            handles.append(_open_windows_directory_guard(current))
        for component in relative_components:
            if component in {"", ".", ".."} or Path(component).name != component:
                raise WindowsDirectoryGuardError(
                    f"Unsafe Windows directory-chain component: {component!r}"
                )
            current /= component
            if create_missing:
                try:
                    current.mkdir(exist_ok=True)
                except OSError as exc:
                    raise WindowsDirectoryGuardError(
                        f"Cannot create guarded Windows directory {current}: {exc}"
                    ) from exc
            handles.append(_open_windows_directory_guard(current))
        yield current
    finally:
        for handle in reversed(handles):
            _close_windows_handle(handle)


def _open_windows_directory_guard(path: Path) -> int:
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

    # Read attributes only.  Share ordinary reads/writes, but deliberately omit
    # FILE_SHARE_DELETE so the directory cannot be renamed or replaced.
    handle = create_file(
        _windows_api_path(path),
        0x0080,  # FILE_READ_ATTRIBUTES
        0x00000001 | 0x00000002,  # FILE_SHARE_READ | FILE_SHARE_WRITE
        None,
        3,  # OPEN_EXISTING
        0x02000000 | 0x00200000,  # BACKUP_SEMANTICS | OPEN_REPARSE_POINT
        None,
    )
    invalid_handle = wintypes.HANDLE(-1).value
    if handle == invalid_handle:
        error = ctypes.WinError(ctypes.get_last_error())
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
    return int(handle)


@contextmanager
def open_windows_readonly_file(
    path: Path,
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

    native_handle: int | None = _open_windows_readonly_file_handle(Path(path))
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


def _open_windows_readonly_file_handle(path: Path) -> int:
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
        0x80000000,  # GENERIC_READ
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
    except Exception:
        _close_windows_handle(native_handle)
        raise
    return native_handle


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


__all__ = [
    "WindowsDirectoryGuardError",
    "WindowsFileGuardError",
    "guard_windows_directory_chain",
    "open_windows_readonly_file",
]
