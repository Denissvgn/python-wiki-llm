# evaluate_knowledge_freshness

**Entry point:** `knowledge_freshness.evaluate_knowledge_freshness`
**Modules involved:** [knowledge_artifacts](../modules/knowledge_artifacts.md), [knowledge_freshness](../modules/knowledge_freshness.md), [knowledge_model](../modules/knowledge_model.md), [source_retirement](../modules/source_retirement.md)

> Evaluate concepts; retirement requires native validation or manifest context.

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `knowledge_artifacts.require_validated_artifacts`
2. `knowledge_model.parse_knowledge_index`
3. `knowledge_model._knowledge_index_to_payload_unchecked`
4. `knowledge_model.parse_knowledge_index`
5. `source_retirement.qualified_retired_entity_locators`

## Touches

- [knowledge_artifacts](../modules/knowledge_artifacts.md)
- [knowledge_freshness](../modules/knowledge_freshness.md)
- [knowledge_model](../modules/knowledge_model.md)
- [source_retirement](../modules/source_retirement.md)

## Behavior

This workflow starts at `knowledge_freshness.evaluate_knowledge_freshness`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
