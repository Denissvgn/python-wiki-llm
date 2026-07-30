"""Tests for commands/status_cmd.py"""

import json
import types

from llm_wiki_cli.commands import context_cmd, extract_cmd, status_cmd
from llm_wiki_cli.services import knowledge_consumption
from llm_wiki_cli.services.knowledge_artifacts import KNOWLEDGE_INDEX_FILENAME
from tests.knowledge_fixtures import fail_if_extraction_runs
from tests.test_knowledge_loader import _committed_state


def _make_args(**kwargs):
    return types.SimpleNamespace(**kwargs)


def _status_counts(output: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for line in output.splitlines():
        label, sep, rest = line.strip().partition(":")
        if not sep:
            continue
        value = rest.strip().split(maxsplit=1)[0] if rest.strip() else ""
        if value.isdigit():
            counts[label] = int(value)
    return counts


def _guard_live_knowledge_evaluation(monkeypatch) -> None:
    monkeypatch.setattr(
        extract_cmd,
        "build_extract_payload",
        fail_if_extraction_runs,
    )
    monkeypatch.setattr(
        extract_cmd,
        "get_inventory_result",
        fail_if_extraction_runs,
    )
    monkeypatch.setattr(
        context_cmd,
        "get_inventory_result",
        fail_if_extraction_runs,
    )
    monkeypatch.setattr(
        knowledge_consumption,
        "evaluate_knowledge_freshness",
        fail_if_extraction_runs,
    )


class TestStatusWiki:
    def test_shows_wiki_exists(self, tmp_project, capsys):
        wiki = tmp_project / "docs" / "llm_wiki"
        for d in ["entities", "modules", "workflows", "flows", "infrastructure"]:
            (wiki / d).mkdir(parents=True)
        (wiki / "index.md").write_text("# Index\n")
        (wiki / "log.md").write_text("# Log\n")
        (wiki / "entities" / "User.md").write_text("# User\n")
        (wiki / "modules" / "main.md").write_text("# main\n")
        (wiki / "workflows" / "signup.md").write_text("# signup\n")
        (wiki / "flows" / "checkout.md").write_text("# checkout\n")
        (wiki / "infrastructure" / "Dockerfile.md").write_text("# Dockerfile\n")
        (wiki / "api-contracts.md").write_text("# API contracts\n")
        (wiki / "dependencies.md").write_text("# Dependencies\n")
        (wiki / "load-order.md").write_text("# Load Order\n")

        status_cmd.run(_make_args(wiki_dir=str(wiki)))
        out = capsys.readouterr().out
        counts = _status_counts(out)

        assert "exists" in out
        assert counts["Index"] == 1
        assert counts["Log"] == 1
        assert counts["Entities"] == 1
        assert counts["Modules"] == 1
        assert counts["Workflows"] == 1
        assert counts["Flows"] == 1
        assert counts["Infrastructure"] == 1
        assert counts["API contracts"] == 1
        assert counts["Dependencies"] == 1
        assert counts["Load order"] == 1
        assert counts["Architecture pages"] == 3

    def test_counts_wiki_pages_without_materializing_globs(
        self, tmp_project, capsys, monkeypatch
    ):
        wiki = tmp_project / "docs" / "llm_wiki"
        for d in ["entities", "modules", "workflows", "flows", "infrastructure"]:
            (wiki / d).mkdir(parents=True)
        (wiki / "entities" / "User.md").write_text("# User\n")
        (wiki / "modules" / "main.md").write_text("# main\n")
        (wiki / "workflows" / "signup.md").write_text("# signup\n")
        (wiki / "flows" / "checkout.md").write_text("# checkout\n")
        (wiki / "infrastructure" / "Dockerfile.md").write_text("# Dockerfile\n")

        def fail_if_materialized(*_args, **_kwargs):
            raise AssertionError(
                "status should count glob results without list allocation"
            )

        monkeypatch.setattr(status_cmd, "list", fail_if_materialized, raising=False)

        status_cmd.run(_make_args(wiki_dir=str(wiki)))
        out = capsys.readouterr().out
        counts = _status_counts(out)

        assert counts["Entities"] == 1
        assert counts["Modules"] == 1
        assert counts["Workflows"] == 1
        assert counts["Flows"] == 1
        assert counts["Infrastructure"] == 1

    def test_missing_optional_registry_surfaces_count_as_zero(
        self, tmp_project, capsys
    ):
        wiki = tmp_project / "docs" / "llm_wiki"
        for d in ["entities", "modules", "workflows"]:
            (wiki / d).mkdir(parents=True)
        (wiki / "entities" / "User.md").write_text("# User\n")

        status_cmd.run(_make_args(wiki_dir=str(wiki)))
        out = capsys.readouterr().out
        counts = _status_counts(out)

        assert counts["Index"] == 0
        assert counts["Log"] == 0
        assert counts["Entities"] == 1
        assert counts["Modules"] == 0
        assert counts["Workflows"] == 0
        assert counts["Flows"] == 0
        assert counts["Infrastructure"] == 0
        assert counts["API contracts"] == 0
        assert counts["Dependencies"] == 0
        assert counts["Load order"] == 0
        assert counts["Architecture pages"] == 0

    def test_shows_wiki_missing(self, tmp_project, capsys):
        status_cmd.run(_make_args(wiki_dir="nonexistent"))
        out = capsys.readouterr().out
        assert "not found" in out


class TestStatusKnowledge:
    def test_ready_projection_reports_snapshot_only_aggregates(
        self,
        tmp_project,
        capsys,
        monkeypatch,
    ):
        wiki = tmp_project / "docs" / "llm_wiki"
        _committed_state(wiki)
        _guard_live_knowledge_evaluation(monkeypatch)

        status_cmd.run(_make_args(wiki_dir=str(wiki), src_dir="."))

        out = capsys.readouterr().out
        assert (
            "Knowledge:       ready (reason: all-projection-commitments-match)"
        ) in out
        assert "Concepts evaluated: 0" in out
        assert "Evidence issues: invalid=0, missing=0, unknown=1" in out
        assert "Freshness: not evaluated (snapshot-only status)" in out
        assert "llm-wiki://entities/User" not in out
        assert "sha256:" not in out

    def test_legacy_projection_reports_absent_without_live_evaluation(
        self,
        tmp_project,
        capsys,
        monkeypatch,
    ):
        wiki = tmp_project / "docs" / "llm_wiki"
        wiki.mkdir(parents=True)
        (wiki / "index.md").write_bytes(b"\xff")
        _guard_live_knowledge_evaluation(monkeypatch)

        status_cmd.run(_make_args(wiki_dir=str(wiki)))

        out = capsys.readouterr().out
        assert (
            "Knowledge:       absent (reason: knowledge-projection-not-present)"
        ) in out
        assert "Evidence issues: unavailable" in out
        assert "Freshness: not evaluated (snapshot-only status)" in out

    def test_invalid_projection_reports_degraded_without_serving_evidence(
        self,
        tmp_project,
        capsys,
        monkeypatch,
    ):
        wiki = tmp_project / "docs" / "llm_wiki"
        _committed_state(wiki)
        (wiki / KNOWLEDGE_INDEX_FILENAME).write_bytes(b"{not-json\n")
        _guard_live_knowledge_evaluation(monkeypatch)

        status_cmd.run(_make_args(wiki_dir=str(wiki)))

        out = capsys.readouterr().out
        assert (
            "Knowledge:       degraded "
            "(reason: policy-selected-surface-only-fallback-after-invalid)"
        ) in out
        assert "Concepts evaluated: 0" in out
        assert "Evidence issues: unavailable" in out
        assert "Freshness: not evaluated (snapshot-only status)" in out
        assert "llm-wiki://entities/User" not in out
        assert "sha256:" not in out


class TestStatusAgent:
    def test_shows_configured_agent(self, tmp_project, capsys):
        wiki = tmp_project / "docs" / "llm_wiki"
        wiki.mkdir(parents=True)
        (tmp_project / ".git" / ".llm-wiki-agent").write_text("claude")

        status_cmd.run(_make_args(wiki_dir=str(wiki)))
        out = capsys.readouterr().out
        assert "claude" in out
        assert "CLI" in out
        assert "Issue reporting: disabled" in out

    def test_shows_issue_reporting_enabled(self, tmp_project, capsys):
        wiki = tmp_project / "docs" / "llm_wiki"
        wiki.mkdir(parents=True)
        config = {
            "agent": "copilot",
            "quality_hints": True,
            "issue_reporting": True,
        }
        (tmp_project / ".git" / ".llm-wiki-agent").write_text(
            json.dumps(config), encoding="utf-8"
        )

        status_cmd.run(_make_args(wiki_dir=str(wiki)))

        out = capsys.readouterr().out
        assert "Issue reporting: enabled" in out

    def test_shows_ide_agent(self, tmp_project, capsys):
        wiki = tmp_project / "docs" / "llm_wiki"
        wiki.mkdir(parents=True)
        (tmp_project / ".git" / ".llm-wiki-agent").write_text("copilot")

        status_cmd.run(_make_args(wiki_dir=str(wiki)))
        out = capsys.readouterr().out
        assert "copilot" in out
        assert "IDE" in out

    def test_shows_not_configured(self, tmp_project, capsys):
        wiki = tmp_project / "docs" / "llm_wiki"
        wiki.mkdir(parents=True)

        status_cmd.run(_make_args(wiki_dir=str(wiki)))
        out = capsys.readouterr().out
        assert "not configured" in out


class TestStatusHooks:
    def test_detects_installed_hooks(self, tmp_project, capsys):
        hooks_dir = tmp_project / ".git" / "hooks"
        hooks_dir.mkdir(parents=True, exist_ok=True)
        (hooks_dir / "post-commit").write_text("#!/bin/sh\n# LLM Wiki hook\n")

        wiki = tmp_project / "docs" / "llm_wiki"
        wiki.mkdir(parents=True)

        status_cmd.run(_make_args(wiki_dir=str(wiki)))
        out = capsys.readouterr().out
        assert "post-commit" in out

    def test_shows_no_hooks(self, tmp_project, capsys):
        wiki = tmp_project / "docs" / "llm_wiki"
        wiki.mkdir(parents=True)

        status_cmd.run(_make_args(wiki_dir=str(wiki)))
        out = capsys.readouterr().out
        assert "none installed" in out


class TestStatusBreaker:
    def test_shows_closed(self, tmp_project, capsys):
        wiki = tmp_project / "docs" / "llm_wiki"
        wiki.mkdir(parents=True)

        status_cmd.run(_make_args(wiki_dir=str(wiki)))
        out = capsys.readouterr().out
        assert "closed" in out

    def test_shows_open(self, tmp_project, capsys):
        git_dir = tmp_project / ".git"
        state = {
            "consecutive_failures": 3,
            "last_failure_ts": "2026-01-01T00:00:00+00:00",
            "state": "open",
        }
        (git_dir / "llm-wiki-breaker.json").write_text(json.dumps(state))

        wiki = tmp_project / "docs" / "llm_wiki"
        wiki.mkdir(parents=True)

        status_cmd.run(_make_args(wiki_dir=str(wiki)))
        out = capsys.readouterr().out
        assert "OPEN" in out
        assert "3" in out
        assert "next trigger evaluates automatic recovery" in out.lower()

    def test_shows_active_half_open_recovery_probe(self, tmp_project, capsys):
        git_dir = tmp_project / ".git"
        state = {
            "consecutive_failures": 3,
            "last_failure_ts": "2026-01-01T00:00:00+00:00",
            "probe_started_ts": "2026-01-01T01:00:00+00:00",
            "state": "half-open",
        }
        (git_dir / "llm-wiki-breaker.json").write_text(json.dumps(state))
        wiki = tmp_project / "docs" / "llm_wiki"
        wiki.mkdir(parents=True)

        status_cmd.run(_make_args(wiki_dir=str(wiki)))

        out = capsys.readouterr().out
        assert "HALF-OPEN" in out
        assert "recovery probe lease persisted" in out
        assert "next trigger evaluates the probe lease" in out.lower()


class TestStatusReferenceSkill:
    def test_not_installed(self, tmp_project, capsys):
        status_cmd.run(_make_args())
        out = capsys.readouterr().out
        assert "Reference skill: not installed" in out

    def test_current(self, tmp_project, capsys):
        from llm_wiki_cli.services.skills import install_reference_skill

        install_reference_skill(agent="generic")
        status_cmd.run(_make_args())
        out = capsys.readouterr().out
        assert "Reference skill: wiki-reference (current)" in out

    def test_differs_from_bundled(self, tmp_project, capsys):
        from pathlib import Path

        from llm_wiki_cli.services.skills import install_reference_skill

        install_reference_skill(agent="generic")
        Path(".llm-wiki/skills/wiki-reference/reference.md").write_text(
            "old\n", encoding="utf-8"
        )
        status_cmd.run(_make_args())
        out = capsys.readouterr().out
        assert "differs from bundled" in out
        assert "llm-wiki upgrade" in out
