"""Concept-qualified authoring evidence and out-of-band runtime captures."""

from __future__ import annotations

import hashlib

import pytest

from llm_wiki_cli.services.documentation_claim_evidence import (
    CLAIM_EVIDENCE_SCHEMA_VERSION,
    RUNTIME_CAPTURE_SCHEMA_VERSION,
    DocumentationClaimEvidenceError,
    normalize_runtime_capture_records,
    qualify_claim_evidence,
    reconcile_claim_evidence_records,
    reconcile_runtime_capture_records,
)
from llm_wiki_cli.services.documentation_queries import (
    DocumentationGraphQueryService,
    DocumentationQueryError,
)
from llm_wiki_cli.services.documentation_run import (
    DocumentationAgentResult,
    DocumentationSchemaError,
)
from llm_wiki_cli.services.contracts import (
    DOCUMENTATION_AGENT_RESULT_SCHEMA_VERSION,
)
from tests.test_knowledge_queries import (
    MODULE_LOCATOR,
    USER_LOCATOR,
    _governed_view,
    _ready_view,
    _sectioned_view,
)
from tests.test_typed_graph_queries import _service as _typed_graph_service


def _graph_query(limit: int) -> dict[str, object]:
    return {
        "direction": "both",
        "kinds": [
            "contains",
            "imports",
            "calls",
            "entrypoint_for",
            "reads",
            "writes",
            "depends_on",
        ],
        "origins": ["extracted", "inferred", "markdown"],
        "resolutions": ["resolved", "ambiguous", "external", "unresolved"],
        "include_evidence": False,
        "limit": limit,
    }


def _capture_record(
    *,
    capture_path: str | None,
    capture_digest: str | None,
    state: str = "captured",
) -> dict[str, object]:
    return {
        "schema_version": RUNTIME_CAPTURE_SCHEMA_VERSION,
        "capture_id": "capture:usage-1",
        "capture_digest": capture_digest,
        "capture_path": capture_path,
        "command_or_flow_id": "cli:run-example",
        "result": {"state": state, "exit_code": None if state == "deferred" else 0},
        "concept_uid": None,
        "concept_locator": USER_LOCATOR,
        "section_locator": None,
        "native_observation": {
            "availability": "ready",
            "reason": "knowledge-ready",
            "structural_evidence_state": "present",
            "freshness_evaluated": False,
            "freshness_state": None,
            "freshness_reason": "freshness-not-evaluated",
        },
        "redaction": {"outcome": "redacted", "limitations": []},
        "environment": {"mode": "disposable", "limitations": []},
        "limitations": ["runtime-evidence-is-not-native-authority"],
    }


def _agent_result_payload(
    *,
    claim_evidence: list[dict[str, object]],
) -> dict[str, object]:
    return {
        "schema_version": DOCUMENTATION_AGENT_RESULT_SCHEMA_VERSION,
        "run_id": "run-claim-shape",
        "stage": "wiki-enrichment",
        "status": "complete",
        "changed_wiki_paths": [],
        "reused_work_ids": [],
        "completed_work_ids": [],
        "deferred_work_ids": [],
        "claims_evidence_pages": ["modules/accounts.md"],
        "claim_evidence": claim_evidence,
        "unresolved_unknowns": [],
        "unsupported_source_notices": [],
        "requested_follow_up_checks": [],
        "reported_source_writes": [],
        "reported_input_wiki_writes": [],
        "reported_generated_block_edits": [],
        "findings": [],
    }


def test_legacy_page_only_agent_result_remains_readable() -> None:
    result = DocumentationAgentResult.from_dict(
        {
            "schema_version": DOCUMENTATION_AGENT_RESULT_SCHEMA_VERSION,
            "run_id": "run-legacy",
            "stage": "user-docs",
            "status": "complete",
            "changed_wiki_paths": [],
            "reused_work_ids": [],
            "completed_work_ids": [],
            "deferred_work_ids": [],
            "claims_evidence_pages": ["guides/operator.md"],
            "unresolved_unknowns": [],
            "unsupported_source_notices": [],
            "requested_follow_up_checks": [],
            "reported_source_writes": [],
            "reported_input_wiki_writes": [],
            "reported_generated_block_edits": [],
            "findings": [],
        }
    )

    assert result.claim_evidence == ()
    assert result.runtime_captures == ()
    assert result.to_dict()["schema_version"] == (
        DOCUMENTATION_AGENT_RESULT_SCHEMA_VERSION
    )


def test_claim_evidence_reconciles_exact_current_identity_and_graph_bounds(
    tmp_path,
) -> None:
    service = _typed_graph_service(tmp_path, limit=1)

    record = qualify_claim_evidence(
        service,
        claim_id="work:module-impact",
        canonical_page="modules/accounts.md",
        concept_query=MODULE_LOCATOR,
        graph_query=_graph_query(1),
    )

    assert record["schema_version"] == CLAIM_EVIDENCE_SCHEMA_VERSION
    assert record["resolution"] == "exact"
    assert record["concept_locator"] == MODULE_LOCATOR
    assert record["freshness"]["evaluated"] is True
    assert record["bounds"]["matches"] == {
        "total": 1,
        "returned": 1,
        "truncated": False,
    }
    assert record["bounds"]["edges"]["returned"] <= 1
    assert record["bounds"]["edges"]["truncated"] is True
    assert reconcile_claim_evidence_records([record], service) == (record,)


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("kinds", ["calls-ish"], "unsupported typed relationship kind"),
        ("kinds", ["vendor//edge"], "unsupported typed relationship kind"),
        ("origins", ["runtime"], "unsupported origin"),
        ("resolutions", ["current"], "unsupported resolution"),
    ],
)
def test_agent_result_rejects_unsupported_graph_filters_during_normalization(
    tmp_path,
    field,
    value,
    message,
) -> None:
    service = _typed_graph_service(tmp_path)
    record = qualify_claim_evidence(
        service,
        claim_id="work:module-impact",
        canonical_page="modules/accounts.md",
        concept_query=MODULE_LOCATOR,
        graph_query=_graph_query(20),
    )
    record["graph_query"][field] = value

    with pytest.raises(DocumentationSchemaError, match=message):
        DocumentationAgentResult.from_dict(
            _agent_result_payload(claim_evidence=[record])
        )


def test_agent_result_accepts_qualified_extension_graph_kind(tmp_path) -> None:
    service = _typed_graph_service(tmp_path)
    record = qualify_claim_evidence(
        service,
        claim_id="work:module-impact",
        canonical_page="modules/accounts.md",
        concept_query=MODULE_LOCATOR,
        graph_query=_graph_query(20),
    )
    record["graph_query"]["kinds"].append("vendor.plugin/relationship")

    normalized = DocumentationAgentResult.from_dict(
        _agent_result_payload(claim_evidence=[record])
    )

    assert "vendor.plugin/relationship" in (
        normalized.claim_evidence[0]["graph_query"]["kinds"]
    )


def test_qualification_wraps_native_query_errors() -> None:
    class FailingService:
        limit = 20

        @staticmethod
        def get_concept(_query):
            raise DocumentationQueryError("injected invalid query")

    with pytest.raises(
        DocumentationClaimEvidenceError,
        match="native concept query failed",
    ):
        qualify_claim_evidence(
            FailingService(),
            claim_id="claim:query-error",
            canonical_page="modules/accounts.md",
            concept_query=MODULE_LOCATOR,
        )


def test_claim_section_beyond_bound_stays_unknown_instead_of_missing(
    tmp_path,
) -> None:
    view, observed = _sectioned_view(tmp_path)
    service = DocumentationGraphQueryService({}, knowledge_view=view, limit=1)
    requested = observed.sections[-1].locator

    record = qualify_claim_evidence(
        service,
        claim_id="finding:late-section",
        canonical_page="entities/User.md",
        concept_query=USER_LOCATOR,
        section_locator=requested,
    )

    assert record["section_locator"] == requested
    assert record["bounds"]["sections"]["truncated"] is True
    assert record["lifecycle_review"]["section_review"] == {
        "state": "bounded-not-returned",
        "reasons": ["section-query-truncated"],
        "ownership": None,
    }


def test_claim_can_use_durable_uid_and_rejects_worker_tampering(tmp_path) -> None:
    view, user_uid, _successor_uid = _governed_view(tmp_path)
    service = DocumentationGraphQueryService({}, knowledge_view=view)
    record = qualify_claim_evidence(
        service,
        claim_id="claim:renamed-user",
        canonical_page="entities/User.md",
        concept_query=user_uid,
    )

    assert record["resolution"] == "exact"
    assert record["concept_uid"] == user_uid
    forged = {**record, "concept_locator": "llm-wiki://entities/Forged"}
    with pytest.raises(
        DocumentationClaimEvidenceError,
        match="current committed native view",
    ):
        reconcile_claim_evidence_records([forged], service)


def test_claim_preserves_expired_section_review_without_private_parsing() -> None:
    section_locator = "llm-wiki://entities/User#section/description/1"

    class QueryService:
        limit = 20

        @staticmethod
        def get_concept(query):
            return {
                "query": query,
                "found": True,
                "ambiguous": False,
                "knowledge": {
                    "availability": "ready",
                    "reason": "all-projection-commitments-match",
                    "freshness_evaluated": True,
                },
                "concept": {
                    "uid": "uid_user",
                    "locator": USER_LOCATOR,
                    "canonical_path": "entities/User.md",
                    "evidence": "present",
                    "freshness": {
                        "state": "current",
                        "reason": "source-content-current",
                    },
                    "lifecycle": "active",
                },
                "bounds": {
                    "matches": {
                        "total": 1,
                        "returned": 1,
                        "truncated": False,
                    }
                },
            }

        @staticmethod
        def list_concept_sections(_query):
            return {
                "sections": [
                    {
                        "locator": section_locator,
                        "ownership": "semantic",
                        "review": {
                            "state": "expired",
                            "reasons": ["scope-changed"],
                        },
                    }
                ],
                "bounds": {
                    "sections": {
                        "total": 1,
                        "returned": 1,
                        "truncated": False,
                    }
                },
            }

    record = qualify_claim_evidence(
        QueryService(),
        claim_id="finding:expired-review",
        canonical_page="entities/User.md",
        concept_query="uid_user",
        section_locator=section_locator,
    )

    assert record["lifecycle_review"] == {
        "lifecycle": "active",
        "section_review": {
            "state": "expired",
            "reasons": ["scope-changed"],
            "ownership": "semantic",
        },
    }


def test_claim_preserves_missing_concept_in_a_ready_view(tmp_path) -> None:
    service = DocumentationGraphQueryService(
        {},
        knowledge_view=_ready_view(tmp_path),
    )

    record = qualify_claim_evidence(
        service,
        claim_id="claim:missing-concept",
        canonical_page="entities/User.md",
        concept_query="llm-wiki://entities/Missing",
    )

    assert record["resolution"] == "missing"
    assert record["concept_uid"] is None
    assert record["concept_locator"] is None


def test_claim_preserves_unsupported_native_state() -> None:
    service = DocumentationGraphQueryService({})

    record = qualify_claim_evidence(
        service,
        claim_id="claim:native-unavailable",
        canonical_page="entities/User.md",
        concept_query=USER_LOCATOR,
    )

    assert record["resolution"] == "native-unavailable"
    assert record["concept_uid"] is None
    assert record["concept_locator"] is None
    assert record["freshness"]["evaluated"] is False
    assert record["structural_evidence"]["state"] is None


def test_runtime_capture_verifies_redacted_bytes_and_reconciles_identity(
    tmp_path,
) -> None:
    capture = tmp_path / "assets" / "guides" / "run.txt"
    capture.parent.mkdir(parents=True)
    capture.write_text("redacted runtime output\n", encoding="utf-8")
    digest = "sha256:" + hashlib.sha256(capture.read_bytes()).hexdigest()
    record = _capture_record(
        capture_path="assets/guides/run.txt",
        capture_digest=digest,
    )
    service = DocumentationGraphQueryService(
        {},
        knowledge_view=_ready_view(tmp_path / "knowledge"),
    )

    reconciled = reconcile_runtime_capture_records(
        [record],
        wiki_root=tmp_path,
        service=service,
    )

    assert reconciled[0]["capture_digest"] == digest
    assert reconciled[0]["reconciliation"] == {
        "resolution": "exact",
        "uid": None,
        "locator": USER_LOCATOR,
        "section_state": "not-requested",
    }


def test_runtime_capture_reconciles_uid_with_a_governed_rename_alias(
    tmp_path,
) -> None:
    capture = tmp_path / "assets" / "guides" / "run.txt"
    capture.parent.mkdir(parents=True)
    capture.write_text("redacted runtime output\n", encoding="utf-8")
    governed, user_uid, _successor_uid = _governed_view(tmp_path / "knowledge")
    service = DocumentationGraphQueryService({}, knowledge_view=governed)
    record = _capture_record(
        capture_path="assets/guides/run.txt",
        capture_digest=(
            "sha256:" + hashlib.sha256(capture.read_bytes()).hexdigest()
        ),
    )
    record["concept_uid"] = user_uid
    record["concept_locator"] = "llm-wiki://entities/LegacyUser"

    reconciled = reconcile_runtime_capture_records(
        [record],
        wiki_root=tmp_path,
        service=service,
    )

    assert reconciled[0]["reconciliation"] == {
        "resolution": "exact",
        "uid": user_uid,
        "locator": USER_LOCATOR,
        "section_state": "not-requested",
    }

    record["concept_locator"] = "llm-wiki://entities/AccountService"
    with pytest.raises(
        DocumentationClaimEvidenceError,
        match="do not resolve to the same",
    ):
        reconcile_runtime_capture_records(
            [record],
            wiki_root=tmp_path,
            service=service,
        )


def test_runtime_capture_deferral_and_secret_rejection_are_explicit() -> None:
    deferred = _capture_record(
        capture_path=None,
        capture_digest=None,
        state="deferred",
    )
    deferred["native_observation"] = {
        "availability": "absent",
        "reason": "knowledge-not-present",
        "structural_evidence_state": None,
        "freshness_evaluated": False,
        "freshness_state": None,
        "freshness_reason": "freshness-not-evaluated",
    }
    deferred["environment"] = {
        "mode": "unavailable",
        "limitations": ["runtime-capability-missing"],
    }
    assert normalize_runtime_capture_records([deferred])[0]["result"]["state"] == (
        "deferred"
    )

    hostile = _capture_record(
        capture_path="assets/guides/run.txt",
        capture_digest="sha256:" + ("0" * 64),
    )
    hostile["limitations"] = ["password=hunter2"]
    with pytest.raises(
        DocumentationClaimEvidenceError,
        match="credential-like",
    ):
        normalize_runtime_capture_records([hostile])

    outside_assets = _capture_record(
        capture_path="guides/run.txt",
        capture_digest="sha256:" + ("0" * 64),
    )
    with pytest.raises(
        DocumentationClaimEvidenceError,
        match="under assets",
    ):
        normalize_runtime_capture_records([outside_assets])

    missing_exit = _capture_record(
        capture_path="assets/guides/run.txt",
        capture_digest="sha256:" + ("0" * 64),
    )
    missing_exit["result"] = {"state": "captured", "exit_code": None}
    with pytest.raises(
        DocumentationClaimEvidenceError,
        match="exit_code must be an integer",
    ):
        normalize_runtime_capture_records([missing_exit])

    unreviewed_binary = _capture_record(
        capture_path="assets/guides/run.png",
        capture_digest="sha256:" + ("0" * 64),
    )
    with pytest.raises(
        DocumentationClaimEvidenceError,
        match="binary media must retain limitation",
    ):
        normalize_runtime_capture_records([unreviewed_binary])
    unreviewed_binary["limitations"] += [
        "binary-media-content-not-machine-inspected",
        "canonical-body-media-review-required",
    ]
    assert normalize_runtime_capture_records([unreviewed_binary])[0][
        "capture_path"
    ] == "assets/guides/run.png"


def test_runtime_capture_rejects_secret_bearing_persisted_text(tmp_path) -> None:
    capture = tmp_path / "assets" / "guides" / "run" / "output.txt"
    capture.parent.mkdir(parents=True)
    capture.write_text(
        "API_KEY=sk-proj-abcdefghijklmnopqrstuvwxyz\n",
        encoding="utf-8",
    )
    record = _capture_record(
        capture_path="assets/guides/run/output.txt",
        capture_digest="sha256:" + hashlib.sha256(capture.read_bytes()).hexdigest(),
    )

    with pytest.raises(
        DocumentationClaimEvidenceError,
        match="credential-like content",
    ):
        reconcile_runtime_capture_records(
            [record],
            wiki_root=tmp_path,
            service=None,
        )
