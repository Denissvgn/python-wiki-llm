# build_live_documentation_query_service

**Entry point:** `documentation_query_builder.build_live_documentation_query_service`
**Modules involved:** [context_packet_builder](../modules/context_packet_builder.md), [documentation_query_builder](../modules/documentation_query_builder.md), [knowledge_consumption](../modules/knowledge_consumption.md), [knowledge_storage_io](../modules/knowledge_storage_io.md), [maintenance_status](../modules/maintenance_status.md), [python_implementation](../modules/python_implementation.md), [query_request_format](../modules/query_request_format.md), [source_path_diagnostics](../modules/source_path_diagnostics.md), [source_selection](../modules/source_selection.md), [source_snapshot](../modules/source_snapshot.md)

> Build a live service using one operation-scoped extraction.

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `query_request_format.normalize_supplied_paths`
2. `query_request_format.DocumentationQueryError`
3. `query_request_format.DocumentationQueryError`
4. `source_selection.resolve_source_selection`
5. `query_request_format.DocumentationQueryError`
6. `source_snapshot.capture_source_selection_inputs`
7. `query_request_format.validate_live_query_source_selection`
8. `context_packet_builder._source_anchor`
9. `context_packet_builder._wiki_anchor`
10. `source_path_diagnostics.source_path_diagnostics`
11. `query_request_format.DocumentationQueryError`
12. `query_request_format.validate_live_query_source_selection`
13. `query_request_format.DocumentationQueryError`
14. `context_packet_builder.confirmed_missing_source_paths`
15. `knowledge_consumption.attach_implementation_read_view`
16. `python_implementation.analysis_identity`
17. `knowledge_storage_io.read_guarded`
18. `maintenance_status.attach_maintenance_view_from_inputs`
19. `query_request_format.DocumentationQueryError`
20. `context_packet_builder._assert_source_unchanged`
21. `context_packet_builder._assert_wiki_unchanged`

## Touches

- [context_packet_builder](../modules/context_packet_builder.md)
- [documentation_query_builder](../modules/documentation_query_builder.md)
- [knowledge_consumption](../modules/knowledge_consumption.md)
- [knowledge_storage_io](../modules/knowledge_storage_io.md)
- [maintenance_status](../modules/maintenance_status.md)
- [python_implementation](../modules/python_implementation.md)
- [query_request_format](../modules/query_request_format.md)
- [source_path_diagnostics](../modules/source_path_diagnostics.md)
- [source_selection](../modules/source_selection.md)
- [source_snapshot](../modules/source_snapshot.md)

## Behavior

This workflow starts at `documentation_query_builder.build_live_documentation_query_service`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
