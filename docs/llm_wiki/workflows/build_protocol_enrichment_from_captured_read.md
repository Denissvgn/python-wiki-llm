# build_protocol_enrichment_from_captured_read

**Entry point:** `context_packet._build_protocol_enrichment_from_captured_read`
**Modules involved:** [context_packet](../modules/context_packet.md), [context_service](../modules/context_service.md), [documentation_queries](../modules/documentation_queries.md), [knowledge_verification](../modules/knowledge_verification.md)

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `context_service._context_query_surface`
2. `documentation_queries.DocumentationGraphQueryService`
3. `knowledge_verification.verification_summaries_for_concepts`
4. `context_service.ProtocolRequestError`
5. `context_service._context_freshness_rank_by_source`
6. `context_service._compact_typed_graph_status`
7. `context_service._symbol_pages_payload`
8. `context_service._surface_filter_payload`
9. `context_service._append_knowledge_context_warning`
10. `context_service._freshness_ranking_policy`
11. `context_service._append_typed_graph_context_warning`

## Touches

- [context_packet](../modules/context_packet.md)
- [context_service](../modules/context_service.md)
- [documentation_queries](../modules/documentation_queries.md)
- [knowledge_verification](../modules/knowledge_verification.md)

## Behavior

This workflow starts at `context_packet._build_protocol_enrichment_from_captured_read`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
