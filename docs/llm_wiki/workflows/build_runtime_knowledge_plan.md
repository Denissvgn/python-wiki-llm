# build_runtime_knowledge_plan

**Entry point:** `knowledge_orchestration.build_runtime_knowledge_plan`
**Modules involved:** [infrastructure_sync](../modules/infrastructure_sync.md), [knowledge_envelope](../modules/knowledge_envelope.md), [knowledge_generation](../modules/knowledge_generation.md), [knowledge_orchestration](../modules/knowledge_orchestration.md), [source_selection](../modules/source_selection.md)

> Build a commit plan from one command's already evaluated run state.

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `source_selection.with_source_selection_generation_input`
2. `knowledge_generation.KnowledgeGenerationError`
3. `infrastructure_sync.infrastructure_evidence_by_page`
4. `knowledge_generation.KnowledgeGenerationInputs`
5. `knowledge_envelope.ProducerComponentInput`

## Touches

- [infrastructure_sync](../modules/infrastructure_sync.md)
- [knowledge_envelope](../modules/knowledge_envelope.md)
- [knowledge_generation](../modules/knowledge_generation.md)
- [knowledge_orchestration](../modules/knowledge_orchestration.md)
- [source_selection](../modules/source_selection.md)

## Behavior

This workflow starts at `knowledge_orchestration.build_runtime_knowledge_plan`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
