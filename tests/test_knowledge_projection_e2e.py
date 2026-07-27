"""End-to-end coverage for governed M5 derived projections."""

from __future__ import annotations

import json
import types
from dataclasses import replace
from pathlib import Path

import pytest

import llm_wiki_cli.api as api
from llm_wiki_cli.commands import (
    bootstrap_cmd,
    context_cmd,
    knowledge_cmd,
    lint_cmd,
    migrate_cmd,
    sync_cmd,
)
from llm_wiki_cli.services import obsidian, site_export
from llm_wiki_cli.services import mcp_server
from llm_wiki_cli.services.contracts import SECTION_OWNERSHIP_EXTENSION_KEY
from llm_wiki_cli.services.documentation_queries import (
    DocumentationGraphQueryService,
)
from llm_wiki_cli.services.knowledge_artifacts import (
    KNOWLEDGE_INDEX_FILENAME,
    build_knowledge_commit_plan,
    commit_knowledge_artifacts,
)
from llm_wiki_cli.services.knowledge_consumption import (
    KnowledgeAvailability,
    KnowledgeReadMode,
    load_knowledge_read_view,
)
from llm_wiki_cli.services.knowledge_evidence import sha256_bytes
from llm_wiki_cli.services.knowledge_generation import (
    build_knowledge_generation_plan,
)
from llm_wiki_cli.services.knowledge_governance import (
    ALIAS_LOCATOR,
    ALIAS_NATURAL_KEY,
    GovernanceActor,
    GovernanceLedger,
    add_review_event,
    alias_key,
    apply_governance_projection,
    concept_references_from_knowledge,
    current_review_evidence,
    load_governance,
    move_concept,
    reconcile_concepts,
    review_scope_hash,
    save_governance,
    set_lifecycle,
)
from llm_wiki_cli.services.knowledge_model import (
    parse_knowledge_index,
    serialize_knowledge_index,
)
from llm_wiki_cli.services.knowledge_projection import (
    project_knowledge,
    projection_concept_summary,
    serialize_knowledge_projection,
)
from llm_wiki_cli.services.knowledge_verification import (
    verification_summaries_for_concepts,
)
from llm_wiki_cli.services.verification_contracts import (
    ARTIFACT_INTEGRITY_CHECKER_ID,
    INTERNAL_LINKS_CHECKER_ID,
    build_artifact_verification_context,
    verify_and_write_receipt,
)
from tests.knowledge_fixtures import (
    FIXTURE_REPOSITORY_IDENTITY,
    FIXTURE_SOURCE_PATH,
    _build_surface_projection,
    duplicate_entity_occurrences_fixture,
    fixture_hash,
    materialize_fixture_tree,
    one_module_two_entities_fixture,
)
from tests.test_knowledge_freshness import _live_evaluation
from tests.test_knowledge_generation import _planner_inputs


PRIVATE_TOKEN = "ghp_seededM5Secret123456789"
PRIVATE_COORDINATE = "/Users/alice/private/checkout/accounts.py:99"
MODULE_LOCATOR = "llm-wiki://modules/accounts"
USER_LOCATOR = "llm-wiki://entities/User"
ACCOUNT_SERVICE_LOCATOR = "llm-wiki://entities/AccountService"
LEGACY_USER_LOCATOR = "llm-wiki://entities/LegacyUser"


def _tree_bytes(root: Path) -> dict[str, bytes]:
    return {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


def _dependency_observations() -> dict[str, object]:
    observations = [
        {
            "source_path": FIXTURE_SOURCE_PATH,
            "module": module,
            "name": name,
            "line": line,
            "candidates": candidates,
            "target_path": target_path,
            "resolution": resolution,
        }
        for module, name, line, candidates, target_path, resolution in (
            (
                ".accounts",
                "AccountService",
                1,
                [FIXTURE_SOURCE_PATH],
                FIXTURE_SOURCE_PATH,
                "resolved",
            ),
            ("requests", "get", 2, [], None, "external"),
            ("requests", "get", 3, [], None, "external"),
            (
                "ambiguous.models",
                "Parser",
                4,
                [FIXTURE_SOURCE_PATH, "src/generated_models.py"],
                None,
                "ambiguous",
            ),
            ("missing.alpha", "alpha", 5, [], None, "unresolved"),
        )
    ]
    return {
        "schema_version": "llm-wiki-dependency-observations/v1",
        "observations": observations,
        "coverage": {
            "observed": len(observations) + 2,
            "emitted": len(observations),
            "omitted": 2,
            "limit": len(observations),
            "truncated": True,
            "limitations": ["fixture/input-truncated"],
        },
    }


def _with_pages(fixture, pages):
    surface_payload, surface_bytes = _build_surface_projection(
        source_files=fixture.source_files,
        assets=fixture.assets,
        inventory=fixture.inventory,
        pages=pages,
        module_page_map=fixture.module_page_map,
        entity_occurrence_page_map=fixture.entity_occurrence_page_map,
    )
    return replace(
        fixture,
        pages=pages,
        surface_payload=surface_payload,
        surface_bytes=surface_bytes,
    )


def _reviewable_section(knowledge, concept_locator: str) -> str:
    section_ownership = knowledge.extensions[SECTION_OWNERSHIP_EXTENSION_KEY]
    page = next(
        value
        for value in section_ownership["pages"]
        if value["page_locator"] == concept_locator
    )
    return next(
        section["locator"]
        for section in page["sections"]
        if section.get("semantic_hash") is not None
    )


def _uid_for(ledger: GovernanceLedger, locator: str) -> str:
    return next(
        uid
        for uid, allocation in ledger.concepts.items()
        if allocation.locator == locator
    )


def _commit_governed_fixture(tmp_path: Path) -> Path:
    fixture = one_module_two_entities_fixture()
    prior_pages = tuple(
        replace(
            page,
            content=(
                page.content.replace(
                    "See [Missing](..\\entities\\Missing.md).\n",
                    (
                        "Missing dependency targets are represented in the "
                        "native graph.\n"
                    ),
                ).replace(
                    "Fixture module documentation.\n",
                    (
                        "Fixture module documentation.\n\n"
                        "## Description\n\n"
                        "Stable account-domain policy.\n"
                    ),
                )
                + (
                    "\n## Description\n\nReviewed entity semantics.\n"
                    if page.canonical_path == "entities/User.md"
                    else ""
                )
            ),
        )
        for page in fixture.pages
    )
    prior_fixture = _with_pages(fixture, prior_pages)
    prior_generated = build_knowledge_generation_plan(
        replace(
            _planner_inputs(tmp_path / "prior-plan", prior_fixture),
            dependency_observations=_dependency_observations(),
            graph_evidence_limit=1,
        )
    )
    prior_knowledge = parse_knowledge_index(
        json.loads(prior_generated.knowledge_index.content)
    )

    final_pages = tuple(
        replace(
            page,
            content=page.content.replace(
                "Stable account-domain policy.",
                "Reviewed account-domain policy.",
            ),
        )
        if page.canonical_path == "modules/accounts.md"
        else page
        for page in prior_pages
    )
    fixture = _with_pages(fixture, final_pages)
    tree = materialize_fixture_tree(
        fixture,
        tmp_path / "checkout",
        consumer="api",
    )
    wiki = tree["wiki_root"]
    inputs = replace(
        _planner_inputs(wiki, fixture),
        dependency_observations=_dependency_observations(),
        graph_evidence_limit=1,
    )
    generated = build_knowledge_generation_plan(inputs)
    knowledge = parse_knowledge_index(
        json.loads(generated.knowledge_index.content)
    )
    knowledge = replace(
        knowledge,
        extensions={
            **knowledge.extensions,
            "example.invalid/private": {
                "token": PRIVATE_TOKEN,
                "source_coordinate": PRIVATE_COORDINATE,
            },
        },
    )

    ledger = reconcile_concepts(
        GovernanceLedger.empty("kb_m5_e2e"),
        concept_references_from_knowledge(prior_knowledge),
    )
    module_uid = _uid_for(ledger, MODULE_LOCATOR)
    prior_module = next(
        concept
        for concept in prior_knowledge.concepts
        if concept.locator == MODULE_LOCATOR
    )
    prior_section = _reviewable_section(prior_knowledge, MODULE_LOCATOR)
    prior_evidence = current_review_evidence(prior_module)
    assert prior_evidence is not None
    ledger = add_review_event(
        ledger,
        module_uid,
        section_locator=prior_section,
        scope_hash=review_scope_hash(prior_knowledge, prior_section),
        evidence=prior_evidence,
        reviewer=GovernanceActor(
            "human",
            "private-expired-reviewer@example.invalid",
        ),
        method="manual-review",
        method_version="1",
        authored_at="2026-07-27T09:00:00Z",
    )
    ledger = reconcile_concepts(
        ledger,
        concept_references_from_knowledge(knowledge),
    )
    user_uid = _uid_for(ledger, USER_LOCATOR)
    account_service_uid = _uid_for(ledger, ACCOUNT_SERVICE_LOCATOR)
    ledger = move_concept(
        ledger,
        user_uid,
        locator=LEGACY_USER_LOCATOR,
        natural_key="code-entity:entities/LegacyUser.md",
    )
    ledger = move_concept(
        ledger,
        user_uid,
        locator=USER_LOCATOR,
        natural_key="code-entity:entities/User.md",
    )

    current_user = next(
        concept
        for concept in knowledge.concepts
        if concept.locator == USER_LOCATOR
    )
    user_section = _reviewable_section(knowledge, USER_LOCATOR)
    user_evidence = current_review_evidence(current_user)
    assert user_evidence is not None
    ledger = add_review_event(
        ledger,
        user_uid,
        section_locator=user_section,
        scope_hash=review_scope_hash(knowledge, user_section),
        evidence=user_evidence,
        reviewer=GovernanceActor(
            "human",
            "private-valid-reviewer@example.invalid",
        ),
        method="manual-review",
        method_version="2",
        authored_at="2026-07-27T09:30:00Z",
    )

    ledger = set_lifecycle(
        ledger,
        module_uid,
        "active",
        actor=GovernanceActor("human", "private-reviewer@example.invalid"),
        authored_at="2026-07-27T10:00:00Z",
    )
    ledger = set_lifecycle(
        ledger,
        module_uid,
        "deprecated",
        actor=GovernanceActor("human", "private-reviewer@example.invalid"),
        authored_at="2026-07-27T11:00:00Z",
    )
    ledger = set_lifecycle(
        ledger,
        user_uid,
        "active",
        actor=GovernanceActor("human", "private-reviewer@example.invalid"),
        authored_at="2026-07-27T10:05:00Z",
    )
    ledger = set_lifecycle(
        ledger,
        user_uid,
        "superseded",
        successor_uid=account_service_uid,
        actor=GovernanceActor("human", "private-reviewer@example.invalid"),
        authored_at="2026-07-27T11:05:00Z",
    )
    ledger = set_lifecycle(
        ledger,
        account_service_uid,
        "active",
        actor=GovernanceActor("human", "private-reviewer@example.invalid"),
        authored_at="2026-07-27T10:10:00Z",
    )
    save_governance(wiki, ledger, expected_hash=None)

    governed = apply_governance_projection(knowledge, ledger)
    plan = build_knowledge_commit_plan(
        wiki,
        surface_index_bytes=generated.surface_index.content,
        knowledge_index_bytes=serialize_knowledge_index(governed).encode("utf-8"),
        manifest=generated.committed_manifest,
    )
    commit_knowledge_artifacts(plan)
    return wiki


def _commit_duplicate_occurrence_fixture(tmp_path: Path) -> Path:
    fixture = duplicate_entity_occurrences_fixture()
    tree = materialize_fixture_tree(
        fixture,
        tmp_path / "duplicate-checkout",
        consumer="api",
    )
    wiki = tree["wiki_root"]
    generated = build_knowledge_generation_plan(_planner_inputs(wiki, fixture))
    knowledge = parse_knowledge_index(
        json.loads(generated.knowledge_index.content)
    )
    ledger = reconcile_concepts(
        GovernanceLedger.empty("kb_m5_duplicate"),
        concept_references_from_knowledge(knowledge),
    )
    save_governance(wiki, ledger, expected_hash=None)
    governed = apply_governance_projection(knowledge, ledger)
    plan = build_knowledge_commit_plan(
        wiki,
        surface_index_bytes=generated.surface_index.content,
        knowledge_index_bytes=serialize_knowledge_index(governed).encode(
            "utf-8"
        ),
        manifest=generated.committed_manifest,
    )
    commit_knowledge_artifacts(plan)
    return wiki


def _write_machine_receipt(wiki: Path, state: str) -> None:
    if state == "not-run":
        return
    view = load_knowledge_read_view(wiki, snapshot_only=True)
    assert view.knowledge is not None
    assert view.manifest_basis is not None
    hashes = view.manifest_basis.artifact_hashes
    assert hashes is not None
    knowledge_hash = hashes.knowledge_index_hash
    if state == "invalidated":
        knowledge_hash = fixture_hash("m5-prior-knowledge")
    context = build_artifact_verification_context(
        view.knowledge,
        knowledge_hash=knowledge_hash,
        surface_index_hash=hashes.surface_index_hash,
        evaluated_envelope_hash=hashes.evaluated_envelope_hash,
        governance_hash=hashes.governance_hash,
    )
    checker_ids = (
        [INTERNAL_LINKS_CHECKER_ID]
        if state == "failed"
        else [ARTIFACT_INTEGRITY_CHECKER_ID]
    )
    receipt = verify_and_write_receipt(wiki, context, checker_ids)
    assert receipt.result.value == (
        "failed" if state == "failed" else "passed"
    )


def test_governed_projection_enriches_site_and_obsidian_without_native_writes(
    tmp_path,
    monkeypatch,
):
    wiki = _commit_governed_fixture(tmp_path)
    _write_machine_receipt(wiki, "failed")
    native_before = _tree_bytes(wiki)
    view = load_knowledge_read_view(
        wiki,
        snapshot_only=True,
        include_machine_verification=True,
    )

    assert view.availability is KnowledgeAvailability.READY
    assert view.mode is KnowledgeReadMode.SNAPSHOT_ONLY
    assert view.freshness_evaluated is False
    projection = project_knowledge(
        view,
        relationship_limit=3,
        public_repository_identity=FIXTURE_REPOSITORY_IDENTITY,
    )
    encoded_projection = serialize_knowledge_projection(projection)
    assert projection.source_knowledge_hash == sha256_bytes(
        (wiki / KNOWLEDGE_INDEX_FILENAME).read_bytes()
    )
    assert projection.bundle["bundle_id"] == "kb_m5_e2e"
    assert projection.bundle["repository_identity"] == FIXTURE_REPOSITORY_IDENTITY
    assert PRIVATE_TOKEN not in encoded_projection
    assert PRIVATE_COORDINATE not in encoded_projection
    assert FIXTURE_SOURCE_PATH not in encoded_projection
    assert "private-reviewer@example.invalid" not in encoded_projection
    assert "private-valid-reviewer@example.invalid" not in encoded_projection
    assert "private-expired-reviewer@example.invalid" not in encoded_projection

    internal_projection = project_knowledge(
        view,
        profile="internal",
        relationship_limit=100,
    )
    assert {
        concept["document"]["role"]
        for concept in internal_projection.concepts.values()
    } == {"generated", "mixed", "semantic"}
    assert {
        concept["evidence"]["state"]
        for concept in projection.concepts.values()
    } == {"not-applicable", "present", "unknown"}
    assert {
        concept["freshness"]["state"]
        for concept in projection.concepts.values()
    } == {"not-evaluated"}
    all_relationships = [
        relationship
        for concept in internal_projection.concepts.values()
        for relationship in concept["relationships"]["items"]
    ]
    assert {
        relationship["resolution"] for relationship in all_relationships
    } == {"ambiguous", "external", "resolved", "unresolved"}
    assert any(
        relationship["resolution"] == "resolved"
        and relationship["target"]["kind"] == "concept"
        and relationship["target"]["present"] is True
        for relationship in all_relationships
    )
    assert any(
        relationship["resolution"] == "external"
        and relationship["target"]["kind"] == "external-resource"
        and relationship["evidence"]["observed"] == 2
        and relationship["evidence"]["unique"] == 2
        and relationship["evidence"]["emitted"] == 1
        and relationship["evidence"]["omitted"] == 1
        and relationship["coverage"]["truncated"] is True
        for relationship in all_relationships
    )
    assert any(
        relationship["resolution"] == "ambiguous"
        and relationship["target"]["candidate_count"] == 2
        for relationship in all_relationships
    )
    assert any(
        relationship["resolution"] == "unresolved"
        and relationship["target"]["present"] is False
        for relationship in all_relationships
    )

    current_view = load_knowledge_read_view(
        wiki,
        live_evaluation=_live_evaluation(view.knowledge),
    )
    current_projection = project_knowledge(
        current_view,
        profile="internal",
    )
    assert {
        concept["freshness"]["state"]
        for concept in current_projection.concepts.values()
    } == {"current", "unknown"}
    changed_view = load_knowledge_read_view(
        wiki,
        live_evaluation=_live_evaluation(
            view.knowledge,
            source_hash_by_path={
                FIXTURE_SOURCE_PATH: fixture_hash("m5-live-source-changed")
            },
            observation_by_locator={
                USER_LOCATOR: fixture_hash("m5-live-user-changed")
            },
        ),
    )
    changed_projection = project_knowledge(
        changed_view,
        profile="internal",
    )
    assert (
        changed_projection.concepts["entities/User.md"]["freshness"]["state"]
        == "source-changed"
    )
    assert (
        changed_projection.concepts["entities/AccountService.md"]["freshness"][
            "state"
        ]
        == "nonsemantic-source-change"
    )
    missing_view = load_knowledge_read_view(
        wiki,
        live_evaluation=_live_evaluation(
            view.knowledge,
            source_hash_by_path={},
            missing_source_paths=frozenset({FIXTURE_SOURCE_PATH}),
        ),
    )
    missing_projection = project_knowledge(
        missing_view,
        profile="internal",
    )
    assert {
        missing_projection.concepts[path]["freshness"]["state"]
        for path in (
            "entities/AccountService.md",
            "entities/User.md",
            "modules/accounts.md",
        )
    } == {"source-missing"}
    incompatible_view = load_knowledge_read_view(
        wiki,
        live_evaluation=_live_evaluation(
            view.knowledge,
            generation_options_hash=fixture_hash(
                "m5-live-generation-options-incompatible"
            ),
        ),
    )
    incompatible_projection = project_knowledge(
        incompatible_view,
        profile="internal",
    )
    assert {
        incompatible_projection.concepts[path]["freshness"]["state"]
        for path in (
            "entities/AccountService.md",
            "entities/User.md",
            "modules/accounts.md",
        )
    } == {"basis-incompatible"}

    query_service = DocumentationGraphQueryService(
        {},
        knowledge_view=view,
        machine_verification=verification_summaries_for_concepts(view),
        limit=100,
    )
    direct_concept = query_service.get_concept(USER_LOCATOR)
    assert direct_concept["concept"]["lifecycle"] == "superseded"
    assert (
        direct_concept["concept"]["successor_uid"]
        == projection.concepts["entities/User.md"]["lifecycle"]["successor_uid"]
    )
    assert direct_concept["concept"]["machine_verification"][
        "recorded_result"
    ] == "failed"
    assert (
        query_service.get_concept(LEGACY_USER_LOCATOR)["concept"]
        == direct_concept["concept"]
    )
    assert api.get_concept(USER_LOCATOR, service=query_service) == direct_concept
    direct_graph = query_service.traverse_typed_graph(
        MODULE_LOCATOR,
        include_evidence=False,
    )
    assert (
        api.traverse_typed_graph(
            MODULE_LOCATOR,
            include_evidence=False,
            service=query_service,
        )
        == direct_graph
    )

    source_root = wiki.parent.parent
    wiki_relative = wiki.relative_to(source_root).as_posix()
    monkeypatch.chdir(source_root)
    live_service = api.build_documentation_query_service(
        ".",
        wiki_dir=wiki_relative,
        limit=100,
        read_only=True,
    )
    live_module = api.get_concept(MODULE_LOCATOR, service=live_service)
    live_graph = api.traverse_typed_graph(
        MODULE_LOCATOR,
        direction="outgoing",
        resolutions=["external"],
        include_evidence=False,
        service=live_service,
    )
    public_mcp = mcp_server.McpWikiService(
        src_dir=".",
        wiki_dir=wiki_relative,
    )
    mcp_module = public_mcp.get_concept(MODULE_LOCATOR, limit=100)
    mcp_graph = public_mcp.traverse_typed_graph(
        MODULE_LOCATOR,
        direction="outgoing",
        resolutions=["external"],
        include_evidence=False,
        limit=100,
    )
    context = api.build_context(
        ".",
        budget=200_000,
        focus="all",
        filters={
            "surface": "modules",
            "relationship_direction": "outgoing",
            "relationship_resolution": "external",
        },
        wiki_dir=wiki_relative,
        read_only=True,
    )

    assert context["knowledge"] == live_module["knowledge"] == mcp_module[
        "knowledge"
    ] == {
        "availability": "ready",
        "reason": "all-projection-commitments-match",
        "freshness_evaluated": True,
    }
    assert live_module["concept"]["freshness"] == mcp_module["concept"][
        "freshness"
    ] == {
        "state": "basis-incompatible",
        "reason": "extractor-selection-changed",
        "live_comparison_performed": True,
    }
    assert context["surface"]["knowledge_selection"] == {
        "unfiltered_total": 1,
        "filtered_total": 1,
        "returned": 1,
        "truncated": False,
    }
    assert context["surface"]["bounds"]["pages"] == {
        "total": 1,
        "returned": 1,
        "truncated": False,
    }
    assert context["bounds"]["files"] == {
        "total": 1,
        "returned": 1,
        "truncated": False,
    }
    assert len(context["surface"]["pages"]) == 1
    context_module = context["surface"]["pages"][0]
    assert context_module["canonical_path"] == "modules/accounts.md"
    assert context_module["mcp_uri"] == MODULE_LOCATOR
    context_knowledge = context_module["knowledge"]
    assert context_knowledge["freshness"] == live_module["concept"][
        "freshness"
    ]
    assert (
        context_knowledge["lifecycle"]
        == live_module["concept"]["lifecycle"]
        == mcp_module["concept"]["lifecycle"]
        == "deprecated"
    )
    assert context_knowledge["verification"] == live_module["concept"][
        "verification"
    ] == "untracked"
    assert context_knowledge["review"] == {
        "scope": "section",
        "state": "has-expired-sections",
        "total": 1,
        "returned": 1,
        "valid_returned": 0,
        "expired_returned": 1,
        "truncated": False,
        "reasons": ["scope-changed"],
    }
    assert context_knowledge["machine_verification"] == {
        "availability": "recorded",
        "valid": True,
        "recorded_result": "failed",
        "passed": False,
        "checks": {"total": 1, "passed": 0, "failed": 1},
        "invalidation_reasons": [],
    }
    encoded_context = json.dumps(context, sort_keys=True)
    for private_value in (
        PRIVATE_TOKEN,
        PRIVATE_COORDINATE,
        "private-reviewer@example.invalid",
        "private-valid-reviewer@example.invalid",
        "private-expired-reviewer@example.invalid",
        "scope_uid",
        "diagnostics",
    ):
        assert private_value not in encoded_context

    context_graph = context_module["typed_graph"]
    expected_graph_bounds = {
        "total": live_graph["total"],
        "returned": live_graph["returned"],
        "truncated": live_graph["truncated"],
    }
    assert expected_graph_bounds == {
        "total": mcp_graph["total"],
        "returned": mcp_graph["returned"],
        "truncated": mcp_graph["truncated"],
    } == {
        "total": context_graph["filtered_total"],
        "returned": context_graph["returned"],
        "truncated": context_graph["truncated"],
    } == {
        "total": 1,
        "returned": 1,
        "truncated": False,
    }
    assert context_graph["direction"] == "outgoing"
    assert context_graph["filters"] == {
        "relationship_direction": "outgoing",
        "relationship_resolution": "external",
    }
    assert context_graph["unfiltered_total"] == 6
    assert context_graph["coverage"] == {
        "scope": "returned-edges",
        "edges": 1,
        "observed": 2,
        "emitted": 1,
        "omitted": 1,
        "truncated": True,
        "limitations": [],
    }
    assert live_graph["edges"][0]["coverage"]["truncated"] is True
    dependencies_coverage = next(
        item
        for item in context["typed_graph"]["coverage"]
        if item["analyzer"] == "dependencies"
    )
    assert dependencies_coverage == {
        "analyzer": "dependencies",
        "observed": 7,
        "emitted": 5,
        "omitted": 2,
        "limit": 5,
        "truncated": True,
        "limitations": ["fixture/input-truncated"],
    }

    def fail_runtime_generation_options(*_args, **_kwargs):
        raise ValueError("force supported snapshot-only fallback")

    with monkeypatch.context() as snapshot_guard:
        snapshot_guard.setattr(
            context_cmd,
            "runtime_generation_options",
            fail_runtime_generation_options,
        )
        snapshot_context = api.build_context(
            ".",
            budget=200_000,
            focus="all",
            filters={
                "surface": "modules",
                "relationship_direction": "outgoing",
                "relationship_resolution": "external",
            },
            wiki_dir=wiki_relative,
            read_only=True,
        )

    assert snapshot_context["knowledge"] == {
        "availability": "ready",
        "reason": "all-projection-commitments-match",
        "freshness_evaluated": False,
    }
    assert snapshot_context["surface"]["knowledge_selection"] == context["surface"][
        "knowledge_selection"
    ]
    assert snapshot_context["surface"]["bounds"] == context["surface"]["bounds"]
    assert snapshot_context["bounds"] == context["bounds"]
    snapshot_module = snapshot_context["surface"]["pages"][0]
    assert snapshot_module["canonical_path"] == context_module["canonical_path"]
    assert snapshot_module["mcp_uri"] == context_module["mcp_uri"]
    assert snapshot_module["knowledge"]["freshness"] == {
        "state": None,
        "reason": "not-evaluated",
        "live_comparison_performed": False,
    }
    assert snapshot_module["knowledge"]["lifecycle"] == context_knowledge["lifecycle"]
    assert snapshot_module["knowledge"]["review"] == context_knowledge["review"]
    assert snapshot_module["knowledge"]["verification"] == context_knowledge[
        "verification"
    ]
    assert snapshot_module["knowledge"]["machine_verification"] == context_knowledge[
        "machine_verification"
    ]
    assert snapshot_module["typed_graph"] == context_graph
    encoded_snapshot_context = json.dumps(snapshot_context, sort_keys=True)
    for private_value in (
        PRIVATE_TOKEN,
        PRIVATE_COORDINATE,
        "private-reviewer@example.invalid",
        "private-valid-reviewer@example.invalid",
        "private-expired-reviewer@example.invalid",
        "scope_uid",
        "diagnostics",
    ):
        assert private_value not in encoded_snapshot_context
    assert _tree_bytes(wiki) == native_before

    site = tmp_path / "site-enriched"
    vault = tmp_path / "vault-enriched"

    def fail_raw_surface_load(*_args, **_kwargs):
        raise AssertionError("enriched Site export loaded raw surface coordinates")

    with monkeypatch.context() as projection_guard:
        projection_guard.setattr(
            site_export,
            "_load_surface_index_sources",
            fail_raw_surface_load,
        )
        site_report = site_export.export_site_mirror(
            wiki_dir=wiki,
            out_dir=site,
            knowledge_metadata="summary",
            knowledge_projection=projection,
        )
    obsidian_report = obsidian.export_obsidian_vault(
        src_dir=str(tmp_path / "source-does-not-exist"),
        wiki_dir=wiki,
        vault_dir=vault,
        knowledge_metadata="summary",
        knowledge_projection=projection,
    )

    assert site_report.ok is True
    assert site_report.issues == []
    assert site_report.warnings == []
    assert obsidian_report.ok is True
    assert obsidian_report.issues == []
    assert _tree_bytes(wiki) == native_before
    site_check = site_export.check_site_mirror(
        wiki_dir=wiki,
        out_dir=site,
        knowledge_metadata="summary",
        knowledge_projection=projection,
    )
    assert site_check.ok
    assert site_check.issues == []
    assert site_check.warnings == []
    obsidian_check = obsidian.check_obsidian_vault(
        wiki_dir=wiki,
        vault_dir=vault,
        knowledge_metadata="summary",
        knowledge_projection=projection,
    )
    assert obsidian_check.ok
    assert obsidian_check.issues == []

    module_summary = projection_concept_summary(
        projection,
        "modules/accounts.md",
    )
    site_module = (site / "modules" / "accounts.md").read_text(encoding="utf-8")
    vault_module = (
        vault / "LLM Wiki" / "Modules" / "accounts.md"
    ).read_text(encoding="utf-8")
    for key in ("knowledge_bundle_id", "knowledge_uid", "source_knowledge_hash"):
        expected = module_summary[key]
        assert f'{key}: "{expected}"' in site_module
        assert f'{key}: "{expected}"' in vault_module
    assert "source_path:" not in site_module
    assert "source_path:" not in vault_module

    user_summary = projection_concept_summary(
        projection,
        "entities/User.md",
    )
    assert module_summary["knowledge_lifecycle"] == "deprecated"
    assert module_summary["knowledge_review"] == "has-expired-sections"
    assert module_summary["knowledge_review_expired"] == "1"
    assert '"reasons":["scope-changed"]' in module_summary[
        "knowledge_review_items"
    ]
    assert user_summary["knowledge_lifecycle"] == "superseded"
    assert user_summary["knowledge_successor_uid"] == (
        projection.concepts["entities/AccountService.md"]["identity"][
            "namespaced_uid"
        ]
    )
    assert user_summary["knowledge_review"] == "has-valid-sections"
    assert user_summary["knowledge_review_valid"] == "1"
    assert user_summary["knowledge_machine_check"] == "failed"
    assert user_summary["knowledge_machine_check_result"] == "failed"

    relationships = projection.concepts["modules/accounts.md"]["relationships"]
    assert relationships["total"] == 6
    assert relationships["returned"] == 3
    assert relationships["truncated"] is True
    assert any(
        item["resolution"] == "unresolved"
        and item["target"] == {
            "kind": "unresolved",
            "label": "Unresolved target",
            "present": False,
        }
        for item in relationships["items"]
    )
    assert "_Relationships: returned 3 of 6; limit 3; truncated true._" in (
        vault_module
    )
    assert "### Outgoing: `imports`" in vault_module
    assert "Unresolved target — resolution `unresolved`" in vault_module
    assert "unique 1" in vault_module
    assert "limit 1, truncated false" in vault_module

    derived_bytes = b"\n".join(
        [*_tree_bytes(site).values(), *_tree_bytes(vault).values()]
    )
    assert PRIVATE_TOKEN.encode() not in derived_bytes
    assert PRIVATE_COORDINATE.encode() not in derived_bytes

    def fail_inventory(*_args, **_kwargs):
        raise AssertionError("disabled Obsidian export ran source inventory")

    monkeypatch.setattr(
        "llm_wiki_cli.commands.extract_cmd.get_inventory",
        fail_inventory,
    )
    site_default = tmp_path / "site-default"
    site_explicit_disabled = tmp_path / "site-explicit-disabled"
    vault_default = tmp_path / "vault-default"
    vault_explicit_disabled = tmp_path / "vault-explicit-disabled"
    site_export.export_site_mirror(wiki_dir=wiki, out_dir=site_default)
    site_export.export_site_mirror(
        wiki_dir=wiki,
        out_dir=site_explicit_disabled,
        knowledge_metadata=None,
        knowledge_projection=None,
    )
    obsidian.export_obsidian_vault(
        src_dir=str(tmp_path / "source-does-not-exist"),
        wiki_dir=wiki,
        vault_dir=vault_default,
    )
    obsidian.export_obsidian_vault(
        src_dir=str(tmp_path / "source-does-not-exist"),
        wiki_dir=wiki,
        vault_dir=vault_explicit_disabled,
        knowledge_metadata=None,
        knowledge_projection=None,
    )

    assert _tree_bytes(site_default) == _tree_bytes(site_explicit_disabled)
    assert _tree_bytes(vault_default) == _tree_bytes(vault_explicit_disabled)
    assert _tree_bytes(wiki) == native_before


@pytest.mark.parametrize(
    ("receipt_state", "expected_state", "expected_result"),
    [
        ("passed", "verified", "passed"),
        ("failed", "failed", "failed"),
        ("invalidated", "invalid", "passed"),
        ("not-run", "not-run", "not-evaluated"),
    ],
)
def test_actual_receipt_states_are_projected_from_the_shared_read_view(
    tmp_path,
    receipt_state,
    expected_state,
    expected_result,
):
    wiki = _commit_governed_fixture(tmp_path)
    _write_machine_receipt(wiki, receipt_state)

    view = load_knowledge_read_view(
        wiki,
        snapshot_only=True,
        include_machine_verification=True,
    )
    projection = project_knowledge(view)

    assert {
        concept["machine_check"]["state"]
        for concept in projection.concepts.values()
    } == {expected_state}
    assert {
        projection_concept_summary(projection, path)[
            "knowledge_machine_check_result"
        ]
        for path in projection.concepts
    } == {expected_result}
    if receipt_state == "invalidated":
        assert view.machine_verification.valid is False
        assert "knowledge-changed" in (
            view.machine_verification.invalidation_reasons
        )
        assert {
            concept["machine_check"]["reason"]
            for concept in projection.concepts.values()
        } == {"knowledge-changed"}
    elif receipt_state == "not-run":
        assert view.machine_verification.availability.value == "absent"
    else:
        assert view.machine_verification.valid is True


def test_duplicate_occurrences_keep_distinct_governed_projection_identity(
    tmp_path,
):
    wiki = _commit_duplicate_occurrence_fixture(tmp_path)
    native_before = _tree_bytes(wiki)
    view = load_knowledge_read_view(wiki, snapshot_only=True)
    projection = project_knowledge(view)

    first = projection.concepts["entities/Parser.md"]
    second = projection.concepts["entities/Parser_2.md"]
    assert first["concept_kind"] == second["concept_kind"] == "code-entity"
    assert first["identity"]["uid"] != second["identity"]["uid"]
    assert (
        first["identity"]["namespaced_uid"]
        != second["identity"]["namespaced_uid"]
    )

    site = tmp_path / "duplicate-site"
    vault = tmp_path / "duplicate-vault"
    site_report = site_export.export_site_mirror(
        wiki_dir=wiki,
        out_dir=site,
        knowledge_metadata="summary",
        knowledge_projection=projection,
    )
    obsidian_report = obsidian.export_obsidian_vault(
        src_dir=str(tmp_path / "source-does-not-exist"),
        wiki_dir=wiki,
        vault_dir=vault,
        knowledge_metadata="summary",
        knowledge_projection=projection,
    )
    assert site_report.ok
    assert site_report.issues == []
    assert site_report.warnings == []
    assert obsidian_report.ok
    assert obsidian_report.issues == []

    site_check = site_export.check_site_mirror(
        wiki_dir=wiki,
        out_dir=site,
        knowledge_metadata="summary",
        knowledge_projection=projection,
    )
    obsidian_check = obsidian.check_obsidian_vault(
        wiki_dir=wiki,
        vault_dir=vault,
        knowledge_metadata="summary",
        knowledge_projection=projection,
    )
    assert site_check.ok
    assert site_check.issues == []
    assert site_check.warnings == []
    assert obsidian_check.ok
    assert obsidian_check.issues == []
    assert _tree_bytes(wiki) == native_before


def test_same_corpus_runs_bootstrap_sync_migrate_and_strict_lint_with_rename(
    tmp_path,
    monkeypatch,
    capsys,
):
    fixture = one_module_two_entities_fixture()
    project = tmp_path / "command-workflow"
    project.mkdir()
    for relative_path, content in fixture.source_files.items():
        source_path = project / relative_path
        source_path.parent.mkdir(parents=True, exist_ok=True)
        source_path.write_text(content, encoding="utf-8")

    wiki = project / "docs" / "llm_wiki"
    monkeypatch.chdir(project)
    bootstrap_cmd.run(
        types.SimpleNamespace(
            src_dir=".",
            wiki_dir=str(wiki),
            overwrite=False,
            depth="full",
            skip_workflows=True,
            source_adapter=True,
            format="text",
        )
    )
    capsys.readouterr()
    knowledge_cmd.run(
        types.SimpleNamespace(
            knowledge_action="init",
            wiki_dir=str(wiki),
            bundle_id="kb_m5_command_workflow",
            dry_run=False,
        )
    )
    capsys.readouterr()

    initial_ledger = load_governance(wiki).ledger
    module_uid = _uid_for(initial_ledger, MODULE_LOCATOR)
    initial_allocation = initial_ledger.concepts[module_uid]
    assert initial_allocation.natural_key == "source-module:modules/accounts.md"

    colliding_module = project / "other" / "accounts.py"
    colliding_module.parent.mkdir(parents=True)
    colliding_module.write_text(
        'class AuditRecord:\n    """One audit record."""\n',
        encoding="utf-8",
    )
    sync_cmd.run(
        types.SimpleNamespace(
            src_dir=".",
            wiki_dir=str(wiki),
            jobs=1,
            no_cache=True,
        )
    )
    capsys.readouterr()

    renamed_ledger = load_governance(wiki).ledger
    renamed_allocation = renamed_ledger.concepts[module_uid]
    assert renamed_allocation.locator != MODULE_LOCATOR
    assert renamed_allocation.natural_key != initial_allocation.natural_key
    assert (
        renamed_ledger.aliases[
            alias_key(ALIAS_LOCATOR, MODULE_LOCATOR)
        ].uid
        == module_uid
    )
    assert (
        renamed_ledger.aliases[
            alias_key(
                ALIAS_NATURAL_KEY,
                initial_allocation.natural_key,
            )
        ].uid
        == module_uid
    )

    migrate_cmd.run(
        types.SimpleNamespace(
            src_dir=".",
            wiki_dir=str(wiki),
            dry_run=False,
        )
    )
    capsys.readouterr()
    lint_cmd.run(
        types.SimpleNamespace(
            src_dir=".",
            wiki_dir=str(wiki),
            strict=True,
            jobs=1,
            no_cache=True,
        )
    )
    capsys.readouterr()

    final_ledger = load_governance(wiki).ledger
    assert final_ledger.concepts[module_uid] == renamed_allocation
    assert (
        final_ledger.aliases[
            alias_key(ALIAS_LOCATOR, MODULE_LOCATOR)
        ].uid
        == module_uid
    )
    view = load_knowledge_read_view(wiki, snapshot_only=True)
    assert view.availability is KnowledgeAvailability.READY
    projection = project_knowledge(view, profile="internal")
    projected = next(
        concept
        for concept in projection.concepts.values()
        if concept["locator"] == renamed_allocation.locator
    )
    assert projected["identity"]["uid"] == module_uid
    query_service = DocumentationGraphQueryService(
        {},
        knowledge_view=view,
    )
    alias_result = query_service.get_concept(MODULE_LOCATOR)["concept"]
    assert alias_result["uid"] == module_uid
    assert alias_result["locator"] == renamed_allocation.locator
