"""Tests for commands/lint_cmd.py"""

import ast
import hashlib
import inspect
import json
import textwrap
import types

import pytest

from llm_wiki_cli import cli
from llm_wiki_cli.commands import extract_cmd
from llm_wiki_cli.commands import lint_cmd
from llm_wiki_cli.commands.extract_cmd import ExtractorStatus, InventoryResult
from llm_wiki_cli.services.inventory_cache import CACHE_FILENAME, InventoryCacheStats
from llm_wiki_cli.services import team


def _make_args(**kwargs):
    """Create a simple namespace mimicking argparse output."""
    return types.SimpleNamespace(**kwargs)


def _body_line_count(function) -> int:
    source = textwrap.dedent(inspect.getsource(function))
    function_node = ast.parse(source).body[0]
    body = [
        stmt
        for stmt in function_node.body
        if not (
            isinstance(stmt, ast.Expr)
            and isinstance(stmt.value, ast.Constant)
            and isinstance(stmt.value.value, str)
        )
    ]
    first_body_line = min(stmt.lineno for stmt in body)
    last_body_line = max(stmt.end_lineno for stmt in body)
    return last_body_line - first_body_line + 1


class TestLintBuildReportStructure:
    def test_build_report_stays_decomposed(self):
        assert _body_line_count(lint_cmd.build_report) <= 45


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

    def test_ignores_anchors_and_mailto_and_validates_file_part(
        self, tmp_path, monkeypatch, capsys
    ):
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
            lambda *a, **k: InventoryResult(
                {}, {"python": ExtractorStatus("python", "skipped", 0)}
            ),
        )
        monkeypatch.setattr(lint_cmd, "get_docker_inventory", lambda *a, **k: {})

        lint_cmd.run(_make_args(wiki_dir="wiki", src_dir="."))
        out = capsys.readouterr().out
        assert "No broken links" in out

    def test_workflow_broken_link_is_not_double_counted(
        self, tmp_path, monkeypatch, capsys
    ):
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
            lambda *a, **k: InventoryResult(
                {}, {"python": ExtractorStatus("python", "skipped", 0)}
            ),
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
                {
                    "a.py": {
                        "language": "python",
                        "classes": [{"name": "A"}],
                        "functions": [],
                    }
                },
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
            json.dumps(
                {
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
                }
            ),
            encoding="utf-8",
        )

        calls = {"inventory": 0}

        def fake_inventory(*args, **kwargs):
            calls["inventory"] += 1
            return InventoryResult(
                {
                    "a.py": {
                        "language": "python",
                        "classes": [{"name": "A"}],
                        "functions": [],
                    }
                },
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
        (wiki / "infrastructure" / "Dockerfile.md").write_text(
            "# Dockerfile\n", encoding="utf-8"
        )
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
                {
                    "a.py": {
                        "language": "python",
                        "classes": [{"name": "A"}],
                        "functions": [],
                    }
                },
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
            lambda *a, **k: pytest.fail(
                "team check should reuse lint docker inventory"
            ),
        )

        lint_cmd.build_report(wiki, ".", strict=False)

        assert docker_calls == {"lint": 1}


class TestLintProfile:
    def test_build_report_converts_extractor_failure_to_issue(
        self, tmp_path, monkeypatch
    ):
        monkeypatch.chdir(tmp_path)
        wiki = tmp_path / "wiki"
        wiki.mkdir()
        cache_stats = InventoryCacheStats(
            enabled=True,
            path="cache.json",
            status="partial",
            hits=1,
        )

        monkeypatch.setattr(
            lint_cmd,
            "get_inventory_result",
            lambda *a, **k: InventoryResult(
                {},
                {"rust": ExtractorStatus("rust", "failed", 1, "helper missing")},
                cache_stats,
            ),
        )
        monkeypatch.setattr(
            lint_cmd,
            "get_docker_inventory",
            lambda *a, **k: pytest.fail(
                "docker inventory should not run after extractor failure"
            ),
        )

        report = lint_cmd.build_report(
            "wiki",
            ".",
            cache_options=lint_cmd.InventoryCacheOptions(
                enabled=True, stats_enabled=True
            ),
        )

        assert report.passed is False
        assert report.cache_stats is cache_stats
        assert report.issue_count == 1
        issue = report.issues[0]
        assert issue.category == "extractor_failure"
        assert issue.target == "rust"
        assert issue.message == "rust extraction failed: helper missing"

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
                {
                    "a.py": {
                        "language": "python",
                        "classes": [{"name": "A"}],
                        "functions": [],
                    }
                },
                {"python": ExtractorStatus("python", "ok", 1)},
            ),
        )
        monkeypatch.setattr(lint_cmd, "get_docker_inventory", lambda *a, **k: {})

        lint_cmd.run(_make_args(wiki_dir=str(wiki), src_dir=".", profile=True, jobs=2))

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
        (wiki / "index.md").write_text(
            "# Index\n- [Ghost](missing.md)\n", encoding="utf-8"
        )
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

    def test_profile_outputs_json_on_extractor_failure(
        self, tmp_path, monkeypatch, capsys
    ):
        monkeypatch.chdir(tmp_path)
        wiki = tmp_path / "wiki"
        wiki.mkdir()

        monkeypatch.setattr(
            lint_cmd,
            "get_inventory_result",
            lambda *a, **k: InventoryResult(
                {},
                {"rust": ExtractorStatus("rust", "failed", 1, "helper missing")},
                InventoryCacheStats(
                    enabled=True, path="cache.json", status="miss", misses=1
                ),
            ),
        )
        monkeypatch.setattr(
            lint_cmd,
            "get_docker_inventory",
            lambda *a, **k: pytest.fail(
                "docker inventory should not run after extractor failure"
            ),
        )

        with pytest.raises(SystemExit) as exc:
            lint_cmd.run(
                _make_args(
                    wiki_dir="wiki",
                    src_dir=".",
                    profile=True,
                    cache_stats=True,
                )
            )

        assert exc.value.code == 1
        captured = capsys.readouterr()
        assert captured.err == ""
        payload = json.loads(captured.out)
        assert payload["ok"] is False
        assert payload["issue_count"] == 1
        assert payload["issues"][0]["category"] == "extractor_failure"
        assert payload["issues"][0]["target"] == "rust"
        assert payload["profile"]["total_ms"] >= 0
        assert {phase["name"] for phase in payload["profile"]["phases"]} >= {
            "inventory"
        }
        assert payload["cache"]["status"] == "miss"

    def test_non_profile_extractor_failure_reports_stderr_only(
        self, tmp_path, monkeypatch, capsys
    ):
        monkeypatch.chdir(tmp_path)
        wiki = tmp_path / "wiki"
        wiki.mkdir()

        monkeypatch.setattr(
            lint_cmd,
            "get_inventory_result",
            lambda *a, **k: InventoryResult(
                {},
                {"python": ExtractorStatus("python", "failed", 1, "boom")},
            ),
        )
        monkeypatch.setattr(
            lint_cmd,
            "get_docker_inventory",
            lambda *a, **k: pytest.fail(
                "docker inventory should not run after extractor failure"
            ),
        )

        with pytest.raises(SystemExit) as exc:
            lint_cmd.run(_make_args(wiki_dir="wiki", src_dir="."))

        assert exc.value.code == 1
        captured = capsys.readouterr()
        assert captured.out == ""
        assert "Error: python extraction failed: boom" in captured.err

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

    def test_profile_with_cache_stats_includes_cache_object(
        self, tmp_path, monkeypatch, capsys
    ):
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
                InventoryCacheStats(
                    enabled=True, path="cache.json", status="hit", hits=3
                ),
            ),
        )
        monkeypatch.setattr(lint_cmd, "get_docker_inventory", lambda *a, **k: {})

        lint_cmd.run(
            _make_args(wiki_dir="wiki", src_dir=".", profile=True, cache_stats=True)
        )

        payload = json.loads(capsys.readouterr().out)
        assert payload["cache"]["status"] == "hit"
        assert payload["cache"]["hits"] == 3

    def test_cache_stats_adds_human_readable_section(
        self, tmp_path, monkeypatch, capsys
    ):
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
                InventoryCacheStats(
                    enabled=True, path="cache.json", status="partial", hits=1, misses=2
                ),
            ),
        )
        monkeypatch.setattr(lint_cmd, "get_docker_inventory", lambda *a, **k: {})

        lint_cmd.run(_make_args(wiki_dir="wiki", src_dir=".", cache_stats=True, jobs=2))
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

        lint_cmd.run(
            _make_args(wiki_dir="wiki", src_dir=".", no_cache=True, cache_stats=True)
        )

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

        lint_cmd.run(
            _make_args(
                wiki_dir="wiki", src_dir=".", rebuild_cache=True, cache_stats=True
            )
        )

        assert seen["cache_options"].rebuild is True

    def test_run_passes_jobs_to_build_report(self, tmp_path, monkeypatch, capsys):
        monkeypatch.chdir(tmp_path)
        (tmp_path / "wiki").mkdir()
        seen = {}

        def fake_build_report(wiki_dir, src_dir, **kwargs):
            seen["parallel_jobs"] = kwargs["parallel_jobs"]
            return lint_cmd.LintReport(
                wiki_dir=str(wiki_dir), src_dir=src_dir, strict=kwargs["strict"]
            )

        monkeypatch.setattr(lint_cmd, "build_report", fake_build_report)

        lint_cmd.run(_make_args(wiki_dir="wiki", src_dir=".", jobs=2))

        assert seen["parallel_jobs"] == 2

    def test_run_defaults_jobs_to_one(self, tmp_path, monkeypatch, capsys):
        monkeypatch.chdir(tmp_path)
        (tmp_path / "wiki").mkdir()
        seen = {}

        def fake_build_report(wiki_dir, src_dir, **kwargs):
            seen["parallel_jobs"] = kwargs["parallel_jobs"]
            return lint_cmd.LintReport(
                wiki_dir=str(wiki_dir), src_dir=src_dir, strict=kwargs["strict"]
            )

        monkeypatch.setattr(lint_cmd, "build_report", fake_build_report)

        lint_cmd.run(_make_args(wiki_dir="wiki", src_dir="."))

        assert seen["parallel_jobs"] == 1

    def test_cli_lint_jobs_auto_resolves_positive_count(self, monkeypatch):
        seen = {}
        monkeypatch.setattr(cli.os, "cpu_count", lambda: 8)
        monkeypatch.setattr(
            cli.lint_cmd, "run", lambda args: seen.setdefault("jobs", args.jobs)
        )
        monkeypatch.setattr("sys.argv", ["llm-wiki", "lint", "--jobs", "auto"])

        cli.main()

        assert seen["jobs"] == 8

    @pytest.mark.parametrize("value", ["0", "-1", "many"])
    def test_cli_lint_rejects_invalid_jobs(self, value, monkeypatch):
        monkeypatch.setattr(
            cli.lint_cmd, "run", lambda _args: pytest.fail("command should not run")
        )
        monkeypatch.setattr("sys.argv", ["llm-wiki", "lint", "--jobs", value])

        with pytest.raises(SystemExit) as exc:
            cli.main()

        assert exc.value.code == 2

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

    def test_no_cache_does_not_save_default_git_cache(
        self, tmp_path, monkeypatch, capsys
    ):
        monkeypatch.chdir(tmp_path)
        (tmp_path / ".git").mkdir()
        wiki = tmp_path / "wiki"
        wiki.mkdir()
        (wiki / "index.md").write_text("# Index\n", encoding="utf-8")
        (wiki / "log.md").write_text("# Log\n", encoding="utf-8")

        lint_cmd.run(_make_args(wiki_dir="wiki", src_dir=".", no_cache=True))

        assert not (tmp_path / ".git" / CACHE_FILENAME).exists()


class TestLintFlowCoverage:
    def _project_with_flows(self, tmp_path, flow_stems):
        (tmp_path / "api.py").write_text(
            textwrap.dedent("""\
            __all__ = ["run"]

            def run():
                return 1
        """)
        )
        wiki = tmp_path / "wiki"
        for d in ["entities", "modules", "workflows", "flows"]:
            (wiki / d).mkdir(parents=True)
        (wiki / "modules" / "api.md").write_text("# api\n")
        index = ["# Index", "- [api](modules/api.md)"]
        for stem in flow_stems:
            (wiki / "flows" / f"{stem}.md").write_text(f"# {stem}\n")
            index.append(f"- [{stem}](flows/{stem}.md)")
        (wiki / "index.md").write_text("\n".join(index) + "\n")
        (wiki / "log.md").write_text("# Log\n")
        return wiki

    def test_valid_flow_is_not_stale(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        wiki = self._project_with_flows(tmp_path, ["api-run"])
        report = lint_cmd.build_report(str(wiki), ".")
        assert report.count("stale_flows") == 0

    def test_stale_flow_is_flagged(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        wiki = self._project_with_flows(tmp_path, ["api-run", "api-ghost"])
        report = lint_cmd.build_report(str(wiki), ".")
        stale = report.by_category().get("stale_flows", [])
        assert [issue.target for issue in stale] == ["api-ghost"]
        assert not report.passed

    def test_absent_flows_dir_is_clean(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        (tmp_path / "api.py").write_text("def run():\n    return 1\n")
        wiki = tmp_path / "wiki"
        for d in ["entities", "modules", "workflows"]:
            (wiki / d).mkdir(parents=True)
        (wiki / "modules" / "api.md").write_text("# api\n")
        (wiki / "index.md").write_text("# Index\n- [api](modules/api.md)\n")
        (wiki / "log.md").write_text("# Log\n")
        report = lint_cmd.build_report(str(wiki), ".")
        assert report.count("stale_flows") == 0


class TestLintDependencyCoverage:
    """DL-501: architecture-page cycle / reconciliation warnings + staleness."""

    def test_no_architecture_pages_produces_no_findings(self, tmp_project):
        wiki = tmp_project / "wiki"
        wiki.mkdir()
        report = lint_cmd.LintReport(wiki_dir=str(wiki), src_dir=".")
        inventory = extract_cmd.get_inventory(".", deep=True)
        lint_cmd._check_dependency_coverage(report, wiki, inventory, ".")
        assert report.diagnostics == []
        assert report.issues == []

    def test_undeclared_dependency_is_warning_not_failure(self, tmp_project):
        # models.py imports pydantic, which pyproject.toml does not declare.
        wiki = tmp_project / "wiki"
        wiki.mkdir()
        (wiki / "dependencies.md").write_text("# Dependencies\n")
        report = lint_cmd.LintReport(wiki_dir=str(wiki), src_dir=".")
        inventory = extract_cmd.get_inventory(".", deep=True)
        lint_cmd._check_dependency_coverage(report, wiki, inventory, ".")

        undeclared = {
            d.target
            for d in report.diagnostics
            if d.category == "undeclared_dependencies"
        }
        assert "pydantic" in undeclared
        # Reconciliation gaps are warnings only — they never fail lint.
        assert report.issues == []
        assert report.passed
        assert {d.severity for d in report.diagnostics} == {"warning"}

    def test_unused_dependency_is_warning_not_failure(self, tmp_path):
        wiki = tmp_path / "wiki"
        wiki.mkdir()
        (wiki / "dependencies.md").write_text("# Dependencies\n")
        (tmp_path / "pyproject.toml").write_text(
            '[project]\ndependencies = ["requests"]\n', encoding="utf-8"
        )
        inventory = {
            "app.py": {"language": "python", "imports": []},
        }
        report = lint_cmd.LintReport(wiki_dir=str(wiki), src_dir=str(tmp_path))
        lint_cmd._check_dependency_coverage(report, wiki, inventory, str(tmp_path))

        unused = [d for d in report.diagnostics if d.category == "unused_dependencies"]
        assert [d.target for d in unused] == ["requests"]
        assert [d.severity for d in unused] == ["warning"]
        assert report.issues == []
        assert report.passed

    def test_import_cycle_is_warning_not_failure(self, tmp_path):
        wiki = tmp_path / "wiki"
        wiki.mkdir()
        (wiki / "load-order.md").write_text("# Load order\n")
        inventory = {
            "a.py": {"language": "python", "imports": [{"module": "b", "name": "b"}]},
            "b.py": {"language": "python", "imports": [{"module": "a", "name": "a"}]},
        }
        report = lint_cmd.LintReport(wiki_dir=str(wiki), src_dir=str(tmp_path))
        lint_cmd._check_dependency_coverage(report, wiki, inventory, str(tmp_path))

        cycles = [d for d in report.diagnostics if d.category == "dependency_cycles"]
        assert len(cycles) == 1
        assert "a.py" in cycles[0].message and "b.py" in cycles[0].message
        assert cycles[0].severity == "warning"
        assert report.issues == []
        assert report.passed

    def test_architecture_page_links_are_checked_by_global_link_pass(self, tmp_path):
        wiki = tmp_path / "wiki"
        wiki.mkdir()
        deps_page = wiki / "dependencies.md"
        deps_page.write_text("# Dependencies\n\n[Missing](modules/missing.md)\n")
        report = lint_cmd.LintReport(wiki_dir=str(wiki), src_dir=str(tmp_path))

        lint_cmd._check_broken_links(report, wiki, lint_cmd._build_page_index(wiki))

        assert [(i.category, i.path, i.target) for i in report.issues] == [
            ("broken_links", "dependencies.md", "modules/missing.md")
        ]

    def test_page_present_but_no_modules_is_stale_issue(self, tmp_path):
        wiki = tmp_path / "wiki"
        wiki.mkdir()
        (wiki / "dependencies.md").write_text("# Dependencies\n")
        (wiki / "load-order.md").write_text("# Load order\n")
        report = lint_cmd.LintReport(wiki_dir=str(wiki), src_dir=str(tmp_path))
        # No source modules at all -> the pages document nothing.
        lint_cmd._check_dependency_coverage(report, wiki, {}, str(tmp_path))

        stale = {i.target for i in report.issues if i.category == "stale_dependencies"}
        assert stale == {"dependencies", "load-order"}
        assert not report.passed

    def test_dependencies_phase_present_in_profile(self):
        assert "dependencies" in lint_cmd._PROFILE_PHASES

    def test_cycle_warning_renders_in_text_output(self):
        report = lint_cmd.LintReport(wiki_dir="wiki", src_dir=".")
        lint_cmd._diagnose(report, "dependency_cycles", "Import cycle: a.py ⇄ b.py")
        text = lint_cmd.render_text(report)
        assert "Import cycle: a.py ⇄ b.py" in text
        assert report.diagnostics[0].severity == "warning"

    def test_clean_run_omits_dependency_allclear_lines(self):
        report = lint_cmd.LintReport(wiki_dir="wiki", src_dir=".")
        text = lint_cmd.render_text(report)
        # Optional architecture checks stay silent when they found nothing.
        assert "import cycle" not in text.lower()
        assert "undeclared dependency" not in text.lower()
