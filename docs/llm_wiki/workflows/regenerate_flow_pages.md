# regenerate_flow_pages

**Entry point:** `sync_cmd._regenerate_flow_pages`
**Modules involved:** [bootstrap_runtime](../modules/bootstrap_runtime.md), [data_flow](../modules/data_flow.md), [entrypoints](../modules/entrypoints.md), [extraction_service](../modules/extraction_service.md), [io](../modules/io.md), [plugins](../modules/plugins.md), [sync_cmd](../modules/sync_cmd.md), [wiki_surface](../modules/wiki_surface.md)

> Regenerate flow pages from the current inventory, preserving Behavior.

Legacy projects run only when a flow page already exists; explicit surface
policy can opt into creating selected missing pages. Detection and Mermaid
diagrams are recomputed from the full inventory, content-equal pages are not
rewritten, and human-edited ``## Behavior`` is preserved by default.

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `extraction_service.resolve_call_edges`
2. `data_flow.build_data_flow_context`
3. `wiki_surface.canonical_path`
4. `entrypoints.build_flow`
5. `data_flow.analyze_data_flow`
6. `bootstrap_runtime._generate_flow_md`
7. `bootstrap_runtime._generated_diagram_style`
8. `plugins.runtime_plugin_fallback_root`
9. `plugins.runtime_project_plugins_enabled`
10. `io.read_md`

## Touches

- [bootstrap_runtime](../modules/bootstrap_runtime.md)
- [data_flow](../modules/data_flow.md)
- [entrypoints](../modules/entrypoints.md)
- [extraction_service](../modules/extraction_service.md)
- [io](../modules/io.md)
- [plugins](../modules/plugins.md)
- [sync_cmd](../modules/sync_cmd.md)
- [wiki_surface](../modules/wiki_surface.md)

## Behavior

This workflow starts at `sync_cmd._regenerate_flow_pages`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
