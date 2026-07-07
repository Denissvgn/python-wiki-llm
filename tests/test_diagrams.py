"""Tests for services/diagrams.py — pure Mermaid renderers."""

from __future__ import annotations

import json
import textwrap

from llm_wiki_cli.services import plugins
from llm_wiki_cli.services.diagrams import (
    data_flow_diagram,
    flowchart,
    resolve_diagram_style,
    sequence_diagram,
)


class TestSequenceDiagram:
    def test_renders_fenced_mermaid_block(self):
        out = sequence_diagram([{"from": "a", "to": "b", "label": "b"}])
        assert out.startswith("```mermaid\nsequenceDiagram")
        assert out.endswith("```")

    def test_declares_participants_in_first_seen_order(self):
        out = sequence_diagram(
            [
                {"from": "main", "to": "parse", "label": "parse"},
                {"from": "main", "to": "run", "label": "run"},
            ]
        )
        lines = out.splitlines()
        assert "    participant p0 as main" in lines
        assert "    participant p1 as parse" in lines
        assert "    participant p2 as run" in lines
        assert "    p0->>p1: parse" in lines
        assert "    p0->>p2: run" in lines

    def test_dashed_arrow_for_boundary_calls(self):
        out = sequence_diagram(
            [{"from": "a", "to": "getcwd", "label": "getcwd", "dashed": True}]
        )
        assert "-->>" in out
        assert "->>" in out  # the dashed arrow still contains the base arrow token

    def test_labels_are_sanitized(self):
        out = sequence_diagram([{"from": "a", "to": "b", "label": "do(x); y\nz"}])
        assert "do x y z" in out
        assert ";" not in out.split("sequenceDiagram", 1)[1]
        assert "\n\n" not in out.split(": ", 1)[1].split("\n")[0]

    def test_is_deterministic(self):
        interactions = [
            {"from": "a", "to": "b", "label": "b"},
            {"from": "b", "to": "c", "label": "c"},
        ]
        assert sequence_diagram(interactions) == sequence_diagram(interactions)


class TestFlowchart:
    def test_renders_nodes_and_edges(self):
        out = flowchart(["a", "b"], [("a", "b")])
        assert out.startswith("```mermaid\nflowchart TD")
        assert '    n0["a"]' in out
        assert '    n1["b"]' in out
        assert "    n0 --> n1" in out

    def test_dedupes_nodes_and_drops_unknown_edges(self):
        out = flowchart(["a", "a", "b"], [("a", "b"), ("a", "missing")])
        assert out.count('n0["a"]') == 1
        assert "n0 --> n1" in out
        # edge to an undeclared node is dropped
        assert out.count("-->") == 1

    def test_custom_direction(self):
        assert "flowchart LR" in flowchart(["a"], [], direction="LR")

    def test_node_links_emit_click_directives(self):
        out = flowchart(
            ["a/b.py", "c.py"],
            [("a/b.py", "c.py")],
            links={"a/b.py": "modules/b.md", "c.py": "modules/c.md"},
        )
        assert '    click n0 "modules/b.md"' in out
        assert '    click n1 "modules/c.md"' in out

    def test_links_to_unknown_nodes_are_ignored(self):
        out = flowchart(["a"], [], links={"a": "modules/a.md", "ghost": "x.md"})
        assert out.count("click") == 1

    def test_highlight_edges_use_thick_arrow(self):
        out = flowchart(
            ["a", "b", "c"],
            [("a", "b"), ("b", "c")],
            highlight_edges={("a", "b")},
        )
        assert "    n0 ==> n1" in out  # highlighted (cyclic)
        assert "    n1 --> n2" in out  # normal

    def test_href_quotes_are_stripped(self):
        out = flowchart(["a"], [], links={"a": 'modules/"a".md'})
        assert '    click n0 "modules/a.md"' in out

    def test_extra_params_default_to_prior_behavior(self):
        assert flowchart(["a", "b"], [("a", "b")]) == flowchart(
            ["a", "b"], [("a", "b")], links=None, highlight_edges=None
        )

    def test_bounded_style_applies_direction_classes_and_colors(self):
        out = flowchart(
            ["api", "database"],
            [("api", "database")],
            style={
                "direction": "LR",
                "node_classes": {"api": "entry", "database": "store"},
                "category_colors": {"entry": "#0f0", "store": "#112233"},
            },
        )

        assert out.startswith("```mermaid\nflowchart LR")
        assert "    class n0 entry" in out
        assert "    class n1 store" in out
        assert "    classDef entry fill:#0f0,stroke:#0f0" in out
        assert "    classDef store fill:#112233,stroke:#112233" in out

    def test_bounded_style_rejects_unsafe_mermaid_fragments(self):
        out = flowchart(
            ["api; raw"],
            [],
            links={"api; raw": 'modules/"api".md'},
            style={
                "direction": "LR\nclassDef injected fill:#fff",
                "node_classes": {"api; raw": "entry; click x"},
                "category_colors": {
                    "entry; click x": "#fff",
                    "raw": "red; markdown",
                },
                "markdown": "```markdown\n# injected",
            },
        )

        assert out.startswith("```mermaid\nflowchart TD")
        assert '    n0["api raw"]' in out
        assert '    click n0 "modules/api.md"' in out
        assert "class n0" not in out
        assert "classDef" not in out
        assert "injected" not in out
        assert "markdown" not in out


class TestDataFlowDiagram:
    def test_renders_labeled_lr_diagram_with_links_and_styled_boundaries(self):
        data_flow = {
            "steps": [
                {"index": 1, "symbol": "run", "file": "pkg/api.py", "kind": "entry"},
                {
                    "index": 2,
                    "symbol": "helper",
                    "file": "pkg/helper.py",
                    "kind": "internal",
                },
                {
                    "index": 3,
                    "symbol": "helper",
                    "file": "pkg/helper.py",
                    "kind": "internal",
                },
                {"index": 4, "symbol": "publish", "file": None, "kind": "unresolved"},
            ],
            "transfers": [
                {
                    "from_step": 1,
                    "to_step": 2,
                    "call": "helper('first')",
                    "kind": "internal",
                },
                {
                    "from_step": 1,
                    "to_step": 3,
                    "call": "helper('second')",
                    "kind": "internal",
                },
                {
                    "from_step": 1,
                    "to_step": 4,
                    "call": "client.publish(result)",
                    "kind": "unresolved",
                },
            ],
            "boundaries": [
                {
                    "step": "run",
                    "step_index": 1,
                    "kind": "filesystem_write",
                    "target": "path.write_text",
                    "line": 5,
                }
            ],
        }

        out = data_flow_diagram(
            data_flow,
            {"pkg/api.py": "api", "pkg/helper.py": "helper"},
        )

        assert out.startswith("```mermaid\nflowchart LR")
        assert 's1["1. run"]' in out
        assert 's2["2. helper"]' in out
        assert 's3["3. helper"]' in out
        assert "s1 -->|helper first| s2" in out
        assert "s1 -->|helper second| s3" in out
        assert "s1 -. client.publish result .-> s4" in out
        assert 'click s1 "../modules/api.md"' in out
        assert 'click s2 "../modules/helper.md"' in out
        assert 'click s3 "../modules/helper.md"' in out
        assert "filesystem_write path.write_text" in out
        assert "class b0 boundary" in out

    def test_accepts_bounded_flowchart_style(self):
        out = data_flow_diagram(
            {
                "steps": [
                    {"index": 1, "symbol": "run", "file": "pkg/api.py"},
                    {"index": 2, "symbol": "save", "file": "pkg/store.py"},
                ],
                "transfers": [
                    {
                        "from_step": 1,
                        "to_step": 2,
                        "call": "save",
                        "kind": "internal",
                    }
                ],
                "boundaries": [],
            },
            {"pkg/api.py": "api", "pkg/store.py": "store"},
            style={
                "direction": "RL",
                "node_classes": {"1. run": "entry", "2. save": "store"},
                "category_colors": {"entry": "#abc", "store": "#123456"},
            },
        )

        assert out.startswith("```mermaid\nflowchart RL")
        assert "    class s1 entry" in out
        assert "    class s2 store" in out
        assert "    classDef entry fill:#abc,stroke:#abc" in out


def _write_diagram_style_plugin(root, *, body):
    plugin_dir = root / "vendor" / "diagram-style-plugin"
    plugin_dir.mkdir(parents=True)
    module_name = "styles_" + "_".join(root.parts[-3:])
    module_name = "".join(
        ch if ch.isalnum() or ch == "_" else "_" for ch in module_name
    )
    (plugin_dir / plugins.MANIFEST_FILENAME).write_text(
        json.dumps(
            {
                "id": "diagram-style-plugin",
                "version": "0.1.0",
                "llm_wiki_version": "*",
                "components": [
                    {
                        "type": "diagram_style",
                        "id": "brand",
                        "entry_point": f"{module_name}:style",
                    }
                ],
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    (plugin_dir / f"{module_name}.py").write_text(
        textwrap.dedent(body), encoding="utf-8"
    )
    plugins.install_plugin(str(plugin_dir), root=root, yes=True)


class TestResolveDiagramStyle:
    def test_merges_installed_plugin_styles_deterministically(self, tmp_path):
        _write_diagram_style_plugin(
            tmp_path,
            body="""
            def style(context):
                assert context["surface"] == "relationships"
                return {
                    "direction": "BT",
                    "node_classes": {"User (models.py)": "entity"},
                    "category_colors": {"entity": "#123456"},
                }
            """,
        )

        style = resolve_diagram_style({"surface": "relationships"}, root=tmp_path)

        assert style == {
            "direction": "BT",
            "node_classes": {"User (models.py)": "entity"},
            "category_colors": {"entity": "#123456"},
        }

    def test_invalid_plugin_style_falls_back_to_defaults(self, tmp_path):
        _write_diagram_style_plugin(
            tmp_path,
            body="""
            def style(context):
                return {
                    "direction": "LR\\nclassDef injected fill:#fff",
                    "node_classes": {"api": "entry; click n0"},
                    "category_colors": {"entry": "red"},
                    "markdown": "```markdown\\n# injected",
                }
            """,
        )

        style = resolve_diagram_style({"surface": "dependencies"}, root=tmp_path)

        assert style == {}

    def test_strict_invalid_plugin_style_raises(self, tmp_path):
        _write_diagram_style_plugin(
            tmp_path,
            body="""
            def style(context):
                return {"direction": "LR\\nclassDef injected fill:#fff"}
            """,
        )

        try:
            resolve_diagram_style(
                {"surface": "dependencies"},
                root=tmp_path,
                strict_plugin_errors=True,
            )
        except Exception as exc:
            assert "direction" in str(exc)
        else:
            raise AssertionError("strict invalid diagram style did not fail")
