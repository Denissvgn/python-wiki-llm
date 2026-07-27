"""Executable contracts for command and payload examples in bundled skills."""

from __future__ import annotations

from pathlib import Path

import pytest

from llm_wiki_cli.commands.bootstrap_cmd import execute_bootstrap
from llm_wiki_cli.services import mcp_server, skills
from llm_wiki_cli.services.bootstrap_service import BootstrapRequest
from tests.skill_contract_harness import (
    CliExample,
    ExampleLocation,
    JsonExample,
    SkillContractError,
    assert_cli_selections_equal,
    assert_markers_in_order,
    extract_context_request_examples,
    extract_fenced_cli_examples,
    extract_query_graph_examples,
    output_value,
    parse_cli_example,
    validate_context_example,
    validate_query_graph_example,
)


def _location(skill_id: str = "contract-fixture") -> ExampleLocation:
    return ExampleLocation(skill_id, Path("skills/contract-fixture/SKILL.md"), 7)


def test_cli_harness_accepts_valid_and_identifies_invalid_fixture():
    valid = CliExample(
        _location(),
        "llm-wiki context --budget 8000 --focus changed --read-only",
    )
    assert parse_cli_example(valid).read_only is True

    invalid = CliExample(
        _location("invalid-cli"),
        "llm-wiki context --budget 8000 --unsupported-flag",
    )
    with pytest.raises(
        SkillContractError,
        match=r"invalid-cli .*SKILL\.md:7.*unrecognized arguments",
    ):
        parse_cli_example(invalid)

    missing_required = CliExample(
        _location("missing-cli-argument"),
        "llm-wiki site export --format mkdocs",
    )
    with pytest.raises(
        SkillContractError,
        match=r"missing-cli-argument .*required: --out-dir",
    ):
        parse_cli_example(missing_required)


def test_mcp_harness_accepts_valid_and_identifies_invalid_fixture():
    valid = JsonExample(
        _location(),
        {"type": "callers", "value": "run", "limit": 20},
    )
    assert validate_query_graph_example(valid) == ("callers", "run", 20)

    invalid = JsonExample(
        _location("invalid-mcp"),
        {"type": "callers", "value": "run", "query_type": "callers"},
    )
    with pytest.raises(
        SkillContractError,
        match=r"invalid-mcp .*Unknown query field: query_type",
    ):
        validate_query_graph_example(invalid)


def test_context_harness_accepts_valid_and_identifies_invalid_fixture():
    valid = JsonExample(
        _location(),
        {
            "protocol": "llm-wiki-context/v1",
            "budget_tokens": 8000,
            "filters": {"symbol": "run"},
        },
    )
    assert validate_context_example(valid)["filters"] == {"symbol": "run"}

    invalid = JsonExample(
        _location("invalid-context"),
        {
            "protocol": "llm-wiki-context/v1",
            "budget_tokens": 8000,
            "unknown": True,
        },
    )
    with pytest.raises(
        SkillContractError,
        match=r"invalid-context .*Unknown request field: unknown",
    ):
        validate_context_example(invalid)


def test_output_path_harness_accepts_valid_and_identifies_invalid_fixture():
    payload = {"dependency_evidence": {"most_depended_on": ["src/core.py"]}}
    assert output_value(
        payload,
        "dependency_evidence.most_depended_on",
        _location(),
    ) == ["src/core.py"]

    with pytest.raises(
        SkillContractError,
        match=r"invalid-output .*dependency_evidence\.metrics\.most_depended_on",
    ):
        output_value(
            payload,
            "dependency_evidence.metrics.most_depended_on",
            _location("invalid-output"),
        )


def test_order_harness_accepts_valid_and_identifies_invalid_fixture():
    assert_markers_in_order(
        "preview, edit, re-anchor, strict validation",
        ("preview", "edit", "re-anchor", "strict validation"),
        _location(),
    )

    with pytest.raises(
        SkillContractError,
        match=r"invalid-order .*missing or out-of-order marker 're-anchor'",
    ):
        assert_markers_in_order(
            "edit, strict validation",
            ("edit", "re-anchor", "strict validation"),
            _location("invalid-order"),
        )


def test_selection_harness_accepts_valid_and_identifies_invalid_fixture():
    hosted_export = CliExample(
        _location(),
        "llm-wiki site export --out-dir site --format mkdocs "
        "--profile user --site-name project",
    )
    hosted_check = CliExample(
        _location(),
        "llm-wiki site check --out-dir site --profile user --site-name project",
    )
    assert_cli_selections_equal(
        (hosted_export, hosted_check),
        ("profile", "site_name"),
    )

    wrong_check = CliExample(
        _location("invalid-selection"),
        "llm-wiki site check --out-dir site --profile reference",
    )
    with pytest.raises(
        SkillContractError,
        match=r"invalid-selection .*selections .* do not match",
    ):
        assert_cli_selections_equal(
            (hosted_export, wrong_check),
            ("profile", "site_name"),
        )


def test_all_complete_fenced_cli_examples_parse_with_real_parser():
    examples = extract_fenced_cli_examples(skills.BUNDLED_SKILLS_ROOT)
    assert examples
    for example in examples:
        parse_cli_example(example)


def test_enumerated_inline_bootstrap_context_example_parses_with_real_parser():
    path = skills.BUNDLED_SKILLS_ROOT / "wiki-bootstrap" / "SKILL.md"
    command = "llm-wiki context --budget 12000 --focus all --format json"
    lines = path.read_text(encoding="utf-8").splitlines()
    line_number = next(
        index for index, line in enumerate(lines, 1) if command in line
    )

    args = parse_cli_example(
        CliExample(
            ExampleLocation("wiki-bootstrap", path, line_number),
            command,
        )
    )

    assert args.budget == 12000
    assert args.focus == "all"


def test_all_fenced_context_requests_validate_with_real_protocol_parser():
    examples = extract_context_request_examples(skills.BUNDLED_SKILLS_ROOT)
    assert {example.location.skill_id for example in examples} >= {
        "impact-analysis",
        "wiki-reference",
    }
    for example in examples:
        validate_context_example(example)


def test_impact_analysis_mcp_examples_validate_and_dispatch(monkeypatch):
    skill_dir = skills.BUNDLED_SKILLS_ROOT / "impact-analysis"
    examples = tuple(
        example
        for path in (skill_dir / "SKILL.md", skill_dir / "reference.md")
        for example in extract_query_graph_examples(path)
    )
    assert examples
    assert {validate_query_graph_example(example)[0] for example in examples} >= {
        "callers",
        "dependency_neighborhood",
        "flow_for_entrypoint",
        "pages_for_symbol",
    }
    for example in examples:
        assert set(example.payload) == {"type", "value", "limit"}
        assert example.payload["limit"] == 20

    dispatched: list[tuple[str, str, int]] = []

    class FixtureQueryService:
        def __init__(self, limit: int):
            self.limit = limit

        def __getattr__(self, method: str):
            def dispatch(value: str):
                dispatched.append((method, value, self.limit))
                return {"method": method, "value": value, "limit": self.limit}

            return dispatch

    monkeypatch.setattr(
        mcp_server,
        "build_documentation_query_service",
        lambda _src, *, wiki_dir, limit: FixtureQueryService(limit),
    )
    service = mcp_server.McpWikiService(src_dir=".", wiki_dir="docs/llm_wiki")

    for example in examples:
        query_type, value, limit = validate_query_graph_example(example)
        result = service.query_graph(example.payload)
        assert result == {
            "method": mcp_server._GRAPH_QUERY_METHODS[query_type],
            "value": value,
            "limit": limit,
        }

    assert len(dispatched) == len(examples)


def test_bootstrap_centrality_documentation_resolves_against_real_output(tmp_path):
    source = tmp_path / "source"
    source.mkdir()
    (source / "core.py").write_text("def run():\n    return 1\n", encoding="utf-8")
    (source / "app.py").write_text(
        "from core import run\n\nVALUE = run()\n",
        encoding="utf-8",
    )
    result = execute_bootstrap(
        BootstrapRequest(source_root=source, wiki_root=tmp_path / "wiki")
    )
    location = ExampleLocation(
        "wiki-bootstrap",
        skills.BUNDLED_SKILLS_ROOT / "wiki-bootstrap" / "SKILL.md",
        1,
    )

    centrality = output_value(
        result.summary,
        "dependency_evidence.most_depended_on",
        location,
    )

    assert centrality
    documented = "\n".join(
        (
            (skills.BUNDLED_SKILLS_ROOT / "wiki-bootstrap" / "SKILL.md").read_text(
                encoding="utf-8"
            ),
            (
                skills.BUNDLED_SKILLS_ROOT / "wiki-bootstrap" / "reference.md"
            ).read_text(encoding="utf-8"),
        )
    )
    assert "dependency_evidence.most_depended_on" in documented
    assert "dependencies.metrics" not in documented


def test_read_only_context_example_discloses_fresh_inventory_contract():
    manifest = (
        skills.BUNDLED_SKILLS_ROOT / "impact-analysis" / "SKILL.md"
    ).read_text(encoding="utf-8")
    normalized = " ".join(manifest.split())

    assert "context --src-dir . --wiki-dir docs/llm_wiki --request - --read-only" in (
        normalized
    )
    assert "performs a fresh source inventory" in normalized
    assert "does not reuse a previously persisted deep inventory" in normalized


def test_known_invalid_skill_contracts_are_absent_and_cache_handoff_is_explicit():
    skill_text = "\n".join(
        path.read_text(encoding="utf-8")
        for path in sorted(skills.BUNDLED_SKILLS_ROOT.rglob("*.md"))
    )

    for invalid in (
        '"query_type"',
        "sync --output-format json",
        "bootstrap --force",
        "dependencies.metrics",
        "attack-surfa ce",
        "ci-check --cache-dir",
        "context --budget 8000-12000",
    ):
        assert invalid not in skill_text
    assert "prepare-extractors --cache-dir <helper-cache>" in skill_text
    assert "--helper-cache-dir <same-helper-cache>" in skill_text
