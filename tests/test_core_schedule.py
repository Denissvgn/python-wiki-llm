"""Advisory native weights, isolated trials and separate time/cost decisions."""

from copy import deepcopy
from decimal import InvalidOperation
from pathlib import Path
import xml.etree.ElementTree as ET

import pytest

from release import core_schedule as scheduling, core_shards as s
from tests.test_core_shards import context, history, NODES

ROOT = Path(__file__).parents[1]


def test_native_weight_profile_keeps_full_inventory_on_patch_dependency_or_machine_drift():
    current = context(s.WINDOWS_LANE)
    previous = {
        "schema_version": s.NATIVE_HISTORY_SCHEMA,
        "source_sha": "b" * 40,
        "run_id": 1,
        "run_attempt": 1,
        "lanes": {
            s.WINDOWS_LANE: {
                "profile": s.profile(s.WINDOWS_LANE),
                "environment": deepcopy(current["environment"]),
                "files_ms": {s.file_name(n): 100 for n in NODES},
                "files_sha256": {s.file_name(n): "e" * 64 for n in NODES},
            }
        },
    }
    expected = s.plan(NODES, current, 2, previous)
    assert expected["history_files_used"] and expected["inventory"] == sorted(NODES)
    for field in ("python", "machine", "packages"):
        altered = deepcopy(current)
        if field == "packages":
            altered["environment"][field]["pytest"] = "99.0.0"
        elif field == "python":
            altered["environment"][field] = "3.13.99"
        else:
            altered["environment"][field] = "different-native-machine"
        result = s.plan(NODES, altered, 2, previous)
        assert (
            result["inventory"] == sorted(NODES) and result["history_files_used"] == []
        )
        assert set(result["weights_ms"].values()) == {60_000}
    # A new candidate's own version is not a third-party runtime dependency.
    current["environment"]["packages"]["agent-wiki-cli"] = "2.0.0"
    current["identity"].update(version="2.0.0", tag="v2.0.0")
    assert s.plan(NODES, current, 2, previous)["history_files_used"]


def test_advisory_weights_never_admit_a_three_shard_qualification():
    with pytest.raises(s.q.QualificationError, match="two native"):
        s.plan(NODES, context(s.WINDOWS_LANE), 3, history(), purpose="qualification")


@pytest.mark.parametrize(
    "scope,count,expected",
    [("windows", 2, 2), ("windows", 3, 3), ("all", 2, 6), ("all", 3, 7)],
)
def test_shadow_matrix_bounds_exact_windows_profile_and_every_required_worker(
    scope, count, expected
):
    value = scheduling.matrices(
        ROOT,
        scope=scope,
        windows_shards=count,
        history="windows-trained",
        fixtures=True,
    )
    windows = [
        row for row in value["shards"]["include"] if row["lane"] == s.WINDOWS_LANE
    ]
    runtime = s.read(ROOT / "release/runtime-policy.json")["profiles"]["windows-core"][
        "python"
    ][0]
    assert len(value["shards"]["include"]) == expected and {
        r["shard"] for r in windows
    } == set(range(count))
    assert all(
        row["python"] == runtime and row["history"] == "windows-trained"
        for row in windows
    )
    assert all(
        row["shards"] == 2
        for row in value["reference"]["include"]
        if row["lane"] != s.WINDOWS_LANE
    )
    assert value["qualifying"] is False


@pytest.mark.parametrize("count", [True, 1, 4, 3.0, "3"])
def test_shadow_matrix_rejects_unbounded_or_untyped_layouts(count):
    with pytest.raises(ValueError):
        scheduling.matrices(
            ROOT,
            scope="windows",
            windows_shards=count,
            history="committed",
            fixtures=False,
        )


@pytest.mark.parametrize("time", ["NaN", "Infinity", "-1", "bad"])
def test_nonfinite_negative_or_missing_case_time_cannot_become_a_weight(time):
    with pytest.raises((ValueError, InvalidOperation)):
        scheduling.file_times({NODES[0]: ET.Element("testcase", time=time)})


def test_case_times_are_exact_decimal_milliseconds_at_file_boundaries():
    cases = {
        NODES[0]: ET.Element("testcase", time="0.001"),
        NODES[1]: ET.Element("testcase", time="0.002"),
    }
    assert scheduling.file_times(cases) == {"tests/test_one.py": 3}


def job(name, start=10, end=20, *, result="success", index=1):
    return {
        "name": name,
        "id": index,
        "run_id": 1,
        "run_attempt": 1,
        "head_sha": "a" * 40,
        "created_at": "2026-11-12T10:00:00Z",
        "started_at": f"2026-11-12T10:00:{start:02}Z",
        "completed_at": f"2026-11-12T10:00:{end:02}Z",
        "status": "completed",
        "conclusion": result,
    }


def test_job_clocks_do_not_mix_queue_span_runner_sum_or_first_failure():
    values = [
        job("Core reference (windows)", 1, 10),
        job("Core shard (windows, 0)", 12, 20, index=2),
        job("Core shard (windows, 1)", 15, 25, result="failure", index=3),
    ]
    result = scheduling.native_clocks(
        {"id": 1, "run_attempt": 1, "head_sha": "a" * 40}, values
    )
    assert result["workers"]["summed_runner_seconds"] == 18
    assert result["workers"]["elapsed_span_seconds"] == 13
    assert result["workers"]["execution_imbalance_seconds"] == 2
    assert result["workers"]["elapsed_after_reference_seconds"] == 15
    assert sorted(result["workers"]["queue_after_reference_seconds"].values()) == [2, 5]
    assert result["first_failed_producer"]["job_id"] == 3
    assert "unobserved" in result["first_case_failure_time"]


def trial(source, run_id, *, elapsed=100, cost=200, count=2):
    env = context(s.WINDOWS_LANE)["environment"]
    return {
        "schema_version": "agent-wiki-native-trial/v1",
        "qualifying": False,
        "run": {"id": run_id, "run_attempt": 1, "head_sha": source},
        "inventory_sha256": "c" * 64,
        "outcomes_sha256": "d" * 64,
        "options": {
            "reference": {
                "include": [
                    {
                        "shards": count,
                        "lane": s.WINDOWS_LANE,
                        "python": "3.13.17",
                        "history": "windows-trained",
                    }
                ]
            }
        },
        "comparison": {
            "passed": True,
            "complete": True,
            "context": {"environment": env},
            "runner_images": {
                "shards": {str(i): "same-native-image" for i in range(count)}
            },
        },
        "clocks": {
            "workers": {
                "pending": [],
                "first_failed_producer": None,
                "queue_after_reference_seconds": {str(i): 1 for i in range(count)},
                "elapsed_after_reference_seconds": elapsed,
                "summed_runner_seconds": cost,
            }
        },
    }


def test_rollout_requires_two_held_out_candidates_and_both_time_and_cost_targets():
    pairs = [
        {
            "control": trial("a" * 40, 1),
            "candidate": trial("a" * 40, 2, elapsed=75, cost=210, count=3),
        }
    ]
    assert (
        scheduling.compare_trials(pairs)["decision"] == "insufficient-held-out-samples"
    )
    pairs.append(
        {
            "control": trial("b" * 40, 3),
            "candidate": trial("b" * 40, 4, elapsed=78, cost=215, count=3),
        }
    )
    assert scheduling.compare_trials(pairs)["decision"] == "ready-for-review"
    pairs[1]["candidate"]["clocks"]["workers"]["summed_runner_seconds"] = 225
    assert scheduling.compare_trials(pairs)["decision"] == "keep-current-default"
    assert scheduling.compare_trials(pairs)["rollout_authority"] is False


@pytest.mark.parametrize(
    "fault",
    [
        "source",
        "runtime",
        "image",
        "outcome",
        "inventory",
        "incomplete",
        "queue",
        "duplicate",
    ],
)
def test_invalid_paired_native_samples_never_recommend_rollout(fault):
    control, candidate = trial("a" * 40, 1), trial("a" * 40, 2, count=3)
    if fault == "source":
        candidate["run"]["head_sha"] = "b" * 40
    elif fault == "runtime":
        candidate["comparison"]["context"]["environment"]["packages"]["coverage"] = (
            "different"
        )
    elif fault == "image":
        candidate["comparison"]["runner_images"]["shards"]["0"] = "another-image"
    elif fault == "outcome":
        candidate["outcomes_sha256"] = "e" * 64
    elif fault == "inventory":
        candidate["inventory_sha256"] = "e" * 64
    elif fault == "incomplete":
        candidate["comparison"]["complete"] = False
    elif fault == "queue":
        candidate["clocks"]["workers"]["queue_after_reference_seconds"]["0"] = None
    else:
        candidate["run"]["id"] = 1
    with pytest.raises(ValueError):
        scheduling.compare_trials([{"control": control, "candidate": candidate}])


def test_source_weights_read_original_git_objects_despite_replacement_refs(tmp_path):
    import hashlib
    import subprocess
    from tests.test_preflight import _git

    root = tmp_path / "repo"
    (root / "tests").mkdir(parents=True)
    path = root / "tests/test_observed.py"
    path.write_bytes(b"def test_observed(): assert True\n")
    original = path.read_bytes()
    _git(root, "init", "-q")
    _git(root, "add", ".")
    _git(root, "commit", "-qm", "observed source")
    source = _git(root, "rev-parse", "HEAD")
    path.write_bytes(b"def test_replacement(): assert False\n")
    _git(root, "add", ".")
    _git(root, "commit", "-qm", "replacement source")
    replacement = _git(root, "rev-parse", "HEAD")
    subprocess.run(["git", "replace", source, replacement], cwd=root, check=True)
    assert scheduling._source_hashes(root, source, {"tests/test_observed.py"}) == {
        "tests/test_observed.py": hashlib.sha256(original).hexdigest()
    }


@pytest.mark.parametrize(
    "field,value",
    [
        ("id", 2),
        ("run_attempt", 2),
        ("head_branch", "fork"),
        ("event", "pull_request"),
        ("status", "in_progress"),
        ("path", "another-workflow"),
    ],
)
def test_capture_refuses_wrong_run_before_downloading_evidence(tmp_path, field, value):
    from types import SimpleNamespace
    from tests.test_preflight import _git

    root = tmp_path / "repo"
    root.mkdir()
    _git(root, "init", "-q")
    (root / ".gitignore").write_text("reports/\n")
    run = {
        "id": 1,
        "run_attempt": 1,
        "status": "completed",
        "event": "workflow_dispatch",
        "path": scheduling.hosted.WORKFLOW,
        "head_branch": "main",
        "repository": {"full_name": "owner/repo"},
        "head_repository": {"full_name": "owner/repo"},
    }
    run[field] = value
    client = SimpleNamespace(get=lambda _path: run)
    with pytest.raises(ValueError, match="run identity"):
        scheduling.capture(
            root, root / "reports/input", "owner/repo", 1, 1, client=client
        )
