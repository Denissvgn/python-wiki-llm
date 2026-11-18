"""CLI compatibility adapter for the migrate runtime service."""

from __future__ import annotations

import sys as _sys
from typing import TYPE_CHECKING

from ..services import migrate_runtime as _service

if TYPE_CHECKING:
    # Mirror legacy exports for static consumers; runtime imports remain aliases.
    from ..services.migrate_runtime import (
        ExistingPage as ExistingPage,
        MIGRATION_PROGRESS_FILENAME as MIGRATION_PROGRESS_FILENAME,
        MigrateAborted as MigrateAborted,
        MigrateRequestAborted as MigrateRequestAborted,
        MigrationPlan as MigrationPlan,
        TargetPage as TargetPage,
        _build_chunks as _build_chunks,
        _build_match_lookups as _build_match_lookups,
        _build_migration_plan as _build_migration_plan,
        _ensure_legacy_gitignore as _ensure_legacy_gitignore,
        _manifest_needs_write as _manifest_needs_write,
        _manifest_payload as _manifest_payload,
        _match_existing_page as _match_existing_page,
        _prepare_migration_governance_plan as _prepare_migration_governance_plan,
        _read_existing_page as _read_existing_page,
        _rewrite_links_in_content as _rewrite_links_in_content,
        _split_location as _split_location,
        _workflow_link_sources as _workflow_link_sources,
        atomic_write_guarded_bytes as atomic_write_guarded_bytes,
        build_runtime_knowledge_plan as build_runtime_knowledge_plan,
        execute_migrate as execute_migrate,
        finalize_runtime_knowledge as finalize_runtime_knowledge,
        get_call_graph as get_call_graph,
        migrate_request_from_args as migrate_request_from_args,
        run as run,
        run_request as run_request,
    )

_sys.modules[__name__] = _service
