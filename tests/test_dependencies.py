"""Tests for services/dependencies.py — internal dependency graph."""

from __future__ import annotations

from llm_wiki_cli.services import dependencies
from llm_wiki_cli.services.dependencies import (
    analyze_dependencies,
    build_dependency_graph,
    build_dependency_observations,
    dependency_metrics,
    detect_cycles,
    detect_side_effects,
    package_dependency_graph,
    top_level_package,
    topological_order,
)
from llm_wiki_cli.services.source_snapshot import build_source_snapshot


def _imp(module, name=None):
    """A minimal import record as the extractors emit them."""
    return {"module": module, "name": name if name is not None else module}


def _mod(*imports):
    return {"imports": list(imports)}


# ── Dependency graph construction ─────────────────────────────────────


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

    def test_from_package_import_submodule_resolves(self):
        inventory = {
            "src/pkg/cli.py": _mod(
                {
                    "module": ".commands",
                    "name": "build_cmd",
                    "type": "from",
                },
                {
                    "module": ".services",
                    "name": "runtime",
                    "type": "from",
                },
            ),
            "src/pkg/commands/build_cmd.py": _mod(),
            "src/pkg/services/runtime.py": _mod(),
        }

        graph = build_dependency_graph(inventory)

        assert graph["edges"] == [
            ("src/pkg/cli.py", "src/pkg/commands/build_cmd.py"),
            ("src/pkg/cli.py", "src/pkg/services/runtime.py"),
        ]
        order = topological_order(graph)["order"]
        assert order.index("src/pkg/commands/build_cmd.py") < order.index(
            "src/pkg/cli.py"
        )
        assert order.index("src/pkg/services/runtime.py") < order.index(
            "src/pkg/cli.py"
        )

    def test_from_package_import_prefers_child_over_package_initializer(self):
        inventory = {
            "src/pkg/cli.py": _mod(
                {
                    "module": ".commands",
                    "name": "build_cmd",
                    "type": "from",
                }
            ),
            "src/pkg/commands/__init__.py": _mod(),
            "src/pkg/commands/build_cmd.py": _mod(),
        }

        graph = build_dependency_graph(inventory)

        assert graph["edges"] == [
            ("src/pkg/cli.py", "src/pkg/commands/build_cmd.py")
        ]

    def test_bare_package_import_resolves_to_init_module(self):
        inventory = {
            "service/server.py": _mod(_imp("tools", "Widget")),
            "service/tools/__init__.py": _mod(),
        }
        graph = build_dependency_graph(inventory)
        assert graph["edges"] == [("service/server.py", "service/tools/__init__.py")]
        assert graph["unresolved"] == []

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
            "Dockerfile": {"language": "docker"},
            "weird": "not-a-dict",
        }
        graph = build_dependency_graph(inventory)
        assert graph["nodes"] == ["a.py", "b.py"]
        assert graph["edges"] == [("a.py", "b.py")]

    def test_language_entry_without_imports_is_an_isolated_node(self):
        inventory = {
            "bundle/main.js": {
                "language": "javascript",
                "module_calls": [{"name": "require", "line": 1}],
            },
            "metadata": {"module_calls": []},
            "empty-language": {"language": "   "},
            "unknown-language": {"language": "custom-plugin-language"},
        }

        graph = build_dependency_graph(inventory)

        assert graph == {
            "edges": [],
            "nodes": ["bundle/main.js"],
            "unresolved": [],
        }
        assert topological_order(graph) == {
            "order": ["bundle/main.js"],
            "cycle_groups": [],
        }

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


class TestBuildDependencyObservations:
    def test_preserves_resolution_candidates_location_and_legacy_shape(self):
        inventory = {
            "app.py": _mod(
                {"module": "pkg.target", "name": "run", "line": 7},
                {"module": "shared", "name": "missing", "line": 0},
                {"module": "requests", "name": "get"},
                {"module": ".missing", "name": "value", "line": -2},
            ),
            "pkg/target.py": _mod(),
            "one/shared.py": _mod(),
            "two/shared.py": _mod(),
        }

        legacy = build_dependency_graph(inventory)
        result = build_dependency_observations(inventory)
        by_module = {item["module"]: item for item in result["observations"]}

        assert legacy == {
            "edges": [
                ("app.py", "one/shared.py"),
                ("app.py", "pkg/target.py"),
                ("app.py", "two/shared.py"),
            ],
            "nodes": [
                "app.py",
                "one/shared.py",
                "pkg/target.py",
                "two/shared.py",
            ],
            "unresolved": [
                {"file": "app.py", "module": ".missing", "name": "value"},
                {"file": "app.py", "module": "requests", "name": "get"},
            ],
        }
        assert by_module["pkg.target"] == {
            "source_path": "app.py",
            "module": "pkg.target",
            "name": "run",
            "line": 7,
            "candidates": ["pkg/target.py"],
            "target_path": "pkg/target.py",
            "resolution": "resolved",
        }
        assert by_module["shared"]["candidates"] == [
            "one/shared.py",
            "two/shared.py",
        ]
        assert by_module["shared"]["target_path"] is None
        assert by_module["shared"]["resolution"] == "ambiguous"
        assert by_module["shared"]["line"] is None
        assert by_module["requests"]["resolution"] == "external"
        assert by_module["requests"]["line"] is None
        assert by_module[".missing"]["resolution"] == "unresolved"
        assert by_module[".missing"]["line"] is None

        assert result["schema_version"] == "llm-wiki-dependency-observations/v1"
        assert result["coverage"]["observed"] == 4
        assert result["coverage"]["emitted"] == 4
        assert result["coverage"]["limit"] is None
        assert result["coverage"]["truncated"] is False
        assert result["coverage"]["omitted"] == 0
        assert result["coverage"]["limitations"]

    def test_keeps_duplicate_and_self_import_observations_deterministically(self):
        imports = [
            {"module": "b", "name": "second"},
            {"module": "a", "name": "a", "line": 0},
            {"module": "b", "name": "first", "line": 2},
        ]
        forward = {
            "a.py": {"imports": list(imports)},
            "b.py": {"imports": []},
        }
        reverse = {
            "b.py": {"imports": []},
            "a.py": {"imports": list(reversed(imports))},
        }

        first = build_dependency_observations(forward)
        second = build_dependency_observations(reverse)

        assert first == second
        assert [item["module"] for item in first["observations"]] == ["a", "b", "b"]
        self_import = first["observations"][0]
        assert self_import["resolution"] == "resolved"
        assert self_import["target_path"] == "a.py"
        assert self_import["line"] is None

    def test_package_child_import_observations_preserve_resolution_semantics(self):
        inventory = {
            "app.py": _mod(
                {
                    "module": "commands",
                    "name": "build",
                    "type": "from",
                },
                {
                    "module": "requests",
                    "name": "Session",
                    "type": "from",
                },
            ),
            "one/commands/build.py": _mod(),
            "two/commands/build.py": _mod(),
        }

        result = build_dependency_observations(inventory)
        by_module = {item["module"]: item for item in result["observations"]}

        assert by_module["commands"] == {
            "source_path": "app.py",
            "module": "commands",
            "name": "build",
            "line": None,
            "candidates": [
                "one/commands/build.py",
                "two/commands/build.py",
            ],
            "target_path": None,
            "resolution": "ambiguous",
        }
        assert by_module["requests"]["candidates"] == []
        assert by_module["requests"]["target_path"] is None
        assert by_module["requests"]["resolution"] == "external"

    def test_versioned_location_sidecar_is_matched_and_validated(self):
        inventory = {
            "a.py": {
                "imports": [
                    {"module": "b", "name": "b"},
                    {"module": "requests", "name": "get"},
                    {"module": ".missing", "name": "value"},
                ]
            },
            "b.py": {"imports": []},
        }
        sidecar = {
            "schema_version": "llm-wiki-import-location-observations/v1",
            "observations": [
                {
                    "source_path": "a.py",
                    "import_index": 2,
                    "module": ".different",
                    "name": "value",
                    "line": 13,
                },
                {
                    "source_path": "a.py",
                    "import_index": 1,
                    "module": "requests",
                    "name": "get",
                    "line": 0,
                },
                {
                    "source_path": "a.py",
                    "import_index": 0,
                    "module": "b",
                    "name": "b",
                    "line": 11,
                },
            ],
        }

        result = build_dependency_observations(
            inventory,
            import_observations=sidecar,
        )
        by_module = {item["module"]: item for item in result["observations"]}

        assert by_module["b"]["line"] == 11
        assert by_module["requests"]["line"] is None
        assert by_module[".missing"]["line"] is None
        assert "invalid-import-location-observations" in result["coverage"][
            "limitations"
        ]
        assert "mismatched-import-location-observations" in result["coverage"][
            "limitations"
        ]
        assert build_dependency_observations(
            inventory,
            import_observations={
                **sidecar,
                "observations": list(reversed(sidecar["observations"])),
            },
        ) == result

    def test_malformed_import_omission_is_reported_exactly(self):
        result = build_dependency_observations(
            {
                "a.py": {
                    "imports": [
                        "not-an-import-record",
                        {"module": "requests", "name": "get"},
                    ]
                }
            }
        )

        assert len(result["observations"]) == 1
        assert result["coverage"] == {
            "observed": 2,
            "emitted": 1,
            "limit": None,
            "truncated": True,
            "omitted": 1,
            "limitations": [
                "external-resolution-is-relative-to-the-selected-inventory",
                "import-locations-depend-on-extractor-support",
                "malformed-import-records",
                "static-import-resolution-does-not-claim-runtime-completeness",
            ],
        }


# ── Cycle detection ───────────────────────────────────────────────────


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


# ── Dependency metrics ────────────────────────────────────────────────


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


# ── Topological ordering ──────────────────────────────────────────────


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


# ── Import side-effect detection ──────────────────────────────────────


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


# ── Aggregation and scale guard ───────────────────────────────────────


def _pymod(*imports):
    return {
        "language": "python",
        "imports": list(imports),
        "classes": [],
        "functions": [],
    }


def _tsmod(*imports):
    return {
        "language": "typescript",
        "imports": list(imports),
        "classes": [],
        "functions": [],
    }


def _jsmod(*imports):
    return {
        "language": "javascript",
        "imports": list(imports),
        "classes": [],
        "functions": [],
    }


def _hsmod(*imports, module="Main"):
    return {
        "language": "haskell",
        "module": module,
        "imports": list(imports),
        "classes": [],
        "functions": [],
    }


def _gomod(*imports):
    return {
        "language": "go",
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

    def test_go_module_imports_resolve_without_stdlib_stem_collision(self, tmp_path):
        (tmp_path / "go.mod").write_text(
            "module github.com/charmbracelet/teamcrush\n\ngo 1.23\n",
            encoding="utf-8",
        )
        inventory = {
            "cmd/teamcrush/main.go": {
                "language": "go",
                "imports": [
                    _imp("github.com/charmbracelet/teamcrush/internal/agents"),
                    _imp("context"),
                ],
            },
            "internal/agents/agent.go": {
                "language": "go",
                "imports": [],
            },
            "internal/orchestrator/context.go": {
                "language": "go",
                "imports": [],
            },
        }

        graph = analyze_dependencies(inventory, str(tmp_path))["graph"]

        assert graph["edges"] == [("cmd/teamcrush/main.go", "internal/agents/agent.go")]
        assert (
            "cmd/teamcrush/main.go",
            "internal/orchestrator/context.go",
        ) not in graph["edges"]
        assert graph["unresolved"] == [
            {
                "file": "cmd/teamcrush/main.go",
                "module": "context",
                "name": "context",
            }
        ]

    def test_nested_go_module_import_resolves_as_internal_dependency(self, tmp_path):
        nested = tmp_path / "libs" / "identity_client_go"
        nested.mkdir(parents=True)
        (nested / "go.mod").write_text(
            "module github.com/traid-platform/identityclient\n\ngo 1.21\n",
            encoding="utf-8",
        )
        inventory = {
            "libs/identity_client_go/example/main.go": _gomod(
                _imp("context"),
                _imp("github.com/traid-platform/identityclient"),
                _imp("github.com/external/undeclared"),
            ),
            "libs/identity_client_go/identity_client.go": _gomod(),
            "libs/identity_client_go/example/context.go": _gomod(),
        }

        bundle = analyze_dependencies(inventory, str(tmp_path))
        graph = bundle["graph"]
        go = bundle["reconciliation"]["languages"]["go"]

        assert graph["edges"] == [
            (
                "libs/identity_client_go/example/main.go",
                "libs/identity_client_go/identity_client.go",
            )
        ]
        assert {
            "file": "libs/identity_client_go/example/main.go",
            "module": "context",
            "name": "context",
        } in graph["unresolved"]
        assert go["used"] == {
            "github.com/external/undeclared": [
                "libs/identity_client_go/example/main.go"
            ]
        }
        assert go["undeclared"] == ["github.com/external/undeclared"]

    def test_haskell_declared_modules_create_internal_edges_and_metrics(self, tmp_path):
        inventory = {
            "hls-analysis/app/Main.hs": {
                "language": "haskell",
                "module": "Main",
                "imports": [
                    _imp("HLSAnalysis.API", ""),
                    _imp("Data.Text", ""),
                ],
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

        bundle = analyze_dependencies(inventory, str(tmp_path))
        graph = bundle["graph"]

        assert graph["edges"] == [
            (
                "hls-analysis/app/Main.hs",
                "hls-analysis/src/HLSAnalysis/API.hs",
            )
        ]
        assert graph["unresolved"] == [
            {
                "file": "hls-analysis/app/Main.hs",
                "module": "Data.Text",
                "name": "",
            }
        ]
        assert bundle["metrics"]["metrics"]["hls-analysis/app/Main.hs"] == {
            "fan_in": 0,
            "fan_out": 1,
        }
        assert bundle["metrics"]["metrics"]["hls-analysis/src/HLSAnalysis/API.hs"] == {
            "fan_in": 1,
            "fan_out": 0,
        }

    def test_haskell_cabal_dependencies_reconcile_known_imports(self, tmp_path):
        cabal = tmp_path / "hls-analysis" / "hls-analysis.cabal"
        cabal.parent.mkdir()
        cabal.write_text(
            """
            cabal-version: 3.0
            name: hls-analysis

            library
              build-depends: base >=4.17
                           , aeson >=2.0
                           , containers >=0.6
                           , servant >=0.19
                           , text >=1.2
                           , unused-required >=1.0
              hs-source-dirs: src

            test-suite hls-analysis-test
              build-depends: base
                           , hls-analysis
                           , hspec >=2.10
              hs-source-dirs: test
            """,
            encoding="utf-8",
        )
        inventory = {
            "hls-analysis/src/HLSAnalysis/API.hs": _hsmod(
                _imp("Prelude", ""),
                _imp("Data.Map", ""),
                _imp("Data.Text", ""),
                _imp("Servant", ""),
                _imp("Unknown.Widget", ""),
                _imp("HLSAnalysis.Types", ""),
                module="HLSAnalysis.API",
            ),
            "hls-analysis/src/HLSAnalysis/Types.hs": _hsmod(module="HLSAnalysis.Types"),
            "hls-analysis/test/Spec.hs": _hsmod(
                _imp("Test.Hspec", ""),
                module="Spec",
            ),
        }

        haskell = analyze_dependencies(inventory, str(tmp_path))["reconciliation"][
            "languages"
        ]["haskell"]

        assert haskell["used"] == {
            "base": ["hls-analysis/src/HLSAnalysis/API.hs"],
            "containers": ["hls-analysis/src/HLSAnalysis/API.hs"],
            "hspec": ["hls-analysis/test/Spec.hs"],
            "servant": ["hls-analysis/src/HLSAnalysis/API.hs"],
            "text": ["hls-analysis/src/HLSAnalysis/API.hs"],
        }
        assert haskell["undeclared"] == []
        assert haskell["unused"] == ["aeson", "unused-required"]
        assert "Data" not in haskell["used"]
        assert "Test" not in haskell["used"]

    def test_haskell_cabal_dependencies_are_scoped_to_nearest_package(self, tmp_path):
        (tmp_path / "cabal.project").write_text(
            "packages:\n  core\n  api\n",
            encoding="utf-8",
        )
        core = tmp_path / "core"
        api = tmp_path / "api"
        core.mkdir()
        api.mkdir()
        (core / "core.cabal").write_text(
            """
            cabal-version: 3.0
            name: core
            library
              build-depends: base, text
              hs-source-dirs: src
            """,
            encoding="utf-8",
        )
        (api / "api.cabal").write_text(
            """
            cabal-version: 3.0
            name: api
            library
              build-depends: base, servant
              hs-source-dirs: src
            """,
            encoding="utf-8",
        )
        inventory = {
            "core/src/Core.hs": _hsmod(
                _imp("Prelude", ""),
                _imp("Data.Text", ""),
                _imp("Servant", ""),
                module="Core",
            ),
            "api/src/API.hs": _hsmod(
                _imp("Prelude", ""),
                _imp("Servant", ""),
                module="API",
            ),
        }

        haskell = analyze_dependencies(inventory, str(tmp_path))["reconciliation"][
            "languages"
        ]["haskell"]

        assert haskell["used"] == {
            "base": ["api/src/API.hs", "core/src/Core.hs"],
            "servant": ["api/src/API.hs", "core/src/Core.hs"],
            "text": ["core/src/Core.hs"],
        }
        assert haskell["undeclared"] == ["servant"]
        assert haskell["unused"] == []

    def test_haskell_stack_and_nix_hints_are_optional_only(self, tmp_path):
        (tmp_path / "app.cabal").write_text(
            """
            cabal-version: 3.0
            name: app
            library
              build-depends: base, text
              hs-source-dirs: src
            """,
            encoding="utf-8",
        )
        (tmp_path / "stack.yaml").write_text(
            """
            packages:
            - .
            extra-deps:
            - hspec-2.11.0
            """,
            encoding="utf-8",
        )
        (tmp_path / "flake.nix").write_text(
            """
            { pkgs, ... }:
            pkgs.haskellPackages.servant
            """,
            encoding="utf-8",
        )
        inventory = {
            "src/App.hs": _hsmod(
                _imp("Data.Text", ""),
                _imp("Servant", ""),
                _imp("Test.Hspec", ""),
                module="App",
            ),
        }

        haskell = analyze_dependencies(inventory, str(tmp_path))["reconciliation"][
            "languages"
        ]["haskell"]

        assert haskell["required"] == ["base", "text"]
        assert haskell["optional"] == ["hspec", "servant"]
        assert haskell["undeclared"] == []
        assert haskell["unused"] == ["base"]

    def test_python_external_imports_do_not_resolve_to_same_stem_go_modules(
        self, tmp_path
    ):
        (tmp_path / "rlm").mkdir()
        (tmp_path / "rlm" / "requirements.txt").write_text(
            "anthropic\nopenai\n",
            encoding="utf-8",
        )
        inventory = {
            "rlm/gateway.py": _pymod(
                _imp("anthropic", "anthropic"),
                _imp("openai", "openai"),
            ),
            "internal/llm/anthropic.go": {
                "language": "go",
                "imports": [],
            },
            "internal/llm/openai.go": {
                "language": "go",
                "imports": [],
            },
        }

        bundle = analyze_dependencies(inventory, str(tmp_path))
        graph = bundle["graph"]
        python = bundle["reconciliation"]["languages"]["python"]

        assert ("rlm/gateway.py", "internal/llm/anthropic.go") not in graph["edges"]
        assert ("rlm/gateway.py", "internal/llm/openai.go") not in graph["edges"]
        assert graph["unresolved"] == [
            {
                "file": "rlm/gateway.py",
                "module": "anthropic",
                "name": "anthropic",
            },
            {
                "file": "rlm/gateway.py",
                "module": "openai",
                "name": "openai",
            },
        ]
        assert python["used"] == {
            "anthropic": ["rlm/gateway.py"],
            "openai": ["rlm/gateway.py"],
        }
        assert python["unused"] == []
        assert python["undeclared"] == []

    def test_python_manifests_ignore_generated_agent_worktree_scopes(self, tmp_path):
        (tmp_path / "rlm").mkdir()
        (tmp_path / "rlm" / "requirements.txt").write_text(
            "openai\n",
            encoding="utf-8",
        )
        worktree_rlm = (
            tmp_path / ".claude" / "worktrees" / "agent-strict-instructions" / "rlm"
        )
        worktree_rlm.mkdir(parents=True)
        (worktree_rlm / "requirements.txt").write_text(
            "openai\n",
            encoding="utf-8",
        )
        inventory = {
            "rlm/gateway.py": _pymod(_imp("openai", "openai")),
        }

        python = analyze_dependencies(inventory, str(tmp_path))["reconciliation"][
            "languages"
        ]["python"]

        assert python["used"] == {"openai": ["rlm/gateway.py"]}
        assert python["unused"] == []

    def test_manifests_under_gitignored_directories_do_not_reconcile(self, tmp_path):
        (tmp_path / ".gitignore").write_text(
            "projects/\n!projects/.gitkeep\n", encoding="utf-8"
        )
        (tmp_path / "docker").mkdir()
        (tmp_path / "docker" / "web-auth-proxy.js").write_text(
            "export const proxy = {};\n", encoding="utf-8"
        )
        ignored = tmp_path / "projects" / "test-project"
        ignored.mkdir(parents=True)
        (ignored / "pyproject.toml").write_text(
            """
            [project]
            dependencies = [
                "boto3",
                "pandas",
                "pyarrow",
                "python-dotenv",
            ]
            """,
            encoding="utf-8",
        )
        (ignored / "package.json").write_text(
            """
            {
              "dependencies": {
                "@aws-sdk/client-s3": "^3.700.0",
                "apache-arrow": "^18.0.0",
                "dotenv": "^16.4.0"
              }
            }
            """,
            encoding="utf-8",
        )
        inventory = {
            "docker/web-auth-proxy.js": _jsmod(),
        }

        languages = analyze_dependencies(inventory, str(tmp_path))["reconciliation"][
            "languages"
        ]

        assert "python" not in languages
        assert "typescript" not in languages

    def test_typescript_nested_manifest_and_tsconfig_aliases_reconcile(self, tmp_path):
        frontend = tmp_path / "frontend"
        (frontend / "src" / "components" / "projects").mkdir(parents=True)
        (frontend / "src" / "hooks").mkdir(parents=True)
        (frontend / "package.json").write_text(
            """
            {
              "dependencies": {
                "@tanstack/react-query": "5.0.0",
                "lucide-react": "0.1.0",
                "react": "18.0.0",
                "react-router-dom": "6.0.0",
                "zustand": "4.0.0"
              },
              "devDependencies": {
                "@playwright/test": "1.0.0",
                "@testing-library/react": "14.0.0",
                "vitest": "1.0.0"
              }
            }
            """,
            encoding="utf-8",
        )
        (frontend / "tsconfig.json").write_text(
            """
            {
              "compilerOptions": {
                "baseUrl": ".",
                "paths": {
                  "@/*": ["./src/*"],
                  "@/components/*": ["./src/components/*"],
                  "@/hooks/*": ["./src/hooks/*"]
                }
              }
            }
            """,
            encoding="utf-8",
        )
        inventory = {
            "frontend/src/App.tsx": _tsmod(
                _imp("@/components/projects", "ProjectList"),
                _imp("@/hooks/useAuth", "useAuth"),
                _imp("@playwright/test", "test"),
                _imp("@tanstack/react-query", "useQuery"),
                _imp("@testing-library/react", "render"),
                _imp("lucide-react", "Icon"),
                _imp("react", "React"),
                _imp("react-router-dom", "Router"),
                _imp("vitest", "describe"),
                _imp("zustand", "create"),
            ),
            "frontend/src/components/projects/index.ts": _tsmod(),
            "frontend/src/hooks/useAuth.ts": _tsmod(),
        }

        bundle = analyze_dependencies(inventory, str(tmp_path))

        assert (
            "frontend/src/App.tsx",
            "frontend/src/components/projects/index.ts",
        ) in bundle["graph"]["edges"]
        assert ("frontend/src/App.tsx", "frontend/src/hooks/useAuth.ts") in bundle[
            "graph"
        ]["edges"]
        typescript = bundle["reconciliation"]["languages"]["typescript"]
        assert typescript["undeclared"] == []
        assert "@playwright/test" in typescript["optional"]
        assert "@testing-library/react" in typescript["optional"]
        assert "vitest" in typescript["optional"]

    def test_nested_typescript_manifest_does_not_leak_outside_scope(self, tmp_path):
        frontend = tmp_path / "frontend"
        frontend.mkdir()
        (frontend / "package.json").write_text(
            '{"dependencies": {"react": "18.0.0"}}',
            encoding="utf-8",
        )
        inventory = {
            "tools/render.ts": _tsmod(_imp("react", "React")),
        }

        typescript = analyze_dependencies(inventory, str(tmp_path))["reconciliation"][
            "languages"
        ]["typescript"]

        assert typescript["undeclared"] == ["react"]

    def test_javascript_inventory_uses_typescript_manifest_and_aliases(self, tmp_path):
        frontend = tmp_path / "frontend"
        (frontend / "src" / "lib").mkdir(parents=True)
        (frontend / "package.json").write_text(
            '{"dependencies": {"react": "18.0.0"}}',
            encoding="utf-8",
        )
        (frontend / "tsconfig.json").write_text(
            """
            {
              "compilerOptions": {
                "baseUrl": ".",
                "paths": {"@/*": ["./src/*"]}
              }
            }
            """,
            encoding="utf-8",
        )
        inventory = {
            "frontend/src/app.js": _jsmod(
                _imp("@/lib/api", "api"),
                _imp("react", "React"),
            ),
            "frontend/src/lib/api.js": _jsmod(),
        }

        bundle = analyze_dependencies(inventory, str(tmp_path))

        assert ("frontend/src/app.js", "frontend/src/lib/api.js") in bundle["graph"][
            "edges"
        ]
        typescript = bundle["reconciliation"]["languages"]["typescript"]
        assert typescript["used"] == {"react": ["frontend/src/app.js"]}
        assert typescript["undeclared"] == []

    def test_typescript_manifests_ignore_generated_agent_worktree_scopes(
        self, tmp_path
    ):
        web = tmp_path / "web"
        web.mkdir()
        (web / "package.json").write_text(
            '{"dependencies": {"react": "18.0.0"}}',
            encoding="utf-8",
        )
        generated_web = (
            tmp_path / ".claude" / "worktrees" / "agent-strict-instructions" / "web"
        )
        generated_web.mkdir(parents=True)
        (generated_web / "package.json").write_text(
            '{"dependencies": {"left-pad": "1.3.0"}}',
            encoding="utf-8",
        )
        inventory = {
            "web/src/app.js": _jsmod(_imp("react", "React")),
        }

        typescript = analyze_dependencies(inventory, str(tmp_path))["reconciliation"][
            "languages"
        ]["typescript"]

        assert typescript["required"] == ["react"]
        assert typescript["unused"] == []

    def test_python_local_src_imports_are_first_party_and_yaml_maps_to_pyyaml(
        self, tmp_path
    ):
        (tmp_path / "src").mkdir()
        (tmp_path / "src" / "__init__.py").write_text("", encoding="utf-8")
        (tmp_path / "pyproject.toml").write_text(
            '[project]\ndependencies = ["PyYAML"]\n',
            encoding="utf-8",
        )
        inventory = {
            "scripts/backup.py": _pymod(
                _imp("src.config", "settings"),
                _imp("yaml", "safe_load"),
            ),
        }

        python = analyze_dependencies(inventory, str(tmp_path))["reconciliation"][
            "languages"
        ]["python"]

        assert python["used"] == {"pyyaml": ["scripts/backup.py"]}
        assert python["undeclared"] == []

    def test_python_service_pyproject_aliases_reconcile_by_nearest_manifest(
        self, tmp_path
    ):
        dialogue = tmp_path / "services" / "dialogue"
        diarization = tmp_path / "services" / "diarization"
        dialogue.mkdir(parents=True)
        diarization.mkdir(parents=True)
        (dialogue / "pyproject.toml").write_text(
            """
            [project]
            name = "dialogue-service"
            dependencies = [
                "grpcio",
                "prometheus-client",
                "pydantic-settings",
            ]
            """,
            encoding="utf-8",
        )
        (diarization / "pyproject.toml").write_text(
            """
            [project]
            name = "diarization-service"
            dependencies = [
                "grpcio",
                "nvidia-riva-client",
                "pyannote.audio",
                "numpy",
            ]
            """,
            encoding="utf-8",
        )
        inventory = {
            "services/dialogue/src/dialogue/main.py": _pymod(
                _imp("grpc"),
                _imp("prometheus_client", "Counter"),
                _imp("pydantic_settings", "BaseSettings"),
            ),
            "services/diarization/src/diarization/riva_backend.py": _pymod(
                _imp("grpc"),
                _imp("riva.client", "RivaClient"),
                _imp("pyannote.audio", "Pipeline"),
                _imp("numpy", "array"),
            ),
        }

        python = analyze_dependencies(inventory, str(tmp_path))["reconciliation"][
            "languages"
        ]["python"]

        assert python["used"] == {
            "grpcio": [
                "services/dialogue/src/dialogue/main.py",
                "services/diarization/src/diarization/riva_backend.py",
            ],
            "numpy": ["services/diarization/src/diarization/riva_backend.py"],
            "nvidia-riva-client": [
                "services/diarization/src/diarization/riva_backend.py"
            ],
            "prometheus-client": ["services/dialogue/src/dialogue/main.py"],
            "pydantic-settings": ["services/dialogue/src/dialogue/main.py"],
            "pyannote-audio": ["services/diarization/src/diarization/riva_backend.py"],
        }
        assert python["undeclared"] == []
        assert python["unused"] == []

    def test_python_internal_service_distribution_import_counts_as_used(self, tmp_path):
        dialogue = tmp_path / "services" / "dialogue"
        shared = tmp_path / "services" / "shared"
        (dialogue / "src" / "dialogue").mkdir(parents=True)
        (shared / "src" / "shared").mkdir(parents=True)
        (dialogue / "pyproject.toml").write_text(
            """
            [project]
            name = "dialogue-service"
            dependencies = ["assistant-shared"]

            [tool.setuptools.packages.find]
            where = ["src"]
            """,
            encoding="utf-8",
        )
        (shared / "pyproject.toml").write_text(
            """
            [project]
            name = "assistant-shared"
            dependencies = []

            [tool.setuptools.packages.find]
            where = ["src"]
            """,
            encoding="utf-8",
        )
        (shared / "src" / "shared" / "__init__.py").write_text("", encoding="utf-8")
        inventory = {
            "services/dialogue/src/dialogue/main.py": _pymod(
                _imp("shared.config", "get_settings")
            ),
            "services/shared/src/shared/config.py": _pymod(),
        }

        bundle = analyze_dependencies(inventory, str(tmp_path))
        graph = bundle["graph"]
        python = bundle["reconciliation"]["languages"]["python"]

        assert (
            "services/dialogue/src/dialogue/main.py",
            "services/shared/src/shared/config.py",
        ) in graph["edges"]
        assert python["used"] == {
            "assistant-shared": ["services/dialogue/src/dialogue/main.py"]
        }
        assert python["undeclared"] == []
        assert python["unused"] == []

    def test_python_repo_qualified_internal_edge_does_not_count_service_dist(
        self, tmp_path
    ):
        service = tmp_path / "services" / "audio_ingest"
        package = service / "src" / "audio_ingest"
        package.mkdir(parents=True)
        (service / "pyproject.toml").write_text(
            """
            [project]
            name = "audio-ingest-service"
            dependencies = []

            [tool.setuptools.packages.find]
            where = ["src"]
            """,
            encoding="utf-8",
        )
        (package / "__init__.py").write_text("", encoding="utf-8")
        inventory = {
            "tests/unit/test_audio.py": _pymod(
                _imp("services.audio_ingest.src.audio_ingest.main", "run")
            ),
            "services/audio_ingest/src/audio_ingest/main.py": _pymod(),
        }

        bundle = analyze_dependencies(inventory, str(tmp_path))
        graph = bundle["graph"]
        python = bundle["reconciliation"]["languages"]["python"]

        assert (
            "tests/unit/test_audio.py",
            "services/audio_ingest/src/audio_ingest/main.py",
        ) in graph["edges"]
        assert "audio-ingest-service" not in python["used"]
        assert "audio-ingest-service" not in python["undeclared"]

    def test_python_true_undeclared_and_unused_remain_scoped(self, tmp_path):
        service = tmp_path / "services" / "dialogue"
        service.mkdir(parents=True)
        (service / "pyproject.toml").write_text(
            """
            [project]
            name = "dialogue-service"
            dependencies = ["requests"]
            """,
            encoding="utf-8",
        )
        inventory = {
            "services/dialogue/src/dialogue/main.py": _pymod(_imp("httpx")),
        }

        python = analyze_dependencies(inventory, str(tmp_path))["reconciliation"][
            "languages"
        ]["python"]

        assert python["undeclared"] == ["httpx"]
        assert python["unused"] == ["requests"]
        assert python["undeclared_details"] == [
            {
                "package": "httpx",
                "files": ["services/dialogue/src/dialogue/main.py"],
                "scope": "services/dialogue",
            }
        ]
        assert python["unused_details"] == [
            {
                "package": "requests",
                "files": [],
                "scope": "services/dialogue",
            }
        ]

    def test_go_sum_versions_are_resolved_metadata(self, tmp_path):
        (tmp_path / "go.mod").write_text(
            """
            module example.com/app

            go 1.22

            require github.com/pkg/errors v0.9.0
            """,
            encoding="utf-8",
        )
        (tmp_path / "go.sum").write_text(
            """
            github.com/pkg/errors v0.8.1 h1:old
            github.com/pkg/errors v0.9.1 h1:direct
            github.com/pkg/errors v0.9.1/go.mod h1:mod
            """,
            encoding="utf-8",
        )
        inventory = {
            "main.go": _gomod(_imp("github.com/pkg/errors")),
        }

        go = analyze_dependencies(inventory, str(tmp_path))["reconciliation"][
            "languages"
        ]["go"]

        assert go["versions"] == {
            "github.com/pkg/errors": {
                "version": "v0.9.1",
                "resolved_from": "go.sum",
            }
        }
        assert go["required"] == ["github.com/pkg/errors"]
        assert go["undeclared"] == []

    def test_rust_cargo_lock_versions_are_resolved_metadata(self, tmp_path):
        (tmp_path / "Cargo.toml").write_text(
            """
            [package]
            name = "app"
            version = "0.1.0"

            [dependencies]
            serde = "1"
            """,
            encoding="utf-8",
        )
        (tmp_path / "Cargo.lock").write_text(
            """
            [[package]]
            name = "serde"
            version = "1.0.197"
            source = "registry+https://github.com/rust-lang/crates.io-index"
            """,
            encoding="utf-8",
        )
        inventory = {
            "src/lib.rs": {
                "language": "rust",
                "imports": [_imp("serde::Serialize")],
                "classes": [],
                "functions": [],
            }
        }

        rust = analyze_dependencies(inventory, str(tmp_path))["reconciliation"][
            "languages"
        ]["rust"]

        assert rust["versions"] == {
            "serde": {"version": "1.0.197", "resolved_from": "Cargo.lock"}
        }
        assert rust["required"] == ["serde"]

    def test_python_poetry_lock_and_requirements_pins_resolve_versions(self, tmp_path):
        (tmp_path / "pyproject.toml").write_text(
            """
            [project]
            dependencies = ["requests>=2", "httpx>=0.27"]
            """,
            encoding="utf-8",
        )
        (tmp_path / "poetry.lock").write_text(
            """
            [[package]]
            name = "requests"
            version = "2.31.0"
            """,
            encoding="utf-8",
        )
        (tmp_path / "requirements.txt").write_text(
            """
            httpx==0.27.2
            click>=8
            -e git+https://example.invalid/pkg#egg=local-pkg
            """,
            encoding="utf-8",
        )
        inventory = {
            "app.py": _pymod(
                _imp("requests", "requests"),
                _imp("httpx", "httpx"),
            )
        }

        python = analyze_dependencies(inventory, str(tmp_path))["reconciliation"][
            "languages"
        ]["python"]

        assert python["versions"] == {
            "httpx": {"version": "0.27.2", "resolved_from": "requirements.txt"},
            "requests": {"version": "2.31.0", "resolved_from": "poetry.lock"},
        }
        assert "click" not in python["versions"]
        assert "local-pkg" not in python["versions"]

    def test_dependency_analysis_reuses_snapshot_for_lockfile_discovery(
        self,
        tmp_path,
        monkeypatch,
    ):
        (tmp_path / "pyproject.toml").write_text(
            '[project]\ndependencies = ["requests>=2"]\n',
            encoding="utf-8",
        )
        (tmp_path / "requirements.txt").write_text(
            "requests==2.31.0\n",
            encoding="utf-8",
        )
        (tmp_path / "app.py").write_text(
            "import requests\n",
            encoding="utf-8",
        )
        snapshot = build_source_snapshot(tmp_path)

        def fail_if_walked(*_args, **_kwargs):
            raise AssertionError("dependency analysis must reuse the source snapshot")

        monkeypatch.setattr(dependencies.os, "walk", fail_if_walked)

        result = analyze_dependencies(
            {"app.py": _pymod(_imp("requests", "requests"))},
            str(tmp_path),
            source_snapshot=snapshot,
        )

        assert result["reconciliation"]["languages"]["python"]["versions"] == {
            "requests": {
                "version": "2.31.0",
                "resolved_from": "requirements.txt",
            }
        }

    def test_javascript_package_lock_and_pnpm_versions_resolve_metadata(self, tmp_path):
        (tmp_path / "package.json").write_text(
            """
            {
              "dependencies": {
                "react": "^18.0.0",
                "@scope/pkg": "^2.0.0",
                "left-pad": "^1.0.0"
              }
            }
            """,
            encoding="utf-8",
        )
        (tmp_path / "package-lock.json").write_text(
            """
            {
              "lockfileVersion": 3,
              "packages": {
                "": {},
                "node_modules/react": {"version": "18.2.0"},
                "node_modules/@scope/pkg": {"version": "2.1.0"}
              }
            }
            """,
            encoding="utf-8",
        )
        (tmp_path / "pnpm-lock.yaml").write_text(
            """
            lockfileVersion: '9.0'
            packages:
              /left-pad@1.3.0:
                resolution: {integrity: sha512-test}
            """,
            encoding="utf-8",
        )
        inventory = {
            "src/app.js": _jsmod(
                _imp("react", "React"),
                _imp("@scope/pkg", "pkg"),
                _imp("left-pad", "leftPad"),
            )
        }

        typescript = analyze_dependencies(inventory, str(tmp_path))["reconciliation"][
            "languages"
        ]["typescript"]

        assert typescript["versions"] == {
            "@scope/pkg": {
                "version": "2.1.0",
                "resolved_from": "package-lock.json",
            },
            "left-pad": {"version": "1.3.0", "resolved_from": "pnpm-lock.yaml"},
            "react": {"version": "18.2.0", "resolved_from": "package-lock.json"},
        }

    def test_unparseable_lockfiles_omit_versions_without_changing_lint_sets(
        self, tmp_path
    ):
        (tmp_path / "package.json").write_text(
            '{"dependencies": {"react": "^18.0.0"}}',
            encoding="utf-8",
        )
        (tmp_path / "package-lock.json").write_text("{not json", encoding="utf-8")
        (tmp_path / "pnpm-lock.yaml").write_text(
            "packages:\n  not a supported shape\n", encoding="utf-8"
        )
        inventory = {"src/app.js": _jsmod(_imp("react", "React"))}

        typescript = analyze_dependencies(inventory, str(tmp_path))["reconciliation"][
            "languages"
        ]["typescript"]

        assert typescript["versions"] == {}
        assert typescript["undeclared"] == []
        assert typescript["unused"] == []


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
