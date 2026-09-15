"""Native consumers preserve safe failures and one coherent input read."""

import json

import pytest

from llm_wiki_cli import api
from llm_wiki_cli.services.mcp_server import McpWikiError, McpWikiService


LOCATOR = "llm-wiki://entities/Account"


@pytest.fixture
def consumer(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "app.py").write_text("class Account:\n    pass\n", encoding="utf-8")
    wiki = tmp_path / "wiki"
    wiki.mkdir()
    (wiki / "index.md").write_text("# Consumer\n", encoding="utf-8")
    return tmp_path


@pytest.mark.parametrize(
    "operation",
    [
        "build_documentation_query_service",
        "query_documentation",
        "get_concept",
        "related_concepts",
        "list_concept_sections",
        "traverse_typed_graph",
        "explain_evidence",
        "get_knowledge_coverage",
        "inspect_concept",
    ],
)
def test_native_path_failures_have_codes_and_no_resolved_root(consumer, operation):
    function = getattr(api, operation)
    value = (
        {"operation": "concept", "value": LOCATOR}
        if operation == "query_documentation"
        else LOCATOR
    )
    args = (
        ()
        if operation in {"build_documentation_query_service", "get_knowledge_coverage"}
        else (value,)
    )
    with pytest.raises(api.InvalidRequestError) as caught:
        function(*args, wiki_dir="../private-outside-wiki")
    assert caught.value.code == "path-policy-error"
    assert caught.value.details == {"field": "wiki_dir"}
    assert str(consumer) not in str(caught.value)
    assert "private-outside-wiki" not in str(caught.value)
    assert caught.value.__cause__ is not None


def test_unknown_request_fields_are_not_echoed_before_reads(consumer, monkeypatch):
    def unexpected(*args, **kwargs):
        pytest.fail("invalid input reached a read")

    monkeypatch.setattr(api, "_snapshot_query_service", unexpected)
    marker = "PRIVATE-REQUEST-FIELD-SENTINEL"
    with pytest.raises(api.InvalidRequestError) as caught:
        api.query_documentation(
            {"operation": "concept", "value": LOCATOR, marker: True}
        )
    assert caught.value.code == "invalid-request"
    assert caught.value.details == {"field": "request"}
    assert marker not in str(caught.value)


@pytest.mark.parametrize(
    "field,value",
    [("read_only", "yes"), ("allow_external_src", 1), ("helper_cache_dir", False)],
)
def test_native_builder_options_fail_before_source_reads(
    consumer, monkeypatch, field, value
):
    monkeypatch.setattr(
        api, "validate_source_root", lambda *a, **k: pytest.fail("unexpected read")
    )
    with pytest.raises(api.InvalidRequestError) as caught:
        api.build_documentation_query_service(**{field: value})
    assert caught.value.code == "invalid-request"
    assert caught.value.details == {"field": field}


def test_missing_source_differs_from_an_empty_available_source(consumer):
    missing = consumer / "missing"
    with pytest.raises(api.WorkspaceStateError) as caught:
        api.build_documentation_query_service(str(missing), wiki_dir="wiki")
    assert caught.value.code == "workspace-state-error"
    assert caught.value.details == {"field": "src_dir"}
    missing.mkdir()
    service = api.build_documentation_query_service(str(missing), wiki_dir="wiki")
    result = api.get_concept(LOCATOR, service=service)
    assert result["found"] is False
    assert result["knowledge"]["availability"] == "absent"


@pytest.mark.parametrize(
    "target,field", [("app.py", "src_dir"), ("wiki/index.md", "wiki_dir")]
)
def test_mutation_during_service_assembly_cannot_return_success(
    consumer, monkeypatch, target, field
):
    original = api.DocumentationGraphQueryService

    def mutate(*args, **kwargs):
        service = original(*args, **kwargs)
        path = consumer / target
        path.write_text(path.read_text() + "\n# changed during capture\n")
        return service

    monkeypatch.setattr(api, "DocumentationGraphQueryService", mutate)
    with pytest.raises(api.WorkspaceStateError) as caught:
        api.get_concept(LOCATOR, wiki_dir="wiki")
    assert caught.value.code == "context-read-mutated"
    assert caught.value.details == {"field": field}
    assert str(consumer) not in str(caught.value)


def test_mcp_native_semantic_errors_match_public_api(consumer):
    service = McpWikiService(src_dir=".", wiki_dir="wiki")
    with pytest.raises(api.InvalidRequestError) as public:
        api.get_concept(LOCATOR, limit=0)
    with pytest.raises(McpWikiError) as transport:
        service.get_concept(LOCATOR, limit=0)
    assert transport.value.code == public.value.code == "invalid-request"
    assert transport.value.data == public.value.details == {"field": "limit"}
    assert str(consumer) not in json.dumps(transport.value.data)


@pytest.mark.parametrize(
    "operation",
    ["build_documentation_query_service", "get_knowledge_coverage", "inspect_concept"],
)
def test_unprepared_live_helper_has_the_same_unavailable_category(consumer, operation):
    source = consumer / "src"
    source.mkdir()
    (source / "private-name.ts").write_text(
        "export class Item { price: number; }\n", encoding="utf-8"
    )
    options: dict[str, object] = {"src_dir": "src", "wiki_dir": "wiki", "helper_cache_dir": "empty-cache"}
    if operation != "build_documentation_query_service":
        options["live"] = True
    with pytest.raises(api.WorkspaceStateError) as failure:
        getattr(api, operation)(
            *([LOCATOR] if operation == "inspect_concept" else []), **options
        )
    assert failure.value.code == "workspace-state-error"
    assert failure.value.details == {"field": "src_dir"}
    assert "prepared helpers" in str(failure.value)
    assert "private-name" not in str(failure.value)
    assert str(consumer) not in str(failure.value)
    assert not (consumer / "empty-cache").exists()
