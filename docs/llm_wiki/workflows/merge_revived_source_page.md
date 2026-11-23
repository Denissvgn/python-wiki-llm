# merge_revived_source_page

**Entry point:** `sync_runtime._merge_revived_source_page`
**Modules involved:** [canonical_json](../modules/canonical_json.md), [section_ownership](../modules/section_ownership.md), [source_retirement](../modules/source_retirement.md), [sync_generated_sections](../modules/sync_generated_sections.md), [sync_runtime](../modules/sync_runtime.md)

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `source_retirement.SourceRetirementError`
2. `canonical_json.sha256_digest`
3. `section_ownership.SemanticMergeResult`
4. `sync_generated_sections.repair_source_sections`

## Touches

- [canonical_json](../modules/canonical_json.md)
- [section_ownership](../modules/section_ownership.md)
- [source_retirement](../modules/source_retirement.md)
- [sync_generated_sections](../modules/sync_generated_sections.md)
- [sync_runtime](../modules/sync_runtime.md)

## Behavior

This workflow starts at `sync_runtime._merge_revived_source_page`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
