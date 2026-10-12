"""First-use JSON preserves complete evidence and the owned canonical lifecycle."""

import asyncio
import json
from pathlib import Path

import pytest

from llm_wiki_cli import api
from llm_wiki_cli.services import mcp_server, task_compact
from llm_wiki_cli.services.token_counting import EstimatedCounter
from llm_wiki_cli.services.workflow_profile import canonical_json, content_id
from llm_wiki_cli.services.context_budget import _accounted_render
from tests.test_task_compact import reseal_canonical
from tests.test_task_compact_receiving import tiny_request
from tests.developer_value.fixtures import POLICY_SOURCE


def options(budget=32000):
    return {"schema_version": task_compact.VIEW_REQUEST_SCHEMA_V2,
            "budget_tokens": budget}


@pytest.fixture
def project(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    Path("src").mkdir()
    Path("src/policy.py").write_text(POLICY_SOURCE)
    request = tiny_request()
    original = api.build_task_context(request, src_dir="src", wiki_dir="wiki")
    assert original.ok
    return request, original


def test_first_use_body_is_complete_readable_json_with_no_external_decoder(project):
    request, original = project
    view = api.build_compact_task_context(request, view_options=options(),
                                         src_dir="src", wiki_dir="wiki")
    payload = json.loads(view.rendered)
    canonical = original.to_payload()
    for key in ("facts", "coverage", "omissions", "followups", "limitations", "anchors"):
        assert payload[key] == canonical[key]
    assert payload["canonical"]["result_id"] == original.result_id
    assert payload["intent"]["text"] == "" and payload["intent"]["task_ref"] is None
    assert payload["native"]["whole_store_validated"] is False
    assert view.schema_version == task_compact.COMPACT_SCHEMA_V2
    assert view.accounting["used_tokens"] == EstimatedCounter().count(view.rendered)
    assert view.canonical_text == original.rendered


@pytest.mark.parametrize("value", [None, False, 0, {"from": "parameters"},
                                   {"unknown": [None, False, 0, "保持 λ 📚"]}])
def test_future_and_literal_observation_fields_remain_exact(project, value):
    request, original = project
    data = original.to_payload()
    fact = next(x for x in data["facts"] if x["facet"] == "source-contract")
    fact["observation"]["contract"]["future-extension"] = value
    text = reseal_canonical(data)
    canonical = api.validate_task_context(text, request)
    view = api.render_compact_task_context(text, request, view_options=options())
    assert view.to_payload()["facts"] == canonical["facts"]
    assert api.expand_compact_task_context(view.rendered, text, request,
                                         view_options=options())["facts"] == canonical["facts"]


@pytest.mark.parametrize("field", ["facts", "coverage", "limitations", "canonical",
                                   "omissions", "native", "schema_version"])
def test_self_rehashed_readable_forgery_cannot_upgrade_or_drop_evidence(project, field):
    request, original = project
    view = api.render_compact_task_context(original, request, view_options=options())
    data = view.to_payload()
    if field in ("facts", "coverage", "limitations"):
        data[field] = []
    elif field == "canonical":
        data[field]["result_id"] = "sha256:" + "0" * 64
    elif field == "native":
        data[field]["whole_store_validated"] = True
    elif field == "schema_version":
        data[field] = task_compact.COMPACT_SCHEMA
    else:
        data[field] = [{"invented": "verified"}]

    def render(accounting):
        data["accounting"] = dict(accounting)
        data["view_id"] = content_id(data["schema_version"],
                                     {k: v for k, v in data.items() if k != "view_id"})
        return canonical_json(data).decode()

    forged = _accounted_render(render, data["accounting"], EstimatedCounter())
    with pytest.raises(api.InvalidRequestError):
        api.validate_compact_task_context(forged,
                                         original.rendered, request, view_options=options())


def test_readable_budget_failure_counts_diagnostic_and_preserves_receipt(project):
    request, original = project
    view = api.build_compact_task_context(request, view_options=options(1),
                                         src_dir="src", wiki_dir="wiki")
    assert not view.ok and view.error == "cannot-fit-compact" and not view.rendered
    assert view.schema_version == task_compact.COMPACT_SCHEMA_V2
    assert view.canonical_text == original.rendered
    assert "facts" not in view.to_payload()
    assert view.to_payload()["diagnostic_accounting"]["used_tokens"] == EstimatedCounter().count(view.diagnostic_rendered)


def test_counter_mutation_cannot_publish_false_current_readable_view(project):
    request, _ = project
    path = Path("src/policy.py")

    class MutatingCounter(EstimatedCounter):
        changed = False

        def count(self, text):
            if task_compact.COMPACT_SCHEMA_V2 in text and not self.changed:
                self.changed = True
                path.write_text(path.read_text() + "\n# concurrent change\n")
            return super().count(text)

    counter = MutatingCounter()
    with pytest.raises(api.LlmWikiApiError):
        api.build_compact_task_context(request, view_options=options(),
                                      src_dir="src", wiki_dir="wiki", counter=counter)
    assert counter.changed


def test_selected_native_mutation_aborts_readable_publication(project, capsys):
    from llm_wiki_cli.services.knowledge_storage_lifecycle import migrate_knowledge_storage

    request, _ = project
    api.bootstrap_wiki("src", "wiki")
    migrate_knowledge_storage(Path("wiki"), to="sharded-v2", recovery_dir=Path("recovery"))
    capsys.readouterr()
    request["options"]["knowledge_mode"] = "required"
    request["requirements"].append({"id": "native", "facet": "concept",
                                     "selector": "llm-wiki://modules/policy"})

    class MutatingCounter(EstimatedCounter):
        changed = False

        def count(self, text):
            if task_compact.COMPACT_SCHEMA_V2 in text and not self.changed:
                self.changed = True
                path = Path("wiki/modules/policy.md")
                path.write_text(path.read_text() + "\n# concurrent authored change\n")
            return super().count(text)

    counter = MutatingCounter()
    with pytest.raises(api.LlmWikiApiError):
        api.build_compact_task_context(request, view_options=options(),
                                      src_dir="src", wiki_dir="wiki", counter=counter)
    assert counter.changed


def test_actual_mcp_v2_metadata_toggle_keeps_qualifications_and_receipts(project):
    from mcp.types import CallToolResult, TextContent

    request, original = project
    server = mcp_server.create_mcp_server(mcp_server.McpServerConfig(
        src_dir="src", wiki_dir="wiki", enable_sessions=True))

    def call(name, args):
        return asyncio.run(server.call_tool(name, args))

    opened = call("open_context_session", {})
    if isinstance(opened, CallToolResult):
        block = opened.content[0]
        assert isinstance(block, TextContent)
        handle = json.loads(block.text)["session_id"]
    elif isinstance(opened, (list, tuple)):
        block = opened[0]
        if isinstance(block, list):
            block = block[0]
        assert isinstance(block, TextContent)
        handle = json.loads(block.text)["session_id"]
    else:
        assert isinstance(opened, dict)
        handle = opened["session_id"]
    args = {"session_id": handle, "request": request, "view_options": options()}
    minimal = call("read_compact_context_session", args)
    full = call("read_compact_context_session", {**args, "include_metadata": True})
    assert isinstance(minimal, CallToolResult) and isinstance(full, CallToolResult)
    first, second = minimal.content[0], full.content[0]
    assert isinstance(first, TextContent) and isinstance(second, TextContent)
    assert first.text == second.text
    assert minimal.structuredContent is not None and full.structuredContent is not None
    assert "work" not in minimal.structuredContent and "work" in full.structuredContent
    for key, value in minimal.structuredContent.items():
        assert full.structuredContent[key] == value
    assert "limitations" in minimal.structuredContent
    assert "environment_validation" in minimal.structuredContent
    receipt = call("get_task_context_receipt", {
        "session_id": handle, "request_id": minimal.structuredContent["request_id"],
        "result_id": minimal.structuredContent["result_id"],
    })
    assert isinstance(receipt, CallToolResult)
    block = receipt.content[0]
    assert isinstance(block, TextContent)
    assert block.text == original.rendered
    unchanged = call("read_compact_context_session", {**args,
        "if_result_id": minimal.structuredContent["result_id"],
        "if_view_id": minimal.structuredContent["view_id"]})
    assert isinstance(unchanged, CallToolResult) and unchanged.structuredContent is not None
    assert unchanged.structuredContent["state"] == "unchanged"
    assert "work" not in unchanged.structuredContent


def test_readable_conversion_is_pure_and_keeps_legacy_bytes(project, monkeypatch):
    request, original = project
    legacy_opts = {"schema_version": task_compact.VIEW_REQUEST_SCHEMA, "budget_tokens": 32000}
    legacy = api.render_compact_task_context(original, request, view_options=legacy_opts)

    def refuse(*args, **kwargs):
        raise AssertionError("presentation performed filesystem I/O")

    monkeypatch.setattr(Path, "read_bytes", refuse)
    monkeypatch.setattr(Path, "read_text", refuse)
    readable = api.render_compact_task_context(original, request, view_options=options())
    assert readable.ok
    assert api.render_compact_task_context(original, request, view_options=legacy_opts).rendered == legacy.rendered


def test_presentation_classification_does_not_change_analysis_identity():
    from llm_wiki_cli.services.analysis_capture import registry

    rules = registry()
    name = "services/task_compact_readable.py"
    assert name in rules["classified_python_files"]
    assert name not in rules["shared"]
    assert all(name not in names for names in rules["providers"].values())


def test_minimal_metadata_preserves_new_qualifications_and_conditional_base(project):
    from llm_wiki_cli.services.task_compact_readable import readable_session_metadata

    request, _ = project
    with api.open_context_session(src_dir="src", wiki_dir="wiki") as owner:
        reply = owner.read_compact(request, view_options=options())
        metadata = reply.metadata()
    metadata["future_qualification"] = {"authority": None, "supported": False}
    metadata["base_id"] = "sha256:" + "1" * 64
    minimal = readable_session_metadata(metadata)
    assert minimal["future_qualification"] == metadata["future_qualification"]
    assert minimal["base_id"] == metadata["base_id"]
    assert "work" not in minimal and "reuse" not in minimal


@pytest.mark.parametrize("state", ["stale", "selected-review", "missing", "corrupt"])
def test_native_gaps_and_review_scope_survive_readable_delivery(project, capsys, state):
    from llm_wiki_cli.services.knowledge_storage_lifecycle import migrate_knowledge_storage
    from llm_wiki_cli.services.maintenance_service import adopt_maintenance_authority

    request, _ = project
    request["options"]["knowledge_mode"] = "auto" if state == "missing" else "required"
    request["requirements"].append({"id": "native", "facet": "concept",
                                     "selector": "llm-wiki://entities/Batch"})
    if state != "missing":
        api.bootstrap_wiki("src", "wiki")
        if state == "selected-review":
            adopt_maintenance_authority("src", "wiki", recovery_dir="maintenance-recovery")
        migrate_knowledge_storage(Path("wiki"), to="sharded-v2", recovery_dir=Path("recovery"))
        capsys.readouterr()
    if state == "stale":
        Path("src/policy.py").write_text(POLICY_SOURCE.replace("values[:limit]", "values[:limit - 1]"))
    if state == "corrupt":
        Path("wiki/.llm-wiki-knowledge.json").write_text("{}\n")
        with pytest.raises(api.LlmWikiApiError):
            api.build_compact_task_context(request, view_options=options(),
                                          src_dir="src", wiki_dir="wiki")
        return
    original = api.build_task_context(request, src_dir="src", wiki_dir="wiki")
    view = api.build_compact_task_context(request, view_options=options(),
                                        src_dir="src", wiki_dir="wiki")
    assert view.ok and view.to_payload()["facts"] == original.to_payload()["facts"]
    assert view.to_payload()["coverage"] == original.to_payload()["coverage"]
    if state == "missing":
        assert not next(x for x in view.to_payload()["coverage"] if x["requirement_id"] == "native")["satisfied"]
    if state == "selected-review":
        concept = next(x for x in view.to_payload()["facts"] if x["facet"] == "concept")
        summary = concept["observation"]["concept"]["maintenance"]
        assert summary["analysis_scope"] == "selected-header"
        assert not summary["live_evaluation_performed"]
    assert all(x["qualification"]["behavior"] == "not-evaluated" for x in view.to_payload()["facts"])


@pytest.mark.parametrize("malformed", ["duplicate", "noncanonical", "nonfinite"])
def test_readable_receiver_rejects_malformed_json(project, malformed):
    request, original = project
    view = api.render_compact_task_context(original, request, view_options=options())
    altered = ('{"ok":true,' + view.rendered[1:] if malformed == "duplicate"
               else " " + view.rendered if malformed == "noncanonical"
               else '{"extra":NaN,' + view.rendered[1:])
    with pytest.raises(api.InvalidRequestError):
        api.validate_compact_task_context(altered, original.rendered, request,
                                         view_options=options())


def test_readable_exact_counter_and_unicode_scope_are_preserved(project):
    from tests.test_task_compact_receiving import CharacterTokenCounter

    request, _ = project
    request["text"] = "读取 λ 📚"
    request["options"]["budget_mode"] = "exact"
    counter = CharacterTokenCounter()
    view = api.build_compact_task_context(request, view_options=options(),
                                        src_dir="src", wiki_dir="wiki", counter=counter)
    assert view.ok and view.accounting["exact_compliance"] is True
    assert view.accounting["used_tokens"] == len(view.rendered)
    assert view.to_payload()["intent"]["text"] == request["text"]
