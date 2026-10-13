# plan_source_page_transitions

**Entry point:** `sync_cmd._plan_source_page_transitions`
**Modules involved:** [knowledge_storage_io](../modules/knowledge_storage_io.md), [source_retirement](../modules/source_retirement.md), [source_selection](../modules/source_selection.md), [sync_cmd](../modules/sync_cmd.md), [sync_transitions](../modules/sync_transitions.md)

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `source_selection.path_is_selected`
2. `sync_transitions.plan_page_transitions`
3. `source_retirement.discover_retired_entities`
4. `knowledge_storage_io.StorageReadSession`
5. `source_retirement.SourceRetirementError`
6. `sync_transitions.RetainedPageRepair`

## Touches

- [knowledge_storage_io](../modules/knowledge_storage_io.md)
- [source_retirement](../modules/source_retirement.md)
- [source_selection](../modules/source_selection.md)
- [sync_cmd](../modules/sync_cmd.md)
- [sync_transitions](../modules/sync_transitions.md)

## Behavior

Combines verified live transitions with source-member history repairs, excluding live moved paths. Retained content is captured under bounded guarded reads; the executor verifies exact originals and saves durable recovery data before application.
