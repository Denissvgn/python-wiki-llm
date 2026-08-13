"""Regression contracts for plugin-disabled production sync runs."""

from __future__ import annotations

import ast
import inspect
import json
from pathlib import Path
import sys
import textwrap

from llm_wiki_cli import cli
from llm_wiki_cli.commands import sync_cmd
from llm_wiki_cli.services import plugins
from llm_wiki_cli.services.bootstrap_runtime import run as run_bootstrap
from llm_wiki_cli.services.extraction_service import InventoryResult


def _install_hostile_runtime_plugin(
    project: Path, *, marker: Path
) -> str:
    module_name = "hostile_sync_no_plugins"
    plugin_dir = (
        project / ".llm-wiki" / "catalog_sources" / "hostile-runtime"
    )
    plugin_dir.mkdir(parents=True)
    (plugin_dir / plugins.MANIFEST_FILENAME).write_text(
        json.dumps(
            {
                "id": "hostile-runtime",
                "version": "0.1.0",
                "llm_wiki_version": "*",
                "components": [
                    {
                        "type": "extractor",
                        "id": "hostile",
                        "language": "hostile",
                        "entry_point": f"{module_name}:HostileExtractor",
                    },
                    {
                        "type": "entrypoint_detector",
                        "id": "hostile",
                        "entry_point": f"{module_name}:detect",
                    },
                    {
                        "type": "diagram_style",
                        "id": "hostile",
                        "entry_point": f"{module_name}:style",
                    },
                    {
                        "type": "lint_rule",
                        "id": "hostile",
                        "entry_point": f"{module_name}:check",
                    },
                ],
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    (plugin_dir / f"{module_name}.py").write_text(
        textwrap.dedent(
            f"""\
            from pathlib import Path

            MARKER = Path({str(marker)!r})


            def _tripwire(phase):
                MARKER.write_text(phase + "\\n", encoding="utf-8")


            _tripwire("import")


            class HostileExtractor:
                def extract(self, src_dir, only_files=None, deep=False):
                    _tripwire("extractor")
                    return {{}}


            def detect(inventory):
                _tripwire("entrypoint-detector")
                return []


            def style(context):
                _tripwire("diagram-style")
                return {{}}


            def check(wiki_dir, src_dir, inventory, pages):
                _tripwire("lint-rule")
                return []
            """
        ),
        encoding="utf-8",
    )

    installed = plugins.install_plugin(
        str(plugin_dir), root=project, yes=True
    )
    assert installed["id"] == "hostile-runtime"
    return module_name


def test_sync_no_plugins_is_a_real_sync_option() -> None:
    args = cli._build_parser().parse_args(["sync", "--no-plugins"])

    assert args.command == "sync"
    assert args.no_plugins is True
    assert args.dry_run is False
    assert args.force is False
    options = sync_cmd._sync_run_options_from_args(args)
    assert options.include_plugins is False
    assert options.dry_run is False
    assert options.force is False


def test_sync_plugin_boundaries_receive_the_production_option() -> None:
    tree = ast.parse(inspect.getsource(sync_cmd))
    plugin_calls = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "runtime_project_plugins_enabled"
    ]
    assert plugin_calls
    assert all(
        any(keyword.arg == "include_plugins" for keyword in call.keywords)
        for call in plugin_calls
    )

    entry_point_calls = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "_detect_sync_entry_points"
    ]
    assert entry_point_calls
    assert all(
        any(keyword.arg == "include_plugins" for keyword in call.keywords)
        for call in entry_point_calls
    )

    inventory_function = next(
        node
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name == "_extract_current_inventory"
    )
    inventory_calls = [
        node
        for node in ast.walk(inventory_function)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "get_inventory_result"
    ]
    assert len(inventory_calls) == 1
    include_plugins = next(
        keyword.value
        for keyword in inventory_calls[0].keywords
        if keyword.arg == "include_plugins"
    )
    assert ast.unparse(include_plugins) == "options.include_plugins"


def test_sync_inventory_receives_plugins_disabled(
    tmp_path: Path, monkeypatch
) -> None:
    (tmp_path / "source.py").write_text("VALUE = 1\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    args = cli._build_parser().parse_args(["sync", "--no-plugins"])
    options = sync_cmd._sync_run_options_from_args(args)
    captured: dict[str, object] = {}

    def fake_inventory(*_args, **kwargs) -> InventoryResult:
        captured.update(kwargs)
        return InventoryResult(
            inventory={},
            statuses={},
            source_snapshot=kwargs["source_snapshot"],
        )

    monkeypatch.setattr(sync_cmd, "get_inventory_result", fake_inventory)

    sync_cmd._extract_current_inventory(options)

    assert captured["include_plugins"] is False


def test_real_sync_no_plugins_never_imports_installed_project_code(
    tmp_project: Path, monkeypatch
) -> None:
    monkeypatch.chdir(tmp_project)
    wiki_dir = tmp_project / "docs" / "llm_wiki"
    bootstrap_args = cli._build_parser().parse_args(
        [
            "bootstrap",
            "--src-dir",
            ".",
            "--wiki-dir",
            str(wiki_dir),
            "--skip-workflows",
            "--skip-flows",
            "--skip-dependencies",
            "--source-adapter",
        ]
    )
    run_bootstrap(bootstrap_args)

    marker = tmp_project / "hostile-plugin-executed.txt"
    module_name = _install_hostile_runtime_plugin(
        tmp_project, marker=marker
    )
    assert not marker.exists()
    assert module_name not in sys.modules

    models_path = tmp_project / "models.py"
    models_path.write_text(
        models_path.read_text(encoding="utf-8")
        + "\n\ndef plugin_free_sync_probe() -> str:\n"
        + '    return "updated"\n',
        encoding="utf-8",
    )
    sync_args = cli._build_parser().parse_args(
        [
            "sync",
            "--src-dir",
            ".",
            "--wiki-dir",
            str(wiki_dir),
            "--no-plugins",
            "--no-cache",
            "--jobs",
            "1",
        ]
    )

    sync_cmd.run(sync_args)

    assert "plugin_free_sync_probe" in (
        wiki_dir / "modules" / "models.md"
    ).read_text(encoding="utf-8")
    assert not marker.exists()
    assert module_name not in sys.modules
