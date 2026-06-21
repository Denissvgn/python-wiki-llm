"""Pure documentation graph query helpers.

This module indexes already-built inventory, call graph, data-flow, dependency,
and wiki-surface payloads. It intentionally performs no file writes, file reads,
network calls, or adapter registration so CLI, Python API, MCP, and context
surfaces can consume the same deterministic query answers later.
"""

from __future__ import annotations

import json
import re
from pathlib import PurePosixPath
from typing import Any, Iterable, Mapping, Optional

from .dependencies import (
    build_dependency_graph,
    dependency_metrics,
    detect_cycles,
    topological_order,
)
from .relationships import build_entity_relationship_summaries

_DEFAULT_LIMIT = 20
_WINDOWS_ABSOLUTE_RE = re.compile(r"^[A-Za-z]:/")


class DocumentationQueryError(ValueError):
    """Raised when a documentation graph query request is invalid."""


def _text_key(value: object) -> tuple[str, str]:
    text = "" if value is None else str(value)
    return text.casefold(), text


def _value_key(value: object) -> tuple:
    if isinstance(value, bool):
        return (0, int(value))
    if isinstance(value, (int, float)):
        return (0, value)
    return (1,) + _text_key(value)


def _record_sort_key(record: Mapping[str, Any]) -> tuple:
    ordered = (
        "canonical_path",
        "file",
        "source_path",
        "symbol",
        "name",
        "id",
        "title",
        "kind",
        "module",
        "role",
        "line",
        "depth",
        "index",
    )
    parts = [_value_key(record.get(key)) for key in ordered if key in record]
    parts.append(_text_key(json.dumps(_jsonable(record), sort_keys=True)))
    return tuple(parts)


def _jsonable(value: object) -> object:
    if isinstance(value, Mapping):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_jsonable(item) for item in value]
    if isinstance(value, list):
        return [_jsonable(item) for item in value]
    return value


def _require_query(value: object, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise DocumentationQueryError(f"{field} must be a non-empty string.")
    return value.strip()


def _normalise_source_path(
    value: object, *, field: str, required: bool
) -> Optional[str]:
    if not isinstance(value, str) or not value.strip():
        if required:
            raise DocumentationQueryError(f"{field} must be a non-empty string.")
        return None

    raw = value.strip().replace("\\", "/")
    if raw.startswith("/") or _WINDOWS_ABSOLUTE_RE.match(raw):
        if required:
            raise DocumentationQueryError(f"{field} must be a relative source path.")
        return None

    path = PurePosixPath(raw)
    if ".." in path.parts:
        if required:
            raise DocumentationQueryError(f"{field} must not contain '..'.")
        return None

    normalised = path.as_posix()
    while normalised.startswith("./"):
        normalised = normalised[2:]
    if not normalised or normalised == ".":
        if required:
            raise DocumentationQueryError(f"{field} must be a source file path.")
        return None
    return normalised


def _module_name(filepath: Optional[str]) -> Optional[str]:
    if not filepath:
        return None
    return PurePosixPath(filepath).stem


def _callable_ref(summary: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "symbol": summary.get("symbol"),
        "name": summary.get("name"),
        "file": summary.get("file"),
        "module": summary.get("module"),
        "kind": summary.get("kind"),
        "owner_class": summary.get("owner_class"),
    }


def _class_ref(summary: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "name": summary.get("name"),
        "file": summary.get("file"),
        "module": summary.get("module"),
        "kind": "class",
    }


def _flow_ref(flow: Mapping[str, Any]) -> dict[str, Any]:
    entry = flow.get("entry", {}) or {}
    return {
        "id": flow.get("id") or entry.get("id"),
        "category": flow.get("category") or entry.get("category"),
        "file": entry.get("file") or flow.get("file"),
        "symbol": entry.get("symbol") or flow.get("symbol"),
        "label": flow.get("label") or entry.get("label") or entry.get("symbol"),
    }


def _page_ref(page: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "kind": page.get("kind"),
        "id": page.get("id"),
        "title": page.get("title"),
        "canonical_path": page.get("canonical_path"),
        "source_path": _normalise_source_path(
            page.get("source_path"), field="source_path", required=False
        ),
        "role": page.get("role"),
        "mcp_uri": page.get("mcp_uri"),
    }


def _edge_pair(edge: object) -> Optional[tuple[str, str]]:
    if isinstance(edge, Mapping):
        source = edge.get("from") or edge.get("source")
        target = edge.get("to") or edge.get("target")
        if isinstance(source, str) and isinstance(target, str):
            return source, target
        return None
    if isinstance(edge, (list, tuple)) and len(edge) == 2:
        return str(edge[0]), str(edge[1])
    return None


class DocumentationGraphQueryService:
    """Read-only graph query service over already-derived documentation payloads."""

    def __init__(
        self,
        inventory: Mapping[str, Mapping[str, Any]],
        *,
        call_edges: Optional[Iterable[Mapping[str, Any]]] = None,
        flows: Optional[Iterable[Mapping[str, Any]]] = None,
        data_flows: Optional[object] = None,
        dependency_analysis: Optional[Mapping[str, Any]] = None,
        surface_index: Optional[Mapping[str, Any]] = None,
        limit: int = _DEFAULT_LIMIT,
    ):
        if isinstance(limit, bool) or not isinstance(limit, int) or limit < 1:
            raise DocumentationQueryError("limit must be a positive integer.")

        self.limit = limit
        self.inventory = {
            _normalise_source_path(path, field="inventory path", required=False)
            or str(path).replace("\\", "/"): dict(data or {})
            for path, data in (inventory or {}).items()
        }
        self.call_edges = [_jsonable(edge) for edge in (call_edges or [])]
        self.flows = [_jsonable(flow) for flow in (flows or [])]
        self.data_flows = self._normalise_data_flows(data_flows)
        self.dependency = self._dependency_payload(dependency_analysis)
        self.pages = self._surface_pages(surface_index or {})

        relationships = build_entity_relationship_summaries(
            self.inventory,
            call_edges=self.call_edges,
            flows=self.flows,
        )
        self.callable_summaries = [
            _jsonable(summary) for summary in relationships.get("functions", [])
        ]
        self.class_summaries = [
            _jsonable(summary) for summary in relationships.get("classes", [])
        ]
        self.callables = [_callable_ref(summary) for summary in self.callable_summaries]
        self.classes = [_class_ref(summary) for summary in self.class_summaries]
        self.callable_by_key = {
            (summary.get("file"), summary.get("symbol")): summary
            for summary in self.callable_summaries
        }

    def flow_for_entrypoint(self, id_or_symbol: object) -> dict[str, Any]:
        """Return a bounded user-flow payload for an entry-point id or symbol."""
        query = _require_query(id_or_symbol, "id_or_symbol")
        matches = self._flow_matches(query, self.flows)
        result = self._selection_result(query, matches, "flow", None)
        if not result["found"]:
            result["flow"] = None
            return result

        flow, truncated = self._bounded_payload(result.pop("_selected"), ("steps",))
        result["flow"] = flow
        result["truncated"] = result["truncated"] or truncated
        return result

    def callers(self, symbol: object) -> dict[str, Any]:
        """Return bounded callers for exactly one callable symbol."""
        query = _require_query(symbol, "symbol")
        matches = self._callable_matches(query)
        result = self._selection_result(query, matches, "callable", None)
        if not result["found"]:
            result["callable"] = None
            result["callers"] = []
            return result

        selected = result.pop("_selected")
        summary = self.callable_by_key[(selected.get("file"), selected.get("symbol"))]
        callers, truncated = self._bounded(summary.get("callers", []))
        result["callable"] = selected
        result["callers"] = callers
        result["truncated"] = result["truncated"] or truncated
        return result

    def callees(self, symbol: object) -> dict[str, Any]:
        """Return bounded callees for exactly one callable symbol."""
        query = _require_query(symbol, "symbol")
        matches = self._callable_matches(query)
        result = self._selection_result(query, matches, "callable", None)
        if not result["found"]:
            result["callable"] = None
            result["callees"] = []
            return result

        selected = result.pop("_selected")
        summary = self.callable_by_key[(selected.get("file"), selected.get("symbol"))]
        callees, truncated = self._bounded(summary.get("callees", []))
        result["callable"] = selected
        result["callees"] = callees
        result["truncated"] = result["truncated"] or truncated
        return result

    def dependency_neighborhood(self, path: object) -> dict[str, Any]:
        """Return bounded inbound/outbound dependency neighbors for a source path."""
        query = _normalise_source_path(path, field="path", required=True)
        graph = self.dependency["graph"]
        nodes = set(graph.get("nodes", [])) | set(self.inventory)
        empty = {
            "query": query,
            "found": False,
            "ambiguous": False,
            "matches": [],
            "truncated": False,
            "path": None,
            "inbound": [],
            "outbound": [],
            "metrics": {"fan_in": 0, "fan_out": 0},
            "cycle_groups": [],
            "load_order_index": None,
            "pages": [],
        }
        if query not in nodes:
            return empty

        inbound = []
        outbound = []
        for source, target in self._dependency_edges():
            if target == query:
                inbound.append(source)
            if source == query:
                outbound.append(target)

        inbound, inbound_truncated = self._bounded_strings(inbound)
        outbound, outbound_truncated = self._bounded_strings(outbound)
        pages, pages_truncated = self._pages_for_source(query)
        order = self.dependency.get("load_order", {}).get("order", []) or []
        metrics = (
            self.dependency.get("metrics", {})
            .get("metrics", {})
            .get(query, {"fan_in": 0, "fan_out": 0})
        )
        cycle_groups = [
            list(group)
            for group in self.dependency.get("cycles", [])
            if query in set(group)
        ]
        cycle_groups, cycles_truncated = self._bounded(cycle_groups)

        return {
            "query": query,
            "found": True,
            "ambiguous": False,
            "matches": [{"path": query}],
            "truncated": any(
                [
                    inbound_truncated,
                    outbound_truncated,
                    pages_truncated,
                    cycles_truncated,
                ]
            ),
            "path": query,
            "inbound": inbound,
            "outbound": outbound,
            "metrics": dict(metrics),
            "cycle_groups": cycle_groups,
            "load_order_index": order.index(query) if query in order else None,
            "pages": pages,
        }

    def data_flow_for_entrypoint(self, id_or_symbol: object) -> dict[str, Any]:
        """Return a bounded data-flow payload for an entry-point id or symbol."""
        query = _require_query(id_or_symbol, "id_or_symbol")
        matches = self._flow_matches(query, self.data_flows)
        result = self._selection_result(query, matches, "data_flow", None)
        if not result["found"]:
            result["data_flow"] = None
            return result

        data_flow, truncated = self._bounded_payload(
            result.pop("_selected"),
            ("steps", "transfers", "boundaries", "gaps"),
        )
        result["data_flow"] = data_flow
        result["truncated"] = result["truncated"] or truncated
        return result

    def pages_for_symbol(self, symbol: object) -> dict[str, Any]:
        """Return bounded wiki surface pages related to exactly one symbol."""
        query = _require_query(symbol, "symbol")
        matches = self._symbol_matches(query)
        result = self._selection_result(query, matches, "symbol", None)
        if not result["found"]:
            result["symbol"] = None
            result["pages"] = []
            return result

        selected = result.pop("_selected")
        pages, pages_truncated = self._pages_for_source(selected.get("file"))
        result["symbol"] = selected
        result["pages"] = pages
        result["truncated"] = result["truncated"] or pages_truncated
        return result

    def _normalise_data_flows(
        self, data_flows: Optional[object]
    ) -> list[dict[str, Any]]:
        if data_flows is None:
            return []
        if isinstance(data_flows, Mapping):
            if "entry" in data_flows or "steps" in data_flows:
                return [_jsonable(data_flows)]  # type: ignore[list-item]
            return [_jsonable(value) for value in data_flows.values()]  # type: ignore[list-item]
        return [_jsonable(value) for value in data_flows]  # type: ignore[union-attr]

    def _dependency_payload(
        self, dependency_analysis: Optional[Mapping[str, Any]]
    ) -> dict[str, Any]:
        if dependency_analysis is None:
            graph = build_dependency_graph(dict(self.inventory))
            return {
                "graph": graph,
                "cycles": detect_cycles(graph),
                "metrics": dependency_metrics(graph),
                "load_order": topological_order(graph),
            }

        graph = dependency_analysis.get("graph") or build_dependency_graph(
            dict(self.inventory)
        )
        return {
            "graph": _jsonable(graph),
            "cycles": _jsonable(
                dependency_analysis.get("cycles") or detect_cycles(graph)
            ),
            "metrics": _jsonable(
                dependency_analysis.get("metrics") or dependency_metrics(graph)
            ),
            "load_order": _jsonable(
                dependency_analysis.get("load_order") or topological_order(graph)
            ),
        }

    def _surface_pages(self, surface_index: Mapping[str, Any]) -> list[dict[str, Any]]:
        pages = [_page_ref(page) for page in surface_index.get("pages", []) or []]
        return sorted(pages, key=_record_sort_key)

    def _dependency_edges(self) -> list[tuple[str, str]]:
        pairs = []
        for edge in self.dependency.get("graph", {}).get("edges", []) or []:
            pair = _edge_pair(edge)
            if pair is not None:
                pairs.append(pair)
        return sorted(
            set(pairs), key=lambda item: (_text_key(item[0]), _text_key(item[1]))
        )

    def _callable_matches(self, query: str) -> list[dict[str, Any]]:
        matches = [
            ref
            for ref in self.callables
            if query in {str(ref.get("symbol")), str(ref.get("name"))}
        ]
        if matches:
            return sorted(matches, key=_record_sort_key)

        if ":" not in query:
            return []
        raw_file, _, raw_symbol = query.partition(":")
        filepath = _normalise_source_path(raw_file, field="symbol file", required=False)
        if not filepath or not raw_symbol:
            return []
        return sorted(
            [
                ref
                for ref in self.callables
                if ref.get("file") == filepath
                and raw_symbol in {str(ref.get("symbol")), str(ref.get("name"))}
            ],
            key=_record_sort_key,
        )

    def _symbol_matches(self, query: str) -> list[dict[str, Any]]:
        callables = self._callable_matches(query)
        classes = [ref for ref in self.classes if query in {str(ref.get("name"))}]
        return sorted(callables + classes, key=_record_sort_key)

    def _flow_matches(
        self, query: str, records: Iterable[Mapping[str, Any]]
    ) -> list[dict[str, Any]]:
        matches = []
        for record in records:
            ref = _flow_ref(record)
            identifiers = {
                str(ref.get("id")),
                str(ref.get("symbol")),
                str(ref.get("label")),
            }
            if query in identifiers:
                matches.append(record)
        return sorted(matches, key=lambda item: _record_sort_key(_flow_ref(item)))

    def _selection_result(
        self,
        query: str,
        matches: list[Mapping[str, Any]],
        payload_key: str,
        empty_payload: object,
    ) -> dict[str, Any]:
        refs = [
            _flow_ref(match) if payload_key in {"flow", "data_flow"} else match
            for match in matches
        ]
        capped, truncated = self._bounded(refs)
        if not matches:
            return {
                "query": query,
                "found": False,
                "ambiguous": False,
                "matches": [],
                "truncated": False,
                payload_key: empty_payload,
            }
        if len(matches) > 1:
            return {
                "query": query,
                "found": False,
                "ambiguous": True,
                "matches": capped,
                "truncated": truncated,
                payload_key: empty_payload,
            }
        return {
            "query": query,
            "found": True,
            "ambiguous": False,
            "matches": capped,
            "truncated": truncated,
            "_selected": _jsonable(matches[0]),
        }

    def _pages_for_source(
        self, source_path: object
    ) -> tuple[list[dict[str, Any]], bool]:
        normalised = _normalise_source_path(
            source_path, field="source_path", required=False
        )
        if normalised is None:
            return [], False
        return self._bounded(
            page for page in self.pages if page.get("source_path") == normalised
        )

    def _bounded_payload(
        self, payload: object, list_keys: tuple[str, ...]
    ) -> tuple[dict[str, Any], bool]:
        copied = _jsonable(payload)
        if not isinstance(copied, dict):
            return {}, False
        truncated = False
        for key in list_keys:
            if not isinstance(copied.get(key), list):
                continue
            copied[key], was_truncated = self._bounded(copied[key])
            truncated = truncated or was_truncated
        return copied, truncated

    def _bounded(self, records: Iterable[object]) -> tuple[list[Any], bool]:
        items = [_jsonable(record) for record in records]
        if all(isinstance(item, Mapping) for item in items):
            items = sorted(items, key=_record_sort_key)  # type: ignore[arg-type]
        truncated = len(items) > self.limit
        return items[: self.limit], truncated

    def _bounded_strings(self, values: Iterable[object]) -> tuple[list[str], bool]:
        ordered = sorted({str(value) for value in values}, key=_text_key)
        truncated = len(ordered) > self.limit
        return ordered[: self.limit], truncated
