"""Tests for services/data_flow.py."""

import json

from llm_wiki_cli.services import data_flow as data_flow_module
from llm_wiki_cli.services.data_flow import analyze_data_flow, build_data_flow_context


def test_analyze_data_flow_orders_steps_boundaries_transfers_and_gaps():
    inventory = {
        "svc.py": {
            "language": "python",
            "classes": [],
            "functions": [
                {
                    "name": "run",
                    "calls": [
                        {
                            "name": "helper",
                            "line": 4,
                            "args": [{"kind": "name", "value": "payload"}],
                        },
                        {
                            "name": "write_text",
                            "attr": "output_path.write_text",
                            "line": 5,
                            "args": [{"kind": "name", "value": "result"}],
                        },
                        {
                            "name": "publish",
                            "attr": "client.publish",
                            "line": 6,
                            "args": [{"kind": "name", "value": "result"}],
                        },
                    ],
                    "data_effects": {
                        "inputs": [
                            {"kind": "param", "name": "payload", "type": "dict"}
                        ],
                        "returns": [{"kind": "name", "value": "result", "line": 7}],
                        "boundary_effects": [
                            {
                                "kind": "filesystem_write",
                                "target": "output_path.write_text",
                                "line": 5,
                            }
                        ],
                    },
                },
                {
                    "name": "helper",
                    "data_effects": {
                        "inputs": [{"kind": "param", "name": "payload", "type": ""}],
                        "returns": [{"kind": "name", "value": "payload", "line": 10}],
                    },
                },
            ],
        }
    }
    edges = [
        {
            "from": {"file": "svc.py", "symbol": "run"},
            "to": {"file": "svc.py", "symbol": "helper"},
            "name": "helper",
            "kind": "internal",
            "line": 4,
        },
        {
            "from": {"file": "svc.py", "symbol": "run"},
            "to": {"file": None, "symbol": "write_text"},
            "name": "output_path.write_text",
            "kind": "unresolved",
            "line": 5,
        },
        {
            "from": {"file": "svc.py", "symbol": "run"},
            "to": {"file": None, "symbol": "publish"},
            "name": "client.publish",
            "kind": "unresolved",
            "line": 6,
        },
    ]
    flow = {
        "entry": {
            "id": "api-run",
            "category": "api",
            "file": "svc.py",
            "symbol": "run",
            "label": "run",
        },
        "steps": [
            {"depth": 0, "file": "svc.py", "symbol": "run", "kind": "entry"},
            {"depth": 1, "file": "svc.py", "symbol": "helper", "kind": "internal"},
            {
                "depth": 1,
                "file": None,
                "symbol": "write_text",
                "kind": "unresolved",
            },
            {"depth": 1, "file": None, "symbol": "publish", "kind": "unresolved"},
        ],
        "modules_touched": ["svc.py"],
        "truncated": False,
    }

    data_flow = analyze_data_flow(inventory, flow, edges)

    assert data_flow["id"] == "api-run"
    assert [step["symbol"] for step in data_flow["steps"]] == [
        "run",
        "helper",
        "write_text",
        "publish",
    ]
    assert data_flow["steps"][0]["inputs"] == [
        {"kind": "param", "name": "payload", "type": "dict"}
    ]
    assert data_flow["boundaries"] == [
        {
            "step": "run",
            "step_index": 1,
            "kind": "filesystem_write",
            "target": "output_path.write_text",
            "line": 5,
        }
    ]
    assert [transfer["call"] for transfer in data_flow["transfers"]] == [
        "helper(payload)",
        "output_path.write_text(result)",
        "client.publish(result)",
    ]
    assert data_flow["gaps"] == [
        {
            "kind": "unresolved_call",
            "step": "run",
            "target": "client.publish",
            "line": 6,
        }
    ]
    json.dumps(data_flow, sort_keys=True)


def test_reusable_context_does_not_rebuild_indexes_or_leak_edges(monkeypatch):
    inventory = {
        "svc.py": {
            "language": "python",
            "classes": [],
            "functions": [
                {
                    "name": "run",
                    "calls": [
                        {"name": "helper", "line": 4},
                        {"name": "helper", "line": 5},
                    ],
                },
                {"name": "helper"},
            ],
        }
    }
    edges = [
        {
            "from": {"file": "svc.py", "symbol": "run"},
            "to": {"file": "svc.py", "symbol": "helper"},
            "name": "helper",
            "kind": "internal",
            "line": 4,
        },
        {
            "from": {"file": "svc.py", "symbol": "run"},
            "to": {"file": "svc.py", "symbol": "helper"},
            "name": "helper",
            "kind": "internal",
            "line": 5,
        },
    ]
    flow = {
        "entry": {
            "id": "api-run",
            "category": "api",
            "file": "svc.py",
            "symbol": "run",
            "label": "run",
        },
        "steps": [
            {"depth": 0, "file": "svc.py", "symbol": "run", "kind": "entry"},
            {"depth": 1, "file": "svc.py", "symbol": "helper", "kind": "internal"},
            {"depth": 1, "file": "svc.py", "symbol": "helper", "kind": "internal"},
        ],
        "modules_touched": ["svc.py"],
        "truncated": False,
    }
    context = build_data_flow_context(inventory, edges)

    def fail_rebuild(*args, **kwargs):
        raise AssertionError("context should reuse prebuilt data-flow indexes")

    monkeypatch.setattr(data_flow_module, "_callable_index", fail_rebuild)
    monkeypatch.setattr(data_flow_module, "_incoming_edge_queues", fail_rebuild)

    first = analyze_data_flow(inventory, flow, edges, context=context)
    second = analyze_data_flow(inventory, flow, edges, context=context)

    assert [transfer["line"] for transfer in first["transfers"]] == [4, 5]
    assert [transfer["line"] for transfer in second["transfers"]] == [4, 5]


def test_step_edge_metadata_prevents_unrelated_callers_from_leaking_into_flow():
    inventory = {
        "svc.py": {
            "language": "python",
            "classes": [],
            "functions": [
                {
                    "name": "other",
                    "calls": [
                        {
                            "name": "helper",
                            "line": 2,
                            "args": [{"kind": "literal", "value": "'other'"}],
                        }
                    ],
                },
                {
                    "name": "run",
                    "calls": [
                        {
                            "name": "helper",
                            "line": 6,
                            "args": [{"kind": "literal", "value": "'run'"}],
                        }
                    ],
                },
                {"name": "helper"},
            ],
        }
    }
    edges = [
        {
            "from": {"file": "svc.py", "symbol": "other"},
            "to": {"file": "svc.py", "symbol": "helper"},
            "name": "helper",
            "kind": "internal",
            "line": 2,
            "args": [{"kind": "literal", "value": "'other'"}],
        },
        {
            "from": {"file": "svc.py", "symbol": "run"},
            "to": {"file": "svc.py", "symbol": "helper"},
            "name": "helper",
            "kind": "internal",
            "line": 6,
            "args": [{"kind": "literal", "value": "'run'"}],
        },
    ]
    flow = {
        "entry": {
            "id": "api-run",
            "category": "api",
            "file": "svc.py",
            "symbol": "run",
            "label": "run",
        },
        "steps": [
            {"depth": 0, "file": "svc.py", "symbol": "run", "kind": "entry"},
            {
                "depth": 1,
                "file": "svc.py",
                "symbol": "helper",
                "kind": "internal",
                "edge": edges[1],
            },
        ],
        "modules_touched": ["svc.py"],
        "truncated": False,
    }

    data_flow = analyze_data_flow(inventory, flow, edges)

    assert data_flow["transfers"] == [
        {
            "from": "run",
            "to": "helper",
            "from_step": 1,
            "to_step": 2,
            "line": 6,
            "call": "helper('run')",
            "arguments": ["'run'"],
            "kind": "internal",
        }
    ]


def test_repeated_helper_calls_and_unknown_arguments_are_distinct_transfers():
    inventory = {
        "svc.py": {
            "language": "python",
            "classes": [],
            "functions": [
                {
                    "name": "run",
                    "calls": [
                        {"name": "helper", "line": 2},
                        {
                            "name": "helper",
                            "line": 3,
                            "args": [{"kind": "literal", "value": "'known'"}],
                        },
                    ],
                },
                {"name": "helper"},
            ],
        }
    }
    edges = [
        {
            "from": {"file": "svc.py", "symbol": "run"},
            "to": {"file": "svc.py", "symbol": "helper"},
            "name": "helper",
            "kind": "internal",
            "line": 2,
        },
        {
            "from": {"file": "svc.py", "symbol": "run"},
            "to": {"file": "svc.py", "symbol": "helper"},
            "name": "helper",
            "kind": "internal",
            "line": 3,
            "args": [{"kind": "literal", "value": "'known'"}],
        },
    ]
    flow = {
        "entry": {
            "id": "api-run",
            "category": "api",
            "file": "svc.py",
            "symbol": "run",
            "label": "run",
        },
        "steps": [
            {"depth": 0, "file": "svc.py", "symbol": "run", "kind": "entry"},
            {
                "depth": 1,
                "file": "svc.py",
                "symbol": "helper",
                "kind": "internal",
                "edge": edges[0],
            },
            {
                "depth": 1,
                "file": "svc.py",
                "symbol": "helper",
                "kind": "internal",
                "edge": edges[1],
            },
        ],
        "modules_touched": ["svc.py"],
        "truncated": False,
    }

    data_flow = analyze_data_flow(inventory, flow, edges)

    assert [transfer["call"] for transfer in data_flow["transfers"]] == [
        "helper(data not statically known)",
        "helper('known')",
    ]
    assert [
        (transfer["from_step"], transfer["to_step"])
        for transfer in data_flow["transfers"]
    ] == [
        (1, 2),
        (1, 3),
    ]
