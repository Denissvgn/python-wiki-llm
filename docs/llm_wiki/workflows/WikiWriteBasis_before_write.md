# WikiWriteBasis_before_write

**Entry point:** `maintenance_protocol.WikiWriteBasis.before_write`
**Modules involved:** [filesystem_guard](../modules/filesystem_guard.md), [knowledge_storage](../modules/knowledge_storage.md), [knowledge_storage_io](../modules/knowledge_storage_io.md), [maintenance_protocol](../modules/maintenance_protocol.md)

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `knowledge_storage_io.read_guarded`
2. `knowledge_storage_io._absolute_path`
3. `knowledge_storage.digest`
4. `knowledge_storage.digest`
5. `knowledge_storage_io.read_guarded`
6. `filesystem_guard.atomic_write_guarded_bytes`
7. `knowledge_storage.canonical_bytes`
8. `knowledge_storage.digest`
9. `knowledge_storage_io.read_guarded`

## Touches

- [filesystem_guard](../modules/filesystem_guard.md)
- [knowledge_storage](../modules/knowledge_storage.md)
- [knowledge_storage_io](../modules/knowledge_storage_io.md)
- [maintenance_protocol](../modules/maintenance_protocol.md)

## Behavior

This workflow starts at `maintenance_protocol.WikiWriteBasis.before_write`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
