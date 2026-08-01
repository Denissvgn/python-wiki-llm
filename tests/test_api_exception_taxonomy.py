"""Stable exception and return-type contracts for the supported Python API."""

from __future__ import annotations

import inspect
from pathlib import Path
import typing
import warnings

import pytest

import llm_wiki_cli.api as api
from llm_wiki_cli import api_types
from llm_wiki_cli.services.bootstrap_service import BootstrapRequestError


_PUBLIC_FUNCTION_NAMES = (
    "admit_calibration_run",
    "admit_p0_calibration_run",
    "adopt_documentation_wiki_snapshot",
    "bootstrap_wiki",
    "build_calibration_agent_packet",
    "build_context",
    "build_qualified_context",
    "build_documentation_agent_packet",
    "build_documentation_query_service",
    "build_p0_calibration_agent_packet",
    "callees",
    "callers",
    "compare_context_packet_basis",
    "data_flow_for_entrypoint",
    "dependency_neighborhood",
    "dispatch_calibration_agent",
    "dispatch_p0_calibration_agent",
    "doctor",
    "explain_evidence",
    "export_documentation_run",
    "extract_source",
    "fingerprint_documentation_wiki_input",
    "flow_for_entrypoint",
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
    "validate_documentation_model_selection",
    "verify_calibration_run",
    "verify_documentation_run",
    "verify_p0_calibration_run",
)

_INVALID_REQUEST_FAILURES = frozenset(
    {
        "build_context",
        "build_qualified_context",
        "build_documentation_query_service",
        "callees",
        "callers",
        "compare_context_packet_basis",
        "data_flow_for_entrypoint",
        "dependency_neighborhood",
        "doctor",
        "explain_evidence",
        "extract_source",
        "flow_for_entrypoint",
        "get_concept",
        "list_concept_sections",
        "list_wiki_pages",
        "pages_for_symbol",
        "prepare_calibration_run",
        "prepare_p0_calibration_run",
        "record_calibration_agent_result",
        "record_p0_calibration_agent_result",
        "related_concepts",
        "select_documentation_model",
        "traverse_typed_graph",
        "use_calibration_host_broker_authenticator",
        "use_p0_calibration_host_broker_authenticator",
        "reconcile_context_packet",
        "validate_context_packet",
        "validate_documentation_model_selection",
    }
)
_WORKSPACE_STATE_FAILURES = frozenset(
    {
        "adopt_documentation_wiki_snapshot",
        "bootstrap_wiki",
        "build_documentation_agent_packet",
        "export_documentation_run",
        "fingerprint_documentation_wiki_input",
        "get_documentation_run_status",
        "prepare_documentation_run",
        "record_documentation_agent_result",
        "verify_documentation_run",
    }
)
_ARTIFACT_INTEGRITY_FAILURES = frozenset(
    {
        "admit_calibration_run",
        "admit_p0_calibration_run",
        "build_calibration_agent_packet",
        "build_p0_calibration_agent_packet",
        "dispatch_calibration_agent",
        "dispatch_p0_calibration_agent",
        "get_calibration_run_status",
        "get_p0_calibration_run_status",
        "verify_calibration_run",
        "verify_p0_calibration_run",
    }
)


class _FailingQueryService:
    @staticmethod
    def _fail() -> None:
        raise api.DocumentationQueryError("provoked query failure")

    def flow_for_entrypoint(self, _value):
        self._fail()

    def data_flow_for_entrypoint(self, _value):
        self._fail()

    def callers(self, _value):
        self._fail()

    def callees(self, _value):
        self._fail()

    def dependency_neighborhood(self, _value):
        self._fail()

    def pages_for_symbol(self, _value):
        self._fail()

    def get_concept(self, _value):
        self._fail()

    def list_concept_sections(self, _value, *, ownership=None):
        del ownership
        self._fail()

    def related_concepts(self, _value, *, direction="both", kinds=None):
        del direction, kinds
        self._fail()

    def traverse_typed_graph(
        self,
        _value,
        *,
        direction="both",
        kinds=None,
        origins=None,
        resolutions=None,
        include_evidence=False,
    ):
        del direction, kinds, origins, resolutions, include_evidence
        self._fail()

    def explain_evidence(self, _value):
        self._fail()


class _NonleafApiFailingQueryService(_FailingQueryService):
    @staticmethod
    def _fail() -> None:
        raise api.LlmWikiApiError("nonleaf API failure")


class _CustomInvalidRequestError(api.InvalidRequestError):
    pass


class _CustomLeafFailingQueryService(_FailingQueryService):
    @staticmethod
    def _fail() -> None:
        raise _CustomInvalidRequestError("custom leaf failure")


def _enter(manager) -> None:
    with manager:
        pass


def _deprecated(callable_, *args, **kwargs):
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", DeprecationWarning)
        return callable_(*args, **kwargs)


def _deprecated_context(callable_, *args, **kwargs) -> None:
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", DeprecationWarning)
        _enter(callable_(*args, **kwargs))


def _failure_cases(tmp_path: Path):
    missing_source = tmp_path / "missing-source"
    missing_wiki = tmp_path / "missing-wiki"
    missing_workspace = tmp_path / "missing-workspace"
    missing_controller = tmp_path / "missing-controller"
    query_service = _FailingQueryService()

    return {
        "bootstrap_wiki": lambda: api.bootstrap_wiki(
            str(missing_source),
            str(tmp_path / "new-wiki"),
        ),
        "extract_source": lambda: api.extract_source(str(missing_source)),
        "build_context": lambda: api.build_context(".", budget=0),
        "build_qualified_context": lambda: api.build_qualified_context(
            ".",
            request={
                "budget_tokens": 0,
                "focus": ["all"],
                "format": "json",
                "filters": {},
            },
        ),
        "validate_context_packet": lambda: api.validate_context_packet(b"{}\n"),
        "compare_context_packet_basis": lambda: api.compare_context_packet_basis(
            b"{}\n",
            {"source_snapshot": {}},
        ),
        "reconcile_context_packet": lambda: api.reconcile_context_packet(b"{}\n"),
        "list_wiki_pages": lambda: api.list_wiki_pages("\0"),
        "build_documentation_query_service": lambda: (
            api.build_documentation_query_service(str(missing_source))
        ),
        "flow_for_entrypoint": lambda: api.flow_for_entrypoint(
            "entry",
            service=query_service,
        ),
        "data_flow_for_entrypoint": lambda: api.data_flow_for_entrypoint(
            "entry",
            service=query_service,
        ),
        "callers": lambda: api.callers("symbol", service=query_service),
        "callees": lambda: api.callees("symbol", service=query_service),
        "dependency_neighborhood": lambda: api.dependency_neighborhood(
            "module.py",
            service=query_service,
        ),
        "doctor": lambda: api.doctor(
            str(missing_source),
            wiki_dir=str(missing_wiki),
            allow_external_src=True,
        ),
        "pages_for_symbol": lambda: api.pages_for_symbol(
            "symbol",
            service=query_service,
        ),
        "get_concept": lambda: api.get_concept(
            "llm-wiki://entities/Thing",
            service=query_service,
        ),
        "list_concept_sections": lambda: api.list_concept_sections(
            "llm-wiki://entities/Thing",
            service=query_service,
        ),
        "related_concepts": lambda: api.related_concepts(
            "llm-wiki://entities/Thing",
            service=query_service,
        ),
        "traverse_typed_graph": lambda: api.traverse_typed_graph(
            "llm-wiki://entities/Thing",
            service=query_service,
        ),
        "explain_evidence": lambda: api.explain_evidence(
            "llm-wiki://entities/Thing",
            service=query_service,
        ),
        "fingerprint_documentation_wiki_input": lambda: (
            api.fingerprint_documentation_wiki_input(missing_wiki)
        ),
        "adopt_documentation_wiki_snapshot": lambda: (
            api.adopt_documentation_wiki_snapshot(
                missing_wiki,
                tmp_path / "adopted-wiki",
            )
        ),
        "prepare_documentation_run": lambda: api.prepare_documentation_run(
            missing_workspace,
            source_root=missing_source,
            site_name="Project",
        ),
        "get_documentation_run_status": lambda: (
            api.get_documentation_run_status(missing_workspace)
        ),
        "build_documentation_agent_packet": lambda: (
            api.build_documentation_agent_packet(
                missing_workspace,
                stage="wiki-enrichment",
            )
        ),
        "record_documentation_agent_result": lambda: (
            api.record_documentation_agent_result(missing_workspace, {})
        ),
        "verify_documentation_run": lambda: api.verify_documentation_run(
            missing_workspace
        ),
        "export_documentation_run": lambda: api.export_documentation_run(
            missing_workspace
        ),
        "prepare_calibration_run": lambda: api.prepare_calibration_run(
            missing_controller,
            control_workspaces=(),
            execution_manifest={},
        ),
        "admit_calibration_run": lambda: api.admit_calibration_run(
            missing_controller,
            authority_grant={},
        ),
        "get_calibration_run_status": lambda: api.get_calibration_run_status(
            missing_controller
        ),
        "build_calibration_agent_packet": lambda: (
            api.build_calibration_agent_packet(
                missing_controller,
                role="intake-a",
            )
        ),
        "dispatch_calibration_agent": lambda: api.dispatch_calibration_agent(
            missing_controller,
            role="intake-a",
        ),
        "record_calibration_agent_result": lambda: (
            api.record_calibration_agent_result(
                missing_controller,
                dispatch_receipt={},
                result={},
            )
        ),
        "verify_calibration_run": lambda: api.verify_calibration_run(
            missing_controller
        ),
        "select_documentation_model": lambda: api.select_documentation_model(
            None,
            None,
        ),
        "validate_documentation_model_selection": lambda: (
            api.validate_documentation_model_selection(None, None, None)
        ),
        "use_calibration_host_broker_authenticator": lambda: _enter(
            api.use_calibration_host_broker_authenticator(object())
        ),
        "prepare_p0_calibration_run": lambda: _deprecated(
            api.prepare_p0_calibration_run,
            missing_controller,
            control_workspaces=(),
            execution_manifest={},
        ),
        "admit_p0_calibration_run": lambda: _deprecated(
            api.admit_p0_calibration_run,
            missing_controller,
            authority_grant={},
        ),
        "get_p0_calibration_run_status": lambda: _deprecated(
            api.get_p0_calibration_run_status,
            missing_controller,
        ),
        "build_p0_calibration_agent_packet": lambda: _deprecated(
            api.build_p0_calibration_agent_packet,
            missing_controller,
            role="intake-a",
        ),
        "dispatch_p0_calibration_agent": lambda: _deprecated(
            api.dispatch_p0_calibration_agent,
            missing_controller,
            role="intake-a",
        ),
        "record_p0_calibration_agent_result": lambda: _deprecated(
            api.record_p0_calibration_agent_result,
            missing_controller,
            dispatch_receipt={},
            result={},
        ),
        "verify_p0_calibration_run": lambda: _deprecated(
            api.verify_p0_calibration_run,
            missing_controller,
        ),
        "use_p0_calibration_host_broker_authenticator": lambda: (
            _deprecated_context(
                api.use_p0_calibration_host_broker_authenticator,
                object(),
            )
        ),
    }


def test_every_public_api_function_has_an_exception_boundary(tmp_path):
    cases = _failure_cases(tmp_path)
    public_functions = {
        name
        for name in api.__all__
        if inspect.isfunction(getattr(api, name))
    }

    assert set(_PUBLIC_FUNCTION_NAMES) == set(cases) == public_functions
    for name in sorted(public_functions):
        function = getattr(api, name)
        assert getattr(function, "__llm_wiki_api_boundary__", False), name


def test_legacy_exception_names_are_leaf_aliases():
    assert api.PathPolicyError is api.InvalidRequestError
    assert api.ExtractionError is api.WorkspaceStateError
    assert api.BootstrapError is api.WorkspaceStateError


def test_nul_wiki_dir_is_an_invalid_request():
    with pytest.raises(api.InvalidRequestError) as raised:
        api.list_wiki_pages("invalid\0wiki")

    assert type(raised.value) is api.InvalidRequestError
    assert isinstance(raised.value.__cause__, api.PathValidationError)


@pytest.mark.parametrize("function_name", _PUBLIC_FUNCTION_NAMES)
def test_public_api_function_maps_a_provoked_failure(tmp_path, function_name):
    expected_types = {
        **{
            name: api.InvalidRequestError
            for name in _INVALID_REQUEST_FAILURES
        },
        **{
            name: api.WorkspaceStateError
            for name in _WORKSPACE_STATE_FAILURES
        },
        **{
            name: api.ArtifactIntegrityError
            for name in _ARTIFACT_INTEGRITY_FAILURES
        },
    }
    assert set(expected_types) == set(_PUBLIC_FUNCTION_NAMES)

    with pytest.raises(expected_types[function_name]) as exc_info:
        _failure_cases(tmp_path)[function_name]()
    assert type(exc_info.value) is expected_types[function_name]
    assert exc_info.value.__cause__ is not None


def test_bootstrap_invalid_contract_value_is_an_invalid_request(tmp_path: Path):
    source = tmp_path / "source"
    source.mkdir()

    with pytest.raises(api.InvalidRequestError) as raised:
        api.bootstrap_wiki(
            str(source),
            str(tmp_path / "wiki"),
            depth="unsupported",
        )
    assert type(raised.value) is api.InvalidRequestError
    assert isinstance(raised.value.__cause__, BootstrapRequestError)


@pytest.mark.parametrize("case", ["overwrite", "overlap"])
def test_bootstrap_request_policy_is_an_invalid_request(
    tmp_path: Path,
    case: str,
):
    source = tmp_path / "source"
    source.mkdir()
    wiki = source / "wiki" if case == "overlap" else tmp_path / "wiki"

    with pytest.raises(api.InvalidRequestError) as raised:
        api.bootstrap_wiki(
            str(source),
            str(wiki),
            overwrite=case == "overwrite",
        )
    assert type(raised.value) is api.InvalidRequestError
    assert isinstance(raised.value.__cause__, BootstrapRequestError)


def test_missing_allowed_query_source_is_workspace_state(tmp_path: Path):
    with pytest.raises(api.WorkspaceStateError) as raised:
        api.build_documentation_query_service(
            str(tmp_path / "missing-source"),
            allow_external_src=True,
        )
    assert type(raised.value) is api.WorkspaceStateError
    assert isinstance(raised.value.__cause__, api.PathValidationError)


@pytest.mark.parametrize(
    "function_name",
    ("build_qualified_context", "reconcile_context_packet"),
)
@pytest.mark.parametrize(
    ("field", "public_error"),
    [
        ("src_dir", api.WorkspaceStateError),
        ("wiki_dir", api.PathPolicyError),
        ("budget_tokens", api.InvalidRequestError),
    ],
)
def test_qualified_context_protocol_fields_follow_context_taxonomy(
    monkeypatch,
    function_name,
    field,
    public_error,
):
    internal_error = api.context_cmd.ProtocolRequestError(
        f"invalid {field}",
        field,
    )

    def fail(*_args, **_kwargs):
        raise internal_error

    monkeypatch.setattr(
        api.context_packet_service,
        function_name,
        fail,
    )
    call = (
        (lambda: api.build_qualified_context())
        if function_name == "build_qualified_context"
        else (lambda: api.reconcile_context_packet(b"packet\n"))
    )

    with pytest.raises(public_error) as raised:
        call()

    assert type(raised.value) is public_error
    assert raised.value.__cause__ is internal_error


@pytest.mark.parametrize("payload", ["{", "{}"])
def test_persisted_documentation_run_corruption_is_artifact_integrity(
    tmp_path: Path,
    payload: str,
):
    run_path = tmp_path / ".llm-wiki-docs" / "run.json"
    run_path.parent.mkdir()
    run_path.write_text(payload, encoding="utf-8")

    with pytest.raises(api.ArtifactIntegrityError) as raised:
        api.get_documentation_run_status(tmp_path)
    assert type(raised.value) is api.ArtifactIntegrityError
    assert isinstance(
        raised.value.__cause__,
        api.DocumentationIntegrityError,
    )
    assert isinstance(
        raised.value.__cause__,
        api.DocumentationSchemaError,
    )


def test_submitted_documentation_result_schema_is_invalid_request(
    tmp_path: Path,
):
    run_path = tmp_path / ".llm-wiki-docs" / "run.json"
    run_path.parent.mkdir()
    fixture_path = (
        Path(__file__).parent
        / "fixtures"
        / "documentation_runs"
        / "partial.json"
    )
    run_path.write_bytes(fixture_path.read_bytes())

    with pytest.raises(api.InvalidRequestError) as raised:
        api.record_documentation_agent_result(tmp_path, {})
    assert type(raised.value) is api.InvalidRequestError
    assert isinstance(raised.value.__cause__, api.DocumentationSchemaError)


def test_public_dict_return_annotations_import_and_resolve():
    expected = {
        "extract_source": api_types.ExtractSourceResult,
        "build_context": (
            api_types.ContextPayload | api_types.MarkdownContextResult
        ),
        "build_qualified_context": api.QualifiedContextPacket,
        "validate_context_packet": api.ContextPacketValidation,
        "compare_context_packet_basis": api.ContextBasisComparison,
        "reconcile_context_packet": api.ContextPacketReconciliation,
        "list_wiki_pages": api_types.WikiPagesResult,
        "doctor": api_types.DoctorResult,
        "flow_for_entrypoint": api_types.FlowForEntrypointResult,
        "data_flow_for_entrypoint": api_types.DataFlowForEntrypointResult,
        "callers": api_types.CallersResult,
        "callees": api_types.CalleesResult,
        "dependency_neighborhood": api_types.DependencyNeighborhoodResult,
        "pages_for_symbol": api_types.PagesForSymbolResult,
        "get_concept": api_types.ConceptResult,
        "list_concept_sections": api_types.ConceptSectionsResult,
        "related_concepts": api_types.RelatedConceptsResult,
        "traverse_typed_graph": api_types.TypedGraphTraversalResult,
        "explain_evidence": api_types.EvidenceExplanationResult,
        "export_documentation_run": api_types.DocumentationExportResult,
    }

    assert {
        name: typing.get_type_hints(getattr(api, name))["return"]
        for name in expected
    } == expected

    bounded = {
        "query",
        "found",
        "ambiguous",
        "matches",
        "truncated",
        "bounds",
    }
    concept = bounded | {"knowledge", "concept", "total", "returned"}
    expected_keys = {
        api_types.ExtractSourceResult: (
            {"schema_version", "inventory", "data_flow_details"},
            {
                "docker",
                "unsupported_sources",
                "entrypoints",
                "data_flows",
                "dependencies",
                "api_contracts",
                "warnings",
            },
        ),
        api_types.ContextPayload: (
            {
                "budget",
                "used",
                "truncated",
                "omitted_files",
                "downgraded_files",
                "bounds",
                "files",
            },
            {
                "graphs",
                "surface",
                "knowledge",
                "typed_graph",
                "ranking_policy",
                "warnings",
            },
        ),
        api_types.MarkdownContextResult: (
            {"content", "payload", "warnings"},
            set(),
        ),
        api_types.WikiPage: (
            {
                "kind",
                "id",
                "label",
                "canonical_path",
                "mcp_uri",
                "role",
                "obsidian_mirror_dir",
            },
            set(),
        ),
        api_types.WikiPageCounts: (
            {"total", "by_kind", "architecture_pages"},
            set(),
        ),
        api_types.WikiPagesResult: (
            {"wiki_dir", "counts", "pages"},
            set(),
        ),
        api_types.DoctorAvailability: (
            {"state", "reason", "usable"},
            set(),
        ),
        api_types.DoctorFreshness: (
            {"evaluated", "disclosure", "concepts", "counts_by_state"},
            set(),
        ),
        api_types.DoctorSnapshotParity: (
            {"state", "issue_count", "reasons"},
            set(),
        ),
        api_types.DoctorGovernance: (
            {
                "state",
                "ledger",
                "projection",
                "expired_reviews",
                "issue_count",
                "reasons",
            },
            set(),
        ),
        api_types.DoctorDrift: (
            {
                "state",
                "confirmed_stale",
                "indeterminate",
                "nonsemantic_changes",
                "counts_by_state",
                "diagnostic_count",
                "reasons",
            },
            set(),
        ),
        api_types.DoctorVerificationReceipt: (
            {"state", "reason", "recorded_result", "passed"},
            set(),
        ),
        api_types.DoctorResult: (
            {
                "schema_version",
                "status",
                "exit_code",
                "strict",
                "wiki_dir",
                "src_dir",
                "availability",
                "freshness",
                "snapshot_parity",
                "governance",
                "drift",
                "verification_receipt",
                "degraded_reasons",
                "unhealthy_reasons",
            },
            set(),
        ),
        api_types.FlowForEntrypointResult: (bounded | {"flow"}, set()),
        api_types.DataFlowForEntrypointResult: (
            bounded | {"data_flow"},
            set(),
        ),
        api_types.CallersResult: (
            bounded | {"callable", "callers"},
            set(),
        ),
        api_types.CalleesResult: (
            bounded | {"callable", "callees"},
            set(),
        ),
        api_types.DependencyNeighborhoodResult: (
            bounded
            | {
                "path",
                "inbound",
                "outbound",
                "metrics",
                "cycle_groups",
                "load_order_index",
                "pages",
            },
            set(),
        ),
        api_types.PagesForSymbolResult: (
            bounded | {"symbol", "pages"},
            set(),
        ),
        api_types.ConceptResult: (concept, set()),
        api_types.ConceptSectionsResult: (
            concept
            | {
                "section_ownership",
                "ownership",
                "sections",
            },
            set(),
        ),
        api_types.RelatedConceptsResult: (
            concept
            | {
                "direction",
                "kinds",
                "relationships",
                "related_concepts",
                "unresolved_targets",
                "external_targets",
            },
            set(),
        ),
        api_types.TypedGraphTraversalResult: (
            concept
            | {
                "direction",
                "kinds",
                "origins",
                "resolutions",
                "include_evidence",
                "typed_graph",
                "edges",
            },
            set(),
        ),
        api_types.EvidenceExplanationResult: (
            concept | {"evidence"},
            set(),
        ),
        api_types.DocumentationExportResult: (
            {
                "schema_version",
                "run_id",
                "state",
                "verdict",
                "source",
                "baseline",
                "intake",
                "skills",
                "coverage",
                "budgets",
                "evidence",
                "execution_route",
                "unresolved_findings",
                "validation",
                "limitations",
                "distribution",
                "deployment_handoff",
                "resume",
                "generated_at",
            },
            set(),
        ),
    }

    assert set(expected_keys) == {
        getattr(api_types, name) for name in api_types.__all__
    }
    for contract, (required, optional) in expected_keys.items():
        assert set(contract.__required_keys__) == required
        assert set(contract.__optional_keys__) == optional


@pytest.mark.parametrize(
    ("internal_error", "public_error"),
    [
        (ValueError("bad request"), api.InvalidRequestError),
        (OSError("workspace unavailable"), api.WorkspaceStateError),
        (
            api.DocumentationIntegrityError("artifact changed"),
            api.ArtifactIntegrityError,
        ),
    ],
)
def test_internal_failure_families_map_to_exact_taxonomy_leaves(
    internal_error,
    public_error,
):
    with pytest.raises(public_error) as exc_info:
        api._raise_api_error(internal_error)

    assert type(exc_info.value) is public_error
    assert exc_info.value.__cause__ is internal_error


@pytest.mark.parametrize(
    ("service", "public_error", "internal_error"),
    [
        (
            _NonleafApiFailingQueryService(),
            api.WorkspaceStateError,
            api.LlmWikiApiError,
        ),
        (
            _CustomLeafFailingQueryService(),
            api.InvalidRequestError,
            _CustomInvalidRequestError,
        ),
    ],
)
def test_public_boundary_reclassifies_nonleaf_api_errors(
    service,
    public_error,
    internal_error,
):
    with pytest.raises(public_error) as exc_info:
        api.callers("symbol", service=service)

    assert type(exc_info.value) is public_error
    assert type(exc_info.value.__cause__) is internal_error


@pytest.mark.parametrize(
    ("category", "public_error"),
    [
        ("invalid_freshness_policy", api.InvalidRequestError),
        ("workspace_unreadable", api.WorkspaceStateError),
        ("metadata_corrupt", api.ArtifactIntegrityError),
        ("knowledge_schema_unsupported", api.ArtifactIntegrityError),
        ("native_artifact_invalid", api.ArtifactIntegrityError),
    ],
)
def test_wiki_input_categories_map_by_failure_source(category, public_error):
    internal_error = api.DocumentationWikiInputError(
        "provoked wiki-input failure",
        category=category,
    )

    with pytest.raises(public_error) as exc_info:
        api._raise_api_error(internal_error)

    assert type(exc_info.value) is public_error
    assert exc_info.value.__cause__ is internal_error
