"""Bind a local host launch to verified snapshot bytes, outside task workspaces.

The controller account and OS remain trusted. Untrusted task processes must not
run with that account's authority; this is not general execution admission.
"""

from contextlib import contextmanager
from dataclasses import dataclass
import hashlib
import os
from pathlib import Path
import stat
import sys
import tempfile
import time

MAX_EXECUTABLE_BYTES = 268_435_456


class ExecutableError(ValueError):
    """The selected executable cannot be bound safely before launch."""


class ExecutableCancelled(ExecutableError):
    """Snapshot preparation was cancelled before launch."""


@dataclass(frozen=True)
class ExecutableBinding:
    target: str
    pass_fds: tuple[int, ...]
    kind: str
    sha256: str
    size: int
    preparation_ns: int

    def receipt(self):
        return {'kind': self.kind, 'target': self.target, 'sha256': self.sha256,
                'bytes': self.size, 'preparation_ns': self.preparation_ns}


def _check_cancelled(cancelled):
    if cancelled is not None and cancelled():
        raise ExecutableCancelled('Executable preparation cancelled')


def _copy(source, destination, cancelled):
    copied = 0
    while True:
        _check_cancelled(cancelled)
        block = os.read(source, min(1_048_576, MAX_EXECUTABLE_BYTES + 1 - copied))
        if not block:
            return copied
        copied += len(block)
        if copied > MAX_EXECUTABLE_BYTES:
            raise ExecutableError('Host executable exceeds its byte bound')
        destination.write(block)


def _verify(stream, expected, cancelled):
    result = hashlib.sha256()
    for block in iter(lambda: stream.read(1_048_576), b''):
        _check_cancelled(cancelled)
        result.update(block)
    if 'sha256:' + result.hexdigest() != expected:
        raise ExecutableError('Selected host binary changed since admission')


@contextmanager
def _linux_snapshot(source, expected, cancelled, started):
    import fcntl

    required = ('F_ADD_SEALS', 'F_GET_SEALS', 'F_SEAL_WRITE', 'F_SEAL_GROW', 'F_SEAL_SHRINK', 'F_SEAL_SEAL')
    if (not all(hasattr(fcntl, name) for name in required) or not hasattr(os, 'memfd_create')
            or not hasattr(os, 'MFD_ALLOW_SEALING')):
        raise ExecutableError('Sealed executable descriptors are unavailable')
    flags = getattr(os, 'MFD_CLOEXEC') | getattr(os, 'MFD_ALLOW_SEALING') | getattr(os, 'MFD_EXEC', 0)
    descriptor = getattr(os, 'memfd_create')('native-host-executable', flags=flags)
    try:
        with os.fdopen(descriptor, 'wb', closefd=False) as stream:
            size = _copy(source, stream, cancelled)
        os.fchmod(descriptor, 0o500)
        seals = (getattr(fcntl, 'F_SEAL_WRITE') | getattr(fcntl, 'F_SEAL_GROW')
                 | getattr(fcntl, 'F_SEAL_SHRINK') | getattr(fcntl, 'F_SEAL_SEAL'))
        fcntl.fcntl(descriptor, getattr(fcntl, 'F_ADD_SEALS'), seals)
        if fcntl.fcntl(descriptor, getattr(fcntl, 'F_GET_SEALS')) & seals != seals:
            raise ExecutableError('Executable descriptor was not sealed')
        os.lseek(descriptor, 0, os.SEEK_SET)
        with os.fdopen(descriptor, 'rb', closefd=False) as stream:
            _verify(stream, expected, cancelled)
        target = f'/proc/self/fd/{descriptor}'
        current = os.stat(target)
        retained = os.fstat(descriptor)
        if (current.st_dev, current.st_ino) != (retained.st_dev, retained.st_ino):
            raise ExecutableError('Executable descriptor path is unavailable')
        yield ExecutableBinding(target, (descriptor,), 'linux-sealed-memfd/v1', expected, size,
                                time.monotonic_ns() - started)
    finally:
        os.close(descriptor)


@contextmanager
def _macos_snapshot(source, expected, cancelled, started):
    if not hasattr(os, 'chflags') or not hasattr(stat, 'UF_IMMUTABLE'):
        raise ExecutableError('Immutable executable snapshots are unavailable')
    with tempfile.TemporaryDirectory(prefix='native-host-executable-') as temporary:
        directory = Path(temporary)
        snapshot = directory / 'codex'
        try:
            with snapshot.open('xb') as stream:
                size = _copy(source, stream, cancelled)
                stream.flush()
                os.fsync(stream.fileno())
            snapshot.chmod(0o500)
            directory.chmod(0o500)
            # Protect the data and its directory entry through the entire call.
            # These are new controller-owned paths, never the configured source.
            for path in (snapshot, directory):
                os.chflags(path, stat.UF_IMMUTABLE, follow_symlinks=False)
                if not path.stat(follow_symlinks=False).st_flags & stat.UF_IMMUTABLE:
                    raise ExecutableError('Executable snapshot was not made immutable')
            with snapshot.open('rb') as stream:
                _verify(stream, expected, cancelled)
            yield ExecutableBinding(str(snapshot), (), 'macos-immutable-copy/v1', expected, size,
                                    time.monotonic_ns() - started)
        finally:
            # Unseal even if preparation fails midway, or cancellation interrupts
            # launch. Never leave an immutable temporary directory behind.
            for path in (directory, snapshot):
                if path.exists() and path.stat(follow_symlinks=False).st_flags & stat.UF_IMMUTABLE:
                    os.chflags(path, 0, follow_symlinks=False)
            directory.chmod(0o700)


@contextmanager
def prepare_executable(path: Path, expected: str, *, cancelled=None):
    """Snapshot, seal and hash once; never execute the original pathname."""
    _check_cancelled(cancelled)
    if (not path.is_absolute() or not isinstance(expected, str) or len(expected) != 71
            or not expected.startswith('sha256:') or any(c not in '0123456789abcdef' for c in expected[7:])):
        raise ExecutableError('An absolute host path and SHA-256 commitment are required')
    if sys.platform not in {'darwin', 'linux'} or not hasattr(os, 'O_NOFOLLOW'):
        raise ExecutableError('Executable binding is unsupported on this platform')
    descriptor = None
    started = time.monotonic_ns()
    try:
        descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK | getattr(os, 'O_CLOEXEC', 0))
        info = os.fstat(descriptor)
        if not stat.S_ISREG(info.st_mode) or not info.st_mode & 0o111 or not 0 < info.st_size <= MAX_EXECUTABLE_BYTES:
            raise ExecutableError('Host executable must be a bounded executable regular file')
        if info.st_mode & (stat.S_ISUID | stat.S_ISGID):
            raise ExecutableError('Elevated host executables are not supported')
        snapshot = _macos_snapshot if sys.platform == 'darwin' else _linux_snapshot
        with snapshot(descriptor, expected, cancelled, started) as binding:
            yield binding
    except OSError as error:
        raise ExecutableError(f'Cannot bind the selected host executable: {error}') from error
    finally:
        if descriptor is not None:
            os.close(descriptor)
