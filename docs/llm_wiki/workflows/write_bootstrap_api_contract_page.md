# write_bootstrap_api_contract_page

**Entry point:** `bootstrap_runtime._write_bootstrap_api_contract_page`
**Modules involved:** [api_contracts](../modules/api_contracts.md), [bootstrap_runtime](../modules/bootstrap_runtime.md), [io](../modules/io.md), [wiki_surface](../modules/wiki_surface.md)

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `wiki_surface.canonical_path`
2. `api_contracts.render_api_contracts_markdown`
3. `io.read_md`

## Touches

- [api_contracts](../modules/api_contracts.md)
- [bootstrap_runtime](../modules/bootstrap_runtime.md)
- [io](../modules/io.md)
- [wiki_surface](../modules/wiki_surface.md)

## Behavior

This workflow starts at `bootstrap_runtime._write_bootstrap_api_contract_page`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
