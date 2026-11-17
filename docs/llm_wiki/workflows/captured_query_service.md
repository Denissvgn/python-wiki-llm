# captured_query_service

**Entry point:** `context_packet_builder._captured_query_service`
**Modules involved:** [context_packet](../modules/context_packet.md), [context_packet_builder](../modules/context_packet_builder.md), [context_request_format](../modules/context_request_format.md), [documentation_queries](../modules/documentation_queries.md), [knowledge_verification](../modules/knowledge_verification.md)

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `documentation_queries.DocumentationGraphQueryService`
2. `context_packet._thaw_json`
3. `knowledge_verification.verification_summaries_for_concepts`
4. `context_request_format.ProtocolRequestError`

## Touches

- [context_packet](../modules/context_packet.md)
- [context_packet_builder](../modules/context_packet_builder.md)
- [context_request_format](../modules/context_request_format.md)
- [documentation_queries](../modules/documentation_queries.md)
- [knowledge_verification](../modules/knowledge_verification.md)

## Behavior

This workflow starts at `context_packet_builder._captured_query_service`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
