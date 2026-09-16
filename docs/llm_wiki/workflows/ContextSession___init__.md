# ContextSession___init__

**Entry point:** `context_session.ContextSession.__init__`
**Modules involved:** [config](../modules/config.md), [context_session](../modules/context_session.md), [task_contract](../modules/task_contract.md), [workflow_profile](../modules/workflow_profile.md)

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `workflow_profile.bounded_int`
2. `workflow_profile.bounded_int`
3. `workflow_profile.WorkflowRequestError`
4. `config.validate_source_root`
5. `config.validate_path`
6. `task_contract.normalize_task_request`

## Touches

- [config](../modules/config.md)
- [context_session](../modules/context_session.md)
- [task_contract](../modules/task_contract.md)
- [workflow_profile](../modules/workflow_profile.md)

## Behavior

This workflow starts at `context_session.ContextSession.__init__`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
