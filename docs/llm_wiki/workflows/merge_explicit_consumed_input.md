# merge_explicit_consumed_input

**Entry point:** `knowledge_orchestration._merge_explicit_consumed_input`
**Modules involved:** [knowledge_envelope](../modules/knowledge_envelope.md), [knowledge_evidence](../modules/knowledge_evidence.md), [knowledge_generation](../modules/knowledge_generation.md), [knowledge_orchestration](../modules/knowledge_orchestration.md)

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `knowledge_generation.KnowledgeGenerationError`
2. `knowledge_generation.KnowledgeGenerationError`
3. `knowledge_evidence.is_valid_sha256`
4. `knowledge_generation.KnowledgeGenerationError`
5. `knowledge_generation.KnowledgeGenerationError`
6. `knowledge_envelope.ConsumedInput`

## Touches

- [knowledge_envelope](../modules/knowledge_envelope.md)
- [knowledge_evidence](../modules/knowledge_evidence.md)
- [knowledge_generation](../modules/knowledge_generation.md)
- [knowledge_orchestration](../modules/knowledge_orchestration.md)

## Behavior

This workflow starts at `knowledge_orchestration._merge_explicit_consumed_input`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
