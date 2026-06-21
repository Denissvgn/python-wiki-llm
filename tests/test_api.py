"""Tests for the supported Python source-adapter API."""

from __future__ import annotations

import textwrap

import pytest

import llm_wiki_cli.api as api
from llm_wiki_cli.api import (
    EXTRACT_SCHEMA_VERSION,
    LlmWikiApiError,
    PathPolicyError,
    build_context,
    build_documentation_query_service,
    callees,
    callers,
    data_flow_for_entrypoint,
    dependency_neighborhood,
    extract_source,
    flow_for_entrypoint,
    list_wiki_pages,
    pages_for_symbol,
)


def _write_query_project(root):
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


def _write_api_wiki(root, rel_path="docs/llm_wiki"):
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


def test_extract_source_returns_stable_payload(tmp_project):
    payload = extract_source(".", summary=True, read_only=True)

    assert payload["schema_version"] == EXTRACT_SCHEMA_VERSION
    assert payload["inventory"]
    first = next(iter(payload["inventory"].values()))
    assert "language" in first


def test_build_context_returns_json_payload(tmp_project):
    payload = build_context(".", budget=100000, focus="all", format="json")

    assert payload["budget"] == 100000
    assert payload["files"]


def test_build_context_returns_markdown_content_and_raw_payload(tmp_project):
    payload = build_context(".", budget=100000, focus="all", format="markdown")

    assert "Context Budget" in payload["content"]
    assert payload["payload"]["files"]


def test_build_context_accepts_graph_filters_and_wiki_dir(tmp_project):
    _write_query_project(tmp_project)
    _write_api_wiki(tmp_project, "agent_wiki")

    payload = build_context(
        ".",
        budget=100000,
        focus="all",
        format="json",
        filters={"symbol": "run", "surface": "flows"},
        wiki_dir="agent_wiki",
    )

    assert payload["graphs"]["symbol"]["callees"]["found"] is True
    assert payload["graphs"]["symbol"]["pages"]["pages"]
    assert payload["surface"]["kind"] == "flows"
    assert [page["canonical_path"] for page in payload["surface"]["pages"]] == [
        "flows/api-run.md"
    ]


def test_list_wiki_pages_returns_registry_metadata_without_running_extraction(
    tmp_project, monkeypatch
):
    _write_api_wiki(tmp_project)

    def fail_if_extracted(*args, **kwargs):  # pragma: no cover - assertion helper
        raise AssertionError("list_wiki_pages must not run source extraction")

    monkeypatch.setattr(api.extract_cmd, "build_extract_payload", fail_if_extracted)

    payload = list_wiki_pages("docs/llm_wiki")

    assert payload["wiki_dir"] == "docs/llm_wiki"
    assert payload["counts"]["by_kind"]["index"] == 1
    assert payload["counts"]["by_kind"]["modules"] == 2
    assert payload["counts"]["by_kind"]["flows"] == 1
    assert payload["counts"]["architecture_pages"] == 2
    assert {
        (page["kind"], page["id"], page["canonical_path"], page["mcp_uri"])
        for page in payload["pages"]
    } >= {
        ("index", "index", "index.md", "llm-wiki://index"),
        ("modules", "api", "modules/api.md", "llm-wiki://modules/api"),
        ("flows", "api-run", "flows/api-run.md", "llm-wiki://flows/api-run"),
        ("dependencies", "dependencies", "dependencies.md", "llm-wiki://dependencies"),
    }


def test_graph_query_service_and_wrappers_return_documentation_answers(tmp_project):
    _write_query_project(tmp_project)
    _write_api_wiki(tmp_project)

    service = build_documentation_query_service(".", wiki_dir="docs/llm_wiki")

    flow = flow_for_entrypoint("api-run", service=service)
    assert flow["found"] is True
    assert flow["flow"]["entry"]["symbol"] == "run"
    assert flow["flow"]["modules_touched"] == ["api.py", "repo.py"]

    data_flow = data_flow_for_entrypoint("run", service=service)
    assert data_flow["found"] is True
    assert data_flow["data_flow"]["entry"]["id"] == "api-run"

    caller_result = callers("save", service=service)
    assert caller_result["found"] is True
    assert caller_result["callers"] == [
        {
            "file": "api.py",
            "module": "api",
            "symbol": "run",
            "kind": "internal",
            "line": 6,
        }
    ]

    callee_result = callees("run", service=service)
    assert callee_result["found"] is True
    assert callee_result["callees"] == [
        {
            "file": "repo.py",
            "module": "repo",
            "symbol": "save",
            "kind": "internal",
            "line": 6,
        }
    ]

    assert dependency_neighborhood("api.py", service=service)["outbound"] == ["repo.py"]
    assert pages_for_symbol("run", service=service)["pages"][0]["canonical_path"] in {
        "flows/api-run.md",
        "modules/api.md",
    }


def test_api_wrappers_map_path_and_query_errors(tmp_project):
    with pytest.raises(PathPolicyError):
        list_wiki_pages("../outside")

    service = build_documentation_query_service(".", wiki_dir="docs/llm_wiki")
    with pytest.raises(LlmWikiApiError, match="symbol must be a non-empty string"):
        callers("", service=service)
