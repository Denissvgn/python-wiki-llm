"""Tests for the TypeScript extractor (ts_extractor.py + ts_scripts/extract.js)."""

from __future__ import annotations

import ast
import inspect
import json
import shutil
import subprocess
import textwrap
from pathlib import Path
from unittest.mock import patch

import pytest

from llm_wiki_cli.extractors import common as extractor_common
from llm_wiki_cli.extractors.ts_extractor import TypeScriptExtractor
from llm_wiki_cli.services.extractor_helpers import typescript_dependencies_ready

# ---------------------------------------------------------------------------
# Skip all tests when Node.js is not available on this machine.
# ---------------------------------------------------------------------------


def _command_available(*cmd: str) -> bool:
    if shutil.which(cmd[0]) is None:
        return False
    try:
        subprocess.run(
            list(cmd),
            capture_output=True,
            text=True,
            check=True,
            timeout=10,
        )
        return True
    except (
        subprocess.CalledProcessError,
        subprocess.TimeoutExpired,
        FileNotFoundError,
    ):
        return False


PROJECT_ROOT = Path(__file__).parents[1]
BUNDLED_TS_SCRIPTS = (
    PROJECT_ROOT / "src" / "llm_wiki_cli" / "extractors" / "ts_scripts"
)
NODE_AVAILABLE = (
    _command_available("node", "--version")
    and typescript_dependencies_ready(PROJECT_ROOT)
)
skip_no_node = pytest.mark.skipif(
    not NODE_AVAILABLE,
    reason="Node.js/ts-morph dependencies not installed — TypeScript extractor tests skipped",
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_ts(tmp_path: Path, filename: str, content: str) -> Path:
    p = tmp_path / filename
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(textwrap.dedent(content), encoding="utf-8")
    return p


def _write_owned_package_sentinels(root: Path) -> None:
    for rel_path in (
        "src/llm_wiki_cli/__init__.py",
        "src/llm_wiki_cli/cli.py",
        "src/llm_wiki_cli/extractors/__init__.py",
        "src/llm_wiki_cli/extractors/common.py",
    ):
        _make_ts(root, rel_path, "# package source\n")


class TestTypeScriptWrapperFiltering:
    def test_full_scan_passes_gitignore_filtered_files_to_subprocess(
        self, tmp_path, monkeypatch
    ):
        _make_ts(tmp_path, "real.ts", "export class Real {}")
        _make_ts(tmp_path, "ignored.ts", "export class Ignored {}")
        (tmp_path / ".gitignore").write_text("ignored.ts\n", encoding="utf-8")
        commands = []

        def fake_run(cmd, *args, **kwargs):
            commands.append(cmd)
            return subprocess.CompletedProcess(
                cmd,
                0,
                stdout='{"real.ts":{"classes":[],"functions":[]}}',
                stderr="",
            )

        monkeypatch.setattr(
            "llm_wiki_cli.extractors.ts_extractor.shutil.which",
            lambda _name: "/bin/tool",
        )
        monkeypatch.setattr(
            "llm_wiki_cli.extractors.ts_extractor.get_prepared_typescript_root",
            lambda *_args: BUNDLED_TS_SCRIPTS,
        )
        monkeypatch.setattr(
            "llm_wiki_cli.extractors.ts_extractor.subprocess.run", fake_run
        )

        TypeScriptExtractor().extract(str(tmp_path))

        cmd = commands[0]
        only_idx = cmd.index("--only-files") + 1
        assert cmd[only_idx] == "real.ts"

    def test_full_scan_skips_generated_javascript_bundles(self, tmp_path, monkeypatch):
        _make_ts(
            tmp_path,
            "services/dashboard/frontend/src/main.js",
            "export const app = 1;",
        )
        _make_ts(
            tmp_path,
            "services/dashboard/static/assets/index-D0zaI3XT.js",
            "function a(){};export{a as Ko};",
        )
        commands = []

        def fake_run(cmd, *args, **kwargs):
            commands.append(cmd)
            return subprocess.CompletedProcess(
                cmd,
                0,
                stdout='{"services/dashboard/frontend/src/main.js":{"classes":[],"functions":[]}}',
                stderr="",
            )

        monkeypatch.setattr(
            "llm_wiki_cli.extractors.ts_extractor.shutil.which",
            lambda _name: "/bin/tool",
        )
        monkeypatch.setattr(
            "llm_wiki_cli.extractors.ts_extractor.get_prepared_typescript_root",
            lambda *_args: BUNDLED_TS_SCRIPTS,
        )
        monkeypatch.setattr(
            "llm_wiki_cli.extractors.ts_extractor.subprocess.run", fake_run
        )

        TypeScriptExtractor().extract(str(tmp_path))

        cmd = commands[0]
        only_idx = cmd.index("--only-files") + 1
        assert cmd[only_idx] == "services/dashboard/frontend/src/main.js"

    def test_only_files_passes_gitignored_explicit_files_to_subprocess(
        self, tmp_path, monkeypatch
    ):
        _make_ts(tmp_path, "frontend/src/lib/api.ts", "export const api = 1;")
        (tmp_path / ".gitignore").write_text("lib/\n", encoding="utf-8")
        commands = []

        def fake_run(cmd, *args, **kwargs):
            commands.append(cmd)
            return subprocess.CompletedProcess(
                cmd,
                0,
                stdout='{"frontend/src/lib/api.ts":{"classes":[],"functions":[]}}',
                stderr="",
            )

        monkeypatch.setattr(
            "llm_wiki_cli.extractors.ts_extractor.shutil.which",
            lambda _name: "/bin/tool",
        )
        monkeypatch.setattr(
            "llm_wiki_cli.extractors.ts_extractor.get_prepared_typescript_root",
            lambda *_args: BUNDLED_TS_SCRIPTS,
        )
        monkeypatch.setattr(
            "llm_wiki_cli.extractors.ts_extractor.subprocess.run", fake_run
        )

        TypeScriptExtractor().extract(
            str(tmp_path),
            only_files=["frontend/src/lib/api.ts"],
        )

        cmd = commands[0]
        only_idx = cmd.index("--only-files") + 1
        assert cmd[only_idx] == "frontend/src/lib/api.ts"

    def test_only_files_passes_exact_generated_javascript_bundle_to_subprocess(
        self, tmp_path, monkeypatch
    ):
        generated = "services/dashboard/static/assets/index-D0zaI3XT.js"
        _make_ts(tmp_path, generated, "function a(){};export{a as Ko};")
        commands = []

        def fake_run(cmd, *args, **kwargs):
            commands.append(cmd)
            return subprocess.CompletedProcess(
                cmd,
                0,
                stdout='{"services/dashboard/static/assets/index-D0zaI3XT.js":{"classes":[],"functions":[]}}',
                stderr="",
            )

        monkeypatch.setattr(
            "llm_wiki_cli.extractors.ts_extractor.shutil.which",
            lambda _name: "/bin/tool",
        )
        monkeypatch.setattr(
            "llm_wiki_cli.extractors.ts_extractor.get_prepared_typescript_root",
            lambda *_args: BUNDLED_TS_SCRIPTS,
        )
        monkeypatch.setattr(
            "llm_wiki_cli.extractors.ts_extractor.subprocess.run", fake_run
        )

        TypeScriptExtractor().extract(str(tmp_path), only_files=[generated])

        cmd = commands[0]
        only_idx = cmd.index("--only-files") + 1
        assert cmd[only_idx] == generated

    def test_large_file_selection_is_split_across_subprocess_calls(
        self, tmp_path, monkeypatch
    ):
        paths = ["src/a.ts", "src/b.ts", "src/c.ts"]
        for rel in paths:
            _make_ts(tmp_path, rel, "export class Item {}\n")
        commands = []

        def fake_run(cmd, *args, **kwargs):
            commands.append(cmd)
            only_files = cmd[cmd.index("--only-files") + 1].split(",")
            payload = {rel: {"classes": [], "functions": []} for rel in only_files}
            return subprocess.CompletedProcess(
                cmd,
                0,
                stdout=json.dumps(payload),
                stderr="",
            )

        monkeypatch.setattr(extractor_common, "MAX_ONLY_FILES_ARG_CHARS", 15)
        monkeypatch.setattr(
            "llm_wiki_cli.extractors.ts_extractor.shutil.which",
            lambda _name: "/bin/tool",
        )
        monkeypatch.setattr(
            "llm_wiki_cli.extractors.ts_extractor.get_prepared_typescript_root",
            lambda *_args: BUNDLED_TS_SCRIPTS,
        )
        monkeypatch.setattr(
            "llm_wiki_cli.extractors.ts_extractor.subprocess.run", fake_run
        )

        inv = TypeScriptExtractor().extract(str(tmp_path))

        assert set(inv) == set(paths)
        assert len(commands) > 1
        for cmd in commands:
            only_arg = cmd[cmd.index("--only-files") + 1]
            assert len(only_arg) <= extractor_common.MAX_ONLY_FILES_ARG_CHARS

    def test_js_and_jsx_files_are_extracted_with_javascript_language(
        self, tmp_path, monkeypatch
    ):
        _make_ts(tmp_path, "script.js", "export function run() {}\n")
        _make_ts(tmp_path, "view.jsx", "export function View() { return null; }\n")
        commands = []

        def fake_run(cmd, *args, **kwargs):
            commands.append(cmd)
            return subprocess.CompletedProcess(
                cmd,
                0,
                stdout=json.dumps(
                    {
                        "script.js": {
                            "classes": [],
                            "functions": [{"name": "run"}],
                        },
                        "view.jsx": {
                            "classes": [],
                            "functions": [{"name": "View"}],
                        },
                    }
                ),
                stderr="",
            )

        monkeypatch.setattr(
            "llm_wiki_cli.extractors.ts_extractor.shutil.which",
            lambda _name: "/bin/tool",
        )
        monkeypatch.setattr(
            "llm_wiki_cli.extractors.ts_extractor.get_prepared_typescript_root",
            lambda *_args: BUNDLED_TS_SCRIPTS,
        )
        monkeypatch.setattr(
            "llm_wiki_cli.extractors.ts_extractor.subprocess.run", fake_run
        )

        inv = TypeScriptExtractor().extract(str(tmp_path), deep=True)

        assert set(inv) == {"script.js", "view.jsx"}
        assert {entry["language"] for entry in inv.values()} == {"javascript"}
        cmd = commands[0]
        assert cmd[cmd.index("--extensions") + 1] == ".ts,.tsx,.js,.jsx"
        only_files = cmd[cmd.index("--only-files") + 1].split(",")
        assert only_files == ["script.js", "view.jsx"]


# ===========================================================================
# Unit-level tests (require Node.js)
# ===========================================================================


@skip_no_node
class TestTypeScriptExtractor:
    def test_empty_dir(self, tmp_path):
        inv = TypeScriptExtractor().extract(str(tmp_path))
        assert inv == {}

    def test_single_file_with_class(self, tmp_path):
        _make_ts(
            tmp_path,
            "models.ts",
            """
            export class User {
                name: string;
                age: number;
            }
            """,
        )
        inv = TypeScriptExtractor().extract(str(tmp_path))
        assert len(inv) == 1
        data = list(inv.values())[0]
        assert len(data["classes"]) == 1
        assert data["classes"][0]["name"] == "User"
        assert data["classes"][0]["kind"] == "class"

    def test_language_field_stamped(self, tmp_path):
        _make_ts(tmp_path, "a.ts", "export class A {}")
        inv = TypeScriptExtractor().extract(str(tmp_path))
        for entry in inv.values():
            assert entry["language"] == "typescript"

    def test_single_file_with_function(self, tmp_path):
        _make_ts(
            tmp_path,
            "utils.ts",
            """
            export function greet(name: string): string {
                return `Hello ${name}`;
            }
            """,
        )
        inv = TypeScriptExtractor().extract(str(tmp_path))
        assert len(inv) == 1
        data = list(inv.values())[0]
        assert data["functions"][0]["name"] == "greet"

    def test_arrow_function_export(self, tmp_path):
        _make_ts(
            tmp_path,
            "utils.ts",
            """
            export const add = (a: number, b: number): number => a + b;
            """,
        )
        inv = TypeScriptExtractor().extract(str(tmp_path))
        fns = list(inv.values())[0]["functions"]
        assert any(f["name"] == "add" for f in fns)

    def test_interface_extraction(self, tmp_path):
        _make_ts(
            tmp_path,
            "types.ts",
            """
            export interface Config {
                host: string;
                port: number;
            }
            """,
        )
        inv = TypeScriptExtractor().extract(str(tmp_path))
        classes = list(inv.values())[0]["classes"]
        assert len(classes) == 1
        assert classes[0]["name"] == "Config"
        assert classes[0]["kind"] == "interface"

    def test_enum_extraction(self, tmp_path):
        _make_ts(
            tmp_path,
            "status.ts",
            """
            export enum Status {
                Active = "active",
                Inactive = "inactive",
            }
            """,
        )
        inv = TypeScriptExtractor().extract(str(tmp_path))
        classes = list(inv.values())[0]["classes"]
        assert classes[0]["name"] == "Status"
        assert classes[0]["kind"] == "enum"

    def test_type_alias_extraction(self, tmp_path):
        _make_ts(
            tmp_path,
            "aliases.ts",
            """
            export type UserId = string;
            export type Handler = (event: Event) => void;
            """,
        )
        inv = TypeScriptExtractor().extract(str(tmp_path))
        classes = list(inv.values())[0]["classes"]
        kinds = {c["kind"] for c in classes}
        assert "type_alias" in kinds
        names = {c["name"] for c in classes}
        assert "UserId" in names
        assert "Handler" in names

    def test_tsx_support(self, tmp_path):
        _make_ts(
            tmp_path,
            "Button.tsx",
            """
            export function Button(props: { label: string }) {
                return null;
            }
            """,
        )
        inv = TypeScriptExtractor().extract(str(tmp_path))
        assert len(inv) == 1
        assert list(inv.values())[0]["functions"][0]["name"] == "Button"

    def test_jsx_support(self, tmp_path):
        _make_ts(
            tmp_path,
            "Button.jsx",
            """
            export function Button(props) {
                return null;
            }
            """,
        )
        inv = TypeScriptExtractor().extract(str(tmp_path))
        assert len(inv) == 1
        data = inv["Button.jsx"]
        assert data["language"] == "javascript"
        assert data["functions"][0]["name"] == "Button"

    def test_skips_node_modules(self, tmp_path):
        nm = tmp_path / "node_modules" / "somelib"
        nm.mkdir(parents=True)
        _make_ts(nm, "index.ts", "export class Hidden {}")
        _make_ts(tmp_path, "real.ts", "export class Visible {}")

        inv = TypeScriptExtractor().extract(str(tmp_path))
        assert len(inv) == 1
        assert list(inv.values())[0]["classes"][0]["name"] == "Visible"

    def test_only_files_respects_node_modules(self, tmp_path):
        nm = tmp_path / "node_modules" / "somelib"
        nm.mkdir(parents=True)
        _make_ts(nm, "index.ts", "export class Hidden {}")

        inv = TypeScriptExtractor().extract(
            str(tmp_path),
            only_files=["node_modules/somelib/index.ts"],
        )
        assert inv == {}

    def test_skips_syntax_errors(self, tmp_path):
        (tmp_path / "bad.ts").write_text("export class {{{{", encoding="utf-8")
        _make_ts(tmp_path, "good.ts", "export class OK {}")

        # Should not raise — bad file is skipped gracefully
        inv = TypeScriptExtractor().extract(str(tmp_path))
        names = [c["name"] for entry in inv.values() for c in entry["classes"]]
        assert "OK" in names

    def test_only_files_filter(self, tmp_path):
        _make_ts(tmp_path, "a.ts", "export class A {}")
        _make_ts(tmp_path, "b.ts", "export class B {}")

        inv = TypeScriptExtractor().extract(str(tmp_path), only_files=["a.ts"])
        class_names = [c["name"] for entry in inv.values() for c in entry["classes"]]
        assert "A" in class_names
        assert "B" not in class_names

    def test_bases_extracted(self, tmp_path):
        _make_ts(
            tmp_path,
            "animal.ts",
            """
            export class Animal {}
            export class Dog extends Animal {}
            """,
        )
        inv = TypeScriptExtractor().extract(str(tmp_path))
        classes = list(inv.values())[0]["classes"]
        dog = next(c for c in classes if c["name"] == "Dog")
        assert "Animal" in dog["bases"]

    # ── Deep mode tests ─────────────────────────────────────────────────────

    def test_deep_mode_includes_jsdoc(self, tmp_path):
        _make_ts(
            tmp_path,
            "service.ts",
            """
            /**
             * A service that does things.
             */
            export class MyService {
                /**
                 * Run the service.
                 */
                run(): void {}
            }
            """,
        )
        inv = TypeScriptExtractor().extract(str(tmp_path), deep=True)
        cls = list(inv.values())[0]["classes"][0]
        assert "service" in cls["docstring"].lower() or "things" in cls["docstring"]
        method = cls["methods"][0]
        assert (
            "run" in method["docstring"].lower()
            or "service" in method["docstring"].lower()
        )

    def test_deep_mode_includes_imports(self, tmp_path):
        _make_ts(
            tmp_path,
            "app.ts",
            """
            import { Router } from 'express';
            import path from 'path';

            export class App {
                private router: Router;
            }
            """,
        )
        inv = TypeScriptExtractor().extract(str(tmp_path), deep=True)
        data = list(inv.values())[0]
        assert "imports" in data
        module_names = {imp["module"] for imp in data["imports"]}
        assert "express" in module_names
        assert "path" in module_names

    def test_deep_mode_includes_methods(self, tmp_path):
        _make_ts(
            tmp_path,
            "calc.ts",
            """
            export class Calculator {
                add(a: number, b: number): number {
                    return a + b;
                }
                async fetchResult(id: string): Promise<number> {
                    return 0;
                }
            }
            """,
        )
        inv = TypeScriptExtractor().extract(str(tmp_path), deep=True)
        cls = list(inv.values())[0]["classes"][0]
        assert len(cls["methods"]) == 2
        add = next(m for m in cls["methods"] if m["name"] == "add")
        assert add["params"][0]["name"] == "a"
        assert add["params"][0]["type"] == "number"
        assert add["return_type"] == "number"
        assert add["is_async"] is False

        fetch = next(m for m in cls["methods"] if m["name"] == "fetchResult")
        assert fetch["is_async"] is True

    def test_deep_mode_includes_attributes(self, tmp_path):
        _make_ts(
            tmp_path,
            "user.ts",
            """
            export class User {
                name: string;
                age: number = 0;
            }
            """,
        )
        inv = TypeScriptExtractor().extract(str(tmp_path), deep=True)
        attrs = list(inv.values())[0]["classes"][0]["attributes"]
        names = {a["name"] for a in attrs}
        assert "name" in names
        assert "age" in names
        age_attr = next(a for a in attrs if a["name"] == "age")
        assert age_attr.get("default") == "0"

    def test_deep_mode_decorators(self, tmp_path):
        _make_ts(
            tmp_path,
            "component.ts",
            """
            function Component(target: any) {}

            @Component
            export class MyComponent {
                @Component
                value: string = "";
            }
            """,
        )
        inv = TypeScriptExtractor().extract(str(tmp_path), deep=True)
        cls = list(inv.values())[0]["classes"][0]
        assert "Component" in cls["decorators"]

    def test_enum_deep_members(self, tmp_path):
        _make_ts(
            tmp_path,
            "status.ts",
            """
            export enum Direction {
                Up = "UP",
                Down = "DOWN",
                Left = "LEFT",
                Right = "RIGHT",
            }
            """,
        )
        inv = TypeScriptExtractor().extract(str(tmp_path), deep=True)
        cls = list(inv.values())[0]["classes"][0]
        assert cls["kind"] == "enum"
        member_names = {a["name"] for a in cls["attributes"]}
        assert {"Up", "Down", "Left", "Right"} == member_names

    def test_interface_deep_methods(self, tmp_path):
        _make_ts(
            tmp_path,
            "repo.ts",
            """
            export interface Repository<T> {
                findById(id: string): Promise<T>;
                save(entity: T): Promise<void>;
            }
            """,
        )
        inv = TypeScriptExtractor().extract(str(tmp_path), deep=True)
        cls = list(inv.values())[0]["classes"][0]
        assert cls["kind"] == "interface"
        method_names = {m["name"] for m in cls["methods"]}
        assert "findById" in method_names
        assert "save" in method_names


# ===========================================================================
# Graceful-degradation tests (Node.js mocked away, no Node.js required)
# ===========================================================================


class TestTypeScriptExtractorWithoutNode:
    def test_node_not_available_returns_empty(self, tmp_path):
        _make_ts(tmp_path, "app.ts", "export class App {}")
        with patch("shutil.which", return_value=None):
            inv = TypeScriptExtractor().extract(str(tmp_path))
        assert inv == {}

    def test_node_not_available_warns_to_stderr(self, tmp_path, capsys):
        _make_ts(tmp_path, "app.ts", "export class App {}")
        with patch("shutil.which", return_value=None):
            TypeScriptExtractor().extract(str(tmp_path))
        err = capsys.readouterr().err
        assert (
            "node" in err.lower() or "nodejs" in err.lower() or "node.js" in err.lower()
        )

    def test_no_ts_files_skips_toolchain_probe(self, tmp_path):
        with patch("llm_wiki_cli.extractors.ts_extractor.shutil.which") as mock_which:
            inv = TypeScriptExtractor().extract(str(tmp_path))
        assert inv == {}
        mock_which.assert_not_called()


class TestTypeScriptExtractorWrapper:
    def test_extract_remains_short_orchestrator(self):
        source = textwrap.dedent(inspect.getsource(TypeScriptExtractor.extract))
        function_node = ast.parse(source).body[0]
        assert isinstance(function_node, ast.FunctionDef)
        body = list(function_node.body)
        if (
            body
            and isinstance(body[0], ast.Expr)
            and isinstance(body[0].value, ast.Constant)
            and isinstance(body[0].value.value, str)
        ):
            body = body[1:]

        first_body_line = min(stmt.lineno for stmt in body)
        last_body_line = max(stmt.end_lineno or stmt.lineno for stmt in body)
        body_lines = last_body_line - first_body_line + 1

        assert body_lines <= 35

    def test_missing_dependencies_do_not_invoke_npm_install(self, tmp_path):
        _make_ts(tmp_path, "app.ts", "export class App {}")
        with patch(
            "llm_wiki_cli.extractors.ts_extractor.shutil.which", return_value="node"
        ):
            with patch(
                "llm_wiki_cli.extractors.ts_extractor.get_prepared_typescript_root",
                return_value=None,
            ):
                with patch(
                    "llm_wiki_cli.extractors.ts_extractor.subprocess.run"
                ) as mock_run:
                    inv = TypeScriptExtractor().extract(str(tmp_path))

        assert inv == {}
        mock_run.assert_not_called()

    def test_normalization_filters_checkout_helper_but_not_unrelated_suffix(
        self, tmp_path
    ):
        _write_owned_package_sentinels(tmp_path)
        bundled = "src/llm_wiki_cli/extractors/ts_scripts/extract.js"
        unrelated = "vendor/llm_wiki_cli/extractors/ts_scripts/extract.js"
        _make_ts(tmp_path, bundled, "export function extract() {}\n")
        _make_ts(tmp_path, unrelated, "export function consumer() {}\n")
        inventory = {
            bundled: {"classes": [], "functions": []},
            unrelated: {"classes": [], "functions": []},
        }

        normalized = TypeScriptExtractor()._normalize_inventory(
            str(tmp_path),
            inventory,
            BUNDLED_TS_SCRIPTS,
        )

        assert list(normalized) == [unrelated]

    def test_relative_external_helper_suffix_fails_open_across_both_filter_stages(
        self, tmp_path, monkeypatch
    ):
        external_root = tmp_path / "external-consumer"
        relative_path = "src/llm_wiki_cli/extractors/ts_scripts/extract.js"
        _make_ts(external_root, relative_path, "export function consumer() {}\n")
        monkeypatch.chdir(Path(__file__).parents[1])
        result = subprocess.CompletedProcess(
            args=["node"],
            returncode=0,
            stdout=json.dumps(
                {relative_path: {"classes": [], "functions": []}}
            ),
            stderr="",
        )
        extractor = TypeScriptExtractor()

        loaded = extractor._load_inventory(result)
        normalized = extractor._normalize_inventory(
            str(external_root), loaded, BUNDLED_TS_SCRIPTS
        )

        assert list(loaded) == [relative_path]
        assert list(normalized) == [relative_path]

    def test_windows_style_inventory_keys_are_normalized(self, tmp_path):
        _make_ts(tmp_path, "web/src/app.ts", "export class App {}")
        result = subprocess.CompletedProcess(
            args=["node"],
            returncode=0,
            stdout='{"web\\\\src\\\\app.ts": {"classes": [], "functions": []}}',
            stderr="",
        )
        with patch(
            "llm_wiki_cli.extractors.ts_extractor.shutil.which", return_value="node"
        ):
            with patch(
                "llm_wiki_cli.extractors.ts_extractor.get_prepared_typescript_root",
                return_value=BUNDLED_TS_SCRIPTS,
            ):
                with patch(
                    "llm_wiki_cli.extractors.ts_extractor.subprocess.run",
                    return_value=result,
                ):
                    inv = TypeScriptExtractor().extract(str(tmp_path))

        assert "web/src/app.ts" in inv
        assert "web\\src\\app.ts" not in inv
        assert inv["web/src/app.ts"]["language"] == "typescript"

    def test_malformed_json_returns_empty(self, tmp_path, capsys):
        _make_ts(tmp_path, "app.ts", "export class App {}")
        result = subprocess.CompletedProcess(
            args=["node"],
            returncode=0,
            stdout="{not-json",
            stderr="",
        )
        with patch(
            "llm_wiki_cli.extractors.ts_extractor.shutil.which", return_value="node"
        ):
            with patch(
                "llm_wiki_cli.extractors.ts_extractor.get_prepared_typescript_root",
                return_value=BUNDLED_TS_SCRIPTS,
            ):
                with patch(
                    "llm_wiki_cli.extractors.ts_extractor.subprocess.run",
                    return_value=result,
                ):
                    inv = TypeScriptExtractor().extract(str(tmp_path))

        assert inv == {}
        assert "malformed JSON" in capsys.readouterr().err

    def test_timeout_returns_empty_and_names_configuration(
        self, tmp_path, capsys, monkeypatch
    ):
        _make_ts(tmp_path, "app.ts", "export class App {}")
        monkeypatch.setenv("LLM_WIKI_EXTRACTOR_TIMEOUT", "37")
        with patch(
            "llm_wiki_cli.extractors.ts_extractor.shutil.which", return_value="node"
        ):
            with patch(
                "llm_wiki_cli.extractors.ts_extractor.get_prepared_typescript_root",
                return_value=BUNDLED_TS_SCRIPTS,
            ):
                with patch(
                    "llm_wiki_cli.extractors.ts_extractor.subprocess.run",
                    side_effect=subprocess.TimeoutExpired(["node"], 37),
                ) as mock_run:
                    extractor = TypeScriptExtractor()
                    inv = extractor.extract(str(tmp_path))

        assert inv == {}
        assert mock_run.call_args.kwargs["timeout"] == 37
        assert extractor.last_error is not None
        assert "LLM_WIKI_EXTRACTOR_TIMEOUT" in extractor.last_error
        assert "LLM_WIKI_EXTRACTOR_TIMEOUT" in capsys.readouterr().err


# ===========================================================================
# Integration: both .py and .ts files in same directory
# ===========================================================================


@skip_no_node
class TestExtractorRegistryIntegration:
    def test_extract_command_merges_both_languages(self, tmp_path):
        """Running all registered extractors on a mixed dir returns both languages."""
        from llm_wiki_cli.commands.extract_cmd import _load_extractor
        from llm_wiki_cli.config import EXTRACTOR_REGISTRY

        (tmp_path / "models.py").write_text(
            textwrap.dedent("class PythonModel:\n    pass\n"), encoding="utf-8"
        )
        _make_ts(tmp_path, "models.ts", "export class TypeScriptModel {}")

        inventory: dict = {}
        for _lang, entry_point in EXTRACTOR_REGISTRY.items():
            extractor = _load_extractor(entry_point)
            inventory.update(extractor.extract(str(tmp_path)))

        languages = {entry["language"] for entry in inventory.values()}
        assert "python" in languages
        assert "typescript" in languages

    def test_typescript_entry_in_registry(self):
        from llm_wiki_cli.config import EXTRACTOR_REGISTRY

        assert "typescript" in EXTRACTOR_REGISTRY
        assert "TypeScriptExtractor" in EXTRACTOR_REGISTRY["typescript"]


# ===========================================================================
# Tests for gap/bug fixes
# ===========================================================================


@skip_no_node
class TestTypeScriptExtractorFixes:
    """Tests specifically validating the gap-analysis bug fixes."""

    def test_interface_bases_external_type(self, tmp_path):
        """getExtends() must report bases even when the type is from an unresolved
        external module (getBaseDeclarations() would silently return [] here)."""
        _make_ts(
            tmp_path,
            "emitter.ts",
            """
            import { EventEmitter } from 'events';
            export interface MyEmitter extends EventEmitter {
                onData: () => void;
            }
            """,
        )
        inv = TypeScriptExtractor().extract(str(tmp_path))
        classes = list(inv.values())[0]["classes"]
        iface = next((c for c in classes if c["name"] == "MyEmitter"), None)
        assert iface is not None
        assert "EventEmitter" in iface["bases"]

    def test_module_docstring_captured(self, tmp_path):
        """deep mode must capture a module-level /** ... */ comment."""
        _make_ts(
            tmp_path,
            "utils.ts",
            """
            /** @module utils - Utility helpers for the project. */
            export function add(a: number, b: number): number {
                return a + b;
            }
            """,
        )
        inv = TypeScriptExtractor().extract(str(tmp_path), deep=True)
        data = list(inv.values())[0]
        assert "module_docstring" in data
        assert (
            "utils" in data["module_docstring"].lower()
            or "utility" in data["module_docstring"].lower()
        )

    def test_anonymous_class_disambiguated(self, tmp_path):
        """An anonymous class (export default class {}) gets a line-disambiguated name
        instead of the bare '<anonymous>' that would collide across files."""
        _make_ts(
            tmp_path,
            "handler.ts",
            """
            /** Default handler */
            export default class {
                run() {}
            }
            """,
        )
        inv = TypeScriptExtractor().extract(str(tmp_path))
        classes = list(inv.values())[0]["classes"]
        assert len(classes) == 1
        name = classes[0]["name"]
        # Must not be the bare '<anonymous>' that caused collisions;
        # must contain the line number for disambiguation.
        assert name.startswith("<anonymous_L"), (
            f"Expected disambiguated name, got: {name!r}"
        )

    def test_dts_files_included(self, tmp_path):
        """First-party declaration files (.d.ts) appear in the inventory."""
        (tmp_path / "types.d.ts").write_text(
            "export declare class Phantom {}\n", encoding="utf-8"
        )
        _make_ts(tmp_path, "real.ts", "export class Real {}")
        inv = TypeScriptExtractor().extract(str(tmp_path), deep=True)

        assert "types.d.ts" in inv
        assert "real.ts" in inv
        dts_classes = [c["name"] for c in inv["types.d.ts"]["classes"]]
        assert "Phantom" in dts_classes

    def test_shallow_module_only_javascript_file_is_retained(self, tmp_path):
        _make_ts(
            tmp_path,
            "docker/proxy.js",
            """
            const http = require("node:http");
            const listenPort = Number.parseInt(process.env.PORT || "3000", 10);
            const server = http.createServer((req, res) => {
              res.end("ok");
            });
            server.listen(listenPort);
            """,
        )

        inv = TypeScriptExtractor().extract(str(tmp_path), deep=False)

        assert sorted(inv) == ["docker/proxy.js"]
        data = inv["docker/proxy.js"]
        assert data["language"] == "javascript"
        assert data["classes"] == []
        assert data["functions"] == []
        assert [constant["name"] for constant in data["constants"]] == [
            "http",
            "listenPort",
            "server",
        ]
        assert [call["name"] for call in data["module_calls"]] == [
            "require",
            "parseInt",
            "createServer",
            "listen",
        ]

    def test_tsconfig_walk_up(self, tmp_path):
        """tsconfig.json one level above srcDir must be discovered automatically."""
        # Write a minimal tsconfig at the parent level.
        tsconfig = {"compilerOptions": {"strict": True}}
        import json as _json

        (tmp_path / "tsconfig.json").write_bytes(_json.dumps(tsconfig).encode("utf-8"))
        src = tmp_path / "src"
        src.mkdir()
        _make_ts(src, "app.ts", "export class App {}")
        # Extract from src/ — tsconfig is at tmp_path/tsconfig.json (one level up).
        inv = TypeScriptExtractor().extract(str(src))
        assert len(inv) == 1
        assert list(inv.values())[0]["classes"][0]["name"] == "App"

    def test_inventory_keys_are_relative(self, tmp_path):
        """Inventory keys must match Python/Go/Rust by being srcDir-relative."""
        nested = tmp_path / "web" / "src"
        nested.mkdir(parents=True)
        _make_ts(nested, "app.ts", "export class App {}")

        inv = TypeScriptExtractor().extract(str(tmp_path))

        assert "web/src/app.ts" in inv
        assert all(not Path(key).is_absolute() for key in inv)

    def test_stderr_forwarded_on_success(self, tmp_path, capsys):
        """Warnings written to Node.js stderr must reach Python sys.stderr."""
        from unittest.mock import patch, MagicMock

        _make_ts(tmp_path, "file.ts", "export class File {}")

        # Simulate a successful Node.js run that also emits a warning on stderr.
        fake_result = MagicMock()
        fake_result.stdout = '{"file.ts": {"classes": [], "functions": []}}'
        fake_result.stderr = "Warning: could not resolve some types\n"

        with patch("subprocess.run", return_value=fake_result):
            TypeScriptExtractor().extract(str(tmp_path))

        err = capsys.readouterr().err
        assert "Warning" in err

    def test_file_named_like_excluded_dir(self, tmp_path):
        """A file named dist.ts inside a valid directory must NOT be excluded."""
        _make_ts(tmp_path, "dist.ts", "export class Dist {}")
        _make_ts(tmp_path, "build.ts", "export class Build {}")
        inv = TypeScriptExtractor().extract(str(tmp_path))
        all_names = [c["name"] for entry in inv.values() for c in entry["classes"]]
        assert "Dist" in all_names
        assert "Build" in all_names

    def test_deep_includes_entrypoint_setup_module(self, tmp_path):
        _make_ts(
            tmp_path,
            "main.tsx",
            """
            import React from 'react';
            import ReactDOM from 'react-dom/client';
            import App from './App';

            const queryClient = new QueryClient();
            ReactDOM.createRoot(document.getElementById('root')!).render(<App />);
            """,
        )

        inv = TypeScriptExtractor().extract(str(tmp_path), deep=True)

        data = inv["main.tsx"]
        assert data["classes"] == []
        assert data["functions"] == []
        assert {imp["module"] for imp in data["imports"]} >= {
            "react",
            "react-dom/client",
            "./App",
        }
        assert data["constants"] == [
            {"name": "queryClient", "line": 6, "exported": False}
        ]
        assert [call["name"] for call in data["module_calls"]] == [
            "QueryClient",
            "render",
        ]

    def test_deep_includes_service_client_setup_module(self, tmp_path):
        _make_ts(
            tmp_path,
            "api.ts",
            """
            import axios, { AxiosInstance } from 'axios';

            const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
            const api: AxiosInstance = axios.create({ baseURL: `${BASE_URL}/api/v1` });

            api.interceptors.request.use((config) => config);

            export default api;
            """,
        )

        data = TypeScriptExtractor().extract(str(tmp_path), deep=True)["api.ts"]

        assert data["exports"] == ["default"]
        constants = {constant["name"]: constant for constant in data["constants"]}
        assert constants["BASE_URL"]["exported"] is False
        assert constants["api"]["line"] == 5
        assert [call["name"] for call in data["module_calls"]] == ["create", "use"]

    def test_deep_includes_exported_query_client_constant(self, tmp_path):
        _make_ts(
            tmp_path,
            "queryClient.ts",
            """
            import { QueryClient } from '@tanstack/react-query';

            export const queryClient = new QueryClient({
              defaultOptions: { queries: { retry: 1 } },
            });
            """,
        )

        data = TypeScriptExtractor().extract(str(tmp_path), deep=True)["queryClient.ts"]

        assert data["exports"] == ["queryClient"]
        assert data["constants"] == [
            {"name": "queryClient", "line": 4, "exported": True}
        ]
        assert data["module_calls"] == [
            {"name": "QueryClient", "target": "queryClient", "line": 4}
        ]

    def test_commonjs_default_assignment_surfaces_top_level_function(self, tmp_path):
        _make_ts(
            tmp_path,
            "SimpleRegister.tsx",
            """
            Object.defineProperty(exports, "__esModule", { value: true });
            exports.default = SimpleRegister;

            function SimpleRegister() {
              return null;
            }
            """,
        )

        data = TypeScriptExtractor().extract(str(tmp_path), deep=True)[
            "SimpleRegister.tsx"
        ]

        assert data["exports"] == ["default"]
        assert [fn["name"] for fn in data["functions"]] == ["SimpleRegister"]

    def test_plain_js_commonjs_service_surfaces_top_level_functions(self, tmp_path):
        _make_ts(
            tmp_path,
            "docker/web-auth-proxy.js",
            """\
            const http = require("node:http");

            function isTruthy(value) {
              return Boolean(value);
            }

            function withAuthHeaders(headers = {}) {
              return { ...headers, authorization: "Bearer token" };
            }

            function rewriteJsonPayload(req, payload) {
              return payload;
            }

            const server = http.createServer((req, res) => {
              res.end(rewriteJsonPayload(req, {}));
            });
            """,
        )

        data = TypeScriptExtractor().extract(str(tmp_path), deep=True)[
            "docker/web-auth-proxy.js"
        ]

        assert data["language"] == "javascript"
        assert [fn["name"] for fn in data["functions"]] == [
            "isTruthy",
            "withAuthHeaders",
            "rewriteJsonPayload",
        ]
        by_name = {fn["name"]: fn for fn in data["functions"]}
        assert by_name["isTruthy"]["line"] == 3
        assert by_name["isTruthy"]["kind"] == "function"
        assert by_name["isTruthy"]["end_line"] == 5
        assert by_name["withAuthHeaders"]["params"] == [
            {"name": "headers", "type": "", "default": "{}"}
        ]
        assert {"name": "createServer", "target": "server", "line": 15} in data[
            "module_calls"
        ]

    def test_plain_js_create_server_named_handler_records_argument(self, tmp_path):
        _make_ts(
            tmp_path,
            "server.js",
            """\
            const http = require("node:http");

            function handleRequest(req, res) {
              res.end("ok");
            }

            const server = http.createServer(handleRequest);
            """,
        )

        data = TypeScriptExtractor().extract(str(tmp_path), deep=True)["server.js"]

        assert {
            "name": "createServer",
            "target": "server",
            "line": 7,
            "args": ["handleRequest"],
        } in data["module_calls"]

    def test_non_exported_typescript_family_functions_stay_private(self, tmp_path):
        _make_ts(
            tmp_path,
            "hidden.ts",
            """\
            export const visible = 1;
            function privateTs() {
              return visible;
            }
            """,
        )
        _make_ts(
            tmp_path,
            "Hidden.tsx",
            """\
            export function PublicTsx() {
              return null;
            }
            function privateTsx() {
              return null;
            }
            """,
        )
        _make_ts(
            tmp_path,
            "Hidden.jsx",
            """\
            export default function PublicJsx() {
              return null;
            }
            function privateJsx() {
              return null;
            }
            """,
        )

        inv = TypeScriptExtractor().extract(str(tmp_path), deep=True)

        assert [fn["name"] for fn in inv["hidden.ts"]["functions"]] == []
        assert [fn["name"] for fn in inv["Hidden.tsx"]["functions"]] == ["PublicTsx"]
        assert [fn["name"] for fn in inv["Hidden.jsx"]["functions"]] == ["PublicJsx"]

    def test_empty_typescript_file_reports_deep_skip_diagnostic(self, tmp_path, capsys):
        _make_ts(tmp_path, "empty.ts", "// comments only\n")

        inv = TypeScriptExtractor().extract(str(tmp_path), deep=True)

        assert inv == {}
        err = capsys.readouterr().err
        assert "skipped empty.ts" in err
        assert "no documentable TypeScript declarations" in err
