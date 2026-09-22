"""Reproduce bounded, non-qualifying optimization measurements from captured inputs."""

from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime
import itertools
import json
import math
from pathlib import Path
import re
import tempfile
import statistics
import xml.etree.ElementTree as ET

from release.optimization_evidence import (
    WORKFLOW,
    canonical,
    digest,
    file_digest,
    load_json,
    resolve,
    verify_baseline,
)
from release.qualification import _node_id

LABEL = re.compile(r"[a-z0-9][a-z0-9.-]{0,80}\Z")
MAX_JSON = 16 * 1024 * 1024
MAX_JUNIT = 32 * 1024 * 1024


def bounded_json(path: Path):
    if path.is_symlink() or path.stat().st_size > MAX_JSON:
        raise ValueError("invalid or oversized JSON input")
    return load_json(path)


def stamp(value):
    if value is None or value.startswith("0001-"):
        return None
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("timestamp must carry a timezone")
    return parsed


def elapsed(start, end):
    first, last = stamp(start), stamp(end)
    if first is None or last is None:
        return None
    seconds = (last - first).total_seconds()
    if seconds < 0:
        raise ValueError("negative time interval")
    return seconds


def phase(step: dict, declared: dict) -> str:
    definition = next(
        (
            s
            for s in declared["steps"]
            if s.get("name", "Run " + s.get("uses", "")) == step["name"]
        ),
        {},
    )
    script = definition.get("run", "")
    uses = definition.get("uses", "")
    if step["name"] == "Verify and extract qualification harnesses":
        return "setup"
    if "release/static_checks.py" in script or step["name"].lower().startswith(
        "audit "
    ):
        return "scanner"
    if (
        "-m pytest" in script
        or "tests/" in script
        and any(word in step["name"].lower() for word in ("run", "verify", "validate"))
    ):
        return "test"
    if (
        "upload-artifact@" in uses
        or "attest-" in uses
        or any(
            word in script
            for word in (
                "project-junit",
                "verify-junit",
                "verify-owner-lanes",
                "compare-smoke",
                "compare-builds",
                " aggregate",
                " bundle",
            )
        )
    ):
        return "evidence"
    if (
        step["name"] == "Set up job"
        or "setup-" in uses
        or "checkout@" in uses
        or "download-artifact@" in uses
        or any(
            word in script
            for word in (
                "pip install",
                "create-venv",
                "-m venv",
                "extract-source",
                "git archive",
                "freeze-source",
            )
        )
        or step["name"] == "Verify and extract qualification harnesses"
    ):
        return "setup"
    return "other"


def read_junit(path: Path) -> dict:
    if path.is_symlink() or path.stat().st_size > MAX_JUNIT:
        raise ValueError("invalid or oversized JUnit input")
    raw = path.read_bytes().decode("utf-8-sig")
    if "<!DOCTYPE" in raw or "<!ENTITY" in raw:
        raise ValueError("JUnit declarations are forbidden")
    root = ET.fromstring(raw)
    if root.tag not in {"testsuite", "testsuites"}:
        raise ValueError("invalid JUnit root")
    nodes = {}
    for case in root.iter("testcase"):
        node = _node_id(case)
        if node in nodes or len(nodes) >= 100_000:
            raise ValueError("duplicate or excessive JUnit nodes")
        seconds = float(case.attrib["time"]) if "time" in case.attrib else None
        if seconds is not None and (not math.isfinite(seconds) or seconds < 0):
            raise ValueError("invalid testcase duration")
        outcomes = [
            name
            for name in ("failure", "error", "skipped")
            if case.find(name) is not None
        ]
        if len(outcomes) > 1:
            raise ValueError("ambiguous testcase outcome")
        skipped = case.find("skipped")
        nodes[node] = {
            "seconds": seconds,
            "outcome": outcomes[0] if outcomes else "passed",
            "skip_reason": (skipped.get("message") or skipped.text or "")
            if skipped is not None
            else None,
        }
    if not nodes:
        raise ValueError("JUnit contains no testcase inventory")
    for suite in root.iter():
        if suite.tag in {"testsuites", "testsuite"} and "tests" in suite.attrib:
            if int(suite.attrib["tests"]) != len(list(suite.iter("testcase"))):
                raise ValueError("JUnit inventory counter differs")
    return nodes


def declared_profile_key(profile: dict) -> str:
    # Timing overlap is a declared-profile comparison, never proof of resolved
    # package equivalence. Test selectors and report destinations are excluded.
    flags = []
    for execution in profile["pytest"]:
        argv = execution["argv"][3:]
        flags.append(
            {
                "argv": [
                    arg for arg in argv if not arg.startswith(("tests", "--junitxml="))
                ],
                "environment": execution["environment"],
                "working_directory": execution["working_directory"],
            }
        )
    return digest(
        canonical(
            {
                "runner": profile["runner"],
                "python": profile["python"],
                "install": [s["script"] for s in profile["install_steps"]],
                "environment": profile["environment"],
                "flags": sorted({json.dumps(f) for f in flags}),
            }
        )
    )


def measure(
    baseline_dir: Path, run_path: Path, jobs_path: Path, index_path: Path, output: Path
) -> dict:
    baseline, contract = verify_baseline(baseline_dir)
    run, pages, index = (
        bounded_json(run_path),
        bounded_json(jobs_path),
        bounded_json(index_path),
    )
    source = baseline["source"]["sha"]
    for record, fields in (
        (run, ("id", "run_attempt")),
        (index, ("run_id", "run_attempt")),
    ):
        if any(type(record[key]) is not int or record[key] < 1 for key in fields):
            raise ValueError("run identities must be positive integers")
    if (
        run["head_sha"] != source
        or run["repository"]["full_name"] != baseline["repository"]
        or run["path"] != WORKFLOW
        or run.get("event") != "workflow_dispatch"
        or type(run["id"]) is not int
        or type(run["run_attempt"]) is not int
        or run["run_attempt"] < 1
    ):
        raise ValueError("run does not match the baseline identity")
    if (
        index["schema_version"] != "agent-wiki-optimization-junit-inputs/v1"
        or index["baseline_sha256"] != file_digest(baseline_dir / "baseline.json")
        or index["run_id"] != run["id"]
        or index["run_attempt"] != run["run_attempt"]
        or index["source_sha"] != source
    ):
        raise ValueError("JUnit input index does not match run/attempt/baseline")
    if set(index) != {
        "schema_version",
        "baseline_sha256",
        "run_id",
        "run_attempt",
        "source_sha",
        "reports",
    }:
        raise ValueError("JUnit index contains non-allowlisted metadata")
    pages = pages if isinstance(pages, list) else [pages]
    if any(
        type(page["total_count"]) is not int or page["total_count"] < 0
        for page in pages
    ):
        raise ValueError("invalid job inventory count")
    jobs = [job for page in pages for job in page["jobs"]]
    if (
        not pages
        or any(page["total_count"] != len(jobs) for page in pages)
        or len(jobs) > 1000
    ):
        raise ValueError("jobs pagination is incomplete")
    job_by_id = {job["id"]: job for job in jobs}
    if len(job_by_id) != len(jobs):
        raise ValueError("duplicate job identity")
    profile_by_name = {p["name"]: p for p in contract["profiles"]}
    if len(profile_by_name) != len(contract["profiles"]):
        raise ValueError("ambiguous declared job names")
    observations = []
    for job in jobs:
        if any(
            type(job[key]) is not int or job[key] < 1
            for key in ("id", "run_id", "run_attempt")
        ):
            raise ValueError("job identities must be positive integers")
        if (
            job["run_id"] != run["id"]
            or job["run_attempt"] != run["run_attempt"]
            or job["head_sha"] != source
            or job["name"] not in profile_by_name
        ):
            raise ValueError("job does not belong to this run/attempt/profile")
        profile = profile_by_name[job["name"]]
        declared = resolve(
            contract["workflow_definition"]["jobs"][profile["job_id"]],
            profile["matrix"],
        )
        steps = []
        phases: dict[str, float] = {}
        intervals = []
        step_numbers = set()
        for step in job["steps"]:
            if (
                type(step["number"]) is not int
                or step["number"] < 1
                or step["number"] in step_numbers
            ):
                raise ValueError("duplicate step number")
            step_numbers.add(step["number"])
            seconds = elapsed(step.get("started_at"), step.get("completed_at"))
            if seconds is not None and seconds > 0:
                first, last = stamp(step["started_at"]), stamp(step["completed_at"])
                job_first, job_last = (
                    stamp(job.get("started_at")),
                    stamp(job.get("completed_at")),
                )
                assert first is not None and last is not None
                if (
                    job_first is None
                    or first < job_first
                    or job_last is not None
                    and last > job_last
                ):
                    raise ValueError("step lies outside job interval")
                intervals.append((first, last))
            category = phase(step, declared)
            steps.append(
                {
                    k: step.get(k)
                    for k in (
                        "name",
                        "number",
                        "status",
                        "conclusion",
                        "started_at",
                        "completed_at",
                    )
                }
                | {"phase": category, "seconds": seconds}
            )
            if seconds is not None:
                phases[category] = phases.get(category, 0.0) + seconds
        timing_anomaly = None
        try:
            seconds = elapsed(job.get("started_at"), job.get("completed_at"))
        except ValueError:
            # GitHub may finalize a never-started cancelled placeholder one
            # second before its nominal start. Preserve unknown timing rather
            # than inventing zero duration or discarding the rest of the run.
            if job["conclusion"] not in {"cancelled", "skipped"} or job["steps"]:
                raise
            seconds = None
            timing_anomaly = "unstarted terminal job has inverted timestamps"
        ordered = sorted(intervals)
        if any(left[1] > right[0] for left, right in zip(ordered, ordered[1:])):
            raise ValueError("overlapping step intervals")
        if seconds is not None and sum(phases.values()) > seconds:
            raise ValueError("step times exceed job interval")
        observations.append(
            {
                k: job.get(k)
                for k in (
                    "id",
                    "name",
                    "status",
                    "conclusion",
                    "created_at",
                    "started_at",
                    "completed_at",
                )
            }
            | {
                "job_id": profile["job_id"],
                "matrix": profile["matrix"],
                "queue_seconds": elapsed(job.get("created_at"), job.get("started_at")),
                "runner_seconds": seconds,
                "phase_seconds": dict(phases),
                "unattributed_seconds": seconds - sum(phases.values())
                if seconds is not None
                else None,
                "actual_python_and_packages": None,
                "timing_anomaly": timing_anomaly,
                "steps": steps,
            }
        )
    lanes, retained = {}, {}
    if len(index["reports"]) > 64:
        raise ValueError("too many JUnit inputs")
    for item in index["reports"]:
        if set(item) != {"lane", "path", "job_id", "sha256"}:
            raise ValueError("JUnit report contains non-allowlisted metadata")
        if type(item["job_id"]) is not int:
            raise ValueError("JUnit job identity must be an integer")
        lane = item["lane"]
        if (
            not LABEL.fullmatch(lane)
            or lane in lanes
            or item["path"] != f"junit/{lane}.xml"
        ):
            raise ValueError("JUnit path is outside the fixed allowlist or duplicated")
        if item["job_id"] not in job_by_id:
            raise ValueError("JUnit refers to an unknown job")
        path = index_path.parent / item["path"]
        if (
            path.parent.is_symlink()
            or path.is_symlink()
            or file_digest(path) != item["sha256"]
        ):
            raise ValueError("JUnit commitment differs")
        nodes = read_junit(path)
        job = job_by_id[item["job_id"]]
        profile = profile_by_name[job["name"]]
        lanes[lane] = {
            "job_id": job["id"],
            "profile_key": declared_profile_key(profile),
            "sha256": item["sha256"],
            "nodes": nodes,
        }
        retained[item["path"]] = path.read_bytes()
    overlaps = []
    for left, right in itertools.combinations(sorted(lanes), 2):
        a, b = lanes[left], lanes[right]
        shared = sorted(a["nodes"].keys() & b["nodes"].keys())
        overlaps.append(
            {
                "lanes": [left, right],
                "declared_profile_match": a["profile_key"] == b["profile_key"],
                "resolved_environment_equivalence": "not-established",
                "common_nodes": len(shared),
                "left_seconds": sum(a["nodes"][n]["seconds"] or 0 for n in shared),
                "right_seconds": sum(b["nodes"][n]["seconds"] or 0 for n in shared),
                "missing_node_times": sum(
                    a["nodes"][n]["seconds"] is None or b["nodes"][n]["seconds"] is None
                    for n in shared
                ),
                "outcome_differences": sum(
                    (a["nodes"][n]["outcome"], a["nodes"][n]["skip_reason"])
                    != (b["nodes"][n]["outcome"], b["nodes"][n]["skip_reason"])
                    for n in shared
                ),
            }
        )
    completed = (
        bool(jobs)
        and run["status"] == "completed"
        and run["conclusion"] == "success"
        and all(
            j["status"] == "completed"
            and j["conclusion"] in {"success", "skipped", "neutral"}
            and (
                j["conclusion"] == "skipped"
                or elapsed(j.get("started_at"), j.get("completed_at")) is not None
            )
            for j in jobs
        )
    )
    ends = [j["completed_at"] for j in jobs if stamp(j.get("completed_at")) is not None]
    last_end = (
        max(
            ends, key=lambda value: datetime.fromisoformat(value.replace("Z", "+00:00"))
        )
        if ends
        else None
    )
    wall = elapsed(run.get("run_started_at"), last_end)
    summary = {
        "schema_version": "agent-wiki-optimization-measurements/v1",
        "qualifying": False,
        "baseline_role": baseline["role"],
        "source_sha": source,
        "baseline_sha256": index["baseline_sha256"],
        "run_id": run["id"],
        "run_attempt": run["run_attempt"],
        "status": run["status"],
        "conclusion": run["conclusion"],
        "sample_count": 1,
        "phase_scope": "workflow-step intervals; mixed commands are not individually timed; unknown work remains other/unattributed",
        "savings_claim": None,
        "completed_workflow_seconds": wall if completed else None,
        "critical_path": {
            "method": "observed workflow makespan including scheduling; not a sum of node durations",
            "wall_seconds": wall if completed else None,
            "job_chain": None,
        },
        "observed_job_span_seconds": wall,
        "initial_run_queue_seconds": elapsed(
            run.get("created_at"), run.get("run_started_at")
        ),
        "observed_runner_seconds": sum(j["runner_seconds"] or 0 for j in observations),
        "incomplete_job_times": sum(j["runner_seconds"] is None for j in observations),
        "jobs": len(jobs),
        "reported_lanes": {
            name: {
                "nodes": len(lane["nodes"]),
                "outcomes": dict(Counter(n["outcome"] for n in lane["nodes"].values())),
                "missing_node_times": sum(
                    n["seconds"] is None for n in lane["nodes"].values()
                ),
                "testcase_seconds": sum(
                    n["seconds"] or 0 for n in lane["nodes"].values()
                ),
            }
            for name, lane in lanes.items()
        },
        "overlaps": overlaps,
        "provenance_limit": "captured API metadata and caller-indexed JUnit; not authenticated release qualification",
    }
    if output.exists() or output.is_symlink():
        raise ValueError("measurement output must be new")
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(
        prefix=".measurements-", dir=output.parent
    ) as temporary:
        staging = Path(temporary) / "result"
        staging.mkdir()
        files = {
            "baseline-ref.json": canonical(baseline),
            "contract.json": canonical(contract),
            "summary.json": canonical(summary),
            "run.json": canonical(
                {
                    k: run.get(k)
                    for k in (
                        "id",
                        "run_attempt",
                        "head_sha",
                        "event",
                        "status",
                        "conclusion",
                        "created_at",
                        "run_started_at",
                        "path",
                    )
                }
            ),
            "jobs.json": canonical(observations),
            "nodes.json": canonical(lanes),
            "junit-index.json": canonical(index),
            **retained,
        }
        for name, raw in files.items():
            destination = staging / name
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(raw)
        manifest = {
            "schema_version": "agent-wiki-optimization-evidence-files/v1",
            "files": {
                name: {"sha256": digest(raw), "bytes": len(raw)}
                for name, raw in files.items()
            },
            "input_digests": {
                "run": file_digest(run_path),
                "jobs": file_digest(jobs_path),
                "junit_index": file_digest(index_path),
            },
            "generator_sha256": file_digest(Path(__file__)),
        }
        (staging / "files.json").write_bytes(canonical(manifest))
        staging.rename(output)
    return summary


def summarize_runs(summaries: list[dict]) -> list[dict]:
    """Describe repeated samples without mixing candidates or incomplete runs."""
    groups: dict[tuple, list] = {}
    seen = set()
    for row in summaries:
        duration = row["completed_workflow_seconds"]
        if (
            row["schema_version"] != "agent-wiki-optimization-measurements/v1"
            or row["qualifying"] is not False
            or duration is not None
            and (
                type(duration) not in (int, float)
                or not math.isfinite(duration)
                or duration < 0
                or row["status"] != "completed"
                or row["conclusion"] != "success"
            )
        ):
            raise ValueError("invalid completed-run measurement")
        key = (row["run_id"], row["run_attempt"])
        if key in seen:
            raise ValueError("duplicate run attempt is not an independent sample")
        seen.add(key)
        groups.setdefault(
            (row["baseline_sha256"], row["source_sha"], row["baseline_role"]), []
        ).append(row)
    result = []
    for key, rows in sorted(groups.items()):
        durations = [
            r["completed_workflow_seconds"]
            for r in rows
            if r["completed_workflow_seconds"] is not None
        ]
        result.append(
            {
                "baseline_sha256": key[0],
                "source_sha": key[1],
                "baseline_role": key[2],
                "sample_count": len(rows),
                "complete_samples": len(durations),
                "excluded_incomplete_samples": len(rows) - len(durations),
                "wall_seconds": {
                    "min": min(durations),
                    "max": max(durations),
                    "median": statistics.median(durations),
                }
                if durations
                else None,
                "confidence": "single sample"
                if len(durations) == 1
                else "observational; no significance claim",
            }
        )
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("baseline", "run", "jobs", "junit-index", "output"):
        parser.add_argument("--" + name, type=Path, required=True)
    args = parser.parse_args()
    summary = measure(args.baseline, args.run, args.jobs, args.junit_index, args.output)
    print(
        json.dumps(
            {
                k: summary[k]
                for k in (
                    "source_sha",
                    "run_id",
                    "run_attempt",
                    "qualifying",
                    "completed_workflow_seconds",
                )
            }
        )
    )


if __name__ == "__main__":
    main()
