"""Shared native-consumer read-session tests (KNOW-202)."""

from __future__ import annotations

import json
from collections import Counter
from dataclasses import replace

import pytest

from llm_wiki_cli.services import knowledge_consumption
from llm_wiki_cli.services.io import write_bytes_atomic
from llm_wiki_cli.services.knowledge_artifacts import KNOWLEDGE_INDEX_FILENAME
from llm_wiki_cli.services.knowledge_consumption import (
    KnowledgeAvailability,
    KnowledgeReadCounts,
    KnowledgeReadMode,
    KnowledgeReadReason,
    KnowledgeReadView,
    build_knowledge_read_view,
    open_knowledge_read_view,
)
from llm_wiki_cli.services.knowledge_evidence import formatted_json_bytes
from llm_wiki_cli.services.knowledge_freshness import KnowledgeFreshnessError
from llm_wiki_cli.services.knowledge_loader import (
    KnowledgeMismatchPolicy,
    KnowledgeStateLoadError,
    load_knowledge_state,
)
from llm_wiki_cli.services.knowledge_model import (
    ComputedFreshness,
    EvidenceState,
    KnowledgeLoadState,
    knowledge_index_to_payload,
    parse_knowledge_index,
)
from llm_wiki_cli.services.sync_manifest import MANIFEST_FILENAME
from llm_wiki_cli.services.wiki_surface_index import SURFACE_INDEX_FILENAME
from tests.knowledge_fixtures import fixture_hash, one_module_two_entities_fixture
from tests.test_knowledge_artifacts import _plan
from tests.test_knowledge_freshness import _live_evaluation
from tests.test_knowledge_loader import _committed_state, _write_fixture_pages


def _expected_concept_counts(knowledge):
    counts = Counter(
        (
            concept.concept_kind.value
            if hasattr(concept.concept_kind, "value")
            else concept.concept_kind
        )
        for concept in knowledge.concepts
    )
    return dict(sorted(counts.items()))


def _expected_evidence_counts(knowledge):
    counts = Counter(
        concept.facets.structure.evidence for concept in knowledge.concepts
    )
    return {state: counts.get(state, 0) for state in EvidenceState}


def _assert_no_knowledge_claims(view: KnowledgeReadView) -> None:
    assert view.knowledge is None
    assert view.freshness is None
    assert view.counts is None


def test_valid_live_read_view_exposes_validated_state_and_exact_counts(tmp_path):
    assert KnowledgeReadMode.DEFAULT is KnowledgeReadMode.EVALUATE_FRESHNESS
    _committed_state(tmp_path)
    loaded = load_knowledge_state(tmp_path)
    assert loaded.knowledge is not None
    live = _live_evaluation(loaded.knowledge)

    view = build_knowledge_read_view(
        loaded,
        live_evaluation=live,
    )

    assert isinstance(view, KnowledgeReadView)
    assert view.availability is KnowledgeAvailability.READY
    assert view.mode is KnowledgeReadMode.EVALUATE_FRESHNESS
    assert view.reason is KnowledgeReadReason.READY
    assert view.surface == loaded.surface
    assert view.knowledge == loaded.knowledge
    assert view.manifest_basis == loaded.manifest_basis
    assert view.projection_findings == ()
    assert view.freshness is not None
    assert isinstance(view.counts, KnowledgeReadCounts)
    assert view.counts.concept_total == len(loaded.knowledge.concepts)
    assert dict(view.counts.concepts_by_kind) == _expected_concept_counts(
        loaded.knowledge
    )
    assert dict(view.counts.evidence_by_state) == _expected_evidence_counts(
        loaded.knowledge
    )
    assert dict(view.counts.freshness_by_state) == dict(view.freshness.counts)
    assert view.counts.freshness_by_state[ComputedFreshness.CURRENT] == 3
    assert view.counts.freshness_by_state[ComputedFreshness.UNKNOWN] == 3


def test_default_read_without_live_evidence_never_claims_current(tmp_path):
    _committed_state(tmp_path)
    loaded = load_knowledge_state(tmp_path)
    assert loaded.knowledge is not None

    view = build_knowledge_read_view(loaded)

    assert view.availability is KnowledgeAvailability.READY
    assert view.mode is KnowledgeReadMode.EVALUATE_FRESHNESS
    assert view.freshness is not None
    assert view.counts is not None
    assert set(view.freshness.by_locator) == {
        concept.locator for concept in loaded.knowledge.concepts
    }
    assert all(
        result.state is ComputedFreshness.UNKNOWN
        for result in view.freshness.by_locator.values()
    )
    assert view.counts.freshness_by_state[ComputedFreshness.CURRENT] == 0
    assert view.counts.freshness_by_state[ComputedFreshness.UNKNOWN] == len(
        loaded.knowledge.concepts
    )


def test_snapshot_only_mode_skips_freshness_but_keeps_snapshot_counts(
    tmp_path,
    monkeypatch,
):
    _committed_state(tmp_path)
    loaded = load_knowledge_state(tmp_path)
    assert loaded.knowledge is not None
    live = _live_evaluation(loaded.knowledge)

    def fail_if_evaluated(*_args, **_kwargs):
        raise AssertionError("snapshot-only reads must not evaluate freshness")

    monkeypatch.setattr(
        knowledge_consumption,
        "evaluate_knowledge_freshness",
        fail_if_evaluated,
    )

    view = build_knowledge_read_view(
        loaded,
        live_evaluation=live,
        mode=KnowledgeReadMode.SNAPSHOT_ONLY,
    )

    assert view.availability is KnowledgeAvailability.READY
    assert view.mode is KnowledgeReadMode.SNAPSHOT_ONLY
    assert view.reason is KnowledgeReadReason.READY
    assert view.freshness is None
    assert view.counts is not None
    assert view.counts.concept_total == len(loaded.knowledge.concepts)
    assert dict(view.counts.concepts_by_kind) == _expected_concept_counts(
        loaded.knowledge
    )
    assert dict(view.counts.evidence_by_state) == _expected_evidence_counts(
        loaded.knowledge
    )
    assert view.counts.freshness_by_state is None


def test_legacy_surface_only_state_is_absent_and_remains_usable(tmp_path):
    fixture = one_module_two_entities_fixture()
    _write_fixture_pages(tmp_path, fixture)
    plan = _plan(tmp_path, fixture)
    write_bytes_atomic(tmp_path / SURFACE_INDEX_FILENAME, plan.surface_index.content)
    loaded = load_knowledge_state(tmp_path)
    assert loaded.status is KnowledgeLoadState.ABSENT

    view = build_knowledge_read_view(loaded)

    assert view.availability is KnowledgeAvailability.ABSENT
    assert view.reason is KnowledgeReadReason.ABSENT
    assert view.surface == loaded.surface
    assert view.manifest_basis is None
    assert view.projection_findings == loaded.issues
    assert tuple(issue.code for issue in view.projection_findings) == (
        "manifest-absent",
    )
    _assert_no_knowledge_claims(view)


@pytest.mark.parametrize("manifest_version", [1, 2, 3, 4])
def test_legacy_manifest_without_knowledge_remains_absent(
    tmp_path,
    manifest_version,
):
    fixture = one_module_two_entities_fixture()
    _write_fixture_pages(tmp_path, fixture)
    plan = _plan(tmp_path, fixture)
    write_bytes_atomic(tmp_path / SURFACE_INDEX_FILENAME, plan.surface_index.content)
    write_bytes_atomic(
        tmp_path / MANIFEST_FILENAME,
        formatted_json_bytes(
            {
                "version": manifest_version,
                "sources": {},
            }
        ),
    )

    view = open_knowledge_read_view(tmp_path, snapshot_only=True)

    assert view.availability is KnowledgeAvailability.ABSENT
    assert view.surface is not None
    assert view.manifest_basis is not None
    assert view.projection_findings == ()
    _assert_no_knowledge_claims(view)


def test_malformed_knowledge_degrades_without_knowledge_claims(tmp_path):
    _committed_state(tmp_path)
    (tmp_path / KNOWLEDGE_INDEX_FILENAME).write_bytes(b"{not-json\n")
    loaded = load_knowledge_state(
        tmp_path,
        policy=KnowledgeMismatchPolicy.DEGRADED,
    )
    assert loaded.status is KnowledgeLoadState.DEGRADED
    assert loaded.underlying_status is KnowledgeLoadState.INVALID

    view = build_knowledge_read_view(loaded)

    assert view.availability is KnowledgeAvailability.DEGRADED
    assert view.reason is KnowledgeReadReason.DEGRADED_INVALID
    assert view.surface == loaded.surface
    assert view.manifest_basis is None
    assert view.projection_findings == loaded.issues
    assert tuple(
        (issue.code, issue.artifact_path, issue.field)
        for issue in view.projection_findings
    ) == (
        (
            "knowledge-invalid",
            KNOWLEDGE_INDEX_FILENAME,
            "knowledge_index_bytes",
        ),
    )
    _assert_no_knowledge_claims(view)


def test_declared_missing_knowledge_is_degraded_not_absent(tmp_path):
    _committed_state(tmp_path)
    (tmp_path / KNOWLEDGE_INDEX_FILENAME).unlink()
    loaded = load_knowledge_state(
        tmp_path,
        policy=KnowledgeMismatchPolicy.DEGRADED,
    )

    view = build_knowledge_read_view(loaded)

    assert view.availability is KnowledgeAvailability.DEGRADED
    assert view.reason is KnowledgeReadReason.DEGRADED_INVALID
    assert view.projection_findings == loaded.issues
    assert any(
        issue.code == "declared-artifact-missing"
        for issue in view.projection_findings
    )
    _assert_no_knowledge_claims(view)


def test_unsupported_schema_is_distinct_from_absent_and_malformed(tmp_path):
    _fixture, plan, _result = _committed_state(tmp_path)
    payload = json.loads(plan.knowledge_index.content)
    payload["schema_version"] = "llm-wiki-knowledge/v999"
    (tmp_path / KNOWLEDGE_INDEX_FILENAME).write_bytes(formatted_json_bytes(payload))
    loaded = load_knowledge_state(
        tmp_path,
        policy=KnowledgeMismatchPolicy.DEGRADED,
    )

    view = build_knowledge_read_view(loaded)

    assert view.availability is KnowledgeAvailability.UNSUPPORTED
    assert view.availability not in {
        KnowledgeAvailability.ABSENT,
        KnowledgeAvailability.DEGRADED,
    }
    assert view.reason is KnowledgeReadReason.UNSUPPORTED_SCHEMA
    assert view.surface == loaded.surface
    assert view.projection_findings == loaded.issues
    assert tuple(
        (issue.code, issue.artifact_path, issue.field)
        for issue in view.projection_findings
    ) == (
        (
            "knowledge-schema-version-unsupported",
            KNOWLEDGE_INDEX_FILENAME,
            "knowledge_index_bytes.schema_version",
        ),
    )
    _assert_no_knowledge_claims(view)


def test_minimal_future_knowledge_shape_opens_as_unsupported(tmp_path):
    _committed_state(tmp_path)
    (tmp_path / KNOWLEDGE_INDEX_FILENAME).write_bytes(
        formatted_json_bytes(
            {
                "schema_version": "llm-wiki-knowledge/v999",
            }
        )
    )

    view = open_knowledge_read_view(tmp_path)

    assert view.availability is KnowledgeAvailability.UNSUPPORTED
    assert view.reason is KnowledgeReadReason.UNSUPPORTED_SCHEMA
    assert view.surface is not None
    assert tuple(
        (issue.code, issue.field) for issue in view.projection_findings
    ) == (
        (
            "knowledge-schema-version-unsupported",
            "knowledge_index_bytes.schema_version",
        ),
    )
    _assert_no_knowledge_claims(view)


def test_mixed_snapshot_degrades_and_yields_no_knowledge_claims(tmp_path):
    _fixture, _plan_value, committed = _committed_state(tmp_path)
    marker = committed.committed_manifest.artifact_hashes
    assert marker is not None
    mismatched_marker = replace(
        marker,
        knowledge_index_hash=fixture_hash("knowledge-consumption:mixed"),
    )
    replace(
        committed.committed_manifest,
        artifact_hashes=mismatched_marker,
    ).save(tmp_path)
    loaded = load_knowledge_state(
        tmp_path,
        policy=KnowledgeMismatchPolicy.DEGRADED,
    )
    assert loaded.status is KnowledgeLoadState.DEGRADED
    assert loaded.underlying_status is KnowledgeLoadState.MIXED_SNAPSHOT

    view = build_knowledge_read_view(loaded)

    assert view.availability is KnowledgeAvailability.DEGRADED
    assert view.reason is KnowledgeReadReason.DEGRADED_MIXED_SNAPSHOT
    assert view.surface == loaded.surface
    assert view.projection_findings == loaded.issues
    assert tuple(
        (issue.code, issue.artifact_path, issue.field)
        for issue in view.projection_findings
    ) == (
        (
            "knowledge-hash-mismatch",
            KNOWLEDGE_INDEX_FILENAME,
            "artifact_hashes.knowledge_index_hash",
        ),
    )
    _assert_no_knowledge_claims(view)


@pytest.mark.parametrize(
    ("mode", "expected_freshness_calls"),
    [
        (KnowledgeReadMode.EVALUATE_FRESHNESS, 1),
        (KnowledgeReadMode.SNAPSHOT_ONLY, 0),
    ],
)
def test_open_read_view_loads_once_evaluates_at_most_once_and_never_rebuilds(
    tmp_path,
    monkeypatch,
    mode,
    expected_freshness_calls,
):
    _committed_state(tmp_path)
    loaded = load_knowledge_state(tmp_path)
    assert loaded.knowledge is not None
    live = _live_evaluation(loaded.knowledge)
    markdown_pages = {"index.md": "# supplied once\n"}
    load_calls = []
    freshness_calls = []
    real_evaluator = knowledge_consumption.evaluate_knowledge_freshness

    def recording_loader(wiki_dir, **kwargs):
        load_calls.append((wiki_dir, kwargs))
        return loaded

    def recording_evaluator(knowledge, live_evaluation):
        freshness_calls.append((knowledge, live_evaluation))
        return real_evaluator(knowledge, live_evaluation)

    monkeypatch.setattr(
        knowledge_consumption,
        "load_knowledge_state",
        recording_loader,
    )
    monkeypatch.setattr(
        knowledge_consumption,
        "evaluate_knowledge_freshness",
        recording_evaluator,
    )

    view = open_knowledge_read_view(
        tmp_path,
        live_evaluation=live,
        mode=mode,
        markdown_pages=markdown_pages,
    )

    assert view.availability is KnowledgeAvailability.READY
    assert len(load_calls) == 1
    assert load_calls[0][0] == tmp_path
    loader_kwargs = load_calls[0][1]
    assert loader_kwargs["policy"] is KnowledgeMismatchPolicy.DEGRADED
    assert loader_kwargs["markdown_pages"] is markdown_pages
    assert "rebuild_callback" not in loader_kwargs
    assert len(freshness_calls) == expected_freshness_calls
    if freshness_calls:
        assert freshness_calls[0] == (loaded.knowledge, live)
    assert (view.freshness is not None) is bool(expected_freshness_calls)


def test_build_read_view_uses_only_the_supplied_loader_result(
    tmp_path,
    monkeypatch,
):
    _committed_state(tmp_path)
    loaded = load_knowledge_state(tmp_path)

    def fail_if_loaded(*_args, **_kwargs):
        raise AssertionError("build_knowledge_read_view must not load artifacts")

    monkeypatch.setattr(
        knowledge_consumption,
        "load_knowledge_state",
        fail_if_loaded,
    )

    view = build_knowledge_read_view(
        loaded,
        mode=KnowledgeReadMode.SNAPSHOT_ONLY,
    )

    assert view.availability is KnowledgeAvailability.READY
    assert view.knowledge == loaded.knowledge


def test_future_manifest_without_knowledge_opens_as_unsupported(tmp_path):
    _committed_state(tmp_path)
    manifest_path = tmp_path / MANIFEST_FILENAME
    payload = json.loads(manifest_path.read_bytes())
    payload["version"] = 999
    manifest_path.write_bytes(formatted_json_bytes(payload))
    (tmp_path / KNOWLEDGE_INDEX_FILENAME).unlink()

    view = open_knowledge_read_view(tmp_path)

    assert view.availability is KnowledgeAvailability.UNSUPPORTED
    assert view.reason is KnowledgeReadReason.MANIFEST_VERSION_UNSUPPORTED
    assert view.surface is not None
    assert view.manifest_basis is None
    assert tuple(issue.code for issue in view.projection_findings) == (
        "manifest-version-unsupported",
    )
    _assert_no_knowledge_claims(view)


def test_future_surface_opens_as_unsupported_without_exposing_payloads(tmp_path):
    _committed_state(tmp_path)
    (tmp_path / SURFACE_INDEX_FILENAME).write_bytes(
        formatted_json_bytes(
            {
                "schema_version": "llm-wiki-surface-index/v999",
            }
        )
    )

    view = open_knowledge_read_view(tmp_path)

    assert view.availability is KnowledgeAvailability.UNSUPPORTED
    assert view.reason is KnowledgeReadReason.SURFACE_SCHEMA_VERSION_UNSUPPORTED
    assert view.surface is None
    assert view.manifest_basis is None
    assert tuple(issue.code for issue in view.projection_findings) == (
        "surface-schema-version-unsupported",
    )
    _assert_no_knowledge_claims(view)


def test_invalid_surface_still_raises_instead_of_fabricating_degraded_view(
    tmp_path,
):
    _fixture, plan, _result = _committed_state(tmp_path)
    surface = json.loads(plan.surface_index.content)
    surface["schema_version"] = 999
    (tmp_path / SURFACE_INDEX_FILENAME).write_bytes(formatted_json_bytes(surface))

    with pytest.raises(KnowledgeStateLoadError) as exc_info:
        open_knowledge_read_view(tmp_path)

    assert exc_info.value.status is KnowledgeLoadState.INVALID
    assert tuple(issue.code for issue in exc_info.value.issues) == (
        "surface-invalid",
    )


def test_ready_view_propagates_live_evaluation_failures(tmp_path, monkeypatch):
    _committed_state(tmp_path)
    loaded = load_knowledge_state(tmp_path)

    def fail_freshness(*_args, **_kwargs):
        raise KnowledgeFreshnessError("live.schema_version", "is invalid")

    monkeypatch.setattr(
        knowledge_consumption,
        "evaluate_knowledge_freshness",
        fail_freshness,
    )

    with pytest.raises(KnowledgeFreshnessError) as exc_info:
        build_knowledge_read_view(loaded)

    assert exc_info.value.field == "live.schema_version"


def test_non_ready_view_never_evaluates_supplied_live_evidence(
    tmp_path,
    monkeypatch,
):
    _committed_state(tmp_path)
    ready = load_knowledge_state(tmp_path)
    assert ready.knowledge is not None
    live = _live_evaluation(ready.knowledge)
    (tmp_path / KNOWLEDGE_INDEX_FILENAME).write_bytes(b"{not-json\n")
    degraded = load_knowledge_state(
        tmp_path,
        policy=KnowledgeMismatchPolicy.DEGRADED,
    )

    def fail_if_evaluated(*_args, **_kwargs):
        raise AssertionError("unavailable knowledge must not evaluate freshness")

    monkeypatch.setattr(
        knowledge_consumption,
        "evaluate_knowledge_freshness",
        fail_if_evaluated,
    )

    view = build_knowledge_read_view(
        degraded,
        live_evaluation=live,
    )

    assert view.availability is KnowledgeAvailability.DEGRADED
    assert view.freshness is None


def test_snapshot_counts_are_independent_of_concept_input_order(tmp_path):
    _committed_state(tmp_path)
    loaded = load_knowledge_state(tmp_path)
    assert loaded.knowledge is not None
    reversed_knowledge = replace(
        loaded.knowledge,
        concepts=tuple(reversed(loaded.knowledge.concepts)),
    )

    original = build_knowledge_read_view(loaded, snapshot_only=True)
    reordered = build_knowledge_read_view(
        replace(loaded, knowledge=reversed_knowledge),
        snapshot_only=True,
    )

    assert original.counts == reordered.counts


def test_counts_preserve_qualified_open_concept_kinds(tmp_path):
    _committed_state(tmp_path)
    loaded = load_knowledge_state(tmp_path)
    assert loaded.knowledge is not None
    custom = replace(
        loaded.knowledge.concepts[0],
        concept_kind="example/custom-kind",
    )
    custom_knowledge = parse_knowledge_index(
        knowledge_index_to_payload(
            replace(
                loaded.knowledge,
                concepts=(custom, *loaded.knowledge.concepts[1:]),
            )
        )
    )

    view = build_knowledge_read_view(
        replace(loaded, knowledge=custom_knowledge),
        snapshot_only=True,
    )

    assert view.counts is not None
    assert view.counts.concepts_by_kind["example/custom-kind"] == 1
    assert sum(view.counts.concepts_by_kind.values()) == view.counts.concepts_total
