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


@pytest.mark.parametrize("purpose", ["shadow", "qualification"])
def test_real_worker_recollects_all_nodes_and_runs_only_its_planned_files(
    tmp_path, purpose
):
    root = tmp_path / "candidate"
    tests = root / "tests"
    tests.mkdir(parents=True)
    for name in ("one", "two"):
        (tests / f"test_{name}.py").write_text("def test_owned():\n    assert True\n")
    nodes = [f"tests/test_{name}.py::test_owned" for name in ("one", "two")]
    value = r.s.plan(nodes, context("core-windows-3.13"), 2, purpose=purpose)
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
                "--purpose",
                purpose,
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
            "--purpose",
            purpose,
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
            "statements": r.statement_map(package, output / "coverage.data", package.parents[1]),
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


@pytest.mark.parametrize("entry,expected", [(0, []), (1, [1])])
def test_empty_module_entry_event_preserves_coverage_without_counting_a_statement(
    tmp_path, monkeypatch, entry, expected
):
    package, directory = coverage_fixture(tmp_path, [1, 2])
    (package / "__init__.py").write_bytes(b"")
    data = CoverageData(basename=str(directory / "coverage.data"))
    data.read()
    # Native Python 3.10 reports line 1; Python 3.11 reports virtual line 0.
    data.add_lines({"/owned/package/__init__.py": {entry}})
    data.write()
    raw_digest = r.q.sha256_file(directory / "coverage.data")
    sources = r.source_manifest(package)
    rows = r.coverage_rows(directory / "coverage.data", ["/owned/package"], sources)
    assert rows["__init__.py"] == expected and sources["__init__.py"]["line_count"] == 0
    assert r.q.sha256_file(directory / "coverage.data") == raw_digest
    r.q.write_json(
        directory / "coverage.json",
        {
            "schema_version": r.COVERAGE_SCHEMA,
            "source_roots": ["/owned/package"],
            "sources": sources,
            "statements": r.statement_map(package, directory / "coverage.data", package.parents[1]),
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
    xml = ET.parse(output / "coverage-core-ubuntu-3.11.xml").getroot()
    assert xml.get("lines-valid") == "2" and xml.get("lines-covered") == "2"
    empty = next(
        row
        for row in xml.iter("class")
        if Path(row.get("filename", "")).name == "__init__.py"
    )
    assert empty.find("lines") is not None and len(list(empty.iter("line"))) == 0


@pytest.mark.parametrize("empty,lines", [
    (False, [0]), (True, [2]), (False, [3]), (False, [0, 1]),
    (True, [0, 1]), (True, [0, 2]),
])
def test_empty_module_compatibility_does_not_accept_invalid_coverage_lines(
    tmp_path, empty, lines
):
    package, directory = coverage_fixture(tmp_path, [1])
    if empty:
        (package / "owned.py").write_bytes(b"")
    data = CoverageData(basename=str(directory / "coverage.data"))
    data.erase()
    data.add_lines({"/owned/package/owned.py": set(lines)})
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


@pytest.mark.parametrize("distinct_alias", [False, True])
def test_coverage_export_has_unique_verified_roots(tmp_path, monkeypatch, distinct_alias):
    checkout = tmp_path / "candidate"
    source = checkout / "src/llm_wiki_cli"
    source.mkdir(parents=True)
    (source / "owned.py").write_bytes(b"VALUE = 1\n")
    package = source
    if distinct_alias:
        package = tmp_path / "site-packages/llm_wiki_cli"
        package.mkdir(parents=True)
        (package / "owned.py").write_bytes(b"VALUE = 1\n")
    monkeypatch.setattr(r.importlib.metadata, "distribution", lambda name: SimpleNamespace(
        locate_file=lambda name: package,
    ))
    expected = [package.as_posix()]
    if distinct_alias:
        expected.append(source.as_posix())

    def verified_rows(data, roots, sources):
        assert roots == expected
        assert sources == r.source_manifest(source)
        return {"owned.py": [1]}

    data = CoverageData(basename=str(tmp_path / "coverage.data"))
    data.add_lines({str(package / "owned.py"): {1}})
    data.write()
    monkeypatch.setattr(r, "coverage_rows", verified_rows)
    r.export_coverage(checkout, tmp_path)
    assert r.s.read(tmp_path / "coverage.json")["source_roots"] == expected
    if distinct_alias:
        (package / "owned.py").write_bytes(b"CHANGED = 2\n")
        with pytest.raises(r.q.QualificationError, match="source bytes differ"):
            r.export_coverage(checkout, tmp_path)


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
        lane="core-ubuntu-3.11",
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
        lane="core-ubuntu-3.11",
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
            r.environment(tmp_path, "core-ubuntu-3.11")
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
        r.environment(tmp_path, "core-ubuntu-3.11")


@pytest.mark.parametrize("failing", [False, True])
@pytest.mark.parametrize("purpose", ["shadow", "qualification"])
def test_real_execution_protocol_retains_success_and_failure_evidence(
    tmp_path, monkeypatch, capsys, failing, purpose
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
        purpose=purpose,
    )
    if purpose == "qualification":
        args.output = tmp_path / "plan"
        assert r.prepare(args) == 0
        args.plan = args.output / "plan.json"
        plan = r.s.read(args.plan)
        r.s.validate_preparation(args.output, plan)
        assert (args.output / "started.jsonl").read_bytes() == b""
        shards = tmp_path / "shards"
        shards.mkdir()
        for index in (0, 1):
            args.index, args.output = index, shards / str(index)
            selected = plan["shards"][index]["nodes"]
            if failing and "tests/test_two.py::test_owned" in selected:
                with pytest.raises(
                    r.q.QualificationError, match="worker exited with code 1"
                ):
                    r.execute(args)
                assert r.s.read(args.output / "execution.json")["complete"] is False
            else:
                assert r.execute(args) == 0
                r.s.validate_execution(args.output, plan, index, purpose=purpose)
        # The real aggregation must retain a partial receipt and block both a
        # failed worker and a complete but undersized logical lane.
        args.output = tmp_path / "aggregate"
        args.preparation, args.shards_root = tmp_path / "plan", shards
        with pytest.raises(r.q.QualificationError):
            r.aggregate_qualification(args)
        assert r.s.read(args.output / "aggregation.json")["complete"] is False
        return
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


def test_pure_promotion_reader_replays_raw_coverage_union_without_third_party_reader(tmp_path, monkeypatch):
    from release import core_coverage
    package, first = coverage_fixture(tmp_path, [1])
    _, second = coverage_fixture(tmp_path, [2])
    monkeypatch.setattr(r, "package_root", lambda root: package)
    output = tmp_path / "combined"
    output.mkdir()
    r.combine_coverage(r.s.plan(NODES, context(), 2), [first, second], package.parents[1], output)
    core_coverage.validate_combination(output, [first, second], package, r.s.read)
    data = CoverageData(basename=str(second / "coverage.data"))
    data.erase()
    data.add_lines({"/owned/package/owned.py": {1}})
    data.write()
    with pytest.raises(ValueError, match="receipt differs"):
        core_coverage.validate_combination(output, [first, second], package, r.s.read)


def test_unexecuted_source_files_cannot_disappear_from_coverage_denominator(tmp_path, monkeypatch):
    package, first = coverage_fixture(tmp_path, [1, 2])
    (package / "unexecuted.py").write_text("third = 3\nfourth = 4\n")
    record = r.s.read(first / "coverage.json")
    record["sources"] = r.source_manifest(package)
    record["statements"] = r.statement_map(package, first / "coverage.data", package.parents[1])
    r.q.write_json(first / "coverage.json", record)
    monkeypatch.setattr(r, "package_root", lambda root: package)
    output = tmp_path / "combined"
    output.mkdir()
    with pytest.raises(r.q.QualificationError, match="below 87%"):
        r.combine_coverage(r.s.plan(NODES, context(), 2), [first], package.parents[1], output)


def test_qualifying_ubuntu_command_replays_complete_inventory_and_raw_coverage(tmp_path, monkeypatch):
    from tests.test_core_shards import execution
    package, seed = coverage_fixture(tmp_path, [1])
    root = package.parents[1]
    (root / "release").mkdir()
    allowlist = root / "release/skip-allowlist.json"
    r.q.write_json(allowlist, {"schema_version": r.q.ALLOWLIST_SCHEMA, "entries": []})
    current = context("core-ubuntu-3.11")
    nodes = [f"tests/test_group_{index % 2}.py::test_owned_{index}" for index in range(5322)]
    plan = r.s.plan(nodes, current, 2, purpose="qualification")
    preparation = tmp_path / "plan"
    preparation.mkdir()
    for name, value in (("plan.json", plan), ("collected.json", plan["inventory"])):
        r.q.write_json(preparation / name, value)
    (preparation / "constraints.txt").write_text(r.constraints(current["environment"]))
    (preparation / "collection.log").write_text("owned collection")
    (preparation / "started.jsonl").write_text("")
    r.q.write_json(preparation / "preparation.json", {
        "schema_version": r.s.PREPARATION_SCHEMA, "purpose": "qualification",
        "qualifying": True, "complete": True, "context": current,
        "plan_sha256": r.s.digest(plan), "exit_code": 0, "seconds": 1.0, "error": None,
        "files": {path.name: r.q.sha256_file(path) for path in preparation.iterdir()},
    })
    shards = tmp_path / "workers"
    shards.mkdir()
    sources = r.source_manifest(package)
    for index in range(2):
        directory = execution(shards / str(index), plan, index)
        data = CoverageData(basename=str(directory / "coverage.data"))
        data.add_lines({"/owned/package/owned.py": {index + 1}})
        data.write()
        r.q.write_json(directory / "coverage.json", {
            "schema_version": r.COVERAGE_SCHEMA, "sources": sources,
            "statements": r.statement_map(package, directory / "coverage.data", root),
            "source_roots": ["/owned/package"], "lines": {"owned.py": [index + 1]},
        })
        receipt = r.s.read(directory / "execution.json")
        receipt["files"].update({name: r.q.sha256_file(directory / name) for name in ("coverage.data", "coverage.json")})
        r.q.write_json(directory / "execution.json", receipt)
    monkeypatch.setattr(r, "context", lambda args: current)
    monkeypatch.setattr(r, "package_root", lambda source: package)
    output = tmp_path / "aggregate"
    args = argparse.Namespace(root=root, output=output, preparation=preparation, shards_root=shards)
    assert r.aggregate_qualification(args) == 0
    assert len(r.s.junit(output / "core-ubuntu-3.11.xml")) == 5322
    r.s.validate_aggregation(output, preparation, [shards / "0", shards / "1"],
        current["identity"], current["harness_sha256"], current["run_id"], current["run_attempt"], allowlist, source_root=root)
    recorded = r.s.read(output / "coverage.json")
    recorded["lines"]["owned.py"] = [1]
    r.q.write_json(output / "coverage.json", recorded)
    aggregation = r.s.read(output / "aggregation.json")
    aggregation["files"]["coverage.json"] = r.q.sha256_file(output / "coverage.json")
    r.q.write_json(output / "aggregation.json", aggregation)
    with pytest.raises(ValueError, match="complete raw shard union"):
        r.s.validate_aggregation(output, preparation, [shards / "0", shards / "1"],
            current["identity"], current["harness_sha256"], current["run_id"], current["run_attempt"], allowlist, source_root=root)


def test_real_coverage_storage_is_admitted_before_qualifying_collection():
    r.probe_coverage_transport()


def test_pure_coverage_reader_rejects_oversized_bitset_before_expansion(tmp_path):
    import sqlite3
    from release import core_coverage
    package, directory = coverage_fixture(tmp_path, [1])
    path = directory / "coverage.data"
    with sqlite3.connect(path) as connection:
        connection.execute("UPDATE line_bits SET numbits = ?", (b"\xff" * 1024,))
    with pytest.raises(ValueError, match="bitset exceeds frozen source"):
        core_coverage.raw_lines(path, ["/owned/package"], r.source_manifest(package))


def test_coverage_statement_map_rejects_rehashed_omitted_uncovered_xml_line(tmp_path, monkeypatch):
    from release import core_coverage
    package, directory = coverage_fixture(tmp_path, [1, 2])
    (package / "owned.py").write_text("\n".join(f"value_{index} = {index}" for index in range(10)) + "\n")
    path = directory / "coverage.data"
    data = CoverageData(basename=str(path))
    data.erase()
    data.add_lines({"/owned/package/owned.py": set(range(1, 10))})
    data.write()
    r.q.write_json(directory / "coverage.json", {
        "schema_version": r.COVERAGE_SCHEMA, "source_roots": ["/owned/package"],
        "sources": r.source_manifest(package),
        "statements": r.statement_map(package, path, package.parents[1]),
        "lines": {"owned.py": list(range(1, 10))},
    })
    monkeypatch.setattr(r, "package_root", lambda root: package)
    output = tmp_path / "combined"
    output.mkdir()
    r.combine_coverage(r.s.plan(NODES, context(), 2), [directory], package.parents[1], output)
    core_coverage.validate_combination(output, [directory], package, r.s.read)
    xml_path = output / "coverage-core-ubuntu-3.11.xml"
    tree = ET.parse(xml_path)
    for node in tree.getroot().iter("class"):
        lines = node.find("lines")
        if lines is not None:
            for line in list(lines):
                if line.attrib["number"] == "10":
                    lines.remove(line)
    tree.getroot().set("lines-valid", "9")
    tree.getroot().set("lines-covered", "9")
    tree.getroot().set("line-rate", "1")
    tree.write(xml_path)
    with pytest.raises(ValueError, match="omitted executable statements"):
        core_coverage.validate_combination(output, [directory], package, r.s.read)


def test_nested_nonpackage_provider_file_keeps_its_coverage_denominator(tmp_path, monkeypatch):
    package, directory = coverage_fixture(tmp_path, [1, 2])
    nested = package / "examples/plugin/data.py"
    nested.parent.mkdir(parents=True)
    nested.write_text("never_executed = 1\nnever_executed_again = 2\n")
    record = r.s.read(directory / "coverage.json")
    record["sources"] = r.source_manifest(package)
    record["statements"] = r.statement_map(package, directory / "coverage.data", package.parents[1])
    r.q.write_json(directory / "coverage.json", record)
    monkeypatch.setattr(r, "package_root", lambda root: package)
    output = tmp_path / "combined"
    output.mkdir()
    with pytest.raises(r.q.QualificationError, match="below 87%"):
        r.combine_coverage(r.s.plan(NODES, context(), 2), [directory], package.parents[1], output)


@pytest.mark.parametrize("drift", [False, True])
def test_final_native_context_revalidation_refuses_environment_drift_before_receipt(tmp_path, monkeypatch, drift):
    from copy import deepcopy
    before = context("core-windows-3.13")
    reference = tmp_path / "context.json"
    r.q.write_json(reference, before)
    after = deepcopy(before)
    if drift:
        after["environment"]["packages"]["injected-build-tool"] = "9.9"
    monkeypatch.setattr(r, "context", lambda args: after)
    output = tmp_path / "context-final.json"
    args = argparse.Namespace(output=output, reference=reference)
    if drift:
        with pytest.raises(r.q.QualificationError, match="environment.packages"):
            r.native_context(args)
        assert not output.exists()
    else:
        assert r.native_context(args) == 0 and r.s.read(output) == before
