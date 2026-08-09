# finalize_bootstrap

**Entry point:** `bootstrap_runtime._finalize_bootstrap`
**Modules involved:** [bootstrap_runtime](../modules/bootstrap_runtime.md), [bootstrap_service](../modules/bootstrap_service.md), [extraction_service](../modules/extraction_service.md), [io](../modules/io.md)

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `io.io`
2. `bootstrap_service.BootstrapResult`
3. `extraction_service.InventoryResult`

## Touches

- [bootstrap_runtime](../modules/bootstrap_runtime.md)
- [bootstrap_service](../modules/bootstrap_service.md)
- [extraction_service](../modules/extraction_service.md)
- [io](../modules/io.md)

## Behavior

Completes a successful first-use generation from the already extracted
inventory. It derives persistent surface policy, writes the landing page and
log, updates requested agent constraints, finalizes the manifest and generated
knowledge artifacts, and only then emits the human or structured completion
summary. The returned `BootstrapResult` contains the same created, updated,
skipped, and warning records accumulated during the run.
