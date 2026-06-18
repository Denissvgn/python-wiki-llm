"""Tests for services/diagrams.py — pure Mermaid renderers."""
from __future__ import annotations

from llm_wiki_cli.services.diagrams import flowchart, sequence_diagram


class TestSequenceDiagram:
    def test_renders_fenced_mermaid_block(self):
        out = sequence_diagram([{"from": "a", "to": "b", "label": "b"}])
        assert out.startswith("```mermaid\nsequenceDiagram")
        assert out.endswith("```")

    def test_declares_participants_in_first_seen_order(self):
        out = sequence_diagram([
            {"from": "main", "to": "parse", "label": "parse"},
            {"from": "main", "to": "run", "label": "run"},
        ])
        lines = out.splitlines()
        assert "    participant p0 as main" in lines
        assert "    participant p1 as parse" in lines
        assert "    participant p2 as run" in lines
        assert "    p0->>p1: parse" in lines
        assert "    p0->>p2: run" in lines

    def test_dashed_arrow_for_boundary_calls(self):
        out = sequence_diagram([{"from": "a", "to": "getcwd", "label": "getcwd", "dashed": True}])
        assert "-->>" in out
        assert "->>" in out  # the dashed arrow still contains the base arrow token

    def test_labels_are_sanitized(self):
        out = sequence_diagram([{"from": "a", "to": "b", "label": "do(x); y\nz"}])
        assert "do x y z" in out
        assert ";" not in out.split("sequenceDiagram", 1)[1]
        assert "\n\n" not in out.split(": ", 1)[1].split("\n")[0]

    def test_is_deterministic(self):
        interactions = [{"from": "a", "to": "b", "label": "b"}, {"from": "b", "to": "c", "label": "c"}]
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
