"""Bounded executable-syntax observations from an already captured Python AST.

No source is opened or application imported here. Available digests describe
captured syntax, never dependencies, prose correctness, or runtime equivalence.
"""

from __future__ import annotations

import ast
from collections import Counter
from collections.abc import Mapping
import hashlib
import io
import json
import math
from pathlib import PurePosixPath
import platform
import re
import sys
import tokenize
from typing import Any

SCHEMA = "llm-wiki-implementation-observations/v1"
EVIDENCE_SCHEMA = "llm-wiki-implementation-evidence/v1"
ALGORITHM = "python-executable-ast/v1"
MAX_OBSERVATIONS = 128
MAX_OBJECT_BYTES = 65536
CONFIGURATION = {
    "algorithm": ALGORITHM,
    "parser_mode": "exec",
    "type_comments": False,
    "decoding": "python-cookie-match-v1",
    "extractor_decoding": "utf-8-then-cp1252",
    "docstrings": "leading-recursive",
    "locations": "excluded",
    "constants": "tagged-v1",
    "max_observations": MAX_OBSERVATIONS,
    "max_object_bytes": MAX_OBJECT_BYTES,
}
_HASH = re.compile(r"sha256:[0-9a-f]{64}\Z")
_SCOPES = (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)
_DECLARATIONS = (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)
_LOCATIONS = frozenset({"lineno", "col_offset", "end_lineno", "end_col_offset"})


def canonical_bytes(value: Any) -> bytes:
    return (
        json.dumps(
            value,
            sort_keys=True,
            ensure_ascii=False,
            separators=(",", ":"),
            allow_nan=False,
        )
        + "\n"
    ).encode("utf-8")


def _digest(value: Any) -> str:
    return "sha256:" + hashlib.sha256(canonical_bytes(value)).hexdigest()


def analysis_identity(captured: object) -> str | None:
    """Bind only issuer-owned surrounding code/runtime and normalization config."""
    from .analysis_capture import _CapturedAnalysis

    if not isinstance(captured, _CapturedAnalysis):
        return None
    components = {}
    for name in ("agent-wiki-cli", "llm-wiki/extractor/python"):
        row = captured.get(name)
        if not isinstance(row, Mapping):
            return None
        values = {key: row.get(key) for key in ("implementation", "runtime")}
        if any(
            not isinstance(value, str) or not _HASH.fullmatch(value)
            for value in values.values()
        ):
            return None
        components[name] = values
    return _digest(
        {
            "schema_version": "llm-wiki-implementation-analysis/v1",
            "components": components,
            "configuration": CONFIGURATION,
        }
    )


def producer(analysis_hash: str | None, *, language="python") -> dict[str, str] | None:
    if analysis_hash is None:
        return None
    if not isinstance(analysis_hash, str) or not _HASH.fullmatch(analysis_hash):
        raise ValueError(
            "implementation analysis identity must be a qualified SHA-256 digest"
        )
    return {
        "language": language,
        "algorithm": ALGORITHM,
        "parser": "cpython-ast"
        if platform.python_implementation() == "CPython"
        else "unsupported-runtime-ast",
        "parser_version": ".".join(str(value) for value in sys.version_info[:3]),
        "analysis_compatibility_hash": analysis_hash,
    }


def comparison_id(value: Mapping[str, Any]) -> str:
    return _digest(
        {
            "schema_version": "llm-wiki-implementation-comparison/v1",
            "producer": dict(value),
        }
    )


def coordinate_supported(coordinate: Mapping[str, Any], scope: str) -> bool:
    path, owner, occurrence = (
        coordinate["source_path"],
        coordinate["qualified_owner"],
        coordinate["occurrence"],
    )
    parsed = PurePosixPath(path)
    return (
        not parsed.is_absolute()
        and path != "."
        and str(parsed) == path
        and ".." not in parsed.parts
        and "\\" not in path
        and ":" not in path
        and not any(ord(char) < 32 for char in path)
        and all(part.isidentifier() for part in owner.split("."))
        and type(occurrence) is int
        and occurrence >= 1
        and (scope == "module") == (owner == "__module__")
        and len(f"{path}:{owner}#{occurrence}".encode("utf-8")) <= 4096
    )


def _docstring(node: ast.AST) -> str | None:
    body = getattr(node, "body", None)
    if isinstance(node, _SCOPES) and body and isinstance(body[0], ast.Expr):
        value = body[0].value
        if isinstance(value, ast.Constant) and isinstance(value.value, str):
            return value.value
    return None


def _scalar(value: Any) -> Any:
    if value is None:
        return {"type": "none"}
    if value is Ellipsis:
        return {"type": "ellipsis"}
    if type(value) is bool:
        return {"type": "bool", "value": value}
    if type(value) is int:
        return {"type": "int", "value": hex(value)}
    if type(value) is float:
        if not math.isfinite(value):
            raise ValueError(
                "nonfinite Python literal cannot be a canonical JSON observation"
            )
        return {"type": "float", "value": value.hex()}
    if type(value) is complex:
        return {
            "type": "complex",
            "real": _scalar(value.real),
            "imaginary": _scalar(value.imag),
        }
    if type(value) is bytes:
        return {"type": "bytes", "value": value.hex()}
    if type(value) is str:
        return {"type": "str", "value": value}
    raise ValueError("unsupported AST scalar")


def _normalize(value: Any) -> Any:
    if isinstance(value, ast.AST):
        fields = {}
        for name, child in ast.iter_fields(value):
            if name in _LOCATIONS:
                continue
            if (
                name == "body"
                and isinstance(value, _SCOPES)
                and _docstring(value) is not None
            ):
                child = child[1:]
            fields[name] = _normalize(child)
        return {"node": type(value).__name__, "fields": fields}
    if isinstance(value, list):
        return [_normalize(item) for item in value]
    return _scalar(value)


def _declarations(tree: ast.AST, path: str):
    counts: Counter[str] = Counter()
    module = {"source_path": path, "qualified_owner": "__module__", "occurrence": 1}
    yield tree, module, "module", []

    root_lineage = [{"coordinate": module, "scope": "module"}]
    pending = [
        (child, "", root_lineage)
        for child in reversed(list(ast.iter_child_nodes(tree)))
    ]
    while pending:
        child, owner, lineage = pending.pop()
        if isinstance(child, _DECLARATIONS):
            qualified = ".".join(filter(None, (owner, child.name)))
            counts[qualified] += 1
            coordinate = {
                "source_path": path,
                "qualified_owner": qualified,
                "occurrence": counts[qualified],
            }
            scope = "class" if isinstance(child, ast.ClassDef) else "callable"
            yield child, coordinate, scope, lineage
            owner = qualified
            lineage = [*lineage, {"coordinate": coordinate, "scope": scope}]
        pending.extend(
            (grandchild, owner, lineage)
            for grandchild in reversed(list(ast.iter_child_nodes(child)))
        )


def _documentation(node: ast.AST) -> list[dict[str, Any]]:
    counts: Counter[str] = Counter()
    result = []

    def walk(current: ast.AST, owner: str):
        selected = owner
        if current is node:
            selected = "__root__"
        elif isinstance(current, _DECLARATIONS):
            selected = ".".join(
                filter(None, (owner if owner != "__root__" else "", current.name))
            )
        if isinstance(current, _SCOPES):
            counts[selected] += 1
            text = _docstring(current)
            if text is not None:
                result.append(
                    {
                        "owner": selected,
                        "occurrence": counts[selected],
                        "node": type(current).__name__,
                        "docstring": text,
                    }
                )
        for child in ast.iter_child_nodes(current):
            walk(child, selected)

    walk(node, "")
    return result


def _evidence(
    node: ast.AST | None,
    coordinate: dict[str, Any],
    scope: str,
    source_hash: str | None,
    configured: dict[str, str],
    reason: str | None,
) -> dict[str, Any]:
    total = (
        sum(isinstance(child, _DECLARATIONS) for child in ast.walk(node))
        - int(isinstance(node, _DECLARATIONS))
        if node is not None
        else 0
    )
    complete = reason is None
    executable = documentation = None
    if complete and node is not None:
        try:
            executable = _digest(
                {
                    "schema_version": "llm-wiki-executable-fingerprint/v1",
                    "algorithm": ALGORITHM,
                    "scope": scope,
                    "ast": _normalize(node),
                }
            )
            documentation = _digest(
                {
                    "schema_version": "llm-wiki-documentation-fingerprint/v1",
                    "algorithm": ALGORITHM,
                    "scope": scope,
                    "docstrings": _documentation(node),
                }
            )
        except (ValueError, RecursionError):
            complete, reason = False, "unsupported-syntax"
            executable = documentation = None
    return {
        "schema_version": EVIDENCE_SCHEMA,
        "coordinate": coordinate,
        "scope": scope,
        "status": "available" if complete else "unavailable",
        "producer": configured,
        "comparison_id": comparison_id(configured),
        "source_hash": source_hash,
        "executable_hash": executable,
        "documentation_hash": documentation,
        "aggregation": {
            "complete_scope": complete,
            "observations_total": total,
            "observations_returned": min(total, MAX_OBSERVATIONS),
            "truncated": total > MAX_OBSERVATIONS,
        },
        "unavailable_reason": reason,
    }


def capture(
    tree: ast.Module | None,
    data: bytes | None,
    source_path: str,
    *,
    configured: dict[str, str] | None,
    reason: str | None = None,
    parsed_source: str | None = None,
) -> dict[str, Any]:
    """Capture per-file rows from the same tree/bytes used by extraction."""
    path = PurePosixPath(source_path)
    if (
        path.is_absolute()
        or source_path == "."
        or ".." in path.parts
        or str(path) != source_path
        or "\\" in source_path
        or ":" in source_path
        or any(ord(char) < 32 for char in source_path)
    ):
        raise ValueError("implementation source path must be portable and relative")
    source_hash = None if data is None else "sha256:" + hashlib.sha256(data).hexdigest()
    if data is None:
        reason = "missing-source"
    elif tree is None:
        reason = reason or "unsupported-syntax"
    elif reason is None:
        try:
            encoding, _ = tokenize.detect_encoding(io.BytesIO(data).readline)
            if parsed_source is None or data.decode(encoding) != parsed_source:
                reason = "unsupported-syntax"
        except (SyntaxError, UnicodeError, LookupError):
            reason = "unsupported-syntax"
    total = (
        1 + sum(isinstance(node, _DECLARATIONS) for node in ast.walk(tree))
        if tree is not None
        else 1
    )
    declared = (
        _declarations(tree, source_path)
        if tree is not None
        else [
            (
                None,
                {
                    "source_path": source_path,
                    "qualified_owner": "__module__",
                    "occurrence": 1,
                },
                "module",
                [],
            )
        ]
    )
    if configured is None:
        return {
            "source_hash": source_hash,
            "producer": None,
            "status": "unavailable",
            "reason": "unsupported-producer",
            "observations": [],
            "bounds": {
                "total": total,
                "returned": 0,
                "truncated": True,
                "omitted": total,
                "reason": "unsupported-producer",
            },
        }
    if configured["language"] != "python":
        reason = "unsupported-language"
    elif (
        configured["algorithm"] != ALGORITHM
        or configured["parser"] != "cpython-ast"
        or re.fullmatch(r"3\.(10|11|12|13|14)\.\d+", configured["parser_version"])
        is None
    ):
        reason = "unsupported-producer"
    rows = []
    candidate = None
    omitted_reason = None
    for node, coordinate, scope, lineage in declared:
        if len(rows) >= MAX_OBSERVATIONS:
            break
        if not coordinate_supported(coordinate, scope) or any(
            not coordinate_supported(parent["coordinate"], parent["scope"])
            for parent in lineage
        ):
            omitted_reason = "selector-limit-or-ambiguous-owner"
            continue
        row = {
            "evidence": _evidence(
                node, coordinate, scope, source_hash, configured, reason
            ),
            "line": None
            if node is None or isinstance(node, ast.Module)
            else getattr(node, "lineno", None),
            "lineage": lineage,
        }
        following = [*rows, row]
        candidate = {
            "source_hash": source_hash,
            "producer": configured,
            "status": "available"
            if reason is None and tree is not None
            else "unavailable",
            "reason": reason,
            "observations": following,
            "bounds": {
                "total": total,
                "returned": len(following),
                "truncated": len(following) < total,
                "omitted": total - len(following),
                "reason": "object-or-observation-limit"
                if len(following) < total
                else None,
            },
        }
        if len(canonical_bytes(candidate)) > MAX_OBJECT_BYTES:
            break
        rows = following
    result = {
        "source_hash": source_hash,
        "producer": configured,
        "status": "available" if reason is None and tree is not None else "unavailable",
        "reason": reason,
        "observations": rows,
        "bounds": {
            "total": total,
            "returned": len(rows),
            "truncated": len(rows) < total,
            "omitted": total - len(rows),
            "reason": "object-or-observation-limit" if len(rows) < total else None,
        },
    }
    if not rows and len(canonical_bytes(result)) > MAX_OBJECT_BYTES:
        raise ValueError("implementation envelope minimum exceeds its byte limit")
    if omitted_reason is not None:
        result["bounds"]["reason"] = omitted_reason
        if not rows:
            result.update(status="unavailable", reason="object-limit")
    if not rows and result["status"] == "available":
        result.update(status="unavailable", reason="object-limit")
    for row in rows:
        coordinate = row["evidence"]["coordinate"]
        returned = sum(
            any(ancestor["coordinate"] == coordinate for ancestor in other["lineage"])
            for other in rows
        )
        aggregation = row["evidence"]["aggregation"]
        aggregation.update(
            observations_returned=returned,
            truncated=returned < aggregation["observations_total"],
        )
    states = {row["evidence"]["status"] for row in rows}
    if "unavailable" in states:
        result["status"] = "partial" if "available" in states else "unavailable"
        result["reason"] = next(
            row["evidence"]["unavailable_reason"]
            for row in rows
            if row["evidence"]["status"] == "unavailable"
        )
    while len(canonical_bytes(result)) > MAX_OBJECT_BYTES:
        if not rows:
            raise ValueError("implementation envelope minimum exceeds its byte limit")
        rows.pop()
        result["bounds"].update(
            returned=len(rows),
            omitted=total - len(rows),
            truncated=True,
            reason="object-or-observation-limit",
        )
        for row in rows:
            coordinate = row["evidence"]["coordinate"]
            returned = sum(
                any(
                    ancestor["coordinate"] == coordinate
                    for ancestor in other["lineage"]
                )
                for other in rows
            )
            aggregation = row["evidence"]["aggregation"]
            aggregation.update(
                observations_returned=returned,
                truncated=returned < aggregation["observations_total"],
            )
        states = {row["evidence"]["status"] for row in rows}
        result["status"] = (
            "partial"
            if len(states) > 1
            else next(iter(states))
            if states
            else "unavailable"
        )
        result["reason"] = next(
            (
                row["evidence"]["unavailable_reason"]
                for row in rows
                if row["evidence"]["status"] == "unavailable"
            ),
            reason if rows else "object-limit",
        )
    return result


def envelope(files: Mapping[str, dict]) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA,
        "files": dict(sorted(files.items())),
        "limitations": [
            "captured-executable-syntax-only",
            "dependencies-and-runtime-behavior-not-evaluated",
        ],
    }
