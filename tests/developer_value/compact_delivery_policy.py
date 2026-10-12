"""Prospective cohort policy scored from captured text, without default adoption."""

import json
from statistics import median

from .compact_experiment import record_sha256

POLICY_SCHEMA = "llm-wiki-compact-delivery-policy/v1"


def evaluate_cohort(pairs, *, policy, expected_captures):
    """Keep every eligible failure in the denominator; controls stay separate.

    Capture pins come from the controller, not token summaries in the records.
    Receiver/source correctness requires its separate canonical/oracle checks.
    """
    if policy.get("schema_version") != POLICY_SCHEMA:
        raise ValueError("Unknown delivery policy")
    case_ids = [case_id for case_id, _, _ in pairs]
    slots = {case_id + suffix for case_id in case_ids for suffix in (":v1", ":v2")}
    if len(set(case_ids)) != len(case_ids) or set(expected_captures) != slots:
        raise ValueError("Complete unique controller-pinned cases are required")
    if any(candidate.get("role") != incumbent.get("role")
           or candidate.get("role") not in ("eligible", "control")
           for _, candidate, incumbent in pairs):
        raise ValueError("Paired frozen roles must agree")

    def count(text):
        return (len(text.encode("utf-8")) + 3) // 4

    def wire(value):
        return json.dumps(value, ensure_ascii=False, sort_keys=True)

    def metrics(value):
        return {
            "body": count(value["body"]),
            "canonical_body": count(value["canonical"]),
            "first_use_sdk": count(wire(value["sdk"])) + count(wire(value["setup"])),
            "canonical_first_use_sdk": count(wire(value["canonical_sdk"])) + count(wire(value["canonical_setup"])),
            **{key: count(wire(value[key])) for key in
               ("unchanged_sdk", "changed_sdk", "lost_sdk")},
        }

    rows, controls = [], []
    for case_id, candidate, incumbent in pairs:
        pinned = (record_sha256(candidate) == expected_captures.get(case_id + ":v2")
                  and record_sha256(incumbent) == expected_captures.get(case_id + ":v1"))
        if candidate["role"] != "eligible":
            controls.append({"case": case_id, "status": candidate["status"], "pinned": pinned})
            continue
        success = candidate["status"] == incumbent["status"] == "success"
        row = {"case": case_id, "success": success, "pinned": pinned}
        if success:
            current, previous = metrics(candidate), metrics(incumbent)
            checks = {
                "source_preserved": candidate.get("source_unchanged") is True,
                "body_cap": current["body"] <= policy["allocation_tokens"],
                "sdk_cap": current["first_use_sdk"] <= policy["allocation_tokens"],
                "body_nonregression": current["body"] <= current["canonical_body"],
                "sdk_nonregression": current["first_use_sdk"] <= current["canonical_first_use_sdk"],
                "warm_body": current["body"] <= previous["body"] * policy["warm_body_ratio_max"],
                "warm_unchanged": current["unchanged_sdk"] <= previous["unchanged_sdk"],
                "warm_changed": current["changed_sdk"] <= previous["changed_sdk"] * policy["warm_sdk_ratio_max"],
                "warm_lost": current["lost_sdk"] <= previous["lost_sdk"] * policy["warm_sdk_ratio_max"],
                "read_latency": candidate["read_ns"] <= max(
                    incumbent["read_ns"] * policy["read_ratio_max"],
                    incumbent["read_ns"] + policy["read_overhead_ns_max"]),
            }
            row.update(metrics=current, checks=checks,
                       body_saving=1 - current["body"] / current["canonical_body"],
                       sdk_saving=1 - current["first_use_sdk"] / current["canonical_first_use_sdk"])
        else:
            row.update(metrics=None, checks={"successful_delivery": False})
        rows.append(row)
    complete = len(rows) == policy["eligible_cases"] and all(row["success"] for row in rows)
    body_median = median(row["body_saving"] for row in rows) if complete else None
    sdk_median = median(row["sdk_saving"] for row in rows) if complete else None
    qualified = (complete and all(row["pinned"] and all(row["checks"].values()) for row in rows)
                 and len(controls) == policy["control_cases"] and all(row["pinned"] for row in controls)
                 and body_median >= policy["median_saving_min"]
                 and sdk_median >= policy["median_saving_min"])
    return {"qualified": qualified, "rows": rows, "controls": controls,
            "successful": sum(row["success"] for row in rows), "total": len(rows),
            "body_saving_median": body_median, "sdk_saving_median": sdk_median,
            "default_adoption": False, "model_productivity_claim": False}
