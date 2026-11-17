"""Published schemas, shared conformance cases and Python validators agree."""

from __future__ import annotations

import io
import json
import sys
import uuid
from collections.abc import Callable
from importlib import resources
from typing import Any, get_args, get_type_hints

import pytest
from jsonschema import Draft202012Validator

from llm_wiki_cli import api, cli
from llm_wiki_cli import api_types
from llm_wiki_cli.services import (
    context_packet,
    context_request_format,
    contracts,
    data_flow,
    entrypoints,
    extract_format,
    maintenance_projection,
    maintenance_queue,
    maintenance_queue_format,
    maintenance_state,
    maintenance_status,
    maintenance_status_format,
    query_result_format,
    search_lexical,
    search_rank,
    search_service,
    surface_index_format,
    wiki_surface,
    wiki_surface_index,
)
from llm_wiki_cli.services.wiki_media import build_asset_index
from llm_wiki_cli.services.context_packet import (
    CONTEXT_PACKET_KNOWLEDGE_SCHEMA_VERSION,
    CONTEXT_PACKET_SCHEMA_VERSION,
    validate_context_packet,
)
from llm_wiki_cli.engine import (
    CONTEXT_RESPONSE_PROTOCOLS,
    ENGINE_CAPABILITIES_SCHEMA_VERSION,
    ENGINE_EVENT_SCHEMA_VERSION,
    CODE_DOCS_PACK,
    Engine,
    EngineEvent,
    Host,
    NoProcessHost,
    SyncError,
    SyncRequest,
    validate_context_response,
    validate_engine_event,
)
from tests.developer_value.fixtures import POLICY_SOURCE
from tests.notes_pack import NOTES_PACK

SCHEMAS = resources.files("llm_wiki_cli.schemas")
CONFORMANCE = SCHEMAS.joinpath("conformance")

def _validate_packet_document(document: object) -> None:
    """Validate a packet document through its canonical bytes."""
    if not isinstance(document, dict):
        raise ValueError("a packet is a JSON object")
    validate_context_packet(context_packet._encode_packet_payload(document))


def _validate_maintenance_event(document: object) -> None:
    """Check an event the way the ledger checks one before a transition."""
    maintenance_state.maintenance_core().validate_schema("maintenance-event-v1", document)


def _validate_maintenance_basis(document: object) -> None:
    """Check a basis with the ledger's coordinate and semantic target grammar."""
    core = maintenance_state.maintenance_core()
    core.validate_schema("maintenance-basis-v1", document)
    assert isinstance(document, dict)
    core._coordinate(document["coordinate"])
    core._target(document["target"])


def _validate_maintenance_record_binding(document: object) -> None:
    """Check a page's record projection against the page its first record names."""
    try:
        page = document["records"][0]["target"]["canonical_path"]  # type: ignore[index]
    except (KeyError, IndexError, TypeError):
        page = "entities/Batch.md"
    adoption_id = document.get("adoption_id") if isinstance(document, dict) else None
    binding = {
        "schema_version": maintenance_projection.BINDING_SCHEMA,
        "adoption_id": adoption_id if isinstance(adoption_id, str) else str(uuid.UUID(int=0, version=4)),
        "state_hash": "sha256:" + "0" * 64,
    }
    concept = {
        "document": {"canonical_path": page},
        "extensions": {maintenance_projection.RECORD_KEY: document},
    }
    maintenance_projection.validate_maintenance_concept_projection(concept, binding=binding)


#: Python validators that must accept exactly the valid cases of a format.
PYTHON_VALIDATORS: dict[str, Callable[[object], object]] = {
    ENGINE_EVENT_SCHEMA_VERSION: validate_engine_event,
    CONTEXT_PACKET_SCHEMA_VERSION: _validate_packet_document,
    CONTEXT_PACKET_KNOWLEDGE_SCHEMA_VERSION: _validate_packet_document,
    **{protocol: validate_context_response for protocol in CONTEXT_RESPONSE_PROTOCOLS},
    query_result_format.DOCUMENTATION_QUERY_SCHEMA_VERSION: (
        query_result_format.validate_documentation_query_result
    ),
    query_result_format.SEARCH_RESULT_SCHEMA_VERSION: query_result_format.validate_search_result,
    surface_index_format.SURFACE_INDEX_SCHEMA_VERSION: surface_index_format.validate_surface_index,
    extract_format.EXTRACT_SCHEMA_VERSION: extract_format.validate_extract_payload,
    maintenance_status_format.MAINTENANCE_STATUS_SCHEMA_VERSION: (
        maintenance_status_format.validate_maintenance_status
    ),
    maintenance_queue_format.MAINTENANCE_QUEUE_SCHEMA_VERSION: (
        maintenance_queue_format.validate_maintenance_queue
    ),
    "llm-wiki-maintenance-adoption/v1": maintenance_state.validate_maintenance_adoption,
    "llm-wiki-maintenance-basis/v1": _validate_maintenance_basis,
    "llm-wiki-maintenance-event/v1": _validate_maintenance_event,
    "llm-wiki-maintenance-state/v1": maintenance_state.validate_maintenance_state,
    maintenance_projection.BINDING_SCHEMA: maintenance_projection.validate_maintenance_binding,
    maintenance_projection.RECORD_SCHEMA: _validate_maintenance_record_binding,
}


def _json(resource: Any) -> Any:
    return json.loads(resource.read_text(encoding="utf-8"))


def _schema(name: str) -> dict[str, Any]:
    schema = _json(SCHEMAS.joinpath(name))
    Draft202012Validator.check_schema(schema)
    return schema


def _case_files() -> list[str]:
    return sorted(item.name for item in CONFORMANCE.iterdir() if item.name.endswith(".cases.json"))


def _cases() -> list[tuple[str, dict[str, Any]]]:
    return [
        (name, case)
        for name in _case_files()
        for case in _json(CONFORMANCE.joinpath(name))["cases"]
    ]


def test_every_case_file_is_well_formed_and_names_its_schema():
    files = _case_files()
    assert {
        "llm-wiki-engine-event-v1.cases.json",
        "llm-wiki-engine-capabilities-v1.cases.json",
        "llm-wiki-qualified-context-packet-v1.cases.json",
        "llm-wiki-qualified-context-packet-v2.cases.json",
        "llm-wiki-context-response-v1.cases.json",
        "llm-wiki-context-response-v2.cases.json",
        "llm-wiki-documentation-query-v1.cases.json",
        "llm-wiki-search-result-v1.cases.json",
    } <= set(files)
    cases_schema = Draft202012Validator(_schema("llm-wiki-conformance-cases-v1.schema.json"))
    for name in files:
        document = _json(CONFORMANCE.joinpath(name))
        cases_schema.validate(document)
        assert name == document["schema"].replace(".schema.json", ".cases.json")
        schema = _schema(document["schema"])
        stem = document["schema"].removesuffix(".schema.json")
        # A format names its version in schema_version, or in protocol for
        # the context protocol responses. A maintenance basis names none, so
        # its format follows from the schema file name.
        for version_key in ("schema_version", "protocol"):
            if version_key in schema["properties"]:
                assert schema["properties"][version_key]["const"] == document["format"]
                break
        else:
            family, version = stem.rsplit("-", 1)
            assert document["format"] == f"{family}/{version}"
        # The maintenance ledger schemas predate the published ids and keep
        # their original urn ids.
        assert schema["$id"].endswith("/" + document["schema"]) or (
            schema["$id"] == "urn:llm-wiki:" + stem.removeprefix("llm-wiki-")
        )
        names = [case["name"] for case in document["cases"]]
        assert len(names) == len(set(names)), name
        assert {case["valid"] for case in document["cases"]} == {True, False}, name


@pytest.mark.parametrize(
    "file_name, case", _cases(), ids=[f"{f.split('.')[0]}:{c['name']}" for f, c in _cases()]
)
def test_schema_and_python_validators_agree_on_each_case(file_name, case):
    document = _json(CONFORMANCE.joinpath(file_name))
    validator = Draft202012Validator(_schema(document["schema"]))
    assert validator.is_valid(case["document"]) is case.get("schema_valid", case["valid"])
    python = PYTHON_VALIDATORS.get(document["format"])
    if python is None:
        return
    if case["valid"]:
        python(case["document"])
    else:
        with pytest.raises(ValueError):
            python(case["document"])


def test_engine_capabilities_match_their_schema():
    validator = Draft202012Validator(_schema("llm-wiki-engine-capabilities-v1.schema.json"))
    for engine in (
        Engine(),
        Engine(host=NoProcessHost()),
        Engine(pack=NOTES_PACK),
        Engine(pack=CODE_DOCS_PACK, helper_preparation="auto"),
    ):
        capabilities = engine.capabilities()
        assert capabilities["schema_version"] == ENGINE_CAPABILITIES_SCHEMA_VERSION
        validator.validate(json.loads(json.dumps(capabilities)))


def test_reported_events_match_their_schema(tmp_path, monkeypatch):
    (tmp_path / "src").mkdir()
    (tmp_path / "src/billing.py").write_text("class Invoice:\n    total: int\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("GIT_CEILING_DIRECTORIES", str(tmp_path.parent))
    events: list[EngineEvent] = []
    host = Host(stdout=io.StringIO(), stderr=io.StringIO(), events=events.append)
    engine = Engine(host=host)
    engine.call(api.bootstrap_wiki, "src", "wiki")
    engine.sync(SyncRequest(source_root="src", wiki_root="wiki"))
    (tmp_path / "not-a-wiki").mkdir()
    with pytest.raises(SyncError):
        engine.sync(SyncRequest(source_root="src", wiki_root="not-a-wiki"))

    validator = Draft202012Validator(_schema("llm-wiki-engine-event-v1.schema.json"))
    assert {event.kind for event in events} >= {"operation.started", "operation.finished", "operation.failed"}
    for event in events:
        document = json.loads(json.dumps(event.to_dict()))
        validator.validate(document)
        validate_engine_event(document)
        assert EngineEvent.from_dict(document) == event


@pytest.mark.parametrize("version, schema_version, protocol", [
    (1, CONTEXT_PACKET_SCHEMA_VERSION, context_request_format.PROTOCOL_VERSION),
    (2, CONTEXT_PACKET_KNOWLEDGE_SCHEMA_VERSION, context_request_format.KNOWLEDGE_PROTOCOL_VERSION),
])
def test_packet_schemas_pin_the_current_policy_constants(version, schema_version, protocol):
    schema = _schema(f"llm-wiki-qualified-context-packet-v{version}.schema.json")
    properties = schema["properties"]
    assert properties["schema_version"]["const"] == schema_version
    assert properties["request"]["properties"]["protocol"]["const"] == protocol
    generator = properties["basis"]["properties"]["generator"]["properties"]
    assert generator["context_protocol"]["const"] == protocol
    assert generator["policy_digest"]["const"] == context_packet._context_policy_digest(schema_version)
    path_policy = properties["path_policy"]["properties"]
    assert path_policy["policy_version"]["const"] == context_packet.CONTEXT_PACKET_PATH_POLICY_VERSION
    assert path_policy["policy_digest"]["const"] == context_packet._path_policy_digest()
    assert sorted(path_policy["field_counts"]["properties"]) == sorted(context_packet._PATH_COUNT_KEYS)
    assert properties["assurance"]["properties"]["level"]["const"] == context_packet.CONTEXT_PACKET_ASSURANCE_LEVEL


@pytest.mark.parametrize(
    "request_overrides",
    [
        {"protocol": "llm-wiki-context/v1"},
        {"protocol": "llm-wiki-context/v1", "format": "markdown", "prefer_fresh": True},
        {"protocol": "llm-wiki-context/v2", "knowledge_mode": "off"},
        {"protocol": "llm-wiki-context/v2", "knowledge_mode": "auto", "format": "markdown"},
        {"protocol": "llm-wiki-context/v2", "knowledge_mode": "auto", "prefer_fresh": True},
    ],
)
def test_built_packets_match_their_schema(tmp_path, monkeypatch, request_overrides):
    (tmp_path / "src").mkdir()
    (tmp_path / "src/accounts.py").write_text(
        'class Account:\n    """A customer account."""\n\n    balance: int\n', encoding="utf-8"
    )
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("GIT_CEILING_DIRECTORIES", str(tmp_path.parent))
    api.bootstrap_wiki("src", "docs/llm_wiki")
    request = {"budget_tokens": 32_000, "focus": ["all"], "format": "json", "filters": {}}
    request.update(request_overrides)

    packet = api.build_qualified_context("src", "docs/llm_wiki", request)

    payload = packet.to_payload()
    version = 2 if request["protocol"].endswith("/v2") else 1
    Draft202012Validator(
        _schema(f"llm-wiki-qualified-context-packet-v{version}.schema.json")
    ).validate(payload)
    _validate_packet_document(payload)


@pytest.mark.parametrize("version", [1, 2])
def test_context_response_success_is_the_packet_response(version):
    response = _schema(f"llm-wiki-context-response-v{version}.schema.json")
    packet = _schema(f"llm-wiki-qualified-context-packet-v{version}.schema.json")
    success = response["$defs"]["success"]
    packet_response = packet["properties"]["response"]
    assert success["properties"] == packet_response["properties"]
    # A packet binds source priorities; a plain protocol response does not.
    assert set(packet_response["required"]) - set(success["required"]) <= {"source_priorities"}
    for name, definition in response["$defs"].items():
        if name not in {"success", "error"}:
            assert definition == packet["$defs"][name], name


@pytest.mark.parametrize(
    "request_overrides",
    [
        {"protocol": "llm-wiki-context/v1"},
        {"protocol": "llm-wiki-context/v1", "format": "markdown", "prefer_fresh": True},
        {"protocol": "llm-wiki-context/v1", "filters": {"symbol": "Account"}},
        {"protocol": "llm-wiki-context/v2", "knowledge_mode": "off"},
        {"protocol": "llm-wiki-context/v2", "knowledge_mode": "auto", "prefer_fresh": True},
        {"protocol": "llm-wiki-context/v2", "knowledge_mode": "required", "format": "markdown"},
        {"protocol": "llm-wiki-context/v1", "focus": ["bogus"]},
        {"protocol": "llm-wiki-context/v2", "knowledge_mode": "auto", "budget_tokens": 0},
    ],
)
def test_emitted_context_responses_match_their_schema(
    tmp_path, monkeypatch, capsys, request_overrides
):
    (tmp_path / "src").mkdir()
    (tmp_path / "src/accounts.py").write_text(
        'class Account:\n    """A customer account."""\n\n    balance: int\n', encoding="utf-8"
    )
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("GIT_CEILING_DIRECTORIES", str(tmp_path.parent))
    api.bootstrap_wiki("src", "docs/llm_wiki")
    request = {"budget_tokens": 8000, "focus": ["all"], "format": "json", "filters": {}}
    request.update(request_overrides)
    (tmp_path / "request.json").write_text(json.dumps(request), encoding="utf-8")
    capsys.readouterr()
    monkeypatch.setattr(sys, "argv", [
        "llm-wiki", "context", "--request", "request.json",
        "--src-dir", "src", "--wiki-dir", "docs/llm_wiki",
    ])

    try:
        cli.main()
    except SystemExit:
        pass

    response = json.loads(capsys.readouterr().out)
    version = 2 if request["protocol"].endswith("/v2") else 1
    Draft202012Validator(_schema(f"llm-wiki-context-response-v{version}.schema.json")).validate(response)
    validate_context_response(response)
    assert response["ok"] is ("bogus" not in request["focus"] and request["budget_tokens"] > 0)


def test_query_formats_match_the_running_code():
    formats = query_result_format
    assert formats.DOCUMENTATION_QUERY_SCHEMA_VERSION == api.DOCUMENTATION_QUERY_SCHEMA_VERSION
    assert set(formats.DOCUMENTATION_QUERY_OPERATIONS) == set(api._DOCUMENTATION_QUERY_FIELDS)
    typed = set(api_types.DocumentationQueryResult.__annotations__)
    assert typed <= formats._QUERY_ENVELOPE_FIELDS | formats.QUERY_PAYLOAD_FIELDS
    assert set(formats.SEARCH_PAGE_KINDS) == set(search_service.SEARCH_KINDS)
    assert formats.SEARCH_RANKINGS["ranked-v1"] == search_rank.RANKING_VERSION
    assert formats.SEARCH_RANKINGS["ranked"] == search_lexical.RANKING_VERSION
    assert formats.SEARCH_RANKINGS["ranked-v2"] == search_lexical.RANKING_VERSION
    assert set(api_types.SearchResult.__annotations__) <= set(
        _schema("llm-wiki-search-result-v1.schema.json")["properties"]
    )

    query = _schema("llm-wiki-documentation-query-v1.schema.json")
    assert set(query["properties"]) == formats._QUERY_ENVELOPE_FIELDS | formats.QUERY_PAYLOAD_FIELDS
    assert query["properties"]["operation"]["enum"] == list(formats.DOCUMENTATION_QUERY_OPERATIONS)
    assert query["properties"]["cost"]["properties"]["scope"]["enum"] == list(formats.QUERY_COST_SCOPES)
    search = _schema("llm-wiki-search-result-v1.schema.json")
    assert search["properties"]["mode"]["enum"] == list(formats.SEARCH_MODES)
    assert search["$defs"]["ranked_match"]["properties"]["kind"]["enum"] == list(formats.SEARCH_PAGE_KINDS)


ORDERS = """class Order:
    \"\"\"A customer order.\"\"\"

    total: int

    def submit(self) -> None:
        self.validate()

    def validate(self) -> None:
        return None


def checkout() -> Order:
    order = Order()
    order.submit()
    return order
"""


@pytest.fixture
def orders_wiki(tmp_path, monkeypatch):
    (tmp_path / "src").mkdir()
    (tmp_path / "src/orders.py").write_text(ORDERS, encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("GIT_CEILING_DIRECTORIES", str(tmp_path.parent))
    api.bootstrap_wiki("src", "docs/llm_wiki")
    return tmp_path


@pytest.mark.parametrize(
    "request_body",
    [
        {"operation": "concept", "value": "llm-wiki://entities/Order"},
        {"operation": "explain", "value": "llm-wiki://modules/orders"},
        {"operation": "related", "value": "llm-wiki://entities/Order"},
        {"operation": "surface", "value": "entities/Order.md"},
        {"operation": "typed", "value": "llm-wiki://entities/Order"},
        {"operation": "symbol", "value": "submit", "allow_full_inventory": True},
        {"operation": "entrypoint", "value": "checkout", "allow_full_inventory": True},
        {"operation": "dependency", "value": "orders.py", "allow_full_inventory": True},
        {"operation": "impact", "paths": ["orders.py"]},
        {"operation": "concept", "value": "llm-wiki://entities/Missing"},
    ],
    ids=lambda body: f"{body['operation']}:{body.get('value', body.get('paths'))}",
)
def test_documentation_query_results_match_their_schema(orders_wiki, request_body):
    result = api.query_documentation(request_body, src_dir="src", wiki_dir="docs/llm_wiki")

    document = json.loads(json.dumps(result))
    Draft202012Validator(_schema("llm-wiki-documentation-query-v1.schema.json")).validate(document)
    query_result_format.validate_documentation_query_result(document)
    assert document["operation"] == request_body["operation"]


@pytest.mark.parametrize("mode", ["ranked", "ranked-v1", "ranked-v2", "substring"])
@pytest.mark.parametrize("options", [{}, {"discovery": "qualified-v1"}, {"limit": 1}])
def test_search_results_match_their_schema(orders_wiki, mode, options):
    result = api.search_wiki("order", src_dir="src", wiki_dir="docs/llm_wiki", mode=mode, **options)

    document = json.loads(json.dumps(result))
    assert document["schema_version"] == query_result_format.SEARCH_RESULT_SCHEMA_VERSION
    Draft202012Validator(_schema("llm-wiki-search-result-v1.schema.json")).validate(document)
    query_result_format.validate_search_result(document)
    assert document["results"]


def test_source_indexed_search_matches_its_schema(orders_wiki):
    result = api.search_wiki(
        "order", src_dir="src", wiki_dir="docs/llm_wiki", mode="ranked-v2", include_source=True
    )

    document = json.loads(json.dumps(result))
    assert "source_indexing" in document
    Draft202012Validator(_schema("llm-wiki-search-result-v1.schema.json")).validate(document)
    query_result_format.validate_search_result(document)


def test_surface_index_schema_matches_the_page_registry(tmp_path):
    schema = _schema("llm-wiki-surface-index-v1.schema.json")
    kinds = [entry.kind.value for entry in wiki_surface.iter_page_kinds()]

    assert schema["properties"]["schema_version"]["const"] == wiki_surface_index.WIKI_SURFACE_INDEX_SCHEMA_VERSION
    assert schema["$defs"]["page"]["properties"]["kind"]["enum"] == kinds
    assert list(schema["properties"]["counts"]["properties"]["by_kind"]["properties"]) == kinds
    media = schema["properties"]["counts"]["properties"]["assets"]["properties"]["by_media_type"]
    media_types = build_asset_index(tmp_path).counts["by_media_type"]
    assert isinstance(media_types, dict)
    assert set(media["properties"]) == set(media_types)
    conditions = {
        rule["if"]["properties"]["kind"]["const"]: rule["then"]["properties"]
        for rule in schema["$defs"]["page"]["allOf"]
    }
    assert list(conditions) == kinds
    for entry in wiki_surface.iter_page_kinds():
        rule = conditions[entry.kind.value]
        assert rule["role"] == {"const": entry.role.value}
        if entry.requires_page_id:
            assert rule["canonical_path"]["pattern"].startswith(f"^{entry.directory}/")
            assert rule["mcp_uri"]["pattern"].startswith(f"^llm-wiki://{entry.mcp_uri_kind}/")
        else:
            assert rule["canonical_path"] == {"const": wiki_surface.canonical_path(entry.kind)}
            assert rule["mcp_uri"] == {"const": wiki_surface.mcp_uri(entry.kind)}


def _check_surface_index(wiki):
    document = json.loads((wiki / wiki_surface_index.SURFACE_INDEX_FILENAME).read_text(encoding="utf-8"))
    Draft202012Validator(_schema("llm-wiki-surface-index-v1.schema.json")).validate(document)
    surface_index_format.validate_surface_index(document)
    return document


def test_written_surface_indexes_match_their_schema(orders_wiki):
    wiki = orders_wiki / "docs/llm_wiki"
    bootstrapped = _check_surface_index(wiki)
    assert {"entities/Order.md", "modules/orders.md"} <= {page["canonical_path"] for page in bootstrapped["pages"]}

    (wiki / "guides").mkdir(exist_ok=True)
    (wiki / "guides/tour.md").write_text("# Tour\n\n![Home](../assets/guides/tour/home.png)\n", encoding="utf-8")
    (wiki / "assets/guides/tour").mkdir(parents=True)
    (wiki / "assets/guides/tour/home.png").write_bytes(b"\x89PNG\r\n\x1a\n")
    (wiki / "assets/guides/tour/notes.txt").write_text("draft\n", encoding="utf-8")
    (orders_wiki / "src/orders.py").write_text(ORDERS + "\n\nclass Refund:\n    amount: int\n", encoding="utf-8")
    api.sync_wiki("src", "docs/llm_wiki")

    synced = _check_surface_index(wiki)
    assert synced["assets"]["by_page"] == {"guides/tour.md": ["assets/guides/tour/home.png"]}
    assert synced["assets"]["unreferenced"] == ["assets/guides/tour/notes.txt"]
    assert "entities/Refund.md" in {page["canonical_path"] for page in synced["pages"]}


def test_extract_schema_matches_the_running_code():
    schema = _schema("llm-wiki-extract-v1.schema.json")
    details = schema["$defs"]["data_flow_details"]
    limits = data_flow.data_flow_effective_limits(flow_depth=entrypoints.DEFAULT_FLOW_DEPTH)

    assert schema["properties"]["schema_version"]["const"] == contracts.EXTRACT_SCHEMA_VERSION
    result = api_types.ExtractSourceResult
    assert set(schema["properties"]) == result.__required_keys__ | result.__optional_keys__
    assert details["properties"]["schema_version"]["const"] == contracts.EXTRACT_DATA_FLOW_DETAILS_SCHEMA_VERSION
    assert list(details["properties"]) == list(extract_format.DATA_FLOW_DETAILS_FIELDS)
    assert list(details["properties"]["coverage"]["properties"]) == list(
        extract_format.DATA_FLOW_DETAILS_COVERAGE_FIELDS
    )
    assert list(details["properties"]["effective_limits"]["properties"]) == list(limits)
    assert list(limits) == list(extract_format.DATA_FLOW_EFFECTIVE_LIMIT_FIELDS)
    assert limits["flows_per_extract"] == data_flow.DEFAULT_DATA_FLOW_DETAILS_FLOW_LIMIT
    reasons = {
        rule["if"]["properties"]["state"]["const"]: rule["then"]["properties"]["reason"]["const"]
        for rule in details["allOf"]
    }
    assert reasons == extract_format.DATA_FLOW_DETAILS_STATES


EXTRACT_PROJECT = {
    "api.py": 'from repo import save\n\n__all__ = ["run"]\n\n\ndef run(payload):\n    return save(payload)\n',
    "repo.py": "class Store:\n    pass\n\n\ndef save(payload):\n    return payload\n",
    "scripts/deploy.sh": "#!/bin/sh\necho deploy\n",
}


def _check_extract_payload(payload: object) -> dict[str, Any]:
    Draft202012Validator(_schema("llm-wiki-extract-v1.schema.json")).validate(payload)
    extract_format.validate_extract_payload(payload)
    assert isinstance(payload, dict)
    return payload


@pytest.mark.parametrize(
    ("files", "options", "state"),
    [
        (EXTRACT_PROJECT, {}, "not_evaluated"),
        (EXTRACT_PROJECT, {"summary": True}, "not_evaluated"),
        (EXTRACT_PROJECT, {"deep": True}, "evaluated"),
        (EXTRACT_PROJECT, {"deep": True, "summary": True}, "evaluated"),
        ({"scripts/deploy.sh": "#!/bin/sh\n"}, {"deep": True}, "unsupported"),
    ],
    ids=["shallow", "summary", "deep", "deep-summary", "unsupported"],
)
def test_extract_payloads_match_their_schema(tmp_path, monkeypatch, files, options, state):
    for name, text in files.items():
        (tmp_path / name).parent.mkdir(parents=True, exist_ok=True)
        (tmp_path / name).write_text(text, encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    payload = _check_extract_payload(api.extract_source(".", **options))

    assert payload["data_flow_details"]["state"] == state
    assert payload["unsupported_sources"]["shell"]["paths"] == ["scripts/deploy.sh"]
    if options.get("deep") and "api.py" in files:
        assert [entry["id"] for entry in payload["entrypoints"]] == [flow["id"] for flow in payload["data_flows"]]


def test_cli_extract_output_matches_its_schema(tmp_path, monkeypatch, capsys):
    for name, text in EXTRACT_PROJECT.items():
        (tmp_path / name).parent.mkdir(parents=True, exist_ok=True)
        (tmp_path / name).write_text(text, encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    capsys.readouterr()
    monkeypatch.setattr(sys, "argv", ["llm-wiki", "extract", "--deep", "--src-dir", "."])

    cli.main()

    payload = _check_extract_payload(json.loads(capsys.readouterr().out))
    assert set(payload["inventory"]) == {"api.py", "repo.py"}


def test_maintenance_status_schema_matches_the_running_code():
    schema = _schema("llm-wiki-maintenance-status-v1.schema.json")
    state = _schema("llm-wiki-maintenance-state-v1.schema.json")
    fmt = maintenance_status_format
    observation = state["properties"]["observations"]["additionalProperties"]["properties"]
    hints = get_type_hints(api_types.MaintenanceRecordResult)

    assert fmt.MAINTENANCE_STATUS_SCHEMA_VERSION == maintenance_status.SCHEMA
    assert (fmt.STATUS_MAX_BYTES, fmt.STATUS_MAX_RECORDS, fmt.STATUS_HISTORY_LIMIT) == (
        maintenance_status.MAX_BYTES, maintenance_status.MAX_RECORDS, maintenance_status.HISTORY_LIMIT,
    )
    assert fmt.STATUS_LIMITATIONS == maintenance_status.LIMITATIONS
    assert set(fmt.ANALYSIS_SCOPES) == maintenance_status.ANALYSIS_SCOPES
    assert set(fmt.SUMMARY_FIELDS) == maintenance_status.SUMMARY_FIELDS
    assert fmt.MAX_LIMIT == maintenance_queue.MAX_QUEUE_LIMIT
    assert set(fmt.STATUS_FIELDS) == set(api_types.MaintenanceStatusResult.__required_keys__)
    assert set(fmt.RECORD_FIELDS) == set(api_types.MaintenanceRecordResult.__required_keys__)
    assert set(get_args(hints["qualification"])) == set(fmt.RECORD_QUALIFICATIONS)
    assert set(get_args(hints["recorded_status"])) == set(fmt.RECORD_STATUSES)
    assert list(schema["properties"]) == [*fmt.STATUS_FIELDS, *fmt.STATUS_OPTIONAL_FIELDS]
    assert schema["$defs"]["coordinate"] == observation["coordinate"]
    assert schema["$defs"]["target"] == observation["target"]
    assert schema["properties"]["limitations"]["const"] == list(maintenance_status.LIMITATIONS)


def _check_maintenance_status(payload: object) -> dict[str, Any]:
    Draft202012Validator(_schema("llm-wiki-maintenance-status-v1.schema.json")).validate(payload)
    maintenance_status_format.validate_maintenance_status(payload)
    assert isinstance(payload, dict)
    return payload


def test_maintenance_status_payloads_match_their_schema(tmp_path, monkeypatch, capsys):
    from llm_wiki_cli.services.sync_manifest import SyncManifest

    monkeypatch.chdir(tmp_path)
    (tmp_path / "src").mkdir()
    (tmp_path / "src/policy.py").write_text(POLICY_SOURCE, encoding="utf-8")
    api.bootstrap_wiki("src", "wiki", knowledge_format="v1")
    unadopted = _check_maintenance_status(api.get_maintenance_status("src", "wiki"))
    assert unadopted["availability"] == "unadopted"

    api.adopt_maintenance("src", "wiki", recovery_dir="recovery")
    live = _check_maintenance_status(api.get_maintenance_status("src", "wiki"))
    record = live["records"][0]
    api.acknowledge_maintenance(
        "src", "wiki", record_id=record["record_id"], expected_state_hash=live["state_hash"],
        expected_basis=record["expected_basis"], actor_kind="agent", actor_id="review-agent",
    )
    reviewed = _check_maintenance_status(api.get_maintenance_status("src", "wiki"))
    snapshot = _check_maintenance_status(api.get_maintenance_status("src", "wiki", live=False))
    selected = _check_maintenance_status(
        api.get_maintenance_status("src", "wiki", record_id=record["record_id"])
    )
    limited = _check_maintenance_status(api.get_maintenance_status("src", "wiki", limit=1))
    capsys.readouterr()
    monkeypatch.setattr(
        sys, "argv", ["llm-wiki", "maintenance", "status", "--src-dir", "src", "--wiki-dir", "wiki", "--format", "json"]
    )
    cli.main()
    emitted = _check_maintenance_status(json.loads(capsys.readouterr().out))
    owner = SyncManifest.load(tmp_path / "wiki").maintenance_state
    report = maintenance_status.build_maintenance_status(
        owner, maintenance_status.marker_from_validated_state(owner)
    )
    page = _check_maintenance_status(report.for_path(record["target"]["canonical_path"]))

    assert {row["qualification"] for row in live["records"]} == {"current-capture"}
    acknowledged = {row["record_id"]: row for row in reviewed["records"]}[record["record_id"]]
    assert acknowledged["effective_status"] == "acknowledged"
    assert acknowledged["acknowledgment"]["actor"]["actor_id"] == "review-agent"
    assert {row["qualification"] for row in snapshot["records"]} == {"snapshot"}
    assert [row["record_id"] for row in selected["records"]] == [record["record_id"]]
    assert limited["bounds"]["returned"] == 1
    assert limited["bounds"]["truncated"] is (len(live["records"]) > 1)
    assert emitted == reviewed
    assert page["summary"]["total"] == page["bounds"]["total"] >= 1


def test_maintenance_queue_schema_matches_the_running_code():
    schema = _schema("llm-wiki-maintenance-queue-v1.schema.json")
    status = _schema("llm-wiki-maintenance-status-v1.schema.json")
    fmt = maintenance_queue_format

    assert fmt.MAINTENANCE_QUEUE_SCHEMA_VERSION == maintenance_queue.QUEUE_SCHEMA
    assert (fmt.MIN_QUEUE_LIMIT, fmt.MAX_QUEUE_LIMIT) == (
        maintenance_queue.MIN_QUEUE_LIMIT, maintenance_queue.MAX_QUEUE_LIMIT,
    )
    assert set(fmt.FRESHNESS_STATES) == set(maintenance_queue._FRESHNESS_WEIGHT)
    assert set(fmt.QUEUE_FIELDS) == set(api_types.MaintenanceQueueResult.__required_keys__)
    assert (fmt.QUEUE_MAX_DETAILS, fmt.QUEUE_MAX_BYTES) == (
        maintenance_status.MAX_RECORDS, maintenance_status.MAX_BYTES,
    )
    for name in ("coordinate", "target", "summary"):
        expected = {key: value for key, value in status["$defs"][name].items() if key != "description"}
        actual = {key: value for key, value in schema["$defs"][name].items() if key != "description"}
        assert actual == expected, name


def _check_maintenance_queue(payload: object) -> dict[str, Any]:
    Draft202012Validator(_schema("llm-wiki-maintenance-queue-v1.schema.json")).validate(payload)
    maintenance_queue_format.validate_maintenance_queue(payload)
    assert isinstance(payload, dict)
    return payload


def test_maintenance_queue_reports_match_their_schema(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "src").mkdir()
    (tmp_path / "src/policy.py").write_text(POLICY_SOURCE, encoding="utf-8")
    api.bootstrap_wiki("src", "wiki", knowledge_format="v1")
    unadopted = _check_maintenance_queue(api.build_maintenance_queue("src", "wiki"))
    limited = _check_maintenance_queue(api.build_maintenance_queue("src", "wiki", limit=1))
    api.adopt_maintenance("src", "wiki", recovery_dir="recovery")
    adopted = _check_maintenance_queue(api.build_maintenance_queue("src", "wiki"))
    capsys.readouterr()
    monkeypatch.setattr(
        sys, "argv", ["llm-wiki", "queue", "--src-dir", "src", "--wiki-dir", "wiki", "--format", "json"]
    )
    cli.main()
    emitted = _check_maintenance_queue(json.loads(capsys.readouterr().out))

    custody = unadopted["qualification"]["ordinary_review_custody"]
    assert custody["availability"] == "unadopted"
    assert any("coverage_gaps" in item for item in unadopted["items"])
    assert limited["returned"] == min(1, unadopted["total"])
    assert adopted["qualification"]["ordinary_review_custody"]["durable_owner_available"]
    assert any("maintenance" in item for item in adopted["items"])
    assert emitted == adopted


def _check_ledger_documents(stem: str, documents: list[object]) -> None:
    validator = Draft202012Validator(_schema(f"llm-wiki-maintenance-{stem}-v1.schema.json"))
    python = PYTHON_VALIDATORS[f"llm-wiki-maintenance-{stem}/v1"]
    unique = {json.dumps(document, sort_keys=True): document for document in documents}
    assert unique, stem
    for document in unique.values():
        validator.validate(document)
        python(document)


def test_maintenance_ledger_documents_match_their_schemas(tmp_path, monkeypatch):
    from llm_wiki_cli.services.sync_manifest import SyncManifest

    validated: dict[str, list[object]] = {"maintenance-event-v1": [], "maintenance-basis-v1": []}
    original = maintenance_state.MaintenanceCore.validate_schema

    def recording(self, name, value):
        original(self, name, value)
        if name in validated:
            validated[name].append(json.loads(json.dumps(value)))

    monkeypatch.setattr(maintenance_state.MaintenanceCore, "validate_schema", recording)
    monkeypatch.chdir(tmp_path)
    (tmp_path / "src").mkdir()
    (tmp_path / "src/policy.py").write_text(POLICY_SOURCE, encoding="utf-8")
    api.bootstrap_wiki("src", "wiki", knowledge_format="v1")
    api.adopt_maintenance("src", "wiki", recovery_dir="recovery")
    (tmp_path / "src/policy.py").write_text(POLICY_SOURCE + "\n\ndef extra():\n    return 1\n", encoding="utf-8")
    api.sync_wiki("src", "wiki")
    live = _check_maintenance_status(api.get_maintenance_status("src", "wiki"))
    record = live["records"][0]
    api.acknowledge_maintenance(
        "src", "wiki", record_id=record["record_id"], expected_state_hash=live["state_hash"],
        expected_basis=record["expected_basis"], actor_kind="agent", actor_id="review-agent",
    )

    wiki = tmp_path / "wiki"
    marker = json.loads((wiki / ".llm-wiki-maintenance-adoption.json").read_text(encoding="utf-8"))
    state = SyncManifest.load(wiki).maintenance_state
    assert state is not None
    knowledge = json.loads((wiki / ".llm-wiki-knowledge.json").read_text(encoding="utf-8"))
    projections = [
        concept["extensions"][maintenance_projection.RECORD_KEY] for concept in knowledge["concepts"]
    ]
    bases = [
        basis
        for record_id, observation in state["observations"].items()
        for basis in (
            observation["basis"],
            state["records"][record_id]["last_present_basis"],
            *(ack["basis"] for ack in state["records"][record_id]["acknowledgment_history"]),
        )
    ]
    events = validated["maintenance-event-v1"]

    _check_ledger_documents("adoption", [marker])
    _check_ledger_documents("state", [state])
    _check_ledger_documents("binding", [knowledge["extensions"][maintenance_projection.BINDING_KEY]])
    _check_ledger_documents("record-binding", projections)
    _check_ledger_documents("basis", [*bases, *validated["maintenance-basis-v1"]])
    _check_ledger_documents("event", events)
    assert any(projection["records"] for projection in projections)
    assert {"acknowledge", "observe"} <= {event["kind"] for event in events}  # type: ignore[index]
    assert any(row["status"] == "acknowledged" for row in state["records"].values())
