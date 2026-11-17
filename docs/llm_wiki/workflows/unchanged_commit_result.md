# unchanged_commit_result

**Entry point:** `knowledge_reuse.unchanged_commit_result`
**Modules involved:** [canonical_json](../modules/canonical_json.md), [knowledge_artifacts](../modules/knowledge_artifacts.md), [knowledge_packs](../modules/knowledge_packs.md), [knowledge_reuse](../modules/knowledge_reuse.md)

> Return the ordinary result shape using already captured, validated bytes.

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `knowledge_artifacts.PlannedArtifactWrite`
2. `canonical_json.sha256_digest`
3. `knowledge_packs.packed_format`
4. `knowledge_artifacts.KnowledgeCommitResult`
5. `knowledge_artifacts.PlannedArtifactWrite`
6. `canonical_json.sha256_digest`

## Touches

- [canonical_json](../modules/canonical_json.md)
- [knowledge_artifacts](../modules/knowledge_artifacts.md)
- [knowledge_packs](../modules/knowledge_packs.md)
- [knowledge_reuse](../modules/knowledge_reuse.md)

## Behavior

This workflow starts at `knowledge_reuse.unchanged_commit_result`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
