from __future__ import annotations

import ast
import inspect
import json
import textwrap
import types
from pathlib import Path

import pytest

from llm_wiki_cli import cli
from llm_wiki_cli.commands import (
    bootstrap_cmd,
    ci_check_cmd,
    generate_prompt_cmd,
    lint_cmd,
    team_cmd,
)
from llm_wiki_cli.services import plugins, team


def _ns(**kwargs):
    return types.SimpleNamespace(**kwargs)


def _bootstrap(wiki_dir: str = "docs/llm_wiki", *, skip_workflows: bool = True):
    bootstrap_cmd.run(
        _ns(
            src_dir=".",
            wiki_dir=wiki_dir,
            overwrite=False,
            depth="full",
            skip_workflows=skip_workflows,
        )
    )


def _write_team_config(data: dict) -> Path:
    path = Path(".llm-wiki/team.json")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return path


def _write_template_plugin(root: Path) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    manifest = {
        "id": "team-templates",
        "version": "0.1.0",
        "llm_wiki_version": "*",
        "components": [
            {
                "type": "prompt_template",
                "id": "team-default",
                "path": "templates/team.md",
            },
            {
                "type": "prompt_template",
                "id": "override",
                "path": "templates/override.md",
            },
            {"type": "lint_rule", "id": "required-rule", "entry_point": "rules:check"},
            {
                "type": "skill",
                "id": "required-skill",
                "path": "skills/required/SKILL.md",
            },
        ],
    }
    (root / plugins.MANIFEST_FILENAME).write_text(
        json.dumps(manifest), encoding="utf-8"
    )
    (root / "templates").mkdir()
    (root / "templates" / "team.md").write_text(
        "TEAM TEMPLATE {wiki_dir} {change_type}\n", encoding="utf-8"
    )
    (root / "templates" / "override.md").write_text(
        "OVERRIDE TEMPLATE {wiki_dir}\n", encoding="utf-8"
    )
    (root / "skills" / "required").mkdir(parents=True)
    (root / "skills" / "required" / "SKILL.md").write_text(
        "# Required Skill\n", encoding="utf-8"
    )
    (root / "rules.py").write_text(
        "def check(wiki_dir, src_dir, inventory, pages):\n    return []\n",
        encoding="utf-8",
    )
    return root


def _conflicted(ours: str, theirs: str) -> str:
    return f"<<<<<<< HEAD\n{ours}\n=======\n{theirs}\n>>>>>>> branch\n"


class TestTeamConfig:
    def test_default_config_round_trips(self, tmp_project):
        path = team.write_default_team_config("docs/llm_wiki")

        config = team.load_team_config(required=True)

        assert path == Path(".llm-wiki/team.json")
        assert config["version"] == 1
        assert config["wiki_dir"] == "docs/llm_wiki"
        assert config["agent"]["required_lint_rules"] == []

    def test_invalid_json_reports_config_error(self, tmp_project):
        Path(".llm-wiki").mkdir()
        Path(".llm-wiki/team.json").write_text("{nope", encoding="utf-8")

        issues = team.build_team_issues(
            "docs/llm_wiki", ".", {}, [], require_config=True
        )

        assert issues[0]["category"] == "team_config"

    def test_unknown_keys_are_rejected(self, tmp_project):
        config = team.default_team_config()
        config["unexpected"] = True

        with pytest.raises(team.TeamConfigError, match="unknown"):
            team.validate_team_config(config)


class TestTeamLintAndCheck:
    def test_check_team_conventions_uses_request_object(self):
        source = textwrap.dedent(inspect.getsource(team.check_team_conventions))
        function_node = ast.parse(source).body[0]

        assert [arg.arg for arg in function_node.args.args] == ["request"]
        assert function_node.args.kwonlyargs == []
        assert function_node.args.vararg is None
        assert function_node.args.kwarg is None

    def test_lint_includes_team_convention_issues(self, tmp_project):
        _bootstrap()
        team.write_default_team_config("docs/llm_wiki")
        user_page = Path("docs/llm_wiki/entities/User.md")
        user_page.write_text(
            user_page.read_text(encoding="utf-8").replace("## Methods", "## Behaviors"),
            encoding="utf-8",
        )

        report = lint_cmd.build_report("docs/llm_wiki", ".", strict=False)

        assert any(issue.category == "team_conventions" for issue in report.issues)

    def test_ci_check_enforces_team_conventions(self, tmp_project):
        _bootstrap()
        team.write_default_team_config("docs/llm_wiki")
        user_page = Path("docs/llm_wiki/entities/User.md")
        user_page.write_text(
            user_page.read_text(encoding="utf-8").replace("## Methods", "## Behaviors"),
            encoding="utf-8",
        )

        with pytest.raises(SystemExit) as exc:
            ci_check_cmd.run(
                _ns(
                    src_dir=".",
                    wiki_dir="docs/llm_wiki",
                    format="markdown",
                    report=".git/team-report.md",
                )
            )

        assert exc.value.code == 1
        assert "team_conventions" in Path(".git/team-report.md").read_text(
            encoding="utf-8"
        )

    def test_team_check_passes_after_bootstrap(self, tmp_project, capsys):
        _bootstrap()
        team.write_default_team_config("docs/llm_wiki")

        team_cmd.run(
            _ns(
                team_action="check",
                src_dir=".",
                wiki_dir="docs/llm_wiki",
                format="text",
            )
        )

        assert "No team issues found" in capsys.readouterr().out


class TestTeamPromptAndPluginRequirements:
    def test_generate_prompt_uses_team_default_template(self, tmp_project):
        _bootstrap()
        plugins.install_plugin(
            str(_write_template_plugin(tmp_project / "vendor" / "team-templates")),
            yes=True,
        )
        config = team.default_team_config("docs/llm_wiki")
        config["agent"]["prompt_template"] = "team-default"
        _write_team_config(config)

        generate_prompt_cmd.run(
            _ns(
                wiki_dir="docs/llm_wiki",
                src_dir=".",
                output=".git/llm-wiki-prompt.txt",
                print_prompt=False,
                change_type="bugfix",
                template=None,
            )
        )

        assert "TEAM TEMPLATE docs/llm_wiki bugfix" in Path(
            ".git/llm-wiki-prompt.txt"
        ).read_text(encoding="utf-8")

    def test_explicit_template_overrides_team_default(self, tmp_project):
        plugins.install_plugin(
            str(_write_template_plugin(tmp_project / "vendor" / "team-templates")),
            yes=True,
        )
        config = team.default_team_config("docs/llm_wiki")
        config["agent"]["prompt_template"] = "team-default"
        _write_team_config(config)

        prompt = generate_prompt_cmd._build_prompt(
            "docs/llm_wiki",
            ".",
            change_type="generic",
            template="override",
            diff_text="",
        )

        assert "OVERRIDE TEMPLATE docs/llm_wiki" in prompt

    def test_missing_required_plugin_components_are_reported(self, tmp_project):
        config = team.default_team_config("docs/llm_wiki")
        config["agent"]["required_lint_rules"] = ["required-rule"]
        config["agent"]["required_skills"] = ["required-skill"]
        _write_team_config(config)

        issues = team.build_team_issues(
            "docs/llm_wiki", ".", {}, [], require_config=True
        )

        assert [issue["category"] for issue in issues].count(
            "team_plugin_requirement"
        ) == 2

    def test_present_required_plugin_components_pass(self, tmp_project):
        plugins.install_plugin(
            str(_write_template_plugin(tmp_project / "vendor" / "team-templates")),
            yes=True,
        )
        config = team.default_team_config("docs/llm_wiki")
        config["agent"]["required_lint_rules"] = ["required-rule"]
        config["agent"]["required_skills"] = ["required-skill"]
        _write_team_config(config)

        issues = team.check_plugin_requirements(config)

        assert issues == []


class TestTeamConflictResolver:
    def test_dry_run_does_not_write_safe_module_resolution(self, tmp_project, capsys):
        _bootstrap()
        module_path = Path("docs/llm_wiki/modules/models.md")
        module_path.write_text(_conflicted("# ours", "# theirs"), encoding="utf-8")

        team_cmd.run(
            _ns(
                team_action="resolve-conflicts",
                src_dir=".",
                wiki_dir="docs/llm_wiki",
                write=False,
                format="text",
            )
        )

        assert "<<<<<<<" in module_path.read_text(encoding="utf-8")
        assert "WOULD RESOLVE modules/models.md" in capsys.readouterr().out

    def test_write_resolves_entity_index_manifest_and_log(self, tmp_project):
        _bootstrap()
        wiki = Path("docs/llm_wiki")
        for rel in ["entities/User.md", "index.md", ".llm-wiki-manifest.json"]:
            (wiki / rel).write_text(_conflicted("ours", "theirs"), encoding="utf-8")
        (wiki / "log.md").write_text(
            "# Architectural Log\n"
            + _conflicted("## 2026-01-01\n- ours", "## 2026-01-02\n- theirs"),
            encoding="utf-8",
        )

        result = team.resolve_conflicts(wiki, ".", write=True)

        assert result["ok"] is True
        assert "<<<<<<<" not in (wiki / "entities/User.md").read_text(encoding="utf-8")
        assert "User" in (wiki / "index.md").read_text(encoding="utf-8")
        json.loads((wiki / ".llm-wiki-manifest.json").read_text(encoding="utf-8"))
        log_text = (wiki / "log.md").read_text(encoding="utf-8")
        assert "- ours" in log_text
        assert "- theirs" in log_text

    def test_workflow_conflict_is_left_unresolved(self, tmp_project):
        _bootstrap()
        workflow = Path("docs/llm_wiki/workflows/manual.md")
        workflow.parent.mkdir(parents=True, exist_ok=True)
        workflow.write_text(_conflicted("# ours", "# theirs"), encoding="utf-8")

        with pytest.raises(SystemExit) as exc:
            team_cmd.run(
                _ns(
                    team_action="resolve-conflicts",
                    src_dir=".",
                    wiki_dir="docs/llm_wiki",
                    write=True,
                    format="json",
                )
            )

        assert exc.value.code == 1
        assert "<<<<<<<" in workflow.read_text(encoding="utf-8")


class TestTeamCliSmoke:
    def test_cli_init_check_and_resolve(self, tmp_project, capsys, monkeypatch):
        _bootstrap()
        monkeypatch.setattr("sys.argv", ["llm-wiki", "team", "init"])
        cli.main()
        assert Path(".llm-wiki/team.json").exists()
        assert "Team config written" in capsys.readouterr().out

        monkeypatch.setattr("sys.argv", ["llm-wiki", "team", "check"])
        cli.main()
        assert "No team issues found" in capsys.readouterr().out

        monkeypatch.setattr("sys.argv", ["llm-wiki", "team", "resolve-conflicts"])
        cli.main()
        assert "No wiki conflict markers found" in capsys.readouterr().out
