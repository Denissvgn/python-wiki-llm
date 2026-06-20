"""Tests for services/module_maps.py."""

from __future__ import annotations

from llm_wiki_cli.services.module_maps import build_module_dependency_maps


def _analysis(nodes, edges, *, cycles=None, reconciliation=None):
    return {
        "graph": {"nodes": list(nodes), "edges": list(edges), "unresolved": []},
        "cycles": list(cycles or []),
        "reconciliation": reconciliation or {"languages": {}},
    }


def test_module_maps_include_acyclic_inbound_and_outbound_neighbors():
    analysis = _analysis(
        ["api.py", "service.py", "repo.py"],
        [("api.py", "service.py"), ("service.py", "repo.py")],
    )

    result = build_module_dependency_maps(analysis)

    assert result["service.py"] == {
        "file": "service.py",
        "detail": "module",
        "inbound": ["api.py"],
        "outbound": ["repo.py"],
        "nodes": ["api.py", "repo.py", "service.py"],
        "edges": [("api.py", "service.py"), ("service.py", "repo.py")],
        "cycle_participation": False,
        "cycle_edges": [],
        "external": {},
        "overflow": {
            "node_limit": 12,
            "total_neighbor_count": 2,
            "omitted_count": 0,
        },
    }
    assert result["api.py"]["inbound"] == []
    assert result["api.py"]["outbound"] == ["service.py"]


def test_module_maps_highlight_local_cycle_participation():
    analysis = _analysis(
        ["api.py", "models.py", "settings.py"],
        [
            ("api.py", "models.py"),
            ("models.py", "api.py"),
            ("settings.py", "api.py"),
        ],
        cycles=[["api.py", "models.py"]],
    )

    result = build_module_dependency_maps(analysis)

    assert result["api.py"]["cycle_participation"] is True
    assert result["api.py"]["cycle_edges"] == [
        ("api.py", "models.py"),
        ("models.py", "api.py"),
    ]
    assert result["settings.py"]["cycle_participation"] is False
    assert result["settings.py"]["cycle_edges"] == []


def test_module_maps_summarize_external_package_counts_per_module():
    reconciliation = {
        "languages": {
            "python": {
                "used": {
                    "requests": ["api.py", "service.py"],
                    "yaml": ["service.py"],
                },
                "required": ["requests"],
                "optional": [],
                "undeclared": ["yaml"],
                "unused": [],
            }
        }
    }
    analysis = _analysis(
        ["api.py", "service.py"],
        [("api.py", "service.py")],
        reconciliation=reconciliation,
    )

    result = build_module_dependency_maps(analysis)

    assert result["service.py"]["external"] == {
        "python": {"used_count": 2, "undeclared_count": 1}
    }
    assert result["api.py"]["external"] == {
        "python": {"used_count": 1, "undeclared_count": 0}
    }
    assert "requests" not in str(result["service.py"]["external"])
    assert "yaml" not in str(result["service.py"]["external"])


def test_module_maps_collapse_large_neighborhoods_to_packages_with_overflow():
    analysis = _analysis(
        [
            "pkg/service.py",
            "adapters/http.py",
            "adapters/db.py",
            "storage/repo.py",
            "storage/cache.py",
            "storage/sql.py",
        ],
        [
            ("adapters/http.py", "pkg/service.py"),
            ("adapters/db.py", "pkg/service.py"),
            ("pkg/service.py", "storage/repo.py"),
            ("pkg/service.py", "storage/cache.py"),
            ("pkg/service.py", "storage/sql.py"),
        ],
    )

    result = build_module_dependency_maps(analysis, node_limit=4)

    assert result["pkg/service.py"] == {
        "file": "pkg/service.py",
        "detail": "package",
        "inbound": [{"package": "adapters", "count": 2}],
        "outbound": [{"package": "storage", "count": 3}],
        "nodes": ["adapters", "pkg/service.py", "storage"],
        "edges": [
            ("adapters", "pkg/service.py"),
            ("pkg/service.py", "storage"),
        ],
        "cycle_participation": False,
        "cycle_edges": [],
        "external": {},
        "overflow": {
            "node_limit": 4,
            "total_neighbor_count": 5,
            "omitted_count": 2,
        },
    }


def test_module_maps_are_deterministic_for_graph_order():
    forward = _analysis(
        ["pkg/service.py", "adapters/http.py", "storage/repo.py"],
        [
            ("adapters/http.py", "pkg/service.py"),
            ("pkg/service.py", "storage/repo.py"),
        ],
    )
    reverse = _analysis(
        ["storage/repo.py", "adapters/http.py", "pkg/service.py"],
        [
            ("pkg/service.py", "storage/repo.py"),
            ("adapters/http.py", "pkg/service.py"),
        ],
    )

    assert build_module_dependency_maps(forward) == build_module_dependency_maps(
        reverse
    )
