# McpWikiService_get_status

**Entry point:** `mcp_server.McpWikiService.get_status`
**Modules involved:** [circuit_breaker](../modules/circuit_breaker.md), [config](../modules/config.md), [knowledge_observability](../modules/knowledge_observability.md), [mcp_server](../modules/mcp_server.md), [wiki_surface](../modules/wiki_surface.md)

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `wiki_surface.iter_page_kinds`
2. `knowledge_observability.load_snapshot_knowledge_observability`
3. `knowledge_observability.knowledge_status_payload`
4. `config.get_agent_config_path`
5. `config.read_config`
6. `circuit_breaker.load_state`

## Touches

- [circuit_breaker](../modules/circuit_breaker.md)
- [config](../modules/config.md)
- [knowledge_observability](../modules/knowledge_observability.md)
- [mcp_server](../modules/mcp_server.md)
- [wiki_surface](../modules/wiki_surface.md)

## Behavior

This workflow starts at `mcp_server.McpWikiService.get_status`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
