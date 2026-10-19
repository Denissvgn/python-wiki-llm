"""Operation isolation and unchanged maintained-producer execution contracts."""

from __future__ import annotations

import copy
import hashlib
import json
import os
from pathlib import Path
from types import SimpleNamespace
import subprocess
import venv
import uuid
import zipfile
import stat
import xml.etree.ElementTree as ET

import pytest

from release import preflight_runner as runner

ROOT = Path(__file__).parents[1]
BINDING = {"repository_root": str(ROOT), "kind": "local-pre-release-work/v1"}
SHA = "a" * 40


def test_launcher_probe_preserves_virtualenv_symlink_spelling(tmp_path):
    # Frozen host suites deliberately have no checkout-local .venv; construct
    # this fixture without pip or any mutation of the executing environment.
    venv.EnvBuilder(with_pip=False, symlinks=os.name != "nt").create(tmp_path / ".venv")
    observed = runner.launcher_probe(tmp_path)
    expected = str(runner._python(tmp_path / ".venv"))
    assert observed["launcher"] == expected
    assert observed["executable"] == expected
    assert observed["prefix"] == str(tmp_path / ".venv")
    assert observed["prefix"] != observed["base_prefix"]


def test_wrong_launcher_fails_before_stage_mutation(tmp_path, monkeypatch):
    work = runner.claim_work(tmp_path / "work", BINDING)
    monkeypatch.setattr(
        runner.subprocess,
        "run",
        lambda *a, **k: subprocess.CompletedProcess(
            a[0],
            0,
            json.dumps(
                {
                    "prefix": "/framework",
                    "base_prefix": "/framework",
                    "executable": "/framework/python",
                }
            ),
            "",
        ),
    )
    monkeypatch.setattr(
        runner,
        "stage_commands",
        lambda *a, **k: pytest.fail("commands must not be rendered"),
    )
    before = {path.name: path.read_bytes() for path in work.iterdir()}
    with pytest.raises(runner.RunnerError, match="launcher/prefix mismatch"):
        runner.execute_stage(
            "prepare",
            repo=ROOT,
            work=work,
            binding=BINDING,
            candidate_sha=SHA,
            version="3.0.0",
        )
    assert {path.name: path.read_bytes() for path in work.iterdir()} == before


@pytest.mark.parametrize("occupied", ["directory", "file", "symlink"])
def test_claim_never_adopts_occupied_or_symlink_scratch(tmp_path, occupied):
    work = tmp_path / "work"
    unrelated = tmp_path / "unrelated"
    unrelated.mkdir()
    sentinel = unrelated / "sentinel"
    sentinel.write_bytes(b"keep\x00\r\n")
    if occupied == "directory":
        work.mkdir()
        (work / "mine").write_bytes(b"user data")
    elif occupied == "file":
        work.write_bytes(b"user data")
    else:
        try:
            work.symlink_to(unrelated, target_is_directory=True)
        except OSError:
            pytest.skip("native symlink creation unavailable")
    with pytest.raises(runner.RunnerError, match="occupied|symbolic link"):
        runner.claim_work(work, BINDING)
    assert sentinel.read_bytes() == b"keep\x00\r\n"
    if occupied == "directory":
        assert (work / "mine").read_bytes() == b"user data"


def test_owner_binding_refuses_replacement_and_malformed_metadata(tmp_path):
    work = runner.claim_work(tmp_path / "work", BINDING)
    assert runner.validate_owned_work(work, BINDING) == work
    with pytest.raises(runner.RunnerError, match="binding mismatch"):
        runner.validate_owned_work(work, {**BINDING, "kind": "different"})
    marker = work / runner.OWNER_FILE
    marker.write_text('{"schema_version":1,"schema_version":2}')
    with pytest.raises(runner.RunnerError, match="duplicate"):
        runner.validate_owned_work(work, BINDING)


def test_full_driver_keeps_maintained_owners_and_strict_full_suite(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(runner, "platform", SimpleNamespace(system=lambda: "Darwin"))
    monkeypatch.setattr(
        runner, "sys", SimpleNamespace(version_info=SimpleNamespace(major=3, minor=14))
    )
    commands = runner.stage_commands(
        "rehearsal", ROOT, tmp_path, candidate_sha=SHA, version="3.0.0"
    )
    names = [command.name for command in commands]
    assert names[:3] == [
        "contract-preflight",
        "maintained-static-checks",
        "freeze-source",
    ]
    full = next(command for command in commands if command.name == "strict-host-core")
    collection = next(command for command in commands if command.name == "collect-host-core")
    assert names.index("collect-host-core") < names.index("strict-host-core")
    assert "--collect" in collection.argv and "shadow" in collection.argv
    assert full.argv[1:5] == ("-m", "pytest", "tests", "-q")
    assert "--strict-config" in full.argv and "xfail_strict=true" in full.argv
    assert (
        "--minimum-collected"
        in next(
            command for command in commands if command.name == "verify-host-junit"
        ).argv
    )
    admission = next(command for command in commands if command.name == "verify-host-junit")
    assert str(ROOT / "release/preflight_runner.py") in admission.argv
    assert "--inventory" in admission.argv and "--started" in admission.argv
    assert admission.argv[admission.argv.index("--minimum-collected") + 1] == "5322"
    assert admission.argv[admission.argv.index("--minimum-passed") + 1] == "5070"
    assert "LLM_WIKI_CACHE_DIR" not in collection.environment
    assert "LLM_WIKI_CACHE_DIR" not in full.environment
    assert collection.environment == full.environment
    for name in [
        "compare-builds",
        "complete-artifact-smoke-wheel",
        "complete-artifact-smoke-sdist",
        "compare-artifact-smoke",
    ]:
        assert name in names
    assert names.index("compare-builds") < names.index("complete-artifact-smoke-wheel")
    installers = [
        command for command in commands if command.name.startswith("install-")
    ]
    assert installers and all(
        command.expected_prefix is not None for command in installers
    )
    for build_copy in ["a", "b"]:
        owner = next(
            command
            for command in commands
            if command.name == "install-build-lock-" + build_copy
        )
        assert "setup" in owner.argv
        assert str(ROOT / "release/dependency_downloads.py") in owner.argv
    assert not any(
        "push" in command.argv or "workflow" in command.argv or "upload" in command.argv
        for command in commands
    )


def test_artifact_parity_uses_identical_fixture_inputs_with_isolated_installs(tmp_path):
    commands = runner.stage_commands(
        "artifacts", ROOT, tmp_path, candidate_sha=SHA, version="3.1.0"
    )
    smoke = {
        kind: next(command for command in commands
                   if command.name == "complete-artifact-smoke-" + kind)
        for kind in ("wheel", "sdist")
    }

    def argument(kind, flag):
        argv = smoke[kind].argv
        return argv[argv.index(flag) + 1]

    # Fixture adoption identities include CLI path arguments. The harness resets
    # its work tree on each serial run; different inputs cannot prove parity.
    assert argument("wheel", "--work") == argument("sdist", "--work")
    assert argument("wheel", "--expected-version") == argument("sdist", "--expected-version")
    assert argument("wheel", "--output") != argument("sdist", "--output")
    for flag in ("--python", "--mcp-python"):
        assert argument("wheel", flag) != argument("sdist", flag)


def test_unsupported_native_python_refuses_instead_of_renaming_lane(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(runner, "platform", SimpleNamespace(system=lambda: "Windows"))
    monkeypatch.setattr(
        runner, "sys", SimpleNamespace(version_info=SimpleNamespace(major=3, minor=14))
    )
    with pytest.raises(runner.RunnerError, match="no matching maintained"):
        runner.stage_commands(
            "host-core", ROOT, tmp_path, candidate_sha=SHA, version="3.0.0"
        )


def test_prepare_only_has_locked_setup_and_readiness_without_wiki_write(tmp_path, monkeypatch):
    monkeypatch.setattr(runner, "platform", SimpleNamespace(system=lambda: "Darwin"))
    commands = runner.stage_commands(
        "prepare", ROOT, tmp_path, candidate_sha=SHA, version="3.0.0"
    )
    assert [command.name for command in commands] == [
        "locked-node-npm",
        "prepared-typescript-owner",
        "provider-input-census",
        "source-archive-budget",
        "repository-doctor",
        "wiki-lint",
        "repository-ci",
        "storage-audit",
    ]
    assert all(
        not ({"sync", "prune", "adopt", "commit"} & set(command.argv))
        for command in commands
    )


@pytest.mark.parametrize("system", ["Windows", "Unknown"])
def test_prepare_refuses_unsupported_setup_hosts(tmp_path, monkeypatch, system):
    monkeypatch.setattr(runner, "platform", SimpleNamespace(system=lambda: system))
    with pytest.raises(runner.RunnerError, match="supported native setup host"):
        runner.stage_commands(
            "prepare", ROOT, tmp_path, candidate_sha=SHA, version="3.0.0"
        )


def _execute_fake(tmp_path, monkeypatch, returncodes):
    work = runner.claim_work(tmp_path / "work", BINDING)
    monkeypatch.setattr(
        runner, "launcher_probe", lambda *a, **k: {"prefix": "isolated"}
    )
    calls = []

    def run(argv, **kwargs):
        calls.append(argv)
        kwargs["stdout"].write(b"retained producer output\n")
        return subprocess.CompletedProcess(argv, returncodes.pop(0))

    monkeypatch.setattr(runner.subprocess, "run", run)
    commands = [
        runner.Command("contract-preflight", ("trusted", "first"), ROOT),
        runner.Command("maintained-static-checks", ("trusted", "second"), ROOT),
        runner.Command("freeze-source", ("trusted", "heavy"), ROOT),
    ]
    monkeypatch.setattr(runner, "stage_commands", lambda *a, **k: commands)
    result = runner.execute_stage(
        "rehearsal",
        repo=ROOT,
        work=work,
        binding=BINDING,
        candidate_sha=SHA,
        version="3.0.0",
    )
    return work, result, calls


def test_independent_cheap_failures_retained_and_heavy_work_withheld(
    tmp_path, monkeypatch
):
    work, result, calls = _execute_fake(tmp_path, monkeypatch, [1, 2])
    assert result["status"] == "failed"
    assert calls == [["trusted", "first"], ["trusted", "second"]]
    assert [row["returncode"] for row in result["commands"]] == [1, 2]
    assert not (work / ".execution-lock").exists()
    assert (
        runner.verify_attempt(result, repo=ROOT, work=work, binding=BINDING)[
            "publication_authority"
        ]
        is False
    )


def test_attempt_verifier_rejects_argv_log_and_omitted_producer(tmp_path, monkeypatch):
    work, result, _ = _execute_fake(tmp_path, monkeypatch, [0, 0, 0])
    assert result["status"] == "passed"
    assert (
        runner.verify_attempt(result, repo=ROOT, work=work, binding=BINDING)["commands"]
        == 3
    )
    original = copy.deepcopy(result)
    for mutate in [
        lambda value: value["commands"][0]["argv"].append("untrusted"),
        lambda value: value["commands"].pop(),
        lambda value: value.update(publication_authority=True),
    ]:
        value = copy.deepcopy(original)
        mutate(value)
        Path(value["scratch"], "attempt.json").write_bytes(
            runner._canonical(value) + b"\n"
        )
        with pytest.raises(runner.RunnerError):
            runner.verify_attempt(value, repo=ROOT, work=work, binding=BINDING)
    Path(original["scratch"], "attempt.json").write_bytes(
        runner._canonical(original) + b"\n"
    )
    Path(original["commands"][0]["log"]).write_bytes(b"substituted output")
    with pytest.raises(runner.RunnerError, match="log differs"):
        runner.verify_attempt(original, repo=ROOT, work=work, binding=BINDING)


def test_subsequent_attempt_does_not_erase_failed_attempt(tmp_path, monkeypatch):
    work, first, _ = _execute_fake(tmp_path, monkeypatch, [1, 2])
    old = Path(first["scratch"], "attempt.json").read_bytes()
    monkeypatch.setattr(
        runner,
        "stage_commands",
        lambda *a, **k: [runner.Command("new", ("trusted",), ROOT)],
    )

    def run(argv, **kwargs):
        kwargs["stdout"].write(b"new output")
        return subprocess.CompletedProcess(argv, 0)

    monkeypatch.setattr(runner.subprocess, "run", run)
    second = runner.execute_stage(
        "contracts",
        repo=ROOT,
        work=work,
        binding=BINDING,
        candidate_sha=SHA,
        version="3.0.0",
    )
    assert first["attempt_id"] != second["attempt_id"]
    assert Path(first["scratch"], "attempt.json").read_bytes() == old
    assert (
        hashlib.sha256(old).hexdigest()
        != hashlib.sha256(
            Path(second["scratch"], "attempt.json").read_bytes()
        ).hexdigest()
    )


def test_evidence_inventory_excludes_mutable_consumer_symlinks(tmp_path, monkeypatch):
    work, result, _ = _execute_fake(tmp_path, monkeypatch, [0, 0, 0])
    scratch = Path(result["scratch"])
    consumer = scratch / "wheel-default-environment/bin"
    consumer.mkdir(parents=True)
    (consumer / "python").symlink_to(ROOT / ".venv/bin/python")
    paths = runner.evidence_paths(result)
    assert scratch / "attempt.json" in paths
    assert all("wheel-default-environment" not in path.parts for path in paths)
    assert len(paths) == 4


def test_shared_driver_environment_skip_stays_blocked(tmp_path, monkeypatch):
    work = runner.claim_work(tmp_path / "work", BINDING)
    monkeypatch.setattr(runner, "launcher_probe", lambda *a, **k: {})

    def run(argv, **kwargs):
        output = Path(argv[argv.index("--output") + 1])
        output.mkdir()
        (output / "results.json").write_text(json.dumps({"state": "blocked"}))
        kwargs["stdout"].write(b"missing prepared owner")
        return subprocess.CompletedProcess(argv, 1)

    monkeypatch.setattr(runner.subprocess, "run", run)
    result = runner.execute_stage(
        "contracts",
        repo=ROOT,
        work=work,
        binding=BINDING,
        candidate_sha=SHA,
        version="3.0.0",
    )
    assert result["status"] == "blocked"
    assert result["commands"][0]["status"] == "blocked"
    runner.verify_attempt(result, repo=ROOT, work=work, binding=BINDING)


def test_existing_wrong_runtime_refuses_without_cleanup_or_setup(tmp_path, monkeypatch):
    repo = tmp_path / "repo"
    node = repo / ".git/llm-wiki-ci-toolchains/node/bin/node"
    npm = repo / ".git/llm-wiki-ci-toolchains/node/lib/node_modules/npm/bin/npm-cli.js"
    for path in (node, npm):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"retained user/runtime bytes")
    (repo / "release").mkdir()
    (repo / "release/toolchain-lock.json").write_bytes(
        (ROOT / "release/toolchain-lock.json").read_bytes()
    )
    before = {path: path.read_bytes() for path in repo.rglob("*") if path.is_file()}
    calls = []
    monkeypatch.setattr(
        runner,
        "launcher_probe",
        lambda *a, **k: {"launcher": "/owned/.venv/bin/python"},
    )

    def run(argv, **kwargs):
        calls.append(argv)
        assert argv[0] == str(node), (
            "existing runtime must never invoke setup or removal"
        )
        return subprocess.CompletedProcess(argv, 0, "v0.0.0\n", "")

    monkeypatch.setattr(runner.subprocess, "run", run)
    with pytest.raises(runner.RunnerError, match="explicit reviewed repair"):
        runner.prepare_runtime(repo)
    assert len(calls) == 1
    assert {
        path: path.read_bytes() for path in repo.rglob("*") if path.is_file()
    } == before


def _archive_fixture(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(
        ["git", "init", "--quiet"], cwd=repo, check=True, capture_output=True
    )
    (repo / ".gitattributes").write_bytes(b"* text=auto eol=lf\n")
    (repo / "app.py").write_bytes(b"VALUE = 1\n")
    subprocess.run(["git", "add", ".gitattributes", "app.py"], cwd=repo, check=True, capture_output=True)
    subprocess.run(
        [
            "git",
            "-c",
            "user.name=Fixture",
            "-c",
            "user.email=fixture@example.invalid",
            "commit",
            "--quiet",
            "-m",
            "fixture",
        ],
        cwd=repo,
        check=True,
        capture_output=True,
    )
    sha = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    owner = {"repository_root": str(repo), "kind": "local-pre-release-work/v1"}
    work = runner.claim_work(tmp_path / "work", owner)
    scratch = work / ("attempt-" + str(uuid.uuid4()))
    scratch.mkdir()
    return repo, sha, scratch / "archive-budget"


@pytest.mark.parametrize("autocrlf", [False, True])
def test_exact_head_archive_screen_retains_bytes_and_refuses_occupied_output(tmp_path, autocrlf):
    repo, sha, output = _archive_fixture(tmp_path)
    subprocess.run(
        ["git", "config", "core.autocrlf", str(autocrlf).lower()],
        cwd=repo, check=True, capture_output=True,
    )
    result = runner.archive_budget(repo, output, sha)
    assert result["state"] == "passed" and result["candidate_sha"] == sha
    archive = output / "candidate-source.zip"
    assert result["archive_sha256"] == hashlib.sha256(archive.read_bytes()).hexdigest()
    with zipfile.ZipFile(archive) as stream:
        assert stream.read("app.py") == b"VALUE = 1\n"
    before = {path: path.read_bytes() for path in output.iterdir()}
    with pytest.raises(FileExistsError):
        runner.archive_budget(repo, output, sha)
    assert {path: path.read_bytes() for path in output.iterdir()} == before


@pytest.mark.parametrize("budget", ["MAX_ARCHIVE", "MAX_EXPANDED"])
def test_source_zip_uses_unchanged_hosted_budgets_and_preserves_oversized_bytes(
    tmp_path, monkeypatch, budget
):
    from release import hosted_evidence

    archive = tmp_path / "source.zip"
    with zipfile.ZipFile(archive, "w") as stream:
        stream.writestr("app.py", "VALUE = 1\n")
    before = archive.read_bytes()
    monkeypatch.setattr(hosted_evidence, budget, 1)
    result = runner.inspect_source_zip(archive)
    assert result["state"] == "blocked" and result["problems"]
    assert archive.read_bytes() == before
    assert (
        result["limits"][
            "archive_bytes" if budget == "MAX_ARCHIVE" else "expanded_bytes"
        ]
        == 1
    )


@pytest.mark.parametrize("kind", ["traversal", "symlink", "duplicate"])
def test_source_zip_refuses_unsafe_or_duplicate_members(tmp_path, kind):
    archive = tmp_path / "source.zip"
    with zipfile.ZipFile(archive, "w") as stream:
        if kind == "traversal":
            stream.writestr("../outside", "bad")
        elif kind == "symlink":
            member = zipfile.ZipInfo("link")
            member.create_system = 3
            member.external_attr = (stat.S_IFLNK | 0o777) << 16
            stream.writestr(member, "outside")
        else:
            stream.writestr("app.py", "first")
            with pytest.warns(UserWarning, match="Duplicate"):
                stream.writestr("app.py", "second")
    before = archive.read_bytes()
    with pytest.raises(runner.RunnerError, match="unsafe, nonregular or duplicate"):
        runner.inspect_source_zip(archive)
    assert archive.read_bytes() == before


def test_expansion_preflight_withholds_archive_and_wrong_head_creates_nothing(
    tmp_path, monkeypatch
):
    from release import hosted_evidence

    repo, sha, output = _archive_fixture(tmp_path)
    with pytest.raises(runner.RunnerError, match="differs from current HEAD"):
        runner.archive_budget(repo, output, "0" * 40)
    assert not output.exists()
    monkeypatch.setattr(hosted_evidence, "MAX_EXPANDED", 1)
    result = runner.archive_budget(repo, output, sha)
    assert result["state"] == "blocked" and result["archive"] is None
    assert not (output / "candidate-source.zip").exists()


def test_archive_block_does_not_hide_independent_wiki_health_checks(
    tmp_path, monkeypatch
):
    work = runner.claim_work(tmp_path / "work", BINDING)
    monkeypatch.setattr(runner, "platform", SimpleNamespace(system=lambda: "Darwin"))
    monkeypatch.setattr(runner, "launcher_probe", lambda *a, **k: {})
    calls = []

    def run(argv, **kwargs):
        calls.append(argv)
        kwargs["stdout"].write(b"retained evidence")
        if "archive-budget" in argv:
            output = Path(argv[argv.index("--output") + 1])
            output.mkdir()
            (output / "report.json").write_text(json.dumps({"state": "blocked"}))
            return subprocess.CompletedProcess(argv, 1)
        return subprocess.CompletedProcess(argv, 0)

    monkeypatch.setattr(runner.subprocess, "run", run)
    result = runner.execute_stage(
        "prepare",
        repo=ROOT,
        work=work,
        binding=BINDING,
        candidate_sha=SHA,
        version="3.0.0",
    )
    assert result["status"] == "blocked"
    assert len(calls) == 8
    assert result["commands"][-1]["name"] == "storage-audit"


def _local_core_inputs(tmp_path):
    root = tmp_path / "source"
    (root / "tests").mkdir(parents=True)
    nodes = ["tests/test_always.py::test_present", "tests/test_go_extract.py::test_go_inventory_evidence_contract"]
    for node in nodes:
        (root / node.partition("::")[0]).write_text("# isolated verifier input\n")
    collection = tmp_path / "collected.json"
    collection.write_text(json.dumps(nodes))
    started = tmp_path / "started.jsonl"
    started.write_bytes(b"")
    tree = ET.Element("testsuite")
    for node in nodes:
        filename, name = node.split("::")
        ET.SubElement(tree, "testcase", classname=filename[:-3].replace("/", "."), name=name)
    junit = tmp_path / "core.xml"
    ET.ElementTree(tree).write(junit, encoding="utf-8")
    allowlist = tmp_path / "allowlist.json"
    entry = {"lane": "core-macos-3.14", "node_id": nodes[1],
             "reason": "Prepared Go helper not available — Go extractor integration tests skipped",
             "owner_lane": "toolchains"}
    allowlist.write_text(json.dumps({"schema_version": "agent-wiki-release-skip-allowlist/v1", "entries": [entry]}))
    return {"repo": root, "inventory_path": collection, "started_path": started,
            "junit_path": junit, "allowlist_path": allowlist, "lane": entry["lane"],
            "minimum_collected": 2, "minimum_passed": 1}


def test_local_core_accepts_complete_prepared_helper_pass_without_claiming_hosted_owner(tmp_path):
    from argparse import Namespace
    from release import qualification

    inputs = _local_core_inputs(tmp_path)
    result = runner.verify_host_junit(**inputs)
    assert result["state"] == "passed" and result["inventory_complete"]
    assert result["counts"] == {"collected": 2, "passed": 2, "skipped": 0, "failed": 0, "errors": 0}
    assert result["conditional_passes"] == ["tests/test_go_extract.py::test_go_inventory_evidence_contract"]
    assert result["pending_hosted_owners"] == ["toolchains"]
    assert result["publication_authority"] is False
    # The bare hosted contract still requires its exact tuple; it is unchanged.
    with pytest.raises(qualification.QualificationError, match="skip contract changed"):
        qualification.verify_junit(Namespace(
            junit=inputs["junit_path"], lane=inputs["lane"], allowlist=inputs["allowlist_path"],
            minimum_collected=2, minimum_passed=1, discovery=False, output=tmp_path / "native.json",
        ))


def test_local_core_accepts_only_the_declared_owned_skip(tmp_path):
    inputs = _local_core_inputs(tmp_path)
    tree = ET.parse(inputs["junit_path"])
    entry = json.loads(inputs["allowlist_path"].read_text())["entries"][0]
    ET.SubElement(list(tree.getroot())[-1], "skipped", message=entry["reason"])
    tree.write(inputs["junit_path"], encoding="utf-8")
    result = runner.verify_host_junit(**inputs)
    assert result["counts"]["skipped"] == 1 and result["counts"]["passed"] == 1
    assert result["pending_hosted_owners"] == ["toolchains"]


def test_local_core_empty_baseline_requires_no_skips(tmp_path):
    inputs = _local_core_inputs(tmp_path)
    value = json.loads(inputs["allowlist_path"].read_text())
    value["entries"] = []
    inputs["allowlist_path"].write_text(json.dumps(value))
    assert runner.verify_host_junit(**inputs)["counts"]["passed"] == 2
    tree = ET.parse(inputs["junit_path"])
    ET.SubElement(list(tree.getroot())[0], "skipped", message="unexpected")
    tree.write(inputs["junit_path"], encoding="utf-8")
    with pytest.raises(runner.RunnerError, match="unowned skip"):
        runner.verify_host_junit(**inputs)


@pytest.mark.parametrize("minimum", [0, -1, True])
def test_local_core_cannot_disable_maintained_minimums(tmp_path, minimum):
    inputs = _local_core_inputs(tmp_path)
    inputs["minimum_collected"] = minimum
    with pytest.raises(runner.RunnerError, match="positive integers"):
        runner.verify_host_junit(**inputs)


def test_retained_local_core_report_replays_inputs_and_json_types(tmp_path, monkeypatch):
    inputs = _local_core_inputs(tmp_path)
    tree = ET.parse(inputs["junit_path"])
    reason = json.loads(inputs["allowlist_path"].read_text())["entries"][0]["reason"]
    ET.SubElement(list(tree.getroot())[-1], "skipped", message=reason)
    tree.write(inputs["junit_path"], encoding="utf-8")
    work = runner.claim_work(tmp_path / "work", BINDING)
    monkeypatch.setattr(runner, "launcher_probe", lambda *a, **k: {"prefix": "isolated"})

    def commands(stage, repo, scratch, **kwargs):
        return [runner.Command("verify-host-junit", (
            "trusted", "verify-host-junit", "--repo", str(inputs["repo"]),
            "--inventory", str(scratch / "collected.json"), "--started", str(scratch / "started.jsonl"),
            "--junit", str(scratch / "host-core.xml"), "--allowlist", str(inputs["allowlist_path"]),
            "--lane", inputs["lane"], "--minimum-collected", "2", "--minimum-passed", "1",
            "--output", str(scratch / "host-result.json"),
        ), ROOT)]

    def run(argv, **kwargs):
        scratch = Path(argv[argv.index("--output") + 1]).parent
        for name, key in (("collected.json", "inventory_path"), ("started.jsonl", "started_path"), ("host-core.xml", "junit_path")):
            (scratch / name).write_bytes(inputs[key].read_bytes())
        result = runner._host_report_for_command(commands("host-core", ROOT, scratch)[0])
        (scratch / "host-result.json").write_bytes(runner._canonical(result))
        kwargs["stdout"].write(b"verified local fixture\n")
        return subprocess.CompletedProcess(argv, 0)

    monkeypatch.setattr(runner, "stage_commands", commands)
    monkeypatch.setattr(runner.subprocess, "run", run)
    attempt = runner.execute_stage("host-core", repo=ROOT, work=work, binding=BINDING, candidate_sha=SHA, version="3.1.0")
    assert runner.verify_attempt(attempt, repo=ROOT, work=work, binding=BINDING)["status"] == "verified"
    assert {"collected.json", "started.jsonl", "host-core.xml", "host-result.json"} <= {
        path.name for path in runner.evidence_paths(attempt)
    }
    report = Path(attempt["scratch"]) / "host-result.json"
    forged = json.loads(report.read_bytes())
    assert forged["counts"]["passed"] == 1
    forged["counts"]["passed"] = True
    report.write_bytes(runner._canonical(forged))
    with pytest.raises(runner.RunnerError, match="collection/JUnit replay"):
        runner.verify_attempt(attempt, repo=ROOT, work=work, binding=BINDING)


@pytest.mark.parametrize("mutation", [
    "missing", "extra", "duplicate", "failure", "unowned-skip", "changed-reason",
    "dropped-owned-node", "collector-ran", "duplicate-inventory", "unreviewed-owner",
])
def test_local_core_rejects_incomplete_or_unowned_outcomes(tmp_path, mutation):
    inputs = _local_core_inputs(tmp_path)
    tree = ET.parse(inputs["junit_path"])
    root = tree.getroot()
    if mutation == "missing":
        root.remove(list(root)[0])
    elif mutation == "extra":
        ET.SubElement(root, "testcase", classname="tests.test_extra", name="test_extra")
    elif mutation == "duplicate":
        root.append(copy.deepcopy(list(root)[0]))
    elif mutation == "failure":
        ET.SubElement(list(root)[0], "failure", message="defect")
    elif mutation in {"unowned-skip", "changed-reason"}:
        ET.SubElement(list(root)[0 if mutation == "unowned-skip" else -1], "skipped", message="unowned")
    elif mutation == "dropped-owned-node":
        root.remove(list(root)[-1])
        nodes = json.loads(inputs["inventory_path"].read_text())[:1]
        inputs["inventory_path"].write_text(json.dumps(nodes))
        inputs["minimum_collected"] = 1
    elif mutation == "collector-ran":
        inputs["started_path"].write_text('"unexpected execution"\n')
    elif mutation == "duplicate-inventory":
        nodes = json.loads(inputs["inventory_path"].read_text())
        inputs["inventory_path"].write_text(json.dumps(nodes + nodes[:1]))
    else:
        value = json.loads(inputs["allowlist_path"].read_text())
        value["entries"][0]["owner_lane"] = "REVIEW-REQUIRED"
        inputs["allowlist_path"].write_text(json.dumps(value))
    tree.write(inputs["junit_path"], encoding="utf-8")
    with pytest.raises(ValueError):
        runner.verify_host_junit(**inputs)
