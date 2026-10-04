"""Independent real-result receiving controls for opt-in compact presentation."""

from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
from typing import Any

import pytest

from llm_wiki_cli import api
from llm_wiki_cli.services import task_compact
from llm_wiki_cli.services.knowledge_storage_lifecycle import migrate_knowledge_storage
from llm_wiki_cli.services.maintenance_service import adopt_maintenance_authority
from llm_wiki_cli.services.token_counting import EstimatedCounter
from llm_wiki_cli.services.workflow_profile import canonical_json, content_id
from tests.developer_value.fixtures import POLICY_SOURCE, materialize

COMPACT_SCHEMA = "llm-wiki-task-compact/v1"
VIEW_SCHEMA = "llm-wiki-task-view-request/v1"
FACT_FIELDS = [
    "fact_id",
    "facet",
    "selector",
    "state",
    "observation",
    "citation_refs",
    "qualification",
]
REQUIREMENT_FIELDS = [
    "id",
    "facet",
    "selector",
    "criterion",
    "state",
    "satisfied",
    "reason",
    "fact_refs",
]


def tiny_request():
    """Same Root comparison request; no smaller source, facts or denominator."""
    return {
        "schema_version": "llm-wiki-task-request/v2",
        "kind": "contract-change",
        "anchors": [{"kind": "symbol", "value": "policy.py:Batch"}],
        "requirements": [
            {
                "id": "contract",
                "facet": "source-contract",
                "selector": "policy.py:Batch",
                "criterion": "present",
            },
            {
                "id": "callees",
                "facet": "callees",
                "selector": "policy.py:public_values",
                "criterion": "present",
            },
        ],
        "options": {"knowledge_mode": "off", "budget_tokens": 32000},
    }


def view_options(budget=32000):
    return {"schema_version": VIEW_SCHEMA, "budget_tokens": budget}


def tree(path):
    return {
        item.relative_to(path).as_posix(): item.read_bytes()
        for item in path.rglob("*")
        if item.is_file()
    }


@pytest.fixture
def tiny(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    Path("src").mkdir()
    Path("src/policy.py").write_text(POLICY_SOURCE, encoding="utf-8")
    assert Path("src/policy.py").read_bytes() == POLICY_SOURCE.encode()
    assert len(POLICY_SOURCE.encode()) == 238
    return tmp_path


def native(tiny, capsys, *, adopted=False, indexed=False):
    api.bootstrap_wiki("src", "wiki")
    if adopted:
        adopt_maintenance_authority("src", "wiki", recovery_dir="maintenance-recovery")
    migrate_knowledge_storage(
        Path("wiki"), to="sharded-v2", recovery_dir=Path("storage-recovery")
    )
    if indexed:
        migrate_knowledge_storage(
            Path("wiki"), to="indexed-v8", recovery_dir=Path("manifest-recovery")
        )
    capsys.readouterr()


def native_request(*, snapshot=False):
    request = {
        "schema_version": "llm-wiki-task-request/v2",
        "requirements": [
            {"id": "class", "facet": "concept", "selector": "llm-wiki://entities/Batch"}
        ],
        "options": {"knowledge_mode": "required"},
    }
    if snapshot:
        request["options"]["read_scope"] = "snapshot"
    else:
        request["requirements"].append(
            {
                "id": "method",
                "facet": "source-contract",
                "selector": "policy.py:Batch.cap#1",
            }
        )
    return request


def canonical(request, **options):
    result = api.build_task_context(request, src_dir="src", wiki_dir="wiki", **options)
    assert result.ok
    received = api.validate_task_context(result.rendered, request, **options)
    return result, received


def expanded(result, request, *, budget=32000, **host):
    view = task_compact.render_compact_task_context(
        result, request, view_options=view_options(budget), **host
    )
    assert view.ok
    validated = task_compact.validate_compact_task_context(
        view.rendered,
        result.rendered,
        request,
        view_options=view_options(budget),
        **host,
    )
    assert validated == view.to_payload()
    value = task_compact.expand_compact_task_context(
        view.rendered,
        result.rendered,
        request,
        view_options=view_options(budget),
        **host,
    )
    return view, value


def exact_selected(value, captured):
    assert value["canonical"] == {
        key: captured[key]
        for key in ("task_id", "request_id", "result_id", "profile_id")
    }
    assert value["state"] == captured["state"]
    assert value["facts"] == captured["facts"]
    assert value["coverage"] == captured["coverage"]
    assert value["omissions"] == captured["omissions"]


def test_tiny_actual_emission_keeps_full_contract_both_targets_and_scope(tiny):
    request = tiny_request()
    before = tree(Path("src"))
    result, received = canonical(request)
    assert len(result.rendered.encode()) == 6734
    assert EstimatedCounter().count(result.rendered) == 1684
    view, value = expanded(result, request)
    exact_selected(value, received)
    outgoing = next(fact for fact in value["facts"] if fact["facet"] == "callees")
    assert {row["symbol"] for row in outgoing["observation"]["callees"]} == {
        "Batch",
        "Batch.cap",
    }
    assert outgoing["qualification"]["negative_claim_supported"] is False
    assert view.canonical_text == result.rendered
    assert dict(view.canonical_accounting) == dict(result.accounting)
    assert view.accounting["used_tokens"] == EstimatedCounter().count(view.rendered)
    assert view.accounting["scope"] == "emitted-text-without-host-chat-framing"
    assert (
        view.accounting["mode"] == "estimated"
        and not view.accounting["exact_compliance"]
    )
    assert tree(Path("src")) == before and not Path("wiki").exists()


@pytest.mark.parametrize("snapshot", [False, True])
def test_real_native_selected_and_snapshot_preserve_citations_qualifiers_and_receipts(
    tiny, capsys, snapshot
):
    native(tiny, capsys)
    request = native_request(snapshot=snapshot)
    before = tree(Path("src")), tree(Path("wiki"))
    result, received = canonical(request)
    view, value = expanded(result, request)
    exact_selected(value, received)
    assert received["storage"]["whole_store_validated"] is False
    assert view.canonical_text == result.rendered
    assert (tree(Path("src")), tree(Path("wiki"))) == before


def test_real_stale_executable_fact_is_not_structural_or_behavior_equivalence(
    tiny, capsys
):
    native(tiny, capsys)
    Path("src/policy.py").write_text(
        POLICY_SOURCE.replace("values[:limit]", "values[:limit - 1]"), encoding="utf-8"
    )
    request = native_request()
    result, received = canonical(request)
    _, value = expanded(result, request)
    exact_selected(value, received)
    method = next(fact for fact in value["facts"] if fact["facet"] == "source-contract")
    assert method["observation"]["implementation"]["state"] == "changed"
    assert method["qualification"]["behavior"] == "not-evaluated"


def test_real_selected_header_review_remains_unavailable_authority(tiny, capsys):
    native(tiny, capsys, adopted=True, indexed=True)
    request = native_request()
    result, received = canonical(request)
    _, value = expanded(result, request)
    exact_selected(value, received)
    concept = next(fact for fact in value["facts"] if fact["facet"] == "concept")
    summary = concept["observation"]["concept"]["maintenance"]
    assert summary["analysis_scope"] == "selected-header"
    assert summary["availability"] == "partial"
    assert not summary["live_evaluation_performed"]
    assert summary["pending"] == summary["acknowledged"] == 0


def test_real_absent_native_and_behavior_gaps_survive_source_facts(tiny):
    request = tiny_request()
    request["options"]["knowledge_mode"] = "auto"
    request["requirements"].extend(
        [
            {
                "id": "native",
                "facet": "concept",
                "selector": "llm-wiki://entities/Batch",
            },
            {"id": "behavior", "facet": "behavior", "selector": "policy.py:Batch.cap"},
        ]
    )
    result, received = canonical(request)
    _, value = expanded(result, request)
    exact_selected(value, received)
    missing = {row["requirement_id"]: row for row in value["coverage"]}
    assert not missing["native"]["satisfied"] and not missing["behavior"]["satisfied"]
    assert value["state"] != "covered"


def test_real_duplicate_owner_ambiguity_and_bounded_graph_are_not_complete(
    tmp_path, monkeypatch
):
    materialize("library", tmp_path.resolve())
    monkeypatch.chdir(tmp_path)
    request = tiny_request()
    request["requirements"].append(
        {
            "id": "duplicate",
            "facet": "source-contract",
            "selector": "scope.py:Repeated.touch",
        }
    )
    request["options"]["max_graph_items"] = 1
    result, received = canonical(request)
    _, value = expanded(result, request)
    exact_selected(value, received)
    duplicate = next(
        row for row in value["coverage"] if row["requirement_id"] == "duplicate"
    )
    assert duplicate["state"] == "ambiguous" and not duplicate["satisfied"]
    outgoing = next(fact for fact in value["facts"] if fact["facet"] == "callees")
    assert outgoing["observation"]["bounds"]["callees"] == {
        "total": 2,
        "returned": 1,
        "truncated": True,
    }


@pytest.mark.parametrize("state", ["flat", "corrupt", "required-absent"])
def test_rejected_real_native_input_has_no_compact_success(tiny, capsys, state):
    if state != "required-absent":
        api.bootstrap_wiki("src", "wiki")
        capsys.readouterr()
    if state == "corrupt":
        migrate_knowledge_storage(
            Path("wiki"), to="sharded-v2", recovery_dir=Path("recovery")
        )
        Path("wiki/.llm-wiki-knowledge.json").write_bytes(b"{}\n")
    before = tree(Path("src")), tree(Path("wiki"))
    with pytest.raises(api.LlmWikiApiError):
        api.build_task_context(
            native_request(snapshot=True), src_dir="src", wiki_dir="wiki"
        )
    assert (tree(Path("src")), tree(Path("wiki"))) == before


def test_canonical_and_compact_budget_failures_are_separate_and_unsalvageable(tiny):
    request = tiny_request()
    result, received = canonical(request)
    failure = task_compact.render_compact_task_context(
        result, request, view_options=view_options(1)
    )
    assert (
        not failure.ok
        and failure.error == "cannot-fit-compact"
        and failure.rendered == ""
    )
    assert "facts" not in failure.to_payload()
    assert failure.canonical_text == result.rendered
    assert failure.accounting["minimum_tokens"] > 1
    diagnostic = failure.to_payload()["diagnostic_accounting"]
    assert diagnostic["used_tokens"] == EstimatedCounter().count(
        failure.diagnostic_rendered
    )
    assert diagnostic["scope"] == "failure-diagnostic-text-without-host-framing"
    request["options"]["budget_tokens"] = 1
    canonical_failure = api.build_task_context(request, src_dir="src", wiki_dir="wiki")
    assert not canonical_failure.ok and canonical_failure.rendered == ""
    with pytest.raises(task_compact.TaskCompactError):
        task_compact.render_compact_task_context(
            canonical_failure, request, view_options=view_options(1)
        )


def test_pure_saved_result_conversion_does_not_claim_current_filesystem_validation(
    tiny,
):
    request = tiny_request()
    result, received = canonical(request)
    Path("src/policy.py").write_text(
        POLICY_SOURCE.replace("values[:limit]", "values[:1]"), encoding="utf-8"
    )
    _, value = expanded(result, request)
    exact_selected(value, received)
    assert Path("src/policy.py").read_text() != POLICY_SOURCE


def reseal_view(value):
    """Recompute body identity/accounting so corruption cannot fail only its hash."""
    value = deepcopy(value)
    counter = EstimatedCounter()
    for _ in range(8):
        value["view_id"] = content_id(
            COMPACT_SCHEMA,
            {key: item for key, item in value.items() if key != "view_id"},
        )
        rendered = canonical_json(value).decode()
        counted = counter.count(rendered)
        if value["accounting"]["used_tokens"] == counted:
            return rendered
        value["accounting"]["used_tokens"] = counted
    raise AssertionError("Rehashed compact accounting did not converge")


def fact_row(value: dict[str, Any], facet):
    assert value["facts"]["columns"] == FACT_FIELDS
    return next(row for row in value["facts"]["rows"] if row[1] == facet)


def test_wire_references_keep_exact_fact_ids_selectors_citations_and_shared_exceptions(
    tiny,
):
    request = tiny_request()
    result, captured = canonical(request)
    view, _ = expanded(result, request)
    payload = view.to_payload()
    assert payload["facts"]["columns"] == FACT_FIELDS
    assert payload["requirements"]["columns"] == REQUIREMENT_FIELDS
    assert len(payload["facts"]["rows"]) == len(captured["facts"]) == 2
    for row, original in zip(payload["facts"]["rows"], captured["facts"]):
        assert row[:4] == [original[key] for key in FACT_FIELDS[:4]]
        assert [payload["citations"][ref] for ref in row[5]] == original["citations"]
        assert {**payload["shared_qualification"], **row[6]} == original[
            "qualification"
        ]
    for row in payload["requirements"]["rows"]:
        original = next(
            item for item in request["requirements"] if item["id"] == row[0]
        )
        assert row[:4] == [original[key] for key in REQUIREMENT_FIELDS[:4]]
        observed = next(
            item for item in captured["coverage"] if item["requirement_id"] == row[0]
        )
        assert row[4:7] == [observed[key] for key in ("state", "satisfied", "reason")]
        assert [payload["facts"]["rows"][ref][0] for ref in row[7]] == observed[
            "fact_ids"
        ]


@pytest.mark.parametrize(
    "mutation",
    [
        "fact-loss",
        "fact-id",
        "selector",
        "citation-identity",
        "citation-unbound",
        "negative-upgrade",
        "scope-upgrade",
        "query-bounds",
        "inner-constructor-substitution",
        "canonical-id",
        "whole-store",
        "requirement-loss",
        "fact-reference",
        "unsupported-schema",
        "extra-field",
    ],
)
def test_self_rehashed_view_cannot_drop_upgrade_or_unbind_canonical_evidence(
    tiny, mutation
):
    request = tiny_request()
    result, _ = canonical(request)
    view, _ = expanded(result, request)
    payload = view.to_payload()
    if mutation == "fact-loss":
        payload["facts"]["rows"].pop()
    elif mutation == "fact-id":
        payload["facts"]["rows"][0][0] = "sha256:" + "0" * 64
    elif mutation == "selector":
        payload["facts"]["rows"][0][2] = "policy.py:Batch#2"
    elif mutation == "citation-identity":
        payload["citations"][0]["source_identity"] = "sha256:" + "0" * 64
    elif mutation == "citation-unbound":
        payload["facts"]["rows"][0][5] = [len(payload["citations"])]
    elif mutation == "negative-upgrade":
        payload["shared_qualification"]["negative_claim_supported"] = True
    elif mutation == "scope-upgrade":
        payload["shared_qualification"]["analysis_scope"] = "full-inventory"
    elif mutation == "query-bounds":
        fact_row(payload, "callees")[4]["value"]["bounds"]["callees"]["total"] = 1
    elif mutation == "inner-constructor-substitution":
        method = next(
            row
            for row in fact_row(payload, "callees")[4]["value"]["callees"]
            if row["symbol"] == "Batch.cap"
        )
        method["symbol"] = "Batch"
    elif mutation == "canonical-id":
        payload["canonical"]["result_id"] = "sha256:" + "0" * 64
    elif mutation == "whole-store":
        payload["native"]["whole_store_validated"] = True
    elif mutation == "requirement-loss":
        payload["requirements"]["rows"].pop()
    elif mutation == "fact-reference":
        payload["requirements"]["rows"][0][7] = [len(payload["facts"]["rows"])]
    elif mutation == "unsupported-schema":
        payload["schema_version"] = "llm-wiki-task-compact/v999"
    else:
        payload["execute"] = "untrusted instruction"
    altered = reseal_view(payload)
    assert (
        content_id(
            COMPACT_SCHEMA,
            {
                key: item
                for key, item in json.loads(altered).items()
                if key != "view_id"
            },
        )
        == json.loads(altered)["view_id"]
    )
    with pytest.raises(task_compact.TaskCompactError):
        task_compact.validate_compact_task_context(
            altered, result.rendered, request, view_options=view_options()
        )


def test_self_rehashed_missing_native_and_behavior_gaps_cannot_be_hidden(tiny):
    request = tiny_request()
    request["requirements"].append(
        {"id": "behavior", "facet": "behavior", "selector": "policy.py:Batch.cap"}
    )
    result, _ = canonical(request)
    view, _ = expanded(result, request)
    payload = view.to_payload()
    row = next(row for row in payload["requirements"]["rows"] if row[0] == "behavior")
    row[4:7] = ["present", True, "verified-behavior"]
    payload["state"] = "covered"
    payload["omissions"] = []
    with pytest.raises(task_compact.TaskCompactError):
        task_compact.validate_compact_task_context(
            reseal_view(payload), result.rendered, request, view_options=view_options()
        )


def test_self_rehashed_selected_header_cannot_become_current_review_authority(
    tiny, capsys
):
    native(tiny, capsys, adopted=True, indexed=True)
    request = native_request()
    result, _ = canonical(request)
    view, _ = expanded(result, request)
    payload = view.to_payload()
    concept = fact_row(payload, "concept")[4]["value"]["concept"]
    summary = concept["maintenance"]
    summary.update(
        availability="ready",
        analysis_scope="full-inventory",
        live_evaluation_performed=True,
        acknowledged=summary["total"],
        unavailable=0,
    )
    with pytest.raises(task_compact.TaskCompactError):
        task_compact.validate_compact_task_context(
            reseal_view(payload), result.rendered, request, view_options=view_options()
        )


@pytest.mark.parametrize("host_change", ["request", "profile", "counter", "budget"])
def test_original_request_profile_counter_and_view_budget_are_required(
    tiny, host_change
):
    request = tiny_request()
    result, _ = canonical(request)
    view, _ = expanded(result, request)
    host = {}
    options = view_options()
    if host_change == "request":
        request["kind"] = "orientation"
    elif host_change == "profile":
        host["profile"] = {
            "schema_version": "llm-wiki-workflow-profile/v1",
            "settings": {"max_graph_items": 1},
        }
    elif host_change == "counter":

        class OtherCounter(EstimatedCounter):
            identity = "different-host-counter/v1"

        host["counter"] = OtherCounter()
    else:
        options = view_options(30000)
    with pytest.raises(ValueError):
        task_compact.validate_compact_task_context(
            view.rendered, result.rendered, request, view_options=options, **host
        )


def test_compact_cannot_salvage_self_rehashed_false_canonical_qualification(tiny):
    request = tiny_request()
    result, value = canonical(request)
    remap = {}
    for fact in value["facts"]:
        old_id = fact["fact_id"]
        fact["qualification"]["negative_claim_supported"] = True
        fact["fact_id"] = content_id(
            "llm-wiki-task-fact/v1",
            {key: item for key, item in fact.items() if key != "fact_id"},
        )
        remap[old_id] = fact["fact_id"]
    for row in value["coverage"]:
        row["fact_ids"] = [remap[identity] for identity in row["fact_ids"]]
    value["result_id"] = content_id(
        "llm-wiki-task-context/v2",
        {key: item for key, item in value.items() if key != "result_id"},
    )
    with pytest.raises(ValueError):
        task_compact.render_compact_task_context(
            canonical_json(value).decode(), request, view_options=view_options()
        )


def test_portably_valid_literal_metadata_cannot_collide_with_compact_defaults(tiny):
    request = tiny_request()
    _, payload = canonical(request)
    fact = next(fact for fact in payload["facts"] if fact["facet"] == "source-contract")
    literal = {"from": "parameters"}
    fact["observation"]["contract"]["methods"][0]["data_effects"]["inputs"] = literal
    old_id = fact["fact_id"]
    fact["fact_id"] = content_id(
        "llm-wiki-task-fact/v1",
        {key: item for key, item in fact.items() if key != "fact_id"},
    )
    for row in payload["coverage"]:
        row["fact_ids"] = [
            fact["fact_id"] if identity == old_id else identity
            for identity in row["fact_ids"]
        ]
    payload["result_id"] = content_id(
        payload["schema_version"],
        {key: item for key, item in payload.items() if key != "result_id"},
    )
    text = canonical_json(payload).decode()
    captured = api.validate_task_context(text, request)
    view = task_compact.render_compact_task_context(
        text, request, view_options=view_options()
    )
    assert view.ok
    value = task_compact.expand_compact_task_context(
        view.rendered, text, request, view_options=view_options()
    )
    exact_selected(value, captured)
    output = next(fact for fact in value["facts"] if fact["facet"] == "source-contract")
    assert (
        output["observation"]["contract"]["methods"][0]["data_effects"]["inputs"]
        == literal
    )


class CharacterTokenCounter:
    """Trusted deterministic test tokenizer: one Unicode scalar per token."""

    identity = "test-character-tokenizer/v1"
    exact = True

    def count(self, text):
        return len(text)


@pytest.mark.parametrize("exact", [False, True])
def test_unicode_full_emission_counter_identity_and_host_framing_are_distinct(
    tiny, exact
):
    request = tiny_request()
    request["text"] = (
        "Inspect María's cap.\n保持 λ 📚 without changing selected evidence."
    )
    counter = CharacterTokenCounter() if exact else EstimatedCounter()
    request["options"]["budget_mode"] = "exact" if exact else "estimated"
    result, received = canonical(request, counter=counter)
    view, value = expanded(result, request, counter=counter)
    exact_selected(value, received)
    assert value["intent"]["text"] == request["text"]
    assert view.rendered.endswith("\n") and "保持" in view.rendered
    assert len(view.rendered.encode()) > len(view.rendered)
    assert (
        view.accounting["counter_id"]
        == result.accounting["counter_id"]
        == counter.identity
    )
    assert view.accounting["used_tokens"] == counter.count(view.rendered)
    assert view.accounting["exact_compliance"] is exact
    assert (
        counter.count("Host framing:\n" + view.rendered)
        > view.accounting["used_tokens"]
    )


def test_production_tiny_size_gate_is_measured_without_dropping_required_facts(tiny):
    request = tiny_request()
    result, received = canonical(request)
    view, value = expanded(result, request)
    exact_selected(value, received)
    counter = EstimatedCounter()
    baseline, compact = counter.count(result.rendered), counter.count(view.rendered)
    assert baseline == 1684
    assert compact == view.accounting["used_tokens"]
    size_admitted = compact <= 1000 and compact <= baseline * 0.5
    # A size miss cannot make correctness pass or remove facts. Default adoption
    # remains a separate Root decision; this test records truthful production size.
    assert type(size_admitted) is bool
    bounded = task_compact.render_compact_task_context(
        result, request, view_options=view_options(1000)
    )
    if compact > 1000:
        assert not bounded.ok and bounded.error == "cannot-fit-compact"
    else:
        assert bounded.ok
        assert (
            task_compact.expand_compact_task_context(
                bounded.rendered,
                result.rendered,
                request,
                view_options=view_options(1000),
            )["facts"]
            == received["facts"]
        )


@pytest.mark.parametrize("invalid", [True, 0, 32001, "1000"])
def test_view_budget_is_strict_and_cannot_broaden_trusted_ceiling(tiny, invalid):
    request = tiny_request()
    result, _ = canonical(request)
    before = tree(Path("src"))
    with pytest.raises(task_compact.TaskCompactError):
        task_compact.render_compact_task_context(
            result, request, view_options=view_options(invalid)
        )
    assert tree(Path("src")) == before


@pytest.mark.parametrize("malformed", ["duplicate-key", "noncanonical", "nonfinite"])
def test_receiver_refuses_duplicate_noncanonical_or_nonfinite_json(tiny, malformed):
    request = tiny_request()
    result, _ = canonical(request)
    view, _ = expanded(result, request)
    if malformed == "duplicate-key":
        altered = '{"view_id":' + json.dumps(view.view_id) + "," + view.rendered[1:]
    elif malformed == "noncanonical":
        altered = " " + view.rendered
    else:
        altered = '{"unexpected":NaN,' + view.rendered[1:]
    with pytest.raises(task_compact.TaskCompactError):
        task_compact.validate_compact_task_context(
            altered, result.rendered, request, view_options=view_options()
        )
