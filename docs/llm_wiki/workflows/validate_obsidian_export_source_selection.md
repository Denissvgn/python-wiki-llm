# validate_obsidian_export_source_selection

**Entry point:** `obsidian.validate_obsidian_export_source_selection`
**Modules involved:** [documentation_query_builder](../modules/documentation_query_builder.md), [obsidian](../modules/obsidian.md), [source_selection](../modules/source_selection.md), [source_snapshot](../modules/source_snapshot.md)

> Freeze and validate the live profile before any persisted wiki read.

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `source_selection.resolve_source_selection`
2. `source_snapshot.capture_source_selection_inputs`
3. `documentation_query_builder.validate_live_query_source_selection`
4. `source_snapshot.build_source_snapshot`
5. `documentation_query_builder.validate_live_query_source_selection`

## Touches

- [documentation_query_builder](../modules/documentation_query_builder.md)
- [obsidian](../modules/obsidian.md)
- [source_selection](../modules/source_selection.md)
- [source_snapshot](../modules/source_snapshot.md)

## Behavior

This workflow starts at `obsidian.validate_obsidian_export_source_selection`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
