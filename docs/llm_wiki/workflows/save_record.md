# save_record

**Entry point:** `bootstrap_recovery._save_record`
**Modules involved:** [bootstrap_recovery](../modules/bootstrap_recovery.md), [filesystem_guard](../modules/filesystem_guard.md), [knowledge_storage](../modules/knowledge_storage.md), [knowledge_storage_io](../modules/knowledge_storage_io.md)

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `knowledge_storage_io.read_guarded`
2. `filesystem_guard.atomic_write_guarded_bytes`
3. `knowledge_storage.canonical_bytes`

## Touches

- [bootstrap_recovery](../modules/bootstrap_recovery.md)
- [filesystem_guard](../modules/filesystem_guard.md)
- [knowledge_storage](../modules/knowledge_storage.md)
- [knowledge_storage_io](../modules/knowledge_storage_io.md)

## Behavior

This workflow starts at `bootstrap_recovery._save_record`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
