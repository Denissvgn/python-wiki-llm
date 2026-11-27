# selected_surface_pages

**Entry point:** `api._selected_surface_pages`
**Modules involved:** [api](../modules/api.md), [canonical_json](../modules/canonical_json.md), [documentation_queries](../modules/documentation_queries.md), [knowledge_artifacts](../modules/knowledge_artifacts.md), [knowledge_storage](../modules/knowledge_storage.md), [knowledge_storage_io](../modules/knowledge_storage_io.md)

> Read the surface index the selected generation commits to.

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `knowledge_storage_io.read_guarded`
2. `canonical_json.sha256_digest`
3. `knowledge_storage.KnowledgeStorageError`
4. `documentation_queries.surface_page_records`
5. `knowledge_artifacts.validate_surface_index_bytes`

## Touches

- [api](../modules/api.md)
- [canonical_json](../modules/canonical_json.md)
- [documentation_queries](../modules/documentation_queries.md)
- [knowledge_artifacts](../modules/knowledge_artifacts.md)
- [knowledge_storage](../modules/knowledge_storage.md)
- [knowledge_storage_io](../modules/knowledge_storage_io.md)

## Behavior

This workflow starts at `api._selected_surface_pages`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
