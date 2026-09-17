# build_scoped_task_read

**Entry point:** `task_context_v2.build_scoped_task_read`
**Modules involved:** [change_selection](../modules/change_selection.md), [config](../modules/config.md), [context_budget](../modules/context_budget.md), [context_packet](../modules/context_packet.md), [knowledge_envelope](../modules/knowledge_envelope.md), [knowledge_storage_access](../modules/knowledge_storage_access.md), [source_selection](../modules/source_selection.md), [task_context](../modules/task_context.md), [task_context_v2](../modules/task_context_v2.md), [task_contract](../modules/task_contract.md), [task_evidence](../modules/task_evidence.md), [workflow_profile](../modules/workflow_profile.md)

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `task_contract.normalize_task_request`
2. `context_packet.ContextPacketUnavailableError`
3. `task_context._counter`
4. `workflow_profile.WorkflowRequestError`
5. `task_context._cancel`
6. `config.validate_source_root`
7. `config.validate_path`
8. `task_context.plan_source_read`
9. `task_context._cancel`
10. `knowledge_storage_access.capture_knowledge_slice`
11. `source_selection.validate_persisted_source_selection_identity`
12. `task_context._cancel`
13. `context_packet.ContextPacketUnavailableError`
14. `context_packet.ContextPacketUnavailableError`
15. `workflow_profile.content_id`
16. `workflow_profile.content_id`
17. `task_evidence.declaration_records`
18. `task_context._cancel`
19. `task_evidence.observe_requirement`
20. `task_evidence.observe_requirement`
21. `knowledge_envelope.hash_source_snapshot`
22. `workflow_profile.content_id`
23. `context_budget._accounted_render`
24. `task_contract.TaskContext`
25. `task_contract.TaskContext`
26. `task_context._cancel`
27. `workflow_profile.WorkflowRequestError`
28. `context_packet._assert_source_unchanged`
29. `change_selection.select_changes`
30. `context_packet.ContextPacketSourceMutationError`
31. `workflow_profile.WorkflowRequestError`
32. `context_packet.ContextPacketSourceMutationError`
33. `task_context.TaskRead`

## Touches

- [change_selection](../modules/change_selection.md)
- [config](../modules/config.md)
- [context_budget](../modules/context_budget.md)
- [context_packet](../modules/context_packet.md)
- [knowledge_envelope](../modules/knowledge_envelope.md)
- [knowledge_storage_access](../modules/knowledge_storage_access.md)
- [source_selection](../modules/source_selection.md)
- [task_context](../modules/task_context.md)
- [task_context_v2](../modules/task_context_v2.md)
- [task_contract](../modules/task_contract.md)
- [task_evidence](../modules/task_evidence.md)
- [workflow_profile](../modules/workflow_profile.md)

## Behavior

Normalizes the explicit task-v2 request, captures selected native/source evidence and composes requirement observations through existing semantic owners. Packed receipts identify member ranges and reserve their final validation work. The published context binds the committed root, selected scope, omissions and budgets; session state retains the observations needed to reproduce authoritative checks.
