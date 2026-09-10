# finalize_bootstrap_artifacts

**Entry point:** `bootstrap_runtime._finalize_bootstrap_artifacts`
**Modules involved:** [bootstrap_runtime](../modules/bootstrap_runtime.md), [knowledge_orchestration](../modules/knowledge_orchestration.md), [knowledge_reuse](../modules/knowledge_reuse.md), [wiki_surface_index](../modules/wiki_surface_index.md)

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `wiki_surface_index.evaluate_surface_index`
2. `knowledge_orchestration.collect_runtime_repository_evidence`
3. `knowledge_orchestration.runtime_generation_options`
4. `knowledge_reuse.build_reuse_input_basis`
5. `knowledge_orchestration.finalize_runtime_knowledge`
6. `knowledge_orchestration.RuntimeKnowledgeInputs`

## Touches

- [bootstrap_runtime](../modules/bootstrap_runtime.md)
- [knowledge_orchestration](../modules/knowledge_orchestration.md)
- [knowledge_reuse](../modules/knowledge_reuse.md)
- [wiki_surface_index](../modules/wiki_surface_index.md)

## Behavior

Evaluates the completed Markdown tree into a canonical surface index, combines
it with the exact source snapshot, page maps, repository identity, generation
options, plugin producers, and graph observations, then calls the shared
runtime finalizer. The finalizer commits a mutually consistent surface index,
knowledge index, envelope, and sync manifest. Each artifact write is folded
back into bootstrap's created, updated, or skipped accounting.
