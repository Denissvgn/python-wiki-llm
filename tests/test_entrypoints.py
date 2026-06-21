"""Tests for services/entrypoints.py — entry-point detection and flow assembly."""

from __future__ import annotations

import ast
import inspect
import textwrap

from llm_wiki_cli.commands.extract_cmd import get_inventory, resolve_call_edges
from llm_wiki_cli.services import plugins
from llm_wiki_cli.services.entrypoints import (
    build_flow,
    detect_entry_points,
    get_entry_points,
    read_console_scripts,
    _parse_scripts_section,
)


def _body_line_count(function) -> int:
    source = textwrap.dedent(inspect.getsource(function))
    body = ast.parse(source).body[0].body
    return max(stmt.end_lineno for stmt in body) - min(stmt.lineno for stmt in body) + 1


def _entry(file, symbol):
    return {
        "id": "x",
        "category": "api",
        "file": file,
        "symbol": symbol,
        "label": symbol,
    }


def _write_detector_plugin(tmp_path, *, body, plugin_id="detector-plugin"):
    plugin_dir = tmp_path / "vendor" / plugin_id
    plugin_dir.mkdir(parents=True)
    module_name = "detectors_" + "_".join(tmp_path.parts[-3:])
    module_name = "".join(
        ch if ch.isalnum() or ch == "_" else "_" for ch in module_name
    )
    (plugin_dir / plugins.MANIFEST_FILENAME).write_text(
        textwrap.dedent(f"""\
        {{
          "id": "{plugin_id}",
          "version": "0.1.0",
          "llm_wiki_version": "*",
          "components": [
            {{
              "type": "entrypoint_detector",
              "id": "worker",
              "entry_point": "{module_name}:detect"
            }}
          ]
        }}
        """),
        encoding="utf-8",
    )
    (plugin_dir / f"{module_name}.py").write_text(
        textwrap.dedent(body), encoding="utf-8"
    )
    plugins.install_plugin(str(plugin_dir), root=tmp_path, yes=True)
    return plugin_dir


class TestGetEntryPoints:
    def test_stays_decomposed(self):
        assert _body_line_count(get_entry_points) <= 35

    def test_detects_api_exports(self, tmp_path):
        (tmp_path / "api.py").write_text(
            textwrap.dedent("""\
            __all__ = ["extract_source", "MISSING"]

            def extract_source():
                pass
        """)
        )
        inventory = get_inventory(str(tmp_path), deep=True)
        api = [e for e in get_entry_points(inventory) if e["category"] == "api"]
        assert len(api) == 1
        assert api[0]["symbol"] == "extract_source"
        assert api[0]["id"] == "api-extract_source"

    def test_detects_decorated_cli_http_mcp(self, tmp_path):
        (tmp_path / "app.py").write_text(
            textwrap.dedent("""\
            @cli.command
            def build():
                pass

            @app.get("/users")
            def list_users():
                pass

            @server.tool()
            def search():
                pass
        """)
        )
        inventory = get_inventory(str(tmp_path), deep=True)
        by_cat = {e["category"]: e["symbol"] for e in get_entry_points(inventory)}
        assert by_cat["cli"] == "build"
        assert by_cat["http"] == "list_users"
        assert by_cat["mcp"] == "search"

    def test_detects_top_level_argparse_dispatch_commands_only(self, tmp_path):
        (tmp_path / "commands").mkdir()
        (tmp_path / "commands" / "bootstrap_cmd.py").write_text(
            "def run(args):\n    return args\n", encoding="utf-8"
        )
        (tmp_path / "commands" / "site_cmd.py").write_text(
            "def run(args):\n    return args\n", encoding="utf-8"
        )
        (tmp_path / "cli.py").write_text(
            textwrap.dedent("""\
            from .commands import bootstrap_cmd, site_cmd

            _COMMAND_MODULES = {
                "bootstrap": bootstrap_cmd,
                "site": site_cmd,
            }

            def _register_commands(subparsers):
                subparsers.add_parser("bootstrap")
                site_parser = subparsers.add_parser("site")
                site_sub = site_parser.add_subparsers(dest="site_action")
                site_sub.add_parser("export")
                site_sub.add_parser("check")
            """),
            encoding="utf-8",
        )
        inventory = get_inventory(str(tmp_path), deep=True)

        cli_entries = [
            entry for entry in get_entry_points(inventory) if entry["category"] == "cli"
        ]

        assert cli_entries == [
            {
                "category": "cli",
                "file": "commands/bootstrap_cmd.py",
                "symbol": "run",
                "label": "bootstrap",
                "id": "cli-bootstrap",
            },
            {
                "category": "cli",
                "file": "commands/site_cmd.py",
                "symbol": "run",
                "label": "site",
                "id": "cli-site",
            },
        ]

    def test_detects_decorated_nested_handlers(self, tmp_path):
        (tmp_path / "factory.py").write_text(
            textwrap.dedent("""\
            def create_server():
                @server.tool()
                def search(query):
                    return run(query)
                return server
        """)
        )
        inventory = get_inventory(str(tmp_path), deep=True)
        mcp = [e for e in get_entry_points(inventory) if e["category"] == "mcp"]
        assert [e["symbol"] for e in mcp] == ["search"]

    def test_bare_http_decorator_is_ignored(self, tmp_path):
        (tmp_path / "m.py").write_text("@get\ndef fetch():\n    pass\n")
        inventory = get_inventory(str(tmp_path), deep=True)
        assert [e for e in get_entry_points(inventory) if e["category"] == "http"] == []

    def test_detects_main_block_process(self, tmp_path):
        (tmp_path / "cli.py").write_text(
            textwrap.dedent("""\
            def main():
                pass

            if __name__ == "__main__":
                main()
        """)
        )
        inventory = get_inventory(str(tmp_path), deep=True)
        proc = [e for e in get_entry_points(inventory) if e["category"] == "process"]
        assert proc[0]["symbol"] == "main"
        assert proc[0]["label"] == "cli"

    def test_resolves_console_script_to_file(self, tmp_path):
        (tmp_path / "pkg").mkdir()
        (tmp_path / "pkg" / "cli.py").write_text("def main():\n    pass\n")
        inventory = get_inventory(str(tmp_path), deep=True)
        scripts = [{"name": "tool", "module": "pkg.cli", "attr": "main"}]
        proc = [
            e
            for e in get_entry_points(inventory, console_scripts=scripts)
            if e["label"] == "tool"
        ]
        assert proc[0]["file"] == "pkg/cli.py"
        assert proc[0]["symbol"] == "main"

    def test_main_block_and_console_script_collapse_to_one(self, tmp_path):
        (tmp_path / "cli.py").write_text(
            textwrap.dedent("""\
            def main():
                pass

            if __name__ == "__main__":
                main()
        """)
        )
        inventory = get_inventory(str(tmp_path), deep=True)
        scripts = [{"name": "mytool", "module": "cli", "attr": "main"}]
        proc = [
            e
            for e in get_entry_points(inventory, console_scripts=scripts)
            if e["category"] == "process"
        ]
        assert len(proc) == 1
        assert (
            proc[0]["label"] == "mytool"
        )  # the specific script name wins over the stem

    def test_ids_are_unique_and_deterministic(self, tmp_path):
        (tmp_path / "a.py").write_text('__all__ = ["run"]\n\ndef run():\n    pass\n')
        (tmp_path / "b.py").write_text('__all__ = ["run"]\n\ndef run():\n    pass\n')
        inventory = get_inventory(str(tmp_path), deep=True)
        eps = get_entry_points(inventory)
        ids = [e["id"] for e in eps]
        assert len(ids) == len(set(ids))
        assert {"api-run-a", "api-run-b"} == set(ids)
        assert get_entry_points(inventory) == eps  # deterministic across runs

    def test_installed_plugin_detector_adds_entry_point(self, tmp_path):
        _write_detector_plugin(
            tmp_path,
            body="""
            def detect(inventory):
                assert "tasks.py" in inventory
                return [{
                    "id": "ignored-by-core",
                    "category": "task",
                    "file": "tasks.py",
                    "symbol": "handle",
                    "label": "task-handler",
                }]
            """,
        )
        (tmp_path / "tasks.py").write_text("def handle():\n    return 1\n")
        inventory = get_inventory(str(tmp_path), deep=True)

        result = detect_entry_points(inventory, root=tmp_path)

        assert result.warnings == []
        assert {
            "id": "task-task-handler",
            "category": "task",
            "file": "tasks.py",
            "symbol": "handle",
            "label": "task-handler",
        } in result.entries

    def test_plugin_detector_falls_back_to_cwd_root(self, tmp_path):
        source = tmp_path / "source"
        source.mkdir()
        _write_detector_plugin(
            tmp_path,
            body="""
            def detect(inventory):
                return [{
                    "category": "task",
                    "file": "tasks.py",
                    "symbol": "handle",
                    "label": "fallback-task",
                }]
            """,
        )
        (source / "tasks.py").write_text("def handle():\n    return 1\n")
        inventory = get_inventory(str(source), deep=True)

        result = detect_entry_points(inventory, root=source, fallback_root=tmp_path)

        assert [entry["id"] for entry in result.entries] == ["task-fallback-task"]

    def test_source_root_plugin_detector_wins_over_cwd_fallback(self, tmp_path):
        source = tmp_path / "source"
        source.mkdir()
        _write_detector_plugin(
            source,
            body="""
            def detect(inventory):
                return [{
                    "category": "task",
                    "file": "tasks.py",
                    "symbol": "handle",
                    "label": "source-task",
                }]
            """,
        )
        _write_detector_plugin(
            tmp_path,
            body="""
            def detect(inventory):
                return [{
                    "category": "task",
                    "file": "tasks.py",
                    "symbol": "handle",
                    "label": "fallback-task",
                }]
            """,
            plugin_id="fallback-detector-plugin",
        )
        (source / "tasks.py").write_text("def handle():\n    return 1\n")
        inventory = get_inventory(str(source), deep=True)

        result = detect_entry_points(inventory, root=source, fallback_root=tmp_path)

        assert [entry["id"] for entry in result.entries] == ["task-source-task"]

    def test_plugin_detector_failure_warns_and_keeps_builtins(self, tmp_path):
        _write_detector_plugin(
            tmp_path,
            body="""
            def detect(inventory):
                raise RuntimeError("detector exploded")
            """,
        )
        (tmp_path / "api.py").write_text('__all__ = ["run"]\n\ndef run():\n    pass\n')
        inventory = get_inventory(str(tmp_path), deep=True)

        result = detect_entry_points(inventory, root=tmp_path)

        assert [entry["id"] for entry in result.entries] == ["api-run"]
        assert len(result.warnings) == 1
        assert "detector-plugin/worker" in result.warnings[0]
        assert "detector exploded" in result.warnings[0]

    def test_plugin_entry_collisions_use_existing_stable_ids(self, tmp_path):
        _write_detector_plugin(
            tmp_path,
            body="""
            def detect(inventory):
                return [{
                    "category": "api",
                    "file": "b.py",
                    "symbol": "run",
                    "label": "run",
                }]
            """,
        )
        (tmp_path / "a.py").write_text('__all__ = ["run"]\n\ndef run():\n    pass\n')
        (tmp_path / "b.py").write_text("def run():\n    pass\n")
        inventory = get_inventory(str(tmp_path), deep=True)

        result = detect_entry_points(inventory, root=tmp_path)

        assert [entry["id"] for entry in result.entries] == ["api-run-a", "api-run-b"]

    def test_invalid_plugin_records_warn_without_crashing(self, tmp_path):
        _write_detector_plugin(
            tmp_path,
            body="""
            def detect(inventory):
                return [{"category": "bad category", "symbol": "run"}]
            """,
        )
        inventory = {"api.py": {"functions": [{"name": "run"}], "classes": []}}

        result = detect_entry_points(inventory, root=tmp_path)

        assert result.entries == []
        assert len(result.warnings) == 1
        assert "bad category" in result.warnings[0]


class TestBuildFlow:
    def test_stays_decomposed(self):
        assert _body_line_count(build_flow) <= 35

    def _edges(self, tmp_path, name, body):
        (tmp_path / name).write_text(textwrap.dedent(body))
        inventory = get_inventory(str(tmp_path), deep=True)
        return resolve_call_edges(inventory)

    def test_traces_internal_call_path(self, tmp_path):
        edges = self._edges(
            tmp_path,
            "m.py",
            """\
            def entry():
                step_one()

            def step_one():
                step_two()

            def step_two():
                pass
        """,
        )
        flow = build_flow(_entry("m.py", "entry"), edges)
        assert [(s["symbol"], s["depth"]) for s in flow["steps"]] == [
            ("entry", 0),
            ("step_one", 1),
            ("step_two", 2),
        ]
        assert flow["truncated"] is False
        assert flow["modules_touched"] == ["m.py"]

    def test_external_calls_are_leaf_steps(self, tmp_path):
        edges = self._edges(
            tmp_path,
            "m.py",
            """\
            import os

            def entry():
                return os.getcwd()
        """,
        )
        flow = build_flow(_entry("m.py", "entry"), edges)
        external = [s for s in flow["steps"] if s["kind"] == "external"]
        assert external[0]["symbol"] == "getcwd"

    def test_cycles_terminate(self, tmp_path):
        edges = self._edges(
            tmp_path,
            "m.py",
            """\
            def ping():
                pong()

            def pong():
                ping()
        """,
        )
        flow = build_flow(_entry("m.py", "ping"), edges)
        assert [s["symbol"] for s in flow["steps"]] == ["ping", "pong", "ping"]

    def test_depth_bound_marks_truncation(self, tmp_path):
        edges = self._edges(
            tmp_path,
            "m.py",
            """\
            def a():
                b()
            def b():
                c()
            def c():
                d()
            def d():
                pass
        """,
        )
        flow = build_flow(_entry("m.py", "a"), edges, max_depth=2)
        assert max(s["depth"] for s in flow["steps"]) == 2
        assert flow["truncated"] is True


class TestConsoleScripts:
    def test_parses_project_scripts_section(self):
        text = textwrap.dedent("""\
            [project]
            name = "x"

            [project.scripts]
            llm-wiki = "llm_wiki_cli.cli:main"
            other = "pkg.mod:run"

            [tool.foo]
            bar = "baz"
        """)
        assert _parse_scripts_section(text) == [
            {"name": "llm-wiki", "module": "llm_wiki_cli.cli", "attr": "main"},
            {"name": "other", "module": "pkg.mod", "attr": "run"},
        ]

    def test_read_console_scripts_missing_file(self, tmp_path):
        assert read_console_scripts(str(tmp_path)) == []

    def test_read_console_scripts_from_pyproject(self, tmp_path):
        (tmp_path / "pyproject.toml").write_text(
            '[project.scripts]\ntool = "pkg.cli:main"\n'
        )
        assert read_console_scripts(str(tmp_path)) == [
            {"name": "tool", "module": "pkg.cli", "attr": "main"}
        ]
