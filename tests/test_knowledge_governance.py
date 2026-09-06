"""Durable identity, lifecycle, review, projection, and recovery tests."""

from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from llm_wiki_cli.services import knowledge_governance as governance
from llm_wiki_cli.services.contracts import SECTION_OWNERSHIP_EXTENSION_KEY
from llm_wiki_cli.services.knowledge_governance import (
    ALIAS_LOCATOR,
    ALIAS_NATURAL_KEY,
    GOVERNANCE_EXTENSION_KEY,
    GOVERNANCE_FILENAME,
    GOVERNANCE_LOCK_FILENAME,
    ConceptGovernanceReference,
    GovernanceActor,
    GovernanceConflictError,
    GovernanceError,
    GovernanceLedger,
    GovernanceWriteStage,
    ReviewEvidence,
    add_alias,
    add_review_event,
    alias_key,
    apply_governance_projection,
    concept_references_from_knowledge,
    current_review_evidence,
    evaluate_review_event,
    governance_lock,
    load_governance,
    move_concept,
    reconcile_concepts,
    review_scope_hash,
    save_governance,
    set_lifecycle,
    validate_governance_ledger,
    validate_governance_projection,
)
from llm_wiki_cli.services.knowledge_model import (
    EvidenceBasis,
    EvidenceState,
    Lifecycle,
    ObservationScope,
    StructuralFacet,
    knowledge_index_to_payload,
    load_knowledge_schema,
    parse_knowledge_index,
)
from llm_wiki_cli.services.section_ownership import (
    observe_page_sections,
    section_ownership_extension,
)
from llm_wiki_cli.services.wiki_surface import PageKind
from tests.knowledge_fixtures import one_module_two_entities_fixture
from tests.test_knowledge_model import _minimum_payload


FIXED_TIME = "2026-07-27T12:00:00Z"
HUMAN = GovernanceActor(kind="human", actor_id="reviewer-1")
TOOL = GovernanceActor(kind="tool", actor_id="llm-wiki-cli")


def _reference(
    locator: str,
    path: str,
    kind: str = "source-module",
) -> ConceptGovernanceReference:
    return ConceptGovernanceReference(
        locator=locator,
        concept_kind=kind,
        natural_key=f"{kind}:{path}",
    )


def _two_concept_ledger() -> GovernanceLedger:
    return reconcile_concepts(
        GovernanceLedger.empty("kb_test-bundle"),
        (
            _reference(
                "llm-wiki://modules/alpha",
                "modules/alpha.md",
            ),
            _reference(
                "llm-wiki://modules/beta",
                "modules/beta.md",
            ),
        ),
    )


def _reviewable_knowledge(markdown: str = "# sync_cmd\n## Description\nStable.\n"):
    payload = _minimum_payload()
    observed = observe_page_sections(
        markdown,
        "llm-wiki://modules/sync_cmd",
        PageKind.MODULES,
    )
    payload["extensions"] = section_ownership_extension([observed])
    model = parse_knowledge_index(payload)
    section = next(
        section
        for section in observed.sections
        if section.semantic_hash is not None
    )
    return model, section.locator, section.semantic_hash


def _review_ledger(knowledge):
    return reconcile_concepts(
        GovernanceLedger.empty("kb_review-bundle"),
        concept_references_from_knowledge(knowledge),
    )


def _source_evidence_knowledge(knowledge, source_hash: str):
    concept = knowledge.concepts[0]
    structure = StructuralFacet(
        evidence=EvidenceState.PRESENT,
        basis=EvidenceBasis(
            scope=ObservationScope.MODULE,
            source_path="src/sync_cmd.py",
            extractor_ref="python-ast",
            source_content_hash=source_hash,
            concept_observation_hash="sha256:" + ("b" * 64),
        ),
    )
    return replace(
        knowledge,
        concepts=(
            replace(
                concept,
                facets=replace(concept.facets, structure=structure),
            ),
        ),
    )


def test_allocation_and_serialization_are_deterministic():
    references = (
        _reference("llm-wiki://modules/beta", "modules/beta.md"),
        _reference("llm-wiki://modules/alpha", "modules/alpha.md"),
    )
    first = reconcile_concepts(
        GovernanceLedger.empty("kb_deterministic"),
        references,
    )
    second = reconcile_concepts(
        GovernanceLedger.empty("kb_deterministic"),
        tuple(reversed(references)),
    )

    assert first == second
    assert first.to_bytes() == second.to_bytes()
    assert tuple(first.concepts) == tuple(sorted(first.concepts))
    assert reconcile_concepts(first, references) == first


def test_supported_move_preserves_uid_and_retains_both_old_aliases():
    initial = reconcile_concepts(
        GovernanceLedger.empty("kb_move-test"),
        (_reference("llm-wiki://modules/old", "modules/old.md"),),
    )
    uid = next(iter(initial.concepts))
    moved = reconcile_concepts(
        initial,
        (_reference("llm-wiki://modules/new", "modules/new.md"),),
        moves={"llm-wiki://modules/old": "llm-wiki://modules/new"},
    )

    assert tuple(moved.concepts) == (uid,)
    assert moved.concepts[uid].locator == "llm-wiki://modules/new"
    assert moved.aliases[alias_key(ALIAS_LOCATOR, "llm-wiki://modules/old")].uid == uid
    assert (
        moved.aliases[
            alias_key(ALIAS_NATURAL_KEY, "source-module:modules/old.md")
        ].uid
        == uid
    )
    assert (
        reconcile_concepts(
            moved,
            (_reference("llm-wiki://modules/new", "modules/new.md"),),
        )
        == moved
    )


def test_explicit_move_can_return_to_an_alias_without_losing_history():
    ledger = _two_concept_ledger()
    uid = next(
        uid
        for uid, allocation in ledger.concepts.items()
        if allocation.locator == "llm-wiki://modules/alpha"
    )
    moved = move_concept(
        ledger,
        uid,
        locator="llm-wiki://modules/gamma",
        natural_key="source-module:modules/gamma.md",
    )
    restored = move_concept(
        moved,
        uid,
        locator="llm-wiki://modules/alpha",
        natural_key="source-module:modules/alpha.md",
    )

    assert alias_key(ALIAS_LOCATOR, "llm-wiki://modules/alpha") not in restored.aliases
    assert restored.aliases[
        alias_key(ALIAS_LOCATOR, "llm-wiki://modules/gamma")
    ].uid == uid


def test_delete_and_recreate_at_new_coordinates_is_not_silently_a_move():
    initial = reconcile_concepts(
        GovernanceLedger.empty("kb_recreate"),
        (_reference("llm-wiki://modules/old", "modules/old.md"),),
    )
    old_uid = next(iter(initial.concepts))
    without_current = reconcile_concepts(initial, ())
    recreated = reconcile_concepts(
        without_current,
        (_reference("llm-wiki://modules/new", "modules/new.md"),),
    )

    assert len(recreated.concepts) == 2
    assert recreated.concepts[old_uid].locator == "llm-wiki://modules/old"
    assert {
        allocation.locator for allocation in recreated.concepts.values()
    } == {"llm-wiki://modules/old", "llm-wiki://modules/new"}


def test_alias_and_allocation_collisions_fail_without_mutating_ledger():
    ledger = _two_concept_ledger()
    alpha_uid = next(
        uid
        for uid, allocation in ledger.concepts.items()
        if allocation.locator.endswith("/alpha")
    )
    before = ledger.to_bytes()

    with pytest.raises(GovernanceError, match="owned"):
        add_alias(
            ledger,
            alpha_uid,
            ALIAS_LOCATOR,
            "llm-wiki://modules/beta",
        )
    with pytest.raises(GovernanceError, match="owned"):
        add_alias(
            ledger,
            alpha_uid,
            ALIAS_LOCATOR,
            "modules/beta.md",
        )
    with pytest.raises(GovernanceError, match="owned"):
        move_concept(
            ledger,
            alpha_uid,
            locator="llm-wiki://modules/beta",
            natural_key="source-module:modules/new-alpha.md",
        )
    assert ledger.to_bytes() == before


def test_lifecycle_is_explicit_predecessor_linked_and_cycle_safe():
    ledger = _two_concept_ledger()
    alpha_uid, beta_uid = tuple(ledger.concepts)
    active = set_lifecycle(
        ledger,
        alpha_uid,
        Lifecycle.ACTIVE,
        actor=TOOL,
        authored_at=FIXED_TIME,
    )
    both_active = set_lifecycle(
        active,
        beta_uid,
        Lifecycle.ACTIVE,
        actor=TOOL,
        authored_at="2026-07-27T12:00:01Z",
    )
    superseded = set_lifecycle(
        both_active,
        alpha_uid,
        Lifecycle.SUPERSEDED,
        successor_uid=beta_uid,
        actor=HUMAN,
        authored_at="2026-07-27T12:00:02Z",
        reason="explicit-supersession",
    )
    assert (
        set_lifecycle(
            superseded,
            alpha_uid,
            Lifecycle.SUPERSEDED,
            successor_uid=beta_uid,
            actor=HUMAN,
            authored_at="2026-07-27T12:00:02Z",
            reason="explicit-supersession",
        )
        == superseded
    )
    with pytest.raises(GovernanceError, match="is required"):
        set_lifecycle(
            superseded,
            alpha_uid,
            Lifecycle.SUPERSEDED,
            actor=HUMAN,
            authored_at="2026-07-27T12:00:02Z",
            reason="explicit-supersession",
        )
    with pytest.raises(GovernanceError, match="different event metadata"):
        set_lifecycle(
            superseded,
            alpha_uid,
            Lifecycle.SUPERSEDED,
            successor_uid=beta_uid,
            actor=HUMAN,
            authored_at="2026-07-27T12:00:04Z",
            reason="explicit-supersession",
        )
    with pytest.raises(GovernanceError, match="actor.kind"):
        set_lifecycle(
            superseded,
            alpha_uid,
            Lifecycle.SUPERSEDED,
            successor_uid=beta_uid,
            actor=GovernanceActor("git", "inferred"),
            authored_at="2026-07-27T12:00:02Z",
            reason="explicit-supersession",
        )

    with pytest.raises(GovernanceError, match="supersession cycle"):
        set_lifecycle(
            superseded,
            beta_uid,
            Lifecycle.SUPERSEDED,
            successor_uid=alpha_uid,
            actor=HUMAN,
            authored_at="2026-07-27T12:00:03Z",
            reason="explicit-supersession",
        )
    assert len(superseded.lifecycle_events) == 3


def test_concurrent_lifecycle_forks_require_manual_resolution():
    ledger = _two_concept_ledger()
    uid = next(iter(ledger.concepts))
    active = set_lifecycle(
        ledger,
        uid,
        Lifecycle.ACTIVE,
        actor=TOOL,
        authored_at=FIXED_TIME,
    )
    left = set_lifecycle(
        active,
        uid,
        Lifecycle.DEPRECATED,
        actor=HUMAN,
        authored_at="2026-07-27T12:01:00Z",
    )
    right = set_lifecycle(
        active,
        uid,
        Lifecycle.DEPRECATED,
        actor=HUMAN,
        authored_at="2026-07-27T12:02:00Z",
    )
    merged_events = dict(left.lifecycle_events)
    merged_events.update(right.lifecycle_events)

    with pytest.raises(GovernanceError, match="concurrent successor"):
        validate_governance_ledger(
            replace(active, lifecycle_events=merged_events)
        )


def test_validation_recomputes_lifecycle_event_ids_from_canonical_content():
    ledger = _two_concept_ledger()
    uid = next(iter(ledger.concepts))
    active = set_lifecycle(
        ledger,
        uid,
        Lifecycle.ACTIVE,
        actor=TOOL,
        authored_at=FIXED_TIME,
    )
    event_id, event = next(iter(active.lifecycle_events.items()))
    assert (
        event_id
        == "le_b176d378b6d0148819f84cee63c46f5abaa0c30b230d9eec9327834599eeeda4"
    )
    tampered = replace(event, reason="tampered-reason")

    with pytest.raises(
        GovernanceError,
        match="event ID does not match canonical event content",
    ) as raised:
        validate_governance_ledger(
            replace(active, lifecycle_events={event_id: tampered})
        )

    assert raised.value.code == "governance-event-conflict"


def test_validation_refuses_rehashed_noncanonical_event_time_before_save(
    tmp_path: Path,
):
    ledger = _two_concept_ledger()
    uid = next(iter(ledger.concepts))
    active = set_lifecycle(
        ledger,
        uid,
        Lifecycle.ACTIVE,
        actor=TOOL,
        authored_at=FIXED_TIME,
    )
    _, event = next(iter(active.lifecycle_events.items()))
    noncanonical = replace(
        event,
        event_id="",
        authored_at="2026-07-27T12:00:00+00:00",
    )
    noncanonical = replace(
        noncanonical,
        event_id=governance._derived_event_id(
            "le",
            governance._lifecycle_event_digest_payload(noncanonical),
        ),
    )
    forged = replace(
        active,
        lifecycle_events={noncanonical.event_id: noncanonical},
    )

    with pytest.raises(GovernanceError, match="canonical UTC"):
        save_governance(tmp_path, forged, expected_hash=None)

    assert not (tmp_path / GOVERNANCE_FILENAME).exists()


def test_review_validity_reports_each_live_expiry_dimension():
    knowledge, section_locator, scope_hash = _reviewable_knowledge()
    source_knowledge = _source_evidence_knowledge(
        knowledge,
        "sha256:" + ("a" * 64),
    )
    ledger = _review_ledger(source_knowledge)
    uid = next(iter(ledger.concepts))
    evidence = current_review_evidence(source_knowledge.concepts[0])
    assert evidence is not None
    reviewed = add_review_event(
        ledger,
        uid,
        section_locator=section_locator,
        scope_hash=scope_hash,
        evidence=evidence,
        reviewer=HUMAN,
        method="manual-review",
        method_version="1",
        authored_at=FIXED_TIME,
    )
    event = next(iter(reviewed.review_events.values()))

    assert evaluate_review_event(event, reviewed, source_knowledge).reasons == ()

    changed_scope, _, _ = _reviewable_knowledge(
        "# sync_cmd\n## Description\nChanged semantics.\n"
    )
    changed_scope = _source_evidence_knowledge(
        changed_scope,
        "sha256:" + ("a" * 64),
    )
    assert evaluate_review_event(event, reviewed, changed_scope).reasons == (
        "scope-changed",
    )

    changed_evidence = _source_evidence_knowledge(
        knowledge,
        "sha256:" + ("c" * 64),
    )
    assert evaluate_review_event(event, reviewed, changed_evidence).reasons == (
        "evidence-changed",
    )

    incompatible = replace(
        source_knowledge,
        concepts=(
            replace(
                source_knowledge.concepts[0],
                facets=replace(
                    source_knowledge.concepts[0].facets,
                    structure=StructuralFacet(evidence=EvidenceState.MISSING),
                ),
            ),
        ),
    )
    assert evaluate_review_event(event, reviewed, incompatible).reasons == (
        "basis-incompatible",
    )

    no_sections = replace(
        source_knowledge,
        extensions={
            key: value
            for key, value in source_knowledge.extensions.items()
            if key != SECTION_OWNERSHIP_EXTENSION_KEY
        },
    )
    assert evaluate_review_event(event, reviewed, no_sections).reasons == (
        "section-missing",
    )

    no_concept = replace(source_knowledge, concepts=())
    assert evaluate_review_event(event, reviewed, no_concept).reasons == (
        "concept-missing",
    )


def test_review_requires_a_human_actor_and_semantic_section():
    knowledge, section_locator, scope_hash = _reviewable_knowledge()
    ledger = _review_ledger(knowledge)
    uid = next(iter(ledger.concepts))
    evidence = ReviewEvidence(mode="no-source")

    with pytest.raises(GovernanceError, match="must be 'human'"):
        add_review_event(
            ledger,
            uid,
            section_locator=section_locator,
            scope_hash=scope_hash,
            evidence=evidence,
            reviewer=TOOL,
            method="manual-review",
            method_version="1",
            authored_at=FIXED_TIME,
        )
    generated_locator = (
        "llm-wiki://modules/sync_cmd#section/sync_cmd~1"
    )
    with pytest.raises(GovernanceError, match="semantic"):
        review_scope_hash(knowledge, generated_locator)


def test_review_authoring_rejects_a_section_owned_by_another_concept():
    knowledge, _section_locator, scope_hash = _reviewable_knowledge()
    ledger = _review_ledger(knowledge)
    uid = next(iter(ledger.concepts))

    with pytest.raises(
        GovernanceError,
        match="must belong to the reviewed concept",
    ):
        add_review_event(
            ledger,
            uid,
            section_locator=(
                "llm-wiki://modules/another"
                "#section/another~1/Description~1"
            ),
            scope_hash=scope_hash,
            evidence=ReviewEvidence(mode="no-source"),
            reviewer=HUMAN,
            method="manual-review",
            method_version="1",
            authored_at=FIXED_TIME,
        )


def test_validation_rejects_rehashed_cross_concept_review_on_load(
    tmp_path: Path,
):
    ledger = _two_concept_ledger()
    alpha_uid = next(
        uid
        for uid, allocation in ledger.concepts.items()
        if allocation.locator == "llm-wiki://modules/alpha"
    )
    beta_uid = next(
        uid
        for uid, allocation in ledger.concepts.items()
        if allocation.locator == "llm-wiki://modules/beta"
    )
    reviewed = add_review_event(
        ledger,
        beta_uid,
        section_locator=(
            "llm-wiki://modules/beta#section/beta~1/Description~1"
        ),
        scope_hash="sha256:" + ("a" * 64),
        evidence=ReviewEvidence(mode="no-source"),
        reviewer=HUMAN,
        method="manual-review",
        method_version="1",
        authored_at=FIXED_TIME,
    )
    prior_id, event = next(iter(reviewed.review_events.items()))
    forged_body = event.to_payload()
    forged_body["concept_uid"] = alpha_uid
    forged_id = governance._derived_event_id("rv", forged_body)
    forged_event = replace(
        event,
        event_id=forged_id,
        concept_uid=alpha_uid,
    )
    forged = replace(
        reviewed,
        review_events={forged_id: forged_event},
    )

    with pytest.raises(
        GovernanceError,
        match="current or historical locator",
    ) as raised:
        validate_governance_ledger(forged)
    assert raised.value.code == "governance-review-scope-mismatch"

    payload = reviewed.to_payload()
    review_payloads = payload["review_events"]
    assert isinstance(review_payloads, dict)
    review_payloads.pop(prior_id)
    review_payloads[forged_id] = forged_event.to_payload()
    (tmp_path / GOVERNANCE_FILENAME).write_bytes(
        governance.formatted_json_bytes(payload)
    )
    with pytest.raises(
        GovernanceError,
        match="current or historical locator",
    ):
        load_governance(tmp_path)


def test_validation_preserves_reviews_bound_to_a_historical_locator():
    ledger = _two_concept_ledger()
    uid = next(
        uid
        for uid, allocation in ledger.concepts.items()
        if allocation.locator == "llm-wiki://modules/alpha"
    )
    reviewed = add_review_event(
        ledger,
        uid,
        section_locator=(
            "llm-wiki://modules/alpha#section/alpha~1/Description~1"
        ),
        scope_hash="sha256:" + ("a" * 64),
        evidence=ReviewEvidence(mode="no-source"),
        reviewer=HUMAN,
        method="manual-review",
        method_version="1",
        authored_at=FIXED_TIME,
    )
    moved = move_concept(
        reviewed,
        uid,
        locator="llm-wiki://modules/renamed-alpha",
        natural_key="source-module:modules/renamed-alpha.md",
    )

    assert validate_governance_ledger(moved) == moved


def test_validation_recomputes_review_event_ids_from_canonical_content():
    ledger = _two_concept_ledger()
    uid = next(iter(ledger.concepts))
    reviewed = add_review_event(
        ledger,
        uid,
        section_locator=(
            f"{ledger.concepts[uid].locator}"
            "#section/concept~1/Description~1"
        ),
        scope_hash="sha256:" + ("a" * 64),
        evidence=ReviewEvidence(mode="no-source"),
        reviewer=HUMAN,
        method="manual-review",
        method_version="1",
        authored_at=FIXED_TIME,
    )
    event_id, event = next(iter(reviewed.review_events.items()))
    assert (
        event_id
        == "rv_97365dc9bf8b05d8f878610224b024d5b37c79340b712ba22b95a7e45d572c1b"
    )
    tampered = replace(event, method_version="2")

    with pytest.raises(
        GovernanceError,
        match="event ID does not match canonical event content",
    ) as raised:
        validate_governance_ledger(
            replace(reviewed, review_events={event_id: tampered})
        )

    assert raised.value.code == "governance-event-conflict"


def test_validation_refuses_rehashed_noncanonical_review_evidence():
    ledger = _two_concept_ledger()
    uid = next(iter(ledger.concepts))
    reviewed = add_review_event(
        ledger,
        uid,
        section_locator=(
            f"{ledger.concepts[uid].locator}"
            "#section/concept~1/Description~1"
        ),
        scope_hash="sha256:" + ("a" * 64),
        evidence=ReviewEvidence(
            mode="source",
            basis_ids=("scope:repository", "extractor:wiki-v1"),
            basis_hashes=(
                "sha256:" + ("c" * 64),
                "sha256:" + ("b" * 64),
            ),
        ),
        reviewer=HUMAN,
        method="manual-review",
        method_version="1",
        authored_at=FIXED_TIME,
    )
    _, event = next(iter(reviewed.review_events.items()))
    noncanonical = replace(
        event,
        event_id="",
        evidence=ReviewEvidence(
            mode="source",
            basis_ids=(
                "scope:repository",
                "extractor:wiki-v1",
                "scope:repository",
            ),
            basis_hashes=(
                "sha256:" + ("c" * 64),
                "sha256:" + ("b" * 64),
            ),
        ),
    )
    noncanonical = replace(
        noncanonical,
        event_id=governance._derived_event_id(
            "rv",
            governance._review_event_digest_payload(noncanonical),
        ),
    )

    with pytest.raises(GovernanceError, match="sorted unique"):
        validate_governance_ledger(
            replace(
                reviewed,
                review_events={noncanonical.event_id: noncanonical},
            )
        )


def test_projection_binds_uid_lifecycle_reviews_hash_and_event_truncation():
    knowledge, section_locator, scope_hash = _reviewable_knowledge()
    ledger = _review_ledger(knowledge)
    uid = next(iter(ledger.concepts))
    active = set_lifecycle(
        ledger,
        uid,
        Lifecycle.ACTIVE,
        actor=TOOL,
        authored_at=FIXED_TIME,
    )
    deprecated = set_lifecycle(
        active,
        uid,
        Lifecycle.DEPRECATED,
        actor=HUMAN,
        authored_at="2026-07-27T12:01:00Z",
    )
    reviewed = add_review_event(
        deprecated,
        uid,
        section_locator=section_locator,
        scope_hash=scope_hash,
        evidence=ReviewEvidence(mode="no-source"),
        reviewer=HUMAN,
        method="manual-review",
        method_version="1",
        authored_at="2026-07-27T12:02:00Z",
    )
    projected = apply_governance_projection(
        knowledge,
        reviewed,
        event_limit=1,
    )
    summary = projected.concepts[0].extensions[GOVERNANCE_EXTENSION_KEY]

    assert projected.concepts[0].lifecycle is Lifecycle.DEPRECATED
    assert summary["uid"] == uid
    assert summary["lifecycle_events"]["returned"] == 1
    assert summary["lifecycle_events"]["total"] == 2
    assert summary["lifecycle_events"]["limit"] == 1
    assert summary["lifecycle_events"]["truncated"] is True
    assert summary["reviews"]["items"][0]["state"] == "valid"
    assert summary["reviews"]["items"][0]["reasons"] == []
    assert validate_governance_projection(projected, ledger=reviewed) is not None


def test_projection_rejects_tampered_supersession_edge_evidence():
    knowledge = parse_knowledge_index(
        one_module_two_entities_fixture().knowledge_payload
    )
    ledger = reconcile_concepts(
        GovernanceLedger.empty("kb_supersession_evidence"),
        concept_references_from_knowledge(knowledge),
    )
    source_uid = next(
        uid
        for uid, allocation in ledger.concepts.items()
        if allocation.locator == "llm-wiki://entities/User"
    )
    successor_uid = next(
        uid
        for uid, allocation in ledger.concepts.items()
        if allocation.locator == "llm-wiki://entities/AccountService"
    )
    ledger = set_lifecycle(
        ledger,
        source_uid,
        Lifecycle.ACTIVE,
        actor=HUMAN,
        authored_at="2026-07-27T12:00:00Z",
    )
    ledger = set_lifecycle(
        ledger,
        source_uid,
        Lifecycle.SUPERSEDED,
        successor_uid=successor_uid,
        actor=HUMAN,
        authored_at="2026-07-27T12:01:00Z",
        reason="explicit-supersession",
    )
    payload = knowledge_index_to_payload(
        apply_governance_projection(knowledge, ledger)
    )
    edge = next(
        edge
        for edge in payload["extensions"]["llm-wiki/typed-graph-v1"]["edges"]
        if edge["kind"] == "supersedes"
    )
    edge["evidence"]["samples"][0]["reason"] = "tampered-reason"
    edge["evidence"]["samples"][0]["attributes"]["governance_hash"] = (
        "sha256:" + "f" * 64
    )
    tampered = parse_knowledge_index(payload)

    with pytest.raises(GovernanceError) as raised:
        validate_governance_projection(tampered, ledger=ledger)
    assert raised.value.code == "governance-projection-mismatch"


def test_json_schema_recognizes_the_reserved_governance_projection():
    knowledge, _, _ = _reviewable_knowledge()
    ledger = _review_ledger(knowledge)
    projected = apply_governance_projection(knowledge, ledger)
    payload = knowledge_index_to_payload(projected)
    validator = Draft202012Validator(load_knowledge_schema())

    assert list(validator.iter_errors(payload)) == []
    payload["extensions"][GOVERNANCE_EXTENSION_KEY]["concepts"][
        "llm-wiki://modules/sync_cmd"
    ]["uid"] = "not-a-uid"
    assert any(
        "does not match" in error.message
        for error in validator.iter_errors(payload)
    )
    assert (
        validator.schema["$defs"]["governanceConceptSummary"]["properties"][
            "aliases"
        ]["maxItems"]
        == governance.MAX_ALIASES_PER_CONCEPT
    )


def test_runtime_enforces_the_schema_alias_limit(monkeypatch):
    ledger = _two_concept_ledger()
    uid = next(iter(ledger.concepts))
    ledger = add_alias(
        ledger,
        uid,
        ALIAS_LOCATOR,
        "llm-wiki://modules/historical-one",
    )
    ledger = add_alias(
        ledger,
        uid,
        ALIAS_LOCATOR,
        "llm-wiki://modules/historical-two",
    )
    monkeypatch.setattr(governance, "MAX_ALIASES_PER_CONCEPT", 1)

    with pytest.raises(GovernanceError, match="alias limit"):
        validate_governance_ledger(ledger)


def test_load_rejects_duplicate_keys_noncanonical_bytes_and_bundle_mismatch(
    tmp_path: Path,
):
    path = tmp_path / GOVERNANCE_FILENAME
    duplicate = (
        b'{"schema_version":"llm-wiki-governance/v1",'
        b'"bundle_id":"kb_duplicate","concepts":{},'
        b'"aliases":{},"aliases":{},"lifecycle_events":{},'
        b'"review_events":{}}'
    )
    path.write_bytes(duplicate)
    with pytest.raises(GovernanceError, match="duplicate JSON key"):
        load_governance(tmp_path)

    ledger = GovernanceLedger.empty("kb_bundle-one")
    path.write_text(
        json.dumps(ledger.to_payload(), sort_keys=True),
        encoding="utf-8",
    )
    with pytest.raises(GovernanceError, match="canonical deterministic"):
        load_governance(tmp_path)

    path.write_bytes(ledger.to_bytes())
    with pytest.raises(GovernanceError, match="does not match expected bundle"):
        load_governance(tmp_path, expected_bundle_id="kb_bundle-two")


def test_load_rejects_excessively_nested_json_without_recursion_escape(
    tmp_path: Path,
):
    path = tmp_path / GOVERNANCE_FILENAME
    path.write_bytes(b"[" * 100_000 + b"0" + b"]" * 100_000)

    # Decoders that can parse this depth reject the root array during validation.
    with pytest.raises(GovernanceError, match="valid UTF-8 JSON|must be an object"):
        load_governance(tmp_path)


def test_load_wraps_json_decoder_recursion_error(tmp_path: Path, monkeypatch):
    (tmp_path / GOVERNANCE_FILENAME).write_bytes(b"{}")
    decoder_error = RecursionError("JSON nesting limit reached")

    def fail_decode(*args, **kwargs):
        raise decoder_error

    monkeypatch.setattr(governance.json, "loads", fail_decode)

    with pytest.raises(GovernanceError, match="valid UTF-8 JSON") as error:
        load_governance(tmp_path)

    assert error.value.__cause__ is decoder_error


def test_load_uses_the_ledger_byte_bound_before_json_parsing(
    tmp_path: Path,
    monkeypatch,
):
    monkeypatch.setattr(governance, "MAX_LEDGER_BYTES", 64)
    (tmp_path / GOVERNANCE_FILENAME).write_bytes(b"{" + b" " * 64)

    with pytest.raises(GovernanceError, match="byte limit"):
        load_governance(tmp_path)


def test_governance_lock_rejects_symlink_without_touching_target(
    tmp_path: Path,
):
    wiki_dir = tmp_path / "wiki"
    wiki_dir.mkdir()
    outside = tmp_path / "outside.txt"
    outside.write_bytes(b"do not change\n")
    (wiki_dir / GOVERNANCE_LOCK_FILENAME).symlink_to(outside)

    with pytest.raises(GovernanceError, match="symbolic-link"):
        with governance_lock(wiki_dir):
            raise AssertionError("unsafe lock unexpectedly acquired")

    assert outside.read_bytes() == b"do not change\n"


def test_oversize_save_preserves_the_prior_complete_ledger(
    tmp_path: Path,
    monkeypatch,
):
    initial = _two_concept_ledger()
    save_governance(tmp_path, initial, expected_hash=None)
    before = (tmp_path / GOVERNANCE_FILENAME).read_bytes()
    uid = next(iter(initial.concepts))
    updated = add_alias(
        initial,
        uid,
        ALIAS_LOCATOR,
        "llm-wiki://modules/a-longer-historical-coordinate",
    )
    limit = (len(initial.to_bytes()) + len(updated.to_bytes())) // 2
    monkeypatch.setattr(governance, "MAX_LEDGER_BYTES", limit)

    with pytest.raises(GovernanceError, match="byte limit"):
        save_governance(
            tmp_path,
            updated,
            expected_hash=initial.content_hash(),
        )

    assert (tmp_path / GOVERNANCE_FILENAME).read_bytes() == before


def test_compare_and_swap_conflict_never_silently_wins(tmp_path: Path):
    initial = _two_concept_ledger()
    save_governance(tmp_path, initial, expected_hash=None)
    observed = load_governance(tmp_path)
    uid = next(iter(initial.concepts))
    first = add_alias(
        initial,
        uid,
        ALIAS_LOCATOR,
        "llm-wiki://modules/historical",
    )
    save_governance(
        tmp_path,
        first,
        expected_hash=observed.content_hash,
    )
    winner = load_governance(tmp_path)

    with pytest.raises(GovernanceConflictError):
        save_governance(
            tmp_path,
            initial,
            expected_hash=observed.content_hash,
        )
    assert load_governance(tmp_path).content == winner.content


def test_failed_atomic_write_leaves_complete_prior_or_next_ledger(
    tmp_path: Path,
):
    initial = _two_concept_ledger()
    save_governance(tmp_path, initial, expected_hash=None)
    loaded = load_governance(tmp_path)
    uid = next(iter(initial.concepts))
    updated = add_alias(
        initial,
        uid,
        ALIAS_LOCATOR,
        "llm-wiki://modules/historical",
    )

    def fail_before_replace(stage: GovernanceWriteStage) -> None:
        if stage is GovernanceWriteStage.TEMP_DURABLE:
            raise RuntimeError("simulated interruption")

    with pytest.raises(RuntimeError, match="simulated interruption"):
        save_governance(
            tmp_path,
            updated,
            expected_hash=loaded.content_hash,
            fault_injector=fail_before_replace,
        )
    assert load_governance(tmp_path).ledger == initial
    assert not tuple(tmp_path.glob(f".{GOVERNANCE_FILENAME}.*.tmp"))

    def fail_after_replace(stage: GovernanceWriteStage) -> None:
        if stage is GovernanceWriteStage.REPLACED:
            raise RuntimeError("simulated interruption")

    with pytest.raises(RuntimeError, match="simulated interruption"):
        save_governance(
            tmp_path,
            updated,
            expected_hash=loaded.content_hash,
            fault_injector=fail_after_replace,
        )
    assert load_governance(tmp_path).ledger in (initial, updated)


def test_ledger_read_and_write_reject_symlinked_ancestor(tmp_path: Path):
    checkout = tmp_path / "checkout"
    checkout.mkdir()
    outside = tmp_path / "outside"
    wiki = outside / "wiki"
    wiki.mkdir(parents=True)
    linked_parent = checkout / "docs"
    try:
        linked_parent.symlink_to(outside, target_is_directory=True)
    except (NotImplementedError, OSError):
        pytest.skip("symbolic links are unavailable on this platform")
    escaped_wiki = linked_parent / "wiki"

    with pytest.raises(GovernanceError, match="component"):
        save_governance(
            escaped_wiki,
            GovernanceLedger.empty("kb_symlink-test"),
            expected_hash=None,
        )
    with pytest.raises(GovernanceError, match="component"):
        load_governance(escaped_wiki)
    assert not (wiki / GOVERNANCE_FILENAME).exists()


def test_ledger_rejects_credentials_absolute_paths_and_prose_fields():
    ledger = _two_concept_ledger()
    uid = next(iter(ledger.concepts))

    with pytest.raises(GovernanceError, match="credential"):
        set_lifecycle(
            ledger,
            uid,
            Lifecycle.ACTIVE,
            actor=GovernanceActor(kind="human", actor_id="api-key-owner"),
            authored_at=FIXED_TIME,
        )
    with pytest.raises(GovernanceError, match="machine reason"):
        set_lifecycle(
            ledger,
            uid,
            Lifecycle.ACTIVE,
            actor=HUMAN,
            authored_at=FIXED_TIME,
            reason="This is explanatory prose.",
        )
