# apply_current_infrastructure_plan

**Entry point:** `sync_runtime._apply_current_infrastructure_plan`
**Modules involved:** [host](../modules/host.md), [io](../modules/io.md), [maintenance_protocol](../modules/maintenance_protocol.md), [source_snapshot](../modules/source_snapshot.md), [sync_runtime](../modules/sync_runtime.md)

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `source_snapshot.unsupported_source_summary`
2. `maintenance_protocol.unlink_maintenance_page`
3. `host.emit`
4. `maintenance_protocol.unlink_maintenance_page`
5. `host.emit`
6. `io.read_md`
7. `io.read_md`
8. `maintenance_protocol.unlink_maintenance_page`
9. `host.emit`

## Touches

- [host](../modules/host.md)
- [io](../modules/io.md)
- [maintenance_protocol](../modules/maintenance_protocol.md)
- [source_snapshot](../modules/source_snapshot.md)
- [sync_runtime](../modules/sync_runtime.md)

## Behavior

This workflow starts at `sync_runtime._apply_current_infrastructure_plan`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
