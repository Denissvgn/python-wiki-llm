from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml

from llm_wiki_cli.extractors.fastapi_contracts import (
    extract_fastapi_declarations,
)
from llm_wiki_cli.extractors.python_extractor import PythonExtractor
from llm_wiki_cli.services.api_contracts import (
    ApiContractError,
    attach_routes_to_entry_points,
    build_api_contracts,
    build_static_api_contracts,
    load_openapi_document,
    render_api_contracts_markdown,
    render_flow_api_contract_section,
)


def _inventory(root: Path, files: dict[str, str]) -> dict:
    for relative, source in files.items():
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(source, encoding="utf-8")
    return PythonExtractor().extract(str(root), deep=True)


def _codes(contracts: dict) -> set[str]:
    return {item["code"] for item in contracts["diagnostics"]}


def _static_fixture(root: Path) -> dict:
    return _inventory(
        root,
        {
            "routers/items.py": '''
from fastapi import (
    APIRouter as Router,
    Body, Cookie, Depends, File, Form, Header, Path, Query, Request,
)
from fastapi.responses import ORJSONResponse
from models import Error, Item

router = Router(
    prefix="/items",
    tags=["items"],
    responses={401: {"model": Error}},
)

@router.api_route(
    "/{item_id}",
    methods=["POST", "PUT"],
    status_code=201,
    response_model=Item,
    response_class=ORJSONResponse,
    responses={
        404: {
            "model": Error,
            "description": "missing",
            "content": {"application/problem+json": {}},
        }
    },
    summary="Upsert item",
    operation_id="upsertItem",
)
async def upsert(
    item_id: int = Path(..., alias="item_id"),
    payload: Item = Body(...),
    upload: bytes = File(...),
    x_token: str = Header(...),
    q: str = Query("all", alias="search"),
    form_name: str = Form(""),
    sid: str | None = Cookie(None),
    ignored: object = Depends(load_user),
    request: Request = None,
) -> Item:
    return payload
''',
            "routers/root.py": '''
from fastapi import APIRouter
from . import items

root_router = APIRouter(prefix="/v1", tags=["root"])
root_router.include_router(items.router, prefix="/catalog", tags=["public"])
''',
            "app.py": '''
from fastapi import FastAPI
from routers.root import root_router as api_router

app = FastAPI(root_path="/proxy")
application = app
application.include_router(api_router, prefix="/api")
''',
            "models.py": "class Item: pass\nclass Error: pass\n",
        },
    )


def test_raw_extractor_tracks_aliases_factory_scope_and_parameter_markers() -> None:
    declarations = extract_fastapi_declarations(
        '''
from fastapi import FastAPI as WebApp, Query as Q

PREFIX = "/v1"

def create_app():
    app = WebApp(root_path="/proxy")

    @app.get(PREFIX + "/items")
    def items(q: str = Q("all", alias="search")):
        return []

    return app
''',
        filepath="app.py",
    )

    assert declarations["applications"][0]["scope"] == "create_app"
    operation = declarations["operations"][0]
    assert operation["handler_qualname"] == "create_app.items"
    assert operation["parameters"][0]["marker"] == {
        "call": "Q",
        "args": [{"kind": "literal", "value": "all"}],
        "kwargs": {"alias": {"kind": "literal", "value": "search"}},
        "marker": "query",
        "canonical_call": "fastapi.Query",
        "source": "default",
    }
    assert "dump(" not in json.dumps(declarations)


def test_deep_python_inventory_retains_fastapi_only_application_module(
    tmp_path: Path,
) -> None:
    inventory = _inventory(
        tmp_path,
        {
            "app.py": '''
from fastapi import FastAPI
from routes import router

app = FastAPI()
app.include_router(router)
'''
        },
    )

    assert inventory["app.py"]["classes"] == []
    assert inventory["app.py"]["functions"] == []
    assert inventory["app.py"]["frameworks"]["fastapi"]["applications"]


def test_pydantic_model_kind_propagates_across_imported_local_base(
    tmp_path: Path,
) -> None:
    inventory = _inventory(
        tmp_path,
        {
            "base.py": "from pydantic import BaseModel\nclass DomainModel(BaseModel): pass\n",
            "user.py": "from base import DomainModel as Base\nclass User(Base): pass\n",
        },
    )

    user = inventory["user.py"]["classes"][0]
    assert user["model_kind"] == "pydantic"


def test_pydantic_model_kind_resolves_the_imported_module_before_propagating(
    tmp_path: Path,
) -> None:
    inventory = _inventory(
        tmp_path,
        {
            "pyd.py": "from pydantic import BaseModel\nclass DomainModel(BaseModel): pass\n",
            "plain.py": "class DomainModel: pass\n",
            "user.py": "from plain import DomainModel\nclass User(DomainModel): pass\n",
        },
    )

    user = inventory["user.py"]["classes"][0]
    assert "model_kind" not in user


def test_dynamic_pydantic_metadata_is_unknown_instead_of_asserted(
    tmp_path: Path,
) -> None:
    inventory = _inventory(
        tmp_path,
        {
            "models.py": '''
from pydantic import BaseModel, ConfigDict, Field

class Item(BaseModel):
    model_config = ConfigDict(alias_generator=make_alias)
    quantity: int = Field(gt=compute_limit(), examples=[make_example()])
'''
        },
    )

    model = inventory["models.py"]["classes"][0]
    field = model["attributes"][0]
    assert "constraints" not in field
    assert "examples" not in field
    assert {item["property"] for item in field["unknowns"]} == {
        "constraint:gt",
        "examples",
    }
    assert "value" not in model["model_config"][0]
    assert model["model_config"][0]["unknowns"][0]["expression"] == "make_alias"


def test_static_contract_composes_nested_routers_and_wire_fields(tmp_path: Path) -> None:
    contracts = build_static_api_contracts(_static_fixture(tmp_path))

    assert contracts["source"] == "static"
    assert len(contracts["applications"]) == 1
    assert len(contracts["operations"]) == 2
    assert {item["method"] for item in contracts["operations"]} == {"POST", "PUT"}
    operation = contracts["operations"][0]
    assert operation["path"] == "/api/v1/catalog/items/{item_id}"
    assert "/proxy" not in operation["path"]
    assert operation["tags"] == ["root", "public", "items"]
    assert operation["operation_id"] == "upsertItem"
    assert operation["summary"] == "Upsert item"

    parameters = {item["python_name"]: item for item in operation["parameters"]}
    assert parameters["item_id"] | {"sentinel": None} == {
        "python_name": "item_id",
        "wire_name": "item_id",
        "location": "path",
        "type": "int",
        "required": True,
        "nullable": False,
        "sentinel": None,
    }
    assert parameters["q"]["wire_name"] == "search"
    assert parameters["q"]["default"] == "all"
    assert parameters["x_token"]["wire_name"] == "x-token"
    assert parameters["sid"]["nullable"] is True
    assert parameters["sid"]["default"] is None
    assert "ignored" not in parameters
    assert "request" not in parameters
    assert operation["request_body"] == {
        "content_types": ["multipart/form-data"],
        "models": ["Item"],
        "required": True,
    }
    responses = {str(item["status_code"]): item for item in operation["responses"]}
    assert set(responses) == {"201", "401", "404"}
    assert responses["201"]["model"] == "Item"
    assert responses["201"]["content_types"] == ["application/json"]
    assert responses["401"]["model"] == "Error"
    assert responses["404"]["content_types"] == ["application/problem+json"]
    assert "422" not in responses
    assert {
        item["field"] for item in operation["unknowns"]
    } == {"parameter:ignored"}


def test_repeated_router_mounts_emit_each_path_and_route_list(tmp_path: Path) -> None:
    inventory = _inventory(
        tmp_path,
        {
            "app.py": '''
from fastapi import APIRouter, FastAPI

router = APIRouter()

@router.get("/health", operation_id="health")
def health(): return {"ok": True}

app = FastAPI()
app.include_router(router, prefix="/one")
app.include_router(router, prefix="/two")
'''
        },
    )
    contracts = build_static_api_contracts(inventory)

    assert [item["path"] for item in contracts["operations"]] == [
        "/one/health",
        "/two/health",
    ]
    entries = attach_routes_to_entry_points(
        [{"file": "app.py", "symbol": "health", "category": "http"}],
        contracts,
    )
    assert [route["path"] for route in entries[0]["routes"]] == [
        "/one/health",
        "/two/health",
    ]


def test_trace_decorator_is_a_first_class_http_operation(tmp_path: Path) -> None:
    inventory = _inventory(
        tmp_path,
        {
            "app.py": '''
from fastapi import FastAPI
app = FastAPI()

@app.trace("/diagnostics")
def diagnostics(): pass
'''
        },
    )

    operation = build_static_api_contracts(inventory)["operations"][0]
    assert (operation["method"], operation["path"]) == ("TRACE", "/diagnostics")


def test_router_cycle_dynamic_prefix_and_unresolved_include_are_diagnostic(
    tmp_path: Path,
) -> None:
    inventory = _inventory(
        tmp_path,
        {
            "app.py": '''
from fastapi import APIRouter, FastAPI

left = APIRouter()
right = APIRouter()
dynamic = APIRouter(prefix=make_prefix())

@left.get("/left")
def left_handler(): pass

@dynamic.get("/hidden")
def dynamic_handler(): pass

left.include_router(right)
right.include_router(left)
app = FastAPI()
app.include_router(left)
app.include_router(dynamic)
app.include_router(missing_router)
'''
        },
    )
    contracts = build_static_api_contracts(inventory)

    assert [item["path"] for item in contracts["operations"]] == ["/left"]
    assert {
        "fastapi_router_cycle",
        "fastapi_prefix_unknown",
        "fastapi_include_unresolved",
    } <= _codes(contracts)


def test_schema_hidden_and_test_source_operations_are_excluded_but_raw_retained(
    tmp_path: Path,
) -> None:
    inventory = _inventory(
        tmp_path,
        {
            "app.py": '''
from fastapi import FastAPI
app = FastAPI()

@app.get("/hidden", include_in_schema=False)
def hidden(): pass
''',
            "tests/test_routes.py": '''
from fastapi import FastAPI
app = FastAPI()

@app.get("/test-only")
def test_only(): pass
''',
        },
    )
    contracts = build_static_api_contracts(inventory)

    assert contracts["operations"] == []
    assert contracts["excluded_counts"] == {
        "test_source": 1,
        "schema_excluded": 1,
        "conditional": 0,
    }
    assert inventory["app.py"]["frameworks"]["fastapi"]["operations"]
    assert inventory["tests/test_routes.py"]["frameworks"]["fastapi"]["operations"]


def test_syntax_only_extraction_never_executes_target_module(tmp_path: Path) -> None:
    sentinel = tmp_path / "executed.txt"
    inventory = _inventory(
        tmp_path,
        {
            "app.py": f'''
from fastapi import FastAPI
from pathlib import Path

Path({str(sentinel)!r}).write_text("executed")
raise RuntimeError("must never execute")

app = FastAPI()

@app.get("/safe")
def safe(): return True
'''
        },
    )

    assert not sentinel.exists()
    assert build_static_api_contracts(inventory)["operations"][0]["path"] == "/safe"


def _openapi_document(path: str = "/items/{item_id}") -> dict:
    return {
        "openapi": "3.1.0",
        "info": {"title": "Inventory", "version": "1"},
        "paths": {
            path: {
                "get": {
                    "operationId": "getItem",
                    "parameters": [
                        {"$ref": "#/components/parameters/ItemId"},
                    ],
                    "requestBody": {"$ref": "#/components/requestBodies/ItemBody"},
                    "responses": {
                        "200": {"$ref": "#/components/responses/Item"},
                        "400": {"$ref": "https://example.invalid/problem.yaml#/Bad"},
                        "401": {"$ref": "#/components/responses/Missing"},
                    },
                }
            },
            "/openapi-only": {
                "post": {
                    "operationId": "openapiOnly",
                    "responses": {"204": {"description": "done"}},
                }
            },
        },
        "components": {
            "schemas": {
                "Item": {
                    "type": "object",
                    "properties": {"name": {"type": "string"}},
                }
            },
            "parameters": {
                "ItemId": {
                    "name": "item-id",
                    "in": "path",
                    "required": True,
                    "schema": {"type": "integer"},
                }
            },
            "requestBodies": {
                "ItemBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {"$ref": "#/components/schemas/Item"}
                        }
                    },
                }
            },
            "responses": {
                "Item": {
                    "description": "ok",
                    "content": {
                        "application/json": {
                            "schema": {"$ref": "#/components/schemas/Item"}
                        }
                    },
                }
            },
        },
    }


def _reconciliation_inventory(root: Path) -> dict:
    return _inventory(
        root,
        {
            "app.py": '''
from fastapi import Body, FastAPI, Path
from models import Item

app = FastAPI()

@app.get(
    "/items/{item_id}",
    operation_id="getItem",
    response_model=Item,
)
def get_item(item_id: int = Path(...), payload: Item = Body(...)) -> Item:
    return payload

@app.delete("/static-only")
def static_only(): pass
''',
            "models.py": "class Item: pass\n",
        },
    )


def test_openapi_json_yaml_equivalence_and_authoritative_reconciliation(
    tmp_path: Path,
) -> None:
    inventory = _reconciliation_inventory(tmp_path)
    document = _openapi_document()
    (tmp_path / "openapi.json").write_text(json.dumps(document), encoding="utf-8")
    (tmp_path / "openapi.yaml").write_text(
        yaml.safe_dump(document, sort_keys=False), encoding="utf-8"
    )

    json_contracts = build_api_contracts(
        inventory, openapi_file="openapi.json", source_root=tmp_path
    )
    yaml_contracts = build_api_contracts(
        inventory, openapi_file="openapi.yaml", source_root=tmp_path
    )

    assert json_contracts["source"] == "openapi"
    assert json_contracts["operations"] == yaml_contracts["operations"]
    assert json_contracts["openapi"]["format"] == "json"
    assert yaml_contracts["openapi"]["format"] == "yaml"
    assert len(json_contracts["operations"]) == 2
    operation = json_contracts["operations"][0]
    assert operation["handler"]["symbol"] == "get_item"
    assert operation["parameters"][0] == {
        "wire_name": "item-id",
        "location": "path",
        "type": "integer",
        "required": True,
        "nullable": False,
    }
    assert operation["request_body"] == {
        "content_types": ["application/json"],
        "models": ["Item"],
        "required": True,
    }
    assert operation["responses"][0]["model"] == "Item"
    assert {
        "openapi_external_ref",
        "openapi_ref_unresolved",
        "openapi_operation_unlinked",
        "static_operation_missing_from_openapi",
        "openapi_parameter_mismatch",
    } <= _codes(json_contracts)


def test_conditional_declarations_remain_raw_and_are_not_asserted(
    tmp_path: Path,
) -> None:
    inventory = _inventory(
        tmp_path,
        {
            "app.py": '''
from fastapi import FastAPI

if ENABLED:
    app = FastAPI()

    @app.get("/maybe")
    def maybe(): pass
'''
        },
    )

    contracts = build_static_api_contracts(inventory)

    assert contracts["operations"] == []
    assert contracts["excluded_counts"]["conditional"] == 1
    assert "fastapi_conditional_declaration" in _codes(contracts)
    assert inventory["app.py"]["frameworks"]["fastapi"]["operations"]


def test_response_alias_and_description_are_normalized(tmp_path: Path) -> None:
    inventory = _inventory(
        tmp_path,
        {
            "app.py": '''
from fastapi import FastAPI
from fastapi.responses import HTMLResponse as HTML
from models import Result as PublicResult

app = FastAPI()

@app.get(
    "/page",
    response_class=HTML,
    response_model=PublicResult,
    response_description="rendered",
)
def page(): pass
''',
            "models.py": "class Result: pass\n",
        },
    )

    response = build_static_api_contracts(inventory)["operations"][0]["responses"][0]

    assert response["content_types"] == ["text/html"]
    assert response["model"] == "Result"
    assert response["description"] == "rendered"


def test_openapi_parameter_content_is_authoritative_without_invented_python_name(
    tmp_path: Path,
) -> None:
    document = {
        "openapi": "3.1.0",
        "info": {"title": "content parameter", "version": "1"},
        "paths": {
            "/items": {
                "get": {
                    "parameters": [
                        {
                            "name": "X-Token",
                            "in": "header",
                            "content": {
                                "application/json": {
                                    "schema": {"type": "string", "default": "token"}
                                }
                            },
                        }
                    ],
                    "responses": {"200": {"description": "ok"}},
                }
            }
        },
    }
    (tmp_path / "openapi.yaml").write_text(yaml.safe_dump(document), encoding="utf-8")

    parameter = build_api_contracts(
        {}, openapi_file="openapi.yaml", source_root=tmp_path
    )["operations"][0]["parameters"][0]

    assert "python_name" not in parameter
    assert parameter["wire_name"] == "X-Token"
    assert parameter["type"] == "string"
    assert parameter["default"] == "token"
    assert parameter["content_types"] == ["application/json"]


def test_openapi_authority_omits_unrelated_static_diagnostics_and_exclusions(
    tmp_path: Path,
) -> None:
    inventory = _inventory(
        tmp_path,
        {
            "app.py": '''
from fastapi import APIRouter, FastAPI
router = APIRouter(prefix=dynamic_prefix())
@router.get("/static")
def static_handler(): pass
app = FastAPI()
app.include_router(router)
'''
        },
    )
    document = {
        "openapi": "3.1.0",
        "info": {"title": "runtime", "version": "1"},
        "paths": {
            "/runtime": {
                "get": {"responses": {"200": {"description": "ok"}}}
            }
        },
    }
    (tmp_path / "openapi.json").write_text(json.dumps(document), encoding="utf-8")

    contracts = build_api_contracts(
        inventory, openapi_file="openapi.json", source_root=tmp_path
    )

    assert "fastapi_prefix_unknown" not in _codes(contracts)
    assert contracts["excluded_counts"] == {
        "test_source": 0,
        "schema_excluded": 0,
        "conditional": 0,
    }


def test_operation_id_fallback_links_and_reports_path_mismatch(tmp_path: Path) -> None:
    inventory = _reconciliation_inventory(tmp_path)
    document = _openapi_document(path="/renamed/{item_id}")
    document["paths"].pop("/openapi-only")
    document["paths"]["/renamed/{item_id}"]["get"]["responses"] = {
        "200": {"description": "ok"}
    }
    (tmp_path / "openapi.yaml").write_text(yaml.safe_dump(document), encoding="utf-8")

    contracts = build_api_contracts(
        inventory, openapi_file="openapi.yaml", source_root=tmp_path
    )

    assert contracts["operations"][0]["handler"]["symbol"] == "get_item"
    assert "openapi_path_mismatch" in _codes(contracts)


@pytest.mark.parametrize(
    ("document", "message"),
    [
        ({"swagger": "2.0", "paths": {}}, "OpenAPI version"),
        ({"openapi": "3.0.3", "paths": []}, "paths field"),
    ],
)
def test_openapi_validation_rejects_wrong_contract(
    tmp_path: Path, document: dict, message: str
) -> None:
    (tmp_path / "openapi.yaml").write_text(yaml.safe_dump(document), encoding="utf-8")
    with pytest.raises(ApiContractError, match=message):
        load_openapi_document("openapi.yaml", source_root=tmp_path)


def test_openapi_path_must_remain_inside_source_root(tmp_path: Path) -> None:
    source_root = tmp_path / "src"
    source_root.mkdir()
    outside = tmp_path / "outside.yaml"
    outside.write_text(yaml.safe_dump(_openapi_document()), encoding="utf-8")

    with pytest.raises(ApiContractError, match="outside source root"):
        build_api_contracts(
            {}, openapi_file="../outside.yaml", source_root=source_root
        )


def test_markdown_and_flow_rendering_escape_tables_and_keep_notes() -> None:
    contracts = {
        "source": "static",
        "applications": [
            {"file": "app.py", "binding": "app", "scope": "<module>", "line": 1}
        ],
        "operations": [
            {
                "id": "get-weird",
                "method": "GET",
                "path": "/items/{a|b}`tick`",
                "summary": "first | second\nline",
                "handler": {"file": "app.py", "symbol": "handler", "line": 2},
                "parameters": [],
                "request_body": None,
                "responses": [],
                "unknowns": [],
            }
        ],
        "diagnostics": [],
        "excluded_counts": {},
    }

    markdown = render_api_contracts_markdown(contracts)
    flow = render_flow_api_contract_section(contracts["operations"])

    assert "## Applications" in markdown
    assert "first \\| second line" in markdown
    assert "## Notes" in markdown
    assert "../api-contracts.md#" in flow
