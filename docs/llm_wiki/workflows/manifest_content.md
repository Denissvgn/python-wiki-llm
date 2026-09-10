# manifest_content

**Entry point:** `team._manifest_content`
**Modules involved:** [bootstrap_runtime](../modules/bootstrap_runtime.md), [source_selection](../modules/source_selection.md), [sync_manifest](../modules/sync_manifest.md), [team](../modules/team.md)

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `bootstrap_runtime.build_module_page_map`
2. `source_selection.with_source_selection_generation_input`
3. `sync_manifest.retained_concept_page_paths`
4. `sync_manifest.prune_manifest_for_source_selection`
5. `sync_manifest.SyncManifest.build_from_inventory`
6. `bootstrap_runtime.build_entity_page_map`
7. `bootstrap_runtime.build_entity_occurrence_page_map`

## Touches

- [bootstrap_runtime](../modules/bootstrap_runtime.md)
- [source_selection](../modules/source_selection.md)
- [sync_manifest](../modules/sync_manifest.md)
- [team](../modules/team.md)

## Behavior

This workflow starts at `team._manifest_content`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
