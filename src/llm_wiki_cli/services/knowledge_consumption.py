"""One read-only knowledge session shared by native consumers.

The session loads and validates projection state once, then optionally computes
freshness once from an already collected :class:`LiveKnowledgeEvaluation`.
It never extracts source, walks a repository, repairs artifacts, or writes
state.  Callers should create one view per native operation and pass that view
to every downstream consumer participating in the operation.
"""

from __future__ import annotations

import re
from collections import Counter
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from types import MappingProxyType
from typing import Any

from .knowledge_freshness import (
    KnowledgeFreshnessReport,
    LiveKnowledgeEvaluation,
    evaluate_knowledge_freshness,
)
from .knowledge_loader import (
    KnowledgeLoadIssue,
    KnowledgeLoadResult,
    KnowledgeMismatchPolicy,
    KnowledgeStateLoadError,
    load_knowledge_state,
)
from .knowledge_model import (
    ComputedFreshness,
    EvidenceState,
    KnowledgeIndex,
    KnowledgeLoadState,
)
from .sync_manifest import SyncManifest


class KnowledgeAvailability(str, Enum):
    """Knowledge capability available to every native read consumer."""

    READY = "ready"
    ABSENT = "absent"
    DEGRADED = "degraded"
    UNSUPPORTED = "unsupported"


class KnowledgeReadMode(str, Enum):
    """Whether a read session evaluates live concept freshness."""

    EVALUATE_FRESHNESS = "evaluate-freshness"
    DEFAULT = "evaluate-freshness"
    SNAPSHOT_ONLY = "snapshot-only"


class KnowledgeReadReason(str, Enum):
    """Stable cross-consumer reasons for knowledge availability."""

    READY = "all-projection-commitments-match"
    ABSENT = "knowledge-projection-not-present"
    DEGRADED_INVALID = "policy-selected-surface-only-fallback-after-invalid"
    DEGRADED_MIXED_SNAPSHOT = (
        "policy-selected-surface-only-fallback-after-mixed-snapshot"
    )
    UNSUPPORTED_SCHEMA = "knowledge-schema-version-unsupported"
    KNOWLEDGE_SCHEMA_VERSION_UNSUPPORTED = "knowledge-schema-version-unsupported"
    MANIFEST_VERSION_UNSUPPORTED = "manifest-version-unsupported"
    SURFACE_SCHEMA_VERSION_UNSUPPORTED = "surface-schema-version-unsupported"


class MachineVerificationAvailability(str, Enum):
    """Whether the read session evaluated a disposable machine receipt."""

    NOT_EVALUATED = "not-evaluated"
    ABSENT = "absent"
    INVALID = "invalid"
    RECORDED = "recorded"


_MACHINE_REASON_NOT_EVALUATED = "verification-receipt-not-evaluated"
_MACHINE_REASON_ABSENT = "verification-receipt-not-present"
_MACHINE_REASON_INVALID = "verification-receipt-invalid"
_MACHINE_REASON_VALID = "verification-receipt-valid"
_MACHINE_REASON_INVALIDATED = "verification-receipt-invalidated"
_MACHINE_SCOPE_KINDS = frozenset({"bundle", "concept", "unknown"})
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
_MACHINE_RESULT_VALUES = frozenset({"passed", "failed"})
_MACHINE_CHECKER_ID_RE = re.compile(r"^[a-z][a-z0-9]*(?:-[a-z0-9]+)*$")
_MACHINE_CHECKER_VERSION_RE = re.compile(r"^[0-9]+(?:\.[0-9]+)*$")
_MACHINE_CODE_RE = re.compile(r"^[a-z][a-z0-9]*(?:-[a-z0-9]+)*$")
_MACHINE_SCOPE_UID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._~:@/-]{0,255}$")
_MACHINE_SUBJECT_RE = re.compile(
    r"^[A-Za-z0-9][A-Za-z0-9._~:/?#@%+=-]{0,319}$"
)
_MACHINE_MAX_CHECKS = 32
_MACHINE_MAX_DIAGNOSTICS = 50


@dataclass(frozen=True)
class MachineVerificationReadView:
    """One receipt evaluation shared by all consumers in a read operation."""

    availability: MachineVerificationAvailability = (
        MachineVerificationAvailability.NOT_EVALUATED
    )
    reason: str = _MACHINE_REASON_NOT_EVALUATED
    scope_kind: str = "unknown"
    scope_uid: str | None = None
    scope_locator: str | None = None
    valid: bool | None = None
    invalidation_reasons: tuple[str, ...] = ()
    recorded_result: str | None = None
    passed: bool | None = None
    checks: Mapping[str, Mapping[str, Any]] = field(
        default_factory=lambda: MappingProxyType({})
    )

    def __post_init__(self) -> None:
        if not isinstance(self.availability, MachineVerificationAvailability):
            raise TypeError(
                "machine verification availability must be "
                "MachineVerificationAvailability"
            )
        if not isinstance(self.reason, str):
            raise TypeError("machine verification reason must be a string")
        if (
            not isinstance(self.scope_kind, str)
            or self.scope_kind not in _MACHINE_SCOPE_KINDS
        ):
            raise ValueError(
                "machine verification scope_kind must be "
                "'bundle', 'concept', or 'unknown'"
            )
        invalidation_reasons = _machine_invalidation_reasons(
            self.invalidation_reasons
        )
        checks = _machine_verification_checks(self.checks)
        object.__setattr__(self, "invalidation_reasons", invalidation_reasons)
        object.__setattr__(self, "checks", checks)

        expected_reason = {
            MachineVerificationAvailability.NOT_EVALUATED: (
                _MACHINE_REASON_NOT_EVALUATED
            ),
            MachineVerificationAvailability.ABSENT: _MACHINE_REASON_ABSENT,
            MachineVerificationAvailability.INVALID: _MACHINE_REASON_INVALID,
        }.get(self.availability)
        if expected_reason is not None:
            if self.reason != expected_reason:
                raise ValueError(
                    "machine verification reason does not match availability"
                )
            if (
                self.scope_kind != "unknown"
                or self.scope_uid is not None
                or self.scope_locator is not None
                or self.valid is not None
                or invalidation_reasons
                or self.recorded_result is not None
                or self.passed is not None
                or checks
            ):
                raise ValueError(
                    "unrecorded machine verification state must not carry "
                    "receipt fields"
                )
            return

        if self.reason not in {
            _MACHINE_REASON_VALID,
            _MACHINE_REASON_INVALIDATED,
        }:
            raise ValueError(
                "recorded machine verification reason is unsupported"
            )
        if (
            not isinstance(self.scope_uid, str)
            or _MACHINE_SCOPE_UID_RE.fullmatch(self.scope_uid) is None
        ):
            raise ValueError(
                "recorded machine verification scope_uid is invalid"
            )
        if self.scope_kind == "concept":
            if (
                not isinstance(self.scope_locator, str)
                or _MACHINE_SUBJECT_RE.fullmatch(self.scope_locator) is None
            ):
                raise ValueError(
                    "concept machine verification scope requires a valid locator"
                )
        elif self.scope_locator is not None:
            raise ValueError(
                "non-concept machine verification scope must not carry a locator"
            )
        if not isinstance(self.valid, bool):
            raise TypeError(
                "recorded machine verification valid must be a boolean"
            )
        if self.valid:
            if self.reason != _MACHINE_REASON_VALID or invalidation_reasons:
                raise ValueError(
                    "valid machine verification must not carry invalidation reasons"
                )
            if self.scope_kind == "unknown":
                raise ValueError(
                    "an unknown machine verification scope cannot be valid"
                )
        else:
            if (
                self.reason != _MACHINE_REASON_INVALIDATED
                or not invalidation_reasons
            ):
                raise ValueError(
                    "invalidated machine verification requires invalidation reasons"
                )
            if (
                self.scope_kind == "unknown"
                and "scope-changed" not in invalidation_reasons
            ):
                raise ValueError(
                    "an unknown machine verification scope requires scope-changed"
                )
        if (
            not isinstance(self.recorded_result, str)
            or self.recorded_result not in _MACHINE_RESULT_VALUES
        ):
            raise ValueError(
                "recorded machine verification result must be 'passed' or 'failed'"
            )
        if not isinstance(self.passed, bool):
            raise TypeError(
                "recorded machine verification passed must be a boolean"
            )
        if not checks:
            raise ValueError(
                "recorded machine verification must contain at least one check"
            )
        expected_result = (
            "passed"
            if all(check["result"] == "passed" for check in checks.values())
            else "failed"
        )
        if self.recorded_result != expected_result:
            raise ValueError(
                "recorded machine verification result does not match checks"
            )
        if self.passed != (self.valid and self.recorded_result == "passed"):
            raise ValueError(
                "machine verification passed does not match validity and result"
            )


@dataclass(frozen=True)
class KnowledgeReadCounts:
    """Aggregate counts derived only from a ready knowledge projection.

    Evidence counts cover the structural evidence state of each concept.
    Every closed evidence and freshness enum state is present, including states
    whose count is zero.  ``freshness_by_state`` is ``None`` in snapshot-only
    mode rather than a fabricated set of zero freshness claims.
    """

    concepts_total: int
    concepts_by_kind: Mapping[str, int]
    evidence_by_state: Mapping[EvidenceState, int]
    freshness_by_state: Mapping[ComputedFreshness, int] | None

    @property
    def concept_total(self) -> int:
        """Compatibility spelling for consumers using a singular noun."""

        return self.concepts_total


@dataclass(frozen=True)
class KnowledgeReadView:
    """Validated, immutable-by-contract state for one native read operation."""

    availability: KnowledgeAvailability
    mode: KnowledgeReadMode
    reason: KnowledgeReadReason
    surface: Mapping[str, Any] | None
    knowledge: KnowledgeIndex | None
    manifest_basis: SyncManifest | None
    freshness: KnowledgeFreshnessReport | None
    counts: KnowledgeReadCounts | None
    projection_findings: tuple[KnowledgeLoadIssue, ...]
    load_state: KnowledgeLoadState
    underlying_load_state: KnowledgeLoadState | None = None
    machine_verification: MachineVerificationReadView = field(
        default_factory=MachineVerificationReadView
    )

    def __post_init__(self) -> None:
        if not isinstance(
            self.machine_verification,
            MachineVerificationReadView,
        ):
            raise TypeError(
                "machine_verification must be a MachineVerificationReadView"
            )

    @property
    def reason_code(self) -> str:
        return self.reason.value

    @property
    def ready(self) -> bool:
        return self.availability is KnowledgeAvailability.READY

    @property
    def knowledge_available(self) -> bool:
        return self.knowledge is not None

    @property
    def freshness_evaluated(self) -> bool:
        return self.freshness is not None

    @property
    def surface_payload(self) -> Mapping[str, Any] | None:
        return self.surface

    @property
    def knowledge_index(self) -> KnowledgeIndex | None:
        return self.knowledge

    @property
    def manifest(self) -> SyncManifest | None:
        return self.manifest_basis

    @property
    def findings(self) -> tuple[KnowledgeLoadIssue, ...]:
        return self.projection_findings


def _machine_invalidation_reasons(value: object) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence):
        raise TypeError(
            "machine verification invalidation_reasons must be a sequence"
        )
    reasons = tuple(value)
    if any(not isinstance(reason, str) for reason in reasons):
        raise TypeError(
            "machine verification invalidation_reasons must contain strings"
        )
    if any(reason not in _MACHINE_INVALIDATION_REASONS for reason in reasons):
        raise ValueError(
            "machine verification invalidation_reasons contains an unsupported "
            "reason"
        )
    if len(reasons) != len(set(reasons)):
        raise ValueError(
            "machine verification invalidation_reasons must be unique"
        )
    return reasons


def _machine_verification_checks(
    value: object,
) -> Mapping[str, Mapping[str, Any]]:
    if not isinstance(value, Mapping):
        raise TypeError("machine verification checks must be a mapping")
    if len(value) > _MACHINE_MAX_CHECKS:
        raise ValueError("machine verification checks exceed the receipt limit")
    normalized: dict[str, Mapping[str, Any]] = {}
    for checker_id in sorted(value, key=str):
        if (
            not isinstance(checker_id, str)
            or _MACHINE_CHECKER_ID_RE.fullmatch(checker_id) is None
        ):
            raise ValueError("machine verification checker id is invalid")
        normalized[checker_id] = _machine_verification_check(
            checker_id,
            value[checker_id],
        )
    return MappingProxyType(normalized)


def _machine_verification_check(
    checker_id: str,
    value: object,
) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise TypeError(
            f"machine verification check {checker_id!r} must be a mapping"
        )
    expected_fields = {
        "version",
        "result",
        "diagnostics",
        "diagnostic_coverage",
    }
    if set(value) != expected_fields:
        raise ValueError(
            f"machine verification check {checker_id!r} has invalid fields"
        )
    version = value["version"]
    if (
        not isinstance(version, str)
        or _MACHINE_CHECKER_VERSION_RE.fullmatch(version) is None
    ):
        raise ValueError(
            f"machine verification check {checker_id!r} version is invalid"
        )
    result = value["result"]
    if not isinstance(result, str) or result not in _MACHINE_RESULT_VALUES:
        raise ValueError(
            f"machine verification check {checker_id!r} result is invalid"
        )
    diagnostics = _machine_diagnostics(
        checker_id,
        value["diagnostics"],
    )
    coverage = _machine_diagnostic_coverage(
        checker_id,
        value["diagnostic_coverage"],
        emitted=len(diagnostics),
    )
    return MappingProxyType(
        {
            "version": version,
            "result": result,
            "diagnostics": diagnostics,
            "diagnostic_coverage": coverage,
        }
    )


def _machine_diagnostics(
    checker_id: str,
    value: object,
) -> tuple[Mapping[str, str], ...]:
    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence):
        raise TypeError(
            f"machine verification check {checker_id!r} diagnostics "
            "must be a sequence"
        )
    if len(value) > _MACHINE_MAX_DIAGNOSTICS:
        raise ValueError(
            f"machine verification check {checker_id!r} diagnostics "
            "exceed the receipt limit"
        )
    diagnostics: list[Mapping[str, str]] = []
    for diagnostic in value:
        if not isinstance(diagnostic, Mapping):
            raise TypeError(
                f"machine verification check {checker_id!r} diagnostic "
                "must be a mapping"
            )
        if set(diagnostic) not in ({"code"}, {"code", "subject"}):
            raise ValueError(
                f"machine verification check {checker_id!r} diagnostic "
                "has invalid fields"
            )
        code = diagnostic["code"]
        if (
            not isinstance(code, str)
            or _MACHINE_CODE_RE.fullmatch(code) is None
        ):
            raise ValueError(
                f"machine verification check {checker_id!r} diagnostic "
                "code is invalid"
            )
        normalized = {"code": code}
        if "subject" in diagnostic:
            subject = diagnostic["subject"]
            if (
                not isinstance(subject, str)
                or _MACHINE_SUBJECT_RE.fullmatch(subject) is None
            ):
                raise ValueError(
                    f"machine verification check {checker_id!r} diagnostic "
                    "subject is invalid"
                )
            normalized["subject"] = subject
        diagnostics.append(MappingProxyType(normalized))
    return tuple(diagnostics)


def _machine_diagnostic_coverage(
    checker_id: str,
    value: object,
    *,
    emitted: int,
) -> Mapping[str, int | bool]:
    if not isinstance(value, Mapping):
        raise TypeError(
            f"machine verification check {checker_id!r} diagnostic coverage "
            "must be a mapping"
        )
    expected_fields = {
        "observed",
        "emitted",
        "omitted",
        "limit",
        "truncated",
    }
    if set(value) != expected_fields:
        raise ValueError(
            f"machine verification check {checker_id!r} diagnostic coverage "
            "has invalid fields"
        )
    for name in ("observed", "emitted", "omitted", "limit"):
        item = value[name]
        if isinstance(item, bool) or not isinstance(item, int) or item < 0:
            raise ValueError(
                f"machine verification check {checker_id!r} diagnostic coverage "
                f"{name} is invalid"
            )
    truncated = value["truncated"]
    if not isinstance(truncated, bool):
        raise TypeError(
            f"machine verification check {checker_id!r} diagnostic coverage "
            "truncated must be a boolean"
        )
    if (
        value["limit"] != _MACHINE_MAX_DIAGNOSTICS
        or value["emitted"] != emitted
        or value["observed"] != value["emitted"] + value["omitted"]
        or truncated != (value["omitted"] > 0)
    ):
        raise ValueError(
            f"machine verification check {checker_id!r} diagnostic coverage "
            "is inconsistent"
        )
    return MappingProxyType(
        {
            "observed": value["observed"],
            "emitted": value["emitted"],
            "omitted": value["omitted"],
            "limit": value["limit"],
            "truncated": truncated,
        }
    )


_UNSUPPORTED_REASON_BY_ISSUE = {
    "knowledge-schema-version-unsupported": (
        KnowledgeReadReason.KNOWLEDGE_SCHEMA_VERSION_UNSUPPORTED
    ),
    "manifest-version-unsupported": KnowledgeReadReason.MANIFEST_VERSION_UNSUPPORTED,
    "surface-schema-version-unsupported": (
        KnowledgeReadReason.SURFACE_SCHEMA_VERSION_UNSUPPORTED
    ),
}


def build_knowledge_read_view(
    load_result: KnowledgeLoadResult,
    *,
    live_evaluation: LiveKnowledgeEvaluation | None = None,
    snapshot_only: bool = False,
    mode: KnowledgeReadMode | str | None = None,
) -> KnowledgeReadView:
    """Build one shared view from an already completed artifact load.

    A ready, ordinary session invokes the pure freshness evaluator exactly
    once.  Passing no live evaluation intentionally produces an all-unknown
    report; snapshot-only mode is the explicit way to skip evaluation.
    """

    if not isinstance(load_result, KnowledgeLoadResult):
        raise TypeError("load_result must be a KnowledgeLoadResult")
    selected_mode = _read_mode(snapshot_only=snapshot_only, mode=mode)
    _validate_load_result(load_result)

    effective_state = (
        load_result.underlying_status
        if load_result.status is KnowledgeLoadState.DEGRADED
        else load_result.status
    )
    assert effective_state is not None

    if effective_state is KnowledgeLoadState.VALID:
        assert load_result.surface is not None
        assert load_result.knowledge is not None
        assert load_result.manifest_basis is not None
        freshness = (
            None
            if selected_mode is KnowledgeReadMode.SNAPSHOT_ONLY
            else evaluate_knowledge_freshness(
                load_result.knowledge,
                live_evaluation,
            )
        )
        counts = _knowledge_counts(load_result.knowledge, freshness)
        return KnowledgeReadView(
            availability=KnowledgeAvailability.READY,
            mode=selected_mode,
            reason=KnowledgeReadReason.READY,
            surface=load_result.surface,
            knowledge=load_result.knowledge,
            manifest_basis=load_result.manifest_basis,
            freshness=freshness,
            counts=counts,
            projection_findings=load_result.issues,
            load_state=load_result.status,
            underlying_load_state=load_result.underlying_status,
        )

    if effective_state is KnowledgeLoadState.ABSENT:
        assert load_result.surface is not None
        return KnowledgeReadView(
            availability=KnowledgeAvailability.ABSENT,
            mode=selected_mode,
            reason=KnowledgeReadReason.ABSENT,
            surface=load_result.surface,
            knowledge=None,
            manifest_basis=load_result.manifest_basis,
            freshness=None,
            counts=None,
            projection_findings=load_result.issues,
            load_state=load_result.status,
            underlying_load_state=load_result.underlying_status,
        )

    unsupported_reason = _unsupported_reason(load_result.issues)
    if (
        effective_state is KnowledgeLoadState.INVALID
        and unsupported_reason is not None
    ):
        availability = KnowledgeAvailability.UNSUPPORTED
        reason = unsupported_reason
    else:
        availability = KnowledgeAvailability.DEGRADED
        reason = (
            KnowledgeReadReason.DEGRADED_MIXED_SNAPSHOT
            if effective_state is KnowledgeLoadState.MIXED_SNAPSHOT
            else KnowledgeReadReason.DEGRADED_INVALID
        )

    return KnowledgeReadView(
        availability=availability,
        mode=selected_mode,
        reason=reason,
        surface=load_result.surface,
        knowledge=None,
        manifest_basis=None,
        freshness=None,
        counts=None,
        projection_findings=load_result.issues,
        load_state=load_result.status,
        underlying_load_state=load_result.underlying_status,
    )


def load_knowledge_read_view(
    wiki_dir: str | Path,
    *,
    live_evaluation: LiveKnowledgeEvaluation | None = None,
    snapshot_only: bool = False,
    mode: KnowledgeReadMode | str | None = None,
    markdown_pages: Mapping[str, str | bytes] | None = None,
    include_machine_verification: bool = False,
) -> KnowledgeReadView:
    """Load exactly once and return a read-only native-consumer session.

    Degraded policy is fixed at this boundary so a valid, page-current surface
    may remain usable without exposing failed knowledge.  Rebuild callbacks are
    deliberately not accepted.  Failures with no independently validated
    fallback surface continue to raise, except an explicitly classified future
    schema can be reported as ``unsupported`` without exposing any payload.
    """

    if not isinstance(include_machine_verification, bool):
        raise TypeError("include_machine_verification must be a boolean")
    try:
        result = load_knowledge_state(
            wiki_dir,
            policy=KnowledgeMismatchPolicy.DEGRADED,
            markdown_pages=markdown_pages,
        )
    except KnowledgeStateLoadError as exc:
        if (
            exc.status is not KnowledgeLoadState.INVALID
            or _unsupported_reason(exc.issues) is None
        ):
            raise
        result = KnowledgeLoadResult(
            status=exc.status,
            surface=None,
            knowledge=None,
            manifest_basis=None,
            issues=exc.issues,
        )
    view = build_knowledge_read_view(
        result,
        live_evaluation=live_evaluation,
        snapshot_only=snapshot_only,
        mode=mode,
    )
    if not include_machine_verification:
        return view

    # Local import keeps receipt evaluation downstream of the core read-view
    # model while making the fully evaluated view the only exporter input.
    from .knowledge_verification import attach_machine_verification_read_view

    return attach_machine_verification_read_view(wiki_dir, view)


def _read_mode(
    *,
    snapshot_only: bool,
    mode: KnowledgeReadMode | str | None,
) -> KnowledgeReadMode:
    if not isinstance(snapshot_only, bool):
        raise TypeError("snapshot_only must be a boolean")
    if mode is None:
        return (
            KnowledgeReadMode.SNAPSHOT_ONLY
            if snapshot_only
            else KnowledgeReadMode.EVALUATE_FRESHNESS
        )
    try:
        selected = (
            mode
            if isinstance(mode, KnowledgeReadMode)
            else KnowledgeReadMode(mode)
        )
    except (TypeError, ValueError) as exc:
        raise ValueError(
            "mode must be 'evaluate-freshness' or 'snapshot-only'"
        ) from exc
    if snapshot_only and selected is not KnowledgeReadMode.SNAPSHOT_ONLY:
        raise ValueError("snapshot_only conflicts with the requested mode")
    return selected


def _validate_load_result(result: KnowledgeLoadResult) -> None:
    if not isinstance(result.status, KnowledgeLoadState):
        raise TypeError("load_result.status must be a KnowledgeLoadState")
    if result.underlying_status is not None and not isinstance(
        result.underlying_status,
        KnowledgeLoadState,
    ):
        raise TypeError(
            "load_result.underlying_status must be a KnowledgeLoadState or None"
        )
    if not isinstance(result.issues, tuple) or any(
        not isinstance(issue, KnowledgeLoadIssue) for issue in result.issues
    ):
        raise TypeError("load_result.issues must be a tuple of KnowledgeLoadIssue")

    if result.status is KnowledgeLoadState.VALID:
        if (
            not isinstance(result.surface, Mapping)
            or not isinstance(result.knowledge, KnowledgeIndex)
            or not isinstance(result.manifest_basis, SyncManifest)
            or result.underlying_status is not None
        ):
            raise ValueError(
                "a valid load result must contain surface, knowledge, and manifest"
            )
        return

    if result.status is KnowledgeLoadState.ABSENT:
        if (
            not isinstance(result.surface, Mapping)
            or result.knowledge is not None
            or (
                result.manifest_basis is not None
                and not isinstance(result.manifest_basis, SyncManifest)
            )
            or result.underlying_status is not None
        ):
            raise ValueError(
                "an absent load result must contain only a validated surface"
            )
        return

    if result.status is KnowledgeLoadState.DEGRADED:
        if (
            not isinstance(result.surface, Mapping)
            or result.knowledge is not None
            or result.underlying_status
            not in {
                KnowledgeLoadState.INVALID,
                KnowledgeLoadState.MIXED_SNAPSHOT,
            }
        ):
            raise ValueError(
                "a degraded load result must contain a validated surface and cause"
            )
        return

    if (
        result.status is KnowledgeLoadState.INVALID
        and result.surface is None
        and _unsupported_reason(result.issues) is not None
    ):
        return
    raise ValueError(
        "invalid or mixed load results require loader-selected degraded fallback"
    )


def _unsupported_reason(
    issues: tuple[KnowledgeLoadIssue, ...],
) -> KnowledgeReadReason | None:
    for issue in issues:
        reason = _UNSUPPORTED_REASON_BY_ISSUE.get(issue.code)
        if reason is not None:
            return reason
    return None


def _knowledge_counts(
    knowledge: KnowledgeIndex,
    freshness: KnowledgeFreshnessReport | None,
) -> KnowledgeReadCounts:
    by_kind: Counter[str] = Counter()
    evidence: Counter[EvidenceState] = Counter()
    for concept in knowledge.concepts:
        raw_kind = concept.concept_kind
        kind = raw_kind.value if isinstance(raw_kind, Enum) else str(raw_kind)
        by_kind[kind] += 1
        evidence[concept.facets.structure.evidence] += 1

    complete_evidence = {
        state: evidence.get(state, 0) for state in EvidenceState
    }
    complete_freshness = (
        None
        if freshness is None
        else {state: freshness.counts[state] for state in ComputedFreshness}
    )
    return KnowledgeReadCounts(
        concepts_total=len(knowledge.concepts),
        concepts_by_kind=MappingProxyType(dict(sorted(by_kind.items()))),
        evidence_by_state=MappingProxyType(complete_evidence),
        freshness_by_state=(
            None
            if complete_freshness is None
            else MappingProxyType(complete_freshness)
        ),
    )


# Both names describe the same per-operation constructor.  ``load`` is the
# preferred spelling; ``open`` reads naturally at adapter call sites.
open_knowledge_read_view = load_knowledge_read_view


__all__ = [
    "KnowledgeAvailability",
    "MachineVerificationAvailability",
    "MachineVerificationReadView",
    "KnowledgeReadCounts",
    "KnowledgeReadMode",
    "KnowledgeReadReason",
    "KnowledgeReadView",
    "build_knowledge_read_view",
    "load_knowledge_read_view",
    "open_knowledge_read_view",
]
