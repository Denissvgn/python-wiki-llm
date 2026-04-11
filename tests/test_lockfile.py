"""Tests for services/lockfile.py"""
import pytest
from pathlib import Path

from llm_wiki_cli.services.lockfile import WikiLock, LockAcquisitionError


class TestWikiLock:
    def test_acquires_and_releases(self, tmp_path):
        with WikiLock(git_dir=tmp_path):
            lock_file = tmp_path / "llm-wiki.lock"
            assert lock_file.exists()

    def test_writes_pid(self, tmp_path):
        import os
        with WikiLock(git_dir=tmp_path):
            content = (tmp_path / "llm-wiki.lock").read_text()
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
