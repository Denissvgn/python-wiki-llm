"""Tests for services/dependencies.py — internal dependency graph (Epic 2.1)."""

from __future__ import annotations

from llm_wiki_cli.services.dependencies import (
    analyze_dependencies,
    build_dependency_graph,
    dependency_metrics,
    detect_cycles,
    detect_side_effects,
    package_dependency_graph,
    top_level_package,
    topological_order,
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


# ── DL-302: topological_order ─────────────────────────────────────────


class TestTopologicalOrder:
    def test_linear_chain_loads_dependencies_first(self):
        # a imports b imports c -> c must load before b before a.
        graph = build_dependency_graph(
            {
                "a.py": _mod(_imp("b")),
                "b.py": _mod(_imp("c")),
                "c.py": _mod(),
            }
        )
        result = topological_order(graph)
        assert result["order"] == ["c.py", "b.py", "a.py"]
        assert result["cycle_groups"] == []

    def test_diamond_places_dependency_before_dependents(self):
        graph = build_dependency_graph(
            {
                "a.py": _mod(_imp("b"), _imp("c")),
                "b.py": _mod(_imp("d")),
                "c.py": _mod(_imp("d")),
                "d.py": _mod(),
            }
        )
        order = topological_order(graph)["order"]
        # d before b and c; b and c before a.
        assert order.index("d.py") < order.index("b.py")
        assert order.index("d.py") < order.index("c.py")
        assert order.index("b.py") < order.index("a.py")
        assert order.index("c.py") < order.index("a.py")

    def test_cycle_group_is_surfaced_not_dropped(self):
        graph = build_dependency_graph(
            {
                "a.py": _mod(_imp("b")),
                "b.py": _mod(_imp("c")),
                "c.py": _mod(_imp("a")),
            }
        )
        result = topological_order(graph)
        assert result["cycle_groups"] == [["a.py", "b.py", "c.py"]]
        # The whole cycle still appears in the order (sorted, adjacent).
        assert result["order"] == ["a.py", "b.py", "c.py"]

    def test_cycle_condensed_then_dependent_follows(self):
        # entry imports a; a<->b<->c form a cycle. The cycle loads, then entry.
        graph = {
            "nodes": ["a.py", "b.py", "c.py", "entry.py"],
            "edges": [
                ("entry.py", "a.py"),
                ("a.py", "b.py"),
                ("b.py", "c.py"),
                ("c.py", "a.py"),
            ],
        }
        result = topological_order(graph)
        assert result["cycle_groups"] == [["a.py", "b.py", "c.py"]]
        assert result["order"] == ["a.py", "b.py", "c.py", "entry.py"]

    def test_isolated_module_still_appears(self):
        graph = build_dependency_graph(
            {
                "a.py": _mod(_imp("b")),
                "b.py": _mod(),
                "lonely.py": _mod(),
            }
        )
        order = topological_order(graph)["order"]
        assert set(order) == {"a.py", "b.py", "lonely.py"}
        assert order.index("b.py") < order.index("a.py")

    def test_alphabetical_tie_break_is_deterministic(self):
        graph = {"nodes": ["z.py", "a.py", "m.py"], "edges": []}
        assert topological_order(graph)["order"] == ["a.py", "m.py", "z.py"]

    def test_output_is_deterministic_regardless_of_input_order(self):
        forward = {
            "a.py": _mod(_imp("b")),
            "b.py": _mod(_imp("c")),
            "c.py": _mod(),
        }
        reverse = dict(reversed(list(forward.items())))
        assert topological_order(build_dependency_graph(forward)) == topological_order(
            build_dependency_graph(reverse)
        )

    def test_empty_graph(self):
        assert topological_order({"nodes": [], "edges": []}) == {
            "order": [],
            "cycle_groups": [],
        }


# ── DL-303: detect_side_effects ───────────────────────────────────────


def _calls(*records):
    return {"module_calls": list(records), "functions": []}


class TestDetectSideEffects:
    def test_module_with_assignment_call_reports_side_effect(self):
        inventory = {
            "app.py": _calls({"name": "Flask", "target": "app", "line": 3}),
        }
        result = detect_side_effects(inventory)
        assert result["side_effects"] == [
            {"file": "app.py", "calls": [{"name": "Flask", "target": "app", "line": 3}]}
        ]
        assert result["best_effort"] is True

    def test_create_app_function_detected_as_factory(self):
        inventory = {
            "factory.py": {
                "functions": [{"name": "create_app"}, {"name": "helper"}],
            },
        }
        factories = detect_side_effects(inventory)["factories"]
        assert factories == [
            {"file": "factory.py", "symbol": "create_app", "kind": "factory"}
        ]

    def test_wiring_names_detected_as_wiring(self):
        inventory = {
            "wiring.py": {
                "functions": [
                    {"name": "configure"},
                    {"name": "register_routes"},
                    {"name": "wire"},
                    {"name": "run"},
                ],
            },
        }
        factories = detect_side_effects(inventory)["factories"]
        assert [(f["symbol"], f["kind"]) for f in factories] == [
            ("configure", "wiring"),
            ("register_routes", "wiring"),
            ("wire", "wiring"),
        ]

    def test_module_without_calls_reports_nothing(self):
        inventory = {"pure.py": {"functions": [{"name": "run"}]}}
        result = detect_side_effects(inventory)
        assert result["side_effects"] == []
        assert result["factories"] == []

    def test_results_are_sorted_and_deterministic(self):
        inventory = {
            "z.py": _calls({"name": "init", "line": 1}),
            "a.py": _calls({"name": "boot", "line": 1}),
        }
        files = [
            entry["file"] for entry in detect_side_effects(inventory)["side_effects"]
        ]
        assert files == ["a.py", "z.py"]

    def test_tolerates_non_dict_and_missing_fields(self):
        inventory = {
            "ok.py": _calls({"name": "go", "line": 1}),
            "weird": "not-a-dict",
            "slim.py": {},  # no functions / module_calls
        }
        result = detect_side_effects(inventory)
        assert [e["file"] for e in result["side_effects"]] == ["ok.py"]
        assert result["factories"] == []


# ── Epic 2.4: aggregation + scale guard ───────────────────────────────


def _pymod(*imports):
    return {
        "language": "python",
        "imports": list(imports),
        "classes": [],
        "functions": [],
    }


class TestAnalyzeDependencies:
    def test_bundle_exposes_every_section(self, tmp_path):
        inventory = {
            "pkg/a.py": _pymod(_imp("pkg.b", "B")),
            "pkg/b.py": _pymod(),
        }
        bundle = analyze_dependencies(inventory, str(tmp_path))
        assert set(bundle) == {
            "graph",
            "cycles",
            "metrics",
            "load_order",
            "side_effects",
            "reconciliation",
        }
        # The shared graph drives the dependent sections.
        assert ("pkg/a.py", "pkg/b.py") in bundle["graph"]["edges"]
        assert bundle["load_order"]["order"] == ["pkg/b.py", "pkg/a.py"]

    def test_is_deterministic(self, tmp_path):
        inventory = {"a.py": _pymod(_imp("b", "x")), "b.py": _pymod()}
        assert analyze_dependencies(inventory, str(tmp_path)) == analyze_dependencies(
            inventory, str(tmp_path)
        )

    def test_tolerates_slim_inventory(self, tmp_path):
        # No imports / non-dict entries must never raise.
        bundle = analyze_dependencies({"x.py": {}, "weird": "nope"}, str(tmp_path))
        assert bundle["graph"]["edges"] == []
        assert bundle["cycles"] == []


class TestTopLevelPackage:
    def test_first_path_component(self):
        assert top_level_package("pkg/sub/mod.py") == "pkg"

    def test_root_file_uses_stem(self):
        assert top_level_package("main.py") == "main"


class TestPackageDependencyGraph:
    def test_collapses_and_drops_intra_package_edges(self):
        graph = {
            "nodes": ["pkg/a.py", "pkg/b.py", "other/c.py"],
            "edges": [("pkg/a.py", "pkg/b.py"), ("pkg/a.py", "other/c.py")],
        }
        collapsed = package_dependency_graph(graph)
        assert collapsed["nodes"] == ["other", "pkg"]
        # pkg→pkg is dropped; pkg→other survives, de-duplicated.
        assert collapsed["edges"] == [("pkg", "other")]

    def test_empty_graph_is_empty(self):
        assert package_dependency_graph({"nodes": [], "edges": []}) == {
            "nodes": [],
            "edges": [],
        }
