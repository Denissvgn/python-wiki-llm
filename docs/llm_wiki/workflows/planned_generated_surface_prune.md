# planned_generated_surface_prune

**Entry point:** `sync_cmd._planned_generated_surface_prune`
**Modules involved:** [extraction_service](../modules/extraction_service.md), [io](../modules/io.md), [sync_cmd](../modules/sync_cmd.md), [wiki_surface](../modules/wiki_surface.md)

> Prove managed live workflows and generated pages absent from the live set.

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `wiki_surface.canonical_path`
2. `extraction_service.get_call_graph`
3. `wiki_surface.canonical_path`
4. `wiki_surface.canonical_path`
5. `wiki_surface.PageKind`
6. `io.read_md`
7. `wiki_surface.PageKind`

## Touches

- [extraction_service](../modules/extraction_service.md)
- [io](../modules/io.md)
- [sync_cmd](../modules/sync_cmd.md)
- [wiki_surface](../modules/wiki_surface.md)

## Behavior

This workflow starts at `sync_cmd._planned_generated_surface_prune`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
