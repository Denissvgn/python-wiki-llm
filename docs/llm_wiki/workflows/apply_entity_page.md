# apply_entity_page

**Entry point:** `sync_cmd._apply_entity_page`
**Modules involved:** [bootstrap_runtime](../modules/bootstrap_runtime.md), [plugins](../modules/plugins.md), [sync_cmd](../modules/sync_cmd.md), [wiki_surface](../modules/wiki_surface.md)

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `wiki_surface.canonical_path`
2. `bootstrap_runtime._generate_entity_md`
3. `bootstrap_runtime._generated_diagram_style`
4. `plugins.runtime_plugin_fallback_root`
5. `plugins.runtime_project_plugins_enabled`

## Touches

- [bootstrap_runtime](../modules/bootstrap_runtime.md)
- [plugins](../modules/plugins.md)
- [sync_cmd](../modules/sync_cmd.md)
- [wiki_surface](../modules/wiki_surface.md)

## Behavior

This workflow starts at `sync_cmd._apply_entity_page`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
