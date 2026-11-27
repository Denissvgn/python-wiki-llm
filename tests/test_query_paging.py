"""Paged and compact typed and impact documentation queries."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

import pytest

from llm_wiki_cli import api
from llm_wiki_cli.services import mcp_server
from llm_wiki_engine.knowledge_storage_lifecycle import migrate_knowledge_storage
from llm_wiki_engine.query_result_format import validate_documentation_query_result

_IMPORTERS = 12
_RESULT_LIMIT = 64 * 1024
_TYPED = {
    "operation": "typed",
    "value": "modules/core.md",
    "direction": "incoming",
    "kinds": ["imports"],
    "limit": 100,
}
_PATHS = [f"mod_{index}.py" for index in range(1, _IMPORTERS + 1)]


@pytest.fixture(scope="module")
def project(tmp_path_factory):
    root = tmp_path_factory.mktemp("paging")
    source = root / "src"
    source.mkdir()
    (source / "core.py").write_text(
        "def shared(value: int) -> int:\n    return value * 2\n"
    )
    for name in _PATHS:
        (source / name).write_text(
            "import core\n\n\n"
            f"def run_{name[:-3]}(value: int) -> int:\n"
            "    return core.shared(value)\n"
        )
    (root / "empty").mkdir()
    previous = Path.cwd()
    os.chdir(root)
    try:
        api.bootstrap_wiki("src", "wiki")
        migrate_knowledge_storage(Path("wiki"), to="packed-v4", recovery_dir=Path("recovery"))
        yield root
    finally:
        os.chdir(previous)


@pytest.fixture
def in_project(project, monkeypatch):
    monkeypatch.chdir(project)
    return project


def _query(request: dict[str, Any]) -> Any:
    result = api.query_documentation(request, src_dir="empty", wiki_dir="wiki")
    validate_documentation_query_result(result)
    assert _size(result) <= _RESULT_LIMIT
    return result


def _size(result: object) -> int:
    return len(
        json.dumps(
            result, ensure_ascii=False, separators=(",", ":"), sort_keys=True
        ).encode("utf-8")
    )


def _walk(request: dict[str, Any], key: str) -> tuple[list[Any], list[Any]]:
    """Follow every follow-up; return all records and each page's result."""

    records: list[Any] = []
    results: list[Any] = []
    while True:
        result = _query(request)
        results.append(result)
        records.extend(result[key])
        follow_up = result.get("follow_up")
        if not follow_up or follow_up["status"] != "available":
            return records, results
        assert follow_up["request"]["offset"] == request.get("offset", 0) + len(
            result[key]
        )
        request = follow_up["request"]


def _keys(records: list[Any]) -> list[str]:
    return sorted(json.dumps(record, sort_keys=True) for record in records)


def test_typed_pages_by_count_cover_every_edge_once(in_project):
    complete = _query({**_TYPED, "projection": "compact"})["edges"]
    assert len(complete) == _IMPORTERS

    edges, results = _walk({**_TYPED, "limit": 5, "projection": "compact"}, "edges")

    assert [len(result["edges"]) for result in results] == [5, 5, 2]
    assert _keys(edges) == _keys(complete)
    assert results[0]["bounds"]["edges"] == {"total": 12, "returned": 5, "truncated": True}
    assert results[-1]["follow_up"] == {"status": "unavailable", "reason": "no-more-records"}


def test_typed_pages_past_the_byte_limit_cover_every_edge_once(in_project):
    edges, results = _walk(dict(_TYPED), "edges")

    assert len(results) > 1
    assert results[0]["truncated"] is True
    assert "result_omitted" not in results[0]
    assert len(edges) == _IMPORTERS
    assert len(set(_keys(edges))) == _IMPORTERS
    assert {edge["related_concept"]["locator"] for edge in edges} == {
        f"llm-wiki://modules/{name[:-3]}" for name in _PATHS
    }


def test_compact_projection_keeps_identity_and_drops_whole_wiki_records(in_project):
    result = _query({**_TYPED, "projection": "compact"})

    assert "follow_up" not in result
    assert result["truncated"] is False
    for concept in (result["concept"], *(edge["related_concept"] for edge in result["edges"])):
        assert {"locator", "canonical_path", "source_path", "title"} <= set(concept)
        assert not {"implementation", "maintenance", "freshness"} & set(concept)
    full = _query({**_TYPED, "limit": 1})
    assert "implementation" in full["edges"][0]["related_concept"]


def test_a_complete_result_without_offset_carries_no_follow_up(in_project):
    result = _query({**_TYPED, "limit": 1, "kinds": ["imports"], "direction": "outgoing"})

    assert result["edges"] == []
    assert "follow_up" not in result


def test_an_offset_past_the_last_record_returns_an_empty_final_page(in_project):
    result = _query({**_TYPED, "offset": 50, "projection": "compact"})

    assert result["edges"] == []
    assert result["bounds"]["edges"]["total"] == _IMPORTERS
    assert result["follow_up"] == {"status": "unavailable", "reason": "no-more-records"}


@pytest.mark.parametrize("read", ["full", "selected"])
def test_impact_pages_cover_every_record_once(in_project, read):
    request = {"operation": "impact", "paths": _PATHS, "limit": 100, "read": read}
    complete = _query({**request, "projection": "compact"})
    assert len(complete["concepts"]) == _IMPORTERS

    concepts, results = _walk({**request, "limit": 5, "projection": "compact"}, "concepts")
    pages, _ = _walk({**request, "limit": 5, "projection": "compact"}, "pages")

    assert len(results) == 3
    assert _keys(concepts) == _keys(complete["concepts"])
    assert _keys(pages) == _keys(complete["pages"])


def test_impact_follow_up_from_a_diff_names_the_resolved_paths(in_project):
    diff = "".join(
        f"diff --git a/{name} b/{name}\n--- a/{name}\n+++ b/{name}\n"
        "@@ -1 +1 @@\n-import core\n+import core  # changed\n"
        for name in _PATHS
    )

    result = _query({"operation": "impact", "diff": diff, "limit": 5})

    follow_up = result["follow_up"]
    assert follow_up["status"] == "available"
    assert "diff" not in follow_up["request"]
    assert follow_up["request"]["paths"] == sorted(_PATHS)
    assert follow_up["request"]["offset"] == 5


@pytest.mark.parametrize(
    ("options", "field"),
    [
        ({"offset": -1}, "offset"),
        ({"offset": "5"}, "offset"),
        ({"offset": True}, "offset"),
        ({"offset": 1_000_001}, "offset"),
        ({"projection": "tiny"}, "projection"),
    ],
)
@pytest.mark.parametrize("operation", ["typed", "impact"])
def test_paging_request_errors_match_across_api_and_mcp(operation, options, field):
    request = (
        {**_TYPED, **options}
        if operation == "typed"
        else {"operation": "impact", "paths": ["app.py"], **options}
    )

    with pytest.raises(api.InvalidRequestError) as python_error:
        api.query_documentation(request)
    with pytest.raises(mcp_server.McpWikiError) as mcp_error:
        mcp_server.McpWikiService().query_documentation(request)

    assert python_error.value.code == "invalid-request"
    assert python_error.value.details == {"field": field}
    assert mcp_error.value.code == python_error.value.code
    assert mcp_error.value.data == python_error.value.details
