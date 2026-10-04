"""Pure presentation must roundtrip exact evidence and account for all output."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, cast

import pytest

from llm_wiki_cli import api
from llm_wiki_cli.services.context_budget import _accounted_render
from llm_wiki_cli.services.task_compact import (
    COMPACT_SCHEMA,
    VIEW_REQUEST_SCHEMA,
    TaskCompactError,
    render_compact_task_context,
    validate_compact_task_context,
    expand_compact_task_context,
)
from llm_wiki_cli.services.task_contract import TaskContext, TASK_RESULT_SCHEMA_V2
from llm_wiki_cli.services.token_counting import EstimatedCounter
from llm_wiki_cli.services.workflow_profile import canonical_json, content_id, WorkflowRequestError
from tests.developer_value.fixtures import POLICY_SOURCE


@pytest.fixture
def canonical(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "policy.py").write_text(POLICY_SOURCE)
    request = {
        "schema_version": "llm-wiki-task-request/v2",
        "kind": "contract-change",
        "requirements": [
            {
                "id": "contract",
                "facet": "source-contract",
                "selector": "policy.py:Batch",
            },
            {"id": "calls", "facet": "callees", "selector": "policy.py:public_values"},
        ],
        "options": {"knowledge_mode": "off", "budget_tokens": 32000},
    }
    result = api.build_task_context(request)
    assert result.ok
    return result, request


def options(budget=32000):
    return {"schema_version": VIEW_REQUEST_SCHEMA, "budget_tokens": budget}


def reseal_canonical(payload):
    old_to_new = {}
    for fact in payload["facts"]:
        old = fact["fact_id"]
        fact["fact_id"] = content_id(
            "llm-wiki-task-fact/v1",
            {key: value for key, value in fact.items() if key != "fact_id"},
        )
        old_to_new[old] = fact["fact_id"]
    for row in payload["coverage"]:
        row["fact_ids"] = [old_to_new.get(key, key) for key in row["fact_ids"]]

    def render(accounting):
        payload["accounting"] = dict(accounting)
        payload["result_id"] = content_id(
            TASK_RESULT_SCHEMA_V2,
            {key: value for key, value in payload.items() if key != "result_id"},
        )
        return canonical_json(payload).decode()

    return _accounted_render(render, payload["accounting"], EstimatedCounter())


def test_complete_roundtrip_preserves_receipts_exact_fact_ids_and_both_call_targets(
    canonical,
):
    original, request = canonical
    compact = render_compact_task_context(original, request, view_options=options())
    assert compact.ok and compact.canonical_text == original.rendered
    assert compact.canonical_accounting == original.accounting
    expanded = expand_compact_task_context(
        compact.rendered, original.rendered, request, view_options=options()
    )
    payload = original.to_payload()
    assert expanded["facts"] == payload["facts"]
    assert (
        expanded["coverage"] == payload["coverage"]
        and expanded["omissions"] == payload["omissions"]
    )
    assert expanded["limitations"] == payload["limitations"]
    assert expanded["native"]["status"] == "off"
    calls = next(fact for fact in expanded["facts"] if fact["facet"] == "callees")
    assert {row["symbol"] for row in calls["observation"]["callees"]} == {
        "Batch",
        "Batch.cap",
    }
    assert compact.accounting["used_tokens"] == EstimatedCounter().count(
        compact.rendered
    )
    with pytest.raises(TypeError):
        cast(dict[str, Any], compact.accounting)["used_tokens"] = 0


@pytest.mark.parametrize(
    "value", [{"from": "parameters"}, None, False, 0, {"unknown": [None, False, 0]}]
)
def test_valid_canonical_literal_input_shapes_never_collide_with_derived_codec(
    canonical, value
):
    original, request = canonical
    payload = original.to_payload()
    contract = next(
        fact for fact in payload["facts"] if fact["facet"] == "source-contract"
    )
    contract["observation"]["contract"]["methods"][0]["data_effects"]["inputs"] = value
    text = reseal_canonical(payload)
    validated = api.validate_task_context(text, request)
    compact = render_compact_task_context(text, request, view_options=options())
    expanded = expand_compact_task_context(
        compact.rendered, text, request, view_options=options()
    )
    assert expanded["facts"] == validated["facts"]


@pytest.mark.parametrize("change", ["missing", "null", "false", "zero", "unknown"])
def test_known_default_codec_preserves_missing_null_false_zero_and_unknown_fields(
    canonical, change
):
    original, request = canonical
    payload = original.to_payload()
    fact = next(fact for fact in payload["facts"] if fact["facet"] == "source-contract")
    method = fact["observation"]["contract"]["methods"][0]
    if change == "missing":
        method.pop("docstring")
    elif change == "null":
        method["docstring"] = None
    elif change == "false":
        method["is_async"] = False
    elif change == "zero":
        method["is_async"] = 0
    else:
        method["future-extension"] = {"unknown": [None, False, 0]}
    text = reseal_canonical(payload)
    api.validate_task_context(text, request)
    compact = render_compact_task_context(text, request, view_options=options())
    assert (
        expand_compact_task_context(
            compact.rendered, text, request, view_options=options()
        )["facts"]
        == json.loads(text)["facts"]
    )


@pytest.mark.parametrize(
    "field",
    ["state", "fact", "citation", "qualification", "requirement", "codec", "bounds"],
)
def test_self_rehashed_and_recounted_compact_tampering_is_rejected(canonical, field):
    original, request = canonical
    result = render_compact_task_context(original, request, view_options=options())
    payload = result.to_payload()
    if field == "state":
        payload["state"] = "empty"
    elif field == "fact":
        payload["facts"]["rows"][0][0] = "sha256:" + "0" * 64
    elif field == "citation":
        payload["facts"]["rows"][0][5] = [100]
    elif field == "qualification":
        payload["shared_qualification"]["behavior"] = "verified"
    elif field == "requirement":
        payload["requirements"]["rows"][0][6] = "complete-runtime-proof"
    elif field == "codec":
        payload["facts"]["rows"][0][4]["codec"] = "guess-v9"
    else:
        payload["facts"]["rows"][1][4]["value"]["bounds"]["callees"]["total"] = 0

    def render(accounting):
        payload["accounting"] = dict(accounting)
        payload["view_id"] = content_id(
            COMPACT_SCHEMA,
            {key: value for key, value in payload.items() if key != "view_id"},
        )
        return canonical_json(payload).decode()

    forged = _accounted_render(render, payload["accounting"], EstimatedCounter())
    with pytest.raises(TaskCompactError):
        validate_compact_task_context(
            forged, original.rendered, request, view_options=options()
        )


def test_minimum_budget_failure_has_no_context_and_separate_actual_diagnostic_accounting(
    canonical,
):
    original, request = canonical
    result = render_compact_task_context(original, request, view_options=options(1))
    assert (
        not result.ok and result.error == "cannot-fit-compact" and result.rendered == ""
    )
    assert result.accounting["minimum_tokens"] > 1
    diagnostic = result.to_payload()
    assert "facts" not in diagnostic and "canonical" not in diagnostic
    assert diagnostic["diagnostic_accounting"][
        "used_tokens"
    ] == EstimatedCounter().count(result.diagnostic_rendered)
    assert result.canonical_text == original.rendered


@pytest.mark.parametrize("bad", [True, -1, 1.2])
def test_every_trusted_count_is_a_strict_nonnegative_integer(canonical, bad):
    original, request = canonical

    class Counter:
        identity = EstimatedCounter.identity
        exact = False

        def count(self, text):
            return bad

    with pytest.raises((TaskCompactError, ValueError)):
        render_compact_task_context(
            original.rendered, request, view_options=options(), counter=Counter()
        )


def test_counter_identity_change_during_callback_is_rejected(canonical):
    original, request = canonical

    class Counter:
        identity = EstimatedCounter.identity
        exact = False

        def count(self, text):
            self.identity = "changed"
            return EstimatedCounter().count(text)

    with pytest.raises((TaskCompactError, WorkflowRequestError)):
        render_compact_task_context(
            original.rendered, request, view_options=options(), counter=Counter()
        )


def test_pure_presentation_never_reads_sources_or_files(canonical, monkeypatch):
    original, request = canonical

    def refuse(*args, **kwargs):
        raise AssertionError("presentation performed filesystem I/O")

    monkeypatch.setattr(Path, "read_bytes", refuse)
    monkeypatch.setattr(Path, "read_text", refuse)
    result = render_compact_task_context(
        original.rendered, request, view_options=options()
    )
    validate_compact_task_context(
        result.rendered, original.rendered, request, view_options=options()
    )


def test_canonical_failure_cannot_be_salvaged_and_budget_does_not_replace_original(
    canonical,
):
    original, request = canonical
    failed = TaskContext(False, "", {}, "cannot-fit")
    with pytest.raises(TaskCompactError):
        render_compact_task_context(failed, request, view_options=options())
    with pytest.raises(TaskCompactError):
        render_compact_task_context(
            original.rendered, request, view_options=options(32001)
        )
    assert original.accounting["budget_tokens"] == 32000
