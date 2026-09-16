"""Public adapter parity and deliberate boundary/accounting failures."""

import asyncio
import io
import json
import sys
import importlib.util
import os

import pytest

from llm_wiki_cli import api, cli
from llm_wiki_cli.services import context_budget, search_service
from llm_wiki_cli.services.mcp_server import McpServerConfig, McpWikiError, McpWikiService, create_mcp_server
from llm_wiki_cli.services.request_json import MAX_REQUEST_BYTES, parse_request
from llm_wiki_cli.services.token_counting import EstimatedCounter
from tests.test_context_budget import ByteCounter
from tests.test_mcp import _write_wiki


@pytest.fixture
def project(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _write_wiki(tmp_path)
    (tmp_path / "app.py").write_text('def café(value: int = 3):\n    return value\n', encoding="utf-8")
    return tmp_path


@pytest.mark.parametrize("mode", ["ranked", "substring"])
def test_search_public_mcp_parity(project, mode):
    result = api.search_wiki("User", mode=mode)
    assert result == McpWikiService().search_wiki("User", mode=mode)
    assert "entities/User.md" in [match["path"] for match in result["results"]]
    if mode == "ranked":
        assert result["results"][0]["path"] == "entities/User.md"
    assert api.search_wiki("no-such-needle", mode=mode)["total"] == 0


@pytest.mark.parametrize("options", [{"query": ""}, {"query": "x", "limit": True},
    {"query": "x", "kinds": "modules"}, {"query": "x", "mode": "guess"}])
def test_bad_search_fails_before_inventory(monkeypatch, options):
    monkeypatch.setattr(search_service, "build_source_snapshot", lambda *a, **k: pytest.fail("source read"))
    with pytest.raises(api.InvalidRequestError):
        api.search_wiki(**options)


def test_queue_public_mcp_parity_and_bounds(project):
    result = api.build_maintenance_queue(limit=1)
    assert result == McpWikiService().get_maintenance_queue(limit=1)
    assert result["advisory"] is True
    assert result["returned"] == 1 and result["total"] > 1
    assert result["omitted"] == result["total"] - 1
    for bad in (0, -1, True, 1001):
        with pytest.raises(api.InvalidRequestError):
            api.build_maintenance_queue(limit=bad)


@pytest.mark.parametrize("fmt", ["json", "packet", "markdown"])
@pytest.mark.parametrize("counter,mode", [(ByteCounter(), "exact"), (EstimatedCounter(), "estimated")])
def test_budgeted_mcp_matches_api_and_independent_validator(project, fmt, counter, mode):
    request = {"protocol": "llm-wiki-context/v3", "budget_tokens": 200000,
               "budget_mode": mode, "format": fmt, "focus": ["all"],
               "changes": {"mode": "paths", "paths": ["app.py", "deleted.py"]}}
    expected = api.build_budgeted_context(request=request, counter=counter)
    actual = McpWikiService(counter=counter).build_budgeted_context(request)
    assert actual == expected.rendered
    payload = api.validate_budgeted_context(actual, request, counter=counter)
    assert counter.count(actual) <= payload["accounting"]["used_tokens"] <= 200000
    with pytest.raises(api.InvalidRequestError):
        api.validate_budgeted_context(actual, {**request, "focus": ["changed"]}, counter=counter)
    if fmt != "markdown":
        payload["accounting"]["used_tokens"] = 1
        corrupted = json.dumps(payload, sort_keys=True, ensure_ascii=False, separators=(",", ":")) + "\n"
        with pytest.raises(api.InvalidRequestError, match="accounting"):
            api.validate_budgeted_context(corrupted, request, counter=counter)


@pytest.mark.parametrize("patch", [{"protocol": "future"}, {"tokenizer": "/private/secret"},
    {"src_dir": "/"}, {"budget_tokens": True}, {"changes": {"mode": "paths", "paths": ["../outside"]}}])
def test_budget_request_rejected_before_source(project, monkeypatch, patch):
    monkeypatch.setattr(context_budget.packets, "capture_context_read", lambda *a, **k: pytest.fail("source read"))
    with pytest.raises(McpWikiError):
        McpWikiService().build_budgeted_context({"protocol": "llm-wiki-context/v3",
            "budget_tokens": 1000, "budget_mode": "estimated", **patch})


def test_budget_errors_do_not_return_partial_success(project):
    with pytest.raises(McpWikiError) as exc:
        McpWikiService().build_budgeted_context({"protocol": "llm-wiki-context/v3", "budget_tokens": 1,
            "changes": {"mode": "paths", "paths": []}})
    assert exc.value.code == "counter-unavailable"
    with pytest.raises(McpWikiError) as exc:
        McpWikiService().build_budgeted_context({"protocol": "llm-wiki-context/v3",
            "budget_tokens": 1, "budget_mode": "estimated", "changes": {"mode": "paths", "paths": []}})
    assert exc.value.code == "cannot-fit"


def test_real_sdk_preserves_single_counted_representation(project):
    if importlib.util.find_spec("mcp") is None:
        if os.environ.get("LLM_WIKI_REQUIRE_MCP_SDK") == "1":
            pytest.fail("MCP SDK is required by this test environment.")
        pytest.skip("MCP SDK is not installed.")
    from mcp import types

    server = create_mcp_server(McpServerConfig(counter=ByteCounter()))
    request = {"protocol": "llm-wiki-context/v3", "budget_tokens": 100000, "format": "packet",
               "changes": {"mode": "paths", "paths": []}}

    async def call():
        handler = server._mcp_server.request_handlers[types.CallToolRequest]
        result = await handler(types.CallToolRequest(method="tools/call",
            params=types.CallToolRequestParams(name="build_budgeted_context", arguments={"request": request})))
        assert isinstance(result.root, types.CallToolResult)
        return result.root

    response = asyncio.run(call())
    assert response.isError is False
    assert response.structuredContent is None
    assert len(response.content) == 1 and response.content[0].type == "text"
    api.validate_budgeted_context(response.content[0].text, request, counter=ByteCounter())


@pytest.mark.parametrize("raw", [b'{"a":1,"a":2}', b'{"a":NaN}', b'[]', b'\xff',
                                  b' ' * (MAX_REQUEST_BYTES + 1), b'[' * 3000,
                                  '{"a":1}'.encode("utf-16")])
def test_request_json_rejects_ambiguous_unbounded_input(raw):
    with pytest.raises(ValueError):
        parse_request(raw)


def test_query_cli_stdin_parity_and_safe_error(tmp_path, monkeypatch, capsys):
    from tests.test_context_packet_knowledge import _materialize_ready_project
    _materialize_ready_project(tmp_path, monkeypatch)
    request = {"operation": "surface", "value": "index.md"}
    monkeypatch.setattr(sys, "argv", ["llm-wiki", "query", "--request", "-"])
    monkeypatch.setattr(sys, "stdin", io.StringIO(json.dumps(request)))
    cli.main()
    assert json.loads(capsys.readouterr().out) == api.query_documentation(request)
    monkeypatch.setattr(sys, "stdin", io.StringIO('{"operation":"run","command":"secret"}'))
    with pytest.raises(SystemExit) as exc:
        cli.main()
    assert exc.value.code == 2
    output = capsys.readouterr()
    assert output.out == "" and "secret" not in output.err


@pytest.mark.parametrize("fields", [{"direction": "invalid"}, {"origins": ["invented"]},
                                    {"include_evidence": 1}, {"resolutions": "resolved"}])
def test_query_filters_are_rejected_before_loading_native_state(monkeypatch, fields):
    monkeypatch.setattr(api, "_snapshot_query_service", lambda *a, **k: pytest.fail("invalid query performed a read"))
    with pytest.raises(api.InvalidRequestError):
        api.query_documentation({"operation": "typed", "value": "modules/app.md", **fields})
