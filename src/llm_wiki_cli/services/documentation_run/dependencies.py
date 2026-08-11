"""Imports shared by the mechanically split lifecycle modules."""

from __future__ import annotations

import copy
import errno
import hashlib
import importlib.util
import json
import os
import re
import shutil
import stat
import subprocess
import sys
import tempfile
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any, Iterable, Mapping, Optional
from urllib.parse import urlsplit
from ... import __version__
from ..contracts import (
    DOCUMENTATION_AGENT_PACKET_SCHEMA_VERSION,
    DOCUMENTATION_AGENT_RESULT_SCHEMA_VERSION,
    DOCUMENTATION_FINAL_REPORT_SCHEMA_VERSION,
    DOCUMENTATION_RUN_SCHEMA_VERSION,
    DOCUMENTATION_SEMANTIC_READINESS_SCHEMA_VERSION,
    DOCUMENTATION_VERIFICATION_SCHEMA_VERSION,
)
from ..bootstrap_service import BootstrapRequest
from ..documentation_claim_evidence import (
    DocumentationClaimEvidenceError,
    normalize_claim_evidence_records,
    normalize_runtime_capture_records,
    preflight_runtime_capture_records,
    reconcile_claim_evidence_records,
    reconcile_runtime_capture_records,
)
from ..documentation_native import (
    DocumentationNativeError,
    DocumentationNativeRefresh,
    refresh_documentation_native_projection,
)
from ..documentation_query_builder import (
    build_documentation_query_service_from_view,
    build_live_documentation_query_service,
    build_snapshot_documentation_query_service,
)
from ..documentation_queries import DocumentationQueryError
from ..documentation_worklist import (
    DOCUMENTATION_WORKLIST_SCHEMA_VERSION,
    build_documentation_worklist,
)
from ..documentation_policy import (
    DocumentationMutationPolicy,
    DocumentationPolicyError,
    IntegrityDifference,
    TreeBaseline,
    capture_tree_baseline,
    compare_source_plugin_tree_baseline,
    compare_source_snapshot_baseline,
    compare_tree_baseline,
    hash_bytes,
    resolve_documentation_policy,
    source_plugin_tree_baseline,
    source_snapshot_tree_baseline,
    source_tree_baseline,
)
from ..source_selection import (
    SourceSelectionError,
    SourceSelectionPolicy,
    resolve_source_selection,
    source_selection_identity_from_generation_inputs,
)
from ..source_snapshot import (
    SourceSnapshot,
    build_source_snapshot,
    capture_source_selection_inputs,
)
from ..documentation_review import (
    DocumentationReviewError,
    DocumentationReviewLedger,
    DocumentationReviewPacket,
    apply_review_loop,
    create_review_ledger,
    normalize_review_findings,
    reconcile_review_ledger,
)
from ..documentation_wiki_input import SUPPORTED_MANIFEST_VERSIONS
from ..filesystem_guard import (
    WindowsDirectoryGuardError,
    guard_windows_directory_chain,
)
from ..io import read_md, write_bytes_atomic, write_text_output
from ..knowledge_artifacts import KNOWLEDGE_INDEX_FILENAME
from ..knowledge_consumption import KnowledgeReadView
from ..knowledge_governance import GOVERNANCE_FILENAME
from ..skills import (
    REFERENCE_DEPENDENT_SKILLS,
    REFERENCE_SKILL_ID,
    export_skills,
    list_bundled_skills,
)
from ..validation import (
    parse_utc_timestamp,
    portable_path_key,
    require_exact_fields as require_shared_exact_fields,
    require_nonempty_text,
    require_portable_relative_path,
    require_sha256 as require_shared_sha256,
    require_trimmed_text_list,
    resolve_workspace_path,
)
from ..verification_contracts import VERIFICATION_RECEIPT_FILENAME
from ..wiki_media import (
    iter_markdown_link_targets,
    local_link_path,
    strip_fenced_code_blocks,
)
from ..wiki_surface_index import WIKI_SURFACE_INDEX_SCHEMA_VERSION


# Documentation preparation emits calibration evidence, but importing the
# ordinary lifecycle must not pull the isolated calibration stack into every
# CLI process.  These signature-preserving adapters cross that boundary only
# when preparation actually requests the evidence.
def build_flow_evidence_census(
    wiki_dir: str,
    *,
    source_root: Optional[str] = None,
    source_revision: str = "unknown",
    source_fingerprint: str = "unknown",
    dependency_evidence: Optional[Mapping[str, Any]] = None,
    tool_revision: str = "unknown",
    allow_surface_fallback: bool = False,
) -> dict[str, Any]:
    from ..calibration.contracts import (
        build_flow_evidence_census as implementation,
    )

    return implementation(
        wiki_dir,
        source_root=source_root,
        source_revision=source_revision,
        source_fingerprint=source_fingerprint,
        dependency_evidence=dependency_evidence,
        tool_revision=tool_revision,
        allow_surface_fallback=allow_surface_fallback,
    )


def build_p0_calibration_shadow(
    worklist: Mapping[str, Any],
    census: Mapping[str, Any],
    *,
    candidate_records: Optional[Iterable[Mapping[str, Any]]] = None,
    policy_version: str = "unscored-shadow/v1",
) -> dict[str, Any]:
    from ..calibration.contracts import (
        build_p0_calibration_shadow as implementation,
    )

    return implementation(
        worklist,
        census,
        candidate_records=candidate_records,
        policy_version=policy_version,
    )


__all__ = (
    'copy',
    'errno',
    'hashlib',
    'importlib',
    'json',
    'os',
    're',
    'shutil',
    'stat',
    'subprocess',
    'sys',
    'tempfile',
    'uuid',
    'dataclass',
    'field',
    'datetime',
    'timezone',
    'Path',
    'PurePosixPath',
    'Any',
    'Iterable',
    'Mapping',
    'urlsplit',
    '__version__',
    'DOCUMENTATION_AGENT_PACKET_SCHEMA_VERSION',
    'DOCUMENTATION_AGENT_RESULT_SCHEMA_VERSION',
    'DOCUMENTATION_FINAL_REPORT_SCHEMA_VERSION',
    'DOCUMENTATION_RUN_SCHEMA_VERSION',
    'DOCUMENTATION_SEMANTIC_READINESS_SCHEMA_VERSION',
    'DOCUMENTATION_VERIFICATION_SCHEMA_VERSION',
    'BootstrapRequest',
    'build_flow_evidence_census',
    'build_p0_calibration_shadow',
    'DocumentationClaimEvidenceError',
    'normalize_claim_evidence_records',
    'normalize_runtime_capture_records',
    'preflight_runtime_capture_records',
    'reconcile_claim_evidence_records',
    'reconcile_runtime_capture_records',
    'DocumentationNativeError',
    'DocumentationNativeRefresh',
    'refresh_documentation_native_projection',
    'build_documentation_query_service_from_view',
    'build_live_documentation_query_service',
    'build_snapshot_documentation_query_service',
    'DocumentationQueryError',
    'DOCUMENTATION_WORKLIST_SCHEMA_VERSION',
    'build_documentation_worklist',
    'DocumentationMutationPolicy',
    'DocumentationPolicyError',
    'IntegrityDifference',
    'TreeBaseline',
    'capture_tree_baseline',
    'compare_source_plugin_tree_baseline',
    'compare_source_snapshot_baseline',
    'compare_tree_baseline',
    'hash_bytes',
    'resolve_documentation_policy',
    'source_plugin_tree_baseline',
    'source_snapshot_tree_baseline',
    'source_tree_baseline',
    'SourceSelectionError',
    'SourceSelectionPolicy',
    'resolve_source_selection',
    'source_selection_identity_from_generation_inputs',
    'SourceSnapshot',
    'build_source_snapshot',
    'capture_source_selection_inputs',
    'DocumentationReviewError',
    'DocumentationReviewLedger',
    'DocumentationReviewPacket',
    'apply_review_loop',
    'create_review_ledger',
    'normalize_review_findings',
    'reconcile_review_ledger',
    'SUPPORTED_MANIFEST_VERSIONS',
    'WindowsDirectoryGuardError',
    'guard_windows_directory_chain',
    'read_md',
    'write_bytes_atomic',
    'write_text_output',
    'KNOWLEDGE_INDEX_FILENAME',
    'KnowledgeReadView',
    'GOVERNANCE_FILENAME',
    'export_skills',
    'list_bundled_skills',
    'REFERENCE_DEPENDENT_SKILLS',
    'REFERENCE_SKILL_ID',
    'parse_utc_timestamp',
    'portable_path_key',
    'require_shared_exact_fields',
    'require_nonempty_text',
    'require_portable_relative_path',
    'require_shared_sha256',
    'require_trimmed_text_list',
    'resolve_workspace_path',
    'VERIFICATION_RECEIPT_FILENAME',
    'iter_markdown_link_targets',
    'local_link_path',
    'strip_fenced_code_blocks',
    'WIKI_SURFACE_INDEX_SCHEMA_VERSION',
)
