# migrate_knowledge_storage

**Entry point:** `knowledge_storage_lifecycle.migrate_knowledge_storage`
**Modules involved:** [knowledge_artifacts](../modules/knowledge_artifacts.md), [knowledge_storage](../modules/knowledge_storage.md), [knowledge_storage_io](../modules/knowledge_storage_io.md), [knowledge_storage_lifecycle](../modules/knowledge_storage_lifecycle.md)

> Explicitly adopt v2, retaining verified recovery bytes outside the wiki.

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `knowledge_storage.KnowledgeStorageError`
2. `knowledge_storage_io._absolute_path`
3. `knowledge_artifacts.build_knowledge_commit_plan`
4. `knowledge_storage.digest`
5. `knowledge_artifacts.current_knowledge_format`
6. `knowledge_storage.digest`
7. `knowledge_storage.KnowledgeStorageError`
8. `knowledge_artifacts.commit_knowledge_artifacts`

## Touches

- [knowledge_artifacts](../modules/knowledge_artifacts.md)
- [knowledge_storage](../modules/knowledge_storage.md)
- [knowledge_storage_io](../modules/knowledge_storage_io.md)
- [knowledge_storage_lifecycle](../modules/knowledge_storage_lifecycle.md)

## Behavior

Validates the original committed generation, plans an equivalent sharded representation and preserves verified recovery bytes outside the wiki. Apply rechecks original inputs before the manifest-last commit and confirms that authored authority remains unchanged. A preview writes nothing and a repeat migration is idempotent.
