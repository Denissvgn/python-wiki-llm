# provider

**Entry point:** `publication_candidate._provider`
**Modules involved:** [analysis_capture](../modules/analysis_capture.md), [canonical_json](../modules/canonical_json.md), [domain_pack](../modules/domain_pack.md), [knowledge_evidence](../modules/knowledge_evidence.md), [knowledge_storage_io](../modules/knowledge_storage_io.md), [publication_candidate](../modules/publication_candidate.md), [publication_targets](../modules/publication_targets.md), [reference_providers](../modules/reference_providers.md)

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `knowledge_storage_io.StorageReadSession`
2. `canonical_json.sha256_digest`
3. `analysis_capture.engine_package_root`
4. `knowledge_storage_io.StorageReadSession`
5. `canonical_json.sha256_digest`
6. `canonical_json.sha256_digest`
7. `publication_targets.current_publication_targets`
8. `reference_providers.reference_providers_identity`
9. `domain_pack.current_pack`
10. `knowledge_evidence.hash_json`

## Touches

- [analysis_capture](../modules/analysis_capture.md)
- [canonical_json](../modules/canonical_json.md)
- [domain_pack](../modules/domain_pack.md)
- [knowledge_evidence](../modules/knowledge_evidence.md)
- [knowledge_storage_io](../modules/knowledge_storage_io.md)
- [publication_candidate](../modules/publication_candidate.md)
- [publication_targets](../modules/publication_targets.md)
- [reference_providers](../modules/reference_providers.md)

## Behavior

This workflow starts at `publication_candidate._provider`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
