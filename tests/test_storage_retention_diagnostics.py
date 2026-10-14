"""Retention diagnoses do not authorize deletion or suppress audit limits."""

from dataclasses import replace
import json
import sys

import pytest

from llm_wiki_cli.cli import main
from llm_wiki_cli.services import knowledge_storage_diagnostics as diagnostics
from llm_wiki_cli.services.knowledge_artifacts import build_knowledge_commit_plan, commit_knowledge_artifacts
from llm_wiki_cli.services.knowledge_loader import load_knowledge_state
from llm_wiki_cli.services.knowledge_storage import KnowledgeStorageError, canonical_bytes, digest, object_path
from llm_wiki_cli.services.knowledge_storage_lifecycle import prune_knowledge_storage, restore_pruned_storage
from tests.test_knowledge_loader import _committed_state
from tests.test_knowledge_storage_lifecycle import git, snapshot


def test_limit_keeps_failed_cli_and_partial_sizes_without_reading_or_pruning(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    root = tmp_path / "wiki with spaces"
    root.mkdir()
    _committed_state(root)
    relative = object_path("sha256:" + "0" * 64)
    path = root / relative
    path.parent.mkdir(parents=True)
    budget = (root / ".llm-wiki-knowledge.json").stat().st_size + 100
    path.write_bytes(b"x" * (budget + 1))
    before = snapshot(root)
    monkeypatch.setattr(diagnostics, "MAX_EXPANDED_BYTES", budget)
    monkeypatch.setattr(diagnostics, "load_knowledge_state", lambda *_: pytest.fail("full audit after size exhaustion"))
    monkeypatch.setattr(sys, "argv", ["llm-wiki", "knowledge", "storage-check", "--wiki-dir", root.name, "--full"])
    with pytest.raises(SystemExit) as exc:
        main()
    assert exc.value.code == 1
    report = json.loads(capsys.readouterr().out)
    assert report["error"]["code"] == "storage-limit"
    assert not report["ok"] and report["integrity"] == "not-audited"
    assert report["objects"] == 1 and report["object_bytes"] == path.stat().st_size
    retention = report["retention"]
    assert retention["namespace_complete"] and not retention["size_inspection_complete"]
    assert retention["max_inspection_bytes"] == budget
    assert retention["referenced_objects"] is None and retention["unreferenced_candidates"] is None
    action = report["next_action"]
    assert action["dry_run"] and action["argv"] == ["llm-wiki", "knowledge", "prune-storage", "--wiki-dir", str(root)]
    assert "--apply" not in action["argv"]
    assert snapshot(root) == before
    assert not (tmp_path / ".llm-wiki-storage-recovery").exists()


def test_namespace_exhaustion_cannot_report_empty_reachability(tmp_path, monkeypatch):
    _committed_state(tmp_path)
    before = snapshot(tmp_path)
    def exhausted(_):
        raise KnowledgeStorageError("objects", "object discovery exceeds its entry limit", code="storage-limit")
    monkeypatch.setattr(diagnostics, "stored_object_paths", exhausted)
    report = diagnostics.storage_report(tmp_path, full=True)
    assert not report["ok"] and not report["retention"]["namespace_complete"]
    assert not report["retention"]["size_inspection_complete"]
    assert report["unreferenced_objects"] is None
    assert report["retention"]["unreferenced_candidates"] is None
    assert report["next_action"]["operation"] == "prune-storage"
    assert snapshot(tmp_path) == before


def test_quick_and_flat_full_have_distinct_reachability_without_implicit_migration(tmp_path):
    _committed_state(tmp_path)
    before = snapshot(tmp_path)
    quick = diagnostics.storage_report(tmp_path)
    assert quick["ok"] and quick["retention"]["size_inspection_complete"]
    assert quick["retention"]["referenced_objects"] is None
    full = diagnostics.storage_report(tmp_path, full=True)
    assert full["ok"] and full["format"] == "v1"
    assert full["retention"]["referenced_objects"] == 0
    assert full["retention"]["unreferenced_candidates"] == 0
    assert "next_action" not in full
    with pytest.raises(KnowledgeStorageError, match="indexed root"):
        prune_knowledge_storage(tmp_path)
    assert snapshot(tmp_path) == before


def test_other_storage_errors_keep_their_distinct_failure(tmp_path, monkeypatch):
    _committed_state(tmp_path)
    def changed(_):
        raise KnowledgeStorageError("objects", "changed", code="storage-mutation")
    monkeypatch.setattr(diagnostics, "stored_object_paths", changed)
    with pytest.raises(KnowledgeStorageError) as exc:
        diagnostics.storage_report(tmp_path)
    assert exc.value.code == "storage-mutation"


@pytest.mark.parametrize("knowledge_format,manifest_format", [
    ("sharded-v2", "v5"), ("sharded-v2", "indexed-v6"),
    ("v1", "indexed-v6"), ("packed-v4-deflate", "indexed-v6"),
])
def test_real_generations_classify_and_recover_retention_without_changing_anchors(
    tmp_path, knowledge_format, manifest_format,
):
    root = tmp_path / "wiki"
    root.mkdir()
    _, original, _ = _committed_state(root)
    git(tmp_path, "init", "-q")
    git(tmp_path, "add", "wiki")
    git(tmp_path, "commit", "-q", "-m", "independent active fixture")
    head = git(tmp_path, "rev-parse", "HEAD")
    authored = {k: v for k, v in snapshot(root).items() if k.endswith(".md")}
    def generation(number):
        current = load_knowledge_state(root)
        assert current.knowledge is not None and current.manifest_basis is not None
        model = replace(current.knowledge, extensions={**current.knowledge.extensions, "consumer/retention-generation": number})
        manifest = current.manifest_basis.without_artifact_hashes()
        manifest.generation_inputs["consumer/retention-generation"] = str(number) * 9_000
        plan = build_knowledge_commit_plan(root, surface_index_bytes=original.surface_index.content,
            knowledge_index=model, manifest=manifest, knowledge_format=knowledge_format, manifest_format=manifest_format)
        commit_knowledge_artifacts(plan)
    generation(0)
    generation(1)
    stale = prune_knowledge_storage(root)["plan"]
    generation(2)
    generation(3)
    # Recognized spelling alone does not establish valid provider content.
    foreign_raw = canonical_bytes({"user-owned": "keep"})
    foreign = root / object_path(digest(foreign_raw))
    foreign.parent.mkdir(parents=True, exist_ok=True)
    foreign.write_bytes(foreign_raw)
    unknown = foreign.parent / "notes.txt"
    unknown.write_bytes(b"preserve user notes")
    before = snapshot(root)
    with pytest.raises(KnowledgeStorageError, match="generation, root or candidate preimages changed"):
        prune_knowledge_storage(root, dry_run=False, plan=stale, recovery_dir=tmp_path / "stale-recovery")
    assert snapshot(root) == before and not (tmp_path / "stale-recovery").exists()
    report = diagnostics.storage_report(root, full=True)
    assert report["ok"] and report["integrity"] == "valid-committed-snapshot"
    state = load_knowledge_state(root)
    assert state.validated_artifacts is not None
    active = state.validated_artifacts.storage_objects
    retention = report["retention"]
    assert retention["referenced_objects"] == len(active)
    assert retention["referenced_bytes"] == sum(map(len, active.values()))
    unreferenced = set(before) - set(active)
    # Independently restrict the namespace size inventory, not all wiki files.
    candidates = set(report["unreferenced_objects"])
    assert foreign.relative_to(root).as_posix() in candidates
    assert candidates <= unreferenced and candidates.isdisjoint(active)
    assert retention["unreferenced_candidates"] == len(candidates) > 1
    assert retention["unreferenced_candidate_bytes"] == sum(len(before[p]) for p in candidates)
    assert retention["candidate_validation"] == "not-performed"
    assert unknown.relative_to(root).as_posix() in report["unknown_entries"]
    preview = prune_knowledge_storage(root)
    assert preview["unreferenced_objects"] and not preview["budget_exhausted"]
    assert foreign.relative_to(root).as_posix() in preview["retained"]
    assert unknown.relative_to(root).as_posix() in preview["retained"]
    assert snapshot(root) == before  # Diagnostic and preview reads never clean.
    applied = prune_knowledge_storage(root, dry_run=False, plan=preview["plan"], recovery_dir=tmp_path / "recovery")
    assert set(applied["removed"]) == set(preview["unreferenced_objects"])
    assert all((root / p).read_bytes() == content for p, content in active.items())
    assert (root / ".llm-wiki-knowledge.json").read_bytes() == before[".llm-wiki-knowledge.json"]
    assert (root / ".llm-wiki-manifest.json").read_bytes() == before[".llm-wiki-manifest.json"]
    assert {k: v for k, v in snapshot(root).items() if k.endswith(".md")} == authored
    assert git(tmp_path, "rev-parse", "HEAD") == head
    after = diagnostics.storage_report(root, full=True)
    assert after["ok"] and after["unreferenced_objects"] == [foreign.relative_to(root).as_posix()]
    # Recovery must contain and restore each exact removed preimage.
    recovered = restore_pruned_storage(root, applied["recovery_manifest"], dry_run=False)
    assert set(recovered["restored"]) == set(applied["removed"])
    assert snapshot(root) == before
    assert git(tmp_path, "rev-parse", "HEAD") == head
