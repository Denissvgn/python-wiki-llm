"""Deterministic, inspection-only planning for qualified-context experiments.

This module treats oracle commands as inert manifest data.  It validates and
compares already materialized packets, or asks the read-only packet builder to
materialize them, but it has no task runner, provider adapter, repository
mutation, or capability probe.
"""

from __future__ import annotations

import hashlib
import json
import math
import re
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from types import MappingProxyType
from typing import Any

from llm_wiki_cli.services.contracts import (
    EVAL_LITE_PLAN_SCHEMA_VERSION,
    EVAL_LITE_TASK_SCHEMA_VERSION,
)
from llm_wiki_cli.services.validation import (
    portable_path_key,
    require_portable_relative_path,
)


_TASK_ID_DOMAIN = b"llm-wiki-eval-lite-task/v1\x00"
_PLAN_DIGEST_DOMAIN = b"llm-wiki-eval-lite-plan/v1\x00"
_VALUE_DIGEST_DOMAIN = b"llm-wiki-eval-lite-value/v1\x00"
_CONTENT_ADDRESS_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
_CAPABILITY_RE = re.compile(r"^[a-z][a-z0-9]*(?:-[a-z0-9]+)*$")
_MAX_TEXT_LENGTH = 1_048_576
_MAX_COLLECTION_ITEMS = 10_000
_MISSING = object()
_TASK_FIELDS = frozenset(
    {
        "schema_version",
        "base_revision",
        "prompt",
        "allowed_surface",
        "oracle",
        "environment",
        "limitations",
    }
)
_ORACLE_FIELDS = frozenset({"command", "timeout_seconds"})
_CONTEXT_REQUEST_PREFIXES = (
    ("request", "filters"),
    ("request", "focus"),
    ("request", "prefer_fresh"),
)
_DERIVED_CONTEXT_PREFIXES = (
    ("packet_id",),
    ("response",),
    ("delivery",),
    ("path_policy",),
)


class EvaluationPlanError(ValueError):
    """A task manifest, packet input, or capability declaration is invalid."""

    def __init__(self, field: str, message: str):
        self.field = field
        self.message = message
        super().__init__(f"{field}: {message}")


@dataclass(frozen=True)
class EvaluationPlan:
    """An immutable canonical inspection plan."""

    _canonical_bytes: bytes
    _payload: Mapping[str, Any]

    @property
    def plan_digest(self) -> str:
        return str(self._payload["plan_digest"])

    @property
    def disposition(self) -> str:
        return str(self._payload["disposition"])

    def to_bytes(self) -> bytes:
        """Return canonical sorted-key UTF-8 JSON ending in one LF."""

        return self._canonical_bytes

    def to_payload(self) -> dict[str, Any]:
        """Return a detached JSON-compatible plan value."""

        return _thaw_json(self._payload)


def normalize_task_manifest(manifest: Mapping[str, Any]) -> dict[str, Any]:
    """Validate and canonicalize the explicit task-first manifest."""

    if not isinstance(manifest, Mapping):
        raise EvaluationPlanError("manifest", "must be an object")
    data = dict(manifest)
    _require_exact_fields(data, _TASK_FIELDS, "manifest")
    if data["schema_version"] != EVAL_LITE_TASK_SCHEMA_VERSION:
        raise EvaluationPlanError(
            "manifest.schema_version",
            f"must be {EVAL_LITE_TASK_SCHEMA_VERSION!r}",
        )
    base_revision = _require_text(
        data["base_revision"],
        "manifest.base_revision",
    )
    if _CONTENT_ADDRESS_RE.fullmatch(base_revision) is None:
        raise EvaluationPlanError(
            "manifest.base_revision",
            "must be a content-addressed sha256:<64 lowercase hex> value",
        )
    prompt = _require_text(data["prompt"], "manifest.prompt")

    allowed_raw = _require_sequence(
        data["allowed_surface"],
        "manifest.allowed_surface",
        allow_empty=False,
    )
    allowed_surface: list[str] = []
    collision_seen: dict[str, str] = {}
    for index, value in enumerate(allowed_raw):
        field = f"manifest.allowed_surface[{index}]"
        text = _require_text(value, field)
        try:
            error = EvaluationPlanError(
                field,
                "must be a canonical portable repository-relative path",
            )
            normalized = require_portable_relative_path(
                text,
                text_error=error,
                relative_error=error,
                escape_error=error,
                traversal_error=error,
                separator_error=error,
                utf8_error=error,
                control_error=error,
                non_nfc_error=error,
                nonportable_error=error,
                reserved_error=error,
                collision_seen=collision_seen,
                collision_error=lambda previous, current: EvaluationPlanError(
                    field,
                    "collides across supported filesystems with "
                    f"{previous!r}: {current!r}",
                ),
            )
        except (TypeError, ValueError) as exc:
            raise EvaluationPlanError(field, str(exc)) from exc
        allowed_surface.append(normalized)
    if len(set(allowed_surface)) != len(allowed_surface):
        raise EvaluationPlanError(
            "manifest.allowed_surface",
            "must not contain duplicate repository-relative paths",
        )
    ordered_surface = sorted(allowed_surface, key=portable_path_key)
    for parent, child in zip(ordered_surface, ordered_surface[1:]):
        if portable_path_key(child).startswith(
            portable_path_key(parent) + "/"
        ):
            raise EvaluationPlanError(
                "manifest.allowed_surface",
                f"contains ambiguous parent/child entries {parent!r} and {child!r}",
            )

    oracle = _normalize_oracle(data["oracle"])
    environment = _normalize_environment(data["environment"])
    limitations_raw = _require_sequence(
        data["limitations"],
        "manifest.limitations",
        allow_empty=True,
    )
    limitations = [
        _require_text(value, f"manifest.limitations[{index}]")
        for index, value in enumerate(limitations_raw)
    ]
    if len(set(limitations)) != len(limitations):
        raise EvaluationPlanError(
            "manifest.limitations",
            "must not contain duplicate declarations",
        )

    return {
        "schema_version": EVAL_LITE_TASK_SCHEMA_VERSION,
        "base_revision": base_revision,
        "prompt": prompt,
        "allowed_surface": sorted(allowed_surface),
        "oracle": oracle,
        "environment": environment,
        "limitations": sorted(limitations),
    }


def build_evaluation_plan(
    manifest: Mapping[str, Any],
    baseline_packet: bytes | bytearray | memoryview | Any,
    treatment_packet: bytes | bytearray | memoryview | Any,
    *,
    available_capabilities: Iterable[str] = (),
    baseline_reconciliation: Any | None = None,
    treatment_reconciliation: Any | None = None,
) -> EvaluationPlan:
    """Build a deterministic exploratory plan without executing either arm."""

    normalized_manifest = normalize_task_manifest(manifest)
    baseline = _validated_packet(baseline_packet, "baseline_packet")
    treatment = _validated_packet(treatment_packet, "treatment_packet")
    capabilities = _normalize_capabilities(available_capabilities)
    source_binding = _source_binding_report(
        normalized_manifest["base_revision"],
        baseline,
        treatment,
    )
    evidence = _evidence_report(
        baseline,
        treatment,
        baseline_reconciliation,
        treatment_reconciliation,
    )

    differences = _packet_differences(baseline["payload"], treatment["payload"])
    confounds = [
        difference
        for difference in differences
        if difference["classification"] == "non-context-confound"
    ]
    required_capabilities = normalized_manifest["environment"][
        "required_capabilities"
    ]
    missing_capabilities = sorted(set(required_capabilities) - set(capabilities))
    capability_report = {
        "basis": "caller-declared-not-live-probed",
        "required": required_capabilities,
        "declared_available": capabilities,
        "missing": missing_capabilities,
        "current": None,
    }

    invalid_reasons: list[str] = []
    if not source_binding["matches"]:
        invalid_reasons.append("task-base-mismatch")
    if confounds:
        invalid_reasons.append("non-context-arm-difference")
    if evidence["state"] == "stale":
        invalid_reasons.append("stale-context-evidence")

    conditional_reasons: list[str] = []
    if evidence["state"] != "current":
        conditional_reasons.append("evidence-currentness-unevaluated")
    if missing_capabilities:
        conditional_reasons.append("execution-capabilities-unavailable")

    if invalid_reasons:
        disposition = "design-invalid"
        reason_codes = invalid_reasons
    elif conditional_reasons:
        disposition = "conditionally-runnable"
        reason_codes = conditional_reasons
    else:
        disposition = "design-valid"
        reason_codes = ["one-variable-parity-satisfied"]

    task_bytes = _canonical_json_bytes(normalized_manifest)
    task_id = _domain_digest(_TASK_ID_DOMAIN, task_bytes)
    operation_manifest = {
        "mode": "inspection-only",
        "exploratory": True,
        "task_id": task_id,
        "base_revision": normalized_manifest["base_revision"],
        "allowed_surface": normalized_manifest["allowed_surface"],
        "oracle": {
            **normalized_manifest["oracle"],
            "handling": "inert-data-not-executed",
        },
        "environment": {
            "digest": _domain_digest(
                _VALUE_DIGEST_DOMAIN,
                _canonical_json_bytes(normalized_manifest["environment"]),
            ),
            "declared_fields": sorted(normalized_manifest["environment"]),
        },
        "steps": [
            "validate-explicit-task-manifest",
            "validate-baseline-qualified-context-packet",
            "validate-treatment-qualified-context-packet",
            "compare-exact-arm-differences",
            "classify-non-context-confounds",
            "report-declared-capability-conditions",
        ],
        "prohibited_operations": [
            "task-execution",
            "provider-call",
            "repository-write",
            "plugin-load",
        ],
    }
    plan_body = {
        "schema_version": EVAL_LITE_PLAN_SCHEMA_VERSION,
        "label": "exploratory",
        "exploratory": True,
        "task": {
            "task_id": task_id,
            "manifest_digest": _domain_digest(_TASK_ID_DOMAIN, task_bytes),
            "limitation_receipt": {
                "count": len(normalized_manifest["limitations"]),
                "digest": _domain_digest(
                    _VALUE_DIGEST_DOMAIN,
                    _canonical_json_bytes(normalized_manifest["limitations"]),
                ),
            },
        },
        "source_binding": source_binding,
        "arms": {
            "baseline": _arm_receipt(baseline),
            "treatment": _arm_receipt(treatment),
        },
        "evidence": evidence,
        "arm_differences": differences,
        "confound_report": {
            "state": "different" if confounds else "matched",
            "count": len(confounds),
            "findings": confounds,
            "categories": _confound_categories(
                differences,
                normalized_manifest,
                source_binding,
                evidence,
                capability_report,
            ),
        },
        "capabilities": capability_report,
        "operation_manifest": operation_manifest,
        "disposition": disposition,
        "reason_codes": reason_codes,
        "limitations": sorted(
            {
                "inspection-does-not-execute-or-prove-task-outcomes",
                "one-variable-parity-is-not-a-general-causal-claim",
                "caller-capability-declarations-are-not-live-proof",
                *(
                    {"task-declared-limitations-present"}
                    if normalized_manifest["limitations"]
                    else set()
                ),
            }
        ),
        "distribution": {
            "classification": "private-inspection-plan",
            "shareable": False,
            "reason": "no-shareable-projection-policy-applied",
        },
    }
    plan_digest = _domain_digest(
        _PLAN_DIGEST_DOMAIN,
        _canonical_json_bytes(plan_body),
    )
    payload = {**plan_body, "plan_digest": plan_digest}
    canonical = _canonical_json_bytes(payload) + b"\n"
    return EvaluationPlan(canonical, _freeze_json(payload))


def materialize_evaluation_plan(
    manifest: Mapping[str, Any],
    *,
    src_dir: str,
    wiki_dir: str,
    baseline_request: Mapping[str, Any],
    treatment_request: Mapping[str, Any],
    available_capabilities: Iterable[str] = (),
) -> EvaluationPlan:
    """Materialize both packets through the read-only QCP builder, then plan."""

    from llm_wiki_cli.services.context_packet import (
        build_qualified_context,
        reconcile_context_packet,
    )

    normalized_manifest = normalize_task_manifest(manifest)
    baseline = build_qualified_context(
        src_dir,
        wiki_dir,
        baseline_request,
        read_only=True,
    )
    treatment = build_qualified_context(
        src_dir,
        wiki_dir,
        treatment_request,
        read_only=True,
    )
    baseline_live = reconcile_context_packet(
        baseline.to_bytes(),
        src_dir,
        wiki_dir,
        read_only=True,
    )
    treatment_live = reconcile_context_packet(
        treatment.to_bytes(),
        src_dir,
        wiki_dir,
        read_only=True,
    )
    return build_evaluation_plan(
        normalized_manifest,
        baseline,
        treatment,
        available_capabilities=available_capabilities,
        baseline_reconciliation=baseline_live,
        treatment_reconciliation=treatment_live,
    )


def _normalize_oracle(value: Any) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise EvaluationPlanError("manifest.oracle", "must be an object")
    oracle = dict(value)
    _require_exact_fields(oracle, _ORACLE_FIELDS, "manifest.oracle")
    command_raw = _require_sequence(
        oracle["command"],
        "manifest.oracle.command",
        allow_empty=False,
    )
    command = [
        _require_text(item, f"manifest.oracle.command[{index}]")
        for index, item in enumerate(command_raw)
    ]
    timeout = oracle["timeout_seconds"]
    if isinstance(timeout, bool) or not isinstance(timeout, int) or timeout < 1:
        raise EvaluationPlanError(
            "manifest.oracle.timeout_seconds",
            "must be a positive integer",
        )
    return {"command": command, "timeout_seconds": timeout}


def _normalize_environment(value: Any) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise EvaluationPlanError("manifest.environment", "must be an object")
    environment = dict(value)
    for required_field, reason in (
        ("model", "the model input is explicit"),
        ("budget", "the execution budget is explicit"),
        ("toolchain", "the execution environment is explicit"),
        (
            "required_capabilities",
            "unavailable execution capabilities are explicit",
        ),
    ):
        if required_field not in environment:
            raise EvaluationPlanError(
                f"manifest.environment.{required_field}",
                f"is required so {reason}",
            )
    _validate_json_tree(environment, "manifest.environment")
    toolchain_raw = _require_sequence(
        environment["toolchain"],
        "manifest.environment.toolchain",
        allow_empty=False,
    )
    toolchain = [
        _require_text(item, f"manifest.environment.toolchain[{index}]")
        for index, item in enumerate(toolchain_raw)
    ]
    required = _normalize_capabilities(
        environment["required_capabilities"],
        field="manifest.environment.required_capabilities",
    )
    model = _require_text(
        environment["model"],
        "manifest.environment.model",
    )
    if not isinstance(environment["budget"], Mapping) or not environment["budget"]:
        raise EvaluationPlanError(
            "manifest.environment.budget",
            "must be a non-empty object",
        )
    normalized = _json_copy(environment)
    normalized["model"] = model
    normalized["toolchain"] = sorted(set(toolchain))
    normalized["required_capabilities"] = required
    return normalized


def _validated_packet(value: Any, field: str) -> dict[str, Any]:
    from llm_wiki_cli.services.context_packet import (
        ContextPacketError,
        QualifiedContextPacket,
        validate_context_packet,
    )

    if isinstance(value, QualifiedContextPacket):
        raw = value.to_bytes()
    elif isinstance(value, (bytes, bytearray, memoryview)):
        raw = bytes(value)
    else:
        raise EvaluationPlanError(
            field,
            "must be canonical packet bytes or a QualifiedContextPacket",
        )
    try:
        validation = validate_context_packet(raw)
    except ContextPacketError as exc:
        raise EvaluationPlanError(field, str(exc)) from exc
    payload = validation.packet.to_payload()
    return {
        "packet_id": validation.packet_id,
        "bytes": raw,
        "payload": payload,
        "validation": validation.to_payload(),
    }


def _source_binding_report(
    expected: str,
    baseline: Mapping[str, Any],
    treatment: Mapping[str, Any],
) -> dict[str, Any]:
    arms: dict[str, Any] = {}
    for name, packet in (
        ("baseline", baseline),
        ("treatment", treatment),
    ):
        identity = packet["payload"]["basis"]["source_snapshot"]["identity"]
        arms[name] = {
            "source_snapshot_identity": identity,
            "matches_expected": identity == expected,
        }
    return {
        "expected_source_snapshot_identity": expected,
        "matches": all(arm["matches_expected"] for arm in arms.values()),
        "arms": arms,
    }


def _evidence_report(
    baseline: Mapping[str, Any],
    treatment: Mapping[str, Any],
    baseline_reconciliation: Any | None,
    treatment_reconciliation: Any | None,
) -> dict[str, Any]:
    arms = {
        "baseline": _reconciliation_receipt(
            baseline_reconciliation,
            baseline["packet_id"],
            "baseline_reconciliation",
        ),
        "treatment": _reconciliation_receipt(
            treatment_reconciliation,
            treatment["packet_id"],
            "treatment_reconciliation",
        ),
    }
    current_values = [arm["current"] for arm in arms.values()]
    if any(value is False for value in current_values):
        state = "stale"
        current: bool | None = False
    elif all(value is True for value in current_values):
        state = "current"
        current = True
    else:
        state = "unevaluated"
        current = None
    return {
        "state": state,
        "current": current,
        "arms": arms,
        "limitations": (
            []
            if state == "current"
            else ["live-basis-currentness-not-established"]
        ),
    }


def _reconciliation_receipt(
    value: Any | None,
    packet_id: str,
    field: str,
) -> dict[str, Any]:
    if value is None:
        return {
            "packet_id": packet_id,
            "state": "unevaluated",
            "current": None,
            "basis": "not-provided",
            "limitations": ["live-reconciliation-not-performed"],
        }
    from llm_wiki_cli.services import context_packet

    if type(value) is not context_packet.ContextPacketReconciliation:
        raise EvaluationPlanError(
            field,
            "must be an official ContextPacketReconciliation returned by "
            "reconcile_context_packet, or None",
        )
    try:
        context_packet._validate_reconciliation_contract(
            packet_id=value.packet_id,
            policy=value.policy,
            state=value.state,
            current=value.current,
            facets=value.facets,
            limitations=value.limitations,
        )
    except ValueError as exc:
        raise EvaluationPlanError(field, str(exc)) from exc
    payload = value.to_payload()
    if payload.get("packet_id") != packet_id:
        raise EvaluationPlanError(
            f"{field}.packet_id",
            "must match the corresponding staged packet",
        )
    state = payload.get("state")
    current = payload.get("current")
    if state not in {"current", "stale", "unevaluated"}:
        raise EvaluationPlanError(
            f"{field}.state",
            "must be current, stale, or unevaluated",
        )
    if current is not True and current is not False and current is not None:
        raise EvaluationPlanError(
            f"{field}.current",
            "must be true, false, or null",
        )
    if (
        (state == "current" and current is not True)
        or (state == "stale" and current is not False)
        or (state == "unevaluated" and current is not None)
    ):
        raise EvaluationPlanError(
            f"{field}.current",
            "must agree with the reconciliation state",
        )
    limitations = payload.get("limitations", [])
    if not isinstance(limitations, list) or any(
        not isinstance(item, str) for item in limitations
    ):
        raise EvaluationPlanError(
            f"{field}.limitations",
            "must be an array of strings",
        )
    return {
        "packet_id": packet_id,
        "state": state,
        "current": current,
        "basis": "official-live-reconciliation",
        "policy": payload.get("policy"),
        "limitations": sorted(limitations),
    }


def _arm_receipt(packet: Mapping[str, Any]) -> dict[str, Any]:
    raw = packet["bytes"]
    payload = packet["payload"]
    return {
        "packet_id": packet["packet_id"],
        "packet_digest": _domain_digest(_VALUE_DIGEST_DOMAIN, raw),
        "byte_length": len(raw),
        "request_digest": _domain_digest(
            _VALUE_DIGEST_DOMAIN,
            _canonical_json_bytes(payload["request"]),
        ),
        "context_response_digest": _domain_digest(
            _VALUE_DIGEST_DOMAIN,
            _canonical_json_bytes(payload["response"]),
        ),
        "structural_validation": packet["validation"],
    }


def _packet_differences(
    baseline: Mapping[str, Any],
    treatment: Mapping[str, Any],
) -> list[dict[str, Any]]:
    raw: list[tuple[tuple[str, ...], Any, Any]] = []
    _walk_differences(baseline, treatment, (), raw)
    differences: list[dict[str, Any]] = []
    for path, left, right in raw:
        classification, category = _classify_difference(path)
        differences.append(
            {
                "path": _json_pointer(path),
                "classification": classification,
                "category": category,
                "baseline": _value_receipt(left),
                "treatment": _value_receipt(right),
            }
        )
    return differences


def _walk_differences(
    left: Any,
    right: Any,
    path: tuple[str, ...],
    output: list[tuple[tuple[str, ...], Any, Any]],
) -> None:
    if isinstance(left, Mapping) and isinstance(right, Mapping):
        for key in sorted(set(left) | set(right)):
            _walk_differences(
                left.get(key, _MISSING),
                right.get(key, _MISSING),
                (*path, str(key)),
                output,
            )
        return
    if (
        isinstance(left, list)
        and isinstance(right, list)
        and left is not _MISSING
        and right is not _MISSING
    ):
        for index in range(max(len(left), len(right))):
            _walk_differences(
                left[index] if index < len(left) else _MISSING,
                right[index] if index < len(right) else _MISSING,
                (*path, str(index)),
                output,
            )
        return
    if left is _MISSING or right is _MISSING or left != right:
        output.append((path, left, right))


def _classify_difference(path: tuple[str, ...]) -> tuple[str, str]:
    if any(path[: len(prefix)] == prefix for prefix in _CONTEXT_REQUEST_PREFIXES):
        return "intended-context", "context-request"
    if any(path[: len(prefix)] == prefix for prefix in _DERIVED_CONTEXT_PREFIXES):
        return "derived-context", "context-materialization"
    if path[:2] == ("request", "budget_tokens"):
        return "non-context-confound", "budget"
    if path[:2] in {("request", "format"), ("request", "protocol")}:
        return "non-context-confound", "tool"
    if path[:2] in {
        ("basis", "source_snapshot"),
        ("basis", "repository"),
        ("basis", "knowledge"),
    }:
        return "non-context-confound", "source"
    if path[:2] == ("basis", "generator"):
        return "non-context-confound", "tool"
    if path[:2] == ("basis", "freshness"):
        return "non-context-confound", "freshness"
    if path[:1] == ("assurance",):
        return "non-context-confound", "assurance"
    return "non-context-confound", "other"


def _confound_categories(
    differences: Sequence[Mapping[str, Any]],
    manifest: Mapping[str, Any],
    source_binding: Mapping[str, Any],
    evidence: Mapping[str, Any],
    capabilities: Mapping[str, Any],
) -> list[dict[str, Any]]:
    categories = (
        "model",
        "prompt",
        "source",
        "tool",
        "budget",
        "oracle",
        "freshness",
        "path-policy",
        "limitation",
        "capability",
        "assurance",
        "other",
    )
    found = {
        str(item["category"])
        for item in differences
        if item["classification"] == "non-context-confound"
    }
    states: dict[str, str] = {
        "model": "shared-by-construction",
        "prompt": "shared-by-construction",
        "source": (
            "different"
            if "source" in found or not source_binding["matches"]
            else "matched"
        ),
        "tool": "different" if "tool" in found else "matched",
        "budget": "different" if "budget" in found else "matched",
        "oracle": "shared-by-construction",
        "freshness": (
            "different"
            if "freshness" in found
            else str(evidence["state"])
        ),
        "path-policy": (
            "context-derived"
            if any(
                str(item["path"]).startswith("/path_policy/")
                for item in differences
            )
            else "matched"
        ),
        "limitation": (
            "shared-by-construction"
            if manifest["limitations"]
            else "declared-empty"
        ),
        "capability": (
            "missing"
            if capabilities["missing"]
            else "caller-declared-not-live-probed"
        ),
        "assurance": "different" if "assurance" in found else "matched",
        "other": "different" if "other" in found else "matched",
    }
    return [
        {"category": category, "state": states[category]}
        for category in categories
    ]


def _value_receipt(value: Any) -> dict[str, Any]:
    if value is _MISSING:
        return {"present": False}
    encoded = _canonical_json_bytes(value)
    receipt: dict[str, Any] = {
        "present": True,
        "type": _json_type(value),
        "canonical_digest": _domain_digest(_VALUE_DIGEST_DOMAIN, encoded),
        "canonical_bytes": len(encoded),
    }
    return receipt


def _normalize_capabilities(
    values: Iterable[str],
    *,
    field: str = "available_capabilities",
) -> list[str]:
    if isinstance(values, (str, bytes, bytearray, memoryview, Mapping)):
        raise EvaluationPlanError(field, "must be an iterable of strings")
    try:
        raw = list(values)
    except TypeError as exc:
        raise EvaluationPlanError(
            field,
            "must be an iterable of strings",
        ) from exc
    if len(raw) > _MAX_COLLECTION_ITEMS:
        raise EvaluationPlanError(
            field,
            f"must not exceed {_MAX_COLLECTION_ITEMS} items",
        )
    capabilities: list[str] = []
    for index, value in enumerate(raw):
        item_field = f"{field}[{index}]"
        text = _require_text(value, item_field)
        if _CAPABILITY_RE.fullmatch(text) is None:
            raise EvaluationPlanError(
                item_field,
                "must be a lowercase hyphenated capability identifier",
            )
        capabilities.append(text)
    if len(set(capabilities)) != len(capabilities):
        raise EvaluationPlanError(field, "must not contain duplicates")
    return sorted(capabilities)


def _require_exact_fields(
    value: Mapping[str, Any],
    expected: frozenset[str],
    field: str,
) -> None:
    missing = sorted(expected - set(value))
    if missing:
        raise EvaluationPlanError(f"{field}.{missing[0]}", "is required")
    unknown = sorted(set(value) - expected)
    if unknown:
        raise EvaluationPlanError(f"{field}.{unknown[0]}", "is not supported")


def _require_text(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise EvaluationPlanError(field, "must be a non-empty string")
    if len(value) > _MAX_TEXT_LENGTH:
        raise EvaluationPlanError(
            field,
            f"must not exceed {_MAX_TEXT_LENGTH} characters",
        )
    return value


def _require_sequence(
    value: Any,
    field: str,
    *,
    allow_empty: bool,
) -> list[Any]:
    if isinstance(value, (str, bytes, bytearray, memoryview, Mapping)):
        raise EvaluationPlanError(field, "must be an array")
    if not isinstance(value, Sequence):
        raise EvaluationPlanError(field, "must be an array")
    result = list(value)
    if not allow_empty and not result:
        raise EvaluationPlanError(field, "must not be empty")
    if len(result) > _MAX_COLLECTION_ITEMS:
        raise EvaluationPlanError(
            field,
            f"must not exceed {_MAX_COLLECTION_ITEMS} items",
        )
    return result


def _validate_json_tree(value: Any, field: str, *, depth: int = 0) -> None:
    if depth > 64:
        raise EvaluationPlanError(field, "exceeds the maximum nesting depth")
    if value is None or isinstance(value, (bool, int, str)):
        if isinstance(value, str) and len(value) > _MAX_TEXT_LENGTH:
            raise EvaluationPlanError(
                field,
                f"must not exceed {_MAX_TEXT_LENGTH} characters",
            )
        return
    if isinstance(value, float):
        if not math.isfinite(value):
            raise EvaluationPlanError(field, "must not contain NaN or infinity")
        return
    if isinstance(value, Mapping):
        if len(value) > _MAX_COLLECTION_ITEMS:
            raise EvaluationPlanError(field, "contains too many object fields")
        for key, child in value.items():
            if not isinstance(key, str):
                raise EvaluationPlanError(field, "object keys must be strings")
            _validate_json_tree(child, f"{field}.{key}", depth=depth + 1)
        return
    if isinstance(value, Sequence) and not isinstance(
        value,
        (str, bytes, bytearray, memoryview),
    ):
        if len(value) > _MAX_COLLECTION_ITEMS:
            raise EvaluationPlanError(field, "contains too many array items")
        for index, child in enumerate(value):
            _validate_json_tree(child, f"{field}[{index}]", depth=depth + 1)
        return
    raise EvaluationPlanError(field, f"contains unsupported value {type(value).__name__}")


def _canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
        allow_nan=False,
    ).encode("utf-8")


def _domain_digest(domain: bytes, value: bytes) -> str:
    return "sha256:" + hashlib.sha256(domain + value).hexdigest()


def _json_copy(value: Any) -> Any:
    return json.loads(_canonical_json_bytes(value).decode("utf-8"))


def _json_type(value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, (int, float)):
        return "number"
    if isinstance(value, str):
        return "string"
    if isinstance(value, list):
        return "array"
    return "object"


def _json_pointer(path: Sequence[str]) -> str:
    if not path:
        return ""
    return "/" + "/".join(
        part.replace("~", "~0").replace("/", "~1") for part in path
    )


def _freeze_json(value: Any) -> Any:
    if isinstance(value, Mapping):
        return MappingProxyType(
            {str(key): _freeze_json(child) for key, child in value.items()}
        )
    if isinstance(value, list):
        return tuple(_freeze_json(child) for child in value)
    return value


def _thaw_json(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(key): _thaw_json(child) for key, child in value.items()}
    if isinstance(value, tuple):
        return [_thaw_json(child) for child in value]
    return value
