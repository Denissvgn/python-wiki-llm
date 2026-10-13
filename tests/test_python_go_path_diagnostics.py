"""Independent supplied-path outcomes for Python parsing and Go test policy."""

from __future__ import annotations

import ast
import json
import subprocess
import sys
from pathlib import Path

import pytest

from llm_wiki_cli import api
from llm_wiki_cli.extractors.common import discover_source_files
from llm_wiki_cli.extractors.python_extractor import PythonExtractor
from llm_wiki_cli.services import extraction_service, extractor_helpers, mcp_server
from llm_wiki_cli.services.source_path_diagnostics import source_path_diagnostics
from llm_wiki_cli.services.source_snapshot import build_source_snapshot


@pytest.fixture
def project(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    source = tmp_path / "source"
    source.mkdir()
    for name, content in {
        "app.py": "def app():\n    return 1\n",
        "broken.py": "def broken(\n",
        "empty.py": "# intentionally empty\n",
        "widget_test.go": "package widget\nfunc TestWidget() {}\n",
        "notes.txt": "unsupported input\n",
        "ignored.py": "def ignored(\n",
        ".gitignore": "ignored.py\n",
    }.items():
        (source / name).write_text(content, encoding="utf-8")
    api.bootstrap_wiki("source", "wiki")
    return source


def query(paths, **options):
    return api.query_documentation(
        {"operation": "impact", "paths": paths, "source_policy": "discovery", **options},
        src_dir="source", wiki_dir="wiki",
    )


def test_python_failure_empty_and_success_are_distinct(project):
    with pytest.raises(SyntaxError):
        ast.parse((project / "broken.py").read_text())
    assert ast.parse((project / "empty.py").read_text()).body == []
    result = query(["app.py", "broken.py", "empty.py", "widget_test.go", "notes.txt", "missing.py"])
    rows = {row["path"]: row for row in result["matches"]}
    assert rows["app.py"]["present"] is True
    assert rows["app.py"]["extraction_state"] == "extracted"
    for path in ("broken.py", "empty.py"):
        assert rows[path]["present"] is False
        assert rows[path]["filesystem_state"] == "file"
        assert rows[path]["selection_state"] == "included"
    assert rows["broken.py"]["extraction_state"] == "failed"
    assert rows["broken.py"]["reason"] == "syntax-error"
    assert rows["broken.py"]["failure_scope"] == "file"
    assert rows["empty.py"]["extraction_state"] == "no-documentable-content"
    assert rows["empty.py"]["reason"] == "no-documentable-content"
    assert "failure_scope" not in rows["empty.py"]
    assert rows["notes.txt"]["extraction_state"] == "unsupported"
    assert rows["notes.txt"]["reason"] == "unsupported-extension"
    assert rows["missing.py"]["filesystem_state"] == "missing"
    assert rows["missing.py"]["reason"] == "missing"


def test_go_test_is_a_policy_exclusion_without_helper_setup(project, monkeypatch):
    monkeypatch.setattr(extractor_helpers, "prepare_helper", lambda *a, **kw: pytest.fail("read prepared a helper"))
    row = query(["widget_test.go"])["matches"][0]
    assert row["present"] is False
    assert row["filesystem_state"] == "file"
    assert row["selection_state"] == "excluded"
    assert row["extraction_state"] == "not-attempted"
    assert row["reason"] == "go-tests-excluded"
    assert "failure_scope" not in row


@pytest.mark.parametrize("include_tests", [None, ["go"]])
def test_go_inclusion_matches_ordinary_discovery(project, monkeypatch, include_tests):
    monkeypatch.setattr(extractor_helpers, "prepare_helper", lambda *a, **kw: pytest.fail("read prepared a helper"))
    (project / "widget.go").write_text("package widget\nfunc Widget() {}\n")
    paths = ("widget.go", "widget_test.go")
    snapshot = build_source_snapshot(project, only_files=paths, include_tests=include_tests, respect_discovery=True)
    expected = {"widget.go", "widget_test.go"} if include_tests else {"widget.go"}
    assert set(snapshot.language_paths("go")) == expected
    assert set(discover_source_files(str(project), (".go",), language="go", include_tests=include_tests)) == expected
    rows = source_path_diagnostics(snapshot, paths)
    assert rows["widget.go"]["selection_state"] == "included"
    if include_tests:
        assert rows["widget_test.go"] == rows["widget.go"]
    else:
        assert rows["widget_test.go"]["reason"] == "go-tests-excluded"
    # The public impact contract deliberately has no Go test-inclusion option.
    with pytest.raises(api.InvalidRequestError):
        query(["widget_test.go"], include_tests=["go"])


@pytest.mark.parametrize("include_empty", [False, True])
def test_diagnostics_do_not_change_ordinary_inventory(project, include_empty):
    extractor = PythonExtractor()
    kwargs = {"src_dir": str(project), "deep": True, "include_empty": include_empty}
    legacy = extractor.extract(**kwargs)
    assert extractor.last_path_outcomes is None
    diagnosed = extractor.extract(**kwargs, diagnostics=True)
    assert diagnosed == legacy
    assert "broken.py" not in diagnosed
    assert ("empty.py" in diagnosed) is include_empty
    assert extractor.last_path_outcomes is not None
    assert extractor.last_path_outcomes["broken.py"]["reason"] == "syntax-error"
    assert extractor.last_path_outcomes["empty.py"]["extraction_state"] == (
        "extracted" if include_empty else "no-documentable-content"
    )
    extractor.extract(**kwargs)
    assert extractor.last_path_outcomes is None
    result = extraction_service.get_inventory_result(extraction_service.InventoryRequest(
        src_dir=project, deep=True, include_empty=include_empty,
    ))
    assert result.path_outcomes == {}
    payload = api.query_documentation(
        {"operation": "impact", "paths": ["broken.py", "empty.py", "widget_test.go"]},
        src_dir="source", wiki_dir="wiki",
    )
    assert all(not row["present"] for row in payload["matches"])
    assert all("extraction_state" not in row and "filesystem_state" not in row for row in payload["matches"])


def test_legacy_missing_outcome_remains_unavailable(project, monkeypatch):
    class LegacyExtractor:
        def extract(self, **kwargs):
            return {}

    monkeypatch.setattr(extraction_service, "_load_extractor", lambda *a: LegacyExtractor())
    row = query(["broken.py"])["matches"][0]
    assert row["extraction_state"] == "unavailable"
    assert row["reason"] == "outcome-not-reported"
    assert "failure_scope" not in row


def test_actual_batch_failure_is_distinct_from_file_syntax_error(project, monkeypatch):
    def fail(self, **kwargs):
        raise RuntimeError("independent batch failure")

    monkeypatch.setattr(PythonExtractor, "extract", fail)
    result = query(["broken.py", "empty.py"])
    assert {row["extraction_state"] for row in result["matches"]} == {"failed"}
    assert {row["reason"] for row in result["matches"]} == {"extractor-batch-failed"}
    assert {row["failure_scope"] for row in result["matches"]} == {"extractor-batch"}


@pytest.mark.parametrize("failure", ["decode", "read"])
def test_python_io_failure_is_attributable_without_stderr_parsing(tmp_path, monkeypatch, failure):
    source = tmp_path / "broken.py"
    source.write_bytes(b"\x81" if failure == "decode" else b"def app(): pass\n")
    if failure == "read":
        monkeypatch.setattr(Path, "read_bytes", lambda *a: (_ for _ in ()).throw(OSError("denied")))
    extractor = PythonExtractor()
    assert extractor.extract(str(tmp_path), source_files=["broken.py"], diagnostics=True) == {}
    assert extractor.last_path_outcomes == {
        "broken.py": {"extraction_state": "failed", "reason": f"source-{failure}-failed", "failure_scope": "file"},
    }


@pytest.mark.parametrize("limit", [1, 8])
def test_api_cli_mcp_agree_under_identical_limits(project, limit):
    request = {"operation": "impact", "paths": ["broken.py", "empty.py", "widget_test.go"], "source_policy": "discovery", "limit": limit}
    result = api.query_documentation(request, src_dir="source", wiki_dir="wiki")
    assert result["bounds"]["matches"] == {"total": 3, "returned": min(limit, 3), "truncated": limit < 3}
    Path("request.json").write_text(json.dumps(request))
    cli = subprocess.run(
        [sys.executable, "-m", "llm_wiki_cli.cli", "query", "--request", "request.json", "--src-dir", "source", "--wiki-dir", "wiki"],
        text=True, capture_output=True,
    )
    assert cli.returncode == 0, cli.stderr
    assert json.loads(cli.stdout) == result
    assert mcp_server.McpWikiService(src_dir="source", wiki_dir="wiki").query_documentation(request) == result


def test_ignore_exclusion_precedes_python_failure(project):
    row = query(["ignored.py"])["matches"][0]
    assert row["filesystem_state"] == "file"
    assert row["selection_state"] == "excluded"
    assert row["extraction_state"] == "not-attempted"
    assert row["reason"] == "gitignore"


def test_source_selection_exclusion_prevents_metadata_read(project, monkeypatch):
    (project / ".llm-wiki").mkdir()
    (project / ".llm-wiki/source-selection.json").write_text(json.dumps({
        "schema_version": "llm-wiki-source-selection/v1", "include": ["app.py"], "exclude": [],
    }))
    snapshot = build_source_snapshot(project, only_files=["broken.py", "widget_test.go"], respect_discovery=True)
    monkeypatch.setattr(Path, "lstat", lambda *a: pytest.fail("excluded source metadata was read"))
    rows = source_path_diagnostics(snapshot, ("broken.py", "widget_test.go"))
    for row in rows.values():
        assert row["filesystem_state"] == "unknown"
        assert row["selection_state"] == "excluded"
        assert row["extraction_state"] == "not-attempted"
        assert row["reason"] == "source-selection"


@pytest.mark.parametrize("path", ["link.py", "linked/app.py"])
def test_no_follow_rejects_leaf_and_parent_symlinks(project, path):
    (project / "link.py").symlink_to(project / "app.py")
    (project / "linked").symlink_to(project, target_is_directory=True)
    with pytest.raises(api.InvalidRequestError):
        query([path])


def test_mutation_aborts_whole_diagnostic_request(project, monkeypatch):
    original = PythonExtractor.extract

    def changing(self, *args, **kwargs):
        result = original(self, *args, **kwargs)
        (project / "app.py").write_text("def app(): return 2\n")
        return result

    monkeypatch.setattr(PythonExtractor, "extract", changing)
    with pytest.raises(api.WorkspaceStateError):
        query(["app.py", "broken.py", "widget_test.go"])
