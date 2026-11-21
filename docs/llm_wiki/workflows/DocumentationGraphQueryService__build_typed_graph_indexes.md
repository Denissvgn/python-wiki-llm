# DocumentationGraphQueryService__build_typed_graph_indexes

**Entry point:** `documentation_queries.DocumentationGraphQueryService._build_typed_graph_indexes`
**Modules involved:** [documentation_queries](../modules/documentation_queries.md), [immutable](../modules/immutable.md), [knowledge_artifacts](../modules/knowledge_artifacts.md), [knowledge_graph](../modules/knowledge_graph.md), [query_request_format](../modules/query_request_format.md)

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `query_request_format.DocumentationQueryError`
2. `immutable.freeze`
3. `knowledge_graph.typed_graph_from_knowledge_extensions`
4. `knowledge_artifacts.require_validated_artifacts`
5. `query_request_format.DocumentationQueryError`
6. `query_request_format.DocumentationQueryError`

## Touches

- [documentation_queries](../modules/documentation_queries.md)
- [immutable](../modules/immutable.md)
- [knowledge_artifacts](../modules/knowledge_artifacts.md)
- [knowledge_graph](../modules/knowledge_graph.md)
- [query_request_format](../modules/query_request_format.md)

## Behavior

This workflow starts at `documentation_queries.DocumentationGraphQueryService._build_typed_graph_indexes`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
