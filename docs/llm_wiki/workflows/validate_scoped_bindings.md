# validate_scoped_bindings

**Entry point:** `task_context_v2.validate_scoped_bindings`
**Modules involved:** [knowledge_envelope](../modules/knowledge_envelope.md), [knowledge_evidence](../modules/knowledge_evidence.md), [knowledge_storage](../modules/knowledge_storage.md), [task_context](../modules/task_context.md), [task_context_v2](../modules/task_context_v2.md), [validation](../modules/validation.md), [workflow_profile](../modules/workflow_profile.md)

> Validate portable scope and consumed-input bindings, without claiming authenticity.

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `task_context._result_fields`
2. `task_context._result_fields`
3. `validation.is_portable_relative_path`
4. `knowledge_evidence.is_valid_sha256`
5. `task_context._result_fields`
6. `knowledge_evidence.is_valid_sha256`
7. `task_context._result_fields`
8. `task_context._result_fields`
9. `knowledge_envelope.ConsumedInput`
10. `knowledge_envelope.hash_source_snapshot`
11. `workflow_profile.content_id`
12. `knowledge_storage._concept_aliases`

## Touches

- [knowledge_envelope](../modules/knowledge_envelope.md)
- [knowledge_evidence](../modules/knowledge_evidence.md)
- [knowledge_storage](../modules/knowledge_storage.md)
- [task_context](../modules/task_context.md)
- [task_context_v2](../modules/task_context_v2.md)
- [validation](../modules/validation.md)
- [workflow_profile](../modules/workflow_profile.md)

## Behavior

Validates task-v2 scope and internal receipt consistency without treating portable hashes as authenticity. Packed storage receipts require bounded sorted nonoverlapping ranges, consistent pack sizes and selected-member archive scope. Root/manifest, work totals, source inputs and fact citations must agree with the declared request and profile.
