"""A matching UID cannot exempt the rest of a portable edge from validation."""

from __future__ import annotations

import pytest

from llm_wiki_cli import api
from llm_wiki_cli.services import knowledge_graph, knowledge_model, task_context
from llm_wiki_cli.services.task_contract import (
    TASK_REQUEST_SCHEMA_V2,
    normalize_task_request,
)
from llm_wiki_cli.services.task_context_v2 import validate_scoped_bindings
from llm_wiki_cli.services.workflow_profile import WorkflowRequestError
from tests.test_snapshot_query_validation import _history_snapshot
from tests.test_task_compact import reseal_canonical


USER = "llm-wiki://entities/User"
SUCCESSOR = "llm-wiki://entities/AccountService"


def _task(tmp_path, monkeypatch, selector):
    wiki = tmp_path / "wiki"
    wiki.mkdir()
    _history_snapshot(wiki, "packed-v4-deflate")
    monkeypatch.chdir(tmp_path)
    request = {
        "schema_version": TASK_REQUEST_SCHEMA_V2,
        "options": {"read_scope": "snapshot", "knowledge_mode": "required"},
        "storage_options": {"selection": "required-facets-v1"},
        "requirements": [
            {"id": "graph", "facet": "typed-relationships", "selector": selector}
        ],
    }
    return api.build_task_context(request, wiki_dir="wiki"), request


@pytest.mark.parametrize("selector", (USER, SUCCESSOR))
@pytest.mark.parametrize(
    "mutation",
    (
        "null",
        "array",
        "string",
        "missing",
        "wrong-kind",
        "mixed-coordinate",
        "unknown-field",
        "empty-uid",
        "numeric-uid",
        "key",
        "evidence",
        "coverage",
        "sample",
        "evidence-count",
        "unqualified-kind",
    ),
)
def test_matching_endpoint_does_not_bless_an_invalid_opposite_endpoint_or_edge(
    tmp_path, monkeypatch, selector, mutation
):
    task, request = _task(tmp_path, monkeypatch, selector)
    payload = task.to_payload()
    edge = next(
        e
        for e in payload["facts"][0]["observation"]["edges"]
        if e["kind"] == "supersedes"
    )
    opposite = "target" if selector == USER else "from"
    if mutation in {"null", "array", "string"}:
        edge[opposite] = {"null": None, "array": [], "string": "invalid"}[mutation]
    elif mutation == "missing":
        del edge[opposite]
    elif mutation == "wrong-kind":
        edge[opposite] = {
            "kind": "source-symbol",
            "source_path": "src/accounts.py",
            "symbol": "User",
        }
    elif mutation == "mixed-coordinate":
        edge[opposite]["locator"] = "llm-wiki://entities/Other"
    elif mutation == "unknown-field":
        edge[opposite]["unexpected"] = True
    elif mutation == "empty-uid":
        edge[opposite]["uid"] = ""
    elif mutation == "numeric-uid":
        edge[opposite]["uid"] = 123
    elif mutation == "key":
        edge["key"] = "sha256:" + "0" * 64
    elif mutation == "evidence":
        edge["evidence"] = {}
    elif mutation == "coverage":
        edge["coverage"]["truncated"] = True
    elif mutation == "sample":
        edge["evidence"]["samples"][0]["source"] = None
    elif mutation == "evidence-count":
        edge["evidence"]["observed"] += 1
    else:
        edge["kind"] = "unknown-kind"
    normalized, profile = normalize_task_request(request)
    with pytest.raises(ValueError):
        validate_scoped_bindings(payload, normalized, profile)
    with pytest.raises(api.InvalidRequestError):
        api.validate_task_context(reseal_canonical(payload), request)
    with pytest.raises(WorkflowRequestError):
        task_context.validate_task_context(reseal_canonical(payload), request)


@pytest.mark.parametrize("selector", (USER, SUCCESSOR))
def test_scoped_raw_edges_cannot_duplicate_an_identity_to_inflate_observations(
    tmp_path, monkeypatch, selector
):
    task, request = _task(tmp_path, monkeypatch, selector)
    payload = task.to_payload()
    observation = payload["facts"][0]["observation"]
    observation["edges"].append(observation["edges"][-1].copy())
    observation["bounds"]["edges"]["returned"] += 1
    observation["bounds"]["edges"]["total"] += 1
    with pytest.raises(api.InvalidRequestError):
        api.validate_task_context(reseal_canonical(payload), request)


@pytest.mark.parametrize("selector", (USER, SUCCESSOR))
@pytest.mark.parametrize("invalid", (None, [], "invalid"))
def test_nonobject_typed_edges_have_the_public_invalid_request_error(
    tmp_path, monkeypatch, selector, invalid
):
    task, request = _task(tmp_path, monkeypatch, selector)
    payload = task.to_payload()
    payload["facts"][0]["observation"]["edges"][0] = invalid
    with pytest.raises(api.InvalidRequestError):
        api.validate_task_context(reseal_canonical(payload), request)
    with pytest.raises(WorkflowRequestError):
        task_context.validate_task_context(reseal_canonical(payload), request)


@pytest.mark.parametrize("selector", (USER, SUCCESSOR))
def test_scoped_result_edge_validation_uses_no_full_model_or_graph_parser(
    tmp_path, monkeypatch, selector
):
    task, request = _task(tmp_path, monkeypatch, selector)
    expected = task.to_payload()

    def full_parse(*args, **kwargs):
        pytest.fail(
            "portable edge validation parsed the complete knowledge model or graph"
        )

    monkeypatch.setattr(knowledge_model, "parse_knowledge_index", full_parse)
    monkeypatch.setattr(knowledge_graph, "validate_typed_graph", full_parse)
    assert api.validate_task_context(task.rendered, request) == expected
