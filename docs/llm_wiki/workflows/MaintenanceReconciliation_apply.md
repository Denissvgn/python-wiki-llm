# MaintenanceReconciliation_apply

**Entry point:** `maintenance_state._MaintenanceReconciliation.apply`
**Modules involved:** [canonical_json](../modules/canonical_json.md), [knowledge_storage](../modules/knowledge_storage.md), [maintenance_shapes](../modules/maintenance_shapes.md), [maintenance_state](../modules/maintenance_state.md)

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `knowledge_storage.canonical_bytes`
2. `maintenance_shapes.require`
3. `maintenance_shapes.require`
4. `canonical_json.sha256_digest`

## Touches

- [canonical_json](../modules/canonical_json.md)
- [knowledge_storage](../modules/knowledge_storage.md)
- [maintenance_shapes](../modules/maintenance_shapes.md)
- [maintenance_state](../modules/maintenance_state.md)

## Behavior

This workflow starts at `maintenance_state._MaintenanceReconciliation.apply`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
