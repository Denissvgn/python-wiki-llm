"""Closed detailed-health contract shared by doctor and CI report readers.

The primary partition counts concepts, independently of lint diagnostics. A
comparison attempt is not necessarily compatible. Confirmed missing sources
are separate from successful content comparisons because absence is checked
before producer compatibility. Unknown/unavailable measurements use null.
"""

from __future__ import annotations

from collections.abc import Mapping
from collections import Counter
import re
from typing import Any, NoReturn

from .contracts import HEALTH_DETAILS_SCHEMA_VERSION
from .knowledge_freshness import (
    FRESHNESS_REASON_STATES,
    KNOWN_FRESHNESS_REASON_CODES,
    REASON_FRESHNESS_NOT_MODELED,
    REASON_LIVE_EVALUATION_NOT_PERFORMED,
    comparable_producer_components,
)
from .knowledge_model import ComputedFreshness, ProducerComponent

EXAMPLE_LIMIT = 3
MAX_COMPONENTS = 4096
MAX_TEXT_BYTES = 8192
MAX_COUNT = (2**53) - 1
FRESHNESS_STATES = frozenset(state.value for state in ComputedFreshness)
COMPARABLE_STATES = frozenset(
    {"current", "nonsemantic-source-change", "source-changed"}
)
_HASH = re.compile(r"sha256:[0-9a-f]{64}\Z")
_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9._/-]*\Z")


class HealthDetailsError(ValueError):
    """Detailed health data is incomplete, unsupported or inconsistent."""


def _fail(field: str, message: str) -> NoReturn:
    raise HealthDetailsError(f"{field}: {message}")


def _object(
    value: object, field: str, keys: set[str] | frozenset[str]
) -> Mapping[str, Any]:
    if not isinstance(value, Mapping) or set(value) != keys:
        _fail(field, "fields do not match the contract")
    return value


def _text(value: object, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        _fail(field, "must be nonempty text")
    try:
        size = len(value.encode("utf-8"))
    except UnicodeError:
        _fail(field, "must be UTF-8 text")
    if size > MAX_TEXT_BYTES:
        _fail(field, "exceeds text byte limit")
    return value


def _count(value: object, field: str) -> int:
    if type(value) is not int or not 0 <= value <= MAX_COUNT:
        _fail(field, "must be a bounded non-negative integer")
    return value


def _hash(value: object, field: str, *, nullable: bool = False) -> None:
    if nullable and value is None:
        return
    if not isinstance(value, str) or _HASH.fullmatch(value) is None:
        _fail(field, "must be a SHA-256 commitment")


def _strings(
    value: object, field: str, limit: int, *, ordered: bool = True
) -> list[str]:
    if not isinstance(value, list) or len(value) > limit:
        _fail(field, "must be a bounded array")
    result = [_text(item, field) for item in value]
    if len(result) != len(set(result)) or ordered and result != sorted(result):
        _fail(field, "must be unique and sorted" if ordered else "must be unique")
    return result


def _component(value: object, field: str) -> str:
    component = _object(
        value, field, {"id", "version", "configuration_hash", "limitations"}
    )
    component_id = _text(component["id"], field + ".id")
    if _ID.fullmatch(component_id) is None:
        _fail(field, "invalid component ID")
    _text(component["version"], field + ".version")
    _hash(component["configuration_hash"], field + ".configuration_hash", nullable=True)
    _strings(
        component["limitations"], field + ".limitations", MAX_COMPONENTS, ordered=False
    )
    return component_id


def _producer(value: object, field: str) -> None:
    if value is None:
        return
    producer = _object(
        value,
        field,
        {
            "knowledge_schema_version",
            "generation_options_hash",
            "tool",
            "extractors",
            "plugins",
        },
    )
    _text(producer["knowledge_schema_version"], field + ".knowledge_schema_version")
    _hash(producer["generation_options_hash"], field + ".generation_options_hash")
    identifiers = [_component(producer["tool"], field + ".tool")]
    for kind in ("extractors", "plugins"):
        entries = producer[kind]
        if not isinstance(entries, list) or len(entries) > MAX_COMPONENTS:
            _fail(field + "." + kind, "must be a bounded array")
        ids = [_component(item, field + "." + kind) for item in entries]
        if ids != sorted(set(ids)):
            _fail(field + "." + kind, "must be unique and sorted by ID")
        identifiers.extend(ids)
    if len(identifiers) != len(set(identifiers)):
        _fail(field, "component IDs must be unique across roles")


def _compatible_global_basis(
    recorded: Mapping[str, Any], live: Mapping[str, Any]
) -> bool:
    def component(row: Mapping[str, Any]) -> ProducerComponent:
        return ProducerComponent(
            row["id"],
            row["version"],
            row["configuration_hash"],
            tuple(row["limitations"]),
        )

    if any(
        recorded[key] != live[key]
        for key in ("knowledge_schema_version", "generation_options_hash")
    ):
        return False
    if not comparable_producer_components(
        component(recorded["tool"]),
        component(live["tool"]),
        configuration_required=False,
    ):
        return False
    if [p["id"] for p in recorded["plugins"]] != [p["id"] for p in live["plugins"]]:
        return False
    if not all(
        comparable_producer_components(component(left), component(right))
        for left, right in zip(recorded["plugins"], live["plugins"])
    ):
        return False
    live_extractors = {p["id"]: p for p in live["extractors"]}
    return any(
        p["id"] in live_extractors
        and comparable_producer_components(
            component(p), component(live_extractors[p["id"]])
        )
        for p in recorded["extractors"]
    )


def validate_health_details(
    value: object,
    *,
    wiki_dir: str,
    src_dir: str,
    freshness: Mapping[str, Any],
    availability: str,
) -> Mapping[str, Any]:
    """Validate detailed evidence and reconcile it with the legacy projection."""
    details = _object(
        value,
        "health_details",
        {
            "schema_version",
            "scope",
            "evaluation",
            "snapshot",
            "basis",
            "coverage",
            "reasons",
        },
    )
    if details["schema_version"] != HEALTH_DETAILS_SCHEMA_VERSION:
        _fail("health_details.schema_version", "unsupported version")
    scope = _object(details["scope"], "scope", {"wiki_dir", "src_dir", "selection"})
    if (
        _text(scope["wiki_dir"], "scope.wiki_dir") != wiki_dir
        or _text(scope["src_dir"], "scope.src_dir") != src_dir
    ):
        _fail("scope", "does not match the enclosing report")
    selection = _object(
        scope["selection"], "scope.selection", {"state", "fingerprint", "inputs_hash"}
    )
    if selection["state"] not in ("configured", "legacy", "unavailable"):
        _fail("scope.selection.state", "unsupported state")
    for name in ("fingerprint", "inputs_hash"):
        if selection["state"] == "configured":
            _hash(selection[name], "scope.selection." + name)
        elif selection[name] is not None:
            _fail("scope.selection", "unconfigured selection cannot have commitments")

    evaluation = _object(details["evaluation"], "evaluation", {"state", "reason"})
    state = evaluation["state"]
    if state not in ("evaluated", "partial", "not-evaluated", "unavailable", "failed"):
        _fail("evaluation.state", "unsupported state")
    evaluated = state in {"evaluated", "partial"}
    if (
        evaluation["reason"]
        != {
            "evaluated": "captured-live-evaluation",
            "partial": "source-extraction-incomplete",
            "not-evaluated": "live-evaluation-not-performed",
            "unavailable": "recorded-knowledge-unavailable",
            "failed": "evaluation-failed",
        }[state]
    ):
        _fail("evaluation.reason", "does not match evaluation state")
    snapshot = _object(
        details["snapshot"],
        "snapshot",
        {
            "validated",
            "knowledge_index_hash",
            "evaluated_envelope_hash",
            "surface_index_hash",
            "recorded_source_hash",
            "recorded_markdown_hash",
            "live_source_hash",
        },
    )
    if type(snapshot["validated"]) is not bool:
        _fail("snapshot.validated", "must be a boolean")
    for name in set(snapshot) - {"validated"}:
        _hash(snapshot[name], "snapshot." + name, nullable=True)
    commitments = (
        snapshot[name]
        for name in (
            "knowledge_index_hash",
            "evaluated_envelope_hash",
            "surface_index_hash",
        )
    )
    if snapshot["validated"]:
        if any(value is None for value in commitments):
            _fail("snapshot", "validated artifacts require all exact-byte commitments")
    elif any(value is not None for value in commitments):
        _fail("snapshot", "unvalidated artifacts cannot claim exact-byte commitments")

    basis = _object(
        details["basis"], "basis", {"policy", "analysis_contract", "recorded", "live"}
    )
    if (
        basis["policy"] != "exact-producer-versions"
        or basis["analysis_contract"] is not None
    ):
        _fail("basis", "unsupported comparison contract")
    _producer(basis["recorded"], "basis.recorded")
    _producer(basis["live"], "basis.live")
    if (basis["live"] is not None) != evaluated:
        _fail("basis.live", "does not match the captured evaluation")

    coverage = _object(
        details["coverage"],
        "coverage",
        {
            "total",
            "modeled",
            "unmodeled",
            "evaluated",
            "comparison_attempted",
            "comparable",
            "outcomes",
        },
    )
    known = coverage["total"] is not None
    if known != (availability == "ready"):
        _fail("coverage", "inventory availability must match the enclosing report")
    if known:
        total, modeled, unmodeled = (
            _count(coverage[name], "coverage." + name)
            for name in ("total", "modeled", "unmodeled")
        )
        if total != modeled + unmodeled:
            _fail("coverage", "total must equal modeled plus unmodeled")
        if state == "unavailable":
            _fail("coverage", "known inventory cannot be unavailable")
        if availability != "ready" or basis["recorded"] is None:
            _fail("coverage", "known inventory requires usable recorded knowledge")
        if (
            snapshot["recorded_source_hash"] is None
            or snapshot["recorded_markdown_hash"] is None
        ):
            _fail("snapshot", "recorded knowledge requires snapshot hashes")
    else:
        total = modeled = unmodeled = 0
        if any(coverage[name] is not None for name in coverage):
            _fail("coverage", "unavailable inventory must use null counters")
        if basis["recorded"] is not None or evaluated or snapshot["validated"]:
            _fail("coverage", "unavailable inventory contradicts captured knowledge")
    if evaluated:
        if not known or not freshness["evaluated"]:
            _fail("evaluation", "requires an evaluated recorded inventory")
        outcomes = _object(coverage["outcomes"], "coverage.outcomes", FRESHNESS_STATES)
        for name, count in outcomes.items():
            _count(count, "coverage.outcomes." + name)
        if (
            sum(outcomes.values()) != modeled
            or _count(coverage["evaluated"], "coverage.evaluated") != modeled
        ):
            _fail("coverage", "modeled outcomes must partition the evaluated inventory")
        if _count(coverage["comparable"], "coverage.comparable") != sum(
            outcomes[name] for name in COMPARABLE_STATES
        ):
            _fail(
                "coverage.comparable", "must count only compatible content comparisons"
            )
        if coverage["comparable"]:
            recorded, live = basis["recorded"], basis["live"]
            if (
                not isinstance(recorded, Mapping)
                or not isinstance(live, Mapping)
                or not _compatible_global_basis(recorded, live)
            ):
                _fail("basis", "incompatible producer cannot claim comparable content")
        if (
            _count(coverage["comparison_attempted"], "coverage.comparison_attempted")
            != modeled - outcomes["unknown"]
        ):
            _fail("coverage.comparison_attempted", "does not match comparison outcomes")
        expected = dict(outcomes)
        expected["unknown"] += unmodeled
        if freshness["counts_by_state"] != expected or freshness["concepts"] != total:
            _fail("coverage", "does not reconcile with legacy freshness")
    elif any(
        coverage[name] is not None
        for name in ("evaluated", "comparison_attempted", "comparable", "outcomes")
    ):
        _fail("coverage", "unevaluated comparison counters must be null")
    elif freshness["evaluated"]:
        unknown_only = {
            name: total if name == "unknown" else 0 for name in FRESHNESS_STATES
        }
        if (
            freshness["counts_by_state"] != unknown_only
            or freshness["concepts"] != total
        ):
            _fail("coverage", "unevaluated evidence cannot claim computed outcomes")

    reasons = details["reasons"]
    if not isinstance(reasons, list) or len(reasons) > len(
        KNOWN_FRESHNESS_REASON_CODES
    ):
        _fail("reasons", "must be a bounded reason array")
    codes = []
    reason_total = 0
    reason_states: Counter[str] = Counter()
    unmodeled_reasons = 0
    all_examples: set[str] = set()
    for row in reasons:
        reason = _object(row, "reason", {"code", "concepts", "examples", "omitted"})
        code = _text(reason["code"], "reason.code")
        if code not in KNOWN_FRESHNESS_REASON_CODES:
            _fail("reason.code", "unsupported reason")
        codes.append(code)
        count = _count(reason["concepts"], "reason.concepts")
        if code == REASON_LIVE_EVALUATION_NOT_PERFORMED:
            _fail("reason.code", "cannot occur in an evaluated primary partition")
        if code == REASON_FRESHNESS_NOT_MODELED:
            unmodeled_reasons += count
        else:
            reason_states[FRESHNESS_REASON_STATES[code].value] += count
        examples = _strings(reason["examples"], "reason.examples", EXAMPLE_LIMIT)
        omitted = _count(reason["omitted"], "reason.omitted")
        if (
            count == 0
            or len(examples) != min(count, EXAMPLE_LIMIT)
            or count != len(examples) + omitted
        ):
            _fail("reason", "example accounting must reconcile")
        if all_examples.intersection(examples):
            _fail("reasons", "a concept cannot occur in multiple primary reason groups")
        all_examples.update(examples)
        reason_total += count
    if codes != sorted(set(codes)):
        _fail("reasons", "must be unique and sorted by code")
    if evaluated and reason_total != total:
        _fail("reasons", "primary reasons must partition all concepts")
    if evaluated and (
        unmodeled_reasons != unmodeled
        or any(
            reason_states[state] != coverage["outcomes"][state]
            for state in FRESHNESS_STATES
        )
    ):
        _fail("reasons", "primary reason states must match the modeled partition")
    if not evaluated and reasons:
        _fail("reasons", "no primary comparison reasons exist before evaluation")
    return details
