"""Guard lifetimes, recovery preimages and session ownership for bounded reads."""

import json
import os
from contextlib import contextmanager
from types import SimpleNamespace

import pytest

from llm_wiki_cli import api
from llm_wiki_cli.services import knowledge_storage_io as storage
from llm_wiki_cli.services import knowledge_governance as governance
from llm_wiki_cli.services.context_session import _memory_size
from llm_wiki_cli.services.knowledge_storage import KnowledgeStorageError, build_knowledge_store, digest
from llm_wiki_cli.services.knowledge_storage_lifecycle import (
    migrate_knowledge_storage, prune_knowledge_storage, restore_pruned_storage,
)
from tests.knowledge_fixtures import one_module_two_entities_fixture
from tests.test_knowledge_loader import _committed_state
from tests.test_knowledge_governance import _two_concept_ledger, HUMAN, FIXED_TIME


def test_batched_ranges_charge_exact_bytes_and_release_their_handles(tmp_path):
    path = tmp_path / 'pack'
    path.write_bytes(b'0123456789')
    session = storage.StorageReadSession(tmp_path, max_bytes=20, coalesce_rechecks=True)
    keys = [('pack', 0, 3, 10), ('pack', 3, 2, 10), ('pack', 8, 2, 10)]
    with session.phase():
        phase = session._phase
        assert session.read_ranges(keys) == [b'012', b'34', b'89']
        assert session.reads == 2 and session.bytes_read == 7
        streams = [item[0] for item in phase.files.values()]
    assert all(stream.closed for stream in streams)
    assert session._phase is None and not phase.files and not phase.directories
    session.recheck()
    assert session.reads == 4 and session.bytes_read == 14
    path.rename(tmp_path / 'released')


@pytest.mark.parametrize('mutation', ['contents', 'replacement', 'mode', 'parent'])
def test_final_phase_reopens_names_and_rejects_changed_inputs(tmp_path, mutation):
    folder = tmp_path / 'objects'
    folder.mkdir()
    path = folder / 'pack'
    path.write_bytes(b'012345')
    session = storage.StorageReadSession(tmp_path)
    with session.phase():
        session.read_range('objects/pack', 0, 3, 6)
    if mutation == 'contents':
        path.write_bytes(b'abc345')
    elif mutation == 'replacement':
        path.rename(folder / 'old')
        path.write_bytes(b'012345')
    elif mutation == 'mode':
        path.chmod(0o444)
    else:
        folder.rename(tmp_path / 'old-objects')
        folder.mkdir()
        path.write_bytes(b'012345')
    try:
        with pytest.raises(KnowledgeStorageError):
            session.recheck()
    finally:
        path.chmod(0o644)


def test_handle_budget_is_bounded_and_cancellation_closes_everything(tmp_path):
    paths = [tmp_path / f'file-{i}' for i in range(40)]
    for path in paths:
        path.write_bytes(b'content')
    cancelled = False
    session = storage.StorageReadSession(tmp_path, max_handles=32, cancelled=lambda: cancelled)
    with pytest.raises(KnowledgeStorageError, match='cancelled'):
        with session.phase():
            phase = session._phase
            for path in paths:
                session.read(path.name, 7)
                assert len(phase.files) + len(phase.directories) <= 32
            streams = [entry[0] for entry in phase.files.values()]
            cancelled = True
            session.read(paths[0].name, 7)
    assert all(stream.closed for stream in streams)
    assert not phase.files and not phase.directories


def test_phase_boundary_rejects_an_ancestor_move_or_native_guard_blocks_it(tmp_path):
    folder = tmp_path / 'objects'
    folder.mkdir()
    (folder / 'pack').write_bytes(b'012345')
    session = storage.StorageReadSession(tmp_path)
    if os.name == 'nt':
        with session.phase():
            session.read_range('objects/pack', 0, 3, 6)
            with pytest.raises(OSError):
                folder.rename(tmp_path / 'moved')
        folder.rename(tmp_path / 'released')
    else:
        with pytest.raises(KnowledgeStorageError, match='phase inputs|parent changed'):
            with session.phase():
                session.read_range('objects/pack', 0, 3, 6)
                folder.rename(tmp_path / 'moved')
    assert session._phase is None


def test_short_positional_reads_are_completed_without_overreading(tmp_path, monkeypatch):
    (tmp_path / 'pack').write_bytes(b'0123456789')
    amounts = []
    def partial(descriptor, length, offset):
        amount = min(length, 2)
        amounts.append(amount)
        os.lseek(descriptor, offset, os.SEEK_SET)
        return os.read(descriptor, amount)
    monkeypatch.setattr(storage.os, 'pread', partial, raising=False)
    with storage.StorageReadSession(tmp_path, max_bytes=7).phase() as session:
        assert session.read_range('pack', 1, 7, 10) == b'1234567'
        assert amounts == [2, 2, 2, 1] and session.bytes_read == 7


def test_windows_phase_model_keeps_metadata_channels_and_seek_fallback(tmp_path, monkeypatch):
    real_fstat = os.fstat
    class WindowsOs:
        name = 'nt'
        def __getattr__(self, key):
            if key == 'pread':
                raise AttributeError(key)
            return getattr(os, key)
        def fstat(self, descriptor):
            observed = real_fstat(descriptor)
            fields = {key: getattr(observed, key) for key in dir(observed) if key.startswith('st_')}
            fields['st_ctime_ns'] += 100
            return SimpleNamespace(**fields)
    backend = WindowsOs()
    @contextmanager
    def opened(path):
        with path.open('rb') as stream:
            yield stream, backend.fstat(stream.fileno())
    handles, closed = [], []
    def pin(path):
        handle = object()
        handles.append(handle)
        return handle
    monkeypatch.setattr(storage, 'os', backend)
    monkeypatch.setattr(storage, '_open_windows_directory_guard', pin)
    monkeypatch.setattr(storage, '_close_windows_handle', closed.append)
    monkeypatch.setattr(storage, 'open_windows_readonly_file', opened)
    (tmp_path / 'pack').write_bytes(b'abcdef')
    session = storage.StorageReadSession(tmp_path)
    with session.phase():
        assert session.read_range('pack', 1, 3, 6) == b'bcd'
        assert session.read_range('pack', 4, 2, 6) == b'ef'
    assert len(handles) == len(closed)
    session.recheck()
    assert len(handles) == len(closed)
    assert session.bytes_read == 10


@pytest.mark.parametrize('ranges', [[('pack', 0, 5, 6), ('pack', 4, 2, 6)],
                                  [('pack', 0, 3, 6), ('pack', 3, 2, 7)], [('pack', 0, 10, 6)]])
def test_invalid_batches_fail_before_opening_files(tmp_path, ranges):
    session = storage.StorageReadSession(tmp_path)
    with pytest.raises(KnowledgeStorageError):
        session.read_ranges(ranges)
    assert session.bytes_read == session.reads == 0


def orphan_fixture(tmp_path):
    root = tmp_path / 'wiki'
    root.mkdir()
    _committed_state(root)
    migrate_knowledge_storage(root, recovery_dir=tmp_path / 'migration')
    logical = json.loads(one_module_two_entities_fixture().knowledge_bytes)
    logical.setdefault('extensions', {})['consumer/old'] = 'recover this complete preimage'
    plan = build_knowledge_store(logical)
    name, raw = next((name, data) for name, data in plan.objects.items() if not (root / name).exists())
    (root / name).parent.mkdir(exist_ok=True)
    (root / name).write_bytes(raw)
    return root, name, raw


def test_prune_plan_is_read_only_and_recovery_is_verified_before_deletion(tmp_path):
    root, name, raw = orphan_fixture(tmp_path)
    recovery = tmp_path / 'prune-recovery'
    preview = prune_knowledge_storage(root, recovery_dir=recovery)
    assert not recovery.exists() and (root / name).read_bytes() == raw
    applied = prune_knowledge_storage(root, dry_run=False, plan=preview['plan'], recovery_dir=recovery)
    assert applied['removed'] == [name] and not (root / name).exists()
    record = applied['recovery_manifest']
    assert restore_pruned_storage(root, record)['preimages'] == 1
    restored = restore_pruned_storage(root, record, dry_run=False)
    assert restored['restored'] == [name] and (root / name).read_bytes() == raw
    before = {str(p): p.stat().st_mtime_ns for p in recovery.rglob('*') if p.is_file()}
    repeated = prune_knowledge_storage(root, dry_run=False, plan=preview['plan'], recovery_dir=recovery)
    assert repeated['recovery_manifest'] == record
    assert before == {str(p): p.stat().st_mtime_ns for p in recovery.rglob('*') if p.is_file()}


def test_stale_prune_plan_and_corrupt_recovery_never_authorize_deletion(tmp_path):
    root, name, raw = orphan_fixture(tmp_path)
    plan = prune_knowledge_storage(root)['plan']
    (root / name).write_bytes(b'concurrent bytes')
    with pytest.raises(KnowledgeStorageError, match='preimages changed'):
        prune_knowledge_storage(root, dry_run=False, plan=plan)
    assert (root / name).read_bytes() == b'concurrent bytes'
    (root / name).write_bytes(raw)
    recovery = tmp_path / 'recovery'
    key = digest(raw)[7:]
    wrong = recovery / 'objects' / key[:2] / (key + '.bin')
    wrong.parent.mkdir(parents=True)
    wrong.write_bytes(b'x' * len(raw))
    with pytest.raises(KnowledgeStorageError, match='preimage differs'):
        prune_knowledge_storage(root, dry_run=False, recovery_dir=recovery)
    assert (root / name).read_bytes() == raw


def test_prune_inspection_budget_retains_unread_objects(tmp_path):
    root, name, raw = orphan_fixture(tmp_path)
    result = prune_knowledge_storage(root, max_bytes=1)
    assert result['budget_exhausted'] and name in result['retained']
    assert result['inspection_bytes'] == 0 and (root / name).read_bytes() == raw


def test_bulk_lifecycle_validates_once_and_keeps_terminal_history(monkeypatch):
    ledger = _two_concept_ledger()
    uid = next(iter(ledger.concepts))
    ledger = governance.set_lifecycle(ledger, uid, 'active', actor=HUMAN, authored_at=FIXED_TIME)
    expected = {uid: governance.current_lifecycle(ledger, uid) for uid in ledger.concepts}
    calls = 0
    original = governance.validate_governance_ledger
    def counted(*args, **kwargs):
        nonlocal calls
        calls += 1
        return original(*args, **kwargs)
    monkeypatch.setattr(governance, 'validate_governance_ledger', counted)
    observed = governance.lifecycle_state_by_uid(ledger)
    assert calls == 1
    assert {uid: (row[0], row[2]) for uid, row in observed.items()} == expected


def test_scoped_entries_share_bytes_with_exact_retained_accounting(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    root = tmp_path / 'wiki'
    root.mkdir()
    _committed_state(root)
    migrate_knowledge_storage(root, to='packed-v4-deflate', recovery_dir=tmp_path / 'backup')
    session = api.open_context_session(wiki_dir=str(root))
    request = {'schema_version': 'llm-wiki-task-request/v2', 'options': {'read_scope': 'snapshot', 'knowledge_mode': 'required'},
               'requirements': [{'id': 'a', 'facet': 'concept', 'selector': 'entities/AccountService.md'}]}
    first = session.read(request)
    request['storage_options'] = {'receipt': 'compact-v1'}
    second = session.read(request)
    assert first.context and second.context and len(session._entries) == 2
    states = [entry.read.scoped_state for entry in session._entries.values()]
    shared = set(states[0].wiki_inputs) & set(states[1].wiki_inputs)
    assert shared
    assert all(states[0].wiki_inputs[path].content is states[1].wiki_inputs[path].content for path in shared)
    assert session._bytes == _memory_size(session._entries)
    assert session._bytes < sum(_memory_size(entry) for entry in session._entries.values())
    session.close()
    assert session._bytes == 0
