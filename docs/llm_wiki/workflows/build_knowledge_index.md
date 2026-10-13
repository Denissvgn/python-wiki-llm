# build_knowledge_index

**Entry point:** `knowledge_index.build_knowledge_index`
**Modules involved:** [immutable](../modules/immutable.md), [knowledge_index](../modules/knowledge_index.md), [knowledge_model](../modules/knowledge_model.md), [progress](../modules/progress.md)

> Build one deterministic v1 knowledge index without performing I/O.

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `knowledge_model.KnowledgeIndex`
2. `progress.record_counts`
3. `immutable.freeze`

## Touches

- [immutable](../modules/immutable.md)
- [knowledge_index](../modules/knowledge_index.md)
- [knowledge_model](../modules/knowledge_model.md)
- [progress](../modules/progress.md)

## Behavior

This workflow starts at `knowledge_index.build_knowledge_index`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
