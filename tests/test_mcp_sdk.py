"""Focused registration contract for the real optional MCP SDK."""

from __future__ import annotations

import asyncio
import importlib.util
import os
from pathlib import Path

import pytest

from llm_wiki_cli.services import mcp_server


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
