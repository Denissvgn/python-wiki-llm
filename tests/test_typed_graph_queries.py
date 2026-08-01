"""Persisted typed-graph query, API, and MCP consumer tests."""

from __future__ import annotations

import json
from dataclasses import replace

import pytest

import llm_wiki_cli.api as api
from llm_wiki_cli.services import mcp_server
from llm_wiki_cli.services.contracts import TYPED_GRAPH_EXTENSION_KEY
from llm_wiki_cli.services.documentation_queries import (
    DocumentationGraphQueryService,
    DocumentationQueryError,
)
from llm_wiki_cli.services.knowledge_graph import (
    GraphConcept,
    KnowledgeGraphInputs,
    materialize_typed_graph,
    relationship_edge_key,
)
from tests.test_knowledge_queries import (
    MODULE_LOCATOR,
    SOURCE_PATH,
    USER_LOCATOR,
    _ready_view,
)


def _graph_view(tmp_path, *, reverse_edges: bool = False):
    view = _ready_view(tmp_path)
    assert view.knowledge is not None
    concepts = []
    for concept in view.knowledge.concepts:
        basis = concept.facets.structure.basis
        source_path = basis.source_path if basis is not None else None
        kind = getattr(concept.concept_kind, "value", concept.concept_kind)
        concepts.append(
            GraphConcept(
                locator=concept.locator,
                concept_kind=kind,
                source_path=source_path,
                symbol=concept.title if kind == "code-entity" else None,
                page_id=concept.document.page_id,
            )
        )

    graph = materialize_typed_graph(
        KnowledgeGraphInputs(
            inventory={SOURCE_PATH: {"language": "python"}},
            concepts=concepts,
            call_edges=(
                {
                    "from": {
                        "file": SOURCE_PATH,
                        "symbol": "AccountService.create",
                    },
                    "to": {"file": SOURCE_PATH, "symbol": "User"},
                    "name": "User",
                    "kind": "internal",
                    "line": 11,
                },
            ),
            dependency_observations={
                "schema_version": "test/dependencies-v1",
                "observations": [
                    {
                        "source_path": SOURCE_PATH,
                        "module": "requests",
                        "name": "",
                        "resolution": "external",
                        "line": 2,
                    }
                ],
                "coverage": {
                    "observed": 1,
                    "emitted": 1,
                    "omitted": 0,
                    "limit": None,
                    "truncated": False,
                    "limitations": [],
                },
            },
            external_dependencies=(
                {
                    "source_path": SOURCE_PATH,
                    "package": "postgresql",
                    "explicit": True,
                    "reason": "configured adapter",
                },
            ),
            evidence_limit=2,
        )
    )

    call_edge = next(edge for edge in graph["edges"] if edge["kind"] == "calls")
    plugin_edge = {
        **call_edge,
        "kind": "example.test/invokes",
    }
    plugin_edge["key"] = relationship_edge_key(
        {
            key: plugin_edge[key]
            for key in ("kind", "from", "target", "origin", "resolution")
        }
    )
    edges = [*graph["edges"], plugin_edge]
    graph["edges"] = list(reversed(edges)) if reverse_edges else edges
    knowledge = replace(
        view.knowledge,
        extensions={
            **view.knowledge.extensions,
            TYPED_GRAPH_EXTENSION_KEY: graph,
        },
    )
    return replace(view, knowledge=knowledge)


def _service(tmp_path, *, limit: int = 20, reverse_edges: bool = False):
    return DocumentationGraphQueryService(
        {},
        limit=limit,
        knowledge_view=_graph_view(tmp_path, reverse_edges=reverse_edges),
    )


def test_typed_graph_absence_is_explicit_and_not_claimed_ready(tmp_path):
    service = DocumentationGraphQueryService(
        {},
        knowledge_view=_ready_view(tmp_path),
    )

    result = service.traverse_typed_graph(MODULE_LOCATOR)

    assert result["found"] is True
    assert result["typed_graph"] == {
        "availability": "absent",
        "reason": "typed-graph-extension-not-present",
        "schema_version": None,
        "coverage": [],
    }
    assert result["edges"] == []
    assert result["total"] == 0
    assert result["returned"] == 0
    assert result["bounds"]["edges"] == {
        "total": 0,
        "returned": 0,
        "truncated": False,
    }


def test_traversal_filters_before_response_bounding_and_hides_samples(tmp_path):
    service = _service(tmp_path, limit=1)

    result = service.traverse_typed_graph(
        MODULE_LOCATOR,
        direction="outgoing",
        kinds=["contains", "imports", "depends_on"],
        origins=["extracted"],
        resolutions=["resolved", "external"],
    )

    assert result["typed_graph"]["availability"] == "ready"
    assert result["typed_graph"]["schema_version"] == "llm-wiki-typed-graph/v1"
    assert result["kinds"] == ["contains", "imports", "depends_on"]
    assert result["origins"] == ["extracted"]
    assert result["resolutions"] == ["resolved", "external"]
    assert result["total"] == 4
    assert result["returned"] == 1
    assert result["truncated"] is True
    assert result["bounds"]["edges"] == {
        "total": 4,
        "returned": 1,
        "truncated": True,
    }
    edge = result["edges"][0]
    assert "samples" not in edge["evidence"]
    assert "aggregate_input_hash" not in edge["evidence"]
    assert edge["evidence"]["observed"] == edge["coverage"]["observed"]
    assert edge["coverage"]["truncated"] is False
    assert result["typed_graph"]["coverage"]


def test_evidence_and_plugin_relationships_are_explicit_opt_ins(tmp_path):
    service = _service(tmp_path)

    unfiltered = service.traverse_typed_graph(
        USER_LOCATOR,
        direction="incoming",
    )
    compact = service.traverse_typed_graph(
        USER_LOCATOR,
        direction="incoming",
        kinds=["example.test/invokes"],
    )
    detailed = service.traverse_typed_graph(
        USER_LOCATOR,
        direction="incoming",
        kinds=["example.test/invokes"],
        include_evidence=True,
    )

    assert "example.test/invokes" in unfiltered["kinds"]
    assert any(
        edge["kind"] == "example.test/invokes"
        for edge in unfiltered["edges"]
    )
    assert compact["total"] == 1
    assert compact["edges"][0]["direction"] == "incoming"
    assert compact["edges"][0]["related_concept"]["locator"].endswith(
        "/AccountService"
    )
    assert "samples" not in compact["edges"][0]["evidence"]
    assert detailed["include_evidence"] is True
    assert detailed["edges"][0]["evidence"]["samples"][0]["kind"] == "call"
    assert detailed["edges"][0]["evidence"]["aggregate_input_hash"].startswith(
        "sha256:"
    )


def test_shuffled_extension_edges_produce_identical_traversal_json(tmp_path):
    ordered_root = tmp_path / "ordered"
    shuffled_root = tmp_path / "shuffled"
    ordered_root.mkdir()
    shuffled_root.mkdir()
    ordered = _service(ordered_root)
    shuffled = _service(shuffled_root, reverse_edges=True)

    first = ordered.traverse_typed_graph(
        USER_LOCATOR,
        include_evidence=True,
    )
    second = shuffled.traverse_typed_graph(
        USER_LOCATOR,
        include_evidence=True,
    )

    assert json.dumps(first, sort_keys=True) == json.dumps(second, sort_keys=True)


def test_typed_graph_extension_does_not_change_legacy_query_json(tmp_path):
    plain_root = tmp_path / "plain"
    graph_root = tmp_path / "graph"
    plain_root.mkdir()
    graph_root.mkdir()
    plain = DocumentationGraphQueryService(
        {},
        knowledge_view=_ready_view(plain_root),
    )
    graph = _service(graph_root)

    for method_name, locator in (
        ("get_concept", USER_LOCATOR),
        ("related_concepts", USER_LOCATOR),
        ("explain_evidence", USER_LOCATOR),
    ):
        assert getattr(plain, method_name)(locator) == getattr(graph, method_name)(
            locator
        )


@pytest.mark.parametrize(
    ("kwargs", "message"),
    [
        ({"direction": "outbound"}, "direction"),
        ({"kinds": "calls"}, "kinds"),
        ({"kinds": ["not-qualified"]}, "relationship kind"),
        ({"origins": ["guessed"]}, "origin"),
        ({"resolutions": [1]}, "resolutions"),
        ({"include_evidence": 1}, "include_evidence"),
    ],
)
def test_invalid_typed_graph_filters_are_rejected(kwargs, message):
    with pytest.raises(DocumentationQueryError, match=message):
        DocumentationGraphQueryService({}).traverse_typed_graph(
            USER_LOCATOR,
            **kwargs,
        )


def test_python_api_wrapper_reuses_service_and_forwards_all_filters(tmp_path):
    service = _service(tmp_path)

    expected = service.traverse_typed_graph(
        USER_LOCATOR,
        direction="incoming",
        kinds=["calls"],
        origins=["extracted"],
        resolutions=["resolved"],
        include_evidence=True,
    )
    actual = api.traverse_typed_graph(
        USER_LOCATOR,
        service=service,
        direction="incoming",
        kinds=["calls"],
        origins=["extracted"],
        resolutions=["resolved"],
        include_evidence=True,
    )

    assert actual == expected


def test_mcp_method_validates_and_delegates_typed_graph_options(monkeypatch):
    calls = []

    class QueryService:
        def traverse_typed_graph(self, locator, **kwargs):
            calls.append((locator, kwargs))
            return {"total": 1, "returned": 1, "truncated": False}

    monkeypatch.setattr(
        mcp_server,
        "build_documentation_query_service",
        lambda *_args, **_kwargs: QueryService(),
    )
    service = mcp_server.McpWikiService()

    result = service.traverse_typed_graph(
        USER_LOCATOR,
        direction="incoming",
        kinds=["example.test/invokes", "calls"],
        origins=["inferred", "extracted"],
        resolutions=["resolved"],
        include_evidence=True,
        limit=200,
    )

    assert result["total"] == 1
    assert calls == [
        (
            USER_LOCATOR,
            {
                "direction": "incoming",
                "kinds": ["calls", "example.test/invokes"],
                "origins": ["extracted", "inferred"],
                "resolutions": ["resolved"],
                "include_evidence": True,
            },
        )
    ]


@pytest.mark.parametrize(
    "kwargs",
    [
        {"direction": "inbound"},
        {"kinds": ["not-qualified"]},
        {"origins": ["guessed"]},
        {"resolutions": "resolved"},
        {"include_evidence": "yes"},
        {"limit": 0},
    ],
)
def test_mcp_typed_graph_validation_happens_before_service_build(
    monkeypatch,
    kwargs,
):
    def fail(*_args, **_kwargs):
        raise AssertionError("query service should not be built")

    monkeypatch.setattr(
        mcp_server,
        "build_documentation_query_service",
        fail,
    )

    with pytest.raises(mcp_server.McpWikiError):
        mcp_server.McpWikiService().traverse_typed_graph(
            USER_LOCATOR,
            **kwargs,
        )
