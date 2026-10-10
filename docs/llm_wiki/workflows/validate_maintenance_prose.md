# validate_maintenance_prose

**Entry point:** `maintenance_projection.validate_maintenance_prose`
**Modules involved:** [maintenance_evidence](../modules/maintenance_evidence.md), [maintenance_projection](../modules/maintenance_projection.md), [maintenance_shapes](../modules/maintenance_shapes.md), [maintenance_state](../modules/maintenance_state.md)

> Validate supplied exact pages; unavailable prose makes no byte claim.

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `maintenance_state.validate_maintenance_state`
2. `maintenance_shapes.MaintenanceError`
3. `maintenance_evidence.captured_semantic_sections`
4. `maintenance_shapes.MaintenanceError`
5. `maintenance_shapes.MaintenanceError`
6. `maintenance_shapes.MaintenanceError`

## Touches

- [maintenance_evidence](../modules/maintenance_evidence.md)
- [maintenance_projection](../modules/maintenance_projection.md)
- [maintenance_shapes](../modules/maintenance_shapes.md)
- [maintenance_state](../modules/maintenance_state.md)

## Behavior

This workflow starts at `maintenance_projection.validate_maintenance_prose`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
