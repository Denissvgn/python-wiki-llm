# prepare_boundary

**Entry point:** `scoped_sync_repair.prepare_boundary`
**Modules involved:** [analysis_compatibility](../modules/analysis_compatibility.md), [knowledge_orchestration](../modules/knowledge_orchestration.md), [knowledge_reuse](../modules/knowledge_reuse.md), [scoped_sync_repair](../modules/scoped_sync_repair.md)

> Accept only an adopted, coherent, stable-producer unchanged-source repair.

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `knowledge_reuse.wiki_input_hashes`
2. `knowledge_orchestration.build_runtime_live_evaluation`
3. `knowledge_orchestration.RuntimeLiveEvaluationInputs`
4. `knowledge_orchestration.runtime_generation_options`
5. `analysis_compatibility.component_record`
6. `knowledge_reuse.implementation_hash`

## Touches

- [analysis_compatibility](../modules/analysis_compatibility.md)
- [knowledge_orchestration](../modules/knowledge_orchestration.md)
- [knowledge_reuse](../modules/knowledge_reuse.md)
- [scoped_sync_repair](../modules/scoped_sync_repair.md)

## Behavior

This workflow starts at `scoped_sync_repair.prepare_boundary`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
