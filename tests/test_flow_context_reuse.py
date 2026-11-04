"""Graph indexes are built once without changing bounded flow observations."""

from __future__ import annotations

from copy import deepcopy
from types import SimpleNamespace
from typing import cast

import pytest

from llm_wiki_cli.commands import sync_cmd
from llm_wiki_cli.services import data_flow, entrypoints


def _entry(symbol):
    return {"id": "api-" + symbol, "category": "api", "file": "app.py",
            "symbol": symbol, "label": symbol}


def _edges():
    def edge(source, target, line, kind="internal"):
        return {"from": {"file": "app.py", "symbol": source},
                "to": {"file": "app.py" if kind == "internal" else None, "symbol": target},
                "line": line, "name": target, "kind": kind,
                "args": [{"kind": "literal", "value": str(line)}]}

    # Legacy order is deliberately different from detailed canonical order.
    return [edge("start", "helper", 20), edge("start", "helper", 10),
            edge("helper", "start", 30), edge("start", "print", 40, "external")]


def _inventory():
    return {"app.py": {"language": "python", "classes": [], "functions": [
        {"name": "start", "calls": [], "effects": {}},
        {"name": "helper", "calls": [], "effects": {}},
    ]}}


@pytest.mark.parametrize("depth", [0, 1, 2, 6])
def test_shared_adjacency_preserves_flow_order_cycles_bounds_and_owned_output(monkeypatch, depth):
    edges = _edges()
    before = deepcopy(edges)
    entries = [_entry("start"), _entry("helper")]
    expected = [(entrypoints.build_flow(entry, edges, max_depth=depth),
                 entrypoints.build_flow_detailed(entry, edges, max_depth=depth))
                for entry in entries]
    context = entrypoints.build_flow_context(edges)

    def unexpected(*args):
        pytest.fail("shared flows must not rebuild adjacency")

    monkeypatch.setattr(entrypoints, "_build_adjacency", unexpected)
    for entry, (legacy, detailed) in zip(entries, expected, strict=True):
        assert entrypoints.build_flow(entry, edges, max_depth=depth, context=context) == legacy
        actual = entrypoints.build_flow_detailed(entry, edges, max_depth=depth, context=context)
        assert actual == detailed
        if len(actual["steps"]) > 1:
            actual["steps"][1]["edge"]["args"].append({"value": "changed output"})
    assert edges == before
    with pytest.raises(TypeError):
        context.adjacency[("app.py", "start")] = ()  # type: ignore[index]


def test_detailed_context_reuses_canonical_indexes_without_changing_legacy_order(monkeypatch):
    edges, inventory = _edges(), _inventory()
    flows = [entrypoints.build_flow_detailed(_entry(symbol), edges)
             for symbol in ("start", "helper")]
    expected_legacy = [data_flow.analyze_data_flow(inventory, flow, edges) for flow in flows]
    expected_detailed = [data_flow.analyze_data_flow_detailed(inventory, flow, edges) for flow in flows]
    context = data_flow.build_data_flow_context(inventory, edges, include_detailed=True)
    assert [edge["line"] for edge in context.incoming_edges[("app.py", "helper", "internal")]] == [20, 10]
    assert context.detailed_incoming_edges is not None
    assert [edge["line"] for edge in context.detailed_incoming_edges[("app.py", "helper", "internal")]] == [10, 20]

    def unexpected(*args):
        pytest.fail("shared data-flow analyses must not sort or rebuild graph indexes")

    monkeypatch.setattr(data_flow, "_callable_index", unexpected)
    monkeypatch.setattr(data_flow, "_incoming_edge_queues", unexpected)
    monkeypatch.setattr(data_flow, "_edge_sort_key", unexpected)
    for flow, legacy, detailed in zip(flows, expected_legacy, expected_detailed, strict=True):
        assert data_flow.analyze_data_flow(inventory, flow, edges, context=context) == legacy
        assert data_flow.analyze_data_flow_detailed(inventory, flow, edges, context=context) == detailed


def test_sync_builds_each_graph_index_once_for_all_selected_flows(tmp_path, monkeypatch):
    edges, inventory = _edges(), _inventory()
    entries = [_entry("start"), _entry("helper")]
    expected_flows = [entrypoints.build_flow_detailed(entry, edges) for entry in entries]
    expected_data = [data_flow.analyze_data_flow_detailed(inventory, flow, edges)
                     for flow in expected_flows]
    counts = {"adjacency": 0, "incoming": 0, "sort_keys": 0}

    def counted(module, name, count):
        original = getattr(module, name)

        def call(*args):
            counts[count] += 1
            return original(*args)

        monkeypatch.setattr(module, name, call)

    counted(entrypoints, "_build_adjacency", "adjacency")
    counted(data_flow, "_incoming_edge_queues", "incoming")
    counted(data_flow, "_edge_sort_key", "sort_keys")
    monkeypatch.setattr(sync_cmd, "resolve_call_edges", lambda *args: edges)
    monkeypatch.setattr(sync_cmd, "resolve_call_observations", lambda *args: {})
    monkeypatch.setattr(sync_cmd, "build_dependency_observations", lambda *args, **kwargs: {})
    monkeypatch.setattr(sync_cmd, "runtime_graph_analyzer_limitations", lambda **kwargs: [])
    monkeypatch.setattr(sync_cmd, "runtime_generation_options", lambda **kwargs: {"data_flow_enabled": True})
    options = SimpleNamespace(initialize_surfaces=(), wiki_dir=tmp_path, src_dir=tmp_path,
                              include_tests=False, preserve_semantic=False)
    surface = SimpleNamespace(flow_entries=entries, new_flow_entries=(), surfaces={},
                              generation_inputs={}, excluded_dependency_tests=0)

    result = sync_cmd._build_sync_graph_observations(
        cast(sync_cmd._SyncRunOptions, options), inventory,
        cast(sync_cmd.SourceSnapshot, None), entries, {},
        cast(sync_cmd._SurfaceInitializationPlan, surface), None,
    )

    assert result.flows == expected_flows
    assert result.data_flows == expected_data
    assert counts == {"adjacency": 1, "incoming": 2, "sort_keys": len(edges)}
