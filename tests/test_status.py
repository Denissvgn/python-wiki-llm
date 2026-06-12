"""Tests for commands/status_cmd.py"""
import json
import types
from pathlib import Path

import pytest

from llm_wiki_cli.commands import status_cmd


def _make_args(**kwargs):
    return types.SimpleNamespace(**kwargs)


class TestStatusWiki:
    def test_shows_wiki_exists(self, tmp_project, capsys):
        wiki = tmp_project / "docs" / "llm_wiki"
        for d in ["entities", "modules", "workflows"]:
            (wiki / d).mkdir(parents=True)
        (wiki / "entities" / "User.md").write_text("# User\n")
        (wiki / "modules" / "main.md").write_text("# main\n")

        status_cmd.run(_make_args(wiki_dir=str(wiki)))
        out = capsys.readouterr().out
        assert "exists" in out
        assert "Entities:      1" in out
        assert "Modules:       1" in out

    def test_counts_wiki_pages_without_materializing_globs(self, tmp_project, capsys, monkeypatch):
        wiki = tmp_project / "docs" / "llm_wiki"
        for d in ["entities", "modules", "workflows"]:
            (wiki / d).mkdir(parents=True)
        (wiki / "entities" / "User.md").write_text("# User\n")
        (wiki / "modules" / "main.md").write_text("# main\n")
        (wiki / "workflows" / "signup.md").write_text("# signup\n")

        def fail_if_materialized(*_args, **_kwargs):
            raise AssertionError("status should count glob results without list allocation")

        monkeypatch.setattr(status_cmd, "list", fail_if_materialized, raising=False)

        status_cmd.run(_make_args(wiki_dir=str(wiki)))
        out = capsys.readouterr().out

        assert "Entities:      1" in out
        assert "Modules:       1" in out
        assert "Workflows:     1" in out

    def test_shows_wiki_missing(self, tmp_project, capsys):
        status_cmd.run(_make_args(wiki_dir="nonexistent"))
        out = capsys.readouterr().out
        assert "not found" in out


class TestStatusAgent:
    def test_shows_configured_agent(self, tmp_project, capsys):
        wiki = tmp_project / "docs" / "llm_wiki"
        wiki.mkdir(parents=True)
        (tmp_project / ".git" / ".llm-wiki-agent").write_text("claude")

        status_cmd.run(_make_args(wiki_dir=str(wiki)))
        out = capsys.readouterr().out
        assert "claude" in out
        assert "CLI" in out

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
