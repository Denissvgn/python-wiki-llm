"""Real read interfaces share conservative caller decisions on owned sources."""

from __future__ import annotations

import io
from hashlib import sha256
import json
from pathlib import Path
import sys
from typing import Any

import pytest

from llm_wiki_cli import api, cli
from llm_wiki_cli.services.documentation_queries import DocumentationGraphQueryService
from llm_wiki_cli.services.documentation_query_builder import (
    build_live_documentation_query_service,
    build_snapshot_documentation_query_service,
)
from llm_wiki_cli.services.extraction_service import (
    get_inventory_result,
    resolve_call_edges,
    resolve_call_observations,
)
from llm_wiki_cli.services.inventory_cache import InventoryCacheOptions
from llm_wiki_cli.services.mcp_server import McpWikiService
from llm_wiki_cli.services.source_selection import SOURCE_SELECTION_SCHEMA_VERSION
from tests.developer_value.fixtures import materialize, projects, source_hashes

STATIC_LIMITATION = "static-call-resolution-does-not-claim-runtime-completeness"
TARGET = ("policy.py", "Batch.cap")


def _tree(path: Path) -> dict[str, bytes]:
    return {
        item.relative_to(path).as_posix(): item.read_bytes()
        for item in path.rglob("*")
        if item.is_file()
    }


@pytest.fixture
def owned_project(tmp_path, monkeypatch, capsys):
    def prepare(name: str, *, selected: bool = False) -> Path:
        root = (tmp_path / name).resolve()
        materialize(name, root)
        monkeypatch.chdir(root)
        if selected:
            policy = root / "src" / ".llm-wiki" / "source-selection.json"
            policy.parent.mkdir()
            policy.write_text(
                json.dumps(
                    {
                        "schema_version": SOURCE_SELECTION_SCHEMA_VERSION,
                        "include": ["policy.py", "client.py"],
                        "exclude": [],
                    }
                ),
                encoding="utf-8",
            )
        api.bootstrap_wiki("src", "wiki")
        capsys.readouterr()
        assert source_hashes(projects()[name]) == {
            path: sha256((root / "src" / path).read_bytes()).hexdigest()
            for path in projects()[name]
        }
        return root

    return prepare


def _coverage(result: dict[str, Any], scope: str = "full-inventory") -> dict:
    assert result["coverage"] == {
        "schema_version": "llm-wiki-static-call-coverage/v1",
        "analysis_scope": scope,
        "runtime_completeness": False,
        "limitations": [STATIC_LIMITATION],
    }
    return result["coverage"]


def _request(selector: str) -> dict:
    return {
        "operation": "symbol",
        "value": selector,
        "allow_full_inventory": True,
        "limit": 100,
    }


def _cli_symbol(selector, monkeypatch, capsys) -> dict:
    with monkeypatch.context() as patch:
        patch.setattr(
            sys,
            "argv",
            [
                "llm-wiki",
                "query",
                "--request",
                "-",
                "--src-dir",
                "src",
                "--wiki-dir",
                "wiki",
            ],
        )
        patch.setattr(sys, "stdin", io.StringIO(json.dumps(_request(selector))))
        cli.main()
    output = capsys.readouterr()
    assert output.err == ""
    return json.loads(output.out)


def _caller_routes(selector, monkeypatch, capsys) -> list[tuple[str, dict[str, Any]]]:
    mcp = McpWikiService("src", "wiki")
    return [
        (
            "python",
            dict(api.callers(selector, src_dir="src", wiki_dir="wiki", limit=100)),
        ),
        (
            "python-combined",
            dict(
                api.query_documentation(
                    _request(selector), src_dir="src", wiki_dir="wiki"
                )
            ),
        ),
        ("cli", _cli_symbol(selector, monkeypatch, capsys)),
        (
            "mcp-graph",
            mcp.query_graph({"type": "callers", "value": selector, "limit": 100}),
        ),
        ("mcp-combined", mcp.query_documentation(_request(selector))),
    ]


def _pairs(result, key):
    return {(row["file"], row["symbol"]) for row in result[key]}


@pytest.mark.parametrize("selector", ["policy.py:Batch.cap", "Batch.cap", "cap"])
def test_library_exact_qualified_short_callers_agree_across_real_interfaces(
    owned_project, selector, monkeypatch, capsys
):
    root = owned_project("library")
    before = _tree(root / "src"), _tree(root / "wiki")
    routes = _caller_routes(selector, monkeypatch, capsys)
    required = {("policy.py", "public_values"), ("client.py", "assigned_values")}
    expected = routes[0][1]["callers"]
    for name, result in routes:
        assert result["found"] and not result["ambiguous"], name
        assert _pairs(result, "callers") == required, name
        assert result["callers"] == expected, name
        _coverage(result)
    direct = next(row for row in expected if row["symbol"] == "public_values")
    assigned = next(row for row in expected if row["symbol"] == "assigned_values")
    assert direct["location"] == {"source_path": "policy.py", "line": 7, "column": 11}
    assert direct["constructor"]["receiver_origin"] == "direct-construction"
    assert assigned["location"] == {"source_path": "client.py", "line": 6, "column": 11}
    assert assigned["constructor"]["source_path"] == "client.py"
    assert assigned["constructor"]["line"] == 5
    assert assigned["constructor"]["column"] == 12
    assert assigned["constructor"]["receiver_origin"] == "assigned-construction"
    assert (_tree(root / "src"), _tree(root / "wiki")) == before


@pytest.mark.parametrize(
    "selector", ["policy.py:Batch.cap", "Batch.cap", "policy.py:cap"]
)
def test_service_explicit_alias_resolves_without_inventing_dynamic_callers(
    owned_project, selector, monkeypatch, capsys
):
    root = owned_project("service")
    before = _tree(root / "src"), _tree(root / "wiki")
    routes = _caller_routes(selector, monkeypatch, capsys)
    expected = routes[0][1]["callers"]
    for name, result in routes:
        assert result["found"] and not result["ambiguous"], name
        assert _pairs(result, "callers") == {
            ("policy.py", "public_values"),
            ("handlers.py", "list_items"),
        }, name
        assert result["callers"] == expected, name
        assert all(row["file"] != "dynamic.py" for row in result["callers"]), name
        _coverage(result)
    imported = next(row for row in expected if row["file"] == "handlers.py")
    assert imported["location"] == {
        "source_path": "handlers.py",
        "line": 10,
        "column": 11,
    }
    assert imported["constructor"]["root_binding"]["name"] == "Batch"
    assert imported["constructor"]["root_binding"]["module"] == "policy"
    assert (_tree(root / "src"), _tree(root / "wiki")) == before


def test_service_short_selector_is_ambiguous_on_every_route(
    owned_project, monkeypatch, capsys
):
    root = owned_project("service")
    before = _tree(root / "src"), _tree(root / "wiki")
    for name, result in _caller_routes("cap", monkeypatch, capsys):
        assert not result["found"] and result["ambiguous"], name
        assert result["callers"] == [], name
        assert _pairs(result, "matches") == {
            TARGET,
            ("dynamic.py", "OtherBatch.cap"),
        }, name
        _coverage(result)
    assert (_tree(root / "src"), _tree(root / "wiki")) == before


def test_factory_uncertainty_has_one_source_owned_reason_and_invocation_location(
    owned_project, monkeypatch, capsys
):
    root = owned_project("service")
    before = _tree(root / "src"), _tree(root / "wiki")
    selector = "dynamic.py:factory_values"
    mcp = McpWikiService("src", "wiki")
    results = [
        dict(api.callees(selector, src_dir="src", wiki_dir="wiki", limit=100)),
        dict(
            api.query_documentation(_request(selector), src_dir="src", wiki_dir="wiki")
        ),
        _cli_symbol(selector, monkeypatch, capsys),
        mcp.query_graph({"type": "callees", "value": selector, "limit": 100}),
        mcp.query_documentation(_request(selector)),
    ]
    collected = get_inventory_result("src", deep=True)
    observed = resolve_call_observations(collected.inventory)["observations"]
    method = next(
        row
        for row in observed
        if row["from"]["symbol"] == "factory_values" and row["name"] == "receiver.cap"
    )
    assert method["kind"] == "unresolved" and method["to"]["file"] is None
    assert method["reason"]
    assert method["location"] == {"source_path": "dynamic.py", "line": 10, "column": 11}
    for result in results:
        assert result["found"] and not result["ambiguous"]
        assert result["callees"] == results[0]["callees"]
        uncertain = next(row for row in result["callees"] if row["line"] == 10)
        assert uncertain["kind"] == "unresolved" and uncertain["file"] is None
        assert uncertain["reason"] == method["reason"]
        assert uncertain["location"] == method["location"]
        _coverage(result)
    assert (_tree(root / "src"), _tree(root / "wiki")) == before


def test_reverse_queries_keep_method_separate_from_constructor_and_graph_samples(
    owned_project,
):
    root = owned_project("library")
    before = _tree(root / "src"), _tree(root / "wiki")
    for selector in ("policy.py:public_values", "client.py:assigned_values"):
        result = dict(api.callees(selector, src_dir="src", wiki_dir="wiki", limit=100))
        assert {TARGET, ("policy.py", "Batch")} <= _pairs(result, "callees")
        _coverage(result)
    typed = api.query_documentation(
        {
            "operation": "typed",
            "value": "llm-wiki://entities/Batch",
            "direction": "incoming",
            "kinds": ["calls"],
            "include_evidence": True,
            "limit": 100,
        },
        src_dir="src",
        wiki_dir="wiki",
    )
    assert "edges" in typed
    samples = [
        sample for edge in typed["edges"] for sample in edge["evidence"]["samples"]
    ]
    methods = [
        sample for sample in samples if sample["target"].get("symbol") == "Batch.cap"
    ]
    assert {
        (sample["source"]["source_path"], sample["source"]["symbol"])
        for sample in methods
    } == {("policy.py", "public_values"), ("client.py", "assigned_values")}
    assert all(sample["location"]["column"] == 12 for sample in methods)
    assigned = next(
        sample for sample in methods if sample["source"]["source_path"] == "client.py"
    )
    assert assigned["location"]["line"] == 6
    assert assigned["attributes"]["constructor"]["line"] == 5
    assert assigned["attributes"]["constructor"]["column"] == 12
    assert (_tree(root / "src"), _tree(root / "wiki")) == before


def test_actual_service_process_flow_and_unresolved_graph_preserve_decisions(
    owned_project,
):
    root = owned_project("service")
    before = _tree(root / "src"), _tree(root / "wiki")
    result = api.flow_for_entrypoint("main", src_dir="src", wiki_dir="wiki", limit=100)
    assert result["found"]
    flow = result["flow"]
    assert flow is not None
    assert any(
        step["file"] == "handlers.py" and step["symbol"] == "list_items"
        for step in flow["steps"]
    )
    assert any(
        step["file"] == "policy.py"
        and step["symbol"] == "Batch.cap"
        and step["kind"] == "internal"
        for step in flow["steps"]
    )
    typed = api.query_documentation(
        {
            "operation": "typed",
            "value": "llm-wiki://modules/dynamic",
            "direction": "outgoing",
            "kinds": ["calls"],
            "include_evidence": True,
            "limit": 100,
        },
        src_dir="src",
        wiki_dir="wiki",
    )
    assert "edges" in typed
    samples = [
        sample for edge in typed["edges"] for sample in edge["evidence"]["samples"]
    ]
    factory = next(
        sample
        for sample in samples
        if sample["source"].get("symbol") == "factory_values"
        and sample["location"].get("line") == 10
    )
    actual = api.callees(
        "dynamic.py:factory_values", src_dir="src", wiki_dir="wiki", limit=100
    )
    uncertain = next(row for row in actual["callees"] if row["line"] == 10)
    assert factory["reason"] == uncertain["reason"]
    assert factory["location"] == {
        "source_path": "dynamic.py",
        "line": 10,
        "column": 12,
    }
    assert factory["target"]["kind"] == "unresolved"
    assert (_tree(root / "src"), _tree(root / "wiki")) == before


def test_static_coverage_qualifies_selected_provided_snapshot_and_empty_results(
    owned_project,
):
    root = owned_project("library")
    before = _tree(root / "src"), _tree(root / "wiki")
    selected = build_live_documentation_query_service(
        source_root=root / "src",
        wiki_root=root / "wiki",
        limit=100,
        read_only=True,
        paths=("policy.py", "client.py"),
    )
    assert _pairs(selected.callers("Batch.cap"), "callers") == {
        ("policy.py", "public_values"),
        ("client.py", "assigned_values"),
    }
    _coverage(selected.callers("Batch.cap"), "selected-source")
    _coverage(selected.callers("absent"), "selected-source")
    collected = get_inventory_result("src", deep=True)
    provided = DocumentationGraphQueryService(
        collected.inventory, call_edges=resolve_call_edges(collected.inventory)
    )
    _coverage(provided.callers("cap"), "provided-inventory")
    empty_provided = DocumentationGraphQueryService({})
    _coverage(dict(api.callers("absent", service=empty_provided)), "provided-inventory")
    snapshot = build_snapshot_documentation_query_service(
        wiki_root=root / "wiki", limit=100
    )
    _coverage(snapshot.callers("absent"), "snapshot")
    missing = dict(api.callers("absent", src_dir="src", wiki_dir="wiki"))
    assert not missing["found"] and missing["callers"] == []
    _coverage(missing)
    assert (_tree(root / "src"), _tree(root / "wiki")) == before


@pytest.mark.parametrize("name", ["library", "service"])
def test_constructor_public_receipts_agree_with_cold_warm_and_cache_disabled_inputs(
    owned_project, name
):
    root = owned_project(name)
    before = _tree(root / "src"), _tree(root / "wiki")
    options = InventoryCacheOptions(enabled=True, cache_dir=str(root / "cache"))
    cold = get_inventory_result("src", deep=True, cache_options=options)
    warm = get_inventory_result("src", deep=True, cache_options=options)
    fresh = get_inventory_result("src", deep=True)
    assert cold.cache_stats is not None and cold.cache_stats.hits == 0
    assert warm.cache_stats is not None and warm.cache_stats.hits == len(
        projects()[name]
    )
    assert warm.cache_stats.fresh_extracted == 0
    assert cold.inventory == warm.inventory == fresh.inventory
    assert (
        resolve_call_observations(cold.inventory)
        == resolve_call_observations(warm.inventory)
        == resolve_call_observations(fresh.inventory)
    )
    projected = DocumentationGraphQueryService(
        warm.inventory, call_edges=resolve_call_edges(warm.inventory)
    )
    actual = api.callers(
        "policy.py:Batch.cap", src_dir="src", wiki_dir="wiki", limit=100
    )
    assert projected.callers("policy.py:Batch.cap")["callers"] == actual["callers"]
    _coverage(projected.callers("policy.py:Batch.cap"), "provided-inventory")
    assert (_tree(root / "src"), _tree(root / "wiki")) == before


def test_actual_narrowing_policy_does_not_claim_full_repository_coverage(
    owned_project, monkeypatch, capsys
):
    root = owned_project("library", selected=True)
    before = _tree(root / "src"), _tree(root / "wiki")
    collected = get_inventory_result("src", deep=True)
    snapshot = collected.source_snapshot
    assert snapshot is not None
    assert snapshot.only_files is None
    assert snapshot.source_selection_policy is not None
    assert set(collected.inventory) == {"policy.py", "client.py"}
    for name, result in _caller_routes("policy.py:Batch.cap", monkeypatch, capsys):
        assert _pairs(result, "callers") == {
            ("policy.py", "public_values"),
            ("client.py", "assigned_values"),
        }, name
        _coverage(result, "selected-source")
    assert (_tree(root / "src"), _tree(root / "wiki")) == before


@pytest.mark.parametrize("name", ["library", "service"])
def test_real_qualified_context_receiving_adapter_accepts_captured_call_metadata(
    owned_project, name
):
    root = owned_project(name)
    before = _tree(root / "src"), _tree(root / "wiki")
    packet = api.build_qualified_context(
        "src",
        "wiki",
        {
            "budget_tokens": 32000,
            "focus": ["all"],
            "format": "json",
            "filters": {},
            "knowledge_mode": "auto",
        },
    )
    payload = packet.to_payload()
    assert payload["schema_version"] == "llm-wiki-qualified-context-packet/v2"
    assert payload["response"]["ok"]
    assert (_tree(root / "src"), _tree(root / "wiki")) == before


@pytest.mark.parametrize("version", [1, 2])
def test_real_task_receiving_adapters_preserve_qualified_constructor_call_facts(
    owned_project, version
):
    root = owned_project("library")
    before = _tree(root / "src"), _tree(root / "wiki")
    request = {
        "schema_version": f"llm-wiki-task-request/v{version}",
        "requirements": [
            {"id": "incoming", "facet": "callers", "selector": "policy.py:Batch.cap"},
            {
                "id": "outgoing",
                "facet": "callees",
                "selector": "policy.py:public_values",
            },
        ],
        "options": {"knowledge_mode": "off"},
    }
    result = api.build_task_context(request, src_dir="src", wiki_dir="wiki")
    received = api.validate_task_context(result.rendered, request)
    assert received["state"] == "covered"
    assert len(received["facts"]) >= 2
    assert all(
        fact["observation"]["coverage"]["runtime_completeness"] is False
        for fact in received["facts"]
    )
    assert (_tree(root / "src"), _tree(root / "wiki")) == before


@pytest.mark.parametrize("version", [1, 2])
def test_real_task_receiving_adapters_retain_factory_uncertainty_without_target_guess(
    owned_project, version
):
    root = owned_project("service")
    before = _tree(root / "src"), _tree(root / "wiki")
    request = {
        "schema_version": f"llm-wiki-task-request/v{version}",
        "requirements": [
            {
                "id": "unknown-dispatch",
                "facet": "callees",
                "selector": "dynamic.py:factory_values",
            }
        ],
        "options": {"knowledge_mode": "off"},
    }
    result = api.build_task_context(request, src_dir="src", wiki_dir="wiki")
    received = api.validate_task_context(result.rendered, request)
    fact = next(fact for fact in received["facts"] if fact["facet"] == "callees")
    unknown = next(row for row in fact["observation"]["callees"] if row["line"] == 10)
    assert unknown["file"] is None and unknown["kind"] == "unresolved"
    assert unknown["reason"]
    assert unknown["location"] == {
        "source_path": "dynamic.py",
        "line": 10,
        "column": 11,
    }
    assert fact["qualification"]["negative_claim_supported"] is False
    assert fact["observation"]["coverage"]["runtime_completeness"] is False
    assert (_tree(root / "src"), _tree(root / "wiki")) == before
