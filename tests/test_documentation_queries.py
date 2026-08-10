"""Tests for pure documentation graph query services."""

from __future__ import annotations

import json

import pytest

from llm_wiki_cli.services.documentation_queries import (
    DocumentationGraphQueryService,
    DocumentationQueryError,
    QUERY_FILTER_VALUE_LIMIT,
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


class _CountingValues:
    def __init__(self, value: str, *, fail: bool = False):
        self.value = value
        self.fail = fail
        self.pulled = 0

    def __iter__(self):
        return self

    def __next__(self):
        self.pulled += 1
        if self.fail:
            raise RuntimeError("iterator failed")
        return self.value


@pytest.mark.parametrize(
    ("field", "invoke"),
    [
        (
            "kinds",
            lambda service, values: service.related_concepts(
                "llm-wiki://entities/User",
                kinds=values,
            ),
        ),
        (
            "kinds",
            lambda service, values: service.traverse_typed_graph(
                "llm-wiki://entities/User",
                kinds=values,
            ),
        ),
        (
            "origins",
            lambda service, values: service.traverse_typed_graph(
                "llm-wiki://entities/User",
                origins=values,
            ),
        ),
    ],
)
def test_query_filter_iterables_are_bounded_and_fail_closed(field, invoke):
    service = DocumentationGraphQueryService({})
    value = "links_to" if field == "kinds" else "extracted"
    oversized = _CountingValues(value)

    with pytest.raises(
        DocumentationQueryError,
        match=f"{field} must contain at most {QUERY_FILTER_VALUE_LIMIT}",
    ):
        invoke(service, oversized)
    assert oversized.pulled == QUERY_FILTER_VALUE_LIMIT + 1

    broken = _CountingValues(value, fail=True)
    with pytest.raises(DocumentationQueryError, match=f"{field} must be an iterable"):
        invoke(service, broken)
    assert broken.pulled == 1


def _assert_bounds(result, expected):
    assert set(result["bounds"]) == set(expected)
    for path, collection in expected.items():
        bound = result["bounds"][path]
        assert bound["returned"] == len(collection)
        assert bound["truncated"] is (bound["total"] > bound["returned"])
    assert result["truncated"] is any(
        bound["truncated"] for bound in result["bounds"].values()
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
    _assert_bounds(
        flow,
        {
            "matches": flow["matches"],
            "flow.steps": flow["flow"]["steps"],
        },
    )

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
    _assert_bounds(
        callers,
        {"matches": callers["matches"], "callers": callers["callers"]},
    )
    callees = service.callees("run")
    assert callees["callees"] == [
        {
            "file": "repo.py",
            "module": "repo",
            "symbol": "save",
            "kind": "internal",
            "line": 3,
        }
    ]
    _assert_bounds(
        callees,
        {"matches": callees["matches"], "callees": callees["callees"]},
    )

    data_flow = service.data_flow_for_entrypoint("run")
    assert data_flow["found"] is True
    assert data_flow["data_flow"]["id"] == "api-run"
    assert data_flow["data_flow"]["transfers"][0]["call"] == "save(payload)"
    _assert_bounds(
        data_flow,
        {
            "matches": data_flow["matches"],
            "data_flow.steps": data_flow["data_flow"]["steps"],
            "data_flow.transfers": data_flow["data_flow"]["transfers"],
            "data_flow.boundaries": data_flow["data_flow"]["boundaries"],
            "data_flow.gaps": data_flow["data_flow"]["gaps"],
        },
    )

    pages = service.pages_for_symbol("run")
    assert pages["found"] is True
    assert [page["canonical_path"] for page in pages["pages"]] == [
        "flows/api-run.md",
        "modules/api.md",
    ]
    _assert_bounds(
        pages,
        {"matches": pages["matches"], "pages": pages["pages"]},
    )

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
        "bounds": {
            "matches": {"total": 0, "returned": 0, "truncated": False},
            "callers": {"total": 0, "returned": 0, "truncated": False},
        },
        "callable": None,
        "callers": [],
    }
    assert service.flow_for_entrypoint("missing")["flow"] is None
    assert service.data_flow_for_entrypoint("missing")["data_flow"] is None
    assert service.pages_for_symbol("missing")["pages"] == []


def test_missing_graph_identifiers_are_never_indexed_as_none_strings():
    service = DocumentationGraphQueryService(
        {
            "broken.py": {
                "imports": [],
                "classes": [{"name": None}],
                "functions": [{"name": None}],
            }
        },
        flows=[{"entry": {}, "steps": []}],
        data_flows=[{"entry": {}, "steps": [], "transfers": []}],
    )

    assert service.callers("None")["found"] is False
    assert service.callees("None")["found"] is False
    assert service.flow_for_entrypoint("None")["found"] is False
    assert service.data_flow_for_entrypoint("None")["found"] is False


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
    _assert_bounds(
        result,
        {"matches": result["matches"], "callees": result["callees"]},
    )


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
    _assert_bounds(
        result,
        {
            "matches": result["matches"],
            "inbound": result["inbound"],
            "outbound": result["outbound"],
            "cycle_groups": result["cycle_groups"],
            "pages": result["pages"],
        },
    )


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
    assert result["bounds"]["callers"] == {
        "total": 3,
        "returned": 2,
        "truncated": True,
    }


def test_default_limit_reports_raw_caller_truncation_past_relationship_page_cap():
    inventory = {
        f"caller_{idx}.py": {
            "classes": [],
            "functions": [{"name": f"caller_{idx}"}],
            "imports": [],
        }
        for idx in range(25)
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
        for idx in range(25)
    ]
    service = DocumentationGraphQueryService(inventory, call_edges=edges)

    result = service.callers("target")

    assert result["truncated"] is True
    assert len(result["callers"]) == 20
    assert [caller["symbol"] for caller in result["callers"]] == sorted(
        f"caller_{idx}" for idx in range(25)
    )[:20]
    assert result["bounds"]["callers"] == {
        "total": 25,
        "returned": 20,
        "truncated": True,
    }


def test_every_query_collection_discloses_exact_zero_equal_and_over_limit_bounds():
    bounded = _service(limit=1)

    flow = bounded.flow_for_entrypoint("api-run")
    assert flow["bounds"]["flow.steps"] == {
        "total": 2,
        "returned": 1,
        "truncated": True,
    }

    dependency = bounded.dependency_neighborhood("api.py")
    _assert_bounds(
        dependency,
        {
            "matches": dependency["matches"],
            "inbound": dependency["inbound"],
            "outbound": dependency["outbound"],
            "cycle_groups": dependency["cycle_groups"],
            "pages": dependency["pages"],
        },
    )
    assert dependency["bounds"]["inbound"] == {
        "total": 0,
        "returned": 0,
        "truncated": False,
    }
    assert dependency["bounds"]["matches"] == {
        "total": 1,
        "returned": 1,
        "truncated": False,
    }
    assert dependency["bounds"]["outbound"] == {
        "total": 2,
        "returned": 1,
        "truncated": True,
    }
    assert dependency["bounds"]["pages"] == {
        "total": 2,
        "returned": 1,
        "truncated": True,
    }

    data_flow = bounded.data_flow_for_entrypoint("api-run")
    _assert_bounds(
        data_flow,
        {
            "matches": data_flow["matches"],
            "data_flow.steps": data_flow["data_flow"]["steps"],
            "data_flow.transfers": data_flow["data_flow"]["transfers"],
            "data_flow.boundaries": data_flow["data_flow"]["boundaries"],
            "data_flow.gaps": data_flow["data_flow"]["gaps"],
        },
    )

    pages = bounded.pages_for_symbol("run")
    assert pages["bounds"]["pages"] == {
        "total": 2,
        "returned": 1,
        "truncated": True,
    }

    missing = bounded.dependency_neighborhood("missing.py")
    _assert_bounds(
        missing,
        {
            "matches": missing["matches"],
            "inbound": missing["inbound"],
            "outbound": missing["outbound"],
            "cycle_groups": missing["cycle_groups"],
            "pages": missing["pages"],
        },
    )


def test_ambiguous_matches_report_exact_bounds_before_empty_payload_bounds():
    inventory = {
        "api.py": {"classes": [], "functions": [{"name": "run"}], "imports": []},
        "jobs.py": {"classes": [], "functions": [{"name": "run"}], "imports": []},
    }
    result = DocumentationGraphQueryService(inventory, limit=1).callees("run")

    assert result["ambiguous"] is True
    assert result["bounds"] == {
        "matches": {"total": 2, "returned": 1, "truncated": True},
        "callees": {"total": 0, "returned": 0, "truncated": False},
    }
    assert result["truncated"] is True


def test_upstream_analyzer_truncation_is_distinct_from_response_bounds():
    flow = _flow()
    flow["truncated"] = True
    result = DocumentationGraphQueryService(
        _inventory(),
        flows=[flow],
    ).flow_for_entrypoint("api-run")

    assert result["flow"]["truncated"] is True
    assert result["bounds"] == {
        "matches": {"total": 1, "returned": 1, "truncated": False},
        "flow.steps": {"total": 2, "returned": 2, "truncated": False},
    }
    assert result["truncated"] is False


def test_query_methods_use_indexes_built_during_service_construction():
    service = _service()

    class NoIterationList(list):
        def __iter__(self):
            raise AssertionError("query attempted to rescan constructor input")

    service.callables = NoIterationList(service.callables)
    service.classes = NoIterationList(service.classes)
    service.flows = NoIterationList(service.flows)
    service.data_flows = NoIterationList(service.data_flows)
    service.pages = NoIterationList(service.pages)
    service.dependency["graph"]["edges"] = NoIterationList(
        service.dependency["graph"]["edges"]
    )
    service.dependency["cycles"] = NoIterationList(service.dependency["cycles"])
    service.dependency["load_order"]["order"] = NoIterationList(
        service.dependency["load_order"]["order"]
    )

    assert service.flow_for_entrypoint("api-run")["found"] is True
    assert service.callers("save")["found"] is True
    assert service.callers("repo.py:save")["found"] is True
    assert service.callees("run")["found"] is True
    assert service.data_flow_for_entrypoint("run")["found"] is True
    assert service.pages_for_symbol("run")["found"] is True
    assert service.dependency_neighborhood("api.py")["found"] is True


@pytest.mark.parametrize("query", ["", "   ", None, 3])
def test_empty_or_non_string_symbol_query_is_invalid(query):
    with pytest.raises(DocumentationQueryError):
        _service().callers(query)  # type: ignore[arg-type]


@pytest.mark.parametrize("path", ["/tmp/api.py", "../api.py", "C:/tmp/api.py", ""])
def test_invalid_dependency_path_query_is_rejected(path):
    with pytest.raises(DocumentationQueryError):
        _service().dependency_neighborhood(path)
