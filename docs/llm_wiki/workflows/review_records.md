# review_records

**Entry point:** `knowledge_storage_diagnostics._review_records`
**Modules involved:** [knowledge_index](../modules/knowledge_index.md), [knowledge_loader](../modules/knowledge_loader.md), [knowledge_storage](../modules/knowledge_storage.md), [knowledge_storage_diagnostics](../modules/knowledge_storage_diagnostics.md)

> Logical review keys preserve duplicates and avoid physical pack identities.

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `knowledge_loader.load_knowledge_state`
2. `knowledge_storage.KnowledgeStorageError`
3. `knowledge_index._model_to_payload`
4. `knowledge_storage.digest`
5. `knowledge_storage.canonical_bytes`

## Touches

- [knowledge_index](../modules/knowledge_index.md)
- [knowledge_loader](../modules/knowledge_loader.md)
- [knowledge_storage](../modules/knowledge_storage.md)
- [knowledge_storage_diagnostics](../modules/knowledge_storage_diagnostics.md)

## Behavior

Loads a fully validated committed snapshot and assigns storage-independent review keys to concepts, relationships, graph edges, section ownership and remaining metadata/extensions. Duplicate relationships receive distinct occurrence keys. The outer review operation compares these logical values and reports bounded output with hashes and explicit omissions.
