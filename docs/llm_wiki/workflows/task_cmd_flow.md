# task_cmd_flow

**Entry point:** `task_cmd.run`
**Modules involved:** [io](../modules/io.md), [request_json](../modules/request_json.md), [task_cmd](../modules/task_cmd.md), [token_counting](../modules/token_counting.md)

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `request_json.load_request`
2. `token_counting.LocalTokenizerCounter`
3. `io.write_utf8_stdout`
4. `io.write_text_output`
5. `io.write_utf8_stdout`

## Touches

- [io](../modules/io.md)
- [request_json](../modules/request_json.md)
- [task_cmd](../modules/task_cmd.md)
- [token_counting](../modules/token_counting.md)

## Behavior

This workflow starts at `task_cmd.run`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
