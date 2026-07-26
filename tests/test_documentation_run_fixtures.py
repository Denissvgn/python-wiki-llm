"""Frozen v1 fixtures for the standalone documentation-run contract."""

from __future__ import annotations

import json
import re
from pathlib import Path, PurePosixPath
from typing import Any

import pytest

from llm_wiki_cli.services.documentation_run import (
    DEFAULT_DOCUMENTATION_SKILLS,
    DocumentationRun,
    DocumentationSchemaError,
    DocumentationTransitionError,
    transition_documentation_run,
)


FIXTURE_DIR = Path(__file__).parent / "fixtures" / "documentation_runs"
SCENARIOS = {
    "complete": "publish_ready",
    "partial": "user_docs",
    "blocked": "blocked",
    "resumed": "review",
}
ACTIVE_STAGE_BY_STATE = {
    "wiki_enrichment": "wiki-enrichment",
    "user_docs": "user-docs",
    "review": "review",
}
HASH_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
VERSION_RE = re.compile(r"^[0-9]+\.[0-9]+\.[0-9]+(?:[+.-][0-9A-Za-z.-]+)?$")
WINDOWS_ABSOLUTE_RE = re.compile(r"^[A-Za-z]:[/\\]")
ROUTER_OWNED_KEYS = {
    "provider",
    "provider_family",
    "provider_id",
    "model",
    "model_id",
    "route_id",
    "endpoint",
    "credentials",
}


def _load_fixture(name: str) -> dict[str, Any]:
    return json.loads((FIXTURE_DIR / f"{name}.json").read_text(encoding="utf-8"))


def _assert_portable_path(value: str) -> None:
    assert value
    assert "\\" not in value
    assert not WINDOWS_ABSOLUTE_RE.match(value)
    path = PurePosixPath(value)
    assert not path.is_absolute()
    assert "." not in path.parts
    assert ".." not in path.parts
    assert path.as_posix() == value


def _all_mapping_keys(value: Any) -> set[str]:
    if isinstance(value, dict):
        return set(value).union(
            *(_all_mapping_keys(child) for child in value.values()), set()
        )
    if isinstance(value, list):
        return set().union(*(_all_mapping_keys(child) for child in value), set())
    return set()


@pytest.mark.parametrize("scenario", SCENARIOS)
def test_documentation_run_fixture_round_trips(scenario: str) -> None:
    payload = _load_fixture(scenario)

    run = DocumentationRun.from_dict(payload)

    assert run.to_dict() == payload
    assert run.state == SCENARIOS[scenario]
    assert run.integration_mode == "external_agent_docs"
    assert run.baseline_strategy == run.baseline["strategy"]


@pytest.mark.parametrize("scenario", SCENARIOS)
def test_documentation_run_fixture_freezes_baseline_input_union(
    scenario: str,
) -> None:
    run = DocumentationRun.from_dict(_load_fixture(scenario))
    baseline = run.baseline
    source = run.source

    assert baseline["source_revision"] == source["revision"]
    assert baseline["freshness"] in {"verified_current", "unverified"}
    if run.baseline_strategy == "bootstrap_source":
        assert source["available"] is True
        assert source["revision"] != "source_unavailable"
        assert HASH_RE.fullmatch(source["content_fingerprint"])
        assert source["revision_kind"] in {"git", "content"}
        assert baseline["freshness_policy"] == "require-current"
        assert baseline["freshness"] == "verified_current"
        assert baseline["input_wiki"] is None
        assert run.evidence["source_baseline"].endswith("source-baseline.json")
        assert run.evidence["bootstrap"].endswith("bootstrap.json")
        return

    assert run.baseline_strategy == "adopt_existing_wiki"
    imported = baseline["input_wiki"]
    assert isinstance(imported, dict)
    assert HASH_RE.fullmatch(imported["input_tree_hash"])
    assert HASH_RE.fullmatch(imported["initial_snapshot_hash"])
    assert imported["compatibility"] in {"current", "legacy_index_only"}
    assert imported["refresh_decision"] in {
        "not_required",
        "allow_unverified",
        "workspace_only_required",
        "workspace_only_completed",
    }
    assert run.evidence["wiki_input"].endswith("wiki-input.json")
    if source["available"]:
        assert source["revision"] != "source_unavailable"
        assert HASH_RE.fullmatch(source["content_fingerprint"])
    else:
        assert source["display_identifier"] == "source_unavailable"
        assert source["revision"] == "source_unavailable"
        assert "source_unavailable" in run.verdict_limitations
        assert "source_verified_publish_ready_unavailable" in run.verdict_limitations
    if imported["refresh_decision"] == "workspace_only_completed":
        assert baseline["freshness_policy"] == "refresh-snapshot"
        assert baseline["freshness"] == "verified_current"
        assert run.evidence["workspace_refresh"].endswith("workspace-refresh.json")


@pytest.mark.parametrize("scenario", SCENARIOS)
def test_documentation_run_fixture_records_trusted_intake_and_skills(
    scenario: str,
) -> None:
    payload = _load_fixture(scenario)
    run = DocumentationRun.from_dict(payload)
    intake = run.intake.to_dict()

    assert intake["trust_rank"] == "human_intent"
    assert intake["project_purpose"] != "unspecified"
    assert set(intake["audiences"]) == set(intake["audience_intent"])
    assert intake["provenance"]["source"] == "supervisor_supplied"
    assert intake["live_service"]["secret_material_persisted"] is False
    assert run.policy["live_service"]["secret_material_persisted"] is False

    assert tuple(skill["id"] for skill in run.skills) == DEFAULT_DOCUMENTATION_SKILLS
    for skill in run.skills:
        assert VERSION_RE.fullmatch(skill["package_version"])
        assert HASH_RE.fullmatch(skill["hash"])
        _assert_portable_path(skill["path"])


@pytest.mark.parametrize("scenario", SCENARIOS)
def test_documentation_run_fixture_uses_only_portable_contract_paths(
    scenario: str,
) -> None:
    run = DocumentationRun.from_dict(_load_fixture(scenario))

    for value in run.paths.values():
        _assert_portable_path(value)
    for value in run.evidence.values():
        _assert_portable_path(value)
    for item in run.validation_results:
        evidence = item.get("evidence")
        if evidence:
            _assert_portable_path(str(evidence))
    for finding in run.unresolved_findings:
        for evidence in finding.get("evidence", []):
            _assert_portable_path(str(evidence))


@pytest.mark.parametrize("scenario", SCENARIOS)
def test_documentation_run_fixture_is_provider_and_model_neutral(
    scenario: str,
) -> None:
    payload = _load_fixture(scenario)

    assert _all_mapping_keys(payload).isdisjoint(ROUTER_OWNED_KEYS)


def test_documentation_run_fixtures_pin_complete_partial_blocked_and_resumed() -> None:
    complete = DocumentationRun.from_dict(_load_fixture("complete"))
    partial = DocumentationRun.from_dict(_load_fixture("partial"))
    blocked = DocumentationRun.from_dict(_load_fixture("blocked"))
    resumed = DocumentationRun.from_dict(_load_fixture("resumed"))

    assert complete.state == "publish_ready"
    assert complete.current_stage is None
    assert complete.resume_state is None
    assert not complete.unresolved_findings

    assert partial.state == "user_docs"
    assert partial.current_stage == ACTIVE_STAGE_BY_STATE[partial.state]
    assert partial.resume_state is None
    assert partial.work["completed"]

    assert blocked.state == "blocked"
    assert blocked.current_stage is None
    assert blocked.resume_state == "review"
    assert blocked.unresolved_findings

    assert resumed.state == "review"
    assert resumed.current_stage == ACTIVE_STAGE_BY_STATE[resumed.state]
    assert resumed.resume_state is None
    assert resumed.stage_attempts["review"] > blocked.stage_attempts["review"]
    assert resumed.evidence["resume"].endswith("resume.json")
    assert any(
        item.get("check") == "resumed_from_blocked"
        for item in resumed.validation_results
    )


def test_documentation_run_v1_preserves_unknown_additive_top_level_fields() -> None:
    payload = _load_fixture("partial")
    additive = {
        "future_optional_metadata": {
            "schema": "example-addition/v1",
            "non_authoritative": True,
        }
    }
    payload.update(additive)

    run = DocumentationRun.from_dict(payload)

    assert run.extensions == additive
    assert run.to_dict() == payload


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("state", "complete", "Unsupported run state"),
        (
            "baseline_strategy",
            "future_baseline",
            "Unsupported baseline strategy",
        ),
        (
            "integration_mode",
            "managed_kb",
            "Unsupported documentation integration_mode",
        ),
    ],
)
def test_documentation_run_v1_rejects_unknown_required_enums(
    field: str,
    value: str,
    message: str,
) -> None:
    payload = _load_fixture("complete")
    payload[field] = value

    with pytest.raises(DocumentationSchemaError, match=message):
        DocumentationRun.from_dict(payload)


def test_documentation_run_v1_rejects_missing_required_field() -> None:
    payload = _load_fixture("complete")
    del payload["source"]

    with pytest.raises(
        DocumentationSchemaError,
        match="Documentation run is missing required field: source",
    ):
        DocumentationRun.from_dict(payload)


@pytest.mark.parametrize("value", ["/wiki", "C:\\wiki", "../wiki", "wiki/../site"])
def test_documentation_run_v1_rejects_nonportable_paths(value: str) -> None:
    payload = _load_fixture("complete")
    payload["paths"]["wiki"] = value

    with pytest.raises(DocumentationSchemaError, match="workspace-relative"):
        DocumentationRun.from_dict(payload)


def test_documentation_run_v1_enforces_terminal_and_exact_resume_transitions() -> None:
    complete = DocumentationRun.from_dict(_load_fixture("complete"))
    with pytest.raises(DocumentationTransitionError, match="Invalid.*transition"):
        transition_documentation_run(complete, "review")

    blocked = DocumentationRun.from_dict(_load_fixture("blocked"))
    with pytest.raises(DocumentationTransitionError, match="must resume"):
        transition_documentation_run(blocked, "user_docs")

    transition_documentation_run(blocked, "review")
    assert blocked.state == "review"
    assert blocked.current_stage == "review"
    assert blocked.resume_state is None
