"""CLI compatibility adapter for the extraction service."""

from __future__ import annotations

import sys as _sys
from typing import TYPE_CHECKING

from ..services import extraction_service as _service

if TYPE_CHECKING:
    # Mirror legacy exports for static consumers; runtime imports remain aliases.
    from ..services.extraction_service import (
        EXTRACTOR_REGISTRY as EXTRACTOR_REGISTRY,
        EXTRACT_SCHEMA_VERSION as EXTRACT_SCHEMA_VERSION,
        ExtractPayloadResult as ExtractPayloadResult,
        ExtractorFailureError as ExtractorFailureError,
        ExtractorStatus as ExtractorStatus,
        GoExtractionRequest as GoExtractionRequest,
        HaskellExtractionRequest as HaskellExtractionRequest,
        InventoryCache as InventoryCache,
        InventoryRequest as InventoryRequest,
        InventoryResult as InventoryResult,
        LANGUAGE_EXTENSIONS as LANGUAGE_EXTENSIONS,
        RustExtractionRequest as RustExtractionRequest,
        ThreadPoolExecutor as ThreadPoolExecutor,
        _build_inventory_result as _build_inventory_result,
        _dependency_extract_block as _dependency_extract_block,
        _load_extractor as _load_extractor,
        _looks_like_compose as _looks_like_compose,
        _parse_compose as _parse_compose,
        _parse_dockerfile as _parse_dockerfile,
        _parse_inline_yaml_list as _parse_inline_yaml_list,
        _public_detailed_data_flow as _public_detailed_data_flow,
        _summarize_inventory as _summarize_inventory,
        analyze_data_flow_detailed as analyze_data_flow_detailed,
        build_data_flow_context as build_data_flow_context,
        build_extract_payload as build_extract_payload,
        build_source_snapshot as build_source_snapshot,
        ensure_complete_inventory as ensure_complete_inventory,
        filter_source_diff as filter_source_diff,
        get_call_graph as get_call_graph,
        get_docker_inventory as get_docker_inventory,
        get_inventory as get_inventory,
        get_inventory_result as get_inventory_result,
        infer_language_from_path as infer_language_from_path,
        languages_with_source as languages_with_source,
        print_inventory_failures as print_inventory_failures,
        resolve_call_edges as resolve_call_edges,
        resolve_call_observations as resolve_call_observations,
        run as run,
        unsupported_source_summary as unsupported_source_summary,
    )

_sys.modules[__name__] = _service
