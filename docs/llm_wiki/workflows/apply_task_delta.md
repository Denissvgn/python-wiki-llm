# apply_task_delta

**Entry point:** `context_session.apply_task_delta`
**Modules involved:** [context_session](../modules/context_session.md), [task_context](../modules/task_context.md), [task_contract](../modules/task_contract.md), [workflow_profile](../modules/workflow_profile.md)

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `workflow_profile.exact_fields`
2. `workflow_profile.WorkflowRequestError`
3. `task_context.validate_task_context`
4. `workflow_profile.WorkflowRequestError`
5. `workflow_profile.exact_fields`
6. `workflow_profile.WorkflowRequestError`
7. `workflow_profile.canonical_json`
8. `task_context.validate_task_context`
9. `workflow_profile.WorkflowRequestError`
10. `task_contract.TaskContext`

## Touches

- [context_session](../modules/context_session.md)
- [task_context](../modules/task_context.md)
- [task_contract](../modules/task_contract.md)
- [workflow_profile](../modules/workflow_profile.md)

## Behavior

This workflow starts at `context_session.apply_task_delta`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
