# save_recovery_snapshot

**Entry point:** `maintenance_protocol.save_recovery_snapshot`
**Modules involved:** [filesystem_guard](../modules/filesystem_guard.md), [knowledge_storage](../modules/knowledge_storage.md), [knowledge_storage_io](../modules/knowledge_storage_io.md), [maintenance_protocol](../modules/maintenance_protocol.md)

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `knowledge_storage_io._absolute_path`
2. `filesystem_guard.ensure_guarded_directory`
3. `knowledge_storage.digest`
4. `knowledge_storage.canonical_bytes`
5. `filesystem_guard.ensure_guarded_directory`
6. `knowledge_storage_io.read_guarded`
7. `filesystem_guard.atomic_write_guarded_bytes`

## Touches

- [filesystem_guard](../modules/filesystem_guard.md)
- [knowledge_storage](../modules/knowledge_storage.md)
- [knowledge_storage_io](../modules/knowledge_storage_io.md)
- [maintenance_protocol](../modules/maintenance_protocol.md)

## Behavior

This workflow starts at `maintenance_protocol.save_recovery_snapshot`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
