"""One continuous owned workspace across discovery, change, review and a new session."""

import pytest

from llm_wiki_cli import api
from tests.developer_value.workflow_fixtures import (
    BODY_PROSE, INITIAL_PROSE, VIEW, compact_payload, mutate_source, prepare_workflow,
    record_workflow_trace, run_behavior_oracle, sync_workflow, task_request, write_description,
)
from tests.developer_value.workflow_oracles import (
    REQUIRED_GAP_STATES, SOURCE_CALLERS, assert_clip_behavior, assert_coverage_gap,
    assert_coverage_preserved, assert_read_only, assert_source_change,
)
from tests.test_developer_value_after_change import _ack, _restart_status, _row


@pytest.mark.parametrize("variant", ["sharded", "packed"])
def test_complete_workflow_keeps_one_task_and_separate_source_prose_review_authorities(tmp_path, monkeypatch, capsys, variant):
    monkeypatch.chdir(tmp_path)
    project = prepare_workflow(tmp_path, variant)
    capsys.readouterr()
    request = task_request(native=True)
    source_before = (project.source / "policy.py").read_bytes()
    before = project.tree()
    discovery = api.search_wiki("Window clip", discovery="qualified-v1", **project.options)
    candidate = next(row for row in discovery["results"] if row["path"] == "entities/Window.md")
    exact = api.inspect_concept(candidate["path"], live=False, **project.options)
    assert exact["concept"]["found"] and not exact["concept"]["ambiguous"]
    _, captured, captured_expanded = compact_payload(project, request)
    assert_coverage_preserved(captured, captured_expanded)
    assert {(row["file"], row["symbol"]) for row in api.callers("policy.py:Window.clip", **project.options)["callers"]} == SOURCE_CALLERS
    assert_read_only(before, project.tree())
    initial_behavior = run_behavior_oracle(project)
    assert_clip_behavior(initial_behavior, "before")
    assert INITIAL_PROSE in (project.wiki / candidate["path"]).read_text()
    initial_status = api.get_maintenance_status(**project.options, live=True, limit=100)
    initial_ack = _ack(project, initial_status, _row(initial_status))
    assert initial_ack["actor"]["kind"] == "agent" and initial_ack["governance_effect"] == "none"

    # Retain an actual host receipt only after the explicit initial owning write.
    with api.open_context_session(**project.context_options) as owner:
        saved = owner.read_compact(request, view_options=VIEW)
        assert saved.canonical is not None and saved.view is not None
        saved_text, saved_id = saved.canonical.rendered, saved.result_id
        saved_value = api.validate_task_context(saved_text, request, policy=project.context_options["policy"])
        mutate_source(project, "body")
        assert_source_change(source_before, (project.source / "policy.py").read_bytes(), "body")
        changed_behavior = run_behavior_oracle(project, "body")
        assert_clip_behavior(changed_behavior, "body")
        before = project.tree()
        live = api.get_maintenance_status(**project.options, live=True, limit=100)
        target = _row(live)
        assert target["effective_status"] == "pending" and "executable-syntax-changed" in target["reasons"]
        assert_read_only(before, project.tree())
        sync_workflow(project)
        assert INITIAL_PROSE in (project.wiki / candidate["path"]).read_text()
        durable = _restart_status(project)
        assert _row(durable)["recorded_status"] == "pending"

        # The agent's prose review records a bounded source/behavior comparison,
        # then explicitly refreshes and acknowledges that exact reviewed basis.
        assert initial_behavior != changed_behavior and "first" in INITIAL_PROSE and "last" in BODY_PROSE
        write_description(project, BODY_PROSE)
        sync_workflow(project)
        reviewed_status = api.get_maintenance_status(**project.options, live=True, limit=100)
        reviewed = _row(reviewed_status)
        acknowledged = _ack(project, reviewed_status, reviewed)
        assert acknowledged["actor"]["kind"] == "agent" and acknowledged["governance_effect"] == "none"
        before = project.tree()
        current_status = api.get_maintenance_status(**project.options, live=True, limit=100)
        assert _row(current_status)["effective_status"] == "acknowledged"
        assert_read_only(before, project.tree())
        # Saved bytes remain a captured historical input; no source edit rewrites them.
        assert saved.canonical.rendered == saved_text

    before = project.tree()
    with api.open_context_session(**project.context_options) as resumed_owner:
        resumed = resumed_owner.read_compact(request, view_options=VIEW, if_result_id=saved_id)
        assert resumed.state == "full" and resumed.canonical is not None and resumed.view is not None
        current = api.validate_task_context(resumed.canonical.rendered, request, policy=project.context_options["policy"])
        expanded = api.expand_compact_task_context(resumed.view.rendered, resumed.canonical.rendered, request,
            view_options=VIEW, policy=project.context_options["policy"])
        assert current["task_id"] == saved_value["task_id"] and current["request_id"] == saved_value["request_id"]
        assert current["result_id"] != saved_value["result_id"] and current["basis"] != saved_value["basis"]
        assert_coverage_preserved(current, expanded)
        for identity, states in REQUIRED_GAP_STATES.items():
            assert_coverage_gap(expanded, identity, states=states)
        _, cold, _ = compact_payload(project, request)
        assert current == cold
        native_fact = next(row for row in current["facts"] if row["facet"] == "concept")
        summary = native_fact["observation"]["concept"]["maintenance"]
        assert summary["analysis_scope"] == "selected-header" and summary["pending"] == summary["acknowledged"] == 0
        assert summary["unavailable"] == summary["total"] > 0
        assert saved_text != resumed.canonical.rendered
    assert_read_only(before, project.tree())
    assert not (project.root / "source-execution-tripwire").exists()
    record_workflow_trace(project, "complete", {"request": request, "discovery": discovery,
        "exact": exact, "before": captured, "saved": saved_value, "after": current,
        "source_behavior_before": initial_behavior, "source_behavior_after": changed_behavior,
        "pending_after_sync_restart": durable, "reviewed_status": reviewed_status,
        "agent_acknowledgment": acknowledged, "current_status": current_status,
        "agent_review_scope": "fixed-owned-source-and-runtime-cases", "human_approval": False,
        "saved_receipt_scope": "historical", "resumed_new_owner_state": "full", "gaps_retained": True})
