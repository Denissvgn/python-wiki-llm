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
from llm_wiki_cli.config import PathValidationError
from llm_wiki_cli.services import plugins, team
from llm_wiki_cli.services.knowledge_evidence import (
    MODULE_OBSERVATION_SCOPE,
    ConceptObservationBasis,
    sha256_bytes,
)
from llm_wiki_cli.services.sync_manifest import (
    MANIFEST_REPAIR_UNAVAILABLE,
    TOMBSTONE_SOURCE_MISSING,
    ManifestEvidenceBaseline,
    ManifestPageSource,
    ManifestTombstone,
    SyncManifest,
)


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
        assert config is not None
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

    def test_config_must_be_an_object(self):
        with pytest.raises(team.TeamConfigError, match="JSON object"):
            team.validate_team_config([])

    @pytest.mark.parametrize(
        ("path", "value", "message"),
        [
            (("version",), 2, "version must"),
            (("wiki_dir",), "", "wiki_dir"),
            (("conventions",), None, "conventions must"),
            (("conventions", "require_log"), "yes", "require_log"),
            (("conventions", "canonical_naming"), "yes", "canonical_naming"),
            (
                ("conventions", "workflow_filename_pattern"),
                7,
                "workflow_filename_pattern",
            ),
            (
                ("conventions", "workflow_filename_pattern"),
                "(",
                "is invalid",
            ),
            (("agent",), None, "agent must"),
            (("agent", "prompt_template"), 7, "prompt_template"),
        ],
    )
    def test_invalid_config_field_types_are_rejected(
        self, path, value, message
    ):
        config = team.default_team_config()
        container = config
        for key in path[:-1]:
            container = container[key]
        container[path[-1]] = value

        with pytest.raises(team.TeamConfigError, match=message):
            team.validate_team_config(config)


class TestTeamLintAndCheck:
    def test_check_team_conventions_uses_request_object(self):
        source = textwrap.dedent(inspect.getsource(team.check_team_conventions))
        function_node = ast.parse(source).body[0]
        assert isinstance(function_node, ast.FunctionDef)

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

    def test_team_check_rejects_external_source_without_opt_in(
        self, tmp_path, monkeypatch
    ):
        project = tmp_path / "project"
        outside = tmp_path / "outside"
        project.mkdir()
        outside.mkdir()
        (project / "docs" / "llm_wiki").mkdir(parents=True)
        monkeypatch.chdir(project)

        with pytest.raises(PathValidationError, match="--src-dir"):
            team_cmd.run(
                _ns(
                    team_action="check",
                    src_dir=str(outside),
                    wiki_dir="docs/llm_wiki",
                    format="text",
                    allow_external_src=False,
                )
            )

    def test_team_check_accepts_external_source_with_opt_in(
        self, tmp_path, monkeypatch, capsys
    ):
        project = tmp_path / "project"
        outside = tmp_path / "outside"
        project.mkdir()
        outside.mkdir()
        (project / "docs" / "llm_wiki").mkdir(parents=True)
        monkeypatch.chdir(project)
        seen = {}
        monkeypatch.setattr(
            team_cmd,
            "get_inventory",
            lambda src_dir: seen.setdefault("src_dir", src_dir) or {},
        )
        monkeypatch.setattr(team, "build_team_issues", lambda *args, **kwargs: [])

        team_cmd.run(
            _ns(
                team_action="check",
                src_dir=str(outside),
                wiki_dir="docs/llm_wiki",
                format="text",
                allow_external_src=True,
            )
        )

        assert Path(seen["src_dir"]) == outside
        assert "No team issues found" in capsys.readouterr().out

    def test_team_check_allow_external_source_still_rejects_external_wiki(
        self, tmp_path, monkeypatch
    ):
        project = tmp_path / "project"
        outside = tmp_path / "outside"
        external_wiki = tmp_path / "external-wiki"
        project.mkdir()
        outside.mkdir()
        external_wiki.mkdir()
        monkeypatch.chdir(project)

        with pytest.raises(PathValidationError, match="--wiki-dir"):
            team_cmd.run(
                _ns(
                    team_action="check",
                    src_dir=str(outside),
                    wiki_dir=str(external_wiki),
                    format="text",
                    allow_external_src=True,
                )
            )


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
        manifest_text = (wiki / ".llm-wiki-manifest.json").read_text(encoding="utf-8")
        json.loads(manifest_text)
        assert manifest_text.endswith("\n")
        assert not manifest_text.endswith("\n\n")
        log_text = (wiki / "log.md").read_text(encoding="utf-8")
        assert "- ours" in log_text
        assert "- theirs" in log_text

    def test_agreed_v5_manifest_preserves_known_evidence_and_tombstone(
        self, tmp_project
    ):
        _bootstrap()
        wiki = Path("docs/llm_wiki")
        manifest = SyncManifest.load(wiki)
        active_path = "modules/models.md"
        active_mapping = manifest.page_source_mappings[active_path]
        active_basis = ConceptObservationBasis(
            scope=MODULE_OBSERVATION_SCOPE,
            source_path=active_mapping.source_path,
            extractor_ref="python-ast",
            source_content_hash=manifest.sources[active_mapping.source_path]["hash"],
            concept_observation_hash=sha256_bytes(b"models observation"),
        )
        manifest.evidence_baselines[active_path] = ManifestEvidenceBaseline.from_basis(
            active_basis
        )

        stale_path = "modules/retired.md"
        stale_basis = ConceptObservationBasis(
            scope=MODULE_OBSERVATION_SCOPE,
            source_path="retired.py",
            extractor_ref="python-ast",
            source_content_hash=sha256_bytes(b"retired source"),
            concept_observation_hash=sha256_bytes(b"retired observation"),
        )
        manifest.page_source_mappings[stale_path] = ManifestPageSource(
            scope=MODULE_OBSERVATION_SCOPE,
            source_path="retired.py",
        )
        manifest.tombstones[stale_path] = ManifestTombstone(
            reason=TOMBSTONE_SOURCE_MISSING,
            last_valid_basis=stale_basis,
        )
        (wiki / stale_path).write_text("# Retired\n", encoding="utf-8")
        manifest.surfaces = {"flows": {"enabled": True, "categories": ["api"]}}
        manifest.generation_inputs = {"openapi_file": "openapi.json"}
        manifest = manifest.with_artifact_hashes(
            surface_index_hash=sha256_bytes(b"surface"),
            knowledge_index_hash=sha256_bytes(b"knowledge"),
            evaluated_envelope_hash=sha256_bytes(b"envelope"),
        )
        theirs = manifest.with_artifact_hashes(
            surface_index_hash=sha256_bytes(b"other surface"),
            knowledge_index_hash=sha256_bytes(b"other knowledge"),
            evaluated_envelope_hash=sha256_bytes(b"other envelope"),
        )
        manifest_path = wiki / ".llm-wiki-manifest.json"
        manifest_path.write_text(
            _conflicted(manifest.to_json(), theirs.to_json()),
            encoding="utf-8",
        )

        result = team.resolve_conflicts(wiki, ".", write=True)

        assert result["ok"] is True
        resolved = SyncManifest.load(wiki)
        assert resolved.evidence_baselines[active_path] == (
            ManifestEvidenceBaseline.from_basis(active_basis)
        )
        assert (
            resolved.page_source_mappings[stale_path]
            == (manifest.page_source_mappings[stale_path])
        )
        assert resolved.tombstones[stale_path] == manifest.tombstones[stale_path]
        assert resolved.surfaces == manifest.surfaces
        assert resolved.generation_inputs == manifest.generation_inputs
        assert resolved.artifact_hashes is None

    def test_differing_v5_operational_state_requires_manual_resolution(
        self, tmp_project
    ):
        _bootstrap()
        wiki = Path("docs/llm_wiki")
        ours = SyncManifest.load(wiki)
        theirs = SyncManifest.from_payload(ours.to_payload())
        theirs.evidence_baselines["modules/models.md"] = (
            ManifestEvidenceBaseline.unknown(MANIFEST_REPAIR_UNAVAILABLE)
        )
        manifest_path = wiki / ".llm-wiki-manifest.json"
        manifest_path.write_text(
            _conflicted(ours.to_json(), theirs.to_json()),
            encoding="utf-8",
        )

        result = team.resolve_conflicts(wiki, ".", write=True)

        assert result["ok"] is False
        assert result["unresolved"] == [
            {
                "path": ".llm-wiki-manifest.json",
                "reason": (
                    "manifest v5 operational state differs and requires "
                    "manual resolution"
                ),
            }
        ]
        assert "<<<<<<<" in manifest_path.read_text(encoding="utf-8")

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
    def test_team_check_help_lists_allow_external_src(self, monkeypatch, capsys):
        monkeypatch.setattr("sys.argv", ["llm-wiki", "team", "check", "--help"])

        with pytest.raises(SystemExit) as exc_info:
            cli.main()

        assert exc_info.value.code == 0
        help_text = capsys.readouterr().out
        assert "--allow-external-src" in help_text
        assert "outside the current working" in help_text
        assert "directory" in help_text

    def test_team_check_parses_allow_external_src(self, monkeypatch):
        seen = {}
        monkeypatch.setattr(
            team_cmd,
            "run",
            lambda args: seen.setdefault("allow_external_src", args.allow_external_src),
        )
        monkeypatch.setattr(
            "sys.argv", ["llm-wiki", "team", "check", "--allow-external-src"]
        )

        cli.main()

        assert seen["allow_external_src"] is True

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
