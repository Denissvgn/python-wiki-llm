"""Tests for the optional MCP server surface."""

from __future__ import annotations

import asyncio
import importlib.util
import sys
import types
from pathlib import Path

import pytest

from llm_wiki_cli import cli
from llm_wiki_cli.commands import context_cmd, mcp_cmd
from llm_wiki_cli.commands.extract_cmd import ExtractorStatus, InventoryResult
from llm_wiki_cli.services import mcp_server


def _args(**overrides):
    defaults = {
        "src_dir": ".",
        "wiki_dir": "docs/llm_wiki",
        "transport": "stdio",
        "host": "127.0.0.1",
        "port": 8765,
        "path": "/mcp",
        "allowed_origin": None,
    }
    defaults.update(overrides)
    return types.SimpleNamespace(**defaults)


def _write_wiki(root: Path) -> Path:
    wiki = root / "docs" / "llm_wiki"
    for subdir in ["entities", "modules", "workflows", "flows", "infrastructure"]:
        (wiki / subdir).mkdir(parents=True, exist_ok=True)
    (wiki / "index.md").write_text(
        "# Index\n\n- [User](entities/User.md)\n", encoding="utf-8"
    )
    (wiki / "log.md").write_text("# Log\n\n- Created wiki\n", encoding="utf-8")
    (wiki / "dependencies.md").write_text(
        "# Dependencies\n\nDependency graph.\n", encoding="utf-8"
    )
    (wiki / "load-order.md").write_text(
        "# Load Order\n\nInitialization sequence.\n", encoding="utf-8"
    )
    (wiki / "entities" / "User.md").write_text(
        "# User\n\nPrimary account entity.\n", encoding="utf-8"
    )
    (wiki / "modules" / "models.md").write_text(
        "# models Module\n\n**Path:** `models.py`\n", encoding="utf-8"
    )
    (wiki / "workflows" / "signup.md").write_text(
        "# Signup\n\nUser signup flow.\n", encoding="utf-8"
    )
    (wiki / "flows" / "checkout.md").write_text(
        "# Checkout\n\nCheckout user flow.\n", encoding="utf-8"
    )
    (wiki / "infrastructure" / "Dockerfile.md").write_text(
        "# Dockerfile\n\nContainer docs.\n", encoding="utf-8"
    )
    (wiki / "legacy").mkdir()
    (wiki / "legacy" / "old.md").write_text(
        "# Old\n\nPrimary account entity.\n", encoding="utf-8"
    )
    return wiki


def _write_legacy_wiki(root: Path) -> Path:
    wiki = root / "docs" / "llm_wiki"
    for subdir in ["entities", "modules", "workflows", "infrastructure"]:
        (wiki / subdir).mkdir(parents=True, exist_ok=True)
    (wiki / "index.md").write_text("# Index\n\n", encoding="utf-8")
    (wiki / "log.md").write_text("# Log\n\n", encoding="utf-8")
    (wiki / "entities" / "User.md").write_text("# User\n\n", encoding="utf-8")
    return wiki


class TestMcpWikiService:
    def test_get_entity_reads_markdown_page(self, tmp_project):
        _write_wiki(tmp_project)
        service = mcp_server.McpWikiService(src_dir=".", wiki_dir="docs/llm_wiki")

        result = service.get_entity("User")

        assert result["uri"] == "llm-wiki://entities/User"
        assert result["path"] == "entities/User.md"
        assert "Primary account entity" in result["content"]

    def test_get_module_accepts_source_path(self, tmp_project):
        _write_wiki(tmp_project)
        service = mcp_server.McpWikiService(src_dir=".", wiki_dir="docs/llm_wiki")

        result = service.get_module("models.py")

        assert result["id"] == "models"
        assert result["uri"] == "llm-wiki://modules/models"

    def test_resource_uri_resolution(self, tmp_project):
        _write_wiki(tmp_project)
        service = mcp_server.McpWikiService(src_dir=".", wiki_dir="docs/llm_wiki")

        index = service.read_resource("llm-wiki://index")
        entity = service.read_resource("llm-wiki://entities/User")
        flow = service.read_resource("llm-wiki://flows/checkout")
        dependencies = service.read_resource("llm-wiki://dependencies")
        load_order = service.read_resource("llm-wiki://load-order")

        assert index["mimeType"] == "text/markdown"
        assert entity["metadata"]["kind"] == "entities"
        assert "Primary account entity" in entity["text"]
        assert flow["metadata"]["path"] == "flows/checkout.md"
        assert dependencies["metadata"]["kind"] == "dependencies"
        assert "Dependency graph" in dependencies["text"]
        assert load_order["metadata"]["path"] == "load-order.md"

    def test_rejects_path_escape_resource(self, tmp_project):
        _write_wiki(tmp_project)
        service = mcp_server.McpWikiService(src_dir=".", wiki_dir="docs/llm_wiki")

        with pytest.raises(mcp_server.McpWikiError):
            service.read_resource("llm-wiki://entities/../User")

    def test_rejects_unsafe_page_id(self, tmp_project):
        _write_wiki(tmp_project)
        service = mcp_server.McpWikiService(src_dir=".", wiki_dir="docs/llm_wiki")

        with pytest.raises(mcp_server.McpWikiError):
            service.get_entity("../User")

    def test_search_wiki_returns_snippets_and_ignores_legacy(self, tmp_project):
        _write_wiki(tmp_project)
        service = mcp_server.McpWikiService(src_dir=".", wiki_dir="docs/llm_wiki")

        result = service.search_wiki("Primary account", limit=10)

        assert result["count"] == 1
        assert result["results"][0]["uri"] == "llm-wiki://entities/User"
        assert "Primary account" in result["results"][0]["snippet"]

    def test_search_wiki_includes_registry_surface_kinds(self, tmp_project):
        _write_wiki(tmp_project)
        service = mcp_server.McpWikiService(src_dir=".", wiki_dir="docs/llm_wiki")

        result = service.search_wiki(
            "Dependency graph", kinds=["dependencies"], limit=10
        )

        assert result["count"] == 1
        assert result["results"][0]["kind"] == "dependencies"
        assert result["results"][0]["uri"] == "llm-wiki://dependencies"

    def test_list_resources_includes_registry_pages(self, tmp_project):
        _write_wiki(tmp_project)
        service = mcp_server.McpWikiService(src_dir=".", wiki_dir="docs/llm_wiki")

        uris = {resource["uri"] for resource in service.list_resources()}

        assert "llm-wiki://flows/checkout" in uris
        assert "llm-wiki://dependencies" in uris
        assert "llm-wiki://load-order" in uris

    def test_legacy_layout_omits_absent_optional_resources(self, tmp_project):
        _write_legacy_wiki(tmp_project)
        service = mcp_server.McpWikiService(src_dir=".", wiki_dir="docs/llm_wiki")

        uris = {resource["uri"] for resource in service.list_resources()}
        status = service.get_status()

        assert "llm-wiki://flows/checkout" not in uris
        assert "llm-wiki://dependencies" not in uris
        assert status["pages"]["flows"] == 0
        assert status["pages"]["architecture_pages"] == 0

    def test_get_context_uses_existing_context_builder(self, tmp_project):
        service = mcp_server.McpWikiService(src_dir=".", wiki_dir="docs/llm_wiki")

        result = service.get_context(budget_tokens=10000, focus=["all"], format="json")

        assert result["protocol"] == "llm-wiki-context/v1"
        assert result["ok"] is True
        assert "models.py" in result["files"]

    def test_get_context_raises_mcp_error_on_extractor_failure(
        self, tmp_project, monkeypatch
    ):
        result = InventoryResult(
            {},
            {"python": ExtractorStatus("python", "failed", 1, "boom")},
        )
        monkeypatch.setattr(
            context_cmd, "get_inventory_result", lambda *args, **kwargs: result
        )
        service = mcp_server.McpWikiService(src_dir=".", wiki_dir="docs/llm_wiki")

        with pytest.raises(
            mcp_server.McpWikiError, match="python extraction failed: boom"
        ):
            service.get_context(budget_tokens=1000, focus=["all"], format="json")

    def test_check_wiki_returns_lint_report(self, tmp_project):
        _write_wiki(tmp_project)
        service = mcp_server.McpWikiService(src_dir=".", wiki_dir="docs/llm_wiki")

        result = service.check_wiki(strict=False)

        assert result["format"] == "json"
        assert result["wiki_dir"] == "docs/llm_wiki"
        assert "issues" in result

    def test_get_status_returns_structured_status(self, tmp_project):
        _write_wiki(tmp_project)
        hooks = tmp_project / ".git" / "hooks"
        hooks.mkdir(parents=True, exist_ok=True)
        (hooks / "post-commit").write_text("# LLM Wiki hook\n", encoding="utf-8")
        service = mcp_server.McpWikiService(src_dir=".", wiki_dir="docs/llm_wiki")

        result = service.get_status()

        assert result["wiki_exists"] is True
        assert result["pages"]["entities"] == 1
        assert result["pages"]["flows"] == 1
        assert result["pages"]["dependencies"] == 1
        assert result["pages"]["load-order"] == 1
        assert result["pages"]["architecture_pages"] == 2
        assert result["hooks"] == ["post-commit"]


class TestOriginSafety:
    def test_loopback_host_validation(self):
        mcp_server.validate_loopback_host("127.0.0.1")
        mcp_server.validate_loopback_host("localhost")

        with pytest.raises(mcp_server.McpWikiError):
            mcp_server.validate_loopback_host("0.0.0.0")

    def test_origin_allows_loopback_configured_port(self):
        assert mcp_server.is_origin_allowed(
            "http://127.0.0.1:8765", port=8765, allowed_origins=[]
        )
        assert mcp_server.is_origin_allowed(
            "http://localhost:8765", port=8765, allowed_origins=[]
        )
        assert not mcp_server.is_origin_allowed(
            "http://localhost:9000", port=8765, allowed_origins=[]
        )
        assert not mcp_server.is_origin_allowed(
            "https://example.com", port=8765, allowed_origins=[]
        )

    def test_origin_allows_explicit_origin(self):
        assert mcp_server.is_origin_allowed(
            "https://agent.example.com",
            port=8765,
            allowed_origins=["https://agent.example.com"],
        )

    def test_origin_validation_middleware_rejects_disallowed_origin(self):
        sent = []

        async def app(scope, receive, send):
            await send({"type": "http.response.start", "status": 200, "headers": []})
            await send({"type": "http.response.body", "body": b"ok"})

        async def send(message):
            sent.append(message)

        middleware = mcp_server.OriginValidationMiddleware(app, port=8765)
        scope = {
            "type": "http",
            "headers": [(b"origin", b"https://example.com")],
        }

        asyncio.run(middleware(scope, None, send))

        assert sent[0]["status"] == 403


class TestMcpCli:
    def test_mcp_help_does_not_require_sdk(self, monkeypatch, capsys):
        monkeypatch.setattr(sys, "argv", ["llm-wiki", "mcp", "--help"])

        with pytest.raises(SystemExit) as exc:
            cli.main()

        assert exc.value.code == 0
        assert "--transport" in capsys.readouterr().out

    def test_missing_sdk_error_is_actionable(self, tmp_project, capsys):
        if importlib.util.find_spec("mcp") is not None:
            pytest.skip("MCP SDK is installed in this environment.")

        with pytest.raises(SystemExit) as exc:
            mcp_cmd.run(_args())

        assert exc.value.code == 1
        assert "pip install 'agent-wiki-cli[mcp]'" in capsys.readouterr().err

    def test_python_version_guard(self, monkeypatch):
        monkeypatch.setattr(mcp_server.sys, "version_info", (3, 9, 0))

        with pytest.raises(mcp_server.MCPDependencyError, match="Python 3.10") as exc:
            mcp_server.ensure_mcp_runtime()

        assert "pip install 'agent-wiki-cli[mcp]'" in str(exc.value)

    def test_optional_sdk_registration_when_installed(self, tmp_project):
        if importlib.util.find_spec("mcp") is None:
            pytest.skip("MCP SDK is not installed.")
        _write_wiki(tmp_project)

        server = mcp_server.create_mcp_server(mcp_server.McpServerConfig())

        assert server is not None
