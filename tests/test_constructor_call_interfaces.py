"""Real read interfaces share conservative caller decisions on owned sources."""

from __future__ import annotations

import io
from hashlib import sha256
import json
from pathlib import Path
import sys
import os
import subprocess
from typing import Any
from types import SimpleNamespace

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
from llm_wiki_cli.services.entrypoints import build_flow
from llm_wiki_cli.services.knowledge_graph import (
    GraphConcept,
    KnowledgeGraphInputs,
    materialize_typed_graph,
)
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


def _callee_routes(selector, monkeypatch, capsys):
    mcp = McpWikiService("src", "wiki")
    return [
        dict(api.callees(selector, src_dir="src", wiki_dir="wiki", limit=100)),
        dict(
            api.query_documentation(_request(selector), src_dir="src", wiki_dir="wiki")
        ),
        _cli_symbol(selector, monkeypatch, capsys),
        mcp.query_graph({"type": "callees", "value": selector, "limit": 100}),
        mcp.query_documentation(_request(selector)),
    ]


_RECEIVER_CONTROLS = [
    case
    for filename in (
        "python_constructor_namespace.json",
        "python_constructor_expressions.json",
    )
    for case in json.loads((Path(__file__).parent / "fixtures" / filename).read_text())
]


@pytest.mark.parametrize("case", _RECEIVER_CONTROLS, ids=lambda case: case["id"])
def test_receiver_controls_share_exact_decisions_across_receiving_interfaces(
    tmp_path, monkeypatch, capsys, case
):
    minimum = tuple(int(part) for part in case["minimum_python"].split("."))
    if sys.version_info[:2] < minimum:
        pytest.skip("Owned syntax requires Python " + case["minimum_python"])
    monkeypatch.chdir(tmp_path)
    source = tmp_path / "src"
    source.mkdir()
    for name, text in case["sources"].items():
        path = source / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
    # An absent wiki also exercises live reads without implicit adoption/migration.
    before = _tree(tmp_path)
    collected = get_inventory_result("src", deep=True)
    legacy = resolve_call_edges(collected.inventory)
    observations = resolve_call_observations(collected.inventory)["observations"]
    supplied = DocumentationGraphQueryService(collected.inventory, call_edges=legacy)
    concepts = [
        GraphConcept(
            locator="llm-wiki://modules/" + Path(name).stem,
            concept_kind="source-module",
            source_path=name,
        )
        for name in collected.inventory
    ]
    for probe in case["probes"]:
        location = {
            "source_path": probe["file"],
            "line": probe["line"],
            "column": probe["column"],
        }
        origin = {"file": probe["file"], "symbol": probe["caller"]}
        matches = [
            edge
            for edge in observations
            if edge["from"] == origin
            and edge.get("location") == location
            and edge["name"].rsplit(".", 1)[-1] == probe["member"]
        ]
        assert len(matches) == 1
        observed = matches[0]
        old = next(
            edge
            for edge in legacy
            if edge["from"] == origin
            and edge.get("location") == location
            and edge["name"] == observed["name"]
        )
        for key in (
            "to",
            "reason",
            "location",
            "resolution",
            "candidates",
            "constructor",
        ):
            assert old.get(key) == observed.get(key), key
        if observed["kind"] == "internal":
            target = observed["to"]["file"] + ":" + observed["to"]["symbol"]
            assert target in probe["allowed"]
            assert not probe["required"] or target in probe["required"]
        else:
            assert not probe["required"] and observed.get("reason")
            assert observed["kind"] in {"unresolved", "ambiguous"}
        selector = probe["file"] + ":" + probe["caller"]
        routes = [
            supplied.callees(selector),
            *_callee_routes(selector, monkeypatch, capsys),
        ]
        expected = routes[0]["callees"]
        for index, result in enumerate(routes):
            assert result["found"] and not result["ambiguous"]
            assert result["callees"] == expected
            _coverage(result, "provided-inventory" if index == 0 else "full-inventory")
        short = probe["caller"].rsplit(".", 1)[-1]
        if supplied.callees(short)["found"]:
            for result in _callee_routes(short, monkeypatch, capsys):
                assert result["found"] and not result["ambiguous"]
                assert result["callees"] == expected
        projected = [
            edge
            for edge in expected
            if edge.get("location") == location
            and edge["symbol"].rsplit(".", 1)[-1] == probe["member"]
        ]
        assert len(projected) == 1
        assert projected[0]["reason"] == observed["reason"]
        assert projected[0]["kind"] == old["kind"]
        # Isolate one occurrence so graph evidence bounds cannot hide this probe.
        graph = materialize_typed_graph(
            KnowledgeGraphInputs(
                inventory=collected.inventory, concepts=concepts, call_edges=[observed]
            )
        )
        samples = [
            sample
            for edge in graph["edges"]
            if edge["kind"] == "calls"
            for sample in edge["evidence"]["samples"]
        ]
        assert len(samples) == 1
        sample = samples[0]
        assert sample["reason"] == observed["reason"]
        assert sample["location"] == {**location, "column": probe["column"] + 1}
        assert sample["target"]["kind"] != "unresolved" or old["kind"] != "internal"
        if old["kind"] == "internal":
            assert sample["target"]["source_path"] == old["to"]["file"]
            assert sample["target"]["symbol"] == old["to"]["symbol"]
        for key in ("constructor", "candidates"):
            if key in observed:
                assert sample["attributes"][key] == observed[key]
        flow = build_flow(origin, [old])
        assert len(flow["steps"]) == 2
        step = flow["steps"][1]
        assert step["kind"] == old["kind"]
        for key in ("reason", "location", "resolution", "constructor", "candidates"):
            assert step["edge"].get(key) == old.get(key), key
        assert (step["file"], step["symbol"]) == (
            old["to"]["file"],
            old["to"]["symbol"],
        )
        # Both directions must use the same call occurrence, including negatives.
        for declaration in probe["candidate_declarations"]:
            target = declaration["target"]
            if target.rsplit(".", 1)[-1] != probe["member"]:
                continue
            incoming = supplied.callers(target)
            for name, actual in _caller_routes(target, monkeypatch, capsys):
                assert incoming["callers"] == actual["callers"], name
            short = target.split(":", 1)[1]
            if supplied.callers(short)["found"]:
                for name, actual in _caller_routes(short, monkeypatch, capsys):
                    assert actual["found"] and not actual["ambiguous"], name
                    assert incoming["callers"] == actual["callers"], name
            occurrences = [
                row
                for row in incoming["callers"]
                if row.get("location") == location
                and (row["file"], row["symbol"]) == (probe["file"], probe["caller"])
            ]
            asserted = old["kind"] == "internal" and target == (
                old["to"]["file"] + ":" + old["to"]["symbol"]
            )
            assert len(occurrences) == int(asserted)
    assert _tree(tmp_path) == before


@pytest.mark.parametrize(
    "selected", [None, ["app.py", "facade.py"], ["app.py", "policy.py"]]
)
def test_import_alias_selection_and_cached_restart_cannot_borrow_excluded_authority(
    tmp_path, monkeypatch, capsys, selected
):
    monkeypatch.chdir(tmp_path)
    source = tmp_path / "src"
    source.mkdir()
    sources = {
        "app.py": "from facade import Alias\ndef run(values): return Alias().cap(values)\n",
        "facade.py": "from policy import Batch as Alias\n",
        "policy.py": "class Batch:\n    def cap(self, values): return values\nraise RuntimeError('parse only')\n",
    }
    for name, text in sources.items():
        (source / name).write_text(text)
    cache = tmp_path / "cache"
    options = InventoryCacheOptions(enabled=True, cache_dir=str(cache))
    full = get_inventory_result("src", deep=True, cache_options=options)
    assert (
        DocumentationGraphQueryService(
            full.inventory, call_edges=resolve_call_edges(full.inventory)
        ).callees("app.py:run")["callees"][0]["file"]
        == "policy.py"
    )
    if selected is not None:
        policy = source / ".llm-wiki/source-selection.json"
        policy.parent.mkdir()
        policy.write_text(
            json.dumps(
                {
                    "schema_version": SOURCE_SELECTION_SCHEMA_VERSION,
                    "include": selected,
                    "exclude": [],
                }
            )
        )
    # Anchor the selected profile through an explicitly authorized setup write.
    api.bootstrap_wiki("src", "wiki")
    capsys.readouterr()
    cold = get_inventory_result("src", deep=True, cache_options=options)
    warm = get_inventory_result("src", deep=True, cache_options=options)
    disabled = get_inventory_result("src", deep=True)
    assert cold.inventory == warm.inventory == disabled.inventory
    assert warm.cache_stats is not None and warm.cache_stats.hits == len(warm.inventory)
    repo = Path(__file__).resolve().parents[1]
    environment = dict(os.environ)
    environment["PYTHONPATH"] = (
        str(repo / "src") + os.pathsep + environment.get("PYTHONPATH", "")
    )
    code = (
        "import json; from llm_wiki_cli.services.extraction_service import get_inventory_result; "
        "from llm_wiki_cli.services.inventory_cache import InventoryCacheOptions; "
        "r=get_inventory_result('src',deep=True,cache_options=InventoryCacheOptions(enabled=True,cache_dir='cache')); "
        "print(json.dumps({'inventory':r.inventory,'hits':r.cache_stats.hits,'fresh':r.cache_stats.fresh_extracted}))"
    )
    before = _tree(tmp_path)
    restarted = subprocess.run(
        [str(repo / ".venv/bin/python"), "-c", code],
        cwd=tmp_path,
        env=environment,
        capture_output=True,
        text=True,
        check=True,
        timeout=60,
    )
    receipt = json.loads(restarted.stdout)
    assert receipt["inventory"] == warm.inventory
    assert receipt["hits"] == len(warm.inventory) and receipt["fresh"] == 0
    for result in _callee_routes("app.py:run", monkeypatch, capsys):
        method = next(row for row in result["callees"] if row["symbol"].endswith("cap"))
        if selected is None:
            assert method["kind"] == "internal" and method["file"] == "policy.py"
        else:
            assert method["kind"] == "unresolved" and method["file"] is None
            assert method["reason"] == "constructor-source-unavailable"
        assert method["location"] == {"source_path": "app.py", "line": 2, "column": 24}
        _coverage(result, "full-inventory" if selected is None else "selected-source")
    assert _tree(tmp_path) == before


def test_producer_incompatibility_does_not_upgrade_snapshot_or_borrow_old_call_edges(
    owned_project, monkeypatch, capsys
):
    from llm_wiki_cli.services import analysis_capture, context_packet

    root = owned_project("library")
    target = "llm-wiki://modules/client"
    before = _tree(root / "src"), _tree(root / "wiki")
    captured = analysis_capture.implementation_hash

    def changed_producer(root, paths):
        return (
            "sha256:"
            + sha256(("changed-provider:" + captured(root, paths)).encode()).hexdigest()
        )

    monkeypatch.setattr(analysis_capture, "implementation_hash", changed_producer)
    mcp = McpWikiService("src", "wiki")
    live = api.inspect_concept(target, src_dir="src", wiki_dir="wiki", live=True)
    assert live == mcp.inspect_concept(target, live=True)
    concept = live["concept"]["concept"]
    assert concept is not None
    assert concept["implementation"]["state"] == "unavailable"
    assert concept["implementation"]["reason"] == "producer-incompatible"
    assert concept["implementation"]["live_comparison_performed"] is False
    assert concept["freshness"]["state"] == "basis-incompatible"
    # Current live call authority remains independently captured and qualified.
    for name, result in _caller_routes("policy.py:Batch.cap", monkeypatch, capsys):
        assert _pairs(result, "callers") == {
            ("policy.py", "public_values"),
            ("client.py", "assigned_values"),
        }, name
    monkeypatch.setattr(
        context_packet,
        "capture_context_read",
        lambda *args, **kwargs: pytest.fail(
            "snapshot read captured application source"
        ),
    )
    snapshot = api.inspect_concept(target, src_dir="src", wiki_dir="wiki")
    assert snapshot == mcp.inspect_concept(target)
    assert snapshot["read_scope"] == "snapshot-only"
    concept = snapshot["concept"]["concept"]
    assert concept is not None
    comparison = concept["implementation"]
    assert (
        comparison["state"] == "unavailable"
        and not comparison["live_comparison_performed"]
    )
    assert (_tree(root / "src"), _tree(root / "wiki")) == before


def test_flow_metadata_is_optional_for_legacy_edges_and_independent_of_input_mutation():
    origin = {"file": "app.py", "symbol": "run"}
    legacy = {
        "from": origin,
        "to": {"file": "app.py", "symbol": "Batch.cap"},
        "name": "batch.cap",
        "kind": "internal",
        "line": 4,
    }
    flow = build_flow(origin, [legacy])
    assert flow["steps"][1]["edge"] == legacy
    current = {
        **legacy,
        "reason": "constructed-receiver-resolved",
        "location": {
            "source_path": "app.py",
            "line": 4,
            "column": 11,
        },
        "constructor": {"members": ["cap"]},
    }
    flow = build_flow(origin, [current])
    current["location"]["line"] = 999
    current["constructor"]["members"].clear()
    assert flow["steps"][1]["edge"]["location"]["line"] == 4
    assert flow["steps"][1]["edge"]["constructor"]["members"] == ["cap"]


@pytest.mark.parametrize(
    "body", ["return Batch().cap()", "batch = Batch(); return batch.cap()"]
)
@pytest.mark.parametrize("retain_column", [False, True])
def test_legacy_supplied_inventory_keeps_uncertainty_reason_and_actual_location(
    tmp_path, monkeypatch, capsys, body, retain_column
):
    from llm_wiki_cli.services import extraction_service

    monkeypatch.chdir(tmp_path)
    Path("src").mkdir()
    Path("src/app.py").write_text(
        "class Batch:\n    def cap(self): return 1\ndef run(): " + body + "\n"
    )
    legacy = get_inventory_result("src", deep=True).inventory
    function = legacy["app.py"]["functions"][0]
    function.pop("call_bindings")
    if not retain_column:
        for call in function["calls"]:
            call.pop("column", None)
    # Supply the older captured inventory at the extraction boundary; the real
    # builders and adapters must neither reconstruct missing authority nor facts.
    monkeypatch.setattr(
        extraction_service,
        "build_extract_payload",
        lambda *args, **kwargs: SimpleNamespace(
            payload={"inventory": legacy, "entrypoints": []}, inventory_result=None
        ),
    )
    before = _tree(tmp_path), json.dumps(legacy, sort_keys=True)
    edges = resolve_call_edges(legacy)
    observed = resolve_call_observations(legacy)["observations"]
    method = next(edge for edge in observed if edge["name"].endswith("cap"))
    assert method["kind"] == "unresolved" and method["to"]["file"] is None
    assert method["reason"] == "call-binding-unavailable"
    assert (
        method["location"]["source_path"] == "app.py"
        and method["location"]["line"] == 3
    )
    assert ("column" in method["location"]) == retain_column
    assert any(edge["to"] == {"file": "app.py", "symbol": "Batch"} for edge in edges)
    for result in _callee_routes("app.py:run", monkeypatch, capsys):
        actual = next(edge for edge in result["callees"] if edge["symbol"] == "cap")
        assert actual["kind"] == "unresolved" and actual["file"] is None
        assert (
            actual["reason"] == method["reason"]
            and actual["location"] == method["location"]
        )
    for name, result in _caller_routes("app.py:Batch.cap", monkeypatch, capsys):
        assert result["callers"] == [], name
    flow = build_flow(method["from"], [method])
    assert flow["steps"][1]["edge"]["reason"] == method["reason"]
    assert flow["steps"][1]["edge"]["location"] == method["location"]
    graph = materialize_typed_graph(
        KnowledgeGraphInputs(
            inventory=legacy,
            concepts=[
                GraphConcept(
                    locator="llm-wiki://modules/app",
                    concept_kind="source-module",
                    source_path="app.py",
                )
            ],
            call_edges=[method],
        )
    )
    sample = next(edge for edge in graph["edges"] if edge["kind"] == "calls")[
        "evidence"
    ]["samples"][0]
    assert sample["reason"] == method["reason"]
    assert sample["location"].get("column") == (
        method["location"]["column"] + 1 if retain_column else None
    )
    assert (_tree(tmp_path), json.dumps(legacy, sort_keys=True)) == before


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
