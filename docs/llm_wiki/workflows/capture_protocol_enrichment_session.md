# capture_protocol_enrichment_session

**Entry point:** `context_service._capture_protocol_enrichment_session`
**Modules involved:** [config](../modules/config.md), [context_service](../modules/context_service.md), [data_flow](../modules/data_flow.md), [documentation_queries](../modules/documentation_queries.md), [entrypoints](../modules/entrypoints.md), [extraction_service](../modules/extraction_service.md), [knowledge_verification](../modules/knowledge_verification.md), [plugins](../modules/plugins.md), [services_dependencies](../modules/services_dependencies.md), [wiki_surface_index](../modules/wiki_surface_index.md)

> Capture the immutable inputs shared by ranking and response assembly.

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `config.validate_path`
2. `entrypoints.get_entry_points`
3. `entrypoints.read_console_scripts`
4. `plugins.runtime_project_plugins_enabled`
5. `extraction_service.resolve_call_edges`
6. `entrypoints.build_flow`
7. `data_flow.build_data_flow_context`
8. `data_flow.analyze_data_flow`
9. `wiki_surface_index.evaluate_surface_index`
10. `documentation_queries.knowledge_view_selection_eligible`
11. `documentation_queries.DocumentationGraphQueryService`
12. `services_dependencies.analyze_dependencies`
13. `knowledge_verification.verification_summaries_for_concepts`

## Touches

- [config](../modules/config.md)
- [context_service](../modules/context_service.md)
- [data_flow](../modules/data_flow.md)
- [documentation_queries](../modules/documentation_queries.md)
- [entrypoints](../modules/entrypoints.md)
- [extraction_service](../modules/extraction_service.md)
- [knowledge_verification](../modules/knowledge_verification.md)
- [plugins](../modules/plugins.md)
- [services_dependencies](../modules/services_dependencies.md)
- [wiki_surface_index](../modules/wiki_surface_index.md)

## Behavior

This workflow starts at `context_service._capture_protocol_enrichment_session`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
