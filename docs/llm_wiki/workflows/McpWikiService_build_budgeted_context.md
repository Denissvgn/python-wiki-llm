# McpWikiService_build_budgeted_context

**Entry point:** `mcp_server.McpWikiService.build_budgeted_context`
**Modules involved:** [api](../modules/api.md), [context_budget](../modules/context_budget.md), [context_service](../modules/context_service.md), [mcp_server](../modules/mcp_server.md)

> Return precisely the canonical v3 text counted by the host counter.

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `context_budget.validate_request`
2. `context_service.ProtocolRequestError`
3. `api.build_budgeted_context`

## Touches

- [api](../modules/api.md)
- [context_budget](../modules/context_budget.md)
- [context_service](../modules/context_service.md)
- [mcp_server](../modules/mcp_server.md)

## Behavior

This workflow starts at `mcp_server.McpWikiService.build_budgeted_context`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
