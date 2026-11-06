# helper_identity

**Entry point:** `extractor_helpers.helper_identity`
**Modules involved:** [extractor_helpers](../modules/extractor_helpers.md), [helper_cache](../modules/helper_cache.md), [helper_runtime](../modules/helper_runtime.md), [typescript_helper_identity](../modules/typescript_helper_identity.md)

> Inspect existing preparation receipts and execution runtime without setup.

A receipt describes preparation, not the runtime currently selected by PATH.
Fingerprints are observed identities, not a claim of release authenticity.

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `helper_runtime.current_helper_operation`
2. `helper_runtime.pinned_helper`
3. `helper_cache.cache_roots`
4. `helper_cache.validate_handle`
5. `helper_cache.preparation_cache_root`
6. `helper_cache.cache_roots`
7. `helper_cache.lookup_helper`
8. `helper_cache.preparation_cache_root`
9. `typescript_helper_identity.read_receipt`
10. `helper_cache._json`
11. `helper_cache._safe`
12. `typescript_helper_identity.dependency_fingerprint`
13. `helper_cache._safe`
14. `helper_cache._native_binary`
15. `helper_cache._native_fingerprint`
16. `helper_cache._safe`
17. `typescript_helper_identity.execution_source_fingerprint`

## Touches

- [extractor_helpers](../modules/extractor_helpers.md)
- [helper_cache](../modules/helper_cache.md)
- [helper_runtime](../modules/helper_runtime.md)
- [typescript_helper_identity](../modules/typescript_helper_identity.md)

## Behavior

This workflow starts at `extractor_helpers.helper_identity`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
