"""Exact source ownership for class symbol coverage, without fuzzy selection."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from llm_wiki_cli import api
from llm_wiki_cli.services.documentation_queries import (
    DocumentationGraphQueryService,
    DocumentationQueryError,
    QUERY_IDENTITY_BYTE_LIMIT,
)


def _service(
    *,
    limit: int = 20,
    duplicate_in_file: bool = False,
    callable_collision: bool = False,
):
    inventory = {
        "backend/models.py": {
            "language": "python",
            "imports": [],
            "classes": [{"name": "Item", "methods": [], "attributes": []}]
            * (2 if duplicate_in_file else 1),
            "functions": [{"name": "run"}]
            + ([{"name": "Item"}] if callable_collision else []),
        },
        "frontend/модели.ts": {
            "language": "typescript",
            "imports": [],
            "classes": [
                {"name": "Item", "kind": "interface", "methods": [], "attributes": []}
            ],
            "functions": [{"name": "run"}],
        },
    }
    pages = [
        {
            "kind": kind,
            "id": filename,
            "title": "Item",
            "canonical_path": f"{kind}/{filename}.md",
            "source_path": source,
            "mcp_uri": f"llm-wiki://{kind}/{filename}",
        }
        for source, filename in (
            ("backend/models.py", "backend_Item"),
            ("frontend/модели.ts", "frontend_Item"),
        )
        for kind in ("modules", "entities")
    ]
    return DocumentationGraphQueryService(
        inventory, surface_index={"pages": pages}, limit=limit
    )


@pytest.mark.parametrize("source", ["backend/models.py", "frontend/модели.ts"])
def test_exact_source_class_lookup_returns_only_its_owner(source: str):
    service = _service()
    result = service.pages_for_symbol(source + ":Item")
    assert result["found"] is True and result["ambiguous"] is False
    assert result["symbol"] == {
        "name": "Item",
        "file": source,
        "module": Path(source).stem,
        "kind": "class",
    }
    assert result["pages"] and all(p["source_path"] == source for p in result["pages"])
    assert result["bounds"]["matches"] == {
        "total": 1,
        "returned": 1,
        "truncated": False,
    }


def test_duplicate_unqualified_class_names_remain_ambiguous():
    result = _service(limit=1).pages_for_symbol("Item")
    assert result["found"] is False and result["ambiguous"] is True
    assert result["pages"] == [] and result["symbol"] is None
    assert result["bounds"]["matches"] == {"total": 2, "returned": 1, "truncated": True}


def test_source_qualification_does_not_hide_callable_class_collision():
    result = _service(callable_collision=True).pages_for_symbol(
        "backend/models.py:Item"
    )
    assert result["found"] is False and result["ambiguous"] is True
    assert result["symbol"] is None and result["pages"] == []
    assert result["bounds"]["matches"]["total"] == 2


def test_repeated_declarations_keep_the_legacy_file_name_graph_identity():
    service = _service(duplicate_in_file=True)
    # The existing relationship summary groups these declarations by file/name.
    # Qualification selects that same graph symbol without inventing occurrences.
    assert service.pages_for_symbol("Item")["bounds"]["matches"]["total"] == 2
    result = service.pages_for_symbol("backend/models.py:Item")
    assert result["found"] is True and result["ambiguous"] is False
    assert result["bounds"]["matches"]["total"] == 1
    assert all(p["source_path"] == "backend/models.py" for p in result["pages"])


@pytest.mark.parametrize(
    "query",
    [
        "models.py:Item",
        "backend/missing.py:Item",
        "Backend/models.py:Item",
        "backend/models.py:item",
        "backend/models.py:Missing",
        "backend/models.py:",
        ":Item",
        "../backend/models.py:Item",
        "/backend/models.py:Item",
        "C:/backend/models.py:Item",
    ],
)
def test_wrong_missing_or_invalid_source_routes_do_not_fuzzy_match(query: str):
    result = _service().pages_for_symbol(query)
    assert result["found"] is False and result["ambiguous"] is False
    assert (
        result["matches"] == [] and result["pages"] == [] and result["symbol"] is None
    )


def test_qualified_class_path_uses_existing_callable_normalization():
    service = _service()
    expected = service.pages_for_symbol("backend/models.py:Item")
    for route in ("./backend/models.py:Item", r"backend\models.py:Item"):
        assert service.pages_for_symbol(route) == expected | {"query": route}
    for route in ("backend/models.py:run", r"backend\models.py:run"):
        result = service.pages_for_symbol(route)
        assert (
            result["found"] is True and result["symbol"]["file"] == "backend/models.py"
        )
    assert service.pages_for_symbol("run")["ambiguous"] is True


def test_qualified_class_pages_keep_exact_bounds():
    result = _service(limit=1).pages_for_symbol("backend/models.py:Item")
    assert result["found"] is True
    assert result["bounds"]["pages"] == {"total": 2, "returned": 1, "truncated": True}
    assert len(result["pages"]) == 1
    assert len(json.dumps(result).encode("utf-8")) < 65536


def test_class_query_keeps_identity_limit_and_no_query_time_io(
    monkeypatch: pytest.MonkeyPatch,
):
    service = _service()
    with pytest.raises(DocumentationQueryError, match="UTF-8 bytes"):
        service.pages_for_symbol("x" * QUERY_IDENTITY_BYTE_LIMIT + ":Item")

    def forbidden(*_args, **_kwargs):
        raise AssertionError(
            "an already built query service must not perform filesystem reads"
        )

    monkeypatch.setattr(Path, "read_bytes", forbidden)
    monkeypatch.setattr(Path, "read_text", forbidden)
    assert service.pages_for_symbol("backend/models.py:Item")["found"] is True


def test_native_concept_identity_matches_the_source_qualified_class(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    monkeypatch.chdir(tmp_path)
    source = tmp_path / "src"
    source.mkdir()
    for name in ("left.py", "right.py"):
        (source / name).write_text(
            'class Item:\n    """A source-owned item."""\n    pass\n', encoding="utf-8"
        )
    api.bootstrap_wiki("src", "wiki")
    service = api.build_documentation_query_service("src", wiki_dir="wiki")
    before = {
        p: p.read_bytes()
        for root in (source, tmp_path / "wiki")
        for p in root.rglob("*")
        if p.is_file()
    }
    assert api.pages_for_symbol("Item", service=service)["ambiguous"] is True
    for filename in ("left.py", "right.py"):
        result = api.pages_for_symbol(filename + ":Item", service=service)
        assert isinstance(result["symbol"], dict)
        assert result["found"] is True and result["symbol"]["file"] == filename
        entities = [p for p in result["pages"] if p["kind"] == "entities"]
        assert len(entities) == 1 and entities[0]["source_path"] == filename
        concept = api.get_concept(entities[0]["mcp_uri"], service=service)
        assert concept["concept"] is not None
        assert (
            concept["found"] is True and concept["concept"]["source_path"] == filename
        )
    assert all(p.read_bytes() == raw for p, raw in before.items())
