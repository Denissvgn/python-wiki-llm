# rebuild_index

**Entry point:** `sync_runtime._rebuild_index`
**Modules involved:** [bootstrap_runtime](../modules/bootstrap_runtime.md), [host](../modules/host.md), [io](../modules/io.md), [sync_runtime](../modules/sync_runtime.md)

> Regenerate index.md from the live inventory.

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `bootstrap_runtime.build_module_page_map`
2. `bootstrap_runtime.build_entity_occurrence_page_map`
3. `bootstrap_runtime._page_name_for_module`
4. `bootstrap_runtime._generate_index_md`
5. `io.read_md`
6. `host.emit`
7. `host.emit`

## Touches

- [bootstrap_runtime](../modules/bootstrap_runtime.md)
- [host](../modules/host.md)
- [io](../modules/io.md)
- [sync_runtime](../modules/sync_runtime.md)

## Behavior

This workflow starts at `sync_runtime._rebuild_index`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
