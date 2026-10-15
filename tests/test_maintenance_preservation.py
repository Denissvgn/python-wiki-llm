"""Adopted authority remains intact through storage and documentation copies."""

from __future__ import annotations

import json
from pathlib import Path
import sys
from unittest.mock import patch

import pytest

from llm_wiki_cli import api, cli
from llm_wiki_cli.services.documentation_native import (
    refresh_documentation_native_projection,
    DocumentationNativeError,
)
from llm_wiki_cli.services.knowledge_artifacts import CommitStage
from llm_wiki_cli.services.documentation_wiki_input import (
    adopt_documentation_wiki_snapshot,
    DocumentationWikiInputError,
)
from llm_wiki_cli.services.knowledge_loader import load_knowledge_state
from llm_wiki_cli.services.knowledge_storage import (
    KnowledgeStorageError,
    canonical_bytes,
    digest,
)
from llm_wiki_cli.services.knowledge_storage import build_knowledge_store
from llm_wiki_cli.services.knowledge_model import knowledge_index_to_payload
from llm_wiki_cli.services.knowledge_storage_access import capture_knowledge_slice
from llm_wiki_cli.services.knowledge_storage_lifecycle import (
    migrate_knowledge_storage,
    recover_knowledge_storage,
    export_knowledge_v1,
)
from llm_wiki_cli.services.maintenance_protocol import (
    ADOPTION_FILENAME,
    guard_maintenance_owner,
)
from llm_wiki_cli.services.maintenance_service import adopt_maintenance_authority
from llm_wiki_cli.services.manifest_storage import object_path
from llm_wiki_cli.services.sync_manifest import MANIFEST_FILENAME, SyncManifest
from tests.developer_value.fixtures import POLICY_SOURCE


def _project(tmp_path, monkeypatch, capsys, *, manifest_format=None, crlf=False):
    monkeypatch.chdir(tmp_path)
    Path("src").mkdir()
    Path("src/policy.py").write_bytes(POLICY_SOURCE.encode())
    api.bootstrap_wiki("src", "wiki", knowledge_format="v1")
    capsys.readouterr()
    if crlf:
        for page in Path("wiki").rglob("*.md"):
            page.write_bytes(page.read_bytes().replace(b"\n", b"\r\n"))
    adopt_maintenance_authority(
        "src", "wiki", recovery_dir="adoption-recovery", manifest_format=manifest_format
    )
    return Path("wiki")


def _bytes(root):
    return {
        p.relative_to(root).as_posix(): p.read_bytes()
        for p in root.rglob("*")
        if p.is_file() and not p.name.endswith(".lock")
    }


@pytest.mark.parametrize(
    "format",
    [
        "sharded-v2",
        "packed-v3",
        "packed-v3-deflate",
        "packed-v4",
        "packed-v4-deflate",
        "indexed-v8",
    ],
)
def test_migration_and_recovery_preserve_marker_owner_and_authored_preimages(
    tmp_path, monkeypatch, capsys, format
):
    wiki = _project(tmp_path, monkeypatch, capsys)
    old = SyncManifest.load(wiki)
    assert old.maintenance_state is not None
    authority = canonical_bytes(old.maintenance_state)
    marker = (wiki / ADOPTION_FILENAME).read_bytes()
    before = _bytes(wiki)
    result = migrate_knowledge_storage(
        wiki, to=format, recovery_dir=Path("storage-recovery")
    )
    assert result["changed"]
    assert canonical_bytes(SyncManifest.load(wiki).maintenance_state) == authority
    assert (wiki / ADOPTION_FILENAME).read_bytes() == marker
    guard_maintenance_owner(wiki)
    backup = json.loads(Path("storage-recovery/recovery.json").read_bytes())
    assert ADOPTION_FILENAME in backup["files"] and MANIFEST_FILENAME in backup["files"]
    assert all(name in backup["files"] for name in before if name.endswith(".md"))
    recover_knowledge_storage(wiki, Path("storage-recovery"))
    assert canonical_bytes(SyncManifest.load(wiki).maintenance_state) == authority
    assert all(
        (wiki / name).read_bytes() == content for name, content in before.items()
    )
    assert load_knowledge_state(wiki).knowledge is not None


def test_indexed_manifest_cli_preserves_adopted_owner_and_recovery(
    tmp_path, monkeypatch, capsys
):
    wiki = _project(tmp_path, monkeypatch, capsys)
    before = _bytes(wiki)
    authority = canonical_bytes(SyncManifest.load(wiki).maintenance_state)
    marker = (wiki / ADOPTION_FILENAME).read_bytes()
    arguments = [
        "llm-wiki", "knowledge", "migrate", "--wiki-dir", "wiki",
        "--to", "indexed-v8", "--recovery-dir", "storage-recovery",
    ]
    with patch.object(sys, "argv", [*arguments, "--dry-run"]):
        cli.main()
    preview = json.loads(capsys.readouterr().out)
    assert preview["to"] == "indexed-v8" and preview["dry_run"]
    assert preview["minimum_reader"] == "manifest/v8"
    assert _bytes(wiki) == before
    assert not Path("storage-recovery").exists()
    with patch.object(sys, "argv", arguments):
        cli.main()
    result = json.loads(capsys.readouterr().out)
    assert result["changed"] and result["to"] == "indexed-v8"
    assert json.loads((wiki / MANIFEST_FILENAME).read_bytes())["version"] == 8
    assert canonical_bytes(SyncManifest.load(wiki).maintenance_state) == authority
    assert (wiki / ADOPTION_FILENAME).read_bytes() == marker
    with patch.object(sys, "argv", [
        "llm-wiki", "knowledge", "recover-storage", "--wiki-dir", "wiki",
        "--recovery-dir", "storage-recovery",
    ]):
        cli.main()
    recovery = json.loads(capsys.readouterr().out)
    assert recovery["schema_version"] == "llm-wiki-storage-recovery/v1"
    assert recovery["changed"] and recovery["dry_run"] is False
    assert canonical_bytes(SyncManifest.load(wiki).maintenance_state) == authority
    assert all((wiki / name).read_bytes() == raw for name, raw in before.items())


def test_indexed_manifest_cli_requires_explicit_maintenance_adoption(
    tmp_path, monkeypatch, capsys
):
    monkeypatch.chdir(tmp_path)
    Path("src").mkdir()
    Path("src/policy.py").write_text(POLICY_SOURCE, encoding="utf-8")
    api.bootstrap_wiki("src", "wiki", knowledge_format="v1")
    capsys.readouterr()
    before = _bytes(Path("wiki"))
    with patch.object(sys, "argv", [
        "llm-wiki", "knowledge", "migrate", "--wiki-dir", "wiki",
        "--to", "indexed-v8", "--recovery-dir", "storage-recovery",
    ]), pytest.raises(SystemExit) as caught:
        cli.main()
    assert caught.value.code == 1
    failure = json.loads(capsys.readouterr().out)
    assert failure["ok"] is False
    assert "requires explicit maintenance adoption" in failure["error"]["message"]
    assert _bytes(Path("wiki")) == before
    assert not Path("storage-recovery").exists()


@pytest.mark.parametrize("operation", ["export", "downgrade"])
def test_lossy_operations_refuse_without_changing_authority(
    tmp_path, monkeypatch, capsys, operation
):
    wiki = _project(tmp_path, monkeypatch, capsys)
    before = _bytes(wiki)
    with pytest.raises(KnowledgeStorageError):
        if operation == "export":
            export_knowledge_v1(wiki, "export.json")
        else:
            migrate_knowledge_storage(
                wiki, to="indexed-v6", recovery_dir="downgrade-recovery"
            )
    assert not Path("export.json").exists()
    assert _bytes(wiki) == before


@pytest.mark.parametrize("manifest_format", ["v7", "indexed-v8"])
def test_documentation_import_copies_adopted_authority_and_all_catalogs(
    tmp_path, monkeypatch, capsys, manifest_format
):
    wiki = _project(tmp_path, monkeypatch, capsys, manifest_format=manifest_format)
    before = _bytes(wiki)
    adopted = adopt_documentation_wiki_snapshot(
        wiki, "workspace/wiki", source_root="src", freshness_policy="refresh-snapshot"
    )
    assert adopted.artifact_form in {"manifest_v7_native", "manifest_v8_native"}
    assert _bytes(Path("workspace/wiki")) == before
    assert (
        SyncManifest.load(Path("workspace/wiki")).maintenance_state
        == SyncManifest.load(wiki).maintenance_state
    )
    assert _bytes(wiki) == before


@pytest.mark.parametrize("manifest_format", ["v7", "indexed-v8"])
def test_selected_read_binds_marker_header_and_projection_without_global_claim(
    tmp_path, monkeypatch, capsys, manifest_format
):
    wiki = _project(tmp_path, monkeypatch, capsys, manifest_format=manifest_format)
    migrate_knowledge_storage(wiki, to="sharded-v2", recovery_dir="storage-recovery")
    before = _bytes(wiki)
    selected = capture_knowledge_slice(wiki, ["source:policy.py"])
    assert selected.maintenance_validation is not None
    assert selected.maintenance_validation["whole_state_validated"] is (
        manifest_format == "v7"
    )
    if manifest_format == "indexed-v8":
        root = json.loads((wiki / MANIFEST_FILENAME).read_bytes())
        ledger = object_path(root["catalogs"]["maintenance_state"]["hash"])
        assert ledger not in selected.session.observations
        assert (
            selected.maintenance_validation["ledger_record_membership"]
            == "not-validated"
        )
    selected.finish()
    assert _bytes(wiki) == before


def test_missing_marker_rejects_import_and_selected_read_before_mutation(
    tmp_path, monkeypatch, capsys
):
    wiki = _project(tmp_path, monkeypatch, capsys)
    migrate_knowledge_storage(wiki, to="sharded-v2", recovery_dir="storage-recovery")
    (wiki / ADOPTION_FILENAME).unlink()
    before = _bytes(wiki)
    with pytest.raises(KnowledgeStorageError):
        capture_knowledge_slice(wiki, ["source:policy.py"])
    with pytest.raises(DocumentationWikiInputError):
        adopt_documentation_wiki_snapshot(
            wiki, "workspace/wiki", freshness_policy="refresh-snapshot"
        )
    assert not Path("workspace/wiki").exists()
    assert _bytes(wiki) == before


def test_native_refresh_preserves_pending_owner_and_marker(
    tmp_path, monkeypatch, capsys
):
    wiki = _project(tmp_path, monkeypatch, capsys)
    before = SyncManifest.load(wiki).maintenance_state
    marker = (wiki / ADOPTION_FILENAME).read_bytes()
    refresh_documentation_native_projection(source_root="src", wiki_root=wiki)
    assert SyncManifest.load(wiki).maintenance_state == before
    assert (wiki / ADOPTION_FILENAME).read_bytes() == marker
    guard_maintenance_owner(wiki)


def test_selected_read_rejects_changed_marker_and_header_projection_binding(
    tmp_path, monkeypatch, capsys
):
    wiki = _project(tmp_path, monkeypatch, capsys, manifest_format="indexed-v8")
    migrate_knowledge_storage(wiki, to="sharded-v2", recovery_dir="storage-recovery")
    selected = capture_knowledge_slice(wiki, ["source:policy.py"])
    marker_path = wiki / ADOPTION_FILENAME
    original = marker_path.read_bytes()
    marker_path.write_bytes(original + b"\n")
    with pytest.raises(KnowledgeStorageError):
        selected.finish()
    marker_path.write_bytes(original)
    root = json.loads((wiki / MANIFEST_FILENAME).read_bytes())
    root["header"]["maintenance_state_hash"] = digest(b"another state")
    (wiki / MANIFEST_FILENAME).write_bytes(canonical_bytes(root))
    before = _bytes(wiki)
    with pytest.raises(KnowledgeStorageError, match="projection"):
        capture_knowledge_slice(wiki, ["source:policy.py"])
    assert _bytes(wiki) == before


def test_selected_unread_ledger_corruption_never_becomes_full_validation(
    tmp_path, monkeypatch, capsys
):
    wiki = _project(tmp_path, monkeypatch, capsys, manifest_format="indexed-v8")
    migrate_knowledge_storage(wiki, to="sharded-v2", recovery_dir="storage-recovery")
    root = json.loads((wiki / MANIFEST_FILENAME).read_bytes())
    ledger = object_path(root["catalogs"]["maintenance_state"]["hash"])
    (wiki / ledger).write_bytes(b"{}\n")
    selected = capture_knowledge_slice(wiki, ["source:policy.py"])
    assert selected.maintenance_validation is not None
    assert selected.maintenance_validation["whole_state_validated"] is False
    assert (
        selected.maintenance_validation["ledger_record_membership"] == "not-validated"
    )
    assert ledger not in selected.session.observations
    selected.finish()
    full = load_knowledge_state(wiki)
    assert full.knowledge is None


@pytest.mark.parametrize("newer_basis", ["authored-prose", "healthy-source-sync"])
def test_storage_recovery_refuses_post_migration_prose_or_newer_same_adoption_owner(
    tmp_path, monkeypatch, capsys, newer_basis
):
    wiki = _project(tmp_path, monkeypatch, capsys)
    migrate_knowledge_storage(wiki, to="sharded-v2", recovery_dir="storage-recovery")
    if newer_basis == "authored-prose":
        page = wiki / "entities/Batch.md"
        page.write_bytes(page.read_bytes() + b"\nLater authored note.\n")
    else:
        Path("src/policy.py").write_bytes(
            POLICY_SOURCE.replace("values[:limit]", "values[:limit - 1]").encode()
        )
        with patch.object(
            sys,
            "argv",
            [
                "llm-wiki",
                "sync",
                "--src-dir",
                "src",
                "--wiki-dir",
                "wiki",
                "--no-plugins",
            ],
        ):
            cli.main()
        capsys.readouterr()
        guard_maintenance_owner(wiki)
    before = _bytes(wiki)
    with pytest.raises(KnowledgeStorageError):
        recover_knowledge_storage(wiki, "storage-recovery")
    assert _bytes(wiki) == before


def test_crlf_raw_prose_survives_migration_recovery_and_selected_validation(
    tmp_path, monkeypatch, capsys
):
    wiki = _project(tmp_path, monkeypatch, capsys, crlf=True)
    before = _bytes(wiki)
    owner = SyncManifest.load(wiki).maintenance_state
    migrate_knowledge_storage(wiki, to="sharded-v2", recovery_dir="storage-recovery")
    selected = capture_knowledge_slice(wiki, ["source:policy.py"])
    selected.finish()
    recover_knowledge_storage(wiki, "storage-recovery")
    assert SyncManifest.load(wiki).maintenance_state == owner
    assert all((wiki / name).read_bytes() == raw for name, raw in before.items())
    assert b"\r\n" in (wiki / "entities/Batch.md").read_bytes()


def test_native_refresh_binds_captured_source_until_manifest_publication(
    tmp_path, monkeypatch, capsys
):
    wiki = _project(tmp_path, monkeypatch, capsys)
    original_manifest = (wiki / MANIFEST_FILENAME).read_bytes()
    source = Path("src/policy.py")
    source.write_bytes(
        POLICY_SOURCE.replace("values[:limit]", "values[:limit - 1]").encode()
    )
    reached = []

    def change_source(stage):
        if stage is CommitStage.KNOWLEDGE_INDEX_WRITTEN:
            reached.append(stage)
            source.write_bytes(
                POLICY_SOURCE.replace("values[:limit]", "values[:limit - 2]").encode()
            )

    with pytest.raises(DocumentationNativeError, match="[Ss]ource"):
        refresh_documentation_native_projection(
            source_root="src", wiki_root=wiki, fault_injector=change_source
        )
    assert reached
    assert (wiki / MANIFEST_FILENAME).read_bytes() == original_manifest


def test_selected_flat_owner_rejects_rehashed_projection_that_hides_pending_records(
    tmp_path, monkeypatch, capsys
):
    wiki = _project(tmp_path, monkeypatch, capsys, manifest_format="v7")
    migrate_knowledge_storage(wiki, to="sharded-v2", recovery_dir="storage-recovery")
    loaded = load_knowledge_state(wiki)
    assert loaded.knowledge is not None and loaded.manifest_basis is not None
    payload = knowledge_index_to_payload(loaded.knowledge)
    concept = next(
        c
        for c in payload["concepts"]
        if c["document"]["canonical_path"] == "entities/Batch.md"
    )
    records = concept["extensions"]["llm-wiki/maintenance-record"]
    assert records["bounds"]["observations_total"] > 0
    records["records"] = []
    records["bounds"] = {
        "observations_total": 0,
        "observations_returned": 0,
        "truncated": False,
    }
    # Forge all storage byte commitments; semantic authority validation must
    # still reject the hidden pending history without trusting mere hashes.
    store = build_knowledge_store(payload)
    for name, content in store.objects.items():
        path = wiki / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
    (wiki / ".llm-wiki-knowledge.json").write_bytes(store.root_bytes)
    old = loaded.manifest_basis.artifact_hashes
    assert old is not None
    forged = loaded.manifest_basis.with_artifact_hashes(
        surface_index_hash=old.surface_index_hash,
        knowledge_index_hash=digest(store.root_bytes),
        evaluated_envelope_hash=old.evaluated_envelope_hash,
        governance_hash=old.governance_hash,
    )
    (wiki / MANIFEST_FILENAME).write_text(forged.to_json())
    before = _bytes(wiki)
    with pytest.raises(KnowledgeStorageError, match="cardinality"):
        capture_knowledge_slice(wiki, ["page:entities/Batch.md"])
    assert _bytes(wiki) == before
