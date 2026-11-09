# snapshot

**Entry point:** `publication_contracts._snapshot`
**Modules involved:** [concept_identity](../modules/concept_identity.md), [publication_contracts](../modules/publication_contracts.md), [sync_manifest](../modules/sync_manifest.md), [validation](../modules/validation.md), [wiki_surface](../modules/wiki_surface.md)

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `wiki_surface.iter_page_kinds`
2. `wiki_surface.PageKind`
3. `wiki_surface.canonical_path`
4. `validation.portable_path_key`
5. `validation.portable_path_key`
6. `wiki_surface.mcp_uri`
7. `concept_identity.validate_concept_uid`
8. `sync_manifest.ManifestPageSource.from_payload`

## Touches

- [concept_identity](../modules/concept_identity.md)
- [publication_contracts](../modules/publication_contracts.md)
- [sync_manifest](../modules/sync_manifest.md)
- [validation](../modules/validation.md)
- [wiki_surface](../modules/wiki_surface.md)

## Behavior

This workflow starts at `publication_contracts._snapshot`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
