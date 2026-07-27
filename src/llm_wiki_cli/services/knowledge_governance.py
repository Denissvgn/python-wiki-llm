"""Durable authority for stable concept identity and explicit governance.

The governance ledger is intentionally narrow.  It stores stable allocations,
historical aliases, lifecycle events, and digest-bound human-review events.
It never stores Markdown, extracted facts, credentials, absolute paths, or a
computed assertion that a review remains valid.

The generated knowledge index is a disposable read projection of this ledger.
This module therefore owns ledger parsing, validation, deterministic state
derivation, optimistic concurrency checks, and durable atomic replacement.
Projection helpers live near the bottom of the module and operate only on
already-validated in-memory knowledge values.
"""

from __future__ import annotations

import json
import os
import re
import stat
import sys
import tempfile
import uuid
from collections import defaultdict
from collections.abc import Iterator, Mapping, Sequence
from contextlib import contextmanager
from dataclasses import dataclass, field, replace
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Callable

from .contracts import (
    GOVERNANCE_EXTENSION_KEY,
    GOVERNANCE_HASH_EXTENSION_KEY,
    GOVERNANCE_SCHEMA_VERSION,
)
from .concept_identity import (
    AliasType,
    ConceptAllocation,
    ConceptIdentityError,
    derive_concept_uid as _derive_identity_uid,
    identity_coordinate_key,
    validate_alias_value,
    validate_bundle_id,
    validate_concept_kind,
    validate_concept_uid,
    validate_locator,
    validate_natural_key,
)
from .knowledge_evidence import (
    canonical_json_text,
    formatted_json_bytes,
    is_valid_sha256,
    sha256_bytes,
)
from .io import first_unsafe_path_component
from .knowledge_envelope import INVENTORY_HASH_EXTENSION
from .knowledge_model import (
    ConceptKind,
    ConceptRecord,
    EvidenceState,
    KnowledgeIndex,
    Lifecycle,
)
from .wiki_media import contains_uri_authority_userinfo

GOVERNANCE_FILENAME = ".llm-wiki-governance.json"
GOVERNANCE_LOCK_FILENAME = "llm-wiki-governance.lock"

DEFAULT_EVENT_LIMIT = 20
MAX_EVENT_LIMIT = 1000
MAX_LEDGER_BYTES = 8 * 1024 * 1024
MAX_ALIASES_PER_CONCEPT = 10_000

ALIAS_LOCATOR = "locator"
ALIAS_NATURAL_KEY = "natural-key"
ALIAS_TYPES = frozenset({ALIAS_LOCATOR, ALIAS_NATURAL_KEY})
ACTOR_KINDS = frozenset({"human", "agent", "process", "tool"})
REVIEW_EVIDENCE_MODES = frozenset({"source", "no-source"})
REVIEW_EXPIRY_REASONS = frozenset(
    {
        "scope-changed",
        "evidence-changed",
        "basis-incompatible",
        "section-missing",
        "concept-missing",
    }
)

_SAFE_ID_RE = re.compile(r"^[A-Za-z][A-Za-z0-9._:-]{2,127}$")
_EVENT_ID_RE = re.compile(r"^(?:le|rv)_[0-9a-f]{64}$")
_MACHINE_CODE_RE = re.compile(r"^[a-z][a-z0-9]*(?:-[a-z0-9]+)*$")
_WINDOWS_ABSOLUTE_RE = re.compile(r"^[A-Za-z]:[/\\]")
_CONTROL_RE = re.compile(r"[\x00-\x1f\x7f]")
_SENSITIVE_RE = re.compile(
    r"(?:password|passwd|secret|api[-_]?key|access[-_]?token|private[-_]?key)",
    re.IGNORECASE,
)
_MISSING = object()


class GovernanceError(ValueError):
    """A field-specific governance validation or mutation failure."""

    def __init__(
        self,
        field: str,
        message: str,
        *,
        code: str = "governance-invalid",
    ):
        self.field = field
        self.message = message
        self.code = code
        super().__init__(f"{field}: {message}")


class GovernanceConflictError(GovernanceError):
    """Raised when optimistic concurrency detects a changed ledger."""

    def __init__(self, field: str, message: str):
        super().__init__(field, message, code="governance-conflict")


class GovernanceWriteStage(str, Enum):
    """Fault-injection points for the durable ledger replacement."""

    TEMP_DURABLE = "temp-durable"
    REPLACED = "replaced"
    DIRECTORY_DURABLE = "directory-durable"


@dataclass(frozen=True)
class GovernanceActor:
    """Explicit event author; never inferred from Git metadata."""

    kind: str
    actor_id: str

    def to_payload(self) -> dict[str, str]:
        return {"kind": self.kind, "id": self.actor_id}


@dataclass(frozen=True)
class GovernanceAllocation:
    """One authoritative stable concept allocation."""

    uid: str
    concept_kind: str
    natural_key: str
    locator: str

    def to_payload(self) -> dict[str, str]:
        return {
            "concept_kind": self.concept_kind,
            "natural_key": self.natural_key,
            "locator": self.locator,
        }


@dataclass(frozen=True)
class GovernanceAlias:
    """A historical locator or natural key owned by one UID."""

    uid: str
    alias_type: str
    value: str

    @property
    def key(self) -> str:
        return alias_key(self.alias_type, self.value)

    def to_payload(self) -> dict[str, str]:
        return {
            "uid": self.uid,
            "type": self.alias_type,
            "value": self.value,
        }


@dataclass(frozen=True)
class LifecycleEvent:
    """One predecessor-linked lifecycle transition."""

    event_id: str
    concept_uid: str
    previous_event_id: str | None
    from_state: Lifecycle
    to_state: Lifecycle
    actor: GovernanceActor
    authored_at: str
    reason: str
    successor_uid: str | None = None

    def to_payload(self) -> dict[str, object]:
        payload: dict[str, object] = {
            "concept_uid": self.concept_uid,
            "previous_event_id": self.previous_event_id,
            "from": self.from_state.value,
            "to": self.to_state.value,
            "actor": self.actor.to_payload(),
            "authored_at": self.authored_at,
            "reason": self.reason,
        }
        if self.successor_uid is not None:
            payload["successor_uid"] = self.successor_uid
        return payload


@dataclass(frozen=True)
class ReviewEvidence:
    """The explicit evidence basis to which a review was authored."""

    mode: str
    basis_ids: tuple[str, ...] = ()
    basis_hashes: tuple[str, ...] = ()

    def to_payload(self) -> dict[str, object]:
        if self.mode == "no-source":
            return {"mode": self.mode}
        return {
            "mode": self.mode,
            "basis_ids": list(self.basis_ids),
            "basis_hashes": list(self.basis_hashes),
        }


@dataclass(frozen=True)
class ReviewEvent:
    """One section-scoped, digest-bound human review event."""

    event_id: str
    concept_uid: str
    section_locator: str
    scope_hash: str
    evidence: ReviewEvidence
    reviewer: GovernanceActor
    method: str
    method_version: str
    authored_at: str

    def to_payload(self) -> dict[str, object]:
        return {
            "concept_uid": self.concept_uid,
            "section_locator": self.section_locator,
            "scope_hash": self.scope_hash,
            "evidence": self.evidence.to_payload(),
            "reviewer": self.reviewer.to_payload(),
            "method": {"id": self.method, "version": self.method_version},
            "authored_at": self.authored_at,
        }


@dataclass(frozen=True)
class GovernanceLedger:
    """Validated non-rebuildable governance authority."""

    bundle_id: str
    concepts: Mapping[str, GovernanceAllocation] = field(default_factory=dict)
    aliases: Mapping[str, GovernanceAlias] = field(default_factory=dict)
    lifecycle_events: Mapping[str, LifecycleEvent] = field(default_factory=dict)
    review_events: Mapping[str, ReviewEvent] = field(default_factory=dict)
    schema_version: str = GOVERNANCE_SCHEMA_VERSION

    @classmethod
    def empty(cls, bundle_id: str | None = None) -> "GovernanceLedger":
        selected = bundle_id or f"kb_{uuid.uuid4().hex}"
        return validate_governance_ledger(cls(bundle_id=selected))

    @classmethod
    def from_payload(
        cls,
        payload: object,
        *,
        expected_bundle_id: str | None = None,
    ) -> "GovernanceLedger":
        return parse_governance_ledger(
            payload,
            expected_bundle_id=expected_bundle_id,
        )

    def to_payload(self) -> dict[str, object]:
        validated = validate_governance_ledger(self)
        return {
            "schema_version": validated.schema_version,
            "bundle_id": validated.bundle_id,
            "concepts": {
                uid: validated.concepts[uid].to_payload()
                for uid in sorted(validated.concepts)
            },
            "aliases": {
                key: validated.aliases[key].to_payload()
                for key in sorted(validated.aliases)
            },
            "lifecycle_events": {
                event_id: validated.lifecycle_events[event_id].to_payload()
                for event_id in sorted(validated.lifecycle_events)
            },
            "review_events": {
                event_id: validated.review_events[event_id].to_payload()
                for event_id in sorted(validated.review_events)
            },
        }

    def to_bytes(self) -> bytes:
        return formatted_json_bytes(self.to_payload())

    def content_hash(self) -> str:
        return sha256_bytes(self.to_bytes())


@dataclass(frozen=True)
class GovernanceLoadResult:
    ledger: GovernanceLedger
    content_hash: str
    content: bytes


@dataclass(frozen=True)
class GovernanceWriteResult:
    path: Path
    previous_hash: str | None
    content_hash: str
    changed: bool


@dataclass(frozen=True)
class ConceptGovernanceReference:
    """Current generated concept coordinates used for reconciliation."""

    locator: str
    concept_kind: str
    natural_key: str


@dataclass(frozen=True)
class ReviewValidity:
    """Computed review validity; this is never persisted in the ledger."""

    event_id: str
    valid: bool
    reasons: tuple[str, ...]

    @property
    def state(self) -> str:
        return "valid" if self.valid else "expired"


FaultInjector = Callable[[GovernanceWriteStage], None]


_ALLOWED_TRANSITIONS: Mapping[Lifecycle, frozenset[Lifecycle]] = {
    Lifecycle.UNKNOWN: frozenset(
        {Lifecycle.DRAFT, Lifecycle.ACTIVE, Lifecycle.DEPRECATED}
    ),
    Lifecycle.DRAFT: frozenset({Lifecycle.ACTIVE, Lifecycle.DEPRECATED}),
    Lifecycle.ACTIVE: frozenset(
        {Lifecycle.DEPRECATED, Lifecycle.SUPERSEDED}
    ),
    Lifecycle.DEPRECATED: frozenset(
        {Lifecycle.ACTIVE, Lifecycle.SUPERSEDED}
    ),
    Lifecycle.SUPERSEDED: frozenset(),
}


def alias_key(alias_type: str, value: str) -> str:
    """Return the canonical merge-stable key for one alias."""

    selected_type = _alias_type(alias_type, "alias.type")
    selected_value = _identity_value(
        value,
        selected_type,
        "alias.value",
    )
    return f"{selected_type}:{selected_value}"


def natural_key_for(
    concept_kind: str,
    canonical_path: str,
) -> str:
    """Build the initial natural key without using an absolute checkout path."""

    kind = _concept_kind(concept_kind, "concept_kind")
    path = _relative_path(canonical_path, "canonical_path")
    return _natural_key(f"{kind}:{path}", "natural_key")


def derive_concept_uid(
    bundle_id: str,
    concept_kind: str,
    natural_key: str,
) -> str:
    """Derive an initial UID; the persisted allocation is authoritative."""

    try:
        return _derive_identity_uid(bundle_id, concept_kind, natural_key)
    except ConceptIdentityError as exc:
        raise GovernanceError(exc.field, exc.message) from exc


def parse_governance_ledger(
    payload: object,
    *,
    expected_bundle_id: str | None = None,
) -> GovernanceLedger:
    """Validate and deserialize one governance payload."""

    root = _object(payload, "governance")
    _exact_fields(
        root,
        "governance",
        {
            "schema_version",
            "bundle_id",
            "concepts",
            "aliases",
            "lifecycle_events",
            "review_events",
        },
    )
    if root["schema_version"] != GOVERNANCE_SCHEMA_VERSION:
        raise GovernanceError(
            "schema_version",
            f"must be {GOVERNANCE_SCHEMA_VERSION!r}",
            code="governance-version-unsupported",
        )
    bundle_id = _bundle_id(root["bundle_id"], "bundle_id")
    if expected_bundle_id is not None and bundle_id != expected_bundle_id:
        raise GovernanceError(
            "bundle_id",
            f"does not match expected bundle {expected_bundle_id!r}",
            code="governance-bundle-mismatch",
        )

    concepts_raw = _object(root["concepts"], "concepts")
    concepts: dict[str, GovernanceAllocation] = {}
    for uid, value in concepts_raw.items():
        uid_value = _concept_uid(uid, f"concepts.{uid} key")
        record = _object(value, f"concepts.{uid}")
        _exact_fields(
            record,
            f"concepts.{uid}",
            {"concept_kind", "natural_key", "locator"},
        )
        concepts[uid_value] = GovernanceAllocation(
            uid=uid_value,
            concept_kind=_concept_kind(
                record["concept_kind"],
                f"concepts.{uid}.concept_kind",
            ),
            natural_key=_identity_value(
                record["natural_key"],
                ALIAS_NATURAL_KEY,
                f"concepts.{uid}.natural_key",
            ),
            locator=_identity_value(
                record["locator"],
                ALIAS_LOCATOR,
                f"concepts.{uid}.locator",
            ),
        )

    aliases_raw = _object(root["aliases"], "aliases")
    aliases: dict[str, GovernanceAlias] = {}
    for key, value in aliases_raw.items():
        record = _object(value, f"aliases.{key}")
        _exact_fields(record, f"aliases.{key}", {"uid", "type", "value"})
        alias = GovernanceAlias(
            uid=_concept_uid(record["uid"], f"aliases.{key}.uid"),
            alias_type=_alias_type(record["type"], f"aliases.{key}.type"),
            value=_identity_value(
                record["value"],
                str(record["type"]),
                f"aliases.{key}.value",
            ),
        )
        if key != alias.key:
            raise GovernanceError(
                f"aliases.{key}",
                f"key must be canonical alias key {alias.key!r}",
            )
        aliases[key] = alias

    lifecycle_raw = _object(root["lifecycle_events"], "lifecycle_events")
    lifecycle_events = {
        event_id: _parse_lifecycle_event(event_id, value)
        for event_id, value in lifecycle_raw.items()
    }
    reviews_raw = _object(root["review_events"], "review_events")
    review_events = {
        event_id: _parse_review_event(event_id, value)
        for event_id, value in reviews_raw.items()
    }
    return validate_governance_ledger(
        GovernanceLedger(
            bundle_id=bundle_id,
            concepts=concepts,
            aliases=aliases,
            lifecycle_events=lifecycle_events,
            review_events=review_events,
        )
    )


def validate_governance_ledger(
    ledger: GovernanceLedger,
    *,
    expected_bundle_id: str | None = None,
) -> GovernanceLedger:
    """Validate all allocation, alias, reference, and event-history invariants."""

    if not isinstance(ledger, GovernanceLedger):
        raise TypeError("ledger must be a GovernanceLedger")
    if ledger.schema_version != GOVERNANCE_SCHEMA_VERSION:
        raise GovernanceError(
            "schema_version",
            f"must be {GOVERNANCE_SCHEMA_VERSION!r}",
            code="governance-version-unsupported",
        )
    bundle_id = _bundle_id(ledger.bundle_id, "bundle_id")
    if expected_bundle_id is not None and bundle_id != expected_bundle_id:
        raise GovernanceError(
            "bundle_id",
            f"does not match expected bundle {expected_bundle_id!r}",
            code="governance-bundle-mismatch",
        )
    concepts = dict(ledger.concepts)
    aliases = dict(ledger.aliases)
    lifecycle_events = dict(ledger.lifecycle_events)
    review_events = dict(ledger.review_events)

    current_keys: dict[tuple[str, str], str] = {}
    for uid, allocation in concepts.items():
        if not isinstance(allocation, GovernanceAllocation):
            raise GovernanceError(f"concepts.{uid}", "must be an allocation")
        if uid != allocation.uid:
            raise GovernanceError(
                f"concepts.{uid}",
                "map key must equal allocation UID",
            )
        _concept_uid(uid, f"concepts.{uid} key")
        _concept_kind(
            allocation.concept_kind,
            f"concepts.{uid}.concept_kind",
        )
        try:
            ConceptAllocation(
                uid=uid,
                concept_kind=allocation.concept_kind,
                natural_key=allocation.natural_key,
                locator=allocation.locator,
            )
        except ConceptIdentityError as exc:
            raise GovernanceError(
                f"concepts.{uid}.{exc.field}",
                exc.message,
            ) from exc
        natural_key = _identity_value(
            allocation.natural_key,
            ALIAS_NATURAL_KEY,
            f"concepts.{uid}.natural_key",
        )
        locator = _identity_value(
            allocation.locator,
            ALIAS_LOCATOR,
            f"concepts.{uid}.locator",
        )
        for key_type, value in (
            (ALIAS_NATURAL_KEY, natural_key),
            (ALIAS_LOCATOR, locator),
        ):
            coordinate = (
                key_type,
                _identity_ownership_key(key_type, value),
            )
            prior = current_keys.get(coordinate)
            if prior is not None and prior != uid:
                raise GovernanceError(
                    f"concepts.{uid}.{key_type}",
                    f"is already owned by UID {prior!r}",
                    code="governance-allocation-conflict",
                )
            current_keys[coordinate] = uid

    alias_owners: dict[tuple[str, str], str] = {}
    alias_counts: defaultdict[str, int] = defaultdict(int)
    for key, alias in aliases.items():
        if not isinstance(alias, GovernanceAlias):
            raise GovernanceError(f"aliases.{key}", "must be an alias")
        if key != alias.key:
            raise GovernanceError(
                f"aliases.{key}",
                f"map key must equal {alias.key!r}",
            )
        if alias.uid not in concepts:
            raise GovernanceError(
                f"aliases.{key}.uid",
                "does not identify an allocated concept",
            )
        alias_counts[alias.uid] += 1
        if alias_counts[alias.uid] > MAX_ALIASES_PER_CONCEPT:
            raise GovernanceError(
                f"aliases.{key}",
                (
                    "exceeds the per-concept alias limit of "
                    f"{MAX_ALIASES_PER_CONCEPT}"
                ),
                code="governance-alias-limit",
            )
        coordinate = (
            alias.alias_type,
            _identity_ownership_key(alias.alias_type, alias.value),
        )
        prior_alias_owner = alias_owners.get(coordinate)
        if prior_alias_owner is not None:
            message = (
                "duplicates an equivalent historical alias"
                if prior_alias_owner == alias.uid
                else f"is already owned by UID {prior_alias_owner!r}"
            )
            raise GovernanceError(
                f"aliases.{key}.value",
                message,
                code="governance-alias-conflict",
            )
        alias_owners[coordinate] = alias.uid
        current_owner = current_keys.get(coordinate)
        if current_owner is not None:
            message = (
                "duplicates the concept's current coordinate"
                if current_owner == alias.uid
                else f"is currently owned by UID {current_owner!r}"
            )
            raise GovernanceError(
                f"aliases.{key}.value",
                message,
                code="governance-alias-conflict",
            )

    for event_id, event in lifecycle_events.items():
        if not isinstance(event, LifecycleEvent):
            raise GovernanceError(
                f"lifecycle_events.{event_id}",
                "must be a lifecycle event",
            )
        if event_id != event.event_id:
            raise GovernanceError(
                f"lifecycle_events.{event_id}",
                "map key must equal event ID",
            )
        _validate_lifecycle_event_fields(event, concepts)
    _validate_lifecycle_histories(concepts, lifecycle_events)

    for event_id, event in review_events.items():
        if not isinstance(event, ReviewEvent):
            raise GovernanceError(
                f"review_events.{event_id}",
                "must be a review event",
            )
        if event_id != event.event_id:
            raise GovernanceError(
                f"review_events.{event_id}",
                "map key must equal event ID",
            )
        _validate_review_event_fields(event, concepts, aliases)

    return GovernanceLedger(
        bundle_id=bundle_id,
        concepts={key: concepts[key] for key in sorted(concepts)},
        aliases={key: aliases[key] for key in sorted(aliases)},
        lifecycle_events={
            key: lifecycle_events[key] for key in sorted(lifecycle_events)
        },
        review_events={key: review_events[key] for key in sorted(review_events)},
    )


def _read_governance_bytes(
    path: Path,
    *,
    missing_ok: bool,
) -> bytes | None:
    """Read at most one bounded regular ledger without following its leaf."""

    try:
        metadata = path.lstat()
    except FileNotFoundError:
        if missing_ok:
            return None
        raise
    except OSError as exc:
        raise GovernanceError(
            GOVERNANCE_FILENAME,
            "could not be inspected",
        ) from exc
    attributes = getattr(metadata, "st_file_attributes", 0)
    reparse_flag = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0)
    if stat.S_ISLNK(metadata.st_mode) or (
        bool(reparse_flag) and bool(attributes & reparse_flag)
    ):
        raise GovernanceError(
            GOVERNANCE_FILENAME,
            "must be a regular file, not a symbolic link or reparse point",
        )
    if not stat.S_ISREG(metadata.st_mode):
        raise GovernanceError(GOVERNANCE_FILENAME, "must be a regular file")
    if metadata.st_size > MAX_LEDGER_BYTES:
        raise GovernanceError(
            GOVERNANCE_FILENAME,
            f"exceeds the {MAX_LEDGER_BYTES}-byte limit",
        )
    flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0)
    flags |= getattr(os, "O_NOFOLLOW", 0)
    try:
        descriptor = os.open(path, flags)
    except OSError as exc:
        raise GovernanceError(
            GOVERNANCE_FILENAME,
            "could not be opened without following links",
        ) from exc
    try:
        opened = os.fstat(descriptor)
        if not stat.S_ISREG(opened.st_mode):
            raise GovernanceError(
                GOVERNANCE_FILENAME,
                "must remain a regular file while being read",
            )
        chunks: list[bytes] = []
        remaining = MAX_LEDGER_BYTES + 1
        while remaining > 0:
            chunk = os.read(descriptor, min(64 * 1024, remaining))
            if not chunk:
                break
            chunks.append(chunk)
            remaining -= len(chunk)
        content = b"".join(chunks)
    finally:
        os.close(descriptor)
    if len(content) > MAX_LEDGER_BYTES:
        raise GovernanceError(
            GOVERNANCE_FILENAME,
            f"exceeds the {MAX_LEDGER_BYTES}-byte limit",
        )
    return content


def load_governance(
    wiki_dir: str | Path,
    *,
    expected_bundle_id: str | None = None,
) -> GovernanceLoadResult:
    """Load one canonical regular-file ledger and reject duplicate JSON keys."""

    root = Path(wiki_dir)
    if first_unsafe_path_component(root) is not None:
        raise GovernanceError(
            "wiki_dir",
            "must not contain traversal, symbolic-link, or reparse-point components",
        )
    path = root / GOVERNANCE_FILENAME
    content = _read_governance_bytes(path, missing_ok=False)
    assert content is not None
    payload = _decode_unique_json(content)
    ledger = parse_governance_ledger(
        payload,
        expected_bundle_id=expected_bundle_id,
    )
    canonical = ledger.to_bytes()
    if content != canonical:
        raise GovernanceError(
            GOVERNANCE_FILENAME,
            "must use canonical deterministic JSON encoding",
        )
    return GovernanceLoadResult(
        ledger=ledger,
        content_hash=sha256_bytes(content),
        content=content,
    )


def save_governance(
    wiki_dir: str | Path,
    ledger: GovernanceLedger,
    *,
    expected_hash: str | None | object = _MISSING,
    fault_injector: FaultInjector | None = None,
) -> GovernanceWriteResult:
    """Durably replace a ledger after an optional compare-and-swap check.

    ``expected_hash=None`` means the caller observed no prior ledger.
    Omitting ``expected_hash`` is supported for low-level recovery tooling, but
    all normal governance mutations should supply the hash they loaded while
    holding :func:`governance_lock`.
    """

    validated = validate_governance_ledger(ledger)
    content = validated.to_bytes()
    if len(content) > MAX_LEDGER_BYTES:
        raise GovernanceError(
            GOVERNANCE_FILENAME,
            f"exceeds the {MAX_LEDGER_BYTES}-byte limit",
        )
    root = Path(wiki_dir)
    if first_unsafe_path_component(root) is not None:
        raise GovernanceError(
            "wiki_dir",
            "must not contain traversal, symbolic-link, or reparse-point components",
        )
    path = root / GOVERNANCE_FILENAME
    previous_content = _read_governance_bytes(path, missing_ok=True)
    previous_hash = (
        sha256_bytes(previous_content) if previous_content is not None else None
    )
    if expected_hash is not _MISSING:
        if expected_hash is not None and not is_valid_sha256(expected_hash):
            raise GovernanceError(
                "expected_hash",
                "must be a canonical SHA-256 value or None",
            )
        if previous_hash != expected_hash:
            raise GovernanceConflictError(
                GOVERNANCE_FILENAME,
                "changed after it was read; no write was performed",
            )
    content_hash = sha256_bytes(content)
    if previous_content == content:
        return GovernanceWriteResult(
            path=path,
            previous_hash=previous_hash,
            content_hash=content_hash,
            changed=False,
        )
    _write_durable_atomic(path, content, fault_injector=fault_injector)
    return GovernanceWriteResult(
        path=path,
        previous_hash=previous_hash,
        content_hash=content_hash,
        changed=True,
    )


@contextmanager
def governance_lock(wiki_dir: str | Path) -> Iterator[None]:
    """Hold the dedicated non-blocking governance mutation lock."""

    root = Path(wiki_dir)
    if first_unsafe_path_component(root) is not None:
        raise GovernanceError(
            "wiki_dir",
            "must not contain traversal, symbolic-link, or reparse-point components",
        )
    lock_root = _governance_lock_root(root)
    lock_root.mkdir(parents=True, exist_ok=True)
    lock_path = lock_root / GOVERNANCE_LOCK_FILENAME
    if first_unsafe_path_component(lock_path) is not None:
        raise GovernanceError(
            GOVERNANCE_LOCK_FILENAME,
            "must be a regular file without symbolic-link or reparse components",
        )
    flags = os.O_RDWR | os.O_CREAT
    flags |= getattr(os, "O_CLOEXEC", 0)
    flags |= getattr(os, "O_NOFOLLOW", 0)
    try:
        file_descriptor = os.open(lock_path, flags, 0o600)
    except OSError as exc:
        raise GovernanceError(
            GOVERNANCE_LOCK_FILENAME,
            "could not be opened safely",
        ) from exc
    try:
        metadata = os.fstat(file_descriptor)
        if not stat.S_ISREG(metadata.st_mode) or metadata.st_nlink != 1:
            raise GovernanceError(
                GOVERNANCE_LOCK_FILENAME,
                "must be one regular file without hard links",
            )
        if sys.platform == "win32" and metadata.st_size == 0:
            os.write(file_descriptor, b"\0")
            os.fsync(file_descriptor)
        descriptor = os.fdopen(file_descriptor, "r+", encoding="utf-8")
    except BaseException:
        os.close(file_descriptor)
        raise
    try:
        try:
            if sys.platform == "win32":
                import msvcrt

                descriptor.seek(0)
                msvcrt.locking(descriptor.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl

                fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except (BlockingIOError, OSError) as exc:
            raise GovernanceConflictError(
                GOVERNANCE_FILENAME,
                "another governance mutation is in progress",
            ) from exc
        yield
    finally:
        try:
            if sys.platform == "win32":
                import msvcrt

                descriptor.seek(0)
                msvcrt.locking(descriptor.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                import fcntl

                fcntl.flock(descriptor, fcntl.LOCK_UN)
        except OSError:
            pass
        descriptor.close()


def reconcile_concepts(
    ledger: GovernanceLedger,
    concepts: Sequence[ConceptGovernanceReference],
    *,
    moves: Mapping[str, str] | None = None,
) -> GovernanceLedger:
    """Carry supported moves and allocate only genuinely new concepts."""

    current = validate_governance_ledger(ledger)
    allocations = dict(current.concepts)
    aliases = dict(current.aliases)
    by_locator = {
        _identity_ownership_key(ALIAS_LOCATOR, allocation.locator): uid
        for uid, allocation in allocations.items()
    }
    by_natural_key = {
        allocation.natural_key: uid for uid, allocation in allocations.items()
    }
    references = _validated_references(concepts)
    refs_by_locator = {
        _identity_ownership_key(ALIAS_LOCATOR, reference.locator): reference
        for reference in references
    }

    for old_locator, new_locator in sorted((moves or {}).items()):
        old_value = _identity_value(
            old_locator,
            ALIAS_LOCATOR,
            "moves old locator",
        )
        new_value = _identity_value(
            new_locator,
            ALIAS_LOCATOR,
            "moves new locator",
        )
        if old_value == new_value:
            continue
        old_coordinate = _identity_ownership_key(ALIAS_LOCATOR, old_value)
        new_coordinate = _identity_ownership_key(ALIAS_LOCATOR, new_value)
        uid = by_locator.get(old_coordinate)
        if uid is None:
            # A supported move observed before governance initialization does
            # not invent historical authority; normal allocation handles it.
            continue
        target_reference = refs_by_locator.get(new_coordinate)
        if target_reference is None:
            raise GovernanceError(
                f"moves.{old_value}",
                f"target locator {new_value!r} is not a current concept",
            )
        target_owner = by_locator.get(new_coordinate)
        if target_owner is not None and target_owner != uid:
            raise GovernanceError(
                f"moves.{old_value}",
                f"target locator is already owned by UID {target_owner!r}",
                code="governance-allocation-conflict",
            )
        old = allocations[uid]
        if old.concept_kind != target_reference.concept_kind:
            raise GovernanceError(
                f"moves.{old_value}",
                "cannot change concept kind during identity carry-forward",
            )
        natural_owner = by_natural_key.get(target_reference.natural_key)
        if natural_owner is not None and natural_owner != uid:
            raise GovernanceError(
                f"moves.{old_value}",
                f"target natural key is already owned by UID {natural_owner!r}",
                code="governance-allocation-conflict",
            )
        for promoted_type, promoted_value in (
            (ALIAS_LOCATOR, target_reference.locator),
            (ALIAS_NATURAL_KEY, target_reference.natural_key),
        ):
            promoted_coordinate = _identity_ownership_key(
                promoted_type,
                promoted_value,
            )
            for promoted_key, promoted in tuple(aliases.items()):
                if (
                    promoted.alias_type == promoted_type
                    and _identity_ownership_key(
                        promoted.alias_type,
                        promoted.value,
                    )
                    == promoted_coordinate
                    and promoted.uid == uid
                ):
                    aliases.pop(promoted_key)
        allocations[uid] = GovernanceAllocation(
            uid=uid,
            concept_kind=old.concept_kind,
            natural_key=target_reference.natural_key,
            locator=target_reference.locator,
        )
        aliases = _put_alias(
            aliases,
            GovernanceAlias(uid, ALIAS_LOCATOR, old.locator),
            allocations,
        )
        if old.natural_key != target_reference.natural_key:
            aliases = _put_alias(
                aliases,
                GovernanceAlias(uid, ALIAS_NATURAL_KEY, old.natural_key),
                allocations,
            )
        by_locator.pop(
            _identity_ownership_key(ALIAS_LOCATOR, old.locator),
            None,
        )
        by_locator[
            _identity_ownership_key(
                ALIAS_LOCATOR,
                target_reference.locator,
            )
        ] = uid
        by_natural_key.pop(old.natural_key, None)
        by_natural_key[target_reference.natural_key] = uid

    for reference in references:
        locator_owner = by_locator.get(
            _identity_ownership_key(ALIAS_LOCATOR, reference.locator)
        )
        natural_owner = by_natural_key.get(reference.natural_key)
        if locator_owner is not None or natural_owner is not None:
            if locator_owner != natural_owner:
                raise GovernanceError(
                    f"concepts.{reference.locator}",
                    "current locator and natural key resolve to different UIDs",
                    code="governance-allocation-conflict",
                )
            assert locator_owner is not None
            allocation = allocations[locator_owner]
            if allocation.concept_kind != reference.concept_kind:
                raise GovernanceError(
                    f"concepts.{reference.locator}",
                    "allocated concept kind does not match the current concept",
                )
            if allocation.locator != reference.locator:
                allocations[locator_owner] = replace(
                    allocation,
                    locator=reference.locator,
                )
            continue
        uid = derive_concept_uid(
            current.bundle_id,
            reference.concept_kind,
            reference.natural_key,
        )
        existing = allocations.get(uid)
        if existing is not None and (
            existing.locator != reference.locator
            or existing.natural_key != reference.natural_key
            or existing.concept_kind != reference.concept_kind
        ):
            raise GovernanceError(
                f"concepts.{uid}",
                "derived UID collides with a different persisted allocation",
                code="governance-allocation-conflict",
            )
        allocations[uid] = GovernanceAllocation(
            uid=uid,
            concept_kind=reference.concept_kind,
            natural_key=reference.natural_key,
            locator=reference.locator,
        )
        by_locator[
            _identity_ownership_key(ALIAS_LOCATOR, reference.locator)
        ] = uid
        by_natural_key[reference.natural_key] = uid

    return validate_governance_ledger(
        replace(current, concepts=allocations, aliases=aliases)
    )


def move_concept(
    ledger: GovernanceLedger,
    uid: str,
    *,
    locator: str,
    natural_key: str,
    concept_kind: str | None = None,
) -> GovernanceLedger:
    """Explicitly move an ambiguously changed concept and retain both aliases."""

    current = validate_governance_ledger(ledger)
    selected_uid = _existing_uid(uid, current.concepts, "uid")
    old = current.concepts[selected_uid]
    kind = (
        old.concept_kind
        if concept_kind is None
        else _concept_kind(concept_kind, "concept_kind")
    )
    if kind != old.concept_kind:
        raise GovernanceError("concept_kind", "a move cannot change concept kind")
    reference = ConceptGovernanceReference(
        locator=_identity_value(locator, ALIAS_LOCATOR, "locator"),
        concept_kind=kind,
        natural_key=_identity_value(
            natural_key,
            ALIAS_NATURAL_KEY,
            "natural_key",
        ),
    )
    aliases = dict(current.aliases)
    allocations = dict(current.concepts)
    for other_uid, allocation in allocations.items():
        if other_uid == selected_uid:
            continue
        if _identity_ownership_key(
            ALIAS_LOCATOR,
            allocation.locator,
        ) == _identity_ownership_key(ALIAS_LOCATOR, reference.locator):
            raise GovernanceError(
                "locator",
                f"is already owned by UID {other_uid!r}",
                code="governance-allocation-conflict",
            )
        if allocation.natural_key == reference.natural_key:
            raise GovernanceError(
                "natural_key",
                f"is already owned by UID {other_uid!r}",
                code="governance-allocation-conflict",
            )
    for promoted_type, promoted_value in (
        (ALIAS_LOCATOR, reference.locator),
        (ALIAS_NATURAL_KEY, reference.natural_key),
    ):
        promoted_coordinate = _identity_ownership_key(
            promoted_type,
            promoted_value,
        )
        for promoted_key, promoted in tuple(aliases.items()):
            if (
                promoted.alias_type == promoted_type
                and _identity_ownership_key(
                    promoted.alias_type,
                    promoted.value,
                )
                == promoted_coordinate
                and promoted.uid == selected_uid
            ):
                aliases.pop(promoted_key)
    allocations[selected_uid] = GovernanceAllocation(
        uid=selected_uid,
        concept_kind=kind,
        natural_key=reference.natural_key,
        locator=reference.locator,
    )
    if old.locator != reference.locator:
        aliases = _put_alias(
            aliases,
            GovernanceAlias(selected_uid, ALIAS_LOCATOR, old.locator),
            allocations,
        )
    if old.natural_key != reference.natural_key:
        aliases = _put_alias(
            aliases,
            GovernanceAlias(
                selected_uid,
                ALIAS_NATURAL_KEY,
                old.natural_key,
            ),
            allocations,
        )
    return validate_governance_ledger(
        replace(current, concepts=allocations, aliases=aliases)
    )


def add_alias(
    ledger: GovernanceLedger,
    uid: str,
    alias_type: str,
    value: str,
) -> GovernanceLedger:
    """Add one explicit historical alias without changing the allocation."""

    current = validate_governance_ledger(ledger)
    selected_uid = _existing_uid(uid, current.concepts, "uid")
    alias = GovernanceAlias(
        uid=selected_uid,
        alias_type=_alias_type(alias_type, "alias_type"),
        value=_identity_value(value, alias_type, "value"),
    )
    aliases = _put_alias(dict(current.aliases), alias, current.concepts)
    return validate_governance_ledger(replace(current, aliases=aliases))


def current_lifecycle(
    ledger: GovernanceLedger,
    uid: str,
) -> tuple[Lifecycle, LifecycleEvent | None]:
    """Derive one concept's current lifecycle deterministically."""

    current = validate_governance_ledger(ledger)
    selected_uid = _existing_uid(uid, current.concepts, "uid")
    events = [
        event
        for event in current.lifecycle_events.values()
        if event.concept_uid == selected_uid
    ]
    if not events:
        return Lifecycle.UNKNOWN, None
    previous_ids = {
        event.previous_event_id
        for event in events
        if event.previous_event_id is not None
    }
    terminal = [event for event in events if event.event_id not in previous_ids]
    if len(terminal) != 1:
        raise GovernanceError(
            f"lifecycle_events.{selected_uid}",
            "does not have exactly one terminal event",
            code="governance-event-conflict",
        )
    return terminal[0].to_state, terminal[0]


def set_lifecycle(
    ledger: GovernanceLedger,
    uid: str,
    state: Lifecycle | str,
    *,
    actor: GovernanceActor,
    authored_at: str | datetime | None = None,
    successor_uid: str | None = None,
    reason: str = "explicit-lifecycle-change",
) -> GovernanceLedger:
    """Append one valid explicit lifecycle transition."""

    current = validate_governance_ledger(ledger)
    selected_uid = _existing_uid(uid, current.concepts, "uid")
    try:
        target = state if isinstance(state, Lifecycle) else Lifecycle(state)
    except (TypeError, ValueError) as exc:
        raise GovernanceError("state", "is not a supported lifecycle state") from exc
    if target is Lifecycle.UNKNOWN:
        raise GovernanceError("state", "cannot transition explicitly to unknown")
    successor: str | None = None
    if target is Lifecycle.SUPERSEDED:
        if successor_uid is None:
            raise GovernanceError(
                "successor_uid",
                "is required when superseding a concept",
            )
        successor = _existing_uid(
            successor_uid,
            current.concepts,
            "successor_uid",
        )
        if successor == selected_uid:
            raise GovernanceError(
                "successor_uid",
                "must identify a different concept",
            )
    elif successor_uid is not None:
        raise GovernanceError(
            "successor_uid",
            "is valid only for a superseded lifecycle",
        )
    selected_actor = _actor(actor, "actor")
    selected_time = authored_event_time(authored_at)
    selected_reason = _machine_code(reason, "reason")
    prior_state, prior_event = current_lifecycle(current, selected_uid)
    if target is prior_state:
        if (
            prior_event is not None
            and prior_event.successor_uid == successor
            and prior_event.actor == selected_actor
            and prior_event.authored_at == selected_time
            and prior_event.reason == selected_reason
        ):
            return current
        raise GovernanceError(
            "state",
            (
                f"lifecycle {target.value!r} is already recorded with "
                "different event metadata"
            ),
            code="governance-transition-invalid",
        )
    if target not in _ALLOWED_TRANSITIONS[prior_state]:
        raise GovernanceError(
            "state",
            f"transition {prior_state.value!r} -> {target.value!r} is not allowed",
            code="governance-transition-invalid",
        )
    event = LifecycleEvent(
        event_id="",
        concept_uid=selected_uid,
        previous_event_id=(
            prior_event.event_id if prior_event is not None else None
        ),
        from_state=prior_state,
        to_state=target,
        actor=selected_actor,
        authored_at=selected_time,
        reason=selected_reason,
        successor_uid=successor,
    )
    event = replace(
        event,
        event_id=_derived_event_id("le", _lifecycle_event_digest_payload(event)),
    )
    event_id = event.event_id
    events = dict(current.lifecycle_events)
    existing = events.get(event_id)
    if existing is not None and existing != event:
        raise GovernanceError(
            f"lifecycle_events.{event_id}",
            "event ID collides with different content",
            code="governance-event-conflict",
        )
    events[event_id] = event
    return validate_governance_ledger(
        replace(current, lifecycle_events=events)
    )


def add_review_event(
    ledger: GovernanceLedger,
    uid: str,
    *,
    section_locator: str,
    scope_hash: str,
    evidence: ReviewEvidence,
    reviewer: GovernanceActor,
    method: str,
    method_version: str,
    authored_at: str | datetime | None = None,
) -> GovernanceLedger:
    """Append one explicit section review without storing a validity verdict."""

    current = validate_governance_ledger(ledger)
    selected_uid = _existing_uid(uid, current.concepts, "uid")
    selected_section = _section_locator(section_locator, "section_locator")
    section_page_locator = selected_section.partition("#section/")[0]
    allocation = current.concepts[selected_uid]
    if _identity_ownership_key(
        ALIAS_LOCATOR,
        section_page_locator,
    ) != _identity_ownership_key(ALIAS_LOCATOR, allocation.locator):
        raise GovernanceError(
            "section_locator",
            "must belong to the reviewed concept's current locator",
            code="governance-review-scope-mismatch",
        )
    selected_scope = _hash(scope_hash, "scope_hash")
    selected_evidence = _review_evidence(evidence, "evidence")
    selected_reviewer = _actor(reviewer, "reviewer")
    selected_method = _safe_name(method, "method")
    selected_version = _safe_name(method_version, "method_version")
    selected_time = authored_event_time(authored_at)
    event = ReviewEvent(
        event_id="",
        concept_uid=selected_uid,
        section_locator=selected_section,
        scope_hash=selected_scope,
        evidence=selected_evidence,
        reviewer=selected_reviewer,
        method=selected_method,
        method_version=selected_version,
        authored_at=selected_time,
    )
    event = replace(
        event,
        event_id=_derived_event_id("rv", _review_event_digest_payload(event)),
    )
    event_id = event.event_id
    events = dict(current.review_events)
    existing = events.get(event_id)
    if existing is not None and existing != event:
        raise GovernanceError(
            f"review_events.{event_id}",
            "event ID collides with different content",
            code="governance-event-conflict",
        )
    events[event_id] = event
    return validate_governance_ledger(replace(current, review_events=events))


def authored_event_time(value: str | datetime | None = None) -> str:
    """Return a canonical real UTC authored-event time."""

    selected = datetime.now(timezone.utc) if value is None else value
    if isinstance(selected, str):
        raw = selected
        try:
            parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        except ValueError as exc:
            raise GovernanceError(
                "authored_at",
                "must be an RFC 3339 timestamp with timezone",
            ) from exc
    elif isinstance(selected, datetime):
        parsed = selected
    else:
        raise GovernanceError(
            "authored_at",
            "must be an RFC 3339 timestamp or datetime",
        )
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise GovernanceError("authored_at", "must include a timezone")
    utc = parsed.astimezone(timezone.utc)
    if utc.microsecond:
        return utc.isoformat(timespec="microseconds").replace("+00:00", "Z")
    return utc.isoformat(timespec="seconds").replace("+00:00", "Z")


def lifecycle_state_by_uid(
    ledger: GovernanceLedger,
) -> dict[str, tuple[Lifecycle, str | None, LifecycleEvent | None]]:
    """Derive lifecycle, successor, and terminal event for every allocation."""

    current = validate_governance_ledger(ledger)
    result: dict[str, tuple[Lifecycle, str | None, LifecycleEvent | None]] = {}
    for uid in current.concepts:
        state, event = current_lifecycle(current, uid)
        result[uid] = (
            state,
            event.successor_uid if event is not None else None,
            event,
        )
    return result


def concept_references_from_knowledge(
    knowledge: KnowledgeIndex,
) -> tuple[ConceptGovernanceReference, ...]:
    """Return canonical identity references from a generated projection."""

    if not isinstance(knowledge, KnowledgeIndex):
        raise TypeError("knowledge must be a KnowledgeIndex")
    references = []
    for concept in knowledge.concepts:
        kind = (
            concept.concept_kind.value
            if isinstance(concept.concept_kind, ConceptKind)
            else concept.concept_kind
        )
        references.append(
            ConceptGovernanceReference(
                locator=concept.locator,
                concept_kind=kind,
                natural_key=natural_key_for(
                    kind,
                    concept.document.canonical_path,
                ),
            )
        )
    return _validated_references(references)


def current_review_evidence(
    concept: ConceptRecord,
) -> ReviewEvidence | None:
    """Return the comparable review evidence basis for one current concept.

    ``None`` means source evidence is promised but presently incompatible or
    unavailable.  Non-source concepts use an explicit ``no-source`` marker.
    """

    if not isinstance(concept, ConceptRecord):
        raise TypeError("concept must be a ConceptRecord")
    structure = concept.facets.structure
    basis = structure.basis
    if structure.evidence is EvidenceState.NOT_APPLICABLE:
        return ReviewEvidence(mode="no-source")
    if basis is None:
        # Semantic/document concepts have no structural source promise.
        if structure.evidence is EvidenceState.UNKNOWN:
            return ReviewEvidence(mode="no-source")
        return None
    if (
        structure.evidence is not EvidenceState.PRESENT
        or basis.extractor_ref is None
        or basis.source_content_hash is None
        or basis.concept_observation_hash is None
    ):
        return None
    basis_ids = (
        f"extractor:{basis.extractor_ref}",
        f"scope:{basis.scope.value}",
    )
    basis_hashes = (
        basis.source_content_hash,
        basis.concept_observation_hash,
    )
    if basis.aggregate_input_hash is not None:
        basis_hashes += (basis.aggregate_input_hash,)
    return _review_evidence(
        ReviewEvidence(
            mode="source",
            basis_ids=basis_ids,
            basis_hashes=basis_hashes,
        ),
        "evidence",
    )


def review_scope_hash(
    knowledge: KnowledgeIndex,
    section_locator: str,
) -> str:
    """Return one reviewable semantic section hash or fail explicitly."""

    selected = _section_locator(section_locator, "section_locator")
    sections = _section_records_by_locator(knowledge)
    section = sections.get(selected)
    if section is None:
        raise GovernanceError(
            "section_locator",
            "does not identify a current section",
            code="section-missing",
        )
    semantic_hash = section.get("semantic_hash")
    if not is_valid_sha256(semantic_hash):
        raise GovernanceError(
            "section_locator",
            "does not identify a semantic or mixed semantic scope",
            code="basis-incompatible",
        )
    assert isinstance(semantic_hash, str)
    return semantic_hash


def evaluate_review_event(
    event: ReviewEvent,
    ledger: GovernanceLedger,
    knowledge: KnowledgeIndex,
) -> ReviewValidity:
    """Compute current validity without mutating or trusting stored truth."""

    current = validate_governance_ledger(ledger)
    if not isinstance(event, ReviewEvent):
        raise TypeError("event must be a ReviewEvent")
    _validate_review_event_fields(event, current.concepts, current.aliases)
    if not isinstance(knowledge, KnowledgeIndex):
        raise TypeError("knowledge must be a KnowledgeIndex")
    allocation = current.concepts[event.concept_uid]
    concepts = {concept.locator: concept for concept in knowledge.concepts}
    concept = concepts.get(allocation.locator)
    reasons: list[str] = []
    if concept is None:
        reasons.append("concept-missing")
    section = _section_records_by_locator(knowledge).get(event.section_locator)
    if section is None:
        reasons.append("section-missing")
    else:
        semantic_hash = section.get("semantic_hash")
        if not is_valid_sha256(semantic_hash):
            reasons.append("basis-incompatible")
        elif semantic_hash != event.scope_hash:
            reasons.append("scope-changed")
    if concept is not None:
        evidence = current_review_evidence(concept)
        if evidence is None or evidence.mode != event.evidence.mode:
            reasons.append("basis-incompatible")
        elif (
            evidence.basis_ids != event.evidence.basis_ids
            or evidence.basis_hashes != event.evidence.basis_hashes
        ):
            reasons.append("evidence-changed")
    return ReviewValidity(
        event_id=event.event_id,
        valid=not reasons,
        reasons=tuple(
            reason
            for reason in (
                "concept-missing",
                "section-missing",
                "basis-incompatible",
                "scope-changed",
                "evidence-changed",
            )
            if reason in reasons
        ),
    )


def strip_governance_projection(knowledge: KnowledgeIndex) -> KnowledgeIndex:
    """Remove disposable governance fields before rebuilding from authority."""

    if not isinstance(knowledge, KnowledgeIndex):
        raise TypeError("knowledge must be a KnowledgeIndex")
    concepts = []
    for concept in knowledge.concepts:
        extensions = dict(concept.extensions)
        extensions.pop(GOVERNANCE_EXTENSION_KEY, None)
        concepts.append(
            replace(
                concept,
                lifecycle=Lifecycle.UNKNOWN,
                extensions=extensions,
            )
        )
    extensions = dict(knowledge.extensions)
    extensions.pop(GOVERNANCE_EXTENSION_KEY, None)
    graph = extensions.get("llm-wiki/typed-graph-v1")
    if isinstance(graph, Mapping):
        from .knowledge_graph import validate_typed_graph

        graph_payload = dict(graph)
        edges = graph_payload.get("edges")
        if isinstance(edges, list):
            graph_payload["edges"] = [
                edge
                for edge in edges
                if not (
                    isinstance(edge, Mapping)
                    and edge.get("kind") == "supersedes"
                    and edge.get("origin") == "governance"
                )
            ]
            extensions["llm-wiki/typed-graph-v1"] = validate_typed_graph(
                graph_payload,
                concept_kinds={
                    concept.locator: (
                        concept.concept_kind.value
                        if isinstance(concept.concept_kind, ConceptKind)
                        else concept.concept_kind
                    )
                    for concept in concepts
                },
            )
    snapshot_extensions = dict(knowledge.bundle.snapshot.extensions)
    snapshot_extensions.pop(GOVERNANCE_HASH_EXTENSION_KEY, None)
    bundle = replace(
        knowledge.bundle,
        snapshot=replace(
            knowledge.bundle.snapshot,
            extensions=snapshot_extensions,
        ),
    )
    return replace(
        knowledge,
        bundle=bundle,
        concepts=tuple(concepts),
        extensions=extensions,
    )


def apply_governance_projection(
    knowledge: KnowledgeIndex,
    ledger: GovernanceLedger,
    *,
    event_limit: int = DEFAULT_EVENT_LIMIT,
) -> KnowledgeIndex:
    """Build the complete disposable governance projection from the ledger."""

    limit = _event_limit(event_limit)
    base = strip_governance_projection(knowledge)
    current = validate_governance_ledger(ledger)
    references = concept_references_from_knowledge(base)
    active_by_locator = {reference.locator: reference for reference in references}
    allocations_by_locator = {
        allocation.locator: allocation
        for allocation in current.concepts.values()
    }
    missing = set(active_by_locator) - set(allocations_by_locator)
    if missing:
        locator = min(missing)
        raise GovernanceError(
            f"concepts.{locator}",
            "has no stable UID allocation",
            code="governance-missing-uid",
        )
    lifecycle = lifecycle_state_by_uid(current)
    aliases_by_uid: defaultdict[str, list[GovernanceAlias]] = defaultdict(list)
    for alias in current.aliases.values():
        aliases_by_uid[alias.uid].append(alias)
    lifecycle_by_uid: defaultdict[str, list[LifecycleEvent]] = defaultdict(list)
    for event in current.lifecycle_events.values():
        lifecycle_by_uid[event.concept_uid].append(event)
    reviews_by_uid: defaultdict[str, list[ReviewEvent]] = defaultdict(list)
    for event in current.review_events.values():
        reviews_by_uid[event.concept_uid].append(event)

    concept_summaries: dict[str, dict[str, object]] = {}
    projected_concepts: list[ConceptRecord] = []
    for concept in base.concepts:
        allocation = allocations_by_locator[concept.locator]
        reference = active_by_locator[concept.locator]
        if (
            allocation.concept_kind != reference.concept_kind
            or allocation.natural_key != reference.natural_key
        ):
            raise GovernanceError(
                f"concepts.{concept.locator}",
                "allocation does not match the current natural key and kind",
                code="governance-allocation-conflict",
            )
        state, successor_uid, _terminal = lifecycle[allocation.uid]
        lifecycle_items = [
            _lifecycle_event_summary(event)
            for event in _ordered_lifecycle_events(
                lifecycle_by_uid[allocation.uid]
            )
        ]
        review_items = []
        for event in sorted(
            reviews_by_uid[allocation.uid],
            key=lambda item: (item.authored_at, item.event_id),
        ):
            validity = evaluate_review_event(event, current, base)
            review_items.append(_review_event_summary(event, validity))
        summary: dict[str, object] = {
            "uid": allocation.uid,
            "aliases": [
                {
                    "type": alias.alias_type,
                    "value": alias.value,
                }
                for alias in sorted(
                    aliases_by_uid[allocation.uid],
                    key=lambda item: (item.alias_type, item.value),
                )
            ],
            "lifecycle": state.value,
            "lifecycle_events": _bounded_event_payload(
                lifecycle_items,
                limit,
            ),
            "reviews": _bounded_event_payload(review_items, limit),
        }
        if successor_uid is not None:
            summary["successor_uid"] = successor_uid
        concept_summaries[concept.locator] = summary
        concept_extensions = dict(concept.extensions)
        concept_extensions[GOVERNANCE_EXTENSION_KEY] = summary
        projected_concepts.append(
            replace(
                concept,
                lifecycle=state,
                extensions=concept_extensions,
            )
        )

    governance_hash = current.content_hash()
    projection = {
        "schema_version": GOVERNANCE_SCHEMA_VERSION,
        "bundle_id": current.bundle_id,
        "input_hash": governance_hash,
        "concepts": {
            locator: concept_summaries[locator]
            for locator in sorted(concept_summaries)
        },
    }
    extensions = dict(base.extensions)
    extensions[GOVERNANCE_EXTENSION_KEY] = projection
    extensions = _add_supersession_edges(
        extensions,
        current,
        projected_concepts,
        governance_hash,
        inventory_hash=base.bundle.snapshot.extensions.get(
            INVENTORY_HASH_EXTENSION
        ),
    )
    snapshot_extensions = dict(base.bundle.snapshot.extensions)
    snapshot_extensions[GOVERNANCE_HASH_EXTENSION_KEY] = governance_hash
    projected = replace(
        base,
        bundle=replace(
            base.bundle,
            snapshot=replace(
                base.bundle.snapshot,
                extensions=snapshot_extensions,
            ),
        ),
        concepts=tuple(projected_concepts),
        extensions=extensions,
    )
    validate_governance_projection(projected, event_limit=limit)
    return projected


def validate_governance_projection(
    knowledge: KnowledgeIndex,
    *,
    ledger: GovernanceLedger | None = None,
    event_limit: int | None = None,
) -> Mapping[str, object] | None:
    """Validate projection/core parity and optionally exact ledger parity."""

    if not isinstance(knowledge, KnowledgeIndex):
        raise TypeError("knowledge must be a KnowledgeIndex")
    raw = knowledge.extensions.get(GOVERNANCE_EXTENSION_KEY)
    snapshot_hash = knowledge.bundle.snapshot.extensions.get(
        GOVERNANCE_HASH_EXTENSION_KEY
    )
    concept_values = [
        concept.extensions.get(GOVERNANCE_EXTENSION_KEY)
        for concept in knowledge.concepts
    ]
    if raw is None:
        if snapshot_hash is not None or any(
            value is not None for value in concept_values
        ):
            raise GovernanceError(
                "extensions",
                "contains an incomplete governance projection",
                code="governance-projection-mismatch",
            )
        return None
    projection = _object(raw, "governance_projection")
    _exact_fields(
        projection,
        "governance_projection",
        {"schema_version", "bundle_id", "input_hash", "concepts"},
    )
    if projection["schema_version"] != GOVERNANCE_SCHEMA_VERSION:
        raise GovernanceError(
            "governance_projection.schema_version",
            f"must be {GOVERNANCE_SCHEMA_VERSION!r}",
        )
    projected_bundle_id = _bundle_id(
        projection["bundle_id"],
        "governance_projection.bundle_id",
    )
    validated_ledger = (
        validate_governance_ledger(ledger)
        if ledger is not None
        else None
    )
    if (
        validated_ledger is not None
        and validated_ledger.bundle_id != projected_bundle_id
    ):
        raise GovernanceError(
            "governance_projection.bundle_id",
            "does not match the authoritative governance ledger bundle",
            code="governance-bundle-mismatch",
        )
    input_hash = _hash(
        projection["input_hash"],
        "governance_projection.input_hash",
    )
    if snapshot_hash != input_hash:
        raise GovernanceError(
            "bundle.snapshot.extensions."
            f"{GOVERNANCE_HASH_EXTENSION_KEY}",
            "does not match the governance projection input hash",
            code="governance-projection-mismatch",
        )
    summaries = _object(
        projection["concepts"],
        "governance_projection.concepts",
    )
    concepts_by_locator = {
        concept.locator: concept for concept in knowledge.concepts
    }
    if set(summaries) != set(concepts_by_locator):
        raise GovernanceError(
            "governance_projection.concepts",
            "must contain exactly every active knowledge concept",
            code="governance-projection-mismatch",
        )
    seen_uids: set[str] = set()
    successor_pairs: set[tuple[str, str]] = set()
    declared_limits: set[int] = set()
    selected_limit = _event_limit(event_limit) if event_limit is not None else None
    for locator, concept in concepts_by_locator.items():
        summary = _validate_concept_summary(
            summaries[locator],
            f"governance_projection.concepts.{locator}",
            limit=selected_limit,
        )
        lifecycle_limit = int(summary["lifecycle_events"]["limit"])
        review_limit = int(summary["reviews"]["limit"])
        if lifecycle_limit != review_limit:
            raise GovernanceError(
                f"governance_projection.concepts.{locator}",
                "must use one event limit for lifecycle and review summaries",
                code="governance-projection-mismatch",
            )
        declared_limits.add(lifecycle_limit)
        uid = str(summary["uid"])
        if uid in seen_uids:
            raise GovernanceError(
                f"governance_projection.concepts.{locator}.uid",
                "duplicates an active concept UID",
            )
        seen_uids.add(uid)
        if concept.lifecycle.value != summary["lifecycle"]:
            raise GovernanceError(
                f"governance_projection.concepts.{locator}.lifecycle",
                "does not match the core concept lifecycle",
                code="governance-projection-mismatch",
            )
        if concept.extensions.get(GOVERNANCE_EXTENSION_KEY) != summary:
            raise GovernanceError(
                f"concepts.{locator}.extensions.{GOVERNANCE_EXTENSION_KEY}",
                "does not match the top-level governance summary",
                code="governance-projection-mismatch",
            )
        successor = summary.get("successor_uid")
        if isinstance(successor, str):
            successor_pairs.add((uid, successor))
    _validate_supersession_projection(
        knowledge,
        successor_pairs,
    )
    if len(declared_limits) > 1:
        raise GovernanceError(
            "governance_projection.concepts",
            "must use one event limit across all concept summaries",
            code="governance-projection-mismatch",
        )
    if validated_ledger is not None:
        exact_limit = (
            selected_limit
            if selected_limit is not None
            else next(iter(declared_limits), DEFAULT_EVENT_LIMIT)
        )
        expected = apply_governance_projection(
            strip_governance_projection(knowledge),
            validated_ledger,
            event_limit=exact_limit,
        )
        if (
            expected.extensions.get(GOVERNANCE_EXTENSION_KEY) != projection
            or expected.bundle.snapshot.extensions.get(
                GOVERNANCE_HASH_EXTENSION_KEY
            )
            != snapshot_hash
            or tuple(
                (
                    concept.locator,
                    concept.lifecycle,
                    concept.extensions.get(GOVERNANCE_EXTENSION_KEY),
                )
                for concept in expected.concepts
            )
            != tuple(
                (
                    concept.locator,
                    concept.lifecycle,
                    concept.extensions.get(GOVERNANCE_EXTENSION_KEY),
                )
                for concept in knowledge.concepts
            )
            or _governance_supersession_edge_payloads(expected)
            != _governance_supersession_edge_payloads(knowledge)
        ):
            raise GovernanceError(
                "governance_projection",
                "does not match the authoritative ledger",
                code="governance-projection-mismatch",
            )
    return projection


def governance_hash_from_knowledge(
    knowledge: KnowledgeIndex,
) -> str | None:
    """Return the validated governance commitment in a knowledge projection."""

    projection = validate_governance_projection(knowledge)
    if projection is None:
        return None
    value = projection["input_hash"]
    assert isinstance(value, str)
    return value


def governance_bundle_id_from_knowledge(
    knowledge: KnowledgeIndex,
) -> str | None:
    """Return the validated stable bundle ID from a governance projection."""

    projection = validate_governance_projection(knowledge)
    if projection is None:
        return None
    value = projection["bundle_id"]
    assert isinstance(value, str)
    return value


def _validate_concept_summary(
    value: object,
    path: str,
    *,
    limit: int | None,
) -> dict[str, object]:
    summary = _object(value, path)
    _exact_fields(
        summary,
        path,
        {"uid", "aliases", "lifecycle", "lifecycle_events", "reviews"},
        optional={"successor_uid"},
    )
    uid = _concept_uid(summary["uid"], f"{path}.uid")
    try:
        lifecycle = Lifecycle(summary["lifecycle"])
    except (TypeError, ValueError) as exc:
        raise GovernanceError(
            f"{path}.lifecycle",
            "is not a supported lifecycle value",
        ) from exc
    aliases = _array(summary["aliases"], f"{path}.aliases")
    if len(aliases) > MAX_ALIASES_PER_CONCEPT:
        raise GovernanceError(
            f"{path}.aliases",
            (
                "exceeds the per-concept alias limit of "
                f"{MAX_ALIASES_PER_CONCEPT}"
            ),
            code="governance-alias-limit",
        )
    normalized_aliases: list[dict[str, str]] = []
    seen_aliases: set[tuple[str, str]] = set()
    for index, raw_alias in enumerate(aliases):
        alias_path = f"{path}.aliases[{index}]"
        alias = _object(raw_alias, alias_path)
        _exact_fields(alias, alias_path, {"type", "value"})
        alias_type = _alias_type(alias["type"], f"{alias_path}.type")
        alias_value = _identity_value(
            alias["value"],
            alias_type,
            f"{alias_path}.value",
        )
        coordinate = (alias_type, alias_value)
        if coordinate in seen_aliases:
            raise GovernanceError(alias_path, "duplicates an alias")
        seen_aliases.add(coordinate)
        normalized_aliases.append(
            {"type": alias_type, "value": alias_value}
        )
    if normalized_aliases != sorted(
        normalized_aliases,
        key=lambda item: (item["type"], item["value"]),
    ):
        raise GovernanceError(f"{path}.aliases", "must be canonically sorted")
    lifecycle_events = _validate_bounded_events(
        summary["lifecycle_events"],
        f"{path}.lifecycle_events",
        limit=limit,
        event_type="lifecycle",
    )
    reviews = _validate_bounded_events(
        summary["reviews"],
        f"{path}.reviews",
        limit=limit,
        event_type="review",
    )
    normalized: dict[str, object] = {
        "uid": uid,
        "aliases": normalized_aliases,
        "lifecycle": lifecycle.value,
        "lifecycle_events": lifecycle_events,
        "reviews": reviews,
    }
    successor = summary.get("successor_uid")
    if lifecycle is Lifecycle.SUPERSEDED:
        if successor is None:
            raise GovernanceError(
                f"{path}.successor_uid",
                "is required for superseded lifecycle",
            )
        successor_uid = _concept_uid(successor, f"{path}.successor_uid")
        if successor_uid == uid:
            raise GovernanceError(
                f"{path}.successor_uid",
                "must identify a different UID",
            )
        normalized["successor_uid"] = successor_uid
    elif successor is not None:
        raise GovernanceError(
            f"{path}.successor_uid",
            "is valid only for superseded lifecycle",
        )
    return normalized


def _validate_bounded_events(
    value: object,
    path: str,
    *,
    limit: int | None,
    event_type: str,
) -> dict[str, object]:
    record = _object(value, path)
    _exact_fields(
        record,
        path,
        {"items", "total", "returned", "limit", "truncated"},
    )
    items = _array(record["items"], f"{path}.items")
    total = _nonnegative_int(record["total"], f"{path}.total")
    returned = _nonnegative_int(record["returned"], f"{path}.returned")
    declared_limit = _nonnegative_int(record["limit"], f"{path}.limit")
    truncated = record["truncated"]
    if not isinstance(truncated, bool):
        raise GovernanceError(f"{path}.truncated", "must be a boolean")
    if declared_limit > MAX_EVENT_LIMIT:
        raise GovernanceError(
            f"{path}.limit",
            f"must be at most {MAX_EVENT_LIMIT}",
        )
    if limit is not None and declared_limit != limit:
        raise GovernanceError(f"{path}.limit", f"must equal {limit}")
    effective_limit = declared_limit if limit is None else limit
    if returned != len(items) or returned > total or returned > effective_limit:
        raise GovernanceError(path, "contains inconsistent event bounds")
    if truncated != (total > returned):
        raise GovernanceError(
            f"{path}.truncated",
            "does not match total and returned",
        )
    normalized_items: list[dict[str, object]] = []
    seen_ids: set[str] = set()
    for index, raw_item in enumerate(items):
        item_path = f"{path}.items[{index}]"
        item = _object(raw_item, item_path)
        if event_type == "lifecycle":
            normalized = _validate_lifecycle_summary(item, item_path)
            event_id = str(normalized["event_id"])
        else:
            normalized = _validate_review_summary(item, item_path)
            event_id = str(normalized["event_id"])
        if event_id in seen_ids:
            raise GovernanceError(item_path, "duplicates an event ID")
        seen_ids.add(event_id)
        normalized_items.append(normalized)
    return {
        "items": normalized_items,
        "total": total,
        "returned": returned,
        "limit": declared_limit,
        "truncated": truncated,
    }


def _validate_lifecycle_summary(
    value: Mapping[str, object],
    path: str,
) -> dict[str, object]:
    _exact_fields(
        value,
        path,
        {"event_id", "from", "to", "actor", "authored_at", "reason"},
        optional={"successor_uid"},
    )
    event_id = _event_id(value["event_id"], f"{path}.event_id", prefix="le")
    try:
        from_state = Lifecycle(value["from"])
        to_state = Lifecycle(value["to"])
    except (TypeError, ValueError) as exc:
        raise GovernanceError(path, "contains invalid lifecycle states") from exc
    actor = _parse_actor(value["actor"], f"{path}.actor")
    authored_at = authored_event_time(value["authored_at"])
    reason = _machine_code(value["reason"], f"{path}.reason")
    normalized: dict[str, object] = {
        "event_id": event_id,
        "from": from_state.value,
        "to": to_state.value,
        "actor": actor.to_payload(),
        "authored_at": authored_at,
        "reason": reason,
    }
    if "successor_uid" in value:
        normalized["successor_uid"] = _concept_uid(
            value["successor_uid"],
            f"{path}.successor_uid",
        )
    return normalized


def _validate_review_summary(
    value: Mapping[str, object],
    path: str,
) -> dict[str, object]:
    _exact_fields(
        value,
        path,
        {
            "event_id",
            "section_locator",
            "state",
            "reasons",
            "reviewer",
            "method",
            "authored_at",
        },
    )
    event_id = _event_id(value["event_id"], f"{path}.event_id", prefix="rv")
    section_locator = _section_locator(
        value["section_locator"],
        f"{path}.section_locator",
    )
    if value["state"] not in {"valid", "expired"}:
        raise GovernanceError(
            f"{path}.state",
            "must be 'valid' or 'expired'",
        )
    reasons_raw = _array(value["reasons"], f"{path}.reasons")
    reasons: list[str] = []
    for reason in reasons_raw:
        if not isinstance(reason, str) or reason not in REVIEW_EXPIRY_REASONS:
            raise GovernanceError(
                f"{path}.reasons",
                "contains an unsupported review expiry reason",
            )
        if reason not in reasons:
            reasons.append(reason)
    if (value["state"] == "valid") != (not reasons):
        raise GovernanceError(path, "review state does not match expiry reasons")
    reviewer = _parse_actor(value["reviewer"], f"{path}.reviewer")
    method = _object(value["method"], f"{path}.method")
    _exact_fields(method, f"{path}.method", {"id", "version"})
    return {
        "event_id": event_id,
        "section_locator": section_locator,
        "state": value["state"],
        "reasons": reasons,
        "reviewer": reviewer.to_payload(),
        "method": {
            "id": _safe_name(method["id"], f"{path}.method.id"),
            "version": _safe_name(
                method["version"],
                f"{path}.method.version",
            ),
        },
        "authored_at": authored_event_time(value["authored_at"]),
    }


def _add_supersession_edges(
    extensions: dict[str, Any],
    ledger: GovernanceLedger,
    concepts: Sequence[ConceptRecord],
    governance_hash: str,
    *,
    inventory_hash: object = None,
) -> dict[str, Any]:
    graph = extensions.get("llm-wiki/typed-graph-v1")
    lifecycle = lifecycle_state_by_uid(ledger)
    supersessions = [
        (uid, successor_uid, event)
        for uid, (state, successor_uid, event) in lifecycle.items()
        if (
            state is Lifecycle.SUPERSEDED
            and successor_uid is not None
            and event is not None
        )
    ]
    if not isinstance(graph, Mapping) and not supersessions:
        return extensions
    from .knowledge_graph import (
        DEFAULT_EVIDENCE_LIMIT,
        GRAPH_INPUT_NAMES,
        GraphConcept,
        KnowledgeGraphInputs,
        materialize_typed_graph,
        relationship_edge_key,
        validate_typed_graph,
    )

    if not isinstance(graph, Mapping):
        graph = materialize_typed_graph(
            KnowledgeGraphInputs(
                inventory={},
                concepts=tuple(
                    GraphConcept(
                        locator=concept.locator,
                        concept_kind=(
                            concept.concept_kind.value
                            if isinstance(concept.concept_kind, ConceptKind)
                            else concept.concept_kind
                        ),
                    )
                    for concept in concepts
                ),
            )
        )
        if inventory_hash is not None:
            if not is_valid_sha256(inventory_hash):
                raise GovernanceError(
                    "bundle.snapshot.extensions."
                    f"{INVENTORY_HASH_EXTENSION}",
                    "must contain a canonical normalized inventory hash",
                    code="governance-projection-mismatch",
                )
            rebound_graph = dict(graph)
            input_hashes = dict(rebound_graph["input_hashes"])
            input_hashes["inventory"] = inventory_hash
            input_hashes["aggregate"] = sha256_bytes(
                canonical_json_text(
                    {
                        name: input_hashes[name]
                        for name in GRAPH_INPUT_NAMES
                    }
                ).encode("utf-8")
            )
            rebound_graph["input_hashes"] = input_hashes
            graph = rebound_graph
    graph_payload = dict(graph)
    edges = [
        dict(edge)
        for edge in graph_payload.get("edges", [])
        if isinstance(edge, Mapping)
    ]
    aggregate_hash = graph_payload["input_hashes"]["concept-map"]
    for uid, successor_uid, event in supersessions:
        source = {"kind": "concept", "uid": uid}
        target = {"kind": "concept", "uid": successor_uid}
        identity = {
            "kind": "supersedes",
            "from": source,
            "target": target,
            "origin": "governance",
            "resolution": "resolved",
        }
        sample = {
            "kind": "supersession",
            "source": source,
            "target": target,
            "reason": event.reason,
            "attributes": {"governance_hash": governance_hash},
        }
        edges.append(
            {
                "key": relationship_edge_key(identity),
                **identity,
                "evidence": {
                    "state": "present",
                    "aggregate_input_hash": aggregate_hash,
                    "observed": 1,
                    "unique": 1,
                    "emitted": 1,
                    "omitted": 0,
                    "samples": [sample],
                },
                "coverage": {
                    "observed": 1,
                    "emitted": 1,
                    "omitted": 0,
                    "limit": DEFAULT_EVIDENCE_LIMIT,
                    "truncated": False,
                    "limitations": [],
                },
            }
        )
    graph_payload["edges"] = edges
    extensions["llm-wiki/typed-graph-v1"] = validate_typed_graph(
        graph_payload,
        concept_kinds={
            concept.locator: (
                concept.concept_kind.value
                if isinstance(concept.concept_kind, ConceptKind)
                else concept.concept_kind
            )
            for concept in concepts
        },
    )
    return extensions


def _governance_supersession_edge_payloads(
    knowledge: KnowledgeIndex,
) -> tuple[str, ...]:
    """Return exact canonical governance-edge payloads for ledger parity."""

    graph = knowledge.extensions.get("llm-wiki/typed-graph-v1")
    if not isinstance(graph, Mapping):
        return ()
    edges = graph.get("edges")
    if not isinstance(edges, list):
        return ()
    return tuple(
        sorted(
            canonical_json_text(edge)
            for edge in edges
            if (
                isinstance(edge, Mapping)
                and edge.get("kind") == "supersedes"
                and edge.get("origin") == "governance"
            )
        )
    )


def _validate_supersession_projection(
    knowledge: KnowledgeIndex,
    expected: set[tuple[str, str]],
) -> None:
    graph = knowledge.extensions.get("llm-wiki/typed-graph-v1")
    observed: set[tuple[str, str]] = set()
    if isinstance(graph, Mapping):
        edges = graph.get("edges")
        if isinstance(edges, list):
            for edge in edges:
                if (
                    not isinstance(edge, Mapping)
                    or edge.get("kind") != "supersedes"
                    or edge.get("origin") != "governance"
                ):
                    continue
                source = edge.get("from")
                target = edge.get("target")
                if isinstance(source, Mapping) and isinstance(target, Mapping):
                    source_uid = source.get("uid")
                    target_uid = target.get("uid")
                    if isinstance(source_uid, str) and isinstance(target_uid, str):
                        observed.add((source_uid, target_uid))
    if observed != expected:
        raise GovernanceError(
            "extensions.llm-wiki/typed-graph-v1.edges",
            "supersedes edges do not match governance successors",
            code="governance-projection-mismatch",
        )


def _section_records_by_locator(
    knowledge: KnowledgeIndex,
) -> dict[str, Mapping[str, object]]:
    from .contracts import SECTION_OWNERSHIP_EXTENSION_KEY

    extension = knowledge.extensions.get(SECTION_OWNERSHIP_EXTENSION_KEY)
    if not isinstance(extension, Mapping):
        return {}
    pages = extension.get("pages")
    if not isinstance(pages, list):
        return {}
    result: dict[str, Mapping[str, object]] = {}
    for page in pages:
        if not isinstance(page, Mapping):
            continue
        sections = page.get("sections")
        if not isinstance(sections, list):
            continue
        for section in sections:
            if not isinstance(section, Mapping):
                continue
            locator = section.get("locator")
            if isinstance(locator, str):
                result[locator] = section
    return result


def _ordered_lifecycle_events(
    values: Sequence[LifecycleEvent],
) -> list[LifecycleEvent]:
    if not values:
        return []
    children = {event.previous_event_id: event for event in values}
    ordered: list[LifecycleEvent] = []
    current = children.get(None)
    while current is not None:
        ordered.append(current)
        current = children.get(current.event_id)
    return ordered


def _lifecycle_event_summary(event: LifecycleEvent) -> dict[str, object]:
    payload: dict[str, object] = {
        "event_id": event.event_id,
        "from": event.from_state.value,
        "to": event.to_state.value,
        "actor": event.actor.to_payload(),
        "authored_at": event.authored_at,
        "reason": event.reason,
    }
    if event.successor_uid is not None:
        payload["successor_uid"] = event.successor_uid
    return payload


def _review_event_summary(
    event: ReviewEvent,
    validity: ReviewValidity,
) -> dict[str, object]:
    return {
        "event_id": event.event_id,
        "section_locator": event.section_locator,
        "state": validity.state,
        "reasons": list(validity.reasons),
        "reviewer": event.reviewer.to_payload(),
        "method": {"id": event.method, "version": event.method_version},
        "authored_at": event.authored_at,
    }


def _bounded_event_payload(
    items: Sequence[dict[str, object]],
    limit: int,
) -> dict[str, object]:
    total = len(items)
    selected = list(items[-limit:])
    return {
        "items": selected,
        "total": total,
        "returned": len(selected),
        "limit": limit,
        "truncated": total > len(selected),
    }


def _event_limit(value: object) -> int:
    if (
        isinstance(value, bool)
        or not isinstance(value, int)
        or not 1 <= value <= MAX_EVENT_LIMIT
    ):
        raise GovernanceError(
            "event_limit",
            f"must be an integer from 1 through {MAX_EVENT_LIMIT}",
        )
    return value


def _nonnegative_int(value: object, path: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise GovernanceError(path, "must be a non-negative integer")
    return value


def _parse_lifecycle_event(event_id: str, value: object) -> LifecycleEvent:
    _event_id(event_id, "lifecycle_events key", prefix="le")
    path = f"lifecycle_events.{event_id}"
    record = _object(value, path)
    _exact_fields(
        record,
        path,
        {
            "concept_uid",
            "previous_event_id",
            "from",
            "to",
            "actor",
            "authored_at",
            "reason",
        },
        optional={"successor_uid"},
    )
    try:
        from_state = Lifecycle(record["from"])
        to_state = Lifecycle(record["to"])
    except (TypeError, ValueError) as exc:
        raise GovernanceError(
            path,
            "from/to must use supported lifecycle states",
        ) from exc
    previous = record["previous_event_id"]
    if previous is not None:
        previous = _event_id(
            previous,
            f"{path}.previous_event_id",
            prefix="le",
        )
    successor = record.get("successor_uid")
    return LifecycleEvent(
        event_id=event_id,
        concept_uid=_concept_uid(record["concept_uid"], f"{path}.concept_uid"),
        previous_event_id=previous,
        from_state=from_state,
        to_state=to_state,
        actor=_parse_actor(record["actor"], f"{path}.actor"),
        authored_at=authored_event_time(record["authored_at"]),
        reason=_machine_code(record["reason"], f"{path}.reason"),
        successor_uid=(
            _concept_uid(successor, f"{path}.successor_uid")
            if successor is not None
            else None
        ),
    )


def _parse_review_event(event_id: str, value: object) -> ReviewEvent:
    _event_id(event_id, "review_events key", prefix="rv")
    path = f"review_events.{event_id}"
    record = _object(value, path)
    _exact_fields(
        record,
        path,
        {
            "concept_uid",
            "section_locator",
            "scope_hash",
            "evidence",
            "reviewer",
            "method",
            "authored_at",
        },
    )
    method = _object(record["method"], f"{path}.method")
    _exact_fields(method, f"{path}.method", {"id", "version"})
    return ReviewEvent(
        event_id=event_id,
        concept_uid=_concept_uid(record["concept_uid"], f"{path}.concept_uid"),
        section_locator=_section_locator(
            record["section_locator"],
            f"{path}.section_locator",
        ),
        scope_hash=_hash(record["scope_hash"], f"{path}.scope_hash"),
        evidence=_parse_review_evidence(
            record["evidence"],
            f"{path}.evidence",
        ),
        reviewer=_parse_actor(record["reviewer"], f"{path}.reviewer"),
        method=_safe_name(method["id"], f"{path}.method.id"),
        method_version=_safe_name(
            method["version"],
            f"{path}.method.version",
        ),
        authored_at=authored_event_time(record["authored_at"]),
    )


def _validate_lifecycle_event_fields(
    event: LifecycleEvent,
    concepts: Mapping[str, GovernanceAllocation],
) -> None:
    path = f"lifecycle_events.{event.event_id}"
    _event_id(event.event_id, path, prefix="le")
    _existing_uid(event.concept_uid, concepts, f"{path}.concept_uid")
    if event.previous_event_id is not None:
        _event_id(
            event.previous_event_id,
            f"{path}.previous_event_id",
            prefix="le",
        )
    if event.to_state is Lifecycle.UNKNOWN:
        raise GovernanceError(f"{path}.to", "cannot transition to unknown")
    if event.to_state not in _ALLOWED_TRANSITIONS[event.from_state]:
        raise GovernanceError(
            f"{path}.to",
            (
                f"transition {event.from_state.value!r} -> "
                f"{event.to_state.value!r} is not allowed"
            ),
            code="governance-transition-invalid",
        )
    _actor(event.actor, f"{path}.actor")
    canonical_time = authored_event_time(event.authored_at)
    if event.authored_at != canonical_time:
        raise GovernanceError(
            f"{path}.authored_at",
            "must use canonical UTC RFC 3339 form",
        )
    _machine_code(event.reason, f"{path}.reason")
    if event.to_state is Lifecycle.SUPERSEDED:
        if event.successor_uid is None:
            raise GovernanceError(
                f"{path}.successor_uid",
                "is required for supersession",
            )
        _existing_uid(event.successor_uid, concepts, f"{path}.successor_uid")
        if event.successor_uid == event.concept_uid:
            raise GovernanceError(
                f"{path}.successor_uid",
                "must identify a different concept",
            )
    elif event.successor_uid is not None:
        raise GovernanceError(
            f"{path}.successor_uid",
            "is valid only for supersession",
        )
    if event.event_id != _derived_event_id(
        "le",
        _lifecycle_event_digest_payload(event),
    ):
        raise GovernanceError(
            path,
            "event ID does not match canonical event content",
            code="governance-event-conflict",
        )


def _validate_lifecycle_histories(
    concepts: Mapping[str, GovernanceAllocation],
    events: Mapping[str, LifecycleEvent],
) -> None:
    by_uid: defaultdict[str, list[LifecycleEvent]] = defaultdict(list)
    for event in events.values():
        by_uid[event.concept_uid].append(event)
    terminal_by_uid: dict[str, LifecycleEvent] = {}
    for uid, concept_events in by_uid.items():
        by_id = {event.event_id: event for event in concept_events}
        children: defaultdict[str | None, list[LifecycleEvent]] = defaultdict(list)
        for event in concept_events:
            if (
                event.previous_event_id is not None
                and event.previous_event_id not in by_id
            ):
                raise GovernanceError(
                    f"lifecycle_events.{event.event_id}.previous_event_id",
                    "does not identify an event for the same concept",
                )
            children[event.previous_event_id].append(event)
        roots = children[None]
        if len(roots) != 1:
            raise GovernanceError(
                f"lifecycle_events.{uid}",
                "must contain exactly one root transition",
                code="governance-event-conflict",
            )
        for parent_id, child_events in children.items():
            if parent_id is not None and len(child_events) > 1:
                raise GovernanceError(
                    f"lifecycle_events.{parent_id}",
                    "has concurrent successor events requiring manual resolution",
                    code="governance-event-conflict",
                )
        visited: set[str] = set()
        state = Lifecycle.UNKNOWN
        current = roots[0]
        while True:
            if current.event_id in visited:
                raise GovernanceError(
                    f"lifecycle_events.{current.event_id}",
                    "contains a predecessor cycle",
                )
            visited.add(current.event_id)
            if current.from_state is not state:
                raise GovernanceError(
                    f"lifecycle_events.{current.event_id}.from",
                    f"must equal prior state {state.value!r}",
                    code="governance-event-conflict",
                )
            state = current.to_state
            next_events = children[current.event_id]
            if not next_events:
                terminal_by_uid[uid] = current
                break
            current = next_events[0]
        if visited != set(by_id):
            event_id = min(set(by_id) - visited)
            raise GovernanceError(
                f"lifecycle_events.{event_id}",
                "is disconnected from the concept's event history",
                code="governance-event-conflict",
            )

    successors = {
        uid: event.successor_uid
        for uid, event in terminal_by_uid.items()
        if event.to_state is Lifecycle.SUPERSEDED
        and event.successor_uid is not None
    }
    for uid in concepts:
        visited: set[str] = set()
        current_uid: str | None = uid
        while current_uid in successors:
            if current_uid in visited:
                raise GovernanceError(
                    f"lifecycle_events.{uid}",
                    "contains a supersession cycle",
                    code="governance-supersession-cycle",
                )
            visited.add(current_uid)
            current_uid = successors[current_uid]


def _validate_review_event_fields(
    event: ReviewEvent,
    concepts: Mapping[str, GovernanceAllocation],
    aliases: Mapping[str, GovernanceAlias],
) -> None:
    path = f"review_events.{event.event_id}"
    _event_id(event.event_id, path, prefix="rv")
    uid = _existing_uid(event.concept_uid, concepts, f"{path}.concept_uid")
    section_locator = _section_locator(
        event.section_locator,
        f"{path}.section_locator",
    )
    _hash(event.scope_hash, f"{path}.scope_hash")
    canonical_evidence = _review_evidence(
        event.evidence,
        f"{path}.evidence",
    )
    if event.evidence != canonical_evidence:
        raise GovernanceError(
            f"{path}.evidence",
            "must use canonical sorted unique evidence values",
        )
    actor = _actor(event.reviewer, f"{path}.reviewer")
    if actor.kind != "human":
        raise GovernanceError(
            f"{path}.reviewer.kind",
            "must be 'human' for a human review event",
        )
    _safe_name(event.method, f"{path}.method")
    _safe_name(event.method_version, f"{path}.method_version")
    canonical_time = authored_event_time(event.authored_at)
    if event.authored_at != canonical_time:
        raise GovernanceError(
            f"{path}.authored_at",
            "must use canonical UTC RFC 3339 form",
        )
    section_page_locator = section_locator.partition("#section/")[0]
    owned_locator_keys = {
        _identity_ownership_key(ALIAS_LOCATOR, concepts[uid].locator)
    }
    owned_locator_keys.update(
        _identity_ownership_key(ALIAS_LOCATOR, alias.value)
        for alias in aliases.values()
        if alias.uid == uid and alias.alias_type == ALIAS_LOCATOR
    )
    if (
        _identity_ownership_key(ALIAS_LOCATOR, section_page_locator)
        not in owned_locator_keys
    ):
        raise GovernanceError(
            f"{path}.section_locator",
            "must belong to the reviewed concept's current or historical locator",
            code="governance-review-scope-mismatch",
        )
    if event.event_id != _derived_event_id(
        "rv",
        _review_event_digest_payload(event),
    ):
        raise GovernanceError(
            path,
            "event ID does not match canonical event content",
            code="governance-event-conflict",
        )


def _parse_review_evidence(value: object, path: str) -> ReviewEvidence:
    record = _object(value, path)
    mode = record.get("mode")
    if mode == "no-source":
        _exact_fields(record, path, {"mode"})
        return ReviewEvidence(mode="no-source")
    _exact_fields(record, path, {"mode", "basis_ids", "basis_hashes"})
    return _review_evidence(
        ReviewEvidence(
            mode=str(mode),
            basis_ids=tuple(_array(record["basis_ids"], f"{path}.basis_ids")),
            basis_hashes=tuple(
                _array(record["basis_hashes"], f"{path}.basis_hashes")
            ),
        ),
        path,
    )


def _review_evidence(value: ReviewEvidence, path: str) -> ReviewEvidence:
    if not isinstance(value, ReviewEvidence):
        raise GovernanceError(path, "must be ReviewEvidence")
    if value.mode not in REVIEW_EVIDENCE_MODES:
        raise GovernanceError(
            f"{path}.mode",
            "must be 'source' or 'no-source'",
        )
    if value.mode == "no-source":
        if value.basis_ids or value.basis_hashes:
            raise GovernanceError(
                path,
                "no-source evidence cannot carry basis IDs or hashes",
            )
        return ReviewEvidence(mode="no-source")
    if not value.basis_ids or not value.basis_hashes:
        raise GovernanceError(
            path,
            "source evidence requires basis IDs and hashes",
        )
    ids = tuple(
        sorted(
            {
                _safe_name(item, f"{path}.basis_ids", allow_slash=True)
                for item in value.basis_ids
            }
        )
    )
    hashes = tuple(
        sorted({_hash(item, f"{path}.basis_hashes") for item in value.basis_hashes})
    )
    return ReviewEvidence(mode="source", basis_ids=ids, basis_hashes=hashes)


def _validated_references(
    values: Sequence[ConceptGovernanceReference],
) -> tuple[ConceptGovernanceReference, ...]:
    if isinstance(values, (str, bytes)) or not isinstance(values, Sequence):
        raise GovernanceError("concepts", "must be a sequence of concept references")
    references: list[ConceptGovernanceReference] = []
    seen_locators: set[str] = set()
    seen_keys: set[str] = set()
    for index, value in enumerate(values):
        if not isinstance(value, ConceptGovernanceReference):
            raise GovernanceError(
                f"concepts[{index}]",
                "must be ConceptGovernanceReference",
            )
        reference = ConceptGovernanceReference(
            locator=_identity_value(
                value.locator,
                ALIAS_LOCATOR,
                f"concepts[{index}].locator",
            ),
            concept_kind=_concept_kind(
                value.concept_kind,
                f"concepts[{index}].concept_kind",
            ),
            natural_key=_identity_value(
                value.natural_key,
                ALIAS_NATURAL_KEY,
                f"concepts[{index}].natural_key",
            ),
        )
        if reference.locator in seen_locators:
            raise GovernanceError(
                f"concepts[{index}].locator",
                "duplicates a current concept locator",
            )
        if reference.natural_key in seen_keys:
            raise GovernanceError(
                f"concepts[{index}].natural_key",
                "duplicates a current concept natural key",
            )
        seen_locators.add(reference.locator)
        seen_keys.add(reference.natural_key)
        references.append(reference)
    return tuple(
        sorted(references, key=lambda item: (item.locator.casefold(), item.locator))
    )


def _put_alias(
    aliases: dict[str, GovernanceAlias],
    alias: GovernanceAlias,
    allocations: Mapping[str, GovernanceAllocation],
) -> dict[str, GovernanceAlias]:
    alias_coordinate = _identity_ownership_key(
        alias.alias_type,
        alias.value,
    )
    for uid, allocation in allocations.items():
        current = (
            allocation.locator
            if alias.alias_type == ALIAS_LOCATOR
            else allocation.natural_key
        )
        if (
            _identity_ownership_key(alias.alias_type, current)
            == alias_coordinate
        ):
            if uid == alias.uid:
                return aliases
            raise GovernanceError(
                f"aliases.{alias.key}",
                f"is currently owned by UID {uid!r}",
                code="governance-alias-conflict",
            )
    for existing in aliases.values():
        if (
            existing.alias_type == alias.alias_type
            and _identity_ownership_key(
                existing.alias_type,
                existing.value,
            )
            == alias_coordinate
        ):
            if existing.uid == alias.uid:
                return aliases
            raise GovernanceError(
                f"aliases.{alias.key}",
                f"is already owned by UID {existing.uid!r}",
                code="governance-alias-conflict",
            )
    aliases[alias.key] = alias
    return aliases


def _write_durable_atomic(
    path: Path,
    content: bytes,
    *,
    fault_injector: FaultInjector | None,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temp_name = tempfile.mkstemp(
        dir=path.parent,
        prefix=f".{path.name}.",
        suffix=".tmp",
    )
    temp_path = Path(temp_name)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        if fault_injector is not None:
            fault_injector(GovernanceWriteStage.TEMP_DURABLE)
        os.replace(temp_path, path)
        if fault_injector is not None:
            fault_injector(GovernanceWriteStage.REPLACED)
        _fsync_directory(path.parent)
        if fault_injector is not None:
            fault_injector(GovernanceWriteStage.DIRECTORY_DURABLE)
    except BaseException:
        try:
            temp_path.unlink()
        except OSError:
            pass
        raise


def _fsync_directory(path: Path) -> None:
    if os.name == "nt":
        return
    flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0)
    try:
        descriptor = os.open(path, flags)
    except OSError:
        return
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _governance_lock_root(wiki_dir: Path) -> Path:
    resolved = wiki_dir.resolve(strict=False)
    for candidate in (resolved, *resolved.parents):
        git = candidate / ".git"
        try:
            metadata = git.lstat()
        except (FileNotFoundError, OSError):
            continue
        attributes = getattr(metadata, "st_file_attributes", 0)
        reparse_flag = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0)
        if stat.S_ISDIR(metadata.st_mode) and not (
            bool(reparse_flag) and bool(attributes & reparse_flag)
        ):
            return git
    return resolved


def _decode_unique_json(content: bytes) -> object:
    def unique_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
        result: dict[str, object] = {}
        for key, value in pairs:
            if key in result:
                raise GovernanceError(
                    GOVERNANCE_FILENAME,
                    f"contains duplicate JSON key {key!r}",
                )
            result[key] = value
        return result

    def reject_constant(value: str) -> None:
        raise GovernanceError(
            GOVERNANCE_FILENAME,
            f"contains non-finite JSON number {value!r}",
        )

    try:
        return json.loads(
            content.decode("utf-8"),
            object_pairs_hook=unique_object,
            parse_constant=reject_constant,
        )
    except GovernanceError:
        raise
    except (UnicodeError, json.JSONDecodeError, RecursionError) as exc:
        raise GovernanceError(
            GOVERNANCE_FILENAME,
            "must contain valid UTF-8 JSON without conflict markers",
        ) from exc


def _parse_actor(value: object, path: str) -> GovernanceActor:
    record = _object(value, path)
    _exact_fields(record, path, {"kind", "id"})
    return _actor(
        GovernanceActor(kind=str(record["kind"]), actor_id=str(record["id"])),
        path,
    )


def _actor(value: GovernanceActor, path: str) -> GovernanceActor:
    if not isinstance(value, GovernanceActor):
        raise GovernanceError(path, "must be GovernanceActor")
    if value.kind not in ACTOR_KINDS:
        raise GovernanceError(
            f"{path}.kind",
            f"must be one of {', '.join(sorted(ACTOR_KINDS))}",
        )
    actor_id = _safe_name(value.actor_id, f"{path}.id")
    return GovernanceActor(value.kind, actor_id)


def _object(value: object, path: str) -> dict[str, object]:
    if not isinstance(value, Mapping):
        raise GovernanceError(path, "must be an object")
    result: dict[str, object] = {}
    for key, item in value.items():
        if not isinstance(key, str):
            raise GovernanceError(path, "must use string keys")
        result[key] = item
    return result


def _array(value: object, path: str) -> list[object]:
    if not isinstance(value, list):
        raise GovernanceError(path, "must be an array")
    return value


def _exact_fields(
    value: Mapping[str, object],
    path: str,
    required: set[str],
    *,
    optional: set[str] = frozenset(),
) -> None:
    missing = required - set(value)
    if missing:
        raise GovernanceError(f"{path}.{min(missing)}", "is required")
    unknown = set(value) - required - optional
    if unknown:
        raise GovernanceError(f"{path}.{min(unknown)}", "is not supported")


def _safe_id(value: object, path: str) -> str:
    if not isinstance(value, str) or _SAFE_ID_RE.fullmatch(value) is None:
        raise GovernanceError(
            path,
            "must be a normalized 3-128 character machine identifier",
        )
    _safe_text(value, path)
    return value


def _event_id(value: object, path: str, *, prefix: str) -> str:
    if (
        not isinstance(value, str)
        or _EVENT_ID_RE.fullmatch(value) is None
        or not value.startswith(f"{prefix}_")
    ):
        raise GovernanceError(path, f"must be a canonical {prefix} event ID")
    return value


def _lifecycle_event_digest_payload(
    event: LifecycleEvent,
) -> dict[str, object]:
    payload = event.to_payload()
    # The nullable successor is part of the v1 event digest domain even though
    # the serialized event omits it when no successor exists.
    payload["successor_uid"] = event.successor_uid
    return payload


def _review_event_digest_payload(event: ReviewEvent) -> dict[str, object]:
    return event.to_payload()


def _derived_event_id(prefix: str, payload: Mapping[str, object]) -> str:
    digest = sha256_bytes(
        canonical_json_text(
            {
                "domain": f"llm-wiki/governance-{prefix}-event/v1",
                "event": payload,
            }
        ).encode("utf-8")
    )
    return f"{prefix}_{digest.removeprefix('sha256:')}"


def _safe_name(
    value: object,
    path: str,
    *,
    allow_slash: bool = False,
) -> str:
    if (
        not isinstance(value, str)
        or not value
        or value != value.strip()
        or len(value) > 256
        or _CONTROL_RE.search(value)
        or (not allow_slash and "/" in value)
    ):
        raise GovernanceError(path, "must be a normalized bounded machine name")
    _safe_text(value, path)
    return value


def _safe_text(value: str, path: str) -> None:
    if _CONTROL_RE.search(value):
        raise GovernanceError(path, "must not contain control characters")
    if _SENSITIVE_RE.search(value):
        raise GovernanceError(path, "must not contain credential-like fields")
    if contains_uri_authority_userinfo(value):
        raise GovernanceError(path, "must not contain URI credentials")
    if value.startswith("/") or _WINDOWS_ABSOLUTE_RE.match(value):
        raise GovernanceError(path, "must not contain an absolute path")


def _machine_code(value: object, path: str) -> str:
    if not isinstance(value, str) or _MACHINE_CODE_RE.fullmatch(value) is None:
        raise GovernanceError(
            path,
            "must be a lowercase hyphen-separated machine reason",
        )
    return value


def _alias_type(value: object, path: str) -> str:
    if not isinstance(value, str) or value not in ALIAS_TYPES:
        raise GovernanceError(
            path,
            "must be 'locator' or 'natural-key'",
        )
    return value


def _identity_value(value: object, alias_type: str, path: str) -> str:
    selected_type = _alias_type(alias_type, f"{path}.type")
    try:
        return validate_alias_value(
            (
                AliasType.LOCATOR
                if selected_type == ALIAS_LOCATOR
                else AliasType.NATURAL_KEY
            ),
            value,
        )
    except ConceptIdentityError as exc:
        raise GovernanceError(path, exc.message) from exc


def _identity_ownership_key(alias_type: str, value: str) -> str:
    selected = (
        AliasType.LOCATOR
        if alias_type == ALIAS_LOCATOR
        else AliasType.NATURAL_KEY
    )
    try:
        return identity_coordinate_key(selected, value)
    except ConceptIdentityError as exc:
        raise GovernanceError("identity", exc.message) from exc


def _relative_path(value: object, path: str) -> str:
    if (
        not isinstance(value, str)
        or not value
        or value.startswith("/")
        or _WINDOWS_ABSOLUTE_RE.match(value)
        or "\\" in value
        or value != value.strip()
    ):
        raise GovernanceError(path, "must be a repository-relative POSIX path")
    parts = value.split("/")
    if any(part in {"", ".", ".."} for part in parts):
        raise GovernanceError(path, "must be a normalized relative path")
    _safe_text(value, path)
    return value


def _section_locator(value: object, path: str) -> str:
    if (
        not isinstance(value, str)
        or not value.startswith("llm-wiki://")
        or "#section/" not in value
        or "?" in value
        or value != value.strip()
    ):
        raise GovernanceError(
            path,
            "must be an exact llm-wiki section locator",
        )
    _safe_text(value, path)
    return value


def _hash(value: object, path: str) -> str:
    if not is_valid_sha256(value):
        raise GovernanceError(path, "must be a canonical SHA-256 value")
    assert isinstance(value, str)
    return value


def _existing_uid(
    value: object,
    concepts: Mapping[str, GovernanceAllocation],
    path: str,
) -> str:
    uid = _concept_uid(value, path)
    if uid not in concepts:
        raise GovernanceError(path, "does not identify an allocated concept")
    return uid


def _bundle_id(value: object, path: str) -> str:
    try:
        return validate_bundle_id(value)
    except ConceptIdentityError as exc:
        raise GovernanceError(path, exc.message) from exc


def _concept_kind(value: object, path: str) -> str:
    try:
        return validate_concept_kind(value)
    except ConceptIdentityError as exc:
        raise GovernanceError(path, exc.message) from exc


def _concept_uid(value: object, path: str) -> str:
    try:
        return validate_concept_uid(value)
    except ConceptIdentityError as exc:
        raise GovernanceError(path, exc.message) from exc


def _natural_key(value: object, path: str) -> str:
    try:
        return validate_natural_key(value)
    except ConceptIdentityError as exc:
        raise GovernanceError(path, exc.message) from exc


__all__ = [
    "ACTOR_KINDS",
    "ALIAS_LOCATOR",
    "ALIAS_NATURAL_KEY",
    "ALIAS_TYPES",
    "ConceptGovernanceReference",
    "DEFAULT_EVENT_LIMIT",
    "GOVERNANCE_EXTENSION_KEY",
    "GOVERNANCE_FILENAME",
    "GOVERNANCE_HASH_EXTENSION_KEY",
    "GOVERNANCE_SCHEMA_VERSION",
    "GovernanceActor",
    "GovernanceAlias",
    "GovernanceAllocation",
    "GovernanceConflictError",
    "GovernanceError",
    "GovernanceLedger",
    "GovernanceLoadResult",
    "GovernanceWriteResult",
    "GovernanceWriteStage",
    "LifecycleEvent",
    "MAX_ALIASES_PER_CONCEPT",
    "MAX_EVENT_LIMIT",
    "MAX_LEDGER_BYTES",
    "REVIEW_EXPIRY_REASONS",
    "ReviewEvidence",
    "ReviewEvent",
    "ReviewValidity",
    "add_alias",
    "add_review_event",
    "apply_governance_projection",
    "alias_key",
    "authored_event_time",
    "concept_references_from_knowledge",
    "current_review_evidence",
    "current_lifecycle",
    "derive_concept_uid",
    "evaluate_review_event",
    "governance_bundle_id_from_knowledge",
    "governance_lock",
    "governance_hash_from_knowledge",
    "lifecycle_state_by_uid",
    "load_governance",
    "move_concept",
    "natural_key_for",
    "parse_governance_ledger",
    "reconcile_concepts",
    "review_scope_hash",
    "save_governance",
    "set_lifecycle",
    "strip_governance_projection",
    "validate_governance_ledger",
    "validate_governance_projection",
]
