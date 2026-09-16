"""Sharded storage participates in the existing authoritative commit protocol."""

from dataclasses import replace
import json

import pytest

from llm_wiki_cli.services.knowledge_artifacts import (
    CommitStage, KnowledgeArtifactError, build_knowledge_commit_plan,
    commit_knowledge_artifacts, require_validated_artifacts,
)
from llm_wiki_cli.services.knowledge_loader import load_knowledge_state, KnowledgeStateLoadError
from llm_wiki_cli.services.knowledge_storage import STORE_SCHEMA
from llm_wiki_cli.services.knowledge_storage_access import capture_knowledge_slice
from llm_wiki_cli.services.sync_manifest import MANIFEST_FILENAME
from tests.test_knowledge_loader import _committed_state


def migrate_plan(tmp_path):
    fixture, old_plan, _ = _committed_state(tmp_path)
    plan = build_knowledge_commit_plan(tmp_path, surface_index_bytes=old_plan.surface_index.content,
        knowledge_index_bytes=old_plan.knowledge_index.content,
        manifest=old_plan.committed_manifest.without_artifact_hashes(), knowledge_format="sharded-v2")
    return fixture, old_plan, plan


def test_sharded_commit_loads_full_validated_native_model_and_preserves_adoption(tmp_path):
    _, old, plan = migrate_plan(tmp_path)
    previous = load_knowledge_state(tmp_path)
    stages = []
    result = commit_knowledge_artifacts(plan, fault_injector=stages.append)
    assert CommitStage.KNOWLEDGE_OBJECTS_WRITTEN in stages
    assert stages[-1] is CommitStage.MANIFEST_WRITTEN
    assert json.loads(result.knowledge_index.content)["schema_version"] == STORE_SCHEMA
    loaded = load_knowledge_state(tmp_path)
    assert loaded.knowledge == previous.knowledge
    assert loaded.validated_artifacts is not None
    assert loaded.validated_artifacts.storage_objects
    assert require_validated_artifacts(loaded.validated_artifacts) is loaded.validated_artifacts
    repeat = build_knowledge_commit_plan(tmp_path, surface_index_bytes=old.surface_index.content,
        knowledge_index_bytes=old.knowledge_index.content, manifest=old.committed_manifest.without_artifact_hashes())
    assert repeat.storage_format == "sharded-v2"
    assert not repeat.changed
    commit_knowledge_artifacts(repeat)
    assert load_knowledge_state(tmp_path).knowledge == previous.knowledge


def test_storage_dry_run_leaves_old_generation_and_no_objects(tmp_path):
    _, old, plan = migrate_plan(tmp_path)
    result = commit_knowledge_artifacts(plan, dry_run=True)
    assert result.changed
    assert not (tmp_path / ".llm-wiki-knowledge").exists()
    assert plan.knowledge_index.path.read_bytes() == old.knowledge_index.content


@pytest.mark.parametrize("stage", [CommitStage.KNOWLEDGE_OBJECTS_WRITTEN, CommitStage.KNOWLEDGE_INDEX_WRITTEN])
def test_interruption_does_not_publish_a_new_manifest(tmp_path, stage):
    _, old, plan = migrate_plan(tmp_path)
    before = (tmp_path / MANIFEST_FILENAME).read_bytes()
    def fail(observed):
        if observed == stage:
            raise RuntimeError("injected")
    with pytest.raises(RuntimeError, match="injected"):
        commit_knowledge_artifacts(plan, fault_injector=fail)
    assert (tmp_path / MANIFEST_FILENAME).read_bytes() == before
    if stage is CommitStage.KNOWLEDGE_OBJECTS_WRITTEN:
        assert plan.knowledge_index.path.read_bytes() == old.knowledge_index.content
        load_knowledge_state(tmp_path)
    else:
        with pytest.raises(KnowledgeStateLoadError):
            load_knowledge_state(tmp_path)


def test_commit_rejects_a_root_changed_after_planning(tmp_path):
    _, _, plan = migrate_plan(tmp_path)
    plan.knowledge_index.path.write_bytes(b"changed after planning\n")
    with pytest.raises(KnowledgeArtifactError, match="changed after planning"):
        commit_knowledge_artifacts(plan)
    assert plan.knowledge_index.path.read_bytes() == b"changed after planning\n"


def test_corrupt_existing_object_is_never_repaired_by_a_repeat_write(tmp_path):
    _, old, plan = migrate_plan(tmp_path)
    commit_knowledge_artifacts(plan)
    corrupted = plan.storage_objects[0].path
    corrupted.write_bytes(b"{}\n")
    with pytest.raises(KnowledgeArtifactError, match="immutable object is corrupt"):
        build_knowledge_commit_plan(tmp_path, surface_index_bytes=old.surface_index.content,
            knowledge_index_bytes=old.knowledge_index.content, manifest=old.committed_manifest.without_artifact_hashes())
    assert corrupted.read_bytes() == b"{}\n"
    with pytest.raises(KnowledgeStateLoadError):
        load_knowledge_state(tmp_path)


def test_replacing_object_map_invalidates_validator_authority(tmp_path):
    _, _, plan = migrate_plan(tmp_path)
    commit_knowledge_artifacts(plan)
    validated = load_knowledge_state(tmp_path).validated_artifacts
    assert validated is not None
    with pytest.raises(TypeError):
        require_validated_artifacts(replace(validated, storage_objects={}))


def test_old_future_format_is_not_overwritten(tmp_path):
    _, old, plan = migrate_plan(tmp_path)
    root = json.loads(plan.knowledge_index.content)
    root["schema_version"] = "llm-wiki-knowledge/v99"
    plan.knowledge_index.path.write_text(json.dumps(root))
    with pytest.raises(KnowledgeArtifactError, match="unknown storage format"):
        build_knowledge_commit_plan(tmp_path, surface_index_bytes=old.surface_index.content,
            knowledge_index_bytes=old.knowledge_index.content, manifest=old.committed_manifest.without_artifact_hashes())


def test_selected_filesystem_read_binds_manifest_pages_and_final_recheck(tmp_path):
    _, _, plan = migrate_plan(tmp_path)
    commit_knowledge_artifacts(plan)
    selected = capture_knowledge_slice(tmp_path, ["source:src/accounts.py"])
    payload = selected.slice.to_payload()
    assert payload["whole_store_validated"] is False
    assert "entities/AccountService.md" in selected.markdown
    before = selected.session.bytes_read
    work = selected.finish()
    assert work["bytes_read"] == 2 * before
    assert work["bytes_read"] < 8_388_608
    assert plan.surface_index.relative_path not in work["files"]


def test_selected_page_mutation_prevents_a_live_scoped_return(tmp_path):
    from llm_wiki_cli.services.knowledge_storage import KnowledgeStorageError
    _, _, plan = migrate_plan(tmp_path)
    commit_knowledge_artifacts(plan)
    selected = capture_knowledge_slice(tmp_path, ["source:src/accounts.py"])
    relative = next(iter(selected.markdown))
    (tmp_path / relative).write_text("changed\n")
    with pytest.raises(KnowledgeStorageError, match="changed"):
        selected.finish()
    with pytest.raises(KnowledgeStorageError, match="differs from its observation"):
        capture_knowledge_slice(tmp_path, ["source:src/accounts.py"])


def test_v2_generation_does_not_serialize_a_monolithic_v1_file(tmp_path, monkeypatch):
    from llm_wiki_cli.services import knowledge_artifacts
    _committed_state(tmp_path)
    loaded = load_knowledge_state(tmp_path)
    assert loaded.validated_artifacts is not None and loaded.manifest_basis is not None
    from llm_wiki_cli.services.knowledge_artifacts import validated_artifact_bytes
    def unexpected(*args, **kwargs):
        raise AssertionError("v2 generation allocated a v1 serialization")
    monkeypatch.setattr(knowledge_artifacts, "_validated_index_serialization", unexpected)
    plan = build_knowledge_commit_plan(tmp_path,
        surface_index_bytes=validated_artifact_bytes(loaded.validated_artifacts)[0],
        knowledge_index=loaded.knowledge, manifest=loaded.manifest_basis.without_artifact_hashes(),
        knowledge_format="sharded-v2")
    assert len(plan.knowledge_index.content) < 262_144
