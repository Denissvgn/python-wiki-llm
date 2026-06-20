"""Tests for services/relationships.py."""

from __future__ import annotations

from llm_wiki_cli.services.relationships import build_entity_relationship_summaries


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
