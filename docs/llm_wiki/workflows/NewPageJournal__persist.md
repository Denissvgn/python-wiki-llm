# NewPageJournal__persist

**Entry point:** `sync_recovery.NewPageJournal._persist`
**Modules involved:** [filesystem_guard](../modules/filesystem_guard.md), [knowledge_governance](../modules/knowledge_governance.md), [knowledge_storage](../modules/knowledge_storage.md), [knowledge_storage_io](../modules/knowledge_storage_io.md), [sync_recovery](../modules/sync_recovery.md)

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `knowledge_storage.canonical_bytes`
2. `knowledge_governance._governance_lock_root`
3. `filesystem_guard.ensure_guarded_directory`
4. `knowledge_storage_io.read_guarded`
5. `filesystem_guard.atomic_write_guarded_bytes`

## Touches

- [filesystem_guard](../modules/filesystem_guard.md)
- [knowledge_governance](../modules/knowledge_governance.md)
- [knowledge_storage](../modules/knowledge_storage.md)
- [knowledge_storage_io](../modules/knowledge_storage_io.md)
- [sync_recovery](../modules/sync_recovery.md)

## Behavior

Writes a bounded canonical journal through guarded compare-and-swap bytes in a
unique operation directory outside the wiki. A repository uses its governance
metadata root; a nonrepository wiki uses the canonical trusted OS temp root.
Journal persistence precedes a new page write, so unavailable recovery storage
refuses that write rather than allowing an unrecorded page.
