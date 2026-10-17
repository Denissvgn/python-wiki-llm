# capture_context_read

**Entry point:** `context_packet.capture_context_read`
**Modules involved:** [config](../modules/config.md), [context_packet](../modules/context_packet.md), [context_service](../modules/context_service.md), [data_flow](../modules/data_flow.md), [documentation_query_builder](../modules/documentation_query_builder.md), [entrypoints](../modules/entrypoints.md), [extraction_service](../modules/extraction_service.md), [knowledge_loader](../modules/knowledge_loader.md), [knowledge_storage_io](../modules/knowledge_storage_io.md), [maintenance_protocol](../modules/maintenance_protocol.md), [maintenance_status](../modules/maintenance_status.md), [plugins](../modules/plugins.md), [services_dependencies](../modules/services_dependencies.md), [source_retirement](../modules/source_retirement.md), [source_selection](../modules/source_selection.md), [source_snapshot](../modules/source_snapshot.md), [wiki_surface_index](../modules/wiki_surface_index.md)

> Capture one source inventory, wiki surface, and knowledge read view.

The function is read-only.  It brackets wiki reads with a content anchor
and validates the source snapshot after extraction, rejecting an
inconsistent capture rather than returning a partially detached view.

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `config.validate_source_root`
2. `config.validate_path`
3. `maintenance_protocol.guard_maintenance_owner`
4. `knowledge_loader.KnowledgeLoadIssue`
5. `source_selection.resolve_source_selection`
6. `source_snapshot.capture_source_selection_inputs`
7. `documentation_query_builder.validate_live_query_source_selection`
8. `context_service.ProtocolRequestError`
9. `context_service.ProtocolRequestError`
10. `source_snapshot.build_source_snapshot`
11. `source_retirement.retained_empty_module_paths_from_wiki`
12. `context_service.ProtocolRequestError`
13. `context_service._extractor_failure_message`
14. `documentation_query_builder.validate_live_query_source_selection`
15. `context_service.ProtocolRequestError`
16. `entrypoints.get_entry_points`
17. `entrypoints.read_console_scripts`
18. `plugins.runtime_plugin_fallback_root`
19. `extraction_service.resolve_call_edges`
20. `entrypoints.build_flow`
21. `data_flow.build_data_flow_context`
22. `data_flow.analyze_data_flow`
23. `wiki_surface_index.evaluate_surface_index`
24. `context_service._build_context_knowledge_view`
25. `services_dependencies.analyze_dependencies`
26. `context_service.ProtocolRequestError`
27. `context_service.ProtocolRequestError`
28. `context_service._selected_git_changed_files`
29. `documentation_query_builder.validate_live_query_source_selection`
30. `context_service.ProtocolRequestError`
31. `knowledge_storage_io.read_guarded`
32. `maintenance_status.attach_maintenance_status`

## Touches

- [config](../modules/config.md)
- [context_packet](../modules/context_packet.md)
- [context_service](../modules/context_service.md)
- [data_flow](../modules/data_flow.md)
- [documentation_query_builder](../modules/documentation_query_builder.md)
- [entrypoints](../modules/entrypoints.md)
- [extraction_service](../modules/extraction_service.md)
- [knowledge_loader](../modules/knowledge_loader.md)
- [knowledge_storage_io](../modules/knowledge_storage_io.md)
- [maintenance_protocol](../modules/maintenance_protocol.md)
- [maintenance_status](../modules/maintenance_status.md)
- [plugins](../modules/plugins.md)
- [services_dependencies](../modules/services_dependencies.md)
- [source_retirement](../modules/source_retirement.md)
- [source_selection](../modules/source_selection.md)
- [source_snapshot](../modules/source_snapshot.md)
- [wiki_surface_index](../modules/wiki_surface_index.md)

## Behavior

Validates the source/wiki path boundaries, then checks a declared ordinary maintenance owner before selection and retirement helpers consume its metadata. Missing, invalid or mismatched authority raises a typed packet failure with the original maintenance cause chained locally. The fixed public diagnostic supplies recovery requirements without exposing raw metadata or host roots and without choosing a backup or identity.

Healthy captures continue through source selection, inventory, surface and knowledge qualification and the final unchanged-input checks. The operation is read-only. Required native evidence remains unsatisfied on authority refusal; packet `off` retains packet integrity obligations, while source-only tasks use their separate contract. No recovery, setup, marker initialization or history reconstruction is performed.
