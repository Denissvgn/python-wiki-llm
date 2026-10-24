"""Derived views cannot borrow source or aggregate evidence as currentness."""

from __future__ import annotations

from dataclasses import replace

import pytest

from llm_wiki_cli import api
from llm_wiki_cli.services.knowledge_coverage import build_knowledge_coverage
from llm_wiki_cli.services.knowledge_freshness import (
    evaluate_knowledge_freshness,
    structural_freshness_modeled,
)
from llm_wiki_cli.services.knowledge_index import validate_knowledge_index
from llm_wiki_cli.services.knowledge_model import (
    ComputedFreshness,
    EvidenceBasis,
    EvidenceState,
    KnowledgeModelError,
    ObservationScope,
    Origin,
    Verification,
    parse_knowledge_index,
    serialize_knowledge_index,
)
from tests.knowledge_fixtures import fixture_hash, one_module_two_entities_fixture
from tests.test_knowledge_freshness import _live_evaluation

WORKFLOW = "llm-wiki://workflows/onboarding"
MODULE = "llm-wiki://modules/accounts"


@pytest.mark.parametrize("evidence", ["absent", "aggregate", "borrowed-module", "extension-only"])
@pytest.mark.parametrize("live_change", ["none", "source", "producer", "options", "snapshot", "missing-source"])
def test_derived_view_stays_unmodeled_even_when_other_evidence_matches(evidence, live_change):
    knowledge = parse_knowledge_index(one_module_two_entities_fixture().knowledge_payload)
    workflow = next(c for c in knowledge.concepts if c.locator == WORKFLOW)
    module = next(c for c in knowledge.concepts if c.locator == MODULE)
    module_basis = module.facets.structure.basis
    assert module_basis is not None and module_basis.source_path is not None
    structure = workflow.facets.structure
    if evidence == "aggregate":
        structure = replace(structure, origin=Origin.INFERRED, evidence=EvidenceState.PRESENT,
                            basis=EvidenceBasis(scope=ObservationScope.AGGREGATE,
                                                aggregate_input_hash=fixture_hash("matching-trace")))
    elif evidence == "borrowed-module":
        structure = replace(structure, origin=Origin.EXTRACTED, evidence=EvidenceState.PRESENT, basis=module_basis)
    elif evidence == "extension-only":
        structure = replace(structure, extensions={"example.invalid/derived-observation": {
            "matching_trace_hash": fixture_hash("matching-trace"),
            "source_snapshot_hash": knowledge.bundle.snapshot.source_snapshot_hash,
        }})
    workflow = replace(workflow, facets=replace(workflow.facets, structure=structure))
    knowledge = replace(knowledge, concepts=tuple(workflow if c.locator == WORKFLOW else c for c in knowledge.concepts))
    live = _live_evaluation(knowledge)
    if live_change == "source":
        live = _live_evaluation(knowledge, source_hash_by_path={module_basis.source_path: fixture_hash("source-changed")})
    elif live_change == "producer":
        live = replace(live, producer=replace(live.producer, tool=replace(live.producer.tool, version="9.9.9")))
    elif live_change == "options":
        live = replace(live, generation_options_hash=fixture_hash("options-changed"))
    elif live_change == "snapshot":
        knowledge = replace(knowledge, bundle=replace(knowledge.bundle, snapshot=replace(
            knowledge.bundle.snapshot, source_snapshot_hash=fixture_hash("other-snapshot"))))
    elif live_change == "missing-source":
        live = _live_evaluation(knowledge, missing_source_paths=frozenset({module_basis.source_path}))
    before = serialize_knowledge_index(knowledge)
    outcome = evaluate_knowledge_freshness(knowledge, live).by_locator[WORKFLOW]
    assert outcome.state is ComputedFreshness.UNKNOWN
    assert outcome.reason_code == "freshness-not-modeled"
    assert not outcome.live_comparison_performed
    assert not structural_freshness_modeled(workflow)
    assert workflow.facets.semantics.verification is Verification.UNTRACKED
    assert serialize_knowledge_index(knowledge) == before


def test_semantic_edit_does_not_gain_structural_or_human_approval():
    knowledge = parse_knowledge_index(one_module_two_entities_fixture().knowledge_payload)
    workflow = next(c for c in knowledge.concepts if c.locator == WORKFLOW)
    changed = replace(workflow, facets=replace(workflow.facets, semantics=replace(
        workflow.facets.semantics, page_hash=fixture_hash("new-authored-behavior"))))
    knowledge = replace(knowledge, concepts=tuple(changed if c.locator == WORKFLOW else c for c in knowledge.concepts))
    report = evaluate_knowledge_freshness(knowledge, _live_evaluation(knowledge))
    assert report.by_locator[WORKFLOW].state is ComputedFreshness.UNKNOWN
    assert report.by_locator[MODULE].state is ComputedFreshness.CURRENT
    assert changed.facets.semantics.verification is Verification.UNTRACKED
    assert all(c.facets.semantics.verification is Verification.UNTRACKED for c in knowledge.concepts)


@pytest.fixture
def source_backed_views(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    source = tmp_path / "src"
    source.mkdir()
    (source / "app.py").write_text(
        '__all__ = ["checkout", "status"]\nfrom engine import compute\nfrom info import describe\n'
        'def checkout(value):\n    return compute(value)\n'
        'def status(value):\n    return describe(value)\n', encoding="utf-8",
    )
    (source / "engine.py").write_text(
        'def compute(value):\n    return clean(value)\n'
        'def clean(value):\n    return value\n'
        'def archive(value):\n    return value\n', encoding="utf-8",
    )
    (source / "info.py").write_text('def describe(value):\n    return value\n', encoding="utf-8")
    api.bootstrap_wiki("src", "wiki")
    return source


def test_source_backed_view_needs_its_own_basis_not_just_an_unchanged_root(source_backed_views):
    before = api.build_documentation_query_service(src_dir="src", wiki_dir="wiki")
    path = source_backed_views / "engine.py"
    path.write_text(path.read_text(encoding="utf-8").replace("return clean(value)", "return archive(value)"), encoding="utf-8")
    after = api.build_documentation_query_service(src_dir="src", wiki_dir="wiki")
    assert before.inventory["app.py"] == after.inventory["app.py"]
    first = before.flow_segment("app.py:checkout")
    second = after.flow_segment("app.py:checkout")
    assert [s["symbol"] for s in first["steps"]] == ["checkout", "compute", "clean"]
    assert [s["symbol"] for s in second["steps"]] == ["checkout", "compute", "archive"]
    assert [s["symbol"] for s in after.flow_segment("app.py:status")["steps"]] == ["status", "describe"]
    explained = after.explain_evidence("llm-wiki://flows/api-checkout")
    assert explained["found"] is True
    assert explained["evidence"]["freshness"]["state"] == "unknown"
    assert explained["evidence"]["freshness"]["reason"] == "freshness-not-modeled"
    view = after.knowledge_view
    assert view is not None and view.freshness is not None
    assert view.freshness.by_locator["llm-wiki://modules/app"].state is ComputedFreshness.CURRENT
    counts = build_knowledge_coverage(view)["counts"]
    assert counts["total"] == 9
    assert (counts["modeled"], counts["unmodeled"], counts["compared"]) == (3, 6, 3)
    assert sum(counts["modeled_freshness"].values()) == 3


@pytest.mark.parametrize("declaration", ["aggregate-only", "present-aggregate", "borrowed-module"])
def test_native_writer_contract_rejects_a_fabricated_derived_basis(source_backed_views, declaration):
    service = api.build_documentation_query_service(src_dir="src", wiki_dir="wiki")
    view = service.knowledge_view
    assert view is not None and view.knowledge is not None
    knowledge = view.knowledge
    target = next(c for c in knowledge.concepts if c.locator == "llm-wiki://flows/api-checkout")
    basis = EvidenceBasis(scope=ObservationScope.AGGREGATE,
                          aggregate_input_hash=fixture_hash("same-snapshot-and-trace"))
    if declaration == "borrowed-module":
        basis = next(c.facets.structure.basis for c in knowledge.concepts if c.locator == "llm-wiki://modules/app")
    structure = replace(target.facets.structure, basis=basis)
    if declaration == "present-aggregate":
        structure = replace(structure, origin=Origin.INFERRED, evidence=EvidenceState.PRESENT)
    invented = replace(target, facets=replace(target.facets, structure=structure))
    changed = replace(knowledge, concepts=tuple(invented if c.locator == target.locator else c for c in knowledge.concepts))
    with pytest.raises(KnowledgeModelError) as refusal:
        validate_knowledge_index(changed)
    assert refusal.value.field.endswith(".origin" if declaration == "present-aggregate" else ".basis")
