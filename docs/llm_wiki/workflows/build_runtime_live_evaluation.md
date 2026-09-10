# build_runtime_live_evaluation

**Entry point:** `knowledge_orchestration.build_runtime_live_evaluation`
**Modules involved:** [infrastructure_sync](../modules/infrastructure_sync.md), [knowledge_envelope](../modules/knowledge_envelope.md), [knowledge_freshness](../modules/knowledge_freshness.md), [knowledge_orchestration](../modules/knowledge_orchestration.md)

> Adapt one existing inventory/snapshot run to the freshness boundary.

The caller supplies reliably missing source paths explicitly. This adapter
performs no source discovery, extraction, filesystem read, or write.
The caller supplies the effective live generation policy. This adapter
commits that policy independently through the same canonical hashing path
as artifact generation.

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `knowledge_envelope.build_producer_record`
2. `knowledge_envelope.ProducerComponentInput`
3. `knowledge_freshness.LiveKnowledgeEvaluation`
4. `knowledge_envelope.hash_generation_options`
5. `infrastructure_sync.current_infrastructure_bases`

## Touches

- [infrastructure_sync](../modules/infrastructure_sync.md)
- [knowledge_envelope](../modules/knowledge_envelope.md)
- [knowledge_freshness](../modules/knowledge_freshness.md)
- [knowledge_orchestration](../modules/knowledge_orchestration.md)

## Behavior

This workflow starts at `knowledge_orchestration.build_runtime_live_evaluation`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
