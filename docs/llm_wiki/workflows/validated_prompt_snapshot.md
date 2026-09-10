# validated_prompt_snapshot

**Entry point:** `generate_prompt_cmd._validated_prompt_snapshot`
**Modules involved:** [documentation_query_builder](../modules/documentation_query_builder.md), [generate_prompt_cmd](../modules/generate_prompt_cmd.md), [source_selection](../modules/source_selection.md), [source_snapshot](../modules/source_snapshot.md)

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `source_selection.resolve_source_selection`
2. `source_snapshot.capture_source_selection_inputs`
3. `documentation_query_builder.validate_live_query_source_selection`
4. `source_snapshot.build_source_snapshot`
5. `documentation_query_builder.validate_live_query_source_selection`

## Touches

- [documentation_query_builder](../modules/documentation_query_builder.md)
- [generate_prompt_cmd](../modules/generate_prompt_cmd.md)
- [source_selection](../modules/source_selection.md)
- [source_snapshot](../modules/source_snapshot.md)

## Behavior

This workflow starts at `generate_prompt_cmd._validated_prompt_snapshot`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
