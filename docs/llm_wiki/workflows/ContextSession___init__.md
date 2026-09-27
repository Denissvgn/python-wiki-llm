# ContextSession___init__

**Entry point:** `context_session.ContextSession.__init__`
**Modules involved:** [analysis_compatibility](../modules/analysis_compatibility.md), [config](../modules/config.md), [context_session](../modules/context_session.md), [task_contract](../modules/task_contract.md), [workflow_profile](../modules/workflow_profile.md)

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `analysis_compatibility.selected_policy`
2. `workflow_profile.bounded_int`
3. `workflow_profile.bounded_int`
4. `workflow_profile.WorkflowRequestError`
5. `config.validate_source_root`
6. `config.validate_path`
7. `task_contract.normalize_task_request`

## Touches

- [analysis_compatibility](../modules/analysis_compatibility.md)
- [config](../modules/config.md)
- [context_session](../modules/context_session.md)
- [task_contract](../modules/task_contract.md)
- [workflow_profile](../modules/workflow_profile.md)

## Behavior

This workflow starts at `context_session.ContextSession.__init__`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
