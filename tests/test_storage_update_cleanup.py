"""Successful writers prune a verified plan. CI audits the retained generation."""

from pathlib import Path
import json
import subprocess

import pytest
import yaml

from llm_wiki_cli import cli
from llm_wiki_cli.commands import sync_cmd
from llm_wiki_cli.services import knowledge_storage_diagnostics as diagnostics
from llm_wiki_cli.services import knowledge_storage_lifecycle as lifecycle
from llm_wiki_cli.services.knowledge_storage import (
    KnowledgeStorageError,
    build_knowledge_store,
)
from tests.knowledge_fixtures import one_module_two_entities_fixture
from tests.test_knowledge_loader import _committed_state
from tests.test_knowledge_storage_lifecycle import snapshot


@pytest.fixture
def stored_wiki(tmp_path):
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    root = tmp_path / "wiki"
    root.mkdir()
    _committed_state(root)
    lifecycle.migrate_knowledge_storage(root, recovery_dir=tmp_path / "migration")
    logical = json.loads(one_module_two_entities_fixture().knowledge_bytes)
    logical.setdefault("extensions", {})["consumer/historical"] = "previous generation"
    previous = build_knowledge_store(logical)
    relative, raw = next(
        (name, raw)
        for name, raw in previous.objects.items()
        if not (root / name).exists()
    )
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(raw)
    return root, path


def test_strict_audit_rejects_orphans_without_mutating_the_wiki(stored_wiki):
    root, orphan = stored_wiki
    before = snapshot(root)
    assert diagnostics.storage_report(root, full=True)["ok"]
    report = diagnostics.storage_report(root, require_referenced=True)
    assert not report["ok"] and report["integrity"] == "valid-committed-snapshot"
    assert report["unreferenced_objects"] == [orphan.relative_to(root).as_posix()]
    assert "unreferenced-storage" in {item["reason"] for item in report["failures"]}
    assert snapshot(root) == before


def test_automatic_cleanup_preserves_current_files_and_verifies_recovery(
    stored_wiki, tmp_path
):
    root, orphan = stored_wiki
    before = snapshot(root)
    result = lifecycle.finalize_knowledge_storage(
        root, recovery_dir=tmp_path / "recovery"
    )
    assert result["removed"] == [orphan.relative_to(root).as_posix()]
    assert snapshot(root) == {
        name: raw for name, raw in before.items() if name not in result["removed"]
    }
    assert diagnostics.storage_report(root, require_referenced=True)["ok"]
    record = Path(result["recovery_manifest"])
    assert record.is_file()
    restore = lifecycle.restore_pruned_storage(root, record)
    assert restore["dry_run"] and not orphan.exists()
    assert lifecycle.finalize_knowledge_storage(
        root, recovery_dir=tmp_path / "recovery"
    ) == {
        "removed": [],
        "bytes": 0,
        "recovery_manifest": None,
    }


def test_unknown_objects_block_automatic_cleanup_before_deletion(stored_wiki, tmp_path):
    root, orphan = stored_wiki
    unknown = orphan.parent / "consumer-notes.txt"
    unknown.write_text("Keep this file.")
    before = snapshot(root)
    with pytest.raises(KnowledgeStorageError, match="retained objects"):
        lifecycle.finalize_knowledge_storage(root, recovery_dir=tmp_path / "recovery")
    assert snapshot(root) == before and not (tmp_path / "recovery").exists()
    assert not diagnostics.storage_report(root, require_referenced=True)["ok"]


def test_strict_audit_detects_new_namespace_entries(stored_wiki, monkeypatch):
    root, orphan = stored_wiki
    original = diagnostics.stored_object_paths
    calls = 0

    def observed(path):
        nonlocal calls
        calls += 1
        if calls == 3:
            (orphan.parent / "new.txt").write_text("concurrent addition")
        return original(path)

    monkeypatch.setattr(diagnostics, "stored_object_paths", observed)
    with pytest.raises(KnowledgeStorageError, match="namespace changed"):
        diagnostics.storage_report(root, require_referenced=True)


def test_failed_sync_never_invokes_automatic_cleanup(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    root = tmp_path / "wiki"
    root.mkdir()
    _committed_state(root)
    args = cli.build_cli_parser().parse_args(
        [
            "sync",
            "--src-dir",
            str(tmp_path),
            "--wiki-dir",
            str(root),
            "--prune-storage",
        ]
    )

    def failed_sync(*_):
        raise SystemExit(2)

    monkeypatch.setattr(sync_cmd, "_run_sync_options", failed_sync)
    calls = []
    monkeypatch.setattr(
        lifecycle,
        "finalize_knowledge_storage",
        lambda *_args, **_kwargs: calls.append(True),
    )
    with pytest.raises(SystemExit) as error:
        sync_cmd.run(args)
    assert error.value.code == 2 and not calls


def test_strict_audit_fences_the_generation_roots(stored_wiki, monkeypatch):
    root, _orphan = stored_wiki
    original = diagnostics._storage_report
    marker = root / ".llm-wiki-manifest.json"
    changed = marker.read_bytes() + b" "

    def report(*args, **kwargs):
        result = original(*args, **kwargs)
        marker.write_bytes(changed)
        return result

    monkeypatch.setattr(diagnostics, "_storage_report", report)
    with pytest.raises(KnowledgeStorageError, match="changed"):
        diagnostics.storage_report(root, require_referenced=True)
    assert marker.read_bytes() == changed


def test_strict_audit_keeps_budget_exhaustion_incomplete(stored_wiki, monkeypatch):
    root, _orphan = stored_wiki
    before = snapshot(root)
    monkeypatch.setattr(diagnostics, "MAX_EXPANDED_BYTES", 1)
    report = diagnostics.storage_report(root, require_referenced=True)
    assert not report["ok"] and report["error"]["code"] == "storage-limit"
    assert report["unreferenced_objects"] is None
    assert snapshot(root) == before


def test_namespace_enumeration_order_does_not_change_the_audit(
    stored_wiki, monkeypatch
):
    root, _orphan = stored_wiki
    original = diagnostics.stored_object_paths
    calls = 0

    def observed(path):
        nonlocal calls
        calls += 1
        owned, unknown = original(path)
        return (list(reversed(owned)), unknown) if calls == 3 else (owned, unknown)

    monkeypatch.setattr(diagnostics, "stored_object_paths", observed)
    report = diagnostics.storage_report(root, require_referenced=True)
    assert not report["ok"] and report["unreferenced_objects"]


def test_cleanup_opt_in_runs_after_success_but_stays_read_only_in_preview(
    stored_wiki, tmp_path, monkeypatch
):
    monkeypatch.chdir(tmp_path)
    root, orphan = stored_wiki
    monkeypatch.setattr(sync_cmd, "_run_sync_options", lambda *_: None)
    argv = [
        "sync",
        "--src-dir",
        str(tmp_path),
        "--wiki-dir",
        str(root),
        "--prune-storage",
        "--storage-recovery-dir",
        str(tmp_path / "recovery"),
    ]
    before = snapshot(root)
    sync_cmd.run(cli.build_cli_parser().parse_args([*argv, "--dry-run"]))
    assert snapshot(root) == before and not (tmp_path / "recovery").exists()
    sync_cmd.run(cli.build_cli_parser().parse_args(argv))
    assert (
        not orphan.exists()
        and diagnostics.storage_report(root, require_referenced=True)["ok"]
    )


def test_legacy_flat_native_generation_has_a_verified_noop_cleanup(tmp_path):
    root = tmp_path / "wiki"
    root.mkdir()
    _committed_state(root)
    before = snapshot(root)
    result = lifecycle.finalize_knowledge_storage(
        root, recovery_dir=tmp_path / "recovery"
    )
    assert result == {"removed": [], "bytes": 0, "recovery_manifest": None}
    assert snapshot(root) == before and not (tmp_path / "recovery").exists()


def test_actual_sync_cli_finishes_with_fully_referenced_storage(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    source = tmp_path / "src"
    source.mkdir()
    app = source / "app.py"
    app.write_text("def limit(value=3):\n    return value\n")

    def command(argv):
        monkeypatch.setattr("sys.argv", ["llm-wiki", *argv])
        cli.main()

    command(
        [
            "bootstrap",
            "--src-dir",
            "src",
            "--wiki-dir",
            "wiki",
            "--knowledge-format",
            "packed-v4-deflate",
            "--skip-flows",
            "--skip-workflows",
            "--skip-dependencies",
        ]
    )
    app.write_text("def limit(value=4):\n    return value + 1\n")
    command(
        [
            "sync",
            "--src-dir",
            "src",
            "--wiki-dir",
            "wiki",
            "--prune-storage",
            "--storage-recovery-dir",
            "recovery",
            "--jobs",
            "1",
            "--no-plugins",
            "--progress",
            "never",
        ]
    )
    assert diagnostics.storage_report("wiki", require_referenced=True)["ok"]
    assert list((tmp_path / "recovery").glob("*.json"))


def test_post_cleanup_audit_failure_reports_its_recovery(
    stored_wiki, tmp_path, monkeypatch
):
    root, orphan = stored_wiki
    original = diagnostics.storage_report
    calls = 0

    def report(*args, **kwargs):
        nonlocal calls
        calls += 1
        if calls == 2:
            raise KnowledgeStorageError(
                "storage", "concurrent root change", code="storage-mutation"
            )
        return original(*args, **kwargs)

    monkeypatch.setattr(diagnostics, "storage_report", report)
    with pytest.raises(KnowledgeStorageError, match="concurrent root change") as error:
        lifecycle.finalize_knowledge_storage(root, recovery_dir=tmp_path / "recovery")
    assert not orphan.exists()
    assert any("Recovery manifest" in note for note in error.value.__notes__)
    assert list((tmp_path / "recovery").glob("*.json"))


def test_exhausted_cleanup_preview_stops_before_apply(
    stored_wiki, tmp_path, monkeypatch
):
    root, _orphan = stored_wiki
    before = snapshot(root)
    calls = []

    def preview(*args, **kwargs):
        calls.append(kwargs)
        return {"budget_exhausted": True, "retained": []}

    monkeypatch.setattr(lifecycle, "prune_knowledge_storage", preview)
    with pytest.raises(KnowledgeStorageError, match="preview is incomplete"):
        lifecycle.finalize_knowledge_storage(root, recovery_dir=tmp_path / "recovery")
    assert calls == [{}] and snapshot(root) == before
    assert not (tmp_path / "recovery").exists()


def test_cli_guard_keeps_the_wiki_read_only_and_rejects_stream_mode(
    stored_wiki, monkeypatch, capsys
):
    root, _orphan = stored_wiki
    monkeypatch.chdir(root.parent)
    before = snapshot(root)
    argv = [
        "llm-wiki",
        "knowledge",
        "storage-check",
        "--wiki-dir",
        "wiki",
        "--require-referenced",
    ]
    for extra in ([], ["--stream"]):
        monkeypatch.setattr("sys.argv", [*argv, *extra])
        with pytest.raises(SystemExit) as error:
            cli.main()
        assert error.value.code == 1
        assert not json.loads(capsys.readouterr().out)["ok"]
        assert snapshot(root) == before


def test_integrity_action_uses_the_read_only_guard_and_root_opts_in():
    root = Path(__file__).parents[1]
    action = yaml.safe_load(
        (root / "integrations/wiki-integrity/action.yml").read_text()
    )
    assert action["inputs"]["require-referenced-storage"]["default"] == "false"
    step = next(
        s
        for s in action["runs"]["steps"]
        if s.get("name") == "Require fully referenced native storage"
    )
    assert "storage-check" in step["run"] and "--require-referenced" in step["run"]
    assert "--apply" not in step["run"] and "prune-storage" not in step["run"]
    workflow = yaml.safe_load((root / ".github/workflows/ci.yml").read_text())
    own = next(
        s
        for s in workflow["jobs"]["wiki-integrity"]["steps"]
        if s.get("uses") == "./integrations/wiki-integrity"
    )
    assert own["with"]["require-referenced-storage"] == "true"
