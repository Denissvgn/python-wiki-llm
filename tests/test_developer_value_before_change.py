"""Before a change: discover, explicitly inspect, retain gaps, and read decisive source."""

import pytest

from llm_wiki_cli import api
from tests.developer_value.workflow_fixtures import (
    POLICY_SOURCE, compact_payload, prepare_workflow, record_workflow_trace, run_behavior_oracle, task_request,
)
from tests.developer_value.workflow_oracles import (
    SOURCE_CALLERS, FORBIDDEN_SOURCE_CALLERS, REQUIRED_GAP_STATES,
    assert_clip_behavior, assert_coverage_gap, assert_coverage_preserved, assert_read_only,
)


@pytest.mark.parametrize("variant", ["source-only", "legacy", "adopted-flat", "sharded", "packed", "native-absent"])
def test_before_change_has_explicit_discovery_exact_evidence_and_unanswered_remainder(tmp_path, monkeypatch, capsys, variant):
    monkeypatch.chdir(tmp_path)
    project = prepare_workflow(tmp_path, variant)
    capsys.readouterr()
    before = project.tree()
    if variant == "source-only":
        discovery = api.build_task_context({"schema_version": "llm-wiki-task-request/v2",
            "anchors": [{"kind": "source", "value": "policy.py"}],
            "options": {"knowledge_mode": "off", "read_scope": "full-inventory"}}, **project.context_options)
        assert discovery.ok
        assert "policy.py:Window.clip#1" in {fact["selector"] for fact in discovery.to_payload()["facts"]}
    elif variant == "native-absent":
        found = api.search_wiki("Window clipping", discovery="qualified-v1", **project.options)
        assert found["results"] and found.get("discovery", {})["native"]["availability"] == "unavailable"
    else:
        native = variant in {"sharded", "packed"}
        found = api.search_wiki("Window clip", kinds=["entities"],
                               discovery="qualified-v1" if native else None, **project.options)
        # Select the predeclared exact coordinate; a fuzzy rank never makes this decision.
        selected = next(row for row in found["results"] if row["path"] == "entities/Window.md")
        exact = api.inspect_concept(selected["path"], live=False, **project.options)
        assert exact["concept"]["found"] and not exact["concept"]["ambiguous"]
        if native:
            member = next(row for row in found.get("discovery", {})["members"] if row["path"] == selected["path"])
            assert member["next_read"]["resolution_performed"] is False
            assert any(row["recorded_status"] == "pending" for row in member["recorded_review"]["records"])

    request = task_request(native=variant in {"sharded", "packed", "native-absent"})
    if variant == "native-absent":
        request["options"]["knowledge_mode"] = "auto"
    compact, canonical, expanded = compact_payload(project, request)
    assert_coverage_preserved(canonical, expanded)
    for requirement, states in REQUIRED_GAP_STATES.items():
        assert_coverage_gap(expanded, requirement, states=states)
    if variant == "native-absent":
        for requirement in ("concept", "prose"):
            assert_coverage_gap(expanded, requirement, states=("unavailable",))
    elif variant in {"sharded", "packed"}:
        assert all(next(row for row in canonical["coverage"] if row["requirement_id"] == name)["satisfied"]
                   for name in ("concept", "prose"))
        concept = next(fact for fact in canonical["facts"] if fact["facet"] == "concept")
        maintenance = concept["observation"]["concept"]["maintenance"]
        assert maintenance["analysis_scope"] == "selected-header" and maintenance["availability"] == "partial"
        assert maintenance["pending"] == maintenance["acknowledged"] == 0

    decisive = next(row for row in expanded["coverage"] if row["requirement_id"] == "decisive")
    assert decisive["satisfied"] and len(decisive["fact_ids"]) == 1
    contract = next(fact for fact in expanded["facts"] if fact["fact_id"] == decisive["fact_ids"][0])
    assert contract["selector"] == "policy.py:Window.clip#1"
    assert (contract["observation"]["path"], contract["observation"]["symbol"],
            contract["observation"]["occurrence"]) == ("policy.py", "Window.clip", 1)
    assert next(param for param in contract["observation"]["contract"]["params"] if param["name"] == "limit")["default"] == "3"
    callers = api.callers("policy.py:Window.clip", **project.options)
    observed = {(row["file"], row["symbol"]) for row in callers["callers"]}
    assert observed == SOURCE_CALLERS and not observed & FORBIDDEN_SOURCE_CALLERS
    call_coverage = callers.get("coverage")
    assert call_coverage is not None and call_coverage["runtime_completeness"] is False
    unresolved = api.callees("client.py:dynamic_clip", **project.options)
    assert not any(row.get("file") == "policy.py" and row.get("symbol") == "Window.clip"
                   for row in unresolved["callees"])
    assert {(row["symbol"], row["kind"], row["file"]) for row in unresolved["callees"]} == {
        ("factory", "unresolved", None), ("clip", "unresolved", None)}
    unresolved_coverage = unresolved.get("coverage")
    assert unresolved_coverage is not None and unresolved_coverage["runtime_completeness"] is False
    # A direct byte read remains decisive source evidence, independent of extracted fields.
    assert (project.source / "policy.py").read_bytes() == POLICY_SOURCE.encode("utf-8")
    assert_read_only(before, project.tree())
    assert not (tmp_path / "source-execution-tripwire").exists()
    # This separately authorized synthetic oracle is never attributed to the provider read.
    behavior = run_behavior_oracle(project)
    assert_clip_behavior(behavior, "before")
    assert_read_only(before, project.tree())
    assert compact.canonical_text
    record_workflow_trace(project, "before", {"request": request, "canonical": canonical,
        "compact": compact.rendered, "callers": callers, "unresolved": unresolved,
        "behavior_oracle": behavior, "provider_behavior_claim": "not-evaluated",
        "read_only_checked": True})


@pytest.mark.parametrize("variant", ["legacy", "adopted-flat"])
def test_legacy_native_narrow_context_stays_usable_without_implicit_compact_migration(tmp_path, monkeypatch, capsys, variant):
    monkeypatch.chdir(tmp_path)
    project = prepare_workflow(tmp_path, variant)
    capsys.readouterr()
    before = project.tree()
    request = task_request(native=True, schema="v1")
    result = api.build_task_context(request, **project.context_options)
    assert result.ok
    payload = api.validate_task_context(result.rendered, request, policy=project.context_options["policy"])
    assert next(row for row in payload["coverage"] if row["requirement_id"] == "concept")["satisfied"]
    for requirement, states in REQUIRED_GAP_STATES.items():
        assert_coverage_gap(payload, requirement, states=states)
    with pytest.raises(api.InvalidRequestError, match="task v2"):
        compact_payload(project, request)
    with pytest.raises(api.LlmWikiApiError):
        compact_payload(project, task_request(native=True))
    assert_read_only(before, project.tree())
    record_workflow_trace(project, "legacy-native", {"request": request, "canonical": payload,
        "compact_native_v2": "refused", "implicit_migration": False, "read_only_checked": True})


def test_read_round_bound_preserves_omission_instead_of_claiming_absence(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    project = prepare_workflow(tmp_path, "source-only")
    before = project.tree()
    request = task_request()
    request["options"]["max_read_rounds"] = 1
    _, canonical, expanded = compact_payload(project, request)
    omitted = [row["requirement_id"] for row in canonical["coverage"] if row["state"] == "omitted"]
    assert omitted
    for requirement in omitted:
        assert_coverage_gap(expanded, requirement, states=("omitted",))
    assert_read_only(before, project.tree())
    record_workflow_trace(project, "read-bound", {"request": request, "canonical": canonical,
        "bounded_omissions": omitted, "absence_proved_for_omissions": False, "read_only_checked": True})
