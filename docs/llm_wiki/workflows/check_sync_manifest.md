# check_sync_manifest

**Entry point:** `lint_service._check_sync_manifest`
**Modules involved:** [extraction_service](../modules/extraction_service.md), [lint_service](../modules/lint_service.md), [source_selection](../modules/source_selection.md), [sync_analysis](../modules/sync_analysis.md), [sync_manifest](../modules/sync_manifest.md), [wiki_lifecycle](../modules/wiki_lifecycle.md)

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `sync_manifest.SyncManifest.load`
2. `wiki_lifecycle.classify_wiki_lifecycle`
3. `wiki_lifecycle.bootstrap_guidance`
4. `wiki_lifecycle.sync_guidance`
5. `wiki_lifecycle.migration_guidance`
6. `extraction_service.get_inventory_result`
7. `source_selection.validate_persisted_source_selection_identity`
8. `sync_analysis.compute_sync_diff`

## Touches

- [extraction_service](../modules/extraction_service.md)
- [lint_service](../modules/lint_service.md)
- [source_selection](../modules/source_selection.md)
- [sync_analysis](../modules/sync_analysis.md)
- [sync_manifest](../modules/sync_manifest.md)
- [wiki_lifecycle](../modules/wiki_lifecycle.md)

## Behavior

This workflow starts at `lint_service._check_sync_manifest`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
