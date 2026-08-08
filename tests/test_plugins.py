from __future__ import annotations

import json
import os
import subprocess
import sys
import textwrap
import types
from pathlib import Path

import pytest

from llm_wiki_cli import cli
from llm_wiki_cli.commands import (
    extract_cmd,
    generate_prompt_cmd,
    init_cmd,
    lint_cmd,
    plugins_cmd,
)
from llm_wiki_cli.services import plugins
from llm_wiki_cli.services.schema import refresh_skill_blocks

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _ns(**kwargs):
    return types.SimpleNamespace(**kwargs)


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


class TestPluginManifestValidation:
    def test_validates_manifest(self, tmp_project):
        plugin_dir = _write_plugin(tmp_project / "vendor" / "demo")

        manifest = plugins.validate_plugin(plugin_dir)

        assert manifest["id"] == "demo-plugin"
        assert manifest["components"][0]["type"] == "skill"

    def test_catalog_loads_string_and_object_entries(self, tmp_project):
        catalog = tmp_project / "catalog.json"
        catalog.write_text(
            json.dumps(
                {
                    "plugins": {
                        "direct": "vendor/direct",
                        "nested": {"path": "vendor/nested"},
                    }
                }
            ),
            encoding="utf-8",
        )

        assert plugins._load_catalog(catalog) == {
            "direct": "vendor/direct",
            "nested": "vendor/nested",
        }
        assert plugins._load_catalog(tmp_project / "missing.json") == {}

    @pytest.mark.parametrize(
        ("content", "message"),
        [
            ("{bad", "Invalid plugin catalog"),
            ("[]", "expected an object"),
            ('{"broken": 42}', "expected a path"),
        ],
    )
    def test_catalog_rejects_malformed_data(
        self, tmp_project, content, message
    ):
        catalog = tmp_project / "catalog.json"
        catalog.write_text(content, encoding="utf-8")

        with pytest.raises(plugins.PluginError, match=message):
            plugins._load_catalog(catalog)

    def test_version_requirements_have_deterministic_semantics(self):
        assert plugins._parse_version("release") == (0, 0, 0)
        assert plugins._parse_version("1.2") == (1, 2, 0)
        assert plugins._version_satisfies("1.5.0", "*")
        assert plugins._version_satisfies("1.5.0", ">=1.4")
        assert plugins._version_satisfies("1.5.0", "==1.5")
        assert not plugins._version_satisfies("1.5.0", "1.4.0")

    def test_safe_prompt_format_preserves_unknown_placeholders(self):
        values = plugins._SafeFormat({"known": "yes"})

        assert "{known} {missing}".format_map(values) == "yes {missing}"
        for directive in (
            "git add -- docs/llm_wiki/\n",
            'git commit -m "docs(wiki): update"\n',
            "git -C . add -- docs/llm_wiki/\n",
            "Then run `git add docs/llm_wiki/`.\n",
            "LLM_WIKI_AUTO_COMMIT=1\n",
        ):
            with pytest.raises(plugins.PluginError, match="owned by llm-wiki"):
                plugins._validate_prompt_template_vcs_boundary(directive)
        plugins._validate_prompt_template_vcs_boundary(
            "Inspect source changes with git diff."
        )

    def test_manifest_rejects_template_owned_git_handoff(self, tmp_project):
        plugin_dir = _write_plugin(
            tmp_project / "vendor" / "unsafe-template",
            components=[
                {
                    "type": "prompt_template",
                    "id": "unsafe",
                    "path": "templates/unsafe.md",
                }
            ],
            extra_files={
                "templates/unsafe.md": "Update the wiki, then `git commit` it.\n",
            },
        )

        with pytest.raises(plugins.PluginError, match="owned by llm-wiki"):
            plugins.validate_plugin(plugin_dir)

    @pytest.mark.parametrize("component_type", ["prompt_template", "skill"])
    def test_rejects_component_path_escape(self, tmp_project, component_type):
        plugin_dir = _write_plugin(
            tmp_project / "vendor" / "escape",
            components=[{"type": component_type, "id": "bad", "path": "../secret.md"}],
        )

        with pytest.raises(plugins.PluginError, match="escapes"):
            plugins.validate_plugin(plugin_dir)

    def test_rejects_entry_point_outside_plugin_directory(self, tmp_project):
        plugin_dir = _write_plugin(
            tmp_project / "vendor" / "outside-entry",
            components=[
                {
                    "type": "lint_rule",
                    "id": "bad",
                    "entry_point": "pathlib:Path",
                }
            ],
        )

        with pytest.raises(plugins.PluginError, match="plugin directory"):
            plugins.validate_plugin(plugin_dir)

    def test_rejects_entry_point_source_under_python_cache_directory(
        self, tmp_project
    ):
        plugin_dir = _write_plugin(
            tmp_project / "vendor" / "cached-entry",
            components=[
                {
                    "type": "lint_rule",
                    "id": "bad",
                    "entry_point": "__pycache__.hidden_rule:check",
                }
            ],
            extra_files={
                "__pycache__/hidden_rule.py": "def check(*args):\n    return []\n"
            },
        )

        with pytest.raises(plugins.PluginError, match="__pycache__"):
            plugins.validate_plugin(plugin_dir)

    @pytest.mark.parametrize(
        ("component_type", "entry_point", "extra_files"),
        [
            (
                "entrypoint_detector",
                "detectors:detect",
                {"detectors.py": "def detect(inventory):\n    return []\n"},
            ),
            (
                "diagram_style",
                "styles:style",
                {"styles.py": "def style(context):\n    return {}\n"},
            ),
        ],
    )
    def test_validates_documentation_entry_point_components(
        self, tmp_project, component_type, entry_point, extra_files
    ):
        plugin_dir = _write_plugin(
            tmp_project / "vendor" / "docs",
            components=[
                {
                    "type": component_type,
                    "id": "docs-hook",
                    "entry_point": entry_point,
                }
            ],
            extra_files=extra_files,
        )

        manifest = plugins.validate_plugin(plugin_dir)

        assert manifest["components"][0] == {
            "type": component_type,
            "id": "docs-hook",
            "entry_point": entry_point,
        }

    def test_install_persists_documentation_components_in_lockfile(self, tmp_project):
        plugin_dir = _write_plugin(
            tmp_project / "vendor" / "docs",
            components=[
                {
                    "type": "entrypoint_detector",
                    "id": "django",
                    "entry_point": "detectors:detect",
                },
                {
                    "type": "diagram_style",
                    "id": "brand",
                    "entry_point": "styles:style",
                },
            ],
            extra_files={
                "detectors.py": "def detect(inventory):\n    return []\n",
                "styles.py": "def style(context):\n    return {}\n",
            },
        )

        plugins.install_plugin(str(plugin_dir), yes=True)

        lock = plugins.read_lock()
        assert lock["version"] == 1
        assert lock["plugins"]["demo-plugin"]["components"] == [
            {
                "type": "entrypoint_detector",
                "id": "django",
                "entry_point": "detectors:detect",
            },
            {
                "type": "diagram_style",
                "id": "brand",
                "entry_point": "styles:style",
            },
        ]

    def test_lists_installed_diagram_style_components(self, tmp_project):
        plugin_dir = _write_plugin(
            tmp_project / "vendor" / "diagram-style",
            plugin_id="diagram-style-plugin",
            components=[
                {
                    "type": "diagram_style",
                    "id": "brand",
                    "entry_point": "styles:style",
                }
            ],
            extra_files={"styles.py": "def style(context):\n    return {}\n"},
        )
        plugins.install_plugin(str(plugin_dir), yes=True)

        components = plugins.diagram_style_components()

        assert len(components) == 1
        assert components[0]["ref"] == "diagram-style-plugin/brand"
        assert components[0]["entry_point"] == "styles:style"

    @pytest.mark.parametrize("component_type", ["entrypoint_detector", "diagram_style"])
    def test_documentation_entry_point_components_reject_invalid_id(
        self, tmp_project, component_type
    ):
        plugin_dir = _write_plugin(
            tmp_project / "vendor" / "docs-invalid-id",
            components=[
                {
                    "type": component_type,
                    "id": "invalid id",
                    "entry_point": "hooks:run",
                }
            ],
            extra_files={"hooks.py": "def run():\n    return None\n"},
        )

        with pytest.raises(plugins.PluginError, match="component.id"):
            plugins.validate_plugin(plugin_dir)

    @pytest.mark.parametrize("component_type", ["entrypoint_detector", "diagram_style"])
    def test_documentation_entry_point_components_reject_outside_entry_point(
        self, tmp_project, component_type
    ):
        plugin_dir = _write_plugin(
            tmp_project / "vendor" / "docs-outside-entry",
            components=[
                {
                    "type": component_type,
                    "id": "bad",
                    "entry_point": "pathlib:Path",
                }
            ],
        )

        with pytest.raises(plugins.PluginError, match="plugin directory"):
            plugins.validate_plugin(plugin_dir)

    def test_extractor_parallel_safe_defaults_false(self, tmp_project):
        plugin_dir = _write_plugin(
            tmp_project / "vendor" / "extractor",
            components=[
                {
                    "type": "extractor",
                    "id": "toy",
                    "language": "toy",
                    "entry_point": "toy_plugin:ToyExtractor",
                }
            ],
            extra_files={
                "toy_plugin.py": """
                    class ToyExtractor:
                        def extract(self, src_dir, only_files=None, deep=False):
                            return {}
                """,
            },
        )

        manifest = plugins.validate_plugin(plugin_dir)

        assert manifest["components"][0]["parallel_safe"] is False

    def test_extractor_parallel_safe_accepts_boolean(self, tmp_project):
        plugin_dir = _write_plugin(
            tmp_project / "vendor" / "extractor",
            components=[
                {
                    "type": "extractor",
                    "id": "toy",
                    "language": "toy",
                    "entry_point": "toy_plugin:ToyExtractor",
                    "parallel_safe": True,
                }
            ],
            extra_files={
                "toy_plugin.py": """
                    class ToyExtractor:
                        def extract(self, src_dir, only_files=None, deep=False):
                            return {}
                """,
            },
        )

        plugins.install_plugin(str(plugin_dir), yes=True)

        lock = plugins.read_lock()
        component = lock["plugins"]["demo-plugin"]["components"][0]
        assert component["parallel_safe"] is True
        assert plugins.parallel_safe_extractor_entry_points() == {
            "toy_plugin:ToyExtractor"
        }

    def test_extractor_parallel_safe_rejects_non_boolean(self, tmp_project):
        plugin_dir = _write_plugin(
            tmp_project / "vendor" / "extractor",
            components=[
                {
                    "type": "extractor",
                    "id": "toy",
                    "language": "toy",
                    "entry_point": "toy_plugin:ToyExtractor",
                    "parallel_safe": "yes",
                }
            ],
            extra_files={
                "toy_plugin.py": """
                    class ToyExtractor:
                        def extract(self, src_dir, only_files=None, deep=False):
                            return {}
                """,
            },
        )

        with pytest.raises(plugins.PluginError, match="parallel_safe"):
            plugins.validate_plugin(plugin_dir)

    def test_resolves_project_catalog_name(self, tmp_project):
        plugin_dir = _write_plugin(
            tmp_project / ".llm-wiki" / "catalog_sources" / "demo"
        )
        catalog = tmp_project / ".llm-wiki" / "catalog.json"
        catalog.parent.mkdir(parents=True, exist_ok=True)
        catalog.write_text(
            json.dumps({"plugins": {"demo": "catalog_sources/demo"}}), encoding="utf-8"
        )

        resolved = plugins.resolve_plugin_ref("demo")

        assert resolved == plugin_dir.resolve()

    def test_direct_plugin_path_must_be_project_local(self, tmp_project, tmp_path):
        plugin_dir = _write_plugin(tmp_path / "outside-plugin")

        with pytest.raises(plugins.PluginError, match="project root"):
            plugins.resolve_plugin_ref(str(plugin_dir))


class TestPluginInstallLifecycle:
    def test_install_writes_lockfile(self, tmp_project):
        plugin_dir = _write_plugin(tmp_project / "vendor" / "demo")

        entry = plugins.install_plugin(str(plugin_dir), yes=True)

        assert entry["id"] == "demo-plugin"
        data = plugins.read_lock()
        assert "demo-plugin" in data["plugins"]
        assert (tmp_project / ".llm-wiki" / "plugins" / "demo-plugin").is_dir()

    def test_install_rejects_duplicate_plugin_id(self, tmp_project):
        plugin_dir = _write_plugin(tmp_project / "vendor" / "demo")
        plugins.install_plugin(str(plugin_dir), yes=True)

        with pytest.raises(plugins.PluginError, match="already installed"):
            plugins.install_plugin(str(plugin_dir), yes=True)

    def test_plugins_remove_strips_skill_blocks(self, tmp_project):
        init_cmd.run(
            _ns(agent="generic", wiki_dir="docs/llm_wiki", no_quality_hints=False)
        )
        plugin_dir = _write_plugin(tmp_project / "vendor" / "demo")
        plugins.install_plugin(str(plugin_dir), yes=True)
        refresh_skill_blocks("generic", "docs/llm_wiki")
        assert "LLM Wiki Skill: demo-plugin/guidelines" in Path("AGENTS.md").read_text(
            encoding="utf-8"
        )

        plugins_cmd.run(
            _ns(
                plugins_action="remove",
                plugin_id="demo-plugin",
                wiki_dir="docs/llm_wiki",
            )
        )

        assert "LLM Wiki Skill: demo-plugin/guidelines" not in Path(
            "AGENTS.md"
        ).read_text(encoding="utf-8")
        assert "demo-plugin" not in plugins.read_lock()["plugins"]

    def test_plugins_remove_strips_legacy_agents_md_skill_blocks(self, tmp_project):
        plugin_dir = _write_plugin(tmp_project / "vendor" / "demo")
        plugins.install_plugin(str(plugin_dir), yes=True)
        Path(".agents.md").write_text(
            "# Legacy Instructions\n\n"
            "# --- LLM Wiki Skill: demo-plugin/guidelines ---\n"
            "Keep wiki edits focused.\n"
            "# --- End LLM Wiki Skill: demo-plugin/guidelines ---\n",
            encoding="utf-8",
        )

        plugins_cmd.run(
            _ns(
                plugins_action="remove",
                plugin_id="demo-plugin",
                wiki_dir="docs/llm_wiki",
            )
        )

        content = Path(".agents.md").read_text(encoding="utf-8")
        assert "Legacy Instructions" in content
        assert "LLM Wiki Skill: demo-plugin/guidelines" not in content


class TestPluginRuntimeIntegration:
    def test_installed_extractor_is_loaded_without_removing_builtins(self, tmp_project):
        (tmp_project / "flow.toy").write_text("run\n", encoding="utf-8")
        plugin_dir = _write_plugin(
            tmp_project / "vendor" / "extractor",
            plugin_id="toy-extractor",
            components=[
                {
                    "type": "extractor",
                    "id": "toy",
                    "language": "toy",
                    "entry_point": "toy_plugin:ToyExtractor",
                }
            ],
            extra_files={
                "toy_plugin.py": """
                    from pathlib import Path

                    class ToyExtractor:
                        def extract(self, src_dir, only_files=None, deep=False):
                            files = [p for p in Path(src_dir).glob("*.toy")]
                            if only_files is not None:
                                wanted = set(only_files)
                                files = [p for p in files if p.name in wanted]
                            return {
                                p.name: {
                                    "language": "toy",
                                    "classes": [],
                                    "functions": [{"name": p.stem, "line": 1}],
                                    "imports": [],
                                }
                                for p in files
                            }
                """,
            },
        )
        plugins.install_plugin(str(plugin_dir), yes=True)

        result = extract_cmd.get_inventory_result(".")
        inventory = result.inventory

        assert "models.py" in inventory
        assert inventory["models.py"]["language"] == "python"
        assert inventory["flow.toy"]["language"] == "toy"
        assert result.extractor_registry["toy"] == "toy_plugin:ToyExtractor"
        assert [component["ref"] for component in result.plugin_components] == [
            "toy-extractor/toy"
        ]
        assert [
            component["ref"] for component in result.producer_plugin_components
        ] == ["toy-extractor/toy"]
        assert result.plugin_lock_path == ".llm-wiki/plugins.lock.json"
        assert result.plugin_lock_hash is not None
        assert result.source_snapshot is not None
        assert set(result.source_snapshot.hashes_for(["flow.toy"])) == {"flow.toy"}

    def test_installed_lint_rule_adds_issue(self, tmp_project, tmp_wiki):
        plugin_dir = _write_plugin(
            tmp_project / "vendor" / "lint",
            plugin_id="lint-plugin",
            components=[
                {
                    "type": "lint_rule",
                    "id": "always",
                    "entry_point": "lint_plugin:check",
                }
            ],
            extra_files={
                "lint_plugin.py": """
                    def check(wiki_dir, src_dir, inventory, pages):
                        return [{
                            "category": "plugin_rule",
                            "message": "Plugin rule fired.",
                            "path": "index.md",
                        }]
                """,
            },
        )
        plugins.install_plugin(str(plugin_dir), yes=True)

        report = lint_cmd.build_report(tmp_wiki, ".")

        assert any(issue.category == "plugin_rule" for issue in report.issues)

    def test_load_entry_point_rejects_lockfile_entry_point_outside_plugin(
        self, tmp_project
    ):
        plugin_dir = _write_plugin(
            tmp_project / "vendor" / "lint",
            plugin_id="lint-plugin",
            components=[
                {
                    "type": "lint_rule",
                    "id": "always",
                    "entry_point": "lint_plugin:check",
                }
            ],
            extra_files={
                "lint_plugin.py": """
                    def check(wiki_dir, src_dir, inventory, pages):
                        return []
                """,
            },
        )
        plugins.install_plugin(str(plugin_dir), yes=True)
        lock = plugins.read_lock()
        lock["plugins"]["lint-plugin"]["components"][0]["entry_point"] = "pathlib:Path"
        plugins.write_lock(lock)

        with pytest.raises(plugins.PluginError, match="installed plugin"):
            plugins.load_entry_point("pathlib:Path")

    def test_load_entry_point_rejects_cache_directory_lockfile_tampering(
        self, tmp_project
    ):
        plugin_dir = _write_plugin(
            tmp_project / "vendor" / "lint-cache-lock",
            plugin_id="lint-cache-lock",
            components=[
                {
                    "type": "lint_rule",
                    "id": "always",
                    "entry_point": "visible_rule:check",
                }
            ],
            extra_files={"visible_rule.py": "def check(*args):\n    return []\n"},
        )
        plugins.install_plugin(str(plugin_dir), yes=True)
        installed = plugins.plugin_store() / "lint-cache-lock"
        hidden = installed / "__pycache__" / "hidden_rule.py"
        hidden.parent.mkdir()
        hidden.write_text(
            "from pathlib import Path\n"
            'Path("cache-entry-executed.txt").write_text("bad", encoding="utf-8")\n'
            "def check(*args):\n    return []\n",
            encoding="utf-8",
        )
        lock = plugins.read_lock()
        lock["plugins"]["lint-cache-lock"]["components"][0]["entry_point"] = (
            "__pycache__.hidden_rule:check"
        )
        plugins.write_lock(lock)

        with pytest.raises(plugins.PluginError, match="__pycache__"):
            plugins.load_entry_point("__pycache__.hidden_rule:check")

        assert not (tmp_project / "cache-entry-executed.txt").exists()

    def test_load_entry_point_rejects_transitive_source_under_cache_directory(
        self, tmp_project
    ):
        plugin_dir = _write_plugin(
            tmp_project / "vendor" / "lint-cache-helper",
            plugin_id="lint-cache-helper",
            components=[
                {
                    "type": "lint_rule",
                    "id": "always",
                    "entry_point": "visible_rule:check",
                }
            ],
            extra_files={"visible_rule.py": "def check(*args):\n    return []\n"},
        )
        plugins.install_plugin(str(plugin_dir), yes=True)
        installed = plugins.plugin_store() / "lint-cache-helper"
        hidden = installed / "__pycache__" / "hidden_helper.py"
        hidden.parent.mkdir()
        hidden.write_text(
            "from pathlib import Path\n"
            'Path("cache-helper-executed.txt").write_text("bad", encoding="utf-8")\n'
            "def check(*args):\n    return []\n",
            encoding="utf-8",
        )
        (installed / "visible_rule.py").write_text(
            "from __pycache__.hidden_helper import check\n",
            encoding="utf-8",
        )

        with pytest.raises(plugins.PluginError, match="__pycache__"):
            plugins.load_entry_point("visible_rule:check")

        assert not (tmp_project / "cache-helper-executed.txt").exists()

    @pytest.mark.parametrize(
        ("configured", "source_plugins_only", "external", "expects_fallback"),
        [
            (False, False, False, True),
            (True, False, False, True),
            (False, True, False, True),
            (False, False, True, True),
            (True, False, True, False),
            (False, True, True, False),
        ],
    )
    def test_runtime_plugin_fallback_root_is_limited_to_legacy_ambient_reads(
        self,
        tmp_project,
        tmp_path,
        configured,
        source_plugins_only,
        external,
        expects_fallback,
    ):
        source_root = tmp_path / "external" if external else tmp_project
        source_root.mkdir(exist_ok=True)

        fallback = plugins.runtime_plugin_fallback_root(
            source_root,
            source_selection_configured=configured,
            source_plugins_only=source_plugins_only,
        )

        assert (fallback == tmp_project) is expects_fallback

    def test_plugin_extractor_entry_point_cannot_import_project_module(
        self, tmp_project
    ):
        (tmp_project / "flow.toy").write_text("run\n", encoding="utf-8")
        plugin_dir = _write_plugin(
            tmp_project / "vendor" / "extractor",
            plugin_id="toy-extractor",
            components=[
                {
                    "type": "extractor",
                    "id": "toy",
                    "language": "toy",
                    "entry_point": "toy_plugin:ToyExtractor",
                }
            ],
            extra_files={
                "toy_plugin.py": """
                    class ToyExtractor:
                        def extract(self, src_dir, only_files=None, deep=False):
                            return {}
                """,
            },
        )
        plugins.install_plugin(str(plugin_dir), yes=True)
        evil_plugin_dir = _write_plugin(
            tmp_project / "vendor" / "evil",
            plugin_id="evil-plugin",
            extra_files={
                "evil_module.py": """
                    from pathlib import Path

                    Path("entry-point-executed.txt").write_text("bad", encoding="utf-8")

                    class Extractor:
                        def extract(self, src_dir, only_files=None, deep=False):
                            return {}
                """,
            },
        )
        plugins.install_plugin(str(evil_plugin_dir), yes=True)
        lock = plugins.read_lock()
        lock["plugins"]["toy-extractor"]["components"][0]["entry_point"] = (
            "evil_module:Extractor"
        )
        plugins.write_lock(lock)

        result = extract_cmd.get_inventory_result(".")

        assert not (tmp_project / "entry-point-executed.txt").exists()
        assert result.statuses["toy"].state == "failed"
        assert "installed plugin" in result.statuses["toy"].message

    def test_prompt_template_renders_known_placeholders(self, tmp_project):
        plugin_dir = _write_plugin(
            tmp_project / "vendor" / "templates",
            plugin_id="template-plugin",
            components=[
                {
                    "type": "prompt_template",
                    "id": "compact",
                    "path": "templates/compact.md",
                }
            ],
            extra_files={
                "templates/compact.md": (
                    "Wiki={wiki_dir}\n"
                    "Source={src_dir}\n"
                    "Type={change_type}\n"
                    "Disposition={wiki_git_disposition}\n"
                    "Eligible={wiki_git_handoff_eligible}\n"
                    "Handoff={wiki_git_handoff}\n"
                ),
            },
        )
        plugins.install_plugin(str(plugin_dir), yes=True)

        prompt = generate_prompt_cmd._build_prompt(
            "docs/llm_wiki",
            ".",
            change_type="bugfix",
            template="compact",
            diff_text="",
        )

        assert "Wiki=docs/llm_wiki" in prompt
        assert "Source=." in prompt
        assert "Type=bugfix" in prompt
        assert "Disposition=included" in prompt
        assert "Eligible=true" in prompt
        assert "Handoff=conditional Git handoff" in prompt
        assert prompt.count("## Repository Policy & Handoff") == 1

        component = plugins.find_prompt_template("compact")
        template_path = Path(component["plugin_dir"]) / component["path"]
        template_path.write_text(
            "Update the wiki.\n```bash\ngit add docs/llm_wiki/\n```\n",
            encoding="utf-8",
        )
        with pytest.raises(plugins.PluginError, match="owned by llm-wiki"):
            generate_prompt_cmd._build_prompt(
                "docs/llm_wiki",
                ".",
                change_type="bugfix",
                template="compact",
                diff_text="",
            )

    def test_skill_refresh_is_idempotent(self, tmp_project):
        init_cmd.run(
            _ns(agent="generic", wiki_dir="docs/llm_wiki", no_quality_hints=False)
        )
        plugin_dir = _write_plugin(tmp_project / "vendor" / "skills")
        plugins.install_plugin(str(plugin_dir), yes=True)

        refresh_skill_blocks("generic", "docs/llm_wiki")
        refresh_skill_blocks("generic", "docs/llm_wiki")

        content = Path("AGENTS.md").read_text(encoding="utf-8")
        assert content.count("# --- LLM Wiki Skill: demo-plugin/guidelines ---") == 1
        assert "Keep wiki edits focused." in content


class TestPluginCliSmoke:
    def test_cli_validate_install_list(self, tmp_project, capsys, monkeypatch):
        plugin_dir = _write_plugin(tmp_project / "vendor" / "demo")

        monkeypatch.setattr(
            "sys.argv", ["llm-wiki", "plugins", "validate", str(plugin_dir)]
        )
        cli.main()
        assert "Plugin valid: demo-plugin" in capsys.readouterr().out

        monkeypatch.setattr(
            "sys.argv", ["llm-wiki", "install", str(plugin_dir), "--yes"]
        )
        cli.main()
        assert "Installed plugin: demo-plugin" in capsys.readouterr().out

        monkeypatch.setattr("sys.argv", ["llm-wiki", "plugins", "list"])
        cli.main()
        assert "demo-plugin 0.1.0" in capsys.readouterr().out

    def test_cli_lists_and_exports_bundled_plugin_sample(
        self, tmp_project, capsys, monkeypatch
    ):
        dest = tmp_project / "vendor" / "documentation-hooks"

        monkeypatch.setattr("sys.argv", ["llm-wiki", "plugins", "samples", "list"])
        cli.main()
        listed = capsys.readouterr().out
        assert "documentation-hooks: Documentation hooks sample plugin" in listed
        assert "m4-documentation-hooks" not in listed

        monkeypatch.setattr(
            "sys.argv",
            [
                "llm-wiki",
                "plugins",
                "samples",
                "export",
                "documentation-hooks",
                "--dest",
                str(dest),
            ],
        )
        cli.main()
        assert (
            "Exported plugin sample: documentation-hooks" in capsys.readouterr().out
        )

        monkeypatch.setattr("sys.argv", ["llm-wiki", "plugins", "validate", str(dest)])
        cli.main()
        assert "Plugin valid: documentation-hooks" in capsys.readouterr().out

        monkeypatch.setattr("sys.argv", ["llm-wiki", "install", str(dest), "--yes"])
        cli.main()
        assert "Installed plugin: documentation-hooks" in capsys.readouterr().out

    def test_cli_legacy_sample_alias_warns_and_exports_canonical_plugin(
        self, tmp_project
    ):
        dest = tmp_project / "vendor" / "legacy-export"
        env = os.environ.copy()
        source_root = str(PROJECT_ROOT / "src")
        current_pythonpath = env.get("PYTHONPATH")
        env["PYTHONPATH"] = (
            os.pathsep.join((source_root, current_pythonpath))
            if current_pythonpath
            else source_root
        )

        completed = subprocess.run(
            [
                sys.executable,
                "-c",
                "from llm_wiki_cli.cli import main; main()",
                "plugins",
                "samples",
                "export",
                "m4-documentation-hooks",
                "--dest",
                str(dest),
            ],
            cwd=tmp_project,
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )

        assert completed.returncode == 0, completed.stderr
        assert "Exported plugin sample: documentation-hooks" in completed.stdout
        assert (
            "Plugin sample 'm4-documentation-hooks' is deprecated; use "
            "'documentation-hooks' instead."
        ) in completed.stderr
        manifest = json.loads(
            (dest / plugins.MANIFEST_FILENAME).read_text(encoding="utf-8")
        )
        assert manifest["id"] == "documentation-hooks"
