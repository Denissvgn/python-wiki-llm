# build_context_knowledge_view

**Entry point:** `context_service._build_context_knowledge_view`
**Modules involved:** [context_service](../modules/context_service.md), [extraction_service](../modules/extraction_service.md), [knowledge_consumption](../modules/knowledge_consumption.md), [wiki_surface_index](../modules/wiki_surface_index.md)

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `knowledge_consumption.KnowledgeReadView`
2. `wiki_surface_index.SurfaceIndexEvaluation`
3. `extraction_service.InventoryResult`

## Touches

- [context_service](../modules/context_service.md)
- [extraction_service](../modules/extraction_service.md)
- [knowledge_consumption](../modules/knowledge_consumption.md)
- [wiki_surface_index](../modules/wiki_surface_index.md)

## Behavior

Builds the knowledge portion of a context response without overstating its
state. If no generated projection is declared it returns an absent,
snapshot-only view. Otherwise it loads the committed artifacts with degraded
mismatch handling and, when a source snapshot is available, compares them with
live source and infrastructure observations. Load or comparison failures are
reported through availability and freshness fields rather than guessed away.
