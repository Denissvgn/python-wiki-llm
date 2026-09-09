"""CLI compatibility adapter for the lint service."""

from __future__ import annotations

import sys as _sys
from typing import TYPE_CHECKING

from ..services import lint_service as _service

if TYPE_CHECKING:
    # Mirror legacy exports for static consumers; runtime imports remain aliases.
    from ..services.lint_service import (
        FENCE_END as FENCE_END,
        GENERATED_DIAGRAM_SECTIONS as GENERATED_DIAGRAM_SECTIONS,
        InventoryCacheOptions as InventoryCacheOptions,
        KnowledgeLintSummary as KnowledgeLintSummary,
        LintIssue as LintIssue,
        LintReport as LintReport,
        MERMAID_CLICK_RE as MERMAID_CLICK_RE,
        MERMAID_FENCE as MERMAID_FENCE,
        MERMAID_NODE_RE as MERMAID_NODE_RE,
        _KnowledgeLintState as _KnowledgeLintState,
        _PROFILE_PHASES as _PROFILE_PHASES,
        _build_page_index as _build_page_index,
        _check_broken_links as _check_broken_links,
        _check_data_flow_diagnostics as _check_data_flow_diagnostics,
        _check_dependency_coverage as _check_dependency_coverage,
        _check_flow_coverage as _check_flow_coverage,
        _check_infrastructure_coverage as _check_infrastructure_coverage,
        _check_javascript_flow_diagnostics as _check_javascript_flow_diagnostics,
        _check_knowledge_lint as _check_knowledge_lint,
        _check_module_coverage as _check_module_coverage,
        _check_orphan_pages as _check_orphan_pages,
        _check_sync_manifest as _check_sync_manifest,
        _collect_code_classes as _collect_code_classes,
        _collect_code_modules as _collect_code_modules,
        _collect_docker_files as _collect_docker_files,
        _collect_documented_infrastructure as _collect_documented_infrastructure,
        _diagnose as _diagnose,
        _reliably_missing_source_paths as _reliably_missing_source_paths,
        _set_knowledge_summary as _set_knowledge_summary,
        build_report as build_report,
        build_runtime_live_evaluation as build_runtime_live_evaluation,
        build_source_snapshot as build_source_snapshot,
        get_entry_points as get_entry_points,
        get_inventory_result as get_inventory_result,
        load_knowledge_state as load_knowledge_state,
        print_extraction_job_plan as print_extraction_job_plan,
        render_markdown as render_markdown,
        render_text as render_text,
        report_to_dict as report_to_dict,
        run as run,
    )

_sys.modules[__name__] = _service
