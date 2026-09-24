"""Native-boundary isolation, actual workers, and coverage merge controls."""

from pathlib import Path
import argparse
import subprocess
import sys
import tarfile
from types import SimpleNamespace
import xml.etree.ElementTree as ET

from coverage import CoverageData
import pytest

from release import core_shard_runner as r
from tests.test_core_shards import context, NODES


@pytest.mark.parametrize("system", ["nt", "posix"])
@pytest.mark.parametrize("failure", ["timeout", "interrupt", "cleanup"])
def test_owned_tree_is_reaped_on_timeout_or_cancellation(
    monkeypatch, tmp_path, system, failure
):
    calls = []
    kill_signal = object()

    class Process:
        pid = 40404
        waits = 0

        def wait(self, timeout):
            self.waits += 1
            if self.waits == 1:
                if failure == "interrupt":
                    raise KeyboardInterrupt()
                raise subprocess.TimeoutExpired(["owned"], timeout)
            assert timeout == 10
            return -1

        def kill(self):
            calls.append("root-killed")

    process = Process()

    def start(command, **options):
        assert options["stdin"] == subprocess.DEVNULL
        assert options["start_new_session"] is (system == "posix")
        return process

    def kill_tree(command, **options):
        if failure == "cleanup":
            raise OSError("owned cleanup failure")
        calls.append(command)

    def kill_group(pid, sig):
        assert sig is kill_signal
        kill_tree(pid)

    os_api = SimpleNamespace(name=system)
    signals = SimpleNamespace()
    if system == "posix":
        os_api.killpg, signals.SIGKILL = kill_group, kill_signal
    monkeypatch.setattr(r, "os", os_api)
    monkeypatch.setattr(r, "signal", signals)
    monkeypatch.setattr(r.subprocess, "Popen", start)
    monkeypatch.setattr(r.subprocess, "run", kill_tree)
    if failure == "timeout":
        result = r.invoke(["owned"], tmp_path, {}, tmp_path / "worker.log", timeout=1)
        assert result["exit_code"] == 124 and result["error"]
    else:
        with pytest.raises(
            KeyboardInterrupt if failure == "interrupt" else RuntimeError
        ):
            r.invoke(["owned"], tmp_path, {}, tmp_path / "worker.log", timeout=1)
    assert process.waits == 2
    assert calls == (
        ["root-killed"]
        if failure == "cleanup"
        else [["taskkill", "/PID", "40404", "/T", "/F"]]
        if system == "nt"
        else [40404]
    )


def test_worker_temporary_and_cache_roots_are_private_and_addopts_are_removed(
    tmp_path, monkeypatch
):
    monkeypatch.setenv("PYTEST_ADDOPTS", "--deselect everything")
    monkeypatch.setenv("PYTEST_PLUGINS", "unexpected_plugin")
    monkeypatch.setenv("LLM_WIKI_CACHE_DIR", str(tmp_path / "caller-cache"))
    one = r.child_environment(
        tmp_path / "one", tmp_path / "temp-one", tmp_path / "source.tar"
    )
    two = r.child_environment(
        tmp_path / "two", tmp_path / "temp-two", tmp_path / "source.tar"
    )
    for name in (
        "TMPDIR",
        "TMP",
        "TEMP",
        "XDG_CACHE_HOME",
        "PIP_CACHE_DIR",
    ):
        assert (
            one[name] != two[name]
            and Path(one[name]).is_dir()
            and Path(two[name]).is_dir()
        )
    assert not {"PYTEST_ADDOPTS", "PYTEST_PLUGINS", "LLM_WIKI_CACHE_DIR"}.intersection(
        one
    )
    assert "LLM_WIKI_CACHE_DIR" not in two


def test_worker_environment_preserves_existing_repository_cache_assertions(
    tmp_path, monkeypatch
):
    # Replay the four original contracts under the actual worker environment.
    # A product cache override made all four fail on every hosted platform.
    monkeypatch.setenv("LLM_WIKI_CACHE_DIR", str(tmp_path / "caller-cache"))
    environment = r.child_environment(
        tmp_path / "state", tmp_path / "temporary", tmp_path / "source.tar"
    )
    nodes = [
        "tests/test_extractor_helpers.py::test_helper_cache_root_resolves_git_env_explicit_and_worktree",
        "tests/test_inventory_cache.py::test_resolves_normal_git_dir",
        "tests/test_inventory_cache.py::test_resolves_git_worktree_file",
        "tests/test_sync.py::TestSyncInventoryRuntime::test_default_sync_creates_git_cache",
    ]
    completed = subprocess.run(
        [sys.executable, "-m", "pytest", *nodes, *r.s.FLAGS],
        cwd=Path(__file__).parents[1],
        env=environment,
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr


def test_real_worker_recollects_all_nodes_and_runs_only_its_planned_files(tmp_path):
    root = tmp_path / "candidate"
    tests = root / "tests"
    tests.mkdir(parents=True)
    for name in ("one", "two"):
        (tests / f"test_{name}.py").write_text("def test_owned():\n    assert True\n")
    nodes = [f"tests/test_{name}.py::test_owned" for name in ("one", "two")]
    value = r.s.plan(nodes, context("core-windows-3.13"), 2)
    plan = tmp_path / "plan.json"
    r.q.write_json(plan, value)
    for index in (0, 1):
        output = tmp_path / str(index)
        output.mkdir()
        completed = subprocess.run(
            [
                sys.executable,
                "-I",
                str(Path(r.__file__).resolve()),
                "worker",
                "--plan",
                str(plan),
                "--index",
                str(index),
                "--output",
                str(output),
            ],
            cwd=root,
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert completed.returncode == 0, completed.stdout + completed.stderr
        assert r.s.read(output / "collected.json") == sorted(nodes)
        assert set(r.s.junit(output / "junit.xml")) == set(
            value["shards"][index]["nodes"]
        )
    (tests / "test_added.py").write_text("def test_added():\n    assert True\n")
    output = tmp_path / "changed"
    output.mkdir()
    completed = subprocess.run(
        [
            sys.executable,
            "-I",
            str(Path(r.__file__).resolve()),
            "worker",
            "--plan",
            str(plan),
            "--index",
            "0",
            "--output",
            str(output),
        ],
        cwd=root,
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert completed.returncode != 0
    assert "full collection differs" in completed.stdout + completed.stderr
    assert (output / "started.jsonl").read_text() == ""


def coverage_fixture(tmp_path, lines):
    package = tmp_path / "candidate/src/llm_wiki_cli"
    package.mkdir(parents=True, exist_ok=True)
    source = package / "owned.py"
    source.write_text("first = 1\nsecond = 2\n")
    output = tmp_path / ("data-" + "-".join(map(str, lines)))
    output.mkdir()
    data = CoverageData(basename=str(output / "coverage.data"))
    data.add_lines({"/owned/package/owned.py": set(lines)})
    data.write()
    sources = r.source_manifest(package)
    r.q.write_json(
        output / "coverage.json",
        {
            "schema_version": r.COVERAGE_SCHEMA,
            "source_roots": ["/owned/package"],
            "sources": sources,
            "lines": r.coverage_rows(
                output / "coverage.data", ["/owned/package"], sources
            ),
        },
    )
    return package, output


def test_real_coverage_merges_disjoint_lines_and_enforces_full_lane_threshold(
    tmp_path, monkeypatch
):
    package, first = coverage_fixture(tmp_path, [1])
    _, second = coverage_fixture(tmp_path, [2])
    monkeypatch.setattr(r, "package_root", lambda root: package)
    value = r.s.plan(NODES, context(), 2)
    output = tmp_path / "combined"
    output.mkdir()
    result = r.combine_coverage(value, [first, second], package.parents[1], output)
    assert result["percent"] == 100
    assert r.s.read(output / "coverage.json")["lines"] == {"owned.py": [1, 2]}
    partial = tmp_path / "partial"
    partial.mkdir()
    with pytest.raises(r.q.QualificationError, match="below 87%"):
        r.combine_coverage(value, [first], package.parents[1], partial)


def test_empty_module_entry_event_preserves_coverage_without_counting_a_statement(
    tmp_path, monkeypatch
):
    package, directory = coverage_fixture(tmp_path, [1, 2])
    (package / "__init__.py").write_bytes(b"")
    data = CoverageData(basename=str(directory / "coverage.data"))
    data.read()
    # Native Python 3.10 reported this exact event for services/__init__.py.
    data.add_lines({"/owned/package/__init__.py": {1}})
    data.write()
    sources = r.source_manifest(package)
    rows = r.coverage_rows(directory / "coverage.data", ["/owned/package"], sources)
    assert rows["__init__.py"] == [1] and sources["__init__.py"]["line_count"] == 0
    r.q.write_json(
        directory / "coverage.json",
        {
            "schema_version": r.COVERAGE_SCHEMA,
            "source_roots": ["/owned/package"],
            "sources": sources,
            "lines": rows,
        },
    )
    monkeypatch.setattr(r, "package_root", lambda root: package)
    output = tmp_path / "combined"
    output.mkdir()
    report = r.combine_coverage(
        r.s.plan(NODES, context(), 2), [directory], package.parents[1], output
    )
    assert report["percent"] == 100
    xml = ET.parse(output / "coverage-core-ubuntu-3.10.xml").getroot()
    assert xml.get("lines-valid") == "2" and xml.get("lines-covered") == "2"
    empty = next(
        row
        for row in xml.iter("class")
        if row.get("filename", "").endswith("/__init__.py")
    )
    assert empty.find("lines") is not None and len(list(empty.iter("line"))) == 0


@pytest.mark.parametrize("empty,line", [(True, 0), (True, 2), (False, 3)])
def test_empty_module_compatibility_does_not_accept_invalid_coverage_lines(
    tmp_path, empty, line
):
    package, directory = coverage_fixture(tmp_path, [1])
    if empty:
        (package / "owned.py").write_bytes(b"")
    data = CoverageData(basename=str(directory / "coverage.data"))
    data.erase()
    data.add_lines({"/owned/package/owned.py": {line}})
    data.write()
    with pytest.raises(
        r.q.QualificationError, match="invalid executed coverage line in owned.py"
    ):
        r.coverage_rows(
            directory / "coverage.data", ["/owned/package"], r.source_manifest(package)
        )


@pytest.mark.parametrize("mutation", ["source", "lines", "outside", "missing"])
def test_coverage_rejects_wrong_source_partial_data_and_outside_paths(
    tmp_path, monkeypatch, mutation
):
    package, directory = coverage_fixture(tmp_path, [1, 2])
    monkeypatch.setattr(r, "package_root", lambda root: package)
    record = r.s.read(directory / "coverage.json")
    if mutation == "source":
        record["sources"]["owned.py"]["sha256"] = "0" * 64
    elif mutation == "lines":
        record["lines"]["owned.py"] = [1]
    elif mutation == "outside":
        data = CoverageData(basename=str(directory / "coverage.data"))
        data.read()
        data.add_lines({str(tmp_path / "outside.py"): {1}})
        data.write()
    else:
        (directory / "coverage.data").unlink()
    r.q.write_json(directory / "coverage.json", record)
    output = tmp_path / "combined"
    output.mkdir()
    with pytest.raises(r.q.QualificationError):
        r.combine_coverage(
            r.s.plan(NODES, context(), 2), [directory], package.parents[1], output
        )


def test_coverage_combines_verified_installed_and_checkout_aliases(tmp_path):
    data = CoverageData(basename=str(tmp_path / "coverage.data"))
    data.add_lines(
        {
            "/owned/checkout/src/llm_wiki_cli/owned.py": {1},
            "/owned/venv/site-packages/llm_wiki_cli/owned.py": {2},
        }
    )
    data.write()
    roots = [
        "/owned/checkout/src/llm_wiki_cli",
        "/owned/venv/site-packages/llm_wiki_cli",
    ]
    sources = {"owned.py": {"sha256": "a" * 64, "line_count": 2}}
    assert r.coverage_rows(tmp_path / "coverage.data", roots, sources) == {
        "owned.py": [1, 2]
    }
    with pytest.raises(r.q.QualificationError, match="outside"):
        r.coverage_rows(tmp_path / "coverage.data", roots[:1], sources)


@pytest.mark.parametrize(
    "mutation", [None, "attempt", "identity", "harness", "lane", "pin-option"]
)
def test_downloaded_plan_and_pins_are_bound_before_package_install(tmp_path, mutation):
    current = context()
    plan = tmp_path / "plan.json"
    identity = tmp_path / "identity.json"
    pins = tmp_path / "constraints.txt"
    r.q.write_json(plan, r.s.plan(NODES, current, 2))
    r.q.write_json(identity, current["identity"])
    pins.write_text(r.constraints(current["environment"]))
    args = argparse.Namespace(
        plan=plan,
        identity=identity,
        constraints=pins,
        harness_sha256=current["harness_sha256"],
        run_id=current["run_id"],
        run_attempt=current["run_attempt"],
        lane="core-ubuntu-3.10",
    )
    if mutation == "attempt":
        args.run_attempt += 1
    elif mutation == "identity":
        changed = current["identity"]
        changed["source"]["sha"] = "f" * 40
        r.q.write_json(identity, changed)
    elif mutation == "harness":
        args.harness_sha256 = "0" * 64
    elif mutation == "lane":
        args.lane = "core-windows-3.13"
    elif mutation == "pin-option":
        pins.write_text(
            pins.read_text() + "--extra-index-url https://example.invalid\n"
        )
    if mutation is None:
        assert r.verify_plan_input(args) == 0
    else:
        with pytest.raises(r.q.QualificationError):
            r.verify_plan_input(args)


def test_freezer_and_preflight_bind_real_git_archives_and_detect_source_changes(
    tmp_path, monkeypatch
):
    root = tmp_path / "repository"
    root.mkdir()

    def git(*arguments):
        return subprocess.check_output(
            ["git", *arguments], cwd=root, stdin=subprocess.DEVNULL
        )

    git("init")
    git("config", "core.autocrlf", "false")
    (root / ".gitattributes").write_text("* -text\n")
    (root / "pyproject.toml").write_text('[project]\nversion = "1.0.0"\n')
    (root / "release").mkdir()
    for name in r.HARNESS_FILES:
        (root / "release" / name).write_bytes(
            Path(r.__file__).with_name(name).read_bytes()
        )
    git("add", ".")
    git(
        "-c",
        "user.name=Fixture",
        "-c",
        "user.email=fixture@example.invalid",
        "-c",
        f"core.hooksPath={tmp_path / 'absent-hooks'}",
        "commit",
        "--no-gpg-sign",
        "-m",
        "owned shadow source",
    )
    sha = git("rev-parse", "HEAD").decode().strip()
    # Shadow evidence remains useful after the current package version is tagged.
    git("tag", "v1.0.0")
    monkeypatch.delenv("GITHUB_OUTPUT", raising=False)
    output = tmp_path / "frozen"
    assert (
        r.freeze(
            argparse.Namespace(
                root=root, output=output, candidate_sha=sha, repository="owned/repo"
            )
        )
        == 0
    )
    identity = r.s.read(output / "identity.json")
    assert identity["source"]["sha"] == sha
    assert r.s.read(output / "freeze.json")["qualifying"] is False
    expected_env = context()["environment"]
    monkeypatch.setattr(r, "environment", lambda root, lane: expected_env)
    args = argparse.Namespace(
        root=root,
        identity=output / "identity.json",
        archive=output / "candidate-source.tar",
        harness=output / "qualification-harnesses.tar",
        harness_sha256=r.q.sha256_file(output / "qualification-harnesses.tar"),
        lane="core-ubuntu-3.10",
        run_id=123,
        run_attempt=1,
    )
    assert r.context(args)["identity"] == identity
    (root / "pyproject.toml").write_text('[project]\nversion = "2.0.0"\n')
    with pytest.raises(r.q.QualificationError, match="source content differs"):
        r.context(args)


@pytest.mark.parametrize(
    "mutation", ["editable", "wrong-root", "base-python", "platform"]
)
def test_executor_rejects_wrong_installation_before_running_tests(
    tmp_path, monkeypatch, mutation
):
    monkeypatch.setattr(
        r.platform, "system", lambda: "Linux" if mutation != "platform" else "Darwin"
    )
    monkeypatch.setattr(
        r.platform,
        "freedesktop_os_release",
        lambda: {"ID": "ubuntu", "VERSION_ID": "24.04"},
        raising=False,
    )
    monkeypatch.setattr(
        r.sys,
        "prefix",
        r.sys.base_prefix if mutation == "base-python" else str(tmp_path / "venv"),
    )
    if mutation in {"base-python", "platform"}:
        with pytest.raises(r.q.QualificationError):
            r.environment(tmp_path, "core-ubuntu-3.10")
        return

    class Distribution:
        metadata = {"Name": "agent-wiki-cli"}
        version = "1.0.0"

        def read_text(self, name):
            import json

            return json.dumps(
                {
                    "url": (tmp_path / "other").as_uri()
                    if mutation == "wrong-root"
                    else tmp_path.as_uri(),
                    "dir_info": {"editable": mutation == "editable"},
                }
            )

    monkeypatch.setattr(r.importlib.metadata, "distributions", lambda: [Distribution()])
    monkeypatch.setattr(
        r.importlib.metadata, "distribution", lambda name: Distribution()
    )
    with pytest.raises(r.q.QualificationError, match="source differs or is editable"):
        r.environment(tmp_path, "core-ubuntu-3.10")


@pytest.mark.parametrize("failing", [False, True])
def test_real_execution_protocol_retains_success_and_failure_evidence(
    tmp_path, monkeypatch, capsys, failing
):
    root = tmp_path / "candidate"
    (root / "tests").mkdir(parents=True)
    for name in ("one", "two"):
        (root / "tests" / f"test_{name}.py").write_text(
            f"def test_owned():\n    assert {not (failing and name == 'two')}\n"
        )
    identity = context("core-windows-3.13")["identity"]
    source = tmp_path / "source.tar"
    harness = tmp_path / "harness.tar"
    for archive, files in (
        (
            source,
            [(path, path.relative_to(root).as_posix()) for path in root.rglob("*.py")],
        ),
        (
            harness,
            [
                (Path(r.__file__).with_name(name), "release/" + name)
                for name in r.HARNESS_FILES
            ],
        ),
    ):
        with tarfile.open(
            archive,
            "w:",
            format=tarfile.PAX_FORMAT,
            pax_headers={"comment": identity["source"]["sha"]},
        ) as stream:
            for path, name in files:
                stream.add(path, arcname=name)
    identity["source"]["archive_sha256"] = r.q.sha256_file(source)
    identity_path = tmp_path / "identity.json"
    r.q.write_json(identity_path, identity)
    monkeypatch.setattr(
        r, "environment", lambda root, lane: context("core-windows-3.13")["environment"]
    )
    args = argparse.Namespace(
        root=root,
        archive=source,
        harness=harness,
        identity=identity_path,
        harness_sha256=r.q.sha256_file(harness),
        lane="core-windows-3.13",
        run_id=123,
        run_attempt=1,
        output=tmp_path / "reference",
        plan=None,
        index=None,
        shards=2,
    )
    if failing:
        with pytest.raises(
            r.q.QualificationError, match="core reference worker exited with code 1"
        ):
            r.execute(args)
        receipt = r.s.read(args.output / "execution.json")
        assert (
            receipt["complete"] is False
            and receipt["exit_code"] == 1
            and receipt["error"]
        )
        assert (args.output / "worker.log").is_file() and (
            args.output / "junit.xml"
        ).is_file()
        assert "see retained worker.log" in receipt["error"]
        assert "FAILED tests/test_two.py::test_owned" in capsys.readouterr().err
        return
    assert r.execute(args) == 0
    plan = r.s.read(args.plan)
    r.s.validate_execution(args.output, plan, None)
    directories = []
    for index in (0, 1):
        args.index, args.output = index, tmp_path / f"shard-{index}"
        assert r.execute(args) == 0
        directories.append(args.output)
    merged = r.s.merge_junit(plan, directories, tmp_path / "combined.xml")
    assert merged["outcomes"] == r.s.outcomes(
        r.s.junit(tmp_path / "reference/junit.xml")
    )
