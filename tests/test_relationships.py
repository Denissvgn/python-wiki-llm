"""Tests for services/relationships.py."""

from __future__ import annotations

from llm_wiki_cli.services.relationships import (
    build_detailed_entity_relationship_summaries,
    build_entity_relationship_summaries,
)


def _by_class(result):
    return {(item["name"], item["file"]): item for item in result["classes"]}


def _by_symbol(result):
    return {(item["symbol"], item["file"]): item for item in result["functions"]}


def test_class_summaries_include_inheritance_attributes_and_references():
    inventory = {
        "models.py": {
            "classes": [
                {
                    "name": "User",
                    "bases": ["Base"],
                    "attributes": [
                        {"name": "email", "type": "str"},
                        {"name": "id", "type": "int"},
                    ],
                    "methods": [{"name": "save"}],
                },
                {"name": "Base", "bases": [], "attributes": [], "methods": []},
            ],
            "functions": [],
            "imports": [],
        },
        "admin.py": {
            "classes": [
                {
                    "name": "Admin",
                    "bases": ["Base"],
                    "attributes": [{"name": "role", "type": "str"}],
                    "methods": [{"name": "authorize"}, {"name": "save"}],
                }
            ],
            "functions": [],
            "imports": [{"module": "models", "name": "Base"}],
        },
        "api.py": {
            "classes": [],
            "functions": [
                {
                    "name": "create_user",
                    "params": [{"name": "payload", "type": "User"}],
                    "return_type": "User",
                    "decorators": [],
                }
            ],
            "imports": [{"module": "models", "name": "User"}],
        },
        "repo.py": {
            "classes": [],
            "functions": [{"name": "list_users", "params": [], "return_type": ""}],
            "imports": [{"module": "models", "name": "User"}],
        },
    }
    call_edges = [
        {
            "from": {"file": "api.py", "symbol": "create_user"},
            "to": {"file": "models.py", "symbol": "User"},
            "name": "User",
            "kind": "internal",
            "line": 7,
        }
    ]

    result = build_entity_relationship_summaries(inventory, call_edges=call_edges)
    classes = _by_class(result)

    assert classes[("User", "models.py")] == {
        "name": "User",
        "file": "models.py",
        "module": "models",
        "bases": [{"name": "Base", "file": "models.py", "module": "models"}],
        "subclasses": [],
        "methods_count": 1,
        "attributes": ["email", "id"],
        "references": [
            {
                "file": "api.py",
                "module": "api",
                "symbol": "create_user",
                "kind": "call",
                "line": 7,
            },
            {
                "file": "api.py",
                "module": "api",
                "symbol": "create_user",
                "kind": "type_reference",
            },
            {
                "file": "repo.py",
                "module": "repo",
                "symbol": None,
                "kind": "import",
            },
        ],
    }
    assert classes[("Base", "models.py")]["subclasses"] == [
        {"name": "Admin", "file": "admin.py", "module": "admin"},
        {"name": "User", "file": "models.py", "module": "models"},
    ]
    assert classes[("Admin", "admin.py")]["bases"] == [
        {"name": "Base", "file": "models.py", "module": "models"}
    ]
    assert classes[("Admin", "admin.py")]["methods_count"] == 2


def test_function_summaries_include_call_links_and_flow_membership():
    inventory = {
        "api.py": {
            "classes": [
                {
                    "name": "Service",
                    "methods": [{"name": "prepare", "calls": [{"name": "helper"}]}],
                }
            ],
            "functions": [{"name": "run"}, {"name": "helper"}],
            "nested_functions": [{"name": "registered"}],
        }
    }
    call_edges = [
        {
            "from": {"file": "api.py", "symbol": "run"},
            "to": {"file": "api.py", "symbol": "helper"},
            "name": "helper",
            "kind": "internal",
            "line": 3,
        },
        {
            "from": {"file": "api.py", "symbol": "Service.prepare"},
            "to": {"file": "api.py", "symbol": "helper"},
            "name": "helper",
            "kind": "internal",
            "line": 8,
        },
    ]
    flows = [
        {
            "entry": {
                "id": "api-run",
                "category": "api",
                "file": "api.py",
                "symbol": "run",
                "label": "run",
            },
            "steps": [
                {"depth": 0, "file": "api.py", "symbol": "run", "kind": "entry"},
                {"depth": 1, "file": "api.py", "symbol": "helper", "kind": "internal"},
            ],
        }
    ]

    result = build_entity_relationship_summaries(
        inventory, call_edges=call_edges, flows=flows
    )
    functions = _by_symbol(result)

    assert functions[("run", "api.py")] == {
        "symbol": "run",
        "name": "run",
        "file": "api.py",
        "module": "api",
        "kind": "function",
        "owner_class": None,
        "callers": [],
        "callees": [
            {
                "file": "api.py",
                "module": "api",
                "symbol": "helper",
                "kind": "internal",
                "line": 3,
            }
        ],
        "entrypoints": [
            {
                "id": "api-run",
                "category": "api",
                "label": "run",
                "role": "entry",
                "depth": 0,
            }
        ],
    }
    assert functions[("helper", "api.py")]["callers"] == [
        {
            "file": "api.py",
            "module": "api",
            "symbol": "run",
            "kind": "internal",
            "line": 3,
        },
        {
            "file": "api.py",
            "module": "api",
            "symbol": "Service.prepare",
            "kind": "internal",
            "line": 8,
        },
    ]
    assert functions[("helper", "api.py")]["entrypoints"] == [
        {
            "id": "api-run",
            "category": "api",
            "label": "run",
            "role": "step",
            "depth": 1,
        }
    ]
    assert functions[("Service.prepare", "api.py")]["owner_class"] == "Service"
    assert functions[("registered", "api.py")]["kind"] == "nested_function"


def test_sparse_non_python_inventory_degrades_to_module_only_summaries():
    result = build_entity_relationship_summaries(
        {
            "web/widget.ts": {
                "language": "typescript",
                "classes": [{"name": "Widget"}],
                "functions": [{"name": "mount"}],
            }
        }
    )

    assert result == {
        "classes": [
            {
                "name": "Widget",
                "file": "web/widget.ts",
                "module": "widget",
                "bases": [],
                "subclasses": [],
                "methods_count": 0,
                "attributes": [],
                "references": [],
            }
        ],
        "functions": [
            {
                "symbol": "mount",
                "name": "mount",
                "file": "web/widget.ts",
                "module": "widget",
                "kind": "function",
                "owner_class": None,
                "callers": [],
                "callees": [],
                "entrypoints": [],
            }
        ],
    }


def test_relationship_summaries_are_deterministic_for_inventory_order():
    first = {
        "b.py": {"classes": [{"name": "B", "bases": ["A"]}], "functions": []},
        "a.py": {"classes": [{"name": "A", "bases": []}], "functions": []},
    }
    second = {
        "a.py": {"classes": [{"name": "A", "bases": []}], "functions": []},
        "b.py": {"classes": [{"name": "B", "bases": ["A"]}], "functions": []},
    }

    assert build_entity_relationship_summaries(
        first
    ) == build_entity_relationship_summaries(second)


def test_haskell_declaration_kind_survives_relationship_summaries():
    inventory = {
        "hls-analysis/src/HLSAnalysis/API.hs": {
            "language": "haskell",
            "module": "HLSAnalysis.API",
            "classes": [{"name": "User", "kind": "data", "line": 7}],
            "functions": [],
            "imports": [],
        }
    }

    result = build_entity_relationship_summaries(inventory)
    classes = _by_class(result)

    assert classes[("User", "hls-analysis/src/HLSAnalysis/API.hs")]["kind"] == "data"


def test_detailed_relationship_summaries_report_exact_totals_and_omissions():
    functions = [{"name": "run"}, *[{"name": f"helper_{i}"} for i in range(14)]]
    inventory = {
        "api.py": {
            "classes": [],
            "functions": functions,
        }
    }
    call_edges = [
        {
            "from": {"file": "api.py", "symbol": "run"},
            "to": {"file": "api.py", "symbol": f"helper_{i}"},
            "name": f"helper_{i}",
            "kind": "internal",
        }
        for i in range(14)
    ]
    legacy = build_entity_relationship_summaries(
        inventory, call_edges=call_edges
    )

    detailed = build_detailed_entity_relationship_summaries(
        inventory, call_edges=call_edges
    )
    opt_in = build_entity_relationship_summaries(
        inventory, call_edges=call_edges, detailed=True
    )

    assert detailed == opt_in
    assert build_entity_relationship_summaries(
        inventory, call_edges=call_edges
    ) == legacy
    assert set(legacy) == {"classes", "functions"}
    assert all("coverage" not in summary for summary in legacy["functions"])
    legacy_run = _by_symbol(legacy)[("run", "api.py")]
    assert len(legacy_run["callees"]) == 12
    assert legacy_run["callees"][0]["line"] == 0

    assert detailed["schema_version"] == "llm-wiki-relationship-summaries/v1"
    detailed_run = _by_symbol(detailed)[("run", "api.py")]
    assert len(detailed_run["callees"]) == 12
    assert detailed_run["callees"][0]["line"] is None
    assert detailed_run["coverage"]["callees"] == {
        "observed": 14,
        "emitted": 12,
        "limit": 12,
        "truncated": True,
        "omitted": 2,
        "limitations": ["presentation-summary-limit"],
    }
    assert detailed["coverage"] == {
        "classes": {
            "observed": 0,
            "emitted": 0,
            "limit": None,
            "truncated": False,
            "omitted": 0,
            "limitations": [],
        },
        "functions": {
            "observed": 15,
            "emitted": 15,
            "limit": None,
            "truncated": False,
            "omitted": 0,
            "limitations": [],
        },
        "relationships": {
            "observed": 28,
            "emitted": 26,
            "limit": None,
            "truncated": True,
            "omitted": 2,
            "limitations": [
                "limit-applies-per-summary-relationship-collection"
            ],
        },
    }


def test_detailed_relationship_summaries_are_deterministic_for_shuffled_inputs():
    functions = [{"name": "run"}, {"name": "alpha"}, {"name": "beta"}]
    inventory = {"api.py": {"classes": [], "functions": functions}}
    edges = [
        {
            "from": {"file": "api.py", "symbol": "run"},
            "to": {"file": "api.py", "symbol": "beta"},
            "name": "beta",
            "kind": "internal",
            "line": 4,
        },
        {
            "from": {"file": "api.py", "symbol": "run"},
            "to": {"file": "api.py", "symbol": "alpha"},
            "name": "alpha",
            "kind": "internal",
            "line": 3,
        },
    ]
    shuffled_inventory = {
        "api.py": {"classes": [], "functions": list(reversed(functions))}
    }

    first = build_detailed_entity_relationship_summaries(inventory, edges)
    second = build_detailed_entity_relationship_summaries(
        shuffled_inventory, list(reversed(edges))
    )

    assert first == second
