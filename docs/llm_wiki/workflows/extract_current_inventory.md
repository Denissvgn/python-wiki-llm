# extract_current_inventory

**Entry point:** `sync_runtime._extract_current_inventory`
**Modules involved:** [extraction_service](../modules/extraction_service.md), [host](../modules/host.md), [source_snapshot](../modules/source_snapshot.md), [sync_runtime](../modules/sync_runtime.md)

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `host.emit`
2. `source_snapshot.build_source_snapshot`
3. `extraction_service.get_inventory_result`
4. `extraction_service.print_inventory_failures`
5. `source_snapshot.format_unsupported_source_summary`
6. `source_snapshot.unsupported_source_summary`
7. `host.emit`
8. `host.emit`

## Touches

- [extraction_service](../modules/extraction_service.md)
- [host](../modules/host.md)
- [source_snapshot](../modules/source_snapshot.md)
- [sync_runtime](../modules/sync_runtime.md)

## Behavior

This workflow starts at `sync_runtime._extract_current_inventory`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
