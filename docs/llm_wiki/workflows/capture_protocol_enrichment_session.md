# capture_protocol_enrichment_session

**Entry point:** `context_service._capture_protocol_enrichment_session`
**Modules involved:** [context_request_format](../modules/context_request_format.md), [context_service](../modules/context_service.md), [data_flow](../modules/data_flow.md), [documentation_queries](../modules/documentation_queries.md), [entrypoints](../modules/entrypoints.md), [extraction_service](../modules/extraction_service.md), [host](../modules/host.md), [knowledge_verification](../modules/knowledge_verification.md), [path_policy](../modules/path_policy.md), [plugins](../modules/plugins.md), [services_dependencies](../modules/services_dependencies.md), [wiki_surface_index](../modules/wiki_surface_index.md)

> Capture the immutable inputs shared by ranking and response assembly.

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `path_policy.validate_path`
2. `entrypoints.get_entry_points`
3. `entrypoints.read_console_scripts`
4. `host.current_host`
5. `host.current_host`
6. `plugins.runtime_project_plugins_enabled`
7. `extraction_service.resolve_call_edges`
8. `entrypoints.build_flow`
9. `data_flow.build_data_flow_context`
10. `data_flow.analyze_data_flow`
11. `wiki_surface_index.evaluate_surface_index`
12. `documentation_queries.knowledge_view_selection_eligible`
13. `documentation_queries.DocumentationGraphQueryService`
14. `services_dependencies.analyze_dependencies`
15. `knowledge_verification.verification_summaries_for_concepts`
16. `context_request_format.ProtocolRequestError`
17. `context_request_format.ProtocolRequestError`
18. `context_request_format.ProtocolRequestError`
19. `context_request_format.ProtocolRequestError`

## Touches

- [context_request_format](../modules/context_request_format.md)
- [context_service](../modules/context_service.md)
- [data_flow](../modules/data_flow.md)
- [documentation_queries](../modules/documentation_queries.md)
- [entrypoints](../modules/entrypoints.md)
- [extraction_service](../modules/extraction_service.md)
- [host](../modules/host.md)
- [knowledge_verification](../modules/knowledge_verification.md)
- [path_policy](../modules/path_policy.md)
- [plugins](../modules/plugins.md)
- [services_dependencies](../modules/services_dependencies.md)
- [wiki_surface_index](../modules/wiki_surface_index.md)

## Behavior

This workflow starts at `context_service._capture_protocol_enrichment_session`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
