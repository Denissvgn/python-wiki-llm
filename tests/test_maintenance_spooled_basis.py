"""Bounded exact preimages retain complete recovery and concurrent-edit guards."""

from pathlib import Path

import pytest

from llm_wiki_cli.services import maintenance_protocol as protocol
from llm_wiki_cli.services.filesystem_guard import atomic_write_guarded_bytes
from llm_wiki_cli.services.storage_spool import ByteSpool
from llm_wiki_cli.services.wiki_write_basis import ACTIVE_WRITE_BASIS


def test_spool_fork_retains_original_bytes_and_owner_lifetime():
    with ByteSpool() as original:
        original["page"] = b"before"
        updated = original.fork()
        updated["page"] = b"after"
        assert original["page"] == b"before" and updated["page"] == b"after"
        updated.close()
        assert original["page"] == b"before"


def test_spool_forks_share_the_physical_byte_quota():
    from llm_wiki_cli.services.knowledge_storage import KnowledgeStorageError
    with ByteSpool(max_bytes=8) as original:
        original["first"] = b"1234"
        fork = original.fork()
        fork["second"] = b"5678"
        with pytest.raises(KnowledgeStorageError, match="quota"):
            original["third"] = b"9"


def test_identical_writes_do_not_consume_more_spool_quota(tmp_path):
    page = tmp_path / "page.md"
    page.write_bytes(b"same")
    with ByteSpool(max_bytes=4) as original:
        original["page.md"] = b"same"
        basis = protocol.WikiWriteBasis(tmp_path, original.fork())
        token = ACTIVE_WRITE_BASIS.set(basis)
        try:
            for _ in range(3):
                atomic_write_guarded_bytes(page, b"same", expected_existing=b"same")
            basis.assert_current()
            assert not basis.changed
            assert basis.expected["page.md"] == basis.preimages["page.md"] == b"same"
            assert isinstance(basis.expected, ByteSpool)
            assert basis.expected.bytes_written == original.bytes_written == 4
        finally:
            ACTIVE_WRITE_BASIS.reset(token)


def test_identical_after_write_still_verifies_persisted_bytes(tmp_path):
    page = tmp_path / "page.md"
    page.write_bytes(b"same")
    with ByteSpool(max_bytes=4) as original:
        original["page.md"] = b"same"
        basis = protocol.WikiWriteBasis(tmp_path, original.fork())
        basis.before_write(page, b"same")
        page.write_bytes(b"away")
        with pytest.raises(protocol.MaintenanceProtocolError, match="Published wiki bytes changed"):
            basis.after_write(page, b"same")
        assert basis.expected["page.md"] == b"same"
        assert not basis.changed


def test_recovery_parent_resolves_linked_worktree_common_directory(tmp_path):
    common = tmp_path / "main" / ".git"
    metadata = common / "worktrees" / "linked"
    metadata.mkdir(parents=True)
    linked = tmp_path / "linked"
    wiki = linked / "docs" / "wiki"
    wiki.mkdir(parents=True)
    (linked / ".git").write_text(f"gitdir: {metadata}\n")
    (metadata / "commondir").write_text("../..\n")
    assert protocol._recovery_parent(wiki) == common


def _adopted(tmp_path, monkeypatch):
    from llm_wiki_cli import api
    from llm_wiki_cli.services.maintenance_service import adopt_maintenance_authority

    monkeypatch.chdir(tmp_path)
    Path("src").mkdir()
    Path("src/app.py").write_text("def run():\n    return 1\n")
    api.bootstrap_wiki("src", "wiki", knowledge_format="packed-v4-deflate")
    adopt_maintenance_authority("src", "wiki", recovery_dir="adoption")
    return tmp_path / "wiki"


def test_noop_uses_spooled_basis_and_never_persists_recovery(tmp_path, monkeypatch):
    wiki = _adopted(tmp_path, monkeypatch)
    def unexpected(*args, **kwargs):
        pytest.fail("no-op must not materialize or persist a complete byte tree")
    monkeypatch.setattr(protocol, "snapshot_wiki", unexpected)
    monkeypatch.setattr(protocol, "save_recovery_snapshot", unexpected)
    with protocol.maintenance_write_operation(wiki) as basis:
        assert basis is not None and isinstance(basis.expected, ByteSpool)
        assert not basis.recovery_started
        page = next(wiki.rglob("*.md"))
        raw = page.read_bytes()
        atomic_write_guarded_bytes(page, raw, expected_existing=raw)
        assert not basis.changed and not basis.recovery_started


def test_cache_writer_lock_is_transient_inside_adopted_wiki(tmp_path, monkeypatch):
    from llm_wiki_cli.services.knowledge_governance import governance_lock
    wiki = _adopted(tmp_path, monkeypatch)
    cache = wiki / "cache"
    cache.mkdir()
    with protocol.maintenance_write_operation(wiki):
        with governance_lock(cache, _lock_filename="llm-wiki-sync-analysis.lock"):
            assert (cache / "llm-wiki-sync-analysis.lock").is_file()


def test_identical_page_bytes_skip_source_rescan_but_changed_write_and_final_check_do_not(tmp_path, monkeypatch):
    wiki = _adopted(tmp_path, monkeypatch)
    page = next(wiki.rglob("*.md"))
    raw = page.read_bytes()
    with protocol.maintenance_write_operation(wiki) as basis:
        assert basis is not None
        calls = []
        monkeypatch.setattr(basis, "assert_source_current", lambda: calls.append(True))
        basis.before_write(page, raw)
        assert calls == []
        basis.before_write(page, raw + b"\n")
        assert len(calls) == 1
        basis.assert_current()
        assert len(calls) == 2
        basis.before_write(wiki / ".llm-wiki-manifest.json", (wiki / ".llm-wiki-manifest.json").read_bytes())
        assert len(calls) == 3


def test_source_change_during_identical_write_is_rejected_at_final_verification(tmp_path, monkeypatch):
    wiki = _adopted(tmp_path, monkeypatch)
    from llm_wiki_cli.services.source_snapshot import build_source_snapshot
    page = next(wiki.rglob("*.md"))
    raw = page.read_bytes()
    with pytest.raises(protocol.MaintenanceProtocolError, match="Source changed"):
        with protocol.maintenance_write_operation(wiki) as basis:
            assert basis is not None
            basis.source_snapshot = build_source_snapshot("src")
            Path("src/app.py").write_text("def run():\n    return 2\n")
            basis.before_write(page, raw)


def test_first_mutation_saves_complete_preimage_before_replacement(tmp_path, monkeypatch):
    wiki = _adopted(tmp_path, monkeypatch)
    page = next(wiki.rglob("*.md"))
    raw = page.read_bytes()
    original = protocol.save_recovery_snapshot
    observed = []
    def capture(directory, files, **kwargs):
        if kwargs.get("kind") == "captured-preimage":
            assert page.read_bytes() == raw
            assert files[page.relative_to(wiki).as_posix()] == raw
            assert ".llm-wiki-manifest.json" in files
            observed.append(directory)
        return original(directory, files, **kwargs)
    monkeypatch.setattr(protocol, "save_recovery_snapshot", capture)
    with protocol.maintenance_write_operation(wiki) as basis:
        atomic_write_guarded_bytes(page, raw + b"\n", expected_existing=raw)
        assert basis is not None and basis.changed and basis.recovery_started
        assert basis.preimages[page.relative_to(wiki).as_posix()] == raw
    assert len(observed) == 1


@pytest.mark.parametrize("change", ["same-size", "addition", "deletion"])
def test_streaming_verification_detects_external_namespace_changes(tmp_path, monkeypatch, change):
    wiki = _adopted(tmp_path, monkeypatch)
    page = next(wiki.rglob("*.md"))
    with pytest.raises(protocol.MaintenanceProtocolError, match="outside"):
        with protocol.maintenance_write_operation(wiki):
            if change == "addition":
                (wiki / "unexpected.txt").write_bytes(b"external")
            elif change == "deletion":
                page.unlink()
            else:
                raw = page.read_bytes()
                page.write_bytes(bytes([raw[0] ^ 1]) + raw[1:])
