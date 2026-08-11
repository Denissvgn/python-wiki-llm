"""Durable product restrictions for conservatively narrowed native workflows."""

import inspect
import types
from pathlib import Path

import pytest

from llm_wiki_cli import api, cli
from llm_wiki_cli.commands import bootstrap_cmd, lint_cmd
from llm_wiki_cli.services import mcp_server, skills
from llm_wiki_cli.services.knowledge_governance import GOVERNANCE_FILENAME


ROOT = Path(__file__).parents[1]


def test_native_drift_is_disabled_without_explicit_report_mode():
    parser = cli._build_parser()

    lint = parser.parse_args(["lint"])
    ci_check = parser.parse_args(["ci-check"])
    lint_report = parser.parse_args(["lint", "--knowledge-drift-report"])
    ci_report = parser.parse_args(["ci-check", "--knowledge-drift-report"])

    assert lint.knowledge_drift_report is False
    assert ci_check.knowledge_drift_report is False
    assert lint_report.knowledge_drift_report is True
    assert ci_report.knowledge_drift_report is True


def test_native_drift_has_no_blocking_gate_surface(capsys):
    parser = cli._build_parser()

    for command in ("lint", "ci-check"):
        with pytest.raises(SystemExit):
            parser.parse_args([command, "--knowledge-drift-gate"])
        capsys.readouterr()

    assert "knowledge_drift_gate" not in inspect.signature(
        lint_cmd.build_report
    ).parameters
    assert "knowledge_drift_gate" not in inspect.signature(
        mcp_server.McpWikiService.check_wiki
    ).parameters


def test_governance_does_not_promote_generic_consumers():
    native_knowledge = (ROOT / "docs" / "native-knowledge.md").read_text(
        encoding="utf-8"
    )
    normalized = " ".join(native_knowledge.split())

    assert "does not promote it into downstream integrations" in normalized
    assert "generic wiki/artifact reader" in normalized
    assert "separately demonstrate" in normalized


def test_bootstrap_and_read_consumers_do_not_initialize_governance(
    tmp_path,
    monkeypatch,
    capsys,
):
    source = tmp_path / "app.py"
    source.write_text("class User:\n    pass\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    bootstrap_cmd.run(
        types.SimpleNamespace(
            src_dir=".",
            wiki_dir="docs/llm_wiki",
            overwrite=False,
            depth="full",
            skip_workflows=True,
        )
    )
    capsys.readouterr()
    wiki = tmp_path / "docs" / "llm_wiki"
    governance = wiki / GOVERNANCE_FILENAME
    before = {
        path.relative_to(wiki).as_posix(): path.read_bytes()
        for path in wiki.rglob("*")
        if path.is_file()
    }

    api_result = api.get_concept(
        "llm-wiki://entities/User",
        src_dir=".",
        wiki_dir="docs/llm_wiki",
    )
    mcp_result = mcp_server.McpWikiService(
        src_dir=".",
        wiki_dir="docs/llm_wiki",
    ).get_concept("llm-wiki://entities/User")

    after = {
        path.relative_to(wiki).as_posix(): path.read_bytes()
        for path in wiki.rglob("*")
        if path.is_file()
    }
    assert api_result["found"] is True
    assert mcp_result["found"] is True
    assert not governance.exists()
    assert after == before


def test_onboarding_skill_disclaims_human_outcomes_and_runtime_assurance():
    skill_dir = (
        ROOT
        / "src"
        / "llm_wiki_cli"
        / "skills"
        / "onboarding-guide"
    )
    skill = (skill_dir / "SKILL.md").read_text(encoding="utf-8")
    reference = (skill_dir / "reference.md").read_text(encoding="utf-8")
    combined = f"{skill}\n{reference}"
    normalized = " ".join(combined.split())

    assert "not evidence that unfamiliar maintainers" in normalized
    assert "Never report an agent-authored guide" in normalized
    assert "does not prove a deployed service" in normalized
    assert "guides/<persona>-navigation.md" in combined
    assert "# <Persona> navigation guide" in combined
    assert "docs(wiki): add navigation guides" in combined
    assert skills.SKILL_DEPENDENCIES["onboarding-guide"] == (
        skills.REFERENCE_SKILL_ID,
    )
    for root in (".claude/skills", ".llm-wiki/skills"):
        assert f"{root}/wiki-reference/references/repository-handoff.md" in skill
    handoff = (
        skills.BUNDLED_SKILLS_ROOT
        / skills.REFERENCE_SKILL_ID
        / "references/repository-handoff.md"
    ).read_text(encoding="utf-8")
    assert "conditionally eligible (exit 1)" in handoff
    assert "applicable local rules authorize a separate wiki commit" in handoff
    assert "guides/<persona>-onboarding.md" not in combined
    assert "docs(wiki): add onboarding guides" not in combined
