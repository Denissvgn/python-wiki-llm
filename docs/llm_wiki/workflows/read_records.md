# read_records

**Entry point:** `historical_sources.read_records`
**Modules involved:** [historical_sources](../modules/historical_sources.md), [knowledge_evidence](../modules/knowledge_evidence.md), [sync_manifest](../modules/sync_manifest.md), [validation](../modules/validation.md), [wiki_surface](../modules/wiki_surface.md)

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `sync_manifest.ManifestPageSource.from_payload`
2. `sync_manifest.ManifestEvidenceBaseline.from_payload`
3. `wiki_surface.canonical_path`
4. `validation.portable_path_key`
5. `knowledge_evidence.is_valid_sha256`
6. `validation.portable_path_key`

## Touches

- [historical_sources](../modules/historical_sources.md)
- [knowledge_evidence](../modules/knowledge_evidence.md)
- [sync_manifest](../modules/sync_manifest.md)
- [validation](../modules/validation.md)
- [wiki_surface](../modules/wiki_surface.md)

## Behavior

This workflow starts at `historical_sources.read_records`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
