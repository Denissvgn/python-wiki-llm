"""One read-only knowledge session shared by native consumers.

The session loads and validates projection state once, then optionally computes
freshness once from an already collected :class:`LiveKnowledgeEvaluation`.
It never extracts source, walks a repository, repairs artifacts, or writes
state.  Callers should create one view per native operation and pass that view
to every downstream consumer participating in the operation.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Mapping
from dataclasses import dataclass
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
) -> KnowledgeReadView:
    """Load exactly once and return a read-only native-consumer session.

    Degraded policy is fixed at this boundary so a valid, page-current surface
    may remain usable without exposing failed knowledge.  Rebuild callbacks are
    deliberately not accepted.  Failures with no independently validated
    fallback surface continue to raise, except an explicitly classified future
    schema can be reported as ``unsupported`` without exposing any payload.
    """

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
    return build_knowledge_read_view(
        result,
        live_evaluation=live_evaluation,
        snapshot_only=snapshot_only,
        mode=mode,
    )


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
    "KnowledgeReadCounts",
    "KnowledgeReadMode",
    "KnowledgeReadReason",
    "KnowledgeReadView",
    "build_knowledge_read_view",
    "load_knowledge_read_view",
    "open_knowledge_read_view",
]
