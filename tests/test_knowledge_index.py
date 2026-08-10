"""Focused coverage for the pure knowledge-index builder."""

from __future__ import annotations

import json
import os
import socket
import subprocess
import urllib.request
from collections.abc import Mapping
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any

import pytest

from llm_wiki_cli import __version__
from llm_wiki_cli.config import EXTRACTOR_REGISTRY
from llm_wiki_cli.services.contracts import KNOWLEDGE_SCHEMA_VERSION
from llm_wiki_cli.services.knowledge_envelope import (
    ConsumedInput,
    ConsumedInputKind,
    EnvelopeInputs,
    EvaluatedEnvelope,
    ProducerComponentInput,
    build_evaluated_envelope,
)
from llm_wiki_cli.services.knowledge_evidence import (
    build_entity_observation_basis,
    build_module_observation_basis,
    formatted_json_bytes,
    sha256_bytes,
)
from llm_wiki_cli.services.knowledge_index import (
    LINK_SYNTAX_EXTENSION,
    KnowledgeIndexBuildError,
    KnowledgeIndexInputs,
    build_knowledge_index,
    knowledge_index_to_payload,
    serialize_knowledge_index,
    validate_knowledge_index,
)
from llm_wiki_cli.services.knowledge_links import collect_link_observations
from llm_wiki_cli.services.knowledge_model import (
    EvidenceState,
    KnowledgeModelError,
    RelationshipKind,
    Resolution,
    TargetClass,
    parse_knowledge_index,
)
from llm_wiki_cli.services.knowledge_model import (
    knowledge_index_to_payload as model_to_payload,
)
from llm_wiki_cli.services.knowledge_orchestration import (
    RUNTIME_GENERATION_OPTION_DEFAULTS,
    prepare_runtime_generation_options,
    runtime_generation_options,
)
from llm_wiki_cli.services.sync_manifest import (
    TOMBSTONE_SOURCE_MISSING,
    TOMBSTONE_UNKNOWN_PROVENANCE,
    ManifestEvidenceBaseline,
    ManifestPageSource,
    ManifestTombstone,
)
from llm_wiki_cli.services.wiki_surface import (
    PageKind,
    SurfaceRole,
    WikiSurfacePage,
    mcp_uri,
)
from llm_wiki_cli.services.wiki_surface_index import (
    WIKI_SURFACE_INDEX_SCHEMA_VERSION,
)
from tests.knowledge_fixtures import (
    EvaluatedKnowledgeFixture,
    duplicate_entity_occurrences_fixture,
    one_module_two_entities_fixture,
)

_VIRTUAL_WIKI = Path("/virtual/knowledge-index-wiki")
_GOLDEN_PATH = (
    Path(__file__).parent / "fixtures" / "knowledge-index" / "complete-v1.json"
)


@dataclass(frozen=True)
class _BuilderCase:
    fixture: EvaluatedKnowledgeFixture
    inputs: KnowledgeIndexInputs


def _surface_locator(kind: PageKind, page_id: str, canonical_path: str) -> str:
    if "/" not in canonical_path:
        return mcp_uri(kind)
    return mcp_uri(kind, page_id)


def _surface_pages(
    fixture: EvaluatedKnowledgeFixture,
) -> tuple[WikiSurfacePage, ...]:
    return tuple(
        WikiSurfacePage(
            kind=PageKind(page.page_kind),
            page_id=page.page_id,
            label="Knowledge fixture",
            path=_VIRTUAL_WIKI / page.canonical_path,
            relative_path=page.canonical_path,
            mcp_uri=_surface_locator(
                PageKind(page.page_kind),
                page.page_id,
                page.canonical_path,
            ),
            obsidian_mirror_dir=None,
            role=SurfaceRole(page.role),
        )
        for page in fixture.pages
    )


def _real_envelope(
    fixture: EvaluatedKnowledgeFixture,
    content_by_page: Mapping[str, str],
) -> EvaluatedEnvelope:
    source_inputs = tuple(
        ConsumedInput.from_bytes(
            source_path,
            content.encode("utf-8"),
            kind=ConsumedInputKind.SOURCE,
        )
        for source_path, content in fixture.source_files.items()
    )
    repository = parse_knowledge_index(fixture.knowledge_payload).bundle.repository
    prepared_generation_options = prepare_runtime_generation_options(
        runtime_generation_options(
            surfaces={},
            include_tests=(),
            preserve_semantic=True,
        ),
        generation_option_defaults=RUNTIME_GENERATION_OPTION_DEFAULTS,
        generation_option_allowlist=tuple(RUNTIME_GENERATION_OPTION_DEFAULTS),
        inventory_complete=True,
    )
    return build_evaluated_envelope(
        EnvelopeInputs(
            repository=repository,
            source_inputs=source_inputs,
            inventory=fixture.inventory,
            markdown_pages=content_by_page,
            surface_index_bytes=fixture.surface_bytes,
            generation_options=prepared_generation_options.values,
            generation_option_defaults=prepared_generation_options.defaults,
            generation_option_allowlist=prepared_generation_options.allowlist,
            tool=ProducerComponentInput(
                component_id="agent-wiki-cli",
                version=__version__,
                configuration={
                    "knowledge_schema": KNOWLEDGE_SCHEMA_VERSION,
                    "surface_schema": WIKI_SURFACE_INDEX_SCHEMA_VERSION,
                },
            ),
            extractors=(
                ProducerComponentInput(
                    component_id="llm-wiki/extractor/python",
                    version=__version__,
                    configuration={
                        "entry_point": EXTRACTOR_REGISTRY["python"],
                        "inventory_mode": "deep",
                        "language": "python",
                    },
                ),
            ),
        )
    )


def _manifest_evidence(
    fixture: EvaluatedKnowledgeFixture,
) -> tuple[
    dict[str, ManifestPageSource],
    dict[str, ManifestEvidenceBaseline],
]:
    source_path, source_text = next(iter(fixture.source_files.items()))
    source_hash = sha256_bytes(source_text.encode("utf-8"))
    file_data = fixture.inventory[source_path]

    page_sources: dict[str, ManifestPageSource] = {}
    baselines: dict[str, ManifestEvidenceBaseline] = {}

    module_page_id = fixture.module_page_map[source_path]
    module_path = f"modules/{module_page_id}.md"
    page_sources[module_path] = ManifestPageSource(
        scope="module",
        source_path=source_path,
    )
    baselines[module_path] = ManifestEvidenceBaseline.from_basis(
        build_module_observation_basis(
            source_path=source_path,
            file_data=file_data,
            source_content_hash=source_hash,
            extractor_ref="llm-wiki/extractor/python",
            inventory_complete=True,
        )
    )

    for (
        entity_name,
        source_path,
        occurrence,
    ), page_id in fixture.entity_occurrence_page_map.items():
        page_path = f"entities/{page_id}.md"
        page_sources[page_path] = ManifestPageSource(
            scope="entity",
            source_path=source_path,
            entity_name=entity_name,
            occurrence=occurrence,
        )
        baselines[page_path] = ManifestEvidenceBaseline.from_basis(
            build_entity_observation_basis(
                source_path=source_path,
                file_data=fixture.inventory[source_path],
                entity_name=entity_name,
                occurrence=occurrence,
                source_content_hash=source_hash,
                extractor_ref="llm-wiki/extractor/python",
                inventory_complete=True,
            )
        )
    return page_sources, baselines


def _builder_case_for(
    fixture: EvaluatedKnowledgeFixture,
) -> _BuilderCase:
    pages = _surface_pages(fixture)
    content_by_page = {page.canonical_path: page.content for page in fixture.pages}
    page_sources, baselines = _manifest_evidence(fixture)
    envelope = _real_envelope(fixture, content_by_page)
    observations = collect_link_observations(
        pages,
        content_by_page,
        existing_asset_paths=frozenset(fixture.assets),
    )
    return _BuilderCase(
        fixture=fixture,
        inputs=KnowledgeIndexInputs(
            envelope=envelope,
            pages=pages,
            content_by_page=content_by_page,
            surface_index_bytes=fixture.surface_bytes,
            page_source_mappings=page_sources,
            evidence_baselines=baselines,
            tombstones={},
            link_observations=observations,
            extensions={},
        ),
    )


@pytest.fixture(scope="module")
def builder_case() -> _BuilderCase:
    return _builder_case_for(one_module_two_entities_fixture())


def _assert_build_error(
    expected_field: str,
    inputs: KnowledgeIndexInputs,
) -> KnowledgeIndexBuildError:
    with pytest.raises(KnowledgeIndexBuildError) as exc_info:
        build_knowledge_index(inputs)
    assert expected_field in exc_info.value.field
    return exc_info.value


def _surface_titles(surface_bytes: bytes) -> dict[str, str]:
    payload = json.loads(surface_bytes)
    return {page["canonical_path"]: page["title"] for page in payload["pages"]}


def test_builds_complete_deterministic_index_from_evaluated_inputs(
    builder_case: _BuilderCase,
) -> None:
    inputs = builder_case.inputs
    model = build_knowledge_index(inputs)
    reversed_inputs = replace(
        inputs,
        pages=tuple(reversed(inputs.pages)),
        content_by_page=dict(reversed(tuple(inputs.content_by_page.items()))),
        page_source_mappings=dict(reversed(tuple(inputs.page_source_mappings.items()))),
        evidence_baselines=dict(reversed(tuple(inputs.evidence_baselines.items()))),
        link_observations=tuple(reversed(inputs.link_observations)),
    )
    permuted = build_knowledge_index(reversed_inputs)

    assert model.schema_version == KNOWLEDGE_SCHEMA_VERSION
    assert model.bundle == inputs.envelope.bundle
    assert len(model.concepts) == len(inputs.pages)
    assert serialize_knowledge_index(model) == serialize_knowledge_index(permuted)
    assert knowledge_index_to_payload(model) == knowledge_index_to_payload(permuted)
    assert validate_knowledge_index(model) == model
    assert validate_knowledge_index(model, inputs=inputs) == model

    concepts_by_path = {
        concept.document.canonical_path: concept for concept in model.concepts
    }
    expected_titles = _surface_titles(inputs.surface_index_bytes)
    assert set(concepts_by_path) == set(inputs.content_by_page)
    assert {
        path: concept.title for path, concept in concepts_by_path.items()
    } == expected_titles
    for path, concept in concepts_by_path.items():
        assert concept.facets.semantics.page_hash == sha256_bytes(
            inputs.content_by_page[path].encode("utf-8")
        )

    derived = [
        relationship
        for relationship in model.relationships
        if relationship.kind is RelationshipKind.DERIVED_FROM
    ]
    links = [
        relationship
        for relationship in model.relationships
        if relationship.kind is RelationshipKind.LINKS_TO
    ]
    assert {relationship.kind for relationship in model.relationships} == {
        RelationshipKind.DERIVED_FROM,
        RelationshipKind.LINKS_TO,
    }
    assert len(derived) == len(inputs.evidence_baselines)
    assert len(links) == len(inputs.link_observations)
    for relationship in links:
        source = next(
            concept
            for concept in model.concepts
            if concept.locator == relationship.source_locator
        )
        assert relationship.evidence.page_hash == (source.facets.semantics.page_hash)


def test_complete_builder_golden_is_byte_stable(
    builder_case: _BuilderCase,
) -> None:
    first = serialize_knowledge_index(
        build_knowledge_index(builder_case.inputs)
    ).encode("utf-8")
    second = serialize_knowledge_index(
        build_knowledge_index(builder_case.inputs)
    ).encode("utf-8")

    assert first == second
    assert first == _GOLDEN_PATH.read_bytes()
    assert first.endswith(b"\n")
    assert not first.endswith(b"\n\n")
    assert b"\r" not in first
    payload = json.loads(first)
    forbidden_keys = {
        "created_at",
        "freshness",
        "mtime",
        "mtime_ns",
        "timestamp",
        "updated_at",
    }

    def keys(value: object) -> set[str]:
        if isinstance(value, dict):
            return set(value) | {
                nested for item in value.values() for nested in keys(item)
            }
        if isinstance(value, list):
            return {nested for item in value for nested in keys(item)}
        return set()

    assert keys(payload).isdisjoint(forbidden_keys)


def test_validator_can_require_exact_projection_of_inputs(
    builder_case: _BuilderCase,
) -> None:
    model = build_knowledge_index(builder_case.inputs)
    first = replace(model.concepts[0], title="Tampered title")
    tampered = replace(model, concepts=(first, *model.concepts[1:]))

    with pytest.raises(KnowledgeIndexBuildError) as exc_info:
        validate_knowledge_index(tampered, inputs=builder_case.inputs)

    assert exc_info.value.field.endswith(".title")


@pytest.mark.parametrize("tampered_value", [True, 1.0])
def test_exact_projection_distinguishes_json_scalar_types(
    builder_case: _BuilderCase,
    tampered_value: object,
) -> None:
    inputs = replace(
        builder_case.inputs,
        extensions={"example.invalid/value": 1},
    )
    model = build_knowledge_index(inputs)
    tampered = replace(
        model,
        extensions={"example.invalid/value": tampered_value},
    )

    with pytest.raises(KnowledgeIndexBuildError) as exc_info:
        validate_knowledge_index(tampered, inputs=inputs)

    assert exc_info.value.field == "model.extensions.example.invalid/value"


def test_standalone_validator_rejects_impossible_builder_output(
    builder_case: _BuilderCase,
) -> None:
    model = build_knowledge_index(builder_case.inputs)

    custom_concept = replace(
        model.concepts[0],
        concept_kind="example.invalid/custom",
    )
    with pytest.raises(KnowledgeModelError, match="knowledge-index construction"):
        validate_knowledge_index(
            replace(model, concepts=(custom_concept, *model.concepts[1:]))
        )

    custom_relationship = replace(
        model.relationships[0],
        kind="example.invalid/custom",
    )
    with pytest.raises(KnowledgeModelError, match="derived_from.*links_to"):
        validate_knowledge_index(
            replace(
                model,
                relationships=(custom_relationship, *model.relationships[1:]),
            )
        )

    payload = model_to_payload(model)
    link = next(
        relationship
        for relationship in payload["relationships"]
        if relationship["kind"] == RelationshipKind.LINKS_TO.value
    )
    del link["extensions"][LINK_SYNTAX_EXTENSION]
    with pytest.raises(KnowledgeModelError) as exc_info:
        validate_knowledge_index(payload)
    assert LINK_SYNTAX_EXTENSION in exc_info.value.field

    structural_index = next(
        index
        for index, concept in enumerate(model.concepts)
        if concept.facets.structure.basis is not None
    )
    structural = model.concepts[structural_index]
    basis = structural.facets.structure.basis
    assert basis is not None
    tool_basis = replace(
        basis,
        extractor_ref=model.bundle.producer.tool.component_id,
    )
    changed_structure = replace(
        structural.facets.structure,
        basis=tool_basis,
    )
    changed_concept = replace(
        structural,
        facets=replace(structural.facets, structure=changed_structure),
    )
    changed_concepts = list(model.concepts)
    changed_concepts[structural_index] = changed_concept
    with pytest.raises(KnowledgeModelError) as exc_info:
        validate_knowledge_index(replace(model, concepts=tuple(changed_concepts)))
    assert exc_info.value.field.endswith(".basis.extractor_ref")

    anchor_index, anchor = next(
        (index, relationship)
        for index, relationship in enumerate(model.relationships)
        if relationship.target.target_class is TargetClass.ANCHOR
    )
    forged_anchor = replace(
        anchor,
        target=replace(anchor.target, target_class=TargetClass.ASSET),
    )
    forged_relationships = list(model.relationships)
    forged_relationships[anchor_index] = forged_anchor
    with pytest.raises(KnowledgeModelError) as exc_info:
        validate_knowledge_index(
            replace(model, relationships=tuple(forged_relationships))
        )
    assert exc_info.value.field.endswith(".target.target_class")

    internal_index, internal = next(
        (index, relationship)
        for index, relationship in enumerate(model.relationships)
        if relationship.kind is RelationshipKind.LINKS_TO
        and relationship.target.canonical_path is not None
    )
    locator_target = next(
        concept.locator
        for concept in model.concepts
        if concept.document.canonical_path == internal.target.canonical_path
    )
    locator_link = replace(
        internal,
        target=replace(
            internal.target,
            canonical_path=None,
            locator=locator_target,
        ),
    )
    locator_relationships = list(model.relationships)
    locator_relationships[internal_index] = locator_link
    with pytest.raises(KnowledgeModelError) as exc_info:
        validate_knowledge_index(
            replace(model, relationships=tuple(locator_relationships))
        )
    assert exc_info.value.field.endswith(".target")

    derived_index, derived = next(
        (index, relationship)
        for index, relationship in enumerate(model.relationships)
        if relationship.kind is RelationshipKind.DERIVED_FROM
    )
    observed_derived = replace(
        derived,
        target=replace(
            derived.target,
            raw_target="source.py",
            normalized_target="source.py",
            label="source",
            location=next(
                relationship.target.location
                for relationship in model.relationships
                if relationship.kind is RelationshipKind.LINKS_TO
                and relationship.target.location is not None
            ),
        ),
    )
    observed_relationships = list(model.relationships)
    observed_relationships[derived_index] = observed_derived
    with pytest.raises(KnowledgeModelError) as exc_info:
        validate_knowledge_index(
            replace(model, relationships=tuple(observed_relationships))
        )
    assert exc_info.value.field.endswith(".target")


def test_builder_wraps_typed_model_failures_at_its_service_boundary(
    builder_case: _BuilderCase,
) -> None:
    inputs = replace(
        builder_case.inputs,
        extensions={"unqualified": "invalid"},
    )

    error = _assert_build_error("extensions.unqualified", inputs)

    assert "namespace/name" in error.message


def test_missing_page_content_and_surface_page_fail_parity_validation(
    builder_case: _BuilderCase,
) -> None:
    inputs = builder_case.inputs
    missing_content = dict(inputs.content_by_page)
    missing_content.pop("index.md")
    _assert_build_error(
        "content_by_page",
        replace(inputs, content_by_page=missing_content),
    )

    surface_payload = json.loads(inputs.surface_index_bytes)
    surface_payload["pages"] = [
        page
        for page in surface_payload["pages"]
        if page["canonical_path"] != "index.md"
    ]
    surface_bytes = formatted_json_bytes(surface_payload)
    snapshot = replace(
        inputs.envelope.bundle.snapshot,
        surface_index_hash=sha256_bytes(surface_bytes),
    )
    envelope = replace(
        inputs.envelope,
        bundle=replace(inputs.envelope.bundle, snapshot=snapshot),
    )
    _assert_build_error(
        "surface_index",
        replace(
            inputs,
            envelope=envelope,
            surface_index_bytes=surface_bytes,
        ),
    )


def test_snapshot_hash_mismatches_fail_before_record_construction(
    builder_case: _BuilderCase,
) -> None:
    inputs = builder_case.inputs
    _assert_build_error(
        "surface_index",
        replace(inputs, surface_index_bytes=inputs.surface_index_bytes + b" "),
    )

    changed_content = dict(inputs.content_by_page)
    changed_content["index.md"] += "\nChanged after envelope evaluation.\n"
    _assert_build_error(
        "markdown_snapshot",
        replace(inputs, content_by_page=changed_content),
    )


def test_surface_projection_rejects_nonfinite_json_values(
    builder_case: _BuilderCase,
) -> None:
    inputs = builder_case.inputs
    surface_payload = json.loads(inputs.surface_index_bytes)
    surface_payload["source_hash"] = float("nan")
    surface_bytes = (
        json.dumps(surface_payload, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")
    snapshot = replace(
        inputs.envelope.bundle.snapshot,
        surface_index_hash=sha256_bytes(surface_bytes),
    )
    envelope = replace(
        inputs.envelope,
        bundle=replace(inputs.envelope.bundle, snapshot=snapshot),
    )

    _assert_build_error(
        "surface_index_bytes",
        replace(
            inputs,
            envelope=envelope,
            surface_index_bytes=surface_bytes,
        ),
    )


def test_surface_projection_rejects_unpaired_surrogate_title(
    builder_case: _BuilderCase,
) -> None:
    inputs = builder_case.inputs
    surface_payload = json.loads(inputs.surface_index_bytes)
    surface_payload["pages"][0]["title"] = "\ud800"
    surface_bytes = (
        json.dumps(surface_payload, indent=2, sort_keys=True, ensure_ascii=True) + "\n"
    ).encode("utf-8")
    snapshot = replace(
        inputs.envelope.bundle.snapshot,
        surface_index_hash=sha256_bytes(surface_bytes),
    )
    envelope = replace(
        inputs.envelope,
        bundle=replace(inputs.envelope.bundle, snapshot=snapshot),
    )

    _assert_build_error(
        "surface_index.pages[0].title",
        replace(
            inputs,
            envelope=envelope,
            surface_index_bytes=surface_bytes,
        ),
    )


def test_unknown_module_or_entity_evidence_is_explicit_not_fabricated(
    builder_case: _BuilderCase,
) -> None:
    inputs = builder_case.inputs
    baselines = dict(inputs.evidence_baselines)
    baselines["entities/User.md"] = ManifestEvidenceBaseline.unknown(
        "inspection-unavailable"
    )

    model = build_knowledge_index(replace(inputs, evidence_baselines=baselines))
    user = next(
        concept
        for concept in model.concepts
        if concept.locator == "llm-wiki://entities/User"
    )

    assert user.facets.structure.evidence is EvidenceState.UNKNOWN
    assert user.facets.structure.basis is None
    assert not any(
        relationship.kind is RelationshipKind.DERIVED_FROM
        and relationship.source_locator == user.locator
        and relationship.evidence.state is EvidenceState.PRESENT
        for relationship in model.relationships
    )


def test_duplicate_entity_occurrences_keep_distinct_concept_evidence() -> None:
    case = _builder_case_for(duplicate_entity_occurrences_fixture())

    model = build_knowledge_index(case.inputs)
    concepts = {concept.document.canonical_path: concept for concept in model.concepts}

    first = concepts["entities/Parser.md"].facets.structure.basis
    second = concepts["entities/Parser_2.md"].facets.structure.basis
    assert first is not None
    assert second is not None
    assert first.concept_observation_hash != second.concept_observation_hash


def test_source_missing_tombstone_retains_recorded_basis_without_live_state(
    builder_case: _BuilderCase,
) -> None:
    inputs = builder_case.inputs
    baselines = dict(inputs.evidence_baselines)
    baseline = baselines.pop("entities/User.md")
    assert baseline.basis is not None
    tombstone = ManifestTombstone(
        reason=TOMBSTONE_SOURCE_MISSING,
        last_valid_basis=baseline.basis,
    )

    model = build_knowledge_index(
        replace(
            inputs,
            evidence_baselines=baselines,
            tombstones={"entities/User.md": tombstone},
        )
    )
    user = next(
        concept
        for concept in model.concepts
        if concept.locator == "llm-wiki://entities/User"
    )

    assert user.facets.structure.evidence is EvidenceState.PRESENT
    assert user.facets.structure.basis is not None
    assert "freshness" not in serialize_knowledge_index(model)


def test_surface_source_requires_a_manifest_mapping(
    builder_case: _BuilderCase,
) -> None:
    inputs = builder_case.inputs
    page_sources = dict(inputs.page_source_mappings)
    page_sources.pop("entities/User.md")
    baselines = dict(inputs.evidence_baselines)
    baselines.pop("entities/User.md")
    tombstone = ManifestTombstone(
        reason=TOMBSTONE_UNKNOWN_PROVENANCE,
        unknown_reason="untracked-page",
    )

    _assert_build_error(
        "surface_index.pages[",
        replace(
            inputs,
            page_source_mappings=page_sources,
            evidence_baselines=baselines,
            tombstones={"entities/User.md": tombstone},
        ),
    )


def test_basis_must_reference_an_envelope_extractor(
    builder_case: _BuilderCase,
) -> None:
    inputs = builder_case.inputs
    baselines = dict(inputs.evidence_baselines)
    baseline = baselines["entities/User.md"]
    assert baseline.basis is not None
    baselines["entities/User.md"] = ManifestEvidenceBaseline.from_basis(
        replace(baseline.basis, extractor_ref="agent-wiki-cli")
    )

    _assert_build_error(
        "extractor_ref",
        replace(inputs, evidence_baselines=baselines),
    )


def test_ambiguous_internal_collision_is_rejected_by_the_builder(
    builder_case: _BuilderCase,
) -> None:
    inputs = builder_case.inputs
    resolved = next(
        observation
        for observation in inputs.link_observations
        if observation.target_class is TargetClass.CONCEPT
        and observation.resolution is Resolution.RESOLVED
    )
    ambiguous = replace(
        resolved,
        resolution=Resolution.AMBIGUOUS,
        resolved_canonical_path=None,
    )
    observations = tuple(
        ambiguous if observation is resolved else observation
        for observation in inputs.link_observations
    )

    _assert_build_error(
        "link_observations",
        replace(inputs, link_observations=observations),
    )


def test_link_observation_must_match_raw_target_normalization(
    builder_case: _BuilderCase,
) -> None:
    inputs = builder_case.inputs
    observation = inputs.link_observations[0]
    changed = replace(
        observation,
        normalized_target="different-target.md",
    )

    _assert_build_error(
        "normalized_target",
        replace(
            inputs,
            link_observations=(changed, *inputs.link_observations[1:]),
        ),
    )


def test_duplicate_supplied_link_occurrence_is_rejected(
    builder_case: _BuilderCase,
) -> None:
    inputs = builder_case.inputs
    first = inputs.link_observations[0]

    _assert_build_error(
        "location",
        replace(
            inputs,
            link_observations=(first, *inputs.link_observations),
        ),
    )


@pytest.mark.parametrize(
    ("changed_field", "changed_value"),
    [
        ("raw_target", "User.md"),
        ("label", "ser"),
    ],
)
def test_link_observation_must_match_exact_parsed_occurrence(
    builder_case: _BuilderCase,
    changed_field: str,
    changed_value: str,
) -> None:
    inputs = builder_case.inputs
    observation = inputs.link_observations[0]
    changed = replace(observation, **{changed_field: changed_value})

    _assert_build_error(
        changed_field,
        replace(
            inputs,
            link_observations=(changed, *inputs.link_observations[1:]),
        ),
    )


def test_link_observation_endpoint_must_match_normalized_target(
    builder_case: _BuilderCase,
) -> None:
    inputs = builder_case.inputs
    internal = next(
        observation
        for observation in inputs.link_observations
        if observation.resolved_canonical_path == "entities/User.md"
    )
    forged_internal = replace(
        internal,
        resolved_canonical_path="entities/AccountService.md",
    )
    internal_observations = tuple(
        forged_internal if observation is internal else observation
        for observation in inputs.link_observations
    )
    _assert_build_error(
        "resolved_canonical_path",
        replace(inputs, link_observations=internal_observations),
    )

    downgraded_internal = replace(
        internal,
        target_class=TargetClass.UNKNOWN,
        resolution=Resolution.UNRESOLVED,
        resolved_canonical_path=None,
    )
    downgraded_observations = tuple(
        downgraded_internal if observation is internal else observation
        for observation in inputs.link_observations
    )
    _assert_build_error(
        "target_class",
        replace(inputs, link_observations=downgraded_observations),
    )

    external = next(
        observation
        for observation in inputs.link_observations
        if observation.target_class is TargetClass.EXTERNAL
    )
    forged_external = replace(
        external,
        external_uri="https://example.invalid/different",
    )
    external_observations = tuple(
        forged_external if observation is external else observation
        for observation in inputs.link_observations
    )
    _assert_build_error(
        "external_uri",
        replace(inputs, link_observations=external_observations),
    )

    downgraded_external = replace(
        external,
        target_class=TargetClass.UNKNOWN,
        resolution=Resolution.UNRESOLVED,
        external_uri=None,
    )
    downgraded_external_observations = tuple(
        downgraded_external if observation is external else observation
        for observation in inputs.link_observations
    )
    _assert_build_error(
        "target_class",
        replace(
            inputs,
            link_observations=downgraded_external_observations,
        ),
    )


def test_builder_accepts_collector_classification_for_malformed_locator(
    builder_case: _BuilderCase,
) -> None:
    inputs = builder_case.inputs
    content = dict(inputs.content_by_page)
    content["modules/accounts.md"] += "\n[Bad locator](llm-wiki://entities/User?x=1)\n"
    envelope = _real_envelope(builder_case.fixture, content)
    observations = collect_link_observations(
        inputs.pages,
        content,
        existing_asset_paths=frozenset(builder_case.fixture.assets),
    )

    model = build_knowledge_index(
        replace(
            inputs,
            envelope=envelope,
            content_by_page=content,
            link_observations=observations,
        )
    )
    malformed = next(
        relationship
        for relationship in model.relationships
        if relationship.target.label == "Bad locator"
    )

    assert malformed.target.target_class is TargetClass.MALFORMED
    assert malformed.resolution is Resolution.UNRESOLVED


def test_unregistered_local_target_allows_only_unknown_or_asset_outcomes(
    builder_case: _BuilderCase,
) -> None:
    inputs = builder_case.inputs
    content = dict(inputs.content_by_page)
    content["modules/accounts.md"] += "\n[Blob](data.bin)\n"
    envelope = _real_envelope(builder_case.fixture, content)
    observations = collect_link_observations(
        inputs.pages,
        content,
        existing_asset_paths=frozenset(builder_case.fixture.assets),
    )
    blob = next(
        observation for observation in observations if observation.label == "Blob"
    )
    assert blob.target_class is TargetClass.UNKNOWN
    forged = replace(
        blob,
        target_class=TargetClass.ANCHOR,
        resolution=Resolution.RESOLVED,
    )
    forged_observations = tuple(
        forged if observation is blob else observation for observation in observations
    )

    _assert_build_error(
        "target_class",
        replace(
            inputs,
            envelope=envelope,
            content_by_page=content,
            link_observations=forged_observations,
        ),
    )

    asset_paths = frozenset({*builder_case.fixture.assets, "modules/data.bin"})
    asset_observations = collect_link_observations(
        inputs.pages,
        content,
        existing_asset_paths=asset_paths,
    )
    asset = next(
        observation for observation in asset_observations if observation.label == "Blob"
    )
    assert asset.target_class is TargetClass.ASSET
    assert asset.resolution is Resolution.RESOLVED
    build_knowledge_index(
        replace(
            inputs,
            envelope=envelope,
            content_by_page=content,
            link_observations=asset_observations,
        )
    )


def test_credential_userinfo_observation_is_omitted_whole(
    builder_case: _BuilderCase,
) -> None:
    inputs = builder_case.inputs
    external = next(
        observation
        for observation in inputs.link_observations
        if observation.target_class is TargetClass.EXTERNAL
    )
    credential = "https://user:secret@example.invalid/reference"
    credential_observation = replace(
        external,
        raw_target=credential,
        normalized_target=credential,
        external_uri=credential,
    )
    observations = (*inputs.link_observations, credential_observation)

    model = build_knowledge_index(replace(inputs, link_observations=observations))

    assert len(
        [
            relationship
            for relationship in model.relationships
            if relationship.kind is RelationshipKind.LINKS_TO
        ]
    ) == len(inputs.link_observations)
    assert credential not in serialize_knowledge_index(model)


def test_angle_wrapped_credential_userinfo_observation_is_omitted_whole(
    builder_case: _BuilderCase,
) -> None:
    inputs = builder_case.inputs
    external = next(
        observation
        for observation in inputs.link_observations
        if observation.target_class is TargetClass.EXTERNAL
    )
    credential = "<https://user:secret@example.invalid/reference>"
    credential_observation = replace(
        external,
        raw_target=credential,
        normalized_target="https://user:secret@example.invalid/reference",
        external_uri="https://user:secret@example.invalid/reference",
    )

    model = build_knowledge_index(
        replace(
            inputs,
            link_observations=(
                *inputs.link_observations,
                credential_observation,
            ),
        )
    )

    serialized = serialize_knowledge_index(model)
    assert credential not in serialized
    assert "user:secret@" not in serialized


def test_optional_title_credential_userinfo_is_omitted_whole(
    builder_case: _BuilderCase,
) -> None:
    inputs = builder_case.inputs
    internal = next(
        observation
        for observation in inputs.link_observations
        if observation.resolved_canonical_path == "entities/User.md"
    )
    raw_target = '../entities/User.md "https://user:secret@example.invalid/private"'
    credential_observation = replace(
        internal,
        raw_target=raw_target,
    )

    model = build_knowledge_index(
        replace(
            inputs,
            link_observations=(
                *inputs.link_observations,
                credential_observation,
            ),
        )
    )

    serialized = serialize_knowledge_index(model)
    assert raw_target not in serialized
    assert "user:secret@" not in serialized


def test_unknown_extensions_round_trip_without_reordering_arrays(
    builder_case: _BuilderCase,
) -> None:
    extension_value: list[Any] = [
        "z-last",
        {"nested": [3, 1, 2]},
        "a-first",
    ]
    inputs = replace(
        builder_case.inputs,
        extensions={"example.invalid/ordered": extension_value},
    )

    model = build_knowledge_index(inputs)
    normalized = knowledge_index_to_payload(validate_knowledge_index(model))
    serialized = serialize_knowledge_index(model)

    assert normalized["extensions"]["example.invalid/ordered"] == extension_value
    assert json.loads(serialized)["extensions"]["example.invalid/ordered"] == (
        extension_value
    )


def test_builder_performs_no_io_and_does_not_mutate_inputs(
    builder_case: _BuilderCase,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    inputs = builder_case.inputs
    pages_before = tuple(inputs.pages)
    content_before = dict(inputs.content_by_page)
    evidence_before = dict(inputs.evidence_baselines)
    observations_before = tuple(inputs.link_observations)

    def forbidden(*_args: object, **_kwargs: object) -> object:
        raise AssertionError("pure knowledge-index builder attempted I/O")

    with monkeypatch.context() as guard:
        for method_name in (
            "read_text",
            "read_bytes",
            "write_text",
            "write_bytes",
            "open",
            "exists",
            "is_file",
            "is_dir",
            "iterdir",
            "glob",
            "rglob",
            "resolve",
        ):
            guard.setattr(Path, method_name, forbidden)
        guard.setattr(os, "walk", forbidden)
        guard.setattr(os, "scandir", forbidden)
        guard.setattr(subprocess, "run", forbidden)
        guard.setattr(subprocess, "Popen", forbidden)
        guard.setattr(socket, "create_connection", forbidden)
        guard.setattr(urllib.request, "urlopen", forbidden)

        model = build_knowledge_index(inputs)
        serialized = serialize_knowledge_index(model)

    assert serialized.endswith("\n")
    assert tuple(inputs.pages) == pages_before
    assert dict(inputs.content_by_page) == content_before
    assert dict(inputs.evidence_baselines) == evidence_before
    assert tuple(inputs.link_observations) == observations_before
