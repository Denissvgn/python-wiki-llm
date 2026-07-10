"""Syntax-only FastAPI declaration extraction.

This module deliberately depends only on :mod:`ast`.  It never imports FastAPI,
Pydantic, or the target application.  The raw declarations it emits are later
resolved into application-level HTTP contracts by
``llm_wiki_cli.services.api_contracts``.

The public integration seam is :func:`extract_fastapi_declarations`.  Python
inventory producers may store a non-empty result at
``file_entry["frameworks"]["fastapi"]``.
"""

from __future__ import annotations

import ast
from collections.abc import Mapping
from typing import Any


_MODULE_SCOPE = "<module>"
_HTTP_METHOD_DECORATORS = {
    "delete",
    "get",
    "head",
    "options",
    "patch",
    "post",
    "put",
    "trace",
}
_ROUTE_DECORATORS = _HTTP_METHOD_DECORATORS | {"api_route", "route"}
_PARAMETER_MARKERS = {
    "Body",
    "Cookie",
    "Depends",
    "File",
    "Form",
    "Header",
    "Path",
    "Query",
    "Security",
}


def _simple_ref(node: ast.AST | None) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        parent = _simple_ref(node.value)
        if parent:
            return f"{parent}.{node.attr}"
    return ""


def _display_expr(node: ast.AST | None) -> str:
    """Return bounded, readable syntax without falling back to ``ast.dump``."""
    if node is None:
        return ""
    try:
        return ast.unparse(node)
    except (AttributeError, ValueError):  # pragma: no cover - Python 3.9 has unparse
        return _simple_ref(node) or "..."


def _import_aliases(tree: ast.AST) -> dict[str, str]:
    aliases: dict[str, str] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                binding = alias.asname or alias.name.split(".", 1)[0]
                aliases[binding] = alias.name
        elif isinstance(node, ast.ImportFrom):
            module = "." * node.level + (node.module or "")
            for alias in node.names:
                if alias.name == "*":
                    continue
                binding = alias.asname or alias.name
                aliases[binding] = f"{module}.{alias.name}".strip(".")
    return aliases


def _canonical_ref(node: ast.AST | None, aliases: Mapping[str, str]) -> str:
    ref = _simple_ref(node)
    if not ref:
        return ""
    root, dot, rest = ref.partition(".")
    target = aliases.get(root)
    if not target:
        return ref
    return f"{target}.{rest}" if dot else target


def _scope_parents(scope: str) -> list[str]:
    if scope == _MODULE_SCOPE:
        return [_MODULE_SCOPE]
    parts = scope.split(".")
    return [".".join(parts[:index]) for index in range(len(parts), 0, -1)] + [
        _MODULE_SCOPE
    ]


def _literal_record(value: Any) -> dict[str, Any]:
    return {"kind": "literal", "value": value}


def _unknown_record() -> dict[str, str]:
    return {"kind": "unknown"}


def _reference_record(value: str) -> dict[str, str]:
    return {"kind": "reference", "value": value}


def _expression_record(
    node: ast.AST | None,
    constants: Mapping[tuple[str, str], dict[str, Any]],
    scope: str,
) -> dict[str, Any]:
    if node is None:
        return _unknown_record()
    if isinstance(node, ast.Constant):
        if node.value is Ellipsis:
            return {"kind": "ellipsis"}
        if isinstance(node.value, (str, int, float, bool, type(None))):
            return _literal_record(node.value)
        return _unknown_record()
    if isinstance(node, ast.Name):
        for candidate_scope in _scope_parents(scope):
            value = constants.get((candidate_scope, node.id))
            if value is not None:
                return dict(value)
        return _reference_record(node.id)
    if isinstance(node, ast.Attribute):
        ref = _simple_ref(node)
        return _reference_record(ref) if ref else _unknown_record()
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.USub, ast.UAdd)):
        operand = _expression_record(node.operand, constants, scope)
        value = operand.get("value") if operand.get("kind") == "literal" else None
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            return _literal_record(-value if isinstance(node.op, ast.USub) else value)
        return _unknown_record()
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
        left = _expression_record(node.left, constants, scope)
        right = _expression_record(node.right, constants, scope)
        if left.get("kind") == right.get("kind") == "literal":
            left_value = left.get("value")
            right_value = right.get("value")
            if isinstance(left_value, str) and isinstance(right_value, str):
                return _literal_record(left_value + right_value)
        return _unknown_record()
    if isinstance(node, (ast.List, ast.Tuple, ast.Set)):
        records = [_expression_record(item, constants, scope) for item in node.elts]
        if all(record.get("kind") == "literal" for record in records):
            return _literal_record([record.get("value") for record in records])
        return {"kind": "sequence", "items": records}
    if isinstance(node, ast.Dict):
        items: list[dict[str, Any]] = []
        for key, value in zip(node.keys, node.values):
            if key is None:
                return _unknown_record()
            items.append(
                {
                    "key": _expression_record(key, constants, scope),
                    "value": _expression_record(value, constants, scope),
                }
            )
        return {"kind": "mapping", "items": items}
    if isinstance(node, ast.Call):
        return {
            "kind": "call",
            "call": _simple_ref(node.func) or "unknown",
            "args": [
                _expression_record(arg, constants, scope) for arg in node.args
            ],
            "kwargs": {
                keyword.arg if keyword.arg is not None else "**": _expression_record(
                    keyword.value, constants, scope
                )
                for keyword in node.keywords
            },
        }
    if isinstance(node, (ast.Subscript, ast.BinOp)):
        text = _display_expr(node)
        return {"kind": "expression", "value": text} if text else _unknown_record()
    return _unknown_record()


def _call_payload(
    node: ast.Call,
    constants: Mapping[tuple[str, str], dict[str, Any]],
    scope: str,
) -> dict[str, Any]:
    return {
        "call": _simple_ref(node.func) or "unknown",
        "args": [_expression_record(arg, constants, scope) for arg in node.args],
        "kwargs": {
            keyword.arg if keyword.arg is not None else "**": _expression_record(
                keyword.value, constants, scope
            )
            for keyword in node.keywords
        },
    }


def _annotation_parts(node: ast.AST | None) -> tuple[str, list[ast.expr]]:
    if not isinstance(node, ast.Subscript):
        return _display_expr(node), []
    if _simple_ref(node.value).rsplit(".", 1)[-1] != "Annotated":
        return _display_expr(node), []
    elements = list(node.slice.elts) if isinstance(node.slice, ast.Tuple) else [node.slice]
    if not elements:
        return _display_expr(node), []
    return _display_expr(elements[0]), elements[1:]


def _marker_payload(
    node: ast.AST | None,
    aliases: Mapping[str, str],
    constants: Mapping[tuple[str, str], dict[str, Any]],
    scope: str,
) -> dict[str, Any] | None:
    if not isinstance(node, ast.Call):
        return None
    canonical = _canonical_ref(node.func, aliases)
    leaf = canonical.rsplit(".", 1)[-1]
    if leaf not in _PARAMETER_MARKERS:
        return None
    if not canonical.startswith("fastapi."):
        return None
    payload = _call_payload(node, constants, scope)
    payload["marker"] = leaf.lower()
    payload["canonical_call"] = canonical
    return payload


def _parameter_payloads(
    node: ast.FunctionDef | ast.AsyncFunctionDef,
    aliases: Mapping[str, str],
    constants: Mapping[tuple[str, str], dict[str, Any]],
    scope: str,
) -> list[dict[str, Any]]:
    arguments = node.args
    positional = list(arguments.posonlyargs) + list(arguments.args)
    positional_defaults: list[ast.expr | None] = [None] * (
        len(positional) - len(arguments.defaults)
    ) + list(arguments.defaults)
    entries: list[tuple[ast.arg, str, ast.AST | None]] = []
    posonly_count = len(arguments.posonlyargs)
    for index, (argument, default) in enumerate(
        zip(positional, positional_defaults)
    ):
        kind = "positional_only" if index < posonly_count else "positional_or_keyword"
        entries.append((argument, kind, default))
    if arguments.vararg is not None:
        entries.append((arguments.vararg, "var_positional", None))
    entries.extend(
        (argument, "keyword_only", default)
        for argument, default in zip(arguments.kwonlyargs, arguments.kw_defaults)
    )
    if arguments.kwarg is not None:
        entries.append((arguments.kwarg, "var_keyword", None))

    payloads: list[dict[str, Any]] = []
    for argument, kind, default in entries:
        annotation, metadata = _annotation_parts(argument.annotation)
        marker = _marker_payload(default, aliases, constants, scope)
        if marker is not None:
            marker["source"] = "default"
        if marker is None:
            for item in metadata:
                marker = _marker_payload(item, aliases, constants, scope)
                if marker is not None:
                    marker["source"] = "annotated"
                    break
        payload: dict[str, Any] = {
            "name": argument.arg,
            "kind": kind,
            "annotation": annotation,
        }
        if default is not None:
            payload["default"] = _expression_record(default, constants, scope)
        if marker is not None:
            payload["marker"] = marker
        payloads.append(payload)
    return payloads


class _FastAPIScanner(ast.NodeVisitor):
    def __init__(self, tree: ast.Module, filepath: str):
        self.filepath = filepath
        self.aliases = _import_aliases(tree)
        self.scope_stack = [_MODULE_SCOPE]
        self.conditional_depth = 0
        self.constants: dict[tuple[str, str], dict[str, Any]] = {}
        self.applications: list[dict[str, Any]] = []
        self.routers: list[dict[str, Any]] = []
        self.binding_aliases: list[dict[str, Any]] = []
        self.includes: list[dict[str, Any]] = []
        self.operations: list[dict[str, Any]] = []

    @property
    def scope(self) -> str:
        return self.scope_stack[-1]

    def _qualname(self, name: str) -> str:
        return name if self.scope == _MODULE_SCOPE else f"{self.scope}.{name}"

    def _record_binding(self, target: ast.AST, value: ast.AST, line: int) -> None:
        if not isinstance(target, ast.Name):
            return
        if not isinstance(value, ast.Call):
            expression = _expression_record(
                value, self.constants, self.scope
            )
            self.constants[(self.scope, target.id)] = expression
            if expression.get("kind") == "reference":
                self.binding_aliases.append(
                    {
                        "binding": target.id,
                        "target": expression.get("value"),
                        "scope": self.scope,
                        "line": line,
                    }
                )
            return
        canonical = _canonical_ref(value.func, self.aliases)
        leaf = canonical.rsplit(".", 1)[-1]
        if leaf not in {"FastAPI", "APIRouter"}:
            return
        if not canonical.startswith("fastapi."):
            return
        record = {
            "binding": target.id,
            "scope": self.scope,
            "line": line,
            "conditional": self.conditional_depth > 0,
            **_call_payload(value, self.constants, self.scope),
        }
        record["canonical_call"] = canonical
        destination = self.applications if leaf == "FastAPI" else self.routers
        destination.append(record)

    def visit_Assign(self, node: ast.Assign) -> None:
        for target in node.targets:
            self._record_binding(target, node.value, node.lineno)
        self.generic_visit(node.value)

    def visit_AnnAssign(self, node: ast.AnnAssign) -> None:
        if node.value is not None:
            self._record_binding(node.target, node.value, node.lineno)
            self.generic_visit(node.value)

    def visit_Expr(self, node: ast.Expr) -> None:
        value = node.value
        if isinstance(value, ast.Call) and isinstance(value.func, ast.Attribute):
            if value.func.attr == "include_router":
                payload = _call_payload(value, self.constants, self.scope)
                payload.update(
                    {
                        "owner": _simple_ref(value.func.value),
                        "scope": self.scope,
                        "line": node.lineno,
                        "conditional": self.conditional_depth > 0,
                    }
                )
                self.includes.append(payload)
        self.generic_visit(node)

    def _visit_function(
        self, node: ast.FunctionDef | ast.AsyncFunctionDef
    ) -> None:
        handler_scope = self.scope
        qualname = self._qualname(node.name)
        for decorator in node.decorator_list:
            if not isinstance(decorator, ast.Call) or not isinstance(
                decorator.func, ast.Attribute
            ):
                continue
            leaf = decorator.func.attr
            if leaf not in _ROUTE_DECORATORS:
                continue
            owner = _simple_ref(decorator.func.value)
            if not owner:
                continue
            payload = _call_payload(decorator, self.constants, handler_scope)
            payload.update(
                {
                    "owner": owner,
                    "decorator": leaf,
                    "handler": node.name,
                    "handler_qualname": qualname,
                    "handler_scope": handler_scope,
                    "line": node.lineno,
                    "decorator_line": decorator.lineno,
                    "conditional": self.conditional_depth > 0,
                    "is_async": isinstance(node, ast.AsyncFunctionDef),
                    "parameters": _parameter_payloads(
                        node,
                        self.aliases,
                        self.constants,
                        handler_scope,
                    ),
                    "return_annotation": _display_expr(node.returns),
                }
            )
            self.operations.append(payload)

        self.scope_stack.append(qualname)
        try:
            for statement in node.body:
                self.visit(statement)
        finally:
            self.scope_stack.pop()

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self._visit_function(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self._visit_function(node)

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        qualname = self._qualname(node.name)
        self.scope_stack.append(qualname)
        try:
            for statement in node.body:
                self.visit(statement)
        finally:
            self.scope_stack.pop()

    def _visit_conditional(self, node: ast.AST) -> None:
        self.conditional_depth += 1
        try:
            self.generic_visit(node)
        finally:
            self.conditional_depth -= 1

    visit_For = _visit_conditional
    visit_AsyncFor = _visit_conditional
    visit_If = _visit_conditional
    visit_Match = _visit_conditional
    visit_Try = _visit_conditional
    visit_While = _visit_conditional
    visit_With = _visit_conditional
    visit_AsyncWith = _visit_conditional

    def result(self) -> dict[str, Any]:
        result: dict[str, Any] = {}
        if self.applications:
            result["applications"] = self.applications
        if self.routers:
            result["routers"] = self.routers
        if self.binding_aliases and (
            self.applications or self.routers or self.includes or self.operations
        ):
            result["aliases"] = self.binding_aliases
        if self.includes:
            result["includes"] = self.includes
        if self.operations:
            result["operations"] = self.operations
        return result


def extract_fastapi_declarations(
    source: str,
    *,
    filepath: str = "",
) -> dict[str, Any]:
    """Extract raw FastAPI declarations from Python source.

    Invalid Python returns an empty result, matching the surrounding Python
    extractor's best-effort behavior.  No target module is imported or executed.
    """
    try:
        tree = ast.parse(source, filename=filepath or "<unknown>")
    except SyntaxError:
        return {}
    scanner = _FastAPIScanner(tree, filepath)
    scanner.visit(tree)
    return scanner.result()


def attach_fastapi_declarations(
    file_entry: dict[str, Any],
    source: str,
    *,
    filepath: str = "",
) -> dict[str, Any]:
    """Attach non-empty FastAPI metadata to an existing Python inventory entry."""
    declarations = extract_fastapi_declarations(source, filepath=filepath)
    if declarations:
        file_entry.setdefault("frameworks", {})["fastapi"] = declarations
    return file_entry


__all__ = ["attach_fastapi_declarations", "extract_fastapi_declarations"]
