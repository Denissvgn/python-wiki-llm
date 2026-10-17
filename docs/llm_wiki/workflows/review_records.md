# review_records

**Entry point:** `knowledge_storage_diagnostics._review_records`
**Modules involved:** [knowledge_index](../modules/knowledge_index.md), [knowledge_loader](../modules/knowledge_loader.md), [knowledge_storage](../modules/knowledge_storage.md), [knowledge_storage_diagnostics](../modules/knowledge_storage_diagnostics.md), [knowledge_storage_io](../modules/knowledge_storage_io.md)

> Logical review keys preserve duplicates and avoid physical pack identities.

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `knowledge_loader.load_knowledge_state`
2. `knowledge_storage.KnowledgeStorageError`
3. `knowledge_index._model_to_payload`
4. `knowledge_storage.digest`
5. `knowledge_storage.canonical_bytes`
6. `knowledge_storage_io._absolute_path`

## Touches

- [knowledge_index](../modules/knowledge_index.md)
- [knowledge_loader](../modules/knowledge_loader.md)
- [knowledge_storage](../modules/knowledge_storage.md)
- [knowledge_storage_diagnostics](../modules/knowledge_storage_diagnostics.md)
- [knowledge_storage_io](../modules/knowledge_storage_io.md)

## Behavior

Loads a fully validated committed snapshot and assigns storage-independent review keys to concepts, relationships, graph edges, section ownership and remaining metadata/extensions. Duplicate relationships receive distinct occurrence keys. It returns these values with the native root location, validated artifact commitments and manifest basis, which the outer review binds to its operation and canonical ordering. Output pages and exact-record chunks retain hashes and explicit omissions without converting snapshot validity into live-source freshness.
