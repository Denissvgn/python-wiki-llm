# DocumentationGraphQueryService__build_knowledge_indexes

**Entry point:** `documentation_queries.DocumentationGraphQueryService._build_knowledge_indexes`
**Modules involved:** [documentation_queries](../modules/documentation_queries.md), [immutable](../modules/immutable.md), [knowledge_consumption](../modules/knowledge_consumption.md), [knowledge_model](../modules/knowledge_model.md), [knowledge_observability](../modules/knowledge_observability.md), [query_request_format](../modules/query_request_format.md)

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `knowledge_observability.knowledge_status_payload`
2. `query_request_format.DocumentationQueryError`
3. `query_request_format.DocumentationQueryError`
4. `query_request_format.DocumentationQueryError`
5. `knowledge_observability.knowledge_status_payload`
6. `query_request_format.DocumentationQueryError`
7. `query_request_format.DocumentationQueryError`
8. `knowledge_consumption._validated_artifacts_for_view`
9. `immutable.freeze`
10. `knowledge_model.knowledge_index_to_payload`
11. `query_request_format.DocumentationQueryError`

## Touches

- [documentation_queries](../modules/documentation_queries.md)
- [immutable](../modules/immutable.md)
- [knowledge_consumption](../modules/knowledge_consumption.md)
- [knowledge_model](../modules/knowledge_model.md)
- [knowledge_observability](../modules/knowledge_observability.md)
- [query_request_format](../modules/query_request_format.md)

## Behavior

This workflow starts at `documentation_queries.DocumentationGraphQueryService._build_knowledge_indexes`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
