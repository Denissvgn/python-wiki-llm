"""Tests for the supported Python source-adapter API."""

from __future__ import annotations

import inspect
import textwrap
import types

import pytest

import llm_wiki_cli.api as api
from llm_wiki_cli.api import (
    EXTRACT_SCHEMA_VERSION,
    ExtractionError,
    LlmWikiApiError,
    PathPolicyError,
    build_context,
    build_documentation_query_service,
    callees,
    callers,
    data_flow_for_entrypoint,
    dependency_neighborhood,
    extract_source,
    flow_for_entrypoint,
    list_wiki_pages,
    pages_for_symbol,
)
from llm_wiki_cli.services.knowledge_artifacts import commit_knowledge_artifacts
from llm_wiki_cli.services.knowledge_consumption import build_knowledge_read_view
from llm_wiki_cli.services.knowledge_loader import KnowledgeLoadResult
from llm_wiki_cli.services.knowledge_model import KnowledgeLoadState
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


def test_supported_api_exports_are_additive_contract():
    expected_exports = {
        "BOOTSTRAP_SUMMARY_SCHEMA_VERSION",
        "EXTRACT_SCHEMA_VERSION",
        "DocumentationGraphQueryService",
        "ExtractionError",
        "LlmWikiApiError",
        "PathPolicyError",
        "build_context",
        "build_documentation_query_service",
        "callees",
        "callers",
        "data_flow_for_entrypoint",
        "dependency_neighborhood",
        "extract_source",
        "explain_evidence",
        "flow_for_entrypoint",
        "get_concept",
        "list_wiki_pages",
        "pages_for_symbol",
        "related_concepts",
    }

    assert expected_exports <= set(api.__all__)


def test_supported_api_signatures_preserve_existing_callers():
    extract_params = inspect.signature(extract_source).parameters
    context_params = inspect.signature(build_context).parameters

    assert list(extract_params) == [
        "src_dir",
        "changed",
        "summary",
        "deep",
        "paths",
        "package",
        "include_empty",
        "allow_external_src",
        "read_only",
    ]
    assert extract_params["src_dir"].default == "."
    assert extract_params["changed"].kind is inspect.Parameter.KEYWORD_ONLY
    assert extract_params["read_only"].default is True

    assert list(context_params) == [
        "src_dir",
        "budget",
        "format",
        "focus",
        "filters",
        "wiki_dir",
        "allow_external_src",
        "read_only",
    ]
    assert context_params["src_dir"].default == "."
    assert context_params["budget"].default == 32000
    assert context_params["filters"].default is None
    assert context_params["wiki_dir"].kind is inspect.Parameter.KEYWORD_ONLY


def test_knowledge_api_signatures_are_explicit_and_builder_stays_compatible():
    builder_params = inspect.signature(
        build_documentation_query_service
    ).parameters
    assert list(builder_params) == [
        "src_dir",
        "wiki_dir",
        "limit",
        "allow_external_src",
        "read_only",
    ]
    assert builder_params["src_dir"].default == "."
    assert builder_params["wiki_dir"].kind is inspect.Parameter.KEYWORD_ONLY
    assert builder_params["limit"].default == 20
    assert builder_params["read_only"].default is True

    common = [
        "locator_or_exact_route",
        "service",
        "src_dir",
        "wiki_dir",
        "limit",
        "allow_external_src",
        "read_only",
    ]
    assert list(inspect.signature(api.get_concept).parameters) == common
    assert list(inspect.signature(api.explain_evidence).parameters) == common
    assert list(inspect.signature(api.related_concepts).parameters) == [
        "locator_or_exact_route",
        "direction",
        "kinds",
        "service",
        "src_dir",
        "wiki_dir",
        "limit",
        "allow_external_src",
        "read_only",
    ]

    for function in (
        api.get_concept,
        api.related_concepts,
        api.explain_evidence,
    ):
        params = inspect.signature(function).parameters
        assert (
            params["locator_or_exact_route"].kind
            is inspect.Parameter.POSITIONAL_OR_KEYWORD
        )
        assert params["service"].kind is inspect.Parameter.KEYWORD_ONLY
        assert params["service"].default is None
        assert params["limit"].default == 20
        assert params["read_only"].default is True
    related_params = inspect.signature(api.related_concepts).parameters
    assert related_params["direction"].default == "both"
    assert related_params["kinds"].default is None


def test_api_error_types_remain_structured_subclasses():
    assert issubclass(PathPolicyError, LlmWikiApiError)
    assert issubclass(ExtractionError, LlmWikiApiError)


@pytest.mark.parametrize(
    "case",
    COMPATIBILITY_CASES,
    ids=lambda case: case.id,
)
def test_python_knowledge_api_uses_shared_compatibility_policy(
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
    service = build_documentation_query_service(
        ".",
        wiki_dir="docs/llm_wiki",
    )

    concept = api.get_concept(
        "llm-wiki://entities/User",
        service=service,
    )
    related = api.related_concepts(
        "llm-wiki://entities/User",
        service=service,
    )
    evidence = api.explain_evidence(
        "llm-wiki://entities/User",
        service=service,
    )

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
    if case.serves_knowledge:
        assert concept["concept"]["locator"] == "llm-wiki://entities/User"
    else:
        assert concept["concept"] is None
        assert related["relationships"] == []
        assert evidence["evidence"] is None


def _write_query_project(root):
    (root / "api.py").write_text(
        textwrap.dedent(
            """\
            from repo import save

            __all__ = ["run"]

            def run(payload):
                return save(payload)
            """
        ),
        encoding="utf-8",
    )
    (root / "repo.py").write_text(
        textwrap.dedent(
            """\
            def save(payload):
                return payload
            """
        ),
        encoding="utf-8",
    )


def _write_api_wiki(root, rel_path="docs/llm_wiki"):
    wiki = root / rel_path
    for subdir in ["entities", "modules", "workflows", "flows", "infrastructure"]:
        (wiki / subdir).mkdir(parents=True, exist_ok=True)
    (wiki / "index.md").write_text("# Index\n\n", encoding="utf-8")
    (wiki / "log.md").write_text("# Log\n\n", encoding="utf-8")
    (wiki / "modules" / "api.md").write_text(
        "# api Module\n\n**Path:** `api.py`\n", encoding="utf-8"
    )
    (wiki / "modules" / "repo.md").write_text(
        "# repo Module\n\n**Path:** `repo.py`\n", encoding="utf-8"
    )
    (wiki / "flows" / "api-run.md").write_text(
        "# api-run\n\nFlow for run.\n", encoding="utf-8"
    )
    (wiki / "dependencies.md").write_text("# Dependencies\n\n", encoding="utf-8")
    (wiki / "load-order.md").write_text("# Load order\n\n", encoding="utf-8")
    return wiki


def test_extract_source_returns_stable_payload(tmp_project):
    payload = extract_source(".", summary=True, read_only=True)

    assert payload["schema_version"] == EXTRACT_SCHEMA_VERSION
    assert payload["inventory"]
    first = next(iter(payload["inventory"].values()))
    assert "language" in first


def test_extract_source_preserves_haskell_inventory_entries(monkeypatch):
    haskell_entry = {
        "language": "haskell",
        "module": "HLSAnalysis.API",
        "imports": [
            {
                "module": "Data.Text",
                "qualified": False,
                "alias": None,
                "line": 4,
            }
        ],
        "classes": [
            {
                "name": "User",
                "kind": "data",
                "line": 8,
                "deriving": ["Show"],
            }
        ],
        "functions": [
            {
                "name": "loadUser",
                "kind": "signature",
                "signature": "UserId -> Maybe User",
                "line": 18,
            },
            {"name": "loadUser", "kind": "function", "line": 19},
        ],
        "language_pragmas": ["FlexibleInstances"],
        "exports": ["User", "loadUser"],
    }
    payload = {
        "schema_version": EXTRACT_SCHEMA_VERSION,
        "inventory": {"hls-analysis/src/HLSAnalysis/API.hs": haskell_entry},
    }

    def fake_build_extract_payload(src_dir, **kwargs):
        assert src_dir == "source-root"
        assert kwargs["read_only"] is True
        return api.extract_cmd.ExtractPayloadResult(
            payload=payload,
            inventory_count=1,
            docker_count=0,
        )

    monkeypatch.setattr(
        api.extract_cmd, "build_extract_payload", fake_build_extract_payload
    )

    assert extract_source("source-root", read_only=True) == payload


def test_build_context_returns_json_payload(tmp_project):
    payload = build_context(".", budget=100000, focus="all", format="json")

    assert payload["budget"] == 100000
    assert payload["files"]


def test_build_context_returns_markdown_content_and_raw_payload(tmp_project):
    payload = build_context(".", budget=100000, focus="all", format="markdown")

    assert "Context Budget" in payload["content"]
    assert payload["payload"]["files"]


def test_build_context_accepts_graph_filters_and_wiki_dir(tmp_project):
    _write_query_project(tmp_project)
    _write_api_wiki(tmp_project, "agent_wiki")

    payload = build_context(
        ".",
        budget=100000,
        focus="all",
        format="json",
        filters={"symbol": "run", "surface": "flows"},
        wiki_dir="agent_wiki",
    )

    assert payload["graphs"]["symbol"]["callees"]["found"] is True
    assert payload["graphs"]["symbol"]["pages"]["pages"]
    assert payload["surface"]["kind"] == "flows"
    assert "files" in payload
    assert [page["canonical_path"] for page in payload["surface"]["pages"]] == [
        "flows/api-run.md"
    ]


def test_build_context_graph_sections_are_optional_additions(tmp_project):
    _write_query_project(tmp_project)
    _write_api_wiki(tmp_project, "agent_wiki")

    plain_payload = build_context(
        ".",
        budget=100000,
        focus="all",
        format="json",
        wiki_dir="agent_wiki",
    )
    enriched_payload = build_context(
        ".",
        budget=100000,
        focus="all",
        format="json",
        filters={"symbol": "run", "entrypoint": "api-run", "surface": "flows"},
        wiki_dir="agent_wiki",
    )

    assert "graphs" not in plain_payload
    assert "surface" not in plain_payload
    assert {"budget", "used", "files"} <= set(enriched_payload)
    assert enriched_payload["graphs"]["entrypoint"]["flow"]["found"] is True
    assert enriched_payload["surface"]["pages"][0]["canonical_path"] == (
        "flows/api-run.md"
    )


def test_build_context_passes_knowledge_refinements_and_preserves_results(
    monkeypatch,
):
    refinements = {
        "surface": "entities",
        "freshness": "source-changed",
        "evidence": "present",
    }
    knowledge_status = {
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
                "knowledge": knowledge_status,
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
                                **knowledge_status,
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

    monkeypatch.setattr(api.context_cmd, "_build_context", fake_build_context)

    result = build_context(
        "source-root",
        budget=4096,
        focus="all",
        format="json",
        filters=refinements,
        wiki_dir="agent_wiki",
    )

    assert seen == {
        "src_dir": "source-root",
        "budget": 4096,
        "format": "json",
        "focus": ["all"],
        "filters": refinements,
        "wiki_dir": "agent_wiki",
    }
    assert result["knowledge"] == knowledge_status
    assert result["surface"]["knowledge_selection"]["unfiltered_total"] == 2
    assert result["surface"]["knowledge_selection"]["filtered_total"] == 1
    assert result["surface"]["pages"][0]["knowledge"]["freshness"]["state"] == (
        "source-changed"
    )
    assert result["warnings"] == [
        "Knowledge context includes stale concept references."
    ]
    assert api.context_cmd.PROTOCOL_VERSION == "llm-wiki-context/v1"


@pytest.mark.parametrize(
    ("filters", "field"),
    [
        ({"freshness": "current"}, "freshness"),
        ({"evidence": "present"}, "evidence"),
    ],
)
def test_build_context_maps_knowledge_refinement_dependency_errors(filters, field):
    with pytest.raises(
        LlmWikiApiError,
        match=rf"filters\.{field} requires filters\.surface or filters\.symbol",
    ):
        build_context(".", filters=filters)


def test_build_context_markdown_preserves_knowledge_status_and_warnings(
    monkeypatch,
):
    status = {
        "availability": "degraded",
        "reason": "policy-selected-surface-only-fallback-after-invalid",
        "freshness_evaluated": False,
    }

    def fake_build_context(_src_dir, budget, _fmt, _focus, _filters, **_kwargs):
        return (
            {
                "budget": budget,
                "used": 0,
                "files": {},
                "knowledge": status,
            },
            ["Knowledge context is degraded; no candidates were dropped."],
        )

    monkeypatch.setattr(api.context_cmd, "_build_context", fake_build_context)

    result = build_context(
        ".",
        format="markdown",
        filters={"surface": "entities"},
    )

    assert result["payload"]["knowledge"] == status
    assert result["warnings"] == [
        "Knowledge context is degraded; no candidates were dropped."
    ]
    assert "## Knowledge" in result["content"]
    assert "- availability: degraded" in result["content"]


def test_build_context_legacy_json_shape_remains_context_v1(monkeypatch):
    legacy_payload = {
        "budget": 1000,
        "used": 0,
        "truncated": False,
        "omitted_files": [],
        "downgraded_files": {},
        "files": {},
    }

    def fake_build_context(*_args, **_kwargs):
        return dict(legacy_payload), []

    monkeypatch.setattr(api.context_cmd, "_build_context", fake_build_context)

    result = build_context(".", budget=1000, focus="all")

    assert result == legacy_payload
    assert "knowledge" not in result
    assert api.context_cmd.PROTOCOL_VERSION == "llm-wiki-context/v1"


def test_list_wiki_pages_returns_registry_metadata_without_running_extraction(
    tmp_project, monkeypatch
):
    wiki = _write_api_wiki(tmp_project)
    (wiki / "guides").mkdir()
    (wiki / "guides" / "operator-onboarding.md").write_text(
        "# Operator Onboarding\n\n", encoding="utf-8"
    )

    def fail_if_extracted(*args, **kwargs):  # pragma: no cover - assertion helper
        raise AssertionError("list_wiki_pages must not run source extraction")

    monkeypatch.setattr(api.extract_cmd, "build_extract_payload", fail_if_extracted)

    payload = list_wiki_pages("docs/llm_wiki")

    assert payload["wiki_dir"] == "docs/llm_wiki"
    assert payload["counts"]["by_kind"]["index"] == 1
    assert payload["counts"]["by_kind"]["modules"] == 2
    assert payload["counts"]["by_kind"]["guides"] == 1
    assert payload["counts"]["by_kind"]["flows"] == 1
    assert payload["counts"]["architecture_pages"] == 2
    assert {
        (page["kind"], page["id"], page["canonical_path"], page["mcp_uri"])
        for page in payload["pages"]
    } >= {
        ("index", "index", "index.md", "llm-wiki://index"),
        ("modules", "api", "modules/api.md", "llm-wiki://modules/api"),
        (
            "guides",
            "operator-onboarding",
            "guides/operator-onboarding.md",
            "llm-wiki://guides/operator-onboarding",
        ),
        ("flows", "api-run", "flows/api-run.md", "llm-wiki://flows/api-run"),
        ("dependencies", "dependencies", "dependencies.md", "llm-wiki://dependencies"),
    }


def test_list_wiki_pages_exposes_api_contract_root_surface(
    tmp_project, monkeypatch
):
    wiki = _write_api_wiki(tmp_project)
    (wiki / "api-contracts.md").write_text(
        "# API contracts\n\n## Notes\n\nReviewed.\n", encoding="utf-8"
    )

    def fail_if_extracted(*args, **kwargs):  # pragma: no cover - assertion helper
        raise AssertionError("list_wiki_pages must not run source extraction")

    monkeypatch.setattr(api.extract_cmd, "build_extract_payload", fail_if_extracted)

    payload = list_wiki_pages("docs/llm_wiki")

    assert payload["counts"]["by_kind"]["api-contracts"] == 1
    assert payload["counts"]["architecture_pages"] == 3
    page = next(
        item for item in payload["pages"] if item["kind"] == "api-contracts"
    )
    assert page["canonical_path"] == "api-contracts.md"
    assert page["mcp_uri"] == "llm-wiki://api-contracts"


def test_query_service_builder_reuses_one_inventory_snapshot_surface_and_view(
    tmp_project,
    monkeypatch,
):
    wiki = _write_api_wiki(tmp_project)
    inventory = {
        "api.py": {
            "language": "python",
            "classes": [],
            "functions": [],
            "imports": [],
        }
    }
    source_snapshot = object()
    retained_inventory = api.extract_cmd.InventoryResult(
        inventory=inventory,
        statuses={},
        source_snapshot=source_snapshot,
    )
    extract_result = api.extract_cmd.ExtractPayloadResult(
        payload={
            "inventory": inventory,
            "entrypoints": [],
            "data_flows": [],
        },
        inventory_count=1,
        docker_count=0,
        inventory_result=retained_inventory,
    )
    surface_payload = {"schema_version": "surface-fixture", "pages": []}
    surface_evaluation = types.SimpleNamespace(payload=surface_payload)
    knowledge_view = object()
    query_surface = {"schema_version": "query-surface", "pages": []}
    dependency_analysis = {"graph": {"nodes": [], "edges": []}}
    call_edges = []
    built_service = object()
    calls = {
        "extract": 0,
        "surface": 0,
        "view": 0,
        "query_surface": 0,
        "dependencies": 0,
        "service": 0,
    }

    def fake_extract(src_dir, **kwargs):
        calls["extract"] += 1
        assert src_dir == str(tmp_project.resolve())
        assert kwargs == {
            "deep": True,
            "allow_external_src": True,
            "read_only": True,
        }
        return extract_result

    def fake_surface(wiki_root, selected_inventory, **kwargs):
        calls["surface"] += 1
        assert wiki_root == wiki.resolve()
        assert selected_inventory is inventory
        assert kwargs == {
            "src_dir": tmp_project.resolve(),
            "entry_points": [],
        }
        return surface_evaluation

    def fake_view(wiki_root, evaluation, selected_inventory, inventory_result):
        calls["view"] += 1
        assert wiki_root == wiki.resolve()
        assert evaluation is surface_evaluation
        assert selected_inventory is inventory
        assert inventory_result is retained_inventory
        return knowledge_view

    def fake_query_surface(payload, view):
        calls["query_surface"] += 1
        assert payload is surface_payload
        assert view is knowledge_view
        return query_surface

    def fake_dependencies(
        selected_inventory,
        src_root,
        *,
        source_snapshot,
    ):
        calls["dependencies"] += 1
        assert selected_inventory is inventory
        assert src_root == str(tmp_project.resolve())
        assert source_snapshot is retained_inventory.source_snapshot
        return dependency_analysis

    def fake_service(selected_inventory, **kwargs):
        calls["service"] += 1
        assert selected_inventory is inventory
        assert kwargs["call_edges"] is call_edges
        assert kwargs["flows"] == []
        assert kwargs["data_flows"] == []
        assert kwargs["dependency_analysis"] is dependency_analysis
        assert kwargs["surface_index"] is query_surface
        assert kwargs["knowledge_view"] is knowledge_view
        assert kwargs["limit"] == 7
        return built_service

    monkeypatch.setattr(
        api.extract_cmd,
        "build_extract_payload",
        fake_extract,
    )
    monkeypatch.setattr(
        api.extract_cmd,
        "resolve_call_edges",
        lambda selected_inventory: (
            call_edges
            if selected_inventory is inventory
            else pytest.fail("builder replaced the retained inventory")
        ),
    )
    monkeypatch.setattr(api, "evaluate_surface_index", fake_surface)
    monkeypatch.setattr(
        api.context_cmd,
        "_build_context_knowledge_view",
        fake_view,
    )
    monkeypatch.setattr(
        api.context_cmd,
        "_context_query_surface",
        fake_query_surface,
    )
    monkeypatch.setattr(api, "analyze_dependencies", fake_dependencies)
    monkeypatch.setattr(api, "DocumentationGraphQueryService", fake_service)

    result = build_documentation_query_service(
        ".",
        wiki_dir="docs/llm_wiki",
        limit=7,
        read_only=True,
    )

    assert result is built_service
    assert calls == {
        "extract": 1,
        "surface": 1,
        "view": 1,
        "query_surface": 1,
        "dependencies": 1,
        "service": 1,
    }


def test_query_service_builder_exposes_committed_knowledge_end_to_end(
    tmp_path,
    monkeypatch,
):
    fixture = one_module_two_entities_fixture()
    tree = materialize_fixture_tree(
        fixture,
        tmp_path / "checkout",
        consumer="api",
    )
    commit_knowledge_artifacts(
        _knowledge_commit_plan(tree["wiki_root"], fixture)
    )
    monkeypatch.chdir(tree["root"])

    service = build_documentation_query_service(
        ".",
        wiki_dir="docs/llm_wiki",
    )
    result = api.get_concept(
        "llm-wiki://entities/User",
        service=service,
    )

    assert result["knowledge"] == {
        "availability": "ready",
        "reason": "all-projection-commitments-match",
        "freshness_evaluated": True,
    }
    assert result["found"] is True
    assert result["concept"]["locator"] == "llm-wiki://entities/User"


def test_graph_query_service_and_wrappers_return_documentation_answers(tmp_project):
    _write_query_project(tmp_project)
    _write_api_wiki(tmp_project)

    service = build_documentation_query_service(".", wiki_dir="docs/llm_wiki")

    flow = flow_for_entrypoint("api-run", service=service)
    assert flow["found"] is True
    assert flow["flow"]["entry"]["symbol"] == "run"
    assert flow["flow"]["modules_touched"] == ["api.py", "repo.py"]

    data_flow = data_flow_for_entrypoint("run", service=service)
    assert data_flow["found"] is True
    assert data_flow["data_flow"]["entry"]["id"] == "api-run"

    caller_result = callers("save", service=service)
    assert caller_result["found"] is True
    assert caller_result["callers"] == [
        {
            "file": "api.py",
            "module": "api",
            "symbol": "run",
            "kind": "internal",
            "line": 6,
        }
    ]

    callee_result = callees("run", service=service)
    assert callee_result["found"] is True
    assert callee_result["callees"] == [
        {
            "file": "repo.py",
            "module": "repo",
            "symbol": "save",
            "kind": "internal",
            "line": 6,
        }
    ]

    assert dependency_neighborhood("api.py", service=service)["outbound"] == ["repo.py"]
    assert pages_for_symbol("run", service=service)["pages"][0]["canonical_path"] in {
        "flows/api-run.md",
        "modules/api.md",
    }
    concept = api.get_concept("llm-wiki://modules/api", service=service)
    assert concept["knowledge"] == {
        "availability": "absent",
        "reason": "knowledge-projection-not-present",
        "freshness_evaluated": False,
    }
    assert concept["found"] is False
    assert concept["concept"] is None


def test_api_wrappers_map_path_and_query_errors(tmp_project):
    with pytest.raises(PathPolicyError):
        list_wiki_pages("../outside")

    service = build_documentation_query_service(".", wiki_dir="docs/llm_wiki")
    with pytest.raises(LlmWikiApiError, match="symbol must be a non-empty string"):
        callers("", service=service)


class _RecordingKnowledgeService:
    def __init__(self):
        self.calls = []
        self.concept_result = {"operation": "get_concept"}
        self.related_result = {"operation": "related_concepts"}
        self.evidence_result = {"operation": "explain_evidence"}

    def get_concept(self, locator_or_exact_route):
        self.calls.append(("get_concept", locator_or_exact_route))
        return self.concept_result

    def related_concepts(
        self,
        locator_or_exact_route,
        *,
        direction="both",
        kinds=None,
    ):
        self.calls.append(
            (
                "related_concepts",
                locator_or_exact_route,
                direction,
                kinds,
            )
        )
        return self.related_result

    def explain_evidence(self, locator_or_exact_route):
        self.calls.append(("explain_evidence", locator_or_exact_route))
        return self.evidence_result


def test_knowledge_wrappers_reuse_supplied_service_without_building_or_extracting(
    monkeypatch,
):
    monkeypatch.setattr(
        api,
        "build_documentation_query_service",
        fail_if_extraction_runs,
    )
    monkeypatch.setattr(
        api.extract_cmd,
        "build_extract_payload",
        fail_if_extraction_runs,
    )
    monkeypatch.setattr(
        api,
        "evaluate_surface_index",
        fail_if_extraction_runs,
    )
    monkeypatch.setattr(
        api.context_cmd,
        "_build_context_knowledge_view",
        fail_if_extraction_runs,
    )
    service = _RecordingKnowledgeService()
    common = {
        "service": service,
        "src_dir": "../unused-source",
        "wiki_dir": "../unused-wiki",
        "limit": 0,
        "allow_external_src": False,
        "read_only": True,
    }

    concept = api.get_concept("llm-wiki://entities/User", **common)
    related = api.related_concepts(
        "entities/User.md",
        direction="outbound",
        kinds=["links_to"],
        **common,
    )
    evidence = api.explain_evidence("llm-wiki://entities/User", **common)

    assert concept is service.concept_result
    assert related is service.related_result
    assert evidence is service.evidence_result
    assert service.calls == [
        ("get_concept", "llm-wiki://entities/User"),
        (
            "related_concepts",
            "entities/User.md",
            "outbound",
            ["links_to"],
        ),
        ("explain_evidence", "llm-wiki://entities/User"),
    ]


class _FailingKnowledgeService:
    @staticmethod
    def _fail():
        raise api.DocumentationQueryError("knowledge query failed")

    def get_concept(self, _locator_or_exact_route):
        self._fail()

    def related_concepts(
        self,
        _locator_or_exact_route,
        *,
        direction="both",
        kinds=None,
    ):
        del direction, kinds
        self._fail()

    def explain_evidence(self, _locator_or_exact_route):
        self._fail()


@pytest.mark.parametrize(
    ("function_name", "kwargs"),
    [
        ("get_concept", {}),
        (
            "related_concepts",
            {"direction": "outbound", "kinds": ["derived_from"]},
        ),
        ("explain_evidence", {}),
    ],
)
def test_knowledge_wrappers_map_query_errors_without_building_service(
    monkeypatch,
    function_name,
    kwargs,
):
    monkeypatch.setattr(
        api,
        "build_documentation_query_service",
        fail_if_extraction_runs,
    )
    service = _FailingKnowledgeService()

    with pytest.raises(
        LlmWikiApiError,
        match="knowledge query failed",
    ) as exc_info:
        getattr(api, function_name)(
            "llm-wiki://entities/User",
            service=service,
            **kwargs,
        )

    assert isinstance(exc_info.value.__cause__, api.DocumentationQueryError)


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
def test_knowledge_wrappers_preserve_structured_non_ready_state_without_extraction(
    monkeypatch,
    load_result,
    availability,
    reason,
):
    view = build_knowledge_read_view(load_result)
    service = api.DocumentationGraphQueryService(
        {},
        knowledge_view=view,
    )
    monkeypatch.setattr(
        api,
        "build_documentation_query_service",
        fail_if_extraction_runs,
    )
    monkeypatch.setattr(
        api.extract_cmd,
        "build_extract_payload",
        fail_if_extraction_runs,
    )

    concept = api.get_concept(
        "llm-wiki://entities/User",
        service=service,
    )
    related = api.related_concepts(
        "llm-wiki://entities/User",
        direction="outbound",
        kinds=["links_to"],
        service=service,
    )
    evidence = api.explain_evidence(
        "llm-wiki://entities/User",
        service=service,
    )

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
    assert related["direction"] == "outbound"
    assert related["kinds"] == ["links_to"]
    assert related["relationships"] == []
    assert evidence["knowledge"] == status
    assert evidence["found"] is False
    assert evidence["evidence"] is None
