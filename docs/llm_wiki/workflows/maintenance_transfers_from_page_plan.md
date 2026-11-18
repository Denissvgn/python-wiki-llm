# maintenance_transfers_from_page_plan

**Entry point:** `maintenance_evidence.maintenance_transfers_from_page_plan`
**Modules involved:** [integrations](../modules/integrations.md), [maintenance_evidence](../modules/maintenance_evidence.md), [maintenance_shapes](../modules/maintenance_shapes.md), [maintenance_state](../modules/maintenance_state.md)

> Use verified page owners and captured semantic sections, never names/hashes.

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `integrations.attributes`
2. `maintenance_state.validate_maintenance_state`
3. `maintenance_shapes.MaintenanceError`
4. `maintenance_state.canonical_hash`
5. `maintenance_state.canonical_hash`
6. `maintenance_state.maintenance_core`
7. `maintenance_state.maintenance_core`

## Touches

- [integrations](../modules/integrations.md)
- [maintenance_evidence](../modules/maintenance_evidence.md)
- [maintenance_shapes](../modules/maintenance_shapes.md)
- [maintenance_state](../modules/maintenance_state.md)

## Behavior

This workflow starts at `maintenance_evidence.maintenance_transfers_from_page_plan`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
