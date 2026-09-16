# validate_task_context

**Entry point:** `task_context.validate_task_context`
**Modules involved:** [context_packet](../modules/context_packet.md), [task_context](../modules/task_context.md), [task_contract](../modules/task_contract.md), [task_evidence](../modules/task_evidence.md), [workflow_profile](../modules/workflow_profile.md)

> Check the task envelope separately from the unchanged embedded packet.

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `task_contract.normalize_task_request`
2. `workflow_profile.canonical_json`
3. `workflow_profile.content_id`
4. `workflow_profile.content_id`
5. `task_evidence.match_declarations`
6. `workflow_profile.content_id`
7. `context_packet.validate_context_packet`
8. `context_packet._encode_packet_payload`
9. `workflow_profile.WorkflowRequestError`

## Touches

- [context_packet](../modules/context_packet.md)
- [task_context](../modules/task_context.md)
- [task_contract](../modules/task_contract.md)
- [task_evidence](../modules/task_evidence.md)
- [workflow_profile](../modules/workflow_profile.md)

## Behavior

This workflow starts at `task_context.validate_task_context`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
