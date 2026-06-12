from __future__ import annotations

import json
import types
from pathlib import Path

import pytest

from llm_wiki_cli.commands import bootstrap_cmd, ci_check_cmd, generate_prompt_cmd, lint_cmd, metrics_cmd, review_cmd
from llm_wiki_cli.services import metrics


def _args(**kwargs):
    return types.SimpleNamespace(**kwargs)


def _bootstrap(wiki_dir: str = "docs/llm_wiki"):
    bootstrap_cmd.run(_args(src_dir=".", wiki_dir=wiki_dir, overwrite=False, depth="full", skip_workflows=False))


class TestStrictLintReport:
    def test_build_report_exposes_structured_issues(self, tmp_project):
        wiki = tmp_project / "wiki"
        (wiki / "entities").mkdir(parents=True)
        (wiki / "index.md").write_text("# Index\n")

        report = lint_cmd.build_report(wiki, ".", strict=True)

        assert not report.passed
        assert report.issue_count > 0
        assert any(issue.category == "wiki_structure" for issue in report.issues)
        assert lint_cmd.report_to_dict(report)["ok"] is False

    def test_strict_passes_after_bootstrap_manifest(self, tmp_project):
        _bootstrap()

        report = lint_cmd.build_report("docs/llm_wiki", ".", strict=True)

        assert report.passed


class TestCiCheck:
    def test_writes_report_and_exits_zero_when_strict_passes(self, tmp_project, capsys):
        _bootstrap()

        ci_check_cmd.run(_args(src_dir=".", wiki_dir="docs/llm_wiki", format="text", report=".git/report.md"))

        assert Path(".git/report.md").exists()
        assert "Lint passed" in capsys.readouterr().out

    def test_exits_nonzero_and_writes_report_on_failure(self, tmp_project):
        wiki = tmp_project / "wiki"
        (wiki / "entities").mkdir(parents=True)
        (wiki / "index.md").write_text("# Index\n")

        with pytest.raises(SystemExit) as exc:
            ci_check_cmd.run(_args(src_dir=".", wiki_dir=str(wiki), format="json", report=".git/report.md"))

        assert exc.value.code == 1
        assert Path(".git/report.md").exists()


class TestMetrics:
    def test_records_and_summarizes_local_events(self, tmp_project):
        _bootstrap()
        metrics.record_event("trigger_start", {"agent": "claude", "mode": "CLI"})
        metrics.record_event("trigger_finish", {"agent": "claude", "mode": "CLI", "duration_ms": 1200, "exit_code": 0})
        metrics.record_validation_event(
            command="lint",
            passed=True,
            issue_count=0,
            strict=True,
            duration_ms=10,
            wiki_dir="docs/llm_wiki",
            src_dir=".",
        )

        events = metrics.load_events(last="30d")
        summary = metrics.summarize_events(events, src_dir=".", wiki_dir="docs/llm_wiki")

        assert summary["accuracy"]["strict_validation_pass_percent"] == 100.0
        assert summary["speed"]["average_successful_sync_ms"] == 1200.0
        assert summary["coverage"]["percent"] == 100.0

    def test_record_event_ignores_metrics_mkdir_oserror(self, tmp_project, monkeypatch):
        def fail_mkdir(self, *args, **kwargs):
            raise OSError("read-only")

        monkeypatch.setattr(Path, "mkdir", fail_mkdir)

        metrics.record_event("trigger_start", {"agent": "claude"})

    def test_record_event_ignores_metrics_append_oserror(self, tmp_project, monkeypatch):
        def fail_open(self, *args, **kwargs):
            raise OSError("read-only")

        monkeypatch.setattr(Path, "open", fail_open)

        metrics.record_event("trigger_start", {"agent": "claude"})

    def test_metrics_command_json_output(self, tmp_project, capsys):
        _bootstrap()
        capsys.readouterr()
        metrics.record_validation_event(
            command="ci-check",
            passed=False,
            issue_count=2,
            strict=True,
            duration_ms=5,
            wiki_dir="docs/llm_wiki",
            src_dir=".",
        )

        metrics_cmd.run(_args(last="30d", format="json", src_dir=".", wiki_dir="docs/llm_wiki"))

        payload = json.loads(capsys.readouterr().out)
        assert payload["accuracy"]["failures"] == 1


class TestSmartPromptTemplates:
    def test_auto_detects_dependency_change(self):
        diff = "diff --git a/package.json b/package.json\n--- a/package.json\n+++ b/package.json\n@@\n+{}"

        assert generate_prompt_cmd.detect_change_type(diff) == "dependency"

    def test_manual_change_type_adds_specific_guidance(self):
        prompt = generate_prompt_cmd._build_prompt(
            "docs/llm_wiki",
            ".",
            change_type="bugfix",
            diff_text="",
        )

        assert "Change type: `bugfix`" in prompt
        assert "accuracy over broad coverage churn" in prompt


class TestReviewMode:
    def test_cross_module_workflow_lookup_scales_with_unique_symbols(self, tmp_project, monkeypatch):
        source_count = 5
        import_count = 12
        workflow_count = 8
        source_paths = [f"source_{index}.py" for index in range(source_count)]
        imported_modules = [f"dep_{index}" for index in range(import_count)]
        imported_paths = [f"{module}.py" for module in imported_modules]
        inventory = {path: {"classes": []} for path in source_paths + imported_paths}
        module_page_map = {path: Path(path).stem for path in inventory}
        wiki_dir = tmp_project / "docs" / "llm_wiki"
        (wiki_dir / "modules").mkdir(parents=True, exist_ok=True)
        for path in source_paths:
            (wiki_dir / "modules" / f"{Path(path).stem}.md").write_text("# module\n", encoding="utf-8")

        checks = {"count": 0}

        class CountingWorkflowText:
            def __init__(self, text: str):
                self.text = text

            def __contains__(self, needle: object) -> bool:
                checks["count"] += 1
                return str(needle) in self.text

        workflow_text = " ".join(Path(path).stem for path in source_paths)
        workflows = {
            f"workflows/flow_{index}.md": CountingWorkflowText(workflow_text)
            for index in range(workflow_count)
        }

        def diff_for(path: str) -> str:
            lines = [
                f"diff --git a/{path} b/{path}",
                f"--- a/{path}",
                f"+++ b/{path}",
                "@@",
            ]
            lines.extend(f"+import {module}" for module in imported_modules)
            return "\n".join(lines)

        monkeypatch.setattr(review_cmd, "get_inventory", lambda src_dir, deep=True: inventory)
        monkeypatch.setattr(review_cmd, "build_module_page_map", lambda current_inventory: module_page_map)
        monkeypatch.setattr(review_cmd, "build_entity_page_map", lambda current_inventory: {})
        monkeypatch.setattr(review_cmd, "_workflow_pages", lambda current_wiki_dir: workflows)

        findings = review_cmd.build_findings(
            "\n".join(diff_for(path) for path in source_paths),
            src_dir=".",
            wiki_dir=str(wiki_dir),
        )

        cross_module_findings = [
            finding for finding in findings if "cross-module import" in finding.reason
        ]
        assert len(cross_module_findings) == source_count * import_count
        assert checks["count"] <= (source_count + import_count) * workflow_count

    def test_review_flags_documented_source_without_wiki_changes(self, tmp_project):
        _bootstrap()
        diff = """diff --git a/models.py b/models.py
--- a/models.py
+++ b/models.py
@@
+class Order:
+    pass
"""

        findings = review_cmd.build_findings(diff, src_dir=".", wiki_dir="docs/llm_wiki")

        assert any("related wiki page" in finding.reason.lower() for finding in findings)

    def test_review_flags_dependency_change_without_infra_wiki(self, tmp_project):
        _bootstrap()
        diff = """diff --git a/pyproject.toml b/pyproject.toml
--- a/pyproject.toml
+++ b/pyproject.toml
@@
+requests = "*"
"""

        findings = review_cmd.build_findings(diff, src_dir=".", wiki_dir="docs/llm_wiki")

        assert any(finding.source_path == "pyproject.toml" for finding in findings)

    def test_review_run_reads_patch_from_stdin_json(self, tmp_project, monkeypatch, capsys):
        _bootstrap()
        capsys.readouterr()
        diff = """diff --git a/pyproject.toml b/pyproject.toml
--- a/pyproject.toml
+++ b/pyproject.toml
@@
+requests = "*"
"""
        monkeypatch.setattr("sys.stdin", types.SimpleNamespace(read=lambda: diff))

        review_cmd.run(_args(src_dir=".", wiki_dir="docs/llm_wiki", patch="-", base=None, head=None, format="json"))

        payload = json.loads(capsys.readouterr().out)
        assert payload["findings"]
