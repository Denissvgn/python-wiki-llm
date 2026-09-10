# regenerate_workflow_pages

**Entry point:** `sync_cmd._regenerate_workflow_pages`
**Modules involved:** [bootstrap_runtime](../modules/bootstrap_runtime.md), [extraction_service](../modules/extraction_service.md), [io](../modules/io.md), [sync_cmd](../modules/sync_cmd.md), [wiki_surface](../modules/wiki_surface.md)

> Refresh proven generated workflows and create explicitly planned pages.

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `extraction_service.get_call_graph`
2. `wiki_surface.canonical_path`
3. `io.read_md`
4. `bootstrap_runtime._generate_workflow_md`

## Touches

- [bootstrap_runtime](../modules/bootstrap_runtime.md)
- [extraction_service](../modules/extraction_service.md)
- [io](../modules/io.md)
- [sync_cmd](../modules/sync_cmd.md)
- [wiki_surface](../modules/wiki_surface.md)

## Behavior

This workflow starts at `sync_cmd._regenerate_workflow_pages`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
