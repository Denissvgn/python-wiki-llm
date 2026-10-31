# DocumentationGraphQueryService__build_typed_graph_indexes

**Entry point:** `documentation_queries.DocumentationGraphQueryService._build_typed_graph_indexes`
**Modules involved:** [documentation_queries](../modules/documentation_queries.md), [immutable](../modules/immutable.md), [knowledge_artifacts](../modules/knowledge_artifacts.md), [knowledge_graph](../modules/knowledge_graph.md)

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `immutable.freeze`
2. `knowledge_graph.typed_graph_from_knowledge_extensions`
3. `knowledge_artifacts.require_validated_artifacts`

## Touches

- [documentation_queries](../modules/documentation_queries.md)
- [immutable](../modules/immutable.md)
- [knowledge_artifacts](../modules/knowledge_artifacts.md)
- [knowledge_graph](../modules/knowledge_graph.md)

## Behavior

This workflow starts at `documentation_queries.DocumentationGraphQueryService._build_typed_graph_indexes`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
