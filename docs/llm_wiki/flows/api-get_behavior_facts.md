# get_behavior_facts

**Entry point:** `get_behavior_facts` (`api`)
**Source:** [api](../modules/api.md)
**Modules touched:** [api](../modules/api.md), [behavior_reference](../modules/behavior_reference.md), [change_selection](../modules/change_selection.md), [cli](../modules/cli.md), and 15 more

**Complete modules touched:**

- [api](../modules/api.md)
- [behavior_reference](../modules/behavior_reference.md)
- [change_selection](../modules/change_selection.md)
- [cli](../modules/cli.md)
- [cli_reference](../modules/cli_reference.md)
- [current_contracts](../modules/current_contracts.md)
- [documentation_queries](../modules/documentation_queries.md)
- [documentation_query_builder](../modules/documentation_query_builder.md)
- [helper_runtime](../modules/helper_runtime.md)
- [io](../modules/io.md)
- [knowledge_evidence](../modules/knowledge_evidence.md)
- [llm_wiki_cli___init__](../modules/llm_wiki_cli___init__.md)
- [reference_cmd](../modules/reference_cmd.md)
- [skills](../modules/skills.md)
- [task_compact](../modules/task_compact.md)
- [task_contract](../modules/task_contract.md)
- [validation](../modules/validation.md)
- [wiki_surface](../modules/wiki_surface.md)
- [workflow_profile](../modules/workflow_profile.md)

## Call sequence

> Static overview in presentation order, not runtime execution order. Arrows retain captured callers; representative internal continuations and boundary examples precede repeated helper detail.

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as get_behavior_facts (src/llm_wiki_cli/api.py)
    participant p1 as get_behavior_facts (src/llm_wiki_cli/services/behavior_reference.py)
    participant p2 as get_cli_contract
    participant p3 as _task_facts
    participant p4 as list_bundled_skills
    participant p5 as validate_behavior_facts
    participant p6 as build_cli_contract
    participant p7 as normalize_task_request
    participant p8 as build_cli_parser
    participant p9 as _provider_package_identity
    participant p10 as normalize_view_options
    participant p11 as _request_defaults
    participant p12 as read_md
    participant p13 as _validate_paths
    participant p14 as _build_parser
    participant p15 as exact_fields
    participant p16 as require_portable_relative_path
    participant p17 as _value
    participant p18 as _command
    participant p19 as bounded_text
    participant p20 as hash_json
    participant p21 as validate_cli_contract
    participant p22 as _installed_identity
    participant p23 as _array
    participant p24 as coordinate
    participant p25 as validate_changes
    participant p26 as normalize_profile
    participant p27 as content_id
    participant p28 as _json_tree
    participant p29 as dict (src/llm_wiki_cli/services…nce.py:get_behavior_facts)
    participant p30 as skill.to_dict
    p0->>p1: get_behavior_facts (src/llm_wiki_cli/services/behavior_reference.py)
    p1->>p2: get_cli_contract
    p1->>p3: _task_facts
    p1->>p4: list_bundled_skills
    p1->>p5: validate_behavior_facts
    p2->>p6: build_cli_contract
    p3->>p7: normalize_task_request
    p2->>p8: build_cli_parser
    p2->>p9: _provider_package_identity
    p3->>p10: normalize_view_options
    p3->>p11: _request_defaults
    p4->>p12: read_md
    p5->>p13: _validate_paths
    p8->>p14: _build_parser
    p7->>p15: exact_fields
    p13->>p16: require_portable_relative_path
    p6->>p17: _value
    p6->>p18: _command
    p7->>p19: bounded_text
    p6->>p20: hash_json
    p6->>p21: validate_cli_contract
    p9->>p22: _installed_identity
    p7->>p23: _array
    p7->>p24: coordinate
    p7->>p25: validate_changes
    p7->>p26: normalize_profile
    p7->>p27: content_id
    p21->>p28: _json_tree
    p1-->>p29: dict (src/llm_wiki_cli/services…nce.py:get_behavior_facts)(config._DEFAULT_CONFIG)
    p1-->>p30: skill.to_dict
```

> Call sequence diagram shows 30 of 599 interactions; 569 omitted to keep the visualization within the 30-interaction and generated-diagram limits, with uncertain identities omitted rather than inferred.

> Captured boundary calls: external 1 of 211 (210 omitted); unresolved 1 of 153 (152 omitted). These counts cover the captured static trace.

Omitted captured detail, grouped by actual caller occurrence and target module:

| Caller | Parent step | Target module | Kind | Omitted interactions |
| --- | --- | --- | --- | --- |
| `src/llm_wiki_cli/services/cli_reference.py:build_cli_contract` | 4 | - | external | 2 |
| `src/llm_wiki_cli/services/cli_reference.py:build_cli_contract` | 4 | [src/llm_wiki_cli/services/cli_reference.py](../modules/cli_reference.md) | internal | 1 |
| `src/llm_wiki_cli/services/cli_reference.py:_value` | 7 | [src/llm_wiki_cli/services/cli_reference.py](../modules/cli_reference.md) | internal | 5 |
| `src/llm_wiki_cli/services/cli_reference.py:_value` | 7 | - | external | 9 |
| `src/llm_wiki_cli/services/cli_reference.py:_value` | 7 | - | unresolved | 2 |
| `src/llm_wiki_cli/services/cli_reference.py:_command` | 25 | - | external | 24 |
| `src/llm_wiki_cli/services/cli_reference.py:_command` | 25 | [src/llm_wiki_cli/services/cli_reference.py](../modules/cli_reference.md) | internal | 10 |
| `src/llm_wiki_cli/services/cli_reference.py:_command` | 25 | - | unresolved | 14 |
> Omission summary shows 8 of 132 groups; 124 further groups are not expanded here. Counts above include all omitted interactions.
> Detailed flow queries retain their own coverage and limits; omitted paths may execute at runtime.

> Trace truncated at the depth limit; deeper calls are omitted.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->

### Analysis coverage

**Effect analysis partially available.** Flow assembly and source effect analysis are separate; empty observations do not prove an empty handler body.

Source steps: 236; effect analysis evaluated: 165, partial: 5, unavailable: 66. Counts include steps omitted from the displayed trace.

Collector observations for 170 source steps with known totals: observed: 805, emitted: 788, omitted: 17. Unavailable totals are excluded.

- Callable record unavailable for one or more source steps; those steps have no represented callable body.
- Effect collector omitted observations before flow assembly; displayed effects are partial.
- Effect collector totals unavailable; observed counts cover captured records only.

| Step | Callable record | Effect analysis | Collector totals | Observed | Emitted | Omitted |
|---|---|---|---|---:|---:|---:|
| `get_behavior_facts (src/llm_wiki_cli/api.py)` | `available` | `evaluated` | `available` | `1` | `1` | `0` |
| `get_behavior_facts (src/llm_wiki_cli/services/behavior_reference.py)` | `available` | `evaluated` | `available` | `6` | `6` | `0` |
| `get_cli_contract` | `available` | `evaluated` | `available` | `1` | `1` | `0` |
| `build_cli_contract` | `available` | `evaluated` | `available` | `6` | `6` | `0` |
| `isinstance (src/llm_wiki_cli/services…nce.py:build_cli_contract)` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `CLIReferenceError` | `unavailable` | `unavailable` | `unavailable` | — | — | — |
| `_value` | `available` | `evaluated` | `available` | `10` | `10` | `0` |
| `CLIReferenceError` | `unavailable` | `unavailable` | `unavailable` | — | — | — |
| `isinstance (src/llm_wiki_cli/services/cli_reference.py:_value)` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `CLIReferenceError` | `unavailable` | `unavailable` | `unavailable` | — | — | — |
| `value.as_posix` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `type (src/llm_wiki_cli/services/cli_reference.py:_value)` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |

```mermaid
flowchart LR
    s1["1. get_behavior_facts (src/llm_wiki_cli/api.py)"]
    s2["2. get_behavior_facts (src/llm_wiki_cli/services/behavior_reference.py)"]
    s3["3. get_cli_contract"]
    s4["4. build_cli_contract"]
    s5["5. isinstance (src/llm_wiki_cli/services…nce.py:build_cli_contract)"]
    s6["6. CLIReferenceError"]
    s7["7. _value"]
    s8["8. CLIReferenceError"]
    s9["9. isinstance (src/llm_wiki_cli/services/cli_reference.py:_value)"]
    s10["10. CLIReferenceError"]
    s11["11. value.as_posix"]
    s12["12. type (src/llm_wiki_cli/services/cli_reference.py:_value)"]
    s1 -->|"get_behavior_facts (src/llm_wiki_cli/services/behavior_reference.py)(data not statically known)"| s2
    s2 -->|"get_cli_contract(data not statically known)"| s3
    s3 -->|"build_cli_contract(build_cli_parser(...), package=_provider_package_identity(...), program='llm-wiki')"| s4
    s4 -. "isinstance (src/llm_wiki_cli/services…nce.py:build_cli_contract)(parser, argparse.ArgumentParser)" .-> s5
    s4 -->|"CLIReferenceError('Reference generation requires an ArgumentParser')"| s6
    s4 -->|"_value(dict(...))"| s7
    s7 -->|"CLIReferenceError('Reference values exceed the supported nesting depth')"| s8
    s7 -. "isinstance (src/llm_wiki_cli/services/cli_reference.py:_value)(value, Path)" .-> s9
    s7 -->|"CLIReferenceError('Reference defaults require Path objects without a drive or root')"| s10
    s7 -. "value.as_posix(data not statically known)" .-> s11
    s7 -. "type (src/llm_wiki_cli/services/cli_reference.py:_value)(value)" .-> s12
    click s1 "../modules/api.md"
    click s2 "../modules/behavior_reference.md"
    click s3 "../modules/cli_reference.md"
    click s4 "../modules/cli_reference.md"
    click s6 "../modules/cli_reference.md"
    click s7 "../modules/cli_reference.md"
    click s8 "../modules/cli_reference.md"
    click s10 "../modules/cli_reference.md"
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `get_behavior_facts (src/llm_wiki_cli/api.py)` | - | - | - | `get_facts(...)` |
| `get_behavior_facts (src/llm_wiki_cli/services/behavior_reference.py)` | - | `config`, `config`, `config`, `skills`, `BEHAVIOR_FACTS_SCHEMA_VERSION` | - | `result` |
| `get_cli_contract` | - | - | - | `build_cli_contract(...)` |
| `build_cli_contract` | `parser: argparse.ArgumentParser`, `package: Mapping[str, Any]`, `program: str` | `argparse`, `CLI_CONTRACT_SCHEMA_VERSION` | - | `result` |
| `isinstance (src/llm_wiki_cli/services…nce.py:build_cli_contract)` | - | - | - | - |
| `CLIReferenceError` | - | - | - | - |
| `_value` | `value: object`, `depth: int` | `_MAX_DEPTH`, `Path`, `Mapping` | - | `value`, `value`, `value`, `...`, `...` |
| `CLIReferenceError` | - | - | - | - |
| `isinstance (src/llm_wiki_cli/services/cli_reference.py:_value)` | - | - | - | - |
| `CLIReferenceError` | - | - | - | - |
| `value.as_posix` | - | - | - | - |
| `type (src/llm_wiki_cli/services/cli_reference.py:_value)` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| get_behavior_facts (src/llm_wiki_cli/api.py) | get_behavior_facts (src/llm_wiki_cli/services/behavior_reference.py) | 3593 | `get_facts(data not statically known)` |
| get_behavior_facts (src/llm_wiki_cli/services/behavior_reference.py) | get_cli_contract | 89 | `cli_reference.get_cli_contract(data not statically known)` |
| get_cli_contract | build_cli_contract | 273 | `build_cli_contract(build_cli_parser(...), package=_provider_package_identity(...), program='llm-wiki')` |
| build_cli_contract | isinstance (src/llm_wiki_cli/services…nce.py:build_cli_contract) | 256 | `isinstance(parser, argparse.ArgumentParser)` |
| build_cli_contract | CLIReferenceError | 257 | `CLIReferenceError('Reference generation requires an ArgumentParser')` |
| build_cli_contract | _value | 260 | `_value(dict(...))` |
| _value | CLIReferenceError | 70 | `CLIReferenceError('Reference values exceed the supported nesting depth')` |
| _value | isinstance (src/llm_wiki_cli/services/cli_reference.py:_value) | 71 | `isinstance(value, Path)` |
| _value | CLIReferenceError | 73 | `CLIReferenceError('Reference defaults require Path objects without a drive or root')` |
| _value | value.as_posix | 76 | `value.as_posix(data not statically known)` |
| _value | type (src/llm_wiki_cli/services/cli_reference.py:_value) | 77 | `type(value)` |

### Boundary effects

*No boundary-effect observations were captured in this static trace.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| external_call | `build_cli_contract` | `isinstance` | 256 |
| external_call | `_value` | `isinstance` | 71 |
| unresolved_call | `_value` | `value.as_posix` | 76 |
| external_call | `_value` | `type` | 77 |
| step_limit | `get_behavior_facts` | `first 12 steps` | 0 |
| truncated_flow | `get_behavior_facts` | `depth limit` | 0 |

## Behavior

This flow starts at `get_behavior_facts` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
