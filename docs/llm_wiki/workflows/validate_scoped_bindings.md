# validate_scoped_bindings

**Entry point:** `task_context_v2.validate_scoped_bindings`
**Modules involved:** [knowledge_envelope](../modules/knowledge_envelope.md), [knowledge_evidence](../modules/knowledge_evidence.md), [knowledge_storage](../modules/knowledge_storage.md), [knowledge_storage_io](../modules/knowledge_storage_io.md), [storage_receipts](../modules/storage_receipts.md), [task_context](../modules/task_context.md), [task_context_v2](../modules/task_context_v2.md), [validation](../modules/validation.md), [workflow_profile](../modules/workflow_profile.md)

> Validate portable scope and consumed-input bindings, without claiming authenticity.

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `storage_receipts.expand_storage_receipt`
2. `task_context._result_fields`
3. `task_context._result_fields`
4. `validation.is_portable_relative_path`
5. `knowledge_evidence.is_valid_sha256`
6. `task_context._result_fields`
7. `knowledge_evidence.is_valid_sha256`
8. `knowledge_storage_io.range_batches`
9. `task_context._result_fields`
10. `task_context._result_fields`
11. `knowledge_envelope.ConsumedInput`
12. `knowledge_envelope.hash_source_snapshot`
13. `workflow_profile.content_id`
14. `knowledge_storage._concept_aliases`

## Touches

- [knowledge_envelope](../modules/knowledge_envelope.md)
- [knowledge_evidence](../modules/knowledge_evidence.md)
- [knowledge_storage](../modules/knowledge_storage.md)
- [knowledge_storage_io](../modules/knowledge_storage_io.md)
- [storage_receipts](../modules/storage_receipts.md)
- [task_context](../modules/task_context.md)
- [task_context_v2](../modules/task_context_v2.md)
- [validation](../modules/validation.md)
- [workflow_profile](../modules/workflow_profile.md)

## Behavior

Validates task-v2 scope and internal receipt consistency without treating portable hashes as authenticity. Packed storage receipts require bounded sorted nonoverlapping ranges, consistent pack sizes and selected-member archive scope. Root/manifest, work totals, source inputs and fact citations must agree with the declared request and profile.
