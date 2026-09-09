"""Retired Git hooks are recognized and removed without enabling installation."""

from __future__ import annotations

import subprocess
from pathlib import Path
from types import SimpleNamespace

import pytest

from llm_wiki_cli import cli
from llm_wiki_cli.commands import hook_cmd, init_cmd
from llm_wiki_cli.services import legacy_hooks

FIXTURES = Path(__file__).parent / "fixtures" / "legacy_hooks"


class TestLegacyHookOwnership:
    @pytest.mark.parametrize(
        ("name", "content"),
        [
            ("post-commit", "#!/bin/sh\n# LLM Wiki old hook\n"),
            (
                "post-commit",
                hook_cmd._build_ide_post_commit("docs/llm_wiki"),
            ),
            (
                "pre-commit",
                hook_cmd._build_validation_pre_commit("docs/llm_wiki"),
            ),
        ],
    )
    def test_crlf_managed_hook_is_owned(self, name: str, content: str):
        crlf = content.replace("\n", "\r\n")

        assert hook_cmd.is_managed_hook_content(name, crlf)

    @pytest.mark.parametrize(
        "content",
        [
            hook_cmd._build_ide_post_commit("docs/llm_wiki").replace("\n", "\r"),
            hook_cmd._build_ide_post_commit("docs/llm_wiki").replace("\n", "\r\n")
            + "echo user-tail\r\n",
        ],
    )
    def test_non_crlf_or_modified_managed_hook_is_not_owned(self, content: str):
        assert not hook_cmd.is_managed_hook_content("post-commit", content)

    @pytest.mark.parametrize("agent", ["custom-agent", "$(id)"])
    def test_legacy_hook_with_non_generated_agent_is_not_owned(
        self,
        tmp_project,
        agent: str,
    ):
        content = hook_cmd._legacy_auto_sync_post_commit(agent, "docs/llm_wiki")

        assert not hook_cmd.is_managed_hook_content("post-commit", content)

    @pytest.mark.parametrize(
        "content",
        [
            hook_cmd._build_ide_post_commit("../../outside"),
            hook_cmd._build_ide_post_commit(
                "docs/llm_wiki",
                source_selection="../../outside-selection.json",
            ),
            hook_cmd._legacy_auto_sync_post_commit("claude", "../../outside"),
        ],
    )
    def test_parameter_edited_hook_outside_project_is_not_owned(
        self,
        tmp_project,
        content: str,
    ):
        assert not hook_cmd.is_managed_hook_content("post-commit", content)

    @pytest.mark.parametrize(
        "content",
        [
            hook_cmd._build_validation_pre_commit("../../outside"),
            hook_cmd._build_validation_pre_commit(
                "docs/llm_wiki",
                source_selection="../../outside-selection.json",
            ),
        ],
    )
    def test_parameter_edited_pre_commit_outside_project_is_not_owned(
        self,
        tmp_project,
        content: str,
    ):
        assert not hook_cmd.is_managed_hook_content("pre-commit", content)


def _write_hook(name: str, content: str | bytes, directory: Path | None = None) -> Path:
    target = (Path(".git/hooks") if directory is None else directory) / name
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(content.encode("utf-8") if isinstance(content, str) else content)
    return target


def test_install_hook_command_is_removed_and_legacy_python_entrypoint_is_inert(
    tmp_project, capsys
):
    parser = cli._build_parser()
    assert "install-hook" not in parser.format_help()
    with pytest.raises(SystemExit) as caught:
        parser.parse_args(["install-hook", "--force", "--enable-validation"])
    assert caught.value.code == 2
    before = sorted(path.relative_to(tmp_project) for path in tmp_project.rglob("*"))
    with pytest.raises(SystemExit) as caught:
        hook_cmd.run(SimpleNamespace(force=True, enable_validation=True))
    assert caught.value.code == 2
    assert "installation has been removed" in capsys.readouterr().err
    assert (
        sorted(path.relative_to(tmp_project) for path in tmp_project.rglob("*"))
        == before
    )


def test_init_does_not_create_git_hooks(tmp_project):
    hooks = Path(".git/hooks")
    before = (
        {path.name: path.read_bytes() for path in hooks.iterdir() if path.is_file()}
        if hooks.exists()
        else {}
    )
    init_cmd.run(SimpleNamespace(agent="generic", wiki_dir="wiki", no_skills=True))
    after = (
        {path.name: path.read_bytes() for path in hooks.iterdir() if path.is_file()}
        if hooks.exists()
        else {}
    )
    assert after == before


@pytest.mark.parametrize("newline", ["\n", "\r\n"])
@pytest.mark.parametrize(
    "name,content",
    [
        (
            "post-commit",
            legacy_hooks._build_ide_post_commit(
                "my docs/wiki", source_selection="config/source scope.json"
            ),
        ),
        (
            "post-commit",
            legacy_hooks._legacy_auto_sync_post_commit("claude", "docs/llm_wiki"),
        ),
        ("post-commit", legacy_hooks._legacy_ide_post_commit("docs/llm_wiki")),
        ("pre-commit", legacy_hooks._build_validation_pre_commit("docs/llm_wiki")),
        *[
            ("pre-push", path.read_text(encoding="utf-8"))
            for path in sorted(FIXTURES.glob("*.sh"))
        ],
    ],
)
def test_cleanup_removes_historical_hooks_and_is_idempotent(
    tmp_project, name, content, newline
):
    hook = _write_hook(name, content.replace("\n", newline))
    before = hook.read_bytes()
    plan = legacy_hooks.inspect_legacy_hooks()
    assert legacy_hooks.remove_legacy_hooks(plan=plan, dry_run=True) == 1
    assert hook.read_bytes() == before
    assert legacy_hooks.remove_legacy_hooks(plan=plan) == 1
    assert not hook.exists()
    assert legacy_hooks.remove_legacy_hooks() == 0


def test_cleanup_preserves_custom_and_edited_hooks(tmp_project):
    contents = {
        "post-commit": legacy_hooks._build_ide_post_commit("wiki") + "echo custom\n",
        "pre-commit": '#!/bin/sh\necho "LLM Wiki is mentioned here"\n',
        "pre-push": "#!/bin/sh\necho custom\n",
    }
    for name, text in contents.items():
        _write_hook(name, text)
    assert legacy_hooks.remove_legacy_hooks() == 0
    for name, text in contents.items():
        assert Path(".git/hooks", name).read_text(encoding="utf-8") == text


def test_cleanup_rechecks_the_whole_plan_before_removing_any_hook(tmp_project):
    first = _write_hook("post-commit", legacy_hooks._build_ide_post_commit("wiki"))
    second = _write_hook(
        "pre-commit", legacy_hooks._build_validation_pre_commit("wiki")
    )
    plan = legacy_hooks.inspect_legacy_hooks()
    custom = b"#!/bin/sh\necho replaced\n"
    second.write_bytes(custom)
    with pytest.raises(
        legacy_hooks.LegacyHookError, match="changed after cleanup preflight"
    ):
        legacy_hooks.remove_legacy_hooks(plan=plan)
    assert first.exists()
    assert second.read_bytes() == custom


def test_cleanup_guard_rejects_a_hook_replaced_after_the_plan_recheck(
    tmp_project, monkeypatch
):
    hook = _write_hook("post-commit", legacy_hooks._build_ide_post_commit("wiki"))
    plan = legacy_hooks.inspect_legacy_hooks()
    remove = legacy_hooks.unlink_guarded_bytes
    replacement = b"#!/bin/sh\necho new owner\n"

    def replace_then_remove(path, **kwargs):
        path.write_bytes(replacement)
        return remove(path, **kwargs)

    monkeypatch.setattr(legacy_hooks, "unlink_guarded_bytes", replace_then_remove)
    with pytest.raises(legacy_hooks.LegacyHookError, match="guarded removal"):
        legacy_hooks.remove_legacy_hooks(plan=plan)
    assert hook.read_bytes() == replacement


def test_cleanup_refuses_redirected_hook_paths(tmp_project):
    outside = tmp_project.parent / "outside-hook"
    outside.write_bytes(b"#!/bin/sh\n# LLM Wiki old hook\n")
    hooks = Path(".git/hooks")
    hooks.mkdir(parents=True, exist_ok=True)
    try:
        (hooks / "post-commit").symlink_to(outside)
    except OSError:
        pytest.skip("Symlinks unavailable")
    with pytest.raises(legacy_hooks.LegacyHookError, match="unsafe component"):
        legacy_hooks.remove_legacy_hooks()
    assert outside.read_bytes() == b"#!/bin/sh\n# LLM Wiki old hook\n"


def test_cleanup_never_creates_a_hooks_directory(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    assert legacy_hooks.remove_legacy_hooks() == 0
    assert not Path(".git").exists()
    Path(".git").mkdir()
    assert legacy_hooks.remove_legacy_hooks() == 0
    assert not Path(".git/hooks").exists()


def _git(root: Path, *arguments: str) -> str:
    return subprocess.check_output(
        [
            "git",
            "-C",
            str(root),
            "-c",
            f"core.hooksPath={root / 'disabled-test-hooks'}",
            *arguments,
        ],
        text=True,
    ).strip()


def test_cleanup_covers_linked_worktrees_and_repository_local_hooks_path(
    tmp_path, monkeypatch
):
    main = tmp_path / "main"
    main.mkdir()
    _git(main, "init")
    _git(
        main,
        "-c",
        "user.name=Test",
        "-c",
        "user.email=test@example.test",
        "commit",
        "--allow-empty",
        "-m",
        "initial",
    )
    worktree = tmp_path / "worktree"
    _git(main, "worktree", "add", "-b", "linked", str(worktree))
    common_hook = _write_hook(
        "post-commit", legacy_hooks._build_ide_post_commit("wiki"), main / ".git/hooks"
    )
    _git(worktree, "config", "core.hooksPath", ".local hooks")
    local_hook = _write_hook(
        "pre-commit",
        legacy_hooks._build_validation_pre_commit("wiki"),
        worktree / ".local hooks",
    )
    monkeypatch.chdir(worktree)
    assert legacy_hooks.remove_legacy_hooks() == 2
    assert not common_hook.exists()
    assert not local_hook.exists()


def test_cleanup_preserves_external_custom_hooks_path(tmp_path, monkeypatch):
    project = tmp_path / "project"
    project.mkdir()
    _git(project, "init")
    external = tmp_path / "external-hooks"
    hook = _write_hook(
        "post-commit", legacy_hooks._build_ide_post_commit("wiki"), external
    )
    _git(project, "config", "core.hooksPath", str(external))
    monkeypatch.chdir(project)
    assert legacy_hooks.remove_legacy_hooks() == 0
    assert hook.exists()


def test_read_only_status_reports_legacy_hooks_without_removing_them(tmp_project):
    from llm_wiki_cli.services.mcp_server import _installed_hooks

    hook = _write_hook("post-commit", legacy_hooks._build_ide_post_commit("wiki"))
    original = hook.read_bytes()
    assert _installed_hooks() == ["post-commit"]
    assert hook.read_bytes() == original
    hook.write_bytes(original + b"echo custom\n")
    assert _installed_hooks() == []
    assert hook.read_bytes() == original + b"echo custom\n"


def test_default_git_hook_cleanup_does_not_require_git_executable(
    tmp_project, monkeypatch
):
    hook = _write_hook("post-commit", legacy_hooks._build_ide_post_commit("wiki"))
    Path(".git/HEAD").write_text("ref: refs/heads/main\n", encoding="utf-8")

    def missing_git(*args, **kwargs):
        raise FileNotFoundError("git unavailable")

    monkeypatch.setattr(legacy_hooks.subprocess, "run", missing_git)
    assert legacy_hooks.remove_legacy_hooks() == 1
    assert not hook.exists()
