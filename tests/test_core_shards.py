"""Complete inventories and adversarial controls for core shard evidence."""

from copy import deepcopy
from pathlib import Path
import random
import json
import shutil
import xml.etree.ElementTree as ET

import pytest

from release import core_shards as s


def context(lane="core-ubuntu-3.10"):
    return {
        "identity": {
            "schema_version": s.q.IDENTITY_SCHEMA,
            "repository": "owned/repo",
            "source": {
                "sha": "a" * 40,
                "tree": "b" * 40,
                "archive_sha256": "c" * 64,
                "commit_epoch": 1,
            },
            "version": "1.0.0",
            "tag": "v1.0.0",
            "mode": "candidate",
        },
        "harness_sha256": "d" * 64,
        "run_id": 123,
        "run_attempt": 1,
        "environment": {
            "profile": s.profile(lane),
            "python": s.PROFILES[lane]["python"] + ".21",
            "machine": "owned",
            "runner_image": "owned-image",
            "packages": {
                "agent-wiki-cli": "1.0.0",
                "pytest": "9.0.0",
                "pytest-cov": "7.0.0",
                "coverage": "7.16.1",
                "tokenizers": "0.22.2",
            },
        },
    }


NODES = [
    "tests/test_one.py::test_a",
    "tests/test_one.py::test_b[x::y/[z]]",
    "tests/test_two.py::TestGroup::test_a",
    "tests/test_three.py::test_a",
    "tests/test_four.py::test_a",
]


def history():
    return {
        "schema_version": s.HISTORY_SCHEMA,
        "source_sha": "e" * 40,
        "run_id": 99,
        "run_attempt": 1,
        "lanes": {
            "core-ubuntu-3.10": {
                "profile": s.profile("core-ubuntu-3.10"),
                "files_ms": {
                    "tests/test_one.py": 12000,
                    "tests/test_two.py": 6000,
                    "tests/test_three.py": 4000,
                    "tests/test_removed.py": 100000,
                },
            }
        },
    }


def test_plan_is_reproducible_complete_and_balanced_at_file_boundaries():
    original = s.plan(NODES, context(), 2, history())
    assert s.validate_plan(original) == original
    for seed in range(15):
        reordered = list(NODES)
        random.Random(seed).shuffle(reordered)
        assert s.plan(reordered, context(), 2, history()) == original
    assert original["shards"][0]["files"] == [
        "tests/test_one.py",
        "tests/test_three.py",
    ]
    assert original["shards"][1]["files"] == ["tests/test_four.py", "tests/test_two.py"]
    assert original["fallback_ms"] == 6000
    assert sorted(
        node for shard in original["shards"] for node in shard["nodes"]
    ) == sorted(NODES)
    assert set(original["shards"][0]["files"]).isdisjoint(
        original["shards"][1]["files"]
    )
    assert "tests/test_removed.py" not in original["weights_ms"]


@pytest.mark.parametrize(
    "kind", ["absent", "missing-lane", "stale-profile", "deleted-files"]
)
def test_missing_or_stale_history_never_drops_current_nodes(kind):
    previous = history()
    if kind == "absent":
        previous = None
    elif kind == "missing-lane":
        previous["lanes"] = {}
    elif kind == "stale-profile":
        previous["lanes"]["core-ubuntu-3.10"]["profile"]["python"] = "3.9"
    else:
        previous["lanes"]["core-ubuntu-3.10"]["files_ms"] = {"tests/test_gone.py": 99}
    value = s.plan(NODES, context(), 2, previous)
    assert value["inventory"] == sorted(NODES)
    assert value["history_files_used"] == []
    assert set(value["weights_ms"].values()) == {1000}


@pytest.mark.parametrize("count", [True, 0, 1, 5, 2.0, "2"])
def test_invalid_shard_count_fails(count):
    with pytest.raises(s.q.QualificationError):
        s.plan(NODES, context(), count)


@pytest.mark.parametrize("weight", [True, 0, -1, float("nan"), float("inf"), 1.5, "12"])
def test_invalid_timing_data_fails(weight):
    previous = history()
    previous["lanes"]["core-ubuntu-3.10"]["files_ms"]["tests/test_one.py"] = weight
    with pytest.raises(s.q.QualificationError):
        s.plan(NODES, context(), 2, previous)


@pytest.mark.parametrize(
    "mutation",
    [
        "missing",
        "duplicate",
        "overlap",
        "split-file",
        "candidate",
        "run",
        "attempt",
        "environment",
        "planner",
        "digest",
        "qualifying",
        "unknown",
    ],
)
def test_invalid_or_stale_plans_fail_even_when_reserialized(mutation):
    expected = context()
    value = s.plan(NODES, expected, 2)
    if mutation == "missing":
        value["shards"].pop()
    elif mutation == "duplicate":
        value["inventory"].append(value["inventory"][0])
    elif mutation == "overlap":
        value["shards"][1]["nodes"].append(value["shards"][0]["nodes"][0])
    elif mutation == "split-file":
        node = "tests/test_one.py::test_a"
        origin = next(row for row in value["shards"] if node in row["nodes"])
        origin["nodes"].remove(node)
        value["shards"][1 - origin["index"]]["nodes"].append(node)
    elif mutation == "candidate":
        value["context"]["identity"]["source"]["sha"] = "f" * 40
    elif mutation in {"run", "attempt"}:
        value["context"]["run_id" if mutation == "run" else "run_attempt"] += 1
    elif mutation == "environment":
        value["context"]["environment"]["packages"]["pytest"] = "9.1.0"
    elif mutation == "planner":
        value["planner"] = "unreviewed"
    elif mutation == "digest":
        value["inventory_sha256"] = "0" * 64
    elif mutation == "qualifying":
        value["qualifying"] = True
    else:
        value["ignored"] = True
    with pytest.raises(s.q.QualificationError):
        s.validate_plan(value, expected)


def test_committed_timing_history_has_explicit_qualified_origin_and_all_profiles():
    value = s.read(Path(__file__).parents[1] / "release/core-shard-timings.json")
    assert value["source_sha"] == "4e0ccb95464cea205bab0258ce0fa8598c7c0dbf"
    assert value["run_id"] == 35923626375 and value["run_attempt"] == 1
    assert set(value["lanes"]) == set(s.PROFILES)
    for lane in s.PROFILES:
        current = context(lane)
        snapshot = deepcopy(value)
        result = s.plan(NODES, current, 2, value)
        assert result["inventory"] == sorted(NODES)
        assert value == snapshot


def write_junit(path, nodes, skip=None):
    suite = ET.Element(
        "testsuite",
        tests=str(len(nodes)),
        failures="0",
        errors="0",
        skipped=str(int(skip is not None)),
    )
    for node in nodes:
        file, _, tail = node.partition("::")
        base, bracket, parameter = tail.partition("[")
        cls, separator, method = base.rpartition("::")
        case = ET.SubElement(
            suite,
            "testcase",
            classname=file[:-3].replace("/", ".") + ("." + cls if separator else ""),
            name=(method if separator else base) + ("[" + parameter if bracket else ""),
            time="0.1",
        )
        if skip == node:
            ET.SubElement(case, "skipped", message="owned reason")
    ET.ElementTree(suite).write(path, encoding="utf-8")


def execution(directory, value, index, skip=None):
    directory.mkdir()
    nodes = value["inventory"] if index is None else value["shards"][index]["nodes"]
    s.q.write_json(directory / "collected.json", value["inventory"])
    s.q.write_json(directory / "selected.json", nodes)
    (directory / "started.jsonl").write_text(
        "".join(json.dumps(node) + "\n" for node in nodes)
    )
    (directory / "worker.log").write_text("owned worker\n")
    write_junit(directory / "junit.xml", nodes, skip=skip)
    receipt = {
        "schema_version": s.EXECUTION_SCHEMA,
        "purpose": "shadow",
        "qualifying": False,
        "complete": True,
        "plan_sha256": s.digest(value),
        "context": value["context"],
        "index": index,
        "exit_code": 0,
        "seconds": 1.0,
        "error": None,
        "files": {path.name: s.q.sha256_file(path) for path in directory.iterdir()},
    }
    s.q.write_json(directory / "execution.json", receipt)
    return directory


def reseal(directory):
    path = directory / "execution.json"
    receipt = s.read(path)
    receipt["files"] = {
        name: s.q.sha256_file(directory / name) for name in receipt["files"]
    }
    s.q.write_json(path, receipt)


@pytest.fixture
def shards(tmp_path):
    value = s.plan(NODES, context("core-windows-3.13"), 2)
    directories = [execution(tmp_path / str(i), value, i) for i in range(2)]
    return value, directories


def test_aggregate_preserves_each_node_and_skip_reason_once(shards, tmp_path):
    value, directories = shards
    node = value["shards"][0]["nodes"][0]
    write_junit(directories[0] / "junit.xml", value["shards"][0]["nodes"], skip=node)
    reseal(directories[0])
    destination = tmp_path / "aggregate.xml"
    result = s.merge_junit(value, list(reversed(directories)), destination)
    assert set(result["outcomes"]) == set(NODES)
    assert result["outcomes"][node] == {"outcome": "skipped", "reason": "owned reason"}
    assert s.outcomes(s.junit(destination)) == result["outcomes"]
    with pytest.raises(s.q.QualificationError, match="new"):
        s.merge_junit(value, directories, destination)


@pytest.mark.parametrize(
    "mutation",
    [
        "missing-shard",
        "same-directory",
        "repeated-index",
        "unplanned-index",
        "stale-plan",
        "stale-attempt",
        "wrong-packages",
        "cancelled",
        "failed",
        "bool-exit",
        "unknown-field",
        "missing-collected",
        "extra-collected",
        "extra-selected",
        "missing-start",
        "duplicate-start",
        "extra-junit",
        "missing-junit",
        "counter",
        "contradiction",
        "partial-coverage",
    ],
)
def test_incomplete_or_spoofed_shards_cannot_produce_lane_evidence(
    shards, tmp_path, mutation
):
    value, directories = shards
    directory = directories[0]
    receipt = s.read(directory / "execution.json")
    if mutation == "missing-shard":
        directories.pop()
    elif mutation == "same-directory":
        directories[1] = directory
    elif mutation == "repeated-index":
        shutil.rmtree(directories[1])
        shutil.copytree(directory, directories[1])
    elif mutation == "unplanned-index":
        receipt["index"] = 2
    elif mutation == "stale-plan":
        receipt["plan_sha256"] = "0" * 64
    elif mutation == "stale-attempt":
        receipt["context"]["run_attempt"] += 1
    elif mutation == "wrong-packages":
        receipt["context"]["environment"]["packages"]["pytest"] = "8.0.0"
    elif mutation == "cancelled":
        receipt["complete"] = False
    elif mutation == "failed":
        receipt["exit_code"] = 1
    elif mutation == "bool-exit":
        receipt["exit_code"] = False
    elif mutation == "unknown-field":
        receipt["ignored"] = True
    elif mutation in {"missing-collected", "extra-collected"}:
        nodes = (
            value["inventory"][:-1]
            if mutation == "missing-collected"
            else value["inventory"] + ["tests/test_new.py::test_x"]
        )
        s.q.write_json(directory / "collected.json", nodes)
    elif mutation == "extra-selected":
        s.q.write_json(directory / "selected.json", value["inventory"])
    elif mutation in {"missing-start", "duplicate-start"}:
        rows = (directory / "started.jsonl").read_text().splitlines()
        rows = rows[:-1] if mutation == "missing-start" else rows + rows[:1]
        (directory / "started.jsonl").write_text("\n".join(rows))
    elif mutation in {"extra-junit", "missing-junit"}:
        nodes = value["shards"][0]["nodes"]
        write_junit(
            directory / "junit.xml",
            nodes + ["tests/test_extra.py::test_x"]
            if mutation == "extra-junit"
            else nodes[:-1],
        )
    elif mutation in {"counter", "contradiction"}:
        tree = ET.parse(directory / "junit.xml")
        if mutation == "counter":
            tree.getroot().set("tests", "999")
        else:
            case = next(tree.getroot().iter("testcase"))
            ET.SubElement(case, "error")
            ET.SubElement(case, "skipped", message="owned reason")
        tree.write(directory / "junit.xml", encoding="utf-8")
    elif mutation == "partial-coverage":
        receipt["files"]["coverage.data"] = "0" * 64
    s.q.write_json(directory / "execution.json", receipt)
    if mutation != "partial-coverage":
        reseal(directory)
    with pytest.raises((s.q.QualificationError, ET.ParseError)):
        s.merge_junit(value, directories, tmp_path / "aggregate.xml")
    assert not (tmp_path / "aggregate.xml").exists()


def test_shadow_shards_are_rejected_by_release_bundle_policy(shards):
    from release import qualification

    value, directories = shards
    for payload in (value, s.read(directories[0] / "execution.json")):
        with pytest.raises(qualification.QualificationError):
            qualification._reject_shadow_value(payload)


@pytest.mark.parametrize(
    "schema", ["agent-wiki-core-shard-freeze/v1", "agent-wiki-core-shard-comparison/v1"]
)
def test_new_shadow_envelopes_cannot_be_promoted_by_relabeling(schema):
    from release import qualification

    with pytest.raises(qualification.QualificationError, match="shadow evidence"):
        qualification._reject_shadow_value(
            {"schema_version": schema, "qualifying": True, "purpose": "qualification"}
        )
    with pytest.raises(qualification.QualificationError, match="shadow evidence"):
        qualification._reject_shadow_value(
            {
                "schema_version": qualification.JUNIT_PROJECTION_SCHEMA,
                "source_lane": "core-shard-shadow-windows",
            }
        )


def test_provider_version_must_match_the_source_identity():
    current = context()
    current["environment"]["packages"]["agent-wiki-cli"] = "99.0.0"
    with pytest.raises(s.q.QualificationError, match="provider version differs"):
        s.plan(NODES, current, 2)


@pytest.mark.parametrize("field", ["index", "estimated_ms"])
def test_shard_records_reject_numeric_type_coercion(field):
    value = s.plan(NODES, context(), 2)
    value["shards"][1][field] = (
        True if field == "index" else float(value["shards"][1][field])
    )
    with pytest.raises(s.q.QualificationError):
        s.validate_plan(value)
