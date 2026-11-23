# ContextSession___init__

**Entry point:** `context_session.ContextSession.__init__`
**Modules involved:** [context_session](../modules/context_session.md), [host](../modules/host.md), [path_policy](../modules/path_policy.md), [task_contract](../modules/task_contract.md), [workflow_profile](../modules/workflow_profile.md)

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `workflow_profile.bounded_int`
2. `workflow_profile.bounded_int`
3. `workflow_profile.WorkflowRequestError`
4. `host.current_host`
5. `path_policy.validate_source_root`
6. `path_policy.validate_path`
7. `task_contract.normalize_task_request`

## Touches

- [context_session](../modules/context_session.md)
- [host](../modules/host.md)
- [path_policy](../modules/path_policy.md)
- [task_contract](../modules/task_contract.md)
- [workflow_profile](../modules/workflow_profile.md)

## Behavior

This workflow starts at `context_session.ContextSession.__init__`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
