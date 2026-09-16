# search_wiki

**Entry point:** `search_service.search_wiki`
**Modules involved:** [config](../modules/config.md), [documentation_query_builder](../modules/documentation_query_builder.md), [search_service](../modules/search_service.md), [source_selection](../modules/source_selection.md), [source_snapshot](../modules/source_snapshot.md)

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `config.validate_source_root`
2. `config.validate_path`
3. `source_selection.resolve_source_selection`
4. `source_snapshot.capture_source_selection_inputs`
5. `documentation_query_builder.validate_live_query_source_selection`
6. `source_snapshot.build_source_snapshot`
7. `documentation_query_builder.validate_live_query_source_selection`

## Touches

- [config](../modules/config.md)
- [documentation_query_builder](../modules/documentation_query_builder.md)
- [search_service](../modules/search_service.md)
- [source_selection](../modules/source_selection.md)
- [source_snapshot](../modules/source_snapshot.md)

## Behavior

This workflow starts at `search_service.search_wiki`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
