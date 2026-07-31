"""Pure documentation graph query helpers.

This module indexes already-built inventory, call graph, data-flow, dependency,
and wiki-surface payloads. It intentionally performs no file writes, file reads,
network calls, or adapter registration so CLI, Python API, MCP, and context
surfaces can consume the same deterministic query answers later.
"""

from __future__ import annotations

import json
import re
from collections import defaultdict
from collections.abc import Iterable as IterableABC
from dataclasses import dataclass
from enum import Enum
from pathlib import PurePosixPath
from typing import Any, Iterable, Mapping, Optional, Sequence, cast

from .contracts import SECTION_OWNERSHIP_EXTENSION_KEY
from .dependencies import (
    build_dependency_graph,
    dependency_metrics,
    detect_cycles,
    topological_order,
)
from .knowledge_consumption import (
    KnowledgeAvailability,
    KnowledgeReadReason,
    KnowledgeReadView,
)
from .knowledge_graph import (
    CORE_RELATIONSHIP_KINDS,
    GRAPH_ORIGINS,
    GRAPH_RESOLUTIONS,
    KnowledgeGraphError,
    typed_graph_from_knowledge_extensions,
)
from .knowledge_governance import GOVERNANCE_EXTENSION_KEY
from .knowledge_model import knowledge_index_to_payload
from .knowledge_observability import (
    knowledge_freshness_hint,
    knowledge_status_payload,
)
from .relationships import build_entity_relationship_summaries
from .validation import (
    normalize_legacy_portable_relative_path,
    require_nonempty_text,
)

_DEFAULT_LIMIT = 20
_QUALIFIED_NAME_RE = re.compile(
    r"^[A-Za-z][A-Za-z0-9._-]*/[A-Za-z][A-Za-z0-9._-]*$"
)
_KNOWLEDGE_RELATIONSHIP_KINDS = ("derived_from", "links_to")
_KNOWLEDGE_DIRECTIONS = ("inbound", "outbound", "both")
_TYPED_GRAPH_DIRECTIONS = ("incoming", "outgoing", "both")
_TYPED_GRAPH_READY_REASON = "typed-graph-extension-ready"
_TYPED_GRAPH_ABSENT_REASON = "typed-graph-extension-not-present"
_SECTION_OWNERSHIP_READY_REASON = "section-ownership-extension-ready"
_SECTION_OWNERSHIP_ABSENT_REASON = "section-ownership-extension-not-present"
_SECTION_OWNERSHIP_VALUES = ("generated", "semantic", "mixed", "unknown")
_NOT_EVALUATED_REASON = "not-evaluated"


class DocumentationQueryError(ValueError):
    """Raised when a documentation graph query request is invalid."""


@dataclass(frozen=True)
class _BoundedResult:
    """One deterministic collection plus its exact response bounds."""

    items: list[Any]
    total: int

    @property
    def returned(self) -> int:
        return len(self.items)

    @property
    def truncated(self) -> bool:
        return self.total > self.returned

    def metadata(self) -> dict[str, Any]:
        return {
            "total": self.total,
            "returned": self.returned,
            "truncated": self.truncated,
        }


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


def _jsonable_mapping(value: Mapping[str, Any]) -> dict[str, Any]:
    return cast(dict[str, Any], _jsonable(value))


def _jsonable_mapping_list(values: Iterable[Mapping[str, Any]]) -> list[dict[str, Any]]:
    return [_jsonable_mapping(value) for value in values]


def _require_query(value: object, field: str) -> str:
    """Retain query-request whitespace normalization for API compatibility."""

    return require_nonempty_text(
        value,
        error=DocumentationQueryError(f"{field} must be a non-empty string."),
        normalize=True,
        reject_control_characters=False,
    )


def _normalise_source_path(
    value: object, *, field: str, required: bool
) -> Optional[str]:
    return normalize_legacy_portable_relative_path(
        value,
        text_error=(
            DocumentationQueryError(f"{field} must be a non-empty string.")
            if required
            else None
        ),
        absolute_error=(
            DocumentationQueryError(f"{field} must be a relative source path.")
            if required
            else None
        ),
        traversal_error=(
            DocumentationQueryError(f"{field} must not contain '..'.")
            if required
            else None
        ),
        empty_error=(
            DocumentationQueryError(f"{field} must be a source file path.")
            if required
            else None
        ),
        invalid_error=(
            DocumentationQueryError(f"{field} must be a relative source path.")
            if required
            else None
        ),
    )


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


def _call_endpoint_ref(endpoint: Mapping[str, Any], edge: Mapping[str, Any]) -> dict:
    filepath = endpoint.get("file")
    return {
        "file": filepath,
        "module": _module_name(str(filepath)) if filepath else None,
        "symbol": endpoint.get("symbol"),
        "kind": edge.get("kind", "unknown"),
        "line": edge.get("line", 0),
    }


def _dedupe_sorted_all(records: Iterable[Mapping[str, Any]]) -> list[dict[str, Any]]:
    unique: dict[str, dict[str, Any]] = {}
    for record in records:
        key = json.dumps(_jsonable(record), sort_keys=True, separators=(",", ":"))
        unique[key] = _jsonable_mapping(record)
    return sorted(unique.values(), key=_record_sort_key)


def _summary_relationship_records(
    summary: Mapping[str, Any], field: str
) -> list[dict[str, Any]]:
    records = summary.get(field)
    if not isinstance(records, list):
        return []
    return [
        _jsonable_mapping(record) for record in records if isinstance(record, Mapping)
    ]


def _wire_value(value: object) -> object:
    return value.value if isinstance(value, Enum) else value


def _canonical_json(value: object) -> str:
    return json.dumps(
        _jsonable(value),
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    )


def _knowledge_target_ref(
    target: Mapping[str, Any],
    resolution: object,
) -> dict[str, Any]:
    """Return only the coordinates needed to understand a compact target."""

    fields = [
        "target_class",
        "locator",
        "canonical_path",
        "source_path",
        "external_uri",
    ]
    if resolution in {"ambiguous", "unresolved"}:
        fields.extend(("raw_target", "normalized_target"))
    elif target.get("target_class") in {"anchor", "asset"}:
        fields.append("normalized_target")
    return {
        field: _jsonable(target[field])
        for field in fields
        if field in target and target[field] is not None
    }


def _freshness_basis_payload(value: object) -> Optional[dict[str, Any]]:
    if value is None:
        return None
    fields = (
        "scope",
        "source_path",
        "extractor_ref",
        "source_content_hash",
        "concept_observation_hash",
        "analysis_basis_hash",
        "unknown_reason",
    )
    payload: dict[str, Any] = {}
    for field in fields:
        item = getattr(value, field, None)
        if item is not None:
            payload[field] = _wire_value(item)
    return payload


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
        knowledge_view: Optional[KnowledgeReadView] = None,
        machine_verification: Optional[Mapping[str, Mapping[str, Any]]] = None,
    ):
        if isinstance(limit, bool) or not isinstance(limit, int) or limit < 1:
            raise DocumentationQueryError("limit must be a positive integer.")

        self.limit = limit
        self.inventory = {
            _normalise_source_path(path, field="inventory path", required=False)
            or str(path).replace("\\", "/"): dict(data or {})
            for path, data in (inventory or {}).items()
        }
        self.call_edges = _jsonable_mapping_list(call_edges or [])
        self.flows = _jsonable_mapping_list(flows or [])
        self.data_flows = self._normalise_data_flows(data_flows)
        self.dependency = self._dependency_payload(dependency_analysis)
        self.pages = self._surface_pages(surface_index or {})
        if machine_verification is None:
            self.machine_verification: dict[str, dict[str, Any]] = {}
        elif not isinstance(machine_verification, Mapping):
            raise DocumentationQueryError(
                "machine_verification must be a mapping keyed by concept coordinate."
            )
        else:
            try:
                self.machine_verification = {
                    str(uid): _jsonable_mapping(summary)
                    for uid, summary in machine_verification.items()
                }
            except (TypeError, ValueError) as exc:
                raise DocumentationQueryError(
                    f"machine_verification is invalid: {exc}"
                ) from exc

        relationships = build_entity_relationship_summaries(
            self.inventory,
            call_edges=self.call_edges,
            flows=self.flows,
        )
        relationship_functions = cast(
            Iterable[Mapping[str, Any]], relationships.get("functions", [])
        )
        relationship_classes = cast(
            Iterable[Mapping[str, Any]], relationships.get("classes", [])
        )
        self.callable_summaries = _jsonable_mapping_list(relationship_functions)
        self.class_summaries = _jsonable_mapping_list(relationship_classes)
        self.callables = [_callable_ref(summary) for summary in self.callable_summaries]
        self.classes = [_class_ref(summary) for summary in self.class_summaries]
        self.callable_by_key = {
            (summary.get("file"), summary.get("symbol")): summary
            for summary in self.callable_summaries
        }
        self.raw_callers, self.raw_callees = self._raw_function_links()
        self._build_graph_query_indexes()
        self._build_knowledge_indexes(knowledge_view)

    def flow_for_entrypoint(self, id_or_symbol: object) -> dict[str, Any]:
        """Return a bounded user-flow payload for an entry-point id or symbol."""
        query = _require_query(id_or_symbol, "id_or_symbol")
        matches = self._flow_matches(query, self._flows_by_identifier)
        result = self._selection_result(query, matches, "flow", None)
        if not result["found"]:
            result["flow"] = None
            self._record_bound(result, "flow.steps", self._bounded(()))
            return result

        flow, bounds = self._bounded_payload(result.pop("_selected"), ("steps",))
        result["flow"] = flow
        for path, bounded in bounds.items():
            self._record_bound(result, f"flow.{path}", bounded)
        return result

    def callers(self, symbol: object) -> dict[str, Any]:
        """Return bounded callers for exactly one callable symbol."""
        query = _require_query(symbol, "symbol")
        matches = self._callable_matches(query)
        result = self._selection_result(query, matches, "callable", None)
        if not result["found"]:
            result["callable"] = None
            result["callers"] = []
            self._record_bound(result, "callers", self._bounded(()))
            return result

        selected = result.pop("_selected")
        summary = self.callable_by_key[(selected.get("file"), selected.get("symbol"))]
        key = (selected.get("file"), selected.get("symbol"))
        caller_records = self.raw_callers.get(key)
        if caller_records is None:
            caller_records = _summary_relationship_records(summary, "callers")
        callers = self._bounded(caller_records)
        result["callable"] = selected
        result["callers"] = callers.items
        self._record_bound(result, "callers", callers)
        return result

    def callees(self, symbol: object) -> dict[str, Any]:
        """Return bounded callees for exactly one callable symbol."""
        query = _require_query(symbol, "symbol")
        matches = self._callable_matches(query)
        result = self._selection_result(query, matches, "callable", None)
        if not result["found"]:
            result["callable"] = None
            result["callees"] = []
            self._record_bound(result, "callees", self._bounded(()))
            return result

        selected = result.pop("_selected")
        summary = self.callable_by_key[(selected.get("file"), selected.get("symbol"))]
        key = (selected.get("file"), selected.get("symbol"))
        callee_records = self.raw_callees.get(key)
        if callee_records is None:
            callee_records = _summary_relationship_records(summary, "callees")
        callees = self._bounded(callee_records)
        result["callable"] = selected
        result["callees"] = callees.items
        self._record_bound(result, "callees", callees)
        return result

    def dependency_neighborhood(self, path: object) -> dict[str, Any]:
        """Return bounded inbound/outbound dependency neighbors for a source path."""
        query = cast(
            str,
            _normalise_source_path(path, field="path", required=True),
        )
        empty_bounds = {
            response_path: self._bounded(())
            for response_path in (
                "matches",
                "inbound",
                "outbound",
                "cycle_groups",
                "pages",
            )
        }
        empty: dict[str, Any] = {
            "query": query,
            "found": False,
            "ambiguous": False,
            "matches": [],
            "truncated": False,
            "bounds": {
                path: bounded.metadata() for path, bounded in empty_bounds.items()
            },
            "path": None,
            "inbound": [],
            "outbound": [],
            "metrics": {"fan_in": 0, "fan_out": 0},
            "cycle_groups": [],
            "load_order_index": None,
            "pages": [],
        }
        if query not in self._dependency_nodes:
            return empty

        inbound = self._bounded_strings(self._dependency_inbound.get(query, ()))
        outbound = self._bounded_strings(self._dependency_outbound.get(query, ()))
        pages = self._pages_for_source(query)
        metrics = (
            self.dependency.get("metrics", {})
            .get("metrics", {})
            .get(query, {"fan_in": 0, "fan_out": 0})
        )
        cycle_groups = self._bounded(self._dependency_cycles_by_path.get(query, ()))
        match_bounds = self._bounded(({"path": query},))
        bounds = {
            "matches": match_bounds.metadata(),
            "inbound": inbound.metadata(),
            "outbound": outbound.metadata(),
            "cycle_groups": cycle_groups.metadata(),
            "pages": pages.metadata(),
        }

        return {
            "query": query,
            "found": True,
            "ambiguous": False,
            "matches": match_bounds.items,
            "truncated": any(bound["truncated"] for bound in bounds.values()),
            "bounds": bounds,
            "path": query,
            "inbound": inbound.items,
            "outbound": outbound.items,
            "metrics": dict(metrics),
            "cycle_groups": cycle_groups.items,
            "load_order_index": self._dependency_order_index.get(query),
            "pages": pages.items,
        }

    def data_flow_for_entrypoint(self, id_or_symbol: object) -> dict[str, Any]:
        """Return a bounded data-flow payload for an entry-point id or symbol."""
        query = _require_query(id_or_symbol, "id_or_symbol")
        matches = self._flow_matches(query, self._data_flows_by_identifier)
        result = self._selection_result(query, matches, "data_flow", None)
        if not result["found"]:
            result["data_flow"] = None
            for key in ("steps", "transfers", "boundaries", "gaps"):
                self._record_bound(
                    result,
                    f"data_flow.{key}",
                    self._bounded(()),
                )
            return result

        data_flow, bounds = self._bounded_payload(
            result.pop("_selected"),
            ("steps", "transfers", "boundaries", "gaps"),
        )
        result["data_flow"] = data_flow
        for path, bounded in bounds.items():
            self._record_bound(result, f"data_flow.{path}", bounded)
        return result

    def pages_for_symbol(self, symbol: object) -> dict[str, Any]:
        """Return bounded wiki surface pages related to exactly one symbol."""
        query = _require_query(symbol, "symbol")
        matches = self._symbol_matches(query)
        result = self._selection_result(query, matches, "symbol", None)
        if not result["found"]:
            result["symbol"] = None
            result["pages"] = []
            self._record_bound(result, "pages", self._bounded(()))
            return result

        selected = result.pop("_selected")
        pages = self._pages_for_source(selected.get("file"))
        result["symbol"] = selected
        result["pages"] = pages.items
        self._record_bound(result, "pages", pages)
        return result

    def get_concept(self, locator_or_exact_route: object) -> dict[str, Any]:
        """Return one concept selected by current coordinate, UID, or alias."""

        query = _require_query(locator_or_exact_route, "locator_or_exact_route")
        result = self._knowledge_selection_result(query)
        locator = result.pop("_selected_locator", None)
        result["concept"] = (
            None if locator is None else self._compact_knowledge_concept(locator)
        )
        return result

    def related_concepts(
        self,
        locator_or_exact_route: object,
        *,
        direction: str = "both",
        kinds: Optional[Iterable[str]] = None,
    ) -> dict[str, Any]:
        """Return bounded relationship observations for one exact identity."""

        query = _require_query(locator_or_exact_route, "locator_or_exact_route")
        selected_direction = self._knowledge_direction(direction)
        selected_kinds = self._knowledge_kinds(kinds)
        result = self._knowledge_selection_result(query)
        locator = result.pop("_selected_locator", None)
        result.update(
            {
                "concept": (
                    None
                    if locator is None
                    else self._compact_knowledge_concept(locator)
                ),
                "direction": selected_direction,
                "kinds": list(selected_kinds),
                "relationships": [],
                "related_concepts": [],
                "unresolved_targets": [],
                "external_targets": [],
            }
        )
        relationship_bounds = self._bounded(())
        self._record_bound(result, "relationships", relationship_bounds)
        if locator is None:
            result.update({"total": 0, "returned": 0, "truncated": False})
            self._sync_truncated(result)
            return result

        observations = [
            item
            for item in self._incident_knowledge_relationships(
                locator,
                selected_direction,
            )
            if self._knowledge_relationship_kinds[item[0]] in selected_kinds
        ]
        bounded_observations = self._bounded(observations)
        returned = bounded_observations.items
        compact_relationships = [
            self._compact_knowledge_relationship(
                cast(int, index),
                cast(str, edge_direction),
            )
            for index, edge_direction in returned
        ]

        related_by_locator: dict[str, dict[str, Any]] = {}
        unresolved_targets: list[dict[str, Any]] = []
        external_targets: list[dict[str, Any]] = []
        for relationship in compact_relationships:
            related = relationship.get("related_concept")
            if isinstance(related, Mapping):
                related_locator = related.get("locator")
                if isinstance(related_locator, str):
                    related_by_locator[related_locator] = _jsonable_mapping(related)

            target_summary = {
                "kind": relationship["kind"],
                "resolution": relationship["resolution"],
                "target": _jsonable(relationship["target"]),
            }
            if relationship["resolution"] in {"ambiguous", "unresolved"}:
                unresolved_targets.append(target_summary)
            if relationship["resolution"] == "external":
                external_targets.append(target_summary)

        result.update(
            {
                "relationships": compact_relationships,
                "related_concepts": [
                    related_by_locator[key] for key in sorted(related_by_locator)
                ],
                "unresolved_targets": unresolved_targets,
                "external_targets": external_targets,
                "total": bounded_observations.total,
                "returned": bounded_observations.returned,
            }
        )
        self._record_bound(result, "relationships", bounded_observations)
        return result

    def list_concept_sections(
        self,
        locator_or_exact_route: object,
        *,
        ownership: str | None = None,
    ) -> dict[str, Any]:
        """Return bounded document-order sections for one exact concept.

        Unavailable native knowledge or section ownership is reported
        explicitly and returns an empty, non-truncated section collection.
        """

        query = _require_query(locator_or_exact_route, "locator_or_exact_route")
        selected_ownership = self._section_ownership_filter(ownership)
        result = self._knowledge_selection_result(query)
        locator = result.pop("_selected_locator", None)
        result.update(
            {
                "section_ownership": _jsonable_mapping(
                    self.section_ownership_status
                ),
                "concept": (
                    None
                    if locator is None
                    else self._compact_knowledge_concept(locator)
                ),
                "ownership": selected_ownership,
                "sections": [],
            }
        )
        section_bounds = _BoundedResult(items=[], total=0)
        self._record_bound(result, "sections", section_bounds)
        if (
            locator is None
            or self.section_ownership_status["availability"]
            != KnowledgeAvailability.READY.value
        ):
            result.update({"total": 0, "returned": 0})
            self._sync_truncated(result)
            return result

        sections = [
            section
            for section in self.sections_by_page_locator.get(locator, ())
            if selected_ownership is None
            or section.get("ownership") == selected_ownership
        ]
        compact_sections = [
            self._compact_section(locator, section)
            for section in sections[: self.limit]
        ]
        section_bounds = _BoundedResult(
            items=compact_sections,
            total=len(sections),
        )
        result.update(
            {
                "sections": compact_sections,
                "total": section_bounds.total,
                "returned": section_bounds.returned,
            }
        )
        self._record_bound(result, "sections", section_bounds)
        return result

    def traverse_typed_graph(
        self,
        locator_or_exact_route: object,
        *,
        direction: str = "both",
        kinds: Optional[Iterable[str]] = None,
        origins: Optional[Iterable[str]] = None,
        resolutions: Optional[Iterable[str]] = None,
        include_evidence: bool = False,
    ) -> dict[str, Any]:
        """Return a bounded traversal of the persisted typed-graph extension.

        Response bounds describe only this query.  Per-edge and analyzer
        coverage continue to describe upstream graph materialization, so a
        response cap can never be confused with omitted analyzer evidence.
        """

        query = _require_query(locator_or_exact_route, "locator_or_exact_route")
        selected_direction = self._typed_graph_direction(direction)
        selected_kinds = self._typed_graph_kinds(kinds)
        selected_origins = self._typed_graph_enum_filter(
            origins,
            field="origins",
            allowed=GRAPH_ORIGINS,
        )
        selected_resolutions = self._typed_graph_enum_filter(
            resolutions,
            field="resolutions",
            allowed=GRAPH_RESOLUTIONS,
        )
        if not isinstance(include_evidence, bool):
            raise DocumentationQueryError("include_evidence must be a boolean.")

        result = self._knowledge_selection_result(query)
        locator = result.pop("_selected_locator", None)
        result.update(
            {
                "typed_graph": _jsonable_mapping(self.typed_graph_status),
                "concept": (
                    None
                    if locator is None
                    else self._compact_knowledge_concept(locator)
                ),
                "direction": selected_direction,
                "kinds": list(selected_kinds),
                "origins": list(selected_origins),
                "resolutions": list(selected_resolutions),
                "include_evidence": include_evidence,
                "edges": [],
            }
        )
        bounded_edges = self._bounded(())
        self._record_bound(result, "edges", bounded_edges)
        if (
            locator is None
            or self.typed_graph_status["availability"]
            != KnowledgeAvailability.READY.value
        ):
            result.update({"total": 0, "returned": 0})
            self._sync_truncated(result)
            return result

        incidents = [
            item
            for item in self._incident_typed_graph_edges(
                cast(str, locator),
                selected_direction,
            )
            if self._typed_graph_edge_kinds[item[0]] in selected_kinds
            and self._typed_graph_edge_origins[item[0]] in selected_origins
            and self._typed_graph_edge_resolutions[item[0]]
            in selected_resolutions
        ]
        bounded_edges = self._bounded(incidents)
        compact_edges = [
            self._compact_typed_graph_edge(
                cast(int, index),
                cast(str, edge_direction),
                include_evidence=include_evidence,
            )
            for index, edge_direction in bounded_edges.items
        ]
        result.update(
            {
                "edges": compact_edges,
                "total": bounded_edges.total,
                "returned": bounded_edges.returned,
            }
        )
        self._record_bound(
            result,
            "edges",
            _BoundedResult(items=compact_edges, total=bounded_edges.total),
        )
        return result

    def explain_evidence(
        self,
        locator_or_exact_route: object,
    ) -> dict[str, Any]:
        """Return full stored and computed evidence for one exact identity."""

        query = _require_query(locator_or_exact_route, "locator_or_exact_route")
        result = self._knowledge_selection_result(query)
        locator = result.pop("_selected_locator", None)
        result["concept"] = (
            None if locator is None else self._compact_knowledge_concept(locator)
        )
        result["evidence"] = None
        relationship_bounds = self._bounded(())
        self._record_bound(result, "evidence.relationships", relationship_bounds)
        if locator is None:
            result.update({"total": 0, "returned": 0, "truncated": False})
            self._sync_truncated(result)
            return result

        concept = self.concept_by_locator[locator]
        observations = [
            item
            for item in self._incident_knowledge_relationships(locator, "both")
            if self._knowledge_relationship_kinds[item[0]]
            in _KNOWLEDGE_RELATIONSHIP_KINDS
        ]
        bounded_observations = self._bounded(observations)
        returned = bounded_observations.items
        relationships = []
        for index, edge_direction in returned:
            relationship = _jsonable_mapping(
                self._knowledge_relationships[cast(int, index)]
            )
            relationship["direction"] = edge_direction
            relationships.append(relationship)

        facets = cast(Mapping[str, Any], concept.get("facets", {}))
        result.update(
            {
                "evidence": {
                    "structure": _jsonable(facets.get("structure", {})),
                    "semantics": _jsonable(facets.get("semantics", {})),
                    "freshness": self._full_knowledge_freshness(locator),
                    "relationships": relationships,
                },
                "total": bounded_observations.total,
                "returned": bounded_observations.returned,
            }
        )
        self._record_bound(
            result,
            "evidence.relationships",
            bounded_observations,
        )
        return result

    def _build_knowledge_indexes(
        self,
        knowledge_view: Optional[KnowledgeReadView],
    ) -> None:
        self.knowledge_view = knowledge_view
        self.concept_by_locator: dict[str, dict[str, Any]] = {}
        self.concept_by_canonical_path: dict[str, dict[str, Any]] = {}
        self.concept_by_mcp_uri: dict[str, dict[str, Any]] = {}
        self.concept_by_uid: dict[str, dict[str, Any]] = {}
        self.concept_by_alias: dict[str, dict[str, Any]] = {}
        self.concepts_by_source_path: dict[
            str, tuple[dict[str, Any], ...]
        ] = {}
        self.relationships_by_source_path: dict[str, tuple[int, ...]] = {}
        self.outbound_relationships: dict[str, tuple[int, ...]] = {}
        self.inbound_relationships: dict[str, tuple[int, ...]] = {}
        self._knowledge_relationships: tuple[dict[str, Any], ...] = ()
        self._knowledge_relationship_kinds: tuple[object, ...] = ()
        self._knowledge_relationship_order: tuple[int, ...] = ()
        self._knowledge_target_locators: tuple[Optional[str], ...] = ()
        self.section_ownership_status: dict[str, Any] = {
            "availability": KnowledgeAvailability.ABSENT.value,
            "reason": KnowledgeReadReason.ABSENT.value,
            "schema_version": None,
        }
        self.sections_by_page_locator: dict[
            str, tuple[dict[str, Any], ...]
        ] = {}
        self.typed_graph_status: dict[str, Any] = {
            "availability": KnowledgeAvailability.ABSENT.value,
            "reason": KnowledgeReadReason.ABSENT.value,
            "schema_version": None,
            "coverage": [],
        }
        self._typed_graph_edges: tuple[dict[str, Any], ...] = ()
        self._typed_graph_edge_kinds: tuple[object, ...] = ()
        self._typed_graph_edge_origins: tuple[object, ...] = ()
        self._typed_graph_edge_resolutions: tuple[object, ...] = ()
        self._typed_graph_target_locators: tuple[Optional[str], ...] = ()
        self._typed_graph_edge_order: tuple[int, ...] = ()
        self.outgoing_typed_graph_edges: dict[str, tuple[int, ...]] = {}
        self.incoming_typed_graph_edges: dict[str, tuple[int, ...]] = {}

        if knowledge_view is None:
            self.knowledge_status = knowledge_status_payload(None)
            return
        if not isinstance(knowledge_view, KnowledgeReadView):
            raise DocumentationQueryError(
                "knowledge_view must be a KnowledgeReadView or None."
            )
        if not isinstance(knowledge_view.availability, KnowledgeAvailability):
            raise DocumentationQueryError(
                "knowledge_view.availability must be a KnowledgeAvailability."
            )
        if not isinstance(knowledge_view.reason, KnowledgeReadReason):
            raise DocumentationQueryError(
                "knowledge_view.reason must be a KnowledgeReadReason."
            )

        self.knowledge_status = knowledge_status_payload(knowledge_view)
        if knowledge_view.availability is not KnowledgeAvailability.READY:
            self.section_ownership_status.update(
                {
                    "availability": knowledge_view.availability.value,
                    "reason": knowledge_view.reason_code,
                }
            )
            self.typed_graph_status.update(
                {
                    "availability": knowledge_view.availability.value,
                    "reason": knowledge_view.reason_code,
                }
            )
            if knowledge_view.knowledge is not None:
                raise DocumentationQueryError(
                    "a non-ready knowledge_view must not expose knowledge."
                )
            return
        if knowledge_view.knowledge is None:
            raise DocumentationQueryError(
                "a ready knowledge_view must contain validated knowledge."
            )

        try:
            payload = knowledge_index_to_payload(knowledge_view.knowledge)
        except (TypeError, ValueError) as exc:
            raise DocumentationQueryError(
                f"knowledge_view.knowledge is invalid: {exc}"
            ) from exc

        concepts = [
            _jsonable_mapping(cast(Mapping[str, Any], concept))
            for concept in payload["concepts"]
        ]
        source_concepts: dict[str, dict[str, dict[str, Any]]] = defaultdict(dict)
        for concept in concepts:
            locator = cast(str, concept["locator"])
            document = cast(Mapping[str, Any], concept["document"])
            canonical_path = cast(str, document["canonical_path"])
            self.concept_by_locator[locator] = concept
            self.concept_by_mcp_uri[locator] = concept
            self.concept_by_canonical_path[canonical_path] = concept

            extensions = concept.get("extensions", {})
            governance = (
                extensions.get(GOVERNANCE_EXTENSION_KEY)
                if isinstance(extensions, Mapping)
                else None
            )
            if isinstance(governance, Mapping):
                uid = governance.get("uid")
                if isinstance(uid, str):
                    self.concept_by_uid[uid] = concept
                aliases = governance.get("aliases", ())
                if isinstance(aliases, list):
                    for alias in aliases:
                        if not isinstance(alias, Mapping):
                            continue
                        alias_value = alias.get("value")
                        if isinstance(alias_value, str):
                            self.concept_by_alias[alias_value] = concept

            facets = cast(Mapping[str, Any], concept.get("facets", {}))
            structure = cast(Mapping[str, Any], facets.get("structure", {}))
            basis = structure.get("basis")
            if isinstance(basis, Mapping):
                source_path = basis.get("source_path")
                if isinstance(source_path, str):
                    source_concepts[source_path][locator] = concept

        relationships = tuple(
            _jsonable_mapping(cast(Mapping[str, Any], relationship))
            for relationship in payload["relationships"]
        )
        outbound: dict[str, list[int]] = defaultdict(list)
        inbound: dict[str, list[int]] = defaultdict(list)
        relationships_by_source: dict[str, list[int]] = defaultdict(list)
        target_locators: list[Optional[str]] = []
        for index, relationship in enumerate(relationships):
            target_locators.append(None)
            source_locator = relationship.get("from")
            if isinstance(source_locator, str):
                outbound[source_locator].append(index)

            target = relationship.get("target")
            if not isinstance(target, Mapping):
                continue
            source_path = target.get("source_path")
            if (
                relationship.get("kind") == "derived_from"
                and isinstance(source_locator, str)
                and isinstance(source_path, str)
            ):
                relationships_by_source[source_path].append(index)
                source_concept = self.concept_by_locator.get(source_locator)
                if source_concept is not None:
                    source_concepts[source_path][source_locator] = source_concept

            target_locator = self._resolved_target_locator(relationship)
            target_locators[-1] = target_locator
            if target_locator is not None:
                inbound[target_locator].append(index)

        self._knowledge_relationships = relationships
        kind_order = {
            kind: index for index, kind in enumerate(_KNOWLEDGE_RELATIONSHIP_KINDS)
        }
        self._knowledge_relationship_kinds = tuple(
            relationship.get("kind") for relationship in relationships
        )
        relationship_sort_keys = tuple(
            (
                kind_order.get(
                    cast(str, relationship.get("kind")),
                    len(kind_order),
                ),
                str(relationship.get("from", "")),
                str(relationship.get("resolution", "")),
                _canonical_json(relationship),
                index,
            )
            for index, relationship in enumerate(relationships)
        )
        relationship_order = [0] * len(relationships)
        for rank, index in enumerate(
            sorted(range(len(relationships)), key=relationship_sort_keys.__getitem__)
        ):
            relationship_order[index] = rank
        self._knowledge_relationship_order = tuple(relationship_order)
        self._knowledge_target_locators = tuple(target_locators)
        self.outbound_relationships = {
            locator: tuple(
                sorted(
                    indexes,
                    key=self._knowledge_relationship_order.__getitem__,
                )
            )
            for locator, indexes in sorted(outbound.items())
        }
        self.inbound_relationships = {
            locator: tuple(
                sorted(
                    indexes,
                    key=self._knowledge_relationship_order.__getitem__,
                )
            )
            for locator, indexes in sorted(inbound.items())
        }
        self.relationships_by_source_path = {
            source_path: tuple(indexes)
            for source_path, indexes in sorted(relationships_by_source.items())
        }
        self.concepts_by_source_path = {
            source_path: tuple(
                by_locator[locator] for locator in sorted(by_locator)
            )
            for source_path, by_locator in sorted(source_concepts.items())
        }
        self._build_section_ownership_indexes(payload)
        self._build_typed_graph_indexes(payload)

    def _build_section_ownership_indexes(
        self,
        payload: Mapping[str, Any],
    ) -> None:
        extensions = payload.get("extensions", {})
        if not isinstance(extensions, Mapping):
            raise DocumentationQueryError(
                "knowledge extensions must be an object."
            )
        extension = extensions.get(SECTION_OWNERSHIP_EXTENSION_KEY)
        if extension is None:
            self.section_ownership_status = {
                "availability": KnowledgeAvailability.ABSENT.value,
                "reason": _SECTION_OWNERSHIP_ABSENT_REASON,
                "schema_version": None,
            }
            return
        if not isinstance(extension, Mapping):
            raise DocumentationQueryError(
                "section ownership extension must be an object."
            )

        pages = extension.get("pages", ())
        if not isinstance(pages, list):
            raise DocumentationQueryError(
                "section ownership extension pages must be an array."
            )
        indexed: dict[str, tuple[dict[str, Any], ...]] = {}
        for page in pages:
            if not isinstance(page, Mapping):
                raise DocumentationQueryError(
                    "section ownership extension pages must contain objects."
                )
            page_locator = page.get("page_locator")
            raw_sections = page.get("sections", ())
            if not isinstance(page_locator, str) or not isinstance(
                raw_sections, list
            ):
                raise DocumentationQueryError(
                    "section ownership extension page is invalid."
                )
            sections = [
                _jsonable_mapping(cast(Mapping[str, Any], section))
                for section in raw_sections
                if isinstance(section, Mapping)
            ]
            if len(sections) != len(raw_sections):
                raise DocumentationQueryError(
                    "section ownership extension sections must contain objects."
                )
            sections.sort(
                key=lambda section: (
                    cast(int, section.get("ordinal", 0)),
                    str(section.get("locator", "")),
                )
            )
            indexed[page_locator] = tuple(sections)

        self.sections_by_page_locator = {
            locator: indexed[locator] for locator in sorted(indexed)
        }
        self.section_ownership_status = {
            "availability": KnowledgeAvailability.READY.value,
            "reason": _SECTION_OWNERSHIP_READY_REASON,
            "schema_version": extension.get("schema_version"),
        }

    def _build_typed_graph_indexes(self, payload: Mapping[str, Any]) -> None:
        extensions = payload.get("extensions", {})
        if not isinstance(extensions, Mapping):
            raise DocumentationQueryError(
                "knowledge extensions must be an object."
            )
        try:
            graph = typed_graph_from_knowledge_extensions(
                extensions,
                concept_kinds={
                    locator: cast(str, concept.get("concept_kind"))
                    for locator, concept in self.concept_by_locator.items()
                },
            )
        except KnowledgeGraphError as exc:
            raise DocumentationQueryError(
                f"typed graph extension is invalid: {exc}"
            ) from exc
        if graph is None:
            self.typed_graph_status = {
                "availability": KnowledgeAvailability.ABSENT.value,
                "reason": _TYPED_GRAPH_ABSENT_REASON,
                "schema_version": None,
                "coverage": [],
            }
            return

        edges = tuple(
            _jsonable_mapping(cast(Mapping[str, Any], edge))
            for edge in graph["edges"]
        )
        outgoing: dict[str, list[int]] = defaultdict(list)
        incoming: dict[str, list[int]] = defaultdict(list)
        target_locators: list[Optional[str]] = []
        for index, edge in enumerate(edges):
            source = edge.get("from")
            source_locator = self._typed_graph_concept_locator(source)
            if (
                isinstance(source_locator, str)
                and source_locator in self.concept_by_locator
            ):
                outgoing[source_locator].append(index)

            target = edge.get("target")
            target_locator = self._typed_graph_concept_locator(target)
            if not (
                isinstance(target_locator, str)
                and target_locator in self.concept_by_locator
            ):
                target_locator = None
            target_locators.append(target_locator)
            if target_locator is not None:
                incoming[target_locator].append(index)

        # The extension validator canonicalizes by edge key.  Retaining an
        # explicit rank lets every query use the constructor-built index only.
        edge_order = tuple(range(len(edges)))
        self._typed_graph_edges = edges
        self._typed_graph_edge_kinds = tuple(
            edge.get("kind") for edge in edges
        )
        self._typed_graph_edge_origins = tuple(
            edge.get("origin") for edge in edges
        )
        self._typed_graph_edge_resolutions = tuple(
            edge.get("resolution") for edge in edges
        )
        self._typed_graph_target_locators = tuple(target_locators)
        self._typed_graph_edge_order = edge_order
        self.outgoing_typed_graph_edges = {
            locator: tuple(sorted(indexes, key=edge_order.__getitem__))
            for locator, indexes in sorted(outgoing.items())
        }
        self.incoming_typed_graph_edges = {
            locator: tuple(sorted(indexes, key=edge_order.__getitem__))
            for locator, indexes in sorted(incoming.items())
        }
        self.typed_graph_status = {
            "availability": KnowledgeAvailability.READY.value,
            "reason": _TYPED_GRAPH_READY_REASON,
            "schema_version": graph["schema_version"],
            "coverage": _jsonable(graph["coverage"]),
        }

    def _typed_graph_concept_locator(self, endpoint: object) -> str | None:
        """Resolve a locator- or durable-UID concept endpoint."""

        if not isinstance(endpoint, Mapping) or endpoint.get("kind") != "concept":
            return None
        locator = endpoint.get("locator")
        if isinstance(locator, str):
            return locator
        uid = endpoint.get("uid")
        if not isinstance(uid, str):
            return None
        concept = self.concept_by_uid.get(uid)
        if concept is None:
            return None
        selected = concept.get("locator")
        return selected if isinstance(selected, str) else None

    def _knowledge_selection_result(self, query: str) -> dict[str, Any]:
        candidates: tuple[dict[str, Any], ...] = ()
        if self.knowledge_status["availability"] == KnowledgeAvailability.READY.value:
            matches_by_locator: dict[str, dict[str, Any]] = {}
            for index in (
                self.concept_by_locator,
                self.concept_by_mcp_uri,
                self.concept_by_canonical_path,
                self.concept_by_uid,
                self.concept_by_alias,
            ):
                direct = index.get(query)
                if direct is not None:
                    matches_by_locator[cast(str, direct["locator"])] = direct
            candidates = tuple(
                matches_by_locator[locator]
                for locator in sorted(matches_by_locator)
            )

        total = len(candidates)
        capped = candidates[: self.limit]
        matches = [
            self._compact_knowledge_concept(cast(str, concept["locator"]))
            for concept in capped
        ]
        match_bounds = _BoundedResult(items=matches, total=total)
        result: dict[str, Any] = {
            "knowledge": dict(self.knowledge_status),
            "query": query,
            "found": total == 1,
            "ambiguous": total > 1,
            "matches": matches,
            "total": total,
            "returned": match_bounds.returned,
            "truncated": match_bounds.truncated,
            "bounds": {"matches": match_bounds.metadata()},
        }
        selected = next(iter(candidates), None)
        if total == 1 and selected is not None:
            result["_selected_locator"] = selected["locator"]
        return result

    def _compact_knowledge_concept(self, locator: str) -> dict[str, Any]:
        concept = self.concept_by_locator[locator]
        document = cast(Mapping[str, Any], concept["document"])
        facets = cast(Mapping[str, Any], concept.get("facets", {}))
        structure = cast(Mapping[str, Any], facets.get("structure", {}))
        semantics = cast(Mapping[str, Any], facets.get("semantics", {}))
        basis = structure.get("basis")
        source_path = (
            basis.get("source_path") if isinstance(basis, Mapping) else None
        )
        result = {
            "locator": locator,
            "concept_kind": concept.get("concept_kind"),
            "title": concept.get("title"),
            "page_kind": document.get("page_kind"),
            "page_id": document.get("page_id"),
            "canonical_path": document.get("canonical_path"),
            "mcp_uri": locator,
            "source_path": source_path,
            "role": document.get("role"),
            "origin": structure.get("origin"),
            "evidence": structure.get("evidence"),
            "verification": semantics.get("verification"),
            "lifecycle": concept.get("lifecycle"),
            "freshness": self._compact_knowledge_freshness(locator),
        }
        extensions = concept.get("extensions", {})
        governance = (
            extensions.get(GOVERNANCE_EXTENSION_KEY)
            if isinstance(extensions, Mapping)
            else None
        )
        if isinstance(governance, Mapping):
            uid = governance.get("uid")
            raw_aliases = governance.get("aliases", [])
            aliases = self._bounded(
                raw_aliases if isinstance(raw_aliases, list) else ()
            )
            result.update(
                {
                    "uid": uid,
                    "aliases": aliases.items,
                    "alias_coverage": aliases.metadata(),
                    "lifecycle_events": _jsonable(
                        governance.get("lifecycle_events", {})
                    ),
                    "reviews": _jsonable(governance.get("reviews", {})),
                    "machine_verification": (
                        None
                        if not isinstance(uid, str)
                        else _jsonable(
                            self.machine_verification.get(
                                uid,
                                self.machine_verification.get(locator),
                            )
                        )
                    ),
                }
            )
            successor_uid = governance.get("successor_uid")
            if isinstance(successor_uid, str):
                result["successor_uid"] = successor_uid
        elif locator in self.machine_verification:
            result["machine_verification"] = _jsonable(
                self.machine_verification[locator]
            )
        return result

    def _compact_section(
        self,
        concept_locator: str,
        section: Mapping[str, Any],
    ) -> dict[str, Any]:
        """Project one section without raw hashes or review authorship."""

        result = {
            "locator": section.get("locator"),
            "page_locator": section.get("page_locator"),
            "heading_path": _jsonable(section.get("heading_path", [])),
            "title": section.get("title"),
            "level": section.get("level"),
            "occurrence": section.get("occurrence"),
            "ordinal": section.get("ordinal"),
            "parent_locator": section.get("parent_locator"),
            "ownership": section.get("ownership"),
            "review": self._compact_section_review(
                concept_locator,
                str(section.get("locator", "")),
            ),
        }
        if "occurrence_path" in section:
            result["occurrence_path"] = _jsonable(
                section.get("occurrence_path")
            )
        return result

    def _compact_section_review(
        self,
        concept_locator: str,
        section_locator: str,
    ) -> dict[str, Any]:
        concept = self.concept_by_locator[concept_locator]
        extensions = concept.get("extensions", {})
        governance = (
            extensions.get(GOVERNANCE_EXTENSION_KEY)
            if isinstance(extensions, Mapping)
            else None
        )
        if not isinstance(governance, Mapping):
            return {
                "state": "unknown",
                "reasons": ["governance-not-available"],
                "history_truncated": False,
            }

        reviews = governance.get("reviews", {})
        if not isinstance(reviews, Mapping):
            return {
                "state": "unknown",
                "reasons": ["governance-not-available"],
                "history_truncated": False,
            }
        history_truncated = bool(reviews.get("truncated"))
        items = reviews.get("items", ())
        if isinstance(items, list):
            matching = [
                item
                for item in items
                if isinstance(item, Mapping)
                and item.get("section_locator") == section_locator
            ]
            if matching:
                latest = matching[-1]
                state = latest.get("state")
                raw_reasons = latest.get("reasons", ())
                return {
                    "state": (
                        state
                        if isinstance(state, str)
                        else "unknown"
                    ),
                    "reasons": (
                        [
                            reason
                            for reason in raw_reasons
                            if isinstance(reason, str)
                        ]
                        if isinstance(raw_reasons, list)
                        else []
                    ),
                    "history_truncated": history_truncated,
                }
        if history_truncated:
            return {
                "state": "unknown",
                "reasons": ["review-history-truncated"],
                "history_truncated": True,
            }
        return {
            "state": "not-reviewed",
            "reasons": [],
            "history_truncated": False,
        }

    def _compact_knowledge_freshness(self, locator: str) -> dict[str, Any]:
        view = self.knowledge_view
        if view is None or view.freshness is None:
            return {
                "state": None,
                "reason": _NOT_EVALUATED_REASON,
                "live_comparison_performed": False,
            }
        freshness = view.freshness.by_locator.get(locator)
        if freshness is None:
            return {
                "state": None,
                "reason": _NOT_EVALUATED_REASON,
                "live_comparison_performed": False,
            }
        result = {
            "state": _wire_value(freshness.state),
            "reason": freshness.reason_code,
            "live_comparison_performed": freshness.live_comparison_performed,
        }
        hint = knowledge_freshness_hint(
            freshness.state,
            freshness.reason_code,
        )
        if hint is not None:
            result["hint"] = hint
        return result

    def _full_knowledge_freshness(self, locator: str) -> Optional[dict[str, Any]]:
        view = self.knowledge_view
        if view is None or view.freshness is None:
            return None
        freshness = view.freshness.by_locator.get(locator)
        if freshness is None:
            return None
        result = {
            "state": _wire_value(freshness.state),
            "reason": freshness.reason_code,
            "description": freshness.description,
            "live_comparison_performed": freshness.live_comparison_performed,
            "recorded_basis": _freshness_basis_payload(
                freshness.recorded_basis
            ),
            "live_basis": _freshness_basis_payload(freshness.live_basis),
        }
        hint = knowledge_freshness_hint(
            freshness.state,
            freshness.reason_code,
        )
        if hint is not None:
            result["hint"] = hint
        return result

    def _knowledge_direction(self, value: object) -> str:
        if not isinstance(value, str) or value not in _KNOWLEDGE_DIRECTIONS:
            choices = ", ".join(repr(item) for item in _KNOWLEDGE_DIRECTIONS)
            raise DocumentationQueryError(f"direction must be one of {choices}.")
        return value

    def _section_ownership_filter(self, value: object) -> str | None:
        if value is None:
            return None
        if not isinstance(value, str) or value not in _SECTION_OWNERSHIP_VALUES:
            choices = ", ".join(repr(item) for item in _SECTION_OWNERSHIP_VALUES)
            raise DocumentationQueryError(
                f"ownership must be one of {choices}, or None."
            )
        return value

    def _knowledge_kinds(
        self,
        values: Optional[Iterable[str]],
    ) -> tuple[str, ...]:
        if values is None:
            return _KNOWLEDGE_RELATIONSHIP_KINDS
        if isinstance(values, (str, bytes, Mapping)):
            raise DocumentationQueryError(
                "kinds must be an iterable of relationship kind strings."
            )
        try:
            requested = list(values)
        except TypeError as exc:
            raise DocumentationQueryError(
                "kinds must be an iterable of relationship kind strings."
            ) from exc
        if any(not isinstance(value, str) for value in requested):
            raise DocumentationQueryError(
                "kinds must contain only relationship kind strings."
            )
        unsupported = sorted(set(requested) - set(_KNOWLEDGE_RELATIONSHIP_KINDS))
        if unsupported:
            raise DocumentationQueryError(
                f"unsupported relationship kind: {unsupported[0]!r}."
            )
        selected = set(requested)
        return tuple(
            kind for kind in _KNOWLEDGE_RELATIONSHIP_KINDS if kind in selected
        )

    def _typed_graph_direction(self, value: object) -> str:
        if not isinstance(value, str) or value not in _TYPED_GRAPH_DIRECTIONS:
            choices = ", ".join(repr(item) for item in _TYPED_GRAPH_DIRECTIONS)
            raise DocumentationQueryError(f"direction must be one of {choices}.")
        return value

    def _typed_graph_kinds(
        self,
        values: Optional[Iterable[str]],
    ) -> tuple[str, ...]:
        if values is None:
            present_extensions = sorted(
                {
                    str(value)
                    for value in self._typed_graph_edge_kinds
                    if isinstance(value, str)
                    and value not in CORE_RELATIONSHIP_KINDS
                }
            )
            return (*CORE_RELATIONSHIP_KINDS, *present_extensions)
        if isinstance(values, (str, bytes, Mapping)) or not isinstance(
            values, IterableABC
        ):
            raise DocumentationQueryError(
                "kinds must be an iterable of typed relationship kind strings."
            )
        requested = list(values)
        if any(not isinstance(value, str) for value in requested):
            raise DocumentationQueryError(
                "kinds must contain only typed relationship kind strings."
            )
        invalid = sorted(
            {
                value
                for value in requested
                if value not in CORE_RELATIONSHIP_KINDS
                and not _QUALIFIED_NAME_RE.fullmatch(value)
            }
        )
        if invalid:
            raise DocumentationQueryError(
                f"unsupported typed relationship kind: {invalid[0]!r}."
            )
        selected = set(requested)
        core = [
            kind for kind in CORE_RELATIONSHIP_KINDS if kind in selected
        ]
        extensions = sorted(selected - set(CORE_RELATIONSHIP_KINDS))
        return tuple(core + extensions)

    def _typed_graph_enum_filter(
        self,
        values: Optional[Iterable[str]],
        *,
        field: str,
        allowed: Sequence[str],
    ) -> tuple[str, ...]:
        if values is None:
            return tuple(allowed)
        if isinstance(values, (str, bytes, Mapping)) or not isinstance(
            values, IterableABC
        ):
            raise DocumentationQueryError(
                f"{field} must be an iterable of strings."
            )
        requested = list(values)
        if any(not isinstance(value, str) for value in requested):
            raise DocumentationQueryError(
                f"{field} must contain only strings."
            )
        unsupported = sorted(set(requested) - set(allowed))
        if unsupported:
            raise DocumentationQueryError(
                f"unsupported {field[:-1]}: {unsupported[0]!r}."
            )
        selected = set(requested)
        return tuple(value for value in allowed if value in selected)

    def _incident_typed_graph_edges(
        self,
        locator: str,
        direction: str,
    ) -> list[tuple[int, str]]:
        selected: dict[int, str] = {}
        if direction in {"outgoing", "both"}:
            for index in self.outgoing_typed_graph_edges.get(locator, ()):
                selected[index] = "outgoing"
        if direction in {"incoming", "both"}:
            for index in self.incoming_typed_graph_edges.get(locator, ()):
                previous = selected.get(index)
                selected[index] = "both" if previous == "outgoing" else "incoming"

        direction_order = {"incoming": 0, "outgoing": 1, "both": 2}
        return sorted(
            selected.items(),
            key=lambda item: (
                direction_order[item[1]],
                self._typed_graph_edge_order[item[0]],
            ),
        )

    def _compact_typed_graph_edge(
        self,
        index: int,
        direction: str,
        *,
        include_evidence: bool,
    ) -> dict[str, Any]:
        edge = self._typed_graph_edges[index]
        source = cast(Mapping[str, Any], edge["from"])
        target = cast(Mapping[str, Any], edge["target"])
        source_locator = self._typed_graph_concept_locator(source)
        target_locator = self._typed_graph_target_locators[index]
        related_locator = (
            source_locator if direction == "incoming" else target_locator
        )
        if direction == "both":
            related_locator = target_locator or source_locator

        evidence = cast(Mapping[str, Any], edge["evidence"])
        if include_evidence:
            evidence_payload = _jsonable_mapping(evidence)
        else:
            evidence_payload = {
                key: _jsonable(evidence[key])
                for key in (
                    "state",
                    "observed",
                    "unique",
                    "emitted",
                    "omitted",
                )
                if key in evidence
            }
        return {
            "key": edge.get("key"),
            "kind": edge.get("kind"),
            "direction": direction,
            "from": _jsonable(source),
            "target": _jsonable(target),
            "origin": edge.get("origin"),
            "resolution": edge.get("resolution"),
            "related_concept": (
                self._compact_knowledge_concept(cast(str, related_locator))
                if isinstance(related_locator, str)
                and related_locator in self.concept_by_locator
                else None
            ),
            "evidence": evidence_payload,
            "coverage": _jsonable(edge["coverage"]),
        }

    def _resolved_target_locator(
        self,
        relationship: Mapping[str, Any],
    ) -> Optional[str]:
        if relationship.get("resolution") != "resolved":
            return None
        target = relationship.get("target")
        if not isinstance(target, Mapping):
            return None
        locator = target.get("locator")
        if isinstance(locator, str) and locator in self.concept_by_locator:
            return locator
        canonical_path = target.get("canonical_path")
        if isinstance(canonical_path, str):
            concept = self.concept_by_canonical_path.get(canonical_path)
            if concept is not None:
                return cast(str, concept["locator"])
        return None

    def _incident_knowledge_relationships(
        self,
        locator: str,
        direction: str,
    ) -> list[tuple[int, str]]:
        selected: dict[int, str] = {}
        if direction in {"outbound", "both"}:
            for index in self.outbound_relationships.get(locator, ()):
                selected[index] = "outbound"
        if direction in {"inbound", "both"}:
            for index in self.inbound_relationships.get(locator, ()):
                previous = selected.get(index)
                selected[index] = "both" if previous == "outbound" else "inbound"

        direction_order = {"inbound": 0, "outbound": 1, "both": 2}
        return sorted(
            selected.items(),
            key=lambda item: (
                direction_order[item[1]],
                self._knowledge_relationship_order[item[0]],
            ),
        )

    def _compact_knowledge_relationship(
        self,
        index: int,
        direction: str,
    ) -> dict[str, Any]:
        relationship = self._knowledge_relationships[index]
        target = cast(Mapping[str, Any], relationship.get("target", {}))
        evidence = cast(Mapping[str, Any], relationship.get("evidence", {}))
        source_locator = cast(str, relationship["from"])
        target_locator = self._knowledge_target_locators[index]
        related_locator = (
            source_locator if direction == "inbound" else target_locator
        )
        if direction == "both":
            related_locator = target_locator or source_locator
        return {
            "kind": relationship.get("kind"),
            "direction": direction,
            "from": source_locator,
            "resolution": relationship.get("resolution"),
            "origin": relationship.get("origin"),
            "evidence": {"state": evidence.get("state")},
            "related_concept": (
                None
                if related_locator is None
                else self._compact_knowledge_concept(related_locator)
            ),
            "target": _knowledge_target_ref(
                target,
                relationship.get("resolution"),
            ),
        }

    def _normalise_data_flows(
        self, data_flows: Optional[object]
    ) -> list[dict[str, Any]]:
        if data_flows is None:
            return []
        if isinstance(data_flows, Mapping):
            if "entry" in data_flows or "steps" in data_flows:
                return [_jsonable_mapping(cast(Mapping[str, Any], data_flows))]
            return [
                _jsonable_mapping(cast(Mapping[str, Any], value))
                for value in data_flows.values()
            ]
        return [
            _jsonable_mapping(cast(Mapping[str, Any], value))
            for value in cast(Iterable[Mapping[str, Any]], data_flows)
        ]

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

    def _build_graph_query_indexes(self) -> None:
        """Index exact graph coordinates once for local query-time work."""

        callables_by_identifier: dict[str, list[dict[str, Any]]] = defaultdict(list)
        callables_by_route: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(
            list
        )
        for ref in self.callables:
            identifiers = {str(ref.get("symbol")), str(ref.get("name"))}
            for identifier in identifiers:
                callables_by_identifier[identifier].append(ref)
                filepath = ref.get("file")
                if isinstance(filepath, str):
                    callables_by_route[(filepath, identifier)].append(ref)
        self._callables_by_identifier = {
            identifier: tuple(sorted(records, key=_record_sort_key))
            for identifier, records in callables_by_identifier.items()
        }
        self._callables_by_route = {
            route: tuple(sorted(records, key=_record_sort_key))
            for route, records in callables_by_route.items()
        }

        classes_by_name: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for ref in self.classes:
            classes_by_name[str(ref.get("name"))].append(ref)
        self._classes_by_name = {
            name: tuple(sorted(records, key=_record_sort_key))
            for name, records in classes_by_name.items()
        }

        def flow_index(
            records: Iterable[Mapping[str, Any]],
        ) -> dict[str, tuple[dict[str, Any], ...]]:
            by_identifier: dict[str, list[dict[str, Any]]] = defaultdict(list)
            for record in records:
                ref = _flow_ref(record)
                identifiers = {
                    str(ref.get("id")),
                    str(ref.get("symbol")),
                    str(ref.get("label")),
                }
                for identifier in identifiers:
                    by_identifier[identifier].append(cast(dict[str, Any], record))
            return {
                identifier: tuple(
                    sorted(
                        matches,
                        key=lambda item: _record_sort_key(_flow_ref(item)),
                    )
                )
                for identifier, matches in by_identifier.items()
            }

        self._flows_by_identifier = flow_index(self.flows)
        self._data_flows_by_identifier = flow_index(self.data_flows)

        pages_by_source: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for page in self.pages:
            source_path = page.get("source_path")
            if isinstance(source_path, str):
                pages_by_source[source_path].append(page)
        self._pages_by_source = {
            source_path: tuple(pages) for source_path, pages in pages_by_source.items()
        }

        pairs = []
        for edge in self.dependency.get("graph", {}).get("edges", []) or []:
            pair = _edge_pair(edge)
            if pair is not None:
                pairs.append(pair)
        self._dependency_edge_pairs = tuple(
            sorted(
                set(pairs),
                key=lambda item: (_text_key(item[0]), _text_key(item[1])),
            )
        )
        inbound: dict[str, list[str]] = defaultdict(list)
        outbound: dict[str, list[str]] = defaultdict(list)
        for source, target in self._dependency_edge_pairs:
            outbound[source].append(target)
            inbound[target].append(source)
        self._dependency_inbound = {
            path: tuple(sorted(neighbors, key=_text_key))
            for path, neighbors in inbound.items()
        }
        self._dependency_outbound = {
            path: tuple(sorted(neighbors, key=_text_key))
            for path, neighbors in outbound.items()
        }

        graph_nodes = self.dependency.get("graph", {}).get("nodes", []) or []
        self._dependency_nodes = frozenset(graph_nodes) | frozenset(self.inventory)

        cycles_by_path: dict[str, list[list[Any]]] = defaultdict(list)
        for group in self.dependency.get("cycles", []) or []:
            copied_group = list(group)
            seen_paths: set[str] = set()
            for member in copied_group:
                if isinstance(member, str) and member not in seen_paths:
                    cycles_by_path[member].append(copied_group)
                    seen_paths.add(member)
        self._dependency_cycles_by_path = {
            path: tuple(groups) for path, groups in cycles_by_path.items()
        }

        self._dependency_order_index: dict[str, int] = {}
        order = self.dependency.get("load_order", {}).get("order", []) or []
        for index, path in enumerate(order):
            if isinstance(path, str):
                self._dependency_order_index.setdefault(path, index)

    def _dependency_edges(self) -> list[tuple[str, str]]:
        return list(self._dependency_edge_pairs)

    def _raw_function_links(
        self,
    ) -> tuple[
        dict[tuple[object, object], list[dict[str, Any]]],
        dict[tuple[object, object], list[dict[str, Any]]],
    ]:
        callers: dict[tuple[object, object], list[dict[str, Any]]] = defaultdict(list)
        callees: dict[tuple[object, object], list[dict[str, Any]]] = defaultdict(list)
        for edge in self.call_edges:
            source = edge.get("from", {}) or {}
            target = edge.get("to", {}) or {}
            source_key = (source.get("file"), source.get("symbol"))
            target_key = (target.get("file"), target.get("symbol"))
            if source_key in self.callable_by_key:
                callees[source_key].append(_call_endpoint_ref(target, edge))
            if target_key in self.callable_by_key:
                callers[target_key].append(_call_endpoint_ref(source, edge))
        return (
            {key: _dedupe_sorted_all(value) for key, value in callers.items()},
            {key: _dedupe_sorted_all(value) for key, value in callees.items()},
        )

    def _callable_matches(self, query: str) -> list[dict[str, Any]]:
        matches = self._callables_by_identifier.get(query, ())
        if matches:
            return list(matches)

        if ":" not in query:
            return []
        raw_file, _, raw_symbol = query.partition(":")
        filepath = _normalise_source_path(raw_file, field="symbol file", required=False)
        if not filepath or not raw_symbol:
            return []
        return list(self._callables_by_route.get((filepath, raw_symbol), ()))

    def _symbol_matches(self, query: str) -> list[dict[str, Any]]:
        callables = self._callable_matches(query)
        classes = list(self._classes_by_name.get(query, ()))
        return sorted(callables + classes, key=_record_sort_key)

    def _flow_matches(
        self,
        query: str,
        index: Mapping[str, Sequence[dict[str, Any]]],
    ) -> list[dict[str, Any]]:
        return list(index.get(query, ()))

    def _selection_result(
        self,
        query: str,
        matches: Sequence[Mapping[str, Any]],
        payload_key: str,
        empty_payload: object,
    ) -> dict[str, Any]:
        refs = [
            _flow_ref(match) if payload_key in {"flow", "data_flow"} else match
            for match in matches
        ]
        bounded_matches = self._bounded(refs)
        if not matches:
            return {
                "query": query,
                "found": False,
                "ambiguous": False,
                "matches": [],
                "truncated": False,
                "bounds": {"matches": bounded_matches.metadata()},
                payload_key: empty_payload,
            }
        if len(matches) > 1:
            return {
                "query": query,
                "found": False,
                "ambiguous": True,
                "matches": bounded_matches.items,
                "truncated": bounded_matches.truncated,
                "bounds": {"matches": bounded_matches.metadata()},
                payload_key: empty_payload,
            }
        return {
            "query": query,
            "found": True,
            "ambiguous": False,
            "matches": bounded_matches.items,
            "truncated": bounded_matches.truncated,
            "bounds": {"matches": bounded_matches.metadata()},
            "_selected": _jsonable(matches[0]),
        }

    def _pages_for_source(self, source_path: object) -> _BoundedResult:
        normalised = _normalise_source_path(
            source_path, field="source_path", required=False
        )
        if normalised is None:
            return self._bounded(())
        return self._bounded(self._pages_by_source.get(normalised, ()))

    def _bounded_payload(
        self, payload: object, list_keys: tuple[str, ...]
    ) -> tuple[dict[str, Any], dict[str, _BoundedResult]]:
        copied = _jsonable(payload)
        if not isinstance(copied, dict):
            return {}, {key: self._bounded(()) for key in list_keys}
        bounds: dict[str, _BoundedResult] = {}
        for key in list_keys:
            if not isinstance(copied.get(key), list):
                bounds[key] = self._bounded(())
                continue
            bounded = self._bounded(copied[key])
            copied[key] = bounded.items
            bounds[key] = bounded
        return copied, bounds

    def _bounded(self, records: Iterable[object]) -> _BoundedResult:
        items = [_jsonable(record) for record in records]
        if all(isinstance(item, Mapping) for item in items):
            items.sort(key=lambda item: _record_sort_key(cast(Mapping[str, Any], item)))
        return _BoundedResult(items=items[: self.limit], total=len(items))

    def _bounded_strings(self, values: Iterable[object]) -> _BoundedResult:
        ordered = sorted({str(value) for value in values}, key=_text_key)
        return _BoundedResult(items=ordered[: self.limit], total=len(ordered))

    def _record_bound(
        self,
        result: dict[str, Any],
        path: str,
        bounded: _BoundedResult,
    ) -> None:
        bounds = result.setdefault("bounds", {})
        if not isinstance(bounds, dict):
            raise DocumentationQueryError("query response bounds must be a mapping.")
        bounds[path] = bounded.metadata()
        self._sync_truncated(result)

    @staticmethod
    def _sync_truncated(result: dict[str, Any]) -> None:
        bounds = result.get("bounds", {})
        result["truncated"] = isinstance(bounds, Mapping) and any(
            isinstance(bound, Mapping) and bool(bound.get("truncated"))
            for bound in bounds.values()
        )
