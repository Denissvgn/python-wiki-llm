"""Manual renewal uses authenticated main proofs and isolated approval changes."""

from copy import deepcopy
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import create_autospec

import pytest

from release import policy_renewal as renewal
from release.qualification_automation import APIError
from tests.test_policy_activation import (
    ActivationPullRequest,
    REPOSITORY,
    RUN,
    SHA,
    ShadowEvidence,
)
from tests.test_release_workflows import _yaml

ROOT = Path(__file__).resolve().parents[1]


def test_evaluation_dispatches_only_nonpromoting_main_profile(monkeypatch):
    calls = []
    client = SimpleNamespace(
        get=lambda path: {
            "ref": "refs/heads/main",
            "object": {"type": "commit", "sha": SHA},
        },
        request=lambda *args: calls.append(args),
    )
    monkeypatch.setattr(renewal, "_run", lambda *a, **kw: SimpleNamespace(stdout=SHA))
    planned = renewal.evaluate(ROOT, REPOSITORY, client, apply=False, correlation="1")
    assert calls == [] and planned["status"] == "planned"
    result = renewal.evaluate(ROOT, REPOSITORY, client, apply=True, correlation="1")
    method, endpoint, payload = calls[0]
    assert method == "POST" and endpoint.endswith(
        "release-qualification.yml/dispatches"
    )
    assert payload["ref"] == "main"
    assert payload["inputs"]["candidate-sha"] == SHA
    assert payload["inputs"]["knowledge-policy-shadow"] == "true"
    assert payload["inputs"]["discovery-mode"] == "false"
    assert result["proof_source_sha"] == SHA


def test_evaluation_refuses_checkout_that_differs_from_main(monkeypatch):
    client = SimpleNamespace(
        get=lambda path: {
            "ref": "refs/heads/main",
            "object": {"type": "commit", "sha": SHA},
        }
    )
    monkeypatch.setattr(
        renewal, "_run", lambda *a, **kw: SimpleNamespace(stdout="b" * 40)
    )
    with pytest.raises(ValueError, match="main advanced"):
        renewal.evaluate(ROOT, REPOSITORY, client, apply=True, correlation="1")


def test_preparation_replays_real_proof_and_writes_only_approval_inputs(
    tmp_path, monkeypatch
):
    shadow = ShadowEvidence(tmp_path)
    client = ActivationPullRequest(shadow)
    shadow.run["head_branch"] = "main"
    before = {
        str(p): p.read_bytes() for p in shadow.policy_root.rglob("*") if p.is_file()
    }
    monkeypatch.setattr(
        renewal, "_run", lambda *a, **kw: SimpleNamespace(stdout=client.base)
    )
    output = tmp_path / "proposal"
    result = renewal.prepare(
        shadow.policy_root, REPOSITORY, client, run_id=RUN, attempt=1, output=output
    )
    assert result["status"] == "proposal_ready"
    assert result["base_sha"] == client.base and result["proof_source_sha"] == SHA
    assert len(result["files"]) == 2
    config = json.loads((output / renewal.maintenance.POLICY_PATH).read_text())
    assert config["activation"]["proof_source_sha"] == SHA != client.base
    assert config["mode"] == "required"
    assert before == {
        str(p): p.read_bytes() for p in shadow.policy_root.rglob("*") if p.is_file()
    }
    client.comparison["merge_base_commit"]["sha"] = "f" * 40
    with pytest.raises(ValueError, match="main history"):
        renewal.prepare(
            shadow.policy_root,
            REPOSITORY,
            client,
            run_id=RUN,
            attempt=1,
            output=tmp_path / "other",
        )


class ApprovalService:
    """Stateful API fixture preserves server effects when responses are lost."""

    def __init__(self, tmp_path):
        proposal = tmp_path / "proposal"
        files = [
            "release/knowledge-maintenance.json",
            "release/policy-activations/" + "a" * 64 + ".json",
        ]
        for name in files:
            target = proposal / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text("{}")
        self.result = {
            "base_sha": SHA,
            "proof_source_sha": "c" * 40,
            "branch": renewal.BRANCH_PREFIX + "a" * 64,
            "proposal": str(proposal),
            "files": files,
        }
        self.main = SHA
        self.refs = {}
        self.commits = {SHA: {"sha": SHA, "tree": {"sha": "d" * 40}}}
        self.pulls = []
        self.writes = []
        self.failure = None
        self.reader = create_autospec(renewal.GitHubClient, instance=True)
        self.reader.get.side_effect = self.get
        self.reader.list.side_effect = self.list
        self.writer = create_autospec(renewal.GitHubClient, instance=True)
        self.writer.get_user.return_value = {"login": "owner", "id": 42}
        self.writer.request.side_effect = self.write

    def get(self, path):
        if path == "/git/ref/heads/main":
            return {"object": {"sha": self.main}}
        if path.startswith("/git/ref/heads/"):
            branch = path.removeprefix("/git/ref/heads/")
            if branch not in self.refs:
                raise APIError(404, "missing")
            return deepcopy(self.refs[branch])
        if path.startswith("/collaborators/"):
            return {"permission": "admin"}
        if path.startswith("/git/commits/"):
            return deepcopy(self.commits[path.removeprefix("/git/commits/")])
        raise AssertionError(path)

    def list(self, path):
        assert path.startswith("/pulls?state=open&head=")
        return deepcopy(self.pulls)

    def fail_once(self, point):
        if self.failure == point:
            self.failure = None
            raise APIError(503, "interrupted API response")

    def write(self, method, path, payload):
        assert method == "POST"
        self.writes.append((method, path, deepcopy(payload)))
        if path in {"/git/blobs", "/git/trees"}:
            digest = hashlib.sha256(renewal.canonical(payload)).hexdigest()[:40]
            return {"sha": digest}
        if path == "/git/commits":
            head = "b" * 40
            self.commits[head] = {
                "sha": head,
                "tree": {"sha": payload["tree"]},
                "parents": [{"sha": p} for p in payload["parents"]],
                "message": payload["message"],
            }
            return {"sha": head}
        if path == "/git/refs":
            branch = payload["ref"].removeprefix("refs/heads/")
            assert branch not in self.refs
            self.refs[branch] = {
                "ref": payload["ref"],
                "object": {"type": "commit", "sha": payload["sha"]},
            }
            self.fail_once("ref-response")
            return deepcopy(self.refs[branch])
        if path == "/pulls":
            self.fail_once("pr-request")
            branch = payload["head"]
            pr = {
                "state": "open",
                "draft": False,
                "head": {
                    "sha": self.refs[branch]["object"]["sha"],
                    "ref": branch,
                    "repo": {"full_name": REPOSITORY},
                },
                "base": {
                    "sha": self.main,
                    "ref": "main",
                    "repo": {"full_name": REPOSITORY},
                },
                "html_url": "https://github.com/example/agent-wiki/pull/1",
            }
            self.pulls.append(pr)
            self.fail_once("pr-response")
            return deepcopy(pr)
        raise AssertionError(path)

    def create(self):
        return renewal.create_pr(
            REPOSITORY,
            self.result,
            self.reader,
            self.writer,
            config={"trusted_bot": {"login": "", "id": None}},
        )


@pytest.fixture
def approval_service(tmp_path):
    return ApprovalService(tmp_path)


def test_approval_pr_has_one_commit_two_files_and_same_name_ref(approval_service):
    service = approval_service
    created = service.create()
    assert created["status"] == "pull_request_created"
    commit = next(row[2] for row in service.writes if row[1] == "/git/commits")
    assert commit["parents"] == [SHA]
    ref = next(row[2] for row in service.writes if row[1] == "/git/refs")
    assert ref == {"ref": "refs/heads/" + service.result["branch"], "sha": "b" * 40}
    tree = next(row[2] for row in service.writes if row[1] == "/git/trees")
    assert {entry["path"] for entry in tree["tree"]} == set(service.result["files"])
    assert all("merge" not in path for _, path, _ in service.writes)


@pytest.mark.parametrize("interruption", ["ref-response", "pr-request", "pr-response"])
def test_approval_retry_recovers_interrupted_server_effects(
    approval_service, interruption
):
    service = approval_service
    service.failure = interruption
    with pytest.raises(APIError, match="interrupted"):
        service.create()
    assert service.result["branch"] in service.refs
    result = service.create()
    assert result["status"] == (
        "pull_request_reused"
        if interruption == "pr-response"
        else "pull_request_created"
    )
    assert len(service.pulls) == 1
    assert sum(path == "/git/commits" for _, path, _ in service.writes) == 1
    assert sum(path == "/git/refs" for _, path, _ in service.writes) == 1
    assert sum(path == "/pulls" for _, path, _ in service.writes) == (
        2 if interruption == "pr-request" else 1
    )
    assert all(method == "POST" for method, _, _ in service.writes)


@pytest.mark.parametrize(
    "mutation", ["tree", "parent", "message", "extra-parent", "invalid-parent"]
)
def test_approval_retry_rejects_unowned_or_superseded_branch(
    approval_service, mutation
):
    service = approval_service
    service.create()
    commit = service.commits["b" * 40]
    if mutation == "tree":
        commit["tree"]["sha"] = "f" * 40
    elif mutation == "parent":
        commit["parents"][0]["sha"] = "f" * 40
    elif mutation == "message":
        commit["message"] = "unrelated change"
    elif mutation == "extra-parent":
        commit["parents"].append({"sha": "f" * 40})
    else:
        commit["parents"] = [None]
    previous_mutations = list(service.writes)
    with pytest.raises(ValueError, match="unowned or superseded"):
        service.create()
    assert all(
        path in {"/git/blobs", "/git/trees"}
        for _, path, _ in service.writes[len(previous_mutations) :]
    )
    assert len(service.pulls) == 1


@pytest.mark.parametrize(
    "mutation",
    ["head", "base", "fork", "draft", "ambiguous", "missing-head", "missing-repo"],
)
def test_approval_retry_rejects_mismatched_existing_pr(approval_service, mutation):
    service = approval_service
    service.create()
    pr = service.pulls[0]
    if mutation == "head":
        pr["head"]["sha"] = "f" * 40
    elif mutation == "base":
        pr["base"]["ref"] = "other"
    elif mutation == "fork":
        pr["head"]["repo"]["full_name"] = "other/repo"
    elif mutation == "draft":
        pr["draft"] = True
    elif mutation == "ambiguous":
        service.pulls.append(deepcopy(pr))
    elif mutation == "missing-head":
        pr["head"] = None
    else:
        pr["head"]["repo"] = None
    with pytest.raises(ValueError, match="ambiguous|differs|incomplete"):
        service.create()
    assert sum(path == "/pulls" for _, path, _ in service.writes) == 1


def test_created_pr_response_must_match_the_verified_proposal(approval_service):
    service = approval_service

    def wrong_response(method, path, payload):
        response = service.write(method, path, payload)
        if path == "/pulls":
            response["head"]["sha"] = "f" * 40
        return response

    service.writer.request.side_effect = wrong_response
    with pytest.raises(ValueError, match="differs"):
        service.create()
    service.writer.request.side_effect = service.write
    assert service.create()["status"] == "pull_request_reused"
    assert len(service.pulls) == 1


def test_workflow_has_clear_choices_main_binding_and_no_publishing():
    workflow = _yaml("policy-renewal.yml")
    inputs = workflow.get("on", workflow.get(True, {}))["workflow_dispatch"]["inputs"]
    assert inputs["operation"]["type"] == "choice"
    assert inputs["operation"]["options"] == ["evaluate", "prepare"]
    assert "candidate-sha" not in inputs and "automation-request-id" not in inputs
    steps = workflow["jobs"]["renewal"]["steps"]
    assert "refs/heads/main" in steps[0]["run"]
    assert steps[1]["with"]["ref"] == "${{ github.workflow_sha }}"
    assert steps[1]["with"]["persist-credentials"] is False
    assert any(
        step.get("with", {}).get("name") == "policy-approval-proposal" for step in steps
    )
    assert "publish" not in workflow["jobs"]
    assert workflow["permissions"]["contents"] == "read"


def test_prepare_without_pr_credentials_reports_reviewable_artifact(
    tmp_path, monkeypatch
):
    output = tmp_path / "status.json"
    monkeypatch.setenv("GITHUB_TOKEN", "read-only-fixture")
    monkeypatch.delenv("POLICY_RENEWAL_TOKEN", raising=False)
    monkeypatch.setattr(
        renewal, "GitHubClient", lambda *args, **kwargs: SimpleNamespace()
    )
    monkeypatch.setattr(
        renewal,
        "prepare",
        lambda *args, **kwargs: {
            "status": "proposal_ready",
            "proof_source_sha": SHA,
            "branch": renewal.BRANCH_PREFIX + "a" * 64,
        },
    )
    monkeypatch.setattr(
        renewal,
        "create_pr",
        lambda *args, **kwargs: pytest.fail("no PR write credentials"),
    )
    assert (
        renewal.main(
            ["prepare", "--proof-run-id", str(RUN), "--output", str(output), "--apply"]
        )
        == 0
    )
    result = json.loads(output.read_text())
    assert result["status"] == "proposal_ready"
    assert "RELEASE_AUTOMATION_TOKEN" in result["next_step"]
    assert "url" not in result
