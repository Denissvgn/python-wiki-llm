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


def test_source_mutation_after_fast_result_is_rejected_by_outer_final_verification(legacy, monkeypatch, capsys):
    _sync(rebuild_knowledge=True)
    before = snapshot_wiki("wiki")
    original = knowledge_reuse.unchanged_commit_result
    def change_after_result(*args, **kwargs):
        result = original(*args, **kwargs)
        source = Path("src/policy.py")
        source.write_text(source.read_text() + "\n# concurrent source edit\n")
        return result
    _trap_builders(monkeypatch)
    monkeypatch.setattr(knowledge_reuse, "unchanged_commit_result", change_after_result)
    with pytest.raises(SystemExit) as error:
        _sync()
    assert error.value.code == 2
    assert "Source changed" in capsys.readouterr().err
    assert snapshot_wiki("wiki") == before


@pytest.mark.parametrize("budget_phase", ["capture", "recheck"])
def test_raw_markdown_inspection_budget_falls_back_to_guarded_generation(legacy, monkeypatch, budget_phase):
    from llm_wiki_cli.services import knowledge_storage_io
    from llm_wiki_cli.services.wiki_surface import collect_wiki_pages

    _sync(rebuild_knowledge=True)
    before = snapshot_wiki("wiki")
    total = sum(page.path.stat().st_size for page in collect_wiki_pages("wiki"))
    budget = total - 1 if budget_phase == "capture" else total + 1
    original_check = knowledge_reuse.maintenance_reuse_check
    original_session = knowledge_storage_io.StorageReadSession

    class BoundedReadSession(original_session):
        def __init__(self, root):
            super().__init__(root, max_bytes=budget)

        def read(self, relative, maximum):
            pytest.fail("oversized reuse capture must decline before retaining provisional page reads")

    def bounded_check(*args, **kwargs):
        # Scope the lower budget to the advisory shortcut, keeping the normal
        # artifact readers under their independent existing resource contracts.
        with patch.object(knowledge_storage_io, "StorageReadSession", BoundedReadSession):
            return original_check(*args, **kwargs)

    monkeypatch.setattr(knowledge_reuse, "maintenance_reuse_check", bounded_check)
    with patch.object(knowledge_orchestration, "build_knowledge_generation_plan",
                      wraps=knowledge_orchestration.build_knowledge_generation_plan) as build:
        _sync()
    assert build.call_count >= 1
    assert snapshot_wiki("wiki") == before


@pytest.mark.parametrize("growth", [1, "exhaust-capture"])
def test_page_growth_after_budget_preflight_cannot_be_treated_as_a_cache_miss(legacy, monkeypatch, growth):
    from llm_wiki_cli.services import knowledge_storage_io
    from llm_wiki_cli.services.wiki_surface import collect_wiki_pages

    _sync(rebuild_knowledge=True)
    total = sum(page.path.stat().st_size for page in collect_wiki_pages("wiki"))
    original_check = knowledge_reuse.maintenance_reuse_check
    original_session = knowledge_storage_io.StorageReadSession
    changed = []

    class GrowingReadSession(original_session):
        def __init__(self, root):
            super().__init__(root, max_bytes=2 * total)

        def read(self, relative, maximum):
            if not changed:
                page = self.root / relative
                extra = 2 * total if growth == "exhaust-capture" else growth
                page.write_bytes(page.read_bytes() + b" " * extra)
                changed.append(relative)
            return super().read(relative, maximum)

    def growing_check(*args, **kwargs):
        with patch.object(knowledge_storage_io, "StorageReadSession", GrowingReadSession):
            return original_check(*args, **kwargs)

    monkeypatch.setattr(knowledge_reuse, "maintenance_reuse_check", growing_check)
    _trap_builders(monkeypatch, extraction=False)
    with pytest.raises(knowledge_storage_io.KnowledgeStorageError) as rejected:
        _sync(dry_run=True)
    assert rejected.value.code == "storage-budget-exhausted"
    assert changed


def test_page_removed_before_budget_preflight_is_rejected(legacy, monkeypatch):
    from llm_wiki_cli.services import knowledge_storage_io, wiki_surface

    _sync(rebuild_knowledge=True)
    original_check = knowledge_reuse.maintenance_reuse_check
    original_collect = wiki_surface.collect_wiki_pages
    removed = []

    def remove_after_collection(root):
        pages = original_collect(root)
        pages[0].path.unlink()
        removed.append(pages[0].relative_path)
        return pages

    def changed_check(*args, **kwargs):
        with patch.object(wiki_surface, "collect_wiki_pages", remove_after_collection):
            return original_check(*args, **kwargs)

    monkeypatch.setattr(knowledge_reuse, "maintenance_reuse_check", changed_check)
    _trap_builders(monkeypatch, extraction=False)
    with pytest.raises(knowledge_storage_io.KnowledgeStorageError) as rejected:
        _sync(dry_run=True)
    assert rejected.value.code == "storage-mutation"
    assert removed


def test_late_budget_exhaustion_does_not_hide_an_evicted_page_mutation(legacy, monkeypatch):
    from llm_wiki_cli.services import knowledge_storage_io
    from llm_wiki_cli.services.wiki_surface import collect_wiki_pages

    notes = Path("wiki/guides")
    notes.mkdir(exist_ok=True)
    for index in range(150):
        (notes / f"note-{index:03}.md").write_text(f"# Note {index}\n")
    _sync(rebuild_knowledge=True)
    pages = collect_wiki_pages("wiki")
    total = sum(page.path.stat().st_size for page in pages)
    original_check = knowledge_reuse.maintenance_reuse_check
    original_session = knowledge_storage_io.StorageReadSession
    changed = []

    class MutatingReadSession(original_session):
        def __init__(self, root):
            super().__init__(root, max_bytes=2 * total)

        def read(self, relative, maximum):
            if relative == pages[-1].relative_path:
                first = self.root / pages[0].relative_path
                assert self._phase is not None and first not in self._phase.files
                first.write_bytes(first.read_bytes().replace(b"\n", b"\r"))
                last = self.root / relative
                last.write_bytes(last.read_bytes() + b" " * (2 * total))
                changed.append(True)
            return super().read(relative, maximum)

    def mutating_check(*args, **kwargs):
        with patch.object(knowledge_storage_io, "StorageReadSession", MutatingReadSession):
            return original_check(*args, **kwargs)

    monkeypatch.setattr(knowledge_reuse, "maintenance_reuse_check", mutating_check)
    _trap_builders(monkeypatch, extraction=False)
    with pytest.raises(knowledge_storage_io.KnowledgeStorageError) as rejected:
        _sync(dry_run=True)
    assert rejected.value.code == "storage-budget-exhausted"
    assert changed


@pytest.mark.parametrize("mutate", [False, True])
def test_reserved_raw_markdown_recheck_has_exact_budget_and_rejects_mutation(legacy, monkeypatch, mutate):
    from llm_wiki_cli.services import knowledge_storage_io
    from llm_wiki_cli.services.wiki_surface import collect_wiki_pages

    _sync(rebuild_knowledge=True)
    before = snapshot_wiki("wiki")
    total = sum(page.path.stat().st_size for page in collect_wiki_pages("wiki"))
    original_check = knowledge_reuse.maintenance_reuse_check
    original_session = knowledge_storage_io.StorageReadSession

    class BoundedReadSession(original_session):
        def __init__(self, root):
            super().__init__(root, max_bytes=2 * total)

    def bounded_check(*args, **kwargs):
        with patch.object(knowledge_storage_io, "StorageReadSession", BoundedReadSession):
            return original_check(*args, **kwargs)

    original_matches = sync_cmd.source_snapshot_matches_current_files

    def mutate_after_capture(snapshot):
        result = original_matches(snapshot)
        page = Path("wiki/modules/policy.md")
        raw = page.read_bytes()
        # CR and LF have identical normalized text and byte lengths, so the
        # exact guarded recheck must detect this independently of wiki hashes.
        page.write_bytes(raw.replace(b"\n", b"\r"))
        return result

    monkeypatch.setattr(knowledge_reuse, "maintenance_reuse_check", bounded_check)
    _trap_builders(monkeypatch)
    if mutate:
        monkeypatch.setattr(sync_cmd, "source_snapshot_matches_current_files", mutate_after_capture)
        with pytest.raises(knowledge_storage_io.KnowledgeStorageError) as rejected:
            _sync()
        assert rejected.value.code == "storage-mutation"
    else:
        _sync()
        assert snapshot_wiki("wiki") == before
