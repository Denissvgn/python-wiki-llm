"""Tests for commands/extract_cmd.py"""
import textwrap
from pathlib import Path

from llm_wiki_cli.commands.extract_cmd import get_inventory, get_call_graph


class TestGetInventory:
    def test_empty_dir(self, tmp_path):
        inventory = get_inventory(str(tmp_path))
        assert inventory == {}

    def test_single_file_with_class(self, tmp_path):
        (tmp_path / "models.py").write_text(textwrap.dedent("""\
            class Foo:
                pass
        """))
        inventory = get_inventory(str(tmp_path))
        assert len(inventory) == 1
        data = list(inventory.values())[0]
        assert len(data["classes"]) == 1
        assert data["classes"][0]["name"] == "Foo"

    def test_single_file_with_function(self, tmp_path):
        (tmp_path / "utils.py").write_text(textwrap.dedent("""\
            def hello():
                pass
        """))
        inventory = get_inventory(str(tmp_path))
        data = list(inventory.values())[0]
        assert len(data["functions"]) == 1
        assert data["functions"][0]["name"] == "hello"

    def test_skips_venv(self, tmp_path):
        venv = tmp_path / ".venv" / "lib"
        venv.mkdir(parents=True)
        (venv / "something.py").write_text("class Hidden: pass\n")
        (tmp_path / "real.py").write_text("class Visible: pass\n")
        inventory = get_inventory(str(tmp_path))
        assert len(inventory) == 1
        assert list(inventory.values())[0]["classes"][0]["name"] == "Visible"

    def test_skips_syntax_errors(self, tmp_path):
        (tmp_path / "bad.py").write_text("def broken(\n")
        (tmp_path / "good.py").write_text("class OK: pass\n")
        inventory = get_inventory(str(tmp_path))
        assert len(inventory) == 1

    def test_deep_mode_includes_docstrings(self, tmp_path):
        (tmp_path / "models.py").write_text(textwrap.dedent("""\
            class Foo:
                \"\"\"A foo class.\"\"\"
                name: str
                value: int = 42
        """))
        inventory = get_inventory(str(tmp_path), deep=True)
        data = list(inventory.values())[0]
        cls = data["classes"][0]
        assert cls["docstring"] == "A foo class."
        assert len(cls["attributes"]) == 2
        assert cls["attributes"][0]["name"] == "name"
        assert cls["attributes"][0]["type"] == "str"
        assert cls["attributes"][1]["default"] == "42"

    def test_deep_mode_includes_imports(self, tmp_path):
        (tmp_path / "main.py").write_text(textwrap.dedent("""\
            from pathlib import Path
            import os

            def run():
                pass
        """))
        inventory = get_inventory(str(tmp_path), deep=True)
        data = list(inventory.values())[0]
        assert "imports" in data
        import_names = {imp["name"] for imp in data["imports"]}
        assert "Path" in import_names
        assert "os" in import_names

    def test_deep_mode_includes_methods(self, tmp_path):
        (tmp_path / "svc.py").write_text(textwrap.dedent("""\
            class Service:
                def start(self, port: int) -> bool:
                    \"\"\"Start the service.\"\"\"
                    return True

                async def stop(self):
                    pass
        """))
        inventory = get_inventory(str(tmp_path), deep=True)
        cls = list(inventory.values())[0]["classes"][0]
        assert len(cls["methods"]) == 2
        start = cls["methods"][0]
        assert start["name"] == "start"
        assert start["params"][0]["name"] == "port"
        assert start["params"][0]["type"] == "int"
        assert start["return_type"] == "bool"
        assert start["docstring"] == "Start the service."
        assert start["is_async"] is False
        stop = cls["methods"][1]
        assert stop["name"] == "stop"
        assert stop["is_async"] is True

    def test_shallow_mode_slim_format(self, tmp_path):
        (tmp_path / "models.py").write_text(textwrap.dedent("""\
            class Foo:
                \"\"\"A foo class.\"\"\"
                name: str

            def helper():
                pass
        """))
        inventory = get_inventory(str(tmp_path), deep=False)
        data = list(inventory.values())[0]
        cls = data["classes"][0]
        # Slim format: no docstring, no attributes, no methods
        assert "docstring" not in cls
        assert "attributes" not in cls
        assert "methods" not in cls
        assert cls["name"] == "Foo"
        assert "line" in cls

    def test_decorators_extracted(self, tmp_path):
        (tmp_path / "api.py").write_text(textwrap.dedent("""\
            def app_get(path):
                def decorator(fn):
                    return fn
                return decorator

            class Controller:
                @app_get("/users")
                def list_users(self):
                    pass
        """))
        inventory = get_inventory(str(tmp_path), deep=True)
        cls = list(inventory.values())[0]["classes"][0]
        method = cls["methods"][0]
        assert len(method["decorators"]) == 1
        assert "app_get" in method["decorators"][0]

    def test_private_functions_excluded(self, tmp_path):
        (tmp_path / "mod.py").write_text(textwrap.dedent("""\
            def public():
                pass

            def _private():
                pass

            class C:
                pass
        """))
        inventory = get_inventory(str(tmp_path), deep=True)
        data = list(inventory.values())[0]
        fn_names = [f["name"] for f in data["functions"]]
        assert "public" in fn_names
        assert "_private" not in fn_names


class TestGetCallGraph:
    def test_no_workflows_single_module(self, tmp_path):
        (tmp_path / "simple.py").write_text("class Foo: pass\n")
        inventory = get_inventory(str(tmp_path), deep=True)
        graph = get_call_graph(inventory)
        assert graph == {}

    def test_no_workflows_below_threshold(self, tmp_path):
        """Two modules don't meet the 3-module threshold."""
        (tmp_path / "a.py").write_text("class A: pass\n")
        (tmp_path / "b.py").write_text(textwrap.dedent("""\
            from a import A

            def use_a(x: A) -> A:
                return x
        """))
        inventory = get_inventory(str(tmp_path), deep=True)
        graph = get_call_graph(inventory)
        assert graph == {}
