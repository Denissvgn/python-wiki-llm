"""Work-count, locality, and payload-bound gates for native knowledge reads."""

from __future__ import annotations

import builtins
import io
import json
import random
import socket
import subprocess
from copy import deepcopy
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace

import pytest

from llm_wiki_cli import api
from llm_wiki_cli.services import knowledge_consumption, mcp_server, source_snapshot
from llm_wiki_cli.services.documentation_queries import (
    DocumentationGraphQueryService,
)
from llm_wiki_cli.services.knowledge_consumption import build_knowledge_read_view
from llm_wiki_cli.services.knowledge_loader import load_knowledge_state
from llm_wiki_cli.services.knowledge_model import parse_knowledge_index
from tests.knowledge_fixtures import fixture_hash
from tests.test_documentation_queries import _service
from tests.test_knowledge_freshness import _live_evaluation
from tests.test_knowledge_loader import _committed_state

_STRESS_CONCEPT_COUNT = 2_000
_STRESS_HUB_LOCATOR = "llm-wiki://entities/Entity0000"
_STRESS_PERIPHERAL_LOCATOR = "llm-wiki://entities/Entity1000"


def _stress_concept(template: dict, index: int) -> dict:
    page_id = f"Entity{index:04d}"
    concept = deepcopy(template)
    concept["locator"] = f"llm-wiki://entities/{page_id}"
    concept["title"] = page_id
    concept["document"].update(
        {
            "page_kind": "entities",
            "page_id": page_id,
            "canonical_path": f"entities/{page_id}.md",
            "role": "semantic",
        }
    )
    structure = concept["facets"]["structure"]
    structure["basis"].update(
        {
            "scope": "entity",
            "source_path": "src/stress.py",
            "concept_observation_hash": fixture_hash(f"stress:observation:{page_id}"),
        }
    )
    concept["facets"]["semantics"]["page_hash"] = fixture_hash(f"stress:page:{page_id}")
    return concept


def _stress_link(
    source_index: int,
    target_index: int,
    *,
    observation: str,
) -> dict:
    source_id = f"Entity{source_index:04d}"
    target_id = f"Entity{target_index:04d}"
    raw_target = f"{target_id}.md"
    return {
        "kind": "links_to",
        "from": f"llm-wiki://entities/{source_id}",
        "target": {
            "target_class": "concept",
            "canonical_path": f"entities/{target_id}.md",
            "raw_target": raw_target,
            "normalized_target": raw_target,
            "label": f"{target_id}-{observation}",
            "location": {
                "start": 0 if observation == "ring" else 2,
                "end": 1 if observation == "ring" else 3,
            },
        },
        "origin": "markdown",
        "evidence": {
            "state": "present",
            "page_hash": fixture_hash(f"stress:page:{source_id}"),
        },
        "resolution": "resolved",
    }


def _stress_knowledge(base_payload: dict):
    template = next(
        concept
        for concept in base_payload["concepts"]
        if concept["concept_kind"] == "code-entity"
    )
    payload = deepcopy(base_payload)
    payload["concepts"] = [
        _stress_concept(template, index) for index in range(_STRESS_CONCEPT_COUNT)
    ]
    payload["relationships"] = [
        _stress_link(
            index,
            (index + 1) % _STRESS_CONCEPT_COUNT,
            observation="ring",
        )
        for index in range(_STRESS_CONCEPT_COUNT)
    ]
    payload["relationships"].extend(
        _stress_link(0, index, observation="hub")
        for index in range(1, _STRESS_CONCEPT_COUNT)
    )
    return parse_knowledge_index(payload)


@pytest.fixture(scope="module")
def stress_views(tmp_path_factory):
    root = tmp_path_factory.mktemp("knowledge-performance")
    fixture, _plan, _result = _committed_state(root)
    loaded = load_knowledge_state(root)
    knowledge = _stress_knowledge(dict(fixture.knowledge_payload))

    concepts = list(knowledge.concepts)
    relationships = list(knowledge.relationships)
    random.Random(210_001).shuffle(concepts)
    random.Random(210_002).shuffle(relationships)
    shuffled = replace(
        knowledge,
        concepts=tuple(concepts),
        relationships=tuple(relationships),
    )

    return (
        build_knowledge_read_view(
            replace(loaded, knowledge=knowledge),
            snapshot_only=True,
        ),
        build_knowledge_read_view(
            replace(loaded, knowledge=shuffled),
            snapshot_only=True,
        ),
    )


def test_query_operation_uses_one_snapshot_one_deep_extraction_and_one_view(
    tmp_path,
    monkeypatch,
):
    (tmp_path / "app.py").write_text(
        "def run() -> None:\n    pass\n",
        encoding="utf-8",
    )
    wiki_root = tmp_path / "docs" / "llm_wiki"
    wiki_root.mkdir(parents=True)
    monkeypatch.chdir(tmp_path)

    calls = {
        "repository_walk": 0,
        "snapshot": 0,
        "deep_extraction": 0,
        "surface": 0,
        "view": 0,
        "service": 0,
    }
    captured_snapshot = []
    extract_results = []
    real_snapshot = api.extract_cmd.build_source_snapshot
    real_inventory = api.extract_cmd.get_inventory_result
    real_extract_payload = api.extract_cmd.build_extract_payload
    real_walk = source_snapshot.os.walk

    def counted_walk(*args, **kwargs):
        calls["repository_walk"] += 1
        return real_walk(*args, **kwargs)

    def counted_snapshot(*args, **kwargs):
        calls["snapshot"] += 1
        snapshot = real_snapshot(*args, **kwargs)
        captured_snapshot.append(snapshot)
        return snapshot

    def counted_inventory(request):
        calls["deep_extraction"] += 1
        assert request.deep is True
        assert request.source_snapshot is captured_snapshot[0]
        result = real_inventory(request)
        assert result.source_snapshot is request.source_snapshot
        return result

    def retained_extract_payload(*args, **kwargs):
        result = real_extract_payload(*args, **kwargs)
        assert result.dependency_analysis is not None
        extract_results.append(result)
        return result

    surface = SimpleNamespace(payload={"pages": []})
    knowledge_view = object()
    query_surface = {"pages": []}
    built_service = object()

    def counted_surface(root, inventory, **kwargs):
        calls["surface"] += 1
        assert root == wiki_root.resolve()
        assert set(inventory) == {"app.py"}
        assert kwargs["src_dir"] == tmp_path.resolve()
        return surface

    def counted_view(root, evaluation, inventory, inventory_result):
        calls["view"] += 1
        assert root == wiki_root.resolve()
        assert evaluation is surface
        assert set(inventory) == {"app.py"}
        assert inventory_result.source_snapshot is captured_snapshot[0]
        return knowledge_view

    def counted_service(inventory, **kwargs):
        calls["service"] += 1
        assert set(inventory) == {"app.py"}
        assert kwargs["surface_index"] is query_surface
        assert kwargs["knowledge_view"] is knowledge_view
        assert kwargs["dependency_analysis"] is extract_results[0].dependency_analysis
        return built_service

    monkeypatch.setattr(source_snapshot.os, "walk", counted_walk)
    monkeypatch.setattr(api.extract_cmd, "build_source_snapshot", counted_snapshot)
    monkeypatch.setattr(api.extract_cmd, "get_inventory_result", counted_inventory)
    monkeypatch.setattr(
        api.extract_cmd,
        "build_extract_payload",
        retained_extract_payload,
    )
    monkeypatch.setattr(api, "evaluate_surface_index", counted_surface)
    monkeypatch.setattr(
        api.context_cmd,
        "_build_context_knowledge_view",
        counted_view,
    )
    monkeypatch.setattr(
        api.context_cmd,
        "_context_query_surface",
        lambda payload, view: (
            query_surface
            if payload is surface.payload and view is knowledge_view
            else pytest.fail("query surface did not reuse the read view")
        ),
    )
    monkeypatch.setattr(
        api,
        "analyze_dependencies",
        lambda *_args, **_kwargs: pytest.fail(
            "API query builder recomputed retained dependency analysis"
        ),
    )
    monkeypatch.setattr(api, "DocumentationGraphQueryService", counted_service)

    result = api.build_documentation_query_service(
        ".",
        wiki_dir="docs/llm_wiki",
        read_only=True,
    )

    assert result is built_service
    assert calls == {
        "repository_walk": 1,
        "snapshot": 1,
        "deep_extraction": 1,
        "surface": 1,
        "view": 1,
        "service": 1,
    }


def test_one_freshness_evaluation_and_zero_query_method_io(
    tmp_path,
    monkeypatch,
):
    _committed_state(tmp_path)
    loaded = load_knowledge_state(tmp_path)
    assert loaded.knowledge is not None
    live = _live_evaluation(loaded.knowledge)
    evaluations = []
    real_evaluator = knowledge_consumption.evaluate_knowledge_freshness

    def counted_evaluator(knowledge, live_evaluation):
        evaluations.append((knowledge, live_evaluation))
        return real_evaluator(knowledge, live_evaluation)

    monkeypatch.setattr(
        knowledge_consumption,
        "evaluate_knowledge_freshness",
        counted_evaluator,
    )
    view = build_knowledge_read_view(loaded, live_evaluation=live)
    service = _service(knowledge_view=view)

    assert evaluations == [(loaded.knowledge, live)]

    def forbidden_io(*_args, **_kwargs):
        raise AssertionError("query methods must not perform I/O")

    for owner, attribute in (
        (builtins, "open"),
        (io, "open"),
        (Path, "open"),
        (Path, "read_bytes"),
        (Path, "read_text"),
        (Path, "write_bytes"),
        (Path, "write_text"),
        (socket, "socket"),
        (socket, "create_connection"),
        (subprocess, "run"),
        (subprocess, "Popen"),
        (subprocess, "check_call"),
        (subprocess, "check_output"),
    ):
        monkeypatch.setattr(owner, attribute, forbidden_io)

    results = (
        service.flow_for_entrypoint("api-run"),
        service.callers("save"),
        service.callees("run"),
        service.dependency_neighborhood("api.py"),
        service.data_flow_for_entrypoint("api-run"),
        service.pages_for_symbol("run"),
        service.get_concept("llm-wiki://entities/User"),
        service.related_concepts("llm-wiki://entities/User"),
        service.explain_evidence("llm-wiki://entities/User"),
    )

    assert all(isinstance(result, dict) for result in results)
    assert evaluations == [(loaded.knowledge, live)]


def test_default_and_mcp_bounds_disclose_stress_truncation(stress_views):
    ordered_view, _shuffled_view = stress_views
    service = DocumentationGraphQueryService({}, knowledge_view=ordered_view)

    assert service.limit == 20
    assert mcp_server._bounded_query_limit(10_000) == 100

    related = service.related_concepts(_STRESS_HUB_LOCATOR)
    assert related["total"] == _STRESS_CONCEPT_COUNT + 1
    assert related["returned"] == 20
    assert related["truncated"] is True
    assert len(related["matches"]) <= 20
    assert len(related["relationships"]) == related["returned"]
    assert len(related["related_concepts"]) <= 20
    assert len(related["unresolved_targets"]) <= 20
    assert len(related["external_targets"]) <= 20

    evidence = service.explain_evidence(_STRESS_HUB_LOCATOR)
    assert evidence["total"] == related["total"]
    assert evidence["returned"] == 20
    assert evidence["truncated"] is True
    assert len(evidence["matches"]) <= 20
    assert len(evidence["evidence"]["relationships"]) == evidence["returned"]


class _LookupProbe(dict):
    def __init__(self, values):
        super().__init__(values)
        self.get_calls = 0
        self.item_calls = 0

    def get(self, key, default=None):
        self.get_calls += 1
        return super().get(key, default)

    def __getitem__(self, key):
        self.item_calls += 1
        return super().__getitem__(key)

    def __iter__(self):
        raise AssertionError("exact lookup must not scan the concept index")


class _RelationshipProbe:
    def __init__(self, values):
        self._values = values
        self.item_calls = 0

    def __getitem__(self, index):
        self.item_calls += 1
        return self._values[index]

    def __len__(self):
        return len(self._values)

    def __iter__(self):
        raise AssertionError("neighbor lookup must not scan every relationship")


def test_exact_lookup_is_indexed_and_neighbor_work_is_local(stress_views):
    ordered_view, _shuffled_view = stress_views
    service = DocumentationGraphQueryService({}, knowledge_view=ordered_view)
    assert len(service.concept_by_locator) == _STRESS_CONCEPT_COUNT
    assert len(service._knowledge_relationships) == (2 * _STRESS_CONCEPT_COUNT) - 1

    concept_probe = _LookupProbe(service.concept_by_locator)
    service.concept_by_locator = concept_probe
    exact = service.get_concept(_STRESS_PERIPHERAL_LOCATOR)

    assert exact["found"] is True
    assert concept_probe.get_calls == 1
    assert concept_probe.item_calls == 2

    relationship_probe = _RelationshipProbe(service._knowledge_relationships)
    service._knowledge_relationships = relationship_probe
    neighbors = service.related_concepts(_STRESS_PERIPHERAL_LOCATOR)

    assert neighbors["total"] == 3
    assert neighbors["returned"] == 3
    assert neighbors["truncated"] is False
    assert relationship_probe.item_calls < 100


def test_thousands_scale_output_is_deterministic_across_shuffled_inputs(
    stress_views,
):
    ordered_view, shuffled_view = stress_views
    assert ordered_view.knowledge is not None
    assert shuffled_view.knowledge is not None
    assert ordered_view.knowledge.concepts != shuffled_view.knowledge.concepts
    assert ordered_view.knowledge.relationships != shuffled_view.knowledge.relationships

    ordered = DocumentationGraphQueryService({}, knowledge_view=ordered_view)
    shuffled = DocumentationGraphQueryService({}, knowledge_view=shuffled_view)

    ordered_payload = {
        "exact": ordered.get_concept(_STRESS_PERIPHERAL_LOCATOR),
        "related": ordered.related_concepts(_STRESS_HUB_LOCATOR),
        "evidence": ordered.explain_evidence(_STRESS_HUB_LOCATOR),
    }
    shuffled_payload = {
        "exact": shuffled.get_concept(_STRESS_PERIPHERAL_LOCATOR),
        "related": shuffled.related_concepts(_STRESS_HUB_LOCATOR),
        "evidence": shuffled.explain_evidence(_STRESS_HUB_LOCATOR),
    }

    assert list(ordered.concept_by_locator) == list(shuffled.concept_by_locator)
    assert ordered._knowledge_relationships == shuffled._knowledge_relationships
    assert json.dumps(
        ordered_payload,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ) == json.dumps(
        shuffled_payload,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    )
