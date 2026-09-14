# build_live_documentation_query_service

**Entry point:** `documentation_query_builder.build_live_documentation_query_service`
**Modules involved:** [context_packet](../modules/context_packet.md), [documentation_queries](../modules/documentation_queries.md), [documentation_query_builder](../modules/documentation_query_builder.md), [source_selection](../modules/source_selection.md), [source_snapshot](../modules/source_snapshot.md)

> Build a live service using one operation-scoped extraction.

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `documentation_queries.DocumentationQueryError`
2. `documentation_queries.DocumentationQueryError`
3. `source_selection.resolve_source_selection`
4. `documentation_queries.DocumentationQueryError`
5. `source_snapshot.capture_source_selection_inputs`
6. `context_packet._source_anchor`
7. `context_packet._wiki_anchor`
8. `documentation_queries.DocumentationQueryError`
9. `documentation_queries.DocumentationQueryError`
10. `documentation_queries.DocumentationQueryError`
11. `context_packet._assert_source_unchanged`
12. `context_packet._assert_wiki_unchanged`

## Touches

- [context_packet](../modules/context_packet.md)
- [documentation_queries](../modules/documentation_queries.md)
- [documentation_query_builder](../modules/documentation_query_builder.md)
- [source_selection](../modules/source_selection.md)
- [source_snapshot](../modules/source_snapshot.md)

## Behavior

This workflow starts at `documentation_query_builder.build_live_documentation_query_service`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
