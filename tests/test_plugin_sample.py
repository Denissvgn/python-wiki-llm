"""Tests for the documented documentation-hooks plugin sample fixture."""

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

import pytest

from llm_wiki_cli.commands.extract_cmd import get_inventory
from llm_wiki_cli.services import plugins
from llm_wiki_cli.services import plugin_samples
from llm_wiki_cli.services.diagrams import data_flow_diagram, resolve_diagram_style
from llm_wiki_cli.services.entrypoints import detect_entry_points

REPO_ROOT = Path(__file__).resolve().parents[1]
SAMPLE_PLUGIN = REPO_ROOT / "examples" / "plugins" / "documentation-hooks"
BUNDLED_SAMPLE_PLUGIN = (
    REPO_ROOT
    / "src"
    / "llm_wiki_cli"
    / "examples"
    / "plugins"
    / "documentation-hooks"
)
SAMPLE_FILES = (
    "README.md",
    "detectors.py",
    "llm-wiki-plugin.json",
    "styles.py",
)


@pytest.fixture(autouse=True)
def _isolated_sample_modules():
    # Each temporary project models a fresh process. The loader correctly
    # rejects modules already loaded from a different installed plugin root.
    names = ("detectors", "styles")
    previous = {name: sys.modules.pop(name) for name in names if name in sys.modules}
    yield
    for name in names:
        sys.modules.pop(name, None)
    sys.modules.update(previous)


def _install_sample_plugin(root: Path) -> Path:
    plugin_dir = root / "vendor" / "documentation-hooks"
    shutil.copytree(SAMPLE_PLUGIN, plugin_dir)
    plugins.install_plugin(str(plugin_dir), root=root, yes=True)
    return plugin_dir


def test_sample_plugin_manifest_uses_documented_component_refs(tmp_path):
    manifest = json.loads((SAMPLE_PLUGIN / plugins.MANIFEST_FILENAME).read_text())

    assert manifest["id"] == "documentation-hooks"
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


def test_bundled_sample_plugin_matches_source_fixture():
    assert plugin_samples.list_samples() == [
        {
            "id": "documentation-hooks",
            "description": "Documentation hooks sample plugin",
        }
    ]

    for rel in SAMPLE_FILES:
        assert (BUNDLED_SAMPLE_PLUGIN / rel).read_bytes() == (
            SAMPLE_PLUGIN / rel
        ).read_bytes()


def test_bundled_sample_plugin_exports_valid_plugin(tmp_path):
    dest = tmp_path / "vendor" / "documentation-hooks"

    result = plugin_samples.export_sample("documentation-hooks", dest)

    assert result == {"id": "documentation-hooks", "path": str(dest)}
    assert sorted(path.name for path in dest.iterdir()) == sorted(SAMPLE_FILES)
    manifest = plugins.validate_plugin(dest)
    assert manifest["id"] == "documentation-hooks"


def test_deprecated_sample_id_exports_canonical_plugin_with_visible_warning(tmp_path):
    dest = tmp_path / "vendor" / "legacy-export"

    with pytest.warns(
        FutureWarning,
        match=r"is deprecated; use 'documentation-hooks' instead",
    ) as captured:
        result = plugin_samples.export_sample("m4-documentation-hooks", dest)

    assert len(captured) == 1
    assert result == {"id": "documentation-hooks", "path": str(dest)}
    manifest = plugins.validate_plugin(dest)
    assert manifest["id"] == "documentation-hooks"


def test_bundled_sample_plugin_export_rejects_relative_destination_escape(tmp_path):
    with pytest.raises(plugins.PluginError, match="inside the project root"):
        plugin_samples.export_sample(
            "documentation-hooks", "../outside", root=tmp_path
        )


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


@pytest.mark.parametrize("symbol", ["handle_task", "task_handler"])
def test_sample_colors_the_actual_numbered_task_entry_node(tmp_path, symbol):
    _install_sample_plugin(tmp_path)
    style = resolve_diagram_style(
        {"surface": "data_flow", "category": "task"}, root=tmp_path,
        strict_plugin_errors=True,
    )
    diagram = data_flow_diagram(
        {"steps": [
            {"index": 1, "file": "tasks.py", "symbol": symbol},
            {"index": 2, "file": "storage.py", "symbol": "save_result"},
        ]},
        {"tasks.py": "tasks", "storage.py": "storage"},
        style=style,
    )
    assert f's1["1. {symbol}"]' in diagram
    assert "classDef entry fill:#2E7D32,stroke:#2E7D32" in diagram
    assert "class s1 entry" in diagram
    assert "class s2 entry" not in diagram


@pytest.mark.parametrize("context", [
    {"surface": "data_flow", "category": "http"},
    {"surface": "data_flow"},
    {"surface": "sequence", "category": "task"},
])
def test_sample_does_not_color_unrelated_surfaces(tmp_path, context):
    _install_sample_plugin(tmp_path)
    style = resolve_diagram_style(context, root=tmp_path, strict_plugin_errors=True)
    diagram = data_flow_diagram(
        {"steps": [{"file": "tasks.py", "symbol": "handle_task"}]}, {}, style=style
    )
    assert "classDef entry" not in diagram
    assert "class s1 entry" not in diagram


def test_cli_reference_documents_sample_plugin_names():
    content = (REPO_ROOT / "docs/cli-reference.md").read_text(encoding="utf-8")

    for expected in [
        "examples/plugins/documentation-hooks",
        "documentation-hooks/worker-tasks",
        "documentation-hooks/brand-flowcharts",
        "detectors:detect_worker_tasks",
        "styles:style_flowcharts",
    ]:
        assert expected in content
