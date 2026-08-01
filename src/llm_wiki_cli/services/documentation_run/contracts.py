"""Persisted contracts for documentation runs."""

from __future__ import annotations

from typing import TYPE_CHECKING

from .dependencies import *

if TYPE_CHECKING:
    from .packet import _render_packet_markdown
    from .schema import (
        _assert_no_forbidden_packet_fields,
        _portable_path_tuple,
        _require_exact_fields,
        _required_agent_result_text,
        _require_utc_timestamp,
        _text_tuple,
        _validate_agent_result_findings,
        _validate_imported_page_edits,
        _validate_run_payload,
    )

RUN_CONTROL_DIR = ".llm-wiki-docs"

RUN_FILENAME = "run.json"

POLICY_FILENAME = "policy.json"

REFRESH_TRANSACTION_FILENAME = "refresh-transaction.json"

_INITIAL_PREPARE_OWNED_ROOTS = (RUN_CONTROL_DIR, "wiki", "site", "_site")

SUPPORTED_RUN_STATES = frozenset(
    {
        "prepared",
        "baseline_ready",
        "wiki_enrichment",
        "user_docs",
        "review",
        "publish_ready",
        "blocked",
    }
)

SUPPORTED_BASELINE_STRATEGIES = frozenset({"bootstrap_source", "adopt_existing_wiki"})

SUPPORTED_AGENT_STAGES = frozenset({"wiki-enrichment", "user-docs", "review"})

SUPPORTED_AGENT_RESULT_STATUSES = frozenset({"complete", "partial", "blocked"})

_AGENT_RESULT_FIELDS = frozenset(
    {
        "schema_version",
        "run_id",
        "stage",
        "status",
        "changed_wiki_paths",
        "reused_work_ids",
        "completed_work_ids",
        "deferred_work_ids",
        "claims_evidence_pages",
        "claim_evidence",
        "runtime_captures",
        "unresolved_unknowns",
        "unsupported_source_notices",
        "requested_follow_up_checks",
        "reported_source_writes",
        "reported_input_wiki_writes",
        "reported_generated_block_edits",
        "imported_page_edits",
        "deferral_rationales",
        "findings",
    }
)

_REQUIRED_AGENT_RESULT_FIELDS = _AGENT_RESULT_FIELDS - {
    "claim_evidence",
    "deferral_rationales",
    "imported_page_edits",
    "runtime_captures",
}

_IMPORTED_PAGE_EDIT_FIELDS = frozenset(
    {
        "work_id",
        "canonical_path",
        "before_hash",
        "after_hash",
        "evidence",
        "rationale",
    }
)

_AGENT_FINDING_FIELDS = frozenset(
    {
        "id",
        "category",
        "severity",
        "status",
        "message",
        "evidence",
        "path",
        "paths",
        "target",
        "targets",
        "rationale",
    }
)

_AGENT_FINDING_STATUSES = frozenset({"open", "resolved", "deferred", "superseded"})

_TERMINAL_AGENT_FINDING_STATUSES = _AGENT_FINDING_STATUSES - {"open"}

_AGENT_FINDING_SEVERITIES = frozenset({"low", "medium", "high"})

SUPPORTED_FRESHNESS_POLICIES = frozenset(
    {"require-current", "refresh-snapshot", "allow-unverified"}
)

SUPPORTED_DOCUMENTATION_KNOWLEDGE_MODES = frozenset(
    {"off", "public-portable", "internal"}
)

DEFAULT_DOCUMENTATION_SKILLS = (
    "agent-docs",
    "wiki-semantic-enhance",
    "user-docs-author",
    "onboarding-guide",
    "usage-examples",
    "doc-review",
    "publish-docs",
)

_GENERATED_MARKER = "Auto-generated"

_DO_NOT_EDIT_MARKER = "Do not edit by hand"

_NATIVE_ARTIFACT_PATHS = frozenset(
    {
        ".llm-wiki-manifest.json",
        ".llm-wiki-surface.json",
        KNOWLEDGE_INDEX_FILENAME,
        GOVERNANCE_FILENAME,
        VERIFICATION_RECEIPT_FILENAME,
    }
)

_NATIVE_REFRESH_MUTABLE_PATHS = _NATIVE_ARTIFACT_PATHS - {
    VERIFICATION_RECEIPT_FILENAME
}

_MAX_BUILDER_LOG_BYTES = 10_000

_PACKET_FORBIDDEN_FIELDS = frozenset(
    {
        "access_token",
        "api_key",
        "apikey",
        "auth_token",
        "authorization",
        "base_url",
        "client_secret",
        "cookie",
        "cookies",
        "credential",
        "credentials",
        "endpoint",
        "headers",
        "model",
        "model_id",
        "model_name",
        "password",
        "provider",
        "provider_family",
        "provider_id",
        "provider_name",
        "secret",
        "sdk",
        "token",
    }
)

_PACKET_FORBIDDEN_KEY_SUFFIXES = frozenset(
    {
        "access_token",
        "api_key",
        "apikey",
        "auth_token",
        "authorization",
        "base_url",
        "client_secret",
        "cookie",
        "credentials",
        "endpoint",
        "model",
        "model_id",
        "model_name",
        "password",
        "provider",
        "provider_id",
        "provider_name",
        "secret",
        "token",
    }
)

_CONTROL_SNAPSHOT_EVIDENCE_KEYS = (
    "source_baseline",
    "bootstrap",
    "wiki_input",
    "workspace_refresh",
    "continuation",
    "native_refresh",
    "wiki_baseline",
    "generated_ownership",
    "semantic_worklist",
    "semantic_readiness",
    "p0_calibration_census",
    "p0_calibration_shadow",
)

_ALLOWED_TRANSITIONS: dict[str, frozenset[str]] = {
    "prepared": frozenset({"baseline_ready", "blocked"}),
    "baseline_ready": frozenset({"wiki_enrichment", "blocked"}),
    "wiki_enrichment": frozenset({"user_docs", "blocked"}),
    "user_docs": frozenset({"review", "blocked"}),
    "review": frozenset({"wiki_enrichment", "user_docs", "publish_ready", "blocked"}),
    "publish_ready": frozenset(),
    "blocked": frozenset(
        {"prepared", "baseline_ready", "wiki_enrichment", "user_docs", "review"}
    ),
}

class DocumentationRunError(RuntimeError):
    """Base error raised by the documentation lifecycle service."""


class DocumentationSchemaError(DocumentationRunError):
    """Raised when a persisted or returned contract is invalid."""


class DocumentationTransitionError(DocumentationRunError):
    """Raised when a stage transition violates the lifecycle graph."""


class DocumentationIntegrityError(DocumentationRunError):
    """Raised when source, input-wiki, or generated ownership changed."""


class DocumentationPersistedStateError(
    DocumentationIntegrityError,
    DocumentationSchemaError,
):
    """Raised when a stored documentation-run contract is corrupt."""


@dataclass(frozen=True)
class DocumentationIntakeBrief:
    project_purpose: str
    audiences: tuple[str, ...]
    audience_intent: dict[str, str]
    live_service: dict[str, Any]
    provenance: dict[str, Any]
    recorded_at: str

    @classmethod
    def from_values(
        cls,
        *,
        project_purpose: str | None,
        audiences: Iterable[str] | None,
        audience_intent: Mapping[str, str] | None = None,
        live_service_url: str | None = None,
        live_service_access_mode: str = "unspecified",
        live_service_observation_allowed: bool = False,
        recorded_at: str | None = None,
    ) -> "DocumentationIntakeBrief":
        if project_purpose is not None and not isinstance(project_purpose, str):
            raise DocumentationSchemaError(
                "Intake project_purpose must be a string or null."
            )
        purpose = (project_purpose or "").strip() or "unspecified"
        if isinstance(audiences, (str, bytes)):
            raise DocumentationSchemaError(
                "Intake audiences must be an iterable of strings, not one string."
            )
        raw_audiences = tuple(audiences or ())
        if any(not isinstance(value, str) for value in raw_audiences):
            raise DocumentationSchemaError("Intake audiences must contain strings.")
        normalized_audiences = tuple(
            dict.fromkeys(
                value.strip().lower()
                for value in raw_audiences
                if value and value.strip()
            )
        )
        if not normalized_audiences:
            normalized_audiences = ("unspecified",)
        if audience_intent is not None and not isinstance(audience_intent, Mapping):
            raise DocumentationSchemaError("Intake audience_intent must be an object.")
        supplied_intent: dict[str, str] = {}
        for raw_audience, raw_intent in dict(audience_intent or {}).items():
            if not isinstance(raw_audience, str) or not isinstance(raw_intent, str):
                raise DocumentationSchemaError(
                    "Intake audience_intent must map audience strings to strings."
                )
            audience_key = raw_audience.strip().lower()
            if not audience_key:
                raise DocumentationSchemaError(
                    "Intake audience_intent keys must not be empty."
                )
            if audience_key in supplied_intent:
                raise DocumentationSchemaError(
                    "Intake audience_intent keys must remain unique after normalization."
                )
            supplied_intent[audience_key] = raw_intent.strip() or "unspecified"
        unknown_intent = sorted(set(supplied_intent) - set(normalized_audiences))
        if unknown_intent:
            raise DocumentationSchemaError(
                "Intake audience_intent contains an audience that was not selected: "
                f"{unknown_intent[0]}"
            )
        intents = {
            audience: supplied_intent.get(audience, "unspecified")
            for audience in normalized_audiences
        }
        if live_service_url is not None and not isinstance(live_service_url, str):
            raise DocumentationSchemaError(
                "Intake live_service_url must be a string or null."
            )
        if not isinstance(live_service_access_mode, str):
            raise DocumentationSchemaError(
                "Intake live_service_access_mode must be a string."
            )
        if not isinstance(live_service_observation_allowed, bool):
            raise DocumentationSchemaError(
                "Intake live_service_observation_allowed must be a boolean."
            )
        timestamp = _utc_now() if recorded_at is None else recorded_at
        address = (live_service_url or "").strip() or "unspecified"
        value = cls(
            project_purpose=purpose,
            audiences=normalized_audiences,
            audience_intent=intents,
            live_service={
                "address": address,
                "access_mode": live_service_access_mode,
                "observation_allowed": live_service_observation_allowed,
                "secret_material_persisted": False,
            },
            provenance={
                "project_purpose": "answered"
                if purpose != "unspecified"
                else "declined",
                "audiences": "answered"
                if normalized_audiences != ("unspecified",)
                else "declined",
                "live_service": (
                    "declined" if address == "unspecified" else "answered"
                ),
                "source": "supervisor_supplied",
            },
            recorded_at=timestamp,
        )
        return cls.from_dict(value.to_dict())

    def to_dict(self) -> dict[str, Any]:
        return {
            "project_purpose": self.project_purpose,
            "audiences": list(self.audiences),
            "audience_intent": dict(self.audience_intent),
            "live_service": dict(self.live_service),
            "provenance": dict(self.provenance),
            "recorded_at": self.recorded_at,
            "trust_rank": "human_intent",
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "DocumentationIntakeBrief":
        _require_exact_fields(
            payload,
            allowed={
                "project_purpose",
                "audiences",
                "audience_intent",
                "live_service",
                "provenance",
                "recorded_at",
                "trust_rank",
            },
            required={
                "project_purpose",
                "audiences",
                "audience_intent",
                "live_service",
                "provenance",
                "recorded_at",
            },
            label="intake",
        )
        audiences = payload.get("audiences")
        intent = payload.get("audience_intent")
        live_service = payload.get("live_service")
        provenance = payload.get("provenance")
        if not isinstance(audiences, list) or not audiences:
            raise DocumentationSchemaError("Intake audiences must be a non-empty list.")
        if not isinstance(intent, dict):
            raise DocumentationSchemaError("Intake audience_intent must be an object.")
        if not isinstance(live_service, dict) or not isinstance(provenance, dict):
            raise DocumentationSchemaError(
                "Intake live_service and provenance must be objects."
            )
        _require_exact_fields(
            live_service,
            allowed={
                "address",
                "access_mode",
                "observation_allowed",
                "secret_material_persisted",
            },
            required={
                "address",
                "access_mode",
                "observation_allowed",
                "secret_material_persisted",
            },
            label="intake live_service",
        )
        _require_exact_fields(
            provenance,
            allowed={"project_purpose", "audiences", "live_service", "source"},
            required={"project_purpose", "audiences", "live_service", "source"},
            label="intake provenance",
        )
        access_mode = live_service.get("access_mode")
        if access_mode not in {"unspecified", "anonymous", "non-secret"}:
            raise DocumentationSchemaError(
                "Intake live_service access_mode is unsupported."
            )
        if not isinstance(live_service.get("observation_allowed"), bool):
            raise DocumentationSchemaError(
                "Intake live_service observation_allowed must be a boolean."
            )
        if live_service.get("secret_material_persisted") is not False:
            raise DocumentationSchemaError(
                "Intake must record secret_material_persisted=false."
            )
        address = live_service.get("address")
        if (
            not isinstance(address, str)
            or not address.strip()
            or address != address.strip()
        ):
            raise DocumentationSchemaError(
                "Intake live_service address must be a non-empty string."
            )
        if address != "unspecified":
            try:
                parsed_address = urlsplit(address)
            except ValueError as exc:
                raise DocumentationSchemaError(
                    "Intake live_service address is invalid."
                ) from exc
            if (
                parsed_address.scheme not in {"http", "https"}
                or not parsed_address.hostname
                or parsed_address.username is not None
                or parsed_address.password is not None
                or parsed_address.query
                or parsed_address.fragment
            ):
                raise DocumentationSchemaError(
                    "Intake live_service address must be a credential-free HTTP(S) "
                    "origin without query or fragment data."
                )
        if any(
            not isinstance(value, str)
            or not value.strip()
            or value != value.strip().lower()
            for value in audiences
        ):
            raise DocumentationSchemaError(
                "Intake audiences must contain normalized strings."
            )
        normalized_audiences = tuple(audiences)
        if len(normalized_audiences) != len(set(normalized_audiences)):
            raise DocumentationSchemaError("Intake audiences must be unique.")
        if any(
            not isinstance(key, str)
            or not isinstance(value, str)
            or not value.strip()
            or value != value.strip()
            for key, value in intent.items()
        ):
            raise DocumentationSchemaError(
                "Intake audience_intent must map audiences to non-empty strings."
            )
        if set(intent) != set(normalized_audiences):
            raise DocumentationSchemaError(
                "Intake audience_intent keys must match audiences."
            )
        if payload.get("trust_rank", "human_intent") != "human_intent":
            raise DocumentationSchemaError("Intake trust_rank must be human_intent.")
        for key in ("project_purpose", "audiences", "live_service"):
            if provenance.get(key) not in {"answered", "declined"}:
                raise DocumentationSchemaError(
                    f"Intake provenance {key} must be answered or declined."
                )
        if provenance.get("source") != "supervisor_supplied":
            raise DocumentationSchemaError(
                "Intake provenance source must be supervisor_supplied."
            )
        project_purpose = payload.get("project_purpose")
        if (
            not isinstance(project_purpose, str)
            or not project_purpose.strip()
            or project_purpose != project_purpose.strip()
        ):
            raise DocumentationSchemaError(
                "Intake project_purpose must be a non-empty string."
            )
        expected_provenance = {
            "project_purpose": (
                "declined" if project_purpose == "unspecified" else "answered"
            ),
            "audiences": (
                "declined" if normalized_audiences == ("unspecified",) else "answered"
            ),
            "live_service": "declined" if address == "unspecified" else "answered",
        }
        for key, expected in expected_provenance.items():
            if provenance.get(key) != expected:
                raise DocumentationSchemaError(
                    f"Intake provenance {key} does not match its recorded answer."
                )
        recorded_at = payload.get("recorded_at")
        _require_utc_timestamp(recorded_at, "Intake recorded_at")
        if not isinstance(recorded_at, str):  # validation narrows for typing
            raise DocumentationSchemaError(
                "Intake recorded_at must be a UTC timestamp string."
            )
        _assert_no_forbidden_packet_fields(payload, label="intake")
        return cls(
            project_purpose=project_purpose,
            audiences=normalized_audiences,
            audience_intent=dict(intent),
            live_service={
                "address": address,
                "access_mode": access_mode,
                "observation_allowed": live_service["observation_allowed"],
                "secret_material_persisted": False,
            },
            provenance={
                "project_purpose": provenance["project_purpose"],
                "audiences": provenance["audiences"],
                "live_service": provenance["live_service"],
                "source": provenance["source"],
            },
            recorded_at=recorded_at,
        )


@dataclass
class DocumentationRun:
    run_id: str
    state: str
    baseline_strategy: str
    created_at: str
    updated_at: str
    intake: DocumentationIntakeBrief
    source: dict[str, Any]
    baseline: dict[str, Any]
    paths: dict[str, str]
    policy: dict[str, Any]
    publication: dict[str, Any]
    skills: list[dict[str, Any]]
    semantic_budget: int
    adjustment_loop_limit: int
    integrity_anchors: dict[str, str] = field(default_factory=dict)
    evidence: dict[str, str] = field(default_factory=dict)
    work: dict[str, list[str]] = field(
        default_factory=lambda: {
            "reused": [],
            "completed": [],
            "deferred": [],
            "blocked": [],
        }
    )
    validation_results: list[dict[str, Any]] = field(default_factory=list)
    unresolved_findings: list[dict[str, Any]] = field(default_factory=list)
    stage_attempts: dict[str, int] = field(default_factory=dict)
    current_stage: str | None = None
    resume_state: str | None = None
    verdict_limitations: list[str] = field(default_factory=list)
    schema_version: str = DOCUMENTATION_RUN_SCHEMA_VERSION
    integration_mode: str = "external_agent_docs"
    extensions: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        payload = {
            "schema_version": self.schema_version,
            "run_id": self.run_id,
            "state": self.state,
            "integration_mode": self.integration_mode,
            "baseline_strategy": self.baseline_strategy,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "intake": self.intake.to_dict(),
            "source": dict(self.source),
            "baseline": dict(self.baseline),
            "paths": dict(self.paths),
            "policy": dict(self.policy),
            "publication": dict(self.publication),
            "skills": [dict(skill) for skill in self.skills],
            "semantic_budget": self.semantic_budget,
            "adjustment_loop_limit": self.adjustment_loop_limit,
            "evidence": dict(self.evidence),
            "work": {key: list(value) for key, value in self.work.items()},
            "validation_results": [dict(item) for item in self.validation_results],
            "unresolved_findings": [dict(item) for item in self.unresolved_findings],
            "stage_attempts": dict(self.stage_attempts),
            "current_stage": self.current_stage,
            "resume_state": self.resume_state,
            "verdict_limitations": list(self.verdict_limitations),
        }
        if self.integrity_anchors:
            payload["integrity_anchors"] = dict(self.integrity_anchors)
        payload.update(self.extensions)
        return payload

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "DocumentationRun":
        _validate_run_payload(payload)
        known = {
            "schema_version",
            "run_id",
            "state",
            "integration_mode",
            "baseline_strategy",
            "created_at",
            "updated_at",
            "intake",
            "source",
            "baseline",
            "paths",
            "policy",
            "publication",
            "skills",
            "semantic_budget",
            "adjustment_loop_limit",
            "integrity_anchors",
            "evidence",
            "work",
            "validation_results",
            "unresolved_findings",
            "stage_attempts",
            "current_stage",
            "resume_state",
            "verdict_limitations",
        }
        work = payload.get("work", {})
        return cls(
            run_id=str(payload["run_id"]),
            state=str(payload["state"]),
            baseline_strategy=str(payload["baseline_strategy"]),
            created_at=str(payload["created_at"]),
            updated_at=str(payload["updated_at"]),
            intake=DocumentationIntakeBrief.from_dict(payload["intake"]),
            source=dict(payload["source"]),
            baseline=dict(payload["baseline"]),
            paths={str(key): str(value) for key, value in payload["paths"].items()},
            policy=dict(payload["policy"]),
            publication=dict(payload["publication"]),
            skills=[dict(item) for item in payload["skills"]],
            semantic_budget=int(payload["semantic_budget"]),
            adjustment_loop_limit=int(payload["adjustment_loop_limit"]),
            integrity_anchors={
                str(key): str(value)
                for key, value in payload.get("integrity_anchors", {}).items()
            },
            evidence={
                str(key): str(value)
                for key, value in payload.get("evidence", {}).items()
            },
            work={
                key: [str(value) for value in work.get(key, [])]
                for key in ("reused", "completed", "deferred", "blocked")
            },
            validation_results=[
                dict(item) for item in payload.get("validation_results", [])
            ],
            unresolved_findings=[
                dict(item) for item in payload.get("unresolved_findings", [])
            ],
            stage_attempts={
                str(key): int(value)
                for key, value in payload.get("stage_attempts", {}).items()
            },
            current_stage=_optional_text(payload.get("current_stage")),
            resume_state=_optional_text(payload.get("resume_state")),
            verdict_limitations=[
                str(value) for value in payload.get("verdict_limitations", [])
            ],
            schema_version=str(payload["schema_version"]),
            integration_mode=str(payload["integration_mode"]),
            extensions={
                key: value for key, value in payload.items() if key not in known
            },
        )


@dataclass(frozen=True)
class DocumentationRunStatus:
    run_id: str
    state: str
    baseline_strategy: str
    source_available: bool
    freshness: str
    current_stage: str | None
    next_actions: tuple[str, ...]
    limitations: tuple[str, ...]
    healthy: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "state": self.state,
            "baseline_strategy": self.baseline_strategy,
            "source_available": self.source_available,
            "freshness": self.freshness,
            "current_stage": self.current_stage,
            "next_actions": list(self.next_actions),
            "limitations": list(self.limitations),
            "healthy": self.healthy,
            "integration_mode": "external_agent_docs",
        }


@dataclass(frozen=True)
class DocumentationAgentPacket:
    payload: dict[str, Any]

    @property
    def run_id(self) -> str:
        return str(self.payload["run_id"])

    @property
    def stage(self) -> str:
        return str(self.payload["stage"])

    def to_dict(self) -> dict[str, Any]:
        return _json_round_trip(self.payload)

    def to_json(self) -> str:
        return json.dumps(self.payload, indent=2, sort_keys=True) + "\n"

    def to_markdown(self) -> str:
        return _render_packet_markdown(self.payload)


@dataclass(frozen=True)
class DocumentationAgentResult:
    run_id: str
    stage: str
    status: str
    changed_wiki_paths: tuple[str, ...]
    reused_work_ids: tuple[str, ...]
    completed_work_ids: tuple[str, ...]
    deferred_work_ids: tuple[str, ...]
    claims_evidence_pages: tuple[str, ...]
    unresolved_unknowns: tuple[str, ...]
    unsupported_source_notices: tuple[str, ...]
    requested_follow_up_checks: tuple[str, ...]
    reported_source_writes: tuple[str, ...]
    reported_input_wiki_writes: tuple[str, ...]
    reported_generated_block_edits: tuple[str, ...]
    claim_evidence: tuple[dict[str, Any], ...] = ()
    runtime_captures: tuple[dict[str, Any], ...] = ()
    imported_page_edits: tuple[dict[str, Any], ...] = ()
    deferral_rationales: dict[str, str] = field(default_factory=dict)
    findings: tuple[dict[str, Any], ...] = ()
    schema_version: str = DOCUMENTATION_AGENT_RESULT_SCHEMA_VERSION

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "DocumentationAgentResult":
        _require_exact_fields(
            payload,
            allowed=set(_AGENT_RESULT_FIELDS),
            required=set(_REQUIRED_AGENT_RESULT_FIELDS),
            label="agent result",
        )
        if payload.get("schema_version") != DOCUMENTATION_AGENT_RESULT_SCHEMA_VERSION:
            raise DocumentationSchemaError(
                "Unsupported documentation agent-result schema_version."
            )
        run_id = _required_agent_result_text(payload["run_id"], "run_id")
        stage = _required_agent_result_text(payload["stage"], "stage")
        status = _required_agent_result_text(payload["status"], "status")
        if stage not in SUPPORTED_AGENT_STAGES:
            raise DocumentationSchemaError(f"Unsupported agent result stage: {stage!r}")
        if status not in SUPPORTED_AGENT_RESULT_STATUSES:
            raise DocumentationSchemaError(
                f"Unsupported agent result status: {status!r}"
            )
        changed_paths = _portable_path_tuple(payload.get("changed_wiki_paths", []))
        evidence_pages = _portable_path_tuple(payload.get("claims_evidence_pages", []))
        rationales = payload.get("deferral_rationales", {})
        if not isinstance(rationales, Mapping) or any(
            not isinstance(key, str)
            or not key.strip()
            or not isinstance(value, str)
            or not value.strip()
            for key, value in rationales.items()
        ):
            raise DocumentationSchemaError(
                "Agent result deferral_rationales must map work ids to non-empty text."
            )
        findings = _validate_agent_result_findings(payload["findings"], stage=stage)
        imported_page_edits = _validate_imported_page_edits(
            payload.get("imported_page_edits", [])
        )
        try:
            claim_evidence = normalize_claim_evidence_records(
                payload.get("claim_evidence", [])
            )
            runtime_captures = normalize_runtime_capture_records(
                payload.get("runtime_captures", [])
            )
        except DocumentationClaimEvidenceError as exc:
            raise DocumentationSchemaError(str(exc)) from exc
        return cls(
            run_id=run_id,
            stage=stage,
            status=status,
            changed_wiki_paths=changed_paths,
            reused_work_ids=_text_tuple(payload.get("reused_work_ids", [])),
            completed_work_ids=_text_tuple(payload.get("completed_work_ids", [])),
            deferred_work_ids=_text_tuple(payload.get("deferred_work_ids", [])),
            claims_evidence_pages=evidence_pages,
            claim_evidence=claim_evidence,
            runtime_captures=runtime_captures,
            unresolved_unknowns=_text_tuple(payload.get("unresolved_unknowns", [])),
            unsupported_source_notices=_text_tuple(
                payload.get("unsupported_source_notices", [])
            ),
            requested_follow_up_checks=_text_tuple(
                payload.get("requested_follow_up_checks", [])
            ),
            reported_source_writes=_portable_path_tuple(
                payload.get("reported_source_writes", [])
            ),
            reported_input_wiki_writes=_portable_path_tuple(
                payload.get("reported_input_wiki_writes", [])
            ),
            reported_generated_block_edits=_portable_path_tuple(
                payload.get("reported_generated_block_edits", [])
            ),
            imported_page_edits=imported_page_edits,
            deferral_rationales={
                key: value.strip() for key, value in rationales.items()
            },
            findings=findings,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "run_id": self.run_id,
            "stage": self.stage,
            "status": self.status,
            "changed_wiki_paths": list(self.changed_wiki_paths),
            "reused_work_ids": list(self.reused_work_ids),
            "completed_work_ids": list(self.completed_work_ids),
            "deferred_work_ids": list(self.deferred_work_ids),
            "claims_evidence_pages": list(self.claims_evidence_pages),
            "claim_evidence": [dict(item) for item in self.claim_evidence],
            "runtime_captures": [dict(item) for item in self.runtime_captures],
            "unresolved_unknowns": list(self.unresolved_unknowns),
            "unsupported_source_notices": list(self.unsupported_source_notices),
            "requested_follow_up_checks": list(self.requested_follow_up_checks),
            "reported_source_writes": list(self.reported_source_writes),
            "reported_input_wiki_writes": list(self.reported_input_wiki_writes),
            "reported_generated_block_edits": list(self.reported_generated_block_edits),
            "imported_page_edits": [dict(item) for item in self.imported_page_edits],
            "deferral_rationales": dict(sorted(self.deferral_rationales.items())),
            "findings": [dict(item) for item in self.findings],
        }


@dataclass(frozen=True)
class DocumentationVerificationReport:
    run_id: str
    state: str
    ok: bool
    checks: tuple[dict[str, Any], ...]
    limitations: tuple[str, ...]
    next_state: str | None = None
    schema_version: str = DOCUMENTATION_VERIFICATION_SCHEMA_VERSION

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "run_id": self.run_id,
            "state": self.state,
            "ok": self.ok,
            "checks": [dict(check) for check in self.checks],
            "limitations": list(self.limitations),
            "next_state": self.next_state,
        }


@dataclass(frozen=True)
class _RefreshContinuationSnapshot:
    """Safe in-memory handoff from an archived run to a refreshed baseline."""

    prior_run_id: str
    prior_source_revision: str
    prior_source_fingerprint: str | None
    prior_wiki_tree_hash: str
    pages: dict[str, dict[str, Any]]


@dataclass
class _RefreshArchiveTransaction:
    """Tracks an archived run until its replacement is safely committed."""

    workspace_root: Path | None = None
    archive: Path | None = None
    prior_run_id: str | None = None
    phase: str | None = None

    @property
    def active(self) -> bool:
        return self.workspace_root is not None and self.archive is not None


@dataclass(frozen=True)
class _NativeEvidenceTransaction:
    """Captured controller state for refresh plus evidence reconciliation."""

    wiki_root: Path
    artifact_snapshot: dict[str, bytes | None]
    control_snapshot: dict[Path, bytes | None]
    run_state: dict[str, Any]


@dataclass
class _InitialPrepareTransaction:
    """Tracks a pristine workspace root until initial preparation commits."""

    workspace_root: Path | None = None
    root_identity: tuple[int, int, int] | None = None
    preserve_root: bool = False

    @property
    def active(self) -> bool:
        return self.workspace_root is not None and self.root_identity is not None

    def clear(self) -> None:
        self.workspace_root = None
        self.root_identity = None
        self.preserve_root = False


def workspace_paths() -> dict[str, str]:
    return {
        "control": RUN_CONTROL_DIR,
        "run": f"{RUN_CONTROL_DIR}/{RUN_FILENAME}",
        "policy": f"{RUN_CONTROL_DIR}/{POLICY_FILENAME}",
        "stages": f"{RUN_CONTROL_DIR}/stages",
        "packets": f"{RUN_CONTROL_DIR}/packets",
        "results": f"{RUN_CONTROL_DIR}/results",
        "evidence": f"{RUN_CONTROL_DIR}/evidence",
        "skills": f"{RUN_CONTROL_DIR}/skills",
        "wiki": "wiki",
        "site": "site",
        "built_site": "_site",
    }


def _optional_text(value: Any) -> str | None:
    if value in (None, ""):
        return None
    return str(value)


def _next_actions(run: DocumentationRun) -> tuple[str, ...]:
    if run.validation_results:
        latest = run.validation_results[-1]
        if latest.get("status") == "partial" and run.current_stage:
            return (
                f"build another {run.current_stage} packet from recorded state",
                "resolve or defer the recorded unknowns before advancement",
            )
    actions = {
        "prepared": ("complete deterministic baseline",),
        "baseline_ready": ("build wiki-enrichment packet",),
        "wiki_enrichment": ("record wiki-enrichment result",),
        "user_docs": ("record user-docs result",),
        "review": ("record independent review result", "verify and export"),
        "publish_ready": ("use the recorded local deployment handoff",),
        "blocked": ("resolve recorded blocking findings", "resume recorded stage"),
    }
    return actions[run.state]


def _state_to_stage(state: str) -> str | None:
    return {
        "wiki_enrichment": "wiki-enrichment",
        "user_docs": "user-docs",
        "review": "review",
    }.get(state)


def _json_round_trip(payload: Mapping[str, Any]) -> dict[str, Any]:
    return json.loads(json.dumps(payload))


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _new_run_id() -> str:
    return str(uuid.uuid4())


def _sha256_json(payload: Mapping[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()

__all__ = (
    'RUN_CONTROL_DIR',
    'RUN_FILENAME',
    'POLICY_FILENAME',
    'REFRESH_TRANSACTION_FILENAME',
    '_INITIAL_PREPARE_OWNED_ROOTS',
    'SUPPORTED_RUN_STATES',
    'SUPPORTED_BASELINE_STRATEGIES',
    'SUPPORTED_AGENT_STAGES',
    'SUPPORTED_AGENT_RESULT_STATUSES',
    '_AGENT_RESULT_FIELDS',
    '_REQUIRED_AGENT_RESULT_FIELDS',
    '_IMPORTED_PAGE_EDIT_FIELDS',
    '_AGENT_FINDING_FIELDS',
    '_AGENT_FINDING_STATUSES',
    '_TERMINAL_AGENT_FINDING_STATUSES',
    '_AGENT_FINDING_SEVERITIES',
    'SUPPORTED_FRESHNESS_POLICIES',
    'SUPPORTED_DOCUMENTATION_KNOWLEDGE_MODES',
    'DEFAULT_DOCUMENTATION_SKILLS',
    '_GENERATED_MARKER',
    '_DO_NOT_EDIT_MARKER',
    '_NATIVE_ARTIFACT_PATHS',
    '_NATIVE_REFRESH_MUTABLE_PATHS',
    '_MAX_BUILDER_LOG_BYTES',
    '_PACKET_FORBIDDEN_FIELDS',
    '_PACKET_FORBIDDEN_KEY_SUFFIXES',
    '_CONTROL_SNAPSHOT_EVIDENCE_KEYS',
    '_ALLOWED_TRANSITIONS',
    'DocumentationRunError',
    'DocumentationSchemaError',
    'DocumentationTransitionError',
    'DocumentationIntegrityError',
    'DocumentationPersistedStateError',
    'DocumentationIntakeBrief',
    'DocumentationRun',
    'DocumentationRunStatus',
    'DocumentationAgentPacket',
    'DocumentationAgentResult',
    'DocumentationVerificationReport',
    '_RefreshContinuationSnapshot',
    '_RefreshArchiveTransaction',
    '_NativeEvidenceTransaction',
    '_InitialPrepareTransaction',
    'workspace_paths',
    '_optional_text',
    '_next_actions',
    '_state_to_stage',
    '_json_round_trip',
    '_utc_now',
    '_new_run_id',
    '_sha256_json',
)
