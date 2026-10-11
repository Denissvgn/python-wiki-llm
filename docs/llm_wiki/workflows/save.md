# save

**Entry point:** `sync_analysis_cache.save`
**Modules involved:** [io](../modules/io.md), [knowledge_evidence](../modules/knowledge_evidence.md), [runtime_output](../modules/runtime_output.md), [sync_analysis_cache](../modules/sync_analysis_cache.md)

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `io.first_unsafe_path_component`
2. `knowledge_evidence.canonical_json_bytes`
3. `io.write_bytes_atomic`
4. `runtime_output.warn`

## Touches

- [io](../modules/io.md)
- [knowledge_evidence](../modules/knowledge_evidence.md)
- [runtime_output](../modules/runtime_output.md)
- [sync_analysis_cache](../modules/sync_analysis_cache.md)

## Behavior

This workflow starts at `sync_analysis_cache.save`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
