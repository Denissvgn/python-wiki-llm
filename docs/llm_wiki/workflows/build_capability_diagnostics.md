# build_capability_diagnostics

**Entry point:** `capability_diagnostics.build_capability_diagnostics`
**Modules involved:** [capability_diagnostics](../modules/capability_diagnostics.md), [config](../modules/config.md), [extractor_helpers](../modules/extractor_helpers.md), [helper_cache](../modules/helper_cache.md), [plugins](../modules/plugins.md), [source_snapshot](../modules/source_snapshot.md)

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `config.validate_source_root`
2. `source_snapshot.build_source_snapshot`
3. `helper_cache.cache_roots`
4. `helper_cache.preparation_cache_root`
5. `extractor_helpers.get_prepared_typescript_root`
6. `extractor_helpers.get_prepared_binary`
7. `extractor_helpers._manifest_path`
8. `helper_cache._profile_slots`
9. `extractor_helpers.helper_preparation_argv`
10. `plugins.read_lock`
11. `plugins.PluginError`
12. `plugins.validate_plugin`
13. `plugins.plugin_store`
14. `plugins.plugin_store`

## Touches

- [capability_diagnostics](../modules/capability_diagnostics.md)
- [config](../modules/config.md)
- [extractor_helpers](../modules/extractor_helpers.md)
- [helper_cache](../modules/helper_cache.md)
- [plugins](../modules/plugins.md)
- [source_snapshot](../modules/source_snapshot.md)

## Behavior

This workflow starts at `capability_diagnostics.build_capability_diagnostics`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
