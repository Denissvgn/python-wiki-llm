# migrate_knowledge_storage

**Entry point:** `knowledge_storage_lifecycle._migrate_knowledge_storage`
**Modules involved:** [canonical_json](../modules/canonical_json.md), [knowledge_artifacts](../modules/knowledge_artifacts.md), [knowledge_storage](../modules/knowledge_storage.md), [knowledge_storage_io](../modules/knowledge_storage_io.md), [knowledge_storage_lifecycle](../modules/knowledge_storage_lifecycle.md)

> Explicitly adopt indexed storage, retaining verified recovery bytes outside the wiki.

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `knowledge_storage.KnowledgeStorageError`
2. `knowledge_storage.KnowledgeStorageError`
3. `knowledge_storage.KnowledgeStorageError`
4. `knowledge_storage_io._absolute_path`
5. `knowledge_artifacts.current_knowledge_format`
6. `knowledge_storage.KnowledgeStorageError`
7. `knowledge_storage.KnowledgeStorageError`
8. `knowledge_storage.KnowledgeStorageError`
9. `knowledge_artifacts.build_knowledge_commit_plan`
10. `canonical_json.sha256_digest`
11. `knowledge_artifacts.current_knowledge_format`
12. `canonical_json.sha256_digest`
13. `knowledge_storage.KnowledgeStorageError`
14. `knowledge_artifacts.commit_knowledge_artifacts`

## Touches

- [canonical_json](../modules/canonical_json.md)
- [knowledge_artifacts](../modules/knowledge_artifacts.md)
- [knowledge_storage](../modules/knowledge_storage.md)
- [knowledge_storage_io](../modules/knowledge_storage_io.md)
- [knowledge_storage_lifecycle](../modules/knowledge_storage_lifecycle.md)

## Behavior

Fully validates the committed snapshot, constructs the explicitly selected indexed profile and preserves an exact recovery copy outside the wiki before mutation. The owning commit publishes physical artifacts, root and manifest in order. Repeating an unchanged migration produces no writes. Authored Markdown and governance remain unchanged and are rechecked after publication.
