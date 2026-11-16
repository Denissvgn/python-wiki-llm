"""Published schemas, shared conformance cases and Python validators agree."""

from __future__ import annotations

import io
import json
import sys
from collections.abc import Callable
from importlib import resources
from typing import Any

import pytest
from jsonschema import Draft202012Validator

from llm_wiki_cli import api, cli
from llm_wiki_cli.services import context_packet, context_request_format
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
    SyncRequest,
    validate_context_response,
    validate_engine_event,
)
from tests.notes_pack import NOTES_PACK

SCHEMAS = resources.files("llm_wiki_cli.schemas")
CONFORMANCE = SCHEMAS.joinpath("conformance")

def _validate_packet_document(document: object) -> None:
    """Validate a packet document through its canonical bytes."""
    if not isinstance(document, dict):
        raise ValueError("a packet is a JSON object")
    validate_context_packet(context_packet._encode_packet_payload(document))


#: Python validators that must accept exactly the valid cases of a format.
PYTHON_VALIDATORS: dict[str, Callable[[object], None]] = {
    ENGINE_EVENT_SCHEMA_VERSION: validate_engine_event,
    CONTEXT_PACKET_SCHEMA_VERSION: _validate_packet_document,
    CONTEXT_PACKET_KNOWLEDGE_SCHEMA_VERSION: _validate_packet_document,
    **{protocol: validate_context_response for protocol in CONTEXT_RESPONSE_PROTOCOLS},
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
    } <= set(files)
    cases_schema = Draft202012Validator(_schema("llm-wiki-conformance-cases-v1.schema.json"))
    for name in files:
        document = _json(CONFORMANCE.joinpath(name))
        cases_schema.validate(document)
        assert name == document["schema"].replace(".schema.json", ".cases.json")
        schema = _schema(document["schema"])
        # A format names its version in schema_version, or in protocol for
        # the context protocol responses.
        version_key = "schema_version" if "schema_version" in schema["properties"] else "protocol"
        assert schema["properties"][version_key]["const"] == document["format"]
        assert schema["$id"].endswith("/" + document["schema"])
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
    with pytest.raises(Exception):
        engine.sync(SyncRequest(source_root="missing", wiki_root="wiki"))

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
