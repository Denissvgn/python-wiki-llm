# normalize_task_request

**Entry point:** `task_contract.normalize_task_request`
**Modules involved:** [change_selection](../modules/change_selection.md), [documentation_query_builder](../modules/documentation_query_builder.md), [task_contract](../modules/task_contract.md), [workflow_profile](../modules/workflow_profile.md)

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `workflow_profile.exact_fields`
2. `workflow_profile.WorkflowRequestError`
3. `workflow_profile.bounded_text`
4. `workflow_profile.WorkflowRequestError`
5. `workflow_profile.bounded_text`
6. `workflow_profile.exact_fields`
7. `workflow_profile.WorkflowRequestError`
8. `workflow_profile.canonical_json`
9. `workflow_profile.exact_fields`
10. `workflow_profile.bounded_text`
11. `workflow_profile.WorkflowRequestError`
12. `workflow_profile.WorkflowRequestError`
13. `workflow_profile.WorkflowRequestError`
14. `change_selection.validate_changes`
15. `workflow_profile.WorkflowRequestError`
16. `documentation_query_builder.normalize_supplied_paths`
17. `workflow_profile.normalize_profile`
18. `workflow_profile.content_id`
19. `workflow_profile.content_id`

## Touches

- [change_selection](../modules/change_selection.md)
- [documentation_query_builder](../modules/documentation_query_builder.md)
- [task_contract](../modules/task_contract.md)
- [workflow_profile](../modules/workflow_profile.md)

## Behavior

This workflow starts at `task_contract.normalize_task_request`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
