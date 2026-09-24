"""Owned, complete Windows producer evidence for qualification boundary controls."""

import argparse

from release import core_shards as s, core_shard_runner as r, qualification as q
from tests.test_core_shards import context, execution


def qualifying_core(
    directory, identity, harness, run_id, allowlist, registry, *, nodes=None
):
    current = context(s.WINDOWS_LANE)
    current.update(identity=identity, harness_sha256=harness, run_id=run_id)
    current["environment"]["packages"]["agent-wiki-cli"] = identity["version"]
    if nodes is None:
        selected = {
            selector.replace("*", "owned") + "::test_owned"
            for kind in ("security", "product")
            for selector in registry["gates"][kind + "-ubuntu-24.04"]
        }
        nodes = sorted(
            selected
            | {f"tests/test_group_{i % 10}.py::test_owned_{i}" for i in range(5322)}
        )
    value = s.plan(nodes, current, 2, purpose="qualification")
    preparation = directory / "windows-plan"
    preparation.mkdir(parents=True)
    q.write_json(preparation / "plan.json", value)
    q.write_json(preparation / "collected.json", value["inventory"])
    (preparation / "constraints.txt").write_text(
        r.constraints(current["environment"]), encoding="utf-8"
    )
    (preparation / "collection.log").write_text("owned collection\n", encoding="utf-8")
    (preparation / "started.jsonl").write_bytes(b"")
    q.write_json(
        preparation / "preparation.json",
        {
            "schema_version": s.PREPARATION_SCHEMA,
            "purpose": "qualification",
            "qualifying": True,
            "complete": True,
            "context": current,
            "plan_sha256": s.digest(value),
            "exit_code": 0,
            "seconds": 1.0,
            "error": None,
            "files": {p.name: q.sha256_file(p) for p in preparation.iterdir()},
        },
    )
    shards = [execution(directory / f"windows-shard-{i}", value, i) for i in range(2)]
    aggregate = directory / "windows"
    aggregate.mkdir()
    xml = aggregate / (s.WINDOWS_LANE + ".xml")
    s.merge_junit(value, shards, xml, purpose="qualification")
    result = aggregate / ("result-" + s.WINDOWS_LANE + ".json")
    q.verify_junit(
        argparse.Namespace(
            junit=xml,
            lane=s.WINDOWS_LANE,
            allowlist=allowlist,
            minimum_collected=5322,
            minimum_passed=5070,
            discovery=False,
            output=result,
        )
    )
    q.write_json(
        aggregate / "aggregation.json",
        {
            "schema_version": s.AGGREGATION_SCHEMA,
            "purpose": "qualification",
            "qualifying": True,
            "complete": True,
            "context": current,
            "plan_sha256": s.digest(value),
            "preparation_sha256": q.sha256_file(preparation / "preparation.json"),
            "shards": {
                str(i): q.sha256_file(p / "execution.json")
                for i, p in enumerate(shards)
            },
            "files": {p.name: q.sha256_file(p) for p in (xml, result)},
        },
    )
    result_paths = {
        "RD-01:" + path.name: path for path in [aggregate, preparation, *shards]
    }
    identity_path = directory / "identity.json"
    q.write_json(identity_path, identity)
    for kind, gate in (("security", "RD-04"), ("product", "RD-05")):
        lane = kind + "-windows-2025"
        projected = directory / kind
        q.project_junit(
            argparse.Namespace(
                identity=identity_path,
                source_junit=xml,
                source_lane=s.WINDOWS_LANE,
                target_lane=lane,
                selector=registry["gates"][kind + "-ubuntu-24.04"],
                projected_junit=projected / (lane + ".xml"),
                receipt=projected / (lane + "-projection.json"),
            )
        )
        # Exercise Windows-produced JSON even when the consuming test host is
        # Linux/macOS. Original bytes still belong to the hosted ZIP fixture.
        receipt = projected / (lane + "-projection.json")
        receipt.write_bytes(
            receipt.read_text(encoding="utf-8").replace("\n", "\r\n").encode("utf-8")
        )
        result_paths[gate + ":windows"] = projected
    return value, result_paths
