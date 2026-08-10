"""Tests for commands/init_cmd.py"""

import json
import types
from pathlib import Path

import pytest

from llm_wiki_cli.commands import init_cmd
from llm_wiki_cli.config import read_config, write_config
from llm_wiki_cli.services.skills import REFERENCE_SKILL_FILES
from llm_wiki_cli.services.source_selection import SOURCE_SELECTION_SCHEMA_VERSION


def _make_args(**kwargs):
    defaults = {"agent": "generic", "wiki_dir": "docs/llm_wiki"}
    defaults.update(kwargs)
    return types.SimpleNamespace(**defaults)


class TestInitCreatesStructure:
    def test_directories_created(self, tmp_project):
        args = _make_args()
        init_cmd.run(args)

        base = Path("docs/llm_wiki")
        assert base.exists()
        assert (base / "entities").exists()
        assert (base / "modules").exists()
        assert (base / "workflows").exists()
        assert (base / "guides").exists()
        assert (base / "guides" / ".gitkeep").exists()
        assert (base / "flows").exists()
        assert (base / "flows" / ".gitkeep").exists()
        assert (base / "infrastructure").exists()
        assert not (base / "dependencies.md").exists()
        assert not (base / "load-order.md").exists()

    def test_core_files_created(self, tmp_project):
        args = _make_args()
        init_cmd.run(args)

        base = Path("docs/llm_wiki")
        assert (base / "index.md").exists()
        assert (base / "log.md").exists()
        index = (base / "index.md").read_text(encoding="utf-8")
        assert "Index" in index
        assert "## Guides" in index


class TestInitAgentSchemas:
    def test_claude_agent(self, tmp_project):
        args = _make_args(agent="claude")
        init_cmd.run(args)
        assert Path("CLAUDE.md").exists()
        content = Path("CLAUDE.md").read_text(encoding="utf-8")
        assert "LLM Wiki Maintainer Constraints" in content
        assert "source of truth for existing page names" in content
        assert "<module_page_stem>_<ClassName>.md" in content
        assert "if a COPY/ADD source is ambiguous" in content

    def test_cursor_agent(self, tmp_project):
        args = _make_args(agent="cursor")
        init_cmd.run(args)
        assert Path(".cursorrules").exists()

    def test_copilot_agent(self, tmp_project):
        args = _make_args(agent="copilot")
        init_cmd.run(args)
        assert Path(".github/copilot-instructions.md").exists()

    def test_generic_agent(self, tmp_project):
        args = _make_args(agent="generic")
        init_cmd.run(args)
        assert Path("AGENTS.md").exists()
        assert not Path(".agents.md").exists()
        content = Path("AGENTS.md").read_text(encoding="utf-8")
        assert "## User docs and usage examples" in content
        assert "usage-examples" in content
        assert "llm-wiki skills export --dest" in content

    def test_omitted_agent_defaults_to_generic_for_new_project(self, tmp_project):
        init_cmd.run(types.SimpleNamespace(wiki_dir="docs/llm_wiki", no_skills=True))

        assert Path("AGENTS.md").exists()
        assert read_config("docs/llm_wiki")["agent"] == "generic"


class TestInitPreservesContent:
    def test_appends_to_existing(self, tmp_project):
        Path("CLAUDE.md").write_text("# My Custom Rules\n\nDo good things.\n")
        args = _make_args(agent="claude")
        init_cmd.run(args)

        content = Path("CLAUDE.md").read_text(encoding="utf-8")
        assert "My Custom Rules" in content
        assert "LLM Wiki Maintainer Constraints" in content

    def test_does_not_duplicate(self, tmp_project):
        args = _make_args(agent="claude")
        init_cmd.run(args)
        init_cmd.run(args)  # run twice

        content = Path("CLAUDE.md").read_text(encoding="utf-8")
        assert content.count("LLM Wiki Maintainer Constraints") == 1

    def test_idempotent_structure(self, tmp_project):
        args = _make_args()
        init_cmd.run(args)
        init_cmd.run(args)

        base = Path("docs/llm_wiki")
        assert (base / "index.md").exists()


class TestInitCustomWikiDir:
    def test_custom_wiki_dir_created(self, tmp_project):
        args = _make_args(agent="claude", wiki_dir="my_docs/wiki")
        init_cmd.run(args)

        assert Path("my_docs/wiki").exists()
        assert Path("my_docs/wiki/index.md").exists()

    def test_agent_file_uses_custom_path(self, tmp_project):
        args = _make_args(agent="claude", wiki_dir="my_docs/wiki")
        init_cmd.run(args)

        content = Path("CLAUDE.md").read_text(encoding="utf-8")
        assert "my_docs/wiki" in content
        assert "docs/llm_wiki" not in content


class TestInitAgentInstallCheck:
    @pytest.mark.parametrize("agent", ["cursor", "copilot", "generic"])
    def test_no_warning_for_schema_only_agents(self, tmp_project, capsys, agent):
        """cursor/copilot/generic have no CLI — no warning expected."""
        args = _make_args(agent=agent)
        init_cmd.run(args)
        out = capsys.readouterr().out
        assert "not installed" not in out

    def test_warning_when_cli_agent_missing(self, tmp_project, capsys, monkeypatch):
        """If 'claude' binary is absent, manual trigger-agent warning is clear."""
        monkeypatch.setattr("shutil.which", lambda _: None)
        args = _make_args(agent="claude")
        init_cmd.run(args)
        out = capsys.readouterr().out
        assert "not installed" in out
        assert "claude" in out
        assert "background auto-sync" not in out
        assert "trigger-agent" in out
        # Schema file is still created despite the warning
        assert Path("CLAUDE.md").exists()

    def test_no_warning_when_cli_agent_present(self, tmp_project, capsys, monkeypatch):
        """No warning when the executable is found on PATH."""
        monkeypatch.setattr("shutil.which", lambda _: "/usr/bin/claude")
        args = _make_args(agent="claude")
        init_cmd.run(args)
        out = capsys.readouterr().out
        assert "not installed" not in out


class TestInitPersistsAgentConfig:
    def test_agent_config_written(self, tmp_project):
        """init writes .llm-wiki-agent with the chosen agent name."""
        args = _make_args(agent="claude")
        init_cmd.run(args)
        config = read_config("docs/llm_wiki")
        assert config["agent"] == "claude"

    @pytest.mark.parametrize("agent", ["aider", "cursor", "copilot", "generic"])
    def test_agent_config_reflects_chosen_agent(self, tmp_project, agent):
        """The config file stores whichever agent was passed."""
        args = _make_args(agent=agent)
        init_cmd.run(args)
        config = read_config("docs/llm_wiki")
        assert config["agent"] == agent

    def test_agent_config_custom_wiki_dir(self, tmp_project):
        """Config is written to .git/ regardless of which wiki dir is used."""
        args = _make_args(agent="opencode", wiki_dir="my_docs/wiki")
        init_cmd.run(args)
        config = read_config("my_docs/wiki")
        assert config["agent"] == "opencode"
        assert not (Path("my_docs/wiki/.llm-wiki-agent")).exists()

    def test_explicit_profile_is_pinned_in_schema_and_local_config(self, tmp_project):
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

        init_cmd.run(
            _make_args(
                agent="generic",
                source_selection=profile.as_posix(),
            )
        )

        schema = Path("AGENTS.md").read_text(encoding="utf-8")
        assert "--source-selection 'config/team selection.json'" in schema
        assert read_config("docs/llm_wiki")["source_selection"] == profile.as_posix()


class TestInitQualityHints:
    """Quality hints are included by default, excluded with --no-quality-hints."""

    def test_default_includes_hints(self, tmp_project):
        args = _make_args(agent="claude")
        init_cmd.run(args)
        content = Path("CLAUDE.md").read_text(encoding="utf-8")
        assert "Agent quality guidelines" in content
        assert "Surgical Changes" in content

    def test_no_quality_hints_flag(self, tmp_project):
        args = _make_args(agent="claude", no_quality_hints=True)
        init_cmd.run(args)
        content = Path("CLAUDE.md").read_text(encoding="utf-8")
        assert "Agent quality guidelines" not in content
        assert "Surgical Changes" not in content
        # Rest of constraints should still be there
        assert "LLM Wiki Maintainer Constraints" in content

    def test_no_quality_hints_persisted(self, tmp_project):
        args = _make_args(agent="copilot", no_quality_hints=True)
        init_cmd.run(args)
        config = read_config("docs/llm_wiki")
        assert config["quality_hints"] is False

    def test_default_hints_persisted(self, tmp_project):
        args = _make_args(agent="copilot")
        init_cmd.run(args)
        config = read_config("docs/llm_wiki")
        assert config["quality_hints"] is True


class TestInitIssueReporting:
    """Tool issue-report instructions are an explicit, persisted opt-in."""

    def test_default_omits_instructions_and_persists_disabled(self, tmp_project):
        init_cmd.run(_make_args(agent="copilot"))

        content = Path(".github/copilot-instructions.md").read_text(encoding="utf-8")
        assert "## Report llm-wiki tool issues" not in content
        assert read_config("docs/llm_wiki")["issue_reporting"] is False

    def test_opt_in_includes_instructions_and_persists_enabled(self, tmp_project):
        init_cmd.run(_make_args(agent="copilot", issue_reporting=True))

        content = Path(".github/copilot-instructions.md").read_text(encoding="utf-8")
        assert "## Report llm-wiki tool issues" in content
        assert read_config("docs/llm_wiki")["issue_reporting"] is True

    def test_no_flag_preserves_stored_opt_in(self, tmp_project):
        init_cmd.run(_make_args(agent="copilot", issue_reporting=True))

        init_cmd.run(_make_args(agent="copilot"))

        content = Path(".github/copilot-instructions.md").read_text(encoding="utf-8")
        assert "## Report llm-wiki tool issues" in content
        assert read_config("docs/llm_wiki")["issue_reporting"] is True

    def test_explicit_flags_toggle_existing_instructions(self, tmp_project):
        schema = Path(".github/copilot-instructions.md")
        init_cmd.run(_make_args(agent="copilot", issue_reporting=True))

        init_cmd.run(_make_args(agent="copilot", issue_reporting=False))

        assert "## Report llm-wiki tool issues" not in schema.read_text(
            encoding="utf-8"
        )
        assert read_config("docs/llm_wiki")["issue_reporting"] is False

        init_cmd.run(_make_args(agent="copilot", issue_reporting=True))

        assert "## Report llm-wiki tool issues" in schema.read_text(encoding="utf-8")
        assert read_config("docs/llm_wiki")["issue_reporting"] is True

    def test_issue_toggle_preserves_other_stored_preferences(self, tmp_project):
        init_cmd.run(
            _make_args(
                agent="copilot",
                no_quality_hints=True,
                no_skills=True,
            )
        )

        init_cmd.run(_make_args(agent="copilot", issue_reporting=True))

        content = Path(".github/copilot-instructions.md").read_text(encoding="utf-8")
        config = read_config("docs/llm_wiki")
        assert "## Report llm-wiki tool issues" in content
        assert "Agent quality guidelines" not in content
        assert not Path(".llm-wiki/skills/wiki-reference").exists()
        assert config["issue_reporting"] is True
        assert config["quality_hints"] is False
        assert config["reference_skill"] is False

    def test_no_flag_removes_legacy_default_on_instructions(self, tmp_project):
        init_cmd.run(_make_args(agent="copilot", issue_reporting=True))
        write_config(
            "docs/llm_wiki",
            {
                "agent": "copilot",
                "quality_hints": True,
                "reference_skill": True,
            },
        )

        init_cmd.run(_make_args(agent="copilot"))

        content = Path(".github/copilot-instructions.md").read_text(encoding="utf-8")
        assert "## Report llm-wiki tool issues" not in content
        assert read_config("docs/llm_wiki")["issue_reporting"] is False


class TestInitGitignore:
    def test_does_not_add_ineffective_git_dir_entries(self, tmp_project):
        Path(".gitignore").write_text("# user rules\n*.pyc\n", encoding="utf-8")

        init_cmd.run(_make_args(agent="claude"))

        content = Path(".gitignore").read_text(encoding="utf-8")
        assert "*.pyc" in content
        assert ".git/llm-wiki-prompt.txt" not in content
        assert ".git/llm-wiki.lock" not in content
        assert ".git/llm-wiki-breaker.json" not in content
        assert ".git/llm-wiki-sync.log" not in content


class TestInitReferenceSkill:
    def test_generic_agent_uses_neutral_skills_dir(self, tmp_project):
        init_cmd.run(_make_args())

        skill_dir = Path(".llm-wiki/skills/wiki-reference")
        assert {
            path.relative_to(skill_dir).as_posix()
            for path in skill_dir.rglob("*")
            if path.is_file()
        } == set(REFERENCE_SKILL_FILES)
        assert not Path(".claude/skills").exists()

    def test_claude_agent_uses_native_skills_dir(self, tmp_project):
        init_cmd.run(_make_args(agent="claude"))

        skill_dir = Path(".claude/skills/wiki-reference")
        assert {
            path.relative_to(skill_dir).as_posix()
            for path in skill_dir.rglob("*")
            if path.is_file()
        } == set(REFERENCE_SKILL_FILES)
        assert not Path(".llm-wiki/skills").exists()

    def test_no_skills_flag_skips_install(self, tmp_project):
        init_cmd.run(_make_args(no_skills=True))

        assert not Path(".llm-wiki/skills/wiki-reference").exists()

    def test_rerun_preserves_locally_modified_copy(self, tmp_project, capsys):
        init_cmd.run(_make_args())
        ref = Path(".llm-wiki/skills/wiki-reference/references/maintenance.md")
        ref.write_text("local notes\n", encoding="utf-8")

        init_cmd.run(_make_args())

        assert ref.read_text(encoding="utf-8") == "local notes\n"
        output = capsys.readouterr().out
        assert "not an exact bundled copy" in output
        assert (
            "skills install --dest .llm-wiki/skills --skill wiki-reference --force"
            in output
        )

    def test_persists_reference_skill_preference(self, tmp_project):
        init_cmd.run(_make_args())
        assert read_config("docs/llm_wiki")["reference_skill"] is True

    def test_no_skills_persists_opt_out(self, tmp_project):
        init_cmd.run(_make_args(no_skills=True))
        assert read_config("docs/llm_wiki")["reference_skill"] is False

    def test_hints_at_other_bundled_skills(self, tmp_project, capsys):
        init_cmd.run(_make_args())
        out = capsys.readouterr().out
        assert "llm-wiki skills list" in out
