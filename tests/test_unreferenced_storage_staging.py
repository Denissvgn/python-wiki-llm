"""Only newly unreferenced hash-addressed bytes may defer source publication fences."""

from __future__ import annotations

from contextvars import copy_context
from dataclasses import replace
from pathlib import Path

import pytest

from llm_wiki_cli import api
from llm_wiki_cli.services import maintenance_protocol as protocol
from llm_wiki_cli.services.filesystem_guard import atomic_write_guarded_bytes, ensure_guarded_directory
from llm_wiki_cli.services.knowledge_orchestration import capture_committed_knowledge
from llm_wiki_cli.services.knowledge_packs import index_path, index_page_path, pack_path
from llm_wiki_cli.services.knowledge_storage import canonical_bytes, digest, object_path
from llm_wiki_cli.services.manifest_storage import object_path as manifest_object_path
from llm_wiki_cli.services.source_snapshot import build_source_snapshot
from llm_wiki_cli.services.sync_manifest import SyncManifest


@pytest.fixture
def adopted(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    source = tmp_path / "src"
    source.mkdir()
    (source / "app.py").write_text("def run():\n    return 1\n")
    api.bootstrap_wiki("src", "wiki", knowledge_format="packed-v4-deflate")
    api.adopt_maintenance("src", "wiki", recovery_dir="adoption")
    wiki = tmp_path / "wiki"
    state = capture_committed_knowledge(wiki, SyncManifest.load(wiki))
    assert state.artifacts is not None
    return wiki, source, build_source_snapshot(source), state


def _candidate(kind="object", *, value="new candidate"):
    raw = canonical_bytes({"candidate": value, "format": kind})
    commitment = digest(raw)
    names = {
        "object": object_path(commitment), "manifest": manifest_object_path(commitment),
        "index": index_path(commitment), "index-page": index_page_path(commitment),
        "pack": pack_path({"hash": commitment, "bucket": "0101"}),
    }
    return names[kind], raw


def _write(wiki, relative, raw, *, previous=None):
    path = wiki / relative
    ensure_guarded_directory(path.parent)
    atomic_write_guarded_bytes(path, raw, expected_existing=previous)


def test_new_unreferenced_storage_keeps_byte_cas_and_recovery_without_per_object_source_scan(adopted, monkeypatch):
    wiki, _source, snapshot, state = adopted
    with protocol.maintenance_write_operation(wiki) as basis:
        assert basis is not None
        basis.source_snapshot = snapshot
        basis.bind_committed_state(state)
        source_checks = []
        original = basis.assert_source_current

        def check():
            source_checks.append(True)
            original()

        monkeypatch.setattr(basis, "assert_source_current", check)
        for kind in ("object", "manifest", "index", "index-page", "pack"):
            relative, raw = _candidate(kind)
            _write(wiki, relative, raw)
            assert basis.expected[relative] == raw
            assert basis.eligible_images is not None
            assert basis.eligible_images[relative] == [None, digest(raw)]
        assert source_checks == []
        assert basis.recovery_started and basis.changed
    assert source_checks == [True]  # The operation's final source fence remains.


@pytest.mark.parametrize("fence", ["page", "surface", "knowledge", "manifest", "final"])
def test_source_mutation_during_blob_staging_is_rejected_at_publication_or_final_fence(adopted, fence):
    wiki, source, snapshot, state = adopted
    roots = {name: (wiki / name).read_bytes() for name in (
        ".llm-wiki-surface.json", ".llm-wiki-knowledge.json", ".llm-wiki-manifest.json",
    )}
    with pytest.raises(protocol.MaintenanceProtocolError, match="Source changed"):
        with protocol.maintenance_write_operation(wiki) as basis:
            assert basis is not None
            basis.source_snapshot = snapshot
            basis.bind_committed_state(state)
            (source / "app.py").write_text("def run():\n    return 2\n")
            relative, raw = _candidate()
            _write(wiki, relative, raw)
            assert (wiki / relative).read_bytes() == raw
            if fence != "final":
                name = {"page": "modules/app.md", "surface": ".llm-wiki-surface.json",
                        "knowledge": ".llm-wiki-knowledge.json", "manifest": ".llm-wiki-manifest.json"}[fence]
                previous = (wiki / name).read_bytes()
                _write(wiki, name, previous + b"\n", previous=previous)
    assert roots == {name: (wiki / name).read_bytes() for name in roots}


@pytest.mark.parametrize("change", ["unbound", "wrong-hash", "unknown-path", "different-source-snapshot", "different-roots"])
def test_unqualified_storage_writes_keep_the_original_source_fence(adopted, change):
    wiki, source, snapshot, state = adopted
    with pytest.raises(protocol.MaintenanceProtocolError, match="Source changed"):
        with protocol.maintenance_write_operation(wiki) as basis:
            assert basis is not None
            basis.source_snapshot = snapshot
            if change != "unbound":
                basis.bind_committed_state(state)
            relative, raw = _candidate()
            if change == "wrong-hash":
                raw += b"corrupt"
            elif change == "unknown-path":
                relative = ".llm-wiki-knowledge/unknown/" + Path(relative).name
            elif change == "different-source-snapshot":
                basis.source_snapshot = replace(snapshot)
            elif change == "different-roots":
                basis.expected[".llm-wiki-knowledge.json"] = b"changed private root basis"
            (source / "app.py").write_text("def run():\n    return 2\n")
            _write(wiki, relative, raw)
    assert not (wiki / relative).exists()


def test_a_prior_referenced_object_cannot_defer_even_if_its_file_is_absent(adopted):
    wiki, source, snapshot, state = adopted
    assert state.artifacts is not None
    relative = next(name for name in state.artifacts.storage_objects if name.startswith(".llm-wiki-knowledge/packs/"))
    raw = state.artifacts.storage_objects[relative]
    (wiki / relative).unlink()  # External deletion after the immutable prior was captured.
    with pytest.raises(protocol.MaintenanceProtocolError, match="Source changed"):
        with protocol.maintenance_write_operation(wiki) as basis:
            assert basis is not None and relative not in basis.preimages
            basis.source_snapshot = snapshot
            basis.bind_committed_state(state)
            (source / "app.py").write_text("def run():\n    return 2\n")
            _write(wiki, relative, raw)
    assert not (wiki / relative).exists()


def test_external_object_creation_cannot_bypass_per_file_byte_cas(adopted):
    wiki, _source, snapshot, state = adopted
    relative, raw = _candidate()
    with pytest.raises(protocol.MaintenanceProtocolError, match="Captured wiki input changed"):
        with protocol.maintenance_write_operation(wiki) as basis:
            assert basis is not None
            basis.source_snapshot = snapshot
            basis.bind_committed_state(state)
            path = wiki / relative
            ensure_guarded_directory(path.parent)
            path.write_bytes(b"external replacement")
            _write(wiki, relative, raw)
    assert (wiki / relative).read_bytes() == b"external replacement"


def test_publication_root_write_permanently_closes_staging(adopted, monkeypatch):
    wiki, _source, snapshot, state = adopted
    with protocol.maintenance_write_operation(wiki) as basis:
        assert basis is not None
        basis.source_snapshot = snapshot
        basis.bind_committed_state(state)
        root = wiki / ".llm-wiki-knowledge.json"
        # The before-write publication fence closes staging even if a later
        # callback aborts the attempted replacement before changing root bytes.
        basis.before_write(root, root.read_bytes() + b"\n")
        checks = []
        original = basis.assert_source_current

        def check():
            checks.append(True)
            original()

        monkeypatch.setattr(basis, "assert_source_current", check)
        relative, raw = _candidate()
        _write(wiki, relative, raw)
        assert checks == [True]


def test_copied_context_cannot_extend_staging_beyond_writer_lifetime(adopted):
    wiki, source, snapshot, state = adopted
    with protocol.maintenance_write_operation(wiki) as basis:
        assert basis is not None
        basis.source_snapshot = snapshot
        basis.bind_committed_state(state)
        copied = copy_context()
    (source / "app.py").write_text("def run():\n    return 2\n")
    relative, raw = _candidate()
    with pytest.raises(protocol.MaintenanceProtocolError, match="Source changed"):
        copied.run(_write, wiki, relative, raw)
    assert not (wiki / relative).exists()


@pytest.mark.parametrize("authority", ["replaced-state", "replaced-artifacts", "wrong-root"])
def test_binding_requires_the_same_root_issued_prior_and_original_roots(adopted, authority, tmp_path):
    wiki, _source, snapshot, state = adopted
    if authority == "replaced-state":
        invalid = replace(state)
    elif authority == "replaced-artifacts":
        assert state.artifacts is not None
        object.__setattr__(state, "artifacts", replace(state.artifacts))
        invalid = state
    else:
        object.__setattr__(state, "wiki_root", tmp_path / "different-wiki")
        invalid = state
    with protocol.maintenance_write_operation(wiki) as basis:
        assert basis is not None
        basis.source_snapshot = snapshot
        with pytest.raises(TypeError):
            basis.bind_committed_state(invalid)


def test_identical_existing_byte_write_keeps_unchanged_helper_behavior(adopted, monkeypatch):
    wiki, _source, snapshot, state = adopted
    assert state.artifacts is not None
    relative, raw = next(iter(state.artifacts.storage_objects.items()))
    with protocol.maintenance_write_operation(wiki) as basis:
        assert basis is not None
        basis.source_snapshot = snapshot
        basis.bind_committed_state(state)
        with monkeypatch.context() as guard:
            guard.setattr(basis, "assert_source_current", lambda: pytest.fail("identical helper write added a source scan"))
            _write(wiki, relative, raw, previous=raw)
        assert not basis.changed and not basis.recovery_started
