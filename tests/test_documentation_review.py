"""Focused tests for the standalone-documentation review ledger."""

from __future__ import annotations

import json
from dataclasses import dataclass

import pytest

from llm_wiki_cli.services.documentation_review import (
    DOCUMENTATION_REVIEW_LEDGER_SCHEMA_VERSION,
    DocumentationReviewError,
    DocumentationReviewLedger,
    DocumentationReviewPacket,
    apply_review_loop,
    create_review_ledger,
    normalize_review_findings,
    normalize_review_records,
    reconcile_review_ledger,
)


def _packet(role: str, iteration: int, *, actor: str = "agent-a"):
    return DocumentationReviewPacket(
        packet_id=f"{role}-{iteration}",
        role=role,
        actor_id=actor,
        iteration=iteration,
        packet_hash=f"sha256:{role}-packet-{iteration}",
        result_hash=f"sha256:{role}-result-{iteration}",
        recorded_at=f"2026-07-18T00:0{iteration}:00Z",
        evidence=(f".llm-wiki-docs/{role}-{iteration}.json",),
    )


def _loop(ledger, records, iteration, *, actor="agent-a"):
    return apply_review_loop(
        ledger,
        records,
        observed_at=f"2026-07-18T00:0{iteration}:00Z",
        worker_packet=_packet("worker", iteration, actor=actor),
        reviewer_packet=_packet("reviewer", iteration, actor=actor),
    )


def test_normalizes_all_sources_and_ids_ignore_wording_and_path_order():
    records = {
        "lint": {
            "issues": [{"category": "broken_links", "path": "guides/start.md"}],
            "diagnostics": [
                {"category": "dependency_cycles", "path": "dependencies.md"}
            ],
        },
        "ci_check": ({"category": "strict", "path": "index.md"} for _ in range(1)),
        "site": [{"category": "published_placeholder", "path": "index.md"}],
        "built_site": [
            {"category": "missing_built_html_target", "path": "_site/index.html"}
        ],
        "media": [{"category": "media_orphan", "path": "assets/unused.png"}],
        "agent_review": [
            {
                "id": "DOC-7",
                "category": "claim mismatch",
                "paths": ["guides/b.md", ".\\guides\\a.md"],
                "target": "claim:auth",
                "message": "First wording",
                "severity": "critical",
            }
        ],
    }
    normalized = normalize_review_findings(records, observed_at="loop-1")

    assert {finding.source for finding in normalized} == {
        "lint",
        "ci-check",
        "site",
        "built-site",
        "media",
        "agent-review",
    }
    agent = next(finding for finding in normalized if finding.source == "agent-review")
    changed = normalize_review_records(
        "agent-review",
        [
            {
                "id": "DOC-99",
                "category": "claim mismatch",
                "paths": ["guides/a.md", "guides/b.md"],
                "target": "claim:auth",
                "message": "Completely different wording",
                "severity": "warning",
            }
        ],
        observed_at="loop-2",
    )[0]

    assert agent.finding_id == changed.finding_id
    assert agent.paths == ("guides/a.md", "guides/b.md")
    assert agent.severity == "high"
    assert changed.severity == "medium"
    assert agent.external_ids == ("DOC-7",)
    assert (
        next(
            finding for finding in normalized if finding.category == "dependency_cycles"
        ).severity
        == "medium"
    )
    assert normalized == tuple(sorted(normalized, key=lambda item: item.finding_id))


@pytest.mark.parametrize("status", ["resolved", "deferred", "superseded"])
def test_terminal_status_requires_explicit_rationale(status):
    with pytest.raises(DocumentationReviewError, match="requires a rationale"):
        normalize_review_records(
            "lint",
            [
                {
                    "category": "broken_links",
                    "path": "index.md",
                    "status": status,
                    "message": "A message is not a terminal disposition.",
                }
            ],
            observed_at="loop-1",
        )


def test_merge_never_drops_absent_findings_and_preserves_terminal_evidence():
    ledger = create_review_ledger("run-1", max_loops=5)
    first = _loop(
        ledger,
        {
            "lint": [
                {
                    "category": "broken_links",
                    "paths": ["guides/b.md", "guides/a.md"],
                    "severity": "error",
                    "evidence": "lint-1.json",
                    "message": "Broken links were found.",
                },
                {
                    "category": "media_orphan",
                    "path": "assets/unused.png",
                    "severity": "warning",
                    "evidence": "media-1.json",
                },
            ]
        },
        1,
    )
    assert first.decision.action == "return_to_worker"
    assert len(first.ledger.findings) == 2

    second = _loop(
        first.ledger,
        {
            "lint": [
                {
                    "category": "broken_links",
                    "paths": ["guides/a.md", "guides/b.md"],
                    "severity": "high",
                    "evidence": "lint-2.json",
                    "message": "Reworded but still broken.",
                }
            ]
        },
        2,
    )
    by_category = {finding.category: finding for finding in second.ledger.findings}
    assert by_category["broken_links"].occurrence_count == 2
    assert {"lint-1.json", "lint-2.json"} <= set(by_category["broken_links"].evidence)
    # An omitted record is not silently treated as fixed.
    assert by_category["media_orphan"].status == "open"
    assert by_category["media_orphan"].occurrence_count == 1

    third = _loop(
        second.ledger,
        {
            "lint": [
                {
                    "category": "media_orphan",
                    "path": "assets/unused.png",
                    "status": "resolved",
                    "rationale": "The unused asset was removed from the workspace.",
                    "evidence": "media-3.json",
                }
            ]
        },
        3,
    )
    by_category = {finding.category: finding for finding in third.ledger.findings}
    assert by_category["broken_links"].status == "open"
    assert by_category["broken_links"].occurrence_count == 2
    assert by_category["media_orphan"].status == "resolved"
    assert by_category["media_orphan"].occurrence_count == 2
    assert "removed from the workspace" in by_category["media_orphan"].rationale


def test_same_high_severity_finding_blocks_on_third_occurrence():
    ledger = create_review_ledger("run-high", max_loops=5)
    finding = {
        "category": "unsafe_generated_edit",
        "path": "modules/core.md",
        "severity": "error",
    }
    for iteration in (1, 2, 3):
        result = _loop(ledger, {"agent-review": [finding]}, iteration)
        ledger = result.ledger

    assert ledger.state == "blocked"
    assert result.decision.blocked is True
    assert result.decision.can_continue is False
    assert result.decision.action == "block"
    assert result.decision.finding_ids == (ledger.findings[0].finding_id,)
    assert ledger.findings[0].occurrence_count == 3


@pytest.mark.parametrize("status", ["deferred", "superseded"])
def test_high_severity_nonresolution_dispositions_remain_blocking(status):
    result = _loop(
        create_review_ledger(f"run-high-{status}", max_loops=3),
        {
            "agent-review": [
                {
                    "category": "unsafe_generated_edit",
                    "path": "modules/core.md",
                    "severity": "high",
                    "status": status,
                    "rationale": "The reviewer cannot prove an affirmative fix.",
                    "evidence": "review.json",
                }
            ]
        },
        1,
    )

    assert result.ledger.state == "adjustment_required"
    assert result.decision.action == "return_to_worker"
    assert result.ledger.unresolved_findings == result.ledger.findings
    with pytest.raises(DocumentationReviewError, match="no unresolved findings"):
        reconcile_review_ledger(
            result.ledger,
            supervisor_packet=_packet("supervisor", 1, actor="supervisor-b"),
            approved=True,
            rationale="The disposition is not an affirmative resolution.",
            evidence=("verification.json",),
            reconciled_at="2026-07-18T00:02:00Z",
        )


def test_configured_loop_limit_blocks_remaining_findings():
    ledger = create_review_ledger("run-limit", max_loops=2)
    finding = {
        "category": "missing_user_guides",
        "path": "guides",
        "severity": "warning",
    }
    first = _loop(ledger, {"site": [finding]}, 1)
    second = _loop(first.ledger, {"site": [finding]}, 2)

    assert first.decision.can_continue is True
    assert second.ledger.loop_count == 2
    assert second.ledger.state == "blocked"
    assert second.decision.rationale.startswith("Unresolved findings remain")


def test_worker_and_reviewer_packets_are_separate_even_for_same_actor():
    result = _loop(create_review_ledger("run-packets"), {}, 1, actor="same-agent")
    payload = result.ledger.to_dict()

    assert result.ledger.state == "awaiting_supervisor"
    assert payload["packets"]["worker"][0]["role"] == "worker"
    assert payload["packets"]["reviewer"][0]["role"] == "reviewer"
    assert payload["packets"]["worker"][0]["actor_id"] == "same-agent"
    assert payload["packets"]["reviewer"][0]["actor_id"] == "same-agent"
    assert (
        payload["packets"]["worker"][0]["packet_id"]
        != payload["packets"]["reviewer"][0]["packet_id"]
    )


def test_new_deterministic_finding_reopens_clean_ledger_before_supervisor():
    clean = _loop(create_review_ledger("run-late-check", max_loops=3), {}, 1)

    checked = _loop(
        clean.ledger,
        {
            "site": [
                {
                    "category": "broken_link",
                    "path": "site/guides/start.md",
                    "target": "missing.html",
                }
            ]
        },
        2,
        actor="deterministic-checker",
    )

    assert clean.ledger.state == "awaiting_supervisor"
    assert checked.ledger.state == "adjustment_required"
    assert checked.ledger.loop_count == 2
    assert checked.decision.action == "return_to_worker"


def test_publish_ready_requires_independent_supervisor_reconciliation():
    result = _loop(create_review_ledger("run-clean"), {}, 1, actor="author-reviewer")

    with pytest.raises(DocumentationReviewError, match="must be independent"):
        reconcile_review_ledger(
            result.ledger,
            supervisor_packet=_packet("supervisor", 1, actor="author-reviewer"),
            approved=True,
            rationale="Looks clean.",
            evidence=("verification.json",),
            reconciled_at="2026-07-18T00:02:00Z",
        )

    approved = reconcile_review_ledger(
        result.ledger,
        supervisor_packet=_packet("supervisor", 1, actor="supervisor-b"),
        approved=True,
        rationale="Deterministic checks and packet hashes reconcile.",
        evidence=("verification.json", "workspace-diff.json"),
        reconciled_at="2026-07-18T00:02:00Z",
    )

    assert approved.publish_ready is True
    assert approved.state == "publish_ready"
    assert approved.supervisor_reconciliations[0].approved is True


def test_ledger_contract_is_deterministic_and_round_trips_json():
    @dataclass
    class ToolFinding:
        category: str
        message: str
        path: str
        severity: str = "warning"

    result = _loop(
        create_review_ledger("run-json"),
        {
            "ci-check": [
                ToolFinding("dependency_cycles", "Cycle found", "dependencies.md")
            ]
        },
        1,
    )
    payload = result.ledger.to_dict()
    restored = DocumentationReviewLedger.from_dict(
        json.loads(json.dumps(payload, sort_keys=True))
    )

    assert payload["schema_version"] == DOCUMENTATION_REVIEW_LEDGER_SCHEMA_VERSION
    assert restored.to_dict() == payload
    assert restored.to_json() == result.ledger.to_json()


def _persisted_ledger_with_finding() -> dict:
    result = _loop(
        create_review_ledger("run-tamper", max_loops=3),
        {
            "lint": [
                {
                    "category": "broken_links",
                    "path": "guides/start.md",
                    "evidence": "lint.json",
                }
            ]
        },
        1,
    )
    return result.ledger.to_dict()


def _persisted_approved_ledger() -> dict:
    reviewed = _loop(create_review_ledger("run-approved"), {}, 1)
    approved = reconcile_review_ledger(
        reviewed.ledger,
        supervisor_packet=_packet("supervisor", 1, actor="supervisor-b"),
        approved=True,
        rationale="The clean ledger and packet hashes reconcile.",
        evidence=("verification.json",),
        reconciled_at="2026-07-18T00:02:00Z",
    )
    return approved.to_dict()


@pytest.mark.parametrize(
    "mutate",
    [
        lambda payload: payload.__setitem__("unexpected", True),
        lambda payload: payload["findings"][0].__setitem__("message", "hidden"),
        lambda payload: payload["packets"].__setitem__("supervisor", []),
        lambda payload: payload["packets"]["worker"][0].__setitem__(
            "provider_id", "hidden"
        ),
    ],
)
def test_persisted_ledger_rejects_unknown_fields_at_every_nested_boundary(mutate):
    payload = _persisted_ledger_with_finding()
    mutate(payload)

    with pytest.raises(DocumentationReviewError, match="unsupported fields"):
        DocumentationReviewLedger.from_dict(payload)


def test_persisted_reconciliation_rejects_unknown_fields():
    payload = _persisted_approved_ledger()
    payload["supervisor_reconciliations"][0]["hidden"] = "value"

    with pytest.raises(DocumentationReviewError, match="unsupported fields"):
        DocumentationReviewLedger.from_dict(payload)


@pytest.mark.parametrize(
    "mutate",
    [
        lambda payload: payload["findings"][0].pop("category"),
        lambda payload: payload["packets"].pop("reviewer"),
        lambda payload: payload["packets"]["worker"][0].pop("result_hash"),
    ],
)
def test_persisted_ledger_rejects_missing_nested_fields(mutate):
    payload = _persisted_ledger_with_finding()
    mutate(payload)

    with pytest.raises(DocumentationReviewError, match="missing required fields"):
        DocumentationReviewLedger.from_dict(payload)


def test_persisted_reconciliation_rejects_missing_fields():
    payload = _persisted_approved_ledger()
    payload["supervisor_reconciliations"][0].pop("reviewed_finding_ids")

    with pytest.raises(DocumentationReviewError, match="missing required fields"):
        DocumentationReviewLedger.from_dict(payload)


@pytest.mark.parametrize(
    "mutate",
    [
        lambda payload: payload.pop("publish_ready"),
        lambda payload: payload.__setitem__("publish_ready", True),
        lambda payload: payload.__setitem__("publish_ready", "false"),
    ],
)
def test_persisted_ledger_rejects_missing_or_forged_publish_ready(mutate):
    payload = _persisted_ledger_with_finding()
    mutate(payload)

    with pytest.raises(DocumentationReviewError):
        DocumentationReviewLedger.from_dict(payload)


def test_persisted_ledger_rejects_state_forged_away_from_approved_reconciliation():
    payload = _persisted_approved_ledger()
    payload["state"] = "awaiting_supervisor"
    payload["publish_ready"] = False

    with pytest.raises(DocumentationReviewError, match="requires publish_ready"):
        DocumentationReviewLedger.from_dict(payload)


@pytest.mark.parametrize(
    "mutate",
    [
        lambda payload: payload.__setitem__("findings", {}),
        lambda payload: payload["findings"][0].__setitem__("paths", "index.md"),
        lambda payload: payload["findings"][0].__setitem__("occurrence_count", "1"),
        lambda payload: payload["packets"]["worker"][0].__setitem__("evidence", [7]),
    ],
)
def test_persisted_ledger_rejects_malformed_required_nested_types(mutate):
    payload = _persisted_ledger_with_finding()
    mutate(payload)

    with pytest.raises(DocumentationReviewError):
        DocumentationReviewLedger.from_dict(payload)


def test_persisted_terminal_finding_requires_evidence_as_well_as_rationale():
    payload = _persisted_ledger_with_finding()
    finding = payload["findings"][0]
    finding["status"] = "resolved"
    finding["rationale"] = "The broken link was corrected and rechecked."
    finding["evidence"] = []
    payload["state"] = "awaiting_supervisor"

    with pytest.raises(DocumentationReviewError, match="explicit evidence"):
        DocumentationReviewLedger.from_dict(payload)


def test_normalized_terminal_finding_requires_explicit_not_inferred_evidence():
    with pytest.raises(DocumentationReviewError, match="explicit evidence"):
        normalize_review_records(
            "lint",
            [
                {
                    "category": "broken_links",
                    "path": "index.md",
                    "status": "resolved",
                    "rationale": "The broken link was corrected.",
                }
            ],
            observed_at="loop-1",
        )
