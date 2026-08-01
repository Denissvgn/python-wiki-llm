"""Safe, deterministic projections over one validated knowledge read view.

The native knowledge index is repository-sensitive.  This module is the only
boundary that turns it into exporter-facing data.  Projection is pure over a
supplied :class:`KnowledgeReadView`: it performs no file reads, source
discovery, extraction, governance mutation, subprocess work, or network I/O.

The ``public-portable`` profile is deliberately allowlist-only.  Unknown
extensions, actors, producer details, raw evidence, source coordinates, remote
identities, and non-parity hashes are never visited while constructing it.
"""

from __future__ import annotations

import json
import math
import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from enum import Enum
from types import MappingProxyType
from typing import Any, NoReturn

from .concept_identity import (
    ConceptIdentityError,
    validate_bundle_id,
    validate_concept_uid,
)
from .contracts import (
    GOVERNANCE_EXTENSION_KEY,
    GOVERNANCE_HASH_EXTENSION_KEY,
    SECTION_OWNERSHIP_EXTENSION_KEY,
    TYPED_GRAPH_EXTENSION_KEY,
)
from .knowledge_artifacts import validate_knowledge_artifacts
from .knowledge_consumption import (
    KnowledgeAvailability,
    KnowledgeReadView,
    MachineVerificationAvailability,
)
from .knowledge_evidence import sha256_bytes
from .knowledge_envelope import (
    KnowledgeEnvelopeError,
    validate_configured_public_identity,
)
from .knowledge_freshness import (
    KNOWN_FRESHNESS_REASON_CODES,
    REASON_RECORDED_BASIS_MATCHES_LIVE_EVALUATION,
)
from .knowledge_governance import validate_governance_projection
from .knowledge_graph import (
    CORE_RELATIONSHIP_KINDS,
    ENDPOINT_KINDS,
    GRAPH_EVIDENCE_STATES,
    GRAPH_ORIGINS,
    GRAPH_RESOLUTIONS,
    typed_graph_from_knowledge_extensions,
)
from .knowledge_model import (
    ActorKind,
    ConceptKind,
    ConceptRecord,
    ComputedFreshness,
    EVALUATED_REVISION_PATTERN,
    EvidenceState,
    KnowledgeIndex,
    KnowledgeProjectionProfile,
    Lifecycle,
    LIMITATION_CODE_PATTERN,
    ObservationScope,
    Origin,
    REPOSITORY_IDENTITY_SOURCE_EXTENSION,
    RepositoryIdentitySource,
    Verification,
    WorkingTreeState,
    serialize_knowledge_index,
)
from .knowledge_observability import (
    UNEVALUATED_FRESHNESS_DISCLOSURE,
    knowledge_freshness_disclosure,
    knowledge_freshness_hint,
)
from .redaction import (
    CREDENTIAL_VALUE_RE as _CREDENTIAL_VALUE_RE,
    PROJECTION_URI_USERINFO_RE as _URI_USERINFO_RE,
    SENSITIVE_KEY_RE as _SENSITIVE_KEY_RE,
)
from .validation import (
    require_bool as require_shared_bool,
    require_choice as require_shared_choice,
    require_exact_fields as require_shared_exact_fields,
    require_mapping as require_shared_mapping,
    require_nonnegative_int as require_shared_nonnegative_int,
    require_portable_relative_path,
    require_positive_int as require_shared_positive_int,
    require_sequence as require_shared_sequence,
    require_sha256 as require_shared_sha256,
)
from .wiki_surface import PageKind, SurfaceRole

PROJECTION_SCHEMA_VERSION = "llm-wiki-knowledge-projection/v1"
DEFAULT_RELATIONSHIP_LIMIT = 20
MAX_RELATIONSHIP_LIMIT = 1000
UNKNOWN_VALUE = "unknown"
NOT_EVALUATED = "not-evaluated"
_EVALUATED_FRESHNESS_DISCLOSURE_RE = re.compile(
    r"^evaluated \((0|[1-9][0-9]*) concepts\)$"
)

_RESERVED_EXTENSION_KEYS = frozenset(
    {
        GOVERNANCE_EXTENSION_KEY,
        GOVERNANCE_HASH_EXTENSION_KEY,
        "llm-wiki/inventory-hash",
        "llm-wiki/link-syntax",
        REPOSITORY_IDENTITY_SOURCE_EXTENSION,
        SECTION_OWNERSHIP_EXTENSION_KEY,
        TYPED_GRAPH_EXTENSION_KEY,
    }
)
_WINDOWS_ABSOLUTE_RE = re.compile(r"^[A-Za-z]:[/\\]")
_TRAVERSAL_RE = re.compile(r"(?:^|[/\\])\.\.(?:[/\\]|$)")
_EMBEDDED_ABSOLUTE_RE = re.compile(
    r"(?:^|[\s\"'=(])(?:/(?!/)[^\s\"']+|[A-Za-z]:[/\\][^\s\"']*)"
)
_RAW_VCS_REMOTE_RE = re.compile(
    r"(?:\bgit@[A-Za-z0-9.-]+:[^\s]+|"
    r"\b(?:https?|ssh|git)://[^\s]+(?:\.git|/(?:scm|git)/))",
    re.IGNORECASE,
)
_CONTROL_RE = re.compile(r"[\x00-\x1f\x7f]")
_EVALUATED_REVISION_RE = re.compile(EVALUATED_REVISION_PATTERN)
_LIMITATION_CODE_RE = re.compile(LIMITATION_CODE_PATTERN)
_QUALIFIED_RELATIONSHIP_KIND_RE = re.compile(
    r"^[A-Za-z][A-Za-z0-9._-]*/[A-Za-z][A-Za-z0-9._-]*$"
)
_SAFE_TOKEN_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._~:@/+?#=-]{0,511}$")
_REVIEW_EXPIRY_REASONS = frozenset(
    {
        "scope-changed",
        "evidence-changed",
        "basis-incompatible",
        "section-missing",
        "concept-missing",
    }
)
_REVIEW_STATES = frozenset(
    {
        "untracked",
        "partial",
        "mixed",
        "has-valid-sections",
        "has-expired-sections",
        UNKNOWN_VALUE,
    }
)
_MACHINE_INVALIDATION_REASONS = frozenset(
    {
        "knowledge-changed",
        "scope-changed",
        "evidence-changed",
        "snapshot-changed",
        "unknown-checker",
        "checker-version-changed",
    }
)
_OMISSION_FIELDS = frozenset(
    {
        "actor_identities",
        "credential_like_values",
        "environment_details",
        "evidence_payloads",
        "external_target_details",
        "internal_hashes",
        "private_repository_identity",
        "private_producer_records",
        "relationship_evidence_samples",
        "semantic_page_hashes",
        "source_target_details",
        "unapproved_concept_kinds",
        "unapproved_relationship_kinds",
        "unknown_extensions",
        "unresolved_target_details",
        "unsafe_paths",
    }
)
_BASE_WARNING_VALUES = frozenset(
    {
        "typed-graph-not-available",
        "governance-not-available",
        "freshness-not-evaluated",
    }
)


class KnowledgeProjectionError(ValueError):
    """Stable failure at the validated projection boundary."""

    def __init__(self, code: str, field: str, message: str):
        self.code = code
        self.field = field
        self.message = message
        super().__init__(f"{field}: {message}")


@dataclass(frozen=True)
class KnowledgeProjection:
    """One deterministic exporter-facing projection."""

    schema_version: str
    profile: KnowledgeProjectionProfile
    source_knowledge_hash: str
    bundle: Mapping[str, Any]
    concepts: Mapping[str, Mapping[str, Any]]
    warnings: tuple[str, ...]
    omitted_fields: Mapping[str, int]
    freshness: str | None = None

    def __post_init__(self) -> None:
        """Detach and recursively freeze every caller-supplied container."""

        object.__setattr__(self, "bundle", _deep_freeze(self.bundle, "bundle"))
        object.__setattr__(
            self,
            "concepts",
            _deep_freeze(self.concepts, "concepts"),
        )
        object.__setattr__(
            self,
            "warnings",
            _deep_freeze(self.warnings, "warnings"),
        )
        object.__setattr__(
            self,
            "omitted_fields",
            _deep_freeze(self.omitted_fields, "omitted_fields"),
        )
        object.__setattr__(
            self,
            "freshness",
            (
                UNEVALUATED_FRESHNESS_DISCLOSURE
                if self.freshness is None
                else self.freshness
            ),
        )

    def to_payload(self) -> dict[str, Any]:
        """Return a detached JSON-compatible payload."""

        _validate_projection_structure(self)
        return {
            "schema_version": self.schema_version,
            "profile": self.profile.value,
            "source_knowledge_hash": self.source_knowledge_hash,
            "freshness": self.freshness,
            "bundle": _json_copy(self.bundle),
            "concepts": {
                path: _json_copy(self.concepts[path])
                for path in sorted(self.concepts)
            },
            "warnings": list(self.warnings),
            "omitted_fields": {
                name: self.omitted_fields[name]
                for name in sorted(self.omitted_fields)
            },
        }

    def concept_for_path(self, canonical_path: str) -> Mapping[str, Any] | None:
        """Return one projected concept by exact canonical Markdown path."""

        if not isinstance(canonical_path, str):
            raise TypeError("canonical_path must be a string")
        return self.concepts.get(canonical_path)


def project_knowledge(
    view: KnowledgeReadView,
    *,
    profile: KnowledgeProjectionProfile | str = (
        KnowledgeProjectionProfile.PUBLIC_PORTABLE
    ),
    relationship_limit: int = DEFAULT_RELATIONSHIP_LIMIT,
    public_repository_identity: str | None = None,
) -> KnowledgeProjection:
    """Build an allowlisted projection from one validated read session."""

    selected_profile = _projection_profile(profile)
    limit = _relationship_limit(relationship_limit)
    knowledge, source_knowledge_hash = _validated_source(view)
    approved_public_identity = _approved_public_repository_identity(
        knowledge,
        selected_profile,
        public_repository_identity,
    )
    governance = validate_governance_projection(knowledge)
    bundle_id = (
        str(governance["bundle_id"])
        if governance is not None
        else UNKNOWN_VALUE
    )

    omitted = _initial_omitted_counts(knowledge, selected_profile)
    concepts_by_locator = {item.locator: item for item in knowledge.concepts}
    governance_by_locator = {
        concept.locator: _governance_summary(concept)
        for concept in knowledge.concepts
    }
    concepts_by_uid = {
        str(summary["uid"]): concepts_by_locator[locator]
        for locator, summary in governance_by_locator.items()
        if isinstance(summary, Mapping) and isinstance(summary.get("uid"), str)
    }
    relation_sets, graph_available = _project_relationships(
        knowledge,
        concepts_by_locator=concepts_by_locator,
        concepts_by_uid=concepts_by_uid,
        bundle_id=bundle_id,
        profile=selected_profile,
        limit=limit,
        omitted=omitted,
    )

    projected_concepts: dict[str, Mapping[str, Any]] = {}
    for concept in sorted(
        knowledge.concepts,
        key=lambda value: value.document.canonical_path,
    ):
        projected = _project_concept(
            concept,
            view=view,
            bundle_id=bundle_id,
            governance=governance_by_locator[concept.locator],
            relationships=relation_sets.get(
                concept.locator,
                _empty_relationships(graph_available, limit),
            ),
            profile=selected_profile,
            omitted=omitted,
        )
        path = concept.document.canonical_path
        if path in projected_concepts:
            raise KnowledgeProjectionError(
                "projection-coordinate-collision",
                "concepts",
                f"multiple concepts claim canonical path {path!r}",
            )
        projected_concepts[path] = MappingProxyType(projected)

    bundle = _project_bundle(
        knowledge,
        bundle_id=bundle_id,
        profile=selected_profile,
        approved_public_identity=approved_public_identity,
        omitted=omitted,
    )
    warnings = _projection_warnings(
        projected_concepts,
        graph_available=graph_available,
        governance_available=governance is not None,
        omitted=omitted,
    )
    projection = KnowledgeProjection(
        schema_version=PROJECTION_SCHEMA_VERSION,
        profile=selected_profile,
        source_knowledge_hash=source_knowledge_hash,
        bundle=MappingProxyType(bundle),
        concepts=MappingProxyType(
            {path: projected_concepts[path] for path in sorted(projected_concepts)}
        ),
        warnings=warnings,
        omitted_fields=MappingProxyType(
            {
                name: count
                for name, count in sorted(omitted.items())
                if count > 0
            }
        ),
        freshness=knowledge_freshness_disclosure(view),
    )
    _validate_projection_structure(projection)
    return projection


def serialize_knowledge_projection(projection: KnowledgeProjection) -> str:
    """Serialize a projection deterministically with one trailing newline."""

    if not isinstance(projection, KnowledgeProjection):
        raise TypeError("projection must be a KnowledgeProjection")
    return (
        json.dumps(
            projection.to_payload(),
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
            allow_nan=False,
        )
        + "\n"
    )


def projection_json_value(value: object) -> Any:
    """Detach one deeply frozen projection value for JSON-only consumers."""

    return _json_copy(value)


def projection_concept_summary(
    projection: KnowledgeProjection,
    canonical_path: str,
) -> dict[str, str]:
    """Flatten the documented safe concept subset for Markdown front matter."""

    if not isinstance(projection, KnowledgeProjection):
        raise TypeError("projection must be a KnowledgeProjection")
    _validate_projection_structure(projection)
    return _projection_concept_summary_unchecked(projection, canonical_path)


def _projection_concept_summary_unchecked(
    projection: KnowledgeProjection,
    canonical_path: str,
) -> dict[str, str]:
    concept = projection.concept_for_path(canonical_path)
    if concept is None:
        raise KnowledgeProjectionError(
            "projection-concept-absent",
            "canonical_path",
            f"has no projected concept for {canonical_path!r}",
        )
    identity = _mapping(concept.get("identity"))
    lifecycle = _mapping(concept.get("lifecycle"))
    evidence = _mapping(concept.get("evidence"))
    freshness = _mapping(concept.get("freshness"))
    review = _mapping(concept.get("review"))
    machine_check = _mapping(concept.get("machine_check"))
    summary = {
        "freshness": str(
            projection.freshness or UNEVALUATED_FRESHNESS_DISCLOSURE
        ),
        "knowledge_projection_schema": projection.schema_version,
        "knowledge_profile": projection.profile.value,
        "knowledge_bundle_id": str(identity.get("bundle_id", UNKNOWN_VALUE)),
        "knowledge_repository_identity": str(
            projection.bundle.get("repository_identity", UNKNOWN_VALUE)
        ),
        "knowledge_repository_identity_source": str(
            projection.bundle.get(
                "repository_identity_source",
                RepositoryIdentitySource.UNKNOWN.value,
            )
        ),
        "knowledge_uid": str(identity.get("namespaced_uid", UNKNOWN_VALUE)),
        "knowledge_concept_kind": str(
            concept.get("concept_kind", UNKNOWN_VALUE)
        ),
        "knowledge_lifecycle": str(
            lifecycle.get("state", UNKNOWN_VALUE)
        ),
        "knowledge_successor_uid": str(
            lifecycle.get("successor_namespaced_uid", UNKNOWN_VALUE)
        ),
        "knowledge_evidence": str(evidence.get("state", UNKNOWN_VALUE)),
        "knowledge_evidence_reason": str(
            evidence.get("reason", "structural-evidence-unknown")
        ),
        "knowledge_freshness": str(
            freshness.get("state", NOT_EVALUATED)
        ),
        "knowledge_freshness_reason": str(
            freshness.get("reason", NOT_EVALUATED)
        ),
        "knowledge_review": str(review.get("state", "untracked")),
        "knowledge_review_total": str(review.get("total", 0)),
        "knowledge_review_scope": "section",
        "knowledge_review_returned": str(review.get("returned", 0)),
        "knowledge_review_valid": str(review.get("valid_returned", 0)),
        "knowledge_review_expired": str(
            review.get("expired_returned", 0)
        ),
        "knowledge_review_items": json.dumps(
            _json_copy(review.get("items", [])),
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        ),
        "knowledge_review_truncated": _boolean_text(
            bool(review.get("truncated", False))
        ),
        "knowledge_machine_check": str(
            machine_check.get("state", "not-run")
        ),
        "knowledge_machine_check_reason": str(
            machine_check.get("reason", "verification-untracked")
        ),
        "knowledge_machine_check_result": str(
            machine_check.get("recorded_result", NOT_EVALUATED)
        ),
        "knowledge_machine_check_total": str(
            _mapping(machine_check.get("checks")).get("total", 0)
        ),
        "knowledge_machine_check_passed": str(
            _mapping(machine_check.get("checks")).get("passed", 0)
        ),
        "knowledge_machine_check_failed": str(
            _mapping(machine_check.get("checks")).get("failed", 0)
        ),
        "source_knowledge_hash": projection.source_knowledge_hash,
    }
    hint = freshness.get("hint")
    if isinstance(hint, str):
        summary["knowledge_freshness_hint"] = hint
    return summary


def validate_projection_summaries(
    projection: KnowledgeProjection,
    canonical_paths: Sequence[str],
) -> dict[str, dict[str, str]]:
    """Validate one projection for an exact derived-output page set.

    Exporters accept an in-memory projection rather than trusting arbitrary
    flattened metadata.  This shared guard ensures both derived surfaces apply
    the same schema, snapshot, page, governed-identity, and lifecycle-reference
    rules before they perform a write.
    """

    if not isinstance(projection, KnowledgeProjection):
        raise KnowledgeProjectionError(
            "projection-type-invalid",
            "projection",
            "must be a KnowledgeProjection",
        )
    if projection.schema_version != PROJECTION_SCHEMA_VERSION:
        raise KnowledgeProjectionError(
            "projection-schema-invalid",
            "schema_version",
            f"must be {PROJECTION_SCHEMA_VERSION!r}",
        )
    if not isinstance(projection.bundle, Mapping):
        raise KnowledgeProjectionError(
            "projection-bundle-invalid",
            "bundle",
            "must be a mapping",
        )
    if not isinstance(projection.concepts, Mapping):
        raise KnowledgeProjectionError(
            "projection-concepts-invalid",
            "concepts",
            "must be a canonical-path mapping",
        )
    if not isinstance(projection.profile, KnowledgeProjectionProfile):
        raise KnowledgeProjectionError(
            "projection-profile-invalid",
            "profile",
            "must be 'internal' or 'public-portable'",
        )
    if (
        not isinstance(projection.source_knowledge_hash, str)
        or re.fullmatch(
            r"sha256:[0-9a-f]{64}",
            projection.source_knowledge_hash,
        )
        is None
    ):
        raise KnowledgeProjectionError(
            "projection-source-hash-invalid",
            "source_knowledge_hash",
            "must be a canonical sha256:<64 lowercase hexadecimal> value",
        )

    _validate_projection_structure(projection)
    if (
        isinstance(canonical_paths, (str, bytes))
        or not isinstance(canonical_paths, Sequence)
        or any(not isinstance(path, str) for path in canonical_paths)
    ):
        raise KnowledgeProjectionError(
            "projection-page-set-invalid",
            "canonical_paths",
            "must be a sequence of canonical path strings",
        )
    expected_paths = set(canonical_paths)
    if len(expected_paths) != len(canonical_paths):
        raise KnowledgeProjectionError(
            "projection-page-set-invalid",
            "canonical_paths",
            "must not contain duplicate page coordinates",
        )
    projected_paths = set(projection.concepts)
    if projected_paths != expected_paths:
        missing = sorted(expected_paths - projected_paths)
        stale = sorted(projected_paths - expected_paths)
        details: list[str] = []
        if missing:
            details.append("missing=" + ",".join(missing))
        if stale:
            details.append("stale=" + ",".join(stale))
        raise KnowledgeProjectionError(
            "projection-page-set-mismatch",
            "concepts",
            "does not match the exported page set: " + "; ".join(details),
        )

    try:
        bundle_id = validate_bundle_id(projection.bundle.get("bundle_id"))
    except ConceptIdentityError as exc:
        raise KnowledgeProjectionError(
            "projection-bundle-invalid",
            "bundle.bundle_id",
            exc.message,
        ) from exc
    repository_identity = projection.bundle.get("repository_identity")
    repository_identity_source = projection.bundle.get(
        "repository_identity_source"
    )
    allowed_identity_sources = {
        RepositoryIdentitySource.UNKNOWN.value,
        RepositoryIdentitySource.CONFIGURED_PUBLIC.value,
    }
    if projection.profile is KnowledgeProjectionProfile.INTERNAL:
        allowed_identity_sources.add(
            RepositoryIdentitySource.NORMALIZED_VCS.value
        )
    if (
        not isinstance(repository_identity, str)
        or repository_identity_source not in allowed_identity_sources
        or (
            (repository_identity == UNKNOWN_VALUE)
            != (
                repository_identity_source
                == RepositoryIdentitySource.UNKNOWN.value
            )
        )
    ):
        raise KnowledgeProjectionError(
            "projection-repository-identity-invalid",
            "bundle.repository_identity",
            "must agree with an allowed repository identity source",
        )
    if repository_identity != UNKNOWN_VALUE:
        try:
            validate_configured_public_identity(repository_identity)
        except KnowledgeEnvelopeError as exc:
            raise KnowledgeProjectionError(
                "projection-repository-identity-invalid",
                "bundle.repository_identity",
                exc.message,
            ) from exc

    summaries: dict[str, dict[str, str]] = {}
    seen_uids: dict[str, str] = {}
    successor_sources: dict[str, list[str]] = {}
    for canonical_path in sorted(expected_paths):
        concept = projection.concepts[canonical_path]
        if not isinstance(concept, Mapping):
            raise KnowledgeProjectionError(
                "projection-concept-invalid",
                f"concepts.{canonical_path}",
                "must be a mapping",
            )
        if concept.get("canonical_path") != canonical_path:
            raise KnowledgeProjectionError(
                "projection-coordinate-mismatch",
                f"concepts.{canonical_path}.canonical_path",
                "must exactly match its projection map key",
            )
        identity = _mapping(concept.get("identity"))
        if identity.get("bundle_id") != bundle_id:
            raise KnowledgeProjectionError(
                "projection-bundle-mismatch",
                f"concepts.{canonical_path}.identity.bundle_id",
                f"must equal governed bundle {bundle_id!r}",
            )
        try:
            uid = validate_concept_uid(identity.get("uid"))
        except ConceptIdentityError as exc:
            raise KnowledgeProjectionError(
                "projection-uid-invalid",
                f"concepts.{canonical_path}.identity.uid",
                exc.message,
            ) from exc
        namespaced_uid = identity.get("namespaced_uid")
        expected_uid = f"{bundle_id}#{uid}"
        if namespaced_uid != expected_uid:
            raise KnowledgeProjectionError(
                "projection-namespaced-uid-invalid",
                f"concepts.{canonical_path}.identity.namespaced_uid",
                f"must be exactly {expected_uid!r}",
            )
        prior = seen_uids.get(expected_uid)
        if prior is not None:
            raise KnowledgeProjectionError(
                "projection-uid-collision",
                f"concepts.{canonical_path}.identity.namespaced_uid",
                f"duplicates the UID projected for {prior!r}",
            )
        seen_uids[expected_uid] = canonical_path

        summary = _projection_concept_summary_unchecked(
            projection,
            canonical_path,
        )
        if summary["knowledge_bundle_id"] != bundle_id:
            raise KnowledgeProjectionError(
                "projection-summary-bundle-mismatch",
                f"concepts.{canonical_path}.identity.bundle_id",
                "does not match the flattened summary",
            )
        if summary["knowledge_uid"] != expected_uid:
            raise KnowledgeProjectionError(
                "projection-summary-uid-mismatch",
                f"concepts.{canonical_path}.identity.namespaced_uid",
                "does not match the flattened summary",
            )
        successor_uid = summary["knowledge_successor_uid"]
        if successor_uid != UNKNOWN_VALUE:
            prefix = f"{bundle_id}#"
            if not successor_uid.startswith(prefix):
                raise KnowledgeProjectionError(
                    "projection-successor-invalid",
                    f"concepts.{canonical_path}.lifecycle.successor_namespaced_uid",
                    "must use the same governed bundle namespace",
                )
            try:
                validate_concept_uid(successor_uid[len(prefix) :])
            except ConceptIdentityError as exc:
                raise KnowledgeProjectionError(
                    "projection-successor-invalid",
                    (
                        f"concepts.{canonical_path}.lifecycle."
                        "successor_namespaced_uid"
                    ),
                    exc.message,
                ) from exc
            if successor_uid == expected_uid:
                raise KnowledgeProjectionError(
                    "projection-successor-self-reference",
                    (
                        f"concepts.{canonical_path}.lifecycle."
                        "successor_namespaced_uid"
                    ),
                    "must identify a different concept",
                )
            successor_sources.setdefault(successor_uid, []).append(
                canonical_path
            )
        summaries[canonical_path] = summary

    dangling = sorted(set(successor_sources) - set(seen_uids))
    if dangling:
        raise KnowledgeProjectionError(
            "projection-successor-absent",
            "concepts.lifecycle.successor_namespaced_uid",
            "is absent from the projected page set: " + ", ".join(dangling),
        )
    for canonical_path in sorted(expected_paths):
        lifecycle = _require_mapping(
            projection.concepts[canonical_path]["lifecycle"],
            f"concepts.{canonical_path}.lifecycle",
        )
        state = lifecycle["state"]
        successor_uid = lifecycle["successor_uid"]
        successor_namespaced = lifecycle["successor_namespaced_uid"]
        if successor_namespaced == UNKNOWN_VALUE:
            if (
                successor_uid != UNKNOWN_VALUE
                or state == Lifecycle.SUPERSEDED.value
            ):
                raise KnowledgeProjectionError(
                    "projection-successor-invalid",
                    (
                        f"concepts.{canonical_path}.lifecycle."
                        "successor_namespaced_uid"
                    ),
                    "must agree with lifecycle state and successor_uid",
                )
            continue
        expected_local_uid = successor_namespaced.removeprefix(
            f"{bundle_id}#"
        )
        if (
            state != Lifecycle.SUPERSEDED.value
            or successor_uid != expected_local_uid
        ):
            raise KnowledgeProjectionError(
                "projection-successor-invalid",
                f"concepts.{canonical_path}.lifecycle.successor_uid",
                "must agree with superseded lifecycle and namespaced successor",
            )
    return summaries


def _validate_projection_structure(projection: KnowledgeProjection) -> None:
    """Validate the complete safe projection wire shape without governance policy."""

    if not isinstance(projection, KnowledgeProjection):
        raise KnowledgeProjectionError(
            "projection-type-invalid",
            "projection",
            "must be a KnowledgeProjection",
        )
    if projection.schema_version != PROJECTION_SCHEMA_VERSION:
        raise KnowledgeProjectionError(
            "projection-schema-invalid",
            "schema_version",
            f"must be {PROJECTION_SCHEMA_VERSION!r}",
        )
    if not isinstance(projection.profile, KnowledgeProjectionProfile):
        raise KnowledgeProjectionError(
            "projection-profile-invalid",
            "profile",
            "must be 'internal' or 'public-portable'",
        )
    _require_sha256(
        projection.source_knowledge_hash,
        "source_knowledge_hash",
        code="projection-source-hash-invalid",
    )
    bundle = _require_mapping(projection.bundle, "bundle")
    concepts = _require_mapping(projection.concepts, "concepts")
    _validate_projection_diagnostics(projection)
    structural_bundle_id = _validate_projection_bundle(
        bundle,
        projection.profile,
    )

    concept_by_path: dict[str, Mapping[str, Any]] = {}
    for raw_path, raw_concept in concepts.items():
        if not isinstance(raw_path, str):
            _shape_error("concepts", "keys must be canonical path strings")
        _require_canonical_path(raw_path, f"concepts.{raw_path} key")
        concept = _require_mapping(raw_concept, f"concepts.{raw_path}")
        _validate_projection_concept(
            concept,
            path=raw_path,
            bundle_id=structural_bundle_id,
            profile=projection.profile,
        )
        concept_by_path[raw_path] = concept

    disclosure = projection.freshness
    if not isinstance(disclosure, str):
        _shape_error("freshness", "must be a freshness disclosure string")
    if disclosure != UNEVALUATED_FRESHNESS_DISCLOSURE:
        match = _EVALUATED_FRESHNESS_DISCLOSURE_RE.fullmatch(disclosure)
        if match is None:
            _shape_error(
                "freshness",
                "must be snapshot-only or use 'evaluated (N concepts)'",
            )
        assert match is not None
        if int(match.group(1)) != len(concept_by_path):
            _shape_error(
                "freshness",
                "evaluated concept count must match the projection",
            )

    aggregate_evaluated = disclosure != UNEVALUATED_FRESHNESS_DISCLOSURE
    for path, concept in concept_by_path.items():
        concept_freshness = _require_mapping(
            concept["freshness"],
            f"concepts.{path}.freshness",
        )
        concept_evaluated = _require_bool(
            concept_freshness["evaluated"],
            f"concepts.{path}.freshness.evaluated",
        )
        if concept_evaluated is not aggregate_evaluated:
            _shape_error(
                "freshness",
                "must agree with every concept freshness evaluated flag",
            )

    for path, concept in concept_by_path.items():
        _validate_projection_relationships(
            _require_mapping(
                concept["relationships"],
                f"concepts.{path}.relationships",
            ),
            path=f"concepts.{path}.relationships",
            profile=projection.profile,
            concepts=concept_by_path,
        )


def _validate_projection_diagnostics(projection: KnowledgeProjection) -> None:
    warnings = projection.warnings
    if (
        isinstance(warnings, (str, bytes))
        or not isinstance(warnings, Sequence)
        or any(not isinstance(value, str) for value in warnings)
    ):
        _shape_error("warnings", "must be a sequence of warning strings")
    warning_values = tuple(warnings)
    if warning_values != tuple(sorted(set(warning_values))):
        _shape_error("warnings", "must be unique and canonically sorted")

    omitted = _require_mapping(projection.omitted_fields, "omitted_fields")
    for name, count in omitted.items():
        if name not in _OMISSION_FIELDS:
            _shape_error(f"omitted_fields.{name}", "is not an allowed omission")
        _require_positive_int(count, f"omitted_fields.{name}")
    expected_omission_warnings = {
        f"omitted-{name.replace('_', '-')}" for name in omitted
    }
    for warning in warning_values:
        if (
            warning not in _BASE_WARNING_VALUES
            and warning not in expected_omission_warnings
        ):
            _shape_error(f"warnings.{warning}", "is not an allowed warning")
    actual_omission_warnings = {
        warning
        for warning in warning_values
        if warning.startswith("omitted-")
    }
    if actual_omission_warnings != expected_omission_warnings:
        _shape_error(
            "warnings",
            "must exactly account for every positive omitted-field count",
        )


def _validate_projection_bundle(
    bundle: Mapping[str, Any],
    profile: KnowledgeProjectionProfile,
) -> str:
    base = {
        "bundle_id",
        "repository_identity",
        "repository_identity_source",
        "evaluated_revision",
        "working_tree",
    }
    if profile is KnowledgeProjectionProfile.PUBLIC_PORTABLE:
        _require_exact_fields(bundle, "bundle", base)
    else:
        _require_exact_fields(
            bundle,
            "bundle",
            base | {"snapshot", "producer"},
            optional={"extensions"},
        )
    raw_bundle_id = bundle["bundle_id"]
    if raw_bundle_id == UNKNOWN_VALUE:
        bundle_id = UNKNOWN_VALUE
    else:
        try:
            bundle_id = validate_bundle_id(raw_bundle_id)
        except ConceptIdentityError as exc:
            raise KnowledgeProjectionError(
                "projection-bundle-invalid",
                "bundle.bundle_id",
                exc.message,
            ) from exc

    identity = bundle["repository_identity"]
    identity_source = bundle["repository_identity_source"]
    allowed_sources = {
        RepositoryIdentitySource.UNKNOWN.value,
        RepositoryIdentitySource.CONFIGURED_PUBLIC.value,
    }
    if profile is KnowledgeProjectionProfile.INTERNAL:
        allowed_sources.add(RepositoryIdentitySource.NORMALIZED_VCS.value)
    if (
        not isinstance(identity, str)
        or identity_source not in allowed_sources
        or (
            (identity == UNKNOWN_VALUE)
            != (identity_source == RepositoryIdentitySource.UNKNOWN.value)
        )
    ):
        raise KnowledgeProjectionError(
            "projection-repository-identity-invalid",
            "bundle.repository_identity",
            "must agree with an allowed repository identity source",
        )
    if identity != UNKNOWN_VALUE:
        try:
            validate_configured_public_identity(identity)
        except KnowledgeEnvelopeError as exc:
            raise KnowledgeProjectionError(
                "projection-repository-identity-invalid",
                "bundle.repository_identity",
                exc.message,
            ) from exc

    revision = bundle["evaluated_revision"]
    working_tree = bundle["working_tree"]
    if profile is KnowledgeProjectionProfile.PUBLIC_PORTABLE:
        if revision != UNKNOWN_VALUE or working_tree != UNKNOWN_VALUE:
            _shape_error(
                "bundle",
                "public-portable bundle state must remain unknown",
            )
        return bundle_id
    if (
        not isinstance(revision, str)
        or _EVALUATED_REVISION_RE.fullmatch(revision) is None
    ):
        _shape_error(
            "bundle.evaluated_revision",
            "must be an unknown or canonical git revision",
        )
    _require_enum(
        working_tree,
        {value.value for value in WorkingTreeState},
        "bundle.working_tree",
    )
    snapshot = _require_mapping(bundle["snapshot"], "bundle.snapshot")
    snapshot_fields = {
        "source_snapshot_hash",
        "markdown_snapshot_hash",
        "surface_index_hash",
        "generation_options_hash",
    }
    _require_exact_fields(snapshot, "bundle.snapshot", snapshot_fields)
    for name in snapshot_fields:
        _require_sha256(snapshot[name], f"bundle.snapshot.{name}")
    _validate_projection_producer(
        _require_mapping(bundle["producer"], "bundle.producer")
    )
    if "extensions" in bundle:
        _validate_safe_json_value(
            bundle["extensions"],
            "bundle.extensions",
        )
    return bundle_id


def _validate_projection_producer(producer: Mapping[str, Any]) -> None:
    _require_exact_fields(
        producer,
        "bundle.producer",
        {"tool", "extractors", "plugins"},
    )
    components: list[tuple[str, Mapping[str, Any]]] = [
        (
            "bundle.producer.tool",
            _require_mapping(producer["tool"], "bundle.producer.tool"),
        )
    ]
    for collection_name in ("extractors", "plugins"):
        values = _require_sequence(
            producer[collection_name],
            f"bundle.producer.{collection_name}",
        )
        components.extend(
            (
                f"bundle.producer.{collection_name}[{index}]",
                _require_mapping(
                    value,
                    f"bundle.producer.{collection_name}[{index}]",
                ),
            )
            for index, value in enumerate(values)
        )
    seen: set[str] = set()
    for path, component in components:
        _require_exact_fields(
            component,
            path,
            {"id", "version", "limitations"},
            optional={"configuration_hash"},
        )
        component_id = _require_safe_text(component["id"], f"{path}.id")
        _require_safe_text(component["version"], f"{path}.version")
        if component_id != UNKNOWN_VALUE:
            if component_id in seen:
                _shape_error(f"{path}.id", "duplicates a producer component id")
            seen.add(component_id)
        limitations = _require_sequence(
            component["limitations"],
            f"{path}.limitations",
        )
        limitation_values: list[str] = []
        for index, limitation in enumerate(limitations):
            value = _require_safe_text(
                limitation,
                f"{path}.limitations[{index}]",
            )
            if _LIMITATION_CODE_RE.fullmatch(value) is None:
                _shape_error(
                    f"{path}.limitations[{index}]",
                    "must be a stable limitation code",
                )
            limitation_values.append(value)
        if limitation_values != sorted(set(limitation_values)):
            _shape_error(path + ".limitations", "must be unique and sorted")
        if "configuration_hash" in component:
            _require_sha256(
                component["configuration_hash"],
                f"{path}.configuration_hash",
            )


def _validate_projection_concept(
    concept: Mapping[str, Any],
    *,
    path: str,
    bundle_id: str,
    profile: KnowledgeProjectionProfile,
) -> None:
    concept_path = f"concepts.{path}"
    base = {
        "canonical_path",
        "title",
        "concept_kind",
        "identity",
        "lifecycle",
        "evidence",
        "freshness",
        "review",
        "semantic_verification",
        "machine_check",
        "relationships",
    }
    if profile is KnowledgeProjectionProfile.PUBLIC_PORTABLE:
        _require_exact_fields(concept, concept_path, base)
    else:
        _require_exact_fields(
            concept,
            concept_path,
            base | {"locator", "document", "authorship"},
            optional={"extensions"},
        )
    if concept["canonical_path"] != path:
        raise KnowledgeProjectionError(
            "projection-coordinate-mismatch",
            f"{concept_path}.canonical_path",
            "must exactly match its projection map key",
        )
    _require_safe_text(concept["title"], f"{concept_path}.title")
    _validate_concept_kind(
        concept["concept_kind"],
        f"{concept_path}.concept_kind",
        profile,
    )
    _require_enum(
        concept["semantic_verification"],
        {value.value for value in Verification},
        f"{concept_path}.semantic_verification",
    )
    _validate_projection_identity(
        _require_mapping(concept["identity"], f"{concept_path}.identity"),
        path=f"{concept_path}.identity",
        bundle_id=bundle_id,
    )
    _validate_projection_lifecycle(
        _require_mapping(
            concept["lifecycle"],
            f"{concept_path}.lifecycle",
        ),
        path=f"{concept_path}.lifecycle",
        bundle_id=bundle_id,
        profile=profile,
    )
    _validate_projection_evidence(
        _require_mapping(concept["evidence"], f"{concept_path}.evidence"),
        path=f"{concept_path}.evidence",
        profile=profile,
    )
    _validate_projection_freshness(
        _require_mapping(
            concept["freshness"],
            f"{concept_path}.freshness",
        ),
        path=f"{concept_path}.freshness",
    )
    _validate_projection_review(
        _require_mapping(concept["review"], f"{concept_path}.review"),
        path=f"{concept_path}.review",
        profile=profile,
    )
    _validate_projection_machine_check(
        _require_mapping(
            concept["machine_check"],
            f"{concept_path}.machine_check",
        ),
        path=f"{concept_path}.machine_check",
    )
    if profile is KnowledgeProjectionProfile.INTERNAL:
        _require_safe_text(concept["locator"], f"{concept_path}.locator")
        document = _require_mapping(
            concept["document"],
            f"{concept_path}.document",
        )
        _require_exact_fields(
            document,
            f"{concept_path}.document",
            {"page_kind", "page_id", "role"},
        )
        _require_enum(
            document["page_kind"],
            {value.value for value in PageKind},
            f"{concept_path}.document.page_kind",
        )
        _require_safe_text(
            document["page_id"],
            f"{concept_path}.document.page_id",
        )
        _require_enum(
            document["role"],
            {value.value for value in SurfaceRole},
            f"{concept_path}.document.role",
        )
        _validate_actor(
            _require_mapping(
                concept["authorship"],
                f"{concept_path}.authorship",
            ),
            f"{concept_path}.authorship",
            allow_unknown=True,
        )
        if "extensions" in concept:
            _validate_safe_json_value(
                concept["extensions"],
                f"{concept_path}.extensions",
            )


def _validate_projection_identity(
    identity: Mapping[str, Any],
    *,
    path: str,
    bundle_id: str,
) -> None:
    _require_exact_fields(
        identity,
        path,
        {"state", "bundle_id", "uid", "namespaced_uid"},
    )
    _require_enum(identity["state"], {"tracked", "untracked"}, path + ".state")
    if identity["bundle_id"] != bundle_id:
        raise KnowledgeProjectionError(
            "projection-bundle-mismatch",
            path + ".bundle_id",
            f"must equal projected bundle {bundle_id!r}",
        )
    if bundle_id == UNKNOWN_VALUE:
        if (
            identity["state"] != "untracked"
            or identity["uid"] != UNKNOWN_VALUE
            or identity["namespaced_uid"] != UNKNOWN_VALUE
        ):
            _shape_error(path, "unknown bundles require untracked identity")
        return
    try:
        uid = validate_concept_uid(identity["uid"])
    except ConceptIdentityError as exc:
        raise KnowledgeProjectionError(
            "projection-uid-invalid",
            path + ".uid",
            exc.message,
        ) from exc
    expected = f"{bundle_id}#{uid}"
    if identity["state"] != "tracked" or identity["namespaced_uid"] != expected:
        raise KnowledgeProjectionError(
            "projection-namespaced-uid-invalid",
            path + ".namespaced_uid",
            f"must be exactly {expected!r}",
        )


def _validate_projection_lifecycle(
    lifecycle: Mapping[str, Any],
    *,
    path: str,
    bundle_id: str,
    profile: KnowledgeProjectionProfile,
) -> None:
    optional = {"events"} if profile is KnowledgeProjectionProfile.INTERNAL else set()
    _require_exact_fields(
        lifecycle,
        path,
        {"state", "successor_uid", "successor_namespaced_uid"},
        optional=optional,
    )
    _require_enum(
        lifecycle["state"],
        {value.value for value in Lifecycle},
        path + ".state",
    )
    successor_uid = lifecycle["successor_uid"]
    successor_namespaced = lifecycle["successor_namespaced_uid"]
    if successor_uid != UNKNOWN_VALUE:
        try:
            validate_concept_uid(successor_uid)
        except ConceptIdentityError as exc:
            raise KnowledgeProjectionError(
                "projection-successor-invalid",
                path + ".successor_uid",
                exc.message,
            ) from exc
    if successor_namespaced != UNKNOWN_VALUE:
        _require_safe_text(
            successor_namespaced,
            path + ".successor_namespaced_uid",
        )
    if "events" in lifecycle:
        for index, event in enumerate(
            _require_sequence(lifecycle["events"], path + ".events")
        ):
            event_path = f"{path}.events[{index}]"
            event_map = _require_mapping(event, event_path)
            _require_exact_fields(
                event_map,
                event_path,
                {"event_id", "from", "to", "actor", "authored_at"},
                optional={"reason", "successor_uid"},
            )
            if (
                not isinstance(event_map["event_id"], str)
                or re.fullmatch(r"le_[0-9a-f]{64}", event_map["event_id"])
                is None
            ):
                _shape_error(event_path + ".event_id", "must be a lifecycle event id")
            for name in ("from", "to"):
                _require_enum(
                    event_map[name],
                    {value.value for value in Lifecycle},
                    f"{event_path}.{name}",
                )
            _validate_actor(
                _require_mapping(event_map["actor"], event_path + ".actor"),
                event_path + ".actor",
                allow_unknown=False,
            )
            _require_safe_text(
                event_map["authored_at"],
                event_path + ".authored_at",
            )
            if "reason" in event_map:
                _require_machine_code(
                    event_map["reason"],
                    event_path + ".reason",
                )
            if "successor_uid" in event_map:
                try:
                    validate_concept_uid(event_map["successor_uid"])
                except ConceptIdentityError as exc:
                    raise KnowledgeProjectionError(
                        "projection-shape-invalid",
                        event_path + ".successor_uid",
                        exc.message,
                    ) from exc


def _validate_projection_evidence(
    evidence: Mapping[str, Any],
    *,
    path: str,
    profile: KnowledgeProjectionProfile,
) -> None:
    optional = {"basis"} if profile is KnowledgeProjectionProfile.INTERNAL else set()
    _require_exact_fields(
        evidence,
        path,
        {"state", "reason", "origin"},
        optional=optional,
    )
    state = _require_enum(
        evidence["state"],
        {value.value for value in EvidenceState},
        path + ".state",
    )
    if evidence["reason"] != f"structural-evidence-{state}":
        _shape_error(path + ".reason", "does not match structural evidence state")
    _require_enum(
        evidence["origin"],
        {value.value for value in Origin},
        path + ".origin",
    )
    if "basis" not in evidence:
        return
    basis = _require_mapping(evidence["basis"], path + ".basis")
    fields = {
        "scope",
        "source_path",
        "extractor_ref",
        "source_content_hash",
        "concept_observation_hash",
        "aggregate_input_hash",
    }
    _require_exact_fields(basis, path + ".basis", set(), optional=fields)
    if "scope" in basis:
        _require_enum(
            basis["scope"],
            {value.value for value in ObservationScope},
            path + ".basis.scope",
        )
    if "source_path" in basis:
        _require_relative_path(
            basis["source_path"],
            path + ".basis.source_path",
        )
    if "extractor_ref" in basis:
        _require_safe_text(
            basis["extractor_ref"],
            path + ".basis.extractor_ref",
        )
    for name in (
        "source_content_hash",
        "concept_observation_hash",
        "aggregate_input_hash",
    ):
        if name in basis:
            _require_sha256(basis[name], f"{path}.basis.{name}")


def _validate_projection_freshness(
    freshness: Mapping[str, Any],
    *,
    path: str,
) -> None:
    _require_exact_fields(
        freshness,
        path,
        {"state", "reason", "evaluated", "live_comparison_performed"},
        optional={"hint"},
    )
    evaluated = _require_bool(freshness["evaluated"], path + ".evaluated")
    live = _require_bool(
        freshness["live_comparison_performed"],
        path + ".live_comparison_performed",
    )
    state = freshness["state"]
    reason = freshness["reason"]
    if state == NOT_EVALUATED:
        if "hint" in freshness:
            _shape_error(
                path + ".hint",
                "is valid only for basis-incompatible freshness",
            )
        if reason != NOT_EVALUATED or evaluated or live:
            _shape_error(path, "not-evaluated freshness carries live claims")
        return
    _require_enum(
        state,
        {value.value for value in ComputedFreshness},
        path + ".state",
    )
    _require_enum(reason, KNOWN_FRESHNESS_REASON_CODES, path + ".reason")
    if not evaluated:
        _shape_error(path + ".evaluated", "must be true for evaluated freshness")
    if state == ComputedFreshness.CURRENT.value:
        if (
            not live
            or reason != REASON_RECORDED_BASIS_MATCHES_LIVE_EVALUATION
        ):
            _shape_error(path, "current freshness requires a positive live match")
    elif reason == REASON_RECORDED_BASIS_MATCHES_LIVE_EVALUATION:
        _shape_error(path + ".reason", "is valid only for current freshness")
    try:
        expected_hint = knowledge_freshness_hint(state, reason)
    except ValueError:
        _shape_error(
            path + ".reason",
            "has no registered actionable freshness guidance",
        )
    if expected_hint is None:
        if "hint" in freshness:
            _shape_error(
                path + ".hint",
                "is valid only for basis-incompatible freshness",
            )
    elif freshness.get("hint") != expected_hint:
        _shape_error(
            path + ".hint",
            "must match the registered actionable freshness guidance",
        )


def _validate_projection_review(
    review: Mapping[str, Any],
    *,
    path: str,
    profile: KnowledgeProjectionProfile,
) -> None:
    _require_exact_fields(
        review,
        path,
        {
            "scope",
            "state",
            "total",
            "returned",
            "valid_returned",
            "expired_returned",
            "truncated",
            "reasons",
            "items",
        },
    )
    if review["scope"] != "section":
        _shape_error(path + ".scope", "must be 'section'")
    total = _require_nonnegative_int(review["total"], path + ".total")
    returned = _require_nonnegative_int(review["returned"], path + ".returned")
    valid = _require_nonnegative_int(
        review["valid_returned"],
        path + ".valid_returned",
    )
    expired = _require_nonnegative_int(
        review["expired_returned"],
        path + ".expired_returned",
    )
    truncated = _require_bool(review["truncated"], path + ".truncated")
    items = _require_sequence(review["items"], path + ".items")
    if (
        returned != len(items)
        or returned > total
        or valid + expired != returned
        or truncated != (total > returned)
    ):
        _shape_error(path, "contains inconsistent review bounds")
    reasons = _validate_review_reasons(review["reasons"], path + ".reasons")
    item_reasons: set[str] = set()
    item_states: list[str] = []
    for index, item in enumerate(items):
        item_path = f"{path}.items[{index}]"
        item_map = _require_mapping(item, item_path)
        required = {"section_locator", "state", "reasons"}
        if profile is KnowledgeProjectionProfile.PUBLIC_PORTABLE:
            _require_exact_fields(item_map, item_path, required)
        else:
            _require_exact_fields(
                item_map,
                item_path,
                required,
                optional={
                    "event_id",
                    "reviewer",
                    "method",
                    "authored_at",
                },
            )
        _require_safe_text(
            item_map["section_locator"],
            item_path + ".section_locator",
        )
        state = _require_enum(
            item_map["state"],
            {"valid", "expired"},
            item_path + ".state",
        )
        selected_reasons = _validate_review_reasons(
            item_map["reasons"],
            item_path + ".reasons",
        )
        if (state == "valid") != (not selected_reasons):
            _shape_error(item_path, "review state does not match reasons")
        item_states.append(state)
        item_reasons.update(selected_reasons)
        if "event_id" in item_map:
            if (
                not isinstance(item_map["event_id"], str)
                or re.fullmatch(r"rv_[0-9a-f]{64}", item_map["event_id"])
                is None
            ):
                _shape_error(item_path + ".event_id", "must be a review event id")
        if "reviewer" in item_map:
            _validate_actor(
                _require_mapping(
                    item_map["reviewer"],
                    item_path + ".reviewer",
                ),
                item_path + ".reviewer",
                allow_unknown=False,
            )
        if "method" in item_map:
            method = _require_mapping(item_map["method"], item_path + ".method")
            _require_exact_fields(
                method,
                item_path + ".method",
                set(),
                optional={"id", "version"},
            )
            for name, value in method.items():
                _require_safe_text(value, f"{item_path}.method.{name}")
        if "authored_at" in item_map:
            _require_safe_text(
                item_map["authored_at"],
                item_path + ".authored_at",
            )
    if valid != item_states.count("valid") or expired != item_states.count("expired"):
        _shape_error(path, "review state counts do not match returned items")
    if tuple(reasons) != tuple(sorted(item_reasons)):
        _shape_error(path + ".reasons", "must equal returned item reasons")
    expected_state = (
        "untracked"
        if total == 0
        else "partial"
        if truncated
        else "mixed"
        if valid and expired
        else "has-valid-sections"
        if valid
        else "has-expired-sections"
        if expired
        else UNKNOWN_VALUE
    )
    _require_enum(review["state"], _REVIEW_STATES, path + ".state")
    if review["state"] != expected_state:
        _shape_error(path + ".state", f"must be {expected_state!r}")


def _validate_review_reasons(value: object, path: str) -> tuple[str, ...]:
    reasons = _require_sequence(value, path)
    selected: list[str] = []
    for index, reason in enumerate(reasons):
        selected.append(
            _require_enum(
                reason,
                _REVIEW_EXPIRY_REASONS,
                f"{path}[{index}]",
            )
        )
    if selected != sorted(set(selected)):
        _shape_error(path, "must be unique and sorted")
    return tuple(selected)


def _validate_projection_machine_check(
    machine: Mapping[str, Any],
    *,
    path: str,
) -> None:
    base = {"state", "reason", "availability"}
    availability = machine.get("availability")
    state = machine.get("state")
    reason = machine.get("reason")
    if availability == MachineVerificationAvailability.NOT_EVALUATED.value:
        _require_exact_fields(machine, path, base)
        if state != NOT_EVALUATED or reason != "verification-receipt-not-evaluated":
            _shape_error(path, "does not match not-evaluated receipt state")
        return
    if availability == MachineVerificationAvailability.ABSENT.value:
        _require_exact_fields(machine, path, base)
        if state != "not-run" or reason not in {
            "verification-receipt-not-present",
            "verification-receipt-scope-unknown",
            "verification-receipt-not-present-for-concept",
        }:
            _shape_error(path, "does not match absent receipt state")
        return
    if availability == MachineVerificationAvailability.INVALID.value:
        _require_exact_fields(machine, path, base)
        if state != "invalid" or reason != "verification-receipt-invalid":
            _shape_error(path, "does not match invalid receipt state")
        return
    if availability != MachineVerificationAvailability.RECORDED.value:
        _shape_error(path + ".availability", "is not a closed receipt availability")
    _require_exact_fields(
        machine,
        path,
        base | {"valid", "recorded_result", "checks"},
    )
    valid = _require_bool(machine["valid"], path + ".valid")
    result = _require_enum(
        machine["recorded_result"],
        {"passed", "failed"},
        path + ".recorded_result",
    )
    checks = _require_mapping(machine["checks"], path + ".checks")
    _require_exact_fields(checks, path + ".checks", {"total", "passed", "failed"})
    total = _require_nonnegative_int(checks["total"], path + ".checks.total")
    passed = _require_nonnegative_int(checks["passed"], path + ".checks.passed")
    failed = _require_nonnegative_int(checks["failed"], path + ".checks.failed")
    if total == 0 or passed + failed != total:
        _shape_error(path + ".checks", "contains inconsistent aggregate counts")
    if valid:
        expected_state = "verified" if result == "passed" else "failed"
        expected_reason = f"verification-receipt-{result}"
        if state != expected_state or reason != expected_reason:
            _shape_error(path, "does not match valid recorded receipt result")
    elif state != "invalid" or reason not in _MACHINE_INVALIDATION_REASONS:
        _shape_error(path, "does not match invalidated receipt result")


def _validate_projection_relationships(
    relationships: Mapping[str, Any],
    *,
    path: str,
    profile: KnowledgeProjectionProfile,
    concepts: Mapping[str, Mapping[str, Any]],
) -> None:
    _require_exact_fields(
        relationships,
        path,
        {"availability", "total", "returned", "limit", "truncated", "items"},
    )
    availability = _require_enum(
        relationships["availability"],
        {"ready", "absent"},
        path + ".availability",
    )
    total = _require_nonnegative_int(relationships["total"], path + ".total")
    returned = _require_nonnegative_int(
        relationships["returned"],
        path + ".returned",
    )
    limit = _require_positive_int(relationships["limit"], path + ".limit")
    if limit > MAX_RELATIONSHIP_LIMIT:
        _shape_error(path + ".limit", "exceeds the relationship limit")
    truncated = _require_bool(relationships["truncated"], path + ".truncated")
    items = _require_sequence(relationships["items"], path + ".items")
    if (
        returned != len(items)
        or returned > total
        or returned > limit
        or truncated != (total > returned)
    ):
        _shape_error(path, "contains inconsistent relationship bounds")
    if availability == "absent" and (total or returned or truncated or items):
        _shape_error(path, "absent relationship state must be empty")
    for index, item in enumerate(items):
        _validate_projection_relationship(
            _require_mapping(item, f"{path}.items[{index}]"),
            path=f"{path}.items[{index}]",
            profile=profile,
            concepts=concepts,
        )


def _validate_projection_relationship(
    relation: Mapping[str, Any],
    *,
    path: str,
    profile: KnowledgeProjectionProfile,
    concepts: Mapping[str, Mapping[str, Any]],
) -> None:
    optional = {"key"} if profile is KnowledgeProjectionProfile.INTERNAL else set()
    _require_exact_fields(
        relation,
        path,
        {"kind", "direction", "origin", "resolution", "target", "evidence", "coverage"},
        optional=optional,
    )
    kind = relation["kind"]
    if profile is KnowledgeProjectionProfile.PUBLIC_PORTABLE:
        _require_enum(kind, set(CORE_RELATIONSHIP_KINDS) | {UNKNOWN_VALUE}, path + ".kind")
    elif (
        kind not in CORE_RELATIONSHIP_KINDS
        and kind != UNKNOWN_VALUE
        and (
            not isinstance(kind, str)
            or _QUALIFIED_RELATIONSHIP_KIND_RE.fullmatch(kind) is None
        )
    ):
        _shape_error(path + ".kind", "is not a closed or qualified relationship kind")
    _require_enum(
        relation["direction"],
        {"incoming", "outgoing", "both"},
        path + ".direction",
    )
    _require_enum(relation["origin"], set(GRAPH_ORIGINS), path + ".origin")
    resolution = _require_enum(
        relation["resolution"],
        set(GRAPH_RESOLUTIONS),
        path + ".resolution",
    )
    if "key" in relation:
        _require_sha256(relation["key"], path + ".key")
    _validate_projection_target(
        _require_mapping(relation["target"], path + ".target"),
        path=path + ".target",
        profile=profile,
        resolution=resolution,
        concepts=concepts,
    )
    evidence = _require_mapping(relation["evidence"], path + ".evidence")
    evidence_optional = (
        {"aggregate_input_hash", "samples"}
        if profile is KnowledgeProjectionProfile.INTERNAL
        else set()
    )
    _require_exact_fields(
        evidence,
        path + ".evidence",
        {"state", "observed", "unique", "emitted", "omitted"},
        optional=evidence_optional,
    )
    state = _require_enum(
        evidence["state"],
        set(GRAPH_EVIDENCE_STATES),
        path + ".evidence.state",
    )
    observed = _require_nonnegative_int(
        evidence["observed"],
        path + ".evidence.observed",
    )
    unique = _require_nonnegative_int(
        evidence["unique"],
        path + ".evidence.unique",
    )
    emitted = _require_nonnegative_int(
        evidence["emitted"],
        path + ".evidence.emitted",
    )
    omitted = _require_nonnegative_int(
        evidence["omitted"],
        path + ".evidence.omitted",
    )
    if (
        not emitted <= unique <= observed
        or omitted != observed - emitted
        or (observed > 0) != (state == "present")
    ):
        _shape_error(path + ".evidence", "contains inconsistent evidence bounds")
    if "aggregate_input_hash" in evidence:
        _require_sha256(
            evidence["aggregate_input_hash"],
            path + ".evidence.aggregate_input_hash",
        )
    if "samples" in evidence:
        samples = _require_sequence(
            evidence["samples"],
            path + ".evidence.samples",
        )
        if len(samples) != emitted:
            _shape_error(
                path + ".evidence.samples",
                "must match the emitted evidence count",
            )
        for index, sample in enumerate(samples):
            _validate_safe_json_value(
                sample,
                f"{path}.evidence.samples[{index}]",
            )

    coverage = _require_mapping(relation["coverage"], path + ".coverage")
    coverage_optional = (
        {"limitations"}
        if profile is KnowledgeProjectionProfile.INTERNAL
        else set()
    )
    _require_exact_fields(
        coverage,
        path + ".coverage",
        {"observed", "emitted", "omitted", "limit", "truncated"},
        optional=coverage_optional,
    )
    coverage_observed = _require_nonnegative_int(
        coverage["observed"],
        path + ".coverage.observed",
    )
    coverage_emitted = _require_nonnegative_int(
        coverage["emitted"],
        path + ".coverage.emitted",
    )
    coverage_omitted = _require_nonnegative_int(
        coverage["omitted"],
        path + ".coverage.omitted",
    )
    coverage_limit = _require_nonnegative_int(
        coverage["limit"],
        path + ".coverage.limit",
    )
    coverage_truncated = _require_bool(
        coverage["truncated"],
        path + ".coverage.truncated",
    )
    if (
        coverage_emitted > coverage_limit
        or coverage_omitted != coverage_observed - coverage_emitted
        or coverage_truncated != (coverage_omitted > 0)
        or (
            (coverage_observed, coverage_emitted, coverage_omitted)
            != (observed, emitted, omitted)
        )
    ):
        _shape_error(path + ".coverage", "does not match relationship evidence")
    if "limitations" in coverage:
        limitations = _require_sequence(
            coverage["limitations"],
            path + ".coverage.limitations",
        )
        selected: list[str] = []
        for index, limitation in enumerate(limitations):
            value = _require_safe_text(
                limitation,
                f"{path}.coverage.limitations[{index}]",
            )
            if _LIMITATION_CODE_RE.fullmatch(value) is None:
                _shape_error(
                    f"{path}.coverage.limitations[{index}]",
                    "must be a stable limitation code",
                )
            selected.append(value)
        if selected != sorted(set(selected)):
            _shape_error(path + ".coverage.limitations", "must be unique and sorted")


def _validate_projection_target(
    target: Mapping[str, Any],
    *,
    path: str,
    profile: KnowledgeProjectionProfile,
    resolution: str,
    concepts: Mapping[str, Mapping[str, Any]],
) -> None:
    kind = _require_enum(target.get("kind"), set(ENDPOINT_KINDS), path + ".kind")
    if kind == "concept":
        _require_exact_fields(
            target,
            path,
            {
                "kind",
                "present",
                "canonical_path",
                "title",
                "concept_kind",
                "namespaced_uid",
            },
        )
        if resolution != "resolved" or target["present"] is not True:
            _shape_error(path, "concept targets must be present and resolved")
        canonical_path = target["canonical_path"]
        if not isinstance(canonical_path, str) or canonical_path not in concepts:
            _shape_error(path + ".canonical_path", "is absent from the projection")
        _require_safe_text(target["title"], path + ".title")
        _validate_concept_kind(
            target["concept_kind"],
            path + ".concept_kind",
            profile,
        )
        target_identity = _require_mapping(
            concepts[canonical_path]["identity"],
            f"concepts.{canonical_path}.identity",
        )
        if target["namespaced_uid"] != target_identity["namespaced_uid"]:
            _shape_error(
                path + ".namespaced_uid",
                "does not match the projected target concept",
            )
        return
    if kind == "external-resource":
        optional = {"resource", "uri"} if profile is KnowledgeProjectionProfile.INTERNAL else set()
        _require_exact_fields(
            target,
            path,
            {"kind", "present", "label"},
            optional=optional,
        )
        if (
            resolution != "external"
            or target["present"] is not False
            or target["label"] != "External resource"
        ):
            _shape_error(path, "does not match an external target")
        for name in optional & set(target):
            _require_safe_text(target[name], f"{path}.{name}")
        return
    if kind == "unresolved":
        optional = (
            {"candidate_count", "raw_target", "candidates"}
            if profile is KnowledgeProjectionProfile.INTERNAL
            else set()
        )
        _require_exact_fields(
            target,
            path,
            {"kind", "present", "label"},
            optional=optional,
        )
        expected_label = (
            "Ambiguous target"
            if resolution == "ambiguous"
            else "Unresolved target"
        )
        if (
            resolution not in {"ambiguous", "unresolved"}
            or target["present"] is not False
            or target["label"] != expected_label
        ):
            _shape_error(path, "does not match an unresolved target")
        if "candidate_count" in target:
            _require_nonnegative_int(
                target["candidate_count"],
                path + ".candidate_count",
            )
        if "raw_target" in target:
            _require_safe_text(target["raw_target"], path + ".raw_target")
        if "candidates" in target:
            candidates = _require_sequence(target["candidates"], path + ".candidates")
            if "candidate_count" in target and len(candidates) != target["candidate_count"]:
                _shape_error(path + ".candidates", "does not match candidate_count")
            for index, candidate in enumerate(candidates):
                _validate_safe_json_value(candidate, f"{path}.candidates[{index}]")
        return
    optional = (
        {"source_path", "symbol", "locator", "uid"}
        if profile is KnowledgeProjectionProfile.INTERNAL
        else set()
    )
    _require_exact_fields(
        target,
        path,
        {"kind", "present", "label"},
        optional=optional,
    )
    if (
        kind != "source-symbol"
        or target["present"] is not False
        or target["label"] != "Source symbol"
        or resolution == "external"
    ):
        _shape_error(path, "does not match a source-symbol target")
    for name in optional & set(target):
        if name == "source_path":
            _require_relative_path(target[name], f"{path}.{name}")
        else:
            _require_safe_text(target[name], f"{path}.{name}")


def _validate_actor(
    actor: Mapping[str, Any],
    path: str,
    *,
    allow_unknown: bool,
) -> None:
    _require_exact_fields(
        actor,
        path,
        {"kind"},
        optional={"id", "version", "model", "organization", "extensions"},
    )
    kinds = {value.value for value in ActorKind}
    if not allow_unknown:
        kinds.discard(ActorKind.UNKNOWN.value)
    _require_enum(actor["kind"], kinds, path + ".kind")
    for name in ("id", "version", "model", "organization"):
        if name in actor:
            _require_safe_text(actor[name], f"{path}.{name}")
    if "extensions" in actor:
        _validate_safe_json_value(actor["extensions"], path + ".extensions")


def _validate_concept_kind(
    value: object,
    path: str,
    profile: KnowledgeProjectionProfile,
) -> None:
    allowed = {item.value for item in ConceptKind} | {UNKNOWN_VALUE}
    if value in allowed:
        return
    if (
        profile is KnowledgeProjectionProfile.INTERNAL
        and isinstance(value, str)
        and _QUALIFIED_RELATIONSHIP_KIND_RE.fullmatch(value) is not None
    ):
        _require_safe_text(value, path)
        return
    _shape_error(path, "is not an allowed concept kind")


def _validate_safe_json_value(
    value: object,
    path: str,
    *,
    depth: int = 0,
) -> None:
    if depth > 64:
        _shape_error(path, "exceeds the safe projection nesting limit")
    if isinstance(value, Mapping):
        for key, item in value.items():
            if not isinstance(key, str):
                _shape_error(path, "mapping keys must be strings")
            _require_safe_text(key, path + " key")
            if _SENSITIVE_KEY_RE.search(key):
                _shape_error(path + "." + key, "uses a sensitive metadata key")
            _validate_safe_json_value(item, path + "." + key, depth=depth + 1)
        return
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        for index, item in enumerate(value):
            _validate_safe_json_value(item, f"{path}[{index}]", depth=depth + 1)
        return
    if isinstance(value, str):
        _require_safe_text(value, path)
        return
    if value is None or isinstance(value, (bool, int)):
        return
    if isinstance(value, float) and math.isfinite(value):
        return
    _shape_error(path, "contains a non-JSON or non-finite value")


def _require_mapping(value: object, path: str) -> Mapping[str, Any]:
    return require_shared_mapping(
        value,
        error=KnowledgeProjectionError(
            "projection-shape-invalid", path, "must be a mapping"
        ),
    )


def _require_sequence(value: object, path: str) -> Sequence[Any]:
    return require_shared_sequence(
        value,
        error=KnowledgeProjectionError(
            "projection-shape-invalid", path, "must be a sequence"
        ),
    )


def _require_exact_fields(
    value: Mapping[str, Any],
    path: str,
    required: set[str],
    *,
    optional: set[str] | frozenset[str] = frozenset(),
) -> None:
    return require_shared_exact_fields(
        value,
        allowed=required | set(optional),
        required=required,
        mapping_error=KnowledgeProjectionError(
            "projection-shape-invalid", path, "must be a mapping"
        ),
        missing_error=lambda fields: KnowledgeProjectionError(
            "projection-shape-invalid", f"{path}.{fields[0]}", "is required"
        ),
        unknown_error=lambda fields: KnowledgeProjectionError(
            "projection-shape-invalid",
            f"{path}.{fields[0]}",
            "is not an allowed field",
        ),
        unknown_first=True,
    )


def _require_safe_text(value: object, path: str) -> str:
    if not isinstance(value, str) or not value:
        _shape_error(path, "must be a non-empty string")
    if len(value) > 8192:
        _shape_error(path, "exceeds the safe projection string limit")
    if (
        _CONTROL_RE.search(value)
        or _CREDENTIAL_VALUE_RE.search(value)
        or _URI_USERINFO_RE.search(value)
        or _RAW_VCS_REMOTE_RE.search(value)
    ):
        _shape_error(path, "contains credential-like or unsafe remote data")
    if (
        value.startswith("/")
        or value.startswith("\\\\")
        or _WINDOWS_ABSOLUTE_RE.match(value)
        or _EMBEDDED_ABSOLUTE_RE.search(value)
        or _TRAVERSAL_RE.search(value)
        or value.casefold().startswith("file:")
    ):
        _shape_error(path, "contains an unsafe path")
    return value


def _require_canonical_path(value: object, path: str) -> str:
    selected = _require_relative_path(value, path)
    if not selected.endswith(".md"):
        _shape_error(path, "must identify a Markdown page")
    return selected


def _require_relative_path(value: object, path: str) -> str:
    selected = _require_safe_text(value, path)
    error = KnowledgeProjectionError(
        "projection-shape-invalid",
        path,
        "must be a normalized repository-relative path",
    )
    return require_portable_relative_path(
        selected,
        relative_error=error,
        separator_error=error,
        non_nfc_error=error,
        nonportable_error=error,
        reserved_error=error,
    )


def _require_enum(value: object, values: set[str] | frozenset[str], path: str) -> str:
    error = KnowledgeProjectionError(
        "projection-shape-invalid", path, "contains an unsupported closed value"
    )
    return require_shared_choice(
        value,
        values,
        text_error=error,
        choice_error=lambda _allowed: error,
    )


def _require_bool(value: object, path: str) -> bool:
    return require_shared_bool(
        value,
        error=KnowledgeProjectionError(
            "projection-shape-invalid", path, "must be a boolean"
        ),
    )


def _require_nonnegative_int(value: object, path: str) -> int:
    return require_shared_nonnegative_int(
        value,
        error=KnowledgeProjectionError(
            "projection-shape-invalid", path, "must be a non-negative integer"
        ),
    )


def _require_positive_int(value: object, path: str) -> int:
    return require_shared_positive_int(
        value,
        invalid_error=KnowledgeProjectionError(
            "projection-shape-invalid", path, "must be a non-negative integer"
        ),
        zero_error=KnowledgeProjectionError(
            "projection-shape-invalid", path, "must be a positive integer"
        ),
    )


def _require_sha256(
    value: object,
    path: str,
    *,
    code: str = "projection-shape-invalid",
) -> str:
    return require_shared_sha256(
        value,
        digest_error=KnowledgeProjectionError(
            code,
            path,
            "must be a canonical sha256:<64 lowercase hexadecimal> value",
        ),
    )


def _require_machine_code(value: object, path: str) -> str:
    selected = _require_safe_text(value, path)
    if re.fullmatch(r"[a-z][a-z0-9]*(?:-[a-z0-9]+)*", selected) is None:
        _shape_error(path, "must be a stable machine code")
    return selected


def _shape_error(path: str, message: str) -> NoReturn:
    raise KnowledgeProjectionError(
        "projection-shape-invalid",
        path,
        message,
    )


def _validated_source(
    view: KnowledgeReadView,
) -> tuple[KnowledgeIndex, str]:
    if not isinstance(view, KnowledgeReadView):
        raise TypeError("view must be a KnowledgeReadView")
    if (
        view.availability is not KnowledgeAvailability.READY
        or not view.ready
        or view.knowledge is None
        or view.surface is None
        or view.manifest_basis is None
    ):
        raise KnowledgeProjectionError(
            "projection-source-unavailable",
            "view.availability",
            (
                "requires a ready validated knowledge read view; "
                f"received {view.availability.value!r} ({view.reason_code})"
            ),
        )
    marker = view.manifest_basis.artifact_hashes
    if marker is None:
        raise KnowledgeProjectionError(
            "projection-source-uncommitted",
            "view.manifest_basis.artifact_hashes",
            "requires exact committed artifact hashes",
        )
    try:
        surface_bytes = (
            json.dumps(
                dict(view.surface),
                indent=2,
                sort_keys=True,
                allow_nan=False,
            )
            + "\n"
        ).encode("utf-8")
        knowledge_bytes = serialize_knowledge_index(view.knowledge).encode("utf-8")
        validated = validate_knowledge_artifacts(
            surface_index_bytes=surface_bytes,
            knowledge_index_bytes=knowledge_bytes,
            manifest=view.manifest_basis,
        )
    except (TypeError, ValueError) as exc:
        raise KnowledgeProjectionError(
            "projection-source-invalid",
            "view",
            f"does not contain one intact committed artifact set: {exc}",
        ) from exc
    if (
        validated.knowledge_index_hash != marker.knowledge_index_hash
        or sha256_bytes(knowledge_bytes) != marker.knowledge_index_hash
    ):
        raise KnowledgeProjectionError(
            "projection-source-mixed",
            "view.knowledge",
            "does not match the committed source knowledge hash",
        )
    return validated.knowledge, marker.knowledge_index_hash


def _project_bundle(
    knowledge: KnowledgeIndex,
    *,
    bundle_id: str,
    profile: KnowledgeProjectionProfile,
    approved_public_identity: str | None,
    omitted: dict[str, int],
) -> dict[str, Any]:
    repository = knowledge.bundle.repository
    identity = UNKNOWN_VALUE
    identity_source = RepositoryIdentitySource.UNKNOWN.value
    if profile is KnowledgeProjectionProfile.INTERNAL:
        identity = repository.identity
        identity_source = repository.identity_source.value
    elif approved_public_identity is not None:
        identity = approved_public_identity
        identity_source = RepositoryIdentitySource.CONFIGURED_PUBLIC.value
    elif repository.identity != UNKNOWN_VALUE:
        omitted["private_repository_identity"] += 1

    payload: dict[str, Any] = {
        "bundle_id": bundle_id,
        "repository_identity": identity,
        "repository_identity_source": identity_source,
        "evaluated_revision": UNKNOWN_VALUE,
        "working_tree": UNKNOWN_VALUE,
    }
    if profile is KnowledgeProjectionProfile.INTERNAL:
        payload.update(
            {
                "evaluated_revision": repository.evaluated_revision,
                "working_tree": repository.working_tree.value,
                "snapshot": {
                    "source_snapshot_hash": (
                        knowledge.bundle.snapshot.source_snapshot_hash
                    ),
                    "markdown_snapshot_hash": (
                        knowledge.bundle.snapshot.markdown_snapshot_hash
                    ),
                    "surface_index_hash": (
                        knowledge.bundle.snapshot.surface_index_hash
                    ),
                    "generation_options_hash": (
                        knowledge.bundle.snapshot.generation_options_hash
                    ),
                },
                "producer": _project_producer(knowledge, omitted=omitted),
            }
        )
        extensions = _project_unknown_extensions(
            knowledge.extensions,
            omitted=omitted,
        )
        if extensions:
            payload["extensions"] = extensions
    return payload


def _project_producer(
    knowledge: KnowledgeIndex,
    *,
    omitted: dict[str, int],
) -> dict[str, Any]:
    producer = knowledge.bundle.producer

    def component(value: Any) -> dict[str, Any]:
        component_id = _safe_internal_scalar(
            "component_id",
            value.component_id,
            omitted,
        )
        version = _safe_internal_scalar(
            "component_version",
            value.version,
            omitted,
        )
        projected: dict[str, Any] = {
            "id": component_id or UNKNOWN_VALUE,
            "version": version or UNKNOWN_VALUE,
            "limitations": [
                safe
                for limitation in value.limitations
                if (
                    safe := _safe_internal_scalar(
                        "component_limitation",
                        limitation,
                        omitted,
                    )
                )
                is not None
            ],
        }
        if value.configuration_hash is not None:
            projected["configuration_hash"] = value.configuration_hash
        return projected

    return {
        "tool": component(producer.tool),
        "extractors": [component(value) for value in producer.extractors],
        "plugins": [component(value) for value in producer.plugins],
    }


def _project_concept(
    concept: ConceptRecord,
    *,
    view: KnowledgeReadView,
    bundle_id: str,
    governance: Mapping[str, Any] | None,
    relationships: Mapping[str, Any],
    profile: KnowledgeProjectionProfile,
    omitted: dict[str, int],
) -> dict[str, Any]:
    uid = (
        str(governance["uid"])
        if governance is not None and isinstance(governance.get("uid"), str)
        else UNKNOWN_VALUE
    )
    successor_uid = (
        str(governance["successor_uid"])
        if governance is not None
        and isinstance(governance.get("successor_uid"), str)
        else UNKNOWN_VALUE
    )
    identity = {
        "state": "tracked" if uid != UNKNOWN_VALUE else "untracked",
        "bundle_id": bundle_id,
        "uid": uid,
        "namespaced_uid": _namespaced_uid(bundle_id, uid),
    }
    payload: dict[str, Any] = {
        "canonical_path": concept.document.canonical_path,
        "title": (
            _safe_internal_scalar("title", concept.title, omitted)
            or "Untitled concept"
        ),
        "concept_kind": _project_concept_kind(
            concept.concept_kind,
            profile=profile,
            omitted=omitted,
        ),
        "identity": identity,
        "lifecycle": {
            "state": concept.lifecycle.value,
            "successor_uid": successor_uid,
            "successor_namespaced_uid": _namespaced_uid(
                bundle_id,
                successor_uid,
            ),
        },
        "evidence": {
            "state": concept.facets.structure.evidence.value,
            "reason": (
                "structural-evidence-"
                + concept.facets.structure.evidence.value
            ),
            "origin": concept.facets.structure.origin.value,
        },
        "freshness": _project_freshness(concept, view),
        "review": _project_review(
            governance,
            profile=profile,
            omitted=omitted,
        ),
        "semantic_verification": (
            concept.facets.semantics.verification.value
        ),
        "machine_check": _project_machine_check(concept, view),
        "relationships": _json_copy(relationships),
    }
    if profile is KnowledgeProjectionProfile.INTERNAL:
        payload["locator"] = (
            _safe_internal_scalar("locator", concept.locator, omitted)
            or UNKNOWN_VALUE
        )
        payload["document"] = {
            "page_kind": concept.document.page_kind.value,
            "page_id": (
                _safe_internal_scalar(
                    "page_id",
                    concept.document.page_id,
                    omitted,
                )
                or UNKNOWN_VALUE
            ),
            "role": concept.document.role.value,
        }
        payload["authorship"] = _project_actor(
            concept.facets.semantics.authorship,
            omitted=omitted,
        )
        basis = concept.facets.structure.basis
        if basis is not None:
            projected_basis: dict[str, Any] = {}
            for name in (
                "scope",
                "source_path",
                "extractor_ref",
                "source_content_hash",
                "concept_observation_hash",
                "aggregate_input_hash",
            ):
                value = getattr(basis, name)
                if value is None:
                    continue
                wire = _wire(value)
                safe = _safe_internal_scalar(name, wire, omitted)
                if safe is not None:
                    projected_basis[name] = safe
            payload["evidence"]["basis"] = projected_basis
        if governance is not None:
            review_items = _safe_internal_value(
                "review_items",
                _mapping(governance.get("reviews")).get("items", []),
                omitted,
            )
            payload["review"]["items"] = (
                review_items if isinstance(review_items, list) else []
            )
            lifecycle_items = _safe_internal_value(
                "lifecycle_events",
                _mapping(governance.get("lifecycle_events")).get("items", []),
                omitted,
            )
            payload["lifecycle"]["events"] = (
                lifecycle_items if isinstance(lifecycle_items, list) else []
            )
        extensions = _project_unknown_extensions(
            concept.extensions,
            omitted=omitted,
        )
        if extensions:
            payload["extensions"] = extensions
    else:
        omitted["semantic_page_hashes"] += 1
        if concept.facets.structure.basis is not None:
            omitted["evidence_payloads"] += 1
        actor = concept.facets.semantics.authorship
        if any(
            value is not None
            for value in (
                actor.actor_id,
                actor.version,
                actor.model,
                actor.organization,
            )
        ):
            omitted["actor_identities"] += 1
        if governance is not None:
            lifecycle_items = _mapping(
                governance.get("lifecycle_events")
            ).get("items", [])
            if isinstance(lifecycle_items, Sequence) and not isinstance(
                lifecycle_items,
                (str, bytes),
            ):
                for item in lifecycle_items:
                    if (
                        isinstance(item, Mapping)
                        and _actor_has_identity(item.get("actor"))
                    ):
                        omitted["actor_identities"] += 1
    return payload


def _project_freshness(
    concept: ConceptRecord,
    view: KnowledgeReadView,
) -> dict[str, Any]:
    report = view.freshness
    if report is None:
        return {
            "state": NOT_EVALUATED,
            "reason": NOT_EVALUATED,
            "evaluated": False,
            "live_comparison_performed": False,
        }
    result = report.by_locator.get(concept.locator)
    if result is None:
        raise KnowledgeProjectionError(
            "projection-freshness-incomplete",
            "view.freshness",
            f"has no result for concept {concept.locator!r}",
        )
    if (
        result.locator != concept.locator
        or not isinstance(result.state, ComputedFreshness)
        or result.reason_code not in KNOWN_FRESHNESS_REASON_CODES
        or not isinstance(result.live_comparison_performed, bool)
        or (
            result.state is ComputedFreshness.CURRENT
            and (
                not result.live_comparison_performed
                or result.reason_code
                != REASON_RECORDED_BASIS_MATCHES_LIVE_EVALUATION
            )
        )
        or (
            result.reason_code
            == REASON_RECORDED_BASIS_MATCHES_LIVE_EVALUATION
            and result.state is not ComputedFreshness.CURRENT
        )
    ):
        raise KnowledgeProjectionError(
            "projection-freshness-invalid",
            f"view.freshness.{concept.locator}",
            "contains an invalid or unrecognized freshness result",
        )
    payload = {
        "state": result.state.value,
        "reason": result.reason_code,
        "evaluated": True,
        "live_comparison_performed": result.live_comparison_performed,
    }
    hint = knowledge_freshness_hint(
        result.state,
        result.reason_code,
    )
    if hint is not None:
        payload["hint"] = hint
    return payload


def _project_review(
    governance: Mapping[str, Any] | None,
    *,
    profile: KnowledgeProjectionProfile,
    omitted: dict[str, int],
) -> dict[str, Any]:
    reviews = (
        _mapping(governance.get("reviews"))
        if governance is not None
        else {}
    )
    items = reviews.get("items")
    item_values = (
        list(items)
        if isinstance(items, Sequence) and not isinstance(items, (str, bytes))
        else []
    )
    valid_returned = sum(
        1
        for item in item_values
        if isinstance(item, Mapping) and item.get("state") == "valid"
    )
    expired_returned = sum(
        1
        for item in item_values
        if isinstance(item, Mapping) and item.get("state") == "expired"
    )
    total = _nonnegative_int(reviews.get("total"), fallback=len(item_values))
    returned = _nonnegative_int(
        reviews.get("returned"),
        fallback=len(item_values),
    )
    # Bounded projection summaries can omit older states.  Preserve exact
    # declared totals while describing only the visible state conservatively.
    if total == 0:
        state = "untracked"
    elif bool(reviews.get("truncated")):
        state = "partial"
    elif valid_returned and expired_returned:
        state = "mixed"
    elif valid_returned:
        state = "has-valid-sections"
    elif expired_returned:
        state = "has-expired-sections"
    else:
        state = UNKNOWN_VALUE
    safe_items: list[dict[str, Any]] = []
    for item in item_values:
        if not isinstance(item, Mapping):
            continue
        section_locator = _safe_internal_scalar(
            "section_locator",
            str(item.get("section_locator", "")),
            omitted,
        )
        if section_locator is None:
            continue
        item_reasons: list[str] = []
        raw_reasons = item.get("reasons", [])
        if isinstance(raw_reasons, Sequence) and not isinstance(
            raw_reasons,
            (str, bytes),
        ):
            for reason in raw_reasons:
                if not isinstance(reason, str):
                    continue
                safe_reason = _safe_internal_scalar(
                    "review_reason",
                    reason,
                    omitted,
                )
                if safe_reason is not None:
                    item_reasons.append(safe_reason)
        safe_items.append(
            {
                "section_locator": section_locator,
                "state": str(item.get("state", UNKNOWN_VALUE)),
                "reasons": sorted(item_reasons),
            }
        )
    reasons = sorted(
        {
            reason
            for item in safe_items
            for reason in item["reasons"]
        }
    )
    if profile is KnowledgeProjectionProfile.PUBLIC_PORTABLE:
        for item in item_values:
            if not isinstance(item, Mapping):
                continue
            if _actor_has_identity(item.get("reviewer")):
                omitted["actor_identities"] += 1
    return {
        "scope": "section",
        "state": state,
        "total": total,
        "returned": returned,
        "valid_returned": valid_returned,
        "expired_returned": expired_returned,
        "truncated": bool(reviews.get("truncated", False)),
        "reasons": reasons,
        "items": safe_items,
    }


def _project_machine_check(
    concept: ConceptRecord,
    view: KnowledgeReadView,
) -> dict[str, Any]:
    evaluated = view.machine_verification
    availability = evaluated.availability
    if availability is MachineVerificationAvailability.NOT_EVALUATED:
        return {
            "state": NOT_EVALUATED,
            "reason": evaluated.reason,
            "availability": availability.value,
        }
    if availability is MachineVerificationAvailability.ABSENT:
        return {
            "state": "not-run",
            "reason": evaluated.reason,
            "availability": availability.value,
        }
    if availability is MachineVerificationAvailability.INVALID:
        return {
            "state": "invalid",
            "reason": evaluated.reason,
            "availability": availability.value,
        }
    if evaluated.scope_kind == "unknown":
        return {
            "state": "not-run",
            "reason": "verification-receipt-scope-unknown",
            "availability": "absent",
        }
    if (
        evaluated.scope_kind == "concept"
        and evaluated.scope_locator != concept.locator
    ):
        return {
            "state": "not-run",
            "reason": "verification-receipt-not-present-for-concept",
            "availability": "absent",
        }
    if not evaluated.valid:
        reason = (
            evaluated.invalidation_reasons[0]
            if evaluated.invalidation_reasons
            else evaluated.reason
        )
        return {
            "state": "invalid",
            "reason": reason,
            "availability": availability.value,
            "valid": False,
            "recorded_result": (
                evaluated.recorded_result or UNKNOWN_VALUE
            ),
            "checks": _machine_check_counts(evaluated.checks),
        }
    if evaluated.recorded_result == "passed":
        state = "verified"
        reason = "verification-receipt-passed"
    elif evaluated.recorded_result == "failed":
        state = "failed"
        reason = "verification-receipt-failed"
    else:
        state = "invalid"
        reason = "verification-receipt-result-unknown"
    return {
        "state": state,
        "reason": reason,
        "availability": availability.value,
        "valid": True,
        "recorded_result": evaluated.recorded_result or UNKNOWN_VALUE,
        "checks": _machine_check_counts(evaluated.checks),
    }


def _machine_check_counts(
    checks: Mapping[str, Mapping[str, Any]],
) -> dict[str, int]:
    results = [
        str(check.get("result", UNKNOWN_VALUE))
        for check in checks.values()
    ]
    return {
        "total": len(results),
        "passed": sum(result == "passed" for result in results),
        "failed": sum(result == "failed" for result in results),
    }


def _project_relationships(
    knowledge: KnowledgeIndex,
    *,
    concepts_by_locator: Mapping[str, ConceptRecord],
    concepts_by_uid: Mapping[str, ConceptRecord],
    bundle_id: str,
    profile: KnowledgeProjectionProfile,
    limit: int,
    omitted: dict[str, int],
) -> tuple[dict[str, Mapping[str, Any]], bool]:
    graph = typed_graph_from_knowledge_extensions(knowledge.extensions)
    if graph is None:
        return {}, False

    # Keep the same incidence and ordering contract as
    # DocumentationGraphQueryService._incident_typed_graph_edges.  The graph
    # validator has already canonicalized edges by key, so the edge index is
    # the stable secondary order.
    by_locator: dict[str, dict[int, str]] = {
        locator: {} for locator in concepts_by_locator
    }
    related_by_edge: dict[
        int,
        tuple[ConceptRecord | None, ConceptRecord | None],
    ] = {}
    edges = list(graph["edges"])
    for index, edge in enumerate(edges):
        source = _endpoint_concept(
            _mapping(edge.get("from")),
            concepts_by_locator,
            concepts_by_uid,
        )
        target = _endpoint_concept(
            _mapping(edge.get("target")),
            concepts_by_locator,
            concepts_by_uid,
        )
        related_by_edge[index] = (source, target)
        if source is not None:
            by_locator[source.locator][index] = "outgoing"
        if target is not None:
            previous = by_locator[target.locator].get(index)
            by_locator[target.locator][index] = (
                "both" if previous == "outgoing" else "incoming"
            )

    direction_order = {"incoming": 0, "outgoing": 1, "both": 2}
    projected: dict[str, Mapping[str, Any]] = {}
    for locator, incidents in by_locator.items():
        ordered = sorted(
            incidents.items(),
            key=lambda item: (
                direction_order[item[1]],
                item[0],
            ),
        )
        selected = ordered[:limit]
        values: list[dict[str, Any]] = []
        for index, direction in selected:
            edge = edges[index]
            source, target = related_by_edge[index]
            if direction == "incoming":
                endpoint = _mapping(edge.get("from"))
                related = source
            else:
                endpoint = _mapping(edge.get("target"))
                related = target or source
            values.append(
                _project_relation(
                    edge,
                    direction=direction,
                    endpoint=endpoint,
                    related=related,
                    bundle_id=bundle_id,
                    profile=profile,
                    omitted=omitted,
                )
            )
        projected[locator] = MappingProxyType(
            {
                "availability": "ready",
                "total": len(ordered),
                "returned": len(values),
                "limit": limit,
                "truncated": len(ordered) > len(values),
                "items": values,
            }
        )
    return projected, True


def _project_relation(
    edge: Mapping[str, Any],
    *,
    direction: str,
    endpoint: Mapping[str, Any],
    related: ConceptRecord | None,
    bundle_id: str,
    profile: KnowledgeProjectionProfile,
    omitted: dict[str, int],
) -> dict[str, Any]:
    evidence = _mapping(edge.get("evidence"))
    coverage = _mapping(edge.get("coverage"))
    resolution = str(edge.get("resolution", "unresolved"))
    target = _project_endpoint(
        endpoint,
        related=related,
        resolution=resolution,
        bundle_id=bundle_id,
        profile=profile,
        omitted=omitted,
    )
    payload: dict[str, Any] = {
        "kind": _project_relationship_kind(
            edge.get("kind"),
            profile=profile,
            omitted=omitted,
        ),
        "direction": direction,
        "origin": str(edge.get("origin", UNKNOWN_VALUE)),
        "resolution": resolution,
        "target": target,
        "evidence": {
            "state": str(evidence.get("state", UNKNOWN_VALUE)),
            "observed": _nonnegative_int(evidence.get("observed")),
            "unique": _nonnegative_int(evidence.get("unique")),
            "emitted": _nonnegative_int(evidence.get("emitted")),
            "omitted": _nonnegative_int(evidence.get("omitted")),
        },
        "coverage": {
            "observed": _nonnegative_int(coverage.get("observed")),
            "emitted": _nonnegative_int(coverage.get("emitted")),
            "omitted": _nonnegative_int(coverage.get("omitted")),
            "limit": _nonnegative_int(coverage.get("limit")),
            "truncated": bool(coverage.get("truncated", False)),
        },
    }
    if profile is KnowledgeProjectionProfile.INTERNAL:
        payload["key"] = (
            _safe_internal_scalar(
                "relationship_key",
                str(edge.get("key", "")),
                omitted,
            )
            or UNKNOWN_VALUE
        )
        aggregate_input_hash = evidence.get("aggregate_input_hash")
        if isinstance(aggregate_input_hash, str):
            payload["evidence"]["aggregate_input_hash"] = aggregate_input_hash
        samples = evidence.get("samples")
        if isinstance(samples, Sequence) and not isinstance(samples, (str, bytes)):
            safe_samples: list[Any] = []
            for sample in samples:
                safe = _safe_internal_value(
                    "relationship_evidence",
                    sample,
                    omitted,
                )
                if safe is not None:
                    safe_samples.append(safe)
            payload["evidence"]["samples"] = safe_samples
        payload["coverage"]["limitations"] = [
            safe
            for value in coverage.get("limitations", [])
            if isinstance(value, str)
            and (
                safe := _safe_internal_scalar(
                    "relationship_limitation",
                    value,
                    omitted,
                )
            )
            is not None
        ]
    else:
        samples = evidence.get("samples")
        if isinstance(samples, Sequence) and not isinstance(samples, (str, bytes)):
            omitted["relationship_evidence_samples"] += len(samples)
        if evidence.get("aggregate_input_hash") is not None:
            omitted["internal_hashes"] += 1
        if edge.get("key") is not None:
            omitted["internal_hashes"] += 1
    return payload


def _project_endpoint(
    endpoint: Mapping[str, Any],
    *,
    related: ConceptRecord | None,
    resolution: str,
    bundle_id: str,
    profile: KnowledgeProjectionProfile,
    omitted: dict[str, int],
) -> dict[str, Any]:
    kind = str(endpoint.get("kind", UNKNOWN_VALUE))
    if related is not None and resolution == "resolved":
        governance = _governance_summary(related)
        uid = (
            str(governance["uid"])
            if governance is not None and isinstance(governance.get("uid"), str)
            else UNKNOWN_VALUE
        )
        return {
            "kind": "concept",
            "present": True,
            "canonical_path": related.document.canonical_path,
            "title": (
                _safe_internal_scalar("relationship_title", related.title, omitted)
                or "Related concept"
            ),
            "concept_kind": _project_concept_kind(
                related.concept_kind,
                profile=profile,
                omitted=omitted,
            ),
            "namespaced_uid": _namespaced_uid(bundle_id, uid),
        }
    if kind == "external-resource":
        payload = {
            "kind": kind,
            "present": False,
            "label": "External resource",
        }
        if profile is KnowledgeProjectionProfile.INTERNAL:
            for name in ("resource", "uri"):
                value = endpoint.get(name)
                if isinstance(value, str):
                    safe = _safe_internal_scalar(name, value, omitted)
                    if safe is not None:
                        payload[name] = safe
        else:
            omitted["external_target_details"] += 1
        return payload
    if kind == "unresolved":
        candidates = endpoint.get("candidates")
        candidate_count = (
            len(candidates)
            if isinstance(candidates, Sequence)
            and not isinstance(candidates, (str, bytes))
            else 0
        )
        label = (
            "Ambiguous target"
            if resolution == "ambiguous"
            else "Unresolved target"
        )
        payload = {
            "kind": kind,
            "present": False,
            "label": label,
        }
        if profile is KnowledgeProjectionProfile.INTERNAL:
            payload["candidate_count"] = candidate_count
            raw = endpoint.get("raw_target")
            if isinstance(raw, str):
                safe = _safe_internal_scalar("raw_target", raw, omitted)
                if safe is not None:
                    payload["raw_target"] = safe
            if isinstance(candidates, Sequence) and not isinstance(
                candidates,
                (str, bytes),
            ):
                safe_candidates = _safe_internal_value(
                    "candidates",
                    candidates,
                    omitted,
                )
                if safe_candidates is not None:
                    payload["candidates"] = safe_candidates
        else:
            omitted["unresolved_target_details"] += 1
        return payload
    payload = {
        "kind": kind,
        "present": False,
        "label": "Source symbol" if kind == "source-symbol" else "Unknown target",
    }
    if profile is KnowledgeProjectionProfile.INTERNAL:
        for name in ("source_path", "symbol", "locator", "uid"):
            value = endpoint.get(name)
            if isinstance(value, str):
                safe = _safe_internal_scalar(name, value, omitted)
                if safe is not None:
                    payload[name] = safe
    else:
        omitted["source_target_details"] += 1
    return payload


def _endpoint_concept(
    endpoint: Mapping[str, Any],
    concepts_by_locator: Mapping[str, ConceptRecord],
    concepts_by_uid: Mapping[str, ConceptRecord],
) -> ConceptRecord | None:
    if endpoint.get("kind") != "concept":
        return None
    locator = endpoint.get("locator")
    if isinstance(locator, str):
        return concepts_by_locator.get(locator)
    uid = endpoint.get("uid")
    if isinstance(uid, str):
        return concepts_by_uid.get(uid)
    return None


def _empty_relationships(available: bool, limit: int) -> Mapping[str, Any]:
    return MappingProxyType(
        {
            "availability": "ready" if available else "absent",
            "total": 0,
            "returned": 0,
            "limit": limit,
            "truncated": False,
            "items": [],
        }
    )


def _projection_warnings(
    concepts: Mapping[str, Mapping[str, Any]],
    *,
    graph_available: bool,
    governance_available: bool,
    omitted: Mapping[str, int],
) -> tuple[str, ...]:
    warnings: set[str] = set()
    if not graph_available:
        warnings.add("typed-graph-not-available")
    if not governance_available:
        warnings.add("governance-not-available")
    if any(
        _mapping(concept.get("freshness")).get("state") == NOT_EVALUATED
        for concept in concepts.values()
    ):
        warnings.add("freshness-not-evaluated")
    warnings.update(
        f"omitted-{name.replace('_', '-')}"
        for name, count in omitted.items()
        if count > 0
    )
    return tuple(sorted(warnings))


def _initial_omitted_counts(
    knowledge: KnowledgeIndex,
    profile: KnowledgeProjectionProfile,
) -> dict[str, int]:
    counts = {
        "actor_identities": 0,
        "credential_like_values": 0,
        "environment_details": 0,
        "evidence_payloads": 0,
        "external_target_details": 0,
        "internal_hashes": 0,
        "private_repository_identity": 0,
        "private_producer_records": 0,
        "relationship_evidence_samples": 0,
        "semantic_page_hashes": 0,
        "source_target_details": 0,
        "unapproved_concept_kinds": 0,
        "unapproved_relationship_kinds": 0,
        "unknown_extensions": 0,
        "unresolved_target_details": 0,
        "unsafe_paths": 0,
    }
    if profile is KnowledgeProjectionProfile.PUBLIC_PORTABLE:
        counts["unknown_extensions"] = _unknown_extension_count(knowledge)
        counts["private_producer_records"] = (
            1
            + len(knowledge.bundle.producer.extractors)
            + len(knowledge.bundle.producer.plugins)
        )
        # Snapshot hashes are omitted except for the exact source knowledge
        # commitment carried separately at the projection root.
        counts["internal_hashes"] += 4
    else:
        # The internal projection deliberately retains only selected extension
        # locations. Account for safe-but-unprojected extension locations
        # instead of silently implying lossless passthrough.
        retained_locations: list[Mapping[str, Any]] = [knowledge.extensions]
        for concept in knowledge.concepts:
            retained_locations.extend(
                (
                    concept.extensions,
                    concept.facets.semantics.authorship.extensions,
                )
            )
        retained = sum(
            1
            for extensions in retained_locations
            for key in extensions
            if key not in _RESERVED_EXTENSION_KEYS
        )
        counts["unknown_extensions"] = max(
            0,
            _unknown_extension_count(knowledge) - retained,
        )
    return counts


def _unknown_extension_count(knowledge: KnowledgeIndex) -> int:
    values: list[Mapping[str, Any]] = [
        knowledge.extensions,
        knowledge.bundle.extensions,
        knowledge.bundle.repository.extensions,
        knowledge.bundle.snapshot.extensions,
        knowledge.bundle.producer.extensions,
        knowledge.bundle.producer.tool.extensions,
    ]
    values.extend(item.extensions for item in knowledge.bundle.producer.extractors)
    values.extend(item.extensions for item in knowledge.bundle.producer.plugins)
    for concept in knowledge.concepts:
        values.extend(
            (
                concept.extensions,
                concept.document.extensions,
                concept.facets.extensions,
                concept.facets.structure.extensions,
                concept.facets.semantics.extensions,
                concept.facets.semantics.authorship.extensions,
            )
        )
        if concept.facets.structure.basis is not None:
            values.append(concept.facets.structure.basis.extensions)
    for relationship in knowledge.relationships:
        values.extend(
            (
                relationship.extensions,
                relationship.target.extensions,
                relationship.evidence.extensions,
            )
        )
        if relationship.target.location is not None:
            values.append(relationship.target.location.extensions)
    return sum(
        1
        for extensions in values
        for key in extensions
        if key not in _RESERVED_EXTENSION_KEYS
    )


def _project_unknown_extensions(
    extensions: Mapping[str, Any],
    *,
    omitted: dict[str, int],
) -> dict[str, Any]:
    projected: dict[str, Any] = {}
    for key in sorted(extensions):
        if key in _RESERVED_EXTENSION_KEYS:
            continue
        safe = _safe_internal_value(key, extensions[key], omitted)
        if safe is not None:
            projected[key] = safe
    return projected


def _safe_internal_value(
    key: str,
    value: Any,
    omitted: dict[str, int],
) -> Any:
    if _SENSITIVE_KEY_RE.search(key):
        category = (
            "environment_details"
            if "env" in key.casefold()
            else "credential_like_values"
        )
        omitted[category] += 1
        return None
    if isinstance(value, Mapping):
        result = {}
        for child_key in sorted(value, key=str):
            if not isinstance(child_key, str):
                omitted["credential_like_values"] += 1
                continue
            child = _safe_internal_value(child_key, value[child_key], omitted)
            if child is not None:
                result[child_key] = child
        return result
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        result = []
        for item in value:
            safe = _safe_internal_value(key, item, omitted)
            if safe is not None:
                result.append(safe)
        return result
    if isinstance(value, str):
        return _safe_internal_scalar(key, value, omitted)
    if value is None or isinstance(value, (bool, int)):
        return value
    if isinstance(value, float):
        if math.isfinite(value):
            return value
        omitted["credential_like_values"] += 1
        return None
    omitted["credential_like_values"] += 1
    return None


def _safe_internal_scalar(
    key: str,
    value: str,
    omitted: dict[str, int],
) -> str | None:
    if (
        _SENSITIVE_KEY_RE.search(key)
        or _CONTROL_RE.search(value)
        or _CREDENTIAL_VALUE_RE.search(value)
        or _URI_USERINFO_RE.search(value)
        or _RAW_VCS_REMOTE_RE.search(value)
    ):
        omitted["credential_like_values"] += 1
        return None
    if (
        value.startswith("/")
        or value.startswith("\\\\")
        or _WINDOWS_ABSOLUTE_RE.match(value)
        or _EMBEDDED_ABSOLUTE_RE.search(value)
        or value.casefold().startswith("file:")
    ):
        omitted["unsafe_paths"] += 1
        return None
    return value


def _project_actor(actor: Any, *, omitted: dict[str, int]) -> dict[str, Any]:
    projected: dict[str, Any] = {"kind": actor.kind.value}
    for name in ("actor_id", "version", "model", "organization"):
        value = getattr(actor, name)
        if value is None:
            continue
        safe = _safe_internal_scalar(name, value, omitted)
        if safe is not None:
            projected["id" if name == "actor_id" else name] = safe
    extensions = _project_unknown_extensions(actor.extensions, omitted=omitted)
    if extensions:
        projected["extensions"] = extensions
    return projected


def _governance_summary(
    concept: ConceptRecord,
) -> Mapping[str, Any] | None:
    value = concept.extensions.get(GOVERNANCE_EXTENSION_KEY)
    return value if isinstance(value, Mapping) else None


def _namespaced_uid(bundle_id: str, uid: str) -> str:
    if bundle_id == UNKNOWN_VALUE or uid == UNKNOWN_VALUE:
        return UNKNOWN_VALUE
    # ``#`` is forbidden by both governance ID grammars, unlike ``::`` which
    # is valid inside bundle IDs and would make the combined value ambiguous.
    return f"{bundle_id}#{uid}"


def _approved_public_repository_identity(
    knowledge: KnowledgeIndex,
    profile: KnowledgeProjectionProfile,
    requested: str | None,
) -> str | None:
    if requested is not None and not isinstance(requested, str):
        raise KnowledgeProjectionError(
            "projection-public-identity-invalid",
            "public_repository_identity",
            "must be a string or None",
        )
    if profile is KnowledgeProjectionProfile.INTERNAL:
        if requested is not None:
            raise KnowledgeProjectionError(
                "projection-public-identity-not-applicable",
                "public_repository_identity",
                "is valid only for the 'public-portable' profile",
            )
        return None
    if requested is None:
        return None
    repository = knowledge.bundle.repository
    if (
        requested == UNKNOWN_VALUE
        or requested != repository.identity
        or repository.identity_source
        is not RepositoryIdentitySource.CONFIGURED_PUBLIC
    ):
        raise KnowledgeProjectionError(
            "projection-public-identity-invalid",
            "public_repository_identity",
            (
                "must exactly match a configured-public identity in the "
                "validated committed artifact"
            ),
        )
    return requested


def _project_concept_kind(
    value: object,
    *,
    profile: KnowledgeProjectionProfile,
    omitted: dict[str, int],
) -> str:
    wire = _wire(value)
    if wire in {kind.value for kind in ConceptKind}:
        return wire
    if profile is KnowledgeProjectionProfile.INTERNAL:
        return (
            _safe_internal_scalar("concept_kind", wire, omitted)
            or UNKNOWN_VALUE
        )
    omitted["unapproved_concept_kinds"] += 1
    return UNKNOWN_VALUE


def _project_relationship_kind(
    value: object,
    *,
    profile: KnowledgeProjectionProfile,
    omitted: dict[str, int],
) -> str:
    wire = _wire(value)
    if wire in CORE_RELATIONSHIP_KINDS:
        return wire
    if profile is KnowledgeProjectionProfile.INTERNAL:
        return (
            _safe_internal_scalar("relationship_kind", wire, omitted)
            or UNKNOWN_VALUE
        )
    omitted["unapproved_relationship_kinds"] += 1
    return UNKNOWN_VALUE


def _actor_has_identity(value: object) -> bool:
    actor = _mapping(value)
    return any(
        actor.get(name) is not None
        for name in ("id", "version", "model", "organization")
    )


def _projection_profile(
    value: KnowledgeProjectionProfile | str,
) -> KnowledgeProjectionProfile:
    try:
        return (
            value
            if isinstance(value, KnowledgeProjectionProfile)
            else KnowledgeProjectionProfile(value)
        )
    except (TypeError, ValueError) as exc:
        raise KnowledgeProjectionError(
            "projection-profile-invalid",
            "profile",
            "must be 'internal' or 'public-portable'",
        ) from exc


def _relationship_limit(value: object) -> int:
    if (
        isinstance(value, bool)
        or not isinstance(value, int)
        or not 1 <= value <= MAX_RELATIONSHIP_LIMIT
    ):
        raise KnowledgeProjectionError(
            "projection-limit-invalid",
            "relationship_limit",
            (
                "must be an integer from 1 through "
                f"{MAX_RELATIONSHIP_LIMIT}"
            ),
        )
    return value


def _mapping(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _wire(value: object) -> str:
    if isinstance(value, Enum):
        return str(value.value)
    return str(value)


def _nonnegative_int(value: object, *, fallback: int = 0) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        return fallback
    return value


def _deep_freeze(
    value: object,
    path: str,
    *,
    _active: set[int] | None = None,
) -> Any:
    """Return a detached, recursively immutable JSON-compatible value."""

    active = set() if _active is None else _active
    if isinstance(value, Mapping):
        marker = id(value)
        if marker in active:
            raise TypeError(f"{path} must not contain recursive mappings")
        active.add(marker)
        try:
            frozen: dict[str, Any] = {}
            for key, item in value.items():
                if not isinstance(key, str):
                    raise TypeError(f"{path} keys must be strings")
                frozen[key] = _deep_freeze(
                    item,
                    f"{path}.{key}",
                    _active=active,
                )
            return MappingProxyType(frozen)
        finally:
            active.remove(marker)
    if isinstance(value, (list, tuple)):
        marker = id(value)
        if marker in active:
            raise TypeError(f"{path} must not contain recursive sequences")
        active.add(marker)
        try:
            return tuple(
                _deep_freeze(item, f"{path}[{index}]", _active=active)
                for index, item in enumerate(value)
            )
        finally:
            active.remove(marker)
    if value is None or isinstance(value, (str, bool, int, float, Enum)):
        return value
    raise TypeError(
        f"{path} must contain only JSON-compatible projection values"
    )


def _json_copy(value: object) -> Any:
    if isinstance(value, Mapping):
        return {
            str(key): _json_copy(item)
            for key, item in sorted(value.items(), key=lambda pair: str(pair[0]))
        }
    if isinstance(value, tuple):
        return [_json_copy(item) for item in value]
    if isinstance(value, list):
        return [_json_copy(item) for item in value]
    if isinstance(value, Enum):
        return value.value
    return value


def _boolean_text(value: bool) -> str:
    return "true" if value else "false"


__all__ = [
    "DEFAULT_RELATIONSHIP_LIMIT",
    "KnowledgeProjection",
    "KnowledgeProjectionError",
    "MAX_RELATIONSHIP_LIMIT",
    "NOT_EVALUATED",
    "PROJECTION_SCHEMA_VERSION",
    "project_knowledge",
    "projection_concept_summary",
    "projection_json_value",
    "serialize_knowledge_projection",
    "validate_projection_summaries",
]
