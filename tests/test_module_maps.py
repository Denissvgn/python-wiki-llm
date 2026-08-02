"""Tests for services/module_maps.py."""

from __future__ import annotations

from llm_wiki_cli.services.dependencies import analyze_dependencies
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


def test_module_maps_use_file_specific_undeclared_details():
    reconciliation = {
        "languages": {
            "python": {
                "used": {
                    "assistant-shared": ["api.py", "service.py"],
                    "grpcio": ["service.py"],
                },
                "required": ["assistant-shared", "grpcio"],
                "optional": [],
                "undeclared": ["assistant-shared"],
                "undeclared_details": [
                    {
                        "package": "assistant-shared",
                        "files": ["api.py"],
                        "scope": None,
                    }
                ],
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

    assert result["api.py"]["external"] == {
        "python": {"used_count": 1, "undeclared_count": 1}
    }
    assert result["service.py"]["external"] == {
        "python": {"used_count": 2, "undeclared_count": 0}
    }


def test_module_maps_include_haskell_declared_module_neighbors(tmp_path):
    inventory = {
        "hls-analysis/app/Main.hs": {
            "language": "haskell",
            "module": "Main",
            "imports": [{"module": "HLSAnalysis.API", "name": ""}],
            "classes": [],
            "functions": [],
        },
        "hls-analysis/src/HLSAnalysis/API.hs": {
            "language": "haskell",
            "module": "HLSAnalysis.API",
            "imports": [],
            "classes": [],
            "functions": [],
        },
    }

    result = build_module_dependency_maps(
        analyze_dependencies(inventory, str(tmp_path))
    )

    assert result["hls-analysis/app/Main.hs"]["outbound"] == [
        "hls-analysis/src/HLSAnalysis/API.hs"
    ]
    assert result["hls-analysis/src/HLSAnalysis/API.hs"]["inbound"] == [
        "hls-analysis/app/Main.hs"
    ]


def test_module_maps_keep_python_external_imports_out_of_go_neighbors(tmp_path):
    (tmp_path / "rlm").mkdir()
    (tmp_path / "rlm" / "requirements.txt").write_text(
        "anthropic\nopenai\n",
        encoding="utf-8",
    )
    inventory = {
        "rlm/gateway.py": {
            "language": "python",
            "imports": [
                {"module": "anthropic", "name": "anthropic"},
                {"module": "openai", "name": "openai"},
            ],
            "classes": [],
            "functions": [],
        },
        "internal/llm/anthropic.go": {
            "language": "go",
            "imports": [],
            "classes": [],
            "functions": [],
        },
        "internal/llm/openai.go": {
            "language": "go",
            "imports": [],
            "classes": [],
            "functions": [],
        },
    }

    result = build_module_dependency_maps(
        analyze_dependencies(inventory, str(tmp_path))
    )

    assert result["rlm/gateway.py"]["outbound"] == []
    assert result["rlm/gateway.py"]["external"] == {
        "python": {"used_count": 2, "undeclared_count": 0}
    }


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


def test_module_maps_preserve_dense_local_edges_for_rendering():
    module = "pkg/focal.py"
    neighbors = [f"pkg/n{index:02d}.py" for index in range(11)]
    direct_edges = [
        *((neighbor, module) for neighbor in neighbors[:6]),
        *((module, neighbor) for neighbor in neighbors[6:]),
    ]
    contextual_edges = [
        (source, target)
        for source_index, source in enumerate(neighbors)
        for target in neighbors[source_index + 1 :]
    ][:49]

    result = build_module_dependency_maps(
        _analysis([module, *neighbors], [*direct_edges, *contextual_edges])
    )
    summary = result[module]

    assert summary["detail"] == "module"
    assert len(summary["nodes"]) == 12
    assert len(summary["edges"]) == 60
    assert set(direct_edges).issubset(set(summary["edges"]))
    assert summary["overflow"] == {
        "node_limit": 12,
        "total_neighbor_count": 11,
        "omitted_count": 0,
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
