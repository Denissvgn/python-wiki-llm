"""Focused tests for the shared KNOW-109/110 generation planner."""

from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path

import pytest

from llm_wiki_cli.services import sync_manifest
from llm_wiki_cli.services.knowledge_artifacts import (
    ArtifactWriteState,
    commit_knowledge_artifacts,
)
from llm_wiki_cli.services.knowledge_envelope import (
    ConsumedInput,
    ConsumedInputKind,
    ProducerComponentInput,
    RepositoryEvidence,
    hash_generation_options,
)
from llm_wiki_cli.services.knowledge_evidence import sha256_bytes
from llm_wiki_cli.services.knowledge_generation import (
    KnowledgeGenerationError,
    KnowledgeGenerationInputs,
    build_knowledge_generation_plan,
)
from llm_wiki_cli.services.knowledge_model import (
    RelationshipKind,
    WorkingTreeState,
    parse_knowledge_index,
)
from llm_wiki_cli.services.knowledge_orchestration import (
    RUNTIME_GENERATION_OPTION_DEFAULTS,
    RuntimeKnowledgeInputs,
    build_runtime_knowledge_plan,
    persist_runtime_generation_policy,
    runtime_generation_options,
)
from llm_wiki_cli.services.source_snapshot import SourceSnapshot
from llm_wiki_cli.services.sync_manifest import TOMBSTONE_SOURCE_MISSING
from llm_wiki_cli.services.wiki_surface_index import SurfaceIndexEvaluation
from tests.knowledge_fixtures import (
    FIXTURE_REPOSITORY_IDENTITY,
    EvaluatedKnowledgeFixture,
    one_module_two_entities_fixture,
)
from tests.test_knowledge_index import _surface_pages


def _planner_inputs(
    tmp_path: Path,
    fixture: EvaluatedKnowledgeFixture | None = None,
) -> KnowledgeGenerationInputs:
    selected = fixture or one_module_two_entities_fixture()
    source_hashes = {
        path: sha256_bytes(content.encode("utf-8"))
        for path, content in selected.source_files.items()
    }
    return KnowledgeGenerationInputs(
        wiki_dir=tmp_path,
        inventory=selected.inventory,
        pages=_surface_pages(selected),
        content_by_page={page.canonical_path: page.content for page in selected.pages},
        surface_index_bytes=selected.surface_bytes,
        surface_index_payload=None,
        source_content_hashes=source_hashes,
        consumed_inputs=tuple(
            ConsumedInput(
                path=path,
                content_hash=content_hash,
                kind=ConsumedInputKind.SOURCE,
            )
            for path, content_hash in source_hashes.items()
        ),
        module_page_map=selected.module_page_map,
        entity_occurrence_page_map=selected.entity_occurrence_page_map,
        extractor_ref_by_source={path: "python-ast" for path in selected.inventory},
        inventory_complete_by_source={path: True for path in selected.inventory},
        repository_evidence=RepositoryEvidence(
            evaluated_revision="0123456789abcdef0123456789abcdef01234567",
            working_tree=WorkingTreeState.CLEAN,
        ),
        configured_public_identity=FIXTURE_REPOSITORY_IDENTITY,
        generation_options={"deep": True},
        generation_option_defaults={"deep": False},
        generation_option_allowlist=("deep",),
        tool=ProducerComponentInput(
            component_id="agent-wiki-cli",
            version="1.4.0",
            configuration={"knowledge_schema": "llm-wiki-knowledge/v1"},
        ),
        extractors=(
            ProducerComponentInput(
                component_id="python-ast",
                version="stdlib",
                configuration={"inventory_mode": "deep"},
                limitations=("syntax-only",),
            ),
        ),
        asset_paths=frozenset(selected.assets),
        manifest_surfaces={"flows": {"enabled": True}},
        manifest_generation_inputs={"options": {"deep": True}},
    )


def test_planner_builds_one_complete_commit_from_evaluated_inputs(tmp_path):
    inputs = _planner_inputs(tmp_path)

    plan = build_knowledge_generation_plan(inputs)
    knowledge = parse_knowledge_index(json.loads(plan.knowledge_index.content))

    assert plan.surface_index.content == inputs.surface_index_bytes
    assert plan.surface_index.state is ArtifactWriteState.CREATED
    assert plan.knowledge_index.state is ArtifactWriteState.CREATED
    assert plan.manifest.state is ArtifactWriteState.CREATED
    assert plan.committed_manifest.artifact_hashes is not None
    assert plan.committed_manifest.artifact_hashes.surface_index_hash == (
        plan.surface_index.content_hash
    )
    assert plan.committed_manifest.artifact_hashes.knowledge_index_hash == (
        plan.knowledge_index.content_hash
    )
    assert set(plan.committed_manifest.evidence_baselines) == {
        page.relative_path
        for page in inputs.pages
        if page.kind.value in {"modules", "entities"}
    }
    assert all(
        baseline.is_known
        for baseline in plan.committed_manifest.evidence_baselines.values()
    )
    assert any(
        relationship.kind is RelationshipKind.LINKS_TO
        for relationship in knowledge.relationships
    )
    assert knowledge.bundle.repository.identity == FIXTURE_REPOSITORY_IDENTITY
    assert knowledge.bundle.snapshot.surface_index_hash == (
        plan.surface_index.content_hash
    )


def test_runtime_projects_selected_plugin_and_effective_option_basis(tmp_path):
    fixture = one_module_two_entities_fixture()
    content_by_page = {page.canonical_path: page.content for page in fixture.pages}
    source_hashes = {
        path: sha256_bytes(content.encode("utf-8"))
        for path, content in fixture.source_files.items()
    }
    source_snapshot = SourceSnapshot(
        root=tmp_path,
        files_by_language={},
        dockerfile_candidates=(),
        compose_candidates=(),
        yaml_candidates=(),
        package_markers=(),
        unsupported_files_by_language={},
        all_source_paths=tuple(source_hashes),
        gitignore_fingerprint=sha256_bytes(b""),
        captured_content_hashes=source_hashes,
        captured_input_kinds={
            path: (ConsumedInputKind.SOURCE.value,) for path in source_hashes
        },
    )
    surface = SurfaceIndexEvaluation(
        pages=_surface_pages(fixture),
        content_by_path=content_by_page,
        payload=fixture.surface_payload,
        serialized_bytes=fixture.surface_bytes,
        existing_asset_paths=frozenset(fixture.assets),
    )
    plugin_component = {
        "type": "extractor",
        "id": "python-observer",
        "language": "python",
        "entry_point": "observer.extractor:PythonObserver",
        "parallel_safe": True,
        "plugin_id": "observer-plugin",
        "plugin_version": "2.1.0",
        "plugin_dir": "/private/plugin/install",
    }
    options = runtime_generation_options(
        surfaces={},
        include_tests=None,
        preserve_semantic=True,
    )
    runtime = RuntimeKnowledgeInputs(
        target_wiki_dir=tmp_path,
        inventory=fixture.inventory,
        surface=surface,
        source_snapshot=source_snapshot,
        module_page_map=fixture.module_page_map,
        entity_occurrence_page_map=fixture.entity_occurrence_page_map,
        repository_evidence=RepositoryEvidence(),
        inventory_complete=True,
        extractor_registry={"python": "observer.extractor:PythonObserver"},
        plugin_extractor_components=(plugin_component,),
        plugin_lock_path=".llm-wiki/plugins.lock.json",
        plugin_lock_hash=sha256_bytes(b'{"version":1}'),
        generation_options=options,
        generation_option_defaults=RUNTIME_GENERATION_OPTION_DEFAULTS,
        generation_option_allowlist=tuple(RUNTIME_GENERATION_OPTION_DEFAULTS),
    )

    baseline = parse_knowledge_index(
        json.loads(build_runtime_knowledge_plan(runtime).knowledge_index.content)
    )
    version_changed = parse_knowledge_index(
        json.loads(
            build_runtime_knowledge_plan(
                replace(
                    runtime,
                    plugin_extractor_components=(
                        {**plugin_component, "plugin_version": "2.2.0"},
                    ),
                )
            ).knowledge_index.content
        )
    )
    option_changed = parse_knowledge_index(
        json.loads(
            build_runtime_knowledge_plan(
                replace(
                    runtime,
                    generation_options=runtime_generation_options(
                        surfaces={},
                        include_tests=("tests/**",),
                        preserve_semantic=True,
                    ),
                )
            ).knowledge_index.content
        )
    )

    assert [item.component_id for item in baseline.bundle.producer.extractors] == [
        "observer-plugin/python-observer"
    ]
    assert [item.component_id for item in baseline.bundle.producer.plugins] == [
        "observer-plugin"
    ]
    assert baseline.bundle.producer.plugins[0].version == "2.1.0"
    assert version_changed.bundle.producer != baseline.bundle.producer
    assert (
        option_changed.bundle.snapshot.generation_options_hash
        != baseline.bundle.snapshot.generation_options_hash
    )
    assert option_changed.bundle.producer == baseline.bundle.producer
    assert "/private/plugin/install" not in (
        build_runtime_knowledge_plan(runtime).knowledge_index.content.decode("utf-8")
    )


def test_runtime_generation_hash_covers_complete_persisted_policy():
    def option_hash(
        *,
        data_flow_enabled: bool,
        dependency_graph_detail: str,
        workflows_enabled: bool,
    ) -> str:
        generation_inputs = persist_runtime_generation_policy(
            {},
            data_flow_enabled=data_flow_enabled,
            dependency_graph_detail=dependency_graph_detail,
            workflows_enabled=workflows_enabled,
        )
        options = runtime_generation_options(
            surfaces={"dependencies": {"enabled": True}},
            generation_inputs=generation_inputs,
            include_tests=None,
            preserve_semantic=True,
        )
        return hash_generation_options(
            options,
            defaults=RUNTIME_GENERATION_OPTION_DEFAULTS,
            allowlist=tuple(RUNTIME_GENERATION_OPTION_DEFAULTS),
        )

    baseline = option_hash(
        data_flow_enabled=True,
        dependency_graph_detail="auto",
        workflows_enabled=True,
    )
    changed = {
        option_hash(
            data_flow_enabled=False,
            dependency_graph_detail="auto",
            workflows_enabled=True,
        ),
        option_hash(
            data_flow_enabled=True,
            dependency_graph_detail="package",
            workflows_enabled=True,
        ),
        option_hash(
            data_flow_enabled=True,
            dependency_graph_detail="auto",
            workflows_enabled=False,
        ),
    }

    assert baseline not in changed
    assert len(changed) == 3


def test_planner_preserves_exact_surface_bytes_and_payload_uses_v1_wire_format(
    tmp_path,
):
    exact = _planner_inputs(tmp_path)
    exact_plan = build_knowledge_generation_plan(exact)
    payload_plan = build_knowledge_generation_plan(
        replace(
            exact,
            surface_index_bytes=None,
            surface_index_payload=one_module_two_entities_fixture().surface_payload,
        )
    )

    assert exact_plan.surface_index.content == exact.surface_index_bytes
    assert payload_plan.surface_index.content == exact.surface_index_bytes
    assert payload_plan.knowledge_index.content == exact_plan.knowledge_index.content
    assert payload_plan.manifest.content == exact_plan.manifest.content


def test_planner_reuses_captured_hashes_and_repeated_plan_is_unchanged(
    tmp_path,
    monkeypatch,
):
    inputs = _planner_inputs(tmp_path)
    first = build_knowledge_generation_plan(inputs)
    committed = commit_knowledge_artifacts(first)

    def unexpected_source_read(*_args, **_kwargs):
        raise AssertionError("planner reread a source file")

    monkeypatch.setattr(sync_manifest, "hash_file", unexpected_source_read)
    repeated = build_knowledge_generation_plan(
        replace(inputs, previous_manifest=committed.committed_manifest)
    )

    assert not repeated.changed
    assert {
        repeated.surface_index.state,
        repeated.knowledge_index.state,
        repeated.manifest.state,
    } == {ArtifactWriteState.UNCHANGED}


def test_planner_carries_removed_source_evidence_as_tombstones(tmp_path):
    inputs = _planner_inputs(tmp_path)
    prior_plan = build_knowledge_generation_plan(inputs)
    prior = prior_plan.committed_manifest
    prior_producer = parse_knowledge_index(
        json.loads(prior_plan.knowledge_index.content)
    ).bundle.producer

    removed = build_knowledge_generation_plan(
        replace(
            inputs,
            inventory={},
            source_content_hashes={},
            consumed_inputs=(),
            module_page_map={},
            entity_occurrence_page_map={},
            extractor_ref_by_source={},
            inventory_complete_by_source={},
            previous_manifest=prior,
            previous_producer=prior_producer,
        )
    )

    assert removed.committed_manifest.sources == {}
    assert removed.committed_manifest.evidence_baselines == {}
    assert set(removed.committed_manifest.tombstones) == set(prior.evidence_baselines)
    assert {
        tombstone.reason for tombstone in removed.committed_manifest.tombstones.values()
    } == {TOMBSTONE_SOURCE_MISSING}
    assert all(
        tombstone.last_valid_basis is not None
        for tombstone in removed.committed_manifest.tombstones.values()
    )


@pytest.mark.parametrize(
    ("changes", "field"),
    [
        (
            {"source_content_hashes": {}},
            "source_content_hashes",
        ),
        (
            {"entity_occurrence_page_map": {}},
            "entity_occurrence_page_map",
        ),
        (
            {"surface_index_payload": {}},
            "surface_index",
        ),
    ],
)
def test_planner_rejects_incomplete_or_ambiguous_evaluated_inputs(
    tmp_path,
    changes,
    field,
):
    inputs = _planner_inputs(tmp_path)

    with pytest.raises(KnowledgeGenerationError) as exc_info:
        build_knowledge_generation_plan(replace(inputs, **changes))

    assert exc_info.value.field == field


def test_manifest_hash_override_has_exact_inventory_parity_without_reading(
    tmp_path,
    monkeypatch,
):
    fixture = one_module_two_entities_fixture()
    inputs = _planner_inputs(tmp_path, fixture)

    def unexpected_source_read(*_args, **_kwargs):
        raise AssertionError("manifest ignored captured source hashes")

    monkeypatch.setattr(sync_manifest, "hash_file", unexpected_source_read)
    plan = build_knowledge_generation_plan(inputs)

    assert {
        path: source["hash"] for path, source in plan.committed_manifest.sources.items()
    } == dict(inputs.source_content_hashes)
