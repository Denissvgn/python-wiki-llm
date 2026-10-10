"""Durable ordinary review survives real managed-wiki publication."""

from pathlib import Path
from unittest.mock import patch
import sys
import json
import pytest

from llm_wiki_cli import api, cli
from llm_wiki_cli.services.maintenance_service import adopt_maintenance_authority
from llm_wiki_cli.services.maintenance_protocol import guard_maintenance_owner
from llm_wiki_cli.services.sync_manifest import SyncManifest
from tests.developer_value.fixtures import POLICY_SOURCE

from llm_wiki_cli.services.knowledge_artifacts import CommitStage
from llm_wiki_cli.services.maintenance_protocol import (
    ADOPTION_FILENAME, MaintenanceProtocolError, snapshot_wiki,
    maintenance_write_operation,
)
from llm_wiki_cli.services.maintenance_service import (
    recover_maintenance_authority, load_recovery_snapshot,
)
from llm_wiki_cli.services.knowledge_loader import load_knowledge_state
from llm_wiki_cli.services.knowledge_model import KnowledgeLoadState


def test_adopt_edit_sync_restart_retains_pending(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    Path("src").mkdir()
    source = Path("src/policy.py")
    source.write_text(POLICY_SOURCE)
    api.bootstrap_wiki("src", "wiki")
    capsys.readouterr()
    result = adopt_maintenance_authority("src", "wiki", recovery_dir="recovery")
    assert result["records"] >= 2
    owner = SyncManifest.load(Path("wiki"))
    assert owner.to_payload()["version"] == 7
    assert owner.maintenance_state is not None
    ids = set(owner.maintenance_state["records"])
    assert all(row["status"] == "pending" for row in owner.maintenance_state["records"].values())
    source.write_text(POLICY_SOURCE.replace("values[:limit]", "values[:limit - 1]"))
    with patch.object(sys, "argv", ["llm-wiki", "sync", "--src-dir", "src", "--wiki-dir", "wiki", "--no-plugins"]):
        cli.main()
    after = SyncManifest.load(Path("wiki"))
    assert after.maintenance_state is not None
    assert set(after.maintenance_state["records"]) == ids
    assert any("executable-syntax-changed" in row["reasons"] for row in after.maintenance_state["records"].values())
    guard_maintenance_owner("wiki")
    before = after.maintenance_state
    with patch.object(sys, "argv", ["llm-wiki", "sync", "--src-dir", "src", "--wiki-dir", "wiki", "--no-plugins"]):
        cli.main()
    assert SyncManifest.load(Path("wiki")).maintenance_state == before


def _legacy(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    Path("src").mkdir()
    Path("src/policy.py").write_text(POLICY_SOURCE)
    api.bootstrap_wiki("src", "wiki")
    return Path("wiki")


def _interrupt_adoption(stage):
    def interrupt(actual):
        if actual == stage:
            raise RuntimeError("interrupted publication")
    return interrupt



@pytest.mark.parametrize("stage", [CommitStage.MAINTENANCE_ADOPTION_WRITTEN,
                                   CommitStage.KNOWLEDGE_INDEX_WRITTEN,
                                   CommitStage.MANIFEST_WRITTEN])
def test_interrupted_adoption_restores_one_complete_identity(tmp_path, monkeypatch, stage):
    wiki = _legacy(tmp_path, monkeypatch)
    with pytest.raises(RuntimeError, match="interrupted"):
        adopt_maintenance_authority("src", wiki, recovery_dir="recovery",
                                    fault_injector=_interrupt_adoption(stage))
    marker = json.loads((wiki / ADOPTION_FILENAME).read_bytes())
    if stage != CommitStage.MANIFEST_WRITTEN:
        with pytest.raises(MaintenanceProtocolError):
            guard_maintenance_owner(wiki)
    result = recover_maintenance_authority(wiki, recovery_dir="recovery/prepared",
        expected_adoption_id=marker["adoption_id"], allow_prepared_adoption=True, src_dir="src")
    assert result["restored"]
    _, _, prepared = load_recovery_snapshot("recovery/prepared")
    assert SyncManifest.load(wiki).maintenance_state == prepared.maintenance_state
    assert guard_maintenance_owner(wiki) == marker
    assert load_knowledge_state(wiki).status == KnowledgeLoadState.VALID


@pytest.mark.parametrize("changed", ["source", "prose"])
def test_adoption_retry_refuses_post_failure_edits(tmp_path, monkeypatch, changed):
    wiki = _legacy(tmp_path, monkeypatch)
    with pytest.raises(RuntimeError):
        adopt_maintenance_authority("src", wiki, recovery_dir="recovery",
            fault_injector=_interrupt_adoption(CommitStage.MAINTENANCE_ADOPTION_WRITTEN))
    marker = json.loads((wiki / ADOPTION_FILENAME).read_bytes())
    path = Path("src/policy.py") if changed == "source" else next((wiki / "entities").glob("*.md"))
    path.write_bytes(path.read_bytes() + b"\n# newer authored input\n")
    before = snapshot_wiki(wiki)
    with pytest.raises(MaintenanceProtocolError) as error:
        recover_maintenance_authority(wiki, recovery_dir="recovery/prepared",
            expected_adoption_id=marker["adoption_id"], allow_prepared_adoption=True, src_dir="src")
    assert error.value.reason == ("source-changed" if changed == "source" else "recovery-conflict")
    assert snapshot_wiki(wiki) == before


def test_lost_marker_fails_full_read_and_complete_recovery_restores_it(tmp_path, monkeypatch):
    wiki = _legacy(tmp_path, monkeypatch)
    adopted = adopt_maintenance_authority("src", wiki, recovery_dir="recovery")
    expected = SyncManifest.load(wiki).maintenance_state
    (wiki / ADOPTION_FILENAME).unlink()
    rebuilt = []
    result = load_knowledge_state(wiki, policy="rebuild", rebuild_callback=rebuilt.append)
    assert result.status == KnowledgeLoadState.INVALID
    assert result.issues[0].code == "maintenance-adoption-missing"
    assert rebuilt == []
    recover_maintenance_authority(wiki, recovery_dir="recovery/prepared",
        expected_adoption_id=adopted["adoption_id"], allow_prepared_adoption=True, src_dir="src")
    assert SyncManifest.load(wiki).maintenance_state == expected


def test_manifest_publication_refuses_external_prose_before_commit(tmp_path, monkeypatch):
    wiki = _legacy(tmp_path, monkeypatch)
    adopt_maintenance_authority("src", wiki, recovery_dir="recovery")
    manifest_path = (wiki / ".llm-wiki-manifest.json").absolute()
    previous = manifest_path.read_bytes()
    from llm_wiki_cli.services.filesystem_guard import atomic_write_guarded_bytes

    with pytest.raises(MaintenanceProtocolError, match="outside"):
        with maintenance_write_operation(wiki):
            prose = next((wiki / "entities").glob("*.md"))
            prose.write_bytes(prose.read_bytes() + b"\nexternal prose\n")
            atomic_write_guarded_bytes(manifest_path, previous, expected_existing=previous)
    assert manifest_path.read_bytes() == previous


def test_recovery_refuses_newer_committed_owner(tmp_path, monkeypatch):
    wiki = _legacy(tmp_path, monkeypatch)
    adopted = adopt_maintenance_authority("src", wiki, recovery_dir="recovery")
    Path("src/policy.py").write_text(POLICY_SOURCE.replace("values[:limit]", "values[:limit - 1]"))
    with patch.object(sys, "argv", ["llm-wiki", "sync", "--src-dir", "src", "--wiki-dir", "wiki", "--no-plugins"]):
        cli.main()
    before = snapshot_wiki(wiki)
    with pytest.raises(MaintenanceProtocolError) as error:
        recover_maintenance_authority(wiki, recovery_dir="recovery/prepared",
            expected_adoption_id=adopted["adoption_id"], allow_prepared_adoption=True, src_dir="src")
    assert error.value.reason == "recovery-newer-owner"
    assert snapshot_wiki(wiki) == before


def test_adoption_preserves_crlf_and_complete_recovery_bytes(tmp_path, monkeypatch):
    wiki = _legacy(tmp_path, monkeypatch)
    page = next((wiki / "entities").glob("*.md"))
    exact = page.read_bytes().replace(b"\n", b"\r\n")
    page.write_bytes(exact)
    adopted = adopt_maintenance_authority("src", wiki, recovery_dir="recovery")
    assert page.read_bytes() == exact
    load_recovery_snapshot("recovery/prepared")
    (wiki / ".llm-wiki-manifest.json").unlink()
    recover_maintenance_authority(wiki, recovery_dir="recovery/prepared",
        expected_adoption_id=adopted["adoption_id"], allow_prepared_adoption=True, src_dir="src")
    assert page.read_bytes() == exact


def test_adopted_human_governance_review_retains_ordinary_pending(tmp_path, monkeypatch):
    wiki = _legacy(tmp_path, monkeypatch)
    adopt_maintenance_authority("src", wiki, recovery_dir="recovery")
    from tests.test_knowledge_cmd import _run
    from llm_wiki_cli.services.knowledge_governance import load_governance
    from llm_wiki_cli.services.contracts import SECTION_OWNERSHIP_EXTENSION_KEY

    ordinary = SyncManifest.load(wiki).maintenance_state
    _run(["init", "--wiki-dir", str(wiki), "--bundle-id", "kb_adopted_review"])
    knowledge = load_knowledge_state(wiki).knowledge
    assert knowledge is not None
    pages = knowledge.extensions[SECTION_OWNERSHIP_EXTENSION_KEY]["pages"]
    page = next(p for p in pages if p["page_locator"].startswith("llm-wiki://entities/"))
    section = next(s for s in page["sections"] if s.get("semantic_hash") is not None)
    ledger = load_governance(wiki).ledger
    uid = next(uid for uid, row in ledger.concepts.items() if row.locator == page["page_locator"])
    _run(["review", "--wiki-dir", str(wiki), "--uid", uid, "--section", section["locator"],
          "--reviewer-kind", "human", "--reviewer-id", "fixture-human", "--method", "manual-review",
          "--method-version", "1", "--authored-at", "2026-10-04T10:00:00Z"])
    assert len(load_governance(wiki).ledger.review_events) == 1
    assert SyncManifest.load(wiki).maintenance_state == ordinary
    assert load_knowledge_state(wiki).status == KnowledgeLoadState.VALID


@pytest.mark.parametrize("change", ["delete", "deselect"])
def test_adopted_source_removal_retains_all_record_history(tmp_path, monkeypatch, change):
    wiki = _legacy(tmp_path, monkeypatch)
    adopt_maintenance_authority("src", wiki, recovery_dir="recovery")
    old = SyncManifest.load(wiki).maintenance_state
    assert old is not None
    if change == "delete":
        Path("src/policy.py").unlink()
    else:
        Path("src/.gitignore").write_text("policy.py\n")
    with patch.object(sys, "argv", ["llm-wiki", "sync", "--src-dir", "src", "--wiki-dir", "wiki", "--no-plugins"]):
        cli.main()
    state = SyncManifest.load(wiki).maintenance_state
    assert state is not None
    assert set(state["records"]) == set(old["records"])
    assert all(row["status"] == "pending" for row in state["records"].values())
    if change == "delete":
        assert all(row["presence"] == "deleted" for row in state["observations"].values())
        assert all("source-deleted" in row["reasons"] for row in state["records"].values())
    else:
        assert all(row["presence"] != "deleted" for row in state["observations"].values())
    guard_maintenance_owner(wiki)


def test_governance_fault_retains_complete_recoverable_ordinary_authority(tmp_path, monkeypatch):
    wiki = _legacy(tmp_path, monkeypatch)
    adopted = adopt_maintenance_authority("src", wiki, recovery_dir="recovery")
    from tests.test_knowledge_cmd import _run
    from llm_wiki_cli.commands import knowledge_cmd
    from llm_wiki_cli.services.knowledge_artifacts import commit_knowledge_artifacts

    def interrupt(plan):
        return commit_knowledge_artifacts(plan,
            fault_injector=_interrupt_adoption(CommitStage.KNOWLEDGE_INDEX_WRITTEN))
    monkeypatch.setattr(knowledge_cmd, "commit_knowledge_artifacts", interrupt)
    with pytest.raises(RuntimeError):
        _run(["init", "--wiki-dir", str(wiki), "--bundle-id", "kb_interrupted_review"])
    assert SyncManifest.load(wiki).maintenance_state is not None
    recovery_roots = list((tmp_path / ".llm-wiki-maintenance-recovery/maintenance-preimages").glob("*"))
    assert len(recovery_roots) == 1
    restored = recover_maintenance_authority(wiki, recovery_dir=recovery_roots[0],
                                            expected_adoption_id=adopted["adoption_id"], allow_captured_preimage=True)
    assert restored["restored"]
    assert not (wiki / ".llm-wiki-governance.json").exists()
    assert load_knowledge_state(wiki).status == KnowledgeLoadState.VALID


@pytest.mark.parametrize("damage", ["missing", "tampered"])
def test_complete_recovery_rejects_rehashed_governance_damage(tmp_path, monkeypatch, damage):
    wiki = _legacy(tmp_path, monkeypatch)
    adopt_maintenance_authority("src", wiki, recovery_dir="recovery")
    from tests.test_knowledge_cmd import _run
    from llm_wiki_cli.services.maintenance_protocol import save_recovery_snapshot, load_adoption_marker
    from llm_wiki_cli.services.knowledge_storage import canonical_bytes, digest

    _run(["init", "--wiki-dir", str(wiki), "--bundle-id", "kb_recovery_authority"])
    files = snapshot_wiki(wiki)
    directory = tmp_path / "complete-recovery"
    save_recovery_snapshot(directory, files, marker=load_adoption_marker(wiki))
    metadata = json.loads((directory / "maintenance-recovery.json").read_bytes())
    name = ".llm-wiki-governance.json"
    if damage == "missing":
        metadata["files"].pop(name)
        (directory / name).unlink()
    else:
        content = (directory / name).read_bytes() + b"\n"
        (directory / name).write_bytes(content)
        metadata["files"][name] = {"hash": digest(content), "bytes": len(content)}
    (directory / "maintenance-recovery.json").write_bytes(canonical_bytes(metadata))
    with pytest.raises(MaintenanceProtocolError) as error:
        load_recovery_snapshot(directory)
    assert error.value.reason == "recovery-invalid"
    assert snapshot_wiki(wiki) == files


def test_dirty_prose_sync_fault_restores_exact_inputs_then_converges(tmp_path, monkeypatch):
    wiki = _legacy(tmp_path, monkeypatch)
    adopted = adopt_maintenance_authority("src", wiki, recovery_dir="recovery")
    from tests.test_knowledge_commands import _write_reviewed_description
    from llm_wiki_cli.services import knowledge_orchestration
    from llm_wiki_cli.services.knowledge_artifacts import commit_knowledge_artifacts

    page = wiki / "entities/Batch.md"
    _write_reviewed_description(page, "New authored prose retained through interrupted sync.")
    exact = page.read_bytes()
    old = SyncManifest.load(wiki).maintenance_state
    def interrupt(plan, **_options):
        return commit_knowledge_artifacts(plan,
            fault_injector=_interrupt_adoption(CommitStage.KNOWLEDGE_INDEX_WRITTEN))
    with monkeypatch.context() as fault:
        fault.setenv("LLM_WIKI_DEBUG", "1")
        fault.setattr(knowledge_orchestration, "commit_knowledge_artifacts", interrupt)
        with patch.object(sys, "argv", ["llm-wiki", "sync", "--src-dir", "src", "--wiki-dir", "wiki", "--no-plugins"]):
            with pytest.raises(RuntimeError):
                cli.main()
    recovery_roots = list((tmp_path / ".llm-wiki-maintenance-recovery/maintenance-preimages").glob("*"))
    assert len(recovery_roots) == 1
    with pytest.raises(MaintenanceProtocolError, match="explicit"):
        load_recovery_snapshot(recovery_roots[0])
    restored = recover_maintenance_authority(wiki, recovery_dir=recovery_roots[0],
        expected_adoption_id=adopted["adoption_id"], allow_captured_preimage=True)
    assert restored["requires_sync"] and not restored["prose_basis_validated"]
    assert page.read_bytes() == exact
    assert SyncManifest.load(wiki).maintenance_state == old
    with patch.object(sys, "argv", ["llm-wiki", "sync", "--src-dir", "src", "--wiki-dir", "wiki", "--no-plugins"]):
        cli.main()
    state = SyncManifest.load(wiki).maintenance_state
    assert state is not None and old is not None
    assert set(state["records"]) == set(old["records"])
    assert page.read_bytes() == exact
    assert any("prose-changed" in row["reasons"] for row in state["records"].values())
    assert load_knowledge_state(wiki).status == KnowledgeLoadState.VALID


def test_reserved_maintenance_projection_cannot_publish_with_legacy_owner(tmp_path, monkeypatch):
    wiki = _legacy(tmp_path, monkeypatch)
    legacy = SyncManifest.load(wiki)
    adopt_maintenance_authority("src", wiki, recovery_dir="recovery")
    view = load_knowledge_state(wiki)
    assert view.knowledge is not None and view.validated_artifacts is not None
    from llm_wiki_cli.services.knowledge_artifacts import (
        build_knowledge_commit_plan, validated_artifact_bytes, KnowledgeArtifactError,
    )
    from llm_wiki_cli.services.knowledge_reuse import REUSE_INPUT_KEY

    values = dict(legacy.generation_inputs)
    values.pop(REUSE_INPUT_KEY, None)
    legacy = legacy.with_generation_state(surfaces=legacy.surfaces, generation_inputs=values)
    surface, _ = validated_artifact_bytes(view.validated_artifacts)
    with pytest.raises(KnowledgeArtifactError, match="adopted manifest owner"):
        build_knowledge_commit_plan("other-wiki", surface_index_bytes=surface,
                                    knowledge_index=view.knowledge, manifest=legacy)
    assert not Path("other-wiki").exists()


@pytest.mark.parametrize("selector", ["concept:llm-wiki://entities/Batch", "extension:llm-wiki/maintenance-binding"])
def test_selected_read_rejects_rehashed_projection_without_authority(tmp_path, monkeypatch, selector):
    wiki = _legacy(tmp_path, monkeypatch)
    legacy = SyncManifest.load(wiki)
    adopt_maintenance_authority("src", wiki, recovery_dir="recovery")
    from llm_wiki_cli.services.knowledge_storage_lifecycle import migrate_knowledge_storage
    migrate_knowledge_storage(wiki, to="sharded-v2", recovery_dir="storage-recovery")
    from llm_wiki_cli.services.knowledge_storage import digest, KnowledgeStorageError
    from llm_wiki_cli.services.knowledge_storage_access import capture_knowledge_slice
    from llm_wiki_cli.services.knowledge_reuse import REUSE_INPUT_KEY
    from llm_wiki_cli.services.knowledge_artifacts import validated_artifact_bytes
    import shutil

    view = load_knowledge_state(wiki)
    assert view.validated_artifacts is not None
    surface, knowledge = validated_artifact_bytes(view.validated_artifacts)
    values = dict(legacy.generation_inputs)
    values.pop(REUSE_INPUT_KEY, None)
    owner = legacy.with_generation_state(surfaces=legacy.surfaces, generation_inputs=values).with_artifact_hashes(
        surface_index_hash=digest(surface), knowledge_index_hash=digest(knowledge),
        evaluated_envelope_hash=view.validated_artifacts.evaluated_envelope_hash)
    orphan = Path("unowned-wiki")
    shutil.copytree(wiki, orphan)
    (orphan / ADOPTION_FILENAME).unlink()
    (orphan / ".llm-wiki-manifest.json").write_text(json.dumps(owner.to_payload()))
    before = snapshot_wiki(orphan)
    rebuilt = []
    full = load_knowledge_state(orphan, policy="rebuild", rebuild_callback=rebuilt.append)
    assert full.status == KnowledgeLoadState.INVALID and full.knowledge is None
    assert rebuilt == []
    from llm_wiki_cli.services.knowledge_orchestration import capture_committed_knowledge
    from llm_wiki_cli.services.knowledge_artifacts import KnowledgeArtifactError
    with pytest.raises(KnowledgeArtifactError, match="adopted manifest owner"):
        capture_committed_knowledge(orphan, owner)
    with pytest.raises(KnowledgeStorageError, match="requires an adopted owner"):
        capture_knowledge_slice(orphan, [selector])
    assert snapshot_wiki(orphan) == before


@pytest.mark.parametrize("damage", ["root-future", "concept-malformed"])
def test_nested_maintenance_parse_errors_never_become_repair_seeds(tmp_path, monkeypatch, damage):
    wiki = _legacy(tmp_path, monkeypatch)
    legacy = SyncManifest.load(wiki)
    adopt_maintenance_authority("src", wiki, recovery_dir="recovery")
    from llm_wiki_cli.services.knowledge_storage import digest
    from llm_wiki_cli.services.knowledge_artifacts import formatted_json_bytes, KnowledgeArtifactError
    from llm_wiki_cli.services.knowledge_orchestration import capture_committed_knowledge
    from llm_wiki_cli.services.knowledge_reuse import REUSE_INPUT_KEY
    import shutil

    assert legacy.artifact_hashes is not None
    payload = json.loads((wiki / ".llm-wiki-knowledge.json").read_bytes())
    if damage == "root-future":
        payload["extensions"]["llm-wiki/maintenance-binding"]["schema_version"] = "llm-wiki-maintenance-binding/v2"
    else:
        payload["concepts"][0]["extensions"]["llm-wiki/maintenance-record"]["records"] = "invalid"
    raw = formatted_json_bytes(payload)
    values = dict(legacy.generation_inputs)
    values.pop(REUSE_INPUT_KEY, None)
    owner = legacy.with_generation_state(surfaces=legacy.surfaces, generation_inputs=values).with_artifact_hashes(
        surface_index_hash=digest((wiki / ".llm-wiki-surface.json").read_bytes()),
        knowledge_index_hash=digest(raw), evaluated_envelope_hash=legacy.artifact_hashes.evaluated_envelope_hash)
    orphan = Path("unowned-wiki")
    shutil.copytree(wiki, orphan)
    (orphan / ADOPTION_FILENAME).unlink()
    (orphan / ".llm-wiki-knowledge.json").write_bytes(raw)
    (orphan / ".llm-wiki-manifest.json").write_bytes(formatted_json_bytes(owner.to_payload()))
    before = snapshot_wiki(orphan)
    rebuilt = []
    view = load_knowledge_state(orphan, policy="rebuild", rebuild_callback=rebuilt.append)
    assert view.status == KnowledgeLoadState.INVALID and view.knowledge is None
    assert rebuilt == []
    with pytest.raises(KnowledgeArtifactError, match="maintenance"):
        capture_committed_knowledge(orphan, owner)
    assert snapshot_wiki(orphan) == before
