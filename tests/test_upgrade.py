"""Tests for llm-wiki upgrade command."""

import json
import os
import subprocess
from pathlib import Path
from types import SimpleNamespace

import pytest

from llm_wiki_cli.commands import upgrade_cmd
from llm_wiki_cli.config import read_config, write_config
from llm_wiki_cli.services.schema import (
    CONSTRAINT_START,
    CONSTRAINT_END,
    SCHEMA_FILENAMES,
)
from llm_wiki_cli.services.source_selection import SOURCE_SELECTION_SCHEMA_VERSION


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _init_project(
    proj: Path,
    agent: str = "copilot",
    wiki_dir: str = "docs/llm_wiki",
    no_skills: bool = False,
    issue_reporting=None,
):
    """Run a minimal init to create the wiki structure and schema file."""
    subprocess.run(["git", "init", str(proj)], capture_output=True, check=True)
    subprocess.run(
        ["git", "-C", str(proj), "config", "user.email", "t@t.com"],
        capture_output=True,
        check=True,
    )
    subprocess.run(
        ["git", "-C", str(proj), "config", "user.name", "T"],
        capture_output=True,
        check=True,
    )

    from llm_wiki_cli.commands import init_cmd

    old_cwd = os.getcwd()
    os.chdir(proj)
    try:
        args = SimpleNamespace(
            agent=agent,
            wiki_dir=wiki_dir,
            no_skills=no_skills,
            issue_reporting=issue_reporting,
        )
        init_cmd.run(args)
    finally:
        os.chdir(old_cwd)


def _make_args(**kwargs):
    defaults = {"wiki_dir": "docs/llm_wiki", "agent": None}
    defaults.update(kwargs)
    return SimpleNamespace(**defaults)


def _write_selection_profile(path: Path, include: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "schema_version": SOURCE_SELECTION_SCHEMA_VERSION,
                "include": [include],
                "exclude": [],
            }
        ),
        encoding="utf-8",
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestUpgradeRefreshesSchema:
    """Constraint block content is replaced (not duplicated) on upgrade."""

    def test_block_replaced_not_duplicated(self, tmp_path):
        _init_project(tmp_path, agent="copilot")
        os.chdir(tmp_path)

        schema = Path(SCHEMA_FILENAMES["copilot"])
        original = schema.read_text(encoding="utf-8")
        assert original.count(CONSTRAINT_START) == 1

        # Upgrade
        upgrade_cmd.run(_make_args())

        updated = schema.read_text(encoding="utf-8")
        assert updated.count(CONSTRAINT_START) == 1
        assert updated.count(CONSTRAINT_END) == 1

    def test_block_content_is_latest(self, tmp_path):
        """After upgrade the block matches what build_schema_content produces."""
        _init_project(tmp_path, agent="copilot")
        os.chdir(tmp_path)

        from llm_wiki_cli.services.schema import build_schema_content

        expected_block = build_schema_content("copilot", "docs/llm_wiki")

        upgrade_cmd.run(_make_args())

        content = Path(SCHEMA_FILENAMES["copilot"]).read_text(encoding="utf-8")
        assert expected_block.strip() in content


class TestUpgradeGenericSchema:
    """Generic agent upgrades target AGENTS.md without legacy migration."""

    def test_generic_upgrade_uses_agents_md(self, tmp_path):
        _init_project(tmp_path, agent="generic")
        os.chdir(tmp_path)

        upgrade_cmd.run(_make_args())

        schema = Path("AGENTS.md")
        assert schema.exists()
        assert CONSTRAINT_START in schema.read_text(encoding="utf-8")
        assert not Path(".agents.md").exists()

    def test_generic_upgrade_does_not_migrate_legacy_agents_md(self, tmp_path):
        subprocess.run(["git", "init", str(tmp_path)], capture_output=True, check=True)
        os.chdir(tmp_path)
        Path("docs/llm_wiki").mkdir(parents=True)
        write_config("docs/llm_wiki", {"agent": "generic", "quality_hints": True})
        legacy_content = (
            "# Legacy Agent Instructions\n\n"
            f"{CONSTRAINT_START}\nlegacy managed block\n{CONSTRAINT_END}\n"
        )
        Path(".agents.md").write_text(legacy_content, encoding="utf-8")

        upgrade_cmd.run(_make_args())

        assert Path("AGENTS.md").exists()
        assert CONSTRAINT_START in Path("AGENTS.md").read_text(encoding="utf-8")
        assert Path(".agents.md").read_text(encoding="utf-8") == legacy_content


class TestUpgradePreservesUserContent:
    """User text outside the constraint markers survives upgrade."""

    def test_user_rules_preserved(self, tmp_path):
        _init_project(tmp_path, agent="copilot")
        os.chdir(tmp_path)

        schema = Path(SCHEMA_FILENAMES["copilot"])
        content = schema.read_text(encoding="utf-8")
        user_rule = "\n# My custom rule\nAlways use type hints.\n"
        schema.write_text(user_rule + content)

        upgrade_cmd.run(_make_args())

        updated = schema.read_text(encoding="utf-8")
        assert "My custom rule" in updated
        assert "Always use type hints." in updated
        assert updated.count(CONSTRAINT_START) == 1


class TestUpgradePreservesWiki:
    """Entity/module pages are never modified by upgrade."""

    def test_wiki_pages_untouched(self, tmp_path):
        _init_project(tmp_path, agent="copilot")
        os.chdir(tmp_path)

        wiki = Path("docs/llm_wiki")
        entity = wiki / "entities" / "Foo.md"
        entity.write_text("# Foo\n\nMy entity.\n")

        upgrade_cmd.run(_make_args())

        assert entity.read_text(encoding="utf-8") == "# Foo\n\nMy entity.\n"


class TestUpgradeSwitchAgent:
    """Switching agents cleans old schema, writes new one, updates config."""

    def test_switch_copilot_to_cursor(self, tmp_path):
        _init_project(tmp_path, agent="copilot")
        os.chdir(tmp_path)

        old_schema = Path(SCHEMA_FILENAMES["copilot"])
        assert old_schema.exists()

        upgrade_cmd.run(_make_args(agent="cursor"))

        # Old schema file should be cleaned/removed
        if old_schema.exists():
            assert CONSTRAINT_START not in old_schema.read_text(encoding="utf-8")

        # New schema file should exist
        new_schema = Path(SCHEMA_FILENAMES["cursor"])
        assert new_schema.exists()
        assert CONSTRAINT_START in new_schema.read_text(encoding="utf-8")

        # Config should be updated
        config = read_config("docs/llm_wiki")
        assert config["agent"] == "cursor"

    def test_switch_preserves_old_user_content(self, tmp_path):
        _init_project(tmp_path, agent="copilot")
        os.chdir(tmp_path)

        old_schema = Path(SCHEMA_FILENAMES["copilot"])
        content = old_schema.read_text(encoding="utf-8")
        old_schema.write_text("# My Copilot Rules\nUse Python 3.12.\n\n" + content)

        upgrade_cmd.run(_make_args(agent="cursor"))

        # Old file should still exist with user content
        assert old_schema.exists()
        remaining = old_schema.read_text(encoding="utf-8")
        assert "My Copilot Rules" in remaining
        assert CONSTRAINT_START not in remaining

    def test_switch_preserves_issue_reporting_preference(self, tmp_path):
        _init_project(tmp_path, agent="copilot", issue_reporting=True)
        os.chdir(tmp_path)

        upgrade_cmd.run(_make_args(agent="cursor"))

        new_schema = Path(SCHEMA_FILENAMES["cursor"])
        assert "## Report llm-wiki tool issues" in new_schema.read_text(
            encoding="utf-8"
        )
        assert read_config("docs/llm_wiki")["issue_reporting"] is True


class TestUpgradeReinstallsHooks:
    """Hook files are updated on upgrade."""

    def test_hooks_installed(self, tmp_path):
        _init_project(tmp_path, agent="copilot")
        os.chdir(tmp_path)

        hook = Path(".git/hooks/post-commit")
        # Remove any existing hook
        if hook.exists():
            hook.unlink()
        assert not hook.exists()

        upgrade_cmd.run(_make_args())

        assert hook.exists()
        content = hook.read_text(encoding="utf-8")
        assert "LLM Wiki" in content

    def test_hooks_refreshed_on_agent_switch(self, tmp_path):
        _init_project(tmp_path, agent="copilot")
        os.chdir(tmp_path)

        # Install initial hooks
        upgrade_cmd.run(_make_args())
        hook = Path(".git/hooks/post-commit")
        old_content = hook.read_text(encoding="utf-8")
        assert "generate-prompt" in old_content  # IDE mode

        # Switch to CLI agent
        upgrade_cmd.run(_make_args(agent="claude"))
        new_content = hook.read_text(encoding="utf-8")
        assert "generate-prompt" in new_content
        assert "trigger-agent" not in new_content

    def test_prompt_hook_keeps_custom_wiki_dir_for_cli_agent(self, tmp_path):
        _init_project(tmp_path, agent="claude", wiki_dir="my docs/wiki")
        os.chdir(tmp_path)

        upgrade_cmd.run(_make_args(wiki_dir="my docs/wiki"))

        hook_text = Path(".git/hooks/post-commit").read_text(encoding="utf-8")
        assert "generate-prompt" in hook_text
        assert "trigger-agent" not in hook_text
        assert "--wiki-dir 'my docs/wiki'" in hook_text


class TestUpgradePreservesSourceSelection:
    def test_explicit_profile_wins_and_refreshes_schema_hooks_and_config(
        self, tmp_path
    ):
        _init_project(tmp_path, agent="generic")
        os.chdir(tmp_path)
        Path("selected-a").mkdir()
        Path("selected-b").mkdir()
        Path("selected-a/app.py").write_text("VALUE = 1\n", encoding="utf-8")
        Path("selected-b/app.py").write_text("VALUE = 2\n", encoding="utf-8")
        _write_selection_profile(Path("config/a.json"), "selected-a")
        _write_selection_profile(Path("config/b.json"), "selected-b")
        stored = read_config("docs/llm_wiki")
        stored["source_selection"] = "config/a.json"
        write_config("docs/llm_wiki", stored)
        pre_commit = Path(".git/hooks/pre-commit")
        pre_commit.parent.mkdir(parents=True, exist_ok=True)
        pre_commit.write_text("#!/bin/sh\n# LLM Wiki\nllm-wiki lint --strict\n")

        upgrade_cmd.run(_make_args(source_selection="config/b.json"))

        schema = Path("AGENTS.md").read_text(encoding="utf-8")
        post = Path(".git/hooks/post-commit").read_text(encoding="utf-8")
        pre = pre_commit.read_text(encoding="utf-8")
        for content in (schema, post, pre):
            assert "--source-selection config/b.json" in content
            assert "--source-selection config/a.json" not in content
        assert read_config("docs/llm_wiki")["source_selection"] == "config/b.json"

    def test_stored_profile_wins_over_auto_discovery(self, tmp_path):
        _init_project(tmp_path, agent="generic")
        os.chdir(tmp_path)
        Path("stored").mkdir()
        Path("discovered").mkdir()
        Path("stored/app.py").write_text("VALUE = 1\n", encoding="utf-8")
        Path("discovered/app.py").write_text("VALUE = 2\n", encoding="utf-8")
        _write_selection_profile(Path("config/stored.json"), "stored")
        _write_selection_profile(
            Path(".llm-wiki/source-selection.json"),
            "discovered",
        )
        stored = read_config("docs/llm_wiki")
        stored["source_selection"] = "config/stored.json"
        write_config("docs/llm_wiki", stored)

        upgrade_cmd.run(_make_args())

        schema = Path("AGENTS.md").read_text(encoding="utf-8")
        assert "--source-selection config/stored.json" in schema
        assert "--source-selection .llm-wiki/source-selection.json" not in schema


class TestUpgradeCreatesNewDirs:
    """New subdirectories appear on upgrade from an older version."""

    def test_infrastructure_dir_created(self, tmp_path):
        _init_project(tmp_path, agent="copilot")
        os.chdir(tmp_path)

        # Simulate an older install without infrastructure/
        infra = Path("docs/llm_wiki/infrastructure")
        if infra.exists():
            import shutil

            shutil.rmtree(infra)
        assert not infra.exists()

        upgrade_cmd.run(_make_args())

        assert infra.exists()
        assert (infra / ".gitkeep").exists()

    def test_registry_dirs_created_without_architecture_placeholders(self, tmp_path):
        _init_project(tmp_path, agent="copilot")
        os.chdir(tmp_path)

        flows = Path("docs/llm_wiki/flows")
        if flows.exists():
            import shutil

            shutil.rmtree(flows)
        Path("docs/llm_wiki/dependencies.md").unlink(missing_ok=True)
        Path("docs/llm_wiki/load-order.md").unlink(missing_ok=True)

        upgrade_cmd.run(_make_args())

        assert flows.exists()
        assert (flows / ".gitkeep").exists()
        assert not Path("docs/llm_wiki/dependencies.md").exists()
        assert not Path("docs/llm_wiki/load-order.md").exists()

    def test_legacy_layout_scaffolded_without_rewriting_pages(self, tmp_path, capsys):
        subprocess.run(["git", "init", str(tmp_path)], capture_output=True, check=True)
        os.chdir(tmp_path)
        wiki = Path("docs/llm_wiki")
        for dirname in ["entities", "modules", "workflows", "infrastructure"]:
            (wiki / dirname).mkdir(parents=True, exist_ok=True)
        pages = {
            "index.md": "# Legacy Index\n\n## Custom\n\nKeep this.\n",
            "log.md": "# Legacy Log\n\nKeep log.\n",
            "entities/User.md": "# User\n\nLegacy entity.\n",
            "modules/models.md": "# models\n\nLegacy module.\n",
            "workflows/signup.md": "# signup\n\nLegacy workflow.\n",
            "infrastructure/docker.md": "# docker\n\nLegacy infrastructure.\n",
        }
        for rel, content in pages.items():
            target = wiki / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")

        upgrade_cmd.run(_make_args(agent="generic"))

        output = capsys.readouterr().out
        assert "Created directory: flows/" in output
        assert "Created .gitkeep: entities/.gitkeep" in output
        assert "Created .gitkeep: flows/.gitkeep" in output
        assert (wiki / "flows" / ".gitkeep").exists()
        assert not (wiki / "dependencies.md").exists()
        assert not (wiki / "load-order.md").exists()
        for rel, content in pages.items():
            assert (wiki / rel).read_text(encoding="utf-8") == content

        snapshot = {
            path.relative_to(wiki).as_posix(): path.read_text(encoding="utf-8")
            for path in wiki.rglob("*")
            if path.is_file()
        }
        upgrade_cmd.run(_make_args(agent="generic"))
        assert {
            path.relative_to(wiki).as_posix(): path.read_text(encoding="utf-8")
            for path in wiki.rglob("*")
            if path.is_file()
        } == snapshot


class TestUpgradeNoAgentConfig:
    """Errors helpfully if no agent is resolvable."""

    def test_error_without_agent(self, tmp_path):
        subprocess.run(["git", "init", str(tmp_path)], capture_output=True, check=True)
        os.chdir(tmp_path)

        # No init, no config, no --agent flag
        wiki = Path("docs/llm_wiki")
        wiki.mkdir(parents=True, exist_ok=True)

        with pytest.raises(SystemExit) as exc_info:
            upgrade_cmd.run(_make_args())

        assert exc_info.value.code == 1


class TestUpgradeQualityHints:
    """Quality hints preference handling across init/upgrade lifecycle."""

    def test_default_includes_hints(self, tmp_path):
        _init_project(tmp_path, agent="copilot")
        os.chdir(tmp_path)

        upgrade_cmd.run(_make_args())

        content = Path(SCHEMA_FILENAMES["copilot"]).read_text(encoding="utf-8")
        assert "Agent quality guidelines" in content
        assert "Surgical Changes" in content

    def test_no_quality_hints_flag(self, tmp_path):
        _init_project(tmp_path, agent="copilot")
        os.chdir(tmp_path)

        upgrade_cmd.run(_make_args(quality_hints=False))

        content = Path(SCHEMA_FILENAMES["copilot"]).read_text(encoding="utf-8")
        assert "Agent quality guidelines" not in content
        assert CONSTRAINT_START in content

    def test_no_quality_hints_persisted(self, tmp_path):
        _init_project(tmp_path, agent="copilot")
        os.chdir(tmp_path)

        upgrade_cmd.run(_make_args(quality_hints=False))

        config = read_config("docs/llm_wiki")
        assert config["quality_hints"] is False

    def test_preserves_stored_no_hints(self, tmp_path):
        """Init with hints disabled, upgrade without flag → still disabled."""
        _init_project(tmp_path, agent="copilot")
        os.chdir(tmp_path)

        # Simulate stored config with quality_hints=False
        from llm_wiki_cli.config import write_config

        write_config("docs/llm_wiki", {"agent": "copilot", "quality_hints": False})

        upgrade_cmd.run(_make_args())  # no quality_hints flag

        content = Path(SCHEMA_FILENAMES["copilot"]).read_text(encoding="utf-8")
        assert "Agent quality guidelines" not in content
        config = read_config("docs/llm_wiki")
        assert config["quality_hints"] is False

    def test_reenable_hints(self, tmp_path):
        """Upgrade with --quality-hints re-enables after previously disabled."""
        _init_project(tmp_path, agent="copilot")
        os.chdir(tmp_path)

        # Disable
        upgrade_cmd.run(_make_args(quality_hints=False))
        assert "Agent quality guidelines" not in Path(
            SCHEMA_FILENAMES["copilot"]
        ).read_text(encoding="utf-8")

        # Re-enable
        upgrade_cmd.run(_make_args(quality_hints=True))
        content = Path(SCHEMA_FILENAMES["copilot"]).read_text(encoding="utf-8")
        assert "Agent quality guidelines" in content
        config = read_config("docs/llm_wiki")
        assert config["quality_hints"] is True


class TestUpgradeIssueReporting:
    """CLI overrides stored issue-reporting state; otherwise state persists."""

    def test_default_omits_instructions_and_persists_disabled(self, tmp_path):
        _init_project(tmp_path, agent="copilot")
        os.chdir(tmp_path)

        upgrade_cmd.run(_make_args())

        content = Path(SCHEMA_FILENAMES["copilot"]).read_text(encoding="utf-8")
        assert "## Report llm-wiki tool issues" not in content
        assert read_config("docs/llm_wiki")["issue_reporting"] is False

    def test_no_flag_preserves_stored_opt_in(self, tmp_path):
        _init_project(tmp_path, agent="copilot", issue_reporting=True)
        os.chdir(tmp_path)

        upgrade_cmd.run(_make_args())

        content = Path(SCHEMA_FILENAMES["copilot"]).read_text(encoding="utf-8")
        assert "## Report llm-wiki tool issues" in content
        assert read_config("docs/llm_wiki")["issue_reporting"] is True

    @pytest.mark.parametrize(
        ("stored", "cli_value"),
        [(False, True), (True, False)],
    )
    def test_cli_flag_overrides_stored_preference(self, tmp_path, stored, cli_value):
        _init_project(tmp_path, agent="copilot", issue_reporting=stored)
        os.chdir(tmp_path)

        upgrade_cmd.run(_make_args(issue_reporting=cli_value))

        content = Path(SCHEMA_FILENAMES["copilot"]).read_text(encoding="utf-8")
        assert ("## Report llm-wiki tool issues" in content) is cli_value
        assert read_config("docs/llm_wiki")["issue_reporting"] is cli_value

    def test_explicit_flags_toggle_instructions_repeatedly(self, tmp_path):
        _init_project(tmp_path, agent="copilot")
        os.chdir(tmp_path)
        schema = Path(SCHEMA_FILENAMES["copilot"])

        upgrade_cmd.run(_make_args(issue_reporting=True))
        assert "## Report llm-wiki tool issues" in schema.read_text(encoding="utf-8")

        upgrade_cmd.run(_make_args(issue_reporting=False))
        assert "## Report llm-wiki tool issues" not in schema.read_text(
            encoding="utf-8"
        )

    def test_missing_legacy_config_key_migrates_to_disabled(self, tmp_path):
        _init_project(tmp_path, agent="copilot", issue_reporting=True)
        os.chdir(tmp_path)
        write_config(
            "docs/llm_wiki",
            {
                "agent": "copilot",
                "quality_hints": True,
                "reference_skill": True,
            },
        )

        upgrade_cmd.run(_make_args())

        content = Path(SCHEMA_FILENAMES["copilot"]).read_text(encoding="utf-8")
        assert "## Report llm-wiki tool issues" not in content
        assert read_config("docs/llm_wiki")["issue_reporting"] is False


class TestUpgradeGitignore:
    """Upgrade preserves .gitignore but does not add ineffective .git/ entries."""

    def test_no_git_dir_entries_added(self, tmp_path):
        _init_project(tmp_path, agent="copilot")
        os.chdir(tmp_path)

        gi = Path(".gitignore")
        gi.write_text("# Other stuff\n*.pyc\n")

        upgrade_cmd.run(_make_args())

        content = gi.read_text(encoding="utf-8")
        assert "*.pyc" in content  # user content preserved
        assert ".git/llm-wiki-prompt.txt" not in content
        assert ".git/llm-wiki.lock" not in content
        assert ".git/llm-wiki-breaker.json" not in content
        assert ".git/llm-wiki-sync.log" not in content


class TestUpgradeIdempotent:
    """Running upgrade twice produces the same result."""

    def test_double_upgrade(self, tmp_path):
        _init_project(tmp_path, agent="copilot")
        os.chdir(tmp_path)

        upgrade_cmd.run(_make_args())
        first = Path(SCHEMA_FILENAMES["copilot"]).read_text(encoding="utf-8")
        hook_first = Path(".git/hooks/post-commit").read_text(encoding="utf-8")
        gi_first = (
            Path(".gitignore").read_text(encoding="utf-8")
            if Path(".gitignore").exists()
            else ""
        )

        upgrade_cmd.run(_make_args())
        second = Path(SCHEMA_FILENAMES["copilot"]).read_text(encoding="utf-8")
        hook_second = Path(".git/hooks/post-commit").read_text(encoding="utf-8")
        gi_second = (
            Path(".gitignore").read_text(encoding="utf-8")
            if Path(".gitignore").exists()
            else ""
        )

        assert first == second
        assert hook_first == hook_second
        assert gi_first == gi_second
        assert ".git/llm-wiki-prompt.txt" not in gi_second
        assert ".git/llm-wiki.lock" not in gi_second


class TestUpgradeReferenceSkill:
    def test_force_refreshes_modified_copy(self, tmp_path):
        _init_project(tmp_path, agent="copilot")
        os.chdir(tmp_path)
        ref = Path(".llm-wiki/skills/wiki-reference/reference.md")
        ref.write_text("stale local copy\n", encoding="utf-8")

        upgrade_cmd.run(_make_args())

        assert ref.read_text(encoding="utf-8") != "stale local copy\n"
        assert "GHC 9.6.x" in ref.read_text(encoding="utf-8")

    def test_installs_when_absent(self, tmp_path):
        _init_project(tmp_path, agent="copilot")
        os.chdir(tmp_path)
        import shutil as _shutil

        _shutil.rmtree(".llm-wiki/skills/wiki-reference")

        upgrade_cmd.run(_make_args())

        assert Path(".llm-wiki/skills/wiki-reference/reference.md").is_file()

    def test_no_skills_flag_skips_refresh(self, tmp_path):
        _init_project(tmp_path, agent="copilot")
        os.chdir(tmp_path)
        ref = Path(".llm-wiki/skills/wiki-reference/reference.md")
        ref.write_text("local copy\n", encoding="utf-8")

        upgrade_cmd.run(_make_args(skills=False))

        assert ref.read_text(encoding="utf-8") == "local copy\n"
        assert read_config("docs/llm_wiki")["reference_skill"] is False

    def test_respects_init_opt_out_without_flag(self, tmp_path):
        _init_project(tmp_path, agent="copilot", no_skills=True)
        os.chdir(tmp_path)
        assert not Path(".llm-wiki/skills/wiki-reference").exists()

        upgrade_cmd.run(_make_args())

        assert not Path(".llm-wiki/skills/wiki-reference").exists()
        assert read_config("docs/llm_wiki")["reference_skill"] is False

    def test_skills_flag_overrides_stored_opt_out(self, tmp_path):
        _init_project(tmp_path, agent="copilot", no_skills=True)
        os.chdir(tmp_path)

        upgrade_cmd.run(_make_args(skills=True))

        assert Path(".llm-wiki/skills/wiki-reference/reference.md").is_file()
        assert read_config("docs/llm_wiki")["reference_skill"] is True

    def test_switch_migrates_skill_to_new_agent_dir(self, tmp_path):
        _init_project(tmp_path, agent="copilot")
        os.chdir(tmp_path)
        assert Path(".llm-wiki/skills/wiki-reference/reference.md").is_file()

        upgrade_cmd.run(_make_args(agent="claude"))

        assert not Path(".llm-wiki/skills/wiki-reference").exists()
        assert Path(".claude/skills/wiki-reference/reference.md").is_file()

    def test_switch_keeps_modified_copy_at_old_location(self, tmp_path):
        _init_project(tmp_path, agent="copilot")
        os.chdir(tmp_path)
        old_ref = Path(".llm-wiki/skills/wiki-reference/reference.md")
        old_ref.write_text("local notes\n", encoding="utf-8")

        upgrade_cmd.run(_make_args(agent="claude"))

        assert old_ref.read_text(encoding="utf-8") == "local notes\n"
        assert Path(".claude/skills/wiki-reference/reference.md").is_file()
