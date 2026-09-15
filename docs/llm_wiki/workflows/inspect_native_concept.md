# inspect_native_concept

**Entry point:** `native_inspection.inspect_native_concept`
**Modules involved:** [context_packet](../modules/context_packet.md), [documentation_queries](../modules/documentation_queries.md), [documentation_query_builder](../modules/documentation_query_builder.md), [knowledge_coverage](../modules/knowledge_coverage.md), [native_inspection](../modules/native_inspection.md)

> Compose existing queries, then check that their common inputs still hold.

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `context_packet.capture_context_read`
2. `documentation_query_builder.build_documentation_query_service_from_view`
3. `context_packet._wiki_anchor`
4. `documentation_query_builder.build_snapshot_documentation_query_service`
5. `knowledge_coverage.build_knowledge_coverage`
6. `documentation_queries.DocumentationQueryError`
7. `context_packet._assert_source_unchanged`
8. `context_packet._assert_wiki_unchanged`

## Touches

- [context_packet](../modules/context_packet.md)
- [documentation_queries](../modules/documentation_queries.md)
- [documentation_query_builder](../modules/documentation_query_builder.md)
- [knowledge_coverage](../modules/knowledge_coverage.md)
- [native_inspection](../modules/native_inspection.md)

## Behavior

This workflow starts at `native_inspection.inspect_native_concept`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
