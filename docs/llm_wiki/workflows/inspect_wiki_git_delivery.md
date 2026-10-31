# inspect_wiki_git_delivery

**Entry point:** `wiki_git_delivery.inspect_wiki_git_delivery`
**Modules involved:** [knowledge_storage](../modules/knowledge_storage.md), [knowledge_storage_io](../modules/knowledge_storage_io.md), [knowledge_storage_lifecycle](../modules/knowledge_storage_lifecycle.md), [wiki_git_delivery](../modules/wiki_git_delivery.md), [wiki_git_policy](../modules/wiki_git_policy.md)

> Check every required native file; an explicit staged check gates handoff.

Ignore policy alone never proves index completeness. Markdown newline
normalization is allowed; native commitments and binary objects must retain
exact bytes. No source inventory, setup, Git writes or network calls occur.

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `knowledge_storage.KnowledgeStorageError`
2. `knowledge_storage_io._absolute_path`
3. `wiki_git_policy.classify_wiki_git_policy`
4. `knowledge_storage_lifecycle._committed_inputs`
5. `knowledge_storage.KnowledgeStorageError`
6. `knowledge_storage.KnowledgeStorageError`

## Touches

- [knowledge_storage](../modules/knowledge_storage.md)
- [knowledge_storage_io](../modules/knowledge_storage_io.md)
- [knowledge_storage_lifecycle](../modules/knowledge_storage_lifecycle.md)
- [wiki_git_delivery](../modules/wiki_git_delivery.md)
- [wiki_git_policy](../modules/wiki_git_policy.md)

## Behavior

This workflow starts at `wiki_git_delivery.inspect_wiki_git_delivery`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
