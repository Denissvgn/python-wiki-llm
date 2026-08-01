"""Commit-protocol tests for generated knowledge artifacts."""

from __future__ import annotations

import json
from dataclasses import replace

import pytest

from llm_wiki_cli.services import io, knowledge_artifacts
from llm_wiki_cli.services.knowledge_artifacts import (
    KNOWLEDGE_INDEX_FILENAME,
    ArtifactWriteState,
    CommitStage,
    KnowledgeArtifactError,
    build_knowledge_commit_plan,
    commit_knowledge_artifacts,
    validate_surface_index_bytes,
)
from llm_wiki_cli.services.knowledge_evidence import sha256_bytes
from llm_wiki_cli.services.knowledge_index import (
    build_knowledge_index,
    serialize_knowledge_index,
)
from llm_wiki_cli.services.sync_manifest import (
    MANIFEST_FILENAME,
    SyncManifest,
)
from llm_wiki_cli.services.wiki_surface_index import SURFACE_INDEX_FILENAME
from tests.knowledge_fixtures import (
    duplicate_entity_occurrences_fixture,
    one_module_two_entities_fixture,
)
from tests.test_knowledge_index import _builder_case_for


def _plan(tmp_path, fixture):
    case = _builder_case_for(fixture)
    model = build_knowledge_index(case.inputs)
    manifest = SyncManifest(
        sources={
            path: {
                "hash": sha256_bytes(content.encode("utf-8")),
                "language": fixture.inventory[path].get("language"),
            }
            for path, content in fixture.source_files.items()
        },
        page_source_mappings=dict(case.inputs.page_source_mappings),
        evidence_baselines=dict(case.inputs.evidence_baselines),
        tombstones=dict(case.inputs.tombstones),
    )
    return build_knowledge_commit_plan(
        tmp_path,
        surface_index_bytes=fixture.surface_bytes,
        knowledge_index_bytes=serialize_knowledge_index(model).encode("utf-8"),
        manifest=manifest,
    )


def _surface_variant(plan, mutate):
    surface = json.loads(plan.surface_index.content)
    mutate(surface)
    surface_bytes = (
        json.dumps(surface, indent=2, sort_keys=True, allow_nan=False) + "\n"
    ).encode("utf-8")
    knowledge = json.loads(plan.knowledge_index.content)
    knowledge["bundle"]["snapshot"]["surface_index_hash"] = sha256_bytes(surface_bytes)
    knowledge_bytes = serialize_knowledge_index(knowledge).encode("utf-8")
    return surface_bytes, knowledge_bytes


def _remove_last_surface_page_with_consistent_counts(surface):
    removed = surface["pages"].pop()
    surface["counts"]["total"] -= 1
    surface["counts"]["by_kind"][removed["kind"]] -= 1


def _canonical_surface_bytes(payload):
    return (
        json.dumps(payload, indent=2, sort_keys=True, allow_nan=False) + "\n"
    ).encode("utf-8")


def _surface_payload_with_flow(plan):
    surface = json.loads(plan.surface_index.content)
    page = next(page for page in surface["pages"] if page["kind"] == "workflows")
    page.update(
        {
            "kind": "flows",
            "canonical_path": f"flows/{page['id']}.md",
            "mcp_uri": f"llm-wiki://flows/{page['id']}",
            "source_path": "src/accounts.py",
        }
    )
    surface["counts"]["by_kind"]["workflows"] -= 1
    surface["counts"]["by_kind"]["flows"] += 1
    surface["flows"] = [
        {
            "id": page["id"],
            "category": "onboarding",
            "entry_point": {
                "symbol": "start_onboarding",
                "source_path": page["source_path"],
                "label": "Start onboarding",
            },
        }
    ]
    return surface


def test_commit_writes_projections_then_manifest_and_commits_exact_hashes(tmp_path):
    fixture = one_module_two_entities_fixture()
    plan = _plan(tmp_path, fixture)
    stages = []

    result = commit_knowledge_artifacts(plan, fault_injector=stages.append)

    assert stages == [
        CommitStage.SURFACE_INDEX_WRITTEN,
        CommitStage.KNOWLEDGE_INDEX_WRITTEN,
        CommitStage.MANIFEST_WRITTEN,
    ]
    assert result.surface_index.state is ArtifactWriteState.CREATED
    assert result.knowledge_index.state is ArtifactWriteState.CREATED
    assert result.manifest.state is ArtifactWriteState.CREATED
    assert (tmp_path / SURFACE_INDEX_FILENAME).read_bytes() == fixture.surface_bytes
    assert (tmp_path / KNOWLEDGE_INDEX_FILENAME).read_bytes() == (
        plan.knowledge_index.content
    )
    loaded = SyncManifest.load(tmp_path)
    assert loaded == result.committed_manifest
    assert loaded.artifact_hashes is not None
    assert loaded.artifact_hashes.surface_index_hash == plan.surface_index.content_hash
    assert loaded.artifact_hashes.knowledge_index_hash == (
        plan.knowledge_index.content_hash
    )
    assert loaded.artifact_hashes.evaluated_envelope_hash == (
        plan.evaluated_envelope_hash
    )
    assert not list(tmp_path.glob(".*.tmp"))


def test_repeating_an_unchanged_commit_writes_nothing(tmp_path, monkeypatch):
    fixture = one_module_two_entities_fixture()
    commit_knowledge_artifacts(_plan(tmp_path, fixture))
    unchanged = _plan(tmp_path, fixture)

    assert not unchanged.changed
    assert {
        unchanged.surface_index.state,
        unchanged.knowledge_index.state,
        unchanged.manifest.state,
    } == {ArtifactWriteState.UNCHANGED}

    def unexpected_write(*_args, **_kwargs):
        raise AssertionError("unchanged commit attempted a write")

    monkeypatch.setattr(knowledge_artifacts, "write_bytes_atomic", unexpected_write)
    result = commit_knowledge_artifacts(unchanged)

    assert not result.changed


def test_dry_run_calculates_complete_plan_without_writes_or_faults(tmp_path):
    fixture = one_module_two_entities_fixture()

    result = commit_knowledge_artifacts(
        _plan(tmp_path, fixture),
        dry_run=True,
        fault_injector=lambda _stage: pytest.fail("dry-run invoked fault seam"),
    )

    assert result.dry_run
    assert result.changed
    assert not (tmp_path / SURFACE_INDEX_FILENAME).exists()
    assert not (tmp_path / KNOWLEDGE_INDEX_FILENAME).exists()
    assert not (tmp_path / MANIFEST_FILENAME).exists()


@pytest.mark.parametrize(
    "failure_stage",
    [
        CommitStage.SURFACE_INDEX_WRITTEN,
        CommitStage.KNOWLEDGE_INDEX_WRITTEN,
    ],
)
def test_projection_failure_keeps_prior_manifest_commit_marker(
    tmp_path,
    failure_stage,
):
    initial = one_module_two_entities_fixture()
    replacement = duplicate_entity_occurrences_fixture()
    initial_result = commit_knowledge_artifacts(_plan(tmp_path, initial))
    replacement_plan = _plan(tmp_path, replacement)
    prior_marker = (tmp_path / MANIFEST_FILENAME).read_bytes()

    def fail(stage):
        if stage is failure_stage:
            raise RuntimeError(f"injected after {stage.value}")

    with pytest.raises(RuntimeError, match="injected after"):
        commit_knowledge_artifacts(replacement_plan, fault_injector=fail)

    assert (tmp_path / MANIFEST_FILENAME).read_bytes() == prior_marker
    assert SyncManifest.load(tmp_path) == initial_result.committed_manifest
    assert not list(tmp_path.glob(".*.tmp"))


def test_orphan_projection_recovery_replaces_manifest_last_even_when_bytes_match(
    tmp_path,
):
    fixture = one_module_two_entities_fixture()
    committed = commit_knowledge_artifacts(_plan(tmp_path, fixture))
    (tmp_path / KNOWLEDGE_INDEX_FILENAME).unlink()
    marker_bytes = (tmp_path / MANIFEST_FILENAME).read_bytes()
    recovered_plan = _plan(tmp_path, fixture)
    stages = []

    assert recovered_plan.knowledge_index.state is ArtifactWriteState.CREATED
    assert recovered_plan.manifest.state is ArtifactWriteState.UPDATED
    commit_knowledge_artifacts(recovered_plan, fault_injector=stages.append)

    assert stages == [
        CommitStage.KNOWLEDGE_INDEX_WRITTEN,
        CommitStage.MANIFEST_WRITTEN,
    ]
    assert (tmp_path / MANIFEST_FILENAME).read_bytes() == marker_bytes
    assert SyncManifest.load(tmp_path) == committed.committed_manifest


def test_commit_rejects_projection_with_mismatched_surface_commitment(tmp_path):
    surface_fixture = one_module_two_entities_fixture()
    knowledge_fixture = duplicate_entity_occurrences_fixture()
    knowledge_plan = _plan(tmp_path / "valid", knowledge_fixture)

    with pytest.raises(KnowledgeArtifactError) as exc_info:
        build_knowledge_commit_plan(
            tmp_path,
            surface_index_bytes=surface_fixture.surface_bytes,
            knowledge_index_bytes=knowledge_plan.knowledge_index.content,
            manifest=knowledge_plan.committed_manifest.without_artifact_hashes(),
        )

    assert exc_info.value.field == (
        "knowledge_index.bundle.snapshot.surface_index_hash"
    )


def test_commit_rejects_noncanonical_knowledge_bytes(tmp_path):
    fixture = one_module_two_entities_fixture()
    valid_plan = _plan(tmp_path / "valid", fixture)
    noncanonical = valid_plan.knowledge_index.content.replace(
        b'  "bundle"',
        b'   "bundle"',
        1,
    )

    with pytest.raises(KnowledgeArtifactError) as exc_info:
        build_knowledge_commit_plan(
            tmp_path,
            surface_index_bytes=fixture.surface_bytes,
            knowledge_index_bytes=noncanonical,
            manifest=valid_plan.committed_manifest.without_artifact_hashes(),
        )

    assert exc_info.value.field == "knowledge_index_bytes"


def test_commit_plan_replaces_stale_caller_artifact_hashes(tmp_path):
    fixture = one_module_two_entities_fixture()
    valid_plan = _plan(tmp_path / "valid", fixture)
    manifest = valid_plan.committed_manifest.without_artifact_hashes()
    manifest = replace(
        manifest,
        artifact_hashes=SyncManifest()
        .with_artifact_hashes(
            surface_index_hash="sha256:" + "1" * 64,
            knowledge_index_hash="sha256:" + "2" * 64,
            evaluated_envelope_hash="sha256:" + "3" * 64,
        )
        .artifact_hashes,
    )

    plan = build_knowledge_commit_plan(
        tmp_path,
        surface_index_bytes=fixture.surface_bytes,
        knowledge_index_bytes=valid_plan.knowledge_index.content,
        manifest=manifest,
    )

    assert plan.committed_manifest.artifact_hashes is not None
    assert plan.committed_manifest.artifact_hashes.surface_index_hash == (
        plan.surface_index.content_hash
    )


def test_commit_rejects_surface_page_parity_gap(tmp_path):
    fixture = one_module_two_entities_fixture()
    valid = _plan(tmp_path / "valid", fixture)
    surface_bytes, knowledge_bytes = _surface_variant(
        valid,
        _remove_last_surface_page_with_consistent_counts,
    )

    with pytest.raises(KnowledgeArtifactError) as exc_info:
        build_knowledge_commit_plan(
            tmp_path,
            surface_index_bytes=surface_bytes,
            knowledge_index_bytes=knowledge_bytes,
            manifest=valid.committed_manifest.without_artifact_hashes(),
        )

    assert exc_info.value.field == "surface_index.pages"


@pytest.mark.parametrize(
    ("mutate", "expected_field"),
    [
        (
            lambda surface: surface["counts"].__setitem__(
                "total", surface["counts"]["total"] + 1
            ),
            "surface_index.counts.total",
        ),
        (
            lambda surface: surface["counts"]["by_kind"].__setitem__(
                "modules", surface["counts"]["by_kind"]["modules"] + 1
            ),
            "surface_index.counts.by_kind.modules",
        ),
        (
            lambda surface: surface["counts"].__setitem__("dependency_architecture", 1),
            "surface_index.counts.dependency_architecture",
        ),
        (
            lambda surface: surface["dependency_pages"].__setitem__(
                "dependencies", True
            ),
            "surface_index.dependency_pages.dependencies",
        ),
        (
            lambda surface: surface["counts"]["assets"].__setitem__(
                "total", surface["counts"]["assets"]["total"] + 1
            ),
            "surface_index.counts.assets.total",
        ),
    ],
)
def test_surface_validation_rejects_inconsistent_summary_counts(
    tmp_path,
    mutate,
    expected_field,
):
    surface = json.loads(
        _plan(
            tmp_path / "valid", one_module_two_entities_fixture()
        ).surface_index.content
    )
    mutate(surface)

    with pytest.raises(KnowledgeArtifactError) as exc_info:
        validate_surface_index_bytes(_canonical_surface_bytes(surface))

    assert exc_info.value.field == expected_field


def test_surface_validation_accepts_flow_page_with_matching_summary(tmp_path):
    plan = _plan(tmp_path / "valid", one_module_two_entities_fixture())
    surface = _surface_payload_with_flow(plan)

    assert (
        validate_surface_index_bytes(_canonical_surface_bytes(surface))["flows"]
        == (surface["flows"])
    )


def test_surface_validation_accepts_additive_bounded_flow_evidence(tmp_path):
    plan = _plan(tmp_path / "valid", one_module_two_entities_fixture())
    surface = _surface_payload_with_flow(plan)
    surface["flows"][0].update(
        {
            "detector": "builtin",
            "language": "python",
            "routes": [
                {
                    "method": "POST",
                    "path": "/accounts",
                    "operation_id": None,
                }
            ],
            "evidence": {
                "flow": {
                    "step_count": 2,
                    "truncated": False,
                    "modules_touched": ["src/accounts.py"],
                },
                "data_flow": {
                    "generated": True,
                    "step_count": 2,
                    "transfer_count": 1,
                    "truncated": False,
                    "boundary_effects": [
                        {
                            "step": "start_onboarding",
                            "step_index": 1,
                            "kind": "database_write",
                            "target": "accounts",
                            "line": 7,
                            "confidence": "high",
                        }
                    ],
                    "gaps": [
                        {
                            "kind": "unresolved_call",
                            "step": "start_onboarding",
                            "target": "publish",
                            "line": 8,
                        }
                    ],
                },
            },
        }
    )

    validated = validate_surface_index_bytes(_canonical_surface_bytes(surface))

    assert validated["flows"] == surface["flows"]


@pytest.mark.parametrize(
    ("mutate", "expected_field"),
    [
        (
            lambda flow: flow.__setitem__("detector", None),
            "surface_index.flows[0].detector",
        ),
        (
            lambda flow: flow.__setitem__(
                "routes", [{"method": "POST", "path": "/accounts"}]
            ),
            "surface_index.flows[0].routes[0].operation_id",
        ),
        (
            lambda flow: flow.__setitem__(
                "evidence",
                {
                    "flow": {
                        "step_count": 1,
                        "truncated": False,
                        "modules_touched": ["../outside.py"],
                    },
                    "data_flow": None,
                },
            ),
            "surface_index.flows[0].evidence.flow.modules_touched[0]",
        ),
    ],
)
def test_surface_validation_rejects_malformed_additive_flow_evidence(
    tmp_path,
    mutate,
    expected_field,
):
    plan = _plan(tmp_path / "valid", one_module_two_entities_fixture())
    surface = _surface_payload_with_flow(plan)
    mutate(surface["flows"][0])

    with pytest.raises(KnowledgeArtifactError) as exc_info:
        validate_surface_index_bytes(_canonical_surface_bytes(surface))

    assert exc_info.value.field == expected_field


@pytest.mark.parametrize(
    ("mutate", "expected_field"),
    [
        (
            lambda surface: surface.__setitem__("flows", []),
            "surface_index.flows",
        ),
        (
            lambda surface: surface["flows"][0].__setitem__("id", "missing"),
            "surface_index.flows[0].id",
        ),
        (
            lambda surface: surface["flows"][0]["entry_point"].__setitem__(
                "source_path", "src/other.py"
            ),
            "surface_index.flows[0].entry_point.source_path",
        ),
        (
            lambda surface: surface["flows"].append(dict(surface["flows"][0])),
            "surface_index.flows[1].id",
        ),
    ],
)
def test_surface_validation_rejects_flow_summary_disagreement(
    tmp_path,
    mutate,
    expected_field,
):
    plan = _plan(tmp_path / "valid", one_module_two_entities_fixture())
    surface = _surface_payload_with_flow(plan)
    mutate(surface)

    with pytest.raises(KnowledgeArtifactError) as exc_info:
        validate_surface_index_bytes(_canonical_surface_bytes(surface))

    assert exc_info.value.field == expected_field


@pytest.mark.parametrize(
    ("mutate", "expected_field"),
    [
        (
            lambda surface: surface["pages"][0].__setitem__(
                "canonical_path",
                "../escape.md",
            ),
            "surface_index.pages[0].canonical_path",
        ),
        (
            lambda surface: surface["pages"][0].__setitem__(
                "source_path",
                "/etc/passwd",
            ),
            "surface_index.pages[0].source_path",
        ),
    ],
)
def test_commit_rejects_unsafe_surface_paths(tmp_path, mutate, expected_field):
    fixture = one_module_two_entities_fixture()
    valid = _plan(tmp_path / "valid", fixture)
    surface_bytes, knowledge_bytes = _surface_variant(valid, mutate)

    with pytest.raises(KnowledgeArtifactError) as exc_info:
        build_knowledge_commit_plan(
            tmp_path,
            surface_index_bytes=surface_bytes,
            knowledge_index_bytes=knowledge_bytes,
            manifest=valid.committed_manifest.without_artifact_hashes(),
        )

    assert exc_info.value.field == expected_field


def test_commit_rejects_manifest_without_active_structural_evidence(tmp_path):
    fixture = one_module_two_entities_fixture()
    valid = _plan(tmp_path / "valid", fixture)

    with pytest.raises(KnowledgeArtifactError) as exc_info:
        build_knowledge_commit_plan(
            tmp_path,
            surface_index_bytes=valid.surface_index.content,
            knowledge_index_bytes=valid.knowledge_index.content,
            manifest=SyncManifest(),
        )

    assert exc_info.value.field == "manifest.evidence_state"


@pytest.mark.parametrize(
    "invalid_hash",
    [
        None,
        "",
        "0" * 64,
        "sha256:" + "A" * 64,
    ],
)
def test_commit_rejects_missing_or_malformed_active_manifest_source_hash(
    tmp_path,
    invalid_hash,
):
    fixture = one_module_two_entities_fixture()
    valid = _plan(tmp_path / "valid", fixture)
    manifest = valid.committed_manifest.without_artifact_hashes()
    source_path = next(iter(manifest.sources))
    sources = {path: dict(value) for path, value in manifest.sources.items()}
    if invalid_hash is None:
        sources[source_path].pop("hash")
    else:
        sources[source_path]["hash"] = invalid_hash

    with pytest.raises(KnowledgeArtifactError) as exc_info:
        build_knowledge_commit_plan(
            tmp_path,
            surface_index_bytes=valid.surface_index.content,
            knowledge_index_bytes=valid.knowledge_index.content,
            manifest=replace(manifest, sources=sources),
        )

    assert exc_info.value.field == f"manifest.sources.{source_path}.hash"


def test_commit_rejects_active_manifest_source_hash_basis_disagreement(tmp_path):
    fixture = one_module_two_entities_fixture()
    valid = _plan(tmp_path / "valid", fixture)
    manifest = valid.committed_manifest.without_artifact_hashes()
    source_path = next(iter(manifest.sources))
    sources = {path: dict(value) for path, value in manifest.sources.items()}
    sources[source_path]["hash"] = "sha256:" + "f" * 64

    with pytest.raises(KnowledgeArtifactError) as exc_info:
        build_knowledge_commit_plan(
            tmp_path,
            surface_index_bytes=valid.surface_index.content,
            knowledge_index_bytes=valid.knowledge_index.content,
            manifest=replace(manifest, sources=sources),
        )

    assert exc_info.value.field.startswith("manifest.evidence_baselines.")
    assert exc_info.value.field.endswith(".basis.source_content_hash")


def test_commit_ignores_hashless_inactive_legacy_manifest_source(tmp_path):
    fixture = one_module_two_entities_fixture()
    valid = _plan(tmp_path / "valid", fixture)
    manifest = valid.committed_manifest.without_artifact_hashes()
    sources = {path: dict(value) for path, value in manifest.sources.items()}
    sources["legacy/removed.py"] = {"language": "python"}

    plan = build_knowledge_commit_plan(
        tmp_path,
        surface_index_bytes=valid.surface_index.content,
        knowledge_index_bytes=valid.knowledge_index.content,
        manifest=replace(manifest, sources=sources),
    )

    assert "legacy/removed.py" in plan.committed_manifest.sources


def test_readback_change_before_manifest_prevents_commit_marker_replacement(tmp_path):
    first = one_module_two_entities_fixture()
    second = duplicate_entity_occurrences_fixture()
    initial = commit_knowledge_artifacts(_plan(tmp_path, first))
    replacement = _plan(tmp_path, second)
    prior_marker = (tmp_path / MANIFEST_FILENAME).read_bytes()

    def tamper_after_knowledge(stage):
        if stage is CommitStage.KNOWLEDGE_INDEX_WRITTEN:
            (tmp_path / SURFACE_INDEX_FILENAME).write_bytes(b"tampered\n")

    with pytest.raises(KnowledgeArtifactError) as exc_info:
        commit_knowledge_artifacts(
            replacement,
            fault_injector=tamper_after_knowledge,
        )

    assert exc_info.value.field == SURFACE_INDEX_FILENAME
    assert (tmp_path / MANIFEST_FILENAME).read_bytes() == prior_marker
    assert SyncManifest.load(tmp_path) == initial.committed_manifest


def test_manifest_atomic_replace_failure_keeps_prior_marker_and_cleans_temp(
    tmp_path,
    monkeypatch,
):
    first = one_module_two_entities_fixture()
    second = duplicate_entity_occurrences_fixture()
    initial = commit_knowledge_artifacts(_plan(tmp_path, first))
    replacement = _plan(tmp_path, second)
    prior_marker = (tmp_path / MANIFEST_FILENAME).read_bytes()
    real_replace = io.os.replace

    def fail_manifest_replace(source, destination):
        if destination == tmp_path / MANIFEST_FILENAME:
            raise OSError("injected manifest replace failure")
        return real_replace(source, destination)

    monkeypatch.setattr(io.os, "replace", fail_manifest_replace)

    with pytest.raises(OSError, match="manifest replace failure"):
        commit_knowledge_artifacts(replacement)

    assert (tmp_path / MANIFEST_FILENAME).read_bytes() == prior_marker
    assert SyncManifest.load(tmp_path) == initial.committed_manifest
    assert not list(tmp_path.glob(".*.tmp"))


def test_failure_after_manifest_write_leaves_a_complete_valid_marker(tmp_path):
    fixture = one_module_two_entities_fixture()
    plan = _plan(tmp_path, fixture)

    def fail_after_manifest(stage):
        if stage is CommitStage.MANIFEST_WRITTEN:
            raise RuntimeError("injected after manifest")

    with pytest.raises(RuntimeError, match="after manifest"):
        commit_knowledge_artifacts(plan, fault_injector=fail_after_manifest)

    assert SyncManifest.load(tmp_path) == plan.committed_manifest
    assert (tmp_path / SURFACE_INDEX_FILENAME).read_bytes() == (
        plan.surface_index.content
    )
    assert (tmp_path / KNOWLEDGE_INDEX_FILENAME).read_bytes() == (
        plan.knowledge_index.content
    )
