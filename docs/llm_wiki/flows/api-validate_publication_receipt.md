# validate_publication_receipt

**Entry point:** `validate_publication_receipt` (`api`)
**Source:** [api](../modules/api.md)
**Modules touched:** [api](../modules/api.md), [knowledge_evidence](../modules/knowledge_evidence.md), [publication_candidate](../modules/publication_candidate.md), [publication_contracts](../modules/publication_contracts.md), and 1 more

**Complete modules touched:**

- [api](../modules/api.md)
- [knowledge_evidence](../modules/knowledge_evidence.md)
- [publication_candidate](../modules/publication_candidate.md)
- [publication_contracts](../modules/publication_contracts.md)
- [validation](../modules/validation.md)

## Call sequence

> Static overview in presentation order, not runtime execution order. Arrows retain captured callers; representative internal continuations and boundary examples precede repeated helper detail.

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as validate_publication_receipt (src/llm_wiki_cli/api.py)
    participant p1 as validate_publication_receipt (src/llm_wiki_cli/services/publication_candidate.py)
    participant p2 as _json_tree
    participant p3 as hash_json
    participant p4 as validate_publication_basis
    participant p5 as validate_publication_report
    participant p6 as _hash_map
    participant p7 as _validate_review
    participant p8 as _proposal
    participant p9 as _guard
    participant p10 as _fail
    participant p11 as canonical_json_bytes
    participant p12 as _portable
    participant p13 as require_portable_relative_path
    participant p14 as _default_path_error
    participant p15 as _check_path_collision
    participant p16 as require_portable_path_component
    participant p17 as _check_hash
    participant p18 as sha256_bytes
    participant p19 as portable_path_key
    participant p20 as PublicationProtocolError
    participant p21 as canonical_json_text
    participant p22 as _syntax_key
    participant p23 as _known_syntax
    participant p24 as _remember_syntax
    participant p25 as SharedValidationError
    participant p26 as isinstance (src/llm_wiki_cli/api.py:v…idate_publication_receipt)
    participant p27 as json.dumps(…).encode
    participant p28 as ValueError (src/llm_wiki_cli/api.py:v…idate_publication_receipt)
    participant p29 as dict
    participant p30 as len (src/llm_wiki_cli/services…idate_publication_receipt)
    p0->>p1: validate_publication_receipt (src/llm_wiki_cli/services/publication_candidate.py)
    p1->>p2: _json_tree
    p1->>p3: hash_json
    p1->>p4: validate_publication_basis
    p1->>p5: validate_publication_report
    p1->>p6: _hash_map
    p1->>p7: _validate_review
    p1->>p8: _proposal
    p4->>p9: _guard
    p2->>p10: _fail
    p3->>p11: canonical_json_bytes
    p6->>p12: _portable
    p12->>p13: require_portable_relative_path
    p13->>p14: _default_path_error
    p13->>p15: _check_path_collision
    p13->>p16: require_portable_path_component
    p1->>p17: _check_hash
    p3->>p18: sha256_bytes
    p6->>p19: portable_path_key
    p10->>p20: PublicationProtocolError
    p11->>p21: canonical_json_text
    p13->>p22: _syntax_key
    p13->>p23: _known_syntax
    p13->>p24: _remember_syntax
    p14->>p25: SharedValidationError
    p0-->>p26: isinstance (src/llm_wiki_cli/api.py:v…idate_publication_receipt)(receipt, Mapping)
    p1-->>p27: json.dumps(…).encode('utf-8')
    p0-->>p28: ValueError (src/llm_wiki_cli/api.py:v…idate_publication_receipt)('Publication receipt must be a mapping')
    p0-->>p29: dict(receipt)
    p1-->>p30: len (src/llm_wiki_cli/services…idate_publication_receipt)(...)
```

> Call sequence diagram shows 30 of 235 interactions; 205 omitted to keep the visualization within the 30-interaction and generated-diagram limits, with uncertain identities omitted rather than inferred.

> Captured boundary calls: external 4 of 125 (121 omitted); unresolved 1 of 51 (50 omitted). These counts cover the captured static trace.

Omitted captured detail, grouped by actual caller occurrence and target module:

| Caller | Parent step | Target module | Kind | Omitted interactions |
| --- | --- | --- | --- | --- |
| `src/llm_wiki_cli/services/publication_contracts.py:_json_tree` | 5 | - | unresolved | 4 |
| `src/llm_wiki_cli/services/publication_contracts.py:_json_tree` | 5 | - | external | 7 |
| `src/llm_wiki_cli/services/publication_contracts.py:_json_tree` | 5 | [src/llm_wiki_cli/services/publication_contracts.py](../modules/publication_contracts.md) | internal | 3 |
| `src/llm_wiki_cli/services/publication_candidate.py:validate_publication_receipt` | 4 | - | external | 74 |
| `src/llm_wiki_cli/services/publication_candidate.py:_check_hash` | 29 | - | external | 2 |
| `src/llm_wiki_cli/services/publication_candidate.py:_check_hash` | 29 | - | unresolved | 1 |
| `src/llm_wiki_cli/services/knowledge_evidence.py:sha256_bytes` | 34 | - | unresolved | 1 |
| `src/llm_wiki_cli/services/knowledge_evidence.py:sha256_bytes` | 34 | - | external | 1 |
> Omission summary shows 8 of 37 groups; 29 further groups are not expanded here. Counts above include all omitted interactions.
> Detailed flow queries retain their own coverage and limits; omitted paths may execute at runtime.

> Trace truncated at the depth limit; deeper calls are omitted.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->

### Analysis coverage

**Effect analysis partially available.** Flow assembly and source effect analysis are separate; empty observations do not prove an empty handler body.

Source steps: 60; effect analysis evaluated: 49, partial: 2, unavailable: 9. Counts include steps omitted from the displayed trace.

Collector observations for 51 source steps with known totals: observed: 157, emitted: 146, omitted: 11. Unavailable totals are excluded.

- Callable record unavailable for one or more source steps; those steps have no represented callable body.
- Effect collector omitted observations before flow assembly; displayed effects are partial.
- Effect collector totals unavailable; observed counts cover captured records only.

| Step | Callable record | Effect analysis | Collector totals | Observed | Emitted | Omitted |
|---|---|---|---|---:|---:|---:|
| `validate_publication_receipt (src/llm_wiki_cli/api.py)` | `available` | `evaluated` | `available` | `2` | `2` | `0` |
| `isinstance (src/llm_wiki_cli/api.py:v…idate_publication_receipt)` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `ValueError (src/llm_wiki_cli/api.py:v…idate_publication_receipt)` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `validate_publication_receipt (src/llm_wiki_cli/services/publication_candidate.py)` | `available` | `evaluated` | `available` | `7` | `7` | `0` |
| `_json_tree` | `available` | `evaluated` | `available` | `6` | `6` | `0` |
| `pending.pop` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `_fail` | `available` | `evaluated` | `available` | `2` | `2` | `0` |
| `PublicationProtocolError` | `unavailable` | `unavailable` | `unavailable` | — | — | — |
| `isinstance (src/llm_wiki_cli/services…n_contracts.py:_json_tree)` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `any (src/llm_wiki_cli/services…n_contracts.py:_json_tree)` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `type (src/llm_wiki_cli/services…n_contracts.py:_json_tree)` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `_fail` | `available` | `evaluated` | `available` | `2` | `2` | `0` |

```mermaid
flowchart LR
    s1["1. validate_publication_receipt (src/llm_wiki_cli/api.py)"]
    s2["2. isinstance (src/llm_wiki_cli/api.py:v…idate_publication_receipt)"]
    s3["3. ValueError (src/llm_wiki_cli/api.py:v…idate_publication_receipt)"]
    s4["4. validate_publication_receipt (src/llm_wiki_cli/services/publication_candidate.py)"]
    s5["5. _json_tree"]
    s6["6. pending.pop"]
    s7["7. _fail"]
    s8["8. PublicationProtocolError"]
    s9["9. isinstance (src/llm_wiki_cli/services…n_contracts.py:_json_tree)"]
    s10["10. any (src/llm_wiki_cli/services…n_contracts.py:_json_tree)"]
    s11["11. type (src/llm_wiki_cli/services…n_contracts.py:_json_tree)"]
    s12["12. _fail"]
    s1 -. "isinstance (src/llm_wiki_cli/api.py:v…idate_publication_receipt)(receipt, Mapping)" .-> s2
    s1 -. "ValueError (src/llm_wiki_cli/api.py:v…idate_publication_receipt)('Publication receipt must be a mapping')" .-> s3
    s1 -->|"validate_publication_receipt (src/llm_wiki_cli/services/publication_candidate.py)(dict(...))"| s4
    s4 -->|"_json_tree(receipt)"| s5
    s5 -. "pending.pop(data not statically known)" .-> s6
    s5 -->|"_fail('document', 'exceeds JSON structural bounds')"| s7
    s7 -->|"PublicationProtocolError(...)"| s8
    s5 -. "isinstance (src/llm_wiki_cli/services…n_contracts.py:_json_tree)(item, Mapping)" .-> s9
    s5 -. "any (src/llm_wiki_cli/services…n_contracts.py:_json_tree)(...)" .-> s10
    s5 -. "type (src/llm_wiki_cli/services…n_contracts.py:_json_tree)(key)" .-> s11
    s5 -->|"_fail('document', 'object keys must be strings')"| s12
    b0["mutation seen.add"]
    s4 -. "mutation seen.add" .-> b0
    b1["mutation pending.pop"]
    s5 -. "mutation pending.pop" .-> b1
    b2["mutation pending.extend"]
    s5 -. "mutation pending.extend" .-> b2
    b3["mutation pending.extend"]
    s5 -. "mutation pending.extend" .-> b3
    click s1 "../modules/api.md"
    click s4 "../modules/publication_candidate.md"
    click s5 "../modules/publication_contracts.md"
    click s7 "../modules/publication_contracts.md"
    click s8 "../modules/publication_contracts.md"
    click s12 "../modules/publication_contracts.md"
    classDef boundary stroke:#b45309,stroke-dasharray: 4 2
    class b0 boundary
    class b1 boundary
    class b2 boundary
    class b3 boundary
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `validate_publication_receipt (src/llm_wiki_cli/api.py)` | `receipt: Mapping[str, Any]` | `Mapping` | - | - |
| `isinstance (src/llm_wiki_cli/api.py:v…idate_publication_receipt)` | - | - | - | - |
| `ValueError (src/llm_wiki_cli/api.py:v…idate_publication_receipt)` | - | - | - | - |
| `validate_publication_receipt (src/llm_wiki_cli/services/publication_candidate.py)` | `receipt: Mapping[str, Any]` | `MAX_TREE_BYTES`, `Mapping`, `_RECEIPT_FIELDS`, `RECEIPT_SCHEMA`, `MAX_FILES` | - | - |
| `_json_tree` | `value: object` | `_MAX_JSON_NODES`, `Mapping` | - | - |
| `pending.pop` | - | - | - | - |
| `_fail` | `field: str`, `message: str` | - | - | - |
| `PublicationProtocolError` | - | - | - | - |
| `isinstance (src/llm_wiki_cli/services…n_contracts.py:_json_tree)` | - | - | - | - |
| `any (src/llm_wiki_cli/services…n_contracts.py:_json_tree)` | - | - | - | - |
| `type (src/llm_wiki_cli/services…n_contracts.py:_json_tree)` | - | - | - | - |
| `_fail` | `field: str`, `message: str` | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| validate_publication_receipt (src/llm_wiki_cli/api.py) | isinstance (src/llm_wiki_cli/api.py:v…idate_publication_receipt) | 3660 | `isinstance(receipt, Mapping)` |
| validate_publication_receipt (src/llm_wiki_cli/api.py) | ValueError (src/llm_wiki_cli/api.py:v…idate_publication_receipt) | 3661 | `ValueError('Publication receipt must be a mapping')` |
| validate_publication_receipt (src/llm_wiki_cli/api.py) | validate_publication_receipt (src/llm_wiki_cli/services/publication_candidate.py) | 3662 | `validate(dict(...))` |
| validate_publication_receipt (src/llm_wiki_cli/services/publication_candidate.py) | _json_tree | 270 | `_json_tree(receipt)` |
| _json_tree | pending.pop | 135 | `pending.pop(data not statically known)` |
| _json_tree | _fail | 138 | `_fail('document', 'exceeds JSON structural bounds')` |
| _fail | PublicationProtocolError | 43 | `PublicationProtocolError(...)` |
| _json_tree | isinstance (src/llm_wiki_cli/services…n_contracts.py:_json_tree) | 139 | `isinstance(item, Mapping)` |
| _json_tree | any (src/llm_wiki_cli/services…n_contracts.py:_json_tree) | 140 | `any(...)` |
| _json_tree | type (src/llm_wiki_cli/services…n_contracts.py:_json_tree) | 140 | `type(key)` |
| _json_tree | _fail | 141 | `_fail('document', 'object keys must be strings')` |

### Boundary effects

| Kind | Target | Step | Line |
|---|---|---|---:|
| mutation | `seen.add` | `validate_publication_receipt` | 409 |
| mutation | `pending.pop` | `_json_tree` | 135 |
| mutation | `pending.extend` | `_json_tree` | 142 |
| mutation | `pending.extend` | `_json_tree` | 144 |

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| external_call | `validate_publication_receipt` | `isinstance` | 3660 |
| external_call | `validate_publication_receipt` | `ValueError` | 3661 |
| external_call | `_json_tree` | `isinstance` | 139 |
| external_call | `_json_tree` | `any` | 140 |
| external_call | `_json_tree` | `type` | 140 |
| step_limit | `validate_publication_receipt` | `first 12 steps` | 0 |
| truncated_flow | `validate_publication_receipt` | `depth limit` | 0 |

## Behavior

This flow starts at `validate_publication_receipt` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
