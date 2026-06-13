"""Tests for llm_wiki_cli.cli."""

from __future__ import annotations

import ast
import inspect
import textwrap

from llm_wiki_cli import cli


def _body_line_count(function) -> int:
    source = textwrap.dedent(inspect.getsource(function))
    function_node = ast.parse(source).body[0]
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
    last_body_line = max(stmt.end_lineno for stmt in body)
    return last_body_line - first_body_line + 1


class TestCliMainStructure:
    def test_main_stays_decomposed(self):
        assert _body_line_count(cli.main) <= 25
