"""Selection cannot silently turn optional job skips into a passing PR gate."""

import hashlib
import json
from pathlib import Path
import re

import yaml
import pytest


ROOT = Path(__file__).parents[1]


def workflow(name):
    return yaml.safe_load((ROOT / ".github/workflows" / name).read_text())


def test_selected_native_diagnostics_have_an_explicit_language_scope():
    env = workflow("ci.yml")["jobs"]["test"]["env"]
    assert env["LLM_WIKI_REQUIRE_NATIVE_DIAGNOSTICS"] == "${{ (matrix.lane == 'toolchains' || matrix.typescript) && '1' || '' }}"
    assert env["LLM_WIKI_REQUIRED_NATIVE_LANGUAGES"] == "${{ matrix.lane == 'toolchains' && 'go,haskell,rust,typescript' || (matrix.typescript && 'typescript' || '') }}"


@pytest.mark.parametrize(("scope", "language", "required"), [
    (None, "go", True), ("", "rust", True),
    ("typescript", "typescript", True), ("typescript", "go", False),
    ("go,haskell,rust,typescript", "haskell", True),
    ("unsupported", "typescript", True),
])
def test_native_diagnostic_scope_preserves_mandatory_owners(monkeypatch, request, scope, language, required):
    from llm_wiki_cli.services import extractor_helpers
    monkeypatch.setattr(extractor_helpers, "get_prepared_binary", lambda *args: None)
    monkeypatch.setattr(extractor_helpers, "typescript_dependencies_ready", lambda *args: False)
    monkeypatch.setenv("LLM_WIKI_REQUIRE_NATIVE_DIAGNOSTICS", "1")
    if scope is None:
        monkeypatch.delenv("LLM_WIKI_REQUIRED_NATIVE_LANGUAGES", raising=False)
    else:
        monkeypatch.setenv("LLM_WIKI_REQUIRED_NATIVE_LANGUAGES", scope)
    require = request.getfixturevalue("require_prepared_diagnostics_helper")
    with pytest.raises(pytest.fail.Exception if required else pytest.skip.Exception):
        require(language)


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
        'registry.get("revision")' in load["run"]
        and 'registry["revision"] != 2' in load["run"]
    )
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
        assert "github.workflow" not in value["concurrency"]["group"]
        assert (
            value["concurrency"]["group"] != workflow("ci.yml")["concurrency"]["group"]
        )
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


def test_shared_action_dependencies_retain_their_required_consumer():
    policy = json.loads((ROOT / "release/pr-ci-policy.json").read_text())
    assert type(policy["revision"]) is int and policy["revision"] == 2
    for path in [
        ".github/scripts/setup-llm-wiki-ci-toolchains.sh",
        "release/qualification.py",
        "release/toolchain-lock.json",
        ".github/workflows/action-selftest.yml",
        "pyproject.toml",
    ]:
        assert any(
            path in rule["paths"] and "hosted-action" in rule["groups"]
            for rule in policy["rules"]
        )


def test_new_controller_is_in_both_pr_and_full_release_lint_scopes():
    from release import static_checks
    import sys

    checks = static_checks.default_checks(ROOT, ROOT / "unused-evidence")
    command = next(check.command for check in checks if check.name == "ruff")
    assert command[:2] == (sys.executable, "-m")
    assert {"release/pr_ci.py", "release/pr_ci_pytest.py"} <= set(command)
    lint = next(
        s
        for s in workflow("ci.yml")["jobs"]["typecheck"]["steps"]
        if s.get("name") == "Check the release lint scope"
    )
    assert all(
        path in lint["run"] for path in ["release/pr_ci.py", "release/pr_ci_pytest.py"]
    )
