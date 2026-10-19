# NewPageJournal_discard_committed

**Entry point:** `sync_recovery.NewPageJournal.discard_committed`
**Modules involved:** [filesystem_guard](../modules/filesystem_guard.md), [knowledge_storage](../modules/knowledge_storage.md), [knowledge_storage_io](../modules/knowledge_storage_io.md), [sync_recovery](../modules/sync_recovery.md)

> Remove only this successful operation's verified private scratch.

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `knowledge_storage.canonical_bytes`
2. `knowledge_storage_io.read_guarded`
3. `knowledge_storage.digest`
4. `knowledge_storage_io.read_guarded`
5. `filesystem_guard.unlink_guarded_bytes`

## Touches

- [filesystem_guard](../modules/filesystem_guard.md)
- [knowledge_storage](../modules/knowledge_storage.md)
- [knowledge_storage_io](../modules/knowledge_storage_io.md)
- [sync_recovery](../modules/sync_recovery.md)

## Behavior

Runs only after successful publication. Preflights the private directory's exact
entry set, journal bytes and postimage commitments, then guardedly removes known
postimages before the committed marker and empty directory. Unexpected entries,
changed bytes or directory replacement stop cleanup. The caller reports retained
scratch without changing a successful publication into a rejected transaction.
