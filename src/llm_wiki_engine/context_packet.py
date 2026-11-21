"""Qualified Context Packet format: wire contracts and offline validation.

This module decides whether packet bytes are a well-formed, self-consistent
Qualified Context Packet: schema, canonical encoding, digests, path policy,
lineage and declared availability. It reads no repository, wiki or knowledge
state and loads none of the builders, so hosts can check packets without the
analysis stack.

Building packets from a live read, and reconciling a packet with live state,
is the application's work (the ``packet_builders`` integration). Their names
stay importable from here for compatibility and load the builder on first use;
without a builder provider they are absent.
"""

from __future__ import annotations

import json
import math
import re
from urllib.parse import urlsplit
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from types import MappingProxyType
from typing import Any

from llm_wiki_engine import context_request_format
from llm_wiki_engine import wiki_surface
from llm_wiki_engine.contracts import (
    CONTEXT_KNOWLEDGE_PROTOCOL_VERSION,
    QUALIFIED_CONTEXT_PACKET_KNOWLEDGE_SCHEMA_VERSION,
    QUALIFIED_CONTEXT_PACKET_SCHEMA_VERSION,
    TYPED_GRAPH_SCHEMA_VERSION,
)
from llm_wiki_engine.context_request_format import (
    CONTEXT_COVERAGE_LIMITATION_CODE_MAX_LENGTH,
    CONTEXT_COVERAGE_LIMITATION_LIMIT,
)
from llm_wiki_engine.knowledge_evidence import (
    canonical_json_bytes,
    is_valid_sha256,
    sha256_bytes,
)
from llm_wiki_engine.knowledge_envelope import (
    KnowledgeEnvelopeError,
    validate_configured_public_identity,
)
from llm_wiki_engine.knowledge_freshness import (
    KNOWN_FRESHNESS_REASON_CODES,
    REASON_RECORDED_BASIS_MATCHES_LIVE_EVALUATION,
)
from llm_wiki_engine.knowledge_graph import (
    CORE_RELATIONSHIP_KINDS,
    ENDPOINT_KINDS,
    GRAPH_COVERAGE_ANALYZERS,
    GRAPH_EVIDENCE_STATES,
    GRAPH_ORIGINS,
    GRAPH_RESOLUTIONS,
    is_supported_relationship_kind,
)
from llm_wiki_engine.knowledge_model import (
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
from llm_wiki_engine.wiki_media import contains_uri_authority_userinfo
from llm_wiki_engine.packet_field_policy import (
    PUBLIC_URI_FIELDS as _PUBLIC_URI_FIELDS,
    STRUCTURAL_PATH_FIELDS as _STRUCTURAL_PATH_FIELDS,
    STRING_CLASSES as _PATH_COUNT_KEYS,
)
from llm_wiki_engine.validation import require_repository_relative_path


CONTEXT_PACKET_SCHEMA_VERSION = QUALIFIED_CONTEXT_PACKET_SCHEMA_VERSION
CONTEXT_PACKET_KNOWLEDGE_SCHEMA_VERSION = (
    QUALIFIED_CONTEXT_PACKET_KNOWLEDGE_SCHEMA_VERSION
)
CONTEXT_PACKET_ASSURANCE_LEVEL = "content-integrity"
CONTEXT_PACKET_POLICY_VERSION = "qualified-context-policy-v1"
CONTEXT_PACKET_KNOWLEDGE_POLICY_VERSION = "qualified-context-policy-v2"
CONTEXT_PACKET_PATH_POLICY_VERSION = "qualified-context-path-policy-v1"

_PACKET_DIGEST_DOMAIN = b"llm-wiki-qualified-context-packet/v1\x00"
_KNOWLEDGE_PACKET_DIGEST_DOMAIN = b"llm-wiki-qualified-context-packet/v2\x00"
_POLICY_DIGEST_DOMAIN = "llm-wiki/qualified-context-policy/v1"
_KNOWLEDGE_POLICY_DIGEST_DOMAIN = "llm-wiki/qualified-context-policy/v2"
_PATH_POLICY_DIGEST_DOMAIN = "llm-wiki/qualified-context-path-policy/v1"

_MAX_PACKET_BYTES = 16 * 1024 * 1024
_MAX_JSON_DEPTH = 64
_MAX_JSON_ITEMS = 250_000
_MAX_TEXT_LENGTH = 2 * 1024 * 1024
_MAX_NORMALIZED_CONTEXT_TARGET_LENGTH = 2048
_MAX_KNOWLEDGE_CONCEPTS = context_request_format.CONTEXT_KNOWLEDGE_CONCEPT_LIMIT
_MAX_KNOWLEDGE_PAGES = context_request_format.CONTEXT_KNOWLEDGE_PAGE_LIMIT
_MAX_KNOWLEDGE_RELATIONSHIPS = context_request_format.CONTEXT_KNOWLEDGE_RELATIONSHIP_LIMIT
_MAX_KNOWLEDGE_PACKET_BYTES = 2 * 1024 * 1024
_LIMITATION_RE = re.compile(r"^[a-z][a-z0-9]*(?:-[a-z0-9]+)*$")
_COVERAGE_LIMITATION_RE = re.compile(r"^[a-z][a-z0-9]*(?:[/-][a-z0-9]+)*$")
_PORTABLE_URI_RE = re.compile(r"^[A-Za-z][A-Za-z0-9+.-]*:[^\x00-\x20]*$")
_RFC3986_URI_RE = re.compile(r"^[A-Za-z0-9._~:/?#\[\]@!$&'()*+,;=%-]+$")
_WINDOWS_ABSOLUTE_RE = re.compile(r"^[A-Za-z]:[\\/]")
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
    context_protocol=context_request_format.PROTOCOL_VERSION,
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

    def __init__(self, field: str, message: str, *, code: str | None = None):
        self.field = field
        self.message = message
        if code is not None:
            self.code = code
        super().__init__(f"{field}: {message}")


class ContextPacketPathPolicyError(ContextPacketError):
    """A structural packet field violates its declared path policy."""

    code = "context-packet-path-policy-rejected"

    def __init__(self, field: str, message: str, *, relative_path: str | None = None):
        self.field = field
        self.relative_path = relative_path
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
            code="unsupported-context-packet",
        )
    return contract


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
                "context_protocol": context_request_format.PROTOCOL_VERSION,
                "context_query_limit": context_request_format._CONTEXT_QUERY_LIMIT,
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
            "context_query_limit": context_request_format._CONTEXT_QUERY_LIMIT,
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
    from llm_wiki_engine.packet_field_policy import (
        UnclassifiedPacketField, classify_string, validate_field_coverage,
    )

    try:
        validate_field_coverage(value)
    except UnclassifiedPacketField as exc:
        raise ContextPacketPathPolicyError(
            _pointer(exc.pointer), "has no declared packet field classification"
        ) from exc
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
        classification = classify_string(pointer)
        if classification == "repository_relative_paths":
            _repository_path(item, _pointer(pointer))
            counts["repository_relative_paths"] += 1
        elif classification == "public_uris":
            if _PORTABLE_URI_RE.fullmatch(item) is None or item.casefold().startswith(
                "file:"
            ):
                raise ContextPacketPathPolicyError(
                    _pointer(pointer),
                    "must be a portable non-file URI",
                )
            counts["public_uris"] += 1
        elif classification == "portable_identities":
            if item != "unknown":
                try:
                    validate_configured_public_identity(item)
                except KnowledgeEnvelopeError as exc:
                    raise ContextPacketPathPolicyError(
                        _pointer(pointer),
                        "must be a normalized portable repository identity",
                    ) from exc
            counts["portable_identities"] += 1
        elif classification == "free_text_values":
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
        normalized = context_request_format._validate_protocol_request(dict(data))
    except context_request_format.ProtocolRequestError as exc:
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
        required | {"selection", "maintenance"},
        "response.knowledge",
        required=required,
    )
    if "maintenance" in data:
        from llm_wiki_engine.maintenance_status import validate_maintenance_summary
        try:
            validate_maintenance_summary(data["maintenance"])
        except (ValueError, TypeError) as exc:
            raise ContextPacketMalformedError("response.knowledge.maintenance", str(exc)) from exc
        if data["mode"] == "off":
            raise ContextPacketMalformedError("response.knowledge.maintenance", "disabled native reads cannot expose ordinary maintenance")
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
    _exact_fields(value, required | {"uid", "implementation", "maintenance"}, field, required=required)
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
    if "implementation" in value:
        _validate_implementation_summary(
            value["implementation"], f"{field}.implementation"
        )
    if "maintenance" in value:
        from llm_wiki_engine.maintenance_status import validate_maintenance_summary
        try:
            validate_maintenance_summary(value["maintenance"])
        except (ValueError, TypeError) as exc:
            raise ContextPacketMalformedError(f"{field}.maintenance", str(exc)) from exc
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


def _validate_implementation_summary(value: Any, field: str) -> None:
    """Validate curated syntax evidence without admitting raw native records."""
    from .implementation_summary import validate_implementation_summary

    try:
        validate_implementation_summary(value)
    except (TypeError, ValueError) as exc:
        raise ContextPacketMalformedError(field, str(exc)) from exc


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


def _domain_hash(domain: str, value: Mapping[str, Any]) -> str:
    return sha256_bytes(
        canonical_json_bytes(
            {
                "domain": domain,
                **value,
            }
        )
    )


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



#: Builder names still importable from this module (see the module docstring).
_BUILDER_NAMES = frozenset(
    {
        "CONTEXT_PACKET_RECONCILIATION_POLICY",
        "CapturedContextRead",
        "ContextBasisComparison",
        "ContextPacketAuthorityError",
        "ContextPacketReconciliation",
        "ContextPacketSourceMutationError",
        "ContextPacketUnavailableError",
        "_CAPTURE_GUARDS",
        "_FRESHNESS_DIGEST_DOMAIN",
        "_RECONCILIATION_FACETS",
        "_RECONCILIATION_FACET_FIELDS",
        "_SOURCE_ANCHOR_DOMAIN",
        "_WIKI_ANCHOR_DOMAIN",
        "_assert_selection_unchanged",
        "_assert_source_inputs_unchanged",
        "_assert_source_unchanged",
        "_assert_wiki_integrity",
        "_assert_wiki_unchanged",
        "_build_knowledge_context_from_captured_read",
        "_build_legacy_context_from_captured_read",
        "_build_protocol_enrichment_from_captured_read",
        "_candidate_packet_size",
        "_captured_query_service",
        "_captured_source_classification",
        "_captured_source_payload",
        "_explicit_filter_enrichment_from_captured_read",
        "_fit_knowledge_packet_response",
        "_freshness_basis",
        "_guard_windows_inputs",
        "_guarded_capture",
        "_is_free_text_pointer",
        "_live_facet",
        "_normalized_request",
        "_packet_basis",
        "_packet_body",
        "_packet_contract_for_request",
        "_reconcile_packet_views",
        "_reconciliation_facets",
        "_set_knowledge_collection_prefix",
        "_source_anchor",
        "_source_snapshot_anchor_payload",
        "_unevaluated_facet",
        "_validate_reconciliation_contract",
        "_wiki_anchor",
        "_wiki_symlink_is_captured_input",
        "_wire_value",
        "build_context_from_captured_read",
        "build_qualified_context",
        "capture_context_read",
        "compare_context_packet_basis",
        "confirmed_missing_source_paths",
        "describe_context_packet_error",
        "packet_from_captured_response",
        "reconcile_context_packet",
    }
)


def __getattr__(name: str) -> Any:
    if name in _BUILDER_NAMES:
        from .integrations import IntegrationUnavailable, provider

        try:
            builders = provider("packet_builders")
        except IntegrationUnavailable as exc:
            raise AttributeError(f"module {__name__!r} has no attribute {name!r}: {exc}") from None
        return getattr(builders, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    "CONTEXT_PACKET_ASSURANCE_LEVEL",
    "CONTEXT_PACKET_KNOWLEDGE_POLICY_VERSION",
    "CONTEXT_PACKET_KNOWLEDGE_SCHEMA_VERSION",
    "CONTEXT_PACKET_PATH_POLICY_VERSION",
    "CONTEXT_PACKET_POLICY_VERSION",
    "CONTEXT_PACKET_SCHEMA_VERSION",
    "ContextPacketError",
    "ContextPacketMalformedError",
    "ContextPacketPathPolicyError",
    "ContextPacketValidation",
    "QualifiedContextPacket",
    "validate_context_packet",
]
