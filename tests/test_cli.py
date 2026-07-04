"""Tests for llm_wiki_cli.cli."""

from __future__ import annotations

import ast
import inspect
import textwrap

import pytest

from llm_wiki_cli import cli


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


class TestCliMainStructure:
    def test_main_stays_decomposed(self):
        assert _body_line_count(cli.main) <= 25


@pytest.mark.parametrize(
    "command", ["extract", "bootstrap", "lint", "sync", "ci-check"]
)
def test_inventory_commands_help_lists_include_tests_go(command, monkeypatch, capsys):
    monkeypatch.setattr("sys.argv", ["llm-wiki", command, "--help"])

    with pytest.raises(SystemExit) as exc_info:
        cli.main()

    assert exc_info.value.code == 0
    help_text = capsys.readouterr().out
    assert "--include-tests {go}" in help_text
    assert "Include language-specific test files in extraction" in help_text


@pytest.mark.parametrize(
    ("command", "module_name"),
    [
        ("extract", "extract_cmd"),
        ("bootstrap", "bootstrap_cmd"),
        ("lint", "lint_cmd"),
        ("sync", "sync_cmd"),
        ("ci-check", "ci_check_cmd"),
    ],
)
def test_inventory_commands_parse_include_tests_go(command, module_name, monkeypatch):
    seen = {}
    command_module = getattr(cli, module_name)
    monkeypatch.setattr(
        command_module,
        "run",
        lambda args: seen.setdefault("include_tests", args.include_tests),
    )
    monkeypatch.setattr("sys.argv", ["llm-wiki", command, "--include-tests", "go"])

    cli.main()

    assert seen["include_tests"] == ["go"]


@pytest.mark.parametrize(
    "command", ["extract", "bootstrap", "lint", "sync", "ci-check"]
)
def test_inventory_commands_reject_unsupported_include_tests_language(
    command, monkeypatch
):
    monkeypatch.setattr("sys.argv", ["llm-wiki", command, "--include-tests", "rust"])

    with pytest.raises(SystemExit) as exc_info:
        cli.main()

    assert exc_info.value.code == 2


@pytest.mark.parametrize(
    "command", ["extract", "bootstrap", "lint", "sync", "ci-check"]
)
def test_inventory_commands_help_lists_helper_cache_dir(command, monkeypatch, capsys):
    monkeypatch.setattr("sys.argv", ["llm-wiki", command, "--help"])

    with pytest.raises(SystemExit) as exc_info:
        cli.main()

    assert exc_info.value.code == 0
    help_text = capsys.readouterr().out
    assert "--helper-cache-dir PATH" in help_text
    assert "TypeScript/JavaScript/Go/Rust/Haskell" in help_text
    assert "extractor" in help_text
    assert "helpers" in help_text


def test_prepare_extractors_help_lists_haskell_language(monkeypatch, capsys):
    monkeypatch.setattr("sys.argv", ["llm-wiki", "prepare-extractors", "--help"])

    with pytest.raises(SystemExit) as exc_info:
        cli.main()

    assert exc_info.value.code == 0
    help_text = capsys.readouterr().out
    assert "--language {typescript,go,rust,haskell}" in help_text
    assert "Helper language to prepare" in help_text


def test_prepare_extractors_help_lists_allow_external_src(monkeypatch, capsys):
    monkeypatch.setattr("sys.argv", ["llm-wiki", "prepare-extractors", "--help"])

    with pytest.raises(SystemExit) as exc_info:
        cli.main()

    assert exc_info.value.code == 0
    help_text = capsys.readouterr().out
    assert "--allow-external-src" in help_text
    assert "outside the current working" in help_text
    assert "directory" in help_text


def test_prepare_extractors_parses_allow_external_src(monkeypatch):
    seen = {}
    monkeypatch.setattr(
        cli.prepare_extractors_cmd,
        "run",
        lambda args: seen.setdefault("allow_external_src", args.allow_external_src),
    )
    monkeypatch.setattr(
        "sys.argv", ["llm-wiki", "prepare-extractors", "--allow-external-src"]
    )

    cli.main()

    assert seen["allow_external_src"] is True
