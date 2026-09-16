# task_cmd_flow

**Entry point:** `task_cmd.run`
**Modules involved:** [api](../modules/api.md), [io](../modules/io.md), [request_json](../modules/request_json.md), [task_cmd](../modules/task_cmd.md), [token_counting](../modules/token_counting.md), [workflow_profile](../modules/workflow_profile.md)

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `request_json.load_request`
2. `workflow_profile.WorkflowPolicy`
3. `api.load_workflow_profile`
4. `token_counting.LocalTokenizerCounter`
5. `api.build_task_context`
6. `io.write_text_output`
7. `io.write_utf8_stdout`

## Touches

- [api](../modules/api.md)
- [io](../modules/io.md)
- [request_json](../modules/request_json.md)
- [task_cmd](../modules/task_cmd.md)
- [token_counting](../modules/token_counting.md)
- [workflow_profile](../modules/workflow_profile.md)

## Behavior

This workflow starts at `task_cmd.run`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
