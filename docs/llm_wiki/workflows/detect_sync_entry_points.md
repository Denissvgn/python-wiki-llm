# detect_sync_entry_points

**Entry point:** `sync_runtime._detect_sync_entry_points`
**Modules involved:** [entrypoints](../modules/entrypoints.md), [host](../modules/host.md), [plugins](../modules/plugins.md), [sync_runtime](../modules/sync_runtime.md)

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `entrypoints.read_console_scripts`
2. `entrypoints.get_detailed_entry_points`
3. `plugins.runtime_plugin_fallback_root`
4. `plugins.runtime_project_plugins_enabled`
5. `host.emit`
6. `entrypoints.entry_points_from_detailed_observations`

## Touches

- [entrypoints](../modules/entrypoints.md)
- [host](../modules/host.md)
- [plugins](../modules/plugins.md)
- [sync_runtime](../modules/sync_runtime.md)

## Behavior

This workflow starts at `sync_runtime._detect_sync_entry_points`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
