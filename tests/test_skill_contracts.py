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
    McpToolExample,
    SkillContractError,
    assert_cli_selections_equal,
    assert_markers_in_order,
    extract_cli_examples,
    extract_context_request_examples,
    extract_fenced_cli_examples,
    extract_inline_cli_examples,
    extract_mcp_tool_examples,
    extract_query_graph_examples,
    output_value,
    parse_cli_example,
    validate_context_example,
    validate_mcp_tool_example,
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


def test_query_graph_harness_extracts_continuation_line_payloads(tmp_path):
    skill = tmp_path / "contract-skill"
    skill.mkdir()
    path = skill / "SKILL.md"
    path.write_text(
        "\n".join(
            [
                "# Contract",
                "",
                "Use MCP `query_graph` with",
                '`{"type": "dependency_neighborhood", "value": "<file>",'
                ' "limit": 20}` —',
                "the context protocol does not expose it.",
                "",
                'Same-line form: `query_graph {"type": "callers",'
                ' "value": "<symbol>", "limit": 20}`.',
                "",
            ]
        ),
        encoding="utf-8",
    )

    examples = extract_query_graph_examples(path)

    assert [
        (example.location.line, validate_query_graph_example(example))
        for example in examples
    ] == [
        (4, ("dependency_neighborhood", "src/contract.py", 20)),
        (7, ("callers", "contract_symbol", 20)),
    ]


def test_context_harness_extracts_shell_quoted_requests(tmp_path):
    skill = tmp_path / "contract-skill"
    skill.mkdir()
    path = skill / "SKILL.md"
    path.write_text(
        "\n".join(
            [
                "# Contract",
                "",
                "```bash",
                "echo '{\"protocol\":\"llm-wiki-context/v1\","
                "\"budget_tokens\":16000,"
                "\"filters\":{\"symbol\":\"<symbol>\"}}' \\",
                "  | llm-wiki context --src-dir . --request - --read-only",
                "```",
                "",
            ]
        ),
        encoding="utf-8",
    )

    examples = extract_context_request_examples(tmp_path)

    assert len(examples) == 1
    assert examples[0].location.line == 4
    validated = validate_context_example(examples[0])
    assert validated["budget_tokens"] == 16000
    assert validated["filters"] == {"symbol": "contract_symbol"}


def test_context_harness_reports_invalid_shell_quoted_request(tmp_path):
    skill = tmp_path / "invalid-shell-context"
    skill.mkdir()
    path = skill / "SKILL.md"
    path.write_text(
        "echo '{\"protocol\":\"llm-wiki-context/v1\",\"unknown\":true}'\n",
        encoding="utf-8",
    )

    examples = extract_context_request_examples(tmp_path)

    assert len(examples) == 1
    with pytest.raises(
        SkillContractError,
        match=r"invalid-shell-context .*Unknown request field: unknown",
    ):
        validate_context_example(examples[0])


def test_named_mcp_tool_harness_accepts_valid_and_identifies_invalid_fixture():
    valid = McpToolExample(
        _location(),
        "traverse_typed_graph",
        {
            "locator_or_exact_route": "llm-wiki://entities/User",
            "direction": "incoming",
            "kinds": ["calls"],
            "origins": ["extracted"],
            "resolutions": ["resolved", "unresolved"],
            "include_evidence": False,
            "limit": 20,
        },
    )
    validated = validate_mcp_tool_example(valid)
    assert validated == {
        "method": "traverse_typed_graph",
        "value": "llm-wiki://entities/User",
        "limit": 20,
        "options": {
            "direction": "incoming",
            "kinds": ["calls"],
            "origins": ["extracted"],
            "resolutions": ["resolved", "unresolved"],
            "include_evidence": False,
        },
    }

    invalid = McpToolExample(
        _location("invalid-native-mcp"),
        "traverse_typed_graph",
        {
            "locator_or_exact_route": "llm-wiki://entities/User",
            "origins": ["guessed"],
        },
    )
    with pytest.raises(
        SkillContractError,
        match=r"invalid-native-mcp .*unsupported origin",
    ):
        validate_mcp_tool_example(invalid)


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


def test_inline_cli_harness_discovers_only_complete_bullets_and_command_tables(
    tmp_path,
):
    skill = tmp_path / "contract-skill"
    skill.mkdir()
    path = skill / "SKILL.md"
    path.write_text(
        "\n".join(
            [
                "# Contract",
                "",
                "- `llm-wiki lint --strict --src-dir . --wiki-dir docs/llm_wiki`",
                "- Use `llm-wiki sync --src-dir .` after editing.",
                "- `llm-wiki ci-check ...`",
                "",
                "| Stage | Command |",
                "| --- | --- |",
                "| Valid | `llm-wiki context --budget 8000 --focus all --read-only` |",
                "| External | `mkdocs build --strict` |",
                "",
            ]
        ),
        encoding="utf-8",
    )

    examples = extract_inline_cli_examples(tmp_path)

    assert [(example.location.line, example.command) for example in examples] == [
        (
            3,
            "llm-wiki lint --strict --src-dir . --wiki-dir docs/llm_wiki",
        ),
        (
            9,
            "llm-wiki context --budget 8000 --focus all --read-only",
        ),
    ]
    for example in examples:
        parse_cli_example(example)


def test_inline_cli_harness_reports_invalid_table_example_location(tmp_path):
    skill = tmp_path / "invalid-inline"
    skill.mkdir()
    path = skill / "reference.md"
    path.write_text(
        "| Stage | Command |\n"
        "| --- | --- |\n"
        "| Broken | `llm-wiki extract --cache-dir cache` |\n",
        encoding="utf-8",
    )
    example = extract_inline_cli_examples(tmp_path)[0]

    with pytest.raises(
        SkillContractError,
        match=r"invalid-inline .*reference\.md:3.*unrecognized arguments",
    ):
        parse_cli_example(example)


def test_inline_cli_harness_reports_invalid_bullet_example_location(tmp_path):
    skill = tmp_path / "invalid-bullet"
    skill.mkdir()
    path = skill / "SKILL.md"
    path.write_text(
        "# Invalid bullet\n\n"
        "- `llm-wiki extract --cache-dir cache`\n",
        encoding="utf-8",
    )
    example = extract_inline_cli_examples(tmp_path)[0]

    with pytest.raises(
        SkillContractError,
        match=r"invalid-bullet .*SKILL\.md:3.*unrecognized arguments",
    ):
        parse_cli_example(example)


def test_fenced_cli_harness_reports_invalid_example_location(tmp_path):
    skill = tmp_path / "invalid-fence"
    skill.mkdir()
    path = skill / "reference.md"
    path.write_text(
        "# Invalid fence\n\n"
        "```bash\n"
        "llm-wiki extract --cache-dir cache\n"
        "```\n",
        encoding="utf-8",
    )
    example = extract_fenced_cli_examples(tmp_path)[0]

    with pytest.raises(
        SkillContractError,
        match=r"invalid-fence .*reference\.md:4.*unrecognized arguments",
    ):
        parse_cli_example(example)


def test_fenced_cli_harness_skips_explicit_command_fragments(tmp_path):
    skill = tmp_path / "fenced-fragments"
    skill.mkdir()
    path = skill / "SKILL.md"
    path.write_text(
        "```bash\n"
        "llm-wiki lint --strict --src-dir . --wiki-dir docs/llm_wiki\n"
        "llm-wiki sync ...\n"
        "llm-wiki extract …\n"
        "llm-wiki extract --src-dir https://example.invalid/.../source\n"
        "```\n",
        encoding="utf-8",
    )

    examples = extract_fenced_cli_examples(tmp_path)

    assert [example.command for example in examples] == [
        "llm-wiki lint --strict --src-dir . --wiki-dir docs/llm_wiki",
        "llm-wiki extract --src-dir https://example.invalid/.../source",
    ]


def test_all_complete_documented_cli_examples_parse_with_real_parser():
    examples = extract_cli_examples(skills.BUNDLED_SKILLS_ROOT)
    assert examples
    for example in examples:
        parse_cli_example(example)


def test_inline_command_inventory_covers_known_skill_matrices():
    examples = extract_inline_cli_examples(skills.BUNDLED_SKILLS_ROOT)
    commands_by_skill: dict[str, set[str]] = {}
    for example in examples:
        commands_by_skill.setdefault(example.location.skill_id, set()).add(
            example.command
        )

    assert any(
        command.startswith("llm-wiki site export ")
        for command in commands_by_skill["user-docs-author"]
    )
    assert {
        "llm-wiki lint --strict --profile --src-dir . --wiki-dir docs/llm_wiki",
        "llm-wiki ci-check --src-dir . --wiki-dir docs/llm_wiki --format json",
    } <= commands_by_skill["dep-audit"]


def test_wiki_reference_native_command_examples_cover_public_actions_and_modes():
    skill_root = skills.BUNDLED_SKILLS_ROOT / "wiki-reference"
    parsed = [
        (example, parse_cli_example(example))
        for example in extract_fenced_cli_examples(skill_root)
    ]
    knowledge_actions = {
        args.knowledge_action
        for _example, args in parsed
        if getattr(args, "command", None) == "knowledge"
    }
    assert knowledge_actions >= {
        "init",
        "status",
        "move",
        "alias",
        "lifecycle",
        "deprecate",
        "supersede",
        "review",
        "verify",
    }

    enriched = [
        args
        for _example, args in parsed
        if getattr(args, "command", None) in {"site", "obsidian"}
        and getattr(args, "knowledge_metadata", None) == "summary"
    ]
    assert {
        (
            args.command,
            getattr(args, "site_action", None)
            or getattr(args, "obsidian_action", None),
            args.knowledge_profile,
        )
        for args in enriched
    } >= {
        ("site", "export", "public-portable"),
        ("site", "check", "public-portable"),
        ("obsidian", "export", "public-portable"),
        ("obsidian", "check", "public-portable"),
    }


def test_enumerated_inline_bootstrap_context_example_parses_with_real_parser():
    path = skills.BUNDLED_SKILLS_ROOT / "wiki-bootstrap" / "SKILL.md"
    command = (
        "llm-wiki context --budget 12000 --focus all --format json "
        "--source-selection <profile>"
    )
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
    assert args.source_selection == "config/contract-profile.json"


def test_wiki_bootstrap_carries_active_selection_through_source_recipes():
    skill_root = skills.BUNDLED_SKILLS_ROOT / "wiki-bootstrap"
    documented = "\n".join(
        path.read_text(encoding="utf-8")
        for path in (skill_root / "SKILL.md", skill_root / "reference.md")
    )

    assert "never replace a configured non-default profile" in documented
    for command in (
        "prepare-extractors",
        "bootstrap",
        "sync",
        "lint",
        "ci-check",
        "team check",
        "context",
    ):
        assert any(
            command in line and "--source-selection <profile>" in line
            for line in documented.splitlines()
        ), command


def test_all_fenced_context_requests_validate_with_real_protocol_parser():
    examples = extract_context_request_examples(skills.BUNDLED_SKILLS_ROOT)
    assert {example.location.skill_id for example in examples} >= {
        "impact-analysis",
        "wiki-reference",
    }
    for example in examples:
        validate_context_example(example)


def test_native_mcp_examples_validate_through_public_tool_methods():
    examples_by_skill: dict[str, tuple[McpToolExample, ...]] = {}
    for skill_id in ("wiki-reference", "impact-analysis"):
        skill_dir = skills.BUNDLED_SKILLS_ROOT / skill_id
        examples_by_skill[skill_id] = tuple(
            example
            for path in (skill_dir / "SKILL.md", skill_dir / "reference.md")
            for example in extract_mcp_tool_examples(path)
        )

    assert {example.tool_name for example in examples_by_skill["wiki-reference"]} == {
        "get_concept",
        "list_concept_sections",
        "related_concepts",
        "traverse_typed_graph",
        "explain_evidence",
    }
    assert {example.tool_name for example in examples_by_skill["impact-analysis"]} == {
        "get_concept",
        "traverse_typed_graph",
        "explain_evidence",
    }

    for examples in examples_by_skill.values():
        for example in examples:
            result = validate_mcp_tool_example(example)
            assert result["method"] == example.tool_name


def test_impact_analysis_mcp_examples_validate_and_dispatch(monkeypatch, tmp_path):
    skill_dir = skills.BUNDLED_SKILLS_ROOT / "impact-analysis"
    examples = tuple(
        example
        for path in (skill_dir / "SKILL.md", skill_dir / "reference.md")
        for example in extract_query_graph_examples(path)
    )
    assert examples
    assert {example.location.path.name for example in examples} == {
        "SKILL.md",
        "reference.md",
    }
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
    source_root = tmp_path / "source"
    wiki_root = tmp_path / "wiki"
    source_root.mkdir()
    wiki_root.mkdir()
    service = mcp_server.McpWikiService(
        src_dir=source_root,
        wiki_dir=wiki_root,
    )

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


def test_independent_source_reading_skills_preserve_active_selection():
    required_fragments = {
        "attack-surface": (
            "prepare-extractors --src-dir . --cache-dir <helper-cache>",
            "extract --src-dir . --deep --read-only",
        ),
        "dep-vuln-triage": (
            "prepare-extractors --src-dir . --source-selection <profile>",
            "extract --src-dir . --deep --read-only --source-selection <profile>",
        ),
        "impact-analysis": (
            "context --src-dir . --wiki-dir docs/llm_wiki",
        ),
        "dep-audit": (
            "lint --strict --profile --src-dir .",
            "ci-check --src-dir .",
        ),
    }
    for skill_id, fragments in required_fragments.items():
        text = (
            skills.BUNDLED_SKILLS_ROOT / skill_id / "SKILL.md"
        ).read_text(encoding="utf-8")
        normalized = " ".join(text.split())
        assert "--source-selection <profile>" in normalized
        assert "omit the whole option only when no profile exists" in normalized
        for fragment in fragments:
            assert fragment in normalized


def test_known_invalid_skill_contracts_are_absent_and_cache_handoff_is_explicit():
    skill_text = "\n".join(
        path.read_text(encoding="utf-8")
        for path in sorted(skills.BUNDLED_SKILLS_ROOT.rglob("*.md"))
    )

    for invalid in (
        '"query_type"',
        "sync --output-format json",
        "bootstrap --force",
        "bootstrap --overwrite",
        "dependencies.metrics",
        "attack-surfa ce",
        "ci-check --cache-dir",
        "context --budget 8000-12000",
    ):
        assert invalid not in skill_text
    assert "prepare-extractors --cache-dir <helper-cache>" in skill_text
    assert "--helper-cache-dir <same-helper-cache>" in skill_text
