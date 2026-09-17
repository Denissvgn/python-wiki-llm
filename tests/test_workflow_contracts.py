"""Explicit profile authority and task canonicalization boundaries."""

import json

import pytest

from llm_wiki_cli.services.task_contract import TASK_REQUEST_SCHEMA, normalize_task_request
from llm_wiki_cli.services.workflow_profile import (
    PROFILE_SCHEMA, WorkflowPolicy, WorkflowRequestError, load_profile, normalize_profile,
)


def test_profiles_are_explicit_detached_and_host_limits_are_authoritative(tmp_path):
    original = normalize_profile()
    changed = original.to_payload()
    changed["settings"]["budget_tokens"] = 1
    assert original.settings["budget_tokens"] == 32000
    assert normalize_profile(original).profile_id == original.profile_id
    path = tmp_path / "profile.json"
    path.write_text(json.dumps(original.to_payload()))
    assert load_profile(path).profile_id == original.profile_id
    narrow = normalize_profile(policy=WorkflowPolicy(budget_tokens=1000, read_scope="snapshot"))
    assert narrow.settings["budget_tokens"] == 1000
    assert narrow.settings["read_scope"] == "snapshot"
    with pytest.raises(WorkflowRequestError, match="host policy"):
        normalize_profile(overrides={"read_scope": "full-inventory"})


@pytest.mark.parametrize("settings", [{"root": "/"}, {"execute": True}, {"max_files": True},
    {"budget_tokens": 0}, {"max_retries": 3}, {"prefer_fresh": "yes"},
    {"counter_id": "/" * 1000}, {"knowledge_mode": "fresh"}])
def test_invalid_profile_cannot_expand_authority(settings):
    with pytest.raises(WorkflowRequestError):
        normalize_profile({"schema_version": PROFILE_SCHEMA, "settings": settings})


def test_native_required_is_independent_of_freshness_and_live_scope():
    result = normalize_profile(overrides={"knowledge_mode": "required", "read_scope": "snapshot",
                                          "prefer_fresh": False})
    assert result.settings["knowledge_mode"] == "required"
    assert result.settings["read_scope"] == "snapshot"
    assert result.settings["prefer_fresh"] is False


def test_task_identity_deduplicates_coordinates_and_separates_host_label():
    anchor = {"kind": "symbol", "value": "source.py:Owner.limit"}
    request = {"schema_version": TASK_REQUEST_SCHEMA, "text": "run a command", "task_ref": "host-1",
               "anchors": [anchor, anchor], "requirements": [
                   {"id": "contract", "facet": "source-contract", "selector": anchor["value"]}]}
    first, profile = normalize_task_request(request)
    second, _ = normalize_task_request({**request, "task_ref": "host-2", "anchors": [anchor]})
    assert first["request_id"] == second["request_id"]
    assert first["task_id"] == second["task_id"]
    assert len(first["anchors"]) == 1
    assert profile.settings["read_scope"] == "selected"
    third, _ = normalize_task_request({**request, "text": "different intent"})
    assert third["request_id"] != first["request_id"]


@pytest.mark.parametrize("patch", [{"schema_version": "future"}, {"unknown": True},
    {"text": "x" * 16385}, {"anchors": [{"kind": "source", "value": "../outside"}]},
    {"anchors": [{"kind": "source", "value": "a\\b.py"}]},
    {"requirements": [{"id": "x", "facet": "source-contract", "selector": "x", "criterion": True}]},
    {"requirements": [{"id": "x", "facet": "command", "selector": "rm -rf /"}]},
    {"options": {"read_scope": "full-inventory"}},
    {"anchors": [{"kind": "source", "value": "a.py"}] * 101}])
def test_invalid_task_fields_fail_without_a_workspace(patch):
    with pytest.raises(ValueError):
        normalize_task_request({"schema_version": TASK_REQUEST_SCHEMA, **patch})


def test_duplicate_requirement_ids_and_empty_task_are_distinct():
    requirement = {"id": "x", "facet": "behavior", "selector": "x"}
    with pytest.raises(WorkflowRequestError, match="duplicate"):
        normalize_task_request({"schema_version": TASK_REQUEST_SCHEMA, "requirements": [requirement, requirement]})
    empty, _ = normalize_task_request({"schema_version": TASK_REQUEST_SCHEMA})
    assert empty["anchors"] == empty["requirements"] == []
