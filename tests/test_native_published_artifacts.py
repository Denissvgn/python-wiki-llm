"""Local controller contracts; these checks do not certify native Windows."""

import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess

import pytest
import yaml


ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "native_published_artifacts", ROOT / "release/native_published_artifacts.py"
)
assert spec and spec.loader
probe = importlib.util.module_from_spec(spec)
spec.loader.exec_module(probe)


def archives(tmp_path):
    names = probe.artifact_names("2.5.0")
    hashes = {}
    for kind, name in names.items():
        content = (kind + " independent archive control").encode()
        (tmp_path / name).write_bytes(content)
        hashes[kind] = hashlib.sha256(content).hexdigest()
    return names, hashes


def test_changed_archive_bytes_are_rejected(tmp_path):
    names, hashes = archives(tmp_path)
    probe.verify_archives(tmp_path, names, hashes)
    (tmp_path / names["wheel"]).write_bytes(b"another build of the same version")
    with pytest.raises(probe.ProbeError, match="wheel archive digest differs"):
        probe.verify_archives(tmp_path, names, hashes)


@pytest.mark.parametrize("extra", [True, False])
def test_extra_or_missing_archives_cannot_be_selected(tmp_path, extra):
    names, hashes = archives(tmp_path)
    if extra:
        (tmp_path / "another.whl").write_bytes(b"unselected archive")
    else:
        (tmp_path / names["sdist"]).unlink()
    with pytest.raises(probe.ProbeError, match="only the two expected"):
        probe.verify_archives(tmp_path, names, hashes)


@pytest.mark.parametrize("version", ["../2.5.0", "2.5.0;echo unsafe", "*", "2.5.0rc1"])
def test_non_stable_or_path_versions_are_rejected(version):
    with pytest.raises(probe.ProbeError, match="stable X.Y.Z"):
        probe.artifact_names(version)


@pytest.mark.parametrize("change", ["equal", "version", "wheel_sha256", "sdist_sha256"])
def test_comparison_cannot_certify_another_pair(tmp_path, change):
    hashes = {"wheel": "a" * 64, "sdist": "b" * 64}
    for kind in hashes:
        (tmp_path / f"{kind}.json").write_text(json.dumps({"artifact": {"sha256": hashes[kind]}}))
    comparison = {"equal": True, "version": "2.5.0",
                  "wheel_sha256": hashes["wheel"], "sdist_sha256": hashes["sdist"]}
    path = tmp_path / "comparison.json"
    path.write_text(json.dumps(comparison))
    probe.verify_comparison(tmp_path, hashes, "2.5.0")
    comparison[change] = False if change == "equal" else "different"
    path.write_text(json.dumps(comparison))
    with pytest.raises(probe.ProbeError, match="comparison did not agree"):
        probe.verify_comparison(tmp_path, hashes, "2.5.0")


def test_non_native_execution_stays_incomplete_without_starting_processes(tmp_path, monkeypatch):
    # Force only this guard, never a Path flavor or a native success claim.
    monkeypatch.setattr(probe, "is_native_windows", lambda: False)
    def forbidden(*args, **kwargs):
        pytest.fail("non-native guard started a process")
    monkeypatch.setattr(probe.subprocess, "run", forbidden)
    output = tmp_path / "evidence"
    code = probe.main(["--repository", "Denissvgn/python-wiki-llm", "--version", "2.5.0",
                      "--harness-dir", str(tmp_path / "harness"), "--harness-sha", "c" * 40,
                      "--wheel-sha256", "a" * 64, "--sdist-sha256", "b" * 64,
                      "--artifacts", str(tmp_path / "dist"), "--work", str(tmp_path / "work"),
                      "--output", str(output)])
    assert code == 2
    receipt = json.loads((output / "probe.json").read_text())
    assert receipt["status"] == "incomplete" and receipt["commands"] == []
    assert "actual native Windows" in receipt["reason"]


def test_bad_download_is_rejected_before_any_consumer_install(tmp_path, monkeypatch):
    # This is an ordering unit control, not a native execution receipt.
    monkeypatch.setattr(probe.sys, "prefix", str(tmp_path / "controller/.venv"))
    monkeypatch.setattr(probe, "is_native_windows", lambda: True)
    monkeypatch.setattr(probe.platform, "platform", lambda: "controlled-unit-fixture")
    monkeypatch.setattr(probe.platform, "machine", lambda: "controlled-unit-fixture")
    artifacts = tmp_path / "dist"
    calls = []
    def controlled(command, **kwargs):
        calls.append(command)
        if command[:1] == ["git"]:
            raw = b"c" * 40 + b"\n" if command[-1] == "HEAD" else b""
        elif command[:3] == ["gh", "release", "download"]:
            artifacts.mkdir(exist_ok=True)
            archives(artifacts)
            raw = b""
        else:
            pytest.fail("unverified download reached consumer execution")
        return subprocess.CompletedProcess(command, 0, raw, b"")
    monkeypatch.setattr(probe.subprocess, "run", controlled)
    output = tmp_path / "evidence"
    code = probe.main(["--repository", "Denissvgn/python-wiki-llm", "--version", "2.5.0",
                      "--harness-dir", str(tmp_path / "harness"), "--harness-sha", "c" * 40,
                      "--wheel-sha256", "a" * 64, "--sdist-sha256", "b" * 64,
                      "--artifacts", str(artifacts), "--work", str(tmp_path / "work"),
                      "--output", str(output)])
    assert code == 2 and len(calls) == 4
    assert "wheel archive digest differs" in json.loads((output / "probe.json").read_text())["reason"]


def test_failure_receipt_cannot_write_inside_protected_harness(tmp_path):
    harness = tmp_path / "harness"
    harness.mkdir()
    output = harness / "unexpected-evidence"
    code = probe.main(["--repository", "Denissvgn/python-wiki-llm", "--version", "2.5.0",
                      "--harness-dir", str(harness), "--harness-sha", "c" * 40,
                      "--wheel-sha256", "a" * 64, "--sdist-sha256", "b" * 64,
                      "--artifacts", str(tmp_path / "dist"), "--work", str(tmp_path / "work"),
                      "--output", str(output)])
    assert code == 2 and not output.exists() and list(harness.iterdir()) == []


def test_workflow_is_manual_native_read_only_and_does_not_rebuild():
    value = yaml.safe_load((ROOT / ".github/workflows/native-published-artifacts.yml").read_text())
    assert set(value.get("on", value.get(True))) == {"workflow_dispatch"}
    assert value["permissions"] == {"contents": "read"}
    job = value["jobs"]["native"]
    assert job["runs-on"] == "windows-2025" and job["timeout-minutes"] == 35
    steps = job["steps"]
    assert all(not step.get("continue-on-error", False) for step in steps)
    checkouts = [step for step in steps if step.get("uses", "").startswith("actions/checkout@")]
    assert len(checkouts) == 2 and all(s["with"]["persist-credentials"] is False for s in checkouts)
    assert checkouts[1]["with"]["ref"] == "${{ inputs.harness-sha }}"
    commands = "\n".join(step.get("run", "") for step in steps)
    assert "-m build" not in commands and "pytest" not in commands and "git push" not in commands
    assert "Scripts/python.exe -I probe-tools/release/native_published_artifacts.py" in commands
    assert "--wheel-sha256 $env:WHEEL_SHA256" in commands and "--sdist-sha256 $env:SDIST_SHA256" in commands
    assert "--git-stdin-adapter" in commands
    inputs = value.get("on", value.get(True))["workflow_dispatch"]["inputs"]
    assert inputs["git-stdin-adapter"]["default"] is False
    upload = steps[-1]
    assert upload["if"] == "${{ always() }}" and upload["with"]["if-no-files-found"] == "error"
    assert "github.run_id" in upload["with"]["name"] and "github.run_attempt" in upload["with"]["name"]


@pytest.mark.parametrize("failure", ["compiler", "parity", "contracts", None])
def test_adapter_requires_native_build_and_independent_contracts(tmp_path, monkeypatch, failure):
    # Ordering/failure controls only; actual executable contracts run on Windows.
    real = tmp_path / "original-git.exe"
    real.write_bytes(b"original helper")
    compiler = tmp_path / "Microsoft.NET/Framework64/v4.0.30319/csc.exe"
    if failure != "compiler":
        compiler.parent.mkdir(parents=True)
        compiler.write_bytes(b"native compiler fixture")
    monkeypatch.setattr(probe.shutil, "which", lambda *a, **kw: str(real))
    output = tmp_path / "evidence"
    output.mkdir()
    environment = {"SystemRoot": str(tmp_path), "PATH": "original-path"}
    calls = []
    def run(label, command, *, env):
        calls.append(label)
        if label == "git-adapter-build":
            (output / "git-adapter/git.exe").write_bytes(b"compiled adapter fixture")
            assert env == environment
            return b""
        assert env == environment or env["AGENT_WIKI_REAL_GIT"] == str(real)
        if label == "git-adapter-contracts":
            return json.dumps({"status": "fail" if failure == "contracts" else "pass", "native": "win32"}).encode()
        if failure == "parity" and label == "git-adapted-0":
            return b"changed Git output"
        return b"same original Git output"
    if failure:
        with pytest.raises(probe.ProbeError):
            probe.prepare_git_adapter(tmp_path / "harness", output, environment, run)
        assert not (output / "git-adapter.json").exists()
        if failure == "compiler":
            assert calls == []
        elif failure == "parity":
            assert "git-adapter-contracts" not in calls
    else:
        adapted, receipt = probe.prepare_git_adapter(tmp_path / "harness", output, environment, run)
        assert adapted["PATH"].startswith(str(output / "git-adapter"))
        assert adapted["AGENT_WIKI_REAL_GIT"] == str(real)
        assert environment == {"SystemRoot": str(tmp_path), "PATH": "original-path"}
        assert receipt["provider_modified"] is False
        assert "plain 2.5.0 remains affected" in receipt["qualification"]
        assert receipt["contracts"]["status"] == "pass"
        assert receipt["source_sha256"] == hashlib.sha256((ROOT / "release/git_stdin_adapter.cs").read_bytes()).hexdigest()
