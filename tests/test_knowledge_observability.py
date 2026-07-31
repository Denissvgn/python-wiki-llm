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
    BASIS_INCOMPATIBLE_HINTS,
    BASIS_INCOMPATIBLE_REASON_CODES,
    KnowledgeAggregateSummary,
    KnowledgePhaseDurations,
    knowledge_freshness_disclosure,
    knowledge_freshness_hint,
    knowledge_status_payload,
    load_snapshot_knowledge_observability,
    summarize_knowledge_view,
)
from llm_wiki_cli.services.knowledge_model import ComputedFreshness
from tests.knowledge_fixtures import fail_if_extraction_runs
from tests.test_knowledge_freshness import _live_evaluation
from tests.test_knowledge_loader import _committed_state


_EXPECTED_BASIS_INCOMPATIBLE_HINTS = {
    "extractor-configuration-changed": (
        "Restore the extractor configuration used at sync, or re-run sync with "
        "the current extractor configuration."
    ),
    "extractor-configuration-unknown": (
        "Make the extractor configuration basis available and explicit, then "
        "re-run sync."
    ),
    "extractor-limitations-changed": (
        "Use an extractor with the limitations recorded at sync, or re-run sync "
        "after accepting the changed limitations."
    ),
    "extractor-selection-changed": (
        "Use the extractor selected at sync for this concept, or re-run sync after "
        "the intentional extractor change."
    ),
    "extractor-version-changed": (
        "Use the extractor version recorded at sync, or re-run sync with the "
        "installed extractor version."
    ),
    "generation-options-changed": (
        "Re-run with the generation options used at sync where supported (check "
        "--include-tests), or re-run sync with the intended current options."
    ),
    "identical-source-observation-mismatch": (
        "Producer nondeterminism or artifact corruption is possible—re-run sync; "
        "if it persists, file a defect."
    ),
    "knowledge-schema-version-changed": (
        "Use the knowledge schema version recorded at sync, or re-run sync with "
        "the current llm-wiki version."
    ),
    "live-extractor-unavailable": (
        "Install or enable the extractor recorded for this concept, or re-run sync "
        "with an available extractor."
    ),
    "observation-scope-changed": (
        "Restore the module, entity, or infrastructure observation scope used at "
        "sync, or re-run sync after an intentional scope change."
    ),
    "plugin-configuration-changed": (
        "Restore the plugin configuration used at sync, or re-run sync with the "
        "current plugin configuration."
    ),
    "plugin-configuration-unknown": (
        "Make every contributing plugin configuration basis available and "
        "explicit, then re-run sync."
    ),
    "plugin-limitations-changed": (
        "Restore the contributing plugin limitations recorded at sync, or re-run "
        "sync after accepting the change."
    ),
    "plugin-set-changed": (
        "Enable the plugin set used at sync, or re-run sync with the currently "
        "enabled plugin set."
    ),
    "plugin-version-changed": (
        "Use the contributing plugin versions recorded at sync, or re-run sync "
        "with the installed versions."
    ),
    "producer-tool-configuration-changed": (
        "Restore the producer configuration used at sync, or re-run sync with the "
        "current producer configuration."
    ),
    "producer-tool-configuration-unknown": (
        "Make the producer configuration basis available and explicit, then "
        "re-run sync."
    ),
    "producer-tool-id-changed": (
        "Use the producer tool recorded at sync, or re-run sync with the current "
        "producer tool."
    ),
    "producer-tool-limitations-changed": (
        "Use a producer with the limitations recorded at sync, or re-run sync "
        "after accepting the changed limitations."
    ),
    "producer-tool-version-changed": (
        "Use the producer version recorded at sync, or re-run sync with the "
        "installed producer version."
    ),
    "source-mapping-changed": (
        "Restore this concept's recorded source mapping, or re-run sync to record "
        "the moved or remapped source."
    ),
    "version-unknown": (
        "Make concrete versions available for every contributing producer, "
        "extractor, and plugin, then re-run sync."
    ),
}


@pytest.mark.parametrize(
    ("reason_code", "expected_hint"),
    sorted(_EXPECTED_BASIS_INCOMPATIBLE_HINTS.items()),
)
def test_every_basis_incompatibility_has_distinct_actionable_guidance(
    reason_code,
    expected_hint,
):
    assert knowledge_freshness_hint(
        ComputedFreshness.BASIS_INCOMPATIBLE,
        reason_code,
    ) == expected_hint
    assert BASIS_INCOMPATIBLE_HINTS[reason_code] == expected_hint


def test_basis_incompatibility_guidance_is_exact_unique_and_privacy_safe():
    assert BASIS_INCOMPATIBLE_REASON_CODES == frozenset(
        _EXPECTED_BASIS_INCOMPATIBLE_HINTS
    )
    assert dict(BASIS_INCOMPATIBLE_HINTS) == _EXPECTED_BASIS_INCOMPATIBLE_HINTS
    hints = tuple(BASIS_INCOMPATIBLE_HINTS.values())
    assert len(hints) == len(set(hints)) == 22
    assert all(hint and hint == hint.strip() for hint in hints)
    encoded = "\n".join(hints)
    assert "sha256:" not in encoded
    assert "llm-wiki://" not in encoded
    assert "src/" not in encoded
    with pytest.raises(TypeError):
        BASIS_INCOMPATIBLE_HINTS["future-reason"] = "mutable"  # type: ignore[index]


@pytest.mark.parametrize("reason_code", [None, "", "future-incompatible-reason"])
def test_unknown_basis_incompatibility_guidance_fails_closed(reason_code):
    with pytest.raises(ValueError, match="known actionable reason"):
        knowledge_freshness_hint("basis-incompatible", reason_code)


@pytest.mark.parametrize(
    "state",
    [None, "not-evaluated", *tuple(
        value for value in ComputedFreshness
        if value is not ComputedFreshness.BASIS_INCOMPATIBLE
    )],
)
def test_guidance_is_absent_outside_basis_incompatibility(state):
    assert (
        knowledge_freshness_hint(state, "generation-options-changed")
        is None
    )


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

    assert knowledge_freshness_disclosure(view) == "evaluated (6 concepts)"
    assert knowledge_status_payload(view)["freshness"] == "evaluated (6 concepts)"
    assert summary.to_payload() == {
        "availability": "ready",
        "reason": "all-projection-commitments-match",
        "freshness": "evaluated (6 concepts)",
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

    assert (
        knowledge_freshness_disclosure(observed.view)
        == "unevaluated (snapshot-only read)"
    )
    assert knowledge_status_payload(observed.view) == {
        "availability": "ready",
        "reason": "all-projection-commitments-match",
        "freshness": "unevaluated (snapshot-only read)",
        "freshness_evaluated": False,
    }
    assert payload["concepts_evaluated"] == 0
    assert payload["freshness"] == "unevaluated (snapshot-only read)"
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
        "freshness": "unevaluated (snapshot-only read)",
        "freshness_evaluated": False,
    }


def test_absent_status_without_a_read_view_discloses_snapshot_limitation():
    assert knowledge_status_payload(None) == {
        "availability": "absent",
        "reason": "knowledge-projection-not-present",
        "freshness": "unevaluated (snapshot-only read)",
        "freshness_evaluated": False,
    }


@pytest.mark.parametrize("value", [None, object(), "view"])
def test_freshness_disclosure_rejects_non_read_views(value):
    with pytest.raises(TypeError, match="KnowledgeReadView"):
        knowledge_freshness_disclosure(value)


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
