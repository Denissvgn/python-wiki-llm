"""Scoped task contracts cannot inherit whole-artifact validation claims."""

import errno
import os
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

from llm_wiki_cli import api
from llm_wiki_cli.services import context_packet
from llm_wiki_cli.services.context_session import build_delta, apply_task_delta
from llm_wiki_cli.services.knowledge_artifacts import commit_knowledge_artifacts
from llm_wiki_cli.services.io import decode_markdown_bytes
from llm_wiki_cli.services.knowledge_storage import digest
from llm_wiki_cli.services.knowledge_storage import KnowledgeStorageError
from llm_wiki_cli.services.knowledge_storage_lifecycle import migrate_knowledge_storage
from llm_wiki_cli.services.storage_receipts import expand_storage_receipt
from llm_wiki_cli.services.task_compact import VIEW_REQUEST_SCHEMA
from llm_wiki_cli.services.task_contract import TASK_REQUEST_SCHEMA_V2, TASK_RESULT_SCHEMA_V2
from llm_wiki_cli.services.workflow_profile import canonical_json, content_id
from tests.native_workflow.oracles import source_facts
from tests.test_knowledge_storage_artifacts import migrate_plan
from tests.test_task_compact import reseal_canonical


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


def _newline_native_project(project, newline, storage_format, receipt="expanded-v1"):
    wiki = project / "wiki"
    wiki.mkdir()
    _, _, plan = migrate_plan(wiki)
    commit_knowledge_artifacts(plan)
    if storage_format == "packed-v3":
        migrate_knowledge_storage(wiki, to=storage_format, recovery_dir=project / "pack-recovery")
    page = wiki / "entities/AccountService.md"
    canonical = decode_markdown_bytes(page.read_bytes())
    page.write_bytes(canonical.replace("\n", newline).encode("utf-8"))
    req = {"schema_version": TASK_REQUEST_SCHEMA_V2,
           "options": {"read_scope": "snapshot", "knowledge_mode": "required"},
           "storage_options": {"selection": "required-facets-v1", "receipt": receipt},
           "requirements": [{"id": "concept", "facet": "concept", "selector": "entities/AccountService.md"}]}
    return wiki, page, req


@pytest.mark.parametrize("newline", ["\n", "\r\n", "\r"], ids=["LF", "CRLF", "CR"])
@pytest.mark.parametrize("storage_format", ["sharded-v2", "packed-v3"])
@pytest.mark.parametrize("receipt", ["expanded-v1", "compact-v1"])
def test_native_page_binding_preserves_raw_receipts_and_canonical_newlines(project, newline, storage_format, receipt):
    wiki, page, req = _newline_native_project(project, newline, storage_format, receipt)
    before = page.read_bytes()
    result = api.build_task_context(req, wiki_dir=str(wiki))
    data = api.validate_task_context(result.rendered, req)
    storage = expand_storage_receipt(data["storage"]) if receipt == "compact-v1" else data["storage"]
    consumed = next(item for item in storage["inputs"] if item["path"] == "entities/AccountService.md")
    assert consumed["hash"] == digest(before) and consumed["bytes"] == len(before)
    fact = data["facts"][0]
    canonical_hash = digest(decode_markdown_bytes(before).encode("utf-8"))
    assert fact["observation"]["concept"]["facets"]["semantics"]["page_hash"] == canonical_hash
    citation = fact["citations"][0]
    if newline == "\n":
        assert "page_binding" not in citation
    else:
        assert citation["page_binding"] == {"raw_content_hash": digest(before), "canonical_page_hash": canonical_hash}
    view_options = {"schema_version": VIEW_REQUEST_SCHEMA, "budget_tokens": 32000}
    compact = api.render_compact_task_context(result.rendered, req, view_options=view_options)
    restored = api.expand_compact_task_context(compact.rendered, result.rendered, req, view_options=view_options)
    assert restored["facts"] == data["facts"]
    assert page.read_bytes() == before


def test_native_page_binding_uses_established_non_utf8_markdown_decoding(project, capsys):
    source = project / "src"
    source.mkdir()
    (source / "app.py").write_bytes(b'"""Caf\xc3\xa9 documentation."""\ndef limit(value=3):\n    return value\n')
    wiki = project / "wiki"
    api.bootstrap_wiki(str(source), str(wiki))
    migrate_knowledge_storage(wiki, to="sharded-v2", recovery_dir=project / "storage-recovery")
    capsys.readouterr()
    page = wiki / "modules/app.md"
    canonical = decode_markdown_bytes(page.read_bytes())
    assert "Café" in canonical
    raw = canonical.encode("cp1252")
    with pytest.raises(UnicodeDecodeError):
        raw.decode("utf-8")
    page.write_bytes(raw)
    req = {"schema_version": TASK_REQUEST_SCHEMA_V2,
           "options": {"read_scope": "snapshot", "knowledge_mode": "required"},
           "requirements": [{"id": "concept", "facet": "concept", "selector": "modules/app.md"}]}
    result = api.build_task_context(req, wiki_dir=str(wiki))
    data = api.validate_task_context(result.rendered, req)
    citation = data["facts"][0]["citations"][0]
    assert citation["page_binding"] == {"raw_content_hash": digest(raw), "canonical_page_hash": digest(canonical.encode("utf-8"))}
    assert page.read_bytes() == raw


@pytest.mark.parametrize("mutation", ["raw", "canonical", "semantic", "receipt", "path", "missing", "duplicate"])
def test_rehashed_native_page_binding_tampering_is_rejected(project, mutation):
    wiki, _, req = _newline_native_project(project, "\r\n", "sharded-v2")
    data = api.build_task_context(req, wiki_dir=str(wiki)).to_payload()
    fact = data["facts"][0]
    citation = fact["citations"][0]
    false_hash = "sha256:" + "0" * 64
    if mutation == "raw":
        citation["page_binding"]["raw_content_hash"] = false_hash
    elif mutation == "canonical":
        citation["page_binding"]["canonical_page_hash"] = false_hash
    elif mutation == "semantic":
        fact["observation"]["concept"]["facets"]["semantics"]["page_hash"] = false_hash
    elif mutation == "receipt":
        next(item for item in data["storage"]["inputs"] if item["path"] == citation["path"])["hash"] = false_hash
    elif mutation == "path":
        citation["path"] = "entities/Other.md"
    elif mutation == "missing":
        del citation["page_binding"]
    else:
        fact["citations"].append(dict(citation))
    with pytest.raises(api.InvalidRequestError):
        api.validate_task_context(reseal_canonical(data), req)


@pytest.mark.parametrize("deny_write", [False, True])
def test_canonical_equivalent_newline_mutation_after_capture_still_refuses(project, monkeypatch, deny_write):
    from llm_wiki_cli.services import knowledge_storage_access

    wiki, page, req = _newline_native_project(project, "\n", "sharded-v2")
    if deny_write:
        original_write = Path.write_bytes

        def denied_write(target, content):
            if target == page:
                raise PermissionError(errno.EACCES, "simulated pinned input", str(target))
            return original_write(target, content)

        monkeypatch.setattr(Path, "write_bytes", denied_write)
        # Exercise only this test's Windows denial assertion; filesystem APIs
        # retain the actual host platform and the API performs real translation.
        monkeypatch.setattr(sys.modules[__name__], "os", SimpleNamespace(name="nt"))
    original = knowledge_storage_access.ScopedKnowledgeRead.finish
    changed = False
    prevented = False
    attempted = False

    def mutate_before_recheck(native):
        nonlocal changed, prevented, attempted
        before = page.read_bytes()
        attempted = True
        try:
            page.write_bytes(before.replace(b"\n", b"\r"))
        except PermissionError as denied:
            assert os.name == "nt" and denied.errno == errno.EACCES
            assert denied.filename == str(page) and page.read_bytes() == before
            prevented = True
            raise
        assert decode_markdown_bytes(page.read_bytes()) == decode_markdown_bytes(before)
        changed = True
        return original(native)

    monkeypatch.setattr(knowledge_storage_access.ScopedKnowledgeRead, "finish", mutate_before_recheck)
    with pytest.raises((api.LlmWikiApiError, PermissionError)) as refused:
        api.build_task_context(req, wiki_dir=str(wiki))
    assert attempted and (changed or prevented)
    if changed:
        cause = refused.value
        while cause is not None and not isinstance(cause, KnowledgeStorageError):
            cause = cause.__cause__
        assert isinstance(cause, KnowledgeStorageError)
        assert cause.code == "storage-mutation"
    else:
        assert isinstance(refused.value, (api.WorkspaceStateError, PermissionError))
        cause = refused.value
        while cause is not None and not isinstance(cause, PermissionError):
            cause = cause.__cause__
        assert isinstance(cause, PermissionError)
        assert cause.errno == errno.EACCES and cause.filename == str(page)


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
