# ContextSession__read

**Entry point:** `context_session.ContextSession._read`
**Modules involved:** [context_session](../modules/context_session.md), [immutable](../modules/immutable.md), [task_compact](../modules/task_compact.md), [task_context](../modules/task_context.md), [task_contract](../modules/task_contract.md), [workflow_profile](../modules/workflow_profile.md)

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `workflow_profile.WorkflowRequestError`
2. `workflow_profile.WorkflowRequestError`
3. `workflow_profile.WorkflowRequestError`
4. `task_contract.normalize_task_request`
5. `task_context._counter`
6. `task_compact.normalize_view_options`
7. `workflow_profile.WorkflowRequestError`
8. `task_compact._CheckedCounter`
9. `workflow_profile.WorkflowRequestError`
10. `workflow_profile.WorkflowRequestError`
11. `workflow_profile.WorkflowRequestError`
12. `workflow_profile.content_id`
13. `workflow_profile.WorkflowRequestError`
14. `immutable.freeze`
15. `workflow_profile.canonical_json`
16. `task_compact.render_compact_task_context`
17. `workflow_profile.canonical_json`
18. `workflow_profile.canonical_json`
19. `workflow_profile.canonical_json`
20. `immutable.freeze`
21. `immutable.freeze`
22. `immutable.freeze`
23. `immutable.freeze`
24. `immutable.freeze`
25. `immutable.freeze`
26. `immutable.freeze`

## Touches

- [context_session](../modules/context_session.md)
- [immutable](../modules/immutable.md)
- [task_compact](../modules/task_compact.md)
- [task_context](../modules/task_context.md)
- [task_contract](../modules/task_contract.md)
- [workflow_profile](../modules/workflow_profile.md)

## Behavior

This workflow starts at `context_session.ContextSession._read`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
