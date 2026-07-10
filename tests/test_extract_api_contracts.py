from __future__ import annotations

import json
import textwrap
import types

import pytest

from llm_wiki_cli import cli
from llm_wiki_cli.commands import extract_cmd
from llm_wiki_cli.services.api_contracts import ApiContractError


def _write_source(tmp_path) -> None:
    (tmp_path / "app.py").write_text(
        textwrap.dedent(
            """\
            from fastapi import FastAPI

            app = FastAPI()


            @app.get("/things")
            def list_things():
                return []
            """
        ),
        encoding="utf-8",
    )


def _write_openapi(tmp_path, filename: str = "contracts/openapi.json") -> str:
    target = tmp_path / filename
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps(
            {
                "openapi": "3.1.0",
                "info": {"title": "Example", "version": "1"},
                "paths": {
                    "/things": {
                        "get": {
                            "operationId": "listThings",
                            "parameters": [
                                {
                                    "name": "limit",
                                    "in": "query",
                                    "required": False,
                                    "schema": {"type": "integer"},
                                }
                            ],
                            "responses": {
                                "200": {
                                    "description": "ok",
                                    "content": {
                                        "application/json": {
                                            "schema": {"type": "array"}
                                        }
                                    },
                                }
                            },
                        }
                    }
                },
            }
        ),
        encoding="utf-8",
    )
    return filename


def test_extract_parser_accepts_deep_openapi_file():
    args = cli._build_parser().parse_args(
        ["extract", "--deep", "--openapi-file", "contracts/openapi.yaml"]
    )

    assert args.deep is True
    assert args.openapi_file == "contracts/openapi.yaml"


def test_extract_run_forwards_openapi_file(tmp_path, monkeypatch, capsys):
    seen = {}

    def fake_build_extract_payload(src_dir, **kwargs):
        seen["src_dir"] = src_dir
        seen["openapi_file"] = kwargs["openapi_file"]
        return extract_cmd.ExtractPayloadResult(
            {"schema_version": "llm-wiki-extract/v1", "inventory": {}},
            inventory_count=0,
            docker_count=0,
        )

    monkeypatch.setattr(extract_cmd, "build_extract_payload", fake_build_extract_payload)
    args = types.SimpleNamespace(
        src_dir=str(tmp_path),
        changed=False,
        summary=False,
        paths=None,
        deep=True,
        package=None,
        include_empty=False,
        output=None,
        read_only=False,
        allow_external_src=True,
        helper_cache_dir=None,
        include_tests=None,
        openapi_file="contracts/openapi.yaml",
    )

    extract_cmd.run(args)

    assert seen == {
        "src_dir": str(tmp_path),
        "openapi_file": "contracts/openapi.yaml",
    }
    assert json.loads(capsys.readouterr().out)["inventory"] == {}


def test_explicit_openapi_requires_deep(tmp_path):
    _write_source(tmp_path)
    openapi_file = _write_openapi(tmp_path)

    with pytest.raises(ValueError, match=r"--openapi-file requires --deep"):
        extract_cmd.build_extract_payload(
            str(tmp_path),
            openapi_file=openapi_file,
            allow_external_src=True,
        )


def test_deep_extract_always_exposes_static_api_contract_shape(tmp_path):
    (tmp_path / "plain.py").write_text("def helper():\n    return 1\n", encoding="utf-8")

    payload = extract_cmd.build_extract_payload(
        str(tmp_path), deep=True, allow_external_src=True
    ).payload

    assert payload["api_contracts"] == {
        "source": "static",
        "applications": [],
        "operations": [],
        "diagnostics": [],
        "excluded_counts": {
            "test_source": 0,
            "schema_excluded": 0,
            "conditional": 0,
        },
    }


def test_openapi_is_resolved_from_source_root_and_authoritative(tmp_path):
    _write_source(tmp_path)
    openapi_file = _write_openapi(tmp_path)

    contracts = extract_cmd.build_extract_payload(
        str(tmp_path),
        deep=True,
        openapi_file=openapi_file,
        allow_external_src=True,
    ).payload["api_contracts"]

    assert contracts["source"] == "openapi"
    assert contracts["openapi"]["path"] == "contracts/openapi.json"
    assert contracts["openapi"]["format"] == "json"
    assert [
        (operation["method"], operation["path"], operation["operation_id"])
        for operation in contracts["operations"]
    ] == [("GET", "/things", "listThings")]
    assert contracts["operations"][0]["parameters"][0]["wire_name"] == "limit"


def test_openapi_must_remain_inside_source_root(tmp_path):
    source = tmp_path / "source"
    source.mkdir()
    _write_source(source)
    outside = _write_openapi(tmp_path, "openapi.json")

    with pytest.raises(ApiContractError, match="outside source root"):
        extract_cmd.build_extract_payload(
            str(source),
            deep=True,
            openapi_file=f"../{outside}",
            allow_external_src=True,
        )


def test_http_entrypoint_is_enriched_with_authoritative_routes(
    tmp_path, monkeypatch
):
    _write_source(tmp_path)
    contracts = {
        "source": "openapi",
        "applications": [],
        "operations": [
            {
                "method": "GET",
                "path": "/things",
                "operation_id": "listThings",
                "handler": {"file": "app.py", "symbol": "list_things"},
            },
            {
                "method": "POST",
                "path": "/things",
                "operation_id": "createThing",
                "handler": {"file": "app.py", "symbol": "list_things"},
            },
        ],
        "diagnostics": [],
        "excluded_counts": {},
    }
    monkeypatch.setattr(extract_cmd, "build_api_contracts", lambda *a, **k: contracts)

    payload = extract_cmd.build_extract_payload(
        str(tmp_path), deep=True, allow_external_src=True
    ).payload

    entry = next(
        item
        for item in payload["entrypoints"]
        if item["category"] == "http" and item["symbol"] == "list_things"
    )
    assert entry["routes"] == [
        {"method": "GET", "path": "/things", "operation_id": "listThings"},
        {"method": "POST", "path": "/things", "operation_id": "createThing"},
    ]


def test_openapi_extract_never_imports_target_application(tmp_path):
    (tmp_path / "app.py").write_text(
        "raise RuntimeError('must not execute')\n", encoding="utf-8"
    )
    openapi_file = _write_openapi(tmp_path)

    result = extract_cmd.build_extract_payload(
        str(tmp_path),
        deep=True,
        openapi_file=openapi_file,
        allow_external_src=True,
    )

    assert result.payload["api_contracts"]["source"] == "openapi"
