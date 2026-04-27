"""Tests for the TypeScript extractor (ts_extractor.py + ts_scripts/extract.js)."""

from __future__ import annotations

import shutil
import textwrap
from pathlib import Path
from unittest.mock import patch

import pytest

from llm_wiki_cli.extractors.ts_extractor import TypeScriptExtractor

# ---------------------------------------------------------------------------
# Skip all tests when Node.js is not available on this machine.
# ---------------------------------------------------------------------------

NODE_AVAILABLE = shutil.which("node") is not None
skip_no_node = pytest.mark.skipif(
    not NODE_AVAILABLE,
    reason="Node.js not found — TypeScript extractor tests skipped",
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_ts(tmp_path: Path, filename: str, content: str) -> Path:
    p = tmp_path / filename
    p.write_text(textwrap.dedent(content), encoding="utf-8")
    return p


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

    def test_skips_node_modules(self, tmp_path):
        nm = tmp_path / "node_modules" / "somelib"
        nm.mkdir(parents=True)
        _make_ts(nm, "index.ts", "export class Hidden {}")
        _make_ts(tmp_path, "real.ts", "export class Visible {}")

        inv = TypeScriptExtractor().extract(str(tmp_path))
        assert len(inv) == 1
        assert list(inv.values())[0]["classes"][0]["name"] == "Visible"

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
        assert "run" in method["docstring"].lower() or "service" in method["docstring"].lower()

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
        with patch("shutil.which", return_value=None):
            inv = TypeScriptExtractor().extract(str(tmp_path))
        assert inv == {}

    def test_node_not_available_warns_to_stderr(self, tmp_path, capsys):
        with patch("shutil.which", return_value=None):
            TypeScriptExtractor().extract(str(tmp_path))
        err = capsys.readouterr().err
        assert "node" in err.lower() or "nodejs" in err.lower() or "node.js" in err.lower()


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
        assert "utils" in data["module_docstring"].lower() or "utility" in data["module_docstring"].lower()

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
        assert name.startswith("<anonymous_L"), f"Expected disambiguated name, got: {name!r}"

    def test_dts_files_excluded(self, tmp_path):
        """Declaration files (.d.ts) must not appear in the inventory."""
        (tmp_path / "types.d.ts").write_text(
            "export declare class Phantom {}\n", encoding="utf-8"
        )
        _make_ts(tmp_path, "real.ts", "export class Real {}")
        inv = TypeScriptExtractor().extract(str(tmp_path))
        all_classes = [c["name"] for entry in inv.values() for c in entry["classes"]]
        assert "Real" in all_classes
        assert "Phantom" not in all_classes

    def test_tsconfig_walk_up(self, tmp_path):
        """tsconfig.json one level above srcDir must be discovered automatically."""
        # Write a minimal tsconfig at the parent level.
        tsconfig = {"compilerOptions": {"strict": True}}
        import json as _json
        (tmp_path / "tsconfig.json").write_bytes(
            _json.dumps(tsconfig).encode("utf-8")
        )
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
        import subprocess
        from unittest.mock import patch, MagicMock
        from llm_wiki_cli.extractors import ts_extractor

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
