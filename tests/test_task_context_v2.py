"""Scoped task contracts cannot inherit whole-artifact validation claims."""

import pytest

from llm_wiki_cli import api
from llm_wiki_cli.services import context_packet
from llm_wiki_cli.services.context_session import build_delta, apply_task_delta
from llm_wiki_cli.services.knowledge_artifacts import commit_knowledge_artifacts
from llm_wiki_cli.services.task_contract import TASK_REQUEST_SCHEMA_V2, TASK_RESULT_SCHEMA_V2
from llm_wiki_cli.services.workflow_profile import canonical_json, content_id
from tests.native_workflow.oracles import source_facts
from tests.test_knowledge_storage_artifacts import migrate_plan


@pytest.fixture
def project(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "app.py").write_text("def limit(value: int = 3, *, force: bool = False) -> int:\n    return value\n\ndef caller():\n    return limit()\n")
    return tmp_path


def request(**options):
    return {"schema_version": TASK_REQUEST_SCHEMA_V2,
            "requirements": [{"id": "contract", "facet": "source-contract", "selector": "app.py:limit"}], **options}


def test_live_source_receipt_uses_existing_independent_contract_observer(project, monkeypatch):
    monkeypatch.setattr(context_packet, "_wiki_anchor", lambda *a, **kw: pytest.fail("scoped task hashed the whole wiki"))
    req = request(options={"knowledge_mode": "off"})
    result = api.build_task_context(req)
    payload = api.validate_task_context(result.rendered, req)
    assert payload["schema_version"] == TASK_RESULT_SCHEMA_V2
    assert payload["packet"] is None and payload["state"] == "covered"
    independent = source_facts(project / "app.py")["declarations"][0]
    assert payload["facts"][0]["observation"]["contract"]["params"] == independent["params"]
    assert payload["source_capture"]["inputs"]
    assert payload["storage"]["status"] == "off"
    assert api.build_task_context(req).rendered == result.rendered


def test_native_scoped_fact_and_md_binding_without_whole_wiki_walk(project, monkeypatch):
    wiki = project / "wiki"
    wiki.mkdir()
    _, _, plan = migrate_plan(wiki)
    commit_knowledge_artifacts(plan)
    monkeypatch.setattr(context_packet, "_wiki_anchor", lambda *a, **kw: pytest.fail("whole-wiki anchor"))
    req = {"schema_version": TASK_REQUEST_SCHEMA_V2, "options": {"read_scope": "snapshot", "knowledge_mode": "required"},
           "requirements": [{"id": "concept", "facet": "concept", "selector": "entities/AccountService.md"}]}
    result = api.build_task_context(req, wiki_dir="wiki")
    data = api.validate_task_context(result.rendered, req)
    assert data["coverage"][0]["satisfied"]
    assert data["storage"]["status"] == "scoped" and data["storage"]["whole_store_validated"] is False
    assert data["storage"]["read_bytes"] <= 8_388_608
    assert data["facts"][0]["qualification"]["native"]["availability"] == "scoped"
    assert data["packet"] is None


@pytest.mark.parametrize("mutation", ["full-claim", "wrong-selector", "covered", "cost", "source-receipt"])
def test_rehashed_false_claims_are_rejected_independently(project, mutation):
    req = request(options={"knowledge_mode": "off"})
    payload = api.build_task_context(req).to_payload()
    if mutation == "full-claim":
        payload["storage"]["whole_store_validated"] = True
    elif mutation == "wrong-selector":
        payload["facts"][0]["observation"]["path"] = "other.py"
        fact = payload["facts"][0]
        old_id = fact["fact_id"]
        fact["fact_id"] = content_id("llm-wiki-task-fact/v1", {k: v for k, v in fact.items() if k != "fact_id"})
        for item in payload["coverage"]:
            item["fact_ids"] = [fact["fact_id"] if x == old_id else x for x in item["fact_ids"]]
    elif mutation == "covered":
        payload["coverage"][0].update(state="missing", satisfied=False, fact_ids=[])
        payload["omissions"] = payload["coverage"]
    elif mutation == "cost":
        payload["storage"]["read_bytes"] = 0.0
    else:
        payload["source_capture"]["inputs"][0]["content_hash"] = "sha256:" + "0" * 64
    payload["result_id"] = content_id(TASK_RESULT_SCHEMA_V2, {k: v for k, v in payload.items() if k != "result_id"})
    with pytest.raises(api.InvalidRequestError):
        api.validate_task_context(canonical_json(payload).decode(), req)


def test_scoped_session_revalidates_and_supports_schema_bound_deltas(project, monkeypatch):
    req = request(options={"knowledge_mode": "off"})
    session = api.open_context_session()
    first = session.read(req)
    assert first.context is not None
    monkeypatch.setattr(context_packet, "_wiki_anchor", lambda *a, **kw: pytest.fail("whole wiki on scoped session"))
    warm = session.read(req, if_result_id=first.result_id)
    assert warm.state == "unchanged" and warm.metadata()["reuse"]["rendering"]
    path = project / "app.py"
    path.write_text(path.read_text().replace("= 3", "= 4"))
    second = session.read(req, if_result_id=first.result_id, delta=True)
    fresh = api.build_task_context(req)
    if second.delta is not None:
        restored = api.apply_task_delta(first.context.rendered, second.delta, req)
        assert restored.rendered == fresh.rendered
    else:
        assert second.context is not None
        assert second.context.rendered == fresh.rendered
    delta = build_delta(first.context, fresh)
    assert delta["schema_version"] == "llm-wiki-task-delta/v2"
    assert apply_task_delta(first.context.rendered, delta, req).rendered == fresh.rendered
    wrong = {**delta, "schema_version": "llm-wiki-task-delta/v1"}
    with pytest.raises(ValueError):
        apply_task_delta(first.context.rendered, wrong, req)


def test_native_session_checks_consumed_objects_and_cold_equivalence(project):
    wiki = project / "wiki"
    wiki.mkdir()
    _, _, plan = migrate_plan(wiki)
    commit_knowledge_artifacts(plan)
    req = {"schema_version": TASK_REQUEST_SCHEMA_V2, "options": {"read_scope": "snapshot", "knowledge_mode": "required"},
           "requirements": [{"id": "concept", "facet": "concept", "selector": "entities/AccountService.md"}]}
    session = api.open_context_session(wiki_dir="wiki")
    first = session.read(req)
    assert first.context is not None
    warm = session.read(req, if_result_id=first.result_id)
    assert warm.state == "unchanged" and warm.metadata()["reuse"]["rendering"]
    cold = session.read(req, reuse=False)
    assert cold.context is not None
    assert cold.context.rendered == api.build_task_context(req, wiki_dir="wiki").rendered
    touched = next(i["path"] for i in first.context.to_payload()["storage"]["inputs"] if "/objects/" in i["path"])
    (wiki / touched).write_bytes(b"{}\n")
    with pytest.raises((ValueError, api.LlmWikiApiError)):
        session.read(req, if_result_id=first.result_id)


def test_missing_native_does_not_mask_required_mode_or_create_reusable_absence(project):
    req = request()
    session = api.open_context_session()
    first = session.read(req)
    assert first.context is not None
    assert first.context.to_payload()["storage"]["status"] == "unavailable"
    next_read = session.read(req)
    assert not next_read.metadata()["reuse"]["rendering"]
    with pytest.raises(api.WorkspaceStateError):
        api.build_task_context(request(options={"knowledge_mode": "required"}))


def test_tiny_output_budget_keeps_v2_error_schema(project):
    result = api.build_task_context(request(options={"knowledge_mode": "off", "budget_tokens": 1}))
    assert not result.ok and result.to_payload()["schema_version"] == TASK_RESULT_SCHEMA_V2
    assert "facts" not in result.to_payload()


def test_v2_python_cli_and_mcp_preserve_the_same_canonical_response(project, monkeypatch, capsys):
    import io
    import json
    import sys
    from llm_wiki_cli import cli
    from llm_wiki_cli.services.mcp_server import McpWikiService
    req = request(options={"knowledge_mode": "off"})
    expected = api.build_task_context(req).rendered
    assert McpWikiService().build_task_context(req) == expected
    monkeypatch.setattr(sys, "argv", ["llm-wiki", "task-context", "--request", "-"])
    monkeypatch.setattr(sys, "stdin", io.StringIO(json.dumps(req)))
    cli.main()
    assert capsys.readouterr().out == expected
