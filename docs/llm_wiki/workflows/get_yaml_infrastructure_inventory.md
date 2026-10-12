# get_yaml_infrastructure_inventory

**Entry point:** `infrastructure_inventory.get_yaml_infrastructure_inventory`
**Modules involved:** [infrastructure_inventory](../modules/infrastructure_inventory.md), [source_snapshot](../modules/source_snapshot.md), [yaml_formats](../modules/yaml_formats.md), [yaml_syntax](../modules/yaml_syntax.md)

> Discover recognized infrastructure and runtime/config YAML files.

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `source_snapshot.build_source_snapshot`
2. `yaml_syntax.load_yaml_documents`
3. `yaml_formats.parse_extended_yaml`

## Touches

- [infrastructure_inventory](../modules/infrastructure_inventory.md)
- [source_snapshot](../modules/source_snapshot.md)
- [yaml_formats](../modules/yaml_formats.md)
- [yaml_syntax](../modules/yaml_syntax.md)

## Behavior

Reads selected YAML candidates from the supplied snapshot or a newly captured
source root. Each candidate is safely composed, then routed by workflow path,
named format, Kubernetes shape/convention or targeted runtime family. Unknown
formats are omitted from this inventory; infrastructure planning preserves their
source-bound discovery diagnostics. No source configuration or template is
executed, and advisory-bearing models must retain their qualification when
rendered or consumed.
