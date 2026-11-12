"""Bounded fresh/prepared fixture measurements on an exact installed candidate."""

from __future__ import annotations

import argparse
from collections import Counter
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import statistics
import sys
import time

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from release import contract_canary as canary
from release import core_shard_runner as runner
from release import core_shards as shards
from release import pr_ci_pytest

SCHEMA = "agent-wiki-native-bottleneck-measurement/v1"
SELECTORS = (
    "tests/test_documentation_calibration_controller.py::test_prepare_requires_reproduced_complete_priority_blind_controls",
    "tests/test_documentation_calibration_controller.py::test_status_rejects_source_mutation_before_admission",
    "tests/test_documentation_calibration_controller.py::test_fully_written_pending_transaction_is_recovered_idempotently",
    "tests/test_documentation_calibration_controller.py::test_early_verify_with_pending_roles_is_read_only_and_ineligible",
    "tests/test_publication_candidate.py::test_candidate_is_deterministic_and_preserves_manual_content",
    "tests/test_publication_candidate.py::test_exact_candidate_and_topic_review_enable_local_readiness",
    "tests/test_publication_candidate.py::test_existing_wiki_live_source_rejects_stale_native_only_dependencies",
    "tests/test_publication_candidate.py::test_unreviewed_receipt_does_not_grant_ownership",
    "tests/test_publication_candidate.py::test_artifact_only_review_does_not_invent_a_local_target",
    "tests/test_sync_analysis_cache.py::test_markdown_edit_reuses_static_inputs_but_completes_actual_commit",
    "tests/test_sync_analysis_cache.py::test_cached_reanchor_matches_independent_full_builder",
    "tests/test_sync_analysis_cache.py::test_corrupt_shard_falls_back_without_losing_prose",
    "tests/test_sync_analysis_cache.py::test_source_edit_reuses_other_files_authenticated_implementation",
)


def summarize(rows: list[dict]) -> dict:
    shards.require(bool(rows), "bottleneck samples are missing")
    original = rows[0]
    groups: dict[str, list[dict]] = {"fresh": [], "prepared": []}
    seen = set()
    for row in rows:
        shards.require(row["complete"] and row["passed"] and row["source_sha"] == original["source_sha"]
                       and row["inventory"] == original["inventory"] and row["outcomes_sha256"] == original["outcomes_sha256"]
                       and row["environment"] == original["environment"], "bottleneck inputs, inventory, outcomes or runtime differ")
        mode = row["mode"]
        shards.require(mode in groups and (mode, row["sample"]) not in seen, "duplicate or unknown measurement sample")
        shards.duration(row["seconds"])
        shards.require(row["seconds"] > 0, "bottleneck elapsed time must be positive")
        seen.add((mode, row["sample"]))
        groups[mode].append(row)
    shards.require(len(groups["fresh"]) == len(groups["prepared"]) >= 2, "two samples per mode are required")
    statistics_by_mode = {}
    for mode, observations in groups.items():
        times = [row["seconds"] for row in observations]
        statistics_by_mode[mode] = {"seconds": times, "min": min(times), "max": max(times), "median": statistics.median(times),
                                    "fixture_profiles": [r["fixture_profile"] for r in observations]}
    return {"schema_version": SCHEMA, "qualifying": False, "source_sha": original["source_sha"],
            "collected_per_sample": len(original["inventory"]), "inventory_sha256": shards.digest(original["inventory"]),
            "environment": original["environment"], "modes": statistics_by_mode,
            "median_ratio": statistics_by_mode["prepared"]["median"] / statistics_by_mode["fresh"]["median"],
            "rollout_authority": False, "scope": "Local bounded fixture experiment. Each process includes its first cold preparation; later leases restore byte-identical files at that preparation's absolute root. Hosted native time/cost/parity remains required."}


def worker(args) -> int:
    import pytest

    expected = canary.verify_candidate(args)
    output = args.output
    output.mkdir(parents=True, exist_ok=False)
    os.environ["LLM_WIKI_TEST_PREPARED_WORKSPACES"] = "1" if args.mode == "prepared" else "0"
    os.environ["LLM_WIKI_TEST_PREPARED_WORKSPACE_REPORT"] = str(output / "workspace-profile.json")
    os.environ["LLM_WIKI_TEST_PREPARED_REPORT_PID"] = str(os.getpid())
    os.environ["PR_CI_COLLECTION"] = str(output / "collection.json")
    started, phases = [], []
    class Observations:
        @pytest.hookimpl(trylast=True)
        def pytest_collection_finish(self, session):
            nodes = shards.inventory([item.nodeid for item in session.items])
            shards.require(0 < len(nodes) <= 64 and all(any(shards.q._selector_matches(s, n) for n in nodes) for s in SELECTORS),
                           "bounded bottleneck inventory differs")
        def pytest_runtest_logstart(self, nodeid, location):
            started.append(nodeid)
            with (output / "started.jsonl").open("a", encoding="utf-8") as stream:
                stream.write(json.dumps(nodeid) + "\n")
        def pytest_runtest_logreport(self, report):
            phases.append({"node": report.nodeid, "phase": report.when, "seconds": report.duration, "outcome": report.outcome})
    before = time.monotonic()
    code = int(pytest.main([*SELECTORS, *shards.FLAGS, "--junitxml=" + str(output / "junit.xml")], plugins=[pr_ci_pytest, Observations()]))
    seconds = time.monotonic() - before
    collection = shards.read(output / "collection.json")
    nodes = shards.inventory(collection["collected"])
    cases = shards.junit(output / "junit.xml")
    shards.require(code == 0 and collection["deselected"] == [] and Counter(collection["selected"]) == Counter(nodes)
                   and Counter(started) == Counter(nodes) and set(cases) == set(nodes)
                   and all(row["outcome"] == "passed" for row in shards.outcomes(cases).values()),
                   "bottleneck measurement failed or lost an actual case")
    shards.require(canary.verify_candidate(args) == expected, "provider changed during bottleneck measurement")
    profile = shards.read(output / "workspace-profile.json")
    shards.require(profile["enabled"] is (args.mode == "prepared") and profile["shared_mutable_files"] is False,
                   "fixture experiment mode differs")
    row = {"schema_version": SCHEMA, "complete": True, "passed": True, "qualifying": False,
           "source_sha": args.source_sha, "mode": args.mode, "sample": args.sample, "seconds": seconds,
           "inventory": nodes, "outcomes_sha256": shards.digest(shards.outcomes(cases)), "phases": phases,
           "fixture_profile": profile,
           "environment": {"python": platform.python_version(), "platform": sys.platform, "machine": platform.machine(),
                           "packages": {d.metadata["Name"]: d.version for d in importlib.metadata.distributions()}}}
    shards.q.write_json(output / "result.json", row)
    return 0


def run(args) -> int:
    canary.verify_candidate(args)
    shards.require(args.samples in {2, 4}, "bottleneck samples must be 2 or 4")
    shards.require(not args.output.is_relative_to(args.root), "measurement evidence must be outside source")
    args.output.mkdir(parents=True, exist_ok=False)
    observations = []
    for sample in range(args.samples):
        # Reverse the order on alternating pairs; retain every sample.
        for mode in (("fresh", "prepared") if sample % 2 == 0 else ("prepared", "fresh")):
            target = args.output / (mode + "-" + str(sample))
            env = runner.child_environment(args.output / (target.name + "-state"), args.output / (target.name + "-tmp"), args.archive)
            command = [sys.executable, "-I", str(Path(__file__).resolve()), "worker"]
            for name in ("root", "archive", "identity", "expected_prefix"):
                command += ["--" + name.replace("_", "-"), str(getattr(args, name))]
            command += ["--source-sha", args.source_sha, "--output", str(target), "--mode", mode, "--sample", str(sample)]
            receipt = runner.invoke(command, args.root, env, args.output / (target.name + ".log"), timeout=600)
            shards.q.write_json(args.output / (target.name + "-execution.json"), receipt)
            shards.require(receipt["exit_code"] == 0, "bottleneck sample failed; retained original log and partial evidence")
            observations.append(shards.read(target / "result.json"))
    report = summarize(observations)
    shards.q.write_json(args.output / "result.json", report)
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("operation", choices=("run", "worker"))
    for name in ("root", "archive", "identity", "expected-prefix", "output"):
        parser.add_argument("--" + name, type=Path, required=True)
    parser.add_argument("--source-sha", required=True)
    parser.add_argument("--samples", type=int, default=2)
    parser.add_argument("--mode", choices=("fresh", "prepared"))
    parser.add_argument("--sample", type=int)
    args = parser.parse_args(argv)
    try:
        for name in ("root", "archive", "identity", "expected_prefix", "output"):
            setattr(args, name, canary.canary.safe(Path(os.path.abspath(getattr(args, name)))))
        return run(args) if args.operation == "run" else worker(args)
    except (OSError, ValueError, RuntimeError) as exc:
        print("Native bottleneck measurement failed: " + str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
