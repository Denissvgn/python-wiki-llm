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

This workflow starts at `extraction_service._build_builtin_extraction_kwargs`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
