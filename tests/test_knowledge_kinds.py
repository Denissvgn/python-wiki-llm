"""Custom knowledge kinds are declared through one context-scoped registry."""

from __future__ import annotations

import json
from dataclasses import replace

import pytest

from llm_wiki_cli.engine import (
    DEFAULT_KINDS,
    ConceptKindSpec,
    Engine,
    KindRegistry,
    NoProcessHost,
    RelationshipKindSpec,
)
from llm_wiki_cli.services import knowledge_index as index
from llm_wiki_cli.services import knowledge_model as model
from llm_wiki_cli.services.knowledge_kinds import current_kinds, using_kinds
from llm_wiki_cli.services.wiki_surface import PageKind
from tests.knowledge_fixtures import one_module_two_entities_fixture
from tests.test_knowledge_artifacts import _plan
from tests.test_knowledge_validation_receipt import _consume

RUNBOOK = ConceptKindSpec("team/runbook", (PageKind.WORKFLOWS, PageKind.GUIDES))


def _payload(root, *, concept_kind=None, relationship_kind=None):
    plan = _plan(root, one_module_two_entities_fixture())
    payload = json.loads(plan.knowledge_index.content)
    if concept_kind is not None:
        concept = next(c for c in payload["concepts"] if c["document"]["page_kind"] == "workflows")
        concept["concept_kind"] = concept_kind
    if relationship_kind is not None:
        relationship = next(r for r in payload["relationships"] if r["kind"] == "links_to")
        relationship["kind"] = relationship_kind
    return plan, payload


def _with_graph_edge(knowledge, kind):
    graph = {"edges": [{"kind": "contains"}, {"kind": kind}]}
    return replace(knowledge, extensions={**knowledge.extensions, "llm-wiki/typed-graph-v1": graph})


def test_the_default_registry_lists_the_format_kinds_and_accepts_custom_ones(tmp_path) -> None:
    assert current_kinds() is DEFAULT_KINDS
    described = DEFAULT_KINDS.describe()
    assert described["relationship"] == ["derived_from", "links_to"]
    assert "supersedes" in described["graph_relationship"]
    assert described["page"][-1] == "load-order"
    assert described["undeclared"] == "accept"
    dependency_view = next(s for s in DEFAULT_KINDS.concept_kinds if s.name == "dependency-view")
    assert dependency_view.page_kinds == (PageKind.DEPENDENCIES, PageKind.LOAD_ORDER)

    _, payload = _payload(tmp_path, concept_kind="team/anything", relationship_kind="team/reviews")
    knowledge = model.parse_knowledge_index(payload)
    DEFAULT_KINDS.check(_with_graph_edge(knowledge, "team/owns"))


def test_a_declared_concept_kind_is_held_to_its_page_kinds(tmp_path) -> None:
    kinds = DEFAULT_KINDS.with_concept_kind(ConceptKindSpec("team/runbook", (PageKind.GUIDES,)))
    _, payload = _payload(tmp_path, concept_kind="team/runbook")

    with using_kinds(kinds), pytest.raises(model.KnowledgeModelError, match="not allowed on page_kind 'workflows'") as refused:
        model.parse_knowledge_index(payload)
    assert refused.value.field.endswith(".concept_kind")

    with using_kinds(DEFAULT_KINDS.with_concept_kind(RUNBOOK)):
        assert model.parse_knowledge_index(payload).concepts


def test_a_document_only_concept_kind_refuses_structural_evidence(tmp_path) -> None:
    kinds = DEFAULT_KINDS.with_concept_kind(
        ConceptKindSpec("team/note", (PageKind.ENTITIES,), document_only=True))
    _, payload = _payload(tmp_path)
    next(c for c in payload["concepts"] if c["document"]["page_kind"] == "entities")["concept_kind"] = "team/note"

    with using_kinds(kinds), pytest.raises(model.KnowledgeModelError, match="document-only"):
        model.parse_knowledge_index(payload)


def test_rejecting_undeclared_refuses_every_unknown_custom_kind(tmp_path) -> None:
    strict = DEFAULT_KINDS.rejecting_undeclared()
    _, plain = _payload(tmp_path / "plain")
    _, custom_concept = _payload(tmp_path / "concept", concept_kind="team/runbook")
    _, custom_relationship = _payload(tmp_path / "relationship", relationship_kind="team/reviews")

    with using_kinds(strict):
        knowledge = model.parse_knowledge_index(plain)
        with pytest.raises(model.KnowledgeModelError, match="'team/runbook' is not a declared concept kind"):
            model.parse_knowledge_index(custom_concept)
        with pytest.raises(model.KnowledgeModelError, match="not a declared relationship kind"):
            model.parse_knowledge_index(custom_relationship)
    with pytest.raises(model.KnowledgeModelError, match="typed-graph relationship") as refused:
        strict.check(_with_graph_edge(knowledge, "team/owns"))
    assert refused.value.field == "extensions.llm-wiki/typed-graph-v1.edges[1].kind"

    declared = (strict.with_concept_kind(RUNBOOK)
                .with_relationship_kind(RelationshipKindSpec("team/reviews"))
                .with_graph_relationship_kind(RelationshipKindSpec("team/owns")))
    with using_kinds(declared):
        model.parse_knowledge_index(custom_concept)
        model.parse_knowledge_index(custom_relationship)
    declared.check(_with_graph_edge(knowledge, "team/owns"))


def test_a_receipt_is_not_trusted_under_another_kind_registry(tmp_path) -> None:
    plan, payload = _payload(tmp_path)
    knowledge = model.parse_knowledge_index(payload)

    with index._knowledge_validation_operation(tmp_path):
        receipt = index._validated_index_receipt(knowledge, tmp_path)
        with using_kinds(DEFAULT_KINDS.rejecting_undeclared()), pytest.raises(TypeError, match="validators"):
            _consume(plan, receipt, tmp_path)
        assert _consume(plan, receipt, tmp_path).knowledge == knowledge


def test_identity_tracks_acceptance_but_not_descriptions() -> None:
    base = DEFAULT_KINDS.identity()
    described = DEFAULT_KINDS.with_relationship_kind(RelationshipKindSpec("team/reviews", "a review"))
    plain = DEFAULT_KINDS.with_relationship_kind(RelationshipKindSpec("team/reviews"))

    assert described.identity() == plain.identity() != base
    assert DEFAULT_KINDS.rejecting_undeclared().identity() != base
    assert DEFAULT_KINDS.with_concept_kind(RUNBOOK).identity() != DEFAULT_KINDS.with_concept_kind(
        ConceptKindSpec("team/runbook", (PageKind.GUIDES,))).identity()


def test_engines_check_kinds_with_their_own_registry(tmp_path) -> None:
    _, payload = _payload(tmp_path, concept_kind="team/runbook")
    strict = Engine(host=NoProcessHost(), kinds=DEFAULT_KINDS.rejecting_undeclared())

    with pytest.raises(model.KnowledgeModelError, match="not a declared concept kind"):
        strict.call(model.parse_knowledge_index, payload)
    assert Engine(host=NoProcessHost()).call(model.parse_knowledge_index, payload).concepts
    assert strict.capabilities()["kinds"] == {**DEFAULT_KINDS.describe(), "undeclared": "reject"}
    with strict.operation() as operation:
        assert operation.kinds is current_kinds()


def test_registry_values_are_checked() -> None:
    with pytest.raises(ValueError, match="qualified"):
        ConceptKindSpec("runbook", (PageKind.GUIDES,))
    with pytest.raises(ValueError, match="page kind"):
        ConceptKindSpec("team/runbook", ("policies",))  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="distinct page kinds"):
        ConceptKindSpec("team/runbook", ())
    with pytest.raises(ValueError, match="qualified"):
        DEFAULT_KINDS.with_relationship_kind(RelationshipKindSpec("reviews"))
    with pytest.raises(ValueError, match="unique"):
        DEFAULT_KINDS.with_concept_kind(RUNBOOK).with_concept_kind(RUNBOOK)
    with pytest.raises(ValueError, match="built-in"):
        KindRegistry(concept_kinds=(RUNBOOK,))
    with pytest.raises(ValueError, match="built-in"):
        KindRegistry(concept_kinds=(ConceptKindSpec("workflow", (PageKind.GUIDES,)),
                                    *DEFAULT_KINDS.concept_kinds[:2], *DEFAULT_KINDS.concept_kinds[3:]))
    with pytest.raises(ValueError, match="undeclared"):
        KindRegistry(undeclared="warn")  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="KindRegistry"):
        Engine(kinds=object())  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="KindRegistry"), using_kinds(object()):  # type: ignore[arg-type]
        pass
