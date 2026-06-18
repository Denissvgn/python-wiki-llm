"""Tests for services/dependencies.py — internal dependency graph (Epic 2.1)."""
from __future__ import annotations

from llm_wiki_cli.services.dependencies import (
    build_dependency_graph,
    dependency_metrics,
    detect_cycles,
)


def _imp(module, name=None):
    """A minimal import record as the extractors emit them."""
    return {"module": module, "name": name if name is not None else module}


def _mod(*imports):
    return {"imports": list(imports)}


# ── DL-101: build_dependency_graph ────────────────────────────────────


class TestBuildDependencyGraph:
    def test_straight_chain(self):
        inventory = {
            "a.py": _mod(_imp("b")),
            "b.py": _mod(_imp("c")),
            "c.py": _mod(),
        }
        graph = build_dependency_graph(inventory)
        assert graph["edges"] == [("a.py", "b.py"), ("b.py", "c.py")]
        assert graph["nodes"] == ["a.py", "b.py", "c.py"]
        assert graph["unresolved"] == []

    def test_diamond(self):
        inventory = {
            "a.py": _mod(_imp("b"), _imp("c")),
            "b.py": _mod(_imp("d")),
            "c.py": _mod(_imp("d")),
            "d.py": _mod(),
        }
        graph = build_dependency_graph(inventory)
        assert graph["edges"] == [
            ("a.py", "b.py"),
            ("a.py", "c.py"),
            ("b.py", "d.py"),
            ("c.py", "d.py"),
        ]

    def test_isolated_node_with_no_internal_imports(self):
        inventory = {
            "a.py": _mod(_imp("b")),
            "b.py": _mod(),
            "lonely.py": _mod(),
        }
        graph = build_dependency_graph(inventory)
        assert "lonely.py" in graph["nodes"]
        assert all("lonely.py" not in edge for edge in graph["edges"])

    def test_relative_imports_resolve_internally(self):
        inventory = {
            "pkg/a.py": _mod(_imp(".b", "thing"), _imp("..top", "Top")),
            "pkg/b.py": _mod(),
            "top.py": _mod(),
        }
        graph = build_dependency_graph(inventory)
        assert ("pkg/a.py", "pkg/b.py") in graph["edges"]
        assert ("pkg/a.py", "top.py") in graph["edges"]
        assert graph["unresolved"] == []

    def test_from_dot_import_submodule_resolves(self):
        # ``from . import b`` carries the target in the imported name.
        inventory = {
            "pkg/a.py": _mod(_imp(".", "b")),
            "pkg/b.py": _mod(),
        }
        graph = build_dependency_graph(inventory)
        assert graph["edges"] == [("pkg/a.py", "pkg/b.py")]

    def test_stdlib_and_third_party_land_in_unresolved(self):
        inventory = {
            "a.py": _mod(_imp("os"), _imp("requests.adapters", "HTTPAdapter")),
        }
        graph = build_dependency_graph(inventory)
        assert graph["edges"] == []
        assert graph["unresolved"] == [
            {"file": "a.py", "module": "os", "name": "os"},
            {"file": "a.py", "module": "requests.adapters", "name": "HTTPAdapter"},
        ]

    def test_self_import_is_neither_edge_nor_unresolved(self):
        inventory = {"a.py": _mod(_imp("a"))}
        graph = build_dependency_graph(inventory)
        assert graph["edges"] == []
        assert graph["unresolved"] == []
        assert graph["nodes"] == ["a.py"]

    def test_ambiguous_module_narrowed_by_symbol(self):
        # Two ``settings`` modules; the imported symbol disambiguates the target.
        inventory = {
            "app.py": _mod(_imp("settings", "DEBUG")),
            "pkg/a/settings.py": {"imports": [], "functions": [{"name": "DEBUG"}]},
            "pkg/b/settings.py": {"imports": [], "functions": []},
        }
        graph = build_dependency_graph(inventory)
        assert graph["edges"] == [("app.py", "pkg/a/settings.py")]

    def test_duplicate_imports_collapse_to_one_edge(self):
        inventory = {
            "a.py": _mod(_imp("b"), _imp("b", "other")),
            "b.py": _mod(),
        }
        assert build_dependency_graph(inventory)["edges"] == [("a.py", "b.py")]

    def test_tolerates_slim_and_non_dict_entries(self):
        inventory = {
            "a.py": _mod(_imp("b")),
            "b.py": _mod(),
            "Dockerfile": {"language": "docker"},  # no "imports" key
            "weird": "not-a-dict",
        }
        graph = build_dependency_graph(inventory)
        assert graph["nodes"] == ["a.py", "b.py"]
        assert graph["edges"] == [("a.py", "b.py")]

    def test_missing_imports_field_never_raises(self):
        # Entirely empty entries must not raise and must not appear as nodes.
        assert build_dependency_graph({"a.py": {}}) == {
            "edges": [],
            "nodes": [],
            "unresolved": [],
        }

    def test_output_is_deterministic_regardless_of_input_order(self):
        forward = {
            "a.py": _mod(_imp("b")),
            "b.py": _mod(_imp("c")),
            "c.py": _mod(),
        }
        reverse = dict(reversed(list(forward.items())))
        assert build_dependency_graph(forward) == build_dependency_graph(reverse)


# ── DL-102: detect_cycles ─────────────────────────────────────────────


class TestDetectCycles:
    def test_acyclic_graph_has_no_cycles(self):
        graph = build_dependency_graph(
            {
                "a.py": _mod(_imp("b")),
                "b.py": _mod(_imp("c")),
                "c.py": _mod(),
            }
        )
        assert detect_cycles(graph) == []

    def test_three_module_cycle_is_one_scc(self):
        graph = build_dependency_graph(
            {
                "a.py": _mod(_imp("b")),
                "b.py": _mod(_imp("c")),
                "c.py": _mod(_imp("a")),
            }
        )
        assert detect_cycles(graph) == [["a.py", "b.py", "c.py"]]

    def test_two_independent_cycles_are_separate_and_ordered(self):
        graph = {
            "nodes": ["a.py", "b.py", "x.py", "y.py"],
            "edges": [
                ("x.py", "y.py"),
                ("y.py", "x.py"),
                ("a.py", "b.py"),
                ("b.py", "a.py"),
            ],
        }
        assert detect_cycles(graph) == [["a.py", "b.py"], ["x.py", "y.py"]]

    def test_acyclic_edges_outside_cycle_are_excluded(self):
        graph = {
            "nodes": ["a.py", "b.py", "c.py", "entry.py"],
            "edges": [
                ("entry.py", "a.py"),
                ("a.py", "b.py"),
                ("b.py", "c.py"),
                ("c.py", "a.py"),
            ],
        }
        assert detect_cycles(graph) == [["a.py", "b.py", "c.py"]]

    def test_explicit_self_loop_is_a_cycle(self):
        graph = {"nodes": ["a.py"], "edges": [("a.py", "a.py")]}
        assert detect_cycles(graph) == [["a.py"]]

    def test_deep_chain_does_not_exceed_recursion_limit(self):
        # Iterative SCC must handle a graph deeper than the recursion limit.
        depth = 4000
        edges = [(f"m{i}.py", f"m{i + 1}.py") for i in range(depth)]
        graph = {"nodes": [f"m{i}.py" for i in range(depth + 1)], "edges": edges}
        assert detect_cycles(graph) == []

    def test_empty_graph(self):
        assert detect_cycles({"nodes": [], "edges": []}) == []


# ── DL-103: dependency_metrics ────────────────────────────────────────


class TestDependencyMetrics:
    def test_counts_match_edge_list(self):
        graph = build_dependency_graph(
            {
                "a.py": _mod(_imp("b"), _imp("c")),
                "b.py": _mod(_imp("d")),
                "c.py": _mod(_imp("d")),
                "d.py": _mod(),
            }
        )
        metrics = dependency_metrics(graph)["metrics"]
        assert metrics["a.py"] == {"fan_in": 0, "fan_out": 2}
        assert metrics["b.py"] == {"fan_in": 1, "fan_out": 1}
        assert metrics["d.py"] == {"fan_in": 2, "fan_out": 0}

    def test_most_depended_on_ranks_by_fan_in_then_alphabetically(self):
        graph = {
            "nodes": ["a.py", "b.py", "hub.py", "z.py"],
            "edges": [
                ("a.py", "hub.py"),
                ("b.py", "hub.py"),
                ("z.py", "hub.py"),
                ("a.py", "b.py"),
            ],
        }
        result = dependency_metrics(graph)
        # hub (3) first; then b (1); then a and z (0) alphabetically.
        assert result["most_depended_on"] == ["hub.py", "b.py", "a.py", "z.py"]

    def test_every_node_appears_even_when_isolated(self):
        graph = {"nodes": ["solo.py"], "edges": []}
        result = dependency_metrics(graph)
        assert result["metrics"] == {"solo.py": {"fan_in": 0, "fan_out": 0}}
        assert result["most_depended_on"] == ["solo.py"]
