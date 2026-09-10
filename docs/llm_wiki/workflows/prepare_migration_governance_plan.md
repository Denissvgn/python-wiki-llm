# prepare_migration_governance_plan

**Entry point:** `migrate_cmd._prepare_migration_governance_plan`
**Modules involved:** [concept_identity](../modules/concept_identity.md), [knowledge_governance](../modules/knowledge_governance.md), [knowledge_orchestration](../modules/knowledge_orchestration.md), [migrate_cmd](../modules/migrate_cmd.md), [wiki_surface](../modules/wiki_surface.md)

> Derive UID carry-forward strictly from the migration's exact matches.

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `wiki_surface.mcp_uri`
2. `wiki_surface.PageKind`
3. `wiki_surface.mcp_uri`
4. `wiki_surface.PageKind`
5. `knowledge_governance.load_governance`
6. `knowledge_orchestration.committed_governance_bundle_id`
7. `knowledge_governance.GovernanceError`
8. `concept_identity.identity_coordinate_key`
9. `concept_identity.identity_coordinate_key`
10. `concept_identity.identity_coordinate_key`
11. `concept_identity.identity_coordinate_key`
12. `concept_identity.identity_coordinate_key`
13. `concept_identity.identity_coordinate_key`
14. `concept_identity.identity_coordinate_key`
15. `concept_identity.identity_coordinate_key`
16. `concept_identity.identity_coordinate_key`
17. `wiki_surface.mcp_uri`
18. `wiki_surface.PageKind`

## Touches

- [concept_identity](../modules/concept_identity.md)
- [knowledge_governance](../modules/knowledge_governance.md)
- [knowledge_orchestration](../modules/knowledge_orchestration.md)
- [migrate_cmd](../modules/migrate_cmd.md)
- [wiki_surface](../modules/wiki_surface.md)

## Behavior

This workflow starts at `migrate_cmd._prepare_migration_governance_plan`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
