"""Shared construction for supported documentation query services."""

from __future__ import annotations

from collections.abc import Callable, Iterable, Mapping
import os
from pathlib import Path
from typing import Any

from .dependencies import analyze_dependencies
from .documentation_queries import (
    DocumentationGraphQueryService,
    DocumentationQueryError,
)
from .entrypoints import build_flow
from .knowledge_consumption import KnowledgeReadView, load_knowledge_read_view
from .knowledge_verification import (
    attach_machine_verification_read_view,
    verification_summaries_for_concepts,
)
from .source_selection import (
    SourceSelectionError,
    resolve_source_selection,
    validate_persisted_source_selection_identity,
)
from .sync_manifest import SyncManifest, SyncManifestError
from .wiki_surface_index import evaluate_surface_index
from .source_snapshot import build_source_snapshot, capture_source_selection_inputs

_UNSET_LIVE_SELECTION_INPUTS = object()


def _wiki_has_persisted_read_state(wiki_root: Path) -> bool:
    """Return whether a wiki contains anything beyond empty scaffolding."""

    try:
        if not wiki_root.is_dir():
            return False
        for root, directories, files in os.walk(wiki_root, followlinks=False):
            directories[:] = [
                name
                for name in directories
                if not (Path(root) / name).is_symlink()
            ]
            if any(
                name not in {".gitkeep", ".llm-wiki-agent"}
                for name in files
            ):
                return True
    except OSError:
        return True
    return False


def validate_live_query_source_selection(
    *,
    source_root: Path,
    wiki_root: Path,
    live_identity: Mapping[str, object] | None,
    live_selection_inputs: Mapping[str, object] | None | object = (
        _UNSET_LIVE_SELECTION_INPUTS
    ),
    operation: str,
    allow_empty_wiki: bool = False,
) -> None:
    """Require a live query profile to match the persisted wiki boundary."""

    try:
        manifest = SyncManifest.load(wiki_root)
    except FileNotFoundError as exc:
        if live_identity is None or (
            allow_empty_wiki and not _wiki_has_persisted_read_state(wiki_root)
        ):
            return
        raise DocumentationQueryError(
            f"{operation} cannot validate the active source-selection profile "
            "because the wiki has no usable sync manifest; run `llm-wiki sync` "
            "with the same --src-dir, --wiki-dir, and --source-selection first"
        ) from exc
    except SyncManifestError as exc:
        raise DocumentationQueryError(
            f"{operation} cannot validate the active source-selection profile "
            "because the wiki sync manifest is invalid; restore it or run "
            "`llm-wiki sync` with the same active profile before querying"
        ) from exc
    except (OSError, TypeError, UnicodeError, ValueError) as exc:
        raise DocumentationQueryError(
            f"{operation} cannot validate the active source-selection profile "
            "because the wiki sync manifest is invalid; restore it or run "
            "`llm-wiki sync` with the same active profile before querying"
        ) from exc

    try:
        if live_selection_inputs is _UNSET_LIVE_SELECTION_INPUTS:
            validate_persisted_source_selection_identity(
                manifest.generation_inputs,
                live_identity,
                operation=operation,
            )
        else:
            validate_persisted_source_selection_identity(
                manifest.generation_inputs,
                live_identity,
                operation=operation,
                live_selection_inputs=live_selection_inputs,
            )
    except SourceSelectionError as exc:
        raise DocumentationQueryError(str(exc)) from exc


def _live_source_selection_identity(
    source_root: Path,
    source_selection: str | Path | None,
    inventory_result: object,
) -> Mapping[str, object] | None:
    source_snapshot = getattr(inventory_result, "source_snapshot", None)
    snapshot_identity = getattr(
        source_snapshot,
        "source_selection_identity",
        None,
    )
    if snapshot_identity is not None:
        return snapshot_identity
    policy = resolve_source_selection(source_root, source_selection)
    return policy.identity if policy is not None else None


def assemble_documentation_query_service(
    *,
    inventory: Mapping[str, Mapping[str, Any]],
    call_edges: Iterable[Mapping[str, Any]],
    flows: Iterable[Mapping[str, Any]],
    data_flows: object,
    dependency_analysis: Mapping[str, Any] | None,
    surface_index: Mapping[str, Any] | None,
    limit: int,
    knowledge_view: object,
    machine_verification: Mapping[str, Mapping[str, Any]],
    service_factory: Any = DocumentationGraphQueryService,
) -> DocumentationGraphQueryService:
    """Assemble the shared service with a caller-supplied service factory."""

    return service_factory(
        inventory,
        call_edges=call_edges,
        flows=flows,
        data_flows=data_flows,
        dependency_analysis=dependency_analysis,
        surface_index=surface_index,
        limit=limit,
        knowledge_view=knowledge_view,
        machine_verification=machine_verification,
    )


def build_documentation_query_service_from_view(
    *,
    wiki_root: Path,
    knowledge_view: KnowledgeReadView,
    limit: int,
    inventory: Mapping[str, Mapping[str, Any]] | None = None,
    call_edges: Iterable[Mapping[str, Any]] = (),
    flows: Iterable[Mapping[str, Any]] = (),
    data_flows: object = (),
    dependency_analysis: Mapping[str, Any] | None = None,
    surface_index: Mapping[str, Any] | None = None,
) -> DocumentationGraphQueryService:
    """Assemble one service around an already evaluated native read view."""

    evaluated_view = attach_machine_verification_read_view(
        wiki_root,
        knowledge_view,
    )
    return assemble_documentation_query_service(
        inventory=inventory or {},
        call_edges=call_edges,
        flows=flows,
        data_flows=data_flows,
        dependency_analysis=dependency_analysis,
        surface_index=surface_index,
        limit=limit,
        knowledge_view=evaluated_view,
        machine_verification=verification_summaries_for_concepts(
            evaluated_view
        ),
    )


def build_snapshot_documentation_query_service(
    *,
    wiki_root: Path,
    limit: int,
) -> DocumentationGraphQueryService:
    """Build a snapshot-only service without source extraction."""

    view = load_knowledge_read_view(
        wiki_root,
        snapshot_only=True,
        include_machine_verification=True,
    )
    return build_documentation_query_service_from_view(
        wiki_root=wiki_root,
        knowledge_view=view,
        limit=limit,
    )


def build_live_documentation_query_service(
    *,
    source_root: Path,
    wiki_root: Path,
    limit: int,
    read_only: bool,
    helper_cache_dir: Path | None = None,
    include_plugins: bool = True,
    source_plugins_only: bool = False,
    require_live_freshness: bool = False,
    source_selection: str | Path | None = None,
    extract_payload_builder: Callable[..., Any] | None = None,
    source_snapshot_builder: Callable[..., Any] | None = None,
    call_edge_resolver: Callable[[Any], Any] | None = None,
    flow_builder: Callable[[Any, Any], Any] = build_flow,
    surface_evaluator: Callable[..., Any] = evaluate_surface_index,
    knowledge_view_builder: Callable[..., Any] | None = None,
    query_surface_builder: Callable[..., Any] | None = None,
    dependency_analyzer: Callable[..., Any] = analyze_dependencies,
    verification_view_attacher: Callable[..., Any] = (
        attach_machine_verification_read_view
    ),
    verification_summarizer: Callable[..., Any] = (
        verification_summaries_for_concepts
    ),
    service_factory: Any = DocumentationGraphQueryService,
) -> DocumentationGraphQueryService:
    """Build a live service using one operation-scoped extraction."""

    # Keep heavyweight extraction/context modules out of this builder's import
    # path until a live query service is requested.
    from . import context_service, extraction_service

    selected_extract_builder = (
        extract_payload_builder or extraction_service.build_extract_payload
    )
    selected_snapshot_builder = source_snapshot_builder or build_source_snapshot
    selected_call_edge_resolver = (
        call_edge_resolver or extraction_service.resolve_call_edges
    )
    selected_view_builder = (
        knowledge_view_builder or context_service._build_context_knowledge_view
    )
    selected_query_surface_builder = (
        query_surface_builder or context_service._context_query_surface
    )
    try:
        selection_policy = resolve_source_selection(source_root, source_selection)
    except SourceSelectionError as exc:
        raise DocumentationQueryError(str(exc)) from exc
    selection_inputs = capture_source_selection_inputs(
        source_root,
        source_selection=source_selection,
        selection_policy=selection_policy,
    )
    validate_live_query_source_selection(
        source_root=source_root,
        wiki_root=wiki_root,
        live_identity=(
            selection_policy.identity if selection_policy is not None else None
        ),
        live_selection_inputs=selection_inputs,
        operation="live documentation query",
    )
    source_snapshot = selected_snapshot_builder(
        source_root,
        source_selection=source_selection,
        selection_policy=selection_policy,
        expected_selection_inputs=selection_inputs,
    )
    extract_options: dict[str, Any] = {
        "deep": True,
        "allow_external_src": True,
        "read_only": read_only,
    }
    if source_selection is not None:
        extract_options["source_selection"] = source_selection
    if helper_cache_dir is not None:
        extract_options["helper_cache_dir"] = str(helper_cache_dir)
    if not include_plugins:
        extract_options["include_plugins"] = False
    if source_plugins_only:
        extract_options["source_plugins_only"] = True
    extract_options["source_snapshot"] = source_snapshot
    result = selected_extract_builder(str(source_root), **extract_options)
    inventory = result.payload["inventory"]
    entrypoints = result.payload.get("entrypoints", [])
    call_edges = selected_call_edge_resolver(inventory)
    flows = [flow_builder(entrypoint, call_edges) for entrypoint in entrypoints]
    inventory_result = getattr(result, "inventory_result", None)
    try:
        live_identity = _live_source_selection_identity(
            source_root,
            source_selection,
            inventory_result,
        )
    except SourceSelectionError as exc:
        raise DocumentationQueryError(str(exc)) from exc
    validate_live_query_source_selection(
        source_root=source_root,
        wiki_root=wiki_root,
        live_identity=live_identity,
        live_selection_inputs=getattr(
            getattr(inventory_result, "source_snapshot", None),
            "source_selection_inputs",
            None,
        ),
        operation="live documentation query",
    )
    surface_evaluation = surface_evaluator(
        wiki_root,
        inventory,
        src_dir=source_root,
        entry_points=entrypoints,
    )
    knowledge_view = selected_view_builder(
        wiki_root,
        surface_evaluation,
        inventory,
        inventory_result,
    )
    if require_live_freshness and (
        not isinstance(knowledge_view, KnowledgeReadView)
        or not knowledge_view.ready
        or not knowledge_view.freshness_evaluated
    ):
        raise DocumentationQueryError(
            "verified-current claim reconciliation requires a live native "
            "freshness evaluation"
        )
    if isinstance(knowledge_view, KnowledgeReadView):
        knowledge_view = verification_view_attacher(
            wiki_root,
            knowledge_view,
        )
        machine_verification = verification_summarizer(knowledge_view)
    else:
        # Preserve the API's test-double adapter contract.
        machine_verification = {}
    query_surface = selected_query_surface_builder(
        surface_evaluation.payload,
        knowledge_view,
    )
    source_snapshot = (
        inventory_result.source_snapshot if inventory_result is not None else None
    )
    dependency_analysis = getattr(result, "dependency_analysis", None)
    if dependency_analysis is None:
        dependency_analysis = dependency_analyzer(
            inventory,
            str(source_root),
            source_snapshot=source_snapshot,
        )
    return assemble_documentation_query_service(
        inventory=inventory,
        call_edges=call_edges,
        flows=flows,
        data_flows=result.payload.get("data_flows") or [],
        dependency_analysis=dependency_analysis,
        surface_index=query_surface,
        limit=limit,
        knowledge_view=knowledge_view,
        machine_verification=machine_verification,
        service_factory=service_factory,
    )


__all__ = [
    "assemble_documentation_query_service",
    "build_documentation_query_service_from_view",
    "build_live_documentation_query_service",
    "build_snapshot_documentation_query_service",
    "validate_live_query_source_selection",
]
