from __future__ import annotations

import builtins
import json
import socket
import subprocess
from copy import deepcopy

import pytest
from jsonschema import Draft202012Validator

from llm_wiki_cli.services.contracts import TYPED_GRAPH_SCHEMA_VERSION
from llm_wiki_cli.services.knowledge_graph import (
    CORE_RELATIONSHIP_KINDS,
    GraphConcept,
    KnowledgeGraphError,
    KnowledgeGraphInputs,
    materialize_typed_graph,
    relationship_edge_key,
    serialize_typed_graph,
    validate_typed_graph,
)
from llm_wiki_cli.services.knowledge_model import load_knowledge_schema


def _coverage(observed: int = 1, emitted: int = 1) -> dict:
    return {
        "observed": observed,
        "emitted": emitted,
        "omitted": observed - emitted,
        "limit": None,
        "truncated": observed > emitted,
        "limitations": [],
    }


def _concepts() -> tuple[GraphConcept, ...]:
    return (
        GraphConcept(
            "llm-wiki://modules/a",
            "source-module",
            source_path="src/a.py",
            page_id="a",
        ),
        GraphConcept(
            "llm-wiki://modules/b",
            "source-module",
            source_path="src/b.py",
            page_id="b",
        ),
        GraphConcept(
            "llm-wiki://entities/A",
            "code-entity",
            source_path="src/a.py",
            symbol="A",
            occurrence=1,
            page_id="A",
        ),
        GraphConcept(
            "llm-wiki://entities/B",
            "code-entity",
            source_path="src/b.py",
            symbol="B",
            occurrence=1,
            page_id="B",
        ),
        GraphConcept(
            "llm-wiki://flows/api-run",
            "user-flow",
            page_id="api-run",
        ),
    )


def _inputs(*, reverse: bool = False, evidence_limit: int = 20):
    calls = [
        {
            "from": {"file": "src/a.py", "symbol": "A.run"},
            "to": {"file": "src/b.py", "symbol": "B.save"},
            "kind": "internal",
            "name": "save",
            "line": 12,
        },
        {
            "from": {"file": "src/a.py", "symbol": "A.run"},
            "to": {"file": "src/b.py", "symbol": "B.save"},
            "kind": "internal",
            "name": "save",
            "line": 13,
        },
        {
            "from": {"file": "src/a.py", "symbol": "A.run"},
            "to": {"file": None, "symbol": "publish"},
            "kind": "external",
            "name": "queue.publish",
        },
        {
            "from": {"file": "src/a.py", "symbol": "A.run"},
            "to": {"file": None, "symbol": "dynamic"},
            "kind": "unresolved",
            "name": "dynamic",
        },
    ]
    imports = [
        {
            "source_path": "src/a.py",
            "module": "src.b",
            "name": "B",
            "line": 2,
            "candidates": ["src/b.py"],
            "target_path": "src/b.py",
            "resolution": "resolved",
        },
        {
            "source_path": "src/a.py",
            "module": "models",
            "name": "User",
            "line": None,
            "candidates": ["src/a.py", "src/b.py"],
            "target_path": None,
            "resolution": "ambiguous",
        },
        {
            "source_path": "src/a.py",
            "module": "requests",
            "name": "get",
            "line": 3,
            "candidates": [],
            "target_path": None,
            "resolution": "external",
        },
        {
            "source_path": "src/a.py",
            "module": ".missing",
            "name": "thing",
            "line": None,
            "candidates": [],
            "target_path": None,
            "resolution": "unresolved",
        },
    ]
    entrypoints = [
        {
            "entry": {
                "id": "api-run",
                "category": "api",
                "file": "src/a.py",
                "symbol": "A.run",
                "label": "run",
            },
            "detector": {
                "id": "builtin.api-export",
                "version": "1",
                "reason": "public API export",
                "source_location": {
                    "source_path": "src/a.py",
                    "line": 8,
                },
                "plugin_component": None,
            },
        }
    ]
    data_flows = [
        {
            "id": "api-run",
            "entry": {
                "id": "api-run",
                "file": "src/a.py",
                "symbol": "A.run",
            },
            "steps": [
                {
                    "file": "src/a.py",
                    "symbol": "A.run",
                    "reads": [{"kind": "environment", "target": "API_TOKEN"}],
                    "writes": [
                        {
                            "kind": "filesystem",
                            "target": "var/result.json",
                            "line": 17,
                        }
                    ],
                }
            ],
        }
    ]
    external_dependencies = [
        {
            "source_path": "src/a.py",
            "package": "requests",
            "explicit": True,
            "reason": "declared in pyproject.toml",
        },
        {
            "source_path": "src/a.py",
            "package": "ignored-import-only",
            "explicit": False,
        },
    ]
    concepts = _concepts()
    if reverse:
        concepts = tuple(reversed(concepts))
        calls.reverse()
        imports.reverse()
        entrypoints.reverse()
        data_flows.reverse()
        external_dependencies.reverse()
    return KnowledgeGraphInputs(
        inventory={
            "src/a.py": {"classes": [{"name": "A"}]},
            "src/b.py": {"classes": [{"name": "B"}]},
        },
        concepts=concepts,
        call_edges=calls,
        dependency_observations={
            "schema_version": "llm-wiki-dependency-observations/v1",
            "observations": imports,
            "coverage": _coverage(4, 4),
        },
        entrypoint_observations={
            "schema_version": "llm-wiki-entrypoint-observations/v1",
            "observations": entrypoints,
            "coverage": _coverage(1, 1),
        },
        flows=[
            {
                "entry": entrypoints[0]["entry"],
                "steps": [
                    {
                        "file": "src/a.py",
                        "symbol": "A.run",
                        "kind": "entry",
                    }
                ],
            }
        ],
        data_flows=data_flows,
        external_dependencies=external_dependencies,
        evidence_limit=evidence_limit,
    )


def test_materializer_emits_every_non_governance_core_kind_and_all_resolutions():
    graph = materialize_typed_graph(_inputs())

    assert graph["schema_version"] == TYPED_GRAPH_SCHEMA_VERSION
    kinds = {edge["kind"] for edge in graph["edges"]}
    assert kinds == set(CORE_RELATIONSHIP_KINDS) - {"supersedes"}
    assert {edge["resolution"] for edge in graph["edges"]} == {
        "resolved",
        "ambiguous",
        "external",
        "unresolved",
    }
    assert all(
        set(edge)
        == {
            "key",
            "kind",
            "from",
            "target",
            "origin",
            "resolution",
            "evidence",
            "coverage",
        }
        for edge in graph["edges"]
    )
    assert all(edge["evidence"]["observed"] >= 1 for edge in graph["edges"])
    assert all(
        edge["coverage"]["omitted"]
        == edge["coverage"]["observed"] - edge["coverage"]["emitted"]
        for edge in graph["edges"]
    )
    assert graph["input_hashes"]["aggregate"].startswith("sha256:")


def test_calls_lift_to_owners_but_retain_exact_symbols_and_unknown_location():
    graph = materialize_typed_graph(_inputs())
    resolved = next(
        edge
        for edge in graph["edges"]
        if edge["kind"] == "calls" and edge["resolution"] == "resolved"
    )
    assert resolved["from"]["locator"] == "llm-wiki://entities/A"
    assert resolved["target"]["locator"] == "llm-wiki://entities/B"
    assert resolved["evidence"]["observed"] == 2
    assert [sample["location"]["line"] for sample in resolved["evidence"]["samples"]] == [
        12,
        13,
    ]
    assert all(sample["source"]["symbol"] == "A.run" for sample in resolved["evidence"]["samples"])

    external = next(
        edge
        for edge in graph["edges"]
        if edge["kind"] == "calls" and edge["resolution"] == "external"
    )
    assert external["evidence"]["samples"][0]["location"] == {
        "source_path": "src/a.py"
    }
    assert "line" not in external["evidence"]["samples"][0]["location"]


def test_duplicate_entity_owners_never_select_an_arbitrary_occurrence_and_self_loops_survive():
    concepts = (
        GraphConcept(
            "llm-wiki://modules/a",
            "source-module",
            source_path="src/a.py",
            page_id="a",
        ),
        GraphConcept(
            "llm-wiki://entities/A",
            "code-entity",
            source_path="src/a.py",
            symbol="A",
            occurrence=1,
            page_id="A",
        ),
        GraphConcept(
            "llm-wiki://entities/A_2",
            "code-entity",
            source_path="src/a.py",
            symbol="A",
            occurrence=2,
            page_id="A_2",
        ),
    )
    graph = materialize_typed_graph(
        KnowledgeGraphInputs(
            inventory={"src/a.py": {"classes": [{"name": "A"}, {"name": "A"}]}},
            concepts=concepts,
            call_edges=[
                {
                    "from": {"file": "src/a.py", "symbol": "A.run"},
                    "to": {"file": "src/a.py", "symbol": "A.help"},
                    "kind": "internal",
                    "name": "help",
                    "line": 3,
                }
            ],
            dependency_observations=[
                {
                    "source_path": "src/a.py",
                    "module": ".a",
                    "name": "A",
                    "line": 1,
                    "candidates": ["src/a.py"],
                    "target_path": "src/a.py",
                    "resolution": "resolved",
                }
            ],
        )
    )

    contains = [edge for edge in graph["edges"] if edge["kind"] == "contains"]
    assert {edge["target"]["locator"] for edge in contains} == {
        "llm-wiki://entities/A",
        "llm-wiki://entities/A_2",
    }
    call = next(edge for edge in graph["edges"] if edge["kind"] == "calls")
    assert call["from"]["locator"] == "llm-wiki://modules/a"
    assert call["target"]["locator"] == "llm-wiki://modules/a"
    imported = next(edge for edge in graph["edges"] if edge["kind"] == "imports")
    assert imported["from"] == imported["target"]


def test_ambiguous_import_candidates_never_become_resolved():
    graph = materialize_typed_graph(_inputs())
    edge = next(
        value
        for value in graph["edges"]
        if value["kind"] == "imports"
        and value["resolution"] == "ambiguous"
    )
    assert edge["target"]["kind"] == "unresolved"
    assert [candidate["locator"] for candidate in edge["target"]["candidates"]] == [
        "llm-wiki://modules/a",
        "llm-wiki://modules/b",
    ]


def test_detailed_call_bundle_and_entrypoint_detector_retain_provenance():
    inputs = _inputs()
    call = {
        "from": {"file": "src/a.py", "symbol": "A.run"},
        "to": {"file": None, "symbol": "save"},
        "name": "save",
        "kind": "ambiguous",
        "line": None,
        "candidates": [
            {"file": "src/a.py", "symbol": "A.save"},
            {"file": "src/b.py", "symbol": "B.save"},
        ],
    }
    graph = materialize_typed_graph(
        KnowledgeGraphInputs(
            **{
                **inputs.__dict__,
                "call_edges": {
                    "schema_version": "llm-wiki-call-observations/v1",
                    "observations": [call],
                    "coverage": _coverage(1, 1),
                },
            }
        )
    )

    call_edge = next(edge for edge in graph["edges"] if edge["kind"] == "calls")
    assert call_edge["resolution"] == "ambiguous"
    assert {
        candidate["locator"]
        for candidate in call_edge["target"]["candidates"]
    } == {
        "llm-wiki://entities/A",
        "llm-wiki://entities/B",
    }
    assert call_edge["evidence"]["samples"][0]["attributes"][
        "candidate_source_symbols"
    ] == [
        {
            "kind": "source-symbol",
            "source_path": "src/a.py",
            "symbol": "A.save",
        },
        {
            "kind": "source-symbol",
            "source_path": "src/b.py",
            "symbol": "B.save",
        },
    ]
    entrypoint = next(
        edge for edge in graph["edges"] if edge["kind"] == "entrypoint_for"
    )
    evidence = entrypoint["evidence"]["samples"][0]
    assert evidence["detector"] == {
        "id": "builtin.api-export",
        "version": "1",
    }
    assert evidence["reason"] == "public API export"
    assert evidence["location"] == {
        "source_path": "src/a.py",
        "line": 8,
    }


def test_duplicate_evidence_is_counted_and_bounded_with_omissions():
    inputs = _inputs(evidence_limit=1)
    repeated = deepcopy(list(inputs.call_edges))
    repeated.append(deepcopy(repeated[0]))
    graph = materialize_typed_graph(
        KnowledgeGraphInputs(
            **{
                **inputs.__dict__,
                "call_edges": repeated,
            }
        )
    )
    edge = next(
        value
        for value in graph["edges"]
        if value["kind"] == "calls"
        and value["resolution"] == "resolved"
    )
    assert edge["evidence"] | {} == edge["evidence"]
    assert edge["evidence"]["observed"] == 3
    assert edge["evidence"]["unique"] == 2
    assert edge["evidence"]["emitted"] == 1
    assert edge["evidence"]["omitted"] == 2
    assert edge["coverage"] == {
        "observed": 3,
        "emitted": 1,
        "omitted": 2,
        "limit": 1,
        "truncated": True,
        "limitations": [],
    }


def test_upstream_data_flow_coverage_stays_separate_from_edge_sampling():
    inputs = _inputs()
    detailed = deepcopy(inputs.data_flows[0])
    detailed["coverage"] = {
        "effects": {
            "by_kind": {
                "reads": {
                    "observed": 3,
                    "emitted": 1,
                    "limitations": ["upstream-effect-collector-totals-may-be-unavailable"],
                },
                "writes": {
                    "observed": 1,
                    "emitted": 1,
                    "limitations": [],
                },
            }
        }
    }
    graph = materialize_typed_graph(
        KnowledgeGraphInputs(
            **{
                **inputs.__dict__,
                "data_flows": [detailed],
            }
        )
    )

    coverage = next(
        item for item in graph["coverage"] if item["analyzer"] == "data-flows"
    )
    assert coverage["observed"] == 4
    assert coverage["emitted"] == 2
    assert coverage["omitted"] == 2
    assert coverage["truncated"] is True
    assert "graph/upstream-data-effects-omitted" in coverage["limitations"]
    assert all(
        edge["coverage"]["omitted"] == 0
        for edge in graph["edges"]
        if edge["kind"] in {"reads", "writes"}
    )


def test_detailed_flow_step_coverage_reaches_graph_analyzer_coverage():
    inputs = _inputs()
    flow = deepcopy(inputs.flows[0])
    flow.update(
        {
            "schema_version": "llm-wiki-flow-observations/v1",
            "truncated": True,
            "coverage": {
                "steps": {
                    "observed": 4,
                    "emitted": 1,
                    "omitted": 3,
                    "limit": None,
                    "depth_limit": 0,
                    "truncated": True,
                    "limitations": ["flow-steps-are-statically-inferred"],
                }
            },
        }
    )
    graph = materialize_typed_graph(
        KnowledgeGraphInputs(**{**inputs.__dict__, "flows": [flow]})
    )

    coverage = next(
        item for item in graph["coverage"] if item["analyzer"] == "flows"
    )
    assert coverage == {
        "analyzer": "flows",
        "observed": 4,
        "emitted": 1,
        "omitted": 3,
        "limit": None,
        "truncated": True,
        "limitations": ["flow-steps-are-statically-inferred"],
    }


def test_legacy_truncated_flow_reports_unknown_reachable_total_limitation():
    inputs = _inputs()
    flow = {**inputs.flows[0], "truncated": True}
    graph = materialize_typed_graph(
        KnowledgeGraphInputs(**{**inputs.__dict__, "flows": [flow]})
    )

    coverage = next(
        item for item in graph["coverage"] if item["analyzer"] == "flows"
    )
    assert coverage["observed"] == coverage["emitted"] == 1
    assert coverage["omitted"] == 0
    assert "graph/flow-reachable-step-total-unavailable" in coverage["limitations"]


def test_analyzer_limitations_are_committed_in_the_aggregate_input_hash():
    inputs = _inputs()
    first = materialize_typed_graph(
        KnowledgeGraphInputs(
            **{
                **inputs.__dict__,
                "analyzer_limitations": {
                    "calls": (
                        "static-call-analysis",
                        "call-depth-limit",
                    )
                },
            }
        )
    )
    reordered = materialize_typed_graph(
        KnowledgeGraphInputs(
            **{
                **inputs.__dict__,
                "analyzer_limitations": {
                    "calls": (
                        "call-depth-limit",
                        "static-call-analysis",
                    )
                },
            }
        )
    )
    changed = materialize_typed_graph(
        KnowledgeGraphInputs(
            **{
                **inputs.__dict__,
                "analyzer_limitations": {
                    "calls": ("static-call-analysis",)
                },
            }
        )
    )

    assert first == reordered
    assert first["input_hashes"]["analyzer-limitations"] != (
        changed["input_hashes"]["analyzer-limitations"]
    )
    assert first["input_hashes"]["aggregate"] != (
        changed["input_hashes"]["aggregate"]
    )


def test_graph_validation_binds_evidence_hashes_and_analyzer_coverage():
    graph = materialize_typed_graph(_inputs())

    wrong_hash = deepcopy(graph)
    wrong_hash["edges"][0]["evidence"]["aggregate_input_hash"] = (
        "sha256:" + ("0" * 64)
    )
    with pytest.raises(KnowledgeGraphError, match="input_hashes"):
        validate_typed_graph(wrong_hash)

    missing_coverage = deepcopy(graph)
    missing_coverage["coverage"].pop()
    with pytest.raises(KnowledgeGraphError, match="structural analyzers"):
        validate_typed_graph(missing_coverage)

    wrong_count = deepcopy(graph)
    calls = next(
        item for item in wrong_count["coverage"] if item["analyzer"] == "calls"
    )
    calls["emitted"] -= 1
    calls["omitted"] += 1
    calls["truncated"] = True
    with pytest.raises(KnowledgeGraphError, match="materialized into typed edges"):
        validate_typed_graph(wrong_count)


def test_all_concept_locator_references_are_checked_but_uids_remain_valid():
    graph = materialize_typed_graph(_inputs())
    concept_kinds = {
        concept.locator: concept.concept_kind for concept in _concepts()
    }

    custom = deepcopy(graph)
    custom_edge = deepcopy(custom["edges"][0])
    custom_edge["kind"] = "vendor/links"
    custom_edge["origin"] = "markdown"
    custom_edge["from"] = {
        "kind": "concept",
        "locator": "llm-wiki://modules/missing",
    }
    custom_edge["key"] = relationship_edge_key(custom_edge)
    custom["edges"].append(custom_edge)
    with pytest.raises(KnowledgeGraphError, match="does not reference"):
        validate_typed_graph(custom, concept_kinds=concept_kinds)

    candidate = deepcopy(graph)
    ambiguous_import = next(
        edge
        for edge in candidate["edges"]
        if edge["kind"] == "imports" and edge["resolution"] == "ambiguous"
    )
    ambiguous_import["target"]["candidates"][0] = {
        "kind": "concept",
        "locator": "llm-wiki://modules/missing",
    }
    ambiguous_import["key"] = relationship_edge_key(ambiguous_import)
    with pytest.raises(KnowledgeGraphError, match="does not reference"):
        validate_typed_graph(candidate, concept_kinds=concept_kinds)

    evidence = deepcopy(graph)
    contains = next(edge for edge in evidence["edges"] if edge["kind"] == "contains")
    contains["evidence"]["samples"][0]["target"] = {
        "kind": "concept",
        "locator": "llm-wiki://entities/missing",
    }
    with pytest.raises(KnowledgeGraphError, match="does not reference"):
        validate_typed_graph(evidence, concept_kinds=concept_kinds)

    uid_graph = deepcopy(graph)
    uid_contains = next(
        edge for edge in uid_graph["edges"] if edge["kind"] == "contains"
    )
    uid_contains["from"] = {"kind": "concept", "uid": "module-stable-id"}
    uid_contains["target"] = {"kind": "concept", "uid": "entity-stable-id"}
    uid_contains["key"] = relationship_edge_key(uid_contains)
    validate_typed_graph(uid_graph, concept_kinds=concept_kinds)


@pytest.mark.parametrize(
    ("relationship_kind", "sample_kind"),
    [
        ("contains", "containment"),
        ("imports", "import"),
        ("calls", "call"),
        ("entrypoint_for", "entrypoint"),
        ("reads", "data-effect"),
        ("writes", "data-effect"),
        ("depends_on", "dependency"),
    ],
)
def test_each_structural_core_kind_enforces_its_evidence_contract(
    relationship_kind,
    sample_kind,
):
    graph = materialize_typed_graph(_inputs())
    edge = next(
        value for value in graph["edges"] if value["kind"] == relationship_kind
    )
    assert {
        sample["kind"] for sample in edge["evidence"]["samples"]
    } == {sample_kind}
    edge["evidence"]["samples"][0]["kind"] = "wrong-evidence"

    with pytest.raises(KnowledgeGraphError, match=sample_kind):
        validate_typed_graph(graph)


def test_entrypoint_evidence_requires_detector_identity():
    graph = materialize_typed_graph(_inputs())
    edge = next(
        value for value in graph["edges"] if value["kind"] == "entrypoint_for"
    )
    edge["evidence"]["samples"][0].pop("detector")

    with pytest.raises(KnowledgeGraphError, match="detector"):
        validate_typed_graph(graph)


def test_shuffled_analyzer_input_produces_byte_identical_graph():
    first = materialize_typed_graph(_inputs())
    second = materialize_typed_graph(_inputs(reverse=True))

    assert serialize_typed_graph(first) == serialize_typed_graph(second)


def test_inventory_hash_accepts_source_control_bytes_without_emitting_them():
    inputs = _inputs()
    inventory = deepcopy(inputs.inventory)
    inventory["src/a.py"]["module_docstring"] = "Windows path: C:\\build\boutput"

    graph = materialize_typed_graph(
        KnowledgeGraphInputs(
            **{
                **inputs.__dict__,
                "inventory": inventory,
            }
        )
    )
    baseline = materialize_typed_graph(inputs)

    assert graph["input_hashes"]["inventory"] != (
        baseline["input_hashes"]["inventory"]
    )
    assert "\b" not in serialize_typed_graph(graph)


def test_contract_accepts_namespaced_plugin_kind_and_reserved_supersedes():
    graph = materialize_typed_graph(_inputs())
    template = deepcopy(graph["edges"][0])

    template["kind"] = "vendor/contains"
    template["origin"] = "markdown"
    template["key"] = relationship_edge_key(template)
    custom = deepcopy(graph)
    custom["edges"].append(template)
    normalized = next(
        edge
        for edge in validate_typed_graph(custom)["edges"]
        if edge["kind"] == "vendor/contains"
    )
    assert normalized["kind"] == "vendor/contains"
    assert normalized["origin"] == "markdown"

    template["kind"] = "supersedes"
    template["origin"] = "governance"
    template["target"] = {
        "kind": "concept",
        "uid": "governance-id-2",
    }
    template["resolution"] = "resolved"
    template["evidence"].update(
        observed=1,
        unique=1,
        emitted=1,
        omitted=0,
        samples=[
            {
                "kind": "supersession",
                "source": template["from"],
                "target": template["target"],
                "reason": "governance ledger replacement",
            }
        ],
    )
    template["coverage"].update(
        observed=1,
        emitted=1,
        omitted=0,
        limit=20,
        truncated=False,
        limitations=[],
    )
    template["key"] = relationship_edge_key(template)
    reserved = deepcopy(graph)
    reserved["edges"].append(template)
    assert any(
        edge["kind"] == "supersedes"
        for edge in validate_typed_graph(reserved)["edges"]
    )


def test_packaged_schema_covers_all_kinds_origins_resolutions_and_truncation():
    graph = materialize_typed_graph(_inputs(evidence_limit=1))
    template = deepcopy(graph["edges"][0])
    template["kind"] = "vendor/contains"
    template["origin"] = "markdown"
    template["key"] = relationship_edge_key(template)
    graph["edges"].append(template)

    supersedes = deepcopy(template)
    supersedes["kind"] = "supersedes"
    supersedes["origin"] = "governance"
    supersedes["resolution"] = "resolved"
    supersedes["target"] = {"kind": "concept", "uid": "successor-id"}
    supersedes["evidence"].update(
        observed=1,
        unique=1,
        emitted=1,
        omitted=0,
        samples=[
            {
                "kind": "supersession",
                "source": supersedes["from"],
                "target": supersedes["target"],
                "reason": "governance ledger replacement",
            }
        ],
    )
    supersedes["coverage"].update(
        observed=1,
        emitted=1,
        omitted=0,
        limit=1,
        truncated=False,
        limitations=[],
    )
    supersedes["key"] = relationship_edge_key(supersedes)
    graph["edges"].append(supersedes)

    schema = load_knowledge_schema()
    graph_schema = {
        "$schema": schema["$schema"],
        "$defs": schema["$defs"],
        "$ref": "#/$defs/typedGraph",
    }
    validator = Draft202012Validator(graph_schema)

    assert list(validator.iter_errors(graph)) == []
    assert set(CORE_RELATIONSHIP_KINDS) <= {
        edge["kind"] for edge in graph["edges"]
    }
    assert {edge["origin"] for edge in graph["edges"]} == {
        "extracted",
        "inferred",
        "markdown",
        "governance",
    }
    assert {edge["resolution"] for edge in graph["edges"]} == {
        "resolved",
        "ambiguous",
        "external",
        "unresolved",
    }
    assert any(edge["coverage"]["truncated"] for edge in graph["edges"])

    invalid = deepcopy(graph)
    contains = next(edge for edge in invalid["edges"] if edge["kind"] == "contains")
    contains["evidence"]["samples"][0]["kind"] = "wrong-evidence"
    assert list(validator.iter_errors(invalid))


@pytest.mark.parametrize(
    ("mutation", "field"),
    [
        (
            lambda edge: edge.update(key="sha256:" + ("0" * 64)),
            "key",
        ),
        (
            lambda edge: edge["coverage"].update(omitted=99),
            "coverage.omitted",
        ),
        (
            lambda edge: edge["evidence"]["samples"][0]["location"].update(line=0),
            "location.line",
        ),
        (
            lambda edge: edge.update(kind="contains", resolution="external"),
            "target",
        ),
        (
            lambda edge: edge.update(kind="contains-extra"),
            "kind",
        ),
    ],
)
def test_contract_rejects_invalid_keys_coverage_locations_and_core_shapes(
    mutation, field
):
    graph = materialize_typed_graph(_inputs())
    payload = deepcopy(graph)
    edge = payload["edges"][0]
    mutation(edge)
    if field != "key":
        edge["key"] = relationship_edge_key(edge)

    with pytest.raises(KnowledgeGraphError) as exc:
        validate_typed_graph(payload)
    assert field in exc.value.field


def test_materializer_performs_no_io_process_or_network_work(monkeypatch):
    def fail(*_args, **_kwargs):
        raise AssertionError("pure graph materializer attempted external work")

    monkeypatch.setattr(builtins, "open", fail)
    monkeypatch.setattr(subprocess, "run", fail)
    monkeypatch.setattr(socket, "create_connection", fail)

    graph = materialize_typed_graph(_inputs())
    assert graph["edges"]
    json.dumps(graph, sort_keys=True)
