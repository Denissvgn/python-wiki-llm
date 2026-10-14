"""Filesystem causes remain visible without changing mutation lock authority."""

from __future__ import annotations

import errno
import json
import os
from pathlib import Path, PurePosixPath, PureWindowsPath
import sys

import pytest

from llm_wiki_cli.cli import main
from llm_wiki_cli.services import knowledge_governance as governance
from tests.test_knowledge_loader import _committed_state


def diagnostic(message):
    return json.loads(message.split("could not be opened safely: ", 1)[1])


@pytest.mark.parametrize("number", [errno.EPERM, errno.EACCES, errno.ENOENT, errno.EROFS, errno.ENOSPC, errno.ELOOP])
@pytest.mark.parametrize("filename", ["llm-wiki-storage.lock", "llm-wiki-governance.lock"])
def test_denied_open_retains_destination_cause_chain_and_safe_flags(tmp_path, monkeypatch, number, filename):
    wiki = tmp_path / "project notes" / "wiki"
    wiki.mkdir(parents=True)
    lock_root = wiki.parent / ".git"
    lock_root.mkdir()
    destination = lock_root / filename
    cause = OSError(number, "controlled filesystem refusal", str(destination))
    original = os.open
    observed = []

    def denied(path, flags, *args, **kwargs):
        if Path(path) == destination:
            observed.append(flags)
            raise cause
        return original(path, flags, *args, **kwargs)

    monkeypatch.setattr(governance.os, "open", denied)
    with pytest.raises(governance.GovernanceError) as error:
        with governance.governance_lock(wiki, _lock_filename=filename):
            pytest.fail("refused lock entered mutation")
    row = diagnostic(error.value.message)
    assert row["path"] == str(destination.resolve())
    assert row["failure"] == "lock-open-failed"
    assert row["errno"] == number
    assert row["errno_name"] == errno.errorcode[number]
    assert row["reason"] == "controlled filesystem refusal"
    assert error.value.code == "governance-invalid"
    assert error.value.__cause__ is cause
    assert len(observed) == 1  # No retry or alternate destination.
    assert observed[0] & os.O_RDWR and observed[0] & os.O_CREAT
    if hasattr(os, "O_NOFOLLOW"):
        assert observed[0] & os.O_NOFOLLOW
    assert not destination.exists()


@pytest.mark.parametrize("path", [
    PureWindowsPath("C:/project notes/日本語/.git/llm-wiki-storage.lock"),
    PurePosixPath(r"/project notes/literal\name/.git/llm-wiki-storage.lock"),
])
def test_path_flavors_are_reversible_native_spellings_not_wire_paths(path):
    cause = PermissionError(errno.EACCES, "Access denied")
    setattr(cause, "winerror", 5)
    message = governance._lock_open_diagnostic(path, cause)
    row = diagnostic(message)
    assert row["path"] == os.fspath(path)
    assert row["winerror"] == 5
    assert row["reason"] == "Access denied"
    assert "\n" not in message


@pytest.mark.parametrize("reason", [None, "line one\nline two\x1b[31m" + "x" * 1000])
def test_reason_is_bounded_and_control_characters_are_quoted(reason):
    cause = OSError() if reason is None else OSError(errno.EIO, reason)
    message = governance._lock_open_diagnostic(PurePosixPath('/project/quote"\n/lock'), cause)
    row = diagnostic(message)
    assert row["path"] == '/project/quote"\n/lock'
    assert len(row["reason"]) <= 256
    assert row["reason_truncated"] is (reason is not None)
    assert "\n" not in message and "\x1b" not in message
    if reason is None:
        assert row["reason"] == "OSError" and row["errno_name"] is None


@pytest.mark.parametrize("fault", ["symlink", "hardlink", "concurrent"])
def test_unsafe_and_owned_locks_still_refuse_without_mutating_target(tmp_path, fault):
    wiki = tmp_path / "wiki"
    wiki.mkdir()
    lock_root = tmp_path / ".git"
    lock_root.mkdir()
    lock = lock_root / "llm-wiki-storage.lock"
    outside = tmp_path / "outside"
    outside.write_bytes(b"preserve original bytes")
    if fault == "symlink":
        lock.symlink_to(outside)
    elif fault == "hardlink":
        lock.hardlink_to(outside)
    if fault == "concurrent":
        with governance.governance_lock(wiki, _lock_filename=lock.name):
            with pytest.raises(governance.GovernanceConflictError, match="another governance mutation"):
                with governance.governance_lock(wiki, _lock_filename=lock.name):
                    pytest.fail("second owner entered mutation")
    else:
        match = "symbolic-link" if fault == "symlink" else "hard links"
        with pytest.raises(governance.GovernanceError, match=match):
            with governance.governance_lock(wiki, _lock_filename=lock.name):
                pytest.fail("unsafe lock entered mutation")
    assert outside.read_bytes() == b"preserve original bytes"


def test_actual_cli_reports_refusal_and_read_only_check_does_not_open_locks(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    wiki = tmp_path / "wiki"
    wiki.mkdir()
    _committed_state(wiki)
    lock_root = tmp_path / ".git"
    lock_root.mkdir()
    destination = lock_root / "llm-wiki-storage.lock"
    before = {p.relative_to(wiki).as_posix(): p.read_bytes() for p in wiki.rglob("*") if p.is_file()}
    original = os.open
    attempted = []

    def denied(path, flags, *args, **kwargs):
        if Path(path).name in {"llm-wiki-storage.lock", "llm-wiki-governance.lock"}:
            attempted.append(Path(path))
            raise PermissionError(errno.EPERM, "Operation not permitted", str(path))
        return original(path, flags, *args, **kwargs)

    monkeypatch.setattr(governance.os, "open", denied)
    monkeypatch.setattr(sys, "argv", ["llm-wiki", "knowledge", "migrate", "--wiki-dir", "wiki", "--to", "sharded-v2", "--recovery-dir", "recovery"])
    with pytest.raises(SystemExit) as error:
        main()
    assert error.value.code == 1
    output = capsys.readouterr()
    result = json.loads(output.out)
    assert not result["ok"] and result["error"]["code"] == "governance-invalid"
    row = diagnostic(result["error"]["message"])
    assert row["path"] == str(destination.resolve()) and row["reason"] == "Operation not permitted"
    assert row["failure"] == "lock-open-failed" and row["errno_name"] == "EPERM"
    assert attempted == [destination]
    assert before == {p.relative_to(wiki).as_posix(): p.read_bytes() for p in wiki.rglob("*") if p.is_file()}
    attempted.clear()
    monkeypatch.setattr(sys, "argv", ["llm-wiki", "knowledge", "storage-check", "--wiki-dir", "wiki", "--full", "--format", "json"])
    main()
    assert json.loads(capsys.readouterr().out)["ok"]
    assert not attempted and not list(lock_root.iterdir())
    assert before == {p.relative_to(wiki).as_posix(): p.read_bytes() for p in wiki.rglob("*") if p.is_file()}


def test_bootstrap_cli_stderr_retains_lock_diagnostic(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("LLM_WIKI_DEBUG", raising=False)
    (tmp_path / ".git").mkdir()
    source = tmp_path / "src"
    source.mkdir()
    (source / "app.py").write_text("def run():\n    return 1\n", encoding="utf-8")
    destination = tmp_path / ".git/llm-wiki-storage.lock"
    original = os.open

    def denied(path, flags, *args, **kwargs):
        if Path(path) == destination:
            raise PermissionError(errno.EPERM, "Operation not permitted", str(path))
        return original(path, flags, *args, **kwargs)

    monkeypatch.setattr(governance.os, "open", denied)
    monkeypatch.setattr(sys, "argv", ["llm-wiki", "bootstrap", "--src-dir", "src", "--wiki-dir", "wiki", "--knowledge-format", "sharded-v2", "--skip-flows", "--skip-workflows", "--skip-dependencies"])
    with pytest.raises(SystemExit) as error:
        main()
    assert error.value.code == 1
    output = capsys.readouterr()
    assert "Error: llm-wiki-storage.lock: could not be opened safely" in output.err
    # Resource guidance, if present, is separate from the single-line diagnostic.
    row = diagnostic(next(line for line in output.err.splitlines() if line.startswith("Error:")))
    assert row["path"] == str(destination.resolve())
    assert row["errno_name"] == "EPERM" and row["reason"] == "Operation not permitted"
    assert not destination.exists()
