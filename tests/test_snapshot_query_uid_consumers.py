"""Consumers of the shared snapshot preserve durable graph identity and custody."""

from __future__ import annotations

from copy import deepcopy

import pytest

from llm_wiki_cli import api
from llm_wiki_cli.services.knowledge_artifacts import (
    build_knowledge_commit_plan,
    commit_knowledge_artifacts,
)
from llm_wiki_cli.services.contracts import TYPED_GRAPH_EXTENSION_KEY
from llm_wiki_cli.services.knowledge_loader import (
    KnowledgeStateLoadError,
    load_knowledge_state,
)
from llm_wiki_cli.services.knowledge_model import parse_knowledge_index
from llm_wiki_cli.services.knowledge_storage import KnowledgeStorageError
from llm_wiki_cli.services.knowledge_storage_access import capture_knowledge_slice
from llm_wiki_cli.services.knowledge_governance import GOVERNANCE_FILENAME
from llm_wiki_cli.services.task_contract import (
    TASK_REQUEST_SCHEMA_V2,
    normalize_task_request,
)
from llm_wiki_cli.services.task_context_v2 import validate_scoped_bindings
from tests.test_task_compact import reseal_canonical
from tests.test_snapshot_query_validation import STORAGE_FORMATS, _history_snapshot


STORED_FORMATS = STORAGE_FORMATS[1:]
USER = "llm-wiki://entities/User"


def _uid(ledger, locator=USER):
    return next(
        uid
        for uid, allocation in ledger.concepts.items()
        if allocation.locator == locator
    )


@pytest.mark.parametrize("storage_format", STORED_FORMATS)
@pytest.mark.parametrize("coordinate", ("page", "locator", "uid", "alias"))
@pytest.mark.parametrize("projected", (False, True))
def test_selected_graph_expands_both_locator_and_durable_uid(
    tmp_path, storage_format, coordinate, projected
):
    _, ledger = _history_snapshot(tmp_path, storage_format)
    selectors = {
        "page": "page:entities/User.md",
        "locator": "concept:" + USER,
        "uid": "concept:" + _uid(ledger),
        "alias": "concept:llm-wiki://entities/LegacyUser",
    }
    capture = capture_knowledge_slice(
        tmp_path,
        [selectors[coordinate]],
        include_graph=True,
        collections=("edges",) if projected else None,
    )
    payload = capture.slice.to_payload()
    capture.finish()
    assert payload["lookup_complete"] is True
    edges = [row["value"] for row in payload["records"]["edges"]]
    assert any(
        edge["kind"] == "supersedes" and edge["from"].get("uid") == _uid(ledger)
        for edge in edges
    )
    assert any(
        edge["kind"] == "contains" and edge["target"].get("locator") == USER
        for edge in edges
    )
    assert payload["whole_store_validated"] is False
    if projected:
        assert all(
            not rows for kind, rows in payload["records"].items() if kind != "edges"
        )


@pytest.mark.parametrize("storage_format", STORED_FORMATS)
@pytest.mark.parametrize("coordinate", ("locator", "uid", "page", "alias"))
def test_scoped_task_preserves_uid_edges_for_exact_concept_requirements(
    tmp_path, monkeypatch, storage_format, coordinate
):
    wiki = tmp_path / "wiki"
    wiki.mkdir()
    _, ledger = _history_snapshot(wiki, storage_format)
    monkeypatch.chdir(tmp_path)
    selectors = {
        "locator": USER,
        "uid": _uid(ledger),
        "page": "entities/User.md",
        "alias": "llm-wiki://entities/LegacyUser",
    }
    request = {
        "schema_version": TASK_REQUEST_SCHEMA_V2,
        "options": {"read_scope": "snapshot", "knowledge_mode": "required"},
        "storage_options": {"selection": "required-facets-v1"},
        "requirements": [
            {
                "id": "graph",
                "facet": "typed-relationships",
                "selector": selectors[coordinate],
            }
        ],
    }
    result = api.build_task_context(request, wiki_dir="wiki")
    payload = api.validate_task_context(result.rendered, request)
    edges = payload["facts"][0]["observation"]["edges"]
    assert any(
        edge["kind"] == "supersedes" and edge["from"].get("uid") == _uid(ledger)
        for edge in edges
    )
    assert payload["storage"]["whole_store_validated"] is False
    assert payload["source_capture"] is None and payload["work"]["source_files"] == 0
    assert (
        payload["facts"][0]["qualification"]["graph_completeness"]
        == "static-observations-only"
    )


@pytest.mark.parametrize("storage_format", STORED_FORMATS)
@pytest.mark.parametrize("corruption", ("reason", "hash"))
def test_selected_uid_edge_evidence_is_checked_against_live_authority(
    tmp_path, storage_format, corruption
):
    old, ledger = _history_snapshot(tmp_path, storage_format)
    state = load_knowledge_state(tmp_path)
    assert state.validated_artifacts is not None
    payload = deepcopy(state.validated_artifacts.knowledge_payload)
    edge = next(
        edge
        for edge in payload["extensions"][TYPED_GRAPH_EXTENSION_KEY]["edges"]
        if edge["kind"] == "supersedes"
    )
    sample = edge["evidence"]["samples"][0]
    if corruption == "reason":
        sample["reason"] = "unrecorded-reason"
    else:
        sample["attributes"]["governance_hash"] = "sha256:" + "f" * 64
    plan = build_knowledge_commit_plan(
        tmp_path,
        surface_index_bytes=old.surface_index.content,
        knowledge_index=parse_knowledge_index(payload),
        manifest=old.committed_manifest.without_artifact_hashes(),
        knowledge_format=storage_format,
    )
    commit_knowledge_artifacts(plan)
    # Exact bytes and the graph shape are coherent; the ledger disagrees.
    with pytest.raises(KnowledgeStateLoadError):
        load_knowledge_state(tmp_path)
    with pytest.raises(KnowledgeStorageError, match="(authority|ledger)"):
        capture_knowledge_slice(tmp_path, ["out:concept:" + _uid(ledger)])


@pytest.mark.parametrize("storage_format", STORED_FORMATS)
def test_incoming_uid_relationship_is_available_to_successor_task(
    tmp_path, monkeypatch, storage_format
):
    wiki = tmp_path / "wiki"
    wiki.mkdir()
    _, ledger = _history_snapshot(wiki, storage_format)
    monkeypatch.chdir(tmp_path)
    successor = "llm-wiki://entities/AccountService"
    request = {
        "schema_version": TASK_REQUEST_SCHEMA_V2,
        "options": {"read_scope": "snapshot", "knowledge_mode": "required"},
        "storage_options": {"selection": "required-facets-v1"},
        "requirements": [
            {
                "id": "graph",
                "facet": "typed-relationships",
                "selector": successor,
                "criterion": "complete",
            }
        ],
    }
    result = api.build_task_context(request, wiki_dir="wiki")
    data = api.validate_task_context(result.rendered, request)
    fact = data["facts"][0]
    assert any(
        edge["kind"] == "supersedes"
        and edge["target"].get("uid") == _uid(ledger, successor)
        for edge in fact["observation"]["edges"]
    )
    assert fact["state"] == "partial" and data["coverage"][0]["satisfied"] is False


@pytest.mark.parametrize("mutation", ("foreign-uid", "mixed-coordinate", "wrong-kind"))
def test_scoped_result_cannot_bind_an_unrelated_uid_edge(
    tmp_path, monkeypatch, mutation
):
    wiki = tmp_path / "wiki"
    wiki.mkdir()
    _, ledger = _history_snapshot(wiki, "packed-v4-deflate")
    monkeypatch.chdir(tmp_path)
    request = {
        "schema_version": TASK_REQUEST_SCHEMA_V2,
        "options": {"read_scope": "snapshot", "knowledge_mode": "required"},
        "requirements": [
            {"id": "graph", "facet": "typed-relationships", "selector": USER}
        ],
    }
    result = api.build_task_context(request, wiki_dir="wiki")
    data = result.to_payload()
    edge = next(
        e for e in data["facts"][0]["observation"]["edges"] if e["kind"] == "supersedes"
    )
    if mutation == "foreign-uid":
        edge["from"]["uid"] = _uid(ledger, "llm-wiki://entities/AccountService")
    elif mutation == "mixed-coordinate":
        edge["from"]["locator"] = "llm-wiki://entities/foreign"
    else:
        edge["from"]["kind"] = "source-symbol"
    normalized, profile = normalize_task_request(request)
    with pytest.raises(
        ValueError, match="typed relationship belongs to a different concept"
    ):
        validate_scoped_bindings(data, normalized, profile)
    with pytest.raises(api.InvalidRequestError):
        api.validate_task_context(reseal_canonical(data), request)


def test_uid_graph_expansion_retains_record_selector_and_byte_bounds(tmp_path):
    _, ledger = _history_snapshot(tmp_path, "packed-v4-deflate")
    selector = "concept:" + _uid(ledger)
    capture = capture_knowledge_slice(
        tmp_path, [selector], include_graph=True, collections=("edges",), max_records=1
    )
    data = capture.slice.to_payload()
    assert data["lookup_complete"] is False
    assert len(data["records"]["edges"]) == 1
    assert data["unverified_records"]["edges"] > 0
    capture.finish()
    complete = capture_knowledge_slice(
        tmp_path, [selector], include_graph=True, collections=("edges",)
    )
    capture_bytes = complete.session.bytes_read
    complete.finish()
    with pytest.raises(KnowledgeStorageError, match="budget"):
        capture_knowledge_slice(
            tmp_path,
            [selector],
            include_graph=True,
            collections=("edges",),
            max_bytes=capture_bytes - 1,
        )
    with pytest.raises(KnowledgeStorageError) as caught:
        capture_knowledge_slice(
            tmp_path,
            [selector, *("term:missing-" + str(i) for i in range(96))],
            include_graph=True,
        )
    assert caught.value.code == "storage-budget-exhausted"


@pytest.mark.parametrize("target", (GOVERNANCE_FILENAME, "entities/User.md"))
def test_uid_graph_read_rechecks_captured_authority_and_pages(tmp_path, target):
    _, ledger = _history_snapshot(tmp_path, "packed-v4-deflate")
    capture = capture_knowledge_slice(
        tmp_path,
        ["concept:" + _uid(ledger)],
        include_graph=True,
        collections=("edges",),
    )
    path = tmp_path / target
    content = path.read_bytes()
    path.write_bytes(b"!" + content[1:])
    with pytest.raises(KnowledgeStorageError) as caught:
        capture.finish()
    assert caught.value.code == "storage-mutation"
