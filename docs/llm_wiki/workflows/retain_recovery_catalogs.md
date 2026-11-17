# retain_recovery_catalogs

**Entry point:** `maintenance_recovery._retain_recovery_catalogs`
**Modules involved:** [canonical_json](../modules/canonical_json.md), [filesystem_guard](../modules/filesystem_guard.md), [knowledge_storage_io](../modules/knowledge_storage_io.md), [maintenance_recovery](../modules/maintenance_recovery.md)

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `knowledge_storage_io._absolute_path`
2. `knowledge_storage_io._absolute_path`
3. `canonical_json.sha256_digest`
4. `knowledge_storage_io.read_guarded`
5. `filesystem_guard.unlink_guarded_bytes`
6. `filesystem_guard.unlink_guarded_bytes`
7. `filesystem_guard.unlink_guarded_bytes`
8. `filesystem_guard.fresh_no_follow_stat`
9. `filesystem_guard.remove_guarded_tree`

## Touches

- [canonical_json](../modules/canonical_json.md)
- [filesystem_guard](../modules/filesystem_guard.md)
- [knowledge_storage_io](../modules/knowledge_storage_io.md)
- [maintenance_recovery](../modules/maintenance_recovery.md)

## Behavior

This workflow starts at `maintenance_recovery._retain_recovery_catalogs`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
