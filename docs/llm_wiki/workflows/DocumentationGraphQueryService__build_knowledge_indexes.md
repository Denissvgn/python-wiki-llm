# DocumentationGraphQueryService__build_knowledge_indexes

**Entry point:** `documentation_queries.DocumentationGraphQueryService._build_knowledge_indexes`
**Modules involved:** [documentation_queries](../modules/documentation_queries.md), [immutable](../modules/immutable.md), [knowledge_consumption](../modules/knowledge_consumption.md), [knowledge_model](../modules/knowledge_model.md), [knowledge_observability](../modules/knowledge_observability.md)

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `knowledge_observability.knowledge_status_payload`
2. `knowledge_observability.knowledge_status_payload`
3. `knowledge_consumption._validated_artifacts_for_view`
4. `immutable.freeze`
5. `knowledge_model.knowledge_index_to_payload`

## Touches

- [documentation_queries](../modules/documentation_queries.md)
- [immutable](../modules/immutable.md)
- [knowledge_consumption](../modules/knowledge_consumption.md)
- [knowledge_model](../modules/knowledge_model.md)
- [knowledge_observability](../modules/knowledge_observability.md)

## Behavior

This workflow starts at `documentation_queries.DocumentationGraphQueryService._build_knowledge_indexes`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
