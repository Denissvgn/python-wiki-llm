"""Tests for the optional MCP server surface."""

from __future__ import annotations

import asyncio
import importlib.util
import json
import os
import sys
import types
from pathlib import Path

import pytest

from llm_wiki_cli import cli
from llm_wiki_cli.commands import context_cmd, mcp_cmd
from llm_wiki_cli.commands.extract_cmd import ExtractorStatus, InventoryResult
from llm_wiki_cli.config import write_config
from llm_wiki_cli.services import (
    context_packet as context_packet_service,
    knowledge_consumption,
    mcp_server,
)
from llm_wiki_cli.services.documentation_queries import (
    DocumentationGraphQueryService,
    DocumentationQueryError,
)
from llm_wiki_cli.services.knowledge_artifacts import (
    KNOWLEDGE_INDEX_FILENAME,
    commit_knowledge_artifacts,
)
from llm_wiki_cli.services.knowledge_consumption import build_knowledge_read_view
from llm_wiki_cli.services.knowledge_loader import KnowledgeLoadResult
from llm_wiki_cli.services.knowledge_model import KnowledgeLoadState
from llm_wiki_cli.services.knowledge_observability import (
    BASIS_INCOMPATIBLE_HINTS,
)
from llm_wiki_cli.services.source_selection import (
    SOURCE_SELECTION_SCHEMA_VERSION,
    resolve_source_selection,
    with_source_selection_generation_input,
)
from llm_wiki_cli.services.source_snapshot import build_source_snapshot
from llm_wiki_cli.services.sync_manifest import SyncManifest
from llm_wiki_cli.services.wiki_surface_index import SURFACE_INDEX_FILENAME
from tests.knowledge_fixtures import (
    fail_if_extraction_runs,
    materialize_fixture_tree,
    one_module_two_entities_fixture,
)
from tests.test_knowledge_artifacts import _plan as _knowledge_commit_plan
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


def _write_selection_profile(path: Path, include: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "schema_version": SOURCE_SELECTION_SCHEMA_VERSION,
                "include": [include],
                "exclude": [],
            }
        ),
        encoding="utf-8",
    )


def _guard_status_extraction(monkeypatch) -> None:
    monkeypatch.setattr(
        mcp_server,
        "build_documentation_query_service",
        fail_if_extraction_runs,
    )
    monkeypatch.setattr(
        mcp_server,
        "get_inventory_result",
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
        "freshness",
        "concepts_evaluated",
        "freshness_counts",
        "evidence_issue_counts",
        "degraded_reason",
        "phase_durations_ms",
        "freshness_evaluated",
    }
    assert summary["availability"] == availability
    assert summary["reason"] == reason
    assert summary["freshness"] == "unevaluated (snapshot-only read)"
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
        "freshness": (
            "evaluated (6 concepts)"
            if case.serves_knowledge
            else "unevaluated (snapshot-only read)"
        ),
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
        "freshness": "unevaluated (snapshot-only read)",
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
    @pytest.mark.parametrize(
        ("method_name", "args"),
        [
            ("get_entity", ("User",)),
            ("get_module", ("models",)),
            ("get_flow", ("checkout",)),
            ("get_architecture_page", ("dependencies",)),
            ("search_wiki", ("User",)),
            ("read_resource", ("llm-wiki://entities/User",)),
            ("list_resources", ()),
        ],
    )
    def test_direct_wiki_reads_reject_stale_persisted_selection(
        self,
        tmp_path,
        method_name,
        args,
    ):
        source = tmp_path / "source"
        (source / "selected-a").mkdir(parents=True)
        (source / "selected-b").mkdir()
        (source / "selected-a" / "app.py").write_text(
            "VALUE = 1\n", encoding="utf-8"
        )
        (source / "selected-b" / "app.py").write_text(
            "VALUE = 2\n", encoding="utf-8"
        )
        profile_a = source / "config" / "a.json"
        profile_b = source / "config" / "b.json"
        _write_selection_profile(profile_a, "selected-a")
        _write_selection_profile(profile_b, "selected-b")
        policy_a = resolve_source_selection(source, "config/a.json")
        assert policy_a is not None
        snapshot_a = build_source_snapshot(source, selection_policy=policy_a)
        wiki = _write_wiki(tmp_path)
        SyncManifest(
            generation_inputs=with_source_selection_generation_input(
                {},
                snapshot_a.source_selection_identity,
                snapshot_a.source_selection_inputs,
            )
        ).save(wiki)
        service = mcp_server.McpWikiService(
            src_dir=str(source),
            wiki_dir=str(wiki),
            source_selection="config/b.json",
        )

        with pytest.raises(mcp_server.McpWikiError, match="llm-wiki sync"):
            getattr(service, method_name)(*args)

    def test_default_profile_path_is_pinned_for_downstream_reads(
        self,
        tmp_path,
        monkeypatch,
    ):
        source = tmp_path / "source"
        (source / "selected").mkdir(parents=True)
        (source / "selected" / "app.py").write_text(
            "VALUE = 1\n", encoding="utf-8"
        )
        profile = source / ".llm-wiki" / "source-selection.json"
        _write_selection_profile(profile, "selected")
        policy = resolve_source_selection(source)
        assert policy is not None
        snapshot = build_source_snapshot(source, selection_policy=policy)
        wiki = tmp_path / "wiki"
        wiki.mkdir()
        SyncManifest(
            generation_inputs=with_source_selection_generation_input(
                {},
                snapshot.source_selection_identity,
                snapshot.source_selection_inputs,
            )
        ).save(wiki)
        overrides = []
        default_reads = 0

        def sequenced_resolver(root, override=None):
            nonlocal default_reads
            del root
            overrides.append(override)
            if override is None:
                default_reads += 1
                return policy if default_reads <= 2 else None
            assert str(override) == policy.path
            return policy

        class QueryService:
            @staticmethod
            def callers(value):
                return {"value": value}

        def fake_builder(_src_dir, **kwargs):
            downstream = sequenced_resolver(
                source,
                kwargs.get("source_selection"),
            )
            assert downstream is policy
            return QueryService()

        monkeypatch.setattr(
            mcp_server,
            "resolve_source_selection",
            sequenced_resolver,
        )
        monkeypatch.setattr(
            mcp_server,
            "build_documentation_query_service",
            fake_builder,
        )
        service = mcp_server.McpWikiService(
            src_dir=str(source),
            wiki_dir=str(wiki),
        )

        assert service.query_graph({"type": "callers", "value": "run"}) == {
            "value": "run"
        }
        assert overrides == [None, None, policy.path]

    @pytest.mark.parametrize("change", ("mutation", "removal", "addition"))
    def test_source_selection_is_pinned_for_server_lifetime(
        self,
        tmp_path,
        monkeypatch,
        change,
    ):
        source = tmp_path / "source"
        (source / "selected").mkdir(parents=True)
        (source / "alternate").mkdir()
        (source / "selected" / "app.py").write_text("VALUE = 1\n", encoding="utf-8")
        (source / "alternate" / "app.py").write_text("VALUE = 2\n", encoding="utf-8")

        def write_policy(path, include):
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(
                json.dumps(
                    {
                        "schema_version": SOURCE_SELECTION_SCHEMA_VERSION,
                        "include": [include],
                        "exclude": [],
                    }
                ),
                encoding="utf-8",
            )

        if change == "addition":
            profile = source / ".llm-wiki" / "source-selection.json"
            source_selection = None
        else:
            profile = source / "config" / "selection.json"
            write_policy(profile, "selected")
            source_selection = "config/selection.json"
        service = mcp_server.McpWikiService(
            src_dir=str(source),
            wiki_dir=str(tmp_path / "wiki"),
            source_selection=source_selection,
        )
        monkeypatch.setattr(
            mcp_server,
            "build_documentation_query_service",
            lambda *args, **kwargs: pytest.fail(
                "query builder must not run after selection drift"
            ),
        )

        if change == "mutation":
            write_policy(profile, "alternate")
        elif change == "removal":
            profile.unlink()
        else:
            write_policy(profile, "selected")

        with pytest.raises(mcp_server.McpWikiError, match="changed during"):
            service.query_graph({"type": "callers", "value": "run"})

    def test_external_source_authorization_reaches_all_guarded_mcp_reads(
        self,
        tmp_path,
        monkeypatch,
    ):
        source = tmp_path / "external-source"
        source.mkdir()
        calls = []

        class QueryService:
            def callers(self, value):
                return {"value": value}

            def get_concept(self, value):
                return {"value": value}

        def fake_query_builder(src_dir, **kwargs):
            calls.append(("query", src_dir, kwargs))
            return QueryService()

        def fake_context_builder(src_dir, *args, **kwargs):
            calls.append(("context", src_dir, kwargs))
            return ({"budget": args[0], "used": 0, "files": {}}, [])

        class Packet:
            packet_id = "sha256:" + "0" * 64

            def to_payload(self):
                return {"external": True}

        def fake_packet_builder(src_dir, wiki_dir, request, **kwargs):
            calls.append(("packet", src_dir, kwargs))
            return Packet()

        monkeypatch.setattr(
            mcp_server,
            "build_documentation_query_service",
            fake_query_builder,
        )
        monkeypatch.setattr(context_cmd, "_build_context", fake_context_builder)
        monkeypatch.setattr(
            context_packet_service,
            "build_qualified_context",
            fake_packet_builder,
        )
        service = mcp_server.McpWikiService(
            src_dir=str(source),
            wiki_dir=str(tmp_path / "wiki"),
            allow_external_src=True,
        )

        service.query_graph({"type": "callers", "value": "run"})
        service.get_concept("llm-wiki://entities/User")
        service.get_context()
        service.get_context_packet()

        assert [name for name, _, _ in calls] == [
            "query",
            "query",
            "context",
            "packet",
        ]
        assert all(Path(src_dir) == source for _, src_dir, _ in calls)
        assert all(options["allow_external_src"] is True for _, _, options in calls)

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

        assert result["total"] == 1
        assert result["returned"] == 1
        assert result["count"] == 1
        assert result["truncated"] is False
        assert result["bounds"]["results"] == {
            "total": 1,
            "returned": 1,
            "truncated": False,
        }
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

    def test_search_wiki_empty_result_has_exact_zero_bounds(self, tmp_project):
        _write_wiki(tmp_project)
        service = mcp_server.McpWikiService(src_dir=".", wiki_dir="docs/llm_wiki")

        result = service.search_wiki(
            "phrase absent from every page",
            kinds=["entities"],
            limit=10,
        )

        assert result["results"] == []
        assert result["total"] == result["returned"] == result["count"] == 0
        assert result["truncated"] is False
        assert result["bounds"]["results"] == {
            "total": 0,
            "returned": 0,
            "truncated": False,
        }

    @pytest.mark.parametrize(
        ("requested_limit", "expected_count"),
        [(None, 20), (250, 100)],
    )
    def test_search_wiki_bounds_results_and_discloses_truncation(
        self,
        tmp_project,
        requested_limit,
        expected_count,
    ):
        wiki = _write_wiki(tmp_project)
        for index in range(101):
            (wiki / "entities" / f"Match{index:03}.md").write_text(
                f"# Match {index}\n\nBounded search fixture.\n",
                encoding="utf-8",
            )
        service = mcp_server.McpWikiService(src_dir=".", wiki_dir="docs/llm_wiki")

        options = {} if requested_limit is None else {"limit": requested_limit}
        result = service.search_wiki(
            "Bounded search fixture",
            kinds=["entities"],
            **options,
        )

        assert result["total"] == 101
        assert result["returned"] == expected_count
        assert result["count"] == expected_count
        assert len(result["results"]) == expected_count
        assert result["truncated"] is True
        assert result["bounds"]["results"] == {
            "total": 101,
            "returned": expected_count,
            "truncated": True,
        }

    def test_search_wiki_exact_limit_is_not_truncated(self, tmp_project):
        wiki = _write_wiki(tmp_project)
        for index in range(3):
            (wiki / "entities" / f"Exact{index}.md").write_text(
                f"# Exact {index}\n\nExact bound fixture.\n",
                encoding="utf-8",
            )
        service = mcp_server.McpWikiService(src_dir=".", wiki_dir="docs/llm_wiki")

        result = service.search_wiki(
            "Exact bound fixture",
            kinds=["entities"],
            limit=3,
        )

        assert result["total"] == result["returned"] == result["count"] == 3
        assert result["truncated"] is False
        assert result["bounds"]["results"] == {
            "total": 3,
            "returned": 3,
            "truncated": False,
        }

    def test_search_wiki_scans_after_limit_and_surfaces_late_read_errors(
        self,
        tmp_project,
        monkeypatch,
    ):
        wiki = _write_wiki(tmp_project)
        (wiki / "entities" / "AFirst.md").write_text(
            "# First\n\nLate read fixture.\n",
            encoding="utf-8",
        )
        (wiki / "entities" / "BSecond.md").write_text(
            "# Second\n\nLate read fixture.\n",
            encoding="utf-8",
        )
        original_read_md = mcp_server.read_md

        def read_with_late_failure(path):
            if path.name == "BSecond.md":
                raise OSError("late read failed")
            return original_read_md(path)

        monkeypatch.setattr(mcp_server, "read_md", read_with_late_failure)
        service = mcp_server.McpWikiService(src_dir=".", wiki_dir="docs/llm_wiki")

        with pytest.raises(OSError, match="late read failed"):
            service.search_wiki(
                "Late read fixture",
                kinds=["entities"],
                limit=1,
            )

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
            "freshness": "evaluated (6 concepts)",
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

    def test_get_context_preserves_compact_typed_relationship_selection(
        self,
        tmp_path,
        monkeypatch,
    ):
        refinements = {
            "symbol": "User",
            "relationship_kind": "calls",
            "relationship_origin": "extracted",
            "relationship_resolution": "resolved",
            "relationship_direction": "incoming",
        }
        graph_status = {
            "availability": "ready",
            "reason": "typed-graph-extension-ready",
            "coverage": [],
        }
        graph_selection = {
            **graph_status,
            "found": True,
            "direction": "incoming",
            "filters": {
                key: value
                for key, value in refinements.items()
                if key.startswith("relationship_")
            },
            "unfiltered_total": 4,
            "filtered_total": 2,
            "returned": 1,
            "truncated": True,
            "coverage": {
                "scope": "returned-edges",
                "edges": 1,
                "observed": 1,
                "emitted": 1,
                "omitted": 0,
                "truncated": False,
                "limitations": [],
            },
        }
        seen = {}

        def fake_build_context(
            _src_dir,
            budget,
            _fmt,
            _focus,
            filters,
            **_kwargs,
        ):
            seen["filters"] = filters
            return (
                {
                    "budget": budget,
                    "used": 0,
                    "files": {},
                    "typed_graph": graph_status,
                    "graphs": {
                        "symbol": {
                            "pages": {
                                "pages": [
                                    {
                                        "canonical_path": "entities/User.md",
                                        "typed_graph": graph_selection,
                                    }
                                ]
                            }
                        }
                    },
                },
                [],
            )

        monkeypatch.setattr(context_cmd, "_build_context", fake_build_context)
        service = mcp_server.McpWikiService(
            src_dir=str(tmp_path),
            wiki_dir=str(tmp_path / "wiki"),
        )

        result = service.get_context(
            focus=["all"],
            format="json",
            filters=refinements,
        )

        assert seen["filters"] == refinements
        assert result["typed_graph"] == graph_status
        assert (
            result["graphs"]["symbol"]["pages"]["pages"][0]["typed_graph"]
            == graph_selection
        )
        encoded = json.dumps(result, sort_keys=True)
        assert "samples" not in encoded
        assert "aggregate_input_hash" not in encoded

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
        tmp_path,
        monkeypatch,
    ):
        status = {
            "availability": "degraded",
            "reason": "policy-selected-surface-only-fallback-after-invalid",
            "freshness": "unevaluated (snapshot-only read)",
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
        service = mcp_server.McpWikiService(
            src_dir=str(tmp_path),
            wiki_dir=str(tmp_path / "wiki"),
        )

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
        tmp_path,
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
        service = mcp_server.McpWikiService(
            src_dir=str(tmp_path),
            wiki_dir=str(tmp_path / "wiki"),
        )

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

    def test_get_context_packet_returns_fresh_packet_and_forwards_bounds(
        self,
        tmp_path,
        monkeypatch,
    ):
        from llm_wiki_cli.services import context_packet

        packet_id = "sha256:" + "a" * 64
        payload = {
            "schema_version": context_packet.CONTEXT_PACKET_SCHEMA_VERSION,
            "packet_id": packet_id,
        }
        seen = {}

        class Packet:
            def __init__(self):
                self.packet_id = packet_id

            def to_payload(self):
                return dict(payload)

        def fake_build(src_dir, wiki_dir, request, *, read_only):
            seen.update(
                {
                    "src_dir": src_dir,
                    "wiki_dir": wiki_dir,
                    "request": request,
                    "read_only": read_only,
                }
            )
            return Packet()

        monkeypatch.setattr(context_packet, "build_qualified_context", fake_build)
        wiki_dir = tmp_path / "wiki"
        service = mcp_server.McpWikiService(
            src_dir="source-root",
            wiki_dir=str(wiki_dir),
        )

        result = service.get_context_packet(
            budget_tokens=4096,
            focus=["all"],
            format="json",
            filters={"surface": "entities"},
            prefer_fresh=True,
        )

        assert result == {
            "state": "fresh",
            "unchanged": False,
            "packet_id": packet_id,
            "packet": payload,
        }
        assert seen == {
            "src_dir": "source-root",
            "wiki_dir": wiki_dir.as_posix(),
            "request": {
                "protocol": "llm-wiki-context/v1",
                "budget_tokens": 4096,
                "focus": ["all"],
                "format": "json",
                "filters": {"surface": "entities"},
                "prefer_fresh": True,
            },
            "read_only": True,
        }

    def test_service_boundaries_serialize_wiki_dir_with_posix_separators(
        self,
        tmp_path,
        monkeypatch,
    ):
        from llm_wiki_cli.services import context_packet

        monkeypatch.chdir(tmp_path)
        calls: dict[str, object] = {"queries": []}

        class QueryService:
            def flow_for_entrypoint(self, _value):
                return {"found": True}

            def get_concept(self, _value):
                return {"found": True}

        def fake_query_builder(src_dir, *, wiki_dir, limit, read_only=None):
            queries = calls["queries"]
            assert isinstance(queries, list)
            queries.append((src_dir, wiki_dir, limit, read_only))
            return QueryService()

        def fake_build_context(*_args, **options):
            calls["context_wiki_dir"] = options["wiki_dir"]
            return ({"used": 0, "files": {}}, [])

        class Packet:
            packet_id = "sha256:" + "a" * 64

            @staticmethod
            def to_payload():
                return {"packet_id": Packet.packet_id}

        def fake_build_packet(src_dir, wiki_dir, _request, *, read_only):
            calls["packet"] = (src_dir, wiki_dir, read_only)
            return Packet()

        monkeypatch.setattr(
            mcp_server,
            "build_documentation_query_service",
            fake_query_builder,
        )
        monkeypatch.setattr(context_cmd, "_build_context", fake_build_context)
        monkeypatch.setattr(
            context_packet,
            "build_qualified_context",
            fake_build_packet,
        )
        service = mcp_server.McpWikiService(
            src_dir="source-root",
            wiki_dir=r"docs\llm_wiki",
        )

        service.query_graph({"type": "flow_for_entrypoint", "value": "run"})
        service.get_context(format="json")
        service.get_context_packet()
        service.get_concept("llm-wiki://entities/User")

        assert calls == {
            "queries": [
                ("source-root", "docs/llm_wiki", 20, None),
                ("source-root", "docs/llm_wiki", 20, True),
            ],
            "context_wiki_dir": "docs/llm_wiki",
            "packet": ("source-root", "docs/llm_wiki", True),
        }

    def test_get_context_packet_revalidates_unchanged_and_changed_ids(
        self,
        tmp_path,
        monkeypatch,
    ):
        from llm_wiki_cli.services import context_packet

        packet_ids = iter(("sha256:" + "a" * 64, "sha256:" + "b" * 64))

        class Packet:
            def __init__(self, packet_id):
                self.packet_id = packet_id

            def to_payload(self):
                return {"packet_id": self.packet_id}

        monkeypatch.setattr(
            context_packet,
            "build_qualified_context",
            lambda *_args, **_kwargs: Packet(next(packet_ids)),
        )
        service = mcp_server.McpWikiService(
            src_dir=str(tmp_path),
            wiki_dir=str(tmp_path / "wiki"),
        )

        unchanged = service.get_context_packet(if_packet_id="sha256:" + "a" * 64)
        changed = service.get_context_packet(if_packet_id="sha256:" + "a" * 64)

        assert unchanged == {
            "state": "unchanged",
            "unchanged": True,
            "packet_id": "sha256:" + "a" * 64,
        }
        assert "packet" not in unchanged
        assert changed == {
            "state": "fresh",
            "unchanged": False,
            "packet_id": "sha256:" + "b" * 64,
            "packet": {"packet_id": "sha256:" + "b" * 64},
        }

    def test_get_context_packet_revalidation_detects_real_source_change(
        self,
        tmp_project,
    ):
        _write_wiki(tmp_project)
        service = mcp_server.McpWikiService(
            src_dir=".",
            wiki_dir="docs/llm_wiki",
        )

        fresh = service.get_context_packet(focus=["all"])
        unchanged = service.get_context_packet(
            focus=["all"],
            if_packet_id=fresh["packet_id"],
        )
        (tmp_project / "models.py").write_text(
            (tmp_project / "models.py").read_text(encoding="utf-8")
            + "\nclass ChangedAfterPacket:\n    pass\n",
            encoding="utf-8",
        )
        changed = service.get_context_packet(
            focus=["all"],
            if_packet_id=fresh["packet_id"],
        )

        assert fresh["state"] == "fresh"
        assert unchanged == {
            "state": "unchanged",
            "unchanged": True,
            "packet_id": fresh["packet_id"],
        }
        assert changed["state"] == "fresh"
        assert changed["unchanged"] is False
        assert changed["packet_id"] != fresh["packet_id"]
        assert changed["packet"]["packet_id"] == changed["packet_id"]

    @pytest.mark.parametrize(
        "if_packet_id",
        ["sha256:" + "A" * 64, "a" * 64, "not-a-digest", 7],
    )
    def test_get_context_packet_rejects_invalid_revalidation_id(
        self,
        if_packet_id,
    ):
        service = mcp_server.McpWikiService()

        with pytest.raises(
            mcp_server.McpWikiError,
            match="if_packet_id must be a sha256:<64 lowercase hex>",
        ):
            service.get_context_packet(if_packet_id=if_packet_id)

    def test_check_wiki_returns_lint_report(self, tmp_project, capsys):
        _write_wiki(tmp_project)
        service = mcp_server.McpWikiService(src_dir=".", wiki_dir="docs/llm_wiki")

        result = service.check_wiki(strict=False)

        assert result["format"] == "json"
        assert result["wiki_dir"] == "docs/llm_wiki"
        assert result["knowledge_drift_gate"] is False
        assert result["knowledge_drift_report"] is False
        assert "issues" in result
        assert "execution" not in result
        assert "Extractor plan:" not in capsys.readouterr().err

    def test_check_wiki_exposes_explicit_native_drift_report_mode(
        self,
        tmp_project,
        monkeypatch,
    ):
        seen = {}

        def fake_build_report(wiki_dir, src_dir, **kwargs):
            seen.update(kwargs)
            return mcp_server.lint_cmd.LintReport(
                wiki_dir=str(wiki_dir),
                src_dir=src_dir,
                strict=bool(kwargs["strict"] or kwargs["knowledge_drift_report"]),
                knowledge_drift_report=kwargs["knowledge_drift_report"],
            )

        monkeypatch.setattr(
            mcp_server.lint_cmd,
            "build_report",
            fake_build_report,
        )
        service = mcp_server.McpWikiService(
            src_dir=".",
            wiki_dir="docs/llm_wiki",
        )

        result = service.check_wiki(knowledge_drift_report=True)

        assert seen["strict"] is False
        assert seen["knowledge_drift_report"] is True
        assert result["strict"] is True
        assert result["knowledge_drift_gate"] is False
        assert result["knowledge_drift_report"] is True

    def test_check_wiki_preserves_structured_freshness_guidance(
        self,
        tmp_path,
        monkeypatch,
    ):
        reason = "generation-options-changed"
        hint = BASIS_INCOMPATIBLE_HINTS[reason]

        def fake_build_report(wiki_dir, src_dir, **kwargs):
            return mcp_server.lint_cmd.LintReport(
                wiki_dir=str(wiki_dir),
                src_dir=src_dir,
                strict=True,
                knowledge_drift_report=True,
                diagnostics=[
                    mcp_server.lint_cmd.LintIssue(
                        category="knowledge_freshness",
                        message=f"Basis is incompatible [reason={reason}].",
                        severity="warning",
                        reason_code=reason,
                        hint=hint,
                    )
                ],
            )

        monkeypatch.setattr(
            mcp_server.lint_cmd,
            "build_report",
            fake_build_report,
        )
        service = mcp_server.McpWikiService(
            src_dir=str(tmp_path),
            wiki_dir=str(tmp_path / "wiki"),
        )

        json_result = service.check_wiki(
            format="json",
            knowledge_drift_report=True,
        )
        markdown_result = service.check_wiki(
            format="markdown",
            knowledge_drift_report=True,
        )

        assert json_result["diagnostics"][0]["reason_code"] == reason
        assert json_result["diagnostics"][0]["hint"] == hint
        assert f"Hint: {hint}" in markdown_result["content"]

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
            "freshness": "unevaluated (snapshot-only read)",
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
            "freshness": "unevaluated (snapshot-only read)",
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
            "freshness": "unevaluated (snapshot-only read)",
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
            "freshness": "unevaluated (snapshot-only read)",
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
            "freshness": "unevaluated (snapshot-only read)",
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
            "freshness": "unevaluated (snapshot-only read)",
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
            "freshness": "unevaluated (snapshot-only read)",
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

    @pytest.mark.parametrize(
        ("live_policy", "freshness_evaluated", "state", "reason"),
        [
            (
                "current",
                True,
                "current",
                "recorded-basis-matches-live-evaluation",
            ),
            (
                "mismatch",
                True,
                "basis-incompatible",
                "generation-options-changed",
            ),
            ("invalid", False, None, "not-evaluated"),
        ],
    )
    def test_knowledge_methods_evaluate_live_options_conservatively(
        self,
        tmp_path,
        monkeypatch,
        live_policy,
        freshness_evaluated,
        state,
        reason,
    ):
        fixture = one_module_two_entities_fixture()
        tree = materialize_fixture_tree(
            fixture,
            tmp_path / "checkout",
            consumer="mcp",
        )
        commit_knowledge_artifacts(_knowledge_commit_plan(tree["wiki_root"], fixture))
        monkeypatch.chdir(tree["root"])
        real_options = context_cmd.runtime_generation_options

        if live_policy == "mismatch":

            def evaluated_options(**kwargs):
                options = real_options(**kwargs)
                options["preserve_semantic"] = False
                return options

            monkeypatch.setattr(
                context_cmd,
                "runtime_generation_options",
                evaluated_options,
            )
        elif live_policy == "invalid":

            def evaluated_options(**_kwargs):
                raise ValueError("invalid runtime generation policy")

            monkeypatch.setattr(
                context_cmd,
                "runtime_generation_options",
                evaluated_options,
            )

        service = mcp_server.McpWikiService(
            src_dir=".",
            wiki_dir="docs/llm_wiki",
        )
        result = service.get_concept("llm-wiki://entities/User")

        assert result["knowledge"] == {
            "availability": "ready",
            "reason": "all-projection-commitments-match",
            "freshness": (
                "evaluated (6 concepts)"
                if freshness_evaluated
                else "unevaluated (snapshot-only read)"
            ),
            "freshness_evaluated": freshness_evaluated,
        }
        expected_freshness = {
            "state": state,
            "reason": reason,
            "live_comparison_performed": freshness_evaluated,
        }
        if live_policy == "mismatch":
            expected_freshness["hint"] = BASIS_INCOMPATIBLE_HINTS[reason]
        assert result["concept"]["freshness"] == expected_freshness

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
                calls["query"].append(("related_concepts", locator, direction, kinds))
                return bounded_result

            def list_concept_sections(
                self,
                locator,
                *,
                ownership,
            ):
                calls["query"].append(("list_concept_sections", locator, ownership))
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
            "get_inventory_result",
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
        sections = service.list_concept_sections(
            " llm-wiki://entities/User ",
            ownership="semantic",
            limit=250,
        )
        evidence = service.explain_evidence(
            " llm-wiki://entities/User ",
            limit=250,
        )

        assert concept is concept_result
        assert related is bounded_result
        assert sections is bounded_result
        assert evidence is bounded_result
        assert calls["builder"] == [
            ("source-root", "agent_wiki", 100, True),
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
            (
                "list_concept_sections",
                "llm-wiki://entities/User",
                "semantic",
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
            (
                "list_concept_sections",
                ("llm-wiki://entities/User",),
                {"ownership": "reviewed"},
                "ownership must be one of",
            ),
            (
                "list_concept_sections",
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
        "locator",
        [
            "/entities/User.md",
            "../entities/User.md",
            "entities/../User.md",
            "entities//User.md",
            "entities/nested/User.md",
            "entities\\User.md",
            "unknown/User.md",
            "https://example.test/entities/User",
            "llm-wiki://user@entities/User",
            "llm-wiki://entities:80/User",
            "llm-wiki://entities/User?view=full",
            "llm-wiki://entities/User#details",
            "llm-wiki://entities/User/",
            "llm-wiki://entities/%",
            "llm-wiki://entities/%2FUser",
            "llm-wiki://entities/%2E%2E",
            "llm-wiki://entities/%55ser",
        ],
    )
    @pytest.mark.parametrize(
        "method_name",
        [
            "get_concept",
            "list_concept_sections",
            "related_concepts",
            "explain_evidence",
        ],
    )
    def test_knowledge_methods_reject_invalid_coordinates_before_extraction(
        self,
        monkeypatch,
        method_name,
        locator,
    ):
        monkeypatch.setattr(
            mcp_server,
            "build_documentation_query_service",
            fail_if_extraction_runs,
        )
        service = mcp_server.McpWikiService()

        with pytest.raises(
            mcp_server.McpWikiError,
            match="must be an exact canonical wiki path or llm-wiki URI",
        ):
            getattr(service, method_name)(locator)

    @pytest.mark.parametrize(
        "locator",
        [
            "index.md",
            "llm-wiki://index",
            "entities/Missing.md",
            "llm-wiki://entities/Missing",
            "entities/Page(1).md",
            "llm-wiki://entities/Page%281%29",
            "lw:entity:0123456789abcdef0123456789abcdef",
            "code-entity:entities/LegacyUser.md",
        ],
    )
    def test_valid_missing_coordinates_delegate_to_normal_lookup(
        self,
        tmp_path,
        monkeypatch,
        locator,
    ):
        calls = []

        class FakeQueryService:
            def get_concept(self, value):
                calls.append(value)
                return {"query": value, "found": False}

        monkeypatch.setattr(
            mcp_server,
            "build_documentation_query_service",
            lambda *_args, **_kwargs: FakeQueryService(),
        )
        service = mcp_server.McpWikiService(
            src_dir=str(tmp_path),
            wiki_dir=str(tmp_path / "wiki"),
        )

        result = service.get_concept(locator)

        assert result == {"query": locator, "found": False}
        assert calls == [locator]

    @pytest.mark.parametrize(
        "method_name",
        [
            "get_concept",
            "list_concept_sections",
            "related_concepts",
            "explain_evidence",
        ],
    )
    @pytest.mark.parametrize("failure_point", ["builder", "query"])
    def test_knowledge_methods_map_api_and_query_errors(
        self,
        tmp_path,
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

            def list_concept_sections(
                self,
                _locator,
                *,
                ownership,
            ):
                del ownership
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
        service = mcp_server.McpWikiService(
            src_dir=str(tmp_path),
            wiki_dir=str(tmp_path / "wiki"),
        )
        if method_name == "related_concepts":
            kwargs = {"direction": "both", "kinds": None}
        elif method_name == "list_concept_sections":
            kwargs = {"ownership": None}
        else:
            kwargs = {}

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
        tmp_path,
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
            "get_inventory_result",
            fail_if_extraction_runs,
        )
        wiki_dir = tmp_path / "wiki"
        service = mcp_server.McpWikiService(
            src_dir=str(tmp_path),
            wiki_dir=str(wiki_dir),
        )

        concept = service.get_concept("llm-wiki://entities/User")
        sections = service.list_concept_sections(
            "llm-wiki://entities/User",
            ownership="unknown",
        )
        related = service.related_concepts(
            "llm-wiki://entities/User",
            direction="outbound",
            kinds=["links_to"],
        )
        evidence = service.explain_evidence("llm-wiki://entities/User")

        status = {
            "availability": availability,
            "reason": reason,
            "freshness": "unevaluated (snapshot-only read)",
            "freshness_evaluated": False,
        }
        assert concept["knowledge"] == status
        assert concept["found"] is False
        assert concept["concept"] is None
        assert sections["knowledge"] == status
        assert sections["found"] is False
        assert sections["section_ownership"] == {
            "availability": availability,
            "reason": reason,
            "schema_version": None,
        }
        assert sections["ownership"] == "unknown"
        assert sections["sections"] == []
        assert related["knowledge"] == status
        assert related["found"] is False
        assert related["relationships"] == []
        assert evidence["knowledge"] == status
        assert evidence["found"] is False
        assert evidence["evidence"] is None
        assert calls == [
            (str(tmp_path), wiki_dir.as_posix(), 20, True),
            (str(tmp_path), wiki_dir.as_posix(), 20, True),
            (str(tmp_path), wiki_dir.as_posix(), 20, True),
            (str(tmp_path), wiki_dir.as_posix(), 20, True),
        ]


class RecordingMcpServer:
    def __init__(self):
        self.tool_names: list[str] = []
        self.tool_functions: dict[str, object] = {}
        self.resource_uris: list[str] = []

    def tool(self):
        def decorator(func):
            self.tool_names.append(func.__name__)
            self.tool_functions[func.__name__] = func
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
        "list_concept_sections",
        "traverse_typed_graph",
        "explain_evidence",
        "search_wiki",
        "get_context",
        "get_context_packet",
        "check_wiki",
        "get_status",
    ]


def test_registered_section_tool_forwards_filter_and_limit():
    calls = []
    expected = {"operation": "list_concept_sections"}

    class RecordingService:
        def list_concept_sections(
            self,
            locator_or_exact_route,
            ownership=None,
            limit=20,
        ):
            calls.append((locator_or_exact_route, ownership, limit))
            return expected

    server = RecordingMcpServer()
    mcp_server._register_mcp_tools(server, RecordingService())

    result = server.tool_functions["list_concept_sections"](
        "llm-wiki://entities/User",
        ownership="mixed",
        limit=7,
    )

    assert result is expected
    assert calls == [("llm-wiki://entities/User", "mixed", 7)]


def test_registered_check_wiki_tool_forwards_native_drift_report_mode():
    calls = []
    expected = {"operation": "check_wiki"}

    class RecordingService:
        def check_wiki(
            self,
            strict=False,
            format="json",
            knowledge_drift_report=False,
        ):
            calls.append((strict, format, knowledge_drift_report))
            return expected

    server = RecordingMcpServer()
    mcp_server._register_mcp_tools(server, RecordingService())

    result = server.tool_functions["check_wiki"](
        strict=True,
        format="markdown",
        knowledge_drift_report=True,
    )

    assert result is expected
    assert calls == [(True, "markdown", True)]


def test_registered_context_packet_tool_forwards_revalidation_and_policy():
    calls = []
    expected = {"state": "unchanged"}

    class RecordingService:
        def get_context_packet(
            self,
            budget_tokens=32000,
            focus=None,
            format="json",
            filters=None,
            prefer_fresh=False,
            if_packet_id=None,
        ):
            calls.append(
                (
                    budget_tokens,
                    focus,
                    format,
                    filters,
                    prefer_fresh,
                    if_packet_id,
                )
            )
            return expected

    server = RecordingMcpServer()
    mcp_server._register_mcp_tools(server, RecordingService())

    result = server.tool_functions["get_context_packet"](
        budget_tokens=2048,
        focus=["all"],
        format="json",
        filters={"surface": "entities"},
        prefer_fresh=True,
        if_packet_id="sha256:" + "a" * 64,
    )

    assert result is expected
    assert calls == [
        (
            2048,
            ["all"],
            "json",
            {"surface": "entities"},
            True,
            "sha256:" + "a" * 64,
        )
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
        "get_context_packet",
        "check_wiki",
        "get_status",
    } <= set(server.tool_names)
    assert {"get_flow", "get_architecture_page", "query_graph"} <= set(
        server.tool_names
    )
    assert {
        "get_concept",
        "list_concept_sections",
        "related_concepts",
        "traverse_typed_graph",
        "explain_evidence",
    } <= set(server.tool_names)


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

    def test_origin_helpers_normalize_defaults_and_reject_malformed_values(self):
        assert not mcp_server._is_loopback_host("not a host")
        assert mcp_server._default_port_for_scheme("http") == 80
        assert mcp_server._default_port_for_scheme("https") == 443
        assert mcp_server._default_port_for_scheme("ftp") is None
        assert (
            mcp_server._normalise_origin("HTTPS://[::1]:8765") == "https://[::1]:8765"
        )

        for origin in (
            "ftp://localhost",
            "http://localhost/path",
            "http://localhost:not-a-port",
        ):
            with pytest.raises(mcp_server.McpWikiError):
                mcp_server._normalise_origin(origin)

    def test_graph_filter_helpers_validate_and_order_values(self):
        assert mcp_server._knowledge_kinds(None) is None
        assert mcp_server._knowledge_kinds([]) == []
        with pytest.raises(mcp_server.McpWikiError, match="iterable"):
            mcp_server._knowledge_kinds("calls")
        with pytest.raises(mcp_server.McpWikiError, match="only"):
            mcp_server._knowledge_kinds([1])
        with pytest.raises(mcp_server.McpWikiError, match="unsupported"):
            mcp_server._knowledge_kinds(["not-a-kind"])

        assert mcp_server._typed_graph_kinds(None) is None
        with pytest.raises(mcp_server.McpWikiError, match="iterable"):
            mcp_server._typed_graph_kinds({"kind": "calls"})
        with pytest.raises(mcp_server.McpWikiError, match="only"):
            mcp_server._typed_graph_kinds([1])
        with pytest.raises(mcp_server.McpWikiError, match="unsupported"):
            mcp_server._typed_graph_kinds(["not a kind"])
        with pytest.raises(mcp_server.McpWikiError, match="direction"):
            mcp_server._typed_graph_direction("sideways")

        assert mcp_server._typed_graph_enum_values(
            ["beta", "alpha"],
            field="states",
            allowed=("alpha", "beta"),
        ) == ["alpha", "beta"]
        with pytest.raises(mcp_server.McpWikiError, match="iterable"):
            mcp_server._typed_graph_enum_values(
                "alpha",
                field="states",
                allowed=("alpha",),
            )
        with pytest.raises(mcp_server.McpWikiError, match="only"):
            mcp_server._typed_graph_enum_values(
                [1],
                field="states",
                allowed=("alpha",),
            )
        with pytest.raises(mcp_server.McpWikiError, match="unsupported"):
            mcp_server._typed_graph_enum_values(
                ["beta"],
                field="states",
                allowed=("alpha",),
            )

    def test_page_and_markdown_helpers_enforce_bounds(self, tmp_path):
        for value in (True, 0):
            with pytest.raises(mcp_server.McpWikiError, match="positive integer"):
                mcp_server._bounded_query_limit(value)
        assert mcp_server._bounded_query_limit(10_000) == 100

        with pytest.raises(mcp_server.McpWikiError, match="non-empty"):
            mcp_server._validate_page_id("")
        with pytest.raises(mcp_server.McpWikiError, match="Unsafe"):
            mcp_server._validate_page_id("%2E%2E")
        assert mcp_server._validate_page_id("User") == "User"

        with pytest.raises(mcp_server.McpWikiError, match="escapes"):
            mcp_server._ensure_inside(tmp_path, tmp_path.parent / "outside.md")

        assert mcp_server._markdown_title("\n## Title\n", "Fallback") == "Title"
        assert mcp_server._markdown_title("#\n", "Fallback") == "Fallback"
        assert mcp_server._markdown_title("No heading", "Fallback") == "Fallback"
        assert mcp_server._count_md(tmp_path / "missing") == 0
        (tmp_path / "one.md").write_text("# One\n", encoding="utf-8")
        (tmp_path / "two.txt").write_text("Two\n", encoding="utf-8")
        assert mcp_server._count_md(tmp_path) == 1

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
    def test_cli_preserves_external_source_authorization_in_server_config(
        self,
        tmp_path,
        monkeypatch,
    ):
        project = tmp_path / "project"
        external = tmp_path / "external"
        project.mkdir()
        external.mkdir()
        (project / "docs" / "llm_wiki").mkdir(parents=True)
        monkeypatch.chdir(project)
        seen = {}
        exports = {
            "McpServerConfig": mcp_server.McpServerConfig,
            "MCPDependencyError": mcp_server.MCPDependencyError,
            "McpWikiError": mcp_server.McpWikiError,
            "run_mcp_server": lambda config: seen.setdefault("config", config),
        }
        monkeypatch.setattr(
            mcp_cmd,
            "_mcp_service_export",
            lambda name: exports[name],
        )

        mcp_cmd.run(
            _args(
                src_dir=str(external),
                allow_external_src=True,
                source_selection=None,
            )
        )

        config = seen["config"]
        assert Path(config.src_dir) == external
        assert config.allow_external_src is True

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

    def test_stdio_server_uses_supported_fastmcp_run_signature(
        self,
        tmp_path,
        monkeypatch,
    ):
        source = tmp_path / "source"
        wiki = tmp_path / "wiki"
        source.mkdir()
        wiki.mkdir()
        calls = []
        monkeypatch.chdir(tmp_path)

        class Server:
            def run(self, *, transport):
                calls.append(transport)

        monkeypatch.setattr(
            mcp_server,
            "create_mcp_server",
            lambda _config: Server(),
        )

        mcp_server.run_mcp_server(
            mcp_server.McpServerConfig(
                src_dir="source",
                wiki_dir="wiki",
            )
        )

        assert calls == ["stdio"]

    def test_server_runner_accepts_opted_in_external_source(
        self,
        tmp_path,
        monkeypatch,
    ):
        project = tmp_path / "project"
        external = tmp_path / "external"
        wiki = project / "wiki"
        project.mkdir()
        external.mkdir()
        wiki.mkdir()
        calls = []
        monkeypatch.chdir(project)

        class Server:
            def run(self, *, transport):
                calls.append(transport)

        monkeypatch.setattr(
            mcp_server,
            "create_mcp_server",
            lambda _config: Server(),
        )

        mcp_server.run_mcp_server(
            mcp_server.McpServerConfig(
                src_dir=str(external),
                allow_external_src=True,
                wiki_dir="wiki",
            )
        )

        assert calls == ["stdio"]

    def test_http_server_wraps_sdk_application_with_origin_validation(
        self,
        tmp_path,
        monkeypatch,
    ):
        source = tmp_path / "source"
        wiki = tmp_path / "wiki"
        source.mkdir()
        wiki.mkdir()
        middleware = []
        uvicorn_calls = []
        monkeypatch.chdir(tmp_path)

        class Application:
            def add_middleware(self, middleware_class, **options):
                middleware.append((middleware_class, options))

        application = Application()

        class Server:
            def streamable_http_app(self):
                return application

        monkeypatch.setattr(
            mcp_server,
            "create_mcp_server",
            lambda _config: Server(),
        )
        monkeypatch.setitem(
            sys.modules,
            "uvicorn",
            types.SimpleNamespace(
                run=lambda app, **options: uvicorn_calls.append((app, options))
            ),
        )

        mcp_server.run_mcp_server(
            mcp_server.McpServerConfig(
                src_dir="source",
                wiki_dir="wiki",
                transport="http",
                port=8765,
                allowed_origins=("https://example.com",),
            )
        )

        assert middleware == [
            (
                mcp_server.OriginValidationMiddleware,
                {
                    "port": 8765,
                    "allowed_origins": ["https://example.com"],
                },
            )
        ]
        assert uvicorn_calls == [
            (
                application,
                {
                    "host": "127.0.0.1",
                    "port": 8765,
                    "log_level": "warning",
                },
            )
        ]

    def test_optional_sdk_registration_when_installed(self, tmp_project):
        if importlib.util.find_spec("mcp") is None:
            if os.environ.get("LLM_WIKI_REQUIRE_MCP_SDK") == "1":
                pytest.fail("MCP SDK is required by this test environment.")
            pytest.skip("MCP SDK is not installed.")
        _write_wiki(tmp_project)

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
