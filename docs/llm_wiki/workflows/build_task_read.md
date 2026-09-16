# build_task_read

**Entry point:** `task_context.build_task_read`
**Modules involved:** [config](../modules/config.md), [task_context](../modules/task_context.md), [task_contract](../modules/task_contract.md), [workflow_profile](../modules/workflow_profile.md)

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `task_contract.normalize_task_request`
2. `workflow_profile.WorkflowRequestError`
3. `config.validate_source_root`
4. `config.validate_path`

## Touches

- [config](../modules/config.md)
- [task_context](../modules/task_context.md)
- [task_contract](../modules/task_contract.md)
- [workflow_profile](../modules/workflow_profile.md)

## Behavior

This workflow starts at `task_context.build_task_read`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
