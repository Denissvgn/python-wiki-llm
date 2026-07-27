"""Read-only machine-verification evaluation for native knowledge sessions.

Verification receipts are disposable evidence anchored to committed native
artifacts.  This module loads and evaluates a receipt without running any
checker, and returns the same coordinate-keyed summaries to every consumer.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import replace
from pathlib import Path
from types import MappingProxyType
from typing import Any

from .knowledge_consumption import (
    KnowledgeReadView,
    MachineVerificationAvailability,
    MachineVerificationReadView,
)
from .knowledge_evidence import hash_json
from .knowledge_governance import GOVERNANCE_EXTENSION_KEY
from .verification_contracts import (
    VerificationReceipt,
    VerificationResult,
    build_artifact_verification_context,
    evaluate_verification_receipt,
    load_verification_receipt,
)


def machine_verification_summaries(
    wiki_dir: str | Path,
    knowledge_view: KnowledgeReadView,
) -> Mapping[str, Mapping[str, Any]]:
    """Return the legacy coordinate-keyed adapter for API/query consumers."""

    if not isinstance(knowledge_view, KnowledgeReadView):
        # Preserve the long-standing adapter behavior for callers that supply
        # an unavailable/test-double view; strict typing remains enforced by
        # the new receipt attachment constructor below.
        return MappingProxyType({})
    attached = attach_machine_verification_read_view(wiki_dir, knowledge_view)
    return verification_summaries_for_concepts(attached)


def attach_machine_verification_read_view(
    wiki_dir: str | Path,
    knowledge_view: KnowledgeReadView,
) -> KnowledgeReadView:
    """Attach one fixed receipt evaluation to an operation-scoped read view."""

    if not isinstance(knowledge_view, KnowledgeReadView):
        raise TypeError("knowledge_view must be a KnowledgeReadView")
    if (
        knowledge_view.machine_verification.availability
        is not MachineVerificationAvailability.NOT_EVALUATED
    ):
        return knowledge_view
    return replace(
        knowledge_view,
        machine_verification=load_machine_verification_read_view(
            wiki_dir,
            knowledge_view,
        ),
    )


def load_machine_verification_read_view(
    wiki_dir: str | Path,
    knowledge_view: KnowledgeReadView,
) -> MachineVerificationReadView:
    """Load and evaluate one fixed receipt without executing a checker."""

    if not isinstance(knowledge_view, KnowledgeReadView):
        raise TypeError("knowledge_view must be a KnowledgeReadView")
    knowledge = knowledge_view.knowledge
    manifest = knowledge_view.manifest_basis
    if knowledge is None or manifest is None or manifest.artifact_hashes is None:
        return MachineVerificationReadView(
            availability=MachineVerificationAvailability.ABSENT,
            reason="verification-receipt-not-present",
        )

    try:
        receipt = load_verification_receipt(Path(wiki_dir))
    except (OSError, RecursionError, TypeError, UnicodeError, ValueError):
        return MachineVerificationReadView(
            availability=MachineVerificationAvailability.INVALID,
            reason="verification-receipt-invalid",
        )
    if receipt is None:
        return MachineVerificationReadView(
            availability=MachineVerificationAvailability.ABSENT,
            reason="verification-receipt-not-present",
        )

    hashes = manifest.artifact_hashes

    def context(scope_locator: str | None):
        return build_artifact_verification_context(
            knowledge,
            knowledge_hash=hashes.knowledge_index_hash,
            surface_index_hash=hashes.surface_index_hash,
            evaluated_envelope_hash=hashes.evaluated_envelope_hash,
            governance_hash=hashes.governance_hash,
            scope_locator=scope_locator,
        )

    bundle_context = context(None)
    selected_locator: str | None = None
    scope_known = receipt.scope_uid == bundle_context.scope_uid
    scope_kind = "bundle" if scope_known else "unknown"
    if not scope_known:
        for concept in knowledge.concepts:
            governance = concept.extensions.get(GOVERNANCE_EXTENSION_KEY)
            uid = governance.get("uid") if isinstance(governance, Mapping) else None
            expected_uid = (
                uid
                if isinstance(uid, str)
                else "locator:"
                + hash_json(concept.locator).removeprefix("sha256:")
            )
            if expected_uid == receipt.scope_uid:
                selected_locator = concept.locator
                scope_known = True
                scope_kind = "concept"
                break
    current_context = context(selected_locator) if scope_known else bundle_context
    evaluation = evaluate_verification_receipt(receipt, current_context)
    summary = machine_verification_summary(
        receipt,
        valid=evaluation.valid,
        reasons=[reason.value for reason in evaluation.reasons],
    )
    return MachineVerificationReadView(
        availability=MachineVerificationAvailability.RECORDED,
        reason=(
            "verification-receipt-valid"
            if evaluation.valid
            else "verification-receipt-invalidated"
        ),
        scope_kind=scope_kind,
        scope_uid=receipt.scope_uid,
        scope_locator=selected_locator,
        valid=evaluation.valid,
        invalidation_reasons=tuple(reason.value for reason in evaluation.reasons),
        recorded_result=receipt.result.value,
        passed=bool(summary["passed"]),
        checks=MappingProxyType(
            {
                checker_id: MappingProxyType(dict(check_summary))
                for checker_id, check_summary in sorted(
                    summary["checks"].items()
                )
            }
        ),
    )


def verification_summaries_for_concepts(
    knowledge_view: KnowledgeReadView,
    evaluated: MachineVerificationReadView | None = None,
) -> Mapping[str, Mapping[str, Any]]:
    """Adapt one receipt evaluation to the existing per-coordinate contract."""

    if not isinstance(knowledge_view, KnowledgeReadView):
        raise TypeError("knowledge_view must be a KnowledgeReadView")
    selected = (
        knowledge_view.machine_verification
        if evaluated is None
        else evaluated
    )
    if not isinstance(selected, MachineVerificationReadView):
        raise TypeError("evaluated must be a MachineVerificationReadView")
    knowledge = knowledge_view.knowledge
    if knowledge is None:
        return MappingProxyType({})
    concept_coordinates: dict[str, str] = {}
    for concept in knowledge.concepts:
        governance = concept.extensions.get(GOVERNANCE_EXTENSION_KEY)
        uid = governance.get("uid") if isinstance(governance, Mapping) else None
        concept_coordinates[concept.locator] = (
            uid if isinstance(uid, str) else concept.locator
        )

    if selected.availability in {
        MachineVerificationAvailability.NOT_EVALUATED,
        MachineVerificationAvailability.ABSENT,
    }:
        return MappingProxyType({})
    if selected.availability is MachineVerificationAvailability.INVALID:
        invalid = {
            "availability": "invalid",
            "reason": selected.reason,
        }
        return _frozen_summaries(
            {
                coordinate: dict(invalid)
                for coordinate in sorted(set(concept_coordinates.values()))
            }
        )

    summary: dict[str, Any] = {
        "availability": "recorded",
        "scope_uid": selected.scope_uid,
        "valid": selected.valid,
        "invalidation_reasons": list(selected.invalidation_reasons),
        "recorded_result": selected.recorded_result,
        "passed": selected.passed,
        "checks": {
            checker_id: _deep_copy(check)
            for checker_id, check in sorted(selected.checks.items())
        },
    }
    if selected.scope_kind == "concept":
        if selected.scope_locator in concept_coordinates:
            return _frozen_summaries(
                {concept_coordinates[selected.scope_locator]: summary}
            )
        return MappingProxyType({})
    if selected.scope_kind == "unknown":
        return MappingProxyType({})
    return _frozen_summaries(
        {
            coordinate: dict(summary)
            for coordinate in sorted(set(concept_coordinates.values()))
        }
    )


def machine_verification_summary(
    receipt: VerificationReceipt,
    *,
    valid: bool,
    reasons: list[str],
) -> dict[str, Any]:
    """Return a compact, bounded machine-only receipt summary."""

    return {
        "availability": "recorded",
        "scope_uid": receipt.scope_uid,
        "valid": valid,
        "invalidation_reasons": reasons,
        "recorded_result": receipt.result.value,
        "passed": valid and receipt.result is VerificationResult.PASSED,
        "checks": {
            check.checker_id: {
                "version": check.checker_version,
                "result": check.result.value,
                "diagnostics": [
                    diagnostic.to_payload() for diagnostic in check.diagnostics
                ],
                "diagnostic_coverage": check.diagnostic_coverage.to_payload(),
            }
            for check in receipt.checks
        },
    }


def _frozen_summaries(
    values: Mapping[str, Mapping[str, Any]],
) -> Mapping[str, Mapping[str, Any]]:
    return MappingProxyType(
        {
            coordinate: MappingProxyType(dict(values[coordinate]))
            for coordinate in sorted(values)
        }
    )


def _deep_copy(value: object) -> Any:
    if isinstance(value, Mapping):
        return {
            str(key): _deep_copy(item)
            for key, item in sorted(value.items(), key=lambda pair: str(pair[0]))
        }
    if isinstance(value, list):
        return [_deep_copy(item) for item in value]
    if isinstance(value, tuple):
        return [_deep_copy(item) for item in value]
    return value


__all__ = [
    "attach_machine_verification_read_view",
    "machine_verification_summaries",
    "machine_verification_summary",
    "load_machine_verification_read_view",
    "verification_summaries_for_concepts",
]
