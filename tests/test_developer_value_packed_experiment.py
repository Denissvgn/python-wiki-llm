"""Matched timing and fail-closed capture integrity controls for AF17."""
from __future__ import annotations

from copy import deepcopy
from dataclasses import replace
import json
from typing import Any

import pytest

from tests.developer_value.packed_experiment import (
    COST_KEYS, GAIN_METRICS, MATCH_KEYS, REQUIRED_CONTROLS, SCHEMA, CapturePins,
    inspect_experiment, maintenance_gate, record_sha256, text_sha256,
)


def pin(label: str) -> str:
    return text_sha256(label)


def sample(*, before: int = 500_000_000, after: int = 450_000_000,
           candidates: int = 1, overhead: bool = False) -> tuple[dict[str, Any], dict[str, Any], CapturePins]:
    ids = [f"C{index + 1}" for index in range(candidates)]
    match = {"input_sha256": pin("input"), "matched_config_sha256": pin("config"),
             "backend": "packed", "selection_sha256": pin("selection"),
             "helper_sha256": pin("helper"), "scope": "maintenance-only"}
    plan = {"schema_version": SCHEMA, "baseline_id": "baseline", "candidate_ids": ids,
            "operations": ["sync_unchanged", "standalone_lint"], "target_operations": ["sync_unchanged"],
            "match": match, "normalization": {"duration_paths": ["/telemetry/duration_ms"],
                                                "fixture_roots": ["/owned/base", "/owned/candidate"]},
            "os_cache": "uncontrolled", "threshold": {"relative": 0.1, "absolute_ns": 50_000_000},
            "gain_metrics": list(GAIN_METRICS),
            "required_controls": list(REQUIRED_CONTROLS)}
    observations = []
    for arm in ["baseline", *ids]:
        for operation in plan["operations"]:
            for slot in range(6):
                wall = before if arm == "baseline" or operation != "sync_unchanged" else after
                # A huge first observation cannot be mixed into the warm median.
                wall = wall * 50 if slot == 0 else wall
                output = json.dumps({"ok": True, "facts": ["required fact"],
                                     "root": "/owned/base/file.py" if arm == "baseline" else "/owned/candidate/file.py",
                                     "telemetry": {"duration_ms": wall / 1_000_000}})
                logical = record_sha256({"ok": True, "facts": ["required fact"],
                                         "root": "<owned-fixture-root>/file.py",
                                         "telemetry": {"duration_ms": "<declared-volatile-duration>"}})
                receipt = json.dumps({"arm": arm, "operation": operation, "slot": slot,
                                      "output_sha256": text_sha256(output), "wall_ns": wall})
                observations.append({"arm": arm, "operation": operation, "repetition": slot,
                    "observation": "first" if slot == 0 else "warm", "status": "success", **match,
                    "provider_sha256": pin(arm), "wall_ns": wall, "cpu_ns": 10,
                    "setup_ns": 20 if overhead else 0, "copy_ns": 30 if overhead else 0, "postcheck_ns": 40 if overhead else 0,
                    "output_text": output, "output_sha256": text_sha256(output), "logical_sha256": logical,
                    "receipt_text": receipt, "receipt_sha256": text_sha256(receipt)})
    controls = {candidate: [{"name": name, "status": "pass", "receipt_text": name,
                            "receipt_sha256": text_sha256(name)} for name in REQUIRED_CONTROLS] for candidate in ids}
    record = {"schema_version": SCHEMA, "observations": observations, "controls": controls}
    pins = CapturePins(record_sha256(plan), record_sha256(record), match["input_sha256"], pin("baseline"),
                       tuple((candidate, pin(candidate)) for candidate in ids))
    return plan, record, pins


def repin(record: dict[str, Any], pins: CapturePins) -> CapturePins:
    return replace(pins, record_sha256=record_sha256(record))


def score(plan: dict[str, Any], record: dict[str, Any], pins: CapturePins):
    return maintenance_gate(inspect_experiment(plan, record, expected=pins))


def test_exact_threshold_and_first_warm_cost_scope() -> None:
    plan, record, pins = sample(after=449_999_991, overhead=True)
    report = inspect_experiment(plan, record, expected=pins)
    gate = maintenance_gate(report)
    assert gate.eligible and gate.maintenance_gain
    assert gate.planned_slots == gate.observed_slots == gate.successful_slots == 24
    operation = report.candidates["C1"]["operations"]["sync_unchanged"]
    assert operation["baseline"]["first"]["wall_ns"] == 25_000_000_000
    assert operation["baseline"]["warm"]["wall_ns"] == {"median": 500_000_000, "min": 500_000_000, "max": 500_000_000}
    assert operation["candidate"]["full_observed_warm_ns"]["median"] == 450_000_081
    assert gate.os_cache == "uncontrolled" and not gate.default_adoption and not gate.task_productivity_claim


@pytest.mark.parametrize(("before", "after", "win"), [
    (500_000_000, 450_000_000, True), (500_000_000, 450_000_001, False),
    (1_000_000_000, 950_000_000, False), (100_000_000, 50_000_001, False),
    (100_000_000, 50_000_000, True), (0, 0, False),
])
def test_gain_requires_both_unrounded_thresholds(before: int, after: int, win: bool) -> None:
    plan, record, pins = sample(before=before, after=after)
    assert score(plan, record, pins).maintenance_gain is win


@pytest.mark.parametrize(("increase", "regression"), [
    (50_000_000, False), (50_000_001, True), (49_999_999, False),
])
def test_regression_on_nontarget_operation_blocks_other_gain(increase: int, regression: bool) -> None:
    plan, record, pins = sample()
    for row in record["observations"]:
        if row["arm"] == "C1" and row["operation"] == "standalone_lint" and row["repetition"]:
            row["wall_ns"] += increase
    report = inspect_experiment(plan, record, expected=repin(record, pins))
    assert bool(report.candidates["C1"]["regressions"]) is regression
    assert maintenance_gate(report).maintenance_gain is not regression


def test_warm_median_uses_five_slots_and_retains_range() -> None:
    plan, record, pins = sample()
    values = [1, 2, 450_000_000, 2_000_000_000, 3_000_000_000]
    for row in record["observations"]:
        if row["arm"] == "C1" and row["operation"] == "sync_unchanged" and row["repetition"]:
            row["wall_ns"] = values[row["repetition"] - 1]
    report = inspect_experiment(plan, record, expected=repin(record, pins))
    assert report.candidates["C1"]["operations"]["sync_unchanged"]["candidate"]["warm"]["wall_ns"] == {
        "median": 450_000_000, "min": 1, "max": 3_000_000_000}
    assert maintenance_gate(report).maintenance_gain


@pytest.mark.parametrize("key", MATCH_KEYS)
def test_repinning_record_does_not_change_matched_foundation(key: str) -> None:
    plan, record, pins = sample()
    record["observations"][0][key] = pin("different")
    assert not score(plan, record, repin(record, pins)).eligible


@pytest.mark.parametrize("key", COST_KEYS)
@pytest.mark.parametrize("value", [None, -1, True, 1.5, "0"])
def test_missing_or_invalid_success_cost_cannot_turn_into_zero(key: str, value: Any) -> None:
    plan, record, pins = sample()
    record["observations"][0][key] = value
    assert not score(plan, record, repin(record, pins)).maintenance_gain


@pytest.mark.parametrize("status", ["error", "timeout", "uninvoked"])
def test_failed_slot_retained_in_denominator_without_statistics(status: str) -> None:
    plan, record, pins = sample()
    row = record["observations"][0]
    row.update(status=status, wall_ns=None, cpu_ns=None, setup_ns=None, copy_ns=None, postcheck_ns=None,
               error="actual operation did not complete")
    report = inspect_experiment(plan, record, expected=repin(record, pins))
    gate = maintenance_gate(report)
    assert not gate.eligible and not gate.maintenance_gain
    assert report.planned_slots == report.observed_slots == 24
    assert report.successful_slots == 23 and report.status_counts[status] == 1
    assert report.candidates["C1"]["operations"]["sync_unchanged"]["complete"] is False


def test_missing_slot_is_uninvoked_not_removed_from_denominator() -> None:
    plan, record, pins = sample()
    record["observations"].pop()
    report = inspect_experiment(plan, record, expected=repin(record, pins))
    assert report.status_counts["uninvoked"] == 1
    assert report.planned_slots == 24 and report.observed_slots == 23
    assert not maintenance_gate(report).eligible


@pytest.mark.parametrize("name", REQUIRED_CONTROLS)
@pytest.mark.parametrize("status", ["fail", "uninvoked"])
def test_every_required_control_must_have_actual_pass_receipt(name: str, status: str) -> None:
    plan, record, pins = sample()
    next(item for item in record["controls"]["C1"] if item["name"] == name)["status"] = status
    assert not score(plan, record, repin(record, pins)).eligible


@pytest.mark.parametrize("field", ["output_text", "output_sha256", "receipt_text", "receipt_sha256", "provider_sha256"])
def test_capture_custody_cannot_be_self_repaired_by_whole_record_pin(field: str) -> None:
    plan, record, pins = sample()
    record["observations"][0][field] = "changed"
    assert not score(plan, record, repin(record, pins)).eligible


def test_decisive_fact_change_cannot_be_hidden_by_rehashed_logical_claim() -> None:
    plan, record, pins = sample()
    row = next(item for item in record["observations"] if item["arm"] == "C1")
    output = json.loads(row["output_text"])
    output["facts"] = []
    row["output_text"] = json.dumps(output)
    row["output_sha256"] = text_sha256(row["output_text"])
    output["telemetry"]["duration_ms"] = "<declared-volatile-duration>"
    output["root"] = "<owned-fixture-root>/file.py"
    row["logical_sha256"] = record_sha256(output)
    assert not score(plan, record, repin(record, pins)).maintenance_gain


@pytest.mark.parametrize("duration_paths", [["/facts"], ["/ok"], ["/telemetry/duration_ms", "/telemetry/duration_ms"], [""]])
def test_even_new_plan_pin_cannot_authorize_dropping_correctness_fields(duration_paths: list[str]) -> None:
    plan, record, pins = sample()
    plan["normalization"]["duration_paths"] = duration_paths
    pins = replace(pins, plan_sha256=record_sha256(plan))
    assert not score(plan, record, pins).eligible


def test_wrong_schedule_or_threshold_pin_is_not_inferred_from_observations() -> None:
    plan, record, pins = sample()
    plan["threshold"]["absolute_ns"] = 1
    assert not score(plan, record, replace(pins, plan_sha256=record_sha256(plan))).eligible


def test_forged_direct_gate_summary_is_rechecked_against_raw_capture() -> None:
    plan, record, pins = sample(after=499_000_000)
    report = inspect_experiment(plan, record, expected=pins)
    invented = deepcopy(report.candidates)
    invented["C1"]["target_wins"] = ["sync_unchanged"]
    forged = replace(report, checks={"made_up": True}, candidates=invented)
    assert not maintenance_gate(forged).maintenance_gain
    assert not maintenance_gate(None).maintenance_gain  # type: ignore[arg-type]


def test_undeclared_candidate_or_duplicate_slot_cannot_replace_required_observation() -> None:
    plan, record, pins = sample()
    record["observations"].append(deepcopy(record["observations"][0]))
    assert not score(plan, record, repin(record, pins)).eligible
    record["observations"][-1]["arm"] = "undeclared"
    assert not score(plan, record, repin(record, pins)).eligible


def test_two_candidates_are_bounded_and_scored_separately() -> None:
    plan, record, pins = sample(candidates=2)
    for row in record["observations"]:
        if row["arm"] == "C2" and row["operation"] == "sync_unchanged":
            row["wall_ns"] = 499_000_000
    gate = score(plan, record, repin(record, pins))
    assert gate.eligible and gate.candidate_gains == {"C1": True, "C2": False}
    assert gate.planned_slots == 36
    plan["candidate_ids"].append("C3")
    assert not score(plan, record, replace(pins, plan_sha256=record_sha256(plan))).eligible


def test_json_duplicates_and_nonfinite_output_are_rejected() -> None:
    plan, record, pins = sample()
    for bad in ('{"ok":true,"ok":false}', '{"value":NaN}'):
        record["observations"][0].update(output_text=bad, output_sha256=text_sha256(bad))
        assert not score(plan, record, repin(record, pins)).eligible


def test_whole_capture_and_plan_pins_are_required() -> None:
    plan, record, pins = sample()
    assert not score(plan, record, replace(pins, record_sha256=pin("unrelated"))).eligible
    assert not score(plan, record, replace(pins, plan_sha256=pin("unrelated"))).eligible
    with pytest.raises(ValueError, match="independent capture pins"):
        inspect_experiment(plan, record, expected=None)  # type: ignore[arg-type]


@pytest.mark.parametrize("phase", ["setup_ns", "copy_ns", "postcheck_ns"])
def test_moving_work_outside_operation_wall_does_not_create_gain(phase: str) -> None:
    plan, record, pins = sample(after=200_000_000)
    for row in record["observations"]:
        if row["arm"] == "C1":
            row[phase] = 1_000_000_000
    report = inspect_experiment(plan, record, expected=repin(record, pins))
    operation = report.candidates["C1"]["operations"]["sync_unchanged"]
    assert operation["warm_wall_gain"] and not operation["full_observed_gain"]
    assert operation["full_observed_regression"]
    assert not maintenance_gate(report).maintenance_gain


def test_full_cost_regression_on_other_operation_blocks_wall_gain() -> None:
    plan, record, pins = sample()
    for row in record["observations"]:
        if row["arm"] == "C1" and row["operation"] == "standalone_lint":
            row["postcheck_ns"] = 50_000_001
    report = inspect_experiment(plan, record, expected=repin(record, pins))
    assert report.candidates["C1"]["regressions"] == ["standalone_lint"]
    assert not maintenance_gate(report).maintenance_gain


def test_full_cost_gate_is_declared_before_observation_not_inferred() -> None:
    plan, record, pins = sample()
    plan.pop("gain_metrics")
    assert not score(plan, record, replace(pins, plan_sha256=record_sha256(plan))).eligible


def per_operation_sample() -> tuple[dict[str, Any], dict[str, Any], CapturePins]:
    plan, record, pins = sample()
    plan["normalization"]["duration_paths"] = {
        "sync_unchanged": ["/telemetry/duration_ms"],
        "standalone_lint": ["/operation_result/knowledge_summary/phase_durations_ms/check",
                            "/operation_result/knowledge_summary/phase_durations_ms/load",
                            "/operation_result/knowledge_summary/phase_durations_ms/evaluate"],
    }
    for row in record["observations"]:
        if row["operation"] == "standalone_lint":
            output = json.loads(row["output_text"])
            output.pop("telemetry")
            output["operation_result"] = {"knowledge_summary": {
                                "phase_durations_ms": {"check": 0, "load": 0.0125, "evaluate": 7.25},
                                "violations": [], "ok": True,
                                "runtime_cache": {"enabled": True, "hits": 0, "misses": 1}}}
            row["output_text"] = json.dumps(output)
            row["output_sha256"] = text_sha256(row["output_text"])
            output["root"] = "<owned-fixture-root>/file.py"
            output["operation_result"]["knowledge_summary"]["phase_durations_ms"] = {
                "check": "<declared-volatile-duration>", "load": "<declared-volatile-duration>",
                "evaluate": "<declared-volatile-duration>"}
            row["logical_sha256"] = record_sha256(output)
    return plan, record, replace(repin(record, pins), plan_sha256=record_sha256(plan))


def test_each_operation_can_retain_full_heterogeneous_result_with_declared_telemetry() -> None:
    plan, record, pins = per_operation_sample()
    assert score(plan, record, pins).maintenance_gain
    row = next(item for item in record["observations"] if item["operation"] == "standalone_lint" and item["arm"] == "C1")
    output = json.loads(row["output_text"])
    output["operation_result"]["knowledge_summary"]["violations"] = ["decisive new violation"]
    row["output_text"] = json.dumps(output)
    row["output_sha256"] = text_sha256(row["output_text"])
    assert not score(plan, record, repin(record, pins)).eligible


@pytest.mark.parametrize("mutation", ["missing", "unknown", "nonlist", "wrong_phase_path", "unknown_phase"])
def test_operation_duration_map_is_complete_and_strictly_telemetry_only(mutation: str) -> None:
    plan, record, pins = per_operation_sample()
    paths = plan["normalization"]["duration_paths"]
    if mutation == "missing":
        paths.pop("standalone_lint")
    elif mutation == "unknown":
        paths["undeclared-operation"] = []
    elif mutation == "nonlist":
        paths["standalone_lint"] = "duration_ms"
    elif mutation == "wrong_phase_path":
        paths["standalone_lint"] = ["/report/facts/load"]
    else:
        paths["standalone_lint"] = ["/report/phase_durations_ms/decisive_fact"]
    assert not score(plan, record, replace(pins, plan_sha256=record_sha256(plan))).eligible


@pytest.mark.parametrize("value", [True, -0.25, "1", None, float("inf")])
def test_phase_telemetry_must_be_finite_nonnegative_observed_number(value: Any) -> None:
    plan, record, pins = per_operation_sample()
    row = next(item for item in record["observations"] if item["operation"] == "standalone_lint")
    output = json.loads(row["output_text"])
    output["operation_result"]["knowledge_summary"]["phase_durations_ms"]["load"] = value
    row["output_text"] = json.dumps(output)
    row["output_sha256"] = text_sha256(row["output_text"])
    assert not score(plan, record, repin(record, pins)).eligible


def test_declared_telemetry_path_must_exist_without_silent_omission() -> None:
    plan, record, pins = per_operation_sample()
    plan["normalization"]["duration_paths"]["sync_unchanged"] = ["/operation_result/knowledge_summary/phase_durations_ms/load"]
    assert not score(plan, record, replace(pins, plan_sha256=record_sha256(plan))).eligible


def test_runtime_cache_correctness_fields_cannot_be_normalized_as_timing() -> None:
    plan, record, pins = per_operation_sample()
    plan["normalization"]["duration_paths"]["standalone_lint"].append("/report/runtime_cache/hits")
    assert not score(plan, record, replace(pins, plan_sha256=record_sha256(plan))).eligible


@pytest.mark.parametrize("path", [
    "/decisive_fact/phase_durations_ms/load", "/source_facts/duration_ms",
    "/logical_model/phase_durations_ms/load", "/logical_model/duration_ms",
    "/operation_result/knowledge_summary/phase_durations_ms/nested/load",
    "/operation_result/knowledge_summary/runtime_cache/duration_ms",
    "/counter/duration", "/producer/elapsed_seconds",
])
def test_known_duration_leaf_inside_correctness_tree_cannot_be_erased(path: str) -> None:
    plan, record, pins = sample()
    plan["normalization"]["duration_paths"] = [path]
    assert not score(plan, record, replace(pins, plan_sha256=record_sha256(plan))).eligible


def test_cli_report_timing_prefix_preserves_full_nested_report() -> None:
    plan, record, pins = per_operation_sample()
    plan["normalization"]["duration_paths"]["standalone_lint"] = [
        path.replace("/operation_result/", "/operation_result/report/")
        for path in plan["normalization"]["duration_paths"]["standalone_lint"]]
    for row in record["observations"]:
        if row["operation"] != "standalone_lint":
            continue
        output = json.loads(row["output_text"])
        output["operation_result"] = {"report": output["operation_result"], "returncode": 0}
        row["output_text"] = json.dumps(output)
        row["output_sha256"] = text_sha256(row["output_text"])
        output["root"] = "<owned-fixture-root>/file.py"
        phase = output["operation_result"]["report"]["knowledge_summary"]["phase_durations_ms"]
        for key in phase:
            phase[key] = "<declared-volatile-duration>"
        row["logical_sha256"] = record_sha256(output)
    assert score(plan, record, replace(repin(record, pins), plan_sha256=record_sha256(plan))).maintenance_gain


@pytest.mark.parametrize("malformed", [None, 1, "control", {}, {"name": ["receiving"]}, {"name": {"nested": True}}])
def test_malformed_control_entry_fails_inspection_without_typeerror(malformed: Any) -> None:
    plan, record, pins = sample()
    record["controls"]["C1"][0] = malformed
    report = inspect_experiment(plan, record, expected=repin(record, pins))
    assert not report.checks["C1_controls"]
    assert not maintenance_gate(report).eligible


@pytest.mark.parametrize("malformed", [None, 1, "controls", {}])
def test_malformed_control_collection_fails_inspection_without_typeerror(malformed: Any) -> None:
    plan, record, pins = sample()
    record["controls"]["C1"] = malformed
    report = inspect_experiment(plan, record, expected=repin(record, pins))
    assert not report.checks["C1_controls"]
    assert not maintenance_gate(report).eligible
