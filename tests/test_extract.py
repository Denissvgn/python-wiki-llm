"""Tests for commands/extract_cmd.py"""

import ast
import errno
import inspect
import json
import shutil
import subprocess
import threading
import textwrap
import types
from pathlib import Path

import pytest

from llm_wiki_cli.commands import extract_cmd
from llm_wiki_cli.commands.extract_cmd import (
    get_inventory,
    get_call_graph,
    resolve_call_observations,
    resolve_call_edges,
    _summarize_inventory,
)
from llm_wiki_cli.config import PathValidationError
from llm_wiki_cli.extractors.python_extractor import (
    PythonExtractor,
    _summarize_expression,
)
from llm_wiki_cli.services.dependencies import (
    analyze_dependencies,
    build_dependency_observations,
)
from llm_wiki_cli.services.extraction_jobs import ExtractionJobRequest
from llm_wiki_cli.services.extractor_helpers import typescript_dependencies_ready
from llm_wiki_cli.services.inventory_cache import InventoryCacheOptions
from llm_wiki_cli.services.packages import discover_packages, stamp_inventory_packages
from llm_wiki_cli.services import plugins
from llm_wiki_cli.services.source_selection import SOURCE_SELECTION_SCHEMA_VERSION
from llm_wiki_cli.services.source_snapshot import build_source_snapshot

PROJECT_ROOT = Path(__file__).parents[1]


def _body_line_count(function) -> int:
    source = textwrap.dedent(inspect.getsource(function))
    function_node = ast.parse(source).body[0]
    assert isinstance(function_node, ast.FunctionDef)
    body = function_node.body
    first_body_line = min(stmt.lineno for stmt in body)
    last_body_line = max(stmt.end_lineno or stmt.lineno for stmt in body)
    return last_body_line - first_body_line + 1


def _expression_node(source: str) -> ast.expr:
    return ast.parse(source, mode="eval").body


def _write_entrypoint_detector_plugin(root: Path, *, body: str) -> None:
    plugin_dir = root / "vendor" / "detector-plugin"
    plugin_dir.mkdir(parents=True)
    module_name = "detectors_" + "_".join(root.parts[-3:])
    module_name = "".join(
        ch if ch.isalnum() or ch == "_" else "_" for ch in module_name
    )
    (plugin_dir / plugins.MANIFEST_FILENAME).write_text(
        textwrap.dedent(f"""\
        {{
          "id": "detector-plugin",
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
    plugins.install_plugin(str(plugin_dir), root=root, yes=True)


class TestExpressionSummarizer:
    def test_summarizes_name(self):
        assert _summarize_expression(_expression_node("src_dir")) == {
            "kind": "name",
            "value": "src_dir",
        }

    def test_summarizes_attribute(self):
        assert _summarize_expression(_expression_node("options.wiki_dir")) == {
            "kind": "attribute",
            "value": "options.wiki_dir",
        }

    @pytest.mark.parametrize(
        ("source", "value"),
        [
            ('"utf-8"', "'utf-8'"),
            ("42", "42"),
            ("True", "True"),
            ("None", "None"),
        ],
    )
    def test_summarizes_constants_as_literals(self, source, value):
        assert _summarize_expression(_expression_node(source)) == {
            "kind": "literal",
            "value": value,
        }

    def test_summarizes_subscript_with_simple_base(self):
        assert _summarize_expression(_expression_node('payload["inventory"]')) == {
            "kind": "subscript",
            "value": "payload[...]",
        }

    @pytest.mark.parametrize(
        ("source", "value"),
        [
            ("Path.cwd()", "Path.cwd(...)"),
            ("build_payload(src_dir)", "build_payload(...)"),
        ],
    )
    def test_summarizes_simple_calls(self, source, value):
        assert _summarize_expression(_expression_node(source)) == {
            "kind": "call",
            "value": value,
        }

    @pytest.mark.parametrize(
        ("source", "value"),
        [
            ("[src_dir, options.wiki_dir]", "[...]"),
            ("(src_dir, options.wiki_dir)", "(...)"),
            ("{src_dir, options.wiki_dir}", "{...}"),
            ('{"path": src_dir}', "{...}"),
        ],
    )
    def test_summarizes_container_literals_with_bounded_values(self, source, value):
        assert _summarize_expression(_expression_node(source)) == {
            "kind": "literal",
            "value": value,
        }

    @pytest.mark.parametrize(
        "source",
        [
            "src_dir / name",
            "factory().value",
            "payload[get_key()]",
        ],
    )
    def test_complex_expressions_degrade_to_bounded_placeholder(self, source):
        assert _summarize_expression(_expression_node(source)) == {
            "kind": "expression",
            "value": "...",
        }


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
            "include_tests",
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

    def test_inventory_with_plugins_disabled_has_no_plugin_provenance(
        self, tmp_path, monkeypatch
    ):
        (tmp_path / "app.py").write_text("class App: pass\n", encoding="utf-8")

        def unexpected_plugin_call(*_args, **_kwargs):
            pytest.fail("disabled plugins must not be discovered or inspected")

        monkeypatch.setattr(
            extract_cmd, "get_extractor_registry", unexpected_plugin_call
        )
        monkeypatch.setattr(
            extract_cmd, "_selected_runtime_plugin_components", unexpected_plugin_call
        )
        monkeypatch.setattr(
            extract_cmd, "_captured_plugin_lock", unexpected_plugin_call
        )
        monkeypatch.setattr(
            extract_cmd,
            "parallel_safe_extractor_entry_points",
            unexpected_plugin_call,
        )

        result = extract_cmd.get_inventory_result(
            extract_cmd.InventoryRequest(
                src_dir=str(tmp_path),
                deep=True,
                include_plugins=False,
            )
        )

        assert sorted(result.inventory) == ["app.py"]
        assert result.extractor_registry == extract_cmd.EXTRACTOR_REGISTRY
        assert result.plugin_components == ()
        assert result.producer_plugin_components == ()
        assert result.plugin_lock_path is None
        assert result.plugin_lock_hash is None

    def test_plugin_inventory_excludes_owned_helper_and_keeps_consumer_suffix(
        self, tmp_path, monkeypatch
    ):
        for rel_path in (
            "src/llm_wiki_cli/__init__.py",
            "src/llm_wiki_cli/cli.py",
            "src/llm_wiki_cli/extractors/__init__.py",
            "src/llm_wiki_cli/extractors/common.py",
        ):
            path = tmp_path / rel_path
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("# package source\n", encoding="utf-8")
        protected = "src/llm_wiki_cli/extractors/go_scripts/main.go"
        ordinary = "flow.toy"
        unrelated = "vendor/llm_wiki_cli/extractors/go_scripts/main.go"
        for rel_path, content in (
            (protected, "package main\n"),
            (ordinary, "flow\n"),
            (unrelated, "package consumer\n"),
        ):
            path = tmp_path / rel_path
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")

        entry_point = "plugin.extractor:CustomExtractor"
        component = {
            "type": "extractor",
            "id": "custom",
            "language": "custom",
            "entry_point": entry_point,
            "plugin_id": "custom-plugin",
            "plugin_version": "1.0.0",
            "ref": "custom-plugin/custom",
        }

        class PluginExtractor:
            last_error = None

            def extract(self, **_kwargs):
                return {
                    rel_path: {
                        "language": "custom",
                        "classes": [],
                        "functions": [],
                    }
                    for rel_path in (protected, ordinary, unrelated)
                }

        monkeypatch.setattr(
            extract_cmd,
            "get_extractor_registry",
            lambda: {"custom": entry_point},
        )
        monkeypatch.setattr(
            extract_cmd,
            "_selected_runtime_plugin_components",
            lambda _source_root: ((component,), "."),
        )
        monkeypatch.setattr(
            extract_cmd,
            "_captured_plugin_lock",
            lambda *_args, **_kwargs: (None, None),
        )
        monkeypatch.setattr(
            extract_cmd,
            "parallel_safe_extractor_entry_points",
            lambda: set(),
        )
        monkeypatch.setattr(
            extract_cmd,
            "_load_extractor",
            lambda _entry_point: PluginExtractor(),
        )

        result = extract_cmd.get_inventory_result(str(tmp_path))

        assert sorted(result.inventory) == [ordinary, unrelated]
        assert result.source_snapshot is not None
        assert protected not in result.source_snapshot.all_source_paths
        assert protected not in result.source_snapshot.captured_content_hashes
        assert ordinary in result.source_snapshot.all_source_paths
        assert unrelated in result.source_snapshot.all_source_paths
        assert set(result.source_snapshot.hashes_for([ordinary, unrelated])) == {
            ordinary,
            unrelated,
        }

    @pytest.mark.parametrize(
        ("language", "selected_paths"),
        (
            ("python", ["selected/app.py"]),
            ("custom", ["selected/README.md", "selected/source.custom"]),
        ),
    )
    def test_configured_plugin_receives_only_finite_selected_paths(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        language: str,
        selected_paths: list[str],
    ) -> None:
        for rel_path in selected_paths:
            path = tmp_path / rel_path
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("selected\n", encoding="utf-8")
        outside = tmp_path / "outside" / (
            "secret.py" if language == "python" else "secret.custom"
        )
        outside.parent.mkdir()
        outside.write_text("SECRET = 'must-not-be-read'\n", encoding="utf-8")
        extension = "py" if language == "python" else "custom"
        ignored_rel = f"selected/ignored.{extension}"
        build_rel = f"selected/build/secret.{extension}"
        for rel_path in (ignored_rel, build_rel):
            path = tmp_path / rel_path
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("SECRET = 'must-not-survive'\n", encoding="utf-8")
        (tmp_path / "selected/.gitignore").write_text(
            f"ignored.{extension}\n",
            encoding="utf-8",
        )
        profile = tmp_path / ".llm-wiki" / "source-selection.json"
        profile.parent.mkdir()
        profile.write_text(
            json.dumps(
                {
                    "schema_version": SOURCE_SELECTION_SCHEMA_VERSION,
                    "include": ["selected"],
                    "exclude": [],
                }
            ),
            encoding="utf-8",
        )

        entry_point = f"plugin.extractor:{language.title()}Extractor"
        component = {
            "type": "extractor",
            "id": language,
            "language": language,
            "entry_point": entry_point,
            "plugin_id": "selection-test",
            "plugin_version": "1.0.0",
            "ref": f"selection-test/{language}",
        }
        calls: list[list[str] | None] = []

        class SelectionAwarePlugin:
            last_error = None

            def extract(self, **kwargs):
                only_files = kwargs.get("only_files")
                calls.append(only_files)
                result = {
                    path: {
                        "language": language,
                        "classes": [],
                        "functions": [],
                    }
                    for path in only_files or ()
                }
                for leaked_path in (ignored_rel, build_rel):
                    result[leaked_path] = {
                        "language": language,
                        "classes": [],
                        "functions": [],
                    }
                return result

        monkeypatch.setattr(
            extract_cmd,
            "get_extractor_registry",
            lambda *args, **kwargs: {language: entry_point},
        )
        monkeypatch.setattr(
            extract_cmd,
            "_configured_runtime_plugin_components",
            lambda _root: ((component,), tmp_path),
        )
        monkeypatch.setattr(
            extract_cmd,
            "_captured_plugin_lock",
            lambda *_args, **_kwargs: (None, None),
        )
        monkeypatch.setattr(
            extract_cmd,
            "parallel_safe_extractor_entry_points",
            lambda *args, **kwargs: set(),
        )
        monkeypatch.setattr(
            extract_cmd,
            "_load_plugin_extractor",
            lambda _entry_point, _root: SelectionAwarePlugin(),
        )

        result = extract_cmd.get_inventory_result(str(tmp_path))

        assert calls == [selected_paths]
        assert sorted(result.inventory) == selected_paths
        assert str(outside.relative_to(tmp_path)) not in result.inventory
        assert ignored_rel not in result.inventory
        assert build_rel not in result.inventory
        assert result.source_snapshot is not None
        assert ignored_rel not in result.source_snapshot.captured_content_hashes
        assert build_rel not in result.source_snapshot.captured_content_hashes
        assert result.source_snapshot.selected_regular_paths == frozenset(
            selected_paths
        )
        assert not result.source_snapshot.path_is_effectively_selected(ignored_rel)
        assert not result.source_snapshot.path_is_effectively_selected(build_rel)
        assert result.source_snapshot.path_is_effectively_selected(
            f"selected/deleted.{extension}"
        )

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
                assert source_files is not None
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

        result = extract_cmd.get_inventory_result(
            str(tmp_path),
            deep=True,
            cache_options=InventoryCacheOptions(
                enabled=True,
                cache_dir=str(tmp_path / "inventory-cache"),
            ),
        )

        request = calls["request"]
        assert isinstance(request, extract_cmd.GoExtractionRequest)
        assert request.src_dir == str(tmp_path)
        assert request.deep is True
        assert request.source_files == ["main.go"]
        assert request.helper_cache_dir is None
        assert calls["only_files"] is None
        assert calls["deep"] is False
        assert sorted(result.inventory) == ["main.go"]

    def test_builtin_go_extractor_receives_include_tests_request(
        self, tmp_path, monkeypatch
    ):
        (tmp_path / "main.go").write_text("package main\n", encoding="utf-8")
        (tmp_path / "main_test.go").write_text("package main\n", encoding="utf-8")
        calls = {"request": None}

        class FakeGoExtractor:
            last_error = None

            def extract(self, src_dir, only_files=None, deep=False):
                calls["request"] = src_dir
                return {
                    rel: {
                        "classes": [],
                        "functions": [],
                        "language": "go",
                    }
                    for rel in src_dir.source_files
                }

        monkeypatch.setattr(
            extract_cmd,
            "get_extractor_registry",
            lambda: {"go": extract_cmd.EXTRACTOR_REGISTRY["go"]},
        )
        monkeypatch.setattr(
            extract_cmd, "_load_extractor", lambda _entry_point: FakeGoExtractor()
        )

        result = extract_cmd.get_inventory_result(
            extract_cmd.InventoryRequest(
                src_dir=str(tmp_path),
                deep=True,
                include_tests={"go"},
            )
        )

        request = calls["request"]
        assert isinstance(request, extract_cmd.GoExtractionRequest)
        assert set(request.include_tests) == {"go"}
        assert request.source_files == ["main.go", "main_test.go"]
        assert sorted(result.inventory) == ["main.go", "main_test.go"]

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

        result = extract_cmd.get_inventory_result(
            str(tmp_path),
            deep=True,
            cache_options=InventoryCacheOptions(
                enabled=True,
                cache_dir=str(tmp_path / "inventory-cache"),
            ),
        )

        request = calls["request"]
        assert isinstance(request, extract_cmd.RustExtractionRequest)
        assert request.src_dir == str(tmp_path)
        assert request.deep is True
        assert request.source_files == ["lib.rs"]
        assert request.helper_cache_dir is None
        assert calls["only_files"] is None
        assert calls["deep"] is False
        assert sorted(result.inventory) == ["lib.rs"]

    def test_builtin_haskell_extractor_receives_request_object(
        self, tmp_path, monkeypatch
    ):
        hls_src = tmp_path / "hls-analysis" / "src" / "HLSAnalysis"
        hls_src.mkdir(parents=True)
        (hls_src / "API.hs").write_text(
            "module HLSAnalysis.API where\n", encoding="utf-8"
        )
        (tmp_path / "hls-analysis" / "Main.lhs").write_text(
            "> module Main where\n", encoding="utf-8"
        )
        calls = {"request": None, "only_files": "unset", "deep": "unset"}

        class FakeHaskellExtractor:
            last_error = None

            def extract(self, src_dir, only_files=None, deep=False):
                calls["request"] = src_dir
                calls["only_files"] = only_files
                calls["deep"] = deep
                return {
                    rel: {
                        "classes": [],
                        "functions": [],
                        "language": "haskell",
                    }
                    for rel in src_dir.source_files
                }

        monkeypatch.setattr(
            extract_cmd,
            "get_extractor_registry",
            lambda: {"haskell": extract_cmd.EXTRACTOR_REGISTRY["haskell"]},
        )
        monkeypatch.setattr(
            extract_cmd,
            "_load_extractor",
            lambda _entry_point: FakeHaskellExtractor(),
        )

        result = extract_cmd.get_inventory_result(
            str(tmp_path),
            deep=True,
            only_files=[
                "hls-analysis/src/HLSAnalysis/API.hs",
                "hls-analysis/Main.lhs",
            ],
            cache_options=InventoryCacheOptions(
                enabled=True,
                cache_dir=str(tmp_path / "inventory-cache"),
            ),
        )

        request = calls["request"]
        assert isinstance(request, extract_cmd.HaskellExtractionRequest)
        assert request.src_dir == str(tmp_path)
        assert request.deep is True
        assert request.only_files == [
            "hls-analysis/src/HLSAnalysis/API.hs",
            "hls-analysis/Main.lhs",
        ]
        assert request.source_files == [
            "hls-analysis/Main.lhs",
            "hls-analysis/src/HLSAnalysis/API.hs",
        ]
        assert calls["only_files"] is None
        assert calls["deep"] is False
        assert sorted(result.inventory) == [
            "hls-analysis/Main.lhs",
            "hls-analysis/src/HLSAnalysis/API.hs",
        ]

    def test_builtin_helpers_receive_explicit_helper_cache_dir(
        self, tmp_path, monkeypatch
    ):
        (tmp_path / "main.go").write_text("package main\n", encoding="utf-8")
        (tmp_path / "lib.rs").write_text("pub struct App;\n", encoding="utf-8")
        requests = {}

        class FakeGoExtractor:
            last_error = None

            def extract(self, src_dir, only_files=None, deep=False):
                requests["go"] = src_dir
                return {
                    "main.go": {
                        "classes": [],
                        "functions": [],
                        "language": "go",
                    }
                }

        class FakeRustExtractor:
            last_error = None

            def extract(self, src_dir, only_files=None, deep=False):
                requests["rust"] = src_dir
                return {
                    "lib.rs": {
                        "classes": [],
                        "functions": [],
                        "language": "rust",
                    }
                }

        registry = {
            "go": extract_cmd.EXTRACTOR_REGISTRY["go"],
            "rust": extract_cmd.EXTRACTOR_REGISTRY["rust"],
        }
        monkeypatch.setattr(extract_cmd, "get_extractor_registry", lambda: registry)

        def fake_load(entry_point):
            if entry_point == registry["go"]:
                return FakeGoExtractor()
            return FakeRustExtractor()

        monkeypatch.setattr(extract_cmd, "_load_extractor", fake_load)

        result = extract_cmd.get_inventory_result(
            str(tmp_path),
            deep=True,
            cache_options=InventoryCacheOptions(
                enabled=True,
                cache_dir=str(tmp_path / "inventory-cache"),
            ),
            helper_cache_dir=str(tmp_path / "helper-cache"),
        )

        assert requests["go"].helper_cache_dir == str(tmp_path / "helper-cache")
        assert requests["rust"].helper_cache_dir == str(tmp_path / "helper-cache")
        assert sorted(result.inventory) == ["lib.rs", "main.go"]

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
        worker_counts: list[int] = []
        real_executor = extract_cmd.ThreadPoolExecutor

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
        monkeypatch.setattr(
            extract_cmd,
            "ThreadPoolExecutor",
            lambda *, max_workers: (
                worker_counts.append(max_workers) or real_executor(max_workers=max_workers)
            ),
        )
        monkeypatch.setattr(extract_cmd, "_instantiate_extractor", fake_instantiate)
        monkeypatch.setattr(
            extract_cmd,
            "_load_extractor",
            lambda _entry_point: pytest.fail(
                "parallel built-ins should use fresh instances"
            ),
        )

        result = extract_cmd.get_inventory_result(
            extract_cmd.InventoryRequest(
                src_dir=str(tmp_path),
                parallel_jobs=20,
                job_request=ExtractionJobRequest("auto", 20),
            )
        )

        assert not result.failed
        assert sorted(created) == ["python", "typescript"]
        assert sorted(result.inventory) == ["app.py", "app.ts"]
        assert worker_counts == [2]
        assert result.extraction_job_plan.to_dict() == {
            "requested_jobs": "auto",
            "resolved_jobs": 20,
            "eligible_parallel_plans": 2,
            "effective_workers": 2,
            "parallel_plan_ids": ["python", "typescript"],
            "sequential_plan_ids": [],
            "cache_elided_plan_ids": [],
        }

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
        assert result.extraction_job_plan.parallel_plan_ids == ("python",)
        assert result.extraction_job_plan.sequential_plan_ids == ("custom",)
        assert result.extraction_job_plan.effective_workers == 1

    def test_inventory_plan_reports_once_before_extractor_work(
        self, tmp_path, monkeypatch
    ):
        (tmp_path / "app.py").write_text("class App: pass\n", encoding="utf-8")
        events: list[str] = []

        class FakeExtractor:
            last_error = None

            def extract(self, **kwargs):
                events.append("extract")
                return {
                    "app.py": {
                        "language": "python",
                        "classes": [],
                        "functions": [],
                    }
                }

        monkeypatch.setattr(
            extract_cmd,
            "get_extractor_registry",
            lambda: {"python": extract_cmd.EXTRACTOR_REGISTRY["python"]},
        )
        monkeypatch.setattr(extract_cmd, "_load_extractor", lambda _ep: FakeExtractor())

        result = extract_cmd.get_inventory_result(
            extract_cmd.InventoryRequest(
                src_dir=str(tmp_path),
                plan_reporter=lambda plan: events.append(
                    f"report:{','.join(plan.parallel_plan_ids)}"
                ),
            )
        )

        assert not result.failed
        assert events == ["report:python", "extract"]

    def test_inventory_plan_is_empty_when_no_extraction_work(
        self, tmp_path, monkeypatch
    ):
        monkeypatch.setattr(
            extract_cmd,
            "get_extractor_registry",
            lambda: {"python": extract_cmd.EXTRACTOR_REGISTRY["python"]},
        )

        result = extract_cmd.get_inventory_result(str(tmp_path), parallel_jobs=4)

        assert result.extraction_job_plan.effective_workers == 0
        assert result.extraction_job_plan.eligible_parallel_plans == 0
        assert result.extraction_job_plan.parallel_plan_ids == ()
        assert result.extraction_job_plan.sequential_plan_ids == ()

    def test_inventory_plan_uses_one_worker_for_sequential_only_plugin(
        self, tmp_path, monkeypatch
    ):
        class PluginExtractor:
            last_error = None

            def extract(self, **kwargs):
                return {}

        monkeypatch.setattr(
            extract_cmd,
            "get_extractor_registry",
            lambda: {"custom": "plugin.extractor:CustomExtractor"},
        )
        monkeypatch.setattr(
            extract_cmd, "parallel_safe_extractor_entry_points", lambda: set()
        )
        monkeypatch.setattr(
            extract_cmd, "_load_extractor", lambda _ep: PluginExtractor()
        )

        result = extract_cmd.get_inventory_result(str(tmp_path), parallel_jobs=8)

        assert result.extraction_job_plan.parallel_plan_ids == ()
        assert result.extraction_job_plan.sequential_plan_ids == ("custom",)
        assert result.extraction_job_plan.effective_workers == 1

    def test_inventory_plan_ids_are_sorted_independent_of_registry_order(
        self, tmp_path, monkeypatch
    ):
        (tmp_path / "app.py").write_text("class App: pass\n", encoding="utf-8")
        (tmp_path / "app.ts").write_text("export class App {}\n", encoding="utf-8")
        registry = {
            "zeta": "plugin.extractor:ZetaExtractor",
            "typescript": extract_cmd.EXTRACTOR_REGISTRY["typescript"],
            "alpha": "plugin.extractor:AlphaExtractor",
            "python": extract_cmd.EXTRACTOR_REGISTRY["python"],
        }

        class FakeExtractor:
            last_error = None

            def extract(self, **kwargs):
                return {}

        monkeypatch.setattr(extract_cmd, "get_extractor_registry", lambda: registry)
        monkeypatch.setattr(
            extract_cmd, "parallel_safe_extractor_entry_points", lambda: set()
        )
        monkeypatch.setattr(
            extract_cmd, "_load_extractor", lambda _ep: FakeExtractor()
        )

        result = extract_cmd.get_inventory_result(str(tmp_path))

        assert result.extraction_job_plan.parallel_plan_ids == (
            "python",
            "typescript",
        )
        assert result.extraction_job_plan.sequential_plan_ids == ("alpha", "zeta")

    def test_inventory_plan_records_fully_warm_cache(
        self, tmp_path, monkeypatch
    ):
        (tmp_path / "app.py").write_text("class App: pass\n", encoding="utf-8")
        (tmp_path / "app.ts").write_text("export class App {}\n", encoding="utf-8")
        registry = {
            "typescript": extract_cmd.EXTRACTOR_REGISTRY["typescript"],
            "python": extract_cmd.EXTRACTOR_REGISTRY["python"],
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
                    for rel_path in kwargs["source_files"]
                }

        monkeypatch.setattr(
            extract_cmd,
            "get_extractor_registry",
            lambda: registry,
        )
        monkeypatch.setattr(
            extract_cmd,
            "_load_extractor",
            lambda entry_point: FakeExtractor(
                "python" if "python_extractor" in entry_point else "typescript"
            ),
        )
        options = InventoryCacheOptions(
            enabled=True,
            cache_dir=str(tmp_path / "inventory-cache"),
        )

        extract_cmd.get_inventory_result(str(tmp_path), cache_options=options)
        result = extract_cmd.get_inventory_result(str(tmp_path), cache_options=options)

        assert result.extraction_job_plan.effective_workers == 0
        assert result.extraction_job_plan.cache_elided_plan_ids == (
            "python",
            "typescript",
        )

    def test_resource_failure_is_not_retried(self, tmp_path, monkeypatch):
        (tmp_path / "app.py").write_text("class App: pass\n", encoding="utf-8")
        calls = 0
        error_number = getattr(errno, "ENOSPC", None)
        if error_number is None:
            pytest.skip("ENOSPC is not defined on this platform")

        class FailingExtractor:
            last_error = None

            def extract(self, **kwargs):
                nonlocal calls
                calls += 1
                raise OSError(error_number, "capacity exhausted")

        monkeypatch.setattr(
            extract_cmd,
            "get_extractor_registry",
            lambda: {"python": extract_cmd.EXTRACTOR_REGISTRY["python"]},
        )
        monkeypatch.setattr(
            extract_cmd, "_load_extractor", lambda _ep: FailingExtractor()
        )

        result = extract_cmd.get_inventory_result(str(tmp_path))

        assert calls == 1
        assert len(result.failed) == 1
        assert "does not identify a single cause" in result.failed[0].message
        assert "manually retry once with --jobs 1" in result.failed[0].message

    def test_executor_start_failure_does_not_fallback_to_serial_work(
        self, tmp_path, monkeypatch
    ):
        (tmp_path / "app.py").write_text("class App: pass\n", encoding="utf-8")
        (tmp_path / "app.ts").write_text("export class App {}\n", encoding="utf-8")
        monkeypatch.setattr(
            extract_cmd,
            "get_extractor_registry",
            lambda: {
                "python": extract_cmd.EXTRACTOR_REGISTRY["python"],
                "typescript": extract_cmd.EXTRACTOR_REGISTRY["typescript"],
            },
        )
        monkeypatch.setattr(
            extract_cmd,
            "ThreadPoolExecutor",
            lambda **_kwargs: (_ for _ in ()).throw(RuntimeError("cannot start")),
        )
        monkeypatch.setattr(
            extract_cmd,
            "_instantiate_extractor",
            lambda _ep: pytest.fail("extractors must not run after executor failure"),
        )

        result = extract_cmd.get_inventory_result(str(tmp_path), parallel_jobs=2)

        assert {status.language for status in result.failed} == {
            "python",
            "typescript",
        }
        assert all("no automatic retry" in status.message for status in result.failed)

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

    def test_python_import_locations_use_additive_versioned_sidecar(self, tmp_path):
        (tmp_path / "main.py").write_text(
            textwrap.dedent("""\
            import os, json as codec
            from .local import (
                Alpha as A,
                Beta,
            )

            def run():
                import nested.module as nested
        """)
        )
        extractor = PythonExtractor()

        inventory = extractor.extract(
            str(tmp_path),
            deep=True,
            capture_import_observations=True,
        )

        assert inventory["main.py"]["imports"] == [
            {"module": "os", "name": "os", "type": "import"},
            {"module": "json", "name": "codec", "type": "import"},
            {"module": ".local", "name": "Alpha", "alias": "A", "type": "from"},
            {"module": ".local", "name": "Beta", "alias": None, "type": "from"},
            {
                "module": "nested.module",
                "name": "nested",
                "type": "import",
            },
        ]
        assert all("line" not in item for item in inventory["main.py"]["imports"])
        sidecar = extractor.last_import_observations
        assert sidecar == {
            "schema_version": "llm-wiki-import-location-observations/v1",
            "observations": [
                {
                    "source_path": "main.py",
                    "import_index": 0,
                    "module": "os",
                    "name": "os",
                    "line": 1,
                },
                {
                    "source_path": "main.py",
                    "import_index": 1,
                    "module": "json",
                    "name": "codec",
                    "line": 1,
                },
                {
                    "source_path": "main.py",
                    "import_index": 2,
                    "module": ".local",
                    "name": "Alpha",
                    "line": 2,
                },
                {
                    "source_path": "main.py",
                    "import_index": 3,
                    "module": ".local",
                    "name": "Beta",
                    "line": 2,
                },
                {
                    "source_path": "main.py",
                    "import_index": 4,
                    "module": "nested.module",
                    "name": "nested",
                    "line": 8,
                },
            ],
            "coverage": {
                "observed": 5,
                "emitted": 5,
                "omitted": 0,
                "limit": None,
                "truncated": False,
                "limitations": [
                    "static-import-observation-does-not-claim-runtime-completeness"
                ],
            },
        }
        detailed = build_dependency_observations(
            inventory,
            tmp_path,
            import_observations=sidecar,
        )
        assert [item["line"] for item in detailed["observations"]] == [2, 2, 1, 8, 1]
        legacy_extractor = PythonExtractor()
        assert legacy_extractor.extract(str(tmp_path), deep=True) == inventory
        assert legacy_extractor.last_import_observations is None

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


class TestPythonContractExtraction:
    def test_complete_signature_preserves_parameter_kinds_and_defaults(self, tmp_path):
        (tmp_path / "api.py").write_text(
            textwrap.dedent("""\
            from typing import Literal

            def publish(
                source: str,
                /,
                destination: str = "out",
                *values: float,
                required: bool,
                mode: Literal["fast", "safe"] = "safe",
                options: dict[str, int] = {"retries": 2},
                **extras: object,
            ) -> str | None:
                return destination
            """),
            encoding="utf-8",
        )

        fn = get_inventory(str(tmp_path), deep=True)["api.py"]["functions"][0]

        assert fn["params"] == [
            {"name": "source", "kind": "positional_only", "type": "str"},
            {
                "name": "destination",
                "kind": "positional_or_keyword",
                "type": "str",
                "default": "'out'",
            },
            {"name": "values", "kind": "var_positional", "type": "float"},
            {"name": "required", "kind": "keyword_only", "type": "bool"},
            {
                "name": "mode",
                "kind": "keyword_only",
                "type": "Literal['fast', 'safe']",
                "default": "'safe'",
            },
            {
                "name": "options",
                "kind": "keyword_only",
                "type": "dict[str, int]",
                "default": "{'retries': 2}",
            },
            {"name": "extras", "kind": "var_keyword", "type": "object"},
        ]
        assert fn["return_type"] == "str | None"
        assert [item["kind"] for item in fn["data_effects"]["inputs"]] == [
            "param"
        ] * 7
        assert [
            item["parameter_kind"] for item in fn["data_effects"]["inputs"]
        ] == [item["kind"] for item in fn["params"]]

    def test_receiver_is_omitted_only_for_class_methods(self, tmp_path):
        (tmp_path / "receivers.py").write_text(
            textwrap.dedent("""\
            def callback(self: object, *, enabled: bool = True):
                return self

            class Service:
                def run(self, value: int, /, *, enabled: bool = True):
                    return value

                @staticmethod
                def static(self: object, *, enabled: bool = True):
                    return self
            """),
            encoding="utf-8",
        )

        data = get_inventory(str(tmp_path), deep=True)["receivers.py"]

        assert [item["name"] for item in data["functions"][0]["params"]] == [
            "self",
            "enabled",
        ]
        assert [
            item["name"] for item in data["classes"][0]["methods"][0]["params"]
        ] == ["value", "enabled"]
        assert [
            item["name"] for item in data["classes"][0]["methods"][1]["params"]
        ] == ["self", "enabled"]

    def test_pydantic_fields_are_normalized_without_importing_pydantic(self, tmp_path):
        (tmp_path / "models.py").write_text(
            textwrap.dedent("""\
            from typing import Annotated, Literal
            from pydantic import BaseModel, Field as PydanticField

            class Request(BaseModel):
                name: Annotated[
                    str,
                    PydanticField(
                        alias="fullName",
                        min_length=1,
                        description="Display name",
                        examples=["Ada"],
                    ),
                ]
                labels: list[str] = PydanticField(
                    default_factory=list,
                    validation_alias="inputLabels",
                    serialization_alias="outputLabels",
                )
                state: Literal["open", "closed"] = "open"
                required_direct: str = PydanticField()
                required_ellipsis: str = PydanticField(default=...)
                count: int = PydanticField(0, ge=0)
                nullable_required: str | None
                forward_nullable: "str | None"
                nullable_defaulted: str | None = PydanticField(default=None, ge=0)
            """),
            encoding="utf-8",
        )

        model = get_inventory(str(tmp_path), deep=True)["models.py"]["classes"][0]
        fields = {item["name"]: item for item in model["attributes"]}

        assert model["model_kind"] == "pydantic"
        assert fields["name"]["required"] is True
        assert fields["name"]["alias"] == "fullName"
        assert fields["name"]["constraints"] == {"min_length": "1"}
        assert fields["name"]["description"] == "Display name"
        assert fields["name"]["examples"] == ["'Ada'"]
        assert "Call(func=" not in fields["name"]["type"]
        assert fields["labels"]["default_factory"] == "list"
        assert fields["labels"]["required"] is False
        assert fields["labels"]["validation_alias"] == "inputLabels"
        assert fields["labels"]["serialization_alias"] == "outputLabels"
        assert fields["state"]["literal_values"] == ["'open'", "'closed'"]
        assert fields["required_direct"]["required"] is True
        assert "default" not in fields["required_direct"]
        assert fields["required_ellipsis"]["required"] is True
        assert "default" not in fields["required_ellipsis"]
        assert fields["count"]["required"] is False
        assert fields["count"]["default"] == "0"
        assert fields["nullable_required"]["required"] is True
        assert fields["nullable_required"]["nullable"] is True
        assert fields["forward_nullable"]["nullable"] is True
        assert fields["nullable_defaulted"]["required"] is False
        assert fields["nullable_defaulted"]["default"] == "None"

    def test_dynamic_alias_is_explicitly_unknown(self, tmp_path):
        (tmp_path / "models.py").write_text(
            "from pydantic import BaseModel, Field\n"
            "class Request(BaseModel):\n"
            "    name: str = Field(alias=build_alias())\n",
            encoding="utf-8",
        )

        field = get_inventory(str(tmp_path), deep=True)["models.py"]["classes"][0][
            "attributes"
        ][0]

        assert "alias" not in field
        assert field["unknowns"] == [
            {
                "property": "alias",
                "expression": "build_alias()",
                "reason": "not_statically_resolvable",
            }
        ]

    def test_enums_literals_and_type_aliases_are_entities(self, tmp_path):
        (tmp_path / "types.py").write_text(
            textwrap.dedent("""\
            from enum import Enum, auto
            from typing import Literal, TypeAlias

            UserId: TypeAlias = int
            Mode = Literal["fast", "safe"]

            class Color(str, Enum):
                RED = "red"
                AUTOMATIC = auto()
            """),
            encoding="utf-8",
        )

        classes = get_inventory(str(tmp_path), deep=True)["types.py"]["classes"]
        by_name = {item["name"]: item for item in classes}

        assert by_name["UserId"]["kind"] == "type_alias"
        assert by_name["UserId"]["target"] == "int"
        assert by_name["Mode"]["target"] == "Literal['fast', 'safe']"
        assert by_name["Mode"]["literal_values"] == ["'fast'", "'safe'"]
        assert by_name["Mode"]["inferred"] is True
        assert by_name["Color"]["kind"] == "enum"
        assert by_name["Color"]["attributes"] == [
            {"name": "RED", "line": 8, "value": "'red'"},
            {"name": "AUTOMATIC", "line": 9, "value": "auto()"},
        ]

        shallow = get_inventory(str(tmp_path), deep=False)["types.py"]["classes"]
        assert {item["name"] for item in shallow} == {"UserId", "Mode", "Color"}
        assert all("target" not in item for item in shallow)

    def test_model_config_and_validators_are_structured(self, tmp_path):
        (tmp_path / "models.py").write_text(
            textwrap.dedent("""\
            from pydantic import BaseModel, ConfigDict, field_validator

            class Request(BaseModel):
                model_config = ConfigDict(extra="forbid", populate_by_name=True)
                name: str

                @field_validator("name", mode="before", check_fields=False)
                @classmethod
                def normalize_name(cls, value: str) -> str:
                    return value.strip()

                @field_validator("name", mode=VALIDATION_MODE)
                @classmethod
                def normalize_name_dynamic(cls, value: str) -> str:
                    return value
            """),
            encoding="utf-8",
        )

        model = get_inventory(str(tmp_path), deep=True)["models.py"]["classes"][0]

        assert model["model_config"] == [
            {
                "name": "extra",
                "value": "'forbid'",
                "line": 4,
                "source": "model_config",
            },
            {
                "name": "populate_by_name",
                "value": "True",
                "line": 4,
                "source": "model_config",
            },
        ]
        assert model["methods"][0]["validator"] == {
            "kind": "field",
            "mode": "before",
            "fields": ["name"],
            "options": {"check_fields": "False"},
        }
        assert model["methods"][1]["validator"] == {
            "kind": "field",
            "mode": "unknown",
            "fields": ["name"],
            "unknowns": [
                {
                    "property": "mode",
                    "expression": "VALIDATION_MODE",
                    "reason": "not_statically_resolvable",
                }
            ],
        }

    @pytest.mark.skipif(not hasattr(ast, "TypeAlias"), reason="requires Python 3.12")
    def test_pep_695_type_alias_is_captured_when_parser_supports_it(self, tmp_path):
        (tmp_path / "types.py").write_text(
            "type Pair[T] = tuple[T, T]\n", encoding="utf-8"
        )

        alias = get_inventory(str(tmp_path), deep=True)["types.py"]["classes"][0]

        assert alias["kind"] == "type_alias"
        assert alias["name"] == "Pair"
        assert alias["target"] == "tuple[T, T]"
        assert alias["type_params"] == ["T"]


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

    def test_call_records_include_compact_args_and_kwargs(self, tmp_path):
        (tmp_path / "m.py").write_text(
            textwrap.dedent("""\
            def run(path, content, extra):
                path.write_text(content, encoding="utf-8", **extra)
        """)
        )
        inventory = get_inventory(str(tmp_path), deep=True)
        call = inventory["m.py"]["functions"][0]["calls"][0]
        assert call == {
            "name": "write_text",
            "attr": "path.write_text",
            "line": 2,
            "args": [{"kind": "name", "value": "content"}],
            "kwargs": [
                {"name": "encoding", "kind": "literal", "value": "'utf-8'"},
                {"name": "**", "kind": "name", "value": "extra"},
            ],
        }

    def test_repeated_same_target_calls_keep_occurrence_metadata(self, tmp_path):
        (tmp_path / "api.py").write_text(
            textwrap.dedent("""\
            def run():
                helper("first")
                helper("second")

            def helper(value):
                return value
        """)
        )
        inventory = get_inventory(str(tmp_path), deep=True)
        run = next(fn for fn in inventory["api.py"]["functions"] if fn["name"] == "run")

        assert run["calls"] == [
            {
                "name": "helper",
                "line": 2,
                "args": [{"kind": "literal", "value": "'first'"}],
            },
            {
                "name": "helper",
                "line": 3,
                "args": [{"kind": "literal", "value": "'second'"}],
            },
        ]
        edges = resolve_call_edges(inventory)
        assert [
            (edge["from"]["symbol"], edge["to"]["symbol"], edge["line"], edge["args"])
            for edge in edges
        ] == [
            ("run", "helper", 2, [{"kind": "literal", "value": "'first'"}]),
            ("run", "helper", 3, [{"kind": "literal", "value": "'second'"}]),
        ]

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

    def test_calls_preserve_occurrences_in_source_order(self, tmp_path):
        (tmp_path / "m.py").write_text(
            textwrap.dedent("""\
            def run():
                first("initial")
                second()
                first("ignored")
        """)
        )
        inventory = get_inventory(str(tmp_path), deep=True)
        run = inventory["m.py"]["functions"][0]
        assert [c["name"] for c in run["calls"]] == ["first", "second", "first"]
        assert [c["line"] for c in run["calls"]] == [2, 3, 4]
        assert run["calls"][0]["args"] == [{"kind": "literal", "value": "'initial'"}]
        assert run["calls"][2]["args"] == [{"kind": "literal", "value": "'ignored'"}]

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


class TestDataEffects:
    def test_inputs_global_reads_and_return_annotations(self, tmp_path):
        (tmp_path / "m.py").write_text(
            textwrap.dedent("""\
            CONFIG = {"mode": "fast"}

            def run(src_dir: str, retries: int = 3) -> dict:
                mode = CONFIG["mode"]
                return {"src": src_dir, "mode": mode}
        """)
        )

        run = get_inventory(str(tmp_path), deep=True)["m.py"]["functions"][0]

        assert run["data_effects"] == {
            "inputs": [
                {
                    "kind": "param",
                    "parameter_kind": "positional_or_keyword",
                    "name": "src_dir",
                    "type": "str",
                },
                {
                    "kind": "param",
                    "parameter_kind": "positional_or_keyword",
                    "name": "retries",
                    "type": "int",
                    "default": "3",
                },
            ],
            "reads": [{"kind": "global", "name": "CONFIG", "line": 4}],
            "returns": [
                {"kind": "literal", "value": "{...}", "line": 5, "annotation": "dict"}
            ],
        }

    def test_bare_returns_are_recorded(self, tmp_path):
        (tmp_path / "m.py").write_text(
            textwrap.dedent("""\
            def maybe(flag):
                if flag:
                    return
                return build(flag)
        """)
        )

        effects = get_inventory(str(tmp_path), deep=True)["m.py"]["functions"][0][
            "data_effects"
        ]

        assert effects["returns"] == [
            {"kind": "none", "line": 3},
            {"kind": "call", "value": "build(...)", "line": 4},
        ]
        assert "build" not in {read["name"] for read in effects.get("reads", [])}

    def test_reads_and_writes_capture_attributes_subscripts_augassign_and_globals(
        self, tmp_path
    ):
        (tmp_path / "m.py").write_text(
            textwrap.dedent("""\
            TOTAL = 0

            def update(self, cls, options, payload):
                global TOTAL
                current = self.state
                cls.config = options.wiki_dir
                payload["status"] = current
                self.count += 1
                TOTAL = payload["status"]
        """)
        )

        effects = get_inventory(str(tmp_path), deep=True)["m.py"]["functions"][0][
            "data_effects"
        ]

        assert effects["reads"] == [
            {"kind": "attribute", "name": "self.state", "line": 5},
            {"kind": "attribute", "name": "options.wiki_dir", "line": 6},
        ]
        assert effects["writes"] == [
            {"kind": "attribute", "name": "cls.config", "line": 6},
            {"kind": "subscript", "name": "payload[...]", "line": 7},
            {"kind": "attribute", "name": "self.count", "line": 8},
            {"kind": "global", "name": "TOTAL", "line": 9},
        ]

    def test_methods_async_functions_and_decorated_nested_functions(self, tmp_path):
        (tmp_path / "m.py").write_text(
            textwrap.dedent("""\
            class Service:
                async def fetch(self, options):
                    self.cache = options.cache
                    return self.cache

            def create(app):
                @app.route("/items")
                def list_items(options):
                    return options.repository
                return app
        """)
        )

        data = get_inventory(str(tmp_path), deep=True)["m.py"]
        method = data["classes"][0]["methods"][0]
        nested = data["nested_functions"][0]
        outer = data["functions"][0]

        assert method["is_async"] is True
        assert method["data_effects"]["reads"] == [
            {"kind": "attribute", "name": "options.cache", "line": 3},
            {"kind": "attribute", "name": "self.cache", "line": 4},
        ]
        assert method["data_effects"]["writes"] == [
            {"kind": "attribute", "name": "self.cache", "line": 3}
        ]
        assert nested["data_effects"]["reads"] == [
            {"kind": "attribute", "name": "options.repository", "line": 9}
        ]
        assert "options.repository" not in {
            read["name"] for read in outer["data_effects"].get("reads", [])
        }

    def test_boundary_effects_classify_common_python_boundaries(self, tmp_path):
        (tmp_path / "m.py").write_text(
            textwrap.dedent("""\
            import logging
            import os
            import requests
            import subprocess

            def run(path, target):
                path.read_text()
                path.write_text("content")
                os.getenv("TOKEN")
                os.environ["MODE"] = "test"
                subprocess.run(["echo", "ok"])
                requests.get("https://example.invalid")
                print("done")
                logging.info("done")
        """)
        )

        effects = get_inventory(str(tmp_path), deep=True)["m.py"]["functions"][0][
            "data_effects"
        ]

        assert effects["boundary_effects"] == [
            {"kind": "filesystem_read", "target": "path.read_text", "line": 7},
            {"kind": "filesystem_write", "target": "path.write_text", "line": 8},
            {"kind": "environment_read", "target": "os.getenv", "line": 9},
            {"kind": "environment_write", "target": "os.environ[...]", "line": 10},
            {"kind": "process", "target": "subprocess.run", "line": 11},
            {"kind": "network", "target": "requests.get", "line": 12},
            {"kind": "output", "target": "print", "line": 13},
            {"kind": "logging", "target": "logging.info", "line": 14},
        ]

    def test_boundary_effect_variants_use_import_aliases_and_literal_modes(
        self, tmp_path
    ):
        (tmp_path / "m.py").write_text(
            textwrap.dedent("""\
            import json
            import os
            import shutil
            import subprocess as sp
            from pathlib import Path
            from subprocess import Popen

            def run(src, dst):
                with open(src) as fh:
                    json.load(fh)
                open(dst, "w")
                shutil.copy(src, dst)
                src.unlink()
                Path.home()
                os.environ.get("TOKEN")
                del os.environ["OLD"]
                sp.check_output(["echo", "ok"])
                Popen(["echo", "ok"])
        """)
        )

        effects = get_inventory(str(tmp_path), deep=True)["m.py"]["functions"][0][
            "data_effects"
        ]

        assert effects["boundary_effects"] == [
            {"kind": "filesystem_read", "target": "open", "line": 9},
            {"kind": "filesystem_read", "target": "json.load", "line": 10},
            {"kind": "filesystem_write", "target": "open", "line": 11},
            {"kind": "filesystem_write", "target": "shutil.copy", "line": 12},
            {"kind": "filesystem_write", "target": "src.unlink", "line": 13},
            {"kind": "environment_read", "target": "Path.home", "line": 14},
            {"kind": "environment_read", "target": "os.environ.get", "line": 15},
            {"kind": "environment_write", "target": "os.environ[...]", "line": 16},
        ]

    def test_boundary_effect_network_variants_are_classified(self, tmp_path):
        (tmp_path / "m.py").write_text(
            textwrap.dedent("""\
            import httpx
            import socket
            import urllib.request as urlrequest

            def run():
                httpx.post("https://example.invalid")
                urlrequest.urlopen("https://example.invalid")
                socket.create_connection(("example.invalid", 443))
        """)
        )

        effects = get_inventory(str(tmp_path), deep=True)["m.py"]["functions"][0][
            "data_effects"
        ]

        assert effects["boundary_effects"] == [
            {"kind": "network", "target": "httpx.post", "line": 6},
            {"kind": "network", "target": "urlrequest.urlopen", "line": 7},
            {"kind": "network", "target": "socket.create_connection", "line": 8},
        ]

    def test_process_import_aliases_classify_without_bare_name_false_positives(
        self, tmp_path
    ):
        (tmp_path / "m.py").write_text(
            textwrap.dedent("""\
            import subprocess as sp
            from subprocess import Popen

            def run():
                sp.check_output(["echo", "ok"])
                Popen(["echo", "ok"])
                run_helper()
        """)
        )

        effects = get_inventory(str(tmp_path), deep=True)["m.py"]["functions"][0][
            "data_effects"
        ]

        assert effects["boundary_effects"] == [
            {"kind": "process", "target": "sp.check_output", "line": 5},
            {"kind": "process", "target": "Popen", "line": 6},
        ]

    def test_generic_mutations_are_classified_but_unknown_calls_are_not(self, tmp_path):
        (tmp_path / "m.py").write_text(
            textwrap.dedent("""\
            def run(items, client):
                items.append("value")
                client.get("https://example.invalid")
                helper()
        """)
        )

        run = get_inventory(str(tmp_path), deep=True)["m.py"]["functions"][0]

        assert run["data_effects"]["boundary_effects"] == [
            {"kind": "mutation", "target": "items.append", "line": 2}
        ]
        assert {call["attr"] for call in run["calls"] if "attr" in call} == {
            "items.append",
            "client.get",
        }

    def test_boundary_effects_are_capped_in_source_order(self, tmp_path):
        calls = "\n".join(f'    print("line-{idx}")' for idx in range(9))
        (tmp_path / "m.py").write_text(f"def run():\n{calls}\n")

        effects = get_inventory(str(tmp_path), deep=True)["m.py"]["functions"][0][
            "data_effects"
        ]

        assert effects["boundary_effects"] == [
            {"kind": "output", "target": "print", "line": line} for line in range(2, 10)
        ]

    def test_empty_effects_and_slim_mode_omit_data_effects(self, tmp_path):
        (tmp_path / "m.py").write_text(
            textwrap.dedent("""\
            def noop():
                pass

            def echo(value):
                return value
        """)
        )

        deep = {
            fn["name"]: fn
            for fn in get_inventory(str(tmp_path), deep=True)["m.py"]["functions"]
        }
        slim = get_inventory(str(tmp_path), deep=False)["m.py"]["functions"]

        assert "data_effects" not in deep["noop"]
        assert "data_effects" in deep["echo"]
        assert all("data_effects" not in fn for fn in slim)

    def test_effect_categories_are_capped_in_source_order(self, tmp_path):
        module_constants = "\n".join(f"CONFIG_{idx} = {idx}" for idx in range(9))
        reads = "\n".join(f"    value_{idx} = CONFIG_{idx}" for idx in range(9))
        (tmp_path / "m.py").write_text(
            f"{module_constants}\n\n\ndef run():\n{reads}\n    return value_8\n"
        )

        effects = get_inventory(str(tmp_path), deep=True)["m.py"]["functions"][0][
            "data_effects"
        ]

        assert [read["name"] for read in effects["reads"]] == [
            f"CONFIG_{idx}" for idx in range(8)
        ]

    def test_effect_observation_sidecar_preserves_raw_totals_without_inventory_keys(
        self, tmp_path
    ):
        module_constants = "\n".join(f"CONFIG_{idx} = {idx}" for idx in range(20))
        reads = ", ".join(f"CONFIG_{idx}" for idx in range(20))
        (tmp_path / "m.py").write_text(
            f"{module_constants}\n\n\ndef run():\n    return ({reads})\n"
        )

        legacy_extractor = PythonExtractor()
        legacy = legacy_extractor.extract(str(tmp_path), deep=True)
        detailed_extractor = PythonExtractor()
        captured = detailed_extractor.extract(
            str(tmp_path),
            deep=True,
            capture_data_effect_observations=True,
        )

        assert captured == legacy
        assert legacy_extractor.last_data_effect_observations is None
        assert all(
            "data_effect_observations" not in callable_record
            for callable_record in captured["m.py"]["functions"]
        )
        sidecar = detailed_extractor.last_data_effect_observations
        assert sidecar is not None
        assert sidecar["schema_version"] == "llm-wiki-data-effect-observations/v1"
        reads_coverage = sidecar["callables"][0]["coverage"]["reads"]
        assert reads_coverage == {
            "observed": 20,
            "emitted": 8,
            "omitted": 12,
            "limit": 8,
            "truncated": True,
        }

    def test_effect_observation_sidecar_is_deterministic_for_file_order(
        self, tmp_path
    ):
        for filename, constant in (("b.py", "B"), ("a.py", "A")):
            (tmp_path / filename).write_text(
                f"{constant} = 1\n\n\ndef read():\n    return {constant}\n"
            )

        first = PythonExtractor()
        first.extract(
            str(tmp_path),
            deep=True,
            source_files=["b.py", "a.py"],
            capture_data_effect_observations=True,
        )
        second = PythonExtractor()
        second.extract(
            str(tmp_path),
            deep=True,
            source_files=["a.py", "b.py"],
            capture_data_effect_observations=True,
        )

        assert first.last_data_effect_observations == (
            second.last_data_effect_observations
        )

    def test_inventory_result_carries_opt_in_effect_sidecar(self, tmp_path):
        module_constants = "\n".join(f"CONFIG_{idx} = {idx}" for idx in range(20))
        reads = ", ".join(f"CONFIG_{idx}" for idx in range(20))
        (tmp_path / "m.py").write_text(
            f"{module_constants}\n\n\ndef run():\n    return ({reads})\n"
        )

        result = extract_cmd.get_inventory_result(
            extract_cmd.InventoryRequest(
                src_dir=tmp_path,
                deep=True,
                include_plugins=False,
                capture_data_effect_observations=True,
            )
        )

        assert result.inventory == get_inventory(str(tmp_path), deep=True)
        assert result.data_effect_observations is not None
        reads_coverage = result.data_effect_observations["callables"][0]["coverage"][
            "reads"
        ]
        assert reads_coverage["observed"] == 20
        assert reads_coverage["emitted"] == 8
        assert reads_coverage["omitted"] == 12

    def test_inventory_result_carries_opt_in_import_sidecar(self, tmp_path):
        (tmp_path / "m.py").write_text(
            "from pathlib import Path\n\n\ndef run():\n    return Path.cwd()\n"
        )

        legacy = extract_cmd.get_inventory_result(
            extract_cmd.InventoryRequest(
                src_dir=tmp_path,
                deep=True,
                include_plugins=False,
            )
        )
        detailed = extract_cmd.get_inventory_result(
            extract_cmd.InventoryRequest(
                src_dir=tmp_path,
                deep=True,
                include_plugins=False,
                capture_import_observations=True,
            )
        )

        assert detailed.inventory == legacy.inventory
        assert legacy.import_observations is None
        assert detailed.import_observations is not None
        assert detailed.import_observations["schema_version"] == (
            "llm-wiki-import-location-observations/v1"
        )
        assert detailed.import_observations["observations"] == [
            {
                "source_path": "m.py",
                "import_index": 0,
                "module": "pathlib",
                "name": "Path",
                "line": 1,
            }
        ]


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

    def test_deep_captures_main_block_calls_without_module_calls(self, tmp_path):
        (tmp_path / "cli.py").write_text(
            textwrap.dedent("""\
            import asyncio

            async def main_entry():
                pass

            if __name__ == "__main__":
                asyncio.run(main_entry())
        """)
        )

        data = get_inventory(str(tmp_path), deep=True)["cli.py"]

        assert data["main_block"] is True
        assert data["main_block_calls"] == [
            {
                "name": "run",
                "attr": "asyncio.run",
                "line": 7,
                "args": [{"kind": "call", "value": "main_entry(...)"}],
            },
            {"name": "main_entry", "line": 7},
        ]
        assert "module_calls" not in data

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
        assert "main_block_calls" not in data


class TestExtractEntryPoints:
    def test_deep_inventory_summarizes_safe_dict_constants(self, tmp_path):
        (tmp_path / "cli.py").write_text(
            textwrap.dedent("""\
            from .commands import bootstrap_cmd, site_cmd

            _COMMAND_MODULES = {
                "bootstrap": bootstrap_cmd,
                "site": site_cmd,
            }
        """),
            encoding="utf-8",
        )

        data = get_inventory(str(tmp_path), deep=True)["cli.py"]

        constants = {constant["name"]: constant for constant in data["constants"]}
        assert constants["_COMMAND_MODULES"]["value"] == {
            "kind": "dict",
            "items": [
                {
                    "key": "bootstrap",
                    "value": {"kind": "name", "value": "bootstrap_cmd"},
                },
                {"key": "site", "value": {"kind": "name", "value": "site_cmd"}},
            ],
        }

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

    def test_deep_payload_includes_plugin_detector_entrypoints(
        self, tmp_path, monkeypatch
    ):
        monkeypatch.chdir(tmp_path)
        _write_entrypoint_detector_plugin(
            tmp_path,
            body="""
            def detect(inventory):
                return [{
                    "category": "task",
                    "file": "tasks.py",
                    "symbol": "handle",
                    "label": "task-handler",
                }]
            """,
        )
        (tmp_path / "tasks.py").write_text("def handle():\n    return 1\n")

        result = extract_cmd.build_extract_payload(".", deep=True)

        assert {
            "id": "task-task-handler",
            "category": "task",
            "file": "tasks.py",
            "symbol": "handle",
            "label": "task-handler",
        } in result.payload["entrypoints"]

    def test_deep_payload_uses_source_root_plugin_when_cwd_differs(
        self, tmp_path, monkeypatch
    ):
        source = tmp_path / "source"
        cwd = tmp_path / "cwd"
        source.mkdir()
        cwd.mkdir()
        _write_entrypoint_detector_plugin(
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
        (source / "tasks.py").write_text("def handle():\n    return 1\n")
        monkeypatch.chdir(cwd)

        result = extract_cmd.build_extract_payload(
            str(source), deep=True, allow_external_src=True
        )

        assert {
            "id": "task-source-task",
            "category": "task",
            "file": "tasks.py",
            "symbol": "handle",
            "label": "source-task",
        } in result.payload["entrypoints"]

    def test_deep_payload_falls_back_to_cwd_plugin_when_source_has_none(
        self, tmp_path, monkeypatch
    ):
        source = tmp_path / "source"
        source.mkdir()
        _write_entrypoint_detector_plugin(
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
        monkeypatch.chdir(tmp_path)

        result = extract_cmd.build_extract_payload(str(source), deep=True)

        assert [entry["id"] for entry in result.payload["entrypoints"]] == [
            "task-fallback-task"
        ]

    def test_deep_payload_includes_plugin_detector_warnings(
        self, tmp_path, monkeypatch
    ):
        monkeypatch.chdir(tmp_path)
        _write_entrypoint_detector_plugin(
            tmp_path,
            body="""
            def detect(inventory):
                raise RuntimeError("no detector today")
            """,
        )
        (tmp_path / "api.py").write_text(
            '__all__ = ["run"]\n\n\ndef run():\n    return 1\n'
        )

        result = extract_cmd.build_extract_payload(".", deep=True)

        assert [entry["id"] for entry in result.payload["entrypoints"]] == ["api-run"]
        assert len(result.payload["warnings"]) == 1
        assert "detector-plugin/worker" in result.payload["warnings"][0]
        assert "no detector today" in result.payload["warnings"][0]


class TestExtractDataFlows:
    def _write_data_flow_project(self, tmp_path):
        (tmp_path / "api.py").write_text(
            textwrap.dedent("""\
            __all__ = ["run"]


            def run(path, client):
                result = helper("alpha")
                path.write_text(result)
                client.publish(result)
                return result


            def helper(value):
                return value
        """),
            encoding="utf-8",
        )

    def test_deep_payload_includes_data_flows(self, tmp_path, monkeypatch):
        self._write_data_flow_project(tmp_path)
        monkeypatch.chdir(tmp_path)

        result = extract_cmd.build_extract_payload(".", deep=True)

        data_flows = result.payload["data_flows"]
        api_flow = next(flow for flow in data_flows if flow["id"] == "api-run")
        assert [step["symbol"] for step in api_flow["steps"]][:2] == ["run", "helper"]
        assert any(
            boundary["kind"] == "filesystem_write"
            and boundary["target"] == "path.write_text"
            for boundary in api_flow["boundaries"]
        )
        assert any(
            transfer["call"] == "helper('alpha')" for transfer in api_flow["transfers"]
        )
        assert any(
            gap["kind"] == "unresolved_call" and gap["target"] == "client.publish"
            for gap in api_flow["gaps"]
        )

    def test_deep_payload_reuses_single_data_flow_context(self, tmp_path, monkeypatch):
        self._write_data_flow_project(tmp_path)
        monkeypatch.chdir(tmp_path)
        calls = 0
        real_build_context = extract_cmd.build_data_flow_context

        def counted_build_context(*args, **kwargs):
            nonlocal calls
            calls += 1
            return real_build_context(*args, **kwargs)

        monkeypatch.setattr(
            extract_cmd, "build_data_flow_context", counted_build_context
        )

        result = extract_cmd.build_extract_payload(".", deep=True)

        assert calls == 1
        assert any(flow["id"] == "api-run" for flow in result.payload["data_flows"])

    def test_non_deep_payload_omits_data_flows(self, tmp_path, monkeypatch):
        self._write_data_flow_project(tmp_path)
        monkeypatch.chdir(tmp_path)

        result = extract_cmd.build_extract_payload(".", deep=False)

        assert "data_flows" not in result.payload

    def test_summary_payload_data_flows_use_full_inventory_before_collapse(
        self, tmp_path, monkeypatch
    ):
        self._write_data_flow_project(tmp_path)
        monkeypatch.chdir(tmp_path)

        result = extract_cmd.build_extract_payload(".", deep=True, summary=True)

        assert "calls" not in result.payload["inventory"]["api.py"]["functions"][0]
        assert any(flow["id"] == "api-run" for flow in result.payload["data_flows"])

    def test_deep_payload_includes_empty_data_flows_for_empty_changed_inventory(
        self, tmp_path, monkeypatch
    ):
        self._write_data_flow_project(tmp_path)
        subprocess.run(["git", "init"], cwd=tmp_path, check=True, capture_output=True)
        subprocess.run(
            ["git", "config", "user.email", "test@example.com"],
            cwd=tmp_path,
            check=True,
        )
        subprocess.run(
            ["git", "config", "user.name", "Test"],
            cwd=tmp_path,
            check=True,
        )
        subprocess.run(["git", "add", "."], cwd=tmp_path, check=True)
        subprocess.run(
            ["git", "commit", "-m", "initial"],
            cwd=tmp_path,
            check=True,
            capture_output=True,
        )
        subprocess.run(
            ["git", "commit", "--allow-empty", "-m", "empty"],
            cwd=tmp_path,
            check=True,
            capture_output=True,
        )
        monkeypatch.chdir(tmp_path)

        result = extract_cmd.build_extract_payload(".", changed=True, deep=True)

        assert result.payload["inventory"] == {}
        assert result.payload["data_flows"] == []

    def test_empty_changed_deep_reuses_one_snapshot_for_dependencies(
        self,
        tmp_path,
        monkeypatch,
    ):
        snapshot = object()
        analysis = {
            "graph": {"edges": []},
            "cycles": [],
            "load_order": {"order": [], "cycle_groups": []},
            "reconciliation": {"languages": {}},
        }
        calls = {"snapshot": 0, "dependencies": 0}

        def fake_snapshot(src_dir, *, only_files, include_tests):
            calls["snapshot"] += 1
            assert src_dir == str(tmp_path.resolve())
            assert only_files == ()
            assert include_tests == frozenset()
            return snapshot

        def fake_dependencies(inventory, project_root, *, source_snapshot):
            calls["dependencies"] += 1
            assert inventory == {}
            assert project_root == str(tmp_path.resolve())
            assert source_snapshot is snapshot
            return analysis

        monkeypatch.setattr(extract_cmd, "_git_changed_files", lambda _root: [])
        monkeypatch.setattr(extract_cmd, "build_source_snapshot", fake_snapshot)
        monkeypatch.setattr(extract_cmd, "analyze_dependencies", fake_dependencies)
        monkeypatch.chdir(tmp_path)

        result = extract_cmd.build_extract_payload(
            ".",
            changed=True,
            deep=True,
        )

        assert calls == {"snapshot": 1, "dependencies": 1}
        assert result.dependency_analysis is analysis


class TestExtractDependencies:
    def _write_dependency_project(self, tmp_path):
        pkg = tmp_path / "pkg"
        pkg.mkdir()
        (pkg / "__init__.py").write_text("", encoding="utf-8")
        (pkg / "a.py").write_text(
            textwrap.dedent("""\
            from pkg.b import work
            import click
            import requests


            def run():
                return work()
            """),
            encoding="utf-8",
        )
        (pkg / "b.py").write_text(
            "def work():\n    return 1\n",
            encoding="utf-8",
        )
        (tmp_path / "pyproject.toml").write_text(
            textwrap.dedent("""\
            [project]
            name = "sample"
            version = "0.1.0"
            dependencies = ["requests", "tomli"]
            """),
            encoding="utf-8",
        )

    def test_deep_payload_includes_dependencies(self, tmp_path, monkeypatch):
        self._write_dependency_project(tmp_path)
        monkeypatch.chdir(tmp_path)

        result = extract_cmd.build_extract_payload(".", deep=True)

        dependencies = result.payload["dependencies"]
        assert ["pkg/a.py", "pkg/b.py"] in dependencies["edges"]
        assert dependencies["cycles"] == []
        assert dependencies["load_order"]["order"] == ["pkg/b.py", "pkg/a.py"]
        assert "python" in dependencies["external"]

    def test_non_deep_payload_omits_dependencies(self, tmp_path, monkeypatch):
        self._write_dependency_project(tmp_path)
        monkeypatch.chdir(tmp_path)

        result = extract_cmd.build_extract_payload(".", deep=False)

        assert "dependencies" not in result.payload

    def test_summary_payload_dependencies_use_full_deep_inventory_before_collapse(
        self, tmp_path, monkeypatch
    ):
        self._write_dependency_project(tmp_path)
        monkeypatch.chdir(tmp_path)

        result = extract_cmd.build_extract_payload(".", deep=True, summary=True)

        assert "imports" not in result.payload["inventory"]["pkg/a.py"]
        dependencies = result.payload["dependencies"]
        assert ["pkg/a.py", "pkg/b.py"] in dependencies["edges"]
        assert dependencies["external"]["python"]["used"]["requests"] == ["pkg/a.py"]

    def test_external_dependencies_are_keyed_by_language(self, tmp_path, monkeypatch):
        self._write_dependency_project(tmp_path)
        monkeypatch.chdir(tmp_path)

        result = extract_cmd.build_extract_payload(".", deep=True)

        python_external = result.payload["dependencies"]["external"]["python"]
        assert set(python_external) == {"used", "undeclared", "unused"}
        assert python_external["used"] == {
            "click": ["pkg/a.py"],
            "requests": ["pkg/a.py"],
        }
        assert python_external["undeclared"] == ["click"]
        assert python_external["unused"] == ["tomli"]

    def test_dependency_extract_block_includes_optional_version_metadata(self):
        analysis = {
            "graph": {"edges": []},
            "cycles": [],
            "load_order": {"order": [], "cycle_groups": []},
            "reconciliation": {
                "languages": {
                    "python": {
                        "used": {"requests": ["app.py"]},
                        "undeclared": [],
                        "unused": [],
                        "versions": {
                            "requests": {
                                "version": "2.31.0",
                                "resolved_from": "poetry.lock",
                            }
                        },
                    }
                }
            },
        }

        dependencies = extract_cmd._dependency_extract_block(analysis)

        assert dependencies["external"]["python"]["versions"] == {
            "requests": {"version": "2.31.0", "resolved_from": "poetry.lock"}
        }

    def test_haskell_external_dependencies_are_keyed_by_language(self, tmp_path):
        (tmp_path / "app.cabal").write_text(
            textwrap.dedent("""\
            cabal-version: 3.0
            name: app
            library
              build-depends: base, text
            """),
            encoding="utf-8",
        )
        analysis = analyze_dependencies(
            {
                "src/App.hs": {
                    "language": "haskell",
                    "module": "App",
                    "imports": [{"module": "Data.Text", "name": ""}],
                    "classes": [],
                    "functions": [],
                }
            },
            str(tmp_path),
        )

        dependencies = extract_cmd._dependency_extract_block(analysis)

        assert dependencies["external"]["haskell"] == {
            "used": {"text": ["src/App.hs"]},
            "undeclared": [],
            "unused": ["base"],
        }

    def test_deep_payload_includes_dependencies_for_empty_changed_inventory(
        self, tmp_path, monkeypatch
    ):
        self._write_dependency_project(tmp_path)
        subprocess.run(["git", "init"], cwd=tmp_path, check=True, capture_output=True)
        subprocess.run(
            ["git", "config", "user.email", "test@example.com"],
            cwd=tmp_path,
            check=True,
        )
        subprocess.run(
            ["git", "config", "user.name", "Test"],
            cwd=tmp_path,
            check=True,
        )
        subprocess.run(["git", "add", "."], cwd=tmp_path, check=True)
        subprocess.run(
            ["git", "commit", "-m", "initial"],
            cwd=tmp_path,
            check=True,
            capture_output=True,
        )
        subprocess.run(
            ["git", "commit", "--allow-empty", "-m", "empty"],
            cwd=tmp_path,
            check=True,
            capture_output=True,
        )
        monkeypatch.chdir(tmp_path)

        result = extract_cmd.build_extract_payload(".", changed=True, deep=True)

        assert result.payload["inventory"] == {}
        assert result.payload["dependencies"]["edges"] == []
        assert "python" in result.payload["dependencies"]["external"]


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


class TestGitignoreDiscovery:
    def test_summary_read_only_ignores_directory_rules_with_trailing_spaces(
        self, tmp_path, monkeypatch, capsys
    ):
        monkeypatch.chdir(tmp_path)
        (tmp_path / ".gitignore").write_text(
            ".shared/ \n.agent/   \n", encoding="utf-8"
        )
        for dirname in (".shared", ".agent"):
            ignored_dir = tmp_path / dirname
            ignored_dir.mkdir()
            (ignored_dir / "example.py").write_text(
                "class Ignored: pass\n", encoding="utf-8"
            )
        (tmp_path / "visible.py").write_text("class Visible: pass\n", encoding="utf-8")

        extract_cmd.run(
            types.SimpleNamespace(
                src_dir=".",
                changed=False,
                summary=True,
                deep=False,
                paths=None,
                package=None,
                include_empty=False,
                output=None,
                read_only=True,
                allow_external_src=False,
            )
        )

        payload = json.loads(capsys.readouterr().out)
        assert set(payload["inventory"]) == {"visible.py"}
        assert ".shared/example.py" not in payload["inventory"]
        assert ".agent/example.py" not in payload["inventory"]


class TestUnsupportedSources:
    def test_shell_files_are_reported_as_unsupported_sources(self, tmp_path):
        (tmp_path / "app.py").write_text("def main():\n    pass\n", encoding="utf-8")
        scripts = tmp_path / "scripts"
        scripts.mkdir()
        (scripts / "deploy.sh").write_text("#!/bin/sh\n", encoding="utf-8")

        summary_result = extract_cmd.build_extract_payload(
            str(tmp_path), summary=True, allow_external_src=True
        )
        deep_result = extract_cmd.build_extract_payload(
            str(tmp_path), deep=True, allow_external_src=True
        )

        expected = {"shell": {"count": 1, "paths": ["scripts/deploy.sh"]}}
        assert summary_result.payload["unsupported_sources"] == expected
        assert deep_result.payload["unsupported_sources"] == expected
        assert "scripts/deploy.sh" not in summary_result.payload["inventory"]
        assert "scripts/deploy.sh" not in deep_result.payload["inventory"]

    def test_generated_javascript_bundles_are_reported_not_extracted(
        self, tmp_path, monkeypatch
    ):
        first_party = "services/dashboard/frontend/src/main.js"
        generated = "services/dashboard/static/assets/index-D0zaI3XT.js"
        for rel_path in (first_party, generated):
            path = tmp_path / rel_path
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("export function visible() {}\n", encoding="utf-8")

        class FakeTypeScriptExtractor:
            last_error = None

            def extract(
                self,
                src_dir,
                only_files=None,
                deep=False,
                source_files=None,
            ):
                assert source_files is not None
                return {
                    rel: {"classes": [], "functions": [], "language": "javascript"}
                    for rel in source_files
                }

        monkeypatch.setattr(
            extract_cmd,
            "get_extractor_registry",
            lambda: {"typescript": extract_cmd.EXTRACTOR_REGISTRY["typescript"]},
        )
        monkeypatch.setattr(
            extract_cmd,
            "_load_extractor",
            lambda _entry_point: FakeTypeScriptExtractor(),
        )

        result = extract_cmd.build_extract_payload(
            str(tmp_path), summary=True, allow_external_src=True
        )

        assert sorted(result.payload["inventory"]) == [first_party]
        assert result.payload["unsupported_sources"] == {
            "generated_javascript_bundle": {"count": 1, "paths": [generated]}
        }

    def test_paths_can_extract_exact_generated_javascript_bundle(
        self, tmp_path, monkeypatch
    ):
        generated = "services/dashboard/static/assets/index-D0zaI3XT.js"
        path = tmp_path / generated
        path.parent.mkdir(parents=True)
        path.write_text("function a(){};export{a as Ko};\n", encoding="utf-8")

        class FakeTypeScriptExtractor:
            last_error = None

            def extract(
                self,
                src_dir,
                only_files=None,
                deep=False,
                source_files=None,
            ):
                assert source_files is not None
                return {
                    rel: {"classes": [], "functions": [], "language": "javascript"}
                    for rel in source_files
                }

        monkeypatch.setattr(
            extract_cmd,
            "get_extractor_registry",
            lambda: {"typescript": extract_cmd.EXTRACTOR_REGISTRY["typescript"]},
        )
        monkeypatch.setattr(
            extract_cmd,
            "_load_extractor",
            lambda _entry_point: FakeTypeScriptExtractor(),
        )

        result = extract_cmd.build_extract_payload(
            str(tmp_path),
            paths=[generated],
            summary=True,
            allow_external_src=True,
        )

        assert sorted(result.payload["inventory"]) == [generated]
        assert "unsupported_sources" not in result.payload

    def test_haskell_summary_output_uses_builtin_inventory(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        app_dir = tmp_path / "app"
        app_dir.mkdir()
        (app_dir / "Main.hs").write_text("module Main where\n", encoding="utf-8")

        class FakeHaskellExtractor:
            last_error = None

            def extract(self, src_dir, only_files=None, deep=False):
                return {
                    rel: {
                        "language": "haskell",
                        "classes": [{"name": "App", "kind": "data"}],
                        "functions": [{"name": "main"}],
                    }
                    for rel in src_dir.source_files
                }

        monkeypatch.setattr(
            extract_cmd,
            "get_extractor_registry",
            lambda: {"haskell": extract_cmd.EXTRACTOR_REGISTRY["haskell"]},
        )
        monkeypatch.setattr(
            extract_cmd,
            "_load_extractor",
            lambda _entry_point: FakeHaskellExtractor(),
        )

        result = extract_cmd.build_extract_payload(".", summary=True)

        assert result.payload["inventory"] == {
            "app/Main.hs": {
                "language": "haskell",
                "classes": ["App"],
                "functions": ["main"],
            }
        }
        assert "unsupported_sources" not in result.payload

    def test_haskell_builtin_registration_suppresses_unsupported_report(
        self, tmp_path, monkeypatch
    ):
        monkeypatch.chdir(tmp_path)
        hls_app = tmp_path / "hls-analysis" / "app"
        hls_src = tmp_path / "hls-analysis" / "src" / "HLSAnalysis"
        hls_app.mkdir(parents=True)
        hls_src.mkdir(parents=True)
        (tmp_path / ".git").mkdir()
        (hls_app / "Main.hs").write_text("module Main where\n", encoding="utf-8")
        (hls_src / "API.hs").write_text(
            "module HLSAnalysis.API where\n", encoding="utf-8"
        )

        result = extract_cmd.get_inventory_result(
            ".",
            helper_cache_dir=str(tmp_path / "unprepared-helper-cache"),
        )

        assert result.inventory == {}
        assert result.statuses["haskell"].state == "failed"
        assert result.statuses["haskell"].files_found == 2
        assert (
            "prepare-extractors --language haskell"
            in result.statuses["haskell"].message
        )
        assert (
            result.statuses["haskell"].message.count(
                "prepare-extractors --language haskell"
            )
            == 1
        )
        assert (
            "before extract/bootstrap/sync/lint/ci-check"
            in result.statuses["haskell"].message
        )
        assert "before lint/extract" not in result.statuses["haskell"].message
        assert (
            extract_cmd.unsupported_source_summary(
                build_source_snapshot("."),
                supported_languages=result.statuses,
            )
            == {}
        )

    def test_no_haskell_files_do_not_probe_haskell_helper(self, tmp_path, monkeypatch):
        (tmp_path / "app.py").write_text("class App: pass\n", encoding="utf-8")
        helper_calls = []

        monkeypatch.setattr(
            "llm_wiki_cli.extractors.haskell_extractor.get_prepared_binary",
            lambda *args, **kwargs: helper_calls.append((args, kwargs)),
        )

        result = extract_cmd.get_inventory_result(str(tmp_path))

        assert result.statuses["haskell"] == extract_cmd.ExtractorStatus(
            "haskell", "skipped", 0
        )
        assert helper_calls == []

    def test_ignored_and_excluded_haskell_files_do_not_probe_helper(
        self, tmp_path, monkeypatch
    ):
        ignored_dir = tmp_path / "ignored"
        ignored_dir.mkdir()
        (ignored_dir / "Main.hs").write_text("module Ignored where\n", encoding="utf-8")
        dist_dir = tmp_path / "dist"
        dist_dir.mkdir()
        (dist_dir / "Generated.hs").write_text(
            "module Generated where\n", encoding="utf-8"
        )
        (tmp_path / ".gitignore").write_text("ignored/\n", encoding="utf-8")
        helper_calls = []

        monkeypatch.setattr(
            "llm_wiki_cli.extractors.haskell_extractor.get_prepared_binary",
            lambda *args, **kwargs: helper_calls.append((args, kwargs)),
        )

        result = extract_cmd.get_inventory_result(str(tmp_path))

        assert result.statuses["haskell"] == extract_cmd.ExtractorStatus(
            "haskell", "skipped", 0
        )
        assert helper_calls == []

    def test_registered_haskell_plugin_suppresses_unsupported_report(
        self, tmp_path, monkeypatch
    ):
        monkeypatch.chdir(tmp_path)
        app_dir = tmp_path / "app"
        app_dir.mkdir()
        (app_dir / "Main.hs").write_text("module Main where\n", encoding="utf-8")
        registry = {
            **extract_cmd.EXTRACTOR_REGISTRY,
            "haskell": "fake_haskell:HaskellExtractor",
        }

        class FakeHaskellExtractor:
            last_error = None

            def extract(self, src_dir, only_files=None, deep=False):
                return {
                    "app/Main.hs": {
                        "language": "haskell",
                        "classes": [],
                        "functions": [{"name": "main"}],
                    }
                }

        monkeypatch.setattr(extract_cmd, "get_extractor_registry", lambda: registry)
        monkeypatch.setattr(
            extract_cmd,
            "_load_extractor",
            lambda entry_point: (
                FakeHaskellExtractor()
                if entry_point == "fake_haskell:HaskellExtractor"
                else extract_cmd._load_extractor(entry_point)
            ),
        )

        result = extract_cmd.build_extract_payload(".", summary=True)

        assert result.payload["inventory"] == {
            "app/Main.hs": {
                "language": "haskell",
                "functions": ["main"],
            }
        }
        assert "unsupported_sources" not in result.payload

    def test_legacy_haskell_plugin_still_suppresses_unsupported_report(
        self, tmp_path, monkeypatch
    ):
        monkeypatch.chdir(tmp_path)
        app_dir = tmp_path / "app"
        app_dir.mkdir()
        (app_dir / "Main.hs").write_text("module Main where\n", encoding="utf-8")

        monkeypatch.setitem(
            extract_cmd.LANGUAGE_EXTENSIONS,
            "haskell",
            (),
        )
        monkeypatch.setitem(
            extract_cmd.EXTRACTOR_REGISTRY,
            "haskell",
            "fake_haskell:HaskellExtractor",
        )
        monkeypatch.setattr(
            "llm_wiki_cli.services.source_snapshot.KNOWN_UNSUPPORTED_LANGUAGE_EXTENSIONS",
            {"haskell": (".hs", ".lhs")},
        )
        snapshot = build_source_snapshot(".")

        assert extract_cmd.unsupported_source_summary(snapshot) == {
            "haskell": {"count": 1, "paths": ["app/Main.hs"]}
        }
        assert (
            extract_cmd.unsupported_source_summary(
                snapshot, supported_languages={"haskell"}
            )
            == {}
        )


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

    def test_detailed_observations_preserve_ambiguity_without_changing_legacy(self):
        inventory = {
            "a.py": {
                "functions": [{"name": "target", "calls": []}],
                "classes": [],
            },
            "b.py": {
                "functions": [{"name": "target", "calls": []}],
                "classes": [],
            },
            "main.py": {
                "imports": [{"module": "", "name": "target"}],
                "functions": [
                    {
                        "name": "run",
                        "calls": [{"name": "target", "attr": ""}],
                    }
                ],
                "classes": [],
            },
        }

        legacy = resolve_call_edges(inventory)
        detailed = resolve_call_observations(inventory)

        assert legacy[-1]["kind"] == "external"
        assert legacy[-1]["line"] == 0
        assert detailed["schema_version"] == "llm-wiki-call-observations/v1"
        assert detailed["coverage"]["observed"] == 1
        observation = detailed["observations"][0]
        assert observation["kind"] == "ambiguous"
        assert observation["line"] is None
        assert observation["candidates"] == [
            {"file": "a.py", "symbol": "target"},
            {"file": "b.py", "symbol": "target"},
        ]
        assert resolve_call_edges(inventory) == legacy

    def test_detailed_observations_are_deterministic_under_inventory_shuffle(self):
        inventory = {
            "a.py": {
                "functions": [{"name": "target", "calls": []}],
                "classes": [],
            },
            "main.py": {
                "imports": [],
                "functions": [
                    {
                        "name": "run",
                        "calls": [{"name": "target", "line": 4}],
                    }
                ],
                "classes": [],
            },
        }
        assert resolve_call_observations(inventory) == resolve_call_observations(
            dict(reversed(list(inventory.items())))
        )


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

    def test_default_inventory_excludes_agent_worktree_sources(self, tmp_path):
        (tmp_path / "app.py").write_text("class App: pass\n", encoding="utf-8")
        worktree = tmp_path / ".claude" / "worktrees" / "agent-strict-instructions"
        worktree.mkdir(parents=True)
        (worktree / "app.py").write_text("class WorktreeApp: pass\n", encoding="utf-8")

        inventory = get_inventory(str(tmp_path))

        assert sorted(inventory) == ["app.py"]

    def test_only_files_can_select_exact_agent_worktree_source(self, tmp_path):
        worktree = tmp_path / ".claude" / "worktrees" / "agent-strict-instructions"
        worktree.mkdir(parents=True)
        (worktree / "app.py").write_text("class WorktreeApp: pass\n", encoding="utf-8")
        (worktree / "sibling.py").write_text("class Sibling: pass\n", encoding="utf-8")

        inventory = get_inventory(
            str(tmp_path),
            only_files=[".claude/worktrees/agent-strict-instructions/app.py"],
        )

        assert sorted(inventory) == [
            ".claude/worktrees/agent-strict-instructions/app.py"
        ]


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
        assert second.cache_stats is not None
        assert second.cache_stats.hits == 1
        assert second.cache_stats.fresh_extracted == 0

    def test_import_sidecar_opt_in_bypasses_warm_python_cache(self, tmp_path):
        (tmp_path / "app.py").write_text(
            "import os\n\n\ndef run():\n    return os.getcwd()\n",
            encoding="utf-8",
        )
        options = self._cache_options(tmp_path)
        legacy = extract_cmd.get_inventory_result(
            str(tmp_path),
            deep=True,
            cache_options=options,
        )

        captured = extract_cmd.get_inventory_result(
            extract_cmd.InventoryRequest(
                src_dir=tmp_path,
                deep=True,
                cache_options=options,
                capture_import_observations=True,
            )
        )
        warm_legacy = extract_cmd.get_inventory_result(
            str(tmp_path),
            deep=True,
            cache_options=options,
        )

        assert captured.inventory == legacy.inventory == warm_legacy.inventory
        assert captured.import_observations is not None
        assert captured.import_observations["observations"][0]["line"] == 1
        assert captured.cache_stats is not None
        assert captured.cache_stats.fresh_extracted == 1
        assert warm_legacy.import_observations is None
        assert warm_legacy.cache_stats is not None
        assert warm_legacy.cache_stats.hits == 1

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
                assert source_files is not None
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
        assert result.cache_stats is not None
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
        assert result.cache_stats is not None
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
        assert result.cache_stats is not None
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
        assert result.cache_stats is not None
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

    def test_keeps_compact_module_metadata(self):
        summary = _summarize_inventory(
            {
                "docker/proxy.js": {
                    "language": "javascript",
                    "classes": [],
                    "functions": [],
                    "imports": [
                        {"module": "node:http", "name": "http"},
                        {"module": "node:http", "name": "http"},
                        {"module": "node:net", "name": "net"},
                    ],
                    "exports": ["default"],
                    "constants": [
                        {"name": "http", "line": 1, "exported": False},
                        {"name": "server", "line": 2, "exported": False},
                    ],
                    "module_calls": [
                        {"name": "require", "line": 1, "target": "http"},
                        {"name": "createServer", "line": 2, "target": "server"},
                        {"name": "listen", "line": 3},
                    ],
                    "module_docstring": "/** Proxy module. */",
                }
            }
        )

        assert summary["docker/proxy.js"] == {
            "language": "javascript",
            "imports": ["node:http", "node:net"],
            "exports": ["default"],
            "constants": ["http", "server"],
            "module_calls": ["require", "createServer", "listen"],
        }


@pytest.mark.skipif(
    not typescript_dependencies_ready(PROJECT_ROOT) or shutil.which("node") is None,
    reason="Node.js/ts-morph dependencies not installed",
)
class TestTypeScriptModuleOnlyExtraction:
    def test_summary_keeps_module_only_javascript_inventory(self, tmp_path):
        path = tmp_path / "docker" / "proxy.js"
        path.parent.mkdir(parents=True)
        path.write_text(
            textwrap.dedent("""\
            const http = require("node:http");
            const listenPort = Number.parseInt(process.env.PORT || "3000", 10);
            const server = http.createServer((req, res) => {
              res.end("ok");
            });
            server.listen(listenPort);
            """),
            encoding="utf-8",
        )

        summary = extract_cmd.build_extract_payload(
            str(tmp_path),
            summary=True,
            allow_external_src=True,
            read_only=True,
        )
        deep = extract_cmd.build_extract_payload(
            str(tmp_path),
            deep=True,
            allow_external_src=True,
            read_only=True,
        )

        assert sorted(summary.payload["inventory"]) == ["docker/proxy.js"]
        assert sorted(deep.payload["inventory"]) == ["docker/proxy.js"]
        entry = summary.payload["inventory"]["docker/proxy.js"]
        assert entry["language"] == "javascript"
        assert entry["constants"] == ["http", "listenPort", "server"]
        assert entry["module_calls"] == [
            "require",
            "parseInt",
            "createServer",
            "listen",
        ]

    def test_deep_payload_includes_javascript_http_entrypoint_and_data_flow(
        self, tmp_path
    ):
        path = tmp_path / "server.js"
        path.write_text(
            textwrap.dedent("""\
            const http = require("node:http");

            function handleRequest(req, res) {
              res.end("ok");
            }

            const server = http.createServer(handleRequest);
            """),
            encoding="utf-8",
        )

        result = extract_cmd.build_extract_payload(
            str(tmp_path),
            deep=True,
            allow_external_src=True,
            read_only=True,
        )

        assert {
            "category": "http",
            "file": "server.js",
            "symbol": "handleRequest",
            "label": "handleRequest",
            "id": "http-handleRequest",
        } in result.payload["entrypoints"]
        assert any(
            flow["id"] == "http-handleRequest" for flow in result.payload["data_flows"]
        )

    def test_paths_keep_pto_style_typescript_modules_in_deep_inventory(self, tmp_path):
        files = {
            "frontend/src/main.tsx": """
                import React from 'react';
                import ReactDOM from 'react-dom/client';
                import App from './App';

                const queryClient = new QueryClient();
                ReactDOM.createRoot(document.getElementById('root')!).render(<App />);
            """,
            "frontend/src/lib/api.ts": """
                import axios, { AxiosInstance } from 'axios';

                const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
                const api: AxiosInstance = axios.create({ baseURL: `${BASE_URL}/api/v1` });
                api.interceptors.request.use((config) => config);

                export default api;
            """,
            "frontend/src/lib/queryClient.ts": """
                import { QueryClient } from '@tanstack/react-query';

                export const queryClient = new QueryClient();
            """,
            "frontend/src/pages/SimpleRegister.tsx": """
                Object.defineProperty(exports, "__esModule", { value: true });
                exports.default = SimpleRegister;

                function SimpleRegister() {
                  return null;
                }
            """,
            "frontend/src/vite-env.d.ts": """
                interface ImportMetaEnv {
                  readonly VITE_API_URL?: string
                }

                interface ImportMeta {
                  readonly env: ImportMetaEnv
                }
            """,
        }
        for rel_path, content in files.items():
            path = tmp_path / rel_path
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(textwrap.dedent(content), encoding="utf-8")

        result = extract_cmd.build_extract_payload(
            str(tmp_path),
            deep=True,
            paths=list(files),
            allow_external_src=True,
        )

        assert set(result.payload["inventory"]) == set(files)
        assert result.inventory_count == 5
        assert result.payload["inventory"]["frontend/src/main.tsx"]["module_calls"]
        assert result.payload["inventory"]["frontend/src/lib/api.ts"]["exports"] == [
            "default"
        ]
        assert result.payload["inventory"]["frontend/src/lib/queryClient.ts"][
            "constants"
        ] == [{"name": "queryClient", "line": 4, "exported": True}]
        assert [
            fn["name"]
            for fn in result.payload["inventory"][
                "frontend/src/pages/SimpleRegister.tsx"
            ]["functions"]
        ] == ["SimpleRegister"]
        assert [
            cls["name"]
            for cls in result.payload["inventory"]["frontend/src/vite-env.d.ts"][
                "classes"
            ]
        ] == ["ImportMetaEnv", "ImportMeta"]

    def test_full_scan_keeps_pto_style_src_lib_modules_under_root_lib_ignore(
        self, tmp_path
    ):
        (tmp_path / ".gitignore").write_text("lib/\n", encoding="utf-8")
        files = {
            "frontend/src/main.tsx": """
                import React from 'react';
                import ReactDOM from 'react-dom/client';
                import App from './App';

                const queryClient = new QueryClient();
                ReactDOM.createRoot(document.getElementById('root')!).render(<App />);
            """,
            "frontend/src/lib/api.ts": """
                import axios, { AxiosInstance } from 'axios';

                const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
                const api: AxiosInstance = axios.create({ baseURL: `${BASE_URL}/api/v1` });
                api.interceptors.request.use((config) => config);

                export default api;
            """,
            "frontend/src/lib/api.tsx": """
                export default function ApiPreview() {
                  return null;
                }
            """,
            "frontend/src/lib/queryClient.ts": """
                import { QueryClient } from '@tanstack/react-query';

                export const queryClient = new QueryClient();
            """,
            "frontend/src/lib/queryClient.tsx": """
                export const QueryClientPreview = () => null;
            """,
            "frontend/src/lib/utils.ts": """
                export function cn(...classes: string[]) {
                  return classes.filter(Boolean).join(' ');
                }
            """,
            "frontend/src/lib/utils.tsx": """
                export function UtilsPreview() {
                  return null;
                }
            """,
            "frontend/src/lib/websocket.ts": """
                export function connectWebSocket() {
                  return new WebSocket('ws://localhost');
                }
            """,
            "frontend/src/lib/websocket.tsx": """
                export function WebSocketPreview() {
                  return null;
                }
            """,
        }
        for rel_path, content in files.items():
            path = tmp_path / rel_path
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(textwrap.dedent(content), encoding="utf-8")
        root_lib = tmp_path / "lib"
        root_lib.mkdir()
        (root_lib / "generated.ts").write_text(
            "export const generated = 1;\n", encoding="utf-8"
        )

        result = extract_cmd.build_extract_payload(
            str(tmp_path),
            deep=True,
            allow_external_src=True,
        )

        assert set(result.payload["inventory"]) == set(files)
        assert "lib/generated.ts" not in result.payload["inventory"]
        assert result.payload["inventory"]["frontend/src/main.tsx"]["module_calls"]
        assert result.payload["inventory"]["frontend/src/lib/api.ts"]["exports"] == [
            "default"
        ]
        assert result.payload["inventory"]["frontend/src/lib/queryClient.ts"][
            "constants"
        ] == [{"name": "queryClient", "line": 4, "exported": True}]
        assert [
            fn["name"]
            for fn in result.payload["inventory"]["frontend/src/lib/utils.ts"][
                "functions"
            ]
        ] == ["cn"]
        assert [
            fn["name"]
            for fn in result.payload["inventory"]["frontend/src/lib/websocket.ts"][
                "functions"
            ]
        ] == ["connectWebSocket"]


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
            "include_tests": None,
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

    def test_run_passes_helper_cache_dir_to_payload(
        self, tmp_path, monkeypatch, capsys
    ):
        monkeypatch.chdir(tmp_path)
        seen = {}

        def fake_build_extract_payload(src_dir, **kwargs):
            seen["src_dir"] = src_dir
            seen["helper_cache_dir"] = kwargs["helper_cache_dir"]
            seen["include_tests"] = kwargs["include_tests"]
            return extract_cmd.ExtractPayloadResult(
                {"schema_version": extract_cmd.EXTRACT_SCHEMA_VERSION, "inventory": {}},
                inventory_count=0,
                docker_count=0,
            )

        monkeypatch.setattr(
            extract_cmd, "build_extract_payload", fake_build_extract_payload
        )

        extract_cmd.run(
            self._args(
                src_dir=".",
                helper_cache_dir=str(tmp_path / "helper-cache"),
                include_tests=["go"],
            )
        )

        assert seen == {
            "src_dir": ".",
            "helper_cache_dir": str(tmp_path / "helper-cache"),
            "include_tests": ["go"],
        }
        assert json.loads(capsys.readouterr().out)["inventory"] == {}
