"""Explicit recovery distinguishes validated generated ownership from authored custody."""

from contextlib import redirect_stdout
import io
import json
from pathlib import Path

import pytest

from llm_wiki_cli import api, cli
from llm_wiki_cli.services.knowledge_loader import load_knowledge_state
from llm_wiki_cli.services.knowledge_storage import canonical_bytes, digest
from llm_wiki_cli.services.maintenance_protocol import ADOPTION_FILENAME, MaintenanceProtocolError, snapshot_wiki
from llm_wiki_cli.services.maintenance_service import load_recovery_snapshot, recover_maintenance_authority
from llm_wiki_cli.services.sync_manifest import SyncManifest, MANIFEST_FILENAME
from tests.test_owned_packet_recovery import FORMATS, owned_project

ROOTS = {".llm-wiki-knowledge.json", ".llm-wiki-surface.json"}
SCENARIOS = ("owner-only", "owner-and-knowledge", "surface", "referenced-closure")


def prepared(root, monkeypatch, mode="packed-v4-deflate", manifest="indexed-v8"):
    monkeypatch.chdir(root)
    with redirect_stdout(io.StringIO()):
        adopted = owned_project(root, mode, manifest)
    state = load_knowledge_state("wiki")
    assert state.validated_artifacts is not None
    referenced = set(state.validated_artifacts.storage_objects)
    return adopted, snapshot_wiki("wiki"), referenced


def remove_generated(wiki, scenario, referenced):
    names = {
        "owner-only": {MANIFEST_FILENAME},
        "owner-and-knowledge": {MANIFEST_FILENAME, ".llm-wiki-knowledge.json"},
        "surface": {".llm-wiki-surface.json"},
        "referenced-closure": {MANIFEST_FILENAME, *ROOTS, *referenced},
    }[scenario]
    for name in names:
        (wiki / name).unlink()
    return names


@pytest.mark.parametrize("mode", FORMATS)
@pytest.mark.parametrize("manifest", ["v7", "indexed-v8"])
@pytest.mark.parametrize("scenario", SCENARIOS)
def test_exact_committed_restoration_across_layouts(tmp_path, monkeypatch, mode, manifest, scenario):
    adopted, full, referenced = prepared(tmp_path, monkeypatch, mode, manifest)
    source = Path("src/app.py").read_bytes()
    deleted = remove_generated(Path("wiki"), scenario, referenced)
    damaged = snapshot_wiki("wiki")
    with pytest.raises(api.LlmWikiApiError):
        api.build_qualified_context("src", "wiki", request={"budget_tokens": 32000, "focus": ["all"], "knowledge_mode": "required"})
    assert snapshot_wiki("wiki") == damaged
    result = api.recover_maintenance("wiki", recovery_dir="recovery/committed", expected_adoption_id=adopted["adoption_id"])
    assert result["restored"] and not result["requires_sync"]
    assert snapshot_wiki("wiki") == full
    assert Path("src/app.py").read_bytes() == source
    for name in deleted:
        assert (Path("wiki") / name).read_bytes() == full[name]
    assert load_knowledge_state("wiki").knowledge is not None
    assert result["adoption_id"] == adopted["adoption_id"]


@pytest.mark.parametrize("damage", ["deleted-page", "edited-page", "deleted-asset", "unknown-current", "changed-root", "changed-object", "prefix-only", "no-anchor"])
def test_new_absence_rule_does_not_admit_unowned_or_changed_bytes(tmp_path, monkeypatch, damage):
    adopted, full, referenced = prepared(tmp_path, monkeypatch)
    wiki = Path("wiki")
    if damage == "deleted-page":
        (wiki / "entities/Item.md").unlink()
    elif damage == "edited-page":
        p = wiki / "entities/Item.md"
        p.write_bytes(p.read_bytes() + b"\nCaller edits\n")
    elif damage in {"deleted-asset", "prefix-only"}:
        # A complete validated backup may contain extra files. Neither its file
        # inventory nor a generated-looking prefix establishes referenced ownership.
        name = "assets/caller.bin" if damage == "deleted-asset" else ".llm-wiki-knowledge/objects/aa/" + "a" * 64 + ".json"
        backup = Path("recovery/committed")
        p = backup / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(b"caller-owned data")
        meta = json.loads((backup / "maintenance-recovery.json").read_bytes())
        meta["files"][name] = {"hash": digest(p.read_bytes()), "bytes": p.stat().st_size}
        (backup / "maintenance-recovery.json").write_bytes(canonical_bytes(meta))
        load_recovery_snapshot(backup)  # Valid backup inventory still grants no ownership.
    elif damage == "unknown-current":
        (wiki / "caller-extra.bin").write_bytes(b"unknown bytes")
    elif damage == "changed-root":
        (wiki / ".llm-wiki-knowledge.json").write_bytes(b"changed projection")
    elif damage == "changed-object":
        assert referenced
        (wiki / sorted(referenced)[0]).write_bytes(b"changed referenced bytes")
    else:
        for name in (ADOPTION_FILENAME, MANIFEST_FILENAME, ".llm-wiki-knowledge.json"):
            (wiki / name).unlink()
    if damage != "no-anchor":
        (wiki / MANIFEST_FILENAME).unlink(missing_ok=True)
    before = snapshot_wiki(wiki)
    with pytest.raises(MaintenanceProtocolError) as error:
        recover_maintenance_authority(wiki, recovery_dir=Path("recovery/committed"), expected_adoption_id=adopted["adoption_id"])
    assert error.value.reason == "recovery-conflict"
    assert snapshot_wiki(wiki) == before


def test_valid_current_owner_can_anchor_recovery_when_marker_is_missing(tmp_path, monkeypatch):
    adopted, full, _ = prepared(tmp_path, monkeypatch)
    Path("wiki", ADOPTION_FILENAME).unlink()
    Path("wiki/.llm-wiki-knowledge.json").unlink()
    recover_maintenance_authority(Path("wiki"), recovery_dir=Path("recovery/committed"), expected_adoption_id=adopted["adoption_id"])
    assert snapshot_wiki("wiki") == full


@pytest.mark.parametrize("fault", ["backup-corrupt", "backup-incomplete", "wrong-id", "unrelated", "newer-owner", "prepared", "captured"])
def test_identity_preimage_and_newer_owner_guards_precede_restoration(tmp_path, monkeypatch, fault):
    adopted, full, referenced = prepared(tmp_path, monkeypatch)
    recovery = Path("recovery/committed")
    expected_id = adopted["adoption_id"]
    if fault == "backup-corrupt":
        (recovery / ".llm-wiki-surface.json").write_bytes(b"wrong")
    elif fault == "backup-incomplete":
        (recovery / sorted(referenced)[0]).unlink()
    elif fault == "wrong-id":
        expected_id = "00000000-0000-4000-8000-000000000000"
    elif fault == "unrelated":
        other = tmp_path / "other-project"
        other.mkdir()
        with monkeypatch.context() as isolated:
            prepared(other, isolated)
        recovery = other / "recovery/committed"
    elif fault == "newer-owner":
        from llm_wiki_cli.commands import sync_cmd
        p = Path("src/app.py")
        p.write_bytes(p.read_bytes() + b"\ndef newer(): return 2\n")
        with redirect_stdout(io.StringIO()):
            sync_cmd.run(cli._build_parser().parse_args(["sync", "--src-dir", "src", "--wiki-dir", "wiki", "--no-plugins"]))
    elif fault == "prepared":
        recovery = Path("recovery/prepared")
    else:
        meta = json.loads((recovery / "maintenance-recovery.json").read_bytes())
        meta["kind"] = "captured-preimage"
        (recovery / "maintenance-recovery.json").write_bytes(canonical_bytes(meta))
    Path("wiki/.llm-wiki-knowledge.json").unlink()
    before = snapshot_wiki("wiki")
    with pytest.raises((ValueError, OSError)):
        recover_maintenance_authority(Path("wiki"), recovery_dir=recovery, expected_adoption_id=expected_id)
    assert snapshot_wiki("wiki") == before


def test_manifest_is_last_and_existing_source_is_not_rolled_back(tmp_path, monkeypatch):
    adopted, full, referenced = prepared(tmp_path, monkeypatch)
    remove_generated(Path("wiki"), "referenced-closure", referenced)
    source = Path("src/app.py")
    source.write_bytes(source.read_bytes() + b"\n# Later source stays intact\n")
    expected_source = source.read_bytes()
    from llm_wiki_cli.services import maintenance_service as owner
    write = owner.atomic_write_guarded_bytes
    observed = []
    def record(path, content, **options):
        observed.append(path.relative_to(Path("wiki").absolute()).as_posix())
        return write(path, content, **options)
    monkeypatch.setattr(owner, "atomic_write_guarded_bytes", record)
    owner.recover_maintenance_authority(Path("wiki"), recovery_dir=Path("recovery/committed"), expected_adoption_id=adopted["adoption_id"])
    assert observed[-1] == MANIFEST_FILENAME
    assert snapshot_wiki("wiki") == full and source.read_bytes() == expected_source
    assert SyncManifest.load(Path("wiki")).maintenance_state is not None


def test_link_substitution_is_rejected_before_restoration(tmp_path, monkeypatch):
    adopted, _, _ = prepared(tmp_path, monkeypatch)
    root = Path("wiki/.llm-wiki-knowledge.json")
    root.unlink()
    target = tmp_path / "external-content"
    target.write_bytes(b"caller content")
    try:
        root.symlink_to(target)
    except OSError:
        pytest.skip("Native symlink creation privilege is unavailable; not covered")
    with pytest.raises(ValueError):
        recover_maintenance_authority(Path("wiki"), recovery_dir=Path("recovery/committed"), expected_adoption_id=adopted["adoption_id"])
    assert root.is_symlink() and target.read_bytes() == b"caller content"


def test_concurrent_appearance_is_not_overwritten_or_committed(tmp_path, monkeypatch):
    adopted, _, _ = prepared(tmp_path, monkeypatch)
    Path("wiki/.llm-wiki-knowledge.json").unlink()
    Path("wiki", MANIFEST_FILENAME).unlink()
    from llm_wiki_cli.services import maintenance_service as owner
    write = owner.atomic_write_guarded_bytes
    def race(path, content, **options):
        if path.name == ".llm-wiki-knowledge.json":
            path.write_bytes(b"concurrent caller bytes")
        return write(path, content, **options)
    monkeypatch.setattr(owner, "atomic_write_guarded_bytes", race)
    with pytest.raises((ValueError, OSError)):
        owner.recover_maintenance_authority(Path("wiki"), recovery_dir=Path("recovery/committed"), expected_adoption_id=adopted["adoption_id"])
    assert Path("wiki/.llm-wiki-knowledge.json").read_bytes() == b"concurrent caller bytes"
    assert not Path("wiki", MANIFEST_FILENAME).exists()
