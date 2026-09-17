# query_cmd_flow

**Entry point:** `query_cmd.run`
**Modules involved:** [api](../modules/api.md), [io](../modules/io.md), [query_cmd](../modules/query_cmd.md), [request_json](../modules/request_json.md)

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `request_json.load_request`
2. `api.query_documentation`
3. `io.write_text_output`
4. `io.write_utf8_stdout`

## Touches

- [api](../modules/api.md)
- [io](../modules/io.md)
- [query_cmd](../modules/query_cmd.md)
- [request_json](../modules/request_json.md)

## Behavior

This workflow starts at `query_cmd.run`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
