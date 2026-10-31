"""Graph anchor discovery must not materialize its graph before final selection."""

from collections import Counter

import pytest

from llm_wiki_cli.services.contracts import TYPED_GRAPH_EXTENSION_KEY
from llm_wiki_cli.services.knowledge_loader import load_knowledge_state
from llm_wiki_cli.services.knowledge_storage import (
    KnowledgeStorageError,
    KnowledgeStoreReader,
)
from llm_wiki_cli.services.knowledge_storage_access import capture_knowledge_slice
from tests.test_snapshot_query_validation import STORAGE_FORMATS, _history_snapshot


STORED_FORMATS = STORAGE_FORMATS[1:]
SOURCE = "source:src/accounts.py"


@pytest.mark.parametrize("storage_format", STORED_FORMATS)
@pytest.mark.parametrize("collections", (None, ("edges",), ("concepts", "edges")))
def test_selected_graph_records_are_validated_once_per_capture(
    tmp_path, monkeypatch, storage_format, collections
):
    _history_snapshot(tmp_path, storage_format)
    calls = Counter()
    original = KnowledgeStoreReader._record_aliases

    def counted(self, collection, row, value):
        if collection == "edges":
            calls[row["id"]] += 1
        return original(self, collection, row, value)

    monkeypatch.setattr(KnowledgeStoreReader, "_record_aliases", counted)
    captured = capture_knowledge_slice(
        tmp_path, [SOURCE], include_graph=True, collections=collections
    )
    payload = captured.slice.to_payload()
    captured.finish()
    ids = {row["id"] for row in payload["records"]["edges"]}
    assert ids and calls == {identity: 1 for identity in ids}
    assert payload["lookup_complete"] is True
    assert payload["whole_store_validated"] is False


@pytest.mark.parametrize("storage_format", STORED_FORMATS)
def test_graph_capture_fits_a_bounded_expansion_without_duplicate_edge_work(
    tmp_path, storage_format
):
    _history_snapshot(tmp_path, storage_format)
    state = load_knowledge_state(tmp_path)
    assert state.knowledge is not None
    expected = {
        edge["key"]: edge
        for edge in state.knowledge.extensions[TYPED_GRAPH_EXTENSION_KEY]["edges"]
    }
    # This fixture's three records and their concept anchors fit in 8 KiB;
    # decoding the graph in both discovery and final selection does not.
    captured = capture_knowledge_slice(
        tmp_path,
        [SOURCE],
        include_graph=True,
        collections=("edges",),
        max_expanded_bytes=8192,
    )
    payload = captured.slice.to_payload()
    captured.finish()
    assert payload["lookup_complete"] is True
    assert {row["id"]: row["value"] for row in payload["records"]["edges"]} == expected
    assert payload["work"]["expanded_bytes"] <= 8192
    with pytest.raises(KnowledgeStorageError, match="budget"):
        capture_knowledge_slice(
            tmp_path,
            [SOURCE],
            include_graph=True,
            collections=("edges",),
            max_expanded_bytes=1024,
        )


@pytest.mark.parametrize("collections", ((), ("unknown",), ("values",), ("lookup",)))
def test_invalid_projection_is_rejected_before_anchor_materialization(
    tmp_path, monkeypatch, collections
):
    _history_snapshot(tmp_path, "packed-v4-deflate")

    def materialized(*args, **kwargs):
        pytest.fail("invalid projection materialized a record")

    monkeypatch.setattr(KnowledgeStoreReader, "_record_aliases", materialized)
    with pytest.raises(KnowledgeStorageError, match="collections"):
        capture_knowledge_slice(
            tmp_path, [SOURCE], include_graph=True, collections=collections
        )
