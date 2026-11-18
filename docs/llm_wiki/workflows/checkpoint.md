# checkpoint

**Entry point:** `git_transport._checkpoint`
**Modules involved:** [canonical_json](../modules/canonical_json.md), [git_transport](../modules/git_transport.md), [knowledge_evidence](../modules/knowledge_evidence.md), [publication_delivery](../modules/publication_delivery.md)

> Relate the observed marker to the commit and prior state it claims.

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `publication_delivery.split_delivery_tree`
2. `publication_delivery.split_delivery_tree`
3. `knowledge_evidence.hash_json`
4. `canonical_json.sha256_digest`
5. `publication_delivery.split_delivery_tree`

## Touches

- [canonical_json](../modules/canonical_json.md)
- [git_transport](../modules/git_transport.md)
- [knowledge_evidence](../modules/knowledge_evidence.md)
- [publication_delivery](../modules/publication_delivery.md)

## Behavior

This workflow starts at `git_transport._checkpoint`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
