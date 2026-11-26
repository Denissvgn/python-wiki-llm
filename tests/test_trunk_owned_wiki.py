"""Trunk ownership keeps generated wiki state off feature branches."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from llm_wiki_cli import cli
from llm_wiki_cli.services import team

pytestmark = pytest.mark.skipif(shutil.which("git") is None, reason="git is not available")

WIKI = "docs/llm_wiki"
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


@pytest.fixture(autouse=True)
def git_environment(monkeypatch, tmp_path):
    for key in list(os.environ):
        if key.startswith("GIT_"):
            monkeypatch.delenv(key)
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", os.devnull)
    monkeypatch.setenv("GIT_CONFIG_NOSYSTEM", "1")
    monkeypatch.setenv("LLM_WIKI_CACHE_DIR", str(tmp_path / "cache"))


def _git(root: Path, *arguments: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(root), *arguments], capture_output=True, text=True
    )
    assert result.returncode == 0, f"git {' '.join(arguments)}: {result.stderr}"
    return result.stdout.strip()


def _run(monkeypatch, root: Path, *arguments: str) -> int:
    monkeypatch.chdir(root)
    monkeypatch.setattr(sys, "argv", ["llm-wiki", *arguments])
    try:
        cli.main()
    except SystemExit as exc:
        return exc.code if isinstance(exc.code, int) else (0 if exc.code is None else 1)
    return 0


def _commit_all(root: Path, message: str) -> None:
    _git(root, "add", "-A")
    _git(root, "commit", "--quiet", "-m", message)


def _append_service(root: Path) -> None:
    with (root / "app" / "service.py").open("a", encoding="utf-8", newline="\n") as stream:
        stream.write(ADDITION)


@pytest.fixture
def repository(monkeypatch, tmp_path) -> Path:
    """A committed wiki on main with trunk ownership and one writer branch."""
    root = tmp_path / "repo"
    (root / "app").mkdir(parents=True)
    _git(root, "init", "--quiet", "-b", "main")
    _git(root, "config", "user.email", "trunk-owned@example.invalid")
    _git(root, "config", "user.name", "Trunk Owned Tests")
    _git(root, "config", "core.longpaths", "true")
    (root / "app" / "__init__.py").write_text("", encoding="utf-8")
    (root / "app" / "service.py").write_text(SERVICE, encoding="utf-8", newline="\n")
    _commit_all(root, "source")
    assert _run(monkeypatch, root, "init", "--agent", "generic", "--no-skills", "--no-quality-hints") == 0
    assert _run(monkeypatch, root, "bootstrap", "--src-dir", ".", "--wiki-dir", WIKI) == 0
    assert _run(
        monkeypatch, root, "team", "init", "--wiki-dir", WIKI,
        "--ownership", "trunk", "--writer-branch", "llm-wiki/refresh",
    ) == 0
    _commit_all(root, "wiki bootstrap")
    return root


def _config(**ownership) -> dict:
    config = team.default_team_config()
    config["ownership"] = ownership
    return config


def test_missing_ownership_keeps_per_branch_writes():
    ownership = team.wiki_ownership(team.validate_team_config(team.default_team_config()))

    assert ownership.mode == "branch"
    assert ownership.may_write("feature/x")
    assert ownership.may_write(None)


def test_trunk_ownership_admits_only_the_trunk_and_writer_branches():
    ownership = team.wiki_ownership(
        team.validate_team_config(
            _config(mode="trunk", trunk="develop", writer_branches=["llm-wiki/refresh"])
        )
    )

    assert ownership.may_write("develop")
    assert ownership.may_write("llm-wiki/refresh")
    assert not ownership.may_write("main")
    assert not ownership.may_write(None)
    assert ownership.is_authored("guides/setup.md")
    assert not ownership.is_authored("guides-old/setup.md")
    assert not ownership.is_authored("index.md")


@pytest.mark.parametrize(
    "ownership, message",
    [
        ({"mode": "shared"}, "ownership.mode"),
        ({"mode": "trunk", "trunk": "--force"}, "ownership.trunk"),
        ({"mode": "trunk", "writer_branches": ["a..b"]}, "ownership.writer_branches"),
        ({"mode": "trunk", "authored_paths": ["../outside"]}, "ownership.authored_paths"),
        ({"mode": "trunk", "owner": "me"}, "unknown key"),
    ],
)
def test_invalid_ownership_is_rejected(ownership, message):
    with pytest.raises(team.TeamConfigError, match=message):
        team.validate_team_config(_config(**ownership))


def test_team_init_records_trunk_ownership(repository):
    recorded = json.loads((repository / ".llm-wiki" / "team.json").read_text(encoding="utf-8"))

    assert recorded["ownership"] == {
        "mode": "trunk",
        "trunk": "main",
        "writer_branches": ["llm-wiki/refresh"],
    }


def test_owning_sync_is_refused_on_a_feature_branch(monkeypatch, capsys, repository):
    _git(repository, "switch", "--quiet", "-c", "feature/invoices")
    _append_service(repository)
    _commit_all(repository, "source change")
    capsys.readouterr()

    code = _run(monkeypatch, repository, "sync", "--src-dir", ".", "--wiki-dir", WIKI)

    captured = capsys.readouterr()
    assert code == 2
    assert "trunk-owned" in captured.err
    assert "'feature/invoices'" in captured.err
    assert _git(repository, "status", "--porcelain") == ""


def test_dry_run_stays_available_on_a_feature_branch(monkeypatch, capsys, repository):
    _git(repository, "switch", "--quiet", "-c", "feature/invoices")
    _append_service(repository)
    _commit_all(repository, "source change")

    code = _run(monkeypatch, repository, "sync", "--dry-run", "--src-dir", ".", "--wiki-dir", WIKI)

    assert code == 0
    assert _git(repository, "status", "--porcelain") == ""


def test_owning_sync_is_refused_on_a_detached_head(monkeypatch, capsys, repository):
    _git(repository, "switch", "--quiet", "--detach")
    capsys.readouterr()

    code = _run(monkeypatch, repository, "sync", "--src-dir", ".", "--wiki-dir", WIKI)

    assert code == 2
    assert "detached HEAD" in capsys.readouterr().err


@pytest.mark.parametrize("branch", ["main", "llm-wiki/refresh"])
def test_writer_branches_sync_normally(monkeypatch, repository, branch):
    if branch != "main":
        _git(repository, "switch", "--quiet", "-c", branch)
    _append_service(repository)
    _commit_all(repository, "source change")

    code = _run(monkeypatch, repository, "sync", "--src-dir", ".", "--wiki-dir", WIKI)

    assert code == 0
    assert _git(repository, "status", "--porcelain") != ""


def test_an_unreadable_policy_refuses_the_owning_sync(monkeypatch, capsys, repository):
    (repository / ".llm-wiki" / "team.json").write_text("{", encoding="utf-8")
    capsys.readouterr()

    code = _run(monkeypatch, repository, "sync", "--src-dir", ".", "--wiki-dir", WIKI)

    assert code == 2
    assert "ownership is unknown" in capsys.readouterr().err


def _branch_check(monkeypatch, capsys, root: Path, *arguments: str) -> tuple[int, dict]:
    capsys.readouterr()
    code = _run(
        monkeypatch, root, "knowledge", "git-check", "--wiki-dir", WIKI, "--base", "main", *arguments
    )
    return code, json.loads(capsys.readouterr().out)


def test_branch_check_passes_when_only_source_changed(monkeypatch, capsys, repository):
    _git(repository, "switch", "--quiet", "-c", "feature/invoices")
    _append_service(repository)
    _commit_all(repository, "source change")

    code, result = _branch_check(monkeypatch, capsys, repository)

    assert code == 0
    assert result["ok"] is True
    assert result["checked"] is True
    assert result["reason"] == "generated-paths-unchanged"
    assert result["branch"] == "feature/invoices"


def test_branch_check_fails_when_a_generated_path_changed(monkeypatch, capsys, repository):
    _git(repository, "switch", "--quiet", "-c", "feature/invoices")
    index = repository / "docs" / "llm_wiki" / "index.md"
    index.write_text(index.read_text(encoding="utf-8") + "\nhand edit\n", encoding="utf-8")
    guide = repository / "docs" / "llm_wiki" / "guides" / "setup.md"
    guide.parent.mkdir(exist_ok=True)
    guide.write_text("# Setup\n", encoding="utf-8")
    _commit_all(repository, "wiki edits")

    code, result = _branch_check(monkeypatch, capsys, repository)

    assert code == 1
    assert result["ok"] is False
    assert result["reason"] == "generated-paths-changed"
    assert result["generated_samples"] == ["docs/llm_wiki/index.md"]
    assert result["authored_changes"] == 1


def test_branch_check_admits_the_named_writer_branch(monkeypatch, capsys, repository):
    _git(repository, "switch", "--quiet", "-c", "work")
    index = repository / "docs" / "llm_wiki" / "index.md"
    index.write_text(index.read_text(encoding="utf-8") + "\nrefresh\n", encoding="utf-8")
    _commit_all(repository, "refresh")
    _git(repository, "switch", "--quiet", "--detach")

    code, result = _branch_check(monkeypatch, capsys, repository, "--branch", "llm-wiki/refresh")

    assert code == 0
    assert result["reason"] == "writer-branch"
    assert result["checked"] is False


def test_branch_check_reports_an_unresolved_base(monkeypatch, capsys, repository):
    _git(repository, "switch", "--quiet", "-c", "feature/invoices")
    capsys.readouterr()

    code = _run(
        monkeypatch, repository, "knowledge", "git-check", "--wiki-dir", WIKI, "--base", "no-such-ref"
    )

    assert code == 1
    assert json.loads(capsys.readouterr().out)["reason"] == "base-unresolved"


def test_branch_check_does_not_apply_without_trunk_ownership(monkeypatch, capsys, repository):
    (repository / ".llm-wiki" / "team.json").write_text(
        json.dumps(team.default_team_config()), encoding="utf-8"
    )

    code, result = _branch_check(monkeypatch, capsys, repository)

    assert code == 0
    assert result["reason"] == "branch-ownership"


def test_strict_lint_reports_a_stale_manifest_as_pending_on_a_feature_branch(
    monkeypatch, capsys, repository
):
    _git(repository, "switch", "--quiet", "-c", "feature/invoices")
    _append_service(repository)
    _commit_all(repository, "source change")
    capsys.readouterr()

    pending = _run(monkeypatch, repository, "lint", "--strict", "--src-dir", ".", "--wiki-dir", WIKI)
    pending_output = capsys.readouterr().out
    required = _run(
        monkeypatch, repository, "lint", "--strict", "--require-fresh", "--src-dir", ".", "--wiki-dir", WIKI
    )
    required_output = capsys.readouterr().out

    assert pending == 0
    assert "awaits the trunk refresh" in pending_output
    assert required == 1
    assert "Sync manifest is stale" in required_output


def test_strict_lint_still_fails_a_stale_manifest_on_the_trunk(monkeypatch, capsys, repository):
    _append_service(repository)
    _commit_all(repository, "source change")
    capsys.readouterr()

    code = _run(monkeypatch, repository, "lint", "--strict", "--src-dir", ".", "--wiki-dir", WIKI)

    assert code == 1
    assert "Sync manifest is stale" in capsys.readouterr().out
