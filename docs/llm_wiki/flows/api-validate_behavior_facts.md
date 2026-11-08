# validate_behavior_facts

**Entry point:** `validate_behavior_facts` (`api`)
**Source:** [api](../modules/api.md)
**Modules touched:** [api](../modules/api.md), [behavior_reference](../modules/behavior_reference.md), [cli_reference](../modules/cli_reference.md), [knowledge_evidence](../modules/knowledge_evidence.md), and 1 more

**Complete modules touched:**

- [api](../modules/api.md)
- [behavior_reference](../modules/behavior_reference.md)
- [cli_reference](../modules/cli_reference.md)
- [knowledge_evidence](../modules/knowledge_evidence.md)
- [validation](../modules/validation.md)

## Call sequence

> Static overview in presentation order, not runtime execution order. Arrows retain captured callers; representative internal continuations and boundary examples precede repeated helper detail.

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as validate_behavior_facts (src/llm_wiki_cli/api.py)
    participant p1 as validate_behavior_facts (src/llm_wiki_cli/services/behavior_reference.py)
    participant p2 as _json_tree
    participant p3 as _validate_schema
    participant p4 as _validate_paths
    participant p5 as hash_json
    participant p6 as require_portable_relative_path
    participant p7 as canonical_json_bytes
    participant p8 as _default_path_error
    participant p9 as _check_path_collision
    participant p10 as require_portable_path_component
    participant p11 as _schema
    participant p12 as CLIReferenceError
    participant p13 as sha256_bytes
    participant p14 as _matches_type
    participant p15 as canonical_json_text
    participant p16 as _syntax_key
    participant p17 as _known_syntax
    participant p18 as _remember_syntax
    participant p19 as SharedValidationError
    participant p20 as portable_path_key
    participant p21 as isinstance (src/llm_wiki_cli/api.py:validate_behavior_facts)
    participant p22 as json.dumps(…).encode
    participant p23 as ValueError (src/llm_wiki_cli/api.py:validate_behavior_facts)
    participant p24 as dict (src/llm_wiki_cli/api.py:validate_behavior_facts)
    participant p25 as isinstance (src/llm_wiki_cli/services…y:validate_behavior_facts)
    participant p26 as dict (src/llm_wiki_cli/services…y:validate_behavior_facts)
    participant p27 as len (src/llm_wiki_cli/services…y:validate_behavior_facts)
    participant p28 as json.dumps (src/llm_wiki_cli/services…y:validate_behavior_facts)
    participant p29 as ValueError (src/llm_wiki_cli/services…y:validate_behavior_facts)
    p0->>p1: validate_behavior_facts (src/llm_wiki_cli/services/behavior_reference.py)
    p1->>p2: _json_tree
    p1->>p3: _validate_schema
    p1->>p4: _validate_paths
    p1->>p5: hash_json
    p4->>p6: require_portable_relative_path
    p5->>p7: canonical_json_bytes
    p6->>p8: _default_path_error
    p6->>p9: _check_path_collision
    p6->>p10: require_portable_path_component
    p1->>p11: _schema
    p2->>p12: CLIReferenceError
    p5->>p13: sha256_bytes
    p3->>p14: _matches_type
    p7->>p15: canonical_json_text
    p6->>p16: _syntax_key
    p6->>p17: _known_syntax
    p6->>p18: _remember_syntax
    p8->>p19: SharedValidationError
    p9->>p20: portable_path_key
    p0-->>p21: isinstance (src/llm_wiki_cli/api.py:validate_behavior_facts)(contract, Mapping)
    p1-->>p22: json.dumps(…).encode('utf-8')
    p0-->>p23: ValueError (src/llm_wiki_cli/api.py:validate_behavior_facts)('Behavior facts must be a mapping')
    p0-->>p24: dict (src/llm_wiki_cli/api.py:validate_behavior_facts)(contract)
    p1-->>p25: isinstance (src/llm_wiki_cli/services…y:validate_behavior_facts)(contract, Mapping)
    p1-->>p26: dict (src/llm_wiki_cli/services…y:validate_behavior_facts)(contract)
    p1-->>p27: len (src/llm_wiki_cli/services…y:validate_behavior_facts)(...)
    p1-->>p28: json.dumps (src/llm_wiki_cli/services…y:validate_behavior_facts)(contract, ensure_ascii=False, allow_nan=False, separators=(...))
    p1-->>p29: ValueError (src/llm_wiki_cli/services…y:validate_behavior_facts)('Behavior facts exceed the document byte limit')
    p1-->>p25: isinstance (src/llm_wiki_cli/services…y:validate_behavior_facts)(contract, dict)
```

> Call sequence diagram shows 30 of 154 interactions; 124 omitted to keep the visualization within the 30-interaction and generated-diagram limits, with uncertain identities omitted rather than inferred.

> Captured boundary calls: external 9 of 67 (58 omitted); unresolved 1 of 38 (37 omitted). These counts cover the captured static trace.

Omitted captured detail, grouped by actual caller occurrence and target module:

| Caller | Parent step | Target module | Kind | Omitted interactions |
| --- | --- | --- | --- | --- |
| `src/llm_wiki_cli/services/cli_reference.py:_json_tree` | 7 | - | external | 7 |
| `src/llm_wiki_cli/services/cli_reference.py:_json_tree` | 7 | [src/llm_wiki_cli/services/cli_reference.py](../modules/cli_reference.md) | internal | 3 |
| `src/llm_wiki_cli/services/cli_reference.py:_json_tree` | 7 | - | unresolved | 1 |
| `src/llm_wiki_cli/services/behavior_reference.py:_schema` | 24 | - | external | 2 |
| `src/llm_wiki_cli/services/behavior_reference.py:_schema` | 24 | - | unresolved | 2 |
| `src/llm_wiki_cli/services/cli_reference.py:_validate_schema` | 29 | [src/llm_wiki_cli/services/cli_reference.py](../modules/cli_reference.md) | internal | 12 |
| `src/llm_wiki_cli/services/cli_reference.py:_validate_schema` | 29 | - | unresolved | 11 |
| `src/llm_wiki_cli/services/cli_reference.py:_validate_schema` | 29 | - | external | 17 |
> Omission summary shows 8 of 30 groups; 22 further groups are not expanded here. Counts above include all omitted interactions.
> Detailed flow queries retain their own coverage and limits; omitted paths may execute at runtime.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->

### Analysis coverage

**Effect analysis partially available.** Flow assembly and source effect analysis are separate; empty observations do not prove an empty handler body.

Source steps: 50; effect analysis evaluated: 31, partial: 2, unavailable: 17. Counts include steps omitted from the displayed trace.

Collector observations for 33 source steps with known totals: observed: 156, emitted: 145, omitted: 11. Unavailable totals are excluded.

- Callable record unavailable for one or more source steps; those steps have no represented callable body.
- Effect collector omitted observations before flow assembly; displayed effects are partial.
- Effect collector totals unavailable; observed counts cover captured records only.

| Step | Callable record | Effect analysis | Collector totals | Observed | Emitted | Omitted |
|---|---|---|---|---:|---:|---:|
| `validate_behavior_facts (src/llm_wiki_cli/api.py)` | `available` | `evaluated` | `available` | `2` | `2` | `0` |
| `isinstance (src/llm_wiki_cli/api.py:validate_behavior_facts)` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `ValueError (src/llm_wiki_cli/api.py:validate_behavior_facts)` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `validate_behavior_facts (src/llm_wiki_cli/services/behavior_reference.py)` | `available` | `evaluated` | `available` | `4` | `4` | `0` |
| `isinstance (src/llm_wiki_cli/services…y:validate_behavior_facts)` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `dict (src/llm_wiki_cli/services…y:validate_behavior_facts)` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `_json_tree` | `available` | `evaluated` | `available` | `10` | `10` | `0` |
| `CLIReferenceError` | `unavailable` | `unavailable` | `unavailable` | — | — | — |
| `type (src/llm_wiki_cli/services…i_reference.py:_json_tree)` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `type (src/llm_wiki_cli/services…i_reference.py:_json_tree)` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `math.isfinite` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `type (src/llm_wiki_cli/services…i_reference.py:_json_tree)` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |

```mermaid
flowchart LR
    s1["1. validate_behavior_facts (src/llm_wiki_cli/api.py)"]
    s2["2. isinstance (src/llm_wiki_cli/api.py:validate_behavior_facts)"]
    s3["3. ValueError (src/llm_wiki_cli/api.py:validate_behavior_facts)"]
    s4["4. validate_behavior_facts (src/llm_wiki_cli/services/behavior_reference.py)"]
    s5["5. isinstance (src/llm_wiki_cli/services…y:validate_behavior_facts)"]
    s6["6. dict (src/llm_wiki_cli/services…y:validate_behavior_facts)"]
    s7["7. _json_tree"]
    s8["8. CLIReferenceError"]
    s9["9. type (src/llm_wiki_cli/services…i_reference.py:_json_tree)"]
    s10["10. type (src/llm_wiki_cli/services…i_reference.py:_json_tree)"]
    s11["11. math.isfinite"]
    s12["12. type (src/llm_wiki_cli/services…i_reference.py:_json_tree)"]
    s1 -. "isinstance (src/llm_wiki_cli/api.py:validate_behavior_facts)(contract, Mapping)" .-> s2
    s1 -. "ValueError (src/llm_wiki_cli/api.py:validate_behavior_facts)('Behavior facts must be a mapping')" .-> s3
    s1 -->|"validate_behavior_facts (src/llm_wiki_cli/services/behavior_reference.py)(dict(...))"| s4
    s4 -. "isinstance (src/llm_wiki_cli/services…y:validate_behavior_facts)(contract, Mapping)" .-> s5
    s4 -. "dict (src/llm_wiki_cli/services…y:validate_behavior_facts)(contract)" .-> s6
    s4 -->|"_json_tree(contract)"| s7
    s7 -->|"CLIReferenceError('CLI contract exceeds its structural bounds')"| s8
    s7 -. "type (src/llm_wiki_cli/services…i_reference.py:_json_tree)(value)" .-> s9
    s7 -. "type (src/llm_wiki_cli/services…i_reference.py:_json_tree)(value)" .-> s10
    s7 -. "math.isfinite(value)" .-> s11
    s7 -. "type (src/llm_wiki_cli/services…i_reference.py:_json_tree)(value)" .-> s12
    click s1 "../modules/api.md"
    click s4 "../modules/behavior_reference.md"
    click s7 "../modules/cli_reference.md"
    click s8 "../modules/cli_reference.md"
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `validate_behavior_facts (src/llm_wiki_cli/api.py)` | `contract: Mapping[str, Any]` | `Mapping` | - | - |
| `isinstance (src/llm_wiki_cli/api.py:validate_behavior_facts)` | - | - | - | - |
| `ValueError (src/llm_wiki_cli/api.py:validate_behavior_facts)` | - | - | - | - |
| `validate_behavior_facts (src/llm_wiki_cli/services/behavior_reference.py)` | `contract: object` | `Mapping`, `MAX_BEHAVIOR_FACTS_BYTES`, `skills` | - | - |
| `isinstance (src/llm_wiki_cli/services…y:validate_behavior_facts)` | - | - | - | - |
| `dict (src/llm_wiki_cli/services…y:validate_behavior_facts)` | - | - | - | - |
| `_json_tree` | `value: object`, `depth: int`, `budget` | `_MAX_NODES`, `_MAX_DEPTH` | `budget[...]` | `none`, `none`, `none`, `none` |
| `CLIReferenceError` | - | - | - | - |
| `type (src/llm_wiki_cli/services…i_reference.py:_json_tree)` | - | - | - | - |
| `type (src/llm_wiki_cli/services…i_reference.py:_json_tree)` | - | - | - | - |
| `math.isfinite` | - | - | - | - |
| `type (src/llm_wiki_cli/services…i_reference.py:_json_tree)` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| validate_behavior_facts (src/llm_wiki_cli/api.py) | isinstance (src/llm_wiki_cli/api.py:validate_behavior_facts) | 3601 | `isinstance(contract, Mapping)` |
| validate_behavior_facts (src/llm_wiki_cli/api.py) | ValueError (src/llm_wiki_cli/api.py:validate_behavior_facts) | 3602 | `ValueError('Behavior facts must be a mapping')` |
| validate_behavior_facts (src/llm_wiki_cli/api.py) | validate_behavior_facts (src/llm_wiki_cli/services/behavior_reference.py) | 3603 | `validate(dict(...))` |
| validate_behavior_facts (src/llm_wiki_cli/services/behavior_reference.py) | isinstance (src/llm_wiki_cli/services…y:validate_behavior_facts) | 150 | `isinstance(contract, Mapping)` |
| validate_behavior_facts (src/llm_wiki_cli/services/behavior_reference.py) | dict (src/llm_wiki_cli/services…y:validate_behavior_facts) | 151 | `dict(contract)` |
| validate_behavior_facts (src/llm_wiki_cli/services/behavior_reference.py) | _json_tree | 152 | `cli_reference._json_tree(contract)` |
| _json_tree | CLIReferenceError | 291 | `CLIReferenceError('CLI contract exceeds its structural bounds')` |
| _json_tree | type (src/llm_wiki_cli/services…i_reference.py:_json_tree) | 292 | `type(value)` |
| _json_tree | type (src/llm_wiki_cli/services…i_reference.py:_json_tree) | 294 | `type(value)` |
| _json_tree | math.isfinite | 294 | `math.isfinite(value)` |
| _json_tree | type (src/llm_wiki_cli/services…i_reference.py:_json_tree) | 296 | `type(value)` |

### Boundary effects

*No boundary-effect observations were captured in this static trace.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| external_call | `validate_behavior_facts` | `isinstance` | 3601 |
| external_call | `validate_behavior_facts` | `ValueError` | 3602 |
| external_call | `validate_behavior_facts` | `isinstance` | 150 |
| external_call | `_json_tree` | `type` | 292 |
| external_call | `_json_tree` | `type` | 294 |
| external_call | `_json_tree` | `math.isfinite` | 294 |
| external_call | `_json_tree` | `type` | 296 |
| step_limit | `validate_behavior_facts` | `first 12 steps` | 0 |

## Behavior

This flow starts at `validate_behavior_facts` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
