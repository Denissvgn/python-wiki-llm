"""Executable compatibility and failure contracts for context knowledge."""

from __future__ import annotations

import inspect
import json
import shlex
from copy import deepcopy
from pathlib import Path
from string import Formatter

import pytest

from llm_wiki_cli import api, cli
from llm_wiki_cli.services import context_service, schema
from llm_wiki_cli.services.context_knowledge_contract import (
    CONTEXT_KNOWLEDGE_CONTRACT_SCHEMA_VERSION,
    KNOWLEDGE_MODE_CLI_OPTION,
    KNOWLEDGE_MODE_REQUEST_FIELD,
    KNOWLEDGE_MODE_VALUES,
    RESERVED_CONTEXT_KNOWLEDGE_PROTOCOL_VERSION,
    RESERVED_QUALIFIED_CONTEXT_PACKET_KNOWLEDGE_SCHEMA_VERSION,
    ContextKnowledgeContractError,
    context_knowledge_contract,
    validate_context_knowledge_contract,
)
from llm_wiki_cli.services.contracts import (
    CONTEXT_PROTOCOL_VERSION,
    PROTOCOL_VERSIONS,
    QUALIFIED_CONTEXT_PACKET_SCHEMA_VERSION,
)
from llm_wiki_cli.services.mcp_server import McpWikiService


FIXTURE_DIR = Path(__file__).parent / "fixtures"
CONTRACT_FIXTURE = FIXTURE_DIR / "context-knowledge-contract-v1.json"
LEGACY_CONTEXT_FIXTURE = FIXTURE_DIR / "context-prefer-fresh-off-v1.json"
LEGACY_PACKET_FIXTURE = FIXTURE_DIR / "context-packet-v1.json"


def _by_state(rows: list[dict]) -> dict[str, dict]:
    return {row["state"]: row for row in rows}


def _by_pair(rows: list[dict]) -> dict[tuple[str, str], dict]:
    return {(row["lifecycle_state"], row["evidence_state"]): row for row in rows}


def _raw_request(**extra: object) -> dict[str, object]:
    request: dict[str, object] = {
        "protocol": CONTEXT_PROTOCOL_VERSION,
        "budget_tokens": 32000,
        "focus": ["all"],
        "format": "json",
    }
    request.update(extra)
    return request


def _replace(contract: dict, path: tuple[str | int, ...], value: object) -> None:
    target: object = contract
    for component in path[:-1]:
        target = target[component]  # type: ignore[index]
    target[path[-1]] = value  # type: ignore[index]


def test_frozen_contract_matches_its_canonical_fixture() -> None:
    fixture = json.loads(CONTRACT_FIXTURE.read_text(encoding="utf-8"))
    validate_context_knowledge_contract(fixture)

    assert context_knowledge_contract() == fixture
    assert CONTRACT_FIXTURE.read_bytes().endswith(b"\n")
    assert b"\r" not in CONTRACT_FIXTURE.read_bytes()


def test_planned_surfaces_are_reserved_while_current_runtime_stays_v1() -> None:
    contract = context_knowledge_contract()

    assert contract["schema_version"] == CONTEXT_KNOWLEDGE_CONTRACT_SCHEMA_VERSION
    assert contract["runtime_state"] == {
        "knowledge_mode": "reserved-not-active",
        "render_profiles": "reserved-not-active",
        "lifecycle_behavior": "reserved-not-active",
        "active_context_protocol": CONTEXT_PROTOCOL_VERSION,
        "active_packet_schema": QUALIFIED_CONTEXT_PACKET_SCHEMA_VERSION,
    }
    assert contract["versioning"]["explicit"]["context_protocol"] == (
        RESERVED_CONTEXT_KNOWLEDGE_PROTOCOL_VERSION
    )
    assert contract["versioning"]["explicit"]["packet_schema"] == (
        RESERVED_QUALIFIED_CONTEXT_PACKET_KNOWLEDGE_SCHEMA_VERSION
    )
    assert RESERVED_CONTEXT_KNOWLEDGE_PROTOCOL_VERSION not in PROTOCOL_VERSIONS
    assert (
        RESERVED_QUALIFIED_CONTEXT_PACKET_KNOWLEDGE_SCHEMA_VERSION
        not in PROTOCOL_VERSIONS
    )
    assert CONTEXT_KNOWLEDGE_CONTRACT_SCHEMA_VERSION not in PROTOCOL_VERSIONS

    with pytest.raises(SystemExit):
        cli._build_parser().parse_args(
            ["context", "--budget", "32000", KNOWLEDGE_MODE_CLI_OPTION, "auto"]
        )
    assert (
        KNOWLEDGE_MODE_REQUEST_FIELD
        not in inspect.signature(api.build_context).parameters
    )
    assert (
        KNOWLEDGE_MODE_REQUEST_FIELD
        not in inspect.signature(api.build_qualified_context).parameters
    )
    assert (
        KNOWLEDGE_MODE_REQUEST_FIELD
        not in inspect.signature(McpWikiService.get_context).parameters
    )
    assert (
        KNOWLEDGE_MODE_REQUEST_FIELD
        not in inspect.signature(McpWikiService.get_context_packet).parameters
    )
    assert "profile" not in inspect.signature(schema.build_schema_content).parameters
    assert (
        "render_profile"
        not in inspect.signature(schema.build_schema_content).parameters
    )


def test_reserved_names_and_request_normalization_are_identical() -> None:
    contract = context_knowledge_contract()
    interfaces = contract["interfaces"]

    assert interfaces["cli"]["name"] == KNOWLEDGE_MODE_CLI_OPTION
    assert interfaces["python-api"]["name"] == KNOWLEDGE_MODE_REQUEST_FIELD
    assert interfaces["mcp"]["name"] == KNOWLEDGE_MODE_REQUEST_FIELD
    assert interfaces["raw-protocol"]["path"] == KNOWLEDGE_MODE_REQUEST_FIELD
    assert interfaces["packet"]["path"] == "request.knowledge_mode"
    assert all(surface["default"] is None for surface in interfaces.values())
    assert contract["request"]["accepted_values"] == list(KNOWLEDGE_MODE_VALUES)
    assert contract["request"]["aliases"] == []
    assert contract["request"]["normalization"] == {
        "omitted": "do-not-add-field",
        "explicit": "exact-lowercase-value",
        "cli-option-with-request-file": "invalid-request",
        "api-parameter-with-request-field": "invalid-request",
        "duplicate": "invalid-request",
    }


def test_omission_preserves_v1_normalization_and_canonical_fixtures() -> None:
    normalized = context_service._validate_protocol_request(_raw_request())

    assert normalized == {
        "protocol": CONTEXT_PROTOCOL_VERSION,
        "budget_tokens": 32000,
        "focus": ["all"],
        "format": "json",
        "filters": {},
        "prefer_fresh": False,
    }
    assert KNOWLEDGE_MODE_REQUEST_FIELD not in normalized
    assert b'"knowledge_mode"' not in LEGACY_CONTEXT_FIXTURE.read_bytes()
    assert b'"knowledge_mode"' not in LEGACY_PACKET_FIXTURE.read_bytes()
    legacy_packet = json.loads(LEGACY_PACKET_FIXTURE.read_text(encoding="utf-8"))
    assert legacy_packet["basis"]["knowledge"] == {
        "availability": "absent",
        "reason": "knowledge-projection-not-present",
        "state": "unavailable",
    }
    assert "knowledge" not in legacy_packet["response"]

    with pytest.raises(context_service.ProtocolRequestError) as caught:
        context_service._validate_protocol_request(_raw_request(knowledge_mode="auto"))
    assert caught.value.field == KNOWLEDGE_MODE_REQUEST_FIELD


def test_existing_freshness_preference_defaults_remain_false() -> None:
    args = cli._build_parser().parse_args(["context", "--budget", "32000"])

    assert args.prefer_fresh is False
    assert (
        inspect.signature(api.build_context).parameters["prefer_fresh"].default is False
    )
    assert (
        inspect.signature(McpWikiService.get_context).parameters["prefer_fresh"].default
        is False
    )
    assert (
        inspect.signature(McpWikiService.get_context_packet)
        .parameters["prefer_fresh"]
        .default
        is False
    )


def test_every_interface_has_exact_success_and_required_failure_mapping() -> None:
    mappings = context_knowledge_contract()["interface_mappings"]

    assert mappings["direct-cli"]["context_json"] == {
        "knowledge_path": "knowledge",
        "ranking_policy_path": "ranking_policy",
    }
    assert mappings["raw-protocol"]["context"] == mappings["direct-cli"]["context_json"]
    assert (
        mappings["python-api-context"]["json"] == mappings["direct-cli"]["context_json"]
    )
    assert mappings["python-api-context"]["markdown"] == {
        "knowledge_path": "payload.knowledge",
        "ranking_policy_path": "payload.ranking_policy",
        "content": "renders-equivalent-disclosures",
    }
    assert (
        mappings["mcp-get-context"]["context"] == mappings["direct-cli"]["context_json"]
    )
    assert mappings["python-api-packet"]["packet"] == {
        "knowledge_path": "response.knowledge",
        "ranking_policy_path": "response.ranking_policy",
    }
    assert mappings["mcp-get-context-packet"]["packet"] == {
        "knowledge_path": "packet.response.knowledge",
        "ranking_policy_path": "packet.response.ranking_policy",
    }
    assert mappings["mcp-get-context-packet"]["unchanged"] == {
        "knowledge_path": "absent",
        "ranking_policy_path": "absent",
    }

    assert mappings["direct-cli"]["required_failure"] == {
        "transport": "process-exit",
        "exit_code": 1,
        "render": "human-readable-error-with-stable-code-and-reason",
        "stream": "stderr",
        "stdout": "empty",
        "output_file": "not-written",
        "packet_emitted": False,
    }
    assert mappings["raw-protocol"]["required_failure"]["render"] == (
        "canonical-required-error-json"
    )
    assert mappings["raw-protocol"]["required_failure"]["stream"] == "stdout"
    for name in ("python-api-context", "python-api-packet"):
        assert mappings[name]["required_failure"]["exception"] == (
            "WorkspaceStateError"
        )
        assert mappings[name]["required_failure"]["attributes"]["code"] == (
            "knowledge-required-unavailable"
        )
        assert mappings[name]["required_failure"]["attributes"]["details"] == (
            "canonical-required-error"
        )
        assert mappings[name]["required_failure"]["response_returned"] is False
    for name in ("mcp-get-context", "mcp-get-context-packet"):
        assert mappings[name]["required_failure"]["exception"] == "McpWikiError"
        assert mappings[name]["required_failure"]["code"] == (
            "knowledge-required-unavailable"
        )


def test_mode_packet_basis_and_ranking_contracts_are_independent() -> None:
    contract = context_knowledge_contract()
    modes = contract["modes"]
    preference = contract["prefer_fresh"]

    assert modes["off"]["context_selection_read"] == "not-constructed"
    assert modes["off"]["packet_basis_capture"] == ("captured-once-without-selection")
    for mode in ("auto", "required"):
        assert modes[mode]["context_selection_read"] == "constructed-once"
        assert modes[mode]["packet_basis_capture"] == (
            "captured-once-and-shared-with-selection"
        )
    assert {mode["mutation"] for mode in modes.values()} == {"never"}

    basis = contract["output_fields"]["packet_basis_knowledge"]
    assert basis["mode_independent"] is True
    assert basis["off_behavior"] == "capture-actual-basis-once-without-selection"
    assert basis["not_requested_value"] == "forbidden-in-packet-basis"

    assert preference["default"] is False
    assert preference["controls_knowledge_inclusion"] is False
    assert preference["off_with_true"] == {
        "outcome": "success-disabled",
        "requested": True,
        "applied": False,
        "reason": "knowledge-selection-disabled",
    }
    assert preference["ranking_presence"] == {
        "not_requested": "absent",
        "requested": "present-even-when-applied-false",
    }
    matrix = preference["disclosure_matrix"]
    assert matrix[0]["field"] == "absent"
    assert all(
        row["field"] == "present"
        for row in matrix
        if row["requested"] and row["successful_response"]
    )
    assert {row["reason"] for row in matrix if row.get("applied") is False} == {
        "knowledge-selection-disabled",
        "no-budget-pressure",
        "qualified-freshness-ranks-unavailable",
        "knowledge-unavailable",
    }


def test_output_selection_freshness_and_error_contracts_are_exact() -> None:
    fields = context_knowledge_contract()["output_fields"]
    knowledge = fields["knowledge"]
    freshness = fields["packet_basis_freshness"]
    ranking = fields["ranking_policy"]
    selected = fields["selected_content"]
    error = fields["required_error"]

    assert knowledge["context_path"] == "knowledge"
    assert knowledge["packet_path"] == "response.knowledge"
    assert set(knowledge["required"]) == {
        "mode",
        "status",
        "availability",
        "reason",
        "selected",
        "freshness_evaluated",
        "bounds",
        "fallback",
    }
    assert freshness["per_concept_values"] == (
        "not-duplicated-basis-is-aggregate-provenance"
    )
    assert ranking["presence"] == {
        "prefer_fresh_false": "absent",
        "prefer_fresh_true": "present-even-when-applied-false",
    }
    assert selected["selected_type"] == "boolean"
    assert selected["selection_presence"] == {
        "selected_true": "required",
        "selected_false": "forbidden",
    }
    assert set(selected["concept_freshness_required"]) == {
        "state",
        "reason",
        "live_comparison_performed",
    }
    assert selected["snapshot_only_freshness"] == {
        "state": "not-evaluated",
        "reason": "live-evaluation-not-performed",
        "live_comparison_performed": False,
    }
    assert selected["classification"] == "inert-evidence"
    assert selected["authorizes"] == []
    assert set(selected["non_authorizing_for"]) >= {
        "execution",
        "network-access",
        "source-edits",
        "git-actions",
        "governance-changes",
    }
    assert error["code"] == "knowledge-required-unavailable"
    assert error["field"] == KNOWLEDGE_MODE_REQUEST_FIELD
    assert error["mutation_permitted"] is False
    assert error["packet_emitted"] is False


def test_reference_lifecycle_matrix_is_complete_and_reserved() -> None:
    contract = context_knowledge_contract()
    rows = _by_state(contract["lifecycle_matrix"])

    assert set(rows) == {
        "current-reference",
        "absent-reference",
        "modified-reference",
        "reference-install-failure",
        "skills-disabled",
        "agent-switch",
        "missing-schema",
        "plugin-blocks",
        "interrupted-upgrade",
    }
    assert rows["current-reference"]["rendered_profile"] == "compact"
    for state in set(rows) - {"current-reference"}:
        assert rows[state]["rendered_profile"] != "compact"
    assert rows["missing-schema"]["rendered_profile"] == "not-rendered"
    assert {row["read_only_knowledge"] for row in rows.values()} == {"independent"}
    assert {row["fallback_evidence"][0] for row in rows.values()} == {
        "qualified-knowledge-if-ready"
    }
    for command in contract["lifecycle_commands"].values():
        assert command["implementation_state"] == "reserved-not-active"
    assert contract["render_profiles"]["implementation_state"] == (
        "reserved-not-active"
    )


EXPECTED_EVIDENCE_WIRE = {
    "ready": (
        "ready",
        "knowledge-ready",
        "selected",
        "selected",
        "recorded",
        "ready",
        "all-projection-commitments-match",
    ),
    "absent": (
        "absent",
        "knowledge-projection-not-present",
        "fallback",
        "error-no-context-response",
        "unavailable",
        "absent",
        "knowledge-projection-not-present",
    ),
    "degraded-mixed": (
        "degraded",
        "policy-selected-surface-only-fallback-after-mixed-snapshot",
        "fallback",
        "error-no-context-response",
        "unavailable",
        "degraded",
        "policy-selected-surface-only-fallback-after-mixed-snapshot",
    ),
    "unsupported": (
        "unsupported",
        "knowledge-schema-version-unsupported",
        "fallback",
        "error-no-context-response",
        "unavailable",
        "unsupported",
        "knowledge-schema-version-unsupported",
    ),
    "incompatible": (
        "degraded",
        "knowledge-basis-incompatible",
        "fallback",
        "error-no-context-response",
        "unavailable",
        "degraded",
        "knowledge-basis-incompatible",
    ),
    "snapshot-only": (
        "ready",
        "knowledge-snapshot-only",
        "selected",
        "selected",
        "recorded",
        "ready",
        "all-projection-commitments-match",
    ),
    "source-changed": (
        "ready",
        "knowledge-source-changed",
        "selected",
        "selected",
        "recorded",
        "ready",
        "all-projection-commitments-match",
    ),
    "bounded-truncated": (
        "ready",
        "knowledge-results-truncated",
        "selected",
        "selected",
        "recorded",
        "ready",
        "all-projection-commitments-match",
    ),
    "invalid-surface": (
        "degraded",
        "surface-validation-failed",
        "fallback",
        "error-no-context-response",
        "unavailable",
        "degraded",
        "policy-selected-surface-only-fallback-after-invalid",
    ),
}


@pytest.mark.parametrize(("state", "expected"), EXPECTED_EVIDENCE_WIRE.items())
def test_every_evidence_state_has_exact_wire_mapping(
    state: str, expected: tuple[str, ...]
) -> None:
    row = _by_state(context_knowledge_contract()["evidence_matrix"])[state]
    wire = row["wire_mapping"]

    assert (
        wire["availability"],
        wire["reason"],
        wire["auto_status"],
        wire["required_status"],
        wire["basis"]["state"],
        wire["basis"]["availability"],
        wire["basis"]["reason"],
    ) == expected
    assert row["mutation_permission"] == "none"


def test_all_lifecycle_evidence_pairs_have_deterministic_safe_composition() -> None:
    contract = context_knowledge_contract()
    lifecycle = _by_state(contract["lifecycle_matrix"])
    evidence = _by_state(contract["evidence_matrix"])
    combined = _by_pair(contract["lifecycle_evidence_matrix"])

    assert len(combined) == len(lifecycle) * len(evidence) == 81
    for lifecycle_state, lifecycle_row in lifecycle.items():
        for evidence_state, evidence_row in evidence.items():
            row = combined[(lifecycle_state, evidence_state)]
            assert row["rendered_profile"] == lifecycle_row["rendered_profile"]
            assert row["read_only_knowledge"] == evidence_row["read_only_knowledge"]
            assert row["fallback_evidence"] == evidence_row["fallback_evidence"]
            assert row["mutation_permission"] == "none"
            if evidence_state == "invalid-surface":
                assert "independently-validated-surface" not in row["fallback_evidence"]

    absent = combined[("absent-reference", "absent")]
    assert [signal["source"] for signal in absent["signals"]["auto"]] == [
        "lifecycle",
        "evidence",
    ]
    assert [route["sources"] for route in absent["recovery_routes"]] == [
        ["lifecycle"],
        ["evidence"],
    ]


def test_recovery_templates_preserve_configured_paths_and_parse() -> None:
    contract = context_knowledge_contract()
    recovery = contract["recovery_templates"]
    declared = set(recovery["parameters"])
    formatter = Formatter()
    commands = [
        row["recovery_command"]
        for matrix in ("lifecycle_matrix", "evidence_matrix")
        for row in contract[matrix]
        if row["recovery_command"] != "none-required"
    ]
    commands.extend(recovery["reference_commands"].values())
    commands.append(recovery["unsupported_projection"]["regeneration_command"])

    substitutions = {
        "src_dir": shlex.quote("configured source"),
        "wiki_dir": shlex.quote("configured wiki"),
        "agent": "claude",
        "skills_dir": shlex.quote(".claude/configured skills"),
    }
    parser = cli._build_parser()
    for template in commands:
        placeholders = {
            field_name
            for _, field_name, _, _ in formatter.parse(template)
            if field_name is not None
        }
        assert placeholders <= declared
        tokens = shlex.split(template.format_map(substitutions))
        assert tokens[0] == "llm-wiki"
        parser.parse_args(tokens[1:])

    unsupported = _by_state(contract["evidence_matrix"])["unsupported"]
    assert not unsupported["recovery_command"].startswith("llm-wiki upgrade")
    assert recovery["unsupported_projection"]["version_probe"] == ("llm-wiki --version")
    assert recovery["unsupported_projection"]["project_upgrade_updates_cli"] is False
    assert recovery["unsupported_projection"]["package_manager_step"] == (
        "environment-specific-update-not-a-cli-command"
    )
    with pytest.raises(SystemExit) as version_exit:
        parser.parse_args(["--version"])
    assert version_exit.value.code == 0
    assert "knowledge init" not in repr(contract).casefold()


CANONICAL_MUTATIONS = [
    (("runtime_state", "active_context_protocol"), "bogus-context/v9"),
    (("versioning", "explicit", "packet_schema"), "bogus-packet/v9"),
    (("request", "explicit_behavior"), "legacy-v1"),
    (("interfaces", "cli", "entrypoint"), "llm-wiki bogus"),
    (
        ("interface_mappings", "mcp-get-context", "context", "knowledge_path"),
        "response.knowledge",
    ),
    (("modes", "auto", "unavailable_outcome"), "success-selected"),
    (("availability_semantics", "required_currentness_condition"), "required"),
    (("output_fields", "required_error", "packet_emitted"), True),
    (("output_fields", "required_error", "mutation_permitted"), 0),
    (
        ("interface_mappings", "direct-cli", "required_failure", "exit_code"),
        True,
    ),
    (("prefer_fresh", "controls_knowledge_inclusion"), True),
    (("render_profiles", "compact"), "any-reference"),
    (
        ("recovery_templates", "unsupported_projection", "project_upgrade_updates_cli"),
        True,
    ),
    (("lifecycle_commands", "status", "mutation"), "repair"),
    (("lifecycle_composition", "rule"), "compact-wins"),
    (("lifecycle_matrix", 6, "rendered_profile"), "compact"),
    (("evidence_matrix", 1, "auto_outcome"), "success-selected"),
    (("evidence_composition", "invalid_surface_scope"), "local"),
    (
        ("lifecycle_evidence_matrix", 8, "fallback_evidence"),
        ["independently-validated-surface"],
    ),
    (("safety_semantics", "grants_authority"), ["execution"]),
]


@pytest.mark.parametrize(("path", "value"), CANONICAL_MUTATIONS)
def test_validator_rejects_every_semantic_mutation(
    path: tuple[str | int, ...], value: object
) -> None:
    contract = context_knowledge_contract()
    _replace(contract, path, value)

    with pytest.raises(ContextKnowledgeContractError):
        validate_context_knowledge_contract(contract)


MALFORMED_CONTAINER_PATHS = [
    ("request", "accepted_values"),
    ("interfaces", "cli"),
    ("modes", "auto"),
    ("output_fields", "ranking_policy"),
    ("evidence_composition", "qualifiers"),
    ("lifecycle_evidence_matrix", 8, "fallback_evidence"),
]


@pytest.mark.parametrize("path", MALFORMED_CONTAINER_PATHS)
def test_validator_normalizes_malformed_container_failures(
    path: tuple[str | int, ...],
) -> None:
    contract = context_knowledge_contract()
    _replace(contract, path, None)

    with pytest.raises(ContextKnowledgeContractError):
        validate_context_knowledge_contract(contract)


def test_validator_rejects_extra_fields_reordered_lists_and_missing_rows() -> None:
    extra = context_knowledge_contract()
    extra["extra"] = True
    with pytest.raises(ContextKnowledgeContractError, match="frozen canonical"):
        validate_context_knowledge_contract(extra)

    reordered = context_knowledge_contract()
    reordered["request"]["accepted_values"].reverse()
    with pytest.raises(ContextKnowledgeContractError):
        validate_context_knowledge_contract(reordered)

    missing = context_knowledge_contract()
    missing["evidence_matrix"].pop()
    with pytest.raises(ContextKnowledgeContractError, match="states must be"):
        validate_context_knowledge_contract(missing)


def test_contract_copies_are_detached() -> None:
    first = context_knowledge_contract()
    second = context_knowledge_contract()

    first["request"]["accepted_values"].append("changed")
    first["lifecycle_matrix"][0]["allowed_actions"].clear()

    assert second == json.loads(CONTRACT_FIXTURE.read_text(encoding="utf-8"))
    assert second != first
    assert deepcopy(second) == second
