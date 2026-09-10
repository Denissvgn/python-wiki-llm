# captured_query_service

**Entry point:** `context_packet._captured_query_service`
**Modules involved:** [context_packet](../modules/context_packet.md), [context_service](../modules/context_service.md), [documentation_queries](../modules/documentation_queries.md), [knowledge_verification](../modules/knowledge_verification.md)

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `documentation_queries.DocumentationGraphQueryService`
2. `knowledge_verification.verification_summaries_for_concepts`
3. `context_service.ProtocolRequestError`

## Touches

- [context_packet](../modules/context_packet.md)
- [context_service](../modules/context_service.md)
- [documentation_queries](../modules/documentation_queries.md)
- [knowledge_verification](../modules/knowledge_verification.md)

## Behavior

This workflow starts at `context_packet._captured_query_service`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
