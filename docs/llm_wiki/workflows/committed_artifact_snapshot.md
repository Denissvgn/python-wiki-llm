# committed_artifact_snapshot

**Entry point:** `knowledge_cmd._committed_artifact_snapshot`
**Modules involved:** [knowledge_artifacts](../modules/knowledge_artifacts.md), [knowledge_cmd](../modules/knowledge_cmd.md), [knowledge_governance](../modules/knowledge_governance.md), [sync_manifest](../modules/sync_manifest.md)

> Read artifacts committed by their manifest without checking live Markdown.

This narrower read is used by the staged move workflow.  A page rename is
expected to make the live Markdown snapshot stale before the following
sync, but the last committed artifacts must still be internally coherent.

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `sync_manifest.SyncManifest.load`
2. `knowledge_artifacts.validate_knowledge_artifacts`
3. `knowledge_governance.GovernanceError`
4. `knowledge_governance.GovernanceError`

## Touches

- [knowledge_artifacts](../modules/knowledge_artifacts.md)
- [knowledge_cmd](../modules/knowledge_cmd.md)
- [knowledge_governance](../modules/knowledge_governance.md)
- [sync_manifest](../modules/sync_manifest.md)

## Behavior

This workflow starts at `knowledge_cmd._committed_artifact_snapshot`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
