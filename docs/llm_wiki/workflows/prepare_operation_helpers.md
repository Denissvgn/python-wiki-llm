# prepare_operation_helpers

**Entry point:** `helper_preparation.prepare_operation_helpers`
**Modules involved:** [helper_cache](../modules/helper_cache.md), [helper_preparation](../modules/helper_preparation.md), [helper_runtime](../modules/helper_runtime.md), [progress](../modules/progress.md)

> Resolve helpers before capture, without changing an inspection's policy.

Operation scopes belong to the CLI/API/service entry point. An unscoped
low-level lookup keeps its historical existing-only behavior. The snapshot
and registry must already have passed their caller's request validation.

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `helper_runtime.current_helper_operation`
2. `helper_runtime.required_helper_languages`
3. `helper_runtime.pinned_helper`
4. `helper_cache.cache_roots`
5. `helper_cache.HelperPreparationError`
6. `helper_cache.validate_handle`
7. `helper_cache.HelperPreparationError`
8. `helper_cache.cache_roots`
9. `helper_cache.HelperPreparationError`
10. `helper_cache.lookup_helper`
11. `progress.phase`
12. `helper_cache.ensure_helper`
13. `helper_runtime.bind_helper`

## Touches

- [helper_cache](../modules/helper_cache.md)
- [helper_preparation](../modules/helper_preparation.md)
- [helper_runtime](../modules/helper_runtime.md)
- [progress](../modules/progress.md)

## Behavior

This workflow starts at `helper_preparation.prepare_operation_helpers`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
