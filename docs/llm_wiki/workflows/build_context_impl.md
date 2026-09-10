# build_context_impl

**Entry point:** `context_service._build_context_impl`
**Modules involved:** [config](../modules/config.md), [context_service](../modules/context_service.md), [documentation_query_builder](../modules/documentation_query_builder.md), [source_selection](../modules/source_selection.md), [source_snapshot](../modules/source_snapshot.md)

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `config.validate_source_root`
2. `config.validate_path`
3. `source_selection.resolve_source_selection`
4. `source_snapshot.capture_source_selection_inputs`
5. `documentation_query_builder.validate_live_query_source_selection`
6. `source_snapshot.build_source_snapshot`
7. `source_selection.resolve_source_selection`
8. `documentation_query_builder.validate_live_query_source_selection`

## Touches

- [config](../modules/config.md)
- [context_service](../modules/context_service.md)
- [documentation_query_builder](../modules/documentation_query_builder.md)
- [source_selection](../modules/source_selection.md)
- [source_snapshot](../modules/source_snapshot.md)

## Behavior

This workflow starts at `context_service._build_context_impl`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
