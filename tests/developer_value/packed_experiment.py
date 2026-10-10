"""Pure matched-maintenance scoring over externally pinned physical captures.

This module runs no providers and makes no task-productivity or adoption claim.
First observations are not cold-cache measurements: OS caches are uncontrolled.
"""
from __future__ import annotations

from collections.abc import Mapping
from dataclasses import asdict, dataclass
import hashlib
import json
import math
from typing import Any, cast

SCHEMA = "af17-matched-maintenance/v1"
REQUIRED_CONTROLS = (
    "standalone_lint", "standalone_ci", "publication", "corruption",
    "concurrent_edit", "receiving", "logical_equivalence", "source_prose_preservation",
)
MATCH_KEYS = (
    "input_sha256", "matched_config_sha256", "backend", "selection_sha256",
    "helper_sha256", "scope",
)
COST_KEYS = ("wall_ns", "cpu_ns", "setup_ns", "copy_ns", "postcheck_ns")
GAIN_METRICS = ("warm_wall_ns", "full_observed_warm_ns")
_DURATION_NAMES = {"duration", "duration_ms", "elapsed_seconds", "wall_ns", "cpu_ns"}
_PHASE_DURATION_NAMES = {"check", "load", "evaluate"}
_PHASE_DURATION_PREFIXES = (
    ("operation_result", "knowledge_summary", "phase_durations_ms"),
    ("operation_result", "report", "knowledge_summary", "phase_durations_ms"),
)


def text_sha256(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def record_sha256(value: Any) -> str:
    return text_sha256(json.dumps(value, sort_keys=True, separators=(",", ":"),
                                  ensure_ascii=False, allow_nan=False))


@dataclass(frozen=True)
class CapturePins:
    """Controller-authored pins, supplied separately from captured observations."""

    plan_sha256: str
    record_sha256: str
    input_sha256: str
    baseline_provider_sha256: str
    candidate_provider_sha256: tuple[tuple[str, str], ...]


@dataclass(frozen=True)
class ExperimentReport:
    checks: Mapping[str, bool]
    candidates: Mapping[str, Any]
    planned_slots: int
    observed_slots: int
    successful_slots: int
    status_counts: Mapping[str, int]
    plan_text: str
    record_text: str
    pins: CapturePins

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class GateDecision:
    eligible: bool
    maintenance_gain: bool
    candidate_gains: Mapping[str, bool]
    reasons: tuple[str, ...]
    planned_slots: int
    observed_slots: int
    successful_slots: int
    default_adoption: bool = False
    task_productivity_claim: bool = False
    os_cache: str = "uncontrolled"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _nonempty(value: Any) -> bool:
    return isinstance(value, str) and bool(value)


def _hash(value: Any) -> bool:
    return (isinstance(value, str) and len(value) == 64
            and all(char in "0123456789abcdef" for char in value))


def _ns(value: Any) -> bool:
    return type(value) is int and value >= 0


def _strict_json(text: str) -> Any:
    def pairs(items: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in items:
            if key in result:
                raise ValueError("duplicate output key")
            result[key] = value
        return result
    def constant(value: str) -> Any:
        raise ValueError(f"nonfinite JSON number: {value}")
    return json.loads(text, object_pairs_hook=pairs, parse_constant=constant)


def _duration_paths_valid(paths: Any) -> bool:
    if not isinstance(paths, list):
        return False
    for path in paths:
        if not isinstance(path, str) or not path.startswith("/") or "~" in path:
            return False
        parts = path.split("/")[1:]
        if any(part in {"", ".", ".."} for part in parts):
            return False
        scalar_timing = (parts[-1] in _DURATION_NAMES
                         and (len(parts) == 1 or parts[:-1] == ["telemetry"]))
        reported_phase = (parts[-1] in _PHASE_DURATION_NAMES
                          and tuple(parts[:-1]) in _PHASE_DURATION_PREFIXES)
        if not (scalar_timing or reported_phase):
            return False
    return len(set(paths)) == len(paths)


def _normalization_valid(value: Any, operations: list[str]) -> bool:
    if not isinstance(value, Mapping) or set(value) != {"duration_paths", "fixture_roots"}:
        return False
    paths = value.get("duration_paths")
    valid_paths = (_duration_paths_valid(paths) if isinstance(paths, list)
                   else isinstance(paths, Mapping) and set(paths) == set(operations)
                   and all(_duration_paths_valid(item) for item in paths.values()))
    roots = value.get("fixture_roots")
    return (valid_paths and isinstance(roots, list)
            and all(isinstance(root, str) and root.startswith("/") and root != "/" and not root.endswith("/")
                    for root in roots))


def _normalize(text: str, normalization: Mapping[str, Any], operation: str | None = None) -> str:
    value = _strict_json(text)
    paths = normalization["duration_paths"]
    if isinstance(paths, Mapping):
        paths = paths[operation]
    for path in paths:
        parts = path.split("/")[1:]
        node = value
        for part in parts[:-1]:
            node = node[int(part)] if isinstance(node, list) else node[part]
        key = parts[-1]
        original = node[int(key)] if isinstance(node, list) else node[key]
        if type(original) not in (int, float) or not math.isfinite(original) or original < 0:
            raise ValueError("declared duration is not an observed nonnegative number")
        if isinstance(node, list):
            node[int(key)] = "<declared-volatile-duration>"
        else:
            node[key] = "<declared-volatile-duration>"
    roots = sorted(normalization["fixture_roots"], key=len, reverse=True)
    def replace(value: Any) -> Any:
        if isinstance(value, str):
            for root in roots:
                if value == root or value.startswith(root + "/"):
                    return "<owned-fixture-root>" + value[len(root):]
            return value
        if isinstance(value, list):
            return [replace(item) for item in value]
        if isinstance(value, dict):
            return {key: replace(item) for key, item in value.items()}
        return value
    return record_sha256(replace(value))


def _median(values: list[int]) -> int:
    return sorted(values)[len(values) // 2]


def _stats(rows: list[Mapping[str, Any]]) -> dict[str, Any]:
    first = next(row for row in rows if row["repetition"] == 0)
    warm = [row for row in rows if row["repetition"] != 0]
    result: dict[str, Any] = {
        "first": {key: first[key] for key in COST_KEYS},
        "warm": {key: {"median": _median([row[key] for row in warm]),
                       "min": min(row[key] for row in warm),
                       "max": max(row[key] for row in warm)} for key in COST_KEYS},
    }
    # These externally timed phases remain visible; no preparation/copy/check
    # cost is silently included in (or excluded from) the operation wall metric.
    totals = [row["wall_ns"] + row["setup_ns"] + row["copy_ns"] + row["postcheck_ns"]
              for row in warm]
    result["full_observed_warm_ns"] = {"median": _median(totals), "min": min(totals), "max": max(totals)}
    return result


def inspect_experiment(plan: Mapping[str, Any], record: Mapping[str, Any], *,
                       expected: CapturePins) -> ExperimentReport:
    """Check physical custody and all scheduled slots before calculating gains.

    Re-pinning a damaged record never changes the separately pinned plan,
    provider identities, or input binding. Missing/failed slots stay in the
    denominator and have no fabricated time or summary statistic.
    """
    if not isinstance(expected, CapturePins):
        raise ValueError("independent capture pins are required")
    plan_text = json.dumps(plan, sort_keys=True, separators=(",", ":"), allow_nan=False)
    record_text = json.dumps(record, sort_keys=True, separators=(",", ":"), allow_nan=False)
    checks: dict[str, bool] = {
        "plan_pin": _hash(expected.plan_sha256) and record_sha256(plan) == expected.plan_sha256,
        "physical_capture_pin": _hash(expected.record_sha256) and record_sha256(record) == expected.record_sha256,
        "schema": plan.get("schema_version") == record.get("schema_version") == SCHEMA,
    }
    baseline = plan.get("baseline_id")
    candidates = plan.get("candidate_ids", [])
    operations = plan.get("operations", [])
    targets = plan.get("target_operations", [])
    candidate_pins = dict(expected.candidate_provider_sha256)
    checks["schedule"] = (isinstance(candidates, list) and 1 <= len(candidates) <= 2
        and all(_nonempty(item) for item in candidates) and len(set(candidates)) == len(candidates)
        and _nonempty(baseline) and baseline not in candidates
        and isinstance(operations, list) and bool(operations)
        and all(_nonempty(item) for item in operations) and len(set(operations)) == len(operations)
        and isinstance(targets, list) and bool(targets) and all(_nonempty(item) for item in targets)
        and len(set(targets)) == len(targets)
        and all(item in operations for item in targets)
        and len(candidate_pins) == len(expected.candidate_provider_sha256)
        and set(candidate_pins) == set(candidates)
        and _hash(expected.baseline_provider_sha256) and all(_hash(item) for item in candidate_pins.values()))
    if not checks["schedule"]:
        return ExperimentReport(checks, {}, 0, 0, 0, {}, plan_text, record_text, expected)
    baseline = cast(str, baseline)
    normalization = plan.get("normalization", {})
    checks["normalization_plan"] = _normalization_valid(normalization, operations)
    checks["threshold"] = plan.get("threshold") == {"relative": 0.1, "absolute_ns": 50_000_000}
    checks["cost_scope"] = plan.get("gain_metrics") == list(GAIN_METRICS)
    checks["cache_scope"] = plan.get("os_cache") == "uncontrolled"
    checks["required_controls"] = plan.get("required_controls") == list(REQUIRED_CONTROLS)
    match = plan.get("match", {})
    checks["matched_foundation"] = (isinstance(match, Mapping) and set(match) == set(MATCH_KEYS)
        and all(_nonempty(match.get(key)) for key in MATCH_KEYS)
        and _hash(expected.input_sha256) and match.get("input_sha256") == expected.input_sha256
        and all(_hash(match.get(key)) for key in MATCH_KEYS if key.endswith("sha256")))
    arms = [baseline, *candidates]
    planned = {(arm, operation, slot) for arm in arms for operation in operations for slot in range(6)}
    observations = record.get("observations", [])
    checks["observations_shape"] = isinstance(observations, list)
    if not isinstance(observations, list):
        observations = []
    observed: dict[tuple[str, str, int], Mapping[str, Any]] = {}
    counts: dict[str, int] = dict.fromkeys(("success", "error", "timeout", "uninvoked"), 0)
    valid = True
    for index, row in enumerate(observations):
        if not isinstance(row, Mapping):
            valid = False
            continue
        arm, operation, repetition = row.get("arm"), row.get("operation"), row.get("repetition")
        if not isinstance(arm, str) or not isinstance(operation, str) or type(repetition) is not int:
            valid = False
            continue
        key = (arm, operation, repetition)
        if key not in planned or key in observed:
            valid = False
            continue
        observed[key] = row
        status = row.get("status")
        if isinstance(status, str) and status in counts:
            counts[status] += 1
        else:
            valid = False
        provider = expected.baseline_provider_sha256 if key[0] == baseline else candidate_pins[key[0]]
        checks[f"slot_{index}_binding"] = (row.get("provider_sha256") == provider
            and all(row.get(name) == match.get(name) for name in MATCH_KEYS)
            and row.get("observation") == ("first" if key[2] == 0 else "warm"))
        checks[f"slot_{index}_receipt"] = (_nonempty(row.get("receipt_text"))
            and text_sha256(row["receipt_text"]) == row.get("receipt_sha256"))
        costs_ok = all(_ns(row.get(name)) for name in COST_KEYS)
        if status != "success":
            checks[f"slot_{index}_failure_costs"] = (all(row.get(name) is None or _ns(row.get(name)) for name in COST_KEYS)
                and _nonempty(row.get("error")))
            continue
        checks[f"slot_{index}_costs"] = costs_ok
        output = row.get("output_text")
        checks[f"slot_{index}_output_pin"] = (isinstance(output, str) and bool(output) and text_sha256(output) == row.get("output_sha256"))
        if checks["normalization_plan"] and checks[f"slot_{index}_output_pin"]:
            try:
                normalized = _normalize(cast(str, output), normalization, operation)
            except (ValueError, TypeError, KeyError, IndexError, OverflowError):
                normalized = None
            checks[f"slot_{index}_normalization"] = normalized is not None and normalized == row.get("logical_sha256")
        else:
            checks[f"slot_{index}_normalization"] = False
    counts["uninvoked"] += len(planned - observed.keys())
    checks["scheduled_slots"] = valid and set(observed) == planned
    checks["successful_slots"] = counts["success"] == len(planned)
    for candidate in candidates:
        controls = record.get("controls", {}).get(candidate, []) if isinstance(record.get("controls"), Mapping) else []
        control_shape = (isinstance(controls, list)
                         and all(isinstance(item, Mapping) and _nonempty(item.get("name")) for item in controls))
        by_name = {item["name"]: item for item in controls} if control_shape else {}
        checks[f"{candidate}_controls"] = (control_shape and len(by_name) == len(controls) == len(REQUIRED_CONTROLS)
            and set(by_name) == set(REQUIRED_CONTROLS)
            and all(item.get("status") == "pass" and _nonempty(item.get("receipt_text"))
                    and text_sha256(item["receipt_text"]) == item.get("receipt_sha256") for item in by_name.values()))
    summaries: dict[str, Any] = {}
    for candidate in candidates:
        summaries[candidate] = {"operations": {}, "target_wins": [], "regressions": []}
        for operation in operations:
            base_rows = [observed.get((baseline, operation, slot), {}) for slot in range(6)]
            cand_rows = [observed.get((candidate, operation, slot), {}) for slot in range(6)]
            equivalent = all(base.get("logical_sha256") == proposed.get("logical_sha256")
                             and _hash(base.get("logical_sha256")) for base, proposed in zip(base_rows, cand_rows))
            checks[f"{candidate}_{operation}_equivalence"] = equivalent
            if not all(row.get("status") == "success" and all(_ns(row.get(key)) for key in COST_KEYS)
                       for row in [*base_rows, *cand_rows]):
                summaries[candidate]["operations"][operation] = {"complete": False, "equivalent": equivalent}
                continue
            base_stats, cand_stats = _stats(base_rows), _stats(cand_rows)
            before, after = base_stats["warm"]["wall_ns"]["median"], cand_stats["warm"]["wall_ns"]["median"]
            delta = before - after
            full_before, full_after = base_stats["full_observed_warm_ns"]["median"], cand_stats["full_observed_warm_ns"]["median"]
            full_delta = full_before - full_after
            wall_gain = before > 0 and delta >= 50_000_000 and delta * 10 >= before
            full_gain = full_before > 0 and full_delta >= 50_000_000 and full_delta * 10 >= full_before
            wall_regression = -delta > 50_000_000 and -delta * 10 > before
            full_regression = -full_delta > 50_000_000 and -full_delta * 10 > full_before
            gain = wall_gain and full_gain
            regression = wall_regression or full_regression
            summaries[candidate]["operations"][operation] = {
                "complete": True, "equivalent": equivalent, "baseline": base_stats, "candidate": cand_stats,
                "warm_wall_delta_ns": delta, "warm_wall_relative_improvement": delta / before if before else None,
                "full_observed_warm_delta_ns": full_delta,
                "full_observed_warm_relative_improvement": full_delta / full_before if full_before else None,
                "warm_wall_gain": wall_gain, "full_observed_gain": full_gain,
                "warm_wall_regression": wall_regression, "full_observed_regression": full_regression,
                "target_gain": gain and operation in targets, "material_regression": regression,
            }
            if gain and operation in targets:
                summaries[candidate]["target_wins"].append(operation)
            if regression:
                summaries[candidate]["regressions"].append(operation)
    return ExperimentReport(checks, summaries, len(planned), len(observed), counts["success"],
                            counts, plan_text, record_text, expected)


def maintenance_gate(report: ExperimentReport) -> GateDecision:
    """Recheck the capture foundation; a fabricated positive summary cannot win."""
    if not isinstance(report, ExperimentReport):
        return GateDecision(False, False, {}, ("missing validated capture foundation",), 0, 0, 0)
    try:
        checked = inspect_experiment(_strict_json(report.plan_text), _strict_json(report.record_text), expected=report.pins)
    except (ValueError, TypeError, KeyError, AttributeError, OverflowError):
        return GateDecision(False, False, {}, ("invalid validated capture foundation",), 0, 0, 0)
    eligible = bool(checked.checks) and all(checked.checks.values())
    gains = {candidate: eligible and bool(value["target_wins"]) and not value["regressions"]
             for candidate, value in checked.candidates.items()}
    reasons = tuple(name for name, passed in checked.checks.items() if not passed)
    if eligible:
        reasons += tuple(f"{candidate}: material regression in {operation}"
                         for candidate, value in checked.candidates.items() for operation in value["regressions"])
        if not any(gains.values()):
            reasons += ("no candidate meets the targeted gain without material regressions",)
    return GateDecision(eligible, any(gains.values()), gains, reasons,
                        checked.planned_slots, checked.observed_slots, checked.successful_slots)
