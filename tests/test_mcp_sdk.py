"""Focused registration contract for the real optional MCP SDK."""

from __future__ import annotations

import asyncio
import importlib.util
import json
import os
from pathlib import Path
from typing import Any

import pytest

from llm_wiki_cli.services import mcp_server
from llm_wiki_cli import api


def _write_minimal_wiki(root: Path) -> None:
    wiki = root / "docs" / "llm_wiki"
    for subdirectory in (
        "entities",
        "modules",
        "workflows",
        "guides",
        "flows",
        "infrastructure",
    ):
        (wiki / subdirectory).mkdir(parents=True, exist_ok=True)
    (root / "module.py").write_text("VALUE = 1\n", encoding="utf-8")
    (wiki / "index.md").write_text("# Index\n", encoding="utf-8")
    (wiki / "log.md").write_text("# Log\n", encoding="utf-8")
    (wiki / "api-contracts.md").write_text("# API Contracts\n", encoding="utf-8")
    (wiki / "dependencies.md").write_text("# Dependencies\n", encoding="utf-8")
    (wiki / "load-order.md").write_text("# Load Order\n", encoding="utf-8")


def test_optional_sdk_registration_when_installed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    if importlib.util.find_spec("mcp") is None:
        if os.environ.get("LLM_WIKI_REQUIRE_MCP_SDK") == "1":
            pytest.fail("MCP SDK is required by this test environment.")
        pytest.skip("MCP SDK is not installed.")

    project = tmp_path / "project"
    project.mkdir()
    _write_minimal_wiki(project)
    monkeypatch.chdir(project)
    server = mcp_server.create_mcp_server(mcp_server.McpServerConfig())

    async def list_registrations():
        return (
            await server.list_tools(),
            await server.list_resources(),
            await server.list_resource_templates(),
        )

    tools, resources, templates = asyncio.run(list_registrations())
    from mcp import types as mcp_types

    async def call_packet(arguments, name="get_context_packet"):
        handler = server._mcp_server.request_handlers[mcp_types.CallToolRequest]
        result = await handler(mcp_types.CallToolRequest(
            method="tools/call",
            params=mcp_types.CallToolRequestParams(name=name, arguments=arguments),
        ))
        assert isinstance(result.root, mcp_types.CallToolResult)
        return result.root

    def packet_payload(result):
        assert result.isError is False
        return result.structuredContent or json.loads(next(
            item.text for item in result.content if item.type == "text"
        ))

    for mode in (None, "off", "auto"):
        arguments: dict[str, Any] = {"focus": ["all"]}
        if mode is not None:
            arguments["knowledge_mode"] = mode
        response = packet_payload(asyncio.run(call_packet(arguments)))
        expected = api.build_qualified_context(request={
            "budget_tokens": 32000, "focus": ["all"], "format": "json", "filters": {},
        }, knowledge_mode=mode)
        raw = (json.dumps(response["packet"], sort_keys=True, separators=(",", ":"),
                          ensure_ascii=False, allow_nan=False) + "\n").encode()
        assert raw == expected.to_bytes()
        assert api.validate_context_packet(raw).packet_id == response["packet_id"]
        unchanged = packet_payload(asyncio.run(call_packet({**arguments, "if_packet_id": response["packet_id"]})))
        assert unchanged["state"] == "unchanged" and "packet" not in unchanged

    failed = asyncio.run(call_packet({"budget_tokens": 0}))
    assert failed.isError is True
    assert failed.structuredContent is not None
    assert failed.structuredContent["state"] == "error"
    assert failed.structuredContent["error"]["code"] == "invalid-request"
    assert failed.structuredContent["error"]["details"] == {"field": "budget_tokens"}
    assert "packet" not in failed.structuredContent
    assert str(project) not in json.dumps(failed.structuredContent)

    for name in ("get_concept", "related_concepts", "list_concept_sections",
                 "traverse_typed_graph", "explain_evidence", "inspect_concept"):
        failed = asyncio.run(call_packet({
            "locator_or_exact_route": "llm-wiki://entities/User", "limit": 0,
        }, name))
        assert failed.isError is True
        assert failed.structuredContent is not None
        assert failed.structuredContent["error"]["code"] == "invalid-request"
        assert failed.structuredContent["error"]["details"] == {"field": "limit"}
        assert str(project) not in json.dumps(failed.structuredContent)

    failed = asyncio.run(call_packet({"request": {
        "operation": "concept", "value": "llm-wiki://entities/User",
        "PRIVATE_UNKNOWN_FIELD": "PRIVATE_VALUE",
    }}, "query_documentation"))
    assert failed.isError is True
    assert failed.structuredContent is not None
    assert failed.structuredContent["error"]["code"] == "invalid-request"
    assert "PRIVATE_" not in json.dumps(failed.structuredContent)
    absent = asyncio.run(call_packet({}, "get_knowledge_coverage"))
    assert absent.isError is True
    assert absent.structuredContent is not None
    assert absent.structuredContent["error"]["code"] == "workspace-state-error"
    assert absent.structuredContent["error"]["details"] == {"field": "wiki_dir"}
    coverage = packet_payload(asyncio.run(call_packet({"live": True}, "get_knowledge_coverage")))
    assert coverage["schema_version"] == "llm-wiki-knowledge-coverage/v1"
    assert coverage["counts"] is None
    assert coverage["freshness_evaluated"] is False
    inspection = packet_payload(asyncio.run(call_packet({
        "locator_or_exact_route": "llm-wiki://entities/User", "live": True,
    }, "inspect_concept")))
    assert inspection["schema_version"] == "llm-wiki-native-inspection/v1"
    assert inspection["coverage"]["availability"] == "absent"
    assert inspection["concept"]["found"] is False

    tools_by_name = {tool.name: tool for tool in tools}
    for name, expected_fields in {
        "get_concept": {"locator_or_exact_route", "limit"},
        "related_concepts": {
            "locator_or_exact_route",
            "direction",
            "kinds",
            "limit",
        },
        "list_concept_sections": {
            "locator_or_exact_route",
            "ownership",
            "limit",
        },
        "traverse_typed_graph": {
            "locator_or_exact_route",
            "direction",
            "kinds",
            "origins",
            "resolutions",
            "include_evidence",
            "limit",
        },
        "explain_evidence": {"locator_or_exact_route", "limit"},
        "inspect_concept": {"locator_or_exact_route", "live", "limit", "include_evidence"},
    }.items():
        schema = tools_by_name[name].inputSchema
        assert set(schema["properties"]) == expected_fields
        assert schema["required"] == ["locator_or_exact_route"]

    for name in ("get_context", "get_context_packet"):
        mode_schema = tools_by_name[name].inputSchema["properties"]["knowledge_mode"]
        assert mode_schema["default"] is None
        assert {"enum": ["off", "auto", "required"], "type": "string"} in (
            mode_schema["anyOf"]
        )

    assert {
        "llm-wiki://index",
        "llm-wiki://log",
        "llm-wiki://api-contracts",
        "llm-wiki://dependencies",
        "llm-wiki://load-order",
    } <= {str(resource.uri) for resource in resources}
    assert {
        "llm-wiki://entities/{page_id}",
        "llm-wiki://modules/{page_id}",
        "llm-wiki://workflows/{page_id}",
        "llm-wiki://guides/{page_id}",
        "llm-wiki://flows/{page_id}",
        "llm-wiki://infrastructure/{page_id}",
    } <= {template.uriTemplate for template in templates}
