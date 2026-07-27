"""Shared in-memory generation planner for native knowledge artifacts.

Bootstrap, sync, migration, and repair all need to construct the same three
artifact commit from one evaluated run.  This module joins the existing
KNOW-102 through KNOW-107 services without discovering pages, rereading source
files, invoking extractors, or writing output.  The only filesystem reads are
the target-state comparisons performed by :func:`build_knowledge_commit_plan`.
"""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from collections.abc import Set as AbstractSet
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .knowledge_artifacts import (
    KnowledgeArtifactError,
    KnowledgeCommitPlan,
    build_knowledge_commit_plan,
    validate_surface_index_bytes,
)
from .knowledge_envelope import (
    ConsumedInput,
    EnvelopeInputs,
    KnowledgeEnvelopeError,
    ProducerComponentInput,
    RepositoryEvidence,
    build_evaluated_envelope,
    build_repository_record,
)
from .knowledge_evidence import (
    ConceptObservationBasis,
    build_entity_observation_basis,
    build_module_observation_basis,
    is_valid_sha256,
)
from .knowledge_index import (
    KnowledgeIndexBuildError,
    KnowledgeIndexInputs,
    build_knowledge_index,
    serialize_knowledge_index,
)
from .knowledge_graph import (
    DEFAULT_EVIDENCE_LIMIT,
    GraphConcept,
    KnowledgeGraphError,
    KnowledgeGraphInputs,
    materialize_typed_graph,
)
from .knowledge_links import (
    KnowledgeLinkError,
    collect_link_observations,
)
from .knowledge_model import ProducerRecord, concept_kind_for_page_kind
from .contracts import (
    SECTION_OWNERSHIP_EXTENSION_KEY,
    TYPED_GRAPH_EXTENSION_KEY,
)
from .section_ownership import observe_page_sections, section_ownership_extension
from .sync_manifest import (
    EVIDENCE_NOT_RECORDED,
    MANIFEST_REPAIR_UNAVAILABLE,
    PRODUCER_BASIS_INCOMPATIBLE,
    TOMBSTONE_UNKNOWN_PROVENANCE,
    ManifestEvidenceBaseline,
    ManifestTombstone,
    SyncManifest,
    SyncManifestError,
)
from .wiki_surface import PageKind, WikiSurfacePage


class KnowledgeGenerationError(ValueError):
    """Field-specific failure at the shared generation-planning boundary."""

    def __init__(self, field: str, message: str):
        self.field = field
        self.message = message
        super().__init__(f"{field}: {message}")


@dataclass(frozen=True)
class KnowledgeGenerationInputs:
    """Complete already-evaluated inputs for one generated artifact set.

    Exactly one of ``surface_index_bytes`` and ``surface_index_payload`` must
    be supplied.  Exact bytes are retained verbatim; a payload is encoded using
    the existing surface-index v1 wire format.

    ``source_content_hashes`` commits each inventory source for manifest and
    concept evidence.  ``consumed_inputs`` is the complete source/config input
    set used by the envelope and must contain a matching commitment for every
    inventory source.
    """

    wiki_dir: str | Path
    inventory: Mapping[str, Mapping[str, Any]]
    pages: Sequence[WikiSurfacePage]
    content_by_page: Mapping[str, str]
    surface_index_bytes: bytes | None
    surface_index_payload: Mapping[str, Any] | None
    source_content_hashes: Mapping[str, str]
    consumed_inputs: Sequence[ConsumedInput]
    module_page_map: Mapping[str, str]
    entity_occurrence_page_map: Mapping[tuple[str, str, int], str]
    extractor_ref_by_source: Mapping[str, str]
    inventory_complete_by_source: Mapping[str, bool]
    repository_evidence: RepositoryEvidence
    generation_options: Mapping[str, Any]
    generation_option_defaults: Mapping[str, Any]
    generation_option_allowlist: Sequence[str]
    tool: ProducerComponentInput
    extractors: Sequence[ProducerComponentInput] = ()
    plugins: Sequence[ProducerComponentInput] = ()
    previous_producer: ProducerRecord | None = None
    configured_public_identity: str | None = None
    previous_manifest: SyncManifest | None = None
    next_manifest: SyncManifest | None = None
    asset_paths: AbstractSet[str] = frozenset()
    manifest_surfaces: Mapping[str, Mapping[str, Any]] | None = None
    manifest_generation_inputs: Mapping[str, object] | None = None
    unknown_evidence_reason: str = EVIDENCE_NOT_RECORDED
    force_unknown_evidence: bool = False
    untrusted_evidence_page_paths: AbstractSet[str] = frozenset()
    regenerated_evidence_page_paths: AbstractSet[str] = frozenset()
    bundle_extensions: Mapping[str, Any] = field(default_factory=dict)
    snapshot_extensions: Mapping[str, Any] = field(default_factory=dict)
    producer_extensions: Mapping[str, Any] = field(default_factory=dict)
    knowledge_extensions: Mapping[str, Any] = field(default_factory=dict)
    call_edges: Mapping[str, Any] | Sequence[Mapping[str, Any]] = ()
    dependency_observations: (
        Mapping[str, Any] | Sequence[Mapping[str, Any]]
    ) = ()
    entrypoint_observations: (
        Mapping[str, Any] | Sequence[Mapping[str, Any]]
    ) = ()
    flows: Sequence[Mapping[str, Any]] = ()
    data_flows: Sequence[Mapping[str, Any]] = ()
    external_dependencies: Sequence[Mapping[str, Any]] = ()
    graph_analyzer_limitations: Mapping[str, Sequence[str]] = field(
        default_factory=dict
    )
    graph_evidence_limit: int = DEFAULT_EVIDENCE_LIMIT


def build_knowledge_generation_plan(
    inputs: KnowledgeGenerationInputs,
) -> KnowledgeCommitPlan:
    """Construct one validated KNOW-107 commit plan from evaluated inputs.

    The returned plan contains exact surface and knowledge bytes plus the
    manifest-last commit marker.  It performs no writes.  Existing target
    artifact bytes may be read solely to classify each planned action as
    created, updated, or unchanged.
    """

    if not isinstance(inputs, KnowledgeGenerationInputs):
        raise TypeError("inputs must be a KnowledgeGenerationInputs")
    try:
        return _build_knowledge_generation_plan(inputs)
    except KnowledgeGenerationError:
        raise
    except (
        KnowledgeArtifactError,
        KnowledgeEnvelopeError,
        KnowledgeGraphError,
        KnowledgeIndexBuildError,
        KnowledgeLinkError,
        SyncManifestError,
    ) as exc:
        raise KnowledgeGenerationError(exc.field, exc.message) from exc


def _build_knowledge_generation_plan(
    inputs: KnowledgeGenerationInputs,
) -> KnowledgeCommitPlan:
    inventory = _validated_inventory(inputs.inventory)
    source_hashes = _validated_source_hashes(
        inventory,
        inputs.source_content_hashes,
    )
    consumed_inputs = _validated_consumed_inputs(
        inventory,
        source_hashes,
        inputs.consumed_inputs,
    )
    module_page_map, entity_page_map, occurrence_page_map = _validated_page_maps(
        inventory,
        inputs.module_page_map,
        inputs.entity_occurrence_page_map,
    )
    extractor_refs = _exact_source_mapping(
        inventory,
        inputs.extractor_ref_by_source,
        "extractor_ref_by_source",
        str,
    )
    completeness = _exact_source_mapping(
        inventory,
        inputs.inventory_complete_by_source,
        "inventory_complete_by_source",
        bool,
    )
    previous = inputs.previous_manifest
    if previous is not None and not isinstance(previous, SyncManifest):
        raise KnowledgeGenerationError(
            "previous_manifest",
            "must be a SyncManifest or None",
        )
    baselines = _build_evidence_baselines(
        inventory,
        source_hashes,
        module_page_map,
        occurrence_page_map,
        extractor_refs,
        completeness,
    )
    regenerated_page_paths = _validated_evidence_page_paths(
        inputs.regenerated_evidence_page_paths,
        baselines,
        "regenerated_evidence_page_paths",
    )
    untrusted_page_paths = _validated_evidence_page_paths(
        inputs.untrusted_evidence_page_paths,
        baselines,
        "untrusted_evidence_page_paths",
    )
    overlapping_page_paths = regenerated_page_paths & untrusted_page_paths
    if overlapping_page_paths:
        page_path = min(overlapping_page_paths)
        raise KnowledgeGenerationError(
            "regenerated_evidence_page_paths",
            f"also marks untrusted page path {page_path!r}",
        )
    manifest_baselines: Mapping[
        str, ConceptObservationBasis | ManifestEvidenceBaseline
    ] = _preserve_unchanged_unknown_baselines(
        baselines,
        previous,
        source_hashes,
        regenerated_page_paths,
    )
    manifest_baselines, pending_regeneration_sources = _mark_untrusted_evidence(
        baselines,
        manifest_baselines,
        untrusted_page_paths,
        previous,
        source_hashes,
        unknown_reason=inputs.unknown_evidence_reason,
    )
    if inputs.force_unknown_evidence:
        unknown_baselines: dict[str, ManifestEvidenceBaseline] = {}
        for page_path in baselines:
            prior = (
                previous.evidence_baselines.get(page_path)
                if previous is not None
                else None
            )
            reason = (
                prior.unknown_reason
                if (
                    prior is not None
                    and not prior.is_known
                    and prior.unknown_reason is not None
                )
                else inputs.unknown_evidence_reason
            )
            unknown_baselines[page_path] = ManifestEvidenceBaseline.unknown(reason)
        manifest_baselines = unknown_baselines
    surface_bytes = _surface_index_bytes(
        inputs.surface_index_bytes,
        inputs.surface_index_payload,
    )

    repository = build_repository_record(
        configured_public_identity=inputs.configured_public_identity,
        evidence=inputs.repository_evidence,
    )
    envelope = build_evaluated_envelope(
        EnvelopeInputs(
            repository=repository,
            source_inputs=consumed_inputs,
            inventory=inventory,
            markdown_pages=inputs.content_by_page,
            surface_index_bytes=surface_bytes,
            generation_options=inputs.generation_options,
            generation_option_defaults=inputs.generation_option_defaults,
            generation_option_allowlist=tuple(inputs.generation_option_allowlist),
            tool=inputs.tool,
            extractors=tuple(inputs.extractors),
            plugins=tuple(inputs.plugins),
            bundle_extensions=inputs.bundle_extensions,
            snapshot_extensions=inputs.snapshot_extensions,
            producer_extensions=inputs.producer_extensions,
        )
    )
    previous_producer = _validated_previous_producer(inputs.previous_producer)

    if inputs.next_manifest is not None:
        if not isinstance(inputs.next_manifest, SyncManifest):
            raise KnowledgeGenerationError(
                "next_manifest",
                "must be a SyncManifest or None",
            )
        manifest = inputs.next_manifest.without_artifact_hashes()
    else:
        manifest = SyncManifest.build_from_inventory(
            inventory,
            "",
            entity_page_map,
            module_page_map,
            entity_occurrence_page_cache=occurrence_page_map,
            surfaces=_next_manifest_mapping(
                inputs.manifest_surfaces,
                previous.surfaces if previous is not None else {},
            ),
            generation_inputs=_next_manifest_mapping(
                inputs.manifest_generation_inputs,
                previous.generation_inputs if previous is not None else {},
            ),
            previous_manifest=previous,
            evidence_baselines=manifest_baselines,
            source_content_hashes=source_hashes,
            retained_page_paths=_structural_page_paths(inputs.pages),
            unknown_evidence_reason=inputs.unknown_evidence_reason,
        )
    if pending_regeneration_sources:
        manifest = _defer_sources_for_regeneration(
            manifest,
            pending_regeneration_sources,
            unknown_reason=inputs.unknown_evidence_reason,
        )
    manifest = _reconcile_active_structural_evidence(
        manifest,
        active_page_paths=frozenset(_structural_page_paths(inputs.pages)),
        previous=previous,
        force_unknown=inputs.force_unknown_evidence,
        unknown_reason=inputs.unknown_evidence_reason,
    )
    manifest = _downgrade_incompatible_tombstones(
        manifest,
        current_producer=envelope.bundle.producer,
        previous_producer=previous_producer,
    )
    observations = collect_link_observations(
        inputs.pages,
        inputs.content_by_page,
        existing_asset_paths=inputs.asset_paths,
    )
    knowledge_extensions = _application_knowledge_extensions(
        inputs,
        inventory=inventory,
        module_page_map=module_page_map,
        occurrence_page_map=occurrence_page_map,
    )
    knowledge = build_knowledge_index(
        KnowledgeIndexInputs(
            envelope=envelope,
            pages=inputs.pages,
            content_by_page=inputs.content_by_page,
            surface_index_bytes=surface_bytes,
            page_source_mappings=manifest.page_source_mappings,
            evidence_baselines=manifest.evidence_baselines,
            tombstones=manifest.tombstones,
            link_observations=observations,
            extensions=knowledge_extensions,
        )
    )
    knowledge_bytes = serialize_knowledge_index(knowledge).encode("utf-8")
    return build_knowledge_commit_plan(
        inputs.wiki_dir,
        surface_index_bytes=surface_bytes,
        knowledge_index_bytes=knowledge_bytes,
        manifest=manifest,
    )


def _application_knowledge_extensions(
    inputs: KnowledgeGenerationInputs,
    *,
    inventory: Mapping[str, Mapping[str, Any]],
    module_page_map: Mapping[str, str],
    occurrence_page_map: Mapping[tuple[str, str, int], str],
) -> dict[str, Any]:
    """Build reserved extensions from the exact final evaluated snapshot."""

    extensions = dict(inputs.knowledge_extensions)
    for key in (
        TYPED_GRAPH_EXTENSION_KEY,
        SECTION_OWNERSHIP_EXTENSION_KEY,
    ):
        if key in extensions:
            raise KnowledgeGenerationError(
                f"knowledge_extensions.{key}",
                "is application-owned and cannot be supplied by callers",
            )

    graph = materialize_typed_graph(
        KnowledgeGraphInputs(
            inventory=inventory,
            concepts=_graph_concepts(
                inputs.pages,
                module_page_map=module_page_map,
                occurrence_page_map=occurrence_page_map,
            ),
            call_edges=inputs.call_edges,
            dependency_observations=inputs.dependency_observations,
            entrypoint_observations=inputs.entrypoint_observations,
            flows=inputs.flows,
            data_flows=inputs.data_flows,
            external_dependencies=inputs.external_dependencies,
            analyzer_limitations=inputs.graph_analyzer_limitations,
            evidence_limit=inputs.graph_evidence_limit,
        )
    )
    extensions[TYPED_GRAPH_EXTENSION_KEY] = graph

    section_pages = []
    for page in inputs.pages:
        try:
            markdown = inputs.content_by_page[page.relative_path]
        except KeyError as exc:
            raise KnowledgeGenerationError(
                f"content_by_page.{page.relative_path}",
                "is required for section ownership",
            ) from exc
        section_pages.append(
            observe_page_sections(
                markdown,
                page.mcp_uri,
                page.kind,
            )
        )
    extensions.update(section_ownership_extension(section_pages))
    return extensions


def _graph_concepts(
    pages: Sequence[WikiSurfacePage],
    *,
    module_page_map: Mapping[str, str],
    occurrence_page_map: Mapping[tuple[str, str, int], str],
) -> tuple[GraphConcept, ...]:
    """Project final surface coordinates into graph ownership coordinates."""

    module_source_by_page = {
        page_id: source_path for source_path, page_id in module_page_map.items()
    }
    entity_by_page = {
        page_id: coordinate
        for coordinate, page_id in occurrence_page_map.items()
    }
    concepts: list[GraphConcept] = []
    for page in pages:
        source_path: str | None = None
        symbol: str | None = None
        occurrence: int | None = None
        if page.kind is PageKind.MODULES:
            source_path = module_source_by_page.get(page.page_id)
        elif page.kind is PageKind.ENTITIES:
            coordinate = entity_by_page.get(page.page_id)
            if coordinate is not None:
                symbol, source_path, occurrence = coordinate
        concepts.append(
            GraphConcept(
                locator=page.mcp_uri,
                concept_kind=concept_kind_for_page_kind(page.kind).value,
                source_path=source_path,
                symbol=symbol,
                occurrence=occurrence,
                page_id=page.page_id,
            )
        )
    return tuple(concepts)


def _preserve_unchanged_unknown_baselines(
    baselines: Mapping[str, ConceptObservationBasis],
    previous: SyncManifest | None,
    source_hashes: Mapping[str, str],
    regenerated_page_paths: frozenset[str],
) -> dict[str, ConceptObservationBasis | ManifestEvidenceBaseline]:
    """Keep unrecoverable provenance unknown until its source is regenerated.

    A reseed establishes current source hashes without proving that retained
    Markdown was generated from those bytes.  Ordinary no-op runs therefore
    preserve its unknown baseline.  A command that explicitly regenerated a
    page can establish a fresh known basis even when the source hash did not
    change.  Repair-specific unknowns are intentionally excluded: sync marks
    those sources pending so the following run regenerates their pages and can
    establish a known basis.
    """

    result: dict[str, ConceptObservationBasis | ManifestEvidenceBaseline] = dict(
        baselines
    )
    if previous is None:
        return result
    for page_path, prior in previous.evidence_baselines.items():
        if (
            prior.is_known
            or prior.unknown_reason == MANIFEST_REPAIR_UNAVAILABLE
            or page_path not in baselines
            or page_path in regenerated_page_paths
        ):
            continue
        mapping = previous.page_source_mappings.get(page_path)
        if mapping is None:
            continue
        current_basis = baselines[page_path]
        previous_source = previous.sources.get(mapping.source_path)
        previous_hash = (
            previous_source.get("hash")
            if isinstance(previous_source, Mapping)
            else None
        )
        if (
            current_basis.source_path == mapping.source_path
            and source_hashes.get(mapping.source_path) == previous_hash
        ):
            result[page_path] = prior
    return result


def _validated_evidence_page_paths(
    value: AbstractSet[str],
    current_baselines: Mapping[str, ConceptObservationBasis],
    field_name: str,
) -> frozenset[str]:
    if isinstance(value, (str, bytes)) or not isinstance(value, AbstractSet):
        raise KnowledgeGenerationError(
            field_name,
            "must be a set of structural page paths",
        )
    result: set[str] = set()
    for page_path in value:
        if not isinstance(page_path, str) or page_path not in current_baselines:
            raise KnowledgeGenerationError(
                field_name,
                f"contains unknown structural page path {page_path!r}",
            )
        result.add(page_path)
    return frozenset(result)


def _mark_untrusted_evidence(
    current_baselines: Mapping[str, ConceptObservationBasis],
    selected_baselines: Mapping[
        str, ConceptObservationBasis | ManifestEvidenceBaseline
    ],
    untrusted_page_paths: AbstractSet[str],
    previous: SyncManifest | None,
    source_hashes: Mapping[str, str],
    *,
    unknown_reason: str,
) -> tuple[
    dict[str, ConceptObservationBasis | ManifestEvidenceBaseline],
    frozenset[str],
]:
    """Avoid claiming fresh evidence for Markdown a command did not rewrite.

    A prior known basis remains valid only when it exactly equals the current
    basis and its source commitment is unchanged. Otherwise the source is
    omitted from the operational manifest so the next normal sync observes it
    as pending and regenerates every structural page derived from that source.
    """

    result = dict(selected_baselines)
    pending_sources: set[str] = set()
    for page_path in sorted(untrusted_page_paths):
        current = current_baselines[page_path]
        prior = (
            previous.evidence_baselines.get(page_path) if previous is not None else None
        )
        prior_mapping = (
            previous.page_source_mappings.get(page_path)
            if previous is not None
            else None
        )
        prior_source = (
            previous.sources.get(current.source_path) if previous is not None else None
        )
        prior_source_hash = (
            prior_source.get("hash") if isinstance(prior_source, Mapping) else None
        )
        if (
            prior is not None
            and prior.is_known
            and prior.basis == current
            and prior_mapping is not None
            and prior_mapping.source_path == current.source_path
            and prior_source_hash == source_hashes[current.source_path]
        ):
            result[page_path] = prior
            continue
        result[page_path] = ManifestEvidenceBaseline.unknown(unknown_reason)
        pending_sources.add(current.source_path)
    return result, frozenset(pending_sources)


def _defer_sources_for_regeneration(
    manifest: SyncManifest,
    source_paths: frozenset[str],
    *,
    unknown_reason: str,
) -> SyncManifest:
    """Retain page coordinates but make skipped source evidence explicitly pending."""

    sources = {
        source_path: dict(source_info)
        for source_path, source_info in manifest.sources.items()
        if source_path not in source_paths
    }
    baselines = {
        page_path: baseline
        for page_path, baseline in manifest.evidence_baselines.items()
        if (
            manifest.page_source_mappings.get(page_path) is None
            or manifest.page_source_mappings[page_path].source_path not in source_paths
        )
    }
    tombstones = dict(manifest.tombstones)
    for page_path, mapping in manifest.page_source_mappings.items():
        if mapping.source_path not in source_paths:
            continue
        tombstones[page_path] = ManifestTombstone(
            reason=TOMBSTONE_UNKNOWN_PROVENANCE,
            unknown_reason=unknown_reason,
        )
    return SyncManifest(
        sources=sources,
        surfaces=manifest.surfaces,
        generation_inputs=manifest.generation_inputs,
        page_source_mappings=manifest.page_source_mappings,
        evidence_baselines=baselines,
        tombstones=tombstones,
        artifact_hashes=None,
    )


def _reconcile_active_structural_evidence(
    manifest: SyncManifest,
    *,
    active_page_paths: frozenset[str],
    previous: SyncManifest | None,
    force_unknown: bool,
    unknown_reason: str,
) -> SyncManifest:
    """Restrict operational evidence to active Markdown structural pages.

    Seed and repair intentionally leave Markdown untouched, so current
    inventory may describe pages that do not exist.  Conversely an active
    retained page may no longer have a live source coordinate.  The manifest
    commits only the active page set: mapped live pages receive an explicit
    baseline and unmapped/removed pages receive an unknown-provenance
    tombstone.  No evidence is inferred from page text.
    """

    mappings = {
        path: mapping
        for path, mapping in manifest.page_source_mappings.items()
        if path in active_page_paths
    }
    baselines = {
        path: baseline
        for path, baseline in manifest.evidence_baselines.items()
        if path in active_page_paths
    }
    tombstones = {
        path: tombstone
        for path, tombstone in manifest.tombstones.items()
        if path in active_page_paths
    }

    for page_path in active_page_paths:
        mapping = mappings.get(page_path)
        has_live_source = (
            mapping is not None and mapping.source_path in manifest.sources
        )
        if force_unknown:
            reason = (
                _prior_explicit_unknown_reason(
                    previous,
                    page_path,
                )
                or unknown_reason
            )
            if has_live_source:
                baselines[page_path] = ManifestEvidenceBaseline.unknown(reason)
                tombstones.pop(page_path, None)
            else:
                baselines.pop(page_path, None)
                tombstones[page_path] = ManifestTombstone(
                    reason=TOMBSTONE_UNKNOWN_PROVENANCE,
                    unknown_reason=reason,
                )
            continue
        if page_path in baselines or page_path in tombstones:
            continue
        if has_live_source:
            baselines[page_path] = ManifestEvidenceBaseline.unknown(unknown_reason)
        else:
            tombstones[page_path] = ManifestTombstone(
                reason=TOMBSTONE_UNKNOWN_PROVENANCE,
                unknown_reason=unknown_reason,
            )

    sources = {
        source_path: dict(source_info)
        for source_path, source_info in manifest.sources.items()
    }
    if force_unknown and unknown_reason == MANIFEST_REPAIR_UNAVAILABLE:
        active_source_paths = {
            mapping.source_path
            for mapping in mappings.values()
            if mapping.source_path in sources
        }
        sources = {
            source_path: source_info
            for source_path, source_info in sources.items()
            if source_path in active_source_paths
        }

    return SyncManifest(
        sources=sources,
        surfaces=manifest.surfaces,
        generation_inputs=manifest.generation_inputs,
        page_source_mappings=mappings,
        evidence_baselines=baselines,
        tombstones=tombstones,
        artifact_hashes=None,
    )


def _validated_previous_producer(
    value: ProducerRecord | None,
) -> ProducerRecord | None:
    if value is None:
        return None
    if not isinstance(value, ProducerRecord):
        raise KnowledgeGenerationError(
            "previous_producer",
            "must be a validated ProducerRecord or None",
        )
    return value


def _downgrade_incompatible_tombstones(
    manifest: SyncManifest,
    *,
    current_producer: ProducerRecord,
    previous_producer: ProducerRecord | None,
) -> SyncManifest:
    """Do not bind historical evidence to a changed same-ID producer.

    A source-missing basis predates the current extraction run. Reusing its
    extractor ID is safe only when both the prior committed tool record and
    referenced extractor record equal their current normalized records. If
    either prior basis is unavailable or changed, preserve the stale page but
    make its provenance explicitly unknown instead of attributing it to the
    current producer.
    """

    active_extractor_refs = {
        baseline.basis.extractor_ref
        for baseline in manifest.evidence_baselines.values()
        if baseline.basis is not None
    }
    current_by_id = {
        component.component_id: component
        for component in current_producer.extractors
        if component.component_id in active_extractor_refs
    }
    previous_by_id = (
        None
        if previous_producer is None
        else {
            component.component_id: component
            for component in previous_producer.extractors
        }
    )
    tombstones = dict(manifest.tombstones)
    changed = False
    for page_path, tombstone in manifest.tombstones.items():
        basis = tombstone.last_valid_basis
        if basis is None:
            continue
        current = current_by_id.get(basis.extractor_ref)
        previous = (
            None if previous_by_id is None else previous_by_id.get(basis.extractor_ref)
        )
        if (
            previous_producer is not None
            and previous_producer.tool == current_producer.tool
            and (current is None or previous == current)
        ):
            continue
        tombstones[page_path] = ManifestTombstone(
            reason=TOMBSTONE_UNKNOWN_PROVENANCE,
            unknown_reason=PRODUCER_BASIS_INCOMPATIBLE,
        )
        changed = True
    if not changed:
        return manifest
    return SyncManifest(
        sources=manifest.sources,
        surfaces=manifest.surfaces,
        generation_inputs=manifest.generation_inputs,
        page_source_mappings=manifest.page_source_mappings,
        evidence_baselines=manifest.evidence_baselines,
        tombstones=tombstones,
        artifact_hashes=None,
    )


def _prior_explicit_unknown_reason(
    previous: SyncManifest | None,
    page_path: str,
) -> str | None:
    if previous is None:
        return None
    baseline = previous.evidence_baselines.get(page_path)
    if (
        baseline is not None
        and not baseline.is_known
        and baseline.unknown_reason is not None
    ):
        return baseline.unknown_reason
    tombstone = previous.tombstones.get(page_path)
    if tombstone is not None and tombstone.unknown_reason is not None:
        return tombstone.unknown_reason
    return None


def _validated_inventory(
    value: object,
) -> dict[str, Mapping[str, Any]]:
    if not isinstance(value, Mapping):
        raise KnowledgeGenerationError("inventory", "must be an object")
    result: dict[str, Mapping[str, Any]] = {}
    for source_path, file_data in value.items():
        if not isinstance(source_path, str):
            raise KnowledgeGenerationError(
                "inventory",
                "must use string source paths",
            )
        if not isinstance(file_data, Mapping):
            raise KnowledgeGenerationError(
                f"inventory.{source_path}",
                "must be an object",
            )
        classes = file_data.get("classes", [])
        if not isinstance(classes, list):
            raise KnowledgeGenerationError(
                f"inventory.{source_path}.classes",
                "must be an array",
            )
        for index, entity in enumerate(classes):
            if not isinstance(entity, Mapping):
                raise KnowledgeGenerationError(
                    f"inventory.{source_path}.classes[{index}]",
                    "must be an object",
                )
            name = entity.get("name")
            if not isinstance(name, str) or not name:
                raise KnowledgeGenerationError(
                    f"inventory.{source_path}.classes[{index}].name",
                    "must be a non-empty string",
                )
        result[source_path] = file_data
    return result


def _validated_source_hashes(
    inventory: Mapping[str, object],
    value: object,
) -> dict[str, str]:
    hashes = _exact_source_mapping(
        inventory,
        value,
        "source_content_hashes",
        str,
    )
    for source_path, content_hash in hashes.items():
        if not is_valid_sha256(content_hash):
            raise KnowledgeGenerationError(
                f"source_content_hashes.{source_path}",
                "must be a canonical lowercase SHA-256 value",
            )
    return hashes


def _validated_consumed_inputs(
    inventory: Mapping[str, object],
    source_hashes: Mapping[str, str],
    value: object,
) -> tuple[ConsumedInput, ...]:
    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence):
        raise KnowledgeGenerationError(
            "consumed_inputs",
            "must be a sequence of ConsumedInput values",
        )
    consumed = tuple(value)
    by_path: dict[str, ConsumedInput] = {}
    for index, item in enumerate(consumed):
        if not isinstance(item, ConsumedInput):
            raise KnowledgeGenerationError(
                f"consumed_inputs[{index}]",
                "must be a ConsumedInput",
            )
        if item.path in by_path:
            raise KnowledgeGenerationError(
                f"consumed_inputs[{index}].path",
                f"duplicates consumed path {item.path!r}",
            )
        by_path[item.path] = item
    for source_path in inventory:
        item = by_path.get(source_path)
        if item is None:
            raise KnowledgeGenerationError(
                f"consumed_inputs.{source_path}",
                "must commit every inventory source",
            )
        if item.content_hash != source_hashes[source_path]:
            raise KnowledgeGenerationError(
                f"consumed_inputs.{source_path}.content_hash",
                "does not match source_content_hashes",
            )
    return consumed


def _validated_page_maps(
    inventory: Mapping[str, Mapping[str, Any]],
    module_value: object,
    occurrence_value: object,
) -> tuple[
    dict[str, str],
    dict[tuple[str, str], str],
    dict[tuple[str, str, int], str],
]:
    if not isinstance(module_value, Mapping):
        raise KnowledgeGenerationError("module_page_map", "must be an object")
    if any(not isinstance(path, str) for path in module_value):
        raise KnowledgeGenerationError(
            "module_page_map",
            "must use string source paths",
        )
    if set(module_value) != set(inventory):
        _raise_page_map_parity(
            "module_page_map",
            set(inventory),
            set(module_value),
        )
    module_map: dict[str, str] = {}
    for source_path, page_id in module_value.items():
        if not isinstance(page_id, str) or not page_id:
            raise KnowledgeGenerationError(
                f"module_page_map.{source_path}",
                "must be a non-empty page id",
            )
        module_map[source_path] = page_id

    if not isinstance(occurrence_value, Mapping):
        raise KnowledgeGenerationError(
            "entity_occurrence_page_map",
            "must be an object",
        )
    expected: set[tuple[str, str, int]] = set()
    for source_path, file_data in inventory.items():
        occurrences: dict[str, int] = {}
        for entity in file_data.get("classes", []):
            assert isinstance(entity, Mapping)
            name = entity["name"]
            assert isinstance(name, str)
            occurrences[name] = occurrences.get(name, 0) + 1
            expected.add((name, source_path, occurrences[name]))
    actual = set(occurrence_value)
    if actual != expected:
        _raise_page_map_parity(
            "entity_occurrence_page_map",
            expected,
            actual,
        )

    occurrence_map: dict[tuple[str, str, int], str] = {}
    entity_map: dict[tuple[str, str], str] = {}
    for coordinate, page_id in occurrence_value.items():
        if (
            not isinstance(coordinate, tuple)
            or len(coordinate) != 3
            or not isinstance(coordinate[0], str)
            or not isinstance(coordinate[1], str)
            or isinstance(coordinate[2], bool)
            or not isinstance(coordinate[2], int)
        ):
            raise KnowledgeGenerationError(
                "entity_occurrence_page_map",
                "must use (entity name, source path, occurrence) tuple keys",
            )
        if not isinstance(page_id, str) or not page_id:
            raise KnowledgeGenerationError(
                f"entity_occurrence_page_map.{coordinate!r}",
                "must be a non-empty page id",
            )
        occurrence_map[coordinate] = page_id
        entity_map.setdefault((coordinate[0], coordinate[1]), page_id)
    return module_map, entity_map, occurrence_map


def _raise_page_map_parity(
    field: str,
    expected: set[Any],
    actual: set[Any],
) -> None:
    missing = expected - actual
    if missing:
        value = min(missing, key=repr)
        raise KnowledgeGenerationError(
            field,
            f"is missing evaluated coordinate {value!r}",
        )
    value = min(actual - expected, key=repr)
    raise KnowledgeGenerationError(
        field,
        f"contains unknown evaluated coordinate {value!r}",
    )


def _exact_source_mapping(
    inventory: Mapping[str, object],
    value: object,
    field: str,
    value_type: type,
) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise KnowledgeGenerationError(field, "must be an object")
    if any(not isinstance(path, str) for path in value):
        raise KnowledgeGenerationError(field, "must use string source paths")
    if set(value) != set(inventory):
        _raise_page_map_parity(field, set(inventory), set(value))
    result: dict[str, Any] = {}
    for source_path, item in value.items():
        if value_type is bool:
            valid = isinstance(item, bool)
        else:
            valid = isinstance(item, value_type) and bool(item)
        if not valid:
            expected = "a boolean" if value_type is bool else "a non-empty string"
            raise KnowledgeGenerationError(
                f"{field}.{source_path}",
                f"must be {expected}",
            )
        result[source_path] = item
    return result


def _build_evidence_baselines(
    inventory: Mapping[str, Mapping[str, Any]],
    source_hashes: Mapping[str, str],
    module_page_map: Mapping[str, str],
    occurrence_page_map: Mapping[tuple[str, str, int], str],
    extractor_refs: Mapping[str, str],
    completeness: Mapping[str, bool],
) -> dict[str, ConceptObservationBasis]:
    baselines: dict[str, ConceptObservationBasis] = {}
    for source_path, file_data in inventory.items():
        module_path = f"modules/{module_page_map[source_path]}.md"
        baselines[module_path] = build_module_observation_basis(
            source_path=source_path,
            file_data=file_data,
            source_content_hash=source_hashes[source_path],
            extractor_ref=extractor_refs[source_path],
            inventory_complete=completeness[source_path],
        )
        occurrences: dict[str, int] = {}
        for entity in file_data.get("classes", []):
            assert isinstance(entity, Mapping)
            name = entity["name"]
            assert isinstance(name, str)
            occurrences[name] = occurrences.get(name, 0) + 1
            occurrence = occurrences[name]
            page_id = occurrence_page_map[(name, source_path, occurrence)]
            baselines[f"entities/{page_id}.md"] = build_entity_observation_basis(
                source_path=source_path,
                file_data=file_data,
                entity_name=name,
                occurrence=occurrence,
                source_content_hash=source_hashes[source_path],
                extractor_ref=extractor_refs[source_path],
                inventory_complete=completeness[source_path],
            )
    return baselines


def _surface_index_bytes(
    exact_bytes: object,
    payload: object,
) -> bytes:
    if (exact_bytes is None) == (payload is None):
        raise KnowledgeGenerationError(
            "surface_index",
            "requires exactly one of surface_index_bytes or surface_index_payload",
        )
    if exact_bytes is not None:
        if not isinstance(exact_bytes, bytes):
            raise KnowledgeGenerationError(
                "surface_index_bytes",
                "must be bytes",
            )
        result = exact_bytes
    else:
        if not isinstance(payload, Mapping):
            raise KnowledgeGenerationError(
                "surface_index_payload",
                "must be an object",
            )
        try:
            result = (
                json.dumps(
                    payload,
                    indent=2,
                    sort_keys=True,
                    allow_nan=False,
                )
                + "\n"
            ).encode("utf-8")
        except (RecursionError, TypeError, UnicodeEncodeError, ValueError) as exc:
            raise KnowledgeGenerationError(
                "surface_index_payload",
                "cannot be encoded as deterministic surface-index v1 JSON",
            ) from exc
    validate_surface_index_bytes(result)
    return result


def _next_manifest_mapping(
    supplied: Mapping[str, Any] | None,
    previous: Mapping[str, Any],
) -> Mapping[str, Any]:
    if supplied is None:
        return previous
    if not isinstance(supplied, Mapping):
        raise KnowledgeGenerationError(
            "manifest_state",
            "must be an object",
        )
    return supplied


def _structural_page_paths(
    pages: Sequence[WikiSurfacePage],
) -> tuple[str, ...]:
    if isinstance(pages, (str, bytes)) or not isinstance(pages, Sequence):
        raise KnowledgeGenerationError(
            "pages",
            "must be a sequence of WikiSurfacePage values",
        )
    result: list[str] = []
    for index, page in enumerate(pages):
        if not isinstance(page, WikiSurfacePage):
            raise KnowledgeGenerationError(
                f"pages[{index}]",
                "must be a WikiSurfacePage",
            )
        if page.kind in {PageKind.MODULES, PageKind.ENTITIES}:
            result.append(page.relative_path)
    return tuple(result)


__all__ = [
    "KnowledgeGenerationError",
    "KnowledgeGenerationInputs",
    "build_knowledge_generation_plan",
]
