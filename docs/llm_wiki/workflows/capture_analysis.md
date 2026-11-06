# capture_analysis

**Entry point:** `analysis_capture.capture_analysis`
**Modules involved:** [analysis_capture](../modules/analysis_capture.md), [analysis_compatibility](../modules/analysis_compatibility.md), [extractor_helpers](../modules/extractor_helpers.md), [helper_cache](../modules/helper_cache.md), [helper_runtime](../modules/helper_runtime.md)

> Capture immutable JSON inputs once; unavailable providers stay unknown.

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `helper_cache.cache_roots`
2. `helper_runtime.current_helper_operation`
3. `helper_runtime.pinned_helper`
4. `analysis_compatibility.digest`
5. `analysis_compatibility.digest`
6. `helper_runtime.pinned_helper`
7. `helper_cache.validate_handle`
8. `helper_cache.lookup_helper`
9. `extractor_helpers.command_output`
10. `analysis_compatibility.digest`

## Touches

- [analysis_capture](../modules/analysis_capture.md)
- [analysis_compatibility](../modules/analysis_compatibility.md)
- [extractor_helpers](../modules/extractor_helpers.md)
- [helper_cache](../modules/helper_cache.md)
- [helper_runtime](../modules/helper_runtime.md)

## Behavior

This workflow starts at `analysis_capture.capture_analysis`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
