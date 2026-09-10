# regenerate_dependency_pages

**Entry point:** `sync_cmd._regenerate_dependency_pages`
**Modules involved:** [bootstrap_runtime](../modules/bootstrap_runtime.md), [io](../modules/io.md), [plugins](../modules/plugins.md), [sync_cmd](../modules/sync_cmd.md)

> Regenerate dependencies.md / load-order.md, preserving ``## Notes``.

Legacy projects regenerate only root pages already present. Explicit
surface policy may select missing architecture pages for creation. The
graph, cycles, reconciliation, and load order are computed once; unchanged
Markdown is not rewritten and human-authored ``## Notes`` is preserved.

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `bootstrap_runtime._generate_dependencies_md`
2. `bootstrap_runtime._generated_diagram_style`
3. `plugins.runtime_plugin_fallback_root`
4. `plugins.runtime_project_plugins_enabled`
5. `bootstrap_runtime._generate_load_order_md`
6. `io.read_md`

## Touches

- [bootstrap_runtime](../modules/bootstrap_runtime.md)
- [io](../modules/io.md)
- [plugins](../modules/plugins.md)
- [sync_cmd](../modules/sync_cmd.md)

## Behavior

This workflow starts at `sync_cmd._regenerate_dependency_pages`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
