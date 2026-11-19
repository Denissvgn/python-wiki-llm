# preflight_page_transition_governance

**Entry point:** `sync_runtime._preflight_page_transition_governance`
**Modules involved:** [knowledge_governance](../modules/knowledge_governance.md), [sync_manifest](../modules/sync_manifest.md), [sync_runtime](../modules/sync_runtime.md), [wiki_surface](../modules/wiki_surface.md)

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `knowledge_governance.load_governance`
2. `knowledge_governance.ConceptGovernanceReference`
3. `wiki_surface.mcp_uri`
4. `knowledge_governance.natural_key_for`
5. `knowledge_governance.reconcile_concepts`
6. `sync_manifest.SyncManifest`

## Touches

- [knowledge_governance](../modules/knowledge_governance.md)
- [sync_manifest](../modules/sync_manifest.md)
- [sync_runtime](../modules/sync_runtime.md)
- [wiki_surface](../modules/wiki_surface.md)

## Behavior

This workflow starts at `sync_runtime._preflight_page_transition_governance`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
