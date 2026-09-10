# SyncManifest__validate_operational_state

**Entry point:** `sync_manifest.SyncManifest._validate_operational_state`
**Modules involved:** [knowledge_evidence](../modules/knowledge_evidence.md), [knowledge_reuse](../modules/knowledge_reuse.md), [source_selection](../modules/source_selection.md), [sync_manifest](../modules/sync_manifest.md)

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `knowledge_reuse.validate_reuse_commitment`
2. `source_selection.source_selection_identity_from_generation_inputs`
3. `source_selection.source_selection_inputs_from_generation_inputs`
4. `knowledge_evidence.is_valid_sha256`

## Touches

- [knowledge_evidence](../modules/knowledge_evidence.md)
- [knowledge_reuse](../modules/knowledge_reuse.md)
- [source_selection](../modules/source_selection.md)
- [sync_manifest](../modules/sync_manifest.md)

## Behavior

This workflow starts at `sync_manifest.SyncManifest._validate_operational_state`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
