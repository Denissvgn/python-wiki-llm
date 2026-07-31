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
from typing import Any, Iterable, Mapping
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
from ..documentation_calibration import (
    build_flow_evidence_census,
    build_p0_calibration_shadow,
)
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
    TreeBaseline,
    capture_tree_baseline,
    compare_tree_baseline,
    hash_bytes,
    resolve_documentation_policy,
    source_tree_baseline,
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
from ..skills import export_skills, list_bundled_skills
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
    'TreeBaseline',
    'capture_tree_baseline',
    'compare_tree_baseline',
    'hash_bytes',
    'resolve_documentation_policy',
    'source_tree_baseline',
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
