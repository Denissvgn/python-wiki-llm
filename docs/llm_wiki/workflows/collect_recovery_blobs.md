# collect_recovery_blobs

**Entry point:** `maintenance_recovery._collect_recovery_blobs`
**Modules involved:** [canonical_json](../modules/canonical_json.md), [filesystem_guard](../modules/filesystem_guard.md), [knowledge_storage_io](../modules/knowledge_storage_io.md), [maintenance_recovery](../modules/maintenance_recovery.md)

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `knowledge_storage_io._absolute_path`
2. `knowledge_storage_io._absolute_path`
3. `knowledge_storage_io.read_guarded`
4. `canonical_json.sha256_digest`
5. `knowledge_storage_io.read_guarded`
6. `canonical_json.sha256_digest`
7. `filesystem_guard.unlink_guarded_bytes`

## Touches

- [canonical_json](../modules/canonical_json.md)
- [filesystem_guard](../modules/filesystem_guard.md)
- [knowledge_storage_io](../modules/knowledge_storage_io.md)
- [maintenance_recovery](../modules/maintenance_recovery.md)

## Behavior

This workflow starts at `maintenance_recovery._collect_recovery_blobs`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
