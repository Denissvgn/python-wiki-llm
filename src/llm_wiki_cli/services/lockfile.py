import fcntl
import os
from pathlib import Path


class LockAcquisitionError(Exception):
    """Raised when the wiki lock cannot be acquired (another sync is running)."""


class WikiLock:
    """Exclusive file lock to prevent concurrent wiki syncs.

    Uses fcntl.flock() for non-blocking exclusive locking on .git/llm-wiki.lock.
    """

    def __init__(self, git_dir: Path = Path(".git")):
        self._lock_path = git_dir / "llm-wiki.lock"
        self._fd = None

    def __enter__(self):
        self._fd = open(self._lock_path, "w")
        try:
            fcntl.flock(self._fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except (BlockingIOError, OSError):
            self._fd.close()
            self._fd = None
            raise LockAcquisitionError(
                "Another llm-wiki sync is already running. Skipping."
            )
        # Write PID for diagnostics
        self._fd.write(str(os.getpid()))
        self._fd.flush()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._fd is not None:
            fcntl.flock(self._fd, fcntl.LOCK_UN)
            self._fd.close()
            self._fd = None
        return False
