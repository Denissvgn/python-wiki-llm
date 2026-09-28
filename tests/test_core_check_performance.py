"""Frozen inputs, metric binding and cleanup for native core-check comparisons."""

import argparse
from copy import deepcopy
import io
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tarfile
from types import SimpleNamespace

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


def _replace_archive(args, role, member, *, revision=None):
    """Rebind an owned fixture so extraction, not digest validation, is exercised."""
    archive = args.output / f"{role}-source.tar"
    with tarfile.open(
        archive,
        "w:",
        format=tarfile.PAX_FORMAT,
        pax_headers={"comment": revision or getattr(args, role)},
    ) as stream:
        stream.addfile(member)
    manifest = args.output / "inputs.json"
    value = json.loads(manifest.read_text(encoding="utf-8"))
    value["files"][archive.name] = performance.digest(archive)
    performance.write(manifest, value)
    return performance.digest(manifest)


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


def test_prepare_requires_safe_extraction_before_creating_workspace(
    frozen, tmp_path, monkeypatch
):
    args, sha = frozen
    work = tmp_path / "work"
    # Model an unpatched interpreter without weakening the real tarfile module.
    monkeypatch.setattr(performance, "tarfile", SimpleNamespace())
    with pytest.raises(RuntimeError, match="requires tarfile.data_filter"):
        performance.prepare(
            argparse.Namespace(inputs=args.output, inputs_sha256=sha, work=work)
        )
    assert not work.exists()


@pytest.mark.parametrize("role", ["baseline", "candidate"])
def test_prepare_identifies_the_archive_with_wrong_revision(frozen, tmp_path, role):
    args, _ = frozen
    sha = _replace_archive(args, role, tarfile.TarInfo("value.txt"), revision="0" * 40)
    with pytest.raises(ValueError, match=f"{role} archive identity differs"):
        performance.prepare(
            argparse.Namespace(
                inputs=args.output, inputs_sha256=sha, work=tmp_path / "work"
            )
        )


@pytest.mark.parametrize("role", ["baseline", "candidate"])
@pytest.mark.parametrize("kind", ["traversal", "symlink", "hardlink", "fifo"])
def test_prepare_rejects_unsafe_archive_members(frozen, tmp_path, role, kind):
    args, _ = frozen
    member = tarfile.TarInfo("../escaped.txt" if kind == "traversal" else "unsafe")
    if kind in {"symlink", "hardlink"}:
        member.type = tarfile.SYMTYPE if kind == "symlink" else tarfile.LNKTYPE
        member.linkname = "../escaped.txt"
    elif kind == "fifo":
        member.type = tarfile.FIFOTYPE
    sha = _replace_archive(args, role, member)
    work = tmp_path / "work"
    with pytest.raises(tarfile.FilterError):
        performance.prepare(
            argparse.Namespace(inputs=args.output, inputs_sha256=sha, work=work)
        )
    assert not (work / "escaped.txt").exists()
    assert not (work / role / "unsafe").is_symlink()
    assert not (work / role / "unsafe").exists()


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
        ("adapter_inventory_sha256", "b" * 64),
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
        "adapter_inventory_sha256": None,
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
    kill_signal = object()

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
        assert command == ["owned"]
        assert options["stdin"] == subprocess.DEVNULL
        assert options["start_new_session"] is (system != "nt")
        return process

    def taskkill(command, **options):
        assert system == "nt"
        assert options["stdin"] == subprocess.DEVNULL
        assert options["timeout"] == 10 and options["check"] is True
        calls.append(command)

    monkeypatch.setattr(performance.subprocess, "Popen", popen)
    monkeypatch.setattr(performance.subprocess, "run", taskkill)
    # Model the entire platform boundary: Windows has neither killpg nor
    # SIGKILL. Local namespaces also leave the host's stdlib modules untouched.
    system_api = SimpleNamespace(name=system)
    signals = SimpleNamespace()
    if system == "posix":
        system_api.killpg = lambda pid, sig: calls.append((pid, sig))
        signals.SIGKILL = kill_signal
    monkeypatch.setattr(performance, "os", system_api)
    monkeypatch.setattr(performance, "signal", signals)
    with pytest.raises(subprocess.TimeoutExpired) as raised:
        performance.run_observation(["owned"], cwd=tmp_path, env={}, log=io.BytesIO())
    assert raised.value.cmd == ["owned"] and raised.value.timeout == performance.TIMEOUT
    assert process.waits == 2
    assert calls == (
        [["taskkill", "/PID", "424242", "/T", "/F"]]
        if system == "nt"
        else [(424242, kill_signal)]
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


def _inventory_work(tmp_path):
    work = tmp_path / "work"
    for role, inventory in (
        ("baseline", "{'knowledge_governance': frozenset({'_relative_path'})}"),
        ("candidate", "{'concept_identity': frozenset({'natural_key_for'})}"),
    ):
        policy = work / role / "tests/test_architecture_layers.py"
        policy.parent.mkdir(parents=True)
        policy.write_text(
            "import ast\nfrom pathlib import Path\n"
            f"{performance.ADAPTER_INVENTORY} = {inventory}\n"
            "def test_shared_validation_adapters_remain_thin():\n"
            "    root = Path(__file__).parents[1] / 'src/llm_wiki_cli/services'\n"
            f"    for family, names in {performance.ADAPTER_INVENTORY}.items():\n"
            "        tree = ast.parse((root / (family + '.py')).read_text())\n"
            "        defined = {n.name for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)}\n"
            "        assert names <= defined\n",
            encoding="utf-8",
        )
    services = work / "candidate/src/llm_wiki_cli/services"
    services.mkdir(parents=True)
    (services / "concept_identity.py").write_text("def natural_key_for(value):\n    return value\n")
    return work


@pytest.fixture
def policy_imports():
    previous_path = sys.path[:]
    previous_modules = {name: module for name, module in sys.modules.items()
                        if name == "tests" or name.startswith("tests.")}
    try:
        yield
    finally:
        sys.path[:] = previous_path
        for name in list(sys.modules):
            if name == "tests" or name.startswith("tests."):
                del sys.modules[name]
        sys.modules.update(previous_modules)


def test_moved_adapter_inventory_is_identical_input_for_both_policy_workers(tmp_path):
    work = _inventory_work(tmp_path)
    inventory = performance.comparison_inventory(work)
    assert inventory["removed"] == [["knowledge_governance", "_relative_path"]]
    assert inventory["added"] == [["concept_identity", "natural_key_for"]]
    assert inventory["baseline_sha256"] != inventory["candidate_sha256"]
    before = performance.tree_identity(work)
    for role in ("baseline", "candidate"):
        output = tmp_path / f"{role}.json"
        result = subprocess.run(
            [sys.executable, "-I", "-B", performance.__file__, "worker", "--work", str(work),
             "--inputs", str(tmp_path), "--role", role, "--target", "adapters", "--output", str(output)],
            stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=30,
        )
        assert result.returncode == 0, result.stderr
        row = json.loads(output.read_text())
        performance.validate_observation(
            row, target="adapters", role=role, coverage=False, memory=False,
            policy_sha256=performance.digest(work / role / "tests/test_architecture_layers.py"),
            adapter_inventory_sha256=inventory["candidate_sha256"],
        )
        with pytest.raises(ValueError, match="identity"):
            performance.validate_observation(
                row, target="adapters", role=role, coverage=False, memory=False,
                policy_sha256=row["policy_sha256"], adapter_inventory_sha256=inventory["baseline_sha256"],
            )
    assert performance.tree_identity(work) == before


@pytest.mark.parametrize("role", ["baseline", "candidate"])
def test_worker_retains_failed_assertion_traceback_with_current_inventory(tmp_path, role):
    work = _inventory_work(tmp_path)
    (work / "candidate/src/llm_wiki_cli/services/concept_identity.py").write_text("")
    output = tmp_path / "observation.json"
    result = subprocess.run(
        [sys.executable, "-I", "-B", performance.__file__, "worker", "--work", str(work),
         "--inputs", str(tmp_path), "--role", role, "--target", "adapters", "--output", str(output)],
        stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=30,
    )
    assert result.returncode == 1
    assert "test_shared_validation_adapters_remain_thin" in result.stderr
    assert "AssertionError" in result.stderr
    assert not output.exists()


@pytest.mark.parametrize("relative", ["knowledge_governance.py", "knowledge_governance/nested.py"])
def test_comparison_cannot_drop_requirements_for_remaining_definitions(tmp_path, relative):
    work = _inventory_work(tmp_path)
    path = work / "candidate/src/llm_wiki_cli/services" / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("class Adapter:\n    def _relative_path(self, value):\n        return value\n")
    with pytest.raises(ValueError, match="required adapter that still exists"):
        performance.comparison_inventory(work)


@pytest.mark.parametrize("declaration", [
    "get_inventory()", "{'../escape': frozenset({'validate'})}",
    "{'owner': frozenset({123})}", "{'owner': frozenset(build_names())}",
    "{'owner': frozenset({'one'}), 'owner': frozenset({'two'})}",
])
def test_adapter_inventory_rejects_nonliteral_or_ambiguous_data(tmp_path, declaration):
    policy = tmp_path / "tests/test_architecture_layers.py"
    policy.parent.mkdir()
    policy.write_text(f"{performance.ADAPTER_INVENTORY} = {declaration}\n")
    with pytest.raises(ValueError):
        performance.adapter_inventory(tmp_path)


def test_adapter_inventory_accepts_an_empty_literal_frozenset(tmp_path):
    policy = tmp_path / "tests/test_architecture_layers.py"
    policy.parent.mkdir()
    policy.write_text(f"{performance.ADAPTER_INVENTORY} = {{'owner': frozenset()}}\n")
    assert performance.adapter_inventory(tmp_path) == {"owner": []}


def test_mixed_missing_inventory_is_not_silently_accepted(tmp_path):
    work = _inventory_work(tmp_path)
    (work / "baseline/tests/test_architecture_layers.py").write_text("pass\n")
    with pytest.raises(ValueError, match="both policies"):
        performance.comparison_inventory(work)


def test_runtime_inventory_must_match_its_frozen_declaration(tmp_path, policy_imports):
    work = _inventory_work(tmp_path)
    policy = work / "baseline/tests/test_architecture_layers.py"
    policy.write_text(policy.read_text() + f"\n{performance.ADAPTER_INVENTORY}.clear()\n")
    inventory = performance.adapter_inventory(work / "baseline")
    module = performance.load_policy(work / "baseline", work / "candidate", policy.name, "baseline")
    with pytest.raises(ValueError, match="changed its declared adapter inventory"):
        performance.bind_inventory(module, inventory, performance.adapter_inventory(work / "candidate"))


def test_complete_adapter_controls_detect_a_weakened_candidate_assertion(tmp_path, policy_imports):
    work = tmp_path / "work"
    tests = Path(__file__).parent
    for role in ("baseline", "candidate"):
        target = work / role / "tests"
        target.mkdir(parents=True)
        (target / "__init__.py").write_text("")
        for name in ("test_architecture_layers.py", "python_source_inventory.py"):
            shutil.copyfile(tests / name, target / name)
    args = argparse.Namespace(work=work)
    results = performance.adapter_control_parity(args)
    assert [r["expected_pass"] for r in results] == [True, False, False, False, False]
    policy = work / "candidate/tests/test_architecture_layers.py"
    policy.write_text(policy.read_text() + "\ndef test_shared_validation_adapters_remain_thin():\n    pass\n")
    with pytest.raises(ValueError, match="adapter control outcome differs: missing/candidate"):
        performance.adapter_control_parity(args)
