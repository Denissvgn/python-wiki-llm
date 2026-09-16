"""Explicit storage lifecycle and local Git-history controls."""

import json
import subprocess
import sys

import pytest

from llm_wiki_cli.cli import main
from llm_wiki_cli.services.knowledge_loader import load_knowledge_state
from llm_wiki_cli.services.knowledge_storage import KnowledgeStorageError, build_knowledge_store, canonical_bytes, digest, object_path
from llm_wiki_cli.services.knowledge_storage_diagnostics import inspect_git_range, storage_report
from llm_wiki_cli.services.knowledge_storage_lifecycle import (
    migrate_knowledge_storage, recover_knowledge_storage, export_knowledge_v1, prune_knowledge_storage,
)
from tests.test_knowledge_loader import _committed_state


def snapshot(root):
    return {p.relative_to(root).as_posix(): p.read_bytes() for p in root.rglob("*") if p.is_file()}


def test_migration_preview_is_read_only_and_apply_preserves_authored_pages(tmp_path):
    root = tmp_path / "wiki"
    root.mkdir()
    _committed_state(root)
    before = snapshot(root)
    preview = migrate_knowledge_storage(root, dry_run=True, recovery_dir=tmp_path / "recovery")
    assert preview["changed"] and preview["to"] == "sharded-v2"
    assert snapshot(root) == before
    assert not (tmp_path / "recovery").exists()
    applied = migrate_knowledge_storage(root, recovery_dir=tmp_path / "recovery")
    assert applied["root_hash"] == preview["root_hash"]
    after = snapshot(root)
    assert {k: v for k, v in before.items() if k.endswith(".md")} == {k: v for k, v in after.items() if k.endswith(".md")}
    assert (tmp_path / "recovery" / ".llm-wiki-knowledge.json").read_bytes() == before[".llm-wiki-knowledge.json"]
    assert load_knowledge_state(root).knowledge is not None
    repeat = migrate_knowledge_storage(root)
    assert repeat["changed"] is False
    assert snapshot(root) == after


def test_non_git_apply_requires_explicit_safe_recovery_location(tmp_path):
    root = tmp_path / "wiki"
    root.mkdir()
    _committed_state(root)
    before = snapshot(root)
    with pytest.raises(KnowledgeStorageError, match="recovery-dir"):
        migrate_knowledge_storage(root)
    with pytest.raises(KnowledgeStorageError, match="outside"):
        migrate_knowledge_storage(root, recovery_dir=root / "backup")
    assert snapshot(root) == before


def test_recovery_restores_exact_original_artifacts_without_touching_authority(tmp_path):
    root = tmp_path / "wiki"
    root.mkdir()
    _committed_state(root)
    before = snapshot(root)
    migrate_knowledge_storage(root, recovery_dir=tmp_path / "recovery")
    preview = recover_knowledge_storage(root, tmp_path / "recovery", dry_run=True)
    assert preview["changed"]
    result = recover_knowledge_storage(root, tmp_path / "recovery")
    assert result["restored_format"] == "v1"
    for name, content in before.items():
        assert (root / name).read_bytes() == content
    assert load_knowledge_state(root).knowledge is not None
    migrate_knowledge_storage(root, recovery_dir=tmp_path / "recovery")
    assert storage_report(root, full=True)["integrity"] == "valid-committed-snapshot"


def test_recovery_refuses_changed_authority(tmp_path):
    root = tmp_path / "wiki"
    root.mkdir()
    _committed_state(root)
    migrate_knowledge_storage(root, recovery_dir=tmp_path / "recovery")
    page = root / "entities" / "AccountService.md"
    page.write_text("Human edit that must survive.\n")
    before = snapshot(root)
    with pytest.raises(KnowledgeStorageError, match="Markdown differs"):
        recover_knowledge_storage(root, tmp_path / "recovery")
    assert snapshot(root) == before


def test_complete_export_does_not_downgrade_the_active_store(tmp_path):
    root = tmp_path / "wiki"
    root.mkdir()
    _committed_state(root)
    original = (root / ".llm-wiki-knowledge.json").read_bytes()
    migrate_knowledge_storage(root, recovery_dir=tmp_path / "recovery")
    result = export_knowledge_v1(root, tmp_path / "legacy.json")
    assert result["format"] == "v1"
    assert (tmp_path / "legacy.json").read_bytes() == original
    assert storage_report(root)["format"] == "sharded-v2"
    with pytest.raises(KnowledgeStorageError, match="overwrite"):
        export_knowledge_v1(root, tmp_path / "legacy.json")


def test_cleanup_removes_only_safe_unreferenced_objects(tmp_path):
    root = tmp_path / "wiki"
    root.mkdir()
    _committed_state(root)
    migrate_knowledge_storage(root, recovery_dir=tmp_path / "recovery")
    from tests.knowledge_fixtures import one_module_two_entities_fixture
    logical = json.loads(one_module_two_entities_fixture().knowledge_bytes)
    logical.setdefault("extensions", {})["consumer/historical"] = "previous generation"
    candidate = build_knowledge_store(logical)
    relative, raw = next((name, data) for name, data in candidate.objects.items() if not (root / name).exists())
    path = root / relative
    path.parent.mkdir(exist_ok=True)
    path.write_bytes(raw)
    foreign = path.parent / "my-notes.txt"
    foreign.write_text("Keep this user file.\n")
    user_json = canonical_bytes({"user-owned": "not a provider object"})
    user_path = root / object_path(digest(user_json))
    user_path.parent.mkdir(exist_ok=True)
    user_path.write_bytes(user_json)
    preview = prune_knowledge_storage(root)
    assert preview["unreferenced_objects"] == [relative]
    assert path.exists()
    applied = prune_knowledge_storage(root, dry_run=False)
    assert applied["removed"] == [relative]
    assert foreign.read_text() == "Keep this user file.\n"
    assert user_path.read_bytes() == user_json
    assert load_knowledge_state(root).knowledge is not None


def test_pointer_only_lfs_checkout_is_reported_without_hydration(tmp_path):
    (tmp_path / ".llm-wiki-knowledge.json").write_text("version https://git-lfs.github.com/spec/v1\noid sha256:" + "0" * 64 + "\nsize 123\n")
    report = storage_report(tmp_path)
    assert report["format"] == "lfs-pointer"
    assert not report["ok"]
    assert {p.name for p in tmp_path.iterdir()} == {".llm-wiki-knowledge.json"}


def test_storage_cli_routes_preview_and_report(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    root = tmp_path / "wiki"
    root.mkdir()
    _committed_state(root)
    monkeypatch.setattr(sys, "argv", ["llm-wiki", "knowledge", "migrate", "--wiki-dir", "wiki", "--to", "sharded-v2", "--dry-run"])
    main()
    preview = json.loads(capsys.readouterr().out)
    assert preview["dry_run"]
    monkeypatch.setattr(sys, "argv", ["llm-wiki", "knowledge", "storage-check", "--wiki-dir", "wiki", "--full", "--format", "json"])
    main()
    assert json.loads(capsys.readouterr().out)["ok"]


def test_bootstrap_sync_and_governance_keep_the_selected_format(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "app.py").write_text("def limit(value=3):\n    return value\n\nclass Box:\n    pass\n")
    def command(*args):
        monkeypatch.setattr(sys, "argv", ["llm-wiki", *args])
        main()
        return capsys.readouterr()
    command("bootstrap", "--src-dir", ".", "--wiki-dir", "wiki", "--knowledge-format", "sharded-v2",
            "--skip-flows", "--skip-workflows", "--skip-dependencies")
    root = tmp_path / "wiki"
    assert storage_report(root, full=True)["format"] == "sharded-v2"
    command("knowledge", "init", "--wiki-dir", "wiki")
    loaded = load_knowledge_state(root)
    assert loaded.manifest_basis is not None and loaded.manifest_basis.artifact_hashes is not None
    assert loaded.manifest_basis.artifact_hashes.governance_hash is not None
    command("sync", "--src-dir", ".", "--wiki-dir", "wiki", "--jobs", "1", "--no-plugins", "--progress", "never")
    assert storage_report(root, full=True)["ok"]
    before = snapshot(root)
    command("sync", "--src-dir", ".", "--wiki-dir", "wiki", "--jobs", "1", "--no-plugins", "--progress", "never")
    assert snapshot(root) == before
    from llm_wiki_cli import api
    req = {"schema_version": "llm-wiki-task-request/v1", "requirements": [
        {"id": "contract", "facet": "source-contract", "selector": "app.py:limit"}]}
    result = api.build_task_context(req, wiki_dir="wiki")
    assert api.validate_task_context(result.rendered, req)["state"] == "covered"
    native_request = {"schema_version": "llm-wiki-task-request/v2",
        "options": {"read_scope": "snapshot", "knowledge_mode": "required"},
        "requirements": [{"id": "meaning", "facet": "semantic-section", "selector": "modules/app.md"},
                         {"id": "relations", "facet": "typed-relationships", "selector": "modules/app.md"}]}
    scoped = api.build_task_context(native_request, wiki_dir="wiki")
    validated = api.validate_task_context(scoped.rendered, native_request)
    assert all(item["satisfied"] for item in validated["coverage"]), validated["coverage"]
    assert all(fact["qualification"]["semantic_review"] == "not-evaluated" for fact in validated["facts"])
    from llm_wiki_cli.services.knowledge_governance import load_governance
    ledger = load_governance(root).ledger
    allocation = next(a for a in ledger.concepts.values() if a.locator == "llm-wiki://modules/app")
    command("knowledge", "alias", "--wiki-dir", "wiki", "--uid", allocation.uid,
            "--type", "locator", "--value", "llm-wiki://modules/old-app")
    for selector in (allocation.uid, allocation.natural_key, "llm-wiki://modules/old-app"):
        alias_request = {"schema_version": "llm-wiki-task-request/v2", "options": {"read_scope": "snapshot", "knowledge_mode": "required"},
            "requirements": [{"id": "identity", "facet": "concept", "selector": selector}]}
        answer = api.build_task_context(alias_request, wiki_dir="wiki")
        assert api.validate_task_context(answer.rendered, alias_request)["state"] == "covered", selector


def git(root, *args):
    return subprocess.check_output(["git", "-c", "user.name=Storage Fixture", "-c", "user.email=storage@example.invalid",
                                    "-C", str(root), *args], stderr=subprocess.STDOUT)


def test_explicit_git_range_finds_oversized_blob_deleted_at_head(tmp_path):
    git(tmp_path, "init", "-q")
    git(tmp_path, "commit", "-q", "--allow-empty", "-m", "base")
    base = git(tmp_path, "rev-parse", "HEAD").decode().strip()
    path = tmp_path / "large.json"
    with path.open("wb") as stream:
        for _ in range(101):
            stream.write(b"x" * 1_048_576)
    git(tmp_path, "add", "large.json")
    git(tmp_path, "commit", "-q", "-m", "oversized historical blob")
    git(tmp_path, "rm", "-q", "large.json")
    git(tmp_path, "commit", "-q", "-m", "latest tree is small")
    report = inspect_git_range(tmp_path, base=base, head="HEAD")
    assert report["complete"] and not report["ok"]
    assert report["failures"][0]["bytes"] == 101 * 1_048_576
    before = git(tmp_path, "rev-parse", "HEAD")
    assert not path.exists()
    assert git(tmp_path, "rev-parse", "HEAD") == before
    # Retain the rejected history and construct the intended small final state
    # on a separate, explicitly nontracking branch from the same base.
    git(tmp_path, "switch", "--no-track", "-c", "corrected", base)
    assert not git(tmp_path, "for-each-ref", "--format=%(upstream:short)", "refs/heads/corrected").strip()
    (tmp_path / "retained-change.txt").write_text("A legitimate source change survives.\n")
    git(tmp_path, "add", "retained-change.txt")
    git(tmp_path, "commit", "-q", "-m", "corrected small final state")
    assert inspect_git_range(tmp_path, base=base, head="HEAD")["ok"]
    assert not git(tmp_path, "for-each-ref", "--format=%(upstream:short)", "refs/heads").strip()


def test_git_check_never_guesses_refs_or_accepts_partial_repository(tmp_path):
    with pytest.raises(KnowledgeStorageError, match="explicit"):
        inspect_git_range(tmp_path, base="", head="HEAD")
    assert not inspect_git_range(tmp_path, base="main", head="HEAD")["complete"]
    git(tmp_path, "init", "-q")
    git(tmp_path, "commit", "-q", "--allow-empty", "-m", "base")
    git(tmp_path, "config", "remote.fixture.promisor", "true")
    report = inspect_git_range(tmp_path, base="HEAD", head="HEAD")
    assert not report["complete"] and not report["network_used"]
    assert "promisor" in report["error"]["message"]
