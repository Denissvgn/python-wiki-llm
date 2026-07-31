"""Deterministic review-ledger and adjustment-loop contracts.

The service consumes already-produced checker or agent-review records.  It does
not run commands, touch the filesystem, or advance a documentation run.  A
caller can therefore persist the returned ledger and make the lifecycle change
only after independently reconciling it with the run and workspace evidence.

Finding identity deliberately excludes prose, severity, evidence ordering, and
path ordering.  Rewording a diagnostic or presenting its affected paths in a
different order must not reset its occurrence counter.
"""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Iterable as IterableABC
from dataclasses import asdict, dataclass, is_dataclass, replace
from typing import Any, Iterable, Mapping, Sequence

from .validation import (
    coerce_nonnegative_int,
    coerce_positive_int,
    coerce_trimmed_text,
    normalize_observational_posix_path,
    require_bool as require_shared_bool,
    require_choice as require_shared_choice,
    require_exact_fields as require_shared_exact_fields,
    require_mapping as require_shared_mapping,
    require_nonempty_text,
    require_nonnegative_int as require_shared_nonnegative_int,
    require_positive_int as require_shared_positive_int,
    require_string,
    require_trimmed_text_list,
)


DOCUMENTATION_REVIEW_LEDGER_SCHEMA_VERSION = "llm-wiki-documentation-review-ledger/v1"

SUPPORTED_REVIEW_SOURCES = frozenset(
    {"lint", "ci-check", "site", "built-site", "media", "agent-review"}
)
SUPPORTED_FINDING_SEVERITIES = frozenset({"low", "medium", "high"})
SUPPORTED_FINDING_STATUSES = frozenset({"open", "resolved", "deferred", "superseded"})
TERMINAL_FINDING_STATUSES = frozenset({"resolved", "deferred", "superseded"})
SUPPORTED_PACKET_ROLES = frozenset({"worker", "reviewer", "supervisor"})
SUPPORTED_LEDGER_STATES = frozenset(
    {
        "pending",
        "adjustment_required",
        "awaiting_supervisor",
        "blocked",
        "publish_ready",
    }
)

_SOURCE_ALIASES = {
    "lint": "lint",
    "ci": "ci-check",
    "ci-check": "ci-check",
    "ci_check": "ci-check",
    "site": "site",
    "built-site": "built-site",
    "built_site": "built-site",
    "media": "media",
    "agent-review": "agent-review",
    "agent_review": "agent-review",
    "review": "agent-review",
}
_SEVERITY_ALIASES = {
    "debug": "low",
    "info": "low",
    "informational": "low",
    "notice": "low",
    "low": "low",
    "warn": "medium",
    "warning": "medium",
    "medium": "medium",
    "moderate": "medium",
    "error": "high",
    "failure": "high",
    "failed": "high",
    "fatal": "high",
    "high": "high",
    "critical": "high",
    "blocker": "high",
}
_SEVERITY_ORDER = {"low": 0, "medium": 1, "high": 2}
_STATUS_ALIASES = {
    "new": "open",
    "open": "open",
    "pending": "open",
    "unresolved": "open",
    "valid": "open",
    "failing": "open",
    "failed": "open",
    "closed": "resolved",
    "fixed": "resolved",
    "passed": "resolved",
    "resolved": "resolved",
    "deferred": "deferred",
    "needs-human-confirmation": "deferred",
    "needs_human_confirmation": "deferred",
    "out-of-scope": "deferred",
    "out_of_scope": "deferred",
    "waived": "deferred",
    "duplicate": "superseded",
    "false-positive": "superseded",
    "false_positive": "superseded",
    "superseded": "superseded",
}
_CATEGORY_RE = re.compile(r"[^a-z0-9_.:-]+")

_FINDING_FIELDS = frozenset(
    {
        "id",
        "category",
        "severity",
        "source",
        "status",
        "evidence",
        "rationale",
        "first_seen",
        "last_seen",
        "occurrence_count",
        "paths",
        "targets",
        "external_ids",
    }
)
_PACKET_FIELDS = frozenset(
    {
        "packet_id",
        "role",
        "actor_id",
        "iteration",
        "packet_hash",
        "result_hash",
        "recorded_at",
        "evidence",
    }
)
_RECONCILIATION_FIELDS = frozenset(
    {
        "packet",
        "approved",
        "rationale",
        "reviewed_finding_ids",
        "evidence",
        "reconciled_at",
    }
)
_LEDGER_FIELDS = frozenset(
    {
        "schema_version",
        "run_id",
        "state",
        "publish_ready",
        "loop_count",
        "max_loops",
        "findings",
        "packets",
        "supervisor_reconciliations",
    }
)
_PACKET_COLLECTION_FIELDS = frozenset({"worker", "reviewer"})


class DocumentationReviewError(ValueError):
    """Raised when review evidence cannot satisfy the ledger contract."""


@dataclass(frozen=True)
class DocumentationReviewFinding:
    """One stable finding accumulated across review iterations."""

    finding_id: str
    category: str
    severity: str
    source: str
    status: str
    evidence: tuple[str, ...]
    rationale: str
    first_seen: str
    last_seen: str
    occurrence_count: int
    paths: tuple[str, ...] = ()
    targets: tuple[str, ...] = ()
    external_ids: tuple[str, ...] = ()

    @property
    def terminal(self) -> bool:
        # High-severity correctness and safety findings require an affirmative
        # resolution. Deferral and supersession remain recorded dispositions,
        # but they must not make a high finding publish-ready.
        if self.severity == "high":
            return self.status == "resolved"
        return self.status in TERMINAL_FINDING_STATUSES

    @property
    def unresolved(self) -> bool:
        return not self.terminal

    def to_dict(self) -> dict[str, Any]:
        """Return a deterministic JSON-compatible finding."""
        return {
            "id": self.finding_id,
            "category": self.category,
            "severity": self.severity,
            "source": self.source,
            "status": self.status,
            "evidence": list(self.evidence),
            "rationale": self.rationale,
            "first_seen": self.first_seen,
            "last_seen": self.last_seen,
            "occurrence_count": self.occurrence_count,
            "paths": list(self.paths),
            "targets": list(self.targets),
            "external_ids": list(self.external_ids),
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "DocumentationReviewFinding":
        _require_exact_fields(payload, _FINDING_FIELDS, "review finding")
        finding = cls(
            finding_id=_required_json_text(payload["id"], "finding id"),
            category=_required_json_text(payload["category"], "finding category"),
            severity=_required_enum(
                payload["severity"], SUPPORTED_FINDING_SEVERITIES, "finding severity"
            ),
            source=_required_enum(
                payload["source"], SUPPORTED_REVIEW_SOURCES, "review finding source"
            ),
            status=_required_enum(
                payload["status"], SUPPORTED_FINDING_STATUSES, "finding status"
            ),
            evidence=_required_string_list(payload["evidence"], "finding evidence"),
            rationale=_required_json_string(payload["rationale"], "finding rationale"),
            first_seen=_required_json_text(payload["first_seen"], "first_seen"),
            last_seen=_required_json_text(payload["last_seen"], "last_seen"),
            occurrence_count=_required_positive_int(
                payload["occurrence_count"], "occurrence_count"
            ),
            paths=_required_string_list(payload["paths"], "finding paths"),
            targets=_required_string_list(payload["targets"], "finding targets"),
            external_ids=_required_string_list(
                payload["external_ids"], "finding external_ids"
            ),
        )
        _validate_finding(finding)
        return finding


@dataclass(frozen=True)
class DocumentationReviewPacket:
    """Auditable reference to one role-specific packet and result."""

    packet_id: str
    role: str
    actor_id: str
    iteration: int
    packet_hash: str
    result_hash: str
    recorded_at: str
    evidence: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.role not in SUPPORTED_PACKET_ROLES:
            raise DocumentationReviewError(
                f"Unsupported documentation-review packet role: {self.role!r}"
            )
        _required_text(self.packet_id, "packet_id")
        _required_text(self.actor_id, "actor_id")
        _positive_int(self.iteration, "packet iteration")
        _required_text(self.packet_hash, "packet_hash")
        _required_text(self.result_hash, "result_hash")
        _required_text(self.recorded_at, "packet recorded_at")

    def to_dict(self) -> dict[str, Any]:
        return {
            "packet_id": self.packet_id,
            "role": self.role,
            "actor_id": self.actor_id,
            "iteration": self.iteration,
            "packet_hash": self.packet_hash,
            "result_hash": self.result_hash,
            "recorded_at": self.recorded_at,
            "evidence": list(sorted(set(self.evidence))),
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "DocumentationReviewPacket":
        _require_exact_fields(payload, _PACKET_FIELDS, "review packet")
        return cls(
            packet_id=_required_json_text(payload["packet_id"], "packet_id"),
            role=_required_enum(payload["role"], SUPPORTED_PACKET_ROLES, "packet role"),
            actor_id=_required_json_text(payload["actor_id"], "actor_id"),
            iteration=_required_positive_int(payload["iteration"], "packet iteration"),
            packet_hash=_required_json_text(payload["packet_hash"], "packet_hash"),
            result_hash=_required_json_text(payload["result_hash"], "result_hash"),
            recorded_at=_required_json_text(
                payload["recorded_at"], "packet recorded_at"
            ),
            evidence=_required_string_list(payload["evidence"], "packet evidence"),
        )


@dataclass(frozen=True)
class SupervisorReconciliation:
    """Independent supervisor disposition for a clean review ledger."""

    packet: DocumentationReviewPacket
    approved: bool
    rationale: str
    reviewed_finding_ids: tuple[str, ...]
    evidence: tuple[str, ...]
    reconciled_at: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "packet": self.packet.to_dict(),
            "approved": self.approved,
            "rationale": self.rationale,
            "reviewed_finding_ids": list(self.reviewed_finding_ids),
            "evidence": list(self.evidence),
            "reconciled_at": self.reconciled_at,
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "SupervisorReconciliation":
        _require_exact_fields(
            payload, _RECONCILIATION_FIELDS, "supervisor reconciliation"
        )
        packet_payload = payload["packet"]
        if not isinstance(packet_payload, Mapping):
            raise DocumentationReviewError(
                "Supervisor reconciliation packet must be an object."
            )
        return cls(
            packet=DocumentationReviewPacket.from_dict(packet_payload),
            approved=_required_bool(payload["approved"], "approved"),
            rationale=_required_json_text(
                payload["rationale"], "supervisor reconciliation rationale"
            ),
            reviewed_finding_ids=_required_string_list(
                payload["reviewed_finding_ids"], "reviewed_finding_ids"
            ),
            evidence=_required_string_list(
                payload["evidence"], "supervisor reconciliation evidence"
            ),
            reconciled_at=_required_json_text(
                payload["reconciled_at"], "reconciled_at"
            ),
        )


@dataclass(frozen=True)
class DocumentationReviewLedger:
    """Versioned, JSON-friendly state for the bounded review loop."""

    run_id: str
    max_loops: int
    loop_count: int = 0
    state: str = "pending"
    findings: tuple[DocumentationReviewFinding, ...] = ()
    worker_packets: tuple[DocumentationReviewPacket, ...] = ()
    reviewer_packets: tuple[DocumentationReviewPacket, ...] = ()
    supervisor_reconciliations: tuple[SupervisorReconciliation, ...] = ()
    schema_version: str = DOCUMENTATION_REVIEW_LEDGER_SCHEMA_VERSION

    @property
    def publish_ready(self) -> bool:
        return self.state == "publish_ready"

    @property
    def unresolved_findings(self) -> tuple[DocumentationReviewFinding, ...]:
        return tuple(finding for finding in self.findings if finding.unresolved)

    def to_dict(self) -> dict[str, Any]:
        findings = tuple(sorted(self.findings, key=lambda item: item.finding_id))
        workers = tuple(
            sorted(
                self.worker_packets, key=lambda item: (item.iteration, item.packet_id)
            )
        )
        reviewers = tuple(
            sorted(
                self.reviewer_packets,
                key=lambda item: (item.iteration, item.packet_id),
            )
        )
        return {
            "schema_version": self.schema_version,
            "run_id": self.run_id,
            "state": self.state,
            "publish_ready": self.publish_ready,
            "loop_count": self.loop_count,
            "max_loops": self.max_loops,
            "findings": [finding.to_dict() for finding in findings],
            "packets": {
                "worker": [packet.to_dict() for packet in workers],
                "reviewer": [packet.to_dict() for packet in reviewers],
            },
            "supervisor_reconciliations": [
                reconciliation.to_dict()
                for reconciliation in self.supervisor_reconciliations
            ],
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, sort_keys=True) + "\n"

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "DocumentationReviewLedger":
        _require_exact_fields(payload, _LEDGER_FIELDS, "review ledger")
        if payload.get("schema_version") != DOCUMENTATION_REVIEW_LEDGER_SCHEMA_VERSION:
            raise DocumentationReviewError(
                "Unsupported documentation review-ledger schema_version."
            )
        publish_ready = _required_bool(payload["publish_ready"], "publish_ready")
        state = _required_enum(
            payload["state"], SUPPORTED_LEDGER_STATES, "ledger state"
        )
        if publish_ready != (state == "publish_ready"):
            raise DocumentationReviewError(
                "Review-ledger publish_ready must equal the derived ledger state."
            )
        packets = payload["packets"]
        if not isinstance(packets, Mapping):
            raise DocumentationReviewError("Review-ledger packets must be an object.")
        _require_exact_fields(packets, _PACKET_COLLECTION_FIELDS, "packet collection")
        worker_payloads = packets["worker"]
        reviewer_payloads = packets["reviewer"]
        finding_payloads = payload["findings"]
        reconciliation_payloads = payload["supervisor_reconciliations"]
        for label, values in (
            ("findings", finding_payloads),
            ("worker packets", worker_payloads),
            ("reviewer packets", reviewer_payloads),
            ("supervisor reconciliations", reconciliation_payloads),
        ):
            if not isinstance(values, list):
                raise DocumentationReviewError(f"Review-ledger {label} must be a list.")
        ledger = cls(
            run_id=_required_json_text(payload["run_id"], "run_id"),
            max_loops=_required_positive_int(payload["max_loops"], "max_loops"),
            loop_count=_required_non_negative_int(payload["loop_count"], "loop_count"),
            state=state,
            findings=tuple(
                DocumentationReviewFinding.from_dict(_require_mapping(item, "finding"))
                for item in finding_payloads
            ),
            worker_packets=tuple(
                DocumentationReviewPacket.from_dict(
                    _require_mapping(item, "worker packet")
                )
                for item in worker_payloads
            ),
            reviewer_packets=tuple(
                DocumentationReviewPacket.from_dict(
                    _require_mapping(item, "reviewer packet")
                )
                for item in reviewer_payloads
            ),
            supervisor_reconciliations=tuple(
                SupervisorReconciliation.from_dict(
                    _require_mapping(item, "supervisor reconciliation")
                )
                for item in reconciliation_payloads
            ),
            schema_version=_required_json_text(
                payload["schema_version"], "schema_version"
            ),
        )
        _validate_ledger(ledger)
        return ledger


@dataclass(frozen=True)
class ReviewLoopDecision:
    """Controller instruction returned without mutating lifecycle state."""

    action: str
    blocked: bool
    can_continue: bool
    requires_supervisor_reconciliation: bool
    publish_ready: bool
    finding_ids: tuple[str, ...]
    rationale: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "action": self.action,
            "blocked": self.blocked,
            "can_continue": self.can_continue,
            "requires_supervisor_reconciliation": (
                self.requires_supervisor_reconciliation
            ),
            "publish_ready": self.publish_ready,
            "finding_ids": list(self.finding_ids),
            "rationale": self.rationale,
        }


@dataclass(frozen=True)
class ReviewLoopResult:
    ledger: DocumentationReviewLedger
    decision: ReviewLoopDecision

    def to_dict(self) -> dict[str, Any]:
        return {
            "ledger": self.ledger.to_dict(),
            "decision": self.decision.to_dict(),
        }


def create_review_ledger(
    run_id: str, *, max_loops: int = 3
) -> DocumentationReviewLedger:
    """Create an empty bounded ledger without reading or writing run state."""
    return DocumentationReviewLedger(
        run_id=_required_text(run_id, "run_id"),
        max_loops=_positive_int(max_loops, "max_loops"),
    )


def normalize_review_records(
    source: str,
    records: object,
    *,
    observed_at: str,
) -> tuple[DocumentationReviewFinding, ...]:
    """Normalize one checker/reviewer result set into stable findings."""
    canonical_source = _normalise_source(source)
    timestamp = _required_text(observed_at, "observed_at")
    by_id: dict[str, DocumentationReviewFinding] = {}
    for record in _iter_review_records(records):
        finding = _normalise_record(canonical_source, record, timestamp)
        previous = by_id.get(finding.finding_id)
        by_id[finding.finding_id] = (
            finding if previous is None else _combine_same_iteration(previous, finding)
        )
    return tuple(by_id[key] for key in sorted(by_id))


def normalize_review_findings(
    records_by_source: Mapping[str, object],
    *,
    observed_at: str,
) -> tuple[DocumentationReviewFinding, ...]:
    """Normalize all supported result sources into one deterministic tuple."""
    combined: dict[str, DocumentationReviewFinding] = {}
    ordered_sources = sorted(
        records_by_source,
        key=lambda source: (_normalise_source(source), str(source)),
    )
    for source in ordered_sources:
        for finding in normalize_review_records(
            source, records_by_source[source], observed_at=observed_at
        ):
            previous = combined.get(finding.finding_id)
            combined[finding.finding_id] = (
                finding
                if previous is None
                else _combine_same_iteration(previous, finding)
            )
    return tuple(combined[key] for key in sorted(combined))


def apply_review_loop(
    ledger: DocumentationReviewLedger,
    records_by_source: Mapping[str, object],
    *,
    observed_at: str,
    worker_packet: DocumentationReviewPacket,
    reviewer_packet: DocumentationReviewPacket,
) -> ReviewLoopResult:
    """Merge one review pass and return the bounded controller decision.

    Missing observations do not close an existing finding.  Closure requires a
    new observation with the same stable identity, a terminal status, and a
    non-empty rationale.
    """
    _validate_ledger(ledger)
    if ledger.state in {"blocked", "publish_ready"}:
        return ReviewLoopResult(ledger=ledger, decision=_decision_for_ledger(ledger))
    preview_observations: tuple[DocumentationReviewFinding, ...] | None = None
    if ledger.state == "awaiting_supervisor":
        preview_observations = normalize_review_findings(
            records_by_source, observed_at=observed_at
        )
        if not preview_observations:
            return ReviewLoopResult(
                ledger=ledger,
                decision=_decision_for_ledger(ledger),
            )
    if ledger.loop_count >= ledger.max_loops:
        blocked = replace(ledger, state="blocked")
        return ReviewLoopResult(ledger=blocked, decision=_decision_for_ledger(blocked))

    iteration = ledger.loop_count + 1
    _validate_loop_packets(worker_packet, reviewer_packet, iteration=iteration)
    observations = preview_observations or normalize_review_findings(
        records_by_source, observed_at=observed_at
    )
    merged = {finding.finding_id: finding for finding in ledger.findings}
    for observation in observations:
        previous = merged.get(observation.finding_id)
        merged[observation.finding_id] = (
            observation
            if previous is None
            else _merge_occurrence(previous, observation)
        )

    findings = tuple(merged[key] for key in sorted(merged))
    unresolved = tuple(finding for finding in findings if finding.unresolved)
    repeated_threshold = min(3, ledger.max_loops)
    repeated_high = tuple(
        finding
        for finding in unresolved
        if finding.severity == "high" and finding.occurrence_count >= repeated_threshold
    )
    at_limit = iteration >= ledger.max_loops
    if repeated_high or (at_limit and unresolved):
        state = "blocked"
    elif unresolved:
        state = "adjustment_required"
    else:
        state = "awaiting_supervisor"

    updated = replace(
        ledger,
        loop_count=iteration,
        state=state,
        findings=findings,
        worker_packets=ledger.worker_packets + (worker_packet,),
        reviewer_packets=ledger.reviewer_packets + (reviewer_packet,),
    )
    _validate_ledger(updated)
    return ReviewLoopResult(ledger=updated, decision=_decision_for_ledger(updated))


def reconcile_review_ledger(
    ledger: DocumentationReviewLedger,
    *,
    supervisor_packet: DocumentationReviewPacket,
    approved: bool,
    rationale: str,
    evidence: Iterable[str],
    reconciled_at: str,
) -> DocumentationReviewLedger:
    """Record independent supervisor reconciliation before ``publish_ready``."""
    _validate_ledger(ledger)
    if ledger.state != "awaiting_supervisor" or ledger.unresolved_findings:
        raise DocumentationReviewError(
            "Supervisor reconciliation requires a ledger with no unresolved findings."
        )
    if supervisor_packet.role != "supervisor":
        raise DocumentationReviewError("Reconciliation requires a supervisor packet.")
    if supervisor_packet.iteration != ledger.loop_count:
        raise DocumentationReviewError(
            "Supervisor packet iteration must match the reviewed ledger iteration."
        )
    previous_actors = {
        packet.actor_id for packet in ledger.worker_packets + ledger.reviewer_packets
    }
    if supervisor_packet.actor_id in previous_actors:
        raise DocumentationReviewError(
            "Supervisor reconciliation must be independent of worker and reviewer actors."
        )
    prior_packet_ids = {
        packet.packet_id for packet in ledger.worker_packets + ledger.reviewer_packets
    }
    prior_packet_ids.update(
        item.packet.packet_id for item in ledger.supervisor_reconciliations
    )
    if supervisor_packet.packet_id in prior_packet_ids:
        raise DocumentationReviewError("Review packet ids must be unique.")

    reconciliation = SupervisorReconciliation(
        packet=supervisor_packet,
        approved=_required_bool(approved, "approved"),
        rationale=_required_text(rationale, "supervisor reconciliation rationale"),
        reviewed_finding_ids=tuple(
            finding.finding_id
            for finding in sorted(ledger.findings, key=lambda item: item.finding_id)
        ),
        evidence=_text_tuple(evidence),
        reconciled_at=_required_text(reconciled_at, "reconciled_at"),
    )
    updated = replace(
        ledger,
        state="publish_ready" if approved else "awaiting_supervisor",
        supervisor_reconciliations=(
            ledger.supervisor_reconciliations + (reconciliation,)
        ),
    )
    _validate_ledger(updated)
    return updated


def _normalise_record(
    source: str, record: Mapping[str, Any], observed_at: str
) -> DocumentationReviewFinding:
    category = _normalise_category(
        _first_present(record, "category", "code", "rule_id", "rule", "type", "kind")
    )
    paths = _normalise_paths(
        _combined_values(record, "path", "paths", "file", "files", "page", "pages")
    )
    targets = _normalise_targets(
        _combined_values(record, "target", "targets", "href", "url")
    )
    stable_hint = _optional_text(
        _first_present(record, "fingerprint", "finding_key", "stable_key")
    )
    external_ids = _text_tuple(
        _combined_values(record, "id", "finding_id", "external_id")
    )
    if category == "unspecified" and not paths and not targets and not stable_hint:
        if external_ids:
            stable_hint = external_ids[0]
        else:
            raise DocumentationReviewError(
                "A review finding requires a category, locator, or stable identity key."
            )
    identity = {
        "source": source,
        "category": category,
        "paths": list(paths),
        "targets": list(targets),
        "stable_hint": stable_hint,
    }
    digest = hashlib.sha256(
        json.dumps(identity, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()[:20]
    status = _normalise_status(record.get("status", "open"))
    explicit_rationale = _optional_text(
        _first_present(
            record,
            "rationale",
            "terminal_rationale",
            "resolution_rationale",
            "resolution",
        )
    )
    _require_terminal_rationale(status, explicit_rationale)
    rationale = explicit_rationale or _optional_text(
        _first_present(record, "message", "recommendation", "reason")
    )
    explicit_evidence = _canonical_evidence_values(
        _combined_values(
            record,
            "evidence",
            "evidence_hash",
            "evidence_hashes",
            "verification",
        )
    )
    _require_terminal_evidence(status, explicit_evidence)
    evidence_values = list(explicit_evidence)
    evidence_values.extend(f"path:{path}" for path in paths)
    evidence_values.extend(f"target:{target}" for target in targets)
    line = record.get("line")
    if line is not None and str(line).strip():
        evidence_values.append(f"line:{str(line).strip()}")
    if not evidence_values:
        evidence_values.append(f"{source}:{category}")
    return DocumentationReviewFinding(
        finding_id=f"DOCREV-{digest}",
        category=category,
        severity=_normalise_severity(record.get("severity", "high")),
        source=source,
        status=status,
        evidence=tuple(sorted(set(evidence_values))),
        rationale=rationale,
        first_seen=observed_at,
        last_seen=observed_at,
        occurrence_count=1,
        paths=paths,
        targets=targets,
        external_ids=external_ids,
    )


def _combine_same_iteration(
    left: DocumentationReviewFinding, right: DocumentationReviewFinding
) -> DocumentationReviewFinding:
    if left.status != right.status:
        raise DocumentationReviewError(
            f"Finding {left.finding_id} has conflicting statuses in one review pass."
        )
    return replace(
        left,
        severity=_higher_severity(left.severity, right.severity),
        evidence=_merge_text(left.evidence, right.evidence),
        rationale=_merge_rationale(left.rationale, right.rationale),
        external_ids=_merge_text(left.external_ids, right.external_ids),
    )


def _merge_occurrence(
    previous: DocumentationReviewFinding,
    observation: DocumentationReviewFinding,
) -> DocumentationReviewFinding:
    if (
        previous.category != observation.category
        or previous.source != observation.source
        or previous.paths != observation.paths
        or previous.targets != observation.targets
    ):
        raise DocumentationReviewError(
            f"Stable finding identity collision for {previous.finding_id}."
        )
    return replace(
        previous,
        severity=_higher_severity(previous.severity, observation.severity),
        status=observation.status,
        evidence=_merge_text(previous.evidence, observation.evidence),
        rationale=_merge_rationale(previous.rationale, observation.rationale),
        last_seen=observation.last_seen,
        occurrence_count=previous.occurrence_count + 1,
        external_ids=_merge_text(previous.external_ids, observation.external_ids),
    )


def _decision_for_ledger(ledger: DocumentationReviewLedger) -> ReviewLoopDecision:
    unresolved_ids = tuple(
        finding.finding_id
        for finding in sorted(
            ledger.unresolved_findings, key=lambda item: item.finding_id
        )
    )
    if ledger.state == "blocked":
        repeated_threshold = min(3, ledger.max_loops)
        repeated = tuple(
            finding.finding_id
            for finding in ledger.unresolved_findings
            if finding.severity == "high"
            and finding.occurrence_count >= repeated_threshold
        )
        rationale = (
            "The same unresolved high-severity finding reached the repetition limit."
            if repeated
            else "Unresolved findings remain at the configured adjustment-loop limit."
        )
        return ReviewLoopDecision(
            action="block",
            blocked=True,
            can_continue=False,
            requires_supervisor_reconciliation=False,
            publish_ready=False,
            finding_ids=tuple(sorted(repeated or unresolved_ids)),
            rationale=rationale,
        )
    if ledger.state == "adjustment_required":
        return ReviewLoopDecision(
            action="return_to_worker",
            blocked=False,
            can_continue=ledger.loop_count < ledger.max_loops,
            requires_supervisor_reconciliation=False,
            publish_ready=False,
            finding_ids=unresolved_ids,
            rationale="Unresolved findings must return to the owning worker stage.",
        )
    if ledger.state == "awaiting_supervisor":
        return ReviewLoopDecision(
            action="supervisor_reconciliation",
            blocked=False,
            can_continue=False,
            requires_supervisor_reconciliation=True,
            publish_ready=False,
            finding_ids=(),
            rationale="A clean ledger still requires independent supervisor reconciliation.",
        )
    if ledger.state == "publish_ready":
        return ReviewLoopDecision(
            action="complete",
            blocked=False,
            can_continue=False,
            requires_supervisor_reconciliation=False,
            publish_ready=True,
            finding_ids=(),
            rationale="Independent supervisor reconciliation approved the clean ledger.",
        )
    return ReviewLoopDecision(
        action="review",
        blocked=False,
        can_continue=True,
        requires_supervisor_reconciliation=False,
        publish_ready=False,
        finding_ids=unresolved_ids,
        rationale="The first bounded review pass has not run.",
    )


def _validate_loop_packets(
    worker: DocumentationReviewPacket,
    reviewer: DocumentationReviewPacket,
    *,
    iteration: int,
) -> None:
    if worker.role != "worker" or reviewer.role != "reviewer":
        raise DocumentationReviewError(
            "Each review loop requires separate worker and reviewer packet roles."
        )
    if worker.packet_id == reviewer.packet_id:
        raise DocumentationReviewError(
            "Worker and reviewer packets must have distinct packet ids."
        )
    if worker.iteration != iteration or reviewer.iteration != iteration:
        raise DocumentationReviewError(
            "Worker and reviewer packet iterations must match the review loop."
        )


def _validate_ledger(ledger: DocumentationReviewLedger) -> None:
    if ledger.schema_version != DOCUMENTATION_REVIEW_LEDGER_SCHEMA_VERSION:
        raise DocumentationReviewError(
            "Unsupported documentation review-ledger schema_version."
        )
    _required_text(ledger.run_id, "run_id")
    _positive_int(ledger.max_loops, "max_loops")
    _non_negative_int(ledger.loop_count, "loop_count")
    if ledger.loop_count > ledger.max_loops:
        raise DocumentationReviewError("loop_count must not exceed max_loops.")
    if ledger.state not in SUPPORTED_LEDGER_STATES:
        raise DocumentationReviewError(
            f"Unsupported documentation review-ledger state: {ledger.state!r}"
        )
    finding_ids = [finding.finding_id for finding in ledger.findings]
    if len(finding_ids) != len(set(finding_ids)):
        raise DocumentationReviewError("Review-ledger finding ids must be unique.")
    for finding in ledger.findings:
        _validate_finding(finding)
    for packet in ledger.worker_packets + ledger.reviewer_packets:
        _validate_packet_evidence(packet)
    packet_ids = [
        packet.packet_id for packet in ledger.worker_packets + ledger.reviewer_packets
    ]
    packet_ids.extend(
        item.packet.packet_id for item in ledger.supervisor_reconciliations
    )
    if len(packet_ids) != len(set(packet_ids)):
        raise DocumentationReviewError("Review packet ids must be unique.")
    if any(packet.role != "worker" for packet in ledger.worker_packets):
        raise DocumentationReviewError("worker_packets contains a non-worker role.")
    if any(packet.role != "reviewer" for packet in ledger.reviewer_packets):
        raise DocumentationReviewError("reviewer_packets contains a non-reviewer role.")
    if (
        len(ledger.worker_packets) != ledger.loop_count
        or len(ledger.reviewer_packets) != ledger.loop_count
    ):
        raise DocumentationReviewError(
            "Each completed review loop requires one worker and one reviewer packet."
        )
    expected_iterations = tuple(range(1, ledger.loop_count + 1))
    if (
        tuple(packet.iteration for packet in ledger.worker_packets)
        != expected_iterations
    ):
        raise DocumentationReviewError(
            "Worker packet iterations must be contiguous and ordered."
        )
    if (
        tuple(packet.iteration for packet in ledger.reviewer_packets)
        != expected_iterations
    ):
        raise DocumentationReviewError(
            "Reviewer packet iterations must be contiguous and ordered."
        )
    if any(
        item.packet.role != "supervisor" for item in ledger.supervisor_reconciliations
    ):
        raise DocumentationReviewError(
            "Supervisor reconciliations require supervisor-role packets."
        )
    if ledger.supervisor_reconciliations and ledger.unresolved_findings:
        raise DocumentationReviewError(
            "Supervisor reconciliations require a ledger with no unresolved findings."
        )
    expected_reviewed_ids = tuple(sorted(finding_ids))
    prior_actors = {
        packet.actor_id for packet in ledger.worker_packets + ledger.reviewer_packets
    }
    for reconciliation in ledger.supervisor_reconciliations:
        _required_bool(reconciliation.approved, "approved")
        _required_text(reconciliation.rationale, "supervisor reconciliation rationale")
        _required_text(reconciliation.reconciled_at, "reconciled_at")
        _validate_packet_evidence(reconciliation.packet)
        _validate_text_items(
            reconciliation.reviewed_finding_ids, "reviewed_finding_ids"
        )
        _validate_text_items(
            reconciliation.evidence, "supervisor reconciliation evidence"
        )
        if reconciliation.reviewed_finding_ids != expected_reviewed_ids:
            raise DocumentationReviewError(
                "Supervisor reconciliation reviewed_finding_ids must exactly match "
                "the review-ledger findings."
            )
        if reconciliation.packet.iteration != ledger.loop_count:
            raise DocumentationReviewError(
                "Supervisor packet iteration must match the reviewed ledger iteration."
            )
        if reconciliation.packet.actor_id in prior_actors:
            raise DocumentationReviewError(
                "Supervisor reconciliation must be independent of worker and "
                "reviewer actors."
            )
    if ledger.loop_count == 0:
        if ledger.state != "pending":
            raise DocumentationReviewError(
                "The review ledger must remain pending before the first loop."
            )
    elif ledger.state == "pending":
        raise DocumentationReviewError("pending is valid only before the first loop.")
    if ledger.state in {"adjustment_required", "blocked"} and not (
        ledger.unresolved_findings
    ):
        raise DocumentationReviewError(
            f"{ledger.state} requires at least one unresolved finding."
        )
    if ledger.state == "awaiting_supervisor" and ledger.unresolved_findings:
        raise DocumentationReviewError(
            "awaiting_supervisor cannot contain unresolved findings."
        )
    approved_reconciliations = tuple(
        item for item in ledger.supervisor_reconciliations if item.approved
    )
    if len(approved_reconciliations) > 1:
        raise DocumentationReviewError(
            "A review ledger may contain at most one approved supervisor reconciliation."
        )
    if approved_reconciliations and (
        not ledger.supervisor_reconciliations[-1].approved
    ):
        raise DocumentationReviewError(
            "An approved supervisor reconciliation must be the final reconciliation."
        )
    if ledger.state == "publish_ready":
        if ledger.unresolved_findings:
            raise DocumentationReviewError(
                "publish_ready cannot contain unresolved review findings."
            )
        if not ledger.supervisor_reconciliations:
            raise DocumentationReviewError(
                "publish_ready requires independent supervisor reconciliation."
            )
        if not ledger.supervisor_reconciliations[-1].approved:
            raise DocumentationReviewError(
                "publish_ready requires an approved supervisor reconciliation."
            )
    elif ledger.supervisor_reconciliations and (
        ledger.supervisor_reconciliations[-1].approved
    ):
        raise DocumentationReviewError(
            "An approved final supervisor reconciliation requires publish_ready state."
        )

    if ledger.loop_count > 0 and ledger.unresolved_findings:
        repeated_threshold = min(3, ledger.max_loops)
        should_block = ledger.loop_count >= ledger.max_loops or any(
            finding.severity == "high"
            and finding.occurrence_count >= repeated_threshold
            for finding in ledger.unresolved_findings
        )
        expected_state = "blocked" if should_block else "adjustment_required"
        if ledger.state != expected_state:
            raise DocumentationReviewError(
                "Review-ledger state is inconsistent with its unresolved findings "
                "and loop bounds."
            )
    elif ledger.loop_count > 0:
        expected_state = (
            "publish_ready"
            if ledger.supervisor_reconciliations
            and ledger.supervisor_reconciliations[-1].approved
            else "awaiting_supervisor"
        )
        if ledger.state != expected_state:
            raise DocumentationReviewError(
                "Review-ledger state is inconsistent with its clean reconciliation "
                "state."
            )


def _record_mapping(record: object) -> Mapping[str, Any]:
    if isinstance(record, Mapping):
        return record
    if is_dataclass(record) and not isinstance(record, type):
        return asdict(record)
    to_dict = getattr(record, "to_dict", None)
    if callable(to_dict):
        payload = to_dict()
        if isinstance(payload, Mapping):
            return payload
    raise DocumentationReviewError("Review findings must be objects or dataclasses.")


def _iter_review_records(records: object) -> Iterable[Mapping[str, Any]]:
    """Flatten common checker report envelopes without losing severity class."""
    if isinstance(records, Mapping) or (
        is_dataclass(records) and not isinstance(records, type)
    ):
        outer: Iterable[object] = (records,)
    elif isinstance(records, (str, bytes)):
        outer = (records,)
    else:
        try:
            outer = iter(records)  # type: ignore[arg-type]
        except TypeError:
            outer = (records,)

    envelope_fields = (
        ("issues", "high"),
        ("errors", "high"),
        ("diagnostics", "medium"),
        ("warnings", "medium"),
        ("findings", "high"),
    )
    for raw in outer:
        record = _record_mapping(raw)
        envelope_keys = [key for key, _severity in envelope_fields if key in record]
        if not envelope_keys:
            yield record
            continue
        for key, default_severity in envelope_fields:
            if key not in record:
                continue
            for item in _iter_scalar_values(record.get(key)):
                child = dict(_record_mapping(item))
                child.setdefault("severity", default_severity)
                yield child


def _normalise_source(value: object) -> str:
    source = _optional_text(value).casefold().replace(" ", "-")
    canonical = _SOURCE_ALIASES.get(source)
    if canonical not in SUPPORTED_REVIEW_SOURCES:
        supported = ", ".join(sorted(SUPPORTED_REVIEW_SOURCES))
        raise DocumentationReviewError(
            f"Unsupported review finding source: {value!r} ({supported})"
        )
    return canonical


def _normalise_category(value: object) -> str:
    category = _optional_text(value).casefold()
    category = _CATEGORY_RE.sub("-", category).strip("-")
    return category or "unspecified"


def _normalise_severity(value: object) -> str:
    raw = _optional_text(value).casefold().replace(" ", "-")
    severity = _SEVERITY_ALIASES.get(raw)
    if severity not in SUPPORTED_FINDING_SEVERITIES:
        raise DocumentationReviewError(f"Unsupported finding severity: {value!r}")
    return severity


def _normalise_status(value: object) -> str:
    raw = _optional_text(value).casefold().replace(" ", "-")
    status = _STATUS_ALIASES.get(raw)
    if status not in SUPPORTED_FINDING_STATUSES:
        raise DocumentationReviewError(f"Unsupported finding status: {value!r}")
    return status


def _normalise_paths(values: object) -> tuple[str, ...]:
    """Keep unsafe spellings visible in non-authoritative review metadata."""

    paths = (
        normalize_observational_posix_path(value)
        for value in _iter_scalar_values(values)
    )
    return tuple(
        sorted(
            {path for path in paths if path is not None},
            key=lambda item: (item.casefold(), item),
        )
    )


def _normalise_targets(values: object) -> tuple[str, ...]:
    targets = [str(value).strip() for value in _iter_scalar_values(values)]
    return tuple(
        sorted(
            {value for value in targets if value},
            key=lambda item: (item.casefold(), item),
        )
    )


def _canonical_evidence_values(values: object) -> tuple[str, ...]:
    evidence: list[str] = []
    for value in _iter_scalar_values(values):
        if isinstance(value, Mapping) or _is_sequence(value):
            evidence.append(
                json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)
            )
        else:
            text = str(value).strip()
            if text:
                evidence.append(text)
    return tuple(sorted(set(evidence)))


def _combined_values(record: Mapping[str, Any], *keys: str) -> list[Any]:
    combined: list[Any] = []
    for key in keys:
        if key not in record or record[key] is None:
            continue
        combined.extend(_iter_scalar_values(record[key]))
    return combined


def _first_present(record: Mapping[str, Any], *keys: str) -> object:
    for key in keys:
        value = record.get(key)
        if value is not None and str(value).strip():
            return value
    return ""


def _iter_scalar_values(value: object) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, (str, bytes, Mapping)):
        return [value]
    if _is_sequence(value) or isinstance(value, (set, frozenset)):
        return list(value)
    if isinstance(value, IterableABC):
        return list(value)
    return [value]


def _is_sequence(value: object) -> bool:
    return isinstance(value, Sequence) and not isinstance(value, (str, bytes))


def _text_tuple(values: object) -> tuple[str, ...]:
    return tuple(
        sorted(
            {
                str(value).strip()
                for value in _iter_scalar_values(values)
                if str(value).strip()
            }
        )
    )


def _merge_text(left: Iterable[str], right: Iterable[str]) -> tuple[str, ...]:
    return tuple(sorted(set(left).union(right)))


def _merge_rationale(left: str, right: str) -> str:
    return " | ".join(sorted({value for value in (left, right) if value}))


def _higher_severity(left: str, right: str) -> str:
    return max((left, right), key=lambda value: _SEVERITY_ORDER[value])


def _require_terminal_rationale(status: str, rationale: str) -> None:
    if status in TERMINAL_FINDING_STATUSES and not rationale.strip():
        raise DocumentationReviewError(
            f"Terminal finding status {status!r} requires a rationale."
        )


def _require_terminal_evidence(status: str, evidence: Iterable[str]) -> None:
    if status in TERMINAL_FINDING_STATUSES and not tuple(evidence):
        raise DocumentationReviewError(
            f"Terminal finding status {status!r} requires explicit evidence."
        )


def _validate_finding(finding: DocumentationReviewFinding) -> None:
    _required_text(finding.finding_id, "finding id")
    _required_text(finding.category, "finding category")
    if finding.severity not in SUPPORTED_FINDING_SEVERITIES:
        raise DocumentationReviewError(
            f"Unsupported finding severity: {finding.severity!r}"
        )
    if finding.source not in SUPPORTED_REVIEW_SOURCES:
        raise DocumentationReviewError(
            f"Unsupported review finding source: {finding.source!r}"
        )
    if finding.status not in SUPPORTED_FINDING_STATUSES:
        raise DocumentationReviewError(
            f"Unsupported finding status: {finding.status!r}"
        )
    _required_text(finding.first_seen, "first_seen")
    _required_text(finding.last_seen, "last_seen")
    _positive_int(finding.occurrence_count, "occurrence_count")
    _validate_text_items(finding.evidence, "finding evidence")
    _validate_text_items(finding.paths, "finding paths")
    _validate_text_items(finding.targets, "finding targets")
    _validate_text_items(finding.external_ids, "finding external_ids")
    if not isinstance(finding.rationale, str):
        raise DocumentationReviewError("finding rationale must be a string.")
    _require_terminal_rationale(finding.status, finding.rationale)
    _require_terminal_evidence(finding.status, finding.evidence)


def _validate_packet_evidence(packet: DocumentationReviewPacket) -> None:
    _validate_text_items(packet.evidence, "packet evidence")


def _validate_text_items(values: object, label: str) -> None:
    """Preserve free-form tuple items stored by the review-ledger contract."""

    require_trimmed_text_list(
        values,
        error=DocumentationReviewError(
            f"{label} must contain only non-empty strings."
        ),
        require_trimmed_items=False,
        reject_control_characters=False,
        container_type=tuple,
    )


def _require_exact_fields(
    payload: Mapping[str, Any], expected: frozenset[str], label: str
) -> None:
    return require_shared_exact_fields(
        payload,
        allowed=expected,
        required=expected,
        mapping_error=DocumentationReviewError(
            f"Review-ledger {label} must be an object."
        ),
        missing_error=lambda fields: DocumentationReviewError(
            f"{label} is missing required fields: {', '.join(fields)}."
        ),
        unknown_error=lambda fields: DocumentationReviewError(
            f"{label} contains unsupported fields: "
            f"{', '.join(str(field) for field in fields)}."
        ),
    )


def _required_json_string(value: object, label: str) -> str:
    return require_string(
        value,
        error=DocumentationReviewError(f"{label} must be a string."),
    )


def _required_json_text(value: object, label: str) -> str:
    """Preserve review-ledger whitespace normalization and embedded controls."""

    text = _required_json_string(value, label)
    return require_nonempty_text(
        text,
        error=DocumentationReviewError(f"{label} must not be empty."),
        normalize=True,
        reject_control_characters=False,
    )


def _required_enum(value: object, supported: frozenset[str], label: str) -> str:
    text = _required_json_text(value, label)
    error = DocumentationReviewError(f"Unsupported {label}: {value!r}")
    return require_shared_choice(
        text,
        supported,
        text_error=error,
        choice_error=lambda _allowed: error,
    )


def _required_string_list(value: object, label: str) -> tuple[str, ...]:
    """Preserve untrimmed free-form strings in persisted review arrays."""

    return tuple(
        require_trimmed_text_list(
            value,
            error=DocumentationReviewError(
                f"{label} must be a list of non-empty strings."
            ),
            require_trimmed_items=False,
            reject_control_characters=False,
        )
    )


def _required_positive_int(value: object, label: str) -> int:
    error = DocumentationReviewError(f"{label} must be a positive integer.")
    return require_shared_positive_int(
        value,
        invalid_error=error,
        zero_error=error,
    )


def _required_non_negative_int(value: object, label: str) -> int:
    return require_shared_nonnegative_int(
        value,
        error=DocumentationReviewError(
            f"{label} must be a non-negative integer."
        ),
    )


def _required_text(value: object, label: str) -> str:
    """Preserve the v1 review contract's coercion of scalar display values."""

    return require_nonempty_text(
        coerce_trimmed_text(value),
        error=DocumentationReviewError(f"{label} must not be empty."),
        reject_control_characters=False,
    )


def _optional_text(value: object) -> str:
    """Preserve the v1 review contract's loose optional display-text coercion."""

    return coerce_trimmed_text(value)


def _required_bool(value: object, label: str) -> bool:
    return require_shared_bool(
        value,
        error=DocumentationReviewError(f"{label} must be a boolean."),
    )


def _positive_int(value: object, label: str) -> int:
    """Preserve legacy integer coercion while still requiring a positive result."""

    return coerce_positive_int(
        value,
        error=DocumentationReviewError(f"{label} must be a positive integer."),
    )


def _non_negative_int(value: object, label: str) -> int:
    """Preserve legacy integer coercion for review summary counters."""

    return coerce_nonnegative_int(
        value,
        error=DocumentationReviewError(
            f"{label} must be a non-negative integer."
        ),
    )


def _require_mapping(value: object, label: str) -> Mapping[str, Any]:
    return require_shared_mapping(
        value,
        error=DocumentationReviewError(
            f"Review-ledger {label} must be an object."
        ),
    )
