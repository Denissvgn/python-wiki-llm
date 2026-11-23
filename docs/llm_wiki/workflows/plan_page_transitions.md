# plan_page_transitions

**Entry point:** `sync_transitions.plan_page_transitions`
**Modules involved:** [source_retirement](../modules/source_retirement.md), [sync_manifest](../modules/sync_manifest.md), [sync_ownership](../modules/sync_ownership.md), [sync_transitions](../modules/sync_transitions.md), [validation](../modules/validation.md)

> Plan every live source-owned page using supplied names, without mutations.

Occupied targets must belong to their incoming owner or to another verified
owner that this same plan moves away. Missing originals never acquire the
content of a different page. This plan describes missing-page creation even
when an unchanged source has not yet been scheduled by sync for refresh.

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `sync_ownership.PageTransitionError`
2. `sync_ownership.PageTransitionError`
3. `source_retirement.retired_entity_mappings`
4. `validation.portable_path_key`
5. `sync_ownership.PageTransitionError`
6. `sync_ownership.PageTransitionError`
7. `sync_manifest.ManifestPageSource`
8. `sync_ownership.PageTransitionError`
9. `validation.portable_path_key`
10. `validation.portable_path_key`
11. `sync_ownership.PageTransitionError`
12. `validation.portable_path_key`
13. `sync_ownership.PageTransitionError`
14. `validation.portable_path_key`
15. `sync_ownership.PageTransitionError`
16. `validation.portable_path_key`
17. `sync_ownership.PageTransitionError`
18. `sync_ownership.PageTransitionError`
19. `validation.portable_path_key`
20. `sync_ownership.PageTransitionError`

## Touches

- [source_retirement](../modules/source_retirement.md)
- [sync_manifest](../modules/sync_manifest.md)
- [sync_ownership](../modules/sync_ownership.md)
- [sync_transitions](../modules/sync_transitions.md)
- [validation](../modules/validation.md)

## Behavior

This workflow starts at `sync_transitions.plan_page_transitions`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
