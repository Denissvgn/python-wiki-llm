"""Published schemas, shared conformance cases and Python validators agree."""

from __future__ import annotations

import io
import json
from collections.abc import Callable
from importlib import resources
from typing import Any

import pytest
from jsonschema import Draft202012Validator

from llm_wiki_cli import api
from llm_wiki_cli.engine import (
    ENGINE_CAPABILITIES_SCHEMA_VERSION,
    ENGINE_EVENT_SCHEMA_VERSION,
    CODE_DOCS_PACK,
    Engine,
    EngineEvent,
    Host,
    NoProcessHost,
    SyncRequest,
    validate_engine_event,
)
from tests.notes_pack import NOTES_PACK

SCHEMAS = resources.files("llm_wiki_cli.schemas")
CONFORMANCE = SCHEMAS.joinpath("conformance")

#: Python validators that must accept exactly the valid cases of a format.
PYTHON_VALIDATORS: dict[str, Callable[[object], None]] = {
    ENGINE_EVENT_SCHEMA_VERSION: validate_engine_event,
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
    assert {"llm-wiki-engine-event-v1.cases.json", "llm-wiki-engine-capabilities-v1.cases.json"} <= set(files)
    cases_schema = Draft202012Validator(_schema("llm-wiki-conformance-cases-v1.schema.json"))
    for name in files:
        document = _json(CONFORMANCE.joinpath(name))
        cases_schema.validate(document)
        assert name == document["schema"].replace(".schema.json", ".cases.json")
        schema = _schema(document["schema"])
        assert schema["properties"]["schema_version"]["const"] == document["format"]
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
    assert validator.is_valid(case["document"]) is case["valid"]
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
