# resolve_publication_finding

**Entry point:** `resolve_publication_finding` (`api`)
**Source:** [api](../modules/api.md)
**Modules touched:** [api](../modules/api.md), [publication_contracts](../modules/publication_contracts.md), [publication_impact](../modules/publication_impact.md)

## Call sequence

> Static overview in presentation order, not runtime execution order. Arrows retain captured callers; representative internal continuations and boundary examples precede repeated helper detail.

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as resolve_publication_finding (src/llm_wiki_cli/api.py)
    participant p1 as resolve_publication_finding (src/llm_wiki_cli/services/publication_impact.py)
    participant p2 as validate_publication_report
    participant p3 as validate_publication_basis
    participant p4 as validate_publication_reviews
    participant p5 as _guard
    participant p6 as _json_tree
    participant p7 as _fail
    participant p8 as PublicationProtocolError
    participant p9 as next
    participant p10 as reviewer.strip
    participant p11 as any (src/llm_wiki_cli/services…esolve_publication_finding)
    participant p12 as reason.strip
    participant p13 as deepcopy
    participant p14 as records.append
    participant p15 as sorted
    participant p16 as callback
    participant p17 as pending.pop
    participant p18 as isinstance
    participant p19 as any (src/llm_wiki_cli/services…on_contracts.py:_json_tree)
    participant p20 as type
    participant p21 as pending.extend
    participant p22 as item.values
    participant p23 as math.isfinite
    p0->>p1: resolve_publication_finding (src/llm_wiki_cli/services/publication_impact.py)
    p1->>p2: validate_publication_report
    p1->>p3: validate_publication_basis
    p1->>p4: validate_publication_reviews
    p2->>p5: _guard
    p5->>p6: _json_tree
    p6->>p7: _fail
    p1->>p8: PublicationProtocolError
    p1-->>p9: next(..., None)
    p1-->>p10: reviewer.strip
    p1-->>p11: any (src/llm_wiki_cli/services…esolve_publication_finding)(...)
    p1-->>p12: reason.strip
    p1-->>p13: deepcopy(validate_publication_reviews(...))
    p1-->>p14: records.append(record)
    p1-->>p15: sorted(records, key=...)
    p5-->>p16: callback(value)
    p6-->>p17: pending.pop
    p6-->>p18: isinstance(item, Mapping)
    p6-->>p19: any (src/llm_wiki_cli/services…on_contracts.py:_json_tree)(...)
    p6-->>p20: type(key)
    p6-->>p21: pending.extend(...)
    p6-->>p22: item.values
    p6-->>p20: type(item)
    p6-->>p21: pending.extend(...)
    p6-->>p20: type(item)
    p6-->>p23: math.isfinite(item)
    p6-->>p20: type(item)
    p1->>p8: PublicationProtocolError
    p1->>p8: PublicationProtocolError
    p1->>p8: PublicationProtocolError
```

> Call sequence diagram shows 30 of 38 interactions; 8 omitted to keep the visualization within the 30-interaction and generated-diagram limits, with uncertain identities omitted rather than inferred.

> Captured boundary calls: external 11 of 11 (0 omitted); unresolved 8 of 8 (0 omitted). These counts cover the captured static trace.

Omitted captured detail, grouped by actual caller occurrence and target module:

| Caller | Parent step | Target module | Kind | Omitted interactions |
| --- | --- | --- | --- | --- |
| `src/llm_wiki_cli/services/publication_contracts.py:_fail` | 7 | [src/llm_wiki_cli/services/publication_contracts.py](../modules/publication_contracts.md) | internal | 1 |
| `src/llm_wiki_cli/services/publication_contracts.py:_json_tree` | 5 | [src/llm_wiki_cli/services/publication_contracts.py](../modules/publication_contracts.md) | internal | 3 |
| `src/llm_wiki_cli/services/publication_contracts.py:_guard` | 4 | [src/llm_wiki_cli/services/publication_contracts.py](../modules/publication_contracts.md) | internal | 1 |
| `src/llm_wiki_cli/services/publication_contracts.py:validate_publication_basis` | 24 | [src/llm_wiki_cli/services/publication_contracts.py](../modules/publication_contracts.md) | internal | 1 |
| `src/llm_wiki_cli/services/publication_impact.py:resolve_publication_finding` | 2 | [src/llm_wiki_cli/services/publication_contracts.py](../modules/publication_contracts.md) | internal | 1 |
| `src/llm_wiki_cli/services/publication_contracts.py:validate_publication_reviews` | 36 | [src/llm_wiki_cli/services/publication_contracts.py](../modules/publication_contracts.md) | internal | 1 |
> Detailed flow queries retain their own coverage and limits; omitted paths may execute at runtime.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->

### Analysis coverage

**Effect analysis partially available.** Flow assembly and source effect analysis are separate; empty observations do not prove an empty handler body.

Source steps: 20; effect analysis evaluated: 13, partial: 0, unavailable: 7. Counts include steps omitted from the displayed trace.

Collector observations for 13 source steps with known totals: observed: 48, emitted: 48, omitted: 0. Unavailable totals are excluded.

- Callable record unavailable for one or more source steps; those steps have no represented callable body.
- Effect collector totals unavailable; observed counts cover captured records only.

| Step | Callable record | Effect analysis | Collector totals | Observed | Emitted | Omitted |
|---|---|---|---|---:|---:|---:|
| `resolve_publication_finding (src/llm_wiki_cli/api.py)` | `available` | `evaluated` | `available` | `7` | `7` | `0` |
| `resolve_publication_finding (src/llm_wiki_cli/services/publication_impact.py)` | `available` | `evaluated` | `available` | `9` | `9` | `0` |
| `validate_publication_report` | `available` | `evaluated` | `available` | `2` | `2` | `0` |
| `_guard` | `available` | `evaluated` | `available` | `4` | `4` | `0` |
| `_json_tree` | `available` | `evaluated` | `available` | `5` | `5` | `0` |
| `pending.pop` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `_fail` | `available` | `evaluated` | `available` | `2` | `2` | `0` |
| `PublicationProtocolError` | `unavailable` | `unavailable` | `unavailable` | — | — | — |
| `isinstance` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `any (src/llm_wiki_cli/services…on_contracts.py:_json_tree)` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `type` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `_fail` | `available` | `evaluated` | `available` | `2` | `2` | `0` |

```mermaid
flowchart LR
    s1["1. resolve_publication_finding (src/llm_wiki_cli/api.py)"]
    s2["2. resolve_publication_finding (src/llm_wiki_cli/services/publication_impact.py)"]
    s3["3. validate_publication_report"]
    s4["4. _guard"]
    s5["5. _json_tree"]
    s6["6. pending.pop"]
    s7["7. _fail"]
    s8["8. PublicationProtocolError"]
    s9["9. isinstance"]
    s10["10. any (src/llm_wiki_cli/services…on_contracts.py:_json_tree)"]
    s11["11. type"]
    s12["12. _fail"]
    s1 -->|"resolve_publication_finding (src/llm_wiki_cli/services/publication_impact.py)(…)"| s2
    s2 -->|"validate_publication_report(report)"| s3
    s3 -->|"_guard(_report, value)"| s4
    s4 -->|"_json_tree(value)"| s5
    s5 -. "pending.pop(data not statically known)" .-> s6
    s5 -->|"_fail('document', 'exceeds JSON structural bounds')"| s7
    s7 -->|"PublicationProtocolError(...)"| s8
    s5 -. "isinstance(item, Mapping)" .-> s9
    s5 -. "any (src/llm_wiki_cli/services…on_contracts.py:_json_tree)(...)" .-> s10
    s5 -. "type(key)" .-> s11
    s5 -->|"_fail('document', 'object keys must be strings')"| s12
    b0["mutation records.append"]
    s2 -. "mutation records.append" .-> b0
    b1["mutation pending.pop"]
    s5 -. "mutation pending.pop" .-> b1
    b2["mutation pending.extend"]
    s5 -. "mutation pending.extend" .-> b2
    b3["mutation pending.extend"]
    s5 -. "mutation pending.extend" .-> b3
    click s1 "../modules/api.md"
    click s2 "../modules/publication_impact.md"
    click s3 "../modules/publication_contracts.md"
    click s4 "../modules/publication_contracts.md"
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
| `resolve_publication_finding (src/llm_wiki_cli/api.py)` | `report: Mapping[str, Any]`, `candidate: Mapping[str, Any]`, `finding_id: str`, `reviewer: str`, `reason: str`, `reviews: Mapping[str, Any] \| None` | - | - | `resolve(...)` |
| `resolve_publication_finding (src/llm_wiki_cli/services/publication_impact.py)` | `report: Mapping[str, Any]`, `candidate: Mapping[str, Any]`, `finding_id: str`, `reviewer: str`, `reason: str`, `reviews: Mapping[str, Any] \| None` | `REVIEWS_SCHEMA` | - | `{...}` |
| `validate_publication_report` | `value: object` | `_report` | - | - |
| `_guard` | `callback`, `value: object` | `PublicationProtocolError` | - | `callback(...)` |
| `_json_tree` | `value: object` | `Mapping` | - | - |
| `pending.pop` | - | - | - | - |
| `_fail` | `field: str`, `message: str` | - | - | - |
| `PublicationProtocolError` | - | - | - | - |
| `isinstance` | - | - | - | - |
| `any (src/llm_wiki_cli/services…on_contracts.py:_json_tree)` | - | - | - | - |
| `type` | - | - | - | - |
| `_fail` | `field: str`, `message: str` | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| resolve_publication_finding (src/llm_wiki_cli/api.py) | resolve_publication_finding (src/llm_wiki_cli/services/publication_impact.py) | 3580 | `resolve(report, candidate, finding_id=finding_id, reviewer=reviewer, reason=reason, reviews=reviews)` |
| resolve_publication_finding (src/llm_wiki_cli/services/publication_impact.py) | validate_publication_report | 423 | `validate_publication_report(report)` |
| validate_publication_report | _guard | 754 | `_guard(_report, value)` |
| _guard | _json_tree | 734 | `_json_tree(value)` |
| _json_tree | pending.pop | 133 | `pending.pop(data not statically known)` |
| _json_tree | _fail | 136 | `_fail('document', 'exceeds JSON structural bounds')` |
| _fail | PublicationProtocolError | 41 | `PublicationProtocolError(...)` |
| _json_tree | isinstance | 137 | `isinstance(item, Mapping)` |
| _json_tree | any (src/llm_wiki_cli/services…on_contracts.py:_json_tree) | 138 | `any(...)` |
| _json_tree | type | 138 | `type(key)` |
| _json_tree | _fail | 139 | `_fail('document', 'object keys must be strings')` |

### Boundary effects

| Kind | Target | Step | Line |
|---|---|---|---:|
| mutation | `records.append` | `resolve_publication_finding` | 466 |
| mutation | `pending.pop` | `_json_tree` | 133 |
| mutation | `pending.extend` | `_json_tree` | 140 |
| mutation | `pending.extend` | `_json_tree` | 142 |

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| external_call | `_json_tree` | `isinstance` | 137 |
| external_call | `_json_tree` | `any` | 138 |
| external_call | `_json_tree` | `type` | 138 |
| step_limit | `resolve_publication_finding` | `first 12 steps` | 0 |

## Behavior

This flow starts at `resolve_publication_finding` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
