"""Independent static route, source-presence and false-coverage controls."""

from __future__ import annotations

import ast
import hashlib
import importlib
from pathlib import Path
import subprocess

import pytest

from llm_wiki_cli.extractors.python_extractor import PythonExtractor, module_alias_target
from llm_wiki_cli.services.extraction_service import ExtractorStatus
from llm_wiki_cli.services.lint_service import (
    LintReport,
    _check_module_coverage,
    report_to_dict,
)
from llm_wiki_cli.services.source_snapshot import build_source_snapshot


ROOT = Path(__file__).resolve().parents[1]
HISTORICAL_ALIASES = {
    "src/llm_wiki_cli/commands/bootstrap_cmd.py": "src/llm_wiki_cli/services/bootstrap_runtime.py",
    "src/llm_wiki_cli/commands/context_cmd.py": "src/llm_wiki_cli/services/context_service.py",
    "src/llm_wiki_cli/commands/extract_cmd.py": "src/llm_wiki_cli/services/extraction_service.py",
    "src/llm_wiki_cli/commands/lint_cmd.py": "src/llm_wiki_cli/services/lint_service.py",
    "src/llm_wiki_cli/services/documentation_calibration.py": "src/llm_wiki_cli/services/calibration/contracts.py",
    "src/llm_wiki_cli/services/documentation_calibration_broker.py": "src/llm_wiki_cli/services/calibration/broker.py",
    "src/llm_wiki_cli/services/documentation_calibration_controller.py": "src/llm_wiki_cli/services/calibration/controller.py",
    "src/llm_wiki_cli/services/documentation_calibration_host_broker.py": "src/llm_wiki_cli/services/calibration/host_broker.py",
}
INITIALIZERS = (
    "src/llm_wiki_cli/schemas/__init__.py",
    "src/llm_wiki_cli/services/__init__.py",
)
SHIM = "import sys as _sys\nfrom . import impl as _impl\n_sys.modules[__name__] = _impl\n"


def _write(root, paths):
    for name, text in paths.items():
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")


def _inventory(root, snapshot):
    return PythonExtractor().extract(
        str(root), deep=True, source_files=snapshot.language_paths("python")
    )


def _coverage(root, snapshot, inventory):
    wiki = root / "wiki"
    wiki.mkdir(exist_ok=True)
    report = LintReport(wiki_dir=str(wiki), src_dir=str(root))
    _check_module_coverage(
        report, wiki, inventory, snapshot,
        {"python": ExtractorStatus(language="python", state="ok", files_found=len(snapshot.language_paths("python")))},
    )
    return report


def _diagnostic(report, path):
    rows = [row for row in report.diagnostics if row.path == path]
    assert len(rows) == 1
    return rows[0]


def test_all_ten_reported_paths_keep_presence_and_exact_static_owner():
    snapshot = build_source_snapshot(ROOT, source_selection=".llm-wiki/source-selection.json")
    hashes = snapshot.hashes_for([*HISTORICAL_ALIASES, *INITIALIZERS])
    inventory = PythonExtractor().extract(
        str(ROOT), deep=True,
        source_files=sorted([*HISTORICAL_ALIASES, *HISTORICAL_ALIASES.values(), *INITIALIZERS]),
    )
    # The independent fixture names source owners, rather than inferring them
    # from classifier output. Redirects never acquire duplicate declarations.
    assert not (set(HISTORICAL_ALIASES) | set(INITIALIZERS)) & set(inventory)
    report = LintReport(wiki_dir="unused", src_dir=str(ROOT))
    _check_module_coverage(
        report, ROOT / "docs/llm_wiki", inventory, snapshot,
        {"python": ExtractorStatus(language="python", state="ok", files_found=len(snapshot.language_paths("python")))},
    )
    for path, owner in HISTORICAL_ALIASES.items():
        row = _diagnostic(report, path)
        assert (row.category, row.reason_code, row.severity, row.target) == (
            "module_source_routes", "static-module-alias", "info", owner,
        )
        assert path in row.message and owner in row.message
        assert hashes[path] in row.message
        assert row.hint is not None and "governance" in row.hint
    for path in INITIALIZERS:
        row = _diagnostic(report, path)
        assert (row.category, row.reason_code, row.severity) == (
            "module_source_presence", "declaration-free-initializer", "info",
        )
        assert hashes[path] in row.message and "no implementation" in row.message
    assert snapshot.hashes_for([*HISTORICAL_ALIASES, *INITIALIZERS]) == hashes
    assert all(hashes[path] == "sha256:" + hashlib.sha256((ROOT / path).read_bytes()).hexdigest() for path in hashes)
    assert not [row for row in report.diagnostics if row.category == "uncovered_source_files" and row.path in hashes]


@pytest.mark.parametrize("body", [
    "import sys\nfrom . import impl\nother.modules[__name__] = impl\n",
    "import sys\nfrom . import impl\nsys = other\nsys.modules[__name__] = impl\n",
    "import sys\nfrom . import impl\nimpl = other\nsys.modules[__name__] = impl\n",
    "import sys\nsys.modules[__name__] = factory()\n",
    "import sys\nfrom . import impl\nif condition:\n    sys.modules[__name__] = impl\n",
    "import sys\nfrom . import impl\nsys.modules[__name__] = impl\nregister()\n",
    "import sys\nfrom . import impl\nregister()\nsys.modules[__name__] = impl\n",
    "import sys\nfrom . import impl\nsys.modules[__name__] = impl\nsys.modules[__name__] = impl\n",
    "import sys\nfrom . import impl\n__name__ = 'other'\nsys.modules[__name__] = impl\n",
    "import sys\nfrom .impl import *\nsys.modules[__name__] = impl\n",
    "import sys\nfrom . import impl\ndef own():\n    return 1\nsys.modules[__name__] = impl\n",
    "import sys\nfrom . import impl\nfrom typing import TYPE_CHECKING\nTYPE_CHECKING = True\nif TYPE_CHECKING:\n    impl = other\nsys.modules[__name__] = impl\n",
    "import sys\nfrom . import impl\nfrom typing import TYPE_CHECKING\nif TYPE_CHECKING:\n    from .other import value\nelse:\n    impl = other\nsys.modules[__name__] = impl\n",
    "import sys\nfrom . import impl\nfrom __future__ import annotations as sys\nsys.modules[__name__] = impl\n",
])
def test_only_import_bound_unconditional_static_shims_are_omitted(tmp_path, body):
    assert module_alias_target(ast.parse(body)) == ""
    _write(tmp_path, {"pkg/shim.py": body, "pkg/impl.py": "def run():\n    return 1\n"})
    snapshot = build_source_snapshot(tmp_path)
    inventory = _inventory(tmp_path, snapshot)
    assert "pkg/shim.py" in inventory
    # Even an extractor miss must remain a warning, never a confident route.
    inventory.pop("pkg/shim.py")
    row = _diagnostic(_coverage(tmp_path, snapshot, inventory), "pkg/shim.py")
    assert row.category == "uncovered_source_files" and row.severity == "warning"


def test_type_only_reexports_do_not_override_the_runtime_alias(tmp_path):
    _write(tmp_path, {
        "pkg/__init__.py": "",
        "pkg/impl.py": "def run():\n    return 1\n",
        "pkg/shim.py": SHIM.replace("_sys.modules", "from typing import TYPE_CHECKING as TC\nif TC:\n    from .other import run as run\n_sys.modules"),
    })
    snapshot = build_source_snapshot(tmp_path)
    inventory = _inventory(tmp_path, snapshot)
    row = _diagnostic(_coverage(tmp_path, snapshot, inventory), "pkg/shim.py")
    assert row.target == "pkg/impl.py" and row.reason_code == "static-module-alias"


def test_reexport_is_a_module_and_never_inferred_as_a_module_alias(tmp_path):
    _write(tmp_path, {"pkg/impl.py": "def run():\n    return 1\n", "pkg/export.py": "from .impl import run as run\n"})
    snapshot = build_source_snapshot(tmp_path)
    inventory = _inventory(tmp_path, snapshot)
    assert "pkg/export.py" in inventory
    assert inventory["pkg/export.py"]["functions"] == []
    assert not [row for row in _coverage(tmp_path, snapshot, inventory).diagnostics if row.path == "pkg/export.py"]
    inventory.pop("pkg/export.py")
    row = _diagnostic(_coverage(tmp_path, snapshot, inventory), "pkg/export.py")
    assert row.category == "uncovered_source_files"


@pytest.mark.parametrize("body", [
    "def actual():\n    return 1\n", "class Actual:\n    pass\n",
    "register()\n", "raise RuntimeError('never execute')\n", "from .impl import run\n",
])
def test_initializer_with_behavior_or_exports_is_never_excused_as_empty(tmp_path, body):
    _write(tmp_path, {"pkg/__init__.py": body})
    snapshot = build_source_snapshot(tmp_path)
    row = _diagnostic(_coverage(tmp_path, snapshot, {}), "pkg/__init__.py")
    assert row.category == "uncovered_source_files" and row.severity == "warning"


def test_real_implementation_miss_and_unowned_empty_module_still_warn(tmp_path):
    _write(tmp_path, {"actual.py": "def run():\n    return 1\n", "empty.py": ""})
    report = _coverage(tmp_path, build_source_snapshot(tmp_path), {})
    assert {row.path for row in report.diagnostics if row.category == "uncovered_source_files"} == {"actual.py", "empty.py"}
    assert {row.message for row in report.diagnostics} == {
        f"Scanned source file produced no module entry, so it has no wiki page: {path}"
        for path in ("actual.py", "empty.py")
    }
    assert report.issues == [] and report.passed


def test_alias_to_a_missing_extraction_is_an_unresolved_warning(tmp_path):
    _write(tmp_path, {"pkg/shim.py": SHIM, "pkg/impl.py": "def run():\n    return 1\n"})
    snapshot = build_source_snapshot(tmp_path)
    row = _diagnostic(_coverage(tmp_path, snapshot, {}), "pkg/shim.py")
    assert row.category == "uncovered_source_files" and row.severity == "warning"
    assert row.reason_code == "alias-target-not-extracted" and "pkg/impl.py" in row.message


@pytest.mark.parametrize("body", [
    "impl = object()\n", "from other import impl\n", "def __getattr__(name):\n    return object()\n",
    "def impl():\n    return 1\n", "register()\n",
    "def unrelated(value: register()):\n    return value\n",
])
def test_package_rebindings_and_dynamic_initializers_do_not_prove_child_routes(tmp_path, body):
    _write(tmp_path, {"pkg/__init__.py": body, "pkg/shim.py": SHIM, "pkg/impl.py": "def run():\n    return 1\n"})
    snapshot = build_source_snapshot(tmp_path)
    row = _diagnostic(_coverage(tmp_path, snapshot, _inventory(tmp_path, snapshot)), "pkg/shim.py")
    assert row.category == "uncovered_source_files"
    assert row.reason_code == "alias-package-binding-unproven"


def test_cycles_and_ambiguous_sources_stay_unresolved(tmp_path):
    _write(tmp_path, {
        "pkg/a.py": SHIM.replace("impl", "b"),
        "pkg/b.py": SHIM.replace("impl", "a"),
        "pkg/shim.py": SHIM,
        "pkg/impl.py": "def run():\n    return 1\n",
        "pkg/impl/__init__.py": "def other():\n    return 2\n",
    })
    snapshot = build_source_snapshot(tmp_path)
    report = _coverage(tmp_path, snapshot, _inventory(tmp_path, snapshot))
    assert _diagnostic(report, "pkg/a.py").reason_code == "alias-cycle"
    assert _diagnostic(report, "pkg/b.py").reason_code == "alias-cycle"
    assert _diagnostic(report, "pkg/shim.py").reason_code == "alias-target-ambiguous"


def test_excluded_target_is_not_read_or_admitted(tmp_path, monkeypatch):
    _write(tmp_path, {"pkg/shim.py": SHIM, "pkg/impl.py": "raise RuntimeError('excluded')\n", ".gitignore": "impl.py\n"})
    snapshot = build_source_snapshot(tmp_path)
    assert "pkg/impl.py" not in snapshot.all_source_paths
    original = Path.open
    def guarded(path, *args, **kwargs):
        assert path != tmp_path / "pkg/impl.py"
        return original(path, *args, **kwargs)
    monkeypatch.setattr(Path, "open", guarded)
    row = _diagnostic(_coverage(tmp_path, snapshot, {}), "pkg/shim.py")
    assert row.reason_code == "alias-target-not-selected"


@pytest.mark.parametrize("mutation", ["edit", "remove", "symlink", "syntax", "budget"])
def test_unavailable_or_changed_capture_cannot_excuse_a_missing_entry(tmp_path, mutation):
    path = tmp_path / "pkg/__init__.py"
    _write(tmp_path, {"pkg/__init__.py": '"""Empty package."""\n'})
    if mutation == "syntax":
        path.write_text("class Broken(:\n")
    elif mutation == "budget":
        path.write_text("#" * (1048576 + 1))
    snapshot = build_source_snapshot(tmp_path)
    if mutation == "edit":
        path.write_text("def real():\n    return 1\n")
    elif mutation == "remove":
        path.unlink()
    elif mutation == "symlink":
        path.unlink()
        other = tmp_path / "outside.py"
        other.write_text("# outside\n")
        path.symlink_to(other)
    row = _diagnostic(_coverage(tmp_path, snapshot, {}), "pkg/__init__.py")
    assert row.category == "uncovered_source_files"
    assert row.severity == "warning"


def test_routes_are_readonly_and_never_execute_project_imports(tmp_path, monkeypatch):
    _write(tmp_path, {"pkg/__init__.py": "", "pkg/shim.py": SHIM, "pkg/impl.py": "raise RuntimeError('must not execute')\ndef run():\n    return 1\n"})
    snapshot = build_source_snapshot(tmp_path)
    inventory = _inventory(tmp_path, snapshot)
    before = snapshot.hashes_for()
    def forbidden(*args, **kwargs):
        pytest.fail("coverage classification executed a process or import")
    monkeypatch.setattr(importlib, "import_module", forbidden)
    monkeypatch.setattr(subprocess, "run", forbidden)
    row = _diagnostic(_coverage(tmp_path, snapshot, inventory), "pkg/shim.py")
    assert row.reason_code == "static-module-alias"
    assert snapshot.hashes_for() == before
    payload = report_to_dict(_coverage(tmp_path, snapshot, inventory))
    assert set(payload) == {"wiki_dir", "src_dir", "strict", "knowledge_drift_gate", "knowledge_drift_report", "ok", "issue_count", "issues", "diagnostics"}


def test_static_routes_can_end_at_a_package_without_ignoring_its_implementation(tmp_path):
    _write(tmp_path, {"pkg/shim.py": SHIM, "pkg/impl/__init__.py": "def run():\n    return 1\n"})
    snapshot = build_source_snapshot(tmp_path)
    row = _diagnostic(_coverage(tmp_path, snapshot, _inventory(tmp_path, snapshot)), "pkg/shim.py")
    assert row.reason_code == "static-module-alias" and row.target == "pkg/impl/__init__.py"


@pytest.mark.parametrize("hops, expected", [(16, "static-module-alias"), (17, "alias-hop-limit")])
def test_alias_hop_bound_is_explicit(tmp_path, hops, expected):
    paths = {"pkg/__init__.py": "", f"pkg/m{hops}.py": "def run():\n    return 1\n"}
    paths.update({f"pkg/m{i}.py": SHIM.replace("impl", f"m{i+1}") for i in range(hops)})
    _write(tmp_path, paths)
    snapshot = build_source_snapshot(tmp_path)
    row = _diagnostic(_coverage(tmp_path, snapshot, _inventory(tmp_path, snapshot)), "pkg/m0.py")
    assert row.reason_code == expected


def test_excluded_initializer_is_not_assumed_to_be_an_empty_namespace(tmp_path):
    _write(tmp_path, {"pkg/shim.py": SHIM, "pkg/impl.py": "def run():\n    return 1\n", "pkg/__init__.py": "impl = object()\n", ".gitignore": "__init__.py\n"})
    snapshot = build_source_snapshot(tmp_path)
    row = _diagnostic(_coverage(tmp_path, snapshot, _inventory(tmp_path, snapshot)), "pkg/shim.py")
    assert row.reason_code == "alias-package-binding-unproven"


@pytest.mark.parametrize("body", [SHIM, "import sys\nimport pkg.impl as impl\nsys.modules[__name__] = impl\n"])
def test_a_module_file_is_not_treated_as_a_parent_package(tmp_path, body):
    _write(tmp_path, {"pkg.py": "def unrelated():\n    return 1\n", "pkg/shim.py": body, "pkg/impl.py": "def run():\n    return 1\n"})
    snapshot = build_source_snapshot(tmp_path)
    row = _diagnostic(_coverage(tmp_path, snapshot, _inventory(tmp_path, snapshot)), "pkg/shim.py")
    assert row.reason_code == "alias-package-binding-unproven"
