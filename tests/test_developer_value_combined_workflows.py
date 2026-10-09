"""Continuous current-provider workflows on newly frozen owned inputs."""

from __future__ import annotations

from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path

import pytest

from llm_wiki_cli import api
from tests.developer_value.combined_workflows import (
    ADOPTED, AFTER_PROSE, BEFORE_PROSE, NATIVE, SOURCES, VARIANTS,
    client_after, input_packet, packet_sha256, prepare_combined, reconcile_queue,
    request_for, source_after,
)
from tests.developer_value.workflow_fixtures import VIEW, record_workflow_trace, sync_workflow, write_description
from tests.developer_value.workflow_oracles import REQUIRED_GAP_STATES, assert_coverage_gap, assert_coverage_preserved, assert_read_only
from tests.test_developer_value_after_change import _ack, _assert_writer_preserves_authority, _restart_status, _row


def _inventory(tree):
    return {path: hashlib.sha256(raw).hexdigest() for path, raw in tree.items()}


def _trace_value(value):
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, dict):
        return {key: _trace_value(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_trace_value(item) for item in value]
    if callable(getattr(value, "metadata", None)):
        canonical = getattr(value, "canonical", None)
        view = getattr(value, "view", None)
        return {"metadata": value.metadata(), "canonical_text": canonical.rendered if canonical is not None else None,
                "compact_text": view.rendered if view is not None else None,
                "validation_scope": getattr(value, "validation_scope", None)}
    if hasattr(value, "rendered"):
        return {"rendered": value.rendered}
    raise TypeError("Unsupported actual workflow response type: " + type(value).__name__)


def _atomic_progress(project, observations):
    destination = os.environ.get("AGENT_WIKI_WORKFLOW_TRACE_DIR")
    if destination is None:
        return
    output = Path(destination).resolve()
    assert not output.is_relative_to(project.root)
    output.mkdir(parents=True, exist_ok=True)
    target = output / ("combined-progress-" + project.variant + ".json")
    temporary = target.with_suffix(".tmp")
    value = {"schema_version": "owned-workflow-trace/v1", "scenario": "combined-progress", "variant": project.variant,
             "model_productivity_measured": False,
             "source_hashes": {path: hashlib.sha256((project.source / path).read_bytes()).hexdigest() for path in SOURCES},
             "observations": observations}
    temporary.write_text(json.dumps(value, sort_keys=True, indent=2, ensure_ascii=False) + "\n")
    temporary.replace(target)


@pytest.mark.parametrize("variant", VARIANTS)
def test_combined_current_workflow_preserves_authority_gaps_and_repaired_callers(tmp_path, monkeypatch, capsys, variant):
    monkeypatch.chdir(tmp_path)
    project = prepare_combined(tmp_path, variant)
    capsys.readouterr()
    request = request_for(variant)
    retained_request = deepcopy(request)
    observations = {"input_packet_sha256": packet_sha256(), "per_operation_reads": [], "queues": [],
                    "runtime_behavior": "not-executed", "human_approval": False}

    def read(label, operation):
        before = project.tree()
        before_mtime = {path: (project.root / path).stat().st_mtime_ns for path in before}
        result = None
        error = None
        try:
            result = operation()
        except Exception as exc:
            error = {"type": type(exc).__name__, "message": str(exc), "code": getattr(exc, "code", None), "details": getattr(exc, "details", None)}
            raise
        finally:
            after = project.tree()
            after_mtime = {path: (project.root / path).stat().st_mtime_ns for path in after}
            observations["per_operation_reads"].append({"operation": label, "before": _inventory(before), "after": _inventory(after),
                                                       "before_mtime_ns": before_mtime, "after_mtime_ns": after_mtime,
                                                       "response": _trace_value(result), "error": error})
            _atomic_progress(project, observations)
            assert_read_only(before, after)
            assert before_mtime == after_mtime, "Read rewrote an artifact even when its bytes were preserved"
            assert not (project.root / "source-execution-tripwire").exists()
        return result

    def payload(reply, *, profile=None):
        assert reply.state == "full" and reply.canonical is not None and reply.view is not None
        assert reply.view.ok and reply.view.canonical_text == reply.canonical.rendered
        canonical = api.validate_task_context(reply.canonical.rendered, request, policy=project.context_options["policy"], profile=profile)
        expanded = api.expand_compact_task_context(reply.view.rendered, reply.canonical.rendered, request,
            view_options=VIEW, policy=project.context_options["policy"], profile=profile)
        assert_coverage_preserved(canonical, expanded)
        decisive = next(row for row in expanded["coverage"] if row["requirement_id"] == "decisive")
        assert decisive["satisfied"] and len(decisive["fact_ids"]) == 1
        contract = next(row for row in expanded["facts"] if row["fact_id"] == decisive["fact_ids"][0])
        assert contract["selector"] == "policy.py:Harbor.route#1"
        assert next(row for row in contract["observation"]["contract"]["params"] if row["name"] == "limit")["default"] == "4"
        for identity, states in REQUIRED_GAP_STATES.items():
            assert_coverage_gap(expanded, identity, states=states)
        if variant == "native-absent":
            for identity in ("concept", "prose"):
                assert_coverage_gap(expanded, identity, states={"unavailable"})
        return canonical

    def callers(stage):
        results = {}
        for target, expected in input_packet()["caller_expectations"].items():
            result = read(stage + ":callers:" + target, lambda target=target: api.callers(target, **project.options))
            assert {row["file"] + ":" + row["symbol"] for row in result["callers"]} == set(expected)
            coverage = result.get("coverage")
            assert coverage is not None and coverage["runtime_completeness"] is False
            results[target] = result
        for selector in ("hazards.py:namespace_route", "hazards.py:conditional_route", "client.py:dynamic_route"):
            result = read(stage + ":callees:" + selector, lambda selector=selector: api.callees(selector, **project.options))
            assert not any(row.get("symbol") in {"NamespaceHarbor.route", "EarlyHarbor.route", "LaterHarbor.route", "Harbor.route"}
                           and row.get("file") is not None for row in result["callees"])
            results[selector] = result
        return results

    def queue(stage):
        if variant in {"source-only", "native-absent"}:
            observations["queues"].append({"stage": stage, "status": "uninvoked",
                "reason": "no-owned-native-prose-workflow", "solved": False})
            return
        response = read(stage + ":queue", lambda: api.build_maintenance_queue(**project.options, limit=1000))
        sources = read(stage + ":source-snapshots", lambda: {path: (project.source / path).read_text() for path in SOURCES})
        prose = read(stage + ":prose-snapshot", lambda: (project.wiki / "entities/Harbor.md").read_text())
        observations["queues"].append({"stage": stage, "response": response,
            "reconciliation": reconcile_queue(response, stage, sources=sources, prose=prose,
                durable_owner_available=not (variant == "legacy" and stage == "pending-after-sync"))})
        if variant == "legacy" and stage == "pending-after-sync":
            reconciliation = observations["queues"][-1]["reconciliation"]
            assert reconciliation["unavailable_unsolved"] and reconciliation["missing_owner_actions"]

    if variant == "source-only":
        discovery = read("discover-source", lambda: api.build_task_context({"schema_version": "llm-wiki-task-request/v2",
            "anchors": [{"kind": "source", "value": "policy.py"}], "options": {"knowledge_mode": "off", "read_scope": "full-inventory"}}, **project.context_options))
        assert discovery.ok
        assert "policy.py:Harbor.route#1" in {fact["selector"] for fact in discovery.to_payload()["facts"]}
        observations["discovery"] = discovery.to_payload()
    else:
        discovery = read("discover-wiki", lambda: api.search_wiki("Harbor", discovery="qualified-v1" if variant in NATIVE or variant == "native-absent" else None, **project.options))
        observations["discovery"] = discovery
        if variant != "native-absent":
            selected = next(row for row in discovery["results"] if row["path"] == "entities/Harbor.md")
            exact = read("exact-inspect", lambda: api.inspect_concept(selected["path"], live=False, **project.options))
            assert exact["concept"]["found"] and not exact["concept"]["ambiguous"]
            observations["exact"] = exact
    assert read("decisive-source", lambda: (project.source / "policy.py").read_text()) == SOURCES["policy.py"]
    observations["callers_before"] = callers("before")
    queue("before")
    stale_status = None
    if variant in ADOPTED:
        status = read("before:status", lambda: api.get_maintenance_status(**project.options, live=True, limit=1000))
        _ack(project, status, _row(status, "Harbor"))
        stale_status = read("before:acknowledged-status", lambda: api.get_maintenance_status(**project.options, live=True, limit=1000))

    with api.open_context_session(**project.context_options) as owner:
        first = read("before:compact", lambda: owner.read_compact(request, view_options=VIEW))
        before_payload = payload(first)
        identity = (before_payload["request_id"], before_payload["result_id"])
        historical = read("before:historical-receipt", lambda: owner.canonical_receipt(*identity))
        assert historical.validation_scope == "historical-captured"
        if variant == "native-absent":
            with pytest.raises(api.InvalidRequestError, match="historical only"):
                read("before:unavailable-current-receipt", lambda: owner.canonical_receipt(*identity, current=True))
            observations["current_receipt_before"] = {"availability": "unavailable", "solved": False}
            # A failed lookup clears custody; retain a fresh actual receipt.
            first = read("before:recapture-after-current-refusal", lambda: owner.read_compact(request, view_options=VIEW))
            assert payload(first) == before_payload
        else:
            current_receipt = read("before:current-receipt", lambda: owner.canonical_receipt(*identity, current=True))
            assert current_receipt.validation_scope == "current-revalidated"
        (project.source / "policy.py").write_text(source_after())
        (project.source / "client.py").write_text(client_after())
        assert read("source-edited:exact-source-bytes", lambda: {path: (project.source / path).read_text() for path in SOURCES}) == {
            **SOURCES, "policy.py": source_after(), "client.py": client_after()}
        assert "records[max(0, len(records) - limit):]" in (project.source / "policy.py").read_text()
        assert "limit=2" in (project.source / "client.py").read_text()
        historical_after = read("source-edited:historical-receipt", lambda: owner.canonical_receipt(*identity))
        assert historical_after.canonical.rendered == historical.canonical.rendered
        with pytest.raises(api.LlmWikiApiError):
            read("source-edited:current-refusal", lambda: owner.canonical_receipt(*identity, current=True))
        observations["callers_after"] = callers("after-source-edit")
        queue("after-source-edit")
        if stale_status is not None:
            rejection_before = project.tree()
            with pytest.raises(api.WorkspaceStateError) as stale_ack:
                _ack(project, stale_status, _row(stale_status, "Harbor"))
            assert stale_ack.value.code == "maintenance-conflict"
            _assert_writer_preserves_authority(rejection_before, project.tree())
            overlay = read("source-edited:status", lambda: api.get_maintenance_status(**project.options, live=True, limit=1000))
            assert _row(overlay, "Harbor")["effective_status"] == "pending"
            observations["pending_overlay"] = overlay
        if variant not in {"source-only", "native-absent"}:
            sync_workflow(project)
            assert BEFORE_PROSE in (project.wiki / "entities/Harbor.md").read_text()
            if variant in ADOPTED:
                durable = read("pending:restart", lambda: _restart_status(project))
                assert _row(durable, "Harbor")["recorded_status"] == "pending"
                observations["pending_restart"] = durable
            queue("pending-after-sync")
            write_description(project, AFTER_PROSE, "entities/Harbor.md")
            if variant in ADOPTED:
                dirty = read("prose-edited:status", lambda: api.get_maintenance_status(**project.options, live=True, limit=1000))
                assert dirty["requires_sync"]
                rejection_before = project.tree()
                with pytest.raises(api.WorkspaceStateError) as dirty_ack:
                    _ack(project, dirty, _row(dirty, "Harbor"))
                assert dirty_ack.value.code == "maintenance-conflict"
                _assert_writer_preserves_authority(rejection_before, project.tree())
            sync_workflow(project)
            assert AFTER_PROSE in (project.wiki / "entities/Harbor.md").read_text()
            queue("after-prose-sync")
            if variant in ADOPTED:
                fresh = read("reviewed:status", lambda: api.get_maintenance_status(**project.options, live=True, limit=1000))
                ack = _ack(project, fresh, _row(fresh, "Harbor"))
                assert ack["actor"]["kind"] == "agent" and ack["governance_effect"] == "none"
                acknowledged = read("acknowledged:restart", lambda: _restart_status(project))
                assert _row(acknowledged, "Harbor")["recorded_status"] == "acknowledged"
                observations["acknowledgment"] = ack
            queue("acknowledged")
        else:
            observations["maintenance"] = {"status": "uninvoked", "reason": "no-owned-native-prose-workflow",
                "agent_acknowledgment": None, "solved": False}
        with api.open_context_session(**project.context_options) as resumed_owner:
            resumed = read("source:resume", lambda: resumed_owner.read_compact(request, view_options=VIEW, if_result_id=first.result_id))
            after_payload = payload(resumed)
            assert after_payload["task_id"] == before_payload["task_id"]
            assert after_payload["result_id"] != before_payload["result_id"]
            with pytest.raises(api.InvalidRequestError, match="not retained"):
                read("new-owner:old-receipt-refusal", lambda: resumed_owner.canonical_receipt(*identity))
            resumed = read("source:recapture-after-custody-refusal", lambda: resumed_owner.read_compact(request, view_options=VIEW))
            assert payload(resumed) == after_payload
            current_identity = (after_payload["request_id"], after_payload["result_id"])
            if variant in NATIVE:
                write_description(project, AFTER_PROSE + " Agent review is ordinary maintenance.", "entities/Harbor.md")
                saved = read("wiki-edit:historical-receipt", lambda: resumed_owner.canonical_receipt(*current_identity))
                assert resumed.canonical is not None
                assert saved.canonical.rendered == resumed.canonical.rendered
                with pytest.raises(api.LlmWikiApiError):
                    read("wiki-edit:current-refusal", lambda: resumed_owner.canonical_receipt(*current_identity, current=True))
                sync_workflow(project)
            else:
                guide = project.wiki / "guides/unconsumed.md"
                guide.parent.mkdir(parents=True, exist_ok=True)
                guide.write_text("# Unconsumed orientation edit\n")
            with api.open_context_session(**project.context_options) as wiki_owner:
                wiki_reply = read("wiki:resume", lambda: wiki_owner.read_compact(request, view_options=VIEW, if_result_id=resumed.result_id))
                wiki_payload = payload(wiki_reply)
                assert wiki_payload["task_id"] == after_payload["task_id"]
                assert (wiki_payload["result_id"] != after_payload["result_id"]) is (variant in NATIVE)
            observations["callers_after_restart_and_wiki"] = callers("after-restart-and-wiki")
            selection = project.source / ".llm-wiki/source-selection.json"
            if selection.exists():
                selection_value = json.loads(selection.read_text())
            else:
                selection.parent.mkdir()
                selection_value = {"schema_version": "llm-wiki-source-selection/v1", "include": list(SOURCES), "exclude": []}
            selection.write_text(json.dumps(selection_value, indent=4, sort_keys=True) + "\n")
            if variant in NATIVE:
                with pytest.raises(api.LlmWikiApiError):
                    read("selection-edit:required-native-refusal", lambda: resumed_owner.read_compact(request, view_options=VIEW))
                sync_workflow(project)
            with api.open_context_session(**project.context_options) as configured_owner:
                configured = read("configuration:resume", lambda: configured_owner.read_compact(request, view_options=VIEW, if_result_id=wiki_reply.result_id))
                configured_payload = payload(configured)
                assert configured_payload["task_id"] == wiki_payload["task_id"]
                assert configured_payload["request_id"] == wiki_payload["request_id"]
                assert configured_payload["source_capture"]["selection_inputs"] != wiki_payload["source_capture"]["selection_inputs"]
            observations.update({"before": before_payload, "after_source": after_payload, "after_wiki": wiki_payload,
                                 "after_configuration": configured_payload, "historical_canonical": historical.canonical.rendered})
            if variant in {"source-only", "native-absent"}:
                with pytest.raises(api.InvalidRequestError) as configured_query:
                    read("configuration:caller-query-refusal", lambda: api.callers("policy.py:Harbor.route", **project.options))
                assert configured_query.value.details is not None
                assert configured_query.value.details["field"] == "source_selection"
                observations["configured_live_caller_query"] = {"availability": "unavailable-without-matching-wiki-manifest",
                    "code": configured_query.value.code, "solved": False}
            else:
                if variant not in NATIVE:
                    sync_workflow(project)
                observations["callers_after_restart_and_configuration"] = callers("after-restart-and-configuration")
    assert request == retained_request
    if variant not in ADOPTED:
        assert not (project.wiki / ".llm-wiki-maintenance-adoption.json").exists()
    record_workflow_trace(project, "combined-current", observations)


def test_source_obligations_do_not_follow_provider_self_labels():
    response = {"items": [{"path": "entities/Harbor.md", "classification": "informational", "score": 0},
                          {"path": "entities/Unrelated.md", "classification": "actionable", "score": 999}],
                "total": 2, "returned": 2, "omitted": 0, "truncated": False, "advisory": True}
    result = reconcile_queue(response, "after-source-edit", sources={**SOURCES, "policy.py": source_after(), "client.py": client_after()}, prose=BEFORE_PROSE)
    assert result["denominator"] == 2
    assert [row["label"] for row in result["rows"]] == ["actionable", "unknown"]
    assert result["not_an_acceptance_score"] and not result["provider_labels_used"]


def test_absent_required_owner_and_truncated_queue_cannot_be_complete_reconciliation():
    response = {"items": [], "total": 0, "returned": 0, "omitted": 0, "truncated": False, "advisory": True}
    with pytest.raises(AssertionError, match="not surfaced"):
        reconcile_queue(response, "pending-after-sync", sources={**SOURCES, "policy.py": source_after(), "client.py": client_after()}, prose=BEFORE_PROSE)
    with pytest.raises(AssertionError):
        reconcile_queue({**response, "total": 1, "omitted": 1, "truncated": True}, "before", sources=SOURCES, prose=BEFORE_PROSE)


def test_unadopted_pending_gap_keeps_the_obligation_and_earns_no_coverage():
    from llm_wiki_cli.services.maintenance_queue import compose_queue
    response = compose_queue([], [], {}, {}, {})
    result = reconcile_queue(response, "pending-after-sync", sources={**SOURCES, "policy.py": source_after(), "client.py": client_after()},
        prose=BEFORE_PROSE, durable_owner_available=False)
    assert result["required_owner_surfaced"] is False
    assert result["covered_owner_actions"] == []
    assert result["missing_owner_actions"] == [{"owner": "entities/Harbor.md:Harbor", "operation": "revise-claim"}]
    assert result["unavailable_unsolved"] and result["not_an_acceptance_score"]


@pytest.mark.parametrize("field,value", [("availability", "ready"), ("durable_owner_available", True),
    ("source_prose_correctness", "correct"), ("review_route", {}), ("limitation", "")])
def test_unadopted_pending_gap_requires_task_facing_negative_capability(field, value):
    from llm_wiki_cli.services.maintenance_queue import compose_queue
    response = compose_queue([], [], {}, {}, {})
    response["qualification"]["ordinary_review_custody"][field] = value
    with pytest.raises(AssertionError):
        reconcile_queue(response, "pending-after-sync", sources={**SOURCES, "policy.py": source_after(), "client.py": client_after()},
            prose=BEFORE_PROSE, durable_owner_available=False)


def test_unadopted_pending_gap_rejects_invisible_qualification():
    response = {"items": [], "total": 0, "returned": 0, "omitted": 0, "advisory": True}
    with pytest.raises(AssertionError, match="task-facing"):
        reconcile_queue(response, "pending-after-sync", sources={**SOURCES, "policy.py": source_after(), "client.py": client_after()},
            prose=BEFORE_PROSE, durable_owner_available=False)
