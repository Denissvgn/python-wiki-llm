# project_maintenance_knowledge

**Entry point:** `maintenance_projection.project_maintenance_knowledge`
**Modules involved:** [knowledge_storage](../modules/knowledge_storage.md), [maintenance_projection](../modules/maintenance_projection.md), [maintenance_shapes](../modules/maintenance_shapes.md), [maintenance_state](../modules/maintenance_state.md)

> Derive root/concept projections; history remains exclusively in the owner.

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `maintenance_state.validate_maintenance_state`
2. `maintenance_state.validate_maintenance_adoption`
3. `maintenance_state.canonical_hash`
4. `maintenance_shapes.MaintenanceError`
5. `maintenance_state.canonical_hash`
6. `knowledge_storage.canonical_bytes`

## Touches

- [knowledge_storage](../modules/knowledge_storage.md)
- [maintenance_projection](../modules/maintenance_projection.md)
- [maintenance_shapes](../modules/maintenance_shapes.md)
- [maintenance_state](../modules/maintenance_state.md)

## Behavior

This workflow starts at `maintenance_projection.project_maintenance_knowledge`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
