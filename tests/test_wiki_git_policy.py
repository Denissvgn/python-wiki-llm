"""Git-native policy tests for wiki version-control handoff."""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

import pytest

from llm_wiki_cli.services import wiki_git_policy
from llm_wiki_cli.services.wiki_git_policy import (
    WikiGitDisposition,
    classify_wiki_git_policy,
)

_REQUIRES_GIT = pytest.mark.skipif(
    shutil.which("git") is None,
    reason="Git is required for repository-policy integration coverage",
)


def _git(root: Path, *arguments: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(root), *arguments],
        check=True,
        capture_output=True,
        text=True,
    )


def _repository(path: Path) -> Path:
    path.mkdir()
    _git(path, "init", "--quiet")
    _git(path, "config", "user.email", "wiki-policy@example.invalid")
    _git(path, "config", "user.name", "Wiki Policy Tests")
    return path


@_REQUIRES_GIT
def test_absent_wiki_is_included_when_no_rule_matches(tmp_path: Path):
    repository = _repository(tmp_path / "repository")

    policy = classify_wiki_git_policy("docs/llm_wiki", cwd=repository)

    assert policy.disposition is WikiGitDisposition.INCLUDED
    assert policy.reason == "included"
    assert policy.repository_root == repository.resolve()
    assert policy.wiki_path == "docs/llm_wiki"
    assert policy.allows_commit_guidance is True


@_REQUIRES_GIT
@pytest.mark.parametrize(
    ("ignore_file", "contents"),
    [
        (".gitignore", "docs/llm_wiki/\n"),
        ("docs/.gitignore", "llm_wiki/\n"),
    ],
)
def test_root_and_nested_rules_ignore_an_absent_wiki(
    tmp_path: Path,
    ignore_file: str,
    contents: str,
):
    repository = _repository(tmp_path / "repository")
    destination = repository / ignore_file
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(contents, encoding="utf-8")

    policy = classify_wiki_git_policy("docs/llm_wiki", cwd=repository)

    assert policy.disposition is WikiGitDisposition.IGNORED
    assert policy.reason == "ignored"
    assert policy.allows_commit_guidance is False


@_REQUIRES_GIT
def test_final_negation_is_honored(tmp_path: Path):
    repository = _repository(tmp_path / "repository")
    (repository / ".gitignore").write_text(
        "docs/llm_wiki/\n"
        "!docs/llm_wiki/\n"
        "!docs/llm_wiki/index.md\n",
        encoding="utf-8",
    )

    policy = classify_wiki_git_policy("docs/llm_wiki", cwd=repository)

    assert policy.disposition is WikiGitDisposition.INCLUDED


@_REQUIRES_GIT
def test_repository_info_exclude_is_authoritative(tmp_path: Path):
    repository = _repository(tmp_path / "repository")
    (repository / ".git" / "info" / "exclude").write_text(
        "docs/llm_wiki/\n",
        encoding="utf-8",
    )

    policy = classify_wiki_git_policy("docs/llm_wiki", cwd=repository)

    assert policy.disposition is WikiGitDisposition.IGNORED


@_REQUIRES_GIT
def test_configured_global_excludes_are_honored(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    repository = _repository(tmp_path / "repository")
    excludes = tmp_path / "global-excludes"
    # Only the canonical child matches; the directory probe itself is included.
    excludes.write_text("index.md\n", encoding="utf-8")
    global_config = tmp_path / "global.gitconfig"
    subprocess.run(
        [
            "git",
            "config",
            "--file",
            str(global_config),
            "core.excludesFile",
            str(excludes),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", str(global_config))

    policy = classify_wiki_git_policy("docs/llm_wiki", cwd=repository)

    assert policy.disposition is WikiGitDisposition.IGNORED


@_REQUIRES_GIT
def test_no_index_detects_a_tracked_path_covered_by_a_new_ignore_rule(
    tmp_path: Path,
):
    repository = _repository(tmp_path / "repository")
    wiki = repository / "docs" / "llm_wiki"
    wiki.mkdir(parents=True)
    (wiki / "index.md").write_text("# Wiki\n", encoding="utf-8")
    _git(repository, "add", "docs/llm_wiki/index.md")
    (repository / ".gitignore").write_text(
        "docs/llm_wiki/\n",
        encoding="utf-8",
    )

    policy = classify_wiki_git_policy(wiki, cwd=repository)

    assert policy.disposition is WikiGitDisposition.IGNORED


@_REQUIRES_GIT
@pytest.mark.parametrize("wiki_dir", ["docs/wiki [prod]", "-wiki", ":(glob)wiki"])
def test_literal_path_handling_covers_spaces_and_pathspec_like_names(
    tmp_path: Path,
    wiki_dir: str,
):
    repository = _repository(tmp_path / "repository")
    (repository / ".gitignore").write_text(
        "docs/**\n-wiki/\n:(glob)wiki/\n",
        encoding="utf-8",
    )

    policy = classify_wiki_git_policy(wiki_dir, cwd=repository)

    assert policy.disposition is WikiGitDisposition.IGNORED
    assert policy.wiki_path == Path(wiki_dir).as_posix()


@_REQUIRES_GIT
def test_repository_redirection_environment_is_discarded(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    repository = _repository(tmp_path / "repository")
    hostile = _repository(tmp_path / "hostile")
    (repository / ".gitignore").write_text(
        "docs/llm_wiki/\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("GIT_DIR", str(hostile / ".git"))
    monkeypatch.setenv("GIT_WORK_TREE", str(hostile))
    monkeypatch.setenv("GIT_INDEX_FILE", str(hostile / ".git" / "index"))
    monkeypatch.setenv("GIT_CONFIG_COUNT", "1")
    monkeypatch.setenv("GIT_CONFIG_KEY_0", "core.excludesFile")
    monkeypatch.setenv("GIT_CONFIG_VALUE_0", os.devnull)

    policy = classify_wiki_git_policy("docs/llm_wiki", cwd=repository)

    assert policy.disposition is WikiGitDisposition.IGNORED
    assert policy.repository_root == repository.resolve()


@_REQUIRES_GIT
def test_linked_worktree_uses_its_own_top_level(tmp_path: Path):
    repository = _repository(tmp_path / "repository")
    (repository / "README.md").write_text("# Repository\n", encoding="utf-8")
    _git(repository, "add", "README.md")
    _git(repository, "commit", "--quiet", "-m", "initial")
    worktree = tmp_path / "linked-worktree"
    _git(
        repository,
        "worktree",
        "add",
        "--quiet",
        "-b",
        "wiki-policy-worktree",
        str(worktree),
    )
    (worktree / ".gitignore").write_text("docs/llm_wiki/\n", encoding="utf-8")

    policy = classify_wiki_git_policy("docs/llm_wiki", cwd=worktree)

    assert policy.disposition is WikiGitDisposition.IGNORED
    assert policy.repository_root == worktree.resolve()


@_REQUIRES_GIT
def test_non_repository_and_outside_path_fail_closed(tmp_path: Path):
    non_repository = tmp_path / "plain"
    non_repository.mkdir()

    non_repository_policy = classify_wiki_git_policy(
        "docs/llm_wiki",
        cwd=non_repository,
    )

    assert non_repository_policy.disposition is WikiGitDisposition.INDETERMINATE
    assert non_repository_policy.reason == "not-repository"

    repository = _repository(tmp_path / "repository")
    outside_policy = classify_wiki_git_policy(tmp_path / "outside", cwd=repository)

    assert outside_policy.disposition is WikiGitDisposition.INDETERMINATE
    assert outside_policy.reason == "outside-repository"
    assert outside_policy.allows_commit_guidance is False


@pytest.mark.parametrize(
    ("error", "reason"),
    [
        (FileNotFoundError("git"), "git-unavailable"),
        (subprocess.TimeoutExpired(["git"], timeout=1), "git-timeout"),
        (OSError("cannot execute"), "git-error"),
    ],
)
def test_git_execution_failures_are_indeterminate(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    error: Exception,
    reason: str,
):
    def fail_git(*_args: object, **_kwargs: object) -> None:
        raise error

    monkeypatch.setattr(wiki_git_policy.subprocess, "run", fail_git)

    policy = classify_wiki_git_policy("docs/llm_wiki", cwd=tmp_path)

    assert policy.disposition is WikiGitDisposition.INDETERMINATE
    assert policy.reason == reason


def test_unexpected_check_ignore_status_fails_closed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    calls: list[tuple[list[str], dict[str, object]]] = []

    def fake_run(command: list[str], **kwargs: object):
        calls.append((command, kwargs))
        if "rev-parse" in command:
            return subprocess.CompletedProcess(command, 0, f"{tmp_path}\n", "")
        return subprocess.CompletedProcess(command, 2, "", "fatal")

    monkeypatch.setattr(wiki_git_policy.subprocess, "run", fake_run)
    monkeypatch.setenv("GIT_DIR", str(tmp_path / "hostile"))

    policy = classify_wiki_git_policy("docs/llm_wiki", cwd=tmp_path, timeout=7)

    assert policy.disposition is WikiGitDisposition.INDETERMINATE
    assert policy.reason == "git-error"
    assert len(calls) == 2
    assert calls[0][0][-2:] == ["rev-parse", "--show-toplevel"]
    assert calls[1][0][-5:] == [
        "check-ignore",
        "--no-index",
        "--",
        "docs/llm_wiki/",
        "docs/llm_wiki/index.md",
    ]
    for _command, kwargs in calls:
        assert kwargs["shell"] is False
        assert kwargs["timeout"] == 7
        environment = kwargs["env"]
        assert isinstance(environment, dict)
        assert "GIT_DIR" not in environment
        assert environment["GIT_OPTIONAL_LOCKS"] == "0"
