# save_recovery_catalog

**Entry point:** `maintenance_recovery._save_recovery_catalog`
**Modules involved:** [filesystem_guard](../modules/filesystem_guard.md), [knowledge_storage](../modules/knowledge_storage.md), [knowledge_storage_io](../modules/knowledge_storage_io.md), [maintenance_recovery](../modules/maintenance_recovery.md)

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `filesystem_guard.ensure_guarded_directory`
2. `knowledge_storage.digest`
3. `knowledge_storage.canonical_bytes`
4. `knowledge_storage_io.read_guarded`
5. `filesystem_guard.unlink_guarded_bytes`

## Touches

- [filesystem_guard](../modules/filesystem_guard.md)
- [knowledge_storage](../modules/knowledge_storage.md)
- [knowledge_storage_io](../modules/knowledge_storage_io.md)
- [maintenance_recovery](../modules/maintenance_recovery.md)

## Behavior

This workflow starts at `maintenance_recovery._save_recovery_catalog`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
