# check_prior_pages

**Entry point:** `historical_retirement.check_prior_pages`
**Modules involved:** [canonical_json](../modules/canonical_json.md), [historical_retirement](../modules/historical_retirement.md), [historical_sources](../modules/historical_sources.md), [knowledge_storage_io](../modules/knowledge_storage_io.md)

> Bind an imminent write to the exact enrollment preimages, including its index.

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `knowledge_storage_io.StorageReadSession`
2. `historical_sources.remove_bound_registry`
3. `historical_sources.page_matches`
4. `canonical_json.sha256_digest`
5. `historical_sources.committed_text`

## Touches

- [canonical_json](../modules/canonical_json.md)
- [historical_retirement](../modules/historical_retirement.md)
- [historical_sources](../modules/historical_sources.md)
- [knowledge_storage_io](../modules/knowledge_storage_io.md)

## Behavior

This workflow starts at `historical_retirement.check_prior_pages`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
