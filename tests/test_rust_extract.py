"""Tests for the Rust extractor (rust_extractor.py + rust_scripts/src/main.rs)."""

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

from llm_wiki_cli.config import EXTRACTOR_REGISTRY
from llm_wiki_cli.extractors import common as extractor_common
from llm_wiki_cli.extractors.rust_extractor import RustExtractionRequest, RustExtractor
from llm_wiki_cli.services.extractor_helpers import (
    get_prepared_binary,
    resolve_helper_cache_root,
)

# ---------------------------------------------------------------------------
# Skip all tests when Rust toolchain is not available on this machine.
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


def _repo_helper_cache_dir() -> str | None:
    cache_root = resolve_helper_cache_root(".")
    if cache_root is None:
        return None
    cache_dir = str(cache_root.parent)
    if get_prepared_binary("rust", ".", cache_dir) is None:
        return None
    return cache_dir


RUST_HELPER_CACHE_DIR = _repo_helper_cache_dir()
CARGO_AVAILABLE = RUST_HELPER_CACHE_DIR is not None
skip_no_cargo = pytest.mark.skipif(
    not CARGO_AVAILABLE,
    reason="Prepared Rust helper not available — Rust extractor integration tests skipped",
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _body_line_count(function) -> int:
    source = textwrap.dedent(inspect.getsource(function))
    function_node = ast.parse(source).body[0]
    assert isinstance(function_node, ast.FunctionDef)

    body = [
        stmt
        for stmt in function_node.body
        if not (
            isinstance(stmt, ast.Expr)
            and isinstance(stmt.value, ast.Constant)
            and isinstance(stmt.value.value, str)
        )
    ]
    first_body_line = min(stmt.lineno for stmt in body)
    last_body_line = max(stmt.end_lineno or stmt.lineno for stmt in body)
    return last_body_line - first_body_line + 1


def _make_rs(tmp_path: Path, filename: str, content: str) -> Path:
    """Write a Rust source file under *tmp_path* and return its path."""
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
        _make_rs(root, rel_path, "# package source\n")


def _extract_rust(
    tmp_path: Path,
    *,
    only_files: list[str] | None = None,
    deep: bool = False,
) -> dict:
    return RustExtractor().extract(
        RustExtractionRequest(
            src_dir=str(tmp_path),
            only_files=only_files,
            deep=deep,
            helper_cache_dir=RUST_HELPER_CACHE_DIR,
        )
    )


class TestRustWrapperFiltering:
    def test_full_scan_passes_gitignore_filtered_files_to_subprocess(
        self, tmp_path, monkeypatch
    ):
        _make_rs(tmp_path, "real.rs", "pub struct Real;\n")
        _make_rs(tmp_path, "ignored.rs", "pub struct Ignored;\n")
        (tmp_path / ".gitignore").write_text("ignored.rs\n", encoding="utf-8")
        commands = []

        def fake_run(cmd, *args, **kwargs):
            commands.append(cmd)
            return subprocess.CompletedProcess(
                cmd,
                0,
                stdout='{"real.rs":{"classes":[],"functions":[]}}',
                stderr="",
            )

        monkeypatch.setattr(
            "llm_wiki_cli.extractors.rust_extractor.get_prepared_binary",
            lambda *a, **k: Path("/tmp/rust-helper"),
        )
        monkeypatch.setattr(
            "llm_wiki_cli.extractors.rust_extractor.subprocess.run", fake_run
        )

        RustExtractor().extract(str(tmp_path))

        cmd = commands[0]
        only_idx = cmd.index("--only-files") + 1
        assert cmd[only_idx] == "real.rs"

    def test_large_file_selection_is_split_across_subprocess_calls(
        self, tmp_path, monkeypatch
    ):
        paths = ["src/a.rs", "src/b.rs", "src/c.rs"]
        for rel in paths:
            _make_rs(tmp_path, rel, "pub struct Item;\n")
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
            "llm_wiki_cli.extractors.rust_extractor.get_prepared_binary",
            lambda *a, **k: Path("/tmp/rust-helper"),
        )
        monkeypatch.setattr(
            "llm_wiki_cli.extractors.rust_extractor.subprocess.run", fake_run
        )

        inv = RustExtractor().extract(str(tmp_path))

        assert set(inv) == set(paths)
        assert len(commands) > 1
        for cmd in commands:
            only_arg = cmd[cmd.index("--only-files") + 1]
            assert len(only_arg) <= extractor_common.MAX_ONLY_FILES_ARG_CHARS


# ===========================================================================
# Unit-level tests (require Rust)
# ===========================================================================


@skip_no_cargo
class TestRustExtractor:
    def test_empty_dir(self, tmp_path):
        inv = _extract_rust(tmp_path)
        assert inv == {}

    def test_single_struct(self, tmp_path):
        _make_rs(
            tmp_path,
            "models.rs",
            """\
            pub struct User {
                pub name: String,
                pub age: u32,
            }
            """,
        )
        inv = _extract_rust(tmp_path)
        assert len(inv) == 1
        data = list(inv.values())[0]
        assert len(data["classes"]) == 1
        assert data["classes"][0]["name"] == "User"
        assert data["classes"][0]["kind"] == "struct"

    def test_language_field_stamped(self, tmp_path):
        _make_rs(tmp_path, "a.rs", "pub struct A;\n")
        inv = _extract_rust(tmp_path)
        for entry in inv.values():
            assert entry["language"] == "rust"

    def test_enum_extraction(self, tmp_path):
        _make_rs(
            tmp_path,
            "status.rs",
            """\
            pub enum Status {
                Active,
                Inactive,
            }
            """,
        )
        inv = _extract_rust(tmp_path)
        data = list(inv.values())[0]
        assert len(data["classes"]) == 1
        assert data["classes"][0]["name"] == "Status"
        assert data["classes"][0]["kind"] == "enum"

    def test_trait_extraction(self, tmp_path):
        _make_rs(
            tmp_path,
            "traits.rs",
            """\
            pub trait Drawable {
                fn draw(&self);
            }
            """,
        )
        inv = _extract_rust(tmp_path)
        data = list(inv.values())[0]
        assert len(data["classes"]) == 1
        assert data["classes"][0]["name"] == "Drawable"
        assert data["classes"][0]["kind"] == "trait"

    def test_type_alias(self, tmp_path):
        _make_rs(
            tmp_path,
            "types.rs",
            """\
            pub type UserId = u64;
            """,
        )
        inv = _extract_rust(tmp_path)
        data = list(inv.values())[0]
        assert any(
            c["name"] == "UserId" and c["kind"] == "type_alias" for c in data["classes"]
        )

    def test_exported_function(self, tmp_path):
        _make_rs(
            tmp_path,
            "utils.rs",
            """\
            pub fn greet(name: &str) -> String {
                format!("Hello {}", name)
            }
            """,
        )
        inv = _extract_rust(tmp_path)
        data = list(inv.values())[0]
        assert len(data["functions"]) == 1
        assert data["functions"][0]["name"] == "greet"

    def test_private_skipped(self, tmp_path):
        _make_rs(
            tmp_path,
            "utils.rs",
            """\
            fn helper_private() {}

            pub fn public_func() {}
            """,
        )
        inv = _extract_rust(tmp_path)
        data = list(inv.values())[0]
        names = [f["name"] for f in data["functions"]]
        assert "public_func" in names
        assert "helper_private" not in names

    def test_only_files(self, tmp_path):
        _make_rs(tmp_path, "a.rs", "pub struct A;\n")
        _make_rs(tmp_path, "b.rs", "pub struct B;\n")
        inv = _extract_rust(tmp_path, only_files=["a.rs"])
        assert len(inv) == 1
        assert any("a.rs" in k for k in inv)

    def test_only_files_respects_excluded_dirs(self, tmp_path):
        _make_rs(tmp_path, "target/debug/build/dep.rs", "pub struct Dep;\n")
        inv = _extract_rust(tmp_path, only_files=["target/debug/build/dep.rs"])
        assert inv == {}

    def test_target_excluded(self, tmp_path):
        _make_rs(tmp_path, "main.rs", "pub struct App;\n")
        _make_rs(
            tmp_path,
            "target/debug/build/dep.rs",
            "pub struct Dep;\n",
        )
        inv = _extract_rust(tmp_path)
        assert len(inv) == 1
        assert not any("target" in k for k in inv)

    def test_impl_bases(self, tmp_path):
        _make_rs(
            tmp_path,
            "models.rs",
            """\
            pub trait Greetable {
                fn greet(&self) -> String;
            }

            pub struct User {
                pub name: String,
            }

            impl Greetable for User {
                fn greet(&self) -> String {
                    format!("Hello {}", self.name)
                }
            }
            """,
        )
        inv = _extract_rust(tmp_path)
        data = list(inv.values())[0]
        user = [c for c in data["classes"] if c["name"] == "User"][0]
        assert "Greetable" in user["bases"]

    def test_derive_as_decorators(self, tmp_path):
        _make_rs(
            tmp_path,
            "models.rs",
            """\
            #[derive(Debug, Clone)]
            pub struct Config {
                pub value: String,
            }
            """,
        )
        inv = _extract_rust(tmp_path, deep=True)
        data = list(inv.values())[0]
        config = data["classes"][0]
        assert "Debug" in config["decorators"]
        assert "Clone" in config["decorators"]

    def test_multiple_files(self, tmp_path):
        _make_rs(tmp_path, "a.rs", "pub struct Alpha;\n")
        _make_rs(tmp_path, "sub/b.rs", "pub struct Beta;\n")
        inv = _extract_rust(tmp_path)
        assert len(inv) == 2

    def test_syntax_error_graceful(self, tmp_path):
        """Files with syntax errors are skipped with a warning, not a crash."""
        _make_rs(tmp_path, "good.rs", "pub struct Good;\n")
        _make_rs(tmp_path, "bad.rs", "pub struct Bad {\n")  # missing closing brace
        inv = _extract_rust(tmp_path)
        # Should still get the good file.
        assert any("good.rs" in k for k in inv)

    def test_cfg_test_skipped(self, tmp_path):
        """Items inside #[cfg(test)] mod should be excluded."""
        _make_rs(
            tmp_path,
            "lib.rs",
            """\
            pub struct Real;

            #[cfg(test)]
            mod tests {
                pub struct TestOnly;
            }
            """,
        )
        inv = _extract_rust(tmp_path)
        data = list(inv.values())[0]
        names = [c["name"] for c in data["classes"]]
        assert "Real" in names
        assert "TestOnly" not in names

    # ── Deep mode tests ───────────────────────────────────────────────────

    def test_deep_struct_docstring(self, tmp_path):
        _make_rs(
            tmp_path,
            "models.rs",
            """\
            /// A registered user in the system.
            pub struct User {
                pub name: String,
            }
            """,
        )
        inv = _extract_rust(tmp_path, deep=True)
        data = list(inv.values())[0]
        user = data["classes"][0]
        assert "registered user" in user["docstring"]

    def test_deep_struct_attributes(self, tmp_path):
        _make_rs(
            tmp_path,
            "models.rs",
            """\
            pub struct User {
                pub name: String,
                pub email: String,
            }
            """,
        )
        inv = _extract_rust(tmp_path, deep=True)
        data = list(inv.values())[0]
        attrs = data["classes"][0]["attributes"]
        names = [a["name"] for a in attrs]
        assert "name" in names
        assert "email" in names

    def test_deep_impl_methods(self, tmp_path):
        _make_rs(
            tmp_path,
            "models.rs",
            """\
            pub struct User {
                pub name: String,
            }

            impl User {
                /// Greet the user.
                pub fn greet(&self) -> String {
                    format!("Hello {}", self.name)
                }
            }
            """,
        )
        inv = _extract_rust(tmp_path, deep=True)
        data = list(inv.values())[0]
        user = [c for c in data["classes"] if c["name"] == "User"][0]
        assert len(user["methods"]) == 1
        assert user["methods"][0]["name"] == "greet"

    def test_deep_function_params(self, tmp_path):
        _make_rs(
            tmp_path,
            "utils.rs",
            """\
            /// Add two numbers.
            pub fn add(a: i32, b: i32) -> i32 {
                a + b
            }
            """,
        )
        inv = _extract_rust(tmp_path, deep=True)
        data = list(inv.values())[0]
        fn_info = data["functions"][0]
        assert fn_info["name"] == "add"
        assert fn_info["docstring"] == "Add two numbers."
        param_names = [p["name"] for p in fn_info["params"]]
        assert "a" in param_names
        assert "b" in param_names
        assert fn_info["return_type"] == "i32"

    def test_deep_trait_methods(self, tmp_path):
        _make_rs(
            tmp_path,
            "traits.rs",
            """\
            /// A writer trait.
            pub trait Writer {
                fn write(&mut self, data: &[u8]) -> usize;
            }
            """,
        )
        inv = _extract_rust(tmp_path, deep=True)
        data = list(inv.values())[0]
        writer = data["classes"][0]
        assert writer["docstring"] == "A writer trait."
        assert len(writer["methods"]) == 1
        assert writer["methods"][0]["name"] == "write"

    def test_deep_imports(self, tmp_path):
        _make_rs(
            tmp_path,
            "main.rs",
            """\
            use std::collections::HashMap;
            use std::io::Read;

            pub fn main() {}
            """,
        )
        inv = _extract_rust(tmp_path, deep=True)
        data = list(inv.values())[0]
        assert "imports" in data
        modules = [i["module"] for i in data["imports"]]
        assert "std::collections::HashMap" in modules
        assert "std::io::Read" in modules

    def test_deep_enum_variants(self, tmp_path):
        _make_rs(
            tmp_path,
            "status.rs",
            """\
            pub enum Direction {
                Up,
                Down,
                Left,
                Right,
            }
            """,
        )
        inv = _extract_rust(tmp_path, deep=True)
        data = list(inv.values())[0]
        cls = data["classes"][0]
        assert cls["kind"] == "enum"
        member_names = {a["name"] for a in cls["attributes"]}
        assert {"Up", "Down", "Left", "Right"} == member_names

    def test_deep_cross_file_impl(self, tmp_path):
        """In deep mode, an impl in a separate file attaches to its struct."""
        _make_rs(
            tmp_path,
            "models.rs",
            """\
            pub struct User {
                pub name: String,
            }
            """,
        )
        _make_rs(
            tmp_path,
            "methods.rs",
            """\
            use super::User;

            impl User {
                pub fn greet(&self) -> String {
                    format!("Hello {}", self.name)
                }
            }
            """,
        )
        inv = _extract_rust(tmp_path, deep=True)
        # Find the User class (may be in either file's entry).
        user = None
        for entry in inv.values():
            for cls in entry["classes"]:
                if cls["name"] == "User":
                    user = cls
        assert user is not None
        method_names = [m["name"] for m in user["methods"]]
        assert "greet" in method_names

    def test_shallow_impl_methods_as_functions(self, tmp_path):
        """In shallow mode, impl methods appear as functions with a receiver field."""
        _make_rs(
            tmp_path,
            "models.rs",
            """\
            pub struct User {
                pub name: String,
            }

            impl User {
                pub fn greet(&self) -> String {
                    format!("Hello {}", self.name)
                }
            }
            """,
        )
        inv = _extract_rust(tmp_path, deep=False)
        data = list(inv.values())[0]
        greet = [f for f in data["functions"] if f["name"] == "greet"]
        assert len(greet) == 1
        assert greet[0].get("receiver") == "User"

    def test_supertrait_as_bases(self, tmp_path):
        _make_rs(
            tmp_path,
            "traits.rs",
            """\
            pub trait Base {}

            pub trait Child: Base {
                fn do_thing(&self);
            }
            """,
        )
        inv = _extract_rust(tmp_path)
        data = list(inv.values())[0]
        child = [c for c in data["classes"] if c["name"] == "Child"][0]
        assert "Base" in child["bases"]

    def test_async_function(self, tmp_path):
        _make_rs(
            tmp_path,
            "async_mod.rs",
            """\
            pub async fn fetch_data(url: &str) -> String {
                String::new()
            }
            """,
        )
        inv = _extract_rust(tmp_path, deep=True)
        data = list(inv.values())[0]
        fn_info = data["functions"][0]
        assert fn_info["is_async"] is True


# ===========================================================================
# Graceful degradation tests (no Rust needed)
# ===========================================================================


class TestRustExtractorWithoutPreparedHelper:
    def test_missing_helper_returns_empty(self, tmp_path):
        _make_rs(tmp_path, "src/lib.rs", "pub struct App;\n")
        with patch(
            "llm_wiki_cli.extractors.rust_extractor.get_prepared_binary",
            return_value=None,
        ):
            inv = RustExtractor().extract(str(tmp_path))
        assert inv == {}

    def test_missing_helper_stderr_warning(self, tmp_path, capsys):
        _make_rs(tmp_path, "src/lib.rs", "pub struct App;\n")
        with patch(
            "llm_wiki_cli.extractors.rust_extractor.get_prepared_binary",
            return_value=None,
        ):
            RustExtractor().extract(str(tmp_path))
        err = capsys.readouterr().err
        assert "prepare-extractors" in err

    def test_no_rust_files_skips_helper_probe(self, tmp_path):
        with patch(
            "llm_wiki_cli.extractors.rust_extractor.get_prepared_binary"
        ) as mock_prepared:
            inv = RustExtractor().extract(str(tmp_path))
        assert inv == {}
        mock_prepared.assert_not_called()


class TestRustExtractorWrapper:
    def test_extract_remains_short_orchestrator(self):
        source = textwrap.dedent(inspect.getsource(RustExtractor.extract))

        assert len(source.splitlines()) <= 30
        assert _body_line_count(RustExtractor.extract) <= 25

    def test_extract_signature_uses_protocol_arguments(self):
        params = list(inspect.signature(RustExtractor.extract).parameters)

        assert params == ["self", "src_dir", "only_files", "deep"]

    def test_normalization_filters_checkout_helper_but_not_unrelated_suffix(
        self, tmp_path
    ):
        _write_owned_package_sentinels(tmp_path)
        bundled = "src/llm_wiki_cli/extractors/rust_scripts/src/main.rs"
        unrelated = "vendor/llm_wiki_cli/extractors/rust_scripts/src/main.rs"
        _make_rs(tmp_path, bundled, "fn main() {}\n")
        _make_rs(tmp_path, unrelated, "pub fn consumer() {}\n")
        inventory = {
            bundled: {"classes": [], "functions": []},
            unrelated: {"classes": [], "functions": []},
        }

        normalized = RustExtractor()._normalize_inventory(str(tmp_path), inventory)

        assert list(normalized) == [unrelated]

    def test_relative_external_helper_suffix_fails_open_across_both_filter_stages(
        self, tmp_path, monkeypatch
    ):
        external_root = tmp_path / "external-consumer"
        relative_path = "src/llm_wiki_cli/extractors/rust_scripts/src/main.rs"
        _make_rs(external_root, relative_path, "pub fn consumer() {}\n")
        monkeypatch.chdir(Path(__file__).parents[1])
        result = subprocess.CompletedProcess(
            args=["rust-helper"],
            returncode=0,
            stdout=json.dumps(
                {relative_path: {"classes": [], "functions": []}}
            ),
            stderr="",
        )
        extractor = RustExtractor()

        loaded = extractor._load_inventory(result)
        normalized = extractor._normalize_inventory(str(external_root), loaded)

        assert list(loaded) == [relative_path]
        assert list(normalized) == [relative_path]

    def test_request_object_passes_cached_source_files_to_helper(
        self, tmp_path, monkeypatch
    ):
        _make_rs(tmp_path, "src/lib.rs", "pub struct App;\n")
        helper_calls = []
        commands = []

        def fake_get_prepared_binary(language, src_dir, helper_cache_dir):
            helper_calls.append((language, src_dir, helper_cache_dir))
            return Path("/tmp/rust-helper")

        def fake_run(cmd, *args, **kwargs):
            commands.append(cmd)
            return subprocess.CompletedProcess(
                cmd,
                0,
                stdout='{"src/lib.rs":{"classes":[],"functions":[]}}',
                stderr="",
            )

        monkeypatch.setattr(
            "llm_wiki_cli.extractors.rust_extractor.get_prepared_binary",
            fake_get_prepared_binary,
        )
        monkeypatch.setattr(
            "llm_wiki_cli.extractors.rust_extractor.subprocess.run", fake_run
        )

        inv = RustExtractor().extract(
            RustExtractionRequest(
                src_dir=str(tmp_path),
                deep=True,
                source_files=["src/lib.rs"],
                helper_cache_dir="cache-dir",
            )
        )

        assert list(inv) == ["src/lib.rs"]
        assert helper_calls == [("rust", str(tmp_path), "cache-dir")]
        assert commands[0][commands[0].index("--only-files") + 1] == "src/lib.rs"
        assert "--deep" in commands[0]

    def test_windows_style_inventory_keys_are_normalized(self, tmp_path):
        _make_rs(tmp_path, "pkg/client.rs", "pub struct Client;\n")
        result = subprocess.CompletedProcess(
            args=["cargo"],
            returncode=0,
            stdout='{"pkg\\\\client.rs": {"classes": [], "functions": []}}',
            stderr="",
        )
        with patch(
            "llm_wiki_cli.extractors.rust_extractor.get_prepared_binary",
            return_value=Path("/tmp/rust-helper"),
        ):
            with patch(
                "llm_wiki_cli.extractors.rust_extractor.subprocess.run",
                return_value=result,
            ):
                inv = RustExtractor().extract(str(tmp_path))

        assert "pkg/client.rs" in inv
        assert "pkg\\client.rs" not in inv
        assert inv["pkg/client.rs"]["language"] == "rust"

    def test_absolute_inventory_keys_are_relative_to_src_dir(self, tmp_path):
        source = tmp_path / "pkg" / "client.rs"
        _make_rs(tmp_path, "pkg/client.rs", "pub struct Client;\n")
        result = subprocess.CompletedProcess(
            args=["cargo"],
            returncode=0,
            stdout=f'{{"{source.as_posix()}": {{"classes": [], "functions": []}}}}',
            stderr="",
        )
        with patch(
            "llm_wiki_cli.extractors.rust_extractor.get_prepared_binary",
            return_value=Path("/tmp/rust-helper"),
        ):
            with patch(
                "llm_wiki_cli.extractors.rust_extractor.subprocess.run",
                return_value=result,
            ):
                inv = RustExtractor().extract(str(tmp_path))

        assert "pkg/client.rs" in inv
        assert source.as_posix() not in inv

    def test_malformed_json_returns_empty(self, tmp_path, capsys):
        _make_rs(tmp_path, "client.rs", "pub struct Client;\n")
        result = subprocess.CompletedProcess(
            args=["cargo"],
            returncode=0,
            stdout="{not-json",
            stderr="",
        )
        with patch(
            "llm_wiki_cli.extractors.rust_extractor.get_prepared_binary",
            return_value=Path("/tmp/rust-helper"),
        ):
            with patch(
                "llm_wiki_cli.extractors.rust_extractor.subprocess.run",
                return_value=result,
            ):
                inv = RustExtractor().extract(str(tmp_path))

        assert inv == {}
        assert "malformed JSON" in capsys.readouterr().err

    def test_timeout_returns_empty_and_names_configuration(
        self, tmp_path, capsys, monkeypatch
    ):
        _make_rs(tmp_path, "client.rs", "pub struct Client;\n")
        monkeypatch.setenv("LLM_WIKI_EXTRACTOR_TIMEOUT", "39")
        with patch(
            "llm_wiki_cli.extractors.rust_extractor.get_prepared_binary",
            return_value=Path("/tmp/rust-helper"),
        ):
            with patch(
                "llm_wiki_cli.extractors.rust_extractor.subprocess.run",
                side_effect=subprocess.TimeoutExpired(["cargo"], 39),
            ) as mock_run:
                extractor = RustExtractor()
                inv = extractor.extract(str(tmp_path))

        assert inv == {}
        assert mock_run.call_args.kwargs["timeout"] == 39
        assert extractor.last_error is not None
        assert "LLM_WIKI_EXTRACTOR_TIMEOUT" in extractor.last_error
        assert "LLM_WIKI_EXTRACTOR_TIMEOUT" in capsys.readouterr().err

    def test_stderr_forwarded_on_success(self, tmp_path, capsys):
        _make_rs(tmp_path, "client.rs", "pub struct Client;\n")
        result = subprocess.CompletedProcess(
            args=["cargo"],
            returncode=0,
            stdout='{"client.rs": {"classes": [], "functions": []}}',
            stderr="Warning: skipped bad.rs\n",
        )
        with patch(
            "llm_wiki_cli.extractors.rust_extractor.get_prepared_binary",
            return_value=Path("/tmp/rust-helper"),
        ):
            with patch(
                "llm_wiki_cli.extractors.rust_extractor.subprocess.run",
                return_value=result,
            ):
                RustExtractor().extract(str(tmp_path))

        assert "Warning: skipped bad.rs" in capsys.readouterr().err


# ===========================================================================
# Registry integration
# ===========================================================================


class TestRustExtractorRegistryIntegration:
    def test_rust_in_registry(self):
        assert "rust" in EXTRACTOR_REGISTRY

    def test_rust_entry_point_format(self):
        ep = EXTRACTOR_REGISTRY["rust"]
        assert ":" in ep
        module_path, class_name = ep.rsplit(":", 1)
        assert module_path == "llm_wiki_cli.extractors.rust_extractor"
        assert class_name == "RustExtractor"
