# apply_current_infrastructure_plan

**Entry point:** `sync_cmd._apply_current_infrastructure_plan`
**Modules involved:** [io](../modules/io.md), [maintenance_protocol](../modules/maintenance_protocol.md), [source_snapshot](../modules/source_snapshot.md), [sync_cmd](../modules/sync_cmd.md)

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `source_snapshot.unsupported_source_summary`
2. `maintenance_protocol.unlink_maintenance_page`
3. `maintenance_protocol.unlink_maintenance_page`
4. `io.read_md`
5. `io.read_md`
6. `maintenance_protocol.unlink_maintenance_page`

## Touches

- [io](../modules/io.md)
- [maintenance_protocol](../modules/maintenance_protocol.md)
- [source_snapshot](../modules/source_snapshot.md)
- [sync_cmd](../modules/sync_cmd.md)

## Behavior

This workflow starts at `sync_cmd._apply_current_infrastructure_plan`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
