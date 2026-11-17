# build_knowledge_context_from_captured_read

**Entry point:** `context_packet_builder._build_knowledge_context_from_captured_read`
**Modules involved:** [context_packet](../modules/context_packet.md), [context_packet_builder](../modules/context_packet_builder.md), [context_service](../modules/context_service.md), [documentation_queries](../modules/documentation_queries.md), [maintenance_status](../modules/maintenance_status.md)

> Build explicit v2 knowledge selection from the coordinated capture.

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `context_packet._thaw_json`
2. `context_service._apply_protocol_filters`
3. `documentation_queries.knowledge_view_selection_eligible`
4. `context_service._context_query_surface`
5. `context_service._context_freshness_rank_by_source`
6. `context_service._build_explicit_knowledge_response`
7. `maintenance_status.compact_maintenance_summary`
8. `context_service._explicit_freshness_ranking_policy`

## Touches

- [context_packet](../modules/context_packet.md)
- [context_packet_builder](../modules/context_packet_builder.md)
- [context_service](../modules/context_service.md)
- [documentation_queries](../modules/documentation_queries.md)
- [maintenance_status](../modules/maintenance_status.md)

## Behavior

This workflow starts at `context_packet_builder._build_knowledge_context_from_captured_read`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
