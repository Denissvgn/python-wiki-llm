"""Manual renewal uses authenticated main proofs and isolated approval changes."""

from copy import deepcopy
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


def test_approval_pr_has_one_commit_two_files_and_same_name_ref(tmp_path):
    proposal = tmp_path / "proposal"
    files = [
        "release/knowledge-maintenance.json",
        "release/policy-activations/" + "a" * 64 + ".json",
    ]
    for name in files:
        target = proposal / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("{}")
    result = {
        "base_sha": SHA,
        "proof_source_sha": "c" * 40,
        "branch": renewal.BRANCH_PREFIX + "a" * 64,
        "proposal": str(proposal),
        "files": files,
    }
    writes = []

    def get(path):
        if path == "/git/ref/heads/main":
            return {"object": {"sha": SHA}}
        if path.startswith("/git/ref/heads/"):
            raise APIError(404, "missing")
        if path.startswith("/collaborators/"):
            return {"permission": "admin"}
        return {"tree": {"sha": "d" * 40}}

    def write(method, path, payload):
        writes.append((method, path, deepcopy(payload)))
        return {
            "sha": "b" * 40,
            "html_url": "https://github.com/example/agent-wiki/pull/1",
        }

    reader = SimpleNamespace(get=get)
    writer = create_autospec(renewal.GitHubClient, instance=True)
    writer.get_user.return_value = {"login": "owner", "id": 42}
    writer.request.side_effect = write
    created = renewal.create_pr(
        REPOSITORY,
        result,
        reader,
        writer,
        config={"trusted_bot": {"login": "", "id": None}},
    )
    assert created["status"] == "pull_request_created"
    commit = next(row[2] for row in writes if row[1] == "/git/commits")
    assert commit["parents"] == [SHA]
    ref = next(row[2] for row in writes if row[1] == "/git/refs")
    assert ref == {"ref": "refs/heads/" + result["branch"], "sha": "b" * 40}
    tree = next(row[2] for row in writes if row[1] == "/git/trees")
    assert {entry["path"] for entry in tree["tree"]} == set(files)
    assert all("merge" not in path for _, path, _ in writes)


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
