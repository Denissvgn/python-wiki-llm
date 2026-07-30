import errno
import math
import os
import sys
import time
from pathlib import Path


_LOCK_SIZE = 4096
_LOCK_RETRY_INTERVAL_SECONDS = 0.05
_LOCK_ACQUISITION_ERROR = "Another llm-wiki sync is already running. Skipping."
_CONTENTION_ERRNOS = frozenset(
    {
        errno.EACCES,
        errno.EAGAIN,
        errno.EWOULDBLOCK,
    }
)
_WINDOWS_CONTENTION_ERRORS = frozenset({32, 33, 36})


class LockAcquisitionError(Exception):
    """Raised when the wiki lock cannot be acquired (another sync is running)."""


class WikiLock:
    """Exclusive file lock to prevent concurrent wiki syncs.

    Uses fcntl.flock() on POSIX and msvcrt.locking() on Windows
    for non-blocking exclusive locking on .git/llm-wiki.lock.  Contention
    remains fail-fast by default; ``wait_seconds`` enables bounded polling.
    """

    def __init__(
        self,
        git_dir: Path = Path(".git"),
        wait_seconds: float = 0,
    ):
        self._lock_path = git_dir / "llm-wiki.lock"
        try:
            parsed_wait = float(wait_seconds)
        except (TypeError, ValueError) as exc:
            raise ValueError(
                "wait_seconds must be a finite non-negative number."
            ) from exc
        if not math.isfinite(parsed_wait) or parsed_wait < 0:
            raise ValueError("wait_seconds must be a finite non-negative number.")
        self._wait_seconds = parsed_wait
        self._fd = None

    def __enter__(self):
        self._fd = open(self._lock_path, "a+")
        try:
            self._acquire_before_deadline()
            # Write PID for diagnostics.
            self._fd.seek(0)
            self._fd.truncate()
            self._fd.write(str(os.getpid()))
            self._fd.flush()
        except BaseException:
            self._fd.close()
            self._fd = None
            raise
        return self

    def _acquire_before_deadline(self) -> None:
        deadline = time.monotonic() + self._wait_seconds
        attempted = False
        while True:
            # Preserve one immediate attempt when wait_seconds is zero, but
            # never begin a later retry after the bounded deadline.
            if attempted and time.monotonic() >= deadline:
                raise LockAcquisitionError(_LOCK_ACQUISITION_ERROR)
            attempted = True
            try:
                self._acquire_once()
                return
            except OSError as exc:
                if not _is_lock_contention_error(exc):
                    raise
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    raise LockAcquisitionError(_LOCK_ACQUISITION_ERROR) from None
                time.sleep(min(_LOCK_RETRY_INTERVAL_SECONDS, remaining))

    def _acquire_once(self) -> None:
        assert self._fd is not None
        if sys.platform == "win32":
            import msvcrt

            # msvcrt locks bytes starting at the current position.  Use a
            # stable range even after another process rewrites the PID.
            self._fd.seek(0)
            msvcrt.locking(self._fd.fileno(), msvcrt.LK_NBLCK, _LOCK_SIZE)
        else:
            import fcntl

            fcntl.flock(self._fd, fcntl.LOCK_EX | fcntl.LOCK_NB)

    def __exit__(self, exc_type, exc_val, exc_tb):
        fd = self._fd
        if fd is not None:
            self._fd = None
            try:
                if sys.platform == "win32":
                    import msvcrt

                    try:
                        fd.seek(0)
                        msvcrt.locking(fd.fileno(), msvcrt.LK_UNLCK, _LOCK_SIZE)
                    except OSError:
                        print(
                            "Warning: failed to release wiki lock file.",
                            file=sys.stderr,
                        )
                else:
                    import fcntl

                    try:
                        fcntl.flock(fd, fcntl.LOCK_UN)
                    except OSError:
                        print(
                            "Warning: failed to release wiki lock file.",
                            file=sys.stderr,
                        )
            finally:
                fd.close()
        return False


def _is_lock_contention_error(exc: OSError) -> bool:
    """Return whether *exc* represents a held non-blocking file lock."""

    if exc.errno in _CONTENTION_ERRNOS:
        return True
    if isinstance(exc, BlockingIOError) and exc.errno is None:
        return True
    return getattr(exc, "winerror", None) in _WINDOWS_CONTENTION_ERRORS
