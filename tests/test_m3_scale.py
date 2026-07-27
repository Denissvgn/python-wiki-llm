"""Focused scale checks for bounded typed-graph materialization and reads."""

from __future__ import annotations

import json
from dataclasses import replace

from llm_wiki_cli.services.contracts import TYPED_GRAPH_EXTENSION_KEY
from llm_wiki_cli.services.documentation_queries import (
    DocumentationGraphQueryService,
)
from llm_wiki_cli.services.knowledge_graph import (
    GraphConcept,
    KnowledgeGraphInputs,
    materialize_typed_graph,
)
from tests.test_knowledge_queries import (
    MODULE_LOCATOR,
    SOURCE_PATH,
    _ready_view,
)


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


def _stress_graph(view, *, reverse: bool):
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
        for line in range(1, 201)
    ]
    dependencies = [
        {
            "source_path": SOURCE_PATH,
            "package": f"package-{index:04d}",
            "explicit": True,
            "reason": "declared dependency",
        }
        for index in range(300)
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
            evidence_limit=3,
        )
    )


def _service(view, graph, *, limit: int) -> DocumentationGraphQueryService:
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


def test_high_fanout_graph_keeps_evidence_and_query_output_bounded(tmp_path):
    view = _ready_view(tmp_path)
    ordered_graph = _stress_graph(view, reverse=False)
    reversed_graph = _stress_graph(view, reverse=True)

    assert ordered_graph == reversed_graph

    ordered = _service(view, ordered_graph, limit=7)
    reversed_service = _service(view, reversed_graph, limit=7)
    outgoing = ordered.traverse_typed_graph(
        MODULE_LOCATOR,
        direction="outgoing",
        kinds=["depends_on"],
    )
    shuffled_outgoing = reversed_service.traverse_typed_graph(
        MODULE_LOCATOR,
        direction="outgoing",
        kinds=["depends_on"],
    )

    assert outgoing == shuffled_outgoing
    assert outgoing["bounds"]["edges"] == {
        "total": 300,
        "returned": 7,
        "truncated": True,
    }
    assert len(json.dumps(outgoing, sort_keys=True).encode("utf-8")) < 20_000

    calls = ordered.traverse_typed_graph(
        "llm-wiki://entities/AccountService",
        direction="outgoing",
        kinds=["calls"],
        include_evidence=True,
    )
    evidence = calls["edges"][0]["evidence"]
    assert calls["bounds"]["edges"] == {
        "total": 1,
        "returned": 1,
        "truncated": False,
    }
    assert evidence["observed"] == 200
    assert evidence["unique"] == 200
    assert evidence["emitted"] == 3
    assert evidence["omitted"] == 197
    assert len(evidence["samples"]) == 3
    assert len(json.dumps(calls, sort_keys=True).encode("utf-8")) < 20_000
