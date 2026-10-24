"""Skipped reconciliation must name its evidence without widening discovery."""

from copy import deepcopy
import json
import subprocess

import pytest

from llm_wiki_cli.services import dependencies, lint_service
from llm_wiki_cli.services.source_snapshot import build_source_snapshot
from tests.test_source_snapshot import _write_owned_llm_wiki_package


def _write(root, name, content):
    path = root / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)
    return path


def _snapshot(root):
    _write(root, ".llm-wiki/source-selection.json", json.dumps({
        "schema_version": "llm-wiki-source-selection/v1", "include": ["src"], "exclude": [],
    }))
    return build_source_snapshot(root)


def _owned(root):
    package = _write_owned_llm_wiki_package(root)
    (package / "extractors/ts_scripts/package.json").write_text('{"dependencies":{"ts-morph":"1"}}')
    (package / "extractors/rust_scripts/Cargo.toml").write_text('[dependencies]\nserde="1"\n')
    return package


@pytest.mark.parametrize("language,scope,manifest", [
    ("typescript", "src/llm_wiki_cli/extractors/ts_scripts", "package.json"),
    ("rust", "", "Cargo.toml"),
])
def test_owned_helper_is_intentionally_excluded_with_exact_manifest(tmp_path, language, scope, manifest):
    _owned(tmp_path)
    snapshot = _snapshot(tmp_path)
    before = deepcopy(snapshot.all_source_paths)
    row = dependencies.describe_unscanned_scopes(tmp_path, language, [scope], snapshot)[0]
    assert row["reason"] == "owned-helper-excluded"
    assert row["owner"] == "llm-wiki-helper"
    assert len(row["manifests"]) == 1 and row["manifests"][0].endswith(manifest)
    assert "preparation" in row["hint"].lower() and "not" in row["hint"].lower()
    assert snapshot.all_source_paths == before
    assert not any(p.endswith(("extract.js", "main.rs")) for p in before)


def test_missing_owned_source_is_not_called_an_intentional_exclusion(tmp_path):
    package = _owned(tmp_path)
    (package / "extractors/rust_scripts/src/main.rs").unlink()
    row = dependencies.describe_unscanned_scopes(tmp_path, "rust", [""], _snapshot(tmp_path))[0]
    assert row["reason"] == "owned-helper-source-missing"
    assert row["sources"] == ["src/llm_wiki_cli/extractors/rust_scripts/src/main.rs"]


def test_focused_owned_helper_root_keeps_the_same_ownership_guard(tmp_path):
    package = _owned(tmp_path)
    helper = package / "extractors/ts_scripts"
    row = dependencies.describe_unscanned_scopes(helper, "typescript", [""], build_source_snapshot(helper))[0]
    assert row["manifests"] == ["package.json"]
    assert row["sources"] == ["extract.js"]
    assert row["reason"] == "owned-helper-excluded"


def test_missing_explicit_source_and_unsupported_inputs_are_separate(tmp_path):
    _write(tmp_path, "src/ui/package.json", '{"dependencies":{"example":"1"}}')
    _write(tmp_path, "src/ui/tsconfig.json", '{"files":["missing.ts"]}')
    row = dependencies.describe_unscanned_scopes(tmp_path, "typescript", ["src/ui"], _snapshot(tmp_path))[0]
    assert row["reason"] == "declared-source-missing"
    assert row["sources"] == ["src/ui/missing.ts"]
    (tmp_path / "src/ui/tsconfig.json").unlink()
    _write(tmp_path, "src/ui/View.java", "class View {}")
    row = dependencies.describe_unscanned_scopes(tmp_path, "typescript", ["src/ui"], _snapshot(tmp_path))[0]
    assert row["reason"] == "unsupported-inputs-present"


def test_similar_consumer_suffix_is_not_claimed_as_owned_or_unprepared(tmp_path):
    scope = "src/consumer/llm_wiki_cli/extractors/ts_scripts"
    _write(tmp_path, scope + "/package.json", '{"dependencies":{"example":"1"}}')
    _write(tmp_path, scope + "/extract.js", "export const value = 1;")
    row = dependencies.describe_unscanned_scopes(tmp_path, "typescript", [scope], _snapshot(tmp_path))[0]
    assert row["owner"] == "unknown"
    assert row["reason"] == "supported-source-not-extracted"
    assert "preparation" in row["hint"].lower() and "not" in row["hint"].lower()


def test_unknown_source_ownership_remains_unknown_and_report_is_read_only(tmp_path, monkeypatch):
    _write(tmp_path, "src/empty/package.json", '{"dependencies":{"example":"1"}}')
    snapshot = _snapshot(tmp_path)
    before = {p: p.read_bytes() for p in tmp_path.rglob("*") if p.is_file()}
    def reject(*args, **kwargs):
        pytest.fail("scope explanation must not invoke tools")
    monkeypatch.setattr(subprocess, "run", reject)
    row = dependencies.describe_unscanned_scopes(tmp_path, "typescript", ["src/empty"], snapshot)[0]
    assert row["reason"] == "source-scope-unavailable" and row["owner"] == "unknown"
    assert before == {p: p.read_bytes() for p in tmp_path.rglob("*") if p.is_file()}


def test_mixed_language_wide_scope_retains_known_subset_and_unknown_owner(tmp_path):
    _owned(tmp_path)
    _write(tmp_path, "src/consumer/Cargo.toml", '[dependencies]\nexample="1"\n')
    snapshot = _snapshot(tmp_path)
    rows = dependencies.describe_unscanned_scopes(tmp_path, "rust", [""], snapshot)
    assert len(rows) == 1 and len(rows[0]["manifests"]) == 2
    assert rows[0]["reason"] == "mixed-source-scope" and rows[0]["owner"] == "unknown"
    other = tmp_path / "other"
    other.mkdir()
    mismatch = dependencies.describe_unscanned_scopes(other, "rust", [""], snapshot)[0]
    assert mismatch["manifests"] == [] and mismatch["reason"] == "source-scope-unavailable"


def test_lint_skip_count_and_reconciliation_shapes_remain_unchanged(tmp_path):
    _owned(tmp_path)
    _write(tmp_path, "src/app.py", "VALUE = 1\n")
    wiki = tmp_path / "wiki"
    wiki.mkdir()
    (wiki / "dependencies.md").write_text("# Dependencies\n")
    snapshot = _snapshot(tmp_path)
    inventory = {"src/app.py": {"language": "python", "functions": [], "classes": [], "imports": []}}
    raw = dependencies.reconcile_dependencies(inventory, str(tmp_path), source_snapshot=snapshot)
    report = lint_service.LintReport(str(wiki), str(tmp_path))
    lint_service._check_dependency_coverage(report, wiki, inventory, str(tmp_path), snapshot)
    skipped = [d for d in report.diagnostics if d.category == "unscanned_manifest_scopes"]
    assert len(skipped) == 2
    assert all(d.path and d.path.endswith(("package.json", "Cargo.toml")) for d in skipped)
    assert all(d.reason_code == "owned-helper-excluded" for d in skipped)
    assert all("<none>" not in d.message for d in skipped)
    assert all(d.severity == "warning" for d in skipped) and report.passed
    assert dependencies.reconcile_dependencies(inventory, str(tmp_path), source_snapshot=snapshot) == raw
    assert raw["languages"]["rust"]["unscanned_scopes"] == [""]
    assert raw["languages"]["rust"]["unused"] == []
