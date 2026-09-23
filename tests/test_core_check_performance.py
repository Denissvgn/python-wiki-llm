"""Frozen inputs, metric binding and cleanup for native core-check comparisons."""

import argparse
from copy import deepcopy
import io
import json
from pathlib import Path
import shutil
import subprocess
import sys

import pytest
import yaml

from release import core_check_performance as performance


@pytest.fixture(scope="module")
def frozen_base(tmp_path_factory):
    tmp_path = tmp_path_factory.mktemp("core-check-inputs")
    root = tmp_path / "repository"
    root.mkdir()
    performance.git(root, "init")
    performance.git(root, "config", "core.autocrlf", "false")
    (root / ".gitattributes").write_text("* -text\n")
    helper = root / "release/core_check_performance.py"
    helper.parent.mkdir()
    helper.write_bytes(Path(performance.__file__).read_bytes())
    policy = root / "tests/test_architecture_layers.py"
    policy.parent.mkdir()
    policy.write_text(
        "from pathlib import Path\n"
        "def test_shared_validation_adapters_remain_thin():\n"
        "    assert (Path(__file__).parents[1] / 'value.txt').read_text() == 'candidate'\n"
    )
    (root / "value.txt").write_text("baseline")

    def commit():
        performance.git(root, "add", ".")
        performance.git(
            root,
            "-c",
            "user.name=Fixture",
            "-c",
            "user.email=fixture@example.invalid",
            "-c",
            f"core.hooksPath={tmp_path / 'absent-hooks'}",
            "commit",
            "--no-gpg-sign",
            "-m",
            "owned fixture",
        )
        return performance.git(root, "rev-parse", "HEAD").decode().strip()

    baseline = commit()
    (root / "value.txt").write_text("candidate")
    candidate = commit()
    directory = tmp_path / "inputs"
    args = argparse.Namespace(
        root=root, baseline=baseline, candidate=candidate, output=directory
    )
    with pytest.MonkeyPatch.context() as environment:
        environment.delenv("GITHUB_SHA", raising=False)
        environment.delenv("GITHUB_OUTPUT", raising=False)
        assert performance.freeze(args) == 0
    return args, performance.digest(directory / "inputs.json")


@pytest.fixture
def frozen(frozen_base, tmp_path):
    original, sha = frozen_base
    args = argparse.Namespace(**vars(original))
    args.output = tmp_path / "inputs"
    shutil.copytree(original.output, args.output)
    return args, sha


def test_freeze_prepare_and_worker_use_candidate_inputs_for_old_policy(
    frozen, tmp_path
):
    frozen_args, sha = frozen
    work = tmp_path / "work"
    assert (
        performance.prepare(
            argparse.Namespace(inputs=frozen_args.output, inputs_sha256=sha, work=work)
        )
        == 0
    )
    assert (work / "baseline/value.txt").read_text() == "baseline"
    assert (work / "candidate/value.txt").read_text() == "candidate"
    output = tmp_path / "observation.json"
    command = [
        sys.executable,
        "-I",
        "-B",
        performance.__file__,
        "worker",
        "--inputs",
        str(frozen_args.output),
        "--work",
        str(work),
        "--role",
        "baseline",
        "--target",
        "adapters",
        "--output",
        str(output),
    ]
    result = subprocess.run(
        command, stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=30
    )
    assert result.returncode == 0, result.stderr
    row = json.loads(output.read_text())
    performance.validate_observation(
        row,
        target="adapters",
        role="baseline",
        coverage=False,
        memory=False,
        policy_sha256=performance.digest(
            work / "baseline/tests/test_architecture_layers.py"
        ),
    )


@pytest.mark.parametrize(
    "mutation", ["archive", "helper", "manifest", "revision", "extra", "shape"]
)
def test_changed_frozen_inputs_cannot_be_used(frozen, mutation):
    args, sha = frozen
    if mutation in {"archive", "helper"}:
        path = args.output / (
            "candidate-source.tar"
            if mutation == "archive"
            else "core_check_performance.py"
        )
        path.write_bytes(path.read_bytes() + b"changed")
    else:
        path = args.output / "inputs.json"
        data = json.loads(path.read_text())
        if mutation == "revision":
            data["candidate_sha"] = "HEAD"
        elif mutation == "extra":
            data["ignored"] = True
        elif mutation == "shape":
            data = []
        else:
            data["qualifying"] = True
        performance.write(path, data)
        if mutation != "manifest":
            sha = performance.digest(path)
    with pytest.raises(ValueError):
        performance.inputs(args.output, sha)


def test_extracted_input_changes_are_rejected(frozen, tmp_path):
    args, sha = frozen
    work = tmp_path / "work"
    performance.prepare(
        argparse.Namespace(inputs=args.output, inputs_sha256=sha, work=work)
    )
    performance.verify_extracted(
        args.output / "candidate-source.tar", work / "candidate"
    )
    (work / "candidate/value.txt").write_text("tampered")
    with pytest.raises(ValueError, match="extracted source differs"):
        performance.verify_extracted(
            args.output / "candidate-source.tar", work / "candidate"
        )


@pytest.mark.parametrize(
    "field,value",
    [
        ("passed", False),
        ("role", "candidate"),
        ("target", "documentation"),
        ("coverage", 0),
        ("seconds", True),
        ("seconds", 0),
        ("seconds", -1),
        ("seconds", float("nan")),
        ("python_peak_bytes", 100),
        ("input_tree_sha256", {}),
        ("policy_sha256", "b" * 64),
    ],
)
def test_observation_results_are_bound_and_finite(field, value):
    row = {
        "passed": True,
        "role": "baseline",
        "target": "adapters",
        "coverage": False,
        "seconds": 1.0,
        "python_peak_bytes": None,
        "input_tree_sha256": "c" * 64,
        "policy_sha256": "a" * 64,
    }
    changed = deepcopy(row)
    changed[field] = value
    with pytest.raises(ValueError):
        performance.validate_observation(
            changed,
            target="adapters",
            role="baseline",
            coverage=False,
            memory=False,
            policy_sha256="a" * 64,
        )
    performance.validate_observation(
        row,
        target="adapters",
        role="baseline",
        coverage=False,
        memory=False,
        policy_sha256="a" * 64,
    )


@pytest.mark.parametrize("system", ["nt", "posix"])
def test_timeout_cleans_the_owned_process_tree(monkeypatch, tmp_path, system):
    calls = []

    class Process:
        pid = 424242
        waits = 0

        def wait(self, timeout):
            self.waits += 1
            if self.waits == 1:
                raise subprocess.TimeoutExpired(["owned"], timeout)
            return -1

    process = Process()

    def popen(command, **options):
        assert options["stdin"] == subprocess.DEVNULL
        assert options["start_new_session"] is (system != "nt")
        return process

    monkeypatch.setattr(performance.subprocess, "Popen", popen)
    monkeypatch.setattr(
        performance.subprocess, "run", lambda command, **options: calls.append(command)
    )
    monkeypatch.setattr(
        performance.os, "killpg", lambda pid, sig: calls.append(pid), raising=False
    )
    with pytest.raises(subprocess.TimeoutExpired):
        performance.run_observation(
            ["owned"], cwd=tmp_path, env={}, log=io.BytesIO(), platform_name=system
        )
    assert process.waits == 2
    assert calls == (
        [["taskkill", "/PID", "424242", "/T", "/F"]] if system == "nt" else [424242]
    )


def test_comparison_runs_before_merge_only_for_affected_checks():
    root = Path(__file__).parents[1]
    workflow = yaml.safe_load((root / ".github/workflows/ci.yml").read_text())
    jobs = workflow["jobs"]
    freeze = jobs["core-check-inputs"]
    assert freeze["if"] == "${{ github.event_name == 'pull_request' }}"
    changes = next(step for step in freeze["steps"] if step.get("id") == "changes")
    assert (
        "git diff --name-only" in changes["run"]
        and "tests/python_source_inventory.py" in changes["run"]
    )
    job = jobs["core-check-comparison"]
    assert job["needs"] == "core-check-inputs"
    assert "outputs.enabled == 'true'" in job["if"]
    assert job["strategy"]["max-parallel"] == 3
    assert [
        (p["os"], p["python"], p["coverage"])
        for p in job["strategy"]["matrix"]["include"]
    ] == [
        ("ubuntu-24.04", "3.10", True),
        ("windows-2025", "3.13", False),
        ("macos-15", "3.14", False),
    ]
    text = "\n".join(str(s) for s in job["steps"])
    assert '"./work/candidate[dev,tokens]"' in text and "--samples 2" in text
    assert (
        "--strict-config" in text
        and "--strict-markers" in text
        and "xfail_strict=true" in text
    )
    assert all("continue-on-error" not in step for step in job["steps"])
    assert job["steps"][-1]["if"] == "always()"


def test_failed_windows_tree_cleanup_is_reported_and_root_is_reaped(
    monkeypatch, tmp_path
):
    class Process:
        pid = 424242
        waits = 0
        killed = False

        def wait(self, timeout):
            self.waits += 1
            if self.waits == 1:
                raise subprocess.TimeoutExpired(["owned"], timeout)
            return -1

        def kill(self):
            self.killed = True

    process = Process()
    monkeypatch.setattr(
        performance.subprocess, "Popen", lambda *args, **kwargs: process
    )

    def cleanup_failure(command, **options):
        raise subprocess.CalledProcessError(1, command)

    monkeypatch.setattr(performance.subprocess, "run", cleanup_failure)
    with pytest.raises(RuntimeError, match="tree cleanup failed"):
        performance.run_observation(
            ["owned"], cwd=tmp_path, env={}, log=io.BytesIO(), platform_name="nt"
        )
    assert process.killed and process.waits == 2
