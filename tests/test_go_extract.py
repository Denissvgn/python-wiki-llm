"""Tests for the Go extractor (go_extractor.py + go_scripts/main.go)."""

from __future__ import annotations

import ast
import inspect
import shutil
import subprocess
import textwrap
from pathlib import Path
from unittest.mock import patch

import pytest

from llm_wiki_cli.config import EXTRACTOR_REGISTRY
from llm_wiki_cli.extractors.go_extractor import GoExtractor
from llm_wiki_cli.services.extractor_helpers import get_prepared_binary

# ---------------------------------------------------------------------------
# Skip all tests when Go is not available on this machine.
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


GO_AVAILABLE = get_prepared_binary("go", ".") is not None
skip_no_go = pytest.mark.skipif(
    not GO_AVAILABLE,
    reason="Prepared Go helper not available — Go extractor integration tests skipped",
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_go(tmp_path: Path, filename: str, content: str) -> Path:
    """Write a Go source file under *tmp_path* and return its path."""
    p = tmp_path / filename
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(textwrap.dedent(content), encoding="utf-8")
    return p


def _body_line_count(function) -> int:
    source = textwrap.dedent(inspect.getsource(function))
    function_node = ast.parse(source).body[0]
    body = list(function_node.body)
    if (
        body
        and isinstance(body[0], ast.Expr)
        and isinstance(body[0].value, ast.Constant)
        and isinstance(body[0].value.value, str)
    ):
        body = body[1:]

    first_body_line = min(stmt.lineno for stmt in body)
    last_body_line = max(stmt.end_lineno for stmt in body)
    return last_body_line - first_body_line + 1


class TestGoWrapperFiltering:
    def test_full_scan_passes_gitignore_filtered_files_to_subprocess(
        self, tmp_path, monkeypatch
    ):
        _make_go(tmp_path, "real.go", "package main\n\ntype Real struct{}\n")
        _make_go(tmp_path, "ignored.go", "package main\n\ntype Ignored struct{}\n")
        (tmp_path / ".gitignore").write_text("ignored.go\n", encoding="utf-8")
        commands = []

        def fake_run(cmd, *args, **kwargs):
            commands.append(cmd)
            return subprocess.CompletedProcess(
                cmd,
                0,
                stdout='{"real.go":{"classes":[],"functions":[]}}',
                stderr="",
            )

        monkeypatch.setattr(
            "llm_wiki_cli.extractors.go_extractor.get_prepared_binary",
            lambda *a, **k: Path("/tmp/go-helper"),
        )
        monkeypatch.setattr(
            "llm_wiki_cli.extractors.go_extractor.subprocess.run", fake_run
        )

        GoExtractor().extract(str(tmp_path))

        cmd = commands[0]
        only_idx = cmd.index("--only-files") + 1
        assert cmd[only_idx] == "real.go"


# ===========================================================================
# Unit-level tests (require Go)
# ===========================================================================


@skip_no_go
class TestGoExtractor:
    def test_empty_dir(self, tmp_path):
        inv = GoExtractor().extract(str(tmp_path))
        assert inv == {}

    def test_single_struct(self, tmp_path):
        _make_go(
            tmp_path,
            "models.go",
            """\
            package models

            type User struct {
                Name string
                Age  int
            }
            """,
        )
        inv = GoExtractor().extract(str(tmp_path))
        assert len(inv) == 1
        data = list(inv.values())[0]
        assert len(data["classes"]) == 1
        assert data["classes"][0]["name"] == "User"
        assert data["classes"][0]["kind"] == "struct"

    def test_language_field_stamped(self, tmp_path):
        _make_go(tmp_path, "a.go", "package a\n\ntype A struct{}\n")
        inv = GoExtractor().extract(str(tmp_path))
        for entry in inv.values():
            assert entry["language"] == "go"

    def test_struct_with_embedded_type(self, tmp_path):
        _make_go(
            tmp_path,
            "models.go",
            """\
            package models

            type Base struct{}

            type Child struct {
                Base
                Name string
            }
            """,
        )
        inv = GoExtractor().extract(str(tmp_path))
        data = list(inv.values())[0]
        child = [c for c in data["classes"] if c["name"] == "Child"][0]
        assert "Base" in child["bases"]

    def test_interface_extraction(self, tmp_path):
        _make_go(
            tmp_path,
            "iface.go",
            """\
            package iface

            type Reader interface {
                Read(p []byte) (n int, err error)
            }
            """,
        )
        inv = GoExtractor().extract(str(tmp_path))
        data = list(inv.values())[0]
        assert len(data["classes"]) == 1
        assert data["classes"][0]["name"] == "Reader"
        assert data["classes"][0]["kind"] == "interface"

    def test_interface_with_embedded(self, tmp_path):
        _make_go(
            tmp_path,
            "iface.go",
            """\
            package iface

            type Reader interface {
                Read(p []byte) (int, error)
            }

            type ReadWriter interface {
                Reader
                Write(p []byte) (int, error)
            }
            """,
        )
        inv = GoExtractor().extract(str(tmp_path))
        data = list(inv.values())[0]
        rw = [c for c in data["classes"] if c["name"] == "ReadWriter"][0]
        assert "Reader" in rw["bases"]

    def test_exported_function(self, tmp_path):
        _make_go(
            tmp_path,
            "utils.go",
            """\
            package utils

            func Greet(name string) string {
                return "Hello " + name
            }
            """,
        )
        inv = GoExtractor().extract(str(tmp_path))
        data = list(inv.values())[0]
        assert len(data["functions"]) == 1
        assert data["functions"][0]["name"] == "Greet"

    def test_unexported_skipped(self, tmp_path):
        _make_go(
            tmp_path,
            "utils.go",
            """\
            package utils

            func helperPrivate() {}

            func PublicFunc() {}
            """,
        )
        inv = GoExtractor().extract(str(tmp_path))
        data = list(inv.values())[0]
        names = [f["name"] for f in data["functions"]]
        assert "PublicFunc" in names
        assert "helperPrivate" not in names

    def test_test_files_excluded(self, tmp_path):
        _make_go(tmp_path, "main.go", "package main\n\nfunc Main() {}\n")
        _make_go(tmp_path, "main_test.go", "package main\n\nfunc TestMain() {}\n")
        inv = GoExtractor().extract(str(tmp_path))
        assert len(inv) == 1
        assert "main_test.go" not in list(inv.keys())[0]

    def test_type_alias(self, tmp_path):
        _make_go(
            tmp_path,
            "types.go",
            """\
            package types

            type StringSlice = []string
            """,
        )
        inv = GoExtractor().extract(str(tmp_path))
        data = list(inv.values())[0]
        assert any(
            c["name"] == "StringSlice" and c["kind"] == "type_alias"
            for c in data["classes"]
        )

    def test_only_files(self, tmp_path):
        _make_go(tmp_path, "a.go", "package a\n\ntype A struct{}\n")
        _make_go(tmp_path, "b.go", "package a\n\ntype B struct{}\n")
        inv = GoExtractor().extract(str(tmp_path), only_files=["a.go"])
        assert len(inv) == 1
        assert any("a.go" in k for k in inv)

    def test_only_files_respects_excluded_dirs(self, tmp_path):
        _make_go(tmp_path, "vendor/dep/dep.go", "package dep\n\ntype Dep struct{}\n")
        inv = GoExtractor().extract(str(tmp_path), only_files=["vendor/dep/dep.go"])
        assert inv == {}

    def test_vendor_excluded(self, tmp_path):
        _make_go(tmp_path, "main.go", "package main\n\ntype App struct{}\n")
        _make_go(tmp_path, "vendor/dep/dep.go", "package dep\n\ntype Dep struct{}\n")
        inv = GoExtractor().extract(str(tmp_path))
        assert len(inv) == 1
        assert not any("vendor" in k for k in inv)

    # ── Deep mode tests ───────────────────────────────────────────────────

    def test_deep_struct_docstring(self, tmp_path):
        _make_go(
            tmp_path,
            "models.go",
            """\
            package models

            // User represents a registered user in the system.
            type User struct {
                Name string
            }
            """,
        )
        inv = GoExtractor().extract(str(tmp_path), deep=True)
        data = list(inv.values())[0]
        user = data["classes"][0]
        assert "registered user" in user["docstring"]

    def test_deep_struct_attributes(self, tmp_path):
        _make_go(
            tmp_path,
            "models.go",
            """\
            package models

            type User struct {
                Name  string `json:"name"`
                Email string `json:"email"`
            }
            """,
        )
        inv = GoExtractor().extract(str(tmp_path), deep=True)
        data = list(inv.values())[0]
        attrs = data["classes"][0]["attributes"]
        names = [a["name"] for a in attrs]
        assert "Name" in names
        assert "Email" in names

    def test_deep_receiver_methods(self, tmp_path):
        _make_go(
            tmp_path,
            "models.go",
            """\
            package models

            type User struct {
                Name string
            }

            // Greet returns a greeting for the user.
            func (u *User) Greet() string {
                return "Hello " + u.Name
            }
            """,
        )
        inv = GoExtractor().extract(str(tmp_path), deep=True)
        data = list(inv.values())[0]
        user = [c for c in data["classes"] if c["name"] == "User"][0]
        assert len(user["methods"]) == 1
        assert user["methods"][0]["name"] == "Greet"

    def test_deep_function_params(self, tmp_path):
        _make_go(
            tmp_path,
            "utils.go",
            """\
            package utils

            // Add returns the sum of a and b.
            func Add(a int, b int) int {
                return a + b
            }
            """,
        )
        inv = GoExtractor().extract(str(tmp_path), deep=True)
        data = list(inv.values())[0]
        fn = data["functions"][0]
        assert fn["name"] == "Add"
        assert fn["docstring"] == "Add returns the sum of a and b."
        param_names = [p["name"] for p in fn["params"]]
        assert "a" in param_names
        assert "b" in param_names
        assert fn["return_type"] == "int"

    def test_deep_interface_methods(self, tmp_path):
        _make_go(
            tmp_path,
            "iface.go",
            """\
            package iface

            // Writer is the interface for writing bytes.
            type Writer interface {
                Write(p []byte) (n int, err error)
            }
            """,
        )
        inv = GoExtractor().extract(str(tmp_path), deep=True)
        data = list(inv.values())[0]
        writer = data["classes"][0]
        assert writer["docstring"] == "Writer is the interface for writing bytes."
        assert len(writer["methods"]) == 1
        assert writer["methods"][0]["name"] == "Write"

    def test_deep_imports(self, tmp_path):
        _make_go(
            tmp_path,
            "main.go",
            """\
            package main

            import (
                "fmt"
                "encoding/json"
            )

            func Main() {
                fmt.Println(json.Marshal)
            }
            """,
        )
        inv = GoExtractor().extract(str(tmp_path), deep=True)
        data = list(inv.values())[0]
        assert "imports" in data
        modules = [i["module"] for i in data["imports"]]
        assert "fmt" in modules
        assert "encoding/json" in modules

    def test_deep_import_alias(self, tmp_path):
        _make_go(
            tmp_path,
            "main.go",
            """\
            package main

            import (
                j "encoding/json"
            )

            func Main() {
                _ = j.Marshal
            }
            """,
        )
        inv = GoExtractor().extract(str(tmp_path), deep=True)
        data = list(inv.values())[0]
        json_imp = [i for i in data["imports"] if i["module"] == "encoding/json"][0]
        assert json_imp["alias"] == "j"

    def test_shallow_receiver_methods_as_functions(self, tmp_path):
        """In shallow mode, receiver methods appear as functions with a receiver field."""
        _make_go(
            tmp_path,
            "models.go",
            """\
            package models

            type User struct {
                Name string
            }

            func (u *User) Greet() string {
                return "Hello " + u.Name
            }
            """,
        )
        inv = GoExtractor().extract(str(tmp_path), deep=False)
        data = list(inv.values())[0]
        greet = [f for f in data["functions"] if f["name"] == "Greet"]
        assert len(greet) == 1
        assert greet[0].get("receiver") == "User"

    def test_syntax_error_graceful(self, tmp_path):
        """Files with syntax errors are skipped with a warning, not a crash."""
        _make_go(tmp_path, "good.go", "package good\n\ntype Good struct{}\n")
        _make_go(
            tmp_path, "bad.go", "package bad\n\ntype Bad struct {\n"
        )  # missing closing brace
        inv = GoExtractor().extract(str(tmp_path))
        # Should still get the good file
        assert any("good.go" in k for k in inv)

    def test_multiple_files(self, tmp_path):
        _make_go(tmp_path, "a.go", "package a\n\ntype Alpha struct{}\n")
        _make_go(tmp_path, "sub/b.go", "package sub\n\ntype Beta struct{}\n")
        inv = GoExtractor().extract(str(tmp_path))
        assert len(inv) == 2

    # ── Kind label tests ──────────────────────────────────────────────────

    def test_named_type(self, tmp_path):
        """type Role string should be kind 'named_type', not 'type_alias'."""
        _make_go(
            tmp_path,
            "types.go",
            """\
            package types

            type Role string
            """,
        )
        inv = GoExtractor().extract(str(tmp_path))
        data = list(inv.values())[0]
        assert any(
            c["name"] == "Role" and c["kind"] == "named_type" for c in data["classes"]
        )

    def test_true_type_alias(self, tmp_path):
        """type StringSlice = []string should remain kind 'type_alias'."""
        _make_go(
            tmp_path,
            "types.go",
            """\
            package types

            type StringSlice = []string
            """,
        )
        inv = GoExtractor().extract(str(tmp_path))
        data = list(inv.values())[0]
        assert any(
            c["name"] == "StringSlice" and c["kind"] == "type_alias"
            for c in data["classes"]
        )

    def test_named_type_method_attachment(self, tmp_path):
        """A method on an exported named type attaches to it in deep mode."""
        _make_go(
            tmp_path,
            "types.go",
            """\
            package types

            type Role string

            func (r Role) IsAdmin() bool {
                return r == "admin"
            }
            """,
        )
        inv = GoExtractor().extract(str(tmp_path), deep=True)
        data = list(inv.values())[0]
        role = [c for c in data["classes"] if c["name"] == "Role"][0]
        assert len(role["methods"]) == 1
        assert role["methods"][0]["name"] == "IsAdmin"

    # ── Cross-file receiver tests ─────────────────────────────────────────

    def test_deep_cross_file_method(self, tmp_path):
        """In deep mode, a method defined in a separate file attaches to its struct."""
        _make_go(
            tmp_path,
            "models.go",
            """\
            package models

            type User struct {
                Name string
            }
            """,
        )
        _make_go(
            tmp_path,
            "methods.go",
            """\
            package models

            func (u *User) Greet() string {
                return "Hello " + u.Name
            }
            """,
        )
        inv = GoExtractor().extract(str(tmp_path), deep=True)
        # Find the User class (may be in either file's entry)
        user = None
        for entry in inv.values():
            for cls in entry["classes"]:
                if cls["name"] == "User":
                    user = cls
        assert user is not None
        method_names = [m["name"] for m in user["methods"]]
        assert "Greet" in method_names
        # Greet must NOT appear as a standalone function
        all_fns = [fn["name"] for entry in inv.values() for fn in entry["functions"]]
        assert "Greet" not in all_fns

    def test_shallow_cross_file_stays_function(self, tmp_path):
        """In shallow mode, cross-file methods stay as functions with a receiver field."""
        _make_go(
            tmp_path,
            "models.go",
            """\
            package models

            type User struct {
                Name string
            }
            """,
        )
        _make_go(
            tmp_path,
            "methods.go",
            """\
            package models

            func (u *User) Greet() string {
                return "Hello " + u.Name
            }
            """,
        )
        inv = GoExtractor().extract(str(tmp_path), deep=False)
        all_fns = [fn for entry in inv.values() for fn in entry["functions"]]
        greet = [f for f in all_fns if f["name"] == "Greet"]
        assert len(greet) == 1
        assert greet[0].get("receiver") == "User"

    def test_unexported_type_exported_method(self, tmp_path):
        """Unexported type must not appear in classes; its exported method stays in functions."""
        _make_go(
            tmp_path,
            "internal.go",
            """\
            package internal

            type myHelper struct{}

            func (h *myHelper) DoWork() {}
            """,
        )
        inv = GoExtractor().extract(str(tmp_path), deep=True)
        data = list(inv.values())[0]
        class_names = [c["name"] for c in data["classes"]]
        assert "myHelper" not in class_names
        fn_names = [f["name"] for f in data["functions"]]
        assert "DoWork" in fn_names
        do_work = [f for f in data["functions"] if f["name"] == "DoWork"][0]
        assert do_work.get("receiver") == "myHelper"


# ===========================================================================
# Graceful degradation tests (no Go needed)
# ===========================================================================


class TestGoExtractorWithoutPreparedHelper:
    def test_missing_helper_returns_empty(self, tmp_path):
        _make_go(tmp_path, "main.go", "package main\n\ntype App struct{}\n")
        with patch(
            "llm_wiki_cli.extractors.go_extractor.get_prepared_binary",
            return_value=None,
        ):
            inv = GoExtractor().extract(str(tmp_path))
        assert inv == {}

    def test_missing_helper_stderr_warning(self, tmp_path, capsys):
        _make_go(tmp_path, "main.go", "package main\n\ntype App struct{}\n")
        with patch(
            "llm_wiki_cli.extractors.go_extractor.get_prepared_binary",
            return_value=None,
        ):
            GoExtractor().extract(str(tmp_path))
        err = capsys.readouterr().err
        assert "prepare-extractors" in err

    def test_no_go_files_skips_helper_probe(self, tmp_path):
        with patch(
            "llm_wiki_cli.extractors.go_extractor.get_prepared_binary"
        ) as mock_prepared:
            inv = GoExtractor().extract(str(tmp_path))
        assert inv == {}
        mock_prepared.assert_not_called()


class TestGoExtractorWrapper:
    def test_extract_remains_short_orchestrator(self):
        source = textwrap.dedent(inspect.getsource(GoExtractor.extract))

        assert len(source.splitlines()) <= 30
        assert _body_line_count(GoExtractor.extract) <= 25

    def test_extract_signature_stays_protocol_sized(self):
        signature = inspect.signature(GoExtractor.extract)
        public_parameters = [
            param.name
            for param in signature.parameters.values()
            if param.name != "self"
        ]

        assert public_parameters == ["src_dir", "only_files", "deep"]

    def test_windows_style_inventory_keys_are_normalized(self, tmp_path):
        _make_go(tmp_path, "pkg/client.go", "package pkg\n\ntype Client struct{}\n")
        result = subprocess.CompletedProcess(
            args=["go"],
            returncode=0,
            stdout='{"pkg\\\\client.go": {"classes": [], "functions": []}}',
            stderr="",
        )
        with patch(
            "llm_wiki_cli.extractors.go_extractor.get_prepared_binary",
            return_value=Path("/tmp/go-helper"),
        ):
            with patch(
                "llm_wiki_cli.extractors.go_extractor.subprocess.run",
                return_value=result,
            ):
                inv = GoExtractor().extract(str(tmp_path))

        assert "pkg/client.go" in inv
        assert "pkg\\client.go" not in inv
        assert inv["pkg/client.go"]["language"] == "go"

    def test_absolute_inventory_keys_are_relative_to_src_dir(self, tmp_path):
        source = tmp_path / "pkg" / "client.go"
        _make_go(tmp_path, "pkg/client.go", "package pkg\n\ntype Client struct{}\n")
        result = subprocess.CompletedProcess(
            args=["go"],
            returncode=0,
            stdout=f'{{"{source.as_posix()}": {{"classes": [], "functions": []}}}}',
            stderr="",
        )
        with patch(
            "llm_wiki_cli.extractors.go_extractor.get_prepared_binary",
            return_value=Path("/tmp/go-helper"),
        ):
            with patch(
                "llm_wiki_cli.extractors.go_extractor.subprocess.run",
                return_value=result,
            ):
                inv = GoExtractor().extract(str(tmp_path))

        assert "pkg/client.go" in inv
        assert source.as_posix() not in inv

    def test_malformed_json_returns_empty(self, tmp_path, capsys):
        _make_go(tmp_path, "client.go", "package main\n\ntype Client struct{}\n")
        result = subprocess.CompletedProcess(
            args=["go"],
            returncode=0,
            stdout="{not-json",
            stderr="",
        )
        with patch(
            "llm_wiki_cli.extractors.go_extractor.get_prepared_binary",
            return_value=Path("/tmp/go-helper"),
        ):
            with patch(
                "llm_wiki_cli.extractors.go_extractor.subprocess.run",
                return_value=result,
            ):
                inv = GoExtractor().extract(str(tmp_path))

        assert inv == {}
        assert "malformed JSON" in capsys.readouterr().err

    def test_timeout_returns_empty(self, tmp_path, capsys):
        _make_go(tmp_path, "client.go", "package main\n\ntype Client struct{}\n")
        with patch(
            "llm_wiki_cli.extractors.go_extractor.get_prepared_binary",
            return_value=Path("/tmp/go-helper"),
        ):
            with patch(
                "llm_wiki_cli.extractors.go_extractor.subprocess.run",
                side_effect=subprocess.TimeoutExpired(["go"], 120),
            ):
                inv = GoExtractor().extract(str(tmp_path))

        assert inv == {}
        assert "timed out" in capsys.readouterr().err

    def test_stderr_forwarded_on_success(self, tmp_path, capsys):
        _make_go(tmp_path, "client.go", "package main\n\ntype Client struct{}\n")
        result = subprocess.CompletedProcess(
            args=["go"],
            returncode=0,
            stdout='{"client.go": {"classes": [], "functions": []}}',
            stderr="Warning: skipped bad.go\n",
        )
        with patch(
            "llm_wiki_cli.extractors.go_extractor.get_prepared_binary",
            return_value=Path("/tmp/go-helper"),
        ):
            with patch(
                "llm_wiki_cli.extractors.go_extractor.subprocess.run",
                return_value=result,
            ):
                GoExtractor().extract(str(tmp_path))

        assert "Warning: skipped bad.go" in capsys.readouterr().err


# ===========================================================================
# Registry integration
# ===========================================================================


class TestGoExtractorRegistryIntegration:
    def test_go_in_registry(self):
        assert "go" in EXTRACTOR_REGISTRY

    def test_go_entry_point_format(self):
        ep = EXTRACTOR_REGISTRY["go"]
        assert ":" in ep
        module_path, class_name = ep.rsplit(":", 1)
        assert module_path == "llm_wiki_cli.extractors.go_extractor"
        assert class_name == "GoExtractor"
