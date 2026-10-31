# recover

**Entry point:** `bootstrap_recovery._recover`
**Modules involved:** [bootstrap_recovery](../modules/bootstrap_recovery.md), [filesystem_guard](../modules/filesystem_guard.md), [knowledge_storage](../modules/knowledge_storage.md), [maintenance_protocol](../modules/maintenance_protocol.md), [wiki_lifecycle](../modules/wiki_lifecycle.md)

> Validate the entire tree before restoring with exact-byte comparisons.

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `wiki_lifecycle.is_pristine_wiki_target`
2. `maintenance_protocol.snapshot_wiki`
3. `knowledge_storage.digest`
4. `maintenance_protocol.MaintenanceProtocolError`
5. `maintenance_protocol.MaintenanceProtocolError`
6. `filesystem_guard.unlink_guarded_bytes`
7. `filesystem_guard.ensure_guarded_directory`
8. `filesystem_guard.atomic_write_guarded_bytes`
9. `filesystem_guard.remove_guarded_tree`
10. `maintenance_protocol.snapshot_wiki`
11. `maintenance_protocol.MaintenanceProtocolError`

## Touches

- [bootstrap_recovery](../modules/bootstrap_recovery.md)
- [filesystem_guard](../modules/filesystem_guard.md)
- [knowledge_storage](../modules/knowledge_storage.md)
- [maintenance_protocol](../modules/maintenance_protocol.md)
- [wiki_lifecycle](../modules/wiki_lifecycle.md)

## Behavior

This workflow starts at `bootstrap_recovery._recover`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
