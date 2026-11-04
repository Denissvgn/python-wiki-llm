"""Adopted no-ops reconcile current review inputs before skipping generation."""

from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from llm_wiki_cli import api
from llm_wiki_cli.commands import sync_cmd
from llm_wiki_cli.services import (
    knowledge_artifacts, knowledge_generation, knowledge_orchestration,
    knowledge_reuse, sync_analysis_cache,
)
from llm_wiki_cli.services.knowledge_loader import load_knowledge_state
from llm_wiki_cli.services.maintenance_protocol import snapshot_wiki
from tests.developer_value.fixtures import POLICY_SOURCE


def _sync(**options):
    sync_cmd.run(SimpleNamespace(src_dir="src", wiki_dir="wiki", cache_dir="cache",
                                 no_plugins=True, jobs=1, force=True, **options))


@pytest.fixture(params=["v1", "packed-v4-deflate"])
def legacy(tmp_path, monkeypatch, request):
    monkeypatch.chdir(tmp_path)
    Path("src").mkdir()
    Path("src/policy.py").write_text(POLICY_SOURCE, encoding="utf-8")
    api.bootstrap_wiki("src", "wiki", knowledge_format=request.param)
    api.adopt_maintenance("src", "wiki", recovery_dir="recovery")
    return tmp_path


def _trap_builders(monkeypatch, *, extraction=True):
    def unexpected(*args, **kwargs):
        pytest.fail("verified adopted no-op performed generation work")

    if extraction:
        monkeypatch.setattr(sync_cmd, "_extract_current_inventory", unexpected)
    monkeypatch.setattr(sync_cmd, "_build_sync_graph_observations", unexpected)
    monkeypatch.setattr(knowledge_orchestration, "build_knowledge_generation_plan", unexpected)
    monkeypatch.setattr(knowledge_generation, "materialize_typed_graph", unexpected)
    monkeypatch.setattr(knowledge_generation, "build_knowledge_commit_plan", unexpected)
    monkeypatch.setattr(knowledge_artifacts, "write_bytes_atomic", unexpected)
    monkeypatch.setattr(sync_analysis_cache, "build_payload", unexpected)


def test_explicit_adopted_migration_preserves_ordinary_legacy_noop_then_enables_fast_path(
    legacy, monkeypatch, capsys,
):
    before = snapshot_wiki("wiki")
    _sync()
    assert snapshot_wiki("wiki") == before
    loaded = load_knowledge_state("wiki")
    assert loaded.knowledge is not None
    assert knowledge_reuse.REUSE_EXTENSION_KEY not in loaded.knowledge.extensions
    _sync(rebuild_knowledge=True)
    assert "Maintenance reuse migration: completed" in capsys.readouterr().out
    loaded = load_knowledge_state("wiki")
    assert loaded.knowledge is not None and loaded.manifest_basis is not None
    commitment = loaded.knowledge.extensions[knowledge_reuse.REUSE_EXTENSION_KEY]
    assert commitment == loaded.manifest_basis.generation_inputs[knowledge_reuse.REUSE_INPUT_KEY]
    assert commitment["lifecycle_hash"] == knowledge_reuse.manifest_lifecycle_hash(loaded.manifest_basis)
    assert Path("cache", sync_analysis_cache.FILENAME).exists()
    before = snapshot_wiki("wiki")
    _trap_builders(monkeypatch)
    _sync()
    assert snapshot_wiki("wiki") == before


@pytest.mark.parametrize("change", ["source", "prose"])
def test_required_change_primes_adopted_reuse_without_migration(legacy, monkeypatch, change):
    if change == "source":
        source = Path("src/policy.py")
        source.write_text(source.read_text().replace("values[:limit]", "values[:limit - 1]"))
    else:
        page = Path("wiki/modules/policy.md")
        page.write_text(page.read_text() + "\n## Operator notes\nRetain these reviewed inputs.\n")
    _sync()
    before = snapshot_wiki("wiki")
    _trap_builders(monkeypatch)
    _sync()
    assert snapshot_wiki("wiki") == before


def test_maintenance_acknowledgment_rebinds_lifecycle_without_losing_fast_path(legacy, monkeypatch):
    _sync(rebuild_knowledge=True)
    status = api.get_maintenance_status("src", "wiki")
    record = next(row for row in status["records"] if row["basis_available"])
    assert status["state_hash"] is not None and record["expected_basis"] is not None
    api.acknowledge_maintenance(
        "src", "wiki", record_id=record["record_id"], expected_state_hash=status["state_hash"],
        expected_basis=record["expected_basis"], actor_kind="agent", actor_id="reviewed-inputs",
    )
    loaded = load_knowledge_state("wiki")
    assert loaded.knowledge is not None and loaded.manifest_basis is not None
    knowledge_reuse.validate_reuse_artifact_parity(loaded.knowledge, loaded.manifest_basis)
    before = snapshot_wiki("wiki")
    _trap_builders(monkeypatch)
    _sync()
    assert snapshot_wiki("wiki") == before


def test_reconciliation_change_cannot_use_committed_noop_hint(legacy, monkeypatch):
    _sync(rebuild_knowledge=True)
    from llm_wiki_cli.services import maintenance_evidence

    original = maintenance_evidence.reconcile_pending_maintenance

    def changed(*args, **kwargs):
        result = original(*args, **kwargs)
        return {**result, "generation": result["generation"] + 1}

    monkeypatch.setattr(maintenance_evidence, "reconcile_pending_maintenance", changed)
    with patch.object(sync_cmd, "_build_sync_graph_observations",
                      side_effect=RuntimeError("normal path required")):
        # The graph may be reused from the authenticated analysis cache, but the
        # final generation must run if current reconciliation changes authority.
        with patch.object(knowledge_orchestration, "build_knowledge_generation_plan",
                          side_effect=RuntimeError("normal path required")):
            with pytest.raises(RuntimeError, match="normal path required"):
                _sync()


def test_raw_markdown_change_during_reuse_is_rejected_even_when_normalized_text_matches(legacy, monkeypatch):
    _sync(rebuild_knowledge=True)
    artifacts = {name: Path("wiki", name).read_bytes() for name in (
        ".llm-wiki-surface.json", ".llm-wiki-knowledge.json", ".llm-wiki-manifest.json",
    )}
    original = sync_cmd.source_snapshot_matches_current_files
    changed = []

    def mutate(snapshot):
        result = original(snapshot)
        page = Path("wiki/modules/policy.md")
        page.write_bytes(page.read_bytes().replace(b"\n", b"\r\n"))
        changed.append(True)
        return result

    monkeypatch.setattr(sync_cmd, "source_snapshot_matches_current_files", mutate)
    _trap_builders(monkeypatch)
    with pytest.raises((ValueError, SystemExit)):
        _sync()
    assert changed
    assert artifacts == {name: Path("wiki", name).read_bytes() for name in artifacts}


def test_unchanged_deselected_history_does_not_disable_adopted_reuse(legacy, monkeypatch):
    Path("src/kept.py").write_text("class Kept:\n    pass\n", encoding="utf-8")
    Path("src/selection.json").write_text(json.dumps({
        "schema_version": "llm-wiki-source-selection/v1", "include": ["kept.py"], "exclude": [],
    }))
    _sync(source_selection="selection.json")
    before = snapshot_wiki("wiki")
    _trap_builders(monkeypatch, extraction=False)
    _sync(source_selection="selection.json")
    assert snapshot_wiki("wiki") == before


def test_unchanged_retired_owner_in_selected_module_does_not_disable_reuse(legacy, monkeypatch):
    Path("src/policy.py").write_text("def public_values():\n    return [1, 2, 3]\n")
    _sync()
    assert Path("wiki/entities/Batch.md").exists()
    before = snapshot_wiki("wiki")
    _trap_builders(monkeypatch, extraction=False)
    _sync()
    assert snapshot_wiki("wiki") == before
