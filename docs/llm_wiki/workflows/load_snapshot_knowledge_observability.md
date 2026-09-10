# load_snapshot_knowledge_observability

**Entry point:** `knowledge_observability.load_snapshot_knowledge_observability`
**Modules involved:** [knowledge_consumption](../modules/knowledge_consumption.md), [knowledge_loader](../modules/knowledge_loader.md), [knowledge_observability](../modules/knowledge_observability.md), [source_selection](../modules/source_selection.md), [source_snapshot](../modules/source_snapshot.md), [sync_manifest](../modules/sync_manifest.md), [wiki_surface_index](../modules/wiki_surface_index.md)

> Load status without extraction while checking current selection identity.

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `source_selection.resolve_source_selection`
2. `source_snapshot.capture_source_selection_inputs`
3. `sync_manifest.SyncManifest.load`
4. `source_selection.validate_persisted_source_selection_identity`
5. `source_snapshot.build_source_snapshot`
6. `knowledge_consumption.build_knowledge_read_view`
7. `knowledge_loader.KnowledgeLoadResult`
8. `wiki_surface_index.evaluate_surface_index`
9. `knowledge_loader.load_knowledge_state`
10. `knowledge_consumption.build_knowledge_read_view`

## Touches

- [knowledge_consumption](../modules/knowledge_consumption.md)
- [knowledge_loader](../modules/knowledge_loader.md)
- [knowledge_observability](../modules/knowledge_observability.md)
- [source_selection](../modules/source_selection.md)
- [source_snapshot](../modules/source_snapshot.md)
- [sync_manifest](../modules/sync_manifest.md)
- [wiki_surface_index](../modules/wiki_surface_index.md)

## Behavior

This workflow starts at `knowledge_observability.load_snapshot_knowledge_observability`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
