"""Tests for services/lockfile.py"""

import pytest

from llm_wiki_cli.services.lockfile import WikiLock, LockAcquisitionError


class TestWikiLock:
    def test_acquires_and_releases(self, tmp_path):
        with WikiLock(git_dir=tmp_path):
            lock_file = tmp_path / "llm-wiki.lock"
            assert lock_file.exists()

    def test_writes_pid(self, tmp_path):
        import os

        with WikiLock(git_dir=tmp_path) as lock:
            # On Windows, msvcrt locks prevent other handles from reading;
            # read through the lock's own file descriptor instead.
            lock._fd.seek(0)
            content = lock._fd.read()
            assert str(os.getpid()) in content

    def test_double_lock_raises(self, tmp_path):
        with WikiLock(git_dir=tmp_path):
            with pytest.raises(LockAcquisitionError):
                with WikiLock(git_dir=tmp_path):
                    pass

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
