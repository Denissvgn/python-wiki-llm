"""Confirmed provider startup recovery is specific and never repeats unknown writes."""

from copy import deepcopy
import json
from types import SimpleNamespace

import pytest

from release import manual_release as m
from tests.test_manual_release import Remote, session, backend
from tests.test_manual_release import project as project


class Recoverable(Remote):
    def startup_failure(self, state, pending, run_id, attempt):
        return {
            "confirmed": True,
            "candidate_sha": state["candidate_sha"],
            "operation_id": pending["operation_id"],
            "run_id": run_id,
            "attempt": attempt,
        }

    def _main(self, _state):
        return None


def test_disposition_does_not_dispatch_and_the_next_qualification_is_admitted_once(
    project, monkeypatch
):
    remote = Recoverable()
    controller, _ = session(project, remote)
    failed = controller.advance()
    identifier = failed["pending"]["operation_id"]
    failed["preflight_receipt"] = str(project / "private/receipt.json")
    controller.store.save(failed, "record-test-receipt")
    monkeypatch.setattr(
        m,
        "verified_preflight",
        lambda *_: {"sha256": "a" * 64, "path": failed["preflight_receipt"]},
    )
    result = controller.resolve_startup(
        identifier, 42, 1, "Confirmed empty provider startup"
    )
    assert (
        result["pending"] is None
        and result["phase"] == "prepared"
        and len(remote.writes) == 1
    )
    assert result["recoveries"][0]["dispatch_performed"] is False
    with pytest.raises(ValueError, match="active qualification"):
        controller.resolve_startup(identifier, 42, 1, "Do not duplicate disposition")
    remote.lose_before_accept = True
    remote.results.clear()
    resumed = controller.advance()
    assert resumed["pending"]["retry_from"]["operation_id"] == identifier
    assert resumed["pending"]["operation_id"] != identifier
    assert "startup_retry" not in resumed
    for _ in range(3):
        controller.advance()
    assert len(remote.writes) == 2


@pytest.mark.parametrize(
    "fault", ["missing", "jobs", "suite", "checks", "attempt", "wrong-run"]
)
def test_provider_evidence_must_prove_exact_original_zero_job_startup(
    project, monkeypatch, fault
):
    remote = Remote()
    controller, _ = session(project, remote)
    state = controller.advance()
    pending = state["pending"]
    api = backend(project, None)
    run = {
        "id": 42,
        "run_attempt": 1,
        "status": "completed",
        "conclusion": "startup_failure",
        "check_suite_id": 7,
    }
    suite = {
        "id": 7,
        "head_sha": state["candidate_sha"],
        "head_branch": "main",
        "status": "completed",
        "conclusion": "startup_failure",
        "app": {"slug": "github-actions"},
        "repository": {"full_name": api.repository},
    }
    jobs, checks = [], []
    if fault == "missing":
        run = None
    elif fault == "jobs":
        jobs = [{"id": 1}]
    elif fault == "suite":
        suite["conclusion"] = "failure"
    elif fault == "checks":
        checks = [{"id": 2}]
    elif fault == "attempt":
        run["run_attempt"] = 2
    else:
        run["id"] = 43
    monkeypatch.setattr(api, "_run", lambda *_a, **_kw: deepcopy(run))
    monkeypatch.setattr(
        api,
        "client",
        SimpleNamespace(
            get=lambda _path: suite,
            list=lambda _path, key: jobs if key == "jobs" else checks,
        ),
    )
    with pytest.raises(ValueError):
        api.startup_failure(state, pending, 42, 1)
    assert controller.store.load()["pending"]["operation_id"] == pending["operation_id"]


def test_lost_response_with_no_visible_run_remains_unresolved(project, monkeypatch):
    controller, _ = session(project, Remote())
    state = controller.advance()
    api = backend(project, None)
    monkeypatch.setattr(api, "_run", lambda *_a, **_kw: None)
    with pytest.raises(ValueError, match="no confirmed"):
        api.startup_failure(state, state["pending"], 42, 1)


def test_provider_startup_proof_reads_exact_run_and_suite_without_persisting_observations(project, monkeypatch):
    controller, _ = session(project, Remote())
    state = controller.advance()
    api = backend(project, None)
    run = {"id": 42, "run_attempt": 1, "name": "Release qualification",
           "head_sha": state["candidate_sha"], "head_branch": "main", "created_at": state["pending"]["started_at"],
           "event": "workflow_dispatch", "path": ".github/workflows/release-qualification.yml",
           "repository": {"full_name": api.repository}, "head_repository": {"full_name": api.repository},
           "status": "completed", "conclusion": "startup_failure", "check_suite_id": 7}
    suite = {"id": 7, "head_sha": state["candidate_sha"], "head_branch": "main", "status": "completed",
             "conclusion": "startup_failure", "app": {"slug": "github-actions"}, "repository": {"full_name": api.repository}}
    reads = []

    def get(path):
        reads.append(path)
        return deepcopy(run if path == "/actions/runs/42" else suite)

    def listing(path, key):
        reads.append(path)
        return [run] if key == "workflow_runs" else []

    monkeypatch.setattr(api, "client", SimpleNamespace(get=get, list=listing))
    before = {p: p.read_bytes() for p in project.rglob("*") if p.is_file() and ".git" not in p.parts}
    proof = api.startup_failure(state, state["pending"], 42, 1)
    assert proof["confirmed"] is True and proof["run_sha256"] == m.digest(m.canonical(run))
    assert "/actions/runs/42/attempts/1/jobs" in reads and "/check-suites/7/check-runs" in reads
    assert before == {p: p.read_bytes() for p in project.rglob("*") if p.is_file() and ".git" not in p.parts}


@pytest.mark.parametrize("fault", ["missing-receipt", "stale-receipt", "moving-main", "wrong-operation"])
def test_startup_disposition_keeps_original_pending_when_readmission_prerequisites_fail(project, monkeypatch, fault):
    remote = Recoverable()
    controller, _ = session(project, remote)
    state = controller.advance()
    identifier = state["pending"]["operation_id"]
    if fault != "missing-receipt":
        state["preflight_receipt"] = str(project / "private/current-receipt.json")
        controller.store.save(state, "record-test-receipt")

    def verify(*args):
        if fault == "stale-receipt":
            raise ValueError("stale local receipt")
        return {"sha256": "a" * 64}

    def main(_state):
        if fault == "moving-main":
            raise ValueError("Main advanced")

    monkeypatch.setattr(m, "verified_preflight", verify)
    monkeypatch.setattr(remote, "_main", main)
    before = (controller.store.work / "state.json").read_bytes()
    with pytest.raises(ValueError):
        controller.resolve_startup("f" * 32 if fault == "wrong-operation" else identifier, 42, 1, "Provider startup failure")
    assert (controller.store.work / "state.json").read_bytes() == before
    assert json.loads(before)["pending"]["operation_id"] == identifier and len(remote.writes) == 1
