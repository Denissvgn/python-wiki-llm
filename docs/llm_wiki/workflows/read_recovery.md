# read_recovery

**Entry point:** `knowledge_storage_lifecycle._read_recovery`
**Modules involved:** [canonical_json](../modules/canonical_json.md), [knowledge_storage](../modules/knowledge_storage.md), [knowledge_storage_io](../modules/knowledge_storage_io.md), [knowledge_storage_lifecycle](../modules/knowledge_storage_lifecycle.md)

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `knowledge_storage.decode_bytes`
2. `knowledge_storage_io.read_guarded`
3. `knowledge_storage.KnowledgeStorageError`
4. `knowledge_storage._hash`
5. `knowledge_storage._hash`
6. `knowledge_storage._hash`
7. `knowledge_storage._hash`
8. `knowledge_storage.KnowledgeStorageError`
9. `knowledge_storage.KnowledgeStorageError`
10. `knowledge_storage.KnowledgeStorageError`
11. `knowledge_storage.KnowledgeStorageError`
12. `knowledge_storage_io.read_guarded`
13. `canonical_json.sha256_digest`
14. `knowledge_storage.KnowledgeStorageError`
15. `knowledge_storage.KnowledgeStorageError`
16. `canonical_json.sha256_digest`
17. `knowledge_storage.KnowledgeStorageError`
18. `canonical_json.sha256_digest`
19. `knowledge_storage.KnowledgeStorageError`

## Touches

- [canonical_json](../modules/canonical_json.md)
- [knowledge_storage](../modules/knowledge_storage.md)
- [knowledge_storage_io](../modules/knowledge_storage_io.md)
- [knowledge_storage_lifecycle](../modules/knowledge_storage_lifecycle.md)

## Behavior

This workflow starts at `knowledge_storage_lifecycle._read_recovery`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
