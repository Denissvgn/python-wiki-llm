# save

**Entry point:** `sync_analysis_cache.save`
**Modules involved:** [io](../modules/io.md), [runtime_output](../modules/runtime_output.md), [sync_analysis_cache](../modules/sync_analysis_cache.md), [sync_analysis_storage](../modules/sync_analysis_storage.md)

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `io.first_unsafe_path_component`
2. `sync_analysis_storage.save`
3. `runtime_output.warn`

## Touches

- [io](../modules/io.md)
- [runtime_output](../modules/runtime_output.md)
- [sync_analysis_cache](../modules/sync_analysis_cache.md)
- [sync_analysis_storage](../modules/sync_analysis_storage.md)

## Behavior

This workflow starts at `sync_analysis_cache.save`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
