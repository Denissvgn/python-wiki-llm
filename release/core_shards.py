"""Content-bound file sharding and complete logical core-lane evidence.

These helpers do not authorize a qualifying producer or a rollout. The shadow
workflow uses them to establish equivalence before changing release execution.
"""

from __future__ import annotations

from collections import Counter
from copy import deepcopy
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import statistics
from typing import Any
import xml.etree.ElementTree as ET

_spec = importlib.util.spec_from_file_location(
    "_core_qualification", Path(__file__).with_name("qualification.py")
)
assert _spec is not None and _spec.loader is not None
q = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(q)

PLAN_SCHEMA = "agent-wiki-core-shard-plan/v2"
EXECUTION_SCHEMA = "agent-wiki-core-shard-execution/v2"
HISTORY_SCHEMA = "agent-wiki-core-shard-timings/v1"
PLANNER = "file-lpt-ms-v1"
ENVIRONMENT_POLICY = "exact-profile-with-recorded-runner-image/v1"
FLAGS = [
    "-q",
    "-p",
    "no:cacheprovider",
    "--strict-config",
    "--strict-markers",
    "-W",
    "error",
    "-o",
    "xfail_strict=true",
]
PROFILES = {
    "core-ubuntu-3.10": {"os": "ubuntu-24.04", "python": "3.10", "coverage": True},
    "core-windows-3.13": {"os": "windows-2025", "python": "3.13", "coverage": False},
    "core-macos-3.14": {"os": "macos-15", "python": "3.14", "coverage": False},
}
MAX_JSON = 32 * 1024 * 1024


def require(condition: bool, message: str) -> None:
    if not condition:
        raise q.QualificationError(message)


def digest(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(
            value, sort_keys=True, separators=(",", ":"), allow_nan=False
        ).encode()
    ).hexdigest()


def read(path: Path) -> Any:
    require(
        not path.is_symlink() and path.stat().st_size <= MAX_JSON,
        f"unsafe or oversized evidence: {path.name}",
    )
    return q.load_json(path)


def fields(value: Any, names: set[str], label: str) -> None:
    require(isinstance(value, dict) and set(value) == names, f"invalid {label} fields")


def positive(value: Any, label: str) -> None:
    require(type(value) is int and value > 0, f"invalid {label}")


def duration(value: Any) -> None:
    require(
        type(value) in (int, float) and math.isfinite(value) and value >= 0,
        "invalid execution duration",
    )


def profile(lane: str) -> dict:
    require(isinstance(lane, str) and lane in PROFILES, "unknown core lane")
    return {
        "lane": lane,
        **PROFILES[lane],
        "extras": ["dev", "tokens"],
        "install": "noneditable",
        "pytest_flags": FLAGS,
    }


def validate_environment(value: Any, lane: str) -> None:
    fields(
        value,
        {"profile", "python", "machine", "runner_image", "packages"},
        "environment",
    )
    require(value["profile"] == profile(lane), "core environment profile differs")
    require(
        isinstance(value["python"], str)
        and value["python"].startswith(PROFILES[lane]["python"] + "."),
        "core interpreter differs",
    )
    for name in ("machine", "runner_image"):
        require(
            isinstance(value[name], str) and bool(value[name].strip()),
            f"invalid {name}",
        )
    packages = value["packages"]
    require(
        isinstance(packages, dict)
        and {"agent-wiki-cli", "pytest", "pytest-cov", "coverage", "tokenizers"}
        <= packages.keys()
        and "mcp" not in packages,
        "core dependency profile differs",
    )
    require(
        all(
            isinstance(k, str) and k and isinstance(v, str) and v
            for k, v in packages.items()
        ),
        "invalid package versions",
    )


def validate_context(value: Any) -> None:
    fields(
        value,
        {"identity", "harness_sha256", "run_id", "run_attempt", "environment"},
        "execution context",
    )
    q._validate_identity(value["identity"])
    require(
        value["identity"]["mode"] == "candidate",
        "core shards require candidate identity",
    )
    q._require_sha256(value["harness_sha256"], "harness digest")
    positive(value["run_id"], "run ID")
    positive(value["run_attempt"], "run attempt")
    environment = value["environment"]
    require(
        isinstance(environment, dict) and isinstance(environment.get("profile"), dict),
        "invalid environment",
    )
    validate_environment(environment, environment["profile"].get("lane"))
    require(
        environment["packages"]["agent-wiki-cli"] == value["identity"]["version"],
        "installed provider version differs from candidate identity",
    )


def compatible_context(expected: dict, observed: dict) -> None:
    """Match execution inputs while retaining hosted image builds as provenance.

    A hosted OS label can schedule different image revisions in the same run.
    Every actual revision remains in its original receipt. Source, run, flags,
    OS profile, architecture, interpreter and resolved packages must still match.
    """
    validate_context(expected)
    validate_context(observed)
    changed = [
        name
        for name in expected
        if name != "environment" and digest(expected[name]) != digest(observed[name])
    ]
    changed.extend(
        "environment." + name
        for name in expected["environment"]
        if name != "runner_image"
        and digest(expected["environment"][name])
        != digest(observed["environment"][name])
    )
    require(not changed, "shard context differs: " + ", ".join(sorted(changed)))


def inventory(nodes: Any) -> list[str]:
    require(
        isinstance(nodes, list)
        and 0 < len(nodes) <= 100_000
        and all(isinstance(node, str) for node in nodes),
        "invalid collected inventory",
    )
    require(len(nodes) == len(set(nodes)), "duplicate collected node")
    for node in nodes:
        q._canonical_junit_selector(node)
        require(node.startswith("tests/") and "::" in node, "invalid core node")
    return sorted(nodes)


def file_name(node: str) -> str:
    return node.partition("::")[0]


def partition(nodes: list[str], weights: dict[str, int], count: int) -> list[dict]:
    positive(count, "shard count")
    files = sorted({file_name(node) for node in nodes})
    require(
        2 <= count <= min(4, len(files)),
        "core shard count must be 2–4 with no empty shards",
    )
    require(
        set(weights) == set(files),
        "timing weights must cover the current files exactly",
    )
    for weight in weights.values():
        positive(weight, "file weight")
    shards: list[dict] = [
        {"index": i, "files": [], "nodes": [], "estimated_ms": 0} for i in range(count)
    ]
    for name in sorted(files, key=lambda name: (-weights[name], name)):
        shard = min(shards, key=lambda row: (row["estimated_ms"], row["index"]))
        shard["files"].append(name)
        shard["estimated_ms"] += weights[name]
    for shard in shards:
        shard["files"].sort()
        selected = set(shard["files"])
        shard["nodes"] = [node for node in nodes if file_name(node) in selected]
    return shards


def plan(
    nodes: list[str], context: dict, count: int, history: dict | None = None
) -> dict:
    validate_context(context)
    nodes = inventory(nodes)
    files = sorted({file_name(node) for node in nodes})
    timings = {}
    if history is not None:
        fields(
            history,
            {"schema_version", "source_sha", "run_id", "run_attempt", "lanes"},
            "timing history",
        )
        require(
            history["schema_version"] == HISTORY_SCHEMA, "unsupported timing history"
        )
        q._require_sha(history["source_sha"], "history source")
        positive(history["run_id"], "history run ID")
        positive(history["run_attempt"], "history attempt")
        require(isinstance(history["lanes"], dict), "invalid history lanes")
        lane = context["environment"]["profile"]["lane"]
        previous = history["lanes"].get(lane)
        if previous is not None:
            fields(previous, {"profile", "files_ms"}, "lane timings")
            require(isinstance(previous["files_ms"], dict), "invalid file timings")
            for name, weight in previous["files_ms"].items():
                q._canonical_junit_selector(name)
                require(
                    name.startswith("tests/") and "::" not in name,
                    "invalid timing file",
                )
                positive(weight, "historical file weight")
            # Old timing affects balance only. A stale profile or deleted file
            # never changes collection or eligibility of any current test.
            if previous["profile"] == context["environment"]["profile"]:
                timings = {
                    name: weight
                    for name, weight in previous["files_ms"].items()
                    if name in files
                }
    fallback = max(1, int(statistics.median(timings.values()))) if timings else 1000
    weights = {name: timings.get(name, fallback) for name in files}
    return {
        "schema_version": PLAN_SCHEMA,
        "planner": PLANNER,
        "environment_policy": ENVIRONMENT_POLICY,
        "purpose": "shadow",
        "qualifying": False,
        "context": deepcopy(context),
        "inventory": nodes,
        "inventory_sha256": digest(nodes),
        "history_sha256": digest(history),
        "history_files_used": sorted(timings),
        "fallback_ms": fallback,
        "weights_ms": weights,
        "shard_count": count,
        "shards": partition(nodes, weights, count),
    }


def validate_plan(value: Any, context: dict | None = None) -> dict:
    fields(
        value,
        {
            "schema_version",
            "planner",
            "environment_policy",
            "purpose",
            "qualifying",
            "context",
            "inventory",
            "inventory_sha256",
            "history_sha256",
            "history_files_used",
            "fallback_ms",
            "weights_ms",
            "shard_count",
            "shards",
        },
        "shard plan",
    )
    require(
        value["schema_version"] == PLAN_SCHEMA
        and value["planner"] == PLANNER
        and value["environment_policy"] == ENVIRONMENT_POLICY
        and value["purpose"] == "shadow"
        and value["qualifying"] is False,
        "unsupported or qualifying shard plan",
    )
    validate_context(value["context"])
    if context is not None:
        compatible_context(value["context"], context)
    nodes = inventory(value["inventory"])
    require(
        nodes == value["inventory"] and digest(nodes) == value["inventory_sha256"],
        "plan inventory differs",
    )
    q._require_sha256(value["history_sha256"], "timing history digest")
    positive(value["fallback_ms"], "fallback weight")
    require(isinstance(value["weights_ms"], dict), "invalid plan weights")
    used = value["history_files_used"]
    require(
        isinstance(used, list)
        and all(isinstance(name, str) for name in used)
        and used == sorted(set(used))
        and set(used) <= set(value["weights_ms"]),
        "invalid timing membership",
    )
    require(isinstance(value["shards"], list), "invalid shard records")
    for index, shard in enumerate(value["shards"]):
        fields(shard, {"index", "files", "nodes", "estimated_ms"}, "shard record")
        require(
            type(shard["index"]) is int and shard["index"] == index,
            "invalid shard index",
        )
        positive(shard["estimated_ms"], "estimated shard weight")
    require(
        value["shards"] == partition(nodes, value["weights_ms"], value["shard_count"]),
        "shards differ from deterministic complete file partition",
    )
    return value


def junit(path: Path) -> dict[str, ET.Element]:
    require(
        not path.is_symlink() and path.stat().st_size <= MAX_JSON,
        "unsafe or oversized JUnit",
    )
    raw = path.read_bytes().decode("utf-8-sig")
    require(
        "<!DOCTYPE" not in raw and "<!ENTITY" not in raw,
        "JUnit declarations are forbidden",
    )
    root = ET.fromstring(raw)
    require(root.tag in {"testsuite", "testsuites"}, "invalid JUnit root")
    result = {}
    for case in root.iter("testcase"):
        node = q._node_id(case)
        require(node not in result, f"duplicate JUnit node: {node}")
        inventory([node])
        require(
            sum(case.find(kind) is not None for kind in ("failure", "error", "skipped"))
            <= 1,
            "contradictory JUnit outcomes",
        )
        if "time" in case.attrib:
            duration(float(case.attrib["time"]))
        result[node] = case
    require(bool(result), "empty JUnit inventory")
    for suite in root.iter():
        if suite.tag in {"testsuite", "testsuites"}:
            cases = list(suite.iter("testcase"))
            for key, observed in (
                ("tests", len(cases)),
                ("failures", sum(c.find("failure") is not None for c in cases)),
                ("errors", sum(c.find("error") is not None for c in cases)),
                ("skipped", sum(c.find("skipped") is not None for c in cases)),
            ):
                if key in suite.attrib:
                    require(
                        int(suite.attrib[key]) == observed,
                        f"JUnit {key} counter differs",
                    )
    return result


def outcomes(cases: dict[str, ET.Element]) -> dict:
    result = {}
    for node, case in cases.items():
        skip = case.find("skipped")
        status = next(
            (
                kind
                for kind in ("failure", "error", "skipped")
                if case.find(kind) is not None
            ),
            "passed",
        )
        result[node] = {
            "outcome": status,
            "reason": ""
            if skip is None
            else skip.get("message") or (skip.text or "").strip(),
        }
    return result


def validate_execution(directory: Path, value: dict, index: int | None) -> dict:
    validate_plan(value)
    receipt = read(directory / "execution.json")
    fields(
        receipt,
        {
            "schema_version",
            "purpose",
            "qualifying",
            "complete",
            "plan_sha256",
            "context",
            "index",
            "exit_code",
            "seconds",
            "files",
            "error",
        },
        "shard execution",
    )
    require(
        receipt["schema_version"] == EXECUTION_SCHEMA
        and receipt["purpose"] == "shadow"
        and receipt["qualifying"] is False
        and receipt["complete"] is True,
        "incomplete or qualifying shard",
    )
    require(
        type(receipt["index"]) is type(index) and receipt["index"] == index,
        "shard index differs",
    )
    require(
        type(receipt["exit_code"]) is int
        and receipt["exit_code"] == 0
        and receipt["error"] is None,
        "shard failed or was cancelled",
    )
    require(
        receipt["plan_sha256"] == digest(value),
        "shard plan digest differs",
    )
    compatible_context(value["context"], receipt["context"])
    duration(receipt["seconds"])
    required = {
        "collected.json",
        "selected.json",
        "started.jsonl",
        "junit.xml",
        "worker.log",
    }
    if value["context"]["environment"]["profile"]["coverage"]:
        required |= {"coverage.data", "coverage.json"}
    require(
        isinstance(receipt["files"], dict) and set(receipt["files"]) == required,
        "shard evidence membership differs",
    )
    for name, sha in receipt["files"].items():
        q._require_sha256(sha, "shard file digest")
        require(
            not (directory / name).is_symlink()
            and q.sha256_file(directory / name) == sha,
            f"shard evidence differs: {name}",
        )
    expected = value["inventory"] if index is None else value["shards"][index]["nodes"]
    require(
        read(directory / "collected.json") == value["inventory"],
        "worker full collection differs",
    )
    require(read(directory / "selected.json") == expected, "worker selection differs")
    started_path = directory / "started.jsonl"
    require(started_path.stat().st_size <= MAX_JSON, "oversized started inventory")
    started = [
        json.loads(line)
        for line in started_path.read_text(encoding="utf-8").splitlines()
    ]
    require(
        Counter(started) == Counter(expected),
        "missing, duplicate or extra started node",
    )
    cases = junit(directory / "junit.xml")
    require(set(cases) == set(expected), "shard JUnit inventory differs")
    require(
        all(
            row["outcome"] in {"passed", "skipped"} for row in outcomes(cases).values()
        ),
        "shard has failing outcomes",
    )
    return receipt


def merge_junit(value: dict, directories: list[Path], output: Path) -> dict:
    validate_plan(value)
    require(
        len(directories) == value["shard_count"]
        and len(set(map(str, directories))) == len(directories),
        "missing or repeated shard directories",
    )
    cases: dict[str, ET.Element] = {}
    indices = set()
    receipts = []
    for directory in directories:
        index = read(directory / "execution.json").get("index")
        require(
            type(index) is int
            and 0 <= index < value["shard_count"]
            and index not in indices,
            "missing, extra or duplicate shard index",
        )
        indices.add(index)
        receipts.append(validate_execution(directory, value, index))
        current = junit(directory / "junit.xml")
        require(not set(cases).intersection(current), "overlapping shard JUnit")
        cases.update(current)
    require(set(cases) == set(value["inventory"]), "aggregate inventory is incomplete")
    suite = ET.Element(
        "testsuite",
        name=value["context"]["environment"]["profile"]["lane"],
        tests=str(len(cases)),
        failures="0",
        errors="0",
        skipped=str(sum(case.find("skipped") is not None for case in cases.values())),
    )
    for node in sorted(cases):
        suite.append(deepcopy(cases[node]))
    output.parent.mkdir(parents=True, exist_ok=True)
    require(not output.exists(), "aggregate JUnit must be new")
    ET.ElementTree(suite).write(output, encoding="utf-8", xml_declaration=True)
    return {"receipts": receipts, "outcomes": outcomes(cases)}
