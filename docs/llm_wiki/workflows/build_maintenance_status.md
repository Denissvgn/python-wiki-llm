# build_maintenance_status

**Entry point:** `maintenance_status.build_maintenance_status`
**Modules involved:** [implementation_evidence](../modules/implementation_evidence.md), [maintenance_evidence](../modules/maintenance_evidence.md), [maintenance_state](../modules/maintenance_state.md), [maintenance_status](../modules/maintenance_status.md)

> Project existing records only; no transition, allocation or storage writes.

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `maintenance_state.validate_maintenance_state`
2. `maintenance_state.validate_maintenance_adoption`
3. `maintenance_state.canonical_hash`
4. `maintenance_state.canonical_hash`
5. `maintenance_evidence.owner_key`
6. `maintenance_evidence.owner_key`
7. `implementation_evidence.compare_implementation_observations`

## Touches

- [implementation_evidence](../modules/implementation_evidence.md)
- [maintenance_evidence](../modules/maintenance_evidence.md)
- [maintenance_state](../modules/maintenance_state.md)
- [maintenance_status](../modules/maintenance_status.md)

## Behavior

This workflow starts at `maintenance_status.build_maintenance_status`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
