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

import hashlib
import json
import math
import os
import re
from collections.abc import Mapping, Sequence
from copy import deepcopy
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from types import MappingProxyType
from typing import Any

from .. import __version__
from ..config import DEFAULT_WIKI_DIR, PathValidationError, validate_path
from . import context_service
from .contracts import QUALIFIED_CONTEXT_PACKET_SCHEMA_VERSION
from .dependencies import analyze_dependencies
from .documentation_queries import (
    DocumentationGraphQueryService,
    DocumentationQueryError,
)
from .extraction_jobs import ExtractionJobRequest
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
from .knowledge_model import ComputedFreshness
from .knowledge_observability import knowledge_freshness_disclosure
from .knowledge_verification import verification_summaries_for_concepts
from .source_snapshot import (
    SourceSnapshot,
    SourceSnapshotError,
    build_source_snapshot,
)
from .validation import require_repository_relative_path
from .wiki_surface_index import SurfaceIndexEvaluation, evaluate_surface_index


CONTEXT_PACKET_SCHEMA_VERSION = QUALIFIED_CONTEXT_PACKET_SCHEMA_VERSION
CONTEXT_PACKET_ASSURANCE_LEVEL = "content-integrity"
CONTEXT_PACKET_POLICY_VERSION = "qualified-context-policy-v1"
CONTEXT_PACKET_PATH_POLICY_VERSION = "qualified-context-path-policy-v1"
CONTEXT_PACKET_RECONCILIATION_POLICY = "qualified-context-complete-policy-v1"

_PACKET_DIGEST_DOMAIN = b"llm-wiki-qualified-context-packet/v1\x00"
_POLICY_DIGEST_DOMAIN = "llm-wiki/qualified-context-policy/v1"
_PATH_POLICY_DIGEST_DOMAIN = "llm-wiki/qualified-context-path-policy/v1"
_SOURCE_ANCHOR_DOMAIN = "llm-wiki/qualified-context-source-anchor/v1"
_WIKI_ANCHOR_DOMAIN = "llm-wiki/qualified-context-wiki-anchor/v1"
_FRESHNESS_DIGEST_DOMAIN = "llm-wiki/qualified-context-freshness/v1"

_MAX_PACKET_BYTES = 16 * 1024 * 1024
_MAX_JSON_DEPTH = 64
_MAX_JSON_ITEMS = 250_000
_MAX_TEXT_LENGTH = 2 * 1024 * 1024
_LIMITATION_RE = re.compile(r"^[a-z][a-z0-9]*(?:-[a-z0-9]+)*$")
_PORTABLE_URI_RE = re.compile(r"^[A-Za-z][A-Za-z0-9+.-]*:[^\x00-\x20]*$")
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
        if not is_valid_sha256(self.source_anchor):
            raise ValueError("source_anchor must be a canonical SHA-256 value")
        if not is_valid_sha256(self.wiki_anchor):
            raise ValueError("wiki_anchor must be a canonical SHA-256 value")


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
                "value": self.packet.to_payload()["basis"]["knowledge"][
                    "availability"
                ],
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
            raise ValueError(
                f"facets.{name}.{unknown_fields[0]} is not supported"
            )
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
            raise ValueError(
                f"facets.{name}.current must be true, false, or null"
            )
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
        raise ValueError(
            "aggregate state and current must match all required facets"
        )

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
    plan_reporter: Any | None = None,
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

    try:
        source_root = context_service.validate_source_root(
            src_dir,
            "--src-dir",
            allow_external=allow_external_src,
        )
        wiki_root = validate_path(wiki_dir, "--wiki-dir")
    except PathValidationError:
        raise

    wiki_anchor_before = _wiki_anchor(wiki_root)
    collected = context_service.get_inventory(
        str(source_root),
        deep=True,
        return_result=True,
        job_request=job_request,
        plan_reporter=plan_reporter,
        include_plugins=False,
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
    _assert_source_unchanged(source_snapshot, source_anchor)

    try:
        entrypoints = tuple(
            context_service.get_entry_points(
                inventory,
                console_scripts=context_service.read_console_scripts(
                    str(source_root)
                ),
                root=source_root,
                fallback_root=Path.cwd(),
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
    except OSError as exc:
        raise context_service.ProtocolRequestError(
            f"Could not capture context read view: {exc}",
            "wiki_dir",
        ) from exc

    wiki_anchor_after = _wiki_anchor(wiki_root)
    if wiki_anchor_before != wiki_anchor_after:
        raise ContextPacketSourceMutationError("wiki")
    _assert_source_unchanged(source_snapshot, source_anchor)

    changed = context_service._git_changed_files(str(source_root))
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
    )


def build_context_from_captured_read(
    captured: CapturedContextRead,
    request: Mapping[str, Any],
) -> tuple[dict[str, Any], list[str]]:
    """Build the existing context payload solely from one captured read."""

    if not isinstance(captured, CapturedContextRead):
        raise TypeError("captured must be a CapturedContextRead")
    normalized = _normalized_request(request)
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


def build_qualified_context(
    src_dir: str = ".",
    wiki_dir: str = DEFAULT_WIKI_DIR,
    request: Mapping[str, Any] | None = None,
    *,
    allow_external_src: bool = False,
    read_only: bool = True,
    job_request: ExtractionJobRequest | None = None,
    plan_reporter: Any | None = None,
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
    captured = capture_context_read(
        src_dir,
        wiki_dir,
        allow_external_src=allow_external_src,
        read_only=read_only,
        job_request=job_request,
        plan_reporter=plan_reporter,
    )
    payload, warnings = build_context_from_captured_read(captured, normalized)
    response = context_service._protocol_success_payload(
        normalized,
        payload,
        warnings,
    )
    body = _packet_body(captured, normalized, response)

    _assert_source_unchanged(captured.source_snapshot, captured.source_anchor)
    if _wiki_anchor(captured.wiki_root) != captured.wiki_anchor:
        raise ContextPacketSourceMutationError("wiki")
    _assert_selection_unchanged(captured)

    semantic_body = {
        "schema_version": CONTEXT_PACKET_SCHEMA_VERSION,
        **body,
    }
    packet_id = _packet_id(semantic_body)
    packet_payload = {
        "schema_version": CONTEXT_PACKET_SCHEMA_VERSION,
        "packet_id": packet_id,
        **body,
    }
    canonical = _encode_packet_payload(packet_payload)
    validated = validate_context_packet(canonical)
    return validated.packet


def validate_context_packet(
    packet_bytes: bytes | bytearray | memoryview,
) -> ContextPacketValidation:
    """Strictly validate canonical bytes without performing live reads."""

    raw = _coerce_packet_bytes(packet_bytes)
    payload = _strict_json_payload(raw)
    _validate_packet_shape(payload)
    canonical = _encode_packet_payload(payload)
    if canonical != raw:
        raise ContextPacketMalformedError(
            "packet_bytes",
            "must use the canonical sorted-key UTF-8 JSON encoding with one LF",
        )

    packet_id = payload["packet_id"]
    semantic_body = {
        key: value
        for key, value in payload.items()
        if key != "packet_id"
    }
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
    plan_reporter: Any | None = None,
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
    )
    live_payload = live_packet.to_payload()
    facets = _reconciliation_facets(packet_payload, live_payload)
    required_states = {
        name: facets[name]["current"] for name in _RECONCILIATION_FACETS
    }
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

    concept_filter_requested = bool(
        context_service._CONCEPT_FILTER_KEYS & set(filters)
    ) or prefer_fresh
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
            enrichment["ranking_policy"] = (
                context_service._freshness_ranking_policy(
                    knowledge_status,
                    freshness_rank_by_source,
                )
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
    candidate.setdefault("protocol", context_service.PROTOCOL_VERSION)
    candidate.setdefault("filters", {})
    return context_service._validate_protocol_request(candidate)


def _packet_body(
    captured: CapturedContextRead,
    request: Mapping[str, Any],
    response: Mapping[str, Any],
) -> dict[str, Any]:
    basis = _packet_basis(captured)
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


def _packet_basis(captured: CapturedContextRead) -> dict[str, Any]:
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
            "context_protocol": context_service.PROTOCOL_VERSION,
            "policy_digest": _context_policy_digest(),
        },
        "freshness": _freshness_basis(view),
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
        state.value: int(view.freshness.counts[state])
        for state in ComputedFreshness
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
    freshness = basis["freshness"]
    if freshness["evaluated"] is False:
        limitations.add("freshness-not-evaluated")
    knowledge = basis["knowledge"]
    if knowledge["state"] == "unavailable":
        availability = knowledge["availability"]
        if availability in {"absent", "degraded", "unsupported"}:
            limitations.add(f"knowledge-{availability}")
    return sorted(limitations)


def _context_policy_digest() -> str:
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
            if (
                _PORTABLE_URI_RE.fullmatch(item) is None
                or item.casefold().startswith("file:")
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
        "limitations": [
            "does-not-establish-absence-of-arbitrary-sensitive-content"
        ],
    }


def _mapping_key_is_repository_path(pointer: tuple[str, ...]) -> bool:
    return pointer in {
        ("response", "files"),
        ("response", "downgraded_files"),
    }


def _list_item_is_repository_path(pointer: tuple[str, ...]) -> bool:
    return pointer == ("response", "omitted_files")


def _is_free_text_pointer(pointer: tuple[str, ...]) -> bool:
    return (
        pointer[:2] in {("delivery", "warnings"), ("response", "warnings")}
        or pointer[:2] == ("delivery", "limitations")
    )


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
    if (
        isinstance(value, str)
        and (
            value.startswith(("/", "\\", "~"))
            or _WINDOWS_ABSOLUTE_RE.match(value)
            or value.casefold().startswith("file:")
        )
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
        {
            name: packet_knowledge[name]
            for name in ("state", "availability", "reason")
        },
        {
            name: live_knowledge[name]
            for name in ("state", "availability", "reason")
        },
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
        "reason": (
            "live-facet-matches-packet" if matches else mismatch_reason
        ),
    }


def _unevaluated_facet(matches: bool, reason: str) -> dict[str, Any]:
    return {
        "matches_expected": matches,
        "current": None,
        "state": "unevaluated",
        "reason": reason,
    }


def _packet_id(body: Mapping[str, Any]) -> str:
    return sha256_bytes(_PACKET_DIGEST_DOMAIN + canonical_json_bytes(body))


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


def _validate_packet_shape(payload: Mapping[str, Any]) -> None:
    _exact_fields(payload, _PACKET_TOP_LEVEL_FIELDS, "packet")
    if payload["schema_version"] != CONTEXT_PACKET_SCHEMA_VERSION:
        raise ContextPacketMalformedError(
            "schema_version",
            f"must be {CONTEXT_PACKET_SCHEMA_VERSION!r}",
        )
    if not is_valid_sha256(payload["packet_id"]):
        raise ContextPacketMalformedError(
            "packet_id",
            "must be a canonical lowercase SHA-256 value",
        )
    _validate_assurance(payload["assurance"])
    request = _validate_packet_request(payload["request"])
    _validate_response(payload["response"], request)
    _validate_basis(payload["basis"])
    _validate_response_basis_consistency(payload["response"], payload["basis"])
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


def _validate_packet_request(value: Any) -> dict[str, Any]:
    data = _mapping(value, "request")
    try:
        return context_service._validate_protocol_request(dict(data))
    except context_service.ProtocolRequestError as exc:
        raise ContextPacketMalformedError(
            f"request.{exc.field or 'request'}",
            str(exc),
        ) from exc


def _validate_response(value: Any, request: Mapping[str, Any]) -> None:
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
    }
    _exact_fields(data, required | optional, "response", required=required)
    if data["protocol"] != context_service.PROTOCOL_VERSION or data["ok"] is not True:
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
        if (
            data.get("prefer_fresh") is not True
            or not isinstance(data.get("ranking_policy"), Mapping)
        ):
            raise ContextPacketMalformedError(
                "response",
                "freshness preference requires its disclosed ranking policy",
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


def _validate_basis(value: Any) -> None:
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
    _validate_knowledge_basis(data["knowledge"])
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
        or generator["context_protocol"] != context_service.PROTOCOL_VERSION
        or generator["policy_digest"] != _context_policy_digest()
    ):
        raise ContextPacketMalformedError(
            "basis.generator",
            "contains an invalid generator binding",
        )
    _validate_freshness_basis(data["freshness"])
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


def _validate_knowledge_basis(value: Any) -> None:
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
    for name in hashes | ({"governance_hash"} if "governance_hash" in data else set()):
        if not is_valid_sha256(data[name]):
            raise ContextPacketMalformedError(
                f"basis.knowledge.{name}",
                "must be a canonical lowercase SHA-256 value",
            )


def _validate_freshness_basis(value: Any) -> None:
    data = _mapping(value, "basis.freshness")
    evaluated = data.get("evaluated")
    if evaluated is False:
        _exact_fields(
            data,
            {"state", "evaluated", "disclosure", "reason"},
            "basis.freshness",
        )
        if (
            data["state"] != "unevaluated"
            or data["disclosure"] != "unevaluated (snapshot-only read)"
            or data["reason"] != "snapshot-only-read"
        ):
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
) -> None:
    knowledge = response.get("knowledge")
    if knowledge is None:
        return
    if not isinstance(knowledge, Mapping):
        raise ContextPacketMalformedError(
            "response.knowledge",
            "must be a JSON object",
        )
    expected = basis["knowledge"]
    freshness = basis["freshness"]
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
    if not isinstance(value, Mapping) or any(
        not isinstance(key, str) for key in value
    ):
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
    if (
        not isinstance(value, list)
        or any(not isinstance(item, str) for item in value)
    ):
        raise ContextPacketMalformedError(field, "must be an array of strings")
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
            path: list(kinds)
            for path, kinds in snapshot.captured_input_kinds.items()
        },
        "language_paths": {
            language: snapshot.language_paths(language)
            for language in sorted(snapshot.files_by_language)
        },
        "unsupported_language_paths": {
            language: snapshot.unsupported_language_paths(language)
            for language in sorted(snapshot.unsupported_files_by_language)
        },
        "dockerfile_paths": [
            item.rel_path for item in snapshot.dockerfile_candidates
        ],
        "compose_paths": [
            item.rel_path for item in snapshot.compose_candidates
        ],
        "yaml_paths": [item.rel_path for item in snapshot.yaml_candidates],
        "package_marker_paths": [
            item.rel_path for item in snapshot.package_markers
        ],
    }


def _assert_source_unchanged(snapshot: SourceSnapshot, expected_anchor: str) -> None:
    try:
        current = build_source_snapshot(snapshot.root)
        missing_built_in_paths = set(snapshot.captured_content_hashes) - set(
            current.captured_content_hashes
        )
        if missing_built_in_paths:
            current = current.with_captured_inventory_paths(
                sorted(missing_built_in_paths)
            )
        current_anchor = _source_anchor(current)
    except (OSError, SourceSnapshotError, ValueError) as exc:
        raise ContextPacketSourceMutationError("source") from exc
    if current_anchor != expected_anchor:
        raise ContextPacketSourceMutationError("source")


def _assert_selection_unchanged(captured: CapturedContextRead) -> None:
    changed = context_service._git_changed_files(str(captured.source_root))
    current = None if changed is None else tuple(changed)
    if current != captured.changed_files:
        raise ContextPacketSourceMutationError("source-selection")


def _wiki_anchor(root: Path) -> str:
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
