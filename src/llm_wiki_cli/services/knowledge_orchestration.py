"""Command-facing orchestration for generated native knowledge artifacts.

The bootstrap, sync, and migration commands already own source discovery,
inventory extraction, Markdown generation, and surface evaluation.  This
module adapts those exact in-memory results to the pure generation planner and
applies the shared atomic commit protocol.  It performs no discovery or
extraction of its own.
"""

from __future__ import annotations

import re
from collections.abc import Iterable, Mapping, Sequence
from collections.abc import Set as AbstractSet
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Any

from .. import __version__
from ..config import AGENT_WORKTREE_DIR_PATTERNS, EXCLUDED_DIRS
from ..extractors.common import (
    BUNDLED_HELPER_IMPLEMENTATION_PATHS,
    is_bundled_helper_implementation_path,
)
from .contracts import KNOWLEDGE_SCHEMA_VERSION
from .knowledge_artifacts import (
    KNOWLEDGE_INDEX_FILENAME,
    FaultInjector,
    KnowledgeArtifactError,
    KnowledgeCommitPlan,
    KnowledgeCommitResult,
    ValidatedKnowledgeArtifacts,
    commit_knowledge_artifacts,
    validate_knowledge_artifacts,
)
from .knowledge_envelope import (
    ConsumedInput,
    ConsumedInputKind,
    ProducerComponentInput,
    RepositoryEvidence,
    build_producer_record,
    collect_git_repository_evidence,
    hash_generation_options,
    plugin_producer_inputs,
)
from .knowledge_evidence import (
    ENTITY_OBSERVATION_SCOPE,
    MODULE_OBSERVATION_SCOPE,
    ConceptObservationBasis,
    build_entity_observation_basis,
    build_module_observation_basis,
    is_valid_sha256,
)
from .knowledge_freshness import LiveKnowledgeEvaluation
from .knowledge_governance import (
    GOVERNANCE_FILENAME,
    ConceptGovernanceReference,
    GovernanceConflictError,
    GovernanceError,
    GovernanceLedger,
    governance_bundle_id_from_knowledge,
    governance_lock,
    load_governance,
    natural_key_for,
    reconcile_concepts,
    save_governance,
    validate_governance_ledger,
)
from .infrastructure_sync import (
    INFRASTRUCTURE_EXTRACTOR_REF,
    INFRASTRUCTURE_SYNC_SCHEMA_VERSION,
    current_infrastructure_bases,
    infrastructure_evidence_by_page,
)
from .knowledge_generation import (
    KnowledgeGenerationError,
    KnowledgeGenerationInputs,
    build_knowledge_generation_plan,
)
from .knowledge_model import (
    KnowledgeIndex,
    ObservationScope,
    ProducerRecord,
    concept_kind_for_page_kind,
)
from .source_snapshot import SourceSnapshot
from .source_selection import (
    SourceSelectionError,
    selection_may_contain_path,
    with_source_selection_generation_input,
)
from .sync_manifest import EVIDENCE_NOT_RECORDED, MANIFEST_FILENAME, SyncManifest
from .wiki_surface_index import (
    SURFACE_INDEX_FILENAME,
    WIKI_SURFACE_INDEX_SCHEMA_VERSION,
    SurfaceIndexEvaluation,
)

_COMPONENT_PART_RE = re.compile(r"[^A-Za-z0-9._-]+")

RUNTIME_GENERATION_INPUT_KEY = "llm-wiki/generation-options/v1"
_RUNTIME_POLICY_KEYS = frozenset(
    {
        "data_flow_enabled",
        "dependency_graph_detail",
        "workflows_enabled",
    }
)
_DEPENDENCY_GRAPH_DETAILS = frozenset({"auto", "module", "package"})
RUNTIME_GENERATION_OPTION_DEFAULTS: dict[str, object] = {
    "api_contracts_enabled": False,
    "data_flow_enabled": True,
    "dependencies_enabled": False,
    "dependency_graph_detail": "auto",
    "exclude_tests": False,
    "flow_categories": None,
    "flows_enabled": False,
    "include_tests": [],
    "preserve_semantic": True,
    "workflows_enabled": True,
}


@dataclass(frozen=True)
class RuntimeKnowledgeInputs:
    """Evaluated command state needed to plan one three-artifact commit."""

    target_wiki_dir: str | Path
    inventory: Mapping[str, Mapping[str, Any]]
    surface: SurfaceIndexEvaluation
    source_snapshot: SourceSnapshot
    module_page_map: Mapping[str, str]
    entity_occurrence_page_map: Mapping[tuple[str, str, int], str]
    repository_evidence: RepositoryEvidence
    inventory_complete: bool
    previous_manifest: SyncManifest | None = None
    next_manifest: SyncManifest | None = None
    manifest_surfaces: Mapping[str, Mapping[str, Any]] | None = None
    manifest_generation_inputs: Mapping[str, object] | None = None
    unknown_evidence_reason: str = EVIDENCE_NOT_RECORDED
    force_unknown_evidence: bool = False
    untrusted_evidence_page_paths: AbstractSet[str] = frozenset()
    regenerated_evidence_page_paths: AbstractSet[str] = frozenset()
    extractor_registry: Mapping[str, str] = field(default_factory=dict)
    plugin_extractor_components: Sequence[Mapping[str, Any]] = ()
    plugin_components: Sequence[Mapping[str, Any]] = ()
    plugin_lock_path: str | None = None
    plugin_lock_hash: str | None = None
    generation_options: Mapping[str, Any] = field(default_factory=dict)
    generation_option_defaults: Mapping[str, Any] = field(default_factory=dict)
    generation_option_allowlist: Sequence[str] = ()
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
    graph_evidence_limit: int = 20
    governance: GovernanceLedger | None = None
    governance_moves: Mapping[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class RuntimeLiveEvaluationInputs:
    """Already evaluated runtime values for one live freshness comparison."""

    knowledge: KnowledgeIndex
    manifest: SyncManifest
    inventory: Mapping[str, Mapping[str, Any]]
    source_snapshot: SourceSnapshot
    generation_options: Mapping[str, Any]
    generation_option_defaults: Mapping[str, Any]
    generation_option_allowlist: Sequence[str]
    infrastructure_inventory: Mapping[str, Mapping[str, Any]] = field(
        default_factory=dict
    )
    missing_source_paths: AbstractSet[str] = frozenset()
    inventory_complete: bool = True
    extractor_registry: Mapping[str, str] = field(default_factory=dict)
    plugin_extractor_components: Sequence[Mapping[str, Any]] = ()
    plugin_components: Sequence[Mapping[str, Any]] = ()


@dataclass(frozen=True)
class PreparedRuntimeGenerationOptions:
    """Canonical writer/reader inputs for the generation-options commitment."""

    values: Mapping[str, Any]
    defaults: Mapping[str, Any]
    allowlist: tuple[str, ...]


def prepare_runtime_generation_options(
    generation_options: Mapping[str, Any],
    *,
    generation_option_defaults: Mapping[str, Any],
    generation_option_allowlist: Sequence[str],
    inventory_complete: bool,
) -> PreparedRuntimeGenerationOptions:
    """Add the evaluated inventory mode to one generation-options projection."""

    if not isinstance(inventory_complete, bool):
        raise TypeError("inventory_complete must be a boolean")
    values = dict(generation_options)
    values["inventory_mode"] = "deep" if inventory_complete else "shallow"
    defaults = dict(generation_option_defaults)
    defaults["inventory_mode"] = "deep"
    allowlist = tuple(
        dict.fromkeys(("inventory_mode", *generation_option_allowlist))
    )
    return PreparedRuntimeGenerationOptions(
        values=values,
        defaults=defaults,
        allowlist=allowlist,
    )


def _runtime_manifest_generation_inputs(
    inputs: RuntimeKnowledgeInputs,
) -> Mapping[str, object]:
    if inputs.next_manifest is not None:
        return inputs.next_manifest.generation_inputs
    if inputs.manifest_generation_inputs is not None:
        return inputs.manifest_generation_inputs
    if inputs.previous_manifest is not None:
        return inputs.previous_manifest.generation_inputs
    return {}


def _infrastructure_extractor_component() -> ProducerComponentInput:
    return ProducerComponentInput(
        component_id=INFRASTRUCTURE_EXTRACTOR_REF,
        version=__version__,
        configuration={
            "observation_schema": INFRASTRUCTURE_SYNC_SCHEMA_VERSION,
        },
    )


def build_runtime_knowledge_plan(
    inputs: RuntimeKnowledgeInputs,
) -> KnowledgeCommitPlan:
    """Build a commit plan from one command's already evaluated run state."""

    if not isinstance(inputs, RuntimeKnowledgeInputs):
        raise TypeError("inputs must be a RuntimeKnowledgeInputs")
    governance = _prepared_runtime_governance(inputs)
    source_hashes = inputs.source_snapshot.hashes_for(inputs.inventory)
    (
        extractor_ref_by_source,
        completeness_by_source,
        extractor_components,
        plugin_components,
    ) = _producer_evidence(
        inputs.inventory,
        inventory_complete=inputs.inventory_complete,
        historical_extractor_refs=_manifest_extractor_refs(inputs.previous_manifest),
        extractor_registry=inputs.extractor_registry,
        plugin_extractor_components=inputs.plugin_extractor_components,
        plugin_components=inputs.plugin_components,
    )
    try:
        generation_inputs = with_source_selection_generation_input(
            _runtime_manifest_generation_inputs(inputs),
            inputs.source_snapshot.source_selection_identity,
            inputs.source_snapshot.source_selection_inputs,
        )
    except SourceSelectionError as exc:
        raise KnowledgeGenerationError(exc.field, exc.message) from exc
    next_manifest = inputs.next_manifest
    if next_manifest is not None:
        next_manifest = next_manifest.with_generation_state(
            surfaces=next_manifest.surfaces,
            generation_inputs=generation_inputs,
        )
    if infrastructure_evidence_by_page(generation_inputs):
        extractor_components = (
            *extractor_components,
            _infrastructure_extractor_component(),
        )
    prepared_generation_options = prepare_runtime_generation_options(
        inputs.generation_options,
        generation_option_defaults=inputs.generation_option_defaults,
        generation_option_allowlist=inputs.generation_option_allowlist,
        inventory_complete=inputs.inventory_complete,
    )
    return build_knowledge_generation_plan(
        KnowledgeGenerationInputs(
            wiki_dir=inputs.target_wiki_dir,
            inventory=inputs.inventory,
            pages=inputs.surface.pages,
            content_by_page=inputs.surface.content_by_path,
            surface_index_bytes=inputs.surface.serialized_bytes,
            surface_index_payload=None,
            source_content_hashes=source_hashes,
            consumed_inputs=_runtime_consumed_inputs(inputs, generation_inputs),
            module_page_map=inputs.module_page_map,
            entity_occurrence_page_map=inputs.entity_occurrence_page_map,
            extractor_ref_by_source=extractor_ref_by_source,
            inventory_complete_by_source=completeness_by_source,
            repository_evidence=inputs.repository_evidence,
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
            extractors=extractor_components,
            plugins=plugin_components,
            previous_producer=_previous_committed_producer(
                inputs.target_wiki_dir,
                inputs.previous_manifest,
            ),
            previous_manifest=inputs.previous_manifest,
            next_manifest=next_manifest,
            asset_paths=inputs.surface.existing_asset_paths,
            manifest_surfaces=inputs.manifest_surfaces,
            manifest_generation_inputs=generation_inputs,
            unknown_evidence_reason=inputs.unknown_evidence_reason,
            force_unknown_evidence=inputs.force_unknown_evidence,
            untrusted_evidence_page_paths=(inputs.untrusted_evidence_page_paths),
            regenerated_evidence_page_paths=(inputs.regenerated_evidence_page_paths),
            call_edges=inputs.call_edges,
            dependency_observations=inputs.dependency_observations,
            entrypoint_observations=inputs.entrypoint_observations,
            flows=inputs.flows,
            data_flows=inputs.data_flows,
            external_dependencies=inputs.external_dependencies,
            graph_analyzer_limitations=inputs.graph_analyzer_limitations,
            graph_evidence_limit=inputs.graph_evidence_limit,
            governance=governance,
        )
    )


def build_runtime_live_evaluation(
    inputs: RuntimeLiveEvaluationInputs,
) -> LiveKnowledgeEvaluation:
    """Adapt one existing inventory/snapshot run to the freshness boundary.

    The caller supplies reliably missing source paths explicitly. This adapter
    performs no source discovery, extraction, filesystem read, or write.
    The caller supplies the effective live generation policy. This adapter
    commits that policy independently through the same canonical hashing path
    as artifact generation.
    """

    if not isinstance(inputs, RuntimeLiveEvaluationInputs):
        raise TypeError("inputs must be a RuntimeLiveEvaluationInputs")
    if not isinstance(inputs.knowledge, KnowledgeIndex):
        raise TypeError("inputs.knowledge must be a KnowledgeIndex")
    if not isinstance(inputs.manifest, SyncManifest):
        raise TypeError("inputs.manifest must be a SyncManifest")
    if not isinstance(inputs.source_snapshot, SourceSnapshot):
        raise TypeError("inputs.source_snapshot must be a SourceSnapshot")
    if not isinstance(inputs.inventory, Mapping):
        raise TypeError("inputs.inventory must be a mapping")
    if not isinstance(inputs.infrastructure_inventory, Mapping):
        raise TypeError("inputs.infrastructure_inventory must be a mapping")

    inventory = dict(inputs.inventory)
    infrastructure_inventory = {
        path: dict(record)
        for path, record in inputs.infrastructure_inventory.items()
    }
    source_hashes = dict(inputs.source_snapshot.hashes_for(inventory))
    recorded_infrastructure_paths = {
        basis.source_path
        for concept in inputs.knowledge.concepts
        if (basis := concept.facets.structure.basis) is not None
        and basis.scope is ObservationScope.INFRASTRUCTURE
        and basis.source_path is not None
    }
    for source_path in sorted(
        set(infrastructure_inventory) | recorded_infrastructure_paths
    ):
        source_hash = inputs.source_snapshot.captured_content_hashes.get(source_path)
        if source_hash is not None:
            source_hashes[source_path] = source_hash
    (
        extractor_ref_by_source,
        _completeness_by_source,
        extractor_components,
        plugin_components,
    ) = _producer_evidence(
        inventory,
        inventory_complete=inputs.inventory_complete,
        extractor_registry=inputs.extractor_registry,
        plugin_extractor_components=inputs.plugin_extractor_components,
        plugin_components=inputs.plugin_components,
    )
    if recorded_infrastructure_paths or infrastructure_inventory:
        extractor_components = (
            *extractor_components,
            _infrastructure_extractor_component(),
        )
    producer = build_producer_record(
        tool=ProducerComponentInput(
            component_id="agent-wiki-cli",
            version=__version__,
            configuration={
                "knowledge_schema": KNOWLEDGE_SCHEMA_VERSION,
                "surface_schema": WIKI_SURFACE_INDEX_SCHEMA_VERSION,
            },
        ),
        extractors=extractor_components,
        plugins=plugin_components,
    )
    prepared_generation_options = prepare_runtime_generation_options(
        inputs.generation_options,
        generation_option_defaults=inputs.generation_option_defaults,
        generation_option_allowlist=inputs.generation_option_allowlist,
        inventory_complete=inputs.inventory_complete,
    )
    return LiveKnowledgeEvaluation(
        schema_version=KNOWLEDGE_SCHEMA_VERSION,
        producer=producer,
        generation_options_hash=hash_generation_options(
            prepared_generation_options.values,
            defaults=prepared_generation_options.defaults,
            allowlist=prepared_generation_options.allowlist,
        ),
        source_content_hashes=source_hashes,
        missing_source_paths=frozenset(inputs.missing_source_paths),
        concept_bases=_runtime_live_concept_bases(
            inputs.knowledge,
            inputs.manifest,
            inventory,
            source_hashes,
            extractor_ref_by_source,
            infrastructure_bases_by_source=current_infrastructure_bases(
                inputs.source_snapshot,
                infrastructure_inventory,
            ),
            inventory_complete=inputs.inventory_complete,
        ),
    )


def _runtime_live_concept_bases(
    knowledge: KnowledgeIndex,
    manifest: SyncManifest,
    inventory: Mapping[str, Mapping[str, Any]],
    source_hashes: Mapping[str, str],
    extractor_ref_by_source: Mapping[str, str],
    *,
    infrastructure_bases_by_source: Mapping[str, ConceptObservationBasis],
    inventory_complete: bool,
) -> dict[str, ConceptObservationBasis]:
    bases: dict[str, ConceptObservationBasis] = {}
    for concept in knowledge.concepts:
        mapping = manifest.page_source_mappings.get(concept.document.canonical_path)
        if mapping is None:
            continue
        source_path = mapping.source_path
        file_data = inventory.get(source_path)
        source_hash = source_hashes.get(source_path)
        extractor_ref = extractor_ref_by_source.get(source_path)
        if file_data is None or source_hash is None or extractor_ref is None:
            continue
        if mapping.scope == MODULE_OBSERVATION_SCOPE:
            basis = build_module_observation_basis(
                source_path=source_path,
                file_data=file_data,
                source_content_hash=source_hash,
                extractor_ref=extractor_ref,
                inventory_complete=inventory_complete,
            )
        elif mapping.scope == ENTITY_OBSERVATION_SCOPE:
            assert mapping.entity_name is not None
            assert mapping.occurrence is not None
            basis = build_entity_observation_basis(
                source_path=source_path,
                file_data=file_data,
                entity_name=mapping.entity_name,
                occurrence=mapping.occurrence,
                source_content_hash=source_hash,
                extractor_ref=extractor_ref,
                inventory_complete=inventory_complete,
            )
        else:
            continue
        bases[concept.locator] = basis
    for concept in knowledge.concepts:
        recorded = concept.facets.structure.basis
        if (
            recorded is None
            or recorded.scope is not ObservationScope.INFRASTRUCTURE
            or recorded.source_path is None
        ):
            continue
        basis = infrastructure_bases_by_source.get(recorded.source_path)
        if basis is not None:
            bases[concept.locator] = basis
    return bases


def _previous_committed_artifacts(
    wiki_dir: str | Path,
    manifest: SyncManifest | None,
) -> ValidatedKnowledgeArtifacts | None:
    """Return the validated prior artifact set without consulting Markdown.

    Markdown may already have been updated by sync, so the full live loader
    would correctly classify the old projections as a mixed snapshot.  This
    narrower check validates the still-committed surface/knowledge/manifest
    trio and its exact marker without consulting current Markdown.
    """

    if manifest is None or manifest.artifact_hashes is None:
        return None
    root = Path(wiki_dir)
    try:
        validated = validate_knowledge_artifacts(
            surface_index_bytes=(root / SURFACE_INDEX_FILENAME).read_bytes(),
            knowledge_index_bytes=(root / KNOWLEDGE_INDEX_FILENAME).read_bytes(),
            manifest=manifest,
        )
    except (KnowledgeArtifactError, OSError, TypeError, ValueError):
        return None
    marker = manifest.artifact_hashes
    if (
        validated.surface_index_hash != marker.surface_index_hash
        or validated.knowledge_index_hash != marker.knowledge_index_hash
        or validated.evaluated_envelope_hash != marker.evaluated_envelope_hash
        or validated.governance_hash != marker.governance_hash
    ):
        return None
    return validated


def committed_governance_bundle_id(
    wiki_dir: str | Path,
    manifest: SyncManifest | None,
) -> str | None:
    """Return a bundle ID only from an intact manifest-committed projection."""

    validated = _previous_committed_artifacts(wiki_dir, manifest)
    if validated is None:
        return None
    return governance_bundle_id_from_knowledge(validated.knowledge)


def _previous_committed_producer(
    wiki_dir: str | Path,
    manifest: SyncManifest | None,
) -> ProducerRecord | None:
    """Return producer evidence only from the prior committed artifact set."""

    validated = _previous_committed_artifacts(wiki_dir, manifest)
    if validated is None:
        return None
    return validated.knowledge.bundle.producer


def finalize_runtime_knowledge(
    inputs: RuntimeKnowledgeInputs,
    *,
    dry_run: bool = False,
    fault_injector: FaultInjector | None = None,
) -> KnowledgeCommitResult:
    """Plan and commit one generated artifact set through the shared protocol."""

    if not isinstance(inputs, RuntimeKnowledgeInputs):
        raise TypeError("inputs must be a RuntimeKnowledgeInputs")
    root = Path(inputs.target_wiki_dir)
    marker_hash = (
        getattr(inputs.previous_manifest.artifact_hashes, "governance_hash", None)
        if (
            inputs.previous_manifest is not None
            and inputs.previous_manifest.artifact_hashes is not None
        )
        else None
    )
    governance_requested = (
        inputs.governance is not None
        or (root / GOVERNANCE_FILENAME).exists()
        or marker_hash is not None
    )
    if not governance_requested:
        return commit_knowledge_artifacts(
            build_runtime_knowledge_plan(inputs),
            dry_run=dry_run,
            fault_injector=fault_injector,
        )
    if dry_run:
        if inputs.governance is not None and (
            (root / GOVERNANCE_FILENAME).exists()
            or (root / GOVERNANCE_FILENAME).is_symlink()
        ):
            loaded = load_governance(root)
            if inputs.governance.content_hash() != loaded.content_hash:
                raise GovernanceConflictError(
                    GOVERNANCE_FILENAME,
                    "supplied governance does not match the live ledger",
                )
        effective = _prepared_runtime_governance(inputs)
        if effective is None:
            raise GovernanceError(
                GOVERNANCE_FILENAME,
                "governance was requested without a ledger",
            )
        return commit_knowledge_artifacts(
            build_runtime_knowledge_plan(
                replace(inputs, governance=effective)
            ),
            dry_run=True,
            fault_injector=fault_injector,
        )

    with governance_lock(root):
        try:
            loaded = load_governance(root)
        except FileNotFoundError:
            loaded = None
        if loaded is None and marker_hash is not None and inputs.governance is None:
            raise GovernanceError(
                GOVERNANCE_FILENAME,
                "is missing but the committed manifest records prior governance; "
                "restore the ledger from version control",
                code="governance-missing",
            )
        if (
            loaded is not None
            and inputs.governance is not None
            and inputs.governance.content_hash() != loaded.content_hash
        ):
            raise GovernanceConflictError(
                GOVERNANCE_FILENAME,
                "supplied governance does not match the live ledger",
            )
        base = inputs.governance or (loaded.ledger if loaded is not None else None)
        if base is None:
            raise GovernanceError(
                GOVERNANCE_FILENAME,
                "governance was requested without a ledger",
            )
        effective = _prepared_runtime_governance(
            replace(inputs, governance=base),
        )
        assert effective is not None
        prepared_inputs = replace(inputs, governance=effective)
        plan = build_runtime_knowledge_plan(prepared_inputs)
        save_governance(
            root,
            effective,
            expected_hash=(
                loaded.content_hash if loaded is not None else None
            ),
        )
        return commit_knowledge_artifacts(
            plan,
            dry_run=False,
            fault_injector=fault_injector,
        )


def _prepared_runtime_governance(
    inputs: RuntimeKnowledgeInputs,
) -> GovernanceLedger | None:
    """Load/reconcile governance without writing or inventing recovery state."""

    root = Path(inputs.target_wiki_dir)
    expected_bundle_id = committed_governance_bundle_id(
        root,
        inputs.previous_manifest,
    )
    if inputs.governance is not None:
        ledger = validate_governance_ledger(
            inputs.governance,
            expected_bundle_id=expected_bundle_id,
        )
    else:
        try:
            ledger = load_governance(
                root,
                expected_bundle_id=expected_bundle_id,
            ).ledger
        except FileNotFoundError:
            marker = (
                inputs.previous_manifest.artifact_hashes
                if inputs.previous_manifest is not None
                else None
            )
            if getattr(marker, "governance_hash", None) is not None:
                raise GovernanceError(
                    GOVERNANCE_FILENAME,
                    "is missing but prior artifacts were governed; restore it "
                    "instead of allocating replacement identities",
                    code="governance-missing",
                )
            return None
    references = []
    for page in inputs.surface.pages:
        concept_kind = concept_kind_for_page_kind(page.kind).value
        references.append(
            ConceptGovernanceReference(
                locator=page.mcp_uri,
                concept_kind=concept_kind,
                natural_key=natural_key_for(
                    concept_kind,
                    page.relative_path,
                ),
            )
        )
    return reconcile_concepts(
        ledger,
        references,
        moves=inputs.governance_moves,
    )


def collect_runtime_repository_evidence(
    source_root: str | Path,
    target_wiki_dir: str | Path,
    *,
    source_snapshot: SourceSnapshot | None = None,
) -> RepositoryEvidence:
    """Collect Git evidence for the evaluated source-selection boundary."""

    source = Path(source_root).resolve()
    target = Path(target_wiki_dir).resolve()
    included_paths: tuple[Path, ...] | None = None
    selection_excludes: tuple[Path, ...] = ()
    worktree_path_filter = None
    if source_snapshot is not None:
        if not isinstance(source_snapshot, SourceSnapshot):
            raise TypeError("source_snapshot must be a SourceSnapshot or None")
        if source_snapshot.root.resolve() != source:
            raise ValueError("source_snapshot root must match source_root")
        policy = source_snapshot.source_selection_policy
        if policy is not None:
            # Root pathspecs retain tracked deletions.  Policy excludes and the
            # eight owned helper implementation paths narrow those roots to the
            # same evaluated source boundary; package markers/locks alongside
            # the helpers remain deliberately included.
            selected_paths = {source / path for path in policy.include}
            selected_paths.add(source / policy.path)
            selected_paths.update(
                source / path
                for path, kinds in source_snapshot.captured_input_kinds.items()
                if ConsumedInputKind.SELECTION.value in kinds
            )
            included_paths = tuple(sorted(selected_paths, key=lambda path: str(path)))
            helper_excludes: set[Path] = set()
            package_roots: set[Path] = set()
            candidate_paths = set(policy.include) | set(
                source_snapshot.selected_regular_paths
            )
            for selected_path in candidate_paths:
                parts = Path(selected_path).parts
                for index, part in enumerate(parts):
                    if part == "llm_wiki_cli":
                        package_roots.add(source.joinpath(*parts[: index + 1]))
            if source.name == "llm_wiki_cli":
                package_roots.add(source)
            for package_root in package_roots:
                for helper_path in BUNDLED_HELPER_IMPLEMENTATION_PATHS:
                    relative = Path(helper_path).relative_to("llm_wiki_cli")
                    candidate = package_root / relative
                    if is_bundled_helper_implementation_path(candidate):
                        helper_excludes.add(candidate)
            selection_excludes = tuple(
                source / path for path in policy.exclude
            ) + tuple(sorted(helper_excludes, key=lambda path: str(path)))

            def configured_worktree_path_filter(candidate: Path) -> bool:
                try:
                    relative = candidate.relative_to(source).as_posix()
                except ValueError:
                    return False
                if relative == policy.path:
                    return True
                if Path(relative).name == ".gitignore":
                    parent = Path(relative).parent.as_posix()
                    try:
                        if selection_may_contain_path(
                            policy,
                            "" if parent == "." else parent,
                        ):
                            return True
                    except SourceSelectionError:
                        return False
                try:
                    return source_snapshot.path_is_effectively_selected(relative)
                except SourceSelectionError:
                    return False

            worktree_path_filter = configured_worktree_path_filter
    return collect_git_repository_evidence(
        source,
        included_worktree_paths=included_paths,
        excluded_worktree_paths=selection_excludes
        + tuple(
            target / filename
            for filename in (
                SURFACE_INDEX_FILENAME,
                KNOWLEDGE_INDEX_FILENAME,
                MANIFEST_FILENAME,
            )
        ),
        excluded_worktree_globs=(
            *(f"**/{name}/**" for name in sorted(EXCLUDED_DIRS)),
            *(
                "**/" + "/".join(pattern) + "/**"
                for pattern in AGENT_WORKTREE_DIR_PATTERNS
            ),
        ),
        worktree_path_filter=worktree_path_filter,
    )


def runtime_generation_options(
    *,
    surfaces: Mapping[str, Mapping[str, Any]],
    generation_inputs: Mapping[str, object] | None = None,
    include_tests: Iterable[str] | None,
    preserve_semantic: bool,
) -> dict[str, object]:
    """Project command policy into one cross-command safe option allowlist."""

    def surface_value(
        name: str,
        key: str,
        default: object,
    ) -> object:
        surface = surfaces.get(name)
        return surface.get(key, default) if isinstance(surface, Mapping) else default

    raw_categories = surface_value("flows", "categories", None)
    categories = (
        sorted({str(value) for value in raw_categories})
        if isinstance(raw_categories, (list, tuple, set, frozenset))
        else None
    )
    persisted_policy = _runtime_policy_from_generation_inputs(generation_inputs)
    data_flow_enabled = (
        RUNTIME_GENERATION_OPTION_DEFAULTS["data_flow_enabled"]
        if persisted_policy is None
        else persisted_policy["data_flow_enabled"]
    )
    dependency_graph_detail = (
        "auto"
        if persisted_policy is None
        else persisted_policy["dependency_graph_detail"]
    )
    workflows_enabled = (
        RUNTIME_GENERATION_OPTION_DEFAULTS["workflows_enabled"]
        if persisted_policy is None
        else persisted_policy["workflows_enabled"]
    )
    return {
        "api_contracts_enabled": bool(surface_value("api_contracts", "enabled", False)),
        "data_flow_enabled": data_flow_enabled,
        "dependencies_enabled": bool(surface_value("dependencies", "enabled", False)),
        "dependency_graph_detail": dependency_graph_detail,
        "exclude_tests": bool(
            surface_value("flows", "exclude_tests", False)
            or surface_value("dependencies", "exclude_tests", False)
        ),
        "flow_categories": categories,
        "flows_enabled": bool(surface_value("flows", "enabled", False)),
        "include_tests": sorted({str(value) for value in (include_tests or ())}),
        "preserve_semantic": bool(preserve_semantic),
        "workflows_enabled": workflows_enabled,
    }


def persist_runtime_generation_policy(
    generation_inputs: Mapping[str, object],
    *,
    data_flow_enabled: bool,
    dependency_graph_detail: str,
    workflows_enabled: bool,
) -> dict[str, object]:
    """Persist bootstrap-only generation policy for later sync parity."""

    policy = {
        "data_flow_enabled": data_flow_enabled,
        "dependency_graph_detail": dependency_graph_detail,
        "workflows_enabled": workflows_enabled,
    }
    _validate_runtime_policy(policy)
    persisted = dict(generation_inputs)
    persisted[RUNTIME_GENERATION_INPUT_KEY] = policy
    return persisted


def _runtime_policy_from_generation_inputs(
    generation_inputs: Mapping[str, object] | None,
) -> dict[str, object] | None:
    if (
        generation_inputs is None
        or RUNTIME_GENERATION_INPUT_KEY not in generation_inputs
    ):
        return None
    raw_policy = generation_inputs[RUNTIME_GENERATION_INPUT_KEY]
    if not isinstance(raw_policy, Mapping):
        raise KnowledgeGenerationError(
            f"manifest_generation_inputs.{RUNTIME_GENERATION_INPUT_KEY}",
            "must be an object",
        )
    policy = dict(raw_policy)
    _validate_runtime_policy(policy)
    return policy


def _validate_runtime_policy(policy: Mapping[str, object]) -> None:
    keys = set(policy)
    if keys != _RUNTIME_POLICY_KEYS:
        missing = sorted(_RUNTIME_POLICY_KEYS - keys)
        if missing:
            field = missing[0]
            message = "is required"
        else:
            field = min(keys - _RUNTIME_POLICY_KEYS)
            message = "is not supported"
        raise KnowledgeGenerationError(
            f"manifest_generation_inputs.{RUNTIME_GENERATION_INPUT_KEY}.{field}",
            message,
        )
    for field in ("data_flow_enabled", "workflows_enabled"):
        if not isinstance(policy[field], bool):
            raise KnowledgeGenerationError(
                f"manifest_generation_inputs.{RUNTIME_GENERATION_INPUT_KEY}.{field}",
                "must be a boolean",
            )
    detail = policy["dependency_graph_detail"]
    if not isinstance(detail, str) or detail not in _DEPENDENCY_GRAPH_DETAILS:
        raise KnowledgeGenerationError(
            "manifest_generation_inputs."
            f"{RUNTIME_GENERATION_INPUT_KEY}.dependency_graph_detail",
            "must be one of: auto, module, package",
        )


def _producer_evidence(
    inventory: Mapping[str, Mapping[str, Any]],
    *,
    inventory_complete: bool,
    historical_extractor_refs: frozenset[str] = frozenset(),
    extractor_registry: Mapping[str, str] | None = None,
    plugin_extractor_components: Sequence[Mapping[str, Any]] = (),
    plugin_components: Sequence[Mapping[str, Any]] = (),
) -> tuple[
    dict[str, str],
    dict[str, bool],
    tuple[ProducerComponentInput, ...],
    tuple[ProducerComponentInput, ...],
]:
    refs: dict[str, str] = {}
    completeness: dict[str, bool] = {}
    components_by_id: dict[str, ProducerComponentInput] = {}
    registry = dict(extractor_registry or {})
    plugin_by_language = _plugin_extractors_by_language(plugin_extractor_components)
    inventory_mode = "deep" if inventory_complete else "shallow"
    for source_path, file_data in inventory.items():
        raw_language = file_data.get("language")
        language = (
            str(raw_language).strip().casefold()
            if raw_language not in (None, "")
            else Path(source_path).suffix.lstrip(".").casefold() or "unknown"
        )
        plugin = plugin_by_language.get(language)
        configuration: Mapping[str, Any] | None
        if plugin is None:
            component_id = _builtin_extractor_id(language)
            version: str | None = __version__
            entry_point = registry.get(language)
            configuration = (
                {
                    "entry_point": entry_point,
                    "inventory_mode": inventory_mode,
                    "language": language,
                }
                if entry_point is not None
                else None
            )
        else:
            plugin_id = str(plugin["plugin_id"])
            component_name = str(plugin["id"])
            component_id = f"{plugin_id}/{component_name}"
            raw_version = plugin.get("plugin_version")
            version = (
                raw_version if isinstance(raw_version, str) and raw_version else None
            )
            configuration = {
                "entry_point": str(plugin["entry_point"]),
                "inventory_mode": inventory_mode,
                "language": language,
                "parallel_safe": plugin.get("parallel_safe") is True,
            }
        refs[source_path] = component_id
        completeness[source_path] = inventory_complete
        components_by_id.setdefault(
            component_id,
            ProducerComponentInput(
                component_id=component_id,
                version=version,
                configuration=configuration,
                limitations=(() if inventory_complete else ("inventory-incomplete",)),
            ),
        )

    components = tuple(
        components_by_id[component_id] for component_id in sorted(components_by_id)
    )
    historical_components = tuple(
        ProducerComponentInput(
            component_id=component_id,
            version=None,
            configuration=None,
            limitations=("historical-evidence",),
        )
        for component_id in sorted(historical_extractor_refs - set(components_by_id))
    )
    selected_plugin_components = (
        plugin_components if plugin_components else plugin_extractor_components
    )
    plugin_ids = {
        str(component["plugin_id"])
        for component in selected_plugin_components
        if isinstance(component, Mapping)
        and isinstance(component.get("plugin_id"), str)
    }
    producer_plugins = plugin_producer_inputs(
        selected_plugin_components,
        plugin_configurations={plugin_id: {} for plugin_id in plugin_ids},
    )
    return (
        refs,
        completeness,
        components + historical_components,
        producer_plugins,
    )


def _builtin_extractor_id(language: str) -> str:
    component_part = _COMPONENT_PART_RE.sub("-", language).strip("-._")
    if not component_part:
        component_part = "unknown"
    return f"llm-wiki/extractor/{component_part}"


def _plugin_extractors_by_language(
    components: Sequence[Mapping[str, Any]],
) -> dict[str, Mapping[str, Any]]:
    by_language: dict[str, Mapping[str, Any]] = {}
    for index, component in enumerate(components):
        if not isinstance(component, Mapping):
            raise KnowledgeGenerationError(
                f"plugin_extractor_components[{index}]",
                "must be an object",
            )
        language = component.get("language")
        plugin_id = component.get("plugin_id")
        component_id = component.get("id")
        entry_point = component.get("entry_point")
        if not isinstance(language, str) or not language.strip():
            raise KnowledgeGenerationError(
                f"plugin_extractor_components[{index}].language",
                "must be a non-empty string",
            )
        for field_name, value in (
            ("plugin_id", plugin_id),
            ("id", component_id),
            ("entry_point", entry_point),
        ):
            if not isinstance(value, str) or not value:
                raise KnowledgeGenerationError(
                    f"plugin_extractor_components[{index}].{field_name}",
                    "must be a non-empty string",
                )
        normalized_language = language.strip().casefold()
        if normalized_language in by_language:
            raise KnowledgeGenerationError(
                f"plugin_extractor_components[{index}].language",
                f"duplicates selected language {normalized_language!r}",
            )
        by_language[normalized_language] = component
    return by_language


def _manifest_extractor_refs(
    manifest: SyncManifest | None,
) -> frozenset[str]:
    if manifest is None:
        return frozenset()
    refs: set[str] = set()
    for baseline in manifest.evidence_baselines.values():
        if baseline.basis is not None:
            refs.add(baseline.basis.extractor_ref)
    for tombstone in manifest.tombstones.values():
        if tombstone.last_valid_basis is not None:
            refs.add(tombstone.last_valid_basis.extractor_ref)
    return frozenset(refs)


def _runtime_consumed_inputs(
    inputs: RuntimeKnowledgeInputs,
    generation_inputs: Mapping[str, object],
) -> tuple[ConsumedInput, ...]:
    """Add explicitly selected inputs to the already captured source basis.

    Source discovery captures normal language, infrastructure, package, YAML,
    and selection inputs in one pass.  An explicitly selected OpenAPI JSON
    document is not otherwise a source-tree candidate, so the command's
    already validated generation-input commitment is merged here without
    rereading it.  When an OpenAPI YAML file was captured by discovery, its
    more specific classification replaces the generic YAML classification.
    """

    consumed_by_path = {
        item.path: item for item in inputs.source_snapshot.to_consumed_inputs()
    }
    _merge_explicit_consumed_input(
        consumed_by_path,
        path=inputs.plugin_lock_path,
        content_hash=inputs.plugin_lock_hash,
        kind=ConsumedInputKind.PLUGIN,
        field="plugin_lock",
    )
    openapi = generation_inputs.get("openapi")
    if openapi is None:
        return tuple(consumed_by_path[path] for path in sorted(consumed_by_path))
    if not isinstance(openapi, Mapping):
        raise KnowledgeGenerationError(
            "manifest_generation_inputs.openapi",
            "must be an object",
        )
    path = openapi.get("path")
    if not isinstance(path, str) or not path:
        raise KnowledgeGenerationError(
            "manifest_generation_inputs.openapi.path",
            "must be a non-empty repository-relative path",
        )
    content_hash = openapi.get("sha256")
    if not is_valid_sha256(content_hash):
        raise KnowledgeGenerationError(
            "manifest_generation_inputs.openapi.sha256",
            "must be a canonical lowercase SHA-256 value",
        )
    assert isinstance(content_hash, str)
    _merge_explicit_consumed_input(
        consumed_by_path,
        path=path,
        content_hash=content_hash,
        kind=ConsumedInputKind.OPENAPI,
        field="manifest_generation_inputs.openapi",
    )
    return tuple(consumed_by_path[path] for path in sorted(consumed_by_path))


def _merge_explicit_consumed_input(
    consumed_by_path: dict[str, ConsumedInput],
    *,
    path: str | None,
    content_hash: str | None,
    kind: ConsumedInputKind,
    field: str,
) -> None:
    if (path is None) != (content_hash is None):
        raise KnowledgeGenerationError(
            field,
            "path and content hash must be supplied together",
        )
    if path is None:
        return
    if not path:
        raise KnowledgeGenerationError(
            f"{field}.path",
            "must be a non-empty repository-relative path",
        )
    if not is_valid_sha256(content_hash):
        raise KnowledgeGenerationError(
            f"{field}.sha256",
            "must be a canonical lowercase SHA-256 value",
        )
    assert isinstance(content_hash, str)
    captured = consumed_by_path.get(path)
    if captured is not None and captured.content_hash != content_hash:
        raise KnowledgeGenerationError(
            f"{field}.sha256",
            "does not match the exact source-snapshot commitment",
        )
    consumed_by_path[path] = ConsumedInput(
        path=path,
        content_hash=content_hash,
        kind=kind,
    )


__all__ = [
    "RUNTIME_GENERATION_INPUT_KEY",
    "RUNTIME_GENERATION_OPTION_DEFAULTS",
    "PreparedRuntimeGenerationOptions",
    "RuntimeKnowledgeInputs",
    "RuntimeLiveEvaluationInputs",
    "build_runtime_knowledge_plan",
    "build_runtime_live_evaluation",
    "collect_runtime_repository_evidence",
    "committed_governance_bundle_id",
    "finalize_runtime_knowledge",
    "persist_runtime_generation_policy",
    "prepare_runtime_generation_options",
    "runtime_generation_options",
]
