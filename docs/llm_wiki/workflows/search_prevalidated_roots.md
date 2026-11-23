# search_prevalidated_roots

**Entry point:** `search_service.search_prevalidated_roots`
**Modules involved:** [canonical_json](../modules/canonical_json.md), [io](../modules/io.md), [knowledge_storage_io](../modules/knowledge_storage_io.md), [query_request_format](../modules/query_request_format.md), [search_discovery](../modules/search_discovery.md), [search_discovery_capture](../modules/search_discovery_capture.md), [search_service](../modules/search_service.md), [search_source](../modules/search_source.md), [source_selection](../modules/source_selection.md)

> Share capture/ranking while preserving trusted MCP configured-root boundaries.

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `source_selection.resolve_source_selection`
2. `query_request_format.validate_live_query_source_selection`
3. `query_request_format.validate_live_query_source_selection`
4. `knowledge_storage_io.StorageReadSession`
5. `knowledge_storage_io.StorageReadSession`
6. `search_source.captured_manifest`
7. `source_selection.validate_persisted_source_selection_identity`
8. `io.decode_markdown_bytes`
9. `search_source.capture_source_index`
10. `search_discovery_capture.capture_discovery`
11. `search_discovery.enrich_search`
12. `canonical_json.compact_line_bytes`
13. `search_discovery.DiscoveryError`
14. `canonical_json.compact_line_bytes`
15. `knowledge_storage_io.StorageReadSession.recheck`
16. `knowledge_storage_io.StorageReadSession.recheck`
17. `source_selection.validate_persisted_source_selection_identity`

## Touches

- [canonical_json](../modules/canonical_json.md)
- [io](../modules/io.md)
- [knowledge_storage_io](../modules/knowledge_storage_io.md)
- [query_request_format](../modules/query_request_format.md)
- [search_discovery](../modules/search_discovery.md)
- [search_discovery_capture](../modules/search_discovery_capture.md)
- [search_service](../modules/search_service.md)
- [search_source](../modules/search_source.md)
- [source_selection](../modules/source_selection.md)

## Behavior

This workflow starts at `search_service.search_prevalidated_roots`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
