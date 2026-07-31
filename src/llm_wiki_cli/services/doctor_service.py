"""Read-only composition for the repository knowledge health report.

The doctor does not define another analyzer. It composes the operation-scoped
knowledge read, freshness counts, drift diagnostics, governance checks, and
verification-receipt evaluation already produced by strict lint.
"""

from __future__ import annotations

import re
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from ..config import DEFAULT_WIKI_DIR, validate_path, validate_source_root
from .contracts import DOCTOR_SCHEMA_VERSION
from .extraction_jobs import ExtractionJobRequest
from .knowledge_consumption import (
    KnowledgeAvailability,
    KnowledgeReadView,
    MachineVerificationAvailability,
)
from .knowledge_governance import GOVERNANCE_EXTENSION_KEY, GOVERNANCE_FILENAME
from .knowledge_artifacts import KNOWLEDGE_INDEX_FILENAME
from .knowledge_model import ComputedFreshness, KnowledgeLoadState
from .knowledge_observability import (
    UNEVALUATED_FRESHNESS_DISCLOSURE,
    knowledge_freshness_disclosure,
)
from .lint_service import LintIssue, LintReport, build_report
from .sync_manifest import SyncManifest
from .verification_contracts import VERIFICATION_RECEIPT_FILENAME
from .wiki_surface_index import SURFACE_INDEX_FILENAME


class DoctorStatus(str, Enum):
    """Closed overall health vocabulary for the doctor contract."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    ABSENT = "absent"


DOCTOR_EXIT_CODES: Mapping[DoctorStatus, int] = {
    DoctorStatus.HEALTHY: 0,
    DoctorStatus.DEGRADED: 1,
    DoctorStatus.UNHEALTHY: 2,
    DoctorStatus.ABSENT: 3,
}

_REASON_RE = re.compile(r"\[reason=([a-z0-9-]+(?:,[a-z0-9-]+)*)\]")
_FRESHNESS_STATES = tuple(state.value for state in ComputedFreshness)
_CONFIRMED_STALE_STATES = frozenset(
    {
        ComputedFreshness.SOURCE_CHANGED.value,
        ComputedFreshness.SOURCE_MISSING.value,
    }
)
_INDETERMINATE_STATES = frozenset(
    {
        ComputedFreshness.UNKNOWN.value,
        ComputedFreshness.BASIS_INCOMPATIBLE.value,
    }
)
_VERIFICATION_UNHEALTHY_STATES = frozenset({"failed", "invalid", "stale"})


@dataclass(frozen=True)
class DoctorReport:
    """One stable machine report plus its process exit classification."""

    status: DoctorStatus
    strict: bool
    wiki_dir: str
    src_dir: str
    availability: Mapping[str, object]
    freshness: Mapping[str, object]
    snapshot_parity: Mapping[str, object]
    governance: Mapping[str, object]
    drift: Mapping[str, object]
    verification_receipt: Mapping[str, object]
    degraded_reasons: tuple[str, ...] = ()
    unhealthy_reasons: tuple[str, ...] = ()

    @property
    def exit_code(self) -> int:
        return DOCTOR_EXIT_CODES[self.status]

    def to_payload(self) -> dict[str, object]:
        return {
            "schema_version": DOCTOR_SCHEMA_VERSION,
            "status": self.status.value,
            "exit_code": self.exit_code,
            "strict": self.strict,
            "wiki_dir": self.wiki_dir,
            "src_dir": self.src_dir,
            "availability": dict(self.availability),
            "freshness": dict(self.freshness),
            "snapshot_parity": dict(self.snapshot_parity),
            "governance": dict(self.governance),
            "drift": dict(self.drift),
            "verification_receipt": dict(self.verification_receipt),
            "degraded_reasons": list(self.degraded_reasons),
            "unhealthy_reasons": list(self.unhealthy_reasons),
        }


def build_doctor_report(
    wiki_dir: str | Path = DEFAULT_WIKI_DIR,
    src_dir: str | Path = ".",
    *,
    strict: bool = False,
    allow_external_src: bool = False,
    helper_cache_dir: str | Path | None = None,
    include_tests: Iterable[str] | None = None,
    parallel_jobs: int = 1,
    job_request: ExtractionJobRequest | None = None,
) -> DoctorReport:
    """Build a doctor report by composing existing strict-lint results."""

    if not isinstance(strict, bool):
        raise TypeError("strict must be a boolean")
    if not isinstance(allow_external_src, bool):
        raise TypeError("allow_external_src must be a boolean")
    if isinstance(parallel_jobs, bool) or not isinstance(parallel_jobs, int):
        raise TypeError("parallel_jobs must be an integer")
    if parallel_jobs < 1:
        raise ValueError("parallel_jobs must be greater than zero")

    wiki_text = str(wiki_dir)
    source_text = str(src_dir)
    validate_path(wiki_text, "--wiki-dir")
    source_root = validate_source_root(
        source_text,
        "--src-dir",
        allow_external=allow_external_src,
    )
    effective_source = str(source_root) if allow_external_src else source_text
    lint = build_report(
        wiki_text,
        effective_source,
        strict=True,
        knowledge_drift_report=True,
        cache_options=None,
        parallel_jobs=parallel_jobs,
        helper_cache_dir=(
            None if helper_cache_dir is None else str(helper_cache_dir)
        ),
        include_tests=include_tests,
        job_request=job_request,
        plan_reporter=None,
        include_plugins=False,
    )
    return compose_doctor_report(
        lint,
        strict=strict,
        wiki_dir=wiki_text,
        src_dir=effective_source,
    )


def compose_doctor_report(
    lint: LintReport,
    *,
    strict: bool,
    wiki_dir: str,
    src_dir: str,
) -> DoctorReport:
    """Compose health sections from one already-computed lint operation."""

    if not isinstance(lint, LintReport):
        raise TypeError("lint must be a LintReport")
    if not isinstance(strict, bool):
        raise TypeError("strict must be a boolean")

    view = lint.knowledge_view
    wiki_root = Path(wiki_dir)
    availability = _availability_section(lint, view, wiki_root)
    freshness = _freshness_section(lint, view)
    snapshot = _snapshot_section(lint, view)
    governance = _governance_section(lint, view, wiki_root)
    drift = _drift_section(lint, freshness, view)
    verification = _verification_section(lint, view)
    status, degraded, unhealthy = _classify(
        strict=strict,
        availability=availability,
        freshness=freshness,
        snapshot=snapshot,
        governance=governance,
        drift=drift,
        verification=verification,
    )
    return DoctorReport(
        status=status,
        strict=strict,
        wiki_dir=wiki_dir,
        src_dir=src_dir,
        availability=availability,
        freshness=freshness,
        snapshot_parity=snapshot,
        governance=governance,
        drift=drift,
        verification_receipt=verification,
        degraded_reasons=degraded,
        unhealthy_reasons=unhealthy,
    )


def render_doctor_text(report: DoctorReport) -> str:
    """Render the report as a compact one-screen human summary."""

    payload = report.to_payload()
    availability = payload["availability"]
    freshness = payload["freshness"]
    snapshot = payload["snapshot_parity"]
    governance = payload["governance"]
    drift = payload["drift"]
    verification = payload["verification_receipt"]
    assert isinstance(availability, Mapping)
    assert isinstance(freshness, Mapping)
    assert isinstance(snapshot, Mapping)
    assert isinstance(governance, Mapping)
    assert isinstance(drift, Mapping)
    assert isinstance(verification, Mapping)

    freshness_counts = _format_counts(freshness["counts_by_state"])
    lines = [
        "LLM Wiki Doctor",
        f"Status:               {report.status.value} (exit {report.exit_code})",
        (
            "Availability:         "
            f"{availability['state']} ({availability['reason']})"
        ),
        f"Freshness:            {freshness['disclosure']}",
    ]
    if freshness_counts is not None:
        lines.append(f"  Counts:             {freshness_counts}")
    lines.extend(
        [
            (
                "Snapshot parity:     "
                f"{snapshot['state']} ({snapshot['issue_count']} issue(s))"
            ),
            (
                "Governance:          "
                f"{governance['state']} "
                f"(ledger={governance['ledger']}, "
                f"projection={governance['projection']}, "
                f"expired reviews={governance['expired_reviews']})"
            ),
            (
                "Drift:               "
                f"{drift['state']} "
                f"(confirmed={drift['confirmed_stale']}, "
                f"indeterminate={drift['indeterminate']}, "
                f"nonsemantic={drift['nonsemantic_changes']})"
            ),
            (
                "Verification receipt: "
                f"{verification['state']} ({verification['reason']})"
            ),
        ]
    )
    if report.unhealthy_reasons:
        lines.append("Unhealthy:            " + ", ".join(report.unhealthy_reasons))
    if report.degraded_reasons:
        lines.append("Degraded:             " + ", ".join(report.degraded_reasons))
    return "\n".join(lines) + "\n"


def _availability_section(
    lint: LintReport,
    view: KnowledgeReadView | None,
    wiki_root: Path,
) -> dict[str, object]:
    if view is not None:
        if (
            view.availability is KnowledgeAvailability.ABSENT
            and (lint.knowledge_enabled or _knowledge_declared(wiki_root))
        ):
            return {
                "state": KnowledgeAvailability.UNSUPPORTED.value,
                "reason": "knowledge-evaluation-unavailable",
                "usable": False,
            }
        return {
            "state": view.availability.value,
            "reason": view.reason_code,
            "usable": view.availability
            in {KnowledgeAvailability.READY, KnowledgeAvailability.DEGRADED},
        }
    if lint.knowledge_enabled or _knowledge_declared(wiki_root):
        return {
            "state": KnowledgeAvailability.UNSUPPORTED.value,
            "reason": "knowledge-evaluation-unavailable",
            "usable": False,
        }
    return {
        "state": KnowledgeAvailability.ABSENT.value,
        "reason": "knowledge-projection-not-present",
        "usable": False,
    }


def _knowledge_declared(wiki_root: Path) -> bool:
    for filename in (
        SURFACE_INDEX_FILENAME,
        KNOWLEDGE_INDEX_FILENAME,
        GOVERNANCE_FILENAME,
        VERIFICATION_RECEIPT_FILENAME,
    ):
        path = wiki_root / filename
        if path.exists() or path.is_symlink():
            return True
    try:
        manifest = SyncManifest.load(wiki_root)
    except (FileNotFoundError, OSError, UnicodeError, ValueError):
        return False
    return manifest.artifact_hashes is not None


def _freshness_section(
    lint: LintReport,
    view: KnowledgeReadView | None,
) -> dict[str, object]:
    summary = lint.knowledge_summary
    if summary is not None:
        counts = (
            None
            if summary.freshness_counts is None
            else {
                state: int(summary.freshness_counts[state])
                for state in _FRESHNESS_STATES
            }
        )
        return {
            "evaluated": summary.freshness_evaluated,
            "disclosure": summary.freshness,
            "concepts": summary.concepts_evaluated,
            "counts_by_state": counts,
        }
    if view is not None and view.freshness is not None:
        counts = {
            state.value: int(view.freshness.counts[state])
            for state in ComputedFreshness
        }
        return {
            "evaluated": True,
            "disclosure": knowledge_freshness_disclosure(view),
            "concepts": sum(counts.values()),
            "counts_by_state": counts,
        }
    return {
        "evaluated": False,
        "disclosure": UNEVALUATED_FRESHNESS_DISCLOSURE,
        "concepts": 0,
        "counts_by_state": None,
    }


def _snapshot_section(
    lint: LintReport,
    view: KnowledgeReadView | None,
) -> dict[str, object]:
    del lint
    if view is None:
        return {
            "state": "not-available",
            "issue_count": 0,
            "reasons": [],
        }
    reasons = sorted({issue.code for issue in view.projection_findings})
    underlying = view.underlying_load_state
    if underlying is KnowledgeLoadState.MIXED_SNAPSHOT:
        state = "mixed"
    elif view.availability is KnowledgeAvailability.READY:
        state = "valid"
    elif view.availability is KnowledgeAvailability.ABSENT:
        state = "not-available"
    else:
        state = "invalid"
    return {
        "state": state,
        "issue_count": len(view.projection_findings),
        "reasons": reasons,
    }


def _governance_section(
    lint: LintReport,
    view: KnowledgeReadView | None,
    wiki_root: Path,
) -> dict[str, object]:
    issues = _issues(lint, "knowledge_governance")
    reasons = _reasons(issues)
    expired_reviews = len(_issues(lint, "knowledge_review"))
    ledger_path = wiki_root / GOVERNANCE_FILENAME
    ledger_present = ledger_path.exists() or ledger_path.is_symlink()
    projection_present = bool(
        view is not None
        and view.knowledge is not None
        and GOVERNANCE_EXTENSION_KEY in view.knowledge.extensions
    )
    if issues:
        state = "invalid"
    elif view is None and lint.knowledge_enabled:
        state = "not-available"
    elif ledger_present or projection_present:
        state = "valid"
    else:
        state = "not-present"
    if state == "invalid":
        ledger = "invalid" if ledger_present else "not-present"
        projection = "invalid" if projection_present else "not-available"
    else:
        ledger = "valid" if ledger_present else "not-present"
        projection = "valid" if projection_present else "not-present"
    return {
        "state": state,
        "ledger": ledger,
        "projection": projection,
        "expired_reviews": expired_reviews,
        "issue_count": len(issues),
        "reasons": reasons,
    }


def _drift_section(
    lint: LintReport,
    freshness: Mapping[str, object],
    view: KnowledgeReadView | None,
) -> dict[str, object]:
    raw_counts = freshness["counts_by_state"]
    counts: dict[str, int] | None = None
    if raw_counts is not None:
        if not isinstance(raw_counts, Mapping):
            raise TypeError("freshness counts_by_state must be a mapping")
        counts = {}
        for state in _FRESHNESS_STATES:
            value = raw_counts[state]
            if isinstance(value, bool) or not isinstance(value, int):
                raise TypeError("freshness state counts must be integers")
            counts[state] = value
    diagnostics = _issues(lint, "knowledge_freshness", diagnostics=True)
    diagnostic_states = _diagnostic_freshness_states(diagnostics, view)
    confirmed = (
        0
        if counts is None
        else sum(counts[state] for state in _CONFIRMED_STALE_STATES)
    )
    indeterminate = sum(
        state in _INDETERMINATE_STATES for state in diagnostic_states
    )
    nonsemantic = diagnostic_states.count(
        ComputedFreshness.NONSEMANTIC_SOURCE_CHANGE.value
    )
    if counts is None:
        state = "not-evaluated"
    elif confirmed:
        state = "stale-confirmed"
    elif indeterminate:
        state = "indeterminate"
    elif nonsemantic:
        state = "nonsemantic-change"
    else:
        state = "current"
    return {
        "state": state,
        "confirmed_stale": confirmed,
        "indeterminate": indeterminate,
        "nonsemantic_changes": nonsemantic,
        "counts_by_state": counts,
        "diagnostic_count": len(diagnostics),
        "reasons": _diagnostic_reasons(diagnostics),
    }


def _diagnostic_freshness_states(
    diagnostics: Iterable[LintIssue],
    view: KnowledgeReadView | None,
) -> list[str]:
    if view is None or view.freshness is None:
        return []
    states: list[str] = []
    for issue in diagnostics:
        if issue.reason_code == "freshness-result-missing":
            states.append(ComputedFreshness.UNKNOWN.value)
            continue
        if issue.target is None:
            continue
        result = view.freshness.by_locator.get(issue.target)
        if result is not None:
            states.append(result.state.value)
    return states


def _diagnostic_reasons(issues: Iterable[LintIssue]) -> list[str]:
    values = list(issues)
    reasons = sorted(
        {
            issue.reason_code
            for issue in values
            if issue.reason_code is not None
        }
    )
    return reasons or (["unspecified"] if values else [])


def _verification_section(
    lint: LintReport,
    view: KnowledgeReadView | None,
) -> dict[str, object]:
    issues = _issues(lint, "knowledge_verification")
    reasons = _reasons(issues)
    if view is None:
        if issues:
            return {
                "state": "invalid",
                "reason": reasons[0],
                "recorded_result": None,
                "passed": None,
            }
        return {
            "state": "not-evaluated" if lint.knowledge_enabled else "absent",
            "reason": (
                "verification-basis-unavailable"
                if lint.knowledge_enabled
                else "verification-receipt-not-present"
            ),
            "recorded_result": None,
            "passed": None,
        }
    receipt = view.machine_verification
    if receipt.availability is MachineVerificationAvailability.INVALID:
        state = "invalid"
    elif receipt.availability in {
        MachineVerificationAvailability.ABSENT,
        MachineVerificationAvailability.NOT_EVALUATED,
    }:
        state = (
            "absent"
            if receipt.availability is MachineVerificationAvailability.ABSENT
            else "not-evaluated"
        )
    elif receipt.valid is False:
        state = "stale"
    elif receipt.recorded_result == "failed":
        state = "failed"
    else:
        state = "valid"
    if issues and state not in _VERIFICATION_UNHEALTHY_STATES:
        state = "invalid"
    return {
        "state": state,
        "reason": reasons[0] if reasons else receipt.reason,
        "recorded_result": receipt.recorded_result,
        "passed": receipt.passed,
    }


def _classify(
    *,
    strict: bool,
    availability: Mapping[str, object],
    freshness: Mapping[str, object],
    snapshot: Mapping[str, object],
    governance: Mapping[str, object],
    drift: Mapping[str, object],
    verification: Mapping[str, object],
) -> tuple[DoctorStatus, tuple[str, ...], tuple[str, ...]]:
    availability_state = availability["state"]
    if availability_state == KnowledgeAvailability.ABSENT.value:
        return DoctorStatus.ABSENT, (), ()

    unhealthy: list[str] = []
    degraded: list[str] = []
    if availability_state == KnowledgeAvailability.UNSUPPORTED.value:
        unhealthy.append("knowledge-unsupported")
    elif availability_state == KnowledgeAvailability.DEGRADED.value:
        degraded.append("knowledge-degraded")
    if snapshot["state"] == "mixed":
        unhealthy.append("mixed-snapshot")
    if governance["state"] == "invalid":
        unhealthy.append("invalid-governance")
    if drift["state"] == "stale-confirmed":
        unhealthy.append("stale-confirmed")
    elif drift["state"] == "indeterminate":
        (
            unhealthy if strict else degraded
        ).append("freshness-indeterminate")
    elif drift["state"] == "nonsemantic-change":
        (
            unhealthy if strict else degraded
        ).append("nonsemantic-source-change")
    if not freshness["evaluated"]:
        degraded.append("freshness-unevaluated")
    expired_reviews = governance["expired_reviews"]
    if isinstance(expired_reviews, bool) or not isinstance(expired_reviews, int):
        raise TypeError("governance expired_reviews must be an integer")
    if expired_reviews > 0:
        degraded.append("expired-reviews")
    if verification["state"] in _VERIFICATION_UNHEALTHY_STATES:
        unhealthy.append(f"verification-{verification['state']}")

    unhealthy_reasons = tuple(dict.fromkeys(unhealthy))
    degraded_reasons = tuple(dict.fromkeys(degraded))
    if unhealthy_reasons:
        return DoctorStatus.UNHEALTHY, degraded_reasons, unhealthy_reasons
    if degraded_reasons:
        return DoctorStatus.DEGRADED, degraded_reasons, ()
    return DoctorStatus.HEALTHY, (), ()


def _issues(
    lint: LintReport,
    category: str,
    *,
    diagnostics: bool = False,
) -> list[LintIssue]:
    values = lint.diagnostics if diagnostics else lint.issues
    return [issue for issue in values if issue.category == category]


def _reasons(issues: Iterable[LintIssue]) -> list[str]:
    reasons: set[str] = set()
    observed = False
    for issue in issues:
        observed = True
        if issue.reason_code is not None:
            reasons.add(issue.reason_code)
        for match in _REASON_RE.findall(issue.message):
            reasons.update(match.split(","))
    if reasons:
        return sorted(reasons)
    return ["unspecified"] if observed else []


def _format_counts(value: object) -> str | None:
    if not isinstance(value, Mapping):
        return None
    return ", ".join(f"{state}={value[state]}" for state in _FRESHNESS_STATES)


__all__ = [
    "DOCTOR_EXIT_CODES",
    "DoctorReport",
    "DoctorStatus",
    "build_doctor_report",
    "compose_doctor_report",
    "render_doctor_text",
]
