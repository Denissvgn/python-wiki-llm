# refresh_documentation_native_projection

**Entry point:** `documentation_native.refresh_documentation_native_projection`
**Modules involved:** [context_service](../modules/context_service.md), [documentation_native](../modules/documentation_native.md), [knowledge_orchestration](../modules/knowledge_orchestration.md), [sync_manifest](../modules/sync_manifest.md)

> Recompute the native trio without mutating canonical Markdown.

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `sync_manifest.SyncManifest.load`
2. `knowledge_orchestration.finalize_runtime_knowledge`
3. `knowledge_orchestration.RuntimeKnowledgeInputs`
4. `knowledge_orchestration.collect_runtime_repository_evidence`
5. `context_service._build_context_knowledge_view`

## Touches

- [context_service](../modules/context_service.md)
- [documentation_native](../modules/documentation_native.md)
- [knowledge_orchestration](../modules/knowledge_orchestration.md)
- [sync_manifest](../modules/sync_manifest.md)

## Behavior

This workflow starts at `documentation_native.refresh_documentation_native_projection`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
