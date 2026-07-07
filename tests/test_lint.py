"""Tests for commands/lint_cmd.py"""

import ast
import hashlib
import inspect
import json
import os
import shutil
import textwrap
import types
from pathlib import Path

import pytest

from llm_wiki_cli import cli
from llm_wiki_cli.config import PathValidationError
from llm_wiki_cli.commands import extract_cmd
from llm_wiki_cli.commands import lint_cmd
from llm_wiki_cli.commands.extract_cmd import ExtractorStatus, InventoryResult
from llm_wiki_cli.services.inventory_cache import CACHE_FILENAME, InventoryCacheStats
from llm_wiki_cli.services import team, wiki_media

TS_NODE_MODULES = (
    Path(__file__).parents[1]
    / "src"
    / "llm_wiki_cli"
    / "extractors"
    / "ts_scripts"
    / "node_modules"
)


def _make_args(**kwargs):
    """Create a simple namespace mimicking argparse output."""
    return types.SimpleNamespace(**kwargs)


def _body_line_count(function) -> int:
    source = textwrap.dedent(inspect.getsource(function))
    function_node = ast.parse(source).body[0]
    assert isinstance(function_node, ast.FunctionDef)
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
    last_body_line = max(stmt.end_lineno or stmt.lineno for stmt in body)
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


class TestJavaScriptFlowDiagnostics:
    def _write_wiki(self, tmp_path: Path) -> Path:
        wiki = tmp_path / "wiki"
        (wiki / "modules").mkdir(parents=True)
        (wiki / "entities").mkdir()
        (wiki / "workflows").mkdir()
        (wiki / "infrastructure").mkdir()
        (wiki / "flows").mkdir()
        (wiki / "modules" / "web-auth-proxy.md").write_text(
            "# web-auth-proxy Module\n", encoding="utf-8"
        )
        (wiki / "index.md").write_text(
            "# Index\n- [web-auth-proxy](modules/web-auth-proxy.md)\n",
            encoding="utf-8",
        )
        (wiki / "log.md").write_text("# Log\n", encoding="utf-8")
        return wiki

    def _mock_inventory(self, monkeypatch, inventory: dict) -> None:
        monkeypatch.setattr(
            lint_cmd,
            "get_inventory_result",
            lambda *a, **k: InventoryResult(
                inventory, {"typescript": ExtractorStatus("typescript", "ok", 1)}
            ),
        )
        monkeypatch.setattr(lint_cmd, "get_docker_inventory", lambda *a, **k: {})
        monkeypatch.setattr(
            lint_cmd, "get_yaml_infrastructure_inventory", lambda *a, **k: {}
        )

    def test_warns_when_javascript_create_server_pattern_is_not_raw_node_http(
        self, tmp_path, monkeypatch
    ):
        wiki = self._write_wiki(tmp_path)
        inventory = {
            "docker/web-auth-proxy.js": {
                "language": "javascript",
                "imports": [{"module": "custom-framework", "name": "framework"}],
                "classes": [],
                "functions": [{"name": "rewriteJsonPayload", "kind": "function"}],
                "module_calls": [
                    {"name": "createServer", "target": "server", "line": 14}
                ],
            }
        }
        self._mock_inventory(monkeypatch, inventory)
        monkeypatch.setattr(lint_cmd, "get_entry_points", lambda *a, **k: [])

        report = lint_cmd.build_report(str(wiki), str(tmp_path))

        diagnostics = [
            item
            for item in report.diagnostics
            if item.category == "javascript_flow_unsupported"
        ]
        assert [(item.target, item.severity) for item in diagnostics] == [
            ("docker/web-auth-proxy.js", "warning")
        ]
        assert "raw http.createServer/https.createServer" in diagnostics[0].message
        assert "entry-point detector" in diagnostics[0].message
        text = lint_cmd.render_text(report)
        assert "JavaScript HTTP flow detection" in text
        assert "Found 1 JavaScript flow diagnostic(s)." in text

    def test_skips_javascript_flow_warning_for_raw_node_http_server(
        self, tmp_path, monkeypatch
    ):
        wiki = self._write_wiki(tmp_path)
        inventory = {
            "docker/web-auth-proxy.js": {
                "language": "javascript",
                "imports": [{"module": "node:http", "name": "http"}],
                "classes": [],
                "functions": [{"name": "rewriteJsonPayload", "kind": "function"}],
                "module_calls": [
                    {"name": "createServer", "target": "server", "line": 14}
                ],
            }
        }
        self._mock_inventory(monkeypatch, inventory)

        report = lint_cmd.build_report(str(wiki), str(tmp_path))

        assert [
            item
            for item in report.diagnostics
            if item.category == "javascript_flow_unsupported"
        ] == []

    def test_skips_javascript_flow_warning_when_entrypoint_covers_file(
        self, tmp_path, monkeypatch
    ):
        wiki = self._write_wiki(tmp_path)
        inventory = {
            "docker/web-auth-proxy.js": {
                "language": "javascript",
                "classes": [],
                "functions": [{"name": "rewriteJsonPayload", "kind": "function"}],
                "module_calls": [
                    {"name": "createServer", "target": "server", "line": 14}
                ],
            }
        }
        self._mock_inventory(monkeypatch, inventory)
        monkeypatch.setattr(
            lint_cmd,
            "get_entry_points",
            lambda *a, **k: [
                {
                    "id": "node-proxy",
                    "category": "http",
                    "file": "docker/web-auth-proxy.js",
                    "symbol": "server",
                    "label": "node-proxy",
                }
            ],
        )

        report = lint_cmd.build_report(str(wiki), str(tmp_path))

        assert [
            item
            for item in report.diagnostics
            if item.category == "javascript_flow_unsupported"
        ] == []


class TestUnsupportedSources:
    def test_shell_unsupported_sources_are_path_specific_strict_diagnostics(
        self, tmp_path
    ):
        scripts = tmp_path / "scripts"
        scripts.mkdir()
        (scripts / "deploy.sh").write_text("#!/bin/sh\n", encoding="utf-8")

        wiki = tmp_path / "wiki"
        for dirname in ("entities", "modules", "workflows", "infrastructure"):
            (wiki / dirname).mkdir(parents=True)
        (wiki / "index.md").write_text("# Index\n", encoding="utf-8")
        (wiki / "log.md").write_text("# Log\n", encoding="utf-8")

        from llm_wiki_cli.commands.sync_cmd import SyncManifest

        SyncManifest.build_from_inventory({}, str(tmp_path), {}, {}).save(wiki)

        report = lint_cmd.build_report(str(wiki), str(tmp_path), strict=True)

        diagnostics = [
            diagnostic
            for diagnostic in report.diagnostics
            if diagnostic.category == "unsupported_sources"
        ]
        assert report.passed is True
        assert report.issue_count == 0
        assert [(item.path, item.target, item.severity) for item in diagnostics] == [
            ("scripts/deploy.sh", "shell", "info")
        ]
        assert "scripts/deploy.sh" in diagnostics[0].message
        assert "Unsupported sources detected" in lint_cmd.render_text(report)

    def test_generated_javascript_bundles_are_info_diagnostics(
        self, tmp_path, monkeypatch
    ):
        generated = tmp_path / "services" / "dashboard" / "static" / "assets"
        generated.mkdir(parents=True)
        (generated / "index-D0zaI3XT.js").write_text(
            "function a(){};export{a as Ko};\n", encoding="utf-8"
        )

        wiki = tmp_path / "wiki"
        for dirname in ("entities", "modules", "workflows", "infrastructure"):
            (wiki / dirname).mkdir(parents=True)
        (wiki / "index.md").write_text("# Index\n", encoding="utf-8")
        (wiki / "log.md").write_text("# Log\n", encoding="utf-8")

        from llm_wiki_cli.commands.sync_cmd import SyncManifest

        SyncManifest.build_from_inventory({}, str(tmp_path), {}, {}).save(wiki)

        monkeypatch.setattr(
            lint_cmd,
            "get_inventory_result",
            lambda *args, **kwargs: InventoryResult(
                inventory={},
                statuses={
                    "typescript": ExtractorStatus("typescript", "ok", 0),
                },
            ),
        )

        report = lint_cmd.build_report(str(wiki), str(tmp_path), strict=True)

        diagnostics = [
            diagnostic
            for diagnostic in report.diagnostics
            if diagnostic.category == "unsupported_sources"
        ]
        assert report.passed is True
        assert report.issue_count == 0
        assert [(item.path, item.target, item.severity) for item in diagnostics] == [
            (
                "services/dashboard/static/assets/index-D0zaI3XT.js",
                "generated JavaScript bundle",
                "info",
            )
        ]
        assert "generated JavaScript bundle" in diagnostics[0].message
        assert "generated_javascript_bundle" not in diagnostics[0].message

    def test_lint_reports_missing_haskell_helper_as_extractor_failure(
        self, tmp_path, monkeypatch
    ):
        monkeypatch.chdir(tmp_path)
        wiki = tmp_path / "wiki"
        wiki.mkdir()
        app_dir = tmp_path / "hls-analysis" / "app"
        app_dir.mkdir(parents=True)
        (app_dir / "Main.hs").write_text("module Main where\n", encoding="utf-8")

        report = lint_cmd.build_report(str(wiki), ".")

        diagnostics = [
            diagnostic
            for diagnostic in report.diagnostics
            if diagnostic.category == "unsupported_sources"
        ]
        assert diagnostics == []
        assert report.passed is False
        assert report.issue_count == 1
        issue = report.issues[0]
        assert issue.category == "extractor_failure"
        assert issue.target == "haskell"
        assert "prepare-extractors --language haskell" in issue.message
        assert "Unsupported sources detected" not in lint_cmd.render_text(report)


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

    def test_guide_broken_link_is_detected(self, tmp_path, monkeypatch, capsys):
        monkeypatch.chdir(tmp_path)
        wiki = tmp_path / "wiki"
        (wiki / "guides").mkdir(parents=True)
        (wiki / "guides" / "operator-onboarding.md").write_text(
            "# Operator Onboarding\n\n- [missing](../modules/missing.md)\n"
        )
        (wiki / "index.md").write_text(
            "# Index\n- [Guide](guides/operator-onboarding.md)\n"
        )
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


class TestLintMediaLinks:
    def _stub_source_inputs(self, monkeypatch):
        monkeypatch.setattr(
            lint_cmd,
            "get_inventory_result",
            lambda *a, **k: InventoryResult(
                {}, {"python": ExtractorStatus("python", "skipped", 0)}
            ),
        )
        monkeypatch.setattr(lint_cmd, "get_docker_inventory", lambda *a, **k: {})
        monkeypatch.setattr(
            lint_cmd, "get_yaml_infrastructure_inventory", lambda *a, **k: {}
        )

    def _wiki_with_guide(self, tmp_path: Path) -> tuple[Path, Path]:
        src = tmp_path / "src"
        src.mkdir()
        wiki = tmp_path / "wiki"
        (wiki / "guides").mkdir(parents=True)
        (wiki / "assets" / "guides" / "tour").mkdir(parents=True)
        (wiki / "index.md").write_text(
            "# Index\n\n- [Tour](guides/tour.md)\n", encoding="utf-8"
        )
        (wiki / "log.md").write_text("# Log\n", encoding="utf-8")
        return src, wiki

    def test_media_links_are_classified_and_markdown_titles_are_stripped(
        self, tmp_path, monkeypatch
    ):
        self._stub_source_inputs(monkeypatch)
        src, wiki = self._wiki_with_guide(tmp_path)
        (wiki / "assets" / "guides" / "tour" / "ok.png").write_bytes(b"ok")
        (wiki / "guides" / "tour.md").write_text(
            "# Tour\n\n"
            '![Screenshot](../assets/guides/tour/ok.png "Home screen")\n'
            "![Missing](../assets/guides/tour/missing.png)\n"
            "[Missing page](missing-page.md)\n",
            encoding="utf-8",
        )

        report = lint_cmd.build_report(wiki, str(src))

        assert sorted(
            (issue.category, issue.path, issue.target) for issue in report.issues
        ) == [
            ("broken_links", "guides/tour.md", "missing-page.md"),
            (
                "media_link_broken",
                "guides/tour.md",
                "../assets/guides/tour/missing.png",
            ),
        ]

    def test_plain_markdown_links_to_media_are_existence_checked(
        self, tmp_path, monkeypatch
    ):
        self._stub_source_inputs(monkeypatch)
        src, wiki = self._wiki_with_guide(tmp_path)
        (wiki / "assets" / "guides" / "tour" / "demo.webm").write_bytes(b"video")
        (wiki / "guides" / "tour.md").write_text(
            "# Tour\n\n"
            "[Demo recording](../assets/guides/tour/demo.webm)\n"
            "[Missing demo](../assets/guides/tour/missing.mp4)\n",
            encoding="utf-8",
        )

        report = lint_cmd.build_report(wiki, str(src))

        assert [
            (issue.category, issue.path, issue.target) for issue in report.issues
        ] == [
            (
                "media_link_broken",
                "guides/tour.md",
                "../assets/guides/tour/missing.mp4",
            ),
        ]
        assert [
            item for item in report.diagnostics if item.category == "media_orphan"
        ] == []
        assert [
            item
            for item in report.diagnostics
            if item.category == "media_missing_alt_text"
        ] == []

    def test_parenthesized_media_targets_are_not_truncated(self, tmp_path, monkeypatch):
        self._stub_source_inputs(monkeypatch)
        src, wiki = self._wiki_with_guide(tmp_path)
        (wiki / "assets" / "guides" / "tour" / "shot(1).png").write_bytes(b"png")
        (wiki / "assets" / "guides" / "tour" / "demo(1).webm").write_bytes(b"webm")
        (wiki / "guides" / "tour.md").write_text(
            "# Tour\n\n"
            "![Screenshot](../assets/guides/tour/shot(1).png)\n"
            "[Demo](../assets/guides/tour/demo(1).webm)\n",
            encoding="utf-8",
        )

        report = lint_cmd.build_report(wiki, str(src))

        assert report.issues == []
        assert [
            item for item in report.diagnostics if item.category == "media_orphan"
        ] == []

    def test_fenced_media_examples_are_ignored_by_media_lint(
        self, tmp_path, monkeypatch
    ):
        self._stub_source_inputs(monkeypatch)
        src, wiki = self._wiki_with_guide(tmp_path)
        (wiki / "assets" / "example.png").write_bytes(b"example")
        (wiki / "guides" / "tour.md").write_text(
            "# Tour\n\n"
            "```html\n"
            '<img src="../assets/missing-from-fence.png">\n'
            "```\n\n"
            "```markdown\n"
            "![Example](../assets/example.png)\n"
            "[Demo](../assets/fenced-demo.webm)\n"
            "```\n\n"
            "![Missing](../assets/unfenced-missing.png)\n",
            encoding="utf-8",
        )

        report = lint_cmd.build_report(wiki, str(src))

        assert [(issue.category, issue.target) for issue in report.issues] == [
            ("media_link_broken", "../assets/unfenced-missing.png")
        ]
        assert [
            (item.category, item.path)
            for item in report.diagnostics
            if item.category == "media_orphan"
        ] == [("media_orphan", "assets/example.png")]

    def test_reference_style_images_are_validated_and_count_as_references(
        self, tmp_path, monkeypatch
    ):
        self._stub_source_inputs(monkeypatch)
        src, wiki = self._wiki_with_guide(tmp_path)
        (wiki / "assets" / "guides" / "tour" / "home.png").write_bytes(b"png")
        (wiki / "assets" / "guides" / "tour" / "collapsed.png").write_bytes(b"png")
        (wiki / "guides" / "tour.md").write_text(
            "# Tour\n\n"
            "![Home][hero image]\n"
            "![Collapsed][]\n"
            "![Missing][missing]\n\n"
            '[hero image]: ../assets/guides/tour/home.png "Home"\n'
            "[collapsed]: ../assets/guides/tour/collapsed.png\n"
            "[missing]: ../assets/guides/tour/missing.png\n",
            encoding="utf-8",
        )

        report = lint_cmd.build_report(wiki, str(src))

        assert [
            (issue.category, issue.path, issue.target) for issue in report.issues
        ] == [
            (
                "media_link_broken",
                "guides/tour.md",
                "../assets/guides/tour/missing.png",
            )
        ]
        assert [
            item for item in report.diagnostics if item.category == "media_orphan"
        ] == []

    def test_raw_html_media_embeds_missing_alt_and_oversize_are_validated(
        self, tmp_path, monkeypatch
    ):
        self._stub_source_inputs(monkeypatch)
        src, wiki = self._wiki_with_guide(tmp_path)
        (wiki / "assets" / "guides" / "tour" / "large.png").write_bytes(b"12345")
        (wiki / "assets" / "guides" / "tour" / "clip.webm").write_bytes(b"video")
        (wiki / "guides" / "tour.md").write_text(
            "# Tour\n\n"
            '<img src="../assets/guides/tour/large.png">\n'
            '<video src="../assets/guides/tour/missing.webm"></video>\n'
            '<video><source src="../assets/guides/tour/clip.webm"></video>\n',
            encoding="utf-8",
        )

        report = lint_cmd.build_report(wiki, str(src), media_size_warn_bytes=4)

        assert [
            (issue.category, issue.path, issue.target) for issue in report.issues
        ] == [
            (
                "media_link_broken",
                "guides/tour.md",
                "../assets/guides/tour/missing.webm",
            )
        ]
        diagnostics = [
            (item.category, item.path, item.target, item.severity)
            for item in report.diagnostics
            if item.category.startswith("media_")
        ]
        assert diagnostics == [
            (
                "media_missing_alt_text",
                "guides/tour.md",
                "../assets/guides/tour/large.png",
                "warning",
            ),
            (
                "media_oversize",
                "guides/tour.md",
                "../assets/guides/tour/large.png",
                "warning",
            ),
            (
                "media_oversize",
                "guides/tour.md",
                "../assets/guides/tour/clip.webm",
                "warning",
            ),
        ]

    def test_raw_html_srcset_candidates_are_validated(self, tmp_path, monkeypatch):
        self._stub_source_inputs(monkeypatch)
        src, wiki = self._wiki_with_guide(tmp_path)
        (wiki / "assets" / "guides" / "tour" / "fallback.png").write_bytes(b"png")
        (wiki / "assets" / "guides" / "tour" / "small.png").write_bytes(b"small")
        (wiki / "guides" / "tour.md").write_text(
            "# Tour\n\n"
            '<img alt="Responsive" src="../assets/guides/tour/fallback.png" '
            'srcset="../assets/guides/tour/small.png 1x, '
            "../assets/guides/tour/missing.png 2x, "
            'https://cdn.example/remote.png 3x, data:image/png;base64,AAAA 4x">\n',
            encoding="utf-8",
        )

        report = lint_cmd.build_report(wiki, str(src))

        assert [
            (issue.category, issue.path, issue.target) for issue in report.issues
        ] == [
            (
                "media_link_broken",
                "guides/tour.md",
                "../assets/guides/tour/missing.png",
            )
        ]
        assert [
            item for item in report.diagnostics if item.category == "media_orphan"
        ] == []

    def test_media_outside_assets_warns_once_per_page(self, tmp_path, monkeypatch):
        self._stub_source_inputs(monkeypatch)
        src, wiki = self._wiki_with_guide(tmp_path)
        (wiki / "guides" / "pic.png").write_bytes(b"png")
        (wiki / "assets" / "guides" / "tour" / "canonical.png").write_bytes(b"png")
        (wiki / "guides" / "tour.md").write_text(
            "# Tour\n\n"
            "![Local](pic.png)\n"
            "![Local again](pic.png)\n"
            "![Canonical](../assets/guides/tour/canonical.png)\n",
            encoding="utf-8",
        )

        report = lint_cmd.build_report(wiki, str(src))

        assert report.issues == []
        assert [
            (item.category, item.path, item.target, item.severity)
            for item in report.diagnostics
            if item.category == "media_outside_assets"
        ] == [
            (
                "media_outside_assets",
                "guides/tour.md",
                "guides/pic.png",
                "warning",
            )
        ]

    def test_orphan_asset_is_a_warning_and_empty_asset_tree_is_compatible(
        self, tmp_path, monkeypatch
    ):
        self._stub_source_inputs(monkeypatch)
        src, wiki = self._wiki_with_guide(tmp_path)
        (wiki / "guides" / "tour.md").write_text("# Tour\n", encoding="utf-8")

        no_asset_report = lint_cmd.build_report(wiki, str(src))
        assert no_asset_report.issues == []
        assert [
            item
            for item in no_asset_report.diagnostics
            if item.category == "media_orphan"
        ] == []

        (wiki / "assets" / "guides" / "tour" / "unused.png").write_bytes(b"unused")
        orphan_report = lint_cmd.build_report(wiki, str(src))

        assert orphan_report.issues == []
        assert [
            (item.path, item.target, item.severity)
            for item in orphan_report.diagnostics
            if item.category == "media_orphan"
        ] == [
            (
                "assets/guides/tour/unused.png",
                "guides/tour.md",
                "warning",
            )
        ]

    def test_all_asset_files_are_inventoried_with_unrecognized_type_warnings(
        self, tmp_path, monkeypatch
    ):
        self._stub_source_inputs(monkeypatch)
        src, wiki = self._wiki_with_guide(tmp_path)
        (wiki / "guides" / "tour.md").write_text("# Tour\n", encoding="utf-8")
        (wiki / "assets" / "guides" / "tour" / "unused.png").write_bytes(b"unused")
        (wiki / "assets" / "guides" / "tour" / "notes.txt").write_text(
            "notes", encoding="utf-8"
        )
        (wiki / "assets" / "guides" / "tour" / "README.md").write_text(
            "readme", encoding="utf-8"
        )
        (wiki / "assets" / "guides" / "tour" / ".hidden.png").write_bytes(b"hidden")
        (wiki / "assets" / ".hidden" / "secret.txt").parent.mkdir(parents=True)
        (wiki / "assets" / ".hidden" / "secret.txt").write_text(
            "secret", encoding="utf-8"
        )

        report = lint_cmd.build_report(wiki, str(src))

        assert [
            (item.category, item.path)
            for item in report.diagnostics
            if item.category in {"media_orphan", "asset_unrecognized_type"}
        ] == [
            ("asset_unrecognized_type", "assets/guides/tour/notes.txt"),
            ("media_orphan", "assets/guides/tour/unused.png"),
        ]

    def test_symlinked_media_escape_warns_without_counting_reference(
        self, tmp_path, monkeypatch
    ):
        self._stub_source_inputs(monkeypatch)
        src, wiki = self._wiki_with_guide(tmp_path)
        outside = tmp_path / "outside"
        outside.mkdir()
        (outside / "escape.png").write_bytes(b"png")
        link = wiki / "assets" / "escape.png"
        try:
            link.symlink_to(outside / "escape.png")
        except (OSError, NotImplementedError) as exc:
            pytest.skip(f"symlinks unavailable: {exc}")
        (wiki / "guides" / "tour.md").write_text(
            "# Tour\n\n![Escape](../assets/escape.png)\n", encoding="utf-8"
        )

        report = lint_cmd.build_report(wiki, str(src))

        assert report.issues == []
        assert [
            (item.category, item.path, item.target, item.severity)
            for item in report.diagnostics
            if item.category == "media_symlink_escape"
        ] == [
            (
                "media_symlink_escape",
                "guides/tour.md",
                "../assets/escape.png",
                "warning",
            )
        ]

    def test_lint_reuses_collected_media_references_for_asset_index(
        self, tmp_path, monkeypatch
    ):
        self._stub_source_inputs(monkeypatch)
        src, wiki = self._wiki_with_guide(tmp_path)
        (wiki / "assets" / "guides" / "tour" / "ok.png").write_bytes(b"ok")
        (wiki / "guides" / "tour.md").write_text(
            "# Tour\n\n![Screenshot](../assets/guides/tour/ok.png)\n",
            encoding="utf-8",
        )
        calls = 0
        original = wiki_media.collect_media_references

        def counted_collect(*args, **kwargs):
            nonlocal calls
            calls += 1
            return original(*args, **kwargs)

        monkeypatch.setattr(wiki_media, "collect_media_references", counted_collect)

        report = lint_cmd.build_report(wiki, str(src))

        assert report.issues == []
        assert calls == len(list(wiki.rglob("*.md")))

    def test_wiki_media_local_link_path_ignores_all_schemes(self):
        assert wiki_media.local_link_path("https://example.com/image.png") is None
        assert wiki_media.local_link_path("data:image/png;base64,AAAA") is None
        assert wiki_media.local_link_path("mailto:docs@example.com") is None
        assert wiki_media.local_link_path("custom:target.png") is None

    def test_lint_run_uses_default_media_size_when_cli_option_is_omitted(
        self, tmp_path, monkeypatch, capsys
    ):
        monkeypatch.chdir(tmp_path)
        self._stub_source_inputs(monkeypatch)
        src, wiki = self._wiki_with_guide(tmp_path)
        (wiki / "assets" / "guides" / "tour" / "ok.png").write_bytes(b"ok")
        (wiki / "guides" / "tour.md").write_text(
            "# Tour\n\n![Screenshot](../assets/guides/tour/ok.png)\n",
            encoding="utf-8",
        )

        lint_cmd.run(
            _make_args(
                wiki_dir=wiki.name,
                src_dir=src.name,
                media_size_warn_bytes=None,
            )
        )

        assert "No broken media links" in capsys.readouterr().out


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
            seen["helper_cache_dir"] = kwargs["helper_cache_dir"]
            seen["include_tests"] = kwargs["include_tests"]
            return lint_cmd.LintReport(
                wiki_dir=str(wiki_dir), src_dir=src_dir, strict=kwargs["strict"]
            )

        monkeypatch.setattr(lint_cmd, "build_report", fake_build_report)

        lint_cmd.run(
            _make_args(
                wiki_dir="wiki",
                src_dir=".",
                helper_cache_dir=str(tmp_path / "helper-cache"),
                include_tests=["go"],
                jobs=2,
            )
        )

        assert seen["parallel_jobs"] == 2
        assert seen["helper_cache_dir"] == str(tmp_path / "helper-cache")
        assert seen["include_tests"] == ["go"]

    def test_build_report_passes_helper_cache_dir_to_inventory(
        self, tmp_path, monkeypatch
    ):
        monkeypatch.chdir(tmp_path)
        wiki = tmp_path / "wiki"
        wiki.mkdir()
        seen = {}

        def fake_inventory(*args, **kwargs):
            seen["helper_cache_dir"] = kwargs["helper_cache_dir"]
            seen["include_tests"] = kwargs["include_tests"]
            return InventoryResult(
                {},
                {"python": ExtractorStatus("python", "skipped", 0)},
                InventoryCacheStats(enabled=False, status="disabled"),
            )

        monkeypatch.setattr(lint_cmd, "get_inventory_result", fake_inventory)
        monkeypatch.setattr(lint_cmd, "get_docker_inventory", lambda *a, **k: {})

        lint_cmd.build_report(
            wiki,
            ".",
            helper_cache_dir=str(tmp_path / "helper-cache"),
            include_tests={"go"},
        )

        assert seen["helper_cache_dir"] == str(tmp_path / "helper-cache")
        assert set(seen["include_tests"]) == {"go"}

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

    def test_cli_lint_allow_external_src_parses_with_jobs_auto(self, monkeypatch):
        seen = {}
        monkeypatch.setattr(cli.os, "cpu_count", lambda: 4)
        monkeypatch.setattr(
            cli.lint_cmd,
            "run",
            lambda args: seen.update(
                allow_external_src=args.allow_external_src,
                jobs=args.jobs,
            ),
        )
        monkeypatch.setattr(
            "sys.argv",
            ["llm-wiki", "lint", "--allow-external-src", "--jobs", "auto"],
        )

        cli.main()

        assert seen == {"allow_external_src": True, "jobs": 4}

    def test_lint_allow_external_src_reaches_report_build(
        self, tmp_path, monkeypatch, capsys
    ):
        runner = tmp_path / "runner"
        external = tmp_path / "external"
        wiki_dir = runner / "wiki"
        runner.mkdir()
        external.mkdir()
        wiki_dir.mkdir()
        monkeypatch.chdir(runner)
        seen = {}

        def fake_build_report(wiki_dir, src_dir, **kwargs):
            seen["wiki_dir"] = wiki_dir
            seen["src_dir"] = src_dir
            return lint_cmd.LintReport(
                wiki_dir=str(wiki_dir),
                src_dir=src_dir,
                strict=kwargs["strict"],
            )

        monkeypatch.setattr(lint_cmd, "build_report", fake_build_report)

        lint_cmd.run(
            _make_args(
                src_dir=os.path.relpath(external, runner),
                wiki_dir="wiki",
                allow_external_src=True,
            )
        )

        assert "Lint passed" in capsys.readouterr().out
        assert Path(seen["src_dir"]) == external.resolve()
        assert seen["wiki_dir"] == Path("wiki")

    def test_lint_external_source_without_opt_in_still_fails_closed(
        self, tmp_path, monkeypatch
    ):
        runner = tmp_path / "runner"
        external = tmp_path / "external"
        runner.mkdir()
        external.mkdir()
        (runner / "wiki").mkdir()
        monkeypatch.chdir(runner)
        monkeypatch.setattr(
            lint_cmd,
            "build_report",
            lambda *a, **k: pytest.fail(
                "path validation should run before build_report"
            ),
        )

        with pytest.raises(PathValidationError) as exc_info:
            lint_cmd.run(
                _make_args(
                    src_dir=os.path.relpath(external, runner),
                    wiki_dir="wiki",
                )
            )

        message = str(exc_info.value)
        assert "--src-dir" in message
        assert "outside the project root" in message

    def test_lint_allow_external_src_still_validates_wiki_path(
        self, tmp_path, monkeypatch
    ):
        monkeypatch.chdir(tmp_path)
        outside = tmp_path.parent / f"{tmp_path.name}-outside"
        outside.mkdir()
        monkeypatch.setattr(
            lint_cmd,
            "build_report",
            lambda *a, **k: pytest.fail(
                "path validation should run before build_report"
            ),
        )

        with pytest.raises(PathValidationError) as exc_info:
            lint_cmd.run(
                _make_args(
                    src_dir=".",
                    wiki_dir=str(outside),
                    allow_external_src=True,
                )
            )

        message = str(exc_info.value)
        assert "--wiki-dir" in message
        assert "outside the project root" in message

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


class TestLintGeneratedDiagrams:
    def _write_wiki(self, tmp_path, entity_body: str, module_body: str) -> None:
        wiki = tmp_path / "wiki"
        (wiki / "entities").mkdir(parents=True)
        (wiki / "modules").mkdir()
        (wiki / "workflows").mkdir()
        (wiki / "infrastructure").mkdir()
        (wiki / "entities" / "User.md").write_text(entity_body, encoding="utf-8")
        (wiki / "modules" / "app.md").write_text(module_body, encoding="utf-8")
        (wiki / "index.md").write_text(
            "# Index\n- [User](entities/User.md)\n- [app](modules/app.md)\n",
            encoding="utf-8",
        )
        (wiki / "log.md").write_text("# Log\n", encoding="utf-8")

    def _mock_inventory(self, monkeypatch) -> None:
        monkeypatch.setattr(
            lint_cmd,
            "get_inventory_result",
            lambda *a, **k: InventoryResult(
                {
                    "app.py": {
                        "language": "python",
                        "classes": [{"name": "User"}],
                        "functions": [],
                    }
                },
                {"python": ExtractorStatus("python", "ok", 1)},
            ),
        )
        monkeypatch.setattr(lint_cmd, "get_docker_inventory", lambda *a, **k: {})

    def test_generated_diagram_click_link_is_hard_broken_link(
        self, tmp_path, monkeypatch
    ):
        monkeypatch.chdir(tmp_path)
        self._mock_inventory(monkeypatch)
        self._write_wiki(
            tmp_path,
            "# User\n\n"
            "## Relationships\n\n"
            "<!-- Auto-generated relationship summary. Do not edit by hand. -->\n"
            "```mermaid\n"
            "flowchart LR\n"
            '    n0["User"]\n'
            '    n1["Missing"]\n'
            "    n1 --> n0\n"
            '    click n1 "../modules/missing.md"\n'
            "```\n",
            "# app\n",
        )

        report = lint_cmd.build_report("wiki", ".")

        broken = [issue for issue in report.issues if issue.category == "broken_links"]
        assert [(issue.path, issue.target) for issue in broken] == [
            ("entities/User.md", "../modules/missing.md")
        ]
        assert "generated diagram" in broken[0].message
        assert report.passed is False

    def test_generated_diagram_bloat_is_warning_not_failure(
        self, tmp_path, monkeypatch
    ):
        monkeypatch.chdir(tmp_path)
        self._mock_inventory(monkeypatch)
        nodes = "\n".join(f'    n{i}["Node {i}"]' for i in range(41))
        self._write_wiki(
            tmp_path,
            "# User\n",
            "# app\n\n"
            "## Local dependency map\n\n"
            "<!-- Auto-generated local dependency summary. Do not edit by hand. -->\n"
            "```mermaid\n"
            "flowchart LR\n"
            f"{nodes}\n"
            "```\n",
        )

        report = lint_cmd.build_report("wiki", ".")

        diagnostics = [
            diagnostic
            for diagnostic in report.diagnostics
            if diagnostic.category == "generated_diagram_bloat"
        ]
        assert report.passed is True
        assert [
            (diagnostic.path, diagnostic.target, diagnostic.severity)
            for diagnostic in diagnostics
        ] == [("modules/app.md", "Local dependency map", "warning")]
        assert "node declarations" in diagnostics[0].message
        assert "41" in diagnostics[0].message
        assert "rerun `llm-wiki sync`" in diagnostics[0].message

    def test_missing_generated_sections_are_clean_for_old_wikis(
        self, tmp_path, monkeypatch
    ):
        monkeypatch.chdir(tmp_path)
        self._mock_inventory(monkeypatch)
        self._write_wiki(tmp_path, "# User\n", "# app\n")

        report = lint_cmd.build_report("wiki", ".")

        assert report.passed is True
        assert report.count("broken_links") == 0
        assert [
            diagnostic
            for diagnostic in report.diagnostics
            if diagnostic.category == "generated_diagram_bloat"
        ] == []

    def test_profile_includes_generated_diagram_phase_and_diagnostics(
        self, tmp_path, monkeypatch, capsys
    ):
        monkeypatch.chdir(tmp_path)
        self._mock_inventory(monkeypatch)
        nodes = "\n".join(f'    n{i}["Node {i}"]' for i in range(41))
        self._write_wiki(
            tmp_path,
            "# User\n",
            "# app\n\n"
            "## Local dependency map\n\n"
            "<!-- Auto-generated local dependency summary. Do not edit by hand. -->\n"
            "```mermaid\n"
            "flowchart LR\n"
            f"{nodes}\n"
            "```\n",
        )

        lint_cmd.run(_make_args(wiki_dir="wiki", src_dir=".", profile=True))

        payload = json.loads(capsys.readouterr().out)
        phase_names = {phase["name"] for phase in payload["profile"]["phases"]}
        assert "generated_diagrams" in phase_names
        assert payload["diagnostics"][0]["category"] == "generated_diagram_bloat"
        assert payload["diagnostics"][0]["path"] == "modules/app.md"

    def test_generated_diagram_bloat_renders_in_text_output(self):
        report = lint_cmd.LintReport(wiki_dir="wiki", src_dir=".")
        lint_cmd._diagnose(
            report,
            "generated_diagram_bloat",
            "Generated diagram bloat in modules/app.md ## Local dependency map",
            path="modules/app.md",
            target="Local dependency map",
        )

        text = lint_cmd.render_text(report)

        assert "Generated diagram bloat in modules/app.md" in text
        assert "Found 1 generated diagram warning(s)." in text


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

    def test_go_http_entrypoint_not_stale_for_external_src_dir(
        self, tmp_path, monkeypatch
    ):
        """Regression: dogfooded on TeamCrush via wiki-bootstrap +
        onboarding-guide (2026-07-04). ``_check_flow_coverage`` built its
        "detected" set with ``get_entry_points(deep_inventory, ...)`` and
        omitted ``root=src_dir``/``fallback_root``, so it defaulted to
        ``root="."``. The Go/Haskell web-server detectors read raw source
        text relative to ``root`` (inventory metadata alone isn't enough),
        so with an external ``--src-dir`` invoked from a different cwd the
        Go entry point silently vanished from the detected set and its
        documented flow page was flagged stale even though the entry point
        was still live in source. Calls ``_check_flow_coverage`` directly
        with a synthetic inventory (as ``test_entrypoints.py`` does for the
        detector itself) so the test doesn't require a prepared Go helper
        toolchain — with a real ``--src-dir`` extraction, a missing Go
        helper fails extraction outright before this check would even run.
        """
        cwd = tmp_path / "cwd"
        cwd.mkdir()
        monkeypatch.chdir(cwd)

        external_src = tmp_path / "external_src"
        server = external_src / "internal" / "web" / "server.go"
        server.parent.mkdir(parents=True)
        server.write_text(
            textwrap.dedent("""\
            package web

            import "net/http"

            func dashboard(w http.ResponseWriter, r *http.Request) {}

            func main() {
                http.HandleFunc("/dashboard", dashboard)
                srv := &http.Server{Addr: ":8080"}
                _ = srv.ListenAndServe()
            }
            """),
            encoding="utf-8",
        )
        deep_inventory = {
            "internal/web/server.go": {
                "language": "go",
                "imports": [{"module": "net/http", "name": "http"}],
                "functions": [{"name": "dashboard"}, {"name": "main"}],
                "classes": [],
            }
        }

        wiki = cwd / "wiki"
        (wiki / "flows").mkdir(parents=True)
        (wiki / "flows" / "http-dashboard.md").write_text("# http-dashboard\n")
        (wiki / "flows" / "http-http.Server.md").write_text("# http-http.Server\n")

        report = lint_cmd.LintReport(wiki_dir=str(wiki), src_dir=str(external_src))
        lint_cmd._check_flow_coverage(report, wiki, deep_inventory, str(external_src))
        assert report.count("stale_flows") == 0

    def test_data_flow_diagnostics_propagates_src_dir_root(self, tmp_path, monkeypatch):
        """Regression (2026-07-04): sibling of
        ``test_go_http_entrypoint_not_stale_for_external_src_dir`` — the
        ``data_flow_gaps`` check shares the same ``get_entry_points`` call
        pattern and needed the same ``root=src_dir``/``fallback_root`` fix.
        Pins the wiring at this call site with a spy, since the full
        detector-level behavior is already proven end-to-end above.
        """
        cwd = tmp_path / "cwd"
        cwd.mkdir()
        monkeypatch.chdir(cwd)
        external_src = tmp_path / "external_src"
        external_src.mkdir()

        wiki = cwd / "wiki"
        (wiki / "flows").mkdir(parents=True)
        (wiki / "flows" / "http-http.Server.md").write_text("# http-http.Server\n")

        calls = []
        real_get_entry_points = lint_cmd.get_entry_points

        def spy(inventory, **kwargs):
            calls.append(kwargs)
            return real_get_entry_points(inventory, **kwargs)

        monkeypatch.setattr(lint_cmd, "get_entry_points", spy)

        report = lint_cmd.LintReport(wiki_dir=str(wiki), src_dir=str(external_src))
        lint_cmd._check_data_flow_diagnostics(report, wiki, {}, str(external_src))

        assert len(calls) == 1
        assert calls[0]["root"] == str(external_src)
        assert calls[0]["fallback_root"] == Path.cwd()


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

    def test_unresolved_typescript_path_alias_is_specific_warning(self, tmp_path):
        wiki = tmp_path / "wiki"
        wiki.mkdir()
        (wiki / "dependencies.md").write_text("# Dependencies\n", encoding="utf-8")
        frontend = tmp_path / "frontend"
        frontend.mkdir()
        (frontend / "tsconfig.json").write_text(
            """
            {
              "compilerOptions": {
                "baseUrl": ".",
                "paths": {
                  "@/*": ["./src/*"]
                }
              }
            }
            """,
            encoding="utf-8",
        )
        inventory = {
            "frontend/src/App.tsx": {
                "language": "typescript",
                "imports": [{"module": "@/missing/widget", "name": "Widget"}],
            },
        }
        report = lint_cmd.LintReport(wiki_dir=str(wiki), src_dir=str(tmp_path))

        lint_cmd._check_dependency_coverage(report, wiki, inventory, str(tmp_path))

        alias_warnings = [
            d for d in report.diagnostics if d.category == "unresolved_path_aliases"
        ]
        undeclared = [
            d for d in report.diagnostics if d.category == "undeclared_dependencies"
        ]
        assert [(d.target, d.severity) for d in alias_warnings] == [
            ("@/missing/widget", "warning")
        ]
        assert [d.target for d in undeclared] == []
        assert report.passed

    @pytest.mark.skipif(
        not (TS_NODE_MODULES / "ts-morph").exists() or shutil.which("node") is None,
        reason="Node.js/ts-morph dependencies not installed",
    )
    def test_typescript_src_lib_alias_resolves_under_root_lib_ignore(self, tmp_path):
        (tmp_path / ".gitignore").write_text("lib/\n", encoding="utf-8")
        wiki = tmp_path / "wiki"
        wiki.mkdir()
        (wiki / "dependencies.md").write_text("# Dependencies\n", encoding="utf-8")
        frontend = tmp_path / "frontend"
        src = frontend / "src"
        (src / "hooks").mkdir(parents=True)
        (src / "lib").mkdir()
        (frontend / "tsconfig.json").write_text(
            textwrap.dedent("""\
            {
              "compilerOptions": {
                "baseUrl": ".",
                "paths": {
                  "@/*": ["./src/*"]
                }
              }
            }
            """),
            encoding="utf-8",
        )
        (src / "hooks" / "useAuth.ts").write_text(
            textwrap.dedent("""\
            import api from '@/lib/api';

            export function useAuth() {
              return api;
            }
            """),
            encoding="utf-8",
        )
        (src / "lib" / "api.ts").write_text(
            textwrap.dedent("""\
            const api = {};

            export default api;
            """),
            encoding="utf-8",
        )

        inventory = extract_cmd.get_inventory(str(tmp_path), deep=True)
        report = lint_cmd.LintReport(wiki_dir=str(wiki), src_dir=str(tmp_path))

        lint_cmd._check_dependency_coverage(report, wiki, inventory, str(tmp_path))

        assert "frontend/src/lib/api.ts" in inventory
        assert [
            d.target
            for d in report.diagnostics
            if d.category == "unresolved_path_aliases"
        ] == []
        assert report.passed

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

    def test_dependency_coverage_ignores_manifests_under_gitignored_projects(
        self, tmp_path
    ):
        wiki = tmp_path / "wiki"
        wiki.mkdir()
        (wiki / "dependencies.md").write_text("# Dependencies\n", encoding="utf-8")
        (tmp_path / ".gitignore").write_text(
            "projects/\n!projects/.gitkeep\n", encoding="utf-8"
        )
        ignored = tmp_path / "projects" / "test-project"
        ignored.mkdir(parents=True)
        (ignored / "pyproject.toml").write_text(
            """
            [project]
            dependencies = [
                "boto3",
                "pandas",
                "pyarrow",
                "python-dotenv",
            ]
            """,
            encoding="utf-8",
        )
        (ignored / "package.json").write_text(
            """
            {
              "dependencies": {
                "@aws-sdk/client-s3": "^3.700.0",
                "apache-arrow": "^18.0.0",
                "dotenv": "^16.4.0"
              }
            }
            """,
            encoding="utf-8",
        )
        inventory = {
            "docker/web-auth-proxy.js": {"language": "javascript", "imports": []},
        }
        report = lint_cmd.LintReport(wiki_dir=str(wiki), src_dir=str(tmp_path))

        lint_cmd._check_dependency_coverage(report, wiki, inventory, str(tmp_path))

        unused = [d for d in report.diagnostics if d.category == "unused_dependencies"]
        assert unused == []
        assert report.issues == []
        assert report.passed

    def test_python_dependencies_are_used_when_go_files_share_import_stems(
        self, tmp_path
    ):
        wiki = tmp_path / "wiki"
        wiki.mkdir()
        (wiki / "dependencies.md").write_text("# Dependencies\n", encoding="utf-8")
        (tmp_path / "rlm").mkdir()
        (tmp_path / "rlm" / "requirements.txt").write_text(
            "anthropic\nopenai\n",
            encoding="utf-8",
        )
        inventory = {
            "rlm/gateway.py": {
                "language": "python",
                "imports": [
                    {"module": "anthropic", "name": "anthropic"},
                    {"module": "openai", "name": "openai"},
                ],
            },
            "internal/llm/anthropic.go": {"language": "go", "imports": []},
            "internal/llm/openai.go": {"language": "go", "imports": []},
        }
        report = lint_cmd.LintReport(wiki_dir=str(wiki), src_dir=str(tmp_path))

        lint_cmd._check_dependency_coverage(report, wiki, inventory, str(tmp_path))

        unused = [d for d in report.diagnostics if d.category == "unused_dependencies"]
        undeclared = [
            d for d in report.diagnostics if d.category == "undeclared_dependencies"
        ]
        assert [d.target for d in unused] == []
        assert [d.target for d in undeclared] == []
        assert report.issues == []
        assert report.passed

    def test_dependency_coverage_reconciles_python_service_aliases_and_local_dists(
        self, tmp_path
    ):
        wiki = tmp_path / "wiki"
        wiki.mkdir()
        (wiki / "dependencies.md").write_text("# Dependencies\n", encoding="utf-8")
        dialogue = tmp_path / "services" / "dialogue"
        shared = tmp_path / "services" / "shared"
        (dialogue / "src" / "dialogue").mkdir(parents=True)
        (shared / "src" / "shared").mkdir(parents=True)
        (dialogue / "pyproject.toml").write_text(
            textwrap.dedent("""\
            [project]
            name = "dialogue-service"
            dependencies = [
                "assistant-shared",
                "grpcio",
                "prometheus-client",
            ]

            [tool.setuptools.packages.find]
            where = ["src"]
            """),
            encoding="utf-8",
        )
        (shared / "pyproject.toml").write_text(
            textwrap.dedent("""\
            [project]
            name = "assistant-shared"
            dependencies = ["pydantic-settings"]

            [tool.setuptools.packages.find]
            where = ["src"]
            """),
            encoding="utf-8",
        )
        (shared / "src" / "shared" / "__init__.py").write_text("", encoding="utf-8")
        inventory = {
            "services/dialogue/src/dialogue/main.py": {
                "language": "python",
                "imports": [
                    {"module": "grpc", "name": "grpc"},
                    {"module": "prometheus_client", "name": "Counter"},
                    {"module": "shared.config", "name": "get_settings"},
                ],
            },
            "services/shared/src/shared/config.py": {
                "language": "python",
                "imports": [
                    {"module": "pydantic_settings", "name": "BaseSettings"},
                ],
            },
        }
        report = lint_cmd.LintReport(wiki_dir=str(wiki), src_dir=str(tmp_path))

        lint_cmd._check_dependency_coverage(report, wiki, inventory, str(tmp_path))

        assert [
            d.target
            for d in report.diagnostics
            if d.category == "undeclared_dependencies"
        ] == []
        assert [
            d.target for d in report.diagnostics if d.category == "unused_dependencies"
        ] == []
        assert report.issues == []
        assert report.passed

    def test_undeclared_dependency_warning_includes_file_and_manifest_scope(
        self, tmp_path
    ):
        wiki = tmp_path / "wiki"
        wiki.mkdir()
        (wiki / "dependencies.md").write_text("# Dependencies\n", encoding="utf-8")
        service = tmp_path / "services" / "dialogue"
        service.mkdir(parents=True)
        (service / "pyproject.toml").write_text(
            textwrap.dedent("""\
            [project]
            name = "dialogue-service"
            dependencies = ["requests"]
            """),
            encoding="utf-8",
        )
        inventory = {
            "services/dialogue/src/dialogue/main.py": {
                "language": "python",
                "imports": [{"module": "httpx", "name": "httpx"}],
            },
        }
        report = lint_cmd.LintReport(wiki_dir=str(wiki), src_dir=str(tmp_path))

        lint_cmd._check_dependency_coverage(report, wiki, inventory, str(tmp_path))

        undeclared = [
            d for d in report.diagnostics if d.category == "undeclared_dependencies"
        ]
        assert [(d.target, d.severity) for d in undeclared] == [("httpx", "warning")]
        assert "services/dialogue/src/dialogue/main.py" in undeclared[0].message
        assert "services/dialogue" in undeclared[0].message
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

    def test_dependency_checks_reuse_single_lint_inventory_extraction(
        self, tmp_project, monkeypatch
    ):
        wiki = tmp_project / "wiki"
        for dirname in ["entities", "modules", "workflows", "infrastructure"]:
            (wiki / dirname).mkdir(parents=True)
        (wiki / "dependencies.md").write_text("# Dependencies\n", encoding="utf-8")
        (wiki / "load-order.md").write_text("# Load order\n", encoding="utf-8")
        (wiki / "index.md").write_text("# Index\n", encoding="utf-8")
        (wiki / "log.md").write_text("# Log\n", encoding="utf-8")

        calls = 0
        real_get_inventory_result = lint_cmd.get_inventory_result

        def counted_get_inventory_result(*args, **kwargs):
            nonlocal calls
            calls += 1
            return real_get_inventory_result(*args, **kwargs)

        monkeypatch.setattr(
            lint_cmd, "get_inventory_result", counted_get_inventory_result
        )

        report = lint_cmd.build_report(str(wiki), ".", strict=False)

        assert calls == 1
        assert any(
            diagnostic.category == "undeclared_dependencies"
            for diagnostic in report.diagnostics
        )
