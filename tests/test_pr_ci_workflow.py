"""Selection cannot silently turn optional job skips into a passing PR gate."""

import hashlib
import json
from pathlib import Path
import re

import yaml


ROOT = Path(__file__).parents[1]


def workflow(name):
    return yaml.safe_load((ROOT / ".github/workflows" / name).read_text())


def test_integrity_and_activation_remain_the_exact_independent_gates():
    text = (ROOT / ".github/workflows/ci.yml").read_text()
    frozen = {
        "activation-proof": "2fb4212f674ee29ea1da09867003d522899be9c4e3c89b3b0b7073e389f7eb85",
        "wiki-integrity": "283a14c2aa3081839e7492e4161ae3b00654b13cd2a73cc293eb7f57a90f5f27",
    }
    for name, expected in frozen.items():
        block = re.search(r"(?ms)^  " + name + r":\n.*?(?=^  [a-z0-9-]+:\n|\Z)", text)
        assert block is not None
        assert hashlib.sha256(block.group(0).encode()).hexdigest() == expected


def test_base_policy_is_loaded_without_a_candidate_bootstrap_or_write_token():
    ci = workflow("ci.yml")
    assert ci["permissions"] == {"contents": "read"}
    triggers = ci.get("on", ci.get(True))
    assert set(triggers) == {"push", "pull_request"}
    assert "edited" in triggers["pull_request"]["types"]
    job = ci["jobs"]["plan"]
    assert all(permission == "read" for permission in job["permissions"].values())
    load = next(
        step
        for step in job["steps"]
        if step.get("name") == "Load only the trusted base selection policy"
    )
    assert (
        load["env"]["BASE_SHA"]
        == "${{ github.event.pull_request.base.sha || github.sha }}"
    )
    assert 'git show "${BASE_SHA}:release/${name}"' in load["run"]
    assert (
        "exit 2" in load["run"]
        and "candidate policy is never executed as a fallback" in load["run"]
    )
    assert "git show HEAD:" not in load["run"]
    assert (
        json.loads((ROOT / "release/automation.json").read_text())["enabled"] is False
    )


def test_selected_execution_and_aggregate_authenticate_the_driver_before_use():
    jobs = workflow("ci.yml")["jobs"]
    execution = jobs["test"]
    assert execution["if"] == "${{ needs.plan.outputs.has-tests == 'true' }}"
    assert (
        execution["strategy"]["matrix"] == "${{ fromJSON(needs.plan.outputs.matrix) }}"
    )
    for operation in ("prepare", "run"):
        step = next(
            s for s in execution["steps"] if "pr_ci.py " + operation in s.get("run", "")
        )
        assert step["run"].index(
            "Base-owned selection driver or plan digest differs"
        ) < step["run"].index("pr_ci.py " + operation)
        assert "BASE_POLICY_SHA256" in step["env"] and "PLAN_SHA256" in step["env"]
        assert "--lane" in step["run"]
        assert "continue-on-error" not in step
    aggregate = jobs["complete"]
    assert aggregate["if"] == "always()" and set(aggregate["needs"]) == set(jobs) - {
        "complete"
    }
    gate = next(s for s in aggregate["steps"] if "pr_ci.py gate" in s.get("run", ""))
    assert (
        "--reports incoming/tests" in gate["run"]
        and "--needs producers.json" in gate["run"]
    )
    assert gate["env"]["PRODUCERS"] == "${{ toJSON(needs) }}"
    assert "continue-on-error" not in gate


def test_expensive_supplementary_workflows_cannot_duplicate_pr_and_main_runs():
    for file, key in [
        ("action-selftest.yml", "action"),
        ("dependency-setup-check.yml", "dependency-controls"),
    ]:
        value = workflow(file)
        assert set(value.get("on", value.get(True))) == {
            "workflow_call",
            "workflow_dispatch",
        }
        caller = workflow("ci.yml")["jobs"][key]
        assert caller["needs"] == "plan"
        assert caller["if"] == "${{ needs.plan.outputs." + key + " == 'true' }}"
    shadow = workflow("core-shard-shadow.yml")
    assert set(shadow.get("on", shadow.get(True))) == {"workflow_dispatch"}


def test_full_native_release_and_new_native_evidence_are_still_required():
    jobs = workflow("release-qualification.yml")["jobs"]
    for key in ("core", "core-windows"):
        job = jobs[key]
        native = next(
            s
            for s in job["steps"]
            if s.get("name")
            == "Verify scoped evidence repair on native Windows and Linux"
        )
        assert native["env"]["LLM_WIKI_REQUIRE_NATIVE_DIAGNOSTICS"] == "1"
        assert "--minimum-collected 146 --minimum-passed 146" in native["run"]
        assert "continue-on-error" not in native
        upload = next(
            s for s in job["steps"] if s.get("name") == "Upload lane evidence"
        )
        assert "evidence/native-regressions/" in upload["with"]["path"]
        assert upload["with"]["if-no-files-found"] == "error"
        full = [
            s["run"]
            for s in job["steps"]
            if "python -m pytest tests -q" in s.get("run", "")
        ]
        assert full
    assert any("--cov-fail-under=87" in s.get("run", "") for s in jobs["core"]["steps"])
    assert "pr_ci.py" not in str(jobs["bundle"])
    for name in (
        "core",
        "core-windows",
        "owner-lanes",
        "knowledge-maintenance",
        "reproducible",
        "smoke-parity",
    ):
        assert name in jobs["bundle"]["needs"]
