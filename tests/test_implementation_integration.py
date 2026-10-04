"""Independent structural/executable observations through real persisted reads."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from llm_wiki_cli import api, cli
from llm_wiki_cli.services.knowledge_model import knowledge_index_to_payload
from llm_wiki_cli.services.knowledge_loader import load_knowledge_state
from llm_wiki_cli.services.knowledge_storage_lifecycle import migrate_knowledge_storage
from llm_wiki_cli.services.mcp_server import McpWikiService
from tests.developer_value.fixtures import POLICY_SOURCE

LOCATOR = "llm-wiki://entities/Batch"
SOURCE = POLICY_SOURCE + '\ndef unaffected() -> int:\n    return 42\n'


def _bytes(root):
    return {p.relative_to(root).as_posix(): p.read_bytes() for p in root.rglob("*") if p.is_file()}


def _concept(value):
    assert value["concept"] is not None
    assert value["concept"]["concept"] is not None
    return value["concept"]["concept"]


def _project(tmp_path, monkeypatch, capsys, storage="flat-v1"):
    monkeypatch.chdir(tmp_path)
    source = tmp_path / "src"
    source.mkdir()
    path = source / "policy.py"
    path.write_text(SOURCE)
    api.bootstrap_wiki("src", "wiki")
    capsys.readouterr()
    if storage != "flat-v1":
        migrate_knowledge_storage(Path("wiki"), to=storage, recovery_dir=Path("recovery"))
    return path, tmp_path / "wiki"


@pytest.mark.parametrize("storage", ["flat-v1", "sharded-v2", "packed-v3", "packed-v3-deflate", "packed-v4", "packed-v4-deflate"])
def test_persisted_slice_change_is_independent_of_structural_freshness(
    tmp_path, monkeypatch, capsys, storage,
):
    path, wiki = _project(tmp_path, monkeypatch, capsys, storage)
    loaded = load_knowledge_state(wiki)
    assert loaded.knowledge is not None
    payload = knowledge_index_to_payload(loaded.knowledge)
    record = next(c for c in payload["concepts"] if c["locator"] == LOCATOR)
    assert record["extensions"]["llm-wiki/implementation"]["scope"] == "class"
    before = _bytes(wiki)
    snapshot = _concept(api.inspect_concept(LOCATOR, src_dir="src", wiki_dir="wiki"))
    assert snapshot["implementation"]["state"] == "unavailable"
    assert snapshot["implementation"]["live_comparison_performed"] is False
    path.write_text(SOURCE.replace("values[:limit]", "values[:limit - 1]"))
    live = _concept(api.inspect_concept(LOCATOR, src_dir="src", wiki_dir="wiki", live=True))
    assert live["freshness"]["state"] == "nonsemantic-source-change"
    assert live["implementation"]["state"] == "changed"
    assert live["implementation"]["scope"] == "class"
    assert live["implementation"]["source_changed"] is True
    assert live["implementation"]["documentation_changed"] is False
    assert live["implementation"]["limitations"]
    mcp = McpWikiService(src_dir="src", wiki_dir="wiki")
    assert _concept(mcp.inspect_concept(LOCATOR, live=True))["implementation"] == live["implementation"]
    selected = api.query_documentation({"operation": "impact", "paths": ["policy.py"]}, src_dir="src", wiki_dir="wiki")
    assert "concepts" in selected and "knowledge" in selected
    selected_class = next(c for c in selected["concepts"] if c["locator"] == LOCATOR)
    assert selected_class["implementation"]["state"] == "changed"
    assert selected_class["implementation"]["analysis_scope"] == "selected-source"
    assert selected["knowledge"]["freshness_evaluated"] is False
    assert _bytes(wiki) == before


@pytest.mark.parametrize("edit,implementation,structural,documentation", [
    (lambda s: "# shifted comment\n" + s, "unchanged", "nonsemantic-source-change", False),
    (lambda s: s.replace("permitted batch limit", "documented batch ceiling"), "unchanged", "nonsemantic-source-change", True),
    (lambda s: s.replace("limit: int = 3", "limit: int = 4"), "changed", "source-changed", False),
])
def test_source_documentation_defaults_keep_separate_meanings(
    tmp_path, monkeypatch, capsys, edit, implementation, structural, documentation,
):
    path, _ = _project(tmp_path, monkeypatch, capsys)
    path.write_text(edit(SOURCE))
    live = _concept(api.inspect_concept(LOCATOR, src_dir="src", wiki_dir="wiki", live=True))
    assert live["freshness"]["state"] == structural
    assert live["implementation"]["state"] == implementation
    assert live["implementation"]["documentation_changed"] is documentation


def test_scoped_task_compares_callable_without_changing_unrelated_sibling(
    tmp_path, monkeypatch, capsys,
):
    path, wiki = _project(tmp_path, monkeypatch, capsys, "sharded-v2")
    path.write_text(SOURCE.replace("values[:limit]", "values[:limit - 1]"))
    request = {"schema_version": "llm-wiki-task-request/v2", "text": "Inspect scoped changes.",
        "requirements": [
            {"id": "body", "facet": "source-contract", "selector": "policy.py:Batch.cap#1"},
            {"id": "sibling", "facet": "source-contract", "selector": "policy.py:unaffected#1"},
            {"id": "module", "facet": "concept", "selector": "llm-wiki://modules/policy"},
        ]}
    before = _bytes(wiki)
    result = api.build_task_context(request, src_dir="src", wiki_dir="wiki").to_payload()
    facts = {f["selector"]: f for f in result["facts"]}
    assert facts["policy.py:Batch.cap#1"]["observation"]["implementation"]["state"] == "changed"
    sibling = facts["policy.py:unaffected#1"]["observation"]["implementation"]
    assert sibling["state"] == "unchanged" and sibling["source_changed"] is True
    module = facts["llm-wiki://modules/policy"]["observation"]["concept"]
    assert module["implementation"]["state"] == "changed"
    assert module["implementation"]["scope"] == "module"
    assert result["storage"]["whole_store_validated"] is False
    assert _bytes(wiki) == before


def test_cli_snapshot_never_claims_executable_unchanged(tmp_path, monkeypatch, capsys):
    _project(tmp_path, monkeypatch, capsys)
    request = tmp_path / "query.json"
    request.write_text(json.dumps({"operation": "concept", "value": LOCATOR}))
    monkeypatch.setattr("sys.argv", ["llm-wiki", "query", "--request", str(request), "--src-dir", "src", "--wiki-dir", "wiki"])
    cli.main()
    result = json.loads(capsys.readouterr().out)
    assert result["concept"]["implementation"]["state"] == "unavailable"
    assert result["concept"]["implementation"]["live_comparison_performed"] is False


def test_module_global_is_changed_without_relabeling_callable_syntax(
    tmp_path, monkeypatch, capsys,
):
    monkeypatch.chdir(tmp_path)
    Path("src").mkdir()
    path = Path("src/globals.py")
    original = "DEFAULT_LIMIT = 3\n\ndef configured_limit() -> int:\n    return DEFAULT_LIMIT\n"
    path.write_text(original)
    api.bootstrap_wiki("src", "wiki")
    capsys.readouterr()
    migrate_knowledge_storage(Path("wiki"), to="packed-v4-deflate", recovery_dir=Path("recovery"))
    path.write_text(original.replace("DEFAULT_LIMIT = 3", "DEFAULT_LIMIT = 4"))
    request = {"schema_version": "llm-wiki-task-request/v2", "requirements": [
        {"id": "callable", "facet": "source-contract", "selector": "globals.py:configured_limit#1"},
        {"id": "module", "facet": "concept", "selector": "llm-wiki://modules/globals"},
    ]}
    result = api.build_task_context(request, src_dir="src", wiki_dir="wiki").to_payload()
    facts = {f["selector"]: f for f in result["facts"]}
    callable_comparison = facts["globals.py:configured_limit#1"]["observation"]["implementation"]
    assert callable_comparison["state"] == "unchanged"
    assert callable_comparison["source_changed"] is True
    module = facts["llm-wiki://modules/globals"]["observation"]["concept"]["implementation"]
    assert module["state"] == "changed" and module["scope"] == "module"
    assert callable_comparison["limitations"] == module["limitations"]


def test_duplicate_parent_method_comparison_keeps_exact_occurrence(
    tmp_path, monkeypatch, capsys,
):
    monkeypatch.chdir(tmp_path)
    Path("src").mkdir()
    path = Path("src/scope.py")
    original = "class Repeated:\n    def touch(self):\n        return 1\n\nclass Repeated:\n    def touch(self):\n        return 2\n"
    path.write_text(original)
    api.bootstrap_wiki("src", "wiki")
    capsys.readouterr()
    migrate_knowledge_storage(Path("wiki"), to="sharded-v2", recovery_dir=Path("recovery"))
    path.write_text(original.replace("return 2", "return 3"))
    request = {"schema_version": "llm-wiki-task-request/v2", "requirements": [
        {"id": "first", "facet": "source-contract", "selector": "scope.py:Repeated.touch#1"},
        {"id": "second", "facet": "source-contract", "selector": "scope.py:Repeated.touch#2"},
        {"id": "module", "facet": "concept", "selector": "llm-wiki://modules/scope"},
    ]}
    result = api.build_task_context(request, src_dir="src", wiki_dir="wiki").to_payload()
    facts = {f["selector"]: f for f in result["facts"]}
    assert facts["scope.py:Repeated.touch#1"]["observation"]["implementation"]["state"] == "unchanged"
    assert facts["scope.py:Repeated.touch#2"]["observation"]["implementation"]["state"] == "changed"


@pytest.mark.parametrize("schema", ["llm-wiki-task-request/v1", "llm-wiki-task-request/v2"])
def test_native_off_does_not_request_implementation_capture(tmp_path, monkeypatch, schema):
    from llm_wiki_cli.extractors import python_extractor

    monkeypatch.chdir(tmp_path)
    Path("src").mkdir()
    Path("src/policy.py").write_text(SOURCE)
    Path("wiki").mkdir()
    monkeypatch.setattr(python_extractor, "capture_implementation", lambda *a, **kw: pytest.fail("native-off captured implementation"))
    request = {"schema_version": schema, "options": {"knowledge_mode": "off"},
        "requirements": [{"id": "source", "facet": "source-contract", "selector": "policy.py:Batch.cap#1"}]}
    result = api.build_task_context(request, src_dir="src", wiki_dir="wiki").to_payload()
    assert result["coverage"][0]["satisfied"] is True
    assert "implementation" not in result["facts"][0]["observation"]
    assert not list(Path("wiki").iterdir())


def test_live_missing_source_is_distinct_from_selected_uncaptured_source(
    tmp_path, monkeypatch, capsys,
):
    path, wiki = _project(tmp_path, monkeypatch, capsys)
    before = _bytes(wiki)
    path.unlink()
    concept = _concept(api.inspect_concept(LOCATOR, src_dir="src", wiki_dir="wiki", live=True))
    assert concept["freshness"]["state"] == "source-missing"
    assert concept["implementation"]["state"] == "unavailable"
    assert concept["implementation"]["reason"] == "missing-source"
    assert concept["implementation"]["live_comparison_performed"] is False
    assert _bytes(wiki) == before


@pytest.mark.parametrize("schema", ["llm-wiki-task-request/v1", "llm-wiki-task-request/v2"])
def test_source_contract_only_has_committed_comparison_and_capture_binding(
    tmp_path, monkeypatch, capsys, schema,
):
    path, _ = _project(tmp_path, monkeypatch, capsys, "sharded-v2")
    path.write_text(SOURCE.replace("values[:limit]", "values[:limit - 1]"))
    request = {"schema_version": schema, "requirements": [
        {"id": "body", "facet": "source-contract", "selector": "policy.py:Batch.cap#1"}]}
    context = api.build_task_context(request, src_dir="src", wiki_dir="wiki")
    result = context.to_payload()
    comparison = result["facts"][0]["observation"]["implementation"]
    assert comparison["state"] == "changed"
    assert result["implementation_capture"]["analysis_compatibility_hash"] == comparison["live"]["producer"]["analysis_compatibility_hash"]
    api.validate_task_context(context.rendered, request)


@pytest.mark.parametrize("schema", ["llm-wiki-task-request/v1", "llm-wiki-task-request/v2"])
@pytest.mark.parametrize("mutation", ["extra-field", "wrong-coordinate", "wrong-source", "false-unchanged"])
def test_rehashed_task_payload_cannot_requalify_implementation(
    tmp_path, monkeypatch, capsys, schema, mutation,
):
    from llm_wiki_cli.services.workflow_profile import canonical_json, content_id

    path, _ = _project(tmp_path, monkeypatch, capsys, "sharded-v2")
    path.write_text(SOURCE.replace("values[:limit]", "values[:limit - 1]"))
    request = {"schema_version": schema, "requirements": [
        {"id": "body", "facet": "source-contract", "selector": "policy.py:Batch.cap#1"}]}
    result = api.build_task_context(request, src_dir="src", wiki_dir="wiki").to_payload()
    fact = result["facts"][0]
    before = fact["fact_id"]
    comparison = fact["observation"]["implementation"]
    if mutation == "extra-field":
        comparison["runtime_verified"] = True
    elif mutation == "wrong-coordinate":
        comparison["coordinate"]["occurrence"] = 2
    elif mutation == "wrong-source":
        comparison["live"]["source_hash"] = "sha256:" + "f" * 64
    else:
        comparison.update(state="unchanged", reason="matching-executable-syntax")
    fact["fact_id"] = content_id("llm-wiki-task-fact/v1", {k: v for k, v in fact.items() if k != "fact_id"})
    for item in result["coverage"]:
        item["fact_ids"] = [fact["fact_id"] if value == before else value for value in item["fact_ids"]]
    result["accounting"]["used_tokens"] = result["accounting"]["budget_tokens"]
    result["result_id"] = content_id(result["schema_version"], {k: v for k, v in result.items() if k != "result_id"})
    with pytest.raises(api.InvalidRequestError):
        api.validate_task_context(canonical_json(result).decode("utf-8"), request)


@pytest.mark.parametrize("schema", ["llm-wiki-task-request/v1", "llm-wiki-task-request/v2"])
def test_rehashed_snapshot_cannot_claim_a_live_implementation_verdict(
    tmp_path, monkeypatch, capsys, schema,
):
    from copy import deepcopy
    from llm_wiki_cli.services.workflow_profile import canonical_json, content_id

    _project(tmp_path, monkeypatch, capsys, "sharded-v2")
    request = {"schema_version": schema, "options": {"read_scope": "snapshot", "knowledge_mode": "required"},
        "requirements": [{"id": "concept", "facet": "concept", "selector": LOCATOR}]}
    result = api.build_task_context(request, src_dir="src", wiki_dir="wiki").to_payload()
    fact = result["facts"][0]
    comparison = fact["observation"]["concept"]["implementation"]
    assert comparison["state"] == "unavailable"
    assert "implementation_capture" not in result
    old = fact["fact_id"]
    comparison.update(state="unchanged", reason="matching-executable-syntax", analysis_scope="full-inventory",
        live_comparison_performed=True, source_changed=False, documentation_changed=False, live=deepcopy(comparison["recorded"]))
    fact["fact_id"] = content_id("llm-wiki-task-fact/v1", {k: v for k, v in fact.items() if k != "fact_id"})
    for item in result["coverage"]:
        item["fact_ids"] = [fact["fact_id"] if value == old else value for value in item["fact_ids"]]
    result["accounting"]["used_tokens"] = result["accounting"]["budget_tokens"]
    result["result_id"] = content_id(result["schema_version"], {k: v for k, v in result.items() if k != "result_id"})
    with pytest.raises(api.InvalidRequestError):
        api.validate_task_context(canonical_json(result).decode("utf-8"), request)


@pytest.mark.parametrize("schema", ["llm-wiki-task-request/v1", "llm-wiki-task-request/v2"])
@pytest.mark.parametrize("mutation", ["native-owner", "declaration-scope"])
def test_rehashed_task_cannot_substitute_same_file_owner_or_declaration_kind(
    tmp_path, monkeypatch, capsys, schema, mutation,
):
    from llm_wiki_cli.services.workflow_profile import canonical_json, content_id

    _project(tmp_path, monkeypatch, capsys, "sharded-v2")
    request = {"schema_version": schema, "anchors": [{"kind": "source", "value": "policy.py"}],
        "requirements": [{"id": "target", "facet": "concept" if mutation == "native-owner" else "source-contract",
                          "selector": LOCATOR if mutation == "native-owner" else "policy.py:Batch.cap#1"}]}
    result = api.build_task_context(request, src_dir="src", wiki_dir="wiki").to_payload()
    fact = next(f for f in result["facts"] if f["facet"] == ("concept" if mutation == "native-owner" else "source-contract"))
    comparison = fact["observation"]["concept"]["implementation"] if mutation == "native-owner" else fact["observation"]["implementation"]
    assert comparison["state"] == "unchanged"
    old = fact["fact_id"]
    if mutation == "native-owner":
        comparison["coordinate"]["qualified_owner"] = "Other"
        for key in ("recorded", "live"):
            comparison[key]["coordinate"]["qualified_owner"] = "Other"
    else:
        comparison["scope"] = "class"
        for key in ("recorded", "live"):
            comparison[key]["scope"] = "class"
    fact["fact_id"] = content_id("llm-wiki-task-fact/v1", {k: v for k, v in fact.items() if k != "fact_id"})
    for item in result["coverage"]:
        item["fact_ids"] = [fact["fact_id"] if value == old else value for value in item["fact_ids"]]
    result["accounting"]["used_tokens"] = result["accounting"]["budget_tokens"]
    result["result_id"] = content_id(result["schema_version"], {k: v for k, v in result.items() if k != "result_id"})
    with pytest.raises(api.InvalidRequestError):
        api.validate_task_context(canonical_json(result).decode("utf-8"), request)
