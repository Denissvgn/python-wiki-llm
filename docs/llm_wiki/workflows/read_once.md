# read_once

**Entry point:** `task_context._read_once`
**Modules involved:** [change_selection](../modules/change_selection.md), [context_budget](../modules/context_budget.md), [context_packet](../modules/context_packet.md), [context_service](../modules/context_service.md), [documentation_query_builder](../modules/documentation_query_builder.md), [knowledge_consumption](../modules/knowledge_consumption.md), [knowledge_envelope](../modules/knowledge_envelope.md), [search_service](../modules/search_service.md), [task_context](../modules/task_context.md), [task_contract](../modules/task_contract.md), [task_evidence](../modules/task_evidence.md), [wiki_surface_index](../modules/wiki_surface_index.md), [workflow_profile](../modules/workflow_profile.md)

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `context_packet._wiki_anchor`
2. `search_service.search_records`
3. `search_service.page_records`
4. `context_packet.capture_context_read`
5. `context_packet.ContextPacketSourceMutationError`
6. `change_selection.select_changes`
7. `context_packet.ContextPacketSourceMutationError`
8. `task_evidence.query_service`
9. `task_evidence.declaration_records`
10. `knowledge_consumption.load_knowledge_read_view`
11. `context_service.KnowledgeRequiredUnavailableError`
12. `wiki_surface_index.evaluate_surface_index`
13. `documentation_query_builder.build_documentation_query_service_from_view`
14. `context_service.KnowledgeRequiredUnavailableError`
15. `task_evidence.observe_requirement`
16. `task_evidence.match_declarations`
17. `task_evidence.observe_requirement`
18. `knowledge_envelope.hash_source_snapshot`
19. `workflow_profile.content_id`
20. `context_budget.validate_request`
21. `context_packet.build_context_from_captured_read`
22. `context_budget.fit_payload`
23. `task_contract.TaskContext`
24. `context_packet._assert_source_unchanged`
25. `context_packet._assert_selection_unchanged`
26. `change_selection.select_changes`
27. `context_packet.ContextPacketSourceMutationError`
28. `context_packet._assert_wiki_unchanged`

## Touches

- [change_selection](../modules/change_selection.md)
- [context_budget](../modules/context_budget.md)
- [context_packet](../modules/context_packet.md)
- [context_service](../modules/context_service.md)
- [documentation_query_builder](../modules/documentation_query_builder.md)
- [knowledge_consumption](../modules/knowledge_consumption.md)
- [knowledge_envelope](../modules/knowledge_envelope.md)
- [search_service](../modules/search_service.md)
- [task_context](../modules/task_context.md)
- [task_contract](../modules/task_contract.md)
- [task_evidence](../modules/task_evidence.md)
- [wiki_surface_index](../modules/wiki_surface_index.md)
- [workflow_profile](../modules/workflow_profile.md)

## Behavior

This workflow starts at `task_context._read_once`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
