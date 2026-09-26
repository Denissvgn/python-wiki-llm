"""Cache measurements cannot hide a partial builder, stale source or failed control."""

import argparse
from copy import deepcopy
from pathlib import Path
import subprocess

import pytest

from release import dependency_setup_probe as p


def result(case):
    artifacts = {
        "agent_wiki_cli-1.0-py3-none-any.whl": "a" * 64,
        "agent_wiki_cli-1.0.tar.gz": "b" * 64,
    }
    state = {
        "baseline": "disabled",
        "cold": "miss",
        "warm": "hit",
        "stale": "rejected",
        "corrupt": "rejected",
        "unavailable": "unavailable",
    }[case]
    setup = {
        "schema_version": p.d.SCHEMA,
        "complete": True,
        "error": None,
        "cache_state": state,
        "installed": {"owned": "1.0"},
        "files": {"owned.whl": {}},
        "identity": {"namespace": "probe"},
        "venv_and_setup_seconds": 1.0,
    }
    return {
        "schema_version": p.SCHEMA,
        "qualifying": False,
        "complete": True,
        "error": None,
        "candidate_sha": "c" * 40,
        "tree": "d" * 40,
        "inputs_sha256": "e" * 64,
        "case": case,
        "artifacts": artifacts,
        "context": {"python": "3.13.15"},
        "cache_namespace": "probe",
        "cache_restore_seconds": 0.5,
        "elapsed_seconds": 4.0,
        "runner_image": "owned",
        "builders": {
            copy: {
                "setup": deepcopy(setup),
                "artifacts": dict(artifacts),
                "build_seconds": 1.0,
            }
            for copy in ("a", "b")
        },
        "validation": {
            "setup": None if case == "baseline" else deepcopy(setup),
            "result": "PASS",
            "artifacts": dict(artifacts),
            "seconds": 1.0,
        },
    }


def test_all_six_controls_compare_without_authorizing_release_or_enabling_cache(
    tmp_path,
):
    paths = []
    for case in p.CASES:
        path = tmp_path / (case + ".json")
        p.d.write_json(path, result(case))
        paths.append(path)
    assert (
        p.compare(argparse.Namespace(result=paths, output=tmp_path / "summary.json"))
        == 0
    )
    summary = p.d.read_json(tmp_path / "summary.json")
    assert summary["qualifying"] is False and summary["complete"] is True
    assert summary["cache_default_enabled"] is False and set(summary["cases"]) == set(
        p.CASES
    )


@pytest.mark.parametrize(
    "mutation",
    [
        "missing",
        "duplicate",
        "candidate",
        "tree",
        "inputs",
        "artifacts",
        "environment",
        "namespace",
        "partial",
        "qualifying",
        "error",
        "builder",
        "builder-bytes",
        "validation",
        "validation-bytes",
        "failed-install",
        "wrong-control",
        "no-packages",
        "negative-duration",
    ],
)
def test_incomplete_or_mismatched_cache_proof_is_rejected(tmp_path, mutation):
    values = [result(case) for case in p.CASES]
    row = values[-1]
    if mutation == "missing":
        values.pop()
    elif mutation == "duplicate":
        values[-1] = deepcopy(values[0])
    elif mutation in {"candidate", "tree", "inputs"}:
        row[
            {"candidate": "candidate_sha", "tree": "tree", "inputs": "inputs_sha256"}[
                mutation
            ]
        ] = "f" * (64 if mutation == "inputs" else 40)
    elif mutation == "artifacts":
        row["artifacts"]["agent_wiki_cli-1.0.tar.gz"] = "f" * 64
    elif mutation == "environment":
        row["context"]["python"] = "3.14.5"
    elif mutation == "namespace":
        row["cache_namespace"] = "different"
    elif mutation == "partial":
        row["complete"] = False
    elif mutation == "qualifying":
        row["qualifying"] = True
    elif mutation == "error":
        row["error"] = "owned failure"
    elif mutation == "builder":
        row["builders"].pop("b")
    elif mutation == "builder-bytes":
        row["builders"]["b"]["artifacts"]["agent_wiki_cli-1.0.tar.gz"] = "f" * 64
    elif mutation == "validation":
        row["validation"]["result"] = "failure"
    elif mutation == "validation-bytes":
        row["validation"]["artifacts"]["agent_wiki_cli-1.0.tar.gz"] = "f" * 64
    elif mutation == "failed-install":
        row["builders"]["a"]["setup"]["complete"] = False
    elif mutation == "wrong-control":
        row["builders"]["b"]["setup"]["cache_state"] = "hit"
    elif mutation == "no-packages":
        row["validation"]["setup"]["installed"] = {}
    else:
        row["elapsed_seconds"] = -1
    paths = []
    for i, value in enumerate(values):
        path = tmp_path / (str(i) + ".json")
        p.d.write_json(path, value)
        paths.append(path)
    with pytest.raises(p.d.DependencyError):
        p.compare(argparse.Namespace(result=paths, output=tmp_path / "summary.json"))
    assert not (tmp_path / "summary.json").exists()


def test_frozen_inputs_bind_the_actual_running_helpers_and_archive(
    tmp_path, monkeypatch
):
    source = tmp_path / "repository"
    source.mkdir()
    subprocess.run(["git", "init", str(source)], check=True, capture_output=True)
    (source / "release").mkdir()
    for name in p.FILES[1:]:
        (source / "release" / name).write_bytes(
            Path(p.__file__).with_name(name).read_bytes()
        )
    subprocess.run(["git", "add", "."], cwd=source, check=True)
    subprocess.run(
        [
            "git",
            "-c",
            "user.name=Fixture",
            "-c",
            "user.email=fixture@example.invalid",
            "-c",
            f"core.hooksPath={source / 'no-hooks'}",
            "commit",
            "--no-gpg-sign",
            "-m",
            "owned",
        ],
        cwd=source,
        check=True,
        capture_output=True,
    )
    sha = p.git(source, "rev-parse", "HEAD").decode().strip()
    frozen = tmp_path / "inputs"
    assert p.freeze(argparse.Namespace(root=source, candidate=sha, output=frozen)) == 0
    digest = p.d.sha256(frozen / "inputs.json")
    assert p.inputs(frozen, digest)["candidate_sha"] == sha
    (frozen / "dependency_downloads.py").write_text("changed helper")
    with pytest.raises(p.d.DependencyError, match="frozen input differs"):
        p.inputs(frozen, digest)


def test_probe_children_cannot_publish_outputs_or_reuse_global_python_and_pip_state(
    monkeypatch,
):
    for name in (
        "GITHUB_OUTPUT",
        "GITHUB_PATH",
        "GITHUB_ENV",
        "VIRTUAL_ENV",
        "PYTHONPATH",
        "PYTHONHOME",
        "PIP_EXTRA_INDEX_URL",
    ):
        monkeypatch.setenv(name, "owned-parent-state")
    value = p.environment(1234)
    assert (
        not {
            "GITHUB_OUTPUT",
            "GITHUB_PATH",
            "GITHUB_ENV",
            "VIRTUAL_ENV",
            "PYTHONPATH",
            "PYTHONHOME",
            "PIP_EXTRA_INDEX_URL",
        }
        & value.keys()
    )
    assert value["PIP_NO_CACHE_DIR"] == "1" and value["SOURCE_DATE_EPOCH"] == "1234"


@pytest.mark.parametrize("platform", ["posix", "nt"])
def test_timed_out_comparison_reaps_its_own_build_process_tree(
    tmp_path, monkeypatch, platform
):
    from types import SimpleNamespace

    calls = []

    class Child:
        pid = 424242
        waits = 0

        def wait(self, timeout):
            self.waits += 1
            if self.waits == 1:
                raise subprocess.TimeoutExpired("owned", timeout)
            return -9

        def poll(self):
            return None

        def kill(self):
            calls.append("root")

    child = Child()

    def start(command, **kwargs):
        assert kwargs["stdin"] == subprocess.DEVNULL
        assert kwargs["start_new_session"] is (platform == "posix")
        return child

    monkeypatch.setattr(p.subprocess, "Popen", start)
    monkeypatch.setattr(
        p.subprocess, "run", lambda command, **kwargs: calls.append(command)
    )
    monkeypatch.setattr(
        p,
        "os",
        SimpleNamespace(name=platform, killpg=lambda pid, sig: calls.append(pid)),
    )
    monkeypatch.setattr(p, "signal", SimpleNamespace(SIGKILL=object()))
    with pytest.raises(subprocess.TimeoutExpired):
        p.invoke(["owned"], tmp_path / "run.log", {})
    assert child.waits == 2
    assert calls == (
        [424242, "root"]
        if platform == "posix"
        else [["taskkill", "/PID", "424242", "/T", "/F"], "root"]
    )
