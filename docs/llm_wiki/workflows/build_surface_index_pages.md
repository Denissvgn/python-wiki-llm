# build_surface_index_pages

**Entry point:** `review_cmd._build_surface_index_pages`
**Modules involved:** [entrypoints](../modules/entrypoints.md), [plugins](../modules/plugins.md), [review_cmd](../modules/review_cmd.md), [wiki_surface_index](../modules/wiki_surface_index.md)

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `entrypoints.read_console_scripts`
2. `entrypoints.get_entry_points`
3. `plugins.runtime_plugin_fallback_root`
4. `plugins.runtime_project_plugins_enabled`
5. `wiki_surface_index.build_surface_index`

## Touches

- [entrypoints](../modules/entrypoints.md)
- [plugins](../modules/plugins.md)
- [review_cmd](../modules/review_cmd.md)
- [wiki_surface_index](../modules/wiki_surface_index.md)

## Behavior

This workflow starts at `review_cmd._build_surface_index_pages`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
