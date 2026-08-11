"""Canonical Qualified Context Packet construction and verification.

The packet builder coordinates one source inventory, one wiki surface
evaluation, and one native-knowledge read view.  Context response construction
then consumes only those captured values.  Optimistic source and wiki anchors
are checked before the canonical bytes are returned, so a mutation cannot
silently detach the response from its declared basis.

This module is deliberately provider- and persistence-free.  It returns bytes
in memory, never refreshes native artifacts, and keeps structural validation
separate from live reconciliation.
"""

from __future__ import annotations

import json
import math
import os
import re
from urllib.parse import urlsplit
from collections.abc import Callable, Mapping, Sequence
from copy import deepcopy
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from types import MappingProxyType
from typing import Any

from .. import __version__
from ..config import DEFAULT_WIKI_DIR, PathValidationError, validate_path
from . import context_service, wiki_surface
from .contracts import (
    CONTEXT_KNOWLEDGE_PROTOCOL_VERSION,
    QUALIFIED_CONTEXT_PACKET_KNOWLEDGE_SCHEMA_VERSION,
    QUALIFIED_CONTEXT_PACKET_SCHEMA_VERSION,
    TYPED_GRAPH_SCHEMA_VERSION,
)
from .dependencies import analyze_dependencies
from .documentation_queries import (
    CONTEXT_COVERAGE_LIMITATION_CODE_MAX_LENGTH,
    CONTEXT_COVERAGE_LIMITATION_LIMIT,
    DocumentationGraphQueryService,
    DocumentationQueryError,
    knowledge_view_selection_eligible,
)
from .documentation_query_builder import validate_live_query_source_selection
from .extraction_jobs import ExtractionJobPlan, ExtractionJobRequest
from .extraction_service import InventoryResult
from .knowledge_consumption import KnowledgeReadView
from .knowledge_evidence import (
    canonical_json_bytes,
    is_valid_sha256,
    sha256_bytes,
)
from .knowledge_envelope import (
    KnowledgeEnvelopeError,
    hash_source_snapshot,
    validate_configured_public_identity,
)
from .knowledge_freshness import (
    KNOWN_FRESHNESS_REASON_CODES,
    REASON_RECORDED_BASIS_MATCHES_LIVE_EVALUATION,
)
from .knowledge_graph import (
    CORE_RELATIONSHIP_KINDS,
    ENDPOINT_KINDS,
    GRAPH_COVERAGE_ANALYZERS,
    GRAPH_EVIDENCE_STATES,
    GRAPH_ORIGINS,
    GRAPH_RESOLUTIONS,
    is_supported_relationship_kind,
)
from .knowledge_model import (
    ComputedFreshness,
    ConceptKind,
    EvidenceState,
    Lifecycle,
    Origin,
    Resolution,
    TargetClass,
    Verification,
    concept_kind_for_page_kind,
)
from .wiki_media import contains_uri_authority_userinfo
from .knowledge_observability import knowledge_freshness_disclosure
from .knowledge_verification import verification_summaries_for_concepts
from .plugins import runtime_plugin_fallback_root
from .source_snapshot import (
    SourceSnapshot,
    SourceSnapshotError,
    build_source_snapshot,
    capture_source_selection_inputs,
    source_snapshot_inputs_match_current_files,
    source_snapshot_matches_current_files,
)
from .validation import require_repository_relative_path
from .wiki_surface_index import SurfaceIndexEvaluation, evaluate_surface_index


CONTEXT_PACKET_SCHEMA_VERSION = QUALIFIED_CONTEXT_PACKET_SCHEMA_VERSION
CONTEXT_PACKET_KNOWLEDGE_SCHEMA_VERSION = (
    QUALIFIED_CONTEXT_PACKET_KNOWLEDGE_SCHEMA_VERSION
)
CONTEXT_PACKET_ASSURANCE_LEVEL = "content-integrity"
CONTEXT_PACKET_POLICY_VERSION = "qualified-context-policy-v1"
CONTEXT_PACKET_KNOWLEDGE_POLICY_VERSION = "qualified-context-policy-v2"
CONTEXT_PACKET_PATH_POLICY_VERSION = "qualified-context-path-policy-v1"
CONTEXT_PACKET_RECONCILIATION_POLICY = "qualified-context-complete-policy-v1"

_PACKET_DIGEST_DOMAIN = b"llm-wiki-qualified-context-packet/v1\x00"
_KNOWLEDGE_PACKET_DIGEST_DOMAIN = b"llm-wiki-qualified-context-packet/v2\x00"
_POLICY_DIGEST_DOMAIN = "llm-wiki/qualified-context-policy/v1"
_KNOWLEDGE_POLICY_DIGEST_DOMAIN = "llm-wiki/qualified-context-policy/v2"
_PATH_POLICY_DIGEST_DOMAIN = "llm-wiki/qualified-context-path-policy/v1"
_SOURCE_ANCHOR_DOMAIN = "llm-wiki/qualified-context-source-anchor/v1"
_WIKI_ANCHOR_DOMAIN = "llm-wiki/qualified-context-wiki-anchor/v1"
_FRESHNESS_DIGEST_DOMAIN = "llm-wiki/qualified-context-freshness/v1"

_MAX_PACKET_BYTES = 16 * 1024 * 1024
_MAX_JSON_DEPTH = 64
_MAX_JSON_ITEMS = 250_000
_MAX_TEXT_LENGTH = 2 * 1024 * 1024
_MAX_NORMALIZED_CONTEXT_TARGET_LENGTH = 2048
_MAX_KNOWLEDGE_CONCEPTS = context_service.CONTEXT_KNOWLEDGE_CONCEPT_LIMIT
_MAX_KNOWLEDGE_PAGES = context_service.CONTEXT_KNOWLEDGE_PAGE_LIMIT
_MAX_KNOWLEDGE_RELATIONSHIPS = context_service.CONTEXT_KNOWLEDGE_RELATIONSHIP_LIMIT
_MAX_KNOWLEDGE_PACKET_BYTES = 2 * 1024 * 1024
_LIMITATION_RE = re.compile(r"^[a-z][a-z0-9]*(?:-[a-z0-9]+)*$")
_COVERAGE_LIMITATION_RE = re.compile(r"^[a-z][a-z0-9]*(?:[/-][a-z0-9]+)*$")
_PORTABLE_URI_RE = re.compile(r"^[A-Za-z][A-Za-z0-9+.-]*:[^\x00-\x20]*$")
_RFC3986_URI_RE = re.compile(r"^[A-Za-z0-9._~:/?#\[\]@!$&'()*+,;=%-]+$")
_WINDOWS_ABSOLUTE_RE = re.compile(r"^[A-Za-z]:[\\/]")
_STRUCTURAL_PATH_FIELDS = frozenset(
    {
        "canonical_path",
        "file",
        "source_path",
    }
)
_PUBLIC_URI_FIELDS = frozenset({"mcp_uri"})
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
_PATH_COUNT_KEYS = (
    "free_text_values",
    "opaque_values",
    "portable_identities",
    "public_uris",
    "repository_relative_paths",
)
_PACKET_TOP_LEVEL_FIELDS = frozenset(
    {
        "schema_version",
        "packet_id",
        "assurance",
        "request",
        "response",
        "basis",
        "delivery",
        "path_policy",
    }
)


@dataclass(frozen=True)
class _PacketWireContract:
    """One immutable schema/protocol/policy binding for canonical packets."""

    schema_version: str
    context_protocol: str
    policy_version: str
    packet_digest_domain: bytes
    policy_digest_domain: str
    max_packet_bytes: int
    knowledge_mode_required: bool
    knowledge_concept_limit: int | None
    knowledge_page_limit: int | None
    knowledge_relationship_limit: int | None


_LEGACY_PACKET_CONTRACT = _PacketWireContract(
    schema_version=CONTEXT_PACKET_SCHEMA_VERSION,
    context_protocol=context_service.PROTOCOL_VERSION,
    policy_version=CONTEXT_PACKET_POLICY_VERSION,
    packet_digest_domain=_PACKET_DIGEST_DOMAIN,
    policy_digest_domain=_POLICY_DIGEST_DOMAIN,
    max_packet_bytes=_MAX_PACKET_BYTES,
    knowledge_mode_required=False,
    knowledge_concept_limit=None,
    knowledge_page_limit=None,
    knowledge_relationship_limit=None,
)
_KNOWLEDGE_PACKET_CONTRACT = _PacketWireContract(
    schema_version=CONTEXT_PACKET_KNOWLEDGE_SCHEMA_VERSION,
    context_protocol=CONTEXT_KNOWLEDGE_PROTOCOL_VERSION,
    policy_version=CONTEXT_PACKET_KNOWLEDGE_POLICY_VERSION,
    packet_digest_domain=_KNOWLEDGE_PACKET_DIGEST_DOMAIN,
    policy_digest_domain=_KNOWLEDGE_POLICY_DIGEST_DOMAIN,
    max_packet_bytes=_MAX_KNOWLEDGE_PACKET_BYTES,
    knowledge_mode_required=True,
    knowledge_concept_limit=_MAX_KNOWLEDGE_CONCEPTS,
    knowledge_page_limit=_MAX_KNOWLEDGE_PAGES,
    knowledge_relationship_limit=_MAX_KNOWLEDGE_RELATIONSHIPS,
)
_PACKET_CONTRACT_BY_SCHEMA = MappingProxyType(
    {
        contract.schema_version: contract
        for contract in (_LEGACY_PACKET_CONTRACT, _KNOWLEDGE_PACKET_CONTRACT)
    }
)


class ContextPacketError(ValueError):
    """Base failure for context-packet construction and consumption."""

    code = "context-packet-error"


class ContextPacketMalformedError(ContextPacketError):
    """The supplied bytes do not satisfy the canonical packet contract."""

    code = "malformed-context-packet"

    def __init__(self, field: str, message: str):
        self.field = field
        self.message = message
        super().__init__(f"{field}: {message}")


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


class ContextPacketPathPolicyError(ContextPacketError):
    """A structural packet field violates its declared path policy."""

    code = "context-packet-path-policy-rejected"

    def __init__(self, field: str, message: str):
        self.field = field
        self.message = message
        super().__init__(f"{field}: {message}")


def _packet_contract_for_schema(schema_version: object) -> _PacketWireContract:
    if not isinstance(schema_version, str):
        raise ContextPacketMalformedError(
            "schema_version",
            "must be a supported qualified-context packet schema identifier",
        )
    contract = _PACKET_CONTRACT_BY_SCHEMA.get(schema_version)
    if contract is None:
        raise ContextPacketMalformedError(
            "schema_version",
            f"unsupported qualified-context packet schema: {schema_version!r}",
        )
    return contract


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
class QualifiedContextPacket:
    """Immutable canonical packet bytes plus safe value accessors."""

    _canonical_bytes: bytes
    _payload: Mapping[str, Any]

    @classmethod
    def _from_validated_payload(
        cls,
        payload: Mapping[str, Any],
        canonical_bytes: bytes,
    ) -> QualifiedContextPacket:
        return cls(
            _canonical_bytes=bytes(canonical_bytes),
            _payload=_freeze_json(payload),
        )

    @property
    def packet_id(self) -> str:
        return str(self._payload["packet_id"])

    @property
    def canonical_bytes(self) -> bytes:
        return self._canonical_bytes

    def to_bytes(self) -> bytes:
        """Return the exact canonical packet bytes."""

        return self._canonical_bytes

    def to_payload(self) -> dict[str, Any]:
        """Return a mutable JSON-compatible copy of the packet payload."""

        return _thaw_json(self._payload)


@dataclass(frozen=True)
class ContextPacketValidation:
    """Successful structural validation with explicitly unevaluated freshness."""

    packet: QualifiedContextPacket
    schema: str = "valid"
    canonical: str = "valid"
    digest: str = "valid"
    path_policy: str = "valid"
    lineage: str = "valid"
    freshness_evaluated: bool = False
    freshness: str = "unevaluated"
    freshness_reason: str = "structural-validation-has-no-live-basis"

    @property
    def valid(self) -> bool:
        return True

    @property
    def packet_id(self) -> str:
        return self.packet.packet_id

    def to_payload(self) -> dict[str, Any]:
        return {
            "valid": True,
            "packet_id": self.packet_id,
            "schema": {"state": self.schema},
            "canonical": {"state": self.canonical},
            "digest": {"state": self.digest},
            "path_policy": {"state": self.path_policy},
            "lineage": {"state": self.lineage},
            "availability": {
                "state": "declared",
                "value": self.packet.to_payload()["basis"]["knowledge"]["availability"],
            },
            "freshness": {
                "state": self.freshness,
                "evaluated": self.freshness_evaluated,
                "reason": self.freshness_reason,
            },
        }


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
) -> CapturedContextRead:
    """Capture one source inventory, wiki surface, and knowledge read view.

    The function is read-only.  It brackets wiki reads with a content anchor
    and validates the source snapshot after extraction, rejecting an
    inconsistent capture rather than returning a partially detached view.
    """

    if not isinstance(read_only, bool):
        raise TypeError("read_only must be a boolean")
    if plan_reporter is not None and not callable(plan_reporter):
        raise TypeError("plan_reporter must be callable or None")
    if not isinstance(allow_selection_mismatch, bool):
        raise TypeError("allow_selection_mismatch must be a boolean")
    if not isinstance(strict_wiki_symlinks, bool):
        raise TypeError("strict_wiki_symlinks must be a boolean")

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

    try:
        selection_policy = context_service.resolve_source_selection(
            source_root,
            source_selection,
        )
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
    source_snapshot = build_source_snapshot(
        source_root,
        source_selection=source_selection,
        selection_policy=selection_policy,
        expected_selection_inputs=selection_inputs,
    )

    collected = context_service.get_inventory(
        str(source_root),
        deep=True,
        return_result=True,
        job_request=job_request,
        plan_reporter=plan_reporter,
        include_plugins=False,
        source_selection=source_selection,
        source_snapshot=source_snapshot,
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
    wiki_anchor_before = (
        _wiki_anchor(wiki_root, reject_all_symlinks=True)
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
        call_edges = tuple(
            context_service.resolve_call_edges(inventory) if entrypoints else ()
        )
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

    _assert_wiki_unchanged(
        wiki_root,
        wiki_anchor_before,
        reject_all_symlinks=strict_wiki_symlinks,
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
    return CapturedContextRead(
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
    )


def build_context_from_captured_read(
    captured: CapturedContextRead,
    request: Mapping[str, Any],
) -> tuple[dict[str, Any], list[str]]:
    """Build a versioned context payload solely from one captured read."""

    if not isinstance(captured, CapturedContextRead):
        raise TypeError("captured must be a CapturedContextRead")
    normalized = _normalized_request(request)
    if normalized["protocol"] == context_service.PROTOCOL_VERSION:
        return _build_legacy_context_from_captured_read(captured, normalized)
    return _build_knowledge_context_from_captured_read(captured, normalized)


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
        elif not captured.changed_files:
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
    body = _packet_body(captured, normalized, response, packet_contract)

    _assert_source_unchanged(captured.source_snapshot, captured.source_anchor)
    _assert_wiki_unchanged(
        captured.wiki_root,
        captured.wiki_anchor,
        reject_all_symlinks=captured.strict_wiki_symlinks,
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


def validate_context_packet(
    packet_bytes: bytes | bytearray | memoryview,
) -> ContextPacketValidation:
    """Strictly validate canonical bytes without performing live reads."""

    raw = _coerce_packet_bytes(packet_bytes)
    payload = _strict_json_payload(raw)
    packet_contract = _packet_contract_for_schema(payload.get("schema_version"))
    if len(raw) > packet_contract.max_packet_bytes:
        raise ContextPacketMalformedError(
            "packet_bytes",
            f"must not exceed {packet_contract.max_packet_bytes} bytes for "
            f"{packet_contract.schema_version!r}",
        )
    _validate_packet_shape(payload, packet_contract)
    canonical = _encode_packet_payload(payload)
    if canonical != raw:
        raise ContextPacketMalformedError(
            "packet_bytes",
            "must use the canonical sorted-key UTF-8 JSON encoding with one LF",
        )

    packet_id = payload["packet_id"]
    semantic_body = {key: value for key, value in payload.items() if key != "packet_id"}
    expected_id = _packet_id(semantic_body)
    if packet_id != expected_id:
        raise ContextPacketMalformedError(
            "packet_id",
            "does not match the domain-separated canonical semantic body",
        )

    declared_receipt = payload["path_policy"]
    policy_input = {
        key: value
        for key, value in payload.items()
        if key not in {"schema_version", "packet_id", "path_policy"}
    }
    expected_receipt = _path_policy_receipt(policy_input)
    if declared_receipt != expected_receipt:
        raise ContextPacketPathPolicyError(
            "path_policy",
            "does not match the packet's classified structural fields",
        )

    packet = QualifiedContextPacket._from_validated_payload(payload, canonical)
    return ContextPacketValidation(packet=packet)


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
    candidate.setdefault(
        "protocol",
        (
            CONTEXT_KNOWLEDGE_PROTOCOL_VERSION
            if "knowledge_mode" in candidate
            else context_service.PROTOCOL_VERSION
        ),
    )
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


def _packet_limitations(
    response: Mapping[str, Any],
    basis: Mapping[str, Any],
) -> list[str]:
    limitations: set[str] = set()
    if response.get("truncated") is True:
        limitations.add("context-truncated")
    response_knowledge = response.get("knowledge")
    if isinstance(response_knowledge, Mapping):
        bounds = response_knowledge.get("bounds")
        if isinstance(bounds, Mapping) and any(
            isinstance(item, Mapping) and item.get("truncated") is True
            for item in bounds.values()
        ):
            limitations.add("knowledge-results-truncated")
        response_availability = response_knowledge.get("availability")
        if response_availability in {"absent", "degraded", "unsupported"}:
            limitations.add(f"knowledge-{response_availability}")
        if response_knowledge.get("reason") == "knowledge-result-exceeds-size-limit":
            limitations.add("knowledge-result-exceeds-size-limit")
    freshness = basis["freshness"]
    if freshness["evaluated"] is False:
        limitations.add("freshness-not-evaluated")
    knowledge = basis["knowledge"]
    if knowledge["state"] == "unavailable":
        availability = knowledge["availability"]
        if availability in {"absent", "degraded", "unsupported"}:
            limitations.add(f"knowledge-{availability}")
    return sorted(limitations)


def _context_policy_digest(
    schema_version: str = CONTEXT_PACKET_SCHEMA_VERSION,
) -> str:
    packet_contract = _packet_contract_for_schema(schema_version)
    if packet_contract is _LEGACY_PACKET_CONTRACT:
        # This exact input is the frozen v1 byte-compatibility contract.
        return _domain_hash(
            _POLICY_DIGEST_DOMAIN,
            {
                "policy_version": CONTEXT_PACKET_POLICY_VERSION,
                "packet_schema": CONTEXT_PACKET_SCHEMA_VERSION,
                "context_protocol": context_service.PROTOCOL_VERSION,
                "context_query_limit": context_service._CONTEXT_QUERY_LIMIT,
                "assurance": CONTEXT_PACKET_ASSURANCE_LEVEL,
                "path_policy": CONTEXT_PACKET_PATH_POLICY_VERSION,
                "prefer_fresh_supported": True,
            },
        )
    return _domain_hash(
        packet_contract.policy_digest_domain,
        {
            "policy_version": packet_contract.policy_version,
            "packet_schema": packet_contract.schema_version,
            "context_protocol": packet_contract.context_protocol,
            "context_query_limit": context_service._CONTEXT_QUERY_LIMIT,
            "max_packet_bytes": packet_contract.max_packet_bytes,
            "knowledge_concept_limit": packet_contract.knowledge_concept_limit,
            "knowledge_page_limit": packet_contract.knowledge_page_limit,
            "knowledge_relationship_limit": (
                packet_contract.knowledge_relationship_limit
            ),
            "coverage_limitation_limit": CONTEXT_COVERAGE_LIMITATION_LIMIT,
            "coverage_limitation_code_max_length": (
                CONTEXT_COVERAGE_LIMITATION_CODE_MAX_LENGTH
            ),
            "oversize_selection_policy": (
                "tail-reduce-relationships-pages-concepts-then-fallback"
            ),
            "source_priority_binding": "response-source-priorities-v1",
            "assurance": CONTEXT_PACKET_ASSURANCE_LEVEL,
            "path_policy": CONTEXT_PACKET_PATH_POLICY_VERSION,
            "prefer_fresh_supported": True,
            "knowledge_modes": ["off", "auto", "required"],
            "raw_evidence_default": "omitted",
        },
    )


def _path_policy_digest() -> str:
    return _domain_hash(
        _PATH_POLICY_DIGEST_DOMAIN,
        {
            "policy_version": CONTEXT_PACKET_PATH_POLICY_VERSION,
            "classes": list(_PATH_COUNT_KEYS),
            "structural_path_fields": sorted(_STRUCTURAL_PATH_FIELDS),
            "public_uri_fields": sorted(_PUBLIC_URI_FIELDS),
            "opaque_source_rule": "slash-like-content-is-not-a-path-finding",
        },
    )


def _path_policy_receipt(value: Mapping[str, Any]) -> dict[str, Any]:
    counts = {name: 0 for name in _PATH_COUNT_KEYS}
    accepted = 0

    def visit(item: Any, pointer: tuple[str, ...]) -> None:
        nonlocal accepted
        if isinstance(item, Mapping):
            for key, child in item.items():
                if not isinstance(key, str):
                    raise ContextPacketPathPolicyError(
                        _pointer(pointer),
                        "JSON object keys must be strings",
                    )
                if _mapping_key_is_repository_path(pointer):
                    _repository_path(key, _pointer((*pointer, key)))
                    counts["repository_relative_paths"] += 1
                    accepted += 1
                visit(child, (*pointer, key))
            return
        if isinstance(item, (list, tuple)):
            for index, child in enumerate(item):
                if _list_item_is_repository_path(pointer):
                    _repository_path(child, _pointer((*pointer, str(index))))
                    counts["repository_relative_paths"] += 1
                    accepted += 1
                else:
                    visit(child, (*pointer, str(index)))
            return
        if not isinstance(item, str):
            return
        field = pointer[-1] if pointer else ""
        if field in _STRUCTURAL_PATH_FIELDS:
            _repository_path(item, _pointer(pointer))
            counts["repository_relative_paths"] += 1
        elif field in _PUBLIC_URI_FIELDS:
            if _PORTABLE_URI_RE.fullmatch(item) is None or item.casefold().startswith(
                "file:"
            ):
                raise ContextPacketPathPolicyError(
                    _pointer(pointer),
                    "must be a portable non-file URI",
                )
            counts["public_uris"] += 1
        elif pointer == ("basis", "repository", "identity"):
            if item != "unknown":
                try:
                    validate_configured_public_identity(item)
                except KnowledgeEnvelopeError as exc:
                    raise ContextPacketPathPolicyError(
                        _pointer(pointer),
                        "must be a normalized portable repository identity",
                    ) from exc
            counts["portable_identities"] += 1
        elif _is_free_text_pointer(pointer):
            counts["free_text_values"] += 1
        else:
            counts["opaque_values"] += 1
        accepted += 1

    visit(value, ())
    return {
        "policy_version": CONTEXT_PACKET_PATH_POLICY_VERSION,
        "policy_digest": _path_policy_digest(),
        "field_counts": counts,
        "finding_counts": {
            "accepted": accepted,
            "redacted": 0,
            "rejected": 0,
        },
        "quarantined": False,
        "final_scan": "passed",
        "limitations": ["does-not-establish-absence-of-arbitrary-sensitive-content"],
    }


def _mapping_key_is_repository_path(pointer: tuple[str, ...]) -> bool:
    return pointer in {
        ("response", "files"),
        ("response", "downgraded_files"),
        ("response", "source_priorities"),
    }


def _list_item_is_repository_path(pointer: tuple[str, ...]) -> bool:
    return pointer == ("response", "omitted_files")


def _is_free_text_pointer(pointer: tuple[str, ...]) -> bool:
    return pointer[:2] in {
        ("delivery", "warnings"),
        ("response", "warnings"),
    } or pointer[:2] == ("delivery", "limitations")


def _repository_path(value: object, field: str) -> str:
    error = ContextPacketPathPolicyError(
        field,
        "must be a normalized repository-relative POSIX path",
    )
    _reject_machine_local_path(value, error)
    return require_repository_relative_path(
        value,
        text_error=error,
        posix_error=error,
        normalized_error=error,
    )


def _reject_machine_local_path(
    value: object,
    error: ContextPacketPathPolicyError,
) -> None:
    if isinstance(value, str) and (
        value.startswith(("/", "\\", "~"))
        or _WINDOWS_ABSOLUTE_RE.match(value)
        or value.casefold().startswith("file:")
    ):
        raise error


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


def _packet_id(body: Mapping[str, Any]) -> str:
    packet_contract = _packet_contract_for_schema(body.get("schema_version"))
    return sha256_bytes(
        packet_contract.packet_digest_domain + canonical_json_bytes(body)
    )


def _encode_packet_payload(payload: Mapping[str, Any]) -> bytes:
    try:
        _validate_json_tree(payload)
        return canonical_json_bytes(payload) + b"\n"
    except ContextPacketMalformedError:
        raise
    except (RecursionError, TypeError, UnicodeEncodeError, ValueError) as exc:
        raise ContextPacketMalformedError(
            "packet",
            "must contain finite canonical JSON values",
        ) from exc


def _coerce_packet_bytes(
    value: bytes | bytearray | memoryview,
) -> bytes:
    if isinstance(value, bytes):
        raw = value
    elif isinstance(value, (bytearray, memoryview)):
        raw = bytes(value)
    else:
        raise TypeError("packet_bytes must be bytes-like")
    if not raw:
        raise ContextPacketMalformedError("packet_bytes", "must not be empty")
    if len(raw) > _MAX_PACKET_BYTES:
        raise ContextPacketMalformedError(
            "packet_bytes",
            f"must not exceed {_MAX_PACKET_BYTES} bytes",
        )
    if raw.startswith(b"\xef\xbb\xbf"):
        raise ContextPacketMalformedError(
            "packet_bytes",
            "must not contain a UTF-8 byte-order mark",
        )
    if not raw.endswith(b"\n") or raw.endswith(b"\n\n") or b"\r" in raw:
        raise ContextPacketMalformedError(
            "packet_bytes",
            "must end in exactly one LF and contain no carriage returns",
        )
    return raw


def _strict_json_payload(raw: bytes) -> dict[str, Any]:
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ContextPacketMalformedError(
            "packet_bytes",
            "must be valid UTF-8",
        ) from exc

    def reject_constant(value: str) -> None:
        raise ContextPacketMalformedError(
            "packet",
            f"non-finite JSON number {value!r} is not supported",
        )

    def strict_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                raise ContextPacketMalformedError(
                    "packet",
                    f"contains duplicate object key {key!r}",
                )
            result[key] = value
        return result

    try:
        decoded = json.loads(
            text,
            object_pairs_hook=strict_object,
            parse_constant=reject_constant,
        )
    except ContextPacketMalformedError:
        raise
    except (json.JSONDecodeError, RecursionError, UnicodeError, ValueError) as exc:
        raise ContextPacketMalformedError(
            "packet_bytes",
            "must contain exactly one valid JSON object",
        ) from exc
    if not isinstance(decoded, dict):
        raise ContextPacketMalformedError("packet", "must be a JSON object")
    _validate_json_tree(decoded)
    return decoded


def _validate_json_tree(value: Any) -> None:
    active: set[int] = set()
    item_count = 0

    def visit(item: Any, field: str, depth: int) -> None:
        nonlocal item_count
        item_count += 1
        if item_count > _MAX_JSON_ITEMS:
            raise ContextPacketMalformedError(
                field,
                f"exceeds the {_MAX_JSON_ITEMS}-item limit",
            )
        if depth > _MAX_JSON_DEPTH:
            raise ContextPacketMalformedError(
                field,
                f"exceeds the {_MAX_JSON_DEPTH}-level depth limit",
            )
        if item is None or isinstance(item, (bool, int)):
            return
        if isinstance(item, float):
            if not math.isfinite(item):
                raise ContextPacketMalformedError(
                    field,
                    "must contain only finite numbers",
                )
            return
        if isinstance(item, str):
            if len(item) > _MAX_TEXT_LENGTH:
                raise ContextPacketMalformedError(
                    field,
                    f"exceeds the {_MAX_TEXT_LENGTH}-character text limit",
                )
            try:
                item.encode("utf-8")
            except UnicodeEncodeError as exc:
                raise ContextPacketMalformedError(
                    field,
                    "must not contain Unicode surrogate code points",
                ) from exc
            return
        if isinstance(item, Mapping):
            identity = id(item)
            if identity in active:
                raise ContextPacketMalformedError(field, "must not contain cycles")
            active.add(identity)
            for key, child in item.items():
                if not isinstance(key, str):
                    raise ContextPacketMalformedError(
                        field,
                        "must use string object keys",
                    )
                visit(child, f"{field}.{key}", depth + 1)
            active.remove(identity)
            return
        if isinstance(item, (list, tuple)):
            identity = id(item)
            if identity in active:
                raise ContextPacketMalformedError(field, "must not contain cycles")
            active.add(identity)
            for index, child in enumerate(item):
                visit(child, f"{field}[{index}]", depth + 1)
            active.remove(identity)
            return
        raise ContextPacketMalformedError(
            field,
            f"contains unsupported value type {type(item).__name__}",
        )

    visit(value, "packet", 0)


def _validate_packet_shape(
    payload: Mapping[str, Any],
    packet_contract: _PacketWireContract,
) -> None:
    _exact_fields(payload, _PACKET_TOP_LEVEL_FIELDS, "packet")
    if payload["schema_version"] != packet_contract.schema_version:
        raise ContextPacketMalformedError(
            "schema_version",
            f"must be {packet_contract.schema_version!r}",
        )
    if not is_valid_sha256(payload["packet_id"]):
        raise ContextPacketMalformedError(
            "packet_id",
            "must be a canonical lowercase SHA-256 value",
        )
    _validate_assurance(payload["assurance"])
    request = _validate_packet_request(payload["request"], packet_contract)
    _validate_response(payload["response"], request, packet_contract)
    _validate_basis(payload["basis"], packet_contract)
    _validate_response_basis_consistency(
        payload["response"],
        payload["basis"],
        request,
        packet_contract,
    )
    _validate_delivery(payload["delivery"], payload["response"], payload["basis"])
    _validate_path_policy_shape(payload["path_policy"])


def _validate_assurance(value: Any) -> None:
    data = _mapping(value, "assurance")
    _exact_fields(data, {"level", "scope"}, "assurance")
    if data["level"] != CONTEXT_PACKET_ASSURANCE_LEVEL:
        raise ContextPacketMalformedError(
            "assurance.level",
            f"must be {CONTEXT_PACKET_ASSURANCE_LEVEL!r}",
        )
    if data["scope"] != "canonical-packet-content":
        raise ContextPacketMalformedError(
            "assurance.scope",
            "must be 'canonical-packet-content'",
        )


def _validate_packet_request(
    value: Any,
    packet_contract: _PacketWireContract,
) -> dict[str, Any]:
    data = _mapping(value, "request")
    try:
        normalized = context_service._validate_protocol_request(dict(data))
    except context_service.ProtocolRequestError as exc:
        raise ContextPacketMalformedError(
            f"request.{exc.field or 'request'}",
            str(exc),
        ) from exc
    if dict(data) != normalized:
        raise ContextPacketMalformedError(
            "request",
            "must use the exact canonical normalized request shape",
        )
    if normalized.get("protocol") != packet_contract.context_protocol:
        raise ContextPacketMalformedError(
            "request.protocol",
            "does not match the packet schema",
        )
    has_mode = "knowledge_mode" in normalized
    if has_mode is not packet_contract.knowledge_mode_required:
        raise ContextPacketMalformedError(
            "request.knowledge_mode",
            (
                "is required by the packet schema"
                if packet_contract.knowledge_mode_required
                else "is not supported by the packet schema"
            ),
        )
    return normalized


def _validate_response(
    value: Any,
    request: Mapping[str, Any],
    packet_contract: _PacketWireContract,
) -> None:
    data = _mapping(value, "response")
    required = {
        "protocol",
        "ok",
        "budget_tokens",
        "used_tokens",
        "format",
        "focus",
        "filters",
        "truncated",
        "omitted_files",
        "downgraded_files",
        "bounds",
    }
    if packet_contract is _KNOWLEDGE_PACKET_CONTRACT:
        required.add("knowledge")
        required.add("source_priorities")
    optional = {
        "warnings",
        "graphs",
        "surface",
        "knowledge",
        "typed_graph",
        "files",
        "content",
        "prefer_fresh",
        "ranking_policy",
        "source_priorities",
    }
    _exact_fields(data, required | optional, "response", required=required)
    if data["protocol"] != packet_contract.context_protocol or data["ok"] is not True:
        raise ContextPacketMalformedError(
            "response",
            "must contain a successful current context-protocol response",
        )
    for name in ("budget_tokens", "format", "focus", "filters"):
        if data[name] != request[name]:
            raise ContextPacketMalformedError(
                f"response.{name}",
                "must match the normalized request",
            )
    if request["prefer_fresh"]:
        if data.get("prefer_fresh") is not True or not isinstance(
            data.get("ranking_policy"), Mapping
        ):
            raise ContextPacketMalformedError(
                "response",
                "freshness preference requires its disclosed ranking policy",
            )
        if packet_contract is _KNOWLEDGE_PACKET_CONTRACT:
            _validate_explicit_ranking_policy(
                data["ranking_policy"],
                data["knowledge"],
                response_truncated=data["truncated"],
            )
    elif "prefer_fresh" in data or "ranking_policy" in data:
        raise ContextPacketMalformedError(
            "response",
            "must not disclose freshness ranking when it was not requested",
        )
    used = data["used_tokens"]
    if isinstance(used, bool) or not isinstance(used, int) or used < 0:
        raise ContextPacketMalformedError(
            "response.used_tokens",
            "must be a non-negative integer",
        )
    if used > request["budget_tokens"]:
        raise ContextPacketMalformedError(
            "response.used_tokens",
            "must not exceed the requested token budget",
        )
    if not isinstance(data["truncated"], bool):
        raise ContextPacketMalformedError(
            "response.truncated",
            "must be a boolean",
        )
    if request["format"] == "json":
        if not isinstance(data.get("files"), Mapping) or "content" in data:
            raise ContextPacketMalformedError(
                "response",
                "JSON context requires files and must not contain content",
            )
    elif not isinstance(data.get("content"), str) or "files" in data:
        raise ContextPacketMalformedError(
            "response",
            "Markdown context requires content and must not contain files",
        )
    _string_list(data["omitted_files"], "response.omitted_files")
    downgraded = _mapping(data["downgraded_files"], "response.downgraded_files")
    if any(value not in {"deep", "slim", "summary"} for value in downgraded.values()):
        raise ContextPacketMalformedError(
            "response.downgraded_files",
            "must map paths to supported detail levels",
        )
    if "warnings" in data:
        _string_list(data["warnings"], "response.warnings")
    if packet_contract is _KNOWLEDGE_PACKET_CONTRACT:
        _validate_explicit_source_bounds(data)
        _validate_explicit_knowledge_response(
            data["knowledge"],
            request,
            source_priorities=_explicit_response_source_priorities(data),
        )


def _validate_explicit_knowledge_response(
    value: Any,
    request: Mapping[str, Any],
    *,
    source_priorities: Mapping[str, str] | None = None,
) -> None:
    data = _mapping(value, "response.knowledge")
    required = {
        "mode",
        "status",
        "availability",
        "reason",
        "selected",
        "freshness_evaluated",
        "bounds",
        "fallback",
    }
    _exact_fields(
        data,
        required | {"selection"},
        "response.knowledge",
        required=required,
    )
    mode = data["mode"]
    if mode != request["knowledge_mode"]:
        raise ContextPacketMalformedError(
            "response.knowledge.mode",
            "must match the normalized request",
        )
    status = data["status"]
    availability = data["availability"]
    reason = _stable_code(data["reason"], "response.knowledge.reason")
    selected = data["selected"]
    freshness_evaluated = data["freshness_evaluated"]
    if status not in {"disabled", "selected", "fallback"}:
        raise ContextPacketMalformedError(
            "response.knowledge.status",
            "must be disabled, selected, or fallback",
        )
    if availability not in {
        "not-evaluated",
        "ready",
        "absent",
        "degraded",
        "unsupported",
    }:
        raise ContextPacketMalformedError(
            "response.knowledge.availability",
            "contains an unsupported availability",
        )
    if not isinstance(selected, bool):
        raise ContextPacketMalformedError(
            "response.knowledge.selected",
            "must be a boolean",
        )
    if not isinstance(freshness_evaluated, bool):
        raise ContextPacketMalformedError(
            "response.knowledge.freshness_evaluated",
            "must be a boolean",
        )

    bounds = _validate_explicit_knowledge_bounds(data["bounds"])
    fallback = _mapping(data["fallback"], "response.knowledge.fallback")
    _exact_fields(
        fallback,
        {"used", "evidence", "reason"},
        "response.knowledge.fallback",
    )
    if not isinstance(fallback["used"], bool):
        raise ContextPacketMalformedError(
            "response.knowledge.fallback.used",
            "must be a boolean",
        )
    evidence = _string_list(
        fallback["evidence"],
        "response.knowledge.fallback.evidence",
    )
    allowed_evidence = {
        (),
        ("markdown", "targeted-source-or-runtime"),
        (
            "independently-validated-surface",
            "markdown",
            "targeted-source-or-runtime",
        ),
    }
    if tuple(evidence) not in allowed_evidence:
        raise ContextPacketMalformedError(
            "response.knowledge.fallback.evidence",
            "does not follow a supported read-only evidence chain",
        )
    fallback_reason = _stable_code(
        fallback["reason"],
        "response.knowledge.fallback.reason",
    )

    if mode == "off":
        if (
            status != "disabled"
            or availability != "not-evaluated"
            or reason != "knowledge-selection-disabled"
            or selected is not False
            or freshness_evaluated is not False
            or fallback["used"] is not False
            or evidence
            or fallback_reason != reason
            or "selection" in data
            or any(item["total"] != 0 for item in bounds.values())
        ):
            raise ContextPacketMalformedError(
                "response.knowledge",
                "contains inconsistent disabled-mode semantics",
            )
        return

    if mode not in {"auto", "required"}:
        raise ContextPacketMalformedError(
            "response.knowledge.mode",
            "must be off, auto, or required",
        )
    if status == "selected":
        if (
            availability != "ready"
            or selected is not True
            or fallback["used"] is not False
            or evidence
            or fallback_reason != "knowledge-selected"
            or reason
            not in {
                "knowledge-ready",
                "knowledge-snapshot-only",
                "knowledge-source-changed",
                "knowledge-results-truncated",
            }
            or "selection" not in data
        ):
            raise ContextPacketMalformedError(
                "response.knowledge",
                "contains inconsistent selected-mode semantics",
            )
        _validate_explicit_selection(
            data["selection"],
            bounds,
            freshness_evaluated=freshness_evaluated,
            source_priorities=source_priorities,
        )
        if reason == "knowledge-results-truncated":
            if not any(item["truncated"] for item in bounds.values()):
                raise ContextPacketMalformedError(
                    "response.knowledge.reason",
                    "requires at least one truncated knowledge collection",
                )
        elif any(item["truncated"] for item in bounds.values()):
            raise ContextPacketMalformedError(
                "response.knowledge.reason",
                "must disclose truncated knowledge results",
            )
        return

    if status != "fallback" or selected is not False or "selection" in data:
        raise ContextPacketMalformedError(
            "response.knowledge",
            "contains inconsistent fallback semantics",
        )
    if fallback["used"] is not True or not evidence or fallback_reason != reason:
        raise ContextPacketMalformedError(
            "response.knowledge.fallback",
            "must disclose the selected fallback evidence and reason",
        )
    if availability == "ready":
        if reason != "no-relevant-native-selection":
            raise ContextPacketMalformedError(
                "response.knowledge.reason",
                "ready fallback requires the no-selection reason",
            )
    elif reason not in {
        "knowledge-projection-not-present",
        "policy-selected-surface-only-fallback-after-mixed-snapshot",
        "policy-selected-surface-only-fallback-after-invalid",
        "knowledge-schema-version-unsupported",
        "knowledge-basis-incompatible",
        "surface-validation-failed",
        "governance-missing",
        "knowledge-result-exceeds-size-limit",
    }:
        raise ContextPacketMalformedError(
            "response.knowledge.reason",
            "is not a supported fallback reason",
        )
    if mode == "required" and availability != "ready":
        raise ContextPacketMalformedError(
            "response.knowledge",
            "required mode cannot emit a successful unavailable response",
        )
    if reason == "knowledge-result-exceeds-size-limit":
        if any(
            item["returned"] != 0 or item["truncated"] is not (item["total"] > 0)
            for item in bounds.values()
        ):
            raise ContextPacketMalformedError(
                "response.knowledge.bounds",
                "oversized fallback bounds must retain totals with no returned selection",
            )
    elif any(item["total"] != 0 for item in bounds.values()):
        raise ContextPacketMalformedError(
            "response.knowledge.bounds",
            "fallback knowledge must not claim returned native selection",
        )


def _validate_explicit_knowledge_bounds(
    value: Any,
) -> dict[str, dict[str, int | bool]]:
    data = _mapping(value, "response.knowledge.bounds")
    contract = _KNOWLEDGE_PACKET_CONTRACT
    assert contract.knowledge_concept_limit is not None
    assert contract.knowledge_page_limit is not None
    assert contract.knowledge_relationship_limit is not None
    limits = {
        "concepts": contract.knowledge_concept_limit,
        "pages": contract.knowledge_page_limit,
        "relationships": contract.knowledge_relationship_limit,
    }
    _exact_fields(data, set(limits), "response.knowledge.bounds")
    return {
        name: _validate_collection_bound(
            data[name],
            f"response.knowledge.bounds.{name}",
            returned_limit=limit,
        )
        for name, limit in limits.items()
    }


def _validate_collection_bound(
    value: Any,
    field: str,
    *,
    returned_limit: int | None = None,
) -> dict[str, int | bool]:
    data = _mapping(value, field)
    _exact_fields(data, {"total", "returned", "truncated"}, field)
    total = _nonnegative_integer(data["total"], f"{field}.total")
    returned = _nonnegative_integer(data["returned"], f"{field}.returned")
    truncated = data["truncated"]
    if not isinstance(truncated, bool):
        raise ContextPacketMalformedError(
            f"{field}.truncated",
            "must be a boolean",
        )
    if returned > total:
        raise ContextPacketMalformedError(
            f"{field}.returned",
            "must not exceed total",
        )
    if returned_limit is not None and returned > returned_limit:
        raise ContextPacketMalformedError(
            f"{field}.returned",
            f"must not exceed the {returned_limit}-item policy limit",
        )
    if truncated is not (total > returned):
        raise ContextPacketMalformedError(
            f"{field}.truncated",
            "must exactly disclose whether total exceeds returned",
        )
    return {"total": total, "returned": returned, "truncated": truncated}


def _validate_explicit_selection(
    value: Any,
    bounds: Mapping[str, Mapping[str, int | bool]],
    *,
    freshness_evaluated: bool,
    source_priorities: Mapping[str, str] | None,
) -> None:
    data = _mapping(value, "response.knowledge.selection")
    _exact_fields(
        data,
        {"concepts", "pages", "relationships", "relationship_coverage"},
        "response.knowledge.selection",
    )
    concepts = _object_list(
        data["concepts"],
        "response.knowledge.selection.concepts",
    )
    pages = _object_list(
        data["pages"],
        "response.knowledge.selection.pages",
    )
    relationships = _object_list(
        data["relationships"],
        "response.knowledge.selection.relationships",
    )
    collections = {
        "concepts": concepts,
        "pages": pages,
        "relationships": relationships,
    }
    for name, items in collections.items():
        if len(items) != bounds[name]["returned"]:
            raise ContextPacketMalformedError(
                f"response.knowledge.selection.{name}",
                "length must match its independent returned bound",
            )
    if not concepts:
        raise ContextPacketMalformedError(
            "response.knowledge.selection.concepts",
            "selected knowledge requires at least one returned concept",
        )
    _reject_raw_projection_content(data, "response.knowledge.selection")
    for index, concept in enumerate(concepts):
        _validate_explicit_concept(
            concept,
            f"response.knowledge.selection.concepts[{index}]",
            freshness_evaluated=freshness_evaluated,
        )
    for index, page in enumerate(pages):
        _validate_explicit_page(
            page,
            f"response.knowledge.selection.pages[{index}]",
        )
    for index, relationship in enumerate(relationships):
        _validate_explicit_relationship(
            relationship,
            f"response.knowledge.selection.relationships[{index}]",
        )
    concept_locators = [str(concept["locator"]) for concept in concepts]
    if len(set(concept_locators)) != len(concept_locators):
        raise ContextPacketMalformedError(
            "response.knowledge.selection.concepts",
            "must contain unique concept locators",
        )
    page_paths = [str(page["canonical_path"]) for page in pages]
    if len(set(page_paths)) != len(page_paths):
        raise ContextPacketMalformedError(
            "response.knowledge.selection.pages",
            "must contain unique canonical page paths",
        )
    relationship_identities = [canonical_json_bytes(item) for item in relationships]
    if len(set(relationship_identities)) != len(relationship_identities):
        raise ContextPacketMalformedError(
            "response.knowledge.selection.relationships",
            "must contain unique canonical relationship records",
        )
    if source_priorities is not None:
        tier_order = {"high": 0, "medium": 1, "low": 2}

        def source_rank(source_path: object, field: str) -> tuple[int, str]:
            if not isinstance(source_path, str) or source_path not in source_priorities:
                raise ContextPacketMalformedError(
                    field,
                    "must refer to a returned source-context file",
                )
            return tier_order[source_priorities[source_path]], source_path

        concept_order = [
            (
                *source_rank(item["source_path"], f"concepts[{index}].source_path"),
                item["locator"],
            )
            for index, item in enumerate(concepts)
        ]
        if concept_order != sorted(concept_order):
            raise ContextPacketMalformedError(
                "response.knowledge.selection.concepts",
                "must follow canonical relevance-tier and source order",
            )
        page_order = [
            (
                *source_rank(item["source_path"], f"pages[{index}].source_path"),
                item["canonical_path"],
            )
            for index, item in enumerate(pages)
        ]
        if page_order != sorted(page_order):
            raise ContextPacketMalformedError(
                "response.knowledge.selection.pages",
                "must follow canonical relevance-tier and source order",
            )
        concept_rank_by_locator = {
            item["locator"]: concept_order[index] for index, item in enumerate(concepts)
        }
        concept_locator_by_path = {
            item["canonical_path"]: item["locator"] for item in concepts
        }
        relationship_order: list[tuple[Any, ...] | None] = []
        for index, item in enumerate(relationships):
            incident_locators: list[str] = []
            source = item.get("from")
            source_locator: str | None = None
            if isinstance(source, str):
                source_locator = source
                incident_locators.append(source_locator)
            elif isinstance(source, Mapping):
                raw_source_locator = source.get("locator")
                if isinstance(raw_source_locator, str):
                    source_locator = raw_source_locator
                    incident_locators.append(raw_source_locator)
            target = item.get("target")
            target_locator: str | None = None
            if isinstance(target, Mapping) and isinstance(
                raw_target_locator := target.get("locator"), str
            ):
                target_locator = raw_target_locator
                incident_locators.append(raw_target_locator)
            elif (
                isinstance(target, Mapping)
                and target.get("target_class") == "concept"
                and isinstance(target.get("canonical_path"), str)
                and target["canonical_path"] in concept_locator_by_path
            ):
                matched_locator = concept_locator_by_path[target["canonical_path"]]
                target_locator = matched_locator
                incident_locators.append(matched_locator)
            source_returned = source_locator in concept_rank_by_locator
            target_returned = target_locator in concept_rank_by_locator
            if source_returned and target_returned and item["direction"] != "both":
                raise ContextPacketMalformedError(
                    f"response.knowledge.selection.relationships[{index}].direction",
                    "must be both when both incident concepts are returned",
                )
            if source_returned and isinstance(target, Mapping):
                if (
                    item["graph"] == "knowledge"
                    and target.get("target_class") not in {"concept"}
                    and item["direction"] != "outbound"
                ):
                    raise ContextPacketMalformedError(
                        f"response.knowledge.selection.relationships[{index}].direction",
                        "must be outbound for a selected source and non-concept target",
                    )
                if (
                    item["graph"] == "typed"
                    and target.get("kind")
                    in {
                        "external-resource",
                        "unresolved",
                    }
                    and item["direction"] != "outgoing"
                ):
                    raise ContextPacketMalformedError(
                        f"response.knowledge.selection.relationships[{index}].direction",
                        "must be outgoing for a selected source and external target",
                    )
            incident_ranks = [
                concept_rank_by_locator[locator]
                for locator in incident_locators
                if locator in concept_rank_by_locator
            ]
            relationship_order.append(
                None
                if not incident_ranks
                else (
                    *min(incident_ranks),
                    0 if item["graph"] == "knowledge" else 1,
                    canonical_json_bytes(item),
                )
            )
        canonical_relationship_order = [
            item for item in relationship_order if item is not None
        ]
        first_unranked = next(
            (index for index, item in enumerate(relationship_order) if item is None),
            len(relationship_order),
        )
        if any(item is not None for item in relationship_order[first_unranked:]):
            raise ContextPacketMalformedError(
                "response.knowledge.selection.relationships",
                "ranked relationships must precede the unranked canonical tail",
            )
        if canonical_relationship_order != sorted(canonical_relationship_order):
            raise ContextPacketMalformedError(
                "response.knowledge.selection.relationships",
                "must follow canonical incident-concept and graph order",
            )
    coverage = _mapping(
        data["relationship_coverage"],
        "response.knowledge.selection.relationship_coverage",
    )
    _exact_fields(
        coverage,
        {"availability", "reason", "schema_version", "coverage"},
        "response.knowledge.selection.relationship_coverage",
    )
    if coverage["availability"] not in {
        "ready",
        "absent",
        "degraded",
        "unsupported",
    } or not isinstance(coverage["reason"], str):
        raise ContextPacketMalformedError(
            "response.knowledge.selection.relationship_coverage",
            "must disclose graph availability and reason",
        )
    if coverage["schema_version"] is not None and (
        not isinstance(coverage["schema_version"], str)
        or not coverage["schema_version"]
    ):
        raise ContextPacketMalformedError(
            "response.knowledge.selection.relationship_coverage.schema_version",
            "must be a non-empty string or null",
        )
    coverage_items = _object_list(
        coverage["coverage"],
        "response.knowledge.selection.relationship_coverage.coverage",
    )
    allowed_coverage = {
        "analyzer",
        "observed",
        "emitted",
        "omitted",
        "limit",
        "truncated",
        "limitations",
        "limitation_bounds",
    }
    for index, item in enumerate(coverage_items):
        item_field = (
            f"response.knowledge.selection.relationship_coverage.coverage[{index}]"
        )
        _exact_fields(item, allowed_coverage, item_field)
        if not isinstance(item["analyzer"], str) or not item["analyzer"]:
            raise ContextPacketMalformedError(
                f"{item_field}.analyzer",
                "must be a non-empty string",
            )
        _validate_canonical_coverage(item, item_field, includes_analyzer=True)
    coverage_analyzers = [str(item["analyzer"]) for item in coverage_items]
    if coverage_analyzers != sorted(set(coverage_analyzers)):
        raise ContextPacketMalformedError(
            "response.knowledge.selection.relationship_coverage.coverage",
            "must contain unique analyzers in canonical order",
        )
    availability = coverage["availability"]
    reason = coverage["reason"]
    schema_version = coverage["schema_version"]
    if availability == "absent":
        if (
            reason != "typed-graph-extension-not-present"
            or schema_version is not None
            or coverage_items
        ):
            raise ContextPacketMalformedError(
                "response.knowledge.selection.relationship_coverage",
                "absent typed-graph coverage requires its canonical empty disclosure",
            )
    elif availability == "ready":
        if (
            reason != "typed-graph-extension-ready"
            or schema_version != TYPED_GRAPH_SCHEMA_VERSION
            or coverage_analyzers != sorted(GRAPH_COVERAGE_ANALYZERS)
        ):
            raise ContextPacketMalformedError(
                "response.knowledge.selection.relationship_coverage",
                "ready typed-graph coverage requires the complete canonical analyzer set",
            )
    else:
        raise ContextPacketMalformedError(
            "response.knowledge.selection.relationship_coverage.availability",
            "selected knowledge coverage must be ready or canonically absent",
        )


def _validate_explicit_concept(
    value: Mapping[str, Any],
    field: str,
    *,
    freshness_evaluated: bool,
) -> None:
    required = {
        "locator",
        "concept_kind",
        "title",
        "page_kind",
        "page_id",
        "canonical_path",
        "mcp_uri",
        "source_path",
        "role",
        "origin",
        "evidence",
        "verification",
        "lifecycle",
        "freshness",
    }
    _exact_fields(value, required | {"uid"}, field, required=required)
    for name in required - {"freshness"}:
        if not isinstance(value[name], str) or not value[name]:
            raise ContextPacketMalformedError(
                f"{field}.{name}",
                "must be a non-empty string",
            )
    if "uid" in value and (not isinstance(value["uid"], str) or not value["uid"]):
        raise ContextPacketMalformedError(
            f"{field}.uid",
            "must be a non-empty string",
        )
    enum_fields = {
        "concept_kind": {item.value for item in ConceptKind},
        "origin": {item.value for item in Origin},
        "evidence": {item.value for item in EvidenceState},
        "verification": {item.value for item in Verification},
        "lifecycle": {item.value for item in Lifecycle},
    }
    for name, allowed in enum_fields.items():
        if value[name] not in allowed:
            raise ContextPacketMalformedError(
                f"{field}.{name}",
                "contains an unsupported knowledge-model value",
            )
    if value["locator"] != value["mcp_uri"]:
        raise ContextPacketMalformedError(
            f"{field}.locator",
            "must match the selected concept MCP URI",
        )
    _validate_wiki_page_coordinate(
        page_kind=value["page_kind"],
        page_id=value["page_id"],
        canonical_path=value["canonical_path"],
        mcp_uri=value["mcp_uri"],
        role=value["role"],
        field=field,
    )
    expected_concept_kind = concept_kind_for_page_kind(value["page_kind"])
    if value["concept_kind"] != expected_concept_kind.value:
        raise ContextPacketMalformedError(
            f"{field}.concept_kind",
            "must match the registered page kind",
        )
    freshness = _mapping(value["freshness"], f"{field}.freshness")
    _exact_fields(
        freshness,
        {"state", "reason", "live_comparison_performed", "hint"},
        f"{field}.freshness",
        required={"state", "reason", "live_comparison_performed"},
    )
    state = freshness["state"]
    if state not in {
        "not-evaluated",
        *(item.value for item in ComputedFreshness),
    }:
        raise ContextPacketMalformedError(
            f"{field}.freshness.state",
            "contains an unsupported freshness state",
        )
    _stable_code(freshness["reason"], f"{field}.freshness.reason")
    if freshness["reason"] not in KNOWN_FRESHNESS_REASON_CODES:
        raise ContextPacketMalformedError(
            f"{field}.freshness.reason",
            "contains an unsupported freshness reason",
        )
    if not isinstance(freshness["live_comparison_performed"], bool):
        raise ContextPacketMalformedError(
            f"{field}.freshness.live_comparison_performed",
            "must be a boolean",
        )
    if "hint" in freshness and (
        not isinstance(freshness["hint"], str) or not freshness["hint"]
    ):
        raise ContextPacketMalformedError(
            f"{field}.freshness.hint",
            "must be a non-empty string",
        )
    if freshness_evaluated:
        if state == "not-evaluated":
            raise ContextPacketMalformedError(
                f"{field}.freshness.state",
                "cannot be not-evaluated under an evaluated knowledge result",
            )
        if (
            state == ComputedFreshness.CURRENT.value
            and (
                freshness["live_comparison_performed"] is not True
                or freshness["reason"] != REASON_RECORDED_BASIS_MATCHES_LIVE_EVALUATION
            )
        ) or (
            freshness["reason"] == REASON_RECORDED_BASIS_MATCHES_LIVE_EVALUATION
            and state != ComputedFreshness.CURRENT.value
        ):
            raise ContextPacketMalformedError(
                f"{field}.freshness",
                "current freshness requires its canonical live-match disclosure",
            )
    elif freshness != {
        "state": "not-evaluated",
        "reason": "live-evaluation-not-performed",
        "live_comparison_performed": False,
    }:
        raise ContextPacketMalformedError(
            f"{field}.freshness",
            "must use the exact snapshot-only freshness disclosure",
        )


def _validate_explicit_page(value: Mapping[str, Any], field: str) -> None:
    fields = {
        "kind",
        "id",
        "title",
        "canonical_path",
        "source_path",
        "role",
        "mcp_uri",
    }
    _exact_fields(value, fields, field)
    for name in fields:
        if not isinstance(value[name], str) or not value[name]:
            raise ContextPacketMalformedError(
                f"{field}.{name}",
                "must be a non-empty string",
            )
    _validate_wiki_page_coordinate(
        page_kind=value["kind"],
        page_id=value["id"],
        canonical_path=value["canonical_path"],
        mcp_uri=value["mcp_uri"],
        role=value["role"],
        field=field,
    )


def _validate_wiki_page_coordinate(
    *,
    page_kind: object,
    page_id: object,
    canonical_path: object,
    mcp_uri: object,
    role: object,
    field: str,
) -> None:
    entry = next(
        (
            candidate
            for candidate in wiki_surface.iter_page_kinds()
            if candidate.kind.value == page_kind
        ),
        None,
    )
    if entry is None or not isinstance(page_id, str):
        raise ContextPacketMalformedError(
            f"{field}.page_kind",
            "must identify a registered wiki surface kind",
        )
    registry_page_id = page_id if entry.requires_page_id else None
    if not entry.requires_page_id and page_id != entry.kind.value:
        raise ContextPacketMalformedError(
            f"{field}.page_id",
            "must match the registered root-page identity",
        )
    try:
        expected_path = wiki_surface.canonical_path(entry.kind, registry_page_id)
        expected_uri = wiki_surface.mcp_uri(entry.kind, registry_page_id)
    except wiki_surface.WikiSurfaceError as exc:
        raise ContextPacketMalformedError(
            field,
            "contains an invalid registered wiki page coordinate",
        ) from exc
    if (
        canonical_path != expected_path
        or mcp_uri != expected_uri
        or role != entry.role.value
    ):
        raise ContextPacketMalformedError(
            field,
            "wiki page kind, id, path, URI, and role must match the registry",
        )


def _validate_explicit_relationship(
    value: Mapping[str, Any],
    field: str,
) -> None:
    graph = value.get("graph")
    shared = {
        "graph",
        "kind",
        "direction",
        "from",
        "origin",
        "resolution",
        "evidence",
        "target",
    }
    if graph == "knowledge":
        _exact_fields(value, shared, field)
        if value["direction"] not in {"inbound", "outbound", "both"}:
            raise ContextPacketMalformedError(
                f"{field}.direction",
                "contains an unsupported knowledge direction",
            )
        if not isinstance(value["from"], str) or not value["from"]:
            raise ContextPacketMalformedError(
                f"{field}.from",
                "must be a non-empty locator",
            )
        _validate_native_wiki_uri(value["from"], f"{field}.from")
        if value["kind"] not in {"derived_from", "links_to"}:
            raise ContextPacketMalformedError(
                f"{field}.kind",
                "contains an unsupported native relationship kind",
            )
        if value["origin"] not in {item.value for item in Origin}:
            raise ContextPacketMalformedError(
                f"{field}.origin",
                "contains an unsupported native relationship origin",
            )
        if value["resolution"] not in {item.value for item in Resolution}:
            raise ContextPacketMalformedError(
                f"{field}.resolution",
                "contains an unsupported native relationship resolution",
            )
    elif graph == "typed":
        _exact_fields(value, shared | {"key", "coverage"}, field)
        key = value["key"]
        if not is_valid_sha256(key):
            raise ContextPacketMalformedError(
                f"{field}.key",
                "must be a canonical SHA-256 typed-edge identity",
            )
        if value["direction"] not in {"incoming", "outgoing", "both"}:
            raise ContextPacketMalformedError(
                f"{field}.direction",
                "contains an unsupported typed-graph direction",
            )
        _validate_context_endpoint(value["from"], f"{field}.from")
        if _mapping(value["from"], f"{field}.from").get("kind") != "concept":
            raise ContextPacketMalformedError(
                f"{field}.from.kind",
                "typed relationship sources must be concept endpoints",
            )
        if "coordinate_state" in _mapping(value["from"], f"{field}.from"):
            raise ContextPacketMalformedError(
                f"{field}.from.coordinate_state",
                "typed relationship sources require a concrete coordinate",
            )
        coverage = _mapping(value["coverage"], f"{field}.coverage")
        _validate_canonical_coverage(coverage, f"{field}.coverage")
        if not is_supported_relationship_kind(value["kind"]):
            raise ContextPacketMalformedError(
                f"{field}.kind",
                "contains an unsupported typed relationship kind",
            )
        if value["origin"] not in GRAPH_ORIGINS:
            raise ContextPacketMalformedError(
                f"{field}.origin",
                "contains an unsupported typed relationship origin",
            )
        if value["resolution"] not in GRAPH_RESOLUTIONS:
            raise ContextPacketMalformedError(
                f"{field}.resolution",
                "contains an unsupported typed relationship resolution",
            )
        target_kind = _mapping(value["target"], f"{field}.target").get("kind")
        expected_target_kind = {
            "resolved": "concept",
            "external": "external-resource",
            "ambiguous": "unresolved",
            "unresolved": "unresolved",
        }[value["resolution"]]
        if target_kind != expected_target_kind:
            raise ContextPacketMalformedError(
                f"{field}.target.kind",
                "must match the typed relationship resolution",
            )
        if value["kind"] in CORE_RELATIONSHIP_KINDS:
            expected_origins = (
                {"governance"}
                if value["kind"] == "supersedes"
                else {"extracted", "inferred"}
            )
            if value["origin"] not in expected_origins:
                raise ContextPacketMalformedError(
                    f"{field}.origin",
                    "does not match the core typed relationship kind",
                )
            if value["kind"] == "depends_on" and (
                value["resolution"] != "external" or target_kind != "external-resource"
            ):
                raise ContextPacketMalformedError(
                    field,
                    "depends_on requires an external-resource target",
                )
            if value["kind"] == "supersedes" and value["resolution"] != "resolved":
                raise ContextPacketMalformedError(
                    field,
                    "supersedes requires a resolved concept target",
                )
    else:
        raise ContextPacketMalformedError(
            f"{field}.graph",
            "must be knowledge or typed",
        )
    for name in ("kind", "origin", "resolution"):
        if not isinstance(value[name], str) or not value[name]:
            raise ContextPacketMalformedError(
                f"{field}.{name}",
                "must be a non-empty string",
            )
    evidence = _mapping(value["evidence"], f"{field}.evidence")
    allowed_evidence = {"state", "observed", "unique", "emitted", "omitted"}
    _exact_fields(
        evidence,
        {"state"} if graph == "knowledge" else allowed_evidence,
        f"{field}.evidence",
    )
    if not isinstance(evidence["state"], str) or not evidence["state"]:
        raise ContextPacketMalformedError(
            f"{field}.evidence.state",
            "must be a non-empty string",
        )
    allowed_evidence_states = (
        {item.value for item in EvidenceState}
        if graph == "knowledge"
        else set(GRAPH_EVIDENCE_STATES)
    )
    if evidence["state"] not in allowed_evidence_states:
        raise ContextPacketMalformedError(
            f"{field}.evidence.state",
            "contains an unsupported relationship evidence state",
        )
    if graph == "typed":
        observed = _nonnegative_integer(
            evidence["observed"], f"{field}.evidence.observed"
        )
        unique = _nonnegative_integer(evidence["unique"], f"{field}.evidence.unique")
        emitted = _nonnegative_integer(evidence["emitted"], f"{field}.evidence.emitted")
        omitted = _nonnegative_integer(evidence["omitted"], f"{field}.evidence.omitted")
        if not (emitted <= unique <= observed) or omitted != observed - emitted:
            raise ContextPacketMalformedError(
                f"{field}.evidence",
                "typed counts require emitted <= unique <= observed and exact omitted",
            )
        if any(
            evidence[name] != coverage[name]
            for name in ("observed", "emitted", "omitted")
        ):
            raise ContextPacketMalformedError(
                f"{field}.evidence",
                "typed evidence counts must match edge coverage",
            )
    _validate_context_endpoint(value["target"], f"{field}.target")
    target = _mapping(value["target"], f"{field}.target")
    if "coordinate_state" in target:
        valid_unavailable = (
            graph == "knowledge"
            and value["resolution"] == "unresolved"
            and target.get("target_class") == "malformed"
        ) or (
            graph == "typed"
            and value["resolution"] in {"ambiguous", "unresolved"}
            and target.get("kind") == "unresolved"
        )
        if not valid_unavailable:
            raise ContextPacketMalformedError(
                f"{field}.target.coordinate_state",
                "is reserved for an unavailable unresolved target coordinate",
            )
    if graph == "knowledge":
        _validate_knowledge_relationship_semantics(value, target, field)


def _validate_knowledge_relationship_semantics(
    relationship: Mapping[str, Any],
    target: Mapping[str, Any],
    field: str,
) -> None:
    kind = relationship["kind"]
    origin = relationship["origin"]
    resolution = relationship["resolution"]
    target_class = target.get("target_class")
    if kind == "derived_from":
        if (
            origin not in {Origin.EXTRACTED.value, Origin.INFERRED.value}
            or resolution != Resolution.RESOLVED.value
            or target_class != TargetClass.SOURCE.value
            or set(target) != {"target_class", "source_path"}
        ):
            raise ContextPacketMalformedError(
                field,
                "derived_from requires extracted/inferred origin and one resolved source target",
            )
        return

    if origin != Origin.MARKDOWN.value:
        raise ContextPacketMalformedError(
            f"{field}.origin",
            "links_to relationships require markdown origin",
        )
    allowed_fields_by_shape: dict[tuple[str, object], set[str]] = {
        (Resolution.RESOLVED.value, TargetClass.CONCEPT.value): {
            "target_class",
            "canonical_path",
        },
        (Resolution.RESOLVED.value, TargetClass.ASSET.value): {
            "target_class",
            "canonical_path",
        },
        (Resolution.RESOLVED.value, TargetClass.ANCHOR.value): {
            "target_class",
            "normalized_target",
        },
        (Resolution.EXTERNAL.value, TargetClass.EXTERNAL.value): {
            "target_class",
            "external_uri",
        },
        (Resolution.EXTERNAL.value, TargetClass.MAIL.value): {
            "target_class",
            "external_uri",
        },
        (Resolution.AMBIGUOUS.value, TargetClass.CONCEPT.value): {
            "target_class",
            "normalized_target",
        },
        (Resolution.UNRESOLVED.value, TargetClass.CONCEPT.value): {
            "target_class",
            "normalized_target",
        },
        (Resolution.UNRESOLVED.value, TargetClass.MALFORMED.value): {
            "target_class",
            "coordinate_state",
        },
    }
    expected_fields = allowed_fields_by_shape.get((resolution, target_class))
    if (
        expected_fields is None
        or set(target) != expected_fields
        and not (
            resolution == Resolution.RESOLVED.value
            and target_class == TargetClass.CONCEPT.value
            and set(target) == {"target_class", "locator"}
        )
    ):
        raise ContextPacketMalformedError(
            f"{field}.target",
            "links_to target class and coordinate must match its resolution",
        )
    external_uri = target.get("external_uri")
    if isinstance(external_uri, str):
        scheme = urlsplit(external_uri).scheme.casefold()
        if (
            target_class == TargetClass.MAIL.value
            and scheme != "mailto"
            or target_class == TargetClass.EXTERNAL.value
            and scheme == "mailto"
        ):
            raise ContextPacketMalformedError(
                f"{field}.target.external_uri",
                "URI scheme must match the external target class",
            )


def _validate_context_endpoint(value: Any, field: str) -> None:
    data = _mapping(value, field)
    allowed = {
        "kind",
        "target_class",
        "locator",
        "uid",
        "canonical_path",
        "source_path",
        "external_uri",
        "resource",
        "symbol",
        "normalized_target",
        "coordinate_state",
    }
    _exact_fields(data, allowed, field, required=set())
    for name, item in data.items():
        if not isinstance(item, str) or not item:
            raise ContextPacketMalformedError(
                f"{field}.{name}",
                "must be a non-empty string",
            )
        if name == "external_uri":
            _validate_portable_uri(item, f"{field}.{name}")
        elif name == "locator":
            _validate_native_wiki_uri(item, f"{field}.{name}")
        elif name == "normalized_target":
            _validate_normalized_context_target(item, f"{field}.{name}")
        elif name == "coordinate_state" and item != "unavailable":
            raise ContextPacketMalformedError(
                f"{field}.{name}",
                "must be unavailable",
            )
        elif name == "resource" and len(item) > 2048:
            raise ContextPacketMalformedError(
                f"{field}.{name}",
                "must be a bounded external resource coordinate",
            )
        elif name == "symbol" and len(item) > 512:
            raise ContextPacketMalformedError(
                f"{field}.{name}",
                "must be a bounded source symbol",
            )
    if "kind" in data and data["kind"] not in ENDPOINT_KINDS:
        raise ContextPacketMalformedError(
            f"{field}.kind",
            "contains an unsupported typed endpoint kind",
        )
    if "target_class" in data and data["target_class"] not in {
        item.value for item in TargetClass
    }:
        raise ContextPacketMalformedError(
            f"{field}.target_class",
            "contains an unsupported target class",
        )
    coordinate_fields = {
        "locator",
        "uid",
        "canonical_path",
        "source_path",
        "external_uri",
        "normalized_target",
        "coordinate_state",
        "resource",
    }
    if not (coordinate_fields & set(data)):
        raise ContextPacketMalformedError(
            field,
            "must contain at least one meaningful endpoint coordinate",
        )
    endpoint_kind = data.get("kind")
    if endpoint_kind == "concept" and (
        set(data) not in ({"kind", "locator"}, {"kind", "uid"})
    ):
        raise ContextPacketMalformedError(
            field,
            "concept endpoints require exactly one locator or UID",
        )
    if endpoint_kind == "source-symbol" and set(data) != {
        "kind",
        "source_path",
        "symbol",
    }:
        raise ContextPacketMalformedError(
            field,
            "source-symbol endpoints require source_path and symbol",
        )
    if endpoint_kind == "external-resource" and (
        "resource" not in data or not set(data) <= {"kind", "resource", "external_uri"}
    ):
        raise ContextPacketMalformedError(
            field,
            "external-resource endpoints require a bounded resource coordinate",
        )
    if endpoint_kind == "unresolved" and (
        set(data)
        not in (
            {"kind", "normalized_target"},
            {"kind", "coordinate_state"},
        )
    ):
        raise ContextPacketMalformedError(
            field,
            "unresolved endpoints require one safe observation coordinate",
        )
    if endpoint_kind is None and len(coordinate_fields & set(data)) != 1:
        raise ContextPacketMalformedError(
            field,
            "must contain exactly one canonical endpoint coordinate",
        )
    if "coordinate_state" in data and not (
        data.get("target_class") == "malformed" or endpoint_kind == "unresolved"
    ):
        raise ContextPacketMalformedError(
            f"{field}.coordinate_state",
            "is only valid for a malformed endpoint",
        )
    target_class = data.get("target_class")
    if "canonical_path" in data and target_class == "concept":
        expected_uri = _wiki_uri_for_canonical_path(data["canonical_path"], field)
        if "locator" in data and data["locator"] != expected_uri:
            raise ContextPacketMalformedError(
                field,
                "canonical_path and locator must identify the same wiki page",
            )
    if target_class == "asset" and (
        "canonical_path" not in data or not data["canonical_path"].startswith("assets/")
    ):
        raise ContextPacketMalformedError(
            field,
            "asset endpoints require a canonical assets/ path",
        )
    if target_class == "source" and "source_path" not in data:
        raise ContextPacketMalformedError(
            field,
            "source endpoints require source_path",
        )
    if target_class in {"external", "mail"} and "external_uri" not in data:
        raise ContextPacketMalformedError(
            field,
            "external endpoints require external_uri",
        )
    if target_class == "anchor" and not data.get("normalized_target", "").startswith(
        "#"
    ):
        raise ContextPacketMalformedError(
            field,
            "anchor endpoints require a normalized anchor coordinate",
        )


def _validate_canonical_coverage(
    value: Mapping[str, Any],
    field: str,
    *,
    includes_analyzer: bool = False,
) -> None:
    fields = {
        "observed",
        "emitted",
        "omitted",
        "limit",
        "truncated",
        "limitations",
        "limitation_bounds",
    }
    if includes_analyzer:
        fields.add("analyzer")
    _exact_fields(value, fields, field)
    observed = _nonnegative_integer(value["observed"], f"{field}.observed")
    emitted = _nonnegative_integer(value["emitted"], f"{field}.emitted")
    omitted = _nonnegative_integer(value["omitted"], f"{field}.omitted")
    limit_value = value["limit"]
    limit = (
        None
        if limit_value is None
        else _nonnegative_integer(limit_value, f"{field}.limit")
    )
    truncated = value["truncated"]
    if not isinstance(truncated, bool):
        raise ContextPacketMalformedError(f"{field}.truncated", "must be a boolean")
    if observed != emitted + omitted:
        raise ContextPacketMalformedError(
            field,
            "observed must equal emitted plus omitted",
        )
    if truncated is not (omitted > 0):
        raise ContextPacketMalformedError(
            f"{field}.truncated",
            "must exactly disclose omitted observations",
        )
    if limit is not None and emitted > limit:
        raise ContextPacketMalformedError(
            f"{field}.limit",
            "must not be lower than emitted",
        )
    limitations = _string_list(value["limitations"], f"{field}.limitations")
    if limitations != sorted(set(limitations)) or any(
        len(item) > CONTEXT_COVERAGE_LIMITATION_CODE_MAX_LENGTH
        or _COVERAGE_LIMITATION_RE.fullmatch(item) is None
        for item in limitations
    ):
        raise ContextPacketMalformedError(
            f"{field}.limitations",
            "must contain bounded sorted unique stable limitation codes",
        )
    limitation_bounds = _validate_collection_bound(
        value["limitation_bounds"],
        f"{field}.limitation_bounds",
        returned_limit=CONTEXT_COVERAGE_LIMITATION_LIMIT,
    )
    if limitation_bounds["returned"] != len(limitations):
        raise ContextPacketMalformedError(
            f"{field}.limitation_bounds.returned",
            "must match the returned limitation-code array",
        )


def _validate_portable_uri(value: str, field: str) -> None:
    if (
        _PORTABLE_URI_RE.fullmatch(value) is None
        or _RFC3986_URI_RE.fullmatch(value) is None
        or any(character.isspace() for character in value)
        or "\\" in value
        or value.casefold().startswith("file:")
        or value.casefold().startswith("llm-wiki:")
        or _WINDOWS_ABSOLUTE_RE.match(value)
        or re.search(r"%(?![0-9A-Fa-f]{2})", value) is not None
        or contains_uri_authority_userinfo(value)
    ):
        raise ContextPacketMalformedError(
            field,
            "must be a portable non-file URI",
        )
    try:
        parsed = urlsplit(value)
        _ = parsed.port
        hostname = parsed.hostname
    except ValueError as exc:
        raise ContextPacketMalformedError(
            field,
            "must be a well-formed portable URI",
        ) from exc
    uses_authority = value[len(parsed.scheme) :].startswith("://")
    requires_authority = parsed.scheme.casefold() in {"http", "https", "ftp", "ftps"}
    if (
        not parsed.scheme
        or (uses_authority or requires_authority)
        and not parsed.netloc
        or (uses_authority or requires_authority)
        and hostname is None
    ):
        raise ContextPacketMalformedError(
            field,
            "must be a well-formed absolute URI",
        )


def _validate_native_wiki_uri(value: str, field: str) -> None:
    if not value.startswith("llm-wiki://"):
        raise ContextPacketMalformedError(
            field,
            "must be a canonical native llm-wiki page URI",
        )
    try:
        wiki_surface.validate_exact_page_coordinate(value)
    except wiki_surface.WikiSurfaceError as exc:
        raise ContextPacketMalformedError(
            field,
            "must be a canonical native llm-wiki page URI",
        ) from exc


def _validate_normalized_context_target(value: str, field: str) -> None:
    if (
        len(value) > _MAX_NORMALIZED_CONTEXT_TARGET_LENGTH
        or "\\" in value
        or value.startswith(("/", "~"))
        or _WINDOWS_ABSOLUTE_RE.match(value)
        or value.casefold().startswith("file:")
        or any(ord(character) < 32 for character in value)
    ):
        raise ContextPacketMalformedError(
            field,
            "must be a safe normalized unresolved target coordinate",
        )


def _wiki_uri_for_canonical_path(value: str, field: str) -> str:
    for entry in wiki_surface.iter_page_kinds():
        if not entry.requires_page_id:
            if value == wiki_surface.canonical_path(entry.kind):
                return wiki_surface.mcp_uri(entry.kind)
            continue
        prefix, _marker, suffix = entry.path_pattern.partition("{page_id}")
        if not value.startswith(prefix) or not value.endswith(suffix):
            continue
        page_id = value[len(prefix) : len(value) - len(suffix) if suffix else None]
        try:
            if wiki_surface.canonical_path(entry.kind, page_id) == value:
                return wiki_surface.mcp_uri(entry.kind, page_id)
        except wiki_surface.WikiSurfaceError:
            continue
    raise ContextPacketMalformedError(
        field,
        "canonical_path must identify a registered wiki page",
    )


def _reject_raw_projection_content(value: Any, field: str) -> None:
    forbidden = {
        "aliases",
        "analysis_basis_hash",
        "concept_observation_hash",
        "content_hash",
        "diagnostics",
        "lifecycle_events",
        "live_basis",
        "machine_verification",
        "page_hash",
        "raw_evidence",
        "recorded_basis",
        "reviews",
        "samples",
        "source_content_hash",
    }

    def visit(item: Any, pointer: str) -> None:
        if isinstance(item, Mapping):
            for key, child in item.items():
                if key in forbidden or key.endswith("_hash"):
                    raise ContextPacketMalformedError(
                        f"{pointer}.{key}",
                        "raw projection evidence is not allowed in context selection",
                    )
                visit(child, f"{pointer}.{key}")
        elif isinstance(item, list):
            for index, child in enumerate(item):
                visit(child, f"{pointer}[{index}]")

    visit(value, field)


def _validate_explicit_ranking_policy(
    value: Any,
    knowledge_value: Any,
    *,
    response_truncated: Any,
) -> None:
    data = _mapping(value, "response.ranking_policy")
    _exact_fields(
        data,
        {
            "requested",
            "policy",
            "scope",
            "budget_pressure",
            "applied",
            "reason",
        },
        "response.ranking_policy",
    )
    if (
        data["requested"] is not True
        or data["policy"] != "current-first"
        or data["scope"] != "within-existing-relevance-tier-under-budget-pressure"
        or not isinstance(data["budget_pressure"], bool)
        or not isinstance(data["applied"], bool)
    ):
        raise ContextPacketMalformedError(
            "response.ranking_policy",
            "contains unsupported explicit freshness-ranking semantics",
        )
    if data["budget_pressure"] is not response_truncated:
        raise ContextPacketMalformedError(
            "response.ranking_policy.budget_pressure",
            "must match source-context budget pressure",
        )
    knowledge = _mapping(knowledge_value, "response.knowledge")
    if knowledge.get("mode") == "off":
        expected_reasons = {"knowledge-selection-disabled"}
        expected_applied = False
    elif knowledge.get("status") != "selected":
        expected_reasons = {"knowledge-unavailable"}
        expected_applied = False
    elif data["budget_pressure"] is False:
        expected_reasons = {"no-budget-pressure"}
        expected_applied = False
    elif data["applied"] is True:
        expected_reasons = {"same-tier-budget-pressure"}
        expected_applied = True
    else:
        expected_reasons = {"qualified-freshness-ranks-unavailable"}
        expected_applied = False
    if (
        data["applied"] is not expected_applied
        or data["reason"] not in expected_reasons
    ):
        raise ContextPacketMalformedError(
            "response.ranking_policy",
            "does not match the disclosed knowledge result and budget pressure",
        )
    if data["applied"] and knowledge.get("freshness_evaluated") is not True:
        raise ContextPacketMalformedError(
            "response.ranking_policy.applied",
            "requires evaluated qualified freshness ranks",
        )


def _validate_explicit_source_bounds(response: Mapping[str, Any]) -> None:
    bounds = _mapping(response["bounds"], "response.bounds")
    _exact_fields(bounds, {"files"}, "response.bounds")
    files_bound = _validate_collection_bound(
        bounds["files"],
        "response.bounds.files",
    )
    omitted = response["omitted_files"]
    if len(set(omitted)) != len(omitted):
        raise ContextPacketMalformedError(
            "response.omitted_files",
            "must contain unique source paths",
        )
    omitted_paths = set(omitted)
    downgraded_paths = set(response["downgraded_files"])
    if downgraded_paths & omitted_paths:
        raise ContextPacketMalformedError(
            "response.downgraded_files",
            "must not include omitted source paths",
        )
    if files_bound["total"] - files_bound["returned"] != len(omitted):
        raise ContextPacketMalformedError(
            "response.bounds.files",
            "must account exactly for returned and omitted source files",
        )
    files = response.get("files")
    if isinstance(files, Mapping):
        returned_paths = set(files)
        if len(files) != files_bound["returned"]:
            raise ContextPacketMalformedError(
                "response.bounds.files.returned",
                "must match the returned files collection",
            )
        if returned_paths & omitted_paths:
            raise ContextPacketMalformedError(
                "response.omitted_files",
                "must be disjoint from returned source files",
            )
        if not downgraded_paths <= returned_paths:
            raise ContextPacketMalformedError(
                "response.downgraded_files",
                "must be a subset of returned source files",
            )
        if files_bound["total"] != len(returned_paths | omitted_paths):
            raise ContextPacketMalformedError(
                "response.bounds.files.total",
                "must count unique returned and omitted source files",
            )
    elif len(downgraded_paths) > files_bound["returned"]:
        raise ContextPacketMalformedError(
            "response.downgraded_files",
            "cannot exceed the returned source-file bound",
        )
    expected_truncated = bool(omitted or response["downgraded_files"])
    if response["truncated"] is not expected_truncated:
        raise ContextPacketMalformedError(
            "response.truncated",
            "must disclose omitted or downgraded source files",
        )


def _explicit_response_source_priorities(
    response: Mapping[str, Any],
) -> dict[str, str]:
    bound = _mapping(response.get("source_priorities"), "response.source_priorities")
    priorities: dict[str, str] = {}
    for path, priority in bound.items():
        _repository_path(path, f"response.source_priorities.{path}")
        if priority not in {"high", "medium", "low"}:
            raise ContextPacketMalformedError(
                f"response.source_priorities.{path}",
                "must be high, medium, or low",
            )
        priorities[path] = priority
    files = response.get("files")
    if not isinstance(files, Mapping):
        files_bound = _mapping(response["bounds"], "response.bounds")["files"]
        if len(priorities) != files_bound["total"] or not set(
            response["omitted_files"]
        ) <= set(priorities):
            raise ContextPacketMalformedError(
                "response.source_priorities",
                "must bind every classified source path in Markdown responses",
            )
        return priorities
    file_priorities: dict[str, str] = {}
    for path, value in files.items():
        if not isinstance(path, str) or not isinstance(value, Mapping):
            raise ContextPacketMalformedError(
                "response.files",
                "must map source paths to file payload objects",
            )
        priority = value.get("priority")
        if priority not in {"high", "medium", "low"}:
            raise ContextPacketMalformedError(
                f"response.files.{path}.priority",
                "must be high, medium, or low",
            )
        file_priorities[path] = priority
    expected_paths = set(files) | set(response["omitted_files"])
    if set(priorities) != expected_paths or any(
        priorities[path] != priority for path, priority in file_priorities.items()
    ):
        raise ContextPacketMalformedError(
            "response.source_priorities",
            "must exactly bind every classified source path and returned priority",
        )
    return priorities


def _validate_basis(value: Any, packet_contract: _PacketWireContract) -> None:
    data = _mapping(value, "basis")
    _exact_fields(
        data,
        {"source_snapshot", "repository", "knowledge", "generator", "freshness"},
        "basis",
    )
    source = _mapping(data["source_snapshot"], "basis.source_snapshot")
    _exact_fields(source, {"identity", "input_count"}, "basis.source_snapshot")
    if not is_valid_sha256(source["identity"]):
        raise ContextPacketMalformedError(
            "basis.source_snapshot.identity",
            "must be a canonical lowercase SHA-256 value",
        )
    _nonnegative_integer(source["input_count"], "basis.source_snapshot.input_count")
    _validate_repository_basis(data["repository"])
    _validate_knowledge_basis(data["knowledge"], packet_contract)
    generator = _mapping(data["generator"], "basis.generator")
    _exact_fields(
        generator,
        {"component", "version", "context_protocol", "policy_digest"},
        "basis.generator",
    )
    if generator["component"] != "agent-wiki-cli":
        raise ContextPacketMalformedError(
            "basis.generator.component",
            "must be 'agent-wiki-cli'",
        )
    if (
        not isinstance(generator["version"], str)
        or not generator["version"]
        or generator["context_protocol"] != packet_contract.context_protocol
        or generator["policy_digest"]
        != _context_policy_digest(packet_contract.schema_version)
    ):
        raise ContextPacketMalformedError(
            "basis.generator",
            "contains an invalid generator binding",
        )
    _validate_freshness_basis(data["freshness"], packet_contract)
    incompatible_basis = (
        packet_contract is _KNOWLEDGE_PACKET_CONTRACT
        and data["knowledge"].get("state") == "unavailable"
        and data["knowledge"].get("availability") == "degraded"
        and data["knowledge"].get("reason") == "knowledge-basis-incompatible"
    )
    incompatible_freshness = (
        data["freshness"].get("evaluated") is False
        and data["freshness"].get("reason") == "knowledge-basis-incompatible"
    )
    if incompatible_basis is not incompatible_freshness:
        raise ContextPacketMalformedError(
            "basis.freshness",
            "must disclose an incompatible selection basis exactly once",
        )
    if (
        data["freshness"]["evaluated"] is True
        and data["knowledge"]["state"] != "recorded"
    ):
        raise ContextPacketMalformedError(
            "basis.freshness",
            "evaluated freshness requires a recorded knowledge envelope",
        )


def _validate_repository_basis(value: Any) -> None:
    data = _mapping(value, "basis.repository")
    state = data.get("state")
    if state == "unavailable":
        _exact_fields(
            data,
            {"state", "reason"},
            "basis.repository",
        )
        if data["reason"] != "native-knowledge-envelope-unavailable":
            raise ContextPacketMalformedError(
                "basis.repository.reason",
                "is not a supported unavailable reason",
            )
        return
    if state != "recorded":
        raise ContextPacketMalformedError(
            "basis.repository.state",
            "must be 'recorded' or 'unavailable'",
        )
    _exact_fields(
        data,
        {"state", "identity", "evaluated_revision", "working_tree"},
        "basis.repository",
    )
    if not all(
        isinstance(data[name], str) and data[name]
        for name in ("identity", "evaluated_revision", "working_tree")
    ):
        raise ContextPacketMalformedError(
            "basis.repository",
            "recorded fields must be non-empty strings",
        )


def _validate_knowledge_basis(
    value: Any,
    packet_contract: _PacketWireContract,
) -> None:
    data = _mapping(value, "basis.knowledge")
    state = data.get("state")
    base = {"state", "availability", "reason"}
    if state == "unavailable":
        _exact_fields(data, base, "basis.knowledge")
        if data["availability"] not in {"absent", "degraded", "unsupported"}:
            raise ContextPacketMalformedError(
                "basis.knowledge.availability",
                "must describe an unavailable knowledge state",
            )
        if packet_contract is _KNOWLEDGE_PACKET_CONTRACT:
            allowed_reasons = {
                "absent": {"knowledge-projection-not-present"},
                "degraded": {
                    "governance-missing",
                    "knowledge-basis-incompatible",
                    "policy-selected-surface-only-fallback-after-invalid",
                    "policy-selected-surface-only-fallback-after-mixed-snapshot",
                    "surface-validation-failed",
                },
                "unsupported": {
                    "knowledge-schema-version-unsupported",
                    "manifest-version-unsupported",
                    "surface-schema-version-unsupported",
                },
            }
            if data["reason"] not in allowed_reasons[data["availability"]]:
                raise ContextPacketMalformedError(
                    "basis.knowledge.reason",
                    "does not match the captured knowledge availability",
                )
        return
    if state != "recorded":
        raise ContextPacketMalformedError(
            "basis.knowledge.state",
            "must be 'recorded' or 'unavailable'",
        )
    hashes = {
        "envelope_hash",
        "knowledge_index_hash",
        "surface_index_hash",
    }
    optional = {"governance_hash"}
    _exact_fields(
        data,
        base | hashes | optional,
        "basis.knowledge",
        required=base | hashes,
    )
    if data["availability"] != "ready":
        raise ContextPacketMalformedError(
            "basis.knowledge.availability",
            "recorded knowledge must be ready",
        )
    if (
        packet_contract is _KNOWLEDGE_PACKET_CONTRACT
        and data["reason"] != "all-projection-commitments-match"
    ):
        raise ContextPacketMalformedError(
            "basis.knowledge.reason",
            "recorded knowledge must bind the ready projection reason",
        )
    for name in hashes | ({"governance_hash"} if "governance_hash" in data else set()):
        if not is_valid_sha256(data[name]):
            raise ContextPacketMalformedError(
                f"basis.knowledge.{name}",
                "must be a canonical lowercase SHA-256 value",
            )


def _validate_freshness_basis(
    value: Any,
    packet_contract: _PacketWireContract,
) -> None:
    data = _mapping(value, "basis.freshness")
    evaluated = data.get("evaluated")
    if evaluated is False:
        _exact_fields(
            data,
            {"state", "evaluated", "disclosure", "reason"},
            "basis.freshness",
        )
        snapshot_only = (
            data["state"] == "unevaluated"
            and data["disclosure"] == "unevaluated (snapshot-only read)"
            and data["reason"] == "snapshot-only-read"
        )
        incompatible = (
            packet_contract is _KNOWLEDGE_PACKET_CONTRACT
            and data["state"] == "unevaluated"
            and data["disclosure"] == "unevaluated (knowledge basis incompatible)"
            and data["reason"] == "knowledge-basis-incompatible"
        )
        if not (snapshot_only or incompatible):
            raise ContextPacketMalformedError(
                "basis.freshness",
                "contains inconsistent unevaluated semantics",
            )
        return
    if evaluated is not True:
        raise ContextPacketMalformedError(
            "basis.freshness.evaluated",
            "must be a boolean",
        )
    _exact_fields(
        data,
        {
            "state",
            "evaluated",
            "disclosure",
            "concept_count",
            "counts",
            "evaluation_digest",
        },
        "basis.freshness",
    )
    if data["state"] != "evaluated":
        raise ContextPacketMalformedError(
            "basis.freshness.state",
            "must be 'evaluated'",
        )
    count = _nonnegative_integer(
        data["concept_count"],
        "basis.freshness.concept_count",
    )
    if data["disclosure"] != f"evaluated ({count} concepts)":
        raise ContextPacketMalformedError(
            "basis.freshness.disclosure",
            "must match concept_count exactly",
        )
    counts = _mapping(data["counts"], "basis.freshness.counts")
    expected_states = {state.value for state in ComputedFreshness}
    _exact_fields(counts, expected_states, "basis.freshness.counts")
    parsed_counts = [
        _nonnegative_integer(value, f"basis.freshness.counts.{name}")
        for name, value in counts.items()
    ]
    if sum(parsed_counts) != count:
        raise ContextPacketMalformedError(
            "basis.freshness.counts",
            "must sum to concept_count",
        )
    if not is_valid_sha256(data["evaluation_digest"]):
        raise ContextPacketMalformedError(
            "basis.freshness.evaluation_digest",
            "must be a canonical lowercase SHA-256 value",
        )


def _validate_response_basis_consistency(
    response: Mapping[str, Any],
    basis: Mapping[str, Any],
    request: Mapping[str, Any],
    packet_contract: _PacketWireContract,
) -> None:
    knowledge = response.get("knowledge")
    if knowledge is None:
        if packet_contract is _KNOWLEDGE_PACKET_CONTRACT:
            raise ContextPacketMalformedError(
                "response.knowledge",
                "is required by the explicit packet schema",
            )
        return
    if not isinstance(knowledge, Mapping):
        raise ContextPacketMalformedError(
            "response.knowledge",
            "must be a JSON object",
        )
    expected = basis["knowledge"]
    freshness = basis["freshness"]
    if packet_contract is _LEGACY_PACKET_CONTRACT:
        if (
            knowledge.get("availability") != expected["availability"]
            or knowledge.get("reason") != expected["reason"]
            or knowledge.get("freshness_evaluated") is not freshness["evaluated"]
            or knowledge.get("freshness") != freshness["disclosure"]
        ):
            raise ContextPacketMalformedError(
                "response.knowledge",
                "must match the packet knowledge and freshness basis",
            )
        return

    mode = request["knowledge_mode"]
    if mode == "off":
        # The basis always captures actual provenance; disabled selection must
        # not rewrite it to a synthetic not-requested state.
        return
    if knowledge.get("freshness_evaluated") is not freshness["evaluated"]:
        raise ContextPacketMalformedError(
            "response.knowledge.freshness_evaluated",
            "must match the captured freshness basis",
        )
    response_availability = knowledge.get("availability")
    response_reason = knowledge.get("reason")
    if response_availability == "ready":
        if expected["state"] != "recorded" or expected["availability"] != "ready":
            raise ContextPacketMalformedError(
                "response.knowledge.availability",
                "ready selection requires a recorded ready packet basis",
            )
    elif response_availability in {"absent", "unsupported"}:
        if (
            expected["state"] != "unavailable"
            or expected["availability"] != response_availability
        ):
            raise ContextPacketMalformedError(
                "response.knowledge.availability",
                "must match the unavailable packet basis",
            )
        if (
            response_availability == "absent"
            and response_reason != "knowledge-projection-not-present"
        ) or (
            response_availability == "unsupported"
            and response_reason != "knowledge-schema-version-unsupported"
        ):
            raise ContextPacketMalformedError(
                "response.knowledge.reason",
                "does not match the unavailable packet basis",
            )
    elif response_availability == "degraded":
        permitted_basis = expected["availability"] == "degraded" or (
            expected["state"] == "recorded"
            and response_reason
            in {
                "governance-missing",
                "knowledge-basis-incompatible",
                "knowledge-result-exceeds-size-limit",
            }
        )
        if not permitted_basis:
            raise ContextPacketMalformedError(
                "response.knowledge.availability",
                "degraded selection is not supported by the packet basis",
            )
        direct_reason_match = response_reason == expected["reason"]
        qualified_reason_match = (
            response_reason == "surface-validation-failed"
            and expected["reason"]
            == "policy-selected-surface-only-fallback-after-invalid"
        ) or response_reason in {
            "governance-missing",
            "knowledge-basis-incompatible",
            "knowledge-result-exceeds-size-limit",
        }
        if not (direct_reason_match or qualified_reason_match):
            raise ContextPacketMalformedError(
                "response.knowledge.reason",
                "does not map to the captured degraded basis reason",
            )
    else:
        raise ContextPacketMalformedError(
            "response.knowledge.availability",
            "does not match a captured knowledge basis",
        )

    if knowledge.get("status") != "selected":
        return
    bounds = knowledge["bounds"]
    if any(item["truncated"] for item in bounds.values()):
        expected_reason = "knowledge-results-truncated"
    elif any(
        concept["freshness"]["state"] in {"source-changed", "source-missing"}
        for concept in knowledge["selection"]["concepts"]
    ):
        expected_reason = "knowledge-source-changed"
    elif not freshness["evaluated"]:
        expected_reason = "knowledge-snapshot-only"
    else:
        expected_reason = "knowledge-ready"
    if response_reason != expected_reason:
        raise ContextPacketMalformedError(
            "response.knowledge.reason",
            "does not follow captured qualifier precedence",
        )
    if freshness["evaluated"]:
        selected_counts = {state.value: 0 for state in ComputedFreshness}
        for concept in knowledge["selection"]["concepts"]:
            state = concept["freshness"]["state"]
            selected_counts[state] += 1
        for state, count in selected_counts.items():
            if count > freshness["counts"][state]:
                raise ContextPacketMalformedError(
                    "response.knowledge.selection.concepts",
                    "freshness states exceed the captured aggregate basis",
                )


def _validate_delivery(
    value: Any,
    response: Mapping[str, Any],
    basis: Mapping[str, Any],
) -> None:
    data = _mapping(value, "delivery")
    _exact_fields(
        data,
        {"bounds", "truncated", "warnings", "limitations"},
        "delivery",
    )
    if (
        data["bounds"] != response["bounds"]
        or data["truncated"] is not response["truncated"]
        or data["warnings"] != response.get("warnings", [])
    ):
        raise ContextPacketMalformedError(
            "delivery",
            "must exactly project response bounds, truncation, and warnings",
        )
    limitations = _string_list(data["limitations"], "delivery.limitations")
    if limitations != sorted(set(limitations)) or any(
        _LIMITATION_RE.fullmatch(item) is None for item in limitations
    ):
        raise ContextPacketMalformedError(
            "delivery.limitations",
            "must contain sorted unique lowercase machine codes",
        )
    if limitations != _packet_limitations(response, basis):
        raise ContextPacketMalformedError(
            "delivery.limitations",
            "must match the declared response and evidence basis",
        )


def _validate_path_policy_shape(value: Any) -> None:
    data = _mapping(value, "path_policy")
    _exact_fields(
        data,
        {
            "policy_version",
            "policy_digest",
            "field_counts",
            "finding_counts",
            "quarantined",
            "final_scan",
            "limitations",
        },
        "path_policy",
    )
    if (
        data["policy_version"] != CONTEXT_PACKET_PATH_POLICY_VERSION
        or data["policy_digest"] != _path_policy_digest()
        or data["quarantined"] is not False
        or data["final_scan"] != "passed"
        or data["limitations"]
        != ["does-not-establish-absence-of-arbitrary-sensitive-content"]
    ):
        raise ContextPacketMalformedError(
            "path_policy",
            "contains unsupported policy semantics",
        )
    counts = _mapping(data["field_counts"], "path_policy.field_counts")
    _exact_fields(counts, set(_PATH_COUNT_KEYS), "path_policy.field_counts")
    for name, count in counts.items():
        _nonnegative_integer(count, f"path_policy.field_counts.{name}")
    findings = _mapping(data["finding_counts"], "path_policy.finding_counts")
    _exact_fields(
        findings,
        {"accepted", "redacted", "rejected"},
        "path_policy.finding_counts",
    )
    for name, count in findings.items():
        _nonnegative_integer(count, f"path_policy.finding_counts.{name}")
    if findings["redacted"] != 0 or findings["rejected"] != 0:
        raise ContextPacketMalformedError(
            "path_policy.finding_counts",
            "a returned packet cannot contain redacted or rejected findings",
        )


def _mapping(value: Any, field: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping) or any(not isinstance(key, str) for key in value):
        raise ContextPacketMalformedError(field, "must be a JSON object")
    return value


def _exact_fields(
    value: Mapping[str, Any],
    allowed: set[str] | frozenset[str],
    field: str,
    *,
    required: set[str] | frozenset[str] | None = None,
) -> None:
    expected_required = set(allowed if required is None else required)
    missing = sorted(expected_required - set(value))
    if missing:
        raise ContextPacketMalformedError(
            f"{field}.{missing[0]}",
            "is required",
        )
    unknown = sorted(set(value) - set(allowed))
    if unknown:
        raise ContextPacketMalformedError(
            f"{field}.{unknown[0]}",
            "is not supported",
        )


def _string_list(value: Any, field: str) -> list[str]:
    if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
        raise ContextPacketMalformedError(field, "must be an array of strings")
    return value


def _object_list(value: Any, field: str) -> list[Mapping[str, Any]]:
    if not isinstance(value, list):
        raise ContextPacketMalformedError(field, "must be an array of objects")
    result: list[Mapping[str, Any]] = []
    for index, item in enumerate(value):
        result.append(_mapping(item, f"{field}[{index}]"))
    return result


def _stable_code(value: Any, field: str) -> str:
    if not isinstance(value, str) or _LIMITATION_RE.fullmatch(value) is None:
        raise ContextPacketMalformedError(
            field,
            "must be a non-empty lowercase hyphenated code",
        )
    return value


def _nonnegative_integer(value: Any, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ContextPacketMalformedError(
            field,
            "must be a non-negative integer",
        )
    return value


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


def _assert_source_unchanged(snapshot: SourceSnapshot, expected_anchor: str) -> None:
    try:
        unchanged = (
            _source_anchor(snapshot) == expected_anchor
            and source_snapshot_matches_current_files(snapshot)
        )
    except (OSError, SourceSnapshotError, ValueError) as exc:
        raise ContextPacketSourceMutationError("source") from exc
    if not unchanged:
        raise ContextPacketSourceMutationError("source")


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
    changed = context_service._selected_git_changed_files(
        str(captured.source_root),
        captured.source_snapshot,
    )
    current = None if changed is None else tuple(changed)
    if current != captured.changed_files:
        raise ContextPacketSourceMutationError("source-selection")


def _wiki_anchor(root: Path, *, reject_all_symlinks: bool = False) -> str:
    if not root.exists():
        return _domain_hash(_WIKI_ANCHOR_DOMAIN, {"state": "absent"})
    records: list[dict[str, str]] = []

    def walk(directory: Path, relative: Path) -> None:
        try:
            entries = sorted(
                os.scandir(directory),
                key=lambda entry: (entry.name.casefold(), entry.name),
            )
        except OSError as exc:
            raise ContextPacketSourceMutationError("wiki") from exc
        for entry in entries:
            rel_path = (relative / entry.name).as_posix()
            try:
                if entry.is_symlink():
                    if reject_all_symlinks or _wiki_symlink_is_captured_input(rel_path):
                        raise ContextPacketPathPolicyError(
                            "wiki_dir",
                            "wiki symlinks are not permitted for qualified context "
                            f"reads: {rel_path!r}",
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
                    content = Path(entry.path).read_bytes()
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
    return _domain_hash(_WIKI_ANCHOR_DOMAIN, {"state": "present", "entries": records})


def _wiki_symlink_is_captured_input(relative_path: str) -> bool:
    if relative_path in {
        ".llm-wiki-governance.json",
        ".llm-wiki-knowledge.json",
        ".llm-wiki-manifest.json",
        ".llm-wiki-surface.json",
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
) -> None:
    try:
        current_anchor = (
            _wiki_anchor(root, reject_all_symlinks=True)
            if reject_all_symlinks
            else _wiki_anchor(root)
        )
    except ContextPacketPathPolicyError as exc:
        raise ContextPacketSourceMutationError("wiki") from exc
    if current_anchor != expected_anchor:
        raise ContextPacketSourceMutationError("wiki")


def _domain_hash(domain: str, value: Mapping[str, Any]) -> str:
    return sha256_bytes(
        canonical_json_bytes(
            {
                "domain": domain,
                **value,
            }
        )
    )


def _wire_value(value: Any) -> Any:
    return value.value if isinstance(value, Enum) else value


def _freeze_json(value: Any) -> Any:
    if isinstance(value, Mapping):
        return MappingProxyType(
            {str(key): _freeze_json(child) for key, child in value.items()}
        )
    if isinstance(value, (list, tuple)):
        return tuple(_freeze_json(child) for child in value)
    return value


def _thaw_json(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(key): _thaw_json(child) for key, child in value.items()}
    if isinstance(value, (list, tuple)):
        return [_thaw_json(child) for child in value]
    return value


def _pointer(parts: Sequence[str]) -> str:
    if not parts:
        return "/"
    return "/" + "/".join(
        str(part).replace("~", "~0").replace("/", "~1") for part in parts
    )


__all__ = [
    "CONTEXT_PACKET_ASSURANCE_LEVEL",
    "CONTEXT_PACKET_KNOWLEDGE_POLICY_VERSION",
    "CONTEXT_PACKET_KNOWLEDGE_SCHEMA_VERSION",
    "CONTEXT_PACKET_PATH_POLICY_VERSION",
    "CONTEXT_PACKET_POLICY_VERSION",
    "CONTEXT_PACKET_RECONCILIATION_POLICY",
    "CONTEXT_PACKET_SCHEMA_VERSION",
    "CapturedContextRead",
    "ContextBasisComparison",
    "ContextPacketError",
    "ContextPacketMalformedError",
    "ContextPacketPathPolicyError",
    "ContextPacketReconciliation",
    "ContextPacketSourceMutationError",
    "ContextPacketUnavailableError",
    "ContextPacketValidation",
    "QualifiedContextPacket",
    "build_context_from_captured_read",
    "build_qualified_context",
    "capture_context_read",
    "compare_context_packet_basis",
    "reconcile_context_packet",
    "validate_context_packet",
]
