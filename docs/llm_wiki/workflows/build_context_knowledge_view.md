# build_context_knowledge_view

**Entry point:** `context_service._build_context_knowledge_view`
**Modules involved:** [context_service](../modules/context_service.md), [extraction_service](../modules/extraction_service.md), [infrastructure_inventory](../modules/infrastructure_inventory.md), [knowledge_consumption](../modules/knowledge_consumption.md), [knowledge_loader](../modules/knowledge_loader.md), [knowledge_orchestration](../modules/knowledge_orchestration.md), [knowledge_verification](../modules/knowledge_verification.md)

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `knowledge_consumption.build_knowledge_read_view`
2. `knowledge_loader.KnowledgeLoadResult`
3. `knowledge_loader.load_knowledge_state`
4. `extraction_service.get_docker_inventory`
5. `infrastructure_inventory.get_yaml_infrastructure_inventory`
6. `knowledge_orchestration.build_runtime_live_evaluation`
7. `knowledge_orchestration.RuntimeLiveEvaluationInputs`
8. `knowledge_orchestration.runtime_generation_options`
9. `knowledge_consumption.build_knowledge_read_view`
10. `knowledge_verification.attach_machine_verification_read_view`

## Touches

- [context_service](../modules/context_service.md)
- [extraction_service](../modules/extraction_service.md)
- [infrastructure_inventory](../modules/infrastructure_inventory.md)
- [knowledge_consumption](../modules/knowledge_consumption.md)
- [knowledge_loader](../modules/knowledge_loader.md)
- [knowledge_orchestration](../modules/knowledge_orchestration.md)
- [knowledge_verification](../modules/knowledge_verification.md)

## Behavior

Builds the knowledge portion of a context response without overstating its
state. If no generated projection is declared it returns an absent,
snapshot-only view. Otherwise it loads the committed artifacts with degraded
mismatch handling and, when a source snapshot is available, compares them with
live source and infrastructure observations. Load or comparison failures are
reported through availability and freshness fields rather than guessed away.
