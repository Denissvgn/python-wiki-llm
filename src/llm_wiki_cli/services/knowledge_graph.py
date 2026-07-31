"""Pure typed-graph contract and materializer.

The M3 graph is an independently versioned, namespaced extension of the
``llm-wiki-knowledge/v1`` read model.  Keeping it behind that extension
preserves the frozen v1 ``derived_from``/``links_to`` relationship contract
while allowing structural analyzers to publish richer endpoints, evidence,
and coverage.

This module is intentionally pure over caller-supplied values.  It performs no
file reads or writes, source discovery, Markdown parsing, helper execution,
subprocess work, network access, or LLM calls.
"""

from __future__ import annotations

import json
import math
import re
from collections import defaultdict
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any
from urllib.parse import urlsplit

from .contracts import TYPED_GRAPH_EXTENSION_KEY, TYPED_GRAPH_SCHEMA_VERSION
from .knowledge_evidence import canonical_json_text, is_valid_sha256, sha256_bytes
from .validation import (
    require_choice,
    require_exact_fields as require_shared_exact_fields,
    require_list,
    require_mapping,
    require_nonempty_text,
    require_nonnegative_int,
    require_positive_int,
    require_repository_relative_path,
    require_sha256,
)
from .wiki_media import contains_uri_authority_userinfo
from .wiki_surface import WikiSurfaceError, validate_exact_page_coordinate

CORE_RELATIONSHIP_KINDS = (
    "contains",
    "imports",
    "calls",
    "entrypoint_for",
    "reads",
    "writes",
    "depends_on",
    "supersedes",
)
EMITTED_RELATIONSHIP_KINDS = CORE_RELATIONSHIP_KINDS[:-1]
GRAPH_ORIGINS = ("extracted", "inferred", "markdown", "governance")
GRAPH_RESOLUTIONS = ("resolved", "ambiguous", "external", "unresolved")
GRAPH_EVIDENCE_STATES = ("present", "unknown", "missing", "invalid")
ENDPOINT_KINDS = ("concept", "source-symbol", "external-resource", "unresolved")
GRAPH_INPUT_NAMES = (
    "inventory",
    "concept-map",
    "calls",
    "dependencies",
    "entrypoints",
    "flows",
    "data-flows",
    "external-dependencies",
    "analyzer-limitations",
)
GRAPH_COVERAGE_ANALYZERS = (
    "calls",
    "concept-map",
    "data-flows",
    "dependencies",
    "entrypoints",
    "external-dependencies",
    "flows",
)
_CORE_KIND_ANALYZERS = {
    "contains": "concept-map",
    "imports": "dependencies",
    "calls": "calls",
    "entrypoint_for": "entrypoints",
    "reads": "data-flows",
    "writes": "data-flows",
    "depends_on": "external-dependencies",
}
DEFAULT_EVIDENCE_LIMIT = 20
MAX_EVIDENCE_LIMIT = 1000
_INVENTORY_SNAPSHOT_DOMAIN = "llm-wiki/inventory-snapshot/v1"
_FLOW_OBSERVATIONS_SCHEMA = "llm-wiki-flow-observations/v1"

_QUALIFIED_NAME_RE = re.compile(
    r"^[A-Za-z][A-Za-z0-9._-]*/[A-Za-z][A-Za-z0-9._-]*$"
)
_LIMITATION_RE = re.compile(
    r"^[a-z][a-z0-9.-]*(?:/[a-z][a-z0-9.-]*)?$"
)
_CONTROL_RE = re.compile(r"[\x00-\x1f\x7f]")
_URI_RE = re.compile(r"^[A-Za-z][A-Za-z0-9+.-]*:")


def is_supported_relationship_kind(value: object) -> bool:
    """Return whether *value* is a core or qualified relationship kind."""

    return isinstance(value, str) and (
        value in CORE_RELATIONSHIP_KINDS
        or _QUALIFIED_NAME_RE.fullmatch(value) is not None
    )


class KnowledgeGraphError(ValueError):
    """Field-specific typed-graph contract or materialization failure."""

    def __init__(self, field: str, message: str):
        self.field = field
        self.message = message
        super().__init__(f"{field}: {message}")


@dataclass(frozen=True)
class GraphConcept:
    """One already-built concept coordinate used for endpoint lifting."""

    locator: str
    concept_kind: str
    source_path: str | None = None
    symbol: str | None = None
    occurrence: int | None = None
    page_id: str | None = None


@dataclass(frozen=True)
class KnowledgeGraphInputs:
    """Complete evaluated inputs for one pure graph materialization."""

    inventory: Mapping[str, Any]
    concepts: Sequence[GraphConcept]
    call_edges: Mapping[str, Any] | Sequence[Mapping[str, Any]] = ()
    dependency_observations: Mapping[str, Any] | Sequence[Mapping[str, Any]] = ()
    entrypoint_observations: Mapping[str, Any] | Sequence[Mapping[str, Any]] = ()
    flows: Sequence[Mapping[str, Any]] = ()
    data_flows: Sequence[Mapping[str, Any]] = ()
    external_dependencies: Sequence[Mapping[str, Any]] = ()
    analyzer_limitations: Mapping[str, Sequence[str]] = field(default_factory=dict)
    evidence_limit: int = DEFAULT_EVIDENCE_LIMIT


@dataclass
class _EdgeAccumulator:
    kind: str
    source: dict[str, Any]
    target: dict[str, Any]
    origin: str
    resolution: str
    aggregate_input_hash: str
    evidence_limit: int
    limitations: set[str] = field(default_factory=set)
    observed: int = 0
    _samples: dict[str, dict[str, Any]] = field(default_factory=dict)

    def add(self, sample: Mapping[str, Any]) -> None:
        self.observed += 1
        normalized = _normalise_evidence_sample(sample, "evidence.sample")
        key = _canonical_json(normalized)
        self._samples.setdefault(key, normalized)

    def payload(self) -> dict[str, Any]:
        identity = {
            "kind": self.kind,
            "from": self.source,
            "target": self.target,
            "origin": self.origin,
            "resolution": self.resolution,
        }
        ordered_samples = [
            self._samples[key] for key in sorted(self._samples)
        ]
        emitted_samples = ordered_samples[: self.evidence_limit]
        emitted = len(emitted_samples)
        omitted = self.observed - emitted
        coverage = {
            "observed": self.observed,
            "emitted": emitted,
            "omitted": omitted,
            "limit": self.evidence_limit,
            "truncated": omitted > 0,
            "limitations": sorted(self.limitations),
        }
        return {
            "key": relationship_edge_key(identity),
            **identity,
            "evidence": {
                "state": "present" if self.observed else "unknown",
                "aggregate_input_hash": self.aggregate_input_hash,
                "observed": self.observed,
                "unique": len(ordered_samples),
                "emitted": emitted,
                "omitted": omitted,
                "samples": emitted_samples,
            },
            "coverage": coverage,
        }


@dataclass
class _MaterializationState:
    inputs: KnowledgeGraphInputs
    concepts: tuple[GraphConcept, ...]
    input_hashes: dict[str, str]
    module_by_source: dict[str, GraphConcept]
    entities_by_source_symbol: dict[tuple[str, str], tuple[GraphConcept, ...]]
    flow_by_id: dict[str, GraphConcept]
    edges: dict[str, _EdgeAccumulator] = field(default_factory=dict)
    coverage: dict[str, dict[str, Any]] = field(default_factory=dict)

    def add_edge(
        self,
        *,
        analyzer: str,
        kind: str,
        source: Mapping[str, Any],
        target: Mapping[str, Any],
        origin: str,
        resolution: str,
        sample: Mapping[str, Any],
        limitations: Iterable[str] = (),
    ) -> None:
        identity = {
            "kind": kind,
            "from": dict(source),
            "target": dict(target),
            "origin": origin,
            "resolution": resolution,
        }
        key = relationship_edge_key(identity)
        accumulator = self.edges.get(key)
        if accumulator is None:
            accumulator = _EdgeAccumulator(
                kind=kind,
                source=dict(source),
                target=dict(target),
                origin=origin,
                resolution=resolution,
                aggregate_input_hash=self.input_hashes[analyzer],
                evidence_limit=self.inputs.evidence_limit,
            )
            self.edges[key] = accumulator
        accumulator.limitations.update(limitations)
        accumulator.add(sample)


def concept_endpoint(locator: str) -> dict[str, str]:
    """Return a typed concept endpoint after validating its exact locator."""

    return _normalise_endpoint(
        {"kind": "concept", "locator": locator},
        "endpoint",
    )


def source_symbol_endpoint(source_path: str, symbol: str) -> dict[str, str]:
    """Return a typed source-symbol endpoint."""

    return _normalise_endpoint(
        {
            "kind": "source-symbol",
            "source_path": source_path,
            "symbol": symbol,
        },
        "endpoint",
    )


def external_resource_endpoint(
    resource: str,
    *,
    uri: str | None = None,
) -> dict[str, str]:
    """Return a typed external-resource endpoint."""

    value: dict[str, str] = {"kind": "external-resource", "resource": resource}
    if uri is not None:
        value["uri"] = uri
    return _normalise_endpoint(value, "endpoint")


def unresolved_endpoint(
    raw_target: str,
    *,
    candidates: Sequence[Mapping[str, Any]] = (),
) -> dict[str, Any]:
    """Return an unresolved endpoint with optional non-authoritative candidates."""

    value: dict[str, Any] = {"kind": "unresolved", "raw_target": raw_target}
    if candidates:
        value["candidates"] = list(candidates)
    return _normalise_endpoint(value, "endpoint")


def relationship_edge_key(identity: Mapping[str, Any]) -> str:
    """Return the domain-separated canonical key for one edge identity."""

    fields = ("kind", "from", "target", "origin", "resolution")
    missing = next((name for name in fields if name not in identity), None)
    if missing is not None:
        raise KnowledgeGraphError(f"edge.{missing}", "is required for edge identity")
    preimage = {
        "domain": TYPED_GRAPH_SCHEMA_VERSION,
        **{name: identity[name] for name in fields},
    }
    return sha256_bytes(_canonical_json(preimage).encode("utf-8"))


def materialize_typed_graph(inputs: KnowledgeGraphInputs) -> dict[str, Any]:
    """Materialize a deterministic evidence-backed graph from evaluated inputs."""

    if not isinstance(inputs, KnowledgeGraphInputs):
        raise TypeError("inputs must be a KnowledgeGraphInputs")
    if (
        isinstance(inputs.evidence_limit, bool)
        or not isinstance(inputs.evidence_limit, int)
        or not 1 <= inputs.evidence_limit <= MAX_EVIDENCE_LIMIT
    ):
        raise KnowledgeGraphError(
            "evidence_limit",
            f"must be an integer from 1 through {MAX_EVIDENCE_LIMIT}",
        )
    concepts = _normalise_graph_concepts(inputs.concepts)
    input_payloads = {
        # Inventory is an input commitment, not an emitted graph value.
        # Extracted source docstrings may legitimately contain escaped control
        # bytes (for example Windows path examples). Canonical JSON safely
        # escapes them while keeping the exact input hash; graph fields still
        # reject control characters below.
        "inventory": _json_value(
            inputs.inventory,
            "inventory",
            allow_control_strings=True,
        ),
        "concept-map": [_graph_concept_payload(value) for value in concepts],
        "calls": _observation_bundle_for_hash(inputs.call_edges, "call_edges"),
        "dependencies": _observation_bundle_for_hash(
            inputs.dependency_observations,
            "dependency_observations",
        ),
        "entrypoints": _observation_bundle_for_hash(
            inputs.entrypoint_observations,
            "entrypoint_observations",
        ),
        "flows": _sorted_json_records(inputs.flows, "flows"),
        "data-flows": _sorted_json_records(inputs.data_flows, "data_flows"),
        "external-dependencies": _sorted_json_records(
            inputs.external_dependencies,
            "external_dependencies",
        ),
        "analyzer-limitations": _normalise_analyzer_limitations(
            inputs.analyzer_limitations
        ),
    }
    input_hashes = {
        name: sha256_bytes(_canonical_json(value).encode("utf-8"))
        for name, value in input_payloads.items()
    }
    input_hashes["inventory"] = sha256_bytes(
        _canonical_json(
            {
                "domain": _INVENTORY_SNAPSHOT_DOMAIN,
                "inventory": input_payloads["inventory"],
            }
        ).encode("utf-8")
    )
    state = _materialization_state(inputs, concepts, input_hashes)

    _materialize_contains(state)
    _materialize_imports(state)
    _materialize_calls(state)
    _materialize_entrypoints(state)
    _materialize_data_effects(state)
    _materialize_external_dependencies(state)

    aggregate_hash = _aggregate_input_hash(input_hashes)
    graph = {
        "schema_version": TYPED_GRAPH_SCHEMA_VERSION,
        "input_hashes": {
            **{name: input_hashes[name] for name in sorted(input_hashes)},
            "aggregate": aggregate_hash,
        },
        "coverage": [
            {"analyzer": analyzer, **state.coverage[analyzer]}
            for analyzer in sorted(state.coverage)
        ],
        "edges": [
            state.edges[key].payload() for key in sorted(state.edges)
        ],
    }
    return validate_typed_graph(
        graph,
        concept_kinds={concept.locator: concept.concept_kind for concept in concepts},
    )


def validate_typed_graph(
    payload: object,
    *,
    concept_kinds: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    """Validate and canonicalize one ``llm-wiki-typed-graph/v1`` payload."""

    graph = _object(payload, "typed_graph")
    _only_fields(
        graph,
        "typed_graph",
        {"schema_version", "input_hashes", "coverage", "edges"},
        required={"schema_version", "input_hashes", "coverage", "edges"},
    )
    if graph["schema_version"] != TYPED_GRAPH_SCHEMA_VERSION:
        raise KnowledgeGraphError(
            "typed_graph.schema_version",
            f"must be {TYPED_GRAPH_SCHEMA_VERSION!r}",
        )
    input_hashes = _normalise_input_hashes(graph["input_hashes"])
    coverage_values = _array(graph["coverage"], "typed_graph.coverage")
    coverage: list[dict[str, Any]] = []
    seen_analyzers: set[str] = set()
    for index, value in enumerate(coverage_values):
        path = f"typed_graph.coverage[{index}]"
        record = _object(value, path)
        _only_fields(
            record,
            path,
            {
                "analyzer",
                "observed",
                "emitted",
                "omitted",
                "limit",
                "truncated",
                "limitations",
            },
            required={
                "analyzer",
                "observed",
                "emitted",
                "omitted",
                "limit",
                "truncated",
                "limitations",
            },
        )
        analyzer = _name(record["analyzer"], f"{path}.analyzer")
        if analyzer in seen_analyzers:
            raise KnowledgeGraphError(
                f"{path}.analyzer", f"duplicates analyzer {analyzer!r}"
            )
        seen_analyzers.add(analyzer)
        coverage.append(
            {
                "analyzer": analyzer,
                **_normalise_coverage(record, path, include_analyzer=True),
            }
        )

    raw_edges = _array(graph["edges"], "typed_graph.edges")
    edges: list[dict[str, Any]] = []
    seen_keys: set[str] = set()
    kinds_by_locator = (
        {
            _locator(locator, "concept_kinds key"): _name(kind, "concept_kinds value")
            for locator, kind in concept_kinds.items()
        }
        if concept_kinds is not None
        else None
    )
    for index, value in enumerate(raw_edges):
        path = f"typed_graph.edges[{index}]"
        edge = _normalise_edge(value, path, kinds_by_locator)
        key = edge["key"]
        if key in seen_keys:
            raise KnowledgeGraphError(f"{path}.key", f"duplicates edge key {key!r}")
        seen_keys.add(key)
        edges.append(edge)
    edges.sort(key=lambda value: value["key"])
    coverage.sort(key=lambda value: value["analyzer"])
    _validate_graph_bindings(input_hashes, coverage, edges)
    return {
        "schema_version": TYPED_GRAPH_SCHEMA_VERSION,
        "input_hashes": input_hashes,
        "coverage": coverage,
        "edges": edges,
    }


def serialize_typed_graph(
    payload: object,
    *,
    concept_kinds: Mapping[str, str] | None = None,
) -> str:
    """Return deterministic JSON for a standalone typed graph."""

    return (
        json.dumps(
            validate_typed_graph(payload, concept_kinds=concept_kinds),
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n"
    )


def typed_graph_from_knowledge_extensions(
    extensions: Mapping[str, Any],
    *,
    concept_kinds: Mapping[str, str] | None = None,
) -> dict[str, Any] | None:
    """Validate the reserved graph extension, returning ``None`` when absent."""

    if not isinstance(extensions, Mapping):
        raise KnowledgeGraphError("extensions", "must be an object")
    value = extensions.get(TYPED_GRAPH_EXTENSION_KEY)
    if value is None:
        return None
    return validate_typed_graph(value, concept_kinds=concept_kinds)


def _materialization_state(
    inputs: KnowledgeGraphInputs,
    concepts: tuple[GraphConcept, ...],
    input_hashes: dict[str, str],
) -> _MaterializationState:
    modules: dict[str, GraphConcept] = {}
    entities: defaultdict[tuple[str, str], list[GraphConcept]] = defaultdict(list)
    flows: dict[str, GraphConcept] = {}
    for concept in concepts:
        if concept.concept_kind == "source-module" and concept.source_path is not None:
            if concept.source_path in modules:
                raise KnowledgeGraphError(
                    "concepts",
                    f"multiple source-module concepts claim {concept.source_path!r}",
                )
            modules[concept.source_path] = concept
        elif (
            concept.concept_kind == "code-entity"
            and concept.source_path is not None
            and concept.symbol is not None
        ):
            entities[(concept.source_path, concept.symbol)].append(concept)
        elif concept.concept_kind == "user-flow" and concept.page_id:
            if concept.page_id in flows:
                raise KnowledgeGraphError(
                    "concepts",
                    f"multiple user-flow concepts claim page id {concept.page_id!r}",
                )
            flows[concept.page_id] = concept

    return _MaterializationState(
        inputs=inputs,
        concepts=concepts,
        input_hashes=input_hashes,
        module_by_source=modules,
        entities_by_source_symbol={
            key: tuple(
                sorted(
                    values,
                    key=lambda value: (
                        value.occurrence or 0,
                        value.locator,
                    ),
                )
            )
            for key, values in entities.items()
        },
        flow_by_id=flows,
    )


def _materialize_contains(state: _MaterializationState) -> None:
    observed = 0
    emitted = 0
    for entity in state.concepts:
        if (
            entity.concept_kind != "code-entity"
            or entity.source_path is None
            or entity.symbol is None
        ):
            continue
        observed += 1
        module = state.module_by_source.get(entity.source_path)
        if module is None:
            continue
        emitted += 1
        state.add_edge(
            analyzer="concept-map",
            kind="contains",
            source=concept_endpoint(module.locator),
            target=concept_endpoint(entity.locator),
            origin="extracted",
            resolution="resolved",
            sample={
                "kind": "containment",
                "source": source_symbol_endpoint(entity.source_path, "<module>"),
                "target": source_symbol_endpoint(entity.source_path, entity.symbol),
                "attributes": {
                    "occurrence": entity.occurrence,
                },
            },
        )
    limitations = list(_limitations(state.inputs, "concept-map"))
    if emitted < observed:
        limitations.append("graph/missing-module-owner")
    state.coverage["concept-map"] = _coverage(
        observed,
        emitted,
        limit=None,
        limitations=limitations,
    )


def _materialize_imports(state: _MaterializationState) -> None:
    observations, supplied_coverage = _observation_collection(
        state.inputs.dependency_observations,
        "dependency_observations",
    )
    emitted = 0
    limitations = list(_limitations(state.inputs, "dependencies"))
    for value in observations:
        if not isinstance(value, Mapping):
            continue
        source_path = value.get("source_path") or value.get("file")
        if not isinstance(source_path, str):
            continue
        module = state.module_by_source.get(source_path)
        if module is None:
            continue
        raw_module = str(value.get("module") or "")
        raw_name = str(value.get("name") or "")
        raw_target = raw_module or raw_name or "unknown"
        resolution = str(value.get("resolution") or "unresolved")
        if resolution not in GRAPH_RESOLUTIONS:
            resolution = "unresolved"

        target: dict[str, Any]
        if resolution == "resolved":
            target_path = value.get("target_path") or value.get("target")
            target_concept = (
                state.module_by_source.get(str(target_path))
                if isinstance(target_path, str)
                else None
            )
            if target_concept is None:
                resolution = "unresolved"
                target = unresolved_endpoint(raw_target)
            else:
                target = concept_endpoint(target_concept.locator)
        elif resolution == "external":
            target = external_resource_endpoint(
                _external_import_resource(raw_module, raw_name)
            )
        else:
            candidate_endpoints = []
            raw_candidates = value.get("candidates")
            if isinstance(raw_candidates, Sequence) and not isinstance(
                raw_candidates, (str, bytes)
            ):
                for candidate in raw_candidates:
                    if not isinstance(candidate, str):
                        continue
                    concept = state.module_by_source.get(candidate)
                    candidate_endpoints.append(
                        concept_endpoint(concept.locator)
                        if concept is not None
                        else source_symbol_endpoint(candidate, raw_name or "<module>")
                    )
            target = unresolved_endpoint(
                raw_target,
                candidates=candidate_endpoints,
            )
        sample_target = (
            source_symbol_endpoint(
                str(value.get("target_path")),
                raw_name or "<module>",
            )
            if isinstance(value.get("target_path"), str)
            else target
        )
        state.add_edge(
            analyzer="dependencies",
            kind="imports",
            source=concept_endpoint(module.locator),
            target=target,
            origin="extracted",
            resolution=resolution,
            sample={
                "kind": "import",
                "source": source_symbol_endpoint(source_path, "<module>"),
                "target": sample_target,
                "location": _line_location(source_path, value.get("line")),
                "attributes": {
                    "module": raw_module,
                    "name": raw_name,
                    "candidates": sorted(
                        str(candidate)
                        for candidate in (value.get("candidates") or [])
                        if isinstance(candidate, str)
                    ),
                },
            },
        )
        emitted += 1
    state.coverage["dependencies"] = _coverage_from_supplied(
        supplied_coverage,
        fallback_observed=len(observations),
        emitted=emitted,
        limitations=limitations,
    )


def _materialize_calls(state: _MaterializationState) -> None:
    observations, supplied_coverage = _observation_collection(
        state.inputs.call_edges,
        "call_edges",
    )
    observed = len(observations)
    emitted = 0
    limitations = list(_limitations(state.inputs, "calls"))
    ordered_edges = sorted(
        (
            value
            for value in observations
            if isinstance(value, Mapping)
        ),
        key=_canonical_json,
    )
    for edge in ordered_edges:
        source_value = edge.get("from")
        target_value = edge.get("to")
        if not isinstance(source_value, Mapping) or not isinstance(
            target_value, Mapping
        ):
            continue
        source_path = source_value.get("file")
        source_symbol = source_value.get("symbol")
        if not isinstance(source_path, str) or not isinstance(source_symbol, str):
            continue
        source_owner = _owner_concept(state, source_path, source_symbol)
        if source_owner is None:
            continue
        target_path = target_value.get("file")
        target_symbol = target_value.get("symbol")
        raw_target = str(
            edge.get("name")
            or target_symbol
            or target_path
            or "unknown"
        )
        edge_kind = str(edge.get("kind") or "unresolved")
        resolution = "unresolved"
        target: dict[str, Any]
        candidate_source_symbols: list[dict[str, Any]] = []
        if edge_kind == "internal" and isinstance(target_path, str):
            target_owner = _owner_concept(
                state,
                target_path,
                str(target_symbol or raw_target),
            )
            if target_owner is not None:
                target = concept_endpoint(target_owner.locator)
                resolution = "resolved"
            else:
                target = unresolved_endpoint(raw_target)
        elif edge_kind == "external":
            target = external_resource_endpoint(raw_target)
            resolution = "external"
        elif edge_kind == "ambiguous":
            candidate_endpoints: list[dict[str, Any]] = []
            raw_candidates = edge.get("candidates")
            if isinstance(raw_candidates, Sequence) and not isinstance(
                raw_candidates,
                (str, bytes),
            ):
                for candidate in raw_candidates:
                    if not isinstance(candidate, Mapping):
                        continue
                    candidate_path = candidate.get("file")
                    candidate_symbol = candidate.get("symbol")
                    if not isinstance(candidate_path, str):
                        continue
                    candidate_owner = _owner_concept(
                        state,
                        candidate_path,
                        str(candidate_symbol or raw_target),
                    )
                    candidate_source_symbols.append(
                        source_symbol_endpoint(
                            candidate_path,
                            str(candidate_symbol or raw_target),
                        )
                    )
                    candidate_endpoints.append(
                        concept_endpoint(candidate_owner.locator)
                        if candidate_owner is not None
                        else source_symbol_endpoint(
                            candidate_path,
                            str(candidate_symbol or raw_target),
                        )
                    )
            target = unresolved_endpoint(
                raw_target,
                candidates=candidate_endpoints,
            )
            resolution = "ambiguous"
        else:
            target = unresolved_endpoint(raw_target)
        sample_target = (
            source_symbol_endpoint(target_path, str(target_symbol or raw_target))
            if isinstance(target_path, str)
            else target
        )
        call_attributes = {
            key: edge[key]
            for key in ("name", "args", "kwargs")
            if key in edge
        }
        if candidate_source_symbols:
            canonical_candidates = {
                _canonical_json(candidate): candidate
                for candidate in candidate_source_symbols
            }
            call_attributes["candidate_source_symbols"] = [
                canonical_candidates[key]
                for key in sorted(canonical_candidates)
            ]
        state.add_edge(
            analyzer="calls",
            kind="calls",
            source=concept_endpoint(source_owner.locator),
            target=target,
            origin="extracted",
            resolution=resolution,
            sample={
                "kind": "call",
                "source": source_symbol_endpoint(source_path, source_symbol),
                "target": sample_target,
                "location": _line_location(source_path, edge.get("line")),
                "attributes": call_attributes,
            },
        )
        emitted += 1
    if emitted < observed:
        limitations.append("graph/unowned-call")
    state.coverage["calls"] = _coverage_from_supplied(
        supplied_coverage,
        fallback_observed=observed,
        emitted=emitted,
        limitations=limitations,
    )


def _materialize_entrypoints(state: _MaterializationState) -> None:
    observations, supplied_coverage = _observation_collection(
        state.inputs.entrypoint_observations,
        "entrypoint_observations",
    )
    emitted = 0
    limitations = list(_limitations(state.inputs, "entrypoints"))
    for observation in observations:
        if not isinstance(observation, Mapping):
            continue
        entry_value = observation.get("entry", observation)
        if not isinstance(entry_value, Mapping):
            continue
        source_path = entry_value.get("file")
        symbol = entry_value.get("symbol")
        if not isinstance(source_path, str) or not isinstance(symbol, str):
            continue
        source_owner = _owner_concept(state, source_path, symbol)
        if source_owner is None:
            continue
        flow_id = entry_value.get("id")
        flow_concept = (
            state.flow_by_id.get(str(flow_id))
            if isinstance(flow_id, str)
            else None
        )
        if flow_concept is None:
            target = unresolved_endpoint(str(flow_id or symbol))
            resolution = "unresolved"
        else:
            target = concept_endpoint(flow_concept.locator)
            resolution = "resolved"
        detector = observation.get("detector")
        detector_value = detector if isinstance(detector, Mapping) else {}
        detector_source_location = detector_value.get("source_location")
        if not isinstance(detector_source_location, Mapping):
            detector_source_location = None
        graph_detector = (
            {
                "id": detector_value.get("id"),
                "version": detector_value.get("version"),
                "component": detector_value.get("plugin_component"),
            }
            if detector_value
            else None
        )
        if graph_detector is not None and graph_detector["component"] is None:
            graph_detector.pop("component")
        state.add_edge(
            analyzer="entrypoints",
            kind="entrypoint_for",
            source=concept_endpoint(source_owner.locator),
            target=target,
            origin="inferred",
            resolution=resolution,
            sample={
                "kind": "entrypoint",
                "source": source_symbol_endpoint(source_path, symbol),
                "target": target,
                "location": (
                    dict(detector_source_location)
                    if detector_source_location is not None
                    else _line_location(source_path, observation.get("line"))
                ),
                "detector": graph_detector,
                "reason": detector_value.get("reason")
                or observation.get("reason"),
                "attributes": {
                    key: entry_value[key]
                    for key in ("id", "category", "label")
                    if key in entry_value
                },
            },
        )
        emitted += 1
    if not observations and state.inputs.flows:
        # A caller may supply flow records from an older analyzer without the
        # detailed entry-point collection. Preserve the observation honestly.
        limitations.append("graph/entrypoint-details-absent")
    state.coverage["entrypoints"] = _coverage_from_supplied(
        supplied_coverage,
        fallback_observed=len(observations),
        emitted=emitted,
        limitations=limitations,
    )
    state.coverage["flows"] = _aggregate_flow_coverage(
        state.inputs.flows,
        limitations=_limitations(state.inputs, "flows"),
    )


def _aggregate_flow_coverage(
    flows: Sequence[Mapping[str, Any]],
    *,
    limitations: Iterable[str],
) -> dict[str, Any]:
    observed = 0
    emitted = 0
    inherited = list(limitations)
    summed_limit = 0
    all_limits_known = bool(flows)

    for index, flow in enumerate(flows):
        if not isinstance(flow, Mapping):
            raise KnowledgeGraphError(f"flows[{index}]", "must be an object")
        raw_steps = flow.get("steps")
        step_count = (
            len(raw_steps)
            if isinstance(raw_steps, Sequence)
            and not isinstance(raw_steps, (str, bytes))
            else 0
        )
        coverage = flow.get("coverage")
        step_coverage = (
            coverage.get("steps") if isinstance(coverage, Mapping) else None
        )
        if (
            flow.get("schema_version") != _FLOW_OBSERVATIONS_SCHEMA
            or not isinstance(step_coverage, Mapping)
        ):
            observed += step_count
            emitted += step_count
            all_limits_known = False
            if flow.get("truncated"):
                inherited.append("graph/flow-reachable-step-total-unavailable")
            continue

        normalized = _normalise_coverage(
            step_coverage,
            f"flows[{index}].coverage.steps",
            include_analyzer=True,
        )
        if normalized["emitted"] != step_count:
            raise KnowledgeGraphError(
                f"flows[{index}].coverage.steps.emitted",
                "must equal the number of supplied flow steps",
            )
        observed += normalized["observed"]
        emitted += normalized["emitted"]
        inherited.extend(normalized["limitations"])
        if normalized["limit"] is None:
            all_limits_known = False
        else:
            summed_limit += normalized["limit"]

    return _coverage(
        observed,
        emitted,
        limit=summed_limit if all_limits_known else None,
        limitations=inherited,
    )


def _materialize_data_effects(state: _MaterializationState) -> None:
    observed = 0
    emitted = 0
    limitations = list(_limitations(state.inputs, "data-flows"))
    for data_flow in sorted(
        (
            value
            for value in state.inputs.data_flows
            if isinstance(value, Mapping)
        ),
        key=_canonical_json,
    ):
        directional_coverage = _directional_data_effect_coverage(data_flow)
        if directional_coverage is not None:
            observed += directional_coverage["observed"]
            limitations.extend(directional_coverage["limitations"])
        candidate_effects_in_flow = 0
        entry = data_flow.get("entry")
        flow_id = data_flow.get("id")
        if not isinstance(entry, Mapping):
            entry = {}
        source_concept = (
            state.flow_by_id.get(str(flow_id))
            if isinstance(flow_id, str)
            else None
        )
        if source_concept is None:
            entry_id = entry.get("id")
            if isinstance(entry_id, str):
                source_concept = state.flow_by_id.get(entry_id)
        if source_concept is None:
            entry_path = entry.get("file")
            entry_symbol = entry.get("symbol")
            if isinstance(entry_path, str) and isinstance(entry_symbol, str):
                source_concept = _owner_concept(state, entry_path, entry_symbol)

        for step in data_flow.get("steps", []) or []:
            if not isinstance(step, Mapping):
                continue
            step_path = step.get("file")
            step_symbol = step.get("symbol")
            for effect_key, graph_kind in (("reads", "reads"), ("writes", "writes")):
                for effect in step.get(effect_key, []) or []:
                    if not isinstance(effect, Mapping):
                        continue
                    candidate_effects_in_flow += 1
                    if source_concept is None:
                        continue
                    resource = _effect_resource(effect)
                    target_concept = state.module_by_source.get(resource)
                    if target_concept is not None:
                        target = concept_endpoint(target_concept.locator)
                        resolution = "resolved"
                    else:
                        target = external_resource_endpoint(resource)
                        resolution = "external"
                    sample_source = (
                        source_symbol_endpoint(str(step_path), str(step_symbol))
                        if isinstance(step_path, str) and isinstance(step_symbol, str)
                        else concept_endpoint(source_concept.locator)
                    )
                    state.add_edge(
                        analyzer="data-flows",
                        kind=graph_kind,
                        source=concept_endpoint(source_concept.locator),
                        target=target,
                        origin="inferred",
                        resolution=resolution,
                        sample={
                            "kind": "data-effect",
                            "source": sample_source,
                            "target": target,
                            "location": (
                                _line_location(step_path, effect.get("line"))
                                if isinstance(step_path, str)
                                else None
                            ),
                            "attributes": dict(effect),
                        },
                    )
                    emitted += 1
        if directional_coverage is None:
            observed += candidate_effects_in_flow
    if emitted < observed:
        limitations.append("graph/upstream-data-effects-omitted")
    if emitted < sum(
        1
        for data_flow in state.inputs.data_flows
        if isinstance(data_flow, Mapping)
        for step in (data_flow.get("steps", []) or [])
        if isinstance(step, Mapping)
        for effect_key in ("reads", "writes")
        for effect in (step.get(effect_key, []) or [])
        if isinstance(effect, Mapping)
    ):
        limitations.append("graph/unowned-data-effect")
    state.coverage["data-flows"] = _coverage(
        observed,
        emitted,
        limit=None,
        limitations=limitations,
    )


def _directional_data_effect_coverage(
    data_flow: Mapping[str, Any],
) -> dict[str, Any] | None:
    """Return upstream reads/writes coverage when the detailed API supplied it."""

    coverage = data_flow.get("coverage")
    if not isinstance(coverage, Mapping):
        return None
    effects = coverage.get("effects")
    if not isinstance(effects, Mapping):
        return None
    by_kind = effects.get("by_kind")
    if not isinstance(by_kind, Mapping):
        return None
    observed = 0
    limitations: list[str] = []
    found = False
    for effect_kind in ("reads", "writes"):
        value = by_kind.get(effect_kind)
        if not isinstance(value, Mapping):
            continue
        raw_observed = value.get("observed")
        if isinstance(raw_observed, int) and not isinstance(raw_observed, bool):
            observed += max(raw_observed, 0)
            found = True
        raw_limitations = value.get("limitations")
        if isinstance(raw_limitations, list):
            limitations.extend(
                item for item in raw_limitations if isinstance(item, str)
            )
    if not found:
        return None
    return {"observed": observed, "limitations": limitations}


def _materialize_external_dependencies(state: _MaterializationState) -> None:
    observed = 0
    emitted = 0
    limitations = list(_limitations(state.inputs, "external-dependencies"))
    for dependency in sorted(
        (
            value
            for value in state.inputs.external_dependencies
            if isinstance(value, Mapping)
        ),
        key=_canonical_json,
    ):
        if dependency.get("explicit") is not True:
            continue
        observed += 1
        source_path = dependency.get("source_path") or dependency.get("file")
        if not isinstance(source_path, str):
            continue
        source = state.module_by_source.get(source_path)
        if source is None:
            continue
        resource = dependency.get("package") or dependency.get("resource")
        if not isinstance(resource, str) or not resource.strip():
            continue
        target = external_resource_endpoint(resource.strip())
        state.add_edge(
            analyzer="external-dependencies",
            kind="depends_on",
            source=concept_endpoint(source.locator),
            target=target,
            origin="extracted",
            resolution="external",
            sample={
                "kind": "dependency",
                "source": source_symbol_endpoint(source_path, "<module>"),
                "target": target,
                "reason": dependency.get("reason"),
                "attributes": {
                    key: dependency[key]
                    for key in sorted(dependency)
                    if key not in {"source_path", "file", "package", "resource"}
                },
            },
        )
        emitted += 1
    state.coverage["external-dependencies"] = _coverage(
        observed,
        emitted,
        limit=None,
        limitations=limitations,
    )


def _owner_concept(
    state: _MaterializationState,
    source_path: str,
    symbol: str,
) -> GraphConcept | None:
    class_name = symbol.split(".", 1)[0]
    entity_candidates = state.entities_by_source_symbol.get(
        (source_path, class_name),
        (),
    )
    if "." in symbol and len(entity_candidates) == 1:
        return entity_candidates[0]
    if symbol == class_name and len(entity_candidates) == 1:
        return entity_candidates[0]
    return state.module_by_source.get(source_path)


def _normalise_graph_concepts(
    values: Sequence[GraphConcept],
) -> tuple[GraphConcept, ...]:
    if isinstance(values, (str, bytes, Mapping)) or not isinstance(values, Sequence):
        raise KnowledgeGraphError("concepts", "must be a sequence")
    concepts: list[GraphConcept] = []
    seen: set[str] = set()
    for index, value in enumerate(values):
        path = f"concepts[{index}]"
        if not isinstance(value, GraphConcept):
            raise KnowledgeGraphError(path, "must be a GraphConcept")
        locator = _locator(value.locator, f"{path}.locator")
        if locator in seen:
            raise KnowledgeGraphError(f"{path}.locator", f"duplicates {locator!r}")
        seen.add(locator)
        kind = _name(value.concept_kind, f"{path}.concept_kind")
        source_path = (
            _relative_path(value.source_path, f"{path}.source_path")
            if value.source_path is not None
            else None
        )
        symbol = (
            _name(value.symbol, f"{path}.symbol")
            if value.symbol is not None
            else None
        )
        occurrence = value.occurrence
        if occurrence is not None:
            occurrence = _positive_int(occurrence, f"{path}.occurrence")
        page_id = (
            _name(value.page_id, f"{path}.page_id")
            if value.page_id is not None
            else None
        )
        concepts.append(
            GraphConcept(
                locator=locator,
                concept_kind=kind,
                source_path=source_path,
                symbol=symbol,
                occurrence=occurrence,
                page_id=page_id,
            )
        )
    concepts.sort(
        key=lambda value: (
            value.locator,
            value.source_path or "",
            value.symbol or "",
            value.occurrence or 0,
        )
    )
    return tuple(concepts)


def _graph_concept_payload(value: GraphConcept) -> dict[str, Any]:
    return {
        key: item
        for key, item in (
            ("locator", value.locator),
            ("concept_kind", value.concept_kind),
            ("source_path", value.source_path),
            ("symbol", value.symbol),
            ("occurrence", value.occurrence),
            ("page_id", value.page_id),
        )
        if item is not None
    }


def _normalise_edge(
    value: object,
    path: str,
    concept_kinds: Mapping[str, str] | None,
) -> dict[str, Any]:
    edge = _object(value, path)
    fields = {
        "key",
        "kind",
        "from",
        "target",
        "origin",
        "resolution",
        "evidence",
        "coverage",
    }
    _only_fields(edge, path, fields, required=fields)
    key = _hash(edge["key"], f"{path}.key")
    kind = _relationship_kind(edge["kind"], f"{path}.kind")
    source = _normalise_endpoint(edge["from"], f"{path}.from")
    target = _normalise_endpoint(edge["target"], f"{path}.target")
    if source["kind"] != "concept":
        raise KnowledgeGraphError(f"{path}.from.kind", "must be 'concept'")
    origin = _enum(edge["origin"], GRAPH_ORIGINS, f"{path}.origin")
    resolution = _enum(
        edge["resolution"],
        GRAPH_RESOLUTIONS,
        f"{path}.resolution",
    )
    _validate_resolution_target(target, resolution, f"{path}.target")
    evidence = _normalise_evidence(edge["evidence"], f"{path}.evidence")
    coverage = _normalise_coverage(edge["coverage"], f"{path}.coverage")
    if evidence["observed"] != coverage["observed"]:
        raise KnowledgeGraphError(
            f"{path}.evidence.observed",
            "must equal coverage.observed",
        )
    if evidence["emitted"] != coverage["emitted"]:
        raise KnowledgeGraphError(
            f"{path}.evidence.emitted",
            "must equal coverage.emitted",
        )
    if evidence["omitted"] != coverage["omitted"]:
        raise KnowledgeGraphError(
            f"{path}.evidence.omitted",
            "must equal coverage.omitted",
        )
    _validate_endpoint_concept_references(
        source,
        concept_kinds,
        f"{path}.from",
    )
    _validate_endpoint_concept_references(
        target,
        concept_kinds,
        f"{path}.target",
    )
    for sample_index, sample in enumerate(evidence["samples"]):
        for endpoint_name in ("source", "target"):
            endpoint = sample.get(endpoint_name)
            if endpoint is not None:
                _validate_endpoint_concept_references(
                    endpoint,
                    concept_kinds,
                    (
                        f"{path}.evidence.samples[{sample_index}]"
                        f".{endpoint_name}"
                    ),
                )
    identity = {
        "kind": kind,
        "from": source,
        "target": target,
        "origin": origin,
        "resolution": resolution,
    }
    expected_key = relationship_edge_key(identity)
    if key != expected_key:
        raise KnowledgeGraphError(
            f"{path}.key",
            f"does not match canonical edge identity; expected {expected_key!r}",
        )
    _validate_core_direction(
        kind,
        source,
        target,
        origin,
        resolution,
        evidence,
        path,
        concept_kinds,
    )
    return {
        "key": key,
        **identity,
        "evidence": evidence,
        "coverage": coverage,
    }


def _normalise_endpoint(value: object, path: str) -> dict[str, Any]:
    endpoint = _object(value, path)
    kind = _enum(endpoint.get("kind"), ENDPOINT_KINDS, f"{path}.kind")
    common = {"kind"}
    if kind == "concept":
        allowed = common | {"locator", "uid"}
        _only_fields(endpoint, path, allowed)
        present = [name for name in ("locator", "uid") if name in endpoint]
        if len(present) != 1:
            raise KnowledgeGraphError(
                path, "concept endpoints require exactly one of locator or uid"
            )
        if present[0] == "locator":
            return {"kind": kind, "locator": _locator(endpoint["locator"], f"{path}.locator")}
        return {"kind": kind, "uid": _name(endpoint["uid"], f"{path}.uid")}
    if kind == "source-symbol":
        allowed = common | {"source_path", "symbol"}
        _only_fields(
            endpoint,
            path,
            allowed,
            required={"source_path", "symbol"},
        )
        return {
            "kind": kind,
            "source_path": _relative_path(
                endpoint["source_path"], f"{path}.source_path"
            ),
            "symbol": _name(endpoint["symbol"], f"{path}.symbol"),
        }
    if kind == "external-resource":
        allowed = common | {"resource", "uri"}
        _only_fields(endpoint, path, allowed, required={"resource"})
        result = {
            "kind": kind,
            "resource": _name(endpoint["resource"], f"{path}.resource"),
        }
        if "uri" in endpoint:
            result["uri"] = _external_uri(endpoint["uri"], f"{path}.uri")
        return result

    allowed = common | {"raw_target", "candidates"}
    _only_fields(endpoint, path, allowed, required={"raw_target"})
    result: dict[str, Any] = {
        "kind": kind,
        "raw_target": _name(endpoint["raw_target"], f"{path}.raw_target"),
    }
    if "candidates" in endpoint:
        raw_candidates = _array(endpoint["candidates"], f"{path}.candidates")
        candidates = [
            _normalise_endpoint(candidate, f"{path}.candidates[{index}]")
            for index, candidate in enumerate(raw_candidates)
        ]
        if any(candidate["kind"] == "unresolved" for candidate in candidates):
            raise KnowledgeGraphError(
                f"{path}.candidates",
                "must not contain unresolved endpoints",
            )
        canonical = {_canonical_json(candidate): candidate for candidate in candidates}
        result["candidates"] = [canonical[key] for key in sorted(canonical)]
    return result


def _normalise_evidence(value: object, path: str) -> dict[str, Any]:
    evidence = _object(value, path)
    fields = {
        "state",
        "aggregate_input_hash",
        "observed",
        "unique",
        "emitted",
        "omitted",
        "samples",
    }
    _only_fields(evidence, path, fields, required=fields)
    state = _enum(
        evidence["state"],
        GRAPH_EVIDENCE_STATES,
        f"{path}.state",
    )
    aggregate_input_hash = _hash(
        evidence["aggregate_input_hash"],
        f"{path}.aggregate_input_hash",
    )
    observed = _nonnegative_int(evidence["observed"], f"{path}.observed")
    unique = _nonnegative_int(evidence["unique"], f"{path}.unique")
    emitted = _nonnegative_int(evidence["emitted"], f"{path}.emitted")
    omitted = _nonnegative_int(evidence["omitted"], f"{path}.omitted")
    samples_value = _array(evidence["samples"], f"{path}.samples")
    samples = [
        _normalise_evidence_sample(sample, f"{path}.samples[{index}]")
        for index, sample in enumerate(samples_value)
    ]
    canonical = [_canonical_json(sample) for sample in samples]
    if canonical != sorted(set(canonical)):
        raise KnowledgeGraphError(
            f"{path}.samples",
            "must be unique and canonically sorted",
        )
    if emitted != len(samples):
        raise KnowledgeGraphError(
            f"{path}.emitted", "must equal the number of evidence samples"
        )
    if unique < emitted or unique > observed:
        raise KnowledgeGraphError(
            f"{path}.unique", "must be between emitted and observed"
        )
    if omitted != observed - emitted:
        raise KnowledgeGraphError(
            f"{path}.omitted", "must equal observed minus emitted"
        )
    if observed and state != "present":
        raise KnowledgeGraphError(
            f"{path}.state", "must be 'present' when observations exist"
        )
    if not observed and state == "present":
        raise KnowledgeGraphError(
            f"{path}.state", "must not be 'present' without observations"
        )
    return {
        "state": state,
        "aggregate_input_hash": aggregate_input_hash,
        "observed": observed,
        "unique": unique,
        "emitted": emitted,
        "omitted": omitted,
        "samples": samples,
    }


def _normalise_evidence_sample(value: object, path: str) -> dict[str, Any]:
    sample = _object(value, path)
    fields = {
        "kind",
        "source",
        "target",
        "location",
        "detector",
        "reason",
        "attributes",
    }
    _only_fields(sample, path, fields, required={"kind"})
    kind = _open_name(sample["kind"], f"{path}.kind")
    result: dict[str, Any] = {"kind": kind}
    for endpoint_name in ("source", "target"):
        endpoint = sample.get(endpoint_name)
        if endpoint is not None:
            result[endpoint_name] = _normalise_endpoint(
                endpoint,
                f"{path}.{endpoint_name}",
            )
    if sample.get("location") is not None:
        result["location"] = _normalise_location(
            sample["location"],
            f"{path}.location",
        )
    if sample.get("detector") is not None:
        result["detector"] = _normalise_detector(
            sample["detector"],
            f"{path}.detector",
        )
    if sample.get("reason") is not None:
        result["reason"] = _name(sample["reason"], f"{path}.reason")
    if sample.get("attributes") is not None:
        attributes = _object(sample["attributes"], f"{path}.attributes")
        result["attributes"] = {
            _name(key, f"{path}.attributes key"): _json_value(
                attributes[key],
                f"{path}.attributes.{key}",
            )
            for key in sorted(attributes)
        }
    return result


def _normalise_location(value: object, path: str) -> dict[str, Any]:
    location = _object(value, path)
    fields = {"source_path", "line", "column", "end_line", "end_column"}
    _only_fields(location, path, fields, required={"source_path"})
    result: dict[str, Any] = {
        "source_path": _relative_path(
            location["source_path"],
            f"{path}.source_path",
        )
    }
    for name in ("line", "column", "end_line", "end_column"):
        raw = location.get(name)
        if raw is not None:
            result[name] = _positive_int(raw, f"{path}.{name}")
    if "end_line" in result and "line" not in result:
        raise KnowledgeGraphError(
            f"{path}.end_line", "requires a starting line"
        )
    if (
        "end_line" in result
        and result["end_line"] < result["line"]
    ):
        raise KnowledgeGraphError(
            f"{path}.end_line", "must not precede line"
        )
    return result


def _normalise_detector(value: object, path: str) -> dict[str, str]:
    detector = _object(value, path)
    fields = {"id", "version", "component"}
    _only_fields(detector, path, fields, required={"id", "version"})
    result = {
        "id": _name(detector["id"], f"{path}.id"),
        "version": _name(detector["version"], f"{path}.version"),
    }
    if detector.get("component") is not None:
        result["component"] = _name(
            detector["component"],
            f"{path}.component",
        )
    return result


def _normalise_coverage(
    value: object,
    path: str,
    *,
    include_analyzer: bool = False,
) -> dict[str, Any]:
    coverage = _object(value, path)
    fields = {
        "observed",
        "emitted",
        "omitted",
        "limit",
        "truncated",
        "limitations",
    }
    if not include_analyzer:
        _only_fields(coverage, path, fields, required=fields)
    observed = _nonnegative_int(coverage["observed"], f"{path}.observed")
    emitted = _nonnegative_int(coverage["emitted"], f"{path}.emitted")
    omitted = _nonnegative_int(coverage["omitted"], f"{path}.omitted")
    limit_value = coverage["limit"]
    limit = (
        None
        if limit_value is None
        else _positive_int(limit_value, f"{path}.limit")
    )
    truncated = coverage["truncated"]
    if not isinstance(truncated, bool):
        raise KnowledgeGraphError(f"{path}.truncated", "must be a boolean")
    limitations_value = _array(
        coverage["limitations"],
        f"{path}.limitations",
    )
    limitations = [
        _limitation(value, f"{path}.limitations[{index}]")
        for index, value in enumerate(limitations_value)
    ]
    if limitations != sorted(set(limitations)):
        raise KnowledgeGraphError(
            f"{path}.limitations",
            "must be unique and sorted",
        )
    if emitted > observed:
        raise KnowledgeGraphError(
            f"{path}.emitted", "must not exceed observed"
        )
    if omitted != observed - emitted:
        raise KnowledgeGraphError(
            f"{path}.omitted", "must equal observed minus emitted"
        )
    if truncated != (omitted > 0):
        raise KnowledgeGraphError(
            f"{path}.truncated",
            "must be true exactly when observations were omitted",
        )
    if limit is not None and emitted > limit:
        raise KnowledgeGraphError(
            f"{path}.emitted", "must not exceed limit"
        )
    return {
        "observed": observed,
        "emitted": emitted,
        "omitted": omitted,
        "limit": limit,
        "truncated": truncated,
        "limitations": limitations,
    }


def _normalise_input_hashes(value: object) -> dict[str, str]:
    hashes = _object(value, "typed_graph.input_hashes")
    expected = set(GRAPH_INPUT_NAMES) | {"aggregate"}
    _only_fields(
        hashes,
        "typed_graph.input_hashes",
        expected,
        required=expected,
    )
    result = {
        name: _hash(hashes[name], f"typed_graph.input_hashes.{name}")
        for name in sorted(hashes)
    }
    expected_aggregate = _aggregate_input_hash(
        {name: result[name] for name in GRAPH_INPUT_NAMES}
    )
    if result["aggregate"] != expected_aggregate:
        raise KnowledgeGraphError(
            "typed_graph.input_hashes.aggregate",
            "does not match the canonical component input hashes",
        )
    return result


def _normalise_analyzer_limitations(
    value: Mapping[str, Sequence[str]],
) -> dict[str, list[str]]:
    if not isinstance(value, Mapping):
        raise KnowledgeGraphError("analyzer_limitations", "must be an object")
    result: dict[str, list[str]] = {}
    for analyzer in sorted(value):
        analyzer_name = _name(analyzer, "analyzer_limitations key")
        raw_limitations = value[analyzer]
        if isinstance(raw_limitations, (str, bytes)) or not isinstance(
            raw_limitations,
            Sequence,
        ):
            raise KnowledgeGraphError(
                f"analyzer_limitations.{analyzer_name}",
                "must be a sequence of limitation codes",
            )
        result[analyzer_name] = sorted(
            {
                _limitation(
                    limitation,
                    f"analyzer_limitations.{analyzer_name}[]",
                )
                for limitation in raw_limitations
            }
        )
    return result


def _validate_graph_bindings(
    input_hashes: Mapping[str, str],
    coverage: Sequence[Mapping[str, Any]],
    edges: Sequence[Mapping[str, Any]],
) -> None:
    coverage_by_analyzer = {
        str(record["analyzer"]): record for record in coverage
    }
    if set(coverage_by_analyzer) != set(GRAPH_COVERAGE_ANALYZERS):
        missing = sorted(set(GRAPH_COVERAGE_ANALYZERS) - set(coverage_by_analyzer))
        extra = sorted(set(coverage_by_analyzer) - set(GRAPH_COVERAGE_ANALYZERS))
        details = []
        if missing:
            details.append("missing " + ", ".join(missing))
        if extra:
            details.append("unexpected " + ", ".join(extra))
        raise KnowledgeGraphError(
            "typed_graph.coverage",
            "must contain exactly the structural analyzers"
            + (f" ({'; '.join(details)})" if details else ""),
        )

    emitted_by_analyzer = {
        analyzer: 0 for analyzer in GRAPH_COVERAGE_ANALYZERS
    }
    component_hashes = {
        input_hashes[name] for name in GRAPH_INPUT_NAMES
    }
    for index, edge in enumerate(edges):
        path = f"typed_graph.edges[{index}]"
        kind = str(edge["kind"])
        analyzer = _CORE_KIND_ANALYZERS.get(kind)
        evidence_hash = edge["evidence"]["aggregate_input_hash"]
        if analyzer is not None:
            expected_hash = input_hashes[analyzer]
            if evidence_hash != expected_hash:
                raise KnowledgeGraphError(
                    f"{path}.evidence.aggregate_input_hash",
                    f"must match typed_graph.input_hashes.{analyzer}",
                )
            emitted_by_analyzer[analyzer] += edge["evidence"]["observed"]
        elif evidence_hash not in component_hashes:
            raise KnowledgeGraphError(
                f"{path}.evidence.aggregate_input_hash",
                "must match one of the graph component input hashes",
            )

    edge_analyzers = set(_CORE_KIND_ANALYZERS.values())
    for analyzer, emitted in emitted_by_analyzer.items():
        if analyzer not in edge_analyzers:
            continue
        if coverage_by_analyzer[analyzer]["emitted"] != emitted:
            raise KnowledgeGraphError(
                f"typed_graph.coverage.{analyzer}.emitted",
                "must equal the observations materialized into typed edges",
            )


def _validate_resolution_target(
    target: Mapping[str, Any],
    resolution: str,
    path: str,
) -> None:
    kind = target["kind"]
    if resolution == "resolved" and kind != "concept":
        raise KnowledgeGraphError(path, "resolved edges require a concept target")
    if resolution == "external" and kind != "external-resource":
        raise KnowledgeGraphError(
            path, "external edges require an external-resource target"
        )
    if resolution in {"ambiguous", "unresolved"} and kind != "unresolved":
        raise KnowledgeGraphError(
            path,
            f"{resolution} edges require an unresolved raw target",
        )


def _validate_core_direction(
    kind: str,
    source: Mapping[str, Any],
    target: Mapping[str, Any],
    origin: str,
    resolution: str,
    evidence: Mapping[str, Any],
    path: str,
    concept_kinds: Mapping[str, str] | None,
) -> None:
    if kind not in CORE_RELATIONSHIP_KINDS:
        return
    kinds_known = concept_kinds is not None
    source_kind = _endpoint_concept_kind(source, concept_kinds)
    target_kind = _endpoint_concept_kind(target, concept_kinds)
    if kind == "contains":
        _require_direction(
            (
                _concept_kind_allowed(
                    source,
                    source_kind,
                    {"source-module"},
                    kinds_known=kinds_known,
                )
                and _concept_kind_allowed(
                    target,
                    target_kind,
                    {"code-entity"},
                    kinds_known=kinds_known,
                )
            )
            and resolution == "resolved",
            path,
            "contains requires source-module -> resolved code-entity",
        )
        _require_origin(origin, {"extracted", "inferred"}, path)
        _require_core_evidence(
            evidence,
            sample_kind="containment",
            required_fields={"source", "target"},
            path=path,
        )
    elif kind == "imports":
        _require_direction(
            _concept_kind_allowed(
                source,
                source_kind,
                {"source-module"},
                kinds_known=kinds_known,
            )
            and (
                resolution != "resolved"
                or _concept_kind_allowed(
                    target,
                    target_kind,
                    {"source-module"},
                    kinds_known=kinds_known,
                )
            ),
            path,
            "imports requires a source-module owner and resolved module target",
        )
        _require_origin(origin, {"extracted", "inferred"}, path)
        _require_core_evidence(
            evidence,
            sample_kind="import",
            required_fields={"source", "target"},
            path=path,
        )
    elif kind == "calls":
        _require_direction(
            _concept_kind_allowed(
                source,
                source_kind,
                {"source-module", "code-entity"},
                kinds_known=kinds_known,
            )
            and (
                resolution != "resolved"
                or _concept_kind_allowed(
                    target,
                    target_kind,
                    {"source-module", "code-entity"},
                    kinds_known=kinds_known,
                )
            ),
            path,
            "calls requires callable-owner concepts",
        )
        _require_origin(origin, {"extracted", "inferred"}, path)
        _require_core_evidence(
            evidence,
            sample_kind="call",
            required_fields={"source", "target"},
            path=path,
        )
    elif kind == "entrypoint_for":
        _require_direction(
            _concept_kind_allowed(
                source,
                source_kind,
                {"source-module", "code-entity"},
                kinds_known=kinds_known,
            )
            and (
                resolution != "resolved"
                or _concept_kind_allowed(
                    target,
                    target_kind,
                    {"user-flow"},
                    kinds_known=kinds_known,
                )
            ),
            path,
            "entrypoint_for requires callable owner -> resolved user-flow",
        )
        _require_origin(origin, {"extracted", "inferred"}, path)
        _require_core_evidence(
            evidence,
            sample_kind="entrypoint",
            required_fields={"source", "target", "detector"},
            path=path,
        )
    elif kind in {"reads", "writes"}:
        _require_direction(
            _concept_kind_allowed(
                source,
                source_kind,
                {"source-module", "code-entity", "workflow", "user-flow"},
                kinds_known=kinds_known,
            ),
            path,
            f"{kind} requires a flow or callable owner",
        )
        _require_origin(origin, {"extracted", "inferred"}, path)
        _require_core_evidence(
            evidence,
            sample_kind="data-effect",
            required_fields={"source", "target"},
            path=path,
        )
    elif kind == "depends_on":
        _require_direction(
            resolution == "external" and target["kind"] == "external-resource",
            path,
            "depends_on is reserved for explicit external dependencies",
        )
        _require_origin(origin, {"extracted", "inferred"}, path)
        _require_core_evidence(
            evidence,
            sample_kind="dependency",
            required_fields={"source", "target"},
            path=path,
        )
    elif kind == "supersedes":
        _require_origin(origin, {"governance"}, path)
        _require_direction(
            resolution == "resolved" and target["kind"] == "concept",
            path,
            "supersedes requires a resolved successor concept",
        )
        _require_core_evidence(
            evidence,
            sample_kind="supersession",
            required_fields={"source", "target", "reason"},
            path=path,
        )


def _endpoint_concept_kind(
    endpoint: Mapping[str, Any],
    concept_kinds: Mapping[str, str] | None,
) -> str | None:
    if (
        concept_kinds is None
        or endpoint.get("kind") != "concept"
        or "locator" not in endpoint
    ):
        return None
    locator = endpoint["locator"]
    return concept_kinds.get(locator)


def _concept_kind_allowed(
    endpoint: Mapping[str, Any],
    actual_kind: str | None,
    allowed: set[str],
    *,
    kinds_known: bool,
) -> bool:
    if not kinds_known:
        return True
    if endpoint.get("kind") == "concept" and "uid" in endpoint:
        # Stable UID resolution belongs to the governance layer. The endpoint
        # is valid, but its concept kind cannot yet be checked against this
        # locator-only projection.
        return True
    return actual_kind in allowed


def _validate_endpoint_concept_references(
    endpoint: Mapping[str, Any],
    concept_kinds: Mapping[str, str] | None,
    path: str,
) -> None:
    if concept_kinds is None:
        return
    if endpoint.get("kind") == "concept" and "locator" in endpoint:
        locator = endpoint["locator"]
        if locator not in concept_kinds:
            raise KnowledgeGraphError(
                f"{path}.locator",
                f"does not reference a knowledge concept: {locator!r}",
            )
    candidates = endpoint.get("candidates")
    if isinstance(candidates, Sequence) and not isinstance(
        candidates,
        (str, bytes),
    ):
        for index, candidate in enumerate(candidates):
            if isinstance(candidate, Mapping):
                _validate_endpoint_concept_references(
                    candidate,
                    concept_kinds,
                    f"{path}.candidates[{index}]",
                )


def _require_direction(condition: bool, path: str, message: str) -> None:
    if not condition:
        raise KnowledgeGraphError(f"{path}.kind", message)


def _require_origin(origin: str, allowed: set[str], path: str) -> None:
    if origin not in allowed:
        raise KnowledgeGraphError(
            f"{path}.origin",
            f"must be one of {', '.join(sorted(allowed))} for this core kind",
        )


def _require_core_evidence(
    evidence: Mapping[str, Any],
    *,
    sample_kind: str,
    required_fields: set[str],
    path: str,
) -> None:
    samples = evidence["samples"]
    if not samples:
        raise KnowledgeGraphError(
            f"{path}.evidence.samples",
            f"core relationship evidence requires {sample_kind!r} samples",
        )
    for index, sample in enumerate(samples):
        sample_path = f"{path}.evidence.samples[{index}]"
        if sample.get("kind") != sample_kind:
            raise KnowledgeGraphError(
                f"{sample_path}.kind",
                f"must be {sample_kind!r} for this core relationship",
            )
        missing = sorted(required_fields - set(sample))
        if missing:
            raise KnowledgeGraphError(
                sample_path,
                "requires " + ", ".join(missing),
            )


def _observation_collection(
    value: Mapping[str, Any] | Sequence[Mapping[str, Any]],
    path: str,
) -> tuple[list[Any], Mapping[str, Any] | None]:
    if isinstance(value, Mapping):
        observations = value.get("observations", [])
        if not isinstance(observations, list):
            raise KnowledgeGraphError(f"{path}.observations", "must be an array")
        coverage = value.get("coverage")
        if coverage is not None and not isinstance(coverage, Mapping):
            raise KnowledgeGraphError(f"{path}.coverage", "must be an object")
        return list(observations), coverage
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        return list(value), None
    raise KnowledgeGraphError(path, "must be an observation bundle or sequence")


def _observation_bundle_for_hash(
    value: Mapping[str, Any] | Sequence[Mapping[str, Any]],
    path: str,
) -> Any:
    if isinstance(value, Mapping):
        normalized = _json_value(value, path)
        observations = normalized.get("observations")
        if isinstance(observations, list):
            normalized["observations"] = sorted(
                observations,
                key=_canonical_json,
            )
        coverage = normalized.get("coverage")
        if isinstance(coverage, Mapping):
            limitations = coverage.get("limitations")
            if isinstance(limitations, list):
                coverage["limitations"] = sorted(set(limitations))
        return normalized
    return _sorted_json_records(value, path)


def _sorted_json_records(
    values: Sequence[Mapping[str, Any]],
    path: str,
) -> list[Any]:
    if isinstance(values, (str, bytes, Mapping)) or not isinstance(
        values, Sequence
    ):
        raise KnowledgeGraphError(path, "must be a sequence")
    normalized = [
        _json_value(value, f"{path}[{index}]")
        for index, value in enumerate(values)
    ]
    return sorted(normalized, key=_canonical_json)


def _coverage_from_supplied(
    supplied: Mapping[str, Any] | None,
    *,
    fallback_observed: int,
    emitted: int,
    limitations: Sequence[str],
) -> dict[str, Any]:
    observed = fallback_observed
    limit: int | None = None
    inherited: list[str] = []
    if supplied is not None:
        raw_observed = supplied.get("observed")
        if isinstance(raw_observed, int) and not isinstance(raw_observed, bool):
            observed = max(raw_observed, fallback_observed)
        raw_limit = supplied.get("limit")
        if isinstance(raw_limit, int) and not isinstance(raw_limit, bool) and raw_limit > 0:
            limit = raw_limit
        raw_limitations = supplied.get("limitations")
        if isinstance(raw_limitations, list):
            inherited = [
                str(value) for value in raw_limitations if isinstance(value, str)
            ]
    return _coverage(
        observed,
        emitted,
        limit=limit,
        limitations=(*limitations, *inherited),
    )


def _coverage(
    observed: int,
    emitted: int,
    *,
    limit: int | None,
    limitations: Iterable[str],
) -> dict[str, Any]:
    safe_observed = max(observed, emitted)
    normalized_limitations = sorted(
        {
            _limitation(value, "coverage.limitations[]")
            for value in limitations
        }
    )
    return {
        "observed": safe_observed,
        "emitted": emitted,
        "omitted": safe_observed - emitted,
        "limit": limit,
        "truncated": safe_observed > emitted,
        "limitations": normalized_limitations,
    }


def _limitations(inputs: KnowledgeGraphInputs, analyzer: str) -> tuple[str, ...]:
    values = inputs.analyzer_limitations.get(analyzer, ())
    if isinstance(values, (str, bytes)) or not isinstance(values, Sequence):
        raise KnowledgeGraphError(
            f"analyzer_limitations.{analyzer}",
            "must be a sequence of limitation codes",
        )
    return tuple(
        _limitation(value, f"analyzer_limitations.{analyzer}[]")
        for value in values
    )


def _line_location(source_path: str, value: object) -> dict[str, Any]:
    location: dict[str, Any] = {
        "source_path": _relative_path(source_path, "location.source_path")
    }
    if isinstance(value, int) and not isinstance(value, bool) and value > 0:
        location["line"] = value
    return location


def _external_import_resource(module: str, name: str) -> str:
    raw = module or name or "unknown"
    root = raw.lstrip(".").split(".", 1)[0]
    return f"package:{root or raw}"


def _effect_resource(effect: Mapping[str, Any]) -> str:
    for key in ("target", "name", "value", "resource", "kind"):
        value = effect.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return "unknown"


def _aggregate_input_hash(input_hashes: Mapping[str, str]) -> str:
    components = {
        name: input_hashes[name] for name in sorted(input_hashes)
    }
    return sha256_bytes(_canonical_json(components).encode("utf-8"))


def _canonical_json(value: object) -> str:
    try:
        return canonical_json_text(value)
    except (OverflowError, RecursionError, TypeError, ValueError) as exc:
        raise KnowledgeGraphError("value", "must be finite canonical JSON") from exc


def _json_value(
    value: object,
    path: str,
    *,
    depth: int = 0,
    allow_control_strings: bool = False,
) -> Any:
    if depth > 64:
        raise KnowledgeGraphError(path, "exceeds the maximum nesting depth")
    if value is None or isinstance(value, (bool, int, str)):
        if (
            isinstance(value, str)
            and not allow_control_strings
            and _CONTROL_RE.search(value)
        ):
            raise KnowledgeGraphError(path, "must not contain control characters")
        return value
    if isinstance(value, float):
        if not math.isfinite(value):
            raise KnowledgeGraphError(path, "must be finite")
        return value
    if isinstance(value, Mapping):
        result: dict[str, Any] = {}
        for key in sorted(value, key=str):
            if not isinstance(key, str):
                raise KnowledgeGraphError(path, "object keys must be strings")
            _name(key, f"{path} key")
            result[key] = _json_value(
                value[key],
                f"{path}.{key}",
                depth=depth + 1,
                allow_control_strings=allow_control_strings,
            )
        return result
    if isinstance(value, (list, tuple)):
        return [
            _json_value(
                item,
                f"{path}[{index}]",
                depth=depth + 1,
                allow_control_strings=allow_control_strings,
            )
            for index, item in enumerate(value)
        ]
    raise KnowledgeGraphError(path, f"unsupported JSON value {type(value).__name__}")


def _object(value: object, path: str) -> dict[str, Any]:
    selected = require_mapping(
        value,
        error=KnowledgeGraphError(path, "must be an object"),
        require_string_keys=True,
        key_error=KnowledgeGraphError(path, "object keys must be strings"),
    )
    return dict(selected)


def _array(value: object, path: str) -> list[Any]:
    return require_list(
        value,
        error=KnowledgeGraphError(path, "must be an array"),
    )


def _only_fields(
    value: Mapping[str, Any],
    path: str,
    allowed: set[str],
    *,
    required: set[str] = frozenset(),
) -> None:
    return require_shared_exact_fields(
        value,
        allowed=allowed,
        required=required,
        mapping_error=KnowledgeGraphError(path, "must be an object"),
        missing_error=lambda fields: KnowledgeGraphError(
            f"{path}.{fields[0]}", "is required"
        ),
        unknown_error=lambda fields: KnowledgeGraphError(
            f"{path}.{fields[0]}", "unknown field"
        ),
        unknown_first=True,
    )


def _enum(value: object, values: Sequence[str], path: str) -> str:
    error = KnowledgeGraphError(
        path,
        f"must be one of {', '.join(repr(item) for item in values)}",
    )
    return require_choice(
        value,
        values,
        text_error=error,
        choice_error=lambda _allowed: error,
        reject_control_characters=False,
    )


def _relationship_kind(value: object, path: str) -> str:
    result = _open_name(value, path)
    if not is_supported_relationship_kind(result):
        raise KnowledgeGraphError(
            path,
            "unknown kinds must use a namespace/name spelling",
        )
    return result


def _open_name(value: object, path: str) -> str:
    result = _name(value, path)
    if "/" in result and not _QUALIFIED_NAME_RE.fullmatch(result):
        raise KnowledgeGraphError(path, "qualified names must use namespace/name")
    return result


def _name(value: object, path: str) -> str:
    return require_nonempty_text(
        value,
        error=KnowledgeGraphError(
            path,
            "must be a non-empty normalized string without control characters",
        ),
        require_trimmed=True,
        reject_delete_character=True,
    )


def _relative_path(value: object, path: str) -> str:
    result = _name(value, path)
    return require_repository_relative_path(
        result,
        text_error=KnowledgeGraphError(
            path,
            "must be a non-empty normalized string without control characters",
        ),
        posix_error=KnowledgeGraphError(
            path, "must be a repository-relative POSIX path"
        ),
        normalized_error=KnowledgeGraphError(
            path, "must be a normalized relative path"
        ),
        normalize_posix_spelling=True,
    )


def _locator(value: object, path: str) -> str:
    result = _name(value, path)
    try:
        validated = validate_exact_page_coordinate(result)
    except WikiSurfaceError as exc:
        raise KnowledgeGraphError(path, "must be an exact LLM Wiki locator") from exc
    if not validated.startswith("llm-wiki://"):
        raise KnowledgeGraphError(path, "must use the llm-wiki URI form")
    return validated


def _external_uri(value: object, path: str) -> str:
    result = _name(value, path)
    if not _URI_RE.match(result):
        raise KnowledgeGraphError(path, "must be an absolute URI")
    if contains_uri_authority_userinfo(result):
        raise KnowledgeGraphError(path, "must not contain URI credentials")
    parsed = urlsplit(result)
    if not parsed.scheme:
        raise KnowledgeGraphError(path, "must include a URI scheme")
    return result


def _hash(value: object, path: str) -> str:
    return require_sha256(
        value,
        digest_error=KnowledgeGraphError(path, "must be a sha256: digest"),
    )


def _limitation(value: object, path: str) -> str:
    result = _name(value, path)
    if not _LIMITATION_RE.fullmatch(result):
        raise KnowledgeGraphError(path, "must be a stable lowercase limitation code")
    return result


def _nonnegative_int(value: object, path: str) -> int:
    return require_nonnegative_int(
        value,
        error=KnowledgeGraphError(path, "must be a non-negative integer"),
    )


def _positive_int(value: object, path: str) -> int:
    error = KnowledgeGraphError(path, "must be a positive integer")
    return require_positive_int(value, invalid_error=error, zero_error=error)


__all__ = [
    "CORE_RELATIONSHIP_KINDS",
    "DEFAULT_EVIDENCE_LIMIT",
    "EMITTED_RELATIONSHIP_KINDS",
    "ENDPOINT_KINDS",
    "GRAPH_EVIDENCE_STATES",
    "GRAPH_INPUT_NAMES",
    "GRAPH_ORIGINS",
    "GRAPH_RESOLUTIONS",
    "GraphConcept",
    "KnowledgeGraphError",
    "KnowledgeGraphInputs",
    "concept_endpoint",
    "external_resource_endpoint",
    "materialize_typed_graph",
    "is_supported_relationship_kind",
    "relationship_edge_key",
    "serialize_typed_graph",
    "source_symbol_endpoint",
    "typed_graph_from_knowledge_extensions",
    "unresolved_endpoint",
    "validate_typed_graph",
]
