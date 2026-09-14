"""Source-grounded inspection parity, operation scope and output bounds."""

import json

import pytest

from llm_wiki_cli import api
from llm_wiki_cli.services import context_packet, native_inspection
from llm_wiki_cli.services.documentation_queries import DocumentationGraphQueryService
from llm_wiki_cli.services.mcp_server import McpWikiService


TARGET = "llm-wiki://entities/Item"


@pytest.fixture
def consumer(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "src").mkdir()
    (tmp_path / "src/catalog.py").write_text(
        "class Item:\n    price: int\n    label: str\n",
        encoding="utf-8",
    )
    api.bootstrap_wiki("src", "wiki")
    return tmp_path


def test_live_inspection_matches_independent_queries_with_one_inventory(
    consumer, monkeypatch
):
    service = api.build_documentation_query_service("src", wiki_dir="wiki")
    expected = {
        "concept": api.get_concept(TARGET, service=service),
        "graph": api.traverse_typed_graph(TARGET, service=service),
        "sections": api.list_concept_sections(TARGET, service=service),
    }
    inventory = context_packet.context_service.get_inventory
    build = native_inspection.build_documentation_query_service_from_view
    counts = {"inventory": 0, "service": 0}

    def capture(*args, **kwargs):
        counts["inventory"] += 1
        return inventory(*args, **kwargs)

    def assemble(*args, **kwargs):
        counts["service"] += 1
        return build(*args, **kwargs)

    monkeypatch.setattr(context_packet.context_service, "get_inventory", capture)
    monkeypatch.setattr(
        native_inspection, "build_documentation_query_service_from_view", assemble
    )
    result = api.inspect_concept(TARGET, src_dir="src", wiki_dir="wiki", live=True)
    assert counts == {"inventory": 1, "service": 1}
    assert {key: result[key] for key in expected} == expected
    assert result["cost"]["full_inventory_performed"] is True
    assert result["coverage"]["counts"] is not None
    assert result["concept"]["concept"] is not None
    assert result["coverage"]["counts"]["compared"] == 2
    assert result["concept"]["concept"]["locator"] == TARGET
    assert result["graph"]["edges"]
    assert all(
        set(edge["evidence"]) <= {"state", "observed", "unique", "emitted", "omitted"}
        for edge in result["graph"]["edges"]
    )
    assert len(json.dumps(result).encode()) <= result["limits"]["result_bytes"]


def test_snapshot_never_scans_source_and_keeps_scope_after_source_change(
    consumer, monkeypatch
):
    source = consumer / "src/catalog.py"
    source.write_text(
        source.read_text().replace("price: int", "price: float"), encoding="utf-8"
    )
    monkeypatch.setattr(
        context_packet,
        "capture_context_read",
        lambda *a, **k: pytest.fail("snapshot scanned source"),
    )
    snapshot = api.inspect_concept(
        TARGET, wiki_dir="wiki", limit=1, include_evidence=True
    )
    assert snapshot == McpWikiService(src_dir="src", wiki_dir="wiki").inspect_concept(
        TARGET, limit=1, include_evidence=True
    )
    assert snapshot["read_scope"] == "snapshot-only"
    assert snapshot["cost"]["full_inventory_performed"] is False
    assert snapshot["concept"]["knowledge"]["freshness_evaluated"] is False
    assert snapshot["graph"]["include_evidence"] is True
    assert snapshot["graph"]["returned"] <= 1
    assert snapshot["sections"]["returned"] <= 1
    assert snapshot["sections"]["truncated"] is True
    assert snapshot["truncated"] is True


@pytest.mark.parametrize(
    "target,field,live",
    [
        ("src/catalog.py", "src_dir", True),
        ("wiki/index.md", "wiki_dir", True),
        ("wiki/index.md", "wiki_dir", False),
    ],
)
def test_mutation_after_last_component_discards_the_entire_result(
    consumer, monkeypatch, target, field, live
):
    original = DocumentationGraphQueryService.list_concept_sections

    def mutate(*args, **kwargs):
        result = original(*args, **kwargs)
        path = consumer / target
        path.write_text(
            path.read_text() + "\n# mutated after final query\n", encoding="utf-8"
        )
        return result

    monkeypatch.setattr(DocumentationGraphQueryService, "list_concept_sections", mutate)
    with pytest.raises(api.WorkspaceStateError) as failure:
        api.inspect_concept(TARGET, src_dir="src", wiki_dir="wiki", live=live)
    assert failure.value.code == "context-read-mutated"
    assert failure.value.details == {"field": field}
    assert str(consumer) not in str(failure.value)


@pytest.mark.parametrize(
    "options,field",
    [
        ({"limit": 0}, "limit"),
        ({"live": "yes"}, "live"),
        ({"include_evidence": 1}, "include_evidence"),
        ({"helper_cache_dir": False}, "helper_cache_dir"),
    ],
)
def test_inspection_validates_before_any_capture(consumer, monkeypatch, options, field):
    monkeypatch.setattr(
        native_inspection,
        "inspect_native_concept",
        lambda *a, **k: pytest.fail("invalid request read files"),
    )
    with pytest.raises(api.InvalidRequestError) as failure:
        api.inspect_concept(TARGET, **options)
    assert failure.value.code == "invalid-request"
    assert failure.value.details == {"field": field}


def test_final_byte_bound_cannot_return_partial_success(consumer, monkeypatch):
    monkeypatch.setattr(native_inspection, "MAX_INSPECTION_BYTES", 1)
    with pytest.raises(api.InvalidRequestError):
        api.inspect_concept(TARGET, wiki_dir="wiki")
