# guard_maintenance_owner

**Entry point:** `maintenance_protocol.guard_maintenance_owner`
**Modules involved:** [knowledge_storage](../modules/knowledge_storage.md), [knowledge_storage_io](../modules/knowledge_storage_io.md), [maintenance_protocol](../modules/maintenance_protocol.md), [maintenance_state](../modules/maintenance_state.md), [sync_manifest](../modules/sync_manifest.md)

> Never seed or repair an adopted wiki whose durable authority was lost.

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `knowledge_storage_io._absolute_path`
2. `sync_manifest.SyncManifest.load`
3. `maintenance_state.validate_maintenance_state`
4. `knowledge_storage.digest`
5. `knowledge_storage.canonical_bytes`
6. `maintenance_state.maintenance_state_hash`

## Touches

- [knowledge_storage](../modules/knowledge_storage.md)
- [knowledge_storage_io](../modules/knowledge_storage_io.md)
- [maintenance_protocol](../modules/maintenance_protocol.md)
- [maintenance_state](../modules/maintenance_state.md)
- [sync_manifest](../modules/sync_manifest.md)

## Behavior

This workflow starts at `maintenance_protocol.guard_maintenance_owner`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
