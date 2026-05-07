"""Tests for ci-check command integration."""
from __future__ import annotations

import json
import types

from llm_wiki_cli.commands import ci_check_cmd
from llm_wiki_cli.commands.lint_cmd import LintReport


def test_ci_check_uses_inventory_cache_options(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "wiki").mkdir()
    seen = {}

    def fake_build_report(wiki_dir, src_dir, **kwargs):
        seen["cache_options"] = kwargs["cache_options"]
        return LintReport(wiki_dir=str(wiki_dir), src_dir=src_dir, strict=kwargs["strict"])

    monkeypatch.setattr(ci_check_cmd, "build_report", fake_build_report)
    monkeypatch.setattr(ci_check_cmd, "record_validation_event", lambda **kwargs: None)

    ci_check_cmd.run(types.SimpleNamespace(
        src_dir=".",
        wiki_dir="wiki",
        format="json",
        report=".git/llm-wiki-ci-report.md",
    ))

    payload = json.loads(capsys.readouterr().out)
    assert payload["ok"] is True
    assert seen["cache_options"].enabled is True
    assert seen["cache_options"].stats_enabled is False
