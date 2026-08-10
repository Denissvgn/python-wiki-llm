"""Frozen compatibility and failure contracts for context knowledge selection.

The active context and packet implementations remain on their v1 contracts.
This module reserves the explicit v2 wire contract so the CLI, Python API,
MCP, raw protocol, and packet implementation can be added without making
independent naming or fallback decisions.

The lifecycle and evidence matrices are data rather than prose.  Consumers can
validate a serialized copy before using it as implementation or release
evidence.  Nothing in this module reads, writes, initializes, or repairs a
knowledge projection or a managed reference.
"""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from copy import deepcopy
from typing import Any

from .contracts import CONTEXT_PROTOCOL_VERSION, QUALIFIED_CONTEXT_PACKET_SCHEMA_VERSION


CONTEXT_KNOWLEDGE_CONTRACT_SCHEMA_VERSION = "llm-wiki-context-knowledge-contract/v1"
RESERVED_CONTEXT_KNOWLEDGE_PROTOCOL_VERSION = "llm-wiki-context/v2"
RESERVED_QUALIFIED_CONTEXT_PACKET_KNOWLEDGE_SCHEMA_VERSION = (
    "llm-wiki-qualified-context-packet/v2"
)
KNOWLEDGE_MODE_VALUES = ("off", "auto", "required")
KNOWLEDGE_MODE_REQUEST_FIELD = "knowledge_mode"
KNOWLEDGE_MODE_CLI_OPTION = "--knowledge-mode"
KNOWLEDGE_MODE_DEFAULT = None

_LIFECYCLE_STATES = (
    "current-reference",
    "absent-reference",
    "modified-reference",
    "reference-install-failure",
    "skills-disabled",
    "agent-switch",
    "missing-schema",
    "plugin-blocks",
    "interrupted-upgrade",
)
_EVIDENCE_STATES = (
    "ready",
    "absent",
    "degraded-mixed",
    "unsupported",
    "incompatible",
    "snapshot-only",
    "source-changed",
    "bounded-truncated",
    "invalid-surface",
)
_LIFECYCLE_FIELDS = frozenset(
    {
        "state",
        "rendered_profile",
        "read_only_knowledge",
        "fallback_evidence",
        "allowed_actions",
        "mutation_permission",
        "warning_or_error",
        "recovery_command",
        "recovery_condition",
        "recovery_parameters",
    }
)
_EVIDENCE_FIELDS = frozenset(
    {
        "state",
        "rendered_profile",
        "read_only_knowledge",
        "fallback_evidence",
        "mutation_permission",
        "auto_outcome",
        "required_outcome",
        "warning_or_error",
        "recovery_command",
        "recovery_precondition",
        "recovery_parameters",
        "found_false_meaning",
        "wire_mapping",
    }
)
_LIFECYCLE_EVIDENCE_FIELDS = frozenset(
    {
        "lifecycle_state",
        "evidence_state",
        "rendered_profile",
        "read_only_knowledge",
        "fallback_evidence",
        "mutation_permission",
        "signals",
        "recovery_routes",
    }
)
_CONTRACT_FIELDS = frozenset(
    {
        "schema_version",
        "runtime_state",
        "versioning",
        "request",
        "interfaces",
        "interface_mappings",
        "modes",
        "availability_semantics",
        "output_fields",
        "prefer_fresh",
        "render_profiles",
        "recovery_templates",
        "lifecycle_commands",
        "lifecycle_composition",
        "lifecycle_matrix",
        "evidence_matrix",
        "evidence_composition",
        "lifecycle_evidence_matrix",
        "safety_semantics",
    }
)

_FALLBACK_CHAIN = [
    "independently-validated-surface",
    "markdown",
    "targeted-source-or-runtime",
]
_LIFECYCLE_FALLBACK_CHAIN = ["qualified-knowledge-if-ready", *_FALLBACK_CHAIN]


def _signal(level: str, code: str | None) -> dict[str, str | None]:
    return {"level": level, "code": code}


def _wire_mapping(
    *,
    availability: str,
    reason: str,
    auto_status: str,
    required_status: str,
    basis_state: str,
    basis_availability: str,
    basis_reason: str,
) -> dict[str, Any]:
    return {
        "availability": availability,
        "reason": reason,
        "auto_status": auto_status,
        "required_status": required_status,
        "basis": {
            "state": basis_state,
            "availability": basis_availability,
            "reason": basis_reason,
        },
    }


def _combined_signals(
    lifecycle: Mapping[str, Any], evidence: Mapping[str, Any]
) -> dict[str, list[dict[str, str]]]:
    result: dict[str, list[dict[str, str]]] = {}
    for mode in ("auto", "required"):
        signals: list[dict[str, str]] = []
        for source, signal in (
            ("lifecycle", lifecycle["warning_or_error"]),
            ("evidence", evidence["warning_or_error"][mode]),
        ):
            if signal["level"] != "none":
                signals.append(
                    {
                        "source": source,
                        "level": signal["level"],
                        "code": signal["code"],
                    }
                )
        result[mode] = signals
    return result


def _combined_recovery_routes(
    lifecycle: Mapping[str, Any], evidence: Mapping[str, Any]
) -> list[dict[str, Any]]:
    routes: list[dict[str, Any]] = []
    by_command: dict[str, dict[str, Any]] = {}
    candidates = (
        (
            "lifecycle",
            lifecycle["recovery_command"],
            lifecycle["recovery_parameters"],
            lifecycle["recovery_condition"],
        ),
        (
            "evidence",
            evidence["recovery_command"],
            evidence["recovery_parameters"],
            evidence["recovery_precondition"],
        ),
    )
    for source, command, parameters, precondition in candidates:
        if command == "none-required":
            continue
        if command in by_command:
            route = by_command[command]
            route["sources"].append(source)
            if precondition not in route["preconditions"]:
                route["preconditions"].append(precondition)
            for parameter in parameters:
                if parameter not in route["parameters"]:
                    route["parameters"].append(parameter)
            continue
        route = {
            "sources": [source],
            "command": command,
            "parameters": list(parameters),
            "preconditions": [precondition],
        }
        by_command[command] = route
        routes.append(route)
    return routes


_CONTRACT: dict[str, Any] = {
    "schema_version": CONTEXT_KNOWLEDGE_CONTRACT_SCHEMA_VERSION,
    "runtime_state": {
        "knowledge_mode": "reserved-not-active",
        "render_profiles": "reserved-not-active",
        "lifecycle_behavior": "reserved-not-active",
        "active_context_protocol": CONTEXT_PROTOCOL_VERSION,
        "active_packet_schema": QUALIFIED_CONTEXT_PACKET_SCHEMA_VERSION,
    },
    "versioning": {
        "legacy": {
            "context_protocol": CONTEXT_PROTOCOL_VERSION,
            "packet_schema": QUALIFIED_CONTEXT_PACKET_SCHEMA_VERSION,
            "packet_policy": "qualified-context-policy-v1",
            "mode_field": "omitted",
            "normalization": "omit-mode-field",
            "compatibility_evidence": "canonical-byte-baseline",
        },
        "explicit": {
            "context_protocol": RESERVED_CONTEXT_KNOWLEDGE_PROTOCOL_VERSION,
            "packet_schema": (
                RESERVED_QUALIFIED_CONTEXT_PACKET_KNOWLEDGE_SCHEMA_VERSION
            ),
            "packet_policy": "qualified-context-policy-v2",
            "mode_field": "required",
            "normalization": "emit-canonical-mode",
            "compatibility_evidence": "mode-and-state-matrix",
            "version_reason": "evidence-selection-and-response-semantics-change",
        },
    },
    "request": {
        "field": KNOWLEDGE_MODE_REQUEST_FIELD,
        "accepted_values": list(KNOWLEDGE_MODE_VALUES),
        "aliases": [],
        "omitted_value": KNOWLEDGE_MODE_DEFAULT,
        "omitted_behavior": "legacy-v1",
        "explicit_behavior": "v2",
        "null_on_wire": "rejected",
        "unknown_value": "invalid-request",
        "normalization": {
            "omitted": "do-not-add-field",
            "explicit": "exact-lowercase-value",
            "cli-option-with-request-file": "invalid-request",
            "api-parameter-with-request-field": "invalid-request",
            "duplicate": "invalid-request",
        },
    },
    "interfaces": {
        "cli": {
            "entrypoint": "llm-wiki context",
            "name": KNOWLEDGE_MODE_CLI_OPTION,
            "default": KNOWLEDGE_MODE_DEFAULT,
            "omission": "do-not-emit-mode",
        },
        "python-api": {
            "entrypoints": ["build_context", "build_qualified_context"],
            "name": KNOWLEDGE_MODE_REQUEST_FIELD,
            "default": KNOWLEDGE_MODE_DEFAULT,
            "omission": "do-not-emit-mode",
        },
        "mcp": {
            "tools": ["get_context", "get_context_packet"],
            "name": KNOWLEDGE_MODE_REQUEST_FIELD,
            "default": KNOWLEDGE_MODE_DEFAULT,
            "omission": "do-not-emit-mode",
        },
        "raw-protocol": {
            "path": KNOWLEDGE_MODE_REQUEST_FIELD,
            "default": KNOWLEDGE_MODE_DEFAULT,
            "omission": "field-absent",
        },
        "packet": {
            "path": f"request.{KNOWLEDGE_MODE_REQUEST_FIELD}",
            "default": KNOWLEDGE_MODE_DEFAULT,
            "omission": "use-v1-packet",
        },
    },
    "interface_mappings": {
        "direct-cli": {
            "entrypoint": "llm-wiki context",
            "context_json": {
                "knowledge_path": "knowledge",
                "ranking_policy_path": "ranking_policy",
            },
            "context_markdown": {
                "knowledge_render": "required-knowledge-disclosure-section",
                "ranking_render": "conditional-ranking-disclosure-section",
            },
            "packet": {
                "knowledge_path": "response.knowledge",
                "ranking_policy_path": "response.ranking_policy",
            },
            "required_failure": {
                "transport": "process-exit",
                "exit_code": 1,
                "render": "human-readable-error-with-stable-code-and-reason",
                "stream": "stderr",
                "stdout": "empty",
                "output_file": "not-written",
                "packet_emitted": False,
            },
        },
        "raw-protocol": {
            "entrypoint": "llm-wiki context --request",
            "context": {
                "knowledge_path": "knowledge",
                "ranking_policy_path": "ranking_policy",
            },
            "required_failure": {
                "transport": "process-exit",
                "exit_code": 1,
                "render": "canonical-required-error-json",
                "stream": "stdout",
                "stderr": "empty",
                "output_file": "not-written",
                "packet_emitted": False,
            },
        },
        "python-api-context": {
            "entrypoint": "build_context",
            "json": {
                "knowledge_path": "knowledge",
                "ranking_policy_path": "ranking_policy",
            },
            "markdown": {
                "knowledge_path": "payload.knowledge",
                "ranking_policy_path": "payload.ranking_policy",
                "content": "renders-equivalent-disclosures",
            },
            "required_failure": {
                "transport": "exception",
                "exception": "WorkspaceStateError",
                "attributes": {
                    "code": "knowledge-required-unavailable",
                    "details": "canonical-required-error",
                },
                "response_returned": False,
            },
        },
        "python-api-packet": {
            "entrypoint": "build_qualified_context",
            "packet": {
                "knowledge_path": "response.knowledge",
                "ranking_policy_path": "response.ranking_policy",
            },
            "required_failure": {
                "transport": "exception",
                "exception": "WorkspaceStateError",
                "attributes": {
                    "code": "knowledge-required-unavailable",
                    "details": "canonical-required-error",
                },
                "response_returned": False,
                "packet_emitted": False,
            },
        },
        "mcp-get-context": {
            "entrypoint": "get_context",
            "context": {
                "knowledge_path": "knowledge",
                "ranking_policy_path": "ranking_policy",
            },
            "required_failure": {
                "transport": "mcp-tool-error",
                "exception": "McpWikiError",
                "code": "knowledge-required-unavailable",
                "data": "canonical-required-error",
                "normal_result_returned": False,
            },
        },
        "mcp-get-context-packet": {
            "entrypoint": "get_context_packet",
            "packet": {
                "knowledge_path": "packet.response.knowledge",
                "ranking_policy_path": "packet.response.ranking_policy",
            },
            "unchanged": {
                "knowledge_path": "absent",
                "ranking_policy_path": "absent",
            },
            "required_failure": {
                "transport": "mcp-tool-error",
                "exception": "McpWikiError",
                "code": "knowledge-required-unavailable",
                "data": "canonical-required-error",
                "normal_result_returned": False,
                "packet_emitted": False,
            },
        },
    },
    "modes": {
        "off": {
            "context_selection_read": "not-constructed",
            "packet_basis_capture": "captured-once-without-selection",
            "ready_outcome": "success-disabled",
            "unavailable_outcome": "success-disabled",
            "response_status": "disabled",
            "mutation": "never",
        },
        "auto": {
            "context_selection_read": "constructed-once",
            "packet_basis_capture": "captured-once-and-shared-with-selection",
            "ready_outcome": "success-selected",
            "unavailable_outcome": "success-fallback",
            "response_status": "selected-or-fallback",
            "mutation": "never",
        },
        "required": {
            "context_selection_read": "constructed-once",
            "packet_basis_capture": "captured-once-and-shared-with-selection",
            "ready_outcome": "success-selected",
            "unavailable_outcome": "error-knowledge-required-unavailable",
            "response_status": "selected-or-error",
            "mutation": "never",
        },
    },
    "availability_semantics": {
        "ready": "consumable-not-complete-or-current",
        "required_success_condition": "availability-ready",
        "required_currentness_condition": "not-required",
        "snapshot_only": "ready-with-explicit-freshness-limitation",
        "degraded_mixed": "diagnostic-only-no-native-conclusion",
    },
    "output_fields": {
        "knowledge": {
            "context_path": "knowledge",
            "packet_path": "response.knowledge",
            "required": [
                "mode",
                "status",
                "availability",
                "reason",
                "selected",
                "freshness_evaluated",
                "bounds",
                "fallback",
            ],
            "bounds_required": ["total", "returned", "truncated"],
            "fallback_required": ["used", "evidence", "reason"],
            "status_values": ["disabled", "selected", "fallback"],
            "availability_values": [
                "not-evaluated",
                "ready",
                "absent",
                "degraded",
                "unsupported",
            ],
            "purpose": "request-outcome-and-selection-status",
            "raw_projection_content": "forbidden",
        },
        "packet_basis_knowledge": {
            "path": "basis.knowledge",
            "required": ["state", "availability", "reason"],
            "ready_hashes": [
                "envelope_hash",
                "knowledge_index_hash",
                "surface_index_hash",
            ],
            "optional_hashes": ["governance_hash"],
            "mode_independent": True,
            "off_behavior": "capture-actual-basis-once-without-selection",
            "not_requested_value": "forbidden-in-packet-basis",
            "purpose": "captured-provenance-only",
            "forbidden": ["mode", "selected", "ranking_policy"],
        },
        "packet_basis_freshness": {
            "path": "basis.freshness",
            "required": ["state", "evaluated", "disclosure"],
            "unevaluated_required": ["reason"],
            "evaluated_required": [
                "concept_count",
                "counts",
                "evaluation_digest",
            ],
            "per_concept_values": "not-duplicated-basis-is-aggregate-provenance",
            "purpose": "captured-aggregate-qualification-basis",
        },
        "ranking_policy": {
            "context_path": "ranking_policy",
            "packet_path": "response.ranking_policy",
            "required": [
                "requested",
                "policy",
                "scope",
                "budget_pressure",
                "applied",
                "reason",
            ],
            "policy_value": "current-first",
            "scope_value": "within-existing-relevance-tier-under-budget-pressure",
            "presence": {
                "prefer_fresh_false": "absent",
                "prefer_fresh_true": "present-even-when-applied-false",
            },
            "requested_value_when_present": True,
            "purpose": "budget-ranking-disclosure-only",
        },
        "selected_content": {
            "selected_flag_path": "knowledge.selected",
            "context_path": "knowledge.selection",
            "packet_path": "response.knowledge.selection",
            "selected_type": "boolean",
            "selection_presence": {
                "selected_true": "required",
                "selected_false": "forbidden",
            },
            "required_collections": ["concepts", "pages", "relationships"],
            "concept_freshness_path": "concepts[].freshness",
            "concept_freshness_required": [
                "state",
                "reason",
                "live_comparison_performed",
            ],
            "concept_freshness_states": [
                "not-evaluated",
                "unknown",
                "current",
                "nonsemantic-source-change",
                "source-changed",
                "basis-incompatible",
                "source-missing",
            ],
            "reason": "non-empty-stable-code",
            "live_comparison_performed": "boolean",
            "snapshot_only_freshness": {
                "state": "not-evaluated",
                "reason": "live-evaluation-not-performed",
                "live_comparison_performed": False,
            },
            "aggregate_evaluated_meaning": (
                "one-result-per-concept-not-one-live-comparison-per-concept"
            ),
            "classification": "inert-evidence",
            "authorizes": [],
            "non_authorizing_for": [
                "execution",
                "network-access",
                "filesystem-mutation",
                "source-edits",
                "git-actions",
                "plugin-selection",
                "skill-selection",
                "governance-changes",
            ],
        },
        "required_error": {
            "path": "error",
            "envelope_required": ["protocol", "ok", "error"],
            "ok": False,
            "required": [
                "code",
                "field",
                "mode",
                "availability",
                "reason",
                "fallback_evidence",
                "recovery_command",
                "mutation_permitted",
            ],
            "code": "knowledge-required-unavailable",
            "field": KNOWLEDGE_MODE_REQUEST_FIELD,
            "mutation_permitted": False,
            "packet_emitted": False,
        },
    },
    "prefer_fresh": {
        "field": "prefer_fresh",
        "default": False,
        "controls_knowledge_inclusion": False,
        "controls": "current-first-ranking-within-an-existing-relevance-tier",
        "applies_only_when": [
            "explicit-mode-auto-or-required",
            "qualified-freshness-ranks-available",
            "budget-pressure",
        ],
        "off_with_true": {
            "outcome": "success-disabled",
            "requested": True,
            "applied": False,
            "reason": "knowledge-selection-disabled",
        },
        "ranking_presence": {
            "not_requested": "absent",
            "requested": "present-even-when-applied-false",
        },
        "disclosure_matrix": [
            {
                "modes": ["off", "auto", "required"],
                "requested": False,
                "successful_response": True,
                "field": "absent",
                "applied": "not-applicable",
                "reason": "not-applicable",
            },
            {
                "modes": ["off"],
                "requested": True,
                "successful_response": True,
                "field": "present",
                "applied": False,
                "reason": "knowledge-selection-disabled",
            },
            {
                "modes": ["auto", "required"],
                "requested": True,
                "successful_response": True,
                "condition": "selected-with-budget-pressure-and-qualified-ranks",
                "field": "present",
                "applied": True,
                "reason": "same-tier-budget-pressure",
            },
            {
                "modes": ["auto", "required"],
                "requested": True,
                "successful_response": True,
                "condition": "selected-without-budget-pressure",
                "field": "present",
                "applied": False,
                "reason": "no-budget-pressure",
            },
            {
                "modes": ["auto", "required"],
                "requested": True,
                "successful_response": True,
                "condition": "selected-without-qualified-freshness-ranks",
                "field": "present",
                "applied": False,
                "reason": "qualified-freshness-ranks-unavailable",
            },
            {
                "modes": ["auto"],
                "requested": True,
                "successful_response": True,
                "condition": "knowledge-fallback",
                "field": "present",
                "applied": False,
                "reason": "knowledge-unavailable",
            },
            {
                "modes": ["required"],
                "requested": True,
                "successful_response": False,
                "condition": "knowledge-required-unavailable",
                "field": "absent-with-success-response",
                "applied": "not-applicable",
                "reason": "not-applicable",
            },
        ],
        "never_filters_stale_or_unknown": True,
        "never_reorders_relevance_tiers": True,
        "legacy_v1_coupling_preserved": True,
    },
    "render_profiles": {
        "implementation_state": "reserved-not-active",
        "compact": "verified-current-managed-reference-only",
        "expanded_inline": "safe-inline-procedure-without-reference-dependency",
        "not_rendered": "schema-file-absent",
        "current_runtime": "legacy-expanded-without-profile-marker",
    },
    "recovery_templates": {
        "implementation_state": "reserved-not-active",
        "parameters": {
            "src_dir": {
                "source": "resolved-request-or-project-configuration",
                "render": "shell-quoted",
            },
            "wiki_dir": {
                "source": "resolved-request-or-project-configuration",
                "render": "shell-quoted",
            },
            "agent": {
                "source": "resolved-request-or-project-configuration",
                "render": "exact-cli-choice",
            },
            "skills_dir": {
                "source": "derived-from-resolved-configured-agent",
                "render": "shell-quoted",
            },
        },
        "rules": [
            "never-substitute-a-default-for-a-configured-path",
            "carry-resolved-wiki-dir-through-project-recovery",
            "carry-resolved-agent-through-schema-or-reference-recovery",
        ],
        "unsupported_projection": {
            "package_manager_step": "environment-specific-update-not-a-cli-command",
            "version_probe": "llm-wiki --version",
            "precondition": (
                "installed-cli-version-supports-required-projection-schema"
            ),
            "regeneration_command": (
                "llm-wiki sync --src-dir {src_dir} --wiki-dir {wiki_dir}"
            ),
            "project_upgrade_updates_cli": False,
        },
        "reference_commands": {
            "install": (
                "llm-wiki skills install --dest {skills_dir} --skill wiki-reference"
            ),
            "force_refresh": (
                "llm-wiki skills install --dest {skills_dir} "
                "--skill wiki-reference --force"
            ),
        },
    },
    "lifecycle_commands": {
        "init": {
            "implementation_state": "reserved-not-active",
            "render_order": "verify-reference-before-compact-profile",
            "reference_failure": "expanded-profile",
            "knowledge_plane": "unchanged",
            "governance": "never-initialize",
        },
        "upgrade": {
            "implementation_state": "reserved-not-active",
            "render_order": "verify-reference-before-compact-profile",
            "reference_failure": "expanded-profile",
            "interruption": "expanded_inline-or-not-rendered-never-compact-broken",
            "modified_reference": "preserve-unless-explicit-force-refresh",
            "knowledge_plane": "unchanged",
            "governance": "never-initialize",
        },
        "status": {
            "implementation_state": "reserved-not-active",
            "live_reference_check": True,
            "required_fields": [
                "rendered_profile",
                "reference_state",
                "reference_path",
                "reference_current",
                "read_only_knowledge",
                "warning",
                "recovery_command",
            ],
            "knowledge_plane": "reported-independently",
            "mutation": "never",
        },
        "uninstall": {
            "implementation_state": "reserved-not-active",
            "managed_block": "remove",
            "unmodified_reference": "remove",
            "modified_reference": "preserve-and-warn",
            "knowledge_artifacts": "keep-unless-remove-wiki-requested",
            "user_and_plugin_content": "preserve",
            "governance": "never-initialize",
        },
    },
    "lifecycle_composition": {
        "rule": "most-conservative-profile-wins",
        "profile_precedence": [
            "not-rendered",
            "expanded_inline",
            "reference-state-dependent",
            "compact",
        ],
        "plugin_blocks": "preserve-regardless-of-profile",
        "read_only_knowledge": "independent-regardless-of-combination",
    },
    "lifecycle_matrix": [
        {
            "state": "current-reference",
            "rendered_profile": "compact",
            "read_only_knowledge": "independent",
            "fallback_evidence": list(_LIFECYCLE_FALLBACK_CHAIN),
            "allowed_actions": [
                "read-context",
                "run-explicitly-authorized-workflow",
                "explicit-uninstall",
            ],
            "mutation_permission": "explicit-command-only",
            "warning_or_error": _signal("none", None),
            "recovery_command": "none-required",
            "recovery_condition": "not-applicable",
            "recovery_parameters": [],
        },
        {
            "state": "absent-reference",
            "rendered_profile": "expanded_inline",
            "read_only_knowledge": "independent",
            "fallback_evidence": list(_LIFECYCLE_FALLBACK_CHAIN),
            "allowed_actions": ["read-context", "explicit-reference-install"],
            "mutation_permission": "explicit-command-only",
            "warning_or_error": _signal("warning", "managed-reference-absent"),
            "recovery_command": (
                "llm-wiki upgrade --wiki-dir {wiki_dir} --agent {agent} --skills"
            ),
            "recovery_condition": "managed-install-target-is-writable",
            "recovery_parameters": ["wiki_dir", "agent"],
        },
        {
            "state": "modified-reference",
            "rendered_profile": "expanded_inline",
            "read_only_knowledge": "independent",
            "fallback_evidence": list(_LIFECYCLE_FALLBACK_CHAIN),
            "allowed_actions": [
                "read-context",
                "preserve-local-reference",
                "explicit-force-refresh",
            ],
            "mutation_permission": "preserve-unless-explicitly-replaced",
            "warning_or_error": _signal("warning", "managed-reference-modified"),
            "recovery_command": (
                "llm-wiki upgrade --wiki-dir {wiki_dir} --agent {agent} --skills"
            ),
            "recovery_condition": "local-changes-preserved-or-discarded-explicitly",
            "recovery_parameters": ["wiki_dir", "agent"],
        },
        {
            "state": "reference-install-failure",
            "rendered_profile": "expanded_inline",
            "read_only_knowledge": "independent",
            "fallback_evidence": list(_LIFECYCLE_FALLBACK_CHAIN),
            "allowed_actions": ["read-context", "explicit-install-retry"],
            "mutation_permission": "no-automatic-retry",
            "warning_or_error": _signal("error", "managed-reference-install-failed"),
            "recovery_command": (
                "llm-wiki upgrade --wiki-dir {wiki_dir} --agent {agent} --skills"
            ),
            "recovery_condition": "install-failure-corrected",
            "recovery_parameters": ["wiki_dir", "agent"],
        },
        {
            "state": "skills-disabled",
            "rendered_profile": "expanded_inline",
            "read_only_knowledge": "independent",
            "fallback_evidence": list(_LIFECYCLE_FALLBACK_CHAIN),
            "allowed_actions": ["read-context", "explicit-skill-opt-in"],
            "mutation_permission": "reference-install-disabled",
            "warning_or_error": _signal("warning", "managed-reference-disabled"),
            "recovery_command": (
                "llm-wiki upgrade --wiki-dir {wiki_dir} --agent {agent} --skills"
            ),
            "recovery_condition": "user-enables-managed-reference",
            "recovery_parameters": ["wiki_dir", "agent"],
        },
        {
            "state": "agent-switch",
            "rendered_profile": "expanded_inline",
            "read_only_knowledge": "independent",
            "fallback_evidence": list(_LIFECYCLE_FALLBACK_CHAIN),
            "allowed_actions": [
                "read-context",
                "preserve-modified-old-reference",
                "verify-target-reference",
            ],
            "mutation_permission": "explicit-upgrade-only",
            "warning_or_error": _signal("warning", "target-reference-unverified"),
            "recovery_command": (
                "llm-wiki upgrade --wiki-dir {wiki_dir} --agent {agent} --skills"
            ),
            "recovery_condition": "target-agent-selected-explicitly",
            "recovery_parameters": ["wiki_dir", "agent"],
        },
        {
            "state": "missing-schema",
            "rendered_profile": "not-rendered",
            "read_only_knowledge": "independent",
            "fallback_evidence": list(_LIFECYCLE_FALLBACK_CHAIN),
            "allowed_actions": ["read-context", "explicit-schema-init"],
            "mutation_permission": "explicit-init-only",
            "warning_or_error": _signal("error", "managed-schema-absent"),
            "recovery_command": ("llm-wiki init --wiki-dir {wiki_dir} --agent {agent}"),
            "recovery_condition": "target-agent-selected-explicitly",
            "recovery_parameters": ["wiki_dir", "agent"],
        },
        {
            "state": "plugin-blocks",
            "rendered_profile": "reference-state-dependent",
            "read_only_knowledge": "independent",
            "fallback_evidence": list(_LIFECYCLE_FALLBACK_CHAIN),
            "allowed_actions": ["read-context", "preserve-plugin-blocks"],
            "mutation_permission": "plugin-blocks-preserved-exactly",
            "warning_or_error": _signal("none", None),
            "recovery_command": "none-required",
            "recovery_condition": "not-applicable",
            "recovery_parameters": [],
        },
        {
            "state": "interrupted-upgrade",
            "rendered_profile": "expanded_inline",
            "read_only_knowledge": "independent",
            "fallback_evidence": list(_LIFECYCLE_FALLBACK_CHAIN),
            "allowed_actions": ["read-context", "explicit-upgrade-resume"],
            "mutation_permission": "explicit-resume-only",
            "warning_or_error": _signal("error", "managed-upgrade-interrupted"),
            "recovery_command": (
                "llm-wiki upgrade --wiki-dir {wiki_dir} --agent {agent} --skills"
            ),
            "recovery_condition": "partial-write-state-inspected",
            "recovery_parameters": ["wiki_dir", "agent"],
        },
    ],
    "evidence_matrix": [
        {
            "state": "ready",
            "rendered_profile": "reference-dependent",
            "read_only_knowledge": "qualified-and-selectable",
            "fallback_evidence": ["qualified-knowledge", *_FALLBACK_CHAIN],
            "mutation_permission": "none",
            "auto_outcome": "success-selected",
            "required_outcome": "success-selected",
            "warning_or_error": {
                "auto": _signal("none", None),
                "required": _signal("none", None),
            },
            "recovery_command": "none-required",
            "recovery_precondition": "none-required",
            "recovery_parameters": [],
            "found_false_meaning": "qualified-only-with-declared-coverage-and-bounds",
            "wire_mapping": _wire_mapping(
                availability="ready",
                reason="knowledge-ready",
                auto_status="selected",
                required_status="selected",
                basis_state="recorded",
                basis_availability="ready",
                basis_reason="all-projection-commitments-match",
            ),
        },
        {
            "state": "absent",
            "rendered_profile": "reference-dependent",
            "read_only_knowledge": "unavailable",
            "fallback_evidence": list(_FALLBACK_CHAIN),
            "mutation_permission": "none",
            "auto_outcome": "success-fallback",
            "required_outcome": "error",
            "warning_or_error": {
                "auto": _signal("warning", "knowledge-projection-not-present"),
                "required": _signal("error", "knowledge-required-unavailable"),
            },
            "recovery_command": (
                "llm-wiki sync --src-dir {src_dir} --wiki-dir {wiki_dir}"
            ),
            "recovery_precondition": "explicit-projection-regeneration-request",
            "recovery_parameters": ["src_dir", "wiki_dir"],
            "found_false_meaning": "inconclusive",
            "wire_mapping": _wire_mapping(
                availability="absent",
                reason="knowledge-projection-not-present",
                auto_status="fallback",
                required_status="error-no-context-response",
                basis_state="unavailable",
                basis_availability="absent",
                basis_reason="knowledge-projection-not-present",
            ),
        },
        {
            "state": "degraded-mixed",
            "rendered_profile": "reference-dependent",
            "read_only_knowledge": "diagnostic-only-no-native-conclusion",
            "fallback_evidence": list(_FALLBACK_CHAIN),
            "mutation_permission": "none",
            "auto_outcome": "success-fallback-with-degraded-disclosure",
            "required_outcome": "error",
            "warning_or_error": {
                "auto": _signal("warning", "knowledge-projection-degraded"),
                "required": _signal("error", "knowledge-required-unavailable"),
            },
            "recovery_command": (
                "llm-wiki sync --src-dir {src_dir} --wiki-dir {wiki_dir}"
            ),
            "recovery_precondition": "explicit-projection-regeneration-request",
            "recovery_parameters": ["src_dir", "wiki_dir"],
            "found_false_meaning": "inconclusive",
            "wire_mapping": _wire_mapping(
                availability="degraded",
                reason=("policy-selected-surface-only-fallback-after-mixed-snapshot"),
                auto_status="fallback",
                required_status="error-no-context-response",
                basis_state="unavailable",
                basis_availability="degraded",
                basis_reason=(
                    "policy-selected-surface-only-fallback-after-mixed-snapshot"
                ),
            ),
        },
        {
            "state": "unsupported",
            "rendered_profile": "reference-dependent",
            "read_only_knowledge": "rejected-without-query",
            "fallback_evidence": list(_FALLBACK_CHAIN),
            "mutation_permission": "none",
            "auto_outcome": "success-fallback",
            "required_outcome": "error",
            "warning_or_error": {
                "auto": _signal("warning", "knowledge-schema-unsupported"),
                "required": _signal("error", "knowledge-required-unavailable"),
            },
            "recovery_command": (
                "llm-wiki sync --src-dir {src_dir} --wiki-dir {wiki_dir}"
            ),
            "recovery_precondition": (
                "installed-cli-version-supports-required-projection-schema"
            ),
            "recovery_parameters": ["src_dir", "wiki_dir"],
            "found_false_meaning": "inconclusive",
            "wire_mapping": _wire_mapping(
                availability="unsupported",
                reason="knowledge-schema-version-unsupported",
                auto_status="fallback",
                required_status="error-no-context-response",
                basis_state="unavailable",
                basis_availability="unsupported",
                basis_reason="knowledge-schema-version-unsupported",
            ),
        },
        {
            "state": "incompatible",
            "rendered_profile": "reference-dependent",
            "read_only_knowledge": "rejected-without-query",
            "fallback_evidence": list(_FALLBACK_CHAIN),
            "mutation_permission": "none",
            "auto_outcome": "success-fallback",
            "required_outcome": "error",
            "warning_or_error": {
                "auto": _signal("warning", "knowledge-basis-incompatible"),
                "required": _signal("error", "knowledge-required-unavailable"),
            },
            "recovery_command": (
                "llm-wiki sync --src-dir {src_dir} --wiki-dir {wiki_dir}"
            ),
            "recovery_precondition": "incompatible-basis-inputs-reconciled",
            "recovery_parameters": ["src_dir", "wiki_dir"],
            "found_false_meaning": "inconclusive",
            "wire_mapping": _wire_mapping(
                availability="degraded",
                reason="knowledge-basis-incompatible",
                auto_status="fallback",
                required_status="error-no-context-response",
                basis_state="unavailable",
                basis_availability="degraded",
                basis_reason="knowledge-basis-incompatible",
            ),
        },
        {
            "state": "snapshot-only",
            "rendered_profile": "reference-dependent",
            "read_only_knowledge": "selectable-attributed-snapshot-not-current",
            "fallback_evidence": ["attributed-knowledge-snapshot", *_FALLBACK_CHAIN],
            "mutation_permission": "none",
            "auto_outcome": "success-selected-with-snapshot-disclosure",
            "required_outcome": "success-selected-with-snapshot-disclosure",
            "warning_or_error": {
                "auto": _signal("warning", "knowledge-snapshot-only"),
                "required": _signal("warning", "knowledge-snapshot-only"),
            },
            "recovery_command": "none-required",
            "recovery_precondition": "none-required",
            "recovery_parameters": [],
            "found_false_meaning": "inconclusive",
            "wire_mapping": _wire_mapping(
                availability="ready",
                reason="knowledge-snapshot-only",
                auto_status="selected",
                required_status="selected",
                basis_state="recorded",
                basis_availability="ready",
                basis_reason="all-projection-commitments-match",
            ),
        },
        {
            "state": "source-changed",
            "rendered_profile": "reference-dependent",
            "read_only_knowledge": "selectable-with-per-concept-qualification",
            "fallback_evidence": [
                "qualified-knowledge",
                "targeted-source-or-runtime",
            ],
            "mutation_permission": "none",
            "auto_outcome": "success-selected-with-source-change-disclosure",
            "required_outcome": "success-selected-with-source-change-disclosure",
            "warning_or_error": {
                "auto": _signal("warning", "knowledge-source-changed"),
                "required": _signal("warning", "knowledge-source-changed"),
            },
            "recovery_command": (
                "llm-wiki sync --src-dir {src_dir} --wiki-dir {wiki_dir}"
            ),
            "recovery_precondition": "explicit-projection-regeneration-request",
            "recovery_parameters": ["src_dir", "wiki_dir"],
            "found_false_meaning": "inconclusive-for-current-source",
            "wire_mapping": _wire_mapping(
                availability="ready",
                reason="knowledge-source-changed",
                auto_status="selected",
                required_status="selected",
                basis_state="recorded",
                basis_availability="ready",
                basis_reason="all-projection-commitments-match",
            ),
        },
        {
            "state": "bounded-truncated",
            "rendered_profile": "reference-dependent",
            "read_only_knowledge": "selectable-with-explicit-bounds",
            "fallback_evidence": [
                "bounded-qualified-knowledge",
                "targeted-source-or-runtime",
            ],
            "mutation_permission": "none",
            "auto_outcome": "success-selected-with-bounds",
            "required_outcome": "success-selected-with-bounds",
            "warning_or_error": {
                "auto": _signal("warning", "knowledge-results-truncated"),
                "required": _signal("warning", "knowledge-results-truncated"),
            },
            "recovery_command": "none-required",
            "recovery_precondition": "none-required",
            "recovery_parameters": [],
            "found_false_meaning": "inconclusive-outside-returned-bounds",
            "wire_mapping": _wire_mapping(
                availability="ready",
                reason="knowledge-results-truncated",
                auto_status="selected",
                required_status="selected",
                basis_state="recorded",
                basis_availability="ready",
                basis_reason="all-projection-commitments-match",
            ),
        },
        {
            "state": "invalid-surface",
            "rendered_profile": "reference-dependent",
            "read_only_knowledge": "rejected-when-surface-binding-is-invalid",
            "fallback_evidence": ["markdown", "targeted-source-or-runtime"],
            "mutation_permission": "none",
            "auto_outcome": "success-fallback-without-surface",
            "required_outcome": "error",
            "warning_or_error": {
                "auto": _signal("warning", "surface-validation-failed"),
                "required": _signal("error", "knowledge-required-unavailable"),
            },
            "recovery_command": (
                "llm-wiki sync --src-dir {src_dir} --wiki-dir {wiki_dir}"
            ),
            "recovery_precondition": "surface-binding-inputs-corrected",
            "recovery_parameters": ["src_dir", "wiki_dir"],
            "found_false_meaning": "inconclusive",
            "wire_mapping": _wire_mapping(
                availability="degraded",
                reason="surface-validation-failed",
                auto_status="fallback",
                required_status="error-no-context-response",
                basis_state="unavailable",
                basis_availability="degraded",
                basis_reason=("policy-selected-surface-only-fallback-after-invalid"),
            ),
        },
    ],
    "evidence_composition": {
        "base_state_precedence": [
            "invalid-surface",
            "incompatible",
            "unsupported",
            "absent",
            "degraded-mixed",
            "ready",
        ],
        "rejecting_base_states": [
            "invalid-surface",
            "incompatible",
            "unsupported",
            "absent",
            "degraded-mixed",
        ],
        "qualifiers": [
            "snapshot-only",
            "source-changed",
            "bounded-truncated",
        ],
        "qualifiers_accumulate": True,
        "auto": "fallback-if-any-rejecting-base-state-applies",
        "required": "error-if-any-rejecting-base-state-applies",
        "profile_source": "lifecycle-row-only",
        "knowledge_and_fallback_source": "resolved-evidence-row-only",
        "signal_order": "lifecycle-then-evidence-omitting-none",
        "recovery_order": "lifecycle-then-evidence-deduplicated",
        "read_mutation_permission": "none",
        "invalid_surface": (
            "remove-independently-validated-surface-after-all-composition"
        ),
        "invalid_surface_scope": "global-all-lifecycle-states",
        "found_false": "apply-the-most-conservative-row-meaning",
    },
    "lifecycle_evidence_matrix": [],
    "safety_semantics": {
        "selected_content": "inert-evidence",
        "stored_operations_and_instructions": "never-executed-as-authority",
        "grants_authority": [],
        "does_not_authorize": [
            "execution",
            "network-access",
            "filesystem-mutation",
            "source-edits",
            "git-actions",
            "plugin-selection",
            "skill-selection",
            "governance-changes",
        ],
        "raw_projection_json": "not-a-supported-read-interface",
        "governance_initialization": "never",
    },
}

_CONTRACT["lifecycle_evidence_matrix"] = [
    {
        "lifecycle_state": lifecycle["state"],
        "evidence_state": evidence["state"],
        "rendered_profile": lifecycle["rendered_profile"],
        "read_only_knowledge": evidence["read_only_knowledge"],
        "fallback_evidence": list(evidence["fallback_evidence"]),
        "mutation_permission": "none",
        "signals": _combined_signals(lifecycle, evidence),
        "recovery_routes": _combined_recovery_routes(lifecycle, evidence),
    }
    for lifecycle in _CONTRACT["lifecycle_matrix"]
    for evidence in _CONTRACT["evidence_matrix"]
]

_CANONICAL_CONTRACT = deepcopy(_CONTRACT)
_CANONICAL_CONTRACT_JSON = json.dumps(
    _CANONICAL_CONTRACT,
    allow_nan=False,
    ensure_ascii=False,
    separators=(",", ":"),
    sort_keys=True,
)


class ContextKnowledgeContractError(ValueError):
    """A serialized context-knowledge contract violates the frozen shape."""


def _matrix_by_state(
    value: object,
    *,
    field: str,
    expected_states: Sequence[str],
    required_fields: frozenset[str],
) -> dict[str, Mapping[str, Any]]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        raise ContextKnowledgeContractError(f"{field} must be an array")
    rows: dict[str, Mapping[str, Any]] = {}
    for index, row in enumerate(value):
        if not isinstance(row, Mapping):
            raise ContextKnowledgeContractError(f"{field}[{index}] must be an object")
        missing = sorted(required_fields - set(row))
        if missing:
            raise ContextKnowledgeContractError(
                f"{field}[{index}] is missing {missing[0]}"
            )
        state = row["state"]
        if not isinstance(state, str):
            raise ContextKnowledgeContractError(
                f"{field}[{index}].state must be a string"
            )
        if state in rows:
            raise ContextKnowledgeContractError(f"{field} duplicates state {state}")
        rows[state] = row
    if set(rows) != set(expected_states):
        raise ContextKnowledgeContractError(
            f"{field} states must be {sorted(expected_states)}"
        )
    return rows


def _validate_context_knowledge_contract(contract: Mapping[str, Any]) -> None:
    """Validate completeness and the fail-safe cross-row invariants."""

    if not isinstance(contract, Mapping):
        raise ContextKnowledgeContractError("contract must be an object")
    missing_contract_fields = sorted(_CONTRACT_FIELDS - set(contract))
    if missing_contract_fields:
        raise ContextKnowledgeContractError(
            f"contract is missing {missing_contract_fields[0]}"
        )
    if contract.get("schema_version") != CONTEXT_KNOWLEDGE_CONTRACT_SCHEMA_VERSION:
        raise ContextKnowledgeContractError("schema_version is unsupported")
    runtime_state = contract.get("runtime_state")
    if not isinstance(runtime_state, Mapping) or any(
        runtime_state.get(name) != "reserved-not-active"
        for name in ("knowledge_mode", "render_profiles", "lifecycle_behavior")
    ):
        raise ContextKnowledgeContractError(
            "planned context and lifecycle behavior must remain reserved"
        )

    request = contract.get("request")
    if not isinstance(request, Mapping):
        raise ContextKnowledgeContractError("request must be an object")
    if request.get("field") != KNOWLEDGE_MODE_REQUEST_FIELD:
        raise ContextKnowledgeContractError("request.field is not canonical")
    if tuple(request.get("accepted_values", ())) != KNOWLEDGE_MODE_VALUES:
        raise ContextKnowledgeContractError("request.accepted_values are not canonical")
    if request.get("aliases") != []:
        raise ContextKnowledgeContractError("request aliases are not supported")
    if request.get("omitted_value", object()) is not None:
        raise ContextKnowledgeContractError("request.omitted_value must be null")
    if request.get("normalization") != {
        "omitted": "do-not-add-field",
        "explicit": "exact-lowercase-value",
        "cli-option-with-request-file": "invalid-request",
        "api-parameter-with-request-field": "invalid-request",
        "duplicate": "invalid-request",
    }:
        raise ContextKnowledgeContractError("request.normalization is incomplete")

    interfaces = contract.get("interfaces")
    if not isinstance(interfaces, Mapping) or set(interfaces) != {
        "cli",
        "python-api",
        "mcp",
        "raw-protocol",
        "packet",
    }:
        raise ContextKnowledgeContractError("interfaces are incomplete")
    if interfaces["cli"].get("name") != KNOWLEDGE_MODE_CLI_OPTION:
        raise ContextKnowledgeContractError("interfaces.cli.name is not canonical")
    for name in ("python-api", "mcp"):
        if interfaces[name].get("name") != KNOWLEDGE_MODE_REQUEST_FIELD:
            raise ContextKnowledgeContractError(
                f"interfaces.{name}.name is not canonical"
            )
    interface_mappings = contract.get("interface_mappings")
    if not isinstance(interface_mappings, Mapping) or set(interface_mappings) != {
        "direct-cli",
        "raw-protocol",
        "python-api-context",
        "python-api-packet",
        "mcp-get-context",
        "mcp-get-context-packet",
    }:
        raise ContextKnowledgeContractError("interface_mappings are incomplete")

    modes = contract.get("modes")
    if not isinstance(modes, Mapping) or set(modes) != set(KNOWLEDGE_MODE_VALUES):
        raise ContextKnowledgeContractError("modes are incomplete")
    if any(mode.get("mutation") != "never" for mode in modes.values()):
        raise ContextKnowledgeContractError("context modes must never mutate")

    availability_semantics = contract.get("availability_semantics")
    if not isinstance(availability_semantics, Mapping) or (
        availability_semantics.get("required_success_condition") != "availability-ready"
        or availability_semantics.get("required_currentness_condition")
        != "not-required"
    ):
        raise ContextKnowledgeContractError("availability_semantics are incomplete")

    output_fields = contract.get("output_fields")
    if not isinstance(output_fields, Mapping) or set(output_fields) != {
        "knowledge",
        "packet_basis_knowledge",
        "packet_basis_freshness",
        "ranking_policy",
        "selected_content",
        "required_error",
    }:
        raise ContextKnowledgeContractError("output_fields are incomplete")
    for name in (
        "knowledge",
        "packet_basis_knowledge",
        "packet_basis_freshness",
        "ranking_policy",
        "required_error",
    ):
        required = output_fields[name].get("required")
        if not isinstance(required, Sequence) or isinstance(required, (str, bytes)):
            raise ContextKnowledgeContractError(
                f"output_fields.{name}.required must be an array"
            )
    if output_fields["required_error"].get("mutation_permitted") is not False:
        raise ContextKnowledgeContractError(
            "required error must forbid mutation explicitly"
        )
    ranking_presence = output_fields["ranking_policy"].get("presence")
    if ranking_presence != {
        "prefer_fresh_false": "absent",
        "prefer_fresh_true": "present-even-when-applied-false",
    }:
        raise ContextKnowledgeContractError("ranking presence is not canonical")

    preference = contract.get("prefer_fresh")
    if not isinstance(preference, Mapping):
        raise ContextKnowledgeContractError("prefer_fresh must be an object")
    if preference.get("default") is not False:
        raise ContextKnowledgeContractError("prefer_fresh.default must be false")
    if preference.get("controls_knowledge_inclusion") is not False:
        raise ContextKnowledgeContractError(
            "prefer_fresh must not control knowledge inclusion"
        )
    if preference.get("never_filters_stale_or_unknown") is not True:
        raise ContextKnowledgeContractError(
            "prefer_fresh must retain stale and unknown evidence"
        )
    if preference.get("never_reorders_relevance_tiers") is not True:
        raise ContextKnowledgeContractError(
            "prefer_fresh must preserve relevance tiers"
        )
    off_with_true = preference.get("off_with_true")
    if not isinstance(off_with_true, Mapping) or off_with_true != {
        "outcome": "success-disabled",
        "requested": True,
        "applied": False,
        "reason": "knowledge-selection-disabled",
    }:
        raise ContextKnowledgeContractError(
            "off plus prefer_fresh must succeed with ranking not applied"
        )

    lifecycle_commands = contract.get("lifecycle_commands")
    if not isinstance(lifecycle_commands, Mapping) or set(lifecycle_commands) != {
        "init",
        "upgrade",
        "status",
        "uninstall",
    }:
        raise ContextKnowledgeContractError("lifecycle_commands are incomplete")
    status_fields = lifecycle_commands["status"].get("required_fields")
    if not isinstance(status_fields, Sequence) or set(status_fields) != {
        "rendered_profile",
        "reference_state",
        "reference_path",
        "reference_current",
        "read_only_knowledge",
        "warning",
        "recovery_command",
    }:
        raise ContextKnowledgeContractError(
            "lifecycle_commands.status.required_fields are incomplete"
        )
    lifecycle_composition = contract.get("lifecycle_composition")
    if not isinstance(lifecycle_composition, Mapping) or (
        lifecycle_composition.get("rule") != "most-conservative-profile-wins"
    ):
        raise ContextKnowledgeContractError("lifecycle_composition is incomplete")

    lifecycle = _matrix_by_state(
        contract.get("lifecycle_matrix"),
        field="lifecycle_matrix",
        expected_states=_LIFECYCLE_STATES,
        required_fields=_LIFECYCLE_FIELDS,
    )
    for state in (
        "absent-reference",
        "modified-reference",
        "reference-install-failure",
        "skills-disabled",
        "agent-switch",
        "missing-schema",
        "interrupted-upgrade",
    ):
        if lifecycle[state]["rendered_profile"] == "compact":
            raise ContextKnowledgeContractError(
                f"lifecycle_matrix.{state} must not render compact"
            )
    if any(row["read_only_knowledge"] != "independent" for row in lifecycle.values()):
        raise ContextKnowledgeContractError(
            "managed-reference lifecycle must not control read-only knowledge"
        )
    if any(
        not row["fallback_evidence"]
        or row["fallback_evidence"][0] != "qualified-knowledge-if-ready"
        for row in lifecycle.values()
    ):
        raise ContextKnowledgeContractError(
            "lifecycle fallback must retain qualified knowledge when ready"
        )
    if any(
        not isinstance(row["recovery_command"], str) or not row["recovery_command"]
        for row in lifecycle.values()
    ):
        raise ContextKnowledgeContractError(
            "every lifecycle recovery_command must be explicit"
        )

    evidence = _matrix_by_state(
        contract.get("evidence_matrix"),
        field="evidence_matrix",
        expected_states=_EVIDENCE_STATES,
        required_fields=_EVIDENCE_FIELDS,
    )
    if any(
        row["rendered_profile"] != "reference-dependent" for row in evidence.values()
    ):
        raise ContextKnowledgeContractError(
            "evidence availability must not select the rendered profile"
        )
    if any(row["mutation_permission"] != "none" for row in evidence.values()):
        raise ContextKnowledgeContractError("evidence fallback must be read-only")
    if evidence["degraded-mixed"]["read_only_knowledge"] != (
        "diagnostic-only-no-native-conclusion"
    ):
        raise ContextKnowledgeContractError(
            "degraded evidence must not support a native conclusion"
        )
    if not str(evidence["snapshot-only"]["required_outcome"]).startswith("success-"):
        raise ContextKnowledgeContractError(
            "required mode must accept a ready attributed snapshot"
        )
    if any(
        not isinstance(row["recovery_command"], str) or not row["recovery_command"]
        for row in evidence.values()
    ):
        raise ContextKnowledgeContractError(
            "every evidence recovery_command must be explicit"
        )
    evidence_composition = contract.get("evidence_composition")
    if not isinstance(evidence_composition, Mapping) or set(
        evidence_composition.get("qualifiers", ())
    ) != {"snapshot-only", "source-changed", "bounded-truncated"}:
        raise ContextKnowledgeContractError("evidence_composition is incomplete")

    combined = contract.get("lifecycle_evidence_matrix")
    if not isinstance(combined, Sequence) or isinstance(combined, (str, bytes)):
        raise ContextKnowledgeContractError(
            "lifecycle_evidence_matrix must be an array"
        )
    combined_by_pair: dict[tuple[str, str], Mapping[str, Any]] = {}
    for index, row in enumerate(combined):
        if not isinstance(row, Mapping):
            raise ContextKnowledgeContractError(
                f"lifecycle_evidence_matrix[{index}] must be an object"
            )
        missing = sorted(_LIFECYCLE_EVIDENCE_FIELDS - set(row))
        if missing:
            raise ContextKnowledgeContractError(
                f"lifecycle_evidence_matrix[{index}] is missing {missing[0]}"
            )
        pair = (row["lifecycle_state"], row["evidence_state"])
        if not all(isinstance(value, str) for value in pair):
            raise ContextKnowledgeContractError(
                f"lifecycle_evidence_matrix[{index}] states must be strings"
            )
        if pair in combined_by_pair:
            raise ContextKnowledgeContractError(
                f"lifecycle_evidence_matrix duplicates {pair}"
            )
        combined_by_pair[pair] = row
    expected_pairs = {
        (lifecycle_state, evidence_state)
        for lifecycle_state in _LIFECYCLE_STATES
        for evidence_state in _EVIDENCE_STATES
    }
    if set(combined_by_pair) != expected_pairs:
        raise ContextKnowledgeContractError(
            "lifecycle_evidence_matrix must cover the complete cross-product"
        )
    for lifecycle_state in _LIFECYCLE_STATES:
        invalid = combined_by_pair[(lifecycle_state, "invalid-surface")]
        if "independently-validated-surface" in invalid["fallback_evidence"]:
            raise ContextKnowledgeContractError(
                "invalid surface must be removed after all fallback composition"
            )
        if invalid["mutation_permission"] != "none":
            raise ContextKnowledgeContractError(
                "combined context reads must never grant mutation"
            )

    try:
        candidate_json = json.dumps(
            contract,
            allow_nan=False,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        )
    except (TypeError, ValueError) as exc:
        raise ContextKnowledgeContractError(
            "contract must contain canonical JSON values"
        ) from exc
    serialized = candidate_json.casefold()
    if "knowledge init" in serialized:
        raise ContextKnowledgeContractError(
            "context and recovery contracts must not initialize governance"
        )
    if contract != _CANONICAL_CONTRACT or candidate_json != _CANONICAL_CONTRACT_JSON:
        raise ContextKnowledgeContractError(
            "contract differs from the frozen canonical contract"
        )


def validate_context_knowledge_contract(contract: Mapping[str, Any]) -> None:
    """Reject every non-canonical candidate with the declared error type."""

    try:
        _validate_context_knowledge_contract(contract)
    except ContextKnowledgeContractError:
        raise
    except (AttributeError, IndexError, KeyError, TypeError) as exc:
        raise ContextKnowledgeContractError(
            "contract contains a malformed canonical container"
        ) from exc


def context_knowledge_contract() -> dict[str, Any]:
    """Return a detached JSON-compatible copy of the frozen contract."""

    contract = deepcopy(_CANONICAL_CONTRACT)
    validate_context_knowledge_contract(contract)
    return contract


validate_context_knowledge_contract(_CANONICAL_CONTRACT)
