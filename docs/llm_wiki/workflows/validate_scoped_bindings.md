# validate_scoped_bindings

**Entry point:** `task_context_v2.validate_scoped_bindings`
**Modules involved:** [knowledge_envelope](../modules/knowledge_envelope.md), [knowledge_graph](../modules/knowledge_graph.md), [knowledge_storage](../modules/knowledge_storage.md), [knowledge_storage_io](../modules/knowledge_storage_io.md), [maintenance_status](../modules/maintenance_status.md), [storage_receipts](../modules/storage_receipts.md), [task_context](../modules/task_context.md), [task_context_v2](../modules/task_context_v2.md), [validation](../modules/validation.md), [workflow_profile](../modules/workflow_profile.md)

> Validate portable scope and consumed-input bindings, without claiming authenticity.

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `storage_receipts.expand_storage_receipt`
2. `task_context._result_fields`
3. `task_context._result_fields`
4. `validation.is_portable_relative_path`
5. `task_context._result_fields`
6. `knowledge_storage_io.range_batches`
7. `task_context._result_fields`
8. `task_context._result_fields`
9. `knowledge_envelope.ConsumedInput`
10. `knowledge_envelope.hash_source_snapshot`
11. `workflow_profile.content_id`
12. `knowledge_storage._concept_aliases`
13. `maintenance_status.validate_maintenance_summary`
14. `task_context._result_fields`
15. `knowledge_graph._normalise_edge`

## Touches

- [knowledge_envelope](../modules/knowledge_envelope.md)
- [knowledge_graph](../modules/knowledge_graph.md)
- [knowledge_storage](../modules/knowledge_storage.md)
- [knowledge_storage_io](../modules/knowledge_storage_io.md)
- [maintenance_status](../modules/maintenance_status.md)
- [storage_receipts](../modules/storage_receipts.md)
- [task_context](../modules/task_context.md)
- [task_context_v2](../modules/task_context_v2.md)
- [validation](../modules/validation.md)
- [workflow_profile](../modules/workflow_profile.md)

## Behavior

Validates task-v2 scope and internal receipt consistency without treating portable hashes as authenticity. Packed storage receipts require bounded sorted nonoverlapping ranges, consistent pack sizes and selected-member archive scope. Root/manifest, work totals, source inputs and fact citations must agree with the declared request and profile.
