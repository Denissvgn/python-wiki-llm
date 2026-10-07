# search_prevalidated_roots

**Entry point:** `search_service.search_prevalidated_roots`
**Modules involved:** [documentation_query_builder](../modules/documentation_query_builder.md), [io](../modules/io.md), [knowledge_storage_io](../modules/knowledge_storage_io.md), [search_discovery](../modules/search_discovery.md), [search_discovery_capture](../modules/search_discovery_capture.md), [search_service](../modules/search_service.md), [search_source](../modules/search_source.md), [source_selection](../modules/source_selection.md), [source_snapshot](../modules/source_snapshot.md), [workflow_profile](../modules/workflow_profile.md)

> Share capture/ranking while preserving trusted MCP configured-root boundaries.

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `source_selection.resolve_source_selection`
2. `source_snapshot.capture_source_selection_inputs`
3. `documentation_query_builder.validate_live_query_source_selection`
4. `source_snapshot.build_source_snapshot`
5. `documentation_query_builder.validate_live_query_source_selection`
6. `knowledge_storage_io.StorageReadSession`
7. `knowledge_storage_io.StorageReadSession`
8. `search_source.captured_manifest`
9. `source_selection.validate_persisted_source_selection_identity`
10. `io.decode_markdown_bytes`
11. `search_source.capture_source_index`
12. `search_discovery_capture.capture_discovery`
13. `search_discovery.enrich_search`
14. `workflow_profile.canonical_json`
15. `search_discovery.DiscoveryError`
16. `workflow_profile.canonical_json`
17. `knowledge_storage_io.StorageReadSession.recheck`
18. `knowledge_storage_io.StorageReadSession.recheck`
19. `source_snapshot.source_snapshot_matches_current_files`
20. `source_selection.validate_persisted_source_selection_identity`

## Touches

- [documentation_query_builder](../modules/documentation_query_builder.md)
- [io](../modules/io.md)
- [knowledge_storage_io](../modules/knowledge_storage_io.md)
- [search_discovery](../modules/search_discovery.md)
- [search_discovery_capture](../modules/search_discovery_capture.md)
- [search_service](../modules/search_service.md)
- [search_source](../modules/search_source.md)
- [source_selection](../modules/source_selection.md)
- [source_snapshot](../modules/source_snapshot.md)
- [workflow_profile](../modules/workflow_profile.md)

## Behavior

This workflow starts at `search_service.search_prevalidated_roots`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
