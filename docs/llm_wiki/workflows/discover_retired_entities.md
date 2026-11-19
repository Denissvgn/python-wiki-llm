# discover_retired_entities

**Entry point:** `source_retirement.discover_retired_entities`
**Modules involved:** [integrations](../modules/integrations.md), [source_retirement](../modules/source_retirement.md), [sync_manifest](../modules/sync_manifest.md), [validation](../modules/validation.md), [wiki_surface](../modules/wiki_surface.md)

> Plan fresh removals and recover exact persisted, previously unmarked owners.

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `integrations.attributes`
2. `sync_manifest.ManifestPageSource`
3. `wiki_surface.canonical_path`
4. `validation.portable_path_key`

## Touches

- [integrations](../modules/integrations.md)
- [source_retirement](../modules/source_retirement.md)
- [sync_manifest](../modules/sync_manifest.md)
- [validation](../modules/validation.md)
- [wiki_surface](../modules/wiki_surface.md)

## Behavior

Reconciles authoritative recorded page ownership with the current documentable inventory. Fresh absent members and previously unmarked tombstones can become planned history. Unmapped pages never acquire inferred identity. Ambiguous duplicate removal fails custody checks before any page write.
