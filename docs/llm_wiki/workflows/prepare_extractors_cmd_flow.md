# prepare_extractors_cmd_flow

**Entry point:** `prepare_extractors_cmd.run`
**Modules involved:** [config](../modules/config.md), [extractor_helpers](../modules/extractor_helpers.md), [prepare_extractors_cmd](../modules/prepare_extractors_cmd.md), [source_selection](../modules/source_selection.md), [source_snapshot](../modules/source_snapshot.md)

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `config.validate_source_root`
2. `source_selection.resolve_source_selection`
3. `source_snapshot.build_source_snapshot`
4. `extractor_helpers.resolve_helper_cache_root`
5. `extractor_helpers.prepare_helper`

## Touches

- [config](../modules/config.md)
- [extractor_helpers](../modules/extractor_helpers.md)
- [prepare_extractors_cmd](../modules/prepare_extractors_cmd.md)
- [source_selection](../modules/source_selection.md)
- [source_snapshot](../modules/source_snapshot.md)

## Behavior

This workflow starts at `prepare_extractors_cmd.run`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
