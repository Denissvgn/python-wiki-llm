"""Tests for the optional MCP server surface."""

from __future__ import annotations

import asyncio
import importlib.util
import json
import sys
import types
from pathlib import Path

import pytest

from llm_wiki_cli import cli
from llm_wiki_cli.commands import context_cmd, mcp_cmd
from llm_wiki_cli.commands.extract_cmd import ExtractorStatus, InventoryResult
from llm_wiki_cli.config import write_config
from llm_wiki_cli.services import knowledge_consumption, mcp_server
from llm_wiki_cli.services.documentation_queries import (
    DocumentationGraphQueryService,
    DocumentationQueryError,
)
from llm_wiki_cli.services.knowledge_artifacts import KNOWLEDGE_INDEX_FILENAME
from llm_wiki_cli.services.knowledge_consumption import build_knowledge_read_view
from llm_wiki_cli.services.knowledge_loader import KnowledgeLoadResult
from llm_wiki_cli.services.knowledge_model import KnowledgeLoadState
from llm_wiki_cli.services.wiki_surface_index import SURFACE_INDEX_FILENAME
from tests.knowledge_fixtures import fail_if_extraction_runs
from tests.test_knowledge_compatibility import (
    COMPATIBILITY_CASES,
    _materialize_case,
)
from tests.test_knowledge_loader import _committed_state


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


def _guard_status_extraction(monkeypatch) -> None:
    monkeypatch.setattr(
        mcp_server,
        "build_documentation_query_service",
        fail_if_extraction_runs,
    )
    monkeypatch.setattr(
        mcp_server,
        "get_inventory",
        fail_if_extraction_runs,
    )
    monkeypatch.setattr(
        mcp_server.context_cmd,
        "get_inventory_result",
        fail_if_extraction_runs,
    )
    monkeypatch.setattr(
        knowledge_consumption,
        "evaluate_knowledge_freshness",
        fail_if_extraction_runs,
    )


def _assert_snapshot_knowledge_summary(
    summary,
    *,
    availability,
    reason,
    evidence_issue_counts,
):
    assert set(summary) == {
        "availability",
        "reason",
        "concepts_evaluated",
        "freshness_counts",
        "evidence_issue_counts",
        "degraded_reason",
        "phase_durations_ms",
        "freshness_evaluated",
    }
    assert summary["availability"] == availability
    assert summary["reason"] == reason
    assert summary["concepts_evaluated"] == 0
    assert summary["freshness_counts"] is None
    assert summary["evidence_issue_counts"] == evidence_issue_counts
    assert summary["degraded_reason"] == (
        reason if availability in {"degraded", "unsupported"} else None
    )
    assert summary["freshness_evaluated"] is False
    assert set(summary["phase_durations_ms"]) == {
        "load",
        "evaluate",
        "check",
    }
    assert isinstance(summary["phase_durations_ms"]["load"], int)
    assert summary["phase_durations_ms"]["load"] >= 0
    assert summary["phase_durations_ms"]["evaluate"] is None
    assert summary["phase_durations_ms"]["check"] is None
    serialized = json.dumps(summary, sort_keys=True)
    assert "llm-wiki://" not in serialized
    assert "sha256:" not in serialized


@pytest.mark.parametrize(
    "case",
    COMPATIBILITY_CASES,
    ids=lambda case: case.id,
)
def test_mcp_knowledge_tools_and_status_share_compatibility_policy(
    tmp_path,
    monkeypatch,
    case,
):
    root = tmp_path / "checkout"
    wiki = root / "docs" / "llm_wiki"
    wiki.mkdir(parents=True)
    fixture = _materialize_case(wiki, case)
    for relative_path, content in fixture.source_files.items():
        source = root / relative_path
        source.parent.mkdir(parents=True, exist_ok=True)
        source.write_text(content, encoding="utf-8")
    monkeypatch.chdir(root)
    query_service = mcp_server.build_documentation_query_service(
        ".",
        wiki_dir="docs/llm_wiki",
    )
    calls = []

    def fake_builder(src_dir, *, wiki_dir, limit, read_only):
        calls.append((src_dir, wiki_dir, limit, read_only))
        return query_service

    monkeypatch.setattr(
        mcp_server,
        "build_documentation_query_service",
        fake_builder,
    )
    service = mcp_server.McpWikiService(
        src_dir=".",
        wiki_dir="docs/llm_wiki",
    )

    concept = service.get_concept("llm-wiki://entities/User")
    related = service.related_concepts("llm-wiki://entities/User")
    evidence = service.explain_evidence("llm-wiki://entities/User")
    status_result = service.get_status()
    status = status_result["knowledge"]

    expected_status = {
        "availability": case.expected_availability.value,
        "reason": case.expected_reason.value,
        "freshness_evaluated": case.serves_knowledge,
    }
    assert concept["knowledge"] == expected_status
    assert related["knowledge"] == expected_status
    assert evidence["knowledge"] == expected_status
    assert concept["found"] is case.serves_knowledge
    assert related["found"] is case.serves_knowledge
    assert evidence["found"] is case.serves_knowledge
    assert status == {
        **expected_status,
        "freshness_evaluated": False,
    }
    if case.expected_availability.value == "absent":
        assert "knowledge_summary" not in status_result
    else:
        _assert_snapshot_knowledge_summary(
            status_result["knowledge_summary"],
            availability=case.expected_availability.value,
            reason=case.expected_reason.value,
            evidence_issue_counts=(
                {"missing": 0, "invalid": 0, "unknown": 1}
                if case.serves_knowledge
                else None
            ),
        )
    assert calls == [
        (".", "docs/llm_wiki", 20, True),
        (".", "docs/llm_wiki", 20, True),
        (".", "docs/llm_wiki", 20, True),
    ]


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

    def test_get_flow_reads_flow_page(self, tmp_project):
        _write_wiki(tmp_project)
        service = mcp_server.McpWikiService(src_dir=".", wiki_dir="docs/llm_wiki")

        result = service.get_flow("checkout")

        assert result["kind"] == "flows"
        assert result["id"] == "checkout"
        assert result["uri"] == "llm-wiki://flows/checkout"
        assert result["path"] == "flows/checkout.md"
        assert "Checkout user flow" in result["content"]

    def test_get_flow_rejects_unsafe_page_id(self, tmp_project):
        _write_wiki(tmp_project)
        service = mcp_server.McpWikiService(src_dir=".", wiki_dir="docs/llm_wiki")

        with pytest.raises(mcp_server.McpWikiError, match="Unsafe wiki page id"):
            service.get_flow("../checkout")

    def test_get_architecture_page_reads_dependency_pages(self, tmp_project):
        _write_wiki(tmp_project)
        service = mcp_server.McpWikiService(src_dir=".", wiki_dir="docs/llm_wiki")

        dependencies = service.get_architecture_page("dependencies")
        load_order = service.get_architecture_page("load-order")

        assert dependencies["uri"] == "llm-wiki://dependencies"
        assert dependencies["path"] == "dependencies.md"
        assert "Dependency graph" in dependencies["content"]
        assert load_order["uri"] == "llm-wiki://load-order"
        assert load_order["path"] == "load-order.md"

    def test_reads_api_contracts_root_resource(self, tmp_project):
        wiki = _write_wiki(tmp_project)
        (wiki / "api-contracts.md").write_text(
            "# API contracts\n\n## Notes\n\nReviewed contract.\n",
            encoding="utf-8",
        )
        service = mcp_server.McpWikiService(src_dir=".", wiki_dir="docs/llm_wiki")

        result = service.read_resource("llm-wiki://api-contracts")

        assert result["metadata"]["kind"] == "api-contracts"
        assert result["metadata"]["path"] == "api-contracts.md"
        assert "Reviewed contract" in result["text"]

    def test_get_architecture_page_rejects_unknown_page(self, tmp_project):
        _write_wiki(tmp_project)
        service = mcp_server.McpWikiService(src_dir=".", wiki_dir="docs/llm_wiki")

        with pytest.raises(mcp_server.McpWikiError, match="Unknown architecture page"):
            service.get_architecture_page("index")

    def test_get_architecture_page_reports_missing_optional_page(self, tmp_project):
        _write_legacy_wiki(tmp_project)
        service = mcp_server.McpWikiService(src_dir=".", wiki_dir="docs/llm_wiki")

        with pytest.raises(mcp_server.McpWikiError, match="Wiki page not found"):
            service.get_architecture_page("dependencies")

    def test_resource_uri_resolution(self, tmp_project):
        wiki = _write_wiki(tmp_project)
        (wiki / "guides").mkdir()
        (wiki / "guides" / "operator-onboarding.md").write_text(
            "# Operator Onboarding\n\nGuide for operators.\n", encoding="utf-8"
        )
        service = mcp_server.McpWikiService(src_dir=".", wiki_dir="docs/llm_wiki")

        index = service.read_resource("llm-wiki://index")
        entity = service.read_resource("llm-wiki://entities/User")
        guide = service.read_resource("llm-wiki://guides/operator-onboarding")
        flow = service.read_resource("llm-wiki://flows/checkout")
        dependencies = service.read_resource("llm-wiki://dependencies")
        load_order = service.read_resource("llm-wiki://load-order")

        assert index["mimeType"] == "text/markdown"
        assert entity["metadata"]["kind"] == "entities"
        assert "Primary account entity" in entity["text"]
        assert guide["metadata"]["kind"] == "guides"
        assert guide["metadata"]["path"] == "guides/operator-onboarding.md"
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

    def test_search_wiki_accepts_all_registry_discovery_kinds(self, tmp_project):
        wiki = _write_wiki(tmp_project)
        (wiki / "guides").mkdir()
        (wiki / "guides" / "operator-onboarding.md").write_text(
            "# Operator Onboarding\n\nGuide for operators.\n", encoding="utf-8"
        )
        service = mcp_server.McpWikiService(src_dir=".", wiki_dir="docs/llm_wiki")

        cases = {
            "index": ("User", "llm-wiki://index"),
            "log": ("Created wiki", "llm-wiki://log"),
            "guides": ("Guide for operators", "llm-wiki://guides/operator-onboarding"),
            "flows": ("Checkout user flow", "llm-wiki://flows/checkout"),
            "dependencies": ("Dependency graph", "llm-wiki://dependencies"),
            "load-order": ("Initialization sequence", "llm-wiki://load-order"),
        }

        for kind, (query, expected_uri) in cases.items():
            result = service.search_wiki(query, kinds=[kind], limit=10)

            assert result["count"] == 1
            assert result["results"][0]["kind"] == kind
            assert result["results"][0]["uri"] == expected_uri

    def test_search_wiki_rejects_unknown_kind(self, tmp_project):
        _write_wiki(tmp_project)
        service = mcp_server.McpWikiService(src_dir=".", wiki_dir="docs/llm_wiki")

        with pytest.raises(mcp_server.McpWikiError, match="Unknown wiki search kind"):
            service.search_wiki("User", kinds=["unknown"], limit=10)

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

    def test_get_context_uses_existing_context_builder(self, tmp_project, capsys):
        service = mcp_server.McpWikiService(src_dir=".", wiki_dir="docs/llm_wiki")

        result = service.get_context(budget_tokens=10000, focus=["all"], format="json")

        assert result["protocol"] == "llm-wiki-context/v1"
        assert result["ok"] is True
        assert "models.py" in result["files"]
        assert "Extractor plan:" not in capsys.readouterr().err

    def test_get_context_passes_filters_and_wiki_dir_to_context_builder(
        self, tmp_project, monkeypatch
    ):
        seen = {}

        def fake_build_context(
            src_dir,
            budget,
            fmt,
            focus,
            filters,
            *,
            emit_warnings,
            wiki_dir,
        ):
            seen["args"] = (src_dir, budget, fmt, focus, filters, emit_warnings)
            seen["wiki_dir"] = wiki_dir
            return (
                {
                    "budget": budget,
                    "used": 0,
                    "files": {},
                    "graphs": {"symbol": {"callers": {"query": "run"}}},
                },
                [],
            )

        monkeypatch.setattr(context_cmd, "_build_context", fake_build_context)
        service = mcp_server.McpWikiService(src_dir="src", wiki_dir="agent_wiki")

        result = service.get_context(
            budget_tokens=1000,
            focus=["all"],
            format="json",
            filters={"symbol": "run"},
        )

        assert seen["args"] == (
            "src",
            1000,
            "json",
            ["all"],
            {"symbol": "run"},
            False,
        )
        assert seen["wiki_dir"] == "agent_wiki"
        assert result["graphs"]["symbol"]["callers"]["query"] == "run"

    def test_get_context_passes_knowledge_refinements_and_preserves_results(
        self,
        monkeypatch,
    ):
        refinements = {
            "surface": "entities",
            "freshness": "source-changed",
            "evidence": "present",
        }
        status = {
            "availability": "ready",
            "reason": "all-projection-commitments-match",
            "freshness_evaluated": True,
        }
        seen = {}

        def fake_build_context(
            src_dir,
            budget,
            fmt,
            focus,
            filters,
            **kwargs,
        ):
            seen.update(
                {
                    "src_dir": src_dir,
                    "budget": budget,
                    "format": fmt,
                    "focus": focus,
                    "filters": filters,
                    "wiki_dir": kwargs["wiki_dir"],
                }
            )
            return (
                {
                    "budget": budget,
                    "used": 0,
                    "files": {},
                    "knowledge": status,
                    "surface": {
                        "kind": "entities",
                        "count": 1,
                        "total": 1,
                        "truncated": False,
                        "knowledge_selection": {
                            "unfiltered_total": 2,
                            "filtered_total": 1,
                            "returned": 1,
                            "truncated": False,
                        },
                        "pages": [
                            {
                                "canonical_path": "entities/User.md",
                                "mcp_uri": "llm-wiki://entities/User",
                                "knowledge": {
                                    **status,
                                    "evidence": "present",
                                    "freshness": {
                                        "state": "source-changed",
                                        "reason": "concept-observation-changed",
                                        "live_comparison_performed": True,
                                    },
                                },
                            }
                        ],
                    },
                },
                ["Knowledge context includes stale concept references."],
            )

        monkeypatch.setattr(context_cmd, "_build_context", fake_build_context)
        service = mcp_server.McpWikiService(
            src_dir="source-root",
            wiki_dir="agent_wiki",
        )

        result = service.get_context(
            budget_tokens=4096,
            focus=["all"],
            format="json",
            filters=refinements,
        )

        assert seen == {
            "src_dir": "source-root",
            "budget": 4096,
            "format": "json",
            "focus": ["all"],
            "filters": refinements,
            "wiki_dir": "agent_wiki",
        }
        assert result["protocol"] == "llm-wiki-context/v1"
        assert result["filters"] == refinements
        assert result["knowledge"] == status
        assert result["surface"]["knowledge_selection"]["unfiltered_total"] == 2
        assert result["surface"]["knowledge_selection"]["filtered_total"] == 1
        assert result["surface"]["pages"][0]["knowledge"]["freshness"]["state"] == (
            "source-changed"
        )
        assert result["warnings"] == [
            "Knowledge context includes stale concept references."
        ]

    @pytest.mark.parametrize(
        ("filters", "field"),
        [
            ({"freshness": "current"}, "freshness"),
            ({"evidence": "present"}, "evidence"),
        ],
    )
    def test_get_context_maps_knowledge_refinement_dependency_errors(
        self,
        filters,
        field,
    ):
        service = mcp_server.McpWikiService()

        with pytest.raises(
            mcp_server.McpWikiError,
            match=rf"filters\.{field} requires filters\.surface or filters\.symbol",
        ):
            service.get_context(filters=filters)

    def test_get_context_markdown_preserves_knowledge_status_and_warnings(
        self,
        monkeypatch,
    ):
        status = {
            "availability": "degraded",
            "reason": "policy-selected-surface-only-fallback-after-invalid",
            "freshness_evaluated": False,
        }

        def fake_build_context(
            _src_dir,
            budget,
            _fmt,
            _focus,
            _filters,
            **_kwargs,
        ):
            return (
                {
                    "budget": budget,
                    "used": 0,
                    "files": {},
                    "knowledge": status,
                },
                ["Knowledge context is degraded; no candidates were dropped."],
            )

        monkeypatch.setattr(context_cmd, "_build_context", fake_build_context)
        service = mcp_server.McpWikiService()

        result = service.get_context(
            format="markdown",
            filters={"surface": "entities"},
        )

        assert result["protocol"] == "llm-wiki-context/v1"
        assert result["knowledge"] == status
        assert result["warnings"] == [
            "Knowledge context is degraded; no candidates were dropped."
        ]
        assert "## Knowledge" in result["content"]
        assert "- availability: degraded" in result["content"]

    def test_get_context_legacy_response_remains_context_v1(
        self,
        monkeypatch,
    ):
        def fake_build_context(_src_dir, budget, _fmt, _focus, _filters, **_kwargs):
            return (
                {
                    "budget": budget,
                    "used": 0,
                    "files": {},
                },
                [],
            )

        monkeypatch.setattr(context_cmd, "_build_context", fake_build_context)
        service = mcp_server.McpWikiService()

        result = service.get_context(
            budget_tokens=1000,
            focus=["all"],
            format="json",
        )

        assert result == {
            "protocol": "llm-wiki-context/v1",
            "ok": True,
            "budget_tokens": 1000,
            "used_tokens": 0,
            "format": "json",
            "focus": ["all"],
            "filters": {},
            "files": {},
        }

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

    def test_check_wiki_returns_lint_report(self, tmp_project, capsys):
        _write_wiki(tmp_project)
        service = mcp_server.McpWikiService(src_dir=".", wiki_dir="docs/llm_wiki")

        result = service.check_wiki(strict=False)

        assert result["format"] == "json"
        assert result["wiki_dir"] == "docs/llm_wiki"
        assert "issues" in result
        assert "execution" not in result
        assert "Extractor plan:" not in capsys.readouterr().err

    def test_get_status_returns_structured_status(self, tmp_project):
        _write_wiki(tmp_project)
        hooks = tmp_project / ".git" / "hooks"
        hooks.mkdir(parents=True, exist_ok=True)
        (hooks / "post-commit").write_text("# LLM Wiki hook\n", encoding="utf-8")
        service = mcp_server.McpWikiService(src_dir=".", wiki_dir="docs/llm_wiki")

        result = service.get_status()

        assert result["wiki_exists"] is True
        assert result["pages"]["entities"] == 1
        assert result["pages"]["index"] == 1
        assert result["pages"]["log"] == 1
        assert result["pages"]["modules"] == 1
        assert result["pages"]["workflows"] == 1
        assert result["pages"]["guides"] == 0
        assert result["pages"]["flows"] == 1
        assert result["pages"]["infrastructure"] == 1
        assert result["pages"]["dependencies"] == 1
        assert result["pages"]["load-order"] == 1
        assert result["pages"]["architecture_pages"] == 2
        assert result["hooks"] == ["post-commit"]

    def test_get_status_reports_ready_snapshot_without_live_extraction(
        self,
        tmp_project,
        monkeypatch,
    ):
        wiki = tmp_project / "docs" / "llm_wiki"
        _committed_state(wiki)
        _guard_status_extraction(monkeypatch)
        service = mcp_server.McpWikiService(
            src_dir=".",
            wiki_dir="docs/llm_wiki",
        )

        result = service.get_status()

        assert result["knowledge"] == {
            "availability": "ready",
            "reason": "all-projection-commitments-match",
            "freshness_evaluated": False,
        }
        _assert_snapshot_knowledge_summary(
            result["knowledge_summary"],
            availability="ready",
            reason="all-projection-commitments-match",
            evidence_issue_counts={
                "missing": 0,
                "invalid": 0,
                "unknown": 1,
            },
        )

    def test_get_status_reports_legacy_absence_without_extraction(
        self,
        tmp_project,
        monkeypatch,
    ):
        _write_legacy_wiki(tmp_project)
        _guard_status_extraction(monkeypatch)
        service = mcp_server.McpWikiService(
            src_dir=".",
            wiki_dir="docs/llm_wiki",
        )

        result = service.get_status()

        assert result["knowledge"] == {
            "availability": "absent",
            "reason": "knowledge-projection-not-present",
            "freshness_evaluated": False,
        }
        assert "knowledge_summary" not in result

    def test_get_status_does_not_read_legacy_markdown_for_knowledge(
        self,
        tmp_project,
        monkeypatch,
    ):
        wiki = _write_legacy_wiki(tmp_project)
        (wiki / "entities" / "User.md").write_bytes(b"\xff")
        _guard_status_extraction(monkeypatch)
        service = mcp_server.McpWikiService(
            src_dir=".",
            wiki_dir="docs/llm_wiki",
        )

        result = service.get_status()

        assert result["knowledge"] == {
            "availability": "absent",
            "reason": "knowledge-projection-not-present",
            "freshness_evaluated": False,
        }
        assert "knowledge_summary" not in result

    def test_get_status_preserves_missing_wiki_status_without_extraction(
        self,
        tmp_project,
        monkeypatch,
    ):
        _guard_status_extraction(monkeypatch)
        service = mcp_server.McpWikiService(
            src_dir=".",
            wiki_dir="docs/missing_wiki",
        )

        result = service.get_status()

        assert result["wiki_exists"] is False
        assert result["knowledge"] == {
            "availability": "absent",
            "reason": "knowledge-projection-not-present",
            "freshness_evaluated": False,
        }
        assert "knowledge_summary" not in result

    def test_get_status_reports_degraded_snapshot_without_extraction(
        self,
        tmp_project,
        monkeypatch,
    ):
        wiki = tmp_project / "docs" / "llm_wiki"
        _committed_state(wiki)
        (wiki / KNOWLEDGE_INDEX_FILENAME).write_bytes(b"{not-json\n")
        _guard_status_extraction(monkeypatch)
        service = mcp_server.McpWikiService(
            src_dir=".",
            wiki_dir="docs/llm_wiki",
        )

        result = service.get_status()

        assert result["knowledge"] == {
            "availability": "degraded",
            "reason": "policy-selected-surface-only-fallback-after-invalid",
            "freshness_evaluated": False,
        }
        _assert_snapshot_knowledge_summary(
            result["knowledge_summary"],
            availability="degraded",
            reason="policy-selected-surface-only-fallback-after-invalid",
            evidence_issue_counts=None,
        )

    def test_get_status_reports_unsupported_snapshot_without_extraction(
        self,
        tmp_project,
        monkeypatch,
    ):
        wiki = tmp_project / "docs" / "llm_wiki"
        _committed_state(wiki)
        knowledge_path = wiki / KNOWLEDGE_INDEX_FILENAME
        payload = json.loads(knowledge_path.read_text(encoding="utf-8"))
        payload["schema_version"] = "llm-wiki-knowledge/v999"
        knowledge_path.write_text(
            json.dumps(payload, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        _guard_status_extraction(monkeypatch)
        service = mcp_server.McpWikiService(
            src_dir=".",
            wiki_dir="docs/llm_wiki",
        )

        result = service.get_status()

        assert result["knowledge"] == {
            "availability": "unsupported",
            "reason": "knowledge-schema-version-unsupported",
            "freshness_evaluated": False,
        }
        _assert_snapshot_knowledge_summary(
            result["knowledge_summary"],
            availability="unsupported",
            reason="knowledge-schema-version-unsupported",
            evidence_issue_counts=None,
        )

    def test_get_status_uses_live_surface_fallback_for_missing_projection_surface(
        self,
        tmp_project,
        monkeypatch,
    ):
        wiki = tmp_project / "docs" / "llm_wiki"
        _committed_state(wiki)
        (wiki / SURFACE_INDEX_FILENAME).unlink()
        _guard_status_extraction(monkeypatch)
        service = mcp_server.McpWikiService(
            src_dir=".",
            wiki_dir="docs/llm_wiki",
        )

        result = service.get_status()

        assert result["knowledge"] == {
            "availability": "degraded",
            "reason": "policy-selected-surface-only-fallback-after-invalid",
            "freshness_evaluated": False,
        }
        _assert_snapshot_knowledge_summary(
            result["knowledge_summary"],
            availability="degraded",
            reason="policy-selected-surface-only-fallback-after-invalid",
            evidence_issue_counts=None,
        )

    def test_get_status_adds_issue_reporting_preference(self, tmp_project):
        _write_wiki(tmp_project)
        write_config(
            "docs/llm_wiki",
            {
                "agent": "copilot",
                "quality_hints": True,
                "reference_skill": True,
                "issue_reporting": True,
            },
        )
        service = mcp_server.McpWikiService(src_dir=".", wiki_dir="docs/llm_wiki")

        result = service.get_status()

        assert result["agent"]["configured"] is True
        assert result["agent"]["issue_reporting"] is True

    def test_query_graph_dispatches_to_documentation_query_service(
        self, tmp_project, monkeypatch
    ):
        seen = {}

        class FakeQueryService:
            def __init__(self, limit):
                self.limit = limit

            def flow_for_entrypoint(self, value):
                seen["flow"] = (value, self.limit)
                return {"query": value, "found": True, "flow": {"id": value}}

        def fake_builder(src_dir, *, wiki_dir, limit):
            seen["builder"] = (src_dir, wiki_dir, limit)
            return FakeQueryService(limit)

        monkeypatch.setattr(
            mcp_server, "build_documentation_query_service", fake_builder
        )
        service = mcp_server.McpWikiService(src_dir="src", wiki_dir="wiki")

        result = service.query_graph(
            {"type": "flow_for_entrypoint", "value": "api-run", "limit": 250}
        )

        assert result == {"query": "api-run", "found": True, "flow": {"id": "api-run"}}
        assert seen["builder"] == ("src", "wiki", 100)
        assert seen["flow"] == ("api-run", 100)

    @pytest.mark.parametrize(
        ("query", "message"),
        [
            ({}, "type must be a non-empty string"),
            ({"type": "missing", "value": "x"}, "Unknown graph query type"),
            ({"type": "callers", "value": ""}, "value must be a non-empty string"),
            (
                {"type": "callers", "value": "run", "limit": 0},
                "limit must be a positive integer",
            ),
            ("callers run", "query must be an object"),
        ],
    )
    def test_query_graph_validates_structured_request(
        self, tmp_project, monkeypatch, query, message
    ):
        def fail_if_built(*args, **kwargs):  # pragma: no cover - assertion helper
            raise AssertionError("invalid graph queries must not build a service")

        monkeypatch.setattr(
            mcp_server, "build_documentation_query_service", fail_if_built
        )
        service = mcp_server.McpWikiService(src_dir=".", wiki_dir="docs/llm_wiki")

        with pytest.raises(mcp_server.McpWikiError, match=message):
            service.query_graph(query)

    def test_query_graph_maps_query_service_errors(self, tmp_project, monkeypatch):
        def fake_builder(*args, **kwargs):
            raise mcp_server.LlmWikiApiError("bad graph request")

        monkeypatch.setattr(
            mcp_server, "build_documentation_query_service", fake_builder
        )
        service = mcp_server.McpWikiService(src_dir=".", wiki_dir="docs/llm_wiki")

        with pytest.raises(mcp_server.McpWikiError, match="bad graph request"):
            service.query_graph({"type": "callers", "value": "run"})

    def test_knowledge_methods_delegate_once_and_cap_external_limit(
        self,
        monkeypatch,
    ):
        calls = {"builder": [], "query": []}
        concept_result = {
            "query": "llm-wiki://entities/User",
            "found": True,
        }
        bounded_result = {
            "total": 101,
            "returned": 100,
            "truncated": True,
        }

        class FakeQueryService:
            def get_concept(self, locator):
                calls["query"].append(("get_concept", locator))
                return concept_result

            def related_concepts(
                self,
                locator,
                *,
                direction,
                kinds,
            ):
                calls["query"].append(
                    ("related_concepts", locator, direction, kinds)
                )
                return bounded_result

            def explain_evidence(self, locator):
                calls["query"].append(("explain_evidence", locator))
                return bounded_result

        query_service = FakeQueryService()

        def fake_builder(src_dir, *, wiki_dir, limit, read_only):
            calls["builder"].append((src_dir, wiki_dir, limit, read_only))
            return query_service

        monkeypatch.setattr(
            mcp_server,
            "build_documentation_query_service",
            fake_builder,
        )
        monkeypatch.setattr(
            mcp_server,
            "get_inventory",
            fail_if_extraction_runs,
        )
        service = mcp_server.McpWikiService(
            src_dir="source-root",
            wiki_dir="agent_wiki",
        )

        concept = service.get_concept(
            "  llm-wiki://entities/User  ",
            limit=250,
        )
        related = service.related_concepts(
            " entities/User.md ",
            direction="outbound",
            kinds=["links_to"],
            limit=250,
        )
        evidence = service.explain_evidence(
            " llm-wiki://entities/User ",
            limit=250,
        )

        assert concept is concept_result
        assert related is bounded_result
        assert evidence is bounded_result
        assert calls["builder"] == [
            ("source-root", "agent_wiki", 100, True),
            ("source-root", "agent_wiki", 100, True),
            ("source-root", "agent_wiki", 100, True),
        ]
        assert calls["query"] == [
            ("get_concept", "llm-wiki://entities/User"),
            (
                "related_concepts",
                "entities/User.md",
                "outbound",
                ["links_to"],
            ),
            ("explain_evidence", "llm-wiki://entities/User"),
        ]
        assert related == {
            "total": 101,
            "returned": 100,
            "truncated": True,
        }

    @pytest.mark.parametrize(
        ("method_name", "args", "kwargs", "message"),
        [
            (
                "get_concept",
                (None,),
                {},
                "locator_or_exact_route must be a non-empty string",
            ),
            (
                "get_concept",
                ("llm-wiki://entities/User",),
                {"limit": True},
                "limit must be a positive integer",
            ),
            (
                "related_concepts",
                ("llm-wiki://entities/User",),
                {"direction": "sideways"},
                "direction must be one of",
            ),
            (
                "related_concepts",
                ("llm-wiki://entities/User",),
                {"kinds": "links_to"},
                "kinds",
            ),
            (
                "related_concepts",
                ("llm-wiki://entities/User",),
                {"kinds": [1]},
                "kinds",
            ),
            (
                "related_concepts",
                ("llm-wiki://entities/User",),
                {"kinds": ["structural"]},
                "unsupported relationship kind",
            ),
            (
                "explain_evidence",
                ("llm-wiki://entities/User",),
                {"limit": 0},
                "limit must be a positive integer",
            ),
        ],
    )
    def test_knowledge_methods_validate_before_building_query_service(
        self,
        monkeypatch,
        method_name,
        args,
        kwargs,
        message,
    ):
        monkeypatch.setattr(
            mcp_server,
            "build_documentation_query_service",
            fail_if_extraction_runs,
        )
        service = mcp_server.McpWikiService()

        with pytest.raises(mcp_server.McpWikiError, match=message):
            getattr(service, method_name)(*args, **kwargs)

    @pytest.mark.parametrize(
        "method_name",
        ["get_concept", "related_concepts", "explain_evidence"],
    )
    @pytest.mark.parametrize("failure_point", ["builder", "query"])
    def test_knowledge_methods_map_api_and_query_errors(
        self,
        monkeypatch,
        method_name,
        failure_point,
    ):
        class FailingQueryService:
            def get_concept(self, _locator):
                raise DocumentationQueryError("bad knowledge query")

            def related_concepts(
                self,
                _locator,
                *,
                direction,
                kinds,
            ):
                del direction, kinds
                raise DocumentationQueryError("bad knowledge query")

            def explain_evidence(self, _locator):
                raise DocumentationQueryError("bad knowledge query")

        def fake_builder(*_args, **_kwargs):
            if failure_point == "builder":
                raise mcp_server.LlmWikiApiError("bad knowledge query")
            return FailingQueryService()

        monkeypatch.setattr(
            mcp_server,
            "build_documentation_query_service",
            fake_builder,
        )
        service = mcp_server.McpWikiService()
        kwargs = (
            {"direction": "both", "kinds": None}
            if method_name == "related_concepts"
            else {}
        )

        with pytest.raises(
            mcp_server.McpWikiError,
            match="bad knowledge query",
        ):
            getattr(service, method_name)(
                "llm-wiki://entities/User",
                **kwargs,
            )

    @pytest.mark.parametrize(
        ("load_result", "availability", "reason"),
        [
            (
                KnowledgeLoadResult(
                    status=KnowledgeLoadState.ABSENT,
                    surface={},
                    knowledge=None,
                    manifest_basis=None,
                ),
                "absent",
                "knowledge-projection-not-present",
            ),
            (
                KnowledgeLoadResult(
                    status=KnowledgeLoadState.DEGRADED,
                    surface={},
                    knowledge=None,
                    manifest_basis=None,
                    underlying_status=KnowledgeLoadState.INVALID,
                ),
                "degraded",
                "policy-selected-surface-only-fallback-after-invalid",
            ),
        ],
    )
    def test_knowledge_methods_preserve_non_ready_status_without_extraction(
        self,
        monkeypatch,
        load_result,
        availability,
        reason,
    ):
        view = build_knowledge_read_view(load_result)
        query_service = DocumentationGraphQueryService(
            {},
            knowledge_view=view,
        )
        calls = []

        def fake_builder(src_dir, *, wiki_dir, limit, read_only):
            calls.append((src_dir, wiki_dir, limit, read_only))
            return query_service

        monkeypatch.setattr(
            mcp_server,
            "build_documentation_query_service",
            fake_builder,
        )
        monkeypatch.setattr(
            mcp_server,
            "get_inventory",
            fail_if_extraction_runs,
        )
        service = mcp_server.McpWikiService()

        concept = service.get_concept("llm-wiki://entities/User")
        related = service.related_concepts(
            "llm-wiki://entities/User",
            direction="outbound",
            kinds=["links_to"],
        )
        evidence = service.explain_evidence("llm-wiki://entities/User")

        status = {
            "availability": availability,
            "reason": reason,
            "freshness_evaluated": False,
        }
        assert concept["knowledge"] == status
        assert concept["found"] is False
        assert concept["concept"] is None
        assert related["knowledge"] == status
        assert related["found"] is False
        assert related["relationships"] == []
        assert evidence["knowledge"] == status
        assert evidence["found"] is False
        assert evidence["evidence"] is None
        assert calls == [
            (".", "docs/llm_wiki", 20, True),
            (".", "docs/llm_wiki", 20, True),
            (".", "docs/llm_wiki", 20, True),
        ]


class RecordingMcpServer:
    def __init__(self):
        self.tool_names: list[str] = []
        self.resource_uris: list[str] = []

    def tool(self):
        def decorator(func):
            self.tool_names.append(func.__name__)
            return func

        return decorator

    def resource(self, uri):
        def decorator(func):
            self.resource_uris.append(uri)
            return func

        return decorator


def test_tool_registration_names_without_sdk(tmp_project):
    server = RecordingMcpServer()
    service = mcp_server.McpWikiService(src_dir=".", wiki_dir="docs/llm_wiki")

    mcp_server._register_mcp_tools(server, service)

    assert server.tool_names == [
        "get_entity",
        "get_module",
        "get_flow",
        "get_architecture_page",
        "query_graph",
        "get_concept",
        "related_concepts",
        "explain_evidence",
        "search_wiki",
        "get_context",
        "check_wiki",
        "get_status",
    ]


def test_tool_registration_preserves_legacy_tools_and_adds_m4_tools(tmp_project):
    server = RecordingMcpServer()
    service = mcp_server.McpWikiService(src_dir=".", wiki_dir="docs/llm_wiki")

    mcp_server._register_mcp_tools(server, service)

    assert {
        "get_entity",
        "get_module",
        "search_wiki",
        "get_context",
        "check_wiki",
        "get_status",
    } <= set(server.tool_names)
    assert {"get_flow", "get_architecture_page", "query_graph"} <= set(
        server.tool_names
    )
    assert {"get_concept", "related_concepts", "explain_evidence"} <= set(
        server.tool_names
    )


def test_resource_registration_preserves_legacy_resources_and_adds_m4_resources(
    tmp_project,
):
    server = RecordingMcpServer()
    service = mcp_server.McpWikiService(src_dir=".", wiki_dir="docs/llm_wiki")

    mcp_server._register_mcp_resources(server, service)

    assert {
        "llm-wiki://index",
        "llm-wiki://log",
        "llm-wiki://entities/{page_id}",
        "llm-wiki://modules/{page_id}",
        "llm-wiki://workflows/{page_id}",
        "llm-wiki://guides/{page_id}",
    } <= set(server.resource_uris)
    assert {
        "llm-wiki://flows/{page_id}",
        "llm-wiki://infrastructure/{page_id}",
        "llm-wiki://dependencies",
        "llm-wiki://load-order",
    } <= set(server.resource_uris)


def test_mcp_graph_validation_errors_remain_structured_mcp_errors(tmp_project):
    service = mcp_server.McpWikiService(src_dir=".", wiki_dir="docs/llm_wiki")

    with pytest.raises(mcp_server.McpWikiError) as exc_info:
        service.query_graph({"type": "callers", "value": ""})

    assert "value must be a non-empty string" in str(exc_info.value)


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
