"""Tests for services/entrypoints.py — entry-point detection and flow assembly."""
from __future__ import annotations

import ast
import inspect
import textwrap

from llm_wiki_cli.commands.extract_cmd import get_inventory, resolve_call_edges
from llm_wiki_cli.services.entrypoints import (
    build_flow,
    get_entry_points,
    read_console_scripts,
    _parse_scripts_section,
)


def _body_line_count(function) -> int:
    source = textwrap.dedent(inspect.getsource(function))
    body = ast.parse(source).body[0].body
    return max(stmt.end_lineno for stmt in body) - min(stmt.lineno for stmt in body) + 1


def _entry(file, symbol):
    return {"id": "x", "category": "api", "file": file, "symbol": symbol, "label": symbol}


class TestGetEntryPoints:
    def test_stays_decomposed(self):
        assert _body_line_count(get_entry_points) <= 35

    def test_detects_api_exports(self, tmp_path):
        (tmp_path / "api.py").write_text(textwrap.dedent("""\
            __all__ = ["extract_source", "MISSING"]

            def extract_source():
                pass
        """))
        inventory = get_inventory(str(tmp_path), deep=True)
        api = [e for e in get_entry_points(inventory) if e["category"] == "api"]
        assert len(api) == 1
        assert api[0]["symbol"] == "extract_source"
        assert api[0]["id"] == "api-extract_source"

    def test_detects_decorated_cli_http_mcp(self, tmp_path):
        (tmp_path / "app.py").write_text(textwrap.dedent("""\
            @cli.command
            def build():
                pass

            @app.get("/users")
            def list_users():
                pass

            @server.tool()
            def search():
                pass
        """))
        inventory = get_inventory(str(tmp_path), deep=True)
        by_cat = {e["category"]: e["symbol"] for e in get_entry_points(inventory)}
        assert by_cat["cli"] == "build"
        assert by_cat["http"] == "list_users"
        assert by_cat["mcp"] == "search"

    def test_detects_decorated_nested_handlers(self, tmp_path):
        (tmp_path / "factory.py").write_text(textwrap.dedent('''\
            def create_server():
                @server.tool()
                def search(query):
                    return run(query)
                return server
        '''))
        inventory = get_inventory(str(tmp_path), deep=True)
        mcp = [e for e in get_entry_points(inventory) if e["category"] == "mcp"]
        assert [e["symbol"] for e in mcp] == ["search"]

    def test_bare_http_decorator_is_ignored(self, tmp_path):
        (tmp_path / "m.py").write_text("@get\ndef fetch():\n    pass\n")
        inventory = get_inventory(str(tmp_path), deep=True)
        assert [e for e in get_entry_points(inventory) if e["category"] == "http"] == []

    def test_detects_main_block_process(self, tmp_path):
        (tmp_path / "cli.py").write_text(textwrap.dedent("""\
            def main():
                pass

            if __name__ == "__main__":
                main()
        """))
        inventory = get_inventory(str(tmp_path), deep=True)
        proc = [e for e in get_entry_points(inventory) if e["category"] == "process"]
        assert proc[0]["symbol"] == "main"
        assert proc[0]["label"] == "cli"

    def test_resolves_console_script_to_file(self, tmp_path):
        (tmp_path / "pkg").mkdir()
        (tmp_path / "pkg" / "cli.py").write_text("def main():\n    pass\n")
        inventory = get_inventory(str(tmp_path), deep=True)
        scripts = [{"name": "tool", "module": "pkg.cli", "attr": "main"}]
        proc = [e for e in get_entry_points(inventory, console_scripts=scripts) if e["label"] == "tool"]
        assert proc[0]["file"] == "pkg/cli.py"
        assert proc[0]["symbol"] == "main"

    def test_main_block_and_console_script_collapse_to_one(self, tmp_path):
        (tmp_path / "cli.py").write_text(textwrap.dedent("""\
            def main():
                pass

            if __name__ == "__main__":
                main()
        """))
        inventory = get_inventory(str(tmp_path), deep=True)
        scripts = [{"name": "mytool", "module": "cli", "attr": "main"}]
        proc = [e for e in get_entry_points(inventory, console_scripts=scripts) if e["category"] == "process"]
        assert len(proc) == 1
        assert proc[0]["label"] == "mytool"  # the specific script name wins over the stem

    def test_ids_are_unique_and_deterministic(self, tmp_path):
        (tmp_path / "a.py").write_text('__all__ = ["run"]\n\ndef run():\n    pass\n')
        (tmp_path / "b.py").write_text('__all__ = ["run"]\n\ndef run():\n    pass\n')
        inventory = get_inventory(str(tmp_path), deep=True)
        eps = get_entry_points(inventory)
        ids = [e["id"] for e in eps]
        assert len(ids) == len(set(ids))
        assert {"api-run-a", "api-run-b"} == set(ids)
        assert get_entry_points(inventory) == eps  # deterministic across runs


class TestBuildFlow:
    def test_stays_decomposed(self):
        assert _body_line_count(build_flow) <= 35

    def _edges(self, tmp_path, name, body):
        (tmp_path / name).write_text(textwrap.dedent(body))
        inventory = get_inventory(str(tmp_path), deep=True)
        return resolve_call_edges(inventory)

    def test_traces_internal_call_path(self, tmp_path):
        edges = self._edges(tmp_path, "m.py", """\
            def entry():
                step_one()

            def step_one():
                step_two()

            def step_two():
                pass
        """)
        flow = build_flow(_entry("m.py", "entry"), edges)
        assert [(s["symbol"], s["depth"]) for s in flow["steps"]] == [
            ("entry", 0), ("step_one", 1), ("step_two", 2),
        ]
        assert flow["truncated"] is False
        assert flow["modules_touched"] == ["m.py"]

    def test_external_calls_are_leaf_steps(self, tmp_path):
        edges = self._edges(tmp_path, "m.py", """\
            import os

            def entry():
                return os.getcwd()
        """)
        flow = build_flow(_entry("m.py", "entry"), edges)
        external = [s for s in flow["steps"] if s["kind"] == "external"]
        assert external[0]["symbol"] == "getcwd"

    def test_cycles_terminate(self, tmp_path):
        edges = self._edges(tmp_path, "m.py", """\
            def ping():
                pong()

            def pong():
                ping()
        """)
        flow = build_flow(_entry("m.py", "ping"), edges)
        assert [s["symbol"] for s in flow["steps"]] == ["ping", "pong", "ping"]

    def test_depth_bound_marks_truncation(self, tmp_path):
        edges = self._edges(tmp_path, "m.py", """\
            def a():
                b()
            def b():
                c()
            def c():
                d()
            def d():
                pass
        """)
        flow = build_flow(_entry("m.py", "a"), edges, max_depth=2)
        assert max(s["depth"] for s in flow["steps"]) == 2
        assert flow["truncated"] is True


class TestConsoleScripts:
    def test_parses_project_scripts_section(self):
        text = textwrap.dedent('''\
            [project]
            name = "x"

            [project.scripts]
            llm-wiki = "llm_wiki_cli.cli:main"
            other = "pkg.mod:run"

            [tool.foo]
            bar = "baz"
        ''')
        assert _parse_scripts_section(text) == [
            {"name": "llm-wiki", "module": "llm_wiki_cli.cli", "attr": "main"},
            {"name": "other", "module": "pkg.mod", "attr": "run"},
        ]

    def test_read_console_scripts_missing_file(self, tmp_path):
        assert read_console_scripts(str(tmp_path)) == []

    def test_read_console_scripts_from_pyproject(self, tmp_path):
        (tmp_path / "pyproject.toml").write_text('[project.scripts]\ntool = "pkg.cli:main"\n')
        assert read_console_scripts(str(tmp_path)) == [
            {"name": "tool", "module": "pkg.cli", "attr": "main"}
        ]
