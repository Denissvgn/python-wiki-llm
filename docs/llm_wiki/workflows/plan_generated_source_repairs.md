# plan_generated_source_repairs

**Entry point:** `sync_generated_sections.plan_generated_source_repairs`
**Modules involved:** [knowledge_storage_io](../modules/knowledge_storage_io.md), [sync_generated_sections](../modules/sync_generated_sections.md), [sync_ownership](../modules/sync_ownership.md), [sync_transitions](../modules/sync_transitions.md)

> Preflight all retained owners and semantic attribution before any write.

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `knowledge_storage_io.StorageReadSession`
2. `knowledge_storage_io.StorageReadSession.read`
3. `sync_transitions.RetainedPageRepair`
4. `sync_ownership.PageTransitionError`

## Touches

- [knowledge_storage_io](../modules/knowledge_storage_io.md)
- [sync_generated_sections](../modules/sync_generated_sections.md)
- [sync_ownership](../modules/sync_ownership.md)
- [sync_transitions](../modules/sync_transitions.md)

## Behavior

This workflow starts at `sync_generated_sections.plan_generated_source_repairs`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
