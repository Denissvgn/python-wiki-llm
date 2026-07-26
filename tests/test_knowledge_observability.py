"""Aggregate, evidence-free knowledge observability contracts."""

from __future__ import annotations

import json
from dataclasses import replace

import pytest

from llm_wiki_cli.services import knowledge_consumption
from llm_wiki_cli.services.knowledge_artifacts import KNOWLEDGE_INDEX_FILENAME
from llm_wiki_cli.services.knowledge_consumption import build_knowledge_read_view
from llm_wiki_cli.services.knowledge_loader import load_knowledge_state
from llm_wiki_cli.services.knowledge_observability import (
    KnowledgeAggregateSummary,
    KnowledgePhaseDurations,
    knowledge_status_payload,
    load_snapshot_knowledge_observability,
    summarize_knowledge_view,
)
from tests.knowledge_fixtures import fail_if_extraction_runs
from tests.test_knowledge_freshness import _live_evaluation
from tests.test_knowledge_loader import _committed_state


def test_live_summary_contains_only_closed_aggregate_counts(tmp_path):
    _committed_state(tmp_path)
    loaded = load_knowledge_state(tmp_path)
    assert loaded.knowledge is not None
    view = build_knowledge_read_view(
        loaded,
        live_evaluation=_live_evaluation(loaded.knowledge),
    )

    summary = summarize_knowledge_view(
        view,
        durations=KnowledgePhaseDurations(
            load_ms=1,
            evaluate_ms=2,
            check_ms=3,
        ),
    )

    assert summary.to_payload() == {
        "availability": "ready",
        "reason": "all-projection-commitments-match",
        "concepts_evaluated": 6,
        "freshness_counts": {
            "basis-incompatible": 0,
            "current": 3,
            "nonsemantic-source-change": 0,
            "source-changed": 0,
            "source-missing": 0,
            "unknown": 3,
        },
        "evidence_issue_counts": {
            "invalid": 0,
            "missing": 0,
            "unknown": 1,
        },
        "degraded_reason": None,
        "phase_durations_ms": {
            "load": 1,
            "evaluate": 2,
            "check": 3,
        },
        "freshness_evaluated": True,
    }
    serialized = json.dumps(summary.to_payload(), sort_keys=True)
    assert "llm-wiki://" not in serialized
    assert "sha256:" not in serialized
    assert "example.invalid/acme/knowledge-fixture" not in serialized


def test_ready_summary_omits_private_repository_metadata(tmp_path):
    secret = "ssh://private.example/acme/internal.git"
    _committed_state(tmp_path)
    loaded = load_knowledge_state(tmp_path)
    assert loaded.knowledge is not None
    private_knowledge = replace(
        loaded.knowledge,
        bundle=replace(
            loaded.knowledge.bundle,
            repository=replace(
                loaded.knowledge.bundle.repository,
                extensions={
                    **loaded.knowledge.bundle.repository.extensions,
                    "example/private-remote": secret,
                },
            ),
        ),
    )
    private_loaded = replace(loaded, knowledge=private_knowledge)
    view = build_knowledge_read_view(
        private_loaded,
        live_evaluation=_live_evaluation(private_knowledge),
    )

    payload = summarize_knowledge_view(view).to_payload()

    assert secret not in json.dumps(payload, sort_keys=True)


def test_snapshot_summary_never_claims_live_freshness(
    tmp_path,
    monkeypatch,
):
    _committed_state(tmp_path)
    monkeypatch.setattr(
        knowledge_consumption,
        "evaluate_knowledge_freshness",
        fail_if_extraction_runs,
    )

    observed = load_snapshot_knowledge_observability(tmp_path)
    payload = observed.summary.to_payload()

    assert knowledge_status_payload(observed.view) == {
        "availability": "ready",
        "reason": "all-projection-commitments-match",
        "freshness_evaluated": False,
    }
    assert payload["concepts_evaluated"] == 0
    assert payload["freshness_counts"] is None
    assert payload["freshness_evaluated"] is False
    assert payload["phase_durations_ms"]["load"] >= 0
    assert payload["phase_durations_ms"]["evaluate"] is None
    assert payload["phase_durations_ms"]["check"] is None


def test_degraded_summary_does_not_expose_invalid_evidence(tmp_path):
    secret = "https://actor:password@private.example/internal"
    _committed_state(tmp_path)
    (tmp_path / KNOWLEDGE_INDEX_FILENAME).write_text(
        json.dumps({"secret": secret}),
        encoding="utf-8",
    )

    observed = load_snapshot_knowledge_observability(tmp_path)
    payload = observed.summary.to_payload()

    assert payload["availability"] == "degraded"
    assert payload["degraded_reason"] == (
        "policy-selected-surface-only-fallback-after-invalid"
    )
    assert payload["concepts_evaluated"] == 0
    assert payload["freshness_counts"] is None
    assert payload["evidence_issue_counts"] is None
    assert secret not in json.dumps(payload, sort_keys=True)


def test_legacy_snapshot_status_does_not_read_markdown(tmp_path):
    wiki = tmp_path / "wiki"
    (wiki / "entities").mkdir(parents=True)
    (wiki / "entities" / "User.md").write_bytes(b"\xff")

    observed = load_snapshot_knowledge_observability(wiki)

    assert knowledge_status_payload(observed.view) == {
        "availability": "absent",
        "reason": "knowledge-projection-not-present",
        "freshness_evaluated": False,
    }


@pytest.mark.parametrize(
    ("field_name", "value"),
    [
        ("load_ms", True),
        ("evaluate_ms", -1),
        ("check_ms", 1.5),
    ],
)
def test_phase_durations_reject_invalid_values(field_name, value):
    values = {"load_ms": None, "evaluate_ms": None, "check_ms": None}
    values[field_name] = value

    with pytest.raises(ValueError, match=field_name):
        KnowledgePhaseDurations(**values)


def test_aggregate_constructor_enforces_closed_privacy_contract():
    with pytest.raises(ValueError, match="reason"):
        KnowledgeAggregateSummary(
            availability="ready",
            reason="ssh://private.example/internal",
            concepts_evaluated=0,
            freshness_counts=None,
            evidence_issue_counts={
                "invalid": 0,
                "missing": 0,
                "unknown": 0,
            },
            degraded_reason=None,
            phase_durations_ms={
                "load": 0,
                "evaluate": None,
                "check": None,
            },
            freshness_evaluated=False,
        )


@pytest.mark.parametrize("value", [0, 1, "false", "true"])
def test_aggregate_constructor_requires_boolean_freshness_evaluated(value):
    with pytest.raises(TypeError, match="freshness_evaluated"):
        KnowledgeAggregateSummary(
            availability="ready",
            reason="all-projection-commitments-match",
            concepts_evaluated=0,
            freshness_counts=None,
            evidence_issue_counts={
                "invalid": 0,
                "missing": 0,
                "unknown": 0,
            },
            degraded_reason=None,
            phase_durations_ms={
                "load": 0,
                "evaluate": None,
                "check": None,
            },
            freshness_evaluated=value,
        )


def test_aggregate_summary_defensively_copies_count_mappings(tmp_path):
    _committed_state(tmp_path)
    loaded = load_knowledge_state(tmp_path)
    view = build_knowledge_read_view(loaded, snapshot_only=True)
    summary = summarize_knowledge_view(view)
    original = summary.to_payload()

    with pytest.raises(TypeError):
        summary.evidence_issue_counts["unknown"] = 999

    assert summary.to_payload() == original
