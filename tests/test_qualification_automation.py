"""Offline state-machine coverage for privileged release coordination."""

from __future__ import annotations

import base64
from copy import deepcopy
from email.message import Message
import hashlib
import io
import json
from pathlib import Path
import subprocess
import sys
import shutil
from types import SimpleNamespace
from typing import Any
import zipfile

import pytest

from release import qualification_automation as qa

REPOSITORY = "owner/project"
CANDIDATE = "a" * 40
NEXT = "b" * 40
BOT = {"login": "release-bot", "id": 123}
CONFIG = {"schema_version": qa.CONFIG_SCHEMA, "enabled": True, "trusted_bot": {**BOT, "check_app_id": 777}}
ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def policy_root(tmp_path):
    for name in (*qa.maintenance.POLICY_INPUTS, qa.maintenance.POLICY_PATH):
        target = tmp_path / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes((ROOT / name).read_bytes())
    config = json.loads((tmp_path / qa.maintenance.POLICY_PATH).read_bytes())
    config["activation"]["implementation_sha256"] = "0" * 64
    (tmp_path / qa.maintenance.POLICY_PATH).write_bytes(qa.canonical(config))
    return tmp_path


def workflow_run(sha=CANDIDATE, *, run_id=10, qualification=False, conclusion="success", event=None, attempt=1):
    profile = "policy-shadow"
    return {"id": run_id, "run_attempt": attempt, "head_sha": sha, "head_branch": "codex/qualification/" + sha if qualification else "main",
            "repository": {"full_name": REPOSITORY, "id": 44}, "head_repository": {"full_name": REPOSITORY, "id": 44},
            "workflow_id": 2 if qualification else 1, "path": qa.QUALIFICATION_PATH if qualification else qa.CI_PATH,
            "name": "Release qualification" if qualification else "CI", "status": "completed", "conclusion": conclusion,
            "event": event or ("workflow_dispatch" if qualification else "push"), "pull_requests": [],
            "display_title": f"Release qualification [{qa.request_id(REPOSITORY, sha, profile)}]" if qualification else "CI"}


class FakeGitHub:
    """API fake stores refs, contents, run attempts, and check-run receipts."""

    def __init__(self, root):
        self.main_sha = CANDIDATE
        self.contents = {CANDIDATE: {name: (root / name).read_bytes() for name in (*qa.maintenance.POLICY_INPUTS, qa.maintenance.POLICY_PATH)}}
        self.refs = {"main": CANDIDATE}
        self.runs = {10: workflow_run()}
        self.rules = {"id": 1, "enforcement": "active", "target": "branch", "bypass_actors": [],
                      "conditions": {"ref_name": {"include": ["refs/heads/main"], "exclude": []}},
                      "rules": [{"type": "required_status_checks", "parameters": {"strict_required_status_checks_policy": True,
                      "required_status_checks": [{"context": x} for x in qa.REQUIRED_CHECKS]}},
                      {"type": "pull_request", "parameters": {"required_approving_review_count": 0}},
                      {"type": "non_fast_forward"}, {"type": "deletion"}]}
        self.auto_merge = True
        self.bot = BOT.copy()
        self.checks = []
        self.mutations = []
        self.pulls = {}
        self.blobs = {}
        self.trees = {"tree-main": {}}
        self.commits: dict[str, Any] = {CANDIDATE: {"tree": {"sha": "tree-main"}}}
        self.archives = {}
        self.artifacts = []
        self.jobs = []
        self.dispatch_error = False

    def get_user(self):
        return self.bot

    def get(self, path):
        if path == "/":
            return {"full_name": REPOSITORY, "allow_auto_merge": self.auto_merge}
        if path.startswith("/git/ref/heads/"):
            branch = path.removeprefix("/git/ref/heads/")
            sha = self.main_sha if branch == "main" else self.refs.get(branch)
            if sha is None:
                raise qa.APIError(404, "no ref")
            return {"ref": "refs/heads/" + branch, "object": {"type": "commit", "sha": sha}}
        if path.startswith("/contents/"):
            name, _, ref = path.removeprefix("/contents/").partition("?ref=")
            ref = qa.urllib.parse.unquote(ref)
            ref = self.refs.get(ref, ref)
            raw = self.contents[ref][name]
            return {"type": "file", "encoding": "base64", "size": len(raw), "content": base64.b64encode(raw).decode()}
        if path.startswith("/actions/workflows/"):
            identifier = path.rsplit("/", 1)[-1]
            return {"id": int(identifier), "path": qa.CI_PATH if identifier == "1" else qa.QUALIFICATION_PATH,
                    "name": "CI" if identifier == "1" else "Release qualification"}
        if path.startswith("/actions/runs/"):
            run_id = int(path.split("/")[3])
            return deepcopy(self.runs[run_id])
        if path == "/rulesets/1":
            return self.rules
        if path.startswith("/git/commits/"):
            return self.commits[path.rsplit("/", 1)[-1]]
        if path.startswith("/pulls/"):
            return deepcopy(self.pulls[int(path.split("/")[2])])
        raise AssertionError(f"unexpected GET {path}")

    def list(self, path, key=None):
        if path.startswith("/rulesets"):
            return [{"id": 1}]
        if path.startswith("/commits/"):
            sha = path.split("/")[2]
            return [deepcopy(x) for x in self.checks if x["head_sha"] == sha]
        if path.startswith("/actions/workflows/") and "/runs?" in path:
            sha = path.split("head_sha=", 1)[1].split("&")[0]
            event = path.split("event=", 1)[1]
            return [deepcopy(x) for x in self.runs.values() if x["head_sha"] == sha and x["event"] == event]
        if path.startswith("/pulls?"):
            return [deepcopy(x) for x in self.pulls.values() if x["state"] == "open"]
        if path.endswith("/artifacts"):
            return deepcopy(self.artifacts)
        if path.endswith("/jobs"):
            return deepcopy(self.jobs)
        raise AssertionError(f"unexpected LIST {path}")

    def archive(self, artifact_id):
        return self.archives[artifact_id]

    def request(self, method, path, payload: Any = None):
        self.mutations.append((method, path, deepcopy(payload)))
        if path == "/check-runs":
            row = {"id": len(self.checks) + 100, "app": {"id": 777}, **deepcopy(payload)}
            self.checks.append(row)
            return deepcopy(row)
        if path.startswith("/check-runs/"):
            row = next(x for x in self.checks if x.get("id") == int(path.rsplit("/", 1)[-1]))
            row.update(deepcopy(payload))
            return deepcopy(row)
        if path == "/git/refs":
            branch = payload["ref"].removeprefix("refs/heads/")
            self.refs[branch] = payload["sha"]
            return {"ref": payload["ref"], "object": {"sha": payload["sha"]}}
        if path.startswith("/git/refs/heads/"):
            branch = path.removeprefix("/git/refs/heads/")
            self.refs[branch] = payload["sha"]
            for pr in self.pulls.values():
                if pr["head"]["ref"] == branch:
                    pr["head"]["sha"] = payload["sha"]
            return {}
        if path.endswith("/dispatches"):
            if self.dispatch_error:
                raise qa.AutomationError("lost response")
            run_id = 20 + sum(x[1].endswith("/dispatches") for x in self.mutations)
            run = workflow_run(payload["inputs"]["candidate-sha"], qualification=True, run_id=run_id)
            run["display_title"] = f"Release qualification [{payload['inputs']['automation-request-id']}]"
            self.runs[run_id] = run
            return {"workflow_run_id": run_id}
        if path == "/git/blobs":
            raw = base64.b64decode(payload["content"])
            sha = hashlib.sha1(raw).hexdigest()
            self.blobs[sha] = raw
            return {"sha": sha}
        if path == "/git/trees":
            sha = hashlib.sha1(qa.canonical(payload)).hexdigest()
            self.trees[sha] = {x["path"]: self.blobs[x["sha"]] for x in payload["tree"]}
            return {"sha": sha}
        if path == "/git/commits":
            sha = hashlib.sha1(qa.canonical(payload)).hexdigest()
            self.commits[sha] = {"tree": {"sha": payload["tree"]}, "parents": [{"sha": x} for x in payload["parents"]]}
            self.contents[sha] = {**self.contents[payload["parents"][0]], **self.trees[payload["tree"]]}
            return {"sha": sha}
        if path == "/pulls":
            number = len(self.pulls) + 1
            self.pulls[number] = {"number": number, "node_id": f"PR_node_{number}", "mergeable_state": "clean", "user": self.bot, "state": "open", "head": {"ref": payload["head"], "sha": self.refs[payload["head"]]},
                                  "base": {"ref": "main", "sha": self.main_sha}}
            return deepcopy(self.pulls[number])
        if path.endswith("/merge"):
            number = int(path.split("/")[2])
            self.pulls[number]["state"] = "closed"
            self.main_sha = self.pulls[number]["head"]["sha"]
            return {"merged": True, "sha": self.main_sha}
        raise AssertionError(f"unexpected {method} {path}")

    def enable_auto_merge(self, node_id, head):
        pr = next(value for value in self.pulls.values() if value["node_id"] == node_id)
        assert pr["head"]["sha"] == head
        self.mutations.append(("GRAPHQL", "enablePullRequestAutoMerge", {"pullRequestId": node_id, "expectedHeadOid": head}))
        pr["auto_merge"] = {"merge_method": "squash"}
        return pr


@pytest.fixture
def controller(policy_root, monkeypatch):
    client = FakeGitHub(policy_root)
    monkeypatch.setattr(qa.qualification, "_run", lambda *args, **kw: SimpleNamespace(stdout=client.main_sha + "\n"))
    value = qa.Coordinator(policy_root, REPOSITORY, client, writer=client, apply=True, config=deepcopy(CONFIG),
        eligibility_check=lambda root: {"status": "eligible", "version": "9.9.9"})
    return value


def activate(controller):
    state = controller.policy_at(CANDIDATE)
    config = state["configuration"]
    config["activation"]["implementation_sha256"] = state["implementation_sha256"]
    controller.client.contents[CANDIDATE][qa.maintenance.POLICY_PATH] = qa.canonical(config)


def shadow_proof(controller, receipt):
    digest = controller.policy_at(CANDIDATE)["implementation_sha256"]
    activation = {"proof_source_sha": CANDIDATE, "run_id": receipt["run_id"], "attempt": 1,
                  "implementation_sha256": digest, "comparison_sha256": "e" * 64}
    from release.policy_activation import configuration_contract
    return {"activation": activation, "audit": {"repository": REPOSITORY, "implementation_sha256": digest,
            "request_id": receipt["request_id"], "configuration": configuration_contract(controller.policy_at(CANDIDATE)["configuration"])}}


@pytest.mark.parametrize("current", [False, True])
def test_inspection_uses_explicit_activation_fixture(policy_root, current):
    state = qa.inspect(policy_root)
    assert state["status"] == "stale"
    if current:
        config = json.loads((policy_root / qa.maintenance.POLICY_PATH).read_bytes())
        config["activation"]["implementation_sha256"] = state["implementation_sha256"]
        (policy_root / qa.maintenance.POLICY_PATH).write_bytes(qa.canonical(config))
        assert qa.inspect(policy_root)["status"] == "current"


@pytest.mark.parametrize("value", [None, 10, "garbage", "A" * 64])
def test_malformed_policy_never_becomes_stale(policy_root, value):
    config = json.loads((policy_root / qa.maintenance.POLICY_PATH).read_bytes())
    config["activation"]["implementation_sha256"] = value
    (policy_root / qa.maintenance.POLICY_PATH).write_bytes(qa.canonical(config))
    assert qa.inspect(policy_root)["status"] == "blocked_policy"


@pytest.mark.parametrize("mode", ["disabled", "shadow", "unsupported"])
def test_automatic_renewal_requires_required_mode(policy_root, mode):
    config = json.loads((policy_root / qa.maintenance.POLICY_PATH).read_bytes())
    config["mode"] = mode
    (policy_root / qa.maintenance.POLICY_PATH).write_bytes(qa.canonical(config))
    assert qa.inspect(policy_root)["status"] == "blocked_policy"


@pytest.mark.parametrize("broken", ["disabled", "token", "bot", "check_publisher", "automerge", "bypass", "missing_bypass_metadata", "checks", "strict", "ruleset", "pull_request", "non_fast_forward", "deletion"])
def test_setup_failures_do_not_mutate(controller, broken):
    if broken == "disabled":
        controller.config["enabled"] = False
    elif broken == "token":
        controller.writer = None
    elif broken == "bot":
        controller.client.bot = {"login": "different", "id": 222}
    elif broken == "check_publisher":
        controller.config["trusted_bot"]["check_app_id"] = None
    elif broken == "automerge":
        controller.client.auto_merge = False
    elif broken == "bypass":
        controller.client.rules["bypass_actors"] = [{"actor_id": 1}]
    elif broken == "missing_bypass_metadata":
        del controller.client.rules["bypass_actors"]
    elif broken == "checks":
        controller.client.rules["rules"][0]["parameters"]["required_status_checks"] = []
    elif broken == "strict":
        controller.client.rules["rules"][0]["parameters"]["strict_required_status_checks_policy"] = False
    elif broken in {"pull_request", "non_fast_forward", "deletion"}:
        controller.client.rules["rules"] = [x for x in controller.client.rules["rules"] if x["type"] != broken]
    else:
        controller.client.rules["enforcement"] = "disabled"
    result = controller.reconcile({"workflow_run": workflow_run()})
    assert result["status"] == "blocked_setup"
    assert not controller.client.mutations


def test_stale_binding_dispatches_bounded_shadow_independent_of_release_eligibility(controller):
    controller.eligibility_check = lambda root: pytest.fail("stale policy must renew between releases")
    result = controller.reconcile({"workflow_run": workflow_run()})
    assert result["status"] == "dispatched"
    assert result["profile"] == "policy-shadow"
    assert controller.client.refs["codex/qualification/" + CANDIDATE] == CANDIDATE
    dispatch = next(x[2] for x in controller.client.mutations if x[1].endswith("/dispatches"))
    assert set(dispatch) == {"ref", "inputs"}
    assert dispatch["inputs"]["knowledge-policy-shadow"] == "true"
    assert "qualification-profile" not in dispatch["inputs"]
    assert dispatch["inputs"]["windows-core-shards"] == "true"
    assert result["run_id"] in controller.client.runs


@pytest.mark.parametrize("status", ["waiting_release_preparation", "blocked_unavailable"])
def test_current_policy_waits_for_release_readiness(controller, status):
    activate(controller)
    controller.eligibility_check = lambda root: {"status": status, "version": "1.2.3", "reason": "not ready"}
    result = controller.reconcile({"workflow_run": workflow_run()})
    assert result["status"] == status
    assert not controller.client.mutations


def test_current_eligible_candidate_dispatches_normal(controller):
    activate(controller)
    result = controller.reconcile({"workflow_run": workflow_run()})
    assert result["profile"] == "normal"
    dispatch = next(x[2] for x in controller.client.mutations if x[1].endswith("/dispatches"))
    assert dispatch["inputs"]["knowledge-policy-shadow"] == "false"


def test_duplicate_event_reuses_exact_dispatch_receipt(controller):
    first = controller.reconcile({"workflow_run": workflow_run()})
    second = controller.reconcile({"workflow_run": workflow_run()})
    assert second["run_id"] == first["run_id"]
    assert sum(x[1].endswith("/dispatches") for x in controller.client.mutations) == 1


def test_unknown_dispatch_response_is_not_retried_automatically(controller):
    controller.client.dispatch_error = True
    result = controller.reconcile({"workflow_run": workflow_run()})
    assert result["status"] == "blocked_dispatch_unknown"
    assert controller.reconcile({"workflow_run": workflow_run()})["status"] == "blocked_dispatch_unknown"
    assert controller.reconcile({}, manual=True, retry=True)["status"] == "blocked_dispatch_unknown"
    assert sum(x[1].endswith("/dispatches") for x in controller.client.mutations) == 1


def test_conflicting_candidate_pin_is_never_moved(controller):
    controller.client.refs["codex/qualification/" + CANDIDATE] = NEXT
    result = controller.reconcile({"workflow_run": workflow_run()})
    assert result["status"] == "blocked"
    assert controller.client.refs["codex/qualification/" + CANDIDATE] == NEXT
    assert not controller.client.mutations


@pytest.mark.parametrize("field,value", [("event", "pull_request_target"), ("head_branch", "feature"), ("name", "Fake"), ("head_sha", "invalid")])
def test_untrusted_completion_is_rejected(controller, field, value):
    controller.client.runs[10][field] = value
    event = {"workflow_run": deepcopy(controller.client.runs[10])}
    assert controller.reconcile(event)["status"] == "blocked"
    assert not controller.client.mutations


def test_fork_repository_is_rejected(controller):
    controller.client.runs[10]["head_repository"]["full_name"] = "attacker/project"
    assert controller.reconcile({"workflow_run": controller.client.runs[10]})["status"] == "blocked"
    assert not controller.client.mutations


def test_failed_ci_does_not_dispatch(controller):
    controller.client.runs[10]["conclusion"] = "failure"
    assert controller.reconcile({"workflow_run": controller.client.runs[10]})["status"] == "blocked_ci"
    assert not controller.client.mutations


def test_superseded_main_completion_waits_for_new_ci(controller):
    controller.client.main_sha = NEXT
    result = controller.reconcile({"workflow_run": workflow_run()})
    assert result["status"] == "superseded"
    assert not controller.client.mutations


def test_manual_resume_requires_successful_exact_main_ci(controller):
    controller.client.runs.clear()
    assert controller.reconcile({}, manual=True)["status"] == "waiting_ci"
    assert not controller.client.mutations


def test_coordinator_replays_manual_approval_without_automatic_receipt(controller, monkeypatch):
    activation = {"proof_source_sha": CANDIDATE, "run_id": 123, "attempt": 1,
                  "implementation_sha256": "a" * 64, "comparison_sha256": "b" * 64}
    audit = {"request_id": None, "candidate_sha": CANDIDATE, "run_id": 123,
             "attempt": 1, "implementation_sha256": activation["implementation_sha256"]}
    verified = {"activation": deepcopy(activation), "audit": deepcopy(audit)}
    calls = []

    def verifier(*args, **kwargs):
        calls.append(kwargs)
        return deepcopy(verified)

    controller.shadow_verifier = verifier
    monkeypatch.setattr(controller, "content", lambda *args: qa.canonical(audit))
    monkeypatch.setattr(controller, "receipts", lambda *args: [])
    assert controller._verify_activation(activation) == verified
    assert calls[0]["main_proof"] is True
    activation["attempt"] = 2
    with pytest.raises(ValueError, match="matching manual audit"):
        controller._verify_activation(activation)
    assert len(calls) == 1
    assert not controller.client.mutations


@pytest.mark.parametrize("main_audit", ["missing", "prior-manual"])
def test_automatic_proof_uses_dispatch_receipt_without_main_audit(controller, monkeypatch, main_audit):
    receipt = controller.reconcile({"workflow_run": workflow_run()})
    verified = shadow_proof(controller, receipt)
    calls = []

    def verifier(*args, **kwargs):
        calls.append(kwargs)
        return deepcopy(verified)

    controller.shadow_verifier = verifier
    audit_reads = []

    def content(*args):
        audit_reads.append(args)
        if main_audit == "missing":
            raise qa.APIError(404, "audit exists only on PR head")
        return qa.canonical({"request_id": None, "candidate_sha": CANDIDATE,
                             "run_id": receipt["run_id"] - 1})

    monkeypatch.setattr(controller, "content", content)
    assert controller._verify_activation(verified["activation"]) == verified
    assert calls[0]["request_id"] == receipt["request_id"]
    assert "main_proof" not in calls[0]
    assert audit_reads == []


def test_failed_qualification_requires_explicit_retry(controller):
    result = controller.reconcile({"workflow_run": workflow_run()})
    run = controller.client.runs[result["run_id"]]
    run["conclusion"] = "failure"
    assert controller.reconcile({"workflow_run": run})["status"] == "failed"
    assert controller.reconcile({}, manual=True)["status"] == "failed"
    assert controller.reconcile({}, manual=True, retry=True)["status"] == "dispatched"
    assert sum(x[1].endswith("/dispatches") for x in controller.client.mutations) == 2


def test_request_title_is_required_to_correlate_run(controller):
    result = controller.reconcile({"workflow_run": workflow_run()})
    run = controller.client.runs[result["run_id"]]
    run["display_title"] = "Release qualification [different]"
    assert controller.reconcile({"workflow_run": run})["status"] == "blocked"


def test_shadow_success_creates_only_activation_and_audit_changes(controller):
    receipt = controller.reconcile({"workflow_run": workflow_run()})
    proof = shadow_proof(controller, receipt)
    controller.shadow_verifier = lambda *args, **kw: deepcopy(proof)
    run = controller.client.runs[receipt["run_id"]]
    result = controller.reconcile({"workflow_run": run})
    assert result["status"] == "waiting_activation_checks"
    assert len(controller.client.pulls) == 1
    tree = next(x[2] for x in controller.client.mutations if x[1] == "/git/trees")
    assert {x["path"] for x in tree["tree"]} == {qa.maintenance.POLICY_PATH, qa.AUDIT_PREFIX + proof["activation"]["implementation_sha256"] + ".json"}
    head = result["activation_head"]
    updated = json.loads(controller.client.contents[head][qa.maintenance.POLICY_PATH])
    previous = json.loads(controller.client.contents[CANDIDATE][qa.maintenance.POLICY_PATH])
    assert {k: v for k, v in updated.items() if k != "activation"} == {k: v for k, v in previous.items() if k != "activation"}
    count = len(controller.client.mutations)
    again = controller.reconcile({"workflow_run": run})
    assert again["activation_head"] == head
    assert len(controller.client.mutations) == count


def test_invalid_shadow_evidence_is_saved_and_not_redispatched(controller):
    receipt = controller.reconcile({"workflow_run": workflow_run()})
    def reject(*args, **kwargs):
        raise ValueError("doctor parity differs")
    controller.shadow_verifier = reject
    result = controller.reconcile({"workflow_run": controller.client.runs[receipt["run_id"]]})
    assert result["status"] == "blocked_evidence"
    assert "doctor parity" in result["reason"]
    assert controller.reconcile({}, manual=True)["status"] == "blocked_evidence"


def test_dry_reconciliation_performs_no_mutations(controller):
    controller.apply = False
    result = controller.reconcile({"workflow_run": workflow_run()})
    assert result["status"] == "planned_dispatch"
    assert not controller.client.mutations


def test_isolated_entrypoint_and_disabled_default(tmp_path):
    checkout = tmp_path / "checkout"
    (checkout / "release").mkdir(parents=True)
    for name in ("qualification_automation.py", "qualification.py", "hosted_evidence.py", "knowledge_maintenance.py"):
        shutil.copyfile(ROOT / "release" / name, checkout / "release" / name)
    config = deepcopy(CONFIG)
    config["enabled"] = False
    (checkout / "release/automation.json").write_bytes(qa.canonical(config))
    assert not (checkout / ".venv").exists()
    result = subprocess.run([sys.executable, "-I", str(checkout / "release/qualification_automation.py"), "reconcile", "--root", str(checkout)],
                            capture_output=True, text=True, cwd=tmp_path)
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)["status"] == "blocked_setup"


def test_full_activation_sequence_requires_exact_head_checks(controller, monkeypatch):
    receipt = controller.reconcile({"workflow_run": workflow_run()})
    proof = shadow_proof(controller, receipt)
    controller.shadow_verifier = lambda *args, **kw: deepcopy(proof)
    proposal = controller.reconcile({"workflow_run": controller.client.runs[receipt["run_id"]]})
    pr = controller.client.pulls[proposal["pull_request"]]
    head = pr["head"]["sha"]
    pr_run = workflow_run(head, run_id=30, event="pull_request")
    pr_run["pull_requests"] = [{"number": pr["number"]}]
    controller.client.runs[30] = pr_run
    controller.validate_pr = lambda *args, **kw: {"status": "pass"}
    assert controller.reconcile({"workflow_run": pr_run})["status"] == "blocked"
    assert controller.client.main_sha == CANDIDATE
    for name in qa.REQUIRED_CHECKS:
        controller.client.checks.append({"name": name, "head_sha": head, "status": "completed", "conclusion": "success"})
    merged = controller.reconcile({"workflow_run": pr_run})
    assert merged["status"] == "activation_merged"
    main_run = workflow_run(merged["candidate_sha"], run_id=40)
    controller.client.runs[40] = main_run
    normal = controller.reconcile({"workflow_run": main_run})
    assert normal["status"] == "dispatched" and normal["profile"] == "normal", normal
    assert sum(x[1].endswith("/dispatches") for x in controller.client.mutations) == 2


def test_normal_artifact_identity_and_archive_digest_are_checked(controller):
    activate(controller)
    receipt = controller.reconcile({"workflow_run": workflow_run()})
    run = controller.client.runs[receipt["run_id"]]
    controller.client.artifacts = [{"id": 3, "name": "qualified-release", "expired": False, "digest": "sha256:" + "0" * 64,
                                    "workflow_run": {"id": run["id"], "head_sha": CANDIDATE, "repository_id": 44, "head_repository_id": 44}}]
    controller.client.archives[3] = b"tampered"
    result = controller.reconcile({"workflow_run": run})
    assert result["status"] == "blocked_evidence"
    assert "archive digest" in result["reason"]


def test_normal_completion_records_verified_artifact_and_is_terminal(controller, monkeypatch):
    activate(controller)
    receipt = controller.reconcile({"workflow_run": workflow_run()})
    run = controller.client.runs[receipt["run_id"]]
    manifest = {"repository": REPOSITORY, "workflow_run_id": run["id"], "source": {"sha": CANDIDATE}, "qualification_context": {"run_attempt": 1}, "version": "9.9.9"}
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, "w") as archive:
        archive.writestr("qualification-manifest.json", qa.canonical(manifest))
    raw = stream.getvalue()
    controller.client.archives[3] = raw
    controller.client.artifacts = [{"id": 3, "name": "qualified-release", "expired": False, "digest": "sha256:" + hashlib.sha256(raw).hexdigest(),
                                    "workflow_run": {"id": run["id"], "head_sha": CANDIDATE, "repository_id": 44, "head_repository_id": 44}, "created_at": "2026-01-01T01:10:00Z", "updated_at": "2026-01-01T01:11:00Z"}]
    controller.client.jobs = [{"id": 78, "run_id": run["id"], "run_attempt": 1, "head_sha": CANDIDATE, "name": "Assemble immutable qualified release", "status": "completed", "conclusion": "success", "started_at": "2026-01-01T01:00:00Z", "completed_at": "2026-01-01T01:20:00Z"}]
    monkeypatch.setattr(qa.qualification, "_validate_manifest", lambda x: x)
    calls = []
    controller.bundle_verifier = lambda root, manifest, run: calls.append(run["id"])
    result = controller.reconcile({"workflow_run": run})
    assert result["status"] == "qualified" and calls == [run["id"]]
    assert result["artifact_id"] == 3 and result["version"] == "9.9.9"
    again = controller.reconcile({"workflow_run": run})
    assert again["status"] == "qualified" and calls == [run["id"]]
    assert not any("/tags" in x[1] or "publish" in x[1] for x in controller.client.mutations)


def test_interrupted_dispatch_recovers_only_one_correlated_run(controller):
    controller.client.dispatch_error = True
    receipt = controller.reconcile({"workflow_run": workflow_run()})
    run = workflow_run(run_id=99, qualification=True)
    controller.client.runs[99] = run
    proof = shadow_proof(controller, {**receipt, "run_id": 99})
    controller.shadow_verifier = lambda *args, **kw: deepcopy(proof)
    recovered = controller.reconcile({"workflow_run": run})
    assert recovered["status"] == "waiting_activation_checks"
    assert recovered["run_id"] == 99
    assert sum(x[1].endswith("/dispatches") for x in controller.client.mutations) == 1


def test_interrupted_dispatch_refuses_ambiguous_runs(controller):
    controller.client.dispatch_error = True
    controller.reconcile({"workflow_run": workflow_run()})
    controller.client.runs[99] = workflow_run(run_id=99, qualification=True)
    controller.client.runs[98] = workflow_run(run_id=98, qualification=True)
    result = controller.reconcile({}, manual=True, retry=True)
    assert result["status"] == "blocked" and "ambiguous" in result["reason"]
    assert sum(x[1].endswith("/dispatches") for x in controller.client.mutations) == 1


def test_manual_resume_replays_completed_qualification(controller):
    receipt = controller.reconcile({"workflow_run": workflow_run()})
    proof = shadow_proof(controller, receipt)
    controller.shadow_verifier = lambda *args, **kw: deepcopy(proof)
    result = controller.reconcile({}, manual=True)
    assert result["status"] == "waiting_activation_checks"
    assert len(controller.client.pulls) == 1


def advance_main(controller, *, change_policy=False):
    client = controller.client
    client.contents[NEXT] = deepcopy(client.contents[CANDIDATE])
    if change_policy:
        client.contents[NEXT][qa.maintenance.LEAF_PATH] += b"\n# changed contract\n"
    client.main_sha = NEXT
    client.commits[NEXT] = {"tree": {"sha": "tree-main"}, "parents": [{"sha": CANDIDATE}]}
    client.runs[50] = workflow_run(NEXT, run_id=50)


def test_changed_main_policy_supersedes_old_shadow_and_starts_latest(controller):
    receipt = controller.reconcile({"workflow_run": workflow_run()})
    advance_main(controller, change_policy=True)
    controller.shadow_verifier = lambda *args, **kw: pytest.fail("superseded proof must not activate")
    result = controller.reconcile({"workflow_run": controller.client.runs[receipt["run_id"]]})
    assert result["status"] == "dispatched" and result["candidate_sha"] == NEXT
    assert not controller.client.pulls
    prior = controller.receipts(CANDIDATE)[0]
    assert prior["status"] == "superseded"


def test_stable_policy_rebases_activation_pr_onto_advanced_main(controller):
    receipt = controller.reconcile({"workflow_run": workflow_run()})
    proof = shadow_proof(controller, receipt)
    controller.shadow_verifier = lambda *args, **kw: deepcopy(proof)
    proposal = controller.reconcile({"workflow_run": controller.client.runs[receipt["run_id"]]})
    head = proposal["activation_head"]
    pr_run = workflow_run(head, run_id=30, event="pull_request")
    pr_run["pull_requests"] = [{"number": proposal["pull_request"]}]
    controller.client.runs[30] = pr_run
    advance_main(controller)
    # The REST PR base.sha follows main; ancestry must be checked using its
    # actual single commit parent rather than this moving base pointer.
    controller.client.pulls[proposal["pull_request"]]["base"]["sha"] = NEXT
    result = controller.reconcile({"workflow_run": pr_run})
    assert result["status"] == "waiting_activation_checks"
    assert result["activation_base"] == NEXT
    assert result["activation_head"] != head
    assert controller.client.commits[result["activation_head"]]["parents"] == [{"sha": NEXT}]
    assert not any(x[1].endswith("/merge") for x in controller.client.mutations)


def test_concurrent_bot_branch_edit_is_not_overwritten(controller):
    receipt = controller.reconcile({"workflow_run": workflow_run()})
    proof = shadow_proof(controller, receipt)
    controller.shadow_verifier = lambda *args, **kw: deepcopy(proof)
    proposal = controller.reconcile({"workflow_run": controller.client.runs[receipt["run_id"]]})
    pr = controller.client.pulls[proposal["pull_request"]]
    # Unknown changes to this branch cannot become owned just because a PR
    # retains the configured bot as its original author.
    pr["head"]["sha"] = "d" * 40
    controller.client.refs[pr["head"]["ref"]] = "d" * 40
    count = len(controller.client.mutations)
    result = controller.reconcile({"workflow_run": controller.client.runs[receipt["run_id"]]})
    assert result["status"] == "blocked_evidence"
    assert "unowned or concurrent" in result["reason"]
    assert not any(x[0] == "PATCH" and "/git/refs" in x[1] for x in controller.client.mutations[count:])


def test_unowned_existing_activation_ref_fails_before_git_writes(controller):
    receipt = controller.reconcile({"workflow_run": workflow_run()})
    proof = shadow_proof(controller, receipt)
    controller.shadow_verifier = lambda *args, **kw: deepcopy(proof)
    branch = "codex/policy-activation/" + proof["activation"]["implementation_sha256"]
    controller.client.refs[branch] = "d" * 40
    result = controller.reconcile({"workflow_run": controller.client.runs[receipt["run_id"]]})
    assert result["status"] == "blocked_evidence"
    assert not any(x[1] in {"/git/blobs", "/git/trees", "/git/commits"} for x in controller.client.mutations)


class HTTPResponse:
    def __init__(self, value):
        self.raw = qa.canonical(value)
    def __enter__(self):
        return self
    def __exit__(self, *args):
        return False
    def read(self, maximum):
        return self.raw[:maximum]


@pytest.mark.parametrize("installation", [False, True])
def test_bot_identity_uses_authenticated_rest_or_graphql_actor(monkeypatch, installation):
    requests = []
    def urlopen(request, timeout):
        requests.append(request)
        if request.full_url.endswith("/user"):
            if installation:
                raise qa.urllib.error.HTTPError(request.full_url, 403, "not available for installation", Message(), None)
            return HTTPResponse(BOT)
        assert request.full_url == "https://api.github.com/graphql"
        return HTTPResponse({"data": {"viewer": {"login": BOT["login"], "databaseId": BOT["id"]}}})
    monkeypatch.setattr(qa.urllib.request, "urlopen", urlopen)
    client = qa.GitHubClient(REPOSITORY, "opaque-token", write=True)
    assert client.get_user() == BOT
    assert len(requests) == (2 if installation else 1)


def test_installation_actor_failure_does_not_guess_identity(monkeypatch):
    def urlopen(request, timeout):
        if request.full_url.endswith("/user"):
            raise qa.urllib.error.HTTPError(request.full_url, 403, "not available", Message(), None)
        return HTTPResponse({"errors": [{"message": "forbidden viewer"}]})
    monkeypatch.setattr(qa.urllib.request, "urlopen", urlopen)
    with pytest.raises(qa.AutomationError, match="authenticate installation"):
        qa.GitHubClient(REPOSITORY, "opaque-token", write=True).get_user()


def test_read_token_is_never_used_for_mutation():
    client = qa.GitHubClient(REPOSITORY, "read-token")
    with pytest.raises(qa.AutomationError, match="read credentials cannot mutate"):
        client.request("POST", "/git/refs", {})


@pytest.mark.parametrize("response_kind", ["queued", "merged", "wrong-head", "wrong-method", "errors", "missing-request", "null-response", "null-pr"])
def test_auto_merge_uses_exact_head_and_authenticates_graphql_response(monkeypatch, response_kind):
    head = "d" * 40
    payload = {"id": "PR_node_1", "headRefOid": head, "merged": False, "autoMergeRequest": {"mergeMethod": "SQUASH"}}
    if response_kind == "merged":
        payload.update(merged=True, mergeCommit={"oid": "e" * 40}, autoMergeRequest=None)
    if response_kind == "wrong-head":
        payload["headRefOid"] = "f" * 40
    if response_kind == "wrong-method":
        payload["autoMergeRequest"] = {"mergeMethod": "MERGE"}
    if response_kind == "missing-request":
        payload["autoMergeRequest"] = None
    body: Any = {"data": {"enablePullRequestAutoMerge": {"pullRequest": payload}}}
    if response_kind == "errors":
        body = {"errors": [{"message": "protected requirement"}]}
    if response_kind == "null-response":
        body = None
    if response_kind == "null-pr":
        body["data"]["enablePullRequestAutoMerge"]["pullRequest"] = None

    def urlopen(request, timeout):
        assert request.full_url == "https://api.github.com/graphql"
        sent = json.loads(request.data)
        assert sent["variables"] == {"id": "PR_node_1", "head": head}
        assert "expectedHeadOid:$head" in sent["query"] and "mergeMethod:SQUASH" in sent["query"]
        return HTTPResponse(body)

    monkeypatch.setattr(qa.urllib.request, "urlopen", urlopen)
    client = qa.GitHubClient(REPOSITORY, "opaque-token", write=True)
    if response_kind in {"queued", "merged"}:
        assert client.enable_auto_merge("PR_node_1", head) == payload
    else:
        with pytest.raises(qa.AutomationError):
            client.enable_auto_merge("PR_node_1", head)


def test_pending_protected_requirements_enable_native_auto_merge_and_resume_after_main_ci(controller):
    receipt = controller.reconcile({"workflow_run": workflow_run()})
    controller.shadow_verifier = lambda *args, **kwargs: shadow_proof(controller, receipt)
    proposal = controller.reconcile({"workflow_run": controller.client.runs[receipt["run_id"]]})
    pr = controller.client.pulls[proposal["pull_request"]]
    head = pr["head"]["sha"]
    pr["mergeable_state"] = "blocked"
    pr_run = workflow_run(head, run_id=30, event="pull_request")
    pr_run["pull_requests"] = [{"number": pr["number"]}]
    controller.client.runs[30] = pr_run
    controller.validate_pr = lambda *args, **kwargs: {"status": "pass"}
    for name in qa.REQUIRED_CHECKS:
        controller.client.checks.append({"name": name, "head_sha": head, "status": "completed", "conclusion": "success"})
    waiting = controller.reconcile({"workflow_run": pr_run})
    assert waiting["status"] == "waiting_activation_merge"
    assert pr["state"] == "open"
    assert not any(path.endswith("/merge") for _, path, _ in controller.client.mutations)
    assert sum(path == "enablePullRequestAutoMerge" for _, path, _ in controller.client.mutations) == 1
    assert controller.reconcile({"workflow_run": pr_run})["status"] == "waiting_activation_merge"
    assert sum(path == "enablePullRequestAutoMerge" for _, path, _ in controller.client.mutations) == 1
    # GitHub fulfills the remaining requirements and merges without another CI
    # completion event. Its main push starts the next authenticated CI cycle.
    controller.client.request("PUT", f"/pulls/{pr['number']}/merge", {"sha": head})
    main_ci = workflow_run(head, run_id=40)
    controller.client.runs[40] = main_ci
    result = controller.reconcile({"workflow_run": main_ci})
    assert result["status"] == "dispatched" and result["profile"] == "normal"


def test_coordinator_rejects_proof_when_nonactivation_configuration_is_unevaluated(controller):
    receipt = controller.reconcile({"workflow_run": workflow_run()})
    verified = shadow_proof(controller, receipt)
    verified["audit"]["configuration"]["thresholds"] = {"strict": 0.95}
    before = len(controller.client.mutations)
    with pytest.raises(qa.AutomationError, match="configuration is superseded"):
        controller.activation_proposal(verified, CANDIDATE, receipt)
    assert len(controller.client.mutations) == before
    assert not controller.client.pulls


def test_remote_inspection_does_not_need_enabled_bot(controller):
    controller.config["enabled"] = False
    controller.writer = None
    assert controller.policy_at(CANDIDATE)["status"] == "stale"
    assert not controller.client.mutations


def test_failed_stale_activation_ci_rebases_then_requires_fresh_success(controller):
    receipt = controller.reconcile({"workflow_run": workflow_run()})
    proof = shadow_proof(controller, receipt)
    controller.shadow_verifier = lambda *args, **kw: deepcopy(proof)
    proposal = controller.reconcile({"workflow_run": controller.client.runs[receipt["run_id"]]})
    failed = workflow_run(proposal["activation_head"], run_id=30, event="pull_request", conclusion="failure")
    failed["pull_requests"] = [{"number": proposal["pull_request"]}]
    controller.client.runs[30] = failed
    advance_main(controller)
    result = controller.reconcile({"workflow_run": failed})
    assert result["status"] == "waiting_activation_checks"
    assert result["activation_base"] == NEXT
    assert result["activation_head"] != proposal["activation_head"]
    assert not any(x[1].endswith("/merge") for x in controller.client.mutations)
    head = result["activation_head"]
    fresh = workflow_run(head, run_id=31, event="pull_request")
    fresh["pull_requests"] = failed["pull_requests"]
    controller.client.runs[31] = fresh
    controller.validate_pr = lambda *args, **kw: {"status": "pass"}
    for name in qa.REQUIRED_CHECKS:
        controller.client.checks.append({"name": name, "head_sha": head, "status": "completed", "conclusion": "success"})
    merged = controller.reconcile({"workflow_run": fresh})
    assert merged["status"] == "activation_merged"
    main_ci = workflow_run(merged["candidate_sha"], run_id=60)
    controller.client.runs[60] = main_ci
    normal = controller.reconcile({"workflow_run": main_ci})
    assert normal["status"] == "dispatched" and normal["profile"] == "normal"


def test_new_main_ci_reuses_owned_stable_activation_proof(controller):
    receipt = controller.reconcile({"workflow_run": workflow_run()})
    proof = shadow_proof(controller, receipt)
    controller.shadow_verifier = lambda *args, **kw: deepcopy(proof)
    proposal = controller.reconcile({"workflow_run": controller.client.runs[receipt["run_id"]]})
    advance_main(controller)
    result = controller.reconcile({"workflow_run": controller.client.runs[50]})
    assert result["status"] == "waiting_activation_checks"
    assert result["activation_base"] == NEXT
    assert result["activation_head"] != proposal["activation_head"]
    assert len(controller.client.pulls) == 1
    assert sum(x[1].endswith("/dispatches") for x in controller.client.mutations) == 1


def test_retry_has_distinct_identity_and_recovers_lost_response(controller):
    first = controller.reconcile({"workflow_run": workflow_run()})
    old = controller.client.runs[first["run_id"]]
    old["conclusion"] = "failure"
    controller.reconcile({"workflow_run": old})
    controller.client.dispatch_error = True
    retry = controller.reconcile({}, manual=True, retry=True)
    assert retry["status"] == "blocked_dispatch_unknown"
    assert retry["request_id"] != first["request_id"] and retry["generation"] == 1
    retried = workflow_run(qualification=True, run_id=90)
    retried["display_title"] = f"Release qualification [{retry['request_id']}]"
    controller.client.runs[90] = retried
    proof = shadow_proof(controller, {**retry, "run_id": 90})
    controller.shadow_verifier = lambda *args, **kw: deepcopy(proof)
    result = controller.reconcile({"workflow_run": retried})
    assert result["status"] == "waiting_activation_checks" and result["run_id"] == 90
    assert controller.reconcile({"workflow_run": old})["status"] == "superseded"
    assert sum(x[1].endswith("/dispatches") for x in controller.client.mutations) == 2


def test_failed_activation_ci_with_current_parent_never_merges(controller):
    receipt = controller.reconcile({"workflow_run": workflow_run()})
    proof = shadow_proof(controller, receipt)
    controller.shadow_verifier = lambda *args, **kw: deepcopy(proof)
    proposal = controller.reconcile({"workflow_run": controller.client.runs[receipt["run_id"]]})
    failed = workflow_run(proposal["activation_head"], run_id=30, event="pull_request", conclusion="failure")
    failed["pull_requests"] = [{"number": proposal["pull_request"]}]
    controller.client.runs[30] = failed
    for name in qa.REQUIRED_CHECKS:
        controller.client.checks.append({"name": name, "head_sha": failed["head_sha"], "status": "completed", "conclusion": "success"})
    assert controller.reconcile({"workflow_run": failed})["status"] == "blocked_ci"
    assert not any(x[1].endswith("/merge") for x in controller.client.mutations)


@pytest.mark.parametrize("app", [{"id": 444, "slug": "foreign-app"}, {"id": 777, "slug": "github-actions"}])
def test_foreign_publisher_cannot_forge_terminal_receipt(controller, app):
    forged = controller.result("qualified", candidate_sha=CANDIDATE, profile="policy-shadow",
                               request_id=qa.request_id(REPOSITORY, CANDIDATE, "policy-shadow"), generation=0, run_id=999)
    controller.client.checks.append({"id": 300, "name": qa.CHECK, "head_sha": CANDIDATE, "external_id": forged["request_id"],
                                    "app": app, "output": {"text": qa.canonical(forged).decode()}})
    assert controller.receipts(CANDIDATE) == []
    result = controller.reconcile({"workflow_run": workflow_run()})
    assert result["status"] == "dispatched"
    assert result["run_id"] != 999


def test_unexpected_receipt_writer_blocks_before_dispatch(controller):
    original = controller.client.request
    def wrong_publisher(method, path, payload=None):
        value = original(method, path, payload)
        if path == "/check-runs":
            value["app"] = {"id": 444}
        return value
    controller.client.request = wrong_publisher
    result = controller.reconcile({"workflow_run": workflow_run()})
    assert result["status"] == "blocked"
    assert "publisher differs" in result["reason"]
    assert not any(x[1].endswith("/dispatches") for x in controller.client.mutations)


def test_ruleset_details_use_bot_administration_read(controller):
    backing = controller.client
    class WorkflowReadToken:
        def get(self, path):
            if path.startswith("/rulesets/"):
                raise qa.APIError(403, "workflow token cannot read ruleset details")
            return backing.get(path)
        def list(self, path, key=None):
            if path.startswith("/rulesets"):
                raise qa.APIError(403, "workflow token cannot read bypass metadata")
            return backing.list(path, key)
    controller.client = WorkflowReadToken()
    assert controller.setup() is None
    assert not backing.mutations


def test_bot_ruleset_permission_failure_is_a_setup_block(controller):
    backing = controller.client
    class BotWithoutAdministration:
        def get_user(self):
            return BOT
        def list(self, path, key=None):
            raise qa.APIError(403, "bot requires Administration(read)")
    controller.writer = BotWithoutAdministration()
    result = controller.setup()
    assert result["status"] == "blocked_setup"
    assert "Administration(read)" in result["reason"]
    assert not backing.mutations
