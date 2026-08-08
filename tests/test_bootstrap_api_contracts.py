"""Bootstrap integration coverage for the optional API-contract surface."""

from __future__ import annotations

import json
import textwrap
import types
from pathlib import Path

import pytest

from llm_wiki_cli import cli
from llm_wiki_cli.commands import bootstrap_cmd
from llm_wiki_cli.services import knowledge_orchestration
from llm_wiki_cli.services.infrastructure_sync import (
    INFRASTRUCTURE_GENERATION_INPUT_KEY,
    INFRASTRUCTURE_SYNC_SCHEMA_VERSION,
)
from llm_wiki_cli.services.knowledge_envelope import ConsumedInputKind


def _args(project: Path, wiki: Path, **overrides):
    values = {
        "src_dir": ".",
        "wiki_dir": str(wiki),
        "overwrite": False,
        "depth": "full",
        "skip_workflows": True,
        "skip_flows": False,
        "skip_data_flow": True,
        "skip_dependencies": True,
        "dependency_graph_detail": "auto",
        "api_contracts": False,
        "openapi_file": None,
        "format": "text",
        "source_adapter": True,
        "allow_external_src": False,
        "helper_cache_dir": None,
        "include_tests": None,
    }
    values.update(overrides)
    return types.SimpleNamespace(**values)


def _write_fastapi_project(project: Path) -> None:
    (project / "app.py").write_text(
        textwrap.dedent(
            """\
            from fastapi import APIRouter, FastAPI, Query

            app = FastAPI(title="Inventory API")
            router = APIRouter(prefix="/v1", tags=["items"])


            @router.post("/items", status_code=201, summary="Create item")
            def create_item(*, search: str | None = Query(None, alias="q")):
                return {"search": search}


            app.include_router(router, prefix="/api")
            """
        ),
        encoding="utf-8",
    )


def test_bootstrap_parser_accepts_api_contract_inputs():
    parser = cli._build_parser()

    static = parser.parse_args(["bootstrap", "--api-contracts"])
    openapi = parser.parse_args(
        ["bootstrap", "--depth", "shallow", "--openapi-file", "openapi.yaml"]
    )

    assert static.api_contracts is True
    assert static.openapi_file is None
    assert openapi.openapi_file == "openapi.yaml"


def test_bootstrap_api_contracts_is_opt_in_and_links_matching_flow(
    tmp_path, monkeypatch, capsys
):
    project = tmp_path / "project"
    project.mkdir()
    _write_fastapi_project(project)
    monkeypatch.chdir(project)

    default_wiki = project / "wiki-default"
    bootstrap_cmd.run(_args(project, default_wiki, skip_flows=True))
    capsys.readouterr()
    assert not (default_wiki / "api-contracts.md").exists()

    wiki = project / "wiki"
    bootstrap_cmd.run(_args(project, wiki, api_contracts=True))
    capsys.readouterr()

    contract = (wiki / "api-contracts.md").read_text(encoding="utf-8")
    flow = (wiki / "flows" / "http-create_item.md").read_text(encoding="utf-8")
    index = (wiki / "index.md").read_text(encoding="utf-8")
    manifest = json.loads(
        (wiki / ".llm-wiki-manifest.json").read_text(encoding="utf-8")
    )

    assert "`POST` | `/api/v1/items`" in contract
    assert "[`create_item`](modules/app.md)" in contract
    assert "[http-create_item](flows/http-create_item.md)" in contract
    assert "## API contract" in flow
    assert "`POST /api/v1/items`" in flow
    assert "[Production HTTP API inventory](api-contracts.md)" in index
    assert manifest["version"] == 5
    assert manifest["surfaces"]["flows"] == {
        "enabled": True,
        "categories": None,
        "exclude_tests": False,
    }
    assert manifest["surfaces"]["dependencies"] == {
        "enabled": False,
        "exclude_tests": False,
    }
    assert manifest["surfaces"]["api_contracts"] == {"enabled": True}
    generation_inputs = manifest["generation_inputs"]
    assert generation_inputs[
        knowledge_orchestration.RUNTIME_GENERATION_INPUT_KEY
    ] == {
        "data_flow_enabled": False,
        "dependency_graph_detail": "auto",
        "workflows_enabled": False,
    }
    assert generation_inputs[INFRASTRUCTURE_GENERATION_INPUT_KEY] == {
        "schema_version": INFRASTRUCTURE_SYNC_SCHEMA_VERSION,
        "status": "nothing-discovered",
        "discovery": {
            "roots": ["."],
            "candidate_count": 0,
            "supported_count": 0,
            "unsupported_yaml_count": 0,
            "unsupported_yaml": [],
        },
        "sources": {},
        "tombstones": {},
    }


def test_openapi_implies_full_contract_surface_and_persists_generation_input(
    tmp_path, monkeypatch, capsys
):
    project = tmp_path / "project"
    project.mkdir()
    _write_fastapi_project(project)
    (project / "openapi.json").write_text(
        json.dumps(
            {
                "openapi": "3.1.0",
                "info": {"title": "Inventory API", "version": "1.0.0"},
                "paths": {
                    "/api/v1/items": {
                        "post": {
                            "operationId": "create_item",
                            "summary": "Authoritative create",
                            "responses": {
                                "201": {
                                    "description": "Created",
                                    "content": {"application/json": {}},
                                }
                            },
                        }
                    }
                },
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.chdir(project)
    wiki = project / "wiki"
    captured_consumed_inputs = ()
    real_build_plan = knowledge_orchestration.build_knowledge_generation_plan

    def capture_build_plan(inputs):
        nonlocal captured_consumed_inputs
        captured_consumed_inputs = tuple(inputs.consumed_inputs)
        return real_build_plan(inputs)

    monkeypatch.setattr(
        knowledge_orchestration,
        "build_knowledge_generation_plan",
        capture_build_plan,
    )

    bootstrap_cmd.run(
        _args(
            project,
            wiki,
            depth="shallow",
            openapi_file="openapi.json",
            format="json",
        )
    )
    captured = capsys.readouterr()
    summary = json.loads(captured.out)
    manifest = json.loads(
        (wiki / ".llm-wiki-manifest.json").read_text(encoding="utf-8")
    )
    contract = (wiki / "api-contracts.md").read_text(encoding="utf-8")

    assert summary["depth"] == "full"
    assert summary["api_contracts"] == {
        "generated": True,
        "source": "openapi",
        "operations": 1,
    }
    assert "**Authority:** OpenAPI 3.1.0 from `openapi.json`" in contract
    assert "Authoritative create" in contract
    assert manifest["surfaces"]["api_contracts"] == {"enabled": True}
    openapi_input = manifest["generation_inputs"]["openapi"]
    assert openapi_input["path"] == "openapi.json"
    assert openapi_input["format"] == "json"
    assert openapi_input["sha256"].startswith("sha256:")
    consumed_openapi = next(
        item for item in captured_consumed_inputs if item.path == "openapi.json"
    )
    assert consumed_openapi.kind is ConsumedInputKind.OPENAPI
    assert consumed_openapi.content_hash == openapi_input["sha256"]


def test_bootstrap_rejects_overwrite_without_touching_contract_semantics(
    tmp_path, monkeypatch, capsys
):
    project = tmp_path / "project"
    project.mkdir()
    _write_fastapi_project(project)
    monkeypatch.chdir(project)
    wiki = project / "wiki"
    args = _args(project, wiki, api_contracts=True)

    bootstrap_cmd.run(args)
    capsys.readouterr()
    contract_path = wiki / "api-contracts.md"
    flow_path = wiki / "flows" / "http-create_item.md"
    contract_path.write_text(
        contract_path.read_text(encoding="utf-8").replace(
            "_Record reviewed runtime-only contract details and reconciliation decisions here._",
            "Runtime contract reviewed by the API team.",
        ),
        encoding="utf-8",
    )
    flow_path.write_text(
        flow_path.read_text(encoding="utf-8").replace(
            "This flow starts at `create_item` and is classified as `http`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.",
            "Creates one inventory item.",
        ),
        encoding="utf-8",
    )
    contract_before = contract_path.read_bytes()
    flow_before = flow_path.read_bytes()
    capsys.readouterr()

    with pytest.raises(SystemExit) as exc_info:
        bootstrap_cmd.run(_args(project, wiki, api_contracts=True, overwrite=True))

    assert exc_info.value.code == 2
    assert contract_path.read_bytes() == contract_before
    assert flow_path.read_bytes() == flow_before
    assert "overwrite` option is no longer supported" in capsys.readouterr().out


def test_invalid_openapi_fails_before_generated_pages(tmp_path, monkeypatch, capsys):
    project = tmp_path / "project"
    project.mkdir()
    _write_fastapi_project(project)
    (project / "openapi.json").write_text("{not-json", encoding="utf-8")
    monkeypatch.chdir(project)
    wiki = project / "wiki"

    with pytest.raises(SystemExit) as exc_info:
        bootstrap_cmd.run(_args(project, wiki, openapi_file="openapi.json"))

    assert exc_info.value.code == 2
    assert "Invalid OpenAPI" in capsys.readouterr().out
    assert not (wiki / "index.md").exists()
    assert not (wiki / "api-contracts.md").exists()


def test_openapi_can_bootstrap_contract_surface_without_python_inventory(
    tmp_path, monkeypatch, capsys
):
    project = tmp_path / "project"
    project.mkdir()
    (project / "openapi.yaml").write_text(
        textwrap.dedent(
            """\
            openapi: 3.0.3
            info:
              title: External API
              version: 1.0.0
            paths:
              /health:
                get:
                  responses:
                    '200':
                      description: Healthy
            """
        ),
        encoding="utf-8",
    )
    monkeypatch.chdir(project)
    wiki = project / "wiki"

    bootstrap_cmd.run(_args(project, wiki, openapi_file="openapi.yaml"))
    capsys.readouterr()

    contract = (wiki / "api-contracts.md").read_text(encoding="utf-8")
    assert "`GET` | `/health`" in contract
    assert "Unknown" in contract
    assert (wiki / "index.md").is_file()
