# impact_query

**Entry point:** `api._impact_query`
**Modules involved:** [api](../modules/api.md), [config](../modules/config.md), [documentation_query_builder](../modules/documentation_query_builder.md), [source_selection](../modules/source_selection.md)

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `documentation_query_builder.normalize_supplied_paths`
2. `documentation_query_builder.supplied_paths_from_unified_diff`
3. `documentation_query_builder.normalize_supplied_paths`
4. `config.validate_source_root`
5. `source_selection.resolve_source_selection`
6. `source_selection.path_is_selected`
7. `documentation_query_builder.build_live_documentation_query_service`
8. `documentation_query_builder.build_snapshot_documentation_query_service`

## Touches

- [api](../modules/api.md)
- [config](../modules/config.md)
- [documentation_query_builder](../modules/documentation_query_builder.md)
- [source_selection](../modules/source_selection.md)

## Behavior

This workflow starts at `api._impact_query`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
