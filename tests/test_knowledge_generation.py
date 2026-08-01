"""Focused tests for the shared KNOW-109/110 generation planner."""

from __future__ import annotations

import json
from copy import deepcopy
from dataclasses import replace
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from llm_wiki_cli.services import sync_manifest
from llm_wiki_cli.services.contracts import (
    SECTION_OWNERSHIP_EXTENSION_KEY,
    TYPED_GRAPH_EXTENSION_KEY,
)
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
from llm_wiki_cli.services.knowledge_freshness import evaluate_knowledge_freshness
from llm_wiki_cli.services.knowledge_generation import (
    KnowledgeGenerationError,
    KnowledgeGenerationInputs,
    build_knowledge_generation_plan,
)
from llm_wiki_cli.services.knowledge_model import (
    ComputedFreshness,
    RelationshipKind,
    WorkingTreeState,
    load_knowledge_schema,
    parse_knowledge_index,
)
from llm_wiki_cli.services.knowledge_orchestration import (
    RUNTIME_GENERATION_OPTION_DEFAULTS,
    RuntimeKnowledgeInputs,
    RuntimeLiveEvaluationInputs,
    build_runtime_knowledge_plan,
    build_runtime_live_evaluation,
    persist_runtime_generation_policy,
    prepare_runtime_generation_options,
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


def _runtime_input_case(
    tmp_path: Path,
    *,
    inventory_complete: bool,
) -> tuple[
    RuntimeKnowledgeInputs,
    SourceSnapshot,
    EvaluatedKnowledgeFixture,
]:
    fixture = one_module_two_entities_fixture()
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
        content_by_path={
            page.canonical_path: page.content for page in fixture.pages
        },
        payload=fixture.surface_payload,
        serialized_bytes=fixture.surface_bytes,
        existing_asset_paths=frozenset(fixture.assets),
    )
    generation_options = runtime_generation_options(
        surfaces={},
        include_tests=None,
        preserve_semantic=True,
    )
    return (
        RuntimeKnowledgeInputs(
            target_wiki_dir=tmp_path,
            inventory=fixture.inventory,
            surface=surface,
            source_snapshot=source_snapshot,
            module_page_map=fixture.module_page_map,
            entity_occurrence_page_map=fixture.entity_occurrence_page_map,
            repository_evidence=RepositoryEvidence(),
            inventory_complete=inventory_complete,
            extractor_registry={
                "python": (
                    "llm_wiki_cli.extractors.python_extractor:PythonExtractor"
                )
            },
            generation_options=generation_options,
            generation_option_defaults=RUNTIME_GENERATION_OPTION_DEFAULTS,
            generation_option_allowlist=tuple(
                RUNTIME_GENERATION_OPTION_DEFAULTS
            ),
        ),
        source_snapshot,
        fixture,
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
    graph = knowledge.extensions[TYPED_GRAPH_EXTENSION_KEY]
    sections = knowledge.extensions[SECTION_OWNERSHIP_EXTENSION_KEY]
    assert {edge["kind"] for edge in graph["edges"]} == {"contains"}
    assert graph["input_hashes"]["inventory"] == (
        knowledge.bundle.snapshot.extensions["llm-wiki/inventory-hash"]
    )
    assert len(sections["pages"]) == len(inputs.pages)
    assert {
        page["page_locator"] for page in sections["pages"]
    } == {page.mcp_uri for page in inputs.pages}


def test_planner_publishes_raw_graph_observations_and_rejects_reserved_collisions(
    tmp_path,
):
    inputs = _planner_inputs(tmp_path)
    source_path = next(iter(inputs.inventory))
    module_locator = next(
        page.mcp_uri for page in inputs.pages if page.kind.value == "modules"
    )
    plan = build_knowledge_generation_plan(
        replace(
            inputs,
            dependency_observations={
                "schema_version": "llm-wiki-dependency-observations/v1",
                "observations": [
                    {
                        "source_path": source_path,
                        "module": "missing",
                        "name": "value",
                        "line": None,
                        "candidates": [],
                        "target_path": None,
                        "resolution": "unresolved",
                    }
                ],
                "coverage": {
                    "observed": 1,
                    "emitted": 1,
                    "omitted": 0,
                    "limit": None,
                    "truncated": False,
                    "limitations": [],
                },
            },
        )
    )
    knowledge = parse_knowledge_index(json.loads(plan.knowledge_index.content))
    edge = next(
        edge
        for edge in knowledge.extensions[TYPED_GRAPH_EXTENSION_KEY]["edges"]
        if edge["kind"] == "imports"
    )
    assert edge["from"]["locator"] == module_locator
    assert edge["resolution"] == "unresolved"
    assert edge["evidence"]["samples"][0]["location"] == {
        "source_path": source_path
    }

    with pytest.raises(KnowledgeGenerationError, match="application-owned"):
        build_knowledge_generation_plan(
            replace(
                inputs,
                knowledge_extensions={TYPED_GRAPH_EXTENSION_KEY: {}},
            )
        )


def test_section_snapshot_parity_distinguishes_raw_and_normalized_line_endings(
    tmp_path,
):
    inputs = _planner_inputs(tmp_path)
    changed_path = next(iter(inputs.content_by_page))
    raw = inputs.content_by_page[changed_path].replace("\n", "\r\n")
    plan = build_knowledge_generation_plan(
        replace(
            inputs,
            content_by_page={**inputs.content_by_page, changed_path: raw},
        )
    )
    knowledge = parse_knowledge_index(json.loads(plan.knowledge_index.content))
    page = next(
        page
        for page in knowledge.extensions[SECTION_OWNERSHIP_EXTENSION_KEY]["pages"]
        if page["page_locator"]
        == next(
            surface.mcp_uri
            for surface in inputs.pages
            if surface.relative_path == changed_path
        )
    )
    assert page["source_hash"] == sha256_bytes(raw.encode("utf-8"))
    assert page["exact_hash"] == sha256_bytes(
        raw.replace("\r\n", "\n").encode("utf-8")
    )


def test_published_reserved_extensions_match_the_packaged_json_schema(tmp_path):
    plan = build_knowledge_generation_plan(_planner_inputs(tmp_path))
    payload = json.loads(plan.knowledge_index.content)
    validator = Draft202012Validator(load_knowledge_schema())

    assert list(validator.iter_errors(payload)) == []

    invalid_graph = deepcopy(payload)
    invalid_graph["extensions"][TYPED_GRAPH_EXTENSION_KEY]["edges"][0][
        "kind"
    ] = "unqualified-custom"
    assert list(validator.iter_errors(invalid_graph))

    invalid_section = deepcopy(payload)
    generated = next(
        section
        for page in invalid_section["extensions"][SECTION_OWNERSHIP_EXTENSION_KEY][
            "pages"
        ]
        for section in page["sections"]
        if section["ownership"] == "generated"
    )
    generated["semantic_hash"] = generated["exact_hash"]
    assert list(validator.iter_errors(invalid_section))

    missing_occurrence_path = deepcopy(payload)
    heading = next(
        section
        for page in missing_occurrence_path["extensions"][
            SECTION_OWNERSHIP_EXTENSION_KEY
        ]["pages"]
        for section in page["sections"]
        if section["title"] is not None
    )
    heading.pop("occurrence_path")
    assert list(validator.iter_errors(missing_occurrence_path))

    invalid_preamble = deepcopy(payload)
    preamble = next(
        section
        for page in invalid_preamble["extensions"][
            SECTION_OWNERSHIP_EXTENSION_KEY
        ]["pages"]
        for section in page["sections"]
        if section["title"] is not None
    )
    preamble["locator"] = f"{preamble['page_locator']}#section/@preamble"
    preamble["title"] = None
    preamble["level"] = 0
    preamble["heading_path"] = []
    preamble["occurrence"] = 1
    preamble["parent_locator"] = None
    preamble["occurrence_path"] = [1]
    assert list(validator.iter_errors(invalid_preamble))


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


@pytest.mark.parametrize(
    ("inventory_complete", "inventory_mode"),
    [(True, "deep"), (False, "shallow")],
)
def test_runtime_writer_and_live_reader_share_generation_option_commitment(
    tmp_path,
    inventory_complete,
    inventory_mode,
):
    runtime, source_snapshot, fixture = _runtime_input_case(
        tmp_path,
        inventory_complete=inventory_complete,
    )
    prepared = prepare_runtime_generation_options(
        runtime.generation_options,
        generation_option_defaults=runtime.generation_option_defaults,
        generation_option_allowlist=runtime.generation_option_allowlist,
        inventory_complete=inventory_complete,
    )
    plan = build_runtime_knowledge_plan(runtime)
    knowledge = parse_knowledge_index(json.loads(plan.knowledge_index.content))

    live = build_runtime_live_evaluation(
        RuntimeLiveEvaluationInputs(
            knowledge=knowledge,
            manifest=plan.committed_manifest,
            inventory=fixture.inventory,
            source_snapshot=source_snapshot,
            generation_options=runtime.generation_options,
            generation_option_defaults=runtime.generation_option_defaults,
            generation_option_allowlist=runtime.generation_option_allowlist,
            inventory_complete=inventory_complete,
            extractor_registry=runtime.extractor_registry,
        )
    )

    assert prepared.values["inventory_mode"] == inventory_mode
    assert prepared.defaults["inventory_mode"] == "deep"
    assert prepared.allowlist[0] == "inventory_mode"
    assert live.generation_options_hash == hash_generation_options(
        prepared.values,
        defaults=prepared.defaults,
        allowlist=prepared.allowlist,
    )
    assert live.generation_options_hash == (
        knowledge.bundle.snapshot.generation_options_hash
    )


def test_runtime_live_generation_hash_is_independent_of_recorded_hash(tmp_path):
    runtime, source_snapshot, fixture = _runtime_input_case(
        tmp_path,
        inventory_complete=True,
    )
    plan = build_runtime_knowledge_plan(runtime)
    knowledge = parse_knowledge_index(json.loads(plan.knowledge_index.content))
    tampered = replace(
        knowledge,
        bundle=replace(
            knowledge.bundle,
            snapshot=replace(
                knowledge.bundle.snapshot,
                generation_options_hash=sha256_bytes(b"recorded-only-value"),
            ),
        ),
    )

    live = build_runtime_live_evaluation(
        RuntimeLiveEvaluationInputs(
            knowledge=tampered,
            manifest=plan.committed_manifest,
            inventory=fixture.inventory,
            source_snapshot=source_snapshot,
            generation_options=runtime.generation_options,
            generation_option_defaults=runtime.generation_option_defaults,
            generation_option_allowlist=runtime.generation_option_allowlist,
            extractor_registry=runtime.extractor_registry,
        )
    )

    assert live.generation_options_hash == (
        knowledge.bundle.snapshot.generation_options_hash
    )
    assert live.generation_options_hash != (
        tampered.bundle.snapshot.generation_options_hash
    )


@pytest.mark.parametrize(
    "changed_options",
    [
        runtime_generation_options(
            surfaces={},
            include_tests=("go",),
            preserve_semantic=True,
        ),
        runtime_generation_options(
            surfaces={},
            include_tests=None,
            preserve_semantic=False,
        ),
    ],
    ids=["include-tests", "preserve-semantic"],
)
def test_runtime_live_generation_option_drift_is_basis_incompatible(
    tmp_path,
    changed_options,
):
    runtime, source_snapshot, fixture = _runtime_input_case(
        tmp_path,
        inventory_complete=True,
    )
    plan = build_runtime_knowledge_plan(runtime)
    knowledge = parse_knowledge_index(json.loads(plan.knowledge_index.content))

    live = build_runtime_live_evaluation(
        RuntimeLiveEvaluationInputs(
            knowledge=knowledge,
            manifest=plan.committed_manifest,
            inventory=fixture.inventory,
            source_snapshot=source_snapshot,
            generation_options=changed_options,
            generation_option_defaults=runtime.generation_option_defaults,
            generation_option_allowlist=runtime.generation_option_allowlist,
            extractor_registry=runtime.extractor_registry,
        )
    )
    report = evaluate_knowledge_freshness(knowledge, live)
    evaluated = [
        result
        for result in report.by_locator.values()
        if result.live_comparison_performed
    ]

    assert live.generation_options_hash != (
        knowledge.bundle.snapshot.generation_options_hash
    )
    assert evaluated
    assert {result.state for result in evaluated} == {
        ComputedFreshness.BASIS_INCOMPATIBLE
    }
    assert {result.reason_code for result in evaluated} == {
        "generation-options-changed"
    }


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
