# capture_context_read

**Entry point:** `context_packet.capture_context_read`
**Modules involved:** [config](../modules/config.md), [context_packet](../modules/context_packet.md), [context_service](../modules/context_service.md), [data_flow](../modules/data_flow.md), [documentation_query_builder](../modules/documentation_query_builder.md), [entrypoints](../modules/entrypoints.md), [extraction_service](../modules/extraction_service.md), [knowledge_storage_io](../modules/knowledge_storage_io.md), [maintenance_status](../modules/maintenance_status.md), [plugins](../modules/plugins.md), [services_dependencies](../modules/services_dependencies.md), [source_selection](../modules/source_selection.md), [source_snapshot](../modules/source_snapshot.md), [wiki_surface_index](../modules/wiki_surface_index.md)

> Capture one source inventory, wiki surface, and knowledge read view.

The function is read-only.  It brackets wiki reads with a content anchor
and validates the source snapshot after extraction, rejecting an
inconsistent capture rather than returning a partially detached view.

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `config.validate_source_root`
2. `config.validate_path`
3. `source_selection.resolve_source_selection`
4. `source_snapshot.capture_source_selection_inputs`
5. `documentation_query_builder.validate_live_query_source_selection`
6. `context_service.ProtocolRequestError`
7. `context_service.ProtocolRequestError`
8. `source_snapshot.build_source_snapshot`
9. `context_service.ProtocolRequestError`
10. `context_service._extractor_failure_message`
11. `documentation_query_builder.validate_live_query_source_selection`
12. `context_service.ProtocolRequestError`
13. `entrypoints.get_entry_points`
14. `entrypoints.read_console_scripts`
15. `plugins.runtime_plugin_fallback_root`
16. `extraction_service.resolve_call_edges`
17. `entrypoints.build_flow`
18. `data_flow.build_data_flow_context`
19. `data_flow.analyze_data_flow`
20. `wiki_surface_index.evaluate_surface_index`
21. `context_service._build_context_knowledge_view`
22. `services_dependencies.analyze_dependencies`
23. `context_service.ProtocolRequestError`
24. `context_service.ProtocolRequestError`
25. `context_service._selected_git_changed_files`
26. `documentation_query_builder.validate_live_query_source_selection`
27. `context_service.ProtocolRequestError`
28. `knowledge_storage_io.read_guarded`
29. `maintenance_status.attach_maintenance_status`

## Touches

- [config](../modules/config.md)
- [context_packet](../modules/context_packet.md)
- [context_service](../modules/context_service.md)
- [data_flow](../modules/data_flow.md)
- [documentation_query_builder](../modules/documentation_query_builder.md)
- [entrypoints](../modules/entrypoints.md)
- [extraction_service](../modules/extraction_service.md)
- [knowledge_storage_io](../modules/knowledge_storage_io.md)
- [maintenance_status](../modules/maintenance_status.md)
- [plugins](../modules/plugins.md)
- [services_dependencies](../modules/services_dependencies.md)
- [source_selection](../modules/source_selection.md)
- [source_snapshot](../modules/source_snapshot.md)
- [wiki_surface_index](../modules/wiki_surface_index.md)

## Behavior

This workflow starts at `context_packet.capture_context_read`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
