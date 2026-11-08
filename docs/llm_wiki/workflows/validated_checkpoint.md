# validated_checkpoint

**Entry point:** `publication_delivery._validated_checkpoint`
**Modules involved:** [knowledge_evidence](../modules/knowledge_evidence.md), [publication_candidate](../modules/publication_candidate.md), [publication_config](../modules/publication_config.md), [publication_delivery](../modules/publication_delivery.md)

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `knowledge_evidence.hash_json`
2. `publication_config.publication_repository`
3. `publication_config.publication_repository`
4. `publication_config.publication_ref_name`
5. `publication_candidate._check_hash`
6. `publication_candidate._check_hash`
7. `publication_candidate._hash_map`
8. `publication_candidate._check_hash`

## Touches

- [knowledge_evidence](../modules/knowledge_evidence.md)
- [publication_candidate](../modules/publication_candidate.md)
- [publication_config](../modules/publication_config.md)
- [publication_delivery](../modules/publication_delivery.md)

## Behavior

This workflow starts at `publication_delivery._validated_checkpoint`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
