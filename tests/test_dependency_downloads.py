"""Trusted wheel hashes remain authoritative across cold, warm and hostile caches."""

import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys

import pytest

from release import dependency_downloads as d

ROOT = Path(__file__).parents[1]


def lock_file(path, name="owned", raw=b"owned wheel", version="1.0"):
    path.write_text(
        f"{name}=={version} \\\n    --hash=sha256:{hashlib.sha256(raw).hexdigest()}\n",
        encoding="utf-8",
    )
    return path


def store(path, identity, lock, raw=b"owned wheel"):
    path.mkdir()
    (path / "owned-1.0-py3-none-any.whl").write_bytes(raw)
    d.write_json(
        path / "manifest.json",
        {"identity": identity, "files": d.wheel_inventory(path, lock)},
    )


def test_minimal_locks_preserve_release_policy_and_explicit_backend_runtime():
    full = d.read_lock(ROOT / "release/requirements.txt")
    build = d.read_lock(ROOT / "release/build-requirements.txt")
    validation = d.read_lock(ROOT / "release/validation-requirements.txt")
    assert set(build) == {"build", "setuptools", "pip", "packaging", "pyproject-hooks"}
    assert set(build) < set(full) and set(validation) < set(full)
    assert not {"build", "pyproject-hooks"} & validation.keys()
    assert {"twine", "pyyaml", "secretstorage", "jeepney"} <= validation.keys()
    assert not {"bandit", "ruff", "pyright", "pip-audit"} & validation.keys()
    assert all(row == full[name] for name, row in validation.items())
    assert all(row == full[name] for name, row in build.items())
    assert (
        f"setuptools=={build['setuptools']['version']}"
        in (ROOT / "pyproject.toml").read_text()
    )


@pytest.mark.parametrize(
    "text",
    [
        "owned>=1.0 --hash=sha256:" + "a" * 64,
        "owned==1.0",
        "owned==1.0 --hash=md5:" + "a" * 32,
        "owned==1.0 --hash=sha256:" + "a" * 64 + " --index-url=https://owned.invalid",
        "agent-wiki-cli==1.0 --hash=sha256:" + "a" * 64,
        "-r other.txt",
        "-c other.txt",
        "-e ./candidate",
        "https://owned.invalid/owned.whl",
        'owned==1.0; python_version > "3.10" --hash=sha256:' + "a" * 64,
        "owned==1.0 --hash=sha256:"
        + "a" * 64
        + "\nowned==1.0 --hash=sha256:"
        + "a" * 64,
        "owned==1.0 \\",
        "",
    ],
)
def test_lock_rejects_unbounded_unhashed_or_candidate_inputs(tmp_path, text):
    path = tmp_path / "lock.txt"
    path.write_text(text)
    with pytest.raises(d.DependencyError):
        d.read_lock(path)


@pytest.mark.parametrize(
    "field",
    [
        "os",
        "os_version",
        "architecture",
        "python",
        "implementation",
        "abi",
        "platform",
        "bootstrap_pip",
    ],
)
def test_cache_identity_binds_actual_platform_interpreter_and_installer(
    tmp_path, monkeypatch, field
):
    path = lock_file(tmp_path / "lock.txt")
    before = d.identity(path, "build")
    environment = deepcopy(before["environment"])
    environment[field] = str(environment[field]) + "-changed"
    monkeypatch.setattr(d, "environment_identity", lambda: environment)
    assert d.identity(path, "build")["key"] != before["key"]


def test_cache_identity_binds_lock_policy_role_and_namespace(tmp_path, monkeypatch):
    path = lock_file(tmp_path / "lock.txt")
    before = d.identity(path, "build")
    assert d.identity(path, "validation")["key"] != before["key"]
    assert d.identity(path, "build", "probe-123-1")["key"] != before["key"]
    lock_file(path, raw=b"other approved bytes")
    assert d.identity(path, "build")["key"] != before["key"]
    policy = tmp_path / "policy.py"
    policy.write_text("owned policy")
    monkeypatch.setattr(d, "__file__", str(policy))
    assert d.identity(path, "build")["key"] != before["key"]


@pytest.mark.parametrize(
    "mutation",
    [
        "stale",
        "corrupt",
        "missing",
        "extra",
        "candidate",
        "directory",
        "symlink",
        "manifest-link",
        "wrong-files",
        "duplicate-json",
        "nonfinite-json",
        "oversized",
    ],
)
def test_restored_cache_is_untrusted_even_with_matching_service_key(
    tmp_path, monkeypatch, mutation
):
    path = lock_file(tmp_path / "lock.txt")
    lock = d.read_lock(path)
    identity = d.identity(path, "build")
    cache = tmp_path / "cache"
    store(cache, identity, lock)
    wheel = cache / "owned-1.0-py3-none-any.whl"
    if mutation == "stale":
        manifest = d.read_json(cache / "manifest.json")
        manifest["identity"]["key"] = "old-key"
        d.write_json(cache / "manifest.json", manifest)
    elif mutation == "corrupt":
        wheel.write_bytes(b"corruption")
    elif mutation == "missing":
        wheel.unlink()
    elif mutation == "extra":
        (cache / "candidate.tar").write_bytes(b"candidate")
    elif mutation == "candidate":
        wheel.rename(cache / "agent_wiki_cli-1.0-py3-none-any.whl")
    elif mutation == "directory":
        wheel.unlink()
        wheel.mkdir()
    elif mutation in {"symlink", "manifest-link"}:
        target = wheel if mutation == "symlink" else cache / "manifest.json"
        original = Path.is_symlink
        monkeypatch.setattr(
            Path, "is_symlink", lambda self: self == target or original(self)
        )
    elif mutation == "wrong-files":
        manifest = d.read_json(cache / "manifest.json")
        manifest["files"][wheel.name]["sha256"] = "a" * 64
        d.write_json(cache / "manifest.json", manifest)
    elif mutation == "duplicate-json":
        (cache / "manifest.json").write_text('{"identity":{},"identity":{}}')
    elif mutation == "nonfinite-json":
        (cache / "manifest.json").write_text('{"identity":NaN,"files":{}}')
    else:
        monkeypatch.setattr(d, "MAX_WHEEL", 1)
    with pytest.raises((d.DependencyError, ValueError)):
        d.verify_cache(cache, identity, lock)


def test_snapshot_revalidates_after_copy_and_never_links_the_restored_store(
    tmp_path, monkeypatch
):
    path = lock_file(tmp_path / "lock.txt")
    lock = d.read_lock(path)
    identity = d.identity(path, "build")
    cache = tmp_path / "cache"
    store(cache, identity, lock)
    snapshot = tmp_path / "snapshot"
    d.copy_verified(cache, snapshot, identity, lock)
    wheel = "owned-1.0-py3-none-any.whl"
    (cache / wheel).write_bytes(b"changed after snapshot")
    assert (snapshot / wheel).read_bytes() == b"owned wheel"
    assert d.verify_cache(snapshot, identity, lock)
    copy = d.shutil.copyfile

    def corrupt_copy(source, target, **kwargs):
        copy(source, target, **kwargs)
        Path(target).write_bytes(b"changed during snapshot")

    monkeypatch.setattr(d.shutil, "copyfile", corrupt_copy)
    with pytest.raises(d.DependencyError):
        d.copy_verified(snapshot, tmp_path / "corrupt-snapshot", identity, lock)


@pytest.mark.parametrize(
    "scenario",
    [
        "disabled",
        "cold",
        "warm",
        "stale",
        "corrupt",
        "unavailable",
        "incompatible",
        "network-failure",
        "install-failure",
        "extra-installed",
    ],
)
def test_setup_fallback_always_reverifies_and_keeps_failures_blocking(
    tmp_path, monkeypatch, scenario
):
    path = lock_file(tmp_path / "lock.txt")
    lock = d.read_lock(path)
    identity = d.identity(path, "build")
    state = tmp_path / "identity.json"
    d.write_json(state, identity)
    cache = None if scenario == "disabled" else tmp_path / "cache"
    if scenario in {"warm", "stale", "corrupt", "incompatible"}:
        assert cache is not None
        store(cache, identity, lock)
        if scenario == "stale":
            manifest = d.read_json(cache / "manifest.json")
            manifest["identity"]["key"] = "old"
            d.write_json(cache / "manifest.json", manifest)
        elif scenario == "corrupt":
            (cache / "owned-1.0-py3-none-any.whl").write_bytes(b"bad")
    calls = []

    def invoke(command, log):
        calls.append(log.name)
        log.write_text("owned command result")
        if scenario == "incompatible" and log.name == "cache-resolution.log":
            raise d.DependencyError("wheel compatibility differs")
        if scenario == "network-failure" and log.name == "download.log":
            raise d.DependencyError("index unavailable")
        if scenario == "install-failure" and log.name == "install.log":
            raise d.DependencyError("installer failed")
        if "download" in command:
            destination = Path(command[command.index("--dest") + 1])
            (destination / "owned-1.0-py3-none-any.whl").write_bytes(b"owned wheel")
        return 0.01

    monkeypatch.setattr(d, "run", invoke)
    monkeypatch.setattr(sys, "prefix", str(tmp_path / "fresh-venv"))
    monkeypatch.setattr(d, "installed", lambda: {"pip": "bootstrap"})
    installed = {"owned": "1.0"}
    if scenario == "extra-installed":
        installed["unlocked-tool"] = "1.0"
    monkeypatch.setattr(
        d.subprocess, "check_output", lambda *a, **k: json.dumps(installed).encode()
    )
    args = argparse.Namespace(
        lock=path,
        profile="build",
        namespace="release",
        identity=state,
        cache=cache,
        cache_available=scenario != "unavailable",
        output=tmp_path / "evidence",
    )
    failed = scenario in {"network-failure", "install-failure", "extra-installed"}
    if failed:
        with pytest.raises(d.DependencyError):
            d.setup(args)
    else:
        assert d.setup(args) == 0
    receipt = d.read_json(args.output / "setup.json")
    assert receipt["complete"] is not failed
    if failed:
        assert receipt["error"] and receipt["cache_exported"] is False
    else:
        expected = {
            "disabled": "disabled",
            "cold": "miss",
            "warm": "hit",
            "stale": "rejected",
            "corrupt": "rejected",
            "unavailable": "unavailable",
            "incompatible": "rejected",
        }[scenario]
        assert receipt["cache_state"] == expected
        assert ("download.log" not in calls) is (scenario == "warm")
        assert receipt["installed"] == {"owned": "1.0"}
        if cache is not None:
            assert d.verify_cache(cache, identity, lock)


def test_commands_keep_download_and_install_boundaries_and_ignore_pip_overrides(
    tmp_path, monkeypatch
):
    lock = tmp_path / "lock"
    wheels = tmp_path / "private-wheels"
    download = d.pip_command("download", lock, destination=wheels)
    install = d.pip_command("install", lock, find_links=wheels)
    for command in (download, install):
        assert command[:4] == [sys.executable, "-I", "-m", "pip"]
        assert {
            "--isolated",
            "--require-hashes",
            "--only-binary=:all:",
            "--no-cache-dir",
        } <= set(command)
        assert "--no-deps" not in command
    assert "--no-index" in install and "--force-reinstall" in install
    assert "--index-url" not in install
    with pytest.raises(d.DependencyError):
        d.pip_command("install", lock)
    monkeypatch.setenv("PIP_EXTRA_INDEX_URL", "https://untrusted.invalid")
    monkeypatch.setenv("PYTHONPATH", "untrusted")
    env = d.command_environment()
    assert "PIP_EXTRA_INDEX_URL" not in env and "PYTHONPATH" not in env
    assert env["PIP_CONFIG_FILE"] == d.os.devnull


def test_preexisting_environment_cannot_supply_an_undeclared_tool(
    tmp_path, monkeypatch
):
    path = lock_file(tmp_path / "lock")
    state = tmp_path / "identity.json"
    d.write_json(state, d.identity(path, "build"))
    monkeypatch.setattr(d, "installed", lambda: {"pip": "bootstrap", "twine": "7.0.0"})
    with pytest.raises(d.DependencyError, match="fresh isolated"):
        d.setup(
            argparse.Namespace(
                lock=path,
                profile="build",
                namespace="release",
                identity=state,
                cache=None,
                cache_available=True,
                output=tmp_path / "setup",
            )
        )


@pytest.mark.parametrize(
    "change",
    ["pip-replaced", "extra-candidate", "changed-wheel", "changed-key", "changed-role"],
)
def test_cache_save_rechecks_content_and_identity_after_building(
    tmp_path, monkeypatch, change
):
    path = lock_file(tmp_path / "lock.txt")
    lock = d.read_lock(path)
    expected = d.identity(path, "build")
    state = tmp_path / "identity.json"
    d.write_json(state, expected)
    cache = tmp_path / "cache"
    store(cache, expected, lock)
    args = argparse.Namespace(
        lock=path, profile="build", namespace="release", identity=state, cache=cache
    )
    if change == "pip-replaced":
        actual = deepcopy(expected["environment"])
        actual["bootstrap_pip"] = "installed-locked-pip"
        monkeypatch.setattr(d, "environment_identity", lambda: actual)
        assert d.verify_command(args) == 0
        return
    if change == "extra-candidate":
        (cache / "agent_wiki_cli-1.0-py3-none-any.whl").write_bytes(
            b"private candidate"
        )
    elif change == "changed-wheel":
        (cache / "owned-1.0-py3-none-any.whl").write_bytes(
            b"mutated after installation"
        )
    elif change == "changed-key":
        expected["key"] = "unbound-key"
        d.write_json(state, expected)
    else:
        args.profile = "validation"
    with pytest.raises(d.DependencyError):
        d.verify_command(args)
