"""A sync in a clean linked worktree records a clean working tree and reaches a fixpoint."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from llm_wiki_cli import cli

pytestmark = pytest.mark.skipif(shutil.which("git") is None, reason="git is not available")

SERVICE = (
    "class OrderService:\n"
    "    def create(self, name: str) -> dict:\n"
    "        return {\"name\": name}\n"
)
ADDITION = (
    "\n\nclass InvoiceService:\n"
    "    def issue(self, order: dict) -> dict:\n"
    "        return {\"order\": order}\n"
)
LOCK_FILES = ("llm-wiki-governance.lock", "llm-wiki-storage.lock")


@pytest.fixture
def git_environment(monkeypatch, tmp_path):
    for key in list(os.environ):
        if key.startswith("GIT_"):
            monkeypatch.delenv(key)
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", os.devnull)
    monkeypatch.setenv("GIT_CONFIG_NOSYSTEM", "1")
    monkeypatch.setenv("LLM_WIKI_CACHE_DIR", str(tmp_path / "cache"))


def _git(root: Path, *arguments: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(root), *arguments],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"git {' '.join(arguments)}: {result.stderr}"
    return result.stdout.strip()


def _run(monkeypatch, root: Path, *arguments: str) -> None:
    monkeypatch.chdir(root)
    monkeypatch.setattr(sys, "argv", ["llm-wiki", *arguments])
    try:
        cli.main()
    except SystemExit as exc:
        assert exc.code in (0, None)


def _commit_all(root: Path, message: str) -> None:
    _git(root, "add", "-A")
    _git(root, "commit", "--quiet", "-m", message)


def _adopted_repository_with_pending_change(monkeypatch, tmp_path: Path) -> Path:
    repository = tmp_path / "repo"
    (repository / "app").mkdir(parents=True)
    _git(repository, "init", "--quiet", "-b", "main")
    _git(repository, "config", "user.email", "worktree-stamp@example.invalid")
    _git(repository, "config", "user.name", "Worktree Stamp Tests")
    # Knowledge object paths exceed the Windows path limit under pytest's
    # temporary directory; the linked worktree shares this setting.
    _git(repository, "config", "core.longpaths", "true")
    (repository / "app" / "__init__.py").write_text("", encoding="utf-8")
    (repository / "app" / "service.py").write_text(SERVICE, encoding="utf-8", newline="\n")
    _commit_all(repository, "source")
    _run(monkeypatch, repository, "init", "--agent", "generic", "--no-skills", "--no-quality-hints")
    _run(
        monkeypatch, repository, "bootstrap", "--src-dir", ".", "--wiki-dir", "docs/llm_wiki",
        "--knowledge-format", "packed-v4-deflate",
    )
    _run(
        monkeypatch, repository, "maintenance", "adopt", "--wiki-dir", "docs/llm_wiki",
        "--src-dir", ".", "--recovery-dir", str(tmp_path / "recovery"),
        "--manifest-format", "indexed-v8",
    )
    _commit_all(repository, "wiki bootstrap")
    with (repository / "app" / "service.py").open("a", encoding="utf-8", newline="\n") as stream:
        stream.write(ADDITION)
    _commit_all(repository, "source change")
    return repository


def _recorded_working_tree(root: Path) -> str:
    knowledge = json.loads(
        (root / "docs" / "llm_wiki" / ".llm-wiki-knowledge.json").read_text(encoding="utf-8")
    )
    return knowledge["store"]["bundle"]["repository"]["working_tree"]


def _sync_commit_and_preview(monkeypatch, capsys, worktree: Path) -> str:
    _run(monkeypatch, worktree, "sync", "--jobs", "1", "--src-dir", ".", "--wiki-dir", "docs/llm_wiki")
    _commit_all(worktree, "wiki sync")
    capsys.readouterr()
    _run(
        monkeypatch, worktree, "sync", "--dry-run", "--jobs", "1",
        "--src-dir", ".", "--wiki-dir", "docs/llm_wiki",
    )
    return capsys.readouterr().out


def _assert_fixpoint(preview: str) -> None:
    assert "(0 changed objects" in preview
    assert "Knowledge index: unchanged" in preview
    assert "Manifest: unchanged" in preview


def test_sync_in_a_linked_worktree_records_clean_and_reaches_a_fixpoint(
    tmp_path, monkeypatch, capsys, git_environment,
):
    repository = _adopted_repository_with_pending_change(monkeypatch, tmp_path)
    worktree = tmp_path / "wt"
    _git(repository, "worktree", "add", "--quiet", "-b", "wt", str(worktree))

    preview = _sync_commit_and_preview(monkeypatch, capsys, worktree)

    assert _recorded_working_tree(worktree) == "clean"
    assert not any((worktree / "docs" / "llm_wiki" / name).exists() for name in LOCK_FILES)
    _assert_fixpoint(preview)


def test_lock_files_kept_in_the_wiki_do_not_make_the_working_tree_dirty(
    tmp_path, monkeypatch, capsys, git_environment,
):
    repository = _adopted_repository_with_pending_change(monkeypatch, tmp_path)
    worktree = tmp_path / "wt"
    _git(repository, "worktree", "add", "--quiet", "-b", "wt", str(worktree))
    # Git still reads this worktree, but its back-pointer no longer names it,
    # so the wiki cannot verify the Git directory and keeps its locks itself.
    admin = Path(_git(worktree, "rev-parse", "--absolute-git-dir"))
    (admin / "gitdir").write_text(f"{tmp_path / 'moved' / '.git'}\n", encoding="utf-8")

    preview = _sync_commit_and_preview(monkeypatch, capsys, worktree)

    assert all((worktree / "docs" / "llm_wiki" / name).exists() for name in LOCK_FILES)
    assert _recorded_working_tree(worktree) == "clean"
    _assert_fixpoint(preview)
