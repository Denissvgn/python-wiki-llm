"""CLI compatibility adapter for the context service."""

from __future__ import annotations

import sys as _sys
from typing import TYPE_CHECKING

from ..services import context_service as _service

if TYPE_CHECKING:
    # Mirror legacy exports for static consumers; runtime imports remain aliases.
    from ..services.context_service import (
        CONTEXT_KNOWLEDGE_CONCEPT_LIMIT as CONTEXT_KNOWLEDGE_CONCEPT_LIMIT,
        CONTEXT_KNOWLEDGE_PAGE_LIMIT as CONTEXT_KNOWLEDGE_PAGE_LIMIT,
        CONTEXT_KNOWLEDGE_RELATIONSHIP_LIMIT as CONTEXT_KNOWLEDGE_RELATIONSHIP_LIMIT,
        CONTEXT_KNOWLEDGE_SERIALIZED_BYTE_LIMIT as CONTEXT_KNOWLEDGE_SERIALIZED_BYTE_LIMIT,
        DocumentationGraphQueryService as DocumentationGraphQueryService,
        KNOWLEDGE_PROTOCOL_VERSION as KNOWLEDGE_PROTOCOL_VERSION,
        KnowledgeRequiredUnavailableError as KnowledgeRequiredUnavailableError,
        PROTOCOL_VERSION as PROTOCOL_VERSION,
        ProtocolRequestError as ProtocolRequestError,
        _append_knowledge_context_warning as _append_knowledge_context_warning,
        _append_typed_graph_context_warning as _append_typed_graph_context_warning,
        _apply_protocol_filters as _apply_protocol_filters,
        _build_context as _build_context,
        _build_context_payload as _build_context_payload,
        _build_context_payload_with_freshness_preference as _build_context_payload_with_freshness_preference,
        _build_entry as _build_entry,
        _build_import_graph as _build_import_graph,
        _build_protocol_enrichment as _build_protocol_enrichment,
        _classify_files as _classify_files,
        _context_freshness_rank_by_source as _context_freshness_rank_by_source,
        _context_query_surface as _context_query_surface,
        _deep_entry as _deep_entry,
        _entry_tokens as _entry_tokens,
        _estimate_tokens as _estimate_tokens,
        _filepath_to_module as _filepath_to_module,
        _freshness_ranking_policy as _freshness_ranking_policy,
        _knowledge_enriched_page_ref as _knowledge_enriched_page_ref,
        _protocol_success_payload as _protocol_success_payload,
        _reliably_missing_context_sources as _reliably_missing_context_sources,
        _render_markdown as _render_markdown,
        _select_knowledge_page_refs as _select_knowledge_page_refs,
        _slim_entry as _slim_entry,
        _summary_entry as _summary_entry,
        _surface_filter_payload as _surface_filter_payload,
        _symbol_pages_payload as _symbol_pages_payload,
        _validate_protocol_request as _validate_protocol_request,
        build_runtime_live_evaluation as build_runtime_live_evaluation,
        evaluate_surface_index as evaluate_surface_index,
        get_entry_points as get_entry_points,
        get_inventory as get_inventory,
        get_inventory_result as get_inventory_result,
        load_knowledge_state as load_knowledge_state,
        print_extraction_job_plan as print_extraction_job_plan,
        run as run,
        runtime_generation_options as runtime_generation_options,
    )

_sys.modules[__name__] = _service
