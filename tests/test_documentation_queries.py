"""Tests for pure documentation graph query services."""

from __future__ import annotations

import json

import pytest

from llm_wiki_cli.services.documentation_queries import (
    DocumentationGraphQueryService,
    DocumentationQueryError,
)


def _inventory() -> dict:
    return {
        "api.py": {
            "language": "python",
            "imports": [
                {"module": "repo", "name": "save"},
                {"module": "models", "name": "User"},
            ],
            "classes": [],
            "functions": [
                {
                    "name": "run",
                    "params": [{"name": "payload", "type": "User"}],
                    "return_type": "User",
                    "decorators": [],
                    "data_effects": {
                        "inputs": [{"name": "payload", "kind": "param", "line": 1}],
                        "reads": [],
                        "writes": [],
                        "returns": [{"value": "User", "line": 3}],
                        "boundary_effects": [],
                    },
                }
            ],
        },
        "repo.py": {
            "language": "python",
            "imports": [],
            "classes": [],
            "functions": [{"name": "save", "params": [], "return_type": "User"}],
        },
        "models.py": {
            "language": "python",
            "imports": [],
            "classes": [{"name": "User", "methods": [], "attributes": []}],
            "functions": [],
        },
    }


def _call_edges() -> list[dict]:
    return [
        {
            "from": {"file": "api.py", "symbol": "run"},
            "to": {"file": "repo.py", "symbol": "save"},
            "name": "save",
            "kind": "internal",
            "line": 3,
        }
    ]


def _flow() -> dict:
    return {
        "entry": {
            "id": "api-run",
            "category": "api",
            "file": "api.py",
            "symbol": "run",
            "label": "run",
        },
        "steps": [
            {"depth": 0, "file": "api.py", "symbol": "run", "kind": "entry"},
            {
                "depth": 1,
                "file": "repo.py",
                "symbol": "save",
                "kind": "internal",
                "edge": _call_edges()[0],
            },
        ],
        "modules_touched": ["api.py", "repo.py"],
        "truncated": False,
    }


def _data_flow() -> dict:
    return {
        "id": "api-run",
        "entry": _flow()["entry"],
        "steps": [
            {
                "index": 1,
                "depth": 0,
                "file": "api.py",
                "symbol": "run",
                "kind": "entry",
                "inputs": [{"name": "payload", "kind": "param", "line": 1}],
                "reads": [],
                "writes": [],
                "returns": [{"value": "User", "line": 3}],
                "boundary_effects": [],
            }
        ],
        "transfers": [
            {
                "from": "run",
                "to": "save",
                "from_step": 1,
                "to_step": 2,
                "line": 3,
                "call": "save(payload)",
                "arguments": ["payload"],
                "kind": "internal",
            }
        ],
        "boundaries": [],
        "gaps": [],
        "truncated": False,
    }


def _surface_index() -> dict:
    return {
        "pages": [
            {
                "kind": "index",
                "id": "index",
                "title": "LLM Wiki Index",
                "canonical_path": "index.md",
                "source_path": None,
                "role": "mixed",
                "mcp_uri": "llm-wiki://index",
                "outgoing_internal_links": ["modules/api.md"],
            },
            {
                "kind": "modules",
                "id": "api",
                "title": "api Module",
                "canonical_path": "modules/api.md",
                "source_path": "api.py",
                "role": "semantic",
                "mcp_uri": "llm-wiki://modules/api",
                "outgoing_internal_links": ["flows/api-run.md"],
            },
            {
                "kind": "flows",
                "id": "api-run",
                "title": "api-run",
                "canonical_path": "flows/api-run.md",
                "source_path": "api.py",
                "role": "mixed",
                "mcp_uri": "llm-wiki://flows/api-run",
                "outgoing_internal_links": ["modules/api.md"],
            },
            {
                "kind": "entities",
                "id": "User",
                "title": "User",
                "canonical_path": "entities/User.md",
                "source_path": "models.py",
                "role": "semantic",
                "mcp_uri": "llm-wiki://entities/User",
                "outgoing_internal_links": [],
            },
            {
                "kind": "dependencies",
                "id": "dependencies",
                "title": "Dependencies",
                "canonical_path": "dependencies.md",
                "source_path": None,
                "role": "mixed",
                "mcp_uri": "llm-wiki://dependencies",
                "outgoing_internal_links": ["modules/api.md"],
            },
        ],
        "flows": [
            {
                "id": "api-run",
                "category": "api",
                "entry_point": {
                    "symbol": "run",
                    "source_path": "api.py",
                    "label": "run",
                },
            }
        ],
    }


def _service(**kwargs) -> DocumentationGraphQueryService:
    return DocumentationGraphQueryService(
        _inventory(),
        call_edges=_call_edges(),
        flows=[_flow()],
        data_flows=[_data_flow()],
        surface_index=_surface_index(),
        **kwargs,
    )


def test_flow_call_data_flow_and_page_queries_are_deterministic_json():
    service = _service()

    flow = service.flow_for_entrypoint("api-run")
    assert flow["found"] is True
    assert flow["ambiguous"] is False
    assert flow["matches"] == [
        {
            "id": "api-run",
            "category": "api",
            "file": "api.py",
            "symbol": "run",
            "label": "run",
        }
    ]
    assert flow["flow"]["modules_touched"] == ["api.py", "repo.py"]

    callers = service.callers("save")
    assert callers["callable"] == {
        "symbol": "save",
        "name": "save",
        "file": "repo.py",
        "module": "repo",
        "kind": "function",
        "owner_class": None,
    }
    assert callers["callers"] == [
        {
            "file": "api.py",
            "module": "api",
            "symbol": "run",
            "kind": "internal",
            "line": 3,
        }
    ]
    assert service.callees("run")["callees"] == [
        {
            "file": "repo.py",
            "module": "repo",
            "symbol": "save",
            "kind": "internal",
            "line": 3,
        }
    ]

    data_flow = service.data_flow_for_entrypoint("run")
    assert data_flow["found"] is True
    assert data_flow["data_flow"]["id"] == "api-run"
    assert data_flow["data_flow"]["transfers"][0]["call"] == "save(payload)"

    pages = service.pages_for_symbol("run")
    assert pages["found"] is True
    assert [page["canonical_path"] for page in pages["pages"]] == [
        "flows/api-run.md",
        "modules/api.md",
    ]

    json.dumps(
        {
            "flow": flow,
            "callers": callers,
            "data_flow": data_flow,
            "pages": pages,
        },
        sort_keys=True,
    )


def test_unknown_symbol_returns_structured_empty_result():
    service = _service()

    assert service.callers("missing") == {
        "query": "missing",
        "found": False,
        "ambiguous": False,
        "matches": [],
        "truncated": False,
        "callable": None,
        "callers": [],
    }
    assert service.flow_for_entrypoint("missing")["flow"] is None
    assert service.data_flow_for_entrypoint("missing")["data_flow"] is None
    assert service.pages_for_symbol("missing")["pages"] == []


def test_ambiguous_symbol_returns_matches_without_selected_payload():
    inventory = {
        "api.py": {"classes": [], "functions": [{"name": "run"}], "imports": []},
        "jobs.py": {"classes": [], "functions": [{"name": "run"}], "imports": []},
    }
    service = DocumentationGraphQueryService(inventory)

    result = service.callees("run")

    assert result["found"] is False
    assert result["ambiguous"] is True
    assert result["callable"] is None
    assert result["callees"] == []
    assert result["matches"] == [
        {
            "symbol": "run",
            "name": "run",
            "file": "api.py",
            "module": "api",
            "kind": "function",
            "owner_class": None,
        },
        {
            "symbol": "run",
            "name": "run",
            "file": "jobs.py",
            "module": "jobs",
            "kind": "function",
            "owner_class": None,
        },
    ]


def test_dependency_neighborhood_includes_neighbors_metrics_and_pages():
    result = _service().dependency_neighborhood("api.py")

    assert result["found"] is True
    assert result["path"] == "api.py"
    assert result["inbound"] == []
    assert result["outbound"] == ["models.py", "repo.py"]
    assert result["metrics"] == {"fan_in": 0, "fan_out": 2}
    assert result["cycle_groups"] == []
    assert result["load_order_index"] >= 0
    assert [page["canonical_path"] for page in result["pages"]] == [
        "flows/api-run.md",
        "modules/api.md",
    ]


def test_bounded_output_sets_truncated_flag():
    inventory = {
        f"caller_{idx}.py": {
            "classes": [],
            "functions": [{"name": f"caller_{idx}"}],
            "imports": [],
        }
        for idx in range(3)
    }
    inventory["target.py"] = {
        "classes": [],
        "functions": [{"name": "target"}],
        "imports": [],
    }
    edges = [
        {
            "from": {"file": f"caller_{idx}.py", "symbol": f"caller_{idx}"},
            "to": {"file": "target.py", "symbol": "target"},
            "name": "target",
            "kind": "internal",
            "line": idx + 1,
        }
        for idx in range(3)
    ]
    service = DocumentationGraphQueryService(inventory, call_edges=edges, limit=2)

    result = service.callers("target")

    assert result["truncated"] is True
    assert [caller["symbol"] for caller in result["callers"]] == [
        "caller_0",
        "caller_1",
    ]


@pytest.mark.parametrize("query", ["", "   ", None, 3])
def test_empty_or_non_string_symbol_query_is_invalid(query):
    with pytest.raises(DocumentationQueryError):
        _service().callers(query)  # type: ignore[arg-type]


@pytest.mark.parametrize("path", ["/tmp/api.py", "../api.py", "C:/tmp/api.py", ""])
def test_invalid_dependency_path_query_is_rejected(path):
    with pytest.raises(DocumentationQueryError):
        _service().dependency_neighborhood(path)
