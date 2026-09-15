# get_knowledge_coverage

**Entry point:** `api.get_knowledge_coverage`
**Modules involved:** [api](../modules/api.md), [context_packet](../modules/context_packet.md), [knowledge_consumption](../modules/knowledge_consumption.md), [knowledge_coverage](../modules/knowledge_coverage.md)

> Explain modeled coverage from a snapshot, live capture or existing service.

A supplied service retains its captured read scope. Source/helper options
apply only to a new live capture; this operation never initializes agents
or writes projections.

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `knowledge_coverage.build_knowledge_coverage`
2. `context_packet.capture_context_read`
3. `knowledge_coverage.build_knowledge_coverage`
4. `context_packet._assert_source_unchanged`
5. `context_packet._assert_wiki_unchanged`
6. `context_packet._wiki_anchor`
7. `knowledge_consumption.load_knowledge_read_view`
8. `knowledge_coverage.build_knowledge_coverage`
9. `context_packet._assert_wiki_unchanged`

## Touches

- [api](../modules/api.md)
- [context_packet](../modules/context_packet.md)
- [knowledge_consumption](../modules/knowledge_consumption.md)
- [knowledge_coverage](../modules/knowledge_coverage.md)

## Behavior

This workflow starts at `api.get_knowledge_coverage`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
