"""End-to-end sync regressions for persisted API-contract authority."""

from __future__ import annotations

import json
import re
import subprocess
import textwrap
import types
from pathlib import Path

import pytest

from llm_wiki_cli import cli
from llm_wiki_cli.commands import bootstrap_cmd, sync_cmd
from llm_wiki_cli.commands.sync_cmd import MANIFEST_FILENAME, SyncManifest
from llm_wiki_cli.services.inventory_cache import CACHE_FILENAME


def _bootstrap_args(project: Path, wiki: Path):
    return types.SimpleNamespace(
        src_dir=str(project),
        wiki_dir=str(wiki),
        overwrite=False,
        depth="full",
        skip_workflows=True,
        skip_flows=True,
        skip_data_flow=False,
        skip_dependencies=True,
        api_contracts=False,
        openapi_file=None,
        dependency_graph_detail="auto",
        format="text",
        source_adapter=True,
        allow_external_src=False,
        helper_cache_dir=None,
        include_tests=None,
    )


def _sync_args(project: Path, wiki: Path, **kwargs):
    defaults = {
        "src_dir": str(project),
        "wiki_dir": str(wiki),
        "initialize_surfaces": None,
        "flow_category": None,
        "exclude_tests": False,
        "dry_run": False,
        "force": False,
        "no_cache": True,
        "rebuild_cache": False,
        "cache_stats": False,
        "cache_dir": None,
        "jobs": 1,
        "no_preserve_semantic": False,
        "allow_external_src": False,
        "helper_cache_dir": None,
        "include_tests": None,
        "openapi_file": None,
        "clear_openapi_file": False,
    }
    defaults.update(kwargs)
    return types.SimpleNamespace(**defaults)


def _write_fastapi_source(project: Path) -> None:
    (project / "app.py").write_text(
        textwrap.dedent(
            """\
            from fastapi import FastAPI, Query

            app = FastAPI()


            @app.get("/items", operation_id="listItems", summary="Static list")
            def list_items(limit: int = Query(10, alias="page-size")):
                return {"limit": limit}
            """
        ),
        encoding="utf-8",
    )


def _write_plain_source(project: Path) -> None:
    (project / "plain.py").write_text(
        "def helper():\n    return 'ok'\n", encoding="utf-8"
    )


def _bootstrap_project(
    tmp_path: Path,
    monkeypatch,
    capsys,
    *,
    fastapi: bool = True,
) -> tuple[Path, Path]:
    project = tmp_path / "project"
    project.mkdir()
    subprocess.run(["git", "init", str(project)], check=True, capture_output=True)
    (project / "pyproject.toml").write_text(
        '[project]\nname = "api-sync"\nversion = "0.1.0"\n',
        encoding="utf-8",
    )
    (_write_fastapi_source if fastapi else _write_plain_source)(project)
    wiki = project / "docs" / "llm_wiki"
    monkeypatch.chdir(project)
    bootstrap_cmd.run(_bootstrap_args(project, wiki))
    capsys.readouterr()
    return project, wiki


@pytest.fixture
def api_project(tmp_path, monkeypatch, capsys):
    return _bootstrap_project(tmp_path, monkeypatch, capsys)


def _write_openapi(project: Path, *, summary: str = "OpenAPI list") -> Path:
    path = project / "contracts" / "openapi.yaml"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        textwrap.dedent(
            f"""\
            openapi: 3.1.0
            info:
              title: API sync fixture
              version: "1"
            paths:
              /items:
                get:
                  operationId: listItems
                  summary: {summary}
                  parameters:
                    - name: page-size
                      in: query
                      required: false
                      schema:
                        type: integer
                        default: 10
                  responses:
                    "200":
                      description: listed
                      content:
                        application/json:
                          schema:
                            type: object
            """
        ),
        encoding="utf-8",
    )
    return path


def _initialize_openapi(
    project: Path,
    wiki: Path,
    *,
    with_flows: bool = False,
) -> Path:
    spec = _write_openapi(project)
    surfaces = [("flows", "api-contracts")] if with_flows else None
    sync_cmd.run(
        _sync_args(
            project,
            wiki,
            openapi_file="contracts/openapi.yaml",
            initialize_surfaces=surfaces,
            flow_category=["http"] if with_flows else None,
        )
    )
    return spec


def _tree_bytes(root: Path) -> dict[str, bytes]:
    return {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in root.rglob("*")
        if path.is_file()
    }


def _replace_section(markdown: str, heading: str, body: str) -> str:
    pattern = re.compile(rf"(?ms)(^## {re.escape(heading)}\s*\n).*?(?=^## |\Z)")
    replacement = rf"\g<1>\n{body}\n"
    updated, count = pattern.subn(replacement, markdown)
    assert count == 1
    return updated


def _section_body(markdown: str, heading: str) -> str:
    pattern = re.compile(
        rf"(?ms)^## {re.escape(heading)}\s*\n(.*?)(?=^## |\Z)"
    )
    match = pattern.search(markdown)
    assert match is not None
    return match.group(1).strip("\n")


def test_sync_parser_accepts_and_separates_openapi_authority_flags():
    parser = cli._build_parser()

    supplied = parser.parse_args(["sync", "--openapi-file", "openapi.yaml"])
    cleared = parser.parse_args(["sync", "--clear-openapi-file"])

    assert supplied.openapi_file == "openapi.yaml"
    assert supplied.clear_openapi_file is False
    assert cleared.openapi_file is None
    assert cleared.clear_openapi_file is True
    with pytest.raises(SystemExit):
        parser.parse_args(
            [
                "sync",
                "--openapi-file",
                "openapi.yaml",
                "--clear-openapi-file",
            ]
        )


def test_openapi_file_persists_and_generates_authoritative_page(
    api_project, capsys
):
    project, wiki = api_project
    _initialize_openapi(project, wiki)

    manifest = SyncManifest.load(wiki)
    openapi = manifest.generation_inputs["openapi"]
    assert openapi["path"] == "contracts/openapi.yaml"
    assert openapi["format"] == "yaml"
    assert str(openapi["sha256"]).startswith("sha256:")
    assert manifest.surfaces["api_contracts"] == {"enabled": True}

    page = (wiki / "api-contracts.md").read_text(encoding="utf-8")
    assert "**Authority:** OpenAPI 3.1.0" in page
    assert "`GET` | `/items` | OpenAPI list" in page
    assert "`page-size`" in page
    assert "CREATED api-contracts.md" in capsys.readouterr().out


def test_spec_only_change_bypasses_clean_source_return_and_updates_page(
    api_project, capsys
):
    project, wiki = api_project
    spec = _initialize_openapi(project, wiki)
    before_manifest = SyncManifest.load(wiki)
    before_hash = before_manifest.generation_inputs["openapi"]["sha256"]
    capsys.readouterr()

    _write_openapi(project, summary="Revised contract summary")
    sync_cmd.run(_sync_args(project, wiki))

    after_manifest = SyncManifest.load(wiki)
    assert after_manifest.sources == before_manifest.sources
    assert after_manifest.generation_inputs["openapi"]["sha256"] != before_hash
    assert "Revised contract summary" in (wiki / "api-contracts.md").read_text(
        encoding="utf-8"
    )
    knowledge = json.loads(
        (wiki / ".llm-wiki-knowledge.json").read_text(encoding="utf-8")
    )
    snapshot_hash = knowledge["bundle"]["snapshot"]["source_snapshot_hash"]
    assert f"- Source snapshot digest: `{snapshot_hash}`" in (
        wiki / "log.md"
    ).read_text(encoding="utf-8")
    assert "UPDATED api-contracts.md" in capsys.readouterr().out
    assert spec.is_file()


@pytest.mark.parametrize("failure", ["missing", "malformed"])
def test_bad_persisted_spec_fails_before_wiki_or_cache_write(
    api_project, capsys, failure
):
    project, wiki = api_project
    spec = _initialize_openapi(project, wiki)
    before = _tree_bytes(wiki)
    cache_dir = project / "isolated-cache"
    cache_path = cache_dir / CACHE_FILENAME
    capsys.readouterr()
    if failure == "missing":
        spec.unlink()
    else:
        spec.write_text("openapi: [not valid", encoding="utf-8")

    with pytest.raises(SystemExit) as exc_info:
        sync_cmd.run(
            _sync_args(
                project,
                wiki,
                no_cache=False,
                cache_dir=str(cache_dir),
            )
        )

    assert exc_info.value.code == 2
    assert _tree_bytes(wiki) == before
    assert not cache_path.exists()
    assert "Error:" in capsys.readouterr().err


def test_clear_openapi_file_returns_existing_surface_to_static_authority(
    api_project,
):
    project, wiki = api_project
    _initialize_openapi(project, wiki)

    sync_cmd.run(_sync_args(project, wiki, clear_openapi_file=True))

    manifest = json.loads(
        (wiki / MANIFEST_FILENAME).read_text(encoding="utf-8")
    )
    assert "openapi" not in manifest.get("generation_inputs", {})
    assert manifest["surfaces"]["api_contracts"] == {"enabled": True}
    page = (wiki / "api-contracts.md").read_text(encoding="utf-8")
    assert "**Authority:** syntax-only static analysis" in page
    assert "`GET` | `/items` | Static list" in page


def test_zero_candidate_initialization_persists_policy_and_creates_empty_page(
    tmp_path, monkeypatch, capsys
):
    project, wiki = _bootstrap_project(
        tmp_path, monkeypatch, capsys, fastapi=False
    )

    sync_cmd.run(
        _sync_args(
            project,
            wiki,
            initialize_surfaces=[("api-contracts",)],
        )
    )

    assert SyncManifest.load(wiki).surfaces["api_contracts"] == {"enabled": True}
    page = (wiki / "api-contracts.md").read_text(encoding="utf-8")
    assert "syntax-only static analysis" in page
    assert "No production HTTP operations were assembled" in page


def test_regeneration_preserves_notes_and_flow_behavior_and_adds_api_section(
    api_project,
):
    project, wiki = api_project
    _initialize_openapi(project, wiki, with_flows=True)
    api_path = wiki / "api-contracts.md"
    flow_path = wiki / "flows" / "http-list_items.md"
    assert flow_path.is_file()

    notes = "Keep this exact note.\n\n- pipe | value\n- `code`"
    behavior = "Operator-approved behavior.\n\n1. Keep ordering.\n2. Keep spacing."
    api_path.write_text(
        _replace_section(api_path.read_text(encoding="utf-8"), "Notes", notes),
        encoding="utf-8",
    )
    flow_path.write_text(
        _replace_section(
            flow_path.read_text(encoding="utf-8"), "Behavior", behavior
        ),
        encoding="utf-8",
    )

    _write_openapi(project, summary="Regenerated API summary")
    sync_cmd.run(_sync_args(project, wiki))

    regenerated_api = api_path.read_text(encoding="utf-8")
    regenerated_flow = flow_path.read_text(encoding="utf-8")
    assert _section_body(regenerated_api, "Notes") == notes
    assert _section_body(regenerated_flow, "Behavior") == behavior
    assert "## API contract" in regenerated_flow
    assert "`GET /items`" in regenerated_flow
    assert "Regenerated API summary" in regenerated_api


def test_openapi_path_containment_failure_does_not_modify_wiki(
    api_project, tmp_path, capsys
):
    project, wiki = api_project
    outside = tmp_path / "outside.yaml"
    outside.write_text(
        "openapi: 3.1.0\ninfo: {title: outside, version: '1'}\npaths: {}\n",
        encoding="utf-8",
    )
    before = _tree_bytes(wiki)

    with pytest.raises(SystemExit) as exc_info:
        sync_cmd.run(
            _sync_args(project, wiki, openapi_file="../outside.yaml")
        )

    assert exc_info.value.code == 2
    assert _tree_bytes(wiki) == before
    assert "outside source root" in capsys.readouterr().err


def test_openapi_dry_run_is_immutable_including_inventory_cache(
    api_project, capsys
):
    project, wiki = api_project
    _write_openapi(project)
    before = _tree_bytes(wiki)
    cache_dir = project / "dry-run-cache"
    cache_path = cache_dir / CACHE_FILENAME

    sync_cmd.run(
        _sync_args(
            project,
            wiki,
            openapi_file="contracts/openapi.yaml",
            initialize_surfaces=[("api-contracts",)],
            dry_run=True,
            no_cache=False,
            cache_dir=str(cache_dir),
        )
    )

    assert _tree_bytes(wiki) == before
    assert not cache_path.exists()
    output = capsys.readouterr().out
    assert "authority: openapi" in output
    assert "DRY-RUN: no files modified." in output
