# build_context_knowledge_view

**Entry point:** `context_service._build_context_knowledge_view`
**Modules involved:** [context_packet](../modules/context_packet.md), [context_service](../modules/context_service.md), [extraction_service](../modules/extraction_service.md), [infrastructure_inventory](../modules/infrastructure_inventory.md), [knowledge_consumption](../modules/knowledge_consumption.md), [knowledge_loader](../modules/knowledge_loader.md), [knowledge_orchestration](../modules/knowledge_orchestration.md), [knowledge_verification](../modules/knowledge_verification.md)

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `knowledge_consumption.build_knowledge_read_view`
2. `knowledge_loader.KnowledgeLoadResult`
3. `knowledge_loader.load_knowledge_state`
4. `context_packet.ContextPacketAuthorityError`
5. `knowledge_loader.KnowledgeStateLoadError`
6. `extraction_service.get_docker_inventory`
7. `infrastructure_inventory.get_yaml_infrastructure_inventory`
8. `knowledge_orchestration.build_runtime_live_evaluation`
9. `knowledge_orchestration.RuntimeLiveEvaluationInputs`
10. `knowledge_orchestration.runtime_generation_options`
11. `knowledge_consumption.build_knowledge_read_view`
12. `knowledge_verification.attach_machine_verification_read_view`

## Touches

- [context_packet](../modules/context_packet.md)
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
live source and infrastructure observations. Ordinary maintenance failures are
raised as a typed authority refusal before an invalid load result reaches the
read-view invariant. An immutable marker is a declaration even when other roots
are absent. Legacy absence and eligible degraded views retain their separate
availability/freshness handling; damaged ownership is never promoted to either.
