"""Deterministic M3 graph scale-gate measurement and record rendering."""

from __future__ import annotations

import json
import tempfile
from dataclasses import replace
from pathlib import Path
from typing import Any, Mapping

from llm_wiki_cli import __version__
from llm_wiki_cli.services.contracts import (
    SECTION_OWNERSHIP_EXTENSION_KEY,
    TYPED_GRAPH_EXTENSION_KEY,
)
from llm_wiki_cli.services.documentation_queries import (
    DocumentationGraphQueryService,
)
from llm_wiki_cli.services.knowledge_evidence import (
    canonical_json_bytes,
    sha256_bytes,
)
from llm_wiki_cli.services.knowledge_graph import (
    GraphConcept,
    KnowledgeGraphInputs,
    materialize_typed_graph,
)
from llm_wiki_cli.services.knowledge_model import serialize_knowledge_index
from llm_wiki_cli.services.section_ownership import (
    observe_page_sections,
    section_ownership_extension,
)
from llm_wiki_cli.services.wiki_surface import PageKind
from tests.test_knowledge_queries import (
    MODULE_LOCATOR,
    SOURCE_PATH,
    _ready_view,
)

M3_SCALE_GATE_SCHEMA_VERSION = "llm-wiki-m3-scale-gate/v1"
M3_SCALE_GATE_RECORD_PATH = (
    Path(__file__).parent / "records" / "knowledge" / "m3-scale-gate.json"
)

CALL_OBSERVATION_COUNT = 200
DEPENDENCY_OBSERVATION_COUNT = 300
EVIDENCE_LIMIT = 3
QUERY_LIMIT = 7

MAX_GRAPH_BYTES = 1_000_000
MAX_INDEX_BYTES = 2_000_000
MAX_QUERY_BYTES = 20_000

SECTION_FIXTURE_MARKDOWN = """# User
## Description
Human meaning.
## Attributes
| Name | Type | Description |
|---|---|---|
| `name` | `str` | Human meaning |
## Relationships
Generated relationship summary.
## Description
Duplicate human prose.
## Custom
Unknown ownership.
"""
SECTION_FIXTURE_LOCATOR = "llm-wiki://entities/User"


def _concept_map(view) -> tuple[GraphConcept, ...]:
    assert view.knowledge is not None
    concepts = []
    for concept in view.knowledge.concepts:
        basis = concept.facets.structure.basis
        source_path = basis.source_path if basis is not None else None
        concept_kind = getattr(
            concept.concept_kind,
            "value",
            concept.concept_kind,
        )
        concepts.append(
            GraphConcept(
                locator=concept.locator,
                concept_kind=concept_kind,
                source_path=source_path,
                symbol=concept.title if concept_kind == "code-entity" else None,
                page_id=concept.document.page_id,
            )
        )
    return tuple(concepts)


def build_stress_graph(view, *, reverse: bool):
    """Materialize the fixed high-fanout graph in either input order."""

    calls = [
        {
            "from": {
                "file": SOURCE_PATH,
                "symbol": "AccountService.create",
            },
            "to": {"file": SOURCE_PATH, "symbol": "User"},
            "name": "User",
            "kind": "internal",
            "line": line,
        }
        for line in range(1, CALL_OBSERVATION_COUNT + 1)
    ]
    dependencies = [
        {
            "source_path": SOURCE_PATH,
            "package": f"package-{index:04d}",
            "explicit": True,
            "reason": "declared dependency",
        }
        for index in range(DEPENDENCY_OBSERVATION_COUNT)
    ]
    if reverse:
        calls.reverse()
        dependencies.reverse()
    return materialize_typed_graph(
        KnowledgeGraphInputs(
            inventory={SOURCE_PATH: {"language": "python"}},
            concepts=_concept_map(view),
            call_edges=calls,
            external_dependencies=dependencies,
            evidence_limit=EVIDENCE_LIMIT,
        )
    )


def _with_section_ownership(view):
    assert view.knowledge is not None
    observed = observe_page_sections(
        SECTION_FIXTURE_MARKDOWN,
        SECTION_FIXTURE_LOCATOR,
        PageKind.ENTITIES,
    )
    knowledge = replace(
        view.knowledge,
        extensions={
            **view.knowledge.extensions,
            **section_ownership_extension([observed]),
        },
    )
    return replace(view, knowledge=knowledge)


def build_stress_service(
    view,
    graph,
    *,
    limit: int = QUERY_LIMIT,
) -> DocumentationGraphQueryService:
    """Build the bounded public query service over the stress graph."""

    assert view.knowledge is not None
    knowledge = replace(
        view.knowledge,
        extensions={
            **view.knowledge.extensions,
            TYPED_GRAPH_EXTENSION_KEY: graph,
        },
    )
    return DocumentationGraphQueryService(
        {},
        limit=limit,
        knowledge_view=replace(view, knowledge=knowledge),
    )


def _edge_counts(graph: Mapping[str, Any]) -> dict[str, Any]:
    by_kind: dict[str, int] = {}
    for edge in graph["edges"]:
        kind = str(edge["kind"])
        by_kind[kind] = by_kind.get(kind, 0) + 1
    return {
        "total": len(graph["edges"]),
        "by_kind": {kind: by_kind[kind] for kind in sorted(by_kind)},
    }


def _evidence_counts(graph: Mapping[str, Any]) -> dict[str, Any]:
    fields = ("observed", "unique", "emitted", "omitted")
    totals = {field: 0 for field in fields}
    by_kind: dict[str, dict[str, int]] = {}
    for edge in graph["edges"]:
        kind = str(edge["kind"])
        evidence = edge["evidence"]
        kind_counts = by_kind.setdefault(
            kind,
            {"edges": 0, **{field: 0 for field in fields}},
        )
        kind_counts["edges"] += 1
        for field in fields:
            value = int(evidence[field])
            kind_counts[field] += value
            totals[field] += value
    return {
        **totals,
        "by_kind": {kind: by_kind[kind] for kind in sorted(by_kind)},
    }


def _section_counts(knowledge) -> dict[str, Any]:
    extension = knowledge.extensions[SECTION_OWNERSHIP_EXTENSION_KEY]
    by_ownership: dict[str, int] = {}
    total = 0
    for page in extension["pages"]:
        for section in page["sections"]:
            ownership = str(section["ownership"])
            by_ownership[ownership] = by_ownership.get(ownership, 0) + 1
            total += 1
    return {
        "pages": len(extension["pages"]),
        "total": total,
        "by_ownership": {
            ownership: by_ownership[ownership]
            for ownership in sorted(by_ownership)
        },
    }


def _serialized_measurement(value: object) -> dict[str, Any]:
    payload = canonical_json_bytes(value)
    return {
        "serialized_bytes": len(payload),
        "sha256": sha256_bytes(payload),
    }


def _budget(*, observed: int, maximum: int) -> dict[str, int | bool]:
    return {
        "observed": observed,
        "maximum": maximum,
        "passed": observed <= maximum,
    }


def build_m3_scale_gate_record(
    fixture_root: Path,
    *,
    reverse: bool = False,
) -> dict[str, Any]:
    """Measure the fixed fixture without recording its temporary location."""

    view = _with_section_ownership(_ready_view(fixture_root))
    assert view.knowledge is not None
    graph = build_stress_graph(view, reverse=reverse)
    knowledge = replace(
        view.knowledge,
        extensions={
            **view.knowledge.extensions,
            TYPED_GRAPH_EXTENSION_KEY: graph,
        },
    )
    service = build_stress_service(view, graph)
    depends_on = service.traverse_typed_graph(
        MODULE_LOCATOR,
        direction="outgoing",
        kinds=["depends_on"],
    )
    calls_with_evidence = service.traverse_typed_graph(
        "llm-wiki://entities/AccountService",
        direction="outgoing",
        kinds=["calls"],
        include_evidence=True,
    )

    graph_measurement = _serialized_measurement(graph)
    index_bytes = serialize_knowledge_index(knowledge).encode("utf-8")
    index_measurement = {
        "serialized_bytes": len(index_bytes),
        "sha256": sha256_bytes(index_bytes),
    }
    query_measurements = {
        "calls_with_evidence": {
            **_serialized_measurement(calls_with_evidence),
            "bounds": calls_with_evidence["bounds"]["edges"],
            "include_evidence": True,
        },
        "depends_on": {
            **_serialized_measurement(depends_on),
            "bounds": depends_on["bounds"]["edges"],
            "include_evidence": False,
        },
    }
    budgets = {
        "calls_query_payload_bytes": _budget(
            observed=query_measurements["calls_with_evidence"][
                "serialized_bytes"
            ],
            maximum=MAX_QUERY_BYTES,
        ),
        "depends_on_query_payload_bytes": _budget(
            observed=query_measurements["depends_on"]["serialized_bytes"],
            maximum=MAX_QUERY_BYTES,
        ),
        "graph_serialized_bytes": _budget(
            observed=graph_measurement["serialized_bytes"],
            maximum=MAX_GRAPH_BYTES,
        ),
        "knowledge_index_serialized_bytes": _budget(
            observed=index_measurement["serialized_bytes"],
            maximum=MAX_INDEX_BYTES,
        ),
    }
    return {
        "schema_version": M3_SCALE_GATE_SCHEMA_VERSION,
        "record_kind": "internal-scale-gate",
        "fixture": {
            "name": "m3-high-fanout-v1",
            "source_path": SOURCE_PATH,
            "call_observations": {
                "count": CALL_OBSERVATION_COUNT,
                "first_line": 1,
                "last_line": CALL_OBSERVATION_COUNT,
                "source_symbol": "AccountService.create",
                "target_symbol": "User",
            },
            "external_dependencies": {
                "count": DEPENDENCY_OBSERVATION_COUNT,
                "name_pattern": "package-{index:04d}",
            },
            "section_ownership": {
                "page_locator": SECTION_FIXTURE_LOCATOR,
                "headings": [
                    "User",
                    "Description",
                    "Attributes",
                    "Relationships",
                    "Description",
                    "Custom",
                ],
            },
            "input_order_variants": ["ascending", "reversed"],
        },
        "limits": {
            "edge_evidence_samples": EVIDENCE_LIMIT,
            "query_edges": QUERY_LIMIT,
        },
        "environment": {
            "execution": "synthetic deterministic fixture",
            "filesystem": "temporary fixture directory",
            "network": "not used",
            "python": "project-supported Python >=3.10",
            "serialization": "UTF-8 deterministic JSON",
            "tool": f"agent-wiki-cli {__version__}",
        },
        "measurements": {
            "concepts": len(knowledge.concepts),
            "edges": _edge_counts(graph),
            "sections": _section_counts(knowledge),
            "graph": graph_measurement,
            "knowledge_index": index_measurement,
            "evidence": _evidence_counts(graph),
            "analyzer_coverage": graph["coverage"],
            "queries": query_measurements,
        },
        "budgets": budgets,
        "result": (
            "pass"
            if all(check["passed"] for check in budgets.values())
            else "fail"
        ),
        "reproduce": ".venv/bin/python -m tests.knowledge_m3_scale_gate",
    }


def _main() -> None:
    with tempfile.TemporaryDirectory(prefix="llm-wiki-m3-scale-gate-") as temp:
        record = build_m3_scale_gate_record(Path(temp))
    print(json.dumps(record, indent=2, sort_keys=True))


if __name__ == "__main__":
    _main()


__all__ = [
    "M3_SCALE_GATE_RECORD_PATH",
    "M3_SCALE_GATE_SCHEMA_VERSION",
    "build_m3_scale_gate_record",
    "build_stress_graph",
    "build_stress_service",
]
