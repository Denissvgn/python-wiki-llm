"""Measurements never turn partial or mismatched evidence into qualification."""

from copy import deepcopy
import json

import pytest

from release import optimization_evidence as evidence
from release import optimization_measurements as measurements
from tests.test_optimization_evidence import repository as repository


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(evidence.canonical(value))


@pytest.fixture
def capture(repository, tmp_path):
    root, sha = repository
    baseline = tmp_path / "baseline"
    evidence.freeze(root, sha, baseline, "owner/repo", required_ancestor=sha)
    inputs = tmp_path / "input"
    run = {
        "id": 5,
        "run_attempt": 1,
        "head_sha": sha,
        "repository": {"full_name": "owner/repo"},
        "path": evidence.WORKFLOW,
        "event": "workflow_dispatch",
        "status": "completed",
        "conclusion": "success",
        "created_at": "2026-09-22T00:00:00Z",
        "run_started_at": "2026-09-22T00:00:00Z",
        "environment": {"TOKEN": "must-not-be-exported"},
    }
    job = {
        "id": 7,
        "run_id": 5,
        "run_attempt": 1,
        "head_sha": sha,
        "name": "core (3.13)",
        "status": "completed",
        "conclusion": "success",
        "created_at": "2026-09-22T00:00:00Z",
        "started_at": "2026-09-22T00:00:05Z",
        "completed_at": "2026-09-22T00:00:15Z",
        "environment": {"TOKEN": "must-not-be-exported"},
        "steps": [
            {
                "name": name,
                "number": i,
                "status": "completed",
                "conclusion": "success",
                "started_at": f"2026-09-22T00:00:{start:02}Z",
                "completed_at": f"2026-09-22T00:00:{end:02}Z",
            }
            for i, (name, start, end) in enumerate(
                (("install", 5, 7), ("check", 7, 10)), 1
            )
        ],
    }
    jobs = {"total_count": 1, "jobs": [job]}
    index = {
        "schema_version": "agent-wiki-optimization-junit-inputs/v1",
        "run_id": 5,
        "run_attempt": 1,
        "source_sha": sha,
        "baseline_sha256": evidence.file_digest(baseline / "baseline.json"),
        "reports": [],
    }
    for lane in ("slow", "product"):
        path = inputs / f"junit/{lane}.xml"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            '<testsuites><testsuite tests="1"><testcase classname="tests.test_a" name="test_x" time="1.25" /></testsuite></testsuites>'
        )
        index["reports"].append(
            {
                "lane": lane,
                "path": f"junit/{lane}.xml",
                "job_id": 7,
                "sha256": evidence.file_digest(path),
            }
        )
    for name, value in (("run", run), ("jobs", jobs), ("index", index)):
        write(inputs / (name + ".json"), value)
    return baseline, inputs, run, jobs, index


def measure(capture, output):
    baseline, inputs, run, jobs, index = capture
    for name, value in (("run", run), ("jobs", jobs), ("index", index)):
        write(inputs / (name + ".json"), value)
    return measurements.measure(
        baseline,
        inputs / "run.json",
        inputs / "jobs.json",
        inputs / "index.json",
        output,
    )


def test_measurements_bind_inputs_separate_clocks_and_reproduce_overlap(
    capture, tmp_path
):
    output = tmp_path / "out"
    summary = measure(capture, output)
    assert (
        summary["qualifying"] is False and summary["completed_workflow_seconds"] == 15
    )
    assert summary["observed_runner_seconds"] == 10
    assert summary["overlaps"] == [
        {
            "lanes": ["product", "slow"],
            "declared_profile_match": True,
            "resolved_environment_equivalence": "not-established",
            "common_nodes": 1,
            "left_seconds": 1.25,
            "right_seconds": 1.25,
            "missing_node_times": 0,
            "outcome_differences": 0,
        }
    ]
    jobs = json.loads((output / "jobs.json").read_text())
    assert jobs[0]["queue_seconds"] == 5 and jobs[0]["unattributed_seconds"] == 5
    assert jobs[0]["phase_seconds"] == {"setup": 2, "test": 3}
    manifest = json.loads((output / "files.json").read_text())
    assert set(manifest["files"]) == {
        "baseline-ref.json",
        "contract.json",
        "summary.json",
        "run.json",
        "jobs.json",
        "nodes.json",
        "junit-index.json",
        "junit/slow.xml",
        "junit/product.xml",
    }
    for name, record in manifest["files"].items():
        raw = (output / name).read_bytes()
        assert evidence.digest(raw) == record["sha256"] and len(raw) == record["bytes"]
        assert b"must-not-be-exported" not in raw
    with pytest.raises(ValueError, match="must be new"):
        measure(capture, output)


@pytest.mark.parametrize("conclusion", ["cancelled", "failure", "timed_out"])
def test_incomplete_runs_never_claim_completed_workflow_duration(
    capture, tmp_path, conclusion
):
    capture[2]["conclusion"] = capture[3]["jobs"][0]["conclusion"] = conclusion
    summary = measure(capture, tmp_path / "out")
    assert summary["completed_workflow_seconds"] is None
    assert summary["critical_path"]["wall_seconds"] is None
    assert (
        summary["observed_job_span_seconds"] == 15
        and summary["observed_runner_seconds"] == 10
    )


@pytest.mark.parametrize(
    "mutation",
    [
        "source",
        "attempt",
        "bool-attempt",
        "repository",
        "index-baseline",
        "extra-index",
        "extra-report",
        "traversal",
        "digest",
        "pagination",
        "duplicate-job",
        "unknown-job",
        "duplicate-step",
        "overlap",
        "backwards",
    ],
)
def test_mismatched_or_ambiguous_inputs_are_rejected(capture, tmp_path, mutation):
    _, _, run, jobs, index = capture
    if mutation == "source":
        run["head_sha"] = "f" * 40
    elif mutation == "attempt":
        jobs["jobs"][0]["run_attempt"] = 2
    elif mutation == "bool-attempt":
        jobs["jobs"][0]["run_attempt"] = True
    elif mutation == "repository":
        run["repository"]["full_name"] = "another/repo"
    elif mutation == "index-baseline":
        index["baseline_sha256"] = "f" * 64
    elif mutation == "extra-index":
        index["environment"] = {"secret": "hidden"}
    elif mutation == "extra-report":
        index["reports"][0]["environment"] = {"secret": "hidden"}
    elif mutation == "traversal":
        index["reports"][0]["path"] = "../secret.xml"
    elif mutation == "digest":
        index["reports"][0]["sha256"] = "f" * 64
    elif mutation == "pagination":
        jobs["total_count"] = 2
    elif mutation == "duplicate-job":
        jobs["jobs"] *= 2
        jobs["total_count"] = 2
    elif mutation == "unknown-job":
        index["reports"][0]["job_id"] = 999
    elif mutation == "duplicate-step":
        jobs["jobs"][0]["steps"] *= 2
    elif mutation == "overlap":
        jobs["jobs"][0]["steps"][1]["started_at"] = "2026-09-22T00:00:06Z"
    else:
        jobs["jobs"][0]["completed_at"] = "2026-09-21T00:00:00Z"
    with pytest.raises(ValueError):
        measure(capture, tmp_path / "out")
    assert not (tmp_path / "out").exists()


@pytest.mark.parametrize(
    "body",
    [
        '<testcase classname="tests.test_a" name="x" time="NaN"/>',
        '<testcase classname="tests.test_a" name="x" time="-1"/>',
        '<testcase classname="tests.test_a" name="x"><failure/><skipped/></testcase>',
        '<testcase classname="tests.test_a" name="x"/><testcase classname="tests.test_a" name="x"/>',
    ],
)
def test_invalid_case_observations_are_rejected(tmp_path, body):
    path = tmp_path / "junit.xml"
    path.write_text(f"<testsuite>{body}</testsuite>")
    with pytest.raises(ValueError):
        measurements.read_junit(path)


def test_missing_node_timing_stays_unknown_and_truncated_inventory_fails(tmp_path):
    path = tmp_path / "junit.xml"
    path.write_text(
        '<testsuite tests="1"><testcase classname="tests.test_a" name="x"/></testsuite>'
    )
    assert measurements.read_junit(path)["tests/test_a.py::x"]["seconds"] is None
    path.write_text(path.read_text().replace('tests="1"', 'tests="2"'))
    with pytest.raises(ValueError, match="inventory"):
        measurements.read_junit(path)


def test_repeated_samples_keep_candidates_separate_and_disclose_variation(
    capture, tmp_path
):
    base = measure(capture, tmp_path / "out")
    second = {**deepcopy(base), "run_id": 6, "completed_workflow_seconds": 25}
    cancelled = {
        **deepcopy(base),
        "run_id": 8,
        "completed_workflow_seconds": None,
        "conclusion": "cancelled",
    }
    other = {
        **deepcopy(base),
        "run_id": 9,
        "source_sha": "f" * 40,
        "baseline_sha256": "e" * 64,
    }
    grouped = measurements.summarize_runs([base, second, cancelled, other])
    assert len(grouped) == 2
    group = next(g for g in grouped if g["sample_count"] == 3)
    assert group["complete_samples"] == 2 and group["excluded_incomplete_samples"] == 1
    assert group["wall_seconds"] == {"min": 15, "max": 25, "median": 20}
    with pytest.raises(ValueError, match="independent sample"):
        measurements.summarize_runs([base, base])
    with pytest.raises(ValueError, match="completed-run"):
        measurements.summarize_runs([{**cancelled, "completed_workflow_seconds": 15}])


def test_cancelled_unstarted_github_placeholder_has_unknown_timing(capture, tmp_path):
    capture[2]["conclusion"] = "cancelled"
    job = capture[3]["jobs"][0]
    job.update(conclusion="cancelled", steps=[], completed_at="2026-09-22T00:00:04Z")
    output = tmp_path / "out"
    summary = measure(capture, output)
    assert summary["completed_workflow_seconds"] is None
    assert summary["incomplete_job_times"] == 1
    observed = json.loads((output / "jobs.json").read_text())[0]
    assert (
        observed["runner_seconds"] is None and "inverted" in observed["timing_anomaly"]
    )


def test_harness_verification_is_setup_despite_test_file_members():
    name = "Verify and extract qualification harnesses"
    assert (
        measurements.phase(
            {"name": name},
            {
                "steps": [
                    {"name": name, "run": "test -f tests/release_artifact_smoke.py"}
                ]
            },
        )
        == "setup"
    )


def test_installing_audit_tools_is_not_scanner_execution():
    name = "Install exact compiler and audit tools"
    declared = {
        "steps": [
            {
                "name": name,
                "run": "python -m pip install --require-hashes -r release/requirements.txt",
            }
        ]
    }
    assert measurements.phase({"name": name}, declared) == "setup"


def test_complete_pagination_and_unknown_queue_times(capture, tmp_path):
    baseline, inputs, run, jobs, index = capture
    second = {
        **deepcopy(jobs["jobs"][0]),
        "id": 8,
        "name": "core (3.10)",
        "created_at": None,
    }
    pages = [
        {"total_count": 2, "jobs": jobs["jobs"]},
        {"total_count": 2, "jobs": [second]},
    ]
    write(inputs / "pages.json", pages)
    output = tmp_path / "out"
    summary = measurements.measure(
        baseline,
        inputs / "run.json",
        inputs / "pages.json",
        inputs / "index.json",
        output,
    )
    assert summary["jobs"] == 2 and summary["observed_runner_seconds"] == 20
    assert summary["completed_workflow_seconds"] == 15
    observed = json.loads((output / "jobs.json").read_text())
    assert observed[1]["queue_seconds"] is None
