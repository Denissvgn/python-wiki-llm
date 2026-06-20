"""Tests for services/data_flow.py."""

import json

from llm_wiki_cli.services.data_flow import analyze_data_flow


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
