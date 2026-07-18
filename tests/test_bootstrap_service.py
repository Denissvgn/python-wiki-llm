"""Typed bootstrap service and public API boundary tests."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from llm_wiki_cli.api import BootstrapError, bootstrap_wiki
from llm_wiki_cli.commands import bootstrap_cmd
from llm_wiki_cli.commands.bootstrap_cmd import execute_bootstrap
from llm_wiki_cli.services.bootstrap_service import (
    BootstrapContractError,
    BootstrapRequest,
    BootstrapResult,
)


def _tree(root: Path) -> dict[str, bytes]:
    return {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in root.rglob("*")
        if path.is_file()
    }


def test_api_and_typed_service_produce_equivalent_wiki_trees(tmp_path):
    source = tmp_path / "source with spaces Ω"
    source.mkdir()
    (source / "app.py").write_text(
        '"""Example service."""\n\ndef run(value: str) -> str:\n    return value\n',
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


def test_api_maps_typed_bootstrap_failures(tmp_path):
    with pytest.raises(BootstrapError, match="does not exist"):
        bootstrap_wiki(
            str(tmp_path / "missing-source"),
            str(tmp_path / "wiki"),
        )


def test_typed_service_rejects_source_nested_under_wiki_output(tmp_path):
    wiki = tmp_path / "documentation output Ω"
    source = wiki / "modules" / "source"
    source.mkdir(parents=True)
    (source / "app.py").write_text("VALUE = 1\n", encoding="utf-8")

    with pytest.raises(BootstrapContractError, match="must not overlap"):
        execute_bootstrap(BootstrapRequest(source_root=source, wiki_root=wiki))

    assert _tree(wiki) == {"modules/source/app.py": b"VALUE = 1\n"}


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

    with pytest.raises(BootstrapContractError, match="must not overlap"):
        execute_bootstrap(BootstrapRequest(source_root=source, wiki_root=wiki_alias))

    assert _tree(wiki) == {"source/app.py": b"VALUE = 1\n"}


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
        overwrite=True,
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
    assert request.overwrite is True
    assert request.source_adapter is True
    assert request.helper_cache_dir == str(tmp_path / "helpers")
    assert list(request.include_tests or ()) == ["tests/**"]
    assert request.trust_source_plugins is True
