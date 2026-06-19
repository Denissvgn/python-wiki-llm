"""Tests for commands/extract_cmd.py"""

import ast
import inspect
import json
import threading
import textwrap
import types
from pathlib import Path

import pytest

from llm_wiki_cli.commands import extract_cmd
from llm_wiki_cli.commands.extract_cmd import (
    get_inventory,
    get_call_graph,
    resolve_call_edges,
    _summarize_inventory,
)
from llm_wiki_cli.config import PathValidationError
from llm_wiki_cli.extractors.python_extractor import PythonExtractor
from llm_wiki_cli.services.inventory_cache import InventoryCacheOptions
from llm_wiki_cli.services.packages import discover_packages, stamp_inventory_packages
from llm_wiki_cli.services.source_snapshot import build_source_snapshot


def _body_line_count(function) -> int:
    source = textwrap.dedent(inspect.getsource(function))
    function_node = ast.parse(source).body[0]
    body = function_node.body
    first_body_line = min(stmt.lineno for stmt in body)
    last_body_line = max(stmt.end_lineno for stmt in body)
    return last_body_line - first_body_line + 1


class TestGetInventory:
    def test_get_inventory_result_uses_request_object(self):
        signature = inspect.signature(extract_cmd.get_inventory_result)

        assert len(signature.parameters) <= 3
        assert not {
            "deep",
            "only_files",
            "include_empty",
            "source_snapshot",
            "cache_options",
            "parallel_jobs",
        } & set(signature.parameters)

    def test_inventory_result_builder_stays_small(self):
        assert _body_line_count(extract_cmd.get_inventory_result) <= 20
        assert _body_line_count(extract_cmd._build_inventory_result) <= 45

    def test_get_inventory_result_accepts_request_object(self, tmp_path):
        (tmp_path / "app.py").write_text("class App: pass\n", encoding="utf-8")

        result = extract_cmd.get_inventory_result(
            extract_cmd.InventoryRequest(src_dir=str(tmp_path), deep=True)
        )

        assert sorted(result.inventory) == ["app.py"]

    def test_empty_dir(self, tmp_path):
        inventory = get_inventory(str(tmp_path))
        assert inventory == {}

    def test_single_file_with_class(self, tmp_path):
        (tmp_path / "models.py").write_text(
            textwrap.dedent("""\
            class Foo:
                pass
        """)
        )
        inventory = get_inventory(str(tmp_path))
        assert len(inventory) == 1
        data = list(inventory.values())[0]
        assert len(data["classes"]) == 1
        assert data["classes"][0]["name"] == "Foo"

    def test_get_inventory_result_builds_snapshot_once_and_passes_source_files(
        self, tmp_path, monkeypatch
    ):
        (tmp_path / "b.py").write_text("class B: pass\n")
        (tmp_path / "a.py").write_text("class A: pass\n")
        real_build_source_snapshot = extract_cmd.build_source_snapshot
        calls = {"snapshot": 0, "source_files": None}

        def fake_build_source_snapshot(*args, **kwargs):
            calls["snapshot"] += 1
            return real_build_source_snapshot(*args, **kwargs)

        class FakePythonExtractor:
            last_error = None

            def extract(
                self,
                src_dir,
                only_files=None,
                deep=False,
                include_empty=False,
                source_files=None,
            ):
                calls["source_files"] = source_files
                return {
                    rel: {"classes": [], "functions": [], "language": "python"}
                    for rel in source_files
                }

        monkeypatch.setattr(
            extract_cmd, "build_source_snapshot", fake_build_source_snapshot
        )
        monkeypatch.setattr(
            extract_cmd, "_load_extractor", lambda _entry_point: FakePythonExtractor()
        )

        result = extract_cmd.get_inventory_result(str(tmp_path))

        assert calls["snapshot"] == 1
        assert calls["source_files"] == ["a.py", "b.py"]
        assert sorted(result.inventory) == ["a.py", "b.py"]

    def test_builtin_go_extractor_receives_request_object(self, tmp_path, monkeypatch):
        (tmp_path / "main.go").write_text("package main\n", encoding="utf-8")
        calls = {"request": None, "only_files": "unset", "deep": "unset"}

        class FakeGoExtractor:
            last_error = None

            def extract(self, src_dir, only_files=None, deep=False):
                calls["request"] = src_dir
                calls["only_files"] = only_files
                calls["deep"] = deep
                return {
                    "main.go": {
                        "classes": [],
                        "functions": [],
                        "language": "go",
                    }
                }

        monkeypatch.setattr(
            extract_cmd,
            "get_extractor_registry",
            lambda: {"go": extract_cmd.EXTRACTOR_REGISTRY["go"]},
        )
        monkeypatch.setattr(
            extract_cmd, "_load_extractor", lambda _entry_point: FakeGoExtractor()
        )

        result = extract_cmd.get_inventory_result(str(tmp_path), deep=True)

        request = calls["request"]
        assert isinstance(request, extract_cmd.GoExtractionRequest)
        assert request.src_dir == str(tmp_path)
        assert request.deep is True
        assert request.source_files == ["main.go"]
        assert request.helper_cache_dir is None
        assert calls["only_files"] is None
        assert calls["deep"] is False
        assert sorted(result.inventory) == ["main.go"]

    def test_builtin_rust_extractor_receives_request_object(
        self, tmp_path, monkeypatch
    ):
        (tmp_path / "lib.rs").write_text("pub struct App;\n", encoding="utf-8")
        calls = {"request": None, "only_files": "unset", "deep": "unset"}

        class FakeRustExtractor:
            last_error = None

            def extract(self, src_dir, only_files=None, deep=False):
                calls["request"] = src_dir
                calls["only_files"] = only_files
                calls["deep"] = deep
                return {
                    "lib.rs": {
                        "classes": [],
                        "functions": [],
                        "language": "rust",
                    }
                }

        monkeypatch.setattr(
            extract_cmd,
            "get_extractor_registry",
            lambda: {"rust": extract_cmd.EXTRACTOR_REGISTRY["rust"]},
        )
        monkeypatch.setattr(
            extract_cmd,
            "_load_extractor",
            lambda _entry_point: FakeRustExtractor(),
        )

        result = extract_cmd.get_inventory_result(str(tmp_path), deep=True)

        request = calls["request"]
        assert isinstance(request, extract_cmd.RustExtractionRequest)
        assert request.src_dir == str(tmp_path)
        assert request.deep is True
        assert request.source_files == ["lib.rs"]
        assert request.helper_cache_dir is None
        assert calls["only_files"] is None
        assert calls["deep"] is False
        assert sorted(result.inventory) == ["lib.rs"]

    def test_parallel_jobs_run_fresh_builtin_extractors_concurrently(
        self, tmp_path, monkeypatch
    ):
        (tmp_path / "app.py").write_text("class App: pass\n", encoding="utf-8")
        (tmp_path / "app.ts").write_text("export class TsApp {}\n", encoding="utf-8")

        registry = {
            "python": extract_cmd.EXTRACTOR_REGISTRY["python"],
            "typescript": extract_cmd.EXTRACTOR_REGISTRY["typescript"],
        }
        started: set[str] = set()
        both_started = threading.Event()
        lock = threading.Lock()
        created: list[str] = []

        class FakeExtractor:
            def __init__(self, language):
                self.language = language
                self.last_error = None

            def extract(self, **kwargs):
                with lock:
                    started.add(self.language)
                    if len(started) == 2:
                        both_started.set()
                if not both_started.wait(timeout=2):
                    raise AssertionError("built-in extractors did not run concurrently")
                rel_path = kwargs["source_files"][0]
                return {
                    rel_path: {
                        "language": self.language,
                        "classes": [{"name": self.language.title()}],
                        "functions": [],
                    }
                }

        def fake_instantiate(entry_point):
            language = "python" if "python_extractor" in entry_point else "typescript"
            created.append(language)
            return FakeExtractor(language)

        monkeypatch.setattr(extract_cmd, "get_extractor_registry", lambda: registry)
        monkeypatch.setattr(extract_cmd, "_instantiate_extractor", fake_instantiate)
        monkeypatch.setattr(
            extract_cmd,
            "_load_extractor",
            lambda _entry_point: pytest.fail(
                "parallel built-ins should use fresh instances"
            ),
        )

        result = extract_cmd.get_inventory_result(str(tmp_path), parallel_jobs=2)

        assert not result.failed
        assert sorted(created) == ["python", "typescript"]
        assert sorted(result.inventory) == ["app.py", "app.ts"]

    def test_parallel_jobs_keep_plugins_sequential(self, tmp_path, monkeypatch):
        (tmp_path / "app.py").write_text("class App: pass\n", encoding="utf-8")
        registry = {
            "python": extract_cmd.EXTRACTOR_REGISTRY["python"],
            "custom": "plugin.extractor:CustomExtractor",
        }
        calls: list[str] = []

        class BuiltinExtractor:
            last_error = None

            def extract(self, **kwargs):
                calls.append("builtin")
                return {
                    "app.py": {"language": "python", "classes": [], "functions": []}
                }

        class PluginExtractor:
            last_error = None

            def extract(self, **kwargs):
                calls.append("plugin")
                return {
                    "virtual.custom": {
                        "language": "custom",
                        "classes": [],
                        "functions": [],
                    }
                }

        monkeypatch.setattr(extract_cmd, "get_extractor_registry", lambda: registry)
        monkeypatch.setattr(
            extract_cmd,
            "_instantiate_extractor",
            lambda _entry_point: BuiltinExtractor(),
        )
        monkeypatch.setattr(
            extract_cmd, "_load_extractor", lambda _entry_point: PluginExtractor()
        )

        result = extract_cmd.get_inventory_result(str(tmp_path), parallel_jobs=2)

        assert calls == ["builtin", "plugin"]
        assert result.statuses["custom"].files_found == 1

    def test_parallel_jobs_run_parallel_safe_plugin_extractors_concurrently(
        self, tmp_path, monkeypatch
    ):
        (tmp_path / "app.py").write_text("class App: pass\n", encoding="utf-8")
        registry = {
            "python": extract_cmd.EXTRACTOR_REGISTRY["python"],
            "custom": "plugin.extractor:CustomExtractor",
        }
        started: set[str] = set()
        both_started = threading.Event()
        lock = threading.Lock()
        created: list[str] = []

        class FakeExtractor:
            def __init__(self, language):
                self.language = language
                self.last_error = None

            def extract(self, **kwargs):
                with lock:
                    started.add(self.language)
                    if len(started) == 2:
                        both_started.set()
                if not both_started.wait(timeout=2):
                    raise AssertionError(
                        "parallel-safe plugin did not run concurrently"
                    )
                if self.language == "python":
                    return {
                        "app.py": {
                            "language": "python",
                            "classes": [],
                            "functions": [],
                        }
                    }
                return {
                    "virtual.custom": {
                        "language": "custom",
                        "classes": [],
                        "functions": [],
                    }
                }

        def fake_instantiate(entry_point):
            language = "custom" if entry_point.startswith("plugin.") else "python"
            created.append(language)
            return FakeExtractor(language)

        monkeypatch.setattr(extract_cmd, "get_extractor_registry", lambda: registry)
        monkeypatch.setattr(
            extract_cmd,
            "parallel_safe_extractor_entry_points",
            lambda: {"plugin.extractor:CustomExtractor"},
            raising=False,
        )
        monkeypatch.setattr(extract_cmd, "_instantiate_extractor", fake_instantiate)
        monkeypatch.setattr(
            extract_cmd,
            "_load_extractor",
            lambda _entry_point: pytest.fail(
                "parallel-safe plugins should use fresh instances"
            ),
        )

        result = extract_cmd.get_inventory_result(str(tmp_path), parallel_jobs=2)

        assert not result.failed
        assert sorted(created) == ["custom", "python"]
        assert sorted(result.inventory) == ["app.py", "virtual.custom"]

    def test_parallel_inventory_merge_order_is_deterministic(
        self, tmp_path, monkeypatch
    ):
        (tmp_path / "b.py").write_text("class B: pass\n", encoding="utf-8")
        (tmp_path / "a.py").write_text("class A: pass\n", encoding="utf-8")
        (tmp_path / "z.ts").write_text("export class Z {}\n", encoding="utf-8")
        registry = {
            "python": extract_cmd.EXTRACTOR_REGISTRY["python"],
            "typescript": extract_cmd.EXTRACTOR_REGISTRY["typescript"],
        }

        class FakeExtractor:
            def __init__(self, language):
                self.language = language
                self.last_error = None

            def extract(self, **kwargs):
                return {
                    rel_path: {
                        "language": self.language,
                        "classes": [],
                        "functions": [],
                    }
                    for rel_path in reversed(kwargs["source_files"])
                }

        def fake_instantiate(entry_point):
            language = "python" if "python_extractor" in entry_point else "typescript"
            return FakeExtractor(language)

        monkeypatch.setattr(extract_cmd, "get_extractor_registry", lambda: registry)
        monkeypatch.setattr(extract_cmd, "_instantiate_extractor", fake_instantiate)

        result = extract_cmd.get_inventory_result(str(tmp_path), parallel_jobs=2)

        assert list(result.inventory) == ["a.py", "b.py", "z.ts"]

    def test_cp1252_python_file_does_not_abort_scan(self, tmp_path):
        (tmp_path / "legacy.py").write_bytes(
            b"# legacy \x96 comment\nclass Legacy:\n    pass\n"
        )
        inventory = get_inventory(str(tmp_path))
        assert "legacy.py" in inventory
        assert inventory["legacy.py"]["classes"][0]["name"] == "Legacy"

    def test_single_file_with_function(self, tmp_path):
        (tmp_path / "utils.py").write_text(
            textwrap.dedent("""\
            def hello():
                pass
        """)
        )
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

    def test_skips_virtualenv_layout_with_custom_name(self, tmp_path):
        site_packages = (
            tmp_path / "custom-python" / "lib" / "python3.13" / "site-packages"
        )
        site_packages.mkdir(parents=True)
        (site_packages / "dependency.py").write_text("class Hidden: pass\n")
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
        (tmp_path / "models.py").write_text(
            textwrap.dedent("""\
            class Foo:
                \"\"\"A foo class.\"\"\"
                name: str
                value: int = 42
        """)
        )
        inventory = get_inventory(str(tmp_path), deep=True)
        data = list(inventory.values())[0]
        cls = data["classes"][0]
        assert cls["docstring"] == "A foo class."
        assert len(cls["attributes"]) == 2
        assert cls["attributes"][0]["name"] == "name"
        assert cls["attributes"][0]["type"] == "str"
        assert cls["attributes"][1]["default"] == "42"

    def test_deep_mode_includes_imports(self, tmp_path):
        (tmp_path / "main.py").write_text(
            textwrap.dedent("""\
            from pathlib import Path
            import os

            def run():
                pass
        """)
        )
        inventory = get_inventory(str(tmp_path), deep=True)
        data = list(inventory.values())[0]
        assert "imports" in data
        import_names = {imp["name"] for imp in data["imports"]}
        assert "Path" in import_names
        assert "os" in import_names

    def test_deep_mode_preserves_relative_import_level(self, tmp_path):
        pkg = tmp_path / "pkg" / "sub"
        pkg.mkdir(parents=True)
        (pkg / "consumer.py").write_text(
            textwrap.dedent("""\
            from .models import Local
            from ..models import Parent

            def run(local: Local, parent: Parent):
                return local, parent
        """)
        )
        inventory = get_inventory(str(tmp_path), deep=True)
        imports = inventory["pkg/sub/consumer.py"]["imports"]
        modules = {imp["name"]: imp["module"] for imp in imports}
        assert modules["Local"] == ".models"
        assert modules["Parent"] == "..models"

    def test_deep_mode_includes_methods(self, tmp_path):
        (tmp_path / "svc.py").write_text(
            textwrap.dedent("""\
            class Service:
                def start(self, port: int) -> bool:
                    \"\"\"Start the service.\"\"\"
                    return True

                async def stop(self):
                    pass
        """)
        )
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
        (tmp_path / "models.py").write_text(
            textwrap.dedent("""\
            class Foo:
                \"\"\"A foo class.\"\"\"
                name: str

            def helper():
                pass
        """)
        )
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
        (tmp_path / "api.py").write_text(
            textwrap.dedent("""\
            def app_get(path):
                def decorator(fn):
                    return fn
                return decorator

            class Controller:
                @app_get("/users")
                def list_users(self):
                    pass
        """)
        )
        inventory = get_inventory(str(tmp_path), deep=True)
        cls = list(inventory.values())[0]["classes"][0]
        method = cls["methods"][0]
        assert len(method["decorators"]) == 1
        assert "app_get" in method["decorators"][0]

    def test_private_functions_excluded(self, tmp_path):
        (tmp_path / "mod.py").write_text(
            textwrap.dedent("""\
            def public():
                pass

            def _private():
                pass

            class C:
                pass
        """)
        )
        inventory = get_inventory(str(tmp_path), deep=True)
        data = list(inventory.values())[0]
        fn_names = [f["name"] for f in data["functions"]]
        assert "public" in fn_names
        # In deep mode, private functions are included but tagged
        assert "_private" in fn_names
        private_fn = [f for f in data["functions"] if f["name"] == "_private"][0]
        assert private_fn.get("private") is True

    def test_nested_functions_are_not_module_functions(self, tmp_path):
        (tmp_path / "mod.py").write_text(
            textwrap.dedent("""\
            def outer():
                def inner():
                    pass
                return inner
        """)
        )
        inventory = get_inventory(str(tmp_path), deep=True)
        functions = list(inventory.values())[0]["functions"]
        assert [fn["name"] for fn in functions] == ["outer"]

    def test_class_inside_function_is_not_module_entity(self, tmp_path):
        (tmp_path / "factory.py").write_text(
            textwrap.dedent("""\
            def make_model():
                class LocalModel:
                    pass
                return LocalModel
        """)
        )
        inventory = get_inventory(str(tmp_path), deep=True)
        data = list(inventory.values())[0]
        assert data["classes"] == []
        assert [fn["name"] for fn in data["functions"]] == ["make_model"]


class TestCallCapture:
    def test_deep_mode_captures_body_calls(self, tmp_path):
        (tmp_path / "m.py").write_text(
            textwrap.dedent("""\
            def helper():
                return 1

            def run():
                value = helper()
                return value
        """)
        )
        inventory = get_inventory(str(tmp_path), deep=True)
        functions = {fn["name"]: fn for fn in inventory["m.py"]["functions"]}
        assert "helper" in {c["name"] for c in functions["run"]["calls"]}
        # Field is omitted for a body that makes no nameable calls.
        assert "calls" not in functions["helper"]

    def test_attribute_call_records_dotted_path(self, tmp_path):
        (tmp_path / "m.py").write_text(
            textwrap.dedent("""\
            import os

            def run():
                return os.getcwd()
        """)
        )
        inventory = get_inventory(str(tmp_path), deep=True)
        call = inventory["m.py"]["functions"][0]["calls"][0]
        assert call["name"] == "getcwd"
        assert call["attr"] == "os.getcwd"

    def test_comprehension_and_lambda_calls_are_kept(self, tmp_path):
        (tmp_path / "m.py").write_text(
            textwrap.dedent("""\
            def transform(xs):
                doubled = [scale(x) for x in xs]
                fn = lambda y: clamp(y)
                return doubled, fn
        """)
        )
        inventory = get_inventory(str(tmp_path), deep=True)
        names = {c["name"] for c in inventory["m.py"]["functions"][0]["calls"]}
        assert {"scale", "clamp"} <= names

    def test_nested_definition_calls_do_not_leak(self, tmp_path):
        (tmp_path / "m.py").write_text(
            textwrap.dedent("""\
            def outer():
                setup()
                def inner():
                    leaked()
                return inner
        """)
        )
        inventory = get_inventory(str(tmp_path), deep=True)
        outer = next(
            fn for fn in inventory["m.py"]["functions"] if fn["name"] == "outer"
        )
        names = {c["name"] for c in outer["calls"]}
        assert "setup" in names
        assert "leaked" not in names

    def test_calls_are_deduplicated_in_source_order(self, tmp_path):
        (tmp_path / "m.py").write_text(
            textwrap.dedent("""\
            def run():
                first()
                second()
                first()
        """)
        )
        inventory = get_inventory(str(tmp_path), deep=True)
        run = inventory["m.py"]["functions"][0]
        assert [c["name"] for c in run["calls"]] == ["first", "second"]

    def test_slim_mode_omits_calls(self, tmp_path):
        (tmp_path / "m.py").write_text(
            textwrap.dedent("""\
            def run():
                helper()

            def helper():
                pass
        """)
        )
        inventory = get_inventory(str(tmp_path), deep=False)
        assert all("calls" not in fn for fn in inventory["m.py"]["functions"])

    def test_method_bodies_capture_calls(self, tmp_path):
        (tmp_path / "m.py").write_text(
            textwrap.dedent("""\
            class Svc:
                def run(self):
                    return self.helper()

                def helper(self):
                    return 1
        """)
        )
        inventory = get_inventory(str(tmp_path), deep=True)
        method = inventory["m.py"]["classes"][0]["methods"][0]
        assert method["calls"][0] == {
            "name": "helper",
            "attr": "self.helper",
            "line": 3,
        }


class TestModuleCalls:
    def test_assignment_call_records_target(self, tmp_path):
        (tmp_path / "m.py").write_text(
            textwrap.dedent("""\
            from flask import Flask

            app = Flask(__name__)
        """)
        )
        data = get_inventory(str(tmp_path), deep=True)["m.py"]
        assert data["module_calls"] == [{"name": "Flask", "target": "app", "line": 3}]

    def test_bare_expression_call_recorded(self, tmp_path):
        (tmp_path / "m.py").write_text(
            textwrap.dedent("""\
            import logging

            configure()
            logging.basicConfig(level=logging.INFO)
        """)
        )
        calls = get_inventory(str(tmp_path), deep=True)["m.py"]["module_calls"]
        assert calls == [
            {"name": "configure", "line": 3},
            {"name": "basicConfig", "attr": "logging.basicConfig", "line": 4},
        ]

    def test_annotated_assignment_call_records_target(self, tmp_path):
        (tmp_path / "m.py").write_text(
            textwrap.dedent("""\
            from flask import Flask

            app: Flask = Flask(__name__)
        """)
        )
        calls = get_inventory(str(tmp_path), deep=True)["m.py"]["module_calls"]
        assert calls == [{"name": "Flask", "target": "app", "line": 3}]

    def test_pure_constants_imports_and_defs_are_not_side_effects(self, tmp_path):
        (tmp_path / "m.py").write_text(
            textwrap.dedent("""\
            import os

            MAX_RETRIES = 3
            NAME = "x"

            def run():
                return helper()

            class Service:
                started = build()
        """)
        )
        assert "module_calls" not in get_inventory(str(tmp_path), deep=True)["m.py"]

    def test_calls_inside_def_and_main_guard_are_not_module_calls(self, tmp_path):
        (tmp_path / "m.py").write_text(
            textwrap.dedent("""\
            def main():
                leaked()

            if __name__ == "__main__":
                main()
        """)
        )
        assert "module_calls" not in get_inventory(str(tmp_path), deep=True)["m.py"]

    def test_module_calls_omitted_in_slim_mode(self, tmp_path):
        (tmp_path / "m.py").write_text(
            "app = Flask(__name__)\n\n\ndef run():\n    pass\n"
        )
        assert "module_calls" not in get_inventory(str(tmp_path), deep=False)["m.py"]

    def test_side_effect_only_module_is_included_in_deep_mode(self, tmp_path):
        # A defless module that only wires up at import time is still content.
        (tmp_path / "wiring.py").write_text("import logging\n\nlogging.basicConfig()\n")
        deep = get_inventory(str(tmp_path), deep=True)
        assert "wiring.py" in deep
        assert deep["wiring.py"]["module_calls"][0]["name"] == "basicConfig"
        # ...but a slim scan keeps dropping defless modules.
        assert "wiring.py" not in get_inventory(str(tmp_path), deep=False)

    def test_module_calls_preserve_source_order(self, tmp_path):
        (tmp_path / "m.py").write_text(
            textwrap.dedent("""\
            register()
            app = create_app()
            wire()
        """)
        )
        names = [
            c["name"]
            for c in get_inventory(str(tmp_path), deep=True)["m.py"]["module_calls"]
        ]
        assert names == ["register", "create_app", "wire"]


class TestEntryPointSignals:
    def test_deep_captures_all_exports(self, tmp_path):
        (tmp_path / "api.py").write_text(
            textwrap.dedent("""\
            __all__ = ["run", "Service"]

            def run():
                pass

            class Service:
                pass
        """)
        )
        data = get_inventory(str(tmp_path), deep=True)["api.py"]
        assert data["all_exports"] == ["run", "Service"]
        assert data["has_all"] is True

    def test_all_exports_omitted_without_dunder_all(self, tmp_path):
        (tmp_path / "m.py").write_text("def run():\n    pass\n")
        assert "all_exports" not in get_inventory(str(tmp_path), deep=True)["m.py"]

    def test_deep_captures_main_block(self, tmp_path):
        (tmp_path / "cli.py").write_text(
            textwrap.dedent("""\
            def main():
                pass

            if __name__ == "__main__":
                main()
        """)
        )
        assert get_inventory(str(tmp_path), deep=True)["cli.py"]["main_block"] is True

    def test_main_block_omitted_when_absent(self, tmp_path):
        (tmp_path / "m.py").write_text("def main():\n    pass\n")
        assert "main_block" not in get_inventory(str(tmp_path), deep=True)["m.py"]

    def test_deep_captures_decorated_nested_functions(self, tmp_path):
        (tmp_path / "factory.py").write_text(
            textwrap.dedent("""\
            def create_server():
                server = make()

                @server.tool()
                def get_entity(entity_id):
                    return service.get(entity_id)

                def _helper():
                    return 1

                return server
        """)
        )
        data = get_inventory(str(tmp_path), deep=True)["factory.py"]
        nested = {fn["name"] for fn in data.get("nested_functions", [])}
        assert "get_entity" in nested  # decorated -> captured
        assert "_helper" not in nested  # undecorated nested -> not captured
        # nested functions are not surfaced as module-level functions
        assert "get_entity" not in {fn["name"] for fn in data["functions"]}

    def test_nested_functions_omitted_when_undecorated_or_slim(self, tmp_path):
        (tmp_path / "m.py").write_text(
            "def run():\n    def inner():\n        pass\n    return inner\n"
        )
        assert "nested_functions" not in get_inventory(str(tmp_path), deep=True)["m.py"]
        (tmp_path / "d.py").write_text(
            "def f():\n    @x.tool()\n    def g():\n        pass\n    return g\n"
        )
        assert (
            "nested_functions" not in get_inventory(str(tmp_path), deep=False)["d.py"]
        )

    def test_slim_mode_omits_entry_signals(self, tmp_path):
        (tmp_path / "api.py").write_text(
            textwrap.dedent("""\
            __all__ = ["run"]

            def run():
                pass

            if __name__ == "__main__":
                run()
        """)
        )
        data = get_inventory(str(tmp_path), deep=False)["api.py"]
        assert "all_exports" not in data
        assert "main_block" not in data


class TestExtractEntryPoints:
    def test_deep_payload_includes_entrypoints(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        (tmp_path / "api.py").write_text(
            '__all__ = ["run"]\n\n\ndef run():\n    return 1\n'
        )
        result = extract_cmd.build_extract_payload(".", deep=True)
        ids = {e["id"] for e in result.payload["entrypoints"]}
        assert "api-run" in ids

    def test_non_deep_payload_omits_entrypoints(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        (tmp_path / "api.py").write_text(
            '__all__ = ["run"]\n\n\ndef run():\n    return 1\n'
        )
        result = extract_cmd.build_extract_payload(".", deep=False)
        assert "entrypoints" not in result.payload


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


class TestExtractPathValidation:
    def test_run_rejects_src_dir_outside_project(self, tmp_project, tmp_path):
        outside = tmp_path / "outside"
        outside.mkdir()

        args = types.SimpleNamespace(
            src_dir=str(outside),
            changed=False,
            summary=False,
            deep=False,
            paths=None,
            package=None,
            include_empty=False,
        )
        with pytest.raises(PathValidationError):
            extract_cmd.run(args)

    def test_run_allows_external_src_with_explicit_flag(
        self, tmp_project, tmp_path, capsys
    ):
        outside = tmp_path / "outside"
        outside.mkdir()
        (outside / "external.py").write_text("class External: pass\n", encoding="utf-8")

        args = types.SimpleNamespace(
            src_dir=str(outside),
            changed=False,
            summary=False,
            deep=False,
            paths=None,
            package=None,
            include_empty=False,
            output=None,
            read_only=True,
            allow_external_src=True,
        )

        extract_cmd.run(args)

        data = json.loads(capsys.readouterr().out)
        assert data["schema_version"] == "llm-wiki-extract/v1"
        assert set(data["inventory"]) == {"external.py"}

    def test_run_writes_output_path_without_stdout(self, tmp_project, tmp_path, capsys):
        out_path = tmp_path / "records" / "extract.json"
        args = types.SimpleNamespace(
            src_dir=".",
            changed=False,
            summary=True,
            deep=False,
            paths=None,
            package=None,
            include_empty=False,
            output=str(out_path),
            read_only=True,
            allow_external_src=False,
        )

        extract_cmd.run(args)

        captured = capsys.readouterr()
        assert captured.out == ""
        data = json.loads(out_path.read_text(encoding="utf-8"))
        assert data["schema_version"] == "llm-wiki-extract/v1"
        assert data["inventory"]
        first = next(iter(data["inventory"].values()))
        assert "language" in first

    def test_read_only_extract_does_not_create_wiki_artifacts(
        self, tmp_project, capsys
    ):
        args = types.SimpleNamespace(
            src_dir=".",
            changed=False,
            summary=False,
            deep=False,
            paths=None,
            package=None,
            include_empty=False,
            output=None,
            read_only=True,
            allow_external_src=False,
        )

        extract_cmd.run(args)

        assert not Path("docs").exists()
        assert not Path(".llm-wiki").exists()


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
    def test_get_call_graph_stays_decomposed(self):
        assert _body_line_count(get_call_graph) <= 35

    def test_no_workflows_single_module(self, tmp_path):
        (tmp_path / "simple.py").write_text("class Foo: pass\n")
        inventory = get_inventory(str(tmp_path), deep=True)
        graph = get_call_graph(inventory)
        assert graph == {}

    def test_no_workflows_below_threshold(self, tmp_path):
        """Two modules don't meet the 3-module threshold."""
        (tmp_path / "a.py").write_text("class A: pass\n")
        (tmp_path / "b.py").write_text(
            textwrap.dedent("""\
            from a import A

            def use_a(x: A) -> A:
                return x
        """)
        )
        inventory = get_inventory(str(tmp_path), deep=True)
        graph = get_call_graph(inventory)
        assert graph == {}

    def test_workflow_tracks_exact_paths_for_colliding_module_stems(self, tmp_path):
        (tmp_path / "models").mkdir()
        (tmp_path / "schemas").mkdir()
        (tmp_path / "routers").mkdir()
        (tmp_path / "models" / "task.py").write_text("class Task:\n    pass\n")
        (tmp_path / "schemas" / "task.py").write_text("class TaskCreate:\n    pass\n")
        (tmp_path / "schemas" / "common.py").write_text(
            "class MessageResponse:\n    pass\n"
        )
        (tmp_path / "routers" / "tasks.py").write_text(
            textwrap.dedent("""\
            from models.task import Task
            from schemas.task import TaskCreate as CreateSchema
            from schemas.common import MessageResponse

            def create_task(task: Task, data: CreateSchema) -> MessageResponse:
                return MessageResponse()
        """)
        )

        inventory = get_inventory(str(tmp_path), deep=True)
        graph = get_call_graph(inventory)

        workflow = graph["create_task"]
        assert workflow["entry_module_path"] == "routers/tasks.py"
        assert set(workflow["modules_touched_paths"]) == {
            "models/task.py",
            "schemas/common.py",
            "schemas/task.py",
            "routers/tasks.py",
        }


class TestResolveCallEdges:
    def test_resolver_stays_decomposed(self):
        assert _body_line_count(resolve_call_edges) <= 35

    def test_tolerates_inventory_without_calls(self):
        inventory = {"m.py": {"functions": [{"name": "f", "line": 1}], "classes": []}}
        assert resolve_call_edges(inventory) == []

    def test_resolves_imported_project_symbol(self, tmp_path):
        (tmp_path / "a.py").write_text("def helper():\n    return 1\n")
        (tmp_path / "b.py").write_text(
            textwrap.dedent("""\
            from a import helper

            def run():
                return helper()
        """)
        )
        inventory = get_inventory(str(tmp_path), deep=True)
        edge = next(
            e for e in resolve_call_edges(inventory) if e["from"]["symbol"] == "run"
        )
        assert edge["to"] == {"file": "a.py", "symbol": "helper"}
        assert edge["kind"] == "internal"

    def test_resolves_self_method_call(self, tmp_path):
        (tmp_path / "svc.py").write_text(
            textwrap.dedent("""\
            class Svc:
                def run(self):
                    return self.helper()

                def helper(self):
                    return 1
        """)
        )
        inventory = get_inventory(str(tmp_path), deep=True)
        edge = next(
            e for e in resolve_call_edges(inventory) if e["from"]["symbol"] == "Svc.run"
        )
        assert edge["to"] == {"file": "svc.py", "symbol": "Svc.helper"}
        assert edge["kind"] == "internal"

    def test_resolves_same_file_symbol(self, tmp_path):
        (tmp_path / "m.py").write_text(
            textwrap.dedent("""\
            def run():
                return helper()

            def helper():
                return 1
        """)
        )
        inventory = get_inventory(str(tmp_path), deep=True)
        edge = next(
            e for e in resolve_call_edges(inventory) if e["from"]["symbol"] == "run"
        )
        assert edge["to"] == {"file": "m.py", "symbol": "helper"}
        assert edge["kind"] == "internal"

    def test_tags_external_import_call(self, tmp_path):
        (tmp_path / "m.py").write_text(
            textwrap.dedent("""\
            import os

            def run():
                return os.getcwd()
        """)
        )
        inventory = get_inventory(str(tmp_path), deep=True)
        edge = next(
            e for e in resolve_call_edges(inventory) if e["name"] == "os.getcwd"
        )
        assert edge["kind"] == "external"
        assert edge["to"]["file"] is None

    def test_tags_unresolved_call(self, tmp_path):
        (tmp_path / "m.py").write_text(
            textwrap.dedent("""\
            def run():
                return mystery()
        """)
        )
        inventory = get_inventory(str(tmp_path), deep=True)
        edge = next(e for e in resolve_call_edges(inventory) if e["name"] == "mystery")
        assert edge["kind"] == "unresolved"
        assert edge["to"]["file"] is None


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

    def test_respects_excluded_dirs(self, tmp_path):
        hidden = tmp_path / ".venv" / "lib" / "hidden.py"
        hidden.parent.mkdir(parents=True)
        hidden.write_text("class Hidden: pass\n")
        inventory = get_inventory(str(tmp_path), only_files=[".venv/lib/hidden.py"])
        assert inventory == {}


class TestInventoryCache:
    def _cache_options(self, tmp_path, *, rebuild=False):
        return InventoryCacheOptions(
            enabled=True,
            rebuild=rebuild,
            cache_dir=str(tmp_path / "cache"),
            stats_enabled=True,
        )

    def test_warm_cache_reuses_python_without_extractor(self, tmp_path, monkeypatch):
        (tmp_path / "app.py").write_text("class App: pass\n", encoding="utf-8")
        options = self._cache_options(tmp_path)

        first = extract_cmd.get_inventory_result(
            str(tmp_path), deep=True, cache_options=options
        )
        assert first.inventory["app.py"]["classes"][0]["name"] == "App"

        def fail_load(_entry_point):
            raise AssertionError("warm cache should not load the Python extractor")

        monkeypatch.setattr(extract_cmd, "_load_extractor", fail_load)
        second = extract_cmd.get_inventory_result(
            str(tmp_path), deep=True, cache_options=options
        )

        assert second.inventory["app.py"]["classes"][0]["name"] == "App"
        assert second.cache_stats.hits == 1
        assert second.cache_stats.fresh_extracted == 0

    def test_changed_file_invalidates_only_that_file(self, tmp_path, monkeypatch):
        (tmp_path / "a.py").write_text("class A: pass\n", encoding="utf-8")
        (tmp_path / "b.py").write_text("class B: pass\n", encoding="utf-8")
        options = self._cache_options(tmp_path)
        extract_cmd.get_inventory_result(
            str(tmp_path), deep=True, cache_options=options
        )
        (tmp_path / "b.py").write_text("class B2: pass\n", encoding="utf-8")
        calls = []

        class FakePythonExtractor:
            last_error = None

            def extract(
                self,
                src_dir,
                only_files=None,
                deep=False,
                include_empty=False,
                source_files=None,
            ):
                calls.append(list(source_files))
                return {
                    "b.py": {
                        "language": "python",
                        "classes": [{"name": "B2", "line": 1, "bases": []}],
                        "functions": [],
                    }
                }

        monkeypatch.setattr(
            extract_cmd, "_load_extractor", lambda _entry_point: FakePythonExtractor()
        )
        monkeypatch.setattr(
            extract_cmd,
            "_instantiate_extractor",
            lambda _entry_point: FakePythonExtractor(),
        )
        result = extract_cmd.get_inventory_result(
            str(tmp_path), deep=True, cache_options=options, parallel_jobs=2
        )

        assert calls == [["b.py"]]
        assert result.inventory["a.py"]["classes"][0]["name"] == "A"
        assert result.inventory["b.py"]["classes"][0]["name"] == "B2"
        assert result.cache_stats.hits == 1
        assert result.cache_stats.changed == 1

    def test_deleted_file_disappears_from_merged_inventory(self, tmp_path, monkeypatch):
        (tmp_path / "a.py").write_text("class A: pass\n", encoding="utf-8")
        (tmp_path / "b.py").write_text("class B: pass\n", encoding="utf-8")
        options = self._cache_options(tmp_path)
        extract_cmd.get_inventory_result(
            str(tmp_path), deep=True, cache_options=options
        )
        (tmp_path / "b.py").unlink()

        def fail_load(_entry_point):
            raise AssertionError("unchanged remaining file should be cached")

        monkeypatch.setattr(extract_cmd, "_load_extractor", fail_load)
        result = extract_cmd.get_inventory_result(
            str(tmp_path), deep=True, cache_options=options
        )

        assert sorted(result.inventory) == ["a.py"]
        assert result.cache_stats.deleted == 1

    def test_package_marker_change_restamps_cached_entry(self, tmp_path, monkeypatch):
        (tmp_path / "pyproject.toml").write_text(
            '[project]\nname = "old"\n', encoding="utf-8"
        )
        (tmp_path / "app.py").write_text("class App: pass\n", encoding="utf-8")
        options = self._cache_options(tmp_path)
        first = extract_cmd.get_inventory_result(
            str(tmp_path), deep=True, cache_options=options
        )
        assert first.inventory["app.py"]["package"] == "old"
        (tmp_path / "pyproject.toml").write_text(
            '[project]\nname = "new"\n', encoding="utf-8"
        )

        def fail_load(_entry_point):
            raise AssertionError("source file should be served from cache")

        monkeypatch.setattr(extract_cmd, "_load_extractor", fail_load)
        second = extract_cmd.get_inventory_result(
            str(tmp_path), deep=True, cache_options=options
        )

        assert second.inventory["app.py"]["package"] == "new"

    def test_corrupt_cache_falls_back_to_full_extraction(self, tmp_path):
        (tmp_path / "app.py").write_text("class App: pass\n", encoding="utf-8")
        cache_dir = tmp_path / "cache"
        cache_dir.mkdir()
        (cache_dir / "llm-wiki-inventory-cache.json").write_text(
            "{bad json", encoding="utf-8"
        )

        result = extract_cmd.get_inventory_result(
            str(tmp_path), deep=True, cache_options=self._cache_options(tmp_path)
        )

        assert result.inventory["app.py"]["classes"][0]["name"] == "App"
        assert result.cache_stats.status == "corrupt"
        assert result.cache_stats.load_error

    def test_extractor_failure_still_surfaces_on_cache_miss(
        self, tmp_path, monkeypatch
    ):
        (tmp_path / "app.py").write_text("class App: pass\n", encoding="utf-8")
        options = self._cache_options(tmp_path)
        save_calls = []

        class FailingPythonExtractor:
            last_error = None

            def extract(self, **kwargs):
                raise RuntimeError("boom")

        monkeypatch.setattr(
            extract_cmd,
            "_load_extractor",
            lambda _entry_point: FailingPythonExtractor(),
        )
        monkeypatch.setattr(
            extract_cmd.InventoryCache,
            "save",
            lambda *args, **kwargs: save_calls.append(args),
        )
        result = extract_cmd.get_inventory_result(
            str(tmp_path), deep=True, cache_options=options
        )

        assert result.failed
        assert result.failed[0].message == "boom"
        assert save_calls == []

    def test_warm_typescript_cache_skips_toolchain_startup(self, tmp_path, monkeypatch):
        (tmp_path / "app.ts").write_text("export class App {}\n", encoding="utf-8")
        options = self._cache_options(tmp_path)

        class FakeTypeScriptExtractor:
            last_error = None

            def extract(self, src_dir, only_files=None, deep=False, source_files=None):
                return {
                    "app.ts": {
                        "language": "typescript",
                        "classes": [{"name": "App"}],
                        "functions": [],
                    }
                }

        monkeypatch.setattr(
            extract_cmd,
            "_load_extractor",
            lambda _entry_point: FakeTypeScriptExtractor(),
        )
        extract_cmd.get_inventory_result(
            str(tmp_path), deep=True, cache_options=options
        )

        def fail_load(_entry_point):
            raise AssertionError("warm TypeScript cache should avoid extractor startup")

        monkeypatch.setattr(extract_cmd, "_load_extractor", fail_load)
        monkeypatch.setattr(
            extract_cmd,
            "_instantiate_extractor",
            lambda _entry_point: pytest.fail(
                "warm cache should avoid fresh extractor startup"
            ),
        )
        result = extract_cmd.get_inventory_result(
            str(tmp_path),
            deep=True,
            cache_options=options,
            parallel_jobs=2,
        )

        assert result.inventory["app.ts"]["classes"][0]["name"] == "App"
        assert result.cache_stats.hits == 1


class TestSummarizeInventory:
    def test_collapses_to_names(self, tmp_path):
        (tmp_path / "models.py").write_text(
            textwrap.dedent("""\
            class Foo:
                pass

            class Bar:
                pass

            def helper():
                pass
        """)
        )
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

    def test_poetry_pyproject_toml(self, tmp_path):
        (tmp_path / "pyproject.toml").write_text(
            '[tool.poetry]\nname = "poetry-pkg"\nversion = "1.0.0"\n'
        )
        packages = discover_packages(str(tmp_path))
        assert packages[0].name == "poetry-pkg"
        assert packages[0].version == "1.0.0"

    def test_discover_packages_from_source_snapshot_matches_standalone(self, tmp_path):
        pkg = tmp_path / "pkg"
        pkg.mkdir()
        (pkg / "pyproject.toml").write_text(
            '[project]\nname = "snapshot-pkg"\nversion = "2.0.0"\n'
        )
        snapshot = build_source_snapshot(tmp_path)

        assert discover_packages(
            str(tmp_path), source_snapshot=snapshot
        ) == discover_packages(str(tmp_path))

    def test_dynamic_pyproject_version_is_marked(self, tmp_path):
        (tmp_path / "pyproject.toml").write_text(
            '[project]\nname = "dynamic-pkg"\ndynamic = ["version"]\n'
        )
        packages = discover_packages(str(tmp_path))
        assert packages[0].name == "dynamic-pkg"
        assert packages[0].version == "dynamic"

    def test_non_python_inventory_keeps_package_none(self, tmp_path):
        (tmp_path / "pyproject.toml").write_text(
            '[project]\nname = "root"\nversion = "1.0.0"\n'
        )
        inventory = {"app.ts": {"language": "typescript"}}
        stamp_inventory_packages(inventory, discover_packages(str(tmp_path)))
        assert inventory["app.ts"]["package"] is None

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

    def test_invalid_setup_py_is_ignored(self, tmp_path):
        (tmp_path / "setup.py").write_text("from setuptools import setup\nsetup(\n")

        assert discover_packages(str(tmp_path)) == []

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
        (tmp_path / "settings.py").write_text(
            textwrap.dedent("""\
            MAX_RETRIES = 3
            DEFAULT_TIMEOUT = 30
        """)
        )
        inv = get_inventory(str(tmp_path))
        assert "settings.py" in inv
        assert len(inv["settings.py"]["constants"]) == 2

    def test_all_only_file_included(self, tmp_path):
        (tmp_path / "__init__.py").write_text(
            textwrap.dedent("""\
            __all__ = ["Foo", "Bar"]
        """)
        )
        inv = get_inventory(str(tmp_path))
        assert "__init__.py" in inv
        assert inv["__init__.py"].get("has_all") is True

    def test_private_functions_in_deep_mode(self, tmp_path):
        (tmp_path / "helpers.py").write_text(
            textwrap.dedent("""\
            def _internal_helper():
                pass

            def public_func():
                pass
        """)
        )
        inv = get_inventory(str(tmp_path), deep=True)
        assert "helpers.py" in inv
        fns = inv["helpers.py"]["functions"]
        names = {f["name"] for f in fns}
        assert "_internal_helper" in names
        assert "public_func" in names
        private = [f for f in fns if f["name"] == "_internal_helper"][0]
        assert private.get("private") is True

    def test_private_functions_excluded_in_shallow_mode(self, tmp_path):
        (tmp_path / "helpers.py").write_text(
            textwrap.dedent("""\
            def _internal_helper():
                pass

            def public_func():
                pass
        """)
        )
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

    def test_zero_byte_python_file_included_when_requested(self, tmp_path):
        (tmp_path / "empty.py").write_text("", encoding="utf-8")

        inv = PythonExtractor().extract(str(tmp_path), include_empty=True)

        assert inv == {
            "empty.py": {
                "classes": [],
                "functions": [],
                "language": "python",
            }
        }

    def test_empty_file_excluded_by_default(self, tmp_path):
        (tmp_path / "empty.py").write_text("# just a comment\n")
        inv = get_inventory(str(tmp_path))
        assert "empty.py" not in inv

    def test_private_only_file_included_in_deep_mode(self, tmp_path):
        (tmp_path / "internal.py").write_text(
            textwrap.dedent("""\
            def _setup():
                pass

            def _teardown():
                pass
        """)
        )
        inv = get_inventory(str(tmp_path), deep=True)
        assert "internal.py" in inv
        fns = inv["internal.py"]["functions"]
        assert all(f.get("private") for f in fns)


class TestExtractExitCodes:
    def _args(self, **kwargs):
        defaults = {
            "src_dir": ".",
            "changed": False,
            "summary": False,
            "paths": None,
            "deep": False,
            "package": None,
            "include_empty": False,
        }
        defaults.update(kwargs)
        return types.SimpleNamespace(**defaults)

    def test_changed_and_paths_exits_two(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        with pytest.raises(SystemExit) as exc_info:
            extract_cmd.run(self._args(src_dir=".", changed=True, paths=["a.py"]))
        assert exc_info.value.code == 2

    def test_unmatched_package_exits_nonzero(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        (tmp_path / "a.py").write_text("class A:\n    pass\n")
        with pytest.raises(SystemExit) as exc_info:
            extract_cmd.run(self._args(src_dir=".", package="missing"))
        assert exc_info.value.code == 1
