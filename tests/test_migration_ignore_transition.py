"""Owned migration controls advance without admitting concurrent source edits."""

import pytest

from llm_wiki_cli.commands import migrate_cmd
from llm_wiki_cli.services.source_snapshot import (
    SourceSnapshotMutationError, build_source_snapshot, source_snapshot_matches_current_files,
)


@pytest.fixture
def owner(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "module.py").write_text("VALUE = 1\n", encoding="utf-8")
    (tmp_path / "sub").mkdir()
    (tmp_path / "sub/.gitignore").write_text("# nested rules\n", encoding="utf-8")
    (tmp_path / "wiki").mkdir()
    (tmp_path / "wiki/sentinel.md").write_bytes(b"Authored prose\n")
    return tmp_path


@pytest.mark.parametrize("configured", [False, True])
def test_owned_ignore_write_preserves_source_and_advances_exact_controls(owner, configured):
    if configured:
        (owner / ".llm-wiki").mkdir()
        (owner / ".llm-wiki/source-selection.json").write_text(
            '{"schema_version":"llm-wiki-source-selection/v1","include":["module.py"],"exclude":[]}',
            encoding="utf-8",
        )
    original = build_source_snapshot(owner)
    plan = migrate_cmd.MigrationPlan("fixture", [], source_snapshot=original)
    assert migrate_cmd._ensure_legacy_gitignore(owner / "wiki", False, plan=plan)
    assert plan.source_snapshot is not None and plan.source_snapshot is not original
    assert source_snapshot_matches_current_files(plan.source_snapshot)
    assert plan.source_snapshot.captured_content_hashes["module.py"] == original.captured_content_hashes["module.py"]
    assert not migrate_cmd._ensure_legacy_gitignore(owner / "wiki", False, plan=plan)
    assert (owner / ".gitignore").read_bytes().count(b"wiki/legacy/") == 1
    assert (owner / "wiki/sentinel.md").read_bytes() == b"Authored prose\n"


@pytest.mark.parametrize("mutation", ["source-edit", "source-add", "other-ignore", "same-byte-replacement", "ignore-postimage"])
def test_owned_ignore_update_rejects_unowned_concurrent_changes(owner, monkeypatch, mutation):
    original = build_source_snapshot(owner)
    plan = migrate_cmd.MigrationPlan("fixture", [], source_snapshot=original)
    writer = migrate_cmd.atomic_write_guarded_bytes

    def write_then_change(path, data, **kwargs):
        result = writer(path, data, **kwargs)
        if mutation == "source-edit":
            (owner / "module.py").write_bytes(b"VALUE = 2\n")
        elif mutation == "source-add":
            (owner / "added.py").write_bytes(b"VALUE = 3\n")
        elif mutation == "other-ignore":
            (owner / "sub/.gitignore").write_bytes(b"# concurrent rules\n")
        elif mutation == "same-byte-replacement":
            replacement = owner / "replacement"
            replacement.write_bytes((owner / "module.py").read_bytes())
            replacement.replace(owner / "module.py")
        else:
            path.write_bytes(data + b"# concurrent rule\n")
        return result

    monkeypatch.setattr(migrate_cmd, "atomic_write_guarded_bytes", write_then_change)
    with pytest.raises(SourceSnapshotMutationError):
        migrate_cmd._ensure_legacy_gitignore(owner / "wiki", False, plan=plan)
    assert plan.source_snapshot is original
    assert (owner / "wiki/sentinel.md").read_bytes() == b"Authored prose\n"


def test_guarded_ignore_write_rejects_concurrent_preimage_edit(owner, monkeypatch):
    original = build_source_snapshot(owner)
    plan = migrate_cmd.MigrationPlan("fixture", [], source_snapshot=original)
    writer = migrate_cmd.atomic_write_guarded_bytes

    def change_then_write(path, data, **kwargs):
        path.write_bytes(b"# concurrent preimage\n")
        return writer(path, data, **kwargs)

    monkeypatch.setattr(migrate_cmd, "atomic_write_guarded_bytes", change_then_write)
    with pytest.raises(OSError):
        migrate_cmd._ensure_legacy_gitignore(owner / "wiki", False, plan=plan)
    assert (owner / ".gitignore").read_bytes() == b"# concurrent preimage\n"
    assert plan.source_snapshot is original


def test_outside_root_preview_write_keeps_original_source_commitment(owner, tmp_path_factory, monkeypatch):
    original = build_source_snapshot(owner)
    plan = migrate_cmd.MigrationPlan("fixture", [], source_snapshot=original)
    stage = tmp_path_factory.mktemp("migration-stage")
    monkeypatch.chdir(stage)
    assert migrate_cmd._ensure_legacy_gitignore(stage / "wiki", False, plan=plan)
    assert plan.source_snapshot is original
    assert not (owner / ".gitignore").exists()
    assert source_snapshot_matches_current_files(original)


@pytest.mark.parametrize("settings", [{"max_files": 8}, {"coherent": True}], ids=["bounded", "coherent"])
def test_unsupported_capture_transition_rejects_before_ignore_write(owner, settings):
    original = build_source_snapshot(owner, **settings)
    plan = migrate_cmd.MigrationPlan("fixture", [], source_snapshot=original)
    with pytest.raises(SourceSnapshotMutationError, match="bounded or coherent"):
        migrate_cmd._ensure_legacy_gitignore(owner / "wiki", False, plan=plan)
    assert not (owner / ".gitignore").exists()
    assert plan.source_snapshot is original
