"""Authenticate provisional finding, measurement and adoption dispositions.

Artifact commitments, live producer identities and a frozen reviewed claim
contract come from a separate controller. Hashes authenticate that review; they
do not establish semantic correctness. This guard never reruns a provider,
infers human acceptance, or makes a historical observation current.
"""

from __future__ import annotations

from collections.abc import Mapping
from hashlib import sha256
import json
import math
from pathlib import PurePosixPath
from typing import Any, TypeGuard

SCHEMA = "developer-value-reconciliation/v1"
CONTRACT_SCHEMA = "developer-value-reconciliation-contract/v1"
ORIGINAL_REQUIREMENTS = frozenset(f"DV{i:02d}" for i in range(27))
RECORD_FIELDS = frozenset({
    "schema_version", "provisional", "final_closure", "current_sources", "evidence",
    "findings", "tasks", "original_requirements", "claim_limits", "historical_limits",
    "amendments", "generated_trace_passed", "combined_limits", "measurements", "adoptions",
    "review_method", "input_revision", "input_tree",
})
MEASUREMENT_FIELDS = frozenset({
    "id", "scope", "restriction", "evidence", "producer_identity_evidence", "producer_sources",
    "applicability", "current_performance_claim", "observations_reexecuted",
})
FINDINGS = frozenset({"R1", "R2", "R3", "R4", "R5", "G1", "G2", "G3", "G4"})
TASKS = frozenset(f"AF{i:02d}" for i in range(25))
FUTURE = frozenset({"AF21", "AF22", "AF23", "AF24"})
DISPOSITIONS = {
    "R1": "fixed-scoped",
    "R2": "fixed-scoped",
    "R3": "prospective-gate-established-restricted",
    "R4": "pending-substitution-integration",
    "R5": "pending-maintained-integration",
    "G1": "mitigated-source-companion-draft",
    "G2": "evaluated-no-gain",
    "G3": "evaluated-no-gain",
    "G4": "evaluated-no-gain",
}
UNMEASURED = {
    "model_productivity": "unmeasured",
    "human_acceptance": "unmeasured",
    "runtime_equivalence": "unestablished",
    "historical_guide_cost": "unavailable",
    "generated_real_trace": "mitigated/not-met",
}
ADOPTIONS = frozenset({"search", "compact", "packed-optimization", "ordinary-review"})


def _records(value: Any, name: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping) or any(not isinstance(k, str) for k in value):
        raise ValueError(f"{name} must be a mapping")
    return value


def _text(value: Any) -> TypeGuard[str]:
    return isinstance(value, str) and bool(value.strip())


def _digest(value: Any) -> TypeGuard[str]:
    return isinstance(value, str) and len(value) == 64 and all(c in "0123456789abcdef" for c in value)


def _pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Duplicate JSON key")
        result[key] = value
    return result


def _constant(value: str) -> Any:
    raise ValueError(f"Nonfinite JSON value: {value}")


def _float(value: str) -> float:
    result = float(value)
    if not math.isfinite(result):
        raise ValueError("Nonfinite JSON number")
    return result


def _json(data: bytes) -> Any:
    try:
        return json.loads(data.decode("utf-8"), object_pairs_hook=_pairs,
                          parse_constant=_constant, parse_float=_float)
    except (UnicodeError, json.JSONDecodeError) as error:
        raise ValueError("Invalid strict JSON") from error


def _same(left: Any, right: Any) -> bool:
    """JSON equality without Python's bool/int or float/int coercion."""
    if isinstance(left, Mapping) and isinstance(right, Mapping):
        return set(left) == set(right) and all(_same(left[k], right[k]) for k in left)
    if type(left) is not type(right):
        return False
    if isinstance(left, list):
        return len(left) == len(right) and all(_same(a, b) for a, b in zip(left, right))
    return left == right


def _pointer(payload: Any, pointer: Any) -> Any:
    """Resolve an exact RFC 6901 pointer, including escaped keys and arrays."""
    if not isinstance(pointer, str) or (pointer and not pointer.startswith("/")):
        raise ValueError("Invalid measurement profile pointer")
    if not pointer:
        return payload
    for token in pointer[1:].split("/"):
        index = 0
        while index < len(token):
            if token[index] == "~":
                if index + 1 == len(token) or token[index + 1] not in "01":
                    raise ValueError("Invalid measurement profile pointer escape")
                index += 1
            index += 1
        token = token.replace("~1", "/").replace("~0", "~")
        if isinstance(payload, Mapping) and token in payload:
            payload = payload[token]
        elif isinstance(payload, list) and token.isascii() and token.isdecimal():
            if (len(token) > 1 and token.startswith("0")) or int(token) >= len(payload):
                raise ValueError("Missing measurement profile pointer")
            payload = payload[int(token)]
        else:
            raise ValueError("Missing measurement profile pointer")
    return payload


def validate_reconciliation(
    record: Mapping[str, Any],
    *,
    trusted_artifacts: Mapping[str, str],
    artifact_bytes: Mapping[str, bytes],
    current_sources: Mapping[str, str],
    contract_bytes: bytes,
    expected_contract_sha256: str,
) -> dict[str, Any]:
    """Bind claims to independent review and raw lineage, then check fixed gates.

    The controller supplies the expected contract digest independently of this
    record. A changed policy requires a new controller pin and source review;
    candidate-authored flags or a digest carried in the record confer no trust.
    """
    record = _records(record, "reconciliation")
    if (not isinstance(contract_bytes, bytes) or not _digest(expected_contract_sha256)
            or sha256(contract_bytes).hexdigest() != expected_contract_sha256):
        raise ValueError("Independent claim contract commitment mismatch")
    contract = _records(_json(contract_bytes), "claim contract")
    if contract.get("schema_version") != CONTRACT_SCHEMA:
        raise ValueError("Unsupported claim contract schema")
    if record.get("schema_version") != SCHEMA:
        raise ValueError("Unsupported reconciliation schema")
    if set(record) - RECORD_FIELDS:
        raise ValueError("Unsupported reconciliation fields")
    if record.get("provisional") is not True or record.get("final_closure") is not False:
        raise ValueError("Reconciliation must remain provisional")
    if _records(record.get("claim_limits"), "claim_limits") != UNMEASURED:
        raise ValueError("Unmeasured claims cannot receive acceptance")
    sources = _records(record.get("current_sources"), "current_sources")
    if not current_sources or sources != current_sources or not all(_digest(h) for h in sources.values()):
        raise ValueError("Current source identity mismatch")

    evidence = _records(record.get("evidence"), "evidence")
    payloads: dict[str, Any] = {}
    for identity, raw in evidence.items():
        item = _records(raw, f"evidence {identity}")
        path, pin = item.get("path"), item.get("sha256")
        if not _text(path) or PurePosixPath(path).is_absolute() or ".." in PurePosixPath(path).parts:
            raise ValueError("Evidence path must be repository-relative")
        if not _digest(pin) or trusted_artifacts.get(path) != pin:
            raise ValueError("Independent artifact commitment mismatch")
        data = artifact_bytes.get(path)
        if not isinstance(data, bytes) or sha256(data).hexdigest() != pin:
            raise ValueError("Artifact bytes mismatch")
        if item.get("format") == "json":
            payloads[identity] = _json(data)
        elif item.get("format") != "bytes":
            raise ValueError("Unsupported artifact format")

    def refs(value: Any) -> None:
        if (not isinstance(value, list) or not value
                or any(not isinstance(v, str) or v not in evidence for v in value)
                or len(set(value)) != len(value)):
            raise ValueError("Every disposition needs authenticated evidence")

    findings = _records(record.get("findings"), "findings")
    if set(findings) != FINDINGS:
        raise ValueError("Every original finding needs a disposition")
    for identity, raw in findings.items():
        row = _records(raw, identity)
        if row.get("status") != DISPOSITIONS[identity] or not _text(row.get("original_claim")):
            raise ValueError("Unsupported finding disposition")
        refs(row.get("evidence"))
        if not isinstance(row.get("limits"), list) or not row["limits"]:
            raise ValueError("Finding scope limits are required")
        owners = row.get("tasks")
        if (not isinstance(owners, list) or not owners
                or any(not isinstance(v, str) or v not in TASKS for v in owners)):
            raise ValueError("Finding task ownership is required")

    caller = _records(payloads.get("caller-current"), "caller-current")
    binding = "src/llm_wiki_cli/extractors/python_bindings.py"
    if caller.get("reviewed_binding_sha256") != sources.get(binding):
        raise ValueError("Caller evidence has a different producer")
    if caller.get("required_repairs_remaining") != []:
        raise ValueError("Caller repairs remain")
    counts = _records(caller.get("results"), "caller results")
    expected = ("applicable_controls", "applicable_passes", "receiving_consistent_readonly", "valid_public_facts")
    if any(type(counts.get(k)) is not int or counts[k] <= 0 for k in expected):
        raise ValueError("Caller positive, negative and receiving evidence required")
    if (counts["applicable_controls"] != counts["applicable_passes"]
            or counts["receiving_consistent_readonly"] != counts["valid_public_facts"]
            or type(counts.get("applicable_failures")) is not int or counts["applicable_failures"] != 0
            or type(counts.get("private_binding_keys")) is not int or counts["private_binding_keys"] != 0):
        raise ValueError("Caller correctness gate failed")
    if any("caller-current" not in findings[k]["evidence"] for k in ("R1", "R2")):
        raise ValueError("Caller findings need current evidence")

    triage = _records(payloads.get("triage-prospective"), "triage-prospective")
    if triage.get("passed") is not True or triage.get("issues") != []:
        raise ValueError("Prospective triage gate missing or failed")
    splits = _records(triage.get("splits"), "triage splits")
    for split in ("development", "confirmation"):
        score = _records(splits.get(split), split)
        keys = ("actionable", "denominator", "covered_count", "required_count")
        if any(type(score.get(k)) is not int or score[k] <= 0 for k in keys):
            raise ValueError("Prospective triage denominators missing")
        if not 0 <= score["actionable"] <= score["denominator"] or 5 * score["actionable"] < 4 * score["denominator"]:
            raise ValueError("Prospective actionability below fixed threshold")
        if score["covered_count"] != score["required_count"]:
            raise ValueError("Required change coverage incomplete")
    if "triage-prospective" not in findings["R3"]["evidence"]:
        raise ValueError("R3 requires prospective evidence")
    history = _records(record.get("historical_limits"), "historical_limits")
    if (history.get("original_triage") != "historical-unmeasured"
            or history.get("retrospective_is_prospective") is not False
            or history.get("historical_cost_recovered") is not False
            or history.get("current_producer_triage_measurement") != "not-claimed"):
        raise ValueError("Historical evidence was promoted")

    tasks = _records(record.get("tasks"), "tasks")
    if set(tasks) != TASKS:
        raise ValueError("Every mandatory task needs a disposition")
    for identity, raw in tasks.items():
        task = _records(raw, identity)
        if task.get("required") is not True:
            raise ValueError("Mandatory task cannot become optional")
        if identity in FUTURE:
            if task.get("status") != "pending" or not _text(task.get("remaining")):
                raise ValueError("Future integration and final checks remain pending")
        elif identity == "AF20":
            if task.get("status") != "validating":
                raise ValueError("Record itself does not close the task")
        else:
            if task.get("status") != "done":
                raise ValueError("Prerequisite work is incomplete")
            refs(task.get("evidence"))

    amendments = _records(record.get("amendments"), "amendments")
    if (amendments.get("A1") != "pending-integration-cost"
            or amendments.get("A2") != "source-companion-draft-only"):
        raise ValueError("Substitution prematurely closed")
    if record.get("generated_trace_passed") is not False:
        raise ValueError("Companion cannot pass generated trace")
    legacy = _records(record.get("combined_limits"), "combined_limits")
    if legacy != {"required": 8, "surfaced": 7, "missed_unsolved": 1, "unknown_rows": 143, "uninvoked": 4}:
        raise ValueError("Combined unavailable work cannot earn acceptance")

    measurements = record.get("measurements")
    if not isinstance(measurements, list) or not measurements:
        raise ValueError("Older measurements need explicit dispositions")
    for raw in measurements:
        item = _records(raw, "measurement")
        if set(item) != MEASUREMENT_FIELDS:
            raise ValueError("Measurement fields must match the closed schema")
        if item.get("observations_reexecuted") is not False:
            raise ValueError("Historical observations must remain unreexecuted")
        refs(item.get("evidence"))
        pins = _records(item.get("producer_sources"), "measurement producer")
        if not pins or not all(_digest(h) for h in pins.values()):
            raise ValueError("Measured producer identity required")
        if item.get("applicability") != "historical-pinned-treatment" or item.get("current_performance_claim") is not False:
            raise ValueError("Old measurements cannot describe current performance")
        if not _text(item.get("scope")) or not _text(item.get("restriction")):
            raise ValueError("Comparable measurement scope and restriction required")

    adoptions = _records(record.get("adoptions"), "adoptions")
    if set(adoptions) != ADOPTIONS:
        raise ValueError("Every default/adoption decision needs a disposition")
    for raw in adoptions.values():
        item = _records(raw, "adoption")
        refs(item.get("evidence"))
        if item.get("decision") != "retain-shipped-contract" or item.get("new_prototype_adopted") is not False:
            raise ValueError("Benefit misses cannot justify new adoption")
        if not _text(item.get("default")):
            raise ValueError("Current default must be explicit")

    # Exact reviewed machine rows and prose bind each role and claim surface.
    # This is review authentication, not an automated interpretation of prose.
    for name in ("findings", "tasks", "adoptions", "claim_limits", "historical_limits",
                 "amendments", "combined_limits", "generated_trace_passed",
                 "review_method", "input_revision", "input_tree"):
        if name not in contract or not _same(record.get(name), contract[name]):
            raise ValueError(f"Reviewed claim contract mismatch: {name}")
    if not _same(evidence, _records(contract.get("evidence_roles"), "contract evidence_roles")):
        raise ValueError("Reviewed evidence role mismatch")

    for identity, task in tasks.items():
        if identity == "AF20" or identity in FUTURE:
            continue
        role = f"task-{identity}"
        if role not in task["evidence"]:
            raise ValueError("Completed task requires its own delivery role")
        delivery = _records(payloads.get(role), role)
        commit = delivery.get("output_commit", delivery.get("commit"))
        if (delivery.get("task") != identity or not _text(commit)
                or commit != task.get("output_commit")):
            raise ValueError("Task delivery identity/commit mismatch")
        for source, target in (("status", "status"), ("outcome", "work_outcome")):
            if source in delivery and not _same(delivery[source], task.get(target)):
                raise ValueError("Task delivery status/outcome mismatch")

    originals = _records(record.get("original_requirements"), "original_requirements")
    reviewed = _records(contract.get("original_requirements"), "contract original_requirements")
    if set(originals) != ORIGINAL_REQUIREMENTS or set(reviewed) != ORIGINAL_REQUIREMENTS:
        raise ValueError("Every original requirement needs a reviewed disposition")
    original_state = _records(payloads.get("original-state"), "original-state")
    original_tasks = _records(original_state.get("tasks"), "original tasks")
    if {k for k in original_tasks if k.startswith("DV")} != ORIGINAL_REQUIREMENTS:
        raise ValueError("Original state requirement coverage mismatch")
    for identity, raw in originals.items():
        row = _records(raw, identity)
        original = _records(original_tasks[identity], f"original {identity}")
        refs(row.get("evidence"))
        if "original-state" not in row["evidence"]:
            raise ValueError("Original requirement needs original-state evidence")
        affected = row.get("affected_findings")
        if (not isinstance(affected, list)
                or any(not isinstance(v, str) or v not in FINDINGS for v in affected)):
            raise ValueError("Original requirement finding association mismatch")
        for field, source in (("title", "title"), ("original_recorded_status", "status"),
                              ("original_output_commit", "output_commit")):
            if not _text(original.get(source)) or not _same(row.get(field), original[source]):
                raise ValueError("Original requirement metadata mismatch")
    if not _same(originals, reviewed):
        raise ValueError("Reviewed original requirement disposition mismatch")

    rules = _records(contract.get("measurement_rules"), "contract measurement_rules")
    if not rules:
        raise ValueError("Reviewed measurement rules required")
    identities: set[str] = set()
    for raw in measurements:
        item = _records(raw, "measurement")
        identity = item.get("id")
        if not _text(identity) or identity in identities or identity not in rules:
            raise ValueError("Unique reviewed measurement identity required")
        identities.add(identity)
        rule = _records(rules[identity], f"measurement rule {identity}")
        refs(rule.get("evidence"))
        if (not set(rule["evidence"]).issubset(item["evidence"])
                or any(not _text(rule.get(k)) or not _same(item.get(k), rule[k])
                       for k in ("scope", "restriction"))):
            raise ValueError("Reviewed measurement evidence/scope/restriction mismatch")
        profiles = rule.get("profiles")
        if not isinstance(profiles, list) or not profiles:
            raise ValueError("Measurement producer profiles required")
        derived: dict[str, str] = {}
        profile_ids: list[str] = []
        for raw_profile in profiles:
            profile = _records(raw_profile, "measurement profile")
            if set(profile) not in ({"evidence", "pointer", "prefix"},
                                    {"evidence", "pointer", "prefix", "hash_member"},
                                    {"evidence", "pointer", "prefix", "key"},
                                    {"evidence", "pointer", "prefix", "key", "strip_prefix"}):
                raise ValueError("Unsupported measurement profile fields")
            role, prefix = profile.get("evidence"), profile.get("prefix")
            if (not isinstance(role, str) or role not in payloads or not _text(prefix)
                    or role not in item["evidence"]):
                raise ValueError("Measurement producer profile evidence missing")
            if role not in profile_ids:
                profile_ids.append(role)
            value = _pointer(payloads[role], profile.get("pointer"))
            mapping: Mapping[str, Any]
            if "key" in profile:
                if "strip_prefix" in profile:
                    strip = profile["strip_prefix"]
                    if not _text(strip) or not isinstance(value, str) or not value.startswith(strip):
                        raise ValueError("Measurement leaf profile prefix mismatch")
                    value = value[len(strip):]
                if not _text(profile["key"]) or not _digest(value):
                    raise ValueError("Measurement leaf profile requires explicit key and digest")
                mapping = {profile["key"]: value}
            else:
                mapping = _records(value, "measurement source profile")
                if "hash_member" in profile:
                    member = profile["hash_member"]
                    if not _text(member):
                        raise ValueError("Measurement profile hash member must be explicit text")
                    mapping = {k: _records(v, "measurement source entry").get(member)
                               for k, v in mapping.items()}
            if not mapping or any(not _text(k) or not _digest(v) for k, v in mapping.items()):
                raise ValueError("Measurement profile must contain source digests")
            for key, pin in mapping.items():
                combined = prefix + ":" + key
                if combined in derived:
                    raise ValueError("Duplicate measurement producer source key")
                derived[combined] = pin
        if (not _same(item.get("producer_identity_evidence"), profile_ids)
                or not _same(item["producer_sources"], derived)):
            raise ValueError("Measurement producer lineage mismatch")
    if identities != set(rules):
        raise ValueError("Every reviewed measurement needs a disposition")
    return {"accepted": True, "provisional": True, "final_closure": False,
            "findings": len(findings), "mandatory_tasks": len(tasks),
            "authenticated_artifacts": len(evidence), "current_source_count": len(sources)}
