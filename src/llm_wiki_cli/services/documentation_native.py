"""Native-knowledge evaluation and refresh for standalone documentation runs.

This module is an internal bridge between the standalone documentation
controller and the native knowledge runtime.  It owns no source discovery
policy of its own: callers supply the already approved source/wiki roots and
the explicit source-plugin trust decision.  Artifact metadata is never used to
select plugins.
"""

from __future__ import annotations

import hashlib
import json
import stat
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath
from typing import Any, Mapping, TypeGuard

from .api_contracts import (
    ApiContractError,
    attach_routes_to_entry_points,
    build_api_contracts,
)
from .data_flow import analyze_data_flow, build_data_flow_context
from .entrypoints import (
    build_flow,
    detect_entry_points,
    read_console_scripts,
)
from .extraction_jobs import ExtractionJobRequest
from .inventory_cache import InventoryCacheOptions
from .infrastructure_inventory import get_yaml_infrastructure_inventory
from .knowledge_artifacts import (
    KNOWLEDGE_INDEX_FILENAME,
    CommitStage,
    KnowledgeArtifactError,
    KnowledgeCommitResult,
    validate_knowledge_artifacts,
    validate_surface_index_bytes,
)
from .knowledge_consumption import KnowledgeReadView
from .knowledge_envelope import (
    ConsumedInput,
    ConsumedInputKind,
    hash_source_snapshot,
)
from .knowledge_freshness import (
    KnowledgeFreshnessReport,
    evaluate_knowledge_freshness,
)
from .knowledge_evidence import is_valid_sha256
from .knowledge_model import ComputedFreshness, KnowledgeIndex, ObservationScope
from .knowledge_orchestration import (
    RUNTIME_GENERATION_OPTION_DEFAULTS,
    RuntimeKnowledgeInputs,
    RuntimeLiveEvaluationInputs,
    build_runtime_live_evaluation,
    collect_runtime_repository_evidence,
    finalize_runtime_knowledge,
    runtime_generation_options,
)
from .paths import is_test_source_path
from .source_snapshot import (
    SourceSnapshot,
    SourceSnapshotError,
    build_source_snapshot,
    capture_source_selection_inputs,
)
from .source_selection import (
    SourceSelectionError,
    resolve_source_selection,
    source_selection_identity_from_generation_inputs,
    source_selection_inputs_from_generation_inputs,
    validate_persisted_source_selection_identity,
)
from .sync_manifest import (
    LEGACY_MANIFEST_VERSION,
    MANIFEST_FILENAME,
    MANIFEST_VERSION,
    SyncManifest,
)
from .validation import is_portable_relative_path
from .wiki_surface import PageKind
from .wiki_surface_index import (
    SURFACE_INDEX_FILENAME,
    WIKI_SURFACE_INDEX_SCHEMA_VERSION,
    SurfaceIndexEvaluation,
    evaluate_surface_index,
)


class DocumentationNativeError(RuntimeError):
    """Fail-closed native evaluation or refresh error."""


@dataclass(frozen=True)
class DocumentationNativeFreshness:
    """Independent v5 compatibility result for standalone adoption."""

    current: bool
    reasons: tuple[str, ...]
    report: KnowledgeFreshnessReport
    source_mismatches: tuple[str, ...] = ()


@dataclass(frozen=True)
class DocumentationNativeRefresh:
    """One controller-owned native projection refresh."""

    commit: KnowledgeCommitResult
    markdown_before: Mapping[str, str]
    markdown_after: Mapping[str, str]
    artifact_hashes_before: Mapping[str, str]
    artifact_hashes_after: Mapping[str, str]
    knowledge_view: KnowledgeReadView | None = field(
        default=None,
        repr=False,
        compare=False,
    )

    @property
    def changed(self) -> bool:
        return self.commit.changed

    @property
    def artifact_hashes(self) -> Mapping[str, str]:
        return self.artifact_hashes_after


@dataclass(frozen=True)
class _DocumentationNativeRuntime:
    inventory: Mapping[str, Mapping[str, Any]]
    infrastructure_inventory: Mapping[str, Mapping[str, Any]]
    inventory_result: Any
    source_snapshot: SourceSnapshot
    uncaptured_generation_inputs: tuple[str, ...] = ()


@dataclass(frozen=True)
class _DocumentationPageMaps:
    module: Mapping[str, str]
    entity: Mapping[tuple[str, str], str]
    occurrence: Mapping[tuple[str, str, int], str]


def _native_source_snapshot_preflight(
    *,
    source_root: str | Path,
    manifest: SyncManifest,
    source_selection: str | Path | None,
    operation: str,
    allow_same_path_identity_update: bool = False,
) -> tuple[Path, SourceSnapshot]:
    source = _validated_directory(source_root, "source_root")
    try:
        policy = resolve_source_selection(source, source_selection)
        live_identity = None if policy is None else policy.identity
        selection_inputs = capture_source_selection_inputs(
            source,
            source_selection=source_selection,
            selection_policy=policy,
        )
        persisted_identity = source_selection_identity_from_generation_inputs(
            manifest.generation_inputs
        )
        validate_persisted_source_selection_identity(
            manifest.generation_inputs,
            live_identity,
            operation=operation,
            allow_same_path_update=(
                allow_same_path_identity_update
                and persisted_identity != live_identity
            ),
            live_selection_inputs=selection_inputs,
        )
        snapshot = build_source_snapshot(
            source,
            include_tests=(),
            source_selection=source_selection,
            selection_policy=policy,
            expected_selection_inputs=selection_inputs,
        )
    except (OSError, SourceSelectionError, SourceSnapshotError, ValueError) as exc:
        raise DocumentationNativeError(
            f"Cannot validate {operation} source-selection inputs: {exc}"
        ) from exc
    return source, snapshot


def evaluate_documentation_native_freshness(
    *,
    knowledge: KnowledgeIndex,
    manifest: SyncManifest,
    source_root: str | Path,
    trust_source_plugins: bool = False,
    helper_cache_dir: str | Path | None = None,
    source_selection: str | Path | None = None,
) -> DocumentationNativeFreshness:
    """Evaluate one validated v5 snapshot against live standalone defaults."""

    if not isinstance(knowledge, KnowledgeIndex):
        raise TypeError("knowledge must be a KnowledgeIndex")
    if not isinstance(manifest, SyncManifest):
        raise TypeError("manifest must be a SyncManifest")
    source, source_snapshot = _native_source_snapshot_preflight(
        source_root=source_root,
        manifest=manifest,
        source_selection=source_selection,
        operation="native freshness",
    )
    generation_input_paths = _generation_input_paths(manifest)
    runtime = _collect_runtime(
        source_root=source,
        trust_source_plugins=trust_source_plugins,
        helper_cache_dir=helper_cache_dir,
        source_selection=source_selection,
        generation_input_paths=generation_input_paths,
        source_snapshot=source_snapshot,
    )
    try:
        generation_options = _runtime_generation_options(manifest)
        source_mismatches = _source_mismatches(
            knowledge=knowledge,
            manifest=manifest,
            runtime=runtime,
        )
        missing_source_paths = set(manifest.sources) - set(runtime.inventory)
        captured_paths = runtime.source_snapshot.captured_content_hashes
        for concept in knowledge.concepts:
            basis = concept.facets.structure.basis
            if (
                basis is None
                or basis.scope is not ObservationScope.INFRASTRUCTURE
                or basis.source_path is None
                or basis.source_path in captured_paths
            ):
                continue
            try:
                (runtime.source_snapshot.root / basis.source_path).lstat()
            except FileNotFoundError:
                missing_source_paths.add(basis.source_path)
            except OSError:
                # Unreadable or excluded paths are indeterminate, not proof of
                # source removal.
                continue
        live = build_runtime_live_evaluation(
            RuntimeLiveEvaluationInputs(
                knowledge=knowledge,
                manifest=manifest,
                inventory=runtime.inventory,
                infrastructure_inventory=runtime.infrastructure_inventory,
                source_snapshot=runtime.source_snapshot,
                generation_options=generation_options,
                generation_option_defaults=RUNTIME_GENERATION_OPTION_DEFAULTS,
                generation_option_allowlist=tuple(
                    RUNTIME_GENERATION_OPTION_DEFAULTS
                ),
                missing_source_paths=missing_source_paths,
                inventory_complete=True,
                extractor_registry=runtime.inventory_result.extractor_registry,
                plugin_extractor_components=(
                    runtime.inventory_result.plugin_components
                ),
                plugin_components=(
                    runtime.inventory_result.producer_plugin_components
                ),
            )
        )
        report = evaluate_knowledge_freshness(knowledge, live)
    except (KeyError, OSError, TypeError, UnicodeError, ValueError) as exc:
        raise DocumentationNativeError(
            f"Cannot evaluate native freshness: {exc}"
        ) from exc

    reasons: list[str] = list(source_mismatches)
    if (
        knowledge.bundle.snapshot.generation_options_hash
        != live.generation_options_hash
    ):
        reasons.append("generation-options-changed")
    if knowledge.bundle.producer != live.producer:
        reasons.append("producer-basis-changed")
    structural_locators = {
        concept.locator
        for concept in knowledge.concepts
        if concept.document.page_kind
        in {PageKind.MODULES, PageKind.ENTITIES, PageKind.INFRASTRUCTURE}
    }
    for locator in sorted(structural_locators):
        result = report.by_locator[locator]
        if result.state is not ComputedFreshness.CURRENT:
            reasons.append(f"{locator}:{result.reason_code}")
    return DocumentationNativeFreshness(
        current=not reasons,
        reasons=tuple(reasons),
        report=report,
        source_mismatches=source_mismatches,
    )


def refresh_documentation_native_projection(
    *,
    source_root: str | Path,
    wiki_root: str | Path,
    trust_source_plugins: bool = False,
    helper_cache_dir: str | Path | None = None,
    source_selection: str | Path | None = None,
    fault_injector: Callable[[CommitStage], None] | None = None,
) -> DocumentationNativeRefresh:
    """Recompute the native trio without mutating canonical Markdown."""

    source = _validated_directory(source_root, "source_root")
    wiki = _validated_directory(wiki_root, "wiki_root")
    manifest_version = _refresh_manifest_version(wiki)
    try:
        manifest = SyncManifest.load(wiki)
    except (FileNotFoundError, OSError, UnicodeError, ValueError) as exc:
        raise DocumentationNativeError(
            f"Cannot load the native refresh manifest: {exc}"
        ) from exc
    artifact_hashes_before = _validate_refresh_artifact_basis(
        wiki,
        manifest,
        manifest_version=manifest_version,
    )
    source, source_snapshot = _native_source_snapshot_preflight(
        source_root=source,
        manifest=manifest,
        source_selection=source_selection,
        operation="native refresh",
        allow_same_path_identity_update=True,
    )
    generation_input_paths = _generation_input_paths(manifest)
    runtime = _collect_runtime(
        source_root=source,
        trust_source_plugins=trust_source_plugins,
        helper_cache_dir=helper_cache_dir,
        source_selection=source_selection,
        generation_input_paths=generation_input_paths,
        source_snapshot=source_snapshot,
    )
    page_maps = _page_maps(runtime.inventory)
    generation_options = _runtime_generation_options(manifest)
    surface = _evaluate_runtime_surface(
        source_root=source,
        wiki_root=wiki,
        runtime=runtime,
        trust_source_plugins=trust_source_plugins,
        manifest=manifest,
        page_maps=page_maps,
        generation_options=generation_options,
    )
    markdown_before = _markdown_hashes(wiki)
    try:
        commit = finalize_runtime_knowledge(
            RuntimeKnowledgeInputs(
                target_wiki_dir=wiki,
                inventory=runtime.inventory,
                surface=surface,
                source_snapshot=runtime.source_snapshot,
                module_page_map=page_maps.module,
                entity_occurrence_page_map=page_maps.occurrence,
                repository_evidence=collect_runtime_repository_evidence(
                    source,
                    wiki,
                    source_snapshot=runtime.source_snapshot,
                ),
                inventory_complete=True,
                previous_manifest=manifest,
                manifest_surfaces=manifest.surfaces,
                manifest_generation_inputs=manifest.generation_inputs,
                regenerated_evidence_page_paths=_regenerated_evidence_pages(
                    page_maps
                ),
                extractor_registry=runtime.inventory_result.extractor_registry,
                plugin_extractor_components=(
                    runtime.inventory_result.plugin_components
                ),
                plugin_components=(
                    runtime.inventory_result.producer_plugin_components
                ),
                plugin_lock_path=runtime.inventory_result.plugin_lock_path,
                plugin_lock_hash=runtime.inventory_result.plugin_lock_hash,
                generation_options=generation_options,
                generation_option_defaults=RUNTIME_GENERATION_OPTION_DEFAULTS,
                generation_option_allowlist=tuple(
                    RUNTIME_GENERATION_OPTION_DEFAULTS
                ),
            ),
            fault_injector=fault_injector,
        )
    except (OSError, RuntimeError, TypeError, UnicodeError, ValueError) as exc:
        if isinstance(exc, DocumentationNativeError):
            raise
        raise DocumentationNativeError(
            f"Native projection refresh failed: {exc}"
        ) from exc
    markdown_after = _markdown_hashes(wiki)
    if markdown_after != markdown_before:
        raise DocumentationNativeError(
            "Native projection refresh changed canonical Markdown."
        )
    artifact_hashes_after = _native_artifact_hashes(wiki)
    expected_after = {
        commit.surface_index.relative_path: commit.surface_index.content_hash,
        commit.knowledge_index.relative_path: commit.knowledge_index.content_hash,
        commit.manifest.relative_path: commit.manifest.content_hash,
    }
    if artifact_hashes_after != expected_after:
        raise DocumentationNativeError(
            "Native projection refresh persisted an unexpected artifact set."
        )
    from .context_service import _build_context_knowledge_view

    knowledge_view = _build_context_knowledge_view(
        wiki,
        surface,
        dict(runtime.inventory),
        runtime.inventory_result,
    )
    if not knowledge_view.ready or not knowledge_view.freshness_evaluated:
        raise DocumentationNativeError(
            "Refreshed native projection did not produce a live evaluated "
            "knowledge view."
        )
    return DocumentationNativeRefresh(
        commit=commit,
        markdown_before=markdown_before,
        markdown_after=markdown_after,
        artifact_hashes_before=artifact_hashes_before,
        artifact_hashes_after=artifact_hashes_after,
        knowledge_view=knowledge_view,
    )


def _collect_runtime(
    *,
    source_root: str | Path,
    trust_source_plugins: bool,
    helper_cache_dir: str | Path | None,
    source_selection: str | Path | None,
    generation_input_paths: tuple[str, ...] = (),
    source_snapshot: SourceSnapshot | None = None,
) -> _DocumentationNativeRuntime:
    source = _validated_directory(source_root, "source_root")
    if not isinstance(trust_source_plugins, bool):
        raise TypeError("trust_source_plugins must be a bool")
    from .extraction_service import (
        InventoryRequest,
        get_docker_inventory,
        get_inventory_result,
    )

    try:
        if source_snapshot is None:
            source_snapshot = build_source_snapshot(
                source,
                include_tests=(),
                source_selection=source_selection,
            )
        elif source_snapshot.root.resolve() != source:
            raise DocumentationNativeError(
                "Native source snapshot belongs to a different source root."
            )
        source_snapshot, uncaptured_generation_inputs = (
            _capture_generation_inputs(
                source_snapshot,
                generation_input_paths,
            )
        )
        result = get_inventory_result(
            InventoryRequest(
                src_dir=source,
                deep=True,
                source_snapshot=source_snapshot,
                cache_options=InventoryCacheOptions(enabled=False),
                parallel_jobs=1,
                helper_cache_dir=(
                    None if helper_cache_dir is None else str(helper_cache_dir)
                ),
                include_tests=(),
                job_request=ExtractionJobRequest.resolved(1),
                include_plugins=trust_source_plugins,
                source_plugins_only=trust_source_plugins,
            )
        )
    except (OSError, TypeError, UnicodeError, ValueError) as exc:
        raise DocumentationNativeError(
            f"Cannot construct native source inventory: {exc}"
        ) from exc
    failed = result.failed
    if failed:
        details = "; ".join(
            f"{status.language}: {status.message or 'extraction failed'}"
            for status in failed
        )
        raise DocumentationNativeError(
            details or "Native source inventory extraction failed."
        )
    evaluated_snapshot = result.source_snapshot or source_snapshot
    docker_infrastructure = get_docker_inventory(
        str(source),
        source_snapshot=evaluated_snapshot,
    )
    infrastructure_inventory = dict(docker_infrastructure)
    for source_path, record in get_yaml_infrastructure_inventory(
        source,
        source_snapshot=evaluated_snapshot,
    ).items():
        infrastructure_inventory.setdefault(source_path, record)
    return _DocumentationNativeRuntime(
        inventory=result.inventory,
        infrastructure_inventory=infrastructure_inventory,
        inventory_result=result,
        source_snapshot=evaluated_snapshot,
        uncaptured_generation_inputs=uncaptured_generation_inputs,
    )


def _evaluate_runtime_surface(
    *,
    source_root: Path,
    wiki_root: Path,
    runtime: _DocumentationNativeRuntime,
    trust_source_plugins: bool,
    manifest: SyncManifest,
    page_maps: _DocumentationPageMaps,
    generation_options: Mapping[str, object],
) -> SurfaceIndexEvaluation:
    try:
        flow_entries = _runtime_flow_entries(
            source_root=source_root,
            runtime=runtime,
            trust_source_plugins=trust_source_plugins,
            manifest=manifest,
            generation_options=generation_options,
        )
        page_source_overrides = {
            page_path: mapping.source_path
            for page_path, mapping in manifest.page_source_mappings.items()
        }
        return evaluate_surface_index(
            wiki_root,
            runtime.inventory,
            src_dir=source_root,
            entity_page_cache=page_maps.entity,
            entity_occurrence_page_cache=page_maps.occurrence,
            module_page_map=page_maps.module,
            entry_points=flow_entries,
            page_source_overrides=page_source_overrides,
        )
    except (
        ApiContractError,
        KeyError,
        OSError,
        TypeError,
        UnicodeError,
        ValueError,
    ) as exc:
        raise DocumentationNativeError(
            f"Cannot evaluate the current wiki surface: {exc}"
        ) from exc


def _runtime_flow_entries(
    *,
    source_root: Path,
    runtime: _DocumentationNativeRuntime,
    trust_source_plugins: bool,
    manifest: SyncManifest,
    generation_options: Mapping[str, object],
) -> list[dict[str, Any]]:
    if generation_options.get("flows_enabled") is not True:
        return []

    detected = detect_entry_points(
        dict(runtime.inventory),
        console_scripts=read_console_scripts(
            str(source_root),
            source_snapshot=runtime.source_snapshot,
        ),
        root=source_root,
        fallback_root=(
            None
            if source_root.resolve() != Path.cwd().resolve()
            else Path.cwd()
        ),
        include_plugins=trust_source_plugins,
        include_provenance=True,
    )
    entries = list(detected.entries)
    categories = generation_options.get("flow_categories")
    if isinstance(categories, list):
        selected_categories = {str(value) for value in categories}
        entries = [
            entry
            for entry in entries
            if str(entry.get("category")) in selected_categories
        ]
    if generation_options.get("exclude_tests") is True:
        entries = [
            entry for entry in entries if not is_test_source_path(entry.get("file"))
        ]

    contracts: Mapping[str, Any] = {}
    if generation_options.get("api_contracts_enabled") is True:
        contracts = _runtime_api_contracts(
            source_root=source_root,
            inventory=runtime.inventory,
            manifest=manifest,
            source_snapshot=runtime.source_snapshot,
        )
    entries = attach_routes_to_entry_points(entries, contracts)

    from .extraction_service import resolve_call_edges

    edges = resolve_call_edges(dict(runtime.inventory)) if entries else []
    data_flow_enabled = generation_options.get("data_flow_enabled") is True
    data_flow_context = (
        build_data_flow_context(dict(runtime.inventory), edges)
        if data_flow_enabled and entries
        else None
    )
    results: list[dict[str, Any]] = []
    for entry in entries:
        flow = build_flow(entry, edges)
        data_flow = (
            analyze_data_flow(
                dict(runtime.inventory),
                flow,
                edges,
                context=data_flow_context,
            )
            if data_flow_enabled
            else None
        )
        record: dict[str, Any] = {
            "id": entry["id"],
            "category": entry["category"],
            "entry": entry["symbol"],
            "file": entry.get("file"),
            "label": entry.get("label"),
            "detector": entry.get("detector", "unknown"),
            "language": (
                runtime.inventory.get(str(entry.get("file") or ""), {}).get(
                    "language"
                )
                or "unknown"
            ),
            "evidence": {
                "flow": {
                    "step_count": len(flow.get("steps", [])),
                    "truncated": bool(flow.get("truncated")),
                    "modules_touched": list(flow.get("modules_touched", [])),
                },
                "data_flow": (
                    {
                        "generated": True,
                        "step_count": len(data_flow.get("steps", [])),
                        "transfer_count": len(data_flow.get("transfers", [])),
                        "truncated": bool(data_flow.get("truncated")),
                        "boundary_effects": list(data_flow.get("boundaries", [])),
                        "gaps": list(data_flow.get("gaps", [])),
                    }
                    if data_flow is not None
                    else None
                ),
            },
        }
        if entry.get("routes"):
            record["routes"] = list(entry["routes"])
        results.append(record)
    return results


def _runtime_api_contracts(
    *,
    source_root: Path,
    inventory: Mapping[str, Mapping[str, Any]],
    manifest: SyncManifest,
    source_snapshot: SourceSnapshot,
) -> Mapping[str, Any]:
    openapi = manifest.generation_inputs.get("openapi")
    openapi_file = openapi.get("path") if isinstance(openapi, Mapping) else None
    contracts = build_api_contracts(
        inventory,
        openapi_file=openapi_file,
        source_root=source_root,
        source_snapshot=source_snapshot,
    )
    if isinstance(openapi, Mapping):
        evaluated = contracts.get("openapi")
        expected = {
            key: openapi.get(key) for key in ("path", "sha256", "format")
        }
        actual = (
            {key: evaluated.get(key) for key in ("path", "sha256", "format")}
            if isinstance(evaluated, Mapping)
            else None
        )
        if actual != expected:
            raise DocumentationNativeError(
                "Current OpenAPI input does not match the manifest commitment."
            )
    return contracts


def _page_maps(
    inventory: Mapping[str, Mapping[str, Any]],
) -> _DocumentationPageMaps:
    from .bootstrap_runtime import (
        build_entity_occurrence_page_map,
        build_entity_page_map,
        build_module_page_map,
    )

    inventory_dict = dict(inventory)
    return _DocumentationPageMaps(
        module=build_module_page_map(inventory_dict),
        entity=build_entity_page_map(inventory_dict),
        occurrence=build_entity_occurrence_page_map(inventory_dict),
    )


def _regenerated_evidence_pages(
    page_maps: _DocumentationPageMaps,
) -> frozenset[str]:
    """Return exactly the structural pages backed by current inventory."""

    return frozenset(
        {
            *(f"modules/{page_id}.md" for page_id in page_maps.module.values()),
            *(
                f"entities/{page_id}.md"
                for page_id in page_maps.occurrence.values()
            ),
        }
    )


def _runtime_generation_options(manifest: SyncManifest) -> dict[str, object]:
    return runtime_generation_options(
        surfaces=manifest.surfaces,
        generation_inputs=manifest.generation_inputs,
        include_tests=(),
        preserve_semantic=True,
    )


def _generation_input_paths(manifest: SyncManifest) -> tuple[str, ...]:
    openapi = manifest.generation_inputs.get("openapi")
    if openapi is None:
        return ()
    if not isinstance(openapi, Mapping):
        raise DocumentationNativeError(
            "manifest generation_inputs.openapi must be an object."
        )
    path = openapi.get("path")
    content_hash = openapi.get("sha256")
    format_name = openapi.get("format")
    if (
        not isinstance(path, str)
        or not path
        or path != path.strip()
        or "\\" in path
        or PurePosixPath(path).is_absolute()
        or any(part in {"", ".", ".."} for part in PurePosixPath(path).parts)
    ):
        raise DocumentationNativeError(
            "manifest generation_inputs.openapi.path must be a safe "
            "repository-relative POSIX path."
        )
    if not is_valid_sha256(content_hash):
        raise DocumentationNativeError(
            "manifest generation_inputs.openapi.sha256 must be a canonical SHA-256."
        )
    if format_name not in {"json", "yaml"}:
        raise DocumentationNativeError(
            "manifest generation_inputs.openapi.format must be 'json' or 'yaml'."
        )
    return (path,)


def _capture_generation_inputs(
    snapshot: SourceSnapshot,
    paths: tuple[str, ...],
) -> tuple[SourceSnapshot, tuple[str, ...]]:
    uncaptured: list[str] = []
    current = snapshot
    for path in paths:
        if path in current.captured_content_hashes:
            continue
        try:
            current = current.with_captured_inventory_paths((path,))
        except SourceSnapshotError:
            uncaptured.append(path)
    return current, tuple(uncaptured)


def _source_mismatches(
    *,
    knowledge: KnowledgeIndex,
    manifest: SyncManifest,
    runtime: _DocumentationNativeRuntime,
) -> tuple[str, ...]:
    recorded_paths = set(manifest.sources)
    current_paths = set(runtime.inventory)
    mismatches = [
        f"added:{path}" for path in sorted(current_paths - recorded_paths)
    ]
    mismatches.extend(
        f"removed:{path}" for path in sorted(recorded_paths - current_paths)
    )
    if source_selection_identity_from_generation_inputs(
        manifest.generation_inputs
    ) != runtime.source_snapshot.source_selection_identity:
        mismatches.append("generation_input_changed:source_selection")
    if source_selection_inputs_from_generation_inputs(
        manifest.generation_inputs
    ) != runtime.source_snapshot.source_selection_inputs:
        mismatches.append("generation_input_changed:source_selection_inputs")
    current_hashes = runtime.source_snapshot.hashes_for(current_paths)
    for path in sorted(recorded_paths & current_paths):
        recorded_hash = manifest.sources[path].get("hash")
        if current_hashes[path] != recorded_hash:
            mismatches.append(f"changed:{path}")

    openapi = manifest.generation_inputs.get("openapi")
    if isinstance(openapi, Mapping):
        path = str(openapi["path"])
        if (
            path in runtime.uncaptured_generation_inputs
            or path not in runtime.source_snapshot.captured_content_hashes
        ):
            mismatches.append(f"generation_input_removed:openapi:{path}")
        elif (
            runtime.source_snapshot.captured_content_hashes[path]
            != openapi.get("sha256")
        ):
            mismatches.append(f"generation_input_changed:openapi:{path}")

    live_snapshot_hash = _live_source_snapshot_hash(runtime, manifest)
    if live_snapshot_hash is None:
        mismatches.append("source-snapshot-unavailable")
    elif live_snapshot_hash != knowledge.bundle.snapshot.source_snapshot_hash:
        mismatches.append("source-snapshot-changed")
    return tuple(dict.fromkeys(mismatches))


def _live_source_snapshot_hash(
    runtime: _DocumentationNativeRuntime,
    manifest: SyncManifest,
) -> str | None:
    if runtime.uncaptured_generation_inputs:
        return None
    consumed = {
        item.path: item for item in runtime.source_snapshot.to_consumed_inputs()
    }
    lock_path = runtime.inventory_result.plugin_lock_path
    lock_hash = runtime.inventory_result.plugin_lock_hash
    if (lock_path is None) != (lock_hash is None):
        return None
    if lock_path is not None:
        assert lock_hash is not None
        consumed[lock_path] = ConsumedInput(
            path=lock_path,
            content_hash=lock_hash,
            kind=ConsumedInputKind.PLUGIN,
        )

    openapi = manifest.generation_inputs.get("openapi")
    if isinstance(openapi, Mapping):
        path = str(openapi["path"])
        content_hash = runtime.source_snapshot.captured_content_hashes.get(path)
        if content_hash is None:
            return None
        consumed[path] = ConsumedInput(
            path=path,
            content_hash=content_hash,
            kind=ConsumedInputKind.OPENAPI,
        )
    return hash_source_snapshot(consumed.values())


def _validate_refresh_artifact_basis(
    wiki_root: Path,
    manifest: SyncManifest,
    *,
    manifest_version: int,
) -> dict[str, str]:
    before = _native_artifact_hashes(wiki_root, allow_missing=True)
    if SURFACE_INDEX_FILENAME not in before:
        raise DocumentationNativeError(
            "Native projection refresh requires an existing surface index."
        )
    marker = manifest.artifact_hashes
    if marker is None:
        if KNOWLEDGE_INDEX_FILENAME in before:
            raise DocumentationNativeError(
                "A markerless manifest cannot refresh an orphan knowledge index."
            )
        surface_bytes = (wiki_root / SURFACE_INDEX_FILENAME).read_bytes()
        try:
            if manifest_version == MANIFEST_VERSION:
                validate_surface_index_bytes(surface_bytes)
            else:
                _validate_legacy_surface_bytes(surface_bytes)
        except (KnowledgeArtifactError, TypeError, UnicodeError, ValueError) as exc:
            raise DocumentationNativeError(
                f"The unmarked surface index is invalid before refresh: {exc}"
            ) from exc
        return before
    if KNOWLEDGE_INDEX_FILENAME not in before:
        raise DocumentationNativeError(
            "The committed native artifact set is incomplete before refresh."
        )
    try:
        validated = validate_knowledge_artifacts(
            surface_index_bytes=(wiki_root / SURFACE_INDEX_FILENAME).read_bytes(),
            knowledge_index_bytes=(wiki_root / KNOWLEDGE_INDEX_FILENAME).read_bytes(),
            manifest=manifest,
        )
    except (KnowledgeArtifactError, OSError, TypeError, ValueError) as exc:
        raise DocumentationNativeError(
            f"The committed native artifact set is invalid before refresh: {exc}"
        ) from exc
    if (
        marker.surface_index_hash != validated.surface_index_hash
        or marker.knowledge_index_hash != validated.knowledge_index_hash
        or marker.evaluated_envelope_hash != validated.evaluated_envelope_hash
        or marker.governance_hash != validated.governance_hash
    ):
        raise DocumentationNativeError(
            "The manifest marker does not match the native artifact set before refresh."
        )
    return before


def _refresh_manifest_version(wiki_root: Path) -> int:
    path = wiki_root / MANIFEST_FILENAME
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, ValueError) as exc:
        raise DocumentationNativeError(
            f"Cannot decode the native refresh manifest: {exc}"
        ) from exc
    if not isinstance(payload, Mapping):
        raise DocumentationNativeError(
            "Native projection refresh manifest must contain an object."
        )
    version = payload.get("version")
    if version not in {LEGACY_MANIFEST_VERSION, MANIFEST_VERSION}:
        raise DocumentationNativeError(
            "Native projection refresh requires manifest version "
            f"{LEGACY_MANIFEST_VERSION} or {MANIFEST_VERSION}."
        )
    assert isinstance(version, int)
    return version


def _validate_legacy_surface_bytes(content: bytes) -> None:
    def unique_object(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f"duplicate object key {key!r}")
            result[key] = value
        return result

    payload = json.loads(
        content.decode("utf-8"),
        object_pairs_hook=unique_object,
        parse_constant=lambda value: (_ for _ in ()).throw(
            ValueError(f"non-finite number {value!r}")
        ),
    )
    if not isinstance(payload, Mapping):
        raise ValueError("legacy surface index must contain an object")
    schema_version = payload.get("schema_version")
    if schema_version not in {
        "llm-wiki-surface/v1",
        WIKI_SURFACE_INDEX_SCHEMA_VERSION,
    }:
        raise ValueError(
            "legacy surface index has an unsupported schema version"
        )
    pages = payload.get("pages")
    if not isinstance(pages, list):
        raise ValueError("legacy surface index pages must be an array")
    seen_paths: set[str] = set()
    for index, page in enumerate(pages):
        if not isinstance(page, Mapping):
            raise ValueError(
                f"legacy surface index pages[{index}] is malformed"
            )
        canonical_path = page.get("canonical_path")
        source_path = page.get("source_path")
        if not _is_safe_relative_posix_path(
            canonical_path,
            required_suffix=".md",
        ):
            raise ValueError(
                "legacy surface index "
                f"pages[{index}].canonical_path is invalid"
            )
        if canonical_path in seen_paths:
            raise ValueError(
                "legacy surface index pages contain duplicate canonical paths"
            )
        seen_paths.add(canonical_path)
        if source_path is not None and not _is_safe_relative_posix_path(
            source_path
        ):
            raise ValueError(
                f"legacy surface index pages[{index}].source_path is invalid"
            )
    source_hash = payload.get("source_hash")
    if source_hash is not None and not is_valid_sha256(source_hash):
        raise ValueError(
            "legacy surface index source_hash must be a canonical SHA-256"
        )
    flows = payload.get("flows", [])
    if not isinstance(flows, list):
        raise ValueError("legacy surface index flows must be an array")


def _is_safe_relative_posix_path(
    value: object,
    *,
    required_suffix: str | None = None,
) -> TypeGuard[str]:
    return isinstance(value, str) and is_portable_relative_path(value) and (
        required_suffix is None
        or value.endswith(required_suffix)
    )


def _native_artifact_hashes(
    wiki_root: Path,
    *,
    allow_missing: bool = False,
) -> dict[str, str]:
    hashes: dict[str, str] = {}
    for name in (
        SURFACE_INDEX_FILENAME,
        KNOWLEDGE_INDEX_FILENAME,
        MANIFEST_FILENAME,
    ):
        path = wiki_root / name
        try:
            metadata = path.lstat()
        except FileNotFoundError:
            if allow_missing:
                continue
            raise DocumentationNativeError(
                f"Native projection refresh did not persist {name}."
            )
        except OSError as exc:
            raise DocumentationNativeError(
                f"Cannot inspect native artifact {name}: {exc}"
            ) from exc
        if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISREG(metadata.st_mode):
            raise DocumentationNativeError(
                f"Native artifact must be a regular file: {name}"
            )
        try:
            content = path.read_bytes()
        except OSError as exc:
            raise DocumentationNativeError(
                f"Cannot read native artifact {name}: {exc}"
            ) from exc
        hashes[name] = "sha256:" + hashlib.sha256(content).hexdigest()
    return hashes


def _validated_directory(value: str | Path, field_name: str) -> Path:
    candidate = Path(value).expanduser()
    try:
        metadata = candidate.lstat()
    except OSError as exc:
        raise DocumentationNativeError(
            f"{field_name} must be an existing regular directory: {candidate}"
        ) from exc
    if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISDIR(metadata.st_mode):
        raise DocumentationNativeError(
            f"{field_name} must be an existing regular directory: {candidate}"
        )
    return candidate.resolve()


def _markdown_hashes(wiki_root: Path) -> dict[str, str]:
    hashes: dict[str, str] = {}
    for path in sorted(wiki_root.rglob("*.md")):
        if path.is_symlink() or not path.is_file():
            raise DocumentationNativeError(
                f"Canonical Markdown is not a regular file: {path}"
            )
        relative = path.relative_to(wiki_root).as_posix()
        hashes[relative] = "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()
    return hashes


__all__ = [
    "DocumentationNativeError",
    "DocumentationNativeFreshness",
    "DocumentationNativeRefresh",
    "evaluate_documentation_native_freshness",
    "refresh_documentation_native_projection",
]
