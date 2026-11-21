"""Build Qualified Context Packets from one captured read.

The packet builder coordinates one source inventory, one wiki surface
evaluation, and one native-knowledge read view.  Context response construction
then consumes only those captured values.  Optimistic source and wiki anchors
are checked before the canonical bytes are returned, so a mutation cannot
silently detach the response from its declared basis.

This module is deliberately provider- and persistence-free.  It returns bytes
in memory and never refreshes native artifacts.  Checking a packet's format
lives in :mod:`context_packet`, which loads none of the builders.
"""

from __future__ import annotations

from llm_wiki_engine.layout import DEFAULT_LAYOUT

import os
import re
import stat
from collections.abc import Callable, Iterable, Mapping, Sequence
from copy import deepcopy
from dataclasses import dataclass
from contextlib import ExitStack
from contextvars import ContextVar
from functools import wraps
from enum import Enum
from pathlib import Path
from types import MappingProxyType
from typing import Any

from .. import __version__
from llm_wiki_engine.path_policy import DEFAULT_WIKI_DIR, PathValidationError, validate_path
from . import context_service
from llm_wiki_engine import wiki_surface
from llm_wiki_engine.contracts import (
    CONTEXT_KNOWLEDGE_PROTOCOL_VERSION,
)
from .dependencies import analyze_dependencies
from .domain_pack import uses_builtin_context_source
from .documentation_queries import (
    DocumentationGraphQueryService,
    DocumentationQueryError,
    knowledge_view_selection_eligible,
)
from .documentation_query_builder import validate_live_query_source_selection
from .extraction_jobs import ExtractionJobPlan, ExtractionJobRequest
from .extraction_service import InventoryResult
from llm_wiki_engine.knowledge_consumption import KnowledgeReadView
from llm_wiki_engine.knowledge_evidence import (
    is_valid_sha256,
    sha256_bytes,
)
from llm_wiki_engine.knowledge_envelope import (
    hash_source_snapshot,
)
from llm_wiki_engine.knowledge_model import (
    ComputedFreshness,
)
from .source_snapshot import directory_identity
from llm_wiki_engine.io import first_unsafe_path_component
from llm_wiki_engine.knowledge_governance import GOVERNANCE_LOCK_FILENAME, _governance_lock_root
from llm_wiki_engine.filesystem_guard import fresh_no_follow_stat, guard_windows_directory_chain, hold_windows_readonly_file
from llm_wiki_engine.knowledge_observability import knowledge_freshness_disclosure
from llm_wiki_engine.knowledge_verification import verification_summaries_for_concepts
from .plugins import runtime_plugin_fallback_root
from .source_snapshot import (
    SourceSnapshot,
    SourceSnapshotError,
    SourceSnapshotMutationError,
    build_source_snapshot,
    capture_source_selection_inputs,
    source_snapshot_inputs_match_current_files,
    source_snapshot_matches_current_files,
)
from llm_wiki_engine.wiki_surface_index import SurfaceIndexEvaluation, evaluate_surface_index
from llm_wiki_engine.context_packet import _context_policy_digest, _domain_hash, _encode_packet_payload, _freeze_json, _KNOWLEDGE_PACKET_CONTRACT, _LEGACY_PACKET_CONTRACT, _LIMITATION_RE, _packet_id, _packet_limitations, _PacketWireContract, _path_policy_receipt, _thaw_json, CONTEXT_PACKET_ASSURANCE_LEVEL, ContextPacketError, ContextPacketMalformedError, ContextPacketPathPolicyError, QualifiedContextPacket, validate_context_packet


CONTEXT_PACKET_RECONCILIATION_POLICY = "qualified-context-complete-policy-v1"


_SOURCE_ANCHOR_DOMAIN = "llm-wiki/qualified-context-source-anchor/v1"


_WIKI_ANCHOR_DOMAIN = "llm-wiki/qualified-context-wiki-anchor/v1"


_FRESHNESS_DIGEST_DOMAIN = "llm-wiki/qualified-context-freshness/v1"


_RECONCILIATION_FACETS = frozenset(
    {
        "request",
        "source_snapshot",
        "repository",
        "availability",
        "knowledge",
        "generator",
        "freshness",
        "context_response",
        "delivery",
        "path_policy",
    }
)


_RECONCILIATION_FACET_FIELDS = frozenset(
    {"matches_expected", "current", "state", "reason"}
)


class ContextPacketSourceMutationError(ContextPacketError):
    """A captured source or wiki anchor changed before packet return."""

    code = "context-read-mutated"

    def __init__(self, facet: str):
        self.facet = facet
        super().__init__(
            f"{facet} changed while the qualified context packet was being built"
        )


class ContextPacketUnavailableError(ContextPacketError):
    """A required read-only packet capability is unavailable."""

    code = "context-packet-unavailable"

    def __init__(self, message: str, *, field: str = "context"):
        self.field = field
        super().__init__(message)


class ContextPacketAuthorityError(ContextPacketError):
    """Ordinary authority refused a read; only explicit complete recovery can restore it."""

    code = "maintenance-authority-unavailable"
    field = "wiki_dir"

    def __init__(self, issues):
        # Raw loader issues stay in the chained local cause. No raw message,
        # host path, malformed marker or guessed recovery identity is rendered.
        allowed = {
            "maintenance-owner-missing", "maintenance-owner-invalid", "maintenance-owner-incompatible",
            "maintenance-owner-mismatch", "maintenance-adoption-missing", "maintenance-adoption-invalid",
            "maintenance-adoption-mismatch",
        }
        self.issues = issues
        causes = list(dict.fromkeys(issue.code for issue in self.issues if issue.code in allowed))[:4]
        self.details = {
            "field": self.field, "reason": causes[0] if causes else "maintenance-authority-invalid",
            "causes": causes, "native_evidence": "unavailable",
            "recovery": {
                "operation": "maintenance recover", "automatic": False, "snapshot_kind": "committed",
                "argv_template": ["llm-wiki", "maintenance", "recover", "--wiki-dir", "{wiki_dir}",
                                  "--recovery-dir", "{recovery_dir}", "--expected-adoption-id", "{expected_adoption_id}"],
                "identity_requirement": "Use the same existing adoption_id from a validated immutable marker or matching complete committed recovery snapshot; never allocate a new identity.",
                "boundary_requirement": "Keep the original request's wiki_dir and src_dir/source selection. Select a complete committed recovery directory outside the wiki and source inputs; no source or wiki is changed by this read.",
                "preconditions": [
                    "Preserve current bytes and custody. Restore one complete matching committed snapshot, including marker, owner, projections, pages and history; do not combine backups.",
                    "Recovery refuses another identity, newer committed authority or conflicting authored edits. Do not reinitialize, delete the marker or enable prepared/captured-preimage modes to bypass refusal.",
                    "Absent validated generated roots and referenced objects can be restored from a committed snapshot only with a matching surviving marker or owner. Missing authored or unreferenced files and changed existing bytes still refuse; preserve that refusal.",
                    "Recovery is a separate authorized write. Then run owning sync and validation with the original source/wiki roots and selection before relying on native evidence.",
                ],
            },
        }
        super().__init__("wiki_dir: Ordinary maintenance authority is missing, invalid or inconsistent. Restore its complete matching committed recovery snapshot through maintenance recover.")


def describe_context_packet_error(error: BaseException) -> dict[str, Any]:
    """Describe a packet failure without echoing offending values or host roots.

    Dynamic mapping keys and raw service messages belong to the chained local
    exception, not to the public diagnostic shared by API, CLI and MCP.
    """
    from .helper_cache import HelperPreparationError
    if isinstance(error, HelperPreparationError):
        from .extractor_helpers import SUPPORTED_HELPERS
        return {
            "code": "helper-preparation-failed",
            "message": "Could not prepare the required helper. Check the selected toolchain and helper cache.",
            "details": {"field": "helper_preparation",
                        "language": error.language if error.language in SUPPORTED_HELPERS else "unknown"},
        }
    if isinstance(error, ContextPacketAuthorityError):
        return {"code": error.code, "message": str(error), "details": deepcopy(error.details)}
    field = getattr(error, "field", None)
    code = "invalid-request"
    message = "Context request is invalid. Check the indicated field."
    if isinstance(error, ContextPacketMalformedError):
        code = (
            "unsupported-context-packet"
            if error.code == "unsupported-context-packet"
            else "malformed-context-packet"
        )
        message = (
            "Packet schema is unsupported. Use a supported qualified packet version."
            if code == "unsupported-context-packet"
            else "Packet bytes do not satisfy the canonical context contract."
        )
    elif isinstance(error, ContextPacketSourceMutationError):
        code = error.code
        field = {"source": "source_snapshot", "wiki": "wiki_dir"}.get(
            error.facet, error.facet
        )
        message = "Source or wiki changed during the context read. Retry the operation."
    elif isinstance(error, ContextPacketUnavailableError):
        code = error.code
        message = "A required context input or read capability is unavailable."
    elif isinstance(error, (ContextPacketPathPolicyError, PathValidationError)):
        code = "path-policy-error"
        if isinstance(error, PathValidationError):
            flag = re.match(r"^(?:Error:\s*)?--(src|wiki)-dir\b", str(error))
            field = f"{flag.group(1)}_dir" if flag is not None else "path"
            cause = error.__cause__
            seen: set[int] = set()
            while cause is not None and id(cause) not in seen:
                seen.add(id(cause))
                if isinstance(cause, OSError):
                    break
                cause = cause.__cause__
            if isinstance(cause, OSError):
                code = "workspace-state-error"
        message = (
            "The context workspace could not be read. Check availability and access."
            if code == "workspace-state-error"
            else "Context path must satisfy the allowed source and wiki boundary."
        )
    elif isinstance(error, context_service.ProtocolRequestError):
        if field == "wiki_dir":
            code = "path-policy-error"
            message = "The wiki path cannot be read under the context path policy."
        elif field == "src_dir":
            code = "context-packet-unavailable"
            message = "The source directory is unavailable or cannot be read."

    roots = {
        "packet", "schema_version", "packet_id", "assurance", "request",
        "response", "basis", "delivery", "path_policy", "expected_basis",
        "src_dir", "wiki_dir", "path", "context", "source_snapshot",
        "source_selection", "protocol", "knowledge_mode", "read_only",
        "budget_tokens", "focus", "format", "filters", "prefer_fresh",
        "if_packet_id", "counter_id", "budget_mode", "changes", "allow_external_src",
        "context_source",
    }
    if field is None and isinstance(error, (TypeError, ValueError)):
        candidate = re.match(r"^([a-z_]+)\b", str(error))
        if candidate is not None and candidate.group(1) in roots:
            field = candidate.group(1)
    # Only fixed contract roots may reach diagnostics. In particular, paths used
    # as keys below response.files never become user-visible error fields.
    first = re.split(r"[.\[/]", field.lstrip("$./"))[0] if isinstance(field, str) else ""
    safe_field = first if first in roots else "packet"
    return {
        "code": code,
        "message": f"{safe_field}: {message}",
        "details": {"field": safe_field},
    }


def _packet_contract_for_request(request: Mapping[str, Any]) -> _PacketWireContract:
    protocol = request.get("protocol")
    if protocol == _LEGACY_PACKET_CONTRACT.context_protocol:
        return _LEGACY_PACKET_CONTRACT
    if protocol == _KNOWLEDGE_PACKET_CONTRACT.context_protocol:
        return _KNOWLEDGE_PACKET_CONTRACT
    raise context_service.ProtocolRequestError(
        f"Unsupported protocol: {protocol!r}.",
        "protocol",
    )


@dataclass(frozen=True)
class CapturedContextRead:
    """One coordinated in-memory source/wiki read used by a packet response."""

    source_root: Path
    wiki_root: Path
    inventory_result: InventoryResult
    source_snapshot: SourceSnapshot
    inventory: Mapping[str, Any]
    changed_files: tuple[str, ...] | None
    entrypoints: tuple[Mapping[str, Any], ...]
    call_edges: tuple[Mapping[str, Any], ...]
    flows: tuple[Mapping[str, Any], ...]
    data_flows: tuple[Mapping[str, Any], ...]
    dependency_analysis: Mapping[str, Any]
    surface_evaluation: SurfaceIndexEvaluation
    knowledge_view: KnowledgeReadView
    source_anchor: str
    wiki_anchor: str
    basis_incompatible: bool = False
    strict_wiki_symlinks: bool = False
    allow_external_src: bool = False
    explicit_changes: bool = False
    change_selection: Mapping[str, Any] | None = None
    wiki_integrity: Mapping[str, tuple[int, ...]] | None = None
    raw_content_by_page: Mapping[str, bytes] | None = None
    capture_implementation_requested: bool = False

    def __post_init__(self) -> None:
        if not isinstance(self.source_root, Path) or not self.source_root.is_absolute():
            raise TypeError("source_root must be an absolute Path")
        if not isinstance(self.wiki_root, Path) or not self.wiki_root.is_absolute():
            raise TypeError("wiki_root must be an absolute Path")
        if not isinstance(self.inventory_result, InventoryResult):
            raise TypeError("inventory_result must be an InventoryResult")
        if not isinstance(self.source_snapshot, SourceSnapshot):
            raise TypeError("source_snapshot must be a SourceSnapshot")
        if not isinstance(self.surface_evaluation, SurfaceIndexEvaluation):
            raise TypeError("surface_evaluation must be a SurfaceIndexEvaluation")
        if not isinstance(self.knowledge_view, KnowledgeReadView):
            raise TypeError("knowledge_view must be a KnowledgeReadView")
        if not isinstance(self.allow_external_src, bool):
            raise TypeError("allow_external_src must be a boolean")
        if not is_valid_sha256(self.source_anchor):
            raise ValueError("source_anchor must be a canonical SHA-256 value")
        if not is_valid_sha256(self.wiki_anchor):
            raise ValueError("wiki_anchor must be a canonical SHA-256 value")
        if not isinstance(self.basis_incompatible, bool):
            raise TypeError("basis_incompatible must be a boolean")
        if not isinstance(self.strict_wiki_symlinks, bool):
            raise TypeError("strict_wiki_symlinks must be a boolean")


@dataclass(frozen=True)
class ContextBasisComparison:
    """Comparison with caller data, which can never assert currentness."""

    packet_id: str
    matches_expected: bool
    facet_matches: Mapping[str, bool]
    current: None = None
    reason: str = "caller-basis-comparison-is-not-live-reconciliation"

    def to_payload(self) -> dict[str, Any]:
        return {
            "packet_id": self.packet_id,
            "matches_expected": self.matches_expected,
            "current": None,
            "reason": self.reason,
            "facets": {
                name: {
                    "matches_expected": matches,
                    "current": None,
                }
                for name, matches in sorted(self.facet_matches.items())
            },
        }


@dataclass(frozen=True, init=False)
class ContextPacketReconciliation:
    """Consumer-time comparison against one fresh official read."""

    packet_id: str
    policy: str
    state: str
    current: bool | None
    facets: Mapping[str, Mapping[str, Any]]
    limitations: tuple[str, ...] = ()

    def __init__(self) -> None:
        raise TypeError(
            "ContextPacketReconciliation values are returned by "
            "reconcile_context_packet"
        )

    @classmethod
    def _from_official_read(
        cls,
        *,
        packet_id: str,
        policy: str,
        state: str,
        current: bool | None,
        facets: Mapping[str, Mapping[str, Any]],
        limitations: Sequence[str] = (),
    ) -> ContextPacketReconciliation:
        frozen_facets = _freeze_json(facets)
        normalized_limitations = tuple(limitations)
        _validate_reconciliation_contract(
            packet_id=packet_id,
            policy=policy,
            state=state,
            current=current,
            facets=frozen_facets,
            limitations=normalized_limitations,
        )
        instance = object.__new__(cls)
        object.__setattr__(instance, "packet_id", packet_id)
        object.__setattr__(instance, "policy", policy)
        object.__setattr__(instance, "state", state)
        object.__setattr__(instance, "current", current)
        object.__setattr__(instance, "facets", frozen_facets)
        object.__setattr__(instance, "limitations", normalized_limitations)
        return instance

    def to_payload(self) -> dict[str, Any]:
        return {
            "packet_id": self.packet_id,
            "policy": self.policy,
            "state": self.state,
            "current": self.current,
            "facets": _thaw_json(self.facets),
            "limitations": list(self.limitations),
        }


def _validate_reconciliation_contract(
    *,
    packet_id: object,
    policy: object,
    state: object,
    current: object,
    facets: object,
    limitations: object,
) -> None:
    if not isinstance(packet_id, str) or not is_valid_sha256(packet_id):
        raise ValueError("packet_id must be a canonical SHA-256 value")
    if policy != CONTEXT_PACKET_RECONCILIATION_POLICY:
        raise ValueError(
            "policy must be the complete context-packet reconciliation policy"
        )
    if not isinstance(facets, Mapping):
        raise ValueError("facets must be an object")
    missing = sorted(_RECONCILIATION_FACETS - set(facets))
    if missing:
        raise ValueError(f"facets.{missing[0]} is required")
    unknown = sorted(set(facets) - _RECONCILIATION_FACETS)
    if unknown:
        raise ValueError(f"facets.{unknown[0]} is not supported")

    facet_currentness: list[bool | None] = []
    for name in sorted(_RECONCILIATION_FACETS):
        finding = facets[name]
        if not isinstance(finding, Mapping):
            raise ValueError(f"facets.{name} must be an object")
        missing_fields = sorted(_RECONCILIATION_FACET_FIELDS - set(finding))
        if missing_fields:
            raise ValueError(f"facets.{name}.{missing_fields[0]} is required")
        unknown_fields = sorted(set(finding) - _RECONCILIATION_FACET_FIELDS)
        if unknown_fields:
            raise ValueError(f"facets.{name}.{unknown_fields[0]} is not supported")
        matches_expected = finding["matches_expected"]
        facet_current = finding["current"]
        facet_state = finding["state"]
        reason = finding["reason"]
        if not isinstance(matches_expected, bool):
            raise ValueError(f"facets.{name}.matches_expected must be a boolean")
        if (
            facet_current is not True
            and facet_current is not False
            and facet_current is not None
        ):
            raise ValueError(f"facets.{name}.current must be true, false, or null")
        if facet_state not in {"current", "stale", "unevaluated"}:
            raise ValueError(
                f"facets.{name}.state must be current, stale, or unevaluated"
            )
        if not isinstance(reason, str) or not reason.strip():
            raise ValueError(f"facets.{name}.reason must be a non-empty string")
        if (
            (
                facet_state == "current"
                and (facet_current is not True or matches_expected is not True)
            )
            or (
                facet_state == "stale"
                and (facet_current is not False or matches_expected is not False)
            )
            or (facet_state == "unevaluated" and facet_current is not None)
        ):
            raise ValueError(f"facets.{name} fields do not agree with its state")
        facet_currentness.append(facet_current)

    if any(value is False for value in facet_currentness):
        expected_state = "stale"
        expected_current: bool | None = False
    elif any(value is None for value in facet_currentness):
        expected_state = "unevaluated"
        expected_current = None
    else:
        expected_state = "current"
        expected_current = True
    if state != expected_state or current is not expected_current:
        raise ValueError("aggregate state and current must match all required facets")

    if not isinstance(limitations, tuple):
        raise ValueError("limitations must be a tuple")
    for index, limitation in enumerate(limitations):
        if (
            not isinstance(limitation, str)
            or _LIMITATION_RE.fullmatch(limitation) is None
        ):
            raise ValueError(
                f"limitations[{index}] must be a lowercase hyphenated identifier"
            )
    if tuple(sorted(set(limitations))) != limitations:
        raise ValueError("limitations must be sorted and contain no duplicates")


_CAPTURE_GUARDS: ContextVar[ExitStack | None] = ContextVar("llm_wiki_capture_guards", default=None)


def _guarded_capture(function):
    @wraps(function)
    def wrapped(*args, **kwargs):
        with ExitStack() as stack:
            token = _CAPTURE_GUARDS.set(stack)
            try:
                return function(*args, **kwargs)
            except SourceSnapshotMutationError as exc:
                raise ContextPacketSourceMutationError("source") from exc
            finally:
                _CAPTURE_GUARDS.reset(token)
    return wrapped


def _guard_windows_inputs(root: Path, paths: Iterable[str]) -> None:
    if os.name != "nt":
        return
    stack = _CAPTURE_GUARDS.get()
    if stack is None:
        raise ContextPacketUnavailableError("Input guard ownership is unavailable")
    try:
        held = getattr(stack, "_llm_wiki_held_paths", set())
        setattr(stack, "_llm_wiki_held_paths", held)
        parents = sorted({(root / path).parent for path in paths}, key=str)
        for parent in parents:
            if parent not in held:
                stack.enter_context(guard_windows_directory_chain(Path(parent.anchor), parent.parts[1:]))
                held.add(parent)
        for path in sorted(paths):
            if root / path not in held:
                stack.enter_context(hold_windows_readonly_file(root / path))
                held.add(root / path)
    except OSError as exc:
        raise ContextPacketUnavailableError("Cannot freeze the required Windows inputs") from exc


@_guarded_capture
def capture_context_read(
    src_dir: str = ".",
    wiki_dir: str = DEFAULT_WIKI_DIR,
    *,
    allow_external_src: bool = False,
    read_only: bool = True,
    job_request: ExtractionJobRequest | None = None,
    plan_reporter: Callable[[ExtractionJobPlan], None] | None = None,
    source_selection: str | Path | None = None,
    allow_selection_mismatch: bool = False,
    strict_wiki_symlinks: bool = False,
    helper_cache_dir: str | None = None,
    only_files: Iterable[str] | None = None,
    max_source_files: int | None = None,
    max_source_bytes: int | None = None,
    max_wiki_bytes: int | None = None,
    respect_ignores: bool = False,
    capture_implementation_observations: bool = True,
) -> CapturedContextRead:
    """Capture one source inventory, wiki surface, and knowledge read view.

    The function is read-only.  It brackets wiki reads with a content anchor
    and validates the source snapshot after extraction, rejecting an
    inconsistent capture rather than returning a partially detached view.
    """

    if not isinstance(read_only, bool):
        raise TypeError("read_only must be a boolean")
    if not isinstance(allow_external_src, bool):
        raise TypeError("allow_external_src must be a boolean")
    if plan_reporter is not None and not callable(plan_reporter):
        raise TypeError("plan_reporter must be callable or None")
    if not isinstance(allow_selection_mismatch, bool):
        raise TypeError("allow_selection_mismatch must be a boolean")
    if not isinstance(strict_wiki_symlinks, bool):
        raise TypeError("strict_wiki_symlinks must be a boolean")
    if not isinstance(capture_implementation_observations, bool):
        raise TypeError("capture_implementation_observations must be a boolean")

    basis_incompatible = False

    try:
        source_root = context_service.validate_source_root(
            src_dir,
            "--src-dir",
            allow_external=allow_external_src,
        )
        wiki_root = validate_path(wiki_dir, "--wiki-dir")
    except PathValidationError:
        raise

    if not source_root.is_dir():
        raise ContextPacketUnavailableError(
            "Source directory must exist and be a directory.", field="src_dir"
        )

    # Broken adopted authority must be diagnosed before source-retirement or
    # selection helpers attempt to consume its owner as ordinary metadata.
    from llm_wiki_engine.maintenance_protocol import ADOPTION_FILENAME, guard_maintenance_owner, MaintenanceProtocolError

    marker_path = wiki_root / ADOPTION_FILENAME
    if marker_path.exists() or marker_path.is_symlink():
        try:
            guard_maintenance_owner(wiki_root)
        except MaintenanceProtocolError as exc:
            from llm_wiki_engine.knowledge_loader import KnowledgeLoadIssue

            raise ContextPacketAuthorityError((KnowledgeLoadIssue(
                "maintenance-" + exc.reason, ADOPTION_FILENAME, str(exc)),)) from exc

    try:
        selection_policy = context_service.resolve_source_selection(
            source_root,
            source_selection,
        )
        selection_inputs = capture_source_selection_inputs(
            source_root,
            source_selection=source_selection,
            selection_policy=selection_policy,
            **({"max_bytes": max_source_bytes} if max_source_bytes is not None else {}),
        )
        validate_live_query_source_selection(
            source_root=source_root,
            wiki_root=wiki_root,
            live_identity=(
                selection_policy.identity if selection_policy is not None else None
            ),
            live_selection_inputs=selection_inputs,
            operation="qualified context packet",
        )
    except DocumentationQueryError as exc:
        if not allow_selection_mismatch:
            raise context_service.ProtocolRequestError(
                str(exc),
                "source_selection",
            ) from exc
        basis_incompatible = True
    except context_service.SourceSelectionError as exc:
        raise context_service.ProtocolRequestError(
            str(exc),
            "source_selection",
        ) from exc
    capture_options: dict[str, Any] = {}
    if only_files is not None:
        capture_options["only_files"] = only_files
    if max_source_files is not None:
        capture_options["max_files"] = max_source_files
    if max_source_bytes is not None:
        capture_options["max_bytes"] = max_source_bytes
    if respect_ignores:
        capture_options["respect_ignores"] = True
        capture_options["coherent"] = True
    source_snapshot = build_source_snapshot(
        source_root,
        source_selection=source_selection,
        selection_policy=selection_policy,
        expected_selection_inputs=selection_inputs,
        **capture_options,
    )
    if respect_ignores and os.name == "nt":
        _guard_windows_inputs(source_root, source_snapshot.captured_content_hashes)
        _assert_source_unchanged(source_snapshot, _source_anchor(source_snapshot))

    helper_options: dict[str, Any] = {"helper_cache_dir": helper_cache_dir} if helper_cache_dir is not None else {}
    from llm_wiki_engine.source_retirement import retained_empty_module_paths_from_wiki
    empty_paths = retained_empty_module_paths_from_wiki(wiki_root)
    if empty_paths:
        helper_options["retain_empty_paths"] = empty_paths
    collected = context_service.get_inventory(
        str(source_root),
        deep=True,
        return_result=True,
        job_request=job_request,
        plan_reporter=plan_reporter,
        include_plugins=False,
        source_selection=source_selection,
        source_snapshot=source_snapshot,
        capture_implementation_observations=capture_implementation_observations,
        **helper_options,
    )
    if not isinstance(collected, InventoryResult):
        raise ContextPacketUnavailableError(
            "qualified context construction requires a captured InventoryResult"
        )
    if collected.failed:
        raise context_service.ProtocolRequestError(
            context_service._extractor_failure_message(collected),
            "src_dir",
        )
    source_snapshot = collected.source_snapshot
    if not isinstance(source_snapshot, SourceSnapshot):
        raise ContextPacketUnavailableError(
            "qualified context construction requires a captured source snapshot"
        )
    inventory = collected.inventory
    if not isinstance(inventory, dict):
        raise ContextPacketUnavailableError(
            "qualified context construction requires a valid source inventory"
        )
    source_anchor = _source_anchor(source_snapshot)
    _assert_source_inputs_unchanged(source_snapshot, source_anchor)
    try:
        validate_live_query_source_selection(
            source_root=source_root,
            wiki_root=wiki_root,
            live_identity=source_snapshot.source_selection_identity,
            live_selection_inputs=source_snapshot.source_selection_inputs,
            operation="qualified context packet",
        )
    except DocumentationQueryError as exc:
        if not allow_selection_mismatch:
            raise context_service.ProtocolRequestError(
                str(exc),
                "source_selection",
            ) from exc
        basis_incompatible = True
    wiki_options: dict[str, Any] = {"max_bytes": max_wiki_bytes} if max_wiki_bytes is not None else {}
    wiki_integrity: dict[str, tuple[int, ...]] | None = {} if respect_ignores else None
    if wiki_integrity is not None:
        wiki_options["integrity_out"] = wiki_integrity
        wiki_options["guard_windows"] = True
    wiki_anchor_before = (
        _wiki_anchor(wiki_root, reject_all_symlinks=True, **wiki_options)
        if strict_wiki_symlinks
        else _wiki_anchor(wiki_root)
    )

    try:
        entrypoints = tuple(
            context_service.get_entry_points(
                inventory,
                console_scripts=context_service.read_console_scripts(
                    str(source_root),
                    source_snapshot=source_snapshot,
                ),
                root=source_root,
                fallback_root=runtime_plugin_fallback_root(
                    source_root,
                    source_selection_configured=(
                        source_snapshot.source_selection_policy is not None
                    ),
                ),
                include_plugins=False,
            )
        )
        call_edges = tuple(context_service.resolve_call_edges(inventory))
        flows = tuple(
            context_service.build_flow(entrypoint, list(call_edges))
            for entrypoint in entrypoints
        )
        data_flow_context = (
            context_service.build_data_flow_context(inventory, list(call_edges))
            if entrypoints
            else None
        )
        data_flows = tuple(
            context_service.analyze_data_flow(
                inventory,
                flow,
                list(call_edges),
                context=data_flow_context,
            )
            for flow in flows
        )
        surface_evaluation = evaluate_surface_index(
            wiki_root,
            inventory,
            src_dir=source_root,
            entry_points=entrypoints,
        )
        knowledge_view = context_service._build_context_knowledge_view(
            wiki_root,
            surface_evaluation,
            inventory,
            collected,
        )
        dependency_analysis = analyze_dependencies(
            inventory,
            str(source_root),
            source_snapshot=source_snapshot,
        )
    except DocumentationQueryError as exc:
        raise context_service.ProtocolRequestError(str(exc), "filters") from exc
    except wiki_surface.WikiSurfacePathError as exc:
        raise ContextPacketPathPolicyError(
            "wiki_dir",
            f"canonical wiki input violates the path policy: {exc.relative_path!r}",
        ) from exc
    except OSError as exc:
        raise context_service.ProtocolRequestError(
            f"Could not capture context read view: {exc}",
            "wiki_dir",
        ) from exc

    wiki_check_options: dict[str, Any] = {}
    if max_wiki_bytes is not None:
        wiki_check_options["max_bytes"] = max_wiki_bytes
    if wiki_integrity is not None:
        wiki_check_options["expected_integrity"] = wiki_integrity
    _assert_wiki_unchanged(
        wiki_root,
        wiki_anchor_before,
        reject_all_symlinks=strict_wiki_symlinks,
        **wiki_check_options,
    )
    wiki_anchor_after = wiki_anchor_before
    _assert_source_inputs_unchanged(source_snapshot, source_anchor)

    changed = context_service._selected_git_changed_files(
        str(source_root),
        source_snapshot,
    )
    try:
        validate_live_query_source_selection(
            source_root=source_root,
            wiki_root=wiki_root,
            live_identity=source_snapshot.source_selection_identity,
            live_selection_inputs=source_snapshot.source_selection_inputs,
            operation="qualified context packet",
        )
    except DocumentationQueryError as exc:
        if not allow_selection_mismatch:
            raise context_service.ProtocolRequestError(
                str(exc),
                "source_selection",
            ) from exc
        basis_incompatible = True
    raw_pages = None
    if capture_implementation_observations and knowledge_view.manifest_basis is not None and knowledge_view.manifest_basis.maintenance_state is not None:
        from llm_wiki_engine.knowledge_storage_io import read_guarded
        raw_pages = {path: read_guarded(wiki_root / path, max_wiki_bytes or 64 * 1024 * 1024).content for path in surface_evaluation.content_by_path}
        _assert_wiki_unchanged(wiki_root, wiki_anchor_after, reject_all_symlinks=strict_wiki_symlinks)
    captured = CapturedContextRead(
        source_root=source_root,
        wiki_root=wiki_root,
        inventory_result=collected,
        source_snapshot=source_snapshot,
        inventory=_freeze_json(inventory),
        changed_files=None if changed is None else tuple(changed),
        entrypoints=tuple(_freeze_json(item) for item in entrypoints),
        call_edges=tuple(_freeze_json(item) for item in call_edges),
        flows=tuple(_freeze_json(item) for item in flows),
        data_flows=tuple(_freeze_json(item) for item in data_flows),
        dependency_analysis=_freeze_json(dependency_analysis),
        surface_evaluation=surface_evaluation,
        knowledge_view=knowledge_view,
        source_anchor=source_anchor,
        wiki_anchor=wiki_anchor_after,
        basis_incompatible=basis_incompatible,
        strict_wiki_symlinks=strict_wiki_symlinks,
        allow_external_src=allow_external_src,
        wiki_integrity=_freeze_json(wiki_integrity) if wiki_integrity is not None else None,
        raw_content_by_page=_freeze_json(raw_pages) if raw_pages is not None else None,
        capture_implementation_requested=capture_implementation_observations,
    )
    from llm_wiki_engine.maintenance_status import attach_maintenance_status
    captured = attach_maintenance_status(captured)
    _assert_source_inputs_unchanged(source_snapshot, source_anchor)
    _assert_wiki_unchanged(wiki_root, wiki_anchor_after, reject_all_symlinks=strict_wiki_symlinks)
    return captured


def build_context_from_captured_read(
    captured: CapturedContextRead,
    request: Mapping[str, Any],
    *,
    freshness_ranking_out: dict[str, int] | None = None,
) -> tuple[dict[str, Any], list[str]]:
    """Build a versioned context payload solely from one captured read."""

    if not isinstance(captured, CapturedContextRead):
        raise TypeError("captured must be a CapturedContextRead")
    normalized = _normalized_request(request)
    if normalized["protocol"] == context_service.PROTOCOL_VERSION:
        return _build_legacy_context_from_captured_read(captured, normalized)
    return _build_knowledge_context_from_captured_read(captured, normalized,
                                                     freshness_ranking_out=freshness_ranking_out)


def _build_legacy_context_from_captured_read(
    captured: CapturedContextRead,
    normalized: Mapping[str, Any],
) -> tuple[dict[str, Any], list[str]]:
    """Retain the frozen v1 response construction without semantic changes."""

    raw_inventory = _thaw_json(captured.inventory)
    filters = normalized["filters"]
    inventory = context_service._apply_protocol_filters(raw_inventory, filters)
    warnings: list[str] = []
    prefer_fresh = normalized["prefer_fresh"]
    freshness_rank_by_source: dict[str, int] = {}
    enrichment: dict[str, Any] = {}
    if prefer_fresh:
        enrichment = _build_protocol_enrichment_from_captured_read(
            captured,
            raw_inventory,
            filters,
            warnings,
            prefer_fresh=True,
            freshness_ranking_out=freshness_rank_by_source,
        )

    if inventory:
        changed: list[str] | None = None
        focus_mode = "all" if "all" in normalized["focus"] else "changed"
        include_neighbors = "neighbors" in normalized["focus"]
        if focus_mode == "changed":
            if captured.changed_files is None:
                warnings.append(
                    "Could not get changed files from git. Treating all files "
                    "as high priority."
                )
                focus_mode = "all"
            elif not captured.changed_files:
                warnings.append(
                    "No files changed in the last commit. Treating all files "
                    "as high priority."
                )
                focus_mode = "all"
            else:
                changed = context_service._normalise_changed_paths(
                    list(captured.changed_files),
                    inventory,
                )
        import_graph = context_service._build_import_graph(inventory)
        classification = context_service._classify_files(
            list(inventory),
            changed,
            import_graph,
            focus_mode,
            include_neighbors=include_neighbors,
        )
        payload, budget_pressure = (
            context_service._build_context_payload_with_freshness_preference(
                inventory,
                classification,
                normalized["budget_tokens"],
                freshness_rank_by_source=(
                    freshness_rank_by_source if prefer_fresh else {}
                ),
            )
        )
    else:
        payload = {
            "budget": normalized["budget_tokens"],
            "used": 0,
            "truncated": False,
            "omitted_files": [],
            "downgraded_files": {},
            "bounds": {
                "files": context_service._bounds_metadata(total=0, returned=0),
            },
            "files": {},
        }
        budget_pressure = False

    if not prefer_fresh:
        enrichment = _build_protocol_enrichment_from_captured_read(
            captured,
            raw_inventory,
            filters,
            warnings,
        )
    ranking_policy = enrichment.get("ranking_policy")
    if isinstance(ranking_policy, dict):
        ranking_policy["budget_pressure"] = budget_pressure
        ranking_policy["applied"] = bool(
            ranking_policy.get("freshness_evaluated")
            and freshness_rank_by_source
            and budget_pressure
        )
    payload.update(enrichment)
    return payload, warnings


def _build_knowledge_context_from_captured_read(
    captured: CapturedContextRead,
    normalized: Mapping[str, Any],
    *,
    freshness_ranking_out: dict[str, int] | None = None,
) -> tuple[dict[str, Any], list[str]]:
    """Build explicit v2 knowledge selection from the coordinated capture."""

    raw_inventory = _thaw_json(captured.inventory)
    filters = normalized["filters"]
    inventory = context_service._apply_protocol_filters(raw_inventory, filters)
    warnings: list[str] = []
    classification = _captured_source_classification(
        captured,
        inventory,
        normalized,
        warnings,
    )
    mode = normalized["knowledge_mode"]
    filter_query_requested = any(
        key in filters for key in ("symbol", "entrypoint", "surface")
    )
    selection_requested = mode in {"auto", "required"}
    selection_eligible = selection_requested and knowledge_view_selection_eligible(
        captured.knowledge_view,
        basis_incompatible=captured.basis_incompatible,
    )
    query_service: DocumentationGraphQueryService | None = None
    query_surface: dict[str, Any] | None = None
    if selection_eligible or filter_query_requested:
        selection_view = captured.knowledge_view if selection_eligible else None
        query_surface = context_service._context_query_surface(
            captured.surface_evaluation.payload,
            selection_view,
            validated_only=selection_eligible,
        )
        query_service = _captured_query_service(
            captured,
            raw_inventory,
            query_surface,
            selection_view,
        )

    enrichment = _explicit_filter_enrichment_from_captured_read(
        query_service,
        query_surface,
        filters,
        warnings,
    )
    freshness_rank_by_source = (
        context_service._context_freshness_rank_by_source(
            query_surface,
            query_service,
        )
        if normalized["prefer_fresh"]
        and selection_eligible
        and query_surface is not None
        and query_service is not None
        else {}
    )
    if freshness_ranking_out is not None:
        freshness_ranking_out.update(freshness_rank_by_source)
    payload, budget_pressure = _captured_source_payload(
        inventory,
        classification,
        normalized["budget_tokens"],
        freshness_rank_by_source=(
            freshness_rank_by_source if normalized["prefer_fresh"] else {}
        ),
    )
    source_priorities = {
        path.replace("\\", "/"): priority
        for path, priority in classification.items()
        if isinstance(path, str) and priority in {"high", "medium", "low"}
    }
    knowledge = context_service._build_explicit_knowledge_response(
        mode,
        captured.knowledge_view if selection_requested else None,
        query_service if selection_requested else None,
        source_priorities,
        src_dir=captured.source_root.as_posix(),
        wiki_dir=captured.wiki_root.as_posix(),
        basis_incompatible=captured.basis_incompatible,
        source_selection=(
            captured.source_snapshot.source_selection_policy.path
            if captured.source_snapshot.source_selection_policy is not None
            else None
        ),
        allow_external_src=captured.allow_external_src,
    )
    if selection_requested and captured.basis_incompatible:
        knowledge = dict(knowledge)
        knowledge["freshness_evaluated"] = False
    maintenance_report = captured.knowledge_view.maintenance_report
    if selection_requested and maintenance_report is not None:
        from llm_wiki_engine.maintenance_status import compact_maintenance_summary
        knowledge = dict(knowledge)
        knowledge["maintenance"] = compact_maintenance_summary(maintenance_report)
    enrichment["knowledge"] = knowledge
    if normalized["prefer_fresh"]:
        enrichment["ranking_policy"] = (
            context_service._explicit_freshness_ranking_policy(
                knowledge,
                freshness_rank_by_source,
                budget_pressure=budget_pressure,
            )
        )
    payload.update(enrichment)
    payload["source_priorities"] = source_priorities
    return payload, warnings


def _captured_source_classification(
    captured: CapturedContextRead,
    inventory: Mapping[str, Any],
    normalized: Mapping[str, Any],
    warnings: list[str],
) -> dict[str, str]:
    if not inventory:
        return {}
    changed: list[str] | None = None
    focus_mode = "all" if "all" in normalized["focus"] else "changed"
    include_neighbors = "neighbors" in normalized["focus"]
    if focus_mode == "changed":
        if captured.changed_files is None:
            warnings.append(
                "Could not get changed files from git. Treating all files "
                "as high priority."
            )
            focus_mode = "all"
        elif not captured.changed_files and not captured.explicit_changes:
            warnings.append(
                "No files changed in the last commit. Treating all files "
                "as high priority."
            )
            focus_mode = "all"
        else:
            changed = context_service._normalise_changed_paths(
                list(captured.changed_files),
                dict(inventory),
            )
    import_graph = context_service._build_import_graph(dict(inventory))
    return context_service._classify_files(
        list(inventory),
        changed,
        import_graph,
        focus_mode,
        include_neighbors=include_neighbors,
    )


def _captured_source_payload(
    inventory: Mapping[str, Any],
    classification: Mapping[str, str],
    budget: int,
    *,
    freshness_rank_by_source: Mapping[str, int],
) -> tuple[dict[str, Any], bool]:
    if inventory:
        return context_service._build_context_payload_with_freshness_preference(
            dict(inventory),
            dict(classification),
            budget,
            freshness_rank_by_source=freshness_rank_by_source,
        )
    return (
        {
            "budget": budget,
            "used": 0,
            "truncated": False,
            "omitted_files": [],
            "downgraded_files": {},
            "bounds": {
                "files": context_service._bounds_metadata(total=0, returned=0),
            },
            "files": {},
        },
        False,
    )


def _captured_query_service(
    captured: CapturedContextRead,
    inventory: Mapping[str, Any],
    query_surface: Mapping[str, Any],
    knowledge_view: KnowledgeReadView | None,
) -> DocumentationGraphQueryService:
    try:
        return DocumentationGraphQueryService(
            dict(inventory),
            call_edges=list(captured.call_edges),
            flows=list(captured.flows),
            data_flows=list(captured.data_flows),
            dependency_analysis=_thaw_json(captured.dependency_analysis),
            surface_index=dict(query_surface),
            limit=context_service._CONTEXT_QUERY_LIMIT,
            knowledge_view=knowledge_view,
            inventory_result=captured.inventory_result,
            machine_verification=(
                verification_summaries_for_concepts(knowledge_view)
                if isinstance(knowledge_view, KnowledgeReadView)
                else None
            ),
        )
    except DocumentationQueryError as exc:
        raise context_service.ProtocolRequestError(str(exc), "filters") from exc


def _explicit_filter_enrichment_from_captured_read(
    query_service: DocumentationGraphQueryService | None,
    query_surface: Mapping[str, Any] | None,
    filters: Mapping[str, Any],
    warnings: list[str],
) -> dict[str, Any]:
    if query_service is None or query_surface is None:
        return {}
    enrichment: dict[str, Any] = {}
    graphs: dict[str, Any] = {}
    knowledge_candidates: list[dict[str, Any]] = []
    relationship_filter_requested = bool(
        context_service._RELATIONSHIP_REFINEMENT_KEYS & set(filters)
    )
    if relationship_filter_requested:
        enrichment["typed_graph"] = context_service._compact_typed_graph_status(
            query_service.typed_graph_status
        )
    if "symbol" in filters:
        symbol = filters["symbol"]
        graphs["symbol"] = {
            "callers": query_service.callers(symbol),
            "callees": query_service.callees(symbol),
            "pages": context_service._symbol_pages_payload(
                query_service,
                dict(query_surface),
                symbol,
                dict(filters),
                observed=knowledge_candidates,
            ),
        }
    if "entrypoint" in filters:
        entrypoint = filters["entrypoint"]
        graphs["entrypoint"] = {
            "flow": query_service.flow_for_entrypoint(entrypoint),
            "data_flow": query_service.data_flow_for_entrypoint(entrypoint),
        }
    if graphs:
        enrichment["graphs"] = graphs
    if "surface" in filters:
        enrichment["surface"] = context_service._surface_filter_payload(
            dict(query_surface),
            filters["surface"],
            limit=context_service._CONTEXT_QUERY_LIMIT,
            query_service=query_service,
            filters=dict(filters),
            observed=knowledge_candidates,
        )
    if relationship_filter_requested:
        context_service._append_typed_graph_context_warning(
            query_service.typed_graph_status,
            knowledge_candidates,
            warnings,
        )
    return enrichment


def build_qualified_context(
    src_dir: str = ".",
    wiki_dir: str = DEFAULT_WIKI_DIR,
    request: Mapping[str, Any] | None = None,
    *,
    allow_external_src: bool = False,
    read_only: bool = True,
    job_request: ExtractionJobRequest | None = None,
    plan_reporter: Callable[[ExtractionJobPlan], None] | None = None,
    source_selection: str | Path | None = None,
) -> QualifiedContextPacket:
    """Build a canonical packet in memory from one coordinated read view."""

    normalized = _normalized_request(
        {
            "budget_tokens": 32_000,
            "focus": ["changed", "neighbors"],
            "format": "json",
            "filters": {},
        }
        if request is None
        else request
    )
    packet_contract = _packet_contract_for_request(normalized)
    captured = capture_context_read(
        src_dir,
        wiki_dir,
        allow_external_src=allow_external_src,
        read_only=read_only,
        job_request=job_request,
        plan_reporter=plan_reporter,
        source_selection=source_selection,
        allow_selection_mismatch=(packet_contract is _KNOWLEDGE_PACKET_CONTRACT),
        strict_wiki_symlinks=(packet_contract is _KNOWLEDGE_PACKET_CONTRACT),
        capture_implementation_observations=(
            normalized.get("knowledge_mode") in {"auto", "required"}
            or (
                normalized.get("knowledge_mode") is None
                and (
                    normalized["prefer_fresh"]
                    or bool(
                        context_service._CONCEPT_FILTER_KEYS
                        & set(normalized["filters"])
                    )
                )
            )
        ),
    )
    payload, warnings = build_context_from_captured_read(captured, normalized)
    response = context_service._protocol_success_payload(
        normalized,
        payload,
        warnings,
    )
    if packet_contract is _KNOWLEDGE_PACKET_CONTRACT:
        response["source_priorities"] = {
            path: priority
            for path, priority in sorted(payload.get("source_priorities", {}).items())
            if isinstance(path, str) and priority in {"high", "medium", "low"}
        }
        response = _fit_knowledge_packet_response(
            captured,
            normalized,
            response,
            packet_contract,
        )
    return packet_from_captured_response(captured, normalized, response)


def packet_from_captured_response(
    captured: CapturedContextRead,
    normalized: Mapping[str, Any],
    response: Mapping[str, Any],
) -> QualifiedContextPacket:
    """Seal and validate a selected response against its unchanged captured basis."""
    if not uses_builtin_context_source():
        # The packet policy digest names the built-in source ranking.
        raise ContextPacketUnavailableError(
            "qualified context packets need the built-in context source; "
            "the active domain pack replaces it",
            field="context_source",
        )
    packet_contract = _packet_contract_for_request(normalized)
    body = _packet_body(captured, normalized, response, packet_contract)

    _assert_source_unchanged(captured.source_snapshot, captured.source_anchor)
    wiki_options: dict[str, Any] = {}
    if captured.wiki_integrity is not None:
        wiki_options["expected_integrity"] = captured.wiki_integrity
    _assert_wiki_unchanged(
        captured.wiki_root,
        captured.wiki_anchor,
        reject_all_symlinks=captured.strict_wiki_symlinks,
        **wiki_options,
    )
    _assert_selection_unchanged(captured)

    semantic_body = {
        "schema_version": packet_contract.schema_version,
        **body,
    }
    packet_id = _packet_id(semantic_body)
    packet_payload = {
        "schema_version": packet_contract.schema_version,
        "packet_id": packet_id,
        **body,
    }
    canonical = _encode_packet_payload(packet_payload)
    validated = validate_context_packet(canonical)
    return validated.packet


def _fit_knowledge_packet_response(
    captured: CapturedContextRead,
    request: Mapping[str, Any],
    response: dict[str, Any],
    packet_contract: _PacketWireContract,
) -> dict[str, Any]:
    """Tail-reduce v2 native selection before the canonical byte limit."""

    if _candidate_packet_size(captured, request, response, packet_contract) <= (
        packet_contract.max_packet_bytes
    ):
        return response
    knowledge = response.get("knowledge")
    if isinstance(knowledge, dict) and knowledge.get("status") == "selected":
        selection = knowledge.get("selection")
        bounds = knowledge.get("bounds")
        if isinstance(selection, dict) and isinstance(bounds, dict):
            for name, minimum in (
                ("relationships", 0),
                ("pages", 0),
                ("concepts", 1),
            ):
                items = selection.get(name)
                bound = bounds.get(name)
                if not isinstance(items, list) or not isinstance(bound, dict):
                    continue
                original_items = list(items)
                if len(original_items) <= minimum:
                    continue
                low = minimum
                high = len(original_items) - 1
                fitted: int | None = None
                while low <= high:
                    candidate = (low + high) // 2
                    _set_knowledge_collection_prefix(
                        selection,
                        bounds,
                        name,
                        original_items,
                        candidate,
                    )
                    knowledge["reason"] = "knowledge-results-truncated"
                    if (
                        _candidate_packet_size(
                            captured,
                            request,
                            response,
                            packet_contract,
                        )
                        <= packet_contract.max_packet_bytes
                    ):
                        fitted = candidate
                        low = candidate + 1
                    else:
                        high = candidate - 1
                if fitted is not None:
                    _set_knowledge_collection_prefix(
                        selection,
                        bounds,
                        name,
                        original_items,
                        fitted,
                    )
                    knowledge["reason"] = "knowledge-results-truncated"
                    return response
                _set_knowledge_collection_prefix(
                    selection,
                    bounds,
                    name,
                    original_items,
                    minimum,
                )
                knowledge["reason"] = "knowledge-results-truncated"

    mode = request["knowledge_mode"]
    if mode == "off":
        raise ContextPacketUnavailableError(
            "disabled knowledge mode cannot fit the v2 packet byte limit without "
            "changing its semantics"
        )
    issue_codes = {issue.code for issue in captured.knowledge_view.projection_findings}
    fallback_evidence = context_service._knowledge_fallback_evidence(
        captured.knowledge_view,
        surface_invalid=bool(
            issue_codes
            & {
                "surface-invalid",
                "surface-read-failed",
                "surface-schema-version-unsupported",
            }
        ),
    )
    if mode == "required":
        raise context_service.KnowledgeRequiredUnavailableError(
            availability="degraded",
            reason="knowledge-result-exceeds-size-limit",
            fallback_evidence=fallback_evidence,
            recovery_command=(
                "narrow the source selection or context focus so the bounded "
                "knowledge result fits the qualified packet limit"
            ),
        )
    previous_bounds = (
        knowledge.get("bounds") if isinstance(knowledge, Mapping) else None
    )
    fallback_bounds = {
        name: {
            "total": (
                int(previous_bounds[name]["total"])
                if isinstance(previous_bounds, Mapping)
                and isinstance(previous_bounds.get(name), Mapping)
                and isinstance(previous_bounds[name].get("total"), int)
                else 0
            ),
            "returned": 0,
            "truncated": bool(
                isinstance(previous_bounds, Mapping)
                and isinstance(previous_bounds.get(name), Mapping)
                and previous_bounds[name].get("total", 0) > 0
            ),
        }
        for name in ("concepts", "pages", "relationships")
    }
    response["knowledge"] = {
        "mode": mode,
        "status": "fallback",
        "availability": "degraded",
        "reason": "knowledge-result-exceeds-size-limit",
        "selected": False,
        "freshness_evaluated": bool(
            isinstance(knowledge, Mapping)
            and knowledge.get("freshness_evaluated") is True
        ),
        "bounds": fallback_bounds,
        "fallback": {
            "used": True,
            "evidence": fallback_evidence,
            "reason": "knowledge-result-exceeds-size-limit",
        },
    }
    if (
        _candidate_packet_size(
            captured,
            request,
            response,
            packet_contract,
        )
        > packet_contract.max_packet_bytes
    ):
        raise ContextPacketUnavailableError(
            "bounded qualified context response exceeds the v2 packet byte limit"
        )
    return response


def _set_knowledge_collection_prefix(
    selection: dict[str, Any],
    bounds: dict[str, Any],
    name: str,
    original_items: list[Any],
    returned: int,
) -> None:
    selection[name] = original_items[:returned]
    bound = bounds[name]
    bound["returned"] = returned
    bound["truncated"] = bound["total"] > returned


def _candidate_packet_size(
    captured: CapturedContextRead,
    request: Mapping[str, Any],
    response: Mapping[str, Any],
    packet_contract: _PacketWireContract,
) -> int:
    body = _packet_body(captured, request, response, packet_contract)
    semantic_body = {"schema_version": packet_contract.schema_version, **body}
    return len(
        _encode_packet_payload(
            {
                "schema_version": packet_contract.schema_version,
                "packet_id": _packet_id(semantic_body),
                **body,
            }
        )
    )


def compare_context_packet_basis(
    packet_bytes: bytes | bytearray | memoryview,
    expected_basis: Mapping[str, Any],
) -> ContextBasisComparison:
    """Compare caller-provided expected basis without claiming currentness."""

    validation = validate_context_packet(packet_bytes)
    if not isinstance(expected_basis, Mapping):
        raise TypeError("expected_basis must be a mapping")
    packet_basis = validation.packet.to_payload()["basis"]
    allowed = set(packet_basis)
    unknown = sorted(set(expected_basis) - allowed)
    if unknown:
        raise ContextPacketMalformedError(
            f"expected_basis.{unknown[0]}",
            "is not a supported basis facet",
        )
    if not expected_basis:
        raise ContextPacketMalformedError(
            "expected_basis",
            "must contain at least one basis facet",
        )
    facet_matches = {
        name: packet_basis[name] == expected_basis[name]
        for name in sorted(expected_basis)
    }
    return ContextBasisComparison(
        packet_id=validation.packet_id,
        matches_expected=all(facet_matches.values()),
        facet_matches=MappingProxyType(facet_matches),
    )


def reconcile_context_packet(
    packet_bytes: bytes | bytearray | memoryview,
    src_dir: str = ".",
    wiki_dir: str = DEFAULT_WIKI_DIR,
    *,
    allow_external_src: bool = False,
    read_only: bool = True,
    job_request: ExtractionJobRequest | None = None,
    plan_reporter: Callable[[ExtractionJobPlan], None] | None = None,
    source_selection: str | Path | None = None,
) -> ContextPacketReconciliation:
    """Validate first, then compare every packet facet with a fresh read."""

    validation = validate_context_packet(packet_bytes)
    packet_payload = validation.packet.to_payload()
    live_packet = build_qualified_context(
        src_dir,
        wiki_dir,
        packet_payload["request"],
        allow_external_src=allow_external_src,
        read_only=read_only,
        job_request=job_request,
        plan_reporter=plan_reporter,
        source_selection=source_selection,
    )
    live_payload = live_packet.to_payload()
    return _reconcile_packet_views(packet_payload, live_payload)


def _reconcile_packet_views(packet_payload: Mapping[str, Any], live_payload: Mapping[str, Any]) -> ContextPacketReconciliation:
    """Compare validated packet views produced by an official captured read."""
    validation = validate_context_packet(_encode_packet_payload(packet_payload))
    validate_context_packet(_encode_packet_payload(live_payload))
    facets = _reconciliation_facets(packet_payload, live_payload)
    required_states = {name: facets[name]["current"] for name in _RECONCILIATION_FACETS}
    if any(value is False for value in required_states.values()):
        state = "stale"
        current: bool | None = False
    elif any(value is None for value in required_states.values()):
        state = "unevaluated"
        current = None
    else:
        state = "current"
        current = True
    return ContextPacketReconciliation._from_official_read(
        packet_id=validation.packet_id,
        policy=CONTEXT_PACKET_RECONCILIATION_POLICY,
        state=state,
        current=current,
        facets=_freeze_json(facets),
        limitations=tuple(packet_payload["delivery"]["limitations"]),
    )


def _build_protocol_enrichment_from_captured_read(
    captured: CapturedContextRead,
    inventory: dict[str, Any],
    filters: dict[str, Any],
    warnings: list[str],
    *,
    prefer_fresh: bool = False,
    freshness_ranking_out: dict[str, int] | None = None,
) -> dict[str, Any]:
    if not prefer_fresh and not any(
        key in filters for key in ("symbol", "entrypoint", "surface")
    ):
        return {}

    concept_filter_requested = (
        bool(context_service._CONCEPT_FILTER_KEYS & set(filters)) or prefer_fresh
    )
    knowledge_view = captured.knowledge_view if concept_filter_requested else None
    query_surface = context_service._context_query_surface(
        captured.surface_evaluation.payload,
        knowledge_view,
    )
    try:
        query_service = DocumentationGraphQueryService(
            inventory,
            call_edges=list(captured.call_edges),
            flows=list(captured.flows),
            data_flows=list(captured.data_flows),
            dependency_analysis=_thaw_json(captured.dependency_analysis),
            surface_index=query_surface,
            limit=context_service._CONTEXT_QUERY_LIMIT,
            knowledge_view=knowledge_view,
            inventory_result=captured.inventory_result,
            machine_verification=(
                verification_summaries_for_concepts(knowledge_view)
                if isinstance(knowledge_view, KnowledgeReadView)
                else None
            ),
        )
    except DocumentationQueryError as exc:
        raise context_service.ProtocolRequestError(str(exc), "filters") from exc

    enrichment: dict[str, Any] = {}
    graphs: dict[str, Any] = {}
    knowledge_candidates: list[dict[str, Any]] = []
    freshness_rank_by_source = (
        context_service._context_freshness_rank_by_source(
            query_surface,
            query_service,
        )
        if prefer_fresh
        else {}
    )
    if freshness_ranking_out is not None:
        freshness_ranking_out.update(freshness_rank_by_source)
    relationship_filter_requested = bool(
        context_service._RELATIONSHIP_REFINEMENT_KEYS & set(filters)
    )
    if relationship_filter_requested:
        enrichment["typed_graph"] = context_service._compact_typed_graph_status(
            query_service.typed_graph_status
        )
    if "symbol" in filters:
        symbol = filters["symbol"]
        graphs["symbol"] = {
            "callers": query_service.callers(symbol),
            "callees": query_service.callees(symbol),
            "pages": context_service._symbol_pages_payload(
                query_service,
                query_surface,
                symbol,
                filters,
                observed=knowledge_candidates,
            ),
        }
    if "entrypoint" in filters:
        entrypoint = filters["entrypoint"]
        graphs["entrypoint"] = {
            "flow": query_service.flow_for_entrypoint(entrypoint),
            "data_flow": query_service.data_flow_for_entrypoint(entrypoint),
        }
    if graphs:
        enrichment["graphs"] = graphs
    if "surface" in filters:
        enrichment["surface"] = context_service._surface_filter_payload(
            query_surface,
            filters["surface"],
            limit=context_service._CONTEXT_QUERY_LIMIT,
            query_service=query_service,
            filters=filters,
            observed=knowledge_candidates,
        )
    if concept_filter_requested:
        knowledge_status = dict(query_service.knowledge_status)
        enrichment["knowledge"] = knowledge_status
        context_service._append_knowledge_context_warning(
            knowledge_status,
            knowledge_candidates,
            filters,
            warnings,
        )
        if prefer_fresh:
            enrichment["ranking_policy"] = context_service._freshness_ranking_policy(
                knowledge_status,
                freshness_rank_by_source,
            )
    if relationship_filter_requested:
        context_service._append_typed_graph_context_warning(
            query_service.typed_graph_status,
            knowledge_candidates,
            warnings,
        )
    return enrichment


def _normalized_request(request: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(request, Mapping):
        raise context_service.ProtocolRequestError(
            "Request must be a JSON object.",
            "request",
        )
    candidate = deepcopy(dict(request))
    if "protocol" not in candidate:
        candidate["protocol"] = CONTEXT_KNOWLEDGE_PROTOCOL_VERSION
        candidate.setdefault("knowledge_mode", "auto")
    candidate.setdefault("filters", {})
    return context_service._validate_protocol_request(candidate)


def _packet_body(
    captured: CapturedContextRead,
    request: Mapping[str, Any],
    response: Mapping[str, Any],
    packet_contract: _PacketWireContract,
) -> dict[str, Any]:
    basis = _packet_basis(captured, packet_contract, request)
    warnings = list(response.get("warnings", []))
    limitations = _packet_limitations(response, basis)
    delivery = {
        "bounds": deepcopy(response.get("bounds", {})),
        "truncated": bool(response.get("truncated", False)),
        "warnings": warnings,
        "limitations": limitations,
    }
    without_path_policy = {
        "assurance": {
            "level": CONTEXT_PACKET_ASSURANCE_LEVEL,
            "scope": "canonical-packet-content",
        },
        "request": deepcopy(dict(request)),
        "response": deepcopy(dict(response)),
        "basis": basis,
        "delivery": delivery,
    }
    return {
        **without_path_policy,
        "path_policy": _path_policy_receipt(without_path_policy),
    }


def _packet_basis(
    captured: CapturedContextRead,
    packet_contract: _PacketWireContract,
    request: Mapping[str, Any],
) -> dict[str, Any]:
    view = captured.knowledge_view
    source_identity = hash_source_snapshot(
        captured.source_snapshot.to_consumed_inputs()
    )
    repository: dict[str, Any]
    knowledge: dict[str, Any]
    if view.knowledge is None:
        repository = {
            "state": "unavailable",
            "reason": "native-knowledge-envelope-unavailable",
        }
        knowledge = {
            "state": "unavailable",
            "availability": view.availability.value,
            "reason": view.reason_code,
        }
    else:
        record = view.knowledge.bundle.repository
        repository = {
            "state": "recorded",
            "identity": record.identity,
            "evaluated_revision": record.evaluated_revision,
            "working_tree": _wire_value(record.working_tree),
        }
        marker = (
            view.manifest_basis.artifact_hashes
            if view.manifest_basis is not None
            else None
        )
        if marker is None:
            raise ContextPacketUnavailableError(
                "ready native knowledge has no committed envelope identity"
            )
        knowledge = {
            "state": "recorded",
            "availability": view.availability.value,
            "reason": view.reason_code,
            "envelope_hash": marker.evaluated_envelope_hash,
            "knowledge_index_hash": marker.knowledge_index_hash,
            "surface_index_hash": marker.surface_index_hash,
        }
        if marker.governance_hash is not None:
            knowledge["governance_hash"] = marker.governance_hash

    freshness = _freshness_basis(view)
    rejects_selection_basis = (
        packet_contract is _KNOWLEDGE_PACKET_CONTRACT
        and captured.basis_incompatible
        and request.get("knowledge_mode") in {"auto", "required"}
    )
    if rejects_selection_basis:
        knowledge = {
            "state": "unavailable",
            "availability": "degraded",
            "reason": "knowledge-basis-incompatible",
        }
        freshness = {
            "state": "unevaluated",
            "evaluated": False,
            "disclosure": "unevaluated (knowledge basis incompatible)",
            "reason": "knowledge-basis-incompatible",
        }

    return {
        "source_snapshot": {
            "identity": source_identity,
            "input_count": len(captured.source_snapshot.captured_content_hashes),
        },
        "repository": repository,
        "knowledge": knowledge,
        "generator": {
            "component": "agent-wiki-cli",
            "version": __version__,
            "context_protocol": packet_contract.context_protocol,
            "policy_digest": _context_policy_digest(packet_contract.schema_version),
        },
        "freshness": freshness,
    }


def _freshness_basis(view: KnowledgeReadView) -> dict[str, Any]:
    if not view.freshness_evaluated:
        return {
            "state": "unevaluated",
            "evaluated": False,
            "disclosure": knowledge_freshness_disclosure(view),
            "reason": "snapshot-only-read",
        }
    assert view.freshness is not None
    results = [
        {
            "locator": locator,
            "state": result.state.value,
            "reason": result.reason_code,
            "live_comparison_performed": result.live_comparison_performed,
        }
        for locator, result in sorted(view.freshness.by_locator.items())
    ]
    counts = {
        state.value: int(view.freshness.counts[state]) for state in ComputedFreshness
    }
    return {
        "state": "evaluated",
        "evaluated": True,
        "disclosure": knowledge_freshness_disclosure(view),
        "concept_count": len(results),
        "counts": counts,
        "evaluation_digest": _domain_hash(
            _FRESHNESS_DIGEST_DOMAIN,
            {"results": results},
        ),
    }


def _is_free_text_pointer(pointer: tuple[str, ...]) -> bool:
    return pointer[:2] in {
        ("delivery", "warnings"),
        ("response", "warnings"),
    } or pointer[:2] == ("delivery", "limitations")


def _reconciliation_facets(
    packet: Mapping[str, Any],
    live: Mapping[str, Any],
) -> dict[str, dict[str, Any]]:
    packet_basis = packet["basis"]
    live_basis = live["basis"]
    facets: dict[str, dict[str, Any]] = {
        "request": _live_facet(
            packet["request"],
            live["request"],
            mismatch_reason="normalized-request-changed",
        )
    }
    for name, mismatch_reason in (
        ("source_snapshot", "source-snapshot-changed"),
        ("generator", "generator-or-policy-changed"),
    ):
        facets[name] = _live_facet(
            packet_basis[name],
            live_basis[name],
            mismatch_reason=mismatch_reason,
        )

    packet_knowledge = packet_basis["knowledge"]
    live_knowledge = live_basis["knowledge"]
    facets["availability"] = _live_facet(
        {name: packet_knowledge[name] for name in ("state", "availability", "reason")},
        {name: live_knowledge[name] for name in ("state", "availability", "reason")},
        mismatch_reason="knowledge-availability-changed",
    )
    knowledge_recorded = (
        packet_knowledge["state"] == "recorded"
        and live_knowledge["state"] == "recorded"
    )
    facets["knowledge"] = (
        _live_facet(
            packet_knowledge,
            live_knowledge,
            mismatch_reason="knowledge-envelope-changed",
        )
        if knowledge_recorded
        else _unevaluated_facet(
            packet_knowledge == live_knowledge,
            "knowledge-currentness-unavailable-without-recorded-envelope",
        )
    )

    repository_recorded = (
        packet_basis["repository"]["state"] == "recorded"
        and live_basis["repository"]["state"] == "recorded"
    )
    facets["repository"] = (
        _live_facet(
            packet_basis["repository"],
            live_basis["repository"],
            mismatch_reason="repository-envelope-record-changed",
        )
        if repository_recorded
        else _unevaluated_facet(
            packet_basis["repository"] == live_basis["repository"],
            "repository-currentness-unavailable-without-recorded-envelope",
        )
    )

    freshness_evaluated = (
        packet_basis["freshness"]["evaluated"] is True
        and live_basis["freshness"]["evaluated"] is True
    )
    facets["freshness"] = (
        _live_facet(
            packet_basis["freshness"],
            live_basis["freshness"],
            mismatch_reason="freshness-evaluation-changed",
        )
        if freshness_evaluated
        else _unevaluated_facet(
            packet_basis["freshness"] == live_basis["freshness"],
            "freshness-currentness-not-evaluated",
        )
    )
    facets["context_response"] = _live_facet(
        packet["response"],
        live["response"],
        mismatch_reason="context-response-changed",
    )
    facets["delivery"] = _live_facet(
        packet["delivery"],
        live["delivery"],
        mismatch_reason="bounds-warnings-or-limitations-changed",
    )
    facets["path_policy"] = _live_facet(
        packet["path_policy"],
        live["path_policy"],
        mismatch_reason="path-policy-or-classification-changed",
    )
    return facets


def _live_facet(
    expected: Any,
    observed: Any,
    *,
    mismatch_reason: str,
) -> dict[str, Any]:
    matches = expected == observed
    return {
        "matches_expected": matches,
        "current": matches,
        "state": "current" if matches else "stale",
        "reason": ("live-facet-matches-packet" if matches else mismatch_reason),
    }


def _unevaluated_facet(matches: bool, reason: str) -> dict[str, Any]:
    return {
        "matches_expected": matches,
        "current": None,
        "state": "unevaluated",
        "reason": reason,
    }


def _source_anchor(snapshot: SourceSnapshot) -> str:
    return _domain_hash(
        _SOURCE_ANCHOR_DOMAIN,
        _source_snapshot_anchor_payload(snapshot),
    )


def _source_snapshot_anchor_payload(snapshot: SourceSnapshot) -> dict[str, Any]:
    return {
        "all_source_paths": list(snapshot.all_source_paths),
        "gitignore_fingerprint": snapshot.gitignore_fingerprint,
        "captured_content_hashes": dict(snapshot.captured_content_hashes),
        "captured_input_kinds": {
            path: list(kinds) for path, kinds in snapshot.captured_input_kinds.items()
        },
        "language_paths": {
            language: snapshot.language_paths(language)
            for language in sorted(snapshot.files_by_language)
        },
        "unsupported_language_paths": {
            language: snapshot.unsupported_language_paths(language)
            for language in sorted(snapshot.unsupported_files_by_language)
        },
        "dockerfile_paths": [item.rel_path for item in snapshot.dockerfile_candidates],
        "compose_paths": [item.rel_path for item in snapshot.compose_candidates],
        "yaml_paths": [item.rel_path for item in snapshot.yaml_candidates],
        "package_marker_paths": [item.rel_path for item in snapshot.package_markers],
    }


def _assert_source_unchanged(snapshot: SourceSnapshot, expected_anchor: str, *, metrics: dict[str, int] | None = None) -> None:
    try:
        unchanged = (
            _source_anchor(snapshot) == expected_anchor
            and source_snapshot_matches_current_files(snapshot, **({"metrics": metrics} if metrics is not None else {}))
        )
    except (OSError, SourceSnapshotError, ValueError) as exc:
        raise ContextPacketSourceMutationError("source") from exc
    if not unchanged:
        raise ContextPacketSourceMutationError("source")


def confirmed_missing_source_paths(snapshot: SourceSnapshot, requested_paths: Iterable[str]) -> frozenset[str]:
    """Adapt the shared source owner's guarded requested-absence observation."""
    from .source_snapshot import confirmed_missing_source_paths as confirm_missing

    try:
        return confirm_missing(snapshot, requested_paths)
    except SourceSnapshotMutationError as exc:
        raise ContextPacketSourceMutationError("source") from exc
    except SourceSnapshotError as exc:
        raise ContextPacketPathPolicyError("source_path", str(exc)) from exc


def _assert_source_inputs_unchanged(
    snapshot: SourceSnapshot,
    expected_anchor: str,
) -> None:
    try:
        unchanged = (
            _source_anchor(snapshot) == expected_anchor
            and source_snapshot_inputs_match_current_files(snapshot)
        )
    except (OSError, SourceSnapshotError, ValueError) as exc:
        raise ContextPacketSourceMutationError("source") from exc
    if not unchanged:
        raise ContextPacketSourceMutationError("source")


def _assert_selection_unchanged(captured: CapturedContextRead) -> None:
    if captured.explicit_changes:
        from .change_selection import select_changes

        if captured.change_selection is None:
            raise ContextPacketSourceMutationError("source-selection")
        request = {
            key: value
            for key, value in captured.change_selection["request"].items()
            if key not in {"commits", "index_id"}
        }
        try:
            current_selection = select_changes(
                captured.source_root, request, snapshot=captured.source_snapshot
            )
        except ValueError as exc:
            raise ContextPacketSourceMutationError("source-selection") from exc
        if current_selection != captured.change_selection:
            raise ContextPacketSourceMutationError("source-selection")
        return
    changed = context_service._selected_git_changed_files(
        str(captured.source_root),
        captured.source_snapshot,
    )
    current = None if changed is None else tuple(changed)
    if current != captured.changed_files:
        raise ContextPacketSourceMutationError("source-selection")


def _wiki_anchor(root: Path, *, reject_all_symlinks: bool = False, max_bytes: int | None = None,
                 metrics: dict[str, int] | None = None,
                 integrity_out: dict[str, tuple[int, ...]] | None = None,
                 guard_windows: bool = False) -> str:
    if integrity_out is not None:
        current = root
        while True:
            integrity_out[str(current)] = directory_identity(current)
            if current.exists() or current.parent == current:
                break
            current = current.parent
    if not root.exists():
        return _domain_hash(_WIKI_ANCHOR_DOMAIN, {"state": "absent"})
    records: list[dict[str, str]] = []
    lock_root = _governance_lock_root(root)
    operational_locks = {
        lock_root / GOVERNANCE_LOCK_FILENAME,
        lock_root / DEFAULT_LAYOUT.storage_lock,
    }
    used_bytes = 0
    inspected_entries = 0

    def walk(directory: Path, relative: Path) -> None:
        nonlocal used_bytes, inspected_entries
        if integrity_out is not None:
            integrity_out[str(directory)] = directory_identity(directory)
        try:
            entries = []
            with os.scandir(directory) as scan:
                for entry in scan:
                    inspected_entries += 1
                    if max_bytes is not None and inspected_entries > 10_000:
                        raise ContextPacketUnavailableError("wiki discovery exceeds the entry limit", field="max_wiki_entries")
                    entries.append(entry)
            entries.sort(key=lambda entry: (entry.name.casefold(), entry.name))
        except OSError as exc:
            raise ContextPacketSourceMutationError("wiki") from exc
        for entry in entries:
            rel_path = (relative / entry.name).as_posix()
            try:
                if Path(entry.path).absolute() in operational_locks:
                    # Mutation locks are operational state, not wiki content.
                    # Windows byte locks prohibit reading them through another
                    # handle while adoption owns the mutation transaction.
                    # DirEntry metadata omits Windows link counts; stat the path freshly.
                    metadata = fresh_no_follow_stat(entry.path)
                    if (first_unsafe_path_component(Path(entry.path)) is not None
                            or not stat.S_ISREG(metadata.st_mode)
                            or metadata.st_nlink != 1):
                        raise ContextPacketPathPolicyError(
                            "wiki_dir", "wiki mutation locks must be single regular files",
                            relative_path=rel_path,
                        )
                    records.append({"path": rel_path, "kind": "operational-lock"})
                    if integrity_out is not None:
                        integrity_out[str(Path(entry.path))] = directory_identity(Path(entry.path))
                elif entry.is_symlink():
                    if reject_all_symlinks or _wiki_symlink_is_captured_input(rel_path):
                        raise ContextPacketPathPolicyError(
                            "wiki_dir",
                            "wiki symlinks are not permitted for qualified context "
                            f"reads: {rel_path!r}",
                            relative_path=rel_path,
                        )
                    target = os.readlink(entry.path)
                    records.append(
                        {
                            "path": rel_path,
                            "kind": "symlink",
                            "content_hash": sha256_bytes(
                                target.encode("utf-8", "surrogateescape")
                            ),
                        }
                    )
                elif entry.is_dir(follow_symlinks=False):
                    records.append({"path": rel_path, "kind": "directory"})
                    walk(Path(entry.path), relative / entry.name)
                elif entry.is_file(follow_symlinks=False):
                    if guard_windows:
                        _guard_windows_inputs(root, [rel_path])
                    before = directory_identity(Path(entry.path)) if integrity_out is not None else None
                    if max_bytes is not None and entry.stat(follow_symlinks=False).st_size > max_bytes - used_bytes:
                        raise ContextPacketUnavailableError("wiki capture exceeds the byte limit", field="max_wiki_bytes")
                    with Path(entry.path).open("rb") as stream:
                        content = stream.read() if max_bytes is None else stream.read(max_bytes - used_bytes + 1)
                    if integrity_out is not None:
                        after = directory_identity(Path(entry.path))
                        if before != after:
                            raise ContextPacketSourceMutationError("wiki")
                        integrity_out[str(Path(entry.path))] = after
                    used_bytes += len(content)
                    if metrics is not None:
                        metrics["files"] = metrics.get("files", 0) + 1
                        metrics["bytes"] = metrics.get("bytes", 0) + len(content)
                    if max_bytes is not None and used_bytes > max_bytes:
                        raise ContextPacketUnavailableError("wiki capture exceeds the byte limit", field="max_wiki_bytes")
                    records.append(
                        {
                            "path": rel_path,
                            "kind": "file",
                            "content_hash": sha256_bytes(content),
                        }
                    )
                else:
                    records.append({"path": rel_path, "kind": "special"})
            except OSError as exc:
                raise ContextPacketSourceMutationError("wiki") from exc

    walk(root, Path())
    if integrity_out is not None:
        _assert_wiki_integrity(integrity_out)
    return _domain_hash(_WIKI_ANCHOR_DOMAIN, {"state": "present", "entries": records})


def _assert_wiki_integrity(expected: Mapping[str, tuple[int, ...]]) -> None:
    if any(directory_identity(Path(path)) != tuple(identity) for path, identity in expected.items()):
        raise ContextPacketSourceMutationError("wiki")


def _wiki_symlink_is_captured_input(relative_path: str) -> bool:
    if relative_path in {
        DEFAULT_LAYOUT.governance,
        DEFAULT_LAYOUT.knowledge_index,
        DEFAULT_LAYOUT.manifest,
        DEFAULT_LAYOUT.surface_index,
    }:
        return True
    try:
        wiki_surface.validate_exact_page_coordinate(relative_path)
    except wiki_surface.WikiSurfaceError:
        return False
    return True


def _assert_wiki_unchanged(
    root: Path,
    expected_anchor: str,
    *,
    reject_all_symlinks: bool = False,
    max_bytes: int | None = None,
    metrics: dict[str, int] | None = None,
    expected_integrity: Mapping[str, tuple[int, ...]] | None = None,
) -> None:
    if expected_integrity is not None:
        _assert_wiki_integrity(expected_integrity)
    options: dict[str, Any] = {}
    if max_bytes is not None:
        options["max_bytes"] = max_bytes
    if metrics is not None:
        options["metrics"] = metrics
    try:
        current_anchor = (
            _wiki_anchor(root, reject_all_symlinks=True, **options)
            if reject_all_symlinks
            else _wiki_anchor(root)
        )
    except ContextPacketPathPolicyError as exc:
        raise ContextPacketSourceMutationError("wiki") from exc
    if current_anchor != expected_anchor:
        raise ContextPacketSourceMutationError("wiki")


def _wire_value(value: Any) -> Any:
    return value.value if isinstance(value, Enum) else value


__all__ = [
    "CONTEXT_PACKET_RECONCILIATION_POLICY",
    "CapturedContextRead",
    "ContextBasisComparison",
    "ContextPacketAuthorityError",
    "ContextPacketReconciliation",
    "ContextPacketSourceMutationError",
    "ContextPacketUnavailableError",
    "build_context_from_captured_read",
    "build_qualified_context",
    "capture_context_read",
    "compare_context_packet_basis",
    "confirmed_missing_source_paths",
    "describe_context_packet_error",
    "packet_from_captured_response",
    "reconcile_context_packet",
]
