"""Retained member pages make qualified historical, never current, promises."""

from __future__ import annotations

import json
from copy import deepcopy
from dataclasses import replace

import pytest

from llm_wiki_cli.services.knowledge_artifacts import (
    KnowledgeArtifactError,
    validate_knowledge_artifacts,
)
from llm_wiki_cli.services.knowledge_consumption import build_knowledge_read_view
from llm_wiki_cli.services.knowledge_envelope import ConsumedInput, ConsumedInputKind
from llm_wiki_cli.services.knowledge_generation import (
    KnowledgeGenerationError,
    build_knowledge_generation_plan,
)
from llm_wiki_cli.services.knowledge_governance import (
    GOVERNANCE_EXTENSION_KEY,
    GovernanceActor,
    GovernanceLedger,
    concept_references_from_knowledge,
    reconcile_concepts,
    set_lifecycle,
)
from llm_wiki_cli.services.knowledge_index import serialize_knowledge_index
from llm_wiki_cli.services.knowledge_loader import KnowledgeLoadResult
from llm_wiki_cli.services.knowledge_model import (
    ActorKind,
    EvidenceState,
    KnowledgeLoadState,
    Lifecycle,
    Verification,
    parse_knowledge_index,
)
from llm_wiki_cli.services.lint_service import (
    LintReport,
    _check_entity_coverage,
    _check_knowledge_concepts,
)
from llm_wiki_cli.services.source_retirement import (
    SOURCE_MEMBER_REMOVED_HEADER,
    SOURCE_RETIREMENT_EXTENSION_KEY,
    SourceRetirementError,
    read_entity_retirement_state,
    retired_entity_mappings,
    with_entity_retirement_state,
)
from tests.knowledge_fixtures import FIXTURE_SOURCE_PATH, fixture_hash
from tests.test_knowledge_generation import _planner_inputs

RETIRED_PATH = "entities/User.md"


def _retirement_inputs(tmp_path, *, unknown=False):
    inputs = _planner_inputs(tmp_path)
    prior = build_knowledge_generation_plan(
        replace(inputs, force_unknown_evidence=unknown)
    )
    producer = parse_knowledge_index(
        json.loads(prior.knowledge_index.content)
    ).bundle.producer
    inventory = {path: deepcopy(dict(data)) for path, data in inputs.inventory.items()}
    inventory[FIXTURE_SOURCE_PATH]["classes"] = [
        cls for cls in inventory[FIXTURE_SOURCE_PATH]["classes"]
        if cls["name"] != "User"
    ]
    owner = prior.committed_manifest.page_source_mappings[RETIRED_PATH]
    source_hash = fixture_hash("surviving-source-with-user-removed")
    return replace(
        inputs,
        inventory=inventory,
        source_content_hashes={FIXTURE_SOURCE_PATH: source_hash},
        consumed_inputs=(ConsumedInput(
            path=FIXTURE_SOURCE_PATH,
            content_hash=source_hash,
            kind=ConsumedInputKind.SOURCE,
        ),),
        entity_occurrence_page_map={
            coordinate: page for coordinate, page in inputs.entity_occurrence_page_map.items()
            if page != "User"
        },
        previous_manifest=prior.committed_manifest,
        previous_producer=producer,
        manifest_generation_inputs=with_entity_retirement_state(
            inputs.manifest_generation_inputs or {}, {RETIRED_PATH: owner}
        ),
    )


def _view(plan):
    knowledge = parse_knowledge_index(json.loads(plan.knowledge_index.content))
    return build_knowledge_read_view(
        KnowledgeLoadResult(
            status=KnowledgeLoadState.VALID,
            surface=json.loads(plan.surface_index.content),
            knowledge=knowledge,
            manifest_basis=plan.committed_manifest,
        ),
        snapshot_only=True,
    )


def _retired_concept(view):
    assert view.knowledge is not None
    return next(
        concept for concept in view.knowledge.concepts
        if concept.document.canonical_path == RETIRED_PATH
    )


@pytest.mark.parametrize("unknown", [False, True])
def test_retirement_projects_historical_or_unknown_without_human_lifecycle(
    tmp_path, unknown
):
    inputs = _retirement_inputs(tmp_path, unknown=unknown)
    plan = build_knowledge_generation_plan(inputs)
    view = _view(plan)
    concept = _retired_concept(view)
    tombstone = plan.committed_manifest.tombstones[RETIRED_PATH]

    assert RETIRED_PATH not in plan.committed_manifest.evidence_baselines
    assert concept.extensions[SOURCE_RETIREMENT_EXTENSION_KEY] == {
        "schema_version": "llm-wiki-entity-retirement/v1",
        "state": "source-member-removed",
        "source_path": FIXTURE_SOURCE_PATH,
        "entity_name": "User",
        "occurrence": 1,
    }
    if unknown:
        assert tombstone.last_valid_basis is None
        assert concept.facets.structure.evidence is EvidenceState.UNKNOWN
        assert concept.facets.structure.basis is None
    else:
        assert tombstone.last_valid_basis is not None
        assert concept.facets.structure.evidence is EvidenceState.PRESENT
        assert concept.facets.structure.basis is not None
        assert concept.facets.structure.basis.source_content_hash == (
            tombstone.last_valid_basis.source_content_hash
        )
        assert concept.facets.structure.basis.source_content_hash != (
            inputs.source_content_hashes[FIXTURE_SOURCE_PATH]
        )
    assert concept.lifecycle is Lifecycle.UNKNOWN
    assert concept.facets.semantics.authorship.kind is ActorKind.UNKNOWN
    assert concept.facets.semantics.verification is Verification.UNTRACKED

    report = LintReport("wiki", "source", strict=True)
    _check_knowledge_concepts(report, view)
    assert report.issues == []
    assert [(item.severity, item.reason_code) for item in report.diagnostics] == [
        ("info", "source-retirement-unknown" if unknown else "source-retirement-historical")
    ]


def test_force_unknown_retirement_cannot_resurrect_live_baseline(tmp_path):
    plan = build_knowledge_generation_plan(
        replace(_retirement_inputs(tmp_path), force_unknown_evidence=True)
    )
    assert RETIRED_PATH in plan.committed_manifest.tombstones
    assert RETIRED_PATH not in plan.committed_manifest.evidence_baselines
    assert _retired_concept(_view(plan)).facets.structure.evidence is EvidenceState.UNKNOWN


def test_source_retirement_preserves_explicit_authored_active_lifecycle(tmp_path):
    inputs = _retirement_inputs(tmp_path)
    model = parse_knowledge_index(json.loads(
        build_knowledge_generation_plan(inputs).knowledge_index.content
    ))
    ledger = reconcile_concepts(
        GovernanceLedger.empty("kb_retirement"),
        concept_references_from_knowledge(model),
    )
    uid = next(
        uid for uid, allocation in ledger.concepts.items()
        if allocation.locator == "llm-wiki://entities/User"
    )
    ledger = set_lifecycle(
        ledger,
        uid,
        Lifecycle.ACTIVE,
        actor=GovernanceActor(kind="human", actor_id="reviewer"),
        authored_at="2026-10-12T10:00:00Z",
    )
    before = deepcopy(ledger)

    plan = build_knowledge_generation_plan(replace(inputs, governance=ledger))
    concept = _retired_concept(_view(plan))

    assert concept.lifecycle is Lifecycle.ACTIVE
    assert concept.extensions[GOVERNANCE_EXTENSION_KEY]["uid"] == uid
    assert concept.extensions[SOURCE_RETIREMENT_EXTENSION_KEY]["state"] == "source-member-removed"
    assert len(ledger.lifecycle_events) == 1
    assert ledger == before


def test_retirement_coverage_excludes_only_bound_canonical_page(tmp_path):
    inputs = _retirement_inputs(tmp_path)
    plan = build_knowledge_generation_plan(inputs)
    entities = tmp_path / "entities"
    entities.mkdir()
    for name in ("User", "AccountService", "Unbound"):
        (entities / f"{name}.md").write_text(SOURCE_MEMBER_REMOVED_HEADER)
    report = LintReport(str(tmp_path), "source")

    _check_entity_coverage(
        report, tmp_path, dict(inputs.inventory), manifest=plan.committed_manifest
    )

    assert [(issue.category, issue.target) for issue in report.issues] == [
        ("stale_entities", "Unbound")
    ]


def test_retirement_header_alone_cannot_relax_coverage_or_unknown_promise(tmp_path):
    inputs = _retirement_inputs(tmp_path, unknown=True)
    inputs = replace(
        inputs,
        manifest_generation_inputs={"options": {"deep": True}},
        content_by_page={
            **inputs.content_by_page,
            RETIRED_PATH: SOURCE_MEMBER_REMOVED_HEADER + inputs.content_by_page[RETIRED_PATH],
        },
    )
    plan = build_knowledge_generation_plan(inputs)
    entities = tmp_path / "entities"
    entities.mkdir()
    (entities / "User.md").write_text(inputs.content_by_page[RETIRED_PATH])
    (entities / "AccountService.md").write_text("# AccountService\n")
    report = LintReport(str(tmp_path), "source", strict=True)

    _check_entity_coverage(
        report, tmp_path, dict(inputs.inventory), manifest=plan.committed_manifest
    )
    _check_knowledge_concepts(report, _view(plan))

    assert any(issue.category == "stale_entities" and issue.target == "User" for issue in report.issues)
    assert any("promised-evidence-unknown" in issue.message for issue in report.issues)
    assert report.diagnostics == []


@pytest.mark.parametrize("marker", [None, False, {}, {"schema_version": "forged", "pages": {}}])
def test_malformed_retirement_marker_fails_generation_and_lint(tmp_path, marker):
    inputs = _retirement_inputs(tmp_path)
    plan = build_knowledge_generation_plan(inputs)
    manifest = replace(
        plan.committed_manifest,
        generation_inputs={"entity_retirement": marker},
    )
    with pytest.raises(KnowledgeGenerationError, match="entity_retirement"):
        build_knowledge_generation_plan(replace(inputs, next_manifest=manifest))
    report = LintReport(str(tmp_path), "source", strict=True)
    _check_knowledge_concepts(report, replace(_view(plan), manifest_basis=manifest))
    assert any(issue.reason_code == "source-retirement-invalid" for issue in report.issues)
    assert report.diagnostics == []


@pytest.mark.parametrize("mutation", ["remove", "mismatch", "unmarked"])
def test_native_retirement_extension_must_match_manifest(tmp_path, mutation):
    plan = build_knowledge_generation_plan(_retirement_inputs(tmp_path))
    view = _view(plan)
    assert view.knowledge is not None
    concept = _retired_concept(view)
    if mutation == "unmarked":
        assert view.manifest_basis is not None
        view = replace(view, manifest_basis=replace(view.manifest_basis, generation_inputs={}))
    else:
        extensions = dict(concept.extensions)
        if mutation == "remove":
            extensions.pop(SOURCE_RETIREMENT_EXTENSION_KEY)
        else:
            extensions[SOURCE_RETIREMENT_EXTENSION_KEY] = {"state": "source-member-removed"}
        view = replace(view, knowledge=replace(
            view.knowledge,
            concepts=tuple(
                replace(item, extensions=extensions) if item.locator == concept.locator else item
                for item in view.knowledge.concepts
            ),
        ))
    report = LintReport(str(tmp_path), "source", strict=True)

    _check_knowledge_concepts(report, view)

    assert any(issue.reason_code == "source-retirement-projection-mismatch" for issue in report.issues)
    assert report.diagnostics == []


@pytest.mark.parametrize("mutation", ["missing", "null", "coordinate", "unmarked"])
def test_generic_native_artifact_read_rejects_retirement_projection_drift(
    tmp_path, mutation
):
    plan = build_knowledge_generation_plan(_retirement_inputs(tmp_path))
    manifest = plan.committed_manifest
    payload = json.loads(plan.knowledge_index.content)
    concept = next(
        item for item in payload["concepts"]
        if item["document"]["canonical_path"] == RETIRED_PATH
    )
    if mutation == "unmarked":
        manifest = replace(manifest, generation_inputs={})
    elif mutation == "missing":
        concept["extensions"].pop(SOURCE_RETIREMENT_EXTENSION_KEY)
    elif mutation == "null":
        concept["extensions"][SOURCE_RETIREMENT_EXTENSION_KEY] = None
    else:
        concept["extensions"][SOURCE_RETIREMENT_EXTENSION_KEY]["occurrence"] = 2

    with pytest.raises(KnowledgeArtifactError, match="source retirement binding"):
        validate_knowledge_artifacts(
            surface_index_bytes=plan.surface_index.content,
            knowledge_index_bytes=serialize_knowledge_index(payload).encode("utf-8"),
            manifest=manifest,
        )


@pytest.mark.parametrize("marker", [None, False, {}])
def test_generic_native_artifact_read_rejects_malformed_retirement_marker(
    tmp_path, marker
):
    plan = build_knowledge_generation_plan(_retirement_inputs(tmp_path))
    manifest = replace(plan.committed_manifest, generation_inputs={"entity_retirement": marker})

    with pytest.raises(KnowledgeArtifactError, match="entity_retirement"):
        validate_knowledge_artifacts(
            surface_index_bytes=plan.surface_index.content,
            knowledge_index_bytes=plan.knowledge_index.content,
            manifest=manifest,
        )


@pytest.mark.parametrize("path", ["modules/User.md", "entities/../User.md", "entities/..md"])
def test_malformed_retirement_paths_fail_with_owned_diagnostic(tmp_path, path):
    inputs = _retirement_inputs(tmp_path)
    assert inputs.previous_manifest is not None
    owner = inputs.previous_manifest.page_source_mappings[RETIRED_PATH]
    marker = {
        "entity_retirement": {
            "schema_version": "llm-wiki-entity-retirement/v1",
            "pages": {path: owner.to_payload()},
        }
    }

    with pytest.raises(SourceRetirementError):
        read_entity_retirement_state(marker)


@pytest.mark.parametrize("mutation", ["owner", "mapping", "tombstone", "revived"])
def test_retirement_binding_cannot_be_forged_against_current_manifest(tmp_path, mutation):
    plan = build_knowledge_generation_plan(_retirement_inputs(tmp_path))
    manifest = plan.committed_manifest
    if mutation == "owner":
        manifest = replace(manifest, generation_inputs=with_entity_retirement_state(
            manifest.generation_inputs,
            {RETIRED_PATH: replace(manifest.page_source_mappings[RETIRED_PATH], occurrence=2)},
        ))
    elif mutation == "mapping":
        manifest = replace(manifest, page_source_mappings={
            path: owner for path, owner in manifest.page_source_mappings.items()
            if path != RETIRED_PATH
        })
    elif mutation == "tombstone":
        manifest = replace(manifest, tombstones={})
    else:
        sources = deepcopy(dict(manifest.sources))
        sources[FIXTURE_SOURCE_PATH]["entities"].append("User")
        manifest = replace(manifest, sources=sources)

    with pytest.raises(SourceRetirementError):
        retired_entity_mappings(manifest)


@pytest.mark.parametrize("membership", [None, "User", {}, [None], [""], "missing"])
def test_retirement_cannot_infer_absence_from_malformed_surviving_source_membership(
    tmp_path, membership
):
    plan = build_knowledge_generation_plan(_retirement_inputs(tmp_path))
    sources = deepcopy(dict(plan.committed_manifest.sources))
    if membership == "missing":
        sources[FIXTURE_SOURCE_PATH].pop("entities")
    else:
        sources[FIXTURE_SOURCE_PATH]["entities"] = membership

    with pytest.raises(SourceRetirementError):
        retired_entity_mappings(replace(plan.committed_manifest, sources=sources))
