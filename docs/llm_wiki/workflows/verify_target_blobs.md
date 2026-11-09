# verify_target_blobs

**Entry point:** `checkout._verify_target_blobs`
**Modules involved:** [checkout](../modules/checkout.md), [knowledge_evidence](../modules/knowledge_evidence.md), [knowledge_storage_io](../modules/knowledge_storage_io.md), [publication_candidate](../modules/publication_candidate.md)

> Bind the public bytes used by the exporter to the unfiltered Git tree.

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `publication_candidate._read_tree`
2. `knowledge_evidence.sha256_bytes`
3. `knowledge_storage_io.read_guarded`

## Touches

- [checkout](../modules/checkout.md)
- [knowledge_evidence](../modules/knowledge_evidence.md)
- [knowledge_storage_io](../modules/knowledge_storage_io.md)
- [publication_candidate](../modules/publication_candidate.md)

## Behavior

This workflow starts at `checkout._verify_target_blobs`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
