"""Tests for commands/lint_cmd.py"""
import textwrap
import types
from pathlib import Path

import pytest

from llm_wiki_cli.commands import lint_cmd
from llm_wiki_cli.commands.extract_cmd import ExtractorStatus, InventoryResult


def _make_args(**kwargs):
    """Create a simple namespace mimicking argparse output."""
    return types.SimpleNamespace(**kwargs)


class TestLintCleanWiki:
    def test_no_issues(self, tmp_project, capsys):
        """A consistent wiki should produce 0 issues."""
        wiki = tmp_project / "wiki"
        for d in ["entities", "modules", "workflows"]:
            (wiki / d).mkdir(parents=True)

        (wiki / "entities" / "User.md").write_text("# User\n")
        (wiki / "entities" / "Item.md").write_text("# Item\n")
        (wiki / "modules" / "models.md").write_text("# models\n")
        (wiki / "modules" / "main.md").write_text("# main\n")
        (wiki / "modules" / "utils.md").write_text("# utils\n")
        (wiki / "index.md").write_text(
            "# Index\n"
            "- [User](entities/User.md)\n"
            "- [Item](entities/Item.md)\n"
            "- [models](modules/models.md)\n"
            "- [main](modules/main.md)\n"
            "- [utils](modules/utils.md)\n"
        )
        (wiki / "log.md").write_text("# Log\n")

        args = _make_args(wiki_dir=str(wiki), src_dir=".")
        lint_cmd.run(args)
        out = capsys.readouterr().out
        assert "Broken link" not in out or "No broken links" in out


class TestLintBrokenLink:
    def test_detects_broken_link(self, tmp_project, capsys):
        wiki = tmp_project / "wiki"
        (wiki / "entities").mkdir(parents=True)
        (wiki / "modules").mkdir(parents=True)
        (wiki / "workflows").mkdir(parents=True)

        (wiki / "index.md").write_text("# Index\n- [Ghost](entities/Ghost.md)\n")
        (wiki / "log.md").write_text("# Log\n")

        args = _make_args(wiki_dir=str(wiki), src_dir=".")
        with pytest.raises(SystemExit):
            lint_cmd.run(args)
        out = capsys.readouterr().out
        assert "Broken link" in out


class TestLintOrphanPage:
    def test_detects_orphan(self, tmp_project, capsys):
        wiki = tmp_project / "wiki"
        (wiki / "entities").mkdir(parents=True)
        (wiki / "modules").mkdir(parents=True)
        (wiki / "workflows").mkdir(parents=True)

        (wiki / "index.md").write_text("# Index\n")
        (wiki / "log.md").write_text("# Log\n")
        (wiki / "entities" / "Orphan.md").write_text("# Orphan\n")

        args = _make_args(wiki_dir=str(wiki), src_dir=".")
        with pytest.raises(SystemExit):
            lint_cmd.run(args)
        out = capsys.readouterr().out
        assert "Orphan" in out


class TestLintUndocumentedClass:
    def test_detects_undocumented(self, tmp_project, capsys):
        """Classes in code but not in wiki should be flagged."""
        wiki = tmp_project / "wiki"
        for d in ["entities", "modules", "workflows"]:
            (wiki / d).mkdir(parents=True)
        (wiki / "index.md").write_text("# Index\n")
        (wiki / "log.md").write_text("# Log\n")
        # No entity pages → User and Item are undocumented

        args = _make_args(wiki_dir=str(wiki), src_dir=".")
        with pytest.raises(SystemExit):
            lint_cmd.run(args)
        out = capsys.readouterr().out
        assert "Undocumented class" in out


class TestLintStaleEntity:
    def test_detects_stale(self, tmp_project, capsys):
        """Entity page for class not in code should be flagged."""
        wiki = tmp_project / "wiki"
        for d in ["entities", "modules", "workflows"]:
            (wiki / d).mkdir(parents=True)
        (wiki / "entities" / "User.md").write_text("# User\n")
        (wiki / "entities" / "Item.md").write_text("# Item\n")
        (wiki / "entities" / "Deleted.md").write_text("# Deleted\n")
        (wiki / "index.md").write_text(
            "# Index\n- [User](entities/User.md)\n- [Item](entities/Item.md)\n"
            "- [Deleted](entities/Deleted.md)\n"
        )
        (wiki / "log.md").write_text("# Log\n")

        args = _make_args(wiki_dir=str(wiki), src_dir=".")
        with pytest.raises(SystemExit):
            lint_cmd.run(args)
        out = capsys.readouterr().out
        assert "Stale entity" in out
        assert "Deleted" in out


class TestLintExitCode:
    def test_exits_1_on_issues(self, tmp_project, capsys):
        """Lint should exit with code 1 when issues are found."""
        wiki = tmp_project / "wiki"
        for d in ["entities", "modules", "workflows"]:
            (wiki / d).mkdir(parents=True)
        (wiki / "index.md").write_text("# Index\n")
        (wiki / "log.md").write_text("# Log\n")

        args = _make_args(wiki_dir=str(wiki), src_dir=".")
        import sys
        with pytest.raises(SystemExit) as exc_info:
            lint_cmd.run(args)
        assert exc_info.value.code == 1


class TestLintInventoryCaching:
    def test_inventory_and_docker_scanned_once(self, tmp_project, monkeypatch, capsys):
        wiki = tmp_project / "wiki"
        for d in ["entities", "modules", "workflows", "infrastructure"]:
            (wiki / d).mkdir(parents=True)
        (wiki / "entities" / "A.md").write_text("# A\n")
        (wiki / "modules" / "a.md").write_text("# a\n")
        (wiki / "infrastructure" / "Dockerfile.md").write_text("# Dockerfile\n")
        (wiki / "index.md").write_text(
            "# Index\n"
            "- [A](entities/A.md)\n"
            "- [a](modules/a.md)\n"
            "- [Dockerfile](infrastructure/Dockerfile.md)\n"
        )
        (wiki / "log.md").write_text("# Log\n")

        calls = {"inventory": 0, "docker": 0}

        def fake_inventory(*args, **kwargs):
            calls["inventory"] += 1
            return InventoryResult(
                {"a.py": {"language": "python", "classes": [{"name": "A"}], "functions": []}},
                {"python": ExtractorStatus("python", "ok", 1)},
            )

        def fake_docker(*args, **kwargs):
            calls["docker"] += 1
            return {"Dockerfile": {"type": "dockerfile"}}

        monkeypatch.setattr(lint_cmd, "get_inventory_result", fake_inventory)
        monkeypatch.setattr(lint_cmd, "get_docker_inventory", fake_docker)

        lint_cmd.run(_make_args(wiki_dir=str(wiki), src_dir="."))

        assert calls == {"inventory": 1, "docker": 1}
