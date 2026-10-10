# capture_maintenance_observations

**Entry point:** `maintenance_service.capture_maintenance_observations`
**Modules involved:** [maintenance_evidence](../modules/maintenance_evidence.md), [maintenance_service](../modules/maintenance_service.md), [python_implementation](../modules/python_implementation.md), [source_snapshot](../modules/source_snapshot.md)

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `source_snapshot.confirmed_missing_source_paths`
2. `maintenance_evidence.captured_observations_from_knowledge`
3. `python_implementation.analysis_identity`

## Touches

- [maintenance_evidence](../modules/maintenance_evidence.md)
- [maintenance_service](../modules/maintenance_service.md)
- [python_implementation](../modules/python_implementation.md)
- [source_snapshot](../modules/source_snapshot.md)

## Behavior

This workflow starts at `maintenance_service.capture_maintenance_observations`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
