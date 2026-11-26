"""Impact answered from a selected read of committed knowledge."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from llm_wiki_cli import api
from llm_wiki_cli.services import mcp_server
from llm_wiki_engine import knowledge_storage_access
from llm_wiki_engine.knowledge_storage import KnowledgeStorageError
from llm_wiki_engine.knowledge_storage_lifecycle import migrate_knowledge_storage
from llm_wiki_engine.query_result_format import validate_documentation_query_result
from tests.developer_value.fixtures import POLICY_SOURCE

_IDENTITY = (
    "locator",
    "concept_kind",
    "title",
    "page_kind",
    "page_id",
    "canonical_path",
    "mcp_uri",
    "source_path",
    "role",
    "origin",
    "evidence",
    "verification",
    "lifecycle",
)
_HELPER_SOURCE = "def helper(value: int) -> int:\n    return value + 1\n"


def _bytes(root: Path) -> dict[str, bytes]:
    return {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in root.rglob("*")
        if path.is_file()
    }


def _project(tmp_path, monkeypatch, capsys, storage):
    monkeypatch.chdir(tmp_path)
    source = tmp_path / "src"
    source.mkdir()
    (source / "policy.py").write_text(POLICY_SOURCE)
    (source / "helper.py").write_text(_HELPER_SOURCE)
    api.bootstrap_wiki("src", "wiki")
    capsys.readouterr()
    if storage != "flat-v1":
        migrate_knowledge_storage(
            Path("wiki"), to=storage, recovery_dir=Path("recovery")
        )
    # An empty source root keeps both reads on the committed snapshot.
    (tmp_path / "empty").mkdir()
    return tmp_path / "wiki"


def _impact(paths, **options) -> Any:
    return api.query_documentation(
        {"operation": "impact", "paths": paths, "limit": 100, **options},
        src_dir="empty",
        wiki_dir="wiki",
    )


@pytest.mark.parametrize("storage", ["flat-v1", "sharded-v2", "packed-v4"])
def test_selected_read_matches_the_full_read_on_the_fields_it_returns(
    tmp_path, monkeypatch, capsys, storage
):
    wiki = _project(tmp_path, monkeypatch, capsys, storage)
    before = _bytes(wiki)
    paths = ["policy.py", "helper.py", "missing.py"]

    selected = _impact(paths, read="selected")
    full = _impact(paths)

    validate_documentation_query_result(selected)
    assert selected["query"]["read"] == "selected"
    assert "read" not in full["query"]
    assert selected["concepts"]
    assert [
        {field: concept.get(field) for field in _IDENTITY}
        for concept in selected["concepts"]
    ] == [
        {field: concept.get(field) for field in _IDENTITY}
        for concept in full["concepts"]
    ]
    for name in ("pages", "relationships", "impacted_paths", "found", "bounds"):
        assert selected[name] == full[name], name
    assert [match["present"] for match in selected["matches"]] == [
        match["present"] for match in full["matches"]
    ]
    assert all(
        "implementation" not in concept and "freshness" not in concept
        for concept in selected["concepts"]
    )
    assert selected["knowledge"]["whole_store_validated"] is False
    assert selected["knowledge"]["validation_scope"] == "selected-records"
    assert selected["cost"] == {
        "scope": "snapshot-index-only",
        "full_inventory_performed": False,
        "supplied_paths": 3,
    }
    assert _bytes(wiki) == before


def test_selected_read_spans_more_paths_than_one_read_selects(
    tmp_path, monkeypatch, capsys
):
    _project(tmp_path, monkeypatch, capsys, "packed-v4")
    paths = ["policy.py", *(f"absent_{index:02d}.py" for index in range(60))]

    selected = _impact(paths, read="selected")

    assert selected["query"]["read"] == "selected"
    assert selected["bounds"]["paths"]["total"] == 61
    assert {page["source_path"] for page in selected["pages"]} == {"policy.py"}


def _failing_selected_read(code):
    def fail(*args, **kwargs):
        raise KnowledgeStorageError("read", "simulated selected read failure", code=code)

    return fail


def test_selected_request_falls_back_to_the_full_read_when_over_budget(
    tmp_path, monkeypatch, capsys
):
    _project(tmp_path, monkeypatch, capsys, "packed-v4")
    monkeypatch.setattr(
        knowledge_storage_access,
        "capture_knowledge_slice",
        _failing_selected_read("storage-budget-exhausted"),
    )

    result = _impact(["policy.py"], read="selected")

    validate_documentation_query_result(result)
    assert result["query"]["read"] == "full"
    assert any("implementation" in concept for concept in result["concepts"])


def test_selected_read_integrity_failure_is_not_hidden_by_a_fallback(
    tmp_path, monkeypatch, capsys
):
    _project(tmp_path, monkeypatch, capsys, "packed-v4")
    monkeypatch.setattr(
        knowledge_storage_access,
        "capture_knowledge_slice",
        _failing_selected_read("storage-mixed-generation"),
    )

    with pytest.raises(api.LlmWikiApiError):
        _impact(["policy.py"], read="selected")


@pytest.mark.parametrize(
    ("options", "field"),
    [
        ({"read": "fast"}, "read"),
        ({"read": "selected", "include_raw_evidence": True}, "include_raw_evidence"),
        ({"read": "selected", "source_policy": "discovery"}, "source_policy"),
    ],
)
def test_selected_read_request_errors_match_across_api_and_mcp(options, field):
    request = {"operation": "impact", "paths": ["app.py"], **options}

    with pytest.raises(api.InvalidRequestError) as python_error:
        api.query_documentation(request)
    with pytest.raises(mcp_server.McpWikiError) as mcp_error:
        mcp_server.McpWikiService().query_documentation(request)

    assert python_error.value.code == "invalid-request"
    assert python_error.value.details == {"field": field}
    assert mcp_error.value.code == python_error.value.code
    assert mcp_error.value.data == python_error.value.details
