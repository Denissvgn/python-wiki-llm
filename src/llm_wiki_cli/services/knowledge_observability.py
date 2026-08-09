"""Privacy-safe observability for native knowledge consumers.

This module is deliberately separate from the deterministic knowledge model.
It projects only closed status values, fixed aggregate counters, static
diagnostic guidance, and optional operational durations.  It never exposes
per-concept evidence, repository identity, hashes, paths, actors, remotes, or
timestamps.
"""

from __future__ import annotations

import time
from collections.abc import Mapping
from dataclasses import dataclass, replace
from pathlib import Path
from types import MappingProxyType
from typing import Any

from .knowledge_artifacts import KNOWLEDGE_INDEX_FILENAME
from .knowledge_consumption import (
    KnowledgeAvailability,
    KnowledgeReadReason,
    KnowledgeReadView,
    build_knowledge_read_view,
)
from .knowledge_freshness import (
    REASON_EXTRACTOR_CONFIGURATION_CHANGED,
    REASON_EXTRACTOR_CONFIGURATION_UNKNOWN,
    REASON_EXTRACTOR_LIMITATIONS_CHANGED,
    REASON_EXTRACTOR_SELECTION_CHANGED,
    REASON_EXTRACTOR_VERSION_CHANGED,
    REASON_GENERATION_OPTIONS_CHANGED,
    REASON_IDENTICAL_SOURCE_OBSERVATION_MISMATCH,
    REASON_LIVE_EXTRACTOR_UNAVAILABLE,
    REASON_OBSERVATION_SCOPE_CHANGED,
    REASON_PLUGIN_CONFIGURATION_CHANGED,
    REASON_PLUGIN_CONFIGURATION_UNKNOWN,
    REASON_PLUGIN_LIMITATIONS_CHANGED,
    REASON_PLUGIN_SET_CHANGED,
    REASON_PLUGIN_VERSION_CHANGED,
    REASON_SCHEMA_VERSION_CHANGED,
    REASON_SOURCE_MAPPING_CHANGED,
    REASON_TOOL_CONFIGURATION_CHANGED,
    REASON_TOOL_CONFIGURATION_UNKNOWN,
    REASON_TOOL_ID_CHANGED,
    REASON_TOOL_LIMITATIONS_CHANGED,
    REASON_TOOL_VERSION_CHANGED,
    REASON_VERSION_UNKNOWN,
)
from .knowledge_loader import (
    KnowledgeLoadIssue,
    KnowledgeLoadResult,
    KnowledgeMismatchPolicy,
    KnowledgeStateLoadError,
    load_knowledge_state,
)
from .knowledge_model import ComputedFreshness, EvidenceState, KnowledgeLoadState
from .source_selection import (
    SourceSelectionError,
    resolve_source_selection,
    source_selection_identity_from_generation_inputs,
    source_selection_inputs_from_generation_inputs,
    validate_persisted_source_selection_identity,
)
from .source_snapshot import build_source_snapshot, capture_source_selection_inputs
from .sync_manifest import SyncManifest
from .wiki_surface_index import SURFACE_INDEX_FILENAME, evaluate_surface_index

_EVIDENCE_ISSUE_STATES = (
    EvidenceState.MISSING,
    EvidenceState.INVALID,
    EvidenceState.UNKNOWN,
)
_UNSUPPORTED_ISSUE_CODES = {
    "knowledge-schema-version-unsupported",
    "manifest-version-unsupported",
    "surface-schema-version-unsupported",
}
_FRESHNESS_COUNT_KEYS = frozenset(state.value for state in ComputedFreshness)
_EVIDENCE_ISSUE_KEYS = frozenset(state.value for state in _EVIDENCE_ISSUE_STATES)
_PHASE_DURATION_KEYS = frozenset({"load", "evaluate", "check"})
_REASON_VALUES = frozenset(reason.value for reason in KnowledgeReadReason)
_DEGRADED_REASON_VALUES = frozenset(
    {
        KnowledgeReadReason.DEGRADED_INVALID.value,
        KnowledgeReadReason.DEGRADED_MIXED_SNAPSHOT.value,
    }
)
_UNSUPPORTED_REASON_VALUES = frozenset(
    {
        KnowledgeReadReason.KNOWLEDGE_SCHEMA_VERSION_UNSUPPORTED.value,
        KnowledgeReadReason.MANIFEST_VERSION_UNSUPPORTED.value,
        KnowledgeReadReason.SURFACE_SCHEMA_VERSION_UNSUPPORTED.value,
    }
)
UNEVALUATED_FRESHNESS_DISCLOSURE = "unevaluated (snapshot-only read)"
BASIS_INCOMPATIBLE_HINTS: Mapping[str, str] = MappingProxyType(
    {
        REASON_EXTRACTOR_CONFIGURATION_CHANGED: (
            "Restore the extractor configuration used at sync, or re-run sync "
            "with the current extractor configuration."
        ),
        REASON_EXTRACTOR_CONFIGURATION_UNKNOWN: (
            "Make the extractor configuration basis available and explicit, "
            "then re-run sync."
        ),
        REASON_EXTRACTOR_LIMITATIONS_CHANGED: (
            "Use an extractor with the limitations recorded at sync, or re-run "
            "sync after accepting the changed limitations."
        ),
        REASON_EXTRACTOR_SELECTION_CHANGED: (
            "Use the extractor selected at sync for this concept, or re-run sync "
            "after the intentional extractor change."
        ),
        REASON_EXTRACTOR_VERSION_CHANGED: (
            "Use the extractor version recorded at sync, or re-run sync with the "
            "installed extractor version."
        ),
        REASON_GENERATION_OPTIONS_CHANGED: (
            "Re-run with the generation options used at sync where supported "
            "(check --include-tests), or re-run sync with the intended current "
            "options."
        ),
        REASON_IDENTICAL_SOURCE_OBSERVATION_MISMATCH: (
            "Producer nondeterminism or artifact corruption is possible—re-run "
            "sync; if it persists, file a defect."
        ),
        REASON_SCHEMA_VERSION_CHANGED: (
            "Use the knowledge schema version recorded at sync, or re-run sync "
            "with the current llm-wiki version."
        ),
        REASON_LIVE_EXTRACTOR_UNAVAILABLE: (
            "Install or enable the extractor recorded for this concept, or re-run "
            "sync with an available extractor."
        ),
        REASON_OBSERVATION_SCOPE_CHANGED: (
            "Restore the module, entity, or infrastructure observation scope used "
            "at sync, or re-run sync after an intentional scope change."
        ),
        REASON_PLUGIN_CONFIGURATION_CHANGED: (
            "Restore the plugin configuration used at sync, or re-run sync with "
            "the current plugin configuration."
        ),
        REASON_PLUGIN_CONFIGURATION_UNKNOWN: (
            "Make every contributing plugin configuration basis available and "
            "explicit, then re-run sync."
        ),
        REASON_PLUGIN_LIMITATIONS_CHANGED: (
            "Restore the contributing plugin limitations recorded at sync, or "
            "re-run sync after accepting the change."
        ),
        REASON_PLUGIN_SET_CHANGED: (
            "Enable the plugin set used at sync, or re-run sync with the currently "
            "enabled plugin set."
        ),
        REASON_PLUGIN_VERSION_CHANGED: (
            "Use the contributing plugin versions recorded at sync, or re-run sync "
            "with the installed versions."
        ),
        REASON_TOOL_CONFIGURATION_CHANGED: (
            "Restore the producer configuration used at sync, or re-run sync with "
            "the current producer configuration."
        ),
        REASON_TOOL_CONFIGURATION_UNKNOWN: (
            "Make the producer configuration basis available and explicit, then "
            "re-run sync."
        ),
        REASON_TOOL_ID_CHANGED: (
            "Use the producer tool recorded at sync, or re-run sync with the "
            "current producer tool."
        ),
        REASON_TOOL_LIMITATIONS_CHANGED: (
            "Use a producer with the limitations recorded at sync, or re-run sync "
            "after accepting the changed limitations."
        ),
        REASON_TOOL_VERSION_CHANGED: (
            "Use the producer version recorded at sync, or re-run sync with the "
            "installed producer version."
        ),
        REASON_SOURCE_MAPPING_CHANGED: (
            "Restore this concept's recorded source mapping, or re-run sync to "
            "record the moved or remapped source."
        ),
        REASON_VERSION_UNKNOWN: (
            "Make concrete versions available for every contributing producer, "
            "extractor, and plugin, then re-run sync."
        ),
    }
)
BASIS_INCOMPATIBLE_REASON_CODES = frozenset(BASIS_INCOMPATIBLE_HINTS)


@dataclass(frozen=True)
class KnowledgePhaseDurations:
    """Operational phase durations in milliseconds.

    ``None`` means that a phase was not run.  In particular, snapshot-only
    status must not fabricate zero-duration evaluation or check phases.
    """

    load_ms: int | None = None
    evaluate_ms: int | None = None
    check_ms: int | None = None

    def __post_init__(self) -> None:
        for field_name, value in (
            ("load_ms", self.load_ms),
            ("evaluate_ms", self.evaluate_ms),
            ("check_ms", self.check_ms),
        ):
            if value is not None and (
                isinstance(value, bool) or not isinstance(value, int) or value < 0
            ):
                raise ValueError(f"{field_name} must be a non-negative integer or None")

    def to_payload(self) -> dict[str, int | None]:
        return {
            "load": self.load_ms,
            "evaluate": self.evaluate_ms,
            "check": self.check_ms,
        }


@dataclass(frozen=True)
class KnowledgeAggregateSummary:
    """Low-cardinality knowledge status safe for reports and local metrics."""

    availability: str
    reason: str
    concepts_evaluated: int
    freshness_counts: Mapping[str, int] | None
    evidence_issue_counts: Mapping[str, int] | None
    degraded_reason: str | None
    phase_durations_ms: Mapping[str, int | None]
    freshness_evaluated: bool

    def __post_init__(self) -> None:
        try:
            availability = KnowledgeAvailability(self.availability)
        except (TypeError, ValueError) as exc:
            raise ValueError(
                "availability must use the closed knowledge vocabulary"
            ) from exc
        if self.reason not in _REASON_VALUES:
            raise ValueError("reason must use the closed knowledge reason vocabulary")
        if isinstance(self.concepts_evaluated, bool) or not isinstance(
            self.concepts_evaluated,
            int,
        ):
            raise TypeError("concepts_evaluated must be a non-negative integer")
        if self.concepts_evaluated < 0:
            raise ValueError("concepts_evaluated must be a non-negative integer")
        if not isinstance(self.freshness_evaluated, bool):
            raise TypeError("freshness_evaluated must be a boolean")

        freshness_counts = _validated_counts(
            self.freshness_counts,
            expected_keys=_FRESHNESS_COUNT_KEYS,
            field_name="freshness_counts",
        )
        evidence_issue_counts = _validated_counts(
            self.evidence_issue_counts,
            expected_keys=_EVIDENCE_ISSUE_KEYS,
            field_name="evidence_issue_counts",
        )
        phase_durations = _validated_phase_durations(self.phase_durations_ms)
        if availability is KnowledgeAvailability.READY:
            if evidence_issue_counts is None:
                raise ValueError(
                    "ready summaries require aggregate evidence issue counts"
                )
        elif evidence_issue_counts is not None:
            raise ValueError("non-ready summaries cannot expose evidence issue counts")

        if self.freshness_evaluated:
            if availability is not KnowledgeAvailability.READY:
                raise ValueError("only ready knowledge can have evaluated freshness")
            if freshness_counts is None:
                raise ValueError(
                    "evaluated freshness requires complete freshness counts"
                )
            if self.concepts_evaluated != sum(freshness_counts.values()):
                raise ValueError(
                    "concepts_evaluated must equal the sum of freshness counts"
                )
        elif freshness_counts is not None or self.concepts_evaluated != 0:
            raise ValueError(
                "unevaluated freshness requires null counts and zero concepts"
            )

        expected_degraded_reason = (
            self.reason
            if availability
            in {KnowledgeAvailability.DEGRADED, KnowledgeAvailability.UNSUPPORTED}
            else None
        )
        if self.degraded_reason != expected_degraded_reason:
            raise ValueError(
                "degraded_reason must equal reason only for degraded or "
                "unsupported knowledge"
            )
        if (
            availability is KnowledgeAvailability.DEGRADED
            and self.reason not in _DEGRADED_REASON_VALUES
        ):
            raise ValueError("degraded availability requires a degraded reason")
        if (
            availability is KnowledgeAvailability.UNSUPPORTED
            and self.reason not in _UNSUPPORTED_REASON_VALUES
        ):
            raise ValueError("unsupported availability requires an unsupported reason")
        if (
            availability is KnowledgeAvailability.READY
            and self.reason != KnowledgeReadReason.READY.value
        ):
            raise ValueError("ready availability requires the ready reason")
        if (
            availability is KnowledgeAvailability.ABSENT
            and self.reason != KnowledgeReadReason.ABSENT.value
        ):
            raise ValueError("absent availability requires the absent reason")

        object.__setattr__(self, "freshness_counts", freshness_counts)
        object.__setattr__(self, "evidence_issue_counts", evidence_issue_counts)
        object.__setattr__(self, "phase_durations_ms", phase_durations)

    def to_payload(self) -> dict[str, object]:
        return {
            "availability": self.availability,
            "reason": self.reason,
            "freshness": self.freshness,
            "concepts_evaluated": self.concepts_evaluated,
            "freshness_counts": (
                None if self.freshness_counts is None else dict(self.freshness_counts)
            ),
            "evidence_issue_counts": (
                None
                if self.evidence_issue_counts is None
                else dict(self.evidence_issue_counts)
            ),
            "degraded_reason": self.degraded_reason,
            "phase_durations_ms": dict(self.phase_durations_ms),
            "freshness_evaluated": self.freshness_evaluated,
        }

    @property
    def freshness(self) -> str:
        """Return the required user-facing freshness disclosure."""

        return _freshness_disclosure(
            evaluated=self.freshness_evaluated,
            concepts_evaluated=self.concepts_evaluated,
        )


def _validated_counts(
    value: Mapping[str, int] | None,
    *,
    expected_keys: frozenset[str],
    field_name: str,
) -> Mapping[str, int] | None:
    if value is None:
        return None
    if not isinstance(value, Mapping) or frozenset(value) != expected_keys:
        raise ValueError(f"{field_name} must contain the complete closed key set")
    copied: dict[str, int] = {}
    for key in sorted(expected_keys):
        count = value[key]
        if isinstance(count, bool) or not isinstance(count, int) or count < 0:
            raise ValueError(f"{field_name}.{key} must be a non-negative integer")
        copied[key] = count
    return MappingProxyType(copied)


def _validated_phase_durations(
    value: Mapping[str, int | None],
) -> Mapping[str, int | None]:
    if not isinstance(value, Mapping) or frozenset(value) != _PHASE_DURATION_KEYS:
        raise ValueError("phase_durations_ms must contain load, evaluate, and check")
    durations = KnowledgePhaseDurations(
        load_ms=value["load"],
        evaluate_ms=value["evaluate"],
        check_ms=value["check"],
    )
    return MappingProxyType(durations.to_payload())


@dataclass(frozen=True)
class SnapshotKnowledgeObservability:
    """One snapshot-only read view and its aggregate operational summary."""

    view: KnowledgeReadView
    summary: KnowledgeAggregateSummary


def summarize_knowledge_view(
    view: KnowledgeReadView,
    *,
    durations: KnowledgePhaseDurations | None = None,
) -> KnowledgeAggregateSummary:
    """Project one read view into a fixed, evidence-free aggregate summary."""

    if not isinstance(view, KnowledgeReadView):
        raise TypeError("view must be a KnowledgeReadView")
    selected_durations = durations or KnowledgePhaseDurations()
    freshness_counts = (
        None
        if view.freshness is None
        else {state.value: int(count) for state, count in view.freshness.counts.items()}
    )
    concepts_evaluated = (
        0 if freshness_counts is None else sum(freshness_counts.values())
    )
    evidence_issue_counts = (
        None
        if view.counts is None
        else {
            state.value: int(view.counts.evidence_by_state.get(state, 0))
            for state in _EVIDENCE_ISSUE_STATES
        }
    )
    degraded_reason = (
        view.reason_code
        if view.availability
        in {KnowledgeAvailability.DEGRADED, KnowledgeAvailability.UNSUPPORTED}
        else None
    )
    return KnowledgeAggregateSummary(
        availability=view.availability.value,
        reason=view.reason_code,
        concepts_evaluated=concepts_evaluated,
        freshness_counts=freshness_counts,
        evidence_issue_counts=evidence_issue_counts,
        degraded_reason=degraded_reason,
        phase_durations_ms=selected_durations.to_payload(),
        freshness_evaluated=view.freshness_evaluated,
    )


def knowledge_freshness_disclosure(view: KnowledgeReadView) -> str:
    """Describe whether the read produced one freshness result per concept.

    An evaluated result can still report that no live comparison was
    performed; consumers must inspect each concept's reason and
    ``live_comparison_performed`` flag.
    """

    if not isinstance(view, KnowledgeReadView):
        raise TypeError("view must be a KnowledgeReadView")
    if not view.freshness_evaluated:
        return UNEVALUATED_FRESHNESS_DISCLOSURE
    assert view.freshness is not None
    return _freshness_disclosure(
        evaluated=True,
        concepts_evaluated=sum(int(count) for count in view.freshness.counts.values()),
    )


def knowledge_freshness_hint(
    state: ComputedFreshness | str | None,
    reason_code: object,
) -> str | None:
    """Return static recovery guidance for one incompatible freshness basis.

    The evaluator's reason vocabulary is closed.  Failing closed here ensures
    that a future incompatible reason cannot be presented without distinct
    actionable guidance.
    """

    state_value = state.value if isinstance(state, ComputedFreshness) else state
    if state_value != ComputedFreshness.BASIS_INCOMPATIBLE.value:
        return None
    if not isinstance(reason_code, str):
        raise ValueError(
            "basis-incompatible freshness requires a known actionable reason code"
        )
    try:
        return BASIS_INCOMPATIBLE_HINTS[reason_code]
    except KeyError as exc:
        raise ValueError(
            "basis-incompatible freshness requires a known actionable reason code"
        ) from exc


def _freshness_disclosure(
    *,
    evaluated: bool,
    concepts_evaluated: int,
) -> str:
    if not evaluated:
        return UNEVALUATED_FRESHNESS_DISCLOSURE
    return f"evaluated ({concepts_evaluated} concepts)"


def knowledge_status_payload(
    view: KnowledgeReadView | None,
) -> dict[str, object]:
    """Return the stable compact status envelope used by MCP and CLI status."""

    if view is None:
        return {
            "availability": KnowledgeAvailability.ABSENT.value,
            "reason": KnowledgeReadReason.ABSENT.value,
            "freshness": UNEVALUATED_FRESHNESS_DISCLOSURE,
            "freshness_evaluated": False,
        }
    if not isinstance(view, KnowledgeReadView):
        raise TypeError("view must be a KnowledgeReadView or None")
    return {
        "availability": view.availability.value,
        "reason": view.reason_code,
        "freshness": knowledge_freshness_disclosure(view),
        "freshness_evaluated": view.freshness_evaluated,
    }


def load_snapshot_knowledge_observability(
    wiki_dir: str | Path,
    *,
    src_dir: str | Path | None = None,
    source_selection: str | Path | None = None,
) -> SnapshotKnowledgeObservability:
    """Load status without extraction while checking current selection identity."""

    started = time.perf_counter()
    wiki_root = Path(wiki_dir)
    effective_src_dir: str | Path = "." if src_dir is None else src_dir
    source_snapshot = None
    if src_dir is not None or source_selection is not None:
        try:
            selection_policy = resolve_source_selection(
                effective_src_dir,
                source_selection,
            )
            selection_inputs = capture_source_selection_inputs(
                effective_src_dir,
                source_selection=source_selection,
                selection_policy=selection_policy,
            )
            manifest = SyncManifest.load(wiki_root)
            validate_persisted_source_selection_identity(
                manifest.generation_inputs,
                selection_policy.identity if selection_policy is not None else None,
                operation="knowledge status",
                live_selection_inputs=selection_inputs,
            )
            source_snapshot = build_source_snapshot(
                effective_src_dir,
                source_selection=source_selection,
                selection_policy=selection_policy,
                expected_selection_inputs=selection_inputs,
            )
        except FileNotFoundError:
            if selection_policy is not None:
                return _snapshot_result(_degraded_snapshot_view(), started)
        except (OSError, SourceSelectionError, TypeError, UnicodeError, ValueError):
            return _snapshot_result(_degraded_snapshot_view(), started)
    if not _knowledge_projection_declared(wiki_root):
        view = build_knowledge_read_view(
            KnowledgeLoadResult(
                status=KnowledgeLoadState.ABSENT,
                surface={},
                knowledge=None,
                manifest_basis=None,
            ),
            snapshot_only=True,
        )
        return _snapshot_result(view, started)

    try:
        surface_evaluation = evaluate_surface_index(
            wiki_root,
            {},
            src_dir=effective_src_dir,
            entry_points=(),
        )
    except (OSError, TypeError, UnicodeError, ValueError):
        return _snapshot_result(_degraded_snapshot_view(), started)

    try:
        load_result = load_knowledge_state(
            wiki_root,
            policy=KnowledgeMismatchPolicy.DEGRADED,
            markdown_pages=surface_evaluation.content_by_path,
        )
    except KnowledgeStateLoadError as exc:
        view = _snapshot_error_view(surface_evaluation.payload, exc)
    except (OSError, TypeError, UnicodeError, ValueError):
        view = _degraded_snapshot_view(surface_evaluation.payload)
    else:
        if source_snapshot is not None:
            load_result = _with_current_source_selection(
                load_result,
                source_snapshot.source_selection_identity,
                source_snapshot.source_selection_inputs,
            )
        view = build_knowledge_read_view(load_result, snapshot_only=True)
    return _snapshot_result(view, started)


def _with_current_source_selection(
    load_result: KnowledgeLoadResult,
    current_identity: Mapping[str, str] | None,
    current_inputs: Mapping[str, object] | None,
) -> KnowledgeLoadResult:
    manifest = load_result.manifest_basis
    if manifest is None or load_result.status is not KnowledgeLoadState.VALID:
        return load_result
    recorded = source_selection_identity_from_generation_inputs(
        manifest.generation_inputs
    )
    recorded_inputs = source_selection_inputs_from_generation_inputs(
        manifest.generation_inputs
    )
    if recorded == current_identity and recorded_inputs == current_inputs:
        return load_result
    issue = KnowledgeLoadIssue(
        code="source-selection-mismatch",
        artifact_path=".llm-wiki-manifest.json",
        field="generation_inputs.source_selection_inputs",
        message=(
            "Persisted knowledge was generated from a different source-selection "
            "boundary; re-run sync with the intended profile."
        ),
    )
    return replace(
        load_result,
        status=KnowledgeLoadState.DEGRADED,
        knowledge=None,
        issues=(*load_result.issues, issue),
        underlying_status=KnowledgeLoadState.MIXED_SNAPSHOT,
    )


def _snapshot_result(
    view: KnowledgeReadView,
    started: float,
) -> SnapshotKnowledgeObservability:
    elapsed_ms = max(0, round((time.perf_counter() - started) * 1000))
    return SnapshotKnowledgeObservability(
        view=view,
        summary=summarize_knowledge_view(
            view,
            durations=KnowledgePhaseDurations(load_ms=elapsed_ms),
        ),
    )


def _knowledge_projection_declared(wiki_root: Path) -> bool:
    if any(
        path.exists() or path.is_symlink()
        for path in (
            wiki_root / SURFACE_INDEX_FILENAME,
            wiki_root / KNOWLEDGE_INDEX_FILENAME,
        )
    ):
        return True
    try:
        manifest = SyncManifest.load(wiki_root)
    except (FileNotFoundError, OSError, UnicodeError, ValueError):
        return False
    return manifest.artifact_hashes is not None


def _snapshot_error_view(
    surface: Mapping[str, Any],
    error: KnowledgeStateLoadError,
) -> KnowledgeReadView:
    if any(issue.code in _UNSUPPORTED_ISSUE_CODES for issue in error.issues):
        load_result = KnowledgeLoadResult(
            status=KnowledgeLoadState.INVALID,
            surface=None,
            knowledge=None,
            manifest_basis=None,
            issues=error.issues,
        )
    else:
        load_result = KnowledgeLoadResult(
            status=KnowledgeLoadState.DEGRADED,
            surface=surface,
            knowledge=None,
            manifest_basis=None,
            issues=error.issues,
            underlying_status=error.status,
        )
    return build_knowledge_read_view(load_result, snapshot_only=True)


def _degraded_snapshot_view(
    surface: Mapping[str, Any] | None = None,
) -> KnowledgeReadView:
    issue = KnowledgeLoadIssue(
        code="knowledge-status-unavailable",
        artifact_path=KNOWLEDGE_INDEX_FILENAME,
        message="snapshot knowledge status could not be evaluated",
    )
    return build_knowledge_read_view(
        KnowledgeLoadResult(
            status=KnowledgeLoadState.DEGRADED,
            surface={} if surface is None else surface,
            knowledge=None,
            manifest_basis=None,
            issues=(issue,),
            underlying_status=KnowledgeLoadState.INVALID,
        ),
        snapshot_only=True,
    )


__all__ = [
    "BASIS_INCOMPATIBLE_HINTS",
    "BASIS_INCOMPATIBLE_REASON_CODES",
    "KnowledgeAggregateSummary",
    "KnowledgePhaseDurations",
    "SnapshotKnowledgeObservability",
    "UNEVALUATED_FRESHNESS_DISCLOSURE",
    "knowledge_freshness_disclosure",
    "knowledge_freshness_hint",
    "knowledge_status_payload",
    "load_snapshot_knowledge_observability",
    "summarize_knowledge_view",
]
