"""CLI compatibility adapter for the bootstrap runtime service."""

from __future__ import annotations

import sys as _sys
from typing import TYPE_CHECKING

from ..services import bootstrap_runtime as _service

if TYPE_CHECKING:
    # Mirror legacy exports for static consumers; runtime imports remain aliases.
    from ..services.bootstrap_runtime import (
        ArtifactWriteState as ArtifactWriteState,
        EntityOccurrenceKey as EntityOccurrenceKey,
        _BootstrapPageMaps as _BootstrapPageMaps,
        _FLOW_MODULE_HEADER_CHAR_LIMIT as _FLOW_MODULE_HEADER_CHAR_LIMIT,
        _FLOW_SEQUENCE_INTERACTION_LIMIT as _FLOW_SEQUENCE_INTERACTION_LIMIT,
        __version__ as __version__,
        _build_relationships as _build_relationships,
        _execute_documentation_workspace_refresh as _execute_documentation_workspace_refresh,
        _format_signature as _format_signature,
        _generate_data_flow_section as _generate_data_flow_section,
        _generate_dependencies_md as _generate_dependencies_md,
        _generate_docker_md as _generate_docker_md,
        _generate_dockerfile_md as _generate_dockerfile_md,
        _generate_entity_md as _generate_entity_md,
        _generate_entity_relationship_section as _generate_entity_relationship_section,
        _generate_flow_md as _generate_flow_md,
        _generate_index_md as _generate_index_md,
        _generate_infrastructure_md as _generate_infrastructure_md,
        _generate_load_order_md as _generate_load_order_md,
        _generate_module_dependency_section as _generate_module_dependency_section,
        _generate_module_md as _generate_module_md,
        _generate_workflow_md as _generate_workflow_md,
        _governance_moves_for_bootstrap as _governance_moves_for_bootstrap,
        _module_dependency_graph as _module_dependency_graph,
        _preflight_bootstrap_governance as _preflight_bootstrap_governance,
        _prepare_bootstrap_page_maps as _prepare_bootstrap_page_maps,
        _preserve_level_two_section as _preserve_level_two_section,
        _record_bootstrap_artifact as _record_bootstrap_artifact,
        _render_dependency_graph_result as _render_dependency_graph_result,
        _source_snapshot_log_lines as _source_snapshot_log_lines,
        _table_inline_code as _table_inline_code,
        _update_agent_constraints as _update_agent_constraints,
        analyze_data_flow_detailed as analyze_data_flow_detailed,
        analyze_dependencies as analyze_dependencies,
        build_data_flow_context as build_data_flow_context,
        build_entity_occurrence_page_map as build_entity_occurrence_page_map,
        build_entity_page_map as build_entity_page_map,
        build_module_page_map as build_module_page_map,
        build_source_snapshot as build_source_snapshot,
        execute_bootstrap as execute_bootstrap,
        finalize_runtime_knowledge as finalize_runtime_knowledge,
        get_inventory_result as get_inventory_result,
        run as run,
        runtime_source_snapshot_hash as runtime_source_snapshot_hash,
    )

_sys.modules[__name__] = _service
