"""Independent module-extension, dependency, and supplied-path acceptance cases."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from llm_wiki_cli import api
from llm_wiki_cli.extractors.ts_extractor import TypeScriptExtractor
from llm_wiki_cli.services import extraction_service, mcp_server
from llm_wiki_cli.services.dependencies import build_dependency_graph
from llm_wiki_cli.services.extractor_helpers import get_prepared_typescript_root
from llm_wiki_cli.services.imports import build_module_path_resolver
from llm_wiki_cli.services.inventory_cache import InventoryCacheOptions
from llm_wiki_cli.services.source_snapshot import build_source_snapshot, source_snapshot_matches_current_files


@pytest.fixture
def project(tmp_path, monkeypatch):
    monkeypatch.setenv(
        "LLM_WIKI_CACHE_DIR",
        os.environ.get("LLM_WIKI_CACHE_DIR", str(Path(__file__).resolve().parents[1] / ".git")),
    )
    monkeypatch.chdir(tmp_path)
    source = tmp_path / "source"
    source.mkdir()
    files = {
        "plain.js": "function plain() { return 1; }",
        "component.jsx": "export function Component() { return null; }",
        "main.mjs": 'import { helper } from "./helper.mjs"; import "./side.mjs"; export function run() { return helper(); }',
        "helper.mjs": "export function helper() { return 1; }",
        "helper.cjs": "function helper() { return 2; } exports.helper = helper;",
        "side.mjs": "console.log('side');",
        "common.cjs": 'const h = require("./helper.cjs"); module.exports = h;',
        "ignored.mjs": "export function ignored() {}",
        "static/assets/index-Ab12Cd34.mjs": "export function bundle() {}",
        "empty.mjs": "\n",
        "bad.cjs": "function broken( {",
        "notes.txt": "not source",
        ".gitignore": "ignored.mjs\n",
    }
    for name, text in files.items():
        path = source / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    if get_prepared_typescript_root() is None:
        if os.environ.get("LLM_WIKI_REQUIRE_NATIVE_DIAGNOSTICS") == "1":
            pytest.fail("prepared TypeScript helper is required in the owner lane")
        pytest.skip("prepared TypeScript helper required")
    api.bootstrap_wiki(str(source), "wiki")
    return source


@pytest.fixture
def helper():
    root = get_prepared_typescript_root()
    if root is None:
        if os.environ.get("LLM_WIKI_REQUIRE_NATIVE_DIAGNOSTICS") == "1":
            pytest.fail("prepared TypeScript helper is required in the owner lane")
        pytest.skip("prepared TypeScript helper required")
    return root


def query(paths, **options):
    return api.query_documentation(
        {"operation": "impact", "paths": paths, "source_policy": "discovery", **options},
        src_dir="source", wiki_dir="wiki",
    )


def test_module_extensions_match_broad_and_targeted_inventory(project, helper):
    paths = ["plain.js", "component.jsx", "main.mjs", "helper.mjs", "helper.cjs", "common.cjs"]
    broad = TypeScriptExtractor().extract(str(project), deep=True)
    targeted = TypeScriptExtractor().extract(str(project), source_files=paths, deep=True)
    assert set(paths).issubset(broad)
    for path in paths:
        assert targeted[path] == broad[path]
        assert targeted[path]["language"] == "javascript"
    assert targeted["plain.js"]["functions"][0]["name"] == "plain"
    assert targeted["helper.cjs"]["functions"][0]["name"] == "helper"
    result = query(paths)
    assert {m["path"] for m in result["matches"] if m["present"]} == set(paths)
    assert {m["extraction_state"] for m in result["matches"]} == {"extracted"}


def test_exact_esm_side_effect_and_commonjs_dependencies(project, helper):
    result = extraction_service.build_extract_payload(str(project), deep=True, paths=[
        "main.mjs", "helper.mjs", "helper.cjs", "side.mjs", "common.cjs",
    ])
    assert result.dependency_analysis is not None
    graph = result.dependency_analysis["graph"]
    assert set(graph["edges"]) == {
        ("main.mjs", "helper.mjs"), ("main.mjs", "side.mjs"), ("common.cjs", "helper.cjs"),
    }
    resolver = build_module_path_resolver(result.payload["inventory"])
    assert resolver.candidates("./helper.mjs", "main.mjs") == {"helper.mjs"}
    del result.payload["inventory"]["helper.mjs"]
    assert build_module_path_resolver(result.payload["inventory"]).candidates("./helper.mjs", "main.mjs") == set()
    entry_only = query(["main.mjs"], include_raw_evidence=True)
    assert "raw_evidence" in entry_only
    assert [r["path"] for r in entry_only["raw_evidence"]] == ["main.mjs"]
    assert entry_only["cost"]["full_inventory_performed"] is False


def test_dynamic_and_shadowed_require_are_explicit_without_invented_edges(project, helper):
    (project / "dynamic.cjs").write_text('''
function deferred() { return require("./helper.cjs"); }
function shadow(require) { return require("./helper.mjs"); }
const load = require;
require(target);
import("./helper.mjs");
''')
    inventory = TypeScriptExtractor().extract(str(project), deep=True, source_files=["dynamic.cjs", "helper.cjs", "helper.mjs"])
    graph = build_dependency_graph(inventory)
    assert graph["edges"] == [("dynamic.cjs", "helper.cjs")]
    assert graph["import_time_edges"] == []
    gaps = inventory["dynamic.cjs"]["import_gaps"]
    assert {g["reason"] for g in gaps} == {"shadowed-call-not-module-import", "indirect-require-unsupported"}
    assert {u["reason"] for u in graph["unresolved"]} == {"dynamic-import", "dynamic-require"}
    assert all(u["module"] == "" for u in graph["unresolved"])


def test_extensionless_collision_does_not_fabricate_edges():
    inventory = {path: {"language": "javascript", "functions": [], "classes": []} for path in ["main.mjs", "helper.mjs", "helper.cjs"]}
    inventory["main.mjs"]["imports"] = [{"module": "./helper", "name": "helper"}]
    inventory["helper.mjs"]["functions"] = [{"name": "helper"}]
    graph = build_dependency_graph(inventory)
    assert graph["edges"] == []
    assert graph["unresolved"][0]["kind"] == "ambiguous"


@pytest.mark.parametrize("binding", [
    "const require = () => null;",
    "if (false) { var require; }",
    "try {} catch (require) { require('./helper.mjs'); }",
    "const { value: require } = object;",
    "require = replacement;",
])
def test_local_require_bindings_never_claim_module_edges(project, helper, binding):
    (project / "bound.cjs").write_text(binding + ('' if 'catch' in binding else '\nrequire("./helper.mjs");'))
    inventory = TypeScriptExtractor().extract(str(project), source_files=["bound.cjs", "helper.mjs"], deep=True)
    assert build_dependency_graph(inventory)["edges"] == []
    assert inventory["bound.cjs"]["import_gaps"]


def test_path_outcomes_are_distinct_and_present_keeps_inventory_meaning(project, helper):
    paths = ["helper.mjs", "notes.txt", "ignored.mjs", "deleted.mjs", "bad.cjs", "empty.mjs", "static/assets/index-Ab12Cd34.mjs"]
    result = query(paths)
    outcomes = {m["path"]: m for m in result["matches"]}
    assert outcomes["helper.mjs"]["present"] is True
    for path in paths[1:]:
        assert outcomes[path]["present"] is False
    assert outcomes["notes.txt"]["extraction_state"] == "unsupported"
    assert outcomes["ignored.mjs"]["reason"] == "gitignore"
    assert outcomes["ignored.mjs"]["filesystem_state"] == "file"
    assert outcomes["deleted.mjs"]["filesystem_state"] == "missing"
    assert outcomes["bad.cjs"]["extraction_state"] == "failed"
    assert outcomes["bad.cjs"]["failure_scope"] == "file"
    assert outcomes["empty.mjs"]["extraction_state"] == "no-documentable-content"
    assert outcomes["static/assets/index-Ab12Cd34.mjs"]["reason"] == "generated-bundle"
    legacy = api.query_documentation({"operation": "impact", "paths": ["ignored.mjs"]}, src_dir="source", wiki_dir="wiki")
    assert legacy["matches"][0]["present"] is True
    assert "filesystem_state" not in legacy["matches"][0]


def test_missing_helper_and_batch_failure_are_attributable(project, monkeypatch):
    monkeypatch.setattr("llm_wiki_cli.extractors.ts_extractor.get_prepared_typescript_root", lambda *a: None)
    result = query(["helper.mjs", "notes.txt"])
    row = next(m for m in result["matches"] if m["path"] == "helper.mjs")
    assert row["extraction_state"] == "unavailable"
    assert row["reason"] == "helper-unavailable"
    with pytest.raises(api.WorkspaceStateError):
        api.query_documentation({"operation": "impact", "paths": ["helper.mjs"]}, src_dir="source", wiki_dir="wiki")


def test_batch_failure_is_not_reported_as_file_parse_failure(project, helper, monkeypatch):
    def fail(self, cmd, root):
        self.last_error = "extraction failed"
        return None
    monkeypatch.setattr(TypeScriptExtractor, "_run_node_extractor", fail)
    result = query(["helper.mjs", "helper.cjs"])
    assert {m["extraction_state"] for m in result["matches"]} == {"failed"}
    assert {m["failure_scope"] for m in result["matches"]} == {"extractor-batch"}
    assert {m["reason"] for m in result["matches"]} == {"extractor-batch-failed"}


def test_chunk_failure_preserves_success_and_unattempted_paths(project, helper, monkeypatch):
    from llm_wiki_cli.extractors import common
    original = TypeScriptExtractor._run_node_extractor
    calls = []
    def fail_second(self, cmd, root):
        calls.append(cmd)
        if len(calls) == 2:
            self.last_error = "extraction failed"
            return None
        return original(self, cmd, root)
    monkeypatch.setattr(common, "MAX_ONLY_FILES_ARG_CHARS", 11)
    monkeypatch.setattr(TypeScriptExtractor, "_run_node_extractor", fail_second)
    result = query(["helper.cjs", "helper.mjs", "main.mjs"])
    rows = {m["path"]: m for m in result["matches"]}
    assert rows["helper.cjs"]["present"] is True
    assert rows["helper.mjs"]["extraction_state"] == "failed"
    assert rows["main.mjs"]["extraction_state"] == "not-attempted"
    assert len(calls) == 2


def test_query_aborts_when_source_changes_during_diagnostic_read(project, helper, monkeypatch):
    original = TypeScriptExtractor.extract
    def changing(self, *args, **kwargs):
        result = original(self, *args, **kwargs)
        (project / "helper.mjs").write_text("export function helper() { return 9; }")
        return result
    monkeypatch.setattr(TypeScriptExtractor, "extract", changing)
    with pytest.raises(api.WorkspaceStateError):
        query(["helper.mjs"])


@pytest.mark.parametrize("suffix", ["mjs", "cjs"])
def test_module_edits_invalidate_captured_source(project, suffix):
    path = f"helper.{suffix}"
    snapshot = build_source_snapshot(project, only_files=[path], respect_discovery=True)
    assert source_snapshot_matches_current_files(snapshot)
    (project / path).write_text((project / path).read_text() + "\nconsole.log('changed');")
    assert not source_snapshot_matches_current_files(snapshot)
    current = build_source_snapshot(project, only_files=[path], respect_discovery=True)
    assert current.captured_content_hashes[path] != snapshot.captured_content_hashes[path]


@pytest.mark.parametrize("suffix", ["mjs", "cjs"])
def test_cached_module_edits_are_reextracted(project, helper, suffix):
    options = InventoryCacheOptions(enabled=True, cache_dir="inventory-cache")
    path = f"helper.{suffix}"
    def read():
        return extraction_service.get_inventory_result(extraction_service.InventoryRequest(
            src_dir=project, deep=True, cache_options=options,
        ))
    first = read()
    warm = read()
    assert warm.cache_stats is not None and warm.cache_stats.hits > 0
    (project / path).write_text((project / path).read_text() + "\nfunction added() {}")
    changed = read()
    assert changed.cache_stats is not None and changed.cache_stats.changed == 1
    assert changed.inventory[path] != first.inventory[path]
    assert "added" in {f["name"] for f in changed.inventory[path]["functions"]}


def test_discovery_keeps_bundle_and_worktree_out_of_inventory(project, helper):
    worktree = project / ".claude/worktrees/copy/main.cjs"
    worktree.parent.mkdir(parents=True)
    worktree.write_text("function hidden() {}")
    result = query(["static/assets/index-Ab12Cd34.mjs", ".claude/worktrees/copy/main.cjs"])
    assert {m["reason"] for m in result["matches"]} == {"generated-bundle", "worktree"}
    assert all(not m["present"] and m["filesystem_state"] == "file" for m in result["matches"])
    legacy = TypeScriptExtractor().extract(str(project), only_files=["static/assets/index-Ab12Cd34.mjs"])
    assert "static/assets/index-Ab12Cd34.mjs" in legacy


def test_profile_exclusion_is_not_a_missing_file(project, helper):
    (project / ".llm-wiki").mkdir()
    (project / ".llm-wiki/source-selection.json").write_text(json.dumps({
        "schema_version": "llm-wiki-source-selection/v1", "include": ["helper.mjs"], "exclude": [],
    }))
    shutil.rmtree("wiki")
    api.bootstrap_wiki(str(project), "wiki")
    result = query(["helper.mjs", "helper.cjs"])
    excluded = next(m for m in result["matches"] if m["path"] == "helper.cjs")
    assert excluded["selection_state"] == "excluded"
    assert excluded["filesystem_state"] == "unknown"
    assert excluded["reason"] == "source-selection"


def test_invalid_policy_and_symlinks_fail_before_extraction(project, monkeypatch):
    monkeypatch.setattr(api, "build_live_documentation_query_service", lambda **kw: pytest.fail("invalid request reached extraction"))
    with pytest.raises(api.InvalidRequestError):
        query(["helper.mjs"], source_policy="invalid")
    (project / "link.mjs").symlink_to(project / "helper.mjs")
    with pytest.raises(api.InvalidRequestError):
        query(["link.mjs"])


def test_bounds_and_cli_mcp_match_api(project, helper):
    paths = ["helper.mjs", "helper.cjs", "deleted.mjs"]
    request = {"operation": "impact", "paths": paths, "source_policy": "discovery", "limit": 1}
    result = query(paths, limit=1)
    assert result["bounds"]["matches"] == {"total": 3, "returned": 1, "truncated": True}
    assert result["cost"]["supplied_paths"] == 3
    (Path.cwd() / "request.json").write_text(json.dumps(request))
    cli = subprocess.run([sys.executable, "-m", "llm_wiki_cli.cli", "query", "--request", "request.json", "--src-dir", "source", "--wiki-dir", "wiki"], text=True, capture_output=True)
    assert cli.returncode == 0, cli.stderr
    assert json.loads(cli.stdout) == result
    service = mcp_server.McpWikiService(src_dir="source", wiki_dir="wiki")
    assert service.query_documentation(request) == result
