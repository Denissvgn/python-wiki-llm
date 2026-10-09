"""Pure AF16 body-size scoring over externally pinned physical captures.

No source selection, provider execution, fixture substitution, or adoption takes
place here. Text estimates are not model tokens, money, or workflow savings.
"""
from __future__ import annotations

from collections.abc import Mapping
from dataclasses import asdict, dataclass, fields
import hashlib
import json
from typing import Any, Protocol

ESTIMATOR_ID = "utf8-ceil-div4/v1"
PRIMARY_CASE = "tiny-matched-primary"
MAX_BODY_TOKENS = 1000
REQUIRED_CONTROLS = (
    "canonical_validation", "full_projection_expansion", "decisive_facts",
    "gaps", "identities", "citations", "qualifications", "receiving_custody",
    "session_controls", "adapter_controls", "source_controls", "accounting",
    "context_facts",
)


REQUIRED_BINDINGS = (
    "source_id", "case_id", "request_sha256", "view_options_sha256",
    "canonical_sha256", "profile_sha256", "policy_sha256", "counter_identity",
    "counter_exact", "frame_identity", "input_sha256", "provider_id",
    "receipt_provider_id", "candidate_id", "budget_tokens", "canonical_ceiling_tokens",
)
REQUIRED_CAPTURE_CHECKS = (
    "physical_capture_pin", *(f"binding_{name}" for name in REQUIRED_BINDINGS),
    "canonical_text_pin", "canonical_accounting", "view_accounting",
    "canonical_body_in_wire", "compact_body_in_wire", "canonical_success",
    "view_status", "receipt_pin", "receipt_binding", "truthful_budget_diagnostic",
)
REQUIRED_MINIMUM_CHECKS = ("minimum_success_pin", "minimum_success_accounting")


class Counter(Protocol):
    identity: str
    exact: bool

    def count(self, text: str) -> int: ...


def text_sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def record_sha256(value: Any) -> str:
    """Hash a physical capture's entire normalized JSON representation."""
    return text_sha256(json.dumps(value, sort_keys=True, separators=(",", ":"),
                                  ensure_ascii=False, allow_nan=False))


@dataclass(frozen=True)
class MetricBindings:
    """Controller pins authored independently of the observations being scored."""

    source_id: str
    case_id: str
    request_sha256: str
    view_options_sha256: str
    canonical_sha256: str
    profile_sha256: str
    policy_sha256: str
    counter_identity: str
    counter_exact: bool
    frame_identity: str
    input_sha256: str
    provider_id: str
    receipt_provider_id: str
    candidate_id: str
    record_sha256: str
    receipt_sha256: str
    budget_tokens: int
    canonical_ceiling_tokens: int
    candidate_ids: tuple[str, ...]
    minimum_success_sha256: str | None = None


@dataclass(frozen=True)
class TextMeasurement:
    bytes: int
    estimated_tokens: int
    sha256: str
    counter_identity: str = ESTIMATOR_ID
    exact: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class Measurement:
    binding: MetricBindings
    status: str
    canonical_body: TextMeasurement
    compact_body: TextMeasurement
    canonical_wire: TextMeasurement
    compact_wire: TextMeasurement
    receipt_followup: tuple[TextMeasurement, ...]
    minimum_success: TextMeasurement | None
    checks: Mapping[str, bool]
    wall_ns: int | None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class GateDecision:
    eligible: bool
    body_size_win: bool
    checks: Mapping[str, bool]
    reasons: tuple[str, ...]
    cases_count: int = 1
    successful_cases: int = 0
    implementation_adopted: bool = False
    default_adoption: bool = False
    workflow_cost_claim: bool = False
    measurement: Measurement | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _positive(value: Any, name: str) -> int:
    if type(value) is not int or value <= 0:
        raise ValueError(f"{name} must be a positive integer")
    return value


def _measure(text: Any, counter: Counter) -> TextMeasurement:
    if not isinstance(text, str) or not text:
        raise ValueError("physical emitted text must be nonempty")
    if counter.identity != ESTIMATOR_ID or counter.exact is not False:
        raise ValueError("counter must retain the externally pinned estimator identity and exactness")
    count = counter.count(text)
    if counter.identity != ESTIMATOR_ID or counter.exact is not False:
        raise ValueError("counter identity or exactness changed while counting")
    byte_count = len(text.encode("utf-8"))
    if type(count) is not int or count <= 0 or count != (byte_count + 3) // 4:
        raise ValueError("counter returned an invalid or scoped estimate")
    return TextMeasurement(byte_count, count, text_sha256(text))


def _validate_pins(expected: MetricBindings) -> None:
    if expected.counter_identity != ESTIMATOR_ID or expected.counter_exact is not False:
        raise ValueError("AF16 requires the frozen estimated-text counter")
    for field in fields(expected):
        if field.type == "str":
            value = getattr(expected, field.name)
            if not isinstance(value, str) or not value:
                raise ValueError(f"empty or invalid external identity: {field.name}")
    budget = _positive(expected.budget_tokens, "budget_tokens")
    ceiling = _positive(expected.canonical_ceiling_tokens, "canonical_ceiling_tokens")
    if budget > ceiling:
        raise ValueError("view budget cannot widen the trusted canonical ceiling")
    ids = expected.candidate_ids
    if not 1 <= len(ids) <= 2 or len(set(ids)) != len(ids) or any(not isinstance(item, str) or not item for item in ids):
        raise ValueError("controller must pin one or two distinct candidate identifiers")
    if expected.candidate_id not in ids:
        raise ValueError("candidate is outside the controller's frozen schedule")


def _accounting(value: Any, measured: TextMeasurement) -> bool:
    return (isinstance(value, Mapping) and type(value.get("tokens")) is int
            and value.get("tokens") == measured.estimated_tokens
            and type(value.get("bytes")) is int and value.get("bytes") == measured.bytes
            and value.get("counter") == measured.counter_identity and value.get("exact") is False)



def _body_in_wire(body: str, wire: str, encoding: Any) -> bool:
    """Check a declared, frame-pinned host format against its actual wire text."""
    if encoding == "verbatim":
        return body in wire
    if encoding != "mcp-calltoolresult-jsontext":
        raise ValueError("wire encoding must explicitly select verbatim or mcp-calltoolresult-jsontext")
    try:
        payload = json.loads(wire)
    except (TypeError, ValueError):
        return False
    if not isinstance(payload, dict) or not isinstance(payload.get("content"), list):
        return False
    return any(isinstance(block, dict) and block.get("type") == "text" and block.get("text") == body
               for block in payload["content"])


def inspect_measurement(canonical_text: str, view_text: str,
                        metadata: Mapping[str, Any], *, expected: MetricBindings,
                        counter: Counter) -> Measurement:
    """Count entire emitted bodies and actual host text; require external custody.

    ``metadata`` contains matching binding fields (except record_sha256 and
    candidate_ids), body accounting, actual canonical_wire_text/wire_text,
    receipt_artifact text, followup_texts, status and all mandatory controls.
    Each wire has an explicit wire_encoding/canonical_wire_encoding descriptor
    (verbatim or mcp-calltoolresult-jsontext), pinned by its capture and frame.
    Status is success, cannot-fit, unavailable, or error. Cannot-fit additionally
    carries the pinned complete minimum_success_text and its own accounting;
    view_accounting always describes the actually emitted diagnostic body.
    """
    _validate_pins(expected)
    record = {"canonical_text": canonical_text, "view_text": view_text, "metadata": dict(metadata)}
    checks = {"physical_capture_pin": record_sha256(record) == expected.record_sha256}
    for name in REQUIRED_BINDINGS:
        actual = metadata.get(name)
        pinned = getattr(expected, name)
        checks[f"binding_{name}"] = actual == pinned and type(actual) is type(pinned)
    canonical = _measure(canonical_text, counter)
    compact = _measure(view_text, counter)
    canonical_wire = _measure(metadata.get("canonical_wire_text"), counter)
    wire = _measure(metadata.get("wire_text"), counter)
    checks["canonical_text_pin"] = canonical.sha256 == expected.canonical_sha256
    checks["canonical_accounting"] = _accounting(metadata.get("canonical_accounting"), canonical)
    checks["view_accounting"] = _accounting(metadata.get("view_accounting"), compact)
    checks["canonical_body_in_wire"] = _body_in_wire(canonical_text, metadata["canonical_wire_text"],
                                                            metadata.get("canonical_wire_encoding"))
    checks["compact_body_in_wire"] = _body_in_wire(view_text, metadata["wire_text"],
                                                          metadata.get("wire_encoding"))
    status = metadata.get("status")
    if status not in ("success", "cannot-fit", "unavailable", "error"):
        raise ValueError("status must explicitly preserve success, cannot-fit, unavailable or error")
    checks["canonical_success"] = metadata.get("canonical_ok") is True
    checks["view_status"] = metadata.get("view_ok") is (status == "success")
    controls = metadata.get("controls", {})
    if not isinstance(controls, Mapping):
        raise ValueError("controls must be an explicit mapping")
    for name in REQUIRED_CONTROLS:
        checks[name] = controls.get(name) is True
    receipt = metadata.get("receipt_artifact")
    if not isinstance(receipt, str) or not receipt:
        raise ValueError("a physical receiving receipt artifact is required")
    checks["receipt_pin"] = text_sha256(receipt) == expected.receipt_sha256
    try:
        receipt_payload = json.loads(receipt)
    except (ValueError, TypeError) as exc:
        raise ValueError("receiving receipt must be JSON text") from exc
    checks["receipt_binding"] = isinstance(receipt_payload, dict) and all(
        receipt_payload.get(name) == getattr(expected, name)
        for name in ("source_id", "case_id", "request_sha256", "canonical_sha256", "profile_sha256",
                     "policy_sha256", "input_sha256", "provider_id", "receipt_provider_id"))
    followup = metadata.get("followup_texts")
    if not isinstance(followup, list):
        raise ValueError("followup_texts must explicitly preserve the observed transport list")
    followup_measurements = tuple(_measure(text, counter) for text in followup)
    minimum = None
    if status == "cannot-fit":
        minimum = _measure(metadata.get("minimum_success_text"), counter)
        checks["minimum_success_pin"] = minimum.sha256 == expected.minimum_success_sha256
        checks["minimum_success_accounting"] = _accounting(metadata.get("minimum_success_accounting"), minimum)
        checks["truthful_budget_diagnostic"] = minimum.estimated_tokens > expected.budget_tokens
    else:
        checks["truthful_budget_diagnostic"] = status == "success"
    wall_ns = metadata.get("wall_ns")
    if wall_ns is not None and (type(wall_ns) is not int or wall_ns < 0):
        raise ValueError("wall_ns must be a nonnegative observed integer or null")
    for name in ("workflow_budget_tokens", "total_budget_tokens", "receipt_budget_tokens"):
        if name in metadata:
            _positive(metadata[name], name)
    return Measurement(expected, status, canonical, compact, canonical_wire, wire,
                       followup_measurements, minimum, checks, wall_ns)


def size_gate(measurement: Measurement) -> GateDecision:
    """Frozen primary full-body rule using integer comparisons only."""
    _validate_pins(measurement.binding)
    checks = dict(measurement.checks)
    required = (*REQUIRED_CAPTURE_CHECKS, *REQUIRED_CONTROLS)
    if measurement.status == "cannot-fit":
        required = (*required, *REQUIRED_MINIMUM_CHECKS)
    for name in required:
        checks[name] = measurement.checks.get(name) is True
    checks["frozen_primary_case"] = measurement.binding.case_id == PRIMARY_CASE
    checks["successful_projection"] = measurement.status == "success"
    checks["within_requested_budget"] = measurement.compact_body.estimated_tokens <= measurement.binding.budget_tokens
    checks["at_most_1000_estimated_tokens"] = measurement.compact_body.estimated_tokens <= MAX_BODY_TOKENS
    checks["at_least_half_smaller"] = 2 * measurement.compact_body.estimated_tokens <= measurement.canonical_body.estimated_tokens
    eligible = all(checks.values())
    # Physical size numbers remain visible for diagnostics, but a mixed or
    # uncontrolled capture cannot establish a paired body-size win.
    body_win = eligible
    return GateDecision(eligible, body_win, checks, tuple(name for name, ok in checks.items() if not ok),
                        successful_cases=int(eligible), measurement=measurement)


def check_comparison(record: Mapping[str, Any], *, expectedpins: MetricBindings | None = None,
                     counter: Counter) -> GateDecision:
    """Score a normalized physical capture only against independently supplied pins.

    Missing external pins remain a one-case negative, never a favorable omitted
    denominator or a self-pinned success. Malformed physical accounting inputs
    raise ValueError; valid error/unavailable/cannot-fit rows are negative cases.
    """
    if expectedpins is None:
        return GateDecision(False, False, {"external_pins": False}, ("external_pins",))
    return size_gate(inspect_measurement(record["canonical_text"], record["view_text"],
                                        record["metadata"], expected=expectedpins, counter=counter))
