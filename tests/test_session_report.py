"""Read-only operation identity, independent failures and evidence-only packets."""

from copy import deepcopy
from datetime import datetime, timedelta
import json
from types import SimpleNamespace

import pytest

from release import manual_release as m, session_report as report, preflight
from tests.test_manual_release import Remote, git, session
from tests.test_manual_release import project as project
from tests.test_preflight import (
    _review_record,
    local_receipt as local_receipt,
    planned_project as planned_project,
)


@pytest.fixture
def recorded(project):
    path = project / ".github/workflows/release-qualification.yml"
    path.parent.mkdir(parents=True)
    path.write_text("""name: Release qualification
jobs:
  freeze: {name: Freeze}
  action: {name: Action, needs: freeze}
  knowledge-maintenance: {name: Knowledge health, needs: freeze}
  core-windows-shards:
    name: Windows shard (${{ matrix.shard }})
    needs: freeze
    strategy: {matrix: {shard: [0, 1]}}
  core-windows: {name: Windows core, needs: core-windows-shards}
  owner-lanes: {name: Skip owners, needs: [knowledge-maintenance, core-windows]}
  decision: {name: Aggregate, needs: [owner-lanes, action]}
""")
    git(project, "add", ".")
    git(project, "commit", "-qm", "workflow")
    remote = Remote()
    controller, state = session(project, remote, scopes=("qualify",))
    state = controller.advance()
    start = datetime.fromisoformat(state["pending"]["started_at"])
    run = {
        "id": 42,
        "run_attempt": 1,
        "name": "Release qualification",
        "head_sha": state["candidate_sha"],
        "head_branch": "main",
        "path": ".github/workflows/release-qualification.yml",
        "event": "workflow_dispatch",
        "status": "in_progress",
        "conclusion": None,
        "created_at": start.isoformat(),
        "repository": {"id": 1, "full_name": state["repository"]},
        "head_repository": {"id": 1, "full_name": state["repository"]},
        "environment": {"TOKEN": "do-not-export-server-environment"},
    }

    def job(
        index, name, status="completed", conclusion: str | None = "success", end=10
    ):
        return {
            "id": index,
            "run_id": 42,
            "run_attempt": 1,
            "head_sha": state["candidate_sha"],
            "name": name,
            "status": status,
            "conclusion": conclusion,
            "started_at": start.isoformat(),
            "completed_at": (start + timedelta(seconds=end)).isoformat()
            if status == "completed"
            else None,
            "environment": {"TOKEN": "do-not-export-job-environment"},
        }

    jobs = [
        job(1, "Freeze"),
        job(2, "Knowledge health", conclusion="failure", end=12),
        job(3, "Windows shard (0)", conclusion="failure", end=90),
        job(4, "Windows shard (1)", "in_progress", None),
        job(5, "Windows core", conclusion="failure", end=100),
        job(6, "Skip owners", conclusion="failure", end=101),
        job(7, "Aggregate", conclusion="failure", end=102),
    ]

    class Reader:
        def get(self, path):
            assert path == "/actions/runs/42"
            return deepcopy(run)

        def list(self, path, key):
            assert path == "/actions/runs/42/attempts/1/jobs" and key == "jobs"
            return deepcopy(jobs)

        def request(self, *_a, **_kw):
            raise AssertionError("report attempted a remote write")

    return controller, state, remote, run, jobs, Reader()


def file_map(root):
    return {
        str(p.relative_to(root)): p.read_bytes() for p in root.rglob("*") if p.is_file()
    }


def test_timeline_does_not_change_state_events_lease_or_dispatch(recorded):
    controller, _, remote, *_rest, reader = recorded
    before = file_map(controller.store.work)
    lease = controller.store.lease.read_bytes()
    result = report.timeline(controller.store, client=reader)
    assert (
        file_map(controller.store.work) == before
        and controller.store.lease.read_bytes() == lease
    )
    assert len(remote.writes) == 1
    operation = result["operations"][0]
    assert (
        operation["key"]["operation_id"]
        == controller.store.load()["pending"]["operation_id"]
    )
    assert operation["key"]["run_id"] == 42 and operation["key"]["attempt"] == 1
    failures = operation["producers"]
    assert failures["first_independent_failure"]["name"] == "Knowledge health"
    assert [r["name"] for r in failures["additional_independent_failures"]] == [
        "Windows shard (0)"
    ]
    assert failures["pending_jobs"] == [
        {"job_id": 4, "name": "Windows shard (1)", "status": "in_progress"}
    ]
    aggregates = [
        r for r in failures["all_failures"] if r["category"] == "downstream-aggregate"
    ]
    assert {r["name"] for r in aggregates} == {
        "Windows core",
        "Skip owners",
        "Aggregate",
    }
    assert (
        result["publication_authority"] is False
        and result["completion"]["recorded_public_verification"] is False
    )


def test_packet_is_keyed_to_one_operation_and_excludes_server_environment(recorded):
    controller, _, _, *_rest, reader = recorded
    value = report.timeline(controller.store, client=reader)
    output = controller.store.root / "private/packet"
    operation = value["operations"][0]
    result = report.packet(
        controller.store.root, output, value, operation["operation_id"]
    )
    raw = (output / "diagnostic.json").read_text()
    assert (
        "do-not-export" not in raw
        and "environment" not in json.loads(raw)["operation"]["observation"]["run"]
    )
    manifest = json.loads((output / "manifest.json").read_bytes())
    assert manifest["key"] == result["key"] == operation["key"]
    assert manifest["files"]["diagnostic.json"]["sha256"] == m.digest(
        (output / "diagnostic.json").read_bytes()
    )
    with pytest.raises(ValueError, match="occupied"):
        report.packet(controller.store.root, output, value, operation["operation_id"])


def test_same_sha_repeated_dispatches_remain_distinct(recorded):
    controller, state, *_ = recorded
    first = deepcopy(state["pending"])
    state["pending"] = {
        **first,
        "operation_id": "b" * 32,
        "response": {"workflow_run_id": 43},
        "started_at": (
            datetime.fromisoformat(first["started_at"]) + timedelta(seconds=1)
        ).isoformat(),
    }
    controller.store.save(state, "intent-qualify")
    rows = report.timeline(controller.store)["operations"]
    assert len(rows) == 2 and {r["key"]["run_id"] for r in rows} == {42, 43}
    ids = []
    for i, row in enumerate(rows):
        packet = report.packet(
            controller.store.root,
            controller.store.root / f"private/packet-{i}",
            report.timeline(controller.store),
            row["operation_id"],
        )
        ids.append(packet["packet_id"])
    assert len(set(ids)) == 2


@pytest.mark.parametrize(
    "field", ["head_sha", "head_branch", "run_attempt", "repository"]
)
def test_mismatched_run_is_not_adopted(recorded, field):
    controller, state, _, run, jobs, _ = recorded
    run[field] = (
        {"full_name": "fork/repo", "id": 2}
        if field == "repository"
        else 2
        if field == "run_attempt"
        else "different"
    )
    operation = report.operations(state, report.snapshot(controller.store)["events"])[0]
    with pytest.raises(ValueError, match="another operation"):
        report.bind_observation(state, operation, run, jobs)


def test_superseded_api_attempt_is_read_at_the_original_attempt(recorded):
    controller, _, _, original, jobs, _ = recorded

    class Reader:
        def get(self, path):
            return (
                {**original, "run_attempt": 2}
                if path == "/actions/runs/42"
                else deepcopy(original)
            )

        def list(self, path, key):
            assert "/attempts/1/jobs" in path
            return deepcopy(jobs)

    result = report.timeline(controller.store, client=Reader())
    observed = result["operations"][0]["observation"]
    assert (
        observed["historical_attempt"] is True
        and observed["attempt"] == 1
        and observed["latest_attempt"] == 2
    )


def test_unknown_dispatch_response_is_never_permission_for_another_post(project):
    remote = Remote()
    remote.lose_before_accept = True
    controller, _ = session(project, remote)
    state = controller.advance()
    reader = SimpleNamespace(list=lambda *_: [])
    operation = report.operations(state, report.snapshot(controller.store)["events"])[0]
    value = report.observe(state, operation, reader)
    assert (
        value["status"] == "unresolved-dispatch" and value["retry_authority"] is False
    )
    assert (
        len(remote.writes) == 1
        and controller.store.load()["pending"]["outcome_unknown"] is True
    )


def test_journal_tail_and_ahead_of_state_are_explicit_not_controller_state(recorded):
    controller, state, *_ = recorded
    path = controller.store.work / "events.jsonl"
    with path.open("ab") as stream:
        stream.write(
            json.dumps(
                {
                    "revision": state["revision"] + 1,
                    "time": m.now(),
                    "event": "intent-qualify",
                    "phase": "prepared",
                }
            ).encode()
            + b"\n"
        )
        stream.write(b'{"incomplete":')
    result = report.timeline(controller.store)
    assert result["events"][-1]["ahead_of_state"] is True
    assert result["warnings"][-1]["kind"] == "incomplete-journal-tail"
    assert result["session"]["revision"] == state["revision"]


@pytest.mark.parametrize("status", [404, 502, 503, 504, 401, 403])
def test_observation_failure_preserves_operation_and_does_not_retry_dispatch(recorded, status):
    controller, _, remote, *_ = recorded
    before = file_map(controller.store.work)

    def unavailable(_path):
        raise report.automation.APIError(status, "unavailable")

    reader = SimpleNamespace(get=unavailable)
    if status in {401, 403}:
        with pytest.raises(report.automation.APIError):
            report.timeline(controller.store, client=reader)
    else:
        value = report.timeline(controller.store, client=reader)
        assert value["operations"][0]["observation"] == {"status": "remote-observation-unavailable", "http_status": status, "retry_authority": False}
    assert before == file_map(controller.store.work) and len(remote.writes) == 1


def test_original_git_workflow_ignores_replacement_objects(recorded):
    controller, state, *_ = recorded
    original = report.declaration(controller.store.root, state["candidate_sha"], "qualify")
    path = controller.store.root / ".github/workflows/release-qualification.yml"
    path.write_text("name: Forged workflow\njobs: {forged: {name: Forged}}\n")
    git(controller.store.root, "add", ".")
    git(controller.store.root, "commit", "-qm", "Different dependency graph")
    replacement = git(controller.store.root, "rev-parse", "HEAD")
    git(controller.store.root, "replace", state["candidate_sha"], replacement)
    assert report.declaration(controller.store.root, state["candidate_sha"], "qualify") == original


def test_host_completion_does_not_establish_unknown_native_targets(local_receipt):
    root, work, _partial_path, _partial_value = local_receipt
    # Execute all stages through the bounded stand-in, rather than relabeling
    # the deliberately partial receipt supplied by local_receipt.
    source = _partial_value["plan"]["candidate_sha"]
    review_path = root / "private/review.json"
    preflight.write_document(review_path, _review_record(source), root=root)
    plan = preflight.create_plan(root, source, review_file=review_path)
    preflight.write_document(root / "private/complete-plan.json", plan, root=root)
    result = preflight.run_plan(root / "private/complete-plan.json", work)
    receipt_path = work / result["receipt_path"]
    value = preflight.read_document(receipt_path)
    target = {
        "status": "unknown",
        "target_execution_verified": False,
        "rows": [
            {
                "owner": "qualification#action",
                "state": "unknown",
                "reasons": ["target-machine-not-declared"],
            }
        ],
    }
    value["plan"]["binding"]["maintenance"] = {
        "mode": "required",
        "target_runtime": target,
    }
    value["plan"] = preflight._sealed(
        {k: v for k, v in value["plan"].items() if k != "plan_hash"}, "plan_hash"
    )
    value = preflight._sealed(
        {k: v for k, v in value.items() if k != "receipt_hash"}, "receipt_hash"
    )
    receipt_path.write_bytes(json.dumps(value).encode())
    result = report.local_preparation(
        {
            "preflight_receipt": str(receipt_path),
            "candidate_sha": value["plan"]["candidate_sha"],
            "root": str(root),
        }
    )
    assert result["host_stages"]["complete"] is True
    assert (
        result["target_proof"]["status"] == "unknown"
        and result["target_proof"]["rows"] == target["rows"]
    )
    assert (
        result["integrity"] == "sealed-record-only"
        and result["target_proof"]["fresh_native_proof_required"] is True
    )


def test_progress_cache_is_read_only_and_session_revision_bound(recorded):
    controller, _, state, *_ = recorded
    current = controller.store.load()
    controller.store.record_progress({
        **current, "observation": "remote-running",
        "remote": {"run_id":42,"attempt":1,"active_jobs":["native core"],"failed_jobs":[]},
    })
    first = report.timeline(controller.store)["handoff"]
    assert first["active_jobs"] == ["native core"] and first["observed_at"]
    assert first["pending_operation_id"] == current["pending"]["operation_id"]
    cache = controller.store.work / "progress.json"
    value = json.loads(cache.read_bytes())
    cache.write_text(json.dumps({**value, "revision":current["revision"]-1}))
    assert report.timeline(controller.store)["handoff"]["observation_status"] == "not-observed"
