"""Shadow scheduling and the boundary separating it from qualification."""

from pathlib import Path
import shlex

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


def test_shadow_never_publishes_qualified_release_and_default_remains_unsharded():
    shadow = workflow()
    text = str(shadow)
    assert "build-bundle" not in text and "finalize-promotion" not in text
    assert "id-token" not in shadow["permissions"]
    qualification = yaml.safe_load(
        (ROOT / ".github/workflows/release-qualification.yml").read_text()
    )
    core = qualification["jobs"]["core"]
    assert len(core["strategy"]["matrix"]["include"]) == 3
    commands = [
        step["run"]
        for step in core["steps"]
        if "python -m pytest tests" in step.get("run", "")
    ]
    assert len(commands) == 2
    assert any("--cov-fail-under=87" in command for command in commands)
    assert "core_shard" not in str(core)
    assert "needs.core.result" in str(qualification["jobs"]["bundle"])
