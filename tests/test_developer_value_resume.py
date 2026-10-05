"""Owned resume scenarios retain task intent and gaps without stale authority."""

from __future__ import annotations

from copy import deepcopy
import json
from typing import Any

import pytest

from llm_wiki_cli import api
from llm_wiki_cli.services import task_context_v2
from llm_wiki_cli.services.context_packet import ContextPacketUnavailableError
from tests.developer_value.workflow_fixtures import (
    BODY_PROSE, VIEW, WorkflowProject, mutate_source, prepare_workflow, sync_workflow,
    record_workflow_trace, task_request, write_description,
)
from tests.developer_value.workflow_oracles import (
    REQUIRED_GAP_STATES, assert_coverage_gap, assert_coverage_preserved, assert_read_only, assert_source_change,
)

VARIANTS = ("source-only", "legacy", "adopted-flat", "native-absent", "sharded", "packed")


def _project(tmp_path, monkeypatch, variant) -> WorkflowProject:
    monkeypatch.chdir(tmp_path)
    return prepare_workflow(tmp_path, variant)


def _request(project: WorkflowProject) -> dict[str, Any]:
    value = task_request(native=project.variant in {"sharded", "packed", "native-absent"})
    if project.variant == "native-absent":
        value["options"]["knowledge_mode"] = "auto"
    return value


def _payload(project, request, reply, *, profile=None):
    assert reply.state == "full" and reply.canonical is not None and reply.view is not None
    assert reply.view.ok and reply.view.canonical_text == reply.canonical.rendered
    validation = {"policy": project.context_options["policy"], "profile": profile}
    canonical = api.validate_task_context(reply.canonical.rendered, request, **validation)
    expanded = api.expand_compact_task_context(reply.view.rendered, reply.canonical.rendered, request,
                                              view_options=VIEW, **validation)
    assert_coverage_preserved(canonical, expanded)
    _gaps(canonical)
    return canonical, expanded


def _gaps(payload):
    for identity, states in REQUIRED_GAP_STATES.items():
        assert_coverage_gap(payload, identity, states=states)


def _canonical(reply):
    assert reply.canonical is not None
    return reply.canonical


def _identity(reply):
    assert reply.canonical is not None and reply.result_id is not None
    return reply.canonical.to_payload()["request_id"], reply.result_id


def _read_only_read(project, owner, request, **kwargs):
    before = project.tree()
    reply = owner.read_compact(request, view_options=VIEW, **kwargs)
    assert_read_only(before, project.tree())
    assert not (project.root / "source-execution-tripwire").exists()
    return reply


def _trace(project, scenario, request, first, previous, *, resumed=None, current=None, **observations):
    record_workflow_trace(project, scenario, {"request": request, "previous": previous,
        "previous_canonical": _canonical(first).rendered,
        "current": current, "current_canonical": _canonical(resumed).rendered if resumed else None,
        "session_metadata": resumed.metadata() if resumed else None,
        "behavior": "not-evaluated-by-resume-read", **observations})


@pytest.mark.parametrize("variant", VARIANTS)
@pytest.mark.parametrize("change", ["body", "default"])
def test_source_resume_reconciles_canonical_identity_and_gaps_across_owners(tmp_path, monkeypatch, variant, change):
    project = _project(tmp_path, monkeypatch, variant)
    request = _request(project)
    retained_request = deepcopy(request)
    with api.open_context_session(**project.context_options) as owner:
        first = _read_only_read(project, owner, request)
        old, _ = _payload(project, request, first)
        identity = _identity(first)
        captured = owner.canonical_receipt(*identity)
        assert captured.validation_scope == "historical-captured"
        warm = _read_only_read(project, owner, request, if_result_id=first.result_id,
                               if_view_id=first.view_id)
        if variant == "native-absent":
            assert warm.state == "full" and not warm.metadata()["reuse"]["rendering"]
        else:
            assert warm.state == "unchanged" and warm.view is None
            assert warm.canonical == first.canonical
        source = project.source / "policy.py"
        before = source.read_bytes()
        mutate_source(project, change)
        assert_source_change(before, source.read_bytes(), change)
        historical = owner.canonical_receipt(*identity)
        assert historical.validation_scope == "historical-captured"
        assert historical.canonical.rendered == captured.canonical.rendered

        resumed = _read_only_read(project, owner, request, if_result_id=first.result_id,
                                  if_view_id=first.view_id, delta=True)
        current, _ = _payload(project, request, resumed)
        assert current["task_id"] == old["task_id"]
        assert current["request_id"] == old["request_id"]
        assert current["task_ref"] == old["task_ref"] == "owned-window-change"
        assert current["result_id"] != old["result_id"]
        assert current["basis"] != old["basis"]
        assert resumed.metadata()["reuse"]["rendering"] is False
        if variant == "native-absent":
            for requirement in ("concept", "prose"):
                assert_coverage_gap(current, requirement, states={"unavailable"})
            assert current["storage"]["status"] == "unavailable"
        if variant in {"sharded", "packed"}:
            for requirement in ("concept", "prose"):
                assert_coverage_gap(current, requirement, states={"stale"})
        after_reads = project.tree()
        reconciled = api.reconcile_task_context(captured.canonical.rendered, request, **project.context_options)
        assert_read_only(after_reads, project.tree())
        assert reconciled["previous_result_id"] == old["result_id"]
        assert reconciled["basis_matches"] is False
        assert reconciled["semantic_adequacy"] == "not-evaluated"
        assert reconciled["context"].rendered == _canonical(resumed).rendered

        with api.open_context_session(**project.context_options) as later:
            new_owner = _read_only_read(project, later, request, if_result_id=first.result_id,
                                        if_view_id=first.view_id, delta=True)
            final, _ = _payload(project, request, new_owner)
            assert final == current
            assert new_owner.delta is None
            assert new_owner.metadata()["reuse"]["capture"] is False
            with pytest.raises(api.InvalidRequestError, match="not retained"):
                later.canonical_receipt(*identity)
        _trace(project, "resume-source-" + change, request, first, old, resumed=resumed, current=current,
               cold_canonical=_canonical(new_owner).rendered, historical_scope=historical.validation_scope,
               reconciliation_previous=reconciled["previous_result_id"],
               reconciliation_current=reconciled["current_result_id"], gaps_retained=True)
    assert request == retained_request


@pytest.mark.parametrize("variant", ["source-only", "sharded", "packed"])
def test_explicit_profile_reload_keeps_intent_but_never_borrows_old_owner_custody(tmp_path, monkeypatch, variant):
    project = _project(tmp_path, monkeypatch, variant)
    request = _request(project)
    path = project.root / "workflow-profile.json"
    path.write_text(json.dumps({"schema_version": "llm-wiki-workflow-profile/v1",
                                "settings": {"prefer_fresh": True}}), encoding="utf-8")
    options = project.context_options
    old_profile = api.load_workflow_profile(path, policy=options["policy"])
    with api.open_context_session(**options, profile=old_profile) as old_owner:
        first = _read_only_read(project, old_owner, request)
        previous, _ = _payload(project, request, first, profile=old_profile)
        identity = _identity(first)
        path.write_text(json.dumps({"schema_version": "llm-wiki-workflow-profile/v1",
                                    "settings": {"prefer_fresh": False}}), encoding="utf-8")
        # Sessions own detached loaded settings, not an ambient file watcher.
        original = old_owner.canonical_receipt(*identity, current=True)
        assert original.validation_scope == "current-revalidated"
        assert original.canonical.rendered == _canonical(first).rendered
        new_profile = api.load_workflow_profile(path, policy=options["policy"])
        assert new_profile.profile_id != old_profile.profile_id
        with api.open_context_session(**options, profile=new_profile) as new_owner:
            resumed = _read_only_read(project, new_owner, request, if_result_id=first.result_id,
                                      if_view_id=first.view_id, delta=True)
            current, _ = _payload(project, request, resumed, profile=new_profile)
            assert current["task_id"] == previous["task_id"]
            assert current["profile_id"] != previous["profile_id"]
            assert current["request_id"] != previous["request_id"]
            assert resumed.delta is None and not resumed.metadata()["reuse"]["rendering"]
            with pytest.raises(api.InvalidRequestError, match="not retained"):
                new_owner.canonical_receipt(*identity)
        # Saved evidence remains valid under its original exact settings only.
        saved = api.render_compact_task_context(_canonical(first).rendered, request, view_options=VIEW,
                                               profile=old_profile, policy=options["policy"])
        assert saved.canonical_text == _canonical(first).rendered
        with pytest.raises(api.InvalidRequestError):
            api.validate_task_context(_canonical(first).rendered, request, profile=new_profile,
                                      policy=options["policy"])
        _trace(project, "resume-profile-reload", request, first, previous, resumed=resumed, current=current,
               old_profile_id=old_profile.profile_id, new_profile_id=new_profile.profile_id,
               original_settings_validation_scope=original.validation_scope,
               new_owner_did_not_borrow_receipt=True)


@pytest.mark.parametrize("variant", ["source-only", "legacy", "adopted-flat"])
def test_unconsumed_wiki_edit_preserves_source_only_identity_without_borrowed_receipt(tmp_path, monkeypatch, variant):
    project = _project(tmp_path, monkeypatch, variant)
    request = task_request(native=False)
    if not project.wiki.exists():
        (project.wiki / "guides").mkdir(parents=True)
        (project.wiki / "guides/unconsumed.md").write_text("# Original unconsumed prose\n", encoding="utf-8")
    with api.open_context_session(**project.context_options) as original_owner:
        first = _read_only_read(project, original_owner, request)
        old, _ = _payload(project, request, first)
        identity = _identity(first)
        if variant == "source-only":
            (project.wiki / "guides/unconsumed.md").write_text("# Changed unconsumed prose\n", encoding="utf-8")
        else:
            write_description(project, "Changed unconsumed prose; source-only context has no native authority.")
        assert original_owner.canonical_receipt(*identity).validation_scope == "historical-captured"
        with api.open_context_session(**project.context_options) as later:
            resumed = _read_only_read(project, later, request, if_result_id=first.result_id,
                                      if_view_id=first.view_id, delta=True)
            current, _ = _payload(project, request, resumed)
            assert current["result_id"] == old["result_id"]
            assert current["storage"]["status"] == "off"
            assert resumed.delta is None and not resumed.metadata()["reuse"]["capture"]
        _trace(project, "resume-unconsumed-wiki", request, first, old, resumed=resumed, current=current,
               unchanged_identity_has_no_wiki_authority=True)


@pytest.mark.parametrize("variant", ["sharded", "packed"])
def test_native_unsynced_prose_refuses_current_receipt_and_recovers_only_after_owning_sync(tmp_path, monkeypatch, variant):
    project = _project(tmp_path, monkeypatch, variant)
    request = _request(project)
    with api.open_context_session(**project.context_options) as owner:
        first = _read_only_read(project, owner, request)
        old, _ = _payload(project, request, first)
        identity = _identity(first)
        write_description(project, BODY_PROSE)
        edited = project.tree()
        assert owner.canonical_receipt(*identity).validation_scope == "historical-captured"
        with pytest.raises(api.LlmWikiApiError):
            owner.canonical_receipt(*identity, current=True)
        assert_read_only(edited, project.tree())
        with pytest.raises(api.LlmWikiApiError):
            owner.read_compact(request, view_options=VIEW, if_result_id=first.result_id,
                               if_view_id=first.view_id)
        assert_read_only(edited, project.tree())
        sync_workflow(project)
        with api.open_context_session(**project.context_options) as later:
            resumed = _read_only_read(project, later, request, if_result_id=first.result_id,
                                      if_view_id=first.view_id)
            current, _ = _payload(project, request, resumed)
            assert current["task_id"] == old["task_id"] and current["request_id"] == old["request_id"]
            assert current["result_id"] != old["result_id"]
            prose = next(fact for fact in current["facts"] if fact["facet"] == "semantic-section")
            assert BODY_PROSE in json.dumps(prose, ensure_ascii=False)
            assert current["storage"]["whole_store_validated"] is False
        _trace(project, "resume-native-prose", request, first, old, resumed=resumed, current=current,
               unsynced_current_validation_refused=True, explicit_owning_sync=True,
               historical_scope="historical-captured")


@pytest.mark.parametrize("variant", ["source-only", "sharded", "packed"])
def test_source_selection_configuration_resume_is_consumed_not_ambient(tmp_path, monkeypatch, variant):
    project = _project(tmp_path, monkeypatch, variant)
    request = _request(project)
    profile = project.source / ".llm-wiki/source-selection.json"
    with api.open_context_session(**project.context_options) as owner:
        first = _read_only_read(project, owner, request)
        old, _ = _payload(project, request, first)
        identity = _identity(first)
        if profile.exists():
            # Same semantic boundary, different exact captured configuration bytes.
            value = json.loads(profile.read_text(encoding="utf-8"))
        else:
            profile.parent.mkdir()
            value = {"schema_version": "llm-wiki-source-selection/v1",
                     "include": ["policy.py", "client.py", "scope.py", "stable.py"], "exclude": []}
        profile.write_text(json.dumps(value, sort_keys=True, indent=4) + "\n", encoding="utf-8")
        historical = owner.canonical_receipt(*identity)
        assert historical.validation_scope == "historical-captured"
        assert historical.canonical.rendered == _canonical(first).rendered
        if variant in {"sharded", "packed"}:
            edited = project.tree()
            with pytest.raises(api.LlmWikiApiError):
                owner.read_compact(request, view_options=VIEW, if_result_id=first.result_id,
                                   if_view_id=first.view_id)
            assert_read_only(edited, project.tree())
            sync_workflow(project)
        with api.open_context_session(**project.context_options) as later:
            resumed = _read_only_read(project, later, request, if_result_id=first.result_id,
                                      if_view_id=first.view_id)
            current, _ = _payload(project, request, resumed)
            assert current["task_id"] == old["task_id"] and current["request_id"] == old["request_id"]
            assert current["result_id"] != old["result_id"]
            assert current["source_capture"]["selection_inputs"] != old["source_capture"]["selection_inputs"]
            if variant in {"sharded", "packed"}:
                assert current["source_capture"]["source_selection"] == old["source_capture"]["source_selection"]
        _trace(project, "resume-source-selection", request, first, old, resumed=resumed, current=current,
               historical_scope=historical.validation_scope,
               explicit_owning_sync=variant in {"sharded", "packed"}, exact_config_inputs_changed=True)


def test_declared_helper_unavailable_fault_on_resume_cannot_publish_old_context(tmp_path, monkeypatch):
    project = _project(tmp_path, monkeypatch, "source-only")
    request = _request(project)
    with api.open_context_session(**project.context_options) as owner:
        first = _read_only_read(project, owner, request)
        old, _ = _payload(project, request, first)
        identity = _identity(first)
        mutate_source(project, "default")
        captured = owner.canonical_receipt(*identity)
        assert captured.validation_scope == "historical-captured"
        edited = project.tree()

        def unavailable(*args, **kwargs):
            # Named fault injection at the existing helper-backed inventory
            # boundary, not a claim about installed workstation runtimes.
            raise ContextPacketUnavailableError("owned helper capture is unavailable", field="src_dir")

        monkeypatch.setattr(task_context_v2.context, "get_inventory", unavailable)
        with pytest.raises(api.LlmWikiApiError):
            owner.read_compact(request, view_options=VIEW, if_result_id=first.result_id,
                               if_view_id=first.view_id, delta=True)
        assert_read_only(edited, project.tree())
        assert not (project.root / "source-execution-tripwire").exists()
        with pytest.raises(api.InvalidRequestError, match="not retained"):
            owner.canonical_receipt(*identity)
        _trace(project, "resume-helper-unavailable-fault", request, first, old,
               fault_boundary="existing selected-source inventory helper capture",
               fault_is_synthetic=True, current_read_refused=True, historical_scope=captured.validation_scope,
               current_usable_context_emitted=False)


@pytest.mark.parametrize("variant", ["legacy", "adopted-flat"])
def test_flat_native_resume_preserves_refusal_without_implicit_migration_or_source_only_downgrade(tmp_path, monkeypatch, variant):
    project = _project(tmp_path, monkeypatch, variant)
    request = task_request(native=False)
    with api.open_context_session(**project.context_options) as owner:
        first = _read_only_read(project, owner, request)
        previous, _ = _payload(project, request, first)
        identity = _identity(first)
        captured = owner.canonical_receipt(*identity)
        for mode in ("auto", "required"):
            declared_native = task_request(native=True)
            declared_native["options"]["knowledge_mode"] = mode
            before = project.tree()
            with pytest.raises(api.InvalidRequestError, match="selected native reads require explicit"):
                owner.read_compact(declared_native, view_options=VIEW, if_result_id=first.result_id,
                                   if_view_id=first.view_id, delta=True)
            assert_read_only(before, project.tree())
        mutate_source(project, "default")
        assert captured.validation_scope == "historical-captured"
        assert captured.canonical.rendered == _canonical(first).rendered
        # Failed reads discard disposable custody. The detached historical
        # artifact remains captured; it cannot serve as a current fallback.
        with pytest.raises(api.InvalidRequestError, match="not retained"):
            owner.canonical_receipt(*identity)
        resumed = _read_only_read(project, owner, request, if_result_id=first.result_id,
                                  if_view_id=first.view_id, delta=True)
        current, _ = _payload(project, request, resumed)
        assert current["task_id"] == previous["task_id"] and current["request_id"] == previous["request_id"]
        assert current["result_id"] != previous["result_id"]
        assert current["storage"]["status"] == "off"
        for mode in ("auto", "required"):
            declared_native = task_request(native=True)
            declared_native["options"]["knowledge_mode"] = mode
            before = project.tree()
            with pytest.raises(api.InvalidRequestError, match="selected native reads require explicit"):
                owner.read_compact(declared_native, view_options=VIEW, if_result_id=resumed.result_id,
                                   if_view_id=resumed.view_id)
            assert_read_only(before, project.tree())
        _trace(project, "resume-flat-native-refusal", request, first, previous, resumed=resumed, current=current,
               explicit_native_auto_refused=True, explicit_native_required_refused=True,
               source_only_is_separate_request=True, migration_performed=False)


def test_bounded_resume_keeps_omitted_requirements_without_claiming_missing_evidence(tmp_path, monkeypatch):
    project = _project(tmp_path, monkeypatch, "source-only")
    request = task_request(native=False)
    request["options"]["max_read_rounds"] = 1
    with api.open_context_session(**project.context_options) as owner:
        first = _read_only_read(project, owner, request)
        old = api.validate_task_context(_canonical(first).rendered, request,
                                        policy=project.context_options["policy"])
        for requirement in ("missing", "behavior"):
            assert_coverage_gap(old, requirement, states={"omitted"})
        mutate_source(project, "default")
        resumed = _read_only_read(project, owner, request, if_result_id=first.result_id,
                                  if_view_id=first.view_id)
        current = api.validate_task_context(_canonical(resumed).rendered, request,
                                            policy=project.context_options["policy"])
        assert resumed.view is not None
        expanded = api.expand_compact_task_context(resumed.view.rendered, _canonical(resumed).rendered,
            request, view_options=VIEW, policy=project.context_options["policy"])
        assert_coverage_preserved(current, expanded)
        for requirement in ("missing", "behavior"):
            assert_coverage_gap(current, requirement, states={"omitted"})
        assert current["task_id"] == old["task_id"] and current["request_id"] == old["request_id"]
        assert current["result_id"] != old["result_id"]
        _trace(project, "resume-bounded-omissions", request, first, old, resumed=resumed, current=current,
               missing_evidence_not_evaluated=True, bounded_omissions_retained=True)


def test_source_edit_cannot_relabel_historical_receipt_current_or_fallback_after_failure(tmp_path, monkeypatch):
    project = _project(tmp_path, monkeypatch, "source-only")
    request = _request(project)
    with api.open_context_session(**project.context_options) as owner:
        first = _read_only_read(project, owner, request)
        old, _ = _payload(project, request, first)
        identity = _identity(first)
        mutate_source(project, "default")
        historical = owner.canonical_receipt(*identity)
        assert historical.validation_scope == "historical-captured"
        edited = project.tree()
        with pytest.raises(api.WorkspaceStateError):
            owner.canonical_receipt(*identity, current=True)
        with pytest.raises(api.InvalidRequestError, match="not retained"):
            owner.canonical_receipt(*identity)
        assert_read_only(edited, project.tree())
        resumed = _read_only_read(project, owner, request, if_result_id=first.result_id,
                                  if_view_id=first.view_id)
        current, _ = _payload(project, request, resumed)
        assert current["result_id"] != old["result_id"]
        assert current["task_id"] == old["task_id"]
        _trace(project, "resume-historical-current-refusal", request, first, old, resumed=resumed, current=current,
               historical_scope=historical.validation_scope, failed_current_validation_cleared_custody=True)
