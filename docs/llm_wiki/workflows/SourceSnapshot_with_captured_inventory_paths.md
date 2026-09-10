# SourceSnapshot_with_captured_inventory_paths

**Entry point:** `source_snapshot.SourceSnapshot.with_captured_inventory_paths`
**Modules involved:** [common](../modules/common.md), [source_selection](../modules/source_selection.md), [source_snapshot](../modules/source_snapshot.md), [validation](../modules/validation.md)

> Commit extractor-returned paths absent from built-in discovery.

Plugin extractors may own extensions unknown to the built-in language
registry. The extractor result already supplies the exact finite path
set, so this boundary reads only those missing files and never performs
another tree walk or invokes an extractor.

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `validation.portable_path_key`
2. `source_selection.path_is_selected`
3. `validation.portable_path_key`
4. `common.is_bundled_helper_implementation_path`
5. `source_selection.locate_exact_repository_path`
6. `common.is_bundled_helper_implementation_path`

## Touches

- [common](../modules/common.md)
- [source_selection](../modules/source_selection.md)
- [source_snapshot](../modules/source_snapshot.md)
- [validation](../modules/validation.md)

## Behavior

This workflow starts at `source_snapshot.SourceSnapshot.with_captured_inventory_paths`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
