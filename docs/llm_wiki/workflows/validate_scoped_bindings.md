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
6. `task_context._result_fields`
7. `knowledge_envelope.ConsumedInput`
8. `knowledge_envelope.hash_source_snapshot`
9. `workflow_profile.content_id`
10. `knowledge_storage._concept_aliases`

## Touches

- [knowledge_envelope](../modules/knowledge_envelope.md)
- [knowledge_evidence](../modules/knowledge_evidence.md)
- [knowledge_storage](../modules/knowledge_storage.md)
- [task_context](../modules/task_context.md)
- [task_context_v2](../modules/task_context_v2.md)
- [validation](../modules/validation.md)
- [workflow_profile](../modules/workflow_profile.md)

## Behavior

Validates the v2 result’s declared scope, actual storage accounting, source commitments, citations and exact selector bindings. It rejects whole-store claims, unrelated observations and legacy full-validity packets in a selected result. Content identities establish consistency, not authenticity or semantic truth.
