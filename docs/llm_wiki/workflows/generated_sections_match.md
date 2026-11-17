# generated_sections_match

**Entry point:** `sync_analysis_cache.generated_sections_match`
**Modules involved:** [canonical_json](../modules/canonical_json.md), [knowledge_storage_io](../modules/knowledge_storage_io.md), [section_ownership](../modules/section_ownership.md), [sync_analysis_cache](../modules/sync_analysis_cache.md)

> Allow prose edits; changing generated structure requires the ordinary path.

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `knowledge_storage_io.read_guarded`
2. `canonical_json.sha256_digest`
3. `section_ownership.observe_page_sections`

## Touches

- [canonical_json](../modules/canonical_json.md)
- [knowledge_storage_io](../modules/knowledge_storage_io.md)
- [section_ownership](../modules/section_ownership.md)
- [sync_analysis_cache](../modules/sync_analysis_cache.md)

## Behavior

This workflow starts at `sync_analysis_cache.generated_sections_match`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
