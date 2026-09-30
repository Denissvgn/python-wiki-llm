# prior_ownership

**Entry point:** `sync_transitions._prior_ownership`
**Modules involved:** [bootstrap_runtime](../modules/bootstrap_runtime.md), [sync_analysis](../modules/sync_analysis.md), [sync_manifest](../modules/sync_manifest.md), [sync_transitions](../modules/sync_transitions.md)

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `sync_analysis._recorded_entity_pages`
2. `sync_manifest.ManifestPageSource`
3. `sync_manifest.ManifestPageSource`
4. `sync_manifest.ManifestPageSource`
5. `sync_manifest.ManifestPageSource`
6. `bootstrap_runtime._module_name_from_path`

## Touches

- [bootstrap_runtime](../modules/bootstrap_runtime.md)
- [sync_analysis](../modules/sync_analysis.md)
- [sync_manifest](../modules/sync_manifest.md)
- [sync_transitions](../modules/sync_transitions.md)

## Behavior

This workflow starts at `sync_transitions._prior_ownership`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
