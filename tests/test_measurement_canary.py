"""Canary completeness and partial evidence controls without native emulation."""

import tarfile
from types import SimpleNamespace
import xml.etree.ElementTree as ET

import pytest

from release import measurement_canary as canary


def complete_result():
    critical = (
        canary.MODULE + "::test_timed_read_and_mutation_restore_equivalent_inputs"
    )
    nodes = [critical + "[" + group + "]" for group in canary.GROUPS]
    nodes += [canary.MODULE + "::test_other_" + str(i) for i in range(13)]
    collection = {"collected": nodes, "selected": list(nodes), "deselected": []}
    cases = {n: ET.Element("testcase") for n in nodes}
    capture = {"complete": True, "measurement_roots": list(canary.GROUPS)}
    return collection, list(nodes), cases, capture


def test_complete_canary_requires_every_collected_started_junit_node_and_five_groups():
    data = complete_result()
    assert canary.validate_results(*data) == {
        "collected": 18,
        "started": 18,
        "passed": 18,
        "skipped": 0,
        "deselected": 0,
    }


def test_windows_regression_runs_when_shared_collection_harness_changes():
    from fnmatch import fnmatchcase
    from pathlib import Path

    import yaml

    root = Path(__file__).parents[1]
    workflow = yaml.safe_load((root / ".github/workflows/windows-measurement.yml").read_text())
    event = workflow.get("on", workflow.get(True))["pull_request"]
    assert event["branches"] == ["main"]
    for path in (
        "tests/__init__.py", "tests/conftest.py", "tests/pytest_portability.py",
        canary.MODULE, "tests/developer_value/runtime.py",
        "tests/provider_conformance/__init__.py", "tests/provider_conformance/python_ast.py",
    ):
        assert any(fnmatchcase(path, pattern) for pattern in event["paths"]), path
    assert not any(fnmatchcase("docs/unrelated.md", pattern) for pattern in event["paths"])


@pytest.mark.parametrize(
    "mutation",
    [
        "duplicate",
        "deselect",
        "missing-group",
        "not-started",
        "duplicate-start",
        "missing-junit",
        "skip",
        "failure",
        "partial-raw",
        "missing-raw-group",
    ],
)
def test_incomplete_or_failed_measurement_evidence_never_passes(mutation):
    collection, started, cases, capture = complete_result()
    first = collection["collected"][0]
    if mutation == "duplicate":
        collection["collected"].append(first)
    elif mutation == "deselect":
        collection["deselected"].append(first)
    elif mutation == "missing-group":
        collection["collected"][0] = collection["selected"][0] = started[0] = (
            canary.MODULE + "::test_replacement"
        )
        cases[canary.MODULE + "::test_replacement"] = cases.pop(first)
    elif mutation == "not-started":
        started.pop()
    elif mutation == "duplicate-start":
        started.append(first)
    elif mutation == "missing-junit":
        cases.pop(first)
    elif mutation in {"skip", "failure"}:
        ET.SubElement(cases[first], "skipped" if mutation == "skip" else "failure")
    elif mutation == "partial-raw":
        capture["complete"] = False
    else:
        capture["measurement_roots"].pop()
    with pytest.raises(canary.CanaryError):
        canary.validate_results(collection, started, cases, capture)


def test_raw_report_capture_retains_partial_worker_outputs(tmp_path):
    basetemp, out = tmp_path / "pytest", tmp_path / "out"
    report = basetemp / "failed-worker/measurements/partial/sample.json"
    report.parent.mkdir(parents=True)
    report.write_text('{"stage":"before-timeout"}')
    out.mkdir()
    result = canary.capture_reports(basetemp, out)
    assert result["complete"] and result["files"][
        "failed-worker/measurements/partial/sample.json"
    ]["sha256"] == canary.sha(report)
    with tarfile.open(out / "measurement-reports.tar") as archive:
        stream = archive.extractfile("failed-worker/measurements/partial/sample.json")
        assert stream is not None
        with stream:
            assert stream.read() == report.read_bytes()


def test_raw_capture_refuses_report_aliases_and_preserves_external_bytes(tmp_path):
    basetemp, out = tmp_path / "pytest", tmp_path / "out"
    reports = basetemp / "worker/measurements"
    reports.mkdir(parents=True)
    outside = tmp_path / "outside.json"
    outside.write_bytes(b"do not read through a report alias")
    (reports / "aliased.json").symlink_to(outside)
    out.mkdir()
    result = canary.capture_reports(basetemp, out)
    assert result["complete"] is False and result["files"] == {}
    assert outside.read_bytes() == b"do not read through a report alias"


def test_raw_capture_byte_limit_is_enforced_without_deleting_worker_data(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(canary, "MAX_REPORT_BYTES", 3)
    basetemp, out = tmp_path / "pytest", tmp_path / "out"
    reports = basetemp / "worker/measurements"
    reports.mkdir(parents=True)
    (reports / "large.json").write_bytes(b"1234")
    out.mkdir()
    result = canary.capture_reports(basetemp, out)
    assert not result["complete"] and (reports / "large.json").read_bytes() == b"1234"


def test_wrong_native_runtime_fails_before_collection_or_source_mutation(
    tmp_path, monkeypatch
):
    root, out = tmp_path / "candidate", tmp_path / "out"
    root.mkdir()
    (root / "sentinel").write_bytes(b"preserve")
    monkeypatch.setattr(canary, "sys", SimpleNamespace(platform="linux"))
    args = SimpleNamespace(root=root, output=out, expected_python="3.13.17")
    with pytest.raises(canary.CanaryError, match="native Windows"):
        canary.run(args)
    assert not out.exists() and (root / "sentinel").read_bytes() == b"preserve"


@pytest.fixture
def pr_checkout(tmp_path):
    import subprocess

    root = tmp_path / "candidate"
    root.mkdir()

    def git(*args, input=None):
        return subprocess.check_output(
            ["git", "-C", str(root), "-c", "user.name=Source guard",
             "-c", "user.email=source@example.invalid", "-c", "commit.gpgsign=false", "-c", "core.autocrlf=false",
             "-c", f"core.hooksPath={tmp_path / 'absent-hooks'}", *args],
            input=input, stderr=subprocess.STDOUT,
        ).decode().strip()

    git("init", "-q")
    (root / "owned").write_text("original bytes")
    (root / ".gitignore").write_text("reports/\n.venv/\nbuild/\n")
    tests = root / "tests"
    tests.mkdir()
    (tests / "test_owned.py").write_text("def test_owned():\n    assert True\n")
    package = root / "src/llm_wiki_cli"
    package.mkdir(parents=True)
    (package / "__init__.py").write_text("VALUE = 1\n")
    git("add", ".")
    git("commit", "-qm", "Base")
    ancestor = git("rev-parse", "HEAD")
    git("commit", "--allow-empty", "-qm", "PR head")
    head = git("rev-parse", "HEAD")
    git("checkout", "--detach", ancestor)
    (root / "base-only").write_text("base change")
    git("add", ".")
    git("commit", "-qm", "Advanced base")
    base = git("rev-parse", "HEAD")
    git("merge", "--no-ff", "-m", "PR test merge", head)
    source = git("rev-parse", "HEAD")
    tree = canary.verify_pr_source(root, source, base, head, include_untracked=True)
    return root, git, source, base, head, tree


def test_pr_source_guard_allows_generated_files_only_after_initial_admission(pr_checkout):
    root, _git, source, base, head, tree = pr_checkout
    generated = root / "generated-report.json"
    generated.write_bytes(b"retained diagnostic")
    assert canary.verify_pr_source(root, source, base, head, tree_sha=tree) == tree
    with pytest.raises(canary.CanaryError, match="source is not clean"):
        canary.verify_pr_source(root, source, base, head, include_untracked=True)
    assert generated.read_bytes() == b"retained diagnostic"


@pytest.mark.parametrize("mutation", [
    "clean-reset", "same-tree-commit", "tracked-change", "wrong-parent", "replaced-tree",
])
def test_pr_source_guard_rejects_changed_identity_even_when_git_status_is_clean(
    pr_checkout, mutation,
):
    root, git, source, base, head, tree = pr_checkout
    reason = "PR merge identity differs"
    if mutation == "clean-reset":
        git("reset", "--hard", head)
    elif mutation == "same-tree-commit":
        git("commit", "--allow-empty", "-qm", "Different clean identity")
        assert git("rev-parse", "HEAD^{tree}") == tree
    elif mutation == "tracked-change":
        (root / "owned").write_text("changed source")
        reason = "PR tracked source changed"
    elif mutation == "wrong-parent":
        base = head
    else:
        (root / "owned").write_text("replacement source")
        git("add", "owned")
        replacement_tree = git("write-tree")
        replacement = git("commit-tree", replacement_tree, "-p", base, "-p", head,
                          input=b"Replacement tree\n")
        git("reset", "--hard", source)
        git("replace", source, replacement)
        git("read-tree", "--reset", "-u", source)
        assert git("rev-parse", "HEAD") == source
        assert git("rev-parse", "HEAD^{tree}") != tree
        reason = "PR tracked source changed"
    if mutation != "tracked-change":
        assert not git("status", "--porcelain", "--untracked-files=no")
    with pytest.raises(canary.CanaryError, match=reason):
        canary.verify_pr_source(root, source, base, head, tree_sha=tree)


@pytest.mark.parametrize("replace_worktree", [False, True])
def test_pr_initial_admission_and_git_reads_use_original_objects(pr_checkout, replace_worktree):
    root, git, source, base, head, original_tree = pr_checkout
    (root / "owned").write_text("replacement source")
    git("add", "owned")
    replacement_tree = git("write-tree")
    replacement = git("commit-tree", replacement_tree, "-p", base, "-p", head,
                      input=b"Replacement merge\n")
    git("reset", "--hard", source)
    git("replace", source, replacement)
    if replace_worktree:
        git("read-tree", "--reset", "-u", source)
        assert not git("status", "--porcelain")
    assert git("rev-parse", "HEAD") == source
    assert git("show", "-s", "--format=%P", source).split() == [base, head]
    assert git("rev-parse", "HEAD^{tree}") == replacement_tree
    assert canary.git_output(root, "rev-parse", "HEAD^{tree}").decode().strip() == original_tree
    # The same wrapper reads base-owned readers and the workflow at runtime.
    assert canary.git_output(root, "show", source + ":owned") == b"original bytes"
    if replace_worktree:
        with pytest.raises(canary.CanaryError, match="PR source is not clean"):
            canary.verify_pr_source(root, source, base, head, include_untracked=True)
    else:
        assert canary.verify_pr_source(root, source, base, head, include_untracked=True) == original_tree
    assert git("replace", "-l") == source


@pytest.mark.parametrize("hiding", ["assume-unchanged", "skip-worktree", "stat-cache"])
def test_canonical_blob_guard_rejects_hidden_dirty_bytes(pr_checkout, hiding):
    import os
    import time

    root, git, source, base, head, tree = pr_checkout
    path = root / "owned"
    if hiding == "stat-cache":
        old = time.time_ns() - 10_000_000_000
        os.utime(path, ns=(old, old))
        git("update-index", "--refresh")
        git("config", "core.trustctime", "false")
        git("config", "core.checkStat", "minimal")
    else:
        git("update-index", "--" + hiding, "owned")
    before = path.stat()
    path.write_bytes(b"mutated! bytes")
    assert path.stat().st_size == before.st_size
    os.utime(path, ns=(before.st_atime_ns, before.st_mtime_ns))
    assert not git("status", "--porcelain")
    assert git("rev-parse", "HEAD") == source
    assert git("rev-parse", "HEAD^{tree}") == tree
    with pytest.raises(canary.CanaryError, match="Canonical tracked source bytes differ"):
        canary.verify_pr_source(root, source, base, head, tree_sha=tree)
    assert path.read_bytes() == b"mutated! bytes"


@pytest.mark.parametrize("limit", ["files", "single-file", "total-bytes", "metadata"])
def test_canonical_blob_guard_has_bounded_inventory_and_content(pr_checkout, monkeypatch, limit):
    root, _git, source, _base, _head, _tree = pr_checkout
    settings = {
        "files": ("MAX_TRACKED_SOURCE_FILES", 1),
        "single-file": ("MAX_TRACKED_FILE_BYTES", 1),
        "total-bytes": ("MAX_TRACKED_SOURCE_BYTES", 1),
        "metadata": ("MAX_GIT_OUTPUT", 1),
    }
    name, value = settings[limit]
    monkeypatch.setattr(canary, name, value)
    with pytest.raises(canary.CanaryError, match="bound"):
        canary.verify_tracked_source(root, source)
    assert (root / "owned").read_bytes() == b"original bytes"


def test_canonical_blob_guard_preserves_windows_executable_mode_semantics(pr_checkout):
    root, git, _source, base, head, _tree = pr_checkout
    git("update-index", "--chmod=+x", "owned")
    tree = git("write-tree")
    source = git("commit-tree", tree, "-p", base, "-p", head, input=b"Executable tracked mode\n")
    git("reset", "--hard", source)
    (root / "owned").chmod(0o644)
    git("config", "core.filemode", "false")
    assert not git("status", "--porcelain")
    assert canary.verify_pr_source(root, source, base, head, include_untracked=True) == tree


def test_canonical_blob_guard_refuses_tracked_symlink_types_without_following(pr_checkout, tmp_path):
    root, git, _source, base, head, _tree = pr_checkout
    outside = tmp_path / "external"
    outside.write_bytes(b"external retained")
    (root / "aliased").symlink_to(outside)
    git("add", "aliased")
    tree = git("write-tree")
    source = git("commit-tree", tree, "-p", base, "-p", head, input=b"Unsupported link\n")
    with pytest.raises(canary.CanaryError, match="Unsupported tracked source type"):
        canary.verify_tracked_source(root, source)
    assert outside.read_bytes() == b"external retained"


def test_canonical_blob_guard_refuses_tracked_parent_redirects(pr_checkout, tmp_path):
    root, git, _source, base, head, _tree = pr_checkout
    nested = root / "nested"
    nested.mkdir()
    (nested / "data").write_bytes(b"original bytes")
    git("add", "nested")
    tree = git("write-tree")
    source = git("commit-tree", tree, "-p", base, "-p", head, input=b"Nested source\n")
    outside = tmp_path / "retained-source"
    nested.rename(outside)
    nested.symlink_to(outside, target_is_directory=True)
    with pytest.raises(canary.CanaryError, match="Redirected canary path"):
        canary.verify_tracked_source(root, source)
    assert (outside / "data").read_bytes() == b"original bytes"


def test_canonical_blob_metadata_rejects_drive_relative_windows_paths(pr_checkout, monkeypatch):
    from pathlib import PureWindowsPath

    root, _git, source, _base, _head, _tree = pr_checkout
    name = "C:escaped.py"
    assert PureWindowsPath(name).drive and not PureWindowsPath(name).is_absolute()
    metadata = b"100644 blob " + b"a" * 40 + b" 1\t" + name.encode() + b"\0"
    monkeypatch.setattr(canary, "git_output", lambda *a: metadata)
    with pytest.raises(canary.CanaryError, match="Invalid tracked source path"):
        canary.verify_tracked_source(root, source)


def test_redirect_detection_uses_windows_reparse_metadata_without_new_path_apis():
    import stat

    class ReparseDirectory:
        def lstat(self):
            return SimpleNamespace(st_mode=stat.S_IFDIR, st_file_attributes=0x400)

    assert canary.redirected(ReparseDirectory())


@pytest.mark.parametrize("name", [
    "conftest.py", "shadow.py", "shadow_package/__init__.py", ".pytest.ini",
    "namespace_shadow/module.py", "namespace_shadow/deep/module.pyc", "namespace_shadow/deep/module.so",
    "tests/test_added.py", "src/llm_wiki_cli/extra.py", "src/llm_wiki_cli/extra.json",
])
def test_pr_source_guard_rejects_executable_and_data_additions_after_observation(pr_checkout, name):
    root, git, source, base, head, tree = pr_checkout
    path = root / name
    path.parent.mkdir(parents=True, exist_ok=True)
    marker = root / "candidate-executed"
    path.write_text(f"from pathlib import Path\nPath({str(marker)!r}).write_text('unsafe')\n")
    assert not git("status", "--porcelain", "--untracked-files=no")
    with pytest.raises(canary.CanaryError, match="unfrozen source"):
        canary.verify_pr_source(root, source, base, head, tree_sha=tree)
    assert not marker.exists()


def test_pr_source_guard_preserves_ordinary_generated_scaffolding(pr_checkout):
    root, _git, source, base, head, tree = pr_checkout
    paths = ["reports/nested/control.py", ".venv/pyvenv.cfg", "build/lib/output.py",
             "src/agent_wiki_cli.egg-info/PKG-INFO",
             "src/llm_wiki_cli/__pycache__/__init__.cpython-313.pyc"]
    for name in paths:
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"retained generated bytes")
    assert canary.verify_pr_source(root, source, base, head, tree_sha=tree) == tree
    assert all((root / name).read_bytes() == b"retained generated bytes" for name in paths)


def test_pr_source_guard_allows_unknown_data_only_and_empty_directories(pr_checkout):
    root, _git, source, base, head, tree = pr_checkout
    (root / "empty-diagnostic").mkdir()
    data = root / "diagnostic/nested/values.json"
    data.parent.mkdir(parents=True)
    data.write_bytes(b'{"captured": true}')
    assert canary.verify_pr_source(root, source, base, head, tree_sha=tree) == tree
    assert data.read_bytes() == b'{"captured": true}'


def test_pr_source_guard_rejects_unknown_directory_redirect_before_following(pr_checkout, tmp_path):
    root, _git, source, base, head, tree = pr_checkout
    outside = tmp_path / "external-package"
    outside.mkdir()
    marker = outside / "module.py"
    marker.write_bytes(b"raise RuntimeError('must not execute')\n")
    (root / "unknown-package").symlink_to(outside, target_is_directory=True)
    with pytest.raises(canary.CanaryError, match="redirected source input"):
        canary.verify_pr_source(root, source, base, head, tree_sha=tree)
    assert marker.read_bytes() == b"raise RuntimeError('must not execute')\n"


def test_raw_capture_materializes_shared_regular_bytes_without_following_aliases(
    tmp_path,
):
    import os

    basetemp, out = tmp_path / "pytest", tmp_path / "out"
    reports = basetemp / "worker/measurements"
    reports.mkdir(parents=True)
    source = reports / "one.json"
    source.write_bytes(b"shared immutable recovery content")
    os.link(source, reports / "two.json")
    out.mkdir()
    result = canary.capture_reports(basetemp, out)
    assert result["complete"] and len(result["files"]) == 2
    with tarfile.open(out / "measurement-reports.tar") as archive:
        members = archive.getmembers()
        assert all(member.isfile() for member in members)
        contents = []
        for member in members:
            stream = archive.extractfile(member)
            assert stream is not None
            with stream:
                contents.append(stream.read())
        assert contents == [source.read_bytes()] * 2
    assert source.stat().st_nlink == 2


def test_installed_probe_cannot_poison_measurement_source_provider(tmp_path):
    import json
    import os
    import subprocess
    import venv
    from pathlib import Path

    root = Path(__file__).parents[1]
    prefix = tmp_path / ".venv"
    venv.EnvBuilder(with_pip=False, symlinks=os.name != "nt").create(prefix)
    executable = prefix / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    site = Path(
        subprocess.check_output(
            [
                str(executable),
                "-I",
                "-c",
                "import pathlib,site;print(next(p for p in site.getsitepackages() if 'site-packages' in pathlib.Path(p).parts))",
            ],
            text=True,
        ).strip()
    )
    provider = tmp_path / "retained"
    source = provider / "src/llm_wiki_cli"
    source.mkdir(parents=True)
    (provider / "pyproject.toml").write_text(
        '[project]\nversion="9.0.0"\n[tool.setuptools.package-data]\nllm_wiki_cli=[]\n'
    )
    (source / "__init__.py").write_text('__version__="9.0.0"\n')
    (source / "api.py").write_text("VALUE=1\n")
    installed = site / "llm_wiki_cli"
    installed.mkdir()
    for name in ("__init__.py", "api.py"):
        (installed / name).write_bytes((source / name).read_bytes())
    metadata = site / "agent_wiki_cli-9.0.0.dist-info"
    metadata.mkdir()
    (metadata / "METADATA").write_text(
        "Metadata-Version: 2.1\nName: agent-wiki-cli\nVersion: 9.0.0\n"
    )
    (metadata / "direct_url.json").write_text(
        json.dumps({"url": provider.resolve().as_uri(), "dir_info": {}})
    )
    script = """import json,pathlib,sys
sys.path.insert(0,sys.argv[1])
from release import measurement_canary as canary
assert 'llm_wiki_cli' not in sys.modules
expected=canary.provider_files(pathlib.Path(sys.argv[2]))
observed=canary.verify_provider(expected)
assert 'site-packages' in pathlib.Path(observed['provider']).parts
assert 'llm_wiki_cli' not in sys.modules
from tests.developer_value.runtime import load_provider
api=load_provider(pathlib.Path(sys.argv[2]))
assert pathlib.Path(api.__file__).is_relative_to(pathlib.Path(sys.argv[2])/'src')
print(json.dumps({'installed_probe':'passed','source_adapter':'passed','controller_provider_imported_before_adapter':False}))
"""
    result = subprocess.run(
        [str(executable), "-I", "-c", script, str(root), str(provider)],
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert (
        json.loads(result.stdout)["controller_provider_imported_before_adapter"]
        is False
    )


@pytest.mark.parametrize("branch", ["main", "release/candidate"])
def test_frozen_canary_preserves_qualification_branch_contract(branch):
    sha = "a" * 40
    ref = "refs/heads/" + branch
    environment = {
        "GITHUB_WORKFLOW_SHA": sha,
        "GITHUB_WORKFLOW_REF": canary.REPOSITORY
        + "/.github/workflows/release-qualification.yml@"
        + ref,
        "GITHUB_REF": ref,
    }
    assert canary.workflow_identity(sha, frozen=True, environment=environment) == (
        sha,
        environment["GITHUB_WORKFLOW_REF"],
    )
    for changed in (
        {"GITHUB_REF": "refs/tags/v4.0.1"},
        {"GITHUB_WORKFLOW_SHA": "b" * 40},
        {"GITHUB_REF": "refs/heads/another"},
    ):
        with pytest.raises(canary.CanaryError):
            canary.workflow_identity(
                sha, frozen=True, environment={**environment, **changed}
            )


def final_probe_scenario(module, tmp_path, monkeypatch, *, mutate):
    """Exercise finalization with real Git; native execution is deliberately stubbed."""
    import json
    import subprocess
    import sys

    root = tmp_path / "candidate"
    root.mkdir()

    def git(*args):
        return subprocess.check_output(
            ["git", "-C", str(root), "-c", "user.name=Final source guard",
             "-c", "user.email=source@example.invalid", "-c", "commit.gpgsign=false",
             "-c", "core.autocrlf=false", "-c", f"core.hooksPath={tmp_path / 'no-hooks'}", *args],
            stderr=subprocess.STDOUT,
        ).decode().strip()

    git("init", "-q")
    files = {"owned": "original", ".gitignore": ".venv/\n", module.MODULE: "# controlled\n",
             ".github/workflows/windows-measurement.yml": "name: controlled\n"}
    files.update({"release/" + name: "# controlled base reader\n" for name in module.READERS})
    for name, text in files.items():
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
    git("add", ".")
    git("commit", "-qm", "Base")
    ancestor = git("rev-parse", "HEAD")
    git("commit", "--allow-empty", "-qm", "PR head")
    head = git("rev-parse", "HEAD")
    git("checkout", "--detach", ancestor)
    (root / "base-only").write_text("base change")
    git("add", ".")
    git("commit", "-qm", "Advanced base")
    base = git("rev-parse", "HEAD")
    git("merge", "--no-ff", "-m", "PR test merge", head)
    source = git("rev-parse", "HEAD")
    prefix = root / ".venv"
    prefix.mkdir()
    out = tmp_path / "evidence"
    env = {"GITHUB_REPOSITORY": module.REPOSITORY, "GITHUB_RUN_ID": "42",
           "GITHUB_RUN_ATTEMPT": "1", "BASE_SHA": base, "HEAD_SHA": head,
           "GITHUB_WORKFLOW_SHA": source,
           "GITHUB_WORKFLOW_REF": module.REPOSITORY + "/.github/workflows/windows-measurement.yml@refs/pull/7/merge"}
    for name, value in env.items():
        monkeypatch.setenv(name, value)
    for name in ("PYTEST_ADDOPTS", "PYTEST_PLUGINS"):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setattr(module, "sys", SimpleNamespace(
        platform="win32", prefix=str(prefix), base_prefix=str(tmp_path / "base"),
        maxsize=2**63 - 1, modules={}, path=list(sys.path), executable=sys.executable,
        orig_argv=[], argv=[],
    ))
    monkeypatch.setattr(module, "platform", SimpleNamespace(
        python_version=lambda: "3.13.17", machine=lambda: "AMD64",
    ))
    collection, started, cases, capture = complete_result()
    reader = SimpleNamespace(
        q=SimpleNamespace(load_json=lambda p: json.loads(p.read_bytes())),
        inventory=sorted, junit=lambda p: cases,
    )
    monkeypatch.setattr(module, "load", lambda name, path: reader if name == "measurement_core_reader" else object())
    monkeypatch.setattr(module, "provider_files", lambda path: {"version": "9.0.0"})
    probes = []

    def verify(expected):
        probes.append(expected)
        if len(probes) == 2 and mutate:
            (root / "owned").write_text("changed by final provider observation")
        return {"controlled_observation": len(probes)}

    monkeypatch.setattr(module, "verify_provider", verify)

    def execute(command, plugins):
        (out / "collection.json").write_text(json.dumps(collection))
        (out / "started.jsonl").write_text("".join(json.dumps(n) + "\n" for n in started))
        (out / "junit.xml").write_text("<testsuite />")
        return 0

    original_import = module.importlib.import_module
    monkeypatch.setattr(module.importlib, "import_module", lambda name: (
        SimpleNamespace(main=execute) if name == "pytest" else original_import(name)
    ))
    monkeypatch.setattr(module, "capture_reports", lambda *args: capture)
    git("remote", "add", "origin", "https://github.com/" + module.REPOSITORY + ".git")
    return SimpleNamespace(root=root, output=out, expected_python="3.13.17", source_sha=source,
                           expected_prefix=None, frozen_identity=None, harness_root=None)


@pytest.mark.parametrize("mutate", [False, True])
def test_canary_rechecks_source_after_final_provider_observation(tmp_path, monkeypatch, mutate):
    args = final_probe_scenario(canary, tmp_path, monkeypatch, mutate=mutate)
    if mutate:
        with pytest.raises(canary.CanaryError, match="PR tracked source changed"):
            canary.run(args)
        assert not (args.output / "result.json").exists()
        assert (args.root / "owned").read_text() == "changed by final provider observation"
    else:
        assert canary.run(args) == 0
        assert canary.git_output(args.root, "status", "--porcelain").strip() == b""
    assert (args.output / "installed-origin-after.json").exists()
