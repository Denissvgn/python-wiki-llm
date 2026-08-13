"""Tests for commands/hook_cmd.py"""

import json
import shutil
import types
from pathlib import Path

import pytest

from llm_wiki_cli.commands import hook_cmd
from llm_wiki_cli.config import read_config, write_config
from llm_wiki_cli.services.source_selection import SOURCE_SELECTION_SCHEMA_VERSION


def _make_args(**kwargs):
    defaults = {
        "wiki_dir": "docs/llm_wiki",
        "agent": None,
        "force": False,
        "enable_validation": False,
    }
    defaults.update(kwargs)
    return types.SimpleNamespace(**defaults)


def _write_agent_config(wiki_dir: str, agent: str):
    git_config = Path(".git") / ".llm-wiki-agent"
    git_config.parent.mkdir(parents=True, exist_ok=True)
    git_config.write_text(agent)


class TestHookReadsAgentConfig:
    def test_hook_from_cli_agent_config_generates_prompt(self, tmp_project):
        """CLI-agent config still installs a prompt hook, not headless sync."""
        _write_agent_config("docs/llm_wiki", "aider")
        args = _make_args()
        hook_cmd.run(args)

        hook_text = (Path(".git/hooks/post-commit")).read_text(encoding="utf-8")
        assert "generate-prompt" in hook_text
        assert "trigger-agent" not in hook_text
        assert "--agent aider" not in hook_text

    def test_hook_agent_override_still_generates_prompt(self, tmp_project):
        """--agent CLI flag does not opt into headless hook execution."""
        _write_agent_config("docs/llm_wiki", "aider")
        args = _make_args(agent="opencode")
        hook_cmd.run(args)

        hook_text = (Path(".git/hooks/post-commit")).read_text(encoding="utf-8")
        assert "generate-prompt" in hook_text
        assert "trigger-agent" not in hook_text
        assert "--agent opencode" not in hook_text

    def test_hook_without_config_generates_prompt(self, tmp_project, capsys):
        """No config is needed because installed hooks are prompt-only."""
        args = _make_args()  # no config file, no --agent
        hook_cmd.run(args)

        out = capsys.readouterr().out
        assert "warning" not in out.lower()

        hook_text = (Path(".git/hooks/post-commit")).read_text(encoding="utf-8")
        assert "generate-prompt" in hook_text
        assert "trigger-agent" not in hook_text


class TestHookInstallsPromptHook:
    """All agents get a prompt-generation hook, not a headless sync hook."""

    def test_post_commit_installed_for_copilot(self, tmp_project, capsys):
        _write_agent_config("docs/llm_wiki", "copilot")
        args = _make_args()
        hook_cmd.run(args)

        hook_path = Path(".git/hooks/post-commit")
        assert hook_path.exists()
        hook_text = hook_path.read_text(encoding="utf-8")
        assert "generate-prompt" in hook_text
        assert "trigger-agent" not in hook_text
        assert "LLM_WIKI_OPEN_PROMPT:-0" in hook_text

    def test_post_commit_installed_for_cursor(self, tmp_project, capsys):
        _write_agent_config("docs/llm_wiki", "cursor")
        args = _make_args()
        hook_cmd.run(args)

        hook_text = Path(".git/hooks/post-commit").read_text(encoding="utf-8")
        assert "generate-prompt" in hook_text

    def test_post_commit_installed_for_generic(self, tmp_project, capsys):
        _write_agent_config("docs/llm_wiki", "generic")
        args = _make_args()
        hook_cmd.run(args)

        hook_text = Path(".git/hooks/post-commit").read_text(encoding="utf-8")
        assert "generate-prompt" in hook_text

    def test_ide_hook_contains_wiki_dir(self, tmp_project):
        _write_agent_config("my_docs/wiki", "copilot")
        args = _make_args(wiki_dir="my_docs/wiki")
        hook_cmd.run(args)

        hook_text = Path(".git/hooks/post-commit").read_text(encoding="utf-8")
        assert "my_docs/wiki" in hook_text

    def test_ide_hook_quotes_wiki_dir_with_spaces(self, tmp_project):
        _write_agent_config("my docs/wiki", "copilot")
        args = _make_args(wiki_dir="my docs/wiki")
        hook_cmd.run(args)

        hook_text = Path(".git/hooks/post-commit").read_text(encoding="utf-8")
        assert "--wiki-dir 'my docs/wiki'" in hook_text

    def test_agent_override_does_not_enable_headless_hook(self, tmp_project, capsys):
        """Passing --agent claude still installs the prompt-generation hook."""
        _write_agent_config("docs/llm_wiki", "copilot")
        args = _make_args(agent="claude")
        hook_cmd.run(args)

        hook_text = Path(".git/hooks/post-commit").read_text(encoding="utf-8")
        assert "generate-prompt" in hook_text
        assert "trigger-agent" not in hook_text
        assert "--agent claude" not in hook_text

    def test_ide_output_message_mentions_paste(self, tmp_project, capsys):
        _write_agent_config("docs/llm_wiki", "copilot")
        args = _make_args()
        hook_cmd.run(args)

        out = capsys.readouterr().out
        assert "generate-prompt" in out or "paste" in out.lower()


class TestHookReadsCustomWikiDir:
    def test_reads_config_from_custom_wiki_dir(self, tmp_project):
        _write_agent_config("my_docs/wiki", "aider")
        args = _make_args(wiki_dir="my_docs/wiki")
        hook_cmd.run(args)

        hook_text = (Path(".git/hooks/post-commit")).read_text(encoding="utf-8")
        assert "generate-prompt" in hook_text
        assert "trigger-agent" not in hook_text
        assert "--wiki-dir my_docs/wiki" in hook_text

    def test_prompt_hook_quotes_wiki_dir_with_spaces(self, tmp_project):
        _write_agent_config("my docs/wiki", "aider")
        args = _make_args(wiki_dir="my docs/wiki")
        hook_cmd.run(args)

        hook_text = Path(".git/hooks/post-commit").read_text(encoding="utf-8")
        assert "generate-prompt" in hook_text
        assert "trigger-agent" not in hook_text
        assert "--wiki-dir 'my docs/wiki'" in hook_text


class TestPostCommitAutoCommitGuard:
    """post-commit hooks must skip when LLM_WIKI_AUTO_COMMIT is set."""

    def test_prompt_post_commit_has_auto_commit_guard(self, tmp_project):
        _write_agent_config("docs/llm_wiki", "claude")
        args = _make_args()
        hook_cmd.run(args)
        hook_text = Path(".git/hooks/post-commit").read_text(encoding="utf-8")
        assert "LLM_WIKI_AUTO_COMMIT" in hook_text


class TestHookInstallSafety:
    def test_unrelated_existing_hook_is_preserved(self, tmp_project):
        hook_path = Path(".git/hooks/post-commit")
        hook_path.parent.mkdir(parents=True, exist_ok=True)
        hook_path.write_text("#!/bin/sh\necho custom\n", encoding="utf-8")

        with pytest.raises(SystemExit) as exc_info:
            hook_cmd.run(_make_args(agent="claude"))

        assert exc_info.value.code == 1
        assert hook_path.read_text(encoding="utf-8") == "#!/bin/sh\necho custom\n"

    @pytest.mark.parametrize(
        "content",
        [
            '#!/bin/sh\necho "check whether LLM Wiki is stale"\n',
            hook_cmd._build_ide_post_commit("docs/llm_wiki") + "echo user-tail\n",
        ],
    )
    def test_signature_substrings_and_managed_hook_edits_are_preserved(
        self,
        tmp_project,
        content: str,
    ):
        hook_path = Path(".git/hooks/post-commit")
        hook_path.parent.mkdir(parents=True, exist_ok=True)
        hook_path.write_text(content, encoding="utf-8")

        with pytest.raises(SystemExit) as exc_info:
            hook_cmd.run(_make_args(agent="claude"))

        assert exc_info.value.code == 1
        assert hook_path.read_text(encoding="utf-8") == content

    def test_force_replaces_unrelated_existing_hook(self, tmp_project):
        hook_path = Path(".git/hooks/post-commit")
        hook_path.parent.mkdir(parents=True, exist_ok=True)
        hook_path.write_text("#!/bin/sh\necho custom\n", encoding="utf-8")

        hook_cmd.run(_make_args(agent="claude", force=True))

        hook_text = hook_path.read_text(encoding="utf-8")
        assert "LLM Wiki" in hook_text
        assert "echo custom" not in hook_text

    def test_managed_existing_hook_is_replaced(self, tmp_project):
        hook_path = Path(".git/hooks/post-commit")
        hook_path.parent.mkdir(parents=True, exist_ok=True)
        hook_path.write_text("#!/bin/sh\n# LLM Wiki old hook\n", encoding="utf-8")

        hook_cmd.run(_make_args(agent="aider"))

        hook_text = hook_path.read_text(encoding="utf-8")
        assert "generate-prompt" in hook_text
        assert "trigger-agent" not in hook_text

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
            hook_cmd._build_ide_post_commit("docs/llm_wiki").replace(
                "\n", "\r\n"
            )
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

    def test_symlinked_hooks_directory_is_rejected_without_outside_write(
        self,
        tmp_project,
        tmp_path,
    ):
        outside = tmp_path / "outside-hooks"
        outside.mkdir()
        hooks_dir = Path(".git/hooks")
        if hooks_dir.exists():
            shutil.rmtree(hooks_dir)
        try:
            hooks_dir.symlink_to(outside, target_is_directory=True)
        except OSError as exc:  # pragma: no cover - platform policy
            pytest.skip(f"symlinks unavailable: {exc}")

        with pytest.raises(SystemExit) as caught:
            hook_cmd.run(_make_args())

        assert caught.value.code == 2
        assert not (outside / "post-commit").exists()

    def test_parent_rebind_at_guarded_write_never_writes_outside(
        self,
        tmp_project,
        tmp_path,
        monkeypatch,
    ):
        hooks_dir = Path(".git/hooks")
        outside = tmp_path / "outside-hooks"
        outside.mkdir()
        held = Path(".git/hooks-held")
        original_write = hook_cmd.atomic_write_executable_bytes

        def rebind_then_write(target, data, **kwargs):
            hooks_dir.rename(held)
            hooks_dir.symlink_to(outside, target_is_directory=True)
            return original_write(target, data, **kwargs)

        monkeypatch.setattr(
            hook_cmd,
            "atomic_write_executable_bytes",
            rebind_then_write,
        )

        with pytest.raises(SystemExit) as caught:
            hook_cmd.run(_make_args())

        assert caught.value.code == 2
        assert not (outside / "post-commit").exists()

    def test_hook_changed_after_preflight_is_preserved(
        self,
        tmp_project,
        monkeypatch,
    ):
        hook_cmd.run(_make_args())
        hook_path = Path(".git/hooks/post-commit")
        custom = b"#!/bin/sh\necho custom concurrent hook\n"
        original_write = hook_cmd.atomic_write_executable_bytes

        def change_then_write(target, data, **kwargs):
            hook_path.write_bytes(custom)
            return original_write(target, data, **kwargs)

        monkeypatch.setattr(
            hook_cmd,
            "atomic_write_executable_bytes",
            change_then_write,
        )

        with pytest.raises(SystemExit) as caught:
            hook_cmd.run(_make_args())

        assert caught.value.code == 2
        assert hook_path.read_bytes() == custom

    def test_missing_hooks_parent_rebind_during_creation_does_not_escape(
        self,
        tmp_project,
        tmp_path,
        monkeypatch,
    ):
        hooks_dir = Path(".git/hooks")
        shutil.rmtree(hooks_dir)
        held = Path(".git-held")
        outside = tmp_path / "outside-git"
        outside.mkdir()
        original_ensure = hook_cmd.ensure_guarded_directory

        def redirect_then_ensure(path, **kwargs):
            Path(".git").rename(held)
            Path(".git").symlink_to(outside, target_is_directory=True)
            return original_ensure(path, **kwargs)

        monkeypatch.setattr(
            hook_cmd,
            "ensure_guarded_directory",
            redirect_then_ensure,
        )

        with pytest.raises(SystemExit) as caught:
            hook_cmd.run(_make_args())

        assert caught.value.code == 2
        assert not (outside / "hooks").exists()

    @pytest.mark.parametrize("separator", ["\n", "\x85", "\u2028", "\u2029"])
    def test_control_character_wiki_dir_is_rejected_before_hook_write(
        self,
        tmp_project,
        separator: str,
    ):
        with pytest.raises(SystemExit) as caught:
            hook_cmd.run(_make_args(wiki_dir=f"docs/a{separator}b"))

        assert caught.value.code == 2
        assert not Path(".git/hooks/post-commit").exists()

    def test_ide_post_commit_has_auto_commit_guard(self, tmp_project):
        _write_agent_config("docs/llm_wiki", "copilot")
        args = _make_args()
        hook_cmd.run(args)
        hook_text = Path(".git/hooks/post-commit").read_text(encoding="utf-8")
        assert "LLM_WIKI_AUTO_COMMIT" in hook_text


class TestValidationHook:
    def test_enable_validation_installs_pre_commit_strict_lint(self, tmp_project):
        _write_agent_config("docs/llm_wiki", "claude")
        hook_cmd.run(_make_args(enable_validation=True))

        hook_text = Path(".git/hooks/pre-commit").read_text(encoding="utf-8")
        assert "lint --strict" in hook_text
        assert "--wiki-dir docs/llm_wiki" in hook_text

    def test_explicit_profile_is_pinned_in_both_hooks_and_local_config(
        self, tmp_project, capsys: pytest.CaptureFixture[str]
    ):
        profile = Path("config/team selection.json")
        profile.parent.mkdir()
        profile.write_text(
            json.dumps(
                {
                    "schema_version": SOURCE_SELECTION_SCHEMA_VERSION,
                    "include": ["src"],
                    "exclude": [],
                }
            ),
            encoding="utf-8",
        )
        Path("src").mkdir()
        Path("src/app.py").write_text("VALUE = 1\n", encoding="utf-8")

        hook_cmd.run(
            _make_args(
                enable_validation=True,
                wiki_dir="my docs/wiki",
                source_selection=profile.as_posix(),
            )
        )

        selection_arg = "--source-selection 'config/team selection.json'"
        assert selection_arg in Path(".git/hooks/post-commit").read_text(
            encoding="utf-8"
        )
        assert selection_arg in Path(".git/hooks/pre-commit").read_text(
            encoding="utf-8"
        )
        assert read_config("my docs/wiki")["source_selection"] == profile.as_posix()
        assert (
            "llm-wiki generate-prompt --wiki-dir 'my docs/wiki' " + selection_arg
            in capsys.readouterr().out
        )

    def test_source_selection_migrates_fallback_config_without_losing_state(
        self,
        tmp_project,
    ):
        git_dir = Path(".git")
        held_git = Path(".git-held")
        git_dir.rename(held_git)
        try:
            write_config(
                "docs/llm_wiki",
                {
                    "agent": "claude",
                    "quality_hints": False,
                    "reference_skill": False,
                    "issue_reporting": True,
                    "extension_state": {"owner": "plugin"},
                },
            )
            fallback = Path("docs/llm_wiki/.llm-wiki-agent")
            assert fallback.exists()
        finally:
            held_git.rename(git_dir)

        profile = Path("config/team.json")
        profile.parent.mkdir()
        profile.write_text(
            json.dumps(
                {
                    "schema_version": SOURCE_SELECTION_SCHEMA_VERSION,
                    "include": ["src"],
                    "exclude": [],
                }
            ),
            encoding="utf-8",
        )
        Path("src").mkdir()
        Path("src/app.py").write_text("VALUE = 1\n", encoding="utf-8")

        hook_cmd.run(_make_args(source_selection=profile.as_posix()))

        config = read_config("docs/llm_wiki")
        assert config["agent"] == "claude"
        assert config["reference_skill"] is False
        assert config["quality_hints"] is False
        assert config["issue_reporting"] is True
        assert config["extension_state"] == {"owner": "plugin"}
        assert config["source_selection"] == profile.as_posix()
        assert not fallback.exists()

    def test_custom_pre_commit_collision_preflights_all_requested_writes(
        self,
        tmp_project,
    ):
        profile = Path("config/team.json")
        profile.parent.mkdir()
        profile.write_text(
            json.dumps(
                {
                    "schema_version": SOURCE_SELECTION_SCHEMA_VERSION,
                    "include": ["src"],
                    "exclude": [],
                }
            ),
            encoding="utf-8",
        )
        Path("src").mkdir()
        Path("src/app.py").write_text("VALUE = 1\n", encoding="utf-8")
        pre_commit = Path(".git/hooks/pre-commit")
        pre_commit.parent.mkdir(parents=True, exist_ok=True)
        custom = "#!/bin/sh\necho custom\n"
        pre_commit.write_text(custom, encoding="utf-8")

        with pytest.raises(SystemExit) as caught:
            hook_cmd.run(
                _make_args(
                    enable_validation=True,
                    source_selection=profile.as_posix(),
                )
            )

        assert caught.value.code == 1
        assert pre_commit.read_text(encoding="utf-8") == custom
        assert not Path(".git/hooks/post-commit").exists()
        assert "source_selection" not in read_config("docs/llm_wiki")
