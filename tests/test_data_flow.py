"""Tests for services/data_flow.py."""

import json

from llm_wiki_cli.extractors.python_extractor import PythonExtractor
from llm_wiki_cli.services import data_flow as data_flow_module
from llm_wiki_cli.services.data_flow import (
    analyze_data_flow,
    analyze_data_flow_detailed,
    build_data_flow_context,
)


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
            "confidence": "unknown",
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


def test_detailed_data_flow_reports_every_bound_and_uses_none_for_unknown_lines():
    effect_records = [
        {"kind": "name", "value": f"value_{index}", "line": 0}
        for index in range(10)
    ]
    inventory = {
        "svc.py": {
            "language": "python",
            "classes": [],
            "functions": [
                {
                    "name": "run",
                    "data_effects": {
                        "inputs": list(effect_records),
                        "reads": list(effect_records),
                        "writes": list(effect_records),
                        "returns": list(effect_records),
                        "boundary_effects": [
                            {
                                "kind": "network_write",
                                "target": f"client_{index}",
                                "line": 0,
                            }
                            for index in range(10)
                        ],
                    },
                }
            ],
        }
    }
    external_edges = [
        {
            "from": {"file": "svc.py", "symbol": "run"},
            "to": {"file": None, "symbol": f"publish_{index}"},
            "name": f"client.publish_{index}",
            "kind": "external",
        }
        for index in range(13)
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
            *[
                {
                    "depth": 1,
                    "file": None,
                    "symbol": f"publish_{index}",
                    "kind": "external",
                    "edge": edge,
                }
                for index, edge in enumerate(external_edges)
            ],
        ],
        "modules_touched": ["svc.py"],
        "truncated": True,
    }

    legacy = analyze_data_flow(inventory, flow, external_edges)
    detailed = analyze_data_flow_detailed(inventory, flow, external_edges)

    assert set(legacy) == {
        "id",
        "entry",
        "steps",
        "transfers",
        "boundaries",
        "gaps",
        "truncated",
    }
    assert legacy["transfers"][0]["line"] == 0
    assert legacy["boundaries"][0]["line"] == 0
    assert detailed["schema_version"] == "llm-wiki-data-flow-observations/v1"
    assert detailed["transfers"][0]["line"] is None
    assert detailed["boundaries"][0]["line"] is None
    assert detailed["steps"][0]["inputs"][0]["line"] is None
    assert '"line": 0' not in json.dumps(detailed, sort_keys=True)

    assert detailed["coverage"]["steps"] == {
        "observed": 14,
        "emitted": 12,
        "limit": 12,
        "truncated": True,
        "omitted": 2,
        "limitations": [
            "flow-steps-are-statically-inferred",
            "upstream-flow-depth-limit-reached",
        ],
    }
    assert detailed["coverage"]["effects"]["observed"] == 50
    assert detailed["coverage"]["effects"]["emitted"] == 40
    assert detailed["coverage"]["effects"]["limit"] == 480
    assert detailed["coverage"]["effects"]["truncated"] is True
    assert detailed["coverage"]["effects"]["omitted"] == 10
    for kind in (
        "inputs",
        "reads",
        "writes",
        "returns",
        "boundary_effects",
    ):
        assert detailed["coverage"]["effects"]["by_kind"][kind]["observed"] == 10
        assert detailed["coverage"]["effects"]["by_kind"][kind]["emitted"] == 8
        assert detailed["coverage"]["effects"]["by_kind"][kind]["limit"] == 96
        assert detailed["coverage"]["effects"]["by_kind"][kind]["truncated"] is True
        assert detailed["coverage"]["effects"]["by_kind"][kind]["omitted"] == 2
        assert detailed["coverage"]["effects"]["by_kind"][kind]["limitations"]
    assert detailed["coverage"]["transfers"]["observed"] == 13
    assert detailed["coverage"]["transfers"]["emitted"] == 11
    assert detailed["coverage"]["transfers"]["limit"] == 12
    assert detailed["coverage"]["transfers"]["omitted"] == 2
    assert detailed["coverage"]["boundaries"]["observed"] == 10
    assert detailed["coverage"]["boundaries"]["emitted"] == 8
    assert detailed["coverage"]["boundaries"]["limit"] == 8
    assert detailed["coverage"]["boundaries"]["omitted"] == 2
    assert detailed["coverage"]["gaps"]["observed"] == 15
    assert detailed["coverage"]["gaps"]["emitted"] == 12
    assert detailed["coverage"]["gaps"]["limit"] == 12
    assert detailed["coverage"]["gaps"]["omitted"] == 3


def test_detailed_data_flow_is_deterministic_for_shuffled_inventory_and_edges():
    first_inventory = {
        "svc.py": {
            "classes": [],
            "functions": [{"name": "run"}, {"name": "helper"}],
        },
        "other.py": {"classes": [], "functions": []},
    }
    second_inventory = dict(reversed(list(first_inventory.items())))
    edges = [
        {
            "from": {"file": "svc.py", "symbol": "run"},
            "to": {"file": "svc.py", "symbol": "helper"},
            "name": "helper",
            "kind": "internal",
            "line": 5,
        },
        {
            "from": {"file": "svc.py", "symbol": "run"},
            "to": {"file": "svc.py", "symbol": "helper"},
            "name": "helper",
            "kind": "internal",
            "line": 2,
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
        "truncated": False,
    }

    first = analyze_data_flow_detailed(first_inventory, flow, edges)
    second = analyze_data_flow_detailed(
        second_inventory, flow, list(reversed(edges))
    )

    assert first == second
    assert [transfer["line"] for transfer in first["transfers"]] == [2, 5]


def test_detailed_data_flow_uses_raw_effect_totals_from_extractor_sidecar(tmp_path):
    module_constants = "\n".join(f"CONFIG_{index} = {index}" for index in range(20))
    reads = ", ".join(f"CONFIG_{index}" for index in range(20))
    (tmp_path / "svc.py").write_text(
        f"{module_constants}\n\n\ndef run():\n    return ({reads})\n"
    )
    extractor = PythonExtractor()
    inventory = extractor.extract(
        str(tmp_path),
        deep=True,
        capture_data_effect_observations=True,
    )
    sidecar = extractor.last_data_effect_observations
    assert sidecar is not None
    flow = {
        "entry": {
            "id": "api-run",
            "category": "api",
            "file": "svc.py",
            "symbol": "run",
            "label": "run",
        },
        "steps": [
            {"depth": 0, "file": "svc.py", "symbol": "run", "kind": "entry"}
        ],
        "truncated": False,
    }

    legacy = analyze_data_flow(inventory, flow, [])
    detailed = analyze_data_flow_detailed(
        inventory,
        flow,
        [],
        data_effect_observations=sidecar,
    )
    context = build_data_flow_context(
        inventory,
        [],
        data_effect_observations=sidecar,
    )

    assert len(legacy["steps"][0]["reads"]) == 8
    assert analyze_data_flow_detailed(inventory, flow, [], context=context) == detailed
    assert detailed["coverage"]["effects"]["by_kind"]["reads"] == {
        "observed": 20,
        "emitted": 8,
        "limit": 8,
        "truncated": True,
        "omitted": 12,
        "limitations": [
            "limit-applies-per-effect-kind-per-emitted-step",
            "static-effects-do-not-claim-runtime-completeness",
        ],
    }


def test_detailed_data_flow_propagates_exact_reachable_flow_step_count():
    inventory = {
        "svc.py": {
            "functions": [{"name": "run"}],
            "classes": [],
        }
    }
    flow = {
        "entry": {
            "id": "api-run",
            "category": "api",
            "file": "svc.py",
            "symbol": "run",
            "label": "run",
        },
        "steps": [
            {"depth": 0, "file": "svc.py", "symbol": "run", "kind": "entry"}
        ],
        "truncated": True,
        "schema_version": "llm-wiki-flow-observations/v1",
        "coverage": {
            "steps": {
                "observed": 4,
                "emitted": 1,
                "omitted": 3,
                "limit": None,
                "depth_limit": 0,
                "truncated": True,
                "limitations": ["flow-steps-are-statically-inferred"],
            }
        },
    }

    detailed = analyze_data_flow_detailed(inventory, flow, [])

    assert detailed["coverage"]["steps"] == {
        "observed": 4,
        "emitted": 1,
        "limit": 12,
        "truncated": True,
        "omitted": 3,
        "limitations": [
            "flow-steps-are-statically-inferred",
            "upstream-flow-depth-limit-reached",
        ],
    }
