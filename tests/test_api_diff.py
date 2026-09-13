"""Versioned exported-contract cases; no application imports or builds."""

import json
import copy
import sys
from pathlib import Path

import pytest

from llm_wiki_cli import cli
from llm_wiki_cli.services.api_contracts import ApiContractError
from llm_wiki_cli.services.api_diff import compare_openapi, render_markdown

CORPUS = json.loads(
    (Path(__file__).parent / "fixtures/api_diff/corpus-v1.json").read_text()
)


@pytest.mark.parametrize("case", CORPUS["cases"], ids=lambda case: case["id"])
def test_declared_compatibility_corpus(case, tmp_path):
    for name in ("baseline", "candidate"):
        (tmp_path / f"{name}.json").write_text(json.dumps(case[name]))
    report = compare_openapi("baseline.json", "candidate.json", source_root=tmp_path)
    assert report["breaking_count"] == case["expected_breaking"]
    assert report == compare_openapi(
        "baseline.json", "candidate.json", source_root=tmp_path
    )
    assert report["baseline"]["document_id"].startswith("sha256:")
    assert render_markdown(report) == render_markdown(report)
    if case["id"] in {
        "enum-narrowing",
        "composition",
        "cycle",
        "unresolved-path",
        "unresolved-response",
    }:
        assert report["status"] == "advisory"


def test_gate_exit_and_source_containment(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    case = CORPUS["cases"][1]
    for name in ("baseline", "candidate"):
        (tmp_path / f"{name}.json").write_text(json.dumps(case[name]))
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "llm-wiki",
            "api-diff",
            "--baseline",
            "baseline.json",
            "--candidate",
            "candidate.json",
        ],
    )
    with pytest.raises(SystemExit) as exc:
        cli.main()
    assert exc.value.code == 1
    assert json.loads(capsys.readouterr().out)["status"] == "breaking"
    with pytest.raises(ApiContractError):
        compare_openapi("../outside.json", "candidate.json", source_root=tmp_path)


@pytest.mark.parametrize("path_item", [None, {"get": None}])
def test_malformed_candidate_is_unknown_instead_of_a_confirmed_removal(
    tmp_path, path_item
):
    baseline = {
        "openapi": "3.1.0",
        "paths": {"/items": {"get": {"responses": {"200": {"description": "OK"}}}}},
    }
    candidate = {"openapi": "3.1.0", "paths": {"/items": path_item}}
    for name, document in (("baseline", baseline), ("candidate", candidate)):
        (tmp_path / f"{name}.json").write_text(json.dumps(document))
    report = compare_openapi("baseline.json", "candidate.json", source_root=tmp_path)
    assert report["status"] == "advisory"
    assert report["breaking_count"] == 0


@pytest.mark.parametrize("schema_type", ["string", "array", "object"])
def test_inapplicable_schema_keywords_do_not_add_request_requirements(
    tmp_path, schema_type
):
    schema = {"type": schema_type}
    if schema_type == "array":
        schema["items"] = {"type": "string"}
    baseline = {
        "openapi": "3.1.0",
        "paths": {
            "/items": {
                "post": {
                    "requestBody": {
                        "content": {"application/json": {"schema": schema}}
                    },
                    "responses": {"200": {"description": "OK"}},
                }
            }
        },
    }
    candidate = copy.deepcopy(baseline)
    changed = candidate["paths"]["/items"]["post"]["requestBody"]["content"][
        "application/json"
    ]["schema"]
    if schema_type == "object":
        changed["items"] = {"required": ["ignored"]}
    else:
        changed["required"] = ["ignored"]
        changed["properties"] = {"ignored": {"type": "object", "required": ["nested"]}}
    for name, document in (("baseline", baseline), ("candidate", candidate)):
        (tmp_path / f"{name}.json").write_text(json.dumps(document))
    report = compare_openapi("baseline.json", "candidate.json", source_root=tmp_path)
    assert report["breaking_count"] == 0


@pytest.mark.parametrize("side", ["baseline", "candidate"])
@pytest.mark.parametrize(
    "malformed",
    [
        {"parameters": None},
        {"parameters": [None]},
        {"parameters": [{"in": "query", "name": "q", "required": "false"}]},
        {"parameters": [{"in": "path", "name": "missing", "required": True}]},
        {"parameters": [{"in": "query", "name": "q"}, {"in": "query", "name": "q"}]},
        {"requestBody": {"required": "false", "content": {"application/json": {}}}},
        {"responses": {"200": None}},
        {"responses": {}},
    ],
)
def test_malformed_wire_evidence_cannot_prove_a_break(tmp_path, side, malformed):
    baseline = {
        "openapi": "3.1.0",
        "paths": {
            "/items": {
                "get": {
                    "responses": {"200": {"description": "OK"}},
                }
            }
        },
    }
    candidate = copy.deepcopy(baseline)
    candidate["paths"]["/items"]["get"]["parameters"] = [
        {"in": "query", "name": "q", "required": True, "schema": {"type": "string"}},
    ]
    documents = {"baseline": baseline, "candidate": candidate}
    documents[side]["paths"]["/items"]["get"].update(malformed)
    for name, document in documents.items():
        (tmp_path / f"{name}.json").write_text(json.dumps(document))
    report = compare_openapi("baseline.json", "candidate.json", source_root=tmp_path)
    assert report["status"] == "advisory"
    assert report["breaking_count"] == 0
    assert any(f["code"] == "unresolved-contract" for f in report["findings"])


def test_referenced_readonly_object_has_no_required_request_fields(tmp_path):
    baseline = {
        "openapi": "3.1.0",
        "paths": {
            "/items": {
                "post": {
                    "requestBody": {
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "server": {
                                            "$ref": "#/components/schemas/Server"
                                        }
                                    },
                                }
                            }
                        }
                    },
                    "responses": {"200": {"description": "OK"}},
                }
            }
        },
        "components": {
            "schemas": {
                "Server": {
                    "readOnly": True,
                    "type": "object",
                    "properties": {"id": {"type": "string"}},
                }
            }
        },
    }
    candidate = copy.deepcopy(baseline)
    candidate["components"]["schemas"]["Server"]["required"] = ["id"]
    for name, document in (("baseline", baseline), ("candidate", candidate)):
        (tmp_path / f"{name}.json").write_text(json.dumps(document))
    report = compare_openapi("baseline.json", "candidate.json", source_root=tmp_path)
    assert report["breaking_count"] == 0
    assert not any(f["code"] == "required-input-added" for f in report["findings"])


def test_unknown_operation_does_not_hide_break_in_a_path_prefix(tmp_path):
    baseline = {
        "openapi": "3.1.0",
        "paths": {
            path: {
                "get": {
                    "responses": {"200": {"description": "OK"}},
                }
            }
            for path in ("/items", "/items/child")
        },
    }
    candidate = copy.deepcopy(baseline)
    candidate["paths"]["/items"]["get"]["responses"] = {
        "404": {"description": "Missing"}
    }
    candidate["paths"]["/items/child"]["get"]["parameters"] = [{"$ref": "#/missing"}]
    for name, document in (("baseline", baseline), ("candidate", candidate)):
        (tmp_path / f"{name}.json").write_text(json.dumps(document))
    report = compare_openapi("baseline.json", "candidate.json", source_root=tmp_path)
    assert report["breaking_count"] == 1
    assert any(
        f["code"] == "success-response-removed" and f["severity"] == "breaking"
        for f in report["findings"]
    )


@pytest.mark.parametrize("side", ["baseline", "candidate"])
@pytest.mark.parametrize("location", ["parameter", "requestBody", "response"])
def test_nested_unresolved_evidence_is_scoped_to_its_operation(
    tmp_path, side, location
):
    baseline = {
        "openapi": "3.1.0",
        "paths": {
            path: {"post": {"responses": {"200": {"description": "OK"}}}}
            for path in ("/items", "/items.requestBody", "/items/child")
        },
    }
    candidate = copy.deepcopy(baseline)
    for item in candidate["paths"].values():
        item["post"]["parameters"] = [
            {
                "in": "query",
                "name": "q",
                "required": True,
                "schema": {"type": "string"},
            },
        ]
    documents = {"baseline": baseline, "candidate": candidate}
    operation = documents[side]["paths"]["/items"]["post"]
    schema = {"type": "array", "items": {"$ref": "#/components/schemas/Missing"}}
    if location == "parameter":
        operation.setdefault("parameters", []).append(
            {"in": "query", "name": "filter", "schema": schema}
        )
    elif location == "requestBody":
        operation["requestBody"] = {"content": {"application/json": {"schema": schema}}}
    else:
        operation["responses"]["200"]["content"] = {
            "application/json": {"schema": schema}
        }
    for name, document in documents.items():
        (tmp_path / f"{name}.json").write_text(json.dumps(document))
    report = compare_openapi("baseline.json", "candidate.json", source_root=tmp_path)
    breaking = [f for f in report["findings"] if f["severity"] == "breaking"]
    assert {f["operation"] for f in breaking} == {
        "POST /items.requestBody",
        "POST /items/child",
    }
    assert report["breaking_count"] == 2


@pytest.mark.parametrize("operation_name", ["X-Token", "x-token"])
@pytest.mark.parametrize("newly_required", [False, True])
def test_inherited_header_identity_does_not_invent_a_new_requirement(
    tmp_path, operation_name, newly_required
):
    baseline = {
        "openapi": "3.1.0",
        "paths": {
            "/items": {
                "parameters": [
                    {
                        "in": "header",
                        "name": "X-Token",
                        "required": True,
                        "schema": {"type": "string"},
                    },
                ],
                "get": {
                    "parameters": [
                        {
                            "in": "header",
                            "name": operation_name,
                            "required": False,
                            "schema": {"type": "string"},
                        },
                    ],
                    "responses": {"200": {"description": "OK"}},
                },
            },
        },
    }
    candidate = copy.deepcopy(baseline)
    candidate["paths"]["/items"]["get"]["parameters"][0]["required"] = newly_required
    for name, document in (("baseline", baseline), ("candidate", candidate)):
        (tmp_path / f"{name}.json").write_text(json.dumps(document))
    report = compare_openapi("baseline.json", "candidate.json", source_root=tmp_path)
    assert report["breaking_count"] == int(
        newly_required and operation_name == "X-Token"
    )
    if operation_name == "x-token":
        assert any(f["code"] == "ambiguous-wire-input" for f in report["findings"])
