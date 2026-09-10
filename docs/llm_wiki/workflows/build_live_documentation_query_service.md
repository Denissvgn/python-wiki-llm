# build_live_documentation_query_service

**Entry point:** `documentation_query_builder.build_live_documentation_query_service`
**Modules involved:** [documentation_queries](../modules/documentation_queries.md), [documentation_query_builder](../modules/documentation_query_builder.md), [source_selection](../modules/source_selection.md), [source_snapshot](../modules/source_snapshot.md)

> Build a live service using one operation-scoped extraction.

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `documentation_queries.DocumentationQueryError`
2. `source_selection.resolve_source_selection`
3. `documentation_queries.DocumentationQueryError`
4. `source_snapshot.capture_source_selection_inputs`
5. `documentation_queries.DocumentationQueryError`
6. `documentation_queries.DocumentationQueryError`
7. `documentation_queries.DocumentationQueryError`

## Touches

- [documentation_queries](../modules/documentation_queries.md)
- [documentation_query_builder](../modules/documentation_query_builder.md)
- [source_selection](../modules/source_selection.md)
- [source_snapshot](../modules/source_snapshot.md)

## Behavior

This workflow starts at `documentation_query_builder.build_live_documentation_query_service`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
