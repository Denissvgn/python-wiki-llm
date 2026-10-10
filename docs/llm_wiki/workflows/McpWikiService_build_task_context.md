# McpWikiService_build_task_context

**Entry point:** `mcp_server.McpWikiService.build_task_context`
**Modules involved:** [api](../modules/api.md), [mcp_server](../modules/mcp_server.md), [task_context](../modules/task_context.md), [task_contract](../modules/task_contract.md)

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `task_contract.normalize_task_request`
2. `task_context._counter`
3. `api.build_task_context`

## Touches

- [api](../modules/api.md)
- [mcp_server](../modules/mcp_server.md)
- [task_context](../modules/task_context.md)
- [task_contract](../modules/task_contract.md)

## Behavior

This workflow starts at `mcp_server.McpWikiService.build_task_context`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
