"""Tests for commands/install_cmd.py"""

from __future__ import annotations

import json
import textwrap
import types
from pathlib import Path

import pytest

from llm_wiki_cli.commands import install_cmd
from llm_wiki_cli.config import PathValidationError
from llm_wiki_cli.services import plugins


def _make_args(**kwargs):
    defaults = {
        "wiki_dir": "docs/llm_wiki",
        "ref": None,
        "dry_run": False,
        "yes": True,
    }
    defaults.update(kwargs)
    return types.SimpleNamespace(**defaults)


def _write_plugin(
    root: Path,
    *,
    plugin_id: str = "demo-plugin",
    components: list[dict] | None = None,
    extra_files: dict[str, str] | None = None,
) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    if components is None:
        components = [
            {"type": "skill", "id": "guidelines", "path": "skills/guidelines/SKILL.md"},
        ]
    manifest = {
        "id": plugin_id,
        "version": "0.1.0",
        "llm_wiki_version": "*",
        "components": components,
    }
    (root / plugins.MANIFEST_FILENAME).write_text(
        json.dumps(manifest, indent=2), encoding="utf-8"
    )

    files = {
        "skills/guidelines/SKILL.md": "# Demo Skill\n\nKeep wiki edits focused.\n",
    }
    files.update(extra_files or {})
    for rel, content in files.items():
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(textwrap.dedent(content), encoding="utf-8")
    return root


class TestInstallDryRun:
    def test_reports_plugin_without_installing(self, tmp_project, capsys):
        plugin_dir = _write_plugin(tmp_project / "vendor" / "demo")

        install_cmd.run(_make_args(ref=str(plugin_dir), dry_run=True))

        out = capsys.readouterr().out
        assert "Plugin valid: demo-plugin 0.1.0 (1 skill)" in out
        assert "Dry run: no files were changed." in out
        assert not (tmp_project / ".llm-wiki" / "plugins" / "demo-plugin").exists()
        assert "demo-plugin" not in plugins.read_lock().get("plugins", {})

    def test_dry_run_does_not_touch_agent_schema(self, tmp_project):
        plugin_dir = _write_plugin(tmp_project / "vendor" / "demo")

        install_cmd.run(_make_args(ref=str(plugin_dir), dry_run=True))

        assert not Path("AGENTS.md").exists()


class TestInstallReal:
    def test_writes_lockfile_and_prints_summary(self, tmp_project, capsys):
        plugin_dir = _write_plugin(tmp_project / "vendor" / "demo")

        install_cmd.run(_make_args(ref=str(plugin_dir)))

        out = capsys.readouterr().out
        assert "Installed plugin: demo-plugin 0.1.0" in out
        assert "Components: 1 skill" in out
        assert (tmp_project / ".llm-wiki" / "plugins" / "demo-plugin").is_dir()
        assert "demo-plugin" in plugins.read_lock()["plugins"]

    def test_refreshes_skill_blocks_and_reports_count(self, tmp_project, capsys):
        plugin_dir = _write_plugin(tmp_project / "vendor" / "demo")

        install_cmd.run(_make_args(ref=str(plugin_dir)))

        out = capsys.readouterr().out
        assert "Updated 1 skill block(s) in agent schema." in out
        assert "LLM Wiki Skill: demo-plugin/guidelines" in Path(
            "AGENTS.md"
        ).read_text(encoding="utf-8")

    def test_multiple_component_kinds_are_summarized_sorted(self, tmp_project, capsys):
        plugin_dir = _write_plugin(
            tmp_project / "vendor" / "demo",
            components=[
                {
                    "type": "skill",
                    "id": "guidelines",
                    "path": "skills/guidelines/SKILL.md",
                },
                {
                    "type": "prompt_template",
                    "id": "review",
                    "path": "prompts/review.md",
                },
            ],
            extra_files={"prompts/review.md": "Review the diff.\n"},
        )

        install_cmd.run(_make_args(ref=str(plugin_dir)))

        out = capsys.readouterr().out
        assert "Components: 1 prompt_template, 1 skill" in out


class TestInstallErrors:
    def test_plugin_error_prints_to_stderr_and_exits_nonzero(
        self, tmp_project, capsys
    ):
        plugin_dir = _write_plugin(tmp_project / "vendor" / "demo")
        install_cmd.run(_make_args(ref=str(plugin_dir)))
        capsys.readouterr()

        with pytest.raises(SystemExit) as exc_info:
            install_cmd.run(_make_args(ref=str(plugin_dir)))

        assert exc_info.value.code == 1
        err = capsys.readouterr().err
        assert "Error:" in err
        assert "already installed" in err

    def test_rejects_wiki_dir_outside_project(self, tmp_project, tmp_path):
        plugin_dir = _write_plugin(tmp_project / "vendor" / "demo")
        outside = tmp_path / "outside_wiki"
        outside.mkdir()

        with pytest.raises(PathValidationError):
            install_cmd.run(_make_args(ref=str(plugin_dir), wiki_dir=str(outside)))

        assert "demo-plugin" not in plugins.read_lock().get("plugins", {})


class TestComponentSummary:
    def test_empty_components_reports_none(self):
        assert install_cmd._component_summary({"components": []}) == "no components"

    def test_missing_components_key_reports_none(self):
        assert install_cmd._component_summary({}) == "no components"

    def test_counts_grouped_by_type_and_sorted(self):
        plugin = {
            "components": [
                {"type": "skill"},
                {"type": "skill"},
                {"type": "lint_rule"},
            ]
        }
        assert install_cmd._component_summary(plugin) == "1 lint_rule, 2 skill"
