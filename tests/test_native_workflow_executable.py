"""Owned executable canaries only; never Codex or model execution."""

import os
from pathlib import Path
import sys

import pytest

from tests.native_workflow import executable as binding
from tests.native_workflow import codex_host as host


def client(tmp_path, name='client', content=b"#!/bin/sh\nprintf 'admitted\\n'\n"):
    path = tmp_path / name
    path.write_bytes(content)
    path.chmod(0o700)
    return path


def supported_or_refused(path):
    if sys.platform in {'darwin', 'linux'}:
        return True
    with pytest.raises(binding.ExecutableError, match='unsupported'):
        with binding.prepare_executable(path, host.binary_hash(path)):
            pytest.fail('Unqualified executable backend was selected')
    return False


@pytest.mark.parametrize('change', ['replacement', 'in-place', 'symlink'])
def test_original_path_swaps_cannot_change_executed_bytes(tmp_path, monkeypatch, change):
    source = client(tmp_path)
    if not supported_or_refused(source):
        return
    original = source.read_bytes()
    expected = host.binary_hash(source)
    other = client(tmp_path, 'replacement', b"#!/bin/sh\nprintf 'unadmitted\\n'\n")
    popen = host.subprocess.Popen

    def swapped(argv, **kwargs):
        # Swap after verification at the actual launch boundary, then restore
        # before the caller could perform a post-execution pathname hash.
        if change == 'replacement':
            os.replace(other, source)
        elif change == 'in-place':
            source.write_bytes(other.read_bytes())
        else:
            source.unlink()
            source.symlink_to(other)
        try:
            process = popen(argv, **kwargs)
            process.wait(timeout=5)
            return process
        finally:
            source.unlink()
            source.write_bytes(original)
            source.chmod(0o700)

    monkeypatch.setattr(host.subprocess, 'Popen', swapped)
    with binding.prepare_executable(source, expected) as selected:
        result = host.run_bounded([str(source)], cwd=tmp_path, input_bytes=b'', timeout=5, executable=selected)
        assert result.returncode == 0 and result.stdout == b'admitted\n'
        assert result.executable_binding is not None
        assert result.executable_binding['sha256'] == expected
        target = Path(selected.target)
    assert not target.exists()
    assert host.binary_hash(source) == expected  # A post-call check alone would miss the swap.


def test_snapshot_is_sealed_and_removed_even_on_failure(tmp_path):
    source = client(tmp_path)
    if not supported_or_refused(source):
        return
    target = None
    with pytest.raises(RuntimeError, match='owned failure'):
        with binding.prepare_executable(source, host.binary_hash(source)) as selected:
            target = Path(selected.target)
            with pytest.raises(OSError):
                target.write_bytes(b'replaced')
            if sys.platform == 'darwin':
                with pytest.raises(OSError):
                    target.unlink()
            raise RuntimeError('owned failure')
    assert target is not None and not target.exists()


def test_mutation_during_copy_fails_before_any_launch(tmp_path, monkeypatch):
    source = client(tmp_path)
    if not supported_or_refused(source):
        return
    expected = host.binary_hash(source)
    original_copy = binding._copy
    def mutated(descriptor, destination, cancelled):
        source.write_bytes(b'changed during capture')
        return original_copy(descriptor, destination, cancelled)
    monkeypatch.setattr(binding, '_copy', mutated)
    with pytest.raises(binding.ExecutableError, match='changed since admission'):
        with binding.prepare_executable(source, expected):
            pytest.fail('Changed executable reached launch')


def test_redirected_or_nonexecutable_sources_are_refused(tmp_path):
    source = client(tmp_path)
    if not supported_or_refused(source):
        return
    alias = tmp_path / 'alias'
    alias.symlink_to(source)
    expected = host.binary_hash(source)
    with pytest.raises(binding.ExecutableError):
        with binding.prepare_executable(alias, expected):
            pytest.fail('A mutable executable link was accepted')
    source.chmod(0o600)
    with pytest.raises(binding.ExecutableError, match='executable regular file'):
        with binding.prepare_executable(source, expected):
            pytest.fail('Execute permission was manufactured')


def test_unsupported_sealing_never_falls_back_to_original_path(tmp_path, monkeypatch):
    source = client(tmp_path)
    if not supported_or_refused(source):
        return
    expected = host.binary_hash(source)
    if sys.platform == 'darwin':
        monkeypatch.delattr(binding.os, 'chflags')
    else:
        monkeypatch.delattr(binding.os, 'memfd_create')
    with pytest.raises(binding.ExecutableError, match='unavailable'):
        with binding.prepare_executable(source, expected):
            pytest.fail('Missing sealing support reached execution')


def test_cancelled_capture_never_exposes_an_executable(tmp_path):
    source = client(tmp_path)
    with pytest.raises(binding.ExecutableCancelled):
        with binding.prepare_executable(source, host.binary_hash(source), cancelled=lambda: True):
            pytest.fail('Cancelled preparation reached execution')
