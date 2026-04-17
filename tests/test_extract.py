"""Tests for commands/extract_cmd.py"""
import textwrap
from pathlib import Path

from llm_wiki_cli.commands.extract_cmd import get_inventory, get_call_graph, _summarize_inventory


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
        # In deep mode, private functions are included but tagged
        assert "_private" in fn_names
        private_fn = [f for f in data["functions"] if f["name"] == "_private"][0]
        assert private_fn.get("private") is True


class TestRelativePathKeys:
    """Inventory keys must be relative to src_dir, not absolute."""

    def test_keys_are_relative(self, tmp_path):
        (tmp_path / "models.py").write_text("class Foo: pass\n")
        inventory = get_inventory(str(tmp_path))
        key = list(inventory.keys())[0]
        assert not Path(key).is_absolute(), f"Key should be relative, got: {key}"
        assert key == "models.py"

    def test_nested_keys_preserve_structure(self, tmp_path):
        sub = tmp_path / "pkg" / "sub"
        sub.mkdir(parents=True)
        (sub / "deep.py").write_text("class Deep: pass\n")
        inventory = get_inventory(str(tmp_path))
        key = list(inventory.keys())[0]
        assert key == "pkg/sub/deep.py"


class TestExcludedDirsRelative:
    """EXCLUDED_DIRS must check relative parts, not absolute path components."""

    def test_project_under_env_parent_not_excluded(self, tmp_path):
        """A project inside a folder named 'env' should NOT be excluded."""
        proj = tmp_path / "env" / "myproject"
        proj.mkdir(parents=True)
        (proj / "app.py").write_text("class App: pass\n")
        inventory = get_inventory(str(proj))
        assert len(inventory) == 1

    def test_project_under_build_parent_not_excluded(self, tmp_path):
        """A project inside a folder named 'build' should NOT be excluded."""
        proj = tmp_path / "build" / "myproject"
        proj.mkdir(parents=True)
        (proj / "app.py").write_text("class App: pass\n")
        inventory = get_inventory(str(proj))
        assert len(inventory) == 1

    def test_project_under_dist_parent_not_excluded(self, tmp_path):
        proj = tmp_path / "dist" / "repo"
        proj.mkdir(parents=True)
        (proj / "app.py").write_text("class App: pass\n")
        inventory = get_inventory(str(proj))
        assert len(inventory) == 1

    def test_venv_inside_project_still_excluded(self, tmp_path):
        """Files under .venv/ within the project must still be excluded."""
        (tmp_path / "app.py").write_text("class App: pass\n")
        venv = tmp_path / ".venv" / "lib"
        venv.mkdir(parents=True)
        (venv / "hidden.py").write_text("class Hidden: pass\n")
        inventory = get_inventory(str(tmp_path))
        assert len(inventory) == 1
        assert list(inventory.values())[0]["classes"][0]["name"] == "App"

    def test_build_inside_project_still_excluded(self, tmp_path):
        """Files under build/ within the project must still be excluded."""
        (tmp_path / "app.py").write_text("class App: pass\n")
        build = tmp_path / "build" / "lib"
        build.mkdir(parents=True)
        (build / "compiled.py").write_text("class Compiled: pass\n")
        inventory = get_inventory(str(tmp_path))
        assert len(inventory) == 1
        assert list(inventory.values())[0]["classes"][0]["name"] == "App"


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


class TestOnlyFiles:
    def test_restricts_to_specified_files(self, tmp_path):
        (tmp_path / "a.py").write_text("class A: pass\n")
        (tmp_path / "b.py").write_text("class B: pass\n")
        (tmp_path / "c.py").write_text("class C: pass\n")
        inventory = get_inventory(str(tmp_path), only_files=["a.py", "c.py"])
        keys = {Path(k).name for k in inventory}
        assert keys == {"a.py", "c.py"}

    def test_ignores_missing_files(self, tmp_path):
        (tmp_path / "a.py").write_text("class A: pass\n")
        inventory = get_inventory(str(tmp_path), only_files=["a.py", "nope.py"])
        assert len(inventory) == 1

    def test_ignores_non_python_files(self, tmp_path):
        (tmp_path / "readme.md").write_text("# Hi\n")
        (tmp_path / "a.py").write_text("class A: pass\n")
        inventory = get_inventory(str(tmp_path), only_files=["readme.md", "a.py"])
        assert len(inventory) == 1


class TestSummarizeInventory:
    def test_collapses_to_names(self, tmp_path):
        (tmp_path / "models.py").write_text(textwrap.dedent("""\
            class Foo:
                pass

            class Bar:
                pass

            def helper():
                pass
        """))
        inventory = get_inventory(str(tmp_path))
        summary = _summarize_inventory(inventory)
        data = list(summary.values())[0]
        assert data["classes"] == ["Foo", "Bar"]
        assert data["functions"] == ["helper"]
        # No nested details (line numbers, bases, etc.)
        assert isinstance(data["classes"][0], str)

    def test_empty_inventory(self):
        assert _summarize_inventory({}) == {}


class TestPackageDiscovery:
    """Test pyproject.toml / setup.py package discovery and inventory stamping."""

    def test_single_pyproject_toml(self, tmp_path):
        (tmp_path / "pyproject.toml").write_text(
            '[project]\nname = "my-pkg"\nversion = "1.0.0"\n'
        )
        (tmp_path / "app.py").write_text("class App: pass\n")
        inv = get_inventory(str(tmp_path))
        assert inv["app.py"]["package"] == "my-pkg"

    def test_monorepo_multiple_packages(self, tmp_path):
        pkg_a = tmp_path / "pkg_a"
        pkg_a.mkdir()
        (pkg_a / "pyproject.toml").write_text(
            '[project]\nname = "alpha"\nversion = "0.1.0"\n'
        )
        (pkg_a / "mod.py").write_text("class A: pass\n")

        pkg_b = tmp_path / "pkg_b"
        pkg_b.mkdir()
        (pkg_b / "pyproject.toml").write_text(
            '[project]\nname = "beta"\nversion = "0.2.0"\n'
        )
        (pkg_b / "mod.py").write_text("class B: pass\n")

        inv = get_inventory(str(tmp_path))
        assert inv["pkg_a/mod.py"]["package"] == "alpha"
        assert inv["pkg_b/mod.py"]["package"] == "beta"

    def test_setup_py_fallback(self, tmp_path):
        (tmp_path / "setup.py").write_text(
            'from setuptools import setup\nsetup(name="legacy", version="2.0")\n'
        )
        (tmp_path / "lib.py").write_text("class Lib: pass\n")
        inv = get_inventory(str(tmp_path))
        assert inv["lib.py"]["package"] == "legacy"

    def test_no_package_marker(self, tmp_path):
        (tmp_path / "script.py").write_text("class Stuff: pass\n")
        inv = get_inventory(str(tmp_path))
        assert inv["script.py"]["package"] is None

    def test_nested_package_wins(self, tmp_path):
        # Root pyproject
        (tmp_path / "pyproject.toml").write_text(
            '[project]\nname = "root"\nversion = "0.0.1"\n'
        )
        sub = tmp_path / "vendor" / "lib"
        sub.mkdir(parents=True)
        (sub / "pyproject.toml").write_text(
            '[project]\nname = "vendored"\nversion = "3.0"\n'
        )
        (sub / "core.py").write_text("class Core: pass\n")
        (tmp_path / "main.py").write_text("class Main: pass\n")

        inv = get_inventory(str(tmp_path))
        assert inv["vendor/lib/core.py"]["package"] == "vendored"
        assert inv["main.py"]["package"] == "root"


class TestSilentDropReduction:
    """Test that files with only constants, __all__, or private functions are included."""

    def test_constants_only_file_included(self, tmp_path):
        (tmp_path / "settings.py").write_text(textwrap.dedent("""\
            MAX_RETRIES = 3
            DEFAULT_TIMEOUT = 30
        """))
        inv = get_inventory(str(tmp_path))
        assert "settings.py" in inv
        assert len(inv["settings.py"]["constants"]) == 2

    def test_all_only_file_included(self, tmp_path):
        (tmp_path / "__init__.py").write_text(textwrap.dedent("""\
            __all__ = ["Foo", "Bar"]
        """))
        inv = get_inventory(str(tmp_path))
        assert "__init__.py" in inv
        assert inv["__init__.py"].get("has_all") is True

    def test_private_functions_in_deep_mode(self, tmp_path):
        (tmp_path / "helpers.py").write_text(textwrap.dedent("""\
            def _internal_helper():
                pass

            def public_func():
                pass
        """))
        inv = get_inventory(str(tmp_path), deep=True)
        assert "helpers.py" in inv
        fns = inv["helpers.py"]["functions"]
        names = {f["name"] for f in fns}
        assert "_internal_helper" in names
        assert "public_func" in names
        private = [f for f in fns if f["name"] == "_internal_helper"][0]
        assert private.get("private") is True

    def test_private_functions_excluded_in_shallow_mode(self, tmp_path):
        (tmp_path / "helpers.py").write_text(textwrap.dedent("""\
            def _internal_helper():
                pass

            def public_func():
                pass
        """))
        inv = get_inventory(str(tmp_path), deep=False)
        assert "helpers.py" in inv
        fns = inv["helpers.py"]["functions"]
        names = {f["name"] for f in fns}
        assert "_internal_helper" not in names
        assert "public_func" in names

    def test_include_empty_flag(self, tmp_path):
        (tmp_path / "empty.py").write_text("# just a comment\n")
        inv = get_inventory(str(tmp_path), include_empty=True)
        assert "empty.py" in inv

    def test_empty_file_excluded_by_default(self, tmp_path):
        (tmp_path / "empty.py").write_text("# just a comment\n")
        inv = get_inventory(str(tmp_path))
        assert "empty.py" not in inv

    def test_private_only_file_included_in_deep_mode(self, tmp_path):
        (tmp_path / "internal.py").write_text(textwrap.dedent("""\
            def _setup():
                pass

            def _teardown():
                pass
        """))
        inv = get_inventory(str(tmp_path), deep=True)
        assert "internal.py" in inv
        fns = inv["internal.py"]["functions"]
        assert all(f.get("private") for f in fns)
