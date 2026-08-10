"""Tests for the supported Python source-adapter API."""

from __future__ import annotations

import inspect
import json
import textwrap
import types
from pathlib import Path
from typing import get_type_hints

import pytest

import llm_wiki_cli.api as api
from llm_wiki_cli.services import contracts as service_contracts
from llm_wiki_cli.services import mcp_server, plugins
from llm_wiki_cli.api import (
    EXTRACT_SCHEMA_VERSION,
    ExtractionError,
    LlmWikiApiError,
    PathPolicyError,
    build_context,
    build_documentation_query_service,
    callees,
    callers,
    data_flow_for_entrypoint,
    dependency_neighborhood,
    extract_source,
    flow_for_entrypoint,
    list_wiki_pages,
    pages_for_symbol,
)
from llm_wiki_cli.services.knowledge_artifacts import (
    build_knowledge_commit_plan,
    commit_knowledge_artifacts,
)
from llm_wiki_cli.services.knowledge_consumption import build_knowledge_read_view
from llm_wiki_cli.services.knowledge_governance import (
    ALIAS_LOCATOR,
    ALIAS_NATURAL_KEY,
    GovernanceActor,
    GovernanceLedger,
    add_alias,
    add_review_event,
    apply_governance_projection,
    concept_references_from_knowledge,
    current_review_evidence,
    reconcile_concepts,
    save_governance,
    set_lifecycle,
)
from llm_wiki_cli.services.knowledge_loader import (
    KnowledgeLoadResult,
    load_knowledge_state,
)
from llm_wiki_cli.services.knowledge_model import (
    KnowledgeLoadState,
    parse_knowledge_index,
    serialize_knowledge_index,
)
from llm_wiki_cli.services.source_selection import (
    SOURCE_SELECTION_SCHEMA_VERSION,
    resolve_source_selection,
    with_source_selection_generation_input,
)
from llm_wiki_cli.services.source_snapshot import build_source_snapshot
from llm_wiki_cli.services.sync_manifest import SyncManifest
from llm_wiki_cli.services.verification_contracts import (
    ARTIFACT_INTEGRITY_CHECKER_ID,
    build_artifact_verification_context,
    verify_and_write_receipt,
)
from tests.knowledge_fixtures import (
    fail_if_extraction_runs,
    fixture_hash,
    materialize_fixture_tree,
    one_module_two_entities_fixture,
)
from tests.test_knowledge_artifacts import _plan as _knowledge_commit_plan
from tests.test_knowledge_compatibility import (
    COMPATIBILITY_CASES,
    _materialize_case,
)


def test_supported_api_exports_are_additive_contract():
    expected_exports = {
        "BOOTSTRAP_SUMMARY_SCHEMA_VERSION",
        "CONTEXT_KNOWLEDGE_PROTOCOL_VERSION",
        "DOCUMENTATION_AGENT_PACKET_SCHEMA_VERSION",
        "DOCUMENTATION_AGENT_RESULT_SCHEMA_VERSION",
        "DOCUMENTATION_FINAL_REPORT_SCHEMA_VERSION",
        "DOCUMENTATION_MODEL_ROUTING_SCHEMA_VERSION",
        "DOCUMENTATION_MODEL_SELECTION_SCHEMA_VERSION",
        "DOCUMENTATION_RUN_SCHEMA_VERSION",
        "DOCUMENTATION_VERIFICATION_SCHEMA_VERSION",
        "DOCTOR_SCHEMA_VERSION",
        "EXTRACT_SCHEMA_VERSION",
        "P0_CALIBRATION_AGENT_PACKET_SCHEMA_VERSION",
        "P0_CALIBRATION_AGENT_RESULT_SCHEMA_VERSION",
        "P0_CALIBRATION_DECISION_SCOPE",
        "P0_CALIBRATION_DISPATCH_RECEIPT_SCHEMA_VERSION",
        "P0_CALIBRATION_RUN_SCHEMA_VERSION",
        "P0_CALIBRATION_VERIFICATION_REPORT_SCHEMA_VERSION",
        "QUALIFIED_CONTEXT_PACKET_KNOWLEDGE_SCHEMA_VERSION",
        "QUALIFIED_CONTEXT_PACKET_SCHEMA_VERSION",
        "ContextBasisComparison",
        "ContextPacketError",
        "ContextPacketMalformedError",
        "ContextPacketPathPolicyError",
        "ContextPacketReconciliation",
        "ContextPacketSourceMutationError",
        "ContextPacketUnavailableError",
        "ContextPacketValidation",
        "DocumentationGraphQueryService",
        "DocumentationAgentPacket",
        "DocumentationAgentResult",
        "DocumentationModelRoutingPolicy",
        "DocumentationModelRoutingRequest",
        "DocumentationModelSelection",
        "DocumentationQueryResult",
        "DocumentationRun",
        "DocumentationRunStatus",
        "DocumentationVerificationReport",
        "DocumentationWikiSnapshot",
        "DoctorResult",
        "ExtractionError",
        "HostBrokerAuthenticationError",
        "HostBrokerAuthenticationProof",
        "HostBrokerAuthenticationUnavailable",
        "HostBrokerAuthenticator",
        "KnowledgeMode",
        "LlmWikiApiError",
        "P0CalibrationAgentPacket",
        "P0CalibrationAgentResult",
        "P0CalibrationDispatchReceipt",
        "P0CalibrationError",
        "P0CalibrationIntegrityError",
        "P0CalibrationRecoveryError",
        "P0CalibrationRun",
        "P0CalibrationSchemaError",
        "P0CalibrationStatus",
        "P0CalibrationTransitionError",
        "P0CalibrationVerificationReport",
        "PathPolicyError",
        "QualifiedContextPacket",
        "admit_calibration_run",
        "admit_p0_calibration_run",
        "adopt_documentation_wiki_snapshot",
        "build_calibration_agent_packet",
        "build_p0_calibration_agent_packet",
        "build_documentation_agent_packet",
        "build_context",
        "build_qualified_context",
        "build_documentation_query_service",
        "callees",
        "callers",
        "compare_context_packet_basis",
        "data_flow_for_entrypoint",
        "dependency_neighborhood",
        "dispatch_calibration_agent",
        "dispatch_p0_calibration_agent",
        "doctor",
        "export_documentation_run",
        "extract_source",
        "explain_evidence",
        "flow_for_entrypoint",
        "fingerprint_documentation_wiki_input",
        "get_calibration_run_status",
        "get_concept",
        "get_documentation_run_status",
        "get_p0_calibration_run_status",
        "list_concept_sections",
        "list_wiki_pages",
        "pages_for_symbol",
        "prepare_calibration_run",
        "prepare_documentation_run",
        "prepare_p0_calibration_run",
        "query_documentation",
        "record_calibration_agent_result",
        "record_documentation_agent_result",
        "record_p0_calibration_agent_result",
        "reconcile_context_packet",
        "related_concepts",
        "select_documentation_model",
        "traverse_typed_graph",
        "use_calibration_host_broker_authenticator",
        "use_p0_calibration_host_broker_authenticator",
        "validate_context_packet",
        "verify_calibration_run",
        "verify_documentation_run",
        "verify_p0_calibration_run",
    }

    assert expected_exports <= set(api.__all__)
    assert len(api.__all__) == len(set(api.__all__))
    assert (
        api.CONTEXT_KNOWLEDGE_PROTOCOL_VERSION
        == service_contracts.CONTEXT_KNOWLEDGE_PROTOCOL_VERSION
        == "llm-wiki-context/v2"
    )
    assert (
        api.QUALIFIED_CONTEXT_PACKET_KNOWLEDGE_SCHEMA_VERSION
        == service_contracts.QUALIFIED_CONTEXT_PACKET_KNOWLEDGE_SCHEMA_VERSION
        == "llm-wiki-qualified-context-packet/v2"
    )
    assert api.CONTEXT_KNOWLEDGE_PROTOCOL_VERSION in service_contracts.PROTOCOL_VERSIONS
    assert (
        api.QUALIFIED_CONTEXT_PACKET_KNOWLEDGE_SCHEMA_VERSION
        in service_contracts.PROTOCOL_VERSIONS
    )


def test_supported_api_signatures_preserve_existing_callers():
    extract_params = inspect.signature(extract_source).parameters
    context_params = inspect.signature(build_context).parameters

    assert list(extract_params) == [
        "src_dir",
        "changed",
        "summary",
        "deep",
        "paths",
        "package",
        "include_empty",
        "allow_external_src",
        "read_only",
        "source_selection",
    ]
    assert extract_params["src_dir"].default == "."
    assert extract_params["changed"].kind is inspect.Parameter.KEYWORD_ONLY
    assert extract_params["read_only"].default is True

    assert list(context_params) == [
        "src_dir",
        "budget",
        "format",
        "focus",
        "filters",
        "wiki_dir",
        "prefer_fresh",
        "allow_external_src",
        "read_only",
        "source_selection",
        "knowledge_mode",
    ]
    assert context_params["src_dir"].default == "."
    assert context_params["budget"].default == 32000
    assert context_params["filters"].default is None
    assert context_params["wiki_dir"].kind is inspect.Parameter.KEYWORD_ONLY
    assert get_type_hints(build_context)["knowledge_mode"] == api.KnowledgeMode | None
    assert (
        get_type_hints(api.build_qualified_context)["knowledge_mode"]
        == api.KnowledgeMode | None
    )


def test_knowledge_api_signatures_are_explicit_and_builder_stays_compatible():
    builder_params = inspect.signature(build_documentation_query_service).parameters
    assert list(builder_params) == [
        "src_dir",
        "wiki_dir",
        "limit",
        "allow_external_src",
        "read_only",
        "source_selection",
    ]
    assert builder_params["src_dir"].default == "."
    assert builder_params["wiki_dir"].kind is inspect.Parameter.KEYWORD_ONLY
    assert builder_params["limit"].default == 20
    assert builder_params["read_only"].default is True

    common = [
        "locator_or_exact_route",
        "service",
        "src_dir",
        "wiki_dir",
        "limit",
        "allow_external_src",
        "read_only",
        "source_selection",
    ]
    assert list(inspect.signature(api.get_concept).parameters) == common
    assert list(inspect.signature(api.explain_evidence).parameters) == common
    assert list(inspect.signature(api.list_concept_sections).parameters) == [
        "locator_or_exact_route",
        "ownership",
        "service",
        "src_dir",
        "wiki_dir",
        "limit",
        "allow_external_src",
        "read_only",
        "source_selection",
    ]
    assert list(inspect.signature(api.related_concepts).parameters) == [
        "locator_or_exact_route",
        "direction",
        "kinds",
        "service",
        "src_dir",
        "wiki_dir",
        "limit",
        "allow_external_src",
        "read_only",
        "source_selection",
    ]
    assert list(inspect.signature(api.traverse_typed_graph).parameters) == [
        "locator_or_exact_route",
        "direction",
        "kinds",
        "origins",
        "resolutions",
        "include_evidence",
        "service",
        "src_dir",
        "wiki_dir",
        "limit",
        "allow_external_src",
        "read_only",
        "source_selection",
    ]

    for function in (
        api.get_concept,
        api.list_concept_sections,
        api.related_concepts,
        api.explain_evidence,
    ):
        params = inspect.signature(function).parameters
        assert (
            params["locator_or_exact_route"].kind
            is inspect.Parameter.POSITIONAL_OR_KEYWORD
        )
        assert params["service"].kind is inspect.Parameter.KEYWORD_ONLY
        assert params["service"].default is None
        assert params["limit"].default == 20
        assert params["read_only"].default is True
    related_params = inspect.signature(api.related_concepts).parameters
    assert related_params["direction"].default == "both"
    assert related_params["kinds"].default is None
    assert (
        inspect.signature(api.list_concept_sections).parameters["ownership"].default
        is None
    )


def test_documentation_lifecycle_api_signatures_match_cli_contract():
    prepare_params = inspect.signature(api.prepare_documentation_run).parameters
    assert list(prepare_params) == [
        "workspace",
        "baseline_strategy",
        "source_root",
        "source_selection",
        "input_wiki_root",
        "freshness_policy",
        "site_name",
        "audiences",
        "project_purpose",
        "audience_intent",
        "live_service_url",
        "live_service_access_mode",
        "live_service_observation_allowed",
        "helper_cache_root",
        "capture_root",
        "trust_source_plugins",
        "semantic_budget",
        "adjustment_loop_limit",
        "distribution_format",
        "link_mode",
        "knowledge_mode",
        "knowledge_public_repository_identity",
        "refresh",
    ]
    assert prepare_params["workspace"].kind is inspect.Parameter.POSITIONAL_OR_KEYWORD
    assert prepare_params["baseline_strategy"].kind is inspect.Parameter.KEYWORD_ONLY

    expected = {
        "get_documentation_run_status": ["workspace"],
        "build_documentation_agent_packet": ["workspace", "stage"],
        "record_documentation_agent_result": ["workspace", "result"],
        "verify_documentation_run": ["workspace", "advance"],
        "export_documentation_run": [
            "workspace",
            "build",
            "builder_command",
            "knowledge_mode",
            "knowledge_public_repository_identity",
        ],
    }
    for name, parameters in expected.items():
        assert list(inspect.signature(getattr(api, name)).parameters) == parameters

    exact_signatures = {
        "prepare_documentation_run": (
            "(workspace: 'str | Path', *, baseline_strategy: 'str' = "
            "'bootstrap_source', source_root: 'str | Path | None' = None, "
            "source_selection: 'str | Path | None' = None, "
            "input_wiki_root: 'str | Path | None' = None, freshness_policy: "
            "'str' = 'require-current', site_name: 'str', audiences: "
            "'Iterable[str] | None' = None, project_purpose: 'str | None' = "
            "None, audience_intent: 'Mapping[str, str] | None' = None, "
            "live_service_url: 'str | None' = None, live_service_access_mode: "
            "'str' = 'unspecified', live_service_observation_allowed: 'bool' = "
            "False, helper_cache_root: 'str | Path | None' = None, "
            "capture_root: 'str | Path | None' = None, trust_source_plugins: "
            "'bool' = False, semantic_budget: 'int' = 30, "
            "adjustment_loop_limit: 'int' = 3, distribution_format: 'str' = "
            "'mkdocs', link_mode: 'str' = 'http', knowledge_mode: 'str' = "
            "'off', knowledge_public_repository_identity: 'str | None' = None, "
            "refresh: 'bool' = False) -> "
            "'DocumentationRun'"
        ),
        "get_documentation_run_status": (
            "(workspace: 'str | Path') -> 'DocumentationRunStatus'"
        ),
        "build_documentation_agent_packet": (
            "(workspace: 'str | Path', *, stage: 'str') -> 'DocumentationAgentPacket'"
        ),
        "record_documentation_agent_result": (
            "(workspace: 'str | Path', result: 'DocumentationAgentResult | "
            "Mapping[str, Any]') -> 'DocumentationRun'"
        ),
        "verify_documentation_run": (
            "(workspace: 'str | Path', *, advance: 'bool' = True) -> "
            "'DocumentationVerificationReport'"
        ),
        "export_documentation_run": (
            "(workspace: 'str | Path', *, build: 'bool' = False, "
            "builder_command: 'Iterable[str] | None' = None, knowledge_mode: "
            "'str | None' = None, knowledge_public_repository_identity: "
            "'str | None' = None) -> "
            "'DocumentationExportResult'"
        ),
    }
    for name, expected_signature in exact_signatures.items():
        assert str(inspect.signature(getattr(api, name))) == expected_signature


def test_calibration_lifecycle_api_signatures_are_supported():
    expected = {
        "prepare_calibration_run": [
            "root",
            "control_workspaces",
            "execution_manifest",
        ],
        "admit_calibration_run": [
            "root",
            "authority_grant",
            "broker_attestation",
        ],
        "get_calibration_run_status": ["root"],
        "build_calibration_agent_packet": ["root", "role"],
        "dispatch_calibration_agent": ["root", "role"],
        "record_calibration_agent_result": [
            "root",
            "dispatch_receipt",
            "result",
        ],
        "verify_calibration_run": ["root", "advance"],
    }

    for name, parameters in expected.items():
        signature = inspect.signature(getattr(api, name))
        assert list(signature.parameters) == parameters
        assert signature.parameters["root"].kind is (
            inspect.Parameter.POSITIONAL_OR_KEYWORD
        )
        for parameter in parameters[1:]:
            assert (
                signature.parameters[parameter].kind is inspect.Parameter.KEYWORD_ONLY
            )

    assert (
        inspect.signature(api.admit_calibration_run)
        .parameters["broker_attestation"]
        .default
        is None
    )
    assert (
        inspect.signature(api.verify_calibration_run).parameters["advance"].default
        is True
    )

    exact_signatures = {
        "prepare_calibration_run": (
            "(root: 'str | Path', *, control_workspaces: 'Sequence[str | Path]', "
            "execution_manifest: 'Mapping[str, Any]') -> 'P0CalibrationRun'"
        ),
        "admit_calibration_run": (
            "(root: 'str | Path', *, authority_grant: 'Mapping[str, Any]', "
            "broker_attestation: 'Mapping[str, Any] | None' = None) -> "
            "'P0CalibrationRun'"
        ),
        "get_calibration_run_status": ("(root: 'str | Path') -> 'P0CalibrationStatus'"),
        "build_calibration_agent_packet": (
            "(root: 'str | Path', *, role: 'str') -> 'P0CalibrationAgentPacket'"
        ),
        "dispatch_calibration_agent": (
            "(root: 'str | Path', *, role: 'str') -> 'P0CalibrationDispatchReceipt'"
        ),
        "record_calibration_agent_result": (
            "(root: 'str | Path', *, dispatch_receipt: "
            "'P0CalibrationDispatchReceipt | Mapping[str, Any]', result: "
            "'P0CalibrationAgentResult | Mapping[str, Any]') -> 'P0CalibrationRun'"
        ),
        "verify_calibration_run": (
            "(root: 'str | Path', *, advance: 'bool' = True) -> "
            "'P0CalibrationVerificationReport'"
        ),
        "use_calibration_host_broker_authenticator": (
            "(authenticator: 'HostBrokerAuthenticator') -> 'Iterator[None]'"
        ),
    }
    for name, expected_signature in exact_signatures.items():
        assert str(inspect.signature(getattr(api, name))) == expected_signature


@pytest.mark.parametrize(
    ("legacy_name", "replacement_name"),
    [
        ("prepare_p0_calibration_run", "prepare_calibration_run"),
        ("admit_p0_calibration_run", "admit_calibration_run"),
        ("get_p0_calibration_run_status", "get_calibration_run_status"),
        ("build_p0_calibration_agent_packet", "build_calibration_agent_packet"),
        ("dispatch_p0_calibration_agent", "dispatch_calibration_agent"),
        ("record_p0_calibration_agent_result", "record_calibration_agent_result"),
        ("verify_p0_calibration_run", "verify_calibration_run"),
        (
            "use_p0_calibration_host_broker_authenticator",
            "use_calibration_host_broker_authenticator",
        ),
    ],
)
def test_p0_calibration_api_names_warn_and_delegate(
    legacy_name,
    replacement_name,
):
    legacy = getattr(api, legacy_name)
    replacement = getattr(api, replacement_name)

    assert legacy.__wrapped__ is replacement
    with pytest.warns(DeprecationWarning, match=f"use {replacement_name} instead"):
        with pytest.raises(TypeError):
            legacy()


def test_api_error_types_remain_structured_subclasses():
    assert issubclass(PathPolicyError, LlmWikiApiError)
    assert issubclass(ExtractionError, LlmWikiApiError)
    assert issubclass(api.P0CalibrationSchemaError, api.P0CalibrationError)
    assert issubclass(api.P0CalibrationIntegrityError, api.P0CalibrationError)
    assert issubclass(api.P0CalibrationTransitionError, api.P0CalibrationError)
    assert issubclass(api.P0CalibrationRecoveryError, api.P0CalibrationError)


@pytest.mark.parametrize(
    "case",
    COMPATIBILITY_CASES,
    ids=lambda case: case.id,
)
def test_python_knowledge_api_uses_shared_compatibility_policy(
    tmp_path,
    monkeypatch,
    case,
):
    root = tmp_path / "checkout"
    wiki = root / "docs" / "llm_wiki"
    wiki.mkdir(parents=True)
    fixture = _materialize_case(wiki, case)
    for relative_path, content in fixture.source_files.items():
        source = root / relative_path
        source.parent.mkdir(parents=True, exist_ok=True)
        source.write_text(content, encoding="utf-8")
    monkeypatch.chdir(root)
    service = build_documentation_query_service(
        ".",
        wiki_dir="docs/llm_wiki",
    )

    concept = api.get_concept(
        "llm-wiki://entities/User",
        service=service,
    )
    related = api.related_concepts(
        "llm-wiki://entities/User",
        service=service,
    )
    evidence = api.explain_evidence(
        "llm-wiki://entities/User",
        service=service,
    )

    expected_status = {
        "availability": case.expected_availability.value,
        "reason": case.expected_reason.value,
        "freshness": (
            "evaluated (6 concepts)"
            if case.serves_knowledge
            else "unevaluated (snapshot-only read)"
        ),
        "freshness_evaluated": case.serves_knowledge,
    }
    assert concept["knowledge"] == expected_status
    assert related["knowledge"] == expected_status
    assert evidence["knowledge"] == expected_status
    assert concept["found"] is case.serves_knowledge
    assert related["found"] is case.serves_knowledge
    assert evidence["found"] is case.serves_knowledge
    if case.serves_knowledge:
        assert concept["concept"]["locator"] == "llm-wiki://entities/User"
    else:
        assert concept["concept"] is None
        assert related["relationships"] == []
        assert evidence["evidence"] is None


def _write_query_project(root):
    (root / "api.py").write_text(
        textwrap.dedent(
            """\
            from repo import save

            __all__ = ["run"]

            def run(payload):
                return save(payload)
            """
        ),
        encoding="utf-8",
    )
    (root / "repo.py").write_text(
        textwrap.dedent(
            """\
            def save(payload):
                return payload
            """
        ),
        encoding="utf-8",
    )


def _write_api_wiki(root, rel_path="docs/llm_wiki"):
    wiki = root / rel_path
    for subdir in ["entities", "modules", "workflows", "flows", "infrastructure"]:
        (wiki / subdir).mkdir(parents=True, exist_ok=True)
    (wiki / "index.md").write_text("# Index\n\n", encoding="utf-8")
    (wiki / "log.md").write_text("# Log\n\n", encoding="utf-8")
    (wiki / "modules" / "api.md").write_text(
        "# api Module\n\n**Path:** `api.py`\n", encoding="utf-8"
    )
    (wiki / "modules" / "repo.md").write_text(
        "# repo Module\n\n**Path:** `repo.py`\n", encoding="utf-8"
    )
    (wiki / "flows" / "api-run.md").write_text(
        "# api-run\n\nFlow for run.\n", encoding="utf-8"
    )
    (wiki / "dependencies.md").write_text("# Dependencies\n\n", encoding="utf-8")
    (wiki / "load-order.md").write_text("# Load order\n\n", encoding="utf-8")
    return wiki


def test_extract_source_returns_stable_payload(tmp_project):
    payload = extract_source(".", summary=True, read_only=True)

    assert payload["schema_version"] == EXTRACT_SCHEMA_VERSION
    assert payload["inventory"]
    first = next(iter(payload["inventory"].values()))
    assert "language" in first


def test_extract_source_preserves_haskell_inventory_entries(monkeypatch):
    haskell_entry = {
        "language": "haskell",
        "module": "HLSAnalysis.API",
        "imports": [
            {
                "module": "Data.Text",
                "qualified": False,
                "alias": None,
                "line": 4,
            }
        ],
        "classes": [
            {
                "name": "User",
                "kind": "data",
                "line": 8,
                "deriving": ["Show"],
            }
        ],
        "functions": [
            {
                "name": "loadUser",
                "kind": "signature",
                "signature": "UserId -> Maybe User",
                "line": 18,
            },
            {"name": "loadUser", "kind": "function", "line": 19},
        ],
        "language_pragmas": ["FlexibleInstances"],
        "exports": ["User", "loadUser"],
    }
    payload = {
        "schema_version": EXTRACT_SCHEMA_VERSION,
        "inventory": {"hls-analysis/src/HLSAnalysis/API.hs": haskell_entry},
    }

    def fake_build_extract_payload(src_dir, **kwargs):
        assert src_dir == "source-root"
        assert kwargs["read_only"] is True
        return api.extract_cmd.ExtractPayloadResult(
            payload=payload,
            inventory_count=1,
            docker_count=0,
        )

    monkeypatch.setattr(
        api.extract_cmd, "build_extract_payload", fake_build_extract_payload
    )

    assert extract_source("source-root", read_only=True) == payload


def test_build_context_returns_json_payload(tmp_project):
    payload = build_context(".", budget=100000, focus="all", format="json")

    assert payload["budget"] == 100000
    assert payload["files"]
    assert payload["bounds"]["files"] == {
        "total": len(payload["files"]),
        "returned": len(payload["files"]),
        "truncated": False,
    }


def test_build_context_returns_markdown_content_and_raw_payload(tmp_project):
    payload = build_context(".", budget=100000, focus="all", format="markdown")

    assert "Context Budget" in payload["content"]
    assert payload["payload"]["files"]
    assert payload["payload"]["bounds"]["files"]["returned"] == len(
        payload["payload"]["files"]
    )


def test_build_context_accepts_graph_filters_and_wiki_dir(tmp_project):
    _write_query_project(tmp_project)
    _write_api_wiki(tmp_project, "agent_wiki")

    payload = build_context(
        ".",
        budget=100000,
        focus="all",
        format="json",
        filters={"symbol": "run", "surface": "flows"},
        wiki_dir="agent_wiki",
    )

    assert payload["graphs"]["symbol"]["callees"]["found"] is True
    assert payload["graphs"]["symbol"]["pages"]["pages"]
    assert payload["surface"]["kind"] == "flows"
    assert payload["surface"]["count"] == payload["surface"]["returned"]
    assert payload["surface"]["bounds"]["pages"]["returned"] == len(
        payload["surface"]["pages"]
    )
    assert "files" in payload
    assert [page["canonical_path"] for page in payload["surface"]["pages"]] == [
        "flows/api-run.md"
    ]


def test_build_context_graph_sections_are_optional_additions(tmp_project):
    _write_query_project(tmp_project)
    _write_api_wiki(tmp_project, "agent_wiki")

    plain_payload = build_context(
        ".",
        budget=100000,
        focus="all",
        format="json",
        wiki_dir="agent_wiki",
    )
    enriched_payload = build_context(
        ".",
        budget=100000,
        focus="all",
        format="json",
        filters={"symbol": "run", "entrypoint": "api-run", "surface": "flows"},
        wiki_dir="agent_wiki",
    )

    assert "graphs" not in plain_payload
    assert "surface" not in plain_payload
    assert {"budget", "used", "files"} <= set(enriched_payload)
    assert enriched_payload["graphs"]["entrypoint"]["flow"]["found"] is True
    assert enriched_payload["surface"]["pages"][0]["canonical_path"] == (
        "flows/api-run.md"
    )


def test_build_context_passes_knowledge_refinements_and_preserves_results(
    monkeypatch,
):
    refinements = {
        "surface": "entities",
        "freshness": "source-changed",
        "evidence": "present",
    }
    knowledge_status = {
        "availability": "ready",
        "reason": "all-projection-commitments-match",
        "freshness": "evaluated (1 concepts)",
        "freshness_evaluated": True,
    }
    seen = {}

    def fake_build_context(
        src_dir,
        budget,
        fmt,
        focus,
        filters,
        **kwargs,
    ):
        seen.update(
            {
                "src_dir": src_dir,
                "budget": budget,
                "format": fmt,
                "focus": focus,
                "filters": filters,
                "wiki_dir": kwargs["wiki_dir"],
            }
        )
        return (
            {
                "budget": budget,
                "used": 0,
                "files": {},
                "knowledge": knowledge_status,
                "surface": {
                    "kind": "entities",
                    "count": 1,
                    "total": 1,
                    "truncated": False,
                    "knowledge_selection": {
                        "unfiltered_total": 2,
                        "filtered_total": 1,
                        "returned": 1,
                        "truncated": False,
                    },
                    "pages": [
                        {
                            "canonical_path": "entities/User.md",
                            "mcp_uri": "llm-wiki://entities/User",
                            "knowledge": {
                                **knowledge_status,
                                "freshness_disclosure": knowledge_status["freshness"],
                                "evidence": "present",
                                "freshness": {
                                    "state": "source-changed",
                                    "reason": "concept-observation-changed",
                                    "live_comparison_performed": True,
                                },
                            },
                        }
                    ],
                },
            },
            ["Knowledge context includes stale concept references."],
        )

    monkeypatch.setattr(api.context_cmd, "_build_context", fake_build_context)

    result = build_context(
        "source-root",
        budget=4096,
        focus="all",
        format="json",
        filters=refinements,
        wiki_dir="agent_wiki",
    )

    assert seen == {
        "src_dir": "source-root",
        "budget": 4096,
        "format": "json",
        "focus": ["all"],
        "filters": refinements,
        "wiki_dir": "agent_wiki",
    }
    assert result["knowledge"] == knowledge_status
    assert result["surface"]["knowledge_selection"]["unfiltered_total"] == 2
    assert result["surface"]["knowledge_selection"]["filtered_total"] == 1
    assert result["surface"]["pages"][0]["knowledge"]["freshness"]["state"] == (
        "source-changed"
    )
    assert result["warnings"] == [
        "Knowledge context includes stale concept references."
    ]
    assert api.context_cmd.PROTOCOL_VERSION == "llm-wiki-context/v1"


def test_build_context_preserves_compact_typed_relationship_selection(
    monkeypatch,
):
    refinements = {
        "surface": "entities",
        "relationship_kind": "calls",
        "relationship_origin": "extracted",
        "relationship_resolution": "resolved",
        "relationship_direction": "incoming",
    }
    graph_status = {
        "availability": "ready",
        "reason": "typed-graph-extension-ready",
        "coverage": [],
    }
    graph_selection = {
        **graph_status,
        "found": True,
        "direction": "incoming",
        "filters": {
            key: value
            for key, value in refinements.items()
            if key.startswith("relationship_")
        },
        "unfiltered_total": 4,
        "filtered_total": 2,
        "returned": 2,
        "truncated": False,
        "coverage": {
            "scope": "returned-edges",
            "edges": 2,
            "observed": 2,
            "emitted": 2,
            "omitted": 0,
            "truncated": False,
            "limitations": [],
        },
    }
    seen = {}

    def fake_build_context(
        _src_dir,
        budget,
        _fmt,
        _focus,
        filters,
        **_kwargs,
    ):
        seen["filters"] = filters
        return (
            {
                "budget": budget,
                "used": 0,
                "files": {},
                "typed_graph": graph_status,
                "surface": {
                    "kind": "entities",
                    "count": 1,
                    "pages": [
                        {
                            "canonical_path": "entities/User.md",
                            "typed_graph": graph_selection,
                        }
                    ],
                },
            },
            [],
        )

    monkeypatch.setattr(api.context_cmd, "_build_context", fake_build_context)

    result = build_context(
        ".",
        focus="all",
        filters=refinements,
    )

    assert seen["filters"] == refinements
    assert result["typed_graph"] == graph_status
    assert result["surface"]["pages"][0]["typed_graph"] == graph_selection
    encoded = json.dumps(result, sort_keys=True)
    assert "samples" not in encoded
    assert "aggregate_input_hash" not in encoded


@pytest.mark.parametrize(
    ("filters", "field"),
    [
        ({"freshness": "current"}, "freshness"),
        ({"evidence": "present"}, "evidence"),
    ],
)
def test_build_context_maps_knowledge_refinement_dependency_errors(filters, field):
    with pytest.raises(
        LlmWikiApiError,
        match=rf"filters\.{field} requires filters\.surface or filters\.symbol",
    ):
        build_context(".", filters=filters)


@pytest.mark.parametrize(
    ("options", "field"),
    [
        ({"focus": []}, "focus"),
        ({"filters": []}, "filters"),
    ],
)
def test_build_context_rejects_explicit_invalid_empty_collections(options, field):
    with pytest.raises(api.InvalidRequestError) as exc_info:
        build_context(".", **options)

    assert exc_info.value.code == "invalid-request"
    assert exc_info.value.details == {"field": field}


def test_build_context_markdown_preserves_knowledge_status_and_warnings(
    monkeypatch,
):
    status = {
        "availability": "degraded",
        "reason": "policy-selected-surface-only-fallback-after-invalid",
        "freshness": "unevaluated (snapshot-only read)",
        "freshness_evaluated": False,
    }

    def fake_build_context(_src_dir, budget, _fmt, _focus, _filters, **_kwargs):
        return (
            {
                "budget": budget,
                "used": 0,
                "files": {},
                "knowledge": status,
            },
            ["Knowledge context is degraded; no candidates were dropped."],
        )

    monkeypatch.setattr(api.context_cmd, "_build_context", fake_build_context)

    result = build_context(
        ".",
        format="markdown",
        filters={"surface": "entities"},
    )

    assert result["payload"]["knowledge"] == status
    assert result["warnings"] == [
        "Knowledge context is degraded; no candidates were dropped."
    ]
    assert "## Knowledge" in result["content"]
    assert "- availability: degraded" in result["content"]
    assert "- freshness: unevaluated (snapshot-only read)" in result["content"]


def test_build_context_legacy_json_shape_remains_context_v1(monkeypatch):
    legacy_payload = {
        "budget": 1000,
        "used": 0,
        "truncated": False,
        "omitted_files": [],
        "downgraded_files": {},
        "files": {},
    }

    seen = {}

    def fake_build_context(*_args, **kwargs):
        seen.update(kwargs)
        return dict(legacy_payload), []

    monkeypatch.setattr(api.context_cmd, "_build_context", fake_build_context)

    result = build_context(".", budget=1000, focus="all")

    assert result == legacy_payload
    assert "knowledge" not in result
    assert api.context_cmd.PROTOCOL_VERSION == "llm-wiki-context/v1"
    assert seen["include_plugins"] is True
    assert seen["knowledge_mode"] is None


def test_query_filter_iterable_consumption_is_bounded():
    class InfiniteKinds:
        def __init__(self):
            self.pulls = 0

        def __iter__(self):
            return self

        def __next__(self):
            self.pulls += 1
            return "derived_from"

    kinds = InfiniteKinds()

    with pytest.raises(api.InvalidRequestError) as exc_info:
        api.related_concepts(
            "llm-wiki://entities/User",
            kinds=kinds,
            service=object(),
        )

    assert kinds.pulls == api.MAX_QUERY_FILTER_VALUES + 1
    assert exc_info.value.code == "invalid-request"
    assert exc_info.value.details == {"field": "kinds"}
    assert f"at most {api.MAX_QUERY_FILTER_VALUES} values" in str(exc_info.value)


def test_query_filter_iteration_failure_is_a_stable_invalid_request():
    class BrokenKinds:
        def __iter__(self):
            return self

        def __next__(self):
            raise RuntimeError("iterator implementation leaked")

    with pytest.raises(api.InvalidRequestError) as exc_info:
        api.related_concepts(
            "llm-wiki://entities/User",
            kinds=BrokenKinds(),
            service=object(),
        )

    assert exc_info.value.code == "invalid-request"
    assert exc_info.value.details == {"field": "kinds"}
    assert "could not be read as an iterable" in str(exc_info.value)


def test_build_context_forwards_opt_in_freshness_policy(monkeypatch):
    seen = {}

    def fake_build_context(
        _src_dir,
        budget,
        _format,
        _focus,
        _filters,
        **kwargs,
    ):
        seen.update(kwargs)
        return (
            {
                "budget": budget,
                "used": 0,
                "truncated": False,
                "omitted_files": [],
                "downgraded_files": {},
                "bounds": {
                    "files": {
                        "total": 0,
                        "returned": 0,
                        "truncated": False,
                    }
                },
                "files": {},
                "ranking_policy": {
                    "name": "relevance-then-current-freshness",
                    "prefer_fresh": True,
                },
            },
            [],
        )

    monkeypatch.setattr(api.context_cmd, "_build_context", fake_build_context)

    result = api.build_context(".", prefer_fresh=True)

    assert seen["prefer_fresh"] is True
    assert result["ranking_policy"]["prefer_fresh"] is True


def test_qualified_context_api_build_validate_and_reconcile_are_typed(
    monkeypatch,
):
    packet_payload = {
        "schema_version": "llm-wiki-qualified-context-packet/v1",
        "packet_id": "sha256:" + "a" * 64,
        "assurance": {},
        "request": {},
        "response": {},
        "basis": {},
        "delivery": {},
        "path_policy": {},
    }
    seen = {}

    packet = types.SimpleNamespace(
        packet_id=packet_payload["packet_id"],
        to_payload=lambda: dict(packet_payload),
        to_bytes=lambda: b"packet\n",
    )

    def fake_build(src_dir, wiki_dir, request, **kwargs):
        seen.update(
            {
                "src_dir": src_dir,
                "wiki_dir": wiki_dir,
                "request": request,
                **kwargs,
            }
        )
        return packet

    validation = types.SimpleNamespace(
        valid=True,
        packet_id=packet_payload["packet_id"],
    )
    comparison = types.SimpleNamespace(
        packet_id=packet_payload["packet_id"],
        matches_expected=True,
        current=None,
    )
    reconciliation = types.SimpleNamespace(
        packet_id=packet_payload["packet_id"],
        state="current",
        current=True,
    )
    monkeypatch.setattr(
        api.context_packet_service,
        "build_qualified_context",
        fake_build,
    )
    monkeypatch.setattr(
        api.context_packet_service,
        "validate_context_packet",
        lambda _raw: validation,
    )
    monkeypatch.setattr(
        api.context_packet_service,
        "compare_context_packet_basis",
        lambda _raw, _basis: comparison,
    )
    monkeypatch.setattr(
        api.context_packet_service,
        "reconcile_context_packet",
        lambda *_args, **_kwargs: reconciliation,
    )

    request = {
        "budget_tokens": 2048,
        "focus": ["all"],
        "format": "json",
        "filters": {},
        "prefer_fresh": True,
    }
    built = api.build_qualified_context(
        "src",
        "agent_wiki",
        request,
    )
    validated = api.validate_context_packet(b"packet\n")
    compared = api.compare_context_packet_basis(
        b"packet\n",
        {"source_snapshot": {}},
    )
    reconciled = api.reconcile_context_packet(
        b"packet\n",
        "src",
        wiki_dir="agent_wiki",
    )

    assert built is packet
    assert validated is validation
    assert compared is comparison
    assert reconciled is reconciliation
    assert seen["request"] is request
    assert seen["read_only"] is True


def test_list_wiki_pages_returns_registry_metadata_without_running_extraction(
    tmp_project, monkeypatch
):
    wiki = _write_api_wiki(tmp_project)
    (wiki / "guides").mkdir()
    (wiki / "guides" / "operator-onboarding.md").write_text(
        "# Operator Onboarding\n\n", encoding="utf-8"
    )

    def fail_if_extracted(*args, **kwargs):  # pragma: no cover - assertion helper
        raise AssertionError("list_wiki_pages must not run source extraction")

    monkeypatch.setattr(api.extract_cmd, "build_extract_payload", fail_if_extracted)

    payload = list_wiki_pages("docs/llm_wiki")

    assert payload["wiki_dir"] == "docs/llm_wiki"
    assert payload["counts"]["by_kind"]["index"] == 1
    assert payload["counts"]["by_kind"]["modules"] == 2
    assert payload["counts"]["by_kind"]["guides"] == 1
    assert payload["counts"]["by_kind"]["flows"] == 1
    assert payload["counts"]["architecture_pages"] == 2
    assert {
        (page["kind"], page["id"], page["canonical_path"], page["mcp_uri"])
        for page in payload["pages"]
    } >= {
        ("index", "index", "index.md", "llm-wiki://index"),
        ("modules", "api", "modules/api.md", "llm-wiki://modules/api"),
        (
            "guides",
            "operator-onboarding",
            "guides/operator-onboarding.md",
            "llm-wiki://guides/operator-onboarding",
        ),
        ("flows", "api-run", "flows/api-run.md", "llm-wiki://flows/api-run"),
        ("dependencies", "dependencies", "dependencies.md", "llm-wiki://dependencies"),
    }


def test_list_wiki_pages_exposes_api_contract_root_surface(tmp_project, monkeypatch):
    wiki = _write_api_wiki(tmp_project)
    (wiki / "api-contracts.md").write_text(
        "# API contracts\n\n## Notes\n\nReviewed.\n", encoding="utf-8"
    )

    def fail_if_extracted(*args, **kwargs):  # pragma: no cover - assertion helper
        raise AssertionError("list_wiki_pages must not run source extraction")

    monkeypatch.setattr(api.extract_cmd, "build_extract_payload", fail_if_extracted)

    payload = list_wiki_pages("docs/llm_wiki")

    assert payload["counts"]["by_kind"]["api-contracts"] == 1
    assert payload["counts"]["architecture_pages"] == 3
    page = next(item for item in payload["pages"] if item["kind"] == "api-contracts")
    assert page["canonical_path"] == "api-contracts.md"
    assert page["mcp_uri"] == "llm-wiki://api-contracts"


def test_query_service_builder_reuses_one_inventory_snapshot_surface_and_view(
    tmp_project,
    monkeypatch,
):
    wiki = _write_api_wiki(tmp_project)
    inventory = {
        "api.py": {
            "language": "python",
            "classes": [],
            "functions": [],
            "imports": [],
        }
    }
    source_snapshot = object()
    retained_inventory = api.extract_cmd.InventoryResult(
        inventory=inventory,
        statuses={},
        source_snapshot=source_snapshot,
    )
    extract_result = api.extract_cmd.ExtractPayloadResult(
        payload={
            "inventory": inventory,
            "entrypoints": [],
            "data_flows": [],
        },
        inventory_count=1,
        docker_count=0,
        inventory_result=retained_inventory,
    )
    surface_payload = {"schema_version": "surface-fixture", "pages": []}
    surface_evaluation = types.SimpleNamespace(payload=surface_payload)
    knowledge_view = object()
    machine_verification = {}
    query_surface = {"schema_version": "query-surface", "pages": []}
    dependency_analysis = {"graph": {"nodes": [], "edges": []}}
    call_edges = []
    built_service = object()
    calls = {
        "extract": 0,
        "surface": 0,
        "view": 0,
        "query_surface": 0,
        "dependencies": 0,
        "service": 0,
    }

    def fake_extract(src_dir, **kwargs):
        calls["extract"] += 1
        assert src_dir == str(tmp_project.resolve())
        guarded_snapshot = kwargs.pop("source_snapshot")
        assert guarded_snapshot.root == tmp_project.resolve()
        assert kwargs == {
            "deep": True,
            "allow_external_src": True,
            "read_only": True,
            "include_plugins": False,
        }
        return extract_result

    def fake_surface(wiki_root, selected_inventory, **kwargs):
        calls["surface"] += 1
        assert wiki_root == wiki.resolve()
        assert selected_inventory is inventory
        assert kwargs == {
            "src_dir": tmp_project.resolve(),
            "entry_points": [],
        }
        return surface_evaluation

    def fake_view(wiki_root, evaluation, selected_inventory, inventory_result):
        calls["view"] += 1
        assert wiki_root == wiki.resolve()
        assert evaluation is surface_evaluation
        assert selected_inventory is inventory
        assert inventory_result is retained_inventory
        return knowledge_view

    def fake_query_surface(payload, view):
        calls["query_surface"] += 1
        assert payload is surface_payload
        assert view is knowledge_view
        return query_surface

    def fake_dependencies(
        selected_inventory,
        src_root,
        *,
        source_snapshot,
    ):
        calls["dependencies"] += 1
        assert selected_inventory is inventory
        assert src_root == str(tmp_project.resolve())
        assert source_snapshot is retained_inventory.source_snapshot
        return dependency_analysis

    def fake_service(selected_inventory, **kwargs):
        calls["service"] += 1
        assert selected_inventory is inventory
        assert kwargs["call_edges"] is call_edges
        assert kwargs["flows"] == []
        assert kwargs["data_flows"] == []
        assert kwargs["dependency_analysis"] is dependency_analysis
        assert kwargs["surface_index"] is query_surface
        assert kwargs["knowledge_view"] is knowledge_view
        assert kwargs["machine_verification"] == machine_verification
        assert kwargs["limit"] == 7
        return built_service

    monkeypatch.setattr(
        api.extract_cmd,
        "build_extract_payload",
        fake_extract,
    )
    monkeypatch.setattr(
        api.extract_cmd,
        "resolve_call_edges",
        lambda selected_inventory: (
            call_edges
            if selected_inventory is inventory
            else pytest.fail("builder replaced the retained inventory")
        ),
    )
    monkeypatch.setattr(api, "evaluate_surface_index", fake_surface)
    monkeypatch.setattr(
        api.context_cmd,
        "_build_context_knowledge_view",
        fake_view,
    )
    monkeypatch.setattr(
        api.context_cmd,
        "_context_query_surface",
        fake_query_surface,
    )
    monkeypatch.setattr(api, "analyze_dependencies", fake_dependencies)
    monkeypatch.setattr(api, "DocumentationGraphQueryService", fake_service)

    result = build_documentation_query_service(
        ".",
        wiki_dir="docs/llm_wiki",
        limit=7,
        read_only=True,
    )

    assert result is built_service
    assert calls == {
        "extract": 1,
        "surface": 1,
        "view": 1,
        "query_surface": 1,
        "dependencies": 1,
        "service": 1,
    }


def test_query_service_builder_exposes_committed_knowledge_end_to_end(
    tmp_path,
    monkeypatch,
):
    fixture = one_module_two_entities_fixture()
    tree = materialize_fixture_tree(
        fixture,
        tmp_path / "checkout",
        consumer="api",
    )
    commit_knowledge_artifacts(_knowledge_commit_plan(tree["wiki_root"], fixture))
    monkeypatch.chdir(tree["root"])

    service = build_documentation_query_service(
        ".",
        wiki_dir="docs/llm_wiki",
    )
    result = api.get_concept(
        "llm-wiki://entities/User",
        service=service,
    )

    assert result["knowledge"] == {
        "availability": "ready",
        "reason": "all-projection-commitments-match",
        "freshness": "evaluated (6 concepts)",
        "freshness_evaluated": True,
    }
    assert result["found"] is True
    assert result["concept"]["locator"] == "llm-wiki://entities/User"
    assert result["concept"]["freshness"]["state"] == "current"


def test_query_service_rejects_stale_persisted_selection_before_wiki_reads(
    tmp_project,
    monkeypatch,
):
    def write_profile(path: Path, include: str) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(
                {
                    "schema_version": SOURCE_SELECTION_SCHEMA_VERSION,
                    "include": [include],
                    "exclude": [],
                }
            ),
            encoding="utf-8",
        )

    Path("selected-a").mkdir()
    Path("selected-b").mkdir()
    Path("selected-a/app.py").write_text("VALUE = 1\n", encoding="utf-8")
    Path("selected-b/app.py").write_text("VALUE = 2\n", encoding="utf-8")
    profile_a = Path("config/a.json")
    profile_b = Path("config/b.json")
    write_profile(profile_a, "selected-a")
    write_profile(profile_b, "selected-b")
    policy_a = resolve_source_selection(".", profile_a.as_posix())
    assert policy_a is not None
    snapshot_a = build_source_snapshot(".", selection_policy=policy_a)
    wiki = Path("docs/llm_wiki")
    wiki.mkdir(parents=True)
    SyncManifest(
        generation_inputs=with_source_selection_generation_input(
            {},
            snapshot_a.source_selection_identity,
            snapshot_a.source_selection_inputs,
        )
    ).save(wiki)
    monkeypatch.setattr(
        api,
        "evaluate_surface_index",
        lambda *_args, **_kwargs: pytest.fail(
            "persisted wiki surfaces must not be read after a selection mismatch"
        ),
    )

    with pytest.raises(api.InvalidRequestError, match="llm-wiki sync"):
        build_documentation_query_service(
            ".",
            wiki_dir=wiki.as_posix(),
            source_selection=profile_b.as_posix(),
        )


def test_query_service_rejects_omitted_explicit_profile_before_extraction(
    tmp_project,
    monkeypatch,
):
    Path("selected").mkdir()
    Path("selected/app.py").write_text("VALUE = 1\n", encoding="utf-8")
    profile = Path("config/explicit.json")
    profile.parent.mkdir()
    profile.write_text(
        json.dumps(
            {
                "schema_version": SOURCE_SELECTION_SCHEMA_VERSION,
                "include": ["selected"],
                "exclude": [],
            }
        ),
        encoding="utf-8",
    )
    policy = resolve_source_selection(".", profile.as_posix())
    assert policy is not None
    snapshot = build_source_snapshot(".", selection_policy=policy)
    wiki = Path("docs/llm_wiki")
    wiki.mkdir(parents=True)
    SyncManifest(
        generation_inputs=with_source_selection_generation_input(
            {},
            snapshot.source_selection_identity,
            snapshot.source_selection_inputs,
        )
    ).save(wiki)
    monkeypatch.setattr(
        api.extract_cmd,
        "build_extract_payload",
        lambda *_args, **_kwargs: pytest.fail(
            "persisted profile omission must fail before extraction or plugins"
        ),
    )

    with pytest.raises(api.InvalidRequestError, match="--source-selection"):
        build_documentation_query_service(".", wiki_dir=wiki.as_posix())


def test_context_rejects_truncated_manifest_before_broad_extraction(
    tmp_project,
    monkeypatch,
):
    Path("secret.py").write_text("MUST_NOT_READ = True\n", encoding="utf-8")
    wiki = Path("docs/llm_wiki")
    wiki.mkdir(parents=True)
    (wiki / ".llm-wiki-manifest.json").write_text(
        '{"generation_inputs":{"source_selection":{"schema_version":'
        '"llm-wiki-source-selection-identity/v1"',
        encoding="utf-8",
    )
    monkeypatch.setattr(
        api.context_cmd,
        "get_inventory",
        lambda *_args, **_kwargs: pytest.fail(
            "an invalid managed manifest must fail before broad extraction"
        ),
    )

    with pytest.raises(api.InvalidRequestError, match="sync manifest is invalid"):
        build_context(".", focus="all", wiki_dir=wiki.as_posix())


@pytest.mark.parametrize("operation", ["extract", "context"])
def test_configured_external_api_does_not_execute_source_plugins(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    operation: str,
) -> None:
    host = tmp_path / "host"
    host.mkdir()
    source = tmp_path / "external-source"
    selected = source / "selected"
    selected.mkdir(parents=True)
    (selected / "tasks.py").write_text("def run():\n    return 1\n", encoding="utf-8")
    profile = source / "config" / "sources.json"
    profile.parent.mkdir()
    profile.write_text(
        json.dumps(
            {
                "schema_version": SOURCE_SELECTION_SCHEMA_VERSION,
                "include": ["selected"],
                "exclude": [],
            }
        ),
        encoding="utf-8",
    )
    plugin_dir = source / "vendor" / "external-detector"
    plugin_dir.mkdir(parents=True)
    module_name = "external_api_detector"
    marker = source / "SOURCE_PLUGIN_EXECUTED"
    (plugin_dir / plugins.MANIFEST_FILENAME).write_text(
        json.dumps(
            {
                "id": "external-api-detector",
                "version": "1.0.0",
                "llm_wiki_version": "*",
                "components": [
                    {
                        "type": "entrypoint_detector",
                        "id": "detector",
                        "entry_point": f"{module_name}:detect",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    (plugin_dir / f"{module_name}.py").write_text(
        "from pathlib import Path\n"
        f"Path({str(marker)!r}).write_text('executed')\n"
        "def detect(inventory):\n"
        "    return []\n",
        encoding="utf-8",
    )
    plugins.install_plugin(str(plugin_dir), root=source, yes=True)
    monkeypatch.chdir(host)

    if operation == "extract":
        extract_source(
            str(source),
            deep=True,
            allow_external_src=True,
            source_selection="config/sources.json",
        )
    else:
        wiki = host / "wiki"
        wiki.mkdir()
        build_context(
            str(source),
            focus="all",
            wiki_dir="wiki",
            allow_external_src=True,
            source_selection="config/sources.json",
        )

    assert not marker.exists()


def test_governed_api_and_mcp_concept_summaries_have_bounded_parity(
    tmp_path,
    monkeypatch,
):
    fixture = one_module_two_entities_fixture()
    tree = materialize_fixture_tree(
        fixture,
        tmp_path / "checkout",
        consumer="api",
    )
    base_plan = _knowledge_commit_plan(tree["wiki_root"], fixture)
    knowledge = parse_knowledge_index(json.loads(base_plan.knowledge_index.content))
    ledger = reconcile_concepts(
        GovernanceLedger.empty("kb_consumer-parity"),
        concept_references_from_knowledge(knowledge),
    )
    user_uid = next(
        uid
        for uid, allocation in ledger.concepts.items()
        if allocation.locator == "llm-wiki://entities/User"
    )
    successor_uid = next(
        uid
        for uid, allocation in ledger.concepts.items()
        if allocation.locator == "llm-wiki://entities/AccountService"
    )
    ledger = add_alias(
        ledger,
        user_uid,
        ALIAS_LOCATOR,
        "llm-wiki://entities/LegacyUser",
    )
    ledger = add_alias(
        ledger,
        user_uid,
        ALIAS_NATURAL_KEY,
        "code-entity:entities/LegacyUser.md",
    )
    reviewer = GovernanceActor("human", "reviewer.example")
    ledger = set_lifecycle(
        ledger,
        user_uid,
        "active",
        actor=reviewer,
        authored_at="2026-07-27T10:00:00Z",
    )
    ledger = set_lifecycle(
        ledger,
        user_uid,
        "superseded",
        successor_uid=successor_uid,
        actor=reviewer,
        authored_at="2026-07-27T11:00:00Z",
    )
    user = next(
        concept
        for concept in knowledge.concepts
        if concept.locator == "llm-wiki://entities/User"
    )
    review_evidence = current_review_evidence(user)
    assert review_evidence is not None
    for version, authored_at in (
        ("1", "2026-07-27T11:30:00Z"),
        ("2", "2026-07-27T11:40:00Z"),
    ):
        ledger = add_review_event(
            ledger,
            user_uid,
            section_locator=("llm-wiki://entities/User#section/User~1/Review~1"),
            scope_hash=fixture_hash("consumer-review"),
            evidence=review_evidence,
            reviewer=reviewer,
            method="manual-review",
            method_version=version,
            authored_at=authored_at,
        )

    projected = apply_governance_projection(
        knowledge,
        ledger,
        event_limit=1,
    )
    save_governance(
        tree["wiki_root"],
        ledger,
        expected_hash=None,
    )
    commit_knowledge_artifacts(
        build_knowledge_commit_plan(
            tree["wiki_root"],
            surface_index_bytes=fixture.surface_bytes,
            knowledge_index_bytes=serialize_knowledge_index(projected).encode("utf-8"),
            manifest=base_plan.committed_manifest,
        )
    )
    monkeypatch.chdir(tree["root"])
    mcp = mcp_server.McpWikiService(
        src_dir=".",
        wiki_dir="docs/llm_wiki",
    )

    coordinates = (
        user_uid,
        "llm-wiki://entities/LegacyUser",
        "code-entity:entities/LegacyUser.md",
        "llm-wiki://entities/User",
    )
    concepts = []
    for coordinate in coordinates:
        api_result = api.get_concept(
            coordinate,
            src_dir=".",
            wiki_dir="docs/llm_wiki",
            limit=1,
        )
        mcp_result = mcp.get_concept(coordinate, limit=1)

        assert api_result == mcp_result
        assert api_result["found"] is True
        concepts.append(api_result["concept"])

    assert all(concept == concepts[0] for concept in concepts)
    concept = concepts[0]
    assert concept["uid"] == user_uid
    assert concept["lifecycle"] == "superseded"
    assert concept["successor_uid"] == successor_uid
    assert concept["aliases"] == [
        {
            "type": "locator",
            "value": "llm-wiki://entities/LegacyUser",
        }
    ]
    assert concept["alias_coverage"] == {
        "total": 2,
        "returned": 1,
        "truncated": True,
    }
    assert concept["lifecycle_events"] == {
        "items": [
            {
                "event_id": concept["lifecycle_events"]["items"][0]["event_id"],
                "from": "active",
                "to": "superseded",
                "actor": {"kind": "human", "id": "reviewer.example"},
                "authored_at": "2026-07-27T11:00:00Z",
                "reason": "explicit-lifecycle-change",
                "successor_uid": successor_uid,
            }
        ],
        "total": 2,
        "returned": 1,
        "limit": 1,
        "truncated": True,
    }
    assert concept["reviews"] == {
        "items": [
            {
                "event_id": concept["reviews"]["items"][0]["event_id"],
                "section_locator": ("llm-wiki://entities/User#section/User~1/Review~1"),
                "state": "expired",
                "reasons": ["section-missing"],
                "reviewer": {"kind": "human", "id": "reviewer.example"},
                "method": {"id": "manual-review", "version": "2"},
                "authored_at": "2026-07-27T11:40:00Z",
            }
        ],
        "total": 2,
        "returned": 1,
        "limit": 1,
        "truncated": True,
    }


def test_api_exposes_machine_receipt_as_separate_read_only_dimension(
    tmp_path,
    monkeypatch,
):
    fixture = one_module_two_entities_fixture()
    tree = materialize_fixture_tree(
        fixture,
        tmp_path / "checkout",
        consumer="api",
    )
    commit_knowledge_artifacts(_knowledge_commit_plan(tree["wiki_root"], fixture))
    loaded = load_knowledge_state(tree["wiki_root"])
    assert loaded.knowledge is not None
    assert loaded.manifest_basis is not None
    assert loaded.manifest_basis.artifact_hashes is not None
    hashes = loaded.manifest_basis.artifact_hashes
    context = build_artifact_verification_context(
        loaded.knowledge,
        knowledge_hash=hashes.knowledge_index_hash,
        surface_index_hash=hashes.surface_index_hash,
        evaluated_envelope_hash=hashes.evaluated_envelope_hash,
        governance_hash=hashes.governance_hash,
    )
    verify_and_write_receipt(
        tree["wiki_root"],
        context,
        [ARTIFACT_INTEGRITY_CHECKER_ID],
    )
    monkeypatch.chdir(tree["root"])

    service = api.build_documentation_query_service(
        src_dir=".",
        wiki_dir="docs/llm_wiki",
    )
    assert service.knowledge_view is not None
    assert service.knowledge_view.machine_verification.availability.value == "recorded"

    result = api.get_concept(
        "llm-wiki://entities/User",
        service=service,
    )

    assert result["concept"]["verification"] == "untracked"
    assert result["concept"]["machine_verification"] == {
        "availability": "recorded",
        "scope_uid": "bundle:locator-only",
        "valid": True,
        "invalidation_reasons": [],
        "recorded_result": "passed",
        "passed": True,
        "checks": {
            "artifact-integrity": {
                "version": "1",
                "result": "passed",
                "diagnostics": [],
                "diagnostic_coverage": {
                    "observed": 0,
                    "emitted": 0,
                    "omitted": 0,
                    "limit": 50,
                    "truncated": False,
                },
            }
        },
    }


def test_query_service_builder_uses_snapshot_only_on_live_option_failure(
    tmp_path,
    monkeypatch,
):
    fixture = one_module_two_entities_fixture()
    tree = materialize_fixture_tree(
        fixture,
        tmp_path / "checkout",
        consumer="api",
    )
    commit_knowledge_artifacts(_knowledge_commit_plan(tree["wiki_root"], fixture))
    monkeypatch.chdir(tree["root"])

    def fail_live_options(**_kwargs):
        raise ValueError("invalid runtime generation policy")

    monkeypatch.setattr(
        api.context_cmd,
        "runtime_generation_options",
        fail_live_options,
    )

    result = api.get_concept(
        "llm-wiki://entities/User",
        src_dir=".",
        wiki_dir="docs/llm_wiki",
    )

    assert result["knowledge"] == {
        "availability": "ready",
        "reason": "all-projection-commitments-match",
        "freshness": "unevaluated (snapshot-only read)",
        "freshness_evaluated": False,
    }
    assert result["concept"]["freshness"] == {
        "state": None,
        "reason": "not-evaluated",
        "live_comparison_performed": False,
    }


def test_graph_query_service_and_wrappers_return_documentation_answers(tmp_project):
    _write_query_project(tmp_project)
    _write_api_wiki(tmp_project)

    service = build_documentation_query_service(".", wiki_dir="docs/llm_wiki")

    flow = flow_for_entrypoint("api-run", service=service)
    assert flow["found"] is True
    assert flow["flow"]["entry"]["symbol"] == "run"
    assert flow["flow"]["modules_touched"] == ["api.py", "repo.py"]

    data_flow = data_flow_for_entrypoint("run", service=service)
    assert data_flow["found"] is True
    assert data_flow["data_flow"]["entry"]["id"] == "api-run"

    caller_result = callers("save", service=service)
    assert caller_result["found"] is True
    assert caller_result["callers"] == [
        {
            "file": "api.py",
            "module": "api",
            "symbol": "run",
            "kind": "internal",
            "line": 6,
        }
    ]

    callee_result = callees("run", service=service)
    assert callee_result["found"] is True
    assert callee_result["callees"] == [
        {
            "file": "repo.py",
            "module": "repo",
            "symbol": "save",
            "kind": "internal",
            "line": 6,
        }
    ]

    assert dependency_neighborhood("api.py", service=service)["outbound"] == ["repo.py"]
    assert pages_for_symbol("run", service=service)["pages"][0]["canonical_path"] in {
        "flows/api-run.md",
        "modules/api.md",
    }
    concept = api.get_concept("llm-wiki://modules/api", service=service)
    assert concept["knowledge"] == {
        "availability": "absent",
        "reason": "knowledge-projection-not-present",
        "freshness": "unevaluated (snapshot-only read)",
        "freshness_evaluated": False,
    }
    assert concept["found"] is False
    assert concept["concept"] is None


def test_api_wrappers_map_path_and_query_errors(tmp_project):
    with pytest.raises(PathPolicyError):
        list_wiki_pages("../outside")

    service = build_documentation_query_service(".", wiki_dir="docs/llm_wiki")
    with pytest.raises(LlmWikiApiError, match="symbol must be a non-empty string"):
        callers("", service=service)


class _RecordingKnowledgeService:
    def __init__(self):
        self.calls = []
        self.concept_result = {"operation": "get_concept"}
        self.sections_result = {"operation": "list_concept_sections"}
        self.related_result = {"operation": "related_concepts"}
        self.evidence_result = {"operation": "explain_evidence"}

    def get_concept(self, locator_or_exact_route):
        self.calls.append(("get_concept", locator_or_exact_route))
        return self.concept_result

    def list_concept_sections(
        self,
        locator_or_exact_route,
        *,
        ownership=None,
    ):
        self.calls.append(("list_concept_sections", locator_or_exact_route, ownership))
        return self.sections_result

    def related_concepts(
        self,
        locator_or_exact_route,
        *,
        direction="both",
        kinds=None,
    ):
        self.calls.append(
            (
                "related_concepts",
                locator_or_exact_route,
                direction,
                kinds,
            )
        )
        return self.related_result

    def explain_evidence(self, locator_or_exact_route):
        self.calls.append(("explain_evidence", locator_or_exact_route))
        return self.evidence_result


def test_knowledge_wrappers_reuse_supplied_service_without_building_or_extracting(
    monkeypatch,
):
    monkeypatch.setattr(
        api,
        "build_documentation_query_service",
        fail_if_extraction_runs,
    )
    monkeypatch.setattr(
        api.extract_cmd,
        "build_extract_payload",
        fail_if_extraction_runs,
    )
    monkeypatch.setattr(
        api,
        "evaluate_surface_index",
        fail_if_extraction_runs,
    )
    monkeypatch.setattr(
        api.context_cmd,
        "_build_context_knowledge_view",
        fail_if_extraction_runs,
    )
    service = _RecordingKnowledgeService()
    common = {
        "service": service,
        "src_dir": "../unused-source",
        "wiki_dir": "../unused-wiki",
        "limit": 0,
        "allow_external_src": False,
        "read_only": True,
    }

    concept = api.get_concept("llm-wiki://entities/User", **common)
    sections = api.list_concept_sections(
        "llm-wiki://entities/User",
        ownership="semantic",
        **common,
    )
    related = api.related_concepts(
        "entities/User.md",
        direction="outbound",
        kinds=["links_to"],
        **common,
    )
    evidence = api.explain_evidence("llm-wiki://entities/User", **common)

    assert concept is service.concept_result
    assert sections is service.sections_result
    assert related is service.related_result
    assert evidence is service.evidence_result
    assert service.calls == [
        ("get_concept", "llm-wiki://entities/User"),
        (
            "list_concept_sections",
            "llm-wiki://entities/User",
            "semantic",
        ),
        (
            "related_concepts",
            "entities/User.md",
            "outbound",
            ["links_to"],
        ),
        ("explain_evidence", "llm-wiki://entities/User"),
    ]


def test_section_query_python_api_and_mcp_results_are_identical(tmp_path, monkeypatch):
    query_service = api.DocumentationGraphQueryService({})
    monkeypatch.setattr(
        mcp_server,
        "build_documentation_query_service",
        lambda *_args, **_kwargs: query_service,
    )

    python_result = api.list_concept_sections(
        "llm-wiki://entities/User",
        ownership="unknown",
        service=query_service,
    )
    mcp_result = mcp_server.McpWikiService(
        src_dir=str(tmp_path),
        wiki_dir=str(tmp_path / "wiki"),
    ).list_concept_sections(
        "llm-wiki://entities/User",
        ownership="unknown",
    )

    assert mcp_result == python_result


class _FailingKnowledgeService:
    @staticmethod
    def _fail():
        raise api.DocumentationQueryError("knowledge query failed")

    def get_concept(self, _locator_or_exact_route):
        self._fail()

    def list_concept_sections(
        self,
        _locator_or_exact_route,
        *,
        ownership=None,
    ):
        del ownership
        self._fail()

    def related_concepts(
        self,
        _locator_or_exact_route,
        *,
        direction="both",
        kinds=None,
    ):
        del direction, kinds
        self._fail()

    def explain_evidence(self, _locator_or_exact_route):
        self._fail()


@pytest.mark.parametrize(
    ("function_name", "kwargs"),
    [
        ("get_concept", {}),
        ("list_concept_sections", {"ownership": "semantic"}),
        (
            "related_concepts",
            {"direction": "outbound", "kinds": ["derived_from"]},
        ),
        ("explain_evidence", {}),
    ],
)
def test_knowledge_wrappers_map_query_errors_without_building_service(
    monkeypatch,
    function_name,
    kwargs,
):
    monkeypatch.setattr(
        api,
        "build_documentation_query_service",
        fail_if_extraction_runs,
    )
    service = _FailingKnowledgeService()

    with pytest.raises(
        LlmWikiApiError,
        match="knowledge query failed",
    ) as exc_info:
        getattr(api, function_name)(
            "llm-wiki://entities/User",
            service=service,
            **kwargs,
        )

    assert isinstance(exc_info.value.__cause__, api.DocumentationQueryError)


@pytest.mark.parametrize(
    ("load_result", "availability", "reason"),
    [
        (
            KnowledgeLoadResult(
                status=KnowledgeLoadState.ABSENT,
                surface={},
                knowledge=None,
                manifest_basis=None,
            ),
            "absent",
            "knowledge-projection-not-present",
        ),
        (
            KnowledgeLoadResult(
                status=KnowledgeLoadState.DEGRADED,
                surface={},
                knowledge=None,
                manifest_basis=None,
                underlying_status=KnowledgeLoadState.INVALID,
            ),
            "degraded",
            "policy-selected-surface-only-fallback-after-invalid",
        ),
    ],
)
def test_knowledge_wrappers_preserve_structured_non_ready_state_without_extraction(
    monkeypatch,
    load_result,
    availability,
    reason,
):
    view = build_knowledge_read_view(load_result)
    service = api.DocumentationGraphQueryService(
        {},
        knowledge_view=view,
    )
    monkeypatch.setattr(
        api,
        "build_documentation_query_service",
        fail_if_extraction_runs,
    )
    monkeypatch.setattr(
        api.extract_cmd,
        "build_extract_payload",
        fail_if_extraction_runs,
    )

    concept = api.get_concept(
        "llm-wiki://entities/User",
        service=service,
    )
    sections = api.list_concept_sections(
        "llm-wiki://entities/User",
        ownership="semantic",
        service=service,
    )
    related = api.related_concepts(
        "llm-wiki://entities/User",
        direction="outbound",
        kinds=["links_to"],
        service=service,
    )
    evidence = api.explain_evidence(
        "llm-wiki://entities/User",
        service=service,
    )

    status = {
        "availability": availability,
        "reason": reason,
        "freshness": "unevaluated (snapshot-only read)",
        "freshness_evaluated": False,
    }
    assert concept["knowledge"] == status
    assert concept["found"] is False
    assert concept["concept"] is None
    assert sections["knowledge"] == status
    assert sections["found"] is False
    assert sections["section_ownership"] == {
        "availability": availability,
        "reason": reason,
        "schema_version": None,
    }
    assert sections["ownership"] == "semantic"
    assert sections["sections"] == []
    assert related["knowledge"] == status
    assert related["found"] is False
    assert related["direction"] == "outbound"
    assert related["kinds"] == ["links_to"]
    assert related["relationships"] == []
    assert evidence["knowledge"] == status
    assert evidence["found"] is False
    assert evidence["evidence"] is None
