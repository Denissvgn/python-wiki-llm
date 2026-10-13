# check_duplicate_removal_custody

**Entry point:** `source_retirement._check_duplicate_removal_custody`
**Modules involved:** [knowledge_evidence](../modules/knowledge_evidence.md), [source_retirement](../modules/source_retirement.md), [sync_manifest](../modules/sync_manifest.md), [wiki_surface](../modules/wiki_surface.md)

> Require an unchanged, distinguishable surviving prefix before retiring suffixes.

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `sync_manifest.ManifestPageSource`
2. `wiki_surface.canonical_path`
3. `knowledge_evidence.entity_observation_hash`
4. `sync_manifest.generated_semantics_for_file`

## Touches

- [knowledge_evidence](../modules/knowledge_evidence.md)
- [source_retirement](../modules/source_retirement.md)
- [sync_manifest](../modules/sync_manifest.md)
- [wiki_surface](../modules/wiki_surface.md)

## Behavior

Checks a shrinking duplicate declaration list against the prior full entity observation hashes and unique generated defaults of the surviving prefix. Changed, unknown or indistinguishable predecessors block retirement before authored context can move to a shifted occurrence.
