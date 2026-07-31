"""Guard the documented native-knowledge consumer decision rules."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _section(text: str, heading: str) -> str:
    return text.split(heading, 1)[1].split("\n## ", 1)[0]


def test_expected_semantics_section_matches_consumer_contracts() -> None:
    text = (ROOT / "docs" / "native-knowledge.md").read_text(encoding="utf-8")
    heading = "## Semantics you should expect"

    assert text.count(heading) == 1
    section = _section(text, heading)
    normalized = " ".join(section.split())

    assert "Branch on `freshness_evaluated`" in normalized
    assert "`live_comparison_performed`" in normalized
    assert "`live-evaluation-not-performed`" in normalized
    assert "`freshness-not-modeled`" in normalized
    assert "Infrastructure is not unconditionally unknown" in normalized
    assert "`recorded-basis-unavailable`" in normalized
    assert "`missing-source-has-no-reliable-recorded-basis`" in normalized
    assert "Treat `expired` as advisory-invalid" in normalized
    assert "read-only surface fallback" in normalized
    assert "`llm-wiki sync`" in normalized
    assert "--allow-governance-recovery" not in section


def test_public_read_and_export_examples_disclose_aggregate_freshness() -> None:
    text = (ROOT / "docs" / "native-knowledge.md").read_text(encoding="utf-8")
    exporter = _section(text, "## Safe derived projections")
    context = _section(text, "## Context filters and ranking")
    queries = _section(text, "## Python API")
    mcp = _section(text, "## MCP tools")

    assert 'freshness: "unevaluated (snapshot-only read)"' in exporter
    assert 'knowledge_freshness: "not-evaluated"' in exporter
    assert '"freshness": "evaluated (6 concepts)"' in context
    assert "`live_comparison_performed`" in context
    assert '"freshness": "evaluated (6 concepts)"' in queries
    assert "`live_comparison_performed`" in queries
    assert '"freshness": "unevaluated (snapshot-only read)"' in mcp
    assert "`concepts_evaluated: 0`" in mcp
    assert "`freshness_counts` null" in mcp
