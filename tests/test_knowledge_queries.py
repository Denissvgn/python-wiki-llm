"""Pure documentation knowledge-query tests (KNOW-204)."""

from __future__ import annotations

import builtins
import io
import json
import socket
import subprocess
from dataclasses import replace
from pathlib import Path

import pytest

from llm_wiki_cli.services import documentation_queries
from llm_wiki_cli.services.documentation_queries import (
    DocumentationGraphQueryService,
    DocumentationQueryError,
)
from llm_wiki_cli.services.knowledge_artifacts import KNOWLEDGE_INDEX_FILENAME
from llm_wiki_cli.services.knowledge_consumption import (
    KnowledgeAvailability,
    KnowledgeReadReason,
    build_knowledge_read_view,
)
from llm_wiki_cli.services.knowledge_evidence import formatted_json_bytes
from llm_wiki_cli.services.knowledge_loader import (
    KnowledgeMismatchPolicy,
    load_knowledge_state,
)
from llm_wiki_cli.services.knowledge_governance import (
    ALIAS_LOCATOR,
    ALIAS_NATURAL_KEY,
    GovernanceActor,
    GovernanceLedger,
    add_alias,
    apply_governance_projection,
    concept_references_from_knowledge,
    reconcile_concepts,
    set_lifecycle,
)
from llm_wiki_cli.services.knowledge_model import Resolution, TargetClass
from llm_wiki_cli.services.sync_manifest import MANIFEST_FILENAME
from tests.knowledge_fixtures import fixture_hash
from tests.test_documentation_queries import _service
from tests.test_knowledge_freshness import _live_evaluation
from tests.test_knowledge_loader import _committed_state

USER_LOCATOR = "llm-wiki://entities/User"
MODULE_LOCATOR = "llm-wiki://modules/accounts"
SOURCE_PATH = "src/accounts.py"


def _ready_view(tmp_path, *, snapshot_only: bool = False, evaluate: bool = True):
    _committed_state(tmp_path)
    loaded = load_knowledge_state(tmp_path)
    assert loaded.knowledge is not None
    live = None if not evaluate else _live_evaluation(loaded.knowledge)
    return build_knowledge_read_view(
        loaded,
        live_evaluation=live,
        snapshot_only=snapshot_only,
    )


def _knowledge_service(view, *, limit: int = 20):
    return DocumentationGraphQueryService(
        {},
        limit=limit,
        knowledge_view=view,
    )


def _governed_view(tmp_path):
    view = _ready_view(tmp_path)
    assert view.knowledge is not None
    ledger = reconcile_concepts(
        GovernanceLedger.empty("query-fixture"),
        concept_references_from_knowledge(view.knowledge),
    )
    user_uid = next(
        uid
        for uid, allocation in ledger.concepts.items()
        if allocation.locator == USER_LOCATOR
    )
    successor_uid = next(
        uid
        for uid, allocation in ledger.concepts.items()
        if allocation.locator == "llm-wiki://entities/AccountService"
    )
    ledger = add_alias(
        ledger,
        user_uid,
        ALIAS_LOCATOR,
        "llm-wiki://entities/LegacyUser",
    )
    ledger = add_alias(
        ledger,
        user_uid,
        ALIAS_NATURAL_KEY,
        "code-entity:entities/LegacyUser.md",
    )
    ledger = set_lifecycle(
        ledger,
        user_uid,
        "active",
        actor=GovernanceActor("human", "reviewer.example"),
        authored_at="2026-07-27T10:00:00Z",
    )
    ledger = set_lifecycle(
        ledger,
        user_uid,
        "superseded",
        successor_uid=successor_uid,
        actor=GovernanceActor("human", "reviewer.example"),
        authored_at="2026-07-27T11:00:00Z",
    )
    return (
        replace(
            view,
            knowledge=apply_governance_projection(view.knowledge, ledger),
        ),
        user_uid,
        successor_uid,
    )


def _assert_compact(value) -> None:
    encoded = json.dumps(value, sort_keys=True)
    assert "sha256:" not in encoded
    assert '"basis"' not in encoded
    assert '"authorship"' not in encoded
    assert '"location"' not in encoded
    assert '"extensions"' not in encoded


def test_omitted_or_none_view_does_not_change_legacy_query_results():
    ordinary = _service()
    explicit_none = _service(knowledge_view=None)

    assert ordinary.flow_for_entrypoint("api-run") == explicit_none.flow_for_entrypoint(
        "api-run"
    )
    assert ordinary.callers("save") == explicit_none.callers("save")
    assert ordinary.callees("run") == explicit_none.callees("run")
    assert ordinary.dependency_neighborhood(
        "api.py"
    ) == explicit_none.dependency_neighborhood("api.py")
    assert ordinary.data_flow_for_entrypoint(
        "api-run"
    ) == explicit_none.data_flow_for_entrypoint("api-run")
    assert ordinary.pages_for_symbol("run") == explicit_none.pages_for_symbol("run")


def test_ready_concept_lookup_is_exact_compact_and_fresh(tmp_path):
    service = _knowledge_service(_ready_view(tmp_path))

    by_locator = service.get_concept(USER_LOCATOR)
    by_route = service.get_concept("entities/User.md")

    assert by_locator == by_route | {"query": USER_LOCATOR}
    assert by_locator["knowledge"] == {
        "availability": "ready",
        "reason": "all-projection-commitments-match",
        "freshness_evaluated": True,
    }
    assert by_locator["found"] is True
    assert by_locator["ambiguous"] is False
    assert by_locator["total"] == 1
    assert by_locator["returned"] == 1
    assert by_locator["truncated"] is False
    assert by_locator["bounds"] == {
        "matches": {"total": 1, "returned": 1, "truncated": False}
    }
    assert by_locator["concept"] == {
        "locator": USER_LOCATOR,
        "concept_kind": "code-entity",
        "title": "User",
        "page_kind": "entities",
        "page_id": "User",
        "canonical_path": "entities/User.md",
        "mcp_uri": USER_LOCATOR,
        "source_path": SOURCE_PATH,
        "role": "semantic",
        "origin": "extracted",
        "evidence": "present",
        "verification": "untracked",
        "lifecycle": "unknown",
        "freshness": {
            "state": "current",
            "reason": "recorded-basis-matches-live-evaluation",
            "live_comparison_performed": True,
        },
    }
    assert by_locator["matches"] == [by_locator["concept"]]
    _assert_compact(by_locator)
    json.dumps(by_locator, sort_keys=True)


def test_governed_concept_lookup_accepts_uid_alias_and_current_locator(tmp_path):
    view, user_uid, successor_uid = _governed_view(tmp_path)
    machine = {
        user_uid: {
            "availability": "recorded",
            "valid": True,
            "recorded_result": "passed",
        }
    }
    service = DocumentationGraphQueryService(
        {},
        knowledge_view=view,
        machine_verification=machine,
    )

    by_uid = service.get_concept(user_uid)
    by_alias = service.get_concept("llm-wiki://entities/LegacyUser")
    by_natural_alias = service.get_concept(
        "code-entity:entities/LegacyUser.md"
    )
    by_locator = service.get_concept(USER_LOCATOR)

    assert (
        by_uid["concept"]
        == by_alias["concept"]
        == by_natural_alias["concept"]
        == by_locator["concept"]
    )
    concept = by_uid["concept"]
    assert concept["uid"] == user_uid
    assert concept["lifecycle"] == "superseded"
    assert concept["successor_uid"] == successor_uid
    assert concept["aliases"] == [
        {"type": "locator", "value": "llm-wiki://entities/LegacyUser"},
        {
            "type": "natural-key",
            "value": "code-entity:entities/LegacyUser.md",
        },
    ]
    assert concept["alias_coverage"] == {
        "total": 2,
        "returned": 2,
        "truncated": False,
    }
    assert concept["lifecycle_events"] == {
        "items": [
            {
                "event_id": concept["lifecycle_events"]["items"][0]["event_id"],
                "from": "unknown",
                "to": "active",
                "actor": {"kind": "human", "id": "reviewer.example"},
                "authored_at": "2026-07-27T10:00:00Z",
                "reason": "explicit-lifecycle-change",
            },
            {
                "event_id": concept["lifecycle_events"]["items"][1]["event_id"],
                "from": "active",
                "to": "superseded",
                "actor": {"kind": "human", "id": "reviewer.example"},
                "authored_at": "2026-07-27T11:00:00Z",
                "reason": "explicit-lifecycle-change",
                "successor_uid": successor_uid,
            },
        ],
        "total": 2,
        "returned": 2,
        "limit": 20,
        "truncated": False,
    }

    bounded = DocumentationGraphQueryService(
        {},
        limit=1,
        knowledge_view=view,
    ).get_concept("code-entity:entities/LegacyUser.md")
    assert bounded["concept"]["aliases"] == [
        {"type": "locator", "value": "llm-wiki://entities/LegacyUser"}
    ]
    assert bounded["concept"]["alias_coverage"] == {
        "total": 2,
        "returned": 1,
        "truncated": True,
    }
    assert concept["reviews"] == {
        "items": [],
        "total": 0,
        "returned": 0,
        "limit": 20,
        "truncated": False,
    }
    assert concept["machine_verification"] == machine[user_uid]
    assert concept["verification"] == "untracked"

    traversal = service.traverse_typed_graph(
        user_uid,
        direction="outgoing",
        kinds=["supersedes"],
        origins=["governance"],
        resolutions=["resolved"],
    )
    assert traversal["total"] == 1
    assert traversal["edges"][0]["from"] == {
        "kind": "concept",
        "uid": user_uid,
    }
    assert traversal["edges"][0]["target"] == {
        "kind": "concept",
        "uid": successor_uid,
    }
    assert (
        traversal["edges"][0]["related_concept"]["uid"]
        == successor_uid
    )


@pytest.mark.parametrize(
    "query",
    [
        "User",
        "entities/user.md",
        "./entities/User.md",
        r"entities\User.md",
        f"{USER_LOCATOR}#details",
    ],
)
def test_concept_identity_does_not_fuzzy_match(tmp_path, query):
    result = _knowledge_service(_ready_view(tmp_path)).get_concept(query)

    assert result["knowledge"]["availability"] == "ready"
    assert result["found"] is False
    assert result["ambiguous"] is False
    assert result["matches"] == []
    assert result["concept"] is None
    assert result["total"] == 0
    assert result["returned"] == 0


def test_source_evidence_path_is_indexed_but_is_not_a_concept_identity(tmp_path):
    service = _knowledge_service(_ready_view(tmp_path))

    assert [
        concept["locator"] for concept in service.concepts_by_source_path[SOURCE_PATH]
    ] == [
        "llm-wiki://entities/AccountService",
        USER_LOCATOR,
        MODULE_LOCATOR,
    ]
    result = service.get_concept(SOURCE_PATH)

    assert result["found"] is False
    assert result["ambiguous"] is False
    assert result["total"] == 0
    assert result["returned"] == 0
    assert result["matches"] == []
    assert result["concept"] is None


def test_snapshot_only_and_evaluated_without_live_are_distinct(tmp_path):
    snapshot_root = tmp_path / "snapshot"
    snapshot_root.mkdir()
    snapshot = _knowledge_service(
        _ready_view(snapshot_root, snapshot_only=True)
    ).get_concept(USER_LOCATOR)

    evaluated_root = tmp_path / "evaluated"
    evaluated_root.mkdir()
    evaluated = _knowledge_service(
        _ready_view(evaluated_root, evaluate=False)
    ).get_concept(USER_LOCATOR)

    assert snapshot["knowledge"]["freshness_evaluated"] is False
    assert snapshot["concept"]["freshness"] == {
        "state": None,
        "reason": "not-evaluated",
        "live_comparison_performed": False,
    }
    assert evaluated["knowledge"]["freshness_evaluated"] is True
    assert evaluated["concept"]["freshness"] == {
        "state": "unknown",
        "reason": "live-evaluation-not-performed",
        "live_comparison_performed": False,
    }


def test_query_projects_every_live_freshness_outcome_and_reason(tmp_path):
    _committed_state(tmp_path)
    loaded = load_knowledge_state(tmp_path)
    assert loaded.knowledge is not None
    knowledge = loaded.knowledge
    changed_source_hash = fixture_hash("query:changed-source")
    changed_observation_hash = fixture_hash("query:changed-observation")
    changed_producer = replace(
        knowledge.bundle.producer,
        tool=replace(
            knowledge.bundle.producer.tool,
            version="2.0.0",
        ),
    )
    cases = (
        (
            _live_evaluation(
                knowledge,
                source_hash_by_path={SOURCE_PATH: changed_source_hash},
            ),
            "nonsemantic-source-change",
            "source-bytes-changed-concept-observation-unchanged",
        ),
        (
            _live_evaluation(
                knowledge,
                source_hash_by_path={SOURCE_PATH: changed_source_hash},
                observation_by_locator={
                    USER_LOCATOR: changed_observation_hash,
                },
            ),
            "source-changed",
            "concept-observation-changed",
        ),
        (
            _live_evaluation(
                knowledge,
                missing_source_paths=frozenset({SOURCE_PATH}),
            ),
            "source-missing",
            "reliably-mapped-source-missing",
        ),
        (
            _live_evaluation(
                knowledge,
                producer=changed_producer,
            ),
            "basis-incompatible",
            "producer-tool-version-changed",
        ),
    )

    for live, expected_state, expected_reason in cases:
        view = build_knowledge_read_view(loaded, live_evaluation=live)
        freshness = _knowledge_service(view).get_concept(USER_LOCATOR)["concept"][
            "freshness"
        ]
        assert freshness == {
            "state": expected_state,
            "reason": expected_reason,
            "live_comparison_performed": True,
        }

    ready = build_knowledge_read_view(
        loaded,
        live_evaluation=_live_evaluation(knowledge),
    )
    document = _knowledge_service(ready).get_concept("llm-wiki://index")
    assert document["concept"]["freshness"] == {
        "state": "unknown",
        "reason": "freshness-not-modeled",
        "live_comparison_performed": False,
    }


@pytest.mark.parametrize(
    ("state", "availability", "reason"),
    [
        (
            "absent",
            KnowledgeAvailability.ABSENT,
            KnowledgeReadReason.ABSENT,
        ),
        (
            "degraded",
            KnowledgeAvailability.DEGRADED,
            KnowledgeReadReason.DEGRADED_INVALID,
        ),
        (
            "unsupported",
            KnowledgeAvailability.UNSUPPORTED,
            KnowledgeReadReason.UNSUPPORTED_SCHEMA,
        ),
    ],
)
def test_loader_selected_non_ready_view_never_exposes_a_trustworthy_empty_graph(
    tmp_path,
    state,
    availability,
    reason,
):
    _committed_state(tmp_path)
    knowledge_path = tmp_path / KNOWLEDGE_INDEX_FILENAME
    if state == "absent":
        knowledge_path.unlink()
        (tmp_path / MANIFEST_FILENAME).unlink()
    elif state == "degraded":
        knowledge_path.write_bytes(b"{not-json\n")
    else:
        knowledge_path.write_bytes(
            formatted_json_bytes(
                {"schema_version": "llm-wiki-knowledge/v999"}
            )
        )
    loaded = load_knowledge_state(
        tmp_path,
        policy=KnowledgeMismatchPolicy.DEGRADED,
    )
    view = build_knowledge_read_view(loaded)
    service = _knowledge_service(view)

    concept = service.get_concept(USER_LOCATOR)
    related = service.related_concepts(USER_LOCATOR)
    explained = service.explain_evidence(USER_LOCATOR)

    assert concept["knowledge"] == {
        "availability": availability.value,
        "reason": reason.value,
        "freshness_evaluated": False,
    }
    assert concept["found"] is False
    assert concept["concept"] is None
    assert concept["bounds"] == {
        "matches": {"total": 0, "returned": 0, "truncated": False}
    }
    assert related["found"] is False
    assert related["relationships"] == []
    assert related["bounds"] == {
        "matches": {"total": 0, "returned": 0, "truncated": False},
        "relationships": {"total": 0, "returned": 0, "truncated": False},
    }
    assert explained["found"] is False
    assert explained["evidence"] is None
    assert explained["bounds"] == {
        "matches": {"total": 0, "returned": 0, "truncated": False},
        "evidence.relationships": {
            "total": 0,
            "returned": 0,
            "truncated": False,
        },
    }


def test_no_view_reports_absent_instead_of_claiming_an_empty_graph():
    result = DocumentationGraphQueryService({}).get_concept(USER_LOCATOR)

    assert result == {
        "knowledge": {
            "availability": "absent",
            "reason": "knowledge-projection-not-present",
            "freshness_evaluated": False,
        },
        "query": USER_LOCATOR,
        "found": False,
        "ambiguous": False,
        "matches": [],
        "total": 0,
        "returned": 0,
        "truncated": False,
        "bounds": {"matches": {"total": 0, "returned": 0, "truncated": False}},
        "concept": None,
    }


def test_related_concepts_preserves_phase_one_target_states(tmp_path):
    service = _knowledge_service(_ready_view(tmp_path))

    result = service.related_concepts(
        MODULE_LOCATOR,
        direction="outbound",
    )

    assert result["found"] is True
    assert result["direction"] == "outbound"
    assert result["kinds"] == ["derived_from", "links_to"]
    assert result["total"] == 8
    assert result["returned"] == 8
    assert result["truncated"] is False
    assert result["bounds"] == {
        "matches": {"total": 1, "returned": 1, "truncated": False},
        "relationships": {"total": 8, "returned": 8, "truncated": False},
    }
    assert [item["kind"] for item in result["relationships"]].count(
        "derived_from"
    ) == 1
    assert [item["kind"] for item in result["relationships"]].count("links_to") == 7
    assert [item["locator"] for item in result["related_concepts"]] == [
        USER_LOCATOR
    ]
    assert {
        item["target"]["target_class"] for item in result["external_targets"]
    } == {"external", "mail"}
    assert {
        item["target"]["target_class"] for item in result["unresolved_targets"]
    } == {"concept", "malformed"}
    derived = next(
        item for item in result["relationships"] if item["kind"] == "derived_from"
    )
    assert derived["target"] == {
        "target_class": "source",
        "source_path": SOURCE_PATH,
    }
    assert derived["related_concept"] is None
    resolved = next(
        item
        for item in result["relationships"]
        if item["target"].get("canonical_path") == "entities/User.md"
    )
    assert resolved["kind"] == "links_to"
    assert resolved["resolution"] == "resolved"
    assert resolved["related_concept"]["locator"] == USER_LOCATOR
    assert resolved["target"] == {
        "target_class": "concept",
        "canonical_path": "entities/User.md",
    }
    assert {
        item["target"]["external_uri"]
        for item in result["relationships"]
        if item["resolution"] == "external"
    } == {
        "https://example.invalid/reference",
        "mailto:support@example.invalid",
    }
    anchor = next(
        item
        for item in result["relationships"]
        if item["target"]["target_class"] == "anchor"
    )
    asset = next(
        item
        for item in result["relationships"]
        if item["target"]["target_class"] == "asset"
    )
    malformed = next(
        item
        for item in result["relationships"]
        if item["target"]["target_class"] == "malformed"
    )
    unresolved = next(
        item
        for item in result["relationships"]
        if item["resolution"] == "unresolved"
        and item["target"]["target_class"] == "concept"
    )
    assert anchor["target"]["normalized_target"] == "#usage"
    assert asset["target"]["normalized_target"] == "../assets/account-flow.svg"
    assert malformed["target"]["raw_target"] == ""
    assert malformed["target"]["normalized_target"] == ""
    assert unresolved["target"]["raw_target"] == r"..\entities\Missing.md"
    assert unresolved["target"]["normalized_target"] == r"..\entities\Missing.md"
    assert all("label" not in item["target"] for item in result["relationships"])
    _assert_compact(result)
    json.dumps(result, sort_keys=True)


def test_related_direction_and_kind_filters_use_observed_edges_only(tmp_path):
    service = _knowledge_service(_ready_view(tmp_path))

    incoming = service.related_concepts(
        USER_LOCATOR,
        direction="inbound",
        kinds=["links_to"],
    )
    outgoing = service.related_concepts(
        USER_LOCATOR,
        direction="outbound",
        kinds=["derived_from"],
    )
    both = service.related_concepts(USER_LOCATOR)

    assert incoming["total"] == 1
    assert incoming["relationships"][0]["from"] == MODULE_LOCATOR
    assert incoming["relationships"][0]["related_concept"]["locator"] == (
        MODULE_LOCATOR
    )
    assert outgoing["total"] == 1
    assert outgoing["relationships"][0]["target"]["source_path"] == SOURCE_PATH
    assert both["total"] == 2
    assert {item["direction"] for item in both["relationships"]} == {
        "inbound",
        "outbound",
    }


def test_related_filters_before_bounding_and_discloses_counts(tmp_path):
    service = _knowledge_service(_ready_view(tmp_path), limit=2)

    result = service.related_concepts(MODULE_LOCATOR, direction="outbound")

    assert result["total"] == 8
    assert result["returned"] == 2
    assert result["truncated"] is True
    assert len(result["relationships"]) == 2
    assert result["bounds"]["relationships"] == {
        "total": 8,
        "returned": 2,
        "truncated": True,
    }
    assert len(result["related_concepts"]) <= 2
    assert len(result["unresolved_targets"]) <= 2
    assert len(result["external_targets"]) <= 2

    filtered = service.related_concepts(
        MODULE_LOCATOR,
        direction="outbound",
        kinds=["derived_from"],
    )
    assert filtered["total"] == 1
    assert filtered["returned"] == 1
    assert filtered["truncated"] is False

    explained = service.explain_evidence(MODULE_LOCATOR)
    assert explained["total"] == 8
    assert explained["returned"] == 2
    assert explained["truncated"] is True
    assert len(explained["evidence"]["relationships"]) == 2
    assert explained["bounds"] == {
        "matches": {"total": 1, "returned": 1, "truncated": False},
        "evidence.relationships": {
            "total": 8,
            "returned": 2,
            "truncated": True,
        },
    }


@pytest.mark.parametrize("direction", ["", "incoming", "out", None, 3])
def test_invalid_related_direction_is_rejected(direction):
    with pytest.raises(DocumentationQueryError, match="direction"):
        DocumentationGraphQueryService({}).related_concepts(
            USER_LOCATOR,
            direction=direction,  # type: ignore[arg-type]
        )


@pytest.mark.parametrize(
    "kinds",
    [
        "links_to",
        b"links_to",
        {"links_to": True},
        ["inferred_from"],
        ["links_to", 3],
        3,
    ],
)
def test_invalid_related_kinds_are_rejected(kinds):
    with pytest.raises(DocumentationQueryError, match="kind"):
        DocumentationGraphQueryService({}).related_concepts(
            USER_LOCATOR,
            kinds=kinds,  # type: ignore[arg-type]
        )


@pytest.mark.parametrize("query", ["", "   ", None, 3])
def test_invalid_knowledge_identity_is_rejected(query):
    service = DocumentationGraphQueryService({})
    with pytest.raises(DocumentationQueryError, match="locator_or_exact_route"):
        service.get_concept(query)
    with pytest.raises(DocumentationQueryError, match="locator_or_exact_route"):
        service.related_concepts(query)
    with pytest.raises(DocumentationQueryError, match="locator_or_exact_route"):
        service.explain_evidence(query)


def test_explain_evidence_is_the_only_detailed_evidence_surface(tmp_path):
    service = _knowledge_service(_ready_view(tmp_path))

    compact = service.get_concept(USER_LOCATOR)
    related = service.related_concepts(USER_LOCATOR)
    explained = service.explain_evidence(USER_LOCATOR)

    _assert_compact(compact)
    _assert_compact(related)
    assert explained["found"] is True
    assert explained["total"] == 2
    assert explained["returned"] == 2
    structure = explained["evidence"]["structure"]
    semantics = explained["evidence"]["semantics"]
    freshness = explained["evidence"]["freshness"]
    assert structure["basis"]["source_content_hash"].startswith("sha256:")
    assert structure["basis"]["concept_observation_hash"].startswith("sha256:")
    assert semantics["page_hash"].startswith("sha256:")
    assert freshness["state"] == "current"
    assert freshness["reason"] == "recorded-basis-matches-live-evaluation"
    assert freshness["recorded_basis"]["source_content_hash"].startswith("sha256:")
    assert freshness["live_basis"]["source_content_hash"].startswith("sha256:")
    relationships = explained["evidence"]["relationships"]
    derived = next(
        relationship
        for relationship in relationships
        if relationship["kind"] == "derived_from"
    )
    link = next(
        relationship
        for relationship in relationships
        if relationship["kind"] == "links_to"
    )
    assert derived["evidence"]["concept_observation_hash"].startswith("sha256:")
    assert link["evidence"]["page_hash"].startswith("sha256:")
    assert link["target"]["label"] == "User"
    assert link["target"]["location"]["start"] >= 0
    assert link["target"]["location"]["end"] > link["target"]["location"]["start"]
    assert all(
        relationship["evidence"] == {"state": "present"}
        for relationship in related["relationships"]
    )
    json.dumps(explained, sort_keys=True)


def test_duplicate_self_links_remain_distinct_but_are_not_double_counted(
    tmp_path,
):
    view = _ready_view(tmp_path)
    assert view.knowledge is not None
    resolved_link = next(
        relationship
        for relationship in view.knowledge.relationships
        if getattr(relationship.kind, "value", relationship.kind) == "links_to"
        and relationship.resolution.value == "resolved"
        and relationship.target.canonical_path == "entities/User.md"
    )
    self_link = replace(resolved_link, source_locator=USER_LOCATOR)
    duplicated = replace(
        view,
        knowledge=replace(
            view.knowledge,
            relationships=(self_link, self_link),
        ),
    )

    result = _knowledge_service(duplicated).related_concepts(USER_LOCATOR)

    assert result["total"] == 2
    assert result["returned"] == 2
    assert [item["direction"] for item in result["relationships"]] == [
        "both",
        "both",
    ]
    assert all(
        item["related_concept"]["locator"] == USER_LOCATOR
        for item in result["relationships"]
    )


def test_open_relationship_kinds_are_not_traversed_in_phase_one(tmp_path):
    view = _ready_view(tmp_path)
    assert view.knowledge is not None
    resolved_link = next(
        relationship
        for relationship in view.knowledge.relationships
        if getattr(relationship.kind, "value", relationship.kind) == "links_to"
        and relationship.resolution.value == "resolved"
        and relationship.target.canonical_path == "entities/User.md"
    )
    future_relationship = replace(
        resolved_link,
        kind="example.invalid/semantic-link",
    )
    future_view = replace(
        view,
        knowledge=replace(
            view.knowledge,
            relationships=(future_relationship,),
        ),
    )
    service = _knowledge_service(future_view)

    related = service.related_concepts(MODULE_LOCATOR)
    explained = service.explain_evidence(MODULE_LOCATOR)

    assert related["total"] == 0
    assert related["relationships"] == []
    assert explained["total"] == 0
    assert explained["evidence"]["relationships"] == []


def test_resolved_endpoint_is_adjacent_even_when_target_class_is_unknown(
    tmp_path,
):
    view = _ready_view(tmp_path)
    assert view.knowledge is not None
    resolved_link = next(
        relationship
        for relationship in view.knowledge.relationships
        if getattr(relationship.kind, "value", relationship.kind) == "links_to"
        and relationship.resolution.value == "resolved"
        and relationship.target.canonical_path == "entities/User.md"
    )
    unknown_class_link = replace(
        resolved_link,
        target=replace(
            resolved_link.target,
            target_class=TargetClass.UNKNOWN,
        ),
    )
    unknown_class_view = replace(
        view,
        knowledge=replace(
            view.knowledge,
            relationships=(unknown_class_link,),
        ),
    )

    result = _knowledge_service(unknown_class_view).related_concepts(
        USER_LOCATOR,
        direction="inbound",
    )

    assert result["total"] == 1
    assert result["relationships"][0]["related_concept"]["locator"] == MODULE_LOCATOR
    assert result["relationships"][0]["target"] == {
        "target_class": "unknown",
        "canonical_path": "entities/User.md",
    }


def test_resolved_locator_endpoint_builds_inbound_adjacency(tmp_path):
    view = _ready_view(tmp_path)
    assert view.knowledge is not None
    resolved_link = next(
        relationship
        for relationship in view.knowledge.relationships
        if getattr(relationship.kind, "value", relationship.kind) == "links_to"
        and relationship.resolution is Resolution.RESOLVED
        and relationship.target.canonical_path == "entities/User.md"
    )
    locator_link = replace(
        resolved_link,
        target=replace(
            resolved_link.target,
            locator=USER_LOCATOR,
            canonical_path=None,
        ),
    )
    locator_view = replace(
        view,
        knowledge=replace(
            view.knowledge,
            relationships=(locator_link,),
        ),
    )

    result = _knowledge_service(locator_view).related_concepts(
        USER_LOCATOR,
        direction="inbound",
    )

    assert result["total"] == 1
    assert result["relationships"][0]["target"] == {
        "target_class": "concept",
        "locator": USER_LOCATOR,
    }
    assert result["relationships"][0]["related_concept"]["locator"] == MODULE_LOCATOR


def test_ambiguous_markdown_target_remains_an_observation_not_a_concept_edge(
    tmp_path,
):
    view = _ready_view(tmp_path)
    assert view.knowledge is not None
    unresolved = next(
        relationship
        for relationship in view.knowledge.relationships
        if getattr(relationship.kind, "value", relationship.kind) == "links_to"
        and relationship.resolution is Resolution.UNRESOLVED
        and relationship.target.target_class is TargetClass.CONCEPT
    )
    ambiguous = replace(unresolved, resolution=Resolution.AMBIGUOUS)
    ambiguous_view = replace(
        view,
        knowledge=replace(
            view.knowledge,
            relationships=(ambiguous,),
        ),
    )

    result = _knowledge_service(ambiguous_view).related_concepts(
        MODULE_LOCATOR,
        direction="outbound",
    )

    assert result["total"] == 1
    assert result["related_concepts"] == []
    assert result["relationships"][0]["resolution"] == "ambiguous"
    assert result["relationships"][0]["related_concept"] is None
    assert result["unresolved_targets"] == [
        {
            "kind": "links_to",
            "resolution": "ambiguous",
            "target": {
                "target_class": "concept",
                "raw_target": unresolved.target.raw_target,
                "normalized_target": unresolved.target.normalized_target,
            },
        }
    ]


def test_shuffled_knowledge_input_produces_identical_query_json(tmp_path):
    view = _ready_view(tmp_path)
    assert view.knowledge is not None
    shuffled = replace(
        view,
        knowledge=replace(
            view.knowledge,
            concepts=tuple(reversed(view.knowledge.concepts)),
            relationships=tuple(reversed(view.knowledge.relationships)),
        ),
    )
    first = _knowledge_service(view)
    second = _knowledge_service(shuffled)

    for method_name, query in (
        ("get_concept", USER_LOCATOR),
        ("related_concepts", MODULE_LOCATOR),
        ("explain_evidence", USER_LOCATOR),
    ):
        first_result = getattr(first, method_name)(query)
        second_result = getattr(second, method_name)(query)
        assert json.dumps(first_result, sort_keys=True) == json.dumps(
            second_result,
            sort_keys=True,
        )


def test_knowledge_is_normalized_and_indexed_only_during_construction(
    tmp_path,
    monkeypatch,
):
    view = _ready_view(tmp_path)
    calls = []
    real_normalizer = documentation_queries.knowledge_index_to_payload

    def recording_normalizer(knowledge):
        calls.append(knowledge)
        return real_normalizer(knowledge)

    monkeypatch.setattr(
        documentation_queries,
        "knowledge_index_to_payload",
        recording_normalizer,
    )
    service = _knowledge_service(view)
    assert len(calls) == 1

    class NoIterationDict(dict):
        def __iter__(self):
            raise AssertionError("query attempted a full index scan")

        def items(self):
            raise AssertionError("query attempted a full index scan")

        def values(self):
            raise AssertionError("query attempted a full index scan")

    service.concept_by_locator = NoIterationDict(service.concept_by_locator)
    service.concept_by_mcp_uri = NoIterationDict(service.concept_by_mcp_uri)
    service.concept_by_canonical_path = NoIterationDict(
        service.concept_by_canonical_path
    )
    service.outbound_relationships = NoIterationDict(
        service.outbound_relationships
    )
    service.inbound_relationships = NoIterationDict(service.inbound_relationships)

    for _ in range(2):
        assert service.get_concept(USER_LOCATOR)["found"] is True
        assert service.related_concepts(USER_LOCATOR)["total"] == 2
        assert service.explain_evidence(USER_LOCATOR)["total"] == 2
    assert len(calls) == 1


def test_service_and_knowledge_queries_perform_no_io_or_external_work(
    tmp_path,
    monkeypatch,
):
    view = _ready_view(tmp_path)

    def fail(*_args, **_kwargs):
        raise AssertionError("pure query service attempted external work")

    monkeypatch.setattr(builtins, "open", fail)
    monkeypatch.setattr(io, "open", fail)
    monkeypatch.setattr(Path, "open", fail)
    monkeypatch.setattr(Path, "read_text", fail)
    monkeypatch.setattr(Path, "read_bytes", fail)
    monkeypatch.setattr(Path, "write_text", fail)
    monkeypatch.setattr(Path, "write_bytes", fail)
    monkeypatch.setattr(socket, "socket", fail)
    monkeypatch.setattr(subprocess, "run", fail)
    monkeypatch.setattr(subprocess, "Popen", fail)

    service = _knowledge_service(view)
    assert service.get_concept(USER_LOCATOR)["found"] is True
    assert service.related_concepts(USER_LOCATOR)["total"] == 2
    assert service.explain_evidence(USER_LOCATOR)["evidence"] is not None


def test_constructor_rejects_unvalidated_knowledge_input():
    with pytest.raises(DocumentationQueryError, match="knowledge_view"):
        DocumentationGraphQueryService(
            {},
            knowledge_view={"knowledge": "raw"},  # type: ignore[arg-type]
        )
