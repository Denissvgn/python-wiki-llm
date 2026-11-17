# wiki_anchor

**Entry point:** `context_packet_builder._wiki_anchor`
**Modules involved:** [context_packet](../modules/context_packet.md), [context_packet_builder](../modules/context_packet_builder.md), [knowledge_governance](../modules/knowledge_governance.md), [source_snapshot](../modules/source_snapshot.md)

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `source_snapshot.directory_identity`
2. `context_packet._domain_hash`
3. `knowledge_governance._governance_lock_root`
4. `context_packet._domain_hash`

## Touches

- [context_packet](../modules/context_packet.md)
- [context_packet_builder](../modules/context_packet_builder.md)
- [knowledge_governance](../modules/knowledge_governance.md)
- [source_snapshot](../modules/source_snapshot.md)

## Behavior

This workflow starts at `context_packet_builder._wiki_anchor`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
