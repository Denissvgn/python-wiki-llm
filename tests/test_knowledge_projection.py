"""Safe native-knowledge projection and redaction contract tests."""

from __future__ import annotations

import json
from copy import deepcopy
from dataclasses import replace

import pytest

from llm_wiki_cli.services.contracts import GOVERNANCE_EXTENSION_KEY
from llm_wiki_cli.services.documentation_queries import (
    DocumentationGraphQueryService,
)
from llm_wiki_cli.services.knowledge_artifacts import (
    build_knowledge_commit_plan,
)
from llm_wiki_cli.services.knowledge_consumption import (
    KnowledgeAvailability,
    KnowledgeReadView,
    MachineVerificationAvailability,
    MachineVerificationReadView,
    build_knowledge_read_view,
)
from llm_wiki_cli.services.knowledge_freshness import (
    evaluate_knowledge_freshness,
)
from llm_wiki_cli.services.knowledge_generation import (
    build_knowledge_generation_plan,
)
from llm_wiki_cli.services.knowledge_loader import KnowledgeLoadResult
from llm_wiki_cli.services.knowledge_governance import (
    GovernanceActor,
    GovernanceLedger,
    apply_governance_projection,
    concept_references_from_knowledge,
    reconcile_concepts,
    set_lifecycle,
)
from llm_wiki_cli.services.knowledge_model import (
    ComputedFreshness,
    KnowledgeLoadState,
    KnowledgeProjectionProfile,
    knowledge_index_to_payload,
    parse_knowledge_index,
    serialize_knowledge_index,
)
from llm_wiki_cli.services.knowledge_observability import (
    BASIS_INCOMPATIBLE_HINTS,
)
from llm_wiki_cli.services.knowledge_projection import (
    KnowledgeProjection,
    KnowledgeProjectionError,
    project_knowledge,
    projection_concept_summary,
    serialize_knowledge_projection,
    validate_projection_summaries,
)
from tests.knowledge_fixtures import (
    FIXTURE_REPOSITORY_IDENTITY,
    duplicate_entity_occurrences_fixture,
    one_module_two_entities_fixture,
)
from tests.test_knowledge_artifacts import _plan
from tests.test_knowledge_freshness import _live_evaluation
from tests.test_knowledge_generation import _planner_inputs


def _view_for_model(tmp_path, model) -> KnowledgeReadView:
    fixture = one_module_two_entities_fixture()
    base_plan = _plan(tmp_path, fixture)
    manifest = replace(
        base_plan.committed_manifest,
        artifact_hashes=None,
    )
    plan = build_knowledge_commit_plan(
        tmp_path,
        surface_index_bytes=fixture.surface_bytes,
        knowledge_index_bytes=serialize_knowledge_index(model).encode("utf-8"),
        manifest=manifest,
    )
    result = KnowledgeLoadResult(
        status=KnowledgeLoadState.VALID,
        surface=json.loads(fixture.surface_bytes),
        knowledge=model,
        manifest_basis=plan.committed_manifest,
        issues=(),
    )
    return build_knowledge_read_view(result, snapshot_only=True)


def _base_model(tmp_path):
    fixture = one_module_two_entities_fixture()
    plan = _plan(tmp_path, fixture)
    return parse_knowledge_index(json.loads(plan.knowledge_index.content))


def _base_view(tmp_path) -> KnowledgeReadView:
    return _view_for_model(tmp_path, _base_model(tmp_path))


def _view_for_generation_plan(plan) -> KnowledgeReadView:
    result = KnowledgeLoadResult(
        status=KnowledgeLoadState.VALID,
        surface=json.loads(plan.surface_index.content),
        knowledge=parse_knowledge_index(
            json.loads(plan.knowledge_index.content)
        ),
        manifest_basis=plan.committed_manifest,
        issues=(),
    )
    return build_knowledge_read_view(result, snapshot_only=True)


def _projection_from_payload(payload) -> KnowledgeProjection:
    return KnowledgeProjection(
        schema_version=payload["schema_version"],
        profile=KnowledgeProjectionProfile(payload["profile"]),
        source_knowledge_hash=payload["source_knowledge_hash"],
        bundle=payload["bundle"],
        concepts=payload["concepts"],
        warnings=tuple(payload["warnings"]),
        omitted_fields=payload["omitted_fields"],
        freshness=payload.get("freshness"),
    )


def _governed_projection(tmp_path) -> KnowledgeProjection:
    model = _base_model(tmp_path)
    ledger = reconcile_concepts(
        GovernanceLedger.empty("kb_projection_validation"),
        concept_references_from_knowledge(model),
    )
    governed = apply_governance_projection(model, ledger)
    return project_knowledge(_view_for_model(tmp_path, governed))


def test_public_projection_is_allowlist_only_and_deterministic(tmp_path):
    model = _base_model(tmp_path)
    first = model.concepts[0]
    secret = "ghp_seededSecret1234567890"
    concept = replace(
        first,
        facets=replace(
            first.facets,
            semantics=replace(
                first.facets.semantics,
                extensions={
                    "example.invalid/source-snippet": (
                        "def private_implementation(): return 'classified'"
                    )
                },
            ),
        ),
        extensions={
            **first.extensions,
            "example.invalid/private": {
                "checkout": "/Users/alice/private/repository",
                "credential": secret,
                "environment": {"DEPLOY_ENV": "classified"},
            },
        },
    )
    model = replace(
        model,
        concepts=(concept, *model.concepts[1:]),
        extensions={
            **model.extensions,
            "example.invalid/benign": {"value": "retained-internal"},
            "example.invalid/secret": {"token": secret},
        },
    )
    ledger = reconcile_concepts(
        GovernanceLedger.empty("projection-redaction"),
        concept_references_from_knowledge(model),
    )
    first_uid = next(
        uid
        for uid, allocation in ledger.concepts.items()
        if allocation.locator == concept.locator
    )
    ledger = set_lifecycle(
        ledger,
        first_uid,
        "active",
        actor=GovernanceActor("human", "private-reviewer@example.invalid"),
        authored_at="2026-07-27T12:00:00Z",
    )
    model = apply_governance_projection(model, ledger)
    view = _view_for_model(tmp_path, model)

    first_projection = project_knowledge(view)
    second_projection = project_knowledge(
        replace(
            view,
            knowledge=replace(
                view.knowledge,
                concepts=tuple(reversed(view.knowledge.concepts)),
            ),
        )
    )
    encoded = serialize_knowledge_projection(first_projection)

    assert encoded == serialize_knowledge_projection(second_projection)
    assert secret not in encoded
    assert "private-reviewer@example.invalid" not in encoded
    assert "/Users/alice" not in encoded
    assert "private_implementation" not in encoded
    assert "example.invalid/private" not in encoded
    assert "example.invalid/benign" not in encoded
    assert first_projection.bundle["repository_identity"] == "unknown"
    assert first_projection.bundle["repository_identity_source"] == "unknown"
    assert first_projection.bundle["evaluated_revision"] == "unknown"
    assert first_projection.bundle["working_tree"] == "unknown"
    assert first_projection.omitted_fields["actor_identities"] >= 1
    assert first_projection.omitted_fields["unknown_extensions"] >= 3
    assert first_projection.omitted_fields["private_repository_identity"] == 1
    assert {
        warning
        for warning in first_projection.warnings
        if warning.startswith("omitted-")
    } == {
        f"omitted-{name.replace('_', '-')}"
        for name, count in first_projection.omitted_fields.items()
        if count > 0
    }


def test_internal_projection_sanitizes_hostile_values_and_raw_events(
    tmp_path,
):
    model = _base_model(tmp_path)
    selected = model.concepts[0]
    ledger = reconcile_concepts(
        GovernanceLedger.empty("kb_hostile_projection"),
        concept_references_from_knowledge(model),
    )
    uid = next(
        concept_uid
        for concept_uid, allocation in ledger.concepts.items()
        if allocation.locator == selected.locator
    )
    ledger = set_lifecycle(
        ledger,
        uid,
        "active",
        actor=GovernanceActor(
            "tool",
            "git@example.invalid:private-repository.git",
        ),
        authored_at="2026-07-27T12:00:00Z",
        reason="sk-proj-abcdefghijk",
    )
    payload = knowledge_index_to_payload(
        apply_governance_projection(model, ledger)
    )
    review = {
        "items": [
            {
                "event_id": "rv_" + ("a" * 64),
                "section_locator": (
                    selected.locator + "#section/Description~1"
                ),
                "state": "valid",
                "reasons": [],
                "reviewer": {
                    "kind": "human",
                    "id": "xoxb-abcdefghijk",
                },
                "method": {
                    "id": "eyJabcdefghij.eyJabcdefghij.abcdefghij",
                    "version": "1",
                },
                "authored_at": "2026-07-27T12:01:00Z",
            }
        ],
        "total": 1,
        "returned": 1,
        "limit": 20,
        "truncated": False,
    }
    governance = payload["extensions"][GOVERNANCE_EXTENSION_KEY]
    governance["concepts"][selected.locator]["reviews"] = deepcopy(review)
    projected_concept = next(
        concept
        for concept in payload["concepts"]
        if concept["locator"] == selected.locator
    )
    projected_concept["extensions"][GOVERNANCE_EXTENSION_KEY][
        "reviews"
    ] = deepcopy(review)
    payload["extensions"]["example.invalid/hostile-values"] = {
        "safe": "safe-extension-value",
        "openai": "sk-proj-abcdefghijk",
        "slack": "xoxb-abcdefghijk",
        "jwt": "eyJabcdefghij.eyJabcdefghij.abcdefghij",
        "scp_remote": "git@example.invalid:private-repository.git",
        "https_remote": (
            "https://example.invalid/acme/private-repository.git"
        ),
        "embedded_path": "checkout at /Users/alice/private/repository",
        "credential_url": (
            "https://alice:hunter2@example.invalid/private"
        ),
    }
    producer_secret = "ghp_producerSecret1234567890"
    payload["bundle"]["producer"]["tool"]["version"] = producer_secret
    model = parse_knowledge_index(payload)

    projection = project_knowledge(
        _view_for_model(tmp_path, model),
        profile=KnowledgeProjectionProfile.INTERNAL,
    )
    encoded = serialize_knowledge_projection(projection)

    assert projection.bundle["repository_identity"] == FIXTURE_REPOSITORY_IDENTITY
    assert projection.bundle["evaluated_revision"].startswith("git:")
    assert projection.bundle["working_tree"] == "clean"
    assert "safe-extension-value" in encoded
    for hostile in (
        "sk-proj-abcdefghijk",
        "xoxb-abcdefghijk",
        "eyJabcdefghij.eyJabcdefghij.abcdefghij",
        "git@example.invalid:private-repository.git",
        "https://example.invalid/acme/private-repository.git",
        "/Users/alice/private/repository",
        "https://alice:hunter2@example.invalid/private",
        producer_secret,
    ):
        assert hostile not in encoded
    assert projection.bundle["producer"]["tool"]["version"] == "unknown"
    assert projection.omitted_fields["credential_like_values"] >= 7
    assert projection.omitted_fields["unsafe_paths"] >= 1
    projected = projection.concepts[selected.document.canonical_path]
    lifecycle_event = projected["lifecycle"]["events"][0]
    review_event = projected["review"]["items"][0]
    assert lifecycle_event["actor"] == {"kind": "tool"}
    assert "reason" not in lifecycle_event
    assert review_event["reviewer"] == {"kind": "human"}
    assert review_event["method"] == {"version": "1"}


def test_public_repository_identity_requires_current_caller_corroboration(
    tmp_path,
):
    view = _base_view(tmp_path)

    unknown = project_knowledge(view)
    path = next(iter(unknown.concepts))
    unknown_summary = projection_concept_summary(unknown, path)
    assert unknown.bundle["repository_identity"] == "unknown"
    assert unknown_summary["knowledge_repository_identity"] == "unknown"
    assert (
        unknown_summary["knowledge_repository_identity_source"] == "unknown"
    )
    approved = project_knowledge(
        view,
        public_repository_identity=FIXTURE_REPOSITORY_IDENTITY,
    )
    approved_summary = projection_concept_summary(approved, path)
    assert approved.bundle["repository_identity"] == FIXTURE_REPOSITORY_IDENTITY
    assert approved.bundle["repository_identity_source"] == "configured-public"
    assert (
        approved_summary["knowledge_repository_identity"]
        == FIXTURE_REPOSITORY_IDENTITY
    )
    assert (
        approved_summary["knowledge_repository_identity_source"]
        == "configured-public"
    )

    with pytest.raises(
        KnowledgeProjectionError,
        match="must exactly match a configured-public identity",
    ):
        project_knowledge(
            view,
            public_repository_identity="example.invalid/wrong/repository",
        )
    with pytest.raises(
        KnowledgeProjectionError,
        match="valid only for the 'public-portable' profile",
    ):
        project_knowledge(
            view,
            profile="internal",
            public_repository_identity=FIXTURE_REPOSITORY_IDENTITY,
        )


def test_projection_rejects_unready_and_mixed_read_views(tmp_path):
    view = _base_view(tmp_path)
    absent = replace(
        view,
        availability=KnowledgeAvailability.ABSENT,
        knowledge=None,
        manifest_basis=None,
    )
    with pytest.raises(KnowledgeProjectionError, match="requires a ready"):
        project_knowledge(absent)

    other = _base_model(tmp_path)
    changed = replace(
        other.concepts[0],
        title="Different committed concept",
    )
    mixed = replace(
        view,
        knowledge=replace(other, concepts=(changed, *other.concepts[1:])),
    )
    with pytest.raises(
        KnowledgeProjectionError,
        match="intact committed artifact set",
    ):
        project_knowledge(mixed)


def test_projection_discloses_snapshot_and_live_evaluation_scope(tmp_path):
    snapshot = _base_view(tmp_path)
    snapshot_projection = project_knowledge(snapshot)

    assert snapshot_projection.freshness == (
        "unevaluated (snapshot-only read)"
    )
    assert snapshot_projection.to_payload()["freshness"] == (
        "unevaluated (snapshot-only read)"
    )
    path = next(iter(snapshot_projection.concepts))
    assert projection_concept_summary(snapshot_projection, path)["freshness"] == (
        "unevaluated (snapshot-only read)"
    )

    evaluated_without_live = project_knowledge(
        replace(
            snapshot,
            freshness=evaluate_knowledge_freshness(snapshot.knowledge),
        )
    )
    assert evaluated_without_live.freshness == (
        f"evaluated ({len(evaluated_without_live.concepts)} concepts)"
    )
    assert all(
        concept["freshness"]
        == {
            "state": "unknown",
            "reason": "live-evaluation-not-performed",
            "evaluated": True,
            "live_comparison_performed": False,
        }
        for concept in evaluated_without_live.concepts.values()
    )

    live = replace(
        snapshot,
        freshness=evaluate_knowledge_freshness(
            snapshot.knowledge,
            _live_evaluation(snapshot.knowledge),
        ),
    )
    live_projection = project_knowledge(live)

    assert live_projection.freshness == (
        f"evaluated ({len(live_projection.concepts)} concepts)"
    )
    projected_freshness = [
        concept["freshness"] for concept in live_projection.concepts.values()
    ]
    assert all(item["evaluated"] is True for item in projected_freshness)
    assert any(
        item["state"] == "unknown"
        and item["live_comparison_performed"] is False
        for item in projected_freshness
    )


def test_empty_evaluated_projection_preserves_zero_concept_disclosure(
    tmp_path,
):
    projection = project_knowledge(_base_view(tmp_path))
    evaluated_empty = replace(
        projection,
        concepts={},
        freshness="evaluated (0 concepts)",
    )

    payload = json.loads(serialize_knowledge_projection(evaluated_empty))

    assert payload["concepts"] == {}
    assert payload["freshness"] == "evaluated (0 concepts)"


@pytest.mark.parametrize(
    ("reason_code", "expected_hint"),
    tuple(BASIS_INCOMPATIBLE_HINTS.items()),
)
def test_projection_and_frontmatter_render_every_incompatible_hint(
    tmp_path,
    reason_code,
    expected_hint,
):
    view = _base_view(tmp_path)
    assert view.knowledge is not None
    report = evaluate_knowledge_freshness(
        view.knowledge,
        _live_evaluation(view.knowledge),
    )
    locator = next(iter(report.by_locator))
    original = report.by_locator[locator]
    by_locator = dict(report.by_locator)
    by_locator[locator] = replace(
        original,
        state=ComputedFreshness.BASIS_INCOMPATIBLE,
        reason_code=reason_code,
        live_comparison_performed=True,
        description="the recorded and live bases are incompatible",
    )
    counts = dict(report.counts)
    counts[original.state] -= 1
    counts[ComputedFreshness.BASIS_INCOMPATIBLE] += 1
    mixed_view = replace(
        view,
        freshness=replace(
            report,
            by_locator=by_locator,
            counts=counts,
        ),
    )

    projection = project_knowledge(mixed_view)
    concept = next(
        concept
        for concept in view.knowledge.concepts
        if concept.locator == locator
    )
    freshness = projection.concepts[concept.document.canonical_path]["freshness"]
    summary = projection_concept_summary(
        projection,
        concept.document.canonical_path,
    )

    assert projection.freshness == (
        f"evaluated ({len(projection.concepts)} concepts)"
    )
    assert freshness["reason"] == reason_code
    assert freshness["hint"] == expected_hint
    assert summary["knowledge_freshness_reason"] == reason_code
    assert summary["knowledge_freshness_hint"] == expected_hint
    serialize_knowledge_projection(projection)


def test_projection_disclosure_is_explicit_counted_and_not_inferred(tmp_path):
    snapshot = project_knowledge(_base_view(tmp_path))
    without_explicit_disclosure = replace(snapshot, freshness=None)

    assert (
        without_explicit_disclosure.freshness
        == "unevaluated (snapshot-only read)"
    )
    serialize_knowledge_projection(without_explicit_disclosure)

    for disclosure in (
        "current",
        f"evaluated ({len(snapshot.concepts) + 1} concepts)",
        "evaluated (-1 concepts)",
        "evaluated (01 concepts)",
    ):
        forged = replace(snapshot, freshness=disclosure)
        with pytest.raises(
            KnowledgeProjectionError,
            match="freshness",
        ):
            serialize_knowledge_projection(forged)


@pytest.mark.parametrize(
    "aggregate_evaluated",
    [False, True],
    ids=["unevaluated-over-evaluated", "evaluated-over-unevaluated"],
)
def test_projection_rejects_aggregate_and_concept_evaluation_conflicts(
    tmp_path,
    aggregate_evaluated,
):
    snapshot = project_knowledge(_base_view(tmp_path))
    assert snapshot.freshness == "unevaluated (snapshot-only read)"
    assert all(
        concept["freshness"]["evaluated"] is False
        for concept in snapshot.concepts.values()
    )

    view = _base_view(tmp_path)
    assert view.knowledge is not None
    evaluated = project_knowledge(
        replace(
            view,
            freshness=evaluate_knowledge_freshness(
                view.knowledge,
                _live_evaluation(view.knowledge),
            ),
        )
    )
    assert all(
        concept["freshness"]["evaluated"] is True
        for concept in evaluated.concepts.values()
    )

    forged = replace(
        evaluated if aggregate_evaluated is False else snapshot,
        freshness=(
            "unevaluated (snapshot-only read)"
            if aggregate_evaluated is False
            else f"evaluated ({len(snapshot.concepts)} concepts)"
        ),
    )

    with pytest.raises(
        KnowledgeProjectionError,
        match="must agree with every concept freshness evaluated flag",
    ):
        forged.to_payload()


def test_projection_rejects_partially_evaluated_concept_flags(tmp_path):
    view = _base_view(tmp_path)
    assert view.knowledge is not None
    evaluated = project_knowledge(
        replace(
            view,
            freshness=evaluate_knowledge_freshness(
                view.knowledge,
                _live_evaluation(view.knowledge),
            ),
        )
    )
    payload = evaluated.to_payload()
    path = next(iter(payload["concepts"]))
    payload["concepts"][path]["freshness"] = {
        "state": "not-evaluated",
        "reason": "not-evaluated",
        "evaluated": False,
        "live_comparison_performed": False,
    }
    forged = _projection_from_payload(payload)

    with pytest.raises(
        KnowledgeProjectionError,
        match="must agree with every concept freshness evaluated flag",
    ):
        forged.to_payload()


def test_projection_rejects_missing_wrong_or_extraneous_hint(tmp_path):
    view = _base_view(tmp_path)
    assert view.knowledge is not None
    report = evaluate_knowledge_freshness(
        view.knowledge,
        _live_evaluation(view.knowledge),
    )
    locator = next(iter(report.by_locator))
    result = report.by_locator[locator]
    reason = "generation-options-changed"
    incompatible = replace(
        result,
        state=ComputedFreshness.BASIS_INCOMPATIBLE,
        reason_code=reason,
        live_comparison_performed=True,
    )
    projection = project_knowledge(
        replace(
            view,
            freshness=replace(
                report,
                by_locator={**report.by_locator, locator: incompatible},
            ),
        )
    )
    concept = next(
        concept
        for concept in view.knowledge.concepts
        if concept.locator == locator
    )
    path = concept.document.canonical_path

    def forged(mutator):
        payload = projection.to_payload()
        mutator(payload["concepts"][path]["freshness"])
        return _projection_from_payload(payload)

    candidates = (
        forged(lambda freshness: freshness.pop("hint")),
        forged(lambda freshness: freshness.__setitem__("hint", "generic")),
    )
    current_path = next(
        candidate_path
        for candidate_path, projected in projection.concepts.items()
        if projected["freshness"]["state"] != "basis-incompatible"
    )
    extraneous_payload = projection.to_payload()
    extraneous_payload["concepts"][current_path]["freshness"]["hint"] = (
        BASIS_INCOMPATIBLE_HINTS[reason]
    )
    candidates += (_projection_from_payload(extraneous_payload),)

    for candidate in candidates:
        with pytest.raises(KnowledgeProjectionError, match="hint"):
            serialize_knowledge_projection(candidate)


def test_projection_rejects_unrecognized_auxiliary_freshness_reason(
    tmp_path,
):
    view = _base_view(tmp_path)
    report = evaluate_knowledge_freshness(view.knowledge)
    locator = next(iter(report.by_locator))
    invalid_result = replace(
        report.by_locator[locator],
        reason_code="future-auxiliary-reason",
    )
    invalid_report = replace(
        report,
        by_locator={
            **report.by_locator,
            locator: invalid_result,
        },
    )

    with pytest.raises(
        KnowledgeProjectionError,
        match="invalid or unrecognized freshness result",
    ):
        project_knowledge(replace(view, freshness=invalid_report))


def test_typed_relationship_projection_matches_native_query_order_and_bounds(
    tmp_path,
):
    fixture = duplicate_entity_occurrences_fixture()
    source_path = next(iter(fixture.source_files))
    calls = (
        {
            "from": {"file": source_path, "symbol": "Parser.run"},
            "to": {"file": source_path, "symbol": "Parser.save"},
            "kind": "internal",
            "name": "save",
            "line": 10,
        },
        {
            "from": {"file": source_path, "symbol": "Parser.run"},
            "to": {"file": None, "symbol": "publish"},
            "kind": "external",
            "name": "queue.publish",
            "line": 11,
        },
        {
            "from": {"file": source_path, "symbol": "Parser.run"},
            "to": {"file": None, "symbol": "dynamic"},
            "kind": "unresolved",
            "name": "dynamic",
            "line": 12,
        },
        {
            "from": {"file": source_path, "symbol": "Parser.run"},
            "to": {"file": None, "symbol": "Parser"},
            "kind": "ambiguous",
            "name": "Parser",
            "line": 13,
            "candidates": [
                {"file": source_path, "symbol": "Parser"},
                {"file": "vendor/parser.py", "symbol": "Parser"},
            ],
        },
    )
    plan = build_knowledge_generation_plan(
        replace(
            _planner_inputs(tmp_path, fixture),
            call_edges=calls,
            graph_evidence_limit=1,
        )
    )
    view = _view_for_generation_plan(plan)
    projection = project_knowledge(
        view,
        profile="internal",
        relationship_limit=20,
    )
    service = DocumentationGraphQueryService(
        {},
        knowledge_view=view,
        limit=20,
    )

    for concept in view.knowledge.concepts:
        path = concept.document.canonical_path
        projected = projection.concepts[path]["relationships"]
        queried = service.traverse_typed_graph(concept.locator)
        assert projected["total"] == queried["total"]
        assert projected["returned"] == queried["returned"]
        assert projected["truncated"] == queried["truncated"]
        assert [
            (
                item["kind"],
                item["direction"],
                item["origin"],
                item["resolution"],
            )
            for item in projected["items"]
        ] == [
            (
                item["kind"],
                item["direction"],
                item["origin"],
                item["resolution"],
            )
            for item in queried["edges"]
        ]
        for item in projected["items"]:
            assert "unique" in item["evidence"]
            assert "limit" in item["coverage"]
            assert item["evidence"]["observed"] >= item["evidence"]["unique"]
            assert item["evidence"]["unique"] >= item["evidence"]["emitted"]
            assert item["coverage"]["observed"] >= item["coverage"]["emitted"]
            assert (
                item["coverage"]["omitted"]
                == item["coverage"]["observed"]
                - item["coverage"]["emitted"]
            )

    module = projection.concepts["modules/test_parser.md"]["relationships"]
    assert {item["resolution"] for item in module["items"]} == {
        "resolved",
        "ambiguous",
        "external",
        "unresolved",
    }
    self_loop = next(
        item
        for item in module["items"]
        if item["resolution"] == "resolved"
        and item["target"].get("canonical_path") == "modules/test_parser.md"
    )
    assert self_loop["direction"] == "both"
    assert next(
        item for item in module["items"] if item["resolution"] == "external"
    )["target"]["kind"] == "external-resource"
    assert {
        item["target"]["kind"]
        for item in module["items"]
        if item["resolution"] in {"ambiguous", "unresolved"}
    } == {"unresolved"}

    bounded = project_knowledge(
        view,
        profile="internal",
        relationship_limit=2,
    ).concepts["modules/test_parser.md"]["relationships"]
    assert bounded["total"] == module["total"]
    assert bounded["returned"] == 2
    assert bounded["limit"] == 2
    assert bounded["truncated"] is True


def test_shared_summary_validator_rejects_malformed_projection_shapes(
    tmp_path,
):
    projection = _governed_projection(tmp_path)
    paths = tuple(sorted(projection.concepts))
    first_path = paths[0]
    first_identity = projection.concepts[first_path]["identity"]
    bundle_id = projection.bundle["bundle_id"]
    namespaced_uid = first_identity["namespaced_uid"]

    def forged(mutate):
        payload = projection.to_payload()
        mutate(payload)
        return _projection_from_payload(payload)

    malformed = (
        (
            forged(
                lambda payload: payload.__setitem__(
                    "schema_version",
                    "llm-wiki-knowledge-projection/future",
                )
            ),
            "projection-schema-invalid",
        ),
        (
            forged(
                lambda payload: payload.__setitem__(
                    "source_knowledge_hash",
                    "sha256:ABC",
                )
            ),
            "projection-source-hash-invalid",
        ),
        (
            forged(
                lambda payload: payload["concepts"][first_path].__setitem__(
                    "canonical_path",
                    "modules/other.md",
                )
            ),
            "projection-coordinate-mismatch",
        ),
        (
            forged(
                lambda payload: payload["concepts"][first_path][
                    "identity"
                ].__setitem__("uid", "")
            ),
            "projection-uid-invalid",
        ),
        (
            forged(
                lambda payload: payload["concepts"][first_path][
                    "identity"
                ].__setitem__("namespaced_uid", "kb_other#concept")
            ),
            "projection-namespaced-uid-invalid",
        ),
        (
            forged(
                lambda payload: payload["concepts"][first_path][
                    "lifecycle"
                ].__setitem__(
                    "successor_namespaced_uid",
                    "kb_other#successor",
                )
            ),
            "projection-successor-invalid",
        ),
        (
            forged(
                lambda payload: payload["concepts"][first_path][
                    "lifecycle"
                ].__setitem__(
                    "successor_namespaced_uid",
                    namespaced_uid,
                )
            ),
            "projection-successor-self-reference",
        ),
        (
            forged(
                lambda payload: payload["concepts"][first_path][
                    "lifecycle"
                ].__setitem__(
                    "successor_namespaced_uid",
                    f"{bundle_id}#lw:entity:{'f' * 32}",
                )
            ),
            "projection-successor-absent",
        ),
    )
    for candidate, expected_code in malformed:
        with pytest.raises(KnowledgeProjectionError) as raised:
            validate_projection_summaries(candidate, paths)
        assert raised.value.code == expected_code

    with pytest.raises(KnowledgeProjectionError) as raised:
        validate_projection_summaries(projection, paths[:-1])
    assert raised.value.code == "projection-page-set-mismatch"


def test_projection_detaches_and_deeply_freezes_nested_payloads(tmp_path):
    projection = _governed_projection(tmp_path)
    payload = projection.to_payload()
    frozen = _projection_from_payload(payload)
    path = next(iter(frozen.concepts))
    before = serialize_knowledge_projection(frozen)

    payload["bundle"]["bundle_id"] = "kb_mutated"
    payload["concepts"][path]["identity"]["uid"] = "unknown"
    payload["concepts"][path]["review"]["items"].append(
        {"section_locator": "/private/review", "state": "valid", "reasons": []}
    )
    payload["warnings"].append("governance-not-available")

    assert serialize_knowledge_projection(frozen) == before
    with pytest.raises(TypeError):
        frozen.bundle["bundle_id"] = "kb_mutated"
    with pytest.raises(TypeError):
        frozen.concepts[path]["identity"]["uid"] = "unknown"
    with pytest.raises(AttributeError):
        frozen.concepts[path]["review"]["items"].append({})


def test_projection_boundaries_reject_nested_secret_path_and_shape_injection(
    tmp_path,
):
    projection = _governed_projection(tmp_path)
    paths = tuple(sorted(projection.concepts))
    source_path, target_path = paths[:2]

    def forged(mutate):
        payload = projection.to_payload()
        mutate(payload)
        return _projection_from_payload(payload)

    def inject_title(payload):
        payload["concepts"][source_path]["title"] = (
            "sk-projectionSecret1234567890"
        )

    def inject_review_path(payload):
        review = payload["concepts"][source_path]["review"]
        review.update(
            {
                "state": "has-valid-sections",
                "total": 1,
                "returned": 1,
                "valid_returned": 1,
                "truncated": False,
                "items": [
                    {
                        "section_locator": "/Users/alice/private/review",
                        "state": "valid",
                        "reasons": [],
                    }
                ],
            }
        )

    def inject_relationship_path(payload):
        target = payload["concepts"][target_path]
        relationships = payload["concepts"][source_path]["relationships"]
        relationships.update(
            {
                "availability": "ready",
                "total": 1,
                "returned": 1,
                "truncated": False,
                "items": [
                    {
                        "kind": "calls",
                        "direction": "outgoing",
                        "origin": "extracted",
                        "resolution": "resolved",
                        "target": {
                            "kind": "concept",
                            "present": True,
                            "canonical_path": target_path,
                            "title": "../../private/target",
                            "concept_kind": target["concept_kind"],
                            "namespaced_uid": target["identity"][
                                "namespaced_uid"
                            ],
                        },
                        "evidence": {
                            "state": "unknown",
                            "observed": 0,
                            "unique": 0,
                            "emitted": 0,
                            "omitted": 0,
                        },
                        "coverage": {
                            "observed": 0,
                            "emitted": 0,
                            "omitted": 0,
                            "limit": 0,
                            "truncated": False,
                        },
                    }
                ],
            }
        )

    def inject_unknown_nested_field(payload):
        payload["concepts"][source_path]["machine_check"][
            "credential"
        ] = "safe-looking-but-unapproved"

    for mutate in (
        inject_title,
        inject_review_path,
        inject_relationship_path,
        inject_unknown_nested_field,
    ):
        candidate = forged(mutate)
        with pytest.raises(KnowledgeProjectionError) as raised:
            validate_projection_summaries(candidate, paths)
        assert raised.value.code == "projection-shape-invalid"
        with pytest.raises(KnowledgeProjectionError):
            serialize_knowledge_projection(candidate)
        with pytest.raises(KnowledgeProjectionError):
            projection_concept_summary(candidate, source_path)


@pytest.mark.parametrize(
    ("availability", "reason", "expected_state"),
    [
        (
            MachineVerificationAvailability.NOT_EVALUATED,
            "verification-receipt-not-evaluated",
            "not-evaluated",
        ),
        (
            MachineVerificationAvailability.ABSENT,
            "verification-receipt-not-present",
            "not-run",
        ),
        (
            MachineVerificationAvailability.INVALID,
            "verification-receipt-invalid",
            "invalid",
        ),
    ],
)
def test_projection_preserves_closed_machine_receipt_states(
    tmp_path,
    availability,
    reason,
    expected_state,
):
    view = replace(
        _base_view(tmp_path),
        machine_verification=MachineVerificationReadView(
            availability=availability,
            reason=reason,
        ),
    )
    projection = project_knowledge(view)
    path = next(iter(projection.concepts))
    concept = projection.concepts[path]
    summary = projection_concept_summary(projection, path)

    assert concept["machine_check"]["state"] == expected_state
    assert summary["knowledge_machine_check"] == expected_state
    assert summary["knowledge_machine_check_reason"] == reason
    assert summary["knowledge_machine_check_result"] == "not-evaluated"
    assert summary["knowledge_freshness"] == "not-evaluated"
    assert concept["freshness"]["live_comparison_performed"] is False
