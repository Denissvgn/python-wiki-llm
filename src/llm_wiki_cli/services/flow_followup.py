"""Bounded, source-bound navigation over an already captured static call graph.

Offsets page one deterministic trace; a depth frontier narrows to a new exact
root in the same graph. Neither operation executes source or extends a legacy
flow's analysis limits. Querying again repeats graph counting, not extraction.
"""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Iterator, Mapping
from typing import Any

from .data_flow import _STEP_LIMIT
from .documentation_queries import DocumentationQueryError
from .entrypoints import DEFAULT_FLOW_DEPTH, _build_adjacency, _flow_step_from_edge, _iter_callables
from .source_snapshot import SourceSnapshot
from .validation import require_portable_relative_path

SCHEMA = "llm-wiki-flow-segment/v1"
_STEP_BYTE_BUDGET = 32 * 1024
_MAX_OFFSET = 1_000_000
_BASIS_RE = re.compile(r"sha256:[0-9a-f]{64}\Z")


def _portable_file(value: str) -> str:
    """Keep the shared path adapter separate from flow request semantics."""
    return require_portable_relative_path(value)


def validate_request(value: object, basis: object = None, offset: object = 0) -> tuple[str, str]:
    """Validate before any workspace access, including exact portable identity."""
    error = DocumentationQueryError("value must be a qualified file:symbol coordinate.", field="value")
    if not isinstance(value, str) or ":" not in value:
        raise error
    try:
        if len(value.encode("utf-8")) > 4096:
            raise error
    except UnicodeError as exc:
        raise error from exc
    file, _, symbol = value.partition(":")
    try:
        _portable_file(file)
    except ValueError as exc:
        raise error from exc
    if not symbol or symbol.strip() != symbol or any(ord(c) < 32 or ord(c) == 127 for c in symbol):
        raise error
    if type(offset) is not int or not 0 <= offset <= _MAX_OFFSET:
        raise DocumentationQueryError("offset must be an integer from 0 to 1000000.", field="offset")
    if basis is not None and (not isinstance(basis, str) or not _BASIS_RE.fullmatch(basis)):
        raise DocumentationQueryError("basis must be a captured flow binding.", field="basis")
    if offset and basis is None:
        raise DocumentationQueryError("offset requires the preceding result's basis.", field="basis")
    return file, symbol


def _binding(inventory: dict, edges: list[dict], receipt: object, query_binding: Mapping | None,
             limit: int) -> tuple[str | None, int, int]:
    snapshot = getattr(receipt, "source_snapshot", None)
    analysis = getattr(receipt, "analysis_components", None)
    if (not isinstance(snapshot, SourceSnapshot) or not isinstance(analysis, Mapping)
            or not analysis or not query_binding):
        return None, 0, 0
    payload = {
        "schema": SCHEMA, "depth_limit": DEFAULT_FLOW_DEPTH, "step_limit": limit,
        "ordering": "captured-edge-depth-first-preorder-global-visited/v1",
        "source": {
            "root": str(snapshot.root),
            "paths": snapshot.all_source_paths, "hashes": snapshot.captured_content_hashes,
            "kinds": snapshot.captured_input_kinds, "ignore": snapshot.gitignore_fingerprint,
            "selection": snapshot.source_selection_identity, "selection_inputs": snapshot.source_selection_inputs,
            "only_files": None if snapshot.only_files is None else sorted(snapshot.only_files),
            "respect_ignores": snapshot.respect_ignores, "respect_discovery": snapshot.respect_discovery,
        },
        "producers": analysis, "query_producer": query_binding, "inventory": inventory, "edges": edges,
    }
    digest = hashlib.sha256()
    size = 0
    # Avoid another serialized copy of the complete inventory in memory.
    for chunk in json.JSONEncoder(sort_keys=True, ensure_ascii=True, separators=(",", ":"), allow_nan=False).iterencode(payload):
        encoded = chunk.encode("utf-8")
        digest.update(encoded)
        size += len(encoded)
    return "sha256:" + digest.hexdigest(), size, len(snapshot.captured_content_hashes)


def _walk(start: tuple, adjacency: dict, depth_limit: int | None, work: dict) -> Iterator[tuple[dict, int]]:
    """Visit each internal node once, keeping only the active iterator stack."""
    visited = {start}
    pending = [(iter(adjacency.get(start, ())), 0)]
    work["expanded_nodes"] = 1
    work["traversed_edges"] = 0
    while pending:
        outgoing, depth = pending[-1]
        edge = next(outgoing, None)
        if edge is None:
            pending.pop()
            continue
        work["traversed_edges"] += 1
        yield edge, depth + 1
        target = (edge["to"]["file"], edge["to"]["symbol"])
        if edge["kind"] == "internal" and target[0] is not None and target not in visited:
            visited.add(target)
            if depth_limit is None or depth + 1 < depth_limit:
                work["expanded_nodes"] += 1
                pending.append((iter(adjacency.get(target, ())), depth + 1))


def _request(value: str, basis: str, *, offset: int = 0, limit: int = _STEP_LIMIT) -> dict:
    return {"operation": "flow-segment", "value": value, "basis": basis,
            "offset": offset, "limit": limit, "allow_full_inventory": True}


def _unavailable(reason: str) -> dict:
    return {"status": "unavailable", "reason": reason}


def segment(inventory: dict, edges: list[dict], receipt: object, value: str,
            *, limit: int, basis: str | None = None, offset: int = 0,
            query_binding: Mapping | None = None) -> dict[str, Any]:
    file, symbol = validate_request(value, basis, offset)
    step_limit = min(_STEP_LIMIT, limit)
    current_basis, binding_bytes, captured_files = _binding(inventory, edges, receipt, query_binding, step_limit)
    if basis is not None and (current_basis is None or basis != current_basis):
        raise DocumentationQueryError("basis differs from this captured source/producer/graph or traversal options; restart the query.", field="basis")
    owners = [(path, name, fn) for path, name, fn in _iter_callables(inventory) if (path, name) == (file, symbol)]
    found = len(owners) == 1
    refs = [{"file": path, "symbol": name, "line": fn.get("line")} for path, name, fn in owners]
    result: dict[str, Any] = {
        "segment_schema": SCHEMA, "query": value, "found": found, "ambiguous": len(owners) > 1,
        "matches": refs[:limit], "owner": {"file": file, "symbol": symbol} if found else None,
        "basis": current_basis, "steps": [], "truncated": len(refs) > limit,
        "bounds": {"matches": {"total": len(refs), "returned": min(len(refs), limit), "truncated": len(refs) > limit}},
        "work": {"inventory_files": len(inventory), "graph_edges": len(edges), "captured_files": captured_files,
                 "binding_bytes": binding_bytes, "expanded_nodes": 0, "traversed_edges": 0, "counted_edges": 0},
        "follow_up": _unavailable("owner-ambiguous" if len(owners) > 1 else "owner-not-found"),
        "limitations": ["captured-static-graph-not-runtime-completeness", "a-small-segment-does-not-limit-inventory-or-graph-counting-work"],
    }
    if not found:
        return result
    if current_basis is None:
        result["follow_up"] = _unavailable("captured-source-and-producer-binding-unavailable")
        return result

    adjacency = _build_adjacency(edges)
    start = (file, symbol)
    steps: list[dict] = []
    delivered_bytes = 0
    delivery_blocked = False
    eligible = 1

    def emit(step: dict, index: int) -> None:
        nonlocal delivered_bytes, delivery_blocked
        if index < offset or len(steps) >= step_limit or delivery_blocked:
            return
        if step["kind"] in {"entry", "internal"} and step["depth"] == DEFAULT_FLOW_DEPTH and adjacency.get((step["file"], step["symbol"])):
            step["follow_up"] = {"status": "available", "request": _request(f"{step['file']}:{step['symbol']}", current_basis, limit=step_limit)}
        size = len(json.dumps(step, ensure_ascii=True, separators=(",", ":")).encode("utf-8"))
        if delivered_bytes + size > _STEP_BYTE_BUDGET:
            delivery_blocked = True
        else:
            steps.append(step)
            delivered_bytes += size

    emit({"depth": 0, "file": file, "symbol": symbol, "kind": "entry"}, 0)
    traversal_work: dict = {}
    for edge, depth in _walk(start, adjacency, DEFAULT_FLOW_DEPTH, traversal_work):
        if offset <= eligible < offset + step_limit and not delivery_blocked:
            emit(_flow_step_from_edge(edge, depth), eligible)
        eligible += 1
    counting_work: dict = {}
    observed = 1 + sum(1 for _ in _walk(start, adjacency, None, counting_work))
    if offset > eligible:
        raise DocumentationQueryError("offset is outside this captured trace.", field="offset")
    omitted_before = min(offset, eligible)
    omitted_after = eligible - omitted_before - len(steps)
    result["steps"] = steps
    result["coverage"] = {
        "observed": observed, "eligible": eligible, "returned": len(steps),
        "omitted_before": omitted_before, "omitted_after": omitted_after,
        "depth_omitted": observed - eligible, "depth_limit": DEFAULT_FLOW_DEPTH,
        "step_limit": step_limit, "runtime_completeness": False,
    }
    result["truncated"] = bool(omitted_before or omitted_after or observed > eligible)
    result["bounds"]["steps"] = {"total": eligible, "returned": len(steps), "truncated": eligible > len(steps)}
    result["work"].update(traversal_work)
    result["work"]["counted_edges"] = counting_work["traversed_edges"]
    result["follow_up"] = (
        _unavailable("step-delivery-byte-limit") if delivery_blocked else
        _unavailable("offset-limit") if omitted_after and offset + len(steps) > _MAX_OFFSET else
        {"status": "available", "request": _request(value, current_basis, offset=offset + len(steps), limit=step_limit)} if omitted_after else
        _unavailable("no-more-rows-at-this-depth")
    )
    return result
