# read_entity_retirement_state

**Entry point:** `source_retirement.read_entity_retirement_state`
**Modules involved:** [source_retirement](../modules/source_retirement.md), [sync_manifest](../modules/sync_manifest.md), [validation](../modules/validation.md), [wiki_surface](../modules/wiki_surface.md)

> Decode exact machine records without deriving ownership from Markdown.

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `wiki_surface.canonical_path`
2. `validation.portable_path_key`
3. `sync_manifest.ManifestPageSource.from_payload`

## Touches

- [source_retirement](../modules/source_retirement.md)
- [sync_manifest](../modules/sync_manifest.md)
- [validation](../modules/validation.md)
- [wiki_surface](../modules/wiki_surface.md)

## Behavior

Validates the versioned machine record, canonical paths, unique entity coordinates and optional recorded generated defaults. It decodes data only; no Markdown header can establish retirement authority.
