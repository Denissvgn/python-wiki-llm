"""Shadow scheduling and the boundary separating it from qualification."""

from pathlib import Path
import json
import os
import shlex
import subprocess
import sys

import pytest
import yaml

from release import core_shards as s

ROOT = Path(__file__).parents[1]


def workflow():
    return yaml.safe_load(
        (ROOT / ".github/workflows/core-shard-shadow.yml").read_text()
    )


def test_native_shadow_has_complete_bounded_matrices_and_attempt_specific_artifacts():
    value = workflow()
    assert value["permissions"] == {"contents": "read"}
    events = value.get("on", value.get(True))
    assert set(events) == {"pull_request", "workflow_dispatch"}
    assert "release/core_shard_runner.py" in events["pull_request"]["paths"]
    assert "tests/test_core_shard_workflow.py" in events["pull_request"]["paths"]
    jobs = value["jobs"]
    for name, replicas in (("reference", 1), ("shards", 2), ("compare", 1)):
        job = jobs[name]
        assert job["strategy"]["fail-fast"] is False
        assert job["strategy"]["max-parallel"] == 3
        matrix = job["strategy"]["matrix"]["include"]
        assert len(matrix) == len(s.PROFILES) * replicas
        for lane in s.PROFILES:
            rows = [row for row in matrix if row["lane"] == lane]
            assert len(rows) == replicas
            assert all(
                row["os"] == s.PROFILES[lane]["os"]
                and row["python"] == s.PROFILES[lane]["python"]
                for row in rows
            )
            if name == "shards":
                assert {row["shard"] for row in rows} == {0, 1}
        steps = job["steps"]
        assert job["defaults"]["run"]["shell"] == "bash"
        assert any("create-venv" in step.get("run", "") for step in steps)
        assert all(not step.get("continue-on-error", False) for step in steps)
        for step in steps:
            if "upload-artifact@" in step.get("uses", ""):
                assert step["if"] == "${{ always() }}"
                assert "github.run_attempt" in step["with"]["name"]
                assert not step["with"]["name"].startswith("evidence-")
            if "download-artifact@" in step.get("uses", ""):
                assert "github.run_attempt" in step["with"].get(
                    "name", step["with"].get("pattern", "")
                )
    assert "!cancelled()" in jobs["compare"]["if"]
    assert "needs.shards.result == 'success'" not in jobs["compare"]["if"]
    assert jobs["complete"]["if"] == "${{ always() }}"
    assert set(jobs["complete"]["needs"]) == {
        "freeze",
        "reference",
        "shards",
        "compare",
    }


def test_pins_are_verified_before_installing_and_all_commands_keep_source_bindings():
    for name in ("shards", "compare"):
        steps = workflow()["jobs"][name]["steps"]
        verify = next(
            i
            for i, step in enumerate(steps)
            if "core_shard_runner.py verify-plan" in step.get("run", "")
        )
        install = next(
            i for i, step in enumerate(steps) if "-m pip install" in step.get("run", "")
        )
        assert verify < install
        command = steps[install]["run"]
        assert "--constraint incoming/reference/constraints.txt" in command
        assert "--requirement incoming/reference/constraints.txt" in command
        assert '"./candidate[dev,tokens]"' in command and " -e " not in command
    for name in ("reference", "shards", "compare"):
        operation = "compare" if name == "compare" else "execute"
        step = next(
            step
            for step in workflow()["jobs"][name]["steps"]
            if "core_shard_runner.py " + operation in step.get("run", "")
        )
        args = shlex.split(step["run"].replace("\\\n", " "))
        for option in (
            "--root",
            "--identity",
            "--archive",
            "--harness",
            "--harness-sha256",
            "--lane",
            "--run-id",
            "--run-attempt",
        ):
            assert args.count(option) == 1


def test_shadow_never_qualifies_and_ubuntu_macos_keep_the_full_core_contract():
    shadow = workflow()
    text = str(shadow)
    assert "build-bundle" not in text and "finalize-promotion" not in text
    assert "id-token" not in shadow["permissions"]
    qualification = yaml.safe_load(
        (ROOT / ".github/workflows/release-qualification.yml").read_text()
    )
    core = qualification["jobs"]["core"]
    assert {row["lane"] for row in core["strategy"]["matrix"]["include"]} == {
        "core-ubuntu-3.10",
        "core-macos-3.14",
    }
    assert core["needs"] == "freeze"
    commands = [
        step["run"]
        for step in core["steps"]
        if "python -m pytest tests" in step.get("run", "")
    ]
    assert len(commands) == 2
    assert any("--cov-fail-under=87" in command for command in commands)
    assert "core_shard" not in str(core)
    assert "needs.core.result" in str(qualification["jobs"]["bundle"])


@pytest.mark.parametrize(
    "reference,shards,compare",
    [
        ("success", "success", "success"),
        ("failure", "skipped", "skipped"),
        ("success", "failure", "failure"),
        ("cancelled", "skipped", "skipped"),
        ("success", "success", "skipped"),
    ],
)
def test_completion_gate_reports_upstream_failures_and_keeps_skips_blocking(
    reference, shards, compare
):
    script = workflow()["jobs"]["complete"]["steps"][-1]["run"].splitlines()
    assert script[0] == "python -I - <<'PY'" and script[-1] == "PY"
    states = {
        "freeze": "success",
        "reference": reference,
        "shards": shards,
        "compare": compare,
    }
    completed = subprocess.run(
        [sys.executable, "-I", "-c", "\n".join(script[1:-1])],
        env={
            **os.environ,
            "NEEDS_JSON": json.dumps(
                {name: {"result": state} for name, state in states.items()}
            ),
        },
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert (completed.returncode == 0) is all(
        state == "success" for state in states.values()
    )
    assert all(f"{name}: {state}" in completed.stdout for name, state in states.items())
    if reference != "success":
        assert "before expansion" in completed.stderr
        assert "not missing variables" in completed.stderr


def qualifying_workflow():
    return yaml.safe_load(
        (ROOT / ".github/workflows/release-qualification.yml").read_text()
    )


def test_windows_rollout_keeps_independent_platforms_and_explicit_unsharded_rollback():
    value = qualifying_workflow()
    inputs = value.get("on", value.get(True))["workflow_dispatch"]["inputs"]
    assert inputs["windows-core-shards"]["type"] == "boolean"
    assert inputs["windows-core-shards"]["default"] is True
    assert "inputs.windows-core-shards" in value["concurrency"]["group"]
    jobs = value["jobs"]
    layout = jobs["freeze"]["outputs"]["core-layout"]
    assert (
        layout
        == "${{ inputs.windows-core-shards && !inputs.discovery-mode && !inputs.ubuntu-suite-shadow && 'windows-sharded' || 'unsharded' }}"
    )
    assert jobs["core"]["needs"] == "freeze"
    assert jobs["core-windows-plan"]["needs"] == "freeze"
    assert jobs["core-windows-shards"]["strategy"] == {
        "fail-fast": False,
        "max-parallel": 2,
        "matrix": {"shard": [0, 1]},
    }
    logical = jobs["core-windows"]
    assert logical["name"] == "RD-01/RD-02 core (core-windows-3.13)"
    assert set(logical["needs"]) == {
        "freeze",
        "core-windows-plan",
        "core-windows-shards",
    }
    assert " ".join(logical["if"].split()) == (
        "${{ !cancelled() && !inputs.bandit-parity-verification && needs.freeze.result == 'success' "
        "&& (needs.freeze.outputs.core-layout == 'unsharded' "
        "|| (needs.core-windows-plan.result == 'success' && needs.core-windows-shards.result == 'success')) }}"
    )
    for name in ("core-windows-plan", "core-windows-shards", "core-windows"):
        job = jobs[name]
        assert job["runs-on"] == "windows-2025"
        assert job["timeout-minutes"] <= 360
        assert job["defaults"]["run"]["shell"] == "bash"
        steps = job["steps"]
        assert any(
            step.get("with", {}).get("python-version") == "3.13" for step in steps
        )
        assert any("create-venv" in step.get("run", "") for step in steps)
        assert not any(step.get("continue-on-error", False) for step in steps)
    rollback = next(
        step
        for step in logical["steps"]
        if "python -m pytest tests" in step.get("run", "")
    )
    assert rollback["if"] == "${{ needs.freeze.outputs.core-layout == 'unsharded' }}"
    assert all(
        flag in rollback["run"]
        for flag in (
            "--strict-config",
            "--strict-markers",
            "-W error",
            "xfail_strict=true",
        )
    )
    for name in ("owner-lanes", "bundle", "decision", "discovery-allowlist"):
        assert "core-windows" in jobs[name]["needs"]
    for name in ("core-windows-shards", "core-windows"):
        steps = jobs[name]["steps"]
        verify = next(
            i
            for i, step in enumerate(steps)
            if "core_shard_runner.py verify-plan" in step.get("run", "")
        )
        install = next(
            i
            for i, step in enumerate(steps)
            if "--constraint incoming/plan/constraints.txt" in step.get("run", "")
            and "pip install" in step["run"]
        )
        assert verify < install and "--purpose qualification" in steps[verify]["run"]
        assert "--requirement incoming/plan/constraints.txt" in steps[install]["run"]
    for name in ("core_shards.py", "core_shard_runner.py", "core-shard-timings.json"):
        assert "release/" + name in str(jobs["freeze"]["steps"])


@pytest.mark.parametrize("windows", ["success", "failure", "cancelled", "skipped"])
def test_real_decision_mapping_requires_windows_for_core_security_and_product(
    tmp_path, windows
):
    import re
    from release import qualification as q

    step = next(
        step
        for step in qualifying_workflow()["jobs"]["decision"]["steps"]
        if step.get("name") == "Emit deterministic aggregate"
    )
    script = step["run"]
    script = script.replace("${{ needs.freeze.outputs.sha }}", "a" * 40).replace(
        "${{ needs.freeze.outputs.version }}", "1.0.0"
    )
    script = script.replace("${{ needs.core-windows.result }}", windows)
    script = re.sub(r"\$\{\{ needs\.[a-z-]+\.result \}\}", "success", script)
    argv = shlex.split(script)[3:]
    assert argv[0] == "aggregate"
    argv[argv.index("--output") + 1] = str(tmp_path / "decision.json")
    completed = subprocess.run(
        [sys.executable, "-I", str(Path(q.__file__).resolve()), *argv],
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert completed.returncode == 0, completed.stderr
    result = q.load_json(tmp_path / "decision.json")
    for gate in ("RD-01", "RD-04", "RD-05"):
        assert (result["gates"][gate] == "PASS") is (windows == "success")
    assert result["gates"]["RD-13"] == "BLOCKED"
