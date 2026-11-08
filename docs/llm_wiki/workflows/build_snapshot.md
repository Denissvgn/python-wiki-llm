# build_snapshot

**Entry point:** `publication_snapshot._build_snapshot`
**Modules involved:** [documentation_native](../modules/documentation_native.md), [helper_runtime](../modules/helper_runtime.md), [io](../modules/io.md), [knowledge_evidence](../modules/knowledge_evidence.md), [knowledge_model](../modules/knowledge_model.md), [knowledge_storage](../modules/knowledge_storage.md), [knowledge_storage_lifecycle](../modules/knowledge_storage_lifecycle.md), [maintenance_protocol](../modules/maintenance_protocol.md), [markdown_sections](../modules/markdown_sections.md), [publication_snapshot](../modules/publication_snapshot.md), [wiki_surface](../modules/wiki_surface.md)

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `knowledge_storage_lifecycle._committed_inputs`
2. `helper_runtime.helper_operation`
3. `documentation_native.evaluate_documentation_native_freshness`
4. `markdown_sections.parse_markdown_document`
5. `io.decode_markdown_bytes`
6. `knowledge_storage.KnowledgeStorageError`
7. `knowledge_storage.KnowledgeStorageError`
8. `knowledge_evidence.sha256_bytes`
9. `knowledge_evidence.sha256_bytes`
10. `knowledge_storage.KnowledgeStorageError`
11. `wiki_surface.collect_wiki_pages`
12. `knowledge_storage.KnowledgeStorageError`
13. `maintenance_protocol.guard_maintenance_owner`
14. `knowledge_storage.KnowledgeStorageError`
15. `knowledge_evidence.hash_json`
16. `knowledge_model._bundle_to_payload`
17. `knowledge_evidence.sha256_bytes`
18. `knowledge_evidence.hash_json`

## Touches

- [documentation_native](../modules/documentation_native.md)
- [helper_runtime](../modules/helper_runtime.md)
- [io](../modules/io.md)
- [knowledge_evidence](../modules/knowledge_evidence.md)
- [knowledge_model](../modules/knowledge_model.md)
- [knowledge_storage](../modules/knowledge_storage.md)
- [knowledge_storage_lifecycle](../modules/knowledge_storage_lifecycle.md)
- [maintenance_protocol](../modules/maintenance_protocol.md)
- [markdown_sections](../modules/markdown_sections.md)
- [publication_snapshot](../modules/publication_snapshot.md)
- [wiki_surface](../modules/wiki_surface.md)

## Behavior

This workflow starts at `publication_snapshot._build_snapshot`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
