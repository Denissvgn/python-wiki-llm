# rebuild_surface_only_index

**Entry point:** `sync_cmd._rebuild_surface_only_index`
**Modules involved:** [bootstrap_runtime](../modules/bootstrap_runtime.md), [io](../modules/io.md), [sync_cmd](../modules/sync_cmd.md), [wiki_surface](../modules/wiki_surface.md)

> Re-index only pages already present during source-deferred backfill.

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `bootstrap_runtime._module_name_from_path`
2. `wiki_surface.canonical_path`
3. `bootstrap_runtime._generate_index_md`
4. `wiki_surface.canonical_path`
5. `wiki_surface.canonical_path`
6. `io.read_md`

## Touches

- [bootstrap_runtime](../modules/bootstrap_runtime.md)
- [io](../modules/io.md)
- [sync_cmd](../modules/sync_cmd.md)
- [wiki_surface](../modules/wiki_surface.md)

## Behavior

This workflow starts at `sync_cmd._rebuild_surface_only_index`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
