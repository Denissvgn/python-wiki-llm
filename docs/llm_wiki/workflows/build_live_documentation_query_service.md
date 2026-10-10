# build_live_documentation_query_service

**Entry point:** `documentation_query_builder.build_live_documentation_query_service`
**Modules involved:** [context_packet](../modules/context_packet.md), [documentation_queries](../modules/documentation_queries.md), [documentation_query_builder](../modules/documentation_query_builder.md), [knowledge_consumption](../modules/knowledge_consumption.md), [knowledge_storage_io](../modules/knowledge_storage_io.md), [maintenance_status](../modules/maintenance_status.md), [python_implementation](../modules/python_implementation.md), [source_selection](../modules/source_selection.md), [source_snapshot](../modules/source_snapshot.md)

> Build a live service using one operation-scoped extraction.

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `documentation_queries.DocumentationQueryError`
2. `documentation_queries.DocumentationQueryError`
3. `source_selection.resolve_source_selection`
4. `documentation_queries.DocumentationQueryError`
5. `source_snapshot.capture_source_selection_inputs`
6. `context_packet._source_anchor`
7. `context_packet._wiki_anchor`
8. `documentation_queries.DocumentationQueryError`
9. `documentation_queries.DocumentationQueryError`
10. `context_packet.confirmed_missing_source_paths`
11. `knowledge_consumption.attach_implementation_read_view`
12. `python_implementation.analysis_identity`
13. `knowledge_storage_io.read_guarded`
14. `maintenance_status.attach_maintenance_view_from_inputs`
15. `documentation_queries.DocumentationQueryError`
16. `context_packet._assert_source_unchanged`
17. `context_packet._assert_wiki_unchanged`

## Touches

- [context_packet](../modules/context_packet.md)
- [documentation_queries](../modules/documentation_queries.md)
- [documentation_query_builder](../modules/documentation_query_builder.md)
- [knowledge_consumption](../modules/knowledge_consumption.md)
- [knowledge_storage_io](../modules/knowledge_storage_io.md)
- [maintenance_status](../modules/maintenance_status.md)
- [python_implementation](../modules/python_implementation.md)
- [source_selection](../modules/source_selection.md)
- [source_snapshot](../modules/source_snapshot.md)

## Behavior

This workflow starts at `documentation_query_builder.build_live_documentation_query_service`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
