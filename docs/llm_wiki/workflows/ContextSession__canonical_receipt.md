# ContextSession__canonical_receipt

**Entry point:** `context_session.ContextSession._canonical_receipt`
**Modules involved:** [context_session](../modules/context_session.md), [immutable](../modules/immutable.md), [task_compact](../modules/task_compact.md), [task_context](../modules/task_context.md), [workflow_profile](../modules/workflow_profile.md)

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `workflow_profile.WorkflowRequestError`
2. `workflow_profile.WorkflowRequestError`
3. `workflow_profile.WorkflowRequestError`
4. `workflow_profile.WorkflowRequestError`
5. `task_compact._CheckedCounter`
6. `task_context._counter`
7. `task_context.validate_task_context`
8. `workflow_profile.WorkflowRequestError`
9. `workflow_profile.WorkflowRequestError`
10. `workflow_profile.WorkflowRequestError`
11. `workflow_profile.WorkflowRequestError`
12. `workflow_profile.WorkflowRequestError`
13. `workflow_profile.WorkflowRequestError`
14. `immutable.freeze`

## Touches

- [context_session](../modules/context_session.md)
- [immutable](../modules/immutable.md)
- [task_compact](../modules/task_compact.md)
- [task_context](../modules/task_context.md)
- [workflow_profile](../modules/workflow_profile.md)

## Behavior

This workflow starts at `context_session.ContextSession._canonical_receipt`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
