# build_snapshot

**Entry point:** `publication_snapshot._build_snapshot`
**Modules involved:** [io](../modules/io.md), [knowledge_evidence](../modules/knowledge_evidence.md), [knowledge_model](../modules/knowledge_model.md), [knowledge_storage](../modules/knowledge_storage.md), [knowledge_storage_lifecycle](../modules/knowledge_storage_lifecycle.md), [maintenance_protocol](../modules/maintenance_protocol.md), [markdown_sections](../modules/markdown_sections.md), [publication_snapshot](../modules/publication_snapshot.md), [wiki_surface](../modules/wiki_surface.md)

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `knowledge_storage_lifecycle._committed_inputs`
2. `markdown_sections.parse_markdown_document`
3. `io.decode_markdown_bytes`
4. `knowledge_storage.KnowledgeStorageError`
5. `knowledge_evidence.sha256_bytes`
6. `wiki_surface.collect_wiki_pages`
7. `knowledge_storage.KnowledgeStorageError`
8. `maintenance_protocol.guard_maintenance_owner`
9. `knowledge_storage.KnowledgeStorageError`
10. `knowledge_evidence.hash_json`
11. `knowledge_model._bundle_to_payload`
12. `knowledge_evidence.sha256_bytes`
13. `knowledge_evidence.hash_json`

## Touches

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
