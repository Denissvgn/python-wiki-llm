# refresh_module_dependency_sections

**Entry point:** `sync_cmd._refresh_module_dependency_sections`
**Modules involved:** [bootstrap_runtime](../modules/bootstrap_runtime.md), [io](../modules/io.md), [plugins](../modules/plugins.md), [sync_cmd](../modules/sync_cmd.md)

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `bootstrap_runtime._page_name_for_module`
2. `bootstrap_runtime._generate_module_md`
3. `bootstrap_runtime._generated_diagram_style`
4. `plugins.runtime_plugin_fallback_root`
5. `plugins.runtime_project_plugins_enabled`
6. `io.read_md`

## Touches

- [bootstrap_runtime](../modules/bootstrap_runtime.md)
- [io](../modules/io.md)
- [plugins](../modules/plugins.md)
- [sync_cmd](../modules/sync_cmd.md)

## Behavior

This workflow starts at `sync_cmd._refresh_module_dependency_sections`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
