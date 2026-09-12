# build_capability_diagnostics

**Entry point:** `capability_diagnostics.build_capability_diagnostics`
**Modules involved:** [capability_diagnostics](../modules/capability_diagnostics.md), [config](../modules/config.md), [extractor_helpers](../modules/extractor_helpers.md), [plugins](../modules/plugins.md), [source_snapshot](../modules/source_snapshot.md)

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `config.validate_source_root`
2. `source_snapshot.build_source_snapshot`
3. `extractor_helpers.resolve_helper_cache_root`
4. `extractor_helpers.get_prepared_typescript_root`
5. `extractor_helpers.get_prepared_binary`
6. `extractor_helpers._manifest_path`
7. `plugins.read_lock`
8. `plugins.PluginError`
9. `plugins.validate_plugin`
10. `plugins.plugin_store`
11. `plugins.plugin_store`

## Touches

- [capability_diagnostics](../modules/capability_diagnostics.md)
- [config](../modules/config.md)
- [extractor_helpers](../modules/extractor_helpers.md)
- [plugins](../modules/plugins.md)
- [source_snapshot](../modules/source_snapshot.md)

## Behavior

This workflow starts at `capability_diagnostics.build_capability_diagnostics`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
