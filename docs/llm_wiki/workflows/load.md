# load

**Entry point:** `sync_analysis_cache.load`
**Modules involved:** [knowledge_envelope](../modules/knowledge_envelope.md), [knowledge_evidence](../modules/knowledge_evidence.md), [knowledge_storage_io](../modules/knowledge_storage_io.md), [progress](../modules/progress.md), [sync_analysis_cache](../modules/sync_analysis_cache.md)

> A cache is advisory; only exact prior committed content authorizes reuse.

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `knowledge_evidence.hash_json`
2. `knowledge_storage_io.read_guarded`
3. `knowledge_evidence.hash_json`
4. `knowledge_envelope.hash_inventory`
5. `progress.record_counts`

## Touches

- [knowledge_envelope](../modules/knowledge_envelope.md)
- [knowledge_evidence](../modules/knowledge_evidence.md)
- [knowledge_storage_io](../modules/knowledge_storage_io.md)
- [progress](../modules/progress.md)
- [sync_analysis_cache](../modules/sync_analysis_cache.md)

## Behavior

This workflow starts at `sync_analysis_cache.load`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
