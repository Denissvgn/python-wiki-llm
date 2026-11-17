# prepare_sync_page_maps

**Entry point:** `sync_runtime._prepare_sync_page_maps`
**Modules involved:** [bootstrap_runtime](../modules/bootstrap_runtime.md), [host](../modules/host.md), [progress](../modules/progress.md), [sync_runtime](../modules/sync_runtime.md)

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `host.emit`
2. `bootstrap_runtime.build_module_page_map`
3. `bootstrap_runtime.build_entity_occurrence_page_map`
4. `bootstrap_runtime.build_entity_page_map`
5. `progress.record_counts`
6. `host.emit`

## Touches

- [bootstrap_runtime](../modules/bootstrap_runtime.md)
- [host](../modules/host.md)
- [progress](../modules/progress.md)
- [sync_runtime](../modules/sync_runtime.md)

## Behavior

This workflow starts at `sync_runtime._prepare_sync_page_maps`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
