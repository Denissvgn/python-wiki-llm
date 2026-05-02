"""Tests for the ``context`` command — structured context budgeting."""
from __future__ import annotations

import json
import sys
import types

import pytest

from llm_wiki_cli.commands import context_cmd


# ── Helpers ───────────────────────────────────────────────────────────


def _make_args(**kwargs):
    defaults = {
        "src_dir": ".",
        "budget": 32000,
        "format": "json",
        "focus": "all",
    }
    defaults.update(kwargs)
    return types.SimpleNamespace(**defaults)


# ── Token estimation ──────────────────────────────────────────────────


class TestEstimateTokens:
    def test_empty_string(self):
        assert context_cmd._estimate_tokens("") == 0

    def test_short_string(self):
        assert context_cmd._estimate_tokens("hello") == 1  # 5 // 4

    def test_typical_string(self):
        text = "x" * 400
        assert context_cmd._estimate_tokens(text) == 100  # 400 // 4


# ── Filepath to module ────────────────────────────────────────────────


class TestFilepathToModule:
    def test_simple(self):
        assert context_cmd._filepath_to_module("config.py") == "config"

    def test_nested(self):
        assert context_cmd._filepath_to_module("llm_wiki_cli/config.py") == "llm_wiki_cli.config"

    def test_src_prefix(self):
        assert context_cmd._filepath_to_module("src/llm_wiki_cli/config.py") == "llm_wiki_cli.config"

    def test_init(self):
        assert context_cmd._filepath_to_module("src/llm_wiki_cli/__init__.py") == "llm_wiki_cli"

    def test_non_python(self):
        assert context_cmd._filepath_to_module("README.md") is None


# ── Import graph ──────────────────────────────────────────────────────


class TestBuildImportGraph:
    def test_no_imports(self):
        inventory = {
            "a.py": {"classes": [], "functions": [], "imports": []},
            "b.py": {"classes": [], "functions": [], "imports": []},
        }
        graph = context_cmd._build_import_graph(inventory)
        assert graph["a.py"] == set()
        assert graph["b.py"] == set()

    def test_one_import(self):
        inventory = {
            "a.py": {
                "classes": [], "functions": [],
                "imports": [{"module": "b", "name": "foo", "type": "from"}],
            },
            "b.py": {"classes": [], "functions": [], "imports": []},
        }
        graph = context_cmd._build_import_graph(inventory)
        assert "b.py" in graph["a.py"]
        assert "a.py" in graph["b.py"]  # bidirectional

    def test_external_import_skipped(self):
        inventory = {
            "a.py": {
                "classes": [], "functions": [],
                "imports": [{"module": "json", "name": "json", "type": "import"}],
            },
        }
        graph = context_cmd._build_import_graph(inventory)
        assert graph["a.py"] == set()

    def test_nested_module_match(self):
        inventory = {
            "src/pkg/mod.py": {
                "classes": [], "functions": [],
                "imports": [{"module": "pkg.utils", "name": "helper", "type": "from"}],
            },
            "src/pkg/utils.py": {"classes": [], "functions": [], "imports": []},
        }
        graph = context_cmd._build_import_graph(inventory)
        assert "src/pkg/utils.py" in graph["src/pkg/mod.py"]


# ── Classification ────────────────────────────────────────────────────


class TestClassifyFiles:
    def test_focus_all(self):
        files = ["a.py", "b.py", "c.py"]
        result = context_cmd._classify_files(files, None, {}, "all")
        assert all(v == "high" for v in result.values())

    def test_changed_high_neighbor_medium_rest_low(self):
        files = ["a.py", "b.py", "c.py"]
        graph = {
            "a.py": {"b.py"},
            "b.py": {"a.py"},
            "c.py": set(),
        }
        result = context_cmd._classify_files(files, ["a.py"], graph, "changed")
        assert result["a.py"] == "high"
        assert result["b.py"] == "medium"
        assert result["c.py"] == "low"

    def test_no_changed_files(self):
        files = ["a.py", "b.py"]
        result = context_cmd._classify_files(files, [], {}, "changed")
        assert result["a.py"] == "low"
        assert result["b.py"] == "low"


# ── Serializers ───────────────────────────────────────────────────────


class TestSerializers:
    def test_deep_entry_strips_language(self):
        data = {"language": "python", "classes": [{"name": "X"}], "functions": []}
        result = context_cmd._deep_entry(data)
        assert "language" not in result
        assert result["classes"] == [{"name": "X"}]

    def test_slim_entry(self):
        data = {
            "classes": [{"name": "X", "bases": ["Y"], "line": 1, "docstring": "doc"}],
            "functions": [{"name": "f", "line": 5, "docstring": "doc"}],
        }
        result = context_cmd._slim_entry(data)
        assert result["classes"] == [{"name": "X", "bases": ["Y"], "line": 1}]
        assert result["functions"] == [{"name": "f", "line": 5}]

    def test_summary_entry(self):
        data = {
            "classes": [{"name": "A"}, {"name": "B"}],
            "functions": [{"name": "f"}],
        }
        result = context_cmd._summary_entry(data)
        assert result == {"classes": ["A", "B"], "functions": ["f"]}


# ── Budget payload ────────────────────────────────────────────────────


class TestBuildContextPayload:
    def test_all_high_within_budget(self):
        inventory = {
            "a.py": {"classes": [{"name": "X"}], "functions": []},
        }
        classification = {"a.py": "high"}
        result = context_cmd._build_context_payload(inventory, classification, 100000)
        assert result["budget"] == 100000
        assert result["used"] > 0
        assert "a.py" in result["files"]
        assert result["files"]["a.py"]["priority"] == "high"
        assert result["files"]["a.py"]["detail"] == "deep"
        assert result["truncated"] is False
        assert result["omitted_files"] == []
        assert result["downgraded_files"] == {}

    def test_high_downgraded_before_omit(self):
        inventory = {
            "a.py": {
                "classes": [{
                    "name": "X",
                    "bases": [],
                    "line": 1,
                    "docstring": "D" * 1000,
                    "methods": [{"name": "run", "params": [], "return_type": None}],
                }],
                "functions": [],
                "imports": [{"module": "huge", "name": "Huge", "type": "from"}],
            },
        }
        classification = {"a.py": "high"}
        summary = context_cmd._build_entry(inventory["a.py"], "high", "summary")
        budget = context_cmd._entry_tokens("a.py", summary)

        result = context_cmd._build_context_payload(inventory, classification, budget)

        assert "a.py" in result["files"]
        assert result["files"]["a.py"]["detail"] == "summary"
        assert result["downgraded_files"] == {"a.py": "summary"}
        assert result["omitted_files"] == []
        assert result["used"] <= result["budget"]
        assert result["truncated"] is True

    def test_high_omitted_when_summary_does_not_fit(self):
        inventory = {
            "a.py": {"classes": [{"name": "X" * 100}], "functions": []},
        }
        classification = {"a.py": "high"}

        result = context_cmd._build_context_payload(inventory, classification, 1)

        assert result["files"] == {}
        assert result["omitted_files"] == ["a.py"]
        assert result["downgraded_files"] == {}
        assert result["used"] == 0
        assert result["truncated"] is True

    def test_medium_and_low_omitted_on_tight_budget(self):
        inventory = {
            "a.py": {"classes": [{"name": "A"}], "functions": []},
            "b.py": {"classes": [{"name": "B"}], "functions": []},
            "c.py": {"classes": [{"name": "C"}], "functions": []},
        }
        classification = {"a.py": "high", "b.py": "medium", "c.py": "low"}
        high_entry = context_cmd._build_entry(inventory["a.py"], "high", "deep")
        budget = context_cmd._entry_tokens("a.py", high_entry)

        result = context_cmd._build_context_payload(inventory, classification, budget)

        assert "a.py" in result["files"]
        assert "b.py" not in result["files"]
        assert "c.py" not in result["files"]
        assert result["omitted_files"] == ["b.py", "c.py"]
        assert result["used"] <= result["budget"]

    def test_later_smaller_file_included_after_large_omitted_file(self):
        inventory = {
            "a.py": {"classes": [{"name": "X" * 200}], "functions": []},
            "b.py": {"classes": [{"name": "B"}], "functions": []},
        }
        classification = {"a.py": "high", "b.py": "high"}
        small_summary = context_cmd._build_entry(inventory["b.py"], "high", "summary")
        budget = context_cmd._entry_tokens("b.py", small_summary)

        result = context_cmd._build_context_payload(inventory, classification, budget)

        assert "a.py" not in result["files"]
        assert "b.py" in result["files"]
        assert result["files"]["b.py"]["detail"] == "summary"
        assert result["omitted_files"] == ["a.py"]
        assert result["downgraded_files"] == {"b.py": "summary"}
        assert result["used"] <= result["budget"]

    def test_output_has_priority_field(self):
        inventory = {
            "a.py": {"classes": [], "functions": [{"name": "f"}]},
            "b.py": {"classes": [], "functions": [{"name": "g"}]},
        }
        classification = {"a.py": "high", "b.py": "low"}
        result = context_cmd._build_context_payload(inventory, classification, 100000)
        assert result["files"]["a.py"]["priority"] == "high"
        assert result["files"]["b.py"]["priority"] == "low"
        assert result["files"]["a.py"]["detail"] == "deep"
        assert result["files"]["b.py"]["detail"] == "summary"


# ── Markdown rendering ───────────────────────────────────────────────


class TestRenderMarkdown:
    def test_contains_tier_headers(self):
        payload = {
            "budget": 1000,
            "used": 50,
            "files": {
                "a.py": {"priority": "high", "classes": [{"name": "X", "bases": []}], "functions": []},
                "b.py": {"priority": "low", "classes": [], "functions": ["f"]},
            },
        }
        md = context_cmd._render_markdown(payload)
        assert "Changed Files (High Priority)" in md
        assert "Index (Low Priority)" in md
        assert "50 / 1000 tokens" in md

    def test_contains_omitted_files_section(self):
        payload = {
            "budget": 10,
            "used": 0,
            "files": {},
            "omitted_files": ["too_big.py"],
        }
        md = context_cmd._render_markdown(payload)
        assert "Omitted Files" in md
        assert "`too_big.py`" in md


# ── Integration ───────────────────────────────────────────────────────


class TestContextRun:
    def test_focus_all_json(self, tmp_project, capsys):
        args = _make_args(focus="all", budget=100000)
        context_cmd.run(args)
        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert "budget" in data
        assert "used" in data
        assert "files" in data
        # tmp_project has models.py, main.py, utils.py — at least some should appear
        assert len(data["files"]) > 0
        # All should be high priority
        for entry in data["files"].values():
            assert entry["priority"] == "high"

    def test_focus_all_markdown(self, tmp_project, capsys):
        args = _make_args(focus="all", budget=100000, format="markdown")
        context_cmd.run(args)
        captured = capsys.readouterr()
        assert "Changed Files (High Priority)" in captured.out
        assert "tokens" in captured.out

    def test_tight_budget_drops_files(self, tmp_project, capsys):
        args = _make_args(focus="all", budget=50)
        context_cmd.run(args)
        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert data["budget"] == 50
        assert data["used"] <= 50
        assert data["truncated"] is True
        assert data["omitted_files"] or data["downgraded_files"]

    def test_changed_focus_warning_goes_to_stderr_json_stays_parseable(self, tmp_project, capsys):
        args = _make_args(focus="changed", budget=100000)
        context_cmd.run(args)
        captured = capsys.readouterr()

        data = json.loads(captured.out)
        assert "files" in data
        assert "Warning:" in captured.err
        assert "Warning:" not in captured.out

    def test_empty_directory(self, tmp_path, capsys, monkeypatch):
        monkeypatch.chdir(tmp_path)
        args = _make_args(focus="all", budget=1000)
        context_cmd.run(args)
        captured = capsys.readouterr()
        assert captured.out.strip() == "{}"

    @pytest.mark.parametrize("value", ["0", "-1"])
    def test_cli_rejects_non_positive_budget(self, tmp_project, monkeypatch, value):
        from llm_wiki_cli import cli

        monkeypatch.setattr(sys, "argv", ["llm-wiki", "context", "--budget", value])
        with pytest.raises(SystemExit) as exc_info:
            cli.main()
        assert exc_info.value.code == 2
