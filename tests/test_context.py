"""Tests for the ``context`` command — structured context budgeting."""

from __future__ import annotations

import io
import json
import sys
import textwrap
import types
from pathlib import Path

import pytest

from llm_wiki_cli.commands import context_cmd
from llm_wiki_cli.commands.extract_cmd import ExtractorStatus, InventoryResult
from llm_wiki_cli.services.extraction_jobs import ExtractionJobPlan


# ── Helpers ───────────────────────────────────────────────────────────


def _make_args(**kwargs):
    defaults = {
        "src_dir": ".",
        "budget": 32000,
        "format": "json",
        "focus": "all",
        "request": None,
    }
    defaults.update(kwargs)
    return types.SimpleNamespace(**defaults)


def _write_request(tmp_path, data) -> str:
    path = tmp_path / "context-request.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    return str(path)


def _protocol_request(**overrides):
    data = {
        "protocol": context_cmd.PROTOCOL_VERSION,
        "budget_tokens": 32000,
        "focus": ["all"],
        "format": "json",
    }
    data.update(overrides)
    return data


def _write_query_project(root: Path) -> None:
    (root / "api.py").write_text(
        textwrap.dedent(
            """\
            from repo import save

            __all__ = ["run"]

            def run(payload):
                return save(payload)
            """
        ),
        encoding="utf-8",
    )
    (root / "repo.py").write_text(
        textwrap.dedent(
            """\
            def save(payload):
                return payload
            """
        ),
        encoding="utf-8",
    )


def _write_query_wiki(root: Path, rel_path: str = "docs/llm_wiki") -> Path:
    wiki = root / rel_path
    for subdir in ["entities", "modules", "workflows", "flows", "infrastructure"]:
        (wiki / subdir).mkdir(parents=True, exist_ok=True)
    (wiki / "index.md").write_text("# Index\n\n", encoding="utf-8")
    (wiki / "log.md").write_text("# Log\n\n", encoding="utf-8")
    (wiki / "modules" / "api.md").write_text(
        "# api Module\n\n**Path:** `api.py`\n", encoding="utf-8"
    )
    (wiki / "modules" / "repo.md").write_text(
        "# repo Module\n\n**Path:** `repo.py`\n", encoding="utf-8"
    )
    (wiki / "flows" / "api-run.md").write_text(
        "# api-run\n\nFlow for run.\n", encoding="utf-8"
    )
    (wiki / "dependencies.md").write_text("# Dependencies\n\n", encoding="utf-8")
    (wiki / "load-order.md").write_text("# Load order\n\n", encoding="utf-8")
    return wiki


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
        assert (
            context_cmd._filepath_to_module("llm_wiki_cli/config.py")
            == "llm_wiki_cli.config"
        )

    def test_src_prefix(self):
        assert (
            context_cmd._filepath_to_module("src/llm_wiki_cli/config.py")
            == "llm_wiki_cli.config"
        )

    def test_init(self):
        assert (
            context_cmd._filepath_to_module("src/llm_wiki_cli/__init__.py")
            == "llm_wiki_cli"
        )

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
                "classes": [],
                "functions": [],
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
                "classes": [],
                "functions": [],
                "imports": [{"module": "json", "name": "json", "type": "import"}],
            },
        }
        graph = context_cmd._build_import_graph(inventory)
        assert graph["a.py"] == set()

    def test_nested_module_match(self):
        inventory = {
            "src/pkg/mod.py": {
                "classes": [],
                "functions": [],
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
                "classes": [
                    {
                        "name": "X",
                        "bases": [],
                        "line": 1,
                        "docstring": "D" * 1000,
                        "methods": [{"name": "run", "params": [], "return_type": None}],
                    }
                ],
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
                "a.py": {
                    "priority": "high",
                    "classes": [{"name": "X", "bases": []}],
                    "functions": [],
                },
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

    def test_contains_graph_and_surface_sections(self):
        payload = {
            "budget": 10,
            "used": 0,
            "files": {},
            "graphs": {
                "symbol": {
                    "callers": {"query": "run", "found": True},
                    "callees": {"query": "run", "found": True},
                    "pages": {"query": "run", "found": True},
                },
                "entrypoint": {
                    "flow": {"query": "api-run", "found": True},
                    "data_flow": {"query": "api-run", "found": True},
                },
            },
            "surface": {
                "kind": "flows",
                "count": 1,
                "truncated": False,
                "pages": [
                    {
                        "id": "api-run",
                        "title": "api-run",
                        "canonical_path": "flows/api-run.md",
                        "mcp_uri": "llm-wiki://flows/api-run",
                    }
                ],
            },
        }

        md = context_cmd._render_markdown(payload)

        assert "Documentation Graphs" in md
        assert "Symbol `run`" in md
        assert "Entry point `api-run`" in md
        assert "Surface `flows`" in md
        assert "`flows/api-run.md`" in md


# ── Protocol helpers ──────────────────────────────────────────────────


class TestProtocolValidation:
    def test_protocol_version_remains_context_v1(self):
        assert context_cmd.PROTOCOL_VERSION == "llm-wiki-context/v1"

    def test_language_filter(self):
        inventory = {
            "src/api/users.py": {"language": "python"},
            "web/api/client.ts": {"language": "typescript"},
        }
        result = context_cmd._apply_protocol_filters(inventory, {"language": "python"})
        assert set(result) == {"src/api/users.py"}

    def test_module_filter_matches_dotted_python_module(self):
        inventory = {
            "src/api/users.py": {"language": "python"},
            "src/db/models.py": {"language": "python"},
        }
        result = context_cmd._apply_protocol_filters(inventory, {"module": "api/*"})
        assert set(result) == {"src/api/users.py"}

    def test_module_filter_matches_path_glob(self):
        inventory = {
            "src/api/users.py": {"language": "python"},
            "web/api/client.ts": {"language": "typescript"},
        }
        result = context_cmd._apply_protocol_filters(inventory, {"module": "web/api/*"})
        assert set(result) == {"web/api/client.ts"}

    def test_validation_defaults(self):
        result = context_cmd._validate_protocol_request(
            {
                "protocol": context_cmd.PROTOCOL_VERSION,
                "budget_tokens": 1000,
            }
        )
        assert result["focus"] == ["changed", "neighbors"]
        assert result["format"] == "json"
        assert result["filters"] == {}

    def test_validation_accepts_graph_and_surface_filters(self):
        result = context_cmd._validate_protocol_request(
            _protocol_request(
                filters={
                    "language": "python",
                    "module": "api/*",
                    "symbol": "api.py:run",
                    "entrypoint": "api-run",
                    "surface": "flows",
                }
            )
        )

        assert result["filters"] == {
            "language": "python",
            "module": "api/*",
            "symbol": "api.py:run",
            "entrypoint": "api-run",
            "surface": "flows",
        }


class TestProtocolRun:
    def test_request_file_json_envelope(self, tmp_project, tmp_path, capsys):
        request = _write_request(tmp_path, _protocol_request(budget_tokens=100000))
        context_cmd.run(_make_args(request=request, budget=None))

        data = json.loads(capsys.readouterr().out)
        assert data["protocol"] == context_cmd.PROTOCOL_VERSION
        assert data["ok"] is True
        assert data["budget_tokens"] == 100000
        assert data["format"] == "json"
        assert data["focus"] == ["all"]
        assert "used_tokens" in data
        assert "files" in data
        assert "content" not in data
        assert "graphs" not in data
        assert "surface" not in data
        assert data["files"]

    def test_success_envelope_keeps_old_json_shape_when_enriched(
        self, tmp_project, tmp_path, capsys
    ):
        _write_query_project(tmp_project)
        _write_query_wiki(tmp_project, "agent_wiki")
        request = _write_request(
            tmp_path,
            _protocol_request(
                budget_tokens=100000,
                filters={
                    "symbol": "run",
                    "entrypoint": "api-run",
                    "surface": "flows",
                },
            ),
        )

        context_cmd.run(_make_args(request=request, budget=None, wiki_dir="agent_wiki"))

        data = json.loads(capsys.readouterr().out)
        assert {
            "protocol",
            "ok",
            "budget_tokens",
            "used_tokens",
            "format",
            "focus",
            "filters",
            "files",
        } <= set(data)
        assert data["protocol"] == "llm-wiki-context/v1"
        assert data["ok"] is True
        assert data["graphs"]["symbol"]["callees"]["found"] is True
        assert data["surface"]["kind"] == "flows"

    def test_request_stdin(self, tmp_project, monkeypatch, capsys):
        monkeypatch.setattr(
            "sys.stdin",
            io.StringIO(json.dumps(_protocol_request(budget_tokens=100000))),
        )
        context_cmd.run(_make_args(request="-", budget=None))

        data = json.loads(capsys.readouterr().out)
        assert data["ok"] is True
        assert data["files"]

    def test_request_markdown_envelope(self, tmp_project, tmp_path, capsys):
        request = _write_request(
            tmp_path,
            _protocol_request(budget_tokens=100000, format="markdown"),
        )
        context_cmd.run(_make_args(request=request, budget=None))

        data = json.loads(capsys.readouterr().out)
        assert data["ok"] is True
        assert data["format"] == "markdown"
        assert "content" in data
        assert "files" not in data
        assert "Context Budget" in data["content"]

    def test_request_language_filter_excludes_nonmatching_inventory(
        self, tmp_path, capsys, monkeypatch
    ):
        inventory = {
            "api.py": {
                "language": "python",
                "classes": [{"name": "Api"}],
                "functions": [],
            },
            "web.ts": {
                "language": "typescript",
                "classes": [{"name": "Web"}],
                "functions": [],
            },
        }
        monkeypatch.setattr(
            context_cmd, "get_inventory", lambda *args, **kwargs: inventory
        )
        request = _write_request(
            tmp_path,
            _protocol_request(filters={"language": "python"}),
        )

        context_cmd.run(_make_args(request=request, budget=None))

        data = json.loads(capsys.readouterr().out)
        assert set(data["files"]) == {"api.py"}

    def test_request_module_filter_matches_path_and_module(
        self, tmp_path, capsys, monkeypatch
    ):
        inventory = {
            "src/api/users.py": {
                "language": "python",
                "classes": [{"name": "User"}],
                "functions": [],
            },
            "web/api/client.ts": {
                "language": "typescript",
                "classes": [{"name": "Client"}],
                "functions": [],
            },
            "src/db/models.py": {
                "language": "python",
                "classes": [{"name": "Model"}],
                "functions": [],
            },
        }
        monkeypatch.setattr(
            context_cmd, "get_inventory", lambda *args, **kwargs: inventory
        )

        request = _write_request(
            tmp_path, _protocol_request(filters={"module": "api/*"})
        )
        context_cmd.run(_make_args(request=request, budget=None))
        data = json.loads(capsys.readouterr().out)
        assert set(data["files"]) == {"src/api/users.py"}

        request = _write_request(
            tmp_path, _protocol_request(filters={"module": "web/api/*"})
        )
        context_cmd.run(_make_args(request=request, budget=None))
        data = json.loads(capsys.readouterr().out)
        assert set(data["files"]) == {"web/api/client.ts"}

    def test_request_graph_and_surface_filters_add_sections(
        self, tmp_project, tmp_path, capsys
    ):
        _write_query_project(tmp_project)
        _write_query_wiki(tmp_project, "agent_wiki")
        request = _write_request(
            tmp_path,
            _protocol_request(
                budget_tokens=100000,
                filters={
                    "symbol": "run",
                    "entrypoint": "api-run",
                    "surface": "flows",
                },
            ),
        )

        context_cmd.run(_make_args(request=request, budget=None, wiki_dir="agent_wiki"))

        data = json.loads(capsys.readouterr().out)
        assert data["ok"] is True
        assert "files" in data
        assert data["graphs"]["symbol"]["callees"]["found"] is True
        assert data["graphs"]["symbol"]["pages"]["pages"]
        assert data["graphs"]["entrypoint"]["flow"]["found"] is True
        assert data["graphs"]["entrypoint"]["data_flow"]["found"] is True
        assert data["surface"]["kind"] == "flows"
        assert [page["canonical_path"] for page in data["surface"]["pages"]] == [
            "flows/api-run.md"
        ]

    def test_graph_and_surface_filters_do_not_compete_with_file_budget(
        self, tmp_project, tmp_path, capsys
    ):
        _write_query_project(tmp_project)
        _write_query_wiki(tmp_project, "agent_wiki")
        request = _write_request(
            tmp_path,
            _protocol_request(
                budget_tokens=1,
                filters={
                    "symbol": "run",
                    "entrypoint": "api-run",
                    "surface": "flows",
                },
            ),
        )

        context_cmd.run(_make_args(request=request, budget=None, wiki_dir="agent_wiki"))

        data = json.loads(capsys.readouterr().out)
        assert data["used_tokens"] == 0
        assert data["files"] == {}
        assert data["graphs"]["symbol"]["callees"]["found"] is True
        assert data["graphs"]["entrypoint"]["flow"]["found"] is True
        assert data["surface"]["pages"]

    def test_unknown_graph_filters_return_structured_empty_results(
        self, tmp_project, tmp_path, capsys
    ):
        _write_query_project(tmp_project)
        _write_query_wiki(tmp_project, "agent_wiki")
        request = _write_request(
            tmp_path,
            _protocol_request(
                budget_tokens=100000,
                filters={"symbol": "missing", "entrypoint": "missing"},
            ),
        )

        context_cmd.run(_make_args(request=request, budget=None, wiki_dir="agent_wiki"))

        data = json.loads(capsys.readouterr().out)
        assert data["graphs"]["symbol"]["callers"]["found"] is False
        assert data["graphs"]["symbol"]["callees"]["found"] is False
        assert data["graphs"]["symbol"]["pages"]["pages"] == []
        assert data["graphs"]["entrypoint"]["flow"]["flow"] is None
        assert data["graphs"]["entrypoint"]["data_flow"]["data_flow"] is None

    def test_request_markdown_includes_graph_and_surface_sections(
        self, tmp_project, tmp_path, capsys
    ):
        _write_query_project(tmp_project)
        _write_query_wiki(tmp_project, "agent_wiki")
        request = _write_request(
            tmp_path,
            _protocol_request(
                budget_tokens=100000,
                format="markdown",
                filters={
                    "symbol": "run",
                    "entrypoint": "api-run",
                    "surface": "flows",
                },
            ),
        )

        context_cmd.run(_make_args(request=request, budget=None, wiki_dir="agent_wiki"))

        data = json.loads(capsys.readouterr().out)
        assert "Documentation Graphs" in data["content"]
        assert "Symbol `run`" in data["content"]
        assert "Entry point `api-run`" in data["content"]
        assert "Surface `flows`" in data["content"]

    @pytest.mark.parametrize(
        ("request_data", "field"),
        [
            ({"protocol": "bad", "budget_tokens": 1000}, "protocol"),
            ({"protocol": context_cmd.PROTOCOL_VERSION}, "budget_tokens"),
            (_protocol_request(focus=["neighbors"]), "focus"),
            (_protocol_request(extra=True), "extra"),
            (_protocol_request(filters={"package": "api"}), "filters.package"),
            (_protocol_request(filters={"symbol": ""}), "filters.symbol"),
            (_protocol_request(filters={"entrypoint": ""}), "filters.entrypoint"),
            (_protocol_request(filters={"surface": "bad"}), "filters.surface"),
        ],
    )
    def test_invalid_requests_return_error_envelope(
        self, tmp_path, capsys, request_data, field
    ):
        request = _write_request(tmp_path, request_data)
        with pytest.raises(SystemExit) as exc_info:
            context_cmd.run(_make_args(request=request, budget=None))

        assert exc_info.value.code == 1
        data = json.loads(capsys.readouterr().out)
        assert data["protocol"] == context_cmd.PROTOCOL_VERSION
        assert data["ok"] is False
        assert data["error"]["code"] == "invalid_request"
        assert data["error"]["field"] == field
        assert isinstance(data["error"]["message"], str)

    def test_invalid_json_returns_error_envelope(self, tmp_path, capsys):
        request = tmp_path / "bad-request.json"
        request.write_text("{bad json", encoding="utf-8")

        with pytest.raises(SystemExit) as exc_info:
            context_cmd.run(_make_args(request=str(request), budget=None))

        assert exc_info.value.code == 1
        data = json.loads(capsys.readouterr().out)
        assert data["ok"] is False
        assert data["error"]["field"] == "request"

    def test_extractor_failure_returns_error_envelope(
        self, tmp_path, monkeypatch, capsys
    ):
        result = InventoryResult(
            {},
            {"python": ExtractorStatus("python", "failed", 1, "boom")},
        )
        monkeypatch.setattr(
            context_cmd, "get_inventory_result", lambda *args, **kwargs: result
        )
        request = _write_request(tmp_path, _protocol_request())

        with pytest.raises(SystemExit) as exc_info:
            context_cmd.run(_make_args(request=request, budget=None))

        assert exc_info.value.code == 1
        data = json.loads(capsys.readouterr().out)
        assert data["ok"] is False
        assert data["error"]["field"] == "src_dir"
        assert "python extraction failed: boom" in data["error"]["message"]


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

    def test_json_output_file_suppresses_stdout(self, tmp_project, tmp_path, capsys):
        out_path = tmp_path / "context.json"
        args = _make_args(
            focus="all", budget=100000, output=str(out_path), read_only=True
        )

        context_cmd.run(args)

        captured = capsys.readouterr()
        assert captured.out == ""
        data = json.loads(out_path.read_text(encoding="utf-8"))
        assert data["files"]

    def test_markdown_output_file_suppresses_stdout(
        self, tmp_project, tmp_path, capsys
    ):
        out_path = tmp_path / "context.md"
        args = _make_args(
            focus="all", budget=100000, format="markdown", output=str(out_path)
        )

        context_cmd.run(args)

        captured = capsys.readouterr()
        assert captured.out == ""
        assert "Context Budget" in out_path.read_text(encoding="utf-8")

    def test_run_allows_external_src_with_explicit_flag(
        self, tmp_project, tmp_path, capsys
    ):
        outside = tmp_path / "outside"
        outside.mkdir()
        (outside / "external.py").write_text("class External: pass\n", encoding="utf-8")
        args = _make_args(
            src_dir=str(outside),
            focus="all",
            budget=100000,
            allow_external_src=True,
        )

        context_cmd.run(args)

        data = json.loads(capsys.readouterr().out)
        assert set(data["files"]) == {"external.py"}

    def test_read_only_context_does_not_create_wiki_artifacts(
        self, tmp_project, capsys
    ):
        context_cmd.run(_make_args(focus="all", budget=100000, read_only=True))

        assert not Path("docs").exists()

    def test_changed_focus_warning_goes_to_stderr_json_stays_parseable(
        self, tmp_project, capsys
    ):
        args = _make_args(focus="changed", budget=100000)
        context_cmd.run(args)
        captured = capsys.readouterr()

        data = json.loads(captured.out)
        assert "files" in data
        assert "Extractor plan: requested=1 resolved=1" in captured.err
        assert captured.err.count("Extractor plan:") == 1
        assert "Warning:" in captured.err
        assert "Warning:" not in captured.out

    def test_extractor_plan_is_reported_once_before_context_inventory_work(
        self, tmp_path, monkeypatch, capsys
    ):
        monkeypatch.chdir(tmp_path)
        events = []
        real_reporter = context_cmd.print_extraction_job_plan

        def recording_reporter(plan):
            events.append("report")
            real_reporter(plan)

        def fake_inventory(*args, **kwargs):
            kwargs["plan_reporter"](ExtractionJobPlan())
            events.append("work")
            return InventoryResult(
                {},
                {"python": ExtractorStatus("python", "skipped", 0)},
            )

        monkeypatch.setattr(
            context_cmd, "print_extraction_job_plan", recording_reporter
        )
        monkeypatch.setattr(context_cmd, "get_inventory_result", fake_inventory)

        context_cmd.run(_make_args(focus="all", budget=1000))

        captured = capsys.readouterr()
        assert captured.out.strip() == "{}"
        assert captured.err.count("Extractor plan:") == 1
        assert events == ["report", "work"]

    def test_empty_directory(self, tmp_path, capsys, monkeypatch):
        monkeypatch.chdir(tmp_path)
        args = _make_args(focus="all", budget=1000)
        context_cmd.run(args)
        captured = capsys.readouterr()
        assert captured.out.strip() == "{}"

    def test_budget_required_without_request(self, tmp_project, capsys):
        with pytest.raises(SystemExit) as exc_info:
            context_cmd.run(_make_args(budget=None))

        assert exc_info.value.code == 2
        assert "--budget is required" in capsys.readouterr().err

    def test_extractor_failure_exits_at_cli_boundary(
        self, tmp_project, monkeypatch, capsys
    ):
        result = InventoryResult(
            {},
            {"python": ExtractorStatus("python", "failed", 1, "boom")},
        )
        monkeypatch.setattr(
            context_cmd, "get_inventory_result", lambda *args, **kwargs: result
        )

        with pytest.raises(SystemExit) as exc_info:
            context_cmd.run(_make_args(focus="all", budget=1000))

        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert captured.out == ""
        assert "Error: python extraction failed: boom" in captured.err

    @pytest.mark.parametrize("value", ["0", "-1"])
    def test_cli_rejects_non_positive_budget(self, tmp_project, monkeypatch, value):
        from llm_wiki_cli import cli

        monkeypatch.setattr(sys, "argv", ["llm-wiki", "context", "--budget", value])
        with pytest.raises(SystemExit) as exc_info:
            cli.main()
        assert exc_info.value.code == 2


class TestBuildProtocolEnrichmentRootPropagation:
    def test_propagates_src_root_to_get_entry_points(self, tmp_path, monkeypatch):
        """Regression (2026-07-04): ``_build_protocol_enrichment`` must pass
        ``root=src_root``/``fallback_root=Path.cwd()`` to ``get_entry_points``.
        Dropping those kwargs (as this call site once did) makes the Go/
        Haskell web-server detectors silently miss entry points whenever
        ``llm-wiki context`` runs with an external ``--src-dir`` from a
        different cwd — proven end-to-end for the sibling lint check in
        ``TestLintFlowCoverage::test_go_http_entrypoint_not_stale_for_external_src_dir``
        in test_lint.py. This test pins the wiring at the call site directly.
        """
        monkeypatch.chdir(tmp_path)
        (tmp_path / "wiki").mkdir()

        calls = []
        real_get_entry_points = context_cmd.get_entry_points

        def spy(inventory, **kwargs):
            calls.append(kwargs)
            return real_get_entry_points(inventory, **kwargs)

        monkeypatch.setattr(context_cmd, "get_entry_points", spy)

        src_root = Path("/some/external/src")
        context_cmd._build_protocol_enrichment(
            {}, {"surface": True}, src_root=src_root, wiki_dir="wiki"
        )

        assert len(calls) == 1
        assert calls[0]["root"] == src_root
        assert calls[0]["fallback_root"] == Path.cwd()
