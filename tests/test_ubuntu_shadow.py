"""Orchestrator controls: independent installs, pinned resolution and failure evidence."""

import argparse
from copy import deepcopy
import os
from pathlib import Path
import shutil
import subprocess
import sys

import pytest

from release import ubuntu_shadow as shadow
from release import qualification as q
from tests.test_ubuntu_suites import evidence as evidence, legacy_for, reseal


@pytest.fixture
def coordinated(evidence, monkeypatch):
    root, registry, original = evidence
    identity = deepcopy(original)
    archive = root.parent / "source.tar"
    archive.write_bytes(b"owned source archive")
    identity["source"]["archive_sha256"] = q.sha256_file(archive)
    harness = root.parent / "harness.tar"
    harness.write_bytes(b"owned harness")
    digest = q.sha256_file(harness)
    q.write_json(root / "identity.json", identity)
    execution = q.load_json(root / "execution.json")
    execution.update(
        identity=identity,
        identity_sha256=q.sha256_file(root / "identity.json"),
        harness_sha256=digest,
    )
    q.write_json(root / "execution.json", execution)
    reseal(root)
    legacy = legacy_for(root, registry, identity)
    sources = dict(zip(shadow.GROUPS, [*legacy.legacy, root], strict=True))
    args = argparse.Namespace(
        work=root.parent / "work",
        output=root.parent / "evidence",
        identity=root / "identity.json",
        archive=archive,
        harness=harness,
        harness_sha256=digest,
        registry=registry,
    )
    monkeypatch.setattr(
        shadow.suites, "frozen_inputs", lambda _: {"identity": identity}
    )
    state = {
        "prepare_fail": None,
        "run_fail": None,
        "prepared": [],
        "ran": [],
        "constraints": [],
    }

    def prepare(arguments, name, constraints, control):
        state["prepared"].append(name)
        directory = arguments.work / name
        directory.mkdir()
        candidate = directory / "candidate"
        candidate.mkdir()
        (candidate / "release").mkdir()
        q.write_json(
            candidate / "release/skip-allowlist.json",
            {"schema_version": q.ALLOWLIST_SCHEMA, "entries": []},
        )
        venv = directory / ".venv"
        venv.mkdir()
        environment = shadow.lane_environment(directory)
        control["preparations"][name] = {"source": str(candidate), "venv": str(venv)}
        if constraints is not None:
            state["constraints"].append(constraints.read_text())
        if name == state["prepare_fail"]:
            if state.get("bootstrap_failure"):
                raise subprocess.CalledProcessError(1, ["owned-ensurepip"])
            raise shadow.q.QualificationError("owned installation failure")
        return candidate, venv / "python", environment, 1.0

    def invoke(command, directory, environment, log, timeout=900):
        log.parent.mkdir(parents=True, exist_ok=True)
        log.write_text("owned child diagnostics")
        if "environment" in command:
            destination = Path(command[command.index("--output") + 1])
            q.write_json(destination, execution["environment"])
        else:
            name = directory.name
            state["ran"].append(name)
            assert environment["TMPDIR"].startswith(str(directory))
            assert environment["XDG_CACHE_HOME"].startswith(str(directory))
            destination = Path(command[command.index("--output") + 1])
            # Even a failing producer may leave apparently passing XML/receipts.
            shutil.copytree(sources[name], destination)
            if name == state["run_fail"]:
                return {"exit_code": 1, "seconds": 0.01, "error": None}
        return {"exit_code": 0, "seconds": 0.01, "error": None}

    monkeypatch.setattr(shadow, "prepare", prepare)
    monkeypatch.setattr(shadow, "invoke", invoke)
    return args, state


def test_one_host_orchestration_uses_independent_inputs_and_common_dependency_pins(
    coordinated,
):
    args, state = coordinated
    assert shadow.run(args) == 0
    control = q.load_json(args.output / "diagnostics/orchestration.json")
    report = q.load_json(args.output / "diagnostics/ubuntu-shadow-comparison.json")
    assert control["passed"] and control["complete"] and control["qualifying"] is False
    with pytest.raises(q.QualificationError, match="shadow evidence"):
        q._reject_shadow_evidence(args.output / "diagnostics/orchestration.json")
    assert report["passed"] and report["complete"] and report["qualifying"] is False
    assert state["prepared"] == ["resolver", *shadow.GROUPS]
    assert state["ran"] == list(shadow.GROUPS)
    assert len(set(state["constraints"])) == 1 and len(state["constraints"]) == 4
    assert "pytest==8.4.2\n" in state["constraints"][0]
    assert "agent-wiki-cli" not in state["constraints"][0]
    assert len({item["source"] for item in control["preparations"].values()}) == 5
    assert len({item["venv"] for item in control["preparations"].values()}) == 5
    assert all(value == "success" for value in report["producer_results"].values())


@pytest.mark.parametrize("phase", ["prepare_fail", "run_fail"])
@pytest.mark.parametrize(
    "lane", ["legacy-slow", "legacy-security", "legacy-product", "union"]
)
def test_failed_lane_does_not_suppress_later_diagnostics_or_allow_acceptance(
    coordinated, phase, lane
):
    args, state = coordinated
    state[phase] = lane
    assert shadow.run(args) == 1
    control = q.load_json(args.output / "diagnostics/orchestration.json")
    report = q.load_json(args.output / "diagnostics/ubuntu-shadow-comparison.json")
    assert not control["passed"] and not report["passed"]
    assert (
        control["producers"][lane]["result"]
        == report["producer_results"][lane]
        == "failure"
    )
    assert report["errors"]
    assert set(state["prepared"]) == {"resolver", *shadow.GROUPS}
    assert set(state["ran"]) == set(shadow.GROUPS) - (
        {lane} if phase == "prepare_fail" else set()
    )
    assert all(
        control["producers"][name]["result"] == "success"
        for name in shadow.GROUPS
        if name != lane
    )


def test_resolver_failure_retains_nonqualifying_report_and_never_runs_suites(
    coordinated,
):
    args, state = coordinated
    state["prepare_fail"] = "resolver"
    assert shadow.run(args) == 1
    report = q.load_json(args.output / "diagnostics/ubuntu-shadow-comparison.json")
    assert report["stage"] == "prepare" and report["errors"]
    assert set(report["producer_results"].values()) == {"not-run"}
    assert not state["ran"]


def test_stale_work_cannot_be_reused(coordinated):
    args, _ = coordinated
    args.work.mkdir()
    (args.work / "old-evidence").write_text("retain")
    with pytest.raises(shadow.q.QualificationError, match="must be new"):
        shadow.run(args)
    assert (args.work / "old-evidence").read_text() == "retain"
    assert not args.output.exists()


def test_lanes_have_isolated_temp_cache_and_import_state(tmp_path, monkeypatch):
    for name in [
        "PYTHONPATH",
        "PYTHONHOME",
        "VIRTUAL_ENV",
        "PYTEST_ADDOPTS",
        "PIP_CONSTRAINT",
        "PIP_REQUIREMENT",
    ]:
        monkeypatch.setenv(name, "caller-state")
    before = dict(os.environ)
    first = shadow.lane_environment(tmp_path / "first")
    second = shadow.lane_environment(tmp_path / "second")
    for name in [
        "TMPDIR",
        "TMP",
        "TEMP",
        "XDG_CACHE_HOME",
        "PIP_CACHE_DIR",
        "LLM_WIKI_CACHE_DIR",
    ]:
        assert first[name] != second[name]
        assert Path(first[name]).is_dir() and Path(second[name]).is_dir()
    for name in [
        "PYTHONPATH",
        "PYTHONHOME",
        "VIRTUAL_ENV",
        "PYTEST_ADDOPTS",
        "PIP_CONSTRAINT",
        "PIP_REQUIREMENT",
    ]:
        assert name not in first and name not in second
    assert dict(os.environ) == before


def test_launch_failure_and_timeout_preserve_diagnostics(tmp_path, monkeypatch):
    missing = shadow.invoke(
        [str(tmp_path / "missing-program")],
        tmp_path,
        dict(os.environ),
        tmp_path / "missing.log",
    )
    assert missing["exit_code"] == 127 and missing["error"]
    # Exercise timeout cleanup without turning interpreter startup speed into
    # a one-second assertion on a loaded Windows runner.
    calls = []

    class OwnedProcess:
        pid = 4242

        def __init__(self, command, **kwargs):
            self.command = command
            self.waits = 0
            kwargs["stdout"].write(b"ready\n")
            assert kwargs["start_new_session"] is (os.name == "posix")

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def wait(self, timeout):
            self.waits += 1
            if self.waits == 1:
                raise subprocess.TimeoutExpired(self.command, timeout)
            calls.append("reaped")
            return 1

        def kill(self):
            calls.append("killed")

    monkeypatch.setattr(shadow.subprocess, "Popen", OwnedProcess)
    monkeypatch.setattr(
        shadow.os, "killpg", lambda pid, sig: calls.append((pid, sig)), raising=False
    )
    timeout = shadow.invoke(
        [sys.executable, "-c", "owned fixture"],
        tmp_path,
        dict(os.environ),
        tmp_path / "timeout.log",
        timeout=1,
    )
    assert timeout["exit_code"] == 124 and timeout["error"]
    assert (tmp_path / "timeout.log").read_text().strip() == "ready"
    assert calls[-1] == "reaped"
    assert calls[0] == (
        (4242, shadow.signal.SIGKILL) if os.name == "posix" else "killed"
    )


@pytest.mark.parametrize("name", ["archive", "harness"])
def test_changed_frozen_input_fails_before_any_install_and_keeps_diagnostics(
    coordinated, name
):
    args, state = coordinated
    getattr(args, name).write_bytes(b"tampered frozen input")
    assert shadow.run(args) == 1
    report = q.load_json(args.output / "diagnostics/ubuntu-shadow-comparison.json")
    assert report["stage"] == "prepare" and report["errors"]
    assert not report["passed"] and not state["prepared"] and not state["ran"]


def test_unsafe_dependency_metadata_cannot_become_an_install_argument(evidence):
    root, _, _ = evidence
    environment = q.load_json(root / "execution.json")["environment"]
    environment["packages"]["pytest"] = "8.4.2\n--extra-index-url=owned.invalid"
    with pytest.raises(shadow.q.QualificationError, match="unsafe resolved"):
        shadow.constraints_text(environment)


def test_venv_bootstrap_error_is_reported_and_later_lanes_still_run(coordinated):
    args, state = coordinated
    state["prepare_fail"] = "legacy-security"
    state["bootstrap_failure"] = True
    assert shadow.run(args) == 1
    assert "legacy-product" in state["ran"] and "union" in state["ran"]
    report = q.load_json(args.output / "diagnostics/ubuntu-shadow-comparison.json")
    assert report["producer_results"]["legacy-security"] == "failure"
    assert report["errors"] and not report["passed"]


def test_real_child_capture_uses_a_startup_budget_separate_from_timeout_controls(
    tmp_path,
):
    result = shadow.invoke(
        [sys.executable, "-I", "-c", "print('owned child')"],
        tmp_path,
        dict(os.environ),
        tmp_path / "real-child.log",
        timeout=15,
    )
    assert result["exit_code"] == 0 and result["error"] is None
    assert (tmp_path / "real-child.log").read_text().strip() == "owned child"
