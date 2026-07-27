"""Operation-scoped machine-verification read-view tests."""

from __future__ import annotations

from dataclasses import replace

import pytest

from llm_wiki_cli.services.knowledge_consumption import (
    KnowledgeReadView,
    MachineVerificationAvailability,
    MachineVerificationReadView,
    load_knowledge_read_view,
)
from llm_wiki_cli.services.knowledge_projection import (
    project_knowledge,
    serialize_knowledge_projection,
)
from llm_wiki_cli.services.knowledge_verification import (
    attach_machine_verification_read_view,
    load_machine_verification_read_view,
    verification_summaries_for_concepts,
)
from llm_wiki_cli.services.verification_contracts import (
    ARTIFACT_INTEGRITY_CHECKER_ID,
    VERIFICATION_RECEIPT_FILENAME,
    VerificationDiagnostic,
    build_artifact_verification_context,
    verify,
    verify_and_write_receipt,
    write_verification_receipt,
)
from tests.knowledge_fixtures import fixture_hash
from tests.test_knowledge_loader import _committed_m3_state


def _ready_view(tmp_path) -> KnowledgeReadView:
    _committed_m3_state(tmp_path)
    return load_knowledge_read_view(tmp_path, snapshot_only=True)


def _context(
    view: KnowledgeReadView,
    *,
    scope_locator: str | None = None,
    knowledge_hash: str | None = None,
    surface_index_hash: str | None = None,
    evaluated_envelope_hash: str | None = None,
    artifact_integrity: bool = True,
    artifact_diagnostics: tuple[VerificationDiagnostic, ...] = (),
):
    assert view.knowledge is not None
    assert view.manifest_basis is not None
    assert view.manifest_basis.artifact_hashes is not None
    hashes = view.manifest_basis.artifact_hashes
    return build_artifact_verification_context(
        view.knowledge,
        knowledge_hash=knowledge_hash or hashes.knowledge_index_hash,
        surface_index_hash=surface_index_hash or hashes.surface_index_hash,
        evaluated_envelope_hash=(
            evaluated_envelope_hash or hashes.evaluated_envelope_hash
        ),
        governance_hash=hashes.governance_hash,
        scope_locator=scope_locator,
        artifact_integrity=artifact_integrity,
        artifact_diagnostics=artifact_diagnostics,
    )


def test_bundle_passed_receipt_is_attached_once_and_shared(tmp_path):
    view = _ready_view(tmp_path)
    verify_and_write_receipt(
        tmp_path,
        _context(view),
        [ARTIFACT_INTEGRITY_CHECKER_ID],
    )

    attached = attach_machine_verification_read_view(tmp_path, view)
    same_operation = attach_machine_verification_read_view(tmp_path, attached)
    summaries = verification_summaries_for_concepts(attached)

    assert attached is not view
    assert same_operation is attached
    assert attached.machine_verification.availability is (
        MachineVerificationAvailability.RECORDED
    )
    assert attached.machine_verification.scope_kind == "bundle"
    assert attached.machine_verification.valid is True
    assert attached.machine_verification.recorded_result == "passed"
    assert attached.machine_verification.passed is True
    assert len(summaries) == len(attached.knowledge.concepts)
    assert {
        summary["recorded_result"] for summary in summaries.values()
    } == {"passed"}


def test_valid_failed_receipt_remains_separate_from_live_validity(tmp_path):
    view = _ready_view(tmp_path)
    diagnostic = VerificationDiagnostic(
        code="manifest-hash-mismatch",
        subject="artifact_hashes.knowledge_index_hash",
    )
    verify_and_write_receipt(
        tmp_path,
        _context(
            view,
            artifact_integrity=False,
            artifact_diagnostics=(diagnostic,),
        ),
        [ARTIFACT_INTEGRITY_CHECKER_ID],
    )

    evaluated = load_machine_verification_read_view(tmp_path, view)

    assert evaluated.availability is MachineVerificationAvailability.RECORDED
    assert evaluated.valid is True
    assert evaluated.recorded_result == "failed"
    assert evaluated.passed is False
    assert evaluated.checks[ARTIFACT_INTEGRITY_CHECKER_ID]["result"] == "failed"


def test_concept_receipt_is_exposed_only_for_its_exact_scope(tmp_path):
    view = _ready_view(tmp_path)
    assert view.knowledge is not None
    locator = view.knowledge.concepts[0].locator
    verify_and_write_receipt(
        tmp_path,
        _context(view, scope_locator=locator),
        [ARTIFACT_INTEGRITY_CHECKER_ID],
    )

    evaluated = load_machine_verification_read_view(tmp_path, view)
    summaries = verification_summaries_for_concepts(view, evaluated)

    assert evaluated.scope_kind == "concept"
    assert evaluated.scope_locator == locator
    assert evaluated.valid is True
    assert list(summaries) == [locator]


def test_invalidated_concept_receipt_remains_exactly_scoped(tmp_path):
    view = _ready_view(tmp_path)
    assert view.knowledge is not None
    locator = view.knowledge.concepts[0].locator
    verify_and_write_receipt(
        tmp_path,
        _context(
            view,
            scope_locator=locator,
            knowledge_hash=fixture_hash(
                "verification-view:old-concept-knowledge"
            ),
        ),
        [ARTIFACT_INTEGRITY_CHECKER_ID],
    )

    evaluated = load_machine_verification_read_view(tmp_path, view)
    summaries = verification_summaries_for_concepts(view, evaluated)

    assert evaluated.scope_kind == "concept"
    assert evaluated.valid is False
    assert list(summaries) == [locator]
    assert summaries[locator]["valid"] is False


def test_invalidated_receipt_preserves_evaluator_reason_order(tmp_path):
    view = _ready_view(tmp_path)
    verify_and_write_receipt(
        tmp_path,
        _context(
            view,
            knowledge_hash=fixture_hash("verification-view:old-knowledge"),
            surface_index_hash=fixture_hash("verification-view:old-surface"),
            evaluated_envelope_hash=fixture_hash(
                "verification-view:old-envelope"
            ),
        ),
        [ARTIFACT_INTEGRITY_CHECKER_ID],
    )

    evaluated = load_machine_verification_read_view(tmp_path, view)
    summaries = verification_summaries_for_concepts(view, evaluated)

    assert evaluated.valid is False
    assert evaluated.reason == "verification-receipt-invalidated"
    assert evaluated.invalidation_reasons == (
        "knowledge-changed",
        "scope-changed",
        "evidence-changed",
        "snapshot-changed",
    )
    assert evaluated.recorded_result == "passed"
    assert evaluated.passed is False
    assert {
        tuple(summary["invalidation_reasons"])
        for summary in summaries.values()
    } == {evaluated.invalidation_reasons}


def test_unknown_receipt_scope_is_not_broadcast_to_current_concepts(tmp_path):
    view = _ready_view(tmp_path)
    receipt = verify(
        _context(view),
        [ARTIFACT_INTEGRITY_CHECKER_ID],
    )
    receipt = replace(
        receipt,
        scope_uid="lw:deleted:0123456789abcdef0123456789abcdef",
    )
    write_verification_receipt(tmp_path, receipt)

    evaluated = load_machine_verification_read_view(tmp_path, view)
    summaries = verification_summaries_for_concepts(view, evaluated)

    assert evaluated.scope_kind == "unknown"
    assert evaluated.scope_locator is None
    assert evaluated.valid is False
    assert evaluated.invalidation_reasons == ("scope-changed",)
    assert dict(summaries) == {}


def test_malformed_receipt_uses_closed_reason_without_echoing_input(tmp_path):
    view = _ready_view(tmp_path)
    seeded_secret = "sk-proj-abcdefghijklmnopqrstuvwxyz123456"
    (tmp_path / VERIFICATION_RECEIPT_FILENAME).write_text(
        seeded_secret,
        encoding="utf-8",
    )

    attached = attach_machine_verification_read_view(tmp_path, view)
    projection = project_knowledge(attached)
    encoded = serialize_knowledge_projection(projection)

    assert attached.machine_verification == MachineVerificationReadView(
        availability=MachineVerificationAvailability.INVALID,
        reason="verification-receipt-invalid",
    )
    assert seeded_secret not in encoded
    assert "verification-receipt-invalid" in encoded


def test_public_projection_omits_arbitrary_strings_from_valid_receipt_view(
    tmp_path,
):
    view = _ready_view(tmp_path)
    verify_and_write_receipt(
        tmp_path,
        _context(view),
        [ARTIFACT_INTEGRITY_CHECKER_ID],
    )
    evaluated = load_machine_verification_read_view(tmp_path, view)
    seeded_secret = "sk-proj-abcdefghijklmnopqrstuvwxyz123456"
    adversarial_but_valid = replace(evaluated, scope_uid=seeded_secret)
    attached = replace(view, machine_verification=adversarial_but_valid)

    assert adversarial_but_valid.valid is True
    assert seeded_secret not in serialize_knowledge_projection(
        project_knowledge(attached)
    )


@pytest.mark.parametrize(
    "change",
    [
        lambda value, secret: replace(value, reason=secret),
        lambda value, secret: replace(
            value,
            valid=False,
            reason="verification-receipt-invalidated",
            invalidation_reasons=(secret,),
            passed=False,
        ),
        lambda value, secret: replace(value, recorded_result=secret),
        lambda value, secret: replace(
            value,
            checks={
                ARTIFACT_INTEGRITY_CHECKER_ID: {
                    **dict(value.checks[ARTIFACT_INTEGRITY_CHECKER_ID]),
                    "result": secret,
                }
            },
        ),
    ],
)
def test_receipt_attachment_rejects_open_ended_projection_values(
    tmp_path,
    change,
):
    view = _ready_view(tmp_path)
    verify_and_write_receipt(
        tmp_path,
        _context(view),
        [ARTIFACT_INTEGRITY_CHECKER_ID],
    )
    evaluated = load_machine_verification_read_view(tmp_path, view)
    seeded_secret = "sk-proj-abcdefghijklmnopqrstuvwxyz123456"

    with pytest.raises((TypeError, ValueError)):
        change(evaluated, seeded_secret)

    with pytest.raises(TypeError, match="MachineVerificationReadView"):
        replace(view, machine_verification={"reason": seeded_secret})
