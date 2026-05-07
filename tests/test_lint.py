"""Tests for commands/lint_cmd.py"""
import hashlib
import json
import textwrap
import types
from pathlib import Path

import pytest

from llm_wiki_cli.commands import extract_cmd
from llm_wiki_cli.commands import lint_cmd
from llm_wiki_cli.commands.extract_cmd import ExtractorStatus, InventoryResult
from llm_wiki_cli.services.inventory_cache import CACHE_FILENAME, InventoryCacheStats
from llm_wiki_cli.services import team


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

    def test_ignores_anchors_and_mailto_and_validates_file_part(self, tmp_path, monkeypatch, capsys):
        monkeypatch.chdir(tmp_path)
        wiki = tmp_path / "wiki"
        wiki.mkdir()
        (wiki / "index.md").write_text("# Index\n- [Notes](notes.md#overview)\n")
        (wiki / "log.md").write_text("# Log\n")
        (wiki / "notes.md").write_text(
            "# Notes\n\n"
            "## Overview\n"
            "[Jump](#overview)\n"
            "[Mail](mailto:user@example.com)\n"
            "[Index](index.md#top)\n"
        )

        monkeypatch.setattr(
            lint_cmd,
            "get_inventory_result",
            lambda *a, **k: InventoryResult({}, {"python": ExtractorStatus("python", "skipped", 0)}),
        )
        monkeypatch.setattr(lint_cmd, "get_docker_inventory", lambda *a, **k: {})

        lint_cmd.run(_make_args(wiki_dir="wiki", src_dir="."))
        out = capsys.readouterr().out
        assert "No broken links" in out

    def test_workflow_broken_link_is_not_double_counted(self, tmp_path, monkeypatch, capsys):
        monkeypatch.chdir(tmp_path)
        wiki = tmp_path / "wiki"
        (wiki / "modules").mkdir(parents=True)
        (wiki / "workflows").mkdir(parents=True)
        (wiki / "workflows" / "flow.md").write_text(
            "# flow\n\n- [missing](../modules/missing.md)\n"
        )
        (wiki / "index.md").write_text("# Index\n- [flow](workflows/flow.md)\n")
        (wiki / "log.md").write_text("# Log\n")

        monkeypatch.setattr(
            lint_cmd,
            "get_inventory_result",
            lambda *a, **k: InventoryResult({}, {"python": ExtractorStatus("python", "skipped", 0)}),
        )
        monkeypatch.setattr(lint_cmd, "get_docker_inventory", lambda *a, **k: {})

        with pytest.raises(SystemExit):
            lint_cmd.run(_make_args(wiki_dir="wiki", src_dir="."))

        out = capsys.readouterr().out
        assert "Found 1 broken link(s)." in out
        assert "Found 1 broken workflow link(s)." in out
        assert "Lint found 1 issue(s)." in out


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

    def test_strict_lint_reuses_existing_inventory(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        (tmp_path / "a.py").write_text("class A:\n    pass\n", encoding="utf-8")
        digest = hashlib.sha256((tmp_path / "a.py").read_bytes()).hexdigest()

        wiki = tmp_path / "wiki"
        for d in ["entities", "modules", "workflows", "infrastructure"]:
            (wiki / d).mkdir(parents=True)
        (wiki / "entities" / "A.md").write_text("# A\n", encoding="utf-8")
        (wiki / "modules" / "a.md").write_text("# a\n", encoding="utf-8")
        (wiki / "index.md").write_text(
            "# Index\n- [A](entities/A.md)\n- [a](modules/a.md)\n",
            encoding="utf-8",
        )
        (wiki / "log.md").write_text("# Log\n", encoding="utf-8")
        (wiki / ".llm-wiki-manifest.json").write_text(
            json.dumps({
                "version": 2,
                "sources": {
                    "a.py": {
                        "hash": f"sha256:{digest}",
                        "language": "python",
                        "entities": ["A"],
                        "entity_pages": {"A": "A"},
                        "module_page": "a",
                    }
                },
            }),
            encoding="utf-8",
        )

        calls = {"inventory": 0}

        def fake_inventory(*args, **kwargs):
            calls["inventory"] += 1
            return InventoryResult(
                {"a.py": {"language": "python", "classes": [{"name": "A"}], "functions": []}},
                {"python": ExtractorStatus("python", "ok", 1)},
            )

        monkeypatch.setattr(lint_cmd, "get_inventory_result", fake_inventory)
        monkeypatch.setattr(lint_cmd, "get_docker_inventory", lambda *a, **k: {})

        report = lint_cmd.build_report(wiki, ".", strict=True)

        assert report.passed
        assert calls == {"inventory": 1}

    def test_team_checks_reuse_lint_docker_inventory(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        wiki = tmp_path / "wiki"
        for d in ["entities", "modules", "workflows", "infrastructure"]:
            (wiki / d).mkdir(parents=True)
        (wiki / "entities" / "A.md").write_text("# A\n", encoding="utf-8")
        (wiki / "modules" / "a.md").write_text("# a\n", encoding="utf-8")
        (wiki / "infrastructure" / "Dockerfile.md").write_text("# Dockerfile\n", encoding="utf-8")
        (wiki / "index.md").write_text(
            "# Index\n"
            "- [A](entities/A.md)\n"
            "- [a](modules/a.md)\n"
            "- [Dockerfile](infrastructure/Dockerfile.md)\n",
            encoding="utf-8",
        )
        (wiki / "log.md").write_text("# Log\n", encoding="utf-8")
        team.write_default_team_config(str(wiki))

        monkeypatch.setattr(
            lint_cmd,
            "get_inventory_result",
            lambda *a, **k: InventoryResult(
                {"a.py": {"language": "python", "classes": [{"name": "A"}], "functions": []}},
                {"python": ExtractorStatus("python", "ok", 1)},
            ),
        )
        docker_calls = {"lint": 0}

        def fake_lint_docker(*args, **kwargs):
            docker_calls["lint"] += 1
            return {"Dockerfile": {"type": "dockerfile"}}

        monkeypatch.setattr(lint_cmd, "get_docker_inventory", fake_lint_docker)
        monkeypatch.setattr(
            extract_cmd,
            "get_docker_inventory",
            lambda *a, **k: pytest.fail("team check should reuse lint docker inventory"),
        )

        lint_cmd.build_report(wiki, ".", strict=False)

        assert docker_calls == {"lint": 1}


class TestLintProfile:
    def test_profile_outputs_combined_json(self, tmp_path, monkeypatch, capsys):
        monkeypatch.chdir(tmp_path)
        wiki = tmp_path / "wiki"
        for d in ["entities", "modules", "workflows", "infrastructure"]:
            (wiki / d).mkdir(parents=True)
        (wiki / "entities" / "A.md").write_text("# A\n", encoding="utf-8")
        (wiki / "modules" / "a.md").write_text("# a\n", encoding="utf-8")
        (wiki / "index.md").write_text(
            "# Index\n- [A](entities/A.md)\n- [a](modules/a.md)\n",
            encoding="utf-8",
        )
        (wiki / "log.md").write_text("# Log\n", encoding="utf-8")

        monkeypatch.setattr(
            lint_cmd,
            "get_inventory_result",
            lambda *a, **k: InventoryResult(
                {"a.py": {"language": "python", "classes": [{"name": "A"}], "functions": []}},
                {"python": ExtractorStatus("python", "ok", 1)},
            ),
        )
        monkeypatch.setattr(lint_cmd, "get_docker_inventory", lambda *a, **k: {})

        lint_cmd.run(_make_args(wiki_dir=str(wiki), src_dir=".", profile=True))

        payload = json.loads(capsys.readouterr().out)
        assert payload["ok"] is True
        assert payload["issue_count"] == 0
        assert payload["diagnostics"] == []
        assert "profile" in payload
        assert isinstance(payload["profile"]["total_ms"], int)
        phase_names = {phase["name"] for phase in payload["profile"]["phases"]}
        assert {
            "inventory",
            "docker_inventory",
            "page_index",
            "links",
            "orphans",
            "entities",
            "modules",
            "workflows",
            "infrastructure",
            "strict",
            "plugins",
            "team",
        } <= phase_names

    def test_profile_preserves_nonzero_exit_code(self, tmp_path, monkeypatch, capsys):
        monkeypatch.chdir(tmp_path)
        wiki = tmp_path / "wiki"
        wiki.mkdir()
        (wiki / "index.md").write_text("# Index\n- [Ghost](missing.md)\n", encoding="utf-8")
        (wiki / "log.md").write_text("# Log\n", encoding="utf-8")

        monkeypatch.setattr(
            lint_cmd,
            "get_inventory_result",
            lambda *a, **k: InventoryResult(
                {},
                {"python": ExtractorStatus("python", "skipped", 0)},
            ),
        )
        monkeypatch.setattr(lint_cmd, "get_docker_inventory", lambda *a, **k: {})

        with pytest.raises(SystemExit) as exc:
            lint_cmd.run(_make_args(wiki_dir=str(wiki), src_dir=".", profile=True))

        assert exc.value.code == 1
        payload = json.loads(capsys.readouterr().out)
        assert payload["ok"] is False
        assert payload["issue_count"] == 1
        assert payload["issues"][0]["category"] == "broken_links"

    def test_default_output_remains_human_readable(self, tmp_path, monkeypatch, capsys):
        monkeypatch.chdir(tmp_path)
        wiki = tmp_path / "wiki"
        wiki.mkdir()
        (wiki / "index.md").write_text("# Index\n", encoding="utf-8")
        (wiki / "log.md").write_text("# Log\n", encoding="utf-8")

        monkeypatch.setattr(
            lint_cmd,
            "get_inventory_result",
            lambda *a, **k: InventoryResult(
                {},
                {"python": ExtractorStatus("python", "skipped", 0)},
            ),
        )
        monkeypatch.setattr(lint_cmd, "get_docker_inventory", lambda *a, **k: {})

        lint_cmd.run(_make_args(wiki_dir=str(wiki), src_dir="."))
        out = capsys.readouterr().out

        assert out.startswith("Linting Wiki at:")
        with pytest.raises(json.JSONDecodeError):
            json.loads(out)

    def test_profile_with_cache_stats_includes_cache_object(self, tmp_path, monkeypatch, capsys):
        monkeypatch.chdir(tmp_path)
        wiki = tmp_path / "wiki"
        wiki.mkdir()
        (wiki / "index.md").write_text("# Index\n", encoding="utf-8")
        (wiki / "log.md").write_text("# Log\n", encoding="utf-8")

        monkeypatch.setattr(
            lint_cmd,
            "get_inventory_result",
            lambda *a, **k: InventoryResult(
                {},
                {"python": ExtractorStatus("python", "skipped", 0)},
                InventoryCacheStats(enabled=True, path="cache.json", status="hit", hits=3),
            ),
        )
        monkeypatch.setattr(lint_cmd, "get_docker_inventory", lambda *a, **k: {})

        lint_cmd.run(_make_args(wiki_dir="wiki", src_dir=".", profile=True, cache_stats=True))

        payload = json.loads(capsys.readouterr().out)
        assert payload["cache"]["status"] == "hit"
        assert payload["cache"]["hits"] == 3

    def test_cache_stats_adds_human_readable_section(self, tmp_path, monkeypatch, capsys):
        monkeypatch.chdir(tmp_path)
        wiki = tmp_path / "wiki"
        wiki.mkdir()
        (wiki / "index.md").write_text("# Index\n", encoding="utf-8")
        (wiki / "log.md").write_text("# Log\n", encoding="utf-8")

        monkeypatch.setattr(
            lint_cmd,
            "get_inventory_result",
            lambda *a, **k: InventoryResult(
                {},
                {"python": ExtractorStatus("python", "skipped", 0)},
                InventoryCacheStats(enabled=True, path="cache.json", status="partial", hits=1, misses=2),
            ),
        )
        monkeypatch.setattr(lint_cmd, "get_docker_inventory", lambda *a, **k: {})

        lint_cmd.run(_make_args(wiki_dir="wiki", src_dir=".", cache_stats=True))
        out = capsys.readouterr().out

        assert "Cache:" in out
        assert "status: partial" in out
        assert "1 hit(s), 2 miss(es)" in out

    def test_no_cache_flag_disables_cache_options(self, tmp_path, monkeypatch, capsys):
        monkeypatch.chdir(tmp_path)
        wiki = tmp_path / "wiki"
        wiki.mkdir()
        (wiki / "index.md").write_text("# Index\n", encoding="utf-8")
        (wiki / "log.md").write_text("# Log\n", encoding="utf-8")
        seen = {}

        def fake_inventory(*args, **kwargs):
            seen["cache_options"] = kwargs["cache_options"]
            return InventoryResult(
                {},
                {"python": ExtractorStatus("python", "skipped", 0)},
                InventoryCacheStats(enabled=False, status="disabled"),
            )

        monkeypatch.setattr(lint_cmd, "get_inventory_result", fake_inventory)
        monkeypatch.setattr(lint_cmd, "get_docker_inventory", lambda *a, **k: {})

        lint_cmd.run(_make_args(wiki_dir="wiki", src_dir=".", no_cache=True, cache_stats=True))

        assert seen["cache_options"].enabled is False

    def test_rebuild_cache_flag_sets_cache_options(self, tmp_path, monkeypatch, capsys):
        monkeypatch.chdir(tmp_path)
        wiki = tmp_path / "wiki"
        wiki.mkdir()
        (wiki / "index.md").write_text("# Index\n", encoding="utf-8")
        (wiki / "log.md").write_text("# Log\n", encoding="utf-8")
        seen = {}

        def fake_inventory(*args, **kwargs):
            seen["cache_options"] = kwargs["cache_options"]
            return InventoryResult(
                {},
                {"python": ExtractorStatus("python", "skipped", 0)},
                InventoryCacheStats(enabled=True, status="rebuild"),
            )

        monkeypatch.setattr(lint_cmd, "get_inventory_result", fake_inventory)
        monkeypatch.setattr(lint_cmd, "get_docker_inventory", lambda *a, **k: {})

        lint_cmd.run(_make_args(wiki_dir="wiki", src_dir=".", rebuild_cache=True, cache_stats=True))

        assert seen["cache_options"].rebuild is True

    def test_lint_creates_default_git_cache(self, tmp_path, monkeypatch, capsys):
        monkeypatch.chdir(tmp_path)
        (tmp_path / ".git").mkdir()
        (tmp_path / "app.py").write_text("class A: pass\n", encoding="utf-8")
        wiki = tmp_path / "wiki"
        (wiki / "entities").mkdir(parents=True)
        (wiki / "modules").mkdir()
        (wiki / "workflows").mkdir()
        (wiki / "infrastructure").mkdir()
        (wiki / "entities" / "A.md").write_text("# A\n", encoding="utf-8")
        (wiki / "modules" / "app.md").write_text("# app\n", encoding="utf-8")
        (wiki / "index.md").write_text(
            "# Index\n- [A](entities/A.md)\n- [app](modules/app.md)\n",
            encoding="utf-8",
        )
        (wiki / "log.md").write_text("# Log\n", encoding="utf-8")

        lint_cmd.run(_make_args(wiki_dir="wiki", src_dir="."))

        assert (tmp_path / ".git" / CACHE_FILENAME).exists()

    def test_no_cache_does_not_save_default_git_cache(self, tmp_path, monkeypatch, capsys):
        monkeypatch.chdir(tmp_path)
        (tmp_path / ".git").mkdir()
        wiki = tmp_path / "wiki"
        wiki.mkdir()
        (wiki / "index.md").write_text("# Index\n", encoding="utf-8")
        (wiki / "log.md").write_text("# Log\n", encoding="utf-8")

        lint_cmd.run(_make_args(wiki_dir="wiki", src_dir=".", no_cache=True))

        assert not (tmp_path / ".git" / CACHE_FILENAME).exists()
