# load_control_workspace

**Entry point:** `controller._load_control_workspace`
**Modules involved:** [calibration_contracts](../modules/calibration_contracts.md), [controller](../modules/controller.md), [documentation_policy](../modules/documentation_policy.md), [protected_artifacts](../modules/protected_artifacts.md)

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `documentation_policy.hash_bytes`
2. `protected_artifacts.canonical_json_bytes`
3. `documentation_policy.hash_bytes`
4. `documentation_policy.TreeBaseline.from_dict`
5. `documentation_policy.compare_tree_baseline`
6. `calibration_contracts.validate_flow_evidence_census`

## Touches

- [calibration_contracts](../modules/calibration_contracts.md)
- [controller](../modules/controller.md)
- [documentation_policy](../modules/documentation_policy.md)
- [protected_artifacts](../modules/protected_artifacts.md)

## Behavior

This workflow starts at `controller._load_control_workspace`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
