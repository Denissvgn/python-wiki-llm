"""Unknown HTTP routes must not break native artifact publication."""

import json
from types import SimpleNamespace

import pytest

from llm_wiki_cli.commands import bootstrap_cmd, sync_cmd
from llm_wiki_cli.services.knowledge_loader import load_knowledge_state
from llm_wiki_cli.services import api_contracts as contract_service
from llm_wiki_cli.services.knowledge_generation import KnowledgeGenerationError
from llm_wiki_cli.services.knowledge_artifacts import (
    KnowledgeArtifactError,
    _validate_surface_flow_routes,
)


def _source(dynamic):
    path = 'f"{PREFIX}/items"' if dynamic else '"/v1/items"'
    return (
        'from fastapi import FastAPI\napp = FastAPI()\nPREFIX = "/v1"\n'
        "@app.get(" + path + ")\n"
        '@app.get("/items", include_in_schema=False)\n'
        "def items():\n    return []\n"
    )


def _snapshot(wiki):
    return {
        name: ((wiki / name).read_bytes(), (wiki / name).stat().st_mtime_ns)
        for name in (
            ".llm-wiki-surface.json",
            ".llm-wiki-knowledge.json",
            ".llm-wiki-manifest.json",
        )
    }


@pytest.mark.parametrize("api_contracts", [False, True])
@pytest.mark.parametrize("initial_dynamic", [False, True])
def test_dynamic_routes_publish_and_converge(
    tmp_path, monkeypatch, api_contracts, initial_dynamic
):
    monkeypatch.chdir(tmp_path)
    source = tmp_path / "src"
    source.mkdir()
    app = source / "app.py"
    app.write_text(_source(initial_dynamic), encoding="utf-8")
    wiki = tmp_path / "wiki"
    bootstrap_cmd.run(
        SimpleNamespace(
            src_dir="src",
            wiki_dir=str(wiki),
            depth="full",
            overwrite=False,
            source_adapter=True,
            skip_workflows=True,
            skip_dependencies=True,
            skip_data_flow=True,
            api_contracts=api_contracts,
        )
    )
    if not initial_dynamic:
        app.write_text(_source(True), encoding="utf-8")
        sync_cmd.run(
            SimpleNamespace(
                src_dir="src", wiki_dir=str(wiki), force=True, rebuild_knowledge=True
            )
        )
    assert load_knowledge_state(wiki).knowledge is not None
    surface = json.loads((wiki / ".llm-wiki-surface.json").read_text())
    flow = next(item for item in surface["flows"] if item["id"] == "http-items")
    assert "routes" not in flow
    assert (wiki / "flows/http-items.md").is_file()
    if api_contracts:
        assert (
            "Unknown" in (wiki / "api-contracts.md").read_text()
            or "unknown" in (wiki / "api-contracts.md").read_text()
        )
    before = _snapshot(wiki)
    for options in ({}, {"no_cache": True}, {"rebuild_knowledge": True}):
        sync_cmd.run(SimpleNamespace(src_dir="src", wiki_dir=str(wiki), **options))
        assert _snapshot(wiki) == before


def test_stored_null_routes_are_still_rejected():
    with pytest.raises(KnowledgeArtifactError, match="must be a non-empty string"):
        _validate_surface_flow_routes(
            [{"method": "GET", "path": None, "operation_id": None}], "routes"
        )


@pytest.mark.parametrize("interrupted", ["bootstrap", "sync"])
def test_recovery_from_legacy_route_failure_preserves_authored_behavior(
    tmp_path, monkeypatch, interrupted
):
    monkeypatch.chdir(tmp_path)
    source = tmp_path / "src"
    source.mkdir()
    app = source / "app.py"
    wiki = tmp_path / "wiki"
    args = dict(
        src_dir="src",
        wiki_dir=str(wiki),
        depth="full",
        overwrite=False,
        source_adapter=True,
        skip_workflows=True,
        skip_dependencies=True,
        skip_data_flow=True,
        api_contracts=True,
    )
    if interrupted == "sync":
        app.write_text(_source(False), encoding="utf-8")
        bootstrap_cmd.run(SimpleNamespace(**args))
    app.write_text(_source(True), encoding="utf-8")
    with monkeypatch.context() as legacy:
        legacy.setattr(
            contract_service,
            "_resolved_flow_route",
            lambda operation: {
                "method": operation["method"],
                "path": operation["path"],
                "operation_id": None,
            },
        )
        with pytest.raises(KnowledgeGenerationError) as failure:
            if interrupted == "bootstrap":
                bootstrap_cmd.run(SimpleNamespace(**args))
            else:
                sync_cmd.run(
                    SimpleNamespace(
                        src_dir="src",
                        wiki_dir=str(wiki),
                        force=True,
                        rebuild_knowledge=True,
                    )
                )
        assert failure.value.field.endswith("routes[0].path")
    flow = wiki / "flows/http-items.md"
    flow.write_text(
        sync_cmd._replace_section_body(
            flow.read_text(), "Behavior", "Keep this operator explanation."
        ),
        encoding="utf-8",
    )
    sync_cmd.run(
        SimpleNamespace(
            src_dir="src", wiki_dir=str(wiki), force=True, rebuild_knowledge=True
        )
    )
    assert load_knowledge_state(wiki).knowledge is not None
    assert "Keep this operator explanation." in flow.read_text()
    record = json.loads((wiki / ".llm-wiki-surface.json").read_text())["flows"][0]
    assert "routes" not in record
