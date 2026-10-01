"""Trusted event orchestration and the bounded nonpromoting profile."""

from pathlib import Path

import yaml


ROOT = Path(__file__).parents[1]


def _workflow(name):
    return yaml.safe_load((ROOT / ".github/workflows" / name).read_text())


def test_coordinator_uses_trusted_revision_and_defers_credentials():
    workflow = _workflow("release-automation.yml")
    triggers = workflow.get("on", workflow.get(True))
    assert triggers["workflow_run"] == {"workflows": ["CI", "Release qualification"], "types": ["completed"]}
    assert "publish" not in triggers["workflow_dispatch"]["inputs"]
    assert workflow["concurrency"]["cancel-in-progress"] is False
    job = workflow["jobs"]["reconcile"]
    steps = {step["name"]: step for step in job["steps"]}
    checkout = steps["Check out the trusted coordinator revision"]
    assert checkout["with"]["ref"] == "${{ github.workflow_sha }}"
    assert checkout["with"]["persist-credentials"] is False
    assert "head_repository.full_name == github.repository" in job["if"]
    command = steps["Reconcile authenticated events"]
    assert command["env"]["RELEASE_AUTOMATION_TOKEN"] == "${{ steps.app.outputs.token || secrets.RELEASE_AUTOMATION_TOKEN }}"
    token = steps["Acquire a repository-scoped short-lived bot token"]
    assert "steps.setup.outputs.enabled == 'true'" in token["if"]
    assert token["uses"] == "actions/create-github-app-token@bcd2ba49218906704ab6c1aa796996da409d3eb1"
    assert token["with"]["repositories"] == "${{ github.event.repository.name }}"
    assert {key for key in token["with"] if key.startswith("permission-")} == {"permission-actions", "permission-contents", "permission-pull-requests", "permission-checks", "permission-administration"}
    assert token["with"]["permission-administration"] == "read"
    assert '--event "${GITHUB_EVENT_PATH}"' in command["run"]
    assert '--apply "${retry[@]}"' in command["run"]
    assert "No release was published" in steps["Explain candidate disposition"]["run"]
    assert steps["Retain automation status"]["if"] == "always()"
    assert workflow["permissions"]["contents"] == "read"


def test_bounded_policy_profile_never_runs_release_only_producers():
    workflow = _workflow("release-qualification.yml")
    live = {"freeze", "action", "knowledge-maintenance", "decision"}
    for name, job in workflow["jobs"].items():
        if name not in live:
            assert "!inputs.knowledge-policy-shadow" in job["if"], name
    freeze = next(step for step in workflow["jobs"]["freeze"]["steps"] if step.get("name") == "Validate identity and create one source archive")
    assert freeze["env"]["SOURCE_PROFILE"] == "${{ inputs.knowledge-policy-shadow && 'policy-shadow' || 'candidate' }}"
    assert '--mode "${SOURCE_PROFILE}"' in freeze["run"]
    decision = workflow["jobs"]["decision"]
    aggregate = next(step for step in decision["steps"] if step.get("name") == "Emit deterministic aggregate")
    assert "!inputs.knowledge-policy-shadow" in aggregate["if"]
    policy = next(step for step in decision["steps"] if step.get("name") == "Require nonpromoting policy shadow verification")
    assert "shadow-decision" in policy["run"]
    assert '"mode": "policy-shadow"' in policy["run"]
    assert policy["env"]["POLICY_COMMIT_EPOCH"] == "${{ needs.freeze.outputs.commit-epoch }}"
    assert "--gate" not in policy["run"]


def test_required_ci_gates_validate_data_without_executing_proposals():
    workflow = _workflow("ci.yml")
    jobs = workflow["jobs"]
    proof = jobs["activation-proof"]
    assert proof["name"] == "Release activation proof"
    checkout = proof["steps"][0]
    assert checkout["with"]["ref"] == "${{ github.event.pull_request.base.sha || github.sha }}"
    assert checkout["with"]["persist-credentials"] is False
    command = next(step for step in proof["steps"] if step.get("name") == "Verify activation-only proposals")
    assert "validate-pr" in command["run"] and "inspect" in command["run"]
    assert "--apply" not in command["run"] and "RELEASE_AUTOMATION_TOKEN" not in command["env"]
    assert all(value == "read" for value in proof["permissions"].values())
    complete = jobs["complete"]
    assert complete["name"] == "CI complete" and complete["if"] == "always()"
    assert set(complete["needs"]) == set(jobs) - {"complete"}
    gate = next(step for step in complete["steps"] if step.get("name") == "Require every mandatory CI producer")
    assert 'value["result"]' in gate["run"] and "raise SystemExit" in gate["run"]
