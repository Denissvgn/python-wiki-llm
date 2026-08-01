"""Tests for services/lockfile.py"""

import errno
import os
import re
import subprocess
import sys
import time
import types

import pytest

from llm_wiki_cli.services import lockfile
from llm_wiki_cli.services.lockfile import LockAcquisitionError, WikiLock


class TestWikiLock:
    def test_acquires_and_releases(self, tmp_path):
        with WikiLock(git_dir=tmp_path):
            lock_file = tmp_path / "llm-wiki.lock"
            assert lock_file.exists()

    def test_writes_pid(self, tmp_path):
        with WikiLock(git_dir=tmp_path) as lock:
            assert lock._fd is not None
            # On Windows, msvcrt locks prevent other handles from reading;
            # read through the lock's own file descriptor instead.
            lock._fd.seek(0)
            content = lock._fd.read()
            assert str(os.getpid()) in content

    def test_double_lock_raises(self, tmp_path):
        with WikiLock(git_dir=tmp_path):
            with pytest.raises(
                LockAcquisitionError,
                match=re.escape(
                    "Another llm-wiki sync is already running. Skipping."
                ),
            ):
                with WikiLock(git_dir=tmp_path):
                    pass

    def test_default_contention_does_not_sleep(self, tmp_path, monkeypatch):
        def unexpected_sleep(_seconds):
            raise AssertionError("default lock acquisition must remain fail-fast")

        monkeypatch.setattr(lockfile.time, "sleep", unexpected_sleep)

        with WikiLock(git_dir=tmp_path):
            with pytest.raises(LockAcquisitionError):
                with WikiLock(git_dir=tmp_path):
                    pass

    def test_waiting_lock_acquires_after_holder_process_releases(self, tmp_path):
        hold_script = """
import sys
import time
from pathlib import Path
from llm_wiki_cli.services.lockfile import WikiLock

with WikiLock(Path(sys.argv[1])):
    print("locked", flush=True)
    time.sleep(0.2)
"""
        holder = subprocess.Popen(
            [sys.executable, "-c", hold_script, str(tmp_path)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        try:
            assert holder.stdout is not None
            assert holder.stdout.readline().strip() == "locked"

            with WikiLock(git_dir=tmp_path, wait_seconds=2):
                pass

            stdout, stderr = holder.communicate(timeout=5)
            assert holder.returncode == 0, (stdout, stderr)
        finally:
            if holder.poll() is None:
                holder.kill()
                holder.wait(timeout=5)

    def test_wait_timeout_preserves_existing_error(self, tmp_path):
        with WikiLock(git_dir=tmp_path):
            started = time.monotonic()
            with pytest.raises(
                LockAcquisitionError,
                match=re.escape(
                    "Another llm-wiki sync is already running. Skipping."
                ),
            ):
                with WikiLock(git_dir=tmp_path, wait_seconds=0.06):
                    pass
            assert time.monotonic() - started >= 0.04

    def test_windows_retry_uses_stable_byte_range(self, tmp_path, monkeypatch):
        calls = []
        lock_attempts = 0
        fake_msvcrt = types.SimpleNamespace(LK_NBLCK=1, LK_UNLCK=2)

        def fake_locking(fd, mode, size):
            nonlocal lock_attempts
            calls.append((mode, size, os.lseek(fd, 0, os.SEEK_CUR)))
            if mode == fake_msvcrt.LK_NBLCK:
                lock_attempts += 1
                if lock_attempts == 1:
                    raise OSError(errno.EACCES, "contended")

        fake_msvcrt.locking = fake_locking
        monkeypatch.setitem(sys.modules, "msvcrt", fake_msvcrt)
        monkeypatch.setattr(lockfile.sys, "platform", "win32")
        monkeypatch.setattr(lockfile.time, "sleep", lambda _seconds: None)

        with WikiLock(git_dir=tmp_path, wait_seconds=1):
            pass

        assert calls == [
            (fake_msvcrt.LK_NBLCK, lockfile._LOCK_SIZE, 0),
            (fake_msvcrt.LK_NBLCK, lockfile._LOCK_SIZE, 0),
            (fake_msvcrt.LK_UNLCK, lockfile._LOCK_SIZE, 0),
        ]

    def test_wait_deadline_is_checked_before_a_late_retry(
        self, tmp_path, monkeypatch
    ):
        clock = 0.0
        attempts = 0
        candidate = WikiLock(git_dir=tmp_path, wait_seconds=1)

        def monotonic():
            return clock

        def oversleep(_seconds):
            nonlocal clock
            clock = 1.5

        def contended_attempt():
            nonlocal attempts
            attempts += 1
            raise BlockingIOError(errno.EAGAIN, "contended")

        monkeypatch.setattr(lockfile.time, "monotonic", monotonic)
        monkeypatch.setattr(lockfile.time, "sleep", oversleep)
        monkeypatch.setattr(candidate, "_acquire_once", contended_attempt)

        with pytest.raises(LockAcquisitionError):
            with candidate:
                pass

        assert attempts == 1

    def test_non_contention_os_error_is_not_retried(self, tmp_path, monkeypatch):
        candidate = WikiLock(git_dir=tmp_path, wait_seconds=1)
        attempts = 0

        def failed_attempt():
            nonlocal attempts
            attempts += 1
            raise OSError(errno.EBADF, "bad descriptor")

        def unexpected_sleep(_seconds):
            raise AssertionError("non-contention errors must not be retried")

        monkeypatch.setattr(candidate, "_acquire_once", failed_attempt)
        monkeypatch.setattr(lockfile.time, "sleep", unexpected_sleep)

        with pytest.raises(OSError) as raised:
            with candidate:
                pass

        assert raised.value.errno == errno.EBADF
        assert attempts == 1
        assert candidate._fd is None

    def test_posix_unlock_error_still_closes_and_forgets_descriptor(
        self, tmp_path, monkeypatch, capsys
    ):
        candidate = WikiLock(git_dir=tmp_path)
        descriptor = open(tmp_path / "llm-wiki.lock", "a+")
        candidate._fd = descriptor
        fake_fcntl = types.SimpleNamespace(LOCK_UN=8)

        def failed_unlock(_fd, mode):
            assert mode == fake_fcntl.LOCK_UN
            raise OSError(errno.EIO, "unlock failed")

        fake_fcntl.flock = failed_unlock
        monkeypatch.setitem(sys.modules, "fcntl", fake_fcntl)
        monkeypatch.setattr(lockfile.sys, "platform", "linux")

        assert candidate.__exit__(None, None, None) is False

        assert descriptor.closed
        assert candidate._fd is None
        assert "failed to release wiki lock" in capsys.readouterr().err

    @pytest.mark.parametrize("wait_seconds", [-1, float("inf"), float("nan"), "bad"])
    def test_rejects_invalid_wait(self, tmp_path, wait_seconds):
        with pytest.raises(
            ValueError,
            match="wait_seconds must be a finite non-negative number",
        ):
            WikiLock(git_dir=tmp_path, wait_seconds=wait_seconds)

    def test_releases_after_exit(self, tmp_path):
        with WikiLock(git_dir=tmp_path):
            pass
        # Second lock should succeed after first is released
        with WikiLock(git_dir=tmp_path):
            pass

    def test_releases_on_exception(self, tmp_path):
        with pytest.raises(RuntimeError):
            with WikiLock(git_dir=tmp_path):
                raise RuntimeError("boom")
        # Should be released
        with WikiLock(git_dir=tmp_path):
            pass
