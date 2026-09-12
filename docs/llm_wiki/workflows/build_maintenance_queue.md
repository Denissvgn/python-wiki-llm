# build_maintenance_queue

**Entry point:** `maintenance_queue.build_maintenance_queue`
**Modules involved:** [context_packet](../modules/context_packet.md), [documentation_worklist](../modules/documentation_worklist.md), [inventory_cache](../modules/inventory_cache.md), [lint_service](../modules/lint_service.md), [maintenance_queue](../modules/maintenance_queue.md)

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `context_packet.capture_context_read`
2. `lint_service.build_report`
3. `inventory_cache.InventoryCacheOptions`
4. `documentation_worklist.build_documentation_worklist`
5. `context_packet._assert_source_unchanged`
6. `context_packet._assert_wiki_unchanged`
7. `context_packet._assert_selection_unchanged`

## Touches

- [context_packet](../modules/context_packet.md)
- [documentation_worklist](../modules/documentation_worklist.md)
- [inventory_cache](../modules/inventory_cache.md)
- [lint_service](../modules/lint_service.md)
- [maintenance_queue](../modules/maintenance_queue.md)

## Behavior

This workflow starts at `maintenance_queue.build_maintenance_queue`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
