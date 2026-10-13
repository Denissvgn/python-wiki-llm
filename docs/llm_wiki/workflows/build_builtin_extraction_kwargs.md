# build_builtin_extraction_kwargs

**Entry point:** `extraction_service._build_builtin_extraction_kwargs`
**Modules involved:** [extraction_service](../modules/extraction_service.md), [go_extractor](../modules/go_extractor.md), [haskell_extractor](../modules/haskell_extractor.md), [rust_extractor](../modules/rust_extractor.md)

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `go_extractor.GoExtractionRequest`
2. `rust_extractor.RustExtractionRequest`
3. `haskell_extractor.HaskellExtractionRequest`

## Touches

- [extraction_service](../modules/extraction_service.md)
- [go_extractor](../modules/go_extractor.md)
- [haskell_extractor](../modules/haskell_extractor.md)
- [rust_extractor](../modules/rust_extractor.md)

## Behavior

Builds the language-specific request from the selected source snapshot and current inventory controls. Native Go, Rust and Haskell request objects receive `capture_path_outcomes` as their opt-in diagnostics flag; Python and JavaScript/TypeScript receive their own diagnostic arguments. Exact source-file selection and helper-cache binding pass through unchanged. Diagnostic extraction requires fresh parser outcomes rather than assuming plain inventory-cache membership is parse qualification.
