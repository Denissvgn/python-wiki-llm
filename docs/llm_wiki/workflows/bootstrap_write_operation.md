# bootstrap_write_operation

**Entry point:** `bootstrap_recovery.bootstrap_write_operation`
**Modules involved:** [bootstrap_recovery](../modules/bootstrap_recovery.md), [knowledge_storage](../modules/knowledge_storage.md), [knowledge_storage_io](../modules/knowledge_storage_io.md), [maintenance_protocol](../modules/maintenance_protocol.md)

> Lock before mutation and retain first-use preimages across interruption.

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `knowledge_storage_io._absolute_path`
2. `maintenance_protocol.governance_writer_lock`
3. `maintenance_protocol.storage_writer_lock`
4. `maintenance_protocol.guard_maintenance_owner`
5. `maintenance_protocol.snapshot_wiki`
6. `maintenance_protocol.save_recovery_snapshot`
7. `knowledge_storage.digest`
8. `knowledge_storage.canonical_bytes`
9. `maintenance_protocol.WikiWriteBasis`

## Touches

- [bootstrap_recovery](../modules/bootstrap_recovery.md)
- [knowledge_storage](../modules/knowledge_storage.md)
- [knowledge_storage_io](../modules/knowledge_storage_io.md)
- [maintenance_protocol](../modules/maintenance_protocol.md)

## Behavior

This workflow starts at `bootstrap_recovery.bootstrap_write_operation`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
