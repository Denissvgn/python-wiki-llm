# runtime_live_concept_bases

**Entry point:** `knowledge_orchestration._runtime_live_concept_bases`
**Modules involved:** [knowledge_evidence](../modules/knowledge_evidence.md), [knowledge_model](../modules/knowledge_model.md), [knowledge_orchestration](../modules/knowledge_orchestration.md), [sync_manifest](../modules/sync_manifest.md)

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `knowledge_evidence.ConceptObservationBasis`
2. `knowledge_model.KnowledgeIndex`
3. `sync_manifest.SyncManifest`

## Touches

- [knowledge_evidence](../modules/knowledge_evidence.md)
- [knowledge_model](../modules/knowledge_model.md)
- [knowledge_orchestration](../modules/knowledge_orchestration.md)
- [sync_manifest](../modules/sync_manifest.md)

## Behavior

Reconstructs current observation bases for concepts that have canonical
manifest source mappings. Module and entity concepts are matched to live
inventory records, exact content hashes, and extractor identities; a second
pass maps infrastructure concepts by their recorded source path. Concepts with
missing or insufficient live inputs are left unresolved so the freshness layer
can report uncertainty instead of inventing a comparison.
