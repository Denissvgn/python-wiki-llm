"""Evidence-backed admission and intake controller for documentation calibration.

This lifecycle is deliberately separate from ``documentation-run/v1``.  The
existing documentation workspaces are read-only controls; this controller
copies only bounded, priority-blind evidence into a fresh protected root and
records every mutation in an application-level, create-once hash-linked
transition ledger.  Its integrity checks inherit the same-user trust
assumptions documented by :mod:`protected_artifacts`; they do not authenticate
content against the filesystem owner, root, or offline modification.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import stat
import tempfile
import unicodedata
import uuid
import warnings
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from functools import wraps
from pathlib import Path, PurePosixPath
from typing import Any, BinaryIO, Callable, Iterable, Mapping, Sequence

from .contracts import (
    CALIBRATION_CONTROLLER_MAX_PACKET_BYTES,
    P0_CALIBRATION_ACCESS_EVENT_SCHEMA_VERSION,
    P0_CALIBRATION_ADMISSION_SCHEMA_VERSION,
    P0_CALIBRATION_AMBIGUOUS_RECOVERY_SCHEMA_VERSION,
    P0_CALIBRATION_AGENT_PACKET_SCHEMA_VERSION,
    P0_CALIBRATION_AGENT_RESULT_SCHEMA_VERSION,
    P0_CALIBRATION_AUTHORITY_GRANT_SCHEMA_VERSION,
    P0_CALIBRATION_CONTROL_RECORD_SCHEMA_VERSION,
    P0_CALIBRATION_DECISION_SCOPE,
    P0_CALIBRATION_DISPATCH_RECEIPT_SCHEMA_VERSION,
    P0_CALIBRATION_EMERGENCY_REJECTION_SCHEMA_VERSION,
    P0_CALIBRATION_EVIDENCE_BUNDLE_SCHEMA_VERSION,
    P0_CALIBRATION_EXECUTION_MANIFEST_SCHEMA_VERSION,
    P0_CALIBRATION_FROZEN_INTAKE_SCHEMA_VERSION,
    P0_CALIBRATION_ISOLATION_ATTESTATION_SCHEMA_VERSION,
    P0_CALIBRATION_LABEL_FIELD_CONTRACT_SCHEMA_VERSION,
    P0_CALIBRATION_OPTIMIZER_SEARCH_CONTRACT_SCHEMA_VERSION,
    P0_CALIBRATION_ROLE_CAPABILITY_MATRIX_SCHEMA_VERSION,
    P0_CALIBRATION_RUN_SCHEMA_VERSION,
    P0_CALIBRATION_RUNTIME_BINDINGS_SCHEMA_VERSION,
    P0_CALIBRATION_TASK_ORACLE_SCHEMA_VERSION,
    P0_CALIBRATION_TRANSITION_SCHEMA_VERSION,
    P0_CALIBRATION_TRANSACTION_SCHEMA_VERSION,
    P0_CALIBRATION_VERIFICATION_REPORT_SCHEMA_VERSION,
)
from .documentation_calibration import (
    DocumentationCalibrationError,
    validate_flow_evidence_census,
)
from .documentation_policy import (
    DocumentationPolicyError,
    TreeBaseline,
    compare_tree_baseline,
    hash_bytes,
)
from .documentation_run import (
    POLICY_FILENAME,
    RUN_CONTROL_DIR,
    DocumentationRun,
    DocumentationRunError,
)
from .documentation_worklist import (
    DOCUMENTATION_WORKLIST_SCHEMA_VERSION,
    WORK_ITEM_PRIORITIES,
    WORK_ITEM_STATUSES,
)
from .filesystem_guard import (
    WindowsDirectoryGuardError,
    WindowsFileGuardError,
    guard_windows_directory_chain,
    open_windows_readonly_file,
)
from .protected_artifacts import (
    ProtectedArtifactError,
    ProtectedArtifactIntegrityError,
    ProtectedArtifactStore,
    canonical_json_bytes,
    validate_portable_relative_path,
)
from .redaction import (
    COMMON_TOKEN_PATTERNS as _COMMON_TOKEN_PATTERNS,
    PRIVATE_KEY_BLOCK_RE as _PRIVATE_KEY_BLOCK_RE,
    SENSITIVE_ASSIGNMENT_RE as _SENSITIVE_ASSIGNMENT_RE,
    SENSITIVE_NATURAL_LANGUAGE_RE as _SENSITIVE_NATURAL_LANGUAGE_RE,
    URI_USERINFO_RE as _URI_USERINFO_RE,
)


CALIBRATION_STATES = (
    "PREFLIGHT",
    "BASELINE_FROZEN",
    "ADMISSION_AUTHORIZED",
    "INTAKE_OPEN",
    "INTAKE_FROZEN",
    "BLOCKED_NO_SHIP",
    "REJECT",
)
CALIBRATION_TERMINAL_STATES = frozenset({"INTAKE_FROZEN", "BLOCKED_NO_SHIP", "REJECT"})
CALIBRATION_ROLES = ("intake-a", "intake-b", "intake-c", "verifier")
INTAKE_ROLES = CALIBRATION_ROLES[:3]
ADMISSION_PROFILES = frozenset({"local_no_egress", "external_authorized"})

_ZERO_HASH = "sha256:" + ("0" * 64)
_SHA256_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
_PORTABLE_ID_RE = re.compile(r"^[a-z0-9][a-z0-9._-]{0,127}$")
_MAX_EXTERNAL_JSON_BYTES = 16 * 1024 * 1024
_MAX_BUNDLE_BYTES = 16 * 1024 * 1024
_MAX_DOCUMENT_BYTES = 64 * 1024
_MAX_DOCUMENT_COUNT = 128
_MAX_DOCUMENT_TOTAL_BYTES = 4 * 1024 * 1024
_MAX_RESULT_BYTES = 4 * 1024 * 1024
_MAX_DISPATCH_FAILURE_MESSAGE_BYTES = 2048
_MAX_TRANSACTION_BYTES = 64 * 1024 * 1024
_EXTERNAL_DISPATCH_FAILURE_REASONS = frozenset(
    {
        "dispatch_failed",
        "resource_exhausted",
        "transport_inconclusive",
        "unreconciled_started_dispatch",
    }
)
_REPARSE_ATTRIBUTE = 0x400
_POSIX_DESCRIPTOR_RELATIVE_READS = (
    os.name != "nt"
    and bool(getattr(os, "O_NOFOLLOW", 0))
    and bool(getattr(os, "O_DIRECTORY", 0))
    and os.open in getattr(os, "supports_dir_fd", set())
)
_DOCUMENT_SUFFIXES = frozenset({".md", ".markdown", ".rst", ".txt", ".adoc"})
_ROOT_DOCUMENT_NAMES = frozenset(
    {
        "readme",
        "contributing",
        "architecture",
        "overview",
        "getting-started",
        "getting_started",
    }
)
_PROJECT_MANIFEST_NAMES = frozenset(
    {
        "pyproject.toml",
        "package.json",
        "cargo.toml",
        "go.mod",
        "pom.xml",
        "build.gradle",
        "build.gradle.kts",
        "composer.json",
        "gemfile",
        "mix.exs",
        "pubspec.yaml",
        "project.clj",
    }
)
_ALLOWED_ROOT_FILES = frozenset(
    {
        "controller.lock",
        "run.json",
        "pending-transaction.json",
        "state-transitions.jsonl",
        "terminal-rejection.json",
    }
)
_ALLOWED_ROOT_DIRS = frozenset(
    {
        "authority",
        "baseline",
        "dispatch",
        "evidence",
        "intake",
        "packets",
        "transitions",
        "verification",
    }
)
_ALLOWED_TRANSITIONS = {
    "PREFLIGHT": frozenset({"BASELINE_FROZEN", "BLOCKED_NO_SHIP", "REJECT"}),
    "BASELINE_FROZEN": frozenset({"ADMISSION_AUTHORIZED", "BLOCKED_NO_SHIP", "REJECT"}),
    "ADMISSION_AUTHORIZED": frozenset({"INTAKE_OPEN", "BLOCKED_NO_SHIP", "REJECT"}),
    "INTAKE_OPEN": frozenset({"INTAKE_FROZEN", "BLOCKED_NO_SHIP", "REJECT"}),
    "INTAKE_FROZEN": frozenset(),
    "BLOCKED_NO_SHIP": frozenset(),
    "REJECT": frozenset(),
}
_FILE_URI_RE = re.compile(r"\bfile:///[^\s<>'\"`]+", re.IGNORECASE)
_WINDOWS_ABSOLUTE_PATH_RE = re.compile(
    r"(?<![A-Za-z0-9])(?:"
    r"[A-Za-z]:[\\/](?:[^\\/\s<>:\"|?*]+[\\/])*[^\\/\s<>:\"|?*]*"
    r"|\\\\[^\\/\s]+[\\/][^\\/\s]+(?:[\\/][^\s<>:\"|?*]+)*"
    r")"
)
_POSIX_ABSOLUTE_PATH_RE = re.compile(
    r"(?<![A-Za-z0-9_:/.])/(?!/)"
    r"(?:applications|bin|boot|code|data|dev|etc|home|lib|lib64|library|media|"
    r"mnt|net|opt|private|proc|project|repo|root|run|sbin|snap|srv|sys|system|"
    r"tmp|users|usr|var|volumes|workspace|workspaces)"
    r"(?:/[^/\s<>'\"`,;:)\]}]+)+",
    re.IGNORECASE,
)
class P0CalibrationError(RuntimeError):
    """Base error raised by the protected calibration lifecycle."""


class P0CalibrationSchemaError(P0CalibrationError):
    """Raised when a calibration contract is malformed."""


class P0CalibrationIntegrityError(P0CalibrationError):
    """Raised when protected evidence or ledger integrity is violated."""


class P0CalibrationTransitionError(P0CalibrationError):
    """Raised when a lifecycle transition is illegal or stale."""


class P0CalibrationRecoveryError(P0CalibrationError):
    """Raised when a crash marker cannot be recovered unambiguously."""


class _ExternalBrokerAuthenticationUnavailable(P0CalibrationError):
    """Raised when external receipt authentication cannot be performed."""


@dataclass(frozen=True)
class _EvidenceFileSnapshot:
    """Bytes, size, and hashes derived from one pinned evidence handle."""

    included: bytes
    original_bytes: int
    sha256: str
    included_sha256: str
    truncated: bool


@dataclass(frozen=True)
class P0CalibrationRun:
    """Current protected controller snapshot."""

    payload: dict[str, Any]

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "P0CalibrationRun":
        normalized = _json_round_trip(payload)
        _validate_run_snapshot(normalized)
        return cls(normalized)

    @property
    def cohort_id(self) -> str:
        return str(self.payload["cohort_id"])

    @property
    def state(self) -> str:
        return str(self.payload["state"])

    @property
    def generation(self) -> int:
        return int(self.payload["generation"])

    @property
    def head_transition_hash(self) -> str:
        return str(self.payload["head_transition_hash"])

    def to_dict(self) -> dict[str, Any]:
        return _json_round_trip(self.payload)

    def to_json(self) -> str:
        return (
            json.dumps(self.payload, ensure_ascii=False, indent=2, sort_keys=True)
            + "\n"
        )


@dataclass(frozen=True)
class P0CalibrationStatus:
    """Operator-facing status for one calibration cohort."""

    cohort_id: str
    state: str
    generation: int
    decision_scope: str
    admission_profile: str
    role_statuses: dict[str, str]
    next_actions: tuple[str, ...]
    limitations: tuple[str, ...]
    terminal: bool
    healthy: bool

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "P0CalibrationStatus":
        _require_exact_fields(
            payload,
            {
                "cohort_id",
                "state",
                "generation",
                "decision_scope",
                "admission_profile",
                "role_statuses",
                "next_actions",
                "limitations",
                "terminal",
                "healthy",
            },
            label="calibration status",
        )
        role_statuses = payload.get("role_statuses")
        if not isinstance(role_statuses, Mapping):
            raise P0CalibrationSchemaError(
                "Calibration status role_statuses must be an object."
            )
        return cls(
            cohort_id=_require_text(payload.get("cohort_id"), "status cohort_id"),
            state=_require_choice(
                payload.get("state"), CALIBRATION_STATES, "status state"
            ),
            generation=_require_nonnegative_int(
                payload.get("generation"), "status generation"
            ),
            decision_scope=_require_text(
                payload.get("decision_scope"), "status decision_scope"
            ),
            admission_profile=_require_choice(
                payload.get("admission_profile"),
                ADMISSION_PROFILES,
                "status admission_profile",
            ),
            role_statuses={
                str(key): _require_text(value, f"status role {key}")
                for key, value in role_statuses.items()
            },
            next_actions=tuple(
                _require_text_list(payload.get("next_actions"), "status next_actions")
            ),
            limitations=tuple(
                _require_text_list(payload.get("limitations"), "status limitations")
            ),
            terminal=_require_bool(payload.get("terminal"), "status terminal"),
            healthy=_require_bool(payload.get("healthy"), "status healthy"),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "cohort_id": self.cohort_id,
            "state": self.state,
            "generation": self.generation,
            "decision_scope": self.decision_scope,
            "admission_profile": self.admission_profile,
            "role_statuses": dict(self.role_statuses),
            "next_actions": list(self.next_actions),
            "limitations": list(self.limitations),
            "terminal": self.terminal,
            "healthy": self.healthy,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, sort_keys=True) + "\n"


@dataclass(frozen=True)
class P0CalibrationAgentPacket:
    """One bounded, provider-neutral role packet."""

    payload: dict[str, Any]

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "P0CalibrationAgentPacket":
        normalized = _json_round_trip(payload)
        _validate_agent_packet(normalized)
        return cls(normalized)

    @property
    def packet_id(self) -> str:
        return str(self.payload["packet_id"])

    @property
    def role(self) -> str:
        return str(self.payload["role"])

    def to_dict(self) -> dict[str, Any]:
        return _json_round_trip(self.payload)

    def to_json(self) -> str:
        return (
            json.dumps(self.payload, ensure_ascii=False, indent=2, sort_keys=True)
            + "\n"
        )


@dataclass(frozen=True)
class P0CalibrationAgentResult:
    """Strict result returned by an intake or verifier role."""

    payload: dict[str, Any]

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "P0CalibrationAgentResult":
        normalized = _json_round_trip(payload)
        _validate_agent_result(normalized)
        return cls(normalized)

    @property
    def result_id(self) -> str:
        return str(self.payload["result_id"])

    @property
    def role(self) -> str:
        return str(self.payload["role"])

    def to_dict(self) -> dict[str, Any]:
        return _json_round_trip(self.payload)

    def to_json(self) -> str:
        return (
            json.dumps(self.payload, ensure_ascii=False, indent=2, sort_keys=True)
            + "\n"
        )


@dataclass(frozen=True)
class P0CalibrationDispatchReceipt:
    """Broker receipt binding one invocation to protected controller state."""

    payload: dict[str, Any]

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "P0CalibrationDispatchReceipt":
        normalized = _json_round_trip(payload)
        _validate_dispatch_receipt(normalized)
        return cls(normalized)

    @property
    def receipt_id(self) -> str:
        return str(self.payload["receipt_id"])

    def to_dict(self) -> dict[str, Any]:
        return _json_round_trip(self.payload)

    def to_json(self) -> str:
        return (
            json.dumps(self.payload, ensure_ascii=False, indent=2, sort_keys=True)
            + "\n"
        )


@dataclass(frozen=True)
class P0CalibrationVerificationReport:
    """Recomputed evidence, citation, and transition gates."""

    payload: dict[str, Any]

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "P0CalibrationVerificationReport":
        normalized = _json_round_trip(payload)
        _validate_verification_report(normalized)
        return cls(normalized)

    @property
    def ok(self) -> bool:
        return bool(self.payload["ok"])

    def to_dict(self) -> dict[str, Any]:
        return _json_round_trip(self.payload)

    def to_json(self) -> str:
        return (
            json.dumps(self.payload, ensure_ascii=False, indent=2, sort_keys=True)
            + "\n"
        )


def prepare_calibration_run(
    root: str | Path,
    *,
    control_workspaces: Sequence[str | Path],
    execution_manifest: Mapping[str, Any],
) -> P0CalibrationRun:
    """Freeze two matching documentation controls into a fresh cohort.

    Preparation performs no agent dispatch and does not authorize intake.
    ``P0C-000`` diagnostics are intentionally not consulted.
    """

    if isinstance(control_workspaces, (str, bytes)) or len(control_workspaces) != 2:
        raise P0CalibrationSchemaError(
            "prepare requires exactly two documentation control workspaces."
        )
    manifest = _json_round_trip(execution_manifest)
    _validate_execution_manifest(manifest)
    controls = [
        _load_control_workspace(Path(value), index=index)
        for index, value in enumerate(control_workspaces, start=1)
    ]
    if controls[0]["workspace_root"] == controls[1]["workspace_root"]:
        raise P0CalibrationIntegrityError(
            "Control workspaces must be independently prepared directories."
        )
    if controls[0]["run"].run_id == controls[1]["run"].run_id:
        raise P0CalibrationIntegrityError(
            "Control workspaces must contain independently prepared documentation "
            "run identities."
        )
    _assert_controls_match(controls)
    protected_root = _validate_protected_root_placement(
        Path(root),
        control_roots=[record["workspace_root"] for record in controls],
        source_roots=[record["source_root"] for record in controls],
    )
    cohort_id = str(uuid.uuid4())
    evidence_bound_roots = [
        protected_root,
        *_implementation_worktree_roots(),
        *(
            Path(record[name])
            for record in controls
            for name in ("workspace_root", "source_root", "wiki_root")
        ),
    ]
    evidence_bundle = _compile_evidence_bundle(
        controls[0],
        bound_roots=evidence_bound_roots,
    )
    independently_compiled = _compile_evidence_bundle(
        controls[1],
        bound_roots=evidence_bound_roots,
    )
    if independently_compiled != evidence_bundle:
        raise P0CalibrationIntegrityError(
            "The two documentation controls do not compile the same frozen "
            "priority-blind evidence bundle."
        )
    refreshed_controls = [
        _load_control_workspace(Path(value), index=index)
        for index, value in enumerate(control_workspaces, start=1)
    ]
    _assert_controls_match(refreshed_controls)
    for original, refreshed in zip(controls, refreshed_controls):
        if _portable_control_record(
            original, cohort_id=cohort_id
        ) != _portable_control_record(refreshed, cohort_id=cohort_id) or any(
            original[name] != refreshed[name]
            for name in ("workspace_root", "source_root", "wiki_root")
        ):
            raise P0CalibrationIntegrityError(
                "A source or documentation control changed while evidence was frozen."
            )
    if len(canonical_json_bytes(evidence_bundle)) > _MAX_BUNDLE_BYTES:
        raise P0CalibrationSchemaError(
            f"Evidence bundle exceeds the {_MAX_BUNDLE_BYTES}-byte limit."
        )
    control_payloads = [
        _portable_control_record(record, cohort_id=cohort_id) for record in controls
    ]
    runtime_bindings = {
        "schema_version": P0_CALIBRATION_RUNTIME_BINDINGS_SCHEMA_VERSION,
        "cohort_id": cohort_id,
        "control_workspaces": [str(record["workspace_root"]) for record in controls],
        "source_roots": [str(record["source_root"]) for record in controls],
        "implementation_roots": [
            str(path) for path in _implementation_worktree_roots()
        ],
    }
    role_matrix = _build_role_capability_matrix(cohort_id)
    manifest_hash = _sha256_json(manifest)
    evidence_hash = _sha256_json(evidence_bundle)
    created_at = _utc_now()
    base_body = {
        "schema_version": P0_CALIBRATION_RUN_SCHEMA_VERSION,
        "cohort_id": cohort_id,
        "state": "PREFLIGHT",
        "decision_scope": P0_CALIBRATION_DECISION_SCOPE,
        "generation": 0,
        "created_at": created_at,
        "updated_at": created_at,
        "execution_manifest_hash": manifest_hash,
        "evidence_bundle_hash": evidence_hash,
        "source": {
            "revision": controls[0]["source_revision"],
            "content_fingerprint": controls[0]["source_fingerprint"],
            "tree_hash": controls[0]["source_tree_hash"],
        },
        "population": _json_round_trip(controls[0]["population"]),
        "admission_profile": manifest["profile"],
        "authority_hash": None,
        "attestation_hash": None,
        "roles": {role: _initial_role_state() for role in CALIBRATION_ROLES},
        "active_dispatches": {},
        "recorded_receipts": {},
        "artifacts": {
            "execution_manifest": "baseline/execution-manifest.json",
            "control_records": [
                "baseline/control-01.json",
                "baseline/control-02.json",
            ],
            "runtime_bindings": "baseline/runtime-bindings.json",
            "evidence_bundle": "evidence/bundle.json",
            "role_capability_matrix": "baseline/role-capability-matrix.json",
        },
        "limitations": [
            "Baseline evidence is frozen but agent dispatch is not authorized.",
            "No labels, scores, weights, candidate policy, or default-policy change exist.",
        ],
        "terminal_reason_codes": [],
    }
    artifacts = [
        ("baseline/execution-manifest.json", manifest),
        ("baseline/control-01.json", control_payloads[0]),
        ("baseline/control-02.json", control_payloads[1]),
        ("baseline/runtime-bindings.json", runtime_bindings),
        ("evidence/bundle.json", evidence_bundle),
        ("baseline/role-capability-matrix.json", role_matrix),
    ]
    try:
        store = ProtectedArtifactStore(protected_root, create=True)
        with store.lock():
            return _commit_transition(
                store,
                current=None,
                expected_generation=0,
                expected_head=_ZERO_HASH,
                target_state="BASELINE_FROZEN",
                event_type="baseline_frozen",
                run_body=base_body,
                artifacts=artifacts,
                reason_codes=(),
            )
    except ProtectedArtifactError as exc:
        raise P0CalibrationIntegrityError(str(exc)) from exc


def get_calibration_run_status(root: str | Path) -> P0CalibrationStatus:
    """Return verified status without advancing the lifecycle."""

    store = _open_store(root)
    with store.lock():
        run = _load_run_locked(store)
        if run.state in {
            "BASELINE_FROZEN",
            "ADMISSION_AUTHORIZED",
            "INTAKE_OPEN",
        }:
            control_failure = _recheck_bound_controls(store, run)
            if control_failure is not None:
                run = _terminal_transition_locked(
                    store,
                    run,
                    state="REJECT",
                    reason_codes=("source_or_control_mutation",),
                    details={"error": control_failure},
                )
            elif run.state in {"ADMISSION_AUTHORIZED", "INTAKE_OPEN"}:
                authority_failure = _authority_freshness_failure(store, run)
                if authority_failure is not None:
                    run = _terminal_transition_locked(
                        store,
                        run,
                        state="BLOCKED_NO_SHIP",
                        reason_codes=("authority_no_longer_valid",),
                        details={"error": authority_failure},
                    )
        if (
            run.state not in CALIBRATION_TERMINAL_STATES
            and _has_indeterminate_admission_probe(run)
        ):
            run = _terminal_transition_locked(
                store,
                run,
                state="BLOCKED_NO_SHIP",
                reason_codes=("indeterminate_started_admission_probe",),
            )
        stale_dispatches = _stale_active_dispatches(run)
        if stale_dispatches and run.state not in CALIBRATION_TERMINAL_STATES:
            run = _terminal_transition_locked(
                store,
                run,
                state="BLOCKED_NO_SHIP",
                reason_codes=("indeterminate_started_dispatch",),
                details={"roles": stale_dispatches},
            )
        return _status_from_run(run)


def validate_p0_calibration_packet_output(
    root: str | Path,
    output: str | Path,
) -> Path:
    """Resolve one private packet destination outside every frozen evidence root."""

    store = _open_store(root)
    requested = Path(os.path.abspath(os.fspath(Path(output).expanduser())))
    _assert_portable_leaf_name(requested.name, "packet output")
    parent = requested.parent
    try:
        _assert_regular_directory(parent, "packet output parent")
        resolved_parent = parent.resolve(strict=True)
    except OSError as exc:
        raise P0CalibrationIntegrityError(
            f"Packet output parent must already exist: {parent}: {exc}"
        ) from exc
    if resolved_parent != parent:
        raise P0CalibrationIntegrityError(
            "Packet output parent cannot traverse a link or reparse point."
        )
    for ancestor in [*reversed(parent.parents), parent]:
        _assert_not_link_or_reparse(ancestor, "packet output parent chain")
    target = resolved_parent / requested.name
    if os.path.lexists(target):
        _assert_not_link_or_reparse(target, "packet output")
        try:
            metadata = target.lstat()
        except OSError as exc:
            raise P0CalibrationIntegrityError(
                f"Cannot inspect packet output {target}: {exc}"
            ) from exc
        if (
            not stat.S_ISREG(metadata.st_mode)
            or int(getattr(metadata, "st_nlink", 1)) != 1
        ):
            raise P0CalibrationIntegrityError(
                "Existing packet output must be one regular, unlinked file."
            )
    with store.lock():
        run = _load_run_locked(store)
        bindings = store.read_json(run.payload["artifacts"]["runtime_bindings"])
        forbidden = [
            store.root,
            *(
                Path(value).resolve(strict=True)
                for value in bindings["control_workspaces"]
            ),
            *(Path(value).resolve(strict=True) for value in bindings["source_roots"]),
            *(
                Path(value).resolve(strict=True)
                for value in bindings["implementation_roots"]
            ),
        ]
        for candidate in forbidden:
            if _paths_overlap(target, candidate):
                raise P0CalibrationIntegrityError(
                    "Calibration packet output must remain outside the protected "
                    "root, source/control roots, and implementation worktree."
                )
    return target


def admit_calibration_run(
    root: str | Path,
    *,
    authority_grant: Mapping[str, Any],
    broker_attestation: Mapping[str, Any] | None = None,
) -> P0CalibrationRun:
    """Authorize one frozen cohort after authority and isolation checks.

    Invalid, expired, revoked, or scope-mismatched authority terminates the
    cohort as ``BLOCKED_NO_SHIP`` before any probe or agent dispatch.
    """

    store = _open_store(root)
    with store.lock():
        run = _load_run_locked(store)
        if run.state == "ADMISSION_AUTHORIZED":
            control_failure = _recheck_bound_controls(store, run)
            if control_failure is not None:
                return _terminal_transition_locked(
                    store,
                    run,
                    state="REJECT",
                    reason_codes=("source_or_control_mutation",),
                    details={"error": control_failure},
                )
            supplied = _sha256_json(_json_round_trip(authority_grant))
            if supplied == run.payload["authority_hash"]:
                freshness_failure = _authority_freshness_failure(store, run)
                if freshness_failure is not None:
                    return _terminal_transition_locked(
                        store,
                        run,
                        state="BLOCKED_NO_SHIP",
                        reason_codes=("authority_no_longer_valid",),
                        details={"error": freshness_failure},
                    )
                return run
            return _terminal_transition_locked(
                store,
                run,
                state="REJECT",
                reason_codes=("authority_replay_bytes_changed",),
            )
        if run.state != "BASELINE_FROZEN":
            raise P0CalibrationTransitionError(
                f"Admission requires BASELINE_FROZEN, not {run.state}."
            )
        control_failure = _recheck_bound_controls(store, run)
        if control_failure is not None:
            return _terminal_transition_locked(
                store,
                run,
                state="REJECT",
                reason_codes=("source_or_control_mutation",),
                details={"error": control_failure},
            )
        if _has_indeterminate_admission_probe(run):
            return _terminal_transition_locked(
                store,
                run,
                state="BLOCKED_NO_SHIP",
                reason_codes=("indeterminate_started_admission_probe",),
            )
        manifest = store.read_json("baseline/execution-manifest.json")
        grant = _json_round_trip(authority_grant)
        if run.payload.get("authority_hash") is not None:
            supplied_hash = _sha256_json(grant)
            if supplied_hash != run.payload["authority_hash"]:
                return _terminal_transition_locked(
                    store,
                    run,
                    state="REJECT",
                    reason_codes=("authority_replay_bytes_changed",),
                )
            freshness_failure = _pre_admission_authority_freshness_failure(store, run)
            if freshness_failure is not None:
                return _terminal_transition_locked(
                    store,
                    run,
                    state="BLOCKED_NO_SHIP",
                    reason_codes=("authority_no_longer_valid",),
                    details={"error": freshness_failure},
                )
            authority_path = run.payload["artifacts"].get("authority_grant")
            if not isinstance(authority_path, str):
                return _terminal_transition_locked(
                    store,
                    run,
                    state="BLOCKED_NO_SHIP",
                    reason_codes=("authority_resume_evidence_missing",),
                )
            frozen_grant = store.read_json(authority_path)
            if frozen_grant != grant:
                return _terminal_transition_locked(
                    store,
                    run,
                    state="REJECT",
                    reason_codes=("authority_replay_bytes_changed",),
                )
            if manifest["profile"] == "local_no_egress":
                return _admit_local_oci(store, run, manifest, frozen_grant)
            return _admit_external_broker(
                store,
                run,
                manifest,
                grant=frozen_grant,
                broker_attestation=broker_attestation,
            )
        try:
            _validate_authority_grant(
                grant,
                run=run,
                manifest=manifest,
                now=datetime.now(timezone.utc),
            )
        except P0CalibrationError as exc:
            return _terminal_transition_locked(
                store,
                run,
                state="BLOCKED_NO_SHIP",
                reason_codes=("authority_invalid",),
                details={"error": _bounded_error(exc)},
            )
        authority_hash = _sha256_json(grant)
        grant_path = f"authority/grant-{grant['grant_id']}.json"
        host_authorization = _build_host_authorization(
            store,
            run=run,
            authority_hash=authority_hash,
        )
        host_authorization_path = "authority/host-authorization.json"
        # Persist valid authority before the potentially long-running probe.
        run = _commit_transition(
            store,
            current=run,
            expected_generation=run.generation,
            expected_head=run.head_transition_hash,
            target_state=run.state,
            event_type="authority_validated",
            updates={
                "authority_hash": authority_hash,
                "artifacts": {
                    **run.payload["artifacts"],
                    "authority_grant": grant_path,
                    "host_authorization": host_authorization_path,
                },
            },
            artifacts=[
                (grant_path, grant),
                (host_authorization_path, host_authorization),
            ],
        )
        if manifest["profile"] == "local_no_egress":
            return _admit_local_oci(store, run, manifest, grant)
        return _admit_external_broker(
            store,
            run,
            manifest,
            grant=grant,
            broker_attestation=broker_attestation,
        )


def _admit_local_oci(
    store: ProtectedArtifactStore,
    run: P0CalibrationRun,
    manifest: Mapping[str, Any],
    grant: Mapping[str, Any],
) -> P0CalibrationRun:
    if grant["profile"] != "local_no_egress":
        current = _load_run_locked(store)
        return _terminal_transition_locked(
            store,
            current,
            state="BLOCKED_NO_SHIP",
            reason_codes=("authority_profile_mismatch",),
        )
    try:
        from .documentation_calibration_broker import (
            OciAdmissionProbeRequest,
            OciRuntimeConfig,
            create_oci_admission_probe_environment,
            execute_oci_admission_probe,
        )

        config = OciRuntimeConfig.from_execution_manifest(manifest)
        probe_id = "probe-" + uuid.uuid4().hex
        with create_oci_admission_probe_environment(
            probe_id=probe_id
        ) as probe_environment:
            request = OciAdmissionProbeRequest.create(
                cohort_id=run.cohort_id,
                probe_id=probe_id,
                authority_hash=str(run.payload["authority_hash"]),
                probe_environment=probe_environment,
                output_limit_bytes=config.output_limits.result_bytes,
            )
            request_payload = request.to_dict()
            request_path = f"authority/probe-request-{probe_id}.json"
            current = _load_run_locked(store)
            if current.generation != run.generation:
                raise P0CalibrationTransitionError(
                    "Calibration generation changed before admission probe."
                )
            run = _commit_transition(
                store,
                current=current,
                expected_generation=current.generation,
                expected_head=current.head_transition_hash,
                target_state=current.state,
                event_type="admission_probe_started",
                updates={
                    "artifacts": {
                        **current.payload["artifacts"],
                        "admission_probe_request": request_path,
                    }
                },
                artifacts=[(request_path, request_payload)],
                details={
                    "probe_id": probe_id,
                    "request_hash": request.request_hash,
                },
            )
            with tempfile.TemporaryDirectory(
                prefix=f"llm-wiki-{run.cohort_id[:8]}-probe-"
            ) as output:
                outcome = execute_oci_admission_probe(
                    config,
                    request_path=store.root / request_path,
                    output_dir=Path(output),
                    probe_environment=probe_environment,
                )
    except Exception as exc:
        # The broker deliberately uses ValueError-derived failures; broad
        # containment here ensures unavailable enforcement never escapes as an
        # accidentally resumable cohort.
        current = _load_run_locked(store)
        return _terminal_transition_locked(
            store,
            current,
            state="BLOCKED_NO_SHIP",
            reason_codes=("isolation_enforcement_unavailable",),
            details={"error": _bounded_error(exc)},
        )

    current = _load_run_locked(store)
    control_failure = _recheck_bound_controls(store, current)
    if control_failure is not None:
        return _terminal_transition_locked(
            store,
            current,
            state="REJECT",
            reason_codes=("source_or_control_mutation",),
            details={"error": control_failure},
        )
    authority_failure = _pre_admission_authority_freshness_failure(store, current)
    if authority_failure is not None:
        return _terminal_transition_locked(
            store,
            current,
            state="BLOCKED_NO_SHIP",
            reason_codes=("authority_no_longer_valid",),
            details={"error": authority_failure},
        )
    run = current
    process_evidence = {
        "started": outcome.process.started,
        "returncode": outcome.process.returncode,
        "timed_out": outcome.process.timed_out,
        "error": outcome.process.error,
        "stdout_sha256": outcome.process.stdout_sha256,
        "stdout_bytes": outcome.process.stdout_bytes,
        "stdout_truncated": outcome.process.stdout_truncated,
        "stderr_sha256": outcome.process.stderr_sha256,
        "stderr_bytes": outcome.process.stderr_bytes,
        "stderr_truncated": outcome.process.stderr_truncated,
        "command_hash": outcome.command_hash,
        "cleanup_status": outcome.cleanup_status,
        "execution_status": outcome.execution_status,
    }
    probe_execution = {
        "schema_version": P0_CALIBRATION_ADMISSION_SCHEMA_VERSION,
        "record_type": "isolation_probe_execution",
        "cohort_id": run.cohort_id,
        "probe_id": probe_id,
        "request_hash": outcome.request_hash,
        "result_hash": outcome.result_hash,
        "passed": outcome.passed,
        "process": process_evidence,
        "error": outcome.error,
    }
    probe_path = f"authority/probe-result-{probe_id}.json"
    execution_path = f"authority/probe-execution-{probe_id}.json"
    probe_result = outcome.result.to_dict() if outcome.result is not None else None
    if not outcome.passed or outcome.result is None:
        failed_artifacts: list[tuple[str, Mapping[str, Any]]] = [
            (execution_path, probe_execution)
        ]
        if probe_result is not None:
            failed_artifacts.append((probe_path, probe_result))
        current = _load_run_locked(store)
        return _commit_transition(
            store,
            current=current,
            expected_generation=current.generation,
            expected_head=current.head_transition_hash,
            target_state="BLOCKED_NO_SHIP",
            event_type="admission_probe_failed",
            artifacts=failed_artifacts,
            reason_codes=("isolation_probe_failed",),
            details={"execution_status": outcome.execution_status},
        )
    assert probe_result is not None
    access_audit = {
        "schema_version": P0_CALIBRATION_ACCESS_EVENT_SCHEMA_VERSION,
        "cohort_id": run.cohort_id,
        "probe_id": probe_id,
        "events": [
            {
                "role": "admission-probe",
                "capability": event.probe,
                "target_id": event.target_id,
                "target_sha256": event.target_sha256,
                "attempted": event.attempted,
                "outcome": event.outcome,
                "evidence": dict(event.evidence),
                "detail": event.detail,
            }
            for event in outcome.result.access_events
        ],
    }
    access_audit_hash = _sha256_json(access_audit)
    attestation = {
        "schema_version": P0_CALIBRATION_ISOLATION_ATTESTATION_SCHEMA_VERSION,
        "attestation_id": "attestation-" + uuid.uuid4().hex,
        "cohort_id": run.cohort_id,
        "profile": "local_no_egress",
        "authority_hash": run.payload["authority_hash"],
        "execution_manifest_hash": run.payload["execution_manifest_hash"],
        "evidence_bundle_hash": run.payload["evidence_bundle_hash"],
        "issued_at": _utc_now(),
        "expires_at": grant["expires_at"],
        "runtime": {
            "kind": config.runtime,
            "executable_sha256": config.executable_sha256,
            "worker_image": config.worker.image,
            "probe_image": config.probe.image,
            "network": "none",
        },
        "access_audit_hash": access_audit_hash,
        "routes": [],
        "authentication": {
            "method": "host-protected-local-oci-probe",
            "principal": config.runtime,
            "reference": probe_id,
            "verified_by_host": True,
        },
    }
    _validate_isolation_attestation(
        attestation,
        run=run,
        manifest=manifest,
        authority_hash=run.payload["authority_hash"],
    )
    attestation_hash = _sha256_json(attestation)
    admission = {
        "schema_version": P0_CALIBRATION_ADMISSION_SCHEMA_VERSION,
        "cohort_id": run.cohort_id,
        "profile": "local_no_egress",
        "authority_hash": run.payload["authority_hash"],
        "attestation_hash": attestation_hash,
        "access_audit_hash": access_audit_hash,
        "admitted": True,
    }
    current = _load_run_locked(store)
    return _commit_transition(
        store,
        current=current,
        expected_generation=current.generation,
        expected_head=current.head_transition_hash,
        target_state="ADMISSION_AUTHORIZED",
        event_type="admission_authorized",
        updates={
            "attestation_hash": attestation_hash,
            "artifacts": {
                **current.payload["artifacts"],
                "probe_result": probe_path,
                "probe_execution": execution_path,
                "access_audit": "authority/access-audit.json",
                "isolation_attestation": "authority/isolation-attestation.json",
                "admission": "authority/admission.json",
            },
            "limitations": [
                "Admission authorizes pre-labeling intake only.",
                "No labels, scores, weights, candidate policy, or default-policy change exist.",
            ],
        },
        artifacts=[
            (probe_path, probe_result),
            (execution_path, probe_execution),
            ("authority/access-audit.json", access_audit),
            ("authority/isolation-attestation.json", attestation),
            ("authority/admission.json", admission),
        ],
    )


def _admit_external_broker(
    store: ProtectedArtifactStore,
    run: P0CalibrationRun,
    manifest: Mapping[str, Any],
    *,
    grant: Mapping[str, Any],
    broker_attestation: Mapping[str, Any] | None,
) -> P0CalibrationRun:
    try:
        if broker_attestation is None:
            raise P0CalibrationSchemaError(
                "external_authorized requires a broker attestation."
            )
        attestation = _json_round_trip(broker_attestation)
        _validate_isolation_attestation(
            attestation,
            run=run,
            manifest=manifest,
            authority_hash=run.payload["authority_hash"],
        )
        attestation_hash = _sha256_json(attestation)
        broker_authentication = _authenticate_external_attestation(
            run=run,
            grant=grant,
            manifest=manifest,
            attestation=attestation,
            attestation_hash=attestation_hash,
        )
    except P0CalibrationError as exc:
        current = _load_run_locked(store)
        return _terminal_transition_locked(
            store,
            current,
            state="BLOCKED_NO_SHIP",
            reason_codes=("external_broker_attestation_invalid",),
            details={"error": _bounded_error(exc)},
        )
    current = _load_run_locked(store)
    control_failure = _recheck_bound_controls(store, current)
    if control_failure is not None:
        return _terminal_transition_locked(
            store,
            current,
            state="REJECT",
            reason_codes=("source_or_control_mutation",),
            details={"error": control_failure},
        )
    authority_failure = _pre_admission_authority_freshness_failure(store, current)
    if authority_failure is not None:
        return _terminal_transition_locked(
            store,
            current,
            state="BLOCKED_NO_SHIP",
            reason_codes=("authority_no_longer_valid",),
            details={"error": authority_failure},
        )
    run = current
    broker_authentication_hash = _sha256_json(broker_authentication)
    admission = {
        "schema_version": P0_CALIBRATION_ADMISSION_SCHEMA_VERSION,
        "cohort_id": run.cohort_id,
        "profile": "external_authorized",
        "authority_hash": run.payload["authority_hash"],
        "attestation_hash": attestation_hash,
        "access_audit_hash": attestation["access_audit_hash"],
        "broker_authentication_hash": broker_authentication_hash,
        "admitted": True,
    }
    return _commit_transition(
        store,
        current=run,
        expected_generation=run.generation,
        expected_head=run.head_transition_hash,
        target_state="ADMISSION_AUTHORIZED",
        event_type="admission_authorized",
        updates={
            "attestation_hash": attestation_hash,
            "artifacts": {
                **run.payload["artifacts"],
                "isolation_attestation": "authority/isolation-attestation.json",
                "broker_authentication": (
                    "authority/external-broker-authentication.json"
                ),
                "admission": "authority/admission.json",
            },
            "limitations": [
                "External admission requires a matching authenticated broker receipt for every result.",
                "No provider credential or adapter is included in this package.",
            ],
        },
        artifacts=[
            ("authority/isolation-attestation.json", attestation),
            (
                "authority/external-broker-authentication.json",
                broker_authentication,
            ),
            ("authority/admission.json", admission),
        ],
    )


def build_calibration_agent_packet(
    root: str | Path,
    *,
    role: str,
) -> P0CalibrationAgentPacket:
    """Build and persist one bounded role packet.

    Intake packets share the same evidence and task contract but carry distinct
    role and packet identities.  Verifier packets are unavailable until all
    three independently produced intake proposals are frozen.
    """

    role = _require_choice(role, CALIBRATION_ROLES, "packet role")
    store = _open_store(root)
    with store.lock():
        run = _load_run_locked(store)
        if run.state not in {"ADMISSION_AUTHORIZED", "INTAKE_OPEN"}:
            raise P0CalibrationTransitionError(
                "Packets require an admitted, nonterminal cohort."
            )
        control_failure = _recheck_bound_controls(store, run)
        if control_failure is not None:
            _terminal_transition_locked(
                store,
                run,
                state="REJECT",
                reason_codes=("source_or_control_mutation",),
                details={"error": control_failure},
            )
            raise P0CalibrationIntegrityError(control_failure)
        authority_failure = _authority_freshness_failure(store, run)
        if authority_failure is not None:
            _terminal_transition_locked(
                store,
                run,
                state="BLOCKED_NO_SHIP",
                reason_codes=("authority_no_longer_valid",),
                details={"error": authority_failure},
            )
            raise P0CalibrationTransitionError(authority_failure)
        role_state = run.payload["roles"][role]
        if role_state["status"] == "packet_issued":
            path = _packet_path_for_role_state(run, role_state, role=role)
            packet = P0CalibrationAgentPacket.from_dict(store.read_json(path))
            _assert_outbound_payload_safe(
                packet.payload,
                bound_roots=_bound_outbound_roots(store),
            )
            if _sha256_json(packet.payload) != role_state["current_packet_hash"]:
                _terminal_transition_locked(
                    store,
                    run,
                    state="REJECT",
                    reason_codes=("packet_artifact_tampered",),
                )
                raise P0CalibrationIntegrityError(
                    f"Frozen packet for {role} no longer matches its hash."
                )
            return packet
        if role_state["status"] in {"dispatch_started", "result_frozen"}:
            raise P0CalibrationTransitionError(
                f"Role {role} already has {role_state['status']}."
            )
        if role == "verifier":
            incomplete = [
                intake_role
                for intake_role in INTAKE_ROLES
                if run.payload["roles"][intake_role]["status"] != "result_frozen"
            ]
            if incomplete:
                raise P0CalibrationTransitionError(
                    "Verifier packet requires all three frozen intake results: "
                    + ", ".join(incomplete)
                )
        attempt = int(role_state["attempts"]) + 1
        if attempt > 2:
            return_packet_error = _terminal_transition_locked(
                store,
                run,
                state="BLOCKED_NO_SHIP",
                reason_codes=("role_attempts_exhausted",),
                details={"role": role},
            )
            del return_packet_error
            raise P0CalibrationTransitionError(
                f"Role {role} exhausted its two-attempt limit."
            )
        manifest = store.read_json(run.payload["artifacts"]["execution_manifest"])
        manifest_budgets = _required_mapping(
            manifest.get("budgets"), "frozen execution manifest budgets"
        )
        issued_attempts = sum(
            int(run.payload["roles"][candidate]["attempts"])
            for candidate in CALIBRATION_ROLES
        )
        max_total_calls = _require_positive_int(
            manifest_budgets.get("max_total_calls"),
            "frozen execution manifest max_total_calls",
        )
        if issued_attempts >= max_total_calls:
            _terminal_transition_locked(
                store,
                run,
                state="BLOCKED_NO_SHIP",
                reason_codes=("dispatch_budget_exhausted",),
                details={
                    "issued_attempts": issued_attempts,
                    "max_total_calls": max_total_calls,
                },
            )
            raise P0CalibrationTransitionError(
                "The frozen execution manifest call budget is exhausted."
            )
        evidence = store.read_json(
            run.payload["artifacts"]["evidence_bundle"],
            max_bytes=_MAX_BUNDLE_BYTES,
        )
        packet_id = str(uuid.uuid4())
        idempotency_key = (
            f"{run.cohort_id}:{role}:{attempt}:{packet_id.replace('-', '')[:16]}"
        )
        outbound_roots = _bound_outbound_roots(store)
        proposal_inputs = (
            _frozen_intake_proposals(store, run) if role == "verifier" else []
        )
        packet_payload = {
            "schema_version": P0_CALIBRATION_AGENT_PACKET_SCHEMA_VERSION,
            "cohort_id": run.cohort_id,
            "packet_id": packet_id,
            "role": role,
            "attempt": attempt,
            "idempotency_key": idempotency_key,
            "authority_hash": run.payload["authority_hash"],
            "attestation_hash": run.payload["attestation_hash"],
            "evidence_bundle_hash": run.payload["evidence_bundle_hash"],
            "objective": (
                "Independently infer a source-supported project purpose, audiences, "
                "capabilities, tasks, journeys, contradictions, unknowns, and limitations."
                if role != "verifier"
                else "Verify the three independent proposals against source citations and freeze a coherent pre-labeling intake."
            ),
            "evidence_bundle": evidence,
            "intake_proposals": proposal_inputs,
            "result_contract": _result_contract_for_role(role),
            "budgets": _packet_budgets(manifest_budgets),
            "forbidden_actions": [
                "read controller state, source roots, credentials, holdouts, or another role output",
                "use network access or a container-engine socket",
                "invent, classify, label, score, rank, or promote a flow",
                "write outside the role-specific output directory",
                "stage, commit, push, deploy, release, or publish",
            ],
        }
        _assert_outbound_payload_safe(
            packet_payload,
            bound_roots=outbound_roots,
        )
        _validate_agent_packet(packet_payload)
        packet_bytes = len(canonical_json_bytes(packet_payload))
        packet_limit = min(
            CALIBRATION_CONTROLLER_MAX_PACKET_BYTES,
            _require_positive_int(
                manifest_budgets.get("max_packet_bytes"),
                "frozen execution manifest max_packet_bytes",
            ),
        )
        if packet_bytes > packet_limit:
            _terminal_transition_locked(
                store,
                run,
                state="BLOCKED_NO_SHIP",
                reason_codes=("packet_size_limit_exceeded",),
                details={
                    "role": role,
                    "packet_bytes": packet_bytes,
                    "packet_limit": packet_limit,
                },
            )
            raise P0CalibrationSchemaError(
                f"Role packet exceeds the frozen {packet_limit}-byte limit."
            )
        packet_hash = _sha256_json(packet_payload)
        packet_path = f"packets/{role}/attempt-{attempt:02d}-{packet_id}.json"
        roles = _json_round_trip(run.payload["roles"])
        roles[role] = {
            **role_state,
            "attempts": attempt,
            "status": "packet_issued",
            "current_packet_id": packet_id,
            "current_packet_hash": packet_hash,
            "packet_generation": run.generation + 1,
            "result_id": None,
            "receipt_id": None,
            "idempotency_key": idempotency_key,
        }
        artifacts = _json_round_trip(run.payload["artifacts"])
        packet_artifacts = _json_round_trip(artifacts.get("packets", {}))
        packet_artifacts[role] = packet_path
        artifacts["packets"] = packet_artifacts
        target_state = (
            "INTAKE_OPEN" if run.state == "ADMISSION_AUTHORIZED" else run.state
        )
        committed = _commit_transition(
            store,
            current=run,
            expected_generation=run.generation,
            expected_head=run.head_transition_hash,
            target_state=target_state,
            event_type="packet_issued",
            updates={"roles": roles, "artifacts": artifacts},
            artifacts=[(packet_path, packet_payload)],
            details={"role": role, "attempt": attempt, "packet_hash": packet_hash},
        )
        del committed
        return P0CalibrationAgentPacket.from_dict(packet_payload)


def _packet_budgets(budgets: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "max_attempts": 2,
        "max_packet_bytes": int(budgets["max_packet_bytes"]),
        "max_result_bytes": int(budgets["max_result_bytes"]),
    }


def _result_contract_for_role(role: str) -> dict[str, Any]:
    claim = {
        "fields": ["claim_id", "statement", "citations"],
        "citation_source": "evidence_bundle.source_excerpts[].citation_id",
        "minimum_citations": 1,
    }
    semantic_fields = [
        "purpose",
        "audiences",
        "capabilities",
        "tasks",
        "journeys",
        "contradictions",
        "unknowns",
        "limitations",
    ]
    contract: dict[str, Any] = {
        "schema_version": P0_CALIBRATION_AGENT_RESULT_SCHEMA_VERSION,
        "status": "complete",
        "payload_field": "verification" if role == "verifier" else "proposal",
        "required_semantic_fields": semantic_fields
        + (
            [
                "primary_journey_claim_id",
                "accepted_claims",
                "rejected_claims",
            ]
            if role == "verifier"
            else []
        ),
        "claim_contract": claim,
        "purpose_cardinality": "exactly_one",
        "other_field_cardinality": "zero_or_more",
    }
    if role == "verifier":
        contract["primary_journey_contract"] = {
            "field": "primary_journey_claim_id",
            "references": "verification.journeys[].claim_id",
            "cardinality": "exactly_one",
        }
        contract["disposition_claim_contract"] = {
            "fields": [
                "claim_id",
                "statement",
                "citations",
                "proposal_claim_ids",
            ],
            "proposal_claim_id_format": "intake-role/claim-id",
            "coverage": "every proposal claim exactly once across accepted and rejected",
        }
    return contract


def _frozen_intake_proposals(
    store: ProtectedArtifactStore, run: P0CalibrationRun
) -> list[dict[str, Any]]:
    proposals = []
    outbound_roots = _bound_outbound_roots(store)
    result_paths = run.payload["artifacts"].get("results", {})
    if not isinstance(result_paths, Mapping):
        raise P0CalibrationIntegrityError("Frozen intake result index is malformed.")
    for role in INTAKE_ROLES:
        path = result_paths.get(role)
        if not isinstance(path, str):
            raise P0CalibrationIntegrityError(
                f"Frozen intake result for {role} is missing."
            )
        result = P0CalibrationAgentResult.from_dict(
            store.read_json(path, max_bytes=_MAX_RESULT_BYTES)
        )
        proposal_record = {
            "role": role,
            "result_id": result.result_id,
            "proposal": _json_round_trip(result.payload["proposal"]),
        }
        sanitized, redactions = _sanitize_outbound_value(
            proposal_record,
            bound_roots=outbound_roots,
        )
        if not isinstance(sanitized, dict):
            raise P0CalibrationIntegrityError(
                f"Sanitized intake proposal for {role} is malformed."
            )
        sanitized["outbound_safety"] = {
            "status": "redacted" if redactions else "no_scanner_matches",
            "scanner": "deterministic-credential-and-host-path-denylist-v1",
            "limitation": (
                "Pattern scanning reduces known credential and host-path leakage; "
                "it is not proof that arbitrary source text contains no secret."
            ),
            "redactions": redactions,
        }
        _assert_outbound_payload_safe(
            sanitized,
            bound_roots=outbound_roots,
        )
        proposals.append(sanitized)
    return proposals


def _packet_path_for_role_state(
    run: P0CalibrationRun,
    role_state: Mapping[str, Any],
    *,
    role: str,
) -> str:
    packets = run.payload["artifacts"].get("packets", {})
    if not isinstance(packets, Mapping) or not isinstance(packets.get(role), str):
        raise P0CalibrationIntegrityError(
            f"Run lost the current packet path for {role}."
        )
    return str(packets[role])


def _build_host_authorization(
    store: ProtectedArtifactStore,
    *,
    run: P0CalibrationRun,
    authority_hash: str,
) -> dict[str, Any]:
    """Derive operator trust from protected host state, not submitted JSON."""

    try:
        protection = store.verify_access_protection()
    except ProtectedArtifactError as exc:
        raise P0CalibrationIntegrityError(
            f"Host authorization protection is unavailable: {exc}"
        ) from exc
    record = {
        "schema_version": P0_CALIBRATION_ADMISSION_SCHEMA_VERSION,
        "record_type": "host_authorization",
        "cohort_id": run.cohort_id,
        "decision_scope": P0_CALIBRATION_DECISION_SCOPE,
        "authority_hash": authority_hash,
        "execution_manifest_hash": run.payload["execution_manifest_hash"],
        "evidence_bundle_hash": run.payload["evidence_bundle_hash"],
        "recorded_at": _utc_now(),
        "protection": protection,
    }
    _validate_host_authorization(
        store,
        record,
        run=run,
        expected_authority_hash=authority_hash,
    )
    return record


def _validate_host_authorization(
    store: ProtectedArtifactStore,
    payload: Mapping[str, Any],
    *,
    run: P0CalibrationRun,
    expected_authority_hash: str | None = None,
) -> None:
    _require_exact_fields(
        payload,
        {
            "schema_version",
            "record_type",
            "cohort_id",
            "decision_scope",
            "authority_hash",
            "execution_manifest_hash",
            "evidence_bundle_hash",
            "recorded_at",
            "protection",
        },
        label="host authorization",
    )
    if (
        payload.get("schema_version") != P0_CALIBRATION_ADMISSION_SCHEMA_VERSION
        or payload.get("record_type") != "host_authorization"
        or payload.get("cohort_id") != run.cohort_id
        or payload.get("decision_scope") != P0_CALIBRATION_DECISION_SCOPE
        or payload.get("authority_hash")
        != (
            run.payload["authority_hash"]
            if expected_authority_hash is None
            else expected_authority_hash
        )
        or payload.get("execution_manifest_hash")
        != run.payload["execution_manifest_hash"]
        or payload.get("evidence_bundle_hash") != run.payload["evidence_bundle_hash"]
    ):
        raise P0CalibrationIntegrityError(
            "Host authorization does not bind the frozen cohort."
        )
    _require_timestamp(payload.get("recorded_at"), "host authorization recorded_at")
    protection = _required_mapping(
        payload.get("protection"), "host authorization protection"
    )
    try:
        current = store.verify_access_protection()
    except ProtectedArtifactError as exc:
        raise P0CalibrationIntegrityError(
            f"Host authorization protection is unavailable: {exc}"
        ) from exc
    if dict(protection) != current:
        raise P0CalibrationIntegrityError(
            "Protected-root host identity or access mechanism changed."
        )


def _authenticate_external_attestation(
    *,
    run: P0CalibrationRun,
    grant: Mapping[str, Any],
    manifest: Mapping[str, Any],
    attestation: Mapping[str, Any],
    attestation_hash: str,
) -> dict[str, Any]:
    """Require host-derived authentication for an external attestation."""

    try:
        from .documentation_calibration_host_broker import (
            require_attestation_authentication,
        )

        proof = require_attestation_authentication(
            cohort_id=run.cohort_id,
            authority_grant=grant,
            execution_manifest=manifest,
            attestation=attestation,
            attestation_hash=attestation_hash,
        )
    except (ImportError, TypeError, ValueError) as exc:
        raise P0CalibrationSchemaError(
            f"External broker authentication failed: {exc}"
        ) from exc
    record = {
        "schema_version": P0_CALIBRATION_ADMISSION_SCHEMA_VERSION,
        "record_type": "external_broker_attestation_authentication",
        "proof": proof.to_dict(),
    }
    _validate_external_broker_authentication(
        record,
        run=run,
        attestation=attestation,
        attestation_hash=attestation_hash,
    )
    return record


def _validate_external_broker_authentication(
    payload: Mapping[str, Any],
    *,
    run: P0CalibrationRun,
    attestation: Mapping[str, Any],
    attestation_hash: str,
    receipt: Mapping[str, Any] | None = None,
    result_hash: str | None = None,
) -> None:
    receipt_mode = receipt is not None
    _require_exact_fields(
        payload,
        {"schema_version", "record_type", "proof"},
        label="external broker authentication",
    )
    expected_type = (
        "external_broker_receipt_authentication"
        if receipt_mode
        else "external_broker_attestation_authentication"
    )
    if (
        payload.get("schema_version") != P0_CALIBRATION_ADMISSION_SCHEMA_VERSION
        or payload.get("record_type") != expected_type
    ):
        raise P0CalibrationSchemaError(
            "External broker authentication record type is invalid."
        )
    proof = _required_mapping(
        payload.get("proof"), "external broker authentication proof"
    )
    _require_exact_fields(
        proof,
        {
            "proof_kind",
            "authenticator_id",
            "broker_id",
            "broker_session",
            "principal",
            "reference",
            "cohort_id",
            "expires_at",
            "authority_hash",
            "execution_manifest_hash",
            "evidence_bundle_hash",
            "attestation_hash",
            "receipt_hash",
            "result_hash",
            "packet_hash",
            "idempotency_key",
            "route_id",
            "role",
            "attempt",
        },
        label="external broker authentication proof",
    )
    for name in (
        "authenticator_id",
        "principal",
        "reference",
    ):
        _require_text(proof.get(name), f"external broker proof {name}")
    runtime = _required_mapping(attestation.get("runtime"), "attestation runtime")
    authentication = _required_mapping(
        attestation.get("authentication"), "attestation authentication"
    )
    expected = {
        "proof_kind": "receipt" if receipt_mode else "attestation",
        "broker_id": runtime.get("broker_id"),
        "broker_session": authentication.get("reference"),
        "cohort_id": run.cohort_id,
        "expires_at": attestation.get("expires_at"),
        "authority_hash": run.payload["authority_hash"],
        "execution_manifest_hash": run.payload["execution_manifest_hash"],
        "evidence_bundle_hash": run.payload["evidence_bundle_hash"],
        "attestation_hash": attestation_hash,
    }
    for name, value in expected.items():
        if proof.get(name) != value:
            raise P0CalibrationSchemaError(
                f"External broker proof {name} does not match admission."
            )
    if not receipt_mode:
        for name in (
            "receipt_hash",
            "result_hash",
            "packet_hash",
            "idempotency_key",
            "route_id",
            "role",
            "attempt",
        ):
            if proof.get(name) is not None:
                raise P0CalibrationSchemaError(
                    f"Attestation authentication proof cannot bind {name}."
                )
        return
    assert receipt is not None
    receipt_expected = {
        "receipt_hash": _sha256_json(receipt),
        "result_hash": result_hash,
        "packet_hash": receipt.get("packet_hash"),
        "idempotency_key": receipt.get("idempotency_key"),
        "route_id": receipt.get("route_id"),
        "role": receipt.get("role"),
        "attempt": receipt.get("attempt"),
    }
    for name, value in receipt_expected.items():
        if proof.get(name) != value:
            raise P0CalibrationSchemaError(
                f"External broker receipt proof {name} does not match."
            )


def _authenticate_external_receipt(
    *,
    run: P0CalibrationRun,
    manifest: Mapping[str, Any],
    attestation: Mapping[str, Any],
    receipt: Mapping[str, Any],
    result: Mapping[str, Any],
) -> dict[str, Any]:
    """Require a host-authenticated proof for one external receipt."""

    receipt_hash = _sha256_json(receipt)
    result_hash = _sha256_json(result)
    try:
        from .documentation_calibration_host_broker import (
            HostBrokerAuthenticationError,
            HostBrokerAuthenticationUnavailable,
            require_receipt_authentication,
        )
    except ImportError as exc:
        raise _ExternalBrokerAuthenticationUnavailable(
            f"External host-broker authentication is unavailable: {exc}"
        ) from exc
    try:
        proof = require_receipt_authentication(
            cohort_id=run.cohort_id,
            execution_manifest=manifest,
            attestation=attestation,
            receipt=receipt,
            receipt_hash=receipt_hash,
            result=result,
            result_hash=result_hash,
        )
    except HostBrokerAuthenticationUnavailable as exc:
        raise _ExternalBrokerAuthenticationUnavailable(str(exc)) from exc
    except HostBrokerAuthenticationError as exc:
        raise P0CalibrationSchemaError(
            f"External receipt authentication failed: {exc}"
        ) from exc
    record = {
        "schema_version": P0_CALIBRATION_ADMISSION_SCHEMA_VERSION,
        "record_type": "external_broker_receipt_authentication",
        "proof": proof.to_dict(),
    }
    _validate_external_broker_authentication(
        record,
        run=run,
        attestation=attestation,
        attestation_hash=_require_sha256(
            run.payload["attestation_hash"], "run attestation_hash"
        ),
        receipt=receipt,
        result_hash=result_hash,
    )
    return record


def _validate_authority_grant(
    payload: Mapping[str, Any],
    *,
    run: P0CalibrationRun,
    manifest: Mapping[str, Any],
    now: datetime,
) -> None:
    _require_exact_fields(
        payload,
        {
            "schema_version",
            "grant_id",
            "cohort_id",
            "decision_scope",
            "profile",
            "evidence_bundle_hash",
            "execution_manifest_hash",
            "allowed_roles",
            "budgets",
            "external_routes",
            "issued_at",
            "expires_at",
            "revocation",
            "authentication",
        },
        label="authority grant",
    )
    if payload.get("schema_version") != P0_CALIBRATION_AUTHORITY_GRANT_SCHEMA_VERSION:
        raise P0CalibrationSchemaError("Unsupported authority-grant schema_version.")
    _portable_id(payload.get("grant_id"), "authority grant_id")
    if payload.get("cohort_id") != run.cohort_id:
        raise P0CalibrationSchemaError("Authority grant is bound to another cohort.")
    if payload.get("decision_scope") != P0_CALIBRATION_DECISION_SCOPE:
        raise P0CalibrationSchemaError(
            "Authority grant decision_scope does not authorize documentation "
            "calibration admission."
        )
    if payload.get("profile") != run.payload["admission_profile"]:
        raise P0CalibrationSchemaError(
            "Authority grant profile does not match the frozen manifest."
        )
    if payload.get("evidence_bundle_hash") != run.payload["evidence_bundle_hash"]:
        raise P0CalibrationSchemaError(
            "Authority grant evidence hash does not match the cohort."
        )
    if payload.get("execution_manifest_hash") != run.payload["execution_manifest_hash"]:
        raise P0CalibrationSchemaError(
            "Authority grant execution-manifest hash does not match."
        )
    if payload.get("allowed_roles") != list(CALIBRATION_ROLES):
        raise P0CalibrationSchemaError(
            "Authority grant must bind the exact lifecycle role inventory."
        )
    if payload.get("budgets") != manifest.get("budgets"):
        raise P0CalibrationSchemaError(
            "Authority grant budgets do not match the frozen execution manifest."
        )
    if payload.get("external_routes") != manifest.get("external_routes"):
        raise P0CalibrationSchemaError(
            "Authority grant external routes do not match the frozen manifest."
        )
    issued = _parse_timestamp(payload.get("issued_at"), "authority issued_at")
    expires = _parse_timestamp(payload.get("expires_at"), "authority expires_at")
    if expires <= issued:
        raise P0CalibrationSchemaError(
            "Authority expires_at must be later than issued_at."
        )
    if issued > now:
        raise P0CalibrationSchemaError("Authority grant is not yet valid.")
    if now >= expires:
        raise P0CalibrationSchemaError("Authority grant has expired.")
    revocation = _required_mapping(payload.get("revocation"), "authority revocation")
    _require_exact_fields(
        revocation,
        {"reference", "revoked"},
        label="authority revocation",
    )
    _require_text(revocation.get("reference"), "authority revocation reference")
    if _require_bool(revocation.get("revoked"), "authority revoked"):
        raise P0CalibrationSchemaError("Authority grant is revoked.")
    authentication = _required_mapping(
        payload.get("authentication"), "authority authentication"
    )
    _require_exact_fields(
        authentication,
        {"method", "principal", "reference", "verified_by_host"},
        label="authority authentication",
    )
    if authentication.get("method") != "host-protected-operator":
        raise P0CalibrationSchemaError(
            "Authority must use the host-protected operator trust method."
        )
    _require_text(authentication.get("principal"), "authority principal")
    _require_text(authentication.get("reference"), "authority reference")
    if authentication.get("verified_by_host") is not True:
        raise P0CalibrationSchemaError(
            "Authority grant was not authenticated by the host."
        )


def _validate_isolation_attestation(
    payload: Mapping[str, Any],
    *,
    run: P0CalibrationRun,
    manifest: Mapping[str, Any],
    authority_hash: Any,
) -> None:
    _require_exact_fields(
        payload,
        {
            "schema_version",
            "attestation_id",
            "cohort_id",
            "profile",
            "authority_hash",
            "execution_manifest_hash",
            "evidence_bundle_hash",
            "issued_at",
            "expires_at",
            "runtime",
            "access_audit_hash",
            "routes",
            "authentication",
        },
        label="isolation attestation",
    )
    if (
        payload.get("schema_version")
        != P0_CALIBRATION_ISOLATION_ATTESTATION_SCHEMA_VERSION
    ):
        raise P0CalibrationSchemaError(
            "Unsupported isolation-attestation schema_version."
        )
    _portable_id(payload.get("attestation_id"), "attestation_id")
    for field_name, expected in (
        ("cohort_id", run.cohort_id),
        ("profile", run.payload["admission_profile"]),
        ("authority_hash", authority_hash),
        ("execution_manifest_hash", run.payload["execution_manifest_hash"]),
        ("evidence_bundle_hash", run.payload["evidence_bundle_hash"]),
    ):
        if payload.get(field_name) != expected:
            raise P0CalibrationSchemaError(
                f"Isolation attestation {field_name} does not match the cohort."
            )
    issued = _parse_timestamp(payload.get("issued_at"), "attestation issued_at")
    expires = _parse_timestamp(payload.get("expires_at"), "attestation expires_at")
    now = datetime.now(timezone.utc)
    if issued > now or expires <= issued or now >= expires:
        raise P0CalibrationSchemaError("Isolation attestation is not currently valid.")
    runtime = _required_mapping(payload.get("runtime"), "attestation runtime")
    authentication = _required_mapping(
        payload.get("authentication"), "attestation authentication"
    )
    _require_exact_fields(
        authentication,
        {"method", "principal", "reference", "verified_by_host"},
        label="attestation authentication",
    )
    _require_text(authentication.get("principal"), "attestation principal")
    _require_text(authentication.get("reference"), "attestation reference")
    if authentication.get("verified_by_host") is not True:
        raise P0CalibrationSchemaError(
            "Isolation attestation is not authenticated by the host."
        )
    _require_sha256(payload.get("access_audit_hash"), "attestation access_audit_hash")
    routes = payload.get("routes")
    if not isinstance(routes, list):
        raise P0CalibrationSchemaError("Attestation routes must be a list.")
    if payload["profile"] == "local_no_egress":
        _require_exact_fields(
            runtime,
            {
                "kind",
                "executable_sha256",
                "worker_image",
                "probe_image",
                "network",
            },
            label="local attestation runtime",
        )
        if runtime.get("kind") != manifest["oci"]["runtime"]:
            raise P0CalibrationSchemaError(
                "Local attestation runtime does not match the manifest."
            )
        if runtime.get("executable_sha256") != manifest["oci"]["executable_sha256"]:
            raise P0CalibrationSchemaError(
                "Local attestation executable identity does not match."
            )
        if (
            runtime.get("worker_image") != manifest["oci"]["worker"]["image"]
            or runtime.get("probe_image") != manifest["oci"]["probe"]["image"]
            or runtime.get("network") != "none"
            or routes
        ):
            raise P0CalibrationSchemaError(
                "Local attestation image/network bindings do not match."
            )
        if authentication.get("method") != "host-protected-local-oci-probe":
            raise P0CalibrationSchemaError(
                "Local attestation authentication method is unsupported."
            )
    else:
        _require_exact_fields(
            runtime,
            {"kind", "broker_id", "runtime_identity", "image_identity"},
            label="external attestation runtime",
        )
        if runtime.get("kind") != "external_broker":
            raise P0CalibrationSchemaError(
                "External attestation runtime kind is unsupported."
            )
        for name in ("broker_id", "runtime_identity", "image_identity"):
            _require_text(runtime.get(name), f"external attestation {name}")
        if routes != manifest["external_routes"]:
            raise P0CalibrationSchemaError(
                "External attestation routes do not match the frozen manifest."
            )
        if authentication.get("method") != "host-protected-external-broker":
            raise P0CalibrationSchemaError(
                "External attestation authentication method is unsupported."
            )


def _recheck_bound_controls(
    store: ProtectedArtifactStore, run: P0CalibrationRun
) -> str | None:
    try:
        bindings = store.read_json("baseline/runtime-bindings.json")
        _require_exact_fields(
            bindings,
            {
                "schema_version",
                "cohort_id",
                "control_workspaces",
                "source_roots",
                "implementation_roots",
            },
            label="runtime bindings",
        )
        if (
            bindings.get("schema_version")
            != P0_CALIBRATION_RUNTIME_BINDINGS_SCHEMA_VERSION
            or bindings.get("cohort_id") != run.cohort_id
        ):
            raise P0CalibrationIntegrityError(
                "Runtime bindings do not match the cohort."
            )
        workspaces = bindings.get("control_workspaces")
        roots = bindings.get("source_roots")
        implementation_roots = bindings.get("implementation_roots")
        if (
            not isinstance(workspaces, list)
            or len(workspaces) != 2
            or not isinstance(roots, list)
            or len(roots) != 2
            or not isinstance(implementation_roots, list)
            or implementation_roots
            != [str(path) for path in _implementation_worktree_roots()]
        ):
            raise P0CalibrationIntegrityError(
                "Runtime bindings must name the two controls/source roots and "
                "the frozen implementation worktrees."
            )
        controls = [
            _load_control_workspace(Path(value), index=index)
            for index, value in enumerate(workspaces, start=1)
        ]
        _assert_controls_match(controls)
        for index, control in enumerate(controls):
            if str(control["source_root"]) != roots[index]:
                raise P0CalibrationIntegrityError(
                    "Runtime source root binding changed."
                )
            frozen = store.read_json(f"baseline/control-{index + 1:02d}.json")
            if frozen != _portable_control_record(control, cohort_id=run.cohort_id):
                raise P0CalibrationIntegrityError(
                    f"Control {index + 1} no longer matches its frozen record."
                )
        bundle = store.read_json("evidence/bundle.json", max_bytes=_MAX_BUNDLE_BYTES)
        if _sha256_json(bundle) != run.payload["evidence_bundle_hash"]:
            raise P0CalibrationIntegrityError(
                "Frozen evidence bundle no longer matches the run."
            )
    except (P0CalibrationError, ProtectedArtifactError) as exc:
        return _bounded_error(exc)
    return None


def _bound_outbound_roots(store: ProtectedArtifactStore) -> tuple[str, ...]:
    try:
        bindings = store.read_json("baseline/runtime-bindings.json")
    except ProtectedArtifactError as exc:
        raise P0CalibrationIntegrityError(str(exc)) from exc
    controls = bindings.get("control_workspaces")
    sources = bindings.get("source_roots")
    implementation_roots = bindings.get("implementation_roots")
    if (
        not isinstance(controls, list)
        or not all(isinstance(value, str) for value in controls)
        or not isinstance(sources, list)
        or not all(isinstance(value, str) for value in sources)
        or not isinstance(implementation_roots, list)
        or not all(isinstance(value, str) for value in implementation_roots)
    ):
        raise P0CalibrationIntegrityError(
            "Runtime bindings cannot supply outbound path guards."
        )
    return _normalize_bound_roots(
        [
            store.root,
            *(Path(value) for value in controls),
            *(Path(value) for value in sources),
            *(Path(value) for value in implementation_roots),
        ]
    )


def _pre_admission_authority_freshness_failure(
    store: ProtectedArtifactStore,
    run: P0CalibrationRun,
) -> str | None:
    try:
        authority_path = run.payload["artifacts"].get("authority_grant")
        if not isinstance(authority_path, str):
            raise P0CalibrationIntegrityError("Run has no frozen authority grant.")
        grant = store.read_json(authority_path)
        manifest = store.read_json(run.payload["artifacts"]["execution_manifest"])
        _validate_authority_grant(
            grant,
            run=run,
            manifest=manifest,
            now=datetime.now(timezone.utc),
        )
        if _sha256_json(grant) != run.payload["authority_hash"]:
            raise P0CalibrationIntegrityError("Frozen authority hash changed.")
        host_authorization_path = run.payload["artifacts"].get("host_authorization")
        if not isinstance(host_authorization_path, str):
            raise P0CalibrationIntegrityError(
                "Run has no host-derived authorization evidence."
            )
        _validate_host_authorization(
            store,
            store.read_json(host_authorization_path),
            run=run,
        )
    except (P0CalibrationError, ProtectedArtifactError) as exc:
        return _bounded_error(exc)
    return None


def _authority_freshness_failure(
    store: ProtectedArtifactStore, run: P0CalibrationRun
) -> str | None:
    try:
        authority_path = run.payload["artifacts"].get("authority_grant")
        if not isinstance(authority_path, str):
            raise P0CalibrationIntegrityError("Run has no frozen authority grant.")
        grant = store.read_json(authority_path)
        manifest = store.read_json(run.payload["artifacts"]["execution_manifest"])
        _validate_authority_grant(
            grant,
            run=run,
            manifest=manifest,
            now=datetime.now(timezone.utc),
        )
        if _sha256_json(grant) != run.payload["authority_hash"]:
            raise P0CalibrationIntegrityError("Frozen authority hash changed.")
        host_authorization_path = run.payload["artifacts"].get("host_authorization")
        if not isinstance(host_authorization_path, str):
            raise P0CalibrationIntegrityError(
                "Run has no host-derived authorization evidence."
            )
        _validate_host_authorization(
            store,
            store.read_json(host_authorization_path),
            run=run,
        )
        attestation_path = run.payload["artifacts"].get("isolation_attestation")
        if not isinstance(attestation_path, str):
            raise P0CalibrationIntegrityError(
                "Run has no frozen isolation attestation."
            )
        attestation = store.read_json(attestation_path)
        _validate_isolation_attestation(
            attestation,
            run=run,
            manifest=manifest,
            authority_hash=run.payload["authority_hash"],
        )
        attestation_hash = _sha256_json(attestation)
        if attestation_hash != run.payload["attestation_hash"]:
            raise P0CalibrationIntegrityError(
                "Frozen isolation-attestation hash changed."
            )
        if run.payload["admission_profile"] == "external_authorized":
            authentication_path = run.payload["artifacts"].get("broker_authentication")
            if not isinstance(authentication_path, str):
                raise P0CalibrationIntegrityError(
                    "Run has no frozen external-broker authentication proof."
                )
            frozen_authentication = store.read_json(authentication_path)
            _validate_external_broker_authentication(
                frozen_authentication,
                run=run,
                attestation=attestation,
                attestation_hash=attestation_hash,
            )
            current_authentication = _authenticate_external_attestation(
                run=run,
                grant=grant,
                manifest=manifest,
                attestation=attestation,
                attestation_hash=attestation_hash,
            )
            if current_authentication != frozen_authentication:
                raise P0CalibrationIntegrityError(
                    "External host-broker authentication identity changed."
                )
            _revalidate_external_receipt_authentications(
                store,
                run=run,
                manifest=manifest,
                attestation=attestation,
            )
    except (P0CalibrationError, ProtectedArtifactError) as exc:
        return _bounded_error(exc)
    return None


def _has_indeterminate_admission_probe(run: P0CalibrationRun) -> bool:
    return (
        run.state == "BASELINE_FROZEN"
        and run.payload.get("authority_hash") is not None
        and isinstance(
            run.payload.get("artifacts", {}).get("admission_probe_request"),
            str,
        )
    )


def _revalidate_external_receipt_authentications(
    store: ProtectedArtifactStore,
    *,
    run: P0CalibrationRun,
    manifest: Mapping[str, Any],
    attestation: Mapping[str, Any],
) -> None:
    """Reauthenticate every frozen external result against its stored proof."""

    artifacts = _required_mapping(run.payload.get("artifacts"), "run artifacts")
    receipts = _required_mapping(artifacts.get("receipts", {}), "run receipts")
    results = _required_mapping(artifacts.get("results", {}), "run results")
    authentications = _required_mapping(
        artifacts.get("receipt_authentications", {}),
        "run receipt authentications",
    )
    attestation_hash = _require_sha256(
        run.payload["attestation_hash"], "run attestation_hash"
    )
    for role in CALIBRATION_ROLES:
        role_state = run.payload["roles"][role]
        if role_state["status"] != "result_frozen":
            continue
        receipt_path = receipts.get(role)
        result_path = results.get(role)
        receipt_id = role_state.get("receipt_id")
        authentication_path = authentications.get(receipt_id)
        if not all(
            isinstance(value, str)
            for value in (
                receipt_path,
                result_path,
                receipt_id,
                authentication_path,
            )
        ):
            raise P0CalibrationIntegrityError(
                f"Frozen external result for {role} lacks authentication evidence."
            )
        receipt = store.read_json(str(receipt_path), max_bytes=_MAX_RESULT_BYTES)
        result = store.read_json(str(result_path), max_bytes=_MAX_RESULT_BYTES)
        frozen_authentication = store.read_json(str(authentication_path))
        _validate_external_broker_authentication(
            frozen_authentication,
            run=run,
            attestation=attestation,
            attestation_hash=attestation_hash,
            receipt=receipt,
            result_hash=_sha256_json(result),
        )
        current_authentication = _authenticate_external_receipt(
            run=run,
            manifest=manifest,
            attestation=attestation,
            receipt=receipt,
            result=result,
        )
        if current_authentication != frozen_authentication:
            raise P0CalibrationIntegrityError(
                f"External receipt authentication identity changed for {role}."
            )


def dispatch_calibration_agent(
    root: str | Path,
    *,
    role: str,
) -> P0CalibrationDispatchReceipt:
    """Invoke the frozen local OCI backend for one already-issued packet."""

    role = _require_choice(role, CALIBRATION_ROLES, "dispatch role")
    store = _open_store(root)
    with store.lock():
        run = _load_run_locked(store)
        if run.payload["admission_profile"] != "local_no_egress":
            raise P0CalibrationTransitionError(
                "external_authorized results must be imported with record-result."
            )
        if run.state != "INTAKE_OPEN":
            raise P0CalibrationTransitionError(
                f"Dispatch requires INTAKE_OPEN, not {run.state}."
            )
        role_state = run.payload["roles"][role]
        if role_state["status"] != "packet_issued":
            raise P0CalibrationTransitionError(
                f"Role {role} has no issued packet ready for dispatch."
            )
        control_failure = _recheck_bound_controls(store, run)
        if control_failure is not None:
            _terminal_transition_locked(
                store,
                run,
                state="REJECT",
                reason_codes=("source_or_control_mutation",),
                details={"error": control_failure},
            )
            raise P0CalibrationIntegrityError(control_failure)
        authority_failure = _authority_freshness_failure(store, run)
        if authority_failure is not None:
            _terminal_transition_locked(
                store,
                run,
                state="BLOCKED_NO_SHIP",
                reason_codes=("authority_no_longer_valid",),
                details={"error": authority_failure},
            )
            raise P0CalibrationTransitionError(authority_failure)
        packet_path = _packet_path_for_role_state(run, role_state, role=role)
        packet_hash = _require_sha256(
            role_state["current_packet_hash"], "role packet hash"
        )
        manifest = store.read_json(run.payload["artifacts"]["execution_manifest"])
        attestation = store.read_json(run.payload["artifacts"]["isolation_attestation"])
        active = _json_round_trip(run.payload["active_dispatches"])
        if len(active) >= 3:
            raise P0CalibrationTransitionError(
                "At most three calibration workers may be active concurrently."
            )
        started_at = datetime.now(timezone.utc)
        timeout_seconds = int(manifest["oci"]["timeout_seconds"])
        grace_seconds = int(manifest["oci"]["termination_grace_seconds"])
        active[role] = {
            "role": role,
            "attempt": role_state["attempts"],
            "packet_id": role_state["current_packet_id"],
            "packet_hash": packet_hash,
            "idempotency_key": role_state["idempotency_key"],
            "generation": run.generation + 1,
            "status": "started",
            "started_at": _format_timestamp(started_at),
            "deadline_at": _format_timestamp(
                started_at + timedelta(seconds=timeout_seconds + grace_seconds + 30)
            ),
        }
        roles = _json_round_trip(run.payload["roles"])
        roles[role] = {**role_state, "status": "dispatch_started"}
        started_run = _commit_transition(
            store,
            current=run,
            expected_generation=run.generation,
            expected_head=run.head_transition_hash,
            target_state=run.state,
            event_type="dispatch_started",
            updates={"roles": roles, "active_dispatches": active},
            details={
                "role": role,
                "attempt": role_state["attempts"],
                "packet_hash": packet_hash,
                "idempotency_key": role_state["idempotency_key"],
            },
        )

    try:
        from .documentation_calibration_broker import (
            OciDispatchContext,
            OciRuntimeConfig,
            dispatch_oci_agent,
        )

        config = OciRuntimeConfig.from_execution_manifest(manifest)
        context = OciDispatchContext(
            cohort_id=started_run.cohort_id,
            generation=started_run.generation,
            head_transition_hash=started_run.head_transition_hash,
            role=role,
            attempt=int(role_state["attempts"]),
            packet_id=str(role_state["current_packet_id"]),
            packet_hash=packet_hash,
            authority_hash=str(started_run.payload["authority_hash"]),
            attestation_hash=str(started_run.payload["attestation_hash"]),
            access_audit_hash=str(attestation["access_audit_hash"]),
            idempotency_key=str(role_state["idempotency_key"]),
        )
        with tempfile.TemporaryDirectory(
            prefix=f"llm-wiki-{started_run.cohort_id[:8]}-{role}-"
        ) as output:
            outcome = dispatch_oci_agent(
                config,
                context=context,
                packet_path=store.root / packet_path,
                output_dir=Path(output),
            )
    except BaseException as exc:
        with store.lock():
            current = _load_run_locked(store)
            if current.state not in CALIBRATION_TERMINAL_STATES:
                _terminal_transition_locked(
                    store,
                    current,
                    state="BLOCKED_NO_SHIP",
                    reason_codes=("dispatch_inconclusive",),
                    details={"role": role, "error": _bounded_error(exc)},
                )
        if not isinstance(exc, Exception):
            raise
        raise P0CalibrationTransitionError(
            f"OCI dispatch was inconclusive and the cohort is blocked: {_bounded_error(exc)}"
        ) from exc

    receipt_payload = outcome.receipt.to_dict()
    receipt = P0CalibrationDispatchReceipt.from_dict(receipt_payload)
    execution = {
        "role": role,
        "attempt": role_state["attempts"],
        "receipt_id": receipt.receipt_id,
        "status": receipt_payload["status"],
        "stdout_prefix": outcome.stdout[:65536],
        "stdout_prefix_truncated": len(outcome.stdout) > 65536,
        "stderr_prefix": outcome.stderr[:65536],
        "stderr_prefix_truncated": len(outcome.stderr) > 65536,
    }
    if receipt_payload["status"] != "complete" or outcome.result is None:
        with store.lock():
            current = _load_run_locked(store)
            receipt_path = f"dispatch/{role}/{receipt.receipt_id}.json"
            execution_path = f"dispatch/{role}/{receipt.receipt_id}-execution.json"
            _commit_transition(
                store,
                current=current,
                expected_generation=current.generation,
                expected_head=current.head_transition_hash,
                target_state="BLOCKED_NO_SHIP",
                event_type="dispatch_failed",
                artifacts=[
                    (receipt_path, receipt_payload),
                    (execution_path, execution),
                ],
                reason_codes=("dispatch_failed_or_inconclusive",),
                details={
                    "role": role,
                    "status": receipt_payload["status"],
                    "started": receipt_payload["started"],
                },
            )
        return receipt
    result = P0CalibrationAgentResult.from_dict(outcome.result)
    _record_p0_calibration_agent_result(
        root,
        dispatch_receipt=receipt,
        result=result,
        allow_local_dispatch=True,
    )
    return receipt


def record_calibration_agent_result(
    root: str | Path,
    *,
    dispatch_receipt: P0CalibrationDispatchReceipt | Mapping[str, Any],
    result: P0CalibrationAgentResult | Mapping[str, Any],
) -> P0CalibrationRun:
    """Import one authenticated, hash-bound broker result."""

    return _record_p0_calibration_agent_result(
        root,
        dispatch_receipt=dispatch_receipt,
        result=result,
        allow_local_dispatch=False,
    )


def _record_p0_calibration_agent_result(
    root: str | Path,
    *,
    dispatch_receipt: P0CalibrationDispatchReceipt | Mapping[str, Any],
    result: P0CalibrationAgentResult | Mapping[str, Any],
    allow_local_dispatch: bool,
) -> P0CalibrationRun:
    receipt = (
        dispatch_receipt
        if isinstance(dispatch_receipt, P0CalibrationDispatchReceipt)
        else P0CalibrationDispatchReceipt.from_dict(dispatch_receipt)
    )
    agent_result = (
        result
        if isinstance(result, P0CalibrationAgentResult)
        else P0CalibrationAgentResult.from_dict(result)
    )
    store = _open_store(root)
    with store.lock():
        run = _load_run_locked(store)
        receipt_hash = _sha256_json(receipt.payload)
        result_hash = _sha256_json(agent_result.payload)
        existing = run.payload["recorded_receipts"].get(receipt.receipt_id)
        if existing is not None:
            if (
                isinstance(existing, Mapping)
                and existing.get("receipt_hash") == receipt_hash
                and existing.get("result_hash") == result_hash
            ):
                return run
            _terminal_transition_locked(
                store,
                run,
                state="REJECT",
                reason_codes=("receipt_or_result_id_reused_with_different_bytes",),
            )
            raise P0CalibrationIntegrityError(
                "Receipt id was reused with different bytes."
            )
        if run.state in CALIBRATION_TERMINAL_STATES:
            raise P0CalibrationTransitionError(
                f"Calibration state {run.state} is terminal."
            )
        control_failure = _recheck_bound_controls(store, run)
        if control_failure is not None:
            _terminal_transition_locked(
                store,
                run,
                state="REJECT",
                reason_codes=("source_or_control_mutation",),
                details={"error": control_failure},
            )
            raise P0CalibrationIntegrityError(control_failure)
        if run.payload["admission_profile"] == "local_no_egress":
            if not allow_local_dispatch:
                raise P0CalibrationTransitionError(
                    "Local OCI results can only be recorded by dispatch."
                )
            local_role = _require_choice(
                receipt.payload.get("role"), CALIBRATION_ROLES, "receipt role"
            )
            if (
                run.payload["roles"][local_role]["status"] != "dispatch_started"
                or local_role not in run.payload["active_dispatches"]
            ):
                raise P0CalibrationTransitionError(
                    "Local OCI receipt has no controller-started dispatch."
                )
        authority_failure = _authority_freshness_failure(store, run)
        if authority_failure is not None:
            _terminal_transition_locked(
                store,
                run,
                state="BLOCKED_NO_SHIP",
                reason_codes=("authority_no_longer_valid",),
                details={"error": authority_failure},
            )
            raise P0CalibrationTransitionError(authority_failure)
        duplicate_capability = next(
            (
                receipt_id
                for receipt_id, binding in run.payload["recorded_receipts"].items()
                if isinstance(binding, Mapping)
                and binding.get("idempotency_key")
                == receipt.payload.get("idempotency_key")
            ),
            None,
        )
        if duplicate_capability is not None:
            _terminal_transition_locked(
                store,
                run,
                state="REJECT",
                reason_codes=("one_use_capability_replayed",),
                details={
                    "prior_receipt_id": duplicate_capability,
                    "receipt_id": receipt.receipt_id,
                },
            )
            raise P0CalibrationIntegrityError(
                "One-use dispatch capability was replayed."
            )
        result_id_path = f"intake/result-ids/{agent_result.result_id}.json"
        if store.exists(result_id_path):
            prior_result = store.read_json(result_id_path, max_bytes=_MAX_RESULT_BYTES)
            _terminal_transition_locked(
                store,
                run,
                state="REJECT",
                reason_codes=("result_id_reused",),
                details={"identical_bytes": prior_result == agent_result.payload},
            )
            raise P0CalibrationIntegrityError(
                "Result id was reused outside an identical receipt replay."
            )
        try:
            broker_authentication = _validate_result_import_bindings(
                store,
                run,
                receipt=receipt,
                result=agent_result,
            )
        except _ExternalBrokerAuthenticationUnavailable as exc:
            _terminal_transition_locked(
                store,
                run,
                state="BLOCKED_NO_SHIP",
                reason_codes=("external_broker_authentication_unavailable",),
                details={"error": _bounded_error(exc)},
            )
            raise P0CalibrationTransitionError(str(exc)) from exc
        except P0CalibrationSchemaError as exc:
            _terminal_transition_locked(
                store,
                run,
                state="REJECT",
                reason_codes=("forged_or_mismatched_receipt",),
                details={"error": _bounded_error(exc)},
            )
            raise P0CalibrationIntegrityError(str(exc)) from exc
        recorded = _json_round_trip(run.payload["recorded_receipts"])
        recorded[receipt.receipt_id] = {
            "receipt_hash": receipt_hash,
            "result_hash": result_hash,
            "idempotency_key": receipt.payload["idempotency_key"],
            "role": receipt.payload["role"],
            "attempt": receipt.payload["attempt"],
            "profile": run.payload["admission_profile"],
            "route_id": receipt.payload.get("route_id"),
            "response_bytes": receipt.payload["response_bytes"],
        }
        broker_authentication_path = (
            f"dispatch/{receipt.payload['role']}/"
            f"{receipt.receipt_id}-authentication.json"
            if broker_authentication is not None
            else None
        )
        broker_authentication_artifacts: list[tuple[str, Mapping[str, Any]]] = []
        if broker_authentication_path is not None and broker_authentication is not None:
            broker_authentication_artifacts.append(
                (broker_authentication_path, broker_authentication)
            )
        if agent_result.payload["status"] == "dispatch_failed":
            role = agent_result.role
            role_state = run.payload["roles"][role]
            receipt_path = f"dispatch/{role}/{receipt.receipt_id}.json"
            result_path = (
                f"intake/{role}/attempt-{role_state['attempts']:02d}-"
                f"{agent_result.result_id}-dispatch-failure.json"
            )
            failure = _required_mapping(
                agent_result.payload["failure"], "result dispatch failure"
            )
            roles = _json_round_trip(run.payload["roles"])
            roles[role] = {
                **role_state,
                "result_id": agent_result.result_id,
                "receipt_id": receipt.receipt_id,
            }
            active = _json_round_trip(run.payload["active_dispatches"])
            active.pop(role, None)
            artifacts = _json_round_trip(run.payload["artifacts"])
            receipts = _json_round_trip(artifacts.get("receipts", {}))
            results = _json_round_trip(artifacts.get("results", {}))
            receipts[role] = receipt_path
            results[role] = result_path
            artifacts["receipts"] = receipts
            artifacts["results"] = results
            if broker_authentication_path is not None:
                receipt_authentications = _json_round_trip(
                    artifacts.get("receipt_authentications", {})
                )
                receipt_authentications[receipt.receipt_id] = broker_authentication_path
                artifacts["receipt_authentications"] = receipt_authentications
            return _commit_transition(
                store,
                current=run,
                expected_generation=run.generation,
                expected_head=run.head_transition_hash,
                target_state="BLOCKED_NO_SHIP",
                event_type="external_dispatch_failed",
                updates={
                    "roles": roles,
                    "active_dispatches": active,
                    "recorded_receipts": recorded,
                    "artifacts": artifacts,
                },
                artifacts=[
                    (receipt_path, receipt.payload),
                    (result_path, agent_result.payload),
                    (result_id_path, agent_result.payload),
                    *broker_authentication_artifacts,
                ],
                reason_codes=("external_dispatch_failed_or_inconclusive",),
                details={
                    "role": role,
                    "attempt": role_state["attempts"],
                    "receipt_status": receipt.payload["status"],
                    "dispatch_started": receipt.payload["started"],
                    "failure_reason_code": failure["reason_code"],
                    "retry_allowed": False,
                },
            )
        evidence = store.read_json(
            run.payload["artifacts"]["evidence_bundle"],
            max_bytes=_MAX_BUNDLE_BYTES,
        )
        try:
            _validate_semantic_result(
                agent_result.payload,
                evidence=evidence,
                proposals=(
                    _frozen_intake_proposals(store, run)
                    if agent_result.role == "verifier"
                    else None
                ),
            )
        except P0CalibrationSchemaError as exc:
            role = agent_result.role
            role_state = run.payload["roles"][role]
            invalid_path = (
                f"intake/{role}/attempt-{role_state['attempts']:02d}-invalid.json"
            )
            invalid_result_path = (
                f"intake/{role}/attempt-{role_state['attempts']:02d}-"
                f"{agent_result.result_id}-invalid-result.json"
            )
            invalid_record = {
                "schema_version": P0_CALIBRATION_AGENT_RESULT_SCHEMA_VERSION,
                "cohort_id": run.cohort_id,
                "role": role,
                "attempt": role_state["attempts"],
                "result_id": agent_result.result_id,
                "result_hash": result_hash,
                "result_artifact": invalid_result_path,
                "error": _bounded_error(exc),
            }
            receipt_path = f"dispatch/{role}/{receipt.receipt_id}.json"
            if role_state["attempts"] >= 2:
                _commit_transition(
                    store,
                    current=run,
                    expected_generation=run.generation,
                    expected_head=run.head_transition_hash,
                    target_state="BLOCKED_NO_SHIP",
                    event_type="semantic_result_invalid",
                    updates={"recorded_receipts": recorded},
                    artifacts=[
                        (receipt_path, receipt.payload),
                        (invalid_path, invalid_record),
                        (invalid_result_path, agent_result.payload),
                        (result_id_path, agent_result.payload),
                        *broker_authentication_artifacts,
                    ],
                    reason_codes=("role_attempts_exhausted",),
                    details={"role": role, "error": _bounded_error(exc)},
                )
            else:
                roles = _json_round_trip(run.payload["roles"])
                roles[role] = {
                    **role_state,
                    "status": "not_issued",
                    "current_packet_id": None,
                    "current_packet_hash": None,
                    "packet_generation": None,
                    "result_id": None,
                    "receipt_id": None,
                    "idempotency_key": None,
                }
                active = _json_round_trip(run.payload["active_dispatches"])
                active.pop(role, None)
                _commit_transition(
                    store,
                    current=run,
                    expected_generation=run.generation,
                    expected_head=run.head_transition_hash,
                    target_state=run.state,
                    event_type="semantic_result_invalid",
                    updates={
                        "roles": roles,
                        "active_dispatches": active,
                        "recorded_receipts": recorded,
                    },
                    artifacts=[
                        (receipt_path, receipt.payload),
                        (invalid_path, invalid_record),
                        (invalid_result_path, agent_result.payload),
                        (result_id_path, agent_result.payload),
                        *broker_authentication_artifacts,
                    ],
                    details={
                        "role": role,
                        "fresh_context_attempt_allowed": True,
                        "error": _bounded_error(exc),
                    },
                )
            raise P0CalibrationSchemaError(
                f"Semantic result is invalid: {exc}"
            ) from exc
        role = agent_result.role
        role_state = run.payload["roles"][role]
        receipt_path = f"dispatch/{role}/{receipt.receipt_id}.json"
        result_path = (
            f"intake/{role}/attempt-{role_state['attempts']:02d}-"
            f"{agent_result.result_id}.json"
        )
        roles = _json_round_trip(run.payload["roles"])
        roles[role] = {
            **role_state,
            "status": "result_frozen",
            "result_id": agent_result.result_id,
            "receipt_id": receipt.receipt_id,
        }
        active = _json_round_trip(run.payload["active_dispatches"])
        active.pop(role, None)
        artifacts = _json_round_trip(run.payload["artifacts"])
        receipts = _json_round_trip(artifacts.get("receipts", {}))
        results = _json_round_trip(artifacts.get("results", {}))
        receipts[role] = receipt_path
        results[role] = result_path
        artifacts["receipts"] = receipts
        artifacts["results"] = results
        if broker_authentication_path is not None:
            receipt_authentications = _json_round_trip(
                artifacts.get("receipt_authentications", {})
            )
            receipt_authentications[receipt.receipt_id] = broker_authentication_path
            artifacts["receipt_authentications"] = receipt_authentications
        return _commit_transition(
            store,
            current=run,
            expected_generation=run.generation,
            expected_head=run.head_transition_hash,
            target_state=run.state,
            event_type="result_frozen",
            updates={
                "roles": roles,
                "active_dispatches": active,
                "recorded_receipts": recorded,
                "artifacts": artifacts,
            },
            artifacts=[
                (receipt_path, receipt.payload),
                (result_path, agent_result.payload),
                (result_id_path, agent_result.payload),
                *broker_authentication_artifacts,
            ],
            details={
                "role": role,
                "attempt": role_state["attempts"],
                "result_hash": result_hash,
            },
        )


def _validate_result_import_bindings(
    store: ProtectedArtifactStore,
    run: P0CalibrationRun,
    *,
    receipt: P0CalibrationDispatchReceipt,
    result: P0CalibrationAgentResult,
) -> dict[str, Any] | None:
    payload = receipt.payload
    if payload.get("cohort_id") != run.cohort_id:
        raise P0CalibrationSchemaError("Receipt cohort_id does not match.")
    role = _require_choice(payload.get("role"), CALIBRATION_ROLES, "receipt role")
    role_state = run.payload["roles"][role]
    if role_state["status"] not in {"packet_issued", "dispatch_started"}:
        raise P0CalibrationSchemaError(f"Receipt role {role} is not awaiting a result.")
    expected = {
        "attempt": role_state["attempts"],
        "packet_hash": role_state["current_packet_hash"],
        "idempotency_key": role_state["idempotency_key"],
        "authority_hash": run.payload["authority_hash"],
    }
    attestation_key = (
        "isolation_attestation_hash"
        if "isolation_attestation_hash" in payload
        else "attestation_hash"
    )
    for name, value in expected.items():
        if payload.get(name) != value:
            raise P0CalibrationSchemaError(
                f"Receipt {name} does not match the issued capability."
            )
    if payload.get(attestation_key) != run.payload["attestation_hash"]:
        raise P0CalibrationSchemaError(
            "Receipt attestation hash does not match admission."
        )
    attestation = store.read_json(run.payload["artifacts"]["isolation_attestation"])
    if payload.get("access_audit_hash") != attestation["access_audit_hash"]:
        raise P0CalibrationSchemaError(
            "Receipt access-audit hash does not match admission."
        )
    binding_generation = int(role_state["packet_generation"])
    active = run.payload["active_dispatches"].get(role)
    if isinstance(active, Mapping):
        binding_generation = int(active["generation"])
    events = _load_transition_events(store)
    if not 1 <= binding_generation <= len(events):
        raise P0CalibrationSchemaError(
            "Receipt generation does not identify a frozen transition."
        )
    binding_head = events[binding_generation - 1]["transition_hash"]
    if (
        payload.get("generation") != binding_generation
        or payload.get("head_transition_hash") != binding_head
    ):
        raise P0CalibrationSchemaError(
            "Receipt generation/head does not match its dispatch capability."
        )
    profile = run.payload["admission_profile"]
    result_status = result.payload["status"]
    if result_status == "complete":
        if payload.get("status") != "complete" or payload.get("started") is not True:
            raise P0CalibrationSchemaError(
                "Only a complete started dispatch receipt can freeze a result."
            )
    else:
        if profile != "external_authorized":
            raise P0CalibrationSchemaError(
                "Dispatch-failure result envelopes are external-broker evidence only."
            )
        failure = _required_mapping(
            result.payload.get("failure"), "result dispatch failure"
        )
        if payload.get("status") != failure["reason_code"]:
            raise P0CalibrationSchemaError(
                "Failure receipt status does not match the result reason_code."
            )
        if payload.get("started") is not failure["dispatch_started"]:
            raise P0CalibrationSchemaError(
                "Failure receipt started flag does not match the result envelope."
            )
    if payload.get("response_hash") != _sha256_json(result.payload):
        raise P0CalibrationSchemaError(
            "Receipt response hash does not match canonical result bytes."
        )
    if payload.get("response_bytes") != len(canonical_json_bytes(result.payload)):
        raise P0CalibrationSchemaError(
            "Receipt response byte count does not match canonical result bytes."
        )
    manifest = store.read_json(run.payload["artifacts"]["execution_manifest"])
    manifest_budgets = _required_mapping(
        manifest.get("budgets"), "frozen execution manifest budgets"
    )
    result_limit = _require_positive_int(
        manifest_budgets.get("max_result_bytes"),
        "frozen execution manifest max_result_bytes",
    )
    if payload["response_bytes"] > result_limit:
        raise P0CalibrationSchemaError(
            "Agent result exceeds the frozen execution-manifest result budget."
        )
    for name, value in (
        ("cohort_id", run.cohort_id),
        ("role", role),
        ("attempt", role_state["attempts"]),
        ("packet_id", role_state["current_packet_id"]),
        ("packet_hash", role_state["current_packet_hash"]),
        ("idempotency_key", role_state["idempotency_key"]),
    ):
        if result.payload.get(name) != value:
            raise P0CalibrationSchemaError(
                f"Agent result {name} does not match its packet."
            )
    if profile == "local_no_egress":
        try:
            from .documentation_calibration_broker import (
                OciDispatchReceipt,
                OciRuntimeConfig,
            )

            OciDispatchReceipt.from_dict(payload)
            config = OciRuntimeConfig.from_execution_manifest(manifest)
        except (ImportError, ValueError, TypeError) as exc:
            raise P0CalibrationSchemaError(
                f"Local OCI receipt does not verify: {exc}"
            ) from exc
        if (
            payload.get("runtime") != config.runtime
            or payload.get("runtime_executable_sha256") != config.executable_sha256
            or payload.get("image") != config.worker.image
            or payload.get("image_digest") != config.worker.digest
        ):
            raise P0CalibrationSchemaError(
                "Local OCI receipt runtime/image identity does not match the "
                "frozen execution manifest."
            )
        return None
    else:
        runtime = attestation["runtime"]
        if payload.get("broker_id") != runtime["broker_id"]:
            raise P0CalibrationSchemaError(
                "External receipt broker identity does not match attestation."
            )
        if (
            payload.get("runtime_identity") != runtime["runtime_identity"]
            or payload.get("image_identity") != runtime["image_identity"]
        ):
            raise P0CalibrationSchemaError(
                "External receipt runtime/image identity does not match attestation."
            )
        route = next(
            (
                candidate
                for candidate in manifest["external_routes"]
                if candidate["route_id"] == payload.get("route_id")
            ),
            None,
        )
        if not isinstance(route, Mapping):
            raise P0CalibrationSchemaError("External receipt route is not authorized.")
        packet_path = _packet_path_for_role_state(run, role_state, role=role)
        packet_payload = store.read_json(
            packet_path,
            max_bytes=CALIBRATION_CONTROLLER_MAX_PACKET_BYTES,
        )
        packet_bytes = len(canonical_json_bytes(packet_payload))
        if packet_bytes > int(route["max_request_bytes"]):
            raise P0CalibrationSchemaError(
                "External receipt route cannot carry the frozen packet bytes."
            )
        if payload["response_bytes"] > int(route["max_response_bytes"]):
            raise P0CalibrationSchemaError(
                "External receipt route response exceeds its frozen byte limit."
            )
        prior_route_calls = sum(
            isinstance(binding, Mapping)
            and binding.get("route_id") == payload["route_id"]
            for binding in run.payload["recorded_receipts"].values()
        )
        if prior_route_calls >= int(route["max_calls"]):
            raise P0CalibrationSchemaError(
                "External receipt route has exhausted its frozen call limit."
            )
        material = dict(payload)
        supplied_receipt_id = str(material.pop("receipt_id"))
        supplied_receipt_hash = str(material.pop("receipt_hash"))
        expected_receipt_hash = _sha256_json(material)
        expected_receipt_id = "receipt-" + expected_receipt_hash.split(":", 1)[1][:24]
        if (
            supplied_receipt_hash != expected_receipt_hash
            or supplied_receipt_id != expected_receipt_id
        ):
            raise P0CalibrationSchemaError("External receipt hash/id does not verify.")
        return _authenticate_external_receipt(
            run=run,
            manifest=manifest,
            attestation=attestation,
            receipt=payload,
            result=result.payload,
        )


def verify_calibration_run(
    root: str | Path,
    *,
    advance: bool = True,
) -> P0CalibrationVerificationReport:
    """Recompute all frozen gates and optionally advance to ``INTAKE_FROZEN``."""

    store = _open_store(root)
    with store.lock():
        run = _load_run_locked(store)
        checks = []
        control_failure = _recheck_bound_controls(store, run)
        checks.append(
            {
                "check": "source_and_controls_unchanged",
                "ok": control_failure is None,
                "detail": control_failure,
            }
        )
        authority_failure = _authority_freshness_failure(store, run)
        checks.append(
            {
                "check": "authority_and_attestation_current",
                "ok": authority_failure is None,
                "detail": authority_failure,
            }
        )
        results_complete = all(
            run.payload["roles"][role]["status"] == "result_frozen"
            for role in CALIBRATION_ROLES
        )
        checks.append(
            {
                "check": "all_role_results_frozen",
                "ok": results_complete,
                "detail": None
                if results_complete
                else "All three intake results and the verifier are required.",
            }
        )
        exhausted_pending_roles = [
            role
            for role in CALIBRATION_ROLES
            if run.payload["roles"][role]["status"] == "not_issued"
            and int(run.payload["roles"][role]["attempts"]) >= 2
        ]
        semantic_error = None
        frozen_results: dict[str, P0CalibrationAgentResult] = {}
        evidence = store.read_json(
            run.payload["artifacts"]["evidence_bundle"],
            max_bytes=_MAX_BUNDLE_BYTES,
        )
        if results_complete:
            try:
                for role in CALIBRATION_ROLES:
                    path = run.payload["artifacts"]["results"][role]
                    result = P0CalibrationAgentResult.from_dict(
                        store.read_json(path, max_bytes=_MAX_RESULT_BYTES)
                    )
                    _validate_semantic_result(
                        result.payload,
                        evidence=evidence,
                        proposals=(
                            _frozen_intake_proposals(store, run)
                            if role == "verifier"
                            else None
                        ),
                    )
                    frozen_results[role] = result
                _validate_coherent_verifier(
                    frozen_results["verifier"].payload["verification"]
                )
            except (P0CalibrationError, ProtectedArtifactError) as exc:
                semantic_error = _bounded_error(exc)
        checks.append(
            {
                "check": "coherent_source_supported_intake",
                "ok": results_complete and semantic_error is None,
                "detail": semantic_error,
            }
        )
        ok = all(bool(check["ok"]) for check in checks)
        report_payload = {
            "schema_version": P0_CALIBRATION_VERIFICATION_REPORT_SCHEMA_VERSION,
            "cohort_id": run.cohort_id,
            "state": run.state,
            "generation": run.generation,
            "decision_scope": P0_CALIBRATION_DECISION_SCOPE,
            "ok": ok,
            "eligible": ok and run.state == "INTAKE_OPEN",
            "next_state": "INTAKE_FROZEN"
            if ok and run.state == "INTAKE_OPEN"
            else None,
            "advanced": False,
            "checks": checks,
            "artifacts": {},
            "limitations": [
                "Verification ends at pre-labeling intake freeze.",
                "No labels, weights, scores, candidate policy, adoption, release, or publication is authorized.",
            ],
        }
        _validate_verification_report(report_payload)
        if not advance:
            return P0CalibrationVerificationReport.from_dict(report_payload)
        if run.state == "INTAKE_FROZEN" and ok:
            report_payload["state"] = run.state
            report_payload["next_state"] = None
            return P0CalibrationVerificationReport.from_dict(report_payload)
        if not ok:
            if run.state not in CALIBRATION_TERMINAL_STATES:
                terminal_state = None
                reason_codes: tuple[str, ...] = ()
                if control_failure is not None:
                    terminal_state = "REJECT"
                    reason_codes = ("source_or_control_mutation",)
                elif authority_failure is not None:
                    terminal_state = "BLOCKED_NO_SHIP"
                    reason_codes = ("authority_no_longer_valid",)
                elif exhausted_pending_roles:
                    terminal_state = "BLOCKED_NO_SHIP"
                    reason_codes = ("role_attempts_exhausted",)
                elif results_complete and semantic_error is not None:
                    terminal_state = "BLOCKED_NO_SHIP"
                    reason_codes = ("intake_verification_incoherent",)
                if terminal_state is not None:
                    _terminal_transition_locked(
                        store,
                        run,
                        state=terminal_state,
                        reason_codes=reason_codes,
                        details={
                            "control_failure": control_failure,
                            "authority_failure": authority_failure,
                            "semantic_error": semantic_error,
                            "results_complete": results_complete,
                            "exhausted_pending_roles": exhausted_pending_roles,
                        },
                    )
            return P0CalibrationVerificationReport.from_dict(report_payload)
        if run.state != "INTAKE_OPEN":
            raise P0CalibrationTransitionError(
                f"Verification cannot advance state {run.state}."
            )
        task_oracle = _build_task_oracle(
            run,
            evidence=evidence,
            verification=frozen_results["verifier"].payload["verification"],
        )
        label_contract = _build_label_field_contract(run)
        optimizer_contract = _build_optimizer_search_contract(run)
        task_hash = _sha256_json(task_oracle)
        label_hash = _sha256_json(label_contract)
        optimizer_hash = _sha256_json(optimizer_contract)
        result_hashes = {
            role: _sha256_json(frozen_results[role].payload)
            for role in CALIBRATION_ROLES
        }
        frozen_intake = {
            "schema_version": P0_CALIBRATION_FROZEN_INTAKE_SCHEMA_VERSION,
            "cohort_id": run.cohort_id,
            "decision_scope": P0_CALIBRATION_DECISION_SCOPE,
            "source": _json_round_trip(run.payload["source"]),
            "population": _json_round_trip(run.payload["population"]),
            "result_hashes": result_hashes,
            "task_oracle_hash": task_hash,
            "label_field_contract_hash": label_hash,
            "optimizer_search_contract_hash": optimizer_hash,
            "contains_labels": False,
            "contains_candidate_policy": False,
            "frozen_at": _utc_now(),
        }
        paths = {
            "task_oracle": "intake/task-oracle.json",
            "label_field_contract": "intake/label-field-contract.json",
            "optimizer_search_contract": "intake/optimizer-search-contract.json",
            "frozen_intake": "intake/frozen-intake.json",
            "verification_report": "verification/intake-freeze.json",
        }
        report_payload.update(
            {
                "state": "INTAKE_FROZEN",
                "generation": run.generation + 1,
                "advanced": True,
                "artifacts": {
                    "task_oracle_hash": task_hash,
                    "label_field_contract_hash": label_hash,
                    "optimizer_search_contract_hash": optimizer_hash,
                    "frozen_intake_hash": _sha256_json(frozen_intake),
                },
            }
        )
        artifacts = _json_round_trip(run.payload["artifacts"])
        artifacts.update(paths)
        committed = _commit_transition(
            store,
            current=run,
            expected_generation=run.generation,
            expected_head=run.head_transition_hash,
            target_state="INTAKE_FROZEN",
            event_type="intake_frozen",
            updates={
                "artifacts": artifacts,
                "limitations": report_payload["limitations"],
            },
            artifacts=[
                (paths["task_oracle"], task_oracle),
                (paths["label_field_contract"], label_contract),
                (paths["optimizer_search_contract"], optimizer_contract),
                (paths["frozen_intake"], frozen_intake),
                (paths["verification_report"], report_payload),
            ],
        )
        report_payload["state"] = committed.state
        return P0CalibrationVerificationReport.from_dict(report_payload)


def _validate_semantic_result(
    payload: Mapping[str, Any],
    *,
    evidence: Mapping[str, Any],
    proposals: Sequence[Mapping[str, Any]] | None = None,
) -> None:
    _validate_agent_result(payload)
    citations = evidence.get("source_excerpts")
    if not isinstance(citations, list):
        raise P0CalibrationSchemaError(
            "Evidence bundle source citations are malformed."
        )
    allowed_citations = {
        item.get("citation_id")
        for item in citations
        if isinstance(item, Mapping) and isinstance(item.get("citation_id"), str)
    }
    role = str(payload["role"])
    semantic_name = "verification" if role == "verifier" else "proposal"
    semantic = _required_mapping(payload.get(semantic_name), semantic_name)
    fields = {
        "purpose",
        "audiences",
        "capabilities",
        "tasks",
        "journeys",
        "contradictions",
        "unknowns",
        "limitations",
    }
    if role == "verifier":
        fields |= {
            "primary_journey_claim_id",
            "accepted_claims",
            "rejected_claims",
        }
    _require_exact_fields(semantic, fields, label=semantic_name)
    seen_claim_ids: set[str] = set()
    _validate_cited_claim(
        semantic.get("purpose"),
        label=f"{semantic_name}.purpose",
        allowed_citations=allowed_citations,
        seen_claim_ids=seen_claim_ids,
    )
    proposal_claims = _proposal_claim_records(proposals) if role == "verifier" else {}
    dispositioned_claims: set[str] = set()
    accepted_proposal_claims: set[str] = set()
    for field_name in sorted(fields - {"purpose", "primary_journey_claim_id"}):
        claims = semantic.get(field_name)
        if not isinstance(claims, list):
            raise P0CalibrationSchemaError(
                f"{semantic_name}.{field_name} must be a list."
            )
        if len(claims) > 1024:
            raise P0CalibrationSchemaError(
                f"{semantic_name}.{field_name} exceeds the claim limit."
            )
        for index, claim in enumerate(claims):
            label = f"{semantic_name}.{field_name}[{index}]"
            if role == "verifier" and field_name in {
                "accepted_claims",
                "rejected_claims",
            }:
                _validate_verifier_disposition_claim(
                    claim,
                    label=label,
                    allowed_citations=allowed_citations,
                    allowed_proposal_claims=frozenset(proposal_claims),
                    seen_claim_ids=seen_claim_ids,
                    dispositioned_claims=dispositioned_claims,
                    accepted_proposal_claims=accepted_proposal_claims,
                    accepted=field_name == "accepted_claims",
                )
            else:
                _validate_cited_claim(
                    claim,
                    label=label,
                    allowed_citations=allowed_citations,
                    seen_claim_ids=seen_claim_ids,
                )
    if role == "verifier" and dispositioned_claims != set(proposal_claims):
        missing = sorted(set(proposal_claims) - dispositioned_claims)
        raise P0CalibrationSchemaError(
            "Verifier dispositions do not account for every intake-proposal "
            f"claim; first missing reference: {missing[0] if missing else 'unknown'}."
        )
    if role == "verifier":
        primary_journey_claim_id = _portable_id(
            semantic.get("primary_journey_claim_id"),
            "verification.primary_journey_claim_id",
        )
        journey_claim_ids = {
            str(claim["claim_id"])
            for claim in semantic["journeys"]
            if isinstance(claim, Mapping)
        }
        if primary_journey_claim_id not in journey_claim_ids:
            raise P0CalibrationSchemaError(
                "Verifier primary_journey_claim_id must reference exactly one "
                "verified journey claim."
            )
        _validate_verifier_synthesis(
            semantic,
            proposal_claims=proposal_claims,
            accepted_proposal_claims=accepted_proposal_claims,
        )


def _proposal_claim_records(
    proposals: Sequence[Mapping[str, Any]] | None,
) -> dict[str, dict[str, Any]]:
    if (
        proposals is None
        or len(proposals) != len(INTAKE_ROLES)
        or not all(isinstance(record, Mapping) for record in proposals)
    ):
        raise P0CalibrationSchemaError(
            "Verifier validation requires the three frozen intake proposals."
        )
    references: dict[str, dict[str, Any]] = {}
    seen_roles: set[str] = set()
    for record in proposals:
        role = _require_choice(record.get("role"), INTAKE_ROLES, "proposal role")
        if role in seen_roles:
            raise P0CalibrationSchemaError(
                f"Verifier proposal inventory repeats role {role}."
            )
        seen_roles.add(role)
        _require_uuid(record.get("result_id"), f"proposal {role} result_id")
        proposal = _required_mapping(record.get("proposal"), f"proposal {role}")
        purpose = _required_mapping(proposal.get("purpose"), f"proposal {role} purpose")
        proposal_claims = [purpose]
        for field_name in (
            "audiences",
            "capabilities",
            "tasks",
            "journeys",
            "contradictions",
            "unknowns",
            "limitations",
        ):
            claims = proposal.get(field_name)
            if not isinstance(claims, list):
                raise P0CalibrationSchemaError(
                    f"Proposal {role} {field_name} is not a claim list."
                )
            for index, claim in enumerate(claims):
                proposal_claims.append(
                    _required_mapping(claim, f"proposal {role} {field_name}[{index}]")
                )
        claim_ids = [
            _portable_id(claim.get("claim_id"), f"proposal {role} claim_id")
            for claim in proposal_claims
        ]
        if len(claim_ids) != len(set(claim_ids)):
            raise P0CalibrationSchemaError(
                f"Proposal {role} repeats a claim identifier."
            )
        for claim_id, claim in zip(claim_ids, proposal_claims):
            reference = f"{role}/{claim_id}"
            references[reference] = _json_round_trip(claim)
    if seen_roles != set(INTAKE_ROLES):
        raise P0CalibrationSchemaError(
            "Verifier proposal inventory does not contain all intake roles."
        )
    return references


def _validate_verifier_disposition_claim(
    payload: Any,
    *,
    label: str,
    allowed_citations: set[Any],
    allowed_proposal_claims: frozenset[str],
    seen_claim_ids: set[str],
    dispositioned_claims: set[str],
    accepted_proposal_claims: set[str],
    accepted: bool,
) -> None:
    claim = _required_mapping(payload, label)
    _require_exact_fields(
        claim,
        {"claim_id", "statement", "citations", "proposal_claim_ids"},
        label=label,
    )
    _validate_cited_claim(
        {
            "claim_id": claim["claim_id"],
            "statement": claim["statement"],
            "citations": claim["citations"],
        },
        label=label,
        allowed_citations=allowed_citations,
        seen_claim_ids=seen_claim_ids,
    )
    references = claim.get("proposal_claim_ids")
    if (
        not isinstance(references, list)
        or not references
        or any(not isinstance(value, str) for value in references)
        or len(references) != len(set(references))
    ):
        raise P0CalibrationSchemaError(
            f"{label}.proposal_claim_ids must be a non-empty unique string list."
        )
    unknown = sorted(set(references) - allowed_proposal_claims)
    repeated = sorted(set(references) & dispositioned_claims)
    if unknown:
        raise P0CalibrationSchemaError(
            f"{label} references an unknown proposal claim: {unknown[0]}."
        )
    if repeated:
        raise P0CalibrationSchemaError(
            f"Proposal claim received more than one verifier disposition: {repeated[0]}."
        )
    dispositioned_claims.update(references)
    if accepted:
        accepted_proposal_claims.update(references)


def _validate_verifier_synthesis(
    verification: Mapping[str, Any],
    *,
    proposal_claims: Mapping[str, Mapping[str, Any]],
    accepted_proposal_claims: set[str],
) -> None:
    accepted = [
        proposal_claims[reference] for reference in sorted(accepted_proposal_claims)
    ]
    for field_name in ("purpose", "audiences", "capabilities", "tasks", "journeys"):
        value = verification.get(field_name)
        claims = [value] if field_name == "purpose" else value
        if not isinstance(claims, list):
            raise P0CalibrationSchemaError(
                f"Verifier synthesis {field_name} must contain claims."
            )
        for index, raw in enumerate(claims):
            claim = _required_mapping(raw, f"verifier synthesis {field_name}[{index}]")
            statement = claim.get("statement")
            citations = claim.get("citations")
            if not any(
                candidate.get("statement") == statement
                and candidate.get("citations") == citations
                for candidate in accepted
            ):
                raise P0CalibrationSchemaError(
                    "Verifier synthesis contains a core claim that was not retained "
                    f"from an accepted intake proposal: {field_name}[{index}]."
                )


def _validate_cited_claim(
    payload: Any,
    *,
    label: str,
    allowed_citations: set[Any],
    seen_claim_ids: set[str],
) -> None:
    claim = _required_mapping(payload, label)
    _require_exact_fields(
        claim,
        {"claim_id", "statement", "citations"},
        label=label,
    )
    claim_id = _portable_id(claim.get("claim_id"), f"{label}.claim_id")
    if claim_id in seen_claim_ids:
        raise P0CalibrationSchemaError(f"Semantic claim id is reused: {claim_id}.")
    seen_claim_ids.add(claim_id)
    statement = _require_text(claim.get("statement"), f"{label}.statement")
    if len(statement.encode("utf-8")) > 8192:
        raise P0CalibrationSchemaError(
            f"{label}.statement exceeds the 8192-byte limit."
        )
    citations = claim.get("citations")
    if (
        not isinstance(citations, list)
        or not citations
        or any(not isinstance(value, str) for value in citations)
        or len(citations) != len(set(citations))
    ):
        raise P0CalibrationSchemaError(
            f"{label}.citations must be a non-empty unique string list."
        )
    unknown = sorted(set(citations) - allowed_citations)
    if unknown:
        raise P0CalibrationSchemaError(
            f"{label} references an unknown source citation: {unknown[0]}."
        )


def _validate_coherent_verifier(verification: Mapping[str, Any]) -> None:
    purpose = _required_mapping(verification.get("purpose"), "verification purpose")
    if not _require_text(purpose.get("statement"), "verification purpose statement"):
        raise P0CalibrationSchemaError(
            "Verifier did not retain a coherent project purpose."
        )
    for field_name in ("audiences", "tasks", "journeys"):
        values = verification.get(field_name)
        if not isinstance(values, list) or not values:
            raise P0CalibrationSchemaError(
                f"Verifier did not retain a coherent {field_name} set."
            )
    primary_journey_claim_id = _portable_id(
        verification.get("primary_journey_claim_id"),
        "verification.primary_journey_claim_id",
    )
    journey_claim_ids = {
        str(claim.get("claim_id"))
        for claim in verification["journeys"]
        if isinstance(claim, Mapping)
    }
    if primary_journey_claim_id not in journey_claim_ids:
        raise P0CalibrationSchemaError(
            "Verifier did not bind one coherent primary journey."
        )


def _build_task_oracle(
    run: P0CalibrationRun,
    *,
    evidence: Mapping[str, Any],
    verification: Mapping[str, Any],
) -> dict[str, Any]:
    census = _required_mapping(evidence.get("census"), "evidence census")
    capsules = census.get("capsules")
    if not isinstance(capsules, list):
        raise P0CalibrationIntegrityError("Evidence census capsules are missing.")
    cases = []
    for capsule in capsules:
        record = _required_mapping(capsule, "census capsule")
        citation = _required_mapping(
            record.get("source_citation"), "census capsule source_citation"
        )
        cases.append(
            {
                "case_id": record["case_id"],
                "flow_id": record["flow_id"],
                "category": record["category"],
                "citation_id": citation["citation_id"],
                "unknown_fields": list(record["unknown_fields"]),
            }
        )
    if len(cases) != run.payload["population"]["total"]:
        raise P0CalibrationIntegrityError(
            "Task oracle does not cover the frozen population."
        )
    primary_journey_claim_id = _portable_id(
        verification.get("primary_journey_claim_id"),
        "verification.primary_journey_claim_id",
    )
    primary_journey = next(
        (
            claim
            for claim in verification["journeys"]
            if isinstance(claim, Mapping)
            and claim.get("claim_id") == primary_journey_claim_id
        ),
        None,
    )
    if primary_journey is None:
        raise P0CalibrationIntegrityError(
            "Task oracle cannot resolve the verified primary journey."
        )
    return {
        "schema_version": P0_CALIBRATION_TASK_ORACLE_SCHEMA_VERSION,
        "cohort_id": run.cohort_id,
        "source": _json_round_trip(run.payload["source"]),
        "population": _json_round_trip(run.payload["population"]),
        "purpose": _json_round_trip(verification["purpose"]),
        "audiences": _json_round_trip_list(verification["audiences"]),
        "capabilities": _json_round_trip_list(verification["capabilities"]),
        "tasks": _json_round_trip_list(verification["tasks"]),
        "journeys": _json_round_trip_list(verification["journeys"]),
        "primary_journey_claim_id": primary_journey_claim_id,
        "primary_journey": _json_round_trip(primary_journey),
        "contradictions": _json_round_trip_list(verification["contradictions"]),
        "unknowns": _json_round_trip_list(verification["unknowns"]),
        "limitations": _json_round_trip_list(verification["limitations"]),
        "cases": cases,
    }


def _build_label_field_contract(run: P0CalibrationRun) -> dict[str, Any]:
    return {
        "schema_version": P0_CALIBRATION_LABEL_FIELD_CONTRACT_SCHEMA_VERSION,
        "cohort_id": run.cohort_id,
        "input_schema": P0_CALIBRATION_TASK_ORACLE_SCHEMA_VERSION,
        "record_fields": [
            {
                "name": "case_id",
                "type": "portable_id",
                "required": True,
            },
            {
                "name": "assigned_priority",
                "type": "enum",
                "allowed_values": ["P0", "P1", "P2"],
                "required": True,
            },
            {
                "name": "reason_codes",
                "type": "unique_string_list",
                "required": True,
            },
            {
                "name": "source_citations",
                "type": "unique_citation_id_list",
                "required": True,
            },
            {
                "name": "representative_id",
                "type": "portable_id_or_null",
                "required": True,
            },
        ],
        "constraints": [
            "Every frozen census case must occur exactly once.",
            "Every non-null representative must identify a frozen census case.",
            "Every reason must be traceable to a versioned rule and source citation.",
        ],
    }


def _build_optimizer_search_contract(run: P0CalibrationRun) -> dict[str, Any]:
    return {
        "schema_version": P0_CALIBRATION_OPTIMIZER_SEARCH_CONTRACT_SCHEMA_VERSION,
        "cohort_id": run.cohort_id,
        "inputs": {
            "task_oracle_schema": P0_CALIBRATION_TASK_ORACLE_SCHEMA_VERSION,
            "label_field_schema": P0_CALIBRATION_LABEL_FIELD_CONTRACT_SCHEMA_VERSION,
        },
        "objectives": [
            "preserve required primary journeys",
            "minimize unsupported promotion and demotion",
            "preserve complete frozen-population accounting",
        ],
        "constraints": [
            "No search begins before independently frozen labels and holdout custody exist.",
            "No candidate may mutate the v1 documentation worklist.",
            "All evaluated records must retain source citations.",
        ],
        "seeds": [17, 29, 43],
        "tie_breaking": [
            "lower unsupported-decision count",
            "higher source-citation coverage",
            "lexicographically smaller canonical parameter serialization",
        ],
    }


def _json_round_trip_list(value: Any) -> list[Any]:
    if not isinstance(value, list):
        raise P0CalibrationSchemaError("Expected a JSON list.")
    wrapped = _json_round_trip({"items": value})
    return list(wrapped["items"])


def _load_control_workspace(workspace: Path, *, index: int) -> dict[str, Any]:
    try:
        root = workspace.expanduser().resolve(strict=True)
    except OSError as exc:
        raise P0CalibrationIntegrityError(
            f"Cannot resolve control workspace {workspace}: {exc}"
        ) from exc
    _assert_regular_directory(root, "control workspace")
    try:
        run = DocumentationRun.from_dict(
            _read_workspace_json(root, f"{RUN_CONTROL_DIR}/run.json")
        )
    except (DocumentationRunError, P0CalibrationError) as exc:
        raise P0CalibrationIntegrityError(
            f"Control {index} is not a valid documentation run: {exc}"
        ) from exc
    if run.state != "baseline_ready":
        raise P0CalibrationIntegrityError(
            f"Control {index} must remain at baseline_ready, not {run.state!r}."
        )
    if (
        run.current_stage is not None
        or run.stage_attempts
        or any(run.work.get(key) for key in run.work)
    ):
        raise P0CalibrationIntegrityError(
            f"Control {index} contains post-baseline agent activity."
        )
    if run.source.get("available") is not True:
        raise P0CalibrationIntegrityError(
            f"Control {index} has no available source snapshot."
        )
    if run.baseline.get("freshness") != "verified_current":
        raise P0CalibrationIntegrityError(
            f"Control {index} source freshness is not verified_current."
        )
    runtime = _load_control_runtime_policy(root, run)
    source_root = runtime["source_root"]
    if source_root is None:
        raise P0CalibrationIntegrityError(
            f"Control {index} runtime policy has no source root."
        )
    wiki_root = root / run.paths["wiki"]
    source_baseline_relative = _required_evidence_path(run, "source_baseline")
    source_baseline, source_baseline_bytes = _read_workspace_json_snapshot(
        root,
        source_baseline_relative,
    )
    if hash_bytes(canonical_json_bytes(source_baseline)) != run.integrity_anchors.get(
        "source_baseline"
    ) and hash_bytes(source_baseline_bytes) != run.integrity_anchors.get(
        "source_baseline"
    ):
        raise P0CalibrationIntegrityError(
            f"Control {index} source-baseline anchor changed."
        )
    try:
        baseline = TreeBaseline.from_dict(source_baseline)
        difference = compare_tree_baseline(baseline, source_root)
    except DocumentationPolicyError as exc:
        raise P0CalibrationIntegrityError(
            f"Control {index} source baseline is invalid: {exc}"
        ) from exc
    if not difference.ok:
        raise P0CalibrationIntegrityError(
            f"Control {index} source changed after baseline: {difference.to_dict()}"
        )
    worklist = _read_workspace_json(
        root, _required_evidence_path(run, "semantic_worklist")
    )
    worklist_counts = _validate_worklist(worklist)
    census = _read_workspace_json(
        root, _required_evidence_path(run, "p0_calibration_census")
    )
    try:
        validate_flow_evidence_census(census)
    except DocumentationCalibrationError as exc:
        raise P0CalibrationIntegrityError(
            f"Control {index} census is invalid: {exc}"
        ) from exc
    population = census.get("population")
    if not isinstance(population, Mapping) or population.get("complete") is not True:
        raise P0CalibrationIntegrityError(
            f"Control {index} census population is incomplete."
        )
    for capsule in census.get("capsules", []):
        citation = capsule.get("source_citation")
        if not isinstance(citation, Mapping) or not _validate_bound_source_citation(
            citation, source_root=source_root
        ):
            raise P0CalibrationIntegrityError(
                f"Control {index} census capsule {capsule.get('flow_id')!r} "
                "lacks a validated source citation."
            )
    shadow = _read_workspace_json(
        root, _required_evidence_path(run, "p0_calibration_shadow")
    )
    if (
        shadow.get("candidate_evaluated") is not False
        or shadow.get("mode") != "evidence_only"
    ):
        raise P0CalibrationIntegrityError(
            f"Control {index} shadow contains candidate qualification evidence."
        )
    census_counts = census.get("counts")
    if not isinstance(census_counts, Mapping):
        raise P0CalibrationIntegrityError(f"Control {index} census counts are missing.")
    documentation_inputs = _snapshot_priority_blind_document_inputs(
        source_root=source_root,
        wiki_root=wiki_root,
    )
    return {
        "index": index,
        "workspace_root": root,
        "source_root": source_root,
        "wiki_root": wiki_root,
        "run": run,
        "source_revision": _require_text(
            run.source.get("revision"), f"control {index} source revision"
        ),
        "source_fingerprint": _require_text(
            run.source.get("content_fingerprint"),
            f"control {index} source fingerprint",
        ),
        "source_tree_hash": _require_sha256(
            source_baseline.get("tree_hash"),
            f"control {index} source tree hash",
        ),
        "source_file_hashes": dict(baseline.file_hashes),
        "source_file_count": _require_nonnegative_int(
            source_baseline.get("file_count"),
            f"control {index} source file_count",
        ),
        "worklist": worklist,
        "worklist_hash": _sha256_json(worklist),
        "worklist_counts": worklist_counts,
        "census": census,
        "census_hash": _sha256_json(census),
        "census_counts": _json_round_trip(census_counts),
        "shadow_hash": _sha256_json(shadow),
        "documentation_inputs": documentation_inputs,
        "population": {
            "total": census_counts["total"],
            "by_category": _json_round_trip(census_counts.get("by_category", {})),
        },
    }


def _assert_controls_match(controls: Sequence[Mapping[str, Any]]) -> None:
    comparable_keys = (
        "source_revision",
        "source_fingerprint",
        "source_tree_hash",
        "source_file_hashes",
        "source_file_count",
        "worklist_hash",
        "worklist_counts",
        "census_hash",
        "census_counts",
        "shadow_hash",
        "documentation_inputs",
        "population",
    )
    mismatches = [
        key for key in comparable_keys if controls[0].get(key) != controls[1].get(key)
    ]
    if mismatches:
        raise P0CalibrationIntegrityError(
            "Documentation controls do not reproduce the same frozen baseline: "
            + ", ".join(mismatches)
        )


def _portable_control_record(
    control: Mapping[str, Any], *, cohort_id: str
) -> dict[str, Any]:
    return {
        "schema_version": P0_CALIBRATION_CONTROL_RECORD_SCHEMA_VERSION,
        "cohort_id": cohort_id,
        "control_index": control["index"],
        "documentation_run_id": control["run"].run_id,
        "documentation_run_schema": control["run"].schema_version,
        "baseline_state": control["run"].state,
        "source": {
            "revision": control["source_revision"],
            "content_fingerprint": control["source_fingerprint"],
            "tree_hash": control["source_tree_hash"],
            "file_count": control["source_file_count"],
        },
        "worklist": {
            "schema_version": control["worklist"]["schema_version"],
            "hash": control["worklist_hash"],
            "counts": _json_round_trip(control["worklist_counts"]),
        },
        "census": {
            "schema_version": control["census"]["schema_version"],
            "hash": control["census_hash"],
            "counts": _json_round_trip(control["census_counts"]),
            "population_complete": True,
            "priority_blind": True,
        },
        "shadow": {
            "hash": control["shadow_hash"],
            "candidate_evaluated": False,
            "accepted_as_qualification": False,
        },
        "documentation_inputs": _json_round_trip(control["documentation_inputs"]),
        "read_only_source": {
            "policy_bound": True,
            "baseline_unchanged": True,
        },
    }


def _compile_evidence_bundle(
    control: Mapping[str, Any],
    *,
    bound_roots: Sequence[Path],
) -> dict[str, Any]:
    outbound_roots = _normalize_bound_roots(bound_roots)
    census = _json_round_trip(control["census"])
    excerpts_by_id: dict[str, dict[str, Any]] = {}
    for capsule in census["capsules"]:
        citation = capsule["source_citation"]
        source_path = _portable_relative_path(
            citation["path"], label="source citation path"
        )
        snapshot = _read_bound_evidence_file(
            control["source_root"],
            source_path,
            included_maximum=_MAX_DOCUMENT_BYTES * 8,
            maximum=_MAX_DOCUMENT_BYTES * 8,
        )
        raw = snapshot.included
        if citation["source_sha256"] != snapshot.sha256:
            raise P0CalibrationIntegrityError(
                f"Cited source hash changed while freezing evidence: {source_path}"
            )
        try:
            lines = raw.decode("utf-8").splitlines()
        except UnicodeDecodeError as exc:
            raise P0CalibrationIntegrityError(
                f"Cited source is not UTF-8: {source_path}"
            ) from exc
        start = int(citation["start_line"])
        end = int(citation["end_line"])
        if start < 1 or end < start or end > len(lines):
            raise P0CalibrationIntegrityError(
                f"Cited source line range is invalid: {source_path}"
            )
        excerpt = "\n".join(lines[start - 1 : end])
        excerpt_sha256 = "sha256:" + hashlib.sha256(excerpt.encode("utf-8")).hexdigest()
        if citation["excerpt_sha256"] != excerpt_sha256:
            raise P0CalibrationIntegrityError(
                f"Cited excerpt hash changed while freezing evidence: {source_path}"
            )
        _redacted_excerpt, excerpt_redactions = _redact_outbound_text(
            excerpt,
            bound_roots=outbound_roots,
        )
        if excerpt_redactions:
            kinds = ", ".join(
                sorted({str(record["kind"]) for record in excerpt_redactions})
            )
            raise P0CalibrationIntegrityError(
                "Cited source contains outbound-sensitive content that cannot be "
                f"redacted without invalidating its citation ({source_path}: {kinds})."
            )
        citation_body = {
            "path": source_path,
            "symbol": citation["symbol"],
            "start_line": start,
            "end_line": end,
            "definition_line": citation["definition_line"],
            "source_sha256": citation["source_sha256"],
            "excerpt_sha256": citation["excerpt_sha256"],
        }
        citation_id = "citation-" + _sha256_json(citation_body).split(":", 1)[1][:24]
        excerpt_record = {
            "citation_id": citation_id,
            **citation_body,
            "excerpt": excerpt,
            "truncated": False,
            "content_status": "verbatim",
            "redactions": [],
        }
        previous = excerpts_by_id.get(citation_id)
        if previous is not None and previous != excerpt_record:
            raise P0CalibrationIntegrityError(
                f"Source citation identity collision for {source_path}."
            )
        excerpts_by_id[citation_id] = excerpt_record
        capsule["source_citation"]["citation_id"] = citation_id
    documents, document_unknowns = _collect_priority_blind_documents(
        control,
        bound_roots=outbound_roots,
    )
    bundle = {
        "schema_version": P0_CALIBRATION_EVIDENCE_BUNDLE_SCHEMA_VERSION,
        "source": {
            "revision": control["source_revision"],
            "content_fingerprint": control["source_fingerprint"],
            "tree_hash": control["source_tree_hash"],
        },
        "population": _json_round_trip(control["population"]),
        "priority_blind": True,
        "census": census,
        "source_excerpts": sorted(
            excerpts_by_id.values(),
            key=lambda item: (
                str(item["path"]).casefold(),
                str(item["path"]),
                int(item["start_line"]),
            ),
        ),
        "documents": documents,
        "unknowns": document_unknowns,
        "limitations": [
            "Static evidence may contain explicit unknowns and is not runtime proof.",
            "No current priority, candidate score, label, weight, or policy outcome is included.",
        ],
    }
    sanitized, bundle_redactions = _sanitize_outbound_value(
        bundle,
        bound_roots=outbound_roots,
    )
    if not isinstance(sanitized, dict):
        raise P0CalibrationIntegrityError(
            "Sanitized evidence bundle is not a JSON object."
        )
    document_redactions = [
        {
            "path": str(document["path"]),
            "redactions": _json_round_trip_list(document["redactions"]),
        }
        for document in sanitized["documents"]
        if document.get("redactions")
    ]
    sanitized["outbound_safety"] = {
        "status": (
            "redacted"
            if document_redactions or bundle_redactions
            else "no_scanner_matches"
        ),
        "scanner": "deterministic-credential-and-host-path-denylist-v1",
        "limitation": (
            "Pattern scanning reduces known credential and host-path leakage; "
            "it is not proof that arbitrary source text contains no secret."
        ),
        "cited_excerpts": "verbatim_only",
        "document_redactions": document_redactions,
        "other_redactions": bundle_redactions,
    }
    _assert_outbound_payload_safe(sanitized, bound_roots=outbound_roots)
    return sanitized


def _collect_priority_blind_documents(
    control: Mapping[str, Any],
    *,
    bound_roots: Sequence[str],
) -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
    ordered = _ordered_priority_blind_document_candidates(
        source_root=control["source_root"],
        wiki_root=control["wiki_root"],
    )
    documents = []
    unknowns = []
    total = 0
    for logical_path, (evidence_root, evidence_relative, kind) in ordered[
        :_MAX_DOCUMENT_COUNT
    ]:
        snapshot = _read_bound_evidence_file(
            evidence_root,
            evidence_relative,
            included_maximum=_MAX_DOCUMENT_BYTES,
            maximum=128 * 1024 * 1024,
        )
        if kind == "project_input":
            expected_hash = control["source_file_hashes"].get(evidence_relative)
            if expected_hash is None or snapshot.sha256 != expected_hash:
                raise P0CalibrationIntegrityError(
                    "Source documentation changed from the frozen tree baseline: "
                    f"{evidence_relative}"
                )
        if total + len(snapshot.included) > _MAX_DOCUMENT_TOTAL_BYTES:
            unknowns.append(
                {"path": logical_path, "reason": "document_total_budget_exhausted"}
            )
            continue
        try:
            content = snapshot.included.decode("utf-8")
        except UnicodeDecodeError:
            unknowns.append({"path": logical_path, "reason": "non_utf8_document"})
            continue
        sanitized_content, redactions = _redact_outbound_text(
            content,
            bound_roots=bound_roots,
        )
        outbound_bytes = sanitized_content.encode("utf-8")
        if total + len(outbound_bytes) > _MAX_DOCUMENT_TOTAL_BYTES:
            unknowns.append(
                {"path": logical_path, "reason": "document_total_budget_exhausted"}
            )
            continue
        total += len(outbound_bytes)
        if redactions:
            unknowns.append(
                {"path": logical_path, "reason": "sensitive_content_redacted"}
            )
        documents.append(
            {
                "path": _portable_relative_path(
                    logical_path, label="document logical path"
                ),
                "kind": kind,
                "sha256": snapshot.sha256,
                "source_included_sha256": snapshot.included_sha256,
                "included_sha256": "sha256:"
                + hashlib.sha256(outbound_bytes).hexdigest(),
                "original_bytes": snapshot.original_bytes,
                "source_included_bytes": len(snapshot.included),
                "included_bytes": len(outbound_bytes),
                "truncated": snapshot.truncated,
                "content_status": "redacted" if redactions else "verbatim",
                "redactions": redactions,
                "content": sanitized_content,
            }
        )
    for logical_path, _value in ordered[_MAX_DOCUMENT_COUNT:]:
        unknowns.append({"path": logical_path, "reason": "document_count_limit"})
    return documents, unknowns


def _ordered_priority_blind_document_candidates(
    *,
    source_root: Path,
    wiki_root: Path,
) -> list[tuple[str, tuple[Path, str, str]]]:
    candidates: dict[str, tuple[Path, str, str]] = {}
    for path in _walk_regular_files(source_root):
        relative = path.relative_to(source_root).as_posix()
        pure = PurePosixPath(relative)
        name = pure.name.casefold()
        stem = pure.stem.casefold()
        is_root_doc = (
            len(pure.parts) == 1
            and pure.suffix.casefold() in _DOCUMENT_SUFFIXES
            and stem in _ROOT_DOCUMENT_NAMES
        )
        is_docs_input = (
            pure.parts
            and pure.parts[0].casefold() in {"doc", "docs", "documentation"}
            and pure.suffix.casefold() in _DOCUMENT_SUFFIXES
        )
        if (
            is_root_doc
            or is_docs_input
            or (len(pure.parts) == 1 and name in _PROJECT_MANIFEST_NAMES)
        ):
            candidates[f"source/{relative}"] = (
                source_root,
                relative,
                "project_input",
            )
    canonical_wiki_names = {
        "index.md",
        "architecture.md",
        "api-contracts.md",
        "dependencies.md",
        "load-order.md",
    }
    if wiki_root.is_dir() and not wiki_root.is_symlink():
        for path in _walk_regular_files(wiki_root):
            relative = path.relative_to(wiki_root).as_posix()
            pure = PurePosixPath(relative)
            if pure.as_posix().casefold() in canonical_wiki_names or (
                pure.parts
                and pure.parts[0].casefold() in {"guides", "workflows"}
                and pure.suffix.casefold() in _DOCUMENT_SUFFIXES
            ):
                candidates[f"wiki/{relative}"] = (
                    wiki_root,
                    relative,
                    "canonical_wiki",
                )
    return sorted(candidates.items(), key=lambda item: (item[0].casefold(), item[0]))


def _snapshot_priority_blind_document_inputs(
    *,
    source_root: Path,
    wiki_root: Path,
) -> dict[str, Any]:
    ordered = _ordered_priority_blind_document_candidates(
        source_root=source_root,
        wiki_root=wiki_root,
    )
    candidate_index = [
        {
            "path": _portable_relative_path(
                logical_path,
                label="control document logical path",
            ),
            "kind": kind,
        }
        for logical_path, (_root, _relative, kind) in ordered
    ]
    selected = []
    for logical_path, (evidence_root, evidence_relative, kind) in ordered[
        :_MAX_DOCUMENT_COUNT
    ]:
        snapshot = _read_bound_evidence_file(
            evidence_root,
            evidence_relative,
            included_maximum=_MAX_DOCUMENT_BYTES,
            maximum=128 * 1024 * 1024,
        )
        selected.append(
            {
                "path": _portable_relative_path(
                    logical_path,
                    label="control document logical path",
                ),
                "kind": kind,
                "sha256": snapshot.sha256,
                "original_bytes": snapshot.original_bytes,
            }
        )
    return {
        "selection": "priority-blind-document-inputs/v1",
        "candidate_count": len(candidate_index),
        "candidate_index_hash": _sha256_json({"inputs": candidate_index}),
        "selected_limit": _MAX_DOCUMENT_COUNT,
        "selected_count": len(selected),
        "selected": selected,
    }


def _build_role_capability_matrix(cohort_id: str) -> dict[str, Any]:
    roles = []
    for role in CALIBRATION_ROLES:
        verifier = role == "verifier"
        roles.append(
            {
                "role": role,
                "reads": (
                    ["packet", "evidence_bundle", "intake_proposals"]
                    if verifier
                    else ["packet", "evidence_bundle"]
                ),
                "writes": [f"role-output/{role}"],
                "network": "denied",
                "credentials": "denied",
                "other_role_writes": "denied",
                "controller_root": "denied",
                "source_root": "denied",
                "dummy_holdout": "denied",
                "max_attempts": 2,
            }
        )
    return {
        "schema_version": P0_CALIBRATION_ROLE_CAPABILITY_MATRIX_SCHEMA_VERSION,
        "cohort_id": cohort_id,
        "maximum_concurrent_workers": 3,
        "receipt_import": "controller_serialized",
        "roles": roles,
    }


def _initial_role_state() -> dict[str, Any]:
    return {
        "attempts": 0,
        "status": "not_issued",
        "current_packet_id": None,
        "current_packet_hash": None,
        "packet_generation": None,
        "result_id": None,
        "receipt_id": None,
        "idempotency_key": None,
    }


def _commit_transition(
    store: ProtectedArtifactStore,
    *,
    current: P0CalibrationRun | None,
    expected_generation: int,
    expected_head: str,
    target_state: str,
    event_type: str,
    run_body: Mapping[str, Any] | None = None,
    updates: Mapping[str, Any] | None = None,
    artifacts: Sequence[tuple[str, Mapping[str, Any]]] = (),
    reason_codes: Sequence[str] = (),
    details: Mapping[str, Any] | None = None,
) -> P0CalibrationRun:
    if target_state not in CALIBRATION_STATES:
        raise P0CalibrationTransitionError(
            f"Unknown calibration target state: {target_state!r}."
        )
    if current is None:
        if expected_generation != 0 or expected_head != _ZERO_HASH:
            raise P0CalibrationTransitionError(
                "Initial transition must compare against generation zero."
            )
        from_state = "PREFLIGHT"
        body = _json_round_trip(run_body or {})
        actual_generation = 0
        actual_head = _ZERO_HASH
    else:
        from_state = current.state
        actual_generation = current.generation
        actual_head = current.head_transition_hash
        body = current.to_dict()
        body.pop("head_transition_hash", None)
        if run_body is not None:
            raise P0CalibrationTransitionError(
                "Existing transitions cannot replace the complete run body."
            )
    if expected_generation != actual_generation or expected_head != actual_head:
        raise P0CalibrationTransitionError(
            "Stale calibration compare-and-swap generation or head hash."
        )
    if from_state in CALIBRATION_TERMINAL_STATES:
        raise P0CalibrationTransitionError(
            f"Calibration state {from_state} is terminal."
        )
    if (
        target_state != from_state
        and target_state not in _ALLOWED_TRANSITIONS[from_state]
    ):
        raise P0CalibrationTransitionError(
            f"Invalid calibration transition: {from_state} -> {target_state}."
        )
    body.update(_json_round_trip(updates or {}))
    body["state"] = target_state
    body["generation"] = actual_generation + 1
    body["updated_at"] = _utc_now()
    if target_state in {"BLOCKED_NO_SHIP", "REJECT"}:
        body["terminal_reason_codes"] = sorted(set(reason_codes))
        body["limitations"] = list(body.get("limitations", [])) + [
            f"Terminal {target_state}: {reason}" for reason in sorted(set(reason_codes))
        ]
    _validate_run_body(body)
    sequence = actual_generation + 1
    artifact_index = [
        {
            "path": validate_portable_relative_path(path),
            "sha256": _sha256_json(payload),
        }
        for path, payload in artifacts
    ]
    transition_base = {
        "schema_version": P0_CALIBRATION_TRANSITION_SCHEMA_VERSION,
        "transition_id": str(uuid.uuid4()),
        "sequence": sequence,
        "cohort_id": body["cohort_id"],
        "event_type": _portable_id(event_type, "transition event_type"),
        "from_state": from_state,
        "to_state": target_state,
        "decision_scope": (
            P0_CALIBRATION_DECISION_SCOPE
            if target_state in CALIBRATION_TERMINAL_STATES
            else None
        ),
        "occurred_at": body["updated_at"],
        "previous_transition_hash": actual_head,
        "expected_generation": actual_generation,
        "reason_codes": sorted(set(reason_codes)),
        "details": _json_round_trip(details or {}),
        "artifacts": artifact_index,
        "resulting_run_body": body,
    }
    transition_hash = _sha256_json(transition_base)
    transition = {**transition_base, "transition_hash": transition_hash}
    snapshot = {**body, "head_transition_hash": transition_hash}
    _validate_run_snapshot(snapshot)
    transition_path = f"transitions/{sequence:08d}.json"
    pending = {
        "schema_version": P0_CALIBRATION_TRANSACTION_SCHEMA_VERSION,
        "transaction_id": transition["transition_id"],
        "status": "pending",
        "expected_generation": actual_generation,
        "expected_head_transition_hash": actual_head,
        "artifacts": [
            {"path": path, "payload": _json_round_trip(payload)}
            for path, payload in artifacts
        ],
        "transition_path": transition_path,
        "transition": transition,
        "snapshot": snapshot,
    }
    store.write_snapshot_json(
        "pending-transaction.json", pending, max_bytes=_MAX_TRANSACTION_BYTES
    )
    for path, payload in artifacts:
        store.write_immutable_json(path, payload, max_bytes=_MAX_BUNDLE_BYTES)
    store.write_immutable_json(transition_path, transition)
    store.write_snapshot_json("run.json", snapshot)
    _rebuild_transition_projection(store)
    store.write_snapshot_json(
        "pending-transaction.json",
        {**pending, "status": "committed"},
        max_bytes=_MAX_TRANSACTION_BYTES,
    )
    return P0CalibrationRun.from_dict(snapshot)


def _recover_pending_transaction(store: ProtectedArtifactStore) -> None:
    if not store.exists("pending-transaction.json"):
        return
    try:
        pending = store.read_json(
            "pending-transaction.json", max_bytes=_MAX_TRANSACTION_BYTES
        )
    except ProtectedArtifactError as exc:
        raise P0CalibrationRecoveryError(
            f"Pending transaction cannot be read unambiguously: {exc}"
        ) from exc
    status = pending.get("status")
    if status == "committed":
        return
    if status != "pending":
        raise P0CalibrationRecoveryError("Pending transaction status is unknown.")
    try:
        artifacts, transition_path, transition, snapshot = (
            _validate_pending_transaction_for_recovery(store, pending)
        )
        for path, payload in artifacts:
            store.write_immutable_json(
                path,
                payload,
                max_bytes=_MAX_BUNDLE_BYTES,
            )
        store.write_immutable_json(transition_path, transition)
        store.write_snapshot_json("run.json", snapshot)
        _rebuild_transition_projection(store)
        store.write_snapshot_json(
            "pending-transaction.json",
            {**pending, "status": "committed"},
            max_bytes=_MAX_TRANSACTION_BYTES,
        )
    except P0CalibrationRecoveryError:
        raise
    except (
        P0CalibrationError,
        ProtectedArtifactError,
        KeyError,
        TypeError,
        ValueError,
    ) as exc:
        raise P0CalibrationRecoveryError(
            f"Pending transaction cannot be recovered unambiguously: {exc}"
        ) from exc


def _validate_pending_transaction_for_recovery(
    store: ProtectedArtifactStore,
    pending: Mapping[str, Any],
) -> tuple[
    list[tuple[str, Mapping[str, Any]]],
    str,
    dict[str, Any],
    dict[str, Any],
]:
    _require_exact_fields(
        pending,
        {
            "schema_version",
            "transaction_id",
            "status",
            "expected_generation",
            "expected_head_transition_hash",
            "artifacts",
            "transition_path",
            "transition",
            "snapshot",
        },
        label="pending transaction",
    )
    if (
        pending.get("schema_version") != P0_CALIBRATION_TRANSACTION_SCHEMA_VERSION
        or pending.get("status") != "pending"
    ):
        raise P0CalibrationRecoveryError("Pending transaction is not fully written.")
    transaction_id = _require_uuid(
        pending.get("transaction_id"), "pending transaction_id"
    )
    expected_generation = _require_nonnegative_int(
        pending.get("expected_generation"),
        "pending expected_generation",
    )
    expected_head = _require_sha256(
        pending.get("expected_head_transition_hash"),
        "pending expected_head_transition_hash",
    )
    artifacts_raw = pending.get("artifacts")
    transition_raw = pending.get("transition")
    snapshot_raw = pending.get("snapshot")
    if (
        not isinstance(artifacts_raw, list)
        or not isinstance(transition_raw, Mapping)
        or not isinstance(snapshot_raw, Mapping)
    ):
        raise P0CalibrationRecoveryError("Pending transaction is not fully written.")

    transition = _json_round_trip(transition_raw)
    snapshot = _json_round_trip(snapshot_raw)
    _validate_transition(transition)
    unhashed_transition = dict(transition)
    supplied_transition_hash = unhashed_transition.pop("transition_hash")
    if _sha256_json(unhashed_transition) != supplied_transition_hash:
        raise P0CalibrationRecoveryError(
            "Pending transaction transition hash does not verify."
        )
    _validate_run_snapshot(snapshot)
    transition_path = _portable_relative_path(
        pending.get("transition_path"),
        label="pending transition path",
    )
    expected_transition_path = f"transitions/{expected_generation + 1:08d}.json"
    if (
        transaction_id != transition["transition_id"]
        or transition_path != expected_transition_path
        or transition["sequence"] != expected_generation + 1
        or transition["expected_generation"] != expected_generation
        or transition["previous_transition_hash"] != expected_head
        or transition["resulting_run_body"]["generation"] != expected_generation + 1
        or transition["resulting_run_body"]["state"] != transition["to_state"]
        or transition["resulting_run_body"]["cohort_id"] != transition["cohort_id"]
    ):
        raise P0CalibrationRecoveryError(
            "Pending transaction identity/CAS bindings are inconsistent."
        )
    expected_snapshot = {
        **_json_round_trip(transition["resulting_run_body"]),
        "head_transition_hash": transition["transition_hash"],
    }
    if snapshot != expected_snapshot:
        raise P0CalibrationRecoveryError(
            "Pending transaction snapshot does not match its transition."
        )

    artifacts: list[tuple[str, Mapping[str, Any]]] = []
    artifact_index: list[dict[str, str]] = []
    seen_paths: set[str] = set()
    for record in artifacts_raw:
        if (
            not isinstance(record, Mapping)
            or set(record) != {"path", "payload"}
            or not isinstance(record.get("payload"), Mapping)
        ):
            raise P0CalibrationRecoveryError(
                "Pending transaction artifact is malformed."
            )
        path = _portable_relative_path(
            record.get("path"),
            label="pending artifact path",
        )
        if path in seen_paths:
            raise P0CalibrationRecoveryError(
                "Pending transaction repeats an artifact path."
            )
        seen_paths.add(path)
        payload = _json_round_trip(record["payload"])
        artifacts.append((path, payload))
        artifact_index.append({"path": path, "sha256": _sha256_json(payload)})
    if artifact_index != transition["artifacts"]:
        raise P0CalibrationRecoveryError(
            "Pending transaction artifacts do not match the transition index."
        )

    events = _load_transition_events(store)
    if len(events) == expected_generation:
        current_head = events[-1]["transition_hash"] if events else _ZERO_HASH
        if current_head != expected_head:
            raise P0CalibrationRecoveryError(
                "Pending transaction CAS head no longer matches the ledger."
            )
        if events and (
            events[-1]["resulting_run_body"]["state"] != transition["from_state"]
            or events[-1]["cohort_id"] != transition["cohort_id"]
        ):
            raise P0CalibrationRecoveryError(
                "Pending transaction does not continue the current cohort state."
            )
    elif len(events) == expected_generation + 1:
        if (
            events[-1] != transition
            or events[-1]["transition_hash"] != transition["transition_hash"]
        ):
            raise P0CalibrationRecoveryError(
                "Pending transition conflicts with the committed ledger."
            )
    else:
        raise P0CalibrationRecoveryError(
            "Pending transaction generation is stale or skips ledger state."
        )
    return artifacts, transition_path, transition, snapshot


def _load_run_locked(store: ProtectedArtifactStore) -> P0CalibrationRun:
    if store.exists("terminal-rejection.json"):
        return _load_emergency_rejection(store)
    try:
        _recover_pending_transaction(store)
    except P0CalibrationRecoveryError as exc:
        try:
            return _block_ambiguous_recovery(store, exc)
        except (
            P0CalibrationError,
            ProtectedArtifactError,
            KeyError,
            TypeError,
            ValueError,
        ) as terminal_error:
            return _persist_emergency_rejection(store, terminal_error)
    try:
        events = _load_transition_events(store)
        if not events:
            raise P0CalibrationIntegrityError(
                "Calibration root has no transition ledger."
            )
        last = events[-1]
        body = _json_round_trip(last["resulting_run_body"])
        expected = {
            **body,
            "head_transition_hash": last["transition_hash"],
        }
        _validate_run_snapshot(expected)
        snapshot_matches = False
        if store.exists("run.json"):
            try:
                snapshot_matches = store.read_json("run.json") == expected
            except ProtectedArtifactError:
                snapshot_matches = False
        if not snapshot_matches:
            store.write_snapshot_json("run.json", expected)
        _rebuild_transition_projection(store, events=events)
        run = P0CalibrationRun.from_dict(expected)
        if run.state not in CALIBRATION_TERMINAL_STATES:
            unknowns = _unknown_root_entries(store.root, events=events)
            if unknowns:
                return _terminal_transition_locked(
                    store,
                    run,
                    state="BLOCKED_NO_SHIP",
                    reason_codes=("unknown_controller_artifact",),
                    details={"unknown_entries": unknowns},
                )
        return run
    except (
        P0CalibrationError,
        ProtectedArtifactError,
        KeyError,
        TypeError,
        ValueError,
    ) as exc:
        return _persist_emergency_rejection(store, exc)


def _block_ambiguous_recovery(
    store: ProtectedArtifactStore, error: BaseException
) -> P0CalibrationRun:
    events = _load_transition_events(store)
    if not events:
        raise P0CalibrationIntegrityError(
            "Ambiguous recovery has no trusted transition."
        )
    last = events[-1]
    snapshot = {
        **_json_round_trip(last["resulting_run_body"]),
        "head_transition_hash": last["transition_hash"],
    }
    run = P0CalibrationRun.from_dict(snapshot)
    if run.state in CALIBRATION_TERMINAL_STATES:
        return run
    try:
        pending = store.read_json(
            "pending-transaction.json", max_bytes=_MAX_TRANSACTION_BYTES
        )
    except ProtectedArtifactError:
        pending = {
            "status": "unreadable",
            "error": _bounded_error(error),
        }
    evidence = {
        "schema_version": P0_CALIBRATION_AMBIGUOUS_RECOVERY_SCHEMA_VERSION,
        "cohort_id": run.cohort_id,
        "detected_at": _utc_now(),
        "error": _bounded_error(error),
        "pending_transaction": pending,
    }
    suffix = _sha256_json(evidence).split(":", 1)[1][:24]
    return _commit_transition(
        store,
        current=run,
        expected_generation=run.generation,
        expected_head=run.head_transition_hash,
        target_state="BLOCKED_NO_SHIP",
        event_type="recovery_ambiguous",
        artifacts=[(f"verification/ambiguous-recovery-{suffix}.json", evidence)],
        reason_codes=("ambiguous_crash_recovery",),
        details={"error": _bounded_error(error)},
    )


def _persist_emergency_rejection(
    store: ProtectedArtifactStore, error: BaseException
) -> P0CalibrationRun:
    if store.exists("terminal-rejection.json"):
        return _load_emergency_rejection(store)
    snapshot: dict[str, Any] | None = None
    try:
        candidate = store.read_json("run.json")
        snapshot = P0CalibrationRun.from_dict(candidate).to_dict()
    except (FileNotFoundError, P0CalibrationError, ProtectedArtifactError):
        try:
            first = store.read_json("transitions/00000001.json")
            body = _json_round_trip(first["resulting_run_body"])
            snapshot = {
                **body,
                "head_transition_hash": first["transition_hash"],
            }
            _validate_run_snapshot(snapshot)
        except (
            FileNotFoundError,
            KeyError,
            P0CalibrationError,
            ProtectedArtifactError,
        ) as fallback_error:
            raise P0CalibrationIntegrityError(
                "Calibration ledger is damaged and no validated cohort identity "
                f"can be recovered: {_bounded_error(fallback_error)}"
            ) from error
    snapshot["state"] = "REJECT"
    snapshot["updated_at"] = _utc_now()
    snapshot["terminal_reason_codes"] = ["ledger_tampering"]
    snapshot["limitations"] = list(snapshot.get("limitations", [])) + [
        "Terminal REJECT: application-level ledger integrity mismatch "
        "(ledger_tampering)"
    ]
    _validate_run_snapshot(snapshot)
    record = {
        "schema_version": P0_CALIBRATION_EMERGENCY_REJECTION_SCHEMA_VERSION,
        "cohort_id": snapshot["cohort_id"],
        "state": "REJECT",
        "decision_scope": P0_CALIBRATION_DECISION_SCOPE,
        "detected_at": snapshot["updated_at"],
        "reason_code": "ledger_tampering",
        "error": _bounded_error(error),
        "last_trusted_head_transition_hash": snapshot["head_transition_hash"],
        "snapshot": snapshot,
    }
    store.write_immutable_json("terminal-rejection.json", record)
    store.write_snapshot_json("run.json", snapshot)
    return P0CalibrationRun.from_dict(snapshot)


def _load_emergency_rejection(
    store: ProtectedArtifactStore,
) -> P0CalibrationRun:
    record = store.read_json("terminal-rejection.json")
    _require_exact_fields(
        record,
        {
            "schema_version",
            "cohort_id",
            "state",
            "decision_scope",
            "detected_at",
            "reason_code",
            "error",
            "last_trusted_head_transition_hash",
            "snapshot",
        },
        label="emergency rejection",
    )
    if (
        record.get("schema_version")
        != P0_CALIBRATION_EMERGENCY_REJECTION_SCHEMA_VERSION
        or record.get("state") != "REJECT"
        or record.get("decision_scope") != P0_CALIBRATION_DECISION_SCOPE
        or record.get("reason_code") != "ledger_tampering"
    ):
        raise P0CalibrationIntegrityError("Emergency rejection record is malformed.")
    snapshot = _required_mapping(record.get("snapshot"), "emergency rejection snapshot")
    run = P0CalibrationRun.from_dict(snapshot)
    if run.state != "REJECT" or run.cohort_id != record.get("cohort_id"):
        raise P0CalibrationIntegrityError(
            "Emergency rejection snapshot does not match its record."
        )
    return run


def _load_transition_events(store: ProtectedArtifactStore) -> list[dict[str, Any]]:
    directory = store.root / "transitions"
    if not directory.is_dir() or directory.is_symlink():
        return []
    entries = sorted(directory.iterdir(), key=lambda path: path.name)
    expected_previous = _ZERO_HASH
    events = []
    cohort_id = None
    for sequence, path in enumerate(entries, start=1):
        expected_name = f"{sequence:08d}.json"
        if path.name != expected_name:
            raise P0CalibrationIntegrityError(
                "Transition ledger numbering is non-contiguous."
            )
        event = store.read_json(f"transitions/{path.name}")
        _validate_transition(event)
        if event["sequence"] != sequence:
            raise P0CalibrationIntegrityError(
                "Transition ledger sequence does not match its filename."
            )
        if event["previous_transition_hash"] != expected_previous:
            raise P0CalibrationIntegrityError(
                "Transition ledger hash chain was changed."
            )
        supplied_hash = event["transition_hash"]
        unhashed = dict(event)
        unhashed.pop("transition_hash")
        if _sha256_json(unhashed) != supplied_hash:
            raise P0CalibrationIntegrityError(
                "Transition ledger record hash does not verify."
            )
        for binding in event["artifacts"]:
            artifact_path = str(binding["path"])
            try:
                artifact = store.read_json(artifact_path, max_bytes=_MAX_BUNDLE_BYTES)
            except (FileNotFoundError, ProtectedArtifactError) as exc:
                raise P0CalibrationIntegrityError(
                    f"Transition artifact is missing or invalid: {artifact_path}"
                ) from exc
            if _sha256_json(artifact) != binding["sha256"]:
                raise P0CalibrationIntegrityError(
                    f"Transition artifact hash changed: {artifact_path}"
                )
        if cohort_id is None:
            cohort_id = event["cohort_id"]
        elif event["cohort_id"] != cohort_id:
            raise P0CalibrationIntegrityError(
                "Transition ledger mixes cohort identities."
            )
        body = event["resulting_run_body"]
        if (
            body.get("generation") != sequence
            or body.get("state") != event["to_state"]
            or event["expected_generation"] != sequence - 1
        ):
            raise P0CalibrationIntegrityError(
                "Transition resulting run body does not match the event."
            )
        expected_previous = supplied_hash
        events.append(event)
    return events


def _rebuild_transition_projection(
    store: ProtectedArtifactStore,
    *,
    events: Sequence[Mapping[str, Any]] | None = None,
) -> None:
    records = list(events) if events is not None else _load_transition_events(store)
    text = "".join(canonical_json_bytes(record).decode("utf-8") for record in records)
    store.write_projection_text("state-transitions.jsonl", text)


def _terminal_transition_locked(
    store: ProtectedArtifactStore,
    run: P0CalibrationRun,
    *,
    state: str,
    reason_codes: Sequence[str],
    details: Mapping[str, Any] | None = None,
) -> P0CalibrationRun:
    if run.state in CALIBRATION_TERMINAL_STATES:
        return run
    return _commit_transition(
        store,
        current=run,
        expected_generation=run.generation,
        expected_head=run.head_transition_hash,
        target_state=state,
        event_type=state.casefold(),
        reason_codes=reason_codes,
        details=details,
    )


def _status_from_run(run: P0CalibrationRun) -> P0CalibrationStatus:
    roles = run.payload["roles"]
    next_actions = {
        "PREFLIGHT": ("complete preparation",),
        "BASELINE_FROZEN": ("admit the frozen cohort",),
        "ADMISSION_AUTHORIZED": ("issue intake-a, intake-b, and intake-c packets",),
        "INTAKE_OPEN": (
            "record pending intake results and run the verifier",
            "verify the frozen intake gates",
        ),
        "INTAKE_FROZEN": (),
        "BLOCKED_NO_SHIP": (),
        "REJECT": (),
    }[run.state]
    return P0CalibrationStatus(
        cohort_id=run.cohort_id,
        state=run.state,
        generation=run.generation,
        decision_scope=P0_CALIBRATION_DECISION_SCOPE,
        admission_profile=run.payload["admission_profile"],
        role_statuses={role: str(roles[role]["status"]) for role in CALIBRATION_ROLES},
        next_actions=next_actions,
        limitations=tuple(str(value) for value in run.payload["limitations"]),
        terminal=run.state in CALIBRATION_TERMINAL_STATES,
        healthy=run.state not in {"BLOCKED_NO_SHIP", "REJECT"},
    )


def _validate_execution_manifest(payload: Mapping[str, Any]) -> None:
    _require_exact_fields(
        payload,
        {
            "schema_version",
            "profile",
            "roles",
            "budgets",
            "oci",
            "external_routes",
        },
        label="execution manifest",
    )
    if (
        payload.get("schema_version")
        != P0_CALIBRATION_EXECUTION_MANIFEST_SCHEMA_VERSION
    ):
        raise P0CalibrationSchemaError("Unsupported execution-manifest schema_version.")
    profile = _require_choice(
        payload.get("profile"), ADMISSION_PROFILES, "manifest profile"
    )
    if payload.get("roles") != list(CALIBRATION_ROLES):
        raise P0CalibrationSchemaError(
            "Execution manifest roles must match the lifecycle role inventory."
        )
    budgets = _required_mapping(payload.get("budgets"), "manifest budgets")
    _require_exact_fields(
        budgets,
        {
            "max_concurrent_workers",
            "max_attempts_per_role",
            "max_total_calls",
            "max_packet_bytes",
            "max_result_bytes",
        },
        label="manifest budgets",
    )
    if budgets.get("max_concurrent_workers") != 3:
        raise P0CalibrationSchemaError(
            "Execution manifest must cap concurrent workers at three."
        )
    if budgets.get("max_attempts_per_role") != 2:
        raise P0CalibrationSchemaError(
            "Execution manifest must cap each role at two attempts."
        )
    total_calls = _require_positive_int(
        budgets.get("max_total_calls"), "manifest max_total_calls"
    )
    if not 4 <= total_calls <= 8:
        raise P0CalibrationSchemaError(
            "Execution manifest max_total_calls must be between four and eight."
        )
    packet_bytes = _require_positive_int(
        budgets.get("max_packet_bytes"), "manifest max_packet_bytes"
    )
    result_bytes = _require_positive_int(
        budgets.get("max_result_bytes"), "manifest max_result_bytes"
    )
    if (
        packet_bytes > CALIBRATION_CONTROLLER_MAX_PACKET_BYTES
        or result_bytes > _MAX_RESULT_BYTES
    ):
        raise P0CalibrationSchemaError(
            "Execution manifest packet or result budget exceeds the controller cap."
        )
    routes = payload.get("external_routes")
    if not isinstance(routes, list):
        raise P0CalibrationSchemaError(
            "Execution manifest external_routes must be a list."
        )
    _validate_external_routes(routes)
    if profile == "local_no_egress":
        if not isinstance(payload.get("oci"), Mapping) or routes:
            raise P0CalibrationSchemaError(
                "local_no_egress requires OCI configuration and no external routes."
            )
        try:
            from .documentation_calibration_broker import OciRuntimeConfig

            config = OciRuntimeConfig.from_dict(payload["oci"])
        except (ImportError, ValueError, TypeError) as exc:
            raise P0CalibrationSchemaError(str(exc)) from exc
        if (
            config.max_packet_bytes != packet_bytes
            or config.output_limits.result_bytes > result_bytes
        ):
            raise P0CalibrationSchemaError(
                "OCI packet/result limits do not match manifest budgets."
            )
    elif payload.get("oci") is not None or not routes:
        raise P0CalibrationSchemaError(
            "external_authorized requires credential-free routes and oci=null."
        )
    try:
        from .documentation_calibration_broker import validate_execution_manifest
    except ImportError:
        return
    try:
        validate_execution_manifest(payload)
    except (ValueError, TypeError) as exc:
        raise P0CalibrationSchemaError(str(exc)) from exc


def _validate_external_routes(routes: Sequence[Any]) -> None:
    route_ids: set[str] = set()
    recipients: set[str] = set()
    for raw in routes:
        route = _required_mapping(raw, "external route")
        _require_exact_fields(
            route,
            {
                "route_id",
                "recipient",
                "max_calls",
                "max_request_bytes",
                "max_response_bytes",
            },
            label="external route",
        )
        route_id = _portable_id(route.get("route_id"), "external route_id")
        recipient = _require_text(route.get("recipient"), "external route recipient")
        if route_id in route_ids or recipient in recipients:
            raise P0CalibrationSchemaError(
                "External route ids and recipients must be unique."
            )
        route_ids.add(route_id)
        recipients.add(recipient)
        _require_positive_int(route.get("max_calls"), "external route max_calls")
        _require_positive_int(
            route.get("max_request_bytes"),
            "external route max_request_bytes",
        )
        _require_positive_int(
            route.get("max_response_bytes"),
            "external route max_response_bytes",
        )


def _validate_worklist(payload: Mapping[str, Any]) -> dict[str, Any]:
    if payload.get("schema_version") != DOCUMENTATION_WORKLIST_SCHEMA_VERSION:
        raise P0CalibrationIntegrityError(
            "Control semantic worklist schema is unsupported."
        )
    items = payload.get("items")
    if not isinstance(items, list) or any(
        not isinstance(item, Mapping) for item in items
    ):
        raise P0CalibrationIntegrityError(
            "Control semantic worklist items are malformed."
        )
    ids = []
    for item in items:
        work_id = item.get("id")
        if not isinstance(work_id, str) or not work_id:
            raise P0CalibrationIntegrityError(
                "Control semantic worklist item lacks an id."
            )
        ids.append(work_id)
        if item.get("priority") not in WORK_ITEM_PRIORITIES:
            raise P0CalibrationIntegrityError(
                "Control semantic worklist has an unsupported priority."
            )
        if item.get("status") not in WORK_ITEM_STATUSES:
            raise P0CalibrationIntegrityError(
                "Control semantic worklist has an unsupported status."
            )
        if not isinstance(item.get("deferred"), bool):
            raise P0CalibrationIntegrityError(
                "Control semantic worklist deferred flags must be boolean."
            )
    if len(ids) != len(set(ids)):
        raise P0CalibrationIntegrityError(
            "Control semantic worklist ids are not unique."
        )
    projected = {
        "total": len(items),
        "by_priority": {
            priority: sum(item.get("priority") == priority for item in items)
            for priority in WORK_ITEM_PRIORITIES
        },
        "by_status": {
            status: sum(item.get("status") == status for item in items)
            for status in sorted(WORK_ITEM_STATUSES)
        },
        "deferred": sum(item.get("deferred") is True for item in items),
    }
    if payload.get("counts") != projected:
        raise P0CalibrationIntegrityError(
            "Control semantic worklist counts do not match its inventory."
        )
    return projected


def _load_control_runtime_policy(
    workspace: Path, run: DocumentationRun
) -> dict[str, Path | None]:
    payload = _read_workspace_json(workspace, f"{RUN_CONTROL_DIR}/{POLICY_FILENAME}")
    _require_exact_fields(
        payload,
        {"schema_version", "portable_policy", "runtime_paths"},
        label="runtime documentation policy",
    )
    if payload.get("schema_version") != "llm-wiki-documentation-policy/v1":
        raise P0CalibrationIntegrityError(
            "Runtime documentation policy schema is unsupported."
        )
    if payload.get("portable_policy") != run.policy:
        raise P0CalibrationIntegrityError(
            "Runtime documentation policy does not match the run."
        )
    raw = payload.get("runtime_paths")
    expected = {
        "workspace_root",
        "source_root",
        "input_wiki_root",
        "helper_cache_root",
        "capture_root",
    }
    if not isinstance(raw, Mapping) or set(raw) != expected:
        raise P0CalibrationIntegrityError(
            "Runtime documentation policy paths are malformed."
        )
    if raw.get("workspace_root") != str(workspace):
        raise P0CalibrationIntegrityError(
            "Runtime documentation policy points at another workspace."
        )
    resolved: dict[str, Path | None] = {"workspace_root": workspace}
    for name in expected - {"workspace_root"}:
        value = raw.get(name)
        if value is None:
            resolved[name] = None
            continue
        if not isinstance(value, str) or not Path(value).is_absolute():
            raise P0CalibrationIntegrityError(
                f"Runtime documentation policy {name} is not absolute."
            )
        path = Path(value)
        try:
            canonical = path.resolve(strict=True)
        except OSError as exc:
            raise P0CalibrationIntegrityError(
                f"Runtime documentation policy {name} is unavailable: {exc}"
            ) from exc
        if str(canonical) != value:
            raise P0CalibrationIntegrityError(
                f"Runtime documentation policy {name} is not canonical."
            )
        resolved[name] = canonical
    if "source" not in run.policy.get("forbidden_write_roots", []):
        raise P0CalibrationIntegrityError(
            "Control run does not bind source as read-only evidence."
        )
    return resolved


def _required_evidence_path(run: DocumentationRun, key: str) -> str:
    value = run.evidence.get(key)
    if not isinstance(value, str) or not value:
        raise P0CalibrationIntegrityError(f"Control run lacks required {key} evidence.")
    return _portable_relative_path(value, label=f"control evidence {key}")


def _read_workspace_json(workspace: Path, relative: str) -> dict[str, Any]:
    payload, _raw = _read_workspace_json_snapshot(workspace, relative)
    return payload


def _read_workspace_json_snapshot(
    workspace: Path,
    relative: str,
) -> tuple[dict[str, Any], bytes]:
    portable = _portable_relative_path(relative, label="control artifact path")
    snapshot = _read_bound_evidence_file(
        workspace,
        portable,
        included_maximum=_MAX_EXTERNAL_JSON_BYTES,
        maximum=_MAX_EXTERNAL_JSON_BYTES,
    )
    raw = snapshot.included
    try:
        payload = json.loads(
            raw.decode("utf-8"),
            object_pairs_hook=_unique_json_object,
            parse_constant=_reject_json_constant,
        )
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise P0CalibrationIntegrityError(
            f"Control artifact {relative!r} is invalid JSON: {exc}"
        ) from exc
    if not isinstance(payload, dict):
        raise P0CalibrationIntegrityError(
            f"Control artifact {relative!r} must be a JSON object."
        )
    return payload, raw


def _validate_bound_source_citation(
    citation: Mapping[str, Any],
    *,
    source_root: Path,
) -> bool:
    """Validate one citation entirely from a safely pinned source handle."""

    try:
        relative = _portable_relative_path(
            citation.get("path"), label="source citation path"
        )
        start = citation.get("start_line")
        end = citation.get("end_line")
        if (
            isinstance(start, bool)
            or not isinstance(start, int)
            or isinstance(end, bool)
            or not isinstance(end, int)
            or start < 1
            or end < start
        ):
            return False
        snapshot = _read_bound_evidence_file(
            source_root,
            relative,
            included_maximum=_MAX_DOCUMENT_BYTES * 8,
            maximum=_MAX_DOCUMENT_BYTES * 8,
        )
        lines = snapshot.included.decode("utf-8").splitlines()
        if end > len(lines):
            return False
        excerpt = "\n".join(lines[start - 1 : end]).encode("utf-8")
    except (P0CalibrationError, UnicodeDecodeError):
        return False
    return (
        citation.get("source_sha256") == snapshot.sha256
        and citation.get("excerpt_sha256")
        == "sha256:" + hashlib.sha256(excerpt).hexdigest()
    )


def _read_bound_evidence_file(
    root: Path,
    relative: str,
    *,
    included_maximum: int,
    maximum: int,
) -> _EvidenceFileSnapshot:
    """Read one source/wiki file without reopening its pathname.

    POSIX opens every absolute-root and relative-path component through pinned
    directory descriptors with ``O_NOFOLLOW``.  Windows pins the complete
    directory chain with native handles and opens the leaf with
    ``FILE_FLAG_OPEN_REPARSE_POINT``.  Size, included bytes, and hashes then all
    come from that one leaf handle.
    """

    if (
        isinstance(included_maximum, bool)
        or not isinstance(included_maximum, int)
        or included_maximum < 0
        or isinstance(maximum, bool)
        or not isinstance(maximum, int)
        or maximum < included_maximum
    ):
        raise P0CalibrationSchemaError("Evidence read limits are invalid.")
    portable = _portable_relative_path(relative, label="external evidence path")
    absolute_root = Path(os.path.abspath(os.fspath(root)))
    if os.name == "nt":
        return _read_bound_evidence_file_windows(
            absolute_root,
            portable,
            included_maximum=included_maximum,
            maximum=maximum,
        )
    return _read_bound_evidence_file_posix(
        absolute_root,
        portable,
        included_maximum=included_maximum,
        maximum=maximum,
    )


def _read_bound_evidence_file_posix(
    root: Path,
    relative: str,
    *,
    included_maximum: int,
    maximum: int,
) -> _EvidenceFileSnapshot:
    no_follow = getattr(os, "O_NOFOLLOW", 0)
    directory_flag = getattr(os, "O_DIRECTORY", 0)
    if (
        not _POSIX_DESCRIPTOR_RELATIVE_READS
        or not no_follow
        or not directory_flag
        or not root.is_absolute()
    ):
        raise P0CalibrationIntegrityError(
            "Descriptor-relative no-follow evidence reads are unavailable."
        )
    directory_flags = (
        os.O_RDONLY | directory_flag | no_follow | getattr(os, "O_CLOEXEC", 0)
    )
    file_flags = (
        os.O_RDONLY
        | no_follow
        | getattr(os, "O_CLOEXEC", 0)
        | getattr(os, "O_BINARY", 0)
    )
    descriptors: list[int] = []
    try:
        anchor = root.anchor
        if not anchor:
            raise P0CalibrationIntegrityError("Evidence root must be an absolute path.")
        descriptor = os.open(anchor, directory_flags)
        descriptors.append(descriptor)
        _assert_open_evidence_directory(os.fstat(descriptor), label="path anchor")
        for component in root.parts[1:]:
            descriptor = os.open(component, directory_flags, dir_fd=descriptor)
            descriptors.append(descriptor)
            _assert_open_evidence_directory(os.fstat(descriptor), label="evidence root")
        relative_parts = PurePosixPath(relative).parts
        for component in relative_parts[:-1]:
            descriptor = os.open(component, directory_flags, dir_fd=descriptor)
            descriptors.append(descriptor)
            _assert_open_evidence_directory(
                os.fstat(descriptor), label=f"evidence directory {component!r}"
            )
        leaf = os.open(relative_parts[-1], file_flags, dir_fd=descriptor)
        descriptors.append(leaf)
        with os.fdopen(leaf, "rb", closefd=False) as stream:
            return _snapshot_open_evidence_stream(
                stream,
                os.fstat(leaf),
                label=relative,
                included_maximum=included_maximum,
                maximum=maximum,
            )
    except P0CalibrationError:
        raise
    except OSError as exc:
        raise P0CalibrationIntegrityError(
            f"Cannot safely read external evidence {relative!r}: {exc}"
        ) from exc
    finally:
        for descriptor in reversed(descriptors):
            try:
                os.close(descriptor)
            except OSError:
                pass


def _read_bound_evidence_file_windows(
    root: Path,
    relative: str,
    *,
    included_maximum: int,
    maximum: int,
) -> _EvidenceFileSnapshot:
    components = PurePosixPath(relative).parts
    try:
        with guard_windows_directory_chain(root, components[:-1]) as parent:
            with open_windows_readonly_file(parent / components[-1]) as (
                stream,
                opened,
            ):
                return _snapshot_open_evidence_stream(
                    stream,
                    opened,
                    label=relative,
                    included_maximum=included_maximum,
                    maximum=maximum,
                )
    except P0CalibrationError:
        raise
    except (WindowsDirectoryGuardError, WindowsFileGuardError, OSError) as exc:
        raise P0CalibrationIntegrityError(
            f"Cannot safely read external evidence {relative!r}: {exc}"
        ) from exc


def _snapshot_open_evidence_stream(
    stream: BinaryIO,
    opened: os.stat_result,
    *,
    label: str,
    included_maximum: int,
    maximum: int,
) -> _EvidenceFileSnapshot:
    _assert_open_evidence_file(opened, label=label)
    if int(opened.st_size) > maximum:
        raise P0CalibrationIntegrityError(
            f"Evidence file exceeds the {maximum}-byte limit: {label}"
        )
    digest = hashlib.sha256()
    included = bytearray()
    total = 0
    while True:
        chunk = stream.read(1024 * 1024)
        if not chunk:
            break
        total += len(chunk)
        if total > maximum:
            raise P0CalibrationIntegrityError(
                f"Evidence file exceeds the {maximum}-byte limit: {label}"
            )
        digest.update(chunk)
        remaining = included_maximum - len(included)
        if remaining > 0:
            included.extend(chunk[:remaining])
    closed_over = os.fstat(stream.fileno())
    _assert_open_evidence_file(closed_over, label=label)
    _assert_stable_evidence_metadata(opened, closed_over, label=label)
    if total != int(opened.st_size):
        raise P0CalibrationIntegrityError(
            f"Evidence file size changed while reading: {label}"
        )
    included_bytes = bytes(included)
    return _EvidenceFileSnapshot(
        included=included_bytes,
        original_bytes=total,
        sha256="sha256:" + digest.hexdigest(),
        included_sha256="sha256:" + hashlib.sha256(included_bytes).hexdigest(),
        truncated=total > included_maximum,
    )


def _assert_open_evidence_directory(payload: os.stat_result, *, label: str) -> None:
    if (
        not stat.S_ISDIR(payload.st_mode)
        or stat.S_ISLNK(payload.st_mode)
        or _is_reparse_metadata(payload)
    ):
        raise P0CalibrationIntegrityError(
            f"Opened {label} is not a regular no-follow directory."
        )


def _assert_open_evidence_file(payload: os.stat_result, *, label: str) -> None:
    if (
        not stat.S_ISREG(payload.st_mode)
        or stat.S_ISLNK(payload.st_mode)
        or _is_reparse_metadata(payload)
    ):
        raise P0CalibrationIntegrityError(
            f"Opened evidence is not a regular no-follow file: {label}"
        )


def _assert_stable_evidence_metadata(
    before: os.stat_result,
    after: os.stat_result,
    *,
    label: str,
) -> None:
    stable_fields = ("st_dev", "st_ino", "st_size", "st_mtime_ns", "st_ctime_ns")
    if any(
        getattr(before, name, None) != getattr(after, name, None)
        for name in stable_fields
    ):
        raise P0CalibrationIntegrityError(
            f"Evidence file changed while reading: {label}"
        )


def _is_reparse_metadata(payload: os.stat_result) -> bool:
    return bool(
        getattr(payload, "st_reparse_tag", 0)
        or getattr(payload, "st_file_attributes", 0) & _REPARSE_ATTRIBUTE
    )


def _walk_regular_files(root: Path) -> Iterable[Path]:
    stack = [root]
    while stack:
        directory = stack.pop()
        _assert_not_link_or_reparse(directory, "evidence directory")
        entries = sorted(
            directory.iterdir(), key=lambda path: (path.name.casefold(), path.name)
        )
        folded: set[str] = set()
        for entry in entries:
            normalized = unicodedata.normalize("NFC", entry.name)
            if normalized != entry.name:
                raise P0CalibrationIntegrityError(
                    f"Evidence path name is not NFC-normalized: {entry.name!r}"
                )
            collision = entry.name.casefold()
            if collision in folded:
                raise P0CalibrationIntegrityError(
                    f"Evidence path has a portable case collision: {entry.name!r}"
                )
            folded.add(collision)
            _assert_not_link_or_reparse(entry, "evidence entry")
            if entry.is_dir():
                if entry.name in {
                    ".git",
                    ".hg",
                    ".svn",
                    ".venv",
                    "node_modules",
                    "__pycache__",
                }:
                    continue
                stack.append(entry)
            elif entry.is_file():
                yield entry


def _validate_protected_root_placement(
    requested: Path,
    *,
    control_roots: Sequence[Path],
    source_roots: Sequence[Path],
) -> Path:
    expanded = Path(os.path.abspath(os.fspath(requested.expanduser())))
    parent = expanded.parent
    try:
        resolved_parent = parent.resolve(strict=True)
    except OSError as exc:
        raise P0CalibrationIntegrityError(
            f"Protected root parent must already exist: {parent}: {exc}"
        ) from exc
    root = resolved_parent / expanded.name
    _assert_portable_leaf_name(root.name, "protected root")
    forbidden = [
        *_implementation_worktree_roots(),
        *control_roots,
        *source_roots,
    ]
    for candidate in forbidden:
        canonical = candidate.resolve()
        if _paths_overlap(root, canonical):
            raise P0CalibrationIntegrityError(
                "Calibration root must be outside source, documentation, and "
                f"implementation worktrees: {canonical}"
            )
    return root


def _implementation_worktree_roots() -> tuple[Path, ...]:
    primary = Path(__file__).resolve().parents[3]
    roots = {primary}
    companion_wiki = Path(f"{primary}.wiki")
    if companion_wiki.is_dir() and not companion_wiki.is_symlink():
        roots.add(companion_wiki.resolve())

    git_entry = primary / ".git"
    common_git_dir: Path | None = None
    try:
        if git_entry.is_dir() and not git_entry.is_symlink():
            common_git_dir = git_entry.resolve()
        elif git_entry.is_file() and not git_entry.is_symlink():
            marker = git_entry.read_text(encoding="utf-8").strip()
            prefix = "gitdir: "
            if marker.startswith(prefix):
                linked_git_dir = Path(marker[len(prefix) :])
                if not linked_git_dir.is_absolute():
                    linked_git_dir = primary / linked_git_dir
                linked_git_dir = linked_git_dir.resolve(strict=True)
                common_marker = linked_git_dir / "commondir"
                if common_marker.is_file() and not common_marker.is_symlink():
                    common_value = common_marker.read_text(encoding="utf-8").strip()
                    common_git_dir = (linked_git_dir / common_value).resolve(
                        strict=True
                    )
    except (OSError, UnicodeError):
        common_git_dir = None

    worktree_metadata = (
        common_git_dir / "worktrees" if common_git_dir is not None else None
    )
    if (
        worktree_metadata is not None
        and worktree_metadata.is_dir()
        and not worktree_metadata.is_symlink()
    ):
        try:
            entries = sorted(worktree_metadata.iterdir(), key=lambda path: path.name)
        except OSError:
            entries = []
        for entry in entries:
            marker = entry / "gitdir"
            try:
                if not marker.is_file() or marker.is_symlink():
                    continue
                git_file = Path(marker.read_text(encoding="utf-8").strip())
                if not git_file.is_absolute():
                    git_file = entry / git_file
                roots.add(git_file.resolve(strict=True).parent)
            except (OSError, UnicodeError):
                continue
    return tuple(sorted(roots, key=lambda path: (str(path).casefold(), str(path))))


def _unknown_root_entries(
    root: Path,
    *,
    events: Sequence[Mapping[str, Any]],
) -> list[str]:
    known_files = set(_ALLOWED_ROOT_FILES)
    known_directories = set(_ALLOWED_ROOT_DIRS)
    for sequence, event in enumerate(events, start=1):
        transition_path = f"transitions/{sequence:08d}.json"
        known_files.add(transition_path)
        for binding in event["artifacts"]:
            known_files.add(str(binding["path"]))
    for relative in known_files:
        parent = PurePosixPath(relative).parent
        while parent.as_posix() not in {".", ""}:
            known_directories.add(parent.as_posix())
            parent = parent.parent

    unknowns = []
    entries = sorted(
        root.rglob("*"),
        key=lambda path: (
            path.relative_to(root).as_posix().casefold(),
            path.relative_to(root).as_posix(),
        ),
    )
    for entry in entries:
        relative = entry.relative_to(root).as_posix()
        _assert_not_link_or_reparse(entry, "protected controller entry")
        if entry.is_file():
            if relative not in known_files:
                unknowns.append(relative)
        elif entry.is_dir():
            if relative not in known_directories:
                unknowns.append(relative + "/")
        else:
            unknowns.append(relative)
    return sorted(set(unknowns))


def _open_store(root: str | Path) -> ProtectedArtifactStore:
    try:
        return ProtectedArtifactStore(root)
    except ProtectedArtifactError as exc:
        raise P0CalibrationIntegrityError(str(exc)) from exc


def _validate_run_snapshot(payload: Mapping[str, Any]) -> None:
    _require_exact_fields(
        payload,
        _run_body_fields() | {"head_transition_hash"},
        label="calibration run",
    )
    body = dict(payload)
    body.pop("head_transition_hash")
    _validate_run_body(body)
    _require_sha256(payload.get("head_transition_hash"), "run head_transition_hash")


def _validate_run_body(payload: Mapping[str, Any]) -> None:
    _require_exact_fields(payload, _run_body_fields(), label="calibration run body")
    if payload.get("schema_version") != P0_CALIBRATION_RUN_SCHEMA_VERSION:
        raise P0CalibrationSchemaError("Unsupported calibration-run schema_version.")
    _require_uuid(payload.get("cohort_id"), "run cohort_id")
    state = _require_choice(payload.get("state"), CALIBRATION_STATES, "run state")
    if payload.get("decision_scope") != P0_CALIBRATION_DECISION_SCOPE:
        raise P0CalibrationSchemaError("Calibration run decision_scope changed.")
    _require_nonnegative_int(payload.get("generation"), "run generation")
    _require_timestamp(payload.get("created_at"), "run created_at")
    _require_timestamp(payload.get("updated_at"), "run updated_at")
    _require_sha256(
        payload.get("execution_manifest_hash"), "run execution_manifest_hash"
    )
    _require_sha256(payload.get("evidence_bundle_hash"), "run evidence_bundle_hash")
    source = payload.get("source")
    population = payload.get("population")
    _required_mapping(source, "run source")
    _required_mapping(population, "run population")
    roles = _required_mapping(payload.get("roles"), "run roles")
    active_dispatches = _required_mapping(
        payload.get("active_dispatches"), "run active_dispatches"
    )
    recorded_receipts = _required_mapping(
        payload.get("recorded_receipts"), "run recorded_receipts"
    )
    _required_mapping(payload.get("artifacts"), "run artifacts")
    if set(roles) != set(CALIBRATION_ROLES):
        raise P0CalibrationSchemaError("Calibration run role inventory is incomplete.")
    for role in CALIBRATION_ROLES:
        _validate_role_state(roles[role], role=role)
    if len(active_dispatches) > 3:
        raise P0CalibrationSchemaError(
            "Run exceeds the three-worker concurrency limit."
        )
    for role, dispatch in active_dispatches.items():
        if role not in CALIBRATION_ROLES:
            raise P0CalibrationSchemaError(
                "Run active_dispatches contains an unknown role."
            )
        _validate_active_dispatch(dispatch, role=str(role))
    if len(recorded_receipts) > 8:
        raise P0CalibrationSchemaError(
            "Run exceeds the maximum frozen receipt-call inventory."
        )
    for receipt_id, binding in recorded_receipts.items():
        _portable_id(receipt_id, "run recorded receipt id")
        record = _required_mapping(binding, f"run recorded receipt {receipt_id}")
        _require_exact_fields(
            record,
            {
                "receipt_hash",
                "result_hash",
                "idempotency_key",
                "role",
                "attempt",
                "profile",
                "route_id",
                "response_bytes",
            },
            label=f"run recorded receipt {receipt_id}",
        )
        _require_sha256(
            record.get("receipt_hash"), f"run recorded receipt {receipt_id} hash"
        )
        _require_sha256(
            record.get("result_hash"), f"run recorded receipt {receipt_id} result hash"
        )
        _require_text(
            record.get("idempotency_key"),
            f"run recorded receipt {receipt_id} idempotency_key",
        )
        _require_choice(
            record.get("role"),
            CALIBRATION_ROLES,
            f"run recorded receipt {receipt_id} role",
        )
        if (
            _require_positive_int(
                record.get("attempt"), f"run recorded receipt {receipt_id} attempt"
            )
            > 2
        ):
            raise P0CalibrationSchemaError(
                f"Run recorded receipt {receipt_id} attempt exceeds two."
            )
        profile = _require_choice(
            record.get("profile"),
            ADMISSION_PROFILES,
            f"run recorded receipt {receipt_id} profile",
        )
        route_id = record.get("route_id")
        if profile == "local_no_egress" and route_id is not None:
            raise P0CalibrationSchemaError(
                f"Local recorded receipt {receipt_id} cannot name a route."
            )
        if profile == "external_authorized":
            _portable_id(route_id, f"run recorded receipt {receipt_id} route_id")
        _require_nonnegative_int(
            record.get("response_bytes"),
            f"run recorded receipt {receipt_id} response_bytes",
        )
    _require_choice(
        payload.get("admission_profile"),
        ADMISSION_PROFILES,
        "run admission_profile",
    )
    for name in ("authority_hash", "attestation_hash"):
        value = payload.get(name)
        if value is not None:
            _require_sha256(value, f"run {name}")
    _require_text_list(payload.get("limitations"), "run limitations")
    reasons = _require_text_list(
        payload.get("terminal_reason_codes"), "run terminal_reason_codes"
    )
    if state in {"BLOCKED_NO_SHIP", "REJECT"} and not reasons:
        raise P0CalibrationSchemaError(
            "Blocked or rejected calibration runs require terminal reasons."
        )
    if state not in {"BLOCKED_NO_SHIP", "REJECT"} and reasons:
        raise P0CalibrationSchemaError(
            "Nonterminal calibration runs cannot carry terminal reasons."
        )


def _run_body_fields() -> set[str]:
    return {
        "schema_version",
        "cohort_id",
        "state",
        "decision_scope",
        "generation",
        "created_at",
        "updated_at",
        "execution_manifest_hash",
        "evidence_bundle_hash",
        "source",
        "population",
        "admission_profile",
        "authority_hash",
        "attestation_hash",
        "roles",
        "active_dispatches",
        "recorded_receipts",
        "artifacts",
        "limitations",
        "terminal_reason_codes",
    }


def _validate_role_state(payload: Any, *, role: str) -> None:
    if not isinstance(payload, Mapping):
        raise P0CalibrationSchemaError(f"Run role {role} must be an object.")
    _require_exact_fields(
        payload,
        {
            "attempts",
            "status",
            "current_packet_id",
            "current_packet_hash",
            "packet_generation",
            "result_id",
            "receipt_id",
            "idempotency_key",
        },
        label=f"run role {role}",
    )
    attempts = _require_nonnegative_int(
        payload.get("attempts"), f"run role {role} attempts"
    )
    if attempts > 2:
        raise P0CalibrationSchemaError(
            f"Run role {role} exceeds its two-attempt limit."
        )
    _require_choice(
        payload.get("status"),
        {"not_issued", "packet_issued", "dispatch_started", "result_frozen"},
        f"run role {role} status",
    )
    for name in (
        "current_packet_id",
        "current_packet_hash",
        "result_id",
        "receipt_id",
        "idempotency_key",
    ):
        value = payload.get(name)
        if value is not None and not isinstance(value, str):
            raise P0CalibrationSchemaError(
                f"Run role {role} {name} must be text or null."
            )
    generation = payload.get("packet_generation")
    if generation is not None:
        _require_nonnegative_int(generation, f"run role {role} packet_generation")


def _validate_active_dispatch(payload: Any, *, role: str) -> None:
    dispatch = _required_mapping(payload, f"active dispatch {role}")
    _require_exact_fields(
        dispatch,
        {
            "role",
            "attempt",
            "packet_id",
            "packet_hash",
            "idempotency_key",
            "generation",
            "status",
            "started_at",
            "deadline_at",
        },
        label=f"active dispatch {role}",
    )
    if dispatch.get("role") != role or dispatch.get("status") != "started":
        raise P0CalibrationSchemaError(
            f"Active dispatch {role} identity/status is inconsistent."
        )
    if (
        _require_positive_int(
            dispatch.get("attempt"), f"active dispatch {role} attempt"
        )
        > 2
    ):
        raise P0CalibrationSchemaError(f"Active dispatch {role} attempt exceeds two.")
    _require_uuid(dispatch.get("packet_id"), f"active dispatch {role} packet_id")
    _require_sha256(dispatch.get("packet_hash"), f"active dispatch {role} packet_hash")
    _require_text(
        dispatch.get("idempotency_key"),
        f"active dispatch {role} idempotency_key",
    )
    _require_positive_int(
        dispatch.get("generation"), f"active dispatch {role} generation"
    )
    started = _parse_timestamp(
        dispatch.get("started_at"), f"active dispatch {role} started_at"
    )
    deadline = _parse_timestamp(
        dispatch.get("deadline_at"), f"active dispatch {role} deadline_at"
    )
    if deadline <= started:
        raise P0CalibrationSchemaError(
            f"Active dispatch {role} deadline must follow its start."
        )


def _validate_transition(payload: Mapping[str, Any]) -> None:
    _require_exact_fields(
        payload,
        {
            "schema_version",
            "transition_id",
            "sequence",
            "cohort_id",
            "event_type",
            "from_state",
            "to_state",
            "decision_scope",
            "occurred_at",
            "previous_transition_hash",
            "expected_generation",
            "reason_codes",
            "details",
            "artifacts",
            "resulting_run_body",
            "transition_hash",
        },
        label="calibration transition",
    )
    if payload.get("schema_version") != P0_CALIBRATION_TRANSITION_SCHEMA_VERSION:
        raise P0CalibrationIntegrityError("Transition schema_version is unsupported.")
    _require_uuid(payload.get("transition_id"), "transition_id")
    _require_positive_int(payload.get("sequence"), "transition sequence")
    _require_uuid(payload.get("cohort_id"), "transition cohort_id")
    _portable_id(payload.get("event_type"), "transition event_type")
    from_state = _require_choice(
        payload.get("from_state"), CALIBRATION_STATES, "transition from_state"
    )
    to_state = _require_choice(
        payload.get("to_state"), CALIBRATION_STATES, "transition to_state"
    )
    if to_state != from_state and to_state not in _ALLOWED_TRANSITIONS[from_state]:
        raise P0CalibrationIntegrityError("Transition edge is illegal.")
    expected_scope = (
        P0_CALIBRATION_DECISION_SCOPE
        if to_state in CALIBRATION_TERMINAL_STATES
        else None
    )
    if payload.get("decision_scope") != expected_scope:
        raise P0CalibrationIntegrityError("Transition decision_scope is inconsistent.")
    _require_timestamp(payload.get("occurred_at"), "transition occurred_at")
    _require_sha256(
        payload.get("previous_transition_hash"),
        "transition previous_transition_hash",
    )
    _require_nonnegative_int(
        payload.get("expected_generation"), "transition expected_generation"
    )
    _require_text_list(payload.get("reason_codes"), "transition reason_codes")
    if not isinstance(payload.get("details"), Mapping):
        raise P0CalibrationIntegrityError("Transition details must be an object.")
    artifacts = payload.get("artifacts")
    if not isinstance(artifacts, list):
        raise P0CalibrationIntegrityError("Transition artifacts must be a list.")
    for artifact in artifacts:
        if not isinstance(artifact, Mapping) or set(artifact) != {"path", "sha256"}:
            raise P0CalibrationIntegrityError(
                "Transition artifact binding is malformed."
            )
        validate_portable_relative_path(
            _require_text(artifact.get("path"), "transition artifact path")
        )
        _require_sha256(artifact.get("sha256"), "transition artifact sha256")
    body = payload.get("resulting_run_body")
    if not isinstance(body, Mapping):
        raise P0CalibrationIntegrityError(
            "Transition resulting_run_body must be an object."
        )
    _validate_run_body(body)
    _require_sha256(payload.get("transition_hash"), "transition hash")


def _validate_agent_packet(payload: Mapping[str, Any]) -> None:
    _require_exact_fields(
        payload,
        {
            "schema_version",
            "cohort_id",
            "packet_id",
            "role",
            "attempt",
            "idempotency_key",
            "authority_hash",
            "attestation_hash",
            "evidence_bundle_hash",
            "objective",
            "evidence_bundle",
            "intake_proposals",
            "result_contract",
            "budgets",
            "forbidden_actions",
        },
        label="agent packet",
    )
    if payload.get("schema_version") != P0_CALIBRATION_AGENT_PACKET_SCHEMA_VERSION:
        raise P0CalibrationSchemaError("Unsupported agent-packet schema_version.")
    _require_uuid(payload.get("cohort_id"), "packet cohort_id")
    _require_uuid(payload.get("packet_id"), "packet_id")
    role = _require_choice(payload.get("role"), CALIBRATION_ROLES, "packet role")
    if _require_positive_int(payload.get("attempt"), "packet attempt") > 2:
        raise P0CalibrationSchemaError("Packet attempt exceeds two.")
    _require_text(payload.get("idempotency_key"), "packet idempotency_key")
    _require_sha256(payload.get("authority_hash"), "packet authority_hash")
    _require_sha256(payload.get("attestation_hash"), "packet attestation_hash")
    _require_sha256(payload.get("evidence_bundle_hash"), "packet evidence hash")
    _require_text(payload.get("objective"), "packet objective")
    evidence = _required_mapping(
        payload.get("evidence_bundle"), "packet evidence_bundle"
    )
    if evidence.get("priority_blind") is not True:
        raise P0CalibrationSchemaError(
            "Packet evidence_bundle must remain priority-blind."
        )
    proposals = payload.get("intake_proposals")
    if not isinstance(proposals, list):
        raise P0CalibrationSchemaError("Packet intake_proposals must be a list.")
    if role != "verifier" and proposals:
        raise P0CalibrationSchemaError(
            "Intake packets cannot contain another role's proposal."
        )
    if role == "verifier" and len(proposals) != 3:
        raise P0CalibrationSchemaError(
            "Verifier packet must contain exactly three intake proposals."
        )
    _required_mapping(payload.get("result_contract"), "packet result_contract")
    _required_mapping(payload.get("budgets"), "packet budgets")
    _require_text_list(payload.get("forbidden_actions"), "packet forbidden_actions")
    _assert_packet_has_no_private_policy_fields(payload)


def _validate_agent_result(payload: Mapping[str, Any]) -> None:
    role = _require_choice(payload.get("role"), CALIBRATION_ROLES, "result role")
    semantic_field = "verification" if role == "verifier" else "proposal"
    base_fields = {
        "schema_version",
        "result_id",
        "cohort_id",
        "packet_id",
        "role",
        "attempt",
        "packet_hash",
        "idempotency_key",
        "status",
    }
    status = payload.get("status")
    if status == "complete":
        expected_fields = base_fields | {semantic_field}
    elif status == "dispatch_failed":
        expected_fields = base_fields | {"failure"}
    else:
        raise P0CalibrationSchemaError(
            "Agent result status must be complete or dispatch_failed."
        )
    _require_exact_fields(
        payload,
        expected_fields,
        label="agent result",
    )
    if payload.get("schema_version") != P0_CALIBRATION_AGENT_RESULT_SCHEMA_VERSION:
        raise P0CalibrationSchemaError("Unsupported agent-result schema_version.")
    _require_uuid(payload.get("cohort_id"), "result cohort_id")
    _require_uuid(payload.get("result_id"), "result_id")
    _require_uuid(payload.get("packet_id"), "result packet_id")
    if _require_positive_int(payload.get("attempt"), "result attempt") > 2:
        raise P0CalibrationSchemaError("Result attempt exceeds two.")
    _require_sha256(payload.get("packet_hash"), "result packet_hash")
    _require_text(payload.get("idempotency_key"), "result idempotency_key")
    if status == "complete":
        _required_mapping(payload.get(semantic_field), f"result {semantic_field}")
        return
    failure = _required_mapping(payload.get("failure"), "result failure")
    _require_exact_fields(
        failure,
        {
            "reason_code",
            "message",
            "dispatch_started",
            "retry_allowed",
        },
        label="agent result failure",
    )
    _require_choice(
        failure.get("reason_code"),
        _EXTERNAL_DISPATCH_FAILURE_REASONS,
        "result failure reason_code",
    )
    message = _require_text(failure.get("message"), "result failure message")
    if (
        len(message.encode("utf-8")) > _MAX_DISPATCH_FAILURE_MESSAGE_BYTES
        or not message.isprintable()
    ):
        raise P0CalibrationSchemaError(
            "Result failure message must be printable text no larger than "
            f"{_MAX_DISPATCH_FAILURE_MESSAGE_BYTES} UTF-8 bytes."
        )
    _require_bool(failure.get("dispatch_started"), "result failure dispatch_started")
    if _require_bool(failure.get("retry_allowed"), "result failure retry_allowed"):
        raise P0CalibrationSchemaError("Result failure retry_allowed must be false.")


def _validate_dispatch_receipt(payload: Mapping[str, Any]) -> None:
    if payload.get("schema_version") != P0_CALIBRATION_DISPATCH_RECEIPT_SCHEMA_VERSION:
        raise P0CalibrationSchemaError("Unsupported dispatch-receipt schema_version.")
    _require_uuid(payload.get("cohort_id"), "receipt cohort_id")
    _portable_id(payload.get("receipt_id"), "receipt_id")
    _require_choice(payload.get("role"), CALIBRATION_ROLES, "receipt role")
    if _require_positive_int(payload.get("attempt"), "receipt attempt") > 2:
        raise P0CalibrationSchemaError("Receipt attempt exceeds two.")
    _require_nonnegative_int(payload.get("generation"), "receipt generation")
    _require_sha256(payload.get("head_transition_hash"), "receipt head_transition_hash")
    _require_uuid(payload.get("packet_id"), "receipt packet_id")
    for name in (
        "packet_hash",
        "authority_hash",
        "attestation_hash",
        "access_audit_hash",
    ):
        _require_sha256(payload.get(name), f"receipt {name}")
    _require_text(payload.get("idempotency_key"), "receipt idempotency_key")
    _require_bool(payload.get("started"), "receipt started")
    status = _require_text(payload.get("status"), "receipt status")
    response_hash = payload.get("response_hash")
    if status == "complete":
        _require_sha256(response_hash, "receipt response_hash")
    elif response_hash is not None:
        _require_sha256(response_hash, "receipt response_hash")
    _require_nonnegative_int(payload.get("response_bytes"), "receipt response_bytes")
    local_fields = {
        "schema_version",
        "receipt_id",
        "receipt_hash",
        "cohort_id",
        "generation",
        "head_transition_hash",
        "role",
        "attempt",
        "idempotency_key",
        "packet_id",
        "packet_hash",
        "authority_hash",
        "attestation_hash",
        "access_audit_hash",
        "runtime",
        "runtime_executable_sha256",
        "image",
        "image_digest",
        "command_hash",
        "container_name",
        "started",
        "status",
        "cleanup_status",
        "exit_code",
        "response_hash",
        "response_bytes",
        "stdout",
        "stderr",
    }
    external_fields = {
        "schema_version",
        "receipt_id",
        "receipt_hash",
        "cohort_id",
        "generation",
        "head_transition_hash",
        "role",
        "attempt",
        "idempotency_key",
        "packet_id",
        "packet_hash",
        "authority_hash",
        "attestation_hash",
        "access_audit_hash",
        "broker_id",
        "route_id",
        "runtime_identity",
        "image_identity",
        "started",
        "status",
        "response_hash",
        "response_bytes",
    }
    if set(payload) == local_fields:
        for name in (
            "receipt_hash",
            "runtime_executable_sha256",
            "image_digest",
            "command_hash",
        ):
            _require_sha256(payload.get(name), f"receipt {name}")
        for name in ("runtime", "image", "container_name", "cleanup_status"):
            _require_text(payload.get(name), f"receipt {name}")
        if not isinstance(payload.get("stdout"), Mapping) or not isinstance(
            payload.get("stderr"), Mapping
        ):
            raise P0CalibrationSchemaError("Receipt stream evidence must be objects.")
    elif set(payload) == external_fields:
        _require_sha256(payload.get("receipt_hash"), "receipt receipt_hash")
        for name in ("broker_id", "route_id", "runtime_identity", "image_identity"):
            _require_text(payload.get(name), f"receipt {name}")
    else:
        _require_exact_fields(payload, local_fields, label="dispatch receipt")


def _validate_verification_report(payload: Mapping[str, Any]) -> None:
    _require_exact_fields(
        payload,
        {
            "schema_version",
            "cohort_id",
            "state",
            "generation",
            "decision_scope",
            "ok",
            "eligible",
            "next_state",
            "advanced",
            "checks",
            "artifacts",
            "limitations",
        },
        label="verification report",
    )
    if (
        payload.get("schema_version")
        != P0_CALIBRATION_VERIFICATION_REPORT_SCHEMA_VERSION
    ):
        raise P0CalibrationSchemaError(
            "Unsupported verification-report schema_version."
        )
    _require_uuid(payload.get("cohort_id"), "verification cohort_id")
    _require_bool(payload.get("ok"), "verification ok")
    _require_bool(payload.get("eligible"), "verification eligible")
    _require_bool(payload.get("advanced"), "verification advanced")
    _require_nonnegative_int(payload.get("generation"), "verification generation")
    if payload.get("decision_scope") != P0_CALIBRATION_DECISION_SCOPE:
        raise P0CalibrationSchemaError("Verification decision_scope changed.")
    _require_choice(payload.get("state"), CALIBRATION_STATES, "verification state")
    next_state = payload.get("next_state")
    if next_state is not None:
        _require_choice(next_state, CALIBRATION_STATES, "verification next_state")
    checks = payload.get("checks")
    if not isinstance(checks, list) or any(
        not isinstance(check, Mapping) for check in checks
    ):
        raise P0CalibrationSchemaError("Verification checks must be a list of objects.")
    if not isinstance(payload.get("artifacts"), Mapping):
        raise P0CalibrationSchemaError("Verification artifacts must be an object.")
    _require_text_list(payload.get("limitations"), "verification limitations")


def _normalize_bound_roots(roots: Sequence[str | Path]) -> tuple[str, ...]:
    normalized: dict[str, str] = {}
    for raw in roots:
        value = os.path.abspath(os.fspath(raw))
        trimmed = value.rstrip("\\/") or value
        if trimmed in {"/", "\\"}:
            raise P0CalibrationIntegrityError(
                "Filesystem roots cannot be embedded in outbound evidence guards."
            )
        variants = {trimmed, trimmed.replace("\\", "/")}
        if os.name == "nt":
            variants.add(trimmed.replace("/", "\\"))
        for variant in variants:
            identity = variant.casefold() if os.name == "nt" else variant
            normalized.setdefault(identity, variant)
    return tuple(
        sorted(
            normalized.values(),
            key=lambda value: (-len(value), value.casefold(), value),
        )
    )


def _redact_outbound_text(
    value: str,
    *,
    bound_roots: Sequence[str],
) -> tuple[str, list[dict[str, Any]]]:
    """Deterministically remove path and credential material from one string."""

    redacted = value
    counts: dict[str, int] = {}

    def apply(
        pattern: re.Pattern[str],
        kind: str,
        replacement: str | Callable[[re.Match[str]], str],
    ) -> None:
        nonlocal redacted
        redacted, count = pattern.subn(replacement, redacted)
        if count:
            counts[kind] = counts.get(kind, 0) + count

    for root in bound_roots:
        apply(
            re.compile(
                re.escape(root),
                re.IGNORECASE if os.name == "nt" else 0,
            ),
            "bound-absolute-root",
            "[REDACTED:bound-absolute-root]",
        )
    apply(
        _PRIVATE_KEY_BLOCK_RE,
        "private-key-block",
        "[REDACTED:private-key-block]",
    )
    apply(
        _URI_USERINFO_RE,
        "uri-credentials",
        lambda match: str(match.group("scheme")) + "[REDACTED:uri-credentials]@",
    )
    for kind, pattern in _COMMON_TOKEN_PATTERNS:
        apply(pattern, kind, f"[REDACTED:{kind}]")

    def replace_assignment(match: re.Match[str]) -> str:
        quote = (
            '"'
            if match.group("double_quoted") is not None
            else "'"
            if match.group("single_quoted") is not None
            else ""
        )
        return (
            str(match.group("prefix"))
            + quote
            + "[REDACTED:sensitive-assignment]"
            + quote
        )

    apply(
        _SENSITIVE_ASSIGNMENT_RE,
        "sensitive-assignment",
        replace_assignment,
    )
    apply(
        _SENSITIVE_NATURAL_LANGUAGE_RE,
        "sensitive-natural-language",
        replace_assignment,
    )
    apply(_FILE_URI_RE, "absolute-host-path", "[REDACTED:absolute-host-path]")
    apply(
        _WINDOWS_ABSOLUTE_PATH_RE,
        "absolute-host-path",
        "[REDACTED:absolute-host-path]",
    )
    apply(
        _POSIX_ABSOLUTE_PATH_RE,
        "absolute-host-path",
        "[REDACTED:absolute-host-path]",
    )
    return redacted, [{"kind": kind, "count": counts[kind]} for kind in sorted(counts)]


def _sanitize_outbound_value(
    value: Any,
    *,
    bound_roots: Sequence[str],
    json_path: str = "$",
) -> tuple[Any, list[dict[str, Any]]]:
    redactions: list[dict[str, Any]] = []
    if isinstance(value, Mapping):
        sanitized_mapping: dict[str, Any] = {}
        for raw_key, child in value.items():
            key = str(raw_key)
            sanitized_key, key_redactions = _redact_outbound_text(
                key,
                bound_roots=bound_roots,
            )
            if key_redactions or sanitized_key != key:
                raise P0CalibrationIntegrityError(
                    "Outbound evidence contains an unsafe mapping key that cannot "
                    "be redacted without changing its contract."
                )
            sanitized_child, child_redactions = _sanitize_outbound_value(
                child,
                bound_roots=bound_roots,
                json_path=f"{json_path}.{key}",
            )
            sanitized_mapping[key] = sanitized_child
            redactions.extend(child_redactions)
        return sanitized_mapping, redactions
    if isinstance(value, list):
        sanitized_list = []
        for index, child in enumerate(value):
            sanitized_child, child_redactions = _sanitize_outbound_value(
                child,
                bound_roots=bound_roots,
                json_path=f"{json_path}[{index}]",
            )
            sanitized_list.append(sanitized_child)
            redactions.extend(child_redactions)
        return sanitized_list, redactions
    if isinstance(value, str):
        sanitized, text_redactions = _redact_outbound_text(
            value,
            bound_roots=bound_roots,
        )
        if text_redactions:
            redactions.append(
                {
                    "json_path": json_path,
                    "redactions": text_redactions,
                }
            )
        return sanitized, redactions
    return value, redactions


def _assert_outbound_payload_safe(
    payload: Any,
    *,
    bound_roots: Sequence[str],
) -> None:
    sanitized, redactions = _sanitize_outbound_value(
        payload,
        bound_roots=bound_roots,
    )
    if sanitized != payload or redactions:
        raise P0CalibrationIntegrityError(
            "Outbound packet still matches the credential or host-path denylist."
        )


def _assert_packet_has_no_private_policy_fields(payload: Mapping[str, Any]) -> None:
    forbidden = {
        "absolute_path",
        "api_key",
        "candidate",
        "candidate_policy",
        "candidate_priority",
        "credential",
        "credentials",
        "current_priority",
        "host_path",
        "password",
        "priority",
        "provider_credentials",
        "score",
        "secret",
        "token",
        "weight",
        "weights",
    }
    path_keys = {"path", "source_path"}

    def visit(value: Any, *, key: str | None = None) -> None:
        if isinstance(value, Mapping):
            for raw_key, child in value.items():
                normalized = str(raw_key).casefold()
                if normalized in forbidden:
                    raise P0CalibrationSchemaError(
                        f"Agent packet contains forbidden field {raw_key!r}."
                    )
                visit(child, key=normalized)
        elif isinstance(value, list):
            for child in value:
                visit(child, key=key)
        elif key in path_keys and isinstance(value, str):
            raw = value.replace("\\", "/")
            if raw.startswith("/") or re.match(r"^[A-Za-z]:/", raw):
                raise P0CalibrationSchemaError(
                    "Agent packet contains an absolute host path."
                )

    visit(payload)
    _assert_outbound_payload_safe(payload, bound_roots=())


def _require_exact_fields(
    payload: Mapping[str, Any], fields: set[str], *, label: str
) -> None:
    if not isinstance(payload, Mapping):
        raise P0CalibrationSchemaError(f"{label.title()} must be an object.")
    actual = set(payload)
    if actual != fields:
        missing = sorted(fields - actual)
        unknown = sorted(actual - fields)
        detail = []
        if missing:
            detail.append("missing " + ", ".join(missing))
        if unknown:
            detail.append("unknown " + ", ".join(unknown))
        raise P0CalibrationSchemaError(
            f"{label.title()} fields are invalid: {'; '.join(detail)}."
        )


def _required_mapping(value: Any, label: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise P0CalibrationSchemaError(f"{label} must be an object.")
    return value


def _require_text(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value or value != value.strip():
        raise P0CalibrationSchemaError(f"{label} must be non-empty trimmed text.")
    return value


def _require_text_list(value: Any, label: str) -> list[str]:
    if not isinstance(value, list) or any(
        not isinstance(item, str) or not item or item != item.strip() for item in value
    ):
        raise P0CalibrationSchemaError(f"{label} must be a list of trimmed strings.")
    return list(value)


def _require_bool(value: Any, label: str) -> bool:
    if not isinstance(value, bool):
        raise P0CalibrationSchemaError(f"{label} must be boolean.")
    return value


def _require_nonnegative_int(value: Any, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise P0CalibrationSchemaError(f"{label} must be a non-negative integer.")
    return value


def _require_positive_int(value: Any, label: str) -> int:
    parsed = _require_nonnegative_int(value, label)
    if parsed < 1:
        raise P0CalibrationSchemaError(f"{label} must be greater than zero.")
    return parsed


def _require_choice(value: Any, choices: Iterable[str], label: str) -> str:
    parsed = _require_text(value, label)
    allowed = frozenset(choices)
    if parsed not in allowed:
        raise P0CalibrationSchemaError(
            f"{label} must be one of: {', '.join(sorted(allowed))}."
        )
    return parsed


def _require_sha256(value: Any, label: str) -> str:
    parsed = _require_text(value, label)
    if not _SHA256_RE.fullmatch(parsed):
        raise P0CalibrationSchemaError(f"{label} must be a lowercase sha256 digest.")
    return parsed


def _require_uuid(value: Any, label: str) -> str:
    parsed = _require_text(value, label)
    try:
        normalized = str(uuid.UUID(parsed))
    except ValueError as exc:
        raise P0CalibrationSchemaError(f"{label} must be a UUID.") from exc
    if parsed != normalized:
        raise P0CalibrationSchemaError(f"{label} must be a canonical UUID.")
    return parsed


def _require_timestamp(value: Any, label: str) -> str:
    parsed = _require_text(value, label)
    if not parsed.endswith("Z"):
        raise P0CalibrationSchemaError(f"{label} must be a UTC Z timestamp.")
    try:
        timestamp = datetime.fromisoformat(parsed[:-1] + "+00:00")
    except ValueError as exc:
        raise P0CalibrationSchemaError(f"{label} is not an ISO timestamp.") from exc
    if timestamp.tzinfo != timezone.utc:
        raise P0CalibrationSchemaError(f"{label} must use UTC.")
    return parsed


def _parse_timestamp(value: Any, label: str) -> datetime:
    parsed = _require_timestamp(value, label)
    return datetime.fromisoformat(parsed[:-1] + "+00:00")


def _portable_id(value: Any, label: str) -> str:
    parsed = _require_text(value, label)
    if not _PORTABLE_ID_RE.fullmatch(parsed):
        raise P0CalibrationSchemaError(f"{label} is not a portable identifier.")
    return parsed


def _portable_relative_path(value: Any, *, label: str) -> str:
    if not isinstance(value, str):
        raise P0CalibrationSchemaError(f"{label} must be text.")
    try:
        return validate_portable_relative_path(value)
    except ProtectedArtifactIntegrityError as exc:
        raise P0CalibrationSchemaError(f"{label} is not portable: {exc}") from exc


def _assert_not_link_or_reparse(path: Path, label: str) -> None:
    try:
        status = path.lstat()
    except OSError as exc:
        raise P0CalibrationIntegrityError(f"Cannot inspect {label}: {exc}") from exc
    if (
        stat.S_ISLNK(status.st_mode)
        or bool(getattr(status, "st_reparse_tag", 0))
        or bool(getattr(status, "st_file_attributes", 0) & _REPARSE_ATTRIBUTE)
    ):
        raise P0CalibrationIntegrityError(
            f"{label} must not be a symlink or reparse point."
        )


def _assert_regular_directory(path: Path, label: str) -> None:
    _assert_not_link_or_reparse(path, label)
    if not path.is_dir():
        raise P0CalibrationIntegrityError(f"{label.title()} is not a directory.")


def _assert_portable_leaf_name(value: str, label: str) -> None:
    try:
        validate_portable_relative_path(value)
    except ProtectedArtifactIntegrityError as exc:
        raise P0CalibrationIntegrityError(
            f"{label.title()} name is not portable: {exc}"
        ) from exc


def _paths_overlap(left: Path, right: Path) -> bool:
    try:
        left.relative_to(right)
        return True
    except ValueError:
        pass
    try:
        right.relative_to(left)
        return True
    except ValueError:
        return False


def _sha256_json(payload: Mapping[str, Any]) -> str:
    return "sha256:" + hashlib.sha256(canonical_json_bytes(payload)).hexdigest()


def _json_round_trip(payload: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(payload, Mapping):
        raise P0CalibrationSchemaError("Calibration payload must be an object.")
    try:
        encoded = json.dumps(
            payload,
            ensure_ascii=False,
            allow_nan=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        normalized = json.loads(encoded)
    except (TypeError, ValueError) as exc:
        raise P0CalibrationSchemaError(
            f"Calibration payload is not canonical JSON data: {exc}"
        ) from exc
    if not isinstance(normalized, dict):
        raise P0CalibrationSchemaError("Calibration payload must be an object.")
    return normalized


def _unique_json_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result = {}
    for key, value in pairs:
        if key in result:
            raise P0CalibrationIntegrityError(
                f"JSON object contains duplicate key {key!r}."
            )
        result[key] = value
    return result


def _reject_json_constant(value: str) -> None:
    raise P0CalibrationIntegrityError(f"JSON constant {value!r} is not permitted.")


def _utc_now() -> str:
    return _format_timestamp(datetime.now(timezone.utc))


def _format_timestamp(value: datetime) -> str:
    return (
        value.astimezone(timezone.utc)
        .isoformat(timespec="seconds")
        .replace("+00:00", "Z")
    )


def _stale_active_dispatches(run: P0CalibrationRun) -> list[str]:
    now = datetime.now(timezone.utc)
    stale = []
    for role, raw in run.payload["active_dispatches"].items():
        if not isinstance(raw, Mapping) or raw.get("status") != "started":
            stale.append(str(role))
            continue
        try:
            deadline = _parse_timestamp(
                raw.get("deadline_at"), f"active dispatch {role} deadline_at"
            )
        except P0CalibrationSchemaError:
            stale.append(str(role))
            continue
        if now >= deadline:
            stale.append(str(role))
    return sorted(stale)


def _bounded_error(error: BaseException) -> str:
    text = " ".join(str(error).split())
    return text[:2048] or type(error).__name__


def _deprecated_calibration_alias(
    replacement: Callable[..., Any],
    legacy_name: str,
) -> Callable[..., Any]:
    """Return a signature-preserving compatibility wrapper."""

    @wraps(replacement)
    def deprecated(*args: Any, **kwargs: Any) -> Any:
        warnings.warn(
            f"{legacy_name} is deprecated; use {replacement.__name__} instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        return replacement(*args, **kwargs)

    deprecated.__name__ = legacy_name
    deprecated.__qualname__ = legacy_name
    return deprecated


admit_p0_calibration_run = _deprecated_calibration_alias(
    admit_calibration_run,
    "admit_p0_calibration_run",
)
build_p0_calibration_agent_packet = _deprecated_calibration_alias(
    build_calibration_agent_packet,
    "build_p0_calibration_agent_packet",
)
dispatch_p0_calibration_agent = _deprecated_calibration_alias(
    dispatch_calibration_agent,
    "dispatch_p0_calibration_agent",
)
get_p0_calibration_run_status = _deprecated_calibration_alias(
    get_calibration_run_status,
    "get_p0_calibration_run_status",
)
prepare_p0_calibration_run = _deprecated_calibration_alias(
    prepare_calibration_run,
    "prepare_p0_calibration_run",
)
record_p0_calibration_agent_result = _deprecated_calibration_alias(
    record_calibration_agent_result,
    "record_p0_calibration_agent_result",
)
verify_p0_calibration_run = _deprecated_calibration_alias(
    verify_calibration_run,
    "verify_p0_calibration_run",
)


__all__ = [
    "ADMISSION_PROFILES",
    "CALIBRATION_ROLES",
    "CALIBRATION_STATES",
    "CALIBRATION_TERMINAL_STATES",
    "INTAKE_ROLES",
    "P0CalibrationAgentPacket",
    "P0CalibrationAgentResult",
    "P0CalibrationDispatchReceipt",
    "P0CalibrationError",
    "P0CalibrationIntegrityError",
    "P0CalibrationRecoveryError",
    "P0CalibrationRun",
    "P0CalibrationSchemaError",
    "P0CalibrationStatus",
    "P0CalibrationTransitionError",
    "P0CalibrationVerificationReport",
    "admit_calibration_run",
    "admit_p0_calibration_run",
    "build_calibration_agent_packet",
    "build_p0_calibration_agent_packet",
    "dispatch_calibration_agent",
    "dispatch_p0_calibration_agent",
    "get_calibration_run_status",
    "get_p0_calibration_run_status",
    "prepare_calibration_run",
    "prepare_p0_calibration_run",
    "record_calibration_agent_result",
    "record_p0_calibration_agent_result",
    "verify_calibration_run",
    "verify_p0_calibration_run",
]
