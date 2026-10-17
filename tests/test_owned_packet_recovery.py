"""Owned-authority refusal remains strict and offers exact recovery requirements."""

from contextlib import redirect_stdout, redirect_stderr
import asyncio
import importlib.util
import io
import json
import os
from pathlib import Path

import pytest

from llm_wiki_cli import api, cli
from llm_wiki_cli.services.knowledge_loader import KnowledgeStateLoadError, load_knowledge_state
from llm_wiki_cli.services.maintenance_protocol import ADOPTION_FILENAME, MaintenanceProtocolError, snapshot_wiki
from llm_wiki_cli.services.maintenance_service import adopt_maintenance_authority, recover_maintenance_authority
from llm_wiki_cli.services.mcp_server import McpWikiService, McpWikiError

FORMATS = ("v1", "sharded-v2", "packed-v3", "packed-v3-deflate", "packed-v4", "packed-v4-deflate")
EXPECTED_CODE = "maintenance-authority-unavailable"
FACTS = ("domain", "cause", "committed_snapshot", "command", "identity", "boundaries")


def owned_project(root, mode="packed-v4-deflate", manifest_format="indexed-v8"):
    root.mkdir(parents=True, exist_ok=True)
    (root / "src").mkdir()
    (root / "src/app.py").write_text("raise RuntimeError('target must not run')\n\nclass Item:\n    value: int\n", encoding="utf-8")
    api.bootstrap_wiki("src", "wiki", knowledge_format=mode)
    result = adopt_maintenance_authority("src", "wiki", recovery_dir="recovery", manifest_format=manifest_format)
    assert load_knowledge_state("wiki").knowledge is not None
    return result


def score(code, details):
    recovery = details.get("recovery", {}) if isinstance(details, dict) else {}
    argv = recovery.get("argv_template", [])
    return {
        "domain": code == EXPECTED_CODE,
        "cause": details.get("reason") == "maintenance-owner-missing",
        "committed_snapshot": recovery.get("snapshot_kind") == "committed",
        "command": argv[:3] == ["llm-wiki", "maintenance", "recover"],
        "identity": "--expected-adoption-id" in argv and bool(recovery.get("identity_requirement")),
        "boundaries": bool(recovery.get("boundary_requirement")) and recovery.get("automatic") is False,
    }


def assert_diagnostic(code, details, reason="maintenance-owner-missing"):
    assert code == EXPECTED_CODE
    assert details["field"] == "wiki_dir"
    assert details["reason"] == reason
    assert details["native_evidence"] == "unavailable"
    assert details["recovery"]["automatic"] is False
    assert len(json.dumps(details).encode("utf-8")) < 8192
    if reason == "maintenance-owner-missing":
        assert all(score(code, details).values())


def public_refusals():
    """Collect all three facade diagnostics without executing recovery."""
    try:
        api.build_qualified_context("src", "wiki", request={"budget_tokens": 32000, "focus": ["all"]})
    except api.InvalidRequestError as exc:
        api_error = exc
        assert_diagnostic(exc.code, exc.details)
    else:
        pytest.fail("owned damage cannot produce a packet")
    try:
        McpWikiService(src_dir="src", wiki_dir="wiki").get_context_packet(focus=["all"])
    except McpWikiError as exc:
        assert_diagnostic(exc.code, exc.data)
        assert exc.data == api_error.details
    else:
        pytest.fail("MCP cannot promote owned damage to native evidence")
    out, err = io.StringIO(), io.StringIO()
    args = cli._build_parser().parse_args(["context", "--src-dir", "src", "--wiki-dir", "wiki",
                                          "--budget", "32000", "--focus", "all", "--format", "packet"])
    from llm_wiki_cli.services import context_service
    with redirect_stdout(out), redirect_stderr(err), pytest.raises(SystemExit) as failure:
        context_service.run(args)
    assert failure.value.code == 1 and not out.getvalue()
    assert "Traceback" not in err.getvalue() and "loader-selected" not in err.getvalue()
    body = json.loads(err.getvalue())
    cli_details = {k: v for k, v in body["error"].items() if k not in {"code", "message"}}
    assert cli_details == api_error.details
    assert_diagnostic(body["error"]["code"], cli_details)
    cause = api_error.__cause__
    from llm_wiki_cli.services.context_packet import ContextPacketAuthorityError
    assert isinstance(cause, ContextPacketAuthorityError)
    assert isinstance(cause.__cause__, (KnowledgeStateLoadError, MaintenanceProtocolError))
    assert cause.issues[0].code == "maintenance-owner-missing"
    return api_error


@pytest.mark.parametrize("mode", FORMATS)
@pytest.mark.parametrize("manifest_format", ["v7", "indexed-v8"])
def test_all_stored_layouts_share_readonly_recovery_diagnostic(tmp_path, monkeypatch, mode, manifest_format):
    monkeypatch.chdir(tmp_path)
    with redirect_stdout(io.StringIO()):
        adopted = owned_project(tmp_path, mode, manifest_format)
    full = snapshot_wiki("wiki")
    source = (tmp_path / "src/app.py").read_bytes()
    (tmp_path / "wiki/.llm-wiki-manifest.json").unlink()
    (tmp_path / "wiki/.llm-wiki-knowledge.json").unlink()
    damaged = snapshot_wiki("wiki")
    error = public_refusals()
    assert snapshot_wiki("wiki") == damaged and (tmp_path / "src/app.py").read_bytes() == source
    # Apply only the explicitly requested existing recovery owner, with facts
    # retained by this caller; the diagnostic never guesses a backup or UUID.
    assert error.details is not None
    argv = error.details["recovery"]["argv_template"]
    substitutions = {"{wiki_dir}": "wiki", "{recovery_dir}": "recovery/committed",
                     "{expected_adoption_id}": adopted["adoption_id"]}
    parsed = cli._build_parser().parse_args([substitutions.get(arg, arg) for arg in argv[1:]])
    from llm_wiki_cli.commands import maintenance_cmd
    # Existing recovery rejects absence of non-owner files, even with a complete
    # matching backup. Keep that guard and its limitation visible; restore only
    # the exact retained projection preimage before exercising owner recovery.
    with redirect_stdout(io.StringIO()), pytest.raises(SystemExit):
        maintenance_cmd.run(parsed)
    assert snapshot_wiki("wiki") == damaged
    assert any("Missing projections" in text for text in error.details["recovery"]["preconditions"])
    (tmp_path / "wiki/.llm-wiki-knowledge.json").write_bytes(full[".llm-wiki-knowledge.json"])
    with redirect_stdout(io.StringIO()):
        maintenance_cmd.run(parsed)
    assert snapshot_wiki("wiki") == full
    assert api.build_qualified_context("src", "wiki", request={"budget_tokens": 32000, "focus": ["all"]}).to_payload()["response"]["knowledge"]["availability"] == "ready"


@pytest.mark.parametrize("damage,reason", [
    ("corrupt-owner", "maintenance-owner-invalid"),
    ("legacy-owner", "maintenance-owner-incompatible"),
    ("missing-marker", "maintenance-adoption-missing"),
    ("corrupt-marker", "maintenance-adoption-invalid"),
    ("marker-mismatch", "maintenance-adoption-mismatch"),
    ("marker-only", "maintenance-owner-missing"),
])
def test_distinct_authority_causes_remain_bounded_and_do_not_repair(tmp_path, monkeypatch, damage, reason):
    monkeypatch.chdir(tmp_path)
    with redirect_stdout(io.StringIO()):
        owned_project(tmp_path)
    wiki = Path("wiki")
    if damage == "corrupt-owner":
        (wiki / ".llm-wiki-manifest.json").write_text('{"private-leak":"' + "sensitive/host/path" * 1000)
    elif damage == "legacy-owner":
        before = Path("recovery/before/.llm-wiki-manifest.json").read_bytes()
        (wiki / ".llm-wiki-manifest.json").write_bytes(before)
    elif damage == "missing-marker":
        (wiki / ADOPTION_FILENAME).unlink()
    elif damage == "corrupt-marker":
        (wiki / ADOPTION_FILENAME).write_bytes(b"private-leak invalid marker")
    elif damage == "marker-mismatch":
        from llm_wiki_cli.services.knowledge_storage import canonical_bytes
        value = json.loads((wiki / ADOPTION_FILENAME).read_bytes())
        value["adoption_id"] = "00000000-0000-4000-8000-000000000000"
        (wiki / ADOPTION_FILENAME).write_bytes(canonical_bytes(value))
    else:
        for name in (".llm-wiki-manifest.json", ".llm-wiki-knowledge.json", ".llm-wiki-surface.json"):
            (wiki / name).unlink()
    before = snapshot_wiki(wiki)
    with pytest.raises(api.InvalidRequestError) as failure:
        api.build_qualified_context("src", "wiki", request={"budget_tokens": 32000, "focus": ["all"]})
    assert_diagnostic(failure.value.code, failure.value.details, reason)
    structured = str(failure.value) + json.dumps(failure.value.details)
    assert "private-leak" not in structured and "sensitive/host/path" not in structured
    assert str(tmp_path) not in structured and "loader-selected" not in structured
    assert snapshot_wiki(wiki) == before


@pytest.mark.parametrize("mode", ["auto", "required", "off"])
def test_packet_modes_preserve_refusal_while_source_only_task_remains_separate(tmp_path, monkeypatch, mode):
    monkeypatch.chdir(tmp_path)
    with redirect_stdout(io.StringIO()):
        owned_project(tmp_path)
    (tmp_path / "wiki/.llm-wiki-manifest.json").unlink()
    before = snapshot_wiki("wiki")
    with pytest.raises(api.InvalidRequestError) as failure:
        api.build_qualified_context("src", "wiki", request={"budget_tokens": 32000, "focus": ["all"], "knowledge_mode": mode})
    assert_diagnostic(failure.value.code, failure.value.details)
    request = {"requirements": [{"id": "source", "facet": "source-contract", "selector": "app.py:Item"}],
               "options": {"knowledge_mode": "off"}}
    assert api.build_task_context(request, src_dir="src", wiki_dir="wiki").ok
    assert snapshot_wiki("wiki") == before


@pytest.mark.parametrize("surface", ["api", "cli", "mcp", "request-cli"])
def test_budgeted_and_request_surfaces_preserve_domain_diagnostic(tmp_path, monkeypatch, surface):
    monkeypatch.chdir(tmp_path)
    with redirect_stdout(io.StringIO()):
        owned_project(tmp_path)
    (tmp_path / "wiki/.llm-wiki-manifest.json").unlink()
    before = snapshot_wiki("wiki")
    request = {"budget_tokens": 32000, "budget_mode": "estimated", "knowledge_mode": "required",
               "format": "packet", "focus": ["all"], "changes": {"mode": "paths", "paths": ["app.py"]}}
    if surface == "api":
        with pytest.raises(api.InvalidRequestError) as failure:
            api.build_budgeted_context("src", "wiki", request)
        assert_diagnostic(failure.value.code, failure.value.details)
    elif surface == "mcp":
        with pytest.raises(McpWikiError) as failure:
            McpWikiService(src_dir="src", wiki_dir="wiki").build_budgeted_context(request)
        assert_diagnostic(failure.value.code, failure.value.data)
    else:
        from llm_wiki_cli.services import context_service
        args = ["context", "--src-dir", "src", "--wiki-dir", "wiki"]
        if surface == "cli":
            args += ["--budget", "32000", "--budget-mode", "estimated", "--format", "packet", "--knowledge-mode", "required"]
        else:
            request.pop("budget_mode")
            request.pop("changes")
            request["format"] = "json"  # Inner v2 representation; CLI selects packet delivery.
            (tmp_path / "request.json").write_text(json.dumps(request))
            args += ["--request", "request.json", "--format", "packet"]
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err), pytest.raises(SystemExit) as failure:
            context_service.run(cli._build_parser().parse_args(args))
        assert failure.value.code == 1 and not out.getvalue()
        body = json.loads(err.getvalue())
        assert_diagnostic(body["error"]["code"], {k: v for k, v in body["error"].items() if k not in {"code", "message"}})
    assert snapshot_wiki("wiki") == before


def test_true_legacy_absence_keeps_auto_fallback_and_required_failure(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "src").mkdir()
    (tmp_path / "src/app.py").write_text("class Item: pass\n")
    with redirect_stdout(io.StringIO()):
        api.bootstrap_wiki("src", "wiki", knowledge_format="v1")
    for name in (".llm-wiki-manifest.json", ".llm-wiki-knowledge.json"):
        (tmp_path / "wiki" / name).unlink()
    assert not (tmp_path / "wiki" / ADOPTION_FILENAME).exists()
    before = snapshot_wiki("wiki")
    response = api.build_qualified_context("src", "wiki", request={"budget_tokens": 32000, "focus": ["all"]}).to_payload()["response"]
    assert response["knowledge"]["availability"] == "absent"
    with pytest.raises(api.LlmWikiApiError) as failure:
        api.build_qualified_context("src", "wiki", request={"budget_tokens": 32000, "focus": ["all"], "knowledge_mode": "required"})
    assert failure.value.code == "knowledge-required-unavailable"
    assert snapshot_wiki("wiki") == before


def test_guidance_does_not_authorize_wrong_identity_or_prose_replacement(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    with redirect_stdout(io.StringIO()):
        adopted = owned_project(tmp_path)
    (tmp_path / "wiki/.llm-wiki-manifest.json").unlink()
    before = snapshot_wiki("wiki")
    with pytest.raises(ValueError, match="another adoption identity"):
        recover_maintenance_authority(Path("wiki"), recovery_dir=Path("recovery/committed"),
                                      expected_adoption_id="00000000-0000-4000-8000-000000000000")
    assert snapshot_wiki("wiki") == before
    page = Path("wiki/entities/Item.md")
    page.write_bytes(page.read_bytes() + b"\nNewer authored prose\n")
    edited = snapshot_wiki("wiki")
    with pytest.raises(ValueError, match="changed outside"):
        recover_maintenance_authority(Path("wiki"), recovery_dir=Path("recovery/committed"),
                                      expected_adoption_id=adopted["adoption_id"])
    assert snapshot_wiki("wiki") == edited


def test_registered_sdk_keeps_structured_authority_failure(tmp_path, monkeypatch):
    if importlib.util.find_spec("mcp") is None:
        if os.environ.get("LLM_WIKI_REQUIRE_MCP_SDK") == "1":
            pytest.fail("MCP SDK is required for this verification owner")
        pytest.skip("Optional MCP SDK is not installed")
    from mcp import types as mcp_types
    from llm_wiki_cli.services.mcp_server import create_mcp_server, McpServerConfig

    monkeypatch.chdir(tmp_path)
    with redirect_stdout(io.StringIO()):
        owned_project(tmp_path)
    (tmp_path / "wiki/.llm-wiki-manifest.json").unlink()
    before = snapshot_wiki("wiki")
    server = create_mcp_server(McpServerConfig(src_dir="src", wiki_dir="wiki"))
    async def call(name, arguments):
        handler = server._mcp_server.request_handlers[mcp_types.CallToolRequest]
        reply = await handler(mcp_types.CallToolRequest(method="tools/call",
            params=mcp_types.CallToolRequestParams(name=name, arguments=arguments)))
        assert isinstance(reply.root, mcp_types.CallToolResult)
        return reply.root
    for name, arguments in (("get_context_packet", {"focus": ["all"]}), ("build_budgeted_context", {"request": {
        "budget_tokens": 32000, "budget_mode": "estimated", "knowledge_mode": "required",
        "format": "packet", "focus": ["all"], "changes": {"mode": "paths", "paths": ["app.py"]}}})):
        reply = asyncio.run(call(name, arguments))
        assert reply.isError and reply.structuredContent is not None
        body = reply.structuredContent
        assert "packet" not in body
        assert_diagnostic(body["error"]["code"], body["error"]["details"])
        assert str(tmp_path) not in json.dumps(body)
    assert snapshot_wiki("wiki") == before


@pytest.mark.parametrize("budgeted", [False, True])
def test_failed_cli_preserves_preexisting_output(tmp_path, monkeypatch, budgeted):
    monkeypatch.chdir(tmp_path)
    with redirect_stdout(io.StringIO()):
        owned_project(tmp_path)
    (tmp_path / "wiki/.llm-wiki-manifest.json").unlink()
    output = tmp_path / "retained.json"
    output.write_bytes(b"original caller bytes\n")
    args = ["context", "--src-dir", "src", "--wiki-dir", "wiki", "--format", "packet", "--budget", "32000",
            "--output", str(output)]
    if budgeted:
        args += ["--budget-mode", "estimated"]
    from llm_wiki_cli.services import context_service
    with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()), pytest.raises(SystemExit):
        context_service.run(cli._build_parser().parse_args(args))
    assert output.read_bytes() == b"original caller bytes\n"
