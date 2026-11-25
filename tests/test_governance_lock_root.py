"""The lock root belongs to the wiki's own repository in every Git layout."""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

import pytest

from llm_wiki_cli.services import bootstrap_recovery
from llm_wiki_engine import knowledge_governance as governance
from llm_wiki_engine.knowledge_storage import canonical_bytes

_REQUIRES_GIT = pytest.mark.skipif(
    shutil.which("git") is None,
    reason="Git is required for repository-layout integration coverage",
)
_GIT_ENVIRONMENT = {
    key: value
    for key, value in os.environ.items()
    if not key.startswith("GIT_")
} | {"GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_NOSYSTEM": "1"}


def _git(root: Path, *arguments: str) -> str:
    return subprocess.run(
        ["git", "-C", str(root), *arguments],
        check=True,
        capture_output=True,
        text=True,
        env=_GIT_ENVIRONMENT,
    ).stdout.strip()


def _repository(path: Path, *, commit: bool = False) -> Path:
    path.mkdir(parents=True)
    _git(path, "init", "--quiet")
    _git(path, "config", "user.email", "lock-root@example.invalid")
    _git(path, "config", "user.name", "Lock Root Tests")
    if commit:
        _git(path, "commit", "--quiet", "--allow-empty", "-m", "initial")
    return path


def _wiki(root: Path) -> Path:
    wiki = root / "wiki"
    wiki.mkdir(parents=True)
    return wiki.resolve()


def _linked_worktree(common: Path, worktree: Path, name: str = "linked") -> Path:
    """Write the files Git creates for a linked worktree and return its admin dir."""
    admin = common / "worktrees" / name
    admin.mkdir(parents=True)
    (common / "HEAD").write_text("ref: refs/heads/main\n", encoding="utf-8")
    worktree.mkdir(parents=True, exist_ok=True)
    (worktree / ".git").write_text(f"gitdir: {admin}\n", encoding="utf-8")
    (admin / "HEAD").write_text("ref: refs/heads/linked\n", encoding="utf-8")
    (admin / "commondir").write_text("../..\n", encoding="utf-8")
    (admin / "gitdir").write_text(f"{worktree / '.git'}\n", encoding="utf-8")
    return admin


def test_plain_repository_keeps_its_git_directory(tmp_path):
    root = tmp_path.resolve() / "repository"
    (root / ".git").mkdir(parents=True)
    wiki = _wiki(root)

    assert governance._governance_lock_root(wiki) == root / ".git"
    metadata = governance.repository_metadata(wiki)
    assert (metadata.kind, metadata.worktree_root) == ("directory", root)
    assert metadata.git_dir == metadata.common_dir == root / ".git"


def test_wiki_without_git_is_its_own_lock_root(tmp_path):
    wiki = _wiki(tmp_path / "plain")

    assert governance._governance_lock_root(wiki) == wiki
    assert governance.repository_metadata(wiki).kind == "none"


def test_linked_worktree_uses_its_own_administrative_directory(tmp_path):
    base = tmp_path.resolve()
    common = base / "main" / ".git"
    worktree = base / "linked"
    admin = _linked_worktree(common, worktree)
    wiki = _wiki(worktree / "docs")

    assert governance._governance_lock_root(wiki) == admin
    metadata = governance.repository_metadata(wiki)
    assert metadata.kind == "linked-worktree"
    assert metadata.worktree_root == worktree
    assert metadata.common_dir == common


def test_linked_worktree_inside_an_unrelated_repository_ignores_that_repository(tmp_path):
    base = tmp_path.resolve()
    (base / "outer" / ".git").mkdir(parents=True)
    worktree = base / "outer" / "linked"
    admin = _linked_worktree(base / "source" / ".git", worktree)
    wiki = _wiki(worktree)

    lock_root = governance._governance_lock_root(wiki)

    assert lock_root == admin
    assert not lock_root.is_relative_to(base / "outer")


def test_linked_worktree_inside_its_own_checkout_does_not_share_the_main_lock(tmp_path):
    base = tmp_path.resolve()
    common = base / "main" / ".git"
    worktree = base / "main" / ".claude" / "worktrees" / "agent"
    admin = _linked_worktree(common, worktree, "agent")
    main_wiki = _wiki(base / "main")
    linked_wiki = _wiki(worktree)

    assert governance._governance_lock_root(main_wiki) == common
    assert governance._governance_lock_root(linked_wiki) == admin


def test_relative_worktree_pointers_are_resolved_from_their_own_files(tmp_path):
    base = tmp_path.resolve()
    common = base / "main" / ".git"
    worktree = base / "linked"
    admin = _linked_worktree(common, worktree)
    (worktree / ".git").write_text(
        "gitdir: ../main/.git/worktrees/linked\n", encoding="utf-8"
    )
    (admin / "gitdir").write_text("../../../../linked/.git\n", encoding="utf-8")

    assert governance._governance_lock_root(_wiki(worktree)) == admin


def test_separate_git_directory_is_verified_through_its_worktree_setting(tmp_path):
    base = tmp_path.resolve()
    (base / "super" / ".git").mkdir(parents=True)
    module = base / "super" / ".git" / "modules" / "library"
    module.mkdir(parents=True)
    (module / "HEAD").write_text("ref: refs/heads/main\n", encoding="utf-8")
    (module / "config").write_text(
        "[core]\n\tbare = false\n\tworktree = ../../../library\n", encoding="utf-8"
    )
    checkout = base / "super" / "library"
    checkout.mkdir()
    (checkout / ".git").write_text("gitdir: ../.git/modules/library\n", encoding="utf-8")

    assert governance._governance_lock_root(_wiki(checkout)) == module
    assert governance.repository_metadata(_wiki(checkout / "docs")).kind == "separate-git-dir"


@pytest.mark.parametrize(
    "damage",
    ["absent-target", "wrong-prefix", "two-lines", "copied-worktree", "missing-head", "oversized"],
)
def test_unverified_git_file_is_a_boundary_not_a_reason_to_search_upward(tmp_path, damage):
    base = tmp_path.resolve()
    (base / "outer" / ".git").mkdir(parents=True)
    worktree = base / "outer" / "linked"
    admin = _linked_worktree(base / "source" / ".git", worktree)
    git_file = worktree / ".git"
    if damage == "absent-target":
        git_file.write_text("gitdir: absent\n", encoding="utf-8")
    elif damage == "wrong-prefix":
        git_file.write_text(f"worktree: {admin}\n", encoding="utf-8")
    elif damage == "two-lines":
        git_file.write_text(f"gitdir: {admin}\ngitdir: {base / 'outer' / '.git'}\n", encoding="utf-8")
    elif damage == "copied-worktree":
        # A copied worktree still names the original's metadata, which names the original.
        (admin / "gitdir").write_text(f"{base / 'elsewhere' / '.git'}\n", encoding="utf-8")
    elif damage == "missing-head":
        (admin / "HEAD").unlink()
    else:
        git_file.write_text("gitdir: " + "x" * 9000 + "\n", encoding="utf-8")
    wiki = _wiki(worktree)

    assert governance._governance_lock_root(wiki) == wiki
    metadata = governance.repository_metadata(wiki)
    assert (metadata.kind, metadata.git_dir) == ("unverified", None)


@pytest.mark.skipif(os.name == "nt", reason="creating symbolic links needs a privilege on Windows")
@pytest.mark.parametrize("entry", ["directory-link", "file-link"])
def test_symbolic_git_entry_is_a_boundary(tmp_path, entry):
    base = tmp_path.resolve()
    (base / "outer" / ".git").mkdir(parents=True)
    worktree = base / "outer" / "linked"
    admin = _linked_worktree(base / "source" / ".git", worktree)
    git_file = worktree / ".git"
    if entry == "directory-link":
        git_file.unlink()
        git_file.symlink_to(base / "source" / ".git", target_is_directory=True)
    else:
        real = worktree / "gitfile"
        git_file.rename(real)
        git_file.symlink_to(real)
        (admin / "gitdir").write_text(f"{real}\n", encoding="utf-8")
    wiki = _wiki(worktree)

    assert governance._governance_lock_root(wiki) == wiki


@pytest.mark.skipif(os.name == "nt", reason="creating symbolic links needs a privilege on Windows")
def test_git_file_cannot_send_locks_through_a_symbolic_link(tmp_path):
    base = tmp_path.resolve()
    worktree = base / "linked"
    admin = _linked_worktree(base / "source" / ".git", worktree)
    alias = base / "alias"
    alias.symlink_to(base / "source", target_is_directory=True)
    (worktree / ".git").write_text(
        f"gitdir: {alias / '.git' / 'worktrees' / 'linked'}\n", encoding="utf-8"
    )
    wiki = _wiki(worktree)

    assert governance._governance_lock_root(wiki) == wiki
    assert admin.is_dir()


def test_governance_lock_is_created_inside_the_linked_worktree_metadata(tmp_path):
    base = tmp_path.resolve()
    (base / "outer" / ".git").mkdir(parents=True)
    worktree = base / "outer" / "linked"
    admin = _linked_worktree(base / "source" / ".git", worktree)
    wiki = _wiki(worktree)

    with governance.governance_lock(wiki):
        assert (admin / governance.GOVERNANCE_LOCK_FILENAME).is_file()

    assert list((base / "outer" / ".git").iterdir()) == []
    assert list(wiki.iterdir()) == []


@_REQUIRES_GIT
def test_git_created_worktree_inside_an_unrelated_repository(tmp_path):
    base = tmp_path.resolve()
    _repository(base / "outer")
    source = _repository(base / "source", commit=True)
    linked = base / "outer" / "linked"
    _git(source, "worktree", "add", "--quiet", "--detach", str(linked))
    wiki = _wiki(linked)

    lock_root = governance._governance_lock_root(wiki)

    assert lock_root == Path(_git(linked, "rev-parse", "--absolute-git-dir")).resolve()
    assert lock_root.is_relative_to(source / ".git")
    assert governance._governance_lock_root(_wiki(source)) == source / ".git"


@_REQUIRES_GIT
def test_git_created_worktree_inside_its_own_checkout(tmp_path):
    base = tmp_path.resolve()
    main = _repository(base / "main", commit=True)
    linked = main / ".claude" / "worktrees" / "agent"
    _git(main, "worktree", "add", "--quiet", "--detach", str(linked))

    lock_root = governance._governance_lock_root(_wiki(linked))

    assert lock_root == Path(_git(linked, "rev-parse", "--absolute-git-dir")).resolve()
    assert lock_root != main / ".git"
    assert governance.repository_metadata(_wiki(linked / "docs")).common_dir == main / ".git"


@_REQUIRES_GIT
def test_git_created_submodule_uses_its_own_git_directory(tmp_path):
    base = tmp_path.resolve()
    library = _repository(base / "library", commit=True)
    parent = _repository(base / "parent", commit=True)
    _git(
        parent, "-c", "protocol.file.allow=always",
        "submodule", "--quiet", "add", str(library), "vendor/library",
    )
    checkout = parent / "vendor" / "library"

    lock_root = governance._governance_lock_root(_wiki(checkout))

    assert lock_root == Path(_git(checkout, "rev-parse", "--absolute-git-dir")).resolve()
    assert lock_root != parent / ".git"


def _pending_record(path: Path, wiki: Path) -> None:
    path.parent.mkdir(parents=True)
    path.write_bytes(canonical_bytes({
        "schema_version": bootstrap_recovery.SCHEMA,
        "wiki_root": str(wiki),
        "operation_id": "0" * 32,
        "status": "writing",
        "metadata_hash": "sha256:" + "0" * 64,
        "directories": [],
    }))


def test_bootstrap_record_is_kept_beside_the_linked_worktree_lock(tmp_path):
    base = tmp_path.resolve()
    worktree = base / "main" / ".claude" / "worktrees" / "agent"
    admin = _linked_worktree(base / "main" / ".git", worktree, "agent")
    wiki = _wiki(worktree)

    assert bootstrap_recovery._record_path(wiki).is_relative_to(admin / "bootstrap-recovery")


def test_interrupted_bootstrap_recorded_at_the_earlier_location_stays_pending(tmp_path, monkeypatch):
    base = tmp_path.resolve()
    common = base / "main" / ".git"
    worktree = base / "main" / ".claude" / "worktrees" / "agent"
    admin = _linked_worktree(common, worktree, "agent")
    wiki = _wiki(worktree)
    current = bootstrap_recovery._record_path(wiki)
    earlier = common / current.relative_to(admin)
    _pending_record(earlier, wiki)

    assert bootstrap_recovery._record_path(wiki) == earlier
    assert bootstrap_recovery.pending_bootstrap(wiki)

    record = bootstrap_recovery._load_record(wiki)
    assert record is not None
    bootstrap_recovery._complete(wiki, record)

    assert not bootstrap_recovery.pending_bootstrap(wiki)
    assert bootstrap_recovery._record_path(wiki) == current
    assert not current.exists()


def test_earlier_record_in_an_unrelated_enclosing_repository_is_never_consulted(tmp_path):
    base = tmp_path.resolve()
    foreign = base / "outer" / ".git"
    foreign.mkdir(parents=True)
    worktree = base / "outer" / "linked"
    admin = _linked_worktree(base / "source" / ".git", worktree)
    wiki = _wiki(worktree)
    current = bootstrap_recovery._record_path(wiki)
    _pending_record(foreign / current.relative_to(admin), wiki)

    assert bootstrap_recovery._record_path(wiki) == current
    assert not bootstrap_recovery.pending_bootstrap(wiki)
