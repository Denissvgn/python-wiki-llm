# attach_maintenance_view_from_inputs

**Entry point:** `maintenance_status.attach_maintenance_view_from_inputs`
**Modules involved:** [maintenance_evidence](../modules/maintenance_evidence.md), [maintenance_status](../modules/maintenance_status.md), [python_implementation](../modules/python_implementation.md), [source_snapshot](../modules/source_snapshot.md)

> Join existing guarded query inputs without extracting source again.

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `source_snapshot.confirmed_missing_source_paths`
2. `python_implementation.analysis_identity`
3. `maintenance_evidence.captured_observations_from_knowledge`

## Touches

- [maintenance_evidence](../modules/maintenance_evidence.md)
- [maintenance_status](../modules/maintenance_status.md)
- [python_implementation](../modules/python_implementation.md)
- [source_snapshot](../modules/source_snapshot.md)

## Behavior

This workflow starts at `maintenance_status.attach_maintenance_view_from_inputs`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
