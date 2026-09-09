"""Portable runtime destination failures preserve useful command results."""

from __future__ import annotations

import errno
from pathlib import Path
from types import SimpleNamespace

import pytest

from llm_wiki_cli import cli
from llm_wiki_cli.services import extraction_service, runtime_output
from llm_wiki_cli.services.inventory_cache import (
    InventoryCache,
    InventoryCacheOptions,
    cache_options_from_args,
)
from llm_wiki_cli.services.lint_service import build_report


def denied(*args, **kwargs):
    raise OSError(errno.EROFS, "injected read-only filesystem")


def test_preflight_preserves_existing_file_and_cleans_probes(tmp_path):
    target = tmp_path / "nested/report.md"
    target.parent.mkdir()
    target.write_bytes(b"original report\n")
    runtime_output.preflight_output_path(target)
    assert target.read_bytes() == b"original report\n"
    assert list(target.parent.iterdir()) == [target]


@pytest.mark.parametrize("entry", ["extract", "lint"])
def test_explicit_cache_rejected_before_snapshot(tmp_path, monkeypatch, entry):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "wiki").mkdir()
    monkeypatch.setattr(runtime_output, "preflight_output_path", denied)
    monkeypatch.setattr(
        extraction_service,
        "_source_snapshot_for_inventory_request",
        lambda *_: pytest.fail("source snapshot"),
    )
    options = InventoryCacheOptions(enabled=True, cache_dir=str(tmp_path / "cache"))
    with pytest.raises(
        runtime_output.RuntimeOutputError, match="explicit cache destination"
    ):
        if entry == "extract":
            extraction_service.get_inventory_result(
                str(tmp_path), cache_options=options
            )
        else:
            build_report("wiki", str(tmp_path), cache_options=options)


def test_implicit_cache_failure_disables_persistence_and_warns(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("LLM_WIKI_CACHE_DIR", raising=False)
    (tmp_path / ".git").mkdir()
    (tmp_path / "app.py").write_text("class App: pass\n", encoding="utf-8")
    warnings = []
    monkeypatch.setattr(runtime_output, "preflight_output_path", denied)
    result = extraction_service.get_inventory_result(
        str(tmp_path),
        deep=True,
        cache_options=InventoryCacheOptions(enabled=True, warning=warnings.append),
    )
    assert "app.py" in result.inventory
    assert result.cache_stats is not None
    assert result.cache_stats.enabled is False
    assert result.cache_stats.status == "disabled"
    assert result.cache_stats.failure_stage == "preflight"
    assert len(warnings) == 1
    assert "--cache-dir" in warnings[0]
    assert list((tmp_path / ".git").iterdir()) == []


def test_environment_cache_override_is_explicit(tmp_path, monkeypatch):
    monkeypatch.setenv("LLM_WIKI_CACHE_DIR", str(tmp_path / "env-cache"))
    monkeypatch.setattr(runtime_output, "preflight_output_path", denied)
    with pytest.raises(runtime_output.RuntimeOutputError, match="explicit cache"):
        InventoryCache(tmp_path, InventoryCacheOptions(enabled=True))


def test_cache_parent_save_failure_is_visible_without_stats(
    tmp_path, monkeypatch, capsys
):
    options = cache_options_from_args(
        SimpleNamespace(cache_dir=str(tmp_path / "cache"))
    )
    assert options.stats_enabled is False
    cache = InventoryCache(tmp_path, options)
    cache.save({}, {"old.py": {}})
    assert cache.path is not None
    previous = cache.path.read_bytes()
    monkeypatch.setattr(Path, "mkdir", denied)
    cache.save({}, {"new.py": {}})
    assert cache.path.read_bytes() == previous
    assert cache.stats.status == "save_failed"
    assert cache.stats.saved_entries == 0
    assert cache.stats.failure_stage == "save"
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "not saved" in captured.err


def test_no_cache_ignores_environment_and_writes_nothing(tmp_path, monkeypatch):
    monkeypatch.setenv("LLM_WIKI_CACHE_DIR", str(tmp_path / "unusable"))
    monkeypatch.setattr(
        runtime_output,
        "preflight_output_path",
        lambda *_: pytest.fail("preflighted disabled cache"),
    )
    cache = InventoryCache(
        tmp_path, cache_options_from_args(SimpleNamespace(no_cache=True))
    )
    cache.save({}, {})
    assert cache.enabled is False
    assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize("option", ["--cache-dir=cache", "--rebuild-cache"])
def test_cli_rejects_contradictory_cache_flags(tmp_path, monkeypatch, capsys, option):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr("sys.argv", ["llm-wiki", "lint", "--no-cache", option])
    with pytest.raises(SystemExit) as error:
        cli.main()
    assert error.value.code == 2
    assert "cannot be combined" in capsys.readouterr().err


def test_preflight_replace_failure_cleans_probes_and_preserves_target(
    tmp_path, monkeypatch
):
    target = tmp_path / "report.md"
    target.write_bytes(b"old\n")
    monkeypatch.setattr(runtime_output.os, "replace", denied)
    with pytest.raises(OSError):
        runtime_output.preflight_output_path(target)
    assert list(tmp_path.iterdir()) == [target]
    assert target.read_bytes() == b"old\n"
