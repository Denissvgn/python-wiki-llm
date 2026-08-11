"""Guard the documented native-knowledge consumer decision rules."""

import re
import shlex
from pathlib import Path

from llm_wiki_cli import cli
from llm_wiki_cli.services.context_knowledge_contract import (
    context_knowledge_contract,
)
from llm_wiki_cli.services.contracts import (
    CONTEXT_KNOWLEDGE_PROTOCOL_VERSION,
    CONTEXT_PROTOCOL_VERSION,
    QUALIFIED_CONTEXT_PACKET_KNOWLEDGE_SCHEMA_VERSION,
    QUALIFIED_CONTEXT_PACKET_SCHEMA_VERSION,
)
from tests.skill_contract_harness import extract_cli_examples, parse_cli_example


ROOT = Path(__file__).resolve().parents[1]
PUBLIC_CONTEXT_DOCS = {
    ROOT / "docs" / "native-knowledge.md",
    ROOT / "docs" / "native-knowledge-use-cases.md",
    ROOT / "docs" / "qualified-context-packets.md",
}


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


def test_native_context_docs_match_the_active_mode_and_version_contract() -> None:
    contract = context_knowledge_contract()
    native = (ROOT / "docs" / "native-knowledge.md").read_text(encoding="utf-8")
    packet = (ROOT / "docs" / "qualified-context-packets.md").read_text(
        encoding="utf-8"
    )
    combined = f"{native}\n{packet}"

    assert "normal bounded evidence plane" in native
    assert all(f"`{mode}`" in combined for mode in contract["modes"])
    assert contract["interfaces"]["cli"]["name"] in native
    assert contract["interfaces"]["python-api"]["name"] in combined
    assert CONTEXT_PROTOCOL_VERSION in packet
    assert CONTEXT_KNOWLEDGE_PROTOCOL_VERSION in packet
    assert QUALIFIED_CONTEXT_PACKET_SCHEMA_VERSION in packet
    assert QUALIFIED_CONTEXT_PACKET_KNOWLEDGE_SCHEMA_VERSION in packet

    output = contract["output_fields"]["knowledge"]
    assert all(f"`{field}`" in native for field in output["required"])
    assert all(f"`{name}`" in native for name in output["bounds_collections"])
    assert all(f"`{field}`" in native for field in output["bounds_required"])

    preference = contract["prefer_fresh"]
    assert "`prefer_fresh` defaults to false" in native
    assert preference["controls_knowledge_inclusion"] is False
    assert preference["controls"] == (
        "current-first-ranking-within-an-existing-relevance-tier"
    )
    nonapplication_reasons = {
        row["reason"]
        for row in preference["disclosure_matrix"]
        if row.get("applied") is False
    }
    assert all(f"`{reason}`" in native for reason in nonapplication_reasons)

    required_error = contract["output_fields"]["required_error"]
    assert f"`{required_error['code']}`" in combined
    assert "Omitted/default behavior is not deprecated in this release" in packet
    assert "release must first announce the deprecation" in packet


def test_every_complete_command_in_native_context_docs_parses() -> None:
    examples = tuple(
        example
        for example in extract_cli_examples(ROOT / "docs")
        if example.location.path in PUBLIC_CONTEXT_DOCS
    )

    assert {example.location.path for example in examples} == PUBLIC_CONTEXT_DOCS
    assert len(examples) >= 18
    parsed = tuple((example, parse_cli_example(example)) for example in examples)
    context_modes = {
        args.knowledge_mode
        for _, args in parsed
        if getattr(args, "command", None) == "context"
    }
    assert context_modes == {"auto"}

    inline_commands = tuple(
        command
        for path in sorted(PUBLIC_CONTEXT_DOCS)
        for command in re.findall(
            r"`(llm-wiki [^`\n]+)`",
            path.read_text(encoding="utf-8"),
        )
    )
    assert len(inline_commands) >= 8
    parser = cli._build_parser()
    for command in inline_commands:
        parser.parse_args(shlex.split(command)[1:])


def test_native_context_docs_do_not_publish_internal_work_vocabulary() -> None:
    prohibited = re.compile(
        r"\b(?:backlog|fixture|milestone|phase|phases|pytest|test|tests)\b",
        flags=re.IGNORECASE,
    )

    for path in sorted(PUBLIC_CONTEXT_DOCS):
        assert prohibited.search(path.read_text(encoding="utf-8")) is None
