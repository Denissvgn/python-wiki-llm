"""Cold snapshot requests reuse validation without retaining authority across reads."""

from __future__ import annotations

from collections import Counter
from copy import deepcopy
from dataclasses import replace
import json

import pytest

from llm_wiki_cli import api
from llm_wiki_cli.services import (
    documentation_query_builder,
    knowledge_graph,
    knowledge_index,
    knowledge_model,
    verification_contracts,
)
from llm_wiki_cli.services.contracts import (
    SECTION_OWNERSHIP_EXTENSION_KEY,
    TYPED_GRAPH_EXTENSION_KEY,
)
from llm_wiki_cli.services.documentation_queries import (
    DocumentationGraphQueryService,
    DocumentationQueryError,
)
from llm_wiki_cli.services.knowledge_artifacts import (
    KNOWLEDGE_INDEX_FILENAME,
    build_knowledge_commit_plan,
    commit_knowledge_artifacts,
    require_validated_artifacts,
)
from llm_wiki_cli.services.knowledge_consumption import load_knowledge_read_view
from llm_wiki_cli.services.knowledge_evidence import formatted_json_bytes, sha256_bytes
from llm_wiki_cli.services.knowledge_governance import (
    GOVERNANCE_FILENAME,
    GovernanceActor,
    GovernanceError,
    GovernanceLedger,
    add_alias,
    add_review_event,
    apply_governance_projection,
    concept_references_from_knowledge,
    current_review_evidence,
    reconcile_concepts,
    save_governance,
    set_lifecycle,
    validate_governance_projection,
)
from llm_wiki_cli.services.knowledge_generation import build_knowledge_generation_plan
from llm_wiki_cli.services.knowledge_loader import load_knowledge_state
from llm_wiki_cli.services.knowledge_packs import open_knowledge_store
from llm_wiki_cli.services.knowledge_storage import KnowledgeStorageError
from llm_wiki_cli.services.knowledge_storage_access import capture_knowledge_slice
from llm_wiki_cli.services.sync_manifest import MANIFEST_FILENAME
from llm_wiki_cli.services.verification_contracts import (
    ARTIFACT_INTEGRITY_CHECKER_ID,
    VerificationContractError,
    build_artifact_verification_context,
    verify_and_write_receipt,
)
from tests.test_knowledge_loader import _committed_knowledge_state
from tests.knowledge_fixtures import one_module_two_entities_fixture
from tests.test_knowledge_generation import _planner_inputs
from tests.test_knowledge_loader import _write_fixture_pages
from tests.test_knowledge_verification_view import _context


STORAGE_FORMATS = (
    "v1",
    "sharded-v2",
    "packed-v3",
    "packed-v3-deflate",
    "packed-v4",
    "packed-v4-deflate",
)
MODULE_LOCATOR = "llm-wiki://modules/accounts"


def _committed_snapshot(root, storage_format, *, governed=False):
    root.mkdir(parents=True, exist_ok=True)
    plan, _ = _committed_knowledge_state(root)
    if governed:
        loaded = load_knowledge_state(root)
        assert loaded.knowledge is not None
        ledger = reconcile_concepts(
            GovernanceLedger.empty("kb_snapshot_validation"),
            concept_references_from_knowledge(loaded.knowledge),
        )
        save_governance(root, ledger)
        plan = build_knowledge_commit_plan(
            root,
            surface_index_bytes=plan.surface_index.content,
            knowledge_index=apply_governance_projection(loaded.knowledge, ledger),
            manifest=plan.committed_manifest.without_artifact_hashes(),
        )
        commit_knowledge_artifacts(plan)
    if storage_format != "v1":
        plan = build_knowledge_commit_plan(
            root,
            surface_index_bytes=plan.surface_index.content,
            knowledge_index_bytes=plan.knowledge_index.content,
            manifest=plan.committed_manifest.without_artifact_hashes(),
            knowledge_format=storage_format,
        )
        commit_knowledge_artifacts(plan)
    return plan


def _count_validation(monkeypatch):
    calls = Counter()
    original_parser = knowledge_model.parse_knowledge_index
    original_graph = knowledge_graph.validate_typed_graph

    def parse(payload):
        # Envelope commitment validation also validates a standalone bundle
        # through an empty model. It never traverses concepts or graph data.
        calls["model" if payload.get("concepts") else "bundle"] += 1
        return original_parser(payload)

    def graph(payload, **kwargs):
        calls["graph"] += 1
        return original_graph(payload, **kwargs)

    monkeypatch.setattr(knowledge_model, "parse_knowledge_index", parse)
    monkeypatch.setattr(knowledge_index, "parse_knowledge_index", parse)
    monkeypatch.setattr(verification_contracts, "parse_knowledge_index", parse)
    monkeypatch.setattr(knowledge_graph, "validate_typed_graph", graph)
    return calls


@pytest.mark.parametrize("storage_format", STORAGE_FORMATS)
@pytest.mark.parametrize("governed", (False, True))
def test_cold_exact_snapshot_request_validates_model_and_graph_once(
    tmp_path, monkeypatch, storage_format, governed
):
    _committed_snapshot(tmp_path, storage_format, governed=governed)
    monkeypatch.chdir(tmp_path)
    calls = _count_validation(monkeypatch)
    monkeypatch.setattr(
        api,
        "build_documentation_query_service",
        lambda *args, **kwargs: pytest.fail("snapshot query extracted source"),
    )

    result = api.query_documentation(
        {"operation": "concept", "value": MODULE_LOCATOR, "limit": 5},
        wiki_dir=".",
    )

    assert result["found"] is True
    concept = result.get("concept")
    assert isinstance(concept, dict) and concept["locator"] == MODULE_LOCATOR
    assert result["cost"] == {
        "full_inventory_performed": False,
        "scope": "snapshot-index-only",
        "supplied_paths": 0,
    }
    assert calls == {"model": 1, "bundle": 1, "graph": 1}


@pytest.mark.parametrize("storage_format", STORAGE_FORMATS)
def test_reused_payload_matches_fully_revalidated_query_results(
    tmp_path, storage_format
):
    _committed_snapshot(tmp_path, storage_format)
    view = load_knowledge_read_view(tmp_path, snapshot_only=True)
    reused = DocumentationGraphQueryService({}, knowledge_view=view)
    revalidated = DocumentationGraphQueryService(
        {}, knowledge_view=replace(view, validated_artifacts=None)
    )

    for method, options in (
        ("get_concept", {}),
        ("related_concepts", {}),
        ("traverse_typed_graph", {"include_evidence": True}),
        ("list_concept_sections", {}),
        ("explain_evidence", {}),
    ):
        actual = getattr(reused, method)(MODULE_LOCATOR, **options)
        expected = getattr(revalidated, method)(MODULE_LOCATOR, **options)
        assert json.dumps(actual, sort_keys=True) == json.dumps(
            expected, sort_keys=True
        )


def test_query_indexes_share_immutable_validator_payload_and_detach_responses(tmp_path):
    _committed_snapshot(tmp_path, "v1")
    view = load_knowledge_read_view(tmp_path, snapshot_only=True)
    artifacts = require_validated_artifacts(view.validated_artifacts)
    service = DocumentationGraphQueryService({}, knowledge_view=view)
    payload = artifacts.knowledge_payload
    concept = next(c for c in payload["concepts"] if c["locator"] == MODULE_LOCATOR)
    graph = payload["extensions"][TYPED_GRAPH_EXTENSION_KEY]

    assert service.concept_by_locator[MODULE_LOCATOR] is concept
    assert service._knowledge_relationships[0] is payload["relationships"][0]
    assert service._typed_graph_edges[0] is graph["edges"][0]
    assert graph is artifacts.knowledge.extensions[TYPED_GRAPH_EXTENSION_KEY]
    with pytest.raises(TypeError, match="immutable"):
        concept["title"] = "Changed"
    with pytest.raises(TypeError, match="immutable"):
        graph["edges"][0]["evidence"]["samples"].clear()
    with pytest.raises(TypeError, match="issued"):
        require_validated_artifacts(replace(artifacts, knowledge_payload={}))

    expected = service.traverse_typed_graph(MODULE_LOCATOR, include_evidence=True)
    changed = service.traverse_typed_graph(MODULE_LOCATOR, include_evidence=True)
    assert changed["edges"]
    changed["edges"][0]["evidence"]["samples"].clear()
    changed["edges"].clear()
    assert (
        service.traverse_typed_graph(MODULE_LOCATOR, include_evidence=True) == expected
    )


@pytest.mark.parametrize(
    "alter",
    ("model", "surface", "marker", "missing-proof", "replaced-proof", "foreign-proof"),
)
def test_unbound_read_view_uses_full_validation(tmp_path, monkeypatch, alter):
    _committed_snapshot(tmp_path, "v1")
    view = load_knowledge_read_view(tmp_path, snapshot_only=True)
    assert view.knowledge is not None and view.manifest_basis is not None
    if alter == "model":
        view = replace(view, knowledge=replace(view.knowledge))
    elif alter == "surface":
        view = replace(view, surface=deepcopy(view.surface))
    elif alter == "marker":
        marker = view.manifest_basis.artifact_hashes
        assert marker is not None
        view = replace(
            view,
            manifest_basis=replace(
                view.manifest_basis,
                artifact_hashes=replace(
                    marker, knowledge_index_hash=sha256_bytes(b"other")
                ),
            ),
        )
    elif alter == "missing-proof":
        view = replace(view, validated_artifacts=None)
    elif alter == "replaced-proof":
        view = replace(view, validated_artifacts=replace(view.validated_artifacts))
    else:
        _committed_snapshot(tmp_path / "other", "v1")
        foreign = load_knowledge_read_view(tmp_path / "other", snapshot_only=True)
        view = replace(view, validated_artifacts=foreign.validated_artifacts)

    calls = _count_validation(monkeypatch)
    service = DocumentationGraphQueryService({}, knowledge_view=view)
    assert service.get_concept(MODULE_LOCATOR)["found"] is True
    assert calls == {"model": 1, "graph": 2}


def test_replaced_invalid_model_is_never_trusted(tmp_path):
    _committed_snapshot(tmp_path, "v1")
    view = load_knowledge_read_view(tmp_path, snapshot_only=True)
    assert view.knowledge is not None
    changed = replace(view, knowledge=replace(view.knowledge, schema_version="invalid"))
    with pytest.raises(DocumentationQueryError, match="knowledge.*invalid"):
        DocumentationGraphQueryService({}, knowledge_view=changed)


def test_separate_snapshot_requests_validate_again_and_observe_corruption(
    tmp_path, monkeypatch
):
    _committed_snapshot(tmp_path, "v1")
    monkeypatch.chdir(tmp_path)
    calls = _count_validation(monkeypatch)
    request = {"operation": "concept", "value": MODULE_LOCATOR}
    first = api.query_documentation(request, wiki_dir=".")
    assert first["found"] is True
    assert api.query_documentation(request, wiki_dir=".") == first
    assert calls == {"model": 2, "bundle": 2, "graph": 2}

    (tmp_path / KNOWLEDGE_INDEX_FILENAME).write_bytes(b"{}\n")
    result = api.query_documentation(request, wiki_dir=".")
    assert result["found"] is False
    knowledge = result.get("knowledge")
    assert isinstance(knowledge, dict) and knowledge["availability"] == "degraded"


@pytest.mark.parametrize(
    "target", ("modules/accounts.md", MANIFEST_FILENAME, KNOWLEDGE_INDEX_FILENAME)
)
def test_snapshot_assembly_retains_final_mutation_check(tmp_path, monkeypatch, target):
    _committed_snapshot(tmp_path, "v1")
    monkeypatch.chdir(tmp_path)
    original = documentation_query_builder.assemble_documentation_query_service

    def changed(**options):
        service = original(**options)
        path = tmp_path / target
        path.write_bytes(path.read_bytes() + b"\n")
        return service

    monkeypatch.setattr(
        documentation_query_builder, "assemble_documentation_query_service", changed
    )
    with pytest.raises(api.WorkspaceStateError) as caught:
        api.query_documentation(
            {"operation": "concept", "value": MODULE_LOCATOR}, wiki_dir="."
        )
    assert caught.value.code == "context-read-mutated"


@pytest.mark.parametrize("corruption", ("endpoint", "sample", "direction", "coverage"))
def test_reused_graph_keeps_intrinsic_and_enclosing_snapshot_validation(
    tmp_path, monkeypatch, corruption
):
    plan = _committed_snapshot(tmp_path, "v1")
    monkeypatch.chdir(tmp_path)
    payload = json.loads(plan.knowledge_index.content)
    graph = payload["extensions"][TYPED_GRAPH_EXTENSION_KEY]
    edge = next(e for e in graph["edges"] if e["kind"] == "contains")
    if corruption == "endpoint":
        edge["target"] = {"kind": "concept", "locator": "llm-wiki://entities/foreign"}
    elif corruption == "sample":
        edge["evidence"]["samples"][0]["target"] = {
            "kind": "concept",
            "locator": "llm-wiki://entities/foreign",
        }
    elif corruption == "direction":
        edge["target"] = {"kind": "concept", "locator": MODULE_LOCATOR}
    else:
        edge["coverage"]["omitted"] += 1
    edge["key"] = knowledge_graph.relationship_edge_key(edge)
    graph["edges"].sort(key=lambda item: item["key"])
    if corruption != "coverage":
        # These are intrinsically valid graphs with invalid snapshot bindings.
        knowledge_model.parse_knowledge_index(payload)
    content = formatted_json_bytes(payload)
    (tmp_path / KNOWLEDGE_INDEX_FILENAME).write_bytes(content)
    marker = plan.committed_manifest.artifact_hashes
    assert marker is not None
    replace(
        plan.committed_manifest,
        artifact_hashes=replace(
            marker,
            knowledge_index_hash=sha256_bytes(content),
        ),
    ).save(tmp_path)

    result = api.query_documentation(
        {"operation": "concept", "value": MODULE_LOCATOR}, wiki_dir="."
    )
    assert result["found"] is False
    knowledge = result.get("knowledge")
    assert isinstance(knowledge, dict) and knowledge["availability"] == "degraded"


def _history_snapshot(root, storage_format="v1"):
    fixture = one_module_two_entities_fixture()
    fixture = replace(
        fixture,
        pages=tuple(
            replace(
                page, content=page.content + "\n## Description\nReviewed meaning.\n"
            )
            if page.canonical_path == "modules/accounts.md"
            else page
            for page in fixture.pages
        ),
    )
    _write_fixture_pages(root, fixture)
    plan = build_knowledge_generation_plan(_planner_inputs(root, fixture))
    knowledge = knowledge_model.parse_knowledge_index(
        json.loads(plan.knowledge_index.content)
    )
    ledger = reconcile_concepts(
        GovernanceLedger.empty("kb_snapshot_history"),
        concept_references_from_knowledge(knowledge),
    )
    uids = {value.locator: uid for uid, value in ledger.concepts.items()}
    actor = GovernanceActor("human", "fixture-reviewer")
    uid = uids["llm-wiki://entities/User"]
    ledger = add_alias(ledger, uid, "locator", "llm-wiki://entities/LegacyUser")
    ledger = set_lifecycle(
        ledger, uid, "active", actor=actor, authored_at="2026-10-28T10:00:00Z"
    )
    ledger = set_lifecycle(
        ledger,
        uid,
        "superseded",
        actor=actor,
        authored_at="2026-10-28T10:01:00Z",
        successor_uid=uids["llm-wiki://entities/AccountService"],
        reason="explicit-successor",
    )
    page = next(
        p
        for p in knowledge.extensions[SECTION_OWNERSHIP_EXTENSION_KEY]["pages"]
        if p["page_locator"] == MODULE_LOCATOR
    )
    section = next(s for s in page["sections"] if s.get("semantic_hash") is not None)
    concept = next(c for c in knowledge.concepts if c.locator == MODULE_LOCATOR)
    evidence = current_review_evidence(concept)
    assert evidence is not None
    ledger = add_review_event(
        ledger,
        uids[MODULE_LOCATOR],
        section_locator=section["locator"],
        scope_hash=section["semantic_hash"],
        evidence=evidence,
        reviewer=actor,
        method="manual-review",
        method_version="1",
        authored_at="2026-10-28T10:02:00Z",
    )
    save_governance(root, ledger)
    plan = build_knowledge_commit_plan(
        root,
        surface_index_bytes=plan.surface_index.content,
        knowledge_index=apply_governance_projection(knowledge, ledger, event_limit=1),
        manifest=plan.committed_manifest.without_artifact_hashes(),
        knowledge_format=storage_format,
    )
    commit_knowledge_artifacts(plan)
    return plan, ledger


@pytest.mark.parametrize("storage_format", STORAGE_FORMATS)
def test_governed_snapshot_reuses_graph_and_preserves_reviews_aliases_and_successors(
    tmp_path, monkeypatch, storage_format
):
    _, ledger = _history_snapshot(tmp_path, storage_format)
    monkeypatch.chdir(tmp_path)
    calls = _count_validation(monkeypatch)
    result = api.query_documentation(
        {"operation": "concept", "value": MODULE_LOCATOR}, wiki_dir="."
    )
    concept = result.get("concept")
    assert (
        isinstance(concept, dict) and concept["reviews"]["items"][0]["state"] == "valid"
    )
    assert calls == {"model": 1, "bundle": 1, "graph": 1}

    view = load_knowledge_read_view(tmp_path, snapshot_only=True)
    assert view.knowledge is not None
    assert validate_governance_projection(
        view.knowledge,
        ledger=ledger,
        _validated_artifacts=view.validated_artifacts,
    ) == validate_governance_projection(view.knowledge, ledger=ledger)
    service = DocumentationGraphQueryService({}, knowledge_view=view)
    selected = service.get_concept("llm-wiki://entities/LegacyUser")["concept"]
    assert selected["lifecycle"] == "superseded" and selected["successor_uid"]
    if storage_format != "v1":
        for selector in ("source:src/accounts.py", "out:concept:" + selected["uid"]):
            captured = capture_knowledge_slice(tmp_path, [selector])
            rows = captured.slice.to_payload()["records"]["edges"]
            assert any(row["value"]["kind"] == "supersedes" for row in rows)
            captured.finish()


@pytest.mark.parametrize("corruption", ("reason", "hash"))
def test_validated_governance_still_compares_exact_supersession_evidence(
    tmp_path, monkeypatch, corruption
):
    plan, ledger = _history_snapshot(tmp_path)
    monkeypatch.chdir(tmp_path)
    payload = json.loads(plan.knowledge_index.content)
    edge = next(
        e
        for e in payload["extensions"][TYPED_GRAPH_EXTENSION_KEY]["edges"]
        if e["kind"] == "supersedes"
    )
    sample = edge["evidence"]["samples"][0]
    if corruption == "reason":
        sample["reason"] = "unrecorded-reason"
    else:
        sample["attributes"]["governance_hash"] = sha256_bytes(b"other-ledger")
    model = knowledge_model.parse_knowledge_index(payload)
    with pytest.raises(GovernanceError, match="authoritative ledger"):
        validate_governance_projection(model, ledger=ledger)
    content = formatted_json_bytes(payload)
    (tmp_path / KNOWLEDGE_INDEX_FILENAME).write_bytes(content)
    marker = plan.committed_manifest.artifact_hashes
    assert marker is not None
    replace(
        plan.committed_manifest,
        artifact_hashes=replace(
            marker,
            knowledge_index_hash=sha256_bytes(content),
        ),
    ).save(tmp_path)

    result = api.query_documentation(
        {"operation": "concept", "value": MODULE_LOCATOR}, wiki_dir="."
    )
    assert result["found"] is False
    knowledge = result.get("knowledge")
    assert isinstance(knowledge, dict) and knowledge["availability"] == "degraded"


def test_governance_reuse_requires_exact_validator_issued_model(tmp_path):
    _, ledger = _history_snapshot(tmp_path)
    view = load_knowledge_read_view(tmp_path, snapshot_only=True)
    assert view.knowledge is not None
    for artifacts, model in (
        (replace(view.validated_artifacts), view.knowledge),
        (view.validated_artifacts, replace(view.knowledge)),
        (object(), view.knowledge),
    ):
        with pytest.raises(TypeError):
            validate_governance_projection(
                model, ledger=ledger, _validated_artifacts=artifacts
            )


def test_new_snapshot_request_rechecks_live_governance_custody(tmp_path, monkeypatch):
    _history_snapshot(tmp_path)
    monkeypatch.chdir(tmp_path)
    request = {"operation": "concept", "value": MODULE_LOCATOR}
    assert api.query_documentation(request, wiki_dir=".")["found"] is True
    (tmp_path / GOVERNANCE_FILENAME).unlink()
    assert api.query_documentation(request, wiki_dir=".")["found"] is False


@pytest.mark.parametrize("misroute", ("wrong-uid", "ambiguous"))
def test_uid_edge_ownership_rejects_misdirected_or_ambiguous_concept_lookup(
    tmp_path, monkeypatch, misroute
):
    plan, ledger = _history_snapshot(tmp_path, "packed-v4-deflate")
    uids = {value.locator: uid for uid, value in ledger.concepts.items()}
    uid = uids["llm-wiki://entities/User"]
    store = open_knowledge_store(
        plan.knowledge_index.content,
        lambda path, maximum: (tmp_path / path).read_bytes(),
    )
    original = store._lookup_references

    def altered(selector):
        if selector != "concept:" + uid:
            return original(selector)
        refs = list(original("concept:" + uids["llm-wiki://entities/AccountService"]))
        return iter(refs * 2 if misroute == "ambiguous" else refs)

    monkeypatch.setattr(store, "_lookup_references", altered)
    with pytest.raises(KnowledgeStorageError, match="(identity|ambiguous)"):
        store._concept_owner(uid)


@pytest.mark.parametrize("storage_format", STORAGE_FORMATS)
@pytest.mark.parametrize("scope", ("bundle", "concept"))
def test_snapshot_receipt_evaluation_reuses_validated_model_and_graph(
    tmp_path, monkeypatch, storage_format, scope
):
    _committed_snapshot(tmp_path, storage_format, governed=True)
    view = load_knowledge_read_view(tmp_path, snapshot_only=True)
    verify_and_write_receipt(
        tmp_path,
        _context(view, scope_locator=MODULE_LOCATOR if scope == "concept" else None),
        [ARTIFACT_INTEGRITY_CHECKER_ID],
    )
    monkeypatch.chdir(tmp_path)
    calls = _count_validation(monkeypatch)

    result = api.query_documentation(
        {"operation": "concept", "value": MODULE_LOCATOR}, wiki_dir="."
    )
    concept = result.get("concept")
    assert (
        isinstance(concept, dict) and concept["machine_verification"]["valid"] is True
    )
    assert calls == {"model": 1, "bundle": 1, "graph": 1}


@pytest.mark.parametrize("scope_locator", (None, MODULE_LOCATOR))
def test_verification_context_reuses_exact_payload_and_keeps_public_context_checks(
    tmp_path, scope_locator
):
    _committed_snapshot(tmp_path, "v1", governed=True)
    view = load_knowledge_read_view(tmp_path, snapshot_only=True)
    artifacts = require_validated_artifacts(view.validated_artifacts)
    options = {
        "knowledge_hash": artifacts.knowledge_index_hash,
        "surface_index_hash": artifacts.surface_index_hash,
        "evaluated_envelope_hash": artifacts.evaluated_envelope_hash,
        "governance_hash": artifacts.governance_hash,
        "scope_locator": scope_locator,
    }
    context = build_artifact_verification_context(
        artifacts.knowledge, **options, _validated_artifacts=artifacts
    )
    assert context == _context(view, scope_locator=scope_locator)
    assert context.knowledge is artifacts.knowledge
    assert "_validated_artifacts" not in vars(context)
    invalid = replace(artifacts.knowledge, schema_version="invalid")
    with pytest.raises(VerificationContractError, match="valid supplied index"):
        replace(context, knowledge=invalid)
    for value in (object(), replace(artifacts)):
        with pytest.raises((TypeError, VerificationContractError)):
            build_artifact_verification_context(
                artifacts.knowledge, **options, _validated_artifacts=value
            )
    for name in (
        "knowledge_hash",
        "surface_index_hash",
        "evaluated_envelope_hash",
        "governance_hash",
    ):
        changed = {**options, name: sha256_bytes(b"other")}
        with pytest.raises(VerificationContractError, match="differs"):
            build_artifact_verification_context(
                artifacts.knowledge, **changed, _validated_artifacts=artifacts
            )


def test_snapshot_receipt_invalidation_keeps_one_full_model_validation(
    tmp_path, monkeypatch
):
    _committed_snapshot(tmp_path, "packed-v4-deflate", governed=True)
    view = load_knowledge_read_view(tmp_path, snapshot_only=True)
    verify_and_write_receipt(
        tmp_path,
        _context(view, knowledge_hash=sha256_bytes(b"older-knowledge")),
        [ARTIFACT_INTEGRITY_CHECKER_ID],
    )
    monkeypatch.chdir(tmp_path)
    calls = _count_validation(monkeypatch)
    result = api.query_documentation(
        {"operation": "concept", "value": MODULE_LOCATOR}, wiki_dir="."
    )
    concept = result.get("concept")
    assert (
        isinstance(concept, dict) and concept["machine_verification"]["valid"] is False
    )
    assert concept["machine_verification"]["invalidation_reasons"]
    assert calls == {"model": 1, "bundle": 1, "graph": 1}
