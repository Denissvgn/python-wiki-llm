# maintenance_write_operation

**Entry point:** `maintenance_protocol.maintenance_write_operation`
**Modules involved:** [knowledge_storage_io](../modules/knowledge_storage_io.md), [maintenance_protocol](../modules/maintenance_protocol.md), [maintenance_recovery](../modules/maintenance_recovery.md), [storage_spool](../modules/storage_spool.md)

> Hold locks from capture to publication; adopted writes retain preimages.

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `knowledge_storage_io._absolute_path`
2. `storage_spool.ByteSpool`
3. `knowledge_storage_io._absolute_path`
4. `maintenance_recovery.mark_recovery_complete`
5. `maintenance_recovery.retain_recovery_catalogs`

## Touches

- [knowledge_storage_io](../modules/knowledge_storage_io.md)
- [maintenance_protocol](../modules/maintenance_protocol.md)
- [maintenance_recovery](../modules/maintenance_recovery.md)
- [storage_spool](../modules/storage_spool.md)

## Behavior

This workflow starts at `maintenance_protocol.maintenance_write_operation`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
