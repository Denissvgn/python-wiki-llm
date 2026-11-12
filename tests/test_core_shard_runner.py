"""Native-boundary isolation, actual workers, and coverage merge controls."""

from contextlib import closing
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


linux_coverage_producer = pytest.mark.skipif(
    sys.platform == "win32",
    reason="canonical coverage producer requires POSIX filesystem paths",
)


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
    monkeypatch.setenv("COVERAGE_FORCE_CONFIG", str(tmp_path / "foreign.coveragerc"))
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
    assert not {"PYTEST_ADDOPTS", "PYTEST_PLUGINS", "COVERAGE_FORCE_CONFIG", "LLM_WIKI_CACHE_DIR"}.intersection(
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


def canonical_linux_artifact(directory):
    """Represent a Linux producer artifact independently of this test host."""
    record = r.s.read(directory / "coverage.json")
    data = CoverageData(basename=str(directory / "coverage.data"))
    data.read()
    # Verify the native merger's exact file inventory before constructing the
    # POSIX transport fixture. Never teach the promotion reader Windows paths.
    roots = record["source_roots"]
    assert len(roots) == 1
    expected = {str(Path(roots[0]) / name) for name in record["lines"]}
    assert set(data.measured_files()) == expected
    for name in expected:
        observed = data.lines(name)
        assert observed is not None
        assert sorted(observed) == record["lines"][Path(name).relative_to(Path(roots[0])).as_posix()]
    data.erase()
    data = CoverageData(basename=str(directory / "coverage.data"))
    data.add_lines({"/owned/package/" + name: lines for name, lines in record["lines"].items()})
    data.write()
    record["source_roots"] = ["/owned/package"]
    r.q.write_json(directory / "coverage.json", record)


@pytest.fixture(params=["continuation-events", "native-tracer"])
def multiline_coverage_artifact(tmp_path, monkeypatch, request):
    from coverage import Coverage

    package = tmp_path / "candidate/src/llm_wiki_cli"
    package.mkdir(parents=True)
    source = package / "owned.py"
    source.write_bytes((
        "\n".join(f"value_{n} = {n}" for n in range(8))
        + "\nflag = True\nif (\n    flag\n):\n    covered = 1\nelse:\n    missed = 2\n"
    ).encode())
    # Python 3.11 traces the condition's continuation line, while the XML
    # reporter attributes that event to the logical statement's first line.
    events = set(range(1, 10)) | {11, 13}
    if request.param == "native-tracer":
        measured = Coverage(data_file=str(tmp_path / "native.data"),
                            source=[str(package)], branch=False, config_file=False)
        with measured.collect():
            exec(compile(source.read_bytes(), str(source), "exec"), {})
        measured.save()
        data = measured.get_data()
        files = list(data.measured_files())
        assert len(files) == 1 and Path(files[0]).resolve() == source.resolve()
        observed = data.lines(files[0])
        assert observed is not None
        events = set(observed)
    directory = tmp_path / "input"
    directory.mkdir()
    data = CoverageData(basename=str(directory / "coverage.data"))
    data.add_lines({"/owned/package/owned.py": events})
    data.write()
    sources = r.source_manifest(package)
    r.q.write_json(directory / "coverage.json", {
        "schema_version": r.COVERAGE_SCHEMA, "source_roots": ["/owned/package"],
        "sources": sources,
        "statements": r.statement_map(package, directory / "coverage.data", package.parents[1]),
        "lines": {"owned.py": sorted(events)},
    })
    monkeypatch.setattr(r, "package_root", lambda root: package)
    output = tmp_path / "combined"
    output.mkdir()
    result = r.combine_coverage(r.s.plan(NODES, context(), 2), [directory], package.parents[1], output)
    assert result["percent"] == pytest.approx(100 * 11 / 12)
    canonical_linux_artifact(output)
    assert r.s.read(output / "coverage.json")["lines"] == {"owned.py": sorted(events)}
    return package, directory, output


def test_pure_coverage_reader_preserves_raw_union_for_multiline_statement_hits(multiline_coverage_artifact):
    from release import core_coverage

    package, directory, output = multiline_coverage_artifact
    before = {path: r.q.sha256_file(path) for path in (
        directory / "coverage.data", directory / "coverage.json",
        output / "coverage.data", output / "coverage.json",
    )}
    core_coverage.validate_combination(output, [directory], package, r.s.read)
    assert {path: r.q.sha256_file(path) for path in before} == before


@pytest.mark.parametrize("number,hits", [(10, 0), (15, 1)])
def test_multiline_coverage_reader_rejects_rehashed_xml_hits(multiline_coverage_artifact, number, hits):
    from release import core_coverage

    package, directory, output = multiline_coverage_artifact
    path = output / "coverage-core-ubuntu-3.11.xml"
    tree = ET.parse(path)
    lines = list(tree.getroot().iter("line"))
    changed = next(line for line in lines if int(line.attrib["number"]) == number)
    assert int(changed.attrib["hits"]) != hits
    changed.set("hits", str(hits))
    covered = sum(int(line.attrib["hits"]) > 0 for line in lines)
    tree.getroot().set("lines-covered", str(covered))
    tree.getroot().set("line-rate", str(covered / len(lines)))
    tree.write(path)
    with pytest.raises(ValueError, match="coverage XML hits differ from raw union"):
        core_coverage.validate_combination(output, [directory], package, r.s.read)


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


@pytest.fixture
def frozen_input_tree(tmp_path):
    import io

    root = tmp_path / "candidate"
    root.mkdir()
    files = {
        ".gitignore": b"reports/\n.venv/\nbuild/\n",
        "pyproject.toml": b'[project]\nname="agent-wiki-cli"\nversion="1.0.0"\n',
        "pytest.ini": b"[pytest]\n",
        "src/llm_wiki_cli/__init__.py": b"VALUE = 1\n",
        "tests/test_owned.py": b"def test_owned(): pass\n",
        "release/helper.py": b"VALUE = 1\n",
        "docs/public.md": b"Public documentation\n",
        "examples/owned.py": b"VALUE = 1\n",
        "src/llm_wiki_cli/extractors/rust_scripts/.gitignore": b"target/\n",
        "src/llm_wiki_cli/extractors/rust_scripts/Cargo.toml": b"frozen Rust input\n",
        "src/llm_wiki_cli/extractors/ts_scripts/.gitignore": b"node_modules/\n",
        "src/llm_wiki_cli/extractors/ts_scripts/extract.js": b"frozen JavaScript input\n",
    }
    archive = tmp_path / "source.tar"
    with tarfile.open(archive, "w", format=tarfile.PAX_FORMAT,
                      pax_headers={"comment": "1" * 40}) as stream:
        for name, data in files.items():
            path = root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
            member = tarfile.TarInfo(name)
            member.size = len(data)
            stream.addfile(member, io.BytesIO(data))
    identity = {"source": {"sha": "1" * 40, "archive_sha256": r.q.sha256_file(archive)}}
    return root, archive, identity


@pytest.mark.parametrize("extra", [
    "conftest.py", ".pytest.toml", "tokenizers/__init__.py", "namespace_shadow/module.py",
    "tests/conftest.py", "tests/fixtures/rogue.json", "release/unfrozen.py",
    "src/new_module.py", "src/llm_wiki_cli/extra.json",
    "src/agent_wiki_cli.egg-info/rogue.py", "tests/__pycache__/rogue.py",
])
def test_unfrozen_execution_inputs_are_rejected_before_collection(
    frozen_input_tree, tmp_path, monkeypatch, extra,
):
    root, archive, identity = frozen_input_tree
    path = root / extra
    path.parent.mkdir(parents=True, exist_ok=True)
    marker = tmp_path / "unfrozen-executed"
    path.write_text(f"from pathlib import Path\nPath({str(marker)!r}).write_text('unsafe')\n")

    def verified_context(args):
        r.verify_source(args.root, archive, identity)
        return context()

    monkeypatch.setattr(r, "context", verified_context)
    monkeypatch.setattr(r, "invoke", lambda *a: pytest.fail("Unfrozen input reached collection"))
    args = argparse.Namespace(root=root, output=tmp_path / "evidence", shards=2, archive=archive)
    with pytest.raises(r.q.QualificationError, match="unfrozen source"):
        r.prepare(args)
    assert not marker.exists()
    assert r.s.read(args.output / "preparation.json")["complete"] is False
    assert not (args.output / "collected.json").exists()


def test_source_additions_are_rechecked_after_collection(frozen_input_tree, tmp_path, monkeypatch):
    root, archive, identity = frozen_input_tree

    current = context("core-windows-3.13")
    current["identity"]["source"].update(identity["source"])

    def verified_context(args):
        r.verify_source(args.root, archive, identity)
        return current

    def collect(*args):
        (root / "conftest.py").write_text("UNFROZEN = True\n")
        return r.s.plan(NODES, current, 2, purpose="qualification")

    monkeypatch.setattr(r, "context", verified_context)
    monkeypatch.setattr(r, "collect_plan", collect)
    args = argparse.Namespace(root=root, output=tmp_path / "evidence", shards=2, archive=archive)
    with pytest.raises(r.q.QualificationError, match="unfrozen source input: conftest.py"):
        r.prepare(args)
    assert r.s.read(args.output / "preparation.json")["complete"] is False


def test_frozen_source_parent_cannot_redirect_to_matching_bytes(frozen_input_tree, tmp_path):
    root, archive, identity = frozen_input_tree
    real = tmp_path / "retained-src"
    (root / "src").rename(real)
    (root / "src").symlink_to(real, target_is_directory=True)
    with pytest.raises(r.q.QualificationError, match="redirected source parent"):
        r.verify_source(root, archive, identity)
    assert (real / "llm_wiki_cli/__init__.py").read_bytes() == b"VALUE = 1\n"


def test_source_guards_keep_ordinary_checkout_scaffolding_opaque(frozen_input_tree, monkeypatch):
    root, archive, identity = frozen_input_tree
    residue = {
        ".git/config": b"git metadata",
        ".venv/lib/python/site-packages/provider/__init__.py": b"installed dependency",
        "build/lib/llm_wiki_cli/__init__.py": b"build output",
        "reports/__init__.py": b"internal tooling",
        "docs/plans/internal.py": b"internal planning tool",
        "examples/project/.venv/foreign.py": b"sample environment",
        "src/.DS_Store": b"Finder metadata",
        "src/llm_wiki_cli/extractors/rust_scripts/target/debug/deps/cache.rlib": b"native build output",
        "src/llm_wiki_cli/extractors/ts_scripts/node_modules/dependency/index.js": b"native dependency cache",
        "src/agent_wiki_cli.egg-info/PKG-INFO": b"built metadata",
        "src/llm_wiki_cli/__pycache__/__init__.cpython-311.pyc": b"generated bytecode",
    }
    for name, data in residue.items():
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
    (root / "tests/fixtures/empty/nested").mkdir(parents=True)
    actual_walk = r.os.walk
    actual_scandir = r.os.scandir
    walks = []
    opaque = [root / "src/llm_wiki_cli/extractors" / path
              for path in ("rust_scripts/target", "ts_scripts/node_modules")]

    def bounded_scandir(path):
        assert not any(Path(path) == cache or cache in Path(path).parents for cache in opaque)
        return actual_scandir(path)

    def bounded_walk(top, **kwargs):
        walks.append(top.relative_to(root).as_posix())
        return actual_walk(top, **kwargs)

    monkeypatch.setattr(r.os, "walk", bounded_walk)
    monkeypatch.setattr(r.os, "scandir", bounded_scandir)
    r.verify_source(root, archive, identity)
    assert set(walks) == {"src", "tests", "release"}
    assert all((root / name).read_bytes() == data for name, data in residue.items())


@pytest.fixture
def shadow_checkout(tmp_path):
    root = tmp_path / "repository"
    root.mkdir()

    def git(*arguments):
        return subprocess.check_output(
            ["git", "-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid",
             "-c", "commit.gpgsign=false", "-c", f"core.hooksPath={tmp_path / 'absent-hooks'}",
             *arguments], cwd=root, stdin=subprocess.DEVNULL
        )

    git("init")
    git("config", "core.autocrlf", "false")
    (root / ".gitattributes").write_text("* -text\n")
    (root / "pyproject.toml").write_text('[project]\nversion = "1.0.0"\n')
    (root / "owned.py").write_text('VALUE = "original"\n')
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
    return root, git, sha


def test_freezer_and_preflight_bind_real_git_archives_and_detect_source_changes(
    shadow_checkout, tmp_path, monkeypatch
):
    root, git, sha = shadow_checkout
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


@pytest.mark.parametrize("flag", ["--assume-unchanged", "--skip-worktree"])
def test_shadow_freezer_rejects_hidden_source_bytes_before_creating_outputs(
    shadow_checkout, tmp_path, monkeypatch, flag,
):
    root, git, sha = shadow_checkout
    git("update-index", flag, "owned.py")
    (root / "owned.py").write_text('VALUE = "hidden modification"\n')
    assert not git("status", "--porcelain").strip()
    monkeypatch.delenv("GITHUB_OUTPUT", raising=False)
    output = tmp_path / "frozen"
    with pytest.raises(r.q.QualificationError, match="Canonical tracked source bytes differ"):
        r.freeze(argparse.Namespace(root=root, output=output, candidate_sha=sha, repository="owned/repo"))
    assert not output.exists()


@pytest.mark.parametrize("replace_worktree", [False, True])
def test_shadow_freezer_uses_original_objects_without_deleting_replacement_refs(
    shadow_checkout, tmp_path, monkeypatch, replace_worktree,
):
    root, git, sha = shadow_checkout
    tree = git("--no-replace-objects", "rev-parse", sha + "^{tree}").decode().strip()
    epoch = int(git("--no-replace-objects", "show", "-s", "--format=%ct", sha))
    original_bytes = (root / "owned.py").read_bytes()
    (root / "owned.py").write_text('VALUE = "replacement"\n')
    git("add", "owned.py")
    git("commit", "-qm", "Replacement source")
    replacement = git("rev-parse", "HEAD").decode().strip()
    git("reset", "--hard", sha)
    git("replace", sha, replacement)
    if replace_worktree:
        git("read-tree", "--reset", "-u", "HEAD")
        assert not git("status", "--porcelain").strip()
    monkeypatch.delenv("GITHUB_OUTPUT", raising=False)
    output = tmp_path / "frozen"
    args = argparse.Namespace(root=root, output=output, candidate_sha=sha, repository="owned/repo")
    if replace_worktree:
        with pytest.raises(r.q.QualificationError, match="shadow source must be clean"):
            r.freeze(args)
        assert not output.exists()
    else:
        assert r.freeze(args) == 0
        identity = r.s.read(output / "identity.json")
        assert identity["source"]["sha"] == sha
        assert identity["source"]["tree"] == tree
        assert identity["source"]["commit_epoch"] == epoch
        with tarfile.open(output / "candidate-source.tar", "r:") as archive:
            stream = archive.extractfile("owned.py")
            assert stream is not None and stream.read() == original_bytes
    assert git("replace", "--list").decode().strip() == sha


def test_shadow_freezer_rechecks_source_after_archive_creation(
    shadow_checkout, tmp_path, monkeypatch,
):
    root, git, sha = shadow_checkout
    (root / "owned.py").write_text('VALUE = "next source"\n')
    git("add", "owned.py")
    git("commit", "-qm", "Next source")
    changed = git("rev-parse", "HEAD").decode().strip()
    git("reset", "--hard", sha)
    original = subprocess.check_output
    archives = []

    def switch_after_first_archive(command, **kwargs):
        result = original(command, **kwargs)
        if "archive" in command:
            archives.append(command)
            if len(archives) == 1:
                original(["git", "reset", "--hard", changed], cwd=root, stdin=subprocess.DEVNULL)
        return result

    monkeypatch.setattr(r.subprocess, "check_output", switch_after_first_archive)
    monkeypatch.delenv("GITHUB_OUTPUT", raising=False)
    output = tmp_path / "frozen"
    with pytest.raises(r.q.QualificationError, match="shadow checkout differs"):
        r.freeze(argparse.Namespace(root=root, output=output, candidate_sha=sha, repository="owned/repo"))
    assert (output / "candidate-source.tar").is_file()
    assert not (output / "freeze.json").exists()


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


@pytest.mark.parametrize("lane", ["core-ubuntu-3.11", "core-windows-3.13"])
@pytest.mark.parametrize("mutation", [
    None, "python", "packaged-data", "extra-python", "extra-data", "missing", "symlink-file", "symlink-parent",
])
def test_complete_provider_namespace_is_checked_before_collection(
    tmp_path, monkeypatch, lane, mutation,
):
    root = tmp_path / "candidate"
    package = root / "src/llm_wiki_cli"
    package.mkdir(parents=True)
    marker = tmp_path / "candidate-executed"
    (root / "pyproject.toml").write_text(
        '[project]\nversion="1.0.0"\n[tool.setuptools.package-data]\nllm_wiki_cli=["*.txt"]\n'
    )
    (package / "__init__.py").write_text(
        f"from pathlib import Path\nPath({str(marker)!r}).write_text('unsafe')\n"
    )
    (package / "owned.txt").write_bytes(b"frozen payload\n")
    prefix = tmp_path / "venv"
    installed = prefix / "lib/site-packages/llm_wiki_cli"
    installed.mkdir(parents=True)
    for path in package.iterdir():
        (installed / path.name).write_bytes(path.read_bytes())
    if mutation == "python":
        (installed / "__init__.py").write_text("STALE = True\n")
    elif mutation == "packaged-data":
        (installed / "owned.txt").write_text("STALE\n")
    elif mutation == "extra-python":
        (installed / "extra.py").write_text("EXTRA = True\n")
    elif mutation == "extra-data":
        (installed / "extra.txt").write_text("EXTRA\n")
    elif mutation == "missing":
        (installed / "owned.txt").unlink()
    elif mutation == "symlink-file":
        (installed / "owned.txt").unlink()
        (installed / "owned.txt").symlink_to(package / "owned.txt")
    elif mutation == "symlink-parent":
        original = installed.parent
        original.rename(original.with_name("retained-site-packages"))
        original.symlink_to(original.with_name("retained-site-packages"), target_is_directory=True)

    class Distribution:
        version = "1.0.0"

        def __init__(self, name):
            self.metadata = {"Name": name}

        def read_text(self, name):
            return r.json.dumps({"url": root.resolve().as_uri(), "dir_info": {}})

        def locate_file(self, name):
            return installed.parent / name

    distributions = [Distribution(name) for name in (
        "agent-wiki-cli", "pytest", "pytest-cov", "coverage", "tokenizers",
    )]
    monkeypatch.setattr(r.importlib.metadata, "distribution", lambda name: distributions[0])
    monkeypatch.setattr(r.importlib.metadata, "distributions", lambda: distributions)
    monkeypatch.setattr(r.sys, "prefix", str(prefix))
    monkeypatch.setattr(r.platform, "system", lambda: "Windows" if "windows" in lane else "Linux")
    monkeypatch.setattr(r.platform, "release", lambda: "2025")
    monkeypatch.setattr(r.platform, "python_version", lambda: r.s.PROFILES[lane]["python"] + ".21")
    monkeypatch.setattr(r.platform, "freedesktop_os_release",
                        lambda: {"ID": "ubuntu", "VERSION_ID": "24.04"}, raising=False)

    def observed_context(args):
        value = context(lane)
        value["environment"] = r.environment(root, lane)
        return value

    events = []

    def no_collection(*args, **kwargs):
        events.append("collection")
        raise RuntimeError("stop after verified namespace")

    monkeypatch.setattr(r, "context", observed_context)
    # Namespace admission is independent of the Ubuntu coverage producer probe.
    monkeypatch.setattr(r, "probe_coverage_transport", lambda root: None)
    monkeypatch.setattr(r, "invoke", no_collection)
    args = argparse.Namespace(root=root, output=tmp_path / "evidence", shards=2, lane=lane, archive=tmp_path / "unused.tar")
    with pytest.raises((ValueError, RuntimeError), match=(
        "stop after verified namespace" if mutation is None else "namespace differs|Redirected canary path"
    )):
        r.prepare(args)
    assert events == (["collection"] if mutation is None else [])
    assert not marker.exists()
    assert r.s.read(args.output / "preparation.json")["complete"] is False


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
    canonical_linux_artifact(output)
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
    native_combine = r.combine_coverage

    def linux_combine(*args):
        result = native_combine(*args)
        canonical_linux_artifact(args[-1])
        return result

    monkeypatch.setattr(r, "combine_coverage", linux_combine)
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


@linux_coverage_producer
def test_real_coverage_storage_is_admitted_before_qualifying_collection():
    r.probe_coverage_transport()


@pytest.mark.parametrize("setting,reason", [
    ("branch = True", "branch policy"),
    ("relative_files = True", "relative path policy"),
    ("dynamic_context = test_function", "context policy"),
    ("context = inherited-context", "context policy"),
    ("plugins = unowned_plugin", "coverage plugins"),
    ("source_pkgs = unowned_package", "additional source packages"),
])
def test_actual_candidate_coverage_configuration_is_rejected_before_collection(
    tmp_path, monkeypatch, setting, reason,
):
    root = tmp_path / "candidate"
    root.mkdir()
    config = root / ".coveragerc"
    original = "[run]\n" + setting + "\n"
    config.write_text(original)
    (root / "pytest.ini").write_text("[pytest]\n")
    current = context()
    events = []

    def verified_source(args):
        events.append("source-and-runtime-verified")
        return current

    def no_collection(*args, **kwargs):
        raise AssertionError("Unsupported instrumentation reached expensive work")

    monkeypatch.setattr(r, "context", verified_source)
    monkeypatch.setattr(r, "invoke", no_collection)
    previous = Path.cwd()
    args = argparse.Namespace(root=root, output=tmp_path / "evidence", shards=2)
    with pytest.raises(r.q.QualificationError, match=reason):
        r.prepare(args)
    assert events == ["source-and-runtime-verified"] and Path.cwd() == previous
    assert config.read_text() == original
    assert not (args.output / "collected.json").exists()
    assert r.s.read(args.output / "preparation.json")["complete"] is False


@pytest.mark.parametrize("option", [
    "--cov-branch", "--cov-context=test", "--cov-config=/unowned/config", "--no-cov", "-p no:pytest_cov",
])
def test_candidate_pytest_instrumentation_overrides_are_rejected_without_execution(tmp_path, option):
    (tmp_path / "pytest.ini").write_text("[pytest]\naddopts = " + option + "\n")
    with pytest.raises(r.q.QualificationError, match="override frozen coverage flags"):
        r.probe_coverage_transport(tmp_path)


@linux_coverage_producer
def test_coverage_admission_does_not_execute_candidate_conftest_or_plugin(tmp_path):
    marker = tmp_path / "executed"
    source = f"from pathlib import Path\nPath({str(marker)!r}).write_text('unsafe')\nraise RuntimeError('must not import')\n"
    (tmp_path / "conftest.py").write_text(source)
    (tmp_path / "sentinel_plugin.py").write_text(source)
    (tmp_path / "pytest.ini").write_text(
        "[pytest]\nrequired_plugins = sentinel-plugin\naddopts = -p sentinel_plugin\n"
    )
    (tmp_path / ".coveragerc").write_text("[run]\nbranch = False\n")
    package = tmp_path / "src/llm_wiki_cli"
    package.mkdir(parents=True)
    (package / "__init__.py").write_text(source)
    before = {p.relative_to(tmp_path).as_posix(): p.read_bytes()
              for p in tmp_path.rglob("*") if p.is_file()}
    r.probe_coverage_transport(tmp_path)
    assert not marker.exists()
    assert before == {p.relative_to(tmp_path).as_posix(): p.read_bytes()
                      for p in tmp_path.rglob("*") if p.is_file()}


@pytest.mark.parametrize("setting", [
    "omit = */hidden.py", "include = */owned.py", "skip_empty = True", "contexts = ^unowned$",
])
def test_coverage_report_inventory_mismatch_is_rejected_before_collection(
    tmp_path, monkeypatch, setting,
):
    root = tmp_path / "candidate"
    package = root / "src/llm_wiki_cli"
    package.mkdir(parents=True)
    (package / "__init__.py").write_bytes(b"")
    for name in ("owned.py", "hidden.py"):
        (package / name).write_text("VALUE = 1\n")
    (root / "pytest.ini").write_text("[pytest]\n")
    config = root / ".coveragerc"
    original = "[report]\n" + setting + "\n"
    config.write_text(original)
    monkeypatch.setattr(r, "context", lambda args: context())

    def no_collection(*args, **kwargs):
        raise AssertionError("Invalid report policy reached collection")

    monkeypatch.setattr(r, "invoke", no_collection)
    args = argparse.Namespace(root=root, output=tmp_path / "evidence", shards=2)
    with pytest.raises(r.q.QualificationError, match="report cannot preserve complete source inventory"):
        r.prepare(args)
    assert config.read_text() == original
    assert r.s.read(args.output / "preparation.json")["complete"] is False
    assert not (args.output / "collected.json").exists()


@pytest.mark.parametrize("setting", [
    "exclude_lines = ^SECOND", "skip_covered = True", "include = */llm_wiki_cli/*",
    "omit = */unowned.py", "contexts = ^$",
])
@linux_coverage_producer
def test_compatible_coverage_report_settings_remain_supported(tmp_path, setting):
    package = tmp_path / "src/llm_wiki_cli"
    package.mkdir(parents=True)
    (package / "__init__.py").write_bytes(b"")
    (package / "owned.py").write_text("FIRST = 1\nSECOND = 2\n")
    (tmp_path / "pytest.ini").write_text("[pytest]\n")
    (tmp_path / ".coveragerc").write_text("[report]\n" + setting + "\n")
    r.probe_coverage_transport(tmp_path)


def test_coverage_additional_source_directory_is_rejected_before_collection(tmp_path, monkeypatch):
    package = tmp_path / "src/llm_wiki_cli"
    package.mkdir(parents=True)
    (package / "owned.py").write_text("VALUE = 1\n")
    (tmp_path / "pytest.ini").write_text("[pytest]\n")
    (tmp_path / ".coveragerc").write_text("[run]\nsource_dirs = ../unowned\n")
    monkeypatch.setattr(r, "package_root", lambda root: package)
    with pytest.raises(r.q.QualificationError, match="additional source directories"):
        r.probe_coverage_transport(tmp_path)


@pytest.mark.parametrize("setting", [
    "omit = */unowned.py", "source_pkgs = llm_wiki_cli", "parallel = True", "concurrency = multiprocessing",
])
@linux_coverage_producer
def test_compatible_coverage_run_settings_remain_supported(tmp_path, setting):
    package = tmp_path / "src/llm_wiki_cli"
    package.mkdir(parents=True)
    (package / "owned.py").write_text("VALUE = 1\n")
    (tmp_path / "pytest.ini").write_text("[pytest]\n")
    (tmp_path / ".coveragerc").write_text("[run]\n" + setting + "\n")
    r.probe_coverage_transport(tmp_path)


@linux_coverage_producer
def test_coverage_report_probe_preserves_active_configured_outputs(tmp_path):
    package = tmp_path / "src/llm_wiki_cli"
    package.mkdir(parents=True)
    (package / "owned.py").write_text("VALUE = 1\n")
    (tmp_path / "pytest.ini").write_text("[pytest]\n")
    data, debug, xml = (tmp_path / name for name in ("active.data", "active.log", "active.xml"))
    for path in (data, debug, xml):
        path.write_bytes(b"retained prior bytes")
    (tmp_path / ".coveragerc").write_text(
        f"[run]\ndata_file = {data}\ndebug_file = {debug}\ndebug = dataio\n[xml]\noutput = {xml}\n"
    )
    r.probe_coverage_transport(tmp_path)
    assert all(path.read_bytes() == b"retained prior bytes" for path in (data, debug, xml))


@pytest.mark.parametrize("name", [".coveragerc.toml", ".pytest.toml"])
def test_alternative_configuration_files_are_bounded_before_reading(tmp_path, name):
    config = tmp_path / name
    config.write_bytes(b"#" * (1024 * 1024 + 1))
    with pytest.raises(r.q.QualificationError, match="configuration is redirected or oversized"):
        r.probe_coverage_transport(tmp_path)


@pytest.mark.parametrize("variable", ["COVERAGE_RCFILE", "COVERAGE_FORCE_CONFIG"])
def test_alternate_coverage_rcfile_is_rejected_before_reading_it(tmp_path, monkeypatch, variable):
    import coverage
    outside = tmp_path / "external.coveragerc"
    outside.write_text("[run]\nbranch = False\n")
    root = tmp_path / "candidate"
    root.mkdir()
    monkeypatch.setenv(variable, str(outside))
    monkeypatch.setattr(coverage, "Coverage", lambda **kwargs: pytest.fail("Alternate config reached constructor"))
    with pytest.raises(r.q.QualificationError, match="alternate " + variable):
        r.probe_coverage_transport(root)
    assert outside.read_text() == "[run]\nbranch = False\n"


def test_execute_checks_actual_coverage_policy_before_starting_worker(tmp_path, monkeypatch):
    root = tmp_path / "candidate"
    root.mkdir()
    (root / ".coveragerc").write_text("[run]\ndynamic_context = test_function\n")
    monkeypatch.setattr(r, "context", lambda args: context())

    def no_worker(*args, **kwargs):
        raise AssertionError("Unsupported instrumentation started worker")

    monkeypatch.setattr(r, "invoke", no_worker)
    args = argparse.Namespace(root=root, output=tmp_path / "evidence", shards=2, purpose="qualification", index=0)
    with pytest.raises(r.q.QualificationError, match="context policy"):
        r.execute(args)
    assert r.s.read(args.output / "execution.json")["complete"] is False


@pytest.mark.parametrize("prefix", ["C:/owned/package", r"C:\owned\package"])
def test_windows_coverage_prefix_cannot_enter_canonical_linux_transport(tmp_path, prefix):
    from release import core_coverage

    package, directory = coverage_fixture(tmp_path, [1])
    path = directory / "coverage.data"
    sources = r.source_manifest(package)
    before = r.q.sha256_file(path)
    with pytest.raises(r.q.QualificationError, match="invalid coverage source prefix"):
        r.coverage_rows(path, [prefix], sources)
    with pytest.raises(ValueError, match="invalid coverage source prefix"):
        core_coverage.raw_lines(path, [prefix], sources)
    assert r.q.sha256_file(path) == before


def test_pure_coverage_reader_rejects_oversized_bitset_before_expansion(tmp_path):
    import sqlite3
    from release import core_coverage
    package, directory = coverage_fixture(tmp_path, [1])
    path = directory / "coverage.data"
    with closing(sqlite3.connect(path)) as connection, connection:
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
    canonical_linux_artifact(output)
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


@pytest.mark.parametrize("failure", [None, "schema", "query"])
def test_raw_coverage_connection_closes_on_success_and_every_failure(tmp_path, monkeypatch, failure):
    import sqlite3
    from release import core_coverage
    package, directory = coverage_fixture(tmp_path, [1, 2])
    path = directory / "coverage.data"
    if failure is not None:
        with closing(sqlite3.connect(path)) as setup, setup:
            if failure == "schema":
                setup.execute("UPDATE meta SET value = '1' WHERE key = 'has_arcs'")
            else:
                setup.execute("DROP TABLE coverage_schema")
    connections = []
    real_connect = sqlite3.connect
    class TrackedConnection(sqlite3.Connection):
        close_count = 0
        def close(self):
            self.close_count += 1
            super().close()
    def tracked_connect(*args, **kwargs):
        connection = real_connect(*args, factory=TrackedConnection, **kwargs)
        connections.append(connection)
        return connection
    monkeypatch.setattr(core_coverage.sqlite3, "connect", tracked_connect)
    try:
        if failure is None:
            assert core_coverage.raw_lines(path, ["/owned/package"], r.source_manifest(package)) == {"owned.py": [1, 2]}
        else:
            with pytest.raises(ValueError if failure == "schema" else sqlite3.DatabaseError):
                core_coverage.raw_lines(path, ["/owned/package"], r.source_manifest(package))
        assert len(connections) == 1 and connections[0].close_count == 1
        with pytest.raises(sqlite3.ProgrammingError, match="closed database"):
            connections[0].execute("SELECT 1")
    finally:
        # A failed close assertion must remain the reported failure rather than
        # leaking this deliberate retained reference into another test's GC.
        for connection in connections:
            if connection.close_count == 0:
                connection.close()
