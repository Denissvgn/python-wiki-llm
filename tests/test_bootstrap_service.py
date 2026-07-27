"""Typed bootstrap service and public API boundary tests."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from llm_wiki_cli.api import BootstrapError, bootstrap_wiki
from llm_wiki_cli.commands import bootstrap_cmd
from llm_wiki_cli.commands.bootstrap_cmd import execute_bootstrap
from llm_wiki_cli.commands.extract_cmd import ExtractorStatus, InventoryResult
from llm_wiki_cli.services.bootstrap_service import (
    BootstrapContractError,
    BootstrapExtractionError,
    BootstrapRequest,
    BootstrapResult,
)
from llm_wiki_cli.services.knowledge_loader import load_knowledge_state
from llm_wiki_cli.services.knowledge_model import KnowledgeLoadState
from llm_wiki_cli.services.sync_manifest import MANIFEST_VERSION, SyncManifest


def _tree(root: Path) -> dict[str, bytes]:
    return {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in root.rglob("*")
        if path.is_file()
    }


def test_api_and_typed_service_produce_equivalent_native_wiki_trees(
    tmp_path, capsys
):
    source = tmp_path / "source with spaces Ω"
    source.mkdir()
    (source / "app.py").write_text(
        (
            '"""Example service."""\n\n'
            '__all__ = ["run"]\n\n'
            "def run(value: str) -> str:\n"
            "    return _normalize(value)\n\n"
            "def _normalize(value: str) -> str:\n"
            "    return value.strip()\n"
        ),
        encoding="utf-8",
    )
    service_wiki = tmp_path / "service wiki"
    api_wiki = tmp_path / "api wiki"

    service_result = execute_bootstrap(
        BootstrapRequest(
            source_root=source,
            wiki_root=service_wiki,
        )
    )
    api_result = bootstrap_wiki(
        str(source),
        str(api_wiki),
        depth="full",
    )

    assert isinstance(service_result, BootstrapResult)
    assert isinstance(api_result, BootstrapResult)
    assert service_result.schema_version == api_result.schema_version
    assert _tree(service_wiki) == _tree(api_wiki)
    assert capsys.readouterr() == ("", "")

    for wiki_root, result in (
        (service_wiki, service_result),
        (api_wiki, api_result),
    ):
        assert result.summary["manifest_path"].endswith(
            "/.llm-wiki-manifest.json"
        )
        assert result.summary["knowledge_path"].endswith(
            "/.llm-wiki-knowledge.json"
        )
        assert result.summary["knowledge_status"] == "created"
        assert result.summary["knowledge_schema_version"] == "llm-wiki-knowledge/v1"
        assert result.summary["flow_evidence"][0]["detector"] == "builtin"
        assert result.summary["flow_evidence"][0]["evidence"]["flow"][
            "step_count"
        ] >= 2
        assert isinstance(result.summary["dependency_evidence"], dict)
        assert SyncManifest.load(wiki_root).to_payload()["version"] == MANIFEST_VERSION
        assert load_knowledge_state(wiki_root).status is KnowledgeLoadState.VALID


def test_typed_service_returns_normalized_empty_summary_without_output(
    tmp_path, capsys
):
    source = tmp_path / "empty source"
    source.mkdir()
    wiki = tmp_path / "empty wiki"

    result = execute_bootstrap(
        BootstrapRequest(
            source_root=source,
            wiki_root=wiki,
        )
    )

    assert result.summary["manifest_path"] is None
    assert result.summary["knowledge_path"] is None
    assert result.summary["knowledge_status"] is None
    assert result.summary["knowledge_schema_version"] == "llm-wiki-knowledge/v1"
    assert result.created_files == ()
    assert result.updated_files == ()
    assert result.skipped_files == ()
    assert capsys.readouterr() == ("", "")


def test_typed_service_raises_structured_extraction_error_without_output(
    tmp_path, monkeypatch, capsys
):
    source = tmp_path / "source"
    source.mkdir()
    (source / "app.py").write_text("VALUE = 1\n", encoding="utf-8")
    wiki = tmp_path / "wiki"

    monkeypatch.setattr(
        bootstrap_cmd,
        "get_inventory_result",
        lambda *_args, **_kwargs: InventoryResult(
            {},
            {
                "python": ExtractorStatus(
                    "python",
                    "failed",
                    1,
                    "synthetic extraction failure",
                )
            },
        ),
    )

    with pytest.raises(
        BootstrapExtractionError,
        match="python: synthetic extraction failure",
    ):
        execute_bootstrap(
            BootstrapRequest(
                source_root=source,
                wiki_root=wiki,
            )
        )

    assert capsys.readouterr() == ("", "")
    assert not (wiki / ".llm-wiki-manifest.json").exists()
    assert not (wiki / ".llm-wiki-surface.json").exists()
    assert not (wiki / ".llm-wiki-knowledge.json").exists()


def test_api_maps_typed_bootstrap_failures(tmp_path):
    with pytest.raises(BootstrapError, match="does not exist"):
        bootstrap_wiki(
            str(tmp_path / "missing-source"),
            str(tmp_path / "wiki"),
        )


def test_public_overwrite_tombstone_rejects_before_extraction_or_writes(
    tmp_path, monkeypatch
):
    source = tmp_path / "source"
    source.mkdir()
    (source / "app.py").write_text("VALUE = 1\n", encoding="utf-8")
    wiki = tmp_path / "wiki"

    def forbidden_inventory(*_args, **_kwargs):
        pytest.fail("existing-target preflight must run before extraction")

    monkeypatch.setattr(bootstrap_cmd, "get_inventory_result", forbidden_inventory)

    with pytest.raises(BootstrapError, match="overwrite.*no longer supported"):
        bootstrap_wiki(str(source), str(wiki), overwrite=True)

    assert not wiki.exists()


@pytest.mark.parametrize(
    ("relative_path", "content", "expected_route", "excluded_route"),
    (
        (
            "index.md",
            "# Existing wiki\n\nCustom overview.\n",
            "llm-wiki sync --jobs 1",
            "llm-wiki migrate --dry-run",
        ),
        (
            "modules/partial.md",
            "# Partial module\n",
            "llm-wiki migrate --dry-run",
            "llm-wiki sync --jobs 1",
        ),
        (
            ".llm-wiki-manifest.json",
            "{}\n",
            "llm-wiki sync --jobs 1",
            "llm-wiki migrate --dry-run",
        ),
        (
            ".llm-wiki-governance.json",
            "{}\n",
            "llm-wiki migrate --dry-run",
            "llm-wiki sync --jobs 1",
        ),
        (
            ".llm-wiki-verification.json",
            "{}\n",
            "llm-wiki migrate --dry-run",
            "llm-wiki sync --jobs 1",
        ),
    ),
)
def test_typed_service_rejects_existing_wiki_content_before_extraction(
    tmp_path,
    monkeypatch,
    relative_path,
    content,
    expected_route,
    excluded_route,
):
    source = tmp_path / "source"
    source.mkdir()
    (source / "app.py").write_text("VALUE = 1\n", encoding="utf-8")
    wiki = tmp_path / "wiki"
    target = wiki / relative_path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
    before = _tree(wiki)

    def forbidden_inventory(*_args, **_kwargs):
        pytest.fail("existing-target preflight must run before extraction")

    monkeypatch.setattr(bootstrap_cmd, "get_inventory_result", forbidden_inventory)

    with pytest.raises(BootstrapContractError) as exc_info:
        execute_bootstrap(BootstrapRequest(source_root=source, wiki_root=wiki))

    message = str(exc_info.value)
    assert "Bootstrap is first-use only" in message
    assert expected_route in message
    assert excluded_route not in message
    assert "No files were changed" in message
    assert _tree(wiki) == before


def test_typed_service_rejects_partial_init_scaffold_before_extraction(
    tmp_path,
    monkeypatch,
):
    source = tmp_path / "source"
    source.mkdir()
    (source / "app.py").write_text("VALUE = 1\n", encoding="utf-8")
    wiki = tmp_path / "wiki"
    (wiki / "modules").mkdir(parents=True)
    (wiki / "modules" / ".gitkeep").touch()
    before = _tree(wiki)

    monkeypatch.setattr(
        bootstrap_cmd,
        "get_inventory_result",
        lambda *_args, **_kwargs: pytest.fail(
            "partial-scaffold preflight must run before extraction"
        ),
    )

    with pytest.raises(BootstrapContractError, match="Existing wiki content"):
        execute_bootstrap(BootstrapRequest(source_root=source, wiki_root=wiki))

    assert _tree(wiki) == before


@pytest.mark.skipif(not hasattr(os, "symlink"), reason="symlinks unavailable")
def test_typed_service_rejects_symlinked_scaffold_entry(tmp_path, monkeypatch):
    source = tmp_path / "source"
    source.mkdir()
    (source / "app.py").write_text("VALUE = 1\n", encoding="utf-8")
    wiki = tmp_path / "wiki"
    wiki.mkdir()
    outside = tmp_path / "outside.md"
    outside.write_text("outside\n", encoding="utf-8")
    link = wiki / "index.md"
    try:
        link.symlink_to(outside)
    except OSError as exc:
        pytest.skip(f"file symlinks unavailable: {exc}")

    monkeypatch.setattr(
        bootstrap_cmd,
        "get_inventory_result",
        lambda *_args, **_kwargs: pytest.fail(
            "symlink preflight must run before extraction"
        ),
    )

    with pytest.raises(BootstrapContractError, match="Existing wiki content"):
        execute_bootstrap(BootstrapRequest(source_root=source, wiki_root=wiki))

    assert outside.read_text(encoding="utf-8") == "outside\n"
    assert link.is_symlink()


@pytest.mark.parametrize(
    ("target_name", "overwrite", "source_adapter"),
    (
        (None, True, True),
        ("sibling", True, True),
        ("wiki", False, True),
        ("wiki", True, False),
    ),
)
def test_internal_documentation_refresh_rejects_every_noncanonical_authority(
    tmp_path,
    monkeypatch,
    target_name,
    overwrite,
    source_adapter,
):
    source = tmp_path / "source"
    source.mkdir()
    (source / "app.py").write_text("VALUE = 1\n", encoding="utf-8")
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    wiki = workspace if target_name is None else workspace / target_name
    before = _tree(workspace)

    monkeypatch.setattr(
        bootstrap_cmd,
        "get_inventory_result",
        lambda *_args, **_kwargs: pytest.fail(
            "internal refresh authority checks must run before extraction"
        ),
    )

    with pytest.raises(BootstrapContractError):
        bootstrap_cmd._execute_documentation_workspace_refresh(
            BootstrapRequest(
                source_root=source,
                wiki_root=wiki,
                overwrite=overwrite,
                source_adapter=source_adapter,
            ),
            workspace_root=workspace,
        )

    assert _tree(workspace) == before


@pytest.mark.skipif(not hasattr(os, "symlink"), reason="symlinks unavailable")
def test_internal_documentation_refresh_rejects_workspace_wiki_symlink_escape(
    tmp_path,
    monkeypatch,
):
    source = tmp_path / "source"
    source.mkdir()
    (source / "app.py").write_text("VALUE = 1\n", encoding="utf-8")
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    marker = outside / "marker.md"
    marker.write_text("outside stays untouched\n", encoding="utf-8")
    wiki_link = workspace / "wiki"
    try:
        wiki_link.symlink_to(outside, target_is_directory=True)
    except OSError as exc:
        pytest.skip(f"directory symlink creation is unavailable: {exc}")

    monkeypatch.setattr(
        bootstrap_cmd,
        "get_inventory_result",
        lambda *_args, **_kwargs: pytest.fail(
            "symlink authority check must run before extraction"
        ),
    )

    with pytest.raises(BootstrapContractError, match="exactly"):
        bootstrap_cmd._execute_documentation_workspace_refresh(
            BootstrapRequest(
                source_root=source,
                wiki_root=wiki_link,
                overwrite=True,
                source_adapter=True,
            ),
            workspace_root=workspace,
        )

    assert marker.read_text(encoding="utf-8") == "outside stays untouched\n"
    assert wiki_link.is_symlink()


def test_typed_service_rejects_source_nested_under_wiki_output(tmp_path):
    wiki = tmp_path / "documentation output Ω"
    source = wiki / "modules" / "source"
    source.mkdir(parents=True)
    (source / "app.py").write_text("VALUE = 1\n", encoding="utf-8")
    before = _tree(wiki)

    with pytest.raises(BootstrapContractError, match="must not overlap"):
        execute_bootstrap(BootstrapRequest(source_root=source, wiki_root=wiki))

    assert _tree(wiki) == before


@pytest.mark.skipif(not hasattr(os, "symlink"), reason="symlinks unavailable")
def test_typed_service_resolves_symlink_before_reverse_overlap_check(tmp_path):
    wiki = tmp_path / "real documentation output"
    source = wiki / "source"
    source.mkdir(parents=True)
    (source / "app.py").write_text("VALUE = 1\n", encoding="utf-8")
    wiki_alias = tmp_path / "documentation output alias"
    try:
        wiki_alias.symlink_to(wiki, target_is_directory=True)
    except OSError as exc:
        pytest.skip(f"directory symlink creation is unavailable: {exc}")
    before = _tree(wiki)

    with pytest.raises(BootstrapContractError, match="must not overlap"):
        execute_bootstrap(BootstrapRequest(source_root=source, wiki_root=wiki_alias))

    assert _tree(wiki) == before


def test_api_forwards_deterministic_bootstrap_options(monkeypatch, tmp_path):
    source = tmp_path / "source"
    source.mkdir()
    captured = {}

    def fake_execute(request):
        captured["request"] = request
        return BootstrapResult(summary={"schema_version": "test/v1"})

    monkeypatch.setattr(bootstrap_cmd, "execute_bootstrap", fake_execute)

    bootstrap_wiki(
        str(source),
        str(tmp_path / "wiki"),
        depth="shallow",
        skip_workflows=True,
        skip_flows=True,
        skip_data_flow=True,
        skip_dependencies=True,
        api_contracts=True,
        openapi_file="openapi.yaml",
        dependency_graph_detail="package",
        overwrite=False,
        helper_cache_dir=str(tmp_path / "helpers"),
        include_tests=["tests/**"],
        trust_source_plugins=True,
    )

    request = captured["request"]
    assert request.depth == "shallow"
    assert request.skip_workflows is True
    assert request.skip_flows is True
    assert request.skip_data_flow is True
    assert request.skip_dependencies is True
    assert request.api_contracts is True
    assert request.openapi_file == "openapi.yaml"
    assert request.dependency_graph_detail == "package"
    assert request.overwrite is False
    assert request.source_adapter is True
    assert request.helper_cache_dir == str(tmp_path / "helpers")
    assert list(request.include_tests or ()) == ["tests/**"]
    assert request.trust_source_plugins is True
