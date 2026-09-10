# validate_live_query_source_selection

**Entry point:** `documentation_query_builder.validate_live_query_source_selection`
**Modules involved:** [documentation_queries](../modules/documentation_queries.md), [documentation_query_builder](../modules/documentation_query_builder.md), [source_selection](../modules/source_selection.md), [sync_manifest](../modules/sync_manifest.md)

> Require a live query profile to match the persisted wiki boundary.

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `sync_manifest.SyncManifest.load`
2. `documentation_queries.DocumentationQueryError`
3. `documentation_queries.DocumentationQueryError`
4. `documentation_queries.DocumentationQueryError`
5. `source_selection.validate_persisted_source_selection_identity`
6. `source_selection.validate_persisted_source_selection_identity`
7. `documentation_queries.DocumentationQueryError`

## Touches

- [documentation_queries](../modules/documentation_queries.md)
- [documentation_query_builder](../modules/documentation_query_builder.md)
- [source_selection](../modules/source_selection.md)
- [sync_manifest](../modules/sync_manifest.md)

## Behavior

This workflow starts at `documentation_query_builder.validate_live_query_source_selection`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
