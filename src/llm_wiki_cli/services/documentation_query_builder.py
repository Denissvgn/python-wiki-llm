"""Shared construction for supported documentation query services."""

from __future__ import annotations

from collections.abc import Callable, Iterable, Mapping
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
from .wiki_surface_index import evaluate_surface_index


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
    """Assemble the shared service while permitting public API test adapters."""

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
    require_live_freshness: bool = False,
    extract_payload_builder: Callable[..., Any] | None = None,
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
    selected_call_edge_resolver = (
        call_edge_resolver or extraction_service.resolve_call_edges
    )
    selected_view_builder = (
        knowledge_view_builder or context_service._build_context_knowledge_view
    )
    selected_query_surface_builder = (
        query_surface_builder or context_service._context_query_surface
    )
    extract_options: dict[str, Any] = {
        "deep": True,
        "allow_external_src": True,
        "read_only": read_only,
    }
    if helper_cache_dir is not None:
        extract_options["helper_cache_dir"] = str(helper_cache_dir)
    if not include_plugins:
        extract_options["include_plugins"] = False
    result = selected_extract_builder(str(source_root), **extract_options)
    inventory = result.payload["inventory"]
    entrypoints = result.payload.get("entrypoints", [])
    call_edges = selected_call_edge_resolver(inventory)
    flows = [flow_builder(entrypoint, call_edges) for entrypoint in entrypoints]
    inventory_result = getattr(result, "inventory_result", None)
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
]
