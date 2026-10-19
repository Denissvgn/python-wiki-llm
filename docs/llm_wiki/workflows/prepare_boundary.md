# prepare_boundary

**Entry point:** `scoped_sync_repair.prepare_boundary`
**Modules involved:** [analysis_compatibility](../modules/analysis_compatibility.md), [knowledge_orchestration](../modules/knowledge_orchestration.md), [knowledge_reuse](../modules/knowledge_reuse.md), [knowledge_storage](../modules/knowledge_storage.md), [scoped_sync_repair](../modules/scoped_sync_repair.md)

> Accept an adopted unchanged-source repair after complete revalidation.

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `knowledge_reuse.wiki_input_hashes`
2. `knowledge_orchestration.build_runtime_live_evaluation`
3. `knowledge_orchestration.RuntimeLiveEvaluationInputs`
4. `knowledge_orchestration.runtime_generation_options`
5. `knowledge_storage.canonical_bytes`
6. `knowledge_storage.canonical_bytes`
7. `analysis_compatibility.component_record`
8. `knowledge_orchestration.runtime_source_snapshot_hash`
9. `knowledge_reuse.implementation_hash`

## Touches

- [analysis_compatibility](../modules/analysis_compatibility.md)
- [knowledge_orchestration](../modules/knowledge_orchestration.md)
- [knowledge_reuse](../modules/knowledge_reuse.md)
- [knowledge_storage](../modules/knowledge_storage.md)
- [scoped_sync_repair](../modules/scoped_sync_repair.md)

## Behavior

This workflow accepts a complete adopted snapshot with unchanged source, selection and generation policy. It requires valid fresh evidence for the requested invalid module/entity coordinates and reproduces every retained known source observation. Only requested generated repairs can accompany that evidence update; mixed source edits, missing pages, pruning and wider surface changes need full review.

A producer transition uses complete current built-in commitments and preserves opaque annotations and component selection. The boundary pins the package, source, wiki and actual helper/runtime inputs for later isolated and live checks. Versions alone cannot establish compatibility, and preparation cannot acknowledge review or create missing authority.
