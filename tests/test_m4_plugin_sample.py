"""Tests for the documented M4 plugin sample fixture."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

from llm_wiki_cli.commands.extract_cmd import get_inventory
from llm_wiki_cli.services import plugins
from llm_wiki_cli.services.diagrams import resolve_diagram_style
from llm_wiki_cli.services.entrypoints import detect_entry_points

REPO_ROOT = Path(__file__).resolve().parents[1]
SAMPLE_PLUGIN = REPO_ROOT / "examples" / "plugins" / "m4-documentation-hooks"


def _install_sample_plugin(root: Path) -> Path:
    plugin_dir = root / "vendor" / "m4-documentation-hooks"
    shutil.copytree(SAMPLE_PLUGIN, plugin_dir)
    plugins.install_plugin(str(plugin_dir), root=root, yes=True)
    return plugin_dir


def test_sample_plugin_manifest_uses_documented_component_refs(tmp_path):
    manifest = json.loads((SAMPLE_PLUGIN / plugins.MANIFEST_FILENAME).read_text())

    assert manifest["id"] == "m4-documentation-hooks"
    assert manifest["components"] == [
        {
            "type": "entrypoint_detector",
            "id": "worker-tasks",
            "entry_point": "detectors:detect_worker_tasks",
            "description": "Detect task-style worker functions as user-facing flows.",
        },
        {
            "type": "diagram_style",
            "id": "brand-flowcharts",
            "entry_point": "styles:style_flowcharts",
            "description": "Apply bounded Mermaid styling to generated flowcharts.",
        },
    ]


def test_sample_plugin_detector_contributes_task_handler_entrypoint(tmp_path):
    _install_sample_plugin(tmp_path)
    (tmp_path / "tasks.py").write_text(
        "def handle_task():\n    return 'handled'\n", encoding="utf-8"
    )
    inventory = get_inventory(str(tmp_path), deep=True)

    result = detect_entry_points(inventory, root=tmp_path)

    assert result.warnings == []
    assert {
        "id": "task-task-handler",
        "category": "task",
        "file": "tasks.py",
        "symbol": "handle_task",
        "label": "task-handler",
    } in result.entries


def test_sample_plugin_diagram_style_resolves_bounded_options(tmp_path):
    _install_sample_plugin(tmp_path)

    style = resolve_diagram_style({"surface": "relationships"}, root=tmp_path)

    assert style == {
        "direction": "LR",
        "node_classes": {"task-handler": "entry"},
        "category_colors": {"entry": "#2E7D32"},
    }


def test_readme_references_tested_sample_plugin_names():
    content = (REPO_ROOT / "README.md").read_text(encoding="utf-8")

    for expected in [
        "examples/plugins/m4-documentation-hooks",
        "m4-documentation-hooks/worker-tasks",
        "m4-documentation-hooks/brand-flowcharts",
        "detectors:detect_worker_tasks",
        "styles:style_flowcharts",
    ]:
        assert expected in content
